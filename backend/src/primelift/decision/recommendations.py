"""Rule-based Phase 5 decision helpers for turning uplift into actions."""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, ConfigDict

from primelift.uplift import DimensionUpliftReport, GroupUpliftResult, analyze_group_uplift

DEFAULT_DECISION_GROUP_COLUMN = "segment"


class RankedSegmentRecommendation(BaseModel):
    """Serializable recommendation for one positively responding segment."""

    model_config = ConfigDict(frozen=True)

    segment: str
    uplift: float
    relative_uplift: float | None
    group_size: int
    treated_count: int
    control_count: int
    treated_conversion_rate: float
    control_conversion_rate: float
    confidence_indicator: str
    estimated_incremental_conversions_per_1000: float
    rationale: str


class PositiveSegmentRankingReport(BaseModel):
    """Serializable ranking of the top positive segments for actioning."""

    model_config = ConfigDict(frozen=True)

    group_column: str
    outcome_column: str
    evaluated_segments: int
    ranked_segment_count: int
    min_uplift_threshold: float
    top_n: int | None
    ranked_segments: list[RankedSegmentRecommendation]


def _validate_top_n(top_n: int | None) -> None:
    """Validate the optional output cap."""

    if top_n is not None and top_n <= 0:
        raise ValueError("top_n must be a positive integer when provided.")


def _validate_segment_report(segment_report: DimensionUpliftReport) -> None:
    """Validate that the report is usable for the first Phase 5 segment ranking slice."""

    if segment_report.group_column != DEFAULT_DECISION_GROUP_COLUMN:
        raise ValueError("Phase 5 ranking currently supports only segment-level uplift reports.")


def _build_rationale(result: GroupUpliftResult) -> str:
    """Create a short explainable rationale for the decision output."""

    confidence_messages = {
        "positive": "bootstrap confidence stays above zero",
        "uncertain": "point estimate is positive but the interval crosses zero",
        "insufficient_data": "point estimate is positive but the group is still too small for a stable interval",
    }
    confidence_message = confidence_messages.get(
        result.confidence_indicator,
        "uplift signal should be reviewed before actioning",
    )
    incremental_conversions = max(result.uplift, 0.0) * 1000.0
    return (
        f"Positive uplift of {result.uplift:.4f} suggests about "
        f"{incremental_conversions:.1f} incremental conversions per 1000 targeted users; "
        f"{confidence_message}."
    )


def rank_positive_uplift_segments(
    segment_report: DimensionUpliftReport,
    min_uplift: float = 0.0,
    top_n: int | None = None,
) -> PositiveSegmentRankingReport:
    """Filter and rank the positive segment uplift results from strongest to weakest."""

    _validate_top_n(top_n)
    _validate_segment_report(segment_report)

    ranked_segments = [
        RankedSegmentRecommendation(
            segment=result.group_value,
            uplift=result.uplift,
            relative_uplift=result.relative_uplift,
            group_size=result.group_size,
            treated_count=result.treated_count,
            control_count=result.control_count,
            treated_conversion_rate=result.treated_conversion_rate,
            control_conversion_rate=result.control_conversion_rate,
            confidence_indicator=result.confidence_indicator,
            estimated_incremental_conversions_per_1000=max(result.uplift, 0.0) * 1000.0,
            rationale=_build_rationale(result),
        )
        for result in segment_report.results
        if result.uplift > min_uplift
    ]

    if top_n is not None:
        ranked_segments = ranked_segments[:top_n]

    return PositiveSegmentRankingReport(
        group_column=segment_report.group_column,
        outcome_column=segment_report.outcome_column,
        evaluated_segments=segment_report.result_count,
        ranked_segment_count=len(ranked_segments),
        min_uplift_threshold=min_uplift,
        top_n=top_n,
        ranked_segments=ranked_segments,
    )


def build_positive_segment_ranking(
    dataset: pd.DataFrame,
    outcome_column: str = "conversion",
    treatment_column: str = "treatment",
    bootstrap_samples: int = 200,
    confidence_level: float = 0.95,
    random_seed: int = 42,
    min_group_size_per_arm: int = 25,
    min_uplift: float = 0.0,
    top_n: int | None = None,
) -> PositiveSegmentRankingReport:
    """Run the Phase 4 segment analysis and convert it into a first Phase 5 ranking."""

    segment_report = analyze_group_uplift(
        dataset=dataset,
        group_column=DEFAULT_DECISION_GROUP_COLUMN,
        outcome_column=outcome_column,
        treatment_column=treatment_column,
        bootstrap_samples=bootstrap_samples,
        confidence_level=confidence_level,
        random_seed=random_seed,
        min_group_size_per_arm=min_group_size_per_arm,
    )
    return rank_positive_uplift_segments(
        segment_report=segment_report,
        min_uplift=min_uplift,
        top_n=top_n,
    )
