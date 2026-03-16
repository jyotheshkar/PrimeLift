"""Script wrapper for the revised Phase 5 DRPolicyForest conversion slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from primelift.data.generator import generate_and_save_default_dataset
from primelift.data.preparation import prepare_model_ready_datasets
from primelift.data.summary import load_dataset
from primelift.decision import (
    train_drpolicyforest_conversion_policy,
    train_drpolicytree_conversion_policy,
)
from primelift.utils.paths import (
    DEFAULT_DATASET_PATH,
    DEFAULT_DRPOLICYFOREST_CONVERSION_MODEL_PATH,
    DEFAULT_DRPOLICYFOREST_CONVERSION_REPORT_PATH,
    DEFAULT_DRPOLICYFOREST_CONVERSION_TEST_DECISIONS_PATH,
    DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH,
    DEFAULT_PREPROCESSING_MANIFEST_PATH,
)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Train the revised Phase 5 DRPolicyForest conversion policy."
    )
    parser.add_argument(
        "--raw-dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to the raw dataset CSV.",
    )
    parser.add_argument(
        "--prepared-manifest",
        type=Path,
        default=DEFAULT_PREPROCESSING_MANIFEST_PATH,
        help="Path to the prepared dataset manifest JSON.",
    )
    parser.add_argument(
        "--model-artifact",
        type=Path,
        default=DEFAULT_DRPOLICYFOREST_CONVERSION_MODEL_PATH,
        help="Path where the trained DRPolicyForest artifact will be written.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=DEFAULT_DRPOLICYFOREST_CONVERSION_REPORT_PATH,
        help="Path where the policy forest report JSON will be written.",
    )
    parser.add_argument(
        "--decisions-output",
        type=Path,
        default=DEFAULT_DRPOLICYFOREST_CONVERSION_TEST_DECISIONS_PATH,
        help="Path where the scored policy-forest decision CSV will be written.",
    )
    parser.add_argument(
        "--policy-tree-report",
        type=Path,
        default=DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH,
        help="Path to the DRPolicyTree report used as the challenger baseline.",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=200,
        help="Number of trees in the policy forest.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=6,
        help="Maximum depth for each policy tree in the forest.",
    )
    parser.add_argument(
        "--min-samples-split",
        type=int,
        default=800,
        help="Minimum sample count required to split an internal node.",
    )
    parser.add_argument(
        "--min-samples-leaf",
        type=int,
        default=300,
        help="Minimum sample count required in each leaf.",
    )
    parser.add_argument(
        "--max-samples",
        type=float,
        default=0.5,
        help="Bootstrap subsample share for each tree.",
    )
    parser.add_argument(
        "--cv",
        type=int,
        default=3,
        help="Cross-validation folds for DR nuisance estimation.",
    )
    parser.add_argument(
        "--honest",
        action="store_true",
        help="Enable honest splitting inside DRPolicyForest.",
    )
    return parser


def _ensure_prepared_data_exists(raw_dataset_path: Path, prepared_manifest_path: Path) -> None:
    """Create the raw dataset and prepared manifest if they do not already exist."""

    if not raw_dataset_path.exists():
        generate_and_save_default_dataset()
    if prepared_manifest_path.exists():
        return

    raw_dataset = load_dataset(raw_dataset_path)
    prepare_model_ready_datasets(dataset=raw_dataset, input_dataset_path=raw_dataset_path)


def _ensure_policy_tree_report_exists(
    *,
    raw_dataset_path: Path,
    prepared_manifest_path: Path,
    policy_tree_report_path: Path,
) -> None:
    """Create the policy-tree baseline report if it does not already exist."""

    if policy_tree_report_path.exists():
        return

    train_drpolicytree_conversion_policy(
        raw_dataset_path=raw_dataset_path,
        prepared_manifest_path=prepared_manifest_path,
        output_report_path=policy_tree_report_path,
    )


def main() -> None:
    """Train the revised Phase 5 DRPolicyForest conversion policy."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    _ensure_prepared_data_exists(args.raw_dataset, args.prepared_manifest)
    _ensure_policy_tree_report_exists(
        raw_dataset_path=args.raw_dataset,
        prepared_manifest_path=args.prepared_manifest,
        policy_tree_report_path=args.policy_tree_report,
    )

    report = train_drpolicyforest_conversion_policy(
        raw_dataset_path=args.raw_dataset,
        prepared_manifest_path=args.prepared_manifest,
        model_artifact_path=args.model_artifact,
        output_report_path=args.output_report,
        decisions_output_path=args.decisions_output,
        policy_tree_report_path=args.policy_tree_report,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_split=args.min_samples_split,
        min_samples_leaf=args.min_samples_leaf,
        max_samples=args.max_samples,
        cv=args.cv,
        honest=args.honest,
    )
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
