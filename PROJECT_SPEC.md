You are helping me build a production-style portfolio project called PrimeLift AI.

PROJECT IDENTITY
PrimeLift AI is an ML-first causal decision engine for experimentation and growth. The system helps teams analyze campaign or experiment data, estimate true incremental lift, identify persuadable users or segments, recommend budget allocation, and surface insights through a modern web application.

CORE PROBLEM
Most businesses look at raw conversion or revenue increases and assume a campaign worked. That is not enough. We need to know:
1. Did the treatment actually cause the lift?
2. Which users or segments were influenced by the treatment?
3. Which users should receive treatment next?
4. Where should future budget go for maximum incremental impact?

PrimeLift AI solves this by combining:
- causal inference baselines
- causal ML uplift modeling
- ML-driven treatment policy learning
- budget decisioning
- interactive analytics UI
- optional agentic workflow layer later

PRIMARY GOAL
Build an end-to-end, local-first MVP that:
- generates or ingests campaign experiment data
- computes ATE with confidence intervals as a scientific baseline
- trains causal ML models for heterogeneous treatment effect estimation
- scores users with predicted incremental conversion and revenue lift
- identifies high-uplift segments and suppressible negative responders
- recommends budget allocation based on predicted incremental impact
- exposes results through a clean backend API
- displays outputs in a polished frontend dashboard

IMPORTANT BUILD STRATEGY
We are not starting with autonomous agents.
We are not stopping at rule-based analytics either.

Before building the API and frontend, the first five phases must become ML-ready and ML-driven.

Build order must be:
1. ML-ready scaffold and training foundation
2. dataset, features, and model-ready data contracts
3. causal ML analysis backend
4. model-based uplift analysis
5. ML decision engine
6. backend API
7. frontend dashboard
8. integration
9. testing and quality hardening
10. optional agent layer later

TECH STACK
Backend:
- Python 3.11+
- pandas
- numpy
- scipy
- scikit-learn
- statsmodels if useful
- lightgbm
- econml
- joblib
- FastAPI
- pydantic
- uvicorn
- pytest

Frontend:
- Next.js
- TypeScript
- Tailwind CSS
- clean reusable components
- charts for metrics and segments
- no unnecessary complexity

GENERAL ENGINEERING RULES
- Use modular src-layout Python package structure.
- Keep functions small and testable.
- Use typed Python where reasonable.
- Use pydantic schemas for contracts and structured outputs.
- Add docstrings and clear comments.
- Separate data, training, scoring, evaluation, and API logic.
- Do not hardcode magic values.
- Keep naming clean and consistent.
- Prefer realistic but lightweight MVP implementations.
- Build everything so it can run locally first.
- Each step should leave the repo in a runnable state.
- Keep scientific baselines in place even after ML models are added.
- Every completed phase must include proof-oriented notes and terminal-verifiable evidence.

MODEL STRATEGY
PrimeLift should use a layered causal ML stack for tabular marketing experiment data:

Baselines:
- Difference-in-means ATE
- Bootstrap confidence interval

CATE and uplift models:
- XLearner as the simple ML uplift baseline
- DRLearner as the main champion model
- CausalForestDML as the non-linear challenger

Policy and targeting models:
- DRPolicyTree as the explainable decision policy model
- DRPolicyForest as the stronger optional policy challenger

Base learners:
- LightGBMClassifier for binary propensity and conversion nuisance models
- LightGBMRegressor for continuous revenue nuisance models

Validation:
- uplift decile analysis
- Qini-style ranking analysis if feasible
- RScorer where appropriate
- DRTester where appropriate

PROJECT PHASES

PHASE 1: ML-READY FOUNDATION
Create a clean repo structure for a causal ML product.

Suggested structure:
primelift-ai/
  README.md
  requirements.txt
  .gitignore
  backend/
    scripts/
    src/
      primelift/
        __init__.py
        data/
        features/
        causal/
        uplift/
        decision/
        models/
        evaluation/
        api/
        utils/
    tests/
  data/
    raw/
    processed/
  artifacts/
    models/
    reports/
    metrics/
  docs/

Requirements:
- virtual environment-ready setup
- dependency list for causal ML stack
- feature-schema definitions for future training
- model registry or blueprint definitions
- artifact path helpers for saved models and reports
- script to verify the ML foundation from the terminal

PHASE 2: DATASET AND FEATURE FOUNDATION
We need a realistic synthetic marketing and experimentation dataset that is not only analytics-ready but model-ready.

Requirements:
- reproducible user-level London experiment dataset
- clear schema and data dictionary
- train, validation, and test splits
- feature lists for numeric, categorical, identifiers, treatment, and outcomes
- leakage-safe preprocessing pipeline
- saved processed feature datasets
- helper utilities to inspect split sizes and feature columns

PHASE 3: CAUSAL ML ANALYSIS CORE
Implement the scientific and modeling layer.

Features:
1. keep the ATE estimator and bootstrap CI baseline
2. train XLearner for uplift estimation
3. train DRLearner for heterogeneous treatment effects
4. train CausalForestDML as challenger
5. support both conversion uplift and revenue uplift workflows where feasible
6. save fitted model artifacts
7. return structured serializable outputs with model metadata

Outputs should include:
- baseline ATE metrics
- per-user CATE predictions
- model comparison summary
- saved artifacts and evaluation metrics

PHASE 4: MODEL-BASED UPLIFT ANALYSIS
Implement uplift analysis driven by model predictions instead of only grouped averages.

Features:
- per-user uplift scoring
- uplift deciles or ranking buckets
- segment-level rollups from model predictions
- borough, device, and channel rollups from model predictions

- top persuadable cohorts
- negative or low-value cohorts for suppression
- model validation summaries for ranking quality

Outputs should include:
- scored dataset views
- uplift summary tables
- ranked segment reports
- optional simple explanation outputs if practical

PHASE 5: ML DECISION ENGINE
Build the first ML-driven action layer that converts uplift predictions into targeting and budget actions.

Requirements:
- rank top positive-uplift users and segments
- suppress users or segments with negative predicted uplift
- allocate budget proportionally toward top positive predicted incremental impact
- support explainable rules via DRPolicyTree
- optionally compare against DRPolicyForest
- produce recommendation summaries such as:
  "Increase spend on High Intent Returners and Bargain Hunters; suppress Window Shoppers."

Keep this version practical and explainable.
Avoid premature enterprise optimization layers.

PHASE 6: BACKEND API
Build a FastAPI backend exposing endpoints like:
- POST /dataset/generate
- GET /dataset/sample
- GET /analysis/ate
- GET /analysis/models
- GET /analysis/segments
- GET /analysis/recommendations
- GET /health

All endpoints should return typed JSON responses using pydantic models.

PHASE 7: FRONTEND UI
Build a modern analytics dashboard.

Main screens and components:
1. Overview dashboard
   - headline KPIs
   - baseline ATE card
   - champion model card
   - top uplift segment card
   - budget recommendation card

2. Uplift insights
   - uplift by segment chart
   - uplift decile view
   - sortable scored segment table
   - positive and negative responder panels

3. Recommendations panel
   - human-readable action summary
   - suggested budget allocation
   - highlighted target and suppress lists

4. Dataset and model panel
   - dataset upload or generate button
   - sample data preview
   - schema summary
   - model registry summary
   - training and scoring status

5. Agent-style query panel later
   - reserve space for future conversational assistant
   - do not implement full agent functionality yet unless asked

UI REQUIREMENTS
- premium feel
- clean grid layout
- strong information hierarchy
- readable charts and tables
- should look like a real analytics SaaS product

PHASE 8: INTEGRATION
Connect frontend to backend APIs.

Requirements:
- dashboard fetches live baseline and model metrics
- uplift tables and charts use backend model outputs
- recommendation panel reflects backend policy and budget outputs
- dataset generation action triggers backend generation
- model training and scoring flows are wired cleanly
- basic loading and error states

PHASE 9: TESTING AND QUALITY
Add tests for:
- data generation shape and schema
- feature pipeline correctness
- deterministic ATE toy cases
- model training smoke tests
- scoring output shape and types
- segment uplift logic
- recommendation logic
- artifact creation

PHASE 10: FUTURE EXTENSIONS
Structure the code so the following can be added later:
- richer CATE estimators
- hyperparameter tuning
- calibration workflows
- budget optimization solver
- report generation
- conversational assistant or orchestration layer
- scheduled experiment reports

IMPORTANT EXECUTION STYLE
Work incrementally.
Do not implement everything at once.
At each task:
- explain what files are being created or changed
- implement only the current slice
- keep code runnable
- avoid speculative overengineering
- provide notes and proof of what was built
- ask before moving to the next phase

CURRENT PRIORITY
First deliverable in the revised roadmap should be:
- ML-ready scaffold
- causal ML dependency plan
- feature-schema definitions
- model registry definitions
- artifact directories and helpers
- terminal-verifiable setup instructions

When in doubt, choose simplicity, correctness, reproducibility, and clear ML structure over cleverness.
