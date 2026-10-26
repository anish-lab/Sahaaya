"""
prepare_boundaries.py — Preprocess and standardize GeoJSON boundaries.

Produces:
    data/processed/india_states.geojson: Standardized 36-state boundary geometries
    matching CANONICAL_STATES for All-India state choropleth mapping.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.build_district_master import match_district

RAW_GEOJSON = ROOT / "data" / "raw" / "boundaries" / "india_states.geojson"
PROCESSED_GEOJSON = ROOT / "data" / "processed" / "india_states.geojson"
TN_GEOJSON = ROOT / "data" / "processed" / "tn_districts.geojson"

def process_india_states():
    if not RAW_GEOJSON.exists():
        print(f"[WARN] {RAW_GEOJSON} not found.")
        return False

    with open(RAW_GEOJSON, encoding="utf-8") as f:
        data = json.load(f)

    valid_features = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        raw_name = props.get("st_nm") or props.get("NAME_1") or props.get("state") or props.get("district")
        canonical = match_district(raw_name)
        if canonical:
            code, name, mtype, score = canonical
            feat["properties"]["district"] = name
            feat["properties"]["district_name"] = name
            feat["properties"]["state"] = name
            feat["properties"]["name"] = name
            feat["properties"]["district_id"] = code
            feat["properties"]["st_nm"] = name
            valid_features.append(feat)

    data["features"] = valid_features
    PROCESSED_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(data, f)

    with open(TN_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(data, f)

    print(f"[OK] Processed {len(valid_features)} state boundaries to {PROCESSED_GEOJSON}")
    return True

if __name__ == "__main__":
    process_india_states()
