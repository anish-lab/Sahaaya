"""
SAHAAYA — District Detail Drill-Down.

Shows a single district's risk profile: dimension scores, cluster membership,
anomaly flags, raw source indicators, and data provenance.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="District Detail", page_icon="\U0001f4cd", layout="wide")

from utils import (  # noqa: E402
    load_features,
    load_clusters,
    load_anomalies,
    is_mock_data,
    SUB_COLS,
    BAND_COLORS,
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = load_features()

if df is None:
    st.error("**features.parquet not found.**  Run the pipeline first.")
    st.stop()

if is_mock_data(df):
    st.warning(
        "\u26a0\ufe0f  Mock / synthetic data detected.  "
        "Results are illustrative only."
    )

clusters_df = load_clusters()
anomalies_df = load_anomalies()

# ---------------------------------------------------------------------------
# Period handling — pick the latest period per district
# ---------------------------------------------------------------------------
time_col = "period" if "period" in df.columns else ("year" if "year" in df.columns else None)

if time_col:
    latest_period = df[time_col].dropna().max()
    view = df[df[time_col] == latest_period].copy()
else:
    view = df.copy()

# ---------------------------------------------------------------------------
# District selector
# ---------------------------------------------------------------------------
districts = sorted(view["district_name"].dropna().unique())
if not districts:
    st.error("No district names found in the data.")
    st.stop()

district = st.sidebar.selectbox("Select district", districts)
row = view[view["district_name"] == district]

if row.empty:
    st.error(f"No data found for **{district}**.")
    st.stop()

latest = row.iloc[0]

# ---------------------------------------------------------------------------
# Header with risk-band badge
# ---------------------------------------------------------------------------
band = latest.get("risk_band", None)
band_color = BAND_COLORS.get(str(band), "#888")
badge = (
    f'<span style="background:{band_color};color:#fff;padding:4px 12px;'
    f'border-radius:8px;font-weight:600">{band}</span>'
    if pd.notna(band)
    else ""
)
st.markdown(f"## {district}  {badge}", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
def _fmt(val, decimals=1):
    """Format a numeric value, returning 'N/A' for NaN."""
    if pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}f}"


cols = st.columns(6)
cols[0].metric("Overall score", _fmt(latest.get("overall_score")))
cols[1].metric("Education", _fmt(latest.get("edu_risk")))
cols[2].metric("Health", _fmt(latest.get("health_risk")))
cols[3].metric("Employment", _fmt(latest.get("emp_risk")))
cols[4].metric("Infrastructure", _fmt(latest.get("infra_risk")))
completeness = latest.get("data_completeness")
cols[5].metric(
    "Data completeness",
    f"{completeness:.0%}" if pd.notna(completeness) else "N/A",
)

st.divider()

# ---------------------------------------------------------------------------
# Dimension scores chart  +  Cluster info
# ---------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Dimension risk scores")
    dim_data = []
    for label, col in SUB_COLS.items():
        val = latest.get(col)
        if pd.notna(val):
            dim_data.append({"Dimension": label, "Score": float(val)})
    if dim_data:
        dim_df = pd.DataFrame(dim_data)
        fig = px.bar(
            dim_df,
            x="Score",
            y="Dimension",
            orientation="h",
            range_x=[0, 100],
            color="Score",
            color_continuous_scale="YlOrRd",
        )
        fig.update_layout(
            coloraxis_showscale=False,
            xaxis_title="Risk (higher = worse)",
            yaxis_title="",
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No dimension scores available for this district.")

with right:
    st.subheader("Cluster membership")
    if clusters_df is not None:
        match = clusters_df[clusters_df["district_name"] == district]
        if not match.empty:
            cluster_id = match.iloc[0]["cluster"]
            st.metric("Cluster", int(cluster_id) if pd.notna(cluster_id) else "N/A")

            # Similar districts in same cluster
            siblings = clusters_df[clusters_df["cluster"] == cluster_id]
            sibling_names = sorted(
                siblings["district_name"].dropna().unique().tolist()
            )
            sibling_names = [n for n in sibling_names if n != district]
            if sibling_names:
                st.markdown("**Similar districts (same cluster):**")
                st.write(", ".join(sibling_names))
            else:
                st.caption("No other districts share this cluster.")
        else:
            st.info("This district is not present in cluster assignments.")
    elif "cluster" in view.columns and pd.notna(latest.get("cluster")):
        cluster_id = latest["cluster"]
        st.metric("Cluster", int(cluster_id))
        siblings = view[view["cluster"] == cluster_id]
        sibling_names = sorted(
            siblings["district_name"].dropna().unique().tolist()
        )
        sibling_names = [n for n in sibling_names if n != district]
        if sibling_names:
            st.markdown("**Similar districts (same cluster):**")
            st.write(", ".join(sibling_names))
    else:
        st.info("Cluster data not available. Run the clustering pipeline.")

# ---------------------------------------------------------------------------
# Anomaly section
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Anomaly status")

anomaly_shown = False
if anomalies_df is not None:
    amatch = anomalies_df[anomalies_df["district_name"] == district]
    if not amatch.empty:
        arow = amatch.iloc[0]
        flagged = arow.get("anomaly_flag", False)
        if flagged:
            st.warning(
                f"\u26a0\ufe0f  **{district}** is flagged as anomalous "
                f"(anomaly score: {_fmt(arow.get('anomaly_score'))})."
            )
            unusual = arow.get("unusual_features", "")
            if pd.notna(unusual) and str(unusual).strip():
                st.markdown(f"**Unusual features:** {unusual}")
            anomaly_shown = True
        else:
            st.success(
                f"**{district}** is not flagged as anomalous "
                f"(score: {_fmt(arow.get('anomaly_score'))})."
            )
            anomaly_shown = True

if not anomaly_shown:
    st.info("Anomaly data not available.  Run the anomaly-detection pipeline.")

# ---------------------------------------------------------------------------
# Raw indicators table
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Source indicators")

standard_cols = {
    "district_id", "district_name", "state", "period", "year",
    "edu_risk", "health_risk", "emp_risk", "infra_risk",
    "overall_score", "risk_band", "data_completeness",
    "cluster", "anomaly_flag", "anomaly_score", "pred_next_score",
}
indicator_cols = [c for c in row.columns if c not in standard_cols]

if indicator_cols:
    indicator_data = row[indicator_cols].T.copy()
    indicator_data.columns = ["Value"]
    indicator_data.index.name = "Indicator"
    indicator_data["Value"] = indicator_data["Value"].apply(
        lambda v: round(v, 2) if isinstance(v, (int, float)) and pd.notna(v) else ("N/A" if pd.isna(v) else v)
    )
    st.dataframe(indicator_data, use_container_width=True)
else:
    st.info("No additional source indicators found beyond the risk scores.")

# ---------------------------------------------------------------------------
# Data provenance
# ---------------------------------------------------------------------------
with st.expander("Data provenance"):
    if time_col and pd.notna(latest.get(time_col)):
        st.markdown(f"**Reporting period:** {latest[time_col]}")
    st.markdown(f"**District ID:** {latest.get('district_id', 'N/A')}")
    if indicator_cols:
        st.markdown(
            f"**Source columns ({len(indicator_cols)}):** "
            + ", ".join(f"`{c}`" for c in indicator_cols)
        )
    st.caption(
        "Dimension scores (edu_risk, health_risk, etc.) are composite indices "
        "derived from the source indicators above.  See the pipeline documentation "
        "for methodology."
    )
