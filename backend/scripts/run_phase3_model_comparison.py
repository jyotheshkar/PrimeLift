"""Script wrapper for the revised Phase 3 model comparison slice."""

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
from primelift.utils.paths import (
    DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH,
    DEFAULT_DATASET_PATH,
    DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH,
    DEFAULT_DRLEARNER_REVENUE_METRICS_PATH,
    DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
    DEFAULT_PREPROCESSING_MANIFEST_PATH,
    DEFAULT_XLEARNER_CONVERSION_METRICS_PATH,
)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate the revised Phase 3 model comparison report."
    )
    parser.add_argument(
        "--prepared-manifest",
        type=Path,
        default=DEFAULT_PREPROCESSING_MANIFEST_PATH,
        help="Path to the prepared dataset manifest.",
    )
    parser.add_argument(
        "--comparison-split",
        type=str,
        default="test",
        choices=("validation", "test"),
        help="Holdout split used for comparison.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
        help="Path where the comparison report JSON will be written.",
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


def _ensure_phase3_reports_exist(prepared_manifest: Path) -> None:
    """Train any missing Phase 3 models so the comparison report can be generated."""

    _ensure_prepared_data_exists(prepared_manifest)

    if not DEFAULT_XLEARNER_CONVERSION_METRICS_PATH.exists():
        train_xlearner_conversion_model(prepared_manifest_path=prepared_manifest)
    if not DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH.exists():
        train_drlearner_conversion_model(prepared_manifest_path=prepared_manifest)
    if not DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH.exists():
        train_causal_forest_conversion_model(prepared_manifest_path=prepared_manifest)
    if not DEFAULT_DRLEARNER_REVENUE_METRICS_PATH.exists():
        train_drlearner_revenue_model(prepared_manifest_path=prepared_manifest)


def main() -> None:
    """Generate the Phase 3 model comparison report."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    _ensure_phase3_reports_exist(args.prepared_manifest)

    report = generate_phase3_model_comparison_report(
        conversion_report_paths=[
            DEFAULT_XLEARNER_CONVERSION_METRICS_PATH,
            DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH,
            DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH,
        ],
        revenue_report_paths=[DEFAULT_DRLEARNER_REVENUE_METRICS_PATH],
        comparison_split=args.comparison_split,
        output_path=args.output_path,
    )
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
