"""
preprocessing — Data cleaning, numeric parsing, and district standardization.
"""

from src.preprocessing.clean import (
    parse_numeric,
    standardize_column_names,
    detect_year_column,
    remove_aggregate_rows,
)
from src.preprocessing.standardize import (
    standardize_district_name,
    apply_canonical_mapping,
)

__all__ = [
    "parse_numeric",
    "standardize_column_names",
    "detect_year_column",
    "remove_aggregate_rows",
    "standardize_district_name",
    "apply_canonical_mapping",
]
