"""
Tests for data validation utilities.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestValidation:
    """Test data validation functions."""

    def test_validate_schema_passes_valid(self, sample_features):
        """Valid DataFrame passes schema validation."""
        try:
            from src.validate_data import validate_schema
            result = validate_schema(
                sample_features,
                required_cols=["district_id", "district_name", "overall_score"],
                numeric_cols=["overall_score", "edu_risk"]
            )
            assert result["valid"] is True
        except ImportError:
            pytest.skip("validate_data module not yet built")

    def test_validate_schema_fails_missing_col(self, sample_features):
        """Missing required column is detected."""
        try:
            from src.validate_data import validate_schema
            result = validate_schema(
                sample_features,
                required_cols=["district_id", "nonexistent_column"],
                numeric_cols=[]
            )
            assert result["valid"] is False
            assert "nonexistent_column" in str(result["missing_cols"])
        except ImportError:
            pytest.skip("validate_data module not yet built")

    def test_validate_ranges(self, sample_features):
        """Values outside expected range are flagged."""
        try:
            from src.validate_data import validate_ranges
            # All values should be 0-100
            report = validate_ranges(sample_features, "overall_score", 0, 100)
            assert report["out_of_range"] == 0
        except ImportError:
            pytest.skip("validate_data module not yet built")

    def test_validate_ranges_catches_violations(self):
        """Out-of-range values are correctly detected."""
        try:
            from src.validate_data import validate_ranges
            df = pd.DataFrame({"score": [10, 50, 150, -5, 80]})
            report = validate_ranges(df, "score", 0, 100)
            assert report["out_of_range"] == 2  # 150 and -5
        except ImportError:
            pytest.skip("validate_data module not yet built")


class TestDistrictMaster:
    """Test entity master building and matching."""

    def test_master_has_36_states(self):
        """State master has 36 Indian States and UTs."""
        try:
            from src.build_district_master import build_master
            master = build_master()
            assert len(master) == 36
        except ImportError:
            pytest.skip("build_district_master module not yet built")

    def test_exact_match(self):
        """Exact canonical name matches correctly."""
        try:
            from src.build_district_master import match_district
            result = match_district("Tamil Nadu")
            assert result is not None
            assert result[1] == "Tamil Nadu"
            assert result[2] == "exact"
        except ImportError:
            pytest.skip("build_district_master module not yet built")

    def test_alias_match(self):
        """Known alias matches correctly."""
        try:
            from src.build_district_master import match_district
            result = match_district("Pondicherry")
            assert result is not None
            assert result[1] == "Puducherry"
            assert result[2] == "alias"
        except ImportError:
            pytest.skip("build_district_master module not yet built")

    def test_fuzzy_match(self):
        """Fuzzy close match works."""
        try:
            from src.build_district_master import match_district
            result = match_district("Keral")  # Missing 'a'
            assert result is not None
            assert result[1] == "Kerala"
        except ImportError:
            pytest.skip("build_district_master module not yet built")

    def test_no_match_garbage(self):
        """Garbage input returns None."""
        try:
            from src.build_district_master import match_district
            result = match_district("xyzzy_nonexistent_12345")
            assert result is None
        except ImportError:
            pytest.skip("build_district_master module not yet built")


class TestFeatures:
    """Test feature engineering and vulnerability index."""

    def test_vulnerability_scale_bounds(self):
        """Min-max scaling produces values in 0-100."""
        try:
            from src.features.vulnerability_index import min_max_scale
            series = pd.Series([10, 20, 30, 40, 50])
            scaled = min_max_scale(series)
            assert scaled.min() >= 0
            assert scaled.max() <= 100
        except ImportError:
            pytest.skip("vulnerability_index module not yet built")

    def test_risk_band_assignment(self):
        """Risk bands are assigned correctly."""
        try:
            from src.features.vulnerability_index import assign_risk_band
            assert assign_risk_band(20) == "Low"
            assert assign_risk_band(40) == "Moderate"
            assert assign_risk_band(55) == "High"
            assert assign_risk_band(80) == "Critical"
        except ImportError:
            pytest.skip("vulnerability_index module not yet built")

    def test_risk_band_nan(self):
        """NaN score gets NaN risk band."""
        try:
            from src.features.vulnerability_index import assign_risk_band
            result = assign_risk_band(float("nan"))
            assert pd.isna(result)
        except ImportError:
            pytest.skip("vulnerability_index module not yet built")

    def test_overall_score_ignores_nan(self):
        """Overall score is mean of available dimensions, skipping NaN."""
        try:
            from src.features.vulnerability_index import compute_overall_score
            score = compute_overall_score(edu=60.0, health=40.0, emp=float("nan"), infra=50.0)
            assert abs(score - 50.0) < 0.1  # mean of 60, 40, 50
        except ImportError:
            pytest.skip("vulnerability_index module not yet built")


class TestClustering:
    """Test clustering model."""

    def test_cluster_assignments_valid(self, sample_features):
        """Cluster model produces valid assignments."""
        try:
            from src.models.cluster import ClusterModel
            import tempfile, os

            with tempfile.TemporaryDirectory() as tmpdir:
                feat_path = Path(tmpdir) / "features.parquet"
                sample_features.to_parquet(feat_path)

                model = ClusterModel(features_path=feat_path, n_clusters=2)
                model.ROOT = Path(tmpdir)
                (Path(tmpdir) / "data" / "processed").mkdir(parents=True)
                (Path(tmpdir) / "models").mkdir(parents=True)
                assignments, _ = model.run()

                assert "cluster" in assignments.columns
                assert assignments["cluster"].notna().all()
                assert set(assignments["cluster"].unique()).issubset({0, 1})
        except ImportError:
            pytest.skip("cluster module not yet built")

    def test_cluster_does_not_use_ids(self, sample_features):
        """Clustering must not use ID or label columns as features."""
        try:
            from src.models.cluster import ClusterModel
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                feat_path = Path(tmpdir) / "features.parquet"
                sample_features.to_parquet(feat_path)

                model = ClusterModel(features_path=feat_path)
                feature_cols = model._select_features(sample_features)

                forbidden = {"district_id", "district_name", "state", "period",
                             "risk_band", "cluster", "anomaly_flag", "anomaly_score"}
                assert len(set(feature_cols) & forbidden) == 0
        except ImportError:
            pytest.skip("cluster module not yet built")


class TestAnomalyDetection:
    """Test anomaly detection model."""

    def test_anomaly_produces_flags(self, sample_features):
        """Anomaly detector produces boolean flags."""
        try:
            from src.models.anomaly import AnomalyDetector
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                feat_path = Path(tmpdir) / "features.parquet"
                sample_features.to_parquet(feat_path)

                detector = AnomalyDetector(features_path=feat_path)
                detector.ROOT = Path(tmpdir)
                (Path(tmpdir) / "data" / "processed").mkdir(parents=True)
                (Path(tmpdir) / "models").mkdir(parents=True)
                results = detector.run()

                assert "anomaly_flag" in results.columns
                assert results["anomaly_flag"].dtype == bool
        except ImportError:
            pytest.skip("anomaly module not yet built")


class TestPreprocessing:
    """Test preprocessing utilities."""

    def test_parse_numeric_commas(self):
        """Numeric parser handles commas."""
        try:
            from src.preprocessing.clean import parse_numeric
            series = pd.Series(["1,234", "5,678.9", "100"])
            result = parse_numeric(series)
            assert result.iloc[0] == 1234.0
            assert result.iloc[1] == 5678.9
        except ImportError:
            pytest.skip("clean module not yet built")

    def test_parse_numeric_percentages(self):
        """Numeric parser handles percentage signs."""
        try:
            from src.preprocessing.clean import parse_numeric
            series = pd.Series(["45%", "67.5%", "100%"])
            result = parse_numeric(series)
            assert result.iloc[0] == 45.0
        except ImportError:
            pytest.skip("clean module not yet built")

    def test_parse_numeric_na_values(self):
        """Numeric parser treats NA/N/A/- as NaN."""
        try:
            from src.preprocessing.clean import parse_numeric
            series = pd.Series(["NA", "N/A", "-", "", "42"])
            result = parse_numeric(series)
            assert pd.isna(result.iloc[0])
            assert pd.isna(result.iloc[1])
            assert pd.isna(result.iloc[2])
            assert pd.isna(result.iloc[3])
            assert result.iloc[4] == 42.0
        except ImportError:
            pytest.skip("clean module not yet built")

    def test_standardize_column_names(self):
        """Column names are lowercased and cleaned."""
        try:
            from src.preprocessing.clean import standardize_column_names
            df = pd.DataFrame({"  District Name ": [1], "Total (Count)": [2], "Year": [3]})
            result = standardize_column_names(df)
            assert "district_name" in result.columns
            assert "total_(count)" in result.columns or "total_count" in result.columns
        except ImportError:
            pytest.skip("clean module not yet built")
