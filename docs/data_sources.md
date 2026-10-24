# SAHAAYA — Data Sources

## Official Government Datasets

### Dataset A — Education: UDISE+

| Field           | Value |
|-----------------|-------|
| **Title**       | Unified District Information System for Education Plus (UDISE+) |
| **Organization**| Ministry of Education, Government of India |
| **URL**         | https://www.data.gov.in/catalog/unified-district-information-system-education-plus-udise-plus |
| **Alt URL**     | https://www.data.gov.in/dataset-group-name/Unified%20district%20information%20system%20for%20education |
| **Format**      | CSV / XLSX (varies by resource) |
| **Coverage**    | District-level, all India |
| **Period**      | Varies by academic year (e.g. 2021-22) |
| **Indicators**  | Enrolment, dropout rates, teacher counts, pupil-teacher ratio, school infrastructure (electricity, toilets, drinking water, internet) |
| **Destination** | `data/raw/udise/` |

---

### Dataset B — Healthcare: NFHS-5

| Field           | Value |
|-----------------|-------|
| **Title**       | National Family Health Survey 5 (NFHS-5) District Factsheet Data |
| **Organization**| Ministry of Health & Family Welfare / IIPS |
| **URL**         | https://www.data.gov.in/catalog/national-family-health-survey-5-nfhs-5-india-districts-factsheet-data-provisional |
| **Format**      | CSV / XLSX |
| **Coverage**    | District-level, all India |
| **Period**      | 2019-21 (single survey round, NOT annual) |
| **Indicators**  | Child stunting, wasting, anaemia, institutional births, vaccination, healthcare access, sanitation |
| **Destination** | `data/raw/nfhs/` |

> **Note**: NFHS-5 is a single survey round (2019-21). Do NOT manufacture annual time-series from it.

---

### Dataset C — Employment: MGNREGA

| Field           | Value |
|-----------------|-------|
| **Title**       | District-wise MGNREGA data at a Glance |
| **Organization**| Ministry of Rural Development, Government of India |
| **URL**         | https://www.data.gov.in/resource/district-wise-mgnrega-data-glance |
| **Format**      | CSV / XLSX |
| **Coverage**    | District-level, all India |
| **Period**      | Financial year (varies) |
| **Indicators**  | Households employed, households demanding employment, person-days, employment fulfilment rate, women participation |
| **Destination** | `data/raw/mgnrega/` |

---

### Dataset D — District Boundaries (GeoJSON / Shapefile)

| Field           | Value |
|-----------------|-------|
| **Title**       | Administrative Boundaries of India |
| **Organization**| Survey of India / data.gov.in |
| **URL**         | https://www.data.gov.in/catalog/admin-boundaries |
| **Format**      | GeoJSON / Shapefile (ZIP) |
| **Coverage**    | District-level boundaries |
| **Destination** | `data/raw/boundaries/` |

> **Note**: District boundary vintages may not match all reporting years. Verify coverage before using.

---

## Provenance Rules

1. **Raw files are immutable.** Never modify downloaded files.
2. **Record download date** when placing files.
3. **Verify URLs** — links may change over time.
4. **Check licensing** — data.gov.in datasets are under OGDL (Open Government Data License).
5. **Do not commit raw data** to git (gitignored by default).
