"""Tests for the revised Phase 3 model comparison slice."""

from __future__ import annotations

import json
from pathlib import Path

from primelift.evaluation import generate_phase3_model_comparison_report


def _write_report(
    path: Path,
    *,
    model_name: str,
    outcome_column: str,
    top_decile_observed_ate: float,
    bottom_decile_observed_ate: float,
    overall_observed_ate: float,
    interval_width: float | None = None,
) -> None:
    """Write a minimal training report fixture for comparison tests."""

    split_evaluation = {
        "split_name": "test",
        "row_count": 1000,
        "mean_predicted_cate": overall_observed_ate,
        "std_predicted_cate": 0.02,
        "positive_cate_share": 0.8,
        "overall_observed_ate": overall_observed_ate,
        "top_decile_mean_predicted_cate": top_decile_observed_ate + 0.01,
        "top_decile_observed_ate": top_decile_observed_ate,
        "bottom_decile_mean_predicted_cate": bottom_decile_observed_ate - 0.01,
        "bottom_decile_observed_ate": bottom_decile_observed_ate,
        "top_segments_by_mean_predicted_cate": [
            {"segment": "High Intent Returners", "mean_predicted_cate": top_decile_observed_ate}
        ],
        "bottom_segments_by_mean_predicted_cate": [
            {"segment": "Lapsed Users", "mean_predicted_cate": bottom_decile_observed_ate}
        ],
    }
    if interval_width is not None:
        split_evaluation["mean_interval_width"] = interval_width

    report = {
        "model_name": model_name,
        "config": {
            "outcome_column": outcome_column,
        },
        "split_evaluations": [split_evaluation],
    }
    path.write_text(json.dumps(report), encoding="utf-8")


def test_generate_phase3_model_comparison_report_selects_expected_champions(tmp_path: Path) -> None:
    """The comparison report should rank models by holdout top-decile performance."""

    xlearner_path = tmp_path / "xlearner.json"
    drlearner_conv_path = tmp_path / "drlearner_conversion.json"
    causal_forest_path = tmp_path / "causal_forest.json"
    drlearner_revenue_path = tmp_path / "drlearner_revenue.json"

    _write_report(
        xlearner_path,
        model_name="xlearner_conversion",
        outcome_column="conversion",
        top_decile_observed_ate=0.01,
        bottom_decile_observed_ate=-0.002,
        overall_observed_ate=0.01,
    )
    _write_report(
        drlearner_conv_path,
        model_name="drlearner_conversion",
        outcome_column="conversion",
        top_decile_observed_ate=0.03,
        bottom_decile_observed_ate=0.005,
        overall_observed_ate=0.01,
    )
    _write_report(
        causal_forest_path,
        model_name="causal_forest_conversion",
        outcome_column="conversion",
        top_decile_observed_ate=0.015,
        bottom_decile_observed_ate=0.01,
        overall_observed_ate=0.01,
        interval_width=0.08,
    )
    _write_report(
        drlearner_revenue_path,
        model_name="drlearner_revenue",
        outcome_column="revenue",
        top_decile_observed_ate=5.0,
        bottom_decile_observed_ate=0.7,
        overall_observed_ate=1.1,
    )

    output_path = tmp_path / "comparison.json"
    report = generate_phase3_model_comparison_report(
        conversion_report_paths=[xlearner_path, drlearner_conv_path, causal_forest_path],
        revenue_report_paths=[drlearner_revenue_path],
        comparison_split="test",
        output_path=output_path,
    )

    assert report.conversion_comparison.champion_model_name == "drlearner_conversion"
    assert report.conversion_comparison.challenger_model_name == "causal_forest_conversion"
    assert report.revenue_comparison.champion_model_name == "drlearner_revenue"
    assert report.revised_phase_3_status == "complete"
    assert output_path.exists()


def test_phase3_model_comparison_report_contains_interval_capability(tmp_path: Path) -> None:
    """Interval-capable models should retain their interval flag in the normalized report."""

    causal_forest_path = tmp_path / "causal_forest.json"
    revenue_path = tmp_path / "revenue.json"

    _write_report(
        causal_forest_path,
        model_name="causal_forest_conversion",
        outcome_column="conversion",
        top_decile_observed_ate=0.02,
        bottom_decile_observed_ate=0.0,
        overall_observed_ate=0.01,
        interval_width=0.07,
    )
    _write_report(
        revenue_path,
        model_name="drlearner_revenue",
        outcome_column="revenue",
        top_decile_observed_ate=4.0,
        bottom_decile_observed_ate=0.5,
        overall_observed_ate=1.0,
    )

    report = generate_phase3_model_comparison_report(
        conversion_report_paths=[causal_forest_path],
        revenue_report_paths=[revenue_path],
        comparison_split="test",
        output_path=tmp_path / "comparison.json",
    )

    assert report.conversion_comparison.ranked_models[0].interval_capable is True
    assert report.conversion_comparison.ranked_models[0].mean_interval_width == 0.07
