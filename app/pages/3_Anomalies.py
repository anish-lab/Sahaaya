"""
SAHAAYA — Anomaly Detection Results Page.

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
    render_section_header,
    render_editorial_scorecard,
    render_sidebar_masthead,
    style_editorial_figure,
)

# ---------------------------------------------------------------------------
# Theme & Masthead
# ---------------------------------------------------------------------------
inject_custom_theme()
render_sidebar_masthead(get_data_status())

render_masthead(
    folio_code="DIAGNOSTIC AUDIT · STATISTICAL RESIDUALS",
    title="Multi-Variate Anomaly Detection Registry",
    deck="Isolation Forest ensemble profiling identifying jurisdictions whose socio-economic telemetry deviates significantly (> 1.5 standard deviations) from baseline regional envelopes. Designed to trigger administrative inquiry, not definitive distress.",
    location_tag="ISOLATION FOREST AUDIT · 100 ESTIMATORS",
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
# Summary Scorecard
# ---------------------------------------------------------------------------
total = len(anomalies_df)
flagged_df = anomalies_df[anomalies_df["anomaly_flag"] == True]  # noqa: E712
n_flagged = len(flagged_df)
pct_flagged = (n_flagged / total * 100) if total > 0 else 0
avg_score = anomalies_df["anomaly_score"].mean() if "anomaly_score" in anomalies_df.columns else None
max_score = anomalies_df["anomaly_score"].max() if "anomaly_score" in anomalies_df.columns else None

render_editorial_scorecard([
    {
        "label": "Flagged Jurisdictions",
        "value": str(n_flagged),
        "note": f"Out of {total} total evaluated units",
        "tag": "Divergent Outliers",
        "tag_bg": "#F7E5DE",
        "tag_fg": "#8A260F",
        "tag_border": "#E5A997",
    },
    {
        "label": "Contamination Ratio",
        "value": f"{pct_flagged:.1f}%",
        "note": "Target algorithmic bound: 10.0%",
        "tag": "Verified",
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
        "label": "Peak Outlier Magnitude",
        "value": f"{max_score:.1f}" if pd.notna(max_score) else "N/A",
        "note": "Highest recorded statistical deviation",
        "tag": "Focal Audit",
        "tag_bg": "#F7E5DE",
        "tag_fg": "#8A260F",
        "tag_border": "#E5A997",
    },
])

# ---------------------------------------------------------------------------
# Flagged Registry & Distribution Histogram
# ---------------------------------------------------------------------------
col_table, col_hist = st.columns([1.3, 1])

with col_table:
    render_section_header("SEC. 01", "Divergent Jurisdiction Register", "Flagged Outliers")

    if n_flagged == 0:
        st.success("No jurisdictions flagged as anomalous under the current forest parameters.")
    else:
        display_cols = ["district_name"]
        if "anomaly_score" in flagged_df.columns:
            display_cols.append("anomaly_score")
        if "unusual_features" in flagged_df.columns:
            display_cols.append("unusual_features")

        show = flagged_df[display_cols].copy()
        show.rename(
            columns={
                "district_name": "Jurisdiction",
                "anomaly_score": "Score",
                "unusual_features": "Divergent Feature Driver(s)",
            },
            inplace=True,
        )
        if "Score" in show.columns:
            show.sort_values("Score", ascending=False, inplace=True)
            show["Score"] = show["Score"].round(1)

        st.dataframe(show, hide_index=True, use_container_width=True)

with col_hist:
    if "anomaly_score" in anomalies_df.columns:
        render_section_header("SEC. 02", "Anomaly Score Density", "Empirical Frequency")

        fig_hist = px.histogram(
            anomalies_df,
            x="anomaly_score",
            nbins=22,
            color_discrete_sequence=["#1E3A2B"],
            labels={"anomaly_score": "Anomaly Score"},
        )
        fig_hist.update_traces(
            marker=dict(line=dict(width=0.8, color="#14241D"))
        )
        style_editorial_figure(
            fig_hist,
            height=280,
            title="Frequency Histogram",
            subtitle="Distribution of negated decision scores across 38 districts",
        )
        fig_hist.update_layout(xaxis_title="Score (0 = baseline, 100 = extreme)", yaxis_title="Count", bargap=0.1)
        st.plotly_chart(fig_hist, use_container_width=True)

# ---------------------------------------------------------------------------
# Detailed Indicator Comparison for a Selected Flagged District
# ---------------------------------------------------------------------------
if n_flagged > 0 and features_df is not None:
    render_section_header("SEC. 03", "Diagnostic Comparative Decomposition", "District vs. State Average")

    flagged_list = sorted(flagged_df["district_name"].dropna().unique())
    selected = st.selectbox("Select Target Outlier for Diagnostic Drill-Down", flagged_list, index=0)

    time_col = "period" if "period" in features_df.columns else ("year" if "year" in features_df.columns else None)
    if time_col and features_df[time_col].nunique() > 1:
        latest_period = features_df[time_col].dropna().max()
        fview = features_df[features_df[time_col] == latest_period].copy()
    else:
        fview = features_df.copy()

    district_row = fview[fview["district_name"] == selected]

    if not district_row.empty:
        dim_cols = [c for c in SUB_COLS.values() if c in fview.columns and fview[c].notna().any()]
        if dim_cols:
            district_vals = district_row.iloc[0][dim_cols]
            mean_vals = fview[dim_cols].mean()

            reverse_map = {v: k for k, v in SUB_COLS.items()}
            comp = pd.DataFrame(
                {
                    "Dimension": [reverse_map.get(c, c) for c in dim_cols],
                    selected: [
                        round(v, 1) if pd.notna(v) else None
                        for v in district_vals
                    ],
                    "State Baseline Average": [round(v, 1) for v in mean_vals],
                }
            )

            comp_long = comp.melt(
                id_vars="Dimension",
                value_vars=[selected, "State Baseline Average"],
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
                    selected: "#B84324",                 # Burnt orange for target outlier
                    "State Baseline Average": "#1E3A2B", # Deep forest green for state average
                },
                text="Index Score",
            )
            fig_comp.update_traces(
                texttemplate="%{y:.1f}",
                textposition="outside",
                marker=dict(line=dict(width=0.8, color="#14241D")),
                textfont=dict(family="IBM Plex Mono", size=10),
            )
            style_editorial_figure(
                fig_comp,
                height=340,
                title=f"Dimensional Discrepancy — {selected}",
                subtitle="Target jurisdiction relative to statewide benchmark means",
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        amatch = anomalies_df[anomalies_df["district_name"] == selected]
        if not amatch.empty:
            unusual = amatch.iloc[0].get("unusual_features", "")
            if pd.notna(unusual) and str(unusual).strip():
                st.markdown(
                    f"""
                    <div style="background:#FFFFFF; border:1px solid #E2DED4; border-left:3px solid #B84324; padding:12px 16px; margin-top:14px;">
                        <span style="font-family:'IBM Plex Mono'; font-size:0.7rem; font-weight:600; color:#8A260F; text-transform:uppercase; letter-spacing:0.08em;">Primary Deviation Drivers:</span>
                        <div style="font-family:'IBM Plex Mono'; font-size:0.82rem; color:#181A18; margin-top:4px;">{unusual}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
