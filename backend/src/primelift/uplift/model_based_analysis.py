"""Model-based uplift decile reporting for revised Phase 4."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict

from primelift.causal import estimate_average_treatment_effect
from primelift.utils.paths import (
    DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_SCORED_VIEW_PATH,
)


class UpliftDecileBucket(BaseModel):
    """Serializable summary for one model-based uplift decile."""

    model_config = ConfigDict(frozen=True)

    decile_rank: int
    decile_label: str
    row_count: int
    min_score: float
    mean_score: float
    max_score: float
    treated_count: int
    control_count: int
    treated_outcome_mean: float
    control_outcome_mean: float
    observed_ate: float | None
    gain_over_overall_ate: float | None


class ModelBasedUpliftDecileReport(BaseModel):
    """Serializable report for the first revised Phase 4 model-based slice."""

    model_config = ConfigDict(frozen=True)

    report_name: str
    outcome_column: str
    split_name: str
    model_name: str
    score_column: str
    comparison_report_path: str
    source_metrics_report_path: str
    source_score_output_path: str
    scored_view_path: str
    output_report_path: str
    decile_count: int
    overall_observed_ate: float
    top_decile_observed_ate: float | None
    bottom_decile_observed_ate: float | None
    observed_top_bottom_gap: float | None
    top_persuadable_deciles: list[int]
    suppression_candidate_deciles: list[int]
    deciles: list[UpliftDecileBucket]


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_champion_metrics_report(
    comparison_report_path: Path,
    outcome_column: str,
) -> Path:
    """Resolve the Phase 3 champion metrics report path for one outcome."""

    comparison_report = _load_json(comparison_report_path)
    comparison_key = f"{outcome_column}_comparison"
    if comparison_key not in comparison_report:
        raise ValueError(f"Outcome '{outcome_column}' was not found in the comparison report.")

    champion_model_name = comparison_report[comparison_key]["champion_model_name"]
    for scorecard in comparison_report[comparison_key]["ranked_models"]:
        if scorecard["model_name"] == champion_model_name:
            return Path(scorecard["metrics_report_path"])

    raise ValueError(
        f"Champion model '{champion_model_name}' for outcome '{outcome_column}' could not be resolved."
    )


def _extract_split_report(training_report: dict[str, Any], split_name: str) -> dict[str, Any]:
    """Extract one split block from a saved Phase 3 training report."""

    for split_evaluation in training_report["split_evaluations"]:
        if split_evaluation["split_name"] == split_name:
            return split_evaluation
    raise ValueError(f"Split '{split_name}' was not found in training report '{training_report['model_name']}'.")


def _build_decile_labels(bucket_count: int) -> dict[int, str]:
    """Build readable labels for uplift deciles."""

    return {
        rank: f"D{rank:02d}_{'highest' if rank == 1 else 'lowest' if rank == bucket_count else 'mid'}"
        for rank in range(1, bucket_count + 1)
    }


def _assign_uplift_deciles(
    scored_frame: pd.DataFrame,
    score_column: str,
    decile_count: int,
) -> tuple[pd.DataFrame, int]:
    """Assign descending uplift deciles, where 1 is the highest-predicted bucket."""

    if decile_count < 2:
        raise ValueError("decile_count must be at least 2.")
    if score_column not in scored_frame.columns:
        raise ValueError(f"Missing score column: {score_column}")

    bucket_count = min(decile_count, len(scored_frame))
    descending_rank = scored_frame[score_column].rank(method="first", ascending=False)
    decile_codes = pd.qcut(descending_rank, q=bucket_count, labels=False)
    if decile_codes.isnull().any():
        raise ValueError("Failed to assign uplift deciles.")

    decile_labels = _build_decile_labels(bucket_count)
    scored_with_deciles = scored_frame.copy()
    scored_with_deciles["uplift_decile_rank"] = decile_codes.astype(int) + 1
    scored_with_deciles["uplift_decile_label"] = scored_with_deciles["uplift_decile_rank"].map(
        decile_labels
    )
    scored_with_deciles = scored_with_deciles.sort_values(
        by=score_column,
        ascending=False,
    ).reset_index(drop=True)
    return scored_with_deciles, bucket_count


def _summarize_decile(
    scored_frame: pd.DataFrame,
    outcome_column: str,
    score_column: str,
    decile_rank: int,
    overall_observed_ate: float,
) -> UpliftDecileBucket:
    """Summarize one decile bucket using observed treatment-effect math."""

    decile_frame = scored_frame.loc[scored_frame["uplift_decile_rank"] == decile_rank]
    treated_count = int((decile_frame["treatment"] == 1).sum())
    control_count = int((decile_frame["treatment"] == 0).sum())
    observed_ate: float | None
    if treated_count > 0 and control_count > 0:
        observed_ate = float(
            estimate_average_treatment_effect(
                dataset=decile_frame,
                outcome_column=outcome_column,
                treatment_column="treatment",
            ).ate
        )
    else:
        observed_ate = None

    return UpliftDecileBucket(
        decile_rank=decile_rank,
        decile_label=str(decile_frame["uplift_decile_label"].iloc[0]),
        row_count=int(len(decile_frame)),
        min_score=float(decile_frame[score_column].min()),
        mean_score=float(decile_frame[score_column].mean()),
        max_score=float(decile_frame[score_column].max()),
        treated_count=treated_count,
        control_count=control_count,
        treated_outcome_mean=float(decile_frame.loc[decile_frame["treatment"] == 1, outcome_column].mean()),
        control_outcome_mean=float(decile_frame.loc[decile_frame["treatment"] == 0, outcome_column].mean()),
        observed_ate=observed_ate,
        gain_over_overall_ate=(
            observed_ate - overall_observed_ate if observed_ate is not None else None
        ),
    )


def generate_model_based_uplift_decile_report(
    comparison_report_path: Path = DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
    outcome_column: str = "conversion",
    split_name: str = "test",
    decile_count: int = 10,
    output_report_path: Path = DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH,
    scored_view_path: Path = DEFAULT_PHASE4_CONVERSION_SCORED_VIEW_PATH,
) -> ModelBasedUpliftDecileReport:
    """Generate the first revised Phase 4 model-based uplift decile report."""

    source_metrics_report_path = _resolve_champion_metrics_report(
        comparison_report_path=comparison_report_path,
        outcome_column=outcome_column,
    )
    training_report = _load_json(source_metrics_report_path)
    split_report = _extract_split_report(training_report, split_name)
    score_column = str(training_report["config"]["score_column"])
    source_score_output_path = Path(split_report["score_output_path"])
    scored_frame = pd.read_csv(source_score_output_path)

    if outcome_column not in scored_frame.columns:
        raise ValueError(f"Outcome column '{outcome_column}' was not found in scored output.")
    if "treatment" not in scored_frame.columns:
        raise ValueError("Scored output must contain the treatment column.")

    scored_with_deciles, bucket_count = _assign_uplift_deciles(
        scored_frame=scored_frame,
        score_column=score_column,
        decile_count=decile_count,
    )

    scored_view_path.parent.mkdir(parents=True, exist_ok=True)
    scored_with_deciles.to_csv(scored_view_path, index=False)

    overall_observed_ate = float(
        estimate_average_treatment_effect(
            dataset=scored_with_deciles,
            outcome_column=outcome_column,
            treatment_column="treatment",
        ).ate
    )

    deciles = [
        _summarize_decile(
            scored_frame=scored_with_deciles,
            outcome_column=outcome_column,
            score_column=score_column,
            decile_rank=decile_rank,
            overall_observed_ate=overall_observed_ate,
        )
        for decile_rank in range(1, bucket_count + 1)
    ]

    observed_top_bottom_gap = None
    if deciles[0].observed_ate is not None and deciles[-1].observed_ate is not None:
        observed_top_bottom_gap = deciles[0].observed_ate - deciles[-1].observed_ate

    top_persuadable_deciles = [
        decile.decile_rank
        for decile in sorted(
            [item for item in deciles if item.gain_over_overall_ate is not None and item.gain_over_overall_ate > 0.0],
            key=lambda item: (item.gain_over_overall_ate, item.mean_score),
            reverse=True,
        )[:3]
    ]
    suppression_candidate_deciles = [
        decile.decile_rank
        for decile in deciles
        if decile.observed_ate is not None and decile.observed_ate <= 0.0
    ]

    report = ModelBasedUpliftDecileReport(
        report_name="phase4_model_based_uplift_deciles",
        outcome_column=outcome_column,
        split_name=split_name,
        model_name=str(training_report["model_name"]),
        score_column=score_column,
        comparison_report_path=str(comparison_report_path),
        source_metrics_report_path=str(source_metrics_report_path),
        source_score_output_path=str(source_score_output_path),
        scored_view_path=str(scored_view_path),
        output_report_path=str(output_report_path),
        decile_count=bucket_count,
        overall_observed_ate=overall_observed_ate,
        top_decile_observed_ate=deciles[0].observed_ate,
        bottom_decile_observed_ate=deciles[-1].observed_ate,
        observed_top_bottom_gap=observed_top_bottom_gap,
        top_persuadable_deciles=top_persuadable_deciles,
        suppression_candidate_deciles=suppression_candidate_deciles,
        deciles=deciles,
    )

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return report
