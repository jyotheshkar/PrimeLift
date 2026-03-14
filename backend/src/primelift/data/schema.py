"""Schema contract and column documentation for the London campaign dataset."""

from __future__ import annotations

DATASET_ROW_COUNT = 100_000
DATASET_RANDOM_SEED = 42

REQUIRED_COLUMNS = [
    "user_id",
    "london_borough",
    "postcode_area",
    "age",
    "age_band",
    "gender",
    "device_type",
    "platform",
    "traffic_source",
    "channel",
    "prior_engagement_score",
    "prior_purchases_90d",
    "prior_sessions_30d",
    "avg_order_value",
    "customer_tenure_days",
    "is_prime_like_member",
    "segment",
    "treatment",
    "conversion",
    "revenue",
    "campaign_id",
    "event_date",
]

COLUMN_DESCRIPTIONS = {
    "user_id": "Deterministic synthetic user key for each eligible London user.",
    "london_borough": "Real London borough or City of London assigned with a non-uniform population-like distribution.",
    "postcode_area": "Plausible London postcode area associated with the borough such as E, EC, N, NW, SE, SW, W, or WC.",
    "age": "Synthetic adult age in years.",
    "age_band": "Bucketed age group derived from age.",
    "gender": "Synthetic self-identification category for modeling mix realism.",
    "device_type": "Primary device type used at exposure time.",
    "platform": "Observed platform at exposure time, aligned to the device mix.",
    "traffic_source": "Top-level acquisition or return source.",
    "channel": "More specific marketing channel nested under the traffic source.",
    "prior_engagement_score": "Recent engagement score on a 0 to 100 scale based on historical activity.",
    "prior_purchases_90d": "Observed completed purchases in the last 90 days.",
    "prior_sessions_30d": "Observed site or app sessions in the last 30 days.",
    "avg_order_value": "Synthetic historical average order value in GBP.",
    "customer_tenure_days": "Days since first recorded activity.",
    "is_prime_like_member": "Binary flag for a paid or loyalty style membership.",
    "segment": "Business-style user segment used for heterogeneous response patterns.",
    "treatment": "Binary experimental treatment assignment.",
    "conversion": "Binary experiment outcome indicating whether the user converted.",
    "revenue": "Observed revenue in GBP; zero when no conversion occurred.",
    "campaign_id": "Synthetic campaign family identifier tied to the acquisition channel mix.",
    "event_date": "Exposure date in ISO format across a recent multi-week window.",
}
