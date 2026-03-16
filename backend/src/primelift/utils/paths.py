"""Path helpers shared across the backend slice."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = REPO_ROOT / "data"
RAW_DATA_DIR = DATA_ROOT / "raw"
PROCESSED_DATA_DIR = DATA_ROOT / "processed"
DOCS_DIR = REPO_ROOT / "docs"
ARTIFACTS_ROOT = REPO_ROOT / "artifacts"
MODEL_ARTIFACTS_DIR = ARTIFACTS_ROOT / "models"
REPORT_ARTIFACTS_DIR = ARTIFACTS_ROOT / "reports"
METRICS_ARTIFACTS_DIR = ARTIFACTS_ROOT / "metrics"
FEATURE_ARTIFACTS_DIR = ARTIFACTS_ROOT / "features"
DEFAULT_DATASET_PATH = RAW_DATA_DIR / "london_campaign_users_100k.csv"
DEFAULT_DATASET_VIEW_PATH = RAW_DATA_DIR / "london_campaign_users_100k_view.html"
DEFAULT_DATA_DICTIONARY_PATH = DOCS_DIR / "london_campaign_users_data_dictionary.md"
DEFAULT_PREPARED_TRAIN_PATH = PROCESSED_DATA_DIR / "london_campaign_users_train_model_ready.csv"
DEFAULT_PREPARED_VALIDATION_PATH = (
    PROCESSED_DATA_DIR / "london_campaign_users_validation_model_ready.csv"
)
DEFAULT_PREPARED_TEST_PATH = PROCESSED_DATA_DIR / "london_campaign_users_test_model_ready.csv"
DEFAULT_PREPROCESSOR_ARTIFACT_PATH = FEATURE_ARTIFACTS_DIR / "feature_preprocessor.joblib"
DEFAULT_PREPROCESSING_MANIFEST_PATH = FEATURE_ARTIFACTS_DIR / "prepared_dataset_manifest.json"
DEFAULT_XLEARNER_CONVERSION_MODEL_PATH = MODEL_ARTIFACTS_DIR / "xlearner_conversion.joblib"
DEFAULT_XLEARNER_CONVERSION_METRICS_PATH = (
    METRICS_ARTIFACTS_DIR / "xlearner_conversion_training_report.json"
)
DEFAULT_XLEARNER_CONVERSION_VALIDATION_SCORES_PATH = (
    REPORT_ARTIFACTS_DIR / "xlearner_conversion_validation_scores.csv"
)
DEFAULT_XLEARNER_CONVERSION_TEST_SCORES_PATH = (
    REPORT_ARTIFACTS_DIR / "xlearner_conversion_test_scores.csv"
)
DEFAULT_DRLEARNER_CONVERSION_MODEL_PATH = MODEL_ARTIFACTS_DIR / "drlearner_conversion.joblib"
DEFAULT_DRLEARNER_CONVERSION_METRICS_PATH = (
    METRICS_ARTIFACTS_DIR / "drlearner_conversion_training_report.json"
)
DEFAULT_DRLEARNER_CONVERSION_VALIDATION_SCORES_PATH = (
    REPORT_ARTIFACTS_DIR / "drlearner_conversion_validation_scores.csv"
)
DEFAULT_DRLEARNER_CONVERSION_TEST_SCORES_PATH = (
    REPORT_ARTIFACTS_DIR / "drlearner_conversion_test_scores.csv"
)
DEFAULT_DRLEARNER_REVENUE_MODEL_PATH = MODEL_ARTIFACTS_DIR / "drlearner_revenue.joblib"
DEFAULT_DRLEARNER_REVENUE_METRICS_PATH = (
    METRICS_ARTIFACTS_DIR / "drlearner_revenue_training_report.json"
)
DEFAULT_DRLEARNER_REVENUE_VALIDATION_SCORES_PATH = (
    REPORT_ARTIFACTS_DIR / "drlearner_revenue_validation_scores.csv"
)
DEFAULT_DRLEARNER_REVENUE_TEST_SCORES_PATH = (
    REPORT_ARTIFACTS_DIR / "drlearner_revenue_test_scores.csv"
)
DEFAULT_CAUSAL_FOREST_CONVERSION_MODEL_PATH = (
    MODEL_ARTIFACTS_DIR / "causal_forest_conversion.joblib"
)
DEFAULT_CAUSAL_FOREST_CONVERSION_METRICS_PATH = (
    METRICS_ARTIFACTS_DIR / "causal_forest_conversion_training_report.json"
)
DEFAULT_CAUSAL_FOREST_CONVERSION_VALIDATION_SCORES_PATH = (
    REPORT_ARTIFACTS_DIR / "causal_forest_conversion_validation_scores.csv"
)
DEFAULT_CAUSAL_FOREST_CONVERSION_TEST_SCORES_PATH = (
    REPORT_ARTIFACTS_DIR / "causal_forest_conversion_test_scores.csv"
)
DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH = (
    METRICS_ARTIFACTS_DIR / "phase3_model_comparison_report.json"
)
DEFAULT_PHASE4_CONVERSION_DECILE_REPORT_PATH = (
    METRICS_ARTIFACTS_DIR / "phase4_conversion_decile_report.json"
)
DEFAULT_PHASE4_CONVERSION_SCORED_VIEW_PATH = (
    REPORT_ARTIFACTS_DIR / "phase4_conversion_scored_view.csv"
)
DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH = (
    METRICS_ARTIFACTS_DIR / "phase4_conversion_rollup_report.json"
)
DEFAULT_PHASE4_CONVERSION_ROLLUP_TABLE_PATH = (
    REPORT_ARTIFACTS_DIR / "phase4_conversion_rollup_table.csv"
)
DEFAULT_PHASE4_CONVERSION_ENRICHED_SCORED_VIEW_PATH = (
    REPORT_ARTIFACTS_DIR / "phase4_conversion_enriched_scored_view.csv"
)
DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH = (
    METRICS_ARTIFACTS_DIR / "phase4_conversion_validation_summary.json"
)
DEFAULT_PHASE5_TARGETING_REPORT_PATH = (
    METRICS_ARTIFACTS_DIR / "phase5_targeting_recommendation_report.json"
)
DEFAULT_PHASE5_TARGET_USERS_PATH = (
    REPORT_ARTIFACTS_DIR / "phase5_target_users.csv"
)
DEFAULT_PHASE5_SUPPRESS_USERS_PATH = (
    REPORT_ARTIFACTS_DIR / "phase5_suppress_users.csv"
)
DEFAULT_PHASE5_BUDGET_ALLOCATION_REPORT_PATH = (
    METRICS_ARTIFACTS_DIR / "phase5_budget_allocation_report.json"
)
DEFAULT_PHASE5_SEGMENT_BUDGET_TABLE_PATH = (
    REPORT_ARTIFACTS_DIR / "phase5_segment_budget_allocation.csv"
)
DEFAULT_DRPOLICYTREE_CONVERSION_MODEL_PATH = (
    MODEL_ARTIFACTS_DIR / "drpolicytree_conversion.joblib"
)
DEFAULT_DRPOLICYTREE_CONVERSION_REPORT_PATH = (
    METRICS_ARTIFACTS_DIR / "drpolicytree_conversion_policy_report.json"
)
DEFAULT_DRPOLICYTREE_CONVERSION_TEST_DECISIONS_PATH = (
    REPORT_ARTIFACTS_DIR / "drpolicytree_conversion_test_decisions.csv"
)
DEFAULT_DRPOLICYFOREST_CONVERSION_MODEL_PATH = (
    MODEL_ARTIFACTS_DIR / "drpolicyforest_conversion.joblib"
)
DEFAULT_DRPOLICYFOREST_CONVERSION_REPORT_PATH = (
    METRICS_ARTIFACTS_DIR / "drpolicyforest_conversion_policy_report.json"
)
DEFAULT_DRPOLICYFOREST_CONVERSION_TEST_DECISIONS_PATH = (
    REPORT_ARTIFACTS_DIR / "drpolicyforest_conversion_test_decisions.csv"
)
DEFAULT_PHASE5_CLOSEOUT_REPORT_PATH = (
    METRICS_ARTIFACTS_DIR / "phase5_decision_closeout_report.json"
)
DEFAULT_PHASE5_FINAL_SEGMENT_ACTIONS_PATH = (
    REPORT_ARTIFACTS_DIR / "phase5_final_segment_actions.csv"
)


def ensure_project_directories() -> None:
    """Create the data and docs directories required by the first backend slice."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)
    MODEL_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    FEATURE_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
