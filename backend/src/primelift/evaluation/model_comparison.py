"""Phase 3 model comparison helpers for revised PrimeLift ML workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from primelift.utils.paths import DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH


class Phase3ModelScorecard(BaseModel):
    """Normalized holdout metrics for one trained Phase 3 model."""

    model_config = ConfigDict(frozen=True)

    model_name: str
    outcome_column: str
    split_name: str
    metrics_report_path: str
    overall_observed_ate: float
    top_decile_observed_ate: float | None
    bottom_decile_observed_ate: float | None
    top_decile_gain_over_baseline: float | None
    bottom_decile_gain_over_baseline: float | None
    observed_top_bottom_gap: float | None
    mean_predicted_cate: float
    std_predicted_cate: float
    positive_cate_share: float
    top_decile_mean_predicted_cate: float | None
    bottom_decile_mean_predicted_cate: float | None
    interval_capable: bool
    mean_interval_width: float | None
    top_segments: list[str]
    bottom_segments: list[str]


class Phase3OutcomeComparison(BaseModel):
    """Comparison summary for one outcome on one holdout split."""

    model_config = ConfigDict(frozen=True)

    outcome_column: str
    split_name: str
    baseline_observed_ate: float
    ranked_models: list[Phase3ModelScorecard]
    champion_model_name: str
    champion_reason: str
    challenger_model_name: str | None
    challenger_reason: str | None


class Phase3ModelComparisonReport(BaseModel):
    """Structured report for the revised Phase 3 model comparison slice."""

    model_config = ConfigDict(frozen=True)

    report_name: str
    comparison_split: str
    generated_from_reports: list[str]
    conversion_comparison: Phase3OutcomeComparison
    revenue_comparison: Phase3OutcomeComparison
    revised_phase_3_status: str
    next_recommended_phase: int
    next_recommended_focus: str


def _load_report(path: Path) -> dict[str, Any]:
    """Load a saved training report from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _extract_split_report(report: dict[str, Any], split_name: str) -> dict[str, Any]:
    """Extract one split evaluation block from a saved training report."""

    for split_evaluation in report["split_evaluations"]:
        if split_evaluation["split_name"] == split_name:
            return split_evaluation
    raise ValueError(f"Split '{split_name}' was not found in report '{report['model_name']}'.")


def _build_scorecard(report_path: Path, split_name: str) -> Phase3ModelScorecard:
    """Build one normalized model scorecard from a saved training report."""

    report = _load_report(report_path)
    split_report = _extract_split_report(report, split_name)
    outcome_column = report["config"]["outcome_column"]
    top_observed = split_report.get("top_decile_observed_ate")
    bottom_observed = split_report.get("bottom_decile_observed_ate")
    overall_observed = float(split_report["overall_observed_ate"])

    return Phase3ModelScorecard(
        model_name=report["model_name"],
        outcome_column=outcome_column,
        split_name=split_name,
        metrics_report_path=str(report_path),
        overall_observed_ate=overall_observed,
        top_decile_observed_ate=float(top_observed) if top_observed is not None else None,
        bottom_decile_observed_ate=float(bottom_observed) if bottom_observed is not None else None,
        top_decile_gain_over_baseline=(
            float(top_observed) - overall_observed if top_observed is not None else None
        ),
        bottom_decile_gain_over_baseline=(
            float(bottom_observed) - overall_observed if bottom_observed is not None else None
        ),
        observed_top_bottom_gap=(
            float(top_observed) - float(bottom_observed)
            if top_observed is not None and bottom_observed is not None
            else None
        ),
        mean_predicted_cate=float(split_report["mean_predicted_cate"]),
        std_predicted_cate=float(split_report["std_predicted_cate"]),
        positive_cate_share=float(split_report["positive_cate_share"]),
        top_decile_mean_predicted_cate=(
            float(split_report["top_decile_mean_predicted_cate"])
            if split_report.get("top_decile_mean_predicted_cate") is not None
            else None
        ),
        bottom_decile_mean_predicted_cate=(
            float(split_report["bottom_decile_mean_predicted_cate"])
            if split_report.get("bottom_decile_mean_predicted_cate") is not None
            else None
        ),
        interval_capable="mean_interval_width" in split_report,
        mean_interval_width=(
            float(split_report["mean_interval_width"])
            if split_report.get("mean_interval_width") is not None
            else None
        ),
        top_segments=[
            str(item["segment"]) for item in split_report.get("top_segments_by_mean_predicted_cate", [])
        ],
        bottom_segments=[
            str(item["segment"])
            for item in split_report.get("bottom_segments_by_mean_predicted_cate", [])
        ],
    )


def _score_sort_key(scorecard: Phase3ModelScorecard) -> tuple[float, float, float]:
    """Ranking key for selecting the best holdout model."""

    top = scorecard.top_decile_observed_ate if scorecard.top_decile_observed_ate is not None else float(
        "-inf"
    )
    top_bottom_gap = (
        scorecard.observed_top_bottom_gap
        if scorecard.observed_top_bottom_gap is not None
        else float("-inf")
    )
    bottom = -scorecard.bottom_decile_observed_ate if scorecard.bottom_decile_observed_ate is not None else 0.0
    return (top, top_bottom_gap, bottom)


def _build_reason(scorecard: Phase3ModelScorecard, role: str) -> str:
    """Build a short explanation for champion or challenger selection."""

    top = (
        f"{scorecard.top_decile_observed_ate:.6f}"
        if scorecard.top_decile_observed_ate is not None
        else "n/a"
    )
    gap = (
        f"{scorecard.observed_top_bottom_gap:.6f}"
        if scorecard.observed_top_bottom_gap is not None
        else "n/a"
    )
    interval_text = (
        f" It also provides interval estimates with mean width {scorecard.mean_interval_width:.6f}."
        if scorecard.interval_capable and scorecard.mean_interval_width is not None
        else ""
    )
    if role == "champion":
        return (
            f"Highest {scorecard.split_name} top-decile observed uplift/revenue effect ({top}) "
            f"with top-vs-bottom observed gap {gap}.{interval_text}"
        )
    return (
        f"Next-best {scorecard.split_name} top-decile observed uplift/revenue effect ({top}) "
        f"with top-vs-bottom observed gap {gap}.{interval_text}"
    )


def _build_outcome_comparison(
    *,
    outcome_column: str,
    split_name: str,
    report_paths: list[Path],
) -> Phase3OutcomeComparison:
    """Build the comparison summary for one outcome."""

    scorecards = [
        _build_scorecard(report_path=report_path, split_name=split_name)
        for report_path in report_paths
    ]
    scorecards = [scorecard for scorecard in scorecards if scorecard.outcome_column == outcome_column]
    if not scorecards:
        raise ValueError(f"No reports were found for outcome '{outcome_column}'.")

    ranked_models = sorted(scorecards, key=_score_sort_key, reverse=True)
    champion = ranked_models[0]
    challenger = ranked_models[1] if len(ranked_models) > 1 else None

    return Phase3OutcomeComparison(
        outcome_column=outcome_column,
        split_name=split_name,
        baseline_observed_ate=champion.overall_observed_ate,
        ranked_models=ranked_models,
        champion_model_name=champion.model_name,
        champion_reason=_build_reason(champion, role="champion"),
        challenger_model_name=challenger.model_name if challenger else None,
        challenger_reason=_build_reason(challenger, role="challenger") if challenger else None,
    )


def generate_phase3_model_comparison_report(
    *,
    conversion_report_paths: list[Path],
    revenue_report_paths: list[Path],
    comparison_split: str = "test",
    output_path: Path = DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
) -> Phase3ModelComparisonReport:
    """Generate the revised Phase 3 comparison report from saved model reports."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated_from_reports = [str(path) for path in [*conversion_report_paths, *revenue_report_paths]]

    report = Phase3ModelComparisonReport(
        report_name="phase3_model_comparison",
        comparison_split=comparison_split,
        generated_from_reports=generated_from_reports,
        conversion_comparison=_build_outcome_comparison(
            outcome_column="conversion",
            split_name=comparison_split,
            report_paths=conversion_report_paths,
        ),
        revenue_comparison=_build_outcome_comparison(
            outcome_column="revenue",
            split_name=comparison_split,
            report_paths=revenue_report_paths,
        ),
        revised_phase_3_status="complete",
        next_recommended_phase=4,
        next_recommended_focus="Model-based uplift reporting and decile analysis.",
    )

    output_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return report
