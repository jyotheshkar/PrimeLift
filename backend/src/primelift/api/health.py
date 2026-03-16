"""Health endpoint helpers for the Phase 6 API foundation slice."""

from __future__ import annotations

from datetime import UTC, datetime

from primelift.api.schemas import HealthReadiness, HealthResponse
from primelift.utils.paths import (
    DEFAULT_DATASET_PATH,
    DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH,
    DEFAULT_PREPROCESSING_MANIFEST_PATH,
)

API_VERSION = "0.1.0"
SERVICE_NAME = "PrimeLift AI API"


def build_health_response() -> HealthResponse:
    """Build the typed health response for the FastAPI slice."""

    readiness = HealthReadiness(
        dataset_ready=DEFAULT_DATASET_PATH.exists(),
        prepared_data_ready=DEFAULT_PREPROCESSING_MANIFEST_PATH.exists(),
        phase5_closeout_ready=DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH.exists(),
    )
    return HealthResponse(
        status="ok",
        service_name=SERVICE_NAME,
        api_version=API_VERSION,
        current_phase=6,
        timestamp_utc=datetime.now(UTC).isoformat(),
        readiness=readiness,
    )
