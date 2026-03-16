"""Tests for the Phase 6 recommendations analysis API slice."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from primelift.api import create_app


def _build_phase5_closeout_payload() -> dict[str, object]:
    """Return a minimal valid Phase 5 closeout report payload for API tests."""

    return {
        "report_name": "phase5_decision_closeout",
        "split_name": "test",
        "targeting_report_path": "artifacts/metrics/phase5_targeting_recommendation_report.json",
        "budget_report_path": "artifacts/metrics/phase5_budget_allocation_report.json",
        "policy_tree_report_path": "artifacts/metrics/drpolicytree_conversion_policy_report.json",
        "policy_forest_report_path": "artifacts/metrics/drpolicyforest_conversion_policy_report.json",
        "output_report_path": "artifacts/metrics/phase5_decision_closeout_report.json",
        "final_segment_actions_path": "artifacts/reports/phase5_final_segment_actions.csv",
        "policy_comparison": {
            "champion_model_name": "drpolicyforest_conversion",
            "champion_value": 0.1234,
            "runner_up_model_name": "always_treat_baseline",
            "runner_up_value": 0.1227,
            "always_treat_value": 0.1227,
            "always_control_value": 0.1127,
            "forest_value": 0.1234,
            "tree_value": 0.1220,
            "champion_gain_over_runner_up": 0.0007,
            "champion_gain_over_always_treat": 0.0007,
            "champion_gain_over_always_control": 0.0107,
            "champion_is_ml_model": True,
            "champion_reason": "DRPolicyForest is the current champion.",
        },
        "prioritized_segments": [
            {
                "segment": "High Intent Returners",
                "action": "prioritize",
                "recommended_budget": 37869.54,
                "budget_share": 0.3787,
                "mean_predicted_conversion_effect": 0.0229,
                "observed_conversion_ate": 0.0243,
                "mean_predicted_revenue_effect": 3.05,
                "policy_alignment": "champion_policy_treat",
                "rationale": "Prioritize High Intent Returners.",
            }
        ],
        "suppressed_segments": [
            {
                "segment": "Lapsed Users",
                "action": "suppress",
                "recommended_budget": 0.0,
                "budget_share": 0.0,
                "mean_predicted_conversion_effect": 0.0002,
                "observed_conversion_ate": -0.0080,
                "mean_predicted_revenue_effect": 0.70,
                "policy_alignment": "champion_policy_holdout",
                "rationale": "Suppress Lapsed Users.",
            }
        ],
        "top_target_users": [
            {
                "user_id": "LON-000001",
                "action": "target",
                "segment": "High Intent Returners",
                "london_borough": "Hackney",
                "predicted_effect": 0.42,
                "rationale": "High predicted incremental impact.",
            }
        ],
        "top_suppress_users": [
            {
                "user_id": "LON-000002",
                "action": "suppress",
                "segment": "Lapsed Users",
                "london_borough": "Camden",
                "predicted_effect": -0.18,
                "rationale": "Low predicted incremental impact.",
            }
        ],
        "final_action_summary": (
            "Use DRPolicyForest as the current policy champion. "
            "Prioritize High Intent Returners; suppress Lapsed Users."
        ),
        "revised_phase_5_status": "complete",
        "next_recommended_phase": 6,
        "next_recommended_focus": "FastAPI backend endpoints for dataset, analysis, and recommendations.",
    }


def test_get_analysis_recommendations_returns_saved_phase5_closeout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The recommendations endpoint should load the saved Phase 5 closeout report."""

    import primelift.api.analysis as analysis_api_module

    closeout_path = tmp_path / "phase5_decision_closeout_report.json"
    closeout_path.write_text(
        json.dumps(_build_phase5_closeout_payload(), indent=2),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH",
        closeout_path,
    )

    client = TestClient(create_app())
    response = client.get("/analysis/recommendations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["policy_champion_model_name"] == "drpolicyforest_conversion"
    assert payload["champion_is_ml_model"] is True
    assert payload["prioritized_segment_count"] == 1
    assert payload["suppressed_segment_count"] == 1
    assert payload["report"]["final_action_summary"].startswith("Use DRPolicyForest")


def test_get_analysis_recommendations_returns_not_found_when_closeout_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The recommendations endpoint should return 404 if the closeout report is absent."""

    import primelift.api.analysis as analysis_api_module

    missing_path = tmp_path / "missing_phase5_closeout_report.json"
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH",
        missing_path,
    )

    client = TestClient(create_app())
    response = client.get("/analysis/recommendations")

    assert response.status_code == 404
    assert "Phase 5 decision closeout report was not found" in response.json()["detail"]
