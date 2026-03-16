"""Tests for the revised Phase 3 CausalForestDML conversion slice."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from primelift.causal import (
    CAUSAL_FOREST_CONVERSION_SCORE_COLUMN,
    CausalForestTrainingReport,
    load_trained_causal_forest_bundle,
    train_causal_forest_conversion_model,
)
from primelift.data.generator import generate_london_campaign_users
from primelift.data.preparation import prepare_model_ready_datasets


@pytest.fixture(scope="module")
def prepared_manifest(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a small prepared dataset manifest for CausalForest tests."""

    tmp_path = tmp_path_factory.mktemp("causal_forest")
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


def test_train_causal_forest_conversion_model_saves_artifacts_and_scores(
    prepared_manifest: Path, tmp_path: Path
) -> None:
    """Training should write the model bundle, metric report, and scored holdout splits."""

    report = train_causal_forest_conversion_model(
        prepared_manifest_path=prepared_manifest,
        model_artifact_path=tmp_path / "causal_forest.joblib",
        metrics_report_path=tmp_path / "causal_forest_report.json",
        validation_scores_path=tmp_path / "validation_scores.csv",
        test_scores_path=tmp_path / "test_scores.csv",
        random_seed=42,
        model_y_params={"n_estimators": 20},
        model_t_params={"n_estimators": 20},
        n_estimators=40,
        min_samples_leaf=20,
        cv=2,
    )

    assert isinstance(report, CausalForestTrainingReport)
    assert report.model_name == "causal_forest_conversion"
    assert Path(report.model_artifact_path).exists()
    assert Path(report.metrics_report_path).exists()
    assert report.feature_column_count > 0
    assert len(report.split_evaluations) == 2


def test_causal_forest_scored_outputs_include_prediction_and_interval_columns(
    prepared_manifest: Path, tmp_path: Path
) -> None:
    """The saved scored split files should contain the forest prediction and interval columns."""

    report = train_causal_forest_conversion_model(
        prepared_manifest_path=prepared_manifest,
        model_artifact_path=tmp_path / "causal_forest.joblib",
        metrics_report_path=tmp_path / "causal_forest_report.json",
        validation_scores_path=tmp_path / "validation_scores.csv",
        test_scores_path=tmp_path / "test_scores.csv",
        random_seed=7,
        model_y_params={"n_estimators": 15},
        model_t_params={"n_estimators": 15},
        n_estimators=40,
        min_samples_leaf=20,
        cv=2,
    )

    for split_evaluation in report.split_evaluations:
        scored_frame = pd.read_csv(split_evaluation.score_output_path)
        assert CAUSAL_FOREST_CONVERSION_SCORE_COLUMN in scored_frame.columns
        assert f"{CAUSAL_FOREST_CONVERSION_SCORE_COLUMN}_ci_lower" in scored_frame.columns
        assert f"{CAUSAL_FOREST_CONVERSION_SCORE_COLUMN}_ci_upper" in scored_frame.columns
        assert scored_frame[CAUSAL_FOREST_CONVERSION_SCORE_COLUMN].notnull().all()
        assert split_evaluation.row_count == len(scored_frame)


def test_saved_causal_forest_bundle_can_be_loaded(
    prepared_manifest: Path, tmp_path: Path
) -> None:
    """The persisted CausalForest bundle should be reloadable from disk."""

    model_artifact_path = tmp_path / "causal_forest.joblib"
    train_causal_forest_conversion_model(
        prepared_manifest_path=prepared_manifest,
        model_artifact_path=model_artifact_path,
        metrics_report_path=tmp_path / "causal_forest_report.json",
        validation_scores_path=tmp_path / "validation_scores.csv",
        test_scores_path=tmp_path / "test_scores.csv",
        random_seed=11,
        model_y_params={"n_estimators": 12},
        model_t_params={"n_estimators": 12},
        n_estimators=40,
        min_samples_leaf=20,
        cv=2,
    )

    bundle = load_trained_causal_forest_bundle(model_artifact_path)

    assert bundle["model_name"] == "causal_forest_conversion"
    assert bundle["score_column"] == CAUSAL_FOREST_CONVERSION_SCORE_COLUMN
    assert len(bundle["feature_columns"]) > 0
