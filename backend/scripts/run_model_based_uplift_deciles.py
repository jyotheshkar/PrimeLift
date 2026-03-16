"""Script wrapper for the first revised Phase 4 model-based uplift slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from primelift.causal import (
    train_causal_forest_conversion_model,
    train_drlearner_conversion_model,
    train_drlearner_revenue_model,
    train_xlearner_conversion_model,
)
from primelift.data.generator import generate_and_save_default_dataset
from primelift.data.preparation import prepare_model_ready_datasets
from primelift.data.summary import load_dataset
from primelift.evaluation import generate_phase3_model_comparison_report
from primelift.uplift import generate_model_based_uplift_decile_report
from primelift.utils.paths import (
    DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH,
    DEFAULT_DATASET_PATH,
    DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH,
    DEFAULT_DRLEARNER_REVENUE_METRICS_PATH,
    DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_SCORED_VIEW_PATH,
    DEFAULT_PREPROCESSING_MANIFEST_PATH,
    DEFAULT_XLEARNER_CONVERSION_METRICS_PATH,
)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate model-based uplift deciles using the selected Phase 3 champion."
    )
    parser.add_argument(
        "--comparison-report",
        type=Path,
        default=DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
        help="Path to the Phase 3 model comparison report.",
    )
    parser.add_argument(
        "--outcome",
        type=str,
        default="conversion",
        choices=("conversion", "revenue"),
        help="Outcome to analyze with the selected Phase 3 champion.",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        choices=("validation", "test"),
        help="Holdout split to bucket into uplift deciles.",
    )
    parser.add_argument(
        "--deciles",
        type=int,
        default=10,
        help="Number of uplift ranking buckets to create.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH,
        help="Path where the decile summary JSON will be written.",
    )
    parser.add_argument(
        "--scored-view",
        type=Path,
        default=DEFAULT_PHASE4_CONVERSION_SCORED_VIEW_PATH,
        help="Path where the scored dataset view with deciles will be written.",
    )
    return parser


def _ensure_prepared_data_exists(prepared_manifest: Path) -> None:
    """Create the raw and prepared dataset assets if they do not already exist."""

    if prepared_manifest.exists():
        return

    if not DEFAULT_DATASET_PATH.exists():
        generate_and_save_default_dataset()

    raw_dataset = load_dataset(DEFAULT_DATASET_PATH)
    prepare_model_ready_datasets(dataset=raw_dataset, input_dataset_path=DEFAULT_DATASET_PATH)


def _ensure_phase3_artifacts_exist(prepared_manifest: Path, comparison_report_path: Path) -> None:
    """Create the required Phase 3 artifacts if they do not already exist."""

    _ensure_prepared_data_exists(prepared_manifest)

    if not DEFAULT_XLEARNER_CONVERSION_METRICS_PATH.exists():
        train_xlearner_conversion_model(prepared_manifest_path=prepared_manifest)
    if not DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH.exists():
        train_drlearner_conversion_model(prepared_manifest_path=prepared_manifest)
    if not DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH.exists():
        train_causal_forest_conversion_model(prepared_manifest_path=prepared_manifest)
    if not DEFAULT_DRLEARNER_REVENUE_METRICS_PATH.exists():
        train_drlearner_revenue_model(prepared_manifest_path=prepared_manifest)
    if not comparison_report_path.exists():
        generate_phase3_model_comparison_report(
            conversion_report_paths=[
                DEFAULT_XLEARNER_CONVERSION_METRICS_PATH,
                DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH,
                DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH,
            ],
            revenue_report_paths=[DEFAULT_DRLEARNER_REVENUE_METRICS_PATH],
            comparison_split="test",
            output_path=comparison_report_path,
        )


def main() -> None:
    """Generate the first revised Phase 4 model-based uplift report."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    _ensure_phase3_artifacts_exist(DEFAULT_PREPROCESSING_MANIFEST_PATH, args.comparison_report)

    report = generate_model_based_uplift_decile_report(
        comparison_report_path=args.comparison_report,
        outcome_column=args.outcome,
        split_name=args.split,
        decile_count=args.deciles,
        output_report_path=args.output_report,
        scored_view_path=args.scored_view,
    )
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
