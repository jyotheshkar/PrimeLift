"""Tests for the Phase 6 FastAPI foundation slice."""

from __future__ import annotations

from fastapi.testclient import TestClient

from primelift.api import create_app


def test_create_app_exposes_health_endpoint() -> None:
    """The app factory should expose a working health endpoint."""

    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service_name"] == "PrimeLift AI API"
    assert payload["api_version"] == "0.1.0"
    assert payload["current_phase"] == 6
    assert "timestamp_utc" in payload


def test_health_endpoint_returns_readiness_flags() -> None:
    """The health endpoint should include the expected readiness contract."""

    client = TestClient(create_app())
    payload = client.get("/health").json()

    assert set(payload["readiness"]) == {
        "dataset_ready",
        "prepared_data_ready",
        "phase5_closeout_ready",
    }
    assert isinstance(payload["readiness"]["dataset_ready"], bool)
    assert isinstance(payload["readiness"]["prepared_data_ready"], bool)
    assert isinstance(payload["readiness"]["phase5_closeout_ready"], bool)


def test_health_endpoint_allows_local_frontend_origin() -> None:
    """The API should expose CORS headers for the local frontend origin."""

    client = TestClient(create_app())
    response = client.get("/health", headers={"Origin": "http://127.0.0.1:3000"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
