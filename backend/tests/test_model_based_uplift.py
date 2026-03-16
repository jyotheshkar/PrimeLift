"""Tests for the first revised Phase 4 model-based uplift slice."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from primelift.uplift import generate_model_based_uplift_decile_report


def _write_test_artifacts(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create minimal comparison, training-report, and scored-output artifacts."""

    score_column = "predicted_cate_drlearner_conversion"
    scored_output_path = tmp_path / "scored.csv"
    rows: list[dict[str, object]] = []

    for index in range(100):
        score = 1.0 - (index / 100.0)
        treatment = index % 2
        decile = (index // 10) + 1
        if decile == 1:
            conversion = 1 if treatment == 1 else 0
        elif decile == 10:
            conversion = 0 if treatment == 1 else 1
        else:
            conversion = 1 if (treatment == 1 and decile <= 4) else 0

        rows.append(
            {
                "user_id": f"user-{index:03d}",
                "campaign_id": "cmp-1",
                "event_date": "2026-03-01",
                "treatment": treatment,
                "conversion": conversion,
                "revenue": float(conversion * 10),
                "segment": "High Intent Returners" if decile <= 5 else "Lapsed Users",
                "london_borough": "Camden",
                "split": "test",
                score_column: score,
            }
        )

    pd.DataFrame(rows).to_csv(scored_output_path, index=False)

    metrics_report_path = tmp_path / "drlearner_conversion_report.json"
    metrics_report = {
        "model_name": "drlearner_conversion",
        "config": {
            "outcome_column": "conversion",
            "score_column": score_column,
        },
        "split_evaluations": [
            {
                "split_name": "test",
                "score_output_path": str(scored_output_path),
            }
        ],
    }
    metrics_report_path.write_text(json.dumps(metrics_report), encoding="utf-8")

    comparison_report_path = tmp_path / "comparison.json"
    comparison_report = {
        "conversion_comparison": {
            "champion_model_name": "drlearner_conversion",
            "ranked_models": [
                {
                    "model_name": "drlearner_conversion",
                    "metrics_report_path": str(metrics_report_path),
                }
            ],
        }
    }
    comparison_report_path.write_text(json.dumps(comparison_report), encoding="utf-8")
    return comparison_report_path, metrics_report_path, scored_output_path


def test_generate_model_based_uplift_decile_report_creates_outputs(tmp_path: Path) -> None:
    """The Phase 4 decile report should save both the scored view and the JSON report."""

    comparison_report_path, _, _ = _write_test_artifacts(tmp_path)
    output_report_path = tmp_path / "phase4_report.json"
    scored_view_path = tmp_path / "phase4_scored_view.csv"

    report = generate_model_based_uplift_decile_report(
        comparison_report_path=comparison_report_path,
        outcome_column="conversion",
        split_name="test",
        decile_count=10,
        output_report_path=output_report_path,
        scored_view_path=scored_view_path,
    )

    assert report.model_name == "drlearner_conversion"
    assert report.decile_count == 10
    assert report.top_persuadable_deciles[0] == 1
    assert 10 in report.suppression_candidate_deciles
    assert output_report_path.exists()
    assert scored_view_path.exists()

    scored_frame = pd.read_csv(scored_view_path)
    assert "uplift_decile_rank" in scored_frame.columns
    assert "uplift_decile_label" in scored_frame.columns
    assert scored_frame["uplift_decile_rank"].nunique() == 10


def test_phase4_decile_report_orders_deciles_from_highest_to_lowest_score(tmp_path: Path) -> None:
    """Decile rank 1 should correspond to the highest predicted-score bucket."""

    comparison_report_path, _, _ = _write_test_artifacts(tmp_path)
    report = generate_model_based_uplift_decile_report(
        comparison_report_path=comparison_report_path,
        outcome_column="conversion",
        split_name="test",
        decile_count=10,
        output_report_path=tmp_path / "phase4_report.json",
        scored_view_path=tmp_path / "phase4_scored_view.csv",
    )

    highest_bucket = report.deciles[0]
    lowest_bucket = report.deciles[-1]

    assert highest_bucket.decile_rank == 1
    assert highest_bucket.mean_score > lowest_bucket.mean_score
    assert highest_bucket.observed_ate is not None
    assert lowest_bucket.observed_ate is not None
    assert report.observed_top_bottom_gap is not None
