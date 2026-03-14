"""Script wrapper for running the completed Phase 3 causal analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from primelift.causal import analyze_average_treatment_effect, estimate_revenue_lift
from primelift.data.summary import load_dataset


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(description="Run the PrimeLift Phase 3 causal analysis.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/london_campaign_users_100k.csv"),
        help="Input dataset path.",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=1000,
        help="Number of bootstrap resamples to use for confidence intervals.",
    )
    parser.add_argument(
        "--confidence-level",
        type=float,
        default=0.95,
        help="Confidence level for the bootstrap interval.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for bootstrap reproducibility.",
    )
    return parser


def main() -> None:
    """Load the generated dataset and print Phase 3 causal results as JSON."""

    parser = _build_argument_parser()
    args = parser.parse_args()

    dataset = load_dataset(args.input)
    conversion_analysis = analyze_average_treatment_effect(
        dataset,
        outcome_column="conversion",
        bootstrap_samples=args.bootstrap_samples,
        confidence_level=args.confidence_level,
        random_seed=args.random_seed,
    )
    revenue_analysis = estimate_revenue_lift(
        dataset,
        bootstrap_samples=args.bootstrap_samples,
        confidence_level=args.confidence_level,
        random_seed=args.random_seed,
    )

    print(
        json.dumps(
            {
                "conversion_analysis": conversion_analysis.model_dump(),
                "revenue_analysis": revenue_analysis.model_dump(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
