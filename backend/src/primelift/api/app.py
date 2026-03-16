"""FastAPI application entrypoint for the Phase 6 foundation slice."""

from __future__ import annotations

import os
from typing import Literal

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from primelift.api.analysis import (
    build_ate_analysis_response,
    build_models_analysis_response,
    build_recommendations_analysis_response,
    build_segments_analysis_response,
)
from primelift.api.dataset import generate_dataset_response, sample_dataset_response
from primelift.api.health import API_VERSION, SERVICE_NAME, build_health_response
from primelift.api.schemas import (
    AnalysisATEResponse,
    AnalysisModelsResponse,
    AnalysisRecommendationsResponse,
    AnalysisSegmentsResponse,
    DatasetGenerateRequest,
    DatasetGenerateResponse,
    DatasetSampleResponse,
    HealthResponse,
)

DEFAULT_FRONTEND_ORIGINS = (
    "http://127.0.0.1:3000",
    "http://localhost:3000",
)


def get_frontend_origins() -> list[str]:
    """Return the allowed frontend origins for local browser-based API access."""

    configured_origins = os.getenv("PRIMELIFT_FRONTEND_ORIGINS")
    if configured_origins is None:
        return list(DEFAULT_FRONTEND_ORIGINS)

    origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    return origins or list(DEFAULT_FRONTEND_ORIGINS)


def create_app() -> FastAPI:
    """Create the PrimeLift FastAPI application."""

    app = FastAPI(
        title=SERVICE_NAME,
        version=API_VERSION,
        summary="ML-first causal decision engine API for PrimeLift.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_frontend_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def get_health() -> HealthResponse:
        """Return a typed health response for the local backend state."""

        return build_health_response()

    @app.post("/dataset/generate", response_model=DatasetGenerateResponse, tags=["dataset"])
    def post_dataset_generate(request: DatasetGenerateRequest) -> DatasetGenerateResponse:
        """Generate the synthetic dataset and save it to the default project path."""

        return generate_dataset_response(request)

    @app.get("/dataset/sample", response_model=DatasetSampleResponse, tags=["dataset"])
    def get_dataset_sample(
        rows: int = Query(
            default=10,
            ge=1,
            le=100,
            description="Number of preview rows to return from the saved dataset.",
        ),
    ) -> DatasetSampleResponse:
        """Return a read-only preview of the saved dataset CSV."""

        return sample_dataset_response(rows=rows)

    @app.get("/analysis/ate", response_model=AnalysisATEResponse, tags=["analysis"])
    def get_analysis_ate(
        outcome: Literal["conversion", "revenue"] = Query(
            default="conversion",
            description="Supported ATE outcome column.",
        ),
        bootstrap_samples: int = Query(
            default=300,
            ge=2,
            le=2000,
            description="Number of bootstrap samples for the confidence interval.",
        ),
        confidence_level: float = Query(
            default=0.95,
            gt=0.0,
            lt=1.0,
            description="Confidence level for the bootstrap interval.",
        ),
        random_seed: int = Query(
            default=42,
            description="Random seed used during bootstrap resampling.",
        ),
    ) -> AnalysisATEResponse:
        """Return the saved-dataset ATE baseline analysis for a supported outcome."""

        return build_ate_analysis_response(
            outcome_column=outcome,
            bootstrap_samples=bootstrap_samples,
            confidence_level=confidence_level,
            random_seed=random_seed,
        )

    @app.get("/analysis/models", response_model=AnalysisModelsResponse, tags=["analysis"])
    def get_analysis_models() -> AnalysisModelsResponse:
        """Return the saved Phase 3 model comparison report and champion summary."""

        return build_models_analysis_response()

    @app.get("/analysis/segments", response_model=AnalysisSegmentsResponse, tags=["analysis"])
    def get_analysis_segments() -> AnalysisSegmentsResponse:
        """Return the saved Phase 4 cohort rollups and validation summary."""

        return build_segments_analysis_response()

    @app.get(
        "/analysis/recommendations",
        response_model=AnalysisRecommendationsResponse,
        tags=["analysis"],
    )
    def get_analysis_recommendations() -> AnalysisRecommendationsResponse:
        """Return the saved Phase 5 closeout recommendations and policy champion."""

        return build_recommendations_analysis_response()

    return app


app = create_app()
