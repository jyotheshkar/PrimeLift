"""Analysis endpoint helpers for the Phase 6 API slices."""

from __future__ import annotations

import json

from fastapi import HTTPException

from primelift.api.schemas import (
    ATEAnalysisResultResponse,
    AnalysisATEResponse,
    AnalysisModelsResponse,
    AnalysisRecommendationsResponse,
    AnalysisSegmentsResponse,
)
from primelift.causal.ate import analyze_average_treatment_effect
from primelift.data.summary import load_dataset
from primelift.decision.decision_closeout import Phase5DecisionCloseoutReport
from primelift.evaluation.model_comparison import Phase3ModelComparisonReport
from primelift.evaluation.phase4_validation import Phase4ValidationSummaryReport
from primelift.uplift.model_based_rollups import ModelBasedRollupReport
from primelift.utils.paths import (
    DEFAULT_DATASET_PATH,
    DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
    DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH,
)


def build_ate_analysis_response(
    outcome_column: str = "conversion",
    bootstrap_samples: int = 300,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> AnalysisATEResponse:
    """Run the saved-dataset ATE analysis and return a typed API response."""

    if not DEFAULT_DATASET_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Dataset CSV was not found at the default path. "
                "Generate the dataset first with POST /dataset/generate."
            ),
        )

    dataset = load_dataset(DEFAULT_DATASET_PATH)
    result = analyze_average_treatment_effect(
        dataset=dataset,
        outcome_column=outcome_column,
        bootstrap_samples=bootstrap_samples,
        confidence_level=confidence_level,
        random_seed=random_seed,
    )
    return AnalysisATEResponse(
        status="ok",
        source_path=str(DEFAULT_DATASET_PATH),
        row_count=int(len(dataset)),
        result=ATEAnalysisResultResponse(**result.model_dump()),
    )


def build_models_analysis_response() -> AnalysisModelsResponse:
    """Load the saved Phase 3 model comparison report and return it as typed JSON."""

    if not DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Phase 3 model comparison report was not found. "
                "Generate it first before calling GET /analysis/models."
            ),
        )

    report_payload = json.loads(
        DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH.read_text(encoding="utf-8")
    )
    report = Phase3ModelComparisonReport(**report_payload)
    return AnalysisModelsResponse(
        status="ok",
        source_path=str(DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH),
        report_name=report.report_name,
        comparison_split=report.comparison_split,
        conversion_champion_model_name=report.conversion_comparison.champion_model_name,
        conversion_challenger_model_name=report.conversion_comparison.challenger_model_name,
        revenue_champion_model_name=report.revenue_comparison.champion_model_name,
        report=report,
    )


def build_segments_analysis_response() -> AnalysisSegmentsResponse:
    """Load the saved Phase 4 rollup and validation reports as typed segment analysis output."""

    if not DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Phase 4 conversion decile report was not found. "
                "Generate it first before calling GET /analysis/segments."
            ),
        )
    if not DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Phase 4 conversion rollup report was not found. "
                "Generate it first before calling GET /analysis/segments."
            ),
        )
    if not DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Phase 4 validation summary report was not found. "
                "Generate it first before calling GET /analysis/segments."
            ),
        )

    decile_payload = json.loads(
        DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH.read_text(encoding="utf-8")
    )
    rollup_payload = json.loads(
        DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH.read_text(encoding="utf-8")
    )
    validation_payload = json.loads(
        DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH.read_text(encoding="utf-8")
    )

    rollup_report = ModelBasedRollupReport(**rollup_payload)
    validation_report = Phase4ValidationSummaryReport(**validation_payload)

    if (
        decile_payload["model_name"] != rollup_report.model_name
        or rollup_report.model_name != validation_report.model_name
    ):
        raise HTTPException(
            status_code=500,
            detail="Phase 4 decile, rollup, and validation reports are inconsistent.",
        )

    return AnalysisSegmentsResponse(
        status="ok",
        decile_report_path=str(DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH),
        rollup_report_path=str(DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH),
        validation_report_path=str(DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH),
        model_name=rollup_report.model_name,
        outcome_column=rollup_report.outcome_column,
        split_name=rollup_report.split_name,
        overall_observed_ate=validation_report.overall_observed_ate,
        top_decile_observed_ate=validation_report.top_decile_observed_ate,
        bottom_decile_observed_ate=validation_report.bottom_decile_observed_ate,
        top_decile_gain_over_overall_ate=validation_report.top_decile_gain_over_overall_ate,
        uplift_concentration_ratio=validation_report.uplift_concentration_ratio,
        positive_decile_count=validation_report.positive_decile_count,
        negative_decile_count=validation_report.negative_decile_count,
        best_decile_rank=validation_report.best_decile_rank,
        worst_decile_rank=validation_report.worst_decile_rank,
        monotonicity_break_count=validation_report.monotonicity_break_count,
        validation_verdict=validation_report.validation_verdict,
        validation_reason=validation_report.validation_reason,
        top_persuadable_cohorts=validation_report.top_persuadable_cohorts,
        suppression_candidates=validation_report.suppression_candidates,
        top_persuadable_deciles=validation_report.top_persuadable_deciles,
        suppression_candidate_deciles=validation_report.suppression_candidate_deciles,
        deciles=decile_payload["deciles"],
        dimension_summaries=validation_report.dimension_summaries,
        reports=rollup_report.reports,
    )


def build_recommendations_analysis_response() -> AnalysisRecommendationsResponse:
    """Load the saved Phase 5 closeout report and return final recommendation output."""

    if not DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Phase 5 decision closeout report was not found. "
                "Generate it first before calling GET /analysis/recommendations."
            ),
        )

    closeout_payload = json.loads(
        DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH.read_text(encoding="utf-8")
    )
    closeout_report = Phase5DecisionCloseoutReport(**closeout_payload)

    return AnalysisRecommendationsResponse(
        status="ok",
        closeout_report_path=str(DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH),
        policy_champion_model_name=closeout_report.policy_comparison.champion_model_name,
        policy_champion_value=closeout_report.policy_comparison.champion_value,
        champion_is_ml_model=closeout_report.policy_comparison.champion_is_ml_model,
        final_action_summary=closeout_report.final_action_summary,
        prioritized_segment_count=len(closeout_report.prioritized_segments),
        suppressed_segment_count=len(closeout_report.suppressed_segments),
        top_target_user_count=len(closeout_report.top_target_users),
        top_suppress_user_count=len(closeout_report.top_suppress_users),
        report=closeout_report,
    )
