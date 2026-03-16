"""Tests for the revised Phase 3 DRLearner revenue slice."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from primelift.causal import (
    DRLEARNER_REVENUE_SCORE_COLUMN,
    DRLearnerTrainingReport,
    load_trained_drlearner_revenue_bundle,
    train_drlearner_revenue_model,
)
from primelift.data.generator import generate_london_campaign_users
from primelift.data.preparation import prepare_model_ready_datasets


@pytest.fixture(scope="module")
def prepared_manifest(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a small prepared dataset manifest for DRLearner revenue tests."""

    tmp_path = tmp_path_factory.mktemp("drlearner_revenue")
    dataset = generate_london_campaign_users(row_count=4000, seed=42)
    summary = prepare_model_ready_datasets(
        dataset=dataset,
        input_dataset_path=tmp_path / "raw.csv",
        train_output_path=tmp_path / "train.csv",
        validation_output_path=tmp_path / "validation.csv",
        test_output_path=tmp_path / "test.csv",
        preprocessor_artifact_path=tmp_path / "feature_preprocessor.joblib",
        manifest_path=tmp_path / "prepared_manifest.json",
    )
    return Path(summary.manifest_path)


def test_train_drlearner_revenue_model_saves_artifacts_and_scores(
    prepared_manifest: Path, tmp_path: Path
) -> None:
    """Training should write the model bundle, metric report, and scored holdout splits."""

    report = train_drlearner_revenue_model(
        prepared_manifest_path=prepared_manifest,
        model_artifact_path=tmp_path / "drlearner_revenue.joblib",
        metrics_report_path=tmp_path / "drlearner_revenue_report.json",
        validation_scores_path=tmp_path / "validation_scores.csv",
        test_scores_path=tmp_path / "test_scores.csv",
        random_seed=42,
        propensity_model_params={"n_estimators": 20},
        regression_model_params={"n_estimators": 20},
        final_model_params={"n_estimators": 15},
        cv=2,
    )

    assert isinstance(report, DRLearnerTrainingReport)
    assert report.model_name == "drlearner_revenue"
    assert Path(report.model_artifact_path).exists()
    assert Path(report.metrics_report_path).exists()
    assert report.feature_column_count > 0
    assert len(report.split_evaluations) == 2
    assert report.config.outcome_column == "revenue"
    assert report.config.discrete_outcome is False


def test_drlearner_revenue_scored_outputs_include_prediction_column(
    prepared_manifest: Path, tmp_path: Path
) -> None:
    """The saved scored split files should contain the DRLearner revenue prediction column."""

    report = train_drlearner_revenue_model(
        prepared_manifest_path=prepared_manifest,
        model_artifact_path=tmp_path / "drlearner_revenue.joblib",
        metrics_report_path=tmp_path / "drlearner_revenue_report.json",
        validation_scores_path=tmp_path / "validation_scores.csv",
        test_scores_path=tmp_path / "test_scores.csv",
        random_seed=7,
        propensity_model_params={"n_estimators": 15},
        regression_model_params={"n_estimators": 15},
        final_model_params={"n_estimators": 10},
        cv=2,
    )

    for split_evaluation in report.split_evaluations:
        scored_frame = pd.read_csv(split_evaluation.score_output_path)
        assert DRLEARNER_REVENUE_SCORE_COLUMN in scored_frame.columns
        assert scored_frame[DRLEARNER_REVENUE_SCORE_COLUMN].notnull().all()
        assert split_evaluation.row_count == len(scored_frame)


def test_saved_drlearner_revenue_bundle_can_be_loaded(
    prepared_manifest: Path, tmp_path: Path
) -> None:
    """The persisted DRLearner revenue bundle should be reloadable from disk."""

    model_artifact_path = tmp_path / "drlearner_revenue.joblib"
    train_drlearner_revenue_model(
        prepared_manifest_path=prepared_manifest,
        model_artifact_path=model_artifact_path,
        metrics_report_path=tmp_path / "drlearner_revenue_report.json",
        validation_scores_path=tmp_path / "validation_scores.csv",
        test_scores_path=tmp_path / "test_scores.csv",
        random_seed=11,
        propensity_model_params={"n_estimators": 12},
        regression_model_params={"n_estimators": 12},
        final_model_params={"n_estimators": 8},
        cv=2,
    )

    bundle = load_trained_drlearner_revenue_bundle(model_artifact_path)

    assert bundle["model_name"] == "drlearner_revenue"
    assert bundle["score_column"] == DRLEARNER_REVENUE_SCORE_COLUMN
    assert bundle["outcome_column"] == "revenue"
    assert len(bundle["feature_columns"]) > 0
