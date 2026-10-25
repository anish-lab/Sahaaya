"""
SAHAAYA — Civic Intelligence, Editorial Precision Design System.

Inspired by high-end editorial cartography, civic research institutes, and
state data observatories. Features warm ivory paper surfaces, deep forest-green
accents, editorial Newsreader serif typography, and restrained burnt-orange highlights.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
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

# Cartographic Stepped / Sequential Scale for Maps
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

    :root {
        --bg-canvas: #F7F5EE;
        --surface-card: #FFFFFF;
        --surface-tint: #EFECE4;
        --forest-deep: #14241D;
        --forest-mid: #223B2F;
        --forest-accent: #385E48;
        --burnt-orange: #B84324;
        --terracotta: #BA6835;
        --antique-olive: #827845;
        --ink-primary: #181A18;
        --ink-secondary: #555B54;
        --ink-muted: #6E756C;
        --ink-faint: #8A9188;
        --rule-line: #E2DED4;
        --rule-dark: #2B3F34;
        --font-serif: 'Newsreader', Georgia, 'Times New Roman', serif;
        --font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        --font-mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }

    /* Global Paper Canvas with Coordinate Grid */
    html, body, [class*="css"] {
        font-family: var(--font-sans) !important;
        color: var(--ink-primary);
    }

    .stApp {
        background-color: var(--bg-canvas) !important;
        background-image:
            linear-gradient(to right, rgba(226, 222, 212, 0.35) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(226, 222, 212, 0.35) 1px, transparent 1px);
        background-size: 48px 48px;
    }

    /* Streamlit Chrome Cleanup — Verified on Streamlit 1.40 - 1.50 */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .stDeployButton, footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* Headings — Editorial Newsreader Serif */
    h1, h2, h3, .editorial-heading {
        font-family: var(--font-serif) !important;
        font-weight: 500 !important;
        color: var(--forest-deep) !important;
        letter-spacing: -0.015em !important;
    }

    h4, h5, h6 {
        font-family: var(--font-sans) !important;
        font-weight: 600 !important;
        color: var(--ink-primary) !important;
        letter-spacing: 0.01em !important;
    }

    /* Masthead & Folio Header */
    .folio-header {
        border-bottom: 2px solid var(--forest-deep);
        padding-bottom: 14px;
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        gap: 16px;
    }

    .folio-meta {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--ink-secondary);
    }

    .masthead-title {
        font-family: var(--font-serif);
        font-size: clamp(1.8rem, 3.2vw, 2.35rem);
        font-weight: 500;
        line-height: 1.15;
        color: var(--forest-deep);
        margin: 4px 0 6px 0;
    }

    .masthead-deck {
        font-family: var(--font-sans);
        font-size: 0.95rem;
        line-height: 1.55;
        color: #444A43;
        max-width: 860px;
        margin: 0;
    }

    .registration-mark {
        font-family: var(--font-mono);
        font-size: 0.68rem;
        color: var(--ink-faint);
        letter-spacing: 0.14em;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 8px;
        white-space: nowrap;
    }

    .registration-mark::before {
        content: "§";
        color: var(--burnt-orange);
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* Dynamic Lede Callout */
    .editorial-lede {
        font-family: var(--font-serif);
        font-size: 1.18rem;
        line-height: 1.55;
        color: var(--forest-deep);
        background: #FFFFFF;
        border-left: 3px solid var(--burnt-orange);
        border-top: 1px solid var(--rule-line);
        border-right: 1px solid var(--rule-line);
        border-bottom: 1px solid var(--rule-line);
        padding: 12px 18px;
        margin-bottom: 22px;
    }

    /* Integrated Editorial Scorecard */
    .editorial-scorecard {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        background: #FFFFFF;
        border: 1px solid var(--rule-line);
        border-top: 3px solid var(--forest-deep);
        margin-bottom: 26px;
    }

    .scorecard-cell {
        padding: 16px 20px;
        border-right: 1px solid var(--rule-line);
        position: relative;
        transition: background 140ms ease-out;
    }

    .scorecard-cell:hover {
        background: #FAF9F5;
    }

    .scorecard-cell:last-child {
        border-right: none;
    }

    .scorecard-label {
        font-family: var(--font-mono);
        font-size: 0.68rem;
        font-weight: 500;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--ink-muted);
        margin-bottom: 6px;
        display: block;
    }

    .scorecard-value {
        font-family: var(--font-serif);
        font-size: 2.15rem;
        font-weight: 600;
        line-height: 1;
        color: var(--forest-deep);
        font-variant-numeric: tabular-nums;
        margin-bottom: 4px;
    }

    .scorecard-note {
        font-family: var(--font-sans);
        font-size: 0.74rem;
        color: #666C63;
        line-height: 1.35;
    }

    .scorecard-tag {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 1px;
        display: inline-block;
        margin-top: 4px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Section Divider Rule */
    .section-rule {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 28px 0 16px 0;
        border-bottom: 1px solid var(--rule-line);
        padding-bottom: 8px;
    }

    .section-code {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--burnt-orange);
    }

    .section-name {
        font-family: var(--font-serif);
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--forest-deep);
    }

    /* Deep Forest-Green Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--forest-deep) !important;
        border-right: 1px solid #233B2F !important;
    }

    /* Sidebar Content Flex Reordering: Promote SAHAAYA Brand Masthead above Navigation */
    [data-testid="stSidebarContent"] {
        display: flex !important;
        flex-direction: column !important;
    }

    [data-testid="stSidebarHeader"] {
        order: -20 !important;
    }

    [data-testid="stSidebarUserContent"] {
        display: contents !important;
    }

    [data-testid="stSidebarUserContent"] > [data-testid="stElementContainer"]:has(.sidebar-masthead),
    [data-testid="stSidebarUserContent"] > div:has(.sidebar-masthead),
    [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sidebar-masthead),
    .sidebar-masthead {
        order: -10 !important;
    }

    [data-testid="stSidebarNav"] {
        order: 0 !important;
        border-top: 1px solid #233B2F;
        border-bottom: 1px solid #233B2F;
        padding: 12px 0 !important;
        margin: 12px 0 !important;
    }

    [data-testid="stSidebarUserContent"] > [data-testid="stElementContainer"]:has(.stExpander),
    [data-testid="stSidebarUserContent"] > div:has(.stExpander),
    [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.stExpander),
    [data-testid="stSidebar"] .stExpander {
        order: 10 !important;
    }

    [data-testid="stSidebarUserContent"] > [data-testid="stElementContainer"]:has(.sidebar-meta-panel),
    [data-testid="stSidebarUserContent"] > div:has(.sidebar-meta-panel),
    [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sidebar-meta-panel),
    .sidebar-meta-panel {
        order: 20 !important;
    }

    [data-testid="stSidebar"] * {
        color: #E6E4DD !important;
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-family: var(--font-serif) !important;
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
        font-family: var(--font-sans) !important;
        font-weight: 400 !important;
        font-size: 0.88rem !important;
        color: #B5BDB6 !important;
        background: transparent !important;
        border-left: 2px solid transparent !important;
        transition: all 140ms ease-out !important;
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
        border-left: 2px solid var(--burnt-orange) !important;
    }

    .sidebar-masthead {
        padding: 18px 12px 14px 12px;
        border-bottom: 1px solid #233B2F;
        margin-bottom: 12px;
    }

    .sidebar-logotype {
        font-family: var(--font-serif);
        font-size: 1.35rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        color: #FAF8F2 !important;
        line-height: 1;
        margin-bottom: 4px;
    }

    .sidebar-descriptor {
        font-family: var(--font-mono);
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
        font-family: var(--font-mono);
        font-size: 0.7rem;
        line-height: 1.6;
    }

    /* Streamlit Tables & Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--rule-line) !important;
        border-radius: 0px !important;
        background: #FFFFFF !important;
    }

    /* Tabs — Quiet Editorial Underline Style */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid var(--rule-line) !important;
        gap: 24px !important;
        padding: 0 0 1px 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: var(--font-mono) !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        color: var(--ink-muted) !important;
        background: transparent !important;
        border-radius: 0px !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: 8px 4px !important;
        transition: all 140ms ease-out !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--forest-deep) !important;
        font-weight: 600 !important;
        border-bottom: 2px solid var(--forest-deep) !important;
    }

    /* Inputs, Selectboxes & Sliders */
    .stSelectbox label, .stSlider label {
        font-family: var(--font-mono) !important;
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        color: #4A5149 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #D5D0C5 !important;
        border-radius: 1px !important;
        color: var(--ink-primary) !important;
        font-family: var(--font-sans) !important;
        font-size: 0.88rem !important;
    }

    /* Forest Green Sliders — Verified on Streamlit 1.50 */
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--forest-deep) !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: 0 0 0 1px var(--forest-deep) !important;
    }
    div[data-baseweb="slider"] div[data-testid="stSliderTrack"] > div {
        background-color: var(--forest-deep) !important;
    }

    /* Buttons — Crisp Editorial Radii & Physical Micro-interaction */
    .stButton > button {
        background-color: var(--forest-deep) !important;
        color: #FAF8F2 !important;
        border: 1px solid var(--forest-deep) !important;
        border-radius: 1px !important;
        font-family: var(--font-mono) !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        padding: 8px 18px !important;
        transition: transform 140ms ease-out, background 140ms ease-out !important;
    }

    .stButton > button:hover {
        background-color: var(--forest-mid) !important;
        border-color: var(--forest-mid) !important;
        color: #FFFFFF !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(20, 36, 29, 0.12) !important;
    }

    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* Secondary / Outline Button */
    .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        color: var(--forest-deep) !important;
        border: 1px solid var(--forest-deep) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: rgba(20, 36, 29, 0.05) !important;
        color: var(--forest-deep) !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #F2EFE8 !important;
        border: 1px solid var(--rule-line) !important;
        border-radius: 0px !important;
        font-family: var(--font-sans) !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        color: var(--ink-primary) !important;
    }

    /* Risk Badge Pills — Minimal Rectangular */
    .editorial-badge {
        font-family: var(--font-mono);
        font-size: 0.68rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 1px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        display: inline-block;
    }

    /* Margin Note Card */
    .editorial-margin-note {
        background: #FFFFFF;
        border: 1px solid var(--rule-line);
        border-left: 3px solid var(--forest-deep);
        padding: 14px 16px;
        margin-bottom: 16px;
    }
    .margin-note-kicker {
        font-family: var(--font-mono);
        font-size: 0.66rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--ink-muted);
        margin-bottom: 4px;
        display: block;
    }
    .margin-note-title {
        font-family: var(--font-serif);
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--forest-deep);
        line-height: 1.25;
        margin-bottom: 6px;
    }
    .margin-note-body {
        font-family: var(--font-sans);
        font-size: 0.8rem;
        color: #4A5149;
        line-height: 1.45;
    }

    /* Source Citation Line */
    .editorial-source-note {
        font-family: var(--font-mono);
        font-size: 0.66rem;
        color: var(--ink-faint);
        letter-spacing: 0.05em;
        padding-top: 6px;
        margin-top: 8px;
        border-top: 1px dashed var(--rule-line);
    }

    /* Accessibility: Reduced Motion */
    @media (prefers-reduced-motion: reduce) {
        * {
            transition: none !important;
            transform: none !important;
            animation: none !important;
        }
    }

    /* Responsive Breakpoints */
    @media (max-width: 1100px) {
        .editorial-scorecard {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        }
    }

    @media (max-width: 820px) {
        .folio-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 10px;
        }
        .registration-mark {
            align-self: flex-start;
        }
        .editorial-scorecard {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 560px) {
        .editorial-scorecard {
            grid-template-columns: 1fr;
        }
        .scorecard-cell {
            border-right: none;
            border-bottom: 1px solid var(--rule-line);
        }
        .scorecard-cell:last-child {
            border-bottom: none;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Reusable Editorial Layout Helpers
# ---------------------------------------------------------------------------
def render_masthead(
    folio_code: str,
    title: str,
    deck: str,
    location_tag: str = "ALL-INDIA OBSERVATORY · 20°35' N, 78°57' E",
) -> None:
    """Render an authoritative editorial folio masthead."""
    html = (
        f'<div class="folio-header">'
        f'<div><div class="folio-meta">{folio_code}</div>'
        f'<h1 class="masthead-title">{title}</h1>'
        f'<p class="masthead-deck">{deck}</p></div>'
        f'<div class="registration-mark">{location_tag}</div>'
        f'</div>'
    )
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


page_masthead = render_masthead  # Alias for convenience


def render_section_header(code: str, title: str, subtitle: str = "") -> None:
    """Render a crisp editorial section rule."""
    sub_html = f'<span style="font-size:0.8rem; color:#6E756C; font-family:\'IBM Plex Sans\'; margin-left:8px;">— {subtitle}</span>' if subtitle else ""
    html = f'<div class="section-rule"><span class="section-code">{code}</span><span class="section-name">{title}</span>{sub_html}</div>'
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


section_header = render_section_header  # Alias for convenience


def render_editorial_scorecard(metrics: list[dict]) -> None:
    """Render an integrated editorial horizontal scorecard with hairline cell dividers."""
    cells = []
    for m in metrics:
        tag_html = ""
        if m.get("tag"):
            bg = m.get("tag_bg", "#EFECE4")
            fg = m.get("tag_fg", "#444A43")
            border = m.get("tag_border", "#D5D0C5")
            tag_html = f'<span class="scorecard-tag" style="background:{bg}; color:{fg}; border:1px solid {border};">{m["tag"]}</span>'
        note_html = f'<div class="scorecard-note">{m.get("note", "")}</div>' if m.get("note") else ""
        cells.append(
            f'<div class="scorecard-cell">'
            f'<span class="scorecard-label">{m["label"]}</span>'
            f'<div class="scorecard-value">{m["value"]}</div>'
            f'{note_html}'
            f'{tag_html}'
            f'</div>'
        )

    grid_html = f'<div class="editorial-scorecard">{"".join(cells)}</div>'
    if hasattr(st, "html"):
        st.html(grid_html)
    else:
        st.markdown(grid_html, unsafe_allow_html=True)


scorecard = render_editorial_scorecard  # Alias for convenience


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


risk_badge = render_editorial_badge  # Alias for convenience


def render_editorial_lede(lede_text: str) -> None:
    """Render a highlighted dynamic analytical finding lede."""
    html = f'<div class="editorial-lede">{lede_text}</div>'
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def source_note(text: str) -> None:
    """Render a subtle footnote / source attribution below a chart or ledger."""
    html = f'<div class="editorial-source-note">SOURCE / PROVENANCE: {text}</div>'
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def margin_note(title: str, text: str, kicker: str = "Analytical Context") -> None:
    """Render a structured marginalia note in an asymmetric side column."""
    html = (
        f'<div class="editorial-margin-note">'
        f'<span class="margin-note-kicker">{kicker}</span>'
        f'<div class="margin-note-title">{title}</div>'
        f'<div class="margin-note-body">{text}</div>'
        f'</div>'
    )
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def render_sidebar_masthead(data_status: dict) -> None:
    """Render the research observatory identity in the sidebar."""
    with st.sidebar:
        sidebar_top = (
            '<div class="sidebar-masthead" id="sahaaya-sidebar-masthead">'
            '<div class="sidebar-logotype">SAHAAYA</div>'
            '<div class="sidebar-descriptor">National Civic Observatory</div>'
            '<div style="font-family:\'IBM Plex Sans\'; font-size:0.75rem; color:#8A9A8E; margin-top:6px; line-height:1.4;">'
            'Multi-sectoral early warning radar synthesizing educational delivery (UDISE+), public health telemetry (NFHS-5), and civic infrastructure across India.'
            '</div>'
            '</div>'
        )
        if hasattr(st, "html"):
            st.html(sidebar_top)
        else:
            st.markdown(sidebar_top, unsafe_allow_html=True)

        js_pin = """
        <script>
        (function() {
            function placeMastheadTop() {
                try {
                    var doc = window.parent.document;
                    if (!doc) return;
                    var masthead = doc.getElementById('sahaaya-sidebar-masthead') || doc.querySelector('.sidebar-masthead');
                    var nav = doc.querySelector('[data-testid="stSidebarNav"]');
                    if (masthead && nav && nav.parentNode) {
                        var targetNode = masthead;
                        while (targetNode.parentElement && 
                               targetNode.parentElement !== nav.parentNode && 
                               targetNode.parentElement.getAttribute('data-testid') !== 'stSidebarContent') {
                            targetNode = targetNode.parentElement;
                        }
                        if (targetNode && targetNode.parentNode && targetNode.nextSibling !== nav) {
                            targetNode.parentNode.insertBefore(targetNode, nav);
                        }
                    }
                } catch(e) {}
            }
            placeMastheadTop();
            var observer = new MutationObserver(placeMastheadTop);
            observer.observe(window.parent.document.body, { childList: true, subtree: true });
            setTimeout(function() { observer.disconnect(); }, 5000);
        })();
        </script>
        """
        components.html(js_pin, height=0, width=0)

        with st.expander("Observatory Pipeline Status", expanded=False):
            items = [
                ("State Feature Store", data_status.get("features", False)),
                ("Cluster Typologies", data_status.get("clusters", False)),
                ("Isolation Forest Anomaly", data_status.get("anomalies", False)),
                ("Survey Boundaries (GeoJSON)", data_status.get("geojson", False)),
            ]
            for label, ok in items:
                status_symbol = "▪ SYNCHRONIZED" if ok else "▫ PENDING"
                status_color = "#99BAA4" if ok else "#8E7569"
                row_html = (
                    f"<div style='display:flex; justify-content:space-between; font-size:0.72rem; padding:4px 0; border-bottom:1px solid #233B2F; font-family:monospace;'>"
                    f"<span style='color:#C4CDC6;'>{label}</span>"
                    f"<span style='color:{status_color}; font-weight:600;'>{status_symbol}</span>"
                    f"</div>"
                )
                if hasattr(st, "html"):
                    st.html(row_html)
                else:
                    st.markdown(row_html, unsafe_allow_html=True)

        sidebar_bottom = (
            '<div class="sidebar-meta-panel">'
            '<div style="color:#7A8F80; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:2px;">GEOGRAPHIC ENVELOPE</div>'
            '<div style="color:#FAF8F2; font-weight:500;">All-India States & UTs</div>'
            '<div style="color:#7A8F80; font-size:0.65rem; margin-top:4px;">EPSG:4326 · Canonical Jurisdictions: 36</div>'
            '</div>'
        )
        if hasattr(st, "html"):
            st.html(sidebar_bottom)
        else:
            st.markdown(sidebar_bottom, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Editorial Plotly Styler & Master Layout Helper
# ---------------------------------------------------------------------------
def plotly_editorial_layout(
    height: int = 380,
    title: str = "",
    subtitle: str = "",
    show_grid: bool = True,
) -> dict:
    """Return a unified Plotly layout dictionary matching the FT / Economist data desk aesthetic."""
    full_title = None
    if title:
        full_title = dict(
            text=f"<b>{title}</b>" + (f"<br><span style='font-size:11px; font-weight:normal; font-family:IBM Plex Mono, monospace; color:#6E756C;'>{subtitle}</span>" if subtitle else ""),
            font=dict(family="Newsreader, Georgia, serif", size=15, color="#14241D"),
            x=0.0,
            xanchor="left",
        )

    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(
            family="IBM Plex Sans, sans-serif",
            size=11,
            color="#2C312E",
        ),
        title=full_title,
        margin=dict(l=15, r=20, t=92 if subtitle else (72 if title else 32), b=38),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="right",
            x=1.0,
            font=dict(size=10, family="IBM Plex Mono, monospace"),
            bgcolor="rgba(247, 245, 238, 0.90)",
            bordercolor="#E2DED4",
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="#14241D",
            font_size=11,
            font_family="IBM Plex Mono, monospace",
            font_color="#FAF8F2",
            bordercolor="#233B2F",
            align="left",
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor="#E2DED4",
            linewidth=1,
            tickfont=dict(family="IBM Plex Mono, monospace", size=10, color="#555B54"),
            title_font=dict(family="IBM Plex Mono, monospace", size=10, color="#555B54"),
        ),
        yaxis=dict(
            showgrid=show_grid,
            gridcolor="#E2DED4",
            gridwidth=0.6,
            zeroline=True,
            zerolinecolor="#C2BCB0",
            zerolinewidth=1,
            showline=False,
            tickfont=dict(family="IBM Plex Mono, monospace", size=10, color="#555B54"),
            title_font=dict(family="IBM Plex Mono, monospace", size=10, color="#555B54"),
        ),
    )
    return layout


def style_editorial_figure(
    fig: go.Figure,
    height: int = 380,
    title: str = "",
    subtitle: str = "",
    show_grid: bool = True,
) -> go.Figure:
    """Format Plotly charts to look like professional editorial research graphs."""
    base_layout = plotly_editorial_layout(height, title, subtitle, show_grid)
    fig.update_layout(**base_layout)
    return fig
