# Phase 8 Live Overview Integration Notes

## What this slice implemented

This first revised Phase 8 slice connects the overview dashboard to the live FastAPI backend instead of relying only on the saved Phase 7 snapshot.

The overview route now:

- starts in a safe `connecting` state
- fetches live data from the local backend API
- switches into a `live` state when the API responds
- falls back to the saved snapshot if the API is unavailable
- shows a visible source badge so the current mode is obvious

This slice only changes the overview route. The uplift insights, recommendations, and dataset/model screens still use saved artifact snapshots and will be integrated in later Phase 8 slices.

## Files changed

- `frontend/src/lib/primelift-api.ts`
- `frontend/src/components/overview-live-dashboard.tsx`
- `frontend/src/app/page.tsx`
- `backend/src/primelift/api/app.py`
- `backend/tests/test_api_health.py`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/globals.css`
- `frontend/.env.example`
- `.gitignore`

## What changed technically

### Frontend

- Added a typed frontend API helper that calls:
  - `/health`
  - `/analysis/ate`
  - `/analysis/models`
  - `/analysis/segments`
  - `/analysis/recommendations`
- Added a client overview component that maps those responses into the existing dashboard layout.
- Preserved the prior snapshot values as the fallback mode.
- Added source-state messaging:
  - `Connecting API`
  - `Live API connected`
  - `Snapshot fallback`

### Backend

- Added CORS middleware so the browser frontend at `http://127.0.0.1:3000` and `http://localhost:3000` can call the FastAPI backend at `http://127.0.0.1:8000`.
- Added a focused backend test to verify the local frontend origin receives the expected CORS header.

### Build stability

- Removed `next/font/google` usage from the layout and replaced it with local font stacks in CSS.
- This keeps the frontend buildable in offline or restricted-network environments.

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

The frontend environment file currently contains:

```text
NEXT_PUBLIC_PRIMELIFT_API_URL=http://127.0.0.1:8000
```

If the frontend must call a different backend origin, update `.env.local` or set `PRIMELIFT_FRONTEND_ORIGINS` on the backend side.

## Proof from verification

### Backend test

```text
.venv\Scripts\python.exe -m pytest backend/tests/test_api_health.py -q
...                                                                      [100%]
3 passed in 28.69s
```

### Frontend quality checks

```text
npm run lint
```

Passed with no ESLint errors.

```text
npm run build
```

Build passed after the local font-stack change.

### Live backend proof

```text
curl.exe -s -i http://127.0.0.1:8000/health
HTTP/1.1 200 OK
...
{"status":"ok","service_name":"PrimeLift AI API","api_version":"0.1.0","current_phase":6,"timestamp_utc":"2026-03-15T10:45:43.001044+00:00","readiness":{"dataset_ready":true,"prepared_data_ready":true,"phase5_closeout_ready":true}}
```

### Browser proof

Playwright loaded `http://127.0.0.1:3000/`, waited for the client fetches to complete, and then observed the page change from the initial connecting state to the live state.

Observed on the page:

- headline changed to `Live London causal decision engine`
- source badge changed to `Live API connected`
- frontend stance changed to `Connected to PrimeLift AI API 0.1.0. Current backend phase: 6.`
- readiness panel changed to live backend-backed items

Observed network requests from the browser:

```text
[GET] http://127.0.0.1:8000/health => [200] OK
[GET] http://127.0.0.1:8000/analysis/ate?outcome=conversion&bootstrap_samples=120 => [200] OK
[GET] http://127.0.0.1:8000/analysis/models => [200] OK
[GET] http://127.0.0.1:8000/analysis/segments => [200] OK
[GET] http://127.0.0.1:8000/analysis/recommendations => [200] OK
```

## What is still left in Phase 8

The live overview integration is complete.

The next Phase 8 slices should integrate:

1. `/uplift-insights`
2. `/recommendations`
3. `/dataset-models`
