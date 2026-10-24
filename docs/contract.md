# features.parquet contract (agree with Person A on Day 1)
One row per (district_id, year).
district_id, district_name, state, year,
<raw indicator columns...>,
edu_risk, health_risk, emp_risk, infra_risk   (0-100, higher = worse)
overall_score (0-100), risk_band (Low/Moderate/High/Critical),
cluster (int), anomaly_flag (bool), pred_next_score (float)
Later: shap_values.parquet -> district_id, year, feature, shap_value