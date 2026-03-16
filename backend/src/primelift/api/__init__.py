"""FastAPI entrypoints and response contracts for PrimeLift."""

from primelift.api.analysis import (
    build_ate_analysis_response,
    build_models_analysis_response,
    build_recommendations_analysis_response,
    build_segments_analysis_response,
)
from primelift.api.app import app, create_app
from primelift.api.dataset import generate_dataset_response, sample_dataset_response
from primelift.api.schemas import (
    ATEAnalysisResultResponse,
    AnalysisATEResponse,
    AnalysisModelsResponse,
    AnalysisRecommendationsResponse,
    AnalysisSegmentsResponse,
    DatasetGenerateRequest,
    DatasetGenerateResponse,
    DatasetSampleResponse,
    DatasetSummaryResponse,
    HealthReadiness,
    HealthResponse,
)

__all__ = [
    "ATEAnalysisResultResponse",
    "AnalysisATEResponse",
    "AnalysisModelsResponse",
    "AnalysisRecommendationsResponse",
    "AnalysisSegmentsResponse",
    "DatasetGenerateRequest",
    "DatasetGenerateResponse",
    "DatasetSampleResponse",
    "DatasetSummaryResponse",
    "HealthReadiness",
    "HealthResponse",
    "app",
    "create_app",
    "build_ate_analysis_response",
    "build_models_analysis_response",
    "build_recommendations_analysis_response",
    "build_segments_analysis_response",
    "generate_dataset_response",
    "sample_dataset_response",
]
