"""
ingestion — Data ingestion modules for government data sources.
"""

from src.ingestion.base import BaseIngestor, read_any_tabular
from src.ingestion.udise import UDISEIngestor
from src.ingestion.nfhs import NFHSIngestor
from src.ingestion.mgnrega import MGNREGAIngestor
from src.ingestion.boundaries import BoundariesIngestor

__all__ = [
    "BaseIngestor",
    "read_any_tabular",
    "UDISEIngestor",
    "NFHSIngestor",
    "MGNREGAIngestor",
    "BoundariesIngestor",
]
