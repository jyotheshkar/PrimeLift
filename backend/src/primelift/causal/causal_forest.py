"""CausalForestDML training and scoring utilities for revised Phase 3."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from econml.dml import CausalForestDML
from lightgbm import LGBMClassifier, LGBMRegressor
from pydantic import BaseModel, ConfigDict

from primelift.causal.ate import analyze_average_treatment_effect, estimate_average_treatment_effect
from primelift.data.preparation import PreparedDatasetSummary, load_prepared_dataset_summary
from primelift.utils.paths import (
    DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH,
    DEFAULT_CAUSAL_FOREST_CONVERSION_MODEL_PATH,
    DEFAULT_CAUSAL_FOREST_CONVERSION_TEST_SCORES_PATH,
    DEFAULT_CAUSAL_FOREST_CONVERSION_VALIDATION_SCORES_PATH,
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
CAUSAL_FOREST_CONVERSION_SCORE_COLUMN = "predicted_cate_causal_forest_conversion"


class CausalForestTrainingConfig(BaseModel):
    """Serializable configuration used for the CausalForestDML conversion model."""

    model_config = ConfigDict(frozen=True)

    outcome_column: str
    treatment_column: str
    score_column: str
    model_y_class: str
    model_t_class: str
    model_y_params: dict[str, Any]
    model_t_params: dict[str, Any]
    n_estimators: int
    max_depth: int | None
    min_samples_leaf: int
    max_samples: float
    cv: int


class CausalForestSplitEvaluation(BaseModel):
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
    mean_interval_lower: float
    mean_interval_upper: float
    mean_interval_width: float
    top_decile_size: int
    top_decile_mean_predicted_cate: float
    top_decile_observed_ate: float | None
    bottom_decile_size: int
    bottom_decile_mean_predicted_cate: float
    bottom_decile_observed_ate: float | None
    top_segments_by_mean_predicted_cate: list[dict[str, float | str]]
    bottom_segments_by_mean_predicted_cate: list[dict[str, float | str]]
    score_output_path: str


class CausalForestTrainingReport(BaseModel):
    """Serializable report for the revised Phase 3 CausalForestDML conversion slice."""

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
    config: CausalForestTrainingConfig
    baseline_validation_analysis: dict[str, float | int | str | None]
    split_evaluations: list[CausalForestSplitEvaluation]


def _load_prepared_split_frame(split_path: str) -> pd.DataFrame:
    """Load one prepared split from disk."""

    return pd.read_csv(split_path)


def _extract_feature_columns(split_frame: pd.DataFrame) -> list[str]:
    """Extract transformed feature columns from a prepared split frame."""

    return [column for column in split_frame.columns if column not in PREPARED_META_COLUMNS]


def _build_lgbm_regressor(
    random_seed: int, overrides: dict[str, Any] | None = None
) -> LGBMRegressor:
    """Build a reproducible LightGBM regressor for the outcome nuisance model."""

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


def _build_lgbm_classifier(
    random_seed: int, overrides: dict[str, Any] | None = None
) -> LGBMClassifier:
    """Build a reproducible LightGBM classifier for the treatment nuisance model."""

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
    interval_lower: np.ndarray,
    interval_upper: np.ndarray,
    score_column: str,
) -> pd.DataFrame:
    """Build the saved scored output frame for one split."""

    output_frame = split_frame.loc[:, list(PREPARED_META_COLUMNS)].copy()
    output_frame[score_column] = scores.astype(float)
    output_frame[f"{score_column}_ci_lower"] = interval_lower.astype(float)
    output_frame[f"{score_column}_ci_upper"] = interval_upper.astype(float)
    return output_frame


def _evaluate_scored_split(
    split_name: str,
    split_frame: pd.DataFrame,
    scores: np.ndarray,
    interval_lower: np.ndarray,
    interval_upper: np.ndarray,
    score_output_path: Path,
    score_column: str,
) -> CausalForestSplitEvaluation:
    """Summarize holdout scoring behavior for one split."""

    scored_frame = _build_scored_output_frame(
        split_frame=split_frame,
        scores=scores,
        interval_lower=interval_lower,
        interval_upper=interval_upper,
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

    return CausalForestSplitEvaluation(
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
        mean_interval_lower=float(np.mean(interval_lower)),
        mean_interval_upper=float(np.mean(interval_upper)),
        mean_interval_width=float(np.mean(interval_upper - interval_lower)),
        top_decile_size=int(len(top_frame)),
        top_decile_mean_predicted_cate=float(top_frame[score_column].mean()),
        top_decile_observed_ate=_safe_observed_ate(top_frame),
        bottom_decile_size=int(len(bottom_frame)),
        bottom_decile_mean_predicted_cate=float(bottom_frame[score_column].mean()),
        bottom_decile_observed_ate=_safe_observed_ate(bottom_frame),
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


def load_trained_causal_forest_bundle(model_artifact_path: Path) -> dict[str, Any]:
    """Load the saved CausalForestDML bundle from disk."""

    return joblib.load(model_artifact_path)


def train_causal_forest_conversion_model(
    prepared_manifest_path: Path = DEFAULT_PREPROCESSING_MANIFEST_PATH,
    model_artifact_path: Path = DEFAULT_CAUSAL_FOREST_CONVERSION_MODEL_PATH,
    metrics_report_path: Path = DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH,
    validation_scores_path: Path = DEFAULT_CAUSAL_FOREST_CONVERSION_VALIDATION_SCORES_PATH,
    test_scores_path: Path = DEFAULT_CAUSAL_FOREST_CONVERSION_TEST_SCORES_PATH,
    random_seed: int = 42,
    model_y_params: dict[str, Any] | None = None,
    model_t_params: dict[str, Any] | None = None,
    n_estimators: int = 80,
    max_depth: int | None = None,
    min_samples_leaf: int = 40,
    max_samples: float = 0.45,
    cv: int = 2,
) -> CausalForestTrainingReport:
    """Train the revised Phase 3 CausalForestDML conversion model and score holdout splits."""

    ensure_project_directories()
    prepared_summary: PreparedDatasetSummary = load_prepared_dataset_summary(prepared_manifest_path)
    split_paths = {split.split_name: split.file_path for split in prepared_summary.splits}

    train_frame = _load_prepared_split_frame(split_paths["train"])
    validation_frame = _load_prepared_split_frame(split_paths["validation"])
    test_frame = _load_prepared_split_frame(split_paths["test"])

    feature_columns = _extract_feature_columns(train_frame)
    X_train = train_frame.loc[:, feature_columns]
    y_train = train_frame["conversion"].to_numpy(dtype=float)
    t_train = train_frame["treatment"].to_numpy(dtype=int)

    forest = CausalForestDML(
        model_y=_build_lgbm_regressor(random_seed=random_seed, overrides=model_y_params),
        model_t=_build_lgbm_classifier(random_seed=random_seed, overrides=model_t_params),
        discrete_treatment=True,
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        max_samples=max_samples,
        cv=cv,
        subforest_size=4,
        random_state=random_seed,
        n_jobs=1,
        verbose=0,
    )

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMRegressor was fitted with feature names",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMClassifier was fitted with feature names",
            category=UserWarning,
        )
        forest.fit(y_train, t_train, X=X_train)

    model_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model_name": "causal_forest_conversion",
        "estimator": forest,
        "feature_columns": feature_columns,
        "score_column": CAUSAL_FOREST_CONVERSION_SCORE_COLUMN,
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
            message="X does not have valid feature names, but LGBMClassifier was fitted with feature names",
            category=UserWarning,
        )
        validation_scores = np.asarray(
            forest.effect(validation_frame.loc[:, feature_columns]),
            dtype=float,
        ).reshape(-1)
        test_scores = np.asarray(
            forest.effect(test_frame.loc[:, feature_columns]),
            dtype=float,
        ).reshape(-1)
        validation_interval = forest.effect_interval(
            validation_frame.loc[:, feature_columns],
            alpha=0.05,
        )
        test_interval = forest.effect_interval(
            test_frame.loc[:, feature_columns],
            alpha=0.05,
        )

    validation_lower = np.asarray(validation_interval[0], dtype=float).reshape(-1)
    validation_upper = np.asarray(validation_interval[1], dtype=float).reshape(-1)
    test_lower = np.asarray(test_interval[0], dtype=float).reshape(-1)
    test_upper = np.asarray(test_interval[1], dtype=float).reshape(-1)

    split_evaluations = [
        _evaluate_scored_split(
            split_name="validation",
            split_frame=validation_frame,
            scores=validation_scores,
            interval_lower=validation_lower,
            interval_upper=validation_upper,
            score_output_path=validation_scores_path,
            score_column=CAUSAL_FOREST_CONVERSION_SCORE_COLUMN,
        ),
        _evaluate_scored_split(
            split_name="test",
            split_frame=test_frame,
            scores=test_scores,
            interval_lower=test_lower,
            interval_upper=test_upper,
            score_output_path=test_scores_path,
            score_column=CAUSAL_FOREST_CONVERSION_SCORE_COLUMN,
        ),
    ]

    config = CausalForestTrainingConfig(
        outcome_column="conversion",
        treatment_column="treatment",
        score_column=CAUSAL_FOREST_CONVERSION_SCORE_COLUMN,
        model_y_class="lightgbm.LGBMRegressor",
        model_t_class="lightgbm.LGBMClassifier",
        model_y_params=_build_lgbm_regressor(random_seed, model_y_params).get_params(),
        model_t_params=_build_lgbm_classifier(random_seed, model_t_params).get_params(),
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        max_samples=max_samples,
        cv=cv,
    )

    validation_baseline = analyze_average_treatment_effect(
        dataset=validation_frame,
        outcome_column="conversion",
        treatment_column="treatment",
        bootstrap_samples=300,
        random_seed=random_seed,
    )

    report = CausalForestTrainingReport(
        model_name="causal_forest_conversion",
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
