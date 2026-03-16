"""Tests for the Phase 6 segment analysis API slice."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from primelift.api import create_app


def _build_rollup_report_payload() -> dict[str, object]:
    """Return a minimal valid Phase 4 rollup report payload for API tests."""

    return {
        "report_name": "phase4_model_based_group_rollups",
        "outcome_column": "conversion",
        "split_name": "test",
        "model_name": "drlearner_conversion",
        "score_column": "predicted_cate_drlearner_conversion",
        "comparison_report_path": "artifacts/metrics/phase3_model_comparison_report.json",
        "source_metrics_report_path": "artifacts/metrics/drlearner_conversion_training_report.json",
        "source_score_output_path": "artifacts/reports/drlearner_conversion_test_scores.csv",
        "raw_dataset_path": "data/raw/london_campaign_users_100k.csv",
        "enriched_scored_view_path": "artifacts/reports/phase4_conversion_enriched_scored_view.csv",
        "rollup_table_path": "artifacts/reports/phase4_conversion_rollup_table.csv",
        "output_report_path": "artifacts/metrics/phase4_conversion_rollup_report.json",
        "overall_observed_ate": 0.01,
        "group_columns": ["segment"],
        "top_persuadable_cohorts": [
            {
                "group_column": "segment",
                "group_value": "High Intent Returners",
                "mean_predicted_effect": 0.023,
                "observed_ate": 0.024,
            }
        ],
        "suppression_candidates": [
            {
                "group_column": "segment",
                "group_value": "Lapsed Users",
                "mean_predicted_effect": 0.0002,
                "observed_ate": -0.008,
            }
        ],
        "reports": [
            {
                "group_column": "segment",
                "outcome_column": "conversion",
                "result_count": 2,
                "top_positive_groups": ["High Intent Returners"],
                "suppression_candidates": ["Lapsed Users"],
                "results": [
                    {
                        "group_column": "segment",
                        "group_value": "High Intent Returners",
                        "outcome_column": "conversion",
                        "group_size": 2000,
                        "treated_count": 1000,
                        "control_count": 1000,
                        "mean_predicted_effect": 0.023,
                        "median_predicted_effect": 0.021,
                        "min_predicted_effect": -0.04,
                        "max_predicted_effect": 0.15,
                        "positive_effect_share": 0.88,
                        "observed_ate": 0.024,
                        "gain_over_overall_ate": 0.014,
                        "recommendation_label": "prioritize",
                    },
                    {
                        "group_column": "segment",
                        "group_value": "Lapsed Users",
                        "outcome_column": "conversion",
                        "group_size": 1200,
                        "treated_count": 600,
                        "control_count": 600,
                        "mean_predicted_effect": 0.0002,
                        "median_predicted_effect": 0.0,
                        "min_predicted_effect": -0.03,
                        "max_predicted_effect": 0.04,
                        "positive_effect_share": 0.68,
                        "observed_ate": -0.008,
                        "gain_over_overall_ate": -0.018,
                        "recommendation_label": "suppress",
                    },
                ],
            }
        ],
    }


def _build_decile_report_payload() -> dict[str, object]:
    """Return a minimal valid Phase 4 decile report payload for API tests."""

    return {
        "report_name": "phase4_model_based_uplift_deciles",
        "outcome_column": "conversion",
        "split_name": "test",
        "model_name": "drlearner_conversion",
        "score_column": "predicted_cate_drlearner_conversion",
        "comparison_report_path": "artifacts/metrics/phase3_model_comparison_report.json",
        "source_metrics_report_path": "artifacts/metrics/drlearner_conversion_training_report.json",
        "source_score_output_path": "artifacts/reports/drlearner_conversion_test_scores.csv",
        "scored_view_path": "artifacts/reports/phase4_conversion_scored_view.csv",
        "output_report_path": "artifacts/metrics/phase4_conversion_decile_report.json",
        "decile_count": 10,
        "overall_observed_ate": 0.01,
        "top_decile_observed_ate": 0.036,
        "bottom_decile_observed_ate": -0.001,
        "observed_top_bottom_gap": 0.037,
        "top_persuadable_deciles": [1, 2, 3],
        "suppression_candidate_deciles": [8, 9],
        "deciles": [
            {
                "decile_rank": 1,
                "decile_label": "D01_highest",
                "row_count": 1500,
                "min_score": 0.03,
                "mean_score": 0.06,
                "max_score": 0.4,
                "treated_count": 750,
                "control_count": 750,
                "treated_outcome_mean": 0.25,
                "control_outcome_mean": 0.21,
                "observed_ate": 0.04,
                "gain_over_overall_ate": 0.03,
            },
            {
                "decile_rank": 9,
                "decile_label": "D09_mid",
                "row_count": 1500,
                "min_score": -0.01,
                "mean_score": -0.002,
                "max_score": 0.0,
                "treated_count": 750,
                "control_count": 750,
                "treated_outcome_mean": 0.07,
                "control_outcome_mean": 0.08,
                "observed_ate": -0.01,
                "gain_over_overall_ate": -0.02,
            },
        ],
    }


def _build_validation_report_payload() -> dict[str, object]:
    """Return a minimal valid Phase 4 validation report payload for API tests."""

    return {
        "report_name": "phase4_validation_summary",
        "outcome_column": "conversion",
        "split_name": "test",
        "model_name": "drlearner_conversion",
        "decile_report_path": "artifacts/metrics/phase4_conversion_decile_report.json",
        "rollup_report_path": "artifacts/metrics/phase4_conversion_rollup_report.json",
        "output_report_path": "artifacts/metrics/phase4_conversion_validation_summary.json",
        "overall_observed_ate": 0.01,
        "top_decile_observed_ate": 0.036,
        "bottom_decile_observed_ate": -0.001,
        "top_decile_gain_over_overall_ate": 0.026,
        "observed_top_bottom_gap": 0.037,
        "uplift_concentration_ratio": 3.6,
        "positive_decile_count": 8,
        "negative_decile_count": 2,
        "best_decile_rank": 1,
        "worst_decile_rank": 9,
        "monotonicity_break_count": 3,
        "top_persuadable_deciles": [1, 2, 3],
        "suppression_candidate_deciles": [8, 9],
        "top_persuadable_cohorts": [
            {
                "group_column": "segment",
                "group_value": "High Intent Returners",
                "mean_predicted_effect": 0.023,
                "observed_ate": 0.024,
            }
        ],
        "suppression_candidates": [
            {
                "group_column": "segment",
                "group_value": "Lapsed Users",
                "mean_predicted_effect": 0.0002,
                "observed_ate": -0.008,
            }
        ],
        "dimension_summaries": [
            {
                "group_column": "segment",
                "prioritize_group_count": 1,
                "suppress_group_count": 1,
                "top_positive_groups": ["High Intent Returners"],
                "suppression_candidates": ["Lapsed Users"],
                "strongest_positive_group": "High Intent Returners",
                "strongest_positive_observed_ate": 0.024,
                "strongest_negative_group": "Lapsed Users",
                "strongest_negative_observed_ate": -0.008,
            }
        ],
        "validation_verdict": "promising_but_noisy",
        "validation_reason": "Top-ranked deciles beat the baseline.",
    }


def test_get_analysis_segments_returns_saved_phase4_outputs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The segments endpoint should load the saved rollup and validation reports."""

    import primelift.api.analysis as analysis_api_module

    decile_path = tmp_path / "phase4_decile_report.json"
    rollup_path = tmp_path / "phase4_rollup_report.json"
    validation_path = tmp_path / "phase4_validation_summary.json"
    decile_path.write_text(json.dumps(_build_decile_report_payload(), indent=2), encoding="utf-8")
    rollup_path.write_text(json.dumps(_build_rollup_report_payload(), indent=2), encoding="utf-8")
    validation_path.write_text(
        json.dumps(_build_validation_report_payload(), indent=2),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH",
        decile_path,
    )
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH",
        rollup_path,
    )
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH",
        validation_path,
    )

    client = TestClient(create_app())
    response = client.get("/analysis/segments")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["model_name"] == "drlearner_conversion"
    assert payload["validation_verdict"] == "promising_but_noisy"
    assert payload["top_decile_gain_over_overall_ate"] == 0.026
    assert payload["monotonicity_break_count"] == 3
    assert payload["deciles"][0]["decile_rank"] == 1
    assert payload["top_persuadable_cohorts"][0]["group_value"] == "High Intent Returners"
    assert payload["suppression_candidates"][0]["group_value"] == "Lapsed Users"
    assert payload["reports"][0]["group_column"] == "segment"


def test_get_analysis_segments_returns_not_found_when_rollup_report_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The segments endpoint should return 404 if the rollup report is absent."""

    import primelift.api.analysis as analysis_api_module

    missing_decile_path = tmp_path / "missing_decile_report.json"
    missing_rollup_path = tmp_path / "missing_rollup_report.json"
    validation_path = tmp_path / "phase4_validation_summary.json"
    validation_path.write_text(
        json.dumps(_build_validation_report_payload(), indent=2),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH",
        missing_decile_path,
    )
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH",
        missing_rollup_path,
    )
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH",
        validation_path,
    )

    client = TestClient(create_app())
    response = client.get("/analysis/segments")

    assert response.status_code == 404
    assert "Phase 4 conversion decile report was not found" in response.json()["detail"]


def test_get_analysis_segments_returns_server_error_for_mismatched_models(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The segments endpoint should fail loudly if the two Phase 4 artifacts disagree."""

    import primelift.api.analysis as analysis_api_module

    decile_path = tmp_path / "phase4_decile_report.json"
    rollup_path = tmp_path / "phase4_rollup_report.json"
    validation_path = tmp_path / "phase4_validation_summary.json"
    validation_payload = _build_validation_report_payload()
    validation_payload["model_name"] = "causal_forest_conversion"

    decile_path.write_text(json.dumps(_build_decile_report_payload(), indent=2), encoding="utf-8")
    rollup_path.write_text(json.dumps(_build_rollup_report_payload(), indent=2), encoding="utf-8")
    validation_path.write_text(json.dumps(validation_payload, indent=2), encoding="utf-8")
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH",
        decile_path,
    )
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH",
        rollup_path,
    )
    monkeypatch.setattr(
        analysis_api_module,
        "DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH",
        validation_path,
    )

    client = TestClient(create_app())
    response = client.get("/analysis/segments")

    assert response.status_code == 500
    assert "inconsistent" in response.json()["detail"]
