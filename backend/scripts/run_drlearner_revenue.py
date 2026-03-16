"""Script wrapper for the revised Phase 3 DRLearner revenue slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from primelift.causal import train_drlearner_revenue_model
from primelift.data.generator import generate_and_save_default_dataset
from primelift.data.preparation import prepare_model_ready_datasets
from primelift.data.summary import load_dataset
from primelift.utils.paths import DEFAULT_DATASET_PATH, DEFAULT_PREPROCESSING_MANIFEST_PATH


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Train and score the revised Phase 3 DRLearner revenue model."
    )
    parser.add_argument(
        "--prepared-manifest",
        type=Path,
        default=DEFAULT_PREPROCESSING_MANIFEST_PATH,
        help="Path to the prepared dataset manifest.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducible training.",
    )
    parser.add_argument(
        "--propensity-estimators",
        type=int,
        default=120,
        help="Number of trees in the DRLearner propensity model.",
    )
    parser.add_argument(
        "--regression-estimators",
        type=int,
        default=120,
        help="Number of trees in the DRLearner revenue nuisance model.",
    )
    parser.add_argument(
        "--final-estimators",
        type=int,
        default=80,
        help="Number of trees in the DRLearner final stage model.",
    )
    parser.add_argument(
        "--cv",
        type=int,
        default=3,
        help="Cross-fitting folds for DRLearner.",
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


def main() -> None:
    """Train and evaluate the DRLearner revenue model."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    _ensure_prepared_data_exists(args.prepared_manifest)

    report = train_drlearner_revenue_model(
        prepared_manifest_path=args.prepared_manifest,
        random_seed=args.random_seed,
        propensity_model_params={"n_estimators": args.propensity_estimators},
        regression_model_params={"n_estimators": args.regression_estimators},
        final_model_params={"n_estimators": args.final_estimators},
        cv=args.cv,
    )
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
