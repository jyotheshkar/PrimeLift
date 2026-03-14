# Phase 3 Causal Analysis Notes

This document explains what was implemented for Phase 3, what it does to the dataset, and what terminal output you should see when you run the analysis yourself.

## Phase 3 Scope

Phase 3 from `PROJECT_SPEC.md` required:

1. ATE estimator
2. Bootstrap confidence interval
3. Summary statistics
4. Revenue lift version

All four items are implemented.

## Files Added or Updated

- `backend/src/primelift/causal/ate.py`
- `backend/src/primelift/causal/__init__.py`
- `backend/scripts/run_causal_analysis.py`
- `backend/tests/test_ate.py`

## What Was Implemented

### 1. ATE estimator

Implemented in `estimate_average_treatment_effect(...)`.

What it computes:

- treated mean
- control mean
- `ate = treated_mean - control_mean`
- absolute lift
- relative lift

This works on `conversion` by default and can also be used on any numeric outcome column such as `revenue`.

### 2. Bootstrap confidence interval

Implemented in `bootstrap_ate_confidence_interval(...)`.

What it does:

- resamples treated users with replacement
- resamples control users with replacement
- recomputes ATE repeatedly
- returns a percentile-based confidence interval

The current command-line script defaults to a 95% confidence interval.

### 3. Summary statistics

Implemented as part of the ATE result model.

Included fields:

- `treated_mean`
- `control_mean`
- `ate`
- `absolute_lift`
- `relative_lift`

### 4. Revenue lift version

Implemented in `estimate_revenue_lift(...)`.

It uses the same Phase 3 pipeline, but runs it on the `revenue` column instead of `conversion`.

## Important Data Impact Note

Phase 3 does **not** change the CSV dataset itself.

It does not rewrite rows, add columns, or alter values inside:

- `data/raw/london_campaign_users_100k.csv`

Instead, it reads the existing dataset and produces **derived analysis outputs** in the terminal:

- conversion treatment effect
- revenue treatment effect
- confidence intervals
- summary metrics

So the correct statement is:

- Phase 2 created the dataset
- Phase 3 analyzes the dataset

## How to Run Phase 3

Activate the environment first:

```powershell
.venv\Scripts\Activate
```

Then run:

```powershell
python backend/scripts/run_causal_analysis.py --bootstrap-samples 300
```

## Terminal Proof: Actual Output

This is the current output from the repository on the generated London 100k dataset:

```json
{
  "conversion_analysis": {
    "outcome_column": "conversion",
    "treatment_column": "treatment",
    "treated_mean": 0.1228565705128205,
    "control_mean": 0.11267971246006389,
    "ate": 0.010176858052756615,
    "absolute_lift": 0.010176858052756615,
    "relative_lift": 0.09031668461493024,
    "ci_lower": 0.00599163133857622,
    "ci_upper": 0.014183745110387478,
    "confidence_level": 0.95,
    "bootstrap_samples": 300
  },
  "revenue_analysis": {
    "outcome_column": "revenue",
    "treatment_column": "treatment",
    "treated_mean": 17.21526923076923,
    "control_mean": 16.23476876996805,
    "ate": 0.9805004608011814,
    "absolute_lift": 0.9805004608011814,
    "relative_lift": 0.06039509861175011,
    "ci_lower": 0.40538064700645676,
    "ci_upper": 1.6590004625771817,
    "confidence_level": 0.95,
    "bootstrap_samples": 300
  }
}
```

## What That Output Means

### Conversion analysis

- Treated conversion rate: `0.1228565705128205`
- Control conversion rate: `0.11267971246006389`
- ATE: `0.010176858052756615`

Interpretation:

- The treated group converted about `1.02 percentage points` higher than control.

Relative lift:

- `0.09031668461493024`

Interpretation:

- That is about `9.03%` lift relative to the control conversion rate.

Bootstrap interval:

- lower bound: `0.00599163133857622`
- upper bound: `0.014183745110387478`

### Revenue analysis

- Treated revenue mean: `17.21526923076923`
- Control revenue mean: `16.23476876996805`
- Revenue ATE: `0.9805004608011814`

Interpretation:

- The treated group produced about `0.98` more revenue units per user on average than control on this synthetic dataset.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_ate.py -q
```

Current output:

```text
.........                                                                [100%]
9 passed in 1.18s
```

## What Those Tests Cover

The Phase 3 tests validate:

- deterministic ATE correctness on toy data
- custom numeric outcomes
- bootstrap output structure
- full combined analysis output
- revenue lift output
- rejection of non-binary treatment values
- rejection of missing treated or control groups
- rejection of invalid bootstrap parameters
- handling of zero control mean for relative lift

## Where to Inspect the Code

- Core implementation: `backend/src/primelift/causal/ate.py`
- Runnable analysis script: `backend/scripts/run_causal_analysis.py`
- Phase 3 tests: `backend/tests/test_ate.py`

## Short Conclusion

Phase 3 is complete because the repository now has:

- point estimate ATE
- summary statistics
- bootstrap confidence intervals
- revenue lift analysis
- runnable CLI output
- passing automated tests
