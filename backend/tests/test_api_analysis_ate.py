"""Tests for the Phase 6 ATE analysis API slice."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from primelift.api import create_app
from primelift.data.generator import generate_london_campaign_users, save_dataset


def test_get_analysis_ate_returns_conversion_baseline_metrics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The analysis endpoint should return typed conversion ATE metrics."""

    import primelift.api.analysis as analysis_api_module

    output_path = tmp_path / "analysis_dataset.csv"
    dataset = generate_london_campaign_users(row_count=400, seed=21)
    save_dataset(dataset, output_path)
    monkeypatch.setattr(analysis_api_module, "DEFAULT_DATASET_PATH", output_path)

    client = TestClient(create_app())
    response = client.get("/analysis/ate?outcome=conversion&bootstrap_samples=50")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["row_count"] == 400
    assert payload["result"]["outcome_column"] == "conversion"
    assert payload["result"]["bootstrap_samples"] == 50
    assert payload["result"]["ci_lower"] <= payload["result"]["ate"] <= payload["result"]["ci_upper"]


def test_get_analysis_ate_supports_revenue_outcome(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The analysis endpoint should support the saved-dataset revenue outcome."""

    import primelift.api.analysis as analysis_api_module

    output_path = tmp_path / "analysis_revenue_dataset.csv"
    dataset = generate_london_campaign_users(row_count=300, seed=22)
    save_dataset(dataset, output_path)
    monkeypatch.setattr(analysis_api_module, "DEFAULT_DATASET_PATH", output_path)

    client = TestClient(create_app())
    response = client.get("/analysis/ate?outcome=revenue&bootstrap_samples=40")

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["outcome_column"] == "revenue"
    assert payload["result"]["bootstrap_samples"] == 40
    assert payload["result"]["treated_mean"] >= 0.0
    assert payload["result"]["control_mean"] >= 0.0


def test_get_analysis_ate_rejects_invalid_bootstrap_count() -> None:
    """The analysis endpoint should validate bootstrap sample count via the query layer."""

    client = TestClient(create_app())
    response = client.get("/analysis/ate?bootstrap_samples=1")

    assert response.status_code == 422


def test_get_analysis_ate_returns_not_found_when_dataset_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The analysis endpoint should return 404 if the dataset CSV is absent."""

    import primelift.api.analysis as analysis_api_module

    missing_path = tmp_path / "missing_analysis_dataset.csv"
    monkeypatch.setattr(analysis_api_module, "DEFAULT_DATASET_PATH", missing_path)

    client = TestClient(create_app())
    response = client.get("/analysis/ate")

    assert response.status_code == 404
    assert "Generate the dataset first" in response.json()["detail"]
