"""
build_features.py — Feature engineering and composite vulnerability scoring.

Merges cleaned interim tables (UDISE+, NFHS-5) to construct the production features.parquet
dataset across Education, Healthcare, and Civic Infrastructure.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Optional

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.features.vulnerability_index import (
    compute_dimension_score,
    compute_overall_score,
    assign_risk_band,
)

INTERIM_DIR = ROOT / "data" / "interim"
PROCESSED_DIR = ROOT / "data" / "processed"
MASTER_FILE = ROOT / "data" / "metadata" / "district_master.json"

# Directionality: True = higher is worse (risk), False = higher is better (protective)
INDICATOR_DIRECTIONS: dict[str, bool] = {
    # Education
    "dropout_rate": True,
    "pupil_teacher_ratio": True,
    "female_literacy_pct": False,
    "schooling_10plus_pct": False,
    # Health
    "stunting_pct": True,
    "wasting_pct": True,
    "anaemia_pct": True,
    "anaemia_children_pct": True,
    "anaemia_women_pct": True,
    "institutional_births_pct": False,
    "full_vaccination_pct": False,
    "health_insurance_pct": False,
    # Infrastructure
    "schools_with_electricity_pct": False,
    "schools_with_toilets_pct": False,
    "schools_with_drinking_water_pct": False,
    "schools_with_internet_pct": False,
    "schools_with_computers_pct": False,
    "school_infra_score": False,
}


def load_interim_table(filename: str) -> Optional[pd.DataFrame]:
    """Load an interim parquet file if present."""
    path = INTERIM_DIR / filename
    if path.exists():
        return pd.read_parquet(path)
    return None


def build_features(output_path: Path = PROCESSED_DIR / "features.parquet") -> pd.DataFrame:
    """Build the final feature table by joining cleaned sources and computing indices."""
    feature_log = {
        "sources_used": [],
        "dimensions_computed": [],
        "total_records": 0,
    }

    # 1. Ingest UDISE (Education & School Infrastructure)
    udise_df = load_interim_table("udise_clean.parquet")
    if udise_df is None or udise_df.empty:
        raise FileNotFoundError("Missing required interim table: udise_clean.parquet")

    df = udise_df.copy()
    feature_log["sources_used"].append("udise")

    # 2. Ingest NFHS (Healthcare & Nutrition)
    nfhs_df = load_interim_table("nfhs_clean.parquet")
    if nfhs_df is not None and not nfhs_df.empty:
        feature_log["sources_used"].append("nfhs")
        merge_cols = [c for c in nfhs_df.columns if c not in {"district_name", "state"}]
        df = df.merge(nfhs_df[merge_cols], on="district_id", how="left")

    # Determine reporting period
    if "period" not in df.columns:
        periods = [df[c].iloc[0] for c in ["period_udise", "period_nfhs"] if c in df.columns and df[c].notna().any()]
        df["period"] = periods[0] if periods else "Latest Available"

    # Identify indicators for each of the 3 active dimensions
    edu_indicators = ["pupil_teacher_ratio", "female_literacy_pct", "schooling_10plus_pct", "dropout_rate"]
    health_indicators = ["stunting_pct", "wasting_pct", "anaemia_pct", "anaemia_children_pct", "anaemia_women_pct", "institutional_births_pct", "full_vaccination_pct", "health_insurance_pct"]
    infra_indicators = ["schools_with_electricity_pct", "schools_with_toilets_pct", "schools_with_drinking_water_pct", "schools_with_internet_pct", "schools_with_computers_pct", "school_infra_score"]

    # Calculate dimension risk scores (0-100)
    df["edu_risk"] = compute_dimension_score(df, edu_indicators, higher_is_worse_map=INDICATOR_DIRECTIONS)
    df["health_risk"] = compute_dimension_score(df, health_indicators, higher_is_worse_map=INDICATOR_DIRECTIONS)
    df["infra_risk"] = compute_dimension_score(df, infra_indicators, higher_is_worse_map=INDICATOR_DIRECTIONS)

    # Ensure emp_risk is dropped if present anywhere in merge
    if "emp_risk" in df.columns:
        df = df.drop(columns=["emp_risk"])

    for dim_col in ["edu_risk", "health_risk", "infra_risk"]:
        if df[dim_col].notna().any():
            feature_log["dimensions_computed"].append(dim_col)

    # Compute overall vulnerability score and risk band across the 3 dimensions
    df["overall_score"] = compute_overall_score(df["edu_risk"], df["health_risk"], df["infra_risk"])
    df["risk_band"] = assign_risk_band(df["overall_score"])

    # Compute data completeness (all 3 dimensions are 100% available)
    dim_cols = ["edu_risk", "health_risk", "infra_risk"]
    df["data_completeness"] = df[dim_cols].notna().mean(axis=1).round(2)
    feature_log["total_records"] = len(df)

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)

    # Write log
    meta_dir = ROOT / "data" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    with open(meta_dir / "feature_engineering_log.json", "w", encoding="utf-8") as f:
        json.dump(feature_log, f, indent=2)

    return df


if __name__ == "__main__":
    df = build_features()
    print("Features built successfully without employment. Shape:", df.shape)
    print("Columns:", list(df.columns))
