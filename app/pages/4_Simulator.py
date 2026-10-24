"""
SAHAAYA — What-If Scenario Simulator.

Lets users adjust indicator values for a selected district and see
how the composite risk scores change.  Uses the WhatIfSimulator from
src.models.simulate if available; otherwise falls back to a simple
re-computation of the weighted mean.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Scenario Simulator — SAHAAYA",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils import (  # noqa: E402
    load_features,
    get_data_status,
    is_mock_data,
    SUB_COLS,
    BAND_COLORS,
    BAND_ORDER,
)
from ui_theme import (  # noqa: E402
    inject_custom_theme,
    render_topbar,
    render_hero,
    render_kpi,
    render_risk_pill,
    render_sidebar_brand,
    style_plotly_fig,
)

# ---------------------------------------------------------------------------
# Theme & Top Navigation
# ---------------------------------------------------------------------------
inject_custom_theme()
render_topbar(current_page="Simulator")

render_hero(
    tag="WHAT-IF POLICY EXPERIMENTATION",
    title="Counterfactual Policy Simulator",
    description="Adjust underlying social and infrastructural indicators to model estimated impact on composite district vulnerability. Designed for budgetary planning and sensitivity analysis.",
)

render_sidebar_brand(get_data_status())

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
features_df = load_features()

if features_df is None:
    st.error("**features.parquet not found.** Run the data pipeline first.")
    st.stop()

if is_mock_data(features_df):
    st.warning("⚠️ Mock / synthetic data detected. Results are illustrative only.")

# ---------------------------------------------------------------------------
# District Selector in Main Ribbon
# ---------------------------------------------------------------------------
time_col = "period" if "period" in features_df.columns else ("year" if "year" in features_df.columns else None)
if time_col and features_df[time_col].nunique() > 1:
    latest_period = features_df[time_col].dropna().max()
    view = features_df[features_df[time_col] == latest_period].copy()
else:
    view = features_df.copy()

districts = sorted(view["district_name"].dropna().unique())
if not districts:
    st.error("No districts found in the data.")
    st.stop()

col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    district = st.selectbox("📍 Select District to Simulate", districts, index=0)
with col_s2:
    period_str = str(view[time_col].iloc[0]) if time_col and not view.empty else "Latest Available"
    st.selectbox("📅 Base Reporting Period", [period_str], disabled=True)

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
    st.warning("No adjustable source indicators found in dataset.")
    st.stop()

# ---------------------------------------------------------------------------
# Baseline Profile KPIs
# ---------------------------------------------------------------------------
def _fmt(val, decimals=1):
    if pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}f}"

st.markdown(
    f"<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.15rem; color:#0f172a; margin-bottom:10px;'>"
    f"📊 Current Baseline Telemetry — {district} "
    f"{render_risk_pill(baseline.get('risk_band', 'Moderate'))}"
    f"</div>",
    unsafe_allow_html=True,
)

b1, b2, b3, b4, b5 = st.columns(5)
with b1:
    render_kpi("Overall Score", _fmt(baseline.get("overall_score")), icon="🎯", color_accent="#4f46e5")
with b2:
    render_kpi("Education Risk", _fmt(baseline.get("edu_risk")), icon="🎓", color_accent="#06b6d4")
with b3:
    render_kpi("Health Risk", _fmt(baseline.get("health_risk")), icon="🏥", color_accent="#f59e0b")
with b4:
    render_kpi("Employment Risk", _fmt(baseline.get("emp_risk")), icon="💼", color_accent="#8b5cf6")
with b5:
    render_kpi("Infra Risk", _fmt(baseline.get("infra_risk")), icon="⚡", color_accent="#ec4899")

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Interactive Intervention Sliders
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px; padding:20px; box-shadow:0 4px 14px -3px rgba(15,23,42,0.04); margin-bottom:24px;">
        <div style="font-family:'Outfit',sans-serif; font-weight:700; font-size:1.15rem; color:#0f172a; margin-bottom:4px;">
            🎛️ Policy Intervention Controls
        </div>
        <div style="font-size:0.85rem; color:#64748b; margin-bottom:16px;">
            Adjust the sliders to model targeted policy interventions and infrastructural investments.
        </div>
    """,
    unsafe_allow_html=True,
)

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
        if lo == hi:
            hi = lo + 1.0
        cur = float(current)
        cur = max(lo, min(hi, cur))

        # Humanized name
        clean_name = col_name.replace("_", " ").title()

        with cols[j % n_per_row]:
            scenario_values[col_name] = st.slider(
                clean_name,
                min_value=round(lo, 2),
                max_value=round(hi, 2),
                value=round(cur, 2),
                step=round((hi - lo) / 100, 4) or 0.01,
            )

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Simulation Trigger & Results
# ---------------------------------------------------------------------------
simulate_clicked = st.button("🚀 Run Scenario Simulation", type="primary", use_container_width=True)

if simulate_clicked:
    simulator = None
    try:
        from src.models.simulate import WhatIfSimulator
        simulator = WhatIfSimulator()
    except Exception:
        simulator = None

    scenario_result = None
    if simulator is not None:
        try:
            scenario_result = simulator.simulate(district, scenario_values)
        except Exception:
            simulator = None

    if scenario_result is None:
        modified = baseline.copy()
        for k, v in scenario_values.items():
            modified[k] = v
        dim_cols = [c for c in SUB_COLS.values() if c in modified.index and pd.notna(modified[c])]
        scenario_result = {
            "edu_risk": modified.get("edu_risk"),
            "health_risk": modified.get("health_risk"),
            "emp_risk": modified.get("emp_risk"),
            "infra_risk": modified.get("infra_risk"),
            "overall_score": modified[dim_cols].mean() if dim_cols else None,
        }

    # Display Side-by-Side Comparison
    st.markdown(
        "<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.25rem; color:#0f172a; margin-top:20px; margin-bottom:12px;'>"
        "🔬 Counterfactual Impact Assessment"
        "</div>",
        unsafe_allow_html=True,
    )

    comp_items = [
        ("Overall Score", "overall_score"),
        ("Education Risk", "edu_risk"),
        ("Health Risk", "health_risk"),
        ("Employment Risk", "emp_risk"),
        ("Infrastructure Risk", "infra_risk"),
    ]

    base_scores = []
    scen_scores = []
    labels = []

    for label, key in comp_items:
        bv = baseline.get(key)
        sv = scenario_result.get(key) if isinstance(scenario_result, dict) else None
        if pd.notna(bv) and pd.notna(sv):
            labels.append(label)
            base_scores.append(round(float(bv), 1))
            scen_scores.append(round(float(sv), 1))

    if labels:
        df_chart = pd.DataFrame({
            "Dimension": labels * 2,
            "Score": base_scores + scen_scores,
            "Scenario": ["Baseline"] * len(labels) + ["Post-Intervention"] * len(labels),
        })

        fig_sim = px.bar(
            df_chart,
            x="Dimension",
            y="Score",
            color="Scenario",
            barmode="group",
            range_y=[0, 100],
            color_discrete_map={
                "Baseline": "#64748b",
                "Post-Intervention": "#4f46e5",
            },
            text="Score",
        )
        fig_sim.update_traces(textposition="outside")
        style_plotly_fig(fig_sim, height=380, title=f"Pre vs. Post Intervention Vulnerability: {district}")
        st.plotly_chart(fig_sim, use_container_width=True)

    # Delta Summary Table
    delta_rows = []
    for label, key in comp_items:
        bv = baseline.get(key)
        sv = scenario_result.get(key) if isinstance(scenario_result, dict) else None
        if pd.notna(bv) and pd.notna(sv):
            diff = float(sv) - float(bv)
            status = "✅ Improved" if diff < -0.1 else ("⚠️ Increased Risk" if diff > 0.1 else "Neutral")
            delta_rows.append({
                "Metric": label,
                "Baseline": f"{bv:.1f}",
                "Simulated": f"{sv:.1f}",
                "Delta": f"{diff:+.1f}",
                "Direction": status,
            })

    if delta_rows:
        st.dataframe(pd.DataFrame(delta_rows), hide_index=True, use_container_width=True)
