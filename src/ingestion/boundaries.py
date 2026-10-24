"""
ingestion.boundaries — District boundary ingestor (GeoJSON / Shapefile).

Discovers boundary files in ``data/raw/boundaries/``, extracts ZIP archives safely,
identifies district name properties, maps them to canonical Tamil Nadu districts,
and saves the filtered and standardized GeoJSON to ``data/processed/tn_districts.geojson``.
"""

from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ingestion.base import BaseIngestor
from src.build_district_master import build_district_master, match_district

COMMON_NAME_PROPERTIES = [
    "district", "district_name", "districtname", "dtname", "dist_name",
    "district_n", "name_2", "name_1", "dt_name", "dist_code", "admin2name",
]

COMMON_STATE_PROPERTIES = [
    "state", "state_name", "statename", "stname", "name_1", "admin1name",
]


class BoundariesIngestor(BaseIngestor):
    """Boundary ingestor for district geometries."""

    SOURCE_NAME = "boundaries"
    RAW_SUBFOLDER = "boundaries"

    def __init__(self, root: Optional[Path] = None):
        super().__init__(root or ROOT)
        self.source_dir = self.raw_dir / self.RAW_SUBFOLDER
        self.output_path = self.processed_dir / "tn_districts.geojson"

    def discover(self) -> list[Path]:
        """Find boundary files (.geojson, .json, .shp, .zip)."""
        supported = {".geojson", ".json", ".shp", ".zip"}
        if not self.source_dir.exists():
            return []
        files = [p for p in self.source_dir.iterdir() if p.is_file() and p.suffix.lower() in supported]
        return sorted(files)

    def validate(self, data: Any) -> dict[str, Any]:
        """Validate boundary geometry dictionary."""
        if not isinstance(data, dict):
            return {"valid": False, "error": "Boundary data is not a dict"}
        return {"valid": "features" in data, "feature_count": len(data.get("features", []))}

    def _safe_extract_zip(self, zip_path: Path, target_dir: Path) -> list[Path]:
        """Safely extract ZIP contents avoiding directory traversal vulnerabilities."""
        target_dir.mkdir(parents=True, exist_ok=True)
        extracted = []
        resolved_target = target_dir.resolve()

        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                # Check for path traversal attacks
                member_path = (target_dir / member.filename).resolve()
                if not str(member_path).startswith(str(resolved_target)):
                    continue
                zf.extract(member, target_dir)
                extracted.append(member_path)
        return extracted

    def inspect(self, filepath: Path) -> dict[str, Any]:
        """Inspect boundary file format and properties."""
        suffix = filepath.suffix.lower()
        if suffix in {".geojson", ".json"}:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                features = data.get("features", [])
                prop_keys = list(features[0].get("properties", {}).keys()) if features else []
                return {
                    "format": "geojson",
                    "feature_count": len(features),
                    "property_keys": prop_keys,
                }
            except Exception as e:
                return {"format": "geojson", "error": str(e)}
        elif suffix == ".zip":
            try:
                with zipfile.ZipFile(filepath, "r") as zf:
                    names = zf.namelist()
                return {"format": "zip", "members": names}
            except Exception as e:
                return {"format": "zip", "error": str(e)}
        return {"format": suffix, "path": str(filepath)}

    def _find_name_property(self, properties: dict[str, Any]) -> Optional[str]:
        """Find the property key that holds the district name."""
        lowered = {k.lower(): k for k in properties.keys()}
        for candidate in COMMON_NAME_PROPERTIES:
            if candidate in lowered:
                return lowered[candidate]
        for k, v in properties.items():
            if isinstance(v, str) and len(v) > 2 and not v.isdigit():
                return k
        return None

    def _find_state_property(self, properties: dict[str, Any]) -> Optional[str]:
        """Find the property key that holds the state name if present."""
        lowered = {k.lower(): k for k in properties.keys()}
        for candidate in COMMON_STATE_PROPERTIES:
            if candidate in lowered:
                return lowered[candidate]
        return None

    def load(self, filepath: Optional[Path] = None) -> Optional[dict]:
        """Load GeoJSON or extract shapefile to process into GeoJSON dictionary."""
        if filepath is None:
            files = self.discover()
            if not files:
                return None
            filepath = files[0]

        suffix = filepath.suffix.lower()
        if suffix in {".geojson", ".json"}:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        elif suffix == ".zip":
            extract_dir = ROOT / "data" / "interim" / "boundaries_extracted"
            extracted_files = self._safe_extract_zip(filepath, extract_dir)
            geojson_files = [p for p in extracted_files if p.suffix.lower() in {".geojson", ".json"}]
            if geojson_files:
                with open(geojson_files[0], "r", encoding="utf-8") as f:
                    return json.load(f)
            # Check for shapefile
            shp_files = [p for p in extracted_files if p.suffix.lower() == ".shp"]
            if shp_files:
                try:
                    import geopandas as gpd
                    gdf = gpd.read_file(shp_files[0])
                    return json.loads(gdf.to_json())
                except ImportError:
                    return None
        elif suffix == ".shp":
            try:
                import geopandas as gpd
                gdf = gpd.read_file(filepath)
                return json.loads(gdf.to_json())
            except ImportError:
                return None
        return None

    def clean(self, geojson_data: dict) -> dict[str, Any]:
        """Standardize district names and filter for Tamil Nadu districts."""
        features = geojson_data.get("features", [])
        if not features:
            return {"geojson": None, "matched_count": 0, "unmatched": []}

        first_props = features[0].get("properties", {})
        name_key = self._find_name_property(first_props)
        state_key = self._find_state_property(first_props)

        matched_features = []
        unmatched = []
        seen_districts = set()

        for feat in features:
            props = feat.get("properties", {})
            raw_name = str(props.get(name_key, "")) if name_key else ""

            match_res = match_district(raw_name)
            if match_res is not None:
                dist_id, canonical_name, match_type, score = match_res
                props["district"] = canonical_name
                props["district_name"] = canonical_name
                props["district_id"] = dist_id
                props["state"] = canonical_name
                feat["properties"] = props
                if dist_id not in seen_districts:
                    matched_features.append(feat)
                    seen_districts.add(dist_id)
            else:
                if raw_name:
                    unmatched.append(raw_name)
                if raw_name:
                    unmatched.append(raw_name)

        filtered_geojson = {
            "type": "FeatureCollection",
            "features": matched_features,
        }

        return {
            "geojson": filtered_geojson,
            "matched_count": len(matched_features),
            "unmatched": unmatched,
        }

    def run(self) -> dict[str, Any]:
        """Execute boundary ingestion pipeline."""
        files = self.discover()
        if not files:
            return {"status": "skipped", "message": "No boundary files found in data/raw/boundaries/"}

        selected_file = files[0]
        data = self.load(selected_file)
        if not data:
            return {"status": "error", "message": f"Failed to load boundary data from {selected_file.name}"}

        cleaned = self.clean(data)
        out_geojson = cleaned["geojson"]
        if out_geojson and cleaned["matched_count"] > 0:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(out_geojson, f)

            return {
                "status": "success",
                "matched_districts": cleaned["matched_count"],
                "saved_to": str(self.output_path),
                "unmatched": cleaned["unmatched"][:10],
            }
        else:
            return {
                "status": "warning",
                "message": "Loaded boundary data but matched 0 Tamil Nadu districts.",
                "unmatched": cleaned["unmatched"][:10],
            }


if __name__ == "__main__":
    ingestor = BoundariesIngestor()
    res = ingestor.run()
    print("Boundaries Ingestion Result:", res)
