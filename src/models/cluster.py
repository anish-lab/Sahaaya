"""
K-Means clustering of Tamil Nadu districts based on vulnerability indicators.

Clusters districts into groups with similar socio-economic profiles using
numeric indicator columns from the shared features.parquet dataset.
Automatically selects the optimal number of clusters via silhouette analysis
when not specified.

Outputs:
    - data/processed/cluster_assignments.parquet
    - data/processed/cluster_profiles.parquet
    - models/cluster_model.pkl
    - models/cluster_scaler.pkl
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


# ---------------------------------------------------------------------------
# Columns that must NEVER be used as input features
# ---------------------------------------------------------------------------
_EXCLUDE_COLS = {
    "district_id", "district_name", "state", "period", "year",
    "risk_band", "cluster", "anomaly_flag", "anomaly_score",
    "pred_next_score", "data_completeness", "unusual_features",
}


class ClusterModel:
    """K-Means clustering on district-level vulnerability indicators.

    Parameters
    ----------
    features_path : Path or str
        Path to the ``features.parquet`` file.
    n_clusters : int or None
        Fixed number of clusters.  If ``None``, the optimal *k* is chosen
        automatically via silhouette analysis.
    max_clusters : int
        Upper bound for *k* when searching for the optimal value.
    random_state : int
        Seed for reproducibility.
    """

    def __init__(
        self,
        features_path: Path | str,
        n_clusters: int | None = None,
        max_clusters: int = 8,
        random_state: int = 42,
    ) -> None:
        self.features_path = Path(features_path)
        self.n_clusters = n_clusters
        self.max_clusters = max_clusters
        self.random_state = random_state

        # Resolved at fit-time
        self.model: KMeans | None = None
        self.scaler: StandardScaler | None = None

    # ------------------------------------------------------------------
    # Feature selection
    # ------------------------------------------------------------------
    def _select_features(self, df: pd.DataFrame) -> list[str]:
        """Select numeric indicator columns, excluding IDs, labels, and
        model-output columns.

        Parameters
        ----------
        df : pd.DataFrame
            The loaded features dataframe.

        Returns
        -------
        list[str]
            Column names to use for clustering.
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [
            c for c in numeric_cols if c.lower() not in _EXCLUDE_COLS
        ]
        return feature_cols

    # ------------------------------------------------------------------
    # Data preparation
    # ------------------------------------------------------------------
    def _prepare_data(
        self, df: pd.DataFrame, feature_cols: list[str]
    ) -> tuple[np.ndarray, StandardScaler]:
        """Handle missing values and scale features.

        * Rows with > 50 % missing values across ``feature_cols`` are dropped.
        * Remaining NaNs are imputed with the column median.
        * Features are standardised with :class:`StandardScaler`.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain ``feature_cols``.
        feature_cols : list[str]
            Columns to prepare.

        Returns
        -------
        tuple[np.ndarray, StandardScaler]
            Scaled feature matrix and the fitted scaler.
        """
        subset = df[feature_cols].copy()

        # Drop columns that are completely all-NaN
        subset = subset.dropna(axis=1, how="all")
        if subset.empty or subset.shape[1] == 0:
            raise ValueError("No valid features with data available for clustering.")

        # Impute remaining NaN with column median (fallback to 0.0)
        medians = subset.median().fillna(0.0)
        subset = subset.fillna(medians)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(subset.values)
        return X_scaled, scaler

    # ------------------------------------------------------------------
    # Optimal k selection
    # ------------------------------------------------------------------
    def find_optimal_k(
        self, X_scaled: np.ndarray, k_range: range | None = None
    ) -> tuple[int, dict[int, float]]:
        """Evaluate silhouette scores for a range of *k* values.

        Parameters
        ----------
        X_scaled : np.ndarray
            Scaled feature matrix.
        k_range : range or None
            Range of *k* values to evaluate (default 2..max_clusters).

        Returns
        -------
        tuple[int, dict[int, float]]
            Best *k* and a mapping ``{k: silhouette_score}``.
        """
        if k_range is None:
            k_range = range(2, self.max_clusters + 1)

        scores: dict[int, float] = {}
        for k in k_range:
            if k >= X_scaled.shape[0]:
                break
            km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = km.fit_predict(X_scaled)
            s = silhouette_score(X_scaled, labels)
            scores[k] = round(float(s), 4)
            print(f"  k={k}  silhouette={s:.4f}")

        best_k = max(scores, key=scores.get)
        print(f"  => Best k = {best_k} (silhouette = {scores[best_k]:.4f})")
        return best_k, scores

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------
    def fit(self) -> pd.DataFrame:
        """Load data, select features, prepare, cluster, and save artefacts.

        Returns
        -------
        pd.DataFrame
            The original dataframe augmented with a ``cluster`` column
            containing the new assignments.
        """
        # Load --------------------------------------------------------
        if not self.features_path.exists():
            print(f"[ERROR] Features file not found: {self.features_path}")
            sys.exit(1)

        df = pd.read_parquet(self.features_path)
        if df.empty:
            print("[ERROR] features.parquet is empty -- nothing to cluster.")
            sys.exit(1)

        feature_cols = self._select_features(df)
        if not feature_cols:
            print("[ERROR] No numeric indicator columns found for clustering.")
            sys.exit(1)

        print(f"[ClusterModel] Using {len(feature_cols)} features: {feature_cols}")

        # Prepare features (drop completely empty columns and impute medians)
        feature_cols = [c for c in feature_cols if df[c].notna().any()]
        subset = df[feature_cols].copy()
        medians = subset.median().fillna(0.0)
        subset = subset.fillna(medians)
        valid_mask = pd.Series(True, index=df.index)

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(subset.values)

        # Optimal k ---------------------------------------------------
        if self.n_clusters is None:
            print("[ClusterModel] Searching for optimal k ...")
            best_k, _ = self.find_optimal_k(X_scaled)
            self.n_clusters = best_k
        else:
            print(f"[ClusterModel] Using user-specified k = {self.n_clusters}")

        # Fit KMeans ---------------------------------------------------
        self.model = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10,
        )
        labels = self.model.fit_predict(X_scaled)

        # Assign labels back (only valid rows get a label)
        df["cluster"] = np.nan
        df.loc[valid_mask, "cluster"] = labels.astype(int)

        # Save model artefacts ----------------------------------------
        root = self.features_path.parents[1]  # project root
        models_dir = root / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.model, models_dir / "cluster_model.pkl")
        joblib.dump(self.scaler, models_dir / "cluster_scaler.pkl")
        print(f"[ClusterModel] Saved model artefacts to {models_dir}")

        return df

    # ------------------------------------------------------------------
    # Profile clusters
    # ------------------------------------------------------------------
    def profile_clusters(
        self, df: pd.DataFrame, feature_cols: list[str]
    ) -> pd.DataFrame:
        """Compute per-cluster summary statistics.

        For each cluster, reports the mean of every feature column, cluster
        size, and a comma-separated list of constituent districts.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain ``cluster`` and ``district_name`` columns plus
            ``feature_cols``.
        feature_cols : list[str]
            Numeric columns to summarise.

        Returns
        -------
        pd.DataFrame
            One row per cluster.
        """
        valid = df.dropna(subset=["cluster"]).copy()
        valid["cluster"] = valid["cluster"].astype(int)

        profiles = valid.groupby("cluster")[feature_cols].mean()
        profiles["size"] = valid.groupby("cluster")["cluster"].count()
        profiles["top_districts"] = (
            valid.groupby("cluster")["district_name"]
            .apply(lambda s: ", ".join(sorted(s.unique())))
        )
        profiles = profiles.reset_index()

        # Save ---------------------------------------------------------
        out_dir = self.features_path.parent  # data/processed
        out_dir.mkdir(parents=True, exist_ok=True)
        profiles.to_parquet(out_dir / "cluster_profiles.parquet", index=False)
        print(f"[ClusterModel] Saved cluster profiles to {out_dir / 'cluster_profiles.parquet'}")
        return profiles

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------
    def run(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Execute the full clustering pipeline.

        1. Fit the model and assign clusters.
        2. Profile each cluster.
        3. Save ``cluster_assignments.parquet`` and
           ``cluster_profiles.parquet``.

        Returns
        -------
        tuple[pd.DataFrame, pd.DataFrame]
            ``(cluster_assignments, cluster_profiles)``
        """
        df = self.fit()
        feature_cols = self._select_features(df)

        profiles = self.profile_clusters(df, feature_cols)

        # Save assignments
        out_dir = self.features_path.parent
        assignments = df[["district_id", "district_name", "cluster"]].copy()
        assignments.to_parquet(
            out_dir / "cluster_assignments.parquet", index=False
        )
        print(
            f"[ClusterModel] Saved cluster assignments to "
            f"{out_dir / 'cluster_assignments.parquet'}"
        )

        return assignments, profiles


# ======================================================================
# CLI entry-point
# ======================================================================
if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))

    features_path = ROOT / "data" / "processed" / "features.parquet"
    model = ClusterModel(features_path=features_path)
    assignments, profiles = model.run()

    print("\n--- Cluster Assignments (head) ---")
    print(assignments.head(10).to_string(index=False))
    print("\n--- Cluster Profiles ---")
    print(profiles.to_string(index=False))
