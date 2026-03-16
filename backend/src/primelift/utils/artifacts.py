"""Helpers for artifact directory planning in the ML-ready foundation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from primelift.utils.paths import (
    ARTIFACTS_ROOT,
    FEATURE_ARTIFACTS_DIR,
    METRICS_ARTIFACTS_DIR,
    MODEL_ARTIFACTS_DIR,
    REPORT_ARTIFACTS_DIR,
)


class ArtifactManifest(BaseModel):
    """Serializable manifest of the main artifact directories used by the project."""

    model_config = ConfigDict(frozen=True)

    artifacts_root: str
    model_artifacts_dir: str
    report_artifacts_dir: str
    metrics_artifacts_dir: str
    feature_artifacts_dir: str


def build_artifact_manifest() -> ArtifactManifest:
    """Build the artifact directory manifest used by the ML-ready scaffold."""

    return ArtifactManifest(
        artifacts_root=str(ARTIFACTS_ROOT),
        model_artifacts_dir=str(MODEL_ARTIFACTS_DIR),
        report_artifacts_dir=str(REPORT_ARTIFACTS_DIR),
        metrics_artifacts_dir=str(METRICS_ARTIFACTS_DIR),
        feature_artifacts_dir=str(FEATURE_ARTIFACTS_DIR),
    )
