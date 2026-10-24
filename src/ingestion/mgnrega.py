from __future__ import annotations

"""
ingestion.mgnrega — MGNREGA employment data ingestor.

Reads raw MGNREGA data from ``data/raw/mgnrega/``, auto-maps columns,
matches States/UTs, and saves cleaned output.
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
    detect_year_column,
    remove_aggregate_rows,
)
from src.preprocessing.standardize import apply_canonical_mapping
from src.build_district_master import build_district_master

COLUMN_PATTERNS: dict[str, list[str]] = {
    "hh_demanded_employment": [
        "demanded_employment", "hh_demanded", "households_demanded", "demand_employment",
    ],
    "hh_provided_employment": [
        "provided_employment", "hh_provided", "households_provided", "employment_provided",
    ],
    "employment_fulfillment_pct": [
        "fulfillment", "fulfilment", "employment_fulfil",
    ],
    "persondays_generated": [
        "persondays_generated", "person_days_generated", "total_persondays", "total_person_days",
    ],
    "persondays_per_hh": [
        "persondays_per_hh", "person_days_per_hh", "persondays_per_household",
    ],
    "women_persondays_pct": [
        "women_personday", "women_person_day", "women_participation",
    ],
    "avg_days_per_hh": [
        "avg_days", "average_days_employment",
    ],
    "avg_wage_rate": [
        "wage_rate", "average_wage", "avg_wage",
    ],
}

DISTRICT_COL_PATTERNS = [
    "state_ut", "states_uts", "state/ut", "states/uts", "state_name", "state", "statename",
    "district", "dist_name", "district_name", "distname", "dist",
]


class MGNREGAIngestor(BaseIngestor):
    """Ingest and clean MGNREGA data for States and UTs."""

    SOURCE = "mgnrega"
    OUTPUT_FILE = "mgnrega_clean.parquet"

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
        print(f"[MGNREGA] Discovered {len(files)} file(s) in {self.source_dir}")
        return files

    def inspect(self, filepath: Path) -> dict:
        df = read_any_tabular(filepath)
        return {
            "file": filepath.name,
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {c: str(d) for c, d in df.dtypes.items()},
        }

    def _auto_map_columns(self, df: pd.DataFrame) -> dict[str, str]:
        mapping: dict[str, str] = {}
        cols_lower = {c: c.lower().replace(" ", "_") for c in df.columns}
        for std_name, patterns in COLUMN_PATTERNS.items():
            for raw_col, col_low in cols_lower.items():
                if any(pat in col_low for pat in patterns):
                    mapping[raw_col] = std_name
                    break
        return mapping

    def _find_col(self, df: pd.DataFrame, patterns: list[str]) -> Optional[str]:
        for col in df.columns:
            cl = col.lower().replace(" ", "_")
            if any(p in cl for p in patterns):
                return col
        return None

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = standardize_column_names(df)
        dist_col = self._find_col(df, DISTRICT_COL_PATTERNS)
        if dist_col:
            df = remove_aggregate_rows(df, dist_col)

        year_col = detect_year_column(df)
        if year_col:
            df["period"] = df[year_col].astype(str)

        col_map = self._auto_map_columns(df)
        df = df.rename(columns=col_map)

        for std_col in COLUMN_PATTERNS.keys():
            if std_col in df.columns:
                df[std_col] = parse_numeric(df[std_col])
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
            print("[MGNREGA] No raw files found. Skipping.")
            return None

        master = build_district_master()
        merged_df = master[["district_id", "district_name", "state"]].copy()

        for fp in files:
            try:
                df = read_any_tabular(fp)
                print(f"[MGNREGA] Read {fp.name}: {df.shape}")
                df = self.clean(df)
                dist_col = self._find_col(df, DISTRICT_COL_PATTERNS)
                if dist_col:
                    matched, unmatched = apply_canonical_mapping(df, dist_col, master)
                    matched = matched[matched["match_type"] != "unmatched"].copy()
                    matched["district_name"] = matched["canonical_name"]
                    matched["state"] = matched["canonical_name"]

                    keep_cols = ["district_id"] + [
                        c for c in matched.columns if c in COLUMN_PATTERNS.keys() or c == "period"
                    ]
                    matched_sub = matched[keep_cols].drop_duplicates(subset=["district_id"])
                    merged_df = merged_df.merge(matched_sub, on="district_id", how="left")
            except Exception as e:
                print(f"[MGNREGA] ERROR reading {fp.name}: {e}")

        out_path = self.interim_dir / self.OUTPUT_FILE
        merged_df.to_parquet(out_path, index=False)
        print(f"[MGNREGA] Saved clean data to {out_path} ({len(merged_df)} states/UTs)")
        return merged_df


if __name__ == "__main__":
    ingestor = MGNREGAIngestor()
    res = ingestor.load()
    if res is not None:
        print(res.head())
