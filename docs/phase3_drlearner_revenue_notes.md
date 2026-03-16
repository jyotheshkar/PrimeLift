# Revised Phase 3 DRLearner Revenue Notes

This document explains what was implemented for the fourth revised Phase 3 ML model slice, what files were added or updated, and what terminal output you should expect when you train the DRLearner revenue model yourself.

## Phase 3 Scope for This Slice

This slice implements the next causal ML model in revised Phase 3:

1. keep the ATE baseline in place
2. keep the XLearner, DRLearner conversion, and CausalForestDML conversion slices in place
3. train `DRLearner` for `revenue`
4. save the trained model artifact
5. score holdout splits
6. save structured training and scoring outputs
7. stop before the next model in Phase 3

This slice implements:

- `DRLearner` for `revenue`

It does **not** yet implement:

- a formal Phase 3 model-selection report across all trained models
- final champion-challenger selection for conversion plus revenue together

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/causal/__init__.py`
- `backend/src/primelift/causal/drlearner.py`
- `backend/src/primelift/models/registry.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/scripts/run_drlearner_revenue.py`
- `backend/tests/test_drlearner_revenue.py`

Generated locally by this slice:

- `artifacts/models/drlearner_revenue.joblib`
- `artifacts/metrics/drlearner_revenue_training_report.json`
- `artifacts/reports/drlearner_revenue_validation_scores.csv`
- `artifacts/reports/drlearner_revenue_test_scores.csv`

## What Was Implemented

### 1. DRLearner revenue training workflow

Implemented in:

- `backend/src/primelift/causal/drlearner.py`

The revenue slice extends the existing DRLearner module so the same reporting structure can be used for both outcomes.

The model is trained on the revised Phase 2 prepared dataset using:

- `LightGBMClassifier` for the propensity nuisance model
- `LightGBMRegressor` for the revenue nuisance model
- `LightGBMRegressor` for the final CATE model

The current training setup uses:

- `discrete_outcome=False`
- `cv=3`

The model trains on the prepared train split and scores:

- validation
- test

### 2. Holdout scoring outputs

Each scored holdout file contains:

- user metadata
- treatment and outcomes
- segment and borough
- predicted revenue uplift score column:
  - `predicted_cate_drlearner_revenue`

### 3. Structured training report

The saved report includes:

- feature count used for training
- train observed revenue ATE baseline
- validation baseline bootstrap revenue ATE
- holdout mean predicted incremental revenue
- positive predicted revenue-uplift share
- top and bottom decile summaries
- top and bottom segments by mean predicted revenue uplift

## Important Scope Note

This slice proves the revenue-oriented DRLearner model is trained and scoring.

It does **not** mean revised Phase 3 is fully complete.

The next step in this phase should be:

- a clean Phase 3 model-comparison layer

That is the right next step because we now have multiple trained models across conversion and revenue, and the repo needs a direct comparison report before claiming a final Phase 3 champion.

## How to Verify Revised Phase 3 DRLearner Revenue Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Train and score the model:

```powershell
python backend/scripts/run_drlearner_revenue.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_drlearner_revenue.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_drlearner_revenue.py
```

```json
{
  "model_name": "drlearner_revenue",
  "prepared_manifest_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\features\\prepared_dataset_manifest.json",
  "feature_column_count": 105,
  "train_row_count": 70000,
  "train_observed_ate": 0.9462441764304721,
  "validation_row_count": 15000,
  "test_row_count": 15000,
  "model_artifact_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\models\\drlearner_revenue.joblib",
  "metrics_report_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\metrics\\drlearner_revenue_training_report.json",
  "config": {
    "outcome_column": "revenue",
    "treatment_column": "treatment",
    "score_column": "predicted_cate_drlearner_revenue",
    "model_propensity_class": "lightgbm.LGBMClassifier",
    "model_regression_class": "lightgbm.LGBMRegressor",
    "model_final_class": "lightgbm.LGBMRegressor",
    "cv": 3,
    "discrete_outcome": false
  },
  "baseline_validation_analysis": {
    "outcome_column": "revenue",
    "treatment_column": "treatment",
    "treated_mean": 17.25228334891174,
    "control_mean": 16.25628145386766,
    "ate": 0.9960018950440777,
    "absolute_lift": 0.9960018950440777,
    "relative_lift": 0.06126874081692962,
    "ci_lower": -0.5407211426890383,
    "ci_upper": 2.7262496190391796,
    "confidence_level": 0.95,
    "bootstrap_samples": 300
  },
  "split_evaluations": [
    {
      "split_name": "validation",
      "row_count": 15000,
      "mean_predicted_cate": 0.9931676505657563,
      "std_predicted_cate": 6.622461977386061,
      "positive_cate_share": 0.8578,
      "overall_observed_ate": 0.9960018950440777,
      "top_decile_mean_predicted_cate": 11.218829891293813,
      "top_decile_observed_ate": 0.24756001879593015,
      "bottom_decile_mean_predicted_cate": -9.739258047561464,
      "bottom_decile_observed_ate": 6.388330473050452,
      "top_segments_by_mean_predicted_cate": [
        {
          "segment": "High Intent Returners",
          "mean_predicted_cate": 3.00573963872602
        },
        {
          "segment": "Young Professionals",
          "mean_predicted_cate": 1.0559543747797961
        },
        {
          "segment": "Students",
          "mean_predicted_cate": 0.895783902508647
        }
      ]
    },
    {
      "split_name": "test",
      "row_count": 15000,
      "mean_predicted_cate": 1.1148086850583407,
      "std_predicted_cate": 6.412404197408853,
      "positive_cate_share": 0.8587333333333333,
      "overall_observed_ate": 1.1248448294694313,
      "top_decile_mean_predicted_cate": 11.759540097017986,
      "top_decile_observed_ate": 6.112633959365958,
      "bottom_decile_mean_predicted_cate": -9.045402240867935,
      "bottom_decile_observed_ate": 0.7178358782154888,
      "top_segments_by_mean_predicted_cate": [
        {
          "segment": "High Intent Returners",
          "mean_predicted_cate": 3.0546288579492105
        },
        {
          "segment": "Young Professionals",
          "mean_predicted_cate": 1.1213857273411545
        },
        {
          "segment": "Students",
          "mean_predicted_cate": 0.8979474821461
        }
      ]
    }
  ]
}
```

## What That Output Means

- The model trained successfully on `70000` prepared rows.
- It used the same `105` transformed features as the other revised Phase 3 slices.
- The average predicted incremental revenue on validation and test is close to the observed revenue ATE baseline.
- The top predicted revenue-uplift segments are:
  - `High Intent Returners`
  - `Young Professionals`
  - `Students`

The useful positive signal is this:

- test overall observed revenue ATE: `1.1248448294694313`
- test top-decile observed revenue ATE: `6.112633959365958`

That means the model is surfacing a top-ranked group with materially higher incremental revenue than the overall test baseline.

The limitation is still important:

- bottom-decile observed revenue ATE is still positive: `0.7178358782154888`
- so the model is not yet giving a clean suppress-do-not-target tail

This slice is therefore a useful revenue model, but not yet the final policy layer.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_drlearner_revenue.py -q
```

Current output:

```text
...                                                                      [100%]
3 passed in 12.00s
```

Full backend test output after this slice:

```text
............................................                             [100%]
44 passed in 19.57s
```

## Where to Inspect the Code

- DRLearner implementation: `backend/src/primelift/causal/drlearner.py`
- revenue CLI: `backend/scripts/run_drlearner_revenue.py`
- focused tests: `backend/tests/test_drlearner_revenue.py`

## Short Conclusion

This revised Phase 3 slice is complete because the repository now has:

- a revenue-specific causal ML uplift model
- saved model and metric artifacts
- scored holdout outputs
- passing automated tests
- proof that the model can surface high incremental-revenue users above the overall baseline

The next step should be:

- a Phase 3 model-comparison layer before moving deeper into later phases
