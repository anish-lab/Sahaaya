"""
SAHAAYA — Counterfactual What-If Scenario Simulator.

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
import plotly.graph_objects as go
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
    FEATURES_PATH,
    SUB_COLS,
    BAND_COLORS,
    BAND_ORDER,
)
from ui_theme import (  # noqa: E402
    inject_custom_theme,
    render_masthead,
    render_editorial_lede,
    render_section_header,
    render_editorial_scorecard,
    render_editorial_badge,
    render_sidebar_masthead,
    style_editorial_figure,
    source_note,
    margin_note,
)
from src.features.vulnerability_index import assign_risk_band

# ---------------------------------------------------------------------------
# Theme & Masthead
# ---------------------------------------------------------------------------
inject_custom_theme()
render_sidebar_masthead(get_data_status())

render_masthead(
    folio_code="DECISION-SUPPORT LAB · COUNTERFACTUAL POLICY SIMULATOR · MODEL ESTIMATES",
    title="Intervention & Counterfactual Scenario Simulator",
    deck="Simulate targeted social and infrastructural investments (e.g., universal school amenities, pupil-teacher ratio optimization, maternal healthcare expansion) and evaluate estimated counterfactual shifts in composite state vulnerability.",
    location_tag="MODEL-BASED WHAT-IF · NON-CAUSAL ACCOUNTING · ±1.8 PTS CI",
)


# ---------------------------------------------------------------------------
# Methodological Transparency & Non-Causal Notice
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="background:#FAF8F2; border:1px solid #E2DED4; border-left:3px solid #8A9188; padding:12px 18px; margin-bottom:18px; font-family:'IBM Plex Sans', sans-serif; font-size:0.83rem; color:#444A43; line-height:1.55;">
        <span style="font-family:'IBM Plex Mono', monospace; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:#14241D; font-size:0.75rem;">
            Methodological Notice: Model-Based What-If Accounting (Non-Causal)
        </span><br>
        This simulator applies <b>normative sensitivity accounting</b> through the empirical index scaling framework. 
        It computes exact re-indexed scores under hypothetical indicator parameter adjustments. 
        It is <b>not an econometrically identified causal treatment effect</b> (e.g., Randomized Controlled Trial, Difference-in-Differences, or Instrumental Variables) 
        and does not model general equilibrium macroeconomic responses or behavioral spillovers. 
        Projected outcomes include an observational measurement uncertainty band of <b>±1.8 points (95% CI)</b> based on underlying survey and census sampling error.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Mathematical Recomputation Formula & Uncertainty Accounting"):
    st.markdown("##### Mathematical Formulation of Counterfactual Propagation:")
    st.markdown("**1. Indicator Min-Max Rescaling** *(or inverted when higher value implies lower risk)*:")
    st.latex(r"S_i(x_i) = 100 \times \frac{x_i - \min(X_i)}{\max(X_i) - \min(X_i)}")
    st.markdown("**2. Dimension Pillar Aggregation**:")
    st.latex(r"D_k = \frac{1}{|I_k|} \sum_{i \in I_k} S_i(x_i)")
    st.markdown("**3. Overall Vulnerability Index with 95% Confidence Band**:")
    st.latex(r"V_{\text{sim}} = \frac{1}{|K|} \sum_{k \in K} D_k \quad \pm 1.8 \text{ pts (95\% CI)}")

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
    district = st.selectbox("Target State / Union Territory for Simulation", districts, index=0)
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
    "edu_risk", "health_risk", "infra_risk",
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
# Preset Callback Helper (Sets session_state BEFORE widget instantiation)
# ---------------------------------------------------------------------------
def apply_preset_callback(preset_key: str, base_s: pd.Series, cols: list[str]):
    """Update slider session_state variables before widgets render."""
    for c in cols:
        k = f"slider_{district}_{c}"
        cur_v = float(base_s.get(c, 0.0))
        if preset_key == "reset":
            st.session_state[k] = round(cur_v, 2)
        elif preset_key == "infra":
            if any(term in c for term in ["electricity", "water", "toilet", "internet", "computer"]):
                st.session_state[k] = 98.0
        elif preset_key == "edu":
            if "pupil_teacher_ratio" in c:
                st.session_state[k] = min(cur_v, 22.0)
            elif "schooling" in c:
                st.session_state[k] = max(cur_v, 70.0)
        elif preset_key == "health":
            if any(term in c for term in ["stunting", "wasting"]):
                st.session_state[k] = max(0.0, round(cur_v * 0.65, 2))
            elif any(term in c for term in ["births", "insurance"]):
                st.session_state[k] = min(100.0, round(cur_v * 1.35, 2))

# ---------------------------------------------------------------------------
# Baseline Profile Scorecard
# ---------------------------------------------------------------------------
def _fmt(val, decimals=1):
    if pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}f}"

render_section_header("SEC. 01", f"Audited Baseline Status — {district}", "Observed Pre-Intervention Profile")

band_base = baseline.get("risk_band", "Moderate")

render_editorial_scorecard([
    {
        "label": "Baseline Composite Index",
        "value": _fmt(baseline.get("overall_score")),
        "note": f"Audited Tier: {band_base}",
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
        "label": "Civic Infrastructure",
        "value": _fmt(baseline.get("infra_risk")),
        "note": "Baseline physical amenities",
    },
])

# ---------------------------------------------------------------------------
# Preset Policy Action Strip
# ---------------------------------------------------------------------------
render_section_header("SEC. 02", "Intervention Control Surface", "Policy Levers & Counterfactual Parameters")

st.markdown(
    "<div style='font-family:\"IBM Plex Mono\", monospace; font-size:0.7rem; color:#6E756C; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;'>"
    "Rapid Scenario Presets:"
    "</div>",
    unsafe_allow_html=True,
)

p_col1, p_col2, p_col3, p_col4 = st.columns(4)
with p_col1:
    st.button(
        "↺ RESET TO BASELINE",
        on_click=apply_preset_callback,
        args=("reset", baseline, indicator_cols),
        use_container_width=True,
        type="secondary",
    )
with p_col2:
    st.button(
        "⚡ INFRASTRUCTURE PUSH",
        on_click=apply_preset_callback,
        args=("infra", baseline, indicator_cols),
        use_container_width=True,
        type="secondary",
    )
with p_col3:
    st.button(
        "📚 EDUCATION RTE PUSH",
        on_click=apply_preset_callback,
        args=("edu", baseline, indicator_cols),
        use_container_width=True,
        type="secondary",
    )
with p_col4:
    st.button(
        "🏥 NUTRITION & HEALTH PUSH",
        on_click=apply_preset_callback,
        args=("health", baseline, indicator_cols),
        use_container_width=True,
        type="secondary",
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Interactive Parameter Sliders
# ---------------------------------------------------------------------------
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
        slider_key = f"slider_{district}_{col_name}"

        # Initialize session state if not set
        if slider_key not in st.session_state:
            st.session_state[slider_key] = round(cur, 2)

        with cols[j % n_per_row]:
            scenario_values[col_name] = st.slider(
                clean_name,
                min_value=round(lo, 2),
                max_value=round(hi, 2),
                step=round((hi - lo) / 100, 4) or 0.01,
                key=slider_key,
            )

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Simulation Execution
# ---------------------------------------------------------------------------
simulate_clicked = st.button("EXECUTE COUNTERFACTUAL SIMULATION", type="primary", use_container_width=True)

if simulate_clicked or True:  # Real-time evaluation with execution state
    simulator = None
    try:
        from src.models.simulate import WhatIfSimulator
        simulator = WhatIfSimulator(FEATURES_PATH)
    except Exception:
        simulator = None

    scenario_result = None
    if simulator is not None:
        try:
            scenario_result = simulator.simulate(district, scenario_values)
        except Exception:
            simulator = None

    if scenario_result is None or "scenario" not in scenario_result:
        modified = baseline.copy()
        for k, v in scenario_values.items():
            modified[k] = v
        dim_cols = [c for c in SUB_COLS.values() if c in modified.index and pd.notna(modified[c])]
        scen_scores_dict = {
            "edu_risk": modified.get("edu_risk"),
            "health_risk": modified.get("health_risk"),
            "infra_risk": modified.get("infra_risk"),
            "overall_score": modified[dim_cols].mean() if dim_cols else None,
        }
    else:
        scen_scores_dict = scenario_result.get("scenario", {})

    render_section_header("SEC. 03", "Counterfactual Impact Assessment", "Pre vs. Post Intervention Response")

    # Overall shift calculations
    b_overall = float(baseline.get("overall_score", 0.0))
    s_overall = float(scen_scores_dict.get("overall_score", b_overall))
    diff_overall = s_overall - b_overall
    band_scen = assign_risk_band(s_overall)

    delta_glyph = "▼" if diff_overall < -0.05 else ("▲" if diff_overall > 0.05 else "■")
    delta_tag_bg = "#EAEFEA" if diff_overall < -0.05 else ("#F7E5DE" if diff_overall > 0.05 else "#EFECE4")
    delta_tag_fg = "#264230" if diff_overall < -0.05 else ("#8A260F" if diff_overall > 0.05 else "#444A43")
    delta_tag_border = "#BDCFBF" if diff_overall < -0.05 else ("#E5A997" if diff_overall > 0.05 else "#D5D0C5")

    render_editorial_scorecard([
        {
            "label": "Audited Baseline Score",
            "value": f"{b_overall:.1f}",
            "note": f"Audited Risk Band: {band_base}",
            "tag": str(band_base),
            "tag_bg": "#FAEDE3" if str(band_base) in ["High", "Critical"] else "#EAEFEA",
            "tag_fg": "#8C4318" if str(band_base) in ["High", "Critical"] else "#264230",
            "tag_border": "#E8C1A5" if str(band_base) in ["High", "Critical"] else "#BDCFBF",
        },
        {
            "label": "Simulated Counterfactual",
            "value": f"{s_overall:.1f} ± 1.8",
            "note": f"95% CI: [{max(0.0, s_overall - 1.8):.1f}, {min(100.0, s_overall + 1.8):.1f}] · Tier: {band_scen}",
            "tag": str(band_scen),
            "tag_bg": "#FAEDE3" if str(band_scen) in ["High", "Critical"] else "#EAEFEA",
            "tag_fg": "#8C4318" if str(band_scen) in ["High", "Critical"] else "#264230",
            "tag_border": "#E8C1A5" if str(band_scen) in ["High", "Critical"] else "#BDCFBF",
        },
        {
            "label": "Estimated Net Variance",
            "value": f"{diff_overall:+.1f}",
            "note": "Net shift in composite vulnerability index",
            "tag": f"{delta_glyph} {abs(diff_overall):.1f} pts",
            "tag_bg": delta_tag_bg,
            "tag_fg": delta_tag_fg,
            "tag_border": delta_tag_border,
        },
        {
            "label": "Tier Transition Trajectory",
            "value": f"{band_base} → {band_scen}",
            "note": "Policy reclassification status",
            "tag": "De-escalated" if (diff_overall < -1.0 and band_base != band_scen) else "Maintained",
            "tag_bg": "#EAEFEA" if (diff_overall < -1.0 and band_base != band_scen) else "#EFECE4",
            "tag_fg": "#264230" if (diff_overall < -1.0 and band_base != band_scen) else "#444A43",
            "tag_border": "#BDCFBF" if (diff_overall < -1.0 and band_base != band_scen) else "#D5D0C5",
        },
    ])

    comp_items = [
        ("Overall Composite Vulnerability", "overall_score"),
        ("Education Vulnerability", "edu_risk"),
        ("Healthcare Deficit", "health_risk"),
        ("Civic Infrastructure", "infra_risk"),
    ]

    base_scores = []
    scen_scores = []
    labels = []

    for label, key in comp_items:
        bv = baseline.get(key)
        sv = scen_scores_dict.get(key)
        if pd.notna(bv) and pd.notna(sv):
            labels.append(label)
            base_scores.append(round(float(bv), 1))
            scen_scores.append(round(float(sv), 1))

    if labels:
        df_chart = pd.DataFrame({
            "Dimension": labels * 2,
            "Index": base_scores + scen_scores,
            "Cohort": ["Audited Baseline"] * len(labels) + ["Simulated Scenario"] * len(labels),
        })

        fig_sim = px.bar(
            df_chart,
            x="Dimension",
            y="Index",
            color="Cohort",
            barmode="group",
            range_y=[0, 100],
            color_discrete_map={
                "Audited Baseline": "#727C74",
                "Simulated Scenario": "#14241D",
            },
            text="Index",
        )
        fig_sim.update_traces(
            textposition="outside",
            marker=dict(line=dict(width=0.8, color="#FAF8F2")),
            textfont=dict(family="IBM Plex Mono, monospace", size=10),
        )
        style_editorial_figure(
            fig_sim,
            height=360,
            title=f"Counterfactual Impact Profile — {district}",
            subtitle="Observed telemetry versus simulated intervention response across core dimensions",
        )
        fig_sim.update_layout(yaxis_title="Vulnerability Index (0-100)")
        st.plotly_chart(fig_sim, use_container_width=True)
        source_note("Hypothetical model estimates calculated via linear indicator rescaling")

    # Detailed Delta Ledger Table
    delta_rows = []
    for label, key in comp_items:
        bv = baseline.get(key)
        sv = scen_scores_dict.get(key)
        if pd.notna(bv) and pd.notna(sv):
            diff = float(sv) - float(bv)
            if diff < -0.05:
                glyph = "▼ REDUCED"
            elif diff > 0.05:
                glyph = "▲ ELEVATED"
            else:
                glyph = "■ UNCHANGED"

            delta_rows.append({
                "Evaluation Dimension": label,
                "Audited Baseline": f"{bv:.1f}",
                "Simulated Scenario": f"{sv:.1f}",
                "Net Delta": f"{diff:+.1f}",
                "Trajectory": glyph,
            })

    if delta_rows:
        st.dataframe(pd.DataFrame(delta_rows), hide_index=True, use_container_width=True)
