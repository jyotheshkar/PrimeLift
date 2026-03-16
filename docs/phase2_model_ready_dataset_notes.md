# Revised Phase 2 Model-Ready Dataset Notes

This document explains what was implemented for the revised ML-first Phase 2, what files now define the model-ready dataset workflow, and what terminal output you should see when you run the preparation yourself.

## Phase 2 Scope

After revising `PROJECT_SPEC.md`, Phase 2 is no longer only about generating a raw synthetic dataset.

It now covers:

1. keeping the reproducible raw London experiment dataset
2. deterministic train, validation, and test splits
3. leakage-safe preprocessing fit on train only
4. saved processed model-ready datasets
5. saved preprocessing artifact and manifest
6. helper utilities to inspect split sizes and transformed feature columns

## Files Added or Updated

Updated:

- `README.md`
- `.gitignore`
- `backend/src/primelift/data/__init__.py`
- `backend/src/primelift/features/__init__.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/features/preprocessing.py`
- `backend/src/primelift/data/preparation.py`
- `backend/scripts/prepare_model_data.py`
- `backend/scripts/summarize_model_data.py`
- `backend/tests/test_model_preparation.py`
- `artifacts/models/.gitkeep`
- `artifacts/reports/.gitkeep`
- `artifacts/metrics/.gitkeep`
- `artifacts/features/.gitkeep`

Generated locally by this phase:

- `data/processed/london_campaign_users_train_model_ready.csv`
- `data/processed/london_campaign_users_validation_model_ready.csv`
- `data/processed/london_campaign_users_test_model_ready.csv`
- `artifacts/features/feature_preprocessor.joblib`
- `artifacts/features/prepared_dataset_manifest.json`

## What Was Implemented

### 1. Deterministic split workflow

Implemented in:

- `backend/src/primelift/data/preparation.py`

The dataset is now split into:

- `70%` train
- `15%` validation
- `15%` test

The split is deterministic with random seed `42`.

To preserve balance, the split logic uses the richest feasible stratification label available from:

- `segment + treatment + conversion`
- `segment + treatment`
- `treatment + conversion`
- `treatment`

This avoids failures on sparse local subsets while still preserving experiment structure as much as possible.

### 2. Leakage-safe preprocessing

Implemented in:

- `backend/src/primelift/features/preprocessing.py`

The preprocessing pipeline is fit on the training split only.

It uses:

- median imputation + standard scaling for numeric features
- most-frequent imputation + one-hot encoding for categorical features

The learned feature matrix excludes:

- `user_id`
- `campaign_id`
- `event_date`
- `treatment`
- `conversion`
- `revenue`

Those columns are kept as metadata in the saved prepared datasets, but they are not used as learned model features.

### 3. Saved model-ready datasets

Prepared CSV outputs are written to:

- `data/processed/london_campaign_users_train_model_ready.csv`
- `data/processed/london_campaign_users_validation_model_ready.csv`
- `data/processed/london_campaign_users_test_model_ready.csv`

Each saved file contains:

- metadata columns
- split label
- transformed numeric features
- transformed one-hot categorical features

### 4. Saved preprocessing artifact

The fitted preprocessing pipeline is saved to:

- `artifacts/features/feature_preprocessor.joblib`

This makes the feature transformation reproducible for later model training phases.

### 5. Saved manifest and inspection utility

The preparation manifest is saved to:

- `artifacts/features/prepared_dataset_manifest.json`

Inspection commands:

```powershell
python backend/scripts/prepare_model_data.py
python backend/scripts/summarize_model_data.py
```

## Important Scope Note

Revised Phase 2 still does **not** train any ML models.

It prepares the raw dataset so Phase 3 can train causal ML models cleanly.

This phase produces:

- model-ready splits
- transformed features
- preprocessing artifacts

It does not yet produce:

- fitted XLearner or DRLearner models
- per-user CATE predictions
- model selection reports

## How to Verify Revised Phase 2

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Prepare the model-ready datasets:

```powershell
python backend/scripts/prepare_model_data.py
```

Inspect the saved manifest:

```powershell
python backend/scripts/summarize_model_data.py
```

Optional quick column check on the train split:

```powershell
python -c "import pandas as pd; df = pd.read_csv('data/processed/london_campaign_users_train_model_ready.csv', nrows=1); print({'column_count': len(df.columns), 'first_columns': df.columns[:15].tolist()})"
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/prepare_model_data.py
```

```json
{
  "input_dataset_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\data\\raw\\london_campaign_users_100k.csv",
  "train_size": 0.7,
  "validation_size": 0.15,
  "test_size": 0.15,
  "random_seed": 42,
  "raw_feature_count": 16,
  "transformed_feature_count": 105,
  "transformed_feature_sample": [
    "numeric__age",
    "numeric__prior_engagement_score",
    "numeric__prior_purchases_90d",
    "numeric__prior_sessions_30d",
    "numeric__avg_order_value",
    "numeric__customer_tenure_days",
    "categorical__london_borough_Barking and Dagenham",
    "categorical__london_borough_Barnet",
    "categorical__london_borough_Bexley",
    "categorical__london_borough_Brent",
    "categorical__london_borough_Bromley",
    "categorical__london_borough_Camden",
    "categorical__london_borough_City of London",
    "categorical__london_borough_Croydon",
    "categorical__london_borough_Ealing",
    "categorical__london_borough_Enfield",
    "categorical__london_borough_Greenwich",
    "categorical__london_borough_Hackney",
    "categorical__london_borough_Hammersmith and Fulham",
    "categorical__london_borough_Haringey"
  ],
  "splits": [
    {
      "split_name": "train",
      "row_count": 70000,
      "treatment_rate": 0.499186,
      "conversion_rate": 0.117757,
      "file_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\data\\processed\\london_campaign_users_train_model_ready.csv"
    },
    {
      "split_name": "validation",
      "row_count": 15000,
      "treatment_rate": 0.499267,
      "conversion_rate": 0.1178,
      "file_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\data\\processed\\london_campaign_users_validation_model_ready.csv"
    },
    {
      "split_name": "test",
      "row_count": 15000,
      "treatment_rate": 0.4992,
      "conversion_rate": 0.117733,
      "file_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\data\\processed\\london_campaign_users_test_model_ready.csv"
    }
  ],
  "preprocessor_artifact_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\features\\feature_preprocessor.joblib",
  "manifest_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\features\\prepared_dataset_manifest.json"
}
```

Current output from:

```powershell
python backend/scripts/summarize_model_data.py
```

It matches the saved manifest above and confirms the preparation assets can be reloaded after they are written to disk.

Current quick column check output:

```text
{'column_count': 114, 'first_columns': ['user_id', 'campaign_id', 'event_date', 'treatment', 'conversion', 'revenue', 'segment', 'london_borough', 'split', 'numeric__age', 'numeric__prior_engagement_score', 'numeric__prior_purchases_90d', 'numeric__prior_sessions_30d', 'numeric__avg_order_value', 'numeric__customer_tenure_days']}
```

That shows:

- `9` metadata columns are preserved
- `105` transformed feature columns are appended
- total saved columns = `114`

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_model_preparation.py -q
```

Current output:

```text
....                                                                     [100%]
4 passed in 4.66s
```

Full backend test output after this phase:

```text
................................                                         [100%]
32 passed in 7.44s
```

## Where to Inspect the Code

- preparation workflow: `backend/src/primelift/data/preparation.py`
- preprocessing pipeline: `backend/src/primelift/features/preprocessing.py`
- feature schema: `backend/src/primelift/features/columns.py`
- preparation script: `backend/scripts/prepare_model_data.py`
- preparation summary script: `backend/scripts/summarize_model_data.py`
- tests: `backend/tests/test_model_preparation.py`

## Short Conclusion

Revised Phase 2 is complete because the repository now has:

- deterministic train, validation, and test splits
- a leakage-safe preprocessing pipeline fit on train only
- saved processed split datasets
- a saved preprocessing artifact
- a saved manifest for inspection
- helper scripts for preparation and summary
- passing tests for the new dataset preparation workflow
