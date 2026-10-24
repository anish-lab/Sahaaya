"""
Isolation Forest anomaly detection for Tamil Nadu district indicators.

Identifies districts whose socio-economic profiles deviate significantly
from the norm.  For each flagged anomaly, reports which specific features
are unusual (> 1.5 standard deviations from the mean).

Outputs:
    - data/processed/anomaly_results.parquet
    - models/anomaly_model.pkl
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Columns that must NEVER be used as input features
# ---------------------------------------------------------------------------
_EXCLUDE_COLS = {
    "district_id", "district_name", "state", "period", "year",
    "risk_band", "cluster", "anomaly_flag", "anomaly_score",
    "pred_next_score", "data_completeness", "unusual_features",
}


class AnomalyDetector:
    """Isolation Forest anomaly detection on district indicators.

    Parameters
    ----------
    features_path : Path or str
        Path to ``features.parquet``.
    contamination : float
        Expected proportion of anomalies in the data (passed to
        :class:`~sklearn.ensemble.IsolationForest`).
    random_state : int
        Seed for reproducibility.
    """

    def __init__(
        self,
        features_path: Path | str,
        contamination: float = 0.1,
        random_state: int = 42,
    ) -> None:
        self.features_path = Path(features_path)
        self.contamination = contamination
        self.random_state = random_state

        self.model: IsolationForest | None = None
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
            Column names to use for anomaly detection.
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
            raise ValueError("No valid features with data available for anomaly detection.")

        # Impute remaining NaN with column median (fallback to 0.0)
        medians = subset.median().fillna(0.0)
        subset = subset.fillna(medians)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(subset.values)
        return X_scaled, scaler

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------
    def fit(self) -> pd.DataFrame:
        """Load data, fit Isolation Forest, score and flag anomalies.

        The ``anomaly_score`` is the negated decision function scaled to
        0--100 where **higher = more anomalous**.  ``anomaly_flag`` is
        ``True`` for rows predicted as anomalies by the forest.

        Returns
        -------
        pd.DataFrame
            Original data augmented with ``anomaly_flag`` and
            ``anomaly_score``.
        """
        if not self.features_path.exists():
            print(f"[ERROR] Features file not found: {self.features_path}")
            sys.exit(1)

        df = pd.read_parquet(self.features_path)
        if df.empty:
            print("[ERROR] features.parquet is empty -- nothing to analyse.")
            sys.exit(1)

        feature_cols = self._select_features(df)
        if not feature_cols:
            print("[ERROR] No numeric indicator columns found for anomaly detection.")
            sys.exit(1)

        print(f"[AnomalyDetector] Using {len(feature_cols)} features: {feature_cols}")

        # Prepare data (drop completely empty columns and impute medians)
        feature_cols = [c for c in feature_cols if df[c].notna().any()]
        subset = df[feature_cols].copy()
        medians = subset.median().fillna(0.0)
        subset = subset.fillna(medians)
        valid_mask = pd.Series(True, index=df.index)

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(subset.values)

        # Fit Isolation Forest -----------------------------------------
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
        )
        predictions = self.model.fit_predict(X_scaled)  # +1 normal, -1 anomaly
        raw_scores = self.model.decision_function(X_scaled)

        # Scale raw scores to 0-100 (higher = more anomalous)
        # decision_function: higher = more normal, so negate
        negated = -raw_scores
        score_min, score_max = negated.min(), negated.max()
        if score_max - score_min > 0:
            scaled_scores = (negated - score_min) / (score_max - score_min) * 100.0
        else:
            scaled_scores = np.full_like(negated, 50.0)

        # Assign back to dataframe
        df["anomaly_flag"] = False
        df.loc[valid_mask, "anomaly_flag"] = predictions == -1
        df["anomaly_score"] = np.nan
        df.loc[valid_mask, "anomaly_score"] = scaled_scores

        # Save model ---------------------------------------------------
        root = self.features_path.parents[1]
        models_dir = root / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, models_dir / "anomaly_model.pkl")
        print(f"[AnomalyDetector] Saved model to {models_dir / 'anomaly_model.pkl'}")

        # Store for explain step
        self._feature_cols = feature_cols
        self._X_scaled = X_scaled
        self._valid_mask = valid_mask

        return df

    # ------------------------------------------------------------------
    # Explain anomalies
    # ------------------------------------------------------------------
    def explain_anomalies(
        self,
        df: pd.DataFrame,
        feature_cols: list[str],
        X_scaled: np.ndarray,
    ) -> pd.DataFrame:
        """Identify which features deviate most for each flagged anomaly.

        A feature is considered *unusual* if its absolute z-score exceeds
        1.5 standard deviations from the population mean (zero in scaled
        space).

        Parameters
        ----------
        df : pd.DataFrame
            Must contain ``anomaly_flag`` and ``district_name``.
        feature_cols : list[str]
            Feature column names corresponding to ``X_scaled`` columns.
        X_scaled : np.ndarray
            Scaled feature matrix (same row order as valid rows in ``df``).

        Returns
        -------
        pd.DataFrame
            Input dataframe with an added ``unusual_features`` column.
        """
        df["unusual_features"] = ""

        # Build a local frame for scaled values aligned to valid indices
        valid_idx = df.index[self._valid_mask]
        anomaly_idx = df.loc[valid_idx].loc[
            df.loc[valid_idx, "anomaly_flag"] == True
        ].index

        if len(anomaly_idx) == 0:
            print("[AnomalyDetector] No anomalies flagged -- nothing to explain.")
            return df

        # Map valid_idx position -> row in X_scaled
        idx_to_row = {idx: row for row, idx in enumerate(valid_idx)}

        for idx in anomaly_idx:
            row_num = idx_to_row[idx]
            vals = X_scaled[row_num]
            unusual = [
                feature_cols[j]
                for j, v in enumerate(vals)
                if abs(v) > 1.5
            ]
            df.at[idx, "unusual_features"] = ", ".join(unusual) if unusual else "none"

        n_flagged = len(anomaly_idx)
        print(f"[AnomalyDetector] Explained {n_flagged} anomalies.")
        return df

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------
    def run(self) -> pd.DataFrame:
        """Execute the full anomaly detection pipeline.

        1. Fit the Isolation Forest and compute scores.
        2. Explain each flagged anomaly.
        3. Save ``anomaly_results.parquet``.

        Returns
        -------
        pd.DataFrame
            Results with ``anomaly_flag``, ``anomaly_score``, and
            ``unusual_features`` columns.
        """
        df = self.fit()
        df = self.explain_anomalies(
            df, self._feature_cols, self._X_scaled
        )

        # Save results -------------------------------------------------
        out_dir = self.features_path.parent
        result_cols = [
            "district_id", "district_name", "anomaly_flag",
            "anomaly_score", "unusual_features",
        ]
        # Include any extra id columns present
        for col in ["year", "period"]:
            if col in df.columns:
                result_cols.insert(2, col)

        results = df[result_cols].copy()
        results.to_parquet(out_dir / "anomaly_results.parquet", index=False)
        print(
            f"[AnomalyDetector] Saved results to "
            f"{out_dir / 'anomaly_results.parquet'}"
        )
        return results


# ======================================================================
# CLI entry-point
# ======================================================================
if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))

    features_path = ROOT / "data" / "processed" / "features.parquet"
    detector = AnomalyDetector(features_path=features_path)
    results = detector.run()

    print("\n--- Anomaly Results Summary ---")
    flagged = results[results["anomaly_flag"] == True]
    print(f"Total rows:     {len(results)}")
    print(f"Flagged:        {len(flagged)}")
    if not flagged.empty:
        print("\nFlagged districts:")
        print(flagged.to_string(index=False))
