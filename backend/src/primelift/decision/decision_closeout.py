"""Final Phase 5 decision closeout reporting for revised PrimeLift."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, ConfigDict

from primelift.utils.paths import (
    DEFAULT_DRPOLICYFOREST_CONVERSION_REPORT_PATH,
    DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH,
    DEFAULT_PHASE5_BUDGET_ALLOCATION_REPORT_PATH,
    DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH,
    DEFAULT_PHASE5_FINAL_SEGMENT_ACTIONS_PATH,
    DEFAULT_PHASE5_TARGETING_REPORT_PATH,
)


class Phase5PolicyComparison(BaseModel):
    """Serializable comparison across the current Phase 5 policy options."""

    model_config = ConfigDict(frozen=True)

    champion_model_name: str
    champion_value: float
    runner_up_model_name: str
    runner_up_value: float
    always_treat_value: float
    always_control_value: float
    forest_value: float
    tree_value: float
    champion_gain_over_runner_up: float
    champion_gain_over_always_treat: float
    champion_gain_over_always_control: float
    champion_is_ml_model: bool
    champion_reason: str


class FinalSegmentAction(BaseModel):
    """Serializable final segment recommendation for the Phase 5 closeout."""

    model_config = ConfigDict(frozen=True)

    segment: str
    action: str
    recommended_budget: float
    budget_share: float
    mean_predicted_conversion_effect: float
    observed_conversion_ate: float | None
    mean_predicted_revenue_effect: float
    policy_alignment: str
    rationale: str


class FinalUserAction(BaseModel):
    """Serializable final user recommendation for the Phase 5 closeout."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    action: str
    segment: str
    london_borough: str
    predicted_effect: float
    rationale: str


class Phase5DecisionCloseoutReport(BaseModel):
    """Serializable final closeout report for revised Phase 5."""

    model_config = ConfigDict(frozen=True)

    report_name: str
    split_name: str
    targeting_report_path: str
    budget_report_path: str
    policy_tree_report_path: str
    policy_forest_report_path: str
    output_report_path: str
    final_segment_actions_path: str
    policy_comparison: Phase5PolicyComparison
    prioritized_segments: list[FinalSegmentAction]
    suppressed_segments: list[FinalSegmentAction]
    top_target_users: list[FinalUserAction]
    top_suppress_users: list[FinalUserAction]
    final_action_summary: str
    revised_phase_5_status: str
    next_recommended_phase: int
    next_recommended_focus: str


def _load_json(path: Path) -> dict:
    """Load a JSON artifact from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _select_policy_champion(
    *,
    forest_report: dict,
    tree_report: dict,
) -> Phase5PolicyComparison:
    """Select the strongest current Phase 5 policy option."""

    candidate_values = {
        "drpolicyforest_conversion": float(forest_report["estimated_policy_value"]),
        "drpolicytree_conversion": float(tree_report["estimated_policy_value"]),
        "always_treat_baseline": float(forest_report["always_treat_value"]),
        "always_control_baseline": float(forest_report["always_control_value"]),
    }
    ranked = sorted(candidate_values.items(), key=lambda item: item[1], reverse=True)
    champion_name, champion_value = ranked[0]
    runner_up_name, runner_up_value = ranked[1]
    champion_is_ml_model = champion_name.startswith("drpolicy")

    if champion_name == "drpolicyforest_conversion":
        champion_reason = (
            "DRPolicyForest is the current champion because it beats the policy tree and both "
            "naive baselines on the holdout split."
        )
    elif champion_name == "drpolicytree_conversion":
        champion_reason = (
            "DRPolicyTree is the current champion because it beats the forest challenger and both "
            "naive baselines on the holdout split."
        )
    else:
        champion_reason = (
            f"{champion_name} currently beats the learned policy models on the holdout split, so "
            "the learned policy layer is not yet the production winner."
        )

    return Phase5PolicyComparison(
        champion_model_name=champion_name,
        champion_value=champion_value,
        runner_up_model_name=runner_up_name,
        runner_up_value=runner_up_value,
        always_treat_value=float(forest_report["always_treat_value"]),
        always_control_value=float(forest_report["always_control_value"]),
        forest_value=float(forest_report["estimated_policy_value"]),
        tree_value=float(tree_report["estimated_policy_value"]),
        champion_gain_over_runner_up=float(champion_value - runner_up_value),
        champion_gain_over_always_treat=float(
            champion_value - float(forest_report["always_treat_value"])
        ),
        champion_gain_over_always_control=float(
            champion_value - float(forest_report["always_control_value"])
        ),
        champion_is_ml_model=champion_is_ml_model,
        champion_reason=champion_reason,
    )


def _build_policy_alignment_sets(
    *,
    forest_report: dict,
    tree_report: dict,
    policy_champion_name: str,
) -> tuple[set[str], set[str]]:
    """Build the champion policy treat and control segment sets."""

    if policy_champion_name == "drpolicytree_conversion":
        champion_report = tree_report
    else:
        champion_report = forest_report

    treat_segments = {
        str(item["segment"]) for item in champion_report.get("top_treat_segments", [])
    }
    control_segments = {
        str(item["segment"]) for item in champion_report.get("top_control_segments", [])
    }
    return treat_segments, control_segments


def _build_policy_alignment_label(
    segment: str,
    treat_segments: set[str],
    control_segments: set[str],
) -> str:
    """Build a compact policy-alignment label for one segment."""

    if segment in treat_segments:
        return "champion_policy_treat"
    if segment in control_segments:
        return "champion_policy_holdout"
    return "neutral"


def _build_prioritized_segment_actions(
    *,
    budget_report: dict,
    treat_segments: set[str],
    control_segments: set[str],
) -> list[FinalSegmentAction]:
    """Build prioritized segment actions from the budget allocation slice."""

    rows = []
    for item in budget_report["top_budget_segments"]:
        segment_name = str(item["segment"])
        policy_alignment = _build_policy_alignment_label(
            segment_name,
            treat_segments,
            control_segments,
        )
        rationale = (
            f"Prioritize {segment_name} with budget {float(item['recommended_budget']):.2f}; "
            f"policy alignment: {policy_alignment}."
        )
        rows.append(
            FinalSegmentAction(
                segment=segment_name,
                action="prioritize",
                recommended_budget=float(item["recommended_budget"]),
                budget_share=float(item["budget_share"]),
                mean_predicted_conversion_effect=float(item["mean_predicted_conversion_effect"]),
                observed_conversion_ate=(
                    float(item["observed_conversion_ate"])
                    if item["observed_conversion_ate"] is not None
                    else None
                ),
                mean_predicted_revenue_effect=float(item["mean_predicted_revenue_effect"]),
                policy_alignment=policy_alignment,
                rationale=rationale,
            )
        )
    return rows


def _build_suppressed_segment_actions(
    *,
    budget_report: dict,
    treat_segments: set[str],
    control_segments: set[str],
) -> list[FinalSegmentAction]:
    """Build suppressed segment actions from the budget allocation slice."""

    rows = []
    for item in budget_report["suppressed_segments"]:
        segment_name = str(item["segment"])
        policy_alignment = _build_policy_alignment_label(
            segment_name,
            treat_segments,
            control_segments,
        )
        rationale = (
            f"Suppress {segment_name} with zero incremental budget; "
            f"policy alignment: {policy_alignment}."
        )
        rows.append(
            FinalSegmentAction(
                segment=segment_name,
                action="suppress",
                recommended_budget=float(item["recommended_budget"]),
                budget_share=0.0,
                mean_predicted_conversion_effect=float(item["mean_predicted_conversion_effect"]),
                observed_conversion_ate=(
                    float(item["observed_conversion_ate"])
                    if item["observed_conversion_ate"] is not None
                    else None
                ),
                mean_predicted_revenue_effect=float(item["mean_predicted_revenue_effect"]),
                policy_alignment=policy_alignment,
                rationale=rationale,
            )
        )
    return rows


def _build_user_actions(users: list[dict], action: str) -> list[FinalUserAction]:
    """Convert saved user actions into the closeout contract."""

    return [
        FinalUserAction(
            user_id=str(item["user_id"]),
            action=action,
            segment=str(item["segment"]),
            london_borough=str(item["london_borough"]),
            predicted_effect=float(item["predicted_effect"]),
            rationale=str(item["rationale"]),
        )
        for item in users[:10]
    ]


def _build_final_summary(
    *,
    policy_comparison: Phase5PolicyComparison,
    prioritized_segments: list[FinalSegmentAction],
    suppressed_segments: list[FinalSegmentAction],
) -> str:
    """Create the final human-readable Phase 5 action summary."""

    top_priorities = ", ".join(segment.segment for segment in prioritized_segments[:3]) or "no priority segments"
    suppressions = ", ".join(segment.segment for segment in suppressed_segments[:2]) or "no suppression segments"
    champion_label = (
        "DRPolicyForest"
        if policy_comparison.champion_model_name == "drpolicyforest_conversion"
        else "DRPolicyTree"
        if policy_comparison.champion_model_name == "drpolicytree_conversion"
        else policy_comparison.champion_model_name
    )
    return (
        f"Use {champion_label} as the current policy champion. Prioritize {top_priorities}; "
        f"suppress {suppressions}."
    )


def generate_phase5_decision_closeout_report(
    *,
    targeting_report_path: Path = DEFAULT_PHASE5_TARGETING_REPORT_PATH,
    budget_report_path: Path = DEFAULT_PHASE5_BUDGET_ALLOCATION_REPORT_PATH,
    policy_tree_report_path: Path = DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH,
    policy_forest_report_path: Path = DEFAULT_DRPOLICYFOREST_CONVERSION_REPORT_PATH,
    output_report_path: Path = DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH,
    final_segment_actions_path: Path = DEFAULT_PHASE5_FINAL_SEGMENT_ACTIONS_PATH,
) -> Phase5DecisionCloseoutReport:
    """Generate the final closeout report for revised Phase 5."""

    targeting_report = _load_json(targeting_report_path)
    budget_report = _load_json(budget_report_path)
    policy_tree_report = _load_json(policy_tree_report_path)
    policy_forest_report = _load_json(policy_forest_report_path)

    policy_comparison = _select_policy_champion(
        forest_report=policy_forest_report,
        tree_report=policy_tree_report,
    )
    treat_segments, control_segments = _build_policy_alignment_sets(
        forest_report=policy_forest_report,
        tree_report=policy_tree_report,
        policy_champion_name=policy_comparison.champion_model_name,
    )

    prioritized_segments = _build_prioritized_segment_actions(
        budget_report=budget_report,
        treat_segments=treat_segments,
        control_segments=control_segments,
    )
    suppressed_segments = _build_suppressed_segment_actions(
        budget_report=budget_report,
        treat_segments=treat_segments,
        control_segments=control_segments,
    )

    final_action_summary = _build_final_summary(
        policy_comparison=policy_comparison,
        prioritized_segments=prioritized_segments,
        suppressed_segments=suppressed_segments,
    )

    segment_table = pd.DataFrame(
        [
            {
                "segment": item.segment,
                "action": item.action,
                "recommended_budget": item.recommended_budget,
                "budget_share": item.budget_share,
                "mean_predicted_conversion_effect": item.mean_predicted_conversion_effect,
                "observed_conversion_ate": item.observed_conversion_ate,
                "mean_predicted_revenue_effect": item.mean_predicted_revenue_effect,
                "policy_alignment": item.policy_alignment,
                "rationale": item.rationale,
            }
            for item in [*prioritized_segments, *suppressed_segments]
        ]
    )
    final_segment_actions_path.parent.mkdir(parents=True, exist_ok=True)
    segment_table.to_csv(final_segment_actions_path, index=False)

    report = Phase5DecisionCloseoutReport(
        report_name="phase5_decision_closeout",
        split_name=str(targeting_report["split_name"]),
        targeting_report_path=str(targeting_report_path),
        budget_report_path=str(budget_report_path),
        policy_tree_report_path=str(policy_tree_report_path),
        policy_forest_report_path=str(policy_forest_report_path),
        output_report_path=str(output_report_path),
        final_segment_actions_path=str(final_segment_actions_path),
        policy_comparison=policy_comparison,
        prioritized_segments=prioritized_segments,
        suppressed_segments=suppressed_segments,
        top_target_users=_build_user_actions(targeting_report["top_target_users"], "target"),
        top_suppress_users=_build_user_actions(targeting_report["top_suppress_users"], "suppress"),
        final_action_summary=final_action_summary,
        revised_phase_5_status="complete",
        next_recommended_phase=6,
        next_recommended_focus="FastAPI backend endpoints for dataset, analysis, and recommendations.",
    )

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return report
