"""Registry of the planned causal ML models for PrimeLift."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ModelBlueprint(BaseModel):
    """Serializable metadata for a planned model component."""

    model_config = ConfigDict(frozen=True)

    name: str
    family: str
    role: str
    package: str
    estimator_class: str
    supported_outcomes: list[str]
    purpose: str
    target_phase: int
    status: str


def get_default_model_blueprints() -> list[ModelBlueprint]:
    """Return the planned causal ML stack for the revised first five phases."""

    return [
        ModelBlueprint(
            name="ate_baseline",
            family="baseline",
            role="scientific_sanity_check",
            package="internal",
            estimator_class="DifferenceInMeans",
            supported_outcomes=["conversion", "revenue"],
            purpose="Keep a non-ML causal baseline that every uplift model must beat.",
            target_phase=3,
            status="implemented",
        ),
        ModelBlueprint(
            name="xlearner_conversion",
            family="cate",
            role="ml_baseline",
            package="econml",
            estimator_class="econml.metalearners.XLearner",
            supported_outcomes=["conversion"],
            purpose="Provide the first ML uplift baseline for conversion scoring.",
            target_phase=3,
            status="implemented",
        ),
        ModelBlueprint(
            name="drlearner_conversion",
            family="cate",
            role="champion_candidate",
            package="econml",
            estimator_class="econml.dr.DRLearner",
            supported_outcomes=["conversion"],
            purpose="Serve as the main CATE model for conversion uplift scoring.",
            target_phase=3,
            status="implemented",
        ),
        ModelBlueprint(
            name="drlearner_revenue",
            family="cate",
            role="champion_candidate",
            package="econml",
            estimator_class="econml.dr.DRLearner",
            supported_outcomes=["revenue"],
            purpose="Estimate incremental revenue effects for budget decisions.",
            target_phase=3,
            status="implemented",
        ),
        ModelBlueprint(
            name="causal_forest_conversion",
            family="cate",
            role="challenger",
            package="econml",
            estimator_class="econml.dml.CausalForestDML",
            supported_outcomes=["conversion"],
            purpose="Model non-linear treatment heterogeneity as a challenger estimator.",
            target_phase=3,
            status="implemented",
        ),
        ModelBlueprint(
            name="dr_policy_tree",
            family="policy",
            role="explainable_decision_model",
            package="econml",
            estimator_class="econml.policy.DRPolicyTree",
            supported_outcomes=["conversion", "revenue"],
            purpose="Generate interpretable targeting policy recommendations.",
            target_phase=5,
            status="implemented",
        ),
        ModelBlueprint(
            name="dr_policy_forest",
            family="policy",
            role="performance_challenger",
            package="econml",
            estimator_class="econml.policy.DRPolicyForest",
            supported_outcomes=["conversion", "revenue"],
            purpose="Provide a higher-capacity policy model after the explainable tree baseline.",
            target_phase=5,
            status="implemented",
        ),
        ModelBlueprint(
            name="lightgbm_classifier",
            family="base_learner",
            role="nuisance_model",
            package="lightgbm",
            estimator_class="lightgbm.LGBMClassifier",
            supported_outcomes=["conversion", "treatment"],
            purpose="Handle binary propensity and conversion nuisance modeling on tabular features.",
            target_phase=1,
            status="implemented",
        ),
        ModelBlueprint(
            name="lightgbm_regressor",
            family="base_learner",
            role="nuisance_model",
            package="lightgbm",
            estimator_class="lightgbm.LGBMRegressor",
            supported_outcomes=["revenue"],
            purpose="Handle continuous revenue nuisance modeling on tabular features.",
            target_phase=1,
            status="implemented",
        ),
    ]
