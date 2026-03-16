"""Script wrapper for the revised Phase 3 CausalForestDML conversion slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from primelift.causal import train_causal_forest_conversion_model
from primelift.data.generator import generate_and_save_default_dataset
from primelift.data.preparation import prepare_model_ready_datasets
from primelift.data.summary import load_dataset
from primelift.utils.paths import DEFAULT_DATASET_PATH, DEFAULT_PREPROCESSING_MANIFEST_PATH


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Train and score the revised Phase 3 CausalForestDML conversion model."
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
        "--outcome-estimators",
        type=int,
        default=120,
        help="Number of trees in the nuisance outcome model.",
    )
    parser.add_argument(
        "--treatment-estimators",
        type=int,
        default=120,
        help="Number of trees in the nuisance treatment model.",
    )
    parser.add_argument(
        "--forest-estimators",
        type=int,
        default=80,
        help="Number of causal forest trees.",
    )
    parser.add_argument(
        "--min-samples-leaf",
        type=int,
        default=40,
        help="Minimum samples per leaf in the causal forest.",
    )
    parser.add_argument(
        "--max-samples",
        type=float,
        default=0.45,
        help="Subsample fraction per causal forest tree.",
    )
    parser.add_argument(
        "--cv",
        type=int,
        default=2,
        help="Cross-fitting folds for nuisance estimation.",
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
    """Train and evaluate the CausalForestDML conversion model."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    _ensure_prepared_data_exists(args.prepared_manifest)

    report = train_causal_forest_conversion_model(
        prepared_manifest_path=args.prepared_manifest,
        random_seed=args.random_seed,
        model_y_params={"n_estimators": args.outcome_estimators},
        model_t_params={"n_estimators": args.treatment_estimators},
        n_estimators=args.forest_estimators,
        min_samples_leaf=args.min_samples_leaf,
        max_samples=args.max_samples,
        cv=args.cv,
    )
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
