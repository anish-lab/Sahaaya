"""
SAHAAYA — Cluster Analysis Page.

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
    page_title="Risk Typologies — SAHAAYA",
    page_icon="§",
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
    render_masthead,
    render_section_header,
    render_editorial_scorecard,
    render_sidebar_masthead,
    style_editorial_figure,
)

# ---------------------------------------------------------------------------
# Theme & Masthead
# ---------------------------------------------------------------------------
inject_custom_theme()
render_sidebar_masthead(get_data_status())

render_masthead(
    folio_code="ANALYTICAL MEMORANDUM · STATISTICAL TYPOLOGIES",
    title="Socio-Economic Risk Archetypes & Cluster Profiles",
    deck="Unsupervised partition modeling (K-Means with Silhouette Optimization) segmenting districts into structurally homogenous peer groups to support tailored policy interventions and regional benchmarking.",
    location_tag="UNSUPERVISED PARTITION ANALYSIS",
)

# ---------------------------------------------------------------------------
# Load data & Fallbacks
# ---------------------------------------------------------------------------
clusters_df = load_clusters()
profiles_df = load_profiles()
features_df = load_features()

if clusters_df is None and (features_df is None or "cluster" not in features_df.columns):
    st.error("Cluster assignment store not located. Run `python src/models/cluster.py` to generate.")
    st.stop()

if features_df is not None and is_mock_data(features_df):
    st.warning("Notice: Synthetic test dataset active. Figures reflect simulated distributions.")

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
    st.error("Column 'cluster' not located in processed data.")
    st.stop()

view = view.dropna(subset=["cluster"])
view["cluster"] = view["cluster"].astype(int)

# ---------------------------------------------------------------------------
# Overview Scorecard
# ---------------------------------------------------------------------------
n_clusters = view["cluster"].nunique()
cluster_sizes = view.groupby("cluster").size().reset_index(name="size")
dim_cols = [c for c in SUB_COLS.values() if c in view.columns and view[c].notna().any()]

render_editorial_scorecard([
    {
        "label": "Optimal Archetypes (k)",
        "value": str(n_clusters),
        "note": "Evaluated via silhouette coefficient optimization",
        "tag": "Silhouette Peak",
        "tag_bg": "#EAEFEA",
        "tag_fg": "#264230",
        "tag_border": "#BDCFBF",
    },
    {
        "label": "Dominant Archetype Size",
        "value": f"{int(cluster_sizes['size'].max())} dists",
        "note": "Modal socio-economic vulnerability pattern",
    },
    {
        "label": "Specialized Archetype Size",
        "value": f"{int(cluster_sizes['size'].min())} dists",
        "note": "Minority structural vulnerability profile",
    },
    {
        "label": "Active Model Dimensions",
        "value": f"{len(dim_cols)} of 4",
        "note": "Features with verified non-null telemetry",
        "tag": "Audited",
        "tag_bg": "#EFECE4",
        "tag_fg": "#444A43",
        "tag_border": "#D5D0C5",
    },
])

# ---------------------------------------------------------------------------
# Dimension Profiles Tab (Grouped Bar & Heatmap)
# ---------------------------------------------------------------------------
render_section_header("SEC. 01", "Cross-Dimension Typology Profiles", "Comparative Risk Archetypes")

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
    profile_long["cluster"] = "Archetype " + profile_long["cluster"].astype(str)

    tab_bar, tab_heat = st.tabs(["Grouped Dimensional Profile", "Risk Density Heatmap"])

    with tab_bar:
        fig_bar = px.bar(
            profile_long,
            x="Dimension",
            y="Mean Score",
            color="cluster",
            barmode="group",
            range_y=[0, 100],
            color_discrete_sequence=["#1E3A2B", "#B84324", "#827845", "#556B5D"],
            labels={"cluster": "Archetype", "Mean Score": "Mean Risk Score (0-100)"},
        )
        fig_bar.update_traces(marker=dict(line=dict(width=0.8, color="#14241D")))
        style_editorial_figure(
            fig_bar,
            height=360,
            title="Archetype Signature Comparison",
            subtitle="Mean normalized vulnerability index across core pillars",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab_heat:
        heat_pivot = profile_long.pivot(
            index="cluster", columns="Dimension", values="Mean Score"
        )
        fig_heat = px.imshow(
            heat_pivot.values,
            x=heat_pivot.columns.tolist(),
            y=heat_pivot.index.tolist(),
            color_continuous_scale=[
                [0.0, "#EAE5D9"],
                [0.4, "#BDCBB9"],
                [0.7, "#C87C47"],
                [1.0, "#A83C1F"],
            ],
            zmin=0,
            zmax=100,
            aspect="auto",
            labels=dict(color="Mean Index"),
        )
        style_editorial_figure(
            fig_heat,
            height=280,
            title="Typology Intensity Matrix",
            subtitle="Dimensional stress density across clusters",
        )
        st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("No dimension score columns located in dataset.")

# ---------------------------------------------------------------------------
# Latent Space Projection & Membership Ledger
# ---------------------------------------------------------------------------
col_pca, col_members = st.columns([1.3, 1])

with col_pca:
    render_section_header("SEC. 02", "Latent Space Projection", "Principal Component Analysis")

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
            scatter_df["Cluster"] = "Archetype " + view["cluster"].astype(str)
            scatter_df["District"] = view["district_name"].values

            fig_scatter = px.scatter(
                scatter_df,
                x="PC1",
                y="PC2" if n_components >= 2 else "PC1",
                color="Cluster",
                hover_name="District",
                hover_data={"Cluster": True, "PC1": ":.2f", "PC2": ":.2f"},
                color_discrete_sequence=["#1E3A2B", "#B84324", "#827845", "#556B5D"],
            )
            fig_scatter.update_traces(
                marker=dict(size=9, opacity=0.9, line=dict(width=0.8, color="#14241D"))
            )
            style_editorial_figure(
                fig_scatter,
                height=380,
                title="PCA Coordinate Mapping",
                subtitle="Orthogonal linear projection of multi-dimensional profiles",
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

            explained = pca.explained_variance_ratio_
            st.caption(
                f"Principal Components capture {explained[0]:.1%} (PC1)"
                + (f" and {explained[1]:.1%} (PC2)" if len(explained) > 1 else "")
                + " of cumulative variance across input indicators."
            )
        except Exception as exc:
            st.warning(f"PCA projection: {exc}")
    else:
        st.info("At least two valid dimensions required for latent space projection.")

with col_members:
    render_section_header("SEC. 03", "Jurisdiction Roster", "Constituent Districts by Archetype")

    for cid in sorted(view["cluster"].unique()):
        members = sorted(view[view["cluster"] == cid]["district_name"].dropna().unique())
        with st.expander(f"Archetype {cid} — {len(members)} Jurisdictions", expanded=(cid == 0)):
            items_str = ", ".join(members)
            st.markdown(
                f"""
                <div style="font-family:'IBM Plex Sans'; font-size:0.84rem; line-height:1.6; color:#2C312E; padding:8px 0;">
                    {items_str}
                </div>
                """,
                unsafe_allow_html=True,
            )
