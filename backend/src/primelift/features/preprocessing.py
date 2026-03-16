"""Leakage-safe preprocessing helpers for PrimeLift model training workflows."""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, ConfigDict
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from primelift.features.columns import (
    DATE_COLUMNS,
    ID_COLUMNS,
    MODEL_CATEGORICAL_FEATURES,
    MODEL_FEATURE_COLUMNS,
    MODEL_NUMERIC_FEATURES,
    OUTCOME_COLUMNS,
    TREATMENT_COLUMNS,
)

EXCLUDED_FROM_MODEL_FEATURES = ID_COLUMNS + DATE_COLUMNS + TREATMENT_COLUMNS + OUTCOME_COLUMNS


class PreprocessingSummary(BaseModel):
    """Serializable summary of the preprocessing contract."""

    model_config = ConfigDict(frozen=True)

    raw_feature_columns: list[str]
    excluded_columns: list[str]
    transformed_feature_columns: list[str]
    transformed_feature_count: int


def build_model_preprocessor() -> ColumnTransformer:
    """Create the Phase 2 preprocessing pipeline for mixed tabular features."""

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, list(MODEL_NUMERIC_FEATURES)),
            ("categorical", categorical_pipeline, list(MODEL_CATEGORICAL_FEATURES)),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def fit_model_preprocessor(train_dataset: pd.DataFrame) -> ColumnTransformer:
    """Fit the preprocessing pipeline on the training split only."""

    preprocessor = build_model_preprocessor()
    preprocessor.fit(train_dataset.loc[:, MODEL_FEATURE_COLUMNS])
    return preprocessor


def transform_model_features(
    dataset: pd.DataFrame, preprocessor: ColumnTransformer
) -> pd.DataFrame:
    """Transform a split into a dense feature matrix with stable column names."""

    transformed_array = preprocessor.transform(dataset.loc[:, MODEL_FEATURE_COLUMNS])
    feature_names = preprocessor.get_feature_names_out().tolist()
    return pd.DataFrame(
        transformed_array,
        index=dataset.index,
        columns=feature_names,
    )


def build_preprocessing_summary(preprocessor: ColumnTransformer) -> PreprocessingSummary:
    """Build the serializable preprocessing summary after fitting."""

    feature_names = preprocessor.get_feature_names_out().tolist()
    return PreprocessingSummary(
        raw_feature_columns=list(MODEL_FEATURE_COLUMNS),
        excluded_columns=list(EXCLUDED_FROM_MODEL_FEATURES),
        transformed_feature_columns=feature_names,
        transformed_feature_count=len(feature_names),
    )
