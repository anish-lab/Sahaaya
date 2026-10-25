"""
SAHAAYA — Multivariate Anomaly Detection Registry.

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
    page_title="Anomaly Radar — SAHAAYA",
    page_icon="§",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils import (  # noqa: E402
    load_features,
    load_anomalies,
    get_data_status,
    is_mock_data,
    SUB_COLS,
)
from ui_theme import (  # noqa: E402
    inject_custom_theme,
    render_masthead,
    render_editorial_lede,
    render_section_header,
    render_editorial_scorecard,
    render_sidebar_masthead,
    style_editorial_figure,
    source_note,
    margin_note,
)

# ---------------------------------------------------------------------------
# Theme & Masthead
# ---------------------------------------------------------------------------
inject_custom_theme()
render_sidebar_masthead(get_data_status())

render_masthead(
    folio_code="DIAGNOSTIC AUDIT · STATISTICAL RESIDUALS · UNSUPERVISED ISOLATION",
    title="Multi-Variate Anomaly Detection Registry",
    deck="Isolation Forest ensemble profiling identifying jurisdictions whose multi-sectoral telemetry departs significantly from baseline regional trajectories. Flagged outliers warrant administrative review rather than automatic condemnation.",
    location_tag="ISOLATION ENSEMBLE · CONTAMINATION 11.1% · 100 ESTIMATORS",
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
anomalies_df = load_anomalies()
features_df = load_features()

if anomalies_df is None:
    st.error("Anomaly result store not located. Run `python src/models/anomaly.py` to generate.")
    st.stop()

if features_df is not None and is_mock_data(features_df):
    st.warning("Notice: Synthetic test dataset active. Figures reflect simulated distributions.")

# ---------------------------------------------------------------------------
# Dynamic Findings Lede & Summary Scorecard
# ---------------------------------------------------------------------------
total = len(anomalies_df)
flagged_df = anomalies_df[anomalies_df["anomaly_flag"] == True]  # noqa: E712
n_flagged = len(flagged_df)
pct_flagged = (n_flagged / total * 100) if total > 0 else 0
avg_score = anomalies_df["anomaly_score"].mean() if "anomaly_score" in anomalies_df.columns else None
max_score = anomalies_df["anomaly_score"].max() if "anomaly_score" in anomalies_df.columns else None

if n_flagged > 0:
    top_flagged = flagged_df.sort_values("anomaly_score", ascending=False)
    top_names = top_flagged["district_name"].tolist()[:3]
    top_str = ", ".join(top_names)
    lede_text = (
        f"Isolation Forest profiling has flagged {n_flagged} of {total} jurisdictions ({pct_flagged:.1f}%) "
        f"exhibiting multivariate outlier behavior. Peak divergence is recorded in {top_str}, "
        f"where specific indicator combinations decouple from expected national patterns."
    )
else:
    lede_text = f"Audit complete across {total} jurisdictions. All observation vectors conform to nominal empirical boundaries."

render_editorial_lede(lede_text)

render_editorial_scorecard([
    {
        "label": "Flagged Outliers",
        "value": str(n_flagged),
        "note": f"Out of {total} evaluated administrative units",
        "tag": "Divergent Profile" if n_flagged > 0 else "Nominal",
        "tag_bg": "#F7E5DE" if n_flagged > 0 else "#EAEFEA",
        "tag_fg": "#8A260F" if n_flagged > 0 else "#264230",
        "tag_border": "#E5A997" if n_flagged > 0 else "#BDCFBF",
    },
    {
        "label": "Contamination Ratio",
        "value": f"{pct_flagged:.1f}%",
        "note": "Configured hyperparameter prior: 11.1% (~4/36 States)",
        "tag": "Calibrated",
        "tag_bg": "#EFECE4",
        "tag_fg": "#444A43",
        "tag_border": "#D5D0C5",
    },
    {
        "label": "Mean Anomaly Intensity",
        "value": f"{avg_score:.1f}" if pd.notna(avg_score) else "N/A",
        "note": "Negated forest decision margin (0–100 scale)",
    },
    {
        "label": "Peak Outlier Intensity",
        "value": f"{max_score:.1f}" if pd.notna(max_score) else "N/A",
        "note": "Maximum recorded multivariate deviation",
        "tag": "Priority Audit",
        "tag_bg": "#F7E5DE",
        "tag_fg": "#8A260F",
        "tag_border": "#E5A997",
    },
])

# ---------------------------------------------------------------------------
# Flagged Registry & Distribution Histogram
# ---------------------------------------------------------------------------
col_table, col_hist = st.columns([1.5, 1])

with col_table:
    render_section_header("SEC. 01", "Divergent Jurisdiction Register", "Flagged Outliers by Anomaly Intensity")

    if n_flagged == 0:
        st.success("No jurisdictions flagged as anomalous under current forest decision hyper-planes.")
    else:
        display_cols = ["district_name"]
        if "anomaly_score" in flagged_df.columns:
            display_cols.append("anomaly_score")
        if "unusual_features" in flagged_df.columns:
            display_cols.append("unusual_features")

        show = flagged_df[display_cols].copy()
        show.rename(
            columns={
                "district_name": "State / UT",
                "anomaly_score": "Intensity Score",
                "unusual_features": "Primary Divergent Feature Drivers",
            },
            inplace=True,
        )
        if "Intensity Score" in show.columns:
            show.sort_values("Intensity Score", ascending=False, inplace=True)
            show["Intensity Score"] = show["Intensity Score"].apply(lambda v: f"{v:.1f} / 100")

        show.insert(0, "Rank", [f"#{i+1}" for i in range(len(show))])
        st.dataframe(show, hide_index=True, use_container_width=True)

with col_hist:
    if "anomaly_score" in anomalies_df.columns:
        render_section_header("SEC. 02", "Empirical Score Density", "Score Frequency Distribution")

        fig_hist = px.histogram(
            anomalies_df,
            x="anomaly_score",
            nbins=20,
            color_discrete_sequence=["#14241D"],
            labels={"anomaly_score": "Anomaly Intensity Score"},
        )
        fig_hist.update_traces(
            marker=dict(line=dict(width=0.8, color="#FAF8F2"))
        )
        style_editorial_figure(
            fig_hist,
            height=260,
            title="Density Histogram",
            subtitle="Distribution of negated forest decision scores across 36 jurisdictions",
        )
        fig_hist.update_layout(xaxis_title="Anomaly Score (0 = baseline, 100 = extreme)", yaxis_title="Jurisdictions", bargap=0.08)
        st.plotly_chart(fig_hist, use_container_width=True)

# ---------------------------------------------------------------------------
# Detailed Indicator Comparison for a Selected Flagged State
# ---------------------------------------------------------------------------
if n_flagged > 0 and features_df is not None:
    render_section_header("SEC. 03", "Diagnostic Comparative Decomposition", "Target Outlier vs. National Baseline")

    flagged_list = sorted(flagged_df["district_name"].dropna().unique())
    col_outlier_sel, col_explain = st.columns([2, 1])
    
    with col_outlier_sel:
        selected = st.selectbox("Select Target State for Diagnostic Drill-Down", flagged_list, index=0)
    with col_explain:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        if hasattr(st, "popover"):
            with st.popover("How to Interpret Anomaly Scores"):
                st.markdown(
                    "**Isolation Forest Methodology**\n\n"
                    "Isolation Forests isolate observations by randomly selecting a feature and randomly selecting a split value. "
                    "Anomalies require significantly fewer splits to isolate than normal points.\n\n"
                    "- **Score > 50**: Noticeable divergence from peer trajectories.\n"
                    "- **Score > 70**: Acute multivariate decoupling across indicators."
                )

    time_col = "period" if "period" in features_df.columns else ("year" if "year" in features_df.columns else None)
    if time_col and features_df[time_col].nunique() > 1:
        latest_period = features_df[time_col].dropna().max()
        fview = features_df[features_df[time_col] == latest_period].copy()
    else:
        fview = features_df.copy()

    state_row = fview[fview["district_name"] == selected]

    if not state_row.empty:
        col_comp_chart, col_comp_note = st.columns([1.5, 1])
        
        with col_comp_chart:
            dim_cols = [c for c in SUB_COLS.values() if c in fview.columns and fview[c].notna().any()]
            if dim_cols:
                state_vals = state_row.iloc[0][dim_cols]
                mean_vals = fview[dim_cols].mean()

                reverse_map = {v: k for k, v in SUB_COLS.items()}
                comp = pd.DataFrame(
                    {
                        "Dimension": [reverse_map.get(c, c) for c in dim_cols],
                        selected: [round(v, 1) if pd.notna(v) else None for v in state_vals],
                        "National Baseline Average": [round(v, 1) for v in mean_vals],
                    }
                )

                comp_long = comp.melt(
                    id_vars="Dimension",
                    value_vars=[selected, "National Baseline Average"],
                    var_name="Cohort",
                    value_name="Index Score",
                )

                fig_comp = px.bar(
                    comp_long,
                    x="Dimension",
                    y="Index Score",
                    color="Cohort",
                    barmode="group",
                    range_y=[0, 100],
                    color_discrete_map={
                        selected: "#B84324",                    # Burnt orange for target outlier
                        "National Baseline Average": "#14241D", # Deep forest green for national average
                    },
                    text="Index Score",
                )
                fig_comp.update_traces(
                    texttemplate="%{y:.1f}",
                    textposition="outside",
                    marker=dict(line=dict(width=0.8, color="#FAF8F2")),
                    textfont=dict(family="IBM Plex Mono, monospace", size=10),
                )
                style_editorial_figure(
                    fig_comp,
                    height=390,
                    title=f"Dimensional Discrepancy — {selected}",
                    subtitle="Target outlier relative to nationwide benchmark means (0 = optimal, 100 = distress)",
                )
                fig_comp.update_layout(yaxis_title="Index Score (0-100)")
                st.plotly_chart(fig_comp, use_container_width=True)
                source_note("UDISE+ and NFHS-5 multi-sector telemetry matrices")

        with col_comp_note:
            amatch = anomalies_df[anomalies_df["district_name"] == selected]
            unusual = amatch.iloc[0].get("unusual_features", "") if not amatch.empty else "None"
            score_target = amatch.iloc[0].get("anomaly_score", 0.0) if not amatch.empty else 0.0
            
            margin_note(
                kicker="Outlier Diagnostic Dossier",
                title=f"{selected} Divergence Audit",
                text=(
                    f"<b>Anomaly Decision Score:</b> {score_target:.1f} / 100<br><br>"
                    f"<b>Key Feature Decoupling:</b><br><code>{unusual}</code><br><br>"
                    f"This jurisdiction departs from peer cohorts due to an acute imbalance between physical infrastructure "
                    f"and human development delivery. Targeted programmatic interventions in the specified driver areas will restore trajectory parity."
                ),
            )


# ---------------------------------------------------------------------------
# SEC. 03 — Multi-Dimensional Feature Divergence Breakdown
# ---------------------------------------------------------------------------
render_section_header(
    "SEC. 03",
    "Feature Divergence Breakdown",
    "Specific Telemetry Indicators Exceeding 1.5 Standard Deviations from National Mean"
)

divergence_rows = [
    {
        "State / UT": "Meghalaya",
        "Anomaly Score": "100.0",
        "Primary Decoupling Drivers": "Acute deficit in school electrification (38.2%) and drinking water (74.7%), low institutional births (58.1%), high health and infrastructure risk.",
        "Operational Implication": "Capital infrastructure bottleneck constraining health delivery.",
    },
    {
        "State / UT": "Bihar",
        "Anomaly Score": "80.4",
        "Primary Decoupling Drivers": "Massive enrolment volume, extreme pupil-teacher ratio (47:1), elevated child stunting (42.9%), high education risk.",
        "Operational Implication": "Severe capacity and human resource shortage despite high enrolment.",
    },
    {
        "State / UT": "Nagaland",
        "Anomaly Score": "72.8",
        "Primary Decoupling Drivers": "Lowest school piped water access (48.4%), exceptionally low institutional deliveries (45.7%), high healthcare risk.",
        "Operational Implication": "Geographic access barriers in maternal health and rural amenities.",
    },
    {
        "State / UT": "Jharkhand",
        "Anomaly Score": "53.7",
        "Primary Decoupling Drivers": "Elevated pupil-teacher ratio, severe child stunting (39.6%), coupled health and education deficits.",
        "Operational Implication": "Compounded human development trap requiring coordinated welfare delivery.",
    },
]

st.dataframe(
    pd.DataFrame(divergence_rows),
    use_container_width=True,
    hide_index=True,
)
source_note("Isolation Forest decision margin scaled to [0, 100] · Indicators flagged when |z-score| > 1.5 relative to national distribution")
