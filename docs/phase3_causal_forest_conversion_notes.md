# Revised Phase 3 CausalForestDML Conversion Notes

This document explains what was implemented for the third revised Phase 3 ML model slice, what files were added or updated, and what terminal output you should expect when you train the CausalForestDML conversion model yourself.

## Phase 3 Scope for This Slice

This slice implements the next causal ML model in revised Phase 3:

1. keep the ATE baseline in place
2. keep the XLearner and DRLearner slices in place
3. train `CausalForestDML` for `conversion`
4. save the trained model artifact
5. score holdout splits
6. save interval estimates and structured training outputs
7. stop before the next model in Phase 3

This slice implements:

- `CausalForestDML` for `conversion`

It does **not** yet implement:

- `DRLearner` for `revenue`
- a Phase 3 model-selection report across all ML models
- final Phase 3 champion-challenger selection

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/causal/__init__.py`
- `backend/src/primelift/models/registry.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/causal/causal_forest.py`
- `backend/scripts/run_causal_forest_conversion.py`
- `backend/tests/test_causal_forest.py`

Generated locally by this slice:

- `artifacts/models/causal_forest_conversion.joblib`
- `artifacts/metrics/causal_forest_conversion_training_report.json`
- `artifacts/reports/causal_forest_conversion_validation_scores.csv`
- `artifacts/reports/causal_forest_conversion_test_scores.csv`

## What Was Implemented

### 1. CausalForestDML training workflow

Implemented in:

- `backend/src/primelift/causal/causal_forest.py`

The model is trained on the revised Phase 2 prepared dataset using:

- `LightGBMRegressor` for the outcome nuisance model
- `LightGBMClassifier` for the treatment nuisance model
- `CausalForestDML` as the final CATE estimator

The current training setup uses:

- `discrete_treatment=True`
- `cv=2`
- honest causal forest inference

The model trains on the prepared train split and scores:

- validation
- test

### 2. Holdout scoring outputs

Each scored holdout file contains:

- user metadata
- treatment and outcomes
- segment and borough
- predicted uplift score column:
  - `predicted_cate_causal_forest_conversion`
- lower and upper interval columns:
  - `predicted_cate_causal_forest_conversion_ci_lower`
  - `predicted_cate_causal_forest_conversion_ci_upper`

### 3. Structured training report

The saved report includes:

- feature count used for training
- train observed ATE baseline
- validation baseline bootstrap ATE
- holdout mean predicted CATE
- holdout mean interval lower and upper bounds
- mean interval width
- positive predicted uplift share
- top and bottom decile summaries
- top and bottom segments by mean predicted uplift

## Important Scope Note

This slice proves the third ML uplift model is trained, scoring, and producing interval estimates.

It does **not** mean revised Phase 3 is fully complete.

The next model in this phase should be:

- `DRLearner` for `revenue`

That is the right next step because this CausalForestDML slice is useful as a challenger with interval estimates, but it is not clearly outperforming DRLearner on holdout ranking in the current synthetic setup.

## How to Verify Revised Phase 3 CausalForestDML Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Train and score the model:

```powershell
python backend/scripts/run_causal_forest_conversion.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_causal_forest.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_causal_forest_conversion.py
```

```json
{
  "model_name": "causal_forest_conversion",
  "prepared_manifest_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\features\\prepared_dataset_manifest.json",
  "feature_column_count": 105,
  "train_row_count": 70000,
  "train_observed_ate": 0.010183578846079719,
  "validation_row_count": 15000,
  "test_row_count": 15000,
  "model_artifact_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\models\\causal_forest_conversion.joblib",
  "metrics_report_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\metrics\\causal_forest_conversion_training_report.json",
  "config": {
    "outcome_column": "conversion",
    "treatment_column": "treatment",
    "score_column": "predicted_cate_causal_forest_conversion",
    "model_y_class": "lightgbm.LGBMRegressor",
    "model_t_class": "lightgbm.LGBMClassifier",
    "n_estimators": 80,
    "min_samples_leaf": 40,
    "max_samples": 0.45,
    "cv": 2
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
      "mean_predicted_cate": 0.01100590459356182,
      "std_predicted_cate": 0.013072888900589585,
      "min_predicted_cate": -0.042917213816693174,
      "max_predicted_cate": 0.08472803842779372,
      "positive_cate_share": 0.8049333333333333,
      "overall_observed_ate": 0.010345568921134918,
      "mean_interval_lower": -0.02821029802027759,
      "mean_interval_upper": 0.050222107207401216,
      "mean_interval_width": 0.07843240522767882,
      "top_decile_size": 1500,
      "top_decile_mean_predicted_cate": 0.03506456403669777,
      "top_decile_observed_ate": 0.002951635846372702,
      "bottom_decile_size": 1500,
      "bottom_decile_mean_predicted_cate": -0.010666390176461314,
      "bottom_decile_observed_ate": 0.013255242088194036,
      "top_segments_by_mean_predicted_cate": [
        {
          "segment": "High Intent Returners",
          "mean_predicted_cate": 0.016288287563995637
        },
        {
          "segment": "Bargain Hunters",
          "mean_predicted_cate": 0.016195871659125022
        },
        {
          "segment": "Young Professionals",
          "mean_predicted_cate": 0.015211160246034937
        }
      ],
      "bottom_segments_by_mean_predicted_cate": [
        {
          "segment": "Lapsed Users",
          "mean_predicted_cate": -5.3454471781300814e-05
        },
        {
          "segment": "Window Shoppers",
          "mean_predicted_cate": 0.004700604956023252
        },
        {
          "segment": "Loyal Members",
          "mean_predicted_cate": 0.008721358152588893
        }
      ]
    },
    {
      "split_name": "test",
      "row_count": 15000,
      "mean_predicted_cate": 0.010946921427718264,
      "std_predicted_cate": 0.013043019793322449,
      "min_predicted_cate": -0.051232886613696314,
      "max_predicted_cate": 0.07903642438591577,
      "positive_cate_share": 0.8037333333333333,
      "overall_observed_ate": 0.009976772207203513,
      "mean_interval_lower": -0.028205231419915603,
      "mean_interval_upper": 0.050099074275352116,
      "mean_interval_width": 0.07830430569526774,
      "top_decile_size": 1500,
      "top_decile_mean_predicted_cate": 0.034894885414083705,
      "top_decile_observed_ate": 0.012935450819672123,
      "bottom_decile_size": 1500,
      "bottom_decile_mean_predicted_cate": -0.010791447992926436,
      "bottom_decile_observed_ate": 0.04092978766150296,
      "top_segments_by_mean_predicted_cate": [
        {
          "segment": "High Intent Returners",
          "mean_predicted_cate": 0.016071499280101376
        },
        {
          "segment": "Bargain Hunters",
          "mean_predicted_cate": 0.015823987347310376
        },
        {
          "segment": "Young Professionals",
          "mean_predicted_cate": 0.01495164648503921
        }
      ],
      "bottom_segments_by_mean_predicted_cate": [
        {
          "segment": "Lapsed Users",
          "mean_predicted_cate": 0.00023047925556218612
        },
        {
          "segment": "Window Shoppers",
          "mean_predicted_cate": 0.0049655050902702
        },
        {
          "segment": "Loyal Members",
          "mean_predicted_cate": 0.008376426805689166
        }
      ]
    }
  ]
}
```

## What That Output Means

- The model trained successfully on `70000` prepared rows.
- It used the same `105` transformed features as the earlier Phase 3 ML slices.
- It produced per-user CATE estimates and per-user interval bounds on both holdout splits.
- The highest mean predicted uplift segments are again:
  - `High Intent Returners`
  - `Bargain Hunters`
  - `Young Professionals`

The important extra capability in this slice is interval output:

- validation mean interval width: `0.07843240522767882`
- test mean interval width: `0.07830430569526774`

That means the model is not only producing point uplift predictions, it is also exposing uncertainty around those predictions.

The important limitation is ranking quality on this synthetic setup:

- DRLearner test top-decile observed uplift: `0.036735419630156474`
- CausalForestDML test top-decile observed uplift: `0.012935450819672123`

So this slice works technically, but it is not the current leading model for targeting quality. It should be treated as a challenger model with useful interval estimates, not the current champion.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_causal_forest.py -q
```

Current output:

```text
...                                                                      [100%]
3 passed in 11.58s
```

Full backend test output after this slice:

```text
.........................................                                [100%]
41 passed in 22.36s
```

## Where to Inspect the Code

- CausalForestDML implementation: `backend/src/primelift/causal/causal_forest.py`
- CLI: `backend/scripts/run_causal_forest_conversion.py`
- focused tests: `backend/tests/test_causal_forest.py`

## Short Conclusion

This revised Phase 3 slice is complete because the repository now has:

- the third actual causal ML uplift model
- saved model and metric artifacts
- scored holdout outputs with interval bounds
- passing automated tests
- proof that the model learns reasonable segment ordering on the synthetic data

The next model to build in revised Phase 3 should be:

- `DRLearner` for `revenue`
