# SAHAAYA (सहाय) — National Civic Vulnerability & Early-Warning Observatory

[![CI Pipeline](https://github.com/anish-lab/Sahaaya/actions/workflows/ci.yml/badge.svg)](https://github.com/anish-lab/Sahaaya/actions/workflows/ci.yml)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sahaaya.streamlit.app)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: OGL-India](https://img.shields.io/badge/License-OGL--India-green.svg)](https://data.gov.in/government-open-data-license-india)
[![External Validation](https://img.shields.io/badge/NITI%20Aayog%20MPI%20%CF%81-0.9037-darkgreen.svg)](#1-external-benchmark-validation-niti-aayog-mpi)
[![Code Style: Editorial](https://img.shields.io/badge/UI%20Aesthetic-FT%20%2F%20Economist-warmivory.svg)](#design-system--editorial-craft)

> **Repository Description**: All-India social vulnerability intelligence & early-warning platform synthesizing UDISE+ education telemetry, NFHS-5 healthcare metrics, and civic infrastructure across 36 States/UTs, featuring unsupervised K-Means archetyping, Isolation Forest anomaly attribution, non-causal counterfactual policy simulation, and rigorous empirical validation against NITI Aayog's Multidimensional Poverty Index ($\rho = 0.9037$).  
> **GitHub Topics**: `civic-intelligence`, `social-vulnerability-index`, `data-journalism`, `streamlit`, `udise-plus`, `nfhs-5`, `machine-learning`, `isolation-forest`, `kmeans-clustering`, `india-open-data`, `policy-simulation`

---

## Executive Summary & Dual-Resolution Architecture

SAHAAYA is a public-interest early-warning intelligence system designed for civil servants, policy planners, and data journalists. It evaluates multi-sectoral vulnerability across India through a **dual-resolution architecture**:

```
                              ┌────────────────────────────────────────────────────────┐
                              │            SAHAAYA DUAL-RESOLUTION PLATFORM           │
                              └────────────────────────────────────────────────────────┘
                                                         │
                        ┌────────────────────────────────┴────────────────────────────────┐
                        ▼                                                                 ▼
      ┌───────────────────────────────────┐                             ┌───────────────────────────────────┐
      │     PRODUCTION OBSERVATORY        │                             │       INTRA-STATE PILOT           │
      │  All-India 36 States & UTs Tier   │                             │   Tamil Nadu 38-District Pilot    │
      ├───────────────────────────────────┤                             ├───────────────────────────────────┤
      │ • Full Macro-Comparative Scope    │                             │ • High-Resolution Sub-State Proof │
      │ • UDISE+ 2022-23 (School Infra)   │                             │ • 38 Administrative Districts     │
      │ • NFHS-5 2019-21 (Health/Nutrition│                             │ • Full 4-Pillar Telemetry         │
      │ • 35/36 Standardized GeoJSON Map  │                             │   (Includes Local MGNREGA Wages)  │
      │ • Validated vs NITI Aayog MPI     │                             │ • Granular Boundary Polygons      │
      └───────────────────────────────────┘                             └───────────────────────────────────┘
```

1. **National Macro Observatory (Primary Production System)**:
   - Full census of all **36 States and Union Territories** of India.
   - Synthesizes 16 indicators from **UDISE+ 2022-23** (Ministry of Education) and **NFHS-5 2019-21** (Ministry of Health & Family Welfare).
   - Validated against **NITI Aayog's National Multidimensional Poverty Index (2023)** with a Spearman rank correlation of **$\rho = 0.9037$** ($p = 4.49 \times 10^{-14}$).
2. **Tamil Nadu District-Level Pilot (Granular Intra-State Proof of Concept)**:
   - Granular intra-state pilot across **38 districts** demonstrating high-resolution sub-state drill-downs and localized GeoJSON choropleths (`data/processed/tn_districts.geojson`).
   - Serves as the pilot deployment for local 4-pillar data integration (including localized MGNREGA employment person-day telemetry).

---

## Methodological Rigor & Technical Validation

### 1. External Benchmark Validation (NITI Aayog MPI)
To verify that SAHAAYA's composite vulnerability score measures real-world socioeconomic distress, we benchmarked the index rankings against **NITI Aayog’s National Multidimensional Poverty Index (2023 Progress Report)** across all 36 States/UTs.

- **Spearman Rank Correlation**: **$\rho = 0.9037$** ($p = 4.49 \times 10^{-14}$)
- **Pearson Linear Correlation**: **$r = 0.8883$** ($p = 4.90 \times 10^{-13}$)
- **Construct Validity**: Anchor jurisdictions independently align with official poverty headcount rates:
  - **Lowest Vulnerability**: Kerala (0.55% MPI vs 11.2 SAHAAYA score), Goa (0.84% MPI vs 16.6 SAHAAYA score), Tamil Nadu (2.20% MPI vs 18.9 SAHAAYA score).
  - **Highest Vulnerability**: Bihar (33.76% MPI vs 69.3 SAHAAYA score), Meghalaya (27.79% MPI vs 73.3 SAHAAYA score), Jharkhand (28.81% MPI vs 56.9 SAHAAYA score).

Run validation script:
```bash
python src/evaluation/validate_index.py
```

### 2. Dimension Weights Justification & Sensitivity Analysis
- **Normative Framework**: Following the **Alkire-Foster / Human Development Index (HDI) / NITI Aayog** standard, each dimension (Education, Health, Infrastructure) is initially weighted equally. This reflects the constitutional premise that the rights to schooling, maternal nutrition, and clean water are mutually non-substitutable.
- **Monte Carlo Sensitivity Check**: We ran **1,000 Dirichlet weight simulations** ($\pm 30\%$ random perturbations around equal weighting):
  - **Top-10 Vulnerable Priority List Stability**: **93.6%** mean Jaccard overlap.
  - **Mean Rank Correlation with Baseline**: **$\rho = 0.9812$** (minimum $\rho = 0.8553$ under extreme perturbations).
- **Comparison to Unsupervised PCA Index**:
  - The First Principal Component (PC1) explains **62.0%** of total cross-dimensional variance.
  - The Spearman rank correlation between the normative equal-weight index and an unsupervised data-driven PCA index is **$\rho = 0.9990$**.

Run weight sensitivity analysis:
```bash
python src/evaluation/weight_sensitivity.py
```

### 3. Clustering Rigor & Reproducibility
For an administrative sample of $N = 36$ jurisdictions:
- **Feature Preprocessing**: All 16 numeric indicators are standardized via `StandardScaler` (zero mean, unit variance) so scale differences (e.g. gross enrollment vs percentages) do not bias Euclidean distance.
- **Choice of $k$ (Elbow + Silhouette)**:
  - $k=2$: Inertia = 401.5, Silhouette = 0.263
  - $k=3$: Inertia = 292.8, **Silhouette = 0.290 (Peak)**
  - $k=4$: Inertia = 243.5, Silhouette = 0.266 (Elbow inflection point)
  - $k \ge 5$: Silhouette decays ($< 0.213$), indicating over-partitioning.
- **Cluster Stability Across Random Seeds**: Evaluating $k=4$ across 50 random initializations (seeds 1 to 50) yields a **Mean Adjusted Rand Index (ARI) of 0.838**, proving the archetypes are structurally stable rather than artifacts of random seed selection.

Run clustering diagnostics:
```bash
python -c "from src.models.cluster import ClusterModel; ClusterModel('data/processed/features.parquet').run()"
```

### 4. Isolation Forest: Contamination & Feature Attribution
- **Contamination Prior ($c = 0.11$)**: Deliberately set to $0.11$ ($\approx 4$ out of 36 jurisdictions) to isolate the top decile tail of extreme multi-dimensional distributional decoupling without over-flagging ordinary statistical variance.
- **Outlier Divergence Drivers ($|z| > 1.5$)**:
  - **Meghalaya (Score 100.0)**: Severe physical deficits in school electrification (38.2%) and drinking water (74.7%), low institutional deliveries (58.1%).
  - **Bihar (Score 80.4)**: Extreme pupil-teacher ratio (47:1), elevated child stunting (42.9%), high education risk.
  - **Nagaland (Score 72.8)**: Lowest school piped water coverage (48.4%), exceptionally low institutional births (45.7%).
  - **Jharkhand (Score 53.7)**: Severe coupled human development deficits across stunting (39.6%) and teacher shortages.

### 5. Simulator Honesty: Non-Causal What-If & Uncertainty
- **Methodological Disclaimer**: The counterfactual simulator is explicitly labeled as a **model-based what-if accounting tool, not a causal inference engine** (such as an RCT, Difference-in-Differences, or Instrumental Variable model). It does not model general equilibrium adjustments or behavioral spillovers.
- **Score Recomputation**:
  $$S_i(x_i) = 100 \times \frac{x_i - \min(X_i)}{\max(X_i) - \min(X_i)}$$
  $$D_k = \frac{1}{|I_k|} \sum_{i \in I_k} S_i(x_i), \quad V_{\text{sim}} = \frac{1}{|K_{\text{obs}}|} \sum_{k \in K_{\text{obs}}} D_k$$
- **Uncertainty Bounds**: Every simulated score includes an empirical observational uncertainty band of **$\pm 1.8$ points (95% CI)** based on survey sampling and administrative measurement error.

### 6. Three Verified Pillars & Data Integrity (100% Telemetry)
- **Exclusion of Unharmonized Datasets**: Employment metrics were removed from the production index because open state-level feeds are currently awaiting centralized data.gov.in harmonization.
- **Three Core Statutory Pillars**:
  1. 🎓 **Education Vulnerability (`edu_risk`)**: Pupil-teacher ratios, female literacy rates, schooling 10+ years, and dropout rates (UDISE+).
  2. 🏥 **Healthcare Deficit (`health_risk`)**: Child stunting, wasting, institutional deliveries, and health insurance coverage (NFHS-5).
  3. 🏗️ **Civic Infrastructure (`infra_risk`)**: School electricity, drinking water, sanitation facilities, internet, and computer access (UDISE+).
- **100% Data Completeness**: With all 3 statutory pillars fully verified and present across all 36 States and Union Territories, `data_completeness = 1.0` (100%) with zero missingness and zero synthetic imputation required:
  $$V = \frac{\text{edu\_risk} + \text{health\_risk} + \text{infra\_risk}}{3} \quad (w_{\text{edu}} = w_{\text{health}} = w_{\text{infra}} = 33.33\%)$$

### 7. Collinearity Audit & Circular Leakage Prevention
- **Collinear Feature Pairs ($|r| \ge 0.70$)**:
  - `schools_with_electricity_pct` $\leftrightarrow$ `schools_with_drinking_water_pct`: $r = 0.813$
  - `schools_with_internet_pct` $\leftrightarrow$ `schools_with_computers_pct`: $r = 0.822$
  - `schools_with_drinking_water_pct` $\leftrightarrow$ `institutional_births_pct`: $r = 0.762$
  - `schools_with_electricity_pct` $\leftrightarrow$ `schools_with_toilets_pct`: $r = 0.725$
- **Circular Leakage Guardrail**: Because the composite index is a deterministic weighted linear combination of normalized indicators, training a predictive model or SHAP explainer to predict `overall_score` directly from these same sub-indicators would produce a tautological $R^2 \approx 1.0$ identity with circular explanations. In SAHAAYA, machine learning is restricted to unsupervised discovery (clustering, isolation forest), and policy what-ifs use transparent mathematical sensitivity accounting.

Run collinearity audit:
```bash
python src/evaluation/correlation_leakage.py
```

---

## Dashboard Pages & Features

| Page | File | Core Functionality | Key Visualizations |
|---|---|---|---|
| **Overview** | [`app/Home.py`](app/Home.py) | All-India vulnerability census across 36 States/UTs | GeoJSON Choropleth map, NITI Aayog MPI validation scatter, bi-axial sectoral correlation |
| **State Dossier** | [`app/pages/1_State.py`](app/pages/1_State.py) | In-depth State & UT drilldown | Dimensional benchmark overlay bars, typology peer cards, telemetry ledger |
| **Clusters** | [`app/pages/2_Clusters.py`](app/pages/2_Clusters.py) | Unsupervised socioeconomic archetypes | 2D PCA latent biplot, Elbow & Silhouette curves, policy playbooks |
| **Anomalies** | [`app/pages/3_Anomalies.py`](app/pages/3_Anomalies.py) | Multi-variate outlier detection | Decision score distribution, outlier vs national mean bar comparison, divergence ledger |
| **Simulator** | [`app/pages/4_Simulator.py`](app/pages/4_Simulator.py) | Interactive what-if policy explorer | Rapid preset scenarios, parameter sliders, before/after scorecard with $\pm 1.8$ pt CI |

---

## Design System & Editorial Craft

SAHAAYA avoids generic "AI SaaS" templates (purple gradients, glowing cards, neon accents) in favor of a restrained, human, editorial aesthetic inspired by data desks at the *Financial Times*, *The Economist*, and *The New York Times*:
- **Color Palette**: Warm ivory canvas (`#F7F5EE`), deep forest green structure (`#14241D` / `#223B2F`), hairline rules (`#E2DED4`), and restrained risk tokens (Low `#EAEFEA`, Moderate `#F5F3E4`, High `#FAEDE3`, Critical `#F7E5DE`).
- **Typography**: Newsreader (editorial headlines & large tabular numbers), IBM Plex Sans (body copy & controls), and IBM Plex Mono (telemetry codes & folio metadata).
- **Cartography**: Clean discrete risk bins, thin state boundaries, and official survey alignment notes.
- **Micro-Interactions**: Subtle physical transitions (140ms ease-out), dark ink hover states, and WCAG AA contrast.

---

## Quick Start & Installation

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/anish-lab/Sahaaya.git
cd Sahaaya

python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
```

### 2. Verify Canonical Jurisdictions & Run Pipeline
```bash
# Verify 36 Canonical States/UTs and Tamil Nadu District pilot master
python src/build_district_master.py

# Preprocess GeoJSON boundary geometries
python src/preprocessing/prepare_boundaries.py

# Execute the core ingestion & feature compilation pipeline
python src/pipeline.py

# Run benchmark validation, weight sensitivity & diagnostic checks
python src/evaluation/validate_index.py
python src/evaluation/weight_sensitivity.py
python src/evaluation/correlation_leakage.py
```

### 3. Launch the Dashboard
```bash
streamlit run app/Home.py
# or
python run_app.py
```
Open **http://localhost:8501** in your browser.

### 4. Run Test Suite
```bash
pytest -v
```
All **29 unit and integration tests** verify data validation, canonical fuzzy matching, index mathematical bounds, cluster stability, Isolation Forest calibration, and NITI Aayog benchmark alignment.

---

## Project Structure

```
Sahaaya/
├── .github/
│   └── workflows/
│       └── ci.yml                     # Automated GitHub Actions test pipeline
├── app/
│   ├── Home.py                        # National Observatory & NITI MPI validation
│   ├── ui_theme.py                    # FT/Economist editorial design tokens & CSS
│   ├── utils.py                       # Cached data loaders & GeoJSON bounds
│   └── pages/
│       ├── 1_State.py              # Jurisdictional dossier & missingness note
│       ├── 2_Clusters.py              # Field guide, PCA biplot & cluster rigor
│       ├── 3_Anomalies.py             # Isolation Forest registry & attribution
│       └── 4_Simulator.py             # Non-causal what-if explorer & ±1.8 pt CI
├── data/
│   ├── raw/                           # Official UDISE+, NFHS-5, boundary sources
│   ├── interim/                       # Cleaned source tables
│   ├── processed/                     # Production features.parquet & GeoJSONs
│   └── metadata/                      # Validation, diagnostics & inventory JSONs
├── docs/
│   ├── contract.md                    # Data schema & inter-module contract
│   └── data_sources.md                # Official data.gov.in provenance links
├── models/                            # Serialized model artifacts (.pkl)
├── reports/
│   └── data_quality_report.md         # Ingestion missingness & validation logs
├── src/
│   ├── build_district_master.py       # 36 States/UTs & TN pilot master lists
│   ├── pipeline.py                    # Master data processing pipeline
│   ├── ingestion/                     # UDISE+ and NFHS-5 data parsers
│   ├── features/                      # Min-max normalization & composite scoring
│   ├── models/                        # Clustering, Isolation Forest, Simulator
│   ├── preprocessing/                 # Cleaning, standardization, GeoJSON prep
│   └── evaluation/                    # NITI MPI validation, sensitivity & leakage
└── tests/
    ├── conftest.py                    # Test fixtures & mocks
    ├── test_all.py                    # 25 core pipeline, model & index tests
    ├── test_setup.py                  # Directory structure tests
    └── test_validation_benchmark.py   # Benchmark, sensitivity & leakage tests
```

---

## Methodological Limitations & Governance

1. **Constructed Analytical Prioritization**: The SAHAAYA index is an administrative decision-support construct for macro fiscal and programmatic allocation. It is not an individual or clinical diagnostic measure.
2. **Survey Sampling vs Administrative Census**: NFHS-5 reflects a multi-stage stratified sample survey (2019-21), whereas UDISE+ reflects an annual school administrative census (2022-23). Inter-temporal differences reflect standard publication cycles of the respective union ministries.
3. **Non-Causal Counterfactuals**: Simulated indicator shifts demonstrate normative index elasticities, not causal counterfactual treatments.
4. **Missing Dimension Treatment**: Missing pillars are not imputed with synthetic values; the index dynamically renormalizes across observed dimensions ($w_d = 1/3$).

---

## License & Data Provenance

- Datasets sourced under the [Open Government Data License - India](https://data.gov.in/government-open-data-license-india).
- Built with Python 3.9+, Streamlit 1.50, Plotly 7.1, Scikit-Learn, and Pandas.
