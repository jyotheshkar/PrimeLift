"""Grouped uplift analysis for important business dimensions."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from pydantic import BaseModel, ConfigDict

from primelift.causal import (
    bootstrap_ate_confidence_interval,
    estimate_average_treatment_effect,
)

DEFAULT_GROUP_COLUMNS = ("segment", "london_borough", "device_type", "channel")


class GroupUpliftResult(BaseModel):
    """Serializable uplift result for a single group value."""

    model_config = ConfigDict(frozen=True)

    group_column: str
    group_value: str
    outcome_column: str
    treated_conversion_rate: float
    control_conversion_rate: float
    uplift: float
    relative_uplift: float | None
    group_size: int
    treated_count: int
    control_count: int
    ci_lower: float | None
    ci_upper: float | None
    confidence_level: float | None
    bootstrap_samples: int | None
    confidence_indicator: str


class DimensionUpliftReport(BaseModel):
    """Serializable uplift report for one grouping dimension."""

    model_config = ConfigDict(frozen=True)

    group_column: str
    outcome_column: str
    result_count: int
    results: list[GroupUpliftResult]


class UpliftAnalysisReport(BaseModel):
    """Serializable uplift report across multiple default grouping dimensions."""

    model_config = ConfigDict(frozen=True)

    outcome_column: str
    group_columns: list[str]
    reports: list[DimensionUpliftReport]


def _validate_group_column(dataset: pd.DataFrame, group_column: str) -> None:
    """Validate the requested grouping column."""

    if group_column not in dataset.columns:
        raise ValueError(f"Missing required group column: {group_column}")

    if dataset[group_column].isnull().any():
        raise ValueError(f"Group column '{group_column}' must not contain null values.")


def _build_confidence_indicator(
    ci_lower: float | None, ci_upper: float | None
) -> str:
    """Translate CI bounds into a simple qualitative confidence indicator."""

    if ci_lower is None or ci_upper is None:
        return "insufficient_data"
    if ci_lower > 0.0:
        return "positive"
    if ci_upper < 0.0:
        return "negative"
    return "uncertain"


def analyze_group_uplift(
    dataset: pd.DataFrame,
    group_column: str,
    outcome_column: str = "conversion",
    treatment_column: str = "treatment",
    bootstrap_samples: int = 200,
    confidence_level: float = 0.95,
    random_seed: int = 42,
    min_group_size_per_arm: int = 25,
) -> DimensionUpliftReport:
    """Analyze uplift for one grouping dimension and sort results by uplift descending."""

    _validate_group_column(dataset, group_column)

    results: list[GroupUpliftResult] = []
    grouped_dataset = dataset.groupby(group_column, sort=False)

    for group_value, group_frame in grouped_dataset:
        treated_count = int((group_frame[treatment_column] == 1).sum())
        control_count = int((group_frame[treatment_column] == 0).sum())
        group_size = int(len(group_frame))

        if treated_count == 0 or control_count == 0:
            continue

        point_estimate = estimate_average_treatment_effect(
            dataset=group_frame,
            outcome_column=outcome_column,
            treatment_column=treatment_column,
        )

        ci_lower: float | None = None
        ci_upper: float | None = None
        applied_confidence_level: float | None = None
        applied_bootstrap_samples: int | None = None

        if treated_count >= min_group_size_per_arm and control_count >= min_group_size_per_arm:
            confidence_interval = bootstrap_ate_confidence_interval(
                dataset=group_frame,
                outcome_column=outcome_column,
                treatment_column=treatment_column,
                bootstrap_samples=bootstrap_samples,
                confidence_level=confidence_level,
                random_seed=random_seed,
            )
            ci_lower = confidence_interval.ci_lower
            ci_upper = confidence_interval.ci_upper
            applied_confidence_level = confidence_interval.confidence_level
            applied_bootstrap_samples = confidence_interval.bootstrap_samples

        results.append(
            GroupUpliftResult(
                group_column=group_column,
                group_value=str(group_value),
                outcome_column=outcome_column,
                treated_conversion_rate=point_estimate.treated_mean,
                control_conversion_rate=point_estimate.control_mean,
                uplift=point_estimate.ate,
                relative_uplift=point_estimate.relative_lift,
                group_size=group_size,
                treated_count=treated_count,
                control_count=control_count,
                ci_lower=ci_lower,
                ci_upper=ci_upper,
                confidence_level=applied_confidence_level,
                bootstrap_samples=applied_bootstrap_samples,
                confidence_indicator=_build_confidence_indicator(
                    ci_lower=ci_lower,
                    ci_upper=ci_upper,
                ),
            )
        )

    sorted_results = sorted(
        results,
        key=lambda result: (-result.uplift, -result.group_size, result.group_value),
    )

    return DimensionUpliftReport(
        group_column=group_column,
        outcome_column=outcome_column,
        result_count=len(sorted_results),
        results=sorted_results,
    )


def analyze_default_uplift_dimensions(
    dataset: pd.DataFrame,
    group_columns: Sequence[str] = DEFAULT_GROUP_COLUMNS,
    outcome_column: str = "conversion",
    treatment_column: str = "treatment",
    bootstrap_samples: int = 200,
    confidence_level: float = 0.95,
    random_seed: int = 42,
    min_group_size_per_arm: int = 25,
) -> UpliftAnalysisReport:
    """Run Phase 4 uplift analysis for the default important business dimensions."""

    reports = [
        analyze_group_uplift(
            dataset=dataset,
            group_column=group_column,
            outcome_column=outcome_column,
            treatment_column=treatment_column,
            bootstrap_samples=bootstrap_samples,
            confidence_level=confidence_level,
            random_seed=random_seed,
            min_group_size_per_arm=min_group_size_per_arm,
        )
        for group_column in group_columns
    ]

    return UpliftAnalysisReport(
        outcome_column=outcome_column,
        group_columns=list(group_columns),
        reports=reports,
    )
