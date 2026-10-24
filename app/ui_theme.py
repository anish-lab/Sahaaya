"""
SAHAAYA — Executive Design System & UI Theme Engine.

Provides luxury styling, Google Fonts, glassmorphism, responsive navigation ribbons,
metric cards, and consistent Plotly styling for the SAHAAYA platform.
"""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# ---------------------------------------------------------------------------
# Brand Color Palette
# ---------------------------------------------------------------------------
PALETTE = {
    "primary": "#4f46e5",       # Indigo 600
    "primary_dark": "#3730a3",  # Indigo 800
    "primary_light": "#e0e7ff", # Indigo 100
    "accent_cyan": "#06b6d4",   # Cyan 500
    "accent_violet": "#8b5cf6", # Violet 500
    "bg_canvas": "#f8fafc",     # Slate 50
    "card_bg": "#ffffff",
    "text_dark": "#0f172a",     # Slate 900
    "text_muted": "#64748b",    # Slate 500
    "border": "#e2e8f0",        # Slate 200
    "risk_low": "#10b981",      # Emerald
    "risk_mod": "#f59e0b",      # Amber
    "risk_high": "#f97316",     # Orange
    "risk_crit": "#e11d48",     # Crimson Rose
}

BAND_STYLING = {
    "Low": {"bg": "#ecfdf5", "text": "#065f46", "border": "#a7f3d0", "dot": "#10b981"},
    "Moderate": {"bg": "#fffbeb", "text": "#92400e", "border": "#fde68a", "dot": "#f59e0b"},
    "High": {"bg": "#fff7ed", "text": "#9a3412", "border": "#fed7aa", "dot": "#f97316"},
    "Critical": {"bg": "#fff1f2", "text": "#9f1239", "border": "#fecdd3", "dot": "#e11d48"},
}

PAGES = [
    {"label": "Overview", "icon": "⚡", "path": "Home.py"},
    {"label": "District Detail", "icon": "📍", "path": "pages/1_District.py"},
    {"label": "Risk Clusters", "icon": "🔮", "path": "pages/2_Clusters.py"},
    {"label": "Anomaly Radar", "icon": "🚨", "path": "pages/3_Anomalies.py"},
    {"label": "Simulator", "icon": "🧪", "path": "pages/4_Simulator.py"},
]

# ---------------------------------------------------------------------------
# Custom CSS Injection
# ---------------------------------------------------------------------------
def inject_custom_theme() -> None:
    """Inject global modern CSS styling and Google Fonts."""
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Typography & Canvas */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #0f172a;
    }

    /* Ambient Mesh Gradient Canvas */
    .stApp {
        background-color: #f8fafc;
        background-image:
            radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.08) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(244, 63, 94, 0.04) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.05) 0px, transparent 50%);
        background-attachment: fixed;
    }

    /* Headings */
    h1, h2, h3, h4, .stTitle {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        color: #0f172a !important;
    }

    /* Top Brand & Navbar Bar */
    .sahaaya-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 22px;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(226, 232, 240, 0.85);
        border-radius: 18px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
    }

    .sahaaya-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .brand-glyph {
        width: 38px;
        height: 38px;
        border-radius: 11px;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 6px 14px -3px rgba(79, 70, 229, 0.4);
    }

    .brand-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.25rem;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #0f172a 0%, #3730a3 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .brand-subtitle {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748b;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .live-pulse-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-radius: 9999px;
        color: #065f46;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }

    .pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulseAnimation 2s infinite;
    }

    @keyframes pulseAnimation {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Hero Banner Component */
    .hero-banner {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 20px;
        padding: 26px 30px;
        margin-bottom: 28px;
        box-shadow: 0 10px 30px -8px rgba(15, 23, 42, 0.05);
        position: relative;
        overflow: hidden;
    }

    .hero-banner::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #4f46e5 0%, #06b6d4 50%, #8b5cf6 100%);
    }

    .hero-tag {
        display: inline-block;
        padding: 4px 10px;
        background: #e0e7ff;
        color: #4338ca;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        border-radius: 6px;
        margin-bottom: 8px;
    }

    .hero-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0 0 6px 0;
        line-height: 1.2;
    }

    .hero-desc {
        color: #475569;
        font-size: 0.95rem;
        line-height: 1.5;
        margin: 0;
        max-width: 900px;
    }

    /* Ultra-Luxe Metric Cards */
    .kpi-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(226, 232, 240, 0.85);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 4px 15px -2px rgba(15, 23, 42, 0.04);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        position: relative;
        overflow: hidden;
    }

    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 28px -5px rgba(79, 70, 229, 0.1);
        border-color: rgba(99, 102, 241, 0.4);
    }

    .kpi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }

    .kpi-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: #64748b;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .kpi-icon-pill {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        background: #f1f5f9;
    }

    .kpi-value {
        font-family: 'Outfit', sans-serif;
        font-size: 1.95rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.1;
        margin-bottom: 6px;
    }

    .kpi-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
    }

    /* In-Page Ribbon Card */
    .filter-ribbon {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 22px;
        box-shadow: 0 2px 10px -2px rgba(15, 23, 42, 0.03);
    }

    /* Modern Streamlit Sidebar Overhaul */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
        border-right: 1px solid #e2e8f0 !important;
        box-shadow: 2px 0 16px -4px rgba(15, 23, 42, 0.04);
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.05rem !important;
        letter-spacing: -0.01em !important;
        color: #1e293b !important;
    }

    /* Style sidebar nav buttons into sleek rounded chips */
    [data-testid="stSidebarNav"] li a {
        border-radius: 10px !important;
        margin: 3px 8px !important;
        padding: 8px 14px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        color: #475569 !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stSidebarNav"] li a:hover {
        background: #f1f5f9 !important;
        color: #4f46e5 !important;
        transform: translateX(3px);
    }

    [data-testid="stSidebarNav"] li a[aria-current="page"] {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px -2px rgba(79, 70, 229, 0.35) !important;
    }

    /* Dataframe / Table styling */
    [data-testid="stDataFrame"] {
        border-radius: 14px !important;
        overflow: hidden;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 2px 12px -2px rgba(15, 23, 42, 0.04) !important;
    }

    /* Sleek Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: rgba(241, 245, 249, 0.8) !important;
        padding: 5px !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 9px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 8px 16px !important;
        color: #64748b !important;
        background: transparent !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #4f46e5 !important;
        box-shadow: 0 2px 8px -1px rgba(15, 23, 42, 0.08) !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        border: 1px solid #e2e8f0 !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: all 0.2s ease !important;
        border: 1px solid #cbd5e1 !important;
    }

    .stButton > button:hover {
        border-color: #4f46e5 !important;
        color: #4f46e5 !important;
        box-shadow: 0 4px 12px -2px rgba(79, 70, 229, 0.15) !important;
        transform: translateY(-1px);
    }

    /* Hide standard Streamlit header bar decoration */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Risk band pills */
    .risk-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .risk-pill-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------
def render_topbar(current_page: str = "Overview") -> None:
    """Render top floating brand bar."""
    st.markdown(
        """
        <div class="sahaaya-topbar">
            <div class="sahaaya-brand">
                <div class="brand-glyph">⚡</div>
                <div>
                    <div class="brand-title">SAHAAYA</div>
                    <div class="brand-subtitle">Tamil Nadu Social Vulnerability & Early Warning</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 14px;">
                <div class="live-pulse-badge">
                    <span class="pulse-dot"></span>
                    ACTIVE REPOSITORY
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(
    tag: str,
    title: str,
    description: str,
) -> None:
    """Render a signature page hero banner."""
    html = f"""
    <div class="hero-banner">
        <div class="hero-tag">{tag}</div>
        <h1 class="hero-title">{title}</h1>
        <p class="hero-desc">{description}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_kpi(
    label: str,
    value: str | int | float,
    icon: str = "📊",
    subtitle: str = "",
    color_accent: str = "#4f46e5",
    badge_text: str = "",
    badge_color: str = "#ecfdf5",
    badge_text_color: str = "#065f46",
) -> None:
    """Render an ultra-luxe HTML KPI card."""
    badge_html = ""
    if badge_text:
        badge_html = f"""
        <span class="kpi-badge" style="background:{badge_color}; color:{badge_text_color};">
            {badge_text}
        </span>
        """
    sub_html = f'<div style="font-size:0.75rem; color:#64748b; font-weight:500;">{subtitle}</div>' if subtitle else ""

    html = f"""
    <div class="kpi-card" style="border-top: 3px solid {color_accent};">
        <div class="kpi-header">
            <span class="kpi-label">{label}</span>
            <div class="kpi-icon-pill">{icon}</div>
        </div>
        <div class="kpi-value">{value}</div>
        <div style="display:flex; align-items:center; justify-content:space-between;">
            {sub_html}
            {badge_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_risk_pill(band_name: str) -> str:
    """Generate HTML snippet for a risk badge with a glowing dot."""
    style = BAND_STYLING.get(str(band_name), {"bg": "#f1f5f9", "text": "#475569", "border": "#cbd5e1", "dot": "#94a3b8"})
    return (
        f'<span class="risk-pill" style="background:{style["bg"]}; color:{style["text"]}; border:1px solid {style["border"]}">'
        f'<span class="risk-pill-dot" style="background:{style["dot"]}"></span>'
        f'{band_name}'
        f'</span>'
    )


def render_sidebar_brand(data_status: dict) -> None:
    """Render an aesthetic branded card inside the sidebar with data indicators."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding:14px; background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; margin-bottom:18px; box-shadow:0 2px 8px -2px rgba(15,23,42,0.04);">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                    <div style="width:30px; height:30px; border-radius:8px; background:linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color:white; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:14px;">S</div>
                    <div>
                        <div style="font-weight:700; font-size:0.95rem; color:#0f172a;">SAHAAYA Radar</div>
                        <div style="font-size:0.7rem; color:#64748b; font-weight:600;">STATE INTELLIGENCE</div>
                    </div>
                </div>
                <div style="font-size:0.75rem; color:#475569; line-height:1.4;">
                    Multi-sectoral early warning index integrating UDISE+, NFHS-5, and MGNREGA indicators.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("System Artifacts", expanded=False):
            items = [
                ("District Features", data_status.get("features", False)),
                ("Cluster Model", data_status.get("clusters", False)),
                ("Anomaly Detector", data_status.get("anomalies", False)),
                ("GeoJSON Boundaries", data_status.get("geojson", False)),
            ]
            for label, ok in items:
                icon = "🟢" if ok else "⚪"
                status_txt = "Available" if ok else "Pending"
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; font-size:0.8rem; padding:4px 0; border-bottom:1px solid #f1f5f9;'>"
                    f"<span>{icon} {label}</span>"
                    f"<span style='color:{'#10b981' if ok else '#94a3b8'}; font-weight:600;'>{status_txt}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# Plotly Luxury Styler
# ---------------------------------------------------------------------------
def style_plotly_fig(
    fig: go.Figure,
    height: int = 400,
    show_grid: bool = True,
    title: str = "",
) -> go.Figure:
    """Apply bespoke luxury typography, clean transparent canvas, and refined margins."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(
            family="Plus Jakarta Sans, sans-serif",
            size=12,
            color="#334155",
        ),
        title=dict(
            text=f"<b>{title}</b>" if title else None,
            font=dict(family="Outfit, sans-serif", size=16, color="#0f172a"),
            x=0,
            xanchor="left",
        ) if title else None,
        margin=dict(l=15, r=15, t=40 if title else 20, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="rgba(226,232,240,0.8)",
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_size=12,
            font_family="Plus Jakarta Sans",
            font_color="#ffffff",
            bordercolor="#334155",
        ),
    )

    if show_grid:
        fig.update_xaxes(
            showgrid=True,
            gridcolor="rgba(226, 232, 240, 0.7)",
            linecolor="rgba(203, 213, 225, 0.8)",
            tickfont=dict(size=11, color="#64748b"),
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor="rgba(226, 232, 240, 0.7)",
            linecolor="rgba(203, 213, 225, 0.8)",
            tickfont=dict(size=11, color="#64748b"),
        )
    return fig
