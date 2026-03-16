# Revised Phase 6 Model Comparison Notes

This document explains what was implemented for the fifth revised Phase 6 slice, what files were added or updated, and what terminal output you should expect when you call the model comparison endpoint yourself.

## Phase 6 Scope for This Slice

This slice adds the saved-model comparison endpoint to the FastAPI backend.

It does the following:

1. define a typed response contract for model comparison output
2. expose `GET /analysis/models`
3. load the saved Phase 3 comparison report from the default artifact path
4. return the current conversion champion, challenger, and revenue champion
5. return the full typed comparison report for downstream UI use

This slice covers:

- model comparison API endpoint
- typed comparison response model
- shared access to the Phase 3 saved comparison artifact
- API smoke tests

It does **not** yet implement:

- `GET /analysis/segments`
- `GET /analysis/recommendations`

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/api/__init__.py`
- `backend/src/primelift/api/analysis.py`
- `backend/src/primelift/api/app.py`
- `backend/src/primelift/api/schemas.py`

Added:

- `backend/tests/test_api_analysis_models.py`
- `docs/phase6_api_models_notes.md`

## What Was Implemented

### 1. Typed model comparison response

Implemented in:

- `backend/src/primelift/api/schemas.py`

The endpoint response currently includes:

- `status`
- `source_path`
- `report_name`
- `comparison_split`
- `conversion_champion_model_name`
- `conversion_challenger_model_name`
- `revenue_champion_model_name`
- `report`

The nested `report` is the full typed Phase 3 comparison payload already generated earlier in the project.

### 2. Shared comparison-artifact loader

Implemented in:

- `backend/src/primelift/api/analysis.py`

The endpoint does **not** retrain or recompute models. It reads the saved comparison artifact:

- `artifacts/metrics/phase3_model_comparison_report.json`

That keeps the endpoint fast, stable, and aligned with the earlier Phase 3 proof flow.

### 3. Explicit missing-artifact behavior

Implemented in:

- `backend/src/primelift/api/analysis.py`

If the Phase 3 comparison report is missing, the API returns `404` with a clear instruction to generate that artifact first.

## How to Verify Revised Phase 6 Model Comparison Slice

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
curl "http://127.0.0.1:8000/analysis/models"
```

Run the focused API tests:

```powershell
python -m pytest backend/tests/test_api_analysis_models.py -q
```

## Terminal Proof: Actual Output

Current output from a direct app request:

```json
{
  "status": "ok",
  "report_name": "phase3_model_comparison",
  "comparison_split": "test",
  "conversion_champion_model_name": "drlearner_conversion",
  "conversion_challenger_model_name": "causal_forest_conversion",
  "revenue_champion_model_name": "drlearner_revenue"
}
```

## What That Output Means

- the API can now expose the saved trained-model ranking directly
- the current conversion champion remains `drlearner_conversion`
- the current conversion challenger remains `causal_forest_conversion`
- the current revenue champion remains `drlearner_revenue`

This is exactly the Phase 3 selection state the frontend will need later.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_api_analysis_models.py -q
```

Current output:

```text
..                                                                       [100%]
2 passed in 12.66s
```

Full backend test output after this slice:

```text
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 38.61s
```

## Where to Inspect the Code

- analysis helper: `backend/src/primelift/api/analysis.py`
- app wiring: `backend/src/primelift/api/app.py`
- schemas: `backend/src/primelift/api/schemas.py`
- focused tests: `backend/tests/test_api_analysis_models.py`

## Short Conclusion

This fifth revised Phase 6 slice is complete because the repository now has:

- a real `GET /analysis/models` endpoint
- typed model comparison responses
- direct access to the saved Phase 3 comparison artifact
- terminal-verifiable API output
- passing automated tests

The next Phase 6 slice should be `GET /analysis/segments`.
