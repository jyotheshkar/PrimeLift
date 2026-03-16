"""DRLearner training and scoring utilities for revised Phase 3."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from econml.dr import DRLearner
from lightgbm import LGBMClassifier, LGBMRegressor
from pydantic import BaseModel, ConfigDict
from sklearn.exceptions import DataConversionWarning

from primelift.causal.ate import analyze_average_treatment_effect, estimate_average_treatment_effect
from primelift.data.preparation import PreparedDatasetSummary, load_prepared_dataset_summary
from primelift.utils.paths import (
    DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH,
    DEFAULT_DRLEARNER_CONVERSION_MODEL_PATH,
    DEFAULT_DRLEARNER_CONVERSION_TEST_SCORES_PATH,
    DEFAULT_DRLEARNER_CONVERSION_VALIDATION_SCORES_PATH,
    DEFAULT_DRLEARNER_REVENUE_METRICS_PATH,
    DEFAULT_DRLEARNER_REVENUE_MODEL_PATH,
    DEFAULT_DRLEARNER_REVENUE_TEST_SCORES_PATH,
    DEFAULT_DRLEARNER_REVENUE_VALIDATION_SCORES_PATH,
    DEFAULT_PREPROCESSING_MANIFEST_PATH,
    ensure_project_directories,
)

PREPARED_META_COLUMNS = (
    "user_id",
    "campaign_id",
    "event_date",
    "treatment",
    "conversion",
    "revenue",
    "segment",
    "london_borough",
    "split",
)
DRLEARNER_CONVERSION_SCORE_COLUMN = "predicted_cate_drlearner_conversion"
DRLEARNER_REVENUE_SCORE_COLUMN = "predicted_cate_drlearner_revenue"


class DRLearnerTrainingConfig(BaseModel):
    """Serializable configuration used for DRLearner training."""

    model_config = ConfigDict(frozen=True)

    outcome_column: str
    treatment_column: str
    score_column: str
    model_propensity_class: str
    model_regression_class: str
    model_final_class: str
    model_propensity_params: dict[str, Any]
    model_regression_params: dict[str, Any]
    model_final_params: dict[str, Any]
    cv: int
    discrete_outcome: bool


class DRLearnerSplitEvaluation(BaseModel):
    """Serializable evaluation summary for one scored holdout split."""

    model_config = ConfigDict(frozen=True)

    split_name: str
    row_count: int
    mean_predicted_cate: float
    std_predicted_cate: float
    min_predicted_cate: float
    max_predicted_cate: float
    positive_cate_share: float
    overall_observed_ate: float
    top_decile_size: int
    top_decile_mean_predicted_cate: float
    top_decile_observed_ate: float | None
    bottom_decile_size: int
    bottom_decile_mean_predicted_cate: float
    bottom_decile_observed_ate: float | None
    top_segments_by_mean_predicted_cate: list[dict[str, float | str]]
    bottom_segments_by_mean_predicted_cate: list[dict[str, float | str]]
    score_output_path: str


class DRLearnerTrainingReport(BaseModel):
    """Serializable report for one revised Phase 3 DRLearner slice."""

    model_config = ConfigDict(frozen=True)

    model_name: str
    prepared_manifest_path: str
    feature_column_count: int
    feature_column_sample: list[str]
    train_row_count: int
    train_observed_ate: float
    validation_row_count: int
    test_row_count: int
    model_artifact_path: str
    metrics_report_path: str
    config: DRLearnerTrainingConfig
    baseline_validation_analysis: dict[str, float | int | str | None]
    split_evaluations: list[DRLearnerSplitEvaluation]


def _load_prepared_split_frame(split_path: str) -> pd.DataFrame:
    """Load one prepared split from disk."""

    return pd.read_csv(split_path)


def _extract_feature_columns(split_frame: pd.DataFrame) -> list[str]:
    """Extract transformed feature columns from a prepared split frame."""

    return [column for column in split_frame.columns if column not in PREPARED_META_COLUMNS]


def _build_lgbm_classifier(
    random_seed: int, overrides: dict[str, Any] | None = None
) -> LGBMClassifier:
    """Build a reproducible LightGBM classifier for DRLearner nuisance tasks."""

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
    """Build a reproducible LightGBM regressor for DRLearner regression tasks."""

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


def _safe_observed_ate(split_frame: pd.DataFrame, outcome_column: str) -> float | None:
    """Compute ATE safely for a scored subset if both treatment arms are present."""

    try:
        return estimate_average_treatment_effect(
            dataset=split_frame,
            outcome_column=outcome_column,
            treatment_column="treatment",
        ).ate
    except ValueError:
        return None


def _build_scored_output_frame(
    split_frame: pd.DataFrame,
    scores: np.ndarray,
    score_column: str,
) -> pd.DataFrame:
    """Build the saved scored output frame for one split."""

    output_frame = split_frame.loc[:, list(PREPARED_META_COLUMNS)].copy()
    output_frame[score_column] = scores.astype(float)
    return output_frame


def _evaluate_scored_split(
    split_name: str,
    split_frame: pd.DataFrame,
    scores: np.ndarray,
    score_output_path: Path,
    score_column: str,
    outcome_column: str,
) -> DRLearnerSplitEvaluation:
    """Summarize holdout scoring behavior for one split."""

    scored_frame = _build_scored_output_frame(
        split_frame=split_frame,
        scores=scores,
        score_column=score_column,
    )
    score_output_path.parent.mkdir(parents=True, exist_ok=True)
    scored_frame.to_csv(score_output_path, index=False)

    top_threshold = float(np.quantile(scores, 0.90))
    bottom_threshold = float(np.quantile(scores, 0.10))
    top_frame = scored_frame.loc[scored_frame[score_column] >= top_threshold]
    bottom_frame = scored_frame.loc[scored_frame[score_column] <= bottom_threshold]
    segment_means = (
        scored_frame.groupby("segment")[score_column].mean().sort_values(ascending=False)
    )

    return DRLearnerSplitEvaluation(
        split_name=split_name,
        row_count=int(len(scored_frame)),
        mean_predicted_cate=float(np.mean(scores)),
        std_predicted_cate=float(np.std(scores)),
        min_predicted_cate=float(np.min(scores)),
        max_predicted_cate=float(np.max(scores)),
        positive_cate_share=float(np.mean(scores > 0.0)),
        overall_observed_ate=float(
            estimate_average_treatment_effect(
                dataset=scored_frame,
                outcome_column=outcome_column,
                treatment_column="treatment",
            ).ate
        ),
        top_decile_size=int(len(top_frame)),
        top_decile_mean_predicted_cate=float(top_frame[score_column].mean()),
        top_decile_observed_ate=_safe_observed_ate(top_frame, outcome_column),
        bottom_decile_size=int(len(bottom_frame)),
        bottom_decile_mean_predicted_cate=float(bottom_frame[score_column].mean()),
        bottom_decile_observed_ate=_safe_observed_ate(bottom_frame, outcome_column),
        top_segments_by_mean_predicted_cate=[
            {"segment": segment_name, "mean_predicted_cate": float(mean_value)}
            for segment_name, mean_value in segment_means.head(3).items()
        ],
        bottom_segments_by_mean_predicted_cate=[
            {"segment": segment_name, "mean_predicted_cate": float(mean_value)}
            for segment_name, mean_value in segment_means.tail(3).sort_values().items()
        ],
        score_output_path=str(score_output_path),
    )


def _fit_effect_scores(drlearner: DRLearner, feature_frame: pd.DataFrame) -> np.ndarray:
    """Compute DRLearner effect scores with warning suppression for LightGBM internals."""

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
        return np.asarray(drlearner.effect(feature_frame), dtype=float).reshape(-1)


def load_trained_drlearner_bundle(model_artifact_path: Path) -> dict[str, Any]:
    """Load a saved DRLearner bundle from disk."""

    return joblib.load(model_artifact_path)


def load_trained_drlearner_revenue_bundle(model_artifact_path: Path) -> dict[str, Any]:
    """Load the saved DRLearner revenue bundle from disk."""

    return load_trained_drlearner_bundle(model_artifact_path)


def _train_drlearner_model(
    *,
    model_name: str,
    outcome_column: str,
    score_column: str,
    discrete_outcome: bool,
    prepared_manifest_path: Path,
    model_artifact_path: Path,
    metrics_report_path: Path,
    validation_scores_path: Path,
    test_scores_path: Path,
    random_seed: int,
    propensity_model_params: dict[str, Any] | None,
    regression_model_params: dict[str, Any] | None,
    final_model_params: dict[str, Any] | None,
    cv: int,
) -> DRLearnerTrainingReport:
    """Train one DRLearner outcome slice and score its holdout splits."""

    ensure_project_directories()
    prepared_summary: PreparedDatasetSummary = load_prepared_dataset_summary(prepared_manifest_path)
    split_paths = {split.split_name: split.file_path for split in prepared_summary.splits}

    train_frame = _load_prepared_split_frame(split_paths["train"])
    validation_frame = _load_prepared_split_frame(split_paths["validation"])
    test_frame = _load_prepared_split_frame(split_paths["test"])

    feature_columns = _extract_feature_columns(train_frame)
    X_train = train_frame.loc[:, feature_columns]
    y_train = train_frame[outcome_column].to_numpy()
    if discrete_outcome:
        y_train = y_train.astype(int)
    else:
        y_train = y_train.astype(float)
    t_train = train_frame["treatment"].to_numpy(dtype=int)

    model_propensity = _build_lgbm_classifier(
        random_seed=random_seed,
        overrides=propensity_model_params,
    )
    if discrete_outcome:
        model_regression = _build_lgbm_classifier(
            random_seed=random_seed,
            overrides=regression_model_params,
        )
    else:
        model_regression = _build_lgbm_regressor(
            random_seed=random_seed,
            overrides=regression_model_params,
        )
    model_final = _build_lgbm_regressor(
        random_seed=random_seed,
        overrides=final_model_params or {"n_estimators": 80},
    )

    drlearner = DRLearner(
        model_propensity=model_propensity,
        model_regression=model_regression,
        model_final=model_final,
        discrete_outcome=discrete_outcome,
        cv=cv,
        random_state=random_seed,
    )

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
        drlearner.fit(y_train, t_train, X=X_train)

    model_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model_name": model_name,
        "estimator": drlearner,
        "feature_columns": feature_columns,
        "score_column": score_column,
        "outcome_column": outcome_column,
        "treatment_column": "treatment",
        "random_seed": random_seed,
    }
    joblib.dump(bundle, model_artifact_path)

    validation_scores = _fit_effect_scores(drlearner, validation_frame.loc[:, feature_columns])
    test_scores = _fit_effect_scores(drlearner, test_frame.loc[:, feature_columns])

    split_evaluations = [
        _evaluate_scored_split(
            split_name="validation",
            split_frame=validation_frame,
            scores=validation_scores,
            score_output_path=validation_scores_path,
            score_column=score_column,
            outcome_column=outcome_column,
        ),
        _evaluate_scored_split(
            split_name="test",
            split_frame=test_frame,
            scores=test_scores,
            score_output_path=test_scores_path,
            score_column=score_column,
            outcome_column=outcome_column,
        ),
    ]

    config = DRLearnerTrainingConfig(
        outcome_column=outcome_column,
        treatment_column="treatment",
        score_column=score_column,
        model_propensity_class="lightgbm.LGBMClassifier",
        model_regression_class=(
            "lightgbm.LGBMClassifier" if discrete_outcome else "lightgbm.LGBMRegressor"
        ),
        model_final_class="lightgbm.LGBMRegressor",
        model_propensity_params=model_propensity.get_params(),
        model_regression_params=model_regression.get_params(),
        model_final_params=model_final.get_params(),
        cv=cv,
        discrete_outcome=discrete_outcome,
    )

    validation_baseline = analyze_average_treatment_effect(
        dataset=validation_frame,
        outcome_column=outcome_column,
        treatment_column="treatment",
        bootstrap_samples=300,
        random_seed=random_seed,
    )

    report = DRLearnerTrainingReport(
        model_name=model_name,
        prepared_manifest_path=str(prepared_manifest_path),
        feature_column_count=len(feature_columns),
        feature_column_sample=feature_columns[:20],
        train_row_count=int(len(train_frame)),
        train_observed_ate=float(
            estimate_average_treatment_effect(
                dataset=train_frame,
                outcome_column=outcome_column,
                treatment_column="treatment",
            ).ate
        ),
        validation_row_count=int(len(validation_frame)),
        test_row_count=int(len(test_frame)),
        model_artifact_path=str(model_artifact_path),
        metrics_report_path=str(metrics_report_path),
        config=config,
        baseline_validation_analysis=validation_baseline.model_dump(),
        split_evaluations=split_evaluations,
    )

    metrics_report_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_report_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return report


def train_drlearner_conversion_model(
    prepared_manifest_path: Path = DEFAULT_PREPROCESSING_MANIFEST_PATH,
    model_artifact_path: Path = DEFAULT_DRLEARNER_CONVERSION_MODEL_PATH,
    metrics_report_path: Path = DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH,
    validation_scores_path: Path = DEFAULT_DRLEARNER_CONVERSION_VALIDATION_SCORES_PATH,
    test_scores_path: Path = DEFAULT_DRLEARNER_CONVERSION_TEST_SCORES_PATH,
    random_seed: int = 42,
    propensity_model_params: dict[str, Any] | None = None,
    regression_model_params: dict[str, Any] | None = None,
    final_model_params: dict[str, Any] | None = None,
    cv: int = 3,
) -> DRLearnerTrainingReport:
    """Train the revised Phase 3 DRLearner conversion model and score holdout splits."""

    return _train_drlearner_model(
        model_name="drlearner_conversion",
        outcome_column="conversion",
        score_column=DRLEARNER_CONVERSION_SCORE_COLUMN,
        discrete_outcome=True,
        prepared_manifest_path=prepared_manifest_path,
        model_artifact_path=model_artifact_path,
        metrics_report_path=metrics_report_path,
        validation_scores_path=validation_scores_path,
        test_scores_path=test_scores_path,
        random_seed=random_seed,
        propensity_model_params=propensity_model_params,
        regression_model_params=regression_model_params,
        final_model_params=final_model_params,
        cv=cv,
    )


def train_drlearner_revenue_model(
    prepared_manifest_path: Path = DEFAULT_PREPROCESSING_MANIFEST_PATH,
    model_artifact_path: Path = DEFAULT_DRLEARNER_REVENUE_MODEL_PATH,
    metrics_report_path: Path = DEFAULT_DRLEARNER_REVENUE_METRICS_PATH,
    validation_scores_path: Path = DEFAULT_DRLEARNER_REVENUE_VALIDATION_SCORES_PATH,
    test_scores_path: Path = DEFAULT_DRLEARNER_REVENUE_TEST_SCORES_PATH,
    random_seed: int = 42,
    propensity_model_params: dict[str, Any] | None = None,
    regression_model_params: dict[str, Any] | None = None,
    final_model_params: dict[str, Any] | None = None,
    cv: int = 3,
) -> DRLearnerTrainingReport:
    """Train the revised Phase 3 DRLearner revenue model and score holdout splits."""

    return _train_drlearner_model(
        model_name="drlearner_revenue",
        outcome_column="revenue",
        score_column=DRLEARNER_REVENUE_SCORE_COLUMN,
        discrete_outcome=False,
        prepared_manifest_path=prepared_manifest_path,
        model_artifact_path=model_artifact_path,
        metrics_report_path=metrics_report_path,
        validation_scores_path=validation_scores_path,
        test_scores_path=test_scores_path,
        random_seed=random_seed,
        propensity_model_params=propensity_model_params,
        regression_model_params=regression_model_params,
        final_model_params=final_model_params,
        cv=cv,
    )
