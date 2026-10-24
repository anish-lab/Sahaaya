"""Launch the SAHAAYA Streamlit dashboard.

Adds the project root to sys.path so that ``app/`` modules can import
from ``src/`` (e.g. ``from src.models.simulate import WhatIfSimulator``).

Usage:
    python run_app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Ensure project root is importable (for src.*)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit.web import cli as stcli

app = ROOT / "app" / "Home.py"
sys.argv = ["streamlit", "run", str(app)]
sys.exit(stcli.main())
