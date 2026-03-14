# Phase 2 Dataset Foundation Notes

This document explains what was implemented for Phase 2, what files define the dataset foundation, and what output you should see in the terminal when you inspect the generated data.

## Phase 2 Scope

Phase 2 required:

1. realistic synthetic experiment dataset generation
2. expected schema and data contract
3. saved CSV output
4. data dictionary
5. lightweight validation tests

All of those items are implemented.

## Files Added or Updated

- `backend/src/primelift/data/generator.py`
- `backend/src/primelift/data/schema.py`
- `backend/src/primelift/data/summary.py`
- `backend/src/primelift/data/viewer.py`
- `backend/scripts/generate_dataset.py`
- `backend/scripts/summarize_dataset.py`
- `backend/tests/test_dataset.py`
- `docs/london_campaign_users_data_dictionary.md`
- `data/raw/london_campaign_users_100k.csv`

## What Was Implemented

### 1. Synthetic dataset generator

Implemented in `generate_london_campaign_users(...)`.

The generator creates exactly:

- `100000` rows

Saved output:

- `data/raw/london_campaign_users_100k.csv`

### 2. Data contract and schema

The required columns and dataset constants are defined in:

- `backend/src/primelift/data/schema.py`

This includes:

- exact required columns
- row count constant
- fixed random seed constant
- column descriptions

### 3. Data dictionary

The column-level documentation is stored in:

- `docs/london_campaign_users_data_dictionary.md`

### 4. Quick inspection utility

Implemented in:

- `backend/src/primelift/data/summary.py`
- `backend/scripts/summarize_dataset.py`

It prints:

- row count
- column names
- treatment/control split
- conversion rate
- segment counts
- borough counts

### 5. Optional full-dataset viewer

For manual inspection of the full dataset, the repository also includes:

- `backend/src/primelift/data/viewer.py`
- `data/raw/london_campaign_users_100k_view.html`

## What the Dataset Contains

The generated dataset includes:

- real London borough names
- plausible postcode areas
- device and platform mix
- channel and traffic source fields
- customer behavior features
- treatment assignment
- conversion outcome
- revenue
- business segments
- event dates

The dataset is reproducible using the configured random seed.

## How to Run Phase 2

Generate the dataset:

```powershell
.venv\Scripts\Activate
python backend/scripts/generate_dataset.py
```

Inspect the generated dataset:

```powershell
python backend/scripts/summarize_dataset.py
```

## Terminal Proof: Current Dataset Summary

This is the current summary output from the repository:

```json
{
  "row_count": 100000,
  "columns": [
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
    "event_date"
  ],
  "treatment_control_split": {
    "0": 50080,
    "1": 49920
  },
  "conversion_rate": 0.1178,
  "segment_counts": {
    "Young Professionals": 17943,
    "Families": 15938,
    "High Intent Returners": 13990,
    "Loyal Members": 12128,
    "Bargain Hunters": 12102,
    "Students": 9970,
    "Window Shoppers": 9871,
    "Lapsed Users": 8058
  },
  "borough_counts": {
    "Croydon": 4787,
    "Barnet": 4317,
    "Ealing": 4240,
    "Bromley": 4143,
    "Lambeth": 3901,
    "Brent": 3841,
    "Newham": 3791,
    "Southwark": 3751,
    "Hackney": 3631,
    "Wandsworth": 3623
  }
}
```

## What That Output Proves

- The CSV exists and loads successfully.
- The dataset has the exact expected row count.
- The required schema is present.
- Treatment is approximately balanced.
- Segment and borough distributions are populated and non-trivial.

## Data Impact Note

Phase 2 is the phase that actually creates the dataset on disk.

It is responsible for:

- generating rows
- assigning features
- assigning treatment
- generating outcomes
- saving the CSV

Later phases read and analyze this dataset but do not replace Phase 2 as the source of the raw CSV.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_dataset.py -q
```

The Phase 2 tests verify:

- exact row count
- required columns exist
- treatment is binary
- conversion is binary
- revenue is zero when conversion is zero
- CSV saving succeeds

The current backend suite already includes these tests and passes:

```text
...................                                                      [100%]
19 passed in 3.68s
```

## Short Conclusion

Phase 2 is complete because the repository now has:

- a realistic synthetic London dataset generator
- a saved 100k CSV
- a schema contract
- a data dictionary
- inspection utilities
- passing dataset validation tests
