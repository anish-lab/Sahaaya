"""
SAHAAYA — District Detail Drill-Down.

Shows a single district's risk profile: dimension scores, cluster membership,
anomaly flags, raw source indicators, and data provenance.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="District Explorer — SAHAAYA",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils import (  # noqa: E402
    load_features,
    load_clusters,
    load_anomalies,
    get_data_status,
    is_mock_data,
    SUB_COLS,
    BAND_COLORS,
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
render_topbar(current_page="District Detail")

# ---------------------------------------------------------------------------
# Load data & Sidebar
# ---------------------------------------------------------------------------
df = load_features()
clusters_df = load_clusters()
anomalies_df = load_anomalies()
render_sidebar_brand(get_data_status())

if df is None:
    st.error("**features.parquet not found.** Please run the data pipeline first.")
    st.stop()

if is_mock_data(df):
    st.warning("⚠️ Synthetic / mock data detected. Results are illustrative only.")

# ---------------------------------------------------------------------------
# Period & District Selector in Main Control Ribbon
# ---------------------------------------------------------------------------
time_col = "period" if "period" in df.columns else ("year" if "year" in df.columns else None)
if time_col and df[time_col].nunique() > 1:
    latest_period = df[time_col].dropna().max()
    view = df[df[time_col] == latest_period].copy()
else:
    view = df.copy()

districts = sorted(view["district_name"].dropna().unique())
if not districts:
    st.error("No district names found in the data.")
    st.stop()

# Interactive in-page selector ribbon
col_sel1, col_sel2 = st.columns([2, 1])
with col_sel1:
    district = st.selectbox("📍 Select District to Inspect", districts, index=0)
with col_sel2:
    period_str = str(view[time_col].iloc[0]) if time_col and not view.empty else "Latest Available"
    st.selectbox("📅 Reporting Period", [period_str], disabled=True)

row = view[view["district_name"] == district]
if row.empty:
    st.error(f"No data found for **{district}**.")
    st.stop()

latest = row.iloc[0]

# ---------------------------------------------------------------------------
# District Hero Header with Risk Badge
# ---------------------------------------------------------------------------
band = latest.get("risk_band", "Unknown")
badge_html = render_risk_pill(band)
district_id = latest.get("district_id", "")

st.markdown(
    f"""
    <div class="hero-banner" style="padding: 22px 28px; margin-top: 10px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <div class="hero-tag">DISTRICT PROFILE • {district_id}</div>
                <h1 style="font-size:2.2rem; font-weight:800; margin:0 0 4px 0; color:#0f172a;">{district}</h1>
                <div style="font-size:0.88rem; color:#64748b; font-weight:500;">
                    State of Tamil Nadu • Telemetry Assessment
                </div>
            </div>
            <div>
                {badge_html}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# KPI Row (Custom Styled)
# ---------------------------------------------------------------------------
def _fmt(val, decimals=1):
    if pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}f}"

k_cols = st.columns(6)

with k_cols[0]:
    render_kpi("Overall Score", _fmt(latest.get("overall_score")), icon="🎯", color_accent="#4f46e5", subtitle="Composite Index")
with k_cols[1]:
    render_kpi("Education Risk", _fmt(latest.get("edu_risk")), icon="🎓", color_accent="#06b6d4", subtitle="UDISE+ Metrics")
with k_cols[2]:
    render_kpi("Health Risk", _fmt(latest.get("health_risk")), icon="🏥", color_accent="#f59e0b", subtitle="NFHS-5 Metrics")
with k_cols[3]:
    render_kpi("Employment Risk", _fmt(latest.get("emp_risk")), icon="💼", color_accent="#8b5cf6", subtitle="MGNREGA telemetry")
with k_cols[4]:
    render_kpi("Infra Risk", _fmt(latest.get("infra_risk")), icon="⚡", color_accent="#ec4899", subtitle="School & Civic Infra")
with k_cols[5]:
    comp_val = latest.get("data_completeness")
    comp_str = f"{comp_val:.0%}" if pd.notna(comp_val) else "N/A"
    render_kpi("Completeness", comp_str, icon="🛡️", color_accent="#10b981", subtitle="Audited Signals")

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Visual Profiling: Dimension Breakdown + Cluster & Anomaly Intelligence
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1.1, 1])

with col_left:
    st.markdown(
        "<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.15rem; color:#0f172a; margin-bottom:12px;'>"
        "📊 Dimension Risk Decomposition"
        "</div>",
        unsafe_allow_html=True,
    )

    dim_data = []
    for label, col in SUB_COLS.items():
        val = latest.get(col)
        if pd.notna(val):
            dim_data.append({"Dimension": label, "Risk Score": float(val)})

    if dim_data:
        dim_df = pd.DataFrame(dim_data)
        fig_dim = px.bar(
            dim_df,
            x="Risk Score",
            y="Dimension",
            orientation="h",
            range_x=[0, 100],
            color="Risk Score",
            color_continuous_scale=[
                [0.0, "#10b981"],
                [0.4, "#fbbf24"],
                [0.7, "#f97316"],
                [1.0, "#e11d48"],
            ],
            text="Risk Score",
        )
        fig_dim.update_traces(
            texttemplate="%{x:.1f}",
            textposition="inside",
            marker=dict(line=dict(width=1, color="rgba(0,0,0,0.08)")),
        )
        style_plotly_fig(fig_dim, height=330)
        fig_dim.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig_dim, use_container_width=True)
    else:
        st.info("No dimension risk scores available for this district.")

with col_right:
    st.markdown(
        "<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.15rem; color:#0f172a; margin-bottom:12px;'>"
        "🔮 Peer Cluster & Anomaly Radar"
        "</div>",
        unsafe_allow_html=True,
    )

    # Cluster Card
    cluster_id = None
    if clusters_df is not None:
        match = clusters_df[clusters_df["district_name"] == district]
        if not match.empty:
            cluster_id = match.iloc[0]["cluster"]
    elif "cluster" in view.columns and pd.notna(latest.get("cluster")):
        cluster_id = latest["cluster"]

    if cluster_id is not None:
        cid_str = f"Cluster {int(cluster_id)}"
        # Siblings
        if clusters_df is not None:
            siblings = sorted(clusters_df[clusters_df["cluster"] == cluster_id]["district_name"].dropna().unique().tolist())
        else:
            siblings = sorted(view[view["cluster"] == cluster_id]["district_name"].dropna().unique().tolist())
        siblings = [n for n in siblings if n != district]
        sib_text = ", ".join(siblings[:6]) + (f" + {len(siblings)-6} more" if len(siblings) > 6 else "")

        st.markdown(
            f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:16px; margin-bottom:14px; box-shadow:0 2px 8px -2px rgba(15,23,42,0.04);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.75rem; font-weight:700; color:#4f46e5; text-transform:uppercase; letter-spacing:0.05em;">Cluster Assignment</span>
                    <span style="background:#e0e7ff; color:#3730a3; padding:2px 8px; border-radius:6px; font-weight:700; font-size:0.75rem;">{cid_str}</span>
                </div>
                <div style="font-size:0.85rem; color:#334155; margin-top:8px; line-height:1.4;">
                    <b>Statistical Peers:</b> {sib_text if sib_text else "None"}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Cluster data not available. Run the clustering step.")

    # Anomaly Card
    if anomalies_df is not None:
        amatch = anomalies_df[anomalies_df["district_name"] == district]
        if not amatch.empty:
            arow = amatch.iloc[0]
            flagged = arow.get("anomaly_flag", False)
            ascore = arow.get("anomaly_score", 0.0)
            unusual = arow.get("unusual_features", "None detected")

            if flagged:
                st.markdown(
                    f"""
                    <div style="background:#fff1f2; border:1px solid #fecdd3; border-radius:14px; padding:16px; box-shadow:0 2px 8px -2px rgba(225,29,72,0.06);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:0.75rem; font-weight:700; color:#e11d48; text-transform:uppercase;">🚨 Anomaly Detected</span>
                            <span style="background:#ffe4e6; color:#9f1239; padding:2px 8px; border-radius:6px; font-weight:700; font-size:0.75rem;">Score: {_fmt(ascore, 1)}</span>
                        </div>
                        <div style="font-size:0.85rem; color:#881337; margin-top:8px; line-height:1.4;">
                            <b>Unusual Feature Drivers:</b> {unusual}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="background:#ecfdf5; border:1px solid #a7f3d0; border-radius:14px; padding:16px; box-shadow:0 2px 8px -2px rgba(16,185,129,0.04);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:0.75rem; font-weight:700; color:#065f46; text-transform:uppercase;">✅ Standard Distribution Pattern</span>
                            <span style="background:#d1fae5; color:#064e3b; padding:2px 8px; border-radius:6px; font-weight:700; font-size:0.75rem;">Score: {_fmt(ascore, 1)}</span>
                        </div>
                        <div style="font-size:0.85rem; color:#065f46; margin-top:8px;">
                            No anomalous deviation detected relative to regional peer patterns.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Raw Indicator Table & Provenance
# ---------------------------------------------------------------------------
st.markdown(
    "<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.15rem; color:#0f172a; margin-bottom:12px;'>"
    "📑 Source Indicator Telemetry"
    "</div>",
    unsafe_allow_html=True,
)

standard_cols = {
    "district_id", "district_name", "state", "period", "year",
    "edu_risk", "health_risk", "emp_risk", "infra_risk",
    "overall_score", "risk_band", "data_completeness",
    "cluster", "anomaly_flag", "anomaly_score", "pred_next_score",
}
indicator_cols = [c for c in row.columns if c not in standard_cols]

if indicator_cols:
    indicator_data = row[indicator_cols].T.copy()
    indicator_data.columns = ["Reported Value"]
    indicator_data.index.name = "Telemetry Indicator"
    indicator_data["Reported Value"] = indicator_data["Reported Value"].apply(
        lambda v: f"{v:,.2f}" if isinstance(v, (int, float)) and pd.notna(v) else ("N/A" if pd.isna(v) else str(v))
    ).astype(str)
    st.dataframe(indicator_data, use_container_width=True)
else:
    st.info("No raw source indicators found beyond composite risk scores.")

with st.expander("🔍 Telemetry Provenance"):
    st.markdown(f"**District ID:** `{district_id}`")
    if time_col and pd.notna(latest.get(time_col)):
        st.markdown(f"**Observation Period:** `{latest[time_col]}`")
    st.caption("All indicators are audited and normalized against Tamil Nadu state distributions.")
