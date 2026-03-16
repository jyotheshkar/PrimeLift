"""Script wrapper for the first Phase 5 decision-ranking slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from primelift.data.summary import load_dataset
from primelift.decision import build_positive_segment_ranking


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Run the first Phase 5 PrimeLift decision-ranking slice."
    )
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
        help="Number of bootstrap resamples per segment.",
    )
    parser.add_argument(
        "--confidence-level",
        type=float,
        default=0.95,
        help="Confidence level for segment uplift intervals.",
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
        help="Minimum treated and control count required before computing segment-level CIs.",
    )
    parser.add_argument(
        "--min-uplift",
        type=float,
        default=0.0,
        help="Minimum uplift threshold a segment must exceed to be ranked.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Maximum number of positive segments to return.",
    )
    return parser


def main() -> None:
    """Load the generated dataset and print the first Phase 5 ranking as JSON."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    dataset = load_dataset(args.input)
    ranking = build_positive_segment_ranking(
        dataset=dataset,
        bootstrap_samples=args.bootstrap_samples,
        confidence_level=args.confidence_level,
        random_seed=args.random_seed,
        min_group_size_per_arm=args.min_group_size_per_arm,
        min_uplift=args.min_uplift,
        top_n=args.top_n,
    )
    print(json.dumps(ranking.model_dump(), indent=2))


if __name__ == "__main__":
    main()
