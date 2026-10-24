"""
SAHAAYA — Cluster Analysis Page.

Visualises clustering results: cluster profiles, membership tables,
PCA-based scatter projection, and auto-generated cluster descriptions.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Risk Clusters — SAHAAYA",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils import (  # noqa: E402
    load_features,
    load_clusters,
    load_profiles,
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
    render_sidebar_brand,
    style_plotly_fig,
)

# ---------------------------------------------------------------------------
# Theme & Top Navigation
# ---------------------------------------------------------------------------
inject_custom_theme()
render_topbar(current_page="Risk Clusters")

render_hero(
    tag="UNSUPERVISED ML TYPOLOGIES",
    title="Socio-Economic Cluster Intelligence",
    description="Algorithmic clustering (K-Means with Silhouette Optimization) grouping districts into structurally homogenous profiles based on shared education, health, and infrastructure dynamics.",
)

render_sidebar_brand(get_data_status())

# ---------------------------------------------------------------------------
# Load data & Fallbacks
# ---------------------------------------------------------------------------
clusters_df = load_clusters()
profiles_df = load_profiles()
features_df = load_features()

if clusters_df is None and (features_df is None or "cluster" not in features_df.columns):
    st.error(
        "**Cluster data not found.** "
        "Run `python src/models/cluster.py` to generate cluster profiles."
    )
    st.stop()

if features_df is not None and is_mock_data(features_df):
    st.warning("⚠️ Mock / synthetic data detected. Results are illustrative only.")

# Merge cluster into features if needed
if clusters_df is not None and features_df is not None:
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

time_col = "period" if "period" in merged.columns else ("year" if "year" in merged.columns else None)
if time_col and merged[time_col].nunique() > 1:
    latest_period = merged[time_col].dropna().max()
    view = merged[merged[time_col] == latest_period].copy()
else:
    view = merged.copy()

if "cluster" not in view.columns:
    st.error("No `cluster` column found in data.")
    st.stop()

view = view.dropna(subset=["cluster"])
view["cluster"] = view["cluster"].astype(int)

# ---------------------------------------------------------------------------
# Overview KPIs
# ---------------------------------------------------------------------------
n_clusters = view["cluster"].nunique()
cluster_sizes = view.groupby("cluster").size().reset_index(name="size")

k1, k2, k3, k4 = st.columns(4)

with k1:
    render_kpi("Distinct Typologies", n_clusters, icon="🔮", color_accent="#4f46e5", subtitle="K-Means optimal partitions")
with k2:
    render_kpi("Largest Cluster", f"{int(cluster_sizes['size'].max())} dists", icon="🏛️", color_accent="#06b6d4", subtitle="Dominant profile size")
with k3:
    render_kpi("Smallest Cluster", f"{int(cluster_sizes['size'].min())} dists", icon="🎯", color_accent="#8b5cf6", subtitle="Specialized archetype")
with k4:
    render_kpi("Clustering Features", len([c for c in SUB_COLS.values() if c in view.columns and view[c].notna().any()]), icon="📐", color_accent="#10b981", subtitle="Risk dimensions modeled")

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Dimension Profiles Tab (Grouped Bar & Heatmap)
# ---------------------------------------------------------------------------
st.markdown(
    "<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.25rem; color:#0f172a; margin-bottom:8px;'>"
    "📊 Comparative Risk Archetypes"
    "</div>",
    unsafe_allow_html=True,
)

dim_cols = [c for c in SUB_COLS.values() if c in view.columns and view[c].notna().any()]

if dim_cols:
    profile_data = view.groupby("cluster")[dim_cols].mean().reset_index()
    profile_long = profile_data.melt(
        id_vars="cluster",
        value_vars=dim_cols,
        var_name="Dimension",
        value_name="Mean Score",
    )
    reverse_map = {v: k for k, v in SUB_COLS.items()}
    profile_long["Dimension"] = profile_long["Dimension"].map(reverse_map).fillna(profile_long["Dimension"])
    profile_long["cluster"] = "Cluster " + profile_long["cluster"].astype(str)

    tab_bar, tab_heat = st.tabs(["📊 Grouped Dimension Profiles", "🔥 Risk Density Matrix (Heatmap)"])

    with tab_bar:
        fig_bar = px.bar(
            profile_long,
            x="Dimension",
            y="Mean Score",
            color="cluster",
            barmode="group",
            range_y=[0, 100],
            color_discrete_sequence=["#4f46e5", "#06b6d4", "#f59e0b", "#ec4899"],
            labels={"cluster": "Archetype", "Mean Score": "Mean Risk (0-100)"},
        )
        style_plotly_fig(fig_bar, height=380, title="Cross-Dimension Vulnerability Benchmark")
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab_heat:
        heat_pivot = profile_long.pivot(
            index="cluster", columns="Dimension", values="Mean Score"
        )
        fig_heat = px.imshow(
            heat_pivot.values,
            x=heat_pivot.columns.tolist(),
            y=heat_pivot.index.tolist(),
            color_continuous_scale="YlOrRd",
            zmin=0,
            zmax=100,
            aspect="auto",
            labels=dict(color="Mean Risk"),
        )
        style_plotly_fig(fig_heat, height=320, title="Cluster Intensity Heatmap")
        st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("No dimension score columns found in data.")

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PCA 2D Spatial Scatter
# ---------------------------------------------------------------------------
col_pca, col_members = st.columns([1.2, 1])

with col_pca:
    st.markdown(
        "<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.15rem; color:#0f172a; margin-bottom:10px;'>"
        "🌐 PCA Latent Space Projection"
        "</div>",
        unsafe_allow_html=True,
    )

    if dim_cols and len(dim_cols) >= 2:
        from sklearn.decomposition import PCA

        pca_input = view[dim_cols].fillna(view[dim_cols].mean()).fillna(0.0)
        n_components = min(2, len(dim_cols))
        try:
            pca = PCA(n_components=n_components, random_state=42)
            coords = pca.fit_transform(pca_input)

            scatter_df = pd.DataFrame(
                coords, columns=[f"PC{i+1}" for i in range(n_components)], index=view.index
            )
            scatter_df["Cluster"] = "Cluster " + view["cluster"].astype(str)
            scatter_df["District"] = view["district_name"].values

            fig_scatter = px.scatter(
                scatter_df,
                x="PC1",
                y="PC2" if n_components >= 2 else "PC1",
                color="Cluster",
                hover_name="District",
                hover_data={"Cluster": True, "PC1": ":.2f", "PC2": ":.2f"},
                color_discrete_sequence=["#4f46e5", "#06b6d4", "#f59e0b", "#ec4899"],
            )
            fig_scatter.update_traces(marker=dict(size=11, opacity=0.85, line=dict(width=1, color="#ffffff")))
            style_plotly_fig(fig_scatter, height=420)
            st.plotly_chart(fig_scatter, use_container_width=True)

            explained = pca.explained_variance_ratio_
            st.caption(
                f"Principal Components capture {explained[0]:.1%}"
                + (f" (PC1) and {explained[1]:.1%} (PC2)" if len(explained) > 1 else "")
                + " of overall variance."
            )
        except Exception as exc:
            st.warning(f"PCA projection: {exc}")
    else:
        st.info("At least 2 dimensions needed for PCA projection.")

with col_members:
    st.markdown(
        "<div style='font-family:Outfit,sans-serif; font-weight:700; font-size:1.15rem; color:#0f172a; margin-bottom:10px;'>"
        "🏛️ Constituent Districts by Cluster"
        "</div>",
        unsafe_allow_html=True,
    )

    for cid in sorted(view["cluster"].unique()):
        members = sorted(view[view["cluster"] == cid]["district_name"].dropna().unique())
        c_badge = f"<span style='background:#e0e7ff; color:#3730a3; padding:2px 8px; border-radius:6px; font-weight:700; font-size:0.75rem;'>{len(members)} districts</span>"

        with st.expander(f"Cluster {cid} ({len(members)} districts)", expanded=(cid == 0)):
            pills = "".join(
                f"<span style='display:inline-block; background:#f1f5f9; color:#1e293b; padding:4px 10px; margin:3px 4px; border-radius:8px; font-size:0.8rem; font-weight:600; border:1px solid #e2e8f0;'>{m}</span>"
                for m in members
            )
            st.markdown(f"<div style='line-height:2;'>{pills}</div>", unsafe_allow_html=True)
