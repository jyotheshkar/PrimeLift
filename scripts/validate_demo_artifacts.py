#!/usr/bin/env python3
"""Check committed demonstration reports without importing ML dependencies.

This is an artifact consistency check, not model reproduction or a security audit.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

REPORT_NAMES = (
    "phase3_model_comparison_report.json",
    "phase4_conversion_decile_report.json",
    "phase4_conversion_rollup_report.json",
    "phase4_conversion_validation_summary.json",
    "phase5_budget_allocation_report.json",
    "phase5_decision_closeout_report.json",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant: {value}")


def check_finite(value: object, location: str) -> None:
    if isinstance(value, float):
        require(math.isfinite(value), f"{location}: non-finite number")
    elif isinstance(value, dict):
        for key, item in value.items():
            check_finite(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            check_finite(item, f"{location}[{index}]")


def near(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-7)


def validate_reports(metrics_dir: Path) -> None:
    reports = []
    for name in REPORT_NAMES:
        payload = json.loads(
            (metrics_dir / name).read_text(encoding="utf-8"),
            parse_constant=reject_constant,
        )
        require(isinstance(payload, dict), f"{name}: expected a JSON object")
        check_finite(payload, name)
        reports.append(payload)

    comparison, deciles, rollups, validation, budget, closeout = reports
    split = comparison["comparison_split"]
    champions = {}
    for outcome in ("conversion", "revenue"):
        ranked = comparison[f"{outcome}_comparison"]
        champion = ranked["champion_model_name"]
        require(ranked["outcome_column"] == outcome, f"{outcome}: outcome mismatch")
        require(ranked["split_name"] == split, f"{outcome}: split mismatch")
        names = [row["model_name"] for row in ranked["ranked_models"]]
        require(len(names) == len(set(names)), f"{outcome}: duplicate model names")
        require(champion in names, f"{outcome}: champion absent from ranking")
        champions[outcome] = champion

    for name, report in zip(REPORT_NAMES[1:4], (deciles, rollups, validation)):
        require(report["model_name"] == champions["conversion"], f"{name}: model mismatch")
        require(report["split_name"] == split, f"{name}: split mismatch")
        require(report["outcome_column"] == "conversion", f"{name}: outcome mismatch")
        require(
            near(report["overall_observed_ate"], deciles["overall_observed_ate"]),
            f"{name}: overall ATE mismatch",
        )

    rows = deciles["deciles"]
    ranks = [row["decile_rank"] for row in rows]
    require(
        sorted(ranks) == list(range(1, deciles["decile_count"] + 1)),
        "Decile ranks must be unique and cover 1..decile_count",
    )
    valid_ranks = set(ranks)
    for key in ("top_persuadable_deciles", "suppression_candidate_deciles"):
        require(set(deciles[key]) <= valid_ranks, f"{key}: unknown decile")
        require(deciles[key] == validation[key], f"{key}: validation mismatch")
    for key in ("top_decile_observed_ate", "bottom_decile_observed_ate"):
        require(near(deciles[key], validation[key]), f"{key}: validation mismatch")

    require(budget["split_name"] == split, "Budget split mismatch")
    require(closeout["split_name"] == split, "Closeout split mismatch")
    require(budget["conversion_model_name"] == champions["conversion"], "Budget conversion model mismatch")
    require(budget["revenue_model_name"] == champions["revenue"], "Budget revenue model mismatch")
    allocated = budget["top_budget_segments"]
    suppressed = budget["suppressed_segments"]
    require(len(allocated) == budget["allocated_segment_count"], "Allocated segment count mismatch")
    require(len(suppressed) == budget["suppressed_segment_count"], "Suppressed segment count mismatch")
    names = [row["segment"] for row in allocated + suppressed]
    require(len(names) == len(set(names)), "A segment appears more than once in the budget")
    for row in allocated + suppressed:
        require(row["recommended_budget"] >= 0, "Negative recommended budget")
    for row in suppressed:
        require(near(row["recommended_budget"], 0), "Suppressed segment has nonzero budget")
    require(
        near(sum(row["recommended_budget"] for row in allocated), budget["allocated_budget"]),
        "Allocated segment budgets do not reconcile",
    )
    require(
        near(budget["allocated_budget"] + budget["unallocated_budget"], budget["total_budget"]),
        "Allocated and unallocated budget do not reconcile to total",
    )
    closeout_rows = closeout["prioritized_segments"] + closeout["suppressed_segments"]
    closeout_names = [row["segment"] for row in closeout_rows]
    require(
        len(closeout_names) == len(set(closeout_names)),
        "A segment appears more than once in the closeout",
    )
    for key, budget_rows in (("prioritized_segments", allocated), ("suppressed_segments", suppressed)):
        actual_rows = closeout[key]
        require(len(actual_rows) == len(budget_rows), f"Closeout {key} count mismatch")
        expected_by_segment = {row["segment"]: row for row in budget_rows}
        actual_by_segment = {row["segment"]: row for row in actual_rows}
        require(
            actual_by_segment.keys() == expected_by_segment.keys(),
            f"Closeout {key} differ from budget",
        )
        for segment, actual in actual_by_segment.items():
            expected = expected_by_segment[segment]
            require(
                near(actual["recommended_budget"], expected["recommended_budget"]),
                f"Closeout {segment}: recommended budget mismatch",
            )
            # Suppressed budget rows have no share field and allocate zero.
            expected_share = expected["budget_share"] if key == "prioritized_segments" else 0.0
            require(
                near(actual["budget_share"], expected_share),
                f"Closeout {segment}: budget share mismatch",
            )
    require(
        near(sum(row["recommended_budget"] for row in closeout_rows), budget["allocated_budget"]),
        "Closeout segment budgets do not reconcile",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metrics-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "artifacts" / "metrics",
    )
    args = parser.parse_args()
    try:
        validate_reports(args.metrics_dir)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Artifact validation failed: {error}")
        return 1
    print(f"Validated {len(REPORT_NAMES)} saved synthetic-demo reports; no training or data generation performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
