"""Tests for revised Phase 2 model-ready dataset preparation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from primelift.data.generator import generate_london_campaign_users
from primelift.data.preparation import (
    load_prepared_dataset_summary,
    prepare_model_ready_datasets,
    split_modeling_dataset,
)
from primelift.features.preprocessing import (
    EXCLUDED_FROM_MODEL_FEATURES,
    fit_model_preprocessor,
    transform_model_features,
)


@pytest.fixture(scope="module")
def modeling_dataset() -> pd.DataFrame:
    """Generate a manageable synthetic dataset for preparation tests."""

    return generate_london_campaign_users(row_count=5000, seed=42)


def test_split_modeling_dataset_covers_all_rows_without_overlap(
    modeling_dataset: pd.DataFrame,
) -> None:
    """Train, validation, and test splits should be exhaustive and disjoint."""

    split_frames = split_modeling_dataset(modeling_dataset)

    total_rows = sum(len(split_frame) for split_frame in split_frames.values())
    assert total_rows == len(modeling_dataset)

    combined_user_ids = set()
    for split_frame in split_frames.values():
        user_ids = set(split_frame["user_id"])
        assert combined_user_ids.isdisjoint(user_ids)
        combined_user_ids.update(user_ids)


def test_preprocessor_excludes_leakage_columns_from_transformed_features(
    modeling_dataset: pd.DataFrame,
) -> None:
    """The preprocessing pipeline should only learn from allowed model features."""

    split_frames = split_modeling_dataset(modeling_dataset)
    preprocessor = fit_model_preprocessor(split_frames["train"])
    transformed_features = transform_model_features(split_frames["validation"], preprocessor)

    assert transformed_features.shape[0] == len(split_frames["validation"])
    for excluded_column in EXCLUDED_FROM_MODEL_FEATURES:
        assert excluded_column not in transformed_features.columns


def test_prepare_model_ready_datasets_writes_outputs_and_manifest(
    modeling_dataset: pd.DataFrame, tmp_path: Path
) -> None:
    """Preparing the dataset should save split outputs, a manifest, and a preprocessor artifact."""

    summary = prepare_model_ready_datasets(
        dataset=modeling_dataset,
        input_dataset_path=tmp_path / "raw.csv",
        train_output_path=tmp_path / "train.csv",
        validation_output_path=tmp_path / "validation.csv",
        test_output_path=tmp_path / "test.csv",
        preprocessor_artifact_path=tmp_path / "feature_preprocessor.joblib",
        manifest_path=tmp_path / "prepared_manifest.json",
    )

    assert summary.transformed_feature_count > summary.raw_feature_count
    assert Path(summary.preprocessor_artifact_path).exists()
    assert Path(summary.manifest_path).exists()
    for split_summary in summary.splits:
        assert Path(split_summary.file_path).exists()

    loaded_summary = load_prepared_dataset_summary(Path(summary.manifest_path))
    assert loaded_summary.transformed_feature_count == summary.transformed_feature_count
    assert [split.split_name for split in loaded_summary.splits] == ["train", "validation", "test"]


def test_default_split_sizes_are_expected(modeling_dataset: pd.DataFrame) -> None:
    """The default split fractions should produce a 70/15/15 partition."""

    split_frames = split_modeling_dataset(modeling_dataset)

    assert len(split_frames["train"]) == 3500
    assert len(split_frames["validation"]) == 750
    assert len(split_frames["test"]) == 750
