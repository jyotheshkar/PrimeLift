"""Explainable DRPolicyTree training and reporting for revised Phase 5."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from econml.policy import DRPolicyTree
from lightgbm import LGBMClassifier, LGBMRegressor
from pydantic import BaseModel, ConfigDict
from sklearn.exceptions import DataConversionWarning

from primelift.causal.ate import estimate_average_treatment_effect
from primelift.data.preparation import load_prepared_dataset_summary
from primelift.data.summary import load_dataset
from primelift.utils.paths import (
    DEFAULT_DATASET_PATH,
    DEFAULT_DRPOLICYTREE_CONVERSION_MODEL_PATH,
    DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH,
    DEFAULT_DRPOLICYTREE_CONVERSION_TEST_DECISIONS_PATH,
    DEFAULT_PREPROCESSING_MANIFEST_PATH,
    ensure_project_directories,
)

POLICY_TREE_CATEGORICAL_FEATURES = (
    "segment",
    "device_type",
    "is_prime_like_member",
)
POLICY_TREE_NUMERIC_FEATURES = (
    "age",
    "prior_engagement_score",
    "prior_purchases_90d",
    "prior_sessions_30d",
    "avg_order_value",
    "customer_tenure_days",
)
POLICY_TREE_RAW_FEATURES = POLICY_TREE_NUMERIC_FEATURES + POLICY_TREE_CATEGORICAL_FEATURES


class PolicyFeatureImportance(BaseModel):
    """Serializable feature-importance entry for the explainable policy tree."""

    model_config = ConfigDict(frozen=True)

    feature_name: str
    importance: float


class PolicyLeafSummary(BaseModel):
    """Serializable summary for one leaf in the explainable policy tree."""

    model_config = ConfigDict(frozen=True)

    leaf_id: int
    depth: int
    recommended_action: str
    estimated_value: float
    test_user_count: int
    rule: str


class PolicySegmentMix(BaseModel):
    """Serializable summary of segment distribution under one policy action."""

    model_config = ConfigDict(frozen=True)

    segment: str
    user_count: int
    user_share: float


class Phase5PolicyTreeReport(BaseModel):
    """Serializable report for the DRPolicyTree Phase 5 slice."""

    model_config = ConfigDict(frozen=True)

    report_name: str
    outcome_column: str
    split_name: str
    raw_dataset_path: str
    prepared_manifest_path: str
    model_artifact_path: str
    decisions_output_path: str
    output_report_path: str
    train_row_count: int
    test_row_count: int
    policy_feature_columns: list[str]
    policy_feature_count: int
    tree_max_depth: int
    tree_actual_depth: int
    tree_leaf_count: int
    recommended_treat_user_count: int
    recommended_control_user_count: int
    recommended_treat_rate: float
    estimated_policy_value: float
    mean_predicted_policy_value: float
    always_treat_value: float
    always_control_value: float
    policy_gain_over_always_treat: float
    policy_gain_over_always_control: float
    recommended_treat_observed_ate: float | None
    top_feature_importances: list[PolicyFeatureImportance]
    top_treat_segments: list[PolicySegmentMix]
    top_control_segments: list[PolicySegmentMix]
    leaf_summaries: list[PolicyLeafSummary]
    action_summary: str


def _build_lgbm_classifier(
    random_seed: int, overrides: dict[str, Any] | None = None
) -> LGBMClassifier:
    """Build a reproducible LightGBM classifier for policy nuisance tasks."""

    parameters: dict[str, Any] = {
        "n_estimators": 120,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_child_samples": 40,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "random_state": random_seed,
        "n_jobs": 1,
        "verbosity": -1,
    }
    if overrides:
        parameters.update(overrides)
    return LGBMClassifier(**parameters)


def _build_lgbm_regressor(
    random_seed: int, overrides: dict[str, Any] | None = None
) -> LGBMRegressor:
    """Build a reproducible LightGBM regressor for policy outcome nuisance tasks."""

    parameters: dict[str, Any] = {
        "n_estimators": 120,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_child_samples": 40,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "random_state": random_seed,
        "n_jobs": 1,
        "verbosity": -1,
    }
    if overrides:
        parameters.update(overrides)
    return LGBMRegressor(**parameters)


def _load_raw_split_frames(
    *,
    raw_dataset_path: Path,
    prepared_manifest_path: Path,
) -> dict[str, pd.DataFrame]:
    """Recover raw split frames by joining prepared split user IDs back to the raw dataset."""

    prepared_summary = load_prepared_dataset_summary(prepared_manifest_path)
    raw_dataset = load_dataset(raw_dataset_path).set_index("user_id", drop=False)
    split_frames: dict[str, pd.DataFrame] = {}

    for split_summary in prepared_summary.splits:
        split_user_ids = pd.read_csv(split_summary.file_path, usecols=["user_id"])["user_id"].tolist()
        split_frame = raw_dataset.loc[split_user_ids].reset_index(drop=True)
        split_frames[split_summary.split_name] = split_frame

    return split_frames


def _encode_policy_features(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Build a compact, interpretable feature matrix for the policy tree."""

    train_features = train_frame.loc[:, list(POLICY_TREE_RAW_FEATURES)].copy()
    test_features = test_frame.loc[:, list(POLICY_TREE_RAW_FEATURES)].copy()

    train_encoded = pd.get_dummies(
        train_features,
        columns=list(POLICY_TREE_CATEGORICAL_FEATURES),
        prefix_sep=" = ",
        dtype=float,
    )
    test_encoded = pd.get_dummies(
        test_features,
        columns=list(POLICY_TREE_CATEGORICAL_FEATURES),
        prefix_sep=" = ",
        dtype=float,
    )
    test_encoded = test_encoded.reindex(columns=train_encoded.columns, fill_value=0.0)

    feature_columns = list(train_encoded.columns)
    return train_encoded, test_encoded, feature_columns


def _fit_policy_tree(
    *,
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    t_train: np.ndarray,
    random_seed: int,
    max_depth: int,
    min_samples_split: int,
    min_samples_leaf: int,
    honest: bool,
    cv: int,
    model_regression_params: dict[str, Any] | None,
    model_propensity_params: dict[str, Any] | None,
) -> DRPolicyTree:
    """Fit a DRPolicyTree with stable local defaults."""

    model_regression = _build_lgbm_regressor(
        random_seed=random_seed,
        overrides=model_regression_params,
    )
    model_propensity = _build_lgbm_classifier(
        random_seed=random_seed,
        overrides=model_propensity_params,
    )
    policy_tree = DRPolicyTree(
        model_regression=model_regression,
        model_propensity=model_propensity,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        honest=honest,
        cv=cv,
        random_state=random_seed,
    )

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMClassifier was fitted with feature names",
            category=UserWarning,
        )
        warnings.filterwarnings("ignore", category=DataConversionWarning)
        policy_tree.fit(y_train, t_train, X=X_train)
    return policy_tree


def _safe_observed_ate(frame: pd.DataFrame) -> float | None:
    """Compute observed ATE within a frame if both treatment arms are present."""

    try:
        return float(
            estimate_average_treatment_effect(
                dataset=frame,
                outcome_column="conversion",
                treatment_column="treatment",
            ).ate
        )
    except ValueError:
        return None


def _estimate_policy_value(
    test_frame: pd.DataFrame,
    recommendations: np.ndarray,
) -> tuple[float, float, float]:
    """Estimate holdout policy value using the randomized test split."""

    treat_mask = recommendations == 1
    control_mask = ~treat_mask

    treat_share = float(np.mean(treat_mask))
    control_share = 1.0 - treat_share

    treat_outcomes = test_frame.loc[treat_mask & (test_frame["treatment"] == 1), "conversion"]
    control_outcomes = test_frame.loc[control_mask & (test_frame["treatment"] == 0), "conversion"]
    if treat_share > 0.0 and treat_outcomes.empty:
        raise ValueError("Policy recommends treatment, but no treated holdout users matched that policy.")
    if control_share > 0.0 and control_outcomes.empty:
        raise ValueError("Policy recommends control, but no control holdout users matched that policy.")

    policy_value = 0.0
    if treat_share > 0.0:
        policy_value += treat_share * float(treat_outcomes.mean())
    if control_share > 0.0:
        policy_value += control_share * float(control_outcomes.mean())

    always_treat_value = float(test_frame.loc[test_frame["treatment"] == 1, "conversion"].mean())
    always_control_value = float(test_frame.loc[test_frame["treatment"] == 0, "conversion"].mean())
    return policy_value, always_treat_value, always_control_value


def _predict_policy_outputs(
    policy_tree: DRPolicyTree,
    X_test: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Predict policy actions, values, and leaf IDs with warning suppression."""

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMClassifier was fitted with feature names",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMRegressor was fitted with feature names",
            category=UserWarning,
        )
        warnings.filterwarnings("ignore", category=DataConversionWarning)
        recommendations = np.asarray(policy_tree.predict(X_test), dtype=int).reshape(-1)
        predicted_policy_values = np.asarray(
            policy_tree.predict_value(X_test),
            dtype=float,
        ).reshape(-1)
        leaf_ids = np.asarray(policy_tree.policy_model_.apply(X_test), dtype=int).reshape(-1)

    return recommendations, predicted_policy_values, leaf_ids


def _format_split_rule(feature_name: str, threshold: float, direction: str) -> str:
    """Format one split rule in a human-readable way."""

    if " = " in feature_name and abs(threshold - 0.5) <= 0.5:
        feature_group, feature_value = feature_name.split(" = ", 1)
        if direction == "left":
            return f"{feature_group} != {feature_value}"
        return f"{feature_group} == {feature_value}"

    operator = "<=" if direction == "left" else ">"
    return f"{feature_name} {operator} {threshold:.2f}"


def _extract_leaf_summaries(
    *,
    policy_tree: DRPolicyTree,
    feature_names: list[str],
    X_test: pd.DataFrame,
) -> list[PolicyLeafSummary]:
    """Extract leaf rules and holdout population from the fitted policy tree."""

    tree = policy_tree.policy_model_.tree_
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMClassifier was fitted with feature names",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMRegressor was fitted with feature names",
            category=UserWarning,
        )
        warnings.filterwarnings("ignore", category=DataConversionWarning)
        leaf_assignments = policy_tree.policy_model_.apply(X_test)
    leaf_counts = pd.Series(leaf_assignments).value_counts().to_dict()
    summaries: list[PolicyLeafSummary] = []

    def traverse(node_id: int, depth: int, conditions: list[str]) -> None:
        left_child = int(tree.children_left[node_id])
        right_child = int(tree.children_right[node_id])
        if left_child == -1 and right_child == -1:
            action_values = tree.value[node_id, :, 0]
            recommended_action = "treat" if int(np.argmax(action_values)) == 1 else "control"
            summaries.append(
                PolicyLeafSummary(
                    leaf_id=node_id,
                    depth=depth,
                    recommended_action=recommended_action,
                    estimated_value=float(np.max(action_values)),
                    test_user_count=int(leaf_counts.get(node_id, 0)),
                    rule=" and ".join(conditions) if conditions else "all users",
                )
            )
            return

        feature_name = feature_names[int(tree.feature[node_id])]
        threshold = float(tree.threshold[node_id])
        traverse(
            left_child,
            depth + 1,
            [*conditions, _format_split_rule(feature_name, threshold, "left")],
        )
        traverse(
            right_child,
            depth + 1,
            [*conditions, _format_split_rule(feature_name, threshold, "right")],
        )

    traverse(0, 0, [])
    return sorted(
        summaries,
        key=lambda item: (item.recommended_action != "treat", -item.test_user_count, -item.estimated_value),
    )


def _build_feature_importance_summary(
    policy_tree: DRPolicyTree,
    feature_names: list[str],
) -> list[PolicyFeatureImportance]:
    """Build the top feature-importance list from the fitted policy tree."""

    importances = np.asarray(policy_tree.feature_importances_, dtype=float)
    pairs = [
        PolicyFeatureImportance(feature_name=name, importance=float(importance))
        for name, importance in zip(feature_names, importances, strict=True)
        if float(importance) > 0.0
    ]
    return sorted(pairs, key=lambda item: item.importance, reverse=True)[:5]


def _build_segment_mix(
    test_frame: pd.DataFrame,
    recommendations: np.ndarray,
    action: int,
) -> list[PolicySegmentMix]:
    """Summarize segment mix for either the policy-treat or policy-control side."""

    subset = test_frame.loc[recommendations == action, "segment"]
    if subset.empty:
        return []

    counts = subset.value_counts()
    total = int(counts.sum())
    return [
        PolicySegmentMix(
            segment=str(segment),
            user_count=int(count),
            user_share=float(count / total),
        )
        for segment, count in counts.head(3).items()
    ]


def _build_action_summary(leaf_summaries: list[PolicyLeafSummary]) -> str:
    """Create a compact explanation of the highest-coverage treat rules."""

    treat_leaves = [leaf for leaf in leaf_summaries if leaf.recommended_action == "treat"]
    if not treat_leaves:
        return "Policy tree does not recommend incremental treatment for the current holdout population."

    lead_rules = "; ".join(leaf.rule for leaf in treat_leaves[:2])
    return f"Treat users matching: {lead_rules}. Hold out the remaining users."


def train_drpolicytree_conversion_policy(
    *,
    raw_dataset_path: Path = DEFAULT_DATASET_PATH,
    prepared_manifest_path: Path = DEFAULT_PREPROCESSING_MANIFEST_PATH,
    model_artifact_path: Path = DEFAULT_DRPOLICYTREE_CONVERSION_MODEL_PATH,
    output_report_path: Path = DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH,
    decisions_output_path: Path = DEFAULT_DRPOLICYTREE_CONVERSION_TEST_DECISIONS_PATH,
    random_seed: int = 42,
    max_depth: int = 3,
    min_samples_split: int = 800,
    min_samples_leaf: int = 300,
    honest: bool = False,
    cv: int = 3,
    model_regression_params: dict[str, Any] | None = None,
    model_propensity_params: dict[str, Any] | None = None,
) -> Phase5PolicyTreeReport:
    """Train the revised Phase 5 DRPolicyTree conversion policy and score the test split."""

    ensure_project_directories()
    split_frames = _load_raw_split_frames(
        raw_dataset_path=raw_dataset_path,
        prepared_manifest_path=prepared_manifest_path,
    )
    train_frame = split_frames["train"]
    test_frame = split_frames["test"]

    X_train, X_test, feature_columns = _encode_policy_features(train_frame, test_frame)
    y_train = train_frame["conversion"].to_numpy(dtype=float)
    t_train = train_frame["treatment"].to_numpy(dtype=int)

    policy_tree = _fit_policy_tree(
        X_train=X_train,
        y_train=y_train,
        t_train=t_train,
        random_seed=random_seed,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        honest=honest,
        cv=cv,
        model_regression_params=model_regression_params,
        model_propensity_params=model_propensity_params,
    )

    recommendations, predicted_policy_values, leaf_ids = _predict_policy_outputs(policy_tree, X_test)

    decisions_frame = test_frame.loc[
        :,
        [
            "user_id",
            "segment",
            "london_borough",
            "device_type",
            "treatment",
            "conversion",
        ],
    ].copy()
    decisions_frame["policy_recommendation"] = recommendations
    decisions_frame["policy_recommendation_label"] = np.where(
        recommendations == 1,
        "treat",
        "control",
    )
    decisions_frame["predicted_policy_value"] = predicted_policy_values
    decisions_frame["policy_leaf_id"] = leaf_ids
    decisions_output_path.parent.mkdir(parents=True, exist_ok=True)
    decisions_frame.to_csv(decisions_output_path, index=False)

    model_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model_name": "drpolicytree_conversion",
            "estimator": policy_tree,
            "policy_feature_columns": feature_columns,
            "policy_raw_feature_columns": list(POLICY_TREE_RAW_FEATURES),
            "outcome_column": "conversion",
            "treatment_column": "treatment",
            "random_seed": random_seed,
        },
        model_artifact_path,
    )

    estimated_policy_value, always_treat_value, always_control_value = _estimate_policy_value(
        test_frame=test_frame,
        recommendations=recommendations,
    )
    treat_subset = test_frame.loc[recommendations == 1].copy()
    recommended_treat_observed_ate = _safe_observed_ate(treat_subset)
    leaf_summaries = _extract_leaf_summaries(
        policy_tree=policy_tree,
        feature_names=feature_columns,
        X_test=X_test,
    )

    report = Phase5PolicyTreeReport(
        report_name="phase5_drpolicytree_conversion_policy",
        outcome_column="conversion",
        split_name="test",
        raw_dataset_path=str(raw_dataset_path),
        prepared_manifest_path=str(prepared_manifest_path),
        model_artifact_path=str(model_artifact_path),
        decisions_output_path=str(decisions_output_path),
        output_report_path=str(output_report_path),
        train_row_count=int(len(train_frame)),
        test_row_count=int(len(test_frame)),
        policy_feature_columns=feature_columns,
        policy_feature_count=len(feature_columns),
        tree_max_depth=max_depth,
        tree_actual_depth=int(policy_tree.policy_model_.get_depth()),
        tree_leaf_count=int(policy_tree.policy_model_.get_n_leaves()),
        recommended_treat_user_count=int(np.sum(recommendations == 1)),
        recommended_control_user_count=int(np.sum(recommendations == 0)),
        recommended_treat_rate=float(np.mean(recommendations == 1)),
        estimated_policy_value=float(estimated_policy_value),
        mean_predicted_policy_value=float(np.mean(predicted_policy_values)),
        always_treat_value=float(always_treat_value),
        always_control_value=float(always_control_value),
        policy_gain_over_always_treat=float(estimated_policy_value - always_treat_value),
        policy_gain_over_always_control=float(estimated_policy_value - always_control_value),
        recommended_treat_observed_ate=recommended_treat_observed_ate,
        top_feature_importances=_build_feature_importance_summary(policy_tree, feature_columns),
        top_treat_segments=_build_segment_mix(test_frame, recommendations, action=1),
        top_control_segments=_build_segment_mix(test_frame, recommendations, action=0),
        leaf_summaries=leaf_summaries,
        action_summary=_build_action_summary(leaf_summaries),
    )

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return report
