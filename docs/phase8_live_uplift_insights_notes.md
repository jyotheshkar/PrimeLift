# Phase 8 Live Uplift Insights Notes

## What this slice implemented

This second revised Phase 8 slice connects the `/uplift-insights` route to the live Phase 4 backend outputs instead of relying only on the saved Phase 7 snapshot.

The uplift insights route now:

- starts in a safe `connecting` state
- fetches the live Phase 4 segment analysis payload from the backend
- switches into a `live` state when the API responds
- falls back to the saved uplift snapshot if the API is unavailable
- keeps the same visual structure while replacing the values with live data

## Files changed

- `backend/src/primelift/api/schemas.py`
- `backend/src/primelift/api/analysis.py`
- `backend/tests/test_api_analysis_segments.py`
- `frontend/src/lib/primelift-api.ts`
- `frontend/src/components/uplift-insights-live-dashboard.tsx`
- `frontend/src/app/uplift-insights/page.tsx`
- `README.md`

## What changed technically

### Backend

The existing `GET /analysis/segments` endpoint now exposes the extra Phase 4 data the uplift screen needs:

- decile report path
- top and bottom decile observed uplift
- top-decile gain over baseline
- uplift concentration ratio
- positive and negative decile counts
- best and worst decile ranks
- monotonicity break count
- full decile table

This keeps the frontend on one Phase 4 endpoint instead of forcing it to read local artifacts directly.

### Frontend

The uplift insights screen now uses a client component that:

- fetches live data from `/analysis/segments`
- maps live segment rollups into the segment action table
- maps live decile rows into the decile grid
- maps live cohort outputs into the positive responder and suppression panels
- preserves snapshot fallback behavior if the API request fails

## How to run it

### Backend

```powershell
.venv\Scripts\python.exe -m uvicorn primelift.api.app:app --app-dir backend/src --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd frontend
copy .env.example .env.local
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open:

```text
http://127.0.0.1:3000/uplift-insights
```

## Proof from verification

### Backend API test

```text
.venv\Scripts\python.exe -m pytest backend/tests/test_api_analysis_segments.py -q
...                                                                      [100%]
3 passed in 27.13s
```

### Frontend checks

```text
npm run lint
```

Passed with no ESLint errors.

```text
npm run build
```

Passed successfully after the live route wiring.

### Live endpoint proof

```text
curl.exe -s http://127.0.0.1:8000/analysis/segments
```

Returned `200 OK` with the updated payload, including:

- `deciles`
- `top_decile_gain_over_overall_ate`
- `uplift_concentration_ratio`
- `monotonicity_break_count`

### Browser proof

Playwright loaded `http://127.0.0.1:3000/uplift-insights`, waited for the client fetch to complete, and then observed:

- source badge changed to `Live API connected`
- title changed to `DRLearner conversion is now driving this uplift screen from live Phase 4 artifacts.`
- notes list changed to live decile and validation messages
- positive responder and suppression panels were populated from the live API response

Observed browser network:

```text
[GET] http://127.0.0.1:8000/analysis/segments => [200] OK
```

## What is still left in Phase 8

This uplift insights live integration is complete.

The next Phase 8 slices should integrate:

1. `/recommendations`
2. `/dataset-models`
