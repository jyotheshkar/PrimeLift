# Phase 4 Segment Uplift Notes

This document explains what was implemented for Phase 4, what it adds on top of the Phase 3 analysis, and what terminal output you should see when you run the grouped uplift analysis yourself.

## Phase 4 Scope

Phase 4 required grouped uplift analysis by important dimensions such as:

- segment
- geography
- device_type
- channel

In this repository, geography is implemented as:

- `london_borough`

For each group, the analysis now computes:

- treated conversion rate
- control conversion rate
- uplift
- group size
- confidence indicator

The results are sorted by uplift descending within each dimension.

## Files Added or Updated

- `backend/src/primelift/uplift/segment_analysis.py`
- `backend/src/primelift/uplift/__init__.py`
- `backend/scripts/run_segment_uplift_analysis.py`
- `backend/tests/test_segment_uplift.py`

## What Was Implemented

### 1. Grouped uplift analysis by business dimensions

Implemented in:

- `analyze_group_uplift(...)`
- `analyze_default_uplift_dimensions(...)`

The default grouped analysis covers:

- `segment`
- `london_borough`
- `device_type`
- `channel`

### 2. Per-group metrics

Each result includes:

- treated conversion rate
- control conversion rate
- uplift
- relative uplift
- treated and control counts
- total group size

### 3. Confidence indicator

Each group is labeled as:

- `positive`
- `negative`
- `uncertain`
- `insufficient_data`

The indicator is based on the group-level bootstrap interval when enough treated and control users exist.

## Important Data Impact Note

Phase 4 does **not** modify the raw CSV dataset.

It does not add new columns to:

- `data/raw/london_campaign_users_100k.csv`

Instead, it reads the existing dataset and produces grouped uplift analysis output in the terminal.

So the correct sequence is:

- Phase 2 created the dataset
- Phase 3 measured overall treatment effect
- Phase 4 identifies where uplift is strongest or weakest by group

## How to Run Phase 4

Activate the environment:

```powershell
.venv\Scripts\Activate
```

Then run:

```powershell
python backend/scripts/run_segment_uplift_analysis.py --bootstrap-samples 120
```

## Terminal Proof: Example Output Highlights

The full command prints a long JSON report. These are the most important current highlights from the generated 100k London dataset.

### Top segment

```json
{
  "group_column": "segment",
  "group_value": "High Intent Returners",
  "outcome_column": "conversion",
  "treated_conversion_rate": 0.2507496787091247,
  "control_conversion_rate": 0.22599112637755833,
  "uplift": 0.024758552331566347,
  "relative_uplift": 0.10955541807514507,
  "group_size": 13990,
  "treated_count": 7003,
  "control_count": 6987,
  "ci_lower": 0.009610957486763575,
  "ci_upper": 0.04081263573866324,
  "confidence_level": 0.95,
  "bootstrap_samples": 120,
  "confidence_indicator": "positive"
}
```

### Lowest segment

```json
{
  "group_column": "segment",
  "group_value": "Lapsed Users",
  "outcome_column": "conversion",
  "treated_conversion_rate": 0.008034145116746171,
  "control_conversion_rate": 0.016441717791411042,
  "uplift": -0.008407572674664871,
  "relative_uplift": -0.5113560992426769,
  "group_size": 8058,
  "treated_count": 3983,
  "control_count": 4075,
  "ci_lower": -0.012624030965961163,
  "ci_upper": -0.004178077381016561,
  "confidence_level": 0.95,
  "bootstrap_samples": 120,
  "confidence_indicator": "negative"
}
```

### Top channel

```json
{
  "group_column": "channel",
  "group_value": "generic_search",
  "outcome_column": "conversion",
  "treated_conversion_rate": 0.13748019017432647,
  "control_conversion_rate": 0.11135767601371797,
  "uplift": 0.026122514160608498,
  "relative_uplift": 0.23458207009807305,
  "group_size": 10005,
  "treated_count": 5048,
  "control_count": 4957,
  "ci_lower": 0.010174708315602925,
  "ci_upper": 0.0427707723825853,
  "confidence_level": 0.95,
  "bootstrap_samples": 120,
  "confidence_indicator": "positive"
}
```

## What That Output Means

- `High Intent Returners` is currently the strongest positive segment on the dataset.
- `Lapsed Users` is currently a negative-response segment.
- `generic_search` is currently the strongest positive channel.

That is the direct Phase 4 proof that the repository can identify where treatment impact is strongest and weakest.

## Test Proof

Run:

```powershell
python -m pytest backend/tests/test_segment_uplift.py -q
```

Current output:

```text
....                                                                     [100%]
4 passed in 1.37s
```

## What Those Tests Cover

The Phase 4 tests validate:

- sorting by uplift descending
- correct positive and negative confidence indicators on toy data
- handling of small groups with insufficient data
- multi-dimension default report generation
- rejection of missing group columns

## Where to Inspect the Code

- Core implementation: `backend/src/primelift/uplift/segment_analysis.py`
- Runnable analysis script: `backend/scripts/run_segment_uplift_analysis.py`
- Phase 4 tests: `backend/tests/test_segment_uplift.py`

## Confidence Indicator Meaning

- `positive`: confidence interval is entirely above zero
- `negative`: confidence interval is entirely below zero
- `uncertain`: confidence interval crosses zero
- `insufficient_data`: the group does not have enough treated and control users for CI computation

## Short Conclusion

Phase 4 is complete because the repository now has:

- grouped uplift analysis across the key business dimensions
- uplift ranking sorted descending
- confidence indicators for each group
- runnable JSON output from the CLI
- passing automated tests
