# The Three Connectivity Groups — K-Means Clustering Results
## Roman Road Network Analysis · DH Lab Seminar · Autumn 2026

## How the Groups Were Formed

K-Means clustering (k=3, random_state=42) was applied to two standardised features per city:
- **Degree Centrality** (C_D) — how many direct road connections a city has
- **Betweenness Centrality** (C_B) — how often a city appears on shortest paths between other cities

The `StandardScaler` was applied before fitting to equalise the variance difference (degree σ=0.025 vs betweenness σ=0.108). The algorithm was evaluated for k=2 to k=5; k=3 was selected based on the elbow inflection point (56.8% inertia drop from k=2→k=3) and silhouette score (s=0.5425).

**The cluster labels were assigned post-hoc based on the centroid values** — the algorithm received no historical information.

---

## Group A: Macro-Hub Cities (2 cities — 4.4% of study set)

**Cities:** Roma, Capua

| City | Modern Name | Region | Betweenness C_B | Degree C_D | Direct Links |
|------|-------------|--------|-----------------|------------|--------------|
| Roma | Rome | Regio I | **0.4845** | 0.1364 | 6 |
| Capua | S.M. Capua Vetere | Regio I | **0.4554** | 0.1364 | 6 |

**Cluster Mean BC:** 0.4700 · **Cluster Mean Degree:** 0.1364

### What this group represents:
Cities in this group sit on the highest possible proportion of all shortest paths between Italian cities — nearly half of all 45×44/2 = 990 city-pair paths pass through Roma and Capua. They also have the highest raw degree count (6 direct connections each — maximum in the dataset).

### Historical context:
Roma was the **origin point of all major consular roads** — Via Appia (south), Via Flaminia (north-east), Via Aurelia (coastal north), Via Latina (Campania). Capua was the first major junction city south of Rome on Via Appia and itself the starting point of Via Appia Antica toward Brundisium. The algorithm, using no historical information, correctly identified these two as the supreme network nodes.

---

## Group B: Regional Connectors (24 cities — 53.3% of study set)

**Examples (top 10 by betweenness):**
Pisae (Pisa), Genua (Genoa), Bononia (Bologna), Beneventum (Benevento), Florentia (Florence), Venusia (Venosa), Placentia (Piacenza), Patavium (Padua), Pompeii, Arretium (Arezzo)

**Full list:** Pisae, Genua, Bononia, Beneventum, Florentia, Venusia, Placentia, Patavium, Pompeii, Arretium, Buxentum, Neapolis, Aesernia, Ariminum, Narnia, Verona, Asculum Picenum, Spoletium, Mutina, Tarentum, Mediolanum, Heraclea, Cremona, Perusia

| Statistic | Value |
|-----------|-------|
| Cities in group | 24 |
| Mean Betweenness | 0.1034 |
| Mean Degree | 0.0714 |
| BC range | 0.0085 – 0.3146 |

### What this group represents:
This is the largest group and contains cities that serve as trans-regional connectors. They appear on a meaningful but not dominant share of shortest paths. They form the structural backbone of the network — the cities that allow traffic to flow between the major hubs and peripheral endpoints.

### Historical context:
- **Pisae & Genua** — Ligurian coastal gateway controlling access from Italy to Gaul/Western provinces
- **Bononia (Bologna)** — Po plain central junction, Via Aemilia's key node connecting Adriatic coast to northern Italy
- **Beneventum** — Campanian crossroads connecting Via Appia, Via Traiana, and roads south to Calabria
- **Florentia** — Arno valley connector between Latium and Cisalpine Gaul via the Apennines

---

## Group C: Peripheral & Maritime Termini (19 cities — 42.2% of study set)

**Examples:** Nola, Alba Pompeia, Corfinium, Consentia, Aquileia, Ancona, Augusta Taurinorum (Turin), Ostia, Puteoli, Brundisium, Rhegium, Tergeste, Luceria, Cales

| Statistic | Value |
|-----------|-------|
| Cities in group | 19 |
| Mean Betweenness | 0.0243 |
| Mean Degree | 0.0455 |
| BC range | 0.0000 – 0.1257 |

### What this group represents:
Cities in this group are road-network endpoints or low-connectivity waypoints. Many have only 1–2 direct road connections, meaning they appear on few shortest paths. They are "leaves" or "terminal nodes" in the terrestrial graph.

### The Port City Paradox (key DH limitation):
Five cities in this group had **C_B = 0.0000** (Ostia, Puteoli, Brundisium, Rhegium, Tergeste) — these are major Roman commercial harbours. Their zero betweenness in the terrestrial graph does not reflect their historical importance. Per the ORBIS model (Scheidel et al., 2012), maritime shipping was 10x–60x cheaper than ox-cart overland transport. These cities were highway **termini** that handed freight off to sea routes — to a shortest-path algorithm operating only on land roads, they appear as dead-ends regardless of their commercial significance.

**This is not a flaw in the algorithm; it correctly reflects what the terrestrial road data captures**, and illustrates the methodological limitation explicitly stated in the proposal: *"road connectivity covers only terrestrial mobility — sea and river routes are missing."*

---

## Summary Comparison

| Feature | Group A — Hubs | Group B — Connectors | Group C — Peripheral |
|---------|---------------|---------------------|---------------------|
| Cities | 2 (4.4%) | 24 (53.3%) | 19 (42.2%) |
| Mean BC | 0.4700 | 0.1034 | 0.0243 |
| Mean Degree | 0.1364 | 0.0714 | 0.0455 |
| Road links | 6 each | 2–4 | 1–2 |
| Role | Empire-wide arterial origin | Trans-regional routing | Endpoints & harbours |
| Examples | Roma, Capua | Bononia, Pisae | Ostia, Brundisium |
