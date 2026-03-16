# Revised Phase 5 Model Targeting Notes

This document explains what was implemented for the first revised Phase 5 slice, what files were added or updated, and what terminal output you should expect when you generate the model-driven targeting report yourself.

## Phase 5 Scope for This Slice

This first revised Phase 5 slice converts the Phase 4 model outputs into concrete targeting and suppression actions.

It does the following:

1. load the Phase 4 validation summary
2. load the Phase 4 rollup report
3. load the Phase 4 scored user view
4. rank top users from the strongest uplift zones
5. rank suppress users from the weakest zones
6. rank target and suppress cohorts
7. produce a compact human-readable action summary

This slice covers:

- rank top positive-uplift users
- suppress users with weak or negative predicted uplift
- rank positive-uplift cohorts
- suppress negative cohorts

It does **not** yet implement:

- budget allocation
- DRPolicyTree
- DRPolicyForest
- the final full Phase 5 decision engine

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/decision/__init__.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/decision/model_targeting.py`
- `backend/scripts/run_model_targeting_decisions.py`
- `backend/tests/test_model_targeting.py`

Generated locally by this slice:

- `artifacts/metrics/phase5_targeting_recommendation_report.json`
- `artifacts/reports/phase5_target_users.csv`
- `artifacts/reports/phase5_suppress_users.csv`

## What Was Implemented

### 1. Model-driven user targeting and suppression

Implemented in:

- `backend/src/primelift/decision/model_targeting.py`

This slice starts from the Phase 4 outputs rather than grouped averages. It uses:

- top persuadable deciles from the Phase 4 validation summary
- suppression deciles from the Phase 4 validation summary
- model-based cohort rollups from the Phase 4 rollup report

The current decision path is therefore driven by the selected champion model rather than by raw conversion differences alone.

### 2. User-level action lists

The report now creates:

- a target-user list
- a suppress-user list

Each user recommendation includes:

- `user_id`
- predicted effect
- uplift decile rank
- segment
- borough
- device type
- channel
- a short rationale string

### 3. Cohort-level action lists

The report also creates:

- target cohorts
- suppress cohorts

Each cohort recommendation includes:

- group column
- group value
- mean predicted effect
- observed ATE
- recommendation label
- a short rationale string

### 4. Human-readable action summary

The report finishes with one short action summary that can be surfaced later in the API or UI.

## Important Scope Note

This is the first revised Phase 5 slice.

It proves the repository can now turn model outputs into:

- user-level target lists
- user-level suppress lists
- cohort-level target lists
- cohort-level suppression lists

It does **not** mean revised Phase 5 is fully complete.

The next logical Phase 5 slice should be:

- budget allocation driven by predicted incremental impact

After that, the explainable policy layer with `DRPolicyTree` is the next serious step.

## How to Verify Revised Phase 5 Targeting Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Generate the targeting report:

```powershell
python backend/scripts/run_model_targeting_decisions.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_model_targeting.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_model_targeting_decisions.py
```

```json
{
  "report_name": "phase5_model_targeting_recommendations",
  "outcome_column": "conversion",
  "split_name": "test",
  "model_name": "drlearner_conversion",
  "target_user_count": 25,
  "suppress_user_count": 25,
  "target_cohort_count": 10,
  "suppress_cohort_count": 10,
  "action_summary": "Increase treatment on Hackney, Merton, High Intent Returners; suppress or deprioritize Sutton, Kingston upon Thames, Kensington and Chelsea."
}
```

Additional output highlights from the same run:

```json
{
  "top_target_users": [
    {
      "user_id": "LON-065845",
      "predicted_effect": 0.4288236903519877,
      "segment": "High Intent Returners",
      "london_borough": "Hackney"
    },
    {
      "user_id": "LON-049529",
      "predicted_effect": 0.4201406432691466,
      "segment": "High Intent Returners",
      "london_borough": "Merton"
    }
  ],
  "top_suppress_users": [
    {
      "user_id": "LON-038770",
      "predicted_effect": -0.265199348886887,
      "segment": "High Intent Returners",
      "london_borough": "Islington"
    },
    {
      "user_id": "LON-056125",
      "predicted_effect": -0.2268177845945407,
      "segment": "High Intent Returners",
      "london_borough": "Tower Hamlets"
    }
  ],
  "target_cohorts": [
    "Hackney",
    "Merton",
    "High Intent Returners",
    "Bargain Hunters",
    "generic_search"
  ],
  "suppress_cohorts": [
    "Sutton",
    "Kingston upon Thames",
    "Kensington and Chelsea",
    "Camden",
    "Redbridge"
  ]
}
```

## What That Output Means

- The current model-driven decision layer is using the Phase 4 conversion champion:
  - `drlearner_conversion`
- It can now surface specific users for treatment and specific users for suppression.
- It can also surface broader cohort actions that are easier to apply operationally.

One important nuance is visible in the output:

- some suppressed users still belong to globally strong segments like `High Intent Returners`

That is not a bug. It is exactly the point of moving from group averages to model-based user-level decisioning. A strong segment can still contain specific users with weak or negative predicted effect.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_model_targeting.py -q
```

Current output:

```text
..                                                                       [100%]
2 passed in 5.62s
```

Full backend test output after this slice:

```text
......................................................                   [100%]
54 passed in 19.46s
```

## Where to Inspect the Code

- targeting module: `backend/src/primelift/decision/model_targeting.py`
- targeting CLI: `backend/scripts/run_model_targeting_decisions.py`
- focused tests: `backend/tests/test_model_targeting.py`

## Short Conclusion

This first revised Phase 5 slice is complete because the repository now has:

- model-driven target-user recommendations
- model-driven suppress-user recommendations
- cohort-level target and suppress recommendations
- human-readable action summary output
- terminal-verifiable artifacts
- passing automated tests

The next Phase 5 slice should be budget allocation.
