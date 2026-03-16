# Revised Phase 5 DRPolicyForest Notes

This document explains what was implemented for the fourth revised Phase 5 slice, what files were added or updated, and what terminal output you should expect when you train the policy-forest challenger yourself.

## Phase 5 Scope for This Slice

This slice adds the stronger policy challenger on top of the explainable tree baseline.

It does the following:

1. recover the raw train and test splits from the saved Phase 2 split contract
2. reuse the same compact policy feature set as `DRPolicyTree`
3. train `DRPolicyForest` on the conversion outcome
4. score the holdout split with policy actions and policy values
5. estimate holdout policy value against always-treat and always-control baselines
6. load the saved `DRPolicyTree` report and compare forest value against tree value

This slice covers:

- stronger policy learning via `DRPolicyForest`
- holdout policy evaluation
- tree-vs-forest challenger comparison
- scored policy decision export

It does **not** yet implement:

- a full policy comparison dashboard
- a Phase 5 final closeout report

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/decision/__init__.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/decision/policy_forest.py`
- `backend/scripts/run_drpolicyforest_conversion.py`
- `backend/tests/test_policy_forest.py`

Generated locally by this slice:

- `artifacts/models/drpolicyforest_conversion.joblib`
- `artifacts/metrics/drpolicyforest_conversion_policy_report.json`
- `artifacts/reports/drpolicyforest_conversion_test_decisions.csv`

## What Was Implemented

### 1. Policy-forest challenger

Implemented in:

- `backend/src/primelift/decision/policy_forest.py`

This slice trains `DRPolicyForest` using the same raw policy features as the tree slice:

- `age`
- `prior_engagement_score`
- `prior_purchases_90d`
- `prior_sessions_30d`
- `avg_order_value`
- `customer_tenure_days`
- `segment`
- `device_type`
- `is_prime_like_member`

Keeping the feature space fixed makes the challenger comparison defensible:

- same split contract
- same feature space
- different policy learner

### 2. Holdout challenger comparison

The report estimates:

- holdout policy value
- always-treat baseline value
- always-control baseline value
- gain over each naive baseline
- saved `DRPolicyTree` value
- gain over the saved tree

That means this slice does not just produce another model artifact. It produces an actual policy challenger result.

### 3. Non-rule-based policy summary

Unlike `DRPolicyTree`, the forest does not expose clean leaf rules for explanation. So this slice reports:

- top feature importances
- top treat-side segments
- top holdout-side segments
- the decision CSV for user-level inspection

That is the right tradeoff here:

- more policy strength
- less direct rule-level interpretability

## Important Scope Note

This slice is the stronger policy challenger.

On the current real dataset, it is actually useful:

- it beats `always_control`
- it beats the saved `DRPolicyTree`
- it also slightly beats `always_treat`

That is the first Phase 5 policy model so far that clears all three comparisons on the real holdout.

## How to Verify Revised Phase 5 DRPolicyForest Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Train and score the policy forest:

```powershell
python backend/scripts/run_drpolicyforest_conversion.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_policy_forest.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_drpolicyforest_conversion.py
```

```json
{
  "report_name": "phase5_drpolicyforest_conversion_policy",
  "split_name": "test",
  "forest_n_estimators": 200,
  "recommended_treat_rate": 0.8878,
  "estimated_policy_value": 0.12349633229269714,
  "always_treat_value": 0.12272970085470085,
  "always_control_value": 0.11275292864749734,
  "policy_tree_value": 0.12208121165004987,
  "policy_gain_over_always_treat": 0.0007666314379962957,
  "policy_gain_over_always_control": 0.010743403645199809,
  "policy_gain_over_tree": 0.0014151206426472746
}
```

Additional output highlights from the same run:

```json
{
  "top_feature_importances": [
    {
      "feature_name": "avg_order_value",
      "importance": 0.47541119543952937
    },
    {
      "feature_name": "prior_engagement_score",
      "importance": 0.13244638682866583
    },
    {
      "feature_name": "segment = Lapsed Users",
      "importance": 0.1274821011899079
    }
  ],
  "top_treat_segments": [
    {
      "segment": "Young Professionals",
      "user_count": 2656,
      "user_share": 0.19944431929113163
    },
    {
      "segment": "Families",
      "user_count": 2342,
      "user_share": 0.17586543515806863
    },
    {
      "segment": "High Intent Returners",
      "user_count": 2019,
      "user_share": 0.1516107231358414
    }
  ],
  "top_control_segments": [
    {
      "segment": "Lapsed Users",
      "user_count": 936,
      "user_share": 0.5561497326203209
    },
    {
      "segment": "Window Shoppers",
      "user_count": 246,
      "user_share": 0.14616755793226383
    }
  ]
}
```

## What That Output Means

- The forest is still mostly recommending treatment, which fits the broadly positive synthetic ATE.
- It is holding out a more concentrated set of likely weak responders than the tree baseline.
- `Lapsed Users` remains the strongest holdout signal, which is consistent with earlier suppression evidence.
- On this holdout, the forest is the stronger policy model so far because it slightly improves on:
  - `always_treat`
  - `always_control`
  - `DRPolicyTree`

That makes it a credible current policy champion.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_policy_forest.py -q
```

Current output:

```text
..                                                                       [100%]
2 passed in 8.56s
```

Full backend test output after this slice:

```text
............................................................             [100%]
60 passed in 27.16s
```

## Where to Inspect the Code

- policy-forest module: `backend/src/primelift/decision/policy_forest.py`
- policy-forest CLI: `backend/scripts/run_drpolicyforest_conversion.py`
- focused tests: `backend/tests/test_policy_forest.py`

## Short Conclusion

This fourth revised Phase 5 slice is complete because the repository now has:

- a stronger `DRPolicyForest` policy challenger
- holdout comparison against naive baselines
- holdout comparison against the saved `DRPolicyTree`
- scored treat/control recommendations on the holdout split
- terminal-verifiable artifacts
- passing automated tests

This is the strongest Phase 5 policy model in the repository so far.
