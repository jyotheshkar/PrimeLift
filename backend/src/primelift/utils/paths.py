"""Path helpers shared across the backend slice."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = REPO_ROOT / "data"
RAW_DATA_DIR = DATA_ROOT / "raw"
PROCESSED_DATA_DIR = DATA_ROOT / "processed"
DOCS_DIR = REPO_ROOT / "docs"
DEFAULT_DATASET_PATH = RAW_DATA_DIR / "london_campaign_users_100k.csv"
DEFAULT_DATASET_VIEW_PATH = RAW_DATA_DIR / "london_campaign_users_100k_view.html"
DEFAULT_DATA_DICTIONARY_PATH = DOCS_DIR / "london_campaign_users_data_dictionary.md"


def ensure_project_directories() -> None:
    """Create the data and docs directories required by the first backend slice."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
