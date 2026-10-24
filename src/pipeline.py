"""
pipeline.py — Master automated data processing and modeling pipeline for SAHAAYA.

Executes end-to-end ingestion, cleaning, district standardization, feature engineering,
clustering, anomaly detection, data quality verification, and output generation.

Usage:
    python src/pipeline.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Ensure project root is first on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.discover_datasets import discover_all_raw, save_inventory
from src.build_district_master import build_district_master
from src.ingestion.udise import UDISEIngestor
from src.ingestion.nfhs import NFHSIngestor
from src.ingestion.mgnrega import MGNREGAIngestor
from src.ingestion.boundaries import BoundariesIngestor
from src.features.build_features import build_features
from src.models.cluster import ClusterModel
from src.models.anomaly import AnomalyDetector
from src.validate_data import generate_quality_report, save_quality_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("SAHAAYA_PIPELINE")


def run_pipeline() -> int:
    """Run full automated pipeline."""
    logger.info("=" * 60)
    logger.info("Starting SAHAAYA Automated Processing Pipeline")
    logger.info("=" * 60)

    # 1. Discover raw datasets
    logger.info("Step 1: Discovering files in data/raw/...")
    inventory = discover_all_raw()
    meta_dir = ROOT / "data" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    save_inventory(inventory, meta_dir / "dataset_inventory.json")

    # 2. Build / load canonical district master
    logger.info("Step 2: Ensuring Tamil Nadu canonical district master...")
    master_df = build_district_master()
    logger.info("District master ready with %d canonical districts.", len(master_df))

    # 3. Source Ingestion
    logger.info("Step 3: Running source ingestors...")
    quality_reports = []
    processed_sources = []

    # Ingest UDISE+ (Education)
    try:
        udise_ingestor = UDISEIngestor()
        udise_res = udise_ingestor.run()
        logger.info("UDISE+ ingestion: %s", udise_res.get("status", "unknown"))
        if udise_res.get("status") == "success":
            processed_sources.append("udise")
            clean_df = udise_ingestor.load_cleaned()
            if clean_df is not None:
                quality_reports.append(generate_quality_report(clean_df, "udise"))
    except Exception as e:
        logger.error("Error during UDISE ingestion: %s", e)

    # Ingest NFHS-5 (Healthcare)
    try:
        nfhs_ingestor = NFHSIngestor()
        nfhs_res = nfhs_ingestor.run()
        logger.info("NFHS-5 ingestion: %s", nfhs_res.get("status", "unknown"))
        if nfhs_res.get("status") == "success":
            processed_sources.append("nfhs")
            clean_df = nfhs_ingestor.load_cleaned()
            if clean_df is not None:
                quality_reports.append(generate_quality_report(clean_df, "nfhs"))
    except Exception as e:
        logger.error("Error during NFHS ingestion: %s", e)

    # Ingest MGNREGA (Employment)
    try:
        mgnrega_ingestor = MGNREGAIngestor()
        mgnrega_res = mgnrega_ingestor.run()
        logger.info("MGNREGA ingestion: %s", mgnrega_res.get("status", "unknown"))
        if mgnrega_res.get("status") == "success":
            processed_sources.append("mgnrega")
            clean_df = mgnrega_ingestor.load_cleaned()
            if clean_df is not None:
                quality_reports.append(generate_quality_report(clean_df, "mgnrega"))
    except Exception as e:
        logger.error("Error during MGNREGA ingestion: %s", e)

    # Ingest Boundaries (GeoJSON / Shapefile)
    try:
        boundaries_ingestor = BoundariesIngestor()
        bound_res = boundaries_ingestor.run()
        logger.info("Boundaries ingestion: %s", bound_res.get("status", "unknown"))
        if bound_res.get("status") == "success":
            processed_sources.append("boundaries")
    except Exception as e:
        logger.error("Error during boundaries ingestion: %s", e)

    # 4. Feature Engineering
    logger.info("Step 4: Building combined district feature table...")
    features_df = build_features(master_df=master_df)
    logger.info(
        "Features generated: %d districts, completeness avg: %.2f",
        len(features_df),
        features_df["data_completeness"].mean() if "data_completeness" in features_df.columns else 0.0,
    )
    quality_reports.append(generate_quality_report(features_df, "features_combined"))

    # 5. Machine Learning Models
    features_path = ROOT / "data" / "processed" / "features.parquet"
    if features_df["overall_score"].notna().sum() >= 5:
        logger.info("Step 5A: Fitting K-Means Clustering on district indicators...")
        try:
            cluster_model = ClusterModel(features_path=features_path)
            cluster_model.run()
            logger.info("Clustering completed successfully.")
        except Exception as e:
            logger.warning("Clustering skipped: %s", e)

        logger.info("Step 5B: Fitting Isolation Forest Anomaly Detector...")
        try:
            anomaly_model = AnomalyDetector(features_path=features_path)
            anomaly_model.run()
            logger.info("Anomaly detection completed successfully.")
        except Exception as e:
            logger.warning("Anomaly detection skipped: %s", e)
    else:
        logger.info("Step 5: Insufficient non-NaN feature rows for ML modeling (<5 districts with data).")

    # 6. Quality Reports
    logger.info("Step 6: Writing data quality validation report...")
    if quality_reports:
        rep_path = save_quality_report(quality_reports)
        logger.info("Data quality report saved to: %s", rep_path)

    # Summary
    logger.info("=" * 60)
    logger.info("Pipeline Execution Complete")
    logger.info("Processed Sources: %s", processed_sources or "None (Place raw files to process)")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(run_pipeline())
