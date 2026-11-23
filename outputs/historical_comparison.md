# Historical Comparison: Computational Results vs. Known Significance
## Roman Road Network Analysis · DH Lab Seminar · Autumn 2026

## Research Question Revisited

> **"What cities were the most connected in the Roman road network of Italy?"**

The computational result (Betweenness Centrality ranking):

| Rank | City (Latin) | Modern Name | BC Score | Cluster |
|------|-------------|-------------|----------|---------|
| **1** | **Roma** | **Rome** | **0.4845** | A — Macro-Hub |
| **2** | **Capua** | S.M. Capua Vetere | **0.4554** | A — Macro-Hub |
| 3 | Pisae | Pisa | 0.3146 | B — Connector |
| 4 | Genua | Genova | 0.2264 | B — Connector |
| 5 | Bononia | Bologna | 0.2242 | B — Connector |
| 6 | Beneventum | Benevento | 0.1856 | B — Connector |
| 7 | Florentia | Florence | 0.1723 | B — Connector |
| 8 | Nola | Nola | 0.1257 | C — Peripheral |
| 9 | Venusia | Venosa | 0.1248 | B — Connector |
| 10 | Placentia | Piacenza | 0.1220 | B — Connector |

---

## Where the Algorithm and History Agree

### 1. Roma as Supreme Network Hub (#1)
**Historical expectation:** Roma was the undisputed centre of the Roman world. All major roads were built radiating outward from Rome, and the phrase *"all roads lead to Rome"* reflects a genuine administrative and logistical reality.

**Computational result:** Roma receives the highest Betweenness Centrality score (0.4845), meaning it lies on the greatest proportion of shortest paths between Italian cities. With 6 direct road connections (the highest degree in the dataset), it is simultaneously the most locally connected and most globally central city.

**Verdict:  Strong agreement.** The algorithm, using no historical labels, independently identifies Roma as the supreme node.

---

### 2. Capua as the Southern Gateway (#2)
**Historical expectation:** Capua was Rome's most important southern ally and later subject city. It was the northern terminus of *Via Appia* and the hub from which roads fanned out to Brundisium (Greece route), Rhegium (Sicily route), and Beneventum (Adriatic route).

**Computational result:** Capua scores 0.4554 betweenness — nearly as high as Roma — with 6 direct connections.

**Verdict:  Strong agreement.** The algorithm independently confirms Capua's structural role as the dominant southern junction.

---

### 3. Pisae & Genua — The Ligurian Gateway (#3 and #4)
**Historical expectation:** These two cities controlled access between the Italian peninsula and Transalpine Gaul (France/Spain). Via Aurelia ran along the Ligurian coast; via Genua, roads climbed to the Alpine passes.

**Computational result:** Despite having only 3 direct connections each (degree rank #10 jointly), both Pisae and Genua score extraordinarily high betweenness: 0.3146 and 0.2264 respectively. This reveals the **Gateway Chokepoint** phenomenon — cities with modest degree but high betweenness, where all north-western traffic must funnel.

**Verdict:  Strong agreement.** The algorithm identifies these as structural bottlenecks — consistent with their position as the only practical road corridor between Italy and Gaul.

---

### 4. Bononia (Bologna) — Po Valley Hub (#5)
**Historical expectation:** Bononia was the starting point of *Via Aemilia* (187 BC), the great military highway cutting across the Po plain. It connected the Adriatic coast to Mediolanum (Milan) and was a key administrative centre for Cisalpine Gaul.

**Computational result:** Betweenness 0.2242, degree 4 connections.

**Verdict:  Agreement.** Bononia's position as the junction point between Via Aemilia, Via Flaminia Minor, and roads to the Adriatic correctly produces high betweenness.

---

## Where the Algorithm and History Diverge

### 5. The Port City Paradox — Ostia, Puteoli, Brundisium (Cluster C, BC = 0.000)

**Historical expectation:**
- **Ostia** — the port of Rome; grain from Egypt, Africa, and Sicily unloaded here
- **Puteoli** (Pozzuoli) — the dominant Campanian harbour, Rome's commercial link to Alexandria
- **Brundisium** (Brindisi) — the only practical embarkation point for Greece and the Eastern Mediterranean

By historical metrics, these were among the most commercially significant cities in Italy.

**Computational result:** All three score **C_B = 0.0000** (rank #33 jointly) and cluster in Group C (Peripheral).

**Explanation:** The terrestrial road network terminates at these harbours. Ships, not ox-carts, carried the bulk of Mediterranean commerce — and sea routes are absent from our graph. Per the ORBIS model (Scheidel et al., 2012), transporting one tonne of cargo by sea was approximately 60x cheaper than overland by cart. Consequently, the Roman road system was designed to *reach* these ports, not *route through* them. To any shortest-path algorithm operating on overland data, they are leaf nodes.

**Verdict:  Algorithmically correct, historically nuanced.** This is not a flaw — it correctly represents what the terrestrial data captures, and validates the proposal's stated limitation.

---

### 6. Mediolanum (Milan) — Lower Than Expected (#27 betweenness rank)

**Historical expectation:** Mediolanum was the administrative capital of the Western Roman Empire from 286 AD onward and a major commercial centre in the Po valley.

**Computational result:** Betweenness 0.038 (rank #27), degree 4 (rank #3), Cluster B.

**Explanation:** Our dataset covers Roman Imperial roads as they existed in the early Empire period. Mediolanum's administrative importance peaked in the late Empire, and its road dominance reflects more the broader Po plain grid (Via Postumia, Via Mediolanum–Genua) than the arterial system of the 1st–2nd century. Additionally, the Po plain's flat, dense road grid distributes betweenness across many parallel routes rather than concentrating it at a single hub.

**Verdict:  Partial divergence** — historically underweighted due to study period focus and dense Po plain routing.

---

## Summary Assessment

| Expectation | Computational Match | Notes |
|------------|---------------------|-------|
| Roma as #1 |  Confirmed | C_B = 0.4845, highest in dataset |
| Capua as major southern hub |  Confirmed | C_B = 0.4554, Cluster A |
| Northern gateways (Pisae, Genua) |  Confirmed | Gateway chokepoint effect |
| Po valley importance (Bononia) |  Confirmed | Via Aemilia junction |
| Port cities as major centres |  Paradox | Zero betweenness — sea routes absent |
| Milan's administrative dominance |  Partial | Late Empire capital; early network underweights it |

**Overall:** The computational results show strong alignment with historical scholarship for terrestrial connectivity. Where divergences occur, they are methodologically interpretable: the data captures overland infrastructure, not maritime or administrative importance. This is consistent with the proposal's framing — *"results will be expressed in terms of patterns within the datasets chosen, not as a precise indicator of the overall importance of each city."*

---

## References
- de Soto, P., et al. (2025). Itiner-e. *Scientific Data*. https://doi.org/10.1038/s41597-025-06140-z
- Pažout, A., et al. (2026). Network science reveals the structure of the Roman road system. *Nature Communications*, 17, 9551.
- Scheidel, W., Meeks, E., & Weiland, J. (2012). ORBIS: The Stanford geospatial network model. Stanford University.
- Pleiades (2025). Data for download. https://pleiades.stoa.org/downloads
