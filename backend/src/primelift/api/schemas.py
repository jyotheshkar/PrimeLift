"""Pydantic request and response contracts for the PrimeLift API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from primelift.evaluation.model_comparison import Phase3ModelComparisonReport
from primelift.evaluation.phase4_validation import Phase4DimensionValidationSummary
from primelift.decision.decision_closeout import Phase5DecisionCloseoutReport
from primelift.uplift.model_based_rollups import ModelBasedDimensionRollup


class HealthReadiness(BaseModel):
    """Readiness summary for the local PrimeLift backend state."""

    model_config = ConfigDict(frozen=True)

    dataset_ready: bool
    prepared_data_ready: bool
    phase5_closeout_ready: bool


class HealthResponse(BaseModel):
    """Typed response for the Phase 6 health endpoint."""

    model_config = ConfigDict(frozen=True)

    status: str
    service_name: str
    api_version: str
    current_phase: int
    timestamp_utc: str
    readiness: HealthReadiness


class DatasetSummaryResponse(BaseModel):
    """Typed dataset summary payload for the dataset generation endpoint."""

    model_config = ConfigDict(frozen=True)

    row_count: int
    columns: list[str]
    treatment_control_split: dict[str, int]
    conversion_rate: float
    segment_counts: dict[str, int]
    borough_counts: dict[str, int]


class DatasetGenerateRequest(BaseModel):
    """Typed request contract for the dataset generation endpoint."""

    model_config = ConfigDict(frozen=True)

    rows: int = Field(default=100_000, gt=0, description="Number of rows to generate.")
    seed: int = Field(default=42, description="Random seed for reproducible generation.")


class DatasetGenerateResponse(BaseModel):
    """Typed response contract for the dataset generation endpoint."""

    model_config = ConfigDict(frozen=True)

    status: str
    output_path: str
    seed: int
    summary: DatasetSummaryResponse


class DatasetSampleResponse(BaseModel):
    """Typed response contract for the dataset sample endpoint."""

    model_config = ConfigDict(frozen=True)

    status: str
    source_path: str
    requested_rows: int
    returned_rows: int
    available_rows: int
    columns: list[str]
    records: list[dict[str, Any]]


class ATEAnalysisResultResponse(BaseModel):
    """Typed ATE analysis metrics returned by the baseline analysis endpoint."""

    model_config = ConfigDict(frozen=True)

    outcome_column: str
    treatment_column: str
    treated_mean: float
    control_mean: float
    ate: float
    absolute_lift: float
    relative_lift: float | None
    ci_lower: float
    ci_upper: float
    confidence_level: float
    bootstrap_samples: int


class AnalysisATEResponse(BaseModel):
    """Typed response contract for the analysis ATE endpoint."""

    model_config = ConfigDict(frozen=True)

    status: str
    source_path: str
    row_count: int
    result: ATEAnalysisResultResponse


class AnalysisModelsResponse(BaseModel):
    """Typed response contract for the model comparison analysis endpoint."""

    model_config = ConfigDict(frozen=True)

    status: str
    source_path: str
    report_name: str
    comparison_split: str
    conversion_champion_model_name: str
    conversion_challenger_model_name: str | None
    revenue_champion_model_name: str
    report: Phase3ModelComparisonReport


class AnalysisSegmentsResponse(BaseModel):
    """Typed response contract for the segment and cohort analysis endpoint."""

    model_config = ConfigDict(frozen=True)

    status: str
    decile_report_path: str
    rollup_report_path: str
    validation_report_path: str
    model_name: str
    outcome_column: str
    split_name: str
    overall_observed_ate: float
    top_decile_observed_ate: float | None
    bottom_decile_observed_ate: float | None
    top_decile_gain_over_overall_ate: float | None
    uplift_concentration_ratio: float | None
    positive_decile_count: int
    negative_decile_count: int
    best_decile_rank: int | None
    worst_decile_rank: int | None
    monotonicity_break_count: int
    validation_verdict: str
    validation_reason: str
    top_persuadable_cohorts: list[dict[str, str | float]]
    suppression_candidates: list[dict[str, str | float]]
    top_persuadable_deciles: list[int]
    suppression_candidate_deciles: list[int]
    deciles: list[dict[str, Any]]
    dimension_summaries: list[Phase4DimensionValidationSummary]
    reports: list[ModelBasedDimensionRollup]


class AnalysisRecommendationsResponse(BaseModel):
    """Typed response contract for the final recommendations endpoint."""

    model_config = ConfigDict(frozen=True)

    status: str
    closeout_report_path: str
    policy_champion_model_name: str
    policy_champion_value: float
    champion_is_ml_model: bool
    final_action_summary: str
    prioritized_segment_count: int
    suppressed_segment_count: int
    top_target_user_count: int
    top_suppress_user_count: int
    report: Phase5DecisionCloseoutReport
