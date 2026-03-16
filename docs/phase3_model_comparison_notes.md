# Revised Phase 3 Model Comparison Notes

This document explains what was implemented for the revised Phase 3 comparison slice, what files were added or updated, and what terminal output you should expect when you generate the comparison report yourself.

## Phase 3 Scope for This Slice

This slice closes revised Phase 3 by comparing the trained model outputs directly on holdout data.

It does the following:

1. load the saved Phase 3 model reports
2. normalize the test-split metrics into one comparison contract
3. rank conversion models by real holdout performance
4. rank revenue models by real holdout performance
5. select the current champion and challenger
6. save a structured comparison report

This slice covers:

- `XLearner` conversion
- `DRLearner` conversion
- `CausalForestDML` conversion
- `DRLearner` revenue

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/evaluation/__init__.py`
- `backend/src/primelift/evaluation/registry.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/evaluation/model_comparison.py`
- `backend/scripts/run_phase3_model_comparison.py`
- `backend/tests/test_model_comparison.py`

Generated locally by this slice:

- `artifacts/metrics/phase3_model_comparison_report.json`

## What Was Implemented

### 1. Phase 3 comparison report

Implemented in:

- `backend/src/primelift/evaluation/model_comparison.py`

The comparison layer reads the saved Phase 3 training reports and extracts the chosen holdout split metrics. It normalizes each model into the same scorecard, including:

- overall observed ATE on the holdout split
- top-decile observed ATE
- bottom-decile observed ATE
- top-decile gain over baseline
- bottom-decile behavior
- top-vs-bottom observed gap
- mean predicted CATE
- positive-score share
- top and bottom predicted segments
- interval support where available

### 2. Champion and challenger selection

The comparison report ranks models by actual holdout performance, not by training-time assumptions.

The current ranking logic is simple and explicit:

- highest top-decile observed effect wins first
- top-vs-bottom observed gap breaks ties
- lower bottom-decile observed effect is preferred after that

### 3. CLI entry point

Implemented in:

- `backend/scripts/run_phase3_model_comparison.py`

This command will generate the comparison report. If any required Phase 3 metrics reports are missing, it will train the missing models first and then produce the comparison output.

## Important Scope Note

This slice is not a new model. It is the selection layer that decides what the current Phase 3 winners actually are.

This is the piece that makes revised Phase 3 complete.

The next logical step after this is:

- revised Phase 4, using the selected models for model-based uplift reporting and decile analysis

## How to Verify Revised Phase 3 Comparison Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Generate the comparison report:

```powershell
python backend/scripts/run_phase3_model_comparison.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_model_comparison.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_phase3_model_comparison.py
```

```json
{
  "report_name": "phase3_model_comparison",
  "comparison_split": "test",
  "conversion_comparison": {
    "outcome_column": "conversion",
    "split_name": "test",
    "baseline_observed_ate": 0.009976772207203513,
    "champion_model_name": "drlearner_conversion",
    "champion_reason": "Highest test top-decile observed uplift/revenue effect (0.036735) with top-vs-bottom observed gap 0.025390.",
    "challenger_model_name": "causal_forest_conversion",
    "challenger_reason": "Next-best test top-decile observed uplift/revenue effect (0.012935) with top-vs-bottom observed gap -0.027994. It also provides interval estimates with mean width 0.078304."
  },
  "revenue_comparison": {
    "outcome_column": "revenue",
    "split_name": "test",
    "baseline_observed_ate": 1.1248448294694313,
    "champion_model_name": "drlearner_revenue",
    "champion_reason": "Highest test top-decile observed uplift/revenue effect (6.112634) with top-vs-bottom observed gap 5.394798."
  },
  "revised_phase_3_status": "complete",
  "next_recommended_phase": 4,
  "next_recommended_focus": "Model-based uplift reporting and decile analysis."
}
```

## What That Output Means

### Conversion

The current conversion ranking is:

1. `DRLearner conversion`
2. `CausalForestDML conversion`
3. `XLearner conversion`

Why `DRLearner conversion` wins:

- highest test top-decile observed uplift: `0.036735419630156474`
- strongest top-vs-bottom observed gap: `0.025389621682071206`

Why `CausalForestDML conversion` remains relevant:

- it is not the best ranker here
- but it does provide uncertainty intervals
- mean test interval width: `0.07830430569526774`

Why `XLearner conversion` is no longer the leader:

- lowest top-decile observed uplift among the three conversion models: `0.006286769869730868`

### Revenue

The current revenue leader is:

- `DRLearner revenue`

Why it wins:

- test overall observed revenue ATE: `1.1248448294694313`
- test top-decile observed revenue ATE: `6.112633959365958`
- top-vs-bottom observed revenue gap: `5.394798081150469`

That means the top-ranked users from this model concentrate substantially more incremental revenue than the overall test baseline.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_model_comparison.py -q
```

Current output:

```text
..                                                                       [100%]
2 passed in 0.47s
```

Full backend test output after this slice:

```text
..............................................                           [100%]
46 passed in 19.98s
```

## Where to Inspect the Code

- comparison module: `backend/src/primelift/evaluation/model_comparison.py`
- comparison CLI: `backend/scripts/run_phase3_model_comparison.py`
- focused tests: `backend/tests/test_model_comparison.py`

## Short Conclusion

This revised Phase 3 slice is complete because the repository now has:

- multiple trained causal ML models
- a direct holdout comparison layer
- explicit champion and challenger selection
- a saved comparison report
- passing automated tests

Revised Phase 3 is now complete.
