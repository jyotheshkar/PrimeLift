"""Tests for the first revised Phase 5 model-driven targeting slice."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from primelift.decision import generate_model_targeting_recommendations


def _write_phase5_test_artifacts(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create minimal Phase 4 artifacts for model-driven decision tests."""

    validation_report_path = tmp_path / "validation_report.json"
    validation_report = {
        "outcome_column": "conversion",
        "split_name": "test",
        "model_name": "drlearner_conversion",
        "top_persuadable_deciles": [1, 2],
        "suppression_candidate_deciles": [9, 10],
    }
    validation_report_path.write_text(json.dumps(validation_report), encoding="utf-8")

    rollup_report_path = tmp_path / "rollup_report.json"
    rollup_report = {
        "outcome_column": "conversion",
        "split_name": "test",
        "model_name": "drlearner_conversion",
        "score_column": "predicted_cate_drlearner_conversion",
        "reports": [
            {
                "results": [
                    {
                        "group_column": "segment",
                        "group_value": "High Intent Returners",
                        "mean_predicted_effect": 0.02,
                        "observed_ate": 0.025,
                        "recommendation_label": "prioritize",
                    },
                    {
                        "group_column": "segment",
                        "group_value": "Lapsed Users",
                        "mean_predicted_effect": -0.002,
                        "observed_ate": -0.01,
                        "recommendation_label": "suppress",
                    },
                ]
            }
        ],
    }
    rollup_report_path.write_text(json.dumps(rollup_report), encoding="utf-8")

    scored_view_path = tmp_path / "scored_view.csv"
    scored_rows = [
        {
            "user_id": "u1",
            "segment": "High Intent Returners",
            "london_borough": "Hackney",
            "device_type": "mobile",
            "channel": "generic_search",
            "uplift_decile_rank": 1,
            "predicted_cate_drlearner_conversion": 0.08,
        },
        {
            "user_id": "u2",
            "segment": "Young Professionals",
            "london_borough": "Camden",
            "device_type": "mobile",
            "channel": "generic_search",
            "uplift_decile_rank": 2,
            "predicted_cate_drlearner_conversion": 0.05,
        },
        {
            "user_id": "u3",
            "segment": "Lapsed Users",
            "london_borough": "Camden",
            "device_type": "desktop",
            "channel": "app_entry",
            "uplift_decile_rank": 9,
            "predicted_cate_drlearner_conversion": -0.01,
        },
        {
            "user_id": "u4",
            "segment": "Window Shoppers",
            "london_borough": "Southwark",
            "device_type": "desktop",
            "channel": "homepage",
            "uplift_decile_rank": 10,
            "predicted_cate_drlearner_conversion": -0.03,
        },
    ]
    pd.DataFrame(scored_rows).to_csv(scored_view_path, index=False)

    return validation_report_path, rollup_report_path, scored_view_path


def test_generate_model_targeting_recommendations_creates_outputs(tmp_path: Path) -> None:
    """The Phase 5 targeting report should create both user output files and the JSON report."""

    validation_report_path, rollup_report_path, scored_view_path = _write_phase5_test_artifacts(
        tmp_path
    )
    output_report_path = tmp_path / "targeting_report.json"
    target_users_path = tmp_path / "target_users.csv"
    suppress_users_path = tmp_path / "suppress_users.csv"

    report = generate_model_targeting_recommendations(
        validation_report_path=validation_report_path,
        rollup_report_path=rollup_report_path,
        scored_view_path=scored_view_path,
        output_report_path=output_report_path,
        target_users_path=target_users_path,
        suppress_users_path=suppress_users_path,
        top_n_users=2,
    )

    assert report.report_name == "phase5_model_targeting_recommendations"
    assert report.target_user_count == 2
    assert report.suppress_user_count == 2
    assert report.target_cohort_count == 1
    assert report.suppress_cohort_count == 1
    assert output_report_path.exists()
    assert target_users_path.exists()
    assert suppress_users_path.exists()


def test_phase5_targeting_recommendations_rank_expected_users_and_cohorts(tmp_path: Path) -> None:
    """Target users should come from the positive deciles and suppress users from the weak zone."""

    validation_report_path, rollup_report_path, scored_view_path = _write_phase5_test_artifacts(
        tmp_path
    )
    report = generate_model_targeting_recommendations(
        validation_report_path=validation_report_path,
        rollup_report_path=rollup_report_path,
        scored_view_path=scored_view_path,
        output_report_path=tmp_path / "targeting_report.json",
        target_users_path=tmp_path / "target_users.csv",
        suppress_users_path=tmp_path / "suppress_users.csv",
        top_n_users=2,
    )

    assert [user.user_id for user in report.top_target_users] == ["u1", "u2"]
    assert [user.user_id for user in report.top_suppress_users] == ["u4", "u3"]
    assert report.target_cohorts[0].group_value == "High Intent Returners"
    assert report.suppress_cohorts[0].group_value == "Lapsed Users"
