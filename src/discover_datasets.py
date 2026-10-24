from __future__ import annotations

"""
discover_datasets.py — Auto-discover raw data files in data/raw/ subfolders.

Scans each data source folder (udise, nfhs, mgnrega, boundaries, additional)
for supported file types, records metadata, and returns a structured inventory.
"""

import sys
import os
import zipfile
import json
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    ".csv", ".xlsx", ".xls", ".parquet",
    ".geojson", ".json", ".zip", ".shp",
}

# Folders to scan under data/raw/
SOURCE_FOLDERS = ["udise", "nfhs", "mgnrega", "boundaries", "additional"]


def _detect_encoding(filepath: Path) -> str:
    """Detect file encoding using chardet (first 64 KB)."""
    try:
        import chardet
    except ImportError:
        return "unknown (chardet not installed)"
    with open(filepath, "rb") as f:
        raw = f.read(65_536)
    result = chardet.detect(raw)
    return result.get("encoding", "unknown") or "unknown"


def _zip_contents(filepath: Path) -> list[str]:
    """List contents of a ZIP file without extracting."""
    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            return zf.namelist()
    except zipfile.BadZipFile:
        return ["<invalid or corrupt ZIP>"]


def _file_info(filepath: Path) -> dict:
    """Collect metadata for a single file."""
    stat = filepath.stat()
    info: dict = {
        "name": filepath.name,
        "path": str(filepath),
        "size_bytes": stat.st_size,
        "size_human": _human_size(stat.st_size),
        "format": filepath.suffix.lower().lstrip("."),
        "last_modified": datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat(),
    }

    # Extra metadata depending on format
    if filepath.suffix.lower() == ".zip":
        info["zip_contents"] = _zip_contents(filepath)
    if filepath.suffix.lower() == ".csv":
        info["detected_encoding"] = _detect_encoding(filepath)

    return info


def _human_size(nbytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(nbytes) < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024  # type: ignore[assignment]
    return f"{nbytes:.1f} TB"


def discover_datasets(raw_dir: Path | None = None) -> dict:
    """
    Scan data/raw/ subfolders for supported data files.

    Parameters
    ----------
    raw_dir : Path, optional
        Override for the raw data directory.  Defaults to ``ROOT / "data" / "raw"``.

    Returns
    -------
    dict
        Keyed by source folder name.  Each value is a list of file-info dicts.
    """
    if raw_dir is None:
        raw_dir = ROOT / "data" / "raw"

    inventory: dict = {}

    for folder_name in SOURCE_FOLDERS:
        folder = raw_dir / folder_name
        if not folder.exists():
            inventory[folder_name] = []
            continue

        files_found: list[dict] = []
        for fp in sorted(folder.rglob("*")):
            if not fp.is_file():
                continue
            if fp.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if fp.name.startswith("."):  # skip hidden files like .gitkeep
                continue
            files_found.append(_file_info(fp))

        inventory[folder_name] = files_found

    return inventory


def save_inventory(inventory: dict, output_path: Path | None = None) -> Path:
    """Save inventory to JSON file."""
    if output_path is None:
        output_path = ROOT / "data" / "metadata" / "dataset_inventory.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)
    return output_path


# Alias for pipeline compatibility
discover_all_raw = discover_datasets


def print_summary(inventory: dict) -> None:
    """Print a human-readable summary of the discovered datasets."""
    print("=" * 60)
    print("  SAHAAYA  --  Raw Dataset Inventory")
    print("=" * 60)

    total_files = 0
    total_bytes = 0

    for source, files in inventory.items():
        n = len(files)
        total_files += n
        src_bytes = sum(f["size_bytes"] for f in files)
        total_bytes += src_bytes
        status = f"{n} file(s), {_human_size(src_bytes)}" if n else "(empty)"
        print(f"  {source:15s}  {status}")

        for f in files:
            extra = ""
            if f["format"] == "zip":
                contents = f.get("zip_contents", [])
                extra = f" -> {len(contents)} entries inside"
            if f["format"] == "csv":
                extra = f" [encoding: {f.get('detected_encoding', '?')}]"
            print(f"    - {f['name']:40s} {f['size_human']:>10s}{extra}")

    print("-" * 60)
    print(
        f"  Total: {total_files} file(s), {_human_size(total_bytes)}"
    )
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    inv = discover_datasets()
    print_summary(inv)

    # Optionally save the inventory as JSON
    meta_dir = ROOT / "data" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    out_path = meta_dir / "dataset_inventory.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=2, ensure_ascii=False)
    print(f"\nInventory saved to {out_path}")
