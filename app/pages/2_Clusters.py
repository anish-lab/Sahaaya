"""
SAHAAYA — Unsupervised Risk Typologies & Cluster Profiles.

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
    render_editorial_lede,
    render_section_header,
    render_editorial_scorecard,
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

render_masthead(
    folio_code="ANALYTICAL MEMORANDUM · STATISTICAL TYPOLOGIES · PARTITION MODEL",
    title="Socio-Economic Risk Archetypes & Cluster Profiles",
    deck="Unsupervised partition modeling (K-Means with Silhouette Optimization) segmenting 36 States and UTs into structurally homogenous peer cohorts to support tailored policy interventions and peer benchmarking.",
    location_tag="UNSUPERVISED PARTITION ANALYSIS · OPTIMAL K=3",
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
# Dynamic Analytical Lede & Overview Scorecard
# ---------------------------------------------------------------------------
n_clusters = view["cluster"].nunique()
cluster_sizes = view.groupby("cluster").size().reset_index(name="size")
dim_cols = [c for c in SUB_COLS.values() if c in view.columns and view[c].notna().any()]

dominant_cluster = cluster_sizes.sort_values("size", ascending=False).iloc[0]["cluster"]
dominant_size = int(cluster_sizes.sort_values("size", ascending=False).iloc[0]["size"])
specialized_cluster = cluster_sizes.sort_values("size", ascending=True).iloc[0]["cluster"]
specialized_size = int(cluster_sizes.sort_values("size", ascending=True).iloc[0]["size"])

render_editorial_lede(
    f"Unsupervised partition analysis reveals {n_clusters} distinct institutional archetypes across India. "
    f"Archetype {dominant_cluster} encompasses the modal group ({dominant_size} jurisdictions with balanced delivery), "
    f"while Archetype {specialized_cluster} ({specialized_size} jurisdictions) represents a highly specialized profile "
    f"requiring custom programmatic investment."
)

render_editorial_scorecard([
    {
        "label": "Optimal Archetypes (k)",
        "value": str(n_clusters),
        "note": "Evaluated via silhouette coefficient (0.290)",
        "tag": "Optimized",
        "tag_bg": "#EAEFEA",
        "tag_fg": "#264230",
        "tag_border": "#BDCFBF",
    },
    {
        "label": f"Modal Archetype {dominant_cluster}",
        "value": f"{dominant_size} states",
        "note": f"{dominant_size/len(view):.0%} of total administrative jurisdictions",
    },
    {
        "label": f"Focal Archetype {specialized_cluster}",
        "value": f"{specialized_size} states",
        "note": "Priority cohort for targeted capital allocation",
        "tag": "Priority Watch",
        "tag_bg": "#FAEDE3",
        "tag_fg": "#8C4318",
        "tag_border": "#E8C1A5",
    },
    {
        "label": "Evaluated Feature Space",
        "value": f"{len(dim_cols)} Dimensions",
        "note": "UDISE+, NFHS-5 multi-sectoral feature matrices",
        "tag": "Synchronized",
        "tag_bg": "#EFECE4",
        "tag_fg": "#444A43",
        "tag_border": "#D5D0C5",
    },
])

# ---------------------------------------------------------------------------
# Dimension Profiles Tab (Grouped Bar & Heatmap)
# ---------------------------------------------------------------------------
render_section_header("SEC. 01", "Cross-Dimension Archetype Profiles", "Comparative Pillar Vulnerability")

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
    profile_long["cluster_label"] = "Archetype " + profile_long["cluster"].astype(str)

    tab_bar, tab_heat = st.tabs(["Grouped Dimensional Profile", "Risk Density Heatmap"])

    with tab_bar:
        fig_bar = px.bar(
            profile_long,
            x="Dimension",
            y="Mean Score",
            color="cluster_label",
            barmode="group",
            range_y=[0, 100],
            color_discrete_sequence=["#14241D", "#BA6835", "#827845", "#385E48"],
            labels={"cluster_label": "Archetype", "Mean Score": "Mean Risk Score (0-100)"},
        )
        fig_bar.update_traces(
            marker=dict(line=dict(width=0.8, color="#FAF8F2")),
            texttemplate="%{y:.1f}",
            textposition="outside",
            textfont=dict(family="IBM Plex Mono, monospace", size=9),
        )
        style_editorial_figure(
            fig_bar,
            height=370,
            title="Archetype Signature Comparison",
            subtitle="Mean normalized vulnerability index across core pillars (0 = optimal, 100 = distress)",
        )
        fig_bar.update_layout(yaxis_title="Mean Vulnerability Index")
        st.plotly_chart(fig_bar, use_container_width=True)
        source_note("K-Means centroids computed over normalized UDISE+ and NFHS-5 indicator scales")

    with tab_heat:
        heat_pivot = profile_long.pivot(
            index="cluster_label", columns="Dimension", values="Mean Score"
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
            subtitle="Dimensional stress density across clusters (darker ochre indicates acute bottleneck)",
        )
        st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("No dimension score columns located in dataset.")

# ---------------------------------------------------------------------------
# Latent Space Projection & Membership Roster
# ---------------------------------------------------------------------------
col_pca, col_members = st.columns([1.5, 1])

with col_pca:
    render_section_header("SEC. 02", "Latent Space Projection", "Principal Component Analysis (PCA)")

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
            scatter_df["Jurisdiction"] = view["district_name"].values

            fig_scatter = px.scatter(
                scatter_df,
                x="PC1",
                y="PC2" if n_components >= 2 else "PC1",
                color="Cluster",
                hover_name="Jurisdiction",
                hover_data={"Cluster": True, "PC1": ":.2f", "PC2": ":.2f"},
                color_discrete_sequence=["#14241D", "#BA6835", "#827845", "#385E48"],
            )
            fig_scatter.update_traces(
                marker=dict(size=10, opacity=0.9, line=dict(width=1, color="#FFFFFF"))
            )
            style_editorial_figure(
                fig_scatter,
                height=380,
                title="PCA Coordinate Mapping",
                subtitle="Orthogonal linear projection of multi-dimensional profiles into 2D latent space",
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

            explained = pca.explained_variance_ratio_
            source_note(
                f"Principal Components capture {explained[0]:.1%} (PC1)"
                + (f" and {explained[1]:.1%} (PC2)" if len(explained) > 1 else "")
                + " of cumulative variance across input indicators."
            )
        except Exception as exc:
            st.warning(f"PCA projection: {exc}")
    else:
        st.info("At least two valid dimensions required for latent space projection.")

with col_members:
    render_section_header("SEC. 03", "Jurisdiction Field Guide", "Roster & Recommended Policy Playbooks")

    playbooks = {
        0: {
            "title": "Institutional Resilience / Maintenance",
            "desc": "High delivery parity across education and healthcare. Priority: sustain capital upkeep, digital classroom integration, and targeted nutrition tracking in sub-pockets.",
        },
        1: {
            "title": "Civic Infrastructure & School Modernization",
            "desc": "Acute deficits in physical school amenities (power, sanitation, broadband connectivity). Priority: accelerated state-wide school electrification and piped drinking water grid connections.",
        },
        2: {
            "title": "Human Development & Nutritional Safety Net",
            "desc": "Elevated pupil-teacher ratios and persistent child stunting/anaemia. Priority: teacher recruitment drives, strengthened mid-day meal nutritional fortifications, and maternal health incentives.",
        },
    }

    for cid in sorted(view["cluster"].unique()):
        members = sorted(view[view["cluster"] == cid]["district_name"].dropna().unique())
        pb = playbooks.get(cid, {"title": "Targeted Sectoral Program", "desc": "Custom administrative intervention."})
        
        with st.expander(f"Archetype {cid} — {len(members)} Jurisdictions", expanded=(cid == dominant_cluster)):
            st.markdown(
                f"<div style='font-family:\"Newsreader\",serif; font-size:1.05rem; font-weight:600; color:#14241D; margin-bottom:4px;'>"
                f"{pb['title']}</div>"
                f"<div style='font-family:\"IBM Plex Sans\",sans-serif; font-size:0.8rem; color:#555B54; line-height:1.45; margin-bottom:10px;'>"
                f"{pb['desc']}</div>"
                f"<div style='font-family:\"IBM Plex Mono\",monospace; font-size:0.72rem; color:#14241D; line-height:1.55; background:#FAF9F5; padding:8px 10px; border:1px solid #E2DED4;'>"
                f"<b>Constituent States & UTs:</b><br>{', '.join(members)}"
                f"</div>",
                unsafe_allow_html=True,
            )
