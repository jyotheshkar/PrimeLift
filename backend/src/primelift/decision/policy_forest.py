"""DRPolicyForest training and reporting for revised Phase 5."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from econml.policy import DRPolicyForest
from pydantic import BaseModel, ConfigDict
from sklearn.exceptions import DataConversionWarning

from primelift.decision.policy_tree import (
    POLICY_TREE_RAW_FEATURES,
    PolicyFeatureImportance,
    PolicySegmentMix,
    _build_feature_importance_summary,
    _build_lgbm_classifier,
    _build_lgbm_regressor,
    _build_segment_mix,
    _encode_policy_features,
    _estimate_policy_value,
    _load_raw_split_frames,
    _safe_observed_ate,
)
from primelift.utils.paths import (
    DEFAULT_DATASET_PATH,
    DEFAULT_DRPOLICYFOREST_CONVERSION_MODEL_PATH,
    DEFAULT_DRPOLICYFOREST_CONVERSION_REPORT_PATH,
    DEFAULT_DRPOLICYFOREST_CONVERSION_TEST_DECISIONS_PATH,
    DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH,
    DEFAULT_PREPROCESSING_MANIFEST_PATH,
    ensure_project_directories,
)


class Phase5PolicyForestReport(BaseModel):
    """Serializable report for the DRPolicyForest Phase 5 slice."""

    model_config = ConfigDict(frozen=True)

    report_name: str
    outcome_column: str
    split_name: str
    raw_dataset_path: str
    prepared_manifest_path: str
    model_artifact_path: str
    decisions_output_path: str
    output_report_path: str
    policy_tree_report_path: str | None
    train_row_count: int
    test_row_count: int
    policy_feature_columns: list[str]
    policy_feature_count: int
    forest_n_estimators: int
    forest_max_depth: int | None
    recommended_treat_user_count: int
    recommended_control_user_count: int
    recommended_treat_rate: float
    estimated_policy_value: float
    mean_predicted_policy_value: float
    always_treat_value: float
    always_control_value: float
    policy_gain_over_always_treat: float
    policy_gain_over_always_control: float
    policy_tree_value: float | None
    policy_gain_over_tree: float | None
    recommended_treat_observed_ate: float | None
    top_feature_importances: list[PolicyFeatureImportance]
    top_treat_segments: list[PolicySegmentMix]
    top_control_segments: list[PolicySegmentMix]
    action_summary: str


def _fit_policy_forest(
    *,
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    t_train: np.ndarray,
    random_seed: int,
    n_estimators: int,
    max_depth: int | None,
    min_samples_split: int,
    min_samples_leaf: int,
    max_samples: float,
    honest: bool,
    cv: int,
    n_jobs: int,
    model_regression_params: dict[str, Any] | None,
    model_propensity_params: dict[str, Any] | None,
) -> DRPolicyForest:
    """Fit a DRPolicyForest with stable local defaults."""

    model_regression = _build_lgbm_regressor(
        random_seed=random_seed,
        overrides=model_regression_params,
    )
    model_propensity = _build_lgbm_classifier(
        random_seed=random_seed,
        overrides=model_propensity_params,
    )
    policy_forest = DRPolicyForest(
        model_regression=model_regression,
        model_propensity=model_propensity,
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        max_samples=max_samples,
        honest=honest,
        cv=cv,
        n_jobs=n_jobs,
        random_state=random_seed,
    )

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=DataConversionWarning)
        policy_forest.fit(y_train, t_train, X=X_train)
    return policy_forest


def _predict_policy_forest_outputs(
    policy_forest: DRPolicyForest,
    X_test: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """Predict policy actions and policy values with warning suppression."""

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=DataConversionWarning)
        recommendations = np.asarray(policy_forest.predict(X_test), dtype=int).reshape(-1)
        predicted_policy_values = np.asarray(
            policy_forest.predict_value(X_test),
            dtype=float,
        ).reshape(-1)
    return recommendations, predicted_policy_values


def _load_policy_tree_value(policy_tree_report_path: Path | None) -> float | None:
    """Load the estimated policy-tree holdout value when available."""

    if policy_tree_report_path is None or not policy_tree_report_path.exists():
        return None
    payload = json.loads(policy_tree_report_path.read_text(encoding="utf-8"))
    return float(payload["estimated_policy_value"])


def _build_action_summary(
    top_treat_segments: list[PolicySegmentMix],
    top_control_segments: list[PolicySegmentMix],
) -> str:
    """Create a compact human-readable summary for the policy forest."""

    treat_names = ", ".join(segment.segment for segment in top_treat_segments[:3]) or "no major cohorts"
    control_names = ", ".join(segment.segment for segment in top_control_segments[:2]) or "no major holdout cohorts"
    return f"Policy forest treats primarily {treat_names}; holds out more of {control_names}."


def train_drpolicyforest_conversion_policy(
    *,
    raw_dataset_path: Path = DEFAULT_DATASET_PATH,
    prepared_manifest_path: Path = DEFAULT_PREPROCESSING_MANIFEST_PATH,
    model_artifact_path: Path = DEFAULT_DRPOLICYFOREST_CONVERSION_MODEL_PATH,
    output_report_path: Path = DEFAULT_DRPOLICYFOREST_CONVERSION_REPORT_PATH,
    decisions_output_path: Path = DEFAULT_DRPOLICYFOREST_CONVERSION_TEST_DECISIONS_PATH,
    policy_tree_report_path: Path | None = DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH,
    random_seed: int = 42,
    n_estimators: int = 200,
    max_depth: int | None = None,
    min_samples_split: int = 800,
    min_samples_leaf: int = 300,
    max_samples: float = 0.5,
    honest: bool = False,
    cv: int = 3,
    n_jobs: int = 1,
    model_regression_params: dict[str, Any] | None = None,
    model_propensity_params: dict[str, Any] | None = None,
) -> Phase5PolicyForestReport:
    """Train the revised Phase 5 DRPolicyForest conversion policy and score the test split."""

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

    policy_forest = _fit_policy_forest(
        X_train=X_train,
        y_train=y_train,
        t_train=t_train,
        random_seed=random_seed,
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        max_samples=max_samples,
        honest=honest,
        cv=cv,
        n_jobs=n_jobs,
        model_regression_params=model_regression_params,
        model_propensity_params=model_propensity_params,
    )

    recommendations, predicted_policy_values = _predict_policy_forest_outputs(policy_forest, X_test)

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
    decisions_output_path.parent.mkdir(parents=True, exist_ok=True)
    decisions_frame.to_csv(decisions_output_path, index=False)

    model_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model_name": "drpolicyforest_conversion",
            "estimator": policy_forest,
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
    tree_value = _load_policy_tree_value(policy_tree_report_path)

    report = Phase5PolicyForestReport(
        report_name="phase5_drpolicyforest_conversion_policy",
        outcome_column="conversion",
        split_name="test",
        raw_dataset_path=str(raw_dataset_path),
        prepared_manifest_path=str(prepared_manifest_path),
        model_artifact_path=str(model_artifact_path),
        decisions_output_path=str(decisions_output_path),
        output_report_path=str(output_report_path),
        policy_tree_report_path=str(policy_tree_report_path) if policy_tree_report_path is not None else None,
        train_row_count=int(len(train_frame)),
        test_row_count=int(len(test_frame)),
        policy_feature_columns=feature_columns,
        policy_feature_count=len(feature_columns),
        forest_n_estimators=n_estimators,
        forest_max_depth=max_depth,
        recommended_treat_user_count=int(np.sum(recommendations == 1)),
        recommended_control_user_count=int(np.sum(recommendations == 0)),
        recommended_treat_rate=float(np.mean(recommendations == 1)),
        estimated_policy_value=float(estimated_policy_value),
        mean_predicted_policy_value=float(np.mean(predicted_policy_values)),
        always_treat_value=float(always_treat_value),
        always_control_value=float(always_control_value),
        policy_gain_over_always_treat=float(estimated_policy_value - always_treat_value),
        policy_gain_over_always_control=float(estimated_policy_value - always_control_value),
        policy_tree_value=tree_value,
        policy_gain_over_tree=(
            float(estimated_policy_value - tree_value) if tree_value is not None else None
        ),
        recommended_treat_observed_ate=recommended_treat_observed_ate,
        top_feature_importances=_build_feature_importance_summary(policy_forest, feature_columns),
        top_treat_segments=_build_segment_mix(test_frame, recommendations, action=1),
        top_control_segments=_build_segment_mix(test_frame, recommendations, action=0),
        action_summary=_build_action_summary(
            _build_segment_mix(test_frame, recommendations, action=1),
            _build_segment_mix(test_frame, recommendations, action=0),
        ),
    )

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return report
