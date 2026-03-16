"""Tests for the compact revised Phase 4 validation summary."""

from __future__ import annotations

import json
from pathlib import Path

from primelift.evaluation import generate_phase4_validation_summary


def _write_validation_test_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    """Create minimal Phase 4 decile and rollup reports for summary tests."""

    decile_report_path = tmp_path / "decile_report.json"
    decile_report = {
        "report_name": "phase4_model_based_uplift_deciles",
        "outcome_column": "conversion",
        "split_name": "test",
        "model_name": "drlearner_conversion",
        "overall_observed_ate": 0.01,
        "top_decile_observed_ate": 0.04,
        "bottom_decile_observed_ate": 0.005,
        "observed_top_bottom_gap": 0.035,
        "top_persuadable_deciles": [1, 2, 3],
        "suppression_candidate_deciles": [5, 9],
        "deciles": [
            {"decile_rank": 1, "observed_ate": 0.04},
            {"decile_rank": 2, "observed_ate": 0.03},
            {"decile_rank": 3, "observed_ate": 0.02},
            {"decile_rank": 4, "observed_ate": 0.01},
            {"decile_rank": 5, "observed_ate": -0.01},
            {"decile_rank": 6, "observed_ate": 0.005},
            {"decile_rank": 7, "observed_ate": 0.002},
            {"decile_rank": 8, "observed_ate": 0.001},
            {"decile_rank": 9, "observed_ate": -0.005},
            {"decile_rank": 10, "observed_ate": 0.005},
        ],
    }
    decile_report_path.write_text(json.dumps(decile_report), encoding="utf-8")

    rollup_report_path = tmp_path / "rollup_report.json"
    rollup_report = {
        "report_name": "phase4_model_based_group_rollups",
        "outcome_column": "conversion",
        "split_name": "test",
        "model_name": "drlearner_conversion",
        "top_persuadable_cohorts": [
            {
                "group_column": "segment",
                "group_value": "High Intent Returners",
                "mean_predicted_effect": 0.02,
                "observed_ate": 0.025,
            }
        ],
        "suppression_candidates": [
            {
                "group_column": "segment",
                "group_value": "Lapsed Users",
                "mean_predicted_effect": 0.001,
                "observed_ate": -0.008,
            }
        ],
        "reports": [
            {
                "group_column": "segment",
                "top_positive_groups": ["High Intent Returners", "Bargain Hunters"],
                "suppression_candidates": ["Lapsed Users"],
                "results": [
                    {
                        "group_value": "High Intent Returners",
                        "recommendation_label": "prioritize",
                        "observed_ate": 0.025,
                    },
                    {
                        "group_value": "Lapsed Users",
                        "recommendation_label": "suppress",
                        "observed_ate": -0.008,
                    },
                ],
            },
            {
                "group_column": "channel",
                "top_positive_groups": ["generic_search"],
                "suppression_candidates": ["app_entry"],
                "results": [
                    {
                        "group_value": "generic_search",
                        "recommendation_label": "prioritize",
                        "observed_ate": 0.03,
                    },
                    {
                        "group_value": "app_entry",
                        "recommendation_label": "suppress",
                        "observed_ate": -0.02,
                    },
                ],
            },
        ],
    }
    rollup_report_path.write_text(json.dumps(rollup_report), encoding="utf-8")
    return decile_report_path, rollup_report_path


def test_generate_phase4_validation_summary_creates_actionable_report(tmp_path: Path) -> None:
    """The summary should combine decile and rollup evidence into one report."""

    decile_report_path, rollup_report_path = _write_validation_test_artifacts(tmp_path)
    output_report_path = tmp_path / "validation_summary.json"

    report = generate_phase4_validation_summary(
        decile_report_path=decile_report_path,
        rollup_report_path=rollup_report_path,
        output_report_path=output_report_path,
    )

    assert report.report_name == "phase4_validation_summary"
    assert report.validation_verdict == "promising_but_noisy"
    assert report.best_decile_rank == 1
    assert report.worst_decile_rank == 5
    assert report.positive_decile_count == 8
    assert report.negative_decile_count == 2
    assert len(report.dimension_summaries) == 2
    assert output_report_path.exists()


def test_phase4_validation_summary_rejects_mismatched_reports(tmp_path: Path) -> None:
    """The summary should fail fast when the decile and rollup reports do not match."""

    decile_report_path, rollup_report_path = _write_validation_test_artifacts(tmp_path)
    bad_rollup = json.loads(rollup_report_path.read_text(encoding="utf-8"))
    bad_rollup["model_name"] = "xlearner_conversion"
    rollup_report_path.write_text(json.dumps(bad_rollup), encoding="utf-8")

    try:
        generate_phase4_validation_summary(
            decile_report_path=decile_report_path,
            rollup_report_path=rollup_report_path,
            output_report_path=tmp_path / "validation_summary.json",
        )
    except ValueError as error:
        assert "same model" in str(error)
    else:
        raise AssertionError("Expected a ValueError for mismatched Phase 4 reports.")
