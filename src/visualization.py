"""
src/visualization.py
====================
Static Matplotlib maps, interactive Folium HTML map, and export helpers.

Outputs generated (all in data/exports/):
  - roman_roads_map.png         — 300 DPI static publication map
  - roman_roads_interactive.html — Standalone Folium interactive map
  - top10_cities.csv / .md      — (also written by network_analysis.py)
  - clustered_cities.geojson    — (also written by clustering.py)

References
----------
- Matplotlib: Hunter (2007). Computing in Science & Engineering, 9(3), 90–95.
- Folium: https://python-visualization.github.io/folium/
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd

logger = logging.getLogger(__name__)

# Colourblind-accessible cluster palette (Okabe–Ito)
CLUSTER_COLOURS = {
    "A": "#E69F00",  # Orange   — Hub cities
    "B": "#56B4E9",  # Sky blue — Regional connectors
    "C": "#009E73",  # Green    — Peripheral cities
    "unknown": "#999999",
}

CLUSTER_LEGEND_LABELS = {
    "A": "Cluster A — High-Connectivity Hubs",
    "B": "Cluster B — Regional Connectors",
    "C": "Cluster C — Peripheral Cities",
}


# ---------------------------------------------------------------------------
# Static Matplotlib map
# ---------------------------------------------------------------------------


def create_static_map(
    clustered_df: "pd.DataFrame",
    roads_gdf: "gpd.GeoDataFrame | None",
    output_path: Path,
    dpi: int = 300,
    figsize: tuple = (14, 16),
) -> None:
    """
    Generate a publication-quality static map of Roman Italy.

    Features:
      - Road network (if roads_gdf provided) as thin grey lines.
      - City nodes sized by betweenness centrality (scaled 30–300 pt²).
      - City nodes coloured by K-Means cluster label.
      - City labels for high-betweenness cities.
      - Legend, scale annotation, data attribution footer.

    Parameters
    ----------
    clustered_df : pd.DataFrame
        Clustered cities with lon, lat, betweenness_centrality, cluster_label.
    roads_gdf : gpd.GeoDataFrame or None
        Italian road segments in WGS84 (EPSG:4326) for background layer.
        Pass None to omit road lines.
    output_path : Path
        Output file path (PNG recommended).
    dpi : int
        Export resolution. Default: 300.
    figsize : tuple
        Figure dimensions in inches. Default: (14, 16).
    """
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt
    import numpy as np

    logger.info("Creating static publication map → %s (DPI=%d)...", output_path, dpi)

    fig, ax = plt.subplots(figsize=figsize, facecolor="#F5F0E8")
    ax.set_facecolor("#E8F4F8")  # Light blue background for sea

    # --- Draw road network ---
    if roads_gdf is not None and len(roads_gdf) > 0:
        try:
            roads_gdf.plot(
                ax=ax,
                color="#8B7355",
                linewidth=0.4,
                alpha=0.6,
                zorder=2,
                label="Roman roads (Itiner-e)",
            )
            logger.info("Roads plotted: %d segments.", len(roads_gdf))
        except Exception as e:
            logger.warning("Could not plot roads: %s", e)

    # --- Scale marker sizes by betweenness centrality ---
    bc = clustered_df["betweenness_centrality"].values
    bc_min, bc_max = bc.min(), bc.max()
    bc_range = bc_max - bc_min if bc_max > bc_min else 1.0
    # Scale to marker area 30–350 pt² (np.sqrt for visual radius scaling)
    marker_sizes = 30 + 320 * ((bc - bc_min) / bc_range) ** 0.7

    # --- Draw city markers by cluster ---
    for label in ["A", "B", "C"]:
        mask = clustered_df["cluster_label"] == label
        if not mask.any():
            continue
        subset = clustered_df[mask]
        sizes = marker_sizes[mask.values]
        colour = CLUSTER_COLOURS.get(label, "#999999")

        ax.scatter(
            subset["lon"], subset["lat"],
            s=sizes,
            c=colour,
            edgecolors="black",
            linewidths=0.5,
            alpha=0.88,
            zorder=5,
            label=CLUSTER_LEGEND_LABELS.get(label, label),
        )

    # --- Labels for top-15 cities by betweenness ---
    label_threshold = clustered_df["betweenness_centrality"].nlargest(15).min()
    for _, row in clustered_df.iterrows():
        if row["betweenness_centrality"] >= label_threshold:
            ax.annotate(
                row["latin_name"],
                xy=(row["lon"], row["lat"]),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=6.5,
                fontfamily="serif",
                color="#2C1810",
                zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", alpha=0.6, ec="none"),
            )

    # --- Map extent: Italy ---
    ax.set_xlim(6.5, 18.8)
    ax.set_ylim(36.4, 47.4)

    # --- Title and labels ---
    ax.set_title(
        "Roman Road Network — Italy\nCity Connectivity Analysis",
        fontsize=14, fontfamily="serif", fontweight="bold", pad=14, color="#2C1810",
    )
    ax.set_xlabel("Longitude (°E) · WGS84", fontsize=9, color="#555")
    ax.set_ylabel("Latitude (°N) · WGS84", fontsize=9, color="#555")

    # --- Legend ---
    legend_patches = [
        mpatches.Patch(color=CLUSTER_COLOURS[l], label=CLUSTER_LEGEND_LABELS[l])
        for l in ["A", "B", "C"]
    ]
    size_handles = [
        ax.scatter([], [], s=30, c="#888", edgecolors="black", lw=0.5, label="Low centrality"),
        ax.scatter([], [], s=150, c="#888", edgecolors="black", lw=0.5, label="Medium centrality"),
        ax.scatter([], [], s=330, c="#888", edgecolors="black", lw=0.5, label="High centrality"),
    ]
    legend = ax.legend(
        handles=legend_patches + size_handles,
        title="K-Means Cluster (k=3)\n& Node size = Betweenness Centrality",
        title_fontsize=8,
        fontsize=8,
        loc="lower left",
        framealpha=0.9,
        edgecolor="#888",
    )
    ax.add_artist(legend)

    # --- Attribution footer ---
    fig.text(
        0.5, 0.01,
        "Data: Itiner-e (de Soto et al., 2025, CC BY 4.0) · Pleiades (2025, CC BY 3.0 US)\n"
        "DH Lab Seminar · Autumn 2026",
        ha="center", fontsize=7, color="#777", style="italic",
    )

    # --- Grid ---
    ax.grid(True, linestyle="--", alpha=0.3, color="#999", zorder=1)
    ax.tick_params(labelsize=8)

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("Static map saved: %s", output_path)


# ---------------------------------------------------------------------------
# Interactive Folium map
# ---------------------------------------------------------------------------


def create_folium_map(
    clustered_df: "pd.DataFrame",
    roads_gdf: "gpd.GeoDataFrame | None",
    output_path: Path,
    center_lat: float = 42.5,
    center_lon: float = 12.5,
    zoom: int = 6,
) -> None:
    """
    Generate an interactive standalone Folium HTML map.

    Features:
      - CartoDB Positron base tiles (clean, light background).
      - Road network as a GeoJSON overlay layer (if roads_gdf provided).
      - City CircleMarkers sized by betweenness centrality, coloured by cluster.
      - Rich popups: Latin name, modern name, Pleiades link, centrality scores,
        cluster label, region.
      - LayerControl: toggle roads/cities.
      - Legend as custom HTML control.

    Parameters
    ----------
    clustered_df : pd.DataFrame
        Clustered cities with all required columns.
    roads_gdf : gpd.GeoDataFrame or None
        Italian road segments in WGS84 (EPSG:4326). Pass None to omit.
    output_path : Path
        Output .html file path.
    """
    import folium
    import folium.plugins

    logger.info("Creating Folium interactive map → %s...", output_path)

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr=(
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>; '
            'Roads: <a href="https://itiner-e.org">Itiner-e</a> (CC BY 4.0); '
            'Settlements: <a href="https://pleiades.stoa.org">Pleiades</a> (CC BY 3.0 US)'
        ),
        name="CartoDB Positron",
        control_scale=True,
    )

    # --- Fullscreen plugin ---
    try:
        folium.plugins.Fullscreen(
            position="topright",
            title="Expand map to fullscreen",
            title_cancel="Exit fullscreen",
            force_separate_button=True,
        ).add_to(m)
    except Exception as e:
        logger.warning("Could not add folium plugin: %s", e)

    # --- Road network layer ---
    if roads_gdf is not None and len(roads_gdf) > 0:
        try:
            road_layer = folium.FeatureGroup(name="Roman Consular Highways (Itiner-e)", show=True)
            folium.GeoJson(
                roads_gdf.__geo_interface__,
                style_function=lambda f: {
                    "color": "#8B5E3C",
                    "weight": 1.5,
                    "opacity": 0.65,
                },
                highlight_function=lambda f: {
                    "color": "#7c2d37",
                    "weight": 3.0,
                    "opacity": 0.95,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=[c for c in ["road_name", "length_km"] if c in roads_gdf.columns],
                    aliases=["Consular Route:", "Length (km):"],
                    sticky=False,
                ),
            ).add_to(road_layer)
            road_layer.add_to(m)
            logger.info("Road layer added to Folium map: %d segments.", len(roads_gdf))
        except Exception as e:
            logger.warning("Could not add road layer to Folium map: %s", e)

    # --- City markers by cluster ---
    bc = clustered_df["betweenness_centrality"].values
    bc_min, bc_max = bc.min(), bc.max()
    bc_range = bc_max - bc_min if bc_max > bc_min else 1.0

    cluster_badge_styles = {
        "A": {"bg": "#fef3c7", "text": "#92400e", "border": "#fde68a", "label": "Macro-Hub"},
        "B": {"bg": "#e0f2fe", "text": "#075985", "border": "#bae6fd", "label": "Regional Connector"},
        "C": {"bg": "#ecfdf5", "text": "#065f46", "border": "#a7f3d0", "label": "Peripheral / Port"},
    }

    for label in ["A", "B", "C"]:
        cluster_layer = folium.FeatureGroup(
            name=f"Cluster {label} — {CLUSTER_LEGEND_LABELS.get(label, label)}",
            show=True,
        )
        colour = CLUSTER_COLOURS.get(label, "#999999")
        badge_style = cluster_badge_styles.get(label, {"bg": "#f3f4f6", "text": "#374151", "border": "#d1d5db", "label": "Cluster"})
        mask = clustered_df["cluster_label"] == label
        subset = clustered_df[mask]

        for _, row in subset.iterrows():
            bc_val = float(row["betweenness_centrality"])
            # Radius: 5–18 px
            radius = 5 + 13 * ((bc_val - bc_min) / bc_range) ** 0.6
            bc_pct = min(100.0, max(5.0, (bc_val / (bc_max if bc_max > 0 else 1.0)) * 100))

            pleiades_url = f"https://pleiades.stoa.org/places/{int(row['pleiades_id'])}"

            popup_html = f"""
            <div style="font-family:'Inter',system-ui,-apple-system,sans-serif; min-width:240px; padding:2px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:{badge_style['text']}; background:{badge_style['bg']}; padding:2px 8px; border-radius:9999px; border:1px solid {badge_style['border']};">
                  Cluster {label} · {badge_style['label']}
                </span>
                <span style="font-size:11px; font-weight:600; color:#4b5563;">Rank #{row.get('betweenness_rank', '?')}</span>
              </div>
              <h4 style="margin:2px 0 2px 0; font-family:'Lora',Georgia,serif; font-size:16px; font-weight:700; color:#111827;">{row['latin_name']}</h4>
              <div style="font-size:12px; color:#4b5563; margin-bottom:8px;">{row['modern_name']} · <span style="color:#6b7280;">{row['region']}</span></div>
              
              <div style="background:#f9fafb; border:1px solid #e5e7eb; border-radius:6px; padding:8px 10px; margin-bottom:8px; font-size:11px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                  <span style="color:#6b7280;">Betweenness:</span>
                  <strong style="color:#111827;">{bc_val:.4f}</strong>
                </div>
                <div style="height:4px; width:100%; background:#e5e7eb; border-radius:2px; margin-bottom:6px; overflow:hidden;">
                  <div style="height:100%; width:{bc_pct:.1f}%; background:#7c2d37; border-radius:2px;"></div>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                  <span style="color:#6b7280;">Direct Links (Degree):</span>
                  <strong style="color:#111827;">{int(row['degree'])} ({row['degree_centrality']:.4f})</strong>
                </div>
                <div style="display:flex; justify-content:space-between;">
                  <span style="color:#6b7280;">Distance-Weighted BC:</span>
                  <strong style="color:#111827;">{float(row.get('betweenness_centrality_weighted', 0)):.4f}</strong>
                </div>
              </div>
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:10px; color:#9ca3af;">Pleiades #{int(row['pleiades_id'])}</span>
                <a href="{pleiades_url}" target="_blank" style="font-size:11px; color:#7c2d37; text-decoration:none; font-weight:600;">
                  Gazetteer Record &rarr;
                </a>
              </div>
            </div>"""

            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=radius,
                color="#111827",
                weight=0.8,
                fill=True,
                fill_color=colour,
                fill_opacity=0.88,
                popup=folium.Popup(popup_html, max_width=290),
                tooltip=f"<b>{row['latin_name']}</b> ({row['modern_name']}) — Cluster {label} · BC #{row.get('betweenness_rank', '?')}",
            ).add_to(cluster_layer)

        cluster_layer.add_to(m)

    # --- Layer control ---
    folium.LayerControl(collapsed=False).add_to(m)

    # --- Custom legend ---
    legend_html = """
    <div style="position:fixed; bottom:25px; left:20px; z-index:9999;
                background:rgba(255,255,255,0.95); backdrop-filter:blur(4px);
                padding:12px 16px; border-radius:8px; border:1px solid #e5e7eb;
                font-family:'Inter',system-ui,-apple-system,sans-serif; font-size:11px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width:260px;">
      <div style="font-family:'Lora',serif; font-weight:700; font-size:13px; color:#111827; margin-bottom:2px;">K-Means Clusters (k=3)</div>
      <div style="color:#6b7280; font-size:10px; margin-bottom:8px;">Node radius ∝ Betweenness Centrality</div>
      <div style="display:flex; align-items:center; margin-bottom:4px;">
        <span style="background:#E69F00; width:10px; height:10px; border-radius:50%; display:inline-block; border:1px solid #111; margin-right:8px; flex-shrink:0;"></span>
        <span><strong>Cluster A:</strong> Macro-Hubs</span>
      </div>
      <div style="display:flex; align-items:center; margin-bottom:4px;">
        <span style="background:#56B4E9; width:10px; height:10px; border-radius:50%; display:inline-block; border:1px solid #111; margin-right:8px; flex-shrink:0;"></span>
        <span><strong>Cluster B:</strong> Regional Connectors</span>
      </div>
      <div style="display:flex; align-items:center; margin-bottom:8px;">
        <span style="background:#009E73; width:10px; height:10px; border-radius:50%; display:inline-block; border:1px solid #111; margin-right:8px; flex-shrink:0;"></span>
        <span><strong>Cluster C:</strong> Peripheral & Port Termini</span>
      </div>
      <div style="font-size:9.5px; color:#9ca3af; border-top:1px solid #f3f4f6; padding-top:6px;">
        Itiner-e (CC BY 4.0) · Pleiades (CC BY 3.0 US)
      </div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save(str(output_path))
    logger.info("Folium interactive map saved: %s", output_path)


# ---------------------------------------------------------------------------
# Centrality bar chart (Matplotlib, for static export)
# ---------------------------------------------------------------------------


def create_centrality_chart(
    centrality_df: "pd.DataFrame",
    output_path: Path,
    metric: str = "betweenness_centrality",
    top_n: int = 20,
    figsize: tuple = (12, 7),
) -> None:
    """
    Create a horizontal bar chart of top cities by centrality metric.

    Parameters
    ----------
    centrality_df : pd.DataFrame
        Centrality results (may include cluster_label column).
    output_path : Path
        Output PNG path.
    metric : str
        Column to rank by.
    top_n : int
        Number of top cities to display.
    """
    import matplotlib.pyplot as plt

    df = centrality_df.nlargest(top_n, metric).copy()
    df = df.sort_values(metric, ascending=True)

    colours = [CLUSTER_COLOURS.get(row.get("cluster_label", "unknown"), "#999")
               for _, row in df.iterrows()]

    fig, ax = plt.subplots(figsize=figsize, facecolor="white")
    bars = ax.barh(df["latin_name"], df[metric], color=colours, edgecolor="black", linewidth=0.4)

    ax.set_xlabel(
        metric.replace("_", " ").title() + " (normalized 0–1)",
        fontsize=10,
    )
    ax.set_title(
        f"Top {top_n} Roman Cities by {metric.replace('_', ' ').title()}\n(Roman Italy, Itiner-e dataset)",
        fontsize=12, fontfamily="serif", fontweight="bold",
    )
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.tick_params(labelsize=9)

    # Legend patches
    import matplotlib.patches as mpatches
    patches = [mpatches.Patch(color=CLUSTER_COLOURS[l], label=CLUSTER_LEGEND_LABELS[l])
               for l in ["A", "B", "C"] if l in CLUSTER_COLOURS]
    ax.legend(handles=patches, fontsize=8, loc="lower right")

    fig.text(0.5, -0.02,
             "Data: Itiner-e (de Soto et al., 2025) · Pleiades (2025) · DH Lab Seminar 2026",
             ha="center", fontsize=7, color="#888", style="italic")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Centrality bar chart saved: %s", output_path)

