"""Script wrapper for running the completed Phase 4 segment uplift analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from primelift.data.summary import load_dataset
from primelift.uplift import analyze_default_uplift_dimensions


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(description="Run the PrimeLift Phase 4 uplift analysis.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/london_campaign_users_100k.csv"),
        help="Input dataset path.",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=200,
        help="Number of bootstrap resamples per group.",
    )
    parser.add_argument(
        "--confidence-level",
        type=float,
        default=0.95,
        help="Confidence level for group uplift intervals.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for bootstrap reproducibility.",
    )
    parser.add_argument(
        "--min-group-size-per-arm",
        type=int,
        default=25,
        help="Minimum treated and control count required before computing group-level CIs.",
    )
    return parser


def main() -> None:
    """Load the generated dataset and print Phase 4 uplift results as JSON."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    dataset = load_dataset(args.input)
    report = analyze_default_uplift_dimensions(
        dataset=dataset,
        bootstrap_samples=args.bootstrap_samples,
        confidence_level=args.confidence_level,
        random_seed=args.random_seed,
        min_group_size_per_arm=args.min_group_size_per_arm,
    )
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
