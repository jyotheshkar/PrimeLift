"""Dataset endpoint helpers for the Phase 6 API slice."""

from __future__ import annotations

from fastapi import HTTPException

from primelift.api.schemas import (
    DatasetGenerateRequest,
    DatasetGenerateResponse,
    DatasetSampleResponse,
    DatasetSummaryResponse,
)
from primelift.data.generator import generate_london_campaign_users, save_dataset
from primelift.data.summary import build_dataset_summary, load_dataset
from primelift.utils.paths import DEFAULT_DATASET_PATH, ensure_project_directories


def generate_dataset_response(request: DatasetGenerateRequest) -> DatasetGenerateResponse:
    """Generate the synthetic dataset and return a typed API response."""

    ensure_project_directories()
    dataset = generate_london_campaign_users(row_count=request.rows, seed=request.seed)
    output_path = save_dataset(dataset, DEFAULT_DATASET_PATH)
    summary = build_dataset_summary(dataset)
    return DatasetGenerateResponse(
        status="generated",
        output_path=str(output_path),
        seed=request.seed,
        summary=DatasetSummaryResponse(**summary),
    )


def sample_dataset_response(rows: int = 10) -> DatasetSampleResponse:
    """Load a small preview of the saved dataset and return it as typed JSON."""

    if not DEFAULT_DATASET_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Dataset CSV was not found at the default path. "
                "Generate the dataset first with POST /dataset/generate."
            ),
        )

    dataset = load_dataset(DEFAULT_DATASET_PATH)
    sample = dataset.head(rows)
    return DatasetSampleResponse(
        status="ok",
        source_path=str(DEFAULT_DATASET_PATH),
        requested_rows=rows,
        returned_rows=int(len(sample)),
        available_rows=int(len(dataset)),
        columns=list(dataset.columns),
        records=sample.to_dict(orient="records"),
    )
