"""Tests for the first Phase 5 decision-ranking slice."""

from __future__ import annotations

import pandas as pd
import pytest

from primelift.decision import (
    PositiveSegmentRankingReport,
    build_positive_segment_ranking,
    rank_positive_uplift_segments,
)
from primelift.uplift import DimensionUpliftReport, GroupUpliftResult


def _build_segment_report() -> DimensionUpliftReport:
    """Create a deterministic segment uplift report for decision tests."""

    return DimensionUpliftReport(
        group_column="segment",
        outcome_column="conversion",
        result_count=4,
        results=[
            GroupUpliftResult(
                group_column="segment",
                group_value="High Intent Returners",
                outcome_column="conversion",
                treated_conversion_rate=0.18,
                control_conversion_rate=0.12,
                uplift=0.06,
                relative_uplift=0.5,
                group_size=1000,
                treated_count=500,
                control_count=500,
                ci_lower=0.02,
                ci_upper=0.09,
                confidence_level=0.95,
                bootstrap_samples=100,
                confidence_indicator="positive",
            ),
            GroupUpliftResult(
                group_column="segment",
                group_value="Young Professionals",
                outcome_column="conversion",
                treated_conversion_rate=0.11,
                control_conversion_rate=0.08,
                uplift=0.03,
                relative_uplift=0.375,
                group_size=1200,
                treated_count=620,
                control_count=580,
                ci_lower=-0.01,
                ci_upper=0.06,
                confidence_level=0.95,
                bootstrap_samples=100,
                confidence_indicator="uncertain",
            ),
            GroupUpliftResult(
                group_column="segment",
                group_value="Families",
                outcome_column="conversion",
                treated_conversion_rate=0.10,
                control_conversion_rate=0.10,
                uplift=0.0,
                relative_uplift=0.0,
                group_size=800,
                treated_count=410,
                control_count=390,
                ci_lower=-0.03,
                ci_upper=0.03,
                confidence_level=0.95,
                bootstrap_samples=100,
                confidence_indicator="uncertain",
            ),
            GroupUpliftResult(
                group_column="segment",
                group_value="Window Shoppers",
                outcome_column="conversion",
                treated_conversion_rate=0.03,
                control_conversion_rate=0.05,
                uplift=-0.02,
                relative_uplift=-0.4,
                group_size=900,
                treated_count=450,
                control_count=450,
                ci_lower=-0.05,
                ci_upper=-0.01,
                confidence_level=0.95,
                bootstrap_samples=100,
                confidence_indicator="negative",
            ),
        ],
    )


def test_rank_positive_uplift_segments_filters_and_orders_results() -> None:
    """Only positive segments should remain, ordered from strongest uplift to weakest."""

    report = rank_positive_uplift_segments(_build_segment_report(), top_n=2)

    assert isinstance(report, PositiveSegmentRankingReport)
    assert report.ranked_segment_count == 2
    assert [segment.segment for segment in report.ranked_segments] == [
        "High Intent Returners",
        "Young Professionals",
    ]
    assert report.ranked_segments[0].estimated_incremental_conversions_per_1000 == pytest.approx(
        60.0
    )


def test_rank_positive_uplift_segments_can_return_no_candidates() -> None:
    """A fully non-positive report should produce an empty decision list."""

    non_positive_report = DimensionUpliftReport(
        group_column="segment",
        outcome_column="conversion",
        result_count=1,
        results=[
            GroupUpliftResult(
                group_column="segment",
                group_value="Window Shoppers",
                outcome_column="conversion",
                treated_conversion_rate=0.02,
                control_conversion_rate=0.03,
                uplift=-0.01,
                relative_uplift=-0.3333333333,
                group_size=600,
                treated_count=300,
                control_count=300,
                ci_lower=-0.03,
                ci_upper=0.0,
                confidence_level=0.95,
                bootstrap_samples=100,
                confidence_indicator="negative",
            )
        ],
    )

    report = rank_positive_uplift_segments(non_positive_report)

    assert report.ranked_segment_count == 0
    assert report.ranked_segments == []


def test_rank_positive_uplift_segments_rejects_non_segment_reports() -> None:
    """The first Phase 5 slice should stay scoped to segment-level actioning."""

    borough_report = DimensionUpliftReport(
        group_column="london_borough",
        outcome_column="conversion",
        result_count=1,
        results=[],
    )

    with pytest.raises(ValueError, match="supports only segment-level uplift reports"):
        rank_positive_uplift_segments(borough_report)


def test_build_positive_segment_ranking_runs_end_to_end() -> None:
    """The convenience wrapper should connect dataset analysis to decision output."""

    dataset = pd.DataFrame(
        {
            "segment": ["A", "A", "A", "A", "B", "B", "B", "B"],
            "treatment": [1, 1, 0, 0, 1, 1, 0, 0],
            "conversion": [1, 1, 0, 0, 0, 1, 0, 1],
        }
    )

    report = build_positive_segment_ranking(
        dataset=dataset,
        bootstrap_samples=20,
        min_group_size_per_arm=1,
    )

    assert isinstance(report, PositiveSegmentRankingReport)
    assert report.group_column == "segment"
    assert report.ranked_segment_count == 1
    assert report.ranked_segments[0].segment == "A"
