"""
src/gis_processing.py
=====================
GIS processing pipeline for the Roman Road Network Analysis.

Implements the two-stage spatial pipeline described in docs/METHODOLOGY.md:

  Stage 1 (this module):
    A. Reproject all data to EPSG:32632 (UTM Zone 32N) for metric operations.
    B. Clean road geometries (repair invalids, explode MultiLineStrings).
    C. Snap nearby road endpoint clusters to heal digitization gaps (250m tolerance).
    D. Snap each of the 45 cities to the nearest road network node (10km threshold).

  Stage 2 (network_analysis.py):
    Build the primary road topology graph and derive the 45-node city-to-city graph.

References
----------
- GeoPandas: Jordahl et al. (2014–). https://geopandas.org
- PyProj: https://pyproj4.github.io/pyproj/
- Shapely: https://shapely.readthedocs.io/
- Methodology: docs/METHODOLOGY.md §3
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import Point

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. CRS reprojection
# ---------------------------------------------------------------------------


def reproject_to_metric(gdf: "gpd.GeoDataFrame", target_crs: str = "EPSG:32632") -> "gpd.GeoDataFrame":
    """
    Reproject a GeoDataFrame to a metric CRS (default: EPSG:32632, UTM Zone 32N).

    All distance-dependent operations (snapping, buffering) must be performed
    after reprojection. Source data is expected in WGS84 (EPSG:4326).

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        Input GeoDataFrame (any CRS).
    target_crs : str
        Target CRS EPSG code string. Default: 'EPSG:32632'.

    Returns
    -------
    gpd.GeoDataFrame
        Reprojected GeoDataFrame.
    """
    if gdf.crs is None:
        logger.warning("GeoDataFrame has no CRS — setting to EPSG:4326 before reprojection.")
        gdf = gdf.set_crs("EPSG:4326")

    source_epsg = gdf.crs.to_epsg()
    target_epsg = int(target_crs.split(":")[1])

    if source_epsg == target_epsg:
        logger.info("GeoDataFrame already in %s — no reprojection needed.", target_crs)
        return gdf

    logger.info("Reprojecting from EPSG:%s → %s ...", source_epsg, target_crs)
    reprojected = gdf.to_crs(target_crs)
    logger.info("Reprojection complete. CRS: %s", reprojected.crs)
    return reprojected


def cities_to_geodataframe(
    catalog_df: "pd.DataFrame",
    lon_col: str = "lon",
    lat_col: str = "lat",
    crs: str = "EPSG:4326",
) -> "gpd.GeoDataFrame":
    """
    Convert the city catalog DataFrame to a GeoDataFrame of Point geometries.

    Parameters
    ----------
    catalog_df : pd.DataFrame
        45-city catalog from ``cities_catalog.get_cities_dataframe()``.
    lon_col, lat_col : str
        Column names for longitude and latitude.
    crs : str
        Source CRS (default: WGS84 EPSG:4326).

    Returns
    -------
    gpd.GeoDataFrame
        Cities as Point geometry GeoDataFrame in the given CRS.
    """
    import geopandas as gpd
    from shapely.geometry import Point

    geometry = [Point(row[lon_col], row[lat_col]) for _, row in catalog_df.iterrows()]
    gdf = gpd.GeoDataFrame(catalog_df.copy(), geometry=geometry, crs=crs)
    logger.info("Created cities GeoDataFrame: %d points in %s.", len(gdf), crs)
    return gdf


# ---------------------------------------------------------------------------
# 2. Road geometry cleaning
# ---------------------------------------------------------------------------


def clean_road_geometries(roads_gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    """
    Clean Itiner-e road geometries for topological processing.

    Steps:
      1. Drop null geometries.
      2. Repair invalid geometries with ``make_valid()``.
      3. Explode MultiLineString → individual LineString components.
      4. Drop empty or degenerate geometries (length == 0).
      5. Reset index.

    Parameters
    ----------
    roads_gdf : gpd.GeoDataFrame
        Itiner-e roads in metric CRS (EPSG:32632).

    Returns
    -------
    gpd.GeoDataFrame
        Cleaned roads with only valid, non-empty LineString geometries.
    """
    import shapely

    n_start = len(roads_gdf)
    logger.info("Cleaning road geometries: %d input features.", n_start)

    # 1. Drop null geometry
    gdf = roads_gdf.dropna(subset=["geometry"]).copy()
    dropped_null = n_start - len(gdf)
    if dropped_null:
        logger.warning("Dropped %d features with null geometry.", dropped_null)

    # 2. Repair invalid geometries
    invalid_mask = ~gdf.is_valid
    n_invalid = invalid_mask.sum()
    if n_invalid > 0:
        logger.info("Repairing %d invalid geometries with make_valid().", n_invalid)
        gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].apply(
            shapely.make_valid
        )

    # 3. Explode MultiLineString → LineString
    geom_types_before = gdf.geometry.geom_type.value_counts().to_dict()
    if "MultiLineString" in geom_types_before:
        gdf = gdf.explode(index_parts=False).reset_index(drop=True)
        logger.info(
            "Exploded MultiLineStrings: %d → %d features.",
            n_start, len(gdf),
        )

    # 4. Drop empty / zero-length geometries
    empty_mask = gdf.geometry.is_empty | (gdf.geometry.length == 0)
    n_empty = empty_mask.sum()
    if n_empty:
        logger.warning("Dropping %d empty or zero-length geometries.", n_empty)
        gdf = gdf[~empty_mask]

    gdf = gdf.reset_index(drop=True)
    logger.info(
        "Road geometry cleaning complete: %d → %d LineString features.",
        n_start, len(gdf),
    )
    return gdf


# ---------------------------------------------------------------------------
# 3. Compute road segment lengths
# ---------------------------------------------------------------------------


def compute_segment_lengths(roads_gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    """
    Add a ``length_m`` column (metres) and ``length_km`` column to road segments.

    Must be called after reprojection to a metric CRS.

    Parameters
    ----------
    roads_gdf : gpd.GeoDataFrame
        Roads in metric CRS (EPSG:32632).

    Returns
    -------
    gpd.GeoDataFrame
        Same GeoDataFrame with ``length_m`` and ``length_km`` columns added.
    """
    gdf = roads_gdf.copy()
    gdf["length_m"] = gdf.geometry.length
    gdf["length_km"] = gdf["length_m"] / 1000.0
    total_km = gdf["length_km"].sum()
    logger.info(
        "Segment lengths computed: %.1f km total road length across %d segments.",
        total_km, len(gdf),
    )
    return gdf


# ---------------------------------------------------------------------------
# 4. Extract road network nodes (endpoints)
# ---------------------------------------------------------------------------


def extract_road_nodes(roads_gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    """
    Extract all unique road segment endpoints as a GeoDataFrame of Points.

    Each LineString endpoint (start and end coordinates) becomes a node.
    Nearby endpoints within the snapping tolerance are merged later.

    Parameters
    ----------
    roads_gdf : gpd.GeoDataFrame
        Cleaned road segments in metric CRS.

    Returns
    -------
    gpd.GeoDataFrame
        Unique road endpoint Points in the same CRS.
        Columns: ``geometry``, ``node_id``.
    """
    import geopandas as gpd
    from shapely.geometry import Point

    endpoints = []
    for geom in roads_gdf.geometry:
        if geom is None or geom.is_empty:
            continue
        coords = list(geom.coords)
        if coords:
            endpoints.append(Point(coords[0]))
            endpoints.append(Point(coords[-1]))

    # Deduplicate exact duplicates
    unique_endpoints = list({(p.x, p.y): p for p in endpoints}.values())
    nodes_gdf = gpd.GeoDataFrame(
        {"node_id": range(len(unique_endpoints)), "geometry": unique_endpoints},
        crs=roads_gdf.crs,
    )
    logger.info("Extracted %d unique road endpoint nodes.", len(nodes_gdf))
    return nodes_gdf


# ---------------------------------------------------------------------------
# 5. City-to-road snapping
# ---------------------------------------------------------------------------


def snap_cities_to_roads(
    cities_metric_gdf: "gpd.GeoDataFrame",
    roads_metric_gdf: "gpd.GeoDataFrame",
    snap_threshold_m: float = 10_000.0,
    warn_threshold_m: float = 5_000.0,
) -> "gpd.GeoDataFrame":
    """
    Snap each city point to the nearest point on the road network.

    For each city, the nearest point on the nearest road segment is computed.
    The city's snapped geometry is the projected point on that segment.

    Parameters
    ----------
    cities_metric_gdf : gpd.GeoDataFrame
        City points in metric CRS (EPSG:32632).
    roads_metric_gdf : gpd.GeoDataFrame
        Cleaned road segments in metric CRS (EPSG:32632).
    snap_threshold_m : float
        Maximum distance (metres) to snap a city to a road.
        Cities beyond this threshold are flagged but still retained with
        their nearest road association (and logged as warnings).
    warn_threshold_m : float
        Distance threshold (metres) above which a WARNING is logged even
        if snapping is still within the outer threshold.

    Returns
    -------
    gpd.GeoDataFrame
        Cities GeoDataFrame with added columns:
        - ``snapped_geometry`` : Point — projected location on road network.
        - ``snap_distance_m``  : float — distance from original to snapped position.
        - ``snap_road_idx``    : int — index of nearest road segment.
        - ``snap_ok``          : bool — True if within snap_threshold_m.
    """
    from shapely.geometry import Point
    from shapely.ops import nearest_points

    cities = cities_metric_gdf.copy()
    snapped_geoms = []
    snap_distances = []
    snap_road_indices = []
    snap_ok_flags = []

    # Build a spatial index on roads for fast nearest-segment lookup
    road_sindex = roads_metric_gdf.sindex

    for _, city_row in cities.iterrows():
        city_pt = city_row.geometry
        latin_name = city_row.get("latin_name", "unknown")

        # Use spatial index to find candidate roads within a generous search radius
        search_radius = max(snap_threshold_m * 2, 20_000)  # double threshold for candidates
        candidates_idx = list(road_sindex.query(city_pt.buffer(search_radius)))

        if not candidates_idx:
            # No roads within search radius — try all roads (slow fallback)
            candidates_idx = list(range(len(roads_metric_gdf)))
            logger.warning(
                "%s: No road within %.0fm search radius — using full road set as fallback.",
                latin_name, search_radius,
            )

        # Find nearest road segment among candidates
        best_distance = float("inf")
        best_snapped_pt = None
        best_road_idx = -1

        for road_idx in candidates_idx:
            road_geom = roads_metric_gdf.iloc[road_idx].geometry
            if road_geom is None or road_geom.is_empty:
                continue
            dist = city_pt.distance(road_geom)
            if dist < best_distance:
                best_distance = dist
                nearest_pt, _ = nearest_points(city_pt, road_geom)
                best_snapped_pt = nearest_pt
                best_road_idx = road_idx

        # Log and flag
        snap_ok = best_distance <= snap_threshold_m

        if best_distance > snap_threshold_m:
            logger.error(
                "%s: Snap distance %.0fm EXCEEDS threshold %.0fm. "
                "City retained but flagged as uncertain (snap_ok=False).",
                latin_name, best_distance, snap_threshold_m,
            )
        elif best_distance > warn_threshold_m:
            logger.warning(
                "%s: Snap distance %.0fm > warn threshold %.0fm — manual inspection recommended.",
                latin_name, best_distance, warn_threshold_m,
            )
        else:
            logger.debug("%s: Snapped at %.0fm.", latin_name, best_distance)

        snapped_geoms.append(best_snapped_pt)
        snap_distances.append(best_distance)
        snap_road_indices.append(best_road_idx)
        snap_ok_flags.append(snap_ok)

    cities["snapped_geometry"] = snapped_geoms
    cities["snap_distance_m"] = snap_distances
    cities["snap_road_idx"] = snap_road_indices
    cities["snap_ok"] = snap_ok_flags

    n_warn = sum(d > warn_threshold_m and ok for d, ok in zip(snap_distances, snap_ok_flags))
    n_fail = sum(not ok for ok in snap_ok_flags)
    logger.info(
        "City snapping complete: %d cities snapped, %d warnings (>%.0fm), %d failures (>%.0fm).",
        len(cities), n_warn, warn_threshold_m, n_fail, snap_threshold_m,
    )
    return cities


# ---------------------------------------------------------------------------
# 6. Export snapping report
# ---------------------------------------------------------------------------


def export_snapping_report(
    snapped_cities: "gpd.GeoDataFrame",
    output_path,
) -> None:
    """
    Export a CSV report of city snapping results to ``data/interim/``.

    Parameters
    ----------
    snapped_cities : gpd.GeoDataFrame
        Output of ``snap_cities_to_roads()``.
    output_path : Path
        Destination CSV path (e.g., ``data/interim/snapping_report.csv``).
    """
    report_cols = [
        "pleiades_id", "latin_name", "modern_name", "region",
        "lon", "lat", "snap_distance_m", "snap_road_idx", "snap_ok",
    ]
    available = [c for c in report_cols if c in snapped_cities.columns]
    report = snapped_cities[available].copy()
    report["snap_distance_m"] = report["snap_distance_m"].round(1)
    report = report.sort_values("snap_distance_m", ascending=False)
    report.to_csv(output_path, index=False)
    logger.info("Snapping report written to %s (%d rows).", output_path, len(report))


# ---------------------------------------------------------------------------
# 7. Save / load interim GeoDataFrames
# ---------------------------------------------------------------------------


def save_interim_gdf(gdf: "gpd.GeoDataFrame", path, driver: str = "GPKG") -> None:
    """Save a GeoDataFrame to an interim file (GeoPackage by default)."""
    gdf.to_file(str(path), driver=driver)
    logger.info("Saved interim GeoDataFrame to %s (%d features).", path, len(gdf))


def load_interim_gdf(path) -> "gpd.GeoDataFrame":
    """Load a GeoDataFrame from an interim file."""
    import geopandas as gpd
    gdf = gpd.read_file(str(path))
    logger.info("Loaded interim GeoDataFrame from %s (%d features).", path, len(gdf))
    return gdf

