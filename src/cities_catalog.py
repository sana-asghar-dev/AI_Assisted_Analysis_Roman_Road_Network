"""
src/cities_catalog.py
=====================
Historically defensible catalog of 45 major Roman cities in Italy.

Selection Criteria
------------------
Cities were selected to represent:
  1. Major administrative and colonial centres across all Augustan regions (I–XI).
  2. Key road junctions and way-stations on the principal Roman highways
     (Via Appia, Via Flaminia, Via Aemilia, Via Postumia, Via Aurelia, etc.).
  3. Strategic ports and military bases relevant to Italian connectivity.
  4. Geographic coverage: from Cisalpine Gaul (Po Valley) south through
     Latium, Campania, Apulia, Lucania, and Bruttium.

Primary Reference for Pleiades IDs
------------------------------------
Pleiades Gazetteer of Ancient Places: https://pleiades.stoa.org/
Data snapshot: Pleiades (2025). Data for download. https://pleiades.stoa.org/downloads

Coordinate Sources
-------------------
Coordinates are the canonical representative point from the Pleiades record
(WGS84, EPSG:4326), cross-checked against modern archaeological site literature.
Where Pleiades provides a bounding polygon, the centroid representative point
is used. All coordinates are recorded to 4 decimal places (≈11m precision).

Historical References
---------------------
  - Pažout, A. et al. (2026). Network science reveals the structure and lasting
    impact of the Roman road system. Nature Communications, 17, 9551.
  - Cornell, T. J. & Matthews, J. (1982). Atlas of the Roman World. Phaidon.
  - Talbert, R. J. A. (ed.) (2000). Barrington Atlas of the Greek and Roman World.
    Princeton University Press.

Data Structure
--------------
Each city is a dict with:
  - pleiades_id   : int     — canonical Pleiades numeric ID
  - latin_name    : str     — standard Latin toponym
  - modern_name   : str     — modern Italian place name or closest equivalent
  - region        : str     — Augustan administrative region (Regio I–XI)
  - region_label  : str     — human-readable region description
  - lon           : float   — WGS84 longitude (EPSG:4326)
  - lat           : float   — WGS84 latitude  (EPSG:4326)
  - notes         : str     — brief historical/selection note
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical 45-city catalog
# ---------------------------------------------------------------------------
# fmt: off
CITIES: list[dict[str, Any]] = [
    # ── Regio I  — Latium et Campania ──────────────────────────────────────
    {
        "pleiades_id": 423025,
        "latin_name": "Roma",
        "modern_name": "Roma (Rome)",
        "region": "Regio I",
        "region_label": "Latium et Campania",
        "lon": 12.4869,
        "lat": 41.8905,
        "notes": (
            "Capital of the Roman Empire; supreme hub of all Italian road "
            "networks. Origin point of the Milliarium Aureum (Golden Milestone)."
        ),
    },
    {
        "pleiades_id": 422995,
        "latin_name": "Ostia",
        "modern_name": "Ostia Antica",
        "region": "Regio I",
        "region_label": "Latium et Campania",
        "lon": 12.2898,
        "lat": 41.7568,
        "notes": (
            "Principal harbour of Rome at the Tiber mouth; key node for "
            "maritime-to-terrestrial traffic transfer. Via Ostiensis terminus."
        ),
    },
    {
        "pleiades_id": 432754,
        "latin_name": "Capua",
        "modern_name": "Santa Maria Capua Vetere",
        "region": "Regio I",
        "region_label": "Latium et Campania",
        "lon": 14.2569,
        "lat": 41.0853,
        "notes": (
            "Most important city of Campania; major junction on the Via Appia "
            "and Via Latina; key military and commercial hub."
        ),
    },
    {
        "pleiades_id": 432744,
        "latin_name": "Neapolis",
        "modern_name": "Napoli (Naples)",
        "region": "Regio I",
        "region_label": "Latium et Campania",
        "lon": 14.2549,
        "lat": 40.8400,
        "notes": (
            "Largest Greek-founded city in Campania; important cultural and "
            "commercial centre. Connected to Capua and Puteoli by road."
        ),
    },
    {
        "pleiades_id": 432975,
        "latin_name": "Puteoli",
        "modern_name": "Pozzuoli",
        "region": "Regio I",
        "region_label": "Latium et Campania",
        "lon": 14.1274,
        "lat": 40.8261,
        "notes": (
            "Major port on the Bay of Naples; chief harbour for eastern "
            "Mediterranean trade until Ostia expanded under Claudius."
        ),
    },
    {
        "pleiades_id": 432808,
        "latin_name": "Herculaneum",
        "modern_name": "Ercolano",
        "region": "Regio I",
        "region_label": "Latium et Campania",
        "lon": 14.3483,
        "lat": 40.8060,
        "notes": (
            "Prosperous Campanian coastal town; destroyed 79 CE (Vesuvius). "
            "Included as representative Campanian road-network node."
        ),
    },
    {
        "pleiades_id": 432860,
        "latin_name": "Nola",
        "modern_name": "Nola",
        "region": "Regio I",
        "region_label": "Latium et Campania",
        "lon": 14.5296,
        "lat": 40.9267,
        "notes": (
            "Ancient Oscan and Roman colony; important road junction east of "
            "Neapolis linking Campania to Apulia."
        ),
    },
    {
        "pleiades_id": 432949,
        "latin_name": "Pompeii",
        "modern_name": "Pompei",
        "region": "Regio I",
        "region_label": "Latium et Campania",
        "lon": 14.4877,
        "lat": 40.7509,
        "notes": (
            "Prosperous Roman town destroyed 79 CE; well-documented road "
            "connections along the Campanian coastal route."
        ),
    },
    # ── Regio II — Apulia et Calabria ───────────────────────────────────────
    {
        "pleiades_id": 442582,
        "latin_name": "Brundisium",
        "modern_name": "Brindisi",
        "region": "Regio II",
        "region_label": "Apulia et Calabria",
        "lon": 17.9457,
        "lat": 40.6328,
        "notes": (
            "Terminus of the Via Appia and Via Traiana; primary embarkation "
            "point for Greece and the Eastern Mediterranean. Key strategic port."
        ),
    },
    {
        "pleiades_id": 442648,
        "latin_name": "Tarentum",
        "modern_name": "Taranto",
        "region": "Regio II",
        "region_label": "Apulia et Calabria",
        "lon": 17.2291,
        "lat": 40.4761,
        "notes": (
            "Major Greek colony turned Roman municipium; important harbour on "
            "the Gulf of Taranto. Junction of routes through southern Italy."
        ),
    },
    {
        "pleiades_id": 442668,
        "latin_name": "Venusia",
        "modern_name": "Venosa",
        "region": "Regio II",
        "region_label": "Apulia et Calabria",
        "lon": 15.8143,
        "lat": 40.9633,
        "notes": (
            "Latin colony on Via Appia; strategic crossroads between Apulia "
            "and Lucania. Birthplace of Horace."
        ),
    },
    {
        "pleiades_id": 442625,
        "latin_name": "Luceria",
        "modern_name": "Lucera",
        "region": "Regio II",
        "region_label": "Apulia et Calabria",
        "lon": 15.3377,
        "lat": 41.5063,
        "notes": (
            "Important Latin colony in northern Apulia; road junction on "
            "routes through the Apennine passes toward the Adriatic."
        ),
    },
    # ── Regio III — Lucania et Bruttii ─────────────────────────────────────
    {
        "pleiades_id": 452310,
        "latin_name": "Rhegium",
        "modern_name": "Reggio Calabria",
        "region": "Regio III",
        "region_label": "Lucania et Bruttii",
        "lon": 15.6440,
        "lat": 38.1106,
        "notes": (
            "Greek colony at the tip of Italy; southern terminus of the Via "
            "Popilia; embarkation point for Sicily. Extreme southern road endpoint."
        ),
    },
    {
        "pleiades_id": 452288,
        "latin_name": "Consentia",
        "modern_name": "Cosenza",
        "region": "Regio III",
        "region_label": "Lucania et Bruttii",
        "lon": 16.2595,
        "lat": 39.2981,
        "notes": (
            "Chief Bruttian city; important road junction on the Via Popilia "
            "through the toe of Italy toward Rhegium."
        ),
    },
    {
        "pleiades_id": 442611,
        "latin_name": "Heraclea",
        "modern_name": "Policoro",
        "region": "Regio III",
        "region_label": "Lucania et Bruttii",
        "lon": 16.6739,
        "lat": 40.2053,
        "notes": (
            "Greek and Lucanian city on the Ionian coast; junction linking "
            "coastal Lucanian route with interior roads."
        ),
    },
    # ── Regio IV — Samnium ──────────────────────────────────────────────────
    {
        "pleiades_id": 432721,
        "latin_name": "Beneventum",
        "modern_name": "Benevento",
        "region": "Regio IV",
        "region_label": "Samnium",
        "lon": 14.7824,
        "lat": 41.1297,
        "notes": (
            "Critical road junction: meeting point of Via Appia, Via Traiana, "
            "and Via Latina. Major Samnite and Roman colony."
        ),
    },
    {
        "pleiades_id": 413122,
        "latin_name": "Aesernia",
        "modern_name": "Isernia",
        "region": "Regio IV",
        "region_label": "Samnium",
        "lon": 14.2340,
        "lat": 41.5943,
        "notes": (
            "Latin colony in Samnium; important strategic garrison point "
            "controlling interior Apennine routes."
        ),
    },
    # ── Regio V — Picenum ───────────────────────────────────────────────────
    {
        "pleiades_id": 413011,
        "latin_name": "Ancona",
        "modern_name": "Ancona",
        "region": "Regio V",
        "region_label": "Picenum",
        "lon": 13.5177,
        "lat": 43.6206,
        "notes": (
            "Major Adriatic port; northern terminus of the Via Flaminia. "
            "Junction linking Adriatic coastal traffic to interior."
        ),
    },
    {
        "pleiades_id": 413036,
        "latin_name": "Asculum Picenum",
        "modern_name": "Ascoli Piceno",
        "region": "Regio V",
        "region_label": "Picenum",
        "lon": 13.5791,
        "lat": 42.8535,
        "notes": (
            "Principal city of Picenum; road junction on routes connecting "
            "the Adriatic coast to the Apennine interior."
        ),
    },
    # ── Regio VI — Umbria ───────────────────────────────────────────────────
    {
        "pleiades_id": 413389,
        "latin_name": "Spoletium",
        "modern_name": "Spoleto",
        "region": "Regio VI",
        "region_label": "Umbria",
        "lon": 12.7376,
        "lat": 42.7342,
        "notes": (
            "Key colony on the Via Flaminia between Rome and Ariminum. "
            "Important military road junction controlling the Apennine pass."
        ),
    },
    {
        "pleiades_id": 413288,
        "latin_name": "Narnia",
        "modern_name": "Narni",
        "region": "Regio VI",
        "region_label": "Umbria",
        "lon": 12.5217,
        "lat": 42.5177,
        "notes": (
            "Latin colony on the Via Flaminia immediately north of Rome; "
            "first major stop on the road north."
        ),
    },
    {
        "pleiades_id": 413222,
        "latin_name": "Iguvium",
        "modern_name": "Gubbio",
        "region": "Regio VI",
        "region_label": "Umbria",
        "lon": 12.5751,
        "lat": 43.3508,
        "notes": (
            "Important Umbrian city; road junction connecting the Via Flaminia "
            "to secondary routes through northern Umbria."
        ),
    },
    # ── Regio VII — Etruria ─────────────────────────────────────────────────
    {
        "pleiades_id": 413179,
        "latin_name": "Florentia",
        "modern_name": "Firenze (Florence)",
        "region": "Regio VII",
        "region_label": "Etruria",
        "lon": 11.2558,
        "lat": 43.7696,
        "notes": (
            "Roman colony at a key Arno river crossing; road junction "
            "connecting Via Cassia and Via Flaminia corridors."
        ),
    },
    {
        "pleiades_id": 413215,
        "latin_name": "Arretium",
        "modern_name": "Arezzo",
        "region": "Regio VII",
        "region_label": "Etruria",
        "lon": 11.8825,
        "lat": 43.4636,
        "notes": (
            "Major Etruscan and Roman city; junction on the Via Cassia with "
            "roads east to Umbrrian towns. Important ceramic production centre."
        ),
    },
    {
        "pleiades_id": 413294,
        "latin_name": "Perusia",
        "modern_name": "Perugia",
        "region": "Regio VII",
        "region_label": "Etruria",
        "lon": 12.3883,
        "lat": 43.1122,
        "notes": (
            "Major Etruscan city and Roman municipium; road junction linking "
            "Etruria to Umbria across the Tiber valley."
        ),
    },
    {
        "pleiades_id": 413305,
        "latin_name": "Pisae",
        "modern_name": "Pisa",
        "region": "Regio VII",
        "region_label": "Etruria",
        "lon": 10.3952,
        "lat": 43.7157,
        "notes": (
            "Coastal Etruscan and Roman city; important harbour at the Arno "
            "mouth on the Via Aurelia corridor."
        ),
    },
    # ── Regio VIII — Aemilia ────────────────────────────────────────────────
    {
        "pleiades_id": 109281,
        "latin_name": "Bononia",
        "modern_name": "Bologna",
        "region": "Regio VIII",
        "region_label": "Aemilia",
        "lon": 11.3426,
        "lat": 44.4938,
        "notes": (
            "Major junction on the Via Aemilia; principal road city of "
            "Cisalpine Gaul crossing the Apennines toward Etruria."
        ),
    },
    {
        "pleiades_id": 109399,
        "latin_name": "Mutina",
        "modern_name": "Modena",
        "region": "Regio VIII",
        "region_label": "Aemilia",
        "lon": 10.9255,
        "lat": 44.6462,
        "notes": (
            "Latin colony on the Via Aemilia; key road centre in the Po "
            "plain between Bononia and Placentia."
        ),
    },
    {
        "pleiades_id": 109427,
        "latin_name": "Parma",
        "modern_name": "Parma",
        "region": "Regio VIII",
        "region_label": "Aemilia",
        "lon": 10.3267,
        "lat": 44.8015,
        "notes": (
            "Latin colony on the Via Aemilia; important road and commercial "
            "node in the Po plain."
        ),
    },
    {
        "pleiades_id": 109448,
        "latin_name": "Placentia",
        "modern_name": "Piacenza",
        "region": "Regio VIII",
        "region_label": "Aemilia",
        "lon": 9.6938,
        "lat": 45.0527,
        "notes": (
            "Latin colony at the terminus of the Via Aemilia on the Po; "
            "major junction connecting to Mediolanum, Genua, and Cremona."
        ),
    },
    {
        "pleiades_id": 109373,
        "latin_name": "Ariminum",
        "modern_name": "Rimini",
        "region": "Regio VIII",
        "region_label": "Aemilia",
        "lon": 12.5674,
        "lat": 44.0598,
        "notes": (
            "Latin colony at the junction of Via Flaminia (from Rome) and "
            "Via Aemilia (north-west); strategic road node on the Adriatic."
        ),
    },
    # ── Regio IX — Liguria ──────────────────────────────────────────────────
    {
        "pleiades_id": 157812,
        "latin_name": "Genua",
        "modern_name": "Genova (Genoa)",
        "region": "Regio IX",
        "region_label": "Liguria",
        "lon": 8.9463,
        "lat": 44.4073,
        "notes": (
            "Major Ligurian port; junction of coastal Via Aurelia and "
            "interior routes over the Apennines toward Placentia (Via Postumia)."
        ),
    },
    {
        "pleiades_id": 157983,
        "latin_name": "Alba Pompeia",
        "modern_name": "Alba",
        "region": "Regio IX",
        "region_label": "Liguria",
        "lon": 8.0361,
        "lat": 44.6985,
        "notes": (
            "Ligurian Roman colony; road junction in the Tanaro valley "
            "connecting the Po plain with Alpine routes."
        ),
    },
    # ── Regio X — Venetia et Histria ────────────────────────────────────────
    {
        "pleiades_id": 187290,
        "latin_name": "Aquileia",
        "modern_name": "Aquileia",
        "region": "Regio X",
        "region_label": "Venetia et Histria",
        "lon": 13.3694,
        "lat": 45.7695,
        "notes": (
            "Critical northeastern gateway of Italy; major road hub connecting "
            "Italy to the Balkans, Danube frontier, and the Amber Road."
        ),
    },
    {
        "pleiades_id": 187543,
        "latin_name": "Verona",
        "modern_name": "Verona",
        "region": "Regio X",
        "region_label": "Venetia et Histria",
        "lon": 10.9930,
        "lat": 45.4386,
        "notes": (
            "Major road junction on the Adige; connecting Via Postumia "
            "with routes north through the Brenner Pass toward Raetia."
        ),
    },
    {
        "pleiades_id": 187432,
        "latin_name": "Patavium",
        "modern_name": "Padova (Padua)",
        "region": "Regio X",
        "region_label": "Venetia et Histria",
        "lon": 11.8768,
        "lat": 45.4064,
        "notes": (
            "Wealthy Venetian city on the Via Postumia; one of the most "
            "prosperous cities in Roman Italy."
        ),
    },
    {
        "pleiades_id": 187488,
        "latin_name": "Tergeste",
        "modern_name": "Trieste",
        "region": "Regio X",
        "region_label": "Venetia et Histria",
        "lon": 13.7766,
        "lat": 45.6495,
        "notes": (
            "Important Adriatic port and road junction near Aquileia; "
            "gateway to Histria and the Dalmatian coast."
        ),
    },
    {
        "pleiades_id": 187342,
        "latin_name": "Cremona",
        "modern_name": "Cremona",
        "region": "Regio X",
        "region_label": "Venetia et Histria",
        "lon": 10.0229,
        "lat": 45.1325,
        "notes": (
            "Latin colony on the Po; road junction on Via Postumia "
            "linking Genua to Aquileia through the Po plain."
        ),
    },
    # ── Regio XI — Transpadana ──────────────────────────────────────────────
    {
        "pleiades_id": 138398,
        "latin_name": "Mediolanum",
        "modern_name": "Milano (Milan)",
        "region": "Regio XI",
        "region_label": "Transpadana",
        "lon": 9.1895,
        "lat": 45.4642,
        "notes": (
            "Capital of Transpadana; supreme road hub of northern Italy "
            "connecting routes to all Alpine passes and major Po plain cities. "
            "Later imperial capital of the West."
        ),
    },
    {
        "pleiades_id": 138439,
        "latin_name": "Augusta Taurinorum",
        "modern_name": "Torino (Turin)",
        "region": "Regio XI",
        "region_label": "Transpadana",
        "lon": 7.6869,
        "lat": 45.0703,
        "notes": (
            "Roman colony at the foot of the Alps; road junction controlling "
            "Mont Cenis and Little St. Bernard passes into Gaul."
        ),
    },
    {
        "pleiades_id": 138463,
        "latin_name": "Ticinum",
        "modern_name": "Pavia",
        "region": "Regio XI",
        "region_label": "Transpadana",
        "lon": 9.1580,
        "lat": 45.1847,
        "notes": (
            "Road junction on the Ticino river; connecting Mediolanum with "
            "Placentia and routes south across the Apennines."
        ),
    },
    {
        "pleiades_id": 138514,
        "latin_name": "Novaria",
        "modern_name": "Novara",
        "region": "Regio XI",
        "region_label": "Transpadana",
        "lon": 8.6196,
        "lat": 45.4463,
        "notes": (
            "Road junction between Mediolanum and Augusta Taurinorum; "
            "controlling western Transpadana."
        ),
    },
    # ── Additional key cities for coverage ──────────────────────────────────
    {
        "pleiades_id": 413063,
        "latin_name": "Corfinium",
        "modern_name": "Corfinio",
        "region": "Regio IV",
        "region_label": "Samnium",
        "lon": 13.8414,
        "lat": 42.1216,
        "notes": (
            "Capital of the Italian allies during the Social War (91–87 BCE); "
            "interior road junction in the central Apennines. Pleiades ID: 413063."
        ),
    },
    {
        "pleiades_id": 413148,
        "latin_name": "Cales",
        "modern_name": "Calvi Risorta",
        "region": "Regio I",
        "region_label": "Latium et Campania",
        "lon": 14.0677,
        "lat": 41.2014,
        "notes": (
            "Important Latin colony on the Via Latina corridor between "
            "Rome and Capua; wine-producing region."
        ),
    },
    {
        "pleiades_id": 413066,
        "latin_name": "Buxentum",
        "modern_name": "Policastro Bussentino",
        "region": "Regio III",
        "region_label": "Lucania et Bruttii",
        "lon": 15.4874,
        "lat": 40.0456,
        "notes": (
            "Latin colony on the Tyrrhenian coast of Lucania; road node "
            "on the coastal route between Campania and Bruttium."
        ),
    },
]
# fmt: on

# ---------------------------------------------------------------------------
# Validate and deduplicate at module load
# ---------------------------------------------------------------------------

# Remove duplicate pleiades_id entries (keep first occurrence)
_seen_ids: set[int] = set()
_unique_cities: list[dict[str, Any]] = []
for _city in CITIES:
    if _city["pleiades_id"] not in _seen_ids:
        _seen_ids.add(_city["pleiades_id"])
        _unique_cities.append(_city)
    else:
        logger.warning(
            "Duplicate pleiades_id %d for '%s' — skipping.",
            _city["pleiades_id"],
            _city["latin_name"],
        )

CITIES = _unique_cities

REQUIRED_FIELDS = {
    "pleiades_id",
    "latin_name",
    "modern_name",
    "region",
    "region_label",
    "lon",
    "lat",
    "notes",
}

# ---------------------------------------------------------------------------
# Public helper functions
# ---------------------------------------------------------------------------


def validate_catalog() -> list[str]:
    """
    Validate every city record in CITIES.

    Returns
    -------
    list[str]
        List of validation error messages. Empty list means all records pass.
    """
    errors: list[str] = []

    for i, city in enumerate(CITIES):
        name = city.get("latin_name", f"<index {i}>")
        missing = REQUIRED_FIELDS - city.keys()
        if missing:
            errors.append(f"{name}: missing fields {missing}")
            continue

        if not isinstance(city["pleiades_id"], int) or city["pleiades_id"] <= 0:
            errors.append(f"{name}: pleiades_id must be a positive integer")

        lon = city.get("lon")
        lat = city.get("lat")
        if lon is None or lat is None:
            errors.append(f"{name}: missing coordinates")
        else:
            if not (-180.0 <= lon <= 180.0):
                errors.append(f"{name}: lon={lon} out of valid WGS84 range")
            if not (-90.0 <= lat <= 90.0):
                errors.append(f"{name}: lat={lat} out of valid WGS84 range")
            # Italy bounding check (generous bounds including Cisalpine Gaul)
            if not (6.5 <= lon <= 18.6):
                errors.append(f"{name}: lon={lon} outside Italy bounds [6.5, 18.6]")
            if not (36.5 <= lat <= 47.5):
                errors.append(f"{name}: lat={lat} outside Italy bounds [36.5, 47.5]")

        for field in ("latin_name", "modern_name", "region", "region_label", "notes"):
            if not isinstance(city.get(field), str) or not city[field].strip():
                errors.append(f"{name}: field '{field}' must be a non-empty string")

        if not city.get("region", "").startswith("Regio"):
            errors.append(
                f"{name}: region '{city.get('region')}' should start with 'Regio'"
            )

    return errors


def get_cities_dataframe() -> "pd.DataFrame":
    """
    Return the catalog as a tidy pandas DataFrame with canonical column order.

    Returns
    -------
    pd.DataFrame
        One row per city; columns ordered for downstream pipeline consumption.
    """
    import pandas as pd

    df = pd.DataFrame(CITIES)
    df = df[
        [
            "pleiades_id",
            "latin_name",
            "modern_name",
            "region",
            "region_label",
            "lon",
            "lat",
            "notes",
        ]
    ].copy()
    df.index.name = "catalog_idx"
    return df


def get_city_by_pleiades_id(pleiades_id: int) -> dict[str, Any] | None:
    """Return a single city dict by its Pleiades ID, or None if not found."""
    for city in CITIES:
        if city["pleiades_id"] == pleiades_id:
            return city
    return None


def get_cities_by_region(region: str) -> list[dict[str, Any]]:
    """Return all cities belonging to a given Augustan region (e.g. 'Regio I')."""
    return [c for c in CITIES if c["region"] == region]


def summary() -> str:
    """Return a human-readable summary string of the catalog."""
    regions = {}
    for city in CITIES:
        regions.setdefault(city["region"], []).append(city["latin_name"])

    lines = [
        f"Roman Italian Cities Catalog — {len(CITIES)} cities",
        "=" * 50,
    ]
    for region in sorted(regions):
        cities = regions[region]
        lines.append(f"  {region}: {len(cities)} cities — {', '.join(sorted(cities))}")
    lines.append("=" * 50)
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    errors = validate_catalog()
    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    print(summary())
    print(f"\nAll {len(CITIES)} city records passed validation ✓")
