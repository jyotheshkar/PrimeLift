"""Tests for the second revised Phase 4 model-based rollup slice."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from primelift.uplift import generate_model_based_group_rollup_report


def _write_rollup_test_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    """Create minimal artifacts required for model-based rollup tests."""

    score_column = "predicted_cate_drlearner_conversion"
    scored_output_path = tmp_path / "scored.csv"
    raw_dataset_path = tmp_path / "raw.csv"

    scored_rows = [
        {
            "user_id": "u1",
            "campaign_id": "cmp-1",
            "event_date": "2026-03-01",
            "treatment": 1,
            "conversion": 1,
            "revenue": 10.0,
            "segment": "High Intent Returners",
            "london_borough": "Camden",
            "split": "test",
            score_column: 0.08,
        },
        {
            "user_id": "u2",
            "campaign_id": "cmp-1",
            "event_date": "2026-03-01",
            "treatment": 0,
            "conversion": 0,
            "revenue": 0.0,
            "segment": "High Intent Returners",
            "london_borough": "Camden",
            "split": "test",
            score_column: 0.07,
        },
        {
            "user_id": "u3",
            "campaign_id": "cmp-1",
            "event_date": "2026-03-01",
            "treatment": 1,
            "conversion": 0,
            "revenue": 0.0,
            "segment": "Lapsed Users",
            "london_borough": "Southwark",
            "split": "test",
            score_column: -0.03,
        },
        {
            "user_id": "u4",
            "campaign_id": "cmp-1",
            "event_date": "2026-03-01",
            "treatment": 0,
            "conversion": 1,
            "revenue": 12.0,
            "segment": "Lapsed Users",
            "london_borough": "Southwark",
            "split": "test",
            score_column: -0.04,
        },
    ]
    pd.DataFrame(scored_rows).to_csv(scored_output_path, index=False)

    raw_rows = [
        {
            "user_id": "u1",
            "london_borough": "Camden",
            "postcode_area": "NW",
            "age": 29,
            "age_band": "25-34",
            "gender": "female",
            "device_type": "mobile",
            "platform": "ios",
            "traffic_source": "paid_search",
            "channel": "generic_search",
            "prior_engagement_score": 70.0,
            "prior_purchases_90d": 2,
            "prior_sessions_30d": 10,
            "avg_order_value": 60.0,
            "customer_tenure_days": 400,
            "is_prime_like_member": 1,
            "segment": "High Intent Returners",
            "treatment": 1,
            "conversion": 1,
            "revenue": 10.0,
            "campaign_id": "cmp-1",
            "event_date": "2026-03-01",
        },
        {
            "user_id": "u2",
            "london_borough": "Camden",
            "postcode_area": "NW",
            "age": 30,
            "age_band": "25-34",
            "gender": "male",
            "device_type": "mobile",
            "platform": "android",
            "traffic_source": "organic_search",
            "channel": "generic_search",
            "prior_engagement_score": 65.0,
            "prior_purchases_90d": 1,
            "prior_sessions_30d": 8,
            "avg_order_value": 55.0,
            "customer_tenure_days": 300,
            "is_prime_like_member": 0,
            "segment": "High Intent Returners",
            "treatment": 0,
            "conversion": 0,
            "revenue": 0.0,
            "campaign_id": "cmp-1",
            "event_date": "2026-03-01",
        },
        {
            "user_id": "u3",
            "london_borough": "Southwark",
            "postcode_area": "SE",
            "age": 41,
            "age_band": "35-44",
            "gender": "female",
            "device_type": "desktop",
            "platform": "web",
            "traffic_source": "direct",
            "channel": "homepage",
            "prior_engagement_score": 15.0,
            "prior_purchases_90d": 0,
            "prior_sessions_30d": 2,
            "avg_order_value": 30.0,
            "customer_tenure_days": 60,
            "is_prime_like_member": 0,
            "segment": "Lapsed Users",
            "treatment": 1,
            "conversion": 0,
            "revenue": 0.0,
            "campaign_id": "cmp-1",
            "event_date": "2026-03-01",
        },
        {
            "user_id": "u4",
            "london_borough": "Southwark",
            "postcode_area": "SE",
            "age": 43,
            "age_band": "35-44",
            "gender": "male",
            "device_type": "desktop",
            "platform": "web",
            "traffic_source": "email",
            "channel": "lifecycle_email",
            "prior_engagement_score": 20.0,
            "prior_purchases_90d": 0,
            "prior_sessions_30d": 3,
            "avg_order_value": 35.0,
            "customer_tenure_days": 70,
            "is_prime_like_member": 0,
            "segment": "Lapsed Users",
            "treatment": 0,
            "conversion": 1,
            "revenue": 12.0,
            "campaign_id": "cmp-1",
            "event_date": "2026-03-01",
        },
    ]
    pd.DataFrame(raw_rows).to_csv(raw_dataset_path, index=False)

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
    return comparison_report_path, raw_dataset_path


def test_generate_model_based_group_rollup_report_creates_outputs(tmp_path: Path) -> None:
    """The Phase 4 rollup report should create the enriched view and flat table outputs."""

    comparison_report_path, raw_dataset_path = _write_rollup_test_artifacts(tmp_path)
    output_report_path = tmp_path / "rollup_report.json"
    rollup_table_path = tmp_path / "rollup_table.csv"
    enriched_scored_view_path = tmp_path / "enriched_scored_view.csv"

    report = generate_model_based_group_rollup_report(
        comparison_report_path=comparison_report_path,
        raw_dataset_path=raw_dataset_path,
        outcome_column="conversion",
        split_name="test",
        output_report_path=output_report_path,
        rollup_table_path=rollup_table_path,
        enriched_scored_view_path=enriched_scored_view_path,
    )

    assert report.model_name == "drlearner_conversion"
    assert output_report_path.exists()
    assert rollup_table_path.exists()
    assert enriched_scored_view_path.exists()
    assert len(report.reports) == 4

    enriched_frame = pd.read_csv(enriched_scored_view_path)
    assert "device_type" in enriched_frame.columns
    assert "channel" in enriched_frame.columns


def test_model_based_group_rollups_surface_positive_and_suppression_groups(tmp_path: Path) -> None:
    """Rollups should rank the strong positive group above the weak negative group."""

    comparison_report_path, raw_dataset_path = _write_rollup_test_artifacts(tmp_path)
    report = generate_model_based_group_rollup_report(
        comparison_report_path=comparison_report_path,
        raw_dataset_path=raw_dataset_path,
        outcome_column="conversion",
        split_name="test",
        output_report_path=tmp_path / "rollup_report.json",
        rollup_table_path=tmp_path / "rollup_table.csv",
        enriched_scored_view_path=tmp_path / "enriched_scored_view.csv",
    )

    segment_report = next(item for item in report.reports if item.group_column == "segment")
    assert segment_report.results[0].group_value == "High Intent Returners"
    assert "High Intent Returners" in segment_report.top_positive_groups
    assert "Lapsed Users" in segment_report.suppression_candidates
