"""Script wrapper for inspecting revised Phase 2 prepared dataset outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from primelift.data.preparation import load_prepared_dataset_summary
from primelift.utils.paths import DEFAULT_PREPROCESSING_MANIFEST_PATH


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Summarize the prepared PrimeLift model-ready datasets."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_PREPROCESSING_MANIFEST_PATH,
        help="Path to the prepared dataset manifest JSON.",
    )
    return parser


def main() -> None:
    """Load the prepared-data manifest and print it as JSON."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    summary = load_prepared_dataset_summary(args.manifest)
    print(json.dumps(summary.model_dump(), indent=2))


if __name__ == "__main__":
    main()
