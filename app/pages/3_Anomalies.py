"""
SAHAAYA — Anomaly Detection Results Page.

Displays districts flagged as anomalous by the pipeline, their anomaly scores,
unusual features, and comparison against district averages.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Anomalies", page_icon="\U0001f50d", layout="wide")

from utils import (  # noqa: E402
    load_features,
    load_anomalies,
    is_mock_data,
    SUB_COLS,
)

# ---------------------------------------------------------------------------
st.title("Anomaly Detection Results")
st.caption(
    "Districts whose indicator patterns differ significantly from "
    "their peers are flagged for further investigation."
)

st.info(
    "\U0001f4a1 **Caveat:** Anomalies indicate unusual patterns \u2014 "
    "they are prompts for investigation, not proof of distress."
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
anomalies_df = load_anomalies()
features_df = load_features()

if anomalies_df is None:
    st.error(
        "**Anomaly results not available.**  "
        "Run the anomaly-detection step of the pipeline to generate "
        "`anomaly_results.parquet`."
    )
    st.stop()

if features_df is not None and is_mock_data(features_df):
    st.warning("\u26a0\ufe0f  Mock / synthetic data detected.  Results are illustrative only.")

# ---------------------------------------------------------------------------
# Summary KPIs
# ---------------------------------------------------------------------------
total = len(anomalies_df)
flagged_df = anomalies_df[anomalies_df["anomaly_flag"] == True]  # noqa: E712
n_flagged = len(flagged_df)
pct_flagged = n_flagged / total * 100 if total > 0 else 0
avg_score = anomalies_df["anomaly_score"].mean() if "anomaly_score" in anomalies_df.columns else None

k1, k2, k3 = st.columns(3)
k1.metric("Districts flagged", n_flagged)
k2.metric("Flagged percentage", f"{pct_flagged:.1f}%")
k3.metric(
    "Avg anomaly score",
    f"{avg_score:.2f}" if pd.notna(avg_score) else "N/A",
)

st.divider()

# ---------------------------------------------------------------------------
# Flagged districts table
# ---------------------------------------------------------------------------
st.subheader("Flagged districts")

if n_flagged == 0:
    st.success("No districts were flagged as anomalous.")
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
            "anomaly_score": "Anomaly Score",
            "unusual_features": "Unusual Features",
        },
        inplace=True,
    )
    if "Anomaly Score" in show.columns:
        show.sort_values("Anomaly Score", ascending=False, inplace=True)
        show["Anomaly Score"] = show["Anomaly Score"].round(3)

    st.dataframe(show, hide_index=True, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Anomaly score distribution
# ---------------------------------------------------------------------------
if "anomaly_score" in anomalies_df.columns:
    st.subheader("Anomaly score distribution")
    fig_hist = px.histogram(
        anomalies_df,
        x="anomaly_score",
        nbins=30,
        color_discrete_sequence=["#e67e22"],
        labels={"anomaly_score": "Anomaly Score"},
    )
    fig_hist.update_layout(
        height=350,
        xaxis_title="Anomaly Score",
        yaxis_title="Count",
        bargap=0.05,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.divider()

# ---------------------------------------------------------------------------
# Detailed comparison for a selected anomaly
# ---------------------------------------------------------------------------
if n_flagged > 0 and features_df is not None:
    st.subheader("Detailed indicator comparison")

    selected = st.selectbox(
        "Select a flagged district",
        sorted(flagged_df["district_name"].dropna().unique()),
    )

    # Use latest period
    time_col = "period" if "period" in features_df.columns else ("year" if "year" in features_df.columns else None)
    if time_col and features_df[time_col].nunique() > 1:
        latest_period = features_df[time_col].dropna().max()
        fview = features_df[features_df[time_col] == latest_period].copy()
    else:
        fview = features_df.copy()

    district_row = fview[fview["district_name"] == selected]

    if not district_row.empty:
        dim_cols = [c for c in SUB_COLS.values() if c in fview.columns]
        if dim_cols:
            district_vals = district_row.iloc[0][dim_cols]
            mean_vals = fview[dim_cols].mean()

            reverse_map = {v: k for k, v in SUB_COLS.items()}
            comp = pd.DataFrame(
                {
                    "Dimension": [reverse_map.get(c, c) for c in dim_cols],
                    "District": [
                        round(v, 1) if pd.notna(v) else None
                        for v in district_vals
                    ],
                    "State Average": [round(v, 1) for v in mean_vals],
                }
            )

            comp_long = comp.melt(
                id_vars="Dimension",
                value_vars=["District", "State Average"],
                var_name="Type",
                value_name="Score",
            )

            fig_comp = px.bar(
                comp_long,
                x="Dimension",
                y="Score",
                color="Type",
                barmode="group",
                range_y=[0, 100],
                color_discrete_map={
                    "District": "#e74c3c",
                    "State Average": "#3498db",
                },
            )
            fig_comp.update_layout(height=400)
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Dimension score columns not found for comparison.")

        # Show unusual features detail
        amatch = anomalies_df[anomalies_df["district_name"] == selected]
        if not amatch.empty:
            unusual = amatch.iloc[0].get("unusual_features", "")
            if pd.notna(unusual) and str(unusual).strip():
                st.markdown(f"**Unusual features:** {unusual}")
    else:
        st.warning(f"No feature data found for {selected} in the latest period.")
