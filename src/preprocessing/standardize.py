"""
preprocessing.standardize — District name standardization utilities.

Provides helpers to normalize messy district name strings and map them
to the canonical SAHAAYA district master using fuzzy matching.
"""

import re
from typing import Optional

import pandas as pd


def standardize_district_name(name) -> Optional[str]:
    """
    Basic string normalization for a district name.

    Steps:
      1. Convert to string, strip whitespace.
      2. Title-case.
      3. Collapse multiple spaces.
      4. Remove trailing "District" / "Dt" / "Dt." suffixes.

    Parameters
    ----------
    name : str-like
        Raw district name.

    Returns
    -------
    str or None
        Cleaned name, or None if input is null/empty.
    """
    if pd.isna(name):
        return None
    s = str(name).strip()
    if not s:
        return None
    s = re.sub(r"\s+", " ", s)
    s = s.title()
    # Remove common suffixes
    s = re.sub(r"\s+(District|Dt\.?)\s*$", "", s, flags=re.IGNORECASE)
    return s.strip() or None


def apply_canonical_mapping(
    df: pd.DataFrame,
    name_col: str,
    district_master: pd.DataFrame,
    *,
    threshold: int = 80,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Match every district name in *df* to the canonical master, adding
    ``district_id`` and ``canonical_name`` columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with a raw district name column.
    name_col : str
        Column in *df* containing raw district names.
    district_master : pd.DataFrame
        Must have ``district_id`` and ``district_name`` columns (from
        :func:`build_district_master.build_district_master`).
    threshold : int
        Fuzzy match threshold (0-100).

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        - Mapped DataFrame with ``district_id``, ``canonical_name``,
          ``match_type``, ``match_score`` appended.
        - Unmatched report (subset of rows that could not be matched).
    """
    # Lazy import to avoid circular dependency at module level
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))
    from src.build_district_master import match_district

    df = df.copy()

    # Standardize names first
    df["_std_name"] = df[name_col].map(standardize_district_name)

    # Match each name
    matches = df["_std_name"].map(
        lambda n: match_district(n, threshold=threshold) if n else None
    )

    df["district_id"] = matches.map(lambda m: m[0] if m else None)
    df["canonical_name"] = matches.map(lambda m: m[1] if m else None)
    df["match_type"] = matches.map(lambda m: m[2] if m else "unmatched")
    df["match_score"] = matches.map(lambda m: m[3] if m else 0.0)

    df.drop(columns=["_std_name"], inplace=True)

    unmatched = df[df["match_type"] == "unmatched"].copy()
    if not unmatched.empty:
        print(
            f"[WARN] {len(unmatched)} row(s) could not be matched to any "
            f"district in column '{name_col}'."
        )

    return df, unmatched
