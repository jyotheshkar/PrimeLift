# Revised Phase 6 Dataset Generation Notes

This document explains what was implemented for the second revised Phase 6 slice, what files were added or updated, and what terminal output you should expect when you call the dataset generation endpoint yourself.

## Phase 6 Scope for This Slice

This slice adds the first real data endpoint to the FastAPI backend.

It does the following:

1. define a typed request contract for dataset generation
2. define a typed response contract for dataset generation
3. expose `POST /dataset/generate`
4. call the same dataset generator used by the CLI
5. save the generated CSV to the default project data path
6. return a typed operational summary of the generated dataset

This slice covers:

- dataset generation API endpoint
- typed request and response models
- shared generator logic between CLI and API
- API smoke tests

It does **not** yet implement:

- `GET /dataset/sample`
- `GET /analysis/ate`
- `GET /analysis/models`
- `GET /analysis/segments`
- `GET /analysis/recommendations`

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/api/__init__.py`
- `backend/src/primelift/api/app.py`
- `backend/src/primelift/api/schemas.py`

Added:

- `backend/src/primelift/api/dataset.py`
- `backend/tests/test_api_dataset_generate.py`

## What Was Implemented

### 1. Typed dataset generation request

Implemented in:

- `backend/src/primelift/api/schemas.py`

The request contract currently accepts:

- `rows`
- `seed`

with positive row-count validation.

### 2. Shared generator path

Implemented in:

- `backend/src/primelift/api/dataset.py`

The endpoint does **not** reimplement generation logic. It calls:

- `generate_london_campaign_users(...)`
- `save_dataset(...)`
- `build_dataset_summary(...)`

so the API and CLI remain aligned.

### 3. Typed response summary

The endpoint returns:

- generation status
- output path
- seed used
- dataset summary

The dataset summary currently includes:

- row count
- column names
- treatment/control split
- conversion rate
- segment counts
- borough counts

## Important Scope Note

This endpoint writes to the default dataset path:

- `data/raw/london_campaign_users_100k.csv`

That is deliberate for now because the project is still local-first and artifact-driven.

For proof during this slice, the endpoint was called once with a 1,000-row payload and then the default 100,000-row dataset was immediately restored so the repo remained consistent afterward.

## How to Verify Revised Phase 6 Dataset Generation Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Start the app:

```powershell
uvicorn primelift.api.app:app --app-dir backend/src --reload
```

Call the endpoint:

```powershell
curl -X POST "http://127.0.0.1:8000/dataset/generate" `
  -H "Content-Type: application/json" `
  -d "{\"rows\": 100000, \"seed\": 42}"
```

Run the focused API tests:

```powershell
python -m pytest backend/tests/test_api_dataset_generate.py -q
```

## Terminal Proof: Actual Output

Current output from a direct app request:

```json
{
  "status": "generated",
  "output_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\data\\raw\\london_campaign_users_100k.csv",
  "row_count": 1000,
  "conversion_rate": 0.119,
  "treatment_control_split": {
    "0": 511,
    "1": 489
  }
}
```

## What That Output Means

- the API can now trigger dataset generation directly
- the request is validated
- the response is typed
- the endpoint returns a useful operational summary instead of only a file path

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_api_dataset_generate.py -q
```

Current output:

```text
..                                                                       [100%]
2 passed in 6.58s
```

Full backend test output after this slice:

```text
..................................................................       [100%]
66 passed in 32.17s
```

## Where to Inspect the Code

- endpoint helper: `backend/src/primelift/api/dataset.py`
- app wiring: `backend/src/primelift/api/app.py`
- schemas: `backend/src/primelift/api/schemas.py`
- focused tests: `backend/tests/test_api_dataset_generate.py`

## Short Conclusion

This second revised Phase 6 slice is complete because the repository now has:

- a real `POST /dataset/generate` endpoint
- typed request and response models
- shared generator logic between CLI and API
- terminal-verifiable API output
- passing automated tests

The next Phase 6 slice should be `GET /dataset/sample`.
