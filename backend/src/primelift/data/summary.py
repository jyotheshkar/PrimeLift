"""Lightweight summary helpers for generated campaign datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from primelift.utils.paths import DEFAULT_DATASET_PATH


def build_dataset_summary(dataset: pd.DataFrame) -> dict[str, object]:
    """Build a compact operational summary for quick dataset inspection."""

    return {
        "row_count": int(len(dataset)),
        "columns": list(dataset.columns),
        "treatment_control_split": {
            str(key): int(value)
            for key, value in dataset["treatment"].value_counts().sort_index().items()
        },
        "conversion_rate": round(float(dataset["conversion"].mean()), 4),
        "segment_counts": {
            key: int(value) for key, value in dataset["segment"].value_counts().items()
        },
        "borough_counts": {
            key: int(value)
            for key, value in dataset["london_borough"].value_counts().head(10).items()
        },
    }


def load_dataset(dataset_path: Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    """Load a CSV dataset from disk."""

    return pd.read_csv(dataset_path)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(description="Summarise a generated PrimeLift dataset.")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to the generated CSV dataset.",
    )
    return parser


def main() -> None:
    """CLI entrypoint for dataset summarisation."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    dataset = load_dataset(args.input)
    summary = build_dataset_summary(dataset)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
