"""Segment-level uplift analysis utilities for PrimeLift."""

from primelift.uplift.model_based_analysis import (
    ModelBasedUpliftDecileReport,
    UpliftDecileBucket,
    generate_model_based_uplift_decile_report,
)
from primelift.uplift.model_based_rollups import (
    DEFAULT_MODEL_ROLLUP_GROUP_COLUMNS,
    ModelBasedDimensionRollup,
    ModelBasedGroupRollup,
    ModelBasedRollupReport,
    generate_model_based_group_rollup_report,
)
from primelift.uplift.segment_analysis import (
    DEFAULT_GROUP_COLUMNS,
    DimensionUpliftReport,
    GroupUpliftResult,
    UpliftAnalysisReport,
    analyze_default_uplift_dimensions,
    analyze_group_uplift,
)

__all__ = [
    "DEFAULT_GROUP_COLUMNS",
    "DEFAULT_MODEL_ROLLUP_GROUP_COLUMNS",
    "DimensionUpliftReport",
    "GroupUpliftResult",
    "ModelBasedDimensionRollup",
    "ModelBasedGroupRollup",
    "ModelBasedRollupReport",
    "ModelBasedUpliftDecileReport",
    "UpliftAnalysisReport",
    "UpliftDecileBucket",
    "analyze_default_uplift_dimensions",
    "analyze_group_uplift",
    "generate_model_based_uplift_decile_report",
    "generate_model_based_group_rollup_report",
]
