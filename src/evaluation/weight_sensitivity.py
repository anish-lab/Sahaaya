"""
weight_sensitivity.py — Weight Justification & Sensitivity Analysis.

Provides methodological justification for equal dimension weighting and demonstrates
empirical robustness via:
1. Normative justification (Alkire-Foster / HDI / NITI Aayog equal pillar framework).
2. Monte Carlo weight perturbation (1,000 simulations drawing Dirichlet weights +/- 30%).
3. Comparison against an unsupervised PCA-derived index (First Principal Component).

Outputs:
    data/metadata/weight_sensitivity.json: Sensitivity analysis metrics and PCA comparison.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Dict, Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def evaluate_weight_sensitivity(
    features_df: pd.DataFrame | None = None,
    n_simulations: int = 1000,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Perform weight sensitivity check and PCA index comparison.

    Parameters
    ----------
    features_df : pd.DataFrame, optional
        Dataframe containing dimension risk scores.
    n_simulations : int, default 1000
        Number of Monte Carlo Dirichlet weight draws.
    random_state : int, default 42
        Seed for reproducibility.

    Returns
    -------
    dict
        Dictionary containing robustness metrics, PCA variance explained, and correlations.
    """
    if features_df is None:
        features_path = ROOT / "data" / "processed" / "features.parquet"
        if not features_path.exists():
            raise FileNotFoundError(f"{features_path} does not exist.")
        features_df = pd.read_parquet(features_path)

    # Available observed dimensions
    dim_candidates = ["edu_risk", "health_risk", "infra_risk"]
    available_dims = [c for c in dim_candidates if c in features_df.columns and features_df[c].notna().any()]

    if len(available_dims) < 2:
        raise ValueError("At least 2 dimension columns required for sensitivity analysis.")

    X = features_df[available_dims].dropna()
    baseline_scores = X.mean(axis=1)
    base_top10 = set(baseline_scores.nlargest(10).index)

    # Monte Carlo Dirichlet perturbation around equal weights
    rng = np.random.default_rng(random_state)
    alpha = [5.0] * len(available_dims)
    weights = rng.dirichlet(alpha, size=n_simulations)

    top10_overlaps = []
    rhos = []
    for w in weights:
        sim_scores = (X * w).sum(axis=1)
        sim_top10 = set(sim_scores.nlargest(10).index)
        overlap = len(base_top10.intersection(sim_top10)) / 10.0
        top10_overlaps.append(overlap)
        r, _ = spearmanr(baseline_scores, sim_scores)
        rhos.append(r)

    # Unsupervised PCA Index Comparison
    pca = PCA(n_components=1)
    pc1 = pca.fit_transform(X).ravel()
    # Align direction with risk (positive correlation)
    if np.corrcoef(pc1, baseline_scores)[0, 1] < 0:
        pc1 = -pc1
    pca_spearman, _ = spearmanr(baseline_scores, pc1)
    pc1_var_explained = float(pca.explained_variance_ratio_[0])

    results = {
        "framework": "Alkire-Foster / Human Development Index (HDI) Normative Equal Weighting",
        "evaluated_dimensions": available_dims,
        "n_simulations": n_simulations,
        "mean_top10_stability": round(float(np.mean(top10_overlaps)), 4),
        "mean_spearman_rho": round(float(np.mean(rhos)), 4),
        "min_spearman_rho": round(float(np.min(rhos)), 4),
        "pca_variance_explained": round(pc1_var_explained, 4),
        "pca_spearman_rho": round(float(pca_spearman), 4),
        "justification": (
            "Equal weighting reflects the normative principle that rights to education, health, "
            "and basic physical infrastructure are mutually non-substitutable and intrinsically of equal "
            f"importance. Empirical robustness testing demonstrates that the Top-10 vulnerable priority list "
            f"has {np.mean(top10_overlaps):.1%} stability under random weight perturbations (+/- 30%), and the "
            f"equal-weight index correlates at rho={pca_spearman:.4f} with an unsupervised data-driven PCA index."
        ),
    }

    # Save to metadata
    out_dir = ROOT / "data" / "metadata"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "weight_sensitivity.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    res = evaluate_weight_sensitivity()
    print("=" * 60)
    print("SAHAAYA Weight Justification & Sensitivity Analysis")
    print("=" * 60)
    print(f"Evaluated Dimensions:    {res['evaluated_dimensions']}")
    print(f"Mean Top-10 Stability:   {res['mean_top10_stability']:.1%}")
    print(f"Mean Spearman rho:       {res['mean_spearman_rho']:.4f} (Min: {res['min_spearman_rho']:.4f})")
    print(f"PCA PC1 Var Explained:   {res['pca_variance_explained']:.1%}")
    print(f"Equal vs PCA rho:        {res['pca_spearman_rho']:.4f}")
    print("=" * 60)
