from __future__ import annotations

"""
ingestion.udise — UDISE+ education data ingestor.

Reads raw UDISE+ data files from ``data/raw/udise/``, auto-maps columns
to standard indicator names, matches States/UTs to the canonical master,
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
    detect_year_column,
    remove_aggregate_rows,
)
from src.preprocessing.standardize import apply_canonical_mapping
from src.build_district_master import build_district_master

# ---------------------------------------------------------------------------
# Column mapping
# ---------------------------------------------------------------------------
COLUMN_PATTERNS: dict[str, list[str]] = {
    "enrolment": [
        "enrolment", "enrollment", "total_enrolment", "total_enrollment",
        "total_students", "enrolment_overall",
    ],
    "dropout_rate": [
        "dropout", "drop_out", "drop_out_rate", "repetition_rate",
    ],
    "pupil_teacher_ratio": [
        "pupil_teacher", "ptr", "pupil_teacher_ratio", "student_teacher", "number_of_teachers", "teachers",
    ],
    "schools_with_electricity_pct": [
        "electricity", "electric", "schools_with_electricity",
    ],
    "schools_with_toilets_pct": [
        "toilet", "toilets", "functional_toilet", "cwsn_friendly_toilets",
    ],
    "schools_with_drinking_water_pct": [
        "drinking_water", "water", "functional_drinking_water",
    ],
    "schools_with_internet_pct": [
        "internet", "computer", "ict", "digital_library", "tinkering_labs", "library",
    ],
}

DISTRICT_COL_PATTERNS = [
    "state_ut", "states_uts", "state/ut", "states/uts", "state_name", "state", "statename",
    "district", "dist_name", "district_name", "distname", "dist",
]


class UDISEIngestor(BaseIngestor):
    """Ingest and clean UDISE+ education data for all States and UTs."""

    SOURCE = "udise"
    OUTPUT_FILE = "udise_clean.parquet"

    def __init__(self, root: Path | None = None):
        super().__init__(root or ROOT)
        self.source_dir = self.raw_dir / self.SOURCE

    def discover(self) -> list[Path]:
        """Find all tabular files in data/raw/udise/."""
        exts = {".csv", ".xlsx", ".xls", ".parquet"}
        if not self.source_dir.exists():
            return []
        files = [
            f
            for f in sorted(self.source_dir.rglob("*"))
            if f.is_file() and f.suffix.lower() in exts and not f.name.startswith(".")
        ]
        print(f"[UDISE] Discovered {len(files)} file(s) in {self.source_dir}")
        return files

    def inspect(self, filepath: Path) -> dict:
        """Return shape, columns, dtypes of a raw file."""
        df = read_any_tabular(filepath)
        return {
            "file": filepath.name,
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {c: str(d) for c, d in df.dtypes.items()},
        }

    def _auto_map_columns(self, df: pd.DataFrame) -> dict[str, str]:
        """Map raw columns to standard indicator names via pattern matching."""
        mapping: dict[str, str] = {}
        cols_lower = {c: c.lower().replace(" ", "_") for c in df.columns}

        for std_name, patterns in COLUMN_PATTERNS.items():
            for raw_col, col_low in cols_lower.items():
                if any(pat in col_low for pat in patterns):
                    mapping[raw_col] = std_name
                    break
        return mapping

    def _find_col(self, df: pd.DataFrame, patterns: list[str]) -> Optional[str]:
        """Find the first column whose lowered name contains any pattern."""
        for col in df.columns:
            cl = col.lower().replace(" ", "_")
            if any(p in cl for p in patterns):
                return col
        return None

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply UDISE-specific cleaning."""
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
        """Validate cleaned UDISE DataFrame."""
        return {
            "source": self.SOURCE,
            "row_count": len(df),
            "columns": list(df.columns),
        }

    def load(self) -> Optional[pd.DataFrame]:
        """Full pipeline: discover -> read -> clean -> match states -> save."""
        files = self.discover()
        if not files:
            print("[UDISE] No raw files found. Skipping.")
            return None

        master = build_district_master()
        merged_df = master[["district_id", "district_name", "state"]].copy()

        for fp in files:
            try:
                df = read_any_tabular(fp)
                print(f"[UDISE] Read {fp.name}: {df.shape}")
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
                print(f"[UDISE] ERROR reading {fp.name}: {e}")

        out_path = self.interim_dir / self.OUTPUT_FILE
        merged_df.to_parquet(out_path, index=False)
        print(f"[UDISE] Saved clean data to {out_path} ({len(merged_df)} states/UTs)")
        return merged_df


if __name__ == "__main__":
    ingestor = UDISEIngestor()
    res = ingestor.load()
    if res is not None:
        print(res.head())
