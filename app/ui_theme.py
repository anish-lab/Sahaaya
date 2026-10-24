"""
SAHAAYA — Civic Intelligence, Editorial Precision Design System.

Inspired by high-end editorial cartography, civic research institutes, and
state data observatories. Features warm ivory paper surfaces, deep forest-green
accents, editorial Newsreader serif typography, and restrained burnt-orange highlights.
"""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# ---------------------------------------------------------------------------
# Editorial Color System
# ---------------------------------------------------------------------------
PALETTE = {
    "bg_ivory": "#F7F5EE",        # Primary ivory canvas
    "surface_parchment": "#FFFFFF",# Crisp paper white
    "surface_tint": "#EFECE4",    # Muted linen tint
    "forest_deep": "#14241D",     # Deep forest green (surfaces & sidebar)
    "forest_mid": "#223B2F",      # Mid forest green
    "forest_accent": "#385E48",   # Muted sage/forest
    "burnt_orange": "#B84324",    # Restrained focal alert
    "terracotta": "#BA6835",      # Warm alert
    "antique_olive": "#827845",   # Moderate indicator
    "ink_black": "#181A18",       # Primary reading typography
    "ink_muted": "#555B54",       # Secondary prose
    "ink_faint": "#8A9188",       # Metadata & coordinates
    "rule_line": "#E2DED4",       # Hairline dividers
    "rule_dark": "#2B3F34",       # Hairline on dark surfaces
}

# Cartographic Continuous Scale for Maps
MAP_COLORSCALE = [
    [0.00, "#EAE5D9"],  # Baseline / Lowest vulnerability (Linen)
    [0.25, "#BDCBB9"],  # Low vulnerability (Pale Sage)
    [0.50, "#8C9D86"],  # Moderate (Sage Forest)
    [0.75, "#C87C47"],  # High (Warm Ochre)
    [1.00, "#A83C1F"],  # Critical (Burnt Sienna)
]

BAND_EDITORIAL_STYLES = {
    "Low": {"bg": "#EAEFEA", "fg": "#264230", "border": "#BDCFBF", "label": "Low Vulnerability"},
    "Moderate": {"bg": "#F5F3E4", "fg": "#5E5624", "border": "#D8D2A8", "label": "Moderate Vulnerability"},
    "High": {"bg": "#FAEDE3", "fg": "#8C4318", "border": "#E8C1A5", "label": "High Vulnerability"},
    "Critical": {"bg": "#F7E5DE", "fg": "#8A260F", "border": "#E5A997", "label": "Critical Vulnerability"},
}

# ---------------------------------------------------------------------------
# Global CSS Injection
# ---------------------------------------------------------------------------
def inject_custom_theme() -> None:
    """Inject typography, layout rules, sidebar styling, and editorial components."""
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,600&family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    /* Global Paper Canvas */
    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #181A18;
    }

    .stApp {
        background-color: #F7F5EE !important;
        background-image:
            linear-gradient(to right, rgba(226, 222, 212, 0.25) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(226, 222, 212, 0.25) 1px, transparent 1px);
        background-size: 48px 48px;
    }

    /* Headings — Editorial Newsreader Serif */
    h1, h2, h3, .editorial-heading {
        font-family: 'Newsreader', Georgia, serif !important;
        font-weight: 500 !important;
        color: #14241D !important;
        letter-spacing: -0.015em !important;
    }

    h4, h5, h6 {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 600 !important;
        color: #181A18 !important;
        letter-spacing: 0.01em !important;
    }

    /* Masthead & Folio Header */
    .folio-header {
        border-bottom: 2px solid #14241D;
        padding-bottom: 14px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }

    .folio-meta {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #555B54;
    }

    .masthead-title {
        font-family: 'Newsreader', Georgia, serif;
        font-size: 2.25rem;
        font-weight: 500;
        line-height: 1.15;
        color: #14241D;
        margin: 4px 0 6px 0;
    }

    .masthead-deck {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 0.95rem;
        line-height: 1.55;
        color: #444A43;
        max-width: 860px;
        margin: 0;
    }

    .registration-mark {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        color: #8A9188;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .registration-mark::before {
        content: "§";
        color: #B84324;
        font-size: 0.85rem;
    }

    /* Integrated Editorial Scorecard (Replaces Generic Floating Cards) */
    .editorial-scorecard {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        background: #FFFFFF;
        border: 1px solid #E2DED4;
        border-top: 3px solid #14241D;
        margin-bottom: 28px;
    }

    .scorecard-cell {
        padding: 16px 20px;
        border-right: 1px solid #E2DED4;
        position: relative;
    }

    .scorecard-cell:last-child {
        border-right: none;
    }

    .scorecard-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        font-weight: 500;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #6E756C;
        margin-bottom: 6px;
        display: block;
    }

    .scorecard-value {
        font-family: 'Newsreader', Georgia, serif;
        font-size: 2.1rem;
        font-weight: 600;
        line-height: 1;
        color: #14241D;
        font-variant-numeric: tabular-nums;
        margin-bottom: 4px;
    }

    .scorecard-note {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 0.74rem;
        color: #666C63;
        line-height: 1.35;
    }

    .scorecard-tag {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.65rem;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 1px;
        display: inline-block;
        margin-top: 4px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Control Bar — Architectural & Flush */
    .control-strip {
        background: #EFECE4;
        border: 1px solid #E0DCD3;
        padding: 12px 18px;
        margin-bottom: 22px;
        display: flex;
        align-items: center;
        gap: 16px;
    }

    /* Section Divider Rule */
    .section-rule {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 28px 0 16px 0;
        border-bottom: 1px solid #E2DED4;
        padding-bottom: 8px;
    }

    .section-code {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #B84324;
    }

    .section-name {
        font-family: 'Newsreader', Georgia, serif;
        font-size: 1.25rem;
        font-weight: 600;
        color: #14241D;
    }

    /* Deep Forest-Green Sidebar */
    [data-testid="stSidebar"] {
        background-color: #14241D !important;
        border-right: 1px solid #233B2F !important;
    }

    [data-testid="stSidebar"] * {
        color: #E6E4DD !important;
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-family: 'Newsreader', Georgia, serif !important;
        color: #FAF8F2 !important;
        font-weight: 500 !important;
    }

    /* Sidebar Navigation Links */
    [data-testid="stSidebarNav"] {
        border-top: 1px solid #233B2F;
        border-bottom: 1px solid #233B2F;
        padding: 12px 0 !important;
        margin: 12px 0 !important;
    }

    [data-testid="stSidebarNav"] li a {
        border-radius: 0px !important;
        padding: 9px 16px !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 400 !important;
        font-size: 0.88rem !important;
        color: #B5BDB6 !important;
        background: transparent !important;
        border-left: 2px solid transparent !important;
        transition: all 0.15s ease !important;
    }

    [data-testid="stSidebarNav"] li a:hover {
        background: rgba(255, 255, 255, 0.04) !important;
        color: #FAF8F2 !important;
        border-left: 2px solid #758A7A !important;
    }

    [data-testid="stSidebarNav"] li a[aria-current="page"] {
        background: rgba(255, 255, 255, 0.06) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-left: 2px solid #C85A2A !important;
    }

    /* Sidebar Header Masthead */
    .sidebar-masthead {
        padding: 18px 12px 14px 12px;
        border-bottom: 1px solid #233B2F;
        margin-bottom: 12px;
    }

    .sidebar-logotype {
        font-family: 'Newsreader', Georgia, serif;
        font-size: 1.35rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        color: #FAF8F2 !important;
        line-height: 1;
        margin-bottom: 4px;
    }

    .sidebar-descriptor {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.65rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #8D9A8F !important;
    }

    .sidebar-meta-panel {
        background: #1B3026;
        border: 1px solid #294435;
        padding: 12px 14px;
        margin-top: 14px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        line-height: 1.6;
    }

    /* Streamlit Tables & Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid #E2DED4 !important;
        border-radius: 0px !important;
        background: #FFFFFF !important;
    }

    /* Tabs — Quiet Editorial Underline Style */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid #E2DED4 !important;
        gap: 24px !important;
        padding: 0 0 1px 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        color: #6E756C !important;
        background: transparent !important;
        border-radius: 0px !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: 8px 4px !important;
    }

    .stTabs [aria-selected="true"] {
        color: #14241D !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #14241D !important;
    }

    /* Inputs, Selectboxes & Sliders */
    .stSelectbox label, .stSlider label {
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 0.74rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        color: #4A5149 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #D5D0C5 !important;
        border-radius: 1px !important;
        color: #181A18 !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.88rem !important;
    }

    /* Buttons — Crisp Minimal Radius */
    .stButton > button {
        background-color: #14241D !important;
        color: #FAF8F2 !important;
        border: 1px solid #14241D !important;
        border-radius: 1px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        padding: 8px 18px !important;
        transition: all 0.15s ease !important;
    }

    .stButton > button:hover {
        background-color: #223B2F !important;
        border-color: #223B2F !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #F2EFE8 !important;
        border: 1px solid #E2DED4 !important;
        border-radius: 0px !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        color: #181A18 !important;
    }

    /* Risk Badge Pills — Minimal Rectangular */
    .editorial-badge {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 1px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        display: inline-block;
    }

    /* Header Bar Clean */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Editorial Layout Components
# ---------------------------------------------------------------------------
def render_masthead(
    folio_code: str,
    title: str,
    deck: str,
    location_tag: str = "TAMIL NADU CIVIC REGISTRY · 11°07' N, 78°39' E",
) -> None:
    """Render a newspaper / research folio masthead."""
    html = f"""
    <div class="folio-header">
        <div>
            <div class="folio-meta">{folio_code}</div>
            <h1 class="masthead-title">{title}</h1>
            <p class="masthead-deck">{deck}</p>
        </div>
        <div class="registration-mark">
            {location_tag}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_section_header(code: str, title: str, subtitle: str = "") -> None:
    """Render a crisp editorial section rule."""
    sub_html = f"<span style='font-size:0.8rem; color:#6E756C; font-family:\"IBM Plex Sans\"; margin-left:8px;'>— {subtitle}</span>" if subtitle else ""
    html = f"""
    <div class="section-rule">
        <span class="section-code">{code}</span>
        <span class="section-name">{title}</span>
        {sub_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_editorial_scorecard(metrics: list[dict]) -> None:
    """Render an integrated editorial horizontal scorecard with hairline cell dividers.

    Parameters
    ----------
    metrics : list of dicts with keys:
        - label (str): uppercase category description
        - value (str or int or float): prominent reading numeral
        - note (str): explanation or baseline comparison
        - tag (str, optional): tiny tag text
        - tag_style (dict, optional): bg, fg, border
    """
    cells = []
    for m in metrics:
        tag_html = ""
        if m.get("tag"):
            bg = m.get("tag_bg", "#EFECE4")
            fg = m.get("tag_fg", "#444A43")
            border = m.get("tag_border", "#D5D0C5")
            tag_html = f"""
            <span class="scorecard-tag" style="background:{bg}; color:{fg}; border:1px solid {border};">
                {m['tag']}
            </span>
            """
        cells.append(
            f"""
            <div class="scorecard-cell">
                <span class="scorecard-label">{m['label']}</span>
                <div class="scorecard-value">{m['value']}</div>
                <div class="scorecard-note">{m.get('note', '')}</div>
                {tag_html}
            </div>
            """
        )

    grid_html = f"""
    <div class="editorial-scorecard">
        {''.join(cells)}
    </div>
    """
    st.markdown(grid_html, unsafe_allow_html=True)


def render_editorial_badge(band_name: str) -> str:
    """Return crisp rectangular editorial badge for risk band."""
    style = BAND_EDITORIAL_STYLES.get(
        str(band_name),
        {"bg": "#EFECE4", "fg": "#444A43", "border": "#D5D0C5", "label": str(band_name)}
    )
    return (
        f'<span class="editorial-badge" style="background:{style["bg"]}; color:{style["fg"]}; border:1px solid {style["border"]};">'
        f'{style.get("label", band_name)}'
        f'</span>'
    )


def render_sidebar_masthead(data_status: dict) -> None:
    """Render the research observatory identity in the sidebar."""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-masthead">
                <div class="sidebar-logotype">SAHAAYA</div>
                <div class="sidebar-descriptor">State Civic Data Observatory</div>
                <div style="font-family:'IBM Plex Sans'; font-size:0.75rem; color:#8A9A8E; margin-top:6px; line-height:1.4;">
                    Multi-dimensional early-warning index synthesising UDISE+, NFHS-5, and MGNREGA telemetry for Tamil Nadu.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Observatory Pipeline Status", expanded=False):
            items = [
                ("District Feature Store", data_status.get("features", False)),
                ("Cluster Typologies", data_status.get("clusters", False)),
                ("Isolation Forest Anomaly", data_status.get("anomalies", False)),
                ("Survey Boundaries (GeoJSON)", data_status.get("geojson", False)),
            ]
            for label, ok in items:
                status_symbol = "▪ SYNCHRONIZED" if ok else "▫ PENDING"
                status_color = "#99BAA4" if ok else "#8E7569"
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; font-size:0.72rem; padding:4px 0; border-bottom:1px solid #233B2F; font-family:\"IBM Plex Mono\";'>"
                    f"<span style='color:#C4CDC6;'>{label}</span>"
                    f"<span style='color:{status_color}; font-weight:600;'>{status_symbol}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            """
            <div class="sidebar-meta-panel">
                <div style="color:#7A8F80; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:2px;">GEOGRAPHIC ENVELOPE</div>
                <div style="color:#FAF8F2; font-weight:500;">Tamil Nadu, India</div>
                <div style="color:#7A8F80; font-size:0.65rem; margin-top:4px;">EPSG:4326 · Canonical Districts: 38</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Editorial Plotly Styler
# ---------------------------------------------------------------------------
def style_editorial_figure(
    fig: go.Figure,
    height: int = 380,
    title: str = "",
    subtitle: str = "",
    show_grid: bool = True,
) -> go.Figure:
    """Format Plotly charts to look like professional editorial research graphs."""
    full_title = None
    if title:
        full_title = dict(
            text=f"<b>{title}</b>" + (f"<br><span style='font-size:11px; font-weight:normal; color:#6E756C;'>{subtitle}</span>" if subtitle else ""),
            font=dict(family="Newsreader, Georgia, serif", size=15, color="#14241D"),
            x=0.0,
            xanchor="left",
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(
            family="IBM Plex Sans, sans-serif",
            size=11,
            color="#2C312E",
        ),
        title=full_title,
        margin=dict(l=10, r=15, t=44 if title else 16, b=24),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, family="IBM Plex Mono"),
            bgcolor="rgba(247, 245, 238, 0.8)",
            bordercolor="#E2DED4",
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="#14241D",
            font_size=11,
            font_family="IBM Plex Mono",
            font_color="#FAF8F2",
            bordercolor="#233B2F",
        ),
    )

    if show_grid:
        fig.update_xaxes(
            showgrid=True,
            gridcolor="#E5E0D5",
            gridwidth=0.75,
            linecolor="#C2BCB0",
            linewidth=1,
            tickfont=dict(size=10, family="IBM Plex Mono", color="#5E655D"),
            zeroline=False,
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor="#E5E0D5",
            gridwidth=0.75,
            linecolor="#C2BCB0",
            linewidth=1,
            tickfont=dict(size=10, family="IBM Plex Mono", color="#5E655D"),
            zeroline=False,
        )

    return fig
