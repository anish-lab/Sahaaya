"""
What-if scenario simulator for SAHAAYA.

Allows users to adjust individual district indicators and immediately see
the effect on dimension risk scores, overall vulnerability score, and risk
band -- without retraining any model.

All outputs are clearly labelled as *hypothetical model-based estimates*.

This module is interactive-only and does not persist any results.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import joblib


# ---------------------------------------------------------------------------
# Columns that are model outputs / identifiers (not adjustable indicators)
# ---------------------------------------------------------------------------
_NON_INDICATOR_COLS = {
    "district_id", "district_name", "state", "period", "year",
    "risk_band", "cluster", "anomaly_flag", "anomaly_score",
    "pred_next_score", "data_completeness", "unusual_features",
    "overall_score", "edu_risk", "health_risk", "emp_risk", "infra_risk",
}

# ---------------------------------------------------------------------------
# Scoring methodology (mirrors make_mock_data / vulnerability_index logic)
# ---------------------------------------------------------------------------
# Dimension risk scores in the current dataset are stored directly in
# edu_risk, health_risk, emp_risk, infra_risk (0-100, higher = worse).
#
# Because we don't yet have a separate vulnerability_index.py that maps
# raw indicators -> dimension scores via a known formula, the simulator
# re-derives dimension scores using a simple linear min-max rescaling
# within the observed data range.  This is the same approach the mock
# data generator uses.
#
# When a proper vulnerability_index module is added, the scoring functions
# below should be swapped out for its canonical implementation.
# ---------------------------------------------------------------------------

# Mapping: indicator column -> which dimension it contributes to
# and direction (+1 = higher value means higher risk, -1 = inverted)
_INDICATOR_DIMENSION_MAP: dict[str, tuple[str, int]] = {
    "dropout_rate":              ("edu_risk",   +1),
    "anaemia_pct":               ("health_risk", +1),
    "mgnrega_persondays_per_hh": ("emp_risk",   -1),  # more persondays = lower risk
    "school_infra_score":        ("infra_risk", -1),  # higher infra score = lower risk
}


def _risk_band(score: float) -> str:
    """Map an overall score (0-100) to a risk band label."""
    if np.isnan(score):
        return "Unknown"
    if score < 35:
        return "Low"
    if score < 50:
        return "Moderate"
    if score < 65:
        return "High"
    return "Critical"


class WhatIfSimulator:
    """Interactive what-if simulator for district vulnerability.

    Parameters
    ----------
    features_path : Path or str
        Path to ``features.parquet``.
    """

    def __init__(self, features_path: Path | str) -> None:
        self.features_path = Path(features_path)

        if not self.features_path.exists():
            print(f"[ERROR] Features file not found: {self.features_path}")
            sys.exit(1)

        self.df = pd.read_parquet(self.features_path)
        if self.df.empty:
            print("[ERROR] features.parquet is empty -- nothing to simulate.")
            sys.exit(1)

        # Identify adjustable numeric indicator columns
        self._indicator_cols = [
            c
            for c in self.df.select_dtypes(include=[np.number]).columns
            if c.lower() not in _NON_INDICATOR_COLS
        ]

        # Compute data-range bounds for each indicator (across all rows)
        self._ranges: dict[str, dict] = {}
        for col in self._indicator_cols:
            vals = self.df[col].dropna()
            self._ranges[col] = {
                "min": float(vals.min()) if len(vals) else 0.0,
                "max": float(vals.max()) if len(vals) else 100.0,
                "median": float(vals.median()) if len(vals) else np.nan,
            }

        # Try to load a predictive model if one exists
        root = self.features_path.parents[1]
        pred_model_path = root / "models" / "prediction_model.pkl"
        self._pred_model = None
        if pred_model_path.exists():
            try:
                self._pred_model = joblib.load(pred_model_path)
                print("[WhatIfSimulator] Loaded prediction model.")
            except Exception as exc:
                warnings.warn(f"Could not load prediction model: {exc}")

        print(
            f"[WhatIfSimulator] Ready. "
            f"{len(self._indicator_cols)} adjustable indicators, "
            f"{len(self.df)} rows loaded."
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def get_district_baseline(self, district_name: str) -> dict:
        """Return the district's most recent actual indicator values and
        computed scores.

        Parameters
        ----------
        district_name : str
            Canonical district name (case-insensitive match).

        Returns
        -------
        dict
            Keys include each indicator, the four dimension scores,
            ``overall_score``, and ``risk_band``.

        Raises
        ------
        ValueError
            If ``district_name`` is not found.
        """
        mask = self.df["district_name"].str.lower() == district_name.lower()
        matches = self.df.loc[mask]
        if matches.empty:
            raise ValueError(
                f"District '{district_name}' not found.  "
                f"Available: {sorted(self.df['district_name'].unique())}"
            )

        # Pick most recent row (by 'year' or 'period' if available)
        sort_col = "year" if "year" in matches.columns else "period"
        row = matches.sort_values(sort_col, ascending=False).iloc[0]

        baseline: dict = {}
        for col in self._indicator_cols:
            baseline[col] = float(row[col]) if pd.notna(row[col]) else np.nan
        for dim in ["edu_risk", "health_risk", "emp_risk", "infra_risk"]:
            baseline[dim] = float(row[dim]) if dim in row and pd.notna(row[dim]) else np.nan
        baseline["overall_score"] = float(row["overall_score"]) if pd.notna(row.get("overall_score")) else np.nan
        baseline["risk_band"] = row.get("risk_band", "Unknown")
        return baseline

    def get_adjustable_indicators(self) -> list[dict]:
        """Return metadata for each adjustable indicator.

        Returns
        -------
        list[dict]
            Each dict has keys: ``name``, ``current_min``, ``current_max``,
            ``median``, ``unit``, ``description``.
        """
        descriptions = {
            "dropout_rate": "School dropout rate (%)",
            "anaemia_pct": "Anaemia prevalence among women (%)",
            "mgnrega_persondays_per_hh": "MGNREGA person-days generated per household",
            "school_infra_score": "Composite school infrastructure score (0-100)",
        }
        result = []
        for col in self._indicator_cols:
            r = self._ranges[col]
            result.append({
                "name": col,
                "current_min": r["min"],
                "current_max": r["max"],
                "median": r["median"],
                "unit": "various",
                "description": descriptions.get(col, col.replace("_", " ").title()),
            })
        return result

    # ------------------------------------------------------------------
    # Core simulation
    # ------------------------------------------------------------------
    def _compute_dimension_score(
        self,
        indicator_value: float,
        indicator_name: str,
    ) -> float | None:
        """Re-derive a dimension score from a raw indicator value using
        min-max rescaling within the observed data range.

        Parameters
        ----------
        indicator_value : float
            The (possibly adjusted) raw indicator value.
        indicator_name : str
            Column name of the indicator.

        Returns
        -------
        float or None
            Score in 0-100, or None if mapping is unknown.
        """
        mapping = _INDICATOR_DIMENSION_MAP.get(indicator_name)
        if mapping is None:
            return None

        _, direction = mapping
        r = self._ranges[indicator_name]
        rng = r["max"] - r["min"]
        if rng == 0:
            return 50.0

        # Normalise to 0-1
        normalised = (indicator_value - r["min"]) / rng

        # If inverted (direction == -1), flip so that higher value = lower risk
        if direction == -1:
            normalised = 1.0 - normalised

        return float(np.clip(normalised * 100.0, 0.0, 100.0))

    def simulate(
        self,
        district_name: str,
        adjustments: dict[str, float],
    ) -> dict:
        """Run a what-if scenario.

        Parameters
        ----------
        district_name : str
            Canonical district name.
        adjustments : dict[str, float]
            Mapping of ``{indicator_name: new_value}``.

        Returns
        -------
        dict
            ``{"baseline": {...}, "scenario": {...}, "delta": {...},
            "adjustments_applied": [...],
            "note": "hypothetical model-based estimates"}``.
        """
        baseline = self.get_district_baseline(district_name)
        scenario = dict(baseline)  # shallow copy
        applied: list[str] = []

        for indicator, new_value in adjustments.items():
            if indicator in {"edu_risk", "health_risk", "emp_risk", "infra_risk"}:
                scenario[indicator] = float(np.clip(new_value, 0.0, 100.0))
                applied.append(f"{indicator}: {baseline.get(indicator, '?')} -> {new_value}")
                continue

            if indicator not in self._indicator_cols:
                warnings.warn(
                    f"Indicator '{indicator}' is not adjustable -- skipped."
                )
                continue

            r = self._ranges[indicator]
            if new_value < r["min"] or new_value > r["max"]:
                warnings.warn(
                    f"Adjustment for '{indicator}' = {new_value} is outside "
                    f"observed data range [{r['min']:.2f}, {r['max']:.2f}].  "
                    f"Proceeding, but results may be less reliable."
                )

            scenario[indicator] = new_value
            applied.append(f"{indicator}: {baseline.get(indicator, '?')} -> {new_value}")

        # Recompute dimension scores using the same methodology
        for indicator in self._indicator_cols:
            mapping = _INDICATOR_DIMENSION_MAP.get(indicator)
            if mapping is None:
                continue
            dim_name, _ = mapping
            new_dim_score = self._compute_dimension_score(
                scenario[indicator], indicator
            )
            if new_dim_score is not None:
                scenario[dim_name] = new_dim_score

        # Recompute overall score and risk band
        dim_scores = [
            scenario[d]
            for d in ["edu_risk", "health_risk", "emp_risk", "infra_risk"]
            if not np.isnan(scenario.get(d, np.nan))
        ]
        if dim_scores:
            scenario["overall_score"] = float(np.mean(dim_scores))
        else:
            scenario["overall_score"] = np.nan
        scenario["risk_band"] = _risk_band(scenario["overall_score"])

        # Predictive model (if available)
        if self._pred_model is not None:
            try:
                pred_features = np.array(
                    [[scenario.get(c, np.nan) for c in self._indicator_cols]]
                )
                scenario["pred_next_score"] = float(
                    self._pred_model.predict(pred_features)[0]
                )
            except Exception:
                scenario["pred_next_score"] = np.nan

        # Compute deltas
        delta: dict = {}
        for key in baseline:
            b = baseline[key]
            s = scenario.get(key, b)
            if isinstance(b, (int, float)) and isinstance(s, (int, float)):
                if not (np.isnan(b) or np.isnan(s)):
                    delta[key] = round(s - b, 4)

        return {
            "baseline": baseline,
            "scenario": scenario,
            "delta": delta,
            "adjustments_applied": applied,
            "note": (
                "HYPOTHETICAL MODEL-BASED ESTIMATES. "
                "These projections use simplified rescaling and should not "
                "be treated as precise policy predictions."
            ),
        }


# ======================================================================
# CLI entry-point -- demo simulation for Chennai
# ======================================================================
if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))

    features_path = ROOT / "data" / "processed" / "features.parquet"
    sim = WhatIfSimulator(features_path=features_path)

    print("\n=== Adjustable Indicators ===")
    for ind in sim.get_adjustable_indicators():
        print(
            f"  {ind['name']:35s}  "
            f"range=[{ind['current_min']:.2f}, {ind['current_max']:.2f}]  "
            f"median={ind['median']:.2f}"
        )

    district = "Chennai"
    print(f"\n=== Baseline for {district} ===")
    baseline = sim.get_district_baseline(district)
    for k, v in baseline.items():
        print(f"  {k:35s}  {v}")

    # Example adjustments: reduce dropout rate and improve infra
    adjustments = {
        "dropout_rate": baseline.get("dropout_rate", 5.0) * 0.7,   # 30% reduction
        "school_infra_score": min(
            baseline.get("school_infra_score", 70) * 1.2, 100.0
        ),  # 20% improvement
    }

    print(f"\n=== What-If Scenario ===")
    print(f"  Adjustments: {adjustments}")
    result = sim.simulate(district, adjustments)

    print(f"\n--- Adjustments Applied ---")
    for adj in result["adjustments_applied"]:
        print(f"  {adj}")

    print(f"\n--- Score Changes ---")
    for key in ["edu_risk", "health_risk", "emp_risk", "infra_risk",
                "overall_score", "risk_band"]:
        b = result["baseline"].get(key, "N/A")
        s = result["scenario"].get(key, "N/A")
        d = result["delta"].get(key, "")
        d_str = f"  (delta: {d:+.2f})" if isinstance(d, (int, float)) else ""
        print(f"  {key:25s}  {b!s:>10s}  ->  {s!s:>10s}{d_str}")

    print(f"\n  NOTE: {result['note']}")
