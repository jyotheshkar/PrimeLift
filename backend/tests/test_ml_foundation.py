"""Tests for the revised Phase 1 ML-ready foundation."""

from __future__ import annotations

from pathlib import Path

from primelift.evaluation import get_default_evaluation_blueprints
from primelift.features import build_feature_schema_summary
from primelift.models import get_default_model_blueprints
from primelift.utils.artifacts import build_artifact_manifest
from primelift.utils.paths import (
    ARTIFACTS_ROOT,
    FEATURE_ARTIFACTS_DIR,
    METRICS_ARTIFACTS_DIR,
    MODEL_ARTIFACTS_DIR,
    REPORT_ARTIFACTS_DIR,
    ensure_project_directories,
)


def test_ml_dependencies_are_importable() -> None:
    """The revised Phase 1 environment should load the main ML libraries."""

    import econml  # noqa: F401
    import lightgbm  # noqa: F401


def test_feature_schema_summary_matches_expected_contract() -> None:
    """The Phase 1 feature schema should expose the model-ready column groups."""

    summary = build_feature_schema_summary()

    assert summary.treatment_columns == ["treatment"]
    assert summary.outcome_columns == ["conversion", "revenue"]
    assert summary.total_model_feature_count == len(summary.model_feature_columns)
    assert "segment" in summary.categorical_feature_columns
    assert "prior_engagement_score" in summary.numeric_feature_columns


def test_model_blueprint_registry_contains_core_planned_models() -> None:
    """The model registry should expose the agreed causal ML stack."""

    blueprint_names = {blueprint.name for blueprint in get_default_model_blueprints()}

    assert {
        "ate_baseline",
        "xlearner_conversion",
        "drlearner_conversion",
        "drlearner_revenue",
        "causal_forest_conversion",
        "dr_policy_tree",
        "dr_policy_forest",
        "lightgbm_classifier",
        "lightgbm_regressor",
    }.issubset(blueprint_names)


def test_evaluation_blueprints_cover_model_and_policy_reporting() -> None:
    """The evaluation scaffold should cover the main planned reporting outputs."""

    blueprint_names = {blueprint.name for blueprint in get_default_evaluation_blueprints()}

    assert "model_comparison_report" in blueprint_names
    assert "uplift_decile_report" in blueprint_names
    assert "policy_recommendation_report" in blueprint_names


def test_artifact_directories_are_available() -> None:
    """The revised Phase 1 scaffold should materialize the main artifact directories."""

    ensure_project_directories()
    manifest = build_artifact_manifest()

    expected_directories = [
        ARTIFACTS_ROOT,
        MODEL_ARTIFACTS_DIR,
        REPORT_ARTIFACTS_DIR,
        METRICS_ARTIFACTS_DIR,
        FEATURE_ARTIFACTS_DIR,
    ]

    for directory in expected_directories:
        assert Path(directory).exists()
        assert Path(directory).is_dir()

    assert manifest.model_artifacts_dir.endswith("artifacts\\models")
