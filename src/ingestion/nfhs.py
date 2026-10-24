from __future__ import annotations

"""
ingestion.nfhs — NFHS-5 health data ingestor.

Reads raw NFHS-5 district factsheet data from ``data/raw/nfhs/``, maps
indicators (stunting, wasting, anaemia, institutional births, vaccination, health insurance),
aggregates across districts to State/UT level, matches States/UTs to the canonical master,
and saves cleaned output.
"""

import sys
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ingestion.base import BaseIngestor, read_any_tabular
from src.preprocessing.clean import (
    parse_numeric,
    standardize_column_names,
    remove_aggregate_rows,
)
from src.preprocessing.standardize import apply_canonical_mapping
from src.build_district_master import build_district_master

COLUMN_PATTERNS: dict[str, list[str]] = {
    "stunting_pct": [
        "stunted", "stunting",
    ],
    "wasting_pct": [
        "wasted", "wasting",
    ],
    "anaemia_children_pct": [
        "children age 6-59 months who are anaemic", "anaemic_children",
    ],
    "anaemia_women_pct": [
        "women age 15-49 years who are anaemic", "anaemic_women",
    ],
    "institutional_births_pct": [
        "institutional births (in the 5 years", "institutional_births", "institutional_birth",
    ],
    "full_vaccination_pct": [
        "fully vaccinated", "full_vaccination", "full_immunization",
    ],
    "health_insurance_pct": [
        "health insurance", "health_insurance",
    ],
}

STATE_COL_PATTERNS = ["state_ut", "states_uts", "state/ut", "state_name", "state", "statename"]
DISTRICT_COL_PATTERNS = ["district_names", "district_name", "district", "dist_name"]


class NFHSIngestor(BaseIngestor):
    """Ingest and clean NFHS-5 health data for States and UTs."""

    SOURCE = "nfhs"
    OUTPUT_FILE = "nfhs_clean.parquet"

    def __init__(self, root: Path | None = None):
        super().__init__(root or ROOT)
        self.source_dir = self.raw_dir / self.SOURCE

    def discover(self) -> list[Path]:
        exts = {".csv", ".xlsx", ".xls", ".parquet"}
        if not self.source_dir.exists():
            return []
        files = [
            f
            for f in sorted(self.source_dir.rglob("*"))
            if f.is_file() and f.suffix.lower() in exts and not f.name.startswith(".")
        ]
        print(f"[NFHS] Discovered {len(files)} file(s) in {self.source_dir}")
        return files

    def inspect(self, filepath: Path) -> dict:
        df = read_any_tabular(filepath)
        return {
            "file": filepath.name,
            "shape": df.shape,
            "columns": list(df.columns),
        }

    def _auto_map_columns(self, df: pd.DataFrame) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for std_name, patterns in COLUMN_PATTERNS.items():
            for col in df.columns:
                col_lower = str(col).lower()
                if any(pat in col_lower for pat in patterns):
                    mapping[col] = std_name
                    break
        return mapping

    def _find_col(self, df: pd.DataFrame, patterns: list[str]) -> Optional[str]:
        for col in df.columns:
            cl = str(col).lower().replace(" ", "_")
            if any(p in cl for p in patterns):
                return col
        return None

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = standardize_column_names(df)
        df["period"] = "NFHS-5 (2019-21)"

        col_map = self._auto_map_columns(df)
        df = df.rename(columns=col_map)

        for std_col in COLUMN_PATTERNS.keys():
            if std_col in df.columns:
                df[std_col] = parse_numeric(df[std_col])

        # Compute composite anaemia if constituent available
        if "anaemia_children_pct" in df.columns and "anaemia_women_pct" in df.columns:
            df["anaemia_pct"] = df[["anaemia_children_pct", "anaemia_women_pct"]].mean(axis=1).round(1)

        return df

    def validate(self, df: pd.DataFrame) -> dict:
        return {
            "source": self.SOURCE,
            "row_count": len(df),
            "columns": list(df.columns),
        }

    def load(self) -> Optional[pd.DataFrame]:
        files = self.discover()
        if not files:
            print("[NFHS] No raw files found. Skipping.")
            return None

        master = build_district_master()
        merged_df = master[["district_id", "district_name", "state"]].copy()

        for fp in files:
            try:
                df = read_any_tabular(fp)
                print(f"[NFHS] Read {fp.name}: {df.shape}")
                df = self.clean(df)

                state_col = self._find_col(df, STATE_COL_PATTERNS)
                if state_col:
                    # Aggregate districts by State/UT
                    numeric_cols = [c for c in COLUMN_PATTERNS.keys() if c in df.columns]
                    if "anaemia_pct" in df.columns:
                        numeric_cols.append("anaemia_pct")

                    agg_dict = {c: "mean" for c in numeric_cols}
                    state_agg = df.groupby(state_col)[numeric_cols].agg("mean").reset_index()

                    matched, unmatched = apply_canonical_mapping(state_agg, state_col, master)
                    matched = matched[matched["match_type"] != "unmatched"].copy()
                    matched["district_name"] = matched["canonical_name"]

                    keep_cols = ["district_id"] + numeric_cols
                    matched_sub = matched[keep_cols].drop_duplicates(subset=["district_id"])
                    merged_df = merged_df.merge(matched_sub, on="district_id", how="left")
            except Exception as e:
                print(f"[NFHS] ERROR reading {fp.name}: {e}")

        out_path = self.interim_dir / self.OUTPUT_FILE
        merged_df.to_parquet(out_path, index=False)
        print(f"[NFHS] Saved clean health data to {out_path} ({len(merged_df)} states/UTs)")
        return merged_df


if __name__ == "__main__":
    ingestor = NFHSIngestor()
    res = ingestor.load()
    if res is not None:
        print(res.head())
