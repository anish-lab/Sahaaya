"""
SAHAAYA — Anomaly Detection Results Page.

Displays districts flagged as anomalous by the pipeline, their anomaly scores,
unusual features, and comparison against district averages.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Anomaly Radar — SAHAAYA",
    page_icon="🚨",
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
    render_topbar,
    render_hero,
    render_kpi,
    render_sidebar_brand,
    style_plotly_fig,
)

# ---------------------------------------------------------------------------
# Theme & Top Navigation
# ---------------------------------------------------------------------------
inject_custom_theme()
render_topbar(current_page="Anomaly Radar")

render_hero(
    tag="ISOLATION FOREST RADAR",
    title="Multi-Variate Anomaly Detection",
    description="Unsupervised machine learning identifying districts that exhibit sharp divergence (> 1.5 standard deviations) from baseline state distributions. Prompts for diagnostic investigation, not definitive distress.",
)

render_sidebar_brand(get_data_status())

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
anomalies_df = load_anomalies()
features_df = load_features()

if anomalies_df is None:
    st.error(
        "**Anomaly results not found.** "
        "Run `python src/models/anomaly.py` to generate `anomaly_results.parquet`."
    )
    st.stop()

if features_df is not None and is_mock_data(features_df):
    st.warning("⚠️ Mock / synthetic data detected. Results are illustrative only.")

# ---------------------------------------------------------------------------
# Summary KPIs
# ---------------------------------------------------------------------------
total = len(anomalies_df)
flagged_df = anomalies_df[anomalies_df["anomaly_flag"] == True]  # noqa: E712
n_flagged = len(flagged_df)
pct_flagged = (n_flagged / total * 100) if total > 0 else 0
avg_score = anomalies_df["anomaly_score"].mean() if "anomaly_score" in anomalies_df.columns else None
max_score = anomalies_df["anomaly_score"].max() if "anomaly_score" in anomalies_df.columns else None

k1, k2, k3, k4 = st.columns(4)

with k1:
    render_kpi(
        "Flagged Districts",
        n_flagged,
        icon="🚨",
        color_accent="#e11d48",
        subtitle=f"Out of {total} total districts",
        badge_text="Outliers",
        badge_color="#ffe4e6",
        badge_text_color="#9f1239",
    )
with k2:
    render_kpi(
        "Anomaly Ratio",
        f"{pct_flagged:.1f}%",
        icon="📊",
        color_accent="#f97316",
        subtitle="Expected contamination: 10%",
        badge_text="Contamination",
        badge_color="#ffedd5",
        badge_text_color="#9a3412",
    )
with k3:
    render_kpi(
        "Mean Anomaly Score",
        f"{avg_score:.1f}" if pd.notna(avg_score) else "N/A",
        icon="📈",
        color_accent="#4f46e5",
        subtitle="Normalized 0-100 scale",
        badge_text="State baseline",
        badge_color="#e0e7ff",
        badge_text_color="#3730a3",
    )
with k4:
    render_kpi(
        "Peak Score",
        f"{max_score:.1f}" if pd.notna(max_score) else "N/A",
        icon="⚡",
        color_accent="#8b5cf6",
        subtitle="Highest deviation index",
        badge_text="Max outlier",
        badge_color="#f3e8ff",
        badge_text_color="#6b21a8",
    )

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Flagged Districts Table & Histogram
# ---------------------------------------------------------------------------
col_table, col_hist = st.columns([1.3, 1])

with col_table:
    st.markdown(
        "<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.15rem; color:#0f172a; margin-bottom:10px;'>"
        "🚨 Anomalous Districts & Deviation Drivers"
        "</div>",
        unsafe_allow_html=True,
    )

    if n_flagged == 0:
        st.success("No districts were flagged as anomalous under the current model.")
    else:
        display_cols = ["district_name"]
        if "anomaly_score" in flagged_df.columns:
            display_cols.append("anomaly_score")
        if "unusual_features" in flagged_df.columns:
            display_cols.append("unusual_features")

        show = flagged_df[display_cols].copy()
        show.rename(
            columns={
                "district_name": "District",
                "anomaly_score": "Score",
                "unusual_features": "Unusual Feature Drivers",
            },
            inplace=True,
        )
        if "Score" in show.columns:
            show.sort_values("Score", ascending=False, inplace=True)
            show["Score"] = show["Score"].round(1)

        st.dataframe(show, hide_index=True, use_container_width=True)

with col_hist:
    if "anomaly_score" in anomalies_df.columns:
        st.markdown(
            "<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.15rem; color:#0f172a; margin-bottom:10px;'>"
            "📊 State Anomaly Density"
            "</div>",
            unsafe_allow_html=True,
        )

        fig_hist = px.histogram(
            anomalies_df,
            x="anomaly_score",
            nbins=25,
            color_discrete_sequence=["#4f46e5"],
            labels={"anomaly_score": "Anomaly Score"},
        )
        fig_hist.update_traces(marker=dict(line=dict(width=1, color="rgba(255,255,255,0.8)")))
        style_plotly_fig(fig_hist, height=310)
        fig_hist.update_layout(xaxis_title="Anomaly Score (0-100)", yaxis_title="Districts Count", bargap=0.08)
        st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Detailed Indicator Comparison for a Selected Flagged District
# ---------------------------------------------------------------------------
if n_flagged > 0 and features_df is not None:
    st.markdown(
        "<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.25rem; color:#0f172a; margin-bottom:8px;'>"
        "🔬 Comparative Dimension Breakdown vs. State Average"
        "</div>",
        unsafe_allow_html=True,
    )

    flagged_list = sorted(flagged_df["district_name"].dropna().unique())
    selected = st.selectbox("Inspect Flagged District Profile", flagged_list, index=0)

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
                    "Tamil Nadu Average": [round(v, 1) for v in mean_vals],
                }
            )

            comp_long = comp.melt(
                id_vars="Dimension",
                value_vars=[selected, "Tamil Nadu Average"],
                var_name="Cohort",
                value_name="Risk Score",
            )

            fig_comp = px.bar(
                comp_long,
                x="Dimension",
                y="Risk Score",
                color="Cohort",
                barmode="group",
                range_y=[0, 100],
                color_discrete_map={
                    selected: "#e11d48",
                    "Tamil Nadu Average": "#4f46e5",
                },
                text="Risk Score",
            )
            fig_comp.update_traces(
                texttemplate="%{y:.1f}",
                textposition="outside",
            )
            style_plotly_fig(fig_comp, height=360, title=f"Risk Signature: {selected} vs. State Average")
            st.plotly_chart(fig_comp, use_container_width=True)

        amatch = anomalies_df[anomalies_df["district_name"] == selected]
        if not amatch.empty:
            unusual = amatch.iloc[0].get("unusual_features", "")
            if pd.notna(unusual) and str(unusual).strip():
                st.info(f"💡 **Specific Features Driving Anomaly:** `{unusual}`")
