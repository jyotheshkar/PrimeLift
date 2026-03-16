"""Model-based rollups across business dimensions for revised Phase 4."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, ConfigDict

from primelift.causal import estimate_average_treatment_effect
from primelift.data.summary import load_dataset
from primelift.uplift.model_based_analysis import (
    _extract_split_report,
    _load_json,
    _resolve_champion_metrics_report,
)
from primelift.utils.paths import (
    DEFAULT_DATASET_PATH,
    DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_ENRICHED_SCORED_VIEW_PATH,
    DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH,
    DEFAULT_PHASE4_CONVERSION_ROLLUP_TABLE_PATH,
)

DEFAULT_MODEL_ROLLUP_GROUP_COLUMNS = ("segment", "london_borough", "device_type", "channel")


class ModelBasedGroupRollup(BaseModel):
    """Serializable model-based rollup for one business group."""

    model_config = ConfigDict(frozen=True)

    group_column: str
    group_value: str
    outcome_column: str
    group_size: int
    treated_count: int
    control_count: int
    mean_predicted_effect: float
    median_predicted_effect: float
    min_predicted_effect: float
    max_predicted_effect: float
    positive_effect_share: float
    observed_ate: float | None
    gain_over_overall_ate: float | None
    recommendation_label: str


class ModelBasedDimensionRollup(BaseModel):
    """Serializable rollup report for one grouping dimension."""

    model_config = ConfigDict(frozen=True)

    group_column: str
    outcome_column: str
    result_count: int
    top_positive_groups: list[str]
    suppression_candidates: list[str]
    results: list[ModelBasedGroupRollup]


class ModelBasedRollupReport(BaseModel):
    """Serializable report for the second revised Phase 4 slice."""

    model_config = ConfigDict(frozen=True)

    report_name: str
    outcome_column: str
    split_name: str
    model_name: str
    score_column: str
    comparison_report_path: str
    source_metrics_report_path: str
    source_score_output_path: str
    raw_dataset_path: str
    enriched_scored_view_path: str
    rollup_table_path: str
    output_report_path: str
    overall_observed_ate: float
    group_columns: list[str]
    top_persuadable_cohorts: list[dict[str, str | float]]
    suppression_candidates: list[dict[str, str | float]]
    reports: list[ModelBasedDimensionRollup]


def _load_scored_frame_with_dimensions(
    *,
    source_score_output_path: Path,
    raw_dataset_path: Path,
    score_column: str,
    required_group_columns: tuple[str, ...],
) -> pd.DataFrame:
    """Load the scored holdout frame and enrich missing business dimensions from the raw dataset."""

    scored_frame = pd.read_csv(source_score_output_path)
    raw_dataset = load_dataset(raw_dataset_path)

    merge_columns = ["user_id", *required_group_columns]
    raw_lookup = raw_dataset.loc[:, merge_columns].drop_duplicates(subset=["user_id"])
    enriched_frame = scored_frame.merge(
        raw_lookup,
        on="user_id",
        how="left",
        suffixes=("", "_raw"),
        validate="one_to_one",
    )

    for group_column in required_group_columns:
        raw_column = f"{group_column}_raw"
        if group_column not in enriched_frame.columns and raw_column in enriched_frame.columns:
            enriched_frame[group_column] = enriched_frame[raw_column]
        elif raw_column in enriched_frame.columns:
            enriched_frame[group_column] = enriched_frame[group_column].fillna(enriched_frame[raw_column])
            enriched_frame = enriched_frame.drop(columns=[raw_column])

        if group_column not in enriched_frame.columns:
            raise ValueError(f"Missing required group column after enrichment: {group_column}")
        if enriched_frame[group_column].isnull().any():
            raise ValueError(f"Null values remain in required group column: {group_column}")

    if score_column not in enriched_frame.columns:
        raise ValueError(f"Missing score column in scored output: {score_column}")

    return enriched_frame


def _build_recommendation_label(
    *,
    mean_predicted_effect: float,
    observed_ate: float | None,
) -> str:
    """Translate model score and observed effect into a practical cohort label."""

    if observed_ate is not None and observed_ate <= 0.0:
        return "suppress"
    if mean_predicted_effect > 0.0 and observed_ate is not None and observed_ate > 0.0:
        return "prioritize"
    if mean_predicted_effect <= 0.0:
        return "monitor"
    return "watch"


def _summarize_group(
    *,
    group_column: str,
    group_value: str,
    group_frame: pd.DataFrame,
    outcome_column: str,
    score_column: str,
    overall_observed_ate: float,
) -> ModelBasedGroupRollup:
    """Summarize one model-based business group."""

    treated_count = int((group_frame["treatment"] == 1).sum())
    control_count = int((group_frame["treatment"] == 0).sum())

    observed_ate: float | None = None
    if treated_count > 0 and control_count > 0:
        observed_ate = float(
            estimate_average_treatment_effect(
                dataset=group_frame,
                outcome_column=outcome_column,
                treatment_column="treatment",
            ).ate
        )

    mean_predicted_effect = float(group_frame[score_column].mean())
    return ModelBasedGroupRollup(
        group_column=group_column,
        group_value=group_value,
        outcome_column=outcome_column,
        group_size=int(len(group_frame)),
        treated_count=treated_count,
        control_count=control_count,
        mean_predicted_effect=mean_predicted_effect,
        median_predicted_effect=float(group_frame[score_column].median()),
        min_predicted_effect=float(group_frame[score_column].min()),
        max_predicted_effect=float(group_frame[score_column].max()),
        positive_effect_share=float((group_frame[score_column] > 0.0).mean()),
        observed_ate=observed_ate,
        gain_over_overall_ate=(
            observed_ate - overall_observed_ate if observed_ate is not None else None
        ),
        recommendation_label=_build_recommendation_label(
            mean_predicted_effect=mean_predicted_effect,
            observed_ate=observed_ate,
        ),
    )


def _build_dimension_rollup(
    *,
    scored_frame: pd.DataFrame,
    group_column: str,
    outcome_column: str,
    score_column: str,
    overall_observed_ate: float,
) -> ModelBasedDimensionRollup:
    """Build one dimension-level model-based rollup."""

    results = [
        _summarize_group(
            group_column=group_column,
            group_value=str(group_value),
            group_frame=group_frame.copy(),
            outcome_column=outcome_column,
            score_column=score_column,
            overall_observed_ate=overall_observed_ate,
        )
        for group_value, group_frame in scored_frame.groupby(group_column, sort=False)
    ]
    sorted_results = sorted(
        results,
        key=lambda item: (
            -item.mean_predicted_effect,
            -(item.observed_ate if item.observed_ate is not None else float("-inf")),
            -item.group_size,
            item.group_value,
        ),
    )

    top_positive_groups = [
        result.group_value
        for result in sorted_results
        if result.recommendation_label == "prioritize"
    ][:3]
    suppression_candidates = [
        result.group_value
        for result in sorted_results
        if result.recommendation_label == "suppress"
    ][:3]

    return ModelBasedDimensionRollup(
        group_column=group_column,
        outcome_column=outcome_column,
        result_count=len(sorted_results),
        top_positive_groups=top_positive_groups,
        suppression_candidates=suppression_candidates,
        results=sorted_results,
    )


def _flatten_rollups_for_table(reports: list[ModelBasedDimensionRollup]) -> pd.DataFrame:
    """Flatten all rollup rows into one table-friendly dataframe."""

    rows = []
    for report in reports:
        for result in report.results:
            rows.append(result.model_dump())
    return pd.DataFrame(rows)


def generate_model_based_group_rollup_report(
    comparison_report_path: Path = DEFAULT_PHASE3_MODEL_COMPARISON_REPORT_PATH,
    raw_dataset_path: Path = DEFAULT_DATASET_PATH,
    outcome_column: str = "conversion",
    split_name: str = "test",
    group_columns: tuple[str, ...] = DEFAULT_MODEL_ROLLUP_GROUP_COLUMNS,
    output_report_path: Path = DEFAULT_PHASE4_CONVERSION_ROLLUP_REPORT_PATH,
    rollup_table_path: Path = DEFAULT_PHASE4_CONVERSION_ROLLUP_TABLE_PATH,
    enriched_scored_view_path: Path = DEFAULT_PHASE4_CONVERSION_ENRICHED_SCORED_VIEW_PATH,
) -> ModelBasedRollupReport:
    """Generate model-based business-dimension rollups from the selected Phase 3 champion."""

    source_metrics_report_path = _resolve_champion_metrics_report(
        comparison_report_path=comparison_report_path,
        outcome_column=outcome_column,
    )
    training_report = _load_json(source_metrics_report_path)
    split_report = _extract_split_report(training_report, split_name)
    score_column = str(training_report["config"]["score_column"])
    source_score_output_path = Path(split_report["score_output_path"])

    scored_frame = _load_scored_frame_with_dimensions(
        source_score_output_path=source_score_output_path,
        raw_dataset_path=raw_dataset_path,
        score_column=score_column,
        required_group_columns=group_columns,
    )

    enriched_scored_view_path.parent.mkdir(parents=True, exist_ok=True)
    scored_frame.to_csv(enriched_scored_view_path, index=False)

    overall_observed_ate = float(
        estimate_average_treatment_effect(
            dataset=scored_frame,
            outcome_column=outcome_column,
            treatment_column="treatment",
        ).ate
    )

    reports = [
        _build_dimension_rollup(
            scored_frame=scored_frame,
            group_column=group_column,
            outcome_column=outcome_column,
            score_column=score_column,
            overall_observed_ate=overall_observed_ate,
        )
        for group_column in group_columns
    ]

    flat_rollup_table = _flatten_rollups_for_table(reports)
    rollup_table_path.parent.mkdir(parents=True, exist_ok=True)
    flat_rollup_table.to_csv(rollup_table_path, index=False)

    top_persuadable_rows = (
        flat_rollup_table.loc[flat_rollup_table["recommendation_label"] == "prioritize"]
        .sort_values(by=["mean_predicted_effect", "observed_ate"], ascending=[False, False])
        .head(5)
    )
    suppression_rows = (
        flat_rollup_table.loc[flat_rollup_table["recommendation_label"] == "suppress"]
        .sort_values(by=["mean_predicted_effect", "observed_ate"], ascending=[True, True])
        .head(5)
    )

    report = ModelBasedRollupReport(
        report_name="phase4_model_based_group_rollups",
        outcome_column=outcome_column,
        split_name=split_name,
        model_name=str(training_report["model_name"]),
        score_column=score_column,
        comparison_report_path=str(comparison_report_path),
        source_metrics_report_path=str(source_metrics_report_path),
        source_score_output_path=str(source_score_output_path),
        raw_dataset_path=str(raw_dataset_path),
        enriched_scored_view_path=str(enriched_scored_view_path),
        rollup_table_path=str(rollup_table_path),
        output_report_path=str(output_report_path),
        overall_observed_ate=overall_observed_ate,
        group_columns=list(group_columns),
        top_persuadable_cohorts=top_persuadable_rows.loc[
            :, ["group_column", "group_value", "mean_predicted_effect", "observed_ate"]
        ].to_dict(orient="records"),
        suppression_candidates=suppression_rows.loc[
            :, ["group_column", "group_value", "mean_predicted_effect", "observed_ate"]
        ].to_dict(orient="records"),
        reports=reports,
    )

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return report
