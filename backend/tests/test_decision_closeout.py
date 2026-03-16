"""Tests for the final revised Phase 5 decision closeout slice."""

from __future__ import annotations

import json
from pathlib import Path

from primelift.decision import generate_phase5_decision_closeout_report


def _write_closeout_test_artifacts(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Create minimal Phase 5 JSON artifacts for closeout tests."""

    targeting_report_path = tmp_path / "targeting_report.json"
    targeting_report = {
        "split_name": "test",
        "top_target_users": [
            {
                "user_id": "u1",
                "segment": "High Intent Returners",
                "london_borough": "Hackney",
                "predicted_effect": 0.18,
                "rationale": "Strong target candidate.",
            }
        ],
        "top_suppress_users": [
            {
                "user_id": "u9",
                "segment": "Lapsed Users",
                "london_borough": "Camden",
                "predicted_effect": -0.03,
                "rationale": "Suppress candidate.",
            }
        ],
    }
    targeting_report_path.write_text(json.dumps(targeting_report), encoding="utf-8")

    budget_report_path = tmp_path / "budget_report.json"
    budget_report = {
        "top_budget_segments": [
            {
                "segment": "High Intent Returners",
                "recommended_budget": 50000.0,
                "budget_share": 0.5,
                "mean_predicted_conversion_effect": 0.02,
                "observed_conversion_ate": 0.03,
                "mean_predicted_revenue_effect": 2.5,
            },
            {
                "segment": "Young Professionals",
                "recommended_budget": 30000.0,
                "budget_share": 0.3,
                "mean_predicted_conversion_effect": 0.012,
                "observed_conversion_ate": 0.016,
                "mean_predicted_revenue_effect": 1.2,
            },
        ],
        "suppressed_segments": [
            {
                "segment": "Lapsed Users",
                "recommended_budget": 0.0,
                "mean_predicted_conversion_effect": -0.002,
                "observed_conversion_ate": -0.01,
                "mean_predicted_revenue_effect": 0.4,
            }
        ],
    }
    budget_report_path.write_text(json.dumps(budget_report), encoding="utf-8")

    policy_tree_report_path = tmp_path / "policy_tree_report.json"
    policy_tree_report = {
        "estimated_policy_value": 0.121,
        "always_treat_value": 0.122,
        "always_control_value": 0.111,
        "top_treat_segments": [{"segment": "High Intent Returners"}],
        "top_control_segments": [{"segment": "Lapsed Users"}],
    }
    policy_tree_report_path.write_text(json.dumps(policy_tree_report), encoding="utf-8")

    policy_forest_report_path = tmp_path / "policy_forest_report.json"
    policy_forest_report = {
        "estimated_policy_value": 0.124,
        "always_treat_value": 0.122,
        "always_control_value": 0.111,
        "top_treat_segments": [
            {"segment": "High Intent Returners"},
            {"segment": "Young Professionals"},
        ],
        "top_control_segments": [{"segment": "Lapsed Users"}],
    }
    policy_forest_report_path.write_text(json.dumps(policy_forest_report), encoding="utf-8")

    return (
        targeting_report_path,
        budget_report_path,
        policy_tree_report_path,
        policy_forest_report_path,
    )


def test_generate_phase5_decision_closeout_report_creates_outputs(tmp_path: Path) -> None:
    """The closeout slice should create both the JSON report and segment action CSV."""

    artifact_paths = _write_closeout_test_artifacts(tmp_path)
    output_report_path = tmp_path / "phase5_closeout.json"
    final_segment_actions_path = tmp_path / "final_segment_actions.csv"

    report = generate_phase5_decision_closeout_report(
        targeting_report_path=artifact_paths[0],
        budget_report_path=artifact_paths[1],
        policy_tree_report_path=artifact_paths[2],
        policy_forest_report_path=artifact_paths[3],
        output_report_path=output_report_path,
        final_segment_actions_path=final_segment_actions_path,
    )

    assert report.report_name == "phase5_decision_closeout"
    assert output_report_path.exists()
    assert final_segment_actions_path.exists()
    assert report.revised_phase_5_status == "complete"


def test_generate_phase5_decision_closeout_report_selects_policy_champion_and_merges_actions(
    tmp_path: Path,
) -> None:
    """The closeout report should choose the strongest policy and merge segment actions."""

    artifact_paths = _write_closeout_test_artifacts(tmp_path)

    report = generate_phase5_decision_closeout_report(
        targeting_report_path=artifact_paths[0],
        budget_report_path=artifact_paths[1],
        policy_tree_report_path=artifact_paths[2],
        policy_forest_report_path=artifact_paths[3],
        output_report_path=tmp_path / "phase5_closeout.json",
        final_segment_actions_path=tmp_path / "final_segment_actions.csv",
    )

    assert report.policy_comparison.champion_model_name == "drpolicyforest_conversion"
    assert report.policy_comparison.champion_is_ml_model is True
    assert report.prioritized_segments[0].segment == "High Intent Returners"
    assert report.prioritized_segments[0].policy_alignment == "champion_policy_treat"
    assert report.suppressed_segments[0].segment == "Lapsed Users"
    assert report.suppressed_segments[0].policy_alignment == "champion_policy_holdout"
    assert report.top_target_users[0].user_id == "u1"
    assert report.top_suppress_users[0].user_id == "u9"
