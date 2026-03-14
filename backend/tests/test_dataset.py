"""Tests for the synthetic London campaign dataset generator."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from primelift.data.generator import generate_london_campaign_users, save_dataset
from primelift.data.schema import DATASET_RANDOM_SEED, DATASET_ROW_COUNT, REQUIRED_COLUMNS


@pytest.fixture(scope="module")
def generated_dataset() -> pd.DataFrame:
    """Generate the canonical 100k dataset once for the test module."""

    return generate_london_campaign_users(
        row_count=DATASET_ROW_COUNT,
        seed=DATASET_RANDOM_SEED,
    )


def test_dataset_row_count_is_exact(generated_dataset: pd.DataFrame) -> None:
    """The synthetic dataset should contain exactly 100000 rows."""

    assert len(generated_dataset) == DATASET_ROW_COUNT


def test_required_columns_exist(generated_dataset: pd.DataFrame) -> None:
    """All required schema columns should be present."""

    assert list(generated_dataset.columns) == REQUIRED_COLUMNS


def test_treatment_values_are_binary(generated_dataset: pd.DataFrame) -> None:
    """Treatment assignments should be encoded as 0 or 1 only."""

    assert set(generated_dataset["treatment"].unique()) <= {0, 1}


def test_conversion_values_are_binary(generated_dataset: pd.DataFrame) -> None:
    """Conversions should be encoded as 0 or 1 only."""

    assert set(generated_dataset["conversion"].unique()) <= {0, 1}


def test_revenue_is_zero_when_conversion_is_zero(generated_dataset: pd.DataFrame) -> None:
    """Revenue must remain zero for non-converted users."""

    no_conversion_rows = generated_dataset["conversion"] == 0
    assert (generated_dataset.loc[no_conversion_rows, "revenue"] == 0).all()


def test_csv_file_is_generated_successfully(
    generated_dataset: pd.DataFrame, tmp_path: Path
) -> None:
    """Saving the generated dataset should create a CSV on disk."""

    output_path = tmp_path / "london_campaign_users_100k.csv"
    saved_path = save_dataset(generated_dataset, output_path)

    assert saved_path.exists()
    loaded_dataset = pd.read_csv(saved_path)
    assert len(loaded_dataset) == DATASET_ROW_COUNT
