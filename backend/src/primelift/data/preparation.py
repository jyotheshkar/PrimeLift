"""Model-ready dataset splitting and preprocessing for revised Phase 2."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from pydantic import BaseModel, ConfigDict
from sklearn.model_selection import train_test_split

from primelift.features import MODEL_FEATURE_COLUMNS
from primelift.features.preprocessing import (
    build_preprocessing_summary,
    fit_model_preprocessor,
    transform_model_features,
)
from primelift.utils.paths import (
    DEFAULT_DATASET_PATH,
    DEFAULT_PREPARED_TEST_PATH,
    DEFAULT_PREPARED_TRAIN_PATH,
    DEFAULT_PREPARED_VALIDATION_PATH,
    DEFAULT_PREPROCESSING_MANIFEST_PATH,
    DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    ensure_project_directories,
)

DEFAULT_SPLIT_RANDOM_SEED = 42
DEFAULT_TRAIN_SIZE = 0.70
DEFAULT_VALIDATION_SIZE = 0.15
DEFAULT_TEST_SIZE = 0.15
MODEL_META_COLUMNS = (
    "user_id",
    "campaign_id",
    "event_date",
    "treatment",
    "conversion",
    "revenue",
)


class PreparedSplitSummary(BaseModel):
    """Serializable summary for one prepared split."""

    model_config = ConfigDict(frozen=True)

    split_name: str
    row_count: int
    treatment_rate: float
    conversion_rate: float
    file_path: str


class PreparedDatasetSummary(BaseModel):
    """Serializable summary for the revised Phase 2 prepared data assets."""

    model_config = ConfigDict(frozen=True)

    input_dataset_path: str
    train_size: float
    validation_size: float
    test_size: float
    random_seed: int
    raw_feature_count: int
    transformed_feature_count: int
    transformed_feature_sample: list[str]
    splits: list[PreparedSplitSummary]
    preprocessor_artifact_path: str
    manifest_path: str


def _validate_split_fractions(
    train_size: float, validation_size: float, test_size: float
) -> None:
    """Validate the requested split sizes."""

    if min(train_size, validation_size, test_size) <= 0:
        raise ValueError("All split sizes must be positive.")

    if not abs((train_size + validation_size + test_size) - 1.0) < 1e-9:
        raise ValueError("train_size, validation_size, and test_size must sum to 1.0.")


def _build_stratification_labels(dataset: pd.DataFrame) -> pd.Series:
    """Create the richest feasible stratification labels for stable local splits."""

    candidate_column_sets = (
        ("segment", "treatment", "conversion"),
        ("segment", "treatment"),
        ("treatment", "conversion"),
        ("treatment",),
    )

    for column_set in candidate_column_sets:
        labels = dataset.loc[:, list(column_set)].astype(str).agg("__".join, axis=1)
        if int(labels.value_counts().min()) >= 2:
            return labels

    raise ValueError("Unable to build a valid stratification label with at least two members.")


def split_modeling_dataset(
    dataset: pd.DataFrame,
    train_size: float = DEFAULT_TRAIN_SIZE,
    validation_size: float = DEFAULT_VALIDATION_SIZE,
    test_size: float = DEFAULT_TEST_SIZE,
    random_seed: int = DEFAULT_SPLIT_RANDOM_SEED,
) -> dict[str, pd.DataFrame]:
    """Split the dataset into deterministic train, validation, and test partitions."""

    _validate_split_fractions(
        train_size=train_size,
        validation_size=validation_size,
        test_size=test_size,
    )

    stratification_labels = _build_stratification_labels(dataset)
    train_frame, temp_frame = train_test_split(
        dataset,
        train_size=train_size,
        random_state=random_seed,
        shuffle=True,
        stratify=stratification_labels,
    )

    temp_labels = _build_stratification_labels(temp_frame)
    validation_share_of_temp = validation_size / (validation_size + test_size)
    validation_frame, test_frame = train_test_split(
        temp_frame,
        train_size=validation_share_of_temp,
        random_state=random_seed,
        shuffle=True,
        stratify=temp_labels,
    )

    return {
        "train": train_frame.sort_values("user_id").reset_index(drop=True),
        "validation": validation_frame.sort_values("user_id").reset_index(drop=True),
        "test": test_frame.sort_values("user_id").reset_index(drop=True),
    }


def _build_prepared_split_frame(
    split_frame: pd.DataFrame,
    transformed_features: pd.DataFrame,
    split_name: str,
) -> pd.DataFrame:
    """Combine metadata, raw groups, and transformed features into one export frame."""

    meta_frame = split_frame.loc[:, list(MODEL_META_COLUMNS) + ["segment", "london_borough"]].copy()
    meta_frame.insert(len(meta_frame.columns), "split", split_name)
    return pd.concat(
        [meta_frame.reset_index(drop=True), transformed_features.reset_index(drop=True)],
        axis=1,
    )


def _write_prepared_split(prepared_frame: pd.DataFrame, output_path: Path) -> Path:
    """Persist one prepared split to CSV."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared_frame.to_csv(output_path, index=False)
    return output_path


def prepare_model_ready_datasets(
    dataset: pd.DataFrame,
    input_dataset_path: Path = DEFAULT_DATASET_PATH,
    train_output_path: Path = DEFAULT_PREPARED_TRAIN_PATH,
    validation_output_path: Path = DEFAULT_PREPARED_VALIDATION_PATH,
    test_output_path: Path = DEFAULT_PREPARED_TEST_PATH,
    preprocessor_artifact_path: Path = DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    manifest_path: Path = DEFAULT_PREPROCESSING_MANIFEST_PATH,
    train_size: float = DEFAULT_TRAIN_SIZE,
    validation_size: float = DEFAULT_VALIDATION_SIZE,
    test_size: float = DEFAULT_TEST_SIZE,
    random_seed: int = DEFAULT_SPLIT_RANDOM_SEED,
) -> PreparedDatasetSummary:
    """Split, preprocess, and save model-ready datasets for revised Phase 2."""

    ensure_project_directories()

    split_frames = split_modeling_dataset(
        dataset=dataset,
        train_size=train_size,
        validation_size=validation_size,
        test_size=test_size,
        random_seed=random_seed,
    )

    preprocessor = fit_model_preprocessor(split_frames["train"])
    preprocessing_summary = build_preprocessing_summary(preprocessor)

    output_paths = {
        "train": train_output_path,
        "validation": validation_output_path,
        "test": test_output_path,
    }

    split_summaries: list[PreparedSplitSummary] = []
    for split_name, split_frame in split_frames.items():
        transformed_features = transform_model_features(split_frame, preprocessor)
        prepared_frame = _build_prepared_split_frame(
            split_frame=split_frame,
            transformed_features=transformed_features,
            split_name=split_name,
        )
        saved_path = _write_prepared_split(prepared_frame, output_paths[split_name])
        split_summaries.append(
            PreparedSplitSummary(
                split_name=split_name,
                row_count=int(len(split_frame)),
                treatment_rate=round(float(split_frame["treatment"].mean()), 6),
                conversion_rate=round(float(split_frame["conversion"].mean()), 6),
                file_path=str(saved_path),
            )
        )

    preprocessor_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, preprocessor_artifact_path)

    summary = PreparedDatasetSummary(
        input_dataset_path=str(input_dataset_path),
        train_size=train_size,
        validation_size=validation_size,
        test_size=test_size,
        random_seed=random_seed,
        raw_feature_count=len(MODEL_FEATURE_COLUMNS),
        transformed_feature_count=preprocessing_summary.transformed_feature_count,
        transformed_feature_sample=preprocessing_summary.transformed_feature_columns[:20],
        splits=split_summaries,
        preprocessor_artifact_path=str(preprocessor_artifact_path),
        manifest_path=str(manifest_path),
    )

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(summary.model_dump(), indent=2),
        encoding="utf-8",
    )

    return summary


def load_prepared_dataset_summary(
    manifest_path: Path = DEFAULT_PREPROCESSING_MANIFEST_PATH,
) -> PreparedDatasetSummary:
    """Load the saved prepared-dataset manifest from disk."""

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return PreparedDatasetSummary(**payload)
