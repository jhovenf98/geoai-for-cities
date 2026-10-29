"""Shared paths. Every script runs from any folder: paths are relative to this file."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

# Study window used for every map and model (lon/lat, WGS84)
BBOX = (-116.40, 32.62, -115.25, 33.80)   # west, south, east, north
