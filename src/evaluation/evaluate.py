from __future__ import annotations

"""
Model evaluation utilities for SAHAAYA.

Provides functions to evaluate clustering quality, anomaly detection
performance, and to generate a combined Markdown report.

Outputs:
    - reports/model_evaluation_report.md  (via save_model_report)
"""


import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    silhouette_score,
    calinski_harabasz_score,
    davies_bouldin_score,
)


# ======================================================================
# Clustering evaluation
# ======================================================================
def evaluate_clustering(X: np.ndarray, labels: np.ndarray) -> dict:
    """Compute standard internal clustering metrics.

    Parameters
    ----------
    X : np.ndarray
        Feature matrix (scaled or unscaled; should match what was used
        for clustering).
    labels : np.ndarray
        Cluster labels (integers).

    Returns
    -------
    dict
        ``{"silhouette_score", "calinski_harabasz", "davies_bouldin"}``.
        Values are ``float`` rounded to 4 decimal places, or ``NaN`` if
        the metric could not be computed (e.g., only 1 cluster).
    """
    unique_labels = set(labels)
    n_clusters = len(unique_labels - {-1})

    result: dict = {
        "silhouette_score": np.nan,
        "calinski_harabasz": np.nan,
        "davies_bouldin": np.nan,
    }

    if n_clusters < 2:
        print(
            "[evaluate_clustering] Fewer than 2 clusters -- "
            "metrics cannot be computed."
        )
        return result

    try:
        result["silhouette_score"] = round(
            float(silhouette_score(X, labels)), 4
        )
    except Exception as exc:
        print(f"[evaluate_clustering] silhouette_score error: {exc}")

    try:
        result["calinski_harabasz"] = round(
            float(calinski_harabasz_score(X, labels)), 4
        )
    except Exception as exc:
        print(f"[evaluate_clustering] calinski_harabasz error: {exc}")

    try:
        result["davies_bouldin"] = round(
            float(davies_bouldin_score(X, labels)), 4
        )
    except Exception as exc:
        print(f"[evaluate_clustering] davies_bouldin error: {exc}")

    return result


# ======================================================================
# Anomaly detection evaluation
# ======================================================================
def evaluate_anomaly_detection(results_df: pd.DataFrame) -> dict:
    """Compute descriptive statistics for anomaly detection results.

    Since ground-truth labels are unavailable, this function reports
    distribution-level summaries rather than precision/recall.

    Parameters
    ----------
    results_df : pd.DataFrame
        Must contain ``anomaly_flag`` (bool) and ``anomaly_score``
        (float 0-100) columns.

    Returns
    -------
    dict
        Summary statistics including counts, percentages, and score
        distribution moments.
    """
    total = len(results_df)
    flagged = results_df["anomaly_flag"].sum() if "anomaly_flag" in results_df.columns else 0
    scores = results_df["anomaly_score"].dropna() if "anomaly_score" in results_df.columns else pd.Series(dtype=float)

    result = {
        "total_rows": int(total),
        "num_flagged": int(flagged),
        "pct_flagged": round(float(flagged / total * 100), 2) if total > 0 else 0.0,
        "mean_anomaly_score": round(float(scores.mean()), 4) if len(scores) > 0 else np.nan,
        "median_anomaly_score": round(float(scores.median()), 4) if len(scores) > 0 else np.nan,
        "std_anomaly_score": round(float(scores.std()), 4) if len(scores) > 0 else np.nan,
        "min_anomaly_score": round(float(scores.min()), 4) if len(scores) > 0 else np.nan,
        "max_anomaly_score": round(float(scores.max()), 4) if len(scores) > 0 else np.nan,
    }
    return result


# ======================================================================
# Report generation
# ======================================================================
def generate_model_report(
    cluster_eval: dict,
    anomaly_eval: dict,
) -> str:
    """Build a Markdown-formatted model evaluation report.

    Parameters
    ----------
    cluster_eval : dict
        Output of :func:`evaluate_clustering`.
    anomaly_eval : dict
        Output of :func:`evaluate_anomaly_detection`.

    Returns
    -------
    str
        Markdown report text.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# SAHAAYA -- Model Evaluation Report",
        "",
        f"Generated: {ts}",
        "",
        "---",
        "",
        "## 1. Clustering Evaluation",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]

    for key in ["silhouette_score", "calinski_harabasz", "davies_bouldin"]:
        val = cluster_eval.get(key, "N/A")
        if isinstance(val, float) and not np.isnan(val):
            val_str = f"{val:.4f}"
        else:
            val_str = "N/A"
        lines.append(f"| {key.replace('_', ' ').title()} | {val_str} |")

    lines += [
        "",
        "**Interpretation:**",
        "",
        "- **Silhouette Score** ranges from -1 to 1; higher is better "
        "(>0.5 = strong structure).",
        "- **Calinski-Harabasz Index**: higher is better (ratio of between- "
        "to within-cluster dispersion).",
        "- **Davies-Bouldin Index**: lower is better (average similarity "
        "between each cluster and its most similar cluster).",
        "",
        "---",
        "",
        "## 2. Anomaly Detection Evaluation",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]

    for key, label in [
        ("total_rows", "Total Rows"),
        ("num_flagged", "Anomalies Flagged"),
        ("pct_flagged", "% Flagged"),
        ("mean_anomaly_score", "Mean Anomaly Score"),
        ("median_anomaly_score", "Median Anomaly Score"),
        ("std_anomaly_score", "Std Dev Anomaly Score"),
        ("min_anomaly_score", "Min Anomaly Score"),
        ("max_anomaly_score", "Max Anomaly Score"),
    ]:
        val = anomaly_eval.get(key, "N/A")
        if isinstance(val, float):
            val_str = f"{val:.4f}" if not np.isnan(val) else "N/A"
        else:
            val_str = str(val)
        lines.append(f"| {label} | {val_str} |")

    lines += [
        "",
        "**Note:** Without ground-truth anomaly labels, these are "
        "descriptive statistics only. Manual review of flagged districts "
        "is recommended.",
        "",
        "---",
        "",
        "*Report generated by SAHAAYA evaluation module.*",
    ]

    return "\n".join(lines)


def save_model_report(report_str: str, root: Path | None = None) -> Path:
    """Save the Markdown report to ``reports/model_evaluation_report.md``.

    Parameters
    ----------
    report_str : str
        Markdown report content.
    root : Path or None
        Project root.  If ``None``, resolved from this file's location.

    Returns
    -------
    Path
        Absolute path to the saved report.
    """
    if root is None:
        root = Path(__file__).resolve().parents[2]
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "model_evaluation_report.md"
    out_path.write_text(report_str, encoding="utf-8")
    print(f"[evaluate] Saved report to {out_path}")
    return out_path


# ======================================================================
# CLI entry-point
# ======================================================================
if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))

    import joblib

    features_path = ROOT / "data" / "processed" / "features.parquet"
    if not features_path.exists():
        print(f"[ERROR] Features file not found: {features_path}")
        sys.exit(1)

    df = pd.read_parquet(features_path)

    # --- Clustering evaluation ---
    cluster_eval: dict = {
        "silhouette_score": np.nan,
        "calinski_harabasz": np.nan,
        "davies_bouldin": np.nan,
    }

    cluster_model_path = ROOT / "models" / "cluster_model.pkl"
    cluster_scaler_path = ROOT / "models" / "cluster_scaler.pkl"

    if cluster_model_path.exists() and cluster_scaler_path.exists():
        km = joblib.load(cluster_model_path)
        scaler = joblib.load(cluster_scaler_path)

        # Re-derive numeric features (same logic as ClusterModel)
        _EXCLUDE = {
            "district_id", "district_name", "state", "period", "year",
            "risk_band", "cluster", "anomaly_flag", "anomaly_score",
            "pred_next_score", "data_completeness", "unusual_features",
        }
        feature_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if c.lower() not in _EXCLUDE
        ]
        subset = df[feature_cols].copy()
        valid_mask = subset.isna().sum(axis=1) <= len(feature_cols) * 0.5
        subset = subset.loc[valid_mask].fillna(subset.loc[valid_mask].median())
        X_scaled = scaler.transform(subset.values)
        labels = km.predict(X_scaled)

        cluster_eval = evaluate_clustering(X_scaled, labels)
        print("[evaluate] Clustering metrics computed.")
    else:
        print("[evaluate] Cluster model not found -- skipping clustering eval.")

    # --- Anomaly evaluation ---
    anomaly_results_path = ROOT / "data" / "processed" / "anomaly_results.parquet"
    if anomaly_results_path.exists():
        anomaly_df = pd.read_parquet(anomaly_results_path)
        anomaly_eval = evaluate_anomaly_detection(anomaly_df)
        print("[evaluate] Anomaly detection metrics computed.")
    else:
        anomaly_eval = evaluate_anomaly_detection(df)
        print(
            "[evaluate] anomaly_results.parquet not found -- "
            "using features.parquet columns if available."
        )

    # --- Generate and save report ---
    report = generate_model_report(cluster_eval, anomaly_eval)
    out = save_model_report(report, ROOT)
    print(f"\nReport saved to: {out}")
