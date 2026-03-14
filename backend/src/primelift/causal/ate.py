"""Average treatment effect analysis utilities for PrimeLift."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict


class ATEResult(BaseModel):
    """Serializable point estimate and summary metrics for ATE."""

    model_config = ConfigDict(frozen=True)

    outcome_column: str
    treatment_column: str
    treated_mean: float
    control_mean: float
    ate: float
    absolute_lift: float
    relative_lift: float | None


class ATEConfidenceInterval(BaseModel):
    """Serializable bootstrap confidence interval for ATE."""

    model_config = ConfigDict(frozen=True)

    outcome_column: str
    treatment_column: str
    ci_lower: float
    ci_upper: float
    confidence_level: float
    bootstrap_samples: int


class CausalAnalysisResult(ATEResult):
    """Combined Phase 3 result including summary stats and bootstrap CI."""

    ci_lower: float
    ci_upper: float
    confidence_level: float
    bootstrap_samples: int


def _validate_input_columns(
    dataset: pd.DataFrame, outcome_column: str, treatment_column: str
) -> None:
    """Validate that the required columns exist and contain usable values."""

    missing_columns = [
        column
        for column in (outcome_column, treatment_column)
        if column not in dataset.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    if dataset[[outcome_column, treatment_column]].isnull().any().any():
        raise ValueError("Outcome and treatment columns must not contain null values.")

    if not pd.api.types.is_numeric_dtype(dataset[outcome_column]):
        raise ValueError("Outcome column must be numeric for ATE estimation.")


def _validate_treatment_assignment(treatment_series: pd.Series) -> None:
    """Validate that treatment assignment is binary and includes both groups."""

    if not treatment_series.isin([0, 1]).all():
        raise ValueError("Treatment column must contain only binary values 0 and 1.")

    unique_values = set(treatment_series.unique())
    if unique_values != {0, 1}:
        raise ValueError("Treatment column must include both treated and control groups.")


def _validate_bootstrap_parameters(
    bootstrap_samples: int, confidence_level: float
) -> None:
    """Validate bootstrap configuration."""

    if bootstrap_samples <= 1:
        raise ValueError("bootstrap_samples must be greater than 1.")

    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between 0 and 1.")


def _extract_group_outcomes(
    dataset: pd.DataFrame,
    outcome_column: str,
    treatment_column: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Extract outcome arrays for treated and control users."""

    _validate_input_columns(
        dataset=dataset,
        outcome_column=outcome_column,
        treatment_column=treatment_column,
    )
    _validate_treatment_assignment(dataset[treatment_column])

    treated_outcomes = dataset.loc[dataset[treatment_column] == 1, outcome_column].to_numpy(
        dtype=float
    )
    control_outcomes = dataset.loc[dataset[treatment_column] == 0, outcome_column].to_numpy(
        dtype=float
    )
    return treated_outcomes, control_outcomes


def _compute_relative_lift(ate: float, control_mean: float) -> float | None:
    """Compute relative lift safely when the control mean is non-zero."""

    if np.isclose(control_mean, 0.0):
        return None
    return float(ate / control_mean)


def estimate_average_treatment_effect(
    dataset: pd.DataFrame,
    outcome_column: str = "conversion",
    treatment_column: str = "treatment",
) -> ATEResult:
    """Estimate ATE as treated mean minus control mean for a chosen outcome."""

    treated_outcomes, control_outcomes = _extract_group_outcomes(
        dataset=dataset,
        outcome_column=outcome_column,
        treatment_column=treatment_column,
    )

    treated_mean = float(treated_outcomes.mean())
    control_mean = float(control_outcomes.mean())
    ate = float(treated_mean - control_mean)

    return ATEResult(
        outcome_column=outcome_column,
        treatment_column=treatment_column,
        treated_mean=treated_mean,
        control_mean=control_mean,
        ate=ate,
        absolute_lift=ate,
        relative_lift=_compute_relative_lift(ate=ate, control_mean=control_mean),
    )


def bootstrap_ate_confidence_interval(
    dataset: pd.DataFrame,
    outcome_column: str = "conversion",
    treatment_column: str = "treatment",
    bootstrap_samples: int = 1000,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> ATEConfidenceInterval:
    """Estimate a bootstrap confidence interval for ATE using stratified resampling."""

    _validate_bootstrap_parameters(
        bootstrap_samples=bootstrap_samples,
        confidence_level=confidence_level,
    )
    treated_outcomes, control_outcomes = _extract_group_outcomes(
        dataset=dataset,
        outcome_column=outcome_column,
        treatment_column=treatment_column,
    )

    rng = np.random.default_rng(random_seed)
    bootstrap_ates = np.empty(bootstrap_samples, dtype=float)

    for index in range(bootstrap_samples):
        treated_sample = rng.choice(
            treated_outcomes, size=treated_outcomes.size, replace=True
        )
        control_sample = rng.choice(
            control_outcomes, size=control_outcomes.size, replace=True
        )
        bootstrap_ates[index] = float(treated_sample.mean() - control_sample.mean())

    alpha = 1.0 - confidence_level
    ci_lower, ci_upper = np.quantile(bootstrap_ates, [alpha / 2.0, 1.0 - alpha / 2.0])

    return ATEConfidenceInterval(
        outcome_column=outcome_column,
        treatment_column=treatment_column,
        ci_lower=float(ci_lower),
        ci_upper=float(ci_upper),
        confidence_level=confidence_level,
        bootstrap_samples=bootstrap_samples,
    )


def analyze_average_treatment_effect(
    dataset: pd.DataFrame,
    outcome_column: str = "conversion",
    treatment_column: str = "treatment",
    bootstrap_samples: int = 1000,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> CausalAnalysisResult:
    """Run the full Phase 3 ATE analysis for a chosen numeric outcome."""

    point_estimate = estimate_average_treatment_effect(
        dataset=dataset,
        outcome_column=outcome_column,
        treatment_column=treatment_column,
    )
    confidence_interval = bootstrap_ate_confidence_interval(
        dataset=dataset,
        outcome_column=outcome_column,
        treatment_column=treatment_column,
        bootstrap_samples=bootstrap_samples,
        confidence_level=confidence_level,
        random_seed=random_seed,
    )

    result_payload = point_estimate.model_dump()
    result_payload.update(
        confidence_interval.model_dump(
            exclude={"outcome_column", "treatment_column"}
        )
    )
    return CausalAnalysisResult(**result_payload)


def estimate_revenue_lift(
    dataset: pd.DataFrame,
    treatment_column: str = "treatment",
    bootstrap_samples: int = 1000,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> CausalAnalysisResult:
    """Convenience wrapper for Phase 3 revenue lift analysis."""

    return analyze_average_treatment_effect(
        dataset=dataset,
        outcome_column="revenue",
        treatment_column=treatment_column,
        bootstrap_samples=bootstrap_samples,
        confidence_level=confidence_level,
        random_seed=random_seed,
    )
