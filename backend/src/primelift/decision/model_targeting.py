"""Model-driven targeting and suppression recommendations for revised Phase 5."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, ConfigDict

from primelift.utils.paths import (
    DEFAULT_PHASE4_CONVERSION_SCORED_VIEW_PATH,
    DEFAULT_PHASE4_CONVERSION_ENRICHED_SCORED_VIEW_PATH,
    DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH,
    DEFAULT_PHASE5_SUPPRESS_USERS_PATH,
    DEFAULT_PHASE5_TARGET_USERS_PATH,
    DEFAULT_PHASE5_TARGETING_REPORT_PATH,
)


class UserActionRecommendation(BaseModel):
    """Serializable recommendation for one user-level action."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    action: str
    predicted_effect: float
    uplift_decile_rank: int | None
    segment: str
    london_borough: str
    device_type: str
    channel: str
    rationale: str


class CohortActionRecommendation(BaseModel):
    """Serializable recommendation for one cohort-level action."""

    model_config = ConfigDict(frozen=True)

    group_column: str
    group_value: str
    action: str
    mean_predicted_effect: float
    observed_ate: float | None
    recommendation_label: str
    rationale: str


class Phase5TargetingRecommendationReport(BaseModel):
    """Serializable report for the first revised Phase 5 decision slice."""

    model_config = ConfigDict(frozen=True)

    report_name: str
    outcome_column: str
    split_name: str
    model_name: str
    validation_report_path: str
    rollup_report_path: str
    scored_view_path: str
    target_users_path: str
    suppress_users_path: str
    output_report_path: str
    target_user_count: int
    suppress_user_count: int
    target_cohort_count: int
    suppress_cohort_count: int
    top_target_users: list[UserActionRecommendation]
    top_suppress_users: list[UserActionRecommendation]
    target_cohorts: list[CohortActionRecommendation]
    suppress_cohorts: list[CohortActionRecommendation]
    action_summary: str


def _load_json(path: Path) -> dict:
    """Load a JSON file from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _build_user_rationale(action: str, predicted_effect: float, decile_rank: int | None) -> str:
    """Build a short rationale for a user-level recommendation."""

    if action == "target":
        decile_text = (
            f" in uplift decile {decile_rank}" if decile_rank is not None else ""
        )
        return (
            f"High predicted incremental impact ({predicted_effect:.4f}){decile_text}; "
            "candidate for prioritized treatment."
        )
    return (
        f"Low or negative predicted incremental impact ({predicted_effect:.4f}); "
        "candidate for suppression."
    )


def _build_cohort_rationale(
    *,
    action: str,
    mean_predicted_effect: float,
    observed_ate: float | None,
) -> str:
    """Build a short rationale for a cohort-level recommendation."""

    observed_text = (
        f" observed ATE {observed_ate:.4f}" if observed_ate is not None else " observed ATE unavailable"
    )
    if action == "target":
        return (
            f"Mean predicted effect {mean_predicted_effect:.4f} with{observed_text}; "
            "prioritize this cohort."
        )
    return (
        f"Mean predicted effect {mean_predicted_effect:.4f} with{observed_text}; "
        "suppress or deprioritize this cohort."
    )


def _validate_required_columns(scored_view: pd.DataFrame) -> None:
    """Validate that the enriched scored view contains the columns needed for decisions."""

    required_columns = {
        "user_id",
        "segment",
        "london_borough",
        "device_type",
        "channel",
        "uplift_decile_rank",
    }
    missing_columns = required_columns.difference(scored_view.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Scored view is missing required decision columns: {missing}")


def _load_decision_scored_view(
    *,
    scored_view_path: Path,
    decile_scored_view_path: Path,
) -> pd.DataFrame:
    """Load the decision scored view and attach decile ranks when they live in a separate Phase 4 file."""

    scored_view = pd.read_csv(scored_view_path)
    if "uplift_decile_rank" in scored_view.columns:
        return scored_view

    decile_view = pd.read_csv(decile_scored_view_path)
    required_decile_columns = {"user_id", "uplift_decile_rank"}
    missing_columns = required_decile_columns.difference(decile_view.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Decile scored view is missing required columns: {missing}")

    merge_columns = ["user_id", "uplift_decile_rank"]
    if "uplift_decile_label" in decile_view.columns:
        merge_columns.append("uplift_decile_label")

    merged_view = scored_view.merge(
        decile_view.loc[:, merge_columns].drop_duplicates(subset=["user_id"]),
        on="user_id",
        how="left",
        validate="one_to_one",
    )
    if merged_view["uplift_decile_rank"].isnull().any():
        raise ValueError("Failed to recover uplift decile ranks for all users.")
    return merged_view


def _rank_target_users(
    *,
    scored_view: pd.DataFrame,
    score_column: str,
    top_deciles: list[int],
    top_n_users: int,
) -> tuple[pd.DataFrame, list[UserActionRecommendation]]:
    """Rank the top target users from the highest-priority uplift deciles."""

    target_frame = scored_view.loc[
        scored_view["uplift_decile_rank"].isin(top_deciles)
    ].sort_values(by=score_column, ascending=False)
    target_frame = target_frame.head(top_n_users).copy()

    recommendations = [
        UserActionRecommendation(
            user_id=str(row["user_id"]),
            action="target",
            predicted_effect=float(row[score_column]),
            uplift_decile_rank=int(row["uplift_decile_rank"]),
            segment=str(row["segment"]),
            london_borough=str(row["london_borough"]),
            device_type=str(row["device_type"]),
            channel=str(row["channel"]),
            rationale=_build_user_rationale(
                action="target",
                predicted_effect=float(row[score_column]),
                decile_rank=int(row["uplift_decile_rank"]),
            ),
        )
        for row in target_frame.to_dict(orient="records")
    ]
    return target_frame, recommendations


def _rank_suppress_users(
    *,
    scored_view: pd.DataFrame,
    score_column: str,
    suppression_deciles: list[int],
    top_n_users: int,
) -> tuple[pd.DataFrame, list[UserActionRecommendation]]:
    """Rank the strongest suppression candidates from negative or weak zones."""

    suppression_mask = scored_view["uplift_decile_rank"].isin(suppression_deciles) | (
        scored_view[score_column] <= 0.0
    )
    suppress_frame = scored_view.loc[suppression_mask].sort_values(by=score_column, ascending=True)
    suppress_frame = suppress_frame.head(top_n_users).copy()

    recommendations = [
        UserActionRecommendation(
            user_id=str(row["user_id"]),
            action="suppress",
            predicted_effect=float(row[score_column]),
            uplift_decile_rank=int(row["uplift_decile_rank"]),
            segment=str(row["segment"]),
            london_borough=str(row["london_borough"]),
            device_type=str(row["device_type"]),
            channel=str(row["channel"]),
            rationale=_build_user_rationale(
                action="suppress",
                predicted_effect=float(row[score_column]),
                decile_rank=int(row["uplift_decile_rank"]),
            ),
        )
        for row in suppress_frame.to_dict(orient="records")
    ]
    return suppress_frame, recommendations


def _build_cohort_recommendations(
    *,
    rollup_report: dict,
    recommendation_label: str,
    action: str,
) -> list[CohortActionRecommendation]:
    """Extract cohort-level actions from the Phase 4 rollup report."""

    rows = []
    for dimension_report in rollup_report["reports"]:
        for result in dimension_report["results"]:
            if result["recommendation_label"] != recommendation_label:
                continue
            rows.append(
                CohortActionRecommendation(
                    group_column=str(result["group_column"]),
                    group_value=str(result["group_value"]),
                    action=action,
                    mean_predicted_effect=float(result["mean_predicted_effect"]),
                    observed_ate=(
                        float(result["observed_ate"])
                        if result["observed_ate"] is not None
                        else None
                    ),
                    recommendation_label=str(result["recommendation_label"]),
                    rationale=_build_cohort_rationale(
                        action=action,
                        mean_predicted_effect=float(result["mean_predicted_effect"]),
                        observed_ate=(
                            float(result["observed_ate"])
                            if result["observed_ate"] is not None
                            else None
                        ),
                    ),
                )
            )

    if action == "target":
        rows = sorted(
            rows,
            key=lambda item: (
                -item.mean_predicted_effect,
                -(item.observed_ate if item.observed_ate is not None else float("-inf")),
                item.group_column,
                item.group_value,
            ),
        )
    else:
        rows = sorted(
            rows,
            key=lambda item: (
                item.observed_ate if item.observed_ate is not None else float("inf"),
                item.mean_predicted_effect,
                item.group_column,
                item.group_value,
            ),
        )
    return rows


def _build_action_summary(
    target_cohorts: list[CohortActionRecommendation],
    suppress_cohorts: list[CohortActionRecommendation],
) -> str:
    """Create a human-readable action summary for the first Phase 5 slice."""

    target_names = ", ".join(cohort.group_value for cohort in target_cohorts[:3]) or "no cohorts"
    suppress_names = ", ".join(cohort.group_value for cohort in suppress_cohorts[:3]) or "no cohorts"
    return f"Increase treatment on {target_names}; suppress or deprioritize {suppress_names}."


def generate_model_targeting_recommendations(
    *,
    validation_report_path: Path = DEFAULT_PHASE4_CONVERSION_VALIDATION_SUMMARY_PATH,
    rollup_report_path: Path = DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH,
    scored_view_path: Path = DEFAULT_PHASE4_CONVERSION_ENRICHED_SCORED_VIEW_PATH,
    decile_scored_view_path: Path = DEFAULT_PHASE4_CONVERSION_SCORED_VIEW_PATH,
    output_report_path: Path = DEFAULT_PHASE5_TARGETING_REPORT_PATH,
    target_users_path: Path = DEFAULT_PHASE5_TARGET_USERS_PATH,
    suppress_users_path: Path = DEFAULT_PHASE5_SUPPRESS_USERS_PATH,
    top_n_users: int = 25,
) -> Phase5TargetingRecommendationReport:
    """Generate the first revised Phase 5 model-driven targeting report."""

    if top_n_users <= 0:
        raise ValueError("top_n_users must be a positive integer.")

    validation_report = _load_json(validation_report_path)
    rollup_report = _load_json(rollup_report_path)
    scored_view = _load_decision_scored_view(
        scored_view_path=scored_view_path,
        decile_scored_view_path=decile_scored_view_path,
    )

    if validation_report["model_name"] != rollup_report["model_name"]:
        raise ValueError("Validation and rollup reports must use the same model.")
    if validation_report["outcome_column"] != rollup_report["outcome_column"]:
        raise ValueError("Validation and rollup reports must use the same outcome.")

    _validate_required_columns(scored_view)

    score_column = str(rollup_report["score_column"])
    if score_column not in scored_view.columns:
        raise ValueError(f"Scored view is missing the score column '{score_column}'.")

    target_user_frame, top_target_users = _rank_target_users(
        scored_view=scored_view,
        score_column=score_column,
        top_deciles=[int(value) for value in validation_report["top_persuadable_deciles"]],
        top_n_users=top_n_users,
    )
    suppress_user_frame, top_suppress_users = _rank_suppress_users(
        scored_view=scored_view,
        score_column=score_column,
        suppression_deciles=[int(value) for value in validation_report["suppression_candidate_deciles"]],
        top_n_users=top_n_users,
    )

    target_users_path.parent.mkdir(parents=True, exist_ok=True)
    target_user_frame.to_csv(target_users_path, index=False)
    suppress_users_path.parent.mkdir(parents=True, exist_ok=True)
    suppress_user_frame.to_csv(suppress_users_path, index=False)

    target_cohorts = _build_cohort_recommendations(
        rollup_report=rollup_report,
        recommendation_label="prioritize",
        action="target",
    )[:10]
    suppress_cohorts = _build_cohort_recommendations(
        rollup_report=rollup_report,
        recommendation_label="suppress",
        action="suppress",
    )[:10]

    report = Phase5TargetingRecommendationReport(
        report_name="phase5_model_targeting_recommendations",
        outcome_column=str(validation_report["outcome_column"]),
        split_name=str(validation_report["split_name"]),
        model_name=str(validation_report["model_name"]),
        validation_report_path=str(validation_report_path),
        rollup_report_path=str(rollup_report_path),
        scored_view_path=str(scored_view_path),
        target_users_path=str(target_users_path),
        suppress_users_path=str(suppress_users_path),
        output_report_path=str(output_report_path),
        target_user_count=int(len(top_target_users)),
        suppress_user_count=int(len(top_suppress_users)),
        target_cohort_count=int(len(target_cohorts)),
        suppress_cohort_count=int(len(suppress_cohorts)),
        top_target_users=top_target_users,
        top_suppress_users=top_suppress_users,
        target_cohorts=target_cohorts,
        suppress_cohorts=suppress_cohorts,
        action_summary=_build_action_summary(target_cohorts, suppress_cohorts),
    )

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return report
