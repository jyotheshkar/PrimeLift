"""Script wrapper for revised Phase 2 model-ready dataset preparation."""

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
from primelift.utils.paths import DEFAULT_DATASET_PATH


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Prepare train, validation, and test model-ready datasets for PrimeLift."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to the raw dataset CSV.",
    )
    parser.add_argument(
        "--train-size",
        type=float,
        default=0.70,
        help="Train split fraction.",
    )
    parser.add_argument(
        "--validation-size",
        type=float,
        default=0.15,
        help="Validation split fraction.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.15,
        help="Test split fraction.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for deterministic splitting.",
    )
    return parser


def main() -> None:
    """Prepare and save the model-ready split datasets."""

    parser = _build_argument_parser()
    args = parser.parse_args()

    if not args.input.exists():
        generate_and_save_default_dataset()

    dataset = load_dataset(args.input)
    summary = prepare_model_ready_datasets(
        dataset=dataset,
        input_dataset_path=args.input,
        train_size=args.train_size,
        validation_size=args.validation_size,
        test_size=args.test_size,
        random_seed=args.random_seed,
    )
    print(json.dumps(summary.model_dump(), indent=2))


if __name__ == "__main__":
    main()
