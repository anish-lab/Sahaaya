"""
SAHAAYA — What-If Scenario Simulator.

Lets users adjust indicator values for a selected district and see
how the composite risk scores change.  Uses the WhatIfSimulator from
src.models.simulate if available; otherwise falls back to a simple
re-computation of the weighted mean.
"""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Simulator", page_icon="\U0001f9ea", layout="wide")

from utils import (  # noqa: E402
    load_features,
    is_mock_data,
    SUB_COLS,
    BAND_COLORS,
    BAND_ORDER,
)

# ---------------------------------------------------------------------------
st.title("What-If Scenario Simulator")
st.caption(
    "Adjust indicator values for a district and explore how composite "
    "risk scores might change."
)

st.info(
    "\U0001f4a1 **Caveat:** These are hypothetical, model-based estimates. "
    "They are *not* causal predictions.  Use for exploratory analysis only."
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
features_df = load_features()

if features_df is None:
    st.error(
        "**features.parquet not found.**  "
        "Run the data pipeline first to generate the processed data."
    )
    st.stop()

if is_mock_data(features_df):
    st.warning("\u26a0\ufe0f  Mock / synthetic data detected.  Results are illustrative only.")

# ---------------------------------------------------------------------------
# Pick latest period
# ---------------------------------------------------------------------------
time_col = "period" if "period" in features_df.columns else ("year" if "year" in features_df.columns else None)
if time_col and features_df[time_col].nunique() > 1:
    latest_period = features_df[time_col].dropna().max()
    view = features_df[features_df[time_col] == latest_period].copy()
else:
    view = features_df.copy()

# ---------------------------------------------------------------------------
# District selector
# ---------------------------------------------------------------------------
districts = sorted(view["district_name"].dropna().unique())
if not districts:
    st.error("No districts found in the data.")
    st.stop()

district = st.sidebar.selectbox("Select district", districts)
row = view[view["district_name"] == district]

if row.empty:
    st.error(f"No data for **{district}**.")
    st.stop()

baseline = row.iloc[0]

# ---------------------------------------------------------------------------
# Identify adjustable indicator columns
# ---------------------------------------------------------------------------
standard_cols = {
    "district_id", "district_name", "state", "period", "year",
    "edu_risk", "health_risk", "emp_risk", "infra_risk",
    "overall_score", "risk_band", "data_completeness",
    "cluster", "anomaly_flag", "anomaly_score", "pred_next_score",
}
indicator_cols = [
    c for c in view.columns
    if c not in standard_cols and pd.api.types.is_numeric_dtype(view[c])
]

if not indicator_cols:
    st.warning(
        "No adjustable source indicators found in the data.  "
        "The simulator requires real source columns (beyond the "
        "standard risk scores) to run scenarios."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Baseline display
# ---------------------------------------------------------------------------
st.subheader(f"Baseline — {district}")

bcols = st.columns(5)


def _fmt(val, decimals=1):
    if pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}f}"


bcols[0].metric("Overall", _fmt(baseline.get("overall_score")))
bcols[1].metric("Education", _fmt(baseline.get("edu_risk")))
bcols[2].metric("Health", _fmt(baseline.get("health_risk")))
bcols[3].metric("Employment", _fmt(baseline.get("emp_risk")))
bcols[4].metric("Infrastructure", _fmt(baseline.get("infra_risk")))

st.divider()

# ---------------------------------------------------------------------------
# Sliders for each adjustable indicator
# ---------------------------------------------------------------------------
st.subheader("Adjust indicators")
st.caption("Move the sliders to set hypothetical values for each indicator.")

scenario_values = {}
n_per_row = 3
for i in range(0, len(indicator_cols), n_per_row):
    cols = st.columns(n_per_row)
    for j, col_name in enumerate(indicator_cols[i : i + n_per_row]):
        current = baseline.get(col_name)
        col_data = view[col_name].dropna()
        if col_data.empty or pd.isna(current):
            continue
        lo = float(col_data.min())
        hi = float(col_data.max())
        # Ensure range makes sense
        if lo == hi:
            hi = lo + 1.0
        cur = float(current)
        cur = max(lo, min(hi, cur))  # clamp to range
        with cols[j % n_per_row]:
            scenario_values[col_name] = st.slider(
                col_name,
                min_value=round(lo, 2),
                max_value=round(hi, 2),
                value=round(cur, 2),
                step=round((hi - lo) / 100, 4) or 0.01,
            )

st.divider()

# ---------------------------------------------------------------------------
# Simulate button
# ---------------------------------------------------------------------------
if st.button("Simulate", type="primary"):
    # Try the real WhatIfSimulator first
    simulator = None
    try:
        from src.models.simulate import WhatIfSimulator
        simulator = WhatIfSimulator()
    except ImportError:
        simulator = None
    except Exception:
        simulator = None

    scenario_result = None

    if simulator is not None:
        try:
            scenario_result = simulator.simulate(district, scenario_values)
        except Exception as exc:
            st.warning(f"WhatIfSimulator failed: {exc}. Falling back to simple re-computation.")
            simulator = None

    # Fallback: simple recalculation (mean of available dimension scores)
    if scenario_result is None:
        # Build a modified row and re-derive scores using the same simple mean
        modified = baseline.copy()
        for k, v in scenario_values.items():
            modified[k] = v

        # If we cannot re-derive dimension scores from indicators without the
        # pipeline's feature-engineering logic, we show the raw indicator changes
        # and note that dimension scores cannot be re-derived.
        dim_cols = [c for c in SUB_COLS.values() if c in modified.index and pd.notna(modified[c])]

        # We can at least show indicator-level deltas
        scenario_result = {
            "edu_risk": modified.get("edu_risk"),
            "health_risk": modified.get("health_risk"),
            "emp_risk": modified.get("emp_risk"),
            "infra_risk": modified.get("infra_risk"),
            "overall_score": modified[dim_cols].mean() if dim_cols else None,
        }

        st.caption(
            "Using simplified fallback: dimension scores unchanged "
            "(full re-derivation requires the pipeline's WhatIfSimulator module)."
        )

    # ----- Display results -----
    st.subheader("Scenario comparison")

    def _risk_band(score):
        if pd.isna(score):
            return "N/A"
        if score < 35:
            return "Low"
        if score < 50:
            return "Moderate"
        if score < 65:
            return "High"
        return "Critical"

    comparison_items = [
        ("Overall", "overall_score"),
        ("Education", "edu_risk"),
        ("Health", "health_risk"),
        ("Employment", "emp_risk"),
        ("Infrastructure", "infra_risk"),
    ]

    cols_left, cols_right = st.columns(2)

    with cols_left:
        st.markdown("#### Baseline")
        for label, key in comparison_items:
            val = baseline.get(key)
            st.metric(label, _fmt(val))

        band_base = baseline.get("risk_band", _risk_band(baseline.get("overall_score")))
        bcolor = BAND_COLORS.get(str(band_base), "#888")
        st.markdown(
            f'Risk band: <span style="background:{bcolor};color:#fff;'
            f'padding:3px 10px;border-radius:6px">{band_base}</span>',
            unsafe_allow_html=True,
        )

    with cols_right:
        st.markdown("#### Scenario")
        for label, key in comparison_items:
            base_val = baseline.get(key)
            scen_val = scenario_result.get(key) if isinstance(scenario_result, dict) else None
            if pd.notna(scen_val) and pd.notna(base_val):
                delta = scen_val - base_val
                delta_str = f"{delta:+.1f}"
                delta_color = "inverse"  # green = negative (improvement)
            else:
                delta_str = None
                delta_color = "off"
            st.metric(
                label,
                _fmt(scen_val),
                delta=delta_str,
                delta_color=delta_color,
            )

        scen_overall = scenario_result.get("overall_score") if isinstance(scenario_result, dict) else None
        band_scen = _risk_band(scen_overall)
        scolor = BAND_COLORS.get(band_scen, "#888")
        st.markdown(
            f'Risk band: <span style="background:{scolor};color:#fff;'
            f'padding:3px 10px;border-radius:6px">{band_scen}</span>',
            unsafe_allow_html=True,
        )

    # --- Indicator deltas ---
    st.divider()
    st.subheader("Indicator changes")
    delta_rows = []
    for col_name in indicator_cols:
        base_v = baseline.get(col_name)
        scen_v = scenario_values.get(col_name)
        if pd.notna(base_v) and scen_v is not None:
            diff = scen_v - base_v
            delta_rows.append(
                {
                    "Indicator": col_name,
                    "Baseline": round(base_v, 2),
                    "Scenario": round(scen_v, 2),
                    "Delta": round(diff, 2),
                }
            )
    if delta_rows:
        delta_df = pd.DataFrame(delta_rows)
        # Color-code: only show rows that actually changed
        changed = delta_df[delta_df["Delta"].abs() > 0.001]
        if not changed.empty:
            st.dataframe(
                changed.style.applymap(
                    lambda v: "color: #2ecc71" if isinstance(v, (int, float)) and v < 0
                    else ("color: #e74c3c" if isinstance(v, (int, float)) and v > 0 else ""),
                    subset=["Delta"],
                ),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No indicators were changed from their baseline values.")
