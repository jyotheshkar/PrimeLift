"""Tests for the revised Phase 5 DRPolicyTree slice."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from primelift.decision import train_drpolicytree_conversion_policy


def _build_policy_test_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    """Create a raw dataset and prepared-manifest shell for policy-tree tests."""

    rng = np.random.default_rng(42)
    row_count = 800

    segments = np.where(
        rng.random(row_count) < 0.35,
        "High Intent Returners",
        "Window Shoppers",
    )
    device_types = np.where(rng.random(row_count) < 0.7, "mobile", "desktop")
    is_member = (rng.random(row_count) < 0.4).astype(int)
    engagement = np.where(
        segments == "High Intent Returners",
        rng.normal(loc=72, scale=10, size=row_count),
        rng.normal(loc=34, scale=12, size=row_count),
    ).clip(1, 99)
    prior_purchases = np.where(
        segments == "High Intent Returners",
        rng.poisson(lam=2.2, size=row_count),
        rng.poisson(lam=0.4, size=row_count),
    )
    prior_sessions = np.where(
        segments == "High Intent Returners",
        rng.poisson(lam=11, size=row_count),
        rng.poisson(lam=4, size=row_count),
    )
    avg_order_value = np.where(
        segments == "High Intent Returners",
        rng.normal(loc=88, scale=14, size=row_count),
        rng.normal(loc=42, scale=10, size=row_count),
    ).clip(10, 250)
    tenure = np.where(
        segments == "High Intent Returners",
        rng.integers(180, 1200, size=row_count),
        rng.integers(10, 400, size=row_count),
    )
    age = rng.integers(18, 70, size=row_count)
    treatment = (rng.random(row_count) < 0.5).astype(int)

    baseline = (
        0.02
        + 0.0025 * prior_purchases
        + 0.0015 * prior_sessions
        + 0.0006 * engagement
        + 0.02 * is_member
    )
    uplift = np.where(
        (segments == "High Intent Returners") | (engagement >= 60),
        0.28,
        -0.08,
    )
    conversion_probability = np.clip(baseline + treatment * uplift, 0.01, 0.92)
    conversion = (rng.random(row_count) < conversion_probability).astype(int)

    raw_dataset = pd.DataFrame(
        {
            "user_id": [f"u{i:04d}" for i in range(row_count)],
            "campaign_id": ["policy-test"] * row_count,
            "event_date": ["2026-03-01"] * row_count,
            "treatment": treatment,
            "conversion": conversion,
            "revenue": conversion.astype(float) * rng.normal(loc=65, scale=15, size=row_count).clip(10, 200),
            "segment": segments,
            "london_borough": np.where(segments == "High Intent Returners", "Hackney", "Camden"),
            "device_type": device_types,
            "is_prime_like_member": is_member,
            "age": age,
            "prior_engagement_score": engagement,
            "prior_purchases_90d": prior_purchases,
            "prior_sessions_30d": prior_sessions,
            "avg_order_value": avg_order_value,
            "customer_tenure_days": tenure,
        }
    )

    raw_dataset = raw_dataset.sample(frac=1.0, random_state=42).reset_index(drop=True)
    raw_dataset_path = tmp_path / "raw_dataset.csv"
    raw_dataset.to_csv(raw_dataset_path, index=False)

    split_paths = {}
    split_indices = {
        "train": slice(0, 400),
        "validation": slice(400, 600),
        "test": slice(600, 800),
    }
    split_summaries = []
    for split_name, split_slice in split_indices.items():
        split_frame = raw_dataset.iloc[split_slice].copy()
        split_path = tmp_path / f"{split_name}_split.csv"
        split_frame.loc[:, ["user_id"]].to_csv(split_path, index=False)
        split_paths[split_name] = split_path
        split_summaries.append(
            {
                "split_name": split_name,
                "row_count": int(len(split_frame)),
                "treatment_rate": float(split_frame["treatment"].mean()),
                "conversion_rate": float(split_frame["conversion"].mean()),
                "file_path": str(split_path),
            }
        )

    prepared_manifest_path = tmp_path / "prepared_manifest.json"
    prepared_manifest = {
        "input_dataset_path": str(raw_dataset_path),
        "train_size": 0.6667,
        "validation_size": 0.1667,
        "test_size": 0.1666,
        "random_seed": 42,
        "raw_feature_count": 16,
        "transformed_feature_count": 16,
        "transformed_feature_sample": [],
        "splits": split_summaries,
        "preprocessor_artifact_path": str(tmp_path / "preprocessor.joblib"),
        "manifest_path": str(prepared_manifest_path),
    }
    prepared_manifest_path.write_text(json.dumps(prepared_manifest), encoding="utf-8")
    return raw_dataset_path, prepared_manifest_path


def test_train_drpolicytree_conversion_policy_creates_outputs(tmp_path: Path) -> None:
    """The policy-tree slice should create a model artifact, report, and scored decisions."""

    raw_dataset_path, prepared_manifest_path = _build_policy_test_artifacts(tmp_path)
    model_artifact_path = tmp_path / "policy_model.joblib"
    output_report_path = tmp_path / "policy_report.json"
    decisions_output_path = tmp_path / "policy_decisions.csv"

    report = train_drpolicytree_conversion_policy(
        raw_dataset_path=raw_dataset_path,
        prepared_manifest_path=prepared_manifest_path,
        model_artifact_path=model_artifact_path,
        output_report_path=output_report_path,
        decisions_output_path=decisions_output_path,
        max_depth=2,
        min_samples_split=20,
        min_samples_leaf=10,
        cv=2,
    )

    assert report.report_name == "phase5_drpolicytree_conversion_policy"
    assert model_artifact_path.exists()
    assert output_report_path.exists()
    assert decisions_output_path.exists()
    assert report.tree_leaf_count >= 2
    assert len(report.leaf_summaries) >= 2


def test_train_drpolicytree_conversion_policy_beats_naive_baselines(tmp_path: Path) -> None:
    """The learned policy should improve on always-control in the synthetic heterogeneous setup."""

    raw_dataset_path, prepared_manifest_path = _build_policy_test_artifacts(tmp_path)

    report = train_drpolicytree_conversion_policy(
        raw_dataset_path=raw_dataset_path,
        prepared_manifest_path=prepared_manifest_path,
        model_artifact_path=tmp_path / "policy_model.joblib",
        output_report_path=tmp_path / "policy_report.json",
        decisions_output_path=tmp_path / "policy_decisions.csv",
        max_depth=2,
        min_samples_split=20,
        min_samples_leaf=10,
        cv=2,
    )

    assert 0.0 < report.recommended_treat_rate < 1.0
    assert report.estimated_policy_value > report.always_control_value
    assert report.policy_gain_over_always_control > 0.0
    assert len(report.top_feature_importances) > 0
    assert any(leaf.recommended_action == "treat" for leaf in report.leaf_summaries)
