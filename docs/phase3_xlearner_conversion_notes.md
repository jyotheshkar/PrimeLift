# Revised Phase 3 XLearner Conversion Notes

This document explains what was implemented for the first revised Phase 3 ML model slice, what files were added or updated, and what terminal output you should expect when you train the XLearner conversion model yourself.

## Phase 3 Scope for This Slice

Revised Phase 3 contains multiple causal ML models, but this slice implements only the first one:

1. keep the existing ATE baseline in place
2. train the first ML uplift model
3. save the trained model artifact
4. score holdout splits
5. save structured training and scoring outputs
6. stop before the next model in Phase 3

This slice implements:

- `XLearner` for `conversion`

It does **not** yet implement:

- `DRLearner`
- `CausalForestDML`
- revenue-model training
- multi-model comparison

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/causal/__init__.py`
- `backend/src/primelift/models/registry.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/causal/xlearner.py`
- `backend/scripts/run_xlearner_conversion.py`
- `backend/tests/test_xlearner.py`

Generated locally by this slice:

- `artifacts/models/xlearner_conversion.joblib`
- `artifacts/metrics/xlearner_conversion_training_report.json`
- `artifacts/reports/xlearner_conversion_validation_scores.csv`
- `artifacts/reports/xlearner_conversion_test_scores.csv`

## What Was Implemented

### 1. XLearner training workflow

Implemented in:

- `backend/src/primelift/causal/xlearner.py`

The model is trained on the revised Phase 2 prepared dataset using:

- `LightGBMRegressor` for base outcome models
- `LightGBMRegressor` for CATE models
- `LogisticRegression` for the propensity model

The model trains on the prepared train split and scores:

- validation
- test

### 2. Holdout scoring outputs

Each scored holdout file contains:

- user metadata
- treatment and outcomes
- segment and borough
- predicted uplift score column:
  - `predicted_cate_xlearner_conversion`

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

This slice proves the first ML uplift model is trained and scoring.

It does **not** mean revised Phase 3 is fully complete.

The next model in this phase should be:

- `DRLearner`

That is the right next step because this first XLearner behaves like a baseline: it learns sensible segment ordering, but its decile ranking signal is not yet strong enough to be the final champion model.

## How to Verify Revised Phase 3 XLearner Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Train and score the model:

```powershell
python backend/scripts/run_xlearner_conversion.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_xlearner.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_xlearner_conversion.py
```

```json
{
  "model_name": "xlearner_conversion",
  "prepared_manifest_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\features\\prepared_dataset_manifest.json",
  "feature_column_count": 105,
  "feature_column_sample": [
    "numeric__age",
    "numeric__prior_engagement_score",
    "numeric__prior_purchases_90d",
    "numeric__prior_sessions_30d",
    "numeric__avg_order_value",
    "numeric__customer_tenure_days",
    "categorical__london_borough_Barking and Dagenham",
    "categorical__london_borough_Barnet",
    "categorical__london_borough_Bexley",
    "categorical__london_borough_Brent",
    "categorical__london_borough_Bromley",
    "categorical__london_borough_Camden",
    "categorical__london_borough_City of London",
    "categorical__london_borough_Croydon",
    "categorical__london_borough_Ealing",
    "categorical__london_borough_Enfield",
    "categorical__london_borough_Greenwich",
    "categorical__london_borough_Hackney",
    "categorical__london_borough_Hammersmith and Fulham",
    "categorical__london_borough_Haringey"
  ],
  "train_row_count": 70000,
  "train_observed_ate": 0.010183578846079719,
  "validation_row_count": 15000,
  "test_row_count": 15000,
  "model_artifact_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\models\\xlearner_conversion.joblib",
  "metrics_report_path": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\metrics\\xlearner_conversion_training_report.json",
  "config": {
    "outcome_column": "conversion",
    "treatment_column": "treatment",
    "score_column": "predicted_cate_xlearner_conversion",
    "base_model_class": "lightgbm.LGBMRegressor",
    "cate_model_class": "lightgbm.LGBMRegressor",
    "propensity_model_class": "sklearn.linear_model.LogisticRegression"
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
      "mean_predicted_cate": 0.01030885796678208,
      "std_predicted_cate": 0.02056032996322506,
      "min_predicted_cate": -0.15581611721646219,
      "max_predicted_cate": 0.19645005409271044,
      "positive_cate_share": 0.8254666666666667,
      "overall_observed_ate": 0.010345568921134918,
      "top_decile_mean_predicted_cate": 0.047871321301922704,
      "bottom_decile_mean_predicted_cate": -0.027614024511776344,
      "top_segments_by_mean_predicted_cate": [
        {
          "segment": "High Intent Returners",
          "mean_predicted_cate": 0.02217380225197724
        },
        {
          "segment": "Bargain Hunters",
          "mean_predicted_cate": 0.01496541883423005
        },
        {
          "segment": "Young Professionals",
          "mean_predicted_cate": 0.013122322402583186
        }
      ],
      "bottom_segments_by_mean_predicted_cate": [
        {
          "segment": "Lapsed Users",
          "mean_predicted_cate": -0.0003062669031812062
        },
        {
          "segment": "Loyal Members",
          "mean_predicted_cate": 0.0018487474163087507
        },
        {
          "segment": "Window Shoppers",
          "mean_predicted_cate": 0.004568491134533785
        }
      ]
    },
    {
      "split_name": "test",
      "row_count": 15000,
      "mean_predicted_cate": 0.010284462220123103,
      "std_predicted_cate": 0.020882772920962692,
      "min_predicted_cate": -0.13444207765295405,
      "max_predicted_cate": 0.20869817021891252,
      "positive_cate_share": 0.8279333333333333,
      "overall_observed_ate": 0.009976772207203513,
      "top_decile_mean_predicted_cate": 0.04820049751830612,
      "bottom_decile_mean_predicted_cate": -0.028041036451185802,
      "top_segments_by_mean_predicted_cate": [
        {
          "segment": "High Intent Returners",
          "mean_predicted_cate": 0.022676094372067357
        },
        {
          "segment": "Bargain Hunters",
          "mean_predicted_cate": 0.014994657997597244
        },
        {
          "segment": "Young Professionals",
          "mean_predicted_cate": 0.012908568198720131
        }
      ],
      "bottom_segments_by_mean_predicted_cate": [
        {
          "segment": "Lapsed Users",
          "mean_predicted_cate": -0.0003405926981637663
        },
        {
          "segment": "Loyal Members",
          "mean_predicted_cate": 0.0022575869978014042
        },
        {
          "segment": "Window Shoppers",
          "mean_predicted_cate": 0.004617216728498055
        }
      ]
    }
  ]
}
```

## What That Output Means

- The model trained successfully on `70000` prepared rows.
- It used `105` transformed features from the revised Phase 2 pipeline.
- The average predicted uplift on validation and test is very close to the observed ATE baseline.
- The highest mean predicted uplift segments are:
  - `High Intent Returners`
  - `Bargain Hunters`
  - `Young Professionals`
- The lowest mean predicted uplift segment is:
  - `Lapsed Users`

That segment ordering is directionally aligned with the synthetic treatment-effect design and shows the first ML model is learning useful heterogeneity.

At the same time, the top-vs-bottom decile observed uplift separation is mixed. That is why this XLearner should be treated as the first ML baseline, not the final champion model.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_xlearner.py -q
```

Current output:

```text
...                                                                      [100%]
3 passed in 9.55s
```

Full backend test output after this slice:

```text
...................................                                      [100%]
35 passed in 15.29s
```

## Where to Inspect the Code

- XLearner implementation: `backend/src/primelift/causal/xlearner.py`
- CLI: `backend/scripts/run_xlearner_conversion.py`
- focused tests: `backend/tests/test_xlearner.py`

## Short Conclusion

This revised Phase 3 slice is complete because the repository now has:

- the first actual causal ML uplift model
- saved model and metric artifacts
- scored holdout outputs
- passing automated tests
- proof that the model learns sensible segment ordering on the synthetic data

The next model to build in revised Phase 3 should be:

- `DRLearner`
