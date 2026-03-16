# Revised Phase 1 ML-Ready Foundation Notes

This document explains what was implemented for the revised ML-first Phase 1, what changed in the repository, and what you should see in the terminal when you verify it yourself.

## Phase 1 Scope

After revising `PROJECT_SPEC.md`, Phase 1 is no longer just a generic scaffold.

It now establishes the ML-ready foundation needed for the first five phases:

1. revised ML-first project roadmap
2. feature-schema definitions for modeling
3. planned model registry for causal ML
4. planned evaluation registry
5. artifact directory helpers for saved models and reports
6. a terminal verification script for the ML scaffold

This phase does **not** train any ML models yet.

It prepares the repository so model training in the next phases has a clean structure.

## Files Added or Updated

Updated:

- `PROJECT_SPEC.md`
- `README.md`
- `requirements.txt`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/features/__init__.py`
- `backend/src/primelift/features/columns.py`
- `backend/src/primelift/models/__init__.py`
- `backend/src/primelift/models/registry.py`
- `backend/src/primelift/evaluation/__init__.py`
- `backend/src/primelift/evaluation/registry.py`
- `backend/src/primelift/utils/artifacts.py`
- `backend/scripts/show_ml_foundation.py`
- `backend/tests/test_ml_foundation.py`

Installed into `.venv` during this phase:

- `econml==0.16.0`
- `lightgbm==4.6.0`

## What Was Implemented

### 1. Revised ML-first project spec

`PROJECT_SPEC.md` now defines the first five phases as ML-oriented:

- Phase 1: ML-ready foundation
- Phase 2: dataset and feature foundation
- Phase 3: causal ML analysis core
- Phase 4: model-based uplift analysis
- Phase 5: ML decision engine

This is the contract the next implementation steps will follow.

### 2. Feature schema contract

Implemented in:

- `backend/src/primelift/features/columns.py`

It defines the modeling column groups used by future ML training code:

- identifier columns
- date columns
- treatment columns
- outcome columns
- group columns
- categorical model features
- numeric model features

Current model feature count:

- `16`

### 3. Model blueprint registry

Implemented in:

- `backend/src/primelift/models/registry.py`

This registry now records the planned causal ML stack:

- ATE baseline
- XLearner
- DRLearner for conversion
- DRLearner for revenue
- CausalForestDML
- DRPolicyTree
- DRPolicyForest
- LightGBMClassifier
- LightGBMRegressor

This phase only registers the models and their intended role.

It does **not** fit them yet.

### 4. Evaluation blueprint registry

Implemented in:

- `backend/src/primelift/evaluation/registry.py`

This defines the planned reporting outputs for later phases, including:

- baseline summary
- model comparison report
- uplift decile report
- segment rollup report
- policy recommendation report

### 5. Artifact path helpers

Implemented in:

- `backend/src/primelift/utils/paths.py`
- `backend/src/primelift/utils/artifacts.py`

This phase now creates and exposes these artifact locations:

- `artifacts/models/`
- `artifacts/reports/`
- `artifacts/metrics/`
- `artifacts/features/`

These are where trained models, reports, metrics, and feature outputs will go in later phases.

### 6. Phase 1 verification script

Implemented in:

- `backend/scripts/show_ml_foundation.py`

This script prints the current ML scaffold as JSON so the phase can be verified from the terminal.

## Important Scope Note

Revised Phase 1 does **not** train or score ML models yet.

It does not produce:

- fitted EconML models
- LightGBM models
- per-user uplift scores
- policy recommendations

Those belong to later revised phases.

## How to Verify Revised Phase 1

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Run the ML foundation verification script:

```powershell
python backend/scripts/show_ml_foundation.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_ml_foundation.py -q
```

Optional direct import check:

```powershell
python -c "import econml, lightgbm; print({'econml': econml.__version__, 'lightgbm': lightgbm.__version__})"
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/show_ml_foundation.py
```

```json
{
  "feature_schema": {
    "identifier_columns": [
      "user_id",
      "campaign_id"
    ],
    "date_columns": [
      "event_date"
    ],
    "treatment_columns": [
      "treatment"
    ],
    "outcome_columns": [
      "conversion",
      "revenue"
    ],
    "group_columns": [
      "segment",
      "london_borough",
      "device_type",
      "channel"
    ],
    "categorical_feature_columns": [
      "london_borough",
      "postcode_area",
      "age_band",
      "gender",
      "device_type",
      "platform",
      "traffic_source",
      "channel",
      "is_prime_like_member",
      "segment"
    ],
    "numeric_feature_columns": [
      "age",
      "prior_engagement_score",
      "prior_purchases_90d",
      "prior_sessions_30d",
      "avg_order_value",
      "customer_tenure_days"
    ],
    "model_feature_columns": [
      "london_borough",
      "postcode_area",
      "age_band",
      "gender",
      "device_type",
      "platform",
      "traffic_source",
      "channel",
      "is_prime_like_member",
      "segment",
      "age",
      "prior_engagement_score",
      "prior_purchases_90d",
      "prior_sessions_30d",
      "avg_order_value",
      "customer_tenure_days"
    ],
    "total_model_feature_count": 16
  },
  "model_blueprints": [
    {
      "name": "ate_baseline",
      "family": "baseline",
      "role": "scientific_sanity_check",
      "package": "internal",
      "estimator_class": "DifferenceInMeans",
      "supported_outcomes": [
        "conversion",
        "revenue"
      ],
      "purpose": "Keep a non-ML causal baseline that every uplift model must beat.",
      "target_phase": 3,
      "status": "implemented"
    },
    {
      "name": "xlearner_conversion",
      "family": "cate",
      "role": "ml_baseline",
      "package": "econml",
      "estimator_class": "econml.metalearners.XLearner",
      "supported_outcomes": [
        "conversion"
      ],
      "purpose": "Provide the first ML uplift baseline for conversion scoring.",
      "target_phase": 3,
      "status": "planned"
    },
    {
      "name": "drlearner_conversion",
      "family": "cate",
      "role": "champion_candidate",
      "package": "econml",
      "estimator_class": "econml.dr.DRLearner",
      "supported_outcomes": [
        "conversion"
      ],
      "purpose": "Serve as the main CATE model for conversion uplift scoring.",
      "target_phase": 3,
      "status": "planned"
    },
    {
      "name": "drlearner_revenue",
      "family": "cate",
      "role": "champion_candidate",
      "package": "econml",
      "estimator_class": "econml.dr.DRLearner",
      "supported_outcomes": [
        "revenue"
      ],
      "purpose": "Estimate incremental revenue effects for budget decisions.",
      "target_phase": 3,
      "status": "planned"
    },
    {
      "name": "causal_forest_conversion",
      "family": "cate",
      "role": "challenger",
      "package": "econml",
      "estimator_class": "econml.dml.CausalForestDML",
      "supported_outcomes": [
        "conversion"
      ],
      "purpose": "Model non-linear treatment heterogeneity as a challenger estimator.",
      "target_phase": 3,
      "status": "planned"
    },
    {
      "name": "dr_policy_tree",
      "family": "policy",
      "role": "explainable_decision_model",
      "package": "econml",
      "estimator_class": "econml.policy.DRPolicyTree",
      "supported_outcomes": [
        "conversion",
        "revenue"
      ],
      "purpose": "Generate interpretable targeting policy recommendations.",
      "target_phase": 5,
      "status": "planned"
    },
    {
      "name": "dr_policy_forest",
      "family": "policy",
      "role": "performance_challenger",
      "package": "econml",
      "estimator_class": "econml.policy.DRPolicyForest",
      "supported_outcomes": [
        "conversion",
        "revenue"
      ],
      "purpose": "Provide a higher-capacity policy model after the explainable tree baseline.",
      "target_phase": 5,
      "status": "planned"
    },
    {
      "name": "lightgbm_classifier",
      "family": "base_learner",
      "role": "nuisance_model",
      "package": "lightgbm",
      "estimator_class": "lightgbm.LGBMClassifier",
      "supported_outcomes": [
        "conversion",
        "treatment"
      ],
      "purpose": "Handle binary propensity and conversion nuisance modeling on tabular features.",
      "target_phase": 1,
      "status": "planned"
    },
    {
      "name": "lightgbm_regressor",
      "family": "base_learner",
      "role": "nuisance_model",
      "package": "lightgbm",
      "estimator_class": "lightgbm.LGBMRegressor",
      "supported_outcomes": [
        "revenue"
      ],
      "purpose": "Handle continuous revenue nuisance modeling on tabular features.",
      "target_phase": 1,
      "status": "planned"
    }
  ],
  "evaluation_blueprints": [
    {
      "name": "ate_baseline_summary",
      "category": "baseline_metrics",
      "target_phase": 3,
      "purpose": "Store treated and control means, ATE, and confidence intervals.",
      "status": "implemented"
    },
    {
      "name": "model_comparison_report",
      "category": "model_selection",
      "target_phase": 3,
      "purpose": "Compare baseline, XLearner, DRLearner, and CausalForestDML outputs.",
      "status": "planned"
    },
    {
      "name": "uplift_decile_report",
      "category": "ranking_quality",
      "target_phase": 4,
      "purpose": "Inspect whether high-scored users concentrate observed incremental lift.",
      "status": "planned"
    },
    {
      "name": "segment_rollup_report",
      "category": "business_reporting",
      "target_phase": 4,
      "purpose": "Summarize model-based uplift across segments, boroughs, devices, and channels.",
      "status": "planned"
    },
    {
      "name": "policy_recommendation_report",
      "category": "decisioning",
      "target_phase": 5,
      "purpose": "Store targeting and suppression recommendations with budget rationale.",
      "status": "planned"
    }
  ],
  "artifact_manifest": {
    "artifacts_root": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts",
    "model_artifacts_dir": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\models",
    "report_artifacts_dir": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\reports",
    "metrics_artifacts_dir": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\metrics",
    "feature_artifacts_dir": "C:\\Users\\Jyothesh karnam\\Desktop\\PrimeLift\\artifacts\\features"
  }
}
```

## Test Proof

Direct dependency import output:

```text
{'econml': '0.16.0', 'lightgbm': '4.6.0'}
```

Run:

```powershell
python -m pytest backend/tests/test_ml_foundation.py -q
```

Current output:

```text
.....                                                                    [100%]
5 passed in 11.29s
```

Full backend test output after this phase:

```text
............................                                             [100%]
28 passed in 11.42s
```

## Where to Inspect the Code

- feature schema: `backend/src/primelift/features/columns.py`
- model registry: `backend/src/primelift/models/registry.py`
- evaluation registry: `backend/src/primelift/evaluation/registry.py`
- artifact helpers: `backend/src/primelift/utils/artifacts.py`
- path setup: `backend/src/primelift/utils/paths.py`
- verification script: `backend/scripts/show_ml_foundation.py`
- tests: `backend/tests/test_ml_foundation.py`

## Short Conclusion

Revised Phase 1 is complete because the repository now has:

- an ML-first project spec
- model-ready feature definitions
- a defined causal ML model stack
- planned evaluation outputs
- artifact directory structure
- a runnable verification script
- passing tests for the new scaffold
