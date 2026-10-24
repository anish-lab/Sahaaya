# SAHAAYA — AI-Powered Social Vulnerability & Early-Warning System

> District-level social vulnerability intelligence platform for Tamil Nadu, India.

## Overview

SAHAAYA evaluates **social vulnerability** across Indian districts using four core dimensions:

| Dimension       | Source Dataset | Indicators |
|-----------------|---------------|------------|
| 🎓 Education    | UDISE+        | Dropout rates, PTR, school infrastructure |
| 🏥 Healthcare   | NFHS-5        | Stunting, anaemia, vaccination, institutional births |
| 💼 Employment   | MGNREGA       | Person-days, employment fulfilment, women participation |
| 🏗️ Infrastructure | UDISE+       | Electricity, toilets, drinking water, internet in schools |

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# pip install -r requirements.txt
```

### 2. Setup Project Structure

```bash
python src/setup_project.py
```

### 3. Download & Place Datasets

See [docs/data_sources.md](docs/data_sources.md) for official download links.

| Dataset   | Download From | Place In |
|-----------|--------------|----------|
| UDISE+    | [data.gov.in](https://www.data.gov.in/catalog/unified-district-information-system-education-plus-udise-plus) | `data/raw/udise/` |
| NFHS-5    | [data.gov.in](https://www.data.gov.in/catalog/national-family-health-survey-5-nfhs-5-india-districts-factsheet-data-provisional) | `data/raw/nfhs/` |
| MGNREGA   | [data.gov.in](https://www.data.gov.in/resource/district-wise-mgnrega-data-glance) | `data/raw/mgnrega/` |
| Boundaries| [data.gov.in](https://www.data.gov.in/catalog/admin-boundaries) | `data/raw/boundaries/` |

### 4. Run the Pipeline

```bash
python src/pipeline.py
```

### 5. Launch the Dashboard

```bash
streamlit run app/Home.py
# or
python run_app.py
```

## Project Structure

```
sahaaya/
├── run_app.py                  # Streamlit launcher
├── requirements.txt            # Python dependencies
├── data/
│   ├── raw/                    # Downloaded government datasets (gitignored)
│   ├── interim/                # Cleaned per-source tables
│   ├── processed/              # Final analysis-ready outputs
│   └── metadata/               # Provenance and inventories
├── models/                     # Saved ML model artifacts
├── reports/                    # Generated quality and evaluation reports
├── docs/
│   ├── contract.md             # Data schema contract
│   └── data_sources.md         # Official dataset documentation
├── src/
│   ├── setup_project.py        # Project directory setup
│   ├── discover_datasets.py    # Auto-discover raw files
│   ├── validate_data.py        # Data validation framework
│   ├── build_district_master.py# Canonical TN district list
│   ├── pipeline.py             # Main data processing pipeline
│   ├── ingestion/              # Source-specific data loaders
│   ├── preprocessing/          # Cleaning and standardization
│   ├── features/               # Feature engineering & vulnerability index
│   ├── models/                 # ML models (clustering, anomaly, simulator)
│   └── evaluation/             # Model evaluation utilities
├── tests/                      # Automated tests
└── app/
    ├── Home.py                 # Main dashboard
    ├── utils.py                # Shared utilities
    └── pages/
        ├── 1_District.py       # District drill-down
        ├── 2_Clusters.py       # Cluster analysis
        ├── 3_Anomalies.py      # Anomaly detection results
        └── 4_Simulator.py      # What-if scenario explorer
```

## ML Components

- **Vulnerability Index**: Composite scoring across 4 dimensions (0–100, higher = worse)
- **K-Means Clustering**: Groups districts by socioeconomic similarity
- **Isolation Forest**: Detects unusual indicator patterns
- **What-If Simulator**: Hypothetical scenario analysis
- **SHAP Explanations**: Feature attribution (when predictive model available)

## Data Contract

See [docs/contract.md](docs/contract.md) for the agreed schema between Person A (education, health, prediction, SHAP) and Person B (MGNREGA, clustering, anomaly, dashboard, simulator).

## Limitations

- Vulnerability scores are **constructed analytical measures**, not ground truth.
- NFHS-5 is a single survey round (2019-21) — not annual data.
- Clustering and anomaly results are **descriptive**, not causal.
- The simulator produces **hypothetical estimates**, not guaranteed outcomes.
- District boundary vintages may not match all reporting years.

## License

Data sourced under [Open Government Data License - India](https://data.gov.in/government-open-data-license-india).
