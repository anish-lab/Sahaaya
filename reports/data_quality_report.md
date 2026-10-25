# SAHAAYA Data Quality & Validation Report

This report is generated automatically by the pipeline during each run.

## Dataset Source: UDISE
- **Total Records**: 36
- **Duplicate District Rows**: 0

### Column Missingness
| Column | Missing (%) |
|---|---|
| `district_id` | 0.0% |
| `district_name` | 0.0% |
| `state` | 0.0% |
| `schools_with_electricity_pct` | 0.0% |
| `schools_with_drinking_water_pct` | 0.0% |
| `schools_with_toilets_pct` | 0.0% |
| `schools_with_internet_pct` | 0.0% |
| `schools_with_computers_pct` | 0.0% |
| `enrolment` | 0.0% |
| `pupil_teacher_ratio` | 0.0% |
| `period` | 0.0% |

### Detected Outliers (>3 Std Dev)
- `schools_with_electricity_pct`: 1 extreme values
- `schools_with_drinking_water_pct`: 2 extreme values
- `enrolment`: 1 extreme values

## Dataset Source: NFHS
- **Total Records**: 36
- **Duplicate District Rows**: 0

### Column Missingness
| Column | Missing (%) |
|---|---|
| `district_id` | 0.0% |
| `district_name` | 0.0% |
| `state` | 0.0% |
| `stunting_pct` | 0.0% |
| `wasting_pct` | 0.0% |
| `institutional_births_pct` | 0.0% |
| `health_insurance_pct` | 0.0% |
| `schooling_10plus_pct` | 0.0% |

### Detected Outliers (>3 Std Dev)
- `institutional_births_pct`: 1 extreme values

## Dataset Source: FEATURES_COMBINED
- **Total Records**: 36
- **Duplicate District Rows**: 0

### Column Missingness
| Column | Missing (%) |
|---|---|
| `district_id` | 0.0% |
| `district_name` | 0.0% |
| `state` | 0.0% |
| `schools_with_electricity_pct` | 0.0% |
| `schools_with_drinking_water_pct` | 0.0% |
| `schools_with_toilets_pct` | 0.0% |
| `schools_with_internet_pct` | 0.0% |
| `schools_with_computers_pct` | 0.0% |
| `enrolment` | 0.0% |
| `pupil_teacher_ratio` | 0.0% |
| `period` | 0.0% |
| `stunting_pct` | 0.0% |
| `wasting_pct` | 0.0% |
| `institutional_births_pct` | 0.0% |
| `health_insurance_pct` | 0.0% |
| `schooling_10plus_pct` | 0.0% |
| `edu_risk` | 0.0% |
| `health_risk` | 0.0% |
| `emp_risk` | 100.0% |
| `infra_risk` | 0.0% |
| `overall_score` | 0.0% |
| `risk_band` | 0.0% |
| `data_completeness` | 0.0% |

### Detected Outliers (>3 Std Dev)
- `schools_with_electricity_pct`: 1 extreme values
- `schools_with_drinking_water_pct`: 2 extreme values
- `enrolment`: 1 extreme values
- `institutional_births_pct`: 1 extreme values
- `infra_risk`: 1 extreme values
