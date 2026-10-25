from __future__ import annotations

"""
ingestion.udise — UDISE+ education data ingestor.

Reads raw UDISE+ data files from ``data/raw/udise/``:
1. Table 2.5: Infrastructure (computes real percentages by dividing by Total Schools)
2. Table 3.17: Total Enrolment
3. Table 4.13: Total Teachers
4. Computes genuine Pupil-Teacher Ratio (PTR = Enrolment / Teachers)
5. Standardizes State/UT names and saves cleaned output.
"""

import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

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

DISTRICT_COL_PATTERNS = [
    "india_state_ut", "india_state__ut", "state_ut", "states_uts", "state/ut",
    "state_name", "state", "statename", "district_name", "district",
]


class UDISEIngestor(BaseIngestor):
    """Ingest and clean UDISE+ education data for all States and UTs."""

    SOURCE = "udise"
    OUTPUT_FILE = "udise_clean.parquet"

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
        print(f"[UDISE] Discovered {len(files)} file(s) in {self.source_dir}")
        return files

    def inspect(self, filepath: Path) -> dict:
        df = read_any_tabular(filepath)
        return {
            "file": filepath.name,
            "shape": df.shape,
            "columns": list(df.columns),
        }

    def _find_col(self, df: pd.DataFrame, patterns: list[str]) -> Optional[str]:
        for col in df.columns:
            cl = str(col).lower().replace(" ", "_")
            if any(p in cl for p in patterns):
                return col
        return None

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = standardize_column_names(df)
        dist_col = self._find_col(df, DISTRICT_COL_PATTERNS)
        if dist_col:
            df = remove_aggregate_rows(df, dist_col)
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
            print("[UDISE] No raw files found. Skipping.")
            return None

        master = build_district_master()
        merged_df = master[["district_id", "district_name", "state"]].copy()

        # Temporary stores
        enrol_df: Optional[pd.DataFrame] = None
        teach_df: Optional[pd.DataFrame] = None
        infra_df: Optional[pd.DataFrame] = None

        for fp in files:
            try:
                raw_df = read_any_tabular(fp)
                print(f"[UDISE] Processing {fp.name}: shape {raw_df.shape}")
                df = self.clean(raw_df)
                dist_col = self._find_col(df, DISTRICT_COL_PATTERNS)
                if not dist_col:
                    continue

                matched, _ = apply_canonical_mapping(df, dist_col, master)
                matched = matched[matched["match_type"] != "unmatched"].copy()

                cols_lower = [str(c).lower() for c in matched.columns]

                # 1. Check if Table 2.5 (Infrastructure)
                if any("total_schools" in c for c in cols_lower) or any("library" in c for c in cols_lower):
                    tot_col = [c for c in matched.columns if "total_schools" in str(c).lower()][0]
                    matched[tot_col] = parse_numeric(matched[tot_col]).replace(0, np.nan)

                    # Compute genuine percentages
                    elec_cols = [c for c in matched.columns if "functional_electricity" in str(c).lower() or "electricity" in str(c).lower()]
                    water_cols = [c for c in matched.columns if "functional_drinking" in str(c).lower() or "drinking_water" in str(c).lower()]
                    toilet_cols = [c for c in matched.columns if "functional_girls" in str(c).lower() or "girls'_toilet" in str(c).lower() or "toilet" in str(c).lower()]
                    net_cols = [c for c in matched.columns if "internet" in str(c).lower()]
                    comp_cols = [c for c in matched.columns if "computer" in str(c).lower() and "functional" in str(c).lower()]

                    infra_res = pd.DataFrame({"district_id": matched["district_id"]})
                    if elec_cols:
                        infra_res["schools_with_electricity_pct"] = (parse_numeric(matched[elec_cols[0]]) / matched[tot_col] * 100.0).clip(0, 100).round(1)
                    if water_cols:
                        infra_res["schools_with_drinking_water_pct"] = (parse_numeric(matched[water_cols[0]]) / matched[tot_col] * 100.0).clip(0, 100).round(1)
                    if toilet_cols:
                        infra_res["schools_with_toilets_pct"] = (parse_numeric(matched[toilet_cols[0]]) / matched[tot_col] * 100.0).clip(0, 100).round(1)
                    if net_cols:
                        infra_res["schools_with_internet_pct"] = (parse_numeric(matched[net_cols[0]]) / matched[tot_col] * 100.0).clip(0, 100).round(1)
                    if comp_cols:
                        infra_res["schools_with_computers_pct"] = (parse_numeric(matched[comp_cols[0]]) / matched[tot_col] * 100.0).clip(0, 100).round(1)

                    infra_df = infra_res.drop_duplicates(subset=["district_id"])

                # 2. Check if Table 3.17 (Enrolment)
                elif any("enrolment" in c for c in cols_lower):
                    enrol_cols = [c for c in matched.columns if "pre-primary_to_higher_secondary_-_total" in str(c).lower() or "total" in str(c).lower()]
                    target_col = enrol_cols[0] if enrol_cols else matched.columns[2]
                    enrol_res = pd.DataFrame({
                        "district_id": matched["district_id"],
                        "enrolment": parse_numeric(matched[target_col]),
                    })
                    enrol_df = enrol_res.drop_duplicates(subset=["district_id"])

                # 3. Check if Table 4.13 (Teachers)
                elif any("teachers" in c for c in cols_lower):
                    # Pick the total teachers column (exclude male/female gender breakdowns and sub-level totals)
                    teach_cols = [
                        c for c in matched.columns
                        if "total" in str(c).lower()
                        and "male" not in str(c).lower()
                        and "female" not in str(c).lower()
                        and "pre_primary" not in str(c).lower()
                        and "primary" not in str(c).lower()
                    ]
                    target_col = teach_cols[0] if teach_cols else matched.columns[2]
                    teach_res = pd.DataFrame({
                        "district_id": matched["district_id"],
                        "teachers": parse_numeric(matched[target_col]),
                    })
                    teach_df = teach_res.drop_duplicates(subset=["district_id"])

            except Exception as e:
                print(f"[UDISE] ERROR reading {fp.name}: {e}")

        # Merge Infrastructure
        if infra_df is not None:
            merged_df = merged_df.merge(infra_df, on="district_id", how="left")

        # Compute Pupil-Teacher Ratio (PTR = Enrolment / Teachers)
        if enrol_df is not None and teach_df is not None:
            ptr_merge = enrol_df.merge(teach_df, on="district_id", how="inner")
            ptr_merge["pupil_teacher_ratio"] = (ptr_merge["enrolment"] / ptr_merge["teachers"].replace(0, np.nan)).round(1)
            merged_df = merged_df.merge(ptr_merge[["district_id", "enrolment", "pupil_teacher_ratio"]], on="district_id", how="left")
        elif enrol_df is not None:
            merged_df = merged_df.merge(enrol_df, on="district_id", how="left")

        merged_df["period"] = "UDISE+ 2022-23"

        out_path = self.interim_dir / self.OUTPUT_FILE
        merged_df.to_parquet(out_path, index=False)
        print(f"[UDISE] Successfully compiled clean education & infrastructure table -> {out_path}")
        return merged_df


if __name__ == "__main__":
    ingestor = UDISEIngestor()
    res = ingestor.load()
    if res is not None:
        print(res.head(8))
