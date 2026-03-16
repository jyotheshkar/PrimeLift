"""Feature schema helpers for PrimeLift's ML-ready foundation."""

from primelift.features.columns import (
    DATE_COLUMNS,
    GROUP_COLUMNS,
    ID_COLUMNS,
    MODEL_CATEGORICAL_FEATURES,
    MODEL_FEATURE_COLUMNS,
    MODEL_NUMERIC_FEATURES,
    OUTCOME_COLUMNS,
    TREATMENT_COLUMNS,
    FeatureSchemaSummary,
    build_feature_schema_summary,
)
from primelift.features.preprocessing import (
    EXCLUDED_FROM_MODEL_FEATURES,
    PreprocessingSummary,
    build_model_preprocessor,
    build_preprocessing_summary,
    fit_model_preprocessor,
    transform_model_features,
)

__all__ = [
    "DATE_COLUMNS",
    "GROUP_COLUMNS",
    "ID_COLUMNS",
    "MODEL_CATEGORICAL_FEATURES",
    "MODEL_FEATURE_COLUMNS",
    "MODEL_NUMERIC_FEATURES",
    "OUTCOME_COLUMNS",
    "TREATMENT_COLUMNS",
    "FeatureSchemaSummary",
    "EXCLUDED_FROM_MODEL_FEATURES",
    "PreprocessingSummary",
    "build_model_preprocessor",
    "build_preprocessing_summary",
    "build_feature_schema_summary",
    "fit_model_preprocessor",
    "transform_model_features",
]
