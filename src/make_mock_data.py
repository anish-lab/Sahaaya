"""Generates a MOCK features.parquet so the app can be built before real data exists.
Run:  python src/make_mock_data.py
Schema = the contract agreed with Person A. Replace the file with the real one on Day 4.
"""
import numpy as np, pandas as pd
from pathlib import Path

TN_DISTRICTS = [
    "Ariyalur","Chengalpattu","Chennai","Coimbatore","Cuddalore","Dharmapuri","Dindigul","Erode",
    "Kallakurichi","Kancheepuram","Kanyakumari","Karur","Krishnagiri","Madurai","Mayiladuthurai",
    "Nagapattinam","Namakkal","Nilgiris","Perambalur","Pudukkottai","Ramanathapuram","Ranipet",
    "Salem","Sivagangai","Tenkasi","Thanjavur","Theni","Thoothukudi","Tiruchirappalli","Tirunelveli",
    "Tirupathur","Tiruppur","Tiruvallur","Tiruvannamalai","Tiruvarur","Vellore","Viluppuram","Virudhunagar",
]
YEARS = [2021, 2022, 2023]
rng = np.random.default_rng(42)

rows = []
for i, name in enumerate(TN_DISTRICTS):
    base = rng.uniform(20, 80, size=4)
    for y in YEARS:
        drift = (y - YEARS[0]) * rng.normal(0, 2, size=4)
        s = np.clip(base + drift + rng.normal(0, 3, size=4), 0, 100)
        rows.append(dict(
            district_id=f"TN{i+1:02d}", district_name=name, state="Tamil Nadu", year=y,
            dropout_rate=s[0] * 0.2, anaemia_pct=20 + s[1] * 0.4,
            mgnrega_persondays_per_hh=60 - s[2] * 0.4, school_infra_score=100 - s[3],
            edu_risk=s[0], health_risk=s[1], emp_risk=s[2], infra_risk=s[3],
        ))

df = pd.DataFrame(rows)
df["overall_score"] = df[["edu_risk", "health_risk", "emp_risk", "infra_risk"]].mean(axis=1)
df["risk_band"] = pd.cut(df["overall_score"], [-1, 35, 50, 65, 101],
                         labels=["Low", "Moderate", "High", "Critical"]).astype(str)
df["cluster"] = rng.integers(0, 4, len(df))
df["anomaly_flag"] = rng.random(len(df)) < 0.07
df["pred_next_score"] = (df["overall_score"] + rng.normal(0, 3, len(df))).clip(0, 100)

Path("data/processed").mkdir(parents=True, exist_ok=True)
df.to_parquet("data/processed/features.parquet", index=False)
print(df.shape); print(df.head())