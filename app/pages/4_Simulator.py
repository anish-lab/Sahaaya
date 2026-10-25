"""
SAHAAYA — What-If Scenario Simulator.

Civic Intelligence, Editorial Precision aesthetic:
Warm ivory surfaces, deep forest-green accents, Newsreader serif typography,
and restrained burnt-orange highlights.
"""
from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
ROOT = APP_DIR.parent
for p in [str(APP_DIR), str(ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Scenario Simulator — SAHAAYA",
    page_icon="§",
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
    render_masthead,
    render_section_header,
    render_editorial_scorecard,
    render_editorial_badge,
    render_sidebar_masthead,
    style_editorial_figure,
)

# ---------------------------------------------------------------------------
# Theme & Masthead
# ---------------------------------------------------------------------------
inject_custom_theme()
render_sidebar_masthead(get_data_status())

render_masthead(
    folio_code="POLICY EXPERIMENTATION LAB · COUNTERFACTUAL MODEL",
    title="Intervention & What-If Scenario Simulator",
    deck="Simulate targeted social and infrastructural investments (e.g., expanding school amenities, boosting maternal healthcare, strengthening rural wage guarantees) and evaluate estimated counterfactual shifts in composite district vulnerability.",
    location_tag="DECISION-SUPPORT LAB · COUNTERFACTUAL INFERENCE",
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
features_df = load_features()

if features_df is None:
    st.error("Telemetry store `features.parquet` not located. Please execute the ingestion pipeline.")
    st.stop()

if is_mock_data(features_df):
    st.warning("Notice: Synthetic test dataset active. Figures reflect simulated distributions.")

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
    st.error("No districts located in active dataset.")
    st.stop()

col_s1, col_s2 = st.columns([2.5, 1])
with col_s1:
    district = st.selectbox("Target Jurisdiction for Simulation", districts, index=0)
with col_s2:
    period_str = str(view[time_col].iloc[0]) if time_col and not view.empty else "Current Administrative Audit"
    st.selectbox("Base Reporting Period", [period_str], disabled=True)

row = view[view["district_name"] == district]
if row.empty:
    st.error(f"No records found for '{district}'.")
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
    st.warning("No adjustable source indicators found in active dataset.")
    st.stop()

# ---------------------------------------------------------------------------
# Baseline Profile Scorecard
# ---------------------------------------------------------------------------
def _fmt(val, decimals=1):
    if pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}f}"

render_section_header("SEC. 01", f"Baseline Scorecard — {district}", "Pre-Intervention Status")

band_base = baseline.get("risk_band", "Moderate")

render_editorial_scorecard([
    {
        "label": "Baseline Composite Index",
        "value": _fmt(baseline.get("overall_score")),
        "note": "Combined pre-intervention risk",
        "tag": str(band_base),
        "tag_bg": "#FAEDE3" if str(band_base) in ["High", "Critical"] else "#EAEFEA",
        "tag_fg": "#8C4318" if str(band_base) in ["High", "Critical"] else "#264230",
        "tag_border": "#E8C1A5" if str(band_base) in ["High", "Critical"] else "#BDCFBF",
    },
    {
        "label": "Education Vulnerability",
        "value": _fmt(baseline.get("edu_risk")),
        "note": "Baseline schooling stress",
    },
    {
        "label": "Healthcare Deficit",
        "value": _fmt(baseline.get("health_risk")),
        "note": "Baseline nutritional stress",
    },
    {
        "label": "Employment Deficit",
        "value": _fmt(baseline.get("emp_risk")),
        "note": "Baseline rural wage stress",
    },
    {
        "label": "Infra Deficit",
        "value": _fmt(baseline.get("infra_risk")),
        "note": "Baseline civic infrastructure",
    },
])

# ---------------------------------------------------------------------------
# Interactive Intervention Sliders
# ---------------------------------------------------------------------------
render_section_header("SEC. 02", "Intervention Control Surface", "Counterfactual Parameter Sliders")

st.markdown(
    """
    <div style="background:#FFFFFF; border:1px solid #E2DED4; border-top:2px solid #14241D; padding:18px 20px; margin-bottom:18px;">
        <div style="font-family:'Newsreader',serif; font-size:1.15rem; color:#14241D; margin-bottom:4px;">
            Simulated Feature Parameters
        </div>
        <div style="font-family:'IBM Plex Sans'; font-size:0.82rem; color:#6E756C; margin-bottom:16px;">
            Adjust the sliders below to model hypothetical state intervention envelopes and capital allocations.
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
# Simulation Execution
# ---------------------------------------------------------------------------
simulate_clicked = st.button("EXECUTE COUNTERFACTUAL SIMULATION", type="primary", use_container_width=True)

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

    render_section_header("SEC. 03", "Counterfactual Impact Assessment", "Pre vs. Post Intervention")

    comp_items = [
        ("Overall Composite Vulnerability", "overall_score"),
        ("Education Vulnerability", "edu_risk"),
        ("Healthcare Deficit", "health_risk"),
        ("Employment Deficit", "emp_risk"),
        ("Civic Infrastructure", "infra_risk"),
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
            "Index": base_scores + scen_scores,
            "State": ["Baseline (Audited)"] * len(labels) + ["Post-Intervention (Simulated)"] * len(labels),
        })

        fig_sim = px.bar(
            df_chart,
            x="Dimension",
            y="Index",
            color="State",
            barmode="group",
            range_y=[0, 100],
            color_discrete_map={
                "Baseline (Audited)": "#5A665E",             # Muted sage/slate
                "Post-Intervention (Simulated)": "#14241D",   # Deep forest green
            },
            text="Index",
        )
        fig_sim.update_traces(
            textposition="outside",
            marker=dict(line=dict(width=0.8, color="#14241D")),
            textfont=dict(family="IBM Plex Mono", size=10),
        )
        style_editorial_figure(
            fig_sim,
            height=360,
            title=f"Counterfactual Impact Comparison — {district}",
            subtitle="Observed telemetry versus simulated intervention response",
        )
        st.plotly_chart(fig_sim, use_container_width=True)

    # Detailed Delta Ledger Table
    delta_rows = []
    for label, key in comp_items:
        bv = baseline.get(key)
        sv = scenario_result.get(key) if isinstance(scenario_result, dict) else None
        if pd.notna(bv) and pd.notna(sv):
            diff = float(sv) - float(bv)
            if diff < -0.1:
                status = "REDUCED / AMELIORATED"
            elif diff > 0.1:
                status = "ELEVATED RISK"
            else:
                status = "PARITY / UNCHANGED"

            delta_rows.append({
                "Evaluation Dimension": label,
                "Audited Baseline": f"{bv:.1f}",
                "Simulated Value": f"{sv:.1f}",
                "Variance (Delta)": f"{diff:+.1f}",
                "Trajectory": status,
            })

    if delta_rows:
        st.dataframe(pd.DataFrame(delta_rows), hide_index=True, use_container_width=True)
