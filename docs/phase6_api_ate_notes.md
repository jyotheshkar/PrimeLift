# Revised Phase 6 ATE Analysis Notes

This document explains what was implemented for the fourth revised Phase 6 slice, what files were added or updated, and what terminal output you should expect when you call the ATE analysis endpoint yourself.

## Phase 6 Scope for This Slice

This slice adds the first analysis endpoint to the FastAPI backend.

It does the following:

1. define a typed response contract for ATE baseline analysis
2. expose `GET /analysis/ate`
3. load the saved dataset CSV from the default project path
4. run the existing Phase 3 baseline ATE and bootstrap CI logic
5. return a typed baseline result for either `conversion` or `revenue`

This slice covers:

- analysis API endpoint
- typed baseline response model
- shared causal baseline logic between scripts and API
- API smoke tests

It does **not** yet implement:

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

- `backend/src/primelift/api/analysis.py`
- `backend/tests/test_api_analysis_ate.py`
- `docs/phase6_api_ate_notes.md`

## What Was Implemented

### 1. Typed baseline analysis response

Implemented in:

- `backend/src/primelift/api/schemas.py`

The endpoint response currently includes:

- `status`
- `source_path`
- `row_count`
- `result`

The nested `result` includes:

- `outcome_column`
- `treatment_column`
- `treated_mean`
- `control_mean`
- `ate`
- `absolute_lift`
- `relative_lift`
- `ci_lower`
- `ci_upper`
- `confidence_level`
- `bootstrap_samples`

### 2. Shared ATE analysis helper

Implemented in:

- `backend/src/primelift/api/analysis.py`

The endpoint does **not** duplicate the causal baseline logic. It calls the existing Phase 3 implementation:

- `analyze_average_treatment_effect(...)`

That keeps the API aligned with the CLI and proof scripts already present in the repo.

### 3. Narrow and explicit query contract

Implemented in:

- `backend/src/primelift/api/app.py`

The endpoint currently supports:

- `outcome=conversion`
- `outcome=revenue`
- `bootstrap_samples`
- `confidence_level`
- `random_seed`

It also returns `404` if the dataset CSV has not been generated yet.

## How to Verify Revised Phase 6 ATE Analysis Slice

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
curl "http://127.0.0.1:8000/analysis/ate?outcome=conversion&bootstrap_samples=300"
```

Run the focused API tests:

```powershell
python -m pytest backend/tests/test_api_analysis_ate.py -q
```

## Terminal Proof: Actual Output

Current output from a direct app request:

```json
{
  "status": "ok",
  "row_count": 100000,
  "outcome_column": "conversion",
  "ate": 0.010176858052756615,
  "ci_lower": 0.006845660724891456,
  "ci_upper": 0.013718153518473017,
  "bootstrap_samples": 120
}
```

## What That Output Means

- the API can now expose the baseline causal estimate directly
- the endpoint is using the real saved 100,000-row dataset
- the output matches the Phase 3 baseline analysis layer instead of inventing a new calculation path
- the treatment effect remains positive on the current synthetic dataset, with a bootstrap interval that stays above zero

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_api_analysis_ate.py -q
```

Current output:

```text
....                                                                     [100%]
4 passed in 12.32s
```

Full backend test output after this slice:

```text
........................................................................ [ 98%]
.                                                                        [100%]
73 passed in 30.43s
```

## Where to Inspect the Code

- analysis helper: `backend/src/primelift/api/analysis.py`
- app wiring: `backend/src/primelift/api/app.py`
- schemas: `backend/src/primelift/api/schemas.py`
- focused tests: `backend/tests/test_api_analysis_ate.py`

## Short Conclusion

This fourth revised Phase 6 slice is complete because the repository now has:

- a real `GET /analysis/ate` endpoint
- typed baseline ATE responses
- shared Phase 3 baseline analysis logic behind the API
- terminal-verifiable API output
- passing automated tests

The next Phase 6 slice should be `GET /analysis/models`.
