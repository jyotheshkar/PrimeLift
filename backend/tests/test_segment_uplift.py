"""Tests for the Phase 4 segment-level uplift analysis."""

from __future__ import annotations

import pandas as pd
import pytest

from primelift.uplift import (
    DEFAULT_GROUP_COLUMNS,
    DimensionUpliftReport,
    GroupUpliftResult,
    UpliftAnalysisReport,
    analyze_default_uplift_dimensions,
    analyze_group_uplift,
)


def test_group_uplift_sorts_results_by_uplift_descending() -> None:
    """Group uplift results should be ordered from strongest positive uplift to weakest."""

    dataset = pd.DataFrame(
        {
            "segment": [
                "A",
                "A",
                "A",
                "A",
                "B",
                "B",
                "B",
                "B",
                "C",
                "C",
                "C",
                "C",
            ],
            "treatment": [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
            "conversion": [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1],
        }
    )

    report = analyze_group_uplift(
        dataset=dataset,
        group_column="segment",
        bootstrap_samples=100,
        confidence_level=0.95,
        random_seed=3,
        min_group_size_per_arm=2,
    )

    assert isinstance(report, DimensionUpliftReport)
    assert [result.group_value for result in report.results] == ["A", "B", "C"]
    assert [result.uplift for result in report.results] == pytest.approx([1.0, 0.0, -1.0])
    assert report.results[0].confidence_indicator == "positive"
    assert report.results[-1].confidence_indicator == "negative"


def test_group_uplift_marks_small_groups_as_insufficient_for_ci() -> None:
    """Small treatment arms should skip group-level CI computation."""

    dataset = pd.DataFrame(
        {
            "device_type": ["mobile", "mobile", "desktop", "desktop"],
            "treatment": [1, 0, 1, 0],
            "conversion": [1, 0, 1, 1],
        }
    )

    report = analyze_group_uplift(
        dataset=dataset,
        group_column="device_type",
        bootstrap_samples=50,
        min_group_size_per_arm=2,
    )

    for result in report.results:
        assert isinstance(result, GroupUpliftResult)
        assert result.confidence_indicator == "insufficient_data"
        assert result.ci_lower is None
        assert result.ci_upper is None


def test_default_uplift_dimensions_return_expected_reports() -> None:
    """The default Phase 4 analysis should return one report per configured dimension."""

    dataset = pd.DataFrame(
        {
            "segment": ["A", "A", "B", "B"],
            "london_borough": ["Camden", "Camden", "Hackney", "Hackney"],
            "device_type": ["mobile", "desktop", "mobile", "desktop"],
            "channel": ["email", "email", "paid_social", "paid_social"],
            "treatment": [1, 0, 1, 0],
            "conversion": [1, 0, 0, 1],
        }
    )

    report = analyze_default_uplift_dimensions(
        dataset=dataset,
        bootstrap_samples=20,
        min_group_size_per_arm=1,
    )

    assert isinstance(report, UpliftAnalysisReport)
    assert report.group_columns == list(DEFAULT_GROUP_COLUMNS)
    assert [dimension.group_column for dimension in report.reports] == list(
        DEFAULT_GROUP_COLUMNS
    )


def test_group_uplift_rejects_missing_group_column() -> None:
    """Requesting a missing grouping column should fail fast."""

    dataset = pd.DataFrame(
        {
            "treatment": [1, 0],
            "conversion": [1, 0],
        }
    )

    with pytest.raises(ValueError, match="Missing required group column"):
        analyze_group_uplift(dataset=dataset, group_column="segment")
