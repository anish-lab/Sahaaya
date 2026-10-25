"""
test_validation_benchmark.py — Tests for external benchmark validation and weight sensitivity.
"""
from pathlib import Path
import pytest
import pandas as pd

from src.evaluation.validate_index import validate_vulnerability_index, NITI_AAYOG_MPI_HEADCOUNT_PCT
from src.evaluation.weight_sensitivity import evaluate_weight_sensitivity
from src.evaluation.correlation_leakage import evaluate_collinearity_and_leakage

ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = ROOT / "data" / "processed" / "features.parquet"


def test_niti_aayog_mpi_coverage():
    """Verify that NITI Aayog MPI benchmark covers all 36 States/UTs."""
    assert len(NITI_AAYOG_MPI_HEADCOUNT_PCT) == 36
    assert "Bihar" in NITI_AAYOG_MPI_HEADCOUNT_PCT
    assert "Kerala" in NITI_AAYOG_MPI_HEADCOUNT_PCT
    assert "Tamil Nadu" in NITI_AAYOG_MPI_HEADCOUNT_PCT


@pytest.mark.skipif(not FEATURES_PATH.exists(), reason="features.parquet not generated yet")
def test_vulnerability_index_validation():
    """Verify external construct validity against NITI Aayog MPI."""
    results = validate_vulnerability_index()
    assert results["sample_size"] == 36
    # Strong Spearman rank correlation >= 0.85
    assert results["spearman_rho"] >= 0.85
    assert results["spearman_pvalue"] < 0.0001
    assert results["pearson_r"] >= 0.80


@pytest.mark.skipif(not FEATURES_PATH.exists(), reason="features.parquet not generated yet")
def test_weight_sensitivity_and_pca():
    """Verify weight robustness and PCA index convergence."""
    results = evaluate_weight_sensitivity(n_simulations=200)
    # Top-10 priority list stability > 85%
    assert results["mean_top10_stability"] >= 0.85
    assert results["mean_spearman_rho"] >= 0.90
    # Equal-weight index correlates strongly with PCA PC1 index (> 0.95)
    assert results["pca_spearman_rho"] >= 0.95
    assert results["pca_variance_explained"] >= 0.50


@pytest.mark.skipif(not FEATURES_PATH.exists(), reason="features.parquet not generated yet")
def test_collinearity_and_leakage_audit():
    """Verify collinearity audit detects known high-correlation pairs."""
    results = evaluate_collinearity_and_leakage(threshold=0.70)
    assert len(results["indicators_audited"]) >= 10
    assert len(results["collinear_pairs"]) >= 1
    assert "leakage_protocol" in results
