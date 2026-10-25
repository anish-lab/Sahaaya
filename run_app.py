"""Launch the SAHAAYA Streamlit dashboard.

Adds the project root and app directory to sys.path so that ``app/`` modules
can import from ``src/`` (e.g. ``from src.models.simulate import WhatIfSimulator``)
and sub-pages can import ``utils`` and ``ui_theme``.

Usage:
    python run_app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"

for p in [str(ROOT), str(APP_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from streamlit.web import cli as stcli

app = APP_DIR / "Home.py"
sys.argv = [
    "streamlit",
    "run",
    str(app),
    "--server.headless=true",
    "--browser.gatherUsageStats=false",
    "--server.port=8501",
]
sys.exit(stcli.main())
