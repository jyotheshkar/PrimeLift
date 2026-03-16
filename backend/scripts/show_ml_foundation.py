"""Script wrapper for verifying the revised Phase 1 ML-ready foundation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from primelift.evaluation import get_default_evaluation_blueprints
from primelift.features import build_feature_schema_summary
from primelift.models import get_default_model_blueprints
from primelift.utils.artifacts import build_artifact_manifest
from primelift.utils.paths import ensure_project_directories


def main() -> None:
    """Print the Phase 1 ML scaffold summary as JSON."""

    ensure_project_directories()
    payload = {
        "feature_schema": build_feature_schema_summary().model_dump(),
        "model_blueprints": [
            blueprint.model_dump() for blueprint in get_default_model_blueprints()
        ],
        "evaluation_blueprints": [
            blueprint.model_dump() for blueprint in get_default_evaluation_blueprints()
        ],
        "artifact_manifest": build_artifact_manifest().model_dump(),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
