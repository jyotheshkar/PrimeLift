# Revised Phase 6 Segment Rollup Notes

This document explains what was implemented for the sixth revised Phase 6 slice, what files were added or updated, and what terminal output you should expect when you call the segment analysis endpoint yourself.

## Phase 6 Scope for This Slice

This slice adds the saved Phase 4 cohort-analysis endpoint to the FastAPI backend.

It does the following:

1. define a typed response contract for segment and cohort analysis
2. expose `GET /analysis/segments`
3. load the saved Phase 4 rollup report from the default artifact path
4. load the saved Phase 4 validation summary from the default artifact path
5. return the current top persuadable cohorts, suppression candidates, and per-dimension rollups

This slice covers:

- segment-analysis API endpoint
- typed cohort and rollup response model
- shared access to the saved Phase 4 artifacts
- API smoke tests

It does **not** yet implement:

- `GET /analysis/recommendations`

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/api/__init__.py`
- `backend/src/primelift/api/analysis.py`
- `backend/src/primelift/api/app.py`
- `backend/src/primelift/api/schemas.py`

Added:

- `backend/tests/test_api_analysis_segments.py`
- `docs/phase6_api_segments_notes.md`

## What Was Implemented

### 1. Typed segment-analysis response

Implemented in:

- `backend/src/primelift/api/schemas.py`

The endpoint response currently includes:

- `status`
- `rollup_report_path`
- `validation_report_path`
- `model_name`
- `outcome_column`
- `split_name`
- `overall_observed_ate`
- `validation_verdict`
- `validation_reason`
- `top_persuadable_cohorts`
- `suppression_candidates`
- `top_persuadable_deciles`
- `suppression_candidate_deciles`
- `dimension_summaries`
- `reports`

### 2. Shared Phase 4 artifact loader

Implemented in:

- `backend/src/primelift/api/analysis.py`

The endpoint does **not** recompute rollups. It reads the saved artifacts:

- `artifacts/metrics/phase4_conversion_rollup_report.json`
- `artifacts/metrics/phase4_conversion_validation_summary.json`

That keeps the endpoint aligned with the earlier Phase 4 proof and evaluation workflow.

### 3. Artifact consistency guard

Implemented in:

- `backend/src/primelift/api/analysis.py`

The endpoint returns `404` if one of the required Phase 4 artifacts is missing.

It also returns a server error if the rollup report and validation summary disagree on the model name, because that indicates corrupted or stale analysis state.

## How to Verify Revised Phase 6 Segment Rollup Slice

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
curl "http://127.0.0.1:8000/analysis/segments"
```

Run the focused API tests:

```powershell
python -m pytest backend/tests/test_api_analysis_segments.py -q
```

## Terminal Proof: Actual Output

Current output from a direct app request:

```json
{
  "status": "ok",
  "model_name": "drlearner_conversion",
  "validation_verdict": "promising_but_noisy",
  "top_persuadable_cohort": "Hackney",
  "suppression_candidate": "Lapsed Users",
  "first_dimension": "segment"
}
```

## What That Output Means

- the API can now expose the saved Phase 4 cohort and segment findings directly
- the current model behind those rollups is `drlearner_conversion`
- the current validation verdict remains `promising_but_noisy`
- the first surfaced top cohort is `Hackney`
- the first surfaced suppression candidate is `Lapsed Users`

This is the model-based segment and cohort state the frontend will need for the uplift-insights view.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_api_analysis_segments.py -q
```

Current output:

```text
...                                                                      [100%]
3 passed in 10.35s
```

Full backend test output after this slice:

```text
........................................................................ [ 92%]
......                                                                   [100%]
78 passed in 34.60s
```

## Where to Inspect the Code

- analysis helper: `backend/src/primelift/api/analysis.py`
- app wiring: `backend/src/primelift/api/app.py`
- schemas: `backend/src/primelift/api/schemas.py`
- focused tests: `backend/tests/test_api_analysis_segments.py`

## Short Conclusion

This sixth revised Phase 6 slice is complete because the repository now has:

- a real `GET /analysis/segments` endpoint
- typed model-based cohort and rollup responses
- direct access to the saved Phase 4 artifacts
- terminal-verifiable API output
- passing automated tests

The next Phase 6 slice should be `GET /analysis/recommendations`.
