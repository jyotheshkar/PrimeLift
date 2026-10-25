# PrimeLift AI

A personal causal-inference and decision-support prototype for a **synthetic** London marketing experiment. It estimates treatment effects, compares uplift models, builds targeting and budget recommendations, and presents results through FastAPI and a Next.js dashboard.

The repository demonstrates an analytical workflow. It does not establish real campaign impact, production deployment, or results for Amazon or any other employer.

## What is implemented

| Area | Implementation | Evidence |
| --- | --- | --- |
| Synthetic data | Seeded NumPy generator; default 100,000 rows, seed 42, 22 columns | [Generator](backend/src/primelift/data/generator.py), [data dictionary](docs/london_campaign_users_data_dictionary.md) |
| Model preparation | 70/15/15 stratified splits; preprocessing fitted on training data | [Preparation](backend/src/primelift/data/preparation.py), [features](backend/src/primelift/features/) |
| Treatment effects | Difference-in-means ATE with stratified bootstrap intervals; EconML XLearner, DRLearner and CausalForestDML | [Causal modules](backend/src/primelift/causal/) |
| Decisions | Uplift deciles/cohort rollups, targeting/suppression, budget allocation, DRPolicyTree/DRPolicyForest comparison | [Uplift](backend/src/primelift/uplift/), [decisions](backend/src/primelift/decision/) |
| API | Dataset generation/preview, ATE calculation and saved-report endpoints | [FastAPI app](backend/src/primelift/api/app.py) |
| Interface | Four Next.js routes with different data-loading behaviour, detailed below | [Routes](frontend/src/app/), [API client](frontend/src/lib/primelift-api.ts) |

## Data provenance and interpretation

The generator creates fictional user identifiers, demographics, engagement, treatment, conversion and revenue. London borough names are real geography; user records and outcomes are simulated. The `is_prime_like_member` field is a simulated loyalty-membership feature, not evidence of Amazon customer data.

Treatment is independently sampled with probability 0.5. Conversion probabilities include deliberately programmed heterogeneous treatment effects; revenue is simulated conditional on conversion. Any reported lift, policy value or budget is a result of this simulation.

The ATE is the treated mean minus the control mean. Its causal interpretation relies on random assignment, consistent treatment/outcome definitions, no interference and representative observation of outcomes. Applying the workflow to observational data would additionally require justified conditional exchangeability and overlap; an estimator cannot verify those assumptions automatically.

The ML modules estimate conditional effects with nuisance/outcome models. Their scores are estimates, not observed individual counterfactuals. Bootstrap intervals in the baseline are not uncertainty bounds for every model or targeting decision.

**Evaluation limitation:** the current model-comparison code selects champions using the split named `test`. Subsequent decile, policy and budget reports reuse that split. These are exploratory selection results, not an untouched final evaluation. Before claiming generalisation, select on validation data and evaluate the frozen policy once on a separate holdout or new experiment.

## Run locally

Use Python 3.11 or 3.12 and a Node.js version supported by the pinned Next.js 16 release (20.9+). Run commands from the repository root unless shown otherwise.

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn primelift.api.app:app --app-dir backend/src --host 127.0.0.1 --port 8001
```

On macOS/Linux, activate with `source .venv/bin/activate`. Requirements use version ranges rather than a locked Python environment, so dependency resolution can differ between installations.

Open [interactive API documentation](http://127.0.0.1:8001/docs) or [health](http://127.0.0.1:8001/health). Health reports file-existence readiness flags; an `ok` response does not prove the analysis has run.

### Frontend

In a second terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev -- --hostname 127.0.0.1 --port 3000
```

On macOS/Linux use `cp .env.example .env.local`. The example sets `NEXT_PUBLIC_PRIMELIFT_API_URL=http://127.0.0.1:8001`, matching the API client's default. Restart the frontend after changing it.

| Route | Current source behaviour |
| --- | --- |
| `/` | Starts idle. Running the dashboard generates/overwrites the synthetic CSV, calculates ATE, then reads saved model, cohort and recommendation reports. It does **not** train the models. Errors show an error screen. |
| `/uplift-insights` | Fetches `/analysis/segments`; uses the checked-in frontend snapshot when the API fails. |
| `/recommendations` | Fetches `/analysis/recommendations`; falls back to its frontend snapshot. |
| `/dataset-models` | Fetches a dataset preview and saved model comparison; falls back to its frontend snapshot. |

An API-connected screen can still be displaying a previously generated report. Changing the dataset row count or seed does not regenerate the committed ML/policy reports, so the dashboard can mix a fresh CSV/ATE with older analysis. Keep this distinction visible when demonstrating the project; report-to-dataset provenance is not enforced.

The raw CSV, processed splits and trained model binaries are not committed. The large HTML dataset view and JSON metric reports are saved demonstration artifacts. Historical absolute paths inside reports describe their original run and are not portable input paths.

### Optional analysis workflow

These commands generate local files; they are not needed for the lightweight artifact check:

```powershell
python backend/scripts/generate_dataset.py --rows 100000 --seed 42
python backend/scripts/prepare_model_data.py
python backend/scripts/run_causal_analysis.py
```

Model training, rollup and policy stages have separate scripts under [backend/scripts](backend/scripts/). They require prepared datasets and upstream artifacts. Full model training can take substantial time; generating a CSV alone is insufficient to reproduce the saved recommendations. [PROJECT_SPEC.md](PROJECT_SPEC.md) and the chronological [phase notes](docs/) provide the development history; current source takes precedence over older phase-status statements.

## Verification

A dependency-free check validates the six committed reports used by the dashboard for JSON integrity, matching model/split identities, decile structure and budget reconciliation:

```powershell
python scripts/validate_demo_artifacts.py
```

It checks internal consistency of the saved files. It does not reproduce model scores, establish data lineage, test the API/UI, or certify causal validity.

The lightweight GitHub Actions workflow runs this check and Python syntax compilation without generating data or training models.

After installing dependencies, the existing backend suite and frontend checks can be run separately:

```powershell
python -m pytest backend/tests -q
cd frontend
npm run lint
npm run build
```

Some backend tests train small models or generate synthetic data. Historical test counts in commit messages/phase notes are run-specific; no current passing count is asserted here.

## Scope and limitations

- Local prototype with a single writable dataset path; concurrent users/runs are not isolated.
- The API has no authentication and currently permits wildcard CORS. The dataset-generation endpoint writes files. Keep the demo on localhost; deployment needs separate access, resource-limit and data-lifecycle design.
- Docker/Fly.io configuration is present; the Docker build generates a dataset. Configuration alone is not proof of an active deployment.
- Synthetic group effects, demographics and targeting outputs are modelling exercises, not validated recommendations about real people.
- The repository contains AI-assisted/co-authored development history. Personal contribution and design decisions should be explained precisely when presenting it.
- No repository licence is currently supplied; third-party dependencies retain their own licences.

A defensible portfolio description is: “Built a synthetic campaign-analysis prototype with treatment-effect estimators, model comparison, decision reports, a FastAPI backend and a partially integrated Next.js interface.” Quantified real-world uplift or production-use claims require separate evidence.
