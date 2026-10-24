"""
SAHAAYA Home — Statewide social-vulnerability dashboard for Tamil Nadu.

Displays KPI summary, choropleth / bar-chart map, top-risk table,
and risk-band distribution.  All data comes from the processed pipeline
outputs; if they are missing the page shows setup instructions instead.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="SAHAAYA — Social Vulnerability Radar",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils import (  # noqa: E402
    load_features,
    load_geojson,
    load_clusters,
    load_anomalies,
    get_data_status,
    is_mock_data,
    GEO_NAME_KEY,
    SUB_COLS,
    BAND_COLORS,
    BAND_ORDER,
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
render_topbar(current_page="Overview")

render_hero(
    tag="AI CIVIC INTELLIGENCE",
    title="Tamil Nadu Social Vulnerability & Early Warning",
    description="Multi-dimensional risk radar synthesizing education (UDISE+), health (NFHS-5), and infrastructure signals to support evidence-based policy targeting and proactive resource allocation.",
)

# ---------------------------------------------------------------------------
# Sidebar — Branded Status Panel
# ---------------------------------------------------------------------------
status = get_data_status()
render_sidebar_brand(status)

# ---------------------------------------------------------------------------
# Load features & production guard
# ---------------------------------------------------------------------------
df = load_features()

if df is None:
    st.error("**features.parquet not found.**")
    st.info(
        "Run the data pipeline first to generate the processed data:\n\n"
        "```bash\n"
        "python -m src.pipeline\n"
        "```\n\n"
        "The pipeline will create `data/processed/features.parquet` and other outputs."
    )
    st.stop()

if is_mock_data(df):
    st.warning(
        "⚠️ **Synthetic / Mock dataset detected.** "
        "Results shown are illustrative. Run the real ingestion pipeline to update."
    )

# ---------------------------------------------------------------------------
# In-Page Control Ribbon (No need to search the sidebar)
# ---------------------------------------------------------------------------
time_col = "period" if "period" in df.columns else ("year" if "year" in df.columns else None)
metric_map = {"Overall Composite Risk": "overall_score", **SUB_COLS}

col_filter1, col_filter2, col_filter3 = st.columns([1.5, 2.5, 1])

with col_filter1:
    if time_col and df[time_col].nunique() > 1:
        periods = sorted(df[time_col].dropna().unique(), reverse=True)
        chosen = st.selectbox("📅 Reporting Period", periods, index=0)
        view = df[df[time_col] == chosen].copy()
    else:
        chosen = df[time_col].iloc[0] if time_col and not df.empty else "Latest Available"
        st.selectbox("📅 Reporting Period", [str(chosen)], disabled=True)
        view = df.copy()

with col_filter2:
    metric_label = st.selectbox(
        "📊 Target Dimension / Score",
        list(metric_map.keys()),
        index=0,
    )
    metric_col = metric_map[metric_label]

with col_filter3:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:right; font-size:0.75rem; color:#64748b; font-weight:600; padding-top:6px;'>"
        f"Districts Loaded: <b>{view['district_name'].nunique()}</b>"
        f"</div>",
        unsafe_allow_html=True,
    )

if metric_col not in view.columns:
    st.warning(f"Column `{metric_col}` not found in dataset.")
    st.stop()

st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)

n_districts = view["district_name"].nunique()
avg_score = view[metric_col].mean()
high_crit = (
    view["risk_band"].isin(["High", "Critical"]).sum()
    if "risk_band" in view.columns
    else "N/A"
)
completeness = (
    f"{view['data_completeness'].mean():.0%}"
    if "data_completeness" in view.columns
    else "N/A"
)

with k1:
    render_kpi(
        label="Districts Monitored",
        value=n_districts,
        icon="🏛️",
        subtitle="Canonical district coverage",
        color_accent="#4f46e5",
        badge_text="Active",
        badge_color="#e0e7ff",
        badge_text_color="#3730a3",
    )

with k2:
    render_kpi(
        label=f"Avg {metric_label.split()[0]} Score",
        value=f"{avg_score:.1f}" if pd.notna(avg_score) else "N/A",
        icon="📈",
        subtitle="Normalized index (0-100 scale)",
        color_accent="#06b6d4",
        badge_text="Benchmark",
        badge_color="#e0f2fe",
        badge_text_color="#0369a1",
    )

with k3:
    render_kpi(
        label="High / Critical Distress",
        value=high_crit,
        icon="🚨",
        subtitle="Districts in upper risk quartile",
        color_accent="#f43f5e",
        badge_text="Priority Watch",
        badge_color="#ffe4e6",
        badge_text_color="#9f1239",
    )

with k4:
    render_kpi(
        label="Data Completeness",
        value=completeness,
        icon="🛡️",
        subtitle="Cross-sector indicator parity",
        color_accent="#10b981",
        badge_text="Audited",
        badge_color="#ecfdf5",
        badge_text_color="#065f46",
    )

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Main Interactive Canvas — Spatial Map & Top-Risk Analysis
# ---------------------------------------------------------------------------
col_map, col_details = st.columns([3, 2])

with col_map:
    geo = load_geojson()
    if geo is not None:
        # Custom elegant continuous scale (Emerald -> Light Amber -> Orange -> Deep Rose)
        custom_scale = [
            [0.0, "#10b981"],
            [0.35, "#34d399"],
            [0.55, "#fbbf24"],
            [0.75, "#f97316"],
            [1.0, "#e11d48"],
        ]

        fig_map = px.choropleth(
            view,
            geojson=geo,
            locations="district_name",
            featureidkey=GEO_NAME_KEY,
            color=metric_col,
            color_continuous_scale=custom_scale,
            range_color=(0, 100),
            hover_name="district_name",
            hover_data={
                "district_name": False,
                metric_col: ":.1f",
                "risk_band": True if "risk_band" in view.columns else False,
            },
            labels={metric_col: "Risk Score", "risk_band": "Risk Band"},
        )
        fig_map.update_geos(
            fitbounds="locations",
            visible=False,
            bgcolor="rgba(0,0,0,0)",
        )
        style_plotly_fig(fig_map, height=620, title=f"Spatial Geographic Distribution — {metric_label}")
        fig_map.update_layout(
            coloraxis_colorbar=dict(
                title="Index",
                thickness=12,
                len=0.7,
                x=0.98,
                bgcolor="rgba(255,255,255,0.7)",
                tickfont=dict(size=10, family="Plus Jakarta Sans"),
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("District boundary GeoJSON not found. Displaying sorted comparative ranking.")
        sorted_view = view.sort_values(metric_col, ascending=True)
        fig_bar = px.bar(
            sorted_view,
            x=metric_col,
            y="district_name",
            orientation="h",
            color=metric_col,
            color_continuous_scale="Viridis",
            range_color=(0, 100),
            labels={metric_col: "Index Score", "district_name": "District"},
        )
        style_plotly_fig(fig_bar, height=max(450, len(sorted_view) * 22), title=f"Comparative Ranking — {metric_label}")
        st.plotly_chart(fig_bar, use_container_width=True)

with col_details:
    # --- Top-10 Priority Watch ---
    st.markdown(
        f"<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.15rem; color:#0f172a; margin-bottom:8px;'>"
        f"🚨 Priority Watchlist — Top 10 by {metric_label}"
        f"</div>",
        unsafe_allow_html=True,
    )

    display_cols = ["district_name", metric_col]
    if "risk_band" in view.columns:
        display_cols.append("risk_band")

    top = (
        view.sort_values(metric_col, ascending=False)
        .head(10)[display_cols]
        .copy()
    )
    rename = {"district_name": "District", metric_col: "Score"}
    if "risk_band" in top.columns:
        rename["risk_band"] = "Risk Band"
    top.rename(columns=rename, inplace=True)
    top["Score"] = top["Score"].round(1)

    st.dataframe(
        top,
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)

    # --- Risk Band Distribution ---
    if "risk_band" in view.columns:
        counts = (
            view["risk_band"]
            .value_counts()
            .reindex(BAND_ORDER)
            .fillna(0)
            .astype(int)
            .reset_index()
        )
        counts.columns = ["Band", "Count"]

        fig_band = px.bar(
            counts,
            x="Band",
            y="Count",
            color="Band",
            color_discrete_map=BAND_COLORS,
            category_orders={"Band": BAND_ORDER},
            text="Count",
        )
        fig_band.update_traces(
            textposition="outside",
            marker=dict(line=dict(width=1, color="rgba(0,0,0,0.1)")),
        )
        style_plotly_fig(fig_band, height=270, title="Statewide Risk-Band Census")
        fig_band.update_layout(showlegend=False)
        st.plotly_chart(fig_band, use_container_width=True)

# ---------------------------------------------------------------------------
# Data Provenance Expander
# ---------------------------------------------------------------------------
with st.expander("🔍 Telemetry & Data Provenance Details"):
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        if "period" in view.columns:
            st.markdown(f"**Reporting Period:** `{', '.join(map(str, df['period'].dropna().unique()))}`")
        st.markdown(f"**Canonical District Count:** `{len(view)}`")
        if "data_completeness" in view.columns:
            st.markdown(f"**Mean Feature Completeness:** `{view['data_completeness'].mean():.1%}`")
    with c_p2:
        standard = {
            "district_id", "district_name", "state", "period", "year",
            "edu_risk", "health_risk", "emp_risk", "infra_risk",
            "overall_score", "risk_band", "data_completeness",
            "cluster", "anomaly_flag", "anomaly_score", "pred_next_score",
        }
        source_cols = [c for c in df.columns if c not in standard]
        st.markdown(f"**Source Indicators Integrated:** `{len(source_cols)} indicators`")
        if source_cols:
            st.caption(", ".join(source_cols[:12]) + ("..." if len(source_cols) > 12 else ""))
