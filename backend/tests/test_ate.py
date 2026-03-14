"""Tests for the full Phase 3 causal analysis core."""

from __future__ import annotations

import pandas as pd
import pytest

from primelift.causal import (
    ATEConfidenceInterval,
    ATEResult,
    CausalAnalysisResult,
    analyze_average_treatment_effect,
    bootstrap_ate_confidence_interval,
    estimate_average_treatment_effect,
    estimate_revenue_lift,
)


def test_ate_matches_difference_in_means_for_binary_outcome() -> None:
    """ATE should equal treated mean minus control mean on a toy dataset."""

    dataset = pd.DataFrame(
        {
            "treatment": [1, 1, 1, 1, 0, 0, 0, 0],
            "conversion": [1, 1, 0, 1, 0, 0, 1, 0],
        }
    )

    result = estimate_average_treatment_effect(dataset)

    assert isinstance(result, ATEResult)
    assert result.treated_mean == pytest.approx(0.75)
    assert result.control_mean == pytest.approx(0.25)
    assert result.ate == pytest.approx(0.5)
    assert result.absolute_lift == pytest.approx(0.5)
    assert result.relative_lift == pytest.approx(2.0)


def test_ate_supports_custom_numeric_outcome_columns() -> None:
    """The estimator should work for any numeric outcome column, not just conversion."""

    dataset = pd.DataFrame(
        {
            "variant": [1, 1, 0, 0],
            "revenue": [120.0, 80.0, 50.0, 30.0],
        }
    )

    result = estimate_average_treatment_effect(
        dataset,
        outcome_column="revenue",
        treatment_column="variant",
    )

    assert result.ate == pytest.approx(60.0)
    assert result.outcome_column == "revenue"
    assert result.treatment_column == "variant"
    assert result.absolute_lift == pytest.approx(60.0)
    assert result.relative_lift == pytest.approx(1.5)


def test_bootstrap_confidence_interval_returns_expected_structure() -> None:
    """Bootstrap CI output should include bounds and contain the point estimate."""

    dataset = pd.DataFrame(
        {
            "treatment": [1, 1, 1, 1, 0, 0, 0, 0],
            "conversion": [1, 1, 0, 1, 0, 0, 1, 0],
        }
    )

    point_estimate = estimate_average_treatment_effect(dataset)
    confidence_interval = bootstrap_ate_confidence_interval(
        dataset,
        bootstrap_samples=300,
        confidence_level=0.95,
        random_seed=11,
    )

    assert isinstance(confidence_interval, ATEConfidenceInterval)
    assert confidence_interval.bootstrap_samples == 300
    assert confidence_interval.confidence_level == pytest.approx(0.95)
    assert confidence_interval.ci_lower <= point_estimate.ate <= confidence_interval.ci_upper


def test_full_phase_three_analysis_combines_point_estimate_and_ci() -> None:
    """The combined Phase 3 analysis should return summary metrics and CI together."""

    dataset = pd.DataFrame(
        {
            "treatment": [1, 1, 1, 1, 0, 0, 0, 0],
            "conversion": [1, 1, 0, 1, 0, 0, 1, 0],
        }
    )

    result = analyze_average_treatment_effect(
        dataset,
        bootstrap_samples=250,
        confidence_level=0.90,
        random_seed=5,
    )

    assert isinstance(result, CausalAnalysisResult)
    assert result.ate == pytest.approx(0.5)
    assert result.absolute_lift == pytest.approx(0.5)
    assert result.relative_lift == pytest.approx(2.0)
    assert result.bootstrap_samples == 250
    assert result.confidence_level == pytest.approx(0.90)
    assert result.ci_lower <= result.ate <= result.ci_upper


def test_revenue_lift_wrapper_analyzes_revenue_column() -> None:
    """Revenue lift analysis should reuse the same Phase 3 machinery on revenue."""

    dataset = pd.DataFrame(
        {
            "treatment": [1, 1, 0, 0],
            "revenue": [120.0, 80.0, 50.0, 30.0],
        }
    )

    result = estimate_revenue_lift(
        dataset,
        bootstrap_samples=250,
        confidence_level=0.95,
        random_seed=7,
    )

    assert result.outcome_column == "revenue"
    assert result.ate == pytest.approx(60.0)
    assert result.treated_mean == pytest.approx(100.0)
    assert result.control_mean == pytest.approx(40.0)
    assert result.ci_lower <= result.ate <= result.ci_upper


def test_ate_rejects_non_binary_treatment_values() -> None:
    """The estimator should fail fast on invalid treatment encoding."""

    dataset = pd.DataFrame(
        {
            "treatment": [0, 1, 2],
            "conversion": [0, 1, 1],
        }
    )

    with pytest.raises(ValueError, match="binary values 0 and 1"):
        estimate_average_treatment_effect(dataset)


def test_ate_rejects_missing_control_or_treated_group() -> None:
    """ATE requires both treatment arms to be present."""

    dataset = pd.DataFrame(
        {
            "treatment": [1, 1, 1],
            "conversion": [0, 1, 1],
        }
    )

    with pytest.raises(ValueError, match="both treated and control groups"):
        estimate_average_treatment_effect(dataset)


def test_bootstrap_rejects_invalid_configuration() -> None:
    """Bootstrap analysis should fail fast on invalid CI settings."""

    dataset = pd.DataFrame(
        {
            "treatment": [1, 1, 0, 0],
            "conversion": [1, 0, 0, 0],
        }
    )

    with pytest.raises(ValueError, match="bootstrap_samples must be greater than 1"):
        bootstrap_ate_confidence_interval(dataset, bootstrap_samples=1)

    with pytest.raises(ValueError, match="confidence_level must be between 0 and 1"):
        bootstrap_ate_confidence_interval(dataset, confidence_level=1.0)


def test_relative_lift_is_none_when_control_mean_is_zero() -> None:
    """Relative lift should be omitted when the control baseline is zero."""

    dataset = pd.DataFrame(
        {
            "treatment": [1, 1, 0, 0],
            "conversion": [1, 0, 0, 0],
        }
    )

    result = estimate_average_treatment_effect(dataset)

    assert result.ate == pytest.approx(0.5)
    assert result.relative_lift is None
