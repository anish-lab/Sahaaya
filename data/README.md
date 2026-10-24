# Data Directory — SAHAAYA

## Folder Structure

### `raw/` — Original downloaded files (NEVER modify these)

| Subfolder       | Dataset                       | Source                  |
|-----------------|-------------------------------|-------------------------|
| `udise/`        | UDISE+ education indicators   | data.gov.in / UDISE+    |
| `nfhs/`         | NFHS-5 health indicators      | data.gov.in / NFHS      |
| `mgnrega/`      | MGNREGA employment data       | data.gov.in / MGNREGA   |
| `boundaries/`   | District boundary geometries  | data.gov.in / Survey of India |
| `additional/`   | Supplementary datasets        | Various                 |

> **Rule**: Drop downloaded files directly into the appropriate subfolder.
> The pipeline auto-discovers files by scanning these folders — no renaming needed.

### `interim/` — Intermediate processing outputs

Per-source cleaned and standardized tables produced by the ingestion pipeline.
These are regenerated every time you run `src/pipeline.py`.

### `processed/` — Final analysis-ready datasets

| File                        | Description                                |
|-----------------------------|--------------------------------------------|
| `district_master.parquet`   | Canonical district list with IDs & aliases |
| `udise_clean.parquet`       | Cleaned education indicators               |
| `nfhs_clean.parquet`        | Cleaned health indicators                  |
| `mgnrega_clean.parquet`     | Cleaned employment indicators              |
| `features.parquet`          | Combined feature table for all districts   |
| `cluster_assignments.parquet` | Cluster memberships                      |
| `cluster_profiles.parquet`  | Cluster summary profiles                   |
| `anomaly_results.parquet`   | Anomaly flags and scores                   |
| `predictions.parquet`       | Forecasted scores (when model is available)|
| `shap_values.parquet`       | SHAP explanations (when available)         |

### `metadata/` — Provenance and quality tracking

| File                      | Description                        |
|---------------------------|------------------------------------|
| `dataset_inventory.json`  | Machine-readable source inventory  |

## Rules

1. **Never modify files in `raw/`** — they are the immutable source of truth.
2. All pipeline outputs go to `interim/` or `processed/`.
3. Running `python src/pipeline.py` regenerates everything from `raw/`.
4. **Do not commit large raw files to git** — they are gitignored.
5. Processed parquet files are also gitignored; regenerate them via the pipeline.
