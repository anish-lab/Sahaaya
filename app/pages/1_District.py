"""
SAHAAYA — District Detail Drill-Down.

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
    page_title="District Dossier — SAHAAYA",
    page_icon="§",
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

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = load_features()
clusters_df = load_clusters()
anomalies_df = load_anomalies()

if df is None:
    st.error("Telemetry store `features.parquet` not located. Please execute the ingestion pipeline.")
    st.stop()

if is_mock_data(df):
    st.warning("Notice: Synthetic test dataset active. Figures reflect simulated distributions.")

# ---------------------------------------------------------------------------
# Control Ribbon — District Selector
# ---------------------------------------------------------------------------
time_col = "period" if "period" in df.columns else ("year" if "year" in df.columns else None)
if time_col and df[time_col].nunique() > 1:
    latest_period = df[time_col].dropna().max()
    view = df[df[time_col] == latest_period].copy()
else:
    view = df.copy()

districts = sorted(view["district_name"].dropna().unique())
if not districts:
    st.error("No districts located in the active telemetry repository.")
    st.stop()

col_sel1, col_sel2 = st.columns([2.5, 1])
with col_sel1:
    district = st.selectbox("Selected Administrative Jurisdiction", districts, index=0)
with col_sel2:
    period_str = str(view[time_col].iloc[0]) if time_col and not view.empty else "Current Administrative Audit"
    st.selectbox("Reporting Period", [period_str], disabled=True)

row = view[view["district_name"] == district]
if row.empty:
    st.error(f"No records found for '{district}'.")
    st.stop()

latest = row.iloc[0]
district_id = latest.get("district_id", "N/A")
band = latest.get("risk_band", "Moderate")

# ---------------------------------------------------------------------------
# Dossier Folio Masthead
# ---------------------------------------------------------------------------
render_masthead(
    folio_code=f"JURISDICTION DOSSIER · CODE: {district_id}",
    title=district,
    deck=f"Diagnostic vulnerability dossier for {district} district/state. Telemetry synthesized across demographic, nutritional, and institutional service delivery indices.",
    location_tag=f"TIER: {band.upper()} VULNERABILITY",
)

# ---------------------------------------------------------------------------
# Integrated Scorecard
# ---------------------------------------------------------------------------
def _fmt(val, decimals=1):
    if pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}f}"

comp_val = latest.get("data_completeness")
comp_str = f"{comp_val:.0%}" if pd.notna(comp_val) else "N/A"

render_editorial_scorecard([
    {
        "label": "Overall Composite Index",
        "value": _fmt(latest.get("overall_score")),
        "note": "Combined risk index",
        "tag": str(band),
        "tag_bg": "#FAEDE3" if str(band) in ["High", "Critical"] else "#EAEFEA",
        "tag_fg": "#8C4318" if str(band) in ["High", "Critical"] else "#264230",
        "tag_border": "#E8C1A5" if str(band) in ["High", "Critical"] else "#BDCFBF",
    },
    {
        "label": "Education Vulnerability",
        "value": _fmt(latest.get("edu_risk")),
        "note": "UDISE+ infrastructure & enrollment",
    },
    {
        "label": "Healthcare Deficit",
        "value": _fmt(latest.get("health_risk")),
        "note": "NFHS-5 maternal & child nutrition",
    },
    {
        "label": "Employment Deficit",
        "value": _fmt(latest.get("emp_risk")),
        "note": "MGNREGA personday coverage",
    },
    {
        "label": "Civic Infrastructure",
        "value": _fmt(latest.get("infra_risk")),
        "note": "Drinking water, sanitation, power",
    },
    {
        "label": "Audited Telemetry",
        "value": comp_str,
        "note": "Feature presence across dimensions",
        "tag": "Verified",
        "tag_bg": "#EFECE4",
        "tag_fg": "#444A43",
        "tag_border": "#D5D0C5",
    },
])

# ---------------------------------------------------------------------------
# Asymmetric Layout: Risk Breakdown vs. Typology & Anomaly Status
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1.2, 1])

with col_left:
    render_section_header("SEC. 01", "Dimension Decomposition", "Normalized Stress Profiles")

    dim_data = []
    for label, col in SUB_COLS.items():
        val = latest.get(col)
        if pd.notna(val):
            dim_data.append({"Dimension": label, "Index": float(val)})

    if dim_data:
        dim_df = pd.DataFrame(dim_data)
        fig_dim = px.bar(
            dim_df,
            x="Index",
            y="Dimension",
            orientation="h",
            range_x=[0, 100],
            color="Index",
            color_continuous_scale=[
                [0.0, "#385E48"],   # Deep sage
                [0.4, "#827845"],   # Antique olive
                [0.7, "#BA6835"],   # Terracotta
                [1.0, "#A83C1F"],   # Burnt sienna
            ],
            text="Index",
        )
        fig_dim.update_traces(
            texttemplate="%{x:.1f}",
            textposition="outside",
            marker=dict(line=dict(width=0.8, color="#253528")),
            textfont=dict(family="IBM Plex Mono", size=10),
        )
        style_editorial_figure(
            fig_dim,
            height=300,
            title=f"Dimensional Burden — {district}",
            subtitle="Relative intensity across four core pillars (0 = optimal, 100 = distress)",
        )
        fig_dim.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig_dim, use_container_width=True)
    else:
        st.info("No dimension scores available for this jurisdiction.")

with col_right:
    render_section_header("SEC. 02", "Typology & Diagnostic Flags", "Machine Learning Intelligence")

    # Cluster Card
    cluster_id = None
    if clusters_df is not None:
        match = clusters_df[clusters_df["district_name"] == district]
        if not match.empty:
            cluster_id = match.iloc[0]["cluster"]
    elif "cluster" in view.columns and pd.notna(latest.get("cluster")):
        cluster_id = latest["cluster"]

    if cluster_id is not None:
        cid_str = f"Typology Archetype {int(cluster_id)}"
        if clusters_df is not None:
            siblings = sorted(clusters_df[clusters_df["cluster"] == cluster_id]["district_name"].dropna().unique().tolist())
        else:
            siblings = sorted(view[view["cluster"] == cluster_id]["district_name"].dropna().unique().tolist())
        siblings = [n for n in siblings if n != district]
        sib_text = ", ".join(siblings[:6]) + (f" + {len(siblings)-6} others" if len(siblings) > 6 else "")

        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #E2DED4; border-left:3px solid #14241D; padding:14px 16px; margin-bottom:14px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-family:'IBM Plex Mono'; font-size:0.68rem; color:#6E756C; text-transform:uppercase; letter-spacing:0.1em;">K-Means Typology</span>
                    <span style="font-family:'IBM Plex Mono'; font-size:0.75rem; font-weight:600; color:#14241D;">{cid_str}</span>
                </div>
                <div style="font-family:'IBM Plex Sans'; font-size:0.84rem; color:#333733; margin-top:6px; line-height:1.45;">
                    <b>Statistical Peer Cohort:</b> {sib_text if sib_text else "No peer districts identified."}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Typology assignments not compiled.")

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
                    <div style="background:#F7E5DE; border:1px solid #E5A997; border-left:3px solid #B84324; padding:14px 16px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-family:'IBM Plex Mono'; font-size:0.68rem; font-weight:600; color:#8A260F; text-transform:uppercase; letter-spacing:0.1em;">§ Anomaly Flagged</span>
                            <span style="font-family:'IBM Plex Mono'; font-size:0.75rem; font-weight:600; color:#8A260F;">Score: {_fmt(ascore, 1)} / 100</span>
                        </div>
                        <div style="font-family:'IBM Plex Sans'; font-size:0.82rem; color:#611A0B; margin-top:6px; line-height:1.45;">
                            <b>Divergent Features:</b> <code>{unusual}</code>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="background:#EAEFEA; border:1px solid #BDCFBF; border-left:3px solid #385E48; padding:14px 16px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-family:'IBM Plex Mono'; font-size:0.68rem; font-weight:600; color:#264230; text-transform:uppercase; letter-spacing:0.1em;">Standard Distribution Envelope</span>
                            <span style="font-family:'IBM Plex Mono'; font-size:0.75rem; font-weight:600; color:#264230;">Score: {_fmt(ascore, 1)} / 100</span>
                        </div>
                        <div style="font-family:'IBM Plex Sans'; font-size:0.82rem; color:#264230; margin-top:6px;">
                            No anomalous multi-variate deviation detected relative to regional peer trajectories.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------------------------
# Raw Indicator Telemetry Table
# ---------------------------------------------------------------------------
render_section_header("SEC. 03", "Primary Telemetry Ledger", "Raw Survey Observations")

standard_cols = {
    "district_id", "district_name", "state", "period", "year",
    "edu_risk", "health_risk", "emp_risk", "infra_risk",
    "overall_score", "risk_band", "data_completeness",
    "cluster", "anomaly_flag", "anomaly_score", "pred_next_score",
}
indicator_cols = [c for c in row.columns if c not in standard_cols]

if indicator_cols:
    indicator_data = row[indicator_cols].T.copy()
    indicator_data.columns = ["Reported Metric"]
    indicator_data.index.name = "Telemetry Indicator Field"
    indicator_data["Reported Metric"] = indicator_data["Reported Metric"].apply(
        lambda v: f"{v:,.2f}" if isinstance(v, (int, float)) and pd.notna(v) else ("N/A" if pd.isna(v) else str(v))
    ).astype(str)
    st.dataframe(indicator_data, use_container_width=True)
else:
    st.info("No raw telemetry fields found beyond composite indices.")

with st.expander("Jurisdiction Telemetry Provenance"):
    st.markdown(
        f"- **Canonical Identifier:** `{district_id}`\n"
        f"- **Observation Window:** `{latest.get(time_col, 'Current')}`\n"
        f"- **Constituent Features Audited:** `{len(indicator_cols)} variables`\n"
        f"- **Standardization Rule:** Min-max feature clipping against historical state extrema."
    )
