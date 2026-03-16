"""Model-driven segment budget allocation for revised Phase 5."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, ConfigDict

from primelift.utils.paths import (
    DEFAULT_DRLEARNER_REVENUE_METRICS_PATH,
    DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH,
    DEFAULT_PHASE5_BUDGET_ALLOCATION_REPORT_PATH,
    DEFAULT_PHASE5_SEGMENT_BUDGET_TABLE_PATH,
)


class SegmentBudgetAllocation(BaseModel):
    """Serializable budget recommendation for one prioritized segment."""

    model_config = ConfigDict(frozen=True)

    segment: str
    eligible_user_count: int
    positive_revenue_user_count: int
    positive_revenue_user_share: float
    mean_predicted_conversion_effect: float
    observed_conversion_ate: float | None
    mean_predicted_revenue_effect: float
    total_positive_predicted_revenue_effect: float
    budget_share: float
    recommended_budget: float
    rationale: str


class SuppressedSegmentBudgetRecommendation(BaseModel):
    """Serializable zero-budget recommendation for a suppressed segment."""

    model_config = ConfigDict(frozen=True)

    segment: str
    eligible_user_count: int
    mean_predicted_conversion_effect: float
    observed_conversion_ate: float | None
    mean_predicted_revenue_effect: float
    recommended_budget: float
    rationale: str


class Phase5BudgetAllocationReport(BaseModel):
    """Serializable report for the budget-allocation Phase 5 slice."""

    model_config = ConfigDict(frozen=True)

    report_name: str
    split_name: str
    conversion_model_name: str
    revenue_model_name: str
    total_budget: float
    allocated_budget: float
    unallocated_budget: float
    conversion_rollup_report_path: str
    revenue_metrics_report_path: str
    revenue_scores_path: str
    budget_table_path: str
    output_report_path: str
    allocated_segment_count: int
    suppressed_segment_count: int
    top_budget_segments: list[SegmentBudgetAllocation]
    suppressed_segments: list[SuppressedSegmentBudgetRecommendation]
    action_summary: str


def _load_json(path: Path) -> dict:
    """Load a JSON artifact from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _extract_segment_rollups(rollup_report: dict) -> tuple[list[dict], list[dict]]:
    """Extract prioritized and suppressed segment rows from the Phase 4 rollup report."""

    for dimension_report in rollup_report["reports"]:
        results = dimension_report.get("results", [])
        if not results:
            continue
        first_result = results[0]
        if first_result.get("group_column") != "segment":
            continue
        prioritized = [
            row for row in results if row.get("recommendation_label") == "prioritize"
        ]
        suppressed = [
            row for row in results if row.get("recommendation_label") == "suppress"
        ]
        return prioritized, suppressed
    raise ValueError("Phase 4 rollup report does not contain segment-level results.")


def _extract_revenue_score_info(revenue_metrics_report: dict, split_name: str) -> tuple[str, Path]:
    """Extract the revenue model score column and scored split path."""

    score_column = str(revenue_metrics_report["config"]["score_column"])
    for split_evaluation in revenue_metrics_report["split_evaluations"]:
        if split_evaluation["split_name"] == split_name:
            return score_column, Path(str(split_evaluation["score_output_path"]))
    raise ValueError(f"Revenue metrics report does not contain split '{split_name}'.")


def _summarize_revenue_scores_by_segment(
    revenue_scores: pd.DataFrame,
    score_column: str,
) -> pd.DataFrame:
    """Build segment-level revenue opportunity summaries from user-level scored outputs."""

    if "segment" not in revenue_scores.columns:
        raise ValueError("Revenue scored output is missing the 'segment' column.")
    if score_column not in revenue_scores.columns:
        raise ValueError(f"Revenue scored output is missing the score column '{score_column}'.")

    revenue_frame = revenue_scores.loc[:, ["segment", score_column]].copy()
    revenue_frame["positive_revenue_effect"] = revenue_frame[score_column].clip(lower=0.0)
    revenue_frame["is_positive_revenue_effect"] = revenue_frame[score_column] > 0.0

    summary = (
        revenue_frame.groupby("segment", as_index=False)
        .agg(
            eligible_user_count=(score_column, "size"),
            positive_revenue_user_count=("is_positive_revenue_effect", "sum"),
            mean_predicted_revenue_effect=(score_column, "mean"),
            total_positive_predicted_revenue_effect=("positive_revenue_effect", "sum"),
        )
        .sort_values(by="total_positive_predicted_revenue_effect", ascending=False)
    )
    summary["positive_revenue_user_share"] = (
        summary["positive_revenue_user_count"] / summary["eligible_user_count"]
    )
    return summary


def _build_budget_rationale(
    *,
    segment: str,
    budget_share: float,
    mean_predicted_revenue_effect: float,
    observed_conversion_ate: float | None,
) -> str:
    """Build an explainable rationale for a positive budget recommendation."""

    observed_text = (
        f" observed conversion ATE {observed_conversion_ate:.4f}"
        if observed_conversion_ate is not None
        else " observed conversion ATE unavailable"
    )
    return (
        f"Allocate {budget_share:.1%} of budget to {segment} because the cohort shows "
        f"mean predicted incremental revenue {mean_predicted_revenue_effect:.4f} with"
        f"{observed_text}."
    )


def _build_zero_budget_rationale(
    *,
    segment: str,
    mean_predicted_revenue_effect: float,
    observed_conversion_ate: float | None,
) -> str:
    """Build an explainable rationale for a zero-budget suppression recommendation."""

    observed_text = (
        f" observed conversion ATE {observed_conversion_ate:.4f}"
        if observed_conversion_ate is not None
        else " observed conversion ATE unavailable"
    )
    return (
        f"Keep {segment} at zero incremental budget because the cohort shows mean predicted "
        f"incremental revenue {mean_predicted_revenue_effect:.4f} with{observed_text}."
    )


def _build_action_summary(
    allocated_segments: list[SegmentBudgetAllocation],
    suppressed_segments: list[SuppressedSegmentBudgetRecommendation],
) -> str:
    """Create a compact budget summary for terminal and UI use."""

    allocation_text = ", ".join(
        f"{segment.segment} ({segment.budget_share:.1%})" for segment in allocated_segments[:3]
    ) or "no positive segments"
    suppressed_text = ", ".join(segment.segment for segment in suppressed_segments[:2]) or "no suppressed segments"
    return f"Allocate budget to {allocation_text}; keep {suppressed_text} at zero incremental budget."


def generate_segment_budget_allocation(
    *,
    conversion_rollup_report_path: Path = DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH,
    revenue_metrics_report_path: Path = DEFAULT_DRLEARNER_REVENUE_METRICS_PATH,
    output_report_path: Path = DEFAULT_PHASE5_BUDGET_ALLOCATION_REPORT_PATH,
    budget_table_path: Path = DEFAULT_PHASE5_SEGMENT_BUDGET_TABLE_PATH,
    total_budget: float = 100_000.0,
) -> Phase5BudgetAllocationReport:
    """Generate segment-level budget recommendations for the revised Phase 5 slice."""

    if total_budget <= 0:
        raise ValueError("total_budget must be greater than zero.")

    rollup_report = _load_json(conversion_rollup_report_path)
    revenue_metrics_report = _load_json(revenue_metrics_report_path)

    split_name = str(rollup_report["split_name"])
    prioritized_segments, suppressed_segments = _extract_segment_rollups(rollup_report)
    score_column, revenue_scores_path = _extract_revenue_score_info(revenue_metrics_report, split_name)
    revenue_scores = pd.read_csv(revenue_scores_path)
    revenue_segment_summary = _summarize_revenue_scores_by_segment(
        revenue_scores=revenue_scores,
        score_column=score_column,
    )

    summary_lookup = revenue_segment_summary.set_index("segment").to_dict(orient="index")

    allocation_rows: list[SegmentBudgetAllocation] = []
    positive_mass_values: list[float] = []
    for row in prioritized_segments:
        segment_name = str(row["group_value"])
        revenue_summary = summary_lookup.get(segment_name)
        if revenue_summary is None:
            raise ValueError(f"Revenue scores do not contain segment '{segment_name}'.")

        positive_mass = float(revenue_summary["total_positive_predicted_revenue_effect"])
        positive_mass_values.append(positive_mass)
        allocation_rows.append(
            SegmentBudgetAllocation(
                segment=segment_name,
                eligible_user_count=int(revenue_summary["eligible_user_count"]),
                positive_revenue_user_count=int(revenue_summary["positive_revenue_user_count"]),
                positive_revenue_user_share=float(revenue_summary["positive_revenue_user_share"]),
                mean_predicted_conversion_effect=float(row["mean_predicted_effect"]),
                observed_conversion_ate=(
                    float(row["observed_ate"]) if row.get("observed_ate") is not None else None
                ),
                mean_predicted_revenue_effect=float(revenue_summary["mean_predicted_revenue_effect"]),
                total_positive_predicted_revenue_effect=positive_mass,
                budget_share=0.0,
                recommended_budget=0.0,
                rationale="",
            )
        )

    total_positive_mass = float(sum(positive_mass_values))
    if total_positive_mass <= 0.0:
        raise ValueError("No positive predicted revenue effect was available for prioritized segments.")

    finalized_allocations: list[SegmentBudgetAllocation] = []
    for allocation in allocation_rows:
        budget_share = allocation.total_positive_predicted_revenue_effect / total_positive_mass
        recommended_budget = total_budget * budget_share
        finalized_allocations.append(
            allocation.model_copy(
                update={
                    "budget_share": budget_share,
                    "recommended_budget": recommended_budget,
                    "rationale": _build_budget_rationale(
                        segment=allocation.segment,
                        budget_share=budget_share,
                        mean_predicted_revenue_effect=allocation.mean_predicted_revenue_effect,
                        observed_conversion_ate=allocation.observed_conversion_ate,
                    ),
                }
            )
        )

    finalized_allocations = sorted(
        finalized_allocations,
        key=lambda item: item.recommended_budget,
        reverse=True,
    )

    zero_budget_rows: list[SuppressedSegmentBudgetRecommendation] = []
    for row in suppressed_segments:
        segment_name = str(row["group_value"])
        revenue_summary = summary_lookup.get(segment_name)
        mean_predicted_revenue_effect = (
            float(revenue_summary["mean_predicted_revenue_effect"])
            if revenue_summary is not None
            else 0.0
        )
        zero_budget_rows.append(
            SuppressedSegmentBudgetRecommendation(
                segment=segment_name,
                eligible_user_count=int(revenue_summary["eligible_user_count"]) if revenue_summary is not None else 0,
                mean_predicted_conversion_effect=float(row["mean_predicted_effect"]),
                observed_conversion_ate=(
                    float(row["observed_ate"]) if row.get("observed_ate") is not None else None
                ),
                mean_predicted_revenue_effect=mean_predicted_revenue_effect,
                recommended_budget=0.0,
                rationale=_build_zero_budget_rationale(
                    segment=segment_name,
                    mean_predicted_revenue_effect=mean_predicted_revenue_effect,
                    observed_conversion_ate=(
                        float(row["observed_ate"]) if row.get("observed_ate") is not None else None
                    ),
                ),
            )
        )

    budget_table_rows = [
        {
            "segment": row.segment,
            "decision": "allocate",
            "eligible_user_count": row.eligible_user_count,
            "positive_revenue_user_count": row.positive_revenue_user_count,
            "positive_revenue_user_share": row.positive_revenue_user_share,
            "mean_predicted_conversion_effect": row.mean_predicted_conversion_effect,
            "observed_conversion_ate": row.observed_conversion_ate,
            "mean_predicted_revenue_effect": row.mean_predicted_revenue_effect,
            "total_positive_predicted_revenue_effect": row.total_positive_predicted_revenue_effect,
            "budget_share": row.budget_share,
            "recommended_budget": row.recommended_budget,
            "rationale": row.rationale,
        }
        for row in finalized_allocations
    ]
    budget_table_rows.extend(
        {
            "segment": row.segment,
            "decision": "suppress",
            "eligible_user_count": row.eligible_user_count,
            "positive_revenue_user_count": 0,
            "positive_revenue_user_share": 0.0,
            "mean_predicted_conversion_effect": row.mean_predicted_conversion_effect,
            "observed_conversion_ate": row.observed_conversion_ate,
            "mean_predicted_revenue_effect": row.mean_predicted_revenue_effect,
            "total_positive_predicted_revenue_effect": 0.0,
            "budget_share": 0.0,
            "recommended_budget": row.recommended_budget,
            "rationale": row.rationale,
        }
        for row in zero_budget_rows
    )

    budget_table = pd.DataFrame(budget_table_rows)
    budget_table_path.parent.mkdir(parents=True, exist_ok=True)
    budget_table.to_csv(budget_table_path, index=False)

    report = Phase5BudgetAllocationReport(
        report_name="phase5_segment_budget_allocation",
        split_name=split_name,
        conversion_model_name=str(rollup_report["model_name"]),
        revenue_model_name=str(revenue_metrics_report["model_name"]),
        total_budget=float(total_budget),
        allocated_budget=float(sum(item.recommended_budget for item in finalized_allocations)),
        unallocated_budget=0.0,
        conversion_rollup_report_path=str(conversion_rollup_report_path),
        revenue_metrics_report_path=str(revenue_metrics_report_path),
        revenue_scores_path=str(revenue_scores_path),
        budget_table_path=str(budget_table_path),
        output_report_path=str(output_report_path),
        allocated_segment_count=len(finalized_allocations),
        suppressed_segment_count=len(zero_budget_rows),
        top_budget_segments=finalized_allocations,
        suppressed_segments=zero_budget_rows,
        action_summary=_build_action_summary(finalized_allocations, zero_budget_rows),
    )

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return report
