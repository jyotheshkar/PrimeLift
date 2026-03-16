"""Tests for the revised Phase 5 budget-allocation slice."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from primelift.decision import generate_segment_budget_allocation


def _write_budget_test_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    """Create minimal rollup and revenue-score artifacts for budget-allocation tests."""

    revenue_scores_path = tmp_path / "revenue_scores.csv"
    pd.DataFrame(
        [
            {"segment": "High Intent Returners", "predicted_cate_drlearner_revenue": 3.0},
            {"segment": "High Intent Returners", "predicted_cate_drlearner_revenue": 2.0},
            {"segment": "High Intent Returners", "predicted_cate_drlearner_revenue": -1.0},
            {"segment": "Young Professionals", "predicted_cate_drlearner_revenue": 1.0},
            {"segment": "Young Professionals", "predicted_cate_drlearner_revenue": 1.0},
            {"segment": "Lapsed Users", "predicted_cate_drlearner_revenue": -0.5},
            {"segment": "Lapsed Users", "predicted_cate_drlearner_revenue": -0.2},
        ]
    ).to_csv(revenue_scores_path, index=False)

    revenue_metrics_report_path = tmp_path / "drlearner_revenue_report.json"
    revenue_metrics_report = {
        "model_name": "drlearner_revenue",
        "config": {
            "outcome_column": "revenue",
            "score_column": "predicted_cate_drlearner_revenue",
        },
        "split_evaluations": [
            {
                "split_name": "test",
                "score_output_path": str(revenue_scores_path),
            }
        ],
    }
    revenue_metrics_report_path.write_text(json.dumps(revenue_metrics_report), encoding="utf-8")

    conversion_rollup_report_path = tmp_path / "conversion_rollup_report.json"
    conversion_rollup_report = {
        "split_name": "test",
        "model_name": "drlearner_conversion",
        "reports": [
            {
                "group_column": "segment",
                "results": [
                    {
                        "group_column": "segment",
                        "group_value": "High Intent Returners",
                        "mean_predicted_effect": 0.025,
                        "observed_ate": 0.03,
                        "recommendation_label": "prioritize",
                    },
                    {
                        "group_column": "segment",
                        "group_value": "Young Professionals",
                        "mean_predicted_effect": 0.012,
                        "observed_ate": 0.015,
                        "recommendation_label": "prioritize",
                    },
                    {
                        "group_column": "segment",
                        "group_value": "Lapsed Users",
                        "mean_predicted_effect": -0.002,
                        "observed_ate": -0.01,
                        "recommendation_label": "suppress",
                    },
                ],
            }
        ],
    }
    conversion_rollup_report_path.write_text(
        json.dumps(conversion_rollup_report),
        encoding="utf-8",
    )

    return conversion_rollup_report_path, revenue_metrics_report_path


def test_generate_segment_budget_allocation_creates_outputs(tmp_path: Path) -> None:
    """The budget-allocation report should create both the JSON report and table CSV."""

    conversion_rollup_report_path, revenue_metrics_report_path = _write_budget_test_artifacts(
        tmp_path
    )
    output_report_path = tmp_path / "budget_report.json"
    budget_table_path = tmp_path / "budget_table.csv"

    report = generate_segment_budget_allocation(
        conversion_rollup_report_path=conversion_rollup_report_path,
        revenue_metrics_report_path=revenue_metrics_report_path,
        output_report_path=output_report_path,
        budget_table_path=budget_table_path,
        total_budget=10_000.0,
    )

    assert report.report_name == "phase5_segment_budget_allocation"
    assert report.allocated_segment_count == 2
    assert report.suppressed_segment_count == 1
    assert output_report_path.exists()
    assert budget_table_path.exists()


def test_generate_segment_budget_allocation_distributes_budget_proportionally(tmp_path: Path) -> None:
    """Positive budget should flow to prioritized segments in proportion to positive revenue mass."""

    conversion_rollup_report_path, revenue_metrics_report_path = _write_budget_test_artifacts(
        tmp_path
    )

    report = generate_segment_budget_allocation(
        conversion_rollup_report_path=conversion_rollup_report_path,
        revenue_metrics_report_path=revenue_metrics_report_path,
        output_report_path=tmp_path / "budget_report.json",
        budget_table_path=tmp_path / "budget_table.csv",
        total_budget=10_000.0,
    )

    assert [segment.segment for segment in report.top_budget_segments] == [
        "High Intent Returners",
        "Young Professionals",
    ]
    assert report.top_budget_segments[0].recommended_budget == 10_000.0 * (5.0 / 7.0)
    assert report.top_budget_segments[1].recommended_budget == 10_000.0 * (2.0 / 7.0)
    assert report.suppressed_segments[0].segment == "Lapsed Users"
    assert report.suppressed_segments[0].recommended_budget == 0.0
    assert sum(segment.recommended_budget for segment in report.top_budget_segments) == 10_000.0
