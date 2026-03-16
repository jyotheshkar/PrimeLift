# Revised Phase 4 Model-Based Rollups Notes

This document explains what was implemented for the second revised Phase 4 slice, what files were added or updated, and what terminal output you should expect when you generate the model-based rollup report yourself.

## Phase 4 Scope for This Slice

This slice extends the first model-based decile report into business-facing cohort rollups.

It does the following:

1. resolve the selected Phase 3 champion
2. load the champion's saved scored holdout output
3. enrich the scored output with business dimensions from the raw dataset
4. roll up predicted effects by business dimension
5. compute observed effect by rolled-up cohort
6. rank top persuadable cohorts and suppression candidates

This slice covers:

- segment-level rollups from model predictions
- borough rollups from model predictions
- device rollups from model predictions
- channel rollups from model predictions
- top persuadable cohorts
- negative or low-value cohorts for suppression

It does **not** yet implement:

- richer ranking-quality summaries beyond the decile slice
- simple explanation outputs for why a cohort is ranked where it is

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/evaluation/registry.py`
- `backend/src/primelift/uplift/__init__.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/uplift/model_based_rollups.py`
- `backend/scripts/run_model_based_rollups.py`
- `backend/tests/test_model_based_rollups.py`

Generated locally by this slice:

- `artifacts/metrics/phase4_conversion_rollup_report.json`
- `artifacts/reports/phase4_conversion_rollup_table.csv`
- `artifacts/reports/phase4_conversion_enriched_scored_view.csv`

## What Was Implemented

### 1. Champion-driven business rollups

Implemented in:

- `backend/src/primelift/uplift/model_based_rollups.py`

The rollup layer starts from the Phase 3 comparison report and resolves the current champion for the selected outcome.

For the current repository state, the selected conversion champion is:

- `drlearner_conversion`

### 2. Enriched scored view

The saved Phase 3 scored output does not contain every business dimension needed for Phase 4. In particular, `device_type` and `channel` are not present in the champion score file.

This slice fixes that by merging the scored output back to the raw dataset using:

- `user_id`

The enriched view preserves the model score and adds the missing business columns required for rollups.

### 3. Dimension rollups

Each dimension result includes:

- group size
- treated and control counts
- mean, median, min, and max predicted effect
- share of positive model scores
- observed ATE inside the cohort
- gain over the overall holdout ATE
- a simple practical label:
  - `prioritize`
  - `suppress`
  - `monitor`
  - `watch`

The default dimensions are:

- `segment`
- `london_borough`
- `device_type`
- `channel`

### 4. Top persuadable and suppression summaries

The report also extracts:

- top persuadable cohorts across all dimensions
- suppression candidates across all dimensions

Those summary lists make the rollups immediately usable for downstream decisioning work in Phase 5.

## Important Scope Note

This slice is the second revised Phase 4 model-based report.

It proves the selected ML model can now be translated into ranked business cohorts, not only per-user buckets.

It does **not** mean revised Phase 4 is fully complete.

The next logical slice in revised Phase 4 should be:

- a compact ranking-quality / validation summary layer that ties the decile and rollup outputs together

## How to Verify Revised Phase 4 Rollup Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Generate the rollup report:

```powershell
python backend/scripts/run_model_based_rollups.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_model_based_rollups.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_model_based_rollups.py
```

```json
{
  "report_name": "phase4_model_based_group_rollups",
  "outcome_column": "conversion",
  "split_name": "test",
  "model_name": "drlearner_conversion",
  "overall_observed_ate": 0.009976772207203513,
  "top_persuadable_cohorts": [
    {
      "group_column": "london_borough",
      "group_value": "Hackney",
      "mean_predicted_effect": 0.02618869958621298,
      "observed_ate": 0.016325779483674224
    },
    {
      "group_column": "london_borough",
      "group_value": "Merton",
      "mean_predicted_effect": 0.025689320177933177,
      "observed_ate": 0.043004923883091656
    },
    {
      "group_column": "segment",
      "group_value": "High Intent Returners",
      "mean_predicted_effect": 0.022910596398893156,
      "observed_ate": 0.02433115230825153
    },
    {
      "group_column": "segment",
      "group_value": "Bargain Hunters",
      "mean_predicted_effect": 0.015572269886188272,
      "observed_ate": 0.023196564839146845
    },
    {
      "group_column": "channel",
      "group_value": "generic_search",
      "mean_predicted_effect": 0.01525901183422402,
      "observed_ate": 0.035392443830121675
    }
  ],
  "suppression_candidates": [
    {
      "group_column": "segment",
      "group_value": "Lapsed Users",
      "mean_predicted_effect": 0.00020662727422083546,
      "observed_ate": -0.008005408097915038
    },
    {
      "group_column": "channel",
      "group_value": "app_entry",
      "mean_predicted_effect": 0.005190320437812259,
      "observed_ate": -0.02393372677867922
    },
    {
      "group_column": "london_borough",
      "group_value": "Camden",
      "mean_predicted_effect": 0.007428894805142698,
      "observed_ate": -0.029281094760521126
    }
  ]
}
```

Additional dimension highlights from the same output:

```json
{
  "segment_top_positive_groups": [
    "High Intent Returners",
    "Bargain Hunters",
    "Young Professionals"
  ],
  "segment_suppression_candidates": [
    "Lapsed Users"
  ],
  "channel_top_positive_groups": [
    "generic_search",
    "affiliate_content",
    "brand_navigation"
  ],
  "channel_suppression_candidates": [
    "seo_content",
    "retargeting_display",
    "seo_brand"
  ]
}
```

## What That Output Means

- The model-driven cohort ranking now extends beyond deciles into business dimensions that a marketer can act on.
- The current strongest segment-level positive cohorts include:
  - `High Intent Returners`
  - `Bargain Hunters`
  - `Young Professionals`
- The current strongest channel-level positive cohort is:
  - `generic_search`
- The current clearest segment-level suppression cohort is:
  - `Lapsed Users`

One useful nuance this slice exposes is that some cohorts have mildly positive average model scores but still negative observed effect on holdout. That is exactly why this rollup layer includes both:

- mean predicted effect
- observed ATE

That prevents the system from acting on scores alone without checking real holdout behavior.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_model_based_rollups.py -q
```

Current output:

```text
..                                                                       [100%]
2 passed in 5.94s
```

Full backend test output after this slice:

```text
..................................................                       [100%]
50 passed in 19.56s
```

## Where to Inspect the Code

- rollup module: `backend/src/primelift/uplift/model_based_rollups.py`
- rollup CLI: `backend/scripts/run_model_based_rollups.py`
- focused tests: `backend/tests/test_model_based_rollups.py`

## Short Conclusion

This second revised Phase 4 slice is complete because the repository now has:

- model-based rollups across the key business dimensions
- enriched scored outputs with the missing business fields restored
- ranked persuadable cohorts
- ranked suppression candidates
- terminal-verifiable output
- passing automated tests

The next slice should consolidate Phase 4 validation and ranking-quality summaries.
