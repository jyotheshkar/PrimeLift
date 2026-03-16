"""Tests for the Phase 6 dataset sample API slice."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from primelift.api import create_app
from primelift.data.generator import generate_london_campaign_users, save_dataset


def test_get_dataset_sample_returns_requested_preview_rows(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The sample endpoint should return a preview from the saved dataset CSV."""

    import primelift.api.dataset as dataset_api_module

    output_path = tmp_path / "sample_dataset.csv"
    dataset = generate_london_campaign_users(row_count=20, seed=9)
    save_dataset(dataset, output_path)
    monkeypatch.setattr(dataset_api_module, "DEFAULT_DATASET_PATH", output_path)

    client = TestClient(create_app())
    response = client.get("/dataset/sample?rows=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["requested_rows"] == 5
    assert payload["returned_rows"] == 5
    assert payload["available_rows"] == 20
    assert "user_id" in payload["columns"]
    assert len(payload["records"]) == 5
    assert payload["records"][0]["user_id"] == "LON-000001"


def test_get_dataset_sample_rejects_invalid_row_count() -> None:
    """The sample endpoint should validate the requested preview row count."""

    client = TestClient(create_app())
    response = client.get("/dataset/sample?rows=0")

    assert response.status_code == 422


def test_get_dataset_sample_returns_not_found_when_dataset_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The sample endpoint should return 404 if the dataset CSV has not been generated."""

    import primelift.api.dataset as dataset_api_module

    missing_path = tmp_path / "missing_dataset.csv"
    monkeypatch.setattr(dataset_api_module, "DEFAULT_DATASET_PATH", missing_path)

    client = TestClient(create_app())
    response = client.get("/dataset/sample?rows=5")

    assert response.status_code == 404
    assert "Generate the dataset first" in response.json()["detail"]
