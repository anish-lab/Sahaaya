"""
SAHAAYA Dashboard — Data loading utilities with caching and production guards.

Provides cached data loading functions for all pipeline outputs,
mock-data detection heuristics, and shared constants for the dashboard.
"""
import json
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT: Path = Path(__file__).resolve().parents[1]
FEATURES_PATH: Path = ROOT / "data" / "processed" / "features.parquet"
CLUSTERS_PATH: Path = ROOT / "data" / "processed" / "cluster_assignments.parquet"
PROFILES_PATH: Path = ROOT / "data" / "processed" / "cluster_profiles.parquet"
ANOMALIES_PATH: Path = ROOT / "data" / "processed" / "anomaly_results.parquet"
INDIA_GEOJSON_PATH: Path = ROOT / "data" / "processed" / "india_states.geojson"
TN_GEOJSON_PATH: Path = ROOT / "data" / "processed" / "tn_districts.geojson"
GEOJSON_PATH: Path = INDIA_GEOJSON_PATH if INDIA_GEOJSON_PATH.exists() else TN_GEOJSON_PATH

# Configurable: the key in GeoJSON feature properties that holds the district name
GEO_NAME_KEY: str = "properties.district"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SUB_COLS: dict[str, str] = {
    "Education": "edu_risk",
    "Health": "health_risk",
    "Infrastructure": "infra_risk",
}

BAND_COLORS: dict[str, str] = {
    "Low": "#385E48",       # Deep muted sage/pine
    "Moderate": "#827845",  # Antiqued brass / olive
    "High": "#BA6835",      # Warm terracotta
    "Critical": "#B84324",  # Burnt orange / sienna
}

BAND_ORDER: list[str] = ["Low", "Moderate", "High", "Critical"]

# Mock-data fingerprint columns (from make_mock_data.py)
_MOCK_INDICATOR_COLS = {
    "dropout_rate",
    "anaemia_pct",
    "mgnrega_persondays_per_hh",
    "school_infra_score",
}
_MOCK_ROW_COUNT = 114  # 38 districts x 3 years
_MOCK_YEARS = {2021, 2022, 2023}


# ---------------------------------------------------------------------------
# Data loaders (all cached)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading features...")
def load_features() -> Optional[pd.DataFrame]:
    """Load features.parquet.  Returns None if the file does not exist."""
    if not FEATURES_PATH.exists():
        return None
    try:
        return pd.read_parquet(FEATURES_PATH)
    except Exception:
        return None


@st.cache_data(show_spinner="Loading cluster assignments...")
def load_clusters() -> Optional[pd.DataFrame]:
    """Load cluster_assignments.parquet.  Returns None if missing."""
    if not CLUSTERS_PATH.exists():
        return None
    try:
        return pd.read_parquet(CLUSTERS_PATH)
    except Exception:
        return None


@st.cache_data(show_spinner="Loading cluster profiles...")
def load_profiles() -> Optional[pd.DataFrame]:
    """Load cluster_profiles.parquet.  Returns None if missing."""
    if not PROFILES_PATH.exists():
        return None
    try:
        return pd.read_parquet(PROFILES_PATH)
    except Exception:
        return None


@st.cache_data(show_spinner="Loading anomaly results...")
def load_anomalies() -> Optional[pd.DataFrame]:
    """Load anomaly_results.parquet.  Returns None if missing."""
    if not ANOMALIES_PATH.exists():
        return None
    try:
        return pd.read_parquet(ANOMALIES_PATH)
    except Exception:
        return None


@st.cache_data(show_spinner="Loading GeoJSON boundaries...")
def load_geojson() -> Optional[dict]:
    """Load tn_districts.geojson.  Returns None if missing."""
    if not GEOJSON_PATH.exists():
        return None
    try:
        return json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Production guards
# ---------------------------------------------------------------------------
def is_mock_data(df: pd.DataFrame) -> bool:
    """Heuristic: detect whether *df* looks like the synthetic mock dataset.

    Checks:
    1. Exactly 114 rows (38 districts x 3 years).
    2. Has a ``year`` column with values {2021, 2022, 2023}.
    3. Contains only the mock indicator columns (no real source indicators).
    """
    if df is None:
        return False
    if len(df) != _MOCK_ROW_COUNT:
        return False
    if "year" in df.columns and set(df["year"].dropna().unique()) == _MOCK_YEARS:
        # Check that the non-standard columns are exactly the mock set
        indicator_cols = set(df.columns) - {
            "district_id", "district_name", "state", "year", "period",
            "edu_risk", "health_risk", "infra_risk",
            "overall_score", "risk_band", "data_completeness",
            "cluster", "anomaly_flag", "anomaly_score",
            "pred_next_score",
        }
        if indicator_cols == _MOCK_INDICATOR_COLS:
            return True
    return False


def get_data_status() -> dict:
    """Return a dict summarising which pipeline outputs exist on disk."""
    return {
        "features": FEATURES_PATH.exists(),
        "clusters": CLUSTERS_PATH.exists(),
        "profiles": PROFILES_PATH.exists(),
        "anomalies": ANOMALIES_PATH.exists(),
        "geojson": GEOJSON_PATH.exists(),
    }
