"""Script wrapper for the final revised Phase 5 decision closeout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from primelift.decision import (
    generate_model_targeting_recommendations,
    generate_phase5_decision_closeout_report,
    generate_segment_budget_allocation,
    train_drpolicyforest_conversion_policy,
    train_drpolicytree_conversion_policy,
)
from primelift.utils.paths import (
    DEFAULT_DRPOLICYFOREST_CONVERSION_REPORT_PATH,
    DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH,
    DEFAULT_PHASE5_BUDGET_ALLOCATION_REPORT_PATH,
    DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH,
    DEFAULT_PHASE5_FINAL_SEGMENT_ACTIONS_PATH,
    DEFAULT_PHASE5_TARGETING_REPORT_PATH,
)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate the final revised Phase 5 decision closeout report."
    )
    parser.add_argument(
        "--targeting-report",
        type=Path,
        default=DEFAULT_PHASE5_TARGETING_REPORT_PATH,
        help="Path to the Phase 5 targeting report JSON.",
    )
    parser.add_argument(
        "--budget-report",
        type=Path,
        default=DEFAULT_PHASE5_BUDGET_ALLOCATION_REPORT_PATH,
        help="Path to the Phase 5 budget allocation report JSON.",
    )
    parser.add_argument(
        "--policy-tree-report",
        type=Path,
        default=DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH,
        help="Path to the DRPolicyTree report JSON.",
    )
    parser.add_argument(
        "--policy-forest-report",
        type=Path,
        default=DEFAULT_DRPOLICYFOREST_CONVERSION_REPORT_PATH,
        help="Path to the DRPolicyForest report JSON.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH,
        help="Path where the final Phase 5 closeout JSON will be written.",
    )
    parser.add_argument(
        "--final-segment-actions",
        type=Path,
        default=DEFAULT_PHASE5_FINAL_SEGMENT_ACTIONS_PATH,
        help="Path where the final segment action CSV will be written.",
    )
    return parser


def _ensure_phase5_artifacts_exist(
    *,
    targeting_report_path: Path,
    budget_report_path: Path,
    policy_tree_report_path: Path,
    policy_forest_report_path: Path,
) -> None:
    """Create missing Phase 5 artifacts using the earlier slices when possible."""

    if not targeting_report_path.exists():
        generate_model_targeting_recommendations(output_report_path=targeting_report_path)
    if not budget_report_path.exists():
        generate_segment_budget_allocation(output_report_path=budget_report_path)
    if not policy_tree_report_path.exists():
        train_drpolicytree_conversion_policy(output_report_path=policy_tree_report_path)
    if not policy_forest_report_path.exists():
        train_drpolicyforest_conversion_policy(
            output_report_path=policy_forest_report_path,
            policy_tree_report_path=policy_tree_report_path,
        )


def main() -> None:
    """Generate the final revised Phase 5 decision closeout report."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    _ensure_phase5_artifacts_exist(
        targeting_report_path=args.targeting_report,
        budget_report_path=args.budget_report,
        policy_tree_report_path=args.policy_tree_report,
        policy_forest_report_path=args.policy_forest_report,
    )

    report = generate_phase5_decision_closeout_report(
        targeting_report_path=args.targeting_report,
        budget_report_path=args.budget_report,
        policy_tree_report_path=args.policy_tree_report,
        policy_forest_report_path=args.policy_forest_report,
        output_report_path=args.output_report,
        final_segment_actions_path=args.final_segment_actions,
    )
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
