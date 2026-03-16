# Revised Phase 5 DRPolicyTree Notes

This document explains what was implemented for the third revised Phase 5 slice, what files were added or updated, and what terminal output you should expect when you train the explainable policy tree yourself.

## Phase 5 Scope for This Slice

This slice adds the first explicit policy-learning model to PrimeLift.

It does the following:

1. recover the raw train and test splits from the saved Phase 2 split contract
2. build a compact, human-readable policy feature set
3. train `DRPolicyTree` on the conversion outcome
4. score the holdout split with policy actions and policy values
5. estimate holdout policy value against always-treat and always-control baselines
6. extract leaf-level rules and feature-importance summaries

This slice covers:

- explainable policy learning via `DRPolicyTree`
- holdout policy evaluation
- scored policy decision export
- leaf-level rule extraction

It does **not** yet implement:

- `DRPolicyForest`
- a policy-model comparison layer
- the final full Phase 5 decision engine

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/decision/__init__.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/decision/policy_tree.py`
- `backend/scripts/run_drpolicytree_conversion.py`
- `backend/tests/test_policy_tree.py`

Generated locally by this slice:

- `artifacts/models/drpolicytree_conversion.joblib`
- `artifacts/metrics/drpolicytree_conversion_policy_report.json`
- `artifacts/reports/drpolicytree_conversion_test_decisions.csv`

## What Was Implemented

### 1. Explainable policy model

Implemented in:

- `backend/src/primelift/decision/policy_tree.py`

This slice trains `DRPolicyTree` on a deliberately small feature set so the resulting rules stay readable.

The current feature set is:

- numeric:
  - `age`
  - `prior_engagement_score`
  - `prior_purchases_90d`
  - `prior_sessions_30d`
  - `avg_order_value`
  - `customer_tenure_days`
- categorical:
  - `segment`
  - `device_type`
  - `is_prime_like_member`

That is intentionally narrower than the full Phase 3 feature space because this slice is about explainable action rules, not maximum raw predictive complexity.

### 2. Holdout policy evaluation

The policy report estimates:

- holdout policy value
- always-treat baseline value
- always-control baseline value
- gain over each baseline

Because the dataset comes from a randomized experiment, the holdout evaluation can be estimated directly from observed treated users in the policy-treat subset and observed control users in the policy-control subset.

### 3. Leaf-level rules

The report extracts:

- each leaf ID
- its recommended action
- its estimated value
- its holdout population size
- its rule path

This makes the model inspectable in a way that later API and frontend layers can surface directly.

## Important Scope Note

This slice is an explainable policy baseline.

It is useful because it turns the existing uplift work into explicit treat-vs-control rules.

It is **not** the final policy answer yet.

On the current real dataset:

- the policy tree beats `always_control`
- but it does **not** beat `always_treat`

That is an honest result, and it means the next Phase 5 slice should test a stronger policy learner:

- `DRPolicyForest`

## How to Verify Revised Phase 5 DRPolicyTree Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Train and score the policy tree:

```powershell
python backend/scripts/run_drpolicytree_conversion.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_policy_tree.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_drpolicytree_conversion.py
```

```json
{
  "report_name": "phase5_drpolicytree_conversion_policy",
  "split_name": "test",
  "tree_leaf_count": 7,
  "recommended_treat_rate": 0.8117333333333333,
  "estimated_policy_value": 0.12208121165004987,
  "always_treat_value": 0.12272970085470085,
  "always_control_value": 0.11275292864749734,
  "policy_gain_over_always_treat": -0.0006484892046509788,
  "policy_gain_over_always_control": 0.009328283002552534
}
```

Additional output highlights from the same run:

```json
{
  "top_feature_importances": [
    {
      "feature_name": "avg_order_value",
      "importance": 0.8192219816424395
    },
    {
      "feature_name": "segment = Lapsed Users",
      "importance": 0.12659833343245636
    },
    {
      "feature_name": "prior_engagement_score",
      "importance": 0.047284497159661924
    }
  ],
  "top_control_segments": [
    {
      "segment": "Lapsed Users",
      "user_count": 1111,
      "user_share": 0.39341359773371104
    }
  ],
  "top_treat_segments": [
    {
      "segment": "Young Professionals",
      "user_count": 2595,
      "user_share": 0.21312417871222075
    },
    {
      "segment": "Families",
      "user_count": 2287,
      "user_share": 0.18782851511169513
    },
    {
      "segment": "High Intent Returners",
      "user_count": 1933,
      "user_share": 0.15875492772667543
    }
  ]
}
```

Example extracted rules from the same run:

```json
[
  {
    "recommended_action": "treat",
    "rule": "avg_order_value <= 147.81 and segment != Lapsed Users and avg_order_value > 43.05"
  },
  {
    "recommended_action": "control",
    "rule": "avg_order_value <= 147.81 and segment == Lapsed Users and age > 31.50"
  }
]
```

## What That Output Means

- The tree has learned explicit holdout rules instead of only ranking scores.
- The model is sending most users to treatment, which fits the fact that the synthetic dataset still has a broadly positive overall ATE.
- The tree is especially cautious around `Lapsed Users`, which is consistent with earlier suppression evidence from Phase 4 and Phase 5.
- The policy is useful as an explainable baseline because it beats `always_control`.
- It is not the final winner because `always_treat` is still slightly better on the current holdout estimate.

That last point is important:

- this slice is a real policy model
- but it is not strong enough yet to close Phase 5 by itself

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_policy_tree.py -q
```

Current output:

```text
..                                                                       [100%]
2 passed in 8.15s
```

Full backend test output after this slice:

```text
..........................................................               [100%]
58 passed in 30.83s
```

## Where to Inspect the Code

- policy module: `backend/src/primelift/decision/policy_tree.py`
- policy CLI: `backend/scripts/run_drpolicytree_conversion.py`
- focused tests: `backend/tests/test_policy_tree.py`

## Short Conclusion

This third revised Phase 5 slice is complete because the repository now has:

- an explainable `DRPolicyTree` policy model
- scored treat/control recommendations on the holdout split
- holdout policy-value evaluation against naive baselines
- leaf-level policy rules
- terminal-verifiable artifacts
- passing automated tests

The next Phase 5 slice should be `DRPolicyForest`.
