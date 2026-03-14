# London Campaign Users Data Dictionary

This file documents the synthetic dataset generated for the first PrimeLift AI backend slice.

Dataset facts:

- Output file: `data/raw/london_campaign_users_100k.csv`
- Row count: `100000`
- Random seed: `42`
- Geography: London borough and postcode-area level
- Event window: `2026-02-01` to `2026-03-02`
- Treatment design: binary randomized experiment with approximately 50/50 assignment

## Column Definitions

| Column | Type | Description |
| --- | --- | --- |
| `user_id` | string | Deterministic synthetic user identifier in the format `LON-000001`. |
| `london_borough` | string | Real London borough or City of London drawn from a non-uniform distribution. |
| `postcode_area` | string | Plausible postcode area associated with the borough, including areas such as `E`, `EC`, `N`, `NW`, `SE`, `SW`, `W`, and `WC`. |
| `age` | integer | Synthetic adult age in years. |
| `age_band` | string | Bucketed age range derived from `age`: `18-24`, `25-34`, `35-44`, `45-54`, `55-64`, or `65+`. |
| `gender` | string | Synthetic gender category used to keep the sample mix realistic. |
| `device_type` | string | Observed primary device at exposure time: `mobile`, `desktop`, or `tablet`. |
| `platform` | string | Platform aligned to the device type, such as `ios`, `android`, or `web`. |
| `traffic_source` | string | Top-level acquisition or return source: `direct`, `paid_search`, `organic_search`, `email`, `social`, `display`, or `affiliate`. |
| `channel` | string | More specific marketing channel nested under the top-level traffic source. |
| `prior_engagement_score` | float | Historical engagement score on a `0-100` scale. Higher values indicate stronger recent activity. |
| `prior_purchases_90d` | integer | Number of purchases completed by the user in the last 90 days. |
| `prior_sessions_30d` | integer | Number of sessions recorded for the user in the last 30 days. |
| `avg_order_value` | float | Synthetic historical average order value in GBP. |
| `customer_tenure_days` | integer | Days since the user first appeared in the product or CRM system. |
| `is_prime_like_member` | integer | Binary membership flag where `1` indicates a loyalty or premium-style member. |
| `segment` | string | Business-facing segment label used to simulate heterogeneous treatment response. |
| `treatment` | integer | Randomized experiment assignment where `1` is treated and `0` is control. |
| `conversion` | integer | Binary conversion outcome generated from the user's baseline probability and treatment effect. |
| `revenue` | float | Observed revenue in GBP. This is always `0` when `conversion = 0`. |
| `campaign_id` | string | Synthetic campaign family identifier tied to the observed traffic source. |
| `event_date` | date string | Exposure date in ISO `YYYY-MM-DD` format across a recent 30-day window. |

## Behavioral Modeling Notes

- Baseline conversion probability increases with engagement, prior purchases, membership, and longer tenure.
- Treatment response varies by segment. High Intent Returners respond most strongly, Young Professionals and Families respond positively, Loyal Members have near-zero uplift, and Window Shoppers trend negative.
- Revenue is generated only for converted users and is loosely anchored to `avg_order_value`, segment value, and light lognormal noise.
