import json
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "data/processed/features.parquet"
GEOJSON = ROOT / "data/raw/tn_districts.geojson"

# >>> After downloading the GeoJSON, open it and set the property that holds the district name.
GEO_NAME_KEY = "properties.district"   # e.g. "properties.DISTRICT", "properties.dtname"

SUB_COLS = {"Education": "edu_risk", "Health": "health_risk",
            "Employment": "emp_risk", "Infrastructure": "infra_risk"}
BAND_COLORS = {"Low": "#2ecc71", "Moderate": "#f1c40f", "High": "#e67e22", "Critical": "#e74c3c"}

@st.cache_data
def load_features() -> pd.DataFrame:
    return pd.read_parquet(FEATURES)

@st.cache_data
def load_geojson():
    if not GEOJSON.exists():
        return None
    return json.loads(GEOJSON.read_text(encoding="utf-8"))