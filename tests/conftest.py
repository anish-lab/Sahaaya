"""
SAHAAYA Test Configuration and Fixtures
────────────────────────────────────────
Shared fixtures for all test modules.
Uses small, clearly-labelled synthetic fixtures for software correctness only.
These fixtures must NEVER be mistaken for official data.
"""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def project_root():
    """Return the project root path."""
    return ROOT


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory structure mimicking the project layout."""
    dirs = [
        "data/raw/udise", "data/raw/nfhs", "data/raw/mgnrega",
        "data/raw/boundaries", "data/raw/additional",
        "data/interim", "data/processed", "data/metadata",
        "models", "reports",
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def sample_district_master():
    """Minimal district master for testing (5 districts only).
    TESTING FIXTURE ONLY — not official data.
    """
    return pd.DataFrame({
        "district_id": ["TN01", "TN02", "TN03", "TN04", "TN05"],
        "district_name": ["Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore"],
        "state": ["Tamil Nadu"] * 5,
    })


@pytest.fixture
def sample_features():
    """Minimal features DataFrame for testing (5 districts, synthetic values).
    TESTING FIXTURE ONLY — not official data.
    """
    rng = np.random.default_rng(42)
    n = 5
    districts = ["Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore"]
    return pd.DataFrame({
        "district_id": [f"TN{i+1:02d}" for i in range(n)],
        "district_name": districts,
        "state": ["Tamil Nadu"] * n,
        "period": ["2021-22"] * n,
        "edu_risk": rng.uniform(10, 90, n).round(1),
        "health_risk": rng.uniform(10, 90, n).round(1),
        "emp_risk": rng.uniform(10, 90, n).round(1),
        "infra_risk": rng.uniform(10, 90, n).round(1),
        "overall_score": rng.uniform(20, 80, n).round(1),
        "risk_band": ["Low", "Moderate", "High", "Critical", "Moderate"],
        "data_completeness": [1.0, 1.0, 0.75, 1.0, 0.5],
    })


@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a sample CSV file for testing file discovery and ingestion."""
    csv_path = tmp_path / "test_data.csv"
    df = pd.DataFrame({
        "State": ["Tamil Nadu", "Tamil Nadu", "Tamil Nadu"],
        "District": ["Chennai", "Coimbatore", "Madurai"],
        "Value1": [100, 200, 300],
        "Value2": [1.5, 2.5, 3.5],
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_xlsx_file(tmp_path):
    """Create a sample XLSX file for testing."""
    xlsx_path = tmp_path / "test_data.xlsx"
    df = pd.DataFrame({
        "State": ["Tamil Nadu", "Tamil Nadu", "Tamil Nadu"],
        "District": ["Chennai", "Coimbatore", "Madurai"],
        "Indicator_A": [10.5, 20.3, 30.1],
        "Indicator_B": ["45%", "55%", "65%"],
    })
    df.to_excel(xlsx_path, index=False)
    return xlsx_path
