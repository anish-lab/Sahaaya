"""
preprocessing.clean — Generic cleaning utilities for government datasets.

Handles the messy realities of Indian government data: commas in numbers,
percentage signs, Hindi/English "NA" variants, aggregate rows, etc.
"""

import re
from typing import Optional

import numpy as np
import pandas as pd


def parse_numeric(series: pd.Series) -> pd.Series:
    """
    Convert a messy string Series to float, handling:
      - Commas (e.g. "1,23,456")
      - Percentage signs ("45.3%")
      - Textual NA variants ("NA", "N/A", "-", "--", "NR", "...", "*")
      - Leading/trailing whitespace
      - Empty strings

    Parameters
    ----------
    series : pd.Series
        Input column (may be str, numeric, or mixed).

    Returns
    -------
    pd.Series
        Float64 series with NaN where parsing fails.
    """
    NA_PATTERNS = {"na", "n/a", "n.a.", "nr", "-", "--", "...", "*", ""}

    def _parse_one(val):
        if pd.isna(val):
            return np.nan
        s = str(val).strip()
        if s.lower() in NA_PATTERNS:
            return np.nan
        # Remove percentage sign and commas
        s = s.replace("%", "").replace(",", "")
        try:
            return float(s)
        except (ValueError, TypeError):
            return np.nan

    return series.map(_parse_one).astype("float64")


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Lowercase, strip whitespace, replace spaces/special chars with underscores.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        Same data, cleaned column names.
    """
    df = df.copy()
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", col.strip().lower()).strip("_")
        for col in df.columns
    ]
    return df


def detect_year_column(df: pd.DataFrame) -> Optional[str]:
    """
    Heuristic to find a year/period column.

    Looks for column names containing 'year', 'period', 'fy', 'session',
    'academic_year', etc.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    str or None
        Column name if found, else None.
    """
    YEAR_KEYWORDS = [
        "year", "period", "fy", "financial_year", "academic_year",
        "session", "survey", "round",
    ]
    for col in df.columns:
        col_lower = col.lower().replace(" ", "_")
        for kw in YEAR_KEYWORDS:
            if kw in col_lower:
                return col
    return None


def remove_aggregate_rows(
    df: pd.DataFrame,
    name_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Remove rows that represent aggregate/total entries rather than
    individual districts.

    Common patterns in Indian government data:
      - "All India", "India", "Total", "Tamil Nadu Total",
        "State Total", "Grand Total", etc.

    Parameters
    ----------
    df : pd.DataFrame
    name_col : str, optional
        Column containing district/region names.  If None, auto-detect
        by looking for columns named 'district', 'district_name', 'name'.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame.
    """
    if name_col is None:
        candidates = [c for c in df.columns if "district" in c.lower() or c.lower() == "name"]
        if not candidates:
            return df
        name_col = candidates[0]

    if name_col not in df.columns:
        return df

    AGGREGATE_PATTERNS = [
        r"(?i)^all\s+india$",
        r"(?i)^india$",
        r"(?i)\btotal\b",
        r"(?i)^grand\s+total$",
        r"(?i)^state\s+total$",
        r"(?i)^overall$",
    ]

    combined = "|".join(AGGREGATE_PATTERNS)
    mask = df[name_col].astype(str).str.contains(combined, regex=True, na=False)
    removed_count = mask.sum()
    if removed_count > 0:
        print(f"[CLEAN] Removed {removed_count} aggregate row(s) from '{name_col}'.")
    return df[~mask].reset_index(drop=True)
