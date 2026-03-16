"""XLearner training and scoring utilities for revised Phase 3."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from econml.metalearners import XLearner
from lightgbm import LGBMRegressor
from pydantic import BaseModel, ConfigDict
from sklearn.linear_model import LogisticRegression

from primelift.causal.ate import analyze_average_treatment_effect, estimate_average_treatment_effect
from primelift.data.preparation import PreparedDatasetSummary, load_prepared_dataset_summary
from primelift.utils.paths import (
    DEFAULT_PREPROCESSING_MANIFEST_PATH,
    DEFAULT_XLEARNER_CONVERSION_METRICS_PATH,
    DEFAULT_XLEARNER_CONVERSION_MODEL_PATH,
    DEFAULT_XLEARNER_CONVERSION_TEST_SCORES_PATH,
    DEFAULT_XLEARNER_CONVERSION_VALIDATION_SCORES_PATH,
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
XLEARNER_CONVERSION_SCORE_COLUMN = "predicted_cate_xlearner_conversion"


class XLearnerTrainingConfig(BaseModel):
    """Serializable configuration used for the XLearner conversion model."""

    model_config = ConfigDict(frozen=True)

    outcome_column: str
    treatment_column: str
    score_column: str
    base_model_class: str
    cate_model_class: str
    propensity_model_class: str
    base_model_params: dict[str, Any]
    cate_model_params: dict[str, Any]
    propensity_model_params: dict[str, Any]


class XLearnerSplitEvaluation(BaseModel):
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


class XLearnerTrainingReport(BaseModel):
    """Serializable report for the revised Phase 3 XLearner conversion slice."""

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
    config: XLearnerTrainingConfig
    baseline_validation_analysis: dict[str, float | int | str | None]
    split_evaluations: list[XLearnerSplitEvaluation]


def _load_prepared_split_frame(split_path: str) -> pd.DataFrame:
    """Load one prepared split from disk."""

    return pd.read_csv(split_path)


def _extract_feature_columns(split_frame: pd.DataFrame) -> list[str]:
    """Extract transformed feature columns from a prepared split frame."""

    return [column for column in split_frame.columns if column not in PREPARED_META_COLUMNS]


def _build_lgbm_regressor(random_seed: int, overrides: dict[str, Any] | None = None) -> LGBMRegressor:
    """Build a reproducible LightGBM regressor for XLearner components."""

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


def _build_propensity_model(
    random_seed: int, overrides: dict[str, Any] | None = None
) -> LogisticRegression:
    """Build the propensity model used by XLearner."""

    parameters: dict[str, Any] = {
        "max_iter": 1000,
        "random_state": random_seed,
    }
    if overrides:
        parameters.update(overrides)
    return LogisticRegression(**parameters)


def _safe_observed_ate(split_frame: pd.DataFrame) -> float | None:
    """Compute ATE safely for a scored subset if both treatment arms are present."""

    try:
        return estimate_average_treatment_effect(
            dataset=split_frame,
            outcome_column="conversion",
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
) -> XLearnerSplitEvaluation:
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
    top_segments = [
        {"segment": segment_name, "mean_predicted_cate": float(mean_value)}
        for segment_name, mean_value in segment_means.head(3).items()
    ]
    bottom_segments = [
        {"segment": segment_name, "mean_predicted_cate": float(mean_value)}
        for segment_name, mean_value in segment_means.tail(3).sort_values().items()
    ]

    return XLearnerSplitEvaluation(
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
                outcome_column="conversion",
                treatment_column="treatment",
            ).ate
        ),
        top_decile_size=int(len(top_frame)),
        top_decile_mean_predicted_cate=float(top_frame[score_column].mean()),
        top_decile_observed_ate=_safe_observed_ate(top_frame),
        bottom_decile_size=int(len(bottom_frame)),
        bottom_decile_mean_predicted_cate=float(bottom_frame[score_column].mean()),
        bottom_decile_observed_ate=_safe_observed_ate(bottom_frame),
        top_segments_by_mean_predicted_cate=top_segments,
        bottom_segments_by_mean_predicted_cate=bottom_segments,
        score_output_path=str(score_output_path),
    )


def load_trained_xlearner_bundle(model_artifact_path: Path) -> dict[str, Any]:
    """Load the saved XLearner bundle from disk."""

    return joblib.load(model_artifact_path)


def train_xlearner_conversion_model(
    prepared_manifest_path: Path = DEFAULT_PREPROCESSING_MANIFEST_PATH,
    model_artifact_path: Path = DEFAULT_XLEARNER_CONVERSION_MODEL_PATH,
    metrics_report_path: Path = DEFAULT_XLEARNER_CONVERSION_METRICS_PATH,
    validation_scores_path: Path = DEFAULT_XLEARNER_CONVERSION_VALIDATION_SCORES_PATH,
    test_scores_path: Path = DEFAULT_XLEARNER_CONVERSION_TEST_SCORES_PATH,
    random_seed: int = 42,
    base_model_params: dict[str, Any] | None = None,
    cate_model_params: dict[str, Any] | None = None,
    propensity_model_params: dict[str, Any] | None = None,
) -> XLearnerTrainingReport:
    """Train the revised Phase 3 XLearner conversion model and score holdout splits."""

    ensure_project_directories()
    prepared_summary: PreparedDatasetSummary = load_prepared_dataset_summary(prepared_manifest_path)
    split_paths = {split.split_name: split.file_path for split in prepared_summary.splits}

    train_frame = _load_prepared_split_frame(split_paths["train"])
    validation_frame = _load_prepared_split_frame(split_paths["validation"])
    test_frame = _load_prepared_split_frame(split_paths["test"])

    feature_columns = _extract_feature_columns(train_frame)
    X_train = train_frame.loc[:, feature_columns].to_numpy(dtype=float)
    y_train = train_frame["conversion"].to_numpy(dtype=float)
    t_train = train_frame["treatment"].to_numpy(dtype=int)

    xlearner = XLearner(
        models=_build_lgbm_regressor(random_seed=random_seed, overrides=base_model_params),
        cate_models=_build_lgbm_regressor(
            random_seed=random_seed,
            overrides=cate_model_params or {"n_estimators": 80},
        ),
        propensity_model=_build_propensity_model(
            random_seed=random_seed,
            overrides=propensity_model_params,
        ),
    )
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMRegressor was fitted with feature names",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="'force_all_finite' was renamed to 'ensure_all_finite' in 1.6 and will be removed in 1.8.",
            category=FutureWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="scipy.optimize: The `disp` and `iprint` options of the L-BFGS-B solver are deprecated and will be removed in SciPy 1.18.0.",
            category=DeprecationWarning,
        )
        xlearner.fit(y_train, t_train, X=X_train)

    model_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model_name": "xlearner_conversion",
        "estimator": xlearner,
        "feature_columns": feature_columns,
        "score_column": XLEARNER_CONVERSION_SCORE_COLUMN,
        "outcome_column": "conversion",
        "treatment_column": "treatment",
        "random_seed": random_seed,
    }
    joblib.dump(bundle, model_artifact_path)

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMRegressor was fitted with feature names",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="'force_all_finite' was renamed to 'ensure_all_finite' in 1.6 and will be removed in 1.8.",
            category=FutureWarning,
        )
        validation_scores = xlearner.effect(
            validation_frame.loc[:, feature_columns].to_numpy(dtype=float)
        )
        test_scores = xlearner.effect(test_frame.loc[:, feature_columns].to_numpy(dtype=float))

    split_evaluations = [
        _evaluate_scored_split(
            split_name="validation",
            split_frame=validation_frame,
            scores=np.asarray(validation_scores, dtype=float),
            score_output_path=validation_scores_path,
            score_column=XLEARNER_CONVERSION_SCORE_COLUMN,
        ),
        _evaluate_scored_split(
            split_name="test",
            split_frame=test_frame,
            scores=np.asarray(test_scores, dtype=float),
            score_output_path=test_scores_path,
            score_column=XLEARNER_CONVERSION_SCORE_COLUMN,
        ),
    ]

    config = XLearnerTrainingConfig(
        outcome_column="conversion",
        treatment_column="treatment",
        score_column=XLEARNER_CONVERSION_SCORE_COLUMN,
        base_model_class="lightgbm.LGBMRegressor",
        cate_model_class="lightgbm.LGBMRegressor",
        propensity_model_class="sklearn.linear_model.LogisticRegression",
        base_model_params=_build_lgbm_regressor(random_seed, base_model_params).get_params(),
        cate_model_params=_build_lgbm_regressor(
            random_seed,
            cate_model_params or {"n_estimators": 80},
        ).get_params(),
        propensity_model_params=_build_propensity_model(
            random_seed, propensity_model_params
        ).get_params(),
    )

    validation_baseline = analyze_average_treatment_effect(
        dataset=validation_frame,
        outcome_column="conversion",
        treatment_column="treatment",
        bootstrap_samples=300,
        random_seed=random_seed,
    )

    report = XLearnerTrainingReport(
        model_name="xlearner_conversion",
        prepared_manifest_path=str(prepared_manifest_path),
        feature_column_count=len(feature_columns),
        feature_column_sample=feature_columns[:20],
        train_row_count=int(len(train_frame)),
        train_observed_ate=float(
            estimate_average_treatment_effect(
                dataset=train_frame,
                outcome_column="conversion",
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
