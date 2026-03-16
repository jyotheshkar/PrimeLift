# Revised Phase 6 Dataset Sample Notes

This document explains what was implemented for the third revised Phase 6 slice, what files were added or updated, and what terminal output you should expect when you call the dataset sample endpoint yourself.

## Phase 6 Scope for This Slice

This slice adds the first read-only dataset preview endpoint to the FastAPI backend.

It does the following:

1. define a typed response contract for dataset preview
2. expose `GET /dataset/sample`
3. load the saved CSV from the default project data path
4. return a bounded preview of rows from the saved dataset
5. return a clear `404` if the dataset has not been generated yet

This slice covers:

- dataset sample API endpoint
- typed response model
- saved-CSV preview logic
- API smoke tests

It does **not** yet implement:

- `GET /analysis/ate`
- `GET /analysis/models`
- `GET /analysis/segments`
- `GET /analysis/recommendations`

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/api/__init__.py`
- `backend/src/primelift/api/app.py`
- `backend/src/primelift/api/dataset.py`
- `backend/src/primelift/api/schemas.py`

Added:

- `backend/tests/test_api_dataset_sample.py`
- `docs/phase6_dataset_sample_notes.md`

## What Was Implemented

### 1. Typed dataset sample response

Implemented in:

- `backend/src/primelift/api/schemas.py`

The response contract currently includes:

- `status`
- `source_path`
- `requested_rows`
- `returned_rows`
- `available_rows`
- `columns`
- `records`

### 2. Shared preview helper

Implemented in:

- `backend/src/primelift/api/dataset.py`

The endpoint does **not** regenerate data. It reads the existing CSV through the shared dataset loader and returns a preview from the saved artifact path.

That keeps the endpoint read-only and consistent with the current local-first artifact workflow.

### 3. Input validation and missing-file behavior

Implemented in:

- `backend/src/primelift/api/app.py`
- `backend/src/primelift/api/dataset.py`

The endpoint validates:

- `rows >= 1`
- `rows <= 100`

If the default dataset CSV does not exist, the API returns `404` with a clear instruction to generate the dataset first.

## How to Verify Revised Phase 6 Dataset Sample Slice

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
curl "http://127.0.0.1:8000/dataset/sample?rows=10"
```

Run the focused API tests:

```powershell
python -m pytest backend/tests/test_api_dataset_sample.py -q
```

## Terminal Proof: Actual Output

Current output from a direct app request:

```json
{
  "status": "ok",
  "requested_rows": 3,
  "returned_rows": 3,
  "available_rows": 100000,
  "first_user_id": "LON-000001",
  "columns": [
    "user_id",
    "london_borough",
    "postcode_area",
    "age",
    "age_band"
  ]
}
```

## What That Output Means

- the API can now preview the saved dataset directly
- the endpoint is read-only
- the response is typed
- the backend is returning rows from the actual 100,000-row CSV already present in the repo

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_api_dataset_sample.py -q
```

Current output:

```text
...                                                                      [100%]
3 passed in 7.09s
```

Full backend test output after this slice:

```text
.....................................................................    [100%]
69 passed in 33.93s
```

## Where to Inspect the Code

- endpoint helper: `backend/src/primelift/api/dataset.py`
- app wiring: `backend/src/primelift/api/app.py`
- schemas: `backend/src/primelift/api/schemas.py`
- focused tests: `backend/tests/test_api_dataset_sample.py`

## Short Conclusion

This third revised Phase 6 slice is complete because the repository now has:

- a real `GET /dataset/sample` endpoint
- typed preview responses
- read-only access to the saved dataset artifact
- terminal-verifiable API output
- passing automated tests

The next Phase 6 slice should be `GET /analysis/ate`.
