from __future__ import annotations

"""
build_district_master.py — Canonical India State & Union Territory Master (36 States/UTs).

Provides reference list of all 28 States and 8 Union Territories of India with
standard identifiers, comprehensive spelling variants/aliases, and fuzzy matching fallback.
"""

import sys
import json
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    import difflib
    HAS_RAPIDFUZZ = False

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# 36 Canonical States and Union Territories of India
# ---------------------------------------------------------------------------
CANONICAL_STATES: list[dict] = [
    {"state_id": "IN-AN", "state_name": "Andaman and Nicobar Islands", "type": "UT"},
    {"state_id": "IN-AP", "state_name": "Andhra Pradesh", "type": "State"},
    {"state_id": "IN-AR", "state_name": "Arunachal Pradesh", "type": "State"},
    {"state_id": "IN-AS", "state_name": "Assam", "type": "State"},
    {"state_id": "IN-BR", "state_name": "Bihar", "type": "State"},
    {"state_id": "IN-CH", "state_name": "Chandigarh", "type": "UT"},
    {"state_id": "IN-CG", "state_name": "Chhattisgarh", "type": "State"},
    {"state_id": "IN-DH", "state_name": "Dadra and Nagar Haveli and Daman and Diu", "type": "UT"},
    {"state_id": "IN-DL", "state_name": "Delhi", "type": "UT"},
    {"state_id": "IN-GA", "state_name": "Goa", "type": "State"},
    {"state_id": "IN-GJ", "state_name": "Gujarat", "type": "State"},
    {"state_id": "IN-HR", "state_name": "Haryana", "type": "State"},
    {"state_id": "IN-HP", "state_name": "Himachal Pradesh", "type": "State"},
    {"state_id": "IN-JK", "state_name": "Jammu and Kashmir", "type": "UT"},
    {"state_id": "IN-JH", "state_name": "Jharkhand", "type": "State"},
    {"state_id": "IN-KA", "state_name": "Karnataka", "type": "State"},
    {"state_id": "IN-KL", "state_name": "Kerala", "type": "State"},
    {"state_id": "IN-LA", "state_name": "Ladakh", "type": "UT"},
    {"state_id": "IN-LD", "state_name": "Lakshadweep", "type": "UT"},
    {"state_id": "IN-MP", "state_name": "Madhya Pradesh", "type": "State"},
    {"state_id": "IN-MH", "state_name": "Maharashtra", "type": "State"},
    {"state_id": "IN-MN", "state_name": "Manipur", "type": "State"},
    {"state_id": "IN-ML", "state_name": "Meghalaya", "type": "State"},
    {"state_id": "IN-MZ", "state_name": "Mizoram", "type": "State"},
    {"state_id": "IN-NL", "state_name": "Nagaland", "type": "State"},
    {"state_id": "IN-OD", "state_name": "Odisha", "type": "State"},
    {"state_id": "IN-PY", "state_name": "Puducherry", "type": "UT"},
    {"state_id": "IN-PB", "state_name": "Punjab", "type": "State"},
    {"state_id": "IN-RJ", "state_name": "Rajasthan", "type": "State"},
    {"state_id": "IN-SK", "state_name": "Sikkim", "type": "State"},
    {"state_id": "IN-TN", "state_name": "Tamil Nadu", "type": "State"},
    {"state_id": "IN-TS", "state_name": "Telangana", "type": "State"},
    {"state_id": "IN-TR", "state_name": "Tripura", "type": "State"},
    {"state_id": "IN-UP", "state_name": "Uttar Pradesh", "type": "State"},
    {"state_id": "IN-UK", "state_name": "Uttarakhand", "type": "State"},
    {"state_id": "IN-WB", "state_name": "West Bengal", "type": "State"},
]

# For backwards compatibility with district contract column names
CANONICAL_DISTRICTS = [
    {
        "district_id": s["state_id"],
        "district_name": s["state_name"],
        "state": s["state_name"],
        "type": s["type"]
    }
    for s in CANONICAL_STATES
]

# ---------------------------------------------------------------------------
# Comprehensive Aliases for Indian States and UTs
# ---------------------------------------------------------------------------
STATE_ALIASES: dict[str, list[str]] = {
    "Andaman and Nicobar Islands": [
        "Andaman & Nicobar Islands", "A & N Islands", "Andaman and Nicobar", "A and N Islands"
    ],
    "Andhra Pradesh": ["AP", "Andhra"],
    "Arunachal Pradesh": ["Arunachal"],
    "Assam": ["Asom"],
    "Bihar": [],
    "Chandigarh": ["CHD"],
    "Chhattisgarh": ["Chhatisgarh", "Chattisgarh", "CG"],
    "Dadra and Nagar Haveli and Daman and Diu": [
        "D&N Haveli and Daman & Diu", "Dadra and Nagar Haveli & Daman and Diu",
        "Daman and Diu", "Dadra and Nagar Haveli", "Daman & Diu", "DNHDD",
        "The Dadra And Nagar Haveli And Daman And Diu", "Dadra & Nagar Haveli"
    ],
    "Delhi": [
        "NCT of Delhi", "National Capital Territory of Delhi", "Delhi (UT)", "NCT OF DELHI"
    ],
    "Goa": [],
    "Gujarat": ["Gujrat"],
    "Haryana": [],
    "Himachal Pradesh": ["Himachal", "HP"],
    "Jammu and Kashmir": ["Jammu & Kashmir", "J&K", "Jammu and Kashmir (UT)"],
    "Jharkhand": [],
    "Karnataka": [],
    "Kerala": [],
    "Ladakh": ["Ladakh (UT)"],
    "Lakshadweep": ["Lakshadweep (UT)"],
    "Madhya Pradesh": ["MP"],
    "Maharashtra": ["Maha"],
    "Manipur": [],
    "Meghalaya": [],
    "Mizoram": [],
    "Nagaland": [],
    "Odisha": ["Orissa"],
    "Puducherry": ["Pondicherry", "Pondicherry (UT)"],
    "Punjab": [],
    "Rajasthan": ["Raj"],
    "Sikkim": [],
    "Tamil Nadu": ["Tamilnadu", "TN"],
    "Telangana": ["Telengana", "TG", "TS"],
    "Tripura": [],
    "Uttar Pradesh": ["UP"],
    "Uttarakhand": ["Uttaranchal", "UK", "UT"],
    "West Bengal": ["Bengal", "WB"],
}


def build_district_master() -> pd.DataFrame:
    """Return DataFrame with all 36 Indian States & UTs."""
    return pd.DataFrame(CANONICAL_DISTRICTS)


build_master = build_district_master


def _build_lookup() -> dict[str, tuple[str, str]]:
    """Build case-insensitive lookup."""
    lookup: dict[str, tuple[str, str]] = {}
    for rec in CANONICAL_DISTRICTS:
        lookup[rec["district_name"].lower()] = (rec["district_id"], rec["district_name"])
    for canonical, aliases in STATE_ALIASES.items():
        did = next(r["district_id"] for r in CANONICAL_DISTRICTS if r["district_name"] == canonical)
        for alias in aliases:
            lookup[alias.lower()] = (did, canonical)
    return lookup


_LOOKUP = _build_lookup()
_ALL_NAMES = list(_LOOKUP.keys())


def match_district(name: str, threshold: int = 80) -> Optional[tuple[str, str, str, float]]:
    """Match an input State / UT name to the canonical master."""
    if not name or not isinstance(name, str):
        return None

    cleaned = " ".join(name.strip().split()).lower()

    # Skip total rows
    if any(tot in cleaned for tot in ["all india", "total", "india", "overall", "national total"]):
        return None

    # 1. Exact match
    for rec in CANONICAL_DISTRICTS:
        if rec["district_name"].lower() == cleaned:
            return (rec["district_id"], rec["district_name"], "exact", 100.0)

    # 2. Alias match
    if cleaned in _LOOKUP:
        did, canonical = _LOOKUP[cleaned]
        return (did, canonical, "alias", 100.0)

    # 3. Fuzzy match
    if HAS_RAPIDFUZZ:
        result = process.extractOne(cleaned, _ALL_NAMES, scorer=fuzz.WRatio, score_cutoff=threshold)
        if result is not None:
            matched_name, score, _ = result
            did, canonical = _LOOKUP[matched_name]
            return (did, canonical, "fuzzy", float(score))
    else:
        best_name = None
        best_score = 0.0
        for cand in _ALL_NAMES:
            ratio = difflib.SequenceMatcher(None, cleaned, cand).ratio() * 100.0
            if ratio > best_score:
                best_score = ratio
                best_name = cand
        if best_score >= threshold and best_name is not None:
            did, canonical = _LOOKUP[best_name]
            return (did, canonical, "fuzzy", float(best_score))

    return None


def match_districts_bulk(names_series: pd.Series) -> pd.DataFrame:
    """Batch-match Series of State/UT names."""
    results = []
    for raw_name in names_series:
        m = match_district(str(raw_name) if pd.notna(raw_name) else "")
        if m:
            results.append({
                "original_name": raw_name,
                "district_id": m[0],
                "canonical_name": m[1],
                "match_type": m[2],
                "score": m[3],
            })
        else:
            results.append({
                "original_name": raw_name,
                "district_id": None,
                "canonical_name": None,
                "match_type": "unmatched",
                "score": 0.0,
            })
    return pd.DataFrame(results)


def save_master(df: pd.DataFrame | None = None) -> Path:
    """Save master to parquet and json."""
    if df is None:
        df = build_district_master()
    out_dir = ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = out_dir / "district_master.parquet"
    df.to_parquet(parquet_path, index=False)

    meta_dir = ROOT / "data" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    with open(meta_dir / "state_aliases.json", "w", encoding="utf-8") as f:
        json.dump(STATE_ALIASES, f, indent=2)

    return parquet_path


if __name__ == "__main__":
    p = save_master()
    print(f"Saved State/UT Master with {len(CANONICAL_STATES)} states to {p}")
