"""
FotoAlert - Scout-Zugaenglichkeits-/Sichtfreiheits-Filter (US-135)

Filtert Scout-Kandidaten (ScoutOpportunity), deren vorgeschlagener Standpunkt
laut Live-Kartendaten nicht zu Fuss erreichbar ist (Wald ohne Weg in der
Naehe, Wasser, aktive Bahnanlage) oder deren Sichtlinie zum Motiv komplett
durch ein Gebaeude verdeckt ist (US-135 Regel 1+2, Example Mapping).

Implementierungsoption A (freigegeben 2026-08-07):
  - Kandidaten werden vor der Live-Pruefung auf ein grobes Raster geclustert
    (ACCESSIBILITY_CLUSTER_SIZE_M) -- pro Rasterzelle (+ Motiv, siehe
    _cluster_key) genau EINE kombinierte Overpass-Live-Anfrage (Sichtlinie
    + Wald/Wasser/Bahn/Weg, data/qa_azimuth.get_scout_accessibility_data),
    nicht eine pro Kandidat. Reduziert die Last massiv (Pre-Mortem: bis zu
    ~2000 Anfragen/Tag bei 1:1-Pruefung ohne Clusterung).
  - Kann eine Pruefung nicht durchgefuehrt werden (Timeout/Fehler/kein
    Ergebnis), gelten ALLE Kandidaten der betroffenen Zelle als NICHT
    bestaetigt und werden ausgeblendet -- kein Label, keine Fehlermeldung
    (Stephan-Entscheidung, US-135-Analyse "im Zweifel ausblenden").
  - Gilt AUSSCHLIESSLICH fuer Scout-Tab-Vorschlaege -- bereits gespeicherte
    Standorte und deren bestehende Sichtachsen-Pruefung (US-09,
    calculations/sightline.py) bleiben vollstaendig unveraendert.

Python-3.9-kompatibel.
"""
from __future__ import annotations

import logging
import math
from typing import Iterable, List, Sequence

from data import qa_azimuth

log = logging.getLogger(__name__)

# Cluster-Rastergroesse (Meter) -- rein technische Lastreduktions-
# Entscheidung, NICHT identisch mit dem fachlichen 50m-Wegradius-AK
# (qa_azimuth.SCOUT_ACCESS_PATH_RADIUS_M). Orientiert an den bestehenden
# Nachbarschafts-Konstanten _DEDUP_RADIUS_M (200m, discover/subjects.py) und
# SCOUT_MIN_NEW_DISTANCE_M (150m, discover/pipeline_base.py), aber bewusst
# feiner gewaehlt: hier wird die tatsaechliche lokale Zugaenglichkeit
# (Wald/Wasser/Bahn/Weg) je Zelle geprueft, nicht nur ein Mindestabstand zu
# bereits bekannten Standorten.
ACCESSIBILITY_CLUSTER_SIZE_M: float = 80.0

_METERS_PER_DEG_LAT: float = 111_320.0


def _meters_per_deg_lon(lat_deg: float) -> float:
    m = 111_320.0 * math.cos(math.radians(lat_deg))
    return m or 1.0


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def _attr(candidate, name: str):
    """Duck-typed Feldzugriff -- funktioniert fuer ScoutOpportunity-Objekte
    (Produktionspfad) UND fuer einfache Dicts (Testkomfort)."""
    if isinstance(candidate, dict):
        return candidate.get(name)
    return getattr(candidate, name, None)


def _cluster_key(candidate) -> tuple:
    """Rundet Standpunkt + Motiv-ID auf eine Rasterzelle (ACCESSIBILITY_
    CLUSTER_SIZE_M). Das Motiv gehoert bewusst mit in den Schluessel: zwei
    Kandidaten mit fast identischem Standpunkt, aber unterschiedlichem
    Motiv, brauchen trotzdem je eine eigene Sichtlinien-Pruefung (die Sicht
    haengt vom Motiv ab, nicht nur vom Standpunkt)."""
    lat = _attr(candidate, "standpoint_lat")
    lon = _attr(candidate, "standpoint_lon")
    subject_id = _attr(candidate, "subject_id")
    lon_m = _meters_per_deg_lon(lat)
    cell_lat = round(lat * _METERS_PER_DEG_LAT / ACCESSIBILITY_CLUSTER_SIZE_M)
    cell_lon = round(lon * lon_m / ACCESSIBILITY_CLUSTER_SIZE_M)
    return (subject_id, cell_lat, cell_lon)


def _point_in_polygon(lat: float, lon: float, nodes: Sequence) -> bool:
    """Ray-Casting Punkt-in-Polygon-Test (nodes: [(lat,lon), ...]). Lat/Lon
    werden wie ebene x/y-Koordinaten behandelt -- fuer die hier relevanten
    kleinraeumigen Wald-/Wasserflaechen ausreichend genau (gleiches
    Praezisionsniveau wie die bestehenden Winkelberechnungen in
    data/qa_azimuth.py, z.B. _footprint_angular_span)."""
    if len(nodes) < 3:
        return False
    inside = False
    n = len(nodes)
    j = n - 1
    for i in range(n):
        yi, xi = nodes[i]
        yj, xj = nodes[j]
        if (yi > lat) != (yj > lat):
            x_intersect = (xj - xi) * (lat - yi) / ((yj - yi) or 1e-15) + xi
            if lon < x_intersect:
                inside = not inside
        j = i
    return inside


def _point_to_segment_distance_m(
    lat: float, lon: float, lat1: float, lon1: float, lat2: float, lon2: float,
) -> float:
    """Punkt-zu-Strecken-Distanz (Meter) fuer EIN Kantensegment einer OSM-
    Way-Geometrie -- lokale ebene Naeherung (lat/lon ueber die bestehenden
    Meter-pro-Grad-Faktoren in x/y umgerechnet), gleiches Genauigkeitsniveau
    wie _point_in_polygon/_haversine_m.

    US-135 Nachbesserung (2026-08-08, realer Fall 'Schloss Pfaueninsel –
    Rundtuerme'): Ersetzt die vorherige reine Punkt-zu-KNOTEN-Distanz. Bei
    sparsam beknoteten, aber raeumlich grossen Wegen (hier: die Havel als
    natural=water-Polygon mit 157 Knoten ueber mehrere hundert Meter
    Uferlaenge) kann die naechste KANTE weit naeher am Standpunkt liegen als
    der naechste KNOTEN. Live beobachtet: gemeldete Knoten-Distanz 94m
    (> SCOUT_ACCESS_WATER_LINE_BUFFER_M), tatsaechliche Kanten-Distanz zur
    Uferlinie unter 10m -- der im Wasser liegende Standpunkt blieb dadurch
    faelschlich als 'zugaenglich' im Scout-Feed sichtbar (AK4-Verletzung)."""
    lon_m = _meters_per_deg_lon(lat)
    px, py = lon * lon_m, lat * _METERS_PER_DEG_LAT
    x1, y1 = lon1 * lon_m, lat1 * _METERS_PER_DEG_LAT
    x2, y2 = lon2 * lon_m, lat2 * _METERS_PER_DEG_LAT
    dx, dy = x2 - x1, y2 - y1
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = x1 + t * dx, y1 + t * dy
    return math.hypot(px - cx, py - cy)


def _min_distance_to_ways_m(lat: float, lon: float, ways: Iterable[dict]) -> float:
    """Kuerzeste Distanz (Meter) zu irgendeiner KANTE (nicht nur zu den
    Knoten) der uebergebenen Wege -- siehe _point_to_segment_distance_m fuer
    die Begruendung der US-135-Nachbesserung vom 2026-08-08. Wege mit nur
    einem Knoten fallen auf die reine Punkt-Distanz zurueck. Gibt
    float('inf') zurueck, wenn `ways` leer ist."""
    best = float("inf")
    for w in ways:
        nodes = w.get("nodes") or []
        if len(nodes) == 1:
            d = _haversine_m(lat, lon, nodes[0][0], nodes[0][1])
            if d < best:
                best = d
            continue
        for i in range(len(nodes) - 1):
            lat1, lon1 = nodes[i]
            lat2, lon2 = nodes[i + 1]
            d = _point_to_segment_distance_m(lat, lon, lat1, lon1, lat2, lon2)
            if d < best:
                best = d
    return best


def _is_excluded(standpoint_lat: float, standpoint_lon: float, data: dict) -> bool:
    """US-135 Regel 2: Standpunkt gilt als NICHT zu Fuss erreichbar, wenn er
    im Wasser liegt, auf/direkt neben aktiven Bahngleisen liegt, oder
    mitten im Wald OHNE Weg in der Naehe (qa_azimuth.SCOUT_ACCESS_PATH_
    RADIUS_M) liegt."""
    water_ways = data.get("water_ways") or []

    # US-135 Nachbesserung (2026-08-09, Havel/Pfaueninsel-Beweisfall
    # 52.429605/13.114616): Grosse mehrteilige Wasserflaechen liefert
    # qa_azimuth.py jetzt als zu Ringen zusammengesetzte Multipolygon-
    # Relationen (relation_id gesetzt) -- je Relation ggf. mehrere
    # geschlossene Ringe (1x outer + 0..n inner fuer Inseln wie die
    # Pfaueninsel selbst). Ein simples "in irgendeinem geschlossenen Ring"
    # wuerde eine Insel (inner-Rolle) faelschlich als Wasser zaehlen, weil
    # ein Punkt auf der Insel auch innerhalb des Aussenrings liegt. Deshalb
    # gilt je Relation die Standard-Gerade-Ungerade-Regel fuer Multipolygone
    # mit Loechern: ein Punkt zaehlt als "im Wasser", wenn er in einer
    # UNGERADEN Anzahl der Ringe DERSELBEN Relation liegt (nur im outer ->
    # 1 = ungerade -> Wasser; im outer UND zusaetzlich in einem inner/
    # Insel-Ring -> 2 = gerade -> kein Wasser). Eigenstaendige Ways ohne
    # relation_id (Alt-Fall: ein einzelner, bereits selbst geschlossener
    # way["natural"="water"]) bilden weiterhin je ihre eigene Ein-Ring-Gruppe
    # -- exakt das Verhalten von vor dieser Nachbesserung.
    #
    # US-135 Randfall-Nachbesserung (2026-08-09, Zweitpruefung): Ringe
    # werden jetzt zusaetzlich nach role ("outer"/"inner", von qa_azimuth.py
    # je Member-Way gesetzt) gruppiert. Scheitert die Rekonstruktion des
    # Aussenrings einer Relation (z.B. Overpass liefert nicht alle Member-
    # Ways -> offene Restsegmente, "closed" bleibt False), aber ein
    # Innenring (z.B. die Pfaueninsel als Loch) wird trotzdem erfolgreich
    # geschlossen, darf die Gerade-Ungerade-Regel NICHT alleine auf diesen
    # Innenring angewendet werden -- sonst zaehlt ein Punkt AUF der Insel
    # faelschlich als "im Wasser" (enclosing_count=1, ungerade), obwohl es
    # Land ist. Deshalb: die Lochregel greift je Relation nur, wenn
    # mindestens ein geschlossener OUTER-Ring vorhanden ist. Fehlt ein
    # geschlossener Outer-Ring komplett, wird die Relation fuer die
    # Lochregel uebersprungen -- der Fall degradiert defensiv auf den
    # bestehenden 15m-Kantenpuffer weiter unten (lieber ein potenziell
    # uebersehener Wasserpunkt als ein faelschlich verworfener Landpunkt).
    # Eigenstaendige Ways ohne relation_id haben kein "role"-Feld und gelten
    # weiterhin implizit als "outer" -- unveraendertes Alt-Verhalten.
    ring_groups: dict = {}
    for w in water_ways:
        if not w.get("closed"):
            continue
        nodes = w.get("nodes") or []
        if len(nodes) < 3:
            continue
        group_key = w.get("relation_id")
        if group_key is None:
            group_key = id(w)
        role = w.get("role") or "outer"
        group = ring_groups.setdefault(group_key, {"outer": [], "inner": []})
        group.setdefault(role, []).append(nodes)

    for group in ring_groups.values():
        outer_rings = group.get("outer") or []
        if not outer_rings:
            # Kein geschlossener Outer-Ring fuer diese Relation -- die
            # Lochregel ist ohne Aussenring nicht anwendbar (siehe Kommentar
            # oben). Ggf. vorhandene Inner-Ringe allein begruenden keinen
            # Wasser-Ausschluss.
            continue
        rings = outer_rings + (group.get("inner") or [])
        enclosing_count = sum(
            1 for nodes in rings
            if _point_in_polygon(standpoint_lat, standpoint_lon, nodes)
        )
        if enclosing_count % 2 == 1:
            return True

    if _min_distance_to_ways_m(standpoint_lat, standpoint_lon, water_ways) < qa_azimuth.SCOUT_ACCESS_WATER_LINE_BUFFER_M:
        return True

    rail_ways = data.get("rail_ways") or []
    if _min_distance_to_ways_m(standpoint_lat, standpoint_lon, rail_ways) < qa_azimuth.SCOUT_ACCESS_RAIL_BUFFER_M:
        return True

    forest_ways = data.get("forest_ways") or []
    in_forest = any(
        _point_in_polygon(standpoint_lat, standpoint_lon, f.get("nodes") or [])
        for f in forest_ways
    )
    if in_forest:
        nearest_path_m = _min_distance_to_ways_m(standpoint_lat, standpoint_lon, data.get("path_ways") or [])
        if nearest_path_m > qa_azimuth.SCOUT_ACCESS_PATH_RADIUS_M:
            return True

    return False


def filter_accessible_candidates(candidates: Sequence) -> list:
    """
    US-135: Filtert eine Liste von Scout-Kandidaten (ScoutOpportunity-
    Objekte oder gleichwertige Dicts mit standpoint_lat/standpoint_lon/
    subject_lat/subject_lon/subject_id) auf tatsaechlich zugaengliche UND
    sichtfreie Vorschlaege.

    Implementierungsoption A: Kandidaten werden vor der Live-Pruefung auf
    ein grobes Raster geclustert (ACCESSIBILITY_CLUSTER_SIZE_M) -- pro
    Rasterzelle genau EINE kombinierte Overpass-Live-/Cache-Anfrage
    (qa_azimuth.get_scout_accessibility_data). WICHTIG (US-135 Nachbesserung
    2026-08-08): Das Cluster buendelt NUR die Overpass-ANFRAGE, nicht das
    VERDIKT -- jedes einzelne Cluster-Mitglied wird mit seinem eigenen
    exakten Standpunkt gegen die gemeinsam geladenen Live-Daten geprueft,
    weil der 50m-Wegradius (AK2) und die Wasserflaeche/-linie (AK4) feiner
    sind als die 80m-Rasterzelle.

    Kann fuer eine Zelle keine Pruefung durchgefuehrt werden (Timeout/
    Fehler/kein Ergebnis -- auch bei einer Exception der Pruef-Funktion
    selbst), gelten ALLE Kandidaten dieser Zelle als NICHT bestaetigt und
    werden ausgeblendet -- kein Label, keine Fehlermeldung (US-135 Regel 3,
    Stephan-Entscheidung "im Zweifel ausblenden"). Nie eine Exception nach
    aussen.

    Gilt ausschliesslich fuer Scout-Tab-Vorschlaege -- veraendert nie
    gespeicherte Standorte oder deren bestehende Sichtachsen-Pruefung
    (calculations/sightline.py, US-09).
    """
    clusters: dict = {}
    order: list = []
    for c in candidates:
        key = _cluster_key(c)
        if key not in clusters:
            clusters[key] = []
            order.append(key)
        clusters[key].append(c)

    accepted: list = []
    for key in order:
        members = clusters[key]
        rep = members[0]
        rep_lat = _attr(rep, "standpoint_lat")
        rep_lon = _attr(rep, "standpoint_lon")
        rep_subject_lat = _attr(rep, "subject_lat")
        rep_subject_lon = _attr(rep, "subject_lon")

        try:
            data = qa_azimuth.get_scout_accessibility_data(
                observer_lat=rep_lat, observer_lon=rep_lon,
                subject_lat=rep_subject_lat, subject_lon=rep_subject_lon,
            )
        except Exception as exc:  # US-135 Regel 3: nie crashen, im Zweifel ausblenden
            log.warning("US-135 Zugaenglichkeitspruefung fuer Cluster %s fehlgeschlagen: %s", key, exc)
            data = None

        if data is None:
            log.info("US-135: Cluster %s (%d Kandidaten) nicht pruefbar -- ausgeblendet.", key, len(members))
            continue

        # US-135 Nachbesserung (2026-08-08, realer Fall Schloss Pfaueninsel,
        # Cluster mit 7 Mitgliedern Tage 10.-16.8., nur der Repraesentant lag
        # nachweislich an Land): Die Rasterzelle (ACCESSIBILITY_CLUSTER_SIZE_M
        # = 80m) buendelt NUR die Overpass-Anfrage -- eine Abfrage pro Zelle
        # statt pro Kandidat. Das gemeinsam geladene 'data' darf aber nicht zu
        # einem gemeinsamen VERDIKT fuehren: der 50m-Wegradius (AK2) und die
        # Wasserlinie/-flaeche (AK4) sind feiner als die 80m-Zelle, zwei
        # Mitglieder derselben Zelle koennen also einen unterschiedlichen
        # tatsaechlichen Zugaenglichkeitsstatus haben. Deshalb jetzt jedes
        # Mitglied einzeln (mit seinem eigenen exakten Standpunkt) gegen die
        # bereits geladenen 'data' pruefen -- kein zusaetzlicher Overpass-Call,
        # nur eine zusaetzliche lokale Pruefung pro Mitglied.
        for member in members:
            m_lat = _attr(member, "standpoint_lat")
            m_lon = _attr(member, "standpoint_lon")
            m_subject_lat = _attr(member, "subject_lat")
            m_subject_lon = _attr(member, "subject_lon")

            blocked = qa_azimuth.is_sightline_blocked_by_buildings(
                m_lat, m_lon, m_subject_lat, m_subject_lon,
                data.get("buildings") or [],
            )
            if blocked:
                continue

            # BUG-101: analog zur Gebaeude-Sichtpruefung oben, zusaetzlich
            # gegen Wald/Baeume pruefen -- nutzt dieselben bereits geladenen
            # 'data' (forest_ways), kein zusaetzlicher Overpass-Call (AK7).
            # Wirkt ZUSAETZLICH zur bestehenden Wald+Weg-Zugaenglichkeits-
            # pruefung in _is_excluded() weiter unten (US-135 Regel 2), nicht
            # anstelle davon (BUG-101 AK4).
            blocked_by_vegetation = qa_azimuth.is_sightline_blocked_by_vegetation(
                m_lat, m_lon, m_subject_lat, m_subject_lon,
                data.get("forest_ways") or [],
            )
            if blocked_by_vegetation:
                continue

            if _is_excluded(m_lat, m_lon, data):
                continue

            accepted.append(member)

    return accepted
