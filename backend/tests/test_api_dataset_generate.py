"""Tests for the Phase 6 dataset generation API slice."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from primelift.api import create_app


def test_post_dataset_generate_creates_csv_and_returns_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The dataset generation endpoint should write a CSV and return a typed summary."""

    import primelift.api.dataset as dataset_api_module

    output_path = tmp_path / "generated_dataset.csv"
    monkeypatch.setattr(dataset_api_module, "DEFAULT_DATASET_PATH", output_path)

    client = TestClient(create_app())
    response = client.post("/dataset/generate", json={"rows": 250, "seed": 7})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "generated"
    assert payload["seed"] == 7
    assert payload["summary"]["row_count"] == 250
    assert "user_id" in payload["summary"]["columns"]
    assert output_path.exists()


def test_post_dataset_generate_rejects_invalid_row_count() -> None:
    """The dataset generation endpoint should validate the requested row count."""

    client = TestClient(create_app())
    response = client.post("/dataset/generate", json={"rows": 0, "seed": 42})

    assert response.status_code == 422
