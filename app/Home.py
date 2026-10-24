"""
SAHAAYA Home — Statewide social-vulnerability dashboard for Tamil Nadu.

Civic Intelligence, Editorial Precision aesthetic:
Warm ivory surfaces, deep forest-green accents, Newsreader serif typography,
and restrained burnt-orange highlights.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="SAHAAYA — Civic Vulnerability Observatory",
    page_icon="§",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils import (  # noqa: E402
    load_features,
    load_geojson,
    get_data_status,
    is_mock_data,
    GEO_NAME_KEY,
    SUB_COLS,
    BAND_COLORS,
    BAND_ORDER,
)
from ui_theme import (  # noqa: E402
    inject_custom_theme,
    render_masthead,
    render_section_header,
    render_editorial_scorecard,
    render_sidebar_masthead,
    style_editorial_figure,
    MAP_COLORSCALE,
)

# ---------------------------------------------------------------------------
# Theme & Masthead
# ---------------------------------------------------------------------------
inject_custom_theme()
render_sidebar_masthead(get_data_status())

render_masthead(
    folio_code="VOL. IV · DISPATCH 2026.10 · STATE REGISTRY SURVEY",
    title="Tamil Nadu Social Vulnerability & Early Warning Observatory",
    deck="Multi-sectoral early warning radar synthesizing educational delivery (UDISE+), public health telemetry (NFHS-5), and civic infrastructure across 38 canonical administrative districts.",
    location_tag="TAMIL NADU · 11°07' N, 78°39' E",
)

# ---------------------------------------------------------------------------
# Data Load & Verification
# ---------------------------------------------------------------------------
df = load_features()

if df is None:
    st.error("Telemetry store `features.parquet` not located. Please execute the ingestion pipeline.")
    st.info("Run `python src/pipeline.py` to compile district feature sets.")
    st.stop()

if is_mock_data(df):
    st.warning("Notice: Synthetic test dataset active. Figures reflect simulated distributions.")

# ---------------------------------------------------------------------------
# Control Ribbon — Flush Editorial Filter Strip
# ---------------------------------------------------------------------------
time_col = "period" if "period" in df.columns else ("year" if "year" in df.columns else None)
metric_map = {"Overall Composite Vulnerability": "overall_score", **SUB_COLS}

col_f1, col_f2, col_f3 = st.columns([1.5, 2.5, 1])

with col_f1:
    if time_col and df[time_col].nunique() > 1:
        periods = sorted(df[time_col].dropna().unique(), reverse=True)
        chosen = st.selectbox("Reporting Horizon", periods, index=0)
        view = df[df[time_col] == chosen].copy()
    else:
        chosen = df[time_col].iloc[0] if time_col and not df.empty else "Current Administrative Audit"
        st.selectbox("Reporting Horizon", [str(chosen)], disabled=True)
        view = df.copy()

with col_f2:
    metric_label = st.selectbox("Evaluated Risk Dimension", list(metric_map.keys()), index=0)
    metric_col = metric_map[metric_label]

with col_f3:
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-family:\"IBM Plex Mono\"; font-size:0.7rem; color:#6E756C; text-align:right; padding-top:6px;'>"
        f"DISTRICTS: <b>{view['district_name'].nunique()}</b>"
        f"</div>",
        unsafe_allow_html=True,
    )

if metric_col not in view.columns:
    st.warning(f"Dimension '{metric_col}' not found in active dataset.")
    st.stop()

# ---------------------------------------------------------------------------
# Integrated Editorial Scorecard (Replaces Generic Floating Cards)
# ---------------------------------------------------------------------------
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

render_editorial_scorecard([
    {
        "label": "Jurisdictions Audited",
        "value": str(n_districts),
        "note": "Canonical Tamil Nadu administrative units",
        "tag": "Synchronized",
        "tag_bg": "#EAEFEA",
        "tag_fg": "#264230",
        "tag_border": "#BDCFBF",
    },
    {
        "label": f"Mean {metric_label.split()[0]} Index",
        "value": f"{avg_score:.1f}" if pd.notna(avg_score) else "N/A",
        "note": "Normalized 0–100 scale (higher indicates elevated stress)",
    },
    {
        "label": "High & Critical Quartile",
        "value": str(high_crit),
        "note": "Districts requiring immediate intervention",
        "tag": "Priority Alert",
        "tag_bg": "#F7E5DE",
        "tag_fg": "#8A260F",
        "tag_border": "#E5A997",
    },
    {
        "label": "Telemetry Completeness",
        "value": str(completeness),
        "note": "Mean multi-sector feature parity across inputs",
        "tag": "Audited",
        "tag_bg": "#EFECE4",
        "tag_fg": "#444A43",
        "tag_border": "#D5D0C5",
    },
])

# ---------------------------------------------------------------------------
# Main Asymmetric Canvas — Cartographic View & Watchlist
# ---------------------------------------------------------------------------
col_map, col_tables = st.columns([1.5, 1])

with col_map:
    render_section_header("SEC. 01", "Geographic Vulnerability Distribution", "Spatial Deciling")

    geo = load_geojson()
    if geo is not None:
        fig_map = px.choropleth(
            view,
            geojson=geo,
            locations="district_name",
            featureidkey=GEO_NAME_KEY,
            color=metric_col,
            color_continuous_scale=MAP_COLORSCALE,
            range_color=(0, 100),
            hover_name="district_name",
            hover_data={
                "district_name": False,
                metric_col: ":.1f",
                "risk_band": True if "risk_band" in view.columns else False,
            },
            labels={metric_col: "Index", "risk_band": "Risk Band"},
        )
        fig_map.update_geos(
            fitbounds="locations",
            visible=False,
            bgcolor="rgba(0,0,0,0)",
        )
        fig_map.update_traces(
            marker_line_width=0.6,
            marker_line_color="#2B362F",
        )
        style_editorial_figure(
            fig_map,
            height=600,
            title="Cartographic Survey",
            subtitle=f"Spatial deciling across Tamil Nadu · {metric_label}",
        )
        fig_map.update_layout(
            coloraxis_colorbar=dict(
                title=dict(text="Index", font=dict(family="IBM Plex Mono", size=10)),
                thickness=10,
                len=0.65,
                x=0.98,
                tickfont=dict(size=9, family="IBM Plex Mono", color="#5E655D"),
                bgcolor="rgba(247, 245, 238, 0.8)",
                bordercolor="#E2DED4",
                borderwidth=1,
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Boundary geometry not detected. Showing rank-ordered bar chart.")
        sorted_view = view.sort_values(metric_col, ascending=True)
        fig_bar = px.bar(
            sorted_view,
            x=metric_col,
            y="district_name",
            orientation="h",
            color=metric_col,
            color_continuous_scale=MAP_COLORSCALE,
            range_color=(0, 100),
            labels={metric_col: "Index", "district_name": "District"},
        )
        style_editorial_figure(
            fig_bar,
            height=max(450, len(sorted_view) * 20),
            title="Rank-Ordered Distribution",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with col_tables:
    render_section_header("SEC. 02", "Priority Watchlist", f"Upper Decile in {metric_label}")

    display_cols = ["district_name", metric_col]
    if "risk_band" in view.columns:
        display_cols.append("risk_band")

    top = (
        view.sort_values(metric_col, ascending=False)
        .head(10)[display_cols]
        .copy()
    )
    rename = {"district_name": "District", metric_col: "Index"}
    if "risk_band" in top.columns:
        rename["risk_band"] = "Risk Band"
    top.rename(columns=rename, inplace=True)
    top["Index"] = top["Index"].round(1)

    st.dataframe(top, hide_index=True, use_container_width=True)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    render_section_header("SEC. 03", "Statewide Risk-Band Census", "Categorical Classification")

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
            marker=dict(line=dict(width=1, color="#2D332D")),
            textfont=dict(family="IBM Plex Mono", size=10),
        )
        style_editorial_figure(
            fig_band,
            height=250,
            title="Risk Tier Census",
            subtitle="Frequency distribution across 4 canonical tiers",
        )
        fig_band.update_layout(showlegend=False)
        st.plotly_chart(fig_band, use_container_width=True)

# ---------------------------------------------------------------------------
# Editorial Colophon & Methodology
# ---------------------------------------------------------------------------
with st.expander("Methodological Notes & Ingestion Provenance"):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            "**Data Sources & Normalization**\n\n"
            "Indices are computed using min-max linear feature scaling normalized over historical state bounds. "
            "Primary inputs include UDISE+ school infrastructure and enrollment telemetry, NFHS-5 district nutritional indicators, "
            "and MGNREGA rural employment person-day metrics."
        )
    with c2:
        standard = {
            "district_id", "district_name", "state", "period", "year",
            "edu_risk", "health_risk", "emp_risk", "infra_risk",
            "overall_score", "risk_band", "data_completeness",
            "cluster", "anomaly_flag", "anomaly_score", "pred_next_score",
        }
        source_cols = [c for c in df.columns if c not in standard]
        st.markdown(
            f"**Audit Parameters**\n\n"
            f"- Observation Period: `{view[time_col].iloc[0] if time_col else 'Current'}`\n"
            f"- Integrated Telemetry Fields: `{len(source_cols)} indicators`\n"
            f"- Canonical Geometries: `38 districts (Tamil Nadu Survey 2021-2024)`"
        )
