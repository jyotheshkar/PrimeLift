"""Data generation and inspection utilities for PrimeLift."""

from primelift.data.generator import generate_and_save_default_dataset, generate_london_campaign_users
from primelift.data.summary import build_dataset_summary

__all__ = [
    "build_dataset_summary",
    "generate_and_save_default_dataset",
    "generate_london_campaign_users",
]
