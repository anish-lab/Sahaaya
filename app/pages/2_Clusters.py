"""
SAHAAYA — Cluster Analysis Page.

Visualises clustering results: cluster profiles, membership tables,
PCA-based scatter projection, and auto-generated cluster descriptions.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Clusters", page_icon="\U0001f4ca", layout="wide")

from utils import (  # noqa: E402
    load_features,
    load_clusters,
    load_profiles,
    is_mock_data,
    SUB_COLS,
    BAND_COLORS,
)

# ---------------------------------------------------------------------------
st.title("Cluster Analysis")
st.caption(
    "Districts are grouped into clusters based on similarity across "
    "risk dimensions.  Explore cluster composition and characteristics below."
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
clusters_df = load_clusters()
profiles_df = load_profiles()
features_df = load_features()

if clusters_df is None and (features_df is None or "cluster" not in features_df.columns):
    st.error(
        "**Cluster data not available.**  "
        "Run the clustering step of the pipeline to generate "
        "`cluster_assignments.parquet`."
    )
    st.stop()

if features_df is not None and is_mock_data(features_df):
    st.warning("\u26a0\ufe0f  Mock / synthetic data detected.  Results are illustrative only.")

# ---------------------------------------------------------------------------
# Resolve cluster column — prefer cluster_assignments, fall back to features
# ---------------------------------------------------------------------------
if clusters_df is not None and features_df is not None:
    # Merge cluster into features if not already there
    if "cluster" not in features_df.columns:
        merged = features_df.merge(
            clusters_df[["district_name", "cluster"]],
            on="district_name",
            how="left",
        )
    else:
        merged = features_df.copy()
else:
    merged = features_df.copy() if features_df is not None else clusters_df.copy()

# Pick latest period
time_col = "period" if "period" in merged.columns else ("year" if "year" in merged.columns else None)
if time_col and merged[time_col].nunique() > 1:
    latest_period = merged[time_col].dropna().max()
    view = merged[merged[time_col] == latest_period].copy()
else:
    view = merged.copy()

if "cluster" not in view.columns:
    st.error("No `cluster` column found after merging data.")
    st.stop()

view = view.dropna(subset=["cluster"])
view["cluster"] = view["cluster"].astype(int)

# ---------------------------------------------------------------------------
# Overview KPIs
# ---------------------------------------------------------------------------
n_clusters = view["cluster"].nunique()
cluster_sizes = view.groupby("cluster").size().reset_index(name="size")

c1, c2, c3 = st.columns(3)
c1.metric("Number of clusters", n_clusters)
c2.metric("Largest cluster size", int(cluster_sizes["size"].max()))
c3.metric("Smallest cluster size", int(cluster_sizes["size"].min()))

st.divider()

# ---------------------------------------------------------------------------
# Cluster profile comparison
# ---------------------------------------------------------------------------
st.subheader("Cluster risk profiles")

dim_cols = [c for c in SUB_COLS.values() if c in view.columns]

if dim_cols:
    profile_data = view.groupby("cluster")[dim_cols].mean().reset_index()
    profile_long = profile_data.melt(
        id_vars="cluster",
        value_vars=dim_cols,
        var_name="Dimension",
        value_name="Mean score",
    )
    # Readable labels
    reverse_map = {v: k for k, v in SUB_COLS.items()}
    profile_long["Dimension"] = profile_long["Dimension"].map(reverse_map).fillna(profile_long["Dimension"])
    profile_long["cluster"] = profile_long["cluster"].astype(str)

    tab_bar, tab_heat = st.tabs(["Grouped bar chart", "Heatmap"])

    with tab_bar:
        fig = px.bar(
            profile_long,
            x="Dimension",
            y="Mean score",
            color="cluster",
            barmode="group",
            range_y=[0, 100],
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={"cluster": "Cluster"},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with tab_heat:
        heat_pivot = profile_long.pivot(
            index="cluster", columns="Dimension", values="Mean score"
        )
        fig_heat = px.imshow(
            heat_pivot.values,
            x=heat_pivot.columns.tolist(),
            y=[f"Cluster {c}" for c in heat_pivot.index],
            color_continuous_scale="YlOrRd",
            zmin=0,
            zmax=100,
            aspect="auto",
            labels=dict(color="Mean score"),
        )
        fig_heat.update_layout(height=350)
        st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Dimension score columns not found in the data.")

st.divider()

# ---------------------------------------------------------------------------
# Cluster membership table
# ---------------------------------------------------------------------------
st.subheader("Cluster membership")

if profiles_df is not None and "districts" in profiles_df.columns:
    for _, prow in profiles_df.sort_values("cluster").iterrows():
        cid = prow["cluster"]
        csize = prow.get("size", "?")
        with st.expander(f"Cluster {cid}  ({csize} districts)"):
            dlist = str(prow["districts"]).split(",")
            st.write(", ".join(d.strip() for d in dlist))
else:
    for cid in sorted(view["cluster"].unique()):
        members = sorted(view[view["cluster"] == cid]["district_name"].dropna().unique())
        with st.expander(f"Cluster {cid}  ({len(members)} districts)"):
            st.write(", ".join(members))

st.divider()

# ---------------------------------------------------------------------------
# PCA scatter plot
# ---------------------------------------------------------------------------
st.subheader("Cluster scatter (PCA projection)")

if dim_cols and len(dim_cols) >= 2:
    from sklearn.decomposition import PCA  # lazy import

    pca_input = view[dim_cols].fillna(view[dim_cols].mean())
    n_components = min(2, len(dim_cols))

    try:
        pca = PCA(n_components=n_components, random_state=42)
        coords = pca.fit_transform(pca_input)

        scatter_df = pd.DataFrame(
            coords, columns=[f"PC{i+1}" for i in range(n_components)], index=view.index
        )
        scatter_df["Cluster"] = view["cluster"].astype(str).values
        scatter_df["District"] = view["district_name"].values

        fig_scatter = px.scatter(
            scatter_df,
            x="PC1",
            y="PC2" if n_components >= 2 else "PC1",
            color="Cluster",
            hover_data=["District"],
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)

        explained = pca.explained_variance_ratio_
        st.caption(
            f"PC1 explains {explained[0]:.0%}"
            + (f", PC2 explains {explained[1]:.0%}" if len(explained) > 1 else "")
            + " of variance in dimension scores."
        )
    except Exception as exc:
        st.warning(f"PCA projection failed: {exc}")
else:
    st.info("Need at least 2 dimension-score columns for PCA projection.")

st.divider()

# ---------------------------------------------------------------------------
# Cluster descriptions (auto-generated)
# ---------------------------------------------------------------------------
st.subheader("Cluster characteristics")

if dim_cols:
    profile_data = view.groupby("cluster")[dim_cols].mean()
    reverse_map = {v: k for k, v in SUB_COLS.items()}

    for cid in sorted(profile_data.index):
        row = profile_data.loc[cid]
        highest = row.idxmax()
        lowest = row.idxmin()
        members = sorted(view[view["cluster"] == cid]["district_name"].dropna().unique())

        st.markdown(f"**Cluster {cid}** ({len(members)} districts)")
        bullets = [
            f"- Highest average risk: **{reverse_map.get(highest, highest)}** ({row[highest]:.1f})",
            f"- Lowest average risk: **{reverse_map.get(lowest, lowest)}** ({row[lowest]:.1f})",
            f"- Overall mean: **{row.mean():.1f}**",
        ]
        st.markdown("\n".join(bullets))
else:
    st.info("Cannot generate descriptions without dimension scores.")
