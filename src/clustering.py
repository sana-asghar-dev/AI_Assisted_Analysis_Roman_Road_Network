"""
src/clustering.py
=================
K-Means clustering of Roman cities by network centrality features.

Pipeline:
  1. Build feature matrix X from degree_centrality and betweenness_centrality.
  2. Standardize with StandardScaler (Z-score normalization).
  3. Run KMeans(n_clusters=3, random_state=42, n_init=10).
  4. Evaluate silhouette scores and inertia for k ∈ {2, 3, 4, 5}.
  5. Assign post-hoc analytical cluster labels.
  6. Export cluster assignments and evaluation metrics.

References
----------
- MacQueen (1967). K-means clustering. Proc. Fifth Berkeley Symposium, 1, 281–297.
- scikit-learn: Pedregosa et al. (2011). JMLR, 12, 2825–2830.
- docs/METHODOLOGY.md §5
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)

# Feature columns used for clustering
FEATURE_COLS = ["degree_centrality", "betweenness_centrality"]

# Analytical cluster label descriptions (assigned post-hoc after centroid inspection)
CLUSTER_LABEL_MAP = {
    "A": "High-Connectivity Hub Cities",
    "B": "Intermediate / Regional Connector Cities",
    "C": "Lower-Connectivity / Peripheral Cities",
}


# ---------------------------------------------------------------------------
# 1. Feature matrix preparation
# ---------------------------------------------------------------------------


def prepare_feature_matrix(centrality_df: "pd.DataFrame") -> tuple["pd.DataFrame", list[str]]:
    """
    Extract and validate the feature matrix for K-Means clustering.

    Parameters
    ----------
    centrality_df : pd.DataFrame
        Full centrality results from ``network_analysis.compute_centralities()``.
        Must contain ``degree_centrality`` and ``betweenness_centrality`` columns.

    Returns
    -------
    tuple[pd.DataFrame, list[str]]
        (feature_df, feature_cols) — DataFrame with only the feature columns,
        indexed identically to centrality_df.
    """
    missing = [c for c in FEATURE_COLS if c not in centrality_df.columns]
    if missing:
        raise ValueError(
            f"Feature columns missing from centrality_df: {missing}. "
            f"Available: {list(centrality_df.columns)}"
        )

    feature_df = centrality_df[FEATURE_COLS].copy()
    null_counts = feature_df.isnull().sum()
    if null_counts.any():
        raise ValueError(
            f"Null values in feature matrix: {null_counts[null_counts > 0].to_dict()}. "
            "Cannot cluster with missing centrality values."
        )

    logger.info(
        "Feature matrix: %d cities × %d features %s.",
        len(feature_df), len(FEATURE_COLS), FEATURE_COLS,
    )
    return feature_df, FEATURE_COLS


# ---------------------------------------------------------------------------
# 2. Standardization
# ---------------------------------------------------------------------------


def standardize_features(feature_df: "pd.DataFrame") -> tuple:
    """
    Standardize feature matrix using Z-score normalization (StandardScaler).

    Ensures degree_centrality and betweenness_centrality contribute equally
    to the K-Means Euclidean distance metric regardless of their scales.

    Parameters
    ----------
    feature_df : pd.DataFrame
        Feature matrix from ``prepare_feature_matrix()``.

    Returns
    -------
    tuple[np.ndarray, StandardScaler]
        (X_scaled, scaler) — scaled feature array and fitted scaler.
        X_scaled shape: (n_cities, n_features).
    """
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(feature_df.values)

    logger.info(
        "Features standardized: means=%s, stds=%s",
        [round(m, 4) for m in scaler.mean_.tolist()],
        [round(s, 4) for s in scaler.scale_.tolist()],
    )
    return X_scaled, scaler


# ---------------------------------------------------------------------------
# 3. K-Means (primary: k=3)
# ---------------------------------------------------------------------------


def run_kmeans(
    X_scaled,
    n_clusters: int = 3,
    random_state: int = 42,
    n_init: int = 10,
) -> tuple:
    """
    Run K-Means clustering and return model + cluster labels.

    Parameters
    ----------
    X_scaled : np.ndarray
        Standardized feature matrix (n_cities × n_features).
    n_clusters : int
        Number of clusters. Default: 3 (seminar primary grouping).
    random_state : int
        Random seed for reproducibility. Default: 42.
    n_init : int
        Number of K-Means initialisations. Default: 10.

    Returns
    -------
    tuple[KMeans, np.ndarray, float]
        (kmeans_model, cluster_labels, inertia)
    """
    from sklearn.cluster import KMeans

    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=n_init,
    )
    labels = kmeans.fit_predict(X_scaled)
    inertia = kmeans.inertia_

    logger.info(
        "KMeans(k=%d, random_state=%d, n_init=%d): inertia=%.4f.",
        n_clusters, random_state, n_init, inertia,
    )
    return kmeans, labels, inertia


# ---------------------------------------------------------------------------
# 4. Silhouette / elbow evaluation across k values
# ---------------------------------------------------------------------------


def evaluate_clustering(X_scaled, k_range=range(2, 6), random_state: int = 42) -> "pd.DataFrame":
    """
    Evaluate K-Means quality across multiple values of k.

    Computes inertia and Silhouette Score for each k in k_range.
    The primary k=3 result is flagged as the seminar selection.

    Parameters
    ----------
    X_scaled : np.ndarray
        Standardized feature matrix.
    k_range : range
        Values of k to test. Default: range(2, 6) → k ∈ {2, 3, 4, 5}.
    random_state : int
        Random seed.

    Returns
    -------
    pd.DataFrame
        Columns: k, inertia, silhouette_score, is_primary_selection.
    """
    import pandas as pd
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    rows = []
    logger.info("Evaluating K-Means for k ∈ %s...", list(k_range))

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertia = km.inertia_

        try:
            sil = silhouette_score(X_scaled, labels)
        except Exception as e:
            sil = float("nan")
            logger.warning("Silhouette score failed for k=%d: %s", k, e)

        rows.append(
            {
                "k": k,
                "inertia": round(inertia, 4),
                "silhouette_score": round(float(sil), 4) if sil == sil else None,
                "is_primary_selection": k == 3,
            }
        )
        logger.info("  k=%d: inertia=%.4f, silhouette=%.4f", k, inertia, sil if sil == sil else -999)

    eval_df = pd.DataFrame(rows)
    return eval_df


# ---------------------------------------------------------------------------
# 5. Post-hoc cluster labeling
# ---------------------------------------------------------------------------


def assign_cluster_labels(
    centrality_df: "pd.DataFrame",
    cluster_labels,
    kmeans_model,
    X_scaled,
) -> "pd.DataFrame":
    """
    Assign analytical labels (A/B/C) to K-Means cluster IDs based on centroid inspection.

    The cluster with the highest mean betweenness centroid → Label A (Hub).
    The cluster with the lowest mean betweenness centroid → Label C (Peripheral).
    The remaining → Label B (Intermediate).

    Labels are assigned post-hoc by inspecting centroids — not predetermined.

    Parameters
    ----------
    centrality_df : pd.DataFrame
        Full centrality results (45 rows).
    cluster_labels : np.ndarray
        Cluster assignments (0-indexed) from KMeans.fit_predict().
    kmeans_model : KMeans
        Fitted KMeans model (for centroid access).
    X_scaled : np.ndarray
        Standardized feature matrix used for clustering.

    Returns
    -------
    pd.DataFrame
        centrality_df with added columns:
        - cluster_id (int 0–2)
        - cluster_label ('A', 'B', or 'C')
        - cluster_description (str)
    """
    import numpy as np
    import pandas as pd

    df = centrality_df.copy()
    df["cluster_id"] = cluster_labels.astype(int)

    # Inspect centroids in scaled space (betweenness is column index 1)
    centroids = kmeans_model.cluster_centers_
    betweenness_centroid_col = 1  # index in FEATURE_COLS: [degree_centrality, betweenness_centrality]

    centroid_betweenness = {
        cluster_id: centroids[cluster_id][betweenness_centroid_col]
        for cluster_id in range(len(centroids))
    }
    sorted_clusters = sorted(centroid_betweenness.keys(), key=lambda c: centroid_betweenness[c])
    # sorted_clusters[0] = lowest betweenness → Label C (Peripheral)
    # sorted_clusters[-1] = highest betweenness → Label A (Hub)
    # sorted_clusters[1] = middle → Label B (Intermediate)

    label_map = {
        sorted_clusters[-1]: "A",  # Highest betweenness → Hub
        sorted_clusters[0]: "C",   # Lowest betweenness → Peripheral
        sorted_clusters[1]: "B",   # Middle → Intermediate
    }

    df["cluster_label"] = df["cluster_id"].map(label_map)
    df["cluster_description"] = df["cluster_label"].map(CLUSTER_LABEL_MAP)

    logger.info("Post-hoc cluster assignment:")
    for cid in sorted(label_map.keys()):
        label = label_map[cid]
        count = (df["cluster_id"] == cid).sum()
        centroid_val = centroid_betweenness[cid]
        logger.info(
            "  Cluster %d → Label %s (%s): %d cities, betweenness centroid=%.4f",
            cid, label, CLUSTER_LABEL_MAP[label], count, centroid_val,
        )

    return df


# ---------------------------------------------------------------------------
# 6. Cluster profile summary
# ---------------------------------------------------------------------------


def compute_cluster_profiles(clustered_df: "pd.DataFrame") -> "pd.DataFrame":
    """
    Compute summary statistics for each K-Means cluster.

    Parameters
    ----------
    clustered_df : pd.DataFrame
        Output of ``assign_cluster_labels()``.

    Returns
    -------
    pd.DataFrame
        One row per cluster with mean/median centrality values and city count.
    """
    import pandas as pd

    profiles = (
        clustered_df.groupby(["cluster_label", "cluster_description"])
        .agg(
            n_cities=("latin_name", "count"),
            mean_degree=("degree_centrality", "mean"),
            median_degree=("degree_centrality", "median"),
            mean_betweenness=("betweenness_centrality", "mean"),
            median_betweenness=("betweenness_centrality", "median"),
            mean_betweenness_weighted=("betweenness_centrality_weighted", "mean"),
            cities=("latin_name", lambda x: "; ".join(sorted(x))),
        )
        .round(6)
        .reset_index()
    )
    profiles = profiles.sort_values("cluster_label")

    logger.info("Cluster profiles:")
    for _, row in profiles.iterrows():
        logger.info(
            "  [%s] %s: %d cities, mean_betweenness=%.4f",
            row["cluster_label"], row["cluster_description"],
            row["n_cities"], row["mean_betweenness"],
        )
    return profiles


# ---------------------------------------------------------------------------
# 7. Run full clustering pipeline
# ---------------------------------------------------------------------------


def run_clustering_pipeline(
    centrality_df: "pd.DataFrame",
    n_clusters: int = 3,
    random_state: int = 42,
) -> dict:
    """
    Execute the complete clustering pipeline and return all results.

    Steps:
      1. Prepare feature matrix.
      2. Standardize features.
      3. Run K-Means (k=3).
      4. Evaluate k ∈ {2, 3, 4, 5}.
      5. Assign post-hoc cluster labels.
      6. Compute cluster profiles.

    Parameters
    ----------
    centrality_df : pd.DataFrame
        Full centrality results from ``network_analysis.compute_centralities()``.
    n_clusters : int
        Primary number of clusters. Default: 3.
    random_state : int
        Reproducibility seed. Default: 42.

    Returns
    -------
    dict with keys:
        - 'clustered_df'     : pd.DataFrame — centrality_df + cluster columns
        - 'cluster_profiles' : pd.DataFrame — cluster summary statistics
        - 'eval_df'          : pd.DataFrame — k vs. inertia/silhouette evaluation
        - 'kmeans_model'     : KMeans — fitted model
        - 'scaler'           : StandardScaler — fitted scaler
        - 'X_scaled'         : np.ndarray — standardized feature matrix
        - 'inertia'          : float — primary model inertia
        - 'silhouette_score' : float — silhouette score for k=3
    """
    from sklearn.metrics import silhouette_score as sk_silhouette

    # 1. Feature matrix
    feature_df, feature_cols = prepare_feature_matrix(centrality_df)

    # 2. Standardize
    X_scaled, scaler = standardize_features(feature_df)

    # 3. Run primary K-Means
    kmeans, labels, inertia = run_kmeans(X_scaled, n_clusters=n_clusters, random_state=random_state)

    # 4. Silhouette score for primary k
    try:
        sil = round(float(sk_silhouette(X_scaled, labels)), 4)
    except Exception:
        sil = None
    logger.info("Primary model (k=%d): inertia=%.4f, silhouette=%.4f", n_clusters, inertia, sil or -1)

    # 5. Evaluate across k range
    from src.config import N_CLUSTERS_RANGE
    eval_df = evaluate_clustering(X_scaled, k_range=N_CLUSTERS_RANGE, random_state=random_state)

    # 6. Assign labels
    clustered_df = assign_cluster_labels(centrality_df, labels, kmeans, X_scaled)

    # 7. Cluster profiles
    cluster_profiles = compute_cluster_profiles(clustered_df)

    return {
        "clustered_df": clustered_df,
        "cluster_profiles": cluster_profiles,
        "eval_df": eval_df,
        "kmeans_model": kmeans,
        "scaler": scaler,
        "X_scaled": X_scaled,
        "inertia": inertia,
        "silhouette_score": sil,
    }


def export_clustering_results(results: dict, exports_dir, processed_dir) -> None:
    """
    Export all clustering outputs to CSV files.

    Writes:
      - ``data/processed/clustered_cities.csv`` — full results with cluster assignments.
      - ``data/exports/cluster_profiles.csv`` — summary stats per cluster.
      - ``data/exports/kmeans_evaluation.csv`` — k vs. silhouette/inertia.
      - ``data/exports/clustered_cities.geojson`` — GeoJSON for Flask map.
    """
    import json

    clustered_df = results["clustered_df"]
    cluster_profiles = results["cluster_profiles"]
    eval_df = results["eval_df"]

    # Full results
    clustered_csv = processed_dir / "clustered_cities.csv"
    clustered_df.to_csv(clustered_csv, index=False)
    logger.info("Clustered cities CSV saved: %s", clustered_csv)

    # Cluster profiles
    profiles_csv = exports_dir / "cluster_profiles.csv"
    cluster_profiles.to_csv(profiles_csv, index=False)
    logger.info("Cluster profiles saved: %s", profiles_csv)

    # Evaluation table
    eval_csv = exports_dir / "kmeans_evaluation.csv"
    eval_df.to_csv(eval_csv, index=False)
    logger.info("K-Means evaluation table saved: %s", eval_csv)

    # GeoJSON for Flask
    _export_cities_geojson(clustered_df, exports_dir / "clustered_cities.geojson")


def _export_cities_geojson(df: "pd.DataFrame", path) -> None:
    """Export the clustered cities DataFrame as a GeoJSON FeatureCollection."""
    import json

    features = []
    for _, row in df.iterrows():
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["lon"]), float(row["lat"])],
            },
            "properties": {
                k: (None if (isinstance(v, float) and v != v) else v)
                for k, v in row.items()
                if k not in ("lon", "lat")
            },
        }
        features.append(feature)

    geojson = {"type": "FeatureCollection", "features": features}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    logger.info("Clustered cities GeoJSON saved: %s (%d features)", path, len(features))

