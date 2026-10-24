"""
ingestion.base — Abstract base ingestor and common I/O utilities for
reading messy government data files.
"""

import csv
import io
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


def detect_encoding(filepath: Path) -> str:
    """
    Detect file encoding using chardet (reads first 64 KB).

    Parameters
    ----------
    filepath : Path
        Path to the file.

    Returns
    -------
    str
        Detected encoding string (e.g. ``"utf-8"``, ``"windows-1252"``).
        Falls back to ``"utf-8"`` on failure.
    """
    try:
        import chardet
    except ImportError:
        return "utf-8"

    with open(filepath, "rb") as fh:
        raw = fh.read(65_536)
    result = chardet.detect(raw)
    return result.get("encoding") or "utf-8"


def _detect_delimiter(filepath: Path, encoding: str) -> str:
    """Sniff the CSV delimiter from the first 8 KB."""
    with open(filepath, "r", encoding=encoding, errors="replace") as fh:
        sample = fh.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def _detect_header_row(filepath: Path, encoding: str, delimiter: str) -> int:
    """
    Heuristic: skip leading metadata rows that are common in Indian
    government datasets (blank lines, title rows, source citations).

    Returns the 0-based row index that looks like the real header.
    """
    with open(filepath, "r", encoding=encoding, errors="replace") as fh:
        lines = [fh.readline() for _ in range(30)]

    best_row = 0
    max_fields = 0
    for i, line in enumerate(lines):
        n_fields = len(line.split(delimiter))
        # Header row typically has the most fields and contains
        # alpha text (not just numbers)
        alpha_ratio = sum(c.isalpha() for c in line) / max(len(line), 1)
        if n_fields > max_fields and alpha_ratio > 0.15:
            max_fields = n_fields
            best_row = i

    return best_row


def read_any_tabular(filepath: Path) -> pd.DataFrame:
    """
    Read a CSV, XLSX, or XLS file with automatic detection of encoding,
    delimiter, and header row.

    Parameters
    ----------
    filepath : Path
        Path to the tabular data file.

    Returns
    -------
    pd.DataFrame
        Raw DataFrame as read from the file.

    Raises
    ------
    ValueError
        If the file format is not supported.
    """
    ext = filepath.suffix.lower()

    if ext == ".csv":
        enc = detect_encoding(filepath)
        delim = _detect_delimiter(filepath, enc)
        header_row = _detect_header_row(filepath, enc, delim)
        return pd.read_csv(
            filepath,
            encoding=enc,
            delimiter=delim,
            header=header_row,
            on_bad_lines="warn",
        )

    if ext in (".xlsx", ".xls"):
        # Try each sheet; return the first one with > 1 column
        xls = pd.ExcelFile(filepath)
        for sheet in xls.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet)
            if df.shape[1] > 1:
                return df
        # Fall back to first sheet
        return pd.read_excel(filepath)

    if ext == ".parquet":
        return pd.read_parquet(filepath)

    raise ValueError(f"Unsupported file format: {ext}")


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class BaseIngestor(ABC):
    """
    Abstract base class for a data-source ingestor.

    Subclasses implement the concrete logic for a specific data source
    (UDISE+, NFHS, MGNREGA, boundaries).
    """

    def __init__(self, root: Optional[Path] = None):
        self.root = root or Path(__file__).resolve().parents[2]
        self.raw_dir: Path = self.root / "data" / "raw"
        self.interim_dir: Path = self.root / "data" / "interim"
        self.processed_dir: Path = self.root / "data" / "processed"
        self.interim_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict:
        """Standard execution wrapper returning status and summary."""
        res = self.load()
        if res is None:
            return {"status": "skipped", "message": f"No data found or loaded for {self.__class__.__name__}"}
        if isinstance(res, dict):
            return {"status": "success", **res}
        if hasattr(res, "empty") and res.empty:
            return {"status": "skipped", "message": f"Loaded empty dataset for {self.__class__.__name__}"}
        return {"status": "success", "rows": len(res)}

    def load_cleaned(self) -> Optional[pd.DataFrame]:
        """Load already saved cleaned parquet file if present."""
        if hasattr(self, "output_path") and isinstance(self.output_path, Path) and self.output_path.exists():
            if self.output_path.suffix == ".parquet":
                return pd.read_parquet(self.output_path)
        if hasattr(self, "OUTPUT_FILE"):
            out = self.interim_dir / self.OUTPUT_FILE
            if out.exists():
                return pd.read_parquet(out)
        return None

    # ---- abstract interface -----------------------------------------------

    @abstractmethod
    def discover(self) -> list[Path]:
        """Return list of raw files belonging to this source."""

    @abstractmethod
    def inspect(self, filepath: Path) -> dict:
        """Inspect a file and return a summary dict (columns, shape, etc.)."""

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> dict:
        """Validate a loaded DataFrame; return a report dict."""

    @abstractmethod
    def load(self) -> Optional[pd.DataFrame]:
        """Load, clean, and return the processed DataFrame (or None)."""

    @abstractmethod
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply source-specific cleaning to a raw DataFrame."""
