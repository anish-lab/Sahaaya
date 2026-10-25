"""
features.build_features — Assembles composite district feature table.

Merges cleaned interim datasets (UDISE+, NFHS-5, MGNREGA) with the canonical
Tamil Nadu district master, calculates standardized dimension risk scores,
computes overall vulnerability index and risk bands, and saves the final
``data/processed/features.parquet`` dataset according to the data contract.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.features.vulnerability_index import (
    compute_dimension_score,
    compute_overall_score,
    assign_risk_band,
)
from src.build_district_master import build_district_master

# Indicator directional mapping (True = higher raw value means higher vulnerability risk)
INDICATOR_DIRECTIONS = {
    # Education
    "dropout_rate": True,
    "pupil_teacher_ratio": True,
    "female_literacy_pct": False,
    "schooling_10plus_pct": False,
    # Healthcare
    "stunting_pct": True,
    "wasting_pct": True,
    "anaemia_pct": True,
    "anaemia_children_pct": True,
    "anaemia_women_pct": True,
    "institutional_births_pct": False,  # higher = better
    "full_vaccination_pct": False,  # higher = better
    "health_insurance_pct": False,  # higher = better
    # Employment (MGNREGA)
    "persondays_per_hh": False,  # more persondays = stronger safety net = lower risk
    "persondays_generated": False,
    "employment_fulfillment_pct": False,
    "women_persondays_pct": False,
    "avg_days_per_hh": False,
    # Infrastructure
    "schools_with_electricity_pct": False,  # higher access = lower risk
    "schools_with_toilets_pct": False,
    "schools_with_drinking_water_pct": False,
    "schools_with_internet_pct": False,
    "school_infra_score": False,
}


def load_interim_table(filename: str) -> Optional[pd.DataFrame]:
    """Safely load parquet from data/interim/."""
    path = ROOT / "data" / "interim" / filename
    if path.exists():
        try:
            return pd.read_parquet(path)
        except Exception:
            return None
    return None


def build_features(
    output_path: Optional[Path] = None,
    master_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Combine cleaned interim datasets into features.parquet."""
    if output_path is None:
        output_path = ROOT / "data" / "processed" / "features.parquet"

    if master_df is None:
        master_df = build_district_master()

    # Base table starts with 38 canonical districts
    df = master_df[["district_id", "district_name", "state"]].copy()
    feature_log = {
        "sources_used": [],
        "dimensions_computed": [],
        "indicator_columns": [],
    }

    # 1. Ingest UDISE+ (Education & Infrastructure)
    udise_df = load_interim_table("udise_clean.parquet")
    if udise_df is not None and not udise_df.empty:
        feature_log["sources_used"].append("udise")
        merge_cols = [c for c in udise_df.columns if c not in {"district_name", "state"}]
        df = df.merge(udise_df[merge_cols], on="district_id", how="left")

    # 2. Ingest NFHS-5 (Healthcare)
    nfhs_df = load_interim_table("nfhs_clean.parquet")
    if nfhs_df is not None and not nfhs_df.empty:
        feature_log["sources_used"].append("nfhs")
        merge_cols = [c for c in nfhs_df.columns if c not in {"district_name", "state"}]
        df = df.merge(nfhs_df[merge_cols], on="district_id", how="left")

    # 3. Ingest MGNREGA (Employment)
    mgnrega_df = load_interim_table("mgnrega_clean.parquet")
    if mgnrega_df is not None and not mgnrega_df.empty:
        feature_log["sources_used"].append("mgnrega")
        merge_cols = [c for c in mgnrega_df.columns if c not in {"district_name", "state"}]
        df = df.merge(mgnrega_df[merge_cols], on="district_id", how="left")

    # Determine reporting period
    if "period" not in df.columns:
        periods = [df[c].iloc[0] for c in ["period_udise", "period_mgnrega", "period_nfhs"] if c in df.columns and df[c].notna().any()]
        df["period"] = periods[0] if periods else "Latest Available"

    # Identify indicators for each dimension
    edu_indicators = ["pupil_teacher_ratio", "female_literacy_pct", "schooling_10plus_pct", "dropout_rate"]
    health_indicators = ["stunting_pct", "wasting_pct", "anaemia_pct", "anaemia_children_pct", "anaemia_women_pct", "institutional_births_pct", "full_vaccination_pct"]
    emp_indicators = ["employment_fulfillment_pct", "persondays_per_hh", "women_persondays_pct", "avg_days_per_hh", "mgnrega_persondays_per_hh"]
    infra_indicators = ["schools_with_electricity_pct", "schools_with_toilets_pct", "schools_with_drinking_water_pct", "schools_with_internet_pct", "school_infra_score"]

    # Calculate dimension risk scores (0-100)
    df["edu_risk"] = compute_dimension_score(df, edu_indicators, higher_is_worse_map=INDICATOR_DIRECTIONS)
    df["health_risk"] = compute_dimension_score(df, health_indicators, higher_is_worse_map=INDICATOR_DIRECTIONS)
    df["emp_risk"] = compute_dimension_score(df, emp_indicators, higher_is_worse_map=INDICATOR_DIRECTIONS)
    df["infra_risk"] = compute_dimension_score(df, infra_indicators, higher_is_worse_map=INDICATOR_DIRECTIONS)

    # If any dimension has no raw data, leave as NaN
    for dim_col in ["edu_risk", "health_risk", "emp_risk", "infra_risk"]:
        if df[dim_col].notna().any():
            feature_log["dimensions_computed"].append(dim_col)

    # Compute overall vulnerability score and risk band
    df["overall_score"] = compute_overall_score(df["edu_risk"], df["health_risk"], df["emp_risk"], df["infra_risk"])
    df["risk_band"] = assign_risk_band(df["overall_score"])

    # Compute data completeness (fraction of 4 dimensions available)
    dim_cols = ["edu_risk", "health_risk", "emp_risk", "infra_risk"]
    df["data_completeness"] = df[dim_cols].notna().mean(axis=1).round(2)

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
    print("Features built successfully. Shape:", df.shape)
    print("Columns:", list(df.columns))
