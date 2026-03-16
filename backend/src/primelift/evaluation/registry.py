"""Registry of planned evaluation outputs for the causal ML roadmap."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EvaluationBlueprint(BaseModel):
    """Serializable metadata for one evaluation artifact or report."""

    model_config = ConfigDict(frozen=True)

    name: str
    category: str
    target_phase: int
    purpose: str
    status: str


def get_default_evaluation_blueprints() -> list[EvaluationBlueprint]:
    """Return the default evaluation deliverables for the revised ML roadmap."""

    return [
        EvaluationBlueprint(
            name="ate_baseline_summary",
            category="baseline_metrics",
            target_phase=3,
            purpose="Store treated and control means, ATE, and confidence intervals.",
            status="implemented",
        ),
        EvaluationBlueprint(
            name="model_comparison_report",
            category="model_selection",
            target_phase=3,
            purpose="Compare baseline, XLearner, DRLearner, and CausalForestDML outputs.",
            status="implemented",
        ),
        EvaluationBlueprint(
            name="uplift_decile_report",
            category="ranking_quality",
            target_phase=4,
            purpose="Inspect whether high-scored users concentrate observed incremental lift.",
            status="implemented",
        ),
        EvaluationBlueprint(
            name="segment_rollup_report",
            category="business_reporting",
            target_phase=4,
            purpose="Summarize model-based uplift across segments, boroughs, devices, and channels.",
            status="implemented",
        ),
        EvaluationBlueprint(
            name="phase4_validation_summary",
            category="ranking_quality",
            target_phase=4,
            purpose="Tie decile and rollup evidence into one compact validation summary.",
            status="implemented",
        ),
        EvaluationBlueprint(
            name="policy_recommendation_report",
            category="decisioning",
            target_phase=5,
            purpose="Store targeting and suppression recommendations with budget rationale.",
            status="planned",
        ),
    ]
