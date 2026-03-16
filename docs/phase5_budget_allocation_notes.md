# Revised Phase 5 Budget Allocation Notes

This document explains what was implemented for the second revised Phase 5 slice, what files were added or updated, and what terminal output you should expect when you generate the budget allocation report yourself.

## Phase 5 Scope for This Slice

This slice converts the current model outputs into a budget recommendation layer.

It does the following:

1. load the Phase 4 conversion rollup report
2. load the saved Phase 3 revenue model report
3. load the scored revenue holdout output for the same split
4. keep only prioritized segment cohorts from the conversion rollup
5. measure positive predicted revenue opportunity inside each prioritized segment
6. allocate a fixed budget pool in proportion to that positive opportunity
7. assign zero incremental budget to suppressed segments

This slice covers:

- segment-level budget allocation
- revenue-weighted opportunity sizing
- zero-budget suppression for weak segments
- one compact human-readable budget summary

It does **not** yet implement:

- DRPolicyTree
- DRPolicyForest
- the final full Phase 5 decision engine

## Files Added or Updated

Updated:

- `README.md`
- `backend/src/primelift/decision/__init__.py`
- `backend/src/primelift/utils/paths.py`

Added:

- `backend/src/primelift/decision/budget_allocation.py`
- `backend/scripts/run_budget_allocation.py`
- `backend/tests/test_budget_allocation.py`

Generated locally by this slice:

- `artifacts/metrics/phase5_budget_allocation_report.json`
- `artifacts/reports/phase5_segment_budget_allocation.csv`

## What Was Implemented

### 1. Segment-level budget allocator

Implemented in:

- `backend/src/primelift/decision/budget_allocation.py`

The allocator uses:

- the Phase 4 conversion rollup report to decide which segments remain eligible for spend
- the Phase 3 revenue uplift model to estimate value opportunity within those eligible segments

The result is practical and explainable:

- conversion uplift says whether a segment is worth targeting
- revenue uplift says how much budget weight that segment should receive

### 2. Positive revenue opportunity sizing

For each prioritized segment, the allocator computes:

- eligible users in the scored holdout split
- positive-revenue user count
- positive-revenue user share
- mean predicted conversion effect
- observed conversion ATE
- mean predicted revenue effect
- total positive predicted revenue effect

The actual budget share is based on:

- `total positive predicted revenue effect`

That is more useful than a plain mean because it captures both:

- how strong the revenue signal is
- how much addressable positive mass exists inside the segment

### 3. Zero-budget suppression

Suppressed segments are carried forward into the report with:

- their conversion context
- their revenue context
- an explicit `recommended_budget = 0`

That keeps the decision layer honest rather than hiding weak segments.

## Important Scope Note

This is the second revised Phase 5 slice.

It proves the repository can now turn model outputs into:

- target-user and suppress-user lists
- cohort-level action summaries
- segment-level budget allocations

It does **not** mean revised Phase 5 is fully complete.

The next serious Phase 5 slice should be:

- `DRPolicyTree` for explainable treatment-policy rules

## How to Verify Revised Phase 5 Budget Slice

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Generate the budget report:

```powershell
python backend/scripts/run_budget_allocation.py
```

Run the focused tests:

```powershell
python -m pytest backend/tests/test_budget_allocation.py -q
```

## Terminal Proof: Actual Output

Current output from:

```powershell
python backend/scripts/run_budget_allocation.py
```

```json
{
  "report_name": "phase5_segment_budget_allocation",
  "split_name": "test",
  "conversion_model_name": "drlearner_conversion",
  "revenue_model_name": "drlearner_revenue",
  "total_budget": 100000.0,
  "allocated_budget": 100000.0,
  "allocated_segment_count": 7,
  "suppressed_segment_count": 1,
  "action_summary": "Allocate budget to High Intent Returners (37.9%), Loyal Members (23.9%), Young Professionals (14.1%); keep Lapsed Users at zero incremental budget."
}
```

Additional output highlights from the same run:

```json
{
  "top_budget_segments": [
    {
      "segment": "High Intent Returners",
      "recommended_budget": 37869.54284717371,
      "budget_share": 0.3786954284717371,
      "mean_predicted_revenue_effect": 3.0546288579492105,
      "observed_conversion_ate": 0.02433115230825153
    },
    {
      "segment": "Loyal Members",
      "recommended_budget": 23925.967304418344,
      "budget_share": 0.23925967304418344,
      "mean_predicted_revenue_effect": 0.4163368981118223,
      "observed_conversion_ate": 0.0009719676784479825
    },
    {
      "segment": "Young Professionals",
      "recommended_budget": 14055.217732693804,
      "budget_share": 0.14055217732693803,
      "mean_predicted_revenue_effect": 1.1213857273411545,
      "observed_conversion_ate": 0.015374774631456145
    }
  ],
  "suppressed_segments": [
    {
      "segment": "Lapsed Users",
      "recommended_budget": 0.0,
      "mean_predicted_revenue_effect": 0.7045421594865333,
      "observed_conversion_ate": -0.008005408097915038
    }
  ]
}
```

## What That Output Means

- Budget is no longer being assigned from raw conversion rates or fixed heuristics.
- The allocator is using:
  - Phase 4 conversion targeting to decide which segments remain eligible
  - the revenue uplift model to size the spend opportunity
- `High Intent Returners` gets the largest share because it has the strongest positive revenue mass in the holdout scores.
- `Loyal Members` still receives a large allocation even though its conversion uplift is modest, because the revenue model sees meaningful positive value opportunity there.
- `Lapsed Users` stays at zero incremental budget because the conversion rollup marked it as a suppression segment.

That last point is important:

- this slice does not blindly optimize on revenue scores alone
- it keeps the conversion-based targeting gate in place

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_budget_allocation.py -q
```

Current output:

```text
..                                                                       [100%]
2 passed in 7.79s
```

Full backend test output after this slice:

```text
........................................................                 [100%]
56 passed in 28.19s
```

## Where to Inspect the Code

- budget allocator: `backend/src/primelift/decision/budget_allocation.py`
- budget CLI: `backend/scripts/run_budget_allocation.py`
- focused tests: `backend/tests/test_budget_allocation.py`

## Short Conclusion

This second revised Phase 5 slice is complete because the repository now has:

- model-driven segment budget allocation
- revenue-weighted opportunity sizing
- zero-budget suppression recommendations
- terminal-verifiable artifacts
- passing automated tests

The next Phase 5 slice should be `DRPolicyTree`.
