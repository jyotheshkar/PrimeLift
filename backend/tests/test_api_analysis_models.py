"""Tests for the Phase 6 model comparison analysis API slice."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from primelift.api import create_app


def _build_phase3_model_report_payload() -> dict[str, object]:
    """Return a minimal valid Phase 3 comparison report payload for API tests."""

    conversion_scorecard = {
        "model_name": "drlearner_conversion",
        "outcome_column": "conversion",
        "split_name": "test",
        "metrics_report_path": "artifacts/metrics/drlearner_conversion_training_report.json",
        "overall_observed_ate": 0.01,
        "top_decile_observed_ate": 0.03,
        "bottom_decile_observed_ate": 0.0,
        "top_decile_gain_over_baseline": 0.02,
        "bottom_decile_gain_over_baseline": -0.01,
        "observed_top_bottom_gap": 0.03,
        "mean_predicted_cate": 0.012,
        "std_predicted_cate": 0.02,
        "positive_cate_share": 0.8,
        "top_decile_mean_predicted_cate": 0.05,
        "bottom_decile_mean_predicted_cate": -0.02,
        "interval_capable": False,
        "mean_interval_width": None,
        "top_segments": ["High Intent Returners"],
        "bottom_segments": ["Lapsed Users"],
    }
    revenue_scorecard = {
        "model_name": "drlearner_revenue",
        "outcome_column": "revenue",
        "split_name": "test",
        "metrics_report_path": "artifacts/metrics/drlearner_revenue_training_report.json",
        "overall_observed_ate": 1.1,
        "top_decile_observed_ate": 5.9,
        "bottom_decile_observed_ate": 0.7,
        "top_decile_gain_over_baseline": 4.8,
        "bottom_decile_gain_over_baseline": -0.4,
        "observed_top_bottom_gap": 5.2,
        "mean_predicted_cate": 1.0,
        "std_predicted_cate": 6.0,
        "positive_cate_share": 0.85,
        "top_decile_mean_predicted_cate": 11.0,
        "bottom_decile_mean_predicted_cate": -8.0,
        "interval_capable": False,
        "mean_interval_width": None,
        "top_segments": ["High Intent Returners"],
        "bottom_segments": ["Lapsed Users"],
    }
    return {
        "report_name": "phase3_model_comparison",
        "comparison_split": "test",
        "generated_from_reports": [
            "artifacts/metrics/drlearner_conversion_training_report.json",
            "artifacts/metrics/drlearner_revenue_training_report.json",
        ],
        "conversion_comparison": {
            "outcome_column": "conversion",
            "split_name": "test",
            "baseline_observed_ate": 0.01,
            "ranked_models": [conversion_scorecard],
            "champion_model_name": "drlearner_conversion",
            "champion_reason": "Highest top-decile observed uplift.",
            "challenger_model_name": None,
            "challenger_reason": None,
        },
        "revenue_comparison": {
            "outcome_column": "revenue",
            "split_name": "test",
            "baseline_observed_ate": 1.1,
            "ranked_models": [revenue_scorecard],
            "champion_model_name": "drlearner_revenue",
            "champion_reason": "Highest top-decile observed revenue effect.",
            "challenger_model_name": None,
            "challenger_reason": None,
        },
        "revised_phase_3_status": "complete",
        "next_recommended_phase": 4,
        "next_recommended_focus": "Model-based uplift reporting and decile analysis.",
    }


def test_get_analysis_models_returns_saved_comparison_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The models endpoint should load the saved comparison report and summarize it."""

    import primelift.api.analysis as analysis_api_module

    report_path = tmp_path / "phase3_model_comparison_report.json"
    report_path.write_text(
        json.dumps(_build_phase3_model_report_payload(), indent=2),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH",
        report_path,
    )

    client = TestClient(create_app())
    response = client.get("/analysis/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["report_name"] == "phase3_model_comparison"
    assert payload["comparison_split"] == "test"
    assert payload["conversion_champion_model_name"] == "drlearner_conversion"
    assert payload["revenue_champion_model_name"] == "drlearner_revenue"
    assert payload["report"]["conversion_comparison"]["ranked_models"][0]["model_name"] == (
        "drlearner_conversion"
    )


def test_get_analysis_models_returns_not_found_when_report_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The models endpoint should return 404 if the comparison report is absent."""

    import primelift.api.analysis as analysis_api_module

    missing_path = tmp_path / "missing_phase3_report.json"
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH",
        missing_path,
    )

    client = TestClient(create_app())
    response = client.get("/analysis/models")

    assert response.status_code == 404
    assert "Phase 3 model comparison report was not found" in response.json()["detail"]
