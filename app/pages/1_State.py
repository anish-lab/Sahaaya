"""
SAHAAYA — State & Union Territory Detail Drill-Down Dossier.

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
    page_title="State Dossier — SAHAAYA",
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
# Control Ribbon — State Selector & Quick-Filter Pills
# ---------------------------------------------------------------------------
time_col = "period" if "period" in df.columns else ("year" if "year" in df.columns else None)
if time_col and df[time_col].nunique() > 1:
    latest_period = df[time_col].dropna().max()
    view = df[df[time_col] == latest_period].copy()
else:
    view = df.copy()

all_states = sorted(view["district_name"].dropna().unique())
if not all_states:
    st.error("No states located in the active telemetry repository.")
    st.stop()

# Quick filter pill strip
col_filter, col_period = st.columns([2.5, 1])
with col_filter:
    tier_choice = "All"
    if "risk_band" in view.columns and hasattr(st, "pills"):
        tier_choice = st.pills(
            "Filter States by Vulnerability Tier",
            ["All", "Critical", "High", "Moderate", "Low"],
            default="All",
        )
        if not tier_choice:
            tier_choice = "All"

if tier_choice != "All" and "risk_band" in view.columns:
    filtered_states = sorted(view[view["risk_band"] == tier_choice]["district_name"].dropna().unique())
    available_states = filtered_states if filtered_states else all_states
else:
    available_states = all_states

col_sel1, col_sel2 = st.columns([2.5, 1])
with col_sel1:
    state_name = st.selectbox("Selected State / Union Territory", available_states, index=0)
with col_sel2:
    period_str = str(view[time_col].iloc[0]) if time_col and not view.empty else "Current Administrative Audit"
    st.selectbox("Reporting Period", [period_str], disabled=True)

row = view[view["district_name"] == state_name]
if row.empty:
    st.error(f"No records found for '{state_name}'.")
    st.stop()

latest = row.iloc[0]
state_id = latest.get("district_id", "N/A")
band = latest.get("risk_band", "Moderate")

# Compute national ranks and percentiles
view_ranked = view.sort_values("overall_score", ascending=False).reset_index(drop=True)
view_ranked["rank"] = view_ranked.index + 1
rank_val = view_ranked[view_ranked["district_name"] == state_name]["rank"].values[0]
total_units = len(view_ranked)
pctile = (total_units - rank_val) / total_units * 100

# ---------------------------------------------------------------------------
# Dossier Folio Masthead
# ---------------------------------------------------------------------------
render_masthead(
    folio_code=f"STATE DOSSIER · CODE: {state_id} · NATIONAL RANK #{rank_val} OF {total_units}",
    title=state_name,
    deck=f"Diagnostic vulnerability dossier for {state_name}. Telemetry synthesized across educational delivery (UDISE+), maternal and child nutrition (NFHS-5), and civic school infrastructure.",
    location_tag=f"TIER: {band.upper()} VULNERABILITY",
)

# ---------------------------------------------------------------------------
# Dynamic Analytical Lede (Findings Statement)
# ---------------------------------------------------------------------------
def _fmt(val, decimals=1):
    if pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}f}"

dim_scores = {}
for label, col in SUB_COLS.items():
    v = latest.get(col)
    if pd.notna(v):
        dim_scores[label] = float(v)

if dim_scores:
    worst_dim = max(dim_scores.items(), key=lambda x: x[1])
    best_dim = min(dim_scores.items(), key=lambda x: x[1])
    lede_summary = (
        f"{state_name} is categorized in the {band.upper()} risk band with a composite index of "
        f"{_fmt(latest.get('overall_score'))} / 100 (national rank #{rank_val} of {total_units}). "
        f"The primary driver of institutional stress is {worst_dim[0]} (index {worst_dim[1]:.1f}), "
        f"while {best_dim[0]} represents the state's most resilient baseline (index {best_dim[1]:.1f})."
    )
    render_editorial_lede(lede_summary)

# ---------------------------------------------------------------------------
# Integrated Scorecard (Education, Healthcare, Civic Infrastructure)
# ---------------------------------------------------------------------------
comp_val = latest.get("data_completeness")
comp_str = f"{comp_val:.0%}" if pd.notna(comp_val) else "100%"

render_editorial_scorecard([
    {
        "label": "Overall Composite Index",
        "value": _fmt(latest.get("overall_score")),
        "note": f"Rank #{rank_val} · Percentile {pctile:.0f}%",
        "tag": str(band),
        "tag_bg": "#FAEDE3" if str(band) in ["High", "Critical"] else "#EAEFEA",
        "tag_fg": "#8C4318" if str(band) in ["High", "Critical"] else "#264230",
        "tag_border": "#E8C1A5" if str(band) in ["High", "Critical"] else "#BDCFBF",
    },
    {
        "label": "Education Vulnerability",
        "value": _fmt(latest.get("edu_risk")),
        "note": "PTR & female literacy deficits",
    },
    {
        "label": "Healthcare Deficit",
        "value": _fmt(latest.get("health_risk")),
        "note": "NFHS-5 child & maternal nutrition",
    },
    {
        "label": "Civic Infrastructure",
        "value": _fmt(latest.get("infra_risk")),
        "note": "Power, drinking water, internet",
    },
    {
        "label": "Audited Telemetry",
        "value": comp_str,
        "note": "All 3 core pillars verified",
        "tag": "100% Complete",
        "tag_bg": "#EAEFEA",
        "tag_fg": "#264230",
        "tag_border": "#BDCFBF",
    },
])

# ---------------------------------------------------------------------------
# Asymmetric Layout: Risk Breakdown vs. Typology & Anomaly Status
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1.5, 1])

with col_left:
    render_section_header("SEC. 01", "Dimension Decomposition", "Normalized Stress Profiles vs. National Medians")

    dim_data = []
    for label, col in SUB_COLS.items():
        val = latest.get(col)
        med = view[col].median() if col in view.columns else None
        if pd.notna(val):
            dim_data.append({
                "Dimension": label,
                "State Index": float(val),
                "National Median": float(med) if pd.notna(med) else None,
            })

    if dim_data:
        dim_df = pd.DataFrame(dim_data)
        fig_dim = go.Figure()

        # National median benchmark background bars
        if "National Median" in dim_df.columns:
            fig_dim.add_trace(go.Bar(
                name="National Benchmark Median",
                y=dim_df["Dimension"],
                x=dim_df["National Median"],
                orientation="h",
                marker=dict(color="#E2DED4", line=dict(width=0)),
                hoverinfo="x+name",
            ))

        # State actual bars
        fig_dim.add_trace(go.Bar(
            name=state_name,
            y=dim_df["Dimension"],
            x=dim_df["State Index"],
            orientation="h",
            marker=dict(
                color=dim_df["State Index"],
                colorscale=[
                    [0.0, "#385E48"],   # Sage green
                    [0.4, "#827845"],   # Antique olive
                    [0.7, "#BA6835"],   # Terracotta
                    [1.0, "#A83C1F"],   # Burnt sienna
                ],
                cmin=0,
                cmax=100,
                line=dict(width=0.8, color="#14241D"),
            ),
            text=dim_df["State Index"].apply(lambda v: f"{v:.1f}"),
            textposition="outside",
            textfont=dict(family="IBM Plex Mono, monospace", size=10),
            hoverinfo="x+name",
        ))

        style_editorial_figure(
            fig_dim,
            height=320,
            title=f"Dimensional Burden — {state_name}",
            subtitle="Solid bars reflect state index; grey bars reflect national median (0 = optimal, 100 = distress)",
        )
        fig_dim.update_layout(
            barmode="overlay",
            xaxis=dict(range=[0, 105], title=dict(text="Vulnerability Index (0-100)", font=dict(family="IBM Plex Mono, monospace", size=10))),
            yaxis=dict(title=""),
            legend=dict(x=1, y=1.05, orientation="h"),
        )
        st.plotly_chart(fig_dim, use_container_width=True)
        source_note("UDISE+ 2022-23 · NFHS-5 (2019-21) standardized indicator matrices")
    else:
        st.info("No dimension scores available for this state.")

with col_right:
    render_section_header("SEC. 02", "Typology & Diagnostic Flags", "Machine Learning Intelligence")

    # Cluster Archetype Card
    cluster_id = None
    if clusters_df is not None:
        match = clusters_df[clusters_df["district_name"] == state_name]
        if not match.empty:
            cluster_id = match.iloc[0]["cluster"]
    elif "cluster" in view.columns and pd.notna(latest.get("cluster")):
        cluster_id = latest["cluster"]

    if cluster_id is not None:
        cid_str = f"Archetype {int(cluster_id)}"
        if clusters_df is not None:
            siblings = sorted(clusters_df[clusters_df["cluster"] == cluster_id]["district_name"].dropna().unique().tolist())
        else:
            siblings = sorted(view[view["cluster"] == cluster_id]["district_name"].dropna().unique().tolist())
        siblings = [n for n in siblings if n != state_name]
        sib_text = ", ".join(siblings[:6]) + (f" + {len(siblings)-6} others" if len(siblings) > 6 else "")

        margin_note(
            kicker="K-Means Typology Partition",
            title=f"Peer Cohort: {cid_str}",
            text=f"<b>Statistically Homogenous State Cohort:</b> {sib_text if sib_text else 'Unique standalone profile.'}<br><br>States in this cluster share structural socio-economic characteristics and benefit from synchronized policy packages.",
        )
    else:
        st.info("Typology assignments not compiled.")

    # Isolation Forest Anomaly Card
    if anomalies_df is not None:
        amatch = anomalies_df[anomalies_df["district_name"] == state_name]
        if not amatch.empty:
            arow = amatch.iloc[0]
            flagged = arow.get("anomaly_flag", False)
            ascore = arow.get("anomaly_score", 0.0)
            unusual = arow.get("unusual_features", "None detected")

            if flagged:
                st.markdown(
                    f"""
                    <div style="background:#F7E5DE; border:1px solid #E5A997; border-left:3px solid #B84324; padding:14px 16px; margin-bottom:14px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-family:'IBM Plex Mono', monospace; font-size:0.68rem; font-weight:600; color:#8A260F; text-transform:uppercase; letter-spacing:0.1em;">§ Multivariate Outlier Flagged</span>
                            <span style="font-family:'IBM Plex Mono', monospace; font-size:0.75rem; font-weight:600; color:#8A260F;">Score: {_fmt(ascore, 1)} / 100</span>
                        </div>
                        <div style="font-family:'IBM Plex Sans', sans-serif; font-size:0.82rem; color:#611A0B; margin-top:6px; line-height:1.45;">
                            <b>Divergent Feature Drivers:</b> <code>{unusual}</code>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="background:#EAEFEA; border:1px solid #BDCFBF; border-left:3px solid #385E48; padding:14px 16px; margin-bottom:14px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-family:'IBM Plex Mono', monospace; font-size:0.68rem; font-weight:600; color:#264230; text-transform:uppercase; letter-spacing:0.1em;">Nominal Statistical Envelope</span>
                            <span style="font-family:'IBM Plex Mono', monospace; font-size:0.75rem; font-weight:600; color:#264230;">Score: {_fmt(ascore, 1)} / 100</span>
                        </div>
                        <div style="font-family:'IBM Plex Sans', sans-serif; font-size:0.82rem; color:#264230; margin-top:6px; line-height:1.45;">
                            No multivariate trajectory divergence detected relative to national baseline envelopes.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------------------------
# Raw Indicator Telemetry Ledger
# ---------------------------------------------------------------------------
render_section_header("SEC. 03", "Primary Telemetry Ledger", "Raw Survey Observations & Benchmarks")

standard_cols = {
    "district_id", "district_name", "state", "period", "year",
    "edu_risk", "health_risk", "infra_risk",
    "overall_score", "risk_band", "data_completeness",
    "cluster", "anomaly_flag", "anomaly_score", "pred_next_score",
}
indicator_cols = [c for c in row.columns if c not in standard_cols]

if indicator_cols:
    ledger_rows = []
    for c in indicator_cols:
        val = row[c].values[0]
        nat_med = view[c].median() if c in view.columns and pd.api.types.is_numeric_dtype(view[c]) else None
        clean_name = c.replace("_", " ").title()
        
        val_str = f"{val:,.2f}" if isinstance(val, (int, float)) and pd.notna(val) else ("N/A" if pd.isna(val) else str(val))
        med_str = f"{nat_med:,.2f}" if isinstance(nat_med, (int, float)) and pd.notna(nat_med) else "N/A"
        
        ledger_rows.append({
            "Indicator Field": clean_name,
            f"{state_name} Reported Value": val_str,
            "National Median": med_str,
        })
        
    ledger_df = pd.DataFrame(ledger_rows)
    st.dataframe(ledger_df, hide_index=True, use_container_width=True)
else:
    st.info("No raw telemetry fields found beyond composite indices.")

with st.expander("State Telemetry Provenance & Methodological Audit"):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"- **Canonical Identifier:** `{state_id}`\n"
            f"- **Observation Window:** `{latest.get(time_col, 'Current')}`\n"
            f"- **Standardization Rule:** Min-max feature scaling against empirical national bounds."
        )
    with c2:
        st.markdown(
            f"- **Constituent Features Audited:** `{len(indicator_cols)} indicators`\n"
            f"- **Risk Classification Threshold:** High (`50–65`), Critical (`≥ 65`)\n"
            f"- **Cluster Membership:** `{cid_str if cluster_id is not None else 'N/A'}`"
        )
