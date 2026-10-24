"""
validate_data.py — Data validation and quality assurance framework.

Provides automated checks for schema compliance, value ranges, district alignment,
missingness, duplicate records, and outputs standardized markdown data quality reports.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def validate_schema(
    df: pd.DataFrame,
    required_cols: list[str],
    numeric_cols: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Validate DataFrame contains required columns and proper data types."""
    missing = [c for c in required_cols if c not in df.columns]
    type_errors = []

    if numeric_cols:
        for c in numeric_cols:
            if c in df.columns:
                non_numeric = pd.to_numeric(df[c], errors="coerce").isna() & df[c].notna()
                if non_numeric.any():
                    type_errors.append(f"Column '{c}' contains {non_numeric.sum()} non-numeric values")

    return {
        "valid": len(missing) == 0 and len(type_errors) == 0,
        "missing_cols": missing,
        "type_errors": type_errors,
    }


def validate_districts(
    df: pd.DataFrame,
    canonical_names: list[str],
    name_col: str = "district_name",
) -> dict[str, Any]:
    """Verify that district names correspond to the canonical district list."""
    if name_col not in df.columns:
        return {"valid": False, "error": f"Column '{name_col}' not found"}

    canonical_set = set(canonical_names)
    present_districts = df[name_col].dropna().unique()
    unrecognized = [d for d in present_districts if d not in canonical_set]

    return {
        "valid": len(unrecognized) == 0,
        "total_districts": len(present_districts),
        "recognized": len(present_districts) - len(unrecognized),
        "unrecognized": unrecognized,
    }


def validate_ranges(
    df: pd.DataFrame,
    col: str,
    min_val: float,
    max_val: float,
) -> dict[str, Any]:
    """Check whether numeric column values fall within an expected range."""
    if col not in df.columns:
        return {"valid": False, "error": f"Column '{col}' not in DataFrame"}

    series = pd.to_numeric(df[col], errors="coerce").dropna()
    if series.empty:
        return {"valid": True, "out_of_range": 0, "min_found": None, "max_found": None}

    out_of_bounds = series[(series < min_val) | (series > max_val)]
    return {
        "valid": len(out_of_bounds) == 0,
        "out_of_range": int(len(out_of_bounds)),
        "min_found": float(series.min()),
        "max_found": float(series.max()),
    }


def generate_quality_report(df: pd.DataFrame, source_name: str) -> dict[str, Any]:
    """Compute detailed data quality metrics for a given dataset."""
    total_rows = len(df)
    missing_counts = df.isna().sum().to_dict()
    missing_pct = {k: round(v / total_rows * 100.0, 1) for k, v in missing_counts.items()} if total_rows > 0 else {}

    # Check for duplicate district rows
    duplicate_districts = 0
    if "district_id" in df.columns:
        duplicate_districts = int(df["district_id"].duplicated().sum())
    elif "district_name" in df.columns:
        duplicate_districts = int(df["district_name"].duplicated().sum())

    # Outliers (Z-score > 3 on numeric columns)
    outliers = {}
    numeric_df = df.select_dtypes(include=[np.number])
    for col in numeric_df.columns:
        s = numeric_df[col].dropna()
        if len(s) > 3 and s.std() > 0:
            z_scores = np.abs((s - s.mean()) / s.std())
            outlier_count = int((z_scores > 3.0).sum())
            if outlier_count > 0:
                outliers[col] = outlier_count

    return {
        "source": source_name,
        "total_records": total_rows,
        "columns": list(df.columns),
        "missing_pct": missing_pct,
        "duplicate_districts": duplicate_districts,
        "outliers": outliers,
    }


def save_quality_report(reports: list[dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """Format quality validation results into reports/data_quality_report.md."""
    if output_path is None:
        output_path = ROOT / "reports" / "data_quality_report.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# SAHAAYA Data Quality & Validation Report",
        "",
        "This report is generated automatically by the pipeline during each run.",
        "",
    ]

    for rep in reports:
        source = rep.get("source", "Unknown")
        lines.append(f"## Dataset Source: {source.upper()}")
        lines.append(f"- **Total Records**: {rep.get('total_records', 0)}")
        lines.append(f"- **Duplicate District Rows**: {rep.get('duplicate_districts', 0)}")
        lines.append("")
        lines.append("### Column Missingness")
        lines.append("| Column | Missing (%) |")
        lines.append("|---|---|")
        for col, pct in rep.get("missing_pct", {}).items():
            lines.append(f"| `{col}` | {pct}% |")
        lines.append("")

        outliers = rep.get("outliers", {})
        if outliers:
            lines.append("### Detected Outliers (>3 Std Dev)")
            for col, cnt in outliers.items():
                lines.append(f"- `{col}`: {cnt} extreme values")
            lines.append("")
        else:
            lines.append("### Outliers: None detected exceeding threshold.")
            lines.append("")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path
