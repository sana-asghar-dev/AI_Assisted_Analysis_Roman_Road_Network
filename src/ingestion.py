"""
src/ingestion.py
================
Data ingestion and schema validation for the Roman Road Network pipeline.

Handles loading of:
  1. Pleiades Gazetteer CSV — ancient settlement names, IDs, and coordinates.
  2. Itiner-e Roman road GeoJSON / GeoPackage — road segment geometries.

Design principles
-----------------
- Never silently substitute invented mock data for missing files.
- Always inspect actual column headers before applying transformations.
- Log exact URLs and manual placement instructions when automated download fails.
- Validate schema and coordinate bounds before returning data to the pipeline.

References
----------
- Pleiades (2025): https://pleiades.stoa.org/downloads
- de Soto et al. (2025) Itiner-e: https://doi.org/10.1038/s41597-025-06140-z
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Download instructions emitted when files are missing
# ---------------------------------------------------------------------------

_PLEIADES_DOWNLOAD_INFO = """
╔══════════════════════════════════════════════════════════════════════╗
║  PLEIADES DATA: Manual Download Required                            ║
╠══════════════════════════════════════════════════════════════════════╣
║  URL:  https://pleiades.stoa.org/downloads                          ║
║  File: pleiades-places-latest.csv.gz                                ║
║        (or pleiades-places-latest.csv if pre-extracted)             ║
║  Licence: CC BY 3.0 US — cite as:                                   ║
║    Pleiades (2025). Data for download. Pleiades Project.            ║
║    https://pleiades.stoa.org/downloads                              ║
╠══════════════════════════════════════════════════════════════════════╣
║  ACTION: Place the file in:                                         ║
║    data/raw/pleiades-places-latest.csv.gz                           ║
║  Then re-run the pipeline.                                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

_ITINERE_DOWNLOAD_INFO = """
╔══════════════════════════════════════════════════════════════════════╗
║  ITINER-E DATA: Manual Download Required                            ║
╠══════════════════════════════════════════════════════════════════════╣
║  URL:  https://itiner-e.org/data                                    ║
║  Preferred: GeoPackage (.gpkg) or GeoJSON (.geojson)               ║
║  Licence: CC BY 4.0 — cite as:                                      ║
║    de Soto, P. et al. (2025). Itiner-e: A high-resolution           ║
║    dataset of roads of the Roman Empire. Scientific Data.           ║
║    https://doi.org/10.1038/s41597-025-06140-z                       ║
╠══════════════════════════════════════════════════════════════════════╣
║  ACTION: Place the file in data/raw/ as one of:                     ║
║    data/raw/itinere_roads.gpkg          (GeoPackage — preferred)    ║
║    data/raw/itinere_roads.geojson       (GeoJSON)                   ║
║    data/raw/itinere_roads.shp           (Shapefile)                 ║
║  Then re-run the pipeline.                                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ---------------------------------------------------------------------------
# Expected schema definitions (validated after load)
# ---------------------------------------------------------------------------

# Minimum columns we require from the Pleiades CSV
PLEIADES_REQUIRED_COLS = {
    "id",
    "title",
    "representative_lat",
    "representative_lon",
}

# Optional but useful Pleiades columns
PLEIADES_OPTIONAL_COLS = {
    "description",
    "place_types",
    "bbox",
    "created",
    "modified",
}

# Italy bounding box in WGS84 degrees
ITALY_LON_MIN, ITALY_LON_MAX = 6.5, 18.6
ITALY_LAT_MIN, ITALY_LAT_MAX = 36.5, 47.5


# ---------------------------------------------------------------------------
# Helper: find a raw data file by trying multiple candidate filenames
# ---------------------------------------------------------------------------


def _find_raw_file(candidates: list[Path]) -> Path | None:
    """Return the first candidate path that exists, or None."""
    for path in candidates:
        if path.exists():
            return path
    return None


# ---------------------------------------------------------------------------
# Pleiades ingestion
# ---------------------------------------------------------------------------


def load_pleiades_csv(raw_dir: Path | None = None) -> "pd.DataFrame":
    """
    Load and validate the Pleiades places CSV dump.

    Searches for the file in ``raw_dir`` (defaults to ``data/raw/``).
    Accepts both compressed (`.csv.gz`) and plain (`.csv`) formats.

    Parameters
    ----------
    raw_dir : Path, optional
        Directory to search for the Pleiades CSV file.
        Defaults to ``src/config.PROJECT_ROOT / 'data' / 'raw'``.

    Returns
    -------
    pd.DataFrame
        Validated Pleiades places dataframe with columns:
        ``id``, ``title``, ``representative_lat``, ``representative_lon``,
        plus any optional columns present in the file.

    Raises
    ------
    FileNotFoundError
        If neither the compressed nor plain CSV is found in ``raw_dir``.
    ValueError
        If required columns are missing or coordinate bounds are invalid.
    """
    import pandas as pd

    from src.config import RAW_DIR

    if raw_dir is None:
        raw_dir = RAW_DIR

    candidates = [
        raw_dir / "pleiades-places-latest.csv.gz",
        raw_dir / "pleiades-places-latest.csv",
        raw_dir / "pleiades_places.csv.gz",
        raw_dir / "pleiades_places.csv",
    ]

    path = _find_raw_file(candidates)
    if path is None:
        logger.error("Pleiades CSV not found in %s", raw_dir)
        logger.error("Tried: %s", [str(c) for c in candidates])
        print(_PLEIADES_DOWNLOAD_INFO)
        raise FileNotFoundError(
            f"Pleiades CSV not found in {raw_dir}. "
            "See download instructions above and place file in data/raw/."
        )

    logger.info("Loading Pleiades CSV from %s", path)

    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as exc:
        raise ValueError(f"Failed to read Pleiades CSV at {path}: {exc}") from exc

    logger.info("Pleiades raw shape: %d rows × %d columns", *df.shape)
    logger.debug("Pleiades columns (actual): %s", list(df.columns))

    # --- Schema validation ---
    missing_cols = PLEIADES_REQUIRED_COLS - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Pleiades CSV is missing required columns: {missing_cols}. "
            f"Actual columns: {list(df.columns)}"
        )

    # --- Cast and clean key fields ---
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["representative_lat"] = pd.to_numeric(df["representative_lat"], errors="coerce")
    df["representative_lon"] = pd.to_numeric(df["representative_lon"], errors="coerce")

    null_ids = df["id"].isna().sum()
    if null_ids > 0:
        logger.warning("%d rows have non-numeric 'id' — dropping.", null_ids)
        df = df.dropna(subset=["id"])

    df["id"] = df["id"].astype(int)

    # --- Coordinate validation ---
    null_coords = df[["representative_lat", "representative_lon"]].isna().any(axis=1).sum()
    if null_coords > 0:
        logger.warning("%d rows have null coordinates — these will be excluded from spatial ops.", null_coords)

    # Check for obviously out-of-range coordinates
    coord_valid = df[
        (df["representative_lat"].between(-90, 90))
        & (df["representative_lon"].between(-180, 180))
    ].copy()
    out_of_range = len(df) - len(coord_valid)
    if out_of_range > 0:
        logger.warning("%d rows with out-of-range WGS84 coordinates dropped.", out_of_range)
    df = coord_valid

    logger.info("Pleiades validated: %d places loaded.", len(df))
    return df


def filter_pleiades_to_italy(df: "pd.DataFrame") -> "pd.DataFrame":
    """
    Filter Pleiades records to the Italian study bounding box.

    Parameters
    ----------
    df : pd.DataFrame
        Full Pleiades dataset as returned by ``load_pleiades_csv()``.

    Returns
    -------
    pd.DataFrame
        Subset of places within the Italy bounding box
        (lon ∈ [6.5°, 18.6°], lat ∈ [36.5°, 47.5°]).
    """
    mask = (
        df["representative_lon"].between(ITALY_LON_MIN, ITALY_LON_MAX)
        & df["representative_lat"].between(ITALY_LAT_MIN, ITALY_LAT_MAX)
    )
    italy_df = df[mask].copy()
    logger.info(
        "Pleiades Italy filter: %d / %d places retained (bbox: lon [%.1f, %.1f], lat [%.1f, %.1f]).",
        len(italy_df), len(df),
        ITALY_LON_MIN, ITALY_LON_MAX, ITALY_LAT_MIN, ITALY_LAT_MAX,
    )
    return italy_df


def match_catalog_to_pleiades(
    catalog_df: "pd.DataFrame",
    pleiades_df: "pd.DataFrame",
) -> "pd.DataFrame":
    """
    Left-join the city catalog to Pleiades by ``pleiades_id`` / ``id``.

    Cities without a matching Pleiades record are retained with NaN for
    Pleiades-specific fields. This allows the catalog's own coordinates
    (pre-verified from Pleiades) to be used as a fallback.

    Parameters
    ----------
    catalog_df : pd.DataFrame
        45-city catalog from ``cities_catalog.get_cities_dataframe()``.
    pleiades_df : pd.DataFrame
        Pleiades Italy subset from ``filter_pleiades_to_italy()``.

    Returns
    -------
    pd.DataFrame
        Merged dataframe with catalog fields + Pleiades title/description.
    """
    pleiades_subset = pleiades_df[
        ["id", "title"] + [c for c in ["description", "place_types"] if c in pleiades_df.columns]
    ].rename(columns={"id": "pleiades_id", "title": "pleiades_title"})

    merged = catalog_df.merge(pleiades_subset, on="pleiades_id", how="left")

    matched = merged["pleiades_title"].notna().sum()
    unmatched = len(merged) - matched
    logger.info(
        "Catalog ↔ Pleiades join: %d/%d cities matched by pleiades_id.",
        matched, len(merged),
    )
    if unmatched > 0:
        unmatched_cities = merged.loc[merged["pleiades_title"].isna(), "latin_name"].tolist()
        logger.warning(
            "%d cities not found in Pleiades Italy subset: %s. "
            "Using catalog coordinates as authoritative fallback.",
            unmatched, unmatched_cities,
        )
    return merged


# ---------------------------------------------------------------------------
# Itiner-e ingestion
# ---------------------------------------------------------------------------


def load_itinere_roads(raw_dir: Path | None = None) -> "gpd.GeoDataFrame":
    """
    Load and validate the Itiner-e Roman roads dataset.

    Searches ``raw_dir`` for GeoPackage, GeoJSON, or Shapefile formats.
    Returns all road segments with their geometries and attributes.

    Parameters
    ----------
    raw_dir : Path, optional
        Directory to search. Defaults to ``data/raw/``.

    Returns
    -------
    geopandas.GeoDataFrame
        Road segments in their original CRS (expected WGS84 / EPSG:4326).
        Geometry column: ``geometry`` (LineString or MultiLineString).

    Raises
    ------
    FileNotFoundError
        If no Itiner-e file is found in ``raw_dir``.
    ValueError
        If the loaded data has no geometry column or empty geometry.
    """
    import geopandas as gpd

    from src.config import RAW_DIR

    if raw_dir is None:
        raw_dir = RAW_DIR

    # Search order: GeoPackage > GeoJSON > Shapefile
    candidates = [
        raw_dir / "itinere_roads.gpkg",
        raw_dir / "itinere_roads.geojson",
        raw_dir / "itinere_roads.json",
        raw_dir / "itinere_roads.shp",
        # Alternative naming conventions
        raw_dir / "roads.gpkg",
        raw_dir / "roads.geojson",
        raw_dir / "roman_roads.gpkg",
        raw_dir / "roman_roads.geojson",
    ]

    path = _find_raw_file(candidates)
    if path is None:
        logger.error("Itiner-e road file not found in %s", raw_dir)
        logger.error("Tried: %s", [str(c) for c in candidates])
        print(_ITINERE_DOWNLOAD_INFO)
        raise FileNotFoundError(
            f"Itiner-e road file not found in {raw_dir}. "
            "See download instructions above."
        )

    logger.info("Loading Itiner-e roads from %s", path)

    try:
        gdf = gpd.read_file(path)
    except Exception as exc:
        raise ValueError(f"Failed to read Itiner-e file at {path}: {exc}") from exc

    logger.info("Itiner-e raw shape: %d features × %d columns", *gdf.shape)
    logger.info("Itiner-e columns (actual): %s", list(gdf.columns))
    logger.info("Itiner-e source CRS: %s", gdf.crs)

    # --- Geometry validation ---
    if gdf.geometry is None or len(gdf) == 0:
        raise ValueError("Itiner-e file loaded but contains no geometry features.")

    invalid_geoms = (~gdf.is_valid).sum()
    if invalid_geoms > 0:
        logger.warning(
            "%d invalid geometries detected in Itiner-e dataset "
            "(will be repaired in gis_processing.py).", invalid_geoms
        )

    null_geoms = gdf.geometry.isna().sum()
    if null_geoms > 0:
        logger.warning("%d features with null geometry — dropping.", null_geoms)
        gdf = gdf.dropna(subset=["geometry"])

    # --- CRS check ---
    if gdf.crs is None:
        logger.warning("Itiner-e file has no CRS defined — assuming EPSG:4326 (WGS84).")
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs.to_epsg() != 4326:
        logger.info(
            "Itiner-e CRS is %s (not EPSG:4326) — reprojection will occur in gis_processing.py.",
            gdf.crs
        )

    # --- Log geometry types ---
    geom_types = gdf.geometry.geom_type.value_counts().to_dict()
    logger.info("Itiner-e geometry types: %s", geom_types)

    logger.info("Itiner-e loaded: %d road features.", len(gdf))
    return gdf


def inspect_itinere_schema(gdf: "gpd.GeoDataFrame") -> dict:
    """
    Inspect and log the actual Itiner-e column schema.

    This function must be called after ``load_itinere_roads()`` to
    verify actual field names before downstream transformations depend
    on them. Returns a dict of column → dtype for logging and documentation.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        Loaded Itiner-e dataset.

    Returns
    -------
    dict
        Mapping of column name → dtype string.
    """
    schema = {col: str(dtype) for col, dtype in gdf.dtypes.items()}
    logger.info("=== Itiner-e Schema Inspection ===")
    for col, dtype in schema.items():
        sample = gdf[col].iloc[0] if len(gdf) > 0 else "N/A"
        logger.info("  %-30s  %-15s  sample: %s", col, dtype, repr(sample)[:60])
    logger.info("==================================")
    return schema


def filter_itinere_to_italy(gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    """
    Spatially filter Itiner-e road segments to the Italian bounding box.

    Filtering is performed on the *original* CRS (expected WGS84).
    The result retains only segments whose geometry intersects the
    Italian bounding box polygon.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        Full Itiner-e dataset (WGS84).

    Returns
    -------
    gpd.GeoDataFrame
        Segments intersecting Italy, in the original CRS.
    """
    from shapely.geometry import box

    italy_box = box(ITALY_LON_MIN, ITALY_LAT_MIN, ITALY_LON_MAX, ITALY_LAT_MAX)

    # Use cx indexer for efficient bbox filtering
    try:
        italy_gdf = gdf.cx[ITALY_LON_MIN:ITALY_LON_MAX, ITALY_LAT_MIN:ITALY_LAT_MAX].copy()
    except Exception:
        # Fallback: explicit intersection test
        italy_gdf = gdf[gdf.intersects(italy_box)].copy()

    italy_gdf = italy_gdf.reset_index(drop=True)

    logger.info(
        "Itiner-e Italy filter: %d / %d segments retained.",
        len(italy_gdf), len(gdf),
    )
    return italy_gdf


# ---------------------------------------------------------------------------
# Convenience function: run both ingestion steps
# ---------------------------------------------------------------------------


def ingest_all(raw_dir: Path | None = None) -> tuple["pd.DataFrame", "gpd.GeoDataFrame"]:
    """
    Run complete ingestion for both Pleiades and Itiner-e.

    Returns
    -------
    tuple[pd.DataFrame, gpd.GeoDataFrame]
        (pleiades_italy_df, itinere_italy_gdf) — both filtered to Italy.
    """
    pleiades_raw = load_pleiades_csv(raw_dir)
    pleiades_italy = filter_pleiades_to_italy(pleiades_raw)

    itinere_raw = load_itinere_roads(raw_dir)
    inspect_itinere_schema(itinere_raw)
    itinere_italy = filter_itinere_to_italy(itinere_raw)

    return pleiades_italy, itinere_italy

