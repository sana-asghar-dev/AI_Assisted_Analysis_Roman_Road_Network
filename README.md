# Proposal Deliverables — Roman Road Network Analysis

> **Project:** AI-Assisted Analysis of the Roman Road Network: Identifying and Grouping the Most Connected Cities in Roman Italy  
> **DH Lab Seminar · Programming Projects · Autumn 2026**

---

## What Is This Folder?

This folder contains **only the outputs explicitly required by the project proposal** (Section 6). It is self-contained and independent of the full Flask web dashboard in the parent project.

---

## Contents

### Main Notebook

| File | Description | Proposal Section |
|------|-------------|-----------------|
| [`roman_road_analysis_complete.ipynb`](roman_road_analysis_complete.ipynb) | Complete self-contained Python pipeline — all 5 stages end-to-end | §5 Method, §6 Expected Outputs |

### `/outputs/` — Generated Deliverables

| File | Description | Proposal Section |
|------|-------------|-----------------|
| [`roman_roads_map.png`](outputs/roman_roads_map.png) | Static map — 45 cities sized by betweenness centrality, coloured by K-Means cluster | §6 ¶1 & ¶2 |
| [`top10_cities.csv`](outputs/top10_cities.csv) | Ranked table of top-10 most connected cities | §6 ¶2 |
| [`centrality_chart.png`](outputs/centrality_chart.png) | Bar chart — betweenness centrality by city, grouped by cluster | §6 ¶2 |
| [`cluster_profiles.csv`](outputs/cluster_profiles.csv) | Cluster centroid statistics (mean BC, DC, city count per cluster) | §6 ¶3 |
| [`kmeans_evaluation.csv`](outputs/kmeans_evaluation.csv) | Silhouette scores and inertia for k=2–5 | §5 Method |
| [`clustered_cities.geojson`](outputs/clustered_cities.geojson) | GeoJSON of all 45 cities with centrality scores and cluster assignments | §5 Method |
| [`cluster_groups_description.md`](outputs/cluster_groups_description.md) | Written explanation of the three connectivity groups with examples | §6 ¶3 |
| [`historical_comparison.md`](outputs/historical_comparison.md) | Discussion comparing results to historical expectations | §6 ¶4 |

---

## How to Run the Notebook

### Prerequisites

```bash
# From the roman-road-network/ parent directory
pip install -r requirements.txt

# Additional notebook dependencies (if not in requirements.txt)
pip install jupyter folium
```

### Launch

```bash
cd proposal_deliverables/
jupyter notebook roman_road_analysis_complete.ipynb
```

### Raw Data Required

The notebook uses pre-computed pipeline results from `../data/processed/` by default. For fully end-to-end execution (Stages 2–3 from raw data), place these files in `../data/raw/`:

| File | Source | License |
|------|--------|---------|
| `pleiades-places-latest.csv` | [pleiades.stoa.org/downloads](https://pleiades.stoa.org/downloads) | CC BY 3.0 US |
| `itinere_roads.geojson` | [doi.org/10.1038/s41597-025-06140-z](https://doi.org/10.1038/s41597-025-06140-z) | CC BY 4.0 |

If raw files are absent, the notebook auto-falls back to `../data/processed/` (pre-computed centrality results) — all visualisation stages still run correctly.

---

## Key Results

### Top-5 Most Connected Cities

| Rank | Latin Name | Modern | BC Score | Cluster |
|------|-----------|--------|----------|---------|
| 1 | **Roma** | Rome | 0.4845 | A — Macro-Hub |
| 2 | **Capua** | S. Maria C. Vetere | 0.4554 | A — Macro-Hub |
| 3 | Pisae | Pisa | 0.3146 | B — Connector |
| 4 | Genua | Genoa | 0.2264 | B — Connector |
| 5 | Bononia | Bologna | 0.2242 | B — Connector |

### Three Cluster Groups

| Cluster | Label | Cities | Mean BC |
|---------|-------|--------|---------|
| **A** | Macro-Hub Cities | 2 (4.4%) | 0.4700 |
| **B** | Regional Connectors | 24 (53.3%) | 0.1034 |
| **C** | Peripheral & Maritime Termini | 19 (42.2%) | 0.0243 |

### Graph Diagnostics
- **45 nodes · 62 edges** · density 0.0626 · fully connected
- Diameter: 12 hops · Average shortest path: 4.71 hops / 425.89 km
- K-Means silhouette (k=3): **0.5425**

---

## Technical Stack

| Library | Purpose |
|---------|---------|
| `pandas` / `geopandas` | Data cleaning, spatial handling |
| `networkx` | Graph construction, degree & betweenness centrality (Brandes) |
| `scikit-learn` | StandardScaler + KMeans(k=3, random_state=42, n_init=10) |
| `matplotlib` | Static map (300 DPI), centrality chart, evaluation curves |
| `folium` | Interactive Leaflet.js map with cluster-coloured markers |

---

## Data Licences

- **Pleiades** (pleiades.stoa.org): Creative Commons Attribution 3.0 US. Cite as: Pleiades Project.
- **Itiner-e** (de Soto et al., 2025): Creative Commons Attribution 4.0 International.
  - de Soto, P. et al. (2025). *Itiner-e: A high-resolution dataset of roads of the Roman Empire.* Scientific Data. https://doi.org/10.1038/s41597-025-06140-z

---

## References

- de Soto, P., Pažout, A., Brughmans, T., et al. (2025). Itiner-e: A high-resolution dataset of roads of the Roman Empire. *Scientific Data.* https://doi.org/10.1038/s41597-025-06140-z  
- MacQueen, J. B. (1967). Some methods for classification and analysis of multivariate observations. *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability*, 1, 281–297.  
- Pažout, A., Brughmans, T., de Soto, P., et al. (2026). Road network centrality in the Roman Empire. *(In press)*
