"""Script wrapper for the compact revised Phase 4 validation summary."""

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
from primelift.evaluation import generate_phase3_model_comparison_report, generate_phase4_validation_summary
from primelift.uplift import (
    generate_model_based_group_rollup_report,
    generate_model_based_uplift_decile_report,
)
from primelift.utils.paths import (
    DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH,
    DEFAULT_DATASET_PATH,
    DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH,
    DEFAULT_DRLEARNER_REVENUE_METRICS_PATH,
    DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH,
    DEFAULT_PREPROCESSING_MANIFEST_PATH,
    DEFAULT_XLEARNER_CONVERSION_METRICS_PATH,
)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate a compact validation summary for revised Phase 4."
    )
    parser.add_argument(
        "--decile-report",
        type=Path,
        default=DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH,
        help="Path to the Phase 4 decile report JSON.",
    )
    parser.add_argument(
        "--rollup-report",
        type=Path,
        default=DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH,
        help="Path to the Phase 4 rollup report JSON.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH,
        help="Path where the validation summary JSON will be written.",
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


def _ensure_phase4_reports_exist(decile_report_path: Path, rollup_report_path: Path) -> None:
    """Create the prerequisite Phase 3 and Phase 4 reports if they are missing."""

    _ensure_prepared_data_exists(DEFAULT_PREPROCESSING_MANIFEST_PATH)

    if not DEFAULT_XLEARNER_CONVERSION_METRICS_PATH.exists():
        train_xlearner_conversion_model(prepared_manifest_path=DEFAULT_PREPROCESSING_MANIFEST_PATH)
    if not DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH.exists():
        train_drlearner_conversion_model(prepared_manifest_path=DEFAULT_PREPROCESSING_MANIFEST_PATH)
    if not DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH.exists():
        train_causal_forest_conversion_model(prepared_manifest_path=DEFAULT_PREPROCESSING_MANIFEST_PATH)
    if not DEFAULT_DRLEARNER_REVENUE_METRICS_PATH.exists():
        train_drlearner_revenue_model(prepared_manifest_path=DEFAULT_PREPROCESSING_MANIFEST_PATH)

    if not DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH.exists():
        generate_phase3_model_comparison_report(
            conversion_report_paths=[
                DEFAULT_XLEARNER_CONVERSION_METRICS_PATH,
                DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH,
                DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH,
            ],
            revenue_report_paths=[DEFAULT_DRLEARNER_REVENUE_METRICS_PATH],
            comparison_split="test",
            output_path=DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
        )

    if not decile_report_path.exists():
        generate_model_based_uplift_decile_report(
            comparison_report_path=DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
            outcome_column="conversion",
            split_name="test",
            output_report_path=decile_report_path,
        )

    if not rollup_report_path.exists():
        generate_model_based_group_rollup_report(
            comparison_report_path=DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
            outcome_column="conversion",
            split_name="test",
            output_report_path=rollup_report_path,
        )


def main() -> None:
    """Generate the compact revised Phase 4 validation summary."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    _ensure_phase4_reports_exist(args.decile_report, args.rollup_report)

    report = generate_phase4_validation_summary(
        decile_report_path=args.decile_report,
        rollup_report_path=args.rollup_report,
        output_report_path=args.output_path,
    )
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
