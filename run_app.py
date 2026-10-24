"""Press the Run (play) button in VS Code on this file to start the app."""
import sys
from pathlib import Path
from streamlit.web import cli as stcli

app = Path(__file__).resolve().parent / "app" / "Home.py"
sys.argv = ["streamlit", "run", str(app)]
sys.exit(stcli.main())