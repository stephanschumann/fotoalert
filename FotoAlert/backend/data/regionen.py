"""US-141 Baustein 1: Land und Region eines Orts aus seinen Koordinaten.

Regeln (Ticket US-141, Entscheidungen vom 2026-10-11):
  - Geografie entscheidet, nie der Name eines Orts. Der Parameter `name` wird bewusst ignoriert
    (Namensfalle „Sächsische Schweiz“ liegt in Deutschland, nicht in der Schweiz).
  - Zwei Ebenen: Land und darunter Region (Bundesländer, Kantone, Provinzen ...). England ist
    eine Region im Vereinigten Königreich (UK); die anderen drei UK-Regionen sind Nordirland,
    Schottland und Wales.
  - Orte außerhalb der Länderliste landen unter „Sonstige“ (ohne Regionen).
  - Ein Ort an einer Grenze zweier Regionen wird nicht still entschieden: Der Vorschlag trägt
    dann `unsicher=True`, damit das Menü nachfragen kann (AK-88).
  - Die Ortszeit-Regel von US-138 (Rechteck für „England“, calculations/ortszeit.py) bleibt
    UNVERÄNDERT und hängt NICHT an diesem Baustein (Entscheidung Frage 28).

Grenzdaten: data/regionen_grenzen.json, erzeugt von tools/build_regionen_grenzen.py aus Natural
Earth 1:10m (gemeinfrei; für Frankreich einschließlich der fünf Übersee-Regionen) und, für
Norwegen, Kartverket 2024 (CC BY 4.0). Die Quelle ist für
Weltkarten gedacht und vereinfacht; Grenzen können örtlich um einen bis wenige Kilometer
abweichen. Deshalb gilt:
  - Orte bis GRENZRAUM_M an der Grenze zu einer anderen Region gelten als unsicher.
  - Orte knapp neben den Grenzdaten (Küste, Hafenmole, Lücke) bekommen die nächstgelegene Region
    (bis KUESTE_M), ebenfalls als unsicher markiert.

Nur Standardbibliothek, Python 3.9-kompatibel. Die Grenzdaten werden erst beim ersten Aufruf von
schlage_region_vor() gelesen.
"""
from __future__ import annotations

import json
import math
import threading
from collections import namedtuple
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SONSTIGE = "Sonstige"
OHNE_REGION = "Ohne Region"   # Sonderfall je Land (Frage 26): Land mit Regionen, Region nicht bestimmbar
LAND_UK = "Vereinigtes Königreich (UK)"

GRENZRAUM_M = 2000.0   # näher als das an einer anderen Region = unsicher (AK-88)
KUESTE_M = 3000.0      # außerhalb der Grenzdaten, aber so nah: nächste Region, unsicher

# Feste Liste der Länder (Reihenfolge = Anzeigereihenfolge: alphabetisch nach deutschem Namen,
# „Sonstige“ am Ende) mit ihren Regionen (ebenfalls alphabetisch nach deutschem Namen; „Ohne Region“
# ist KEIN Listeneintrag, sondern ein Sonderfall je Land). Regionszahlen: Deutschland 16,
# Frankreich 18 (13 auf dem Festland einschließlich Korsika plus die fünf Übersee-Regionen;
# Entscheidung Stephan 2026-10-15 „Frankreich mit Übersee“), Italien 20, Niederlande 12,
# Norwegen 15 (seit 2024), Österreich 9, Schweiz 26, Vereinigtes Königreich 4.
REGIONEN: Dict[str, Tuple[str, ...]] = {
    "Deutschland": (
        "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen",
        "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz",
        "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen",
    ),
    "Frankreich": (
        "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne", "Centre-Val de Loire",
        "Französisch-Guayana", "Grand Est", "Guadeloupe", "Hauts-de-France", "Korsika",
        "La Réunion", "Martinique", "Mayotte", "Normandie", "Nouvelle-Aquitaine", "Okzitanien",
        "Pays de la Loire", "Provence-Alpes-Côte d'Azur", "Île-de-France",
    ),
    "Italien": (
        "Abruzzen", "Aostatal", "Apulien", "Basilicata", "Emilia-Romagna", "Friaul-Julisch Venetien",
        "Kalabrien", "Kampanien", "Latium", "Ligurien", "Lombardei", "Marken", "Molise", "Piemont",
        "Sardinien", "Sizilien", "Toskana", "Trentino-Südtirol", "Umbrien", "Venetien",
    ),
    "Niederlande": (
        "Drenthe", "Flevoland", "Friesland", "Gelderland", "Groningen", "Limburg", "Nordbrabant",
        "Nordholland", "Overijssel", "Seeland", "Südholland", "Utrecht",
    ),
    "Norwegen": (
        "Agder", "Akershus", "Buskerud", "Finnmark", "Innlandet", "Møre og Romsdal", "Nordland",
        "Oslo", "Rogaland", "Telemark", "Troms", "Trøndelag", "Vestfold", "Vestland", "Østfold",
    ),
    "Österreich": (
        "Burgenland", "Kärnten", "Niederösterreich", "Oberösterreich", "Salzburg", "Steiermark",
        "Tirol", "Vorarlberg", "Wien",
    ),
    "Schweiz": (
        "Aargau", "Appenzell Ausserrhoden", "Appenzell Innerrhoden", "Basel-Landschaft", "Basel-Stadt",
        "Bern", "Freiburg", "Genf", "Glarus", "Graubünden", "Jura", "Luzern", "Neuenburg", "Nidwalden",
        "Obwalden", "Schaffhausen", "Schwyz", "Solothurn", "St. Gallen", "Tessin", "Thurgau", "Uri",
        "Waadt", "Wallis", "Zug", "Zürich",
    ),
    LAND_UK: ("England", "Nordirland", "Schottland", "Wales"),
    SONSTIGE: (),
}

LAENDER: List[str] = list(REGIONEN)

_GRENZDATEN = Path(__file__).with_name("regionen_grenzen.json")
_M_PRO_GRAD_BREITE = 110540.0
_M_PRO_GRAD_LAENGE = 111320.0


class Zuordnung(namedtuple("Zuordnung", ["land", "region", "unsicher"])):
    """Ergebnis von schlage_region_vor(): Land, Region (None = keine) und ob der Vorschlag unsicher ist.

    Verhält sich wie ein Tupel (land, region, unsicher). Zusätzlich gilt ein Vergleich mit einem
    TEXT als Vergleich mit dem Land — das ist die frühere Rückgabeform („nur das Gebiet“) und wird
    von den unveränderten Fällen in test_us141_regel.py (Orte nach Lage, ungültige Koordinaten)
    weiter so geprüft.
    """

    __slots__ = ()

    def __eq__(self, other):
        if isinstance(other, str):
            return self.land == other
        return tuple.__eq__(self, other)

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = tuple.__hash__

    def als_dict(self) -> dict:
        return {"land": self.land, "region": self.region, "unsicher": self.unsicher}


_SONSTIGE_ERGEBNIS = Zuordnung(SONSTIGE, None, False)

# ── Grenzdaten (lazy) ────────────────────────────────────────────────────────

_sperre = threading.Lock()
_polygone: Optional[list] = None   # Einträge: (land, region, ringe, (min_lon, min_lat, max_lon, max_lat), bbox_fläche)


def _lade_polygone() -> list:
    global _polygone
    if _polygone is not None:
        return _polygone
    with _sperre:
        if _polygone is not None:
            return _polygone
        roh = json.loads(_GRENZDATEN.read_text(encoding="utf-8"))
        liste = []
        for g in roh["gebiete"]:
            for poly in g["polygone"]:
                aussen = poly[0]
                lons = [p[0] for p in aussen]
                lats = [p[1] for p in aussen]
                box = (min(lons), min(lats), max(lons), max(lats))
                flaeche = (box[2] - box[0]) * (box[3] - box[1])
                liste.append((g["land"], g["region"], poly, box, flaeche))
        _polygone = liste
        return _polygone


def _im_ring(lon: float, lat: float, ring: list) -> bool:
    innen = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat):
            if lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
                innen = not innen
        j = i
    return innen


def _im_polygon(lon: float, lat: float, poly: list) -> bool:
    if not _im_ring(lon, lat, poly[0]):
        return False
    for loch in poly[1:]:
        if _im_ring(lon, lat, loch):
            return False
    return True


def _abstand_m(lon: float, lat: float, poly: list) -> float:
    """Kleinster Abstand (Meter) vom Punkt zu den Ringkanten des Polygons (äußerer Ring und Löcher)."""
    kx = math.cos(math.radians(lat)) * _M_PRO_GRAD_LAENGE
    ky = _M_PRO_GRAD_BREITE
    best = float("inf")
    for ring in poly:
        ax = (ring[0][0] - lon) * kx
        ay = (ring[0][1] - lat) * ky
        for k in range(1, len(ring)):
            bx = (ring[k][0] - lon) * kx
            by = (ring[k][1] - lat) * ky
            dx, dy = bx - ax, by - ay
            l2 = dx * dx + dy * dy
            if l2 == 0.0:
                d = math.hypot(ax, ay)
            else:
                t = max(0.0, min(1.0, -(ax * dx + ay * dy) / l2))
                d = math.hypot(ax + t * dx, ay + t * dy)
            if d < best:
                best = d
            ax, ay = bx, by
    return best


def _koordinate(wert) -> Optional[float]:
    if isinstance(wert, bool) or wert is None:
        return None
    try:
        zahl = float(wert)
    except (TypeError, ValueError):
        return None
    return zahl if math.isfinite(zahl) else None


def schlage_region_vor(lat, lon, name=None) -> Zuordnung:
    """Land und Region für eine Koordinate (AK-85 bis AK-89).

    `name` wird nie ausgewertet. Ungültige Koordinaten (fehlend, keine Zahl, nicht endlich,
    außerhalb von ±90/±180) ergeben ("Sonstige", None, unsicher=False) — ohne Absturz.
    Dieselbe Lage ergibt immer dieselbe Antwort.
    """
    la = _koordinate(lat)
    lo = _koordinate(lon)
    if la is None or lo is None or abs(la) > 90.0 or abs(lo) > 180.0:
        return _SONSTIGE_ERGEBNIS

    alle = _lade_polygone()

    # 1. Punkt in einem Polygon? Bei mehreren Treffern (Enklave, ungenaue Grenze) gewinnt das kleinste.
    treffer = None
    for eintrag in alle:
        box = eintrag[3]
        if box[0] <= lo <= box[2] and box[1] <= la <= box[3] and _im_polygon(lo, la, eintrag[2]):
            if treffer is None or eintrag[4] < treffer[4]:
                treffer = eintrag

    # Suchrahmen in Grad für die Abstandsprüfung
    breite_grad = max(GRENZRAUM_M, KUESTE_M) / _M_PRO_GRAD_BREITE
    laenge_grad = max(GRENZRAUM_M, KUESTE_M) / (max(math.cos(math.radians(la)), 0.05) * _M_PRO_GRAD_LAENGE)

    def nahe(eintrag) -> bool:
        b = eintrag[3]
        return (b[0] - laenge_grad <= lo <= b[2] + laenge_grad) and (b[1] - breite_grad <= la <= b[3] + breite_grad)

    if treffer is not None:
        land, region = treffer[0], treffer[1]
        unsicher = False
        for eintrag in alle:
            if (eintrag[0], eintrag[1]) == (land, region) or not nahe(eintrag):
                continue
            if _abstand_m(lo, la, eintrag[2]) <= GRENZRAUM_M:
                unsicher = True
                break
        return Zuordnung(land, region, unsicher)

    # 2. Außerhalb aller Polygone: nächstes Gebiet innerhalb KUESTE_M (Küste, Mole, Lücke), unsicher.
    bester = None
    bester_abstand = KUESTE_M
    for eintrag in alle:
        if not nahe(eintrag):
            continue
        d = _abstand_m(lo, la, eintrag[2])
        if d <= bester_abstand:
            bester, bester_abstand = eintrag, d
    if bester is not None:
        return Zuordnung(bester[0], bester[1], True)
    return _SONSTIGE_ERGEBNIS


def ist_gueltig(land: Optional[str], region: Optional[str]) -> bool:
    """Gehört die Region zum Land? „Ohne Region“ ist für Länder mit Regionen erlaubt; „Sonstige“
    hat keine Regionen (region None oder leer)."""
    if land not in REGIONEN:
        return False
    if land == SONSTIGE:
        return region in (None, "")
    return region == OHNE_REGION or region in REGIONEN[land]
