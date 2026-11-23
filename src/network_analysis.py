"""
src/network_analysis.py
=======================
NetworkX graph construction and centrality analysis for the Roman Road Network.

Implements the two-stage graph construction described in docs/METHODOLOGY.md §4:

  Stage A — Road Topology Graph (G_road):
    Build a weighted undirected graph from all road segments, where nodes are
    snapped road endpoints and edges are individual road segments with length_km
    as the edge weight.

  Stage B — City-to-City Graph (G_cities, 45 nodes):
    Derive a simplified graph where:
    - V = the 45 selected Roman cities.
    - An edge e(u,v) exists if a road path connects u and v without passing
      through any other city w in V.
    - Edge weight = total road distance (km) along the shortest path.

Centrality Calculations:
  - Degree Centrality (unweighted): nx.degree_centrality(G)
  - Betweenness Centrality, unweighted: nx.betweenness_centrality(G)
  - Betweenness Centrality, distance-weighted: nx.betweenness_centrality(G, weight='length_km')

References
----------
- NetworkX: Hagberg et al. (2008). https://networkx.org
- Methodology: docs/METHODOLOGY.md §4
- Pažout et al. (2026). Nature Communications, 17, 9551.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import geopandas as gpd
    import networkx as nx
    import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage A: Road Topology Graph
# ---------------------------------------------------------------------------


def build_road_topology_graph(
    roads_gdf: "gpd.GeoDataFrame",
    weight_col: str = "length_km",
    coord_precision: int = 1,
) -> "nx.Graph":
    """
    Build a weighted undirected graph from road segment geometries.

    Each road segment's start and end coordinates become graph nodes.
    Coordinates are rounded to ``coord_precision`` metres (after metric
    projection) to merge nearby snapped endpoints into the same node.

    Parameters
    ----------
    roads_gdf : gpd.GeoDataFrame
        Cleaned road segments in metric CRS (EPSG:32632).
        Must have a ``length_km`` column (from ``compute_segment_lengths()``).
    weight_col : str
        Edge weight attribute. Default: 'length_km'.
    coord_precision : int
        Decimal places for coordinate rounding (metres). Default: 1 (10cm precision).
        Nearby endpoints snapped within 250m tolerance share the same rounded key
        due to the prior snapping step.

    Returns
    -------
    networkx.Graph
        Road topology graph G_road.
        Nodes: (x_rounded, y_rounded) coordinate tuples (EPSG:32632 metres).
        Edges: road segment connections with attributes:
            - length_km : float
            - road_name : str (if available)
            - segment_idx : int (original GeoDataFrame row index)
    """
    import networkx as nx

    G = nx.Graph()

    for seg_idx, row in roads_gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        coords = list(geom.coords)
        if len(coords) < 2:
            continue

        # Round coordinates to merge nearly-identical snapped endpoints
        u = (round(coords[0][0], coord_precision), round(coords[0][1], coord_precision))
        v = (round(coords[-1][0], coord_precision), round(coords[-1][1], coord_precision))

        if u == v:
            continue  # Skip degenerate zero-length loops

        length_km = row.get(weight_col, 0.0)
        road_name = row.get("road_name", row.get("name", row.get("NAME", "")))

        G.add_edge(
            u, v,
            length_km=float(length_km),
            road_name=str(road_name) if road_name else "",
            segment_idx=int(seg_idx),
        )

    logger.info(
        "Road topology graph: %d nodes, %d edges, density=%.4f.",
        G.number_of_nodes(), G.number_of_edges(), nx.density(G),
    )
    return G


# ---------------------------------------------------------------------------
# Stage B: City-to-City Simplified Graph (45 nodes)
# ---------------------------------------------------------------------------


def build_city_graph(
    G_road: "nx.Graph",
    snapped_cities: "gpd.GeoDataFrame",
    coord_precision: int = 1,
) -> tuple["nx.Graph", dict[int, Any]]:
    r"""
    Derive the 45-node City-to-City graph from the road topology graph.

    Algorithm:
      1. Map each city to its nearest node in G_road (using snapped coordinates).
      2. For each pair of cities (u, v), compute the shortest road path in G_road.
      3. Add edge (u, v) to G_cities if the shortest path exists AND does not
         pass through any other city node c ∈ V \ {u, v}.
         (This implements 'no intermediate city' contraction.)
      4. Store the total road distance as the edge weight 'length_km'.

    Parameters
    ----------
    G_road : nx.Graph
        Road topology graph from ``build_road_topology_graph()``.
    snapped_cities : gpd.GeoDataFrame
        Cities GeoDataFrame with 'snapped_geometry' column (EPSG:32632).
        Must include 'pleiades_id', 'latin_name' columns.
    coord_precision : int
        Must match the precision used in ``build_road_topology_graph()``.

    Returns
    -------
    tuple[nx.Graph, dict]
        - G_cities: 45-node city graph.
          Nodes: pleiades_id (int), with attrs: latin_name, modern_name, lon, lat, region.
          Edges: (pleiades_id_u, pleiades_id_v) with attrs: length_km, road_names, n_segments.
        - city_node_map: dict mapping pleiades_id → nearest G_road node coordinate tuple.
    """
    import networkx as nx

    # --- Step 1: Map cities → road graph nodes ---
    city_node_map: dict[int, tuple] = {}  # pleiades_id → G_road node key
    node_to_city: dict[tuple, int] = {}   # G_road node key → pleiades_id

    road_nodes = list(G_road.nodes())
    if not road_nodes:
        raise ValueError("Road topology graph has no nodes — check road data loading.")

    road_coords = [(n[0], n[1]) for n in road_nodes]

    for _, city_row in snapped_cities.iterrows():
        pid = int(city_row["pleiades_id"])
        snapped_pt = city_row.get("snapped_geometry")

        if snapped_pt is None or snapped_pt.is_empty:
            # Fallback: use original city geometry
            snapped_pt = city_row.geometry
            logger.warning(
                "%s (pid=%d): No snapped geometry — using original city point.",
                city_row.get("latin_name", "unknown"), pid,
            )

        # Round snapped coords to find nearest G_road node
        sx = round(snapped_pt.x, coord_precision)
        sy = round(snapped_pt.y, coord_precision)
        candidate_key = (sx, sy)

        if candidate_key in G_road.nodes:
            city_node_map[pid] = candidate_key
        else:
            # Find nearest node by Euclidean distance
            dists = [(abs(sx - rx) + abs(sy - ry), (rx, ry)) for rx, ry in road_coords]
            dists.sort()
            nearest_key = dists[0][1]
            nearest_dist = dists[0][0]
            city_node_map[pid] = nearest_key
            if nearest_dist > 5000:
                logger.warning(
                    "%s (pid=%d): Mapped to road node %.0fm away (snapped point not in graph).",
                    city_row.get("latin_name", "?"), pid, nearest_dist,
                )

        node_to_city[city_node_map[pid]] = pid

    logger.info("Mapped %d cities to road graph nodes.", len(city_node_map))

    # City pleiades_id set for intermediate-city detection
    city_pids = set(city_node_map.keys())
    city_road_nodes = set(city_node_map.values())

    # --- Step 2: Build city graph ---
    G_cities = nx.Graph()

    # Add nodes with attributes
    for _, city_row in snapped_cities.iterrows():
        pid = int(city_row["pleiades_id"])
        G_cities.add_node(
            pid,
            latin_name=str(city_row.get("latin_name", "")),
            modern_name=str(city_row.get("modern_name", "")),
            region=str(city_row.get("region", "")),
            lon=float(city_row.get("lon", 0)),
            lat=float(city_row.get("lat", 0)),
            snap_ok=bool(city_row.get("snap_ok", True)),
        )

    # Identify the largest connected component of G_road for shortest paths
    if not nx.is_connected(G_road):
        components = sorted(nx.connected_components(G_road), key=len, reverse=True)
        logger.warning(
            "Road graph has %d connected components. Using largest (%d nodes).",
            len(components), len(components[0]),
        )
        G_road_main = G_road.subgraph(components[0]).copy()
    else:
        G_road_main = G_road

    # --- Step 3: City-pair shortest paths with intermediate-city check ---
    city_list = list(city_node_map.keys())
    edges_added = 0
    edges_skipped_disconnected = 0
    edges_skipped_intermediate = 0

    for i, pid_u in enumerate(city_list):
        for j, pid_v in enumerate(city_list):
            if j <= i:
                continue  # undirected, only process each pair once

            road_node_u = city_node_map[pid_u]
            road_node_v = city_node_map[pid_v]

            # Skip if either node isn't in the main component
            if road_node_u not in G_road_main or road_node_v not in G_road_main:
                edges_skipped_disconnected += 1
                continue

            try:
                path_nodes = nx.shortest_path(
                    G_road_main, road_node_u, road_node_v, weight="length_km"
                )
            except nx.NetworkXNoPath:
                edges_skipped_disconnected += 1
                continue

            # Check if any intermediate node belongs to another city
            intermediate_nodes = set(path_nodes[1:-1])
            intermediate_cities = intermediate_nodes & city_road_nodes
            # Remove u and v themselves if they appear
            intermediate_cities -= {road_node_u, road_node_v}

            if intermediate_cities:
                edges_skipped_intermediate += 1
                continue

            # Compute total road distance along the path
            total_km = 0.0
            road_names = set()
            n_segments = len(path_nodes) - 1

            for k in range(len(path_nodes) - 1):
                edge_data = G_road_main.edges[path_nodes[k], path_nodes[k + 1]]
                total_km += edge_data.get("length_km", 0.0)
                rn = edge_data.get("road_name", "")
                if rn:
                    road_names.add(rn)

            G_cities.add_edge(
                pid_u, pid_v,
                length_km=round(total_km, 3),
                road_names=", ".join(sorted(road_names)) if road_names else "",
                n_segments=n_segments,
            )
            edges_added += 1

    logger.info(
        "City-to-City graph: %d nodes, %d edges added, "
        "%d skipped (disconnected), %d skipped (intermediate city).",
        G_cities.number_of_nodes(), edges_added,
        edges_skipped_disconnected, edges_skipped_intermediate,
    )
    return G_cities, city_node_map


# ---------------------------------------------------------------------------
# Graph Diagnostics
# ---------------------------------------------------------------------------


def compute_graph_diagnostics(G: "nx.Graph") -> dict:
    """
    Compute global network statistics for the city graph.

    Parameters
    ----------
    G : nx.Graph
        City-to-city graph.

    Returns
    -------
    dict
        Dictionary of graph-level statistics.
    """
    import networkx as nx

    stats: dict[str, Any] = {
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "density": round(nx.density(G), 6),
        "n_connected_components": nx.number_connected_components(G),
        "is_connected": nx.is_connected(G),
    }

    # Compute diameter and avg path length on largest component only
    if stats["is_connected"]:
        working_G = G
    else:
        largest_cc = max(nx.connected_components(G), key=len)
        working_G = G.subgraph(largest_cc)
        stats["largest_component_size"] = len(largest_cc)

    try:
        stats["diameter"] = nx.diameter(working_G)
        stats["avg_shortest_path_length"] = round(
            nx.average_shortest_path_length(working_G), 4
        )
        stats["avg_shortest_path_length_km"] = round(
            nx.average_shortest_path_length(working_G, weight="length_km"), 2
        )
    except Exception as e:
        logger.warning("Could not compute diameter / avg path length: %s", e)
        stats["diameter"] = None
        stats["avg_shortest_path_length"] = None
        stats["avg_shortest_path_length_km"] = None

    for key, val in stats.items():
        logger.info("  Graph stat | %-35s : %s", key, val)

    return stats


# ---------------------------------------------------------------------------
# Centrality Calculations
# ---------------------------------------------------------------------------


def compute_centralities(G: "nx.Graph") -> "pd.DataFrame":
    """
    Compute Degree and Betweenness Centrality for all cities in the graph.

    Computes:
      - Raw degree (k_v)
      - Degree centrality C_D(v) = k_v / (n-1)
      - Unweighted betweenness centrality C_B(v) [topological steps]
      - Weighted betweenness centrality C_B_w(v) [road distance in km]

    Parameters
    ----------
    G : nx.Graph
        City-to-city graph (nodes = pleiades_id).

    Returns
    -------
    pd.DataFrame
        One row per city with columns:
        pleiades_id, latin_name, modern_name, region, lon, lat,
        degree, degree_centrality,
        betweenness_centrality, betweenness_centrality_weighted,
        degree_rank, betweenness_rank, betweenness_weighted_rank.
    """
    import networkx as nx
    import pandas as pd

    logger.info("Computing centrality measures for %d-node city graph...", G.number_of_nodes())

    # Node attributes
    node_attrs = dict(G.nodes(data=True))

    # Degree
    degree_dict = dict(G.degree())
    degree_centrality = nx.degree_centrality(G)

    # Betweenness — unweighted
    logger.info("Computing unweighted betweenness centrality...")
    betweenness = nx.betweenness_centrality(G, normalized=True)

    # Betweenness — weighted by road distance
    logger.info("Computing distance-weighted betweenness centrality...")
    betweenness_weighted = nx.betweenness_centrality(
        G, normalized=True, weight="length_km"
    )

    # Build results DataFrame
    rows = []
    for pid in G.nodes():
        attrs = node_attrs.get(pid, {})
        rows.append(
            {
                "pleiades_id": pid,
                "latin_name": attrs.get("latin_name", ""),
                "modern_name": attrs.get("modern_name", ""),
                "region": attrs.get("region", ""),
                "lon": attrs.get("lon", 0.0),
                "lat": attrs.get("lat", 0.0),
                "degree": degree_dict[pid],
                "degree_centrality": round(degree_centrality[pid], 6),
                "betweenness_centrality": round(betweenness[pid], 6),
                "betweenness_centrality_weighted": round(betweenness_weighted[pid], 6),
            }
        )

    df = pd.DataFrame(rows)

    # Add rank columns (rank 1 = highest value)
    df["degree_rank"] = df["degree_centrality"].rank(ascending=False, method="min").astype(int)
    df["betweenness_rank"] = df["betweenness_centrality"].rank(ascending=False, method="min").astype(int)
    df["betweenness_weighted_rank"] = df["betweenness_centrality_weighted"].rank(ascending=False, method="min").astype(int)

    df = df.sort_values("betweenness_rank").reset_index(drop=True)

    logger.info(
        "Centrality computation complete. Top city by betweenness: %s (%.4f).",
        df.iloc[0]["latin_name"] if len(df) > 0 else "N/A",
        df.iloc[0]["betweenness_centrality"] if len(df) > 0 else 0,
    )
    return df


def get_top_n_cities(centrality_df: "pd.DataFrame", n: int = 10, metric: str = "betweenness_centrality") -> "pd.DataFrame":
    """
    Return the top-N cities sorted by the given centrality metric.

    Parameters
    ----------
    centrality_df : pd.DataFrame
        Output of ``compute_centralities()``.
    n : int
        Number of top cities to return.
    metric : str
        Column to rank by. Default: 'betweenness_centrality'.

    Returns
    -------
    pd.DataFrame
        Top-N cities with rank, Latin name, modern name, and centrality scores.
    """
    top = centrality_df.nlargest(n, metric).copy()
    top.insert(0, "rank", range(1, len(top) + 1))
    return top.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Graph Export / Import
# ---------------------------------------------------------------------------


def export_graph_to_csv(
    centrality_df: "pd.DataFrame",
    diagnostics: dict,
    output_dir,
) -> None:
    """
    Export centrality results and graph diagnostics to CSV files.

    Writes:
      - ``data/processed/centrality_results.csv`` — full 45-city centrality table.
      - ``data/exports/top10_cities.csv`` — top-10 by betweenness centrality.
      - ``data/exports/graph_diagnostics.csv`` — global network statistics.
      - ``data/exports/top10_cities.md`` — Markdown table for seminar report.

    Parameters
    ----------
    centrality_df : pd.DataFrame
        Full centrality results from ``compute_centralities()``.
    diagnostics : dict
        Output of ``compute_graph_diagnostics()``.
    output_dir : Path
        Base output directory (``data/`` root).
    """
    import pandas as pd
    from src.config import EXPORTS_DIR, PROCESSED_DIR

    # Full centrality results → processed/
    centrality_path = PROCESSED_DIR / "centrality_results.csv"
    centrality_df.to_csv(centrality_path, index=False)
    logger.info("Centrality results saved to %s", centrality_path)

    # Top-10 table → exports/
    top10 = get_top_n_cities(centrality_df, n=10)
    top10_csv_path = EXPORTS_DIR / "top10_cities.csv"
    top10.to_csv(top10_csv_path, index=False)
    logger.info("Top-10 cities CSV saved to %s", top10_csv_path)

    # Markdown table
    _export_top10_markdown(top10, EXPORTS_DIR / "top10_cities.md")

    # Graph diagnostics
    diag_df = pd.DataFrame([diagnostics])
    diag_path = EXPORTS_DIR / "graph_diagnostics.csv"
    diag_df.to_csv(diag_path, index=False)
    logger.info("Graph diagnostics saved to %s", diag_path)


def _export_top10_markdown(top10_df: "pd.DataFrame", path) -> None:
    """Write the Top-10 cities table as a Markdown file."""
    display_cols = [
        "rank", "latin_name", "modern_name", "region",
        "degree", "degree_centrality", "betweenness_centrality",
        "betweenness_centrality_weighted",
    ]
    cols = [c for c in display_cols if c in top10_df.columns]
    df = top10_df[cols].copy()

    header = "# Top 10 Most Connected Cities — Roman Road Network, Italy\n\n"
    header += "_Ranked by Betweenness Centrality (unweighted). Source: Itiner-e + Pleiades._\n\n"

    lines = [header]
    col_headers = {
        "rank": "Rank",
        "latin_name": "Latin Name",
        "modern_name": "Modern Name",
        "region": "Region",
        "degree": "Degree (k)",
        "degree_centrality": "Degree Centrality",
        "betweenness_centrality": "Betweenness (unweighted)",
        "betweenness_centrality_weighted": "Betweenness (distance-weighted)",
    }
    headers = [col_headers.get(c, c) for c in cols]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for _, row in df.iterrows():
        values = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                values.append(f"{v:.4f}")
            else:
                values.append(str(v))
        lines.append("| " + " | ".join(values) + " |")

    lines.append("\n")
    lines.append("## Notes\n")
    lines.append("- **Betweenness Centrality**: Fraction of shortest road paths between all city pairs that pass through this city.\n")
    lines.append("- **Degree (k)**: Number of direct road connections to other selected cities.\n")
    lines.append("- **Distance-weighted betweenness** uses road length (km) as path cost.\n")
    lines.append("- All values normalized to [0, 1].\n")
    lines.append("- Source: Itiner-e (de Soto et al., 2025, CC BY 4.0) + Pleiades (2025, CC BY 3.0 US).\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Top-10 Markdown table saved to %s", path)

