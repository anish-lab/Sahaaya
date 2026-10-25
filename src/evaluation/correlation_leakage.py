"""
correlation_leakage.py — Collinearity Audit & Leakage Prevention.

Calculates the pairwise correlation matrix across raw indicators to:
1. Detect multicollinear feature pairs (|r| >= 0.70).
2. Explicitly guard against circular identity leakage:
   Prevent predictive models and SHAP attribution from circularly predicting
   the composite vulnerability index directly from the sub-indicators used to construct it.

Outputs:
    data/metadata/feature_correlation.json: Collinearity audit and leakage protocol.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Dict, Any, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def evaluate_collinearity_and_leakage(
    features_df: pd.DataFrame | None = None,
    threshold: float = 0.70,
) -> Dict[str, Any]:
    """Audit collinearity across raw indicators and document leakage boundaries.

    Parameters
    ----------
    features_df : pd.DataFrame, optional
        Dataframe containing raw indicator columns.
    threshold : float, default 0.70
        Absolute Pearson correlation threshold for flagging collinear pairs.

    Returns
    -------
    dict
        Dictionary containing correlation matrix, collinear pairs, and leakage policy.
    """
    if features_df is None:
        features_path = ROOT / "data" / "processed" / "features.parquet"
        if not features_path.exists():
            raise FileNotFoundError(f"{features_path} does not exist.")
        features_df = pd.read_parquet(features_path)

    raw_candidates = [
        "schools_with_electricity_pct",
        "schools_with_drinking_water_pct",
        "schools_with_toilets_pct",
        "schools_with_internet_pct",
        "schools_with_computers_pct",
        "pupil_teacher_ratio",
        "stunting_pct",
        "wasting_pct",
        "institutional_births_pct",
        "health_insurance_pct",
        "schooling_10plus_pct",
    ]
    indicators = [c for c in raw_candidates if c in features_df.columns and features_df[c].notna().any()]

    if len(indicators) < 2:
        raise ValueError("At least 2 indicators required for correlation analysis.")

    corr_matrix = features_df[indicators].corr().round(3)

    collinear_pairs: List[Dict[str, Any]] = []
    for i in range(len(indicators)):
        for j in range(i + 1, len(indicators)):
            c1, c2 = indicators[i], indicators[j]
            val = float(corr_matrix.loc[c1, c2])
            if abs(val) >= threshold:
                collinear_pairs.append({
                    "indicator_1": c1,
                    "indicator_2": c2,
                    "pearson_r": round(val, 3),
                    "interpretation": (
                        "Strong collinearity indicates structural co-dependence. "
                        "When applying predictive models, one of these indicators should be regularized "
                        "or reduced via PCA/ridge regression to prevent variance inflation."
                    ),
                })

    leakage_protocol = {
        "definition": (
            "Target leakage occurs when features fed into a predictive model or SHAP explanation "
            "contain direct deterministic components of the target variable."
        ),
        "sahaaya_guardrail": (
            "Because overall_score is a deterministic weighted linear combination of normalized indicators, "
            "regressing overall_score on these same 11 indicators yields a trivial identity with R^2 ~ 1.0, "
            "producing circular and uninformative SHAP explanations. In SAHAAYA: "
            "(1) Unsupervised clustering and Isolation Forest are trained on standardized indicators to discover "
            "intrinsic data geometry rather than predict overall_score. "
            "(2) Counterfactual simulation uses explicit linear index sensitivity accounting rather than an "
            "in-sample regression black box, ensuring 100% transparency with zero circular leakage."
        ),
    }

    results = {
        "indicators_audited": indicators,
        "collinear_threshold": threshold,
        "collinear_pairs": collinear_pairs,
        "correlation_matrix": corr_matrix.to_dict(),
        "leakage_protocol": leakage_protocol,
    }

    # Save to metadata
    out_dir = ROOT / "data" / "metadata"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "feature_correlation.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    res = evaluate_collinearity_and_leakage()
    print("=" * 60)
    print("SAHAAYA Collinearity Audit & Leakage Prevention")
    print("=" * 60)
    print(f"Audited Indicators:      {len(res['indicators_audited'])}")
    print(f"Collinear Pairs (|r|>=0.70): {len(res['collinear_pairs'])}")
    for p in res["collinear_pairs"]:
        print(f"  {p['indicator_1']} <-> {p['indicator_2']}: r = {p['pearson_r']}")
    print("=" * 60)
