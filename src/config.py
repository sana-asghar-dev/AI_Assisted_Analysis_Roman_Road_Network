"""
src/config.py
=============
Central configuration constants for the Roman Road Network Analysis pipeline.
All paths, CRS definitions, and reproducibility constants are defined here.
"""
from pathlib import Path

# ---------------------------------------------------------------
# Repository root (two levels up from this file: src/ → project/)
# ---------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------
# Data directories
# ---------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"

# ---------------------------------------------------------------
# Documentation directories
# ---------------------------------------------------------------
DOCS_DIR = PROJECT_ROOT / "docs"

# ---------------------------------------------------------------
# Coordinate Reference Systems
# ---------------------------------------------------------------
# Geographic WGS84 — used by Pleiades and Itiner-e source data
CRS_WGS84 = "EPSG:4326"

# Metric projected CRS for Italy — UTM Zone 32N
# Used for all distance calculations, buffer operations, and snapping.
# Covers mainland Italy, Sicily, and Sardinia accurately.
CRS_METRIC = "EPSG:32632"

# Alternative: ETRS89-extended / LAEA Europe (pan-European equal-area)
CRS_LAEA = "EPSG:3035"

# Primary metric CRS used throughout the pipeline
CRS_PRIMARY = CRS_METRIC

# ---------------------------------------------------------------
# Italy bounding box (WGS84 degrees)
# Generous bounds to capture Cisalpine Gaul, Dalmatian coast refs,
# and the islands (Sicily, Sardinia excluded from main road analysis).
# ---------------------------------------------------------------
ITALY_BBOX = {
    "min_lon": 6.5,
    "min_lat": 36.5,
    "max_lon": 18.6,
    "max_lat": 47.2,
}

# ---------------------------------------------------------------
# Spatial snapping tolerances (in metres, after metric reprojection)
# ---------------------------------------------------------------
# Tolerance for snapping road segment endpoints to heal digitization gaps.
ENDPOINT_SNAP_TOLERANCE_M = 250  # metres

# Maximum distance to snap a city point to the nearest road node/segment.
CITY_SNAP_THRESHOLD_M = 10_000  # 10 km — log a WARNING for any city > 5 km

# City-snap warning threshold — log if city is more than this far from road
CITY_SNAP_WARN_M = 5_000  # 5 km

# ---------------------------------------------------------------
# Network analysis parameters
# ---------------------------------------------------------------
# Edge weight attribute name (road distance in kilometres)
EDGE_WEIGHT = "length_km"

# ---------------------------------------------------------------
# Machine Learning / Clustering
# ---------------------------------------------------------------
RANDOM_STATE = 42
N_CLUSTERS_PRIMARY = 3
N_CLUSTERS_RANGE = range(2, 6)  # k = 2, 3, 4, 5 for elbow/silhouette evaluation

# ---------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------
# Static map DPI for publication-quality export
STATIC_MAP_DPI = 300

# Folium map default centre (Rome, WGS84)
MAP_DEFAULT_LAT = 41.9
MAP_DEFAULT_LON = 12.5
MAP_DEFAULT_ZOOM = 6

# ---------------------------------------------------------------
# Logging
# ---------------------------------------------------------------
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------
# Ensure output directories exist at import time
# ---------------------------------------------------------------
for _dir in (RAW_DIR, INTERIM_DIR, PROCESSED_DIR, EXPORTS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

