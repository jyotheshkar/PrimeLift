"""Central feature schema definitions for PrimeLift modeling workflows."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

ID_COLUMNS = ("user_id", "campaign_id")
DATE_COLUMNS = ("event_date",)
TREATMENT_COLUMNS = ("treatment",)
OUTCOME_COLUMNS = ("conversion", "revenue")
GROUP_COLUMNS = ("segment", "london_borough", "device_type", "channel")

MODEL_CATEGORICAL_FEATURES = (
    "london_borough",
    "postcode_area",
    "age_band",
    "gender",
    "device_type",
    "platform",
    "traffic_source",
    "channel",
    "is_prime_like_member",
    "segment",
)

MODEL_NUMERIC_FEATURES = (
    "age",
    "prior_engagement_score",
    "prior_purchases_90d",
    "prior_sessions_30d",
    "avg_order_value",
    "customer_tenure_days",
)

MODEL_FEATURE_COLUMNS = MODEL_CATEGORICAL_FEATURES + MODEL_NUMERIC_FEATURES


class FeatureSchemaSummary(BaseModel):
    """Serializable summary of the current modeling feature contract."""

    model_config = ConfigDict(frozen=True)

    identifier_columns: list[str]
    date_columns: list[str]
    treatment_columns: list[str]
    outcome_columns: list[str]
    group_columns: list[str]
    categorical_feature_columns: list[str]
    numeric_feature_columns: list[str]
    model_feature_columns: list[str]
    total_model_feature_count: int


def build_feature_schema_summary() -> FeatureSchemaSummary:
    """Build a compact summary of the ML-ready feature schema."""

    return FeatureSchemaSummary(
        identifier_columns=list(ID_COLUMNS),
        date_columns=list(DATE_COLUMNS),
        treatment_columns=list(TREATMENT_COLUMNS),
        outcome_columns=list(OUTCOME_COLUMNS),
        group_columns=list(GROUP_COLUMNS),
        categorical_feature_columns=list(MODEL_CATEGORICAL_FEATURES),
        numeric_feature_columns=list(MODEL_NUMERIC_FEATURES),
        model_feature_columns=list(MODEL_FEATURE_COLUMNS),
        total_model_feature_count=len(MODEL_FEATURE_COLUMNS),
    )
