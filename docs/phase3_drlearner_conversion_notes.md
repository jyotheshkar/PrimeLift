# Revised Phase 3 DRLearner Conversion Notes

This document explains what was implemented for the second revised Phase 3 ML model slice, what files were added or updated, and what terminal output you should expect when you train the DRLearner conversion model yourself.

## Phase 3 Scope for This Slice

This slice implements the next causal ML model in revised Phase 3:

1. keep the ATE baseline in place
2. keep the XLearner baseline in place
3. train `DRLearner` for `conversion`
4. save the trained model artifact
5. score holdout splits
6. save structured training and scoring outputs
7. stop before the next model in Phase 3

This slice implements:

- `DRLearner` for `conversion`

It does **not** yet implement:

- `DRLearner` for `revenue`
- `CausalForestDML`
- multi-model model-selection reports

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/causal/__init__.py`
- `backend/src/primelift/models/registry.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/causal/drlearner.py`
- `backend/scripts/run_drlearner_conversion.py`
- `backend/tests/test_drlearner.py`

Generated locally by this slice:

- `artifacts/models/drlearner_conversion.joblib`
- `artifacts/metrics/drlearner_conversion_training_report.json`
- `artifacts/reports/drlearner_conversion_validation_scores.csv`
- `artifacts/reports/drlearner_conversion_test_scores.csv`

## What Was Implemented

### 1. DRLearner training workflow

Implemented in:

- `backend/src/primelift/causal/drlearner.py`

The model is trained on the revised Phase 2 prepared dataset using:

- `LightGBMClassifier` for the propensity nuisance model
- `LightGBMClassifier` for the outcome regression nuisance model
- `LightGBMRegressor` for the final CATE model

The current training setup uses:

- `discrete_outcome=True`
- `cv=3`

The model trains on the prepared train split and scores:

- validation
- test

### 2. Holdout scoring outputs

Each scored holdout file contains:

- user metadata
- treatment and outcomes
- segment and borough
- predicted uplift score column:
  - `predicted_cate_drlearner_conversion`

### 3. Structured training report

The saved report includes:

- feature count used for training
- train observed ATE baseline
- validation baseline bootstrap ATE
- holdout mean predicted CATE
- positive predicted uplift share
- top and bottom decile summaries
- top and bottom segments by mean predicted uplift

## Important Scope Note

This slice proves the second ML uplift model is trained and scoring.

It does **not** mean revised Phase 3 is fully complete.

The next model in this phase should be:

- `CausalForestDML`

That is the right next step because DRLearner improves the ranking signal over XLearner, but it still does not cleanly separate the negative-responder segments in this synthetic setup.

## How to Verify Revised Phase 3 DRLearner Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Train and score the model:

```powershell
python backend/scripts/run_drlearner_conversion.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_drlearner.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_drlearner_conversion.py
```

```json
{
  "model_name": "drlearner_conversion",
  "prepared_manifest_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\features\\prepared_dataset_manifest.json",
  "feature_column_count": 105,
  "train_row_count": 70000,
  "train_observed_ate": 0.010183578846079719,
  "validation_row_count": 15000,
  "test_row_count": 15000,
  "model_artifact_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\models\\drlearner_conversion.joblib",
  "metrics_report_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\metrics\\drlearner_conversion_training_report.json",
  "config": {
    "outcome_column": "conversion",
    "treatment_column": "treatment",
    "score_column": "predicted_cate_drlearner_conversion",
    "model_propensity_class": "lightgbm.LGBMClassifier",
    "model_regression_class": "lightgbm.LGBMClassifier",
    "model_final_class": "lightgbm.LGBMRegressor",
    "cv": 3
  },
  "baseline_validation_analysis": {
    "outcome_column": "conversion",
    "treatment_column": "treatment",
    "treated_mean": 0.12298037121110962,
    "control_mean": 0.1126348022899747,
    "ate": 0.010345568921134918,
    "absolute_lift": 0.010345568921134918,
    "relative_lift": 0.09185055338846852,
    "ci_lower": 0.0002751708141452187,
    "ci_upper": 0.021347483698587164,
    "confidence_level": 0.95,
    "bootstrap_samples": 300
  },
  "split_evaluations": [
    {
      "split_name": "validation",
      "row_count": 15000,
      "mean_predicted_cate": 0.010756623539981,
      "std_predicted_cate": 0.03169204751106089,
      "positive_cate_share": 0.8329333333333333,
      "overall_observed_ate": 0.010345568921134918,
      "top_decile_mean_predicted_cate": 0.0669959055545939,
      "top_decile_observed_ate": 0.015339469120981691,
      "bottom_decile_mean_predicted_cate": -0.04466100059357874,
      "bottom_decile_observed_ate": 0.02856045150308334,
      "top_segments_by_mean_predicted_cate": [
        {
          "segment": "High Intent Returners",
          "mean_predicted_cate": 0.02327132264537373
        },
        {
          "segment": "Bargain Hunters",
          "mean_predicted_cate": 0.016074710260138243
        },
        {
          "segment": "Young Professionals",
          "mean_predicted_cate": 0.012398042743283913
        }
      ]
    },
    {
      "split_name": "test",
      "row_count": 15000,
      "mean_predicted_cate": 0.010704826480802376,
      "std_predicted_cate": 0.031667336776370465,
      "positive_cate_share": 0.832,
      "overall_observed_ate": 0.009976772207203513,
      "top_decile_mean_predicted_cate": 0.06722212842209364,
      "top_decile_observed_ate": 0.036735419630156474,
      "bottom_decile_mean_predicted_cate": -0.04367375477968902,
      "bottom_decile_observed_ate": 0.011345797948085268,
      "top_segments_by_mean_predicted_cate": [
        {
          "segment": "High Intent Returners",
          "mean_predicted_cate": 0.022910596398893184
        },
        {
          "segment": "Bargain Hunters",
          "mean_predicted_cate": 0.015572269886188317
        },
        {
          "segment": "Young Professionals",
          "mean_predicted_cate": 0.01284284035459908
        }
      ]
    }
  ]
}
```

Additional terminal segment summary on the saved scored outputs:

Validation:

```text
{'High Intent Returners': 0.0233, 'Bargain Hunters': 0.0161, 'Young Professionals': 0.0124, 'Students': 0.0089, 'Window Shoppers': 0.0084, 'Families': 0.0077, 'Loyal Members': 0.0029, 'Lapsed Users': 0.0003}
```

Test:

```text
{'High Intent Returners': 0.0229, 'Bargain Hunters': 0.0156, 'Young Professionals': 0.0128, 'Students': 0.0088, 'Window Shoppers': 0.0085, 'Families': 0.007, 'Loyal Members': 0.0039, 'Lapsed Users': 0.0002}
```

## What That Output Means

- The model trained successfully on `70000` prepared rows.
- It used the same `105` transformed features as the XLearner slice.
- The average predicted uplift on validation and test stays close to the observed ATE baseline.
- The highest mean predicted uplift segments are again:
  - `High Intent Returners`
  - `Bargain Hunters`
  - `Young Professionals`

The useful improvement over XLearner is this:

- XLearner test top-decile observed uplift: `0.006286769869730868`
- DRLearner test top-decile observed uplift: `0.036735419630156474`

That means DRLearner is doing a better job surfacing the strongest positive responders at the top of the ranking.

The remaining weakness is this:

- the lowest-predicted segments are still not strongly negative on holdout
- `Window Shoppers` are still predicted mildly positive instead of suppressed
- bottom-decile observed uplift is still positive on both holdout splits

So DRLearner is a stronger candidate than XLearner, but still not the final answer for the synthetic treatment-effect design.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_drlearner.py -q
```

Current output:

```text
...                                                                      [100%]
3 passed in 9.77s
```

Full backend test output after this slice:

```text
......................................                                   [100%]
38 passed in 16.13s
```

## Where to Inspect the Code

- DRLearner implementation: `backend/src/primelift/causal/drlearner.py`
- CLI: `backend/scripts/run_drlearner_conversion.py`
- focused tests: `backend/tests/test_drlearner.py`

## Short Conclusion

This revised Phase 3 slice is complete because the repository now has:

- the second actual causal ML uplift model
- saved model and metric artifacts
- scored holdout outputs
- passing automated tests
- proof that DRLearner improves top-decile ranking over the XLearner baseline

The next model to build in revised Phase 3 should be:

- `CausalForestDML`
