"""Compact validation summary for revised Phase 4 model-based reporting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from primelift.utils.paths import DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH


class Phase4DimensionValidationSummary(BaseModel):
    """Compact validation summary for one business dimension."""

    model_config = ConfigDict(frozen=True)

    group_column: str
    prioritize_group_count: int
    suppress_group_count: int
    top_positive_groups: list[str]
    suppression_candidates: list[str]
    strongest_positive_group: str
    strongest_positive_observed_ate: float | None
    strongest_negative_group: str | None
    strongest_negative_observed_ate: float | None


class Phase4ValidationSummaryReport(BaseModel):
    """Compact validation summary tying Phase 4 outputs together."""

    model_config = ConfigDict(frozen=True)

    report_name: str
    outcome_column: str
    split_name: str
    model_name: str
    decile_report_path: str
    rollup_report_path: str
    output_report_path: str
    overall_observed_ate: float
    top_decile_observed_ate: float | None
    bottom_decile_observed_ate: float | None
    top_decile_gain_over_overall_ate: float | None
    observed_top_bottom_gap: float | None
    uplift_concentration_ratio: float | None
    positive_decile_count: int
    negative_decile_count: int
    best_decile_rank: int | None
    worst_decile_rank: int | None
    monotonicity_break_count: int
    top_persuadable_deciles: list[int]
    suppression_candidate_deciles: list[int]
    top_persuadable_cohorts: list[dict[str, str | float]]
    suppression_candidates: list[dict[str, str | float]]
    dimension_summaries: list[Phase4DimensionValidationSummary]
    validation_verdict: str
    validation_reason: str


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _count_monotonicity_breaks(observed_ates: list[float]) -> int:
    """Count increases in observed ATE as predicted-rank decreases."""

    return sum(
        1
        for previous, current in zip(observed_ates, observed_ates[1:], strict=False)
        if current > previous
    )


def _build_dimension_summary(report: dict[str, Any]) -> Phase4DimensionValidationSummary:
    """Build a compact validation summary for one dimension rollup."""

    prioritize_results = [
        result for result in report["results"] if result["recommendation_label"] == "prioritize"
    ]
    suppress_results = [
        result for result in report["results"] if result["recommendation_label"] == "suppress"
    ]

    strongest_positive = max(
        report["results"],
        key=lambda item: (
            item["observed_ate"] if item["observed_ate"] is not None else float("-inf")
        ),
    )
    strongest_negative = (
        min(
            suppress_results,
            key=lambda item: item["observed_ate"],
        )
        if suppress_results
        else None
    )

    return Phase4DimensionValidationSummary(
        group_column=str(report["group_column"]),
        prioritize_group_count=len(prioritize_results),
        suppress_group_count=len(suppress_results),
        top_positive_groups=[str(value) for value in report["top_positive_groups"]],
        suppression_candidates=[str(value) for value in report["suppression_candidates"]],
        strongest_positive_group=str(strongest_positive["group_value"]),
        strongest_positive_observed_ate=(
            float(strongest_positive["observed_ate"])
            if strongest_positive["observed_ate"] is not None
            else None
        ),
        strongest_negative_group=(
            str(strongest_negative["group_value"]) if strongest_negative is not None else None
        ),
        strongest_negative_observed_ate=(
            float(strongest_negative["observed_ate"]) if strongest_negative is not None else None
        ),
    )


def _build_validation_verdict(
    *,
    top_decile_gain_over_overall_ate: float | None,
    observed_top_bottom_gap: float | None,
    negative_decile_count: int,
    suppression_candidate_count: int,
    monotonicity_break_count: int,
) -> tuple[str, str]:
    """Translate summary metrics into a concise quality verdict."""

    if (
        top_decile_gain_over_overall_ate is not None
        and top_decile_gain_over_overall_ate > 0.0
        and observed_top_bottom_gap is not None
        and observed_top_bottom_gap > 0.0
        and negative_decile_count > 0
        and suppression_candidate_count > 0
    ):
        if monotonicity_break_count <= 1:
            return (
                "actionable",
                "Top-ranked deciles beat the overall baseline, the top-vs-bottom gap is positive, and suppression zones are visible with relatively orderly ranking.",
            )
        return (
            "promising_but_noisy",
            "Top-ranked deciles beat the baseline and both decile- and cohort-level suppression zones exist, but the observed decile ranking is not monotonic end to end.",
        )

    if top_decile_gain_over_overall_ate is not None and top_decile_gain_over_overall_ate > 0.0:
        return (
            "mixed",
            "The top decile beats the baseline, but the rest of the ranking does not yet show enough separation for clean operational use.",
        )

    return (
        "weak",
        "The current model-based ranking does not show enough holdout concentration above the baseline to justify acting on it confidently.",
    )


def generate_phase4_validation_summary(
    *,
    decile_report_path: Path,
    rollup_report_path: Path,
    output_report_path: Path = DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH,
) -> Phase4ValidationSummaryReport:
    """Generate a compact Phase 4 validation summary from the decile and rollup reports."""

    decile_report = _load_json(decile_report_path)
    rollup_report = _load_json(rollup_report_path)

    if decile_report["model_name"] != rollup_report["model_name"]:
        raise ValueError("Decile and rollup reports must come from the same model.")
    if decile_report["outcome_column"] != rollup_report["outcome_column"]:
        raise ValueError("Decile and rollup reports must describe the same outcome.")
    if decile_report["split_name"] != rollup_report["split_name"]:
        raise ValueError("Decile and rollup reports must describe the same split.")

    observed_deciles = [
        float(decile["observed_ate"])
        for decile in decile_report["deciles"]
        if decile["observed_ate"] is not None
    ]
    positive_decile_count = sum(1 for value in observed_deciles if value > 0.0)
    negative_decile_count = sum(1 for value in observed_deciles if value <= 0.0)

    best_decile = max(
        decile_report["deciles"],
        key=lambda item: item["observed_ate"] if item["observed_ate"] is not None else float("-inf"),
    )
    worst_decile = min(
        decile_report["deciles"],
        key=lambda item: item["observed_ate"] if item["observed_ate"] is not None else float("inf"),
    )

    top_decile_observed_ate = (
        float(decile_report["top_decile_observed_ate"])
        if decile_report["top_decile_observed_ate"] is not None
        else None
    )
    overall_observed_ate = float(decile_report["overall_observed_ate"])
    top_decile_gain_over_overall_ate = (
        top_decile_observed_ate - overall_observed_ate
        if top_decile_observed_ate is not None
        else None
    )
    uplift_concentration_ratio = (
        top_decile_observed_ate / overall_observed_ate
        if top_decile_observed_ate is not None and overall_observed_ate != 0.0
        else None
    )

    dimension_summaries = [
        _build_dimension_summary(report) for report in rollup_report["reports"]
    ]
    suppression_candidate_count = len(rollup_report["suppression_candidates"])
    validation_verdict, validation_reason = _build_validation_verdict(
        top_decile_gain_over_overall_ate=top_decile_gain_over_overall_ate,
        observed_top_bottom_gap=(
            float(decile_report["observed_top_bottom_gap"])
            if decile_report["observed_top_bottom_gap"] is not None
            else None
        ),
        negative_decile_count=negative_decile_count,
        suppression_candidate_count=suppression_candidate_count,
        monotonicity_break_count=_count_monotonicity_breaks(observed_deciles),
    )

    report = Phase4ValidationSummaryReport(
        report_name="phase4_validation_summary",
        outcome_column=str(decile_report["outcome_column"]),
        split_name=str(decile_report["split_name"]),
        model_name=str(decile_report["model_name"]),
        decile_report_path=str(decile_report_path),
        rollup_report_path=str(rollup_report_path),
        output_report_path=str(output_report_path),
        overall_observed_ate=overall_observed_ate,
        top_decile_observed_ate=top_decile_observed_ate,
        bottom_decile_observed_ate=(
            float(decile_report["bottom_decile_observed_ate"])
            if decile_report["bottom_decile_observed_ate"] is not None
            else None
        ),
        top_decile_gain_over_overall_ate=top_decile_gain_over_overall_ate,
        observed_top_bottom_gap=(
            float(decile_report["observed_top_bottom_gap"])
            if decile_report["observed_top_bottom_gap"] is not None
            else None
        ),
        uplift_concentration_ratio=uplift_concentration_ratio,
        positive_decile_count=positive_decile_count,
        negative_decile_count=negative_decile_count,
        best_decile_rank=int(best_decile["decile_rank"]) if best_decile["observed_ate"] is not None else None,
        worst_decile_rank=int(worst_decile["decile_rank"]) if worst_decile["observed_ate"] is not None else None,
        monotonicity_break_count=_count_monotonicity_breaks(observed_deciles),
        top_persuadable_deciles=[int(value) for value in decile_report["top_persuadable_deciles"]],
        suppression_candidate_deciles=[int(value) for value in decile_report["suppression_candidate_deciles"]],
        top_persuadable_cohorts=rollup_report["top_persuadable_cohorts"],
        suppression_candidates=rollup_report["suppression_candidates"],
        dimension_summaries=dimension_summaries,
        validation_verdict=validation_verdict,
        validation_reason=validation_reason,
    )

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return report
