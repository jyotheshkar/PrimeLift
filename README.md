# PrimeLift AI

GitHub repository connection is verified, and the repo now contains the current backend work plus the revised ML-first Phase 1 foundation from `PROJECT_SPEC.md`.

PrimeLift AI is a local-first experimentation and growth analytics product. This repository currently implements the backend foundation and the first frontend dashboard slice for the project:

- Python backend scaffold
- revised ML-ready feature and model scaffold
- realistic synthetic London campaign dataset generation
- revised Phase 2 model-ready split and preprocessing pipeline
- revised Phase 3 first ML uplift model slice with XLearner
- revised Phase 3 second ML uplift model slice with DRLearner
- revised Phase 3 third ML uplift model slice with CausalForestDML
- revised Phase 3 fourth ML uplift model slice with DRLearner for revenue
- revised Phase 3 model comparison and selection layer
- revised Phase 4 first model-based uplift slice with champion decile analysis
- revised Phase 4 second model-based uplift slice with business-dimension rollups
- revised Phase 4 compact validation summary slice
- revised Phase 5 first ML decision slice with model-driven targeting and suppression
- revised Phase 5 second ML decision slice with segment budget allocation
- revised Phase 5 third ML decision slice with DRPolicyTree
- revised Phase 5 fourth ML decision slice with DRPolicyForest challenger
- revised Phase 5 final decision closeout and policy champion selection
- revised Phase 6 first API slice with FastAPI app foundation and health endpoint
- revised Phase 6 second API slice with dataset generation endpoint
- revised Phase 6 third API slice with dataset sample endpoint
- revised Phase 6 fourth API slice with ATE baseline analysis endpoint
- revised Phase 6 fifth API slice with model comparison endpoint
- revised Phase 6 sixth API slice with segment rollup endpoint
- revised Phase 6 seventh API slice with final recommendations endpoint
- revised Phase 7 first frontend slice with overview dashboard foundation
- revised Phase 7 second frontend slice with uplift insights screen
- revised Phase 7 third frontend slice with recommendations screen
- revised Phase 7 fourth frontend slice with dataset and model panel
- revised Phase 8 first frontend-backend integration slice with live overview wiring
- revised Phase 8 second frontend-backend integration slice with live uplift insights wiring
- Phase 3 causal analysis core
- Phase 4 segment uplift analysis
- initial Phase 5 decision ranking slice
- schema and data dictionary documentation
- quick inspection utility
- lightweight tests

The frontend now includes live Phase 8 integration on the overview and uplift insights routes. The recommendations and dataset/model routes are still Phase 7 snapshot screens until their own Phase 8 integrations are built.

## Repository Structure

```text
PrimeLift/
  backend/
    scripts/
      run_causal_forest_conversion.py
      generate_dataset.py
      prepare_model_data.py
      run_causal_analysis.py
      run_drlearner_revenue.py
      run_drlearner_conversion.py
      run_model_based_uplift_deciles.py
      run_model_based_rollups.py
      run_budget_allocation.py
      run_drpolicytree_conversion.py
      run_drpolicyforest_conversion.py
      run_phase5_decision_closeout.py
      run_model_targeting_decisions.py
      run_phase4_validation_summary.py
      run_phase3_model_comparison.py
      run_decision_ranking.py
      run_segment_uplift_analysis.py
      run_xlearner_conversion.py
      show_ml_foundation.py
      summarize_model_data.py
      render_dataset_view.py
      summarize_dataset.py
    src/
      primelift/
        __init__.py
        api/
          analysis.py
          app.py
          dataset.py
          health.py
          schemas.py
        causal/
          ate.py
          causal_forest.py
          drlearner.py
          xlearner.py
        data/
          generator.py
          preparation.py
          schema.py
          summary.py
          viewer.py
        decision/
          budget_allocation.py
          decision_closeout.py
          policy_forest.py
          model_targeting.py
          policy_tree.py
          recommendations.py
        evaluation/
          model_comparison.py
          phase4_validation.py
          registry.py
        features/
          columns.py
          preprocessing.py
        models/
          registry.py
        uplift/
          model_based_analysis.py
          model_based_rollups.py
          segment_analysis.py
        utils/
          artifacts.py
          paths.py
    tests/
      test_ate.py
      conftest.py
      test_decision_ranking.py
      test_dataset.py
      test_causal_forest.py
      test_drlearner.py
      test_drlearner_revenue.py
      test_ml_foundation.py
      test_model_based_uplift.py
      test_model_based_rollups.py
      test_budget_allocation.py
      test_decision_closeout.py
      test_model_targeting.py
      test_api_health.py
      test_api_dataset_generate.py
      test_api_dataset_sample.py
      test_api_analysis_ate.py
      test_api_analysis_models.py
      test_api_analysis_segments.py
      test_api_analysis_recommendations.py
      test_policy_forest.py
      test_policy_tree.py
      test_phase4_validation_summary.py
      test_model_comparison.py
      test_model_preparation.py
      test_segment_uplift.py
      test_xlearner.py
  artifacts/
    features/
    metrics/
    models/
    reports/
  frontend/
    package.json
    src/
      app/
        globals.css
        layout.tsx
        page.tsx
        dataset-models/
          page.tsx
        recommendations/
          page.tsx
        uplift-insights/
          page.tsx
      components/
        app-header.tsx
        metric-card.tsx
        section-card.tsx
      lib/
        dataset-models-data.ts
        overview-data.ts
        recommendations-data.ts
        uplift-insights-data.ts
  data/
    raw/
    processed/
  docs/
    london_campaign_users_data_dictionary.md
  PROJECT_SPEC.md
  README.md
  requirements.txt
```

## Environment Setup

Use Python 3.11 or newer.

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
```

### Mac/Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The revised ML-first dependency plan now includes:

- `lightgbm`
- `econml`
- `joblib`

alongside the existing analytics and API libraries.

## Run Revised Phase 1 ML Foundation Check

Print the current ML-ready scaffold from the terminal:

```bash
python backend/scripts/show_ml_foundation.py
```

This prints structured JSON for:

- feature schema groups
- planned model blueprints
- planned evaluation blueprints
- artifact directories

## Generate the Dataset

Create the default 100,000-row London marketing experiment dataset:

```bash
python backend/scripts/generate_dataset.py
```

Output:

- `data/raw/london_campaign_users_100k.csv`

The generator uses a fixed random seed for reproducibility. You can override defaults if needed:

```bash
python backend/scripts/generate_dataset.py --rows 100000 --seed 42
```

## Inspect the Dataset

Print a quick operational summary:

```bash
python backend/scripts/summarize_dataset.py
```

The inspection utility reports:

- row count
- treatment/control split
- conversion rate
- segment counts
- borough counts

## Run Revised Phase 2 Model Preparation

Prepare deterministic train, validation, and test datasets for model training:

```bash
python backend/scripts/prepare_model_data.py
```

This saves:

- processed train split CSV
- processed validation split CSV
- processed test split CSV
- fitted preprocessing artifact
- preparation manifest JSON

Inspect the saved preparation manifest:

```bash
python backend/scripts/summarize_model_data.py
```

The revised Phase 2 preparation output includes:

- split sizes
- treatment and conversion rates by split
- raw feature count
- transformed feature count
- transformed feature name sample
- saved artifact paths

## Run Phase 3 Causal Analysis

Run the completed Phase 3 analysis on the generated dataset:

```bash
python backend/scripts/run_causal_analysis.py
```

This prints structured JSON for:

- conversion ATE
- bootstrap 95 percent confidence interval
- treated and control means
- absolute lift
- relative lift
- revenue lift analysis

## Run Revised Phase 3 XLearner Training

Train the first ML uplift model on the prepared dataset:

```bash
python backend/scripts/run_xlearner_conversion.py
```

This saves:

- trained XLearner conversion artifact
- training report JSON
- scored validation split CSV
- scored test split CSV

The revised Phase 3 XLearner output includes:

- feature count used for training
- train observed ATE baseline
- validation bootstrap ATE baseline
- mean predicted CATE on holdout splits
- top and bottom decile summaries
- top and bottom segments by mean predicted uplift

## Run Revised Phase 3 DRLearner Training

Train the next ML uplift model on the prepared dataset:

```bash
python backend/scripts/run_drlearner_conversion.py
```

This saves:

- trained DRLearner conversion artifact
- training report JSON
- scored validation split CSV
- scored test split CSV

The revised Phase 3 DRLearner output includes:

- feature count used for training
- train observed ATE baseline
- validation bootstrap ATE baseline
- mean predicted CATE on holdout splits
- top and bottom decile summaries
- top and bottom segments by mean predicted uplift

## Run Revised Phase 3 CausalForestDML Training

Train the next ML uplift model on the prepared dataset:

```bash
python backend/scripts/run_causal_forest_conversion.py
```

This saves:

- trained CausalForestDML conversion artifact
- training report JSON
- scored validation split CSV
- scored test split CSV

The revised Phase 3 CausalForestDML output includes:

- feature count used for training
- train observed ATE baseline
- validation bootstrap ATE baseline
- mean predicted CATE on holdout splits
- mean CATE interval lower and upper bounds
- mean interval width
- top and bottom decile summaries
- top and bottom segments by mean predicted uplift

## Run Revised Phase 3 DRLearner Revenue Training

Train the revenue uplift model on the prepared dataset:

```bash
python backend/scripts/run_drlearner_revenue.py
```

This saves:

- trained DRLearner revenue artifact
- training report JSON
- scored validation split CSV
- scored test split CSV

The revised Phase 3 DRLearner revenue output includes:

- feature count used for training
- train observed revenue ATE baseline
- validation bootstrap revenue ATE baseline
- mean predicted incremental revenue on holdout splits
- top and bottom decile summaries
- top and bottom segments by mean predicted revenue uplift

## Run Revised Phase 3 Model Comparison

Generate the Phase 3 comparison and selection report:

```bash
python backend/scripts/run_phase3_model_comparison.py
```

This saves:

- Phase 3 comparison report JSON

The revised Phase 3 comparison output includes:

- ranked conversion models on the holdout split
- ranked revenue models on the holdout split
- champion and challenger selection
- top-decile lift over the baseline
- bottom-decile behavior
- interval-awareness flags for models that expose uncertainty

This is the slice that closes revised Phase 3 and makes the current model winners explicit.

## Run Revised Phase 4 Model-Based Uplift Deciles

Generate the first revised Phase 4 uplift report using the selected Phase 3 champion:

```bash
python backend/scripts/run_model_based_uplift_deciles.py
```

This saves:

- Phase 4 decile summary JSON
- scored dataset view with uplift decile labels

The revised Phase 4 decile output includes:

- selected champion model name
- per-user scored view with `uplift_decile_rank`
- decile-by-decile observed uplift
- top and bottom decile comparison
- top persuadable deciles
- suppression-candidate deciles

This is the first model-based reporting slice for revised Phase 4.

## Run Revised Phase 4 Model-Based Rollups

Generate model-based cohort rollups using the selected Phase 3 champion:

```bash
python backend/scripts/run_model_based_rollups.py
```

This saves:

- Phase 4 rollup report JSON
- flattened rollup table CSV
- enriched scored view CSV

The revised Phase 4 rollup output includes:

- ranked segment rollups from model predictions
- ranked borough rollups from model predictions
- ranked device rollups from model predictions
- ranked channel rollups from model predictions
- top persuadable cohorts
- suppression candidates

This is the second model-based reporting slice for revised Phase 4.

## Run Revised Phase 4 Validation Summary

Generate the compact ranking-quality and validation summary:

```bash
python backend/scripts/run_phase4_validation_summary.py
```

This saves:

- Phase 4 validation summary JSON

The revised Phase 4 validation output includes:

- top-decile gain over the overall baseline
- uplift concentration ratio
- positive and negative decile counts
- monotonicity break count
- top persuadable deciles
- suppression deciles
- top persuadable cohorts
- suppression candidates
- one compact validation verdict

This slice closes revised Phase 4.

## Run Revised Phase 5 Model Targeting Decisions

Generate the first model-driven Phase 5 targeting report:

```bash
python backend/scripts/run_model_targeting_decisions.py
```

This saves:

- Phase 5 targeting report JSON
- target-user CSV
- suppress-user CSV

The revised Phase 5 targeting output includes:

- top target users from the strongest uplift zones
- top suppress users from weak or negative zones
- target cohorts from the model-based rollups
- suppress cohorts from the model-based rollups
- a compact human-readable action summary

This is the first revised Phase 5 ML decision slice.

## Run Revised Phase 5 Budget Allocation

Generate the segment-level budget allocation report:

```bash
python backend/scripts/run_budget_allocation.py
```

This saves:

- Phase 5 budget allocation report JSON
- segment budget allocation CSV

The revised Phase 5 budget output includes:

- prioritized segments with recommended budget shares
- zero-budget suppressed segments
- positive predicted revenue opportunity by segment
- conversion uplift context from the Phase 4 model-based rollups
- a compact human-readable budget summary

This is the second revised Phase 5 ML decision slice.

## Run Revised Phase 5 DRPolicyTree

Train the explainable conversion policy tree and score the holdout split:

```bash
python backend/scripts/run_drpolicytree_conversion.py
```

This saves:

- DRPolicyTree model artifact
- policy report JSON
- scored test decision CSV

The revised Phase 5 policy-tree output includes:

- recommended treat rate
- holdout policy value
- comparison versus always-treat and always-control
- top policy features
- leaf-level treat and control rules
- a compact human-readable policy summary

This is the third revised Phase 5 ML decision slice.

## Run Revised Phase 5 DRPolicyForest

Train the stronger policy challenger and compare it with the tree baseline:

```bash
python backend/scripts/run_drpolicyforest_conversion.py
```

This saves:

- DRPolicyForest model artifact
- policy-forest report JSON
- scored test decision CSV

The revised Phase 5 policy-forest output includes:

- recommended treat rate
- holdout policy value
- comparison versus always-treat and always-control
- comparison versus the saved DRPolicyTree report
- top policy features
- top treat and holdout segment mixes
- a compact human-readable policy summary

This is the fourth revised Phase 5 ML decision slice.

## Run Revised Phase 5 Decision Closeout

Generate the final consolidated Phase 5 recommendation report:

```bash
python backend/scripts/run_phase5_decision_closeout.py
```

This saves:

- final Phase 5 closeout report JSON
- final segment action CSV

The final Phase 5 closeout output includes:

- policy champion selection
- policy comparison against tree and naive baselines
- consolidated prioritized segment actions
- consolidated suppressed segment actions
- top target users and suppress users
- one final human-readable recommendation summary

This is the slice that closes revised Phase 5.

## Run Revised Phase 6 API Foundation

Start the FastAPI application locally:

```bash
uvicorn primelift.api.app:app --app-dir backend/src --reload
```

The first Phase 6 API slice currently exposes:

- `GET /health`

The health response includes:

- service status
- API version
- current phase
- UTC timestamp
- readiness flags for:
  - raw dataset
  - prepared data
  - Phase 5 closeout artifacts

This is the first revised Phase 6 API slice.

## Run Revised Phase 6 Dataset Generation Endpoint

Start the FastAPI app locally:

```bash
uvicorn primelift.api.app:app --app-dir backend/src --reload
```

Then call the dataset generation endpoint:

```bash
curl -X POST "http://127.0.0.1:8000/dataset/generate" \
  -H "Content-Type: application/json" \
  -d "{\"rows\": 100000, \"seed\": 42}"
```

The second Phase 6 API slice currently exposes:

- `POST /dataset/generate`

The dataset generation response includes:

- generation status
- saved output path
- seed used
- typed dataset summary:
  - row count
  - columns
  - treatment/control split
  - conversion rate
  - segment counts
  - borough counts

This is the second revised Phase 6 API slice.

## Run Revised Phase 6 Dataset Sample Endpoint

Start the FastAPI app locally:

```bash
uvicorn primelift.api.app:app --app-dir backend/src --reload
```

Then call the dataset sample endpoint:

```bash
curl "http://127.0.0.1:8000/dataset/sample?rows=10"
```

The third Phase 6 API slice currently exposes:

- `GET /dataset/sample`

The dataset sample response includes:

- request status
- source CSV path
- requested row count
- returned row count
- available total rows
- dataset columns
- preview records from the saved CSV

This is the third revised Phase 6 API slice.

## Run Revised Phase 6 ATE Analysis Endpoint

Start the FastAPI app locally:

```bash
uvicorn primelift.api.app:app --app-dir backend/src --reload
```

Then call the analysis endpoint:

```bash
curl "http://127.0.0.1:8000/analysis/ate?outcome=conversion&bootstrap_samples=300"
```

The fourth Phase 6 API slice currently exposes:

- `GET /analysis/ate`

The ATE analysis response includes:

- request status
- source CSV path
- dataset row count
- typed baseline result:
  - outcome column
  - treatment column
  - treated mean
  - control mean
  - ATE
  - absolute lift
  - relative lift
  - confidence interval bounds
  - confidence level
  - bootstrap sample count

This is the fourth revised Phase 6 API slice.

## Run Revised Phase 6 Model Comparison Endpoint

Start the FastAPI app locally:

```bash
uvicorn primelift.api.app:app --app-dir backend/src --reload
```

Then call the model comparison endpoint:

```bash
curl "http://127.0.0.1:8000/analysis/models"
```

The fifth Phase 6 API slice currently exposes:

- `GET /analysis/models`

The model comparison response includes:

- request status
- source comparison-report path
- report name
- comparison split
- conversion champion model name
- conversion challenger model name
- revenue champion model name
- full typed Phase 3 comparison report

This is the fifth revised Phase 6 API slice.

## Run Revised Phase 6 Segment Rollup Endpoint

Start the FastAPI app locally:

```bash
uvicorn primelift.api.app:app --app-dir backend/src --reload
```

Then call the segment analysis endpoint:

```bash
curl "http://127.0.0.1:8000/analysis/segments"
```

The sixth Phase 6 API slice currently exposes:

- `GET /analysis/segments`

The segment analysis response includes:

- request status
- rollup and validation report paths
- model name
- outcome column
- split name
- overall observed ATE
- validation verdict and reason
- top persuadable cohorts
- suppression candidates
- top persuadable and suppression deciles
- dimension summaries
- detailed per-dimension rollup reports

This is the sixth revised Phase 6 API slice.

## Run Revised Phase 6 Recommendations Endpoint

Start the FastAPI app locally:

```bash
uvicorn primelift.api.app:app --app-dir backend/src --reload
```

Then call the recommendations endpoint:

```bash
curl "http://127.0.0.1:8000/analysis/recommendations"
```

The seventh Phase 6 API slice currently exposes:

- `GET /analysis/recommendations`

The recommendations response includes:

- request status
- Phase 5 closeout report path
- policy champion model name and value
- whether the champion is an ML model
- final human-readable action summary
- counts for prioritized segments, suppressed segments, target users, and suppress users
- full typed Phase 5 closeout report

This is the seventh revised Phase 6 API slice.

## Run Phase 4 Segment Uplift Analysis

Run the grouped uplift analysis on the generated dataset:

```bash
python backend/scripts/run_segment_uplift_analysis.py
```

This prints structured JSON for uplift analysis grouped by:

- segment
- london_borough
- device_type
- channel

Each group includes:

- treated conversion rate
- control conversion rate
- uplift
- group size
- confidence indicator

## Run Phase 5 Decision Ranking

Run the first Phase 5 rule-based decision slice on the generated dataset:

```bash
python backend/scripts/run_decision_ranking.py
```

This currently ranks only the top positively responding segments and returns:

- ranked positive segments
- uplift and relative uplift
- treated and control conversion rates
- group size and arm counts
- confidence indicator
- explainable rationale per segment

## Run the Tests

```bash
pytest backend/tests -q
```

## Run Revised Phase 7 Overview Dashboard

Install frontend dependencies once:

```bash
cd frontend
npm install
```

Start the frontend locally:

```bash
cd frontend
npm run dev
```

Verify the first frontend slice:

```bash
cd frontend
npm run lint
npm run build
```

The first Phase 7 frontend slice currently includes:

- a branded PrimeLift overview dashboard
- KPI cards based on saved backend artifact values
- uplift, suppression, recommendation, and readiness sections
- static snapshot data only for now

Live API integration is intentionally deferred to Phase 8.

## Run Revised Phase 7 Uplift Insights Screen

Start the frontend locally:

```bash
cd frontend
npm run dev
```

Open the uplift route:

```text
http://127.0.0.1:3000/uplift-insights
```

Verify the code quality:

```bash
cd frontend
npm run lint
npm run build
```

The second Phase 7 frontend slice currently includes:

- a dedicated uplift insights route
- segment-level uplift bars from saved Phase 4 outputs
- decile view for model ranking quality
- positive responder and suppression panels
- a sorted segment table using saved artifact snapshot values

Live API integration remains deferred to Phase 8.

## Run Revised Phase 7 Recommendations Screen

Start the frontend locally:

```bash
cd frontend
npm run dev
```

Open the recommendations route:

```text
http://127.0.0.1:3000/recommendations
```

Verify the code quality:

```bash
cd frontend
npm run lint
npm run build
```

The third Phase 7 frontend slice currently includes:

- a dedicated recommendations route
- policy champion summary from the saved Phase 5 closeout
- segment budget allocation cards
- suppression plan panel
- target and suppress user lists

Live API integration remains deferred to Phase 8.

## Run Revised Phase 7 Dataset and Model Panel

Start the frontend locally:

```bash
cd frontend
npm run dev
```

Open the dataset/models route:

```text
http://127.0.0.1:3000/dataset-models
```

Verify the code quality:

```bash
cd frontend
npm run lint
npm run build
```

The fourth Phase 7 frontend slice currently includes:

- a dedicated dataset and model panel route
- dataset split summary and sample data preview
- schema-group summary for identifiers, features, treatment, and outcomes
- model registry panel
- training and scoring status panel

Live API integration remains deferred to Phase 8.

## Run Revised Phase 8 Live Overview Integration

Start the backend locally:

```bash
.venv\Scripts\python.exe -m uvicorn primelift.api.app:app --app-dir backend/src --host 127.0.0.1 --port 8000
```

Start the frontend locally:

```bash
cd frontend
copy .env.example .env.local
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open the overview route:

```text
http://127.0.0.1:3000/
```

Verify the code quality:

```bash
.venv\Scripts\python.exe -m pytest backend/tests/test_api_health.py -q
cd frontend
npm run lint
npm run build
```

The first revised Phase 8 integration slice currently includes:

- live overview fetches from the local FastAPI backend
- client-side source-state switching between:
  - connecting
  - live
  - fallback
- visible live status badge on the overview route
- browser-safe CORS support for the local frontend origin
- offline-safe font configuration for frontend builds

The recommendations and dataset/model routes still use saved snapshots and will be integrated in later Phase 8 slices.

## Run Revised Phase 8 Live Uplift Insights Integration

Start the backend locally:

```bash
.venv\Scripts\python.exe -m uvicorn primelift.api.app:app --app-dir backend/src --host 127.0.0.1 --port 8000
```

Start the frontend locally:

```bash
cd frontend
copy .env.example .env.local
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open the uplift route:

```text
http://127.0.0.1:3000/uplift-insights
```

Verify the code quality:

```bash
.venv\Scripts\python.exe -m pytest backend/tests/test_api_analysis_segments.py -q
cd frontend
npm run lint
npm run build
```

The second revised Phase 8 integration slice currently includes:

- live uplift insights fetches from the Phase 4 backend segment endpoint
- live decile table driven by the saved Phase 4 decile artifact
- live segment action table driven by the saved Phase 4 rollup artifact
- live positive responder and suppression cohort panels
- client-side source-state switching between:
  - connecting
  - live
  - fallback

The recommendations and dataset/model routes still use saved snapshots and will be integrated in later Phase 8 slices.

## Data Dictionary

Column definitions for the generated dataset live in:

- `docs/london_campaign_users_data_dictionary.md`

Detailed notes for the completed Phase 1 work live in:

- `docs/phase1_project_scaffolding_notes.md`

Detailed notes for the revised ML-first Phase 1 work live in:

- `docs/phase1_ml_ready_foundation_notes.md`

Detailed notes for the completed Phase 2 work live in:

- `docs/phase2_dataset_foundation_notes.md`

Detailed notes for the revised ML-first Phase 2 work live in:

- `docs/phase2_model_ready_dataset_notes.md`

Detailed notes for the completed Phase 3 work live in:

- `docs/phase3_causal_analysis_notes.md`

Detailed notes for the revised ML-first Phase 3 XLearner slice live in:

- `docs/phase3_xlearner_conversion_notes.md`

Detailed notes for the revised ML-first Phase 3 DRLearner slice live in:

- `docs/phase3_drlearner_conversion_notes.md`

Detailed notes for the revised ML-first Phase 3 CausalForestDML slice live in:

- `docs/phase3_causal_forest_conversion_notes.md`

Detailed notes for the revised ML-first Phase 3 DRLearner revenue slice live in:

- `docs/phase3_drlearner_revenue_notes.md`

Detailed notes for the revised ML-first Phase 3 comparison slice live in:

- `docs/phase3_model_comparison_notes.md`

Detailed notes for the revised ML-first Phase 4 decile slice live in:

- `docs/phase4_model_based_uplift_deciles_notes.md`

Detailed notes for the revised ML-first Phase 4 rollup slice live in:

- `docs/phase4_model_based_rollups_notes.md`

Detailed notes for the revised ML-first Phase 4 validation slice live in:

- `docs/phase4_validation_summary_notes.md`

Detailed notes for the revised ML-first Phase 5 targeting slice live in:

- `docs/phase5_model_targeting_notes.md`

Detailed notes for the revised ML-first Phase 5 budget allocation slice live in:

- `docs/phase5_budget_allocation_notes.md`

Detailed notes for the revised ML-first Phase 5 DRPolicyTree slice live in:

- `docs/phase5_drpolicytree_notes.md`

Detailed notes for the revised ML-first Phase 5 DRPolicyForest slice live in:

- `docs/phase5_drpolicyforest_notes.md`

Detailed notes for the revised ML-first Phase 5 closeout slice live in:

- `docs/phase5_decision_closeout_notes.md`

Detailed notes for the revised ML-first Phase 6 API foundation slice live in:

- `docs/phase6_api_foundation_notes.md`

Detailed notes for the revised ML-first Phase 6 dataset generation slice live in:

- `docs/phase6_dataset_generate_notes.md`

Detailed notes for the revised ML-first Phase 6 dataset sample slice live in:

- `docs/phase6_dataset_sample_notes.md`

Detailed notes for the revised ML-first Phase 6 ATE analysis slice live in:

- `docs/phase6_api_ate_notes.md`

Detailed notes for the revised ML-first Phase 6 model comparison slice live in:

- `docs/phase6_api_models_notes.md`

Detailed notes for the revised ML-first Phase 6 segment rollup slice live in:

- `docs/phase6_api_segments_notes.md`

Detailed notes for the revised ML-first Phase 6 recommendations slice live in:

- `docs/phase6_api_recommendations_notes.md`

Detailed notes for the revised ML-first Phase 7 overview slice live in:

- `docs/phase7_overview_dashboard_notes.md`

Detailed notes for the revised ML-first Phase 7 uplift insights slice live in:

- `docs/phase7_uplift_insights_notes.md`

Detailed notes for the revised ML-first Phase 7 recommendations slice live in:

- `docs/phase7_recommendations_screen_notes.md`

Detailed notes for the revised ML-first Phase 7 dataset and model panel slice live in:

- `docs/phase7_dataset_models_panel_notes.md`

Detailed notes for the revised ML-first Phase 8 live overview integration slice live in:

- `docs/phase8_live_overview_integration_notes.md`

Detailed notes for the revised ML-first Phase 8 live uplift insights integration slice live in:

- `docs/phase8_live_uplift_insights_notes.md`

Detailed notes for the completed Phase 4 work live in:

- `docs/phase4_segment_uplift_notes.md`
