# Revised Phase 4 Model-Based Uplift Deciles Notes

This document explains what was implemented for the first revised Phase 4 slice, what files were added or updated, and what terminal output you should expect when you generate the model-based uplift decile report yourself.

## Phase 4 Scope for This Slice

Revised Phase 4 is model-based, not only grouped-average based.

This first slice implements:

1. select the current Phase 3 champion model
2. load its saved scored holdout output
3. bucket users into uplift deciles
4. save an enhanced scored dataset view
5. compute observed uplift by decile
6. identify the strongest and weakest deciles

This slice covers:

- `per-user uplift scoring` via the saved Phase 3 scores
- `uplift deciles or ranking buckets`
- `scored dataset views`
- a first `ranking quality` summary

It does **not** yet implement:

- segment-level model-based rollups
- borough, device, and channel rollups from model predictions
- top persuadable cohort summaries by business dimension
- suppression recommendations by segment

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/evaluation/registry.py`
- `backend/src/primelift/uplift/__init__.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/uplift/model_based_analysis.py`
- `backend/scripts/run_model_based_uplift_deciles.py`
- `backend/tests/test_model_based_uplift.py`

Generated locally by this slice:

- `artifacts/metrics/phase4_conversion_decile_report.json`
- `artifacts/reports/phase4_conversion_scored_view.csv`

## What Was Implemented

### 1. Champion-based decile analysis

Implemented in:

- `backend/src/primelift/uplift/model_based_analysis.py`

The report starts from the saved Phase 3 comparison report, resolves the current champion for the chosen outcome, and reads that model's saved scored holdout CSV.

On the current repository state, the selected conversion champion is:

- `drlearner_conversion`

### 2. Per-user scored view with decile labels

The scored view now includes:

- the original Phase 3 model score column
- `uplift_decile_rank`
- `uplift_decile_label`

The deciles are descending:

- `1` is the highest predicted uplift bucket
- `10` is the lowest predicted uplift bucket

### 3. Decile validation summary

Each decile summary includes:

- row count
- min, mean, and max predicted score
- treated and control counts
- treated and control observed outcome means
- observed ATE within the decile
- gain over the overall holdout ATE

The report also includes:

- top-decile observed uplift
- bottom-decile observed uplift
- top-vs-bottom observed gap
- top persuadable deciles
- suppression-candidate deciles

## Important Scope Note

This slice is the first revised Phase 4 model-based report.

It proves the selected ML model can be turned into:

- a scored dataset view
- ranking buckets
- observed uplift validation by bucket

It does **not** mean revised Phase 4 is fully complete.

The next logical slice in revised Phase 4 should be:

- segment, borough, device, and channel rollups based on model predictions

## How to Verify Revised Phase 4 Decile Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Generate the report:

```powershell
python backend/scripts/run_model_based_uplift_deciles.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_model_based_uplift.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_model_based_uplift_deciles.py
```

```json
{
  "report_name": "phase4_model_based_uplift_deciles",
  "outcome_column": "conversion",
  "split_name": "test",
  "model_name": "drlearner_conversion",
  "score_column": "predicted_cate_drlearner_conversion",
  "overall_observed_ate": 0.009976772207203513,
  "top_decile_observed_ate": 0.036735419630156474,
  "bottom_decile_observed_ate": 0.011345797948085268,
  "observed_top_bottom_gap": 0.025389621682071206,
  "top_persuadable_deciles": [
    2,
    1,
    3
  ],
  "suppression_candidate_deciles": [
    5,
    9
  ]
}
```

Additional bucket highlights from the same output:

```json
{
  "decile_1": {
    "mean_score": 0.06722212842209359,
    "observed_ate": 0.036735419630156474
  },
  "decile_2": {
    "mean_score": 0.025965124420987744,
    "observed_ate": 0.04018492176386912
  },
  "decile_5": {
    "mean_score": 0.009984419349683802,
    "observed_ate": -0.009857419468403447
  },
  "decile_9": {
    "mean_score": -0.0020660342903854384,
    "observed_ate": -0.00504022400995599
  }
}
```

## What That Output Means

- The Phase 3 conversion champion is now being used as the driver for Phase 4.
- The strongest observed lift is concentrated near the top of the ranking:
  - decile `1` observed uplift: `0.036735419630156474`
  - decile `2` observed uplift: `0.04018492176386912`
- Some middle/lower buckets are now clearly weak or negative:
  - decile `5` observed uplift: `-0.009857419468403447`
  - decile `9` observed uplift: `-0.00504022400995599`

That is the main proof this slice needed to establish: the model ranking is useful enough to separate stronger and weaker treatment-response zones within the holdout data.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_model_based_uplift.py -q
```

Current output:

```text
..                                                                       [100%]
2 passed in 6.03s
```

Full backend test output after this slice:

```text
................................................                         [100%]
48 passed in 19.37s
```

## Where to Inspect the Code

- model-based uplift module: `backend/src/primelift/uplift/model_based_analysis.py`
- Phase 4 CLI: `backend/scripts/run_model_based_uplift_deciles.py`
- focused tests: `backend/tests/test_model_based_uplift.py`

## Short Conclusion

This first revised Phase 4 slice is complete because the repository now has:

- a model-based uplift decile report
- a saved per-user scored view with ranking buckets
- observed uplift validation by bucket
- terminal-verifiable output
- passing automated tests

The next slice should add model-based rollups by segment and other business dimensions.
