You are helping me build a production-style portfolio project called PrimeLift AI.

PROJECT IDENTITY
PrimeLift AI is an agentic causal decision engine for experimentation and growth. The system helps teams analyse campaign or experiment data, estimate true incremental lift, identify persuadable users or segments, recommend budget allocation, and surface insights through a modern web application.

CORE PROBLEM
Most businesses look at raw conversion or revenue increases and assume a campaign worked. But that is not enough. We need to know:
1. Did the treatment actually cause the lift?
2. Which users or segments were influenced by the treatment?
3. Where should future budget go for maximum incremental impact?

PrimeLift AI solves this by combining:
- causal inference
- uplift modelling
- budget decisioning
- interactive analytics UI
- optional agentic workflow layer later

PRIMARY GOAL
Build an end-to-end, local-first MVP that:
- generates or ingests campaign experiment data
- computes ATE with confidence intervals
- performs segment-level uplift analysis
- identifies high-uplift segments
- recommends budget allocation based on incremental impact
- exposes results through a clean backend API
- displays outputs in a polished frontend dashboard

IMPORTANT BUILD STRATEGY
We are NOT starting with autonomous agents.
We are starting with a strong scientific product core first.

Build order must be:
1. dataset and data contracts
2. core causal analysis backend
3. uplift and decision modules
4. API layer
5. frontend dashboard
6. integration
7. optional agent layer later

TECH STACK
Backend:
- Python 3.11+
- pandas
- numpy
- scipy
- scikit-learn
- statsmodels if useful
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
- Use modular src-layout Python package structure
- Keep functions small and testable
- Use typed Python where reasonable
- Use pydantic schemas for API contracts
- Add docstrings and clear comments
- Separate business logic from API layer
- Do not hardcode magic values
- Keep naming clean and consistent
- Prefer realistic but lightweight MVP implementations
- Build everything so it can run locally first
- Each step should leave the repo in a runnable state

PROJECT PHASES

PHASE 1: PROJECT SCAFFOLDING
Create a clean repo structure for an end-to-end data product.

Suggested structure:
primelift-ai/
  README.md
  requirements.txt
  .gitignore
  backend/
    src/
      primelift/
        __init__.py
        data/
        causal/
        uplift/
        decision/
        api/
        utils/
    tests/
  frontend/
    app or src/
  data/
    raw/
    processed/
  notebooks/
  docs/

Set up a Python virtual environment-ready backend and a separate frontend app.

PHASE 2: DATASET FOUNDATION
We need a realistic synthetic marketing/experimentation dataset for MVP development.

Create a data generation module that simulates user-level campaign experiment data with fields like:
- user_id
- treatment
- conversion
- revenue
- segment
- age_band
- geography
- device_type
- prior_engagement_score
- prior_purchases
- channel
- campaign_id

Requirements:
- binary treatment assignment
- realistic baseline conversion probabilities
- uplift should vary by segment
- some segments should respond positively
- some weakly
- some negatively
- revenue should exist for converted users
- dataset should be reproducible using a random seed
- save generated CSV to data/raw/

Also define a data dictionary and expected schema.

PHASE 3: CAUSAL ANALYSIS CORE
Implement the first scientific layer.

Features:
1. ATE estimator
   - difference in means between treated and control
2. bootstrap confidence interval
   - 95 percent CI
3. summary statistics
   - treated conversion rate
   - control conversion rate
   - absolute lift
   - relative lift if useful
4. revenue lift version if possible

Output should be structured and serialisable.

PHASE 4: SEGMENT-LEVEL UPLIFT ANALYSIS
Implement grouped analysis by important dimensions such as:
- segment
- geography
- device_type
- channel

For each group compute:
- treated conversion rate
- control conversion rate
- uplift
- group size
- confidence indicator if possible

Return sorted segment-level results by uplift descending.

PHASE 5: DECISION ENGINE MVP
Build a simple decision layer that converts analysis into actions.

Initial rules:
- rank top segments by positive uplift
- suppress segments with negative uplift
- allocate budget proportionally toward top positive incremental segments
- produce recommendation summary such as:
  “Increase spend on Young Professionals and Retargeted Users; reduce spend on Existing Subscribers”

Keep this first version rule-based and explainable.
Do not jump into advanced optimisation too early.

PHASE 6: BACKEND API
Build a FastAPI backend exposing endpoints like:
- POST /dataset/generate
- GET /dataset/sample
- GET /analysis/ate
- GET /analysis/segments
- GET /analysis/recommendations
- GET /health

All endpoints should return typed JSON responses using pydantic models.

PHASE 7: FRONTEND UI
Build a modern dark-mode analytics dashboard.

Main screens/components:
1. Overview dashboard
   - headline KPIs
   - ATE card
   - confidence interval card
   - top segment card
   - budget recommendation card

2. Segment insights
   - uplift by segment chart
   - sortable table
   - positive and negative responders

3. Recommendations panel
   - human-readable action summary
   - suggested budget allocation
   - highlighted target segments

4. Dataset panel
   - dataset upload or generate button
   - sample data preview
   - schema summary

5. Agent-style query panel later
   - reserve space for future conversational assistant
   - do not implement full agent functionality yet unless asked

UI REQUIREMENTS
- dark mode, premium feel
- black, deep navy, cyan accents
- clean grid layout
- sticky top navigation
- no clutter
- good spacing and hierarchy
- charts should be readable
- cards should look like a real SaaS analytics product

PHASE 8: INTEGRATION
Connect frontend to backend APIs.

Requirements:
- dashboard fetches current metrics from API
- segment chart uses live backend output
- recommendations panel reflects backend decision engine
- dataset generation action triggers backend generation
- basic loading and error states

PHASE 9: TESTING AND QUALITY
Add tests for:
- data generation shape and schema
- ATE correctness on deterministic toy cases
- bootstrap output format
- segment analysis logic
- recommendation logic

PHASE 10: FUTURE EXTENSIONS
Structure the code so the following can be added later:
- CATE estimation
- causal forest or meta-learners
- uplift modelling
- budget optimisation solver
- report generation
- conversational assistant or OpenClaw-based orchestration
- scheduled experiment reports

IMPORTANT EXECUTION STYLE
Work incrementally.
Do not implement everything at once.
At each task:
- explain what files are being created or changed
- implement only the current slice
- keep code runnable
- avoid speculative overengineering

CURRENT PRIORITY
Start with the backend scientific core before frontend polish.
First deliverable should be:
- repo scaffold
- synthetic dataset generator
- data schema
- saved CSV output
- README instructions to run locally

When in doubt, choose simplicity, correctness, and modularity over cleverness.