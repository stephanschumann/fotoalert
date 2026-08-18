"""
FotoAlert – Auto-Ableitung des idealen Azimut-Bereichs (TASK-45)

Leitet für Locations ohne kuratierten Idealbereich automatisch ab, aus welcher
Himmelsrichtung Sonne oder Mond hinter dem Motiv stehen müssten.

Strategie (Option C — Bearing-Basis + optionale Overpass-Verfeinerung):
  • **Basis (immer):** Peilung (Bearing) vom Fotografen-Standort zum Motiv,
    aufgeweitet um eine feste Toleranz → (ideal_azimuth_min, ideal_azimuth_max).
    Kein Netz, deterministisch, sofort für jeden Spot mit beiden Koordinaten.
  • **Verfeinerung (optional):** Wo ein OSM-Gebäude-Footprint sauber ladbar ist,
    wird der Bereich auf die tatsächliche horizontale Ausdehnung des Bauwerks
    (linke bis rechte Kante vom Standort aus gesehen) verbreitert.
  • **Still degradierend:** Jeder Netzfehler, jedes Timeout, jede fehlende
    Geometrie fällt geräuschlos auf die Bearing-Basis zurück — kein Crash,
    keine Exception nach außen.

Bereichs-Konvention (kompatibel zu main._compute_possible_bodies):
  (min, max) als Grad 0–360. Kreuzt das Band die Nordgrenze (0/360°), gilt
  min > max (z.B. (350, 10)); der Konsument interpretiert das als Wrap-around.

Python-3.9-kompatibel.
"""

from __future__ import annotations

import json
import logging
import os
import math
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, timezone

from discover.geometry import bearing_between

logger = logging.getLogger(__name__)

# Default-Toleranz: Halbe Bandbreite um die Sichtlinie (Grad).
# ±15° ist die konventionelle Vorgabe aus der TASK-45-Spec.
DEFAULT_TOLERANCE_DEG: float = 15.0

# Overpass: öffentlicher Endpoint + kurzes Timeout, damit ein langsamer/down
# Server den QA-Lauf nicht hängen lässt (Pre-Mortem-Gegenmaßnahme).
OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
# Mirror-Liste für Fallback bei Serverblockade/-ausfall: overpass-api.de
# zuerst (TASK-59, live verifiziert 2026-08-02 mit gesetztem User-Agent/
# Referer-Header: liefert echte Daten, keine Sperre mehr), kumi.systems als
# zweiter Versuch (liefert im selben Live-Test weiterhin einen Timeout-Fehler
# "server too busy" — Grundproblem ist echte Serverauslastung, nicht der
# fehlende Header, bleibt daher unzuverlässig).
OVERPASS_MIRRORS: List[str] = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
OVERPASS_TIMEOUT_S: float = 8.0
# Suchradius um die Motiv-Koordinate für den Gebäude-Footprint (Meter).
OVERPASS_SEARCH_RADIUS_M: int = 40

# TASK-59: Optionale eigene Overpass-Server-Adresse (künftiger, selbst
# gehosteter Server für zuverlässigere Gebäudedaten). Der Server existiert
# noch NICHT — Stephan baut ihn erst in einem separaten Schritt auf. Solange
# die Umgebungsvariable leer/nicht gesetzt ist (heutiger Zustand), bleibt das
# Verhalten exakt wie vor TASK-59: nur OVERPASS_MIRRORS wird angefragt. Ist
# sie gesetzt, versucht _fetch_from_mirrors() zuerst diesen eigenen Server und
# fällt bei dessen Fehlschlag automatisch auf OVERPASS_MIRRORS zurück
# (von Stephan am 2026-07-15 bestätigte Ausfallverhalten-Variante "öffentliche
# Server bleiben Rückfallebene", TASK-59 Frage 2 / AK "Edge Case: Fällt der
# eigene Server komplett aus...").
OWN_OVERPASS_URL: Optional[str] = os.environ.get("OWN_OVERPASS_URL") or None

# TASK-59 Option E (2026-08-02): Aus der Recherche zur Zuverlässigkeit der
# öffentlichen Mirrors — beide (Kumi/Private.coffee, overpass-api.de/FOSSGIS)
# verlangen laut OSM-Wiki einen gesetzten User-Agent/Referer-Header; ein
# bisher nicht gesetzter Header ist ein möglicher (bisher nicht geprüfter)
# Mitgrund für die bisherigen Sperren/Timeouts. Kostet nichts, gilt für JEDE
# Anfrage an einen Overpass-Server (eigenen wie öffentlichen).
OVERPASS_USER_AGENT: str = (
    "FotoAlert/1.0 (+https://fotoalert.stephanschumann.com; "
    "contact: stephanschumann@me.com)"
)
OVERPASS_REFERER: str = "https://fotoalert.stephanschumann.com"
OVERPASS_REQUEST_HEADERS: dict = {
    "User-Agent": OVERPASS_USER_AGENT,
    "Referer": OVERPASS_REFERER,
}

# Live-Bug (US-09): Der kostenlose Overpass-Server lehnt bei zu schneller
# Anfragefolge Verbindungen ab ([Errno 61] Connection refused), wodurch der
# Sichtachsen-Check für praktisch alle Locations auf "nicht_geprueft" zurückfiel.
# Overpass empfiehlt bei Bulk-Nutzung nicht schneller als ~1 Anfrage/Sekunde;
# 1.2s ist ein konservativer Puffer darüber (analog RATE_LIMIT_PAUSE_S in
# elevation.py für OpenTopoData). Dieser Client ist synchron (httpx.Client,
# kein async/await) — daher threading.Lock + time.sleep() statt asyncio.
OVERPASS_RATE_LIMIT_PAUSE_S: float = 1.2

# Obergrenze für die Toleranz: knapp unter 180°, damit ein gepuffertes Band nie
# zum Vollkreis (min == max) entartet.
MAX_TOLERANCE_DEG: float = 179.999

# Modul-weiter Rate-Limit-Tracker für Overpass-Netzanfragen: hält den Abstand
# zur letzten tatsächlichen Netzanfrage auch ÜBER beide Aufrufer hinweg ein
# (_fetch_overpass_footprint UND fetch_buildings_along_line treffen denselben
# Server). Lock macht das gegen gleichzeitige Aufrufe aus verschiedenen Threads
# sicher (synchrones Pendant zu _rate_limit_lock in elevation.py).
_overpass_rate_limit_lock = threading.Lock()
_last_overpass_request_ts: Optional[float] = None

# ---------------------------------------------------------------------------
# TASK-59 Option E (2026-08-02): lokale Batch-Cache-Datei statt Live-Anfrage
# ---------------------------------------------------------------------------
# Kein eigener Server mehr (siehe Weg-Gate-Entscheidung 2026-08-02, ersetzt die
# Server-Entscheidung vom 2026-07-15). Stattdessen extrahiert ein wöchentlich
# laufender GitHub-Actions-Workflow (produktiv seit 2026-08-02, siehe
# .github/workflows/update-building-data.yml) regelmäßig Gebäude-Footprints
# aus einem lokalen Geofabrik-Auszug für die ~60 bekannten Basis-Locations
# (backend/data/locations.py) und committet das
# Ergebnis als backend/data/cache/building_footprints.json ins Repo. Beide
# Funktionen unten (_fetch_overpass_footprint, fetch_buildings_along_line)
# schauen zuerst hier nach, BEVOR sie einen Live-Mirror kontaktieren.
#
# Bewusste Scope-Grenze: Nur die Basis-Locations aus data/locations.py sind
# Teil des Batch-Exports, da nur sie im Git-Repo stehen — Custom-Locations
# (vom Host über die App angelegt) leben ausschließlich in der Server-DB und
# sind dem GitHub-Actions-Workflow nicht zugänglich. Für sie (und für neu
# angelegte/koordinaten-korrigierte Basis-Locations, die noch nicht im
# letzten Batch-Lauf enthalten sind) bleibt der bestehende Live-Mirror-Pfad
# unverändert die einzige Datenquelle — automatisch, ohne Sonderfall-Code:
# ein Koordinaten-Abgleich, der keinen Treffer findet, fällt einfach durch.
BUILDING_CACHE_PATH: Path = Path(__file__).resolve().parent / "cache" / "building_footprints.json"

# Toleranz für den Koordinaten-Abgleich zwischen einer Live-Anfrage und einem
# Cache-Eintrag (Grad, ~1m bei diesem Wert). Beide Werte stammen aus derselben
# Python-Fließkommazahl über JSON-Round-Trip — 1e-5 ist großzügig genug für
# Rundungsrauschen, aber eng genug, dass eine tatsächlich manuell korrigierte
# Koordinate (Meter- bis Zehnermeter-Bereich) zuverlässig NICHT mehr matcht
# und automatisch auf den Live-Pfad zurückfällt.
BUILDING_CACHE_COORD_TOLERANCE_DEG: float = 1e-5

_building_cache_lock = threading.Lock()
# None = noch nicht geladen; danach immer eine Liste (ggf. leer bei fehlender
# oder fehlerhafter Datei — kein Unterschied zum "Cache-Miss"-Verhalten).
_building_cache_entries: Optional[List[dict]] = None


def _load_building_cache() -> List[dict]:
    """Lädt (einmalig, thread-sicher, gecached für die Prozesslaufzeit) die
    lokale Gebäude-Cache-Datei (TASK-59 Option E). Fehlt die Datei (z.B. weil
    der GitHub-Actions-Job noch nie erfolgreich gelaufen ist) oder ist sie
    fehlerhaft/leer, wird das geräuschlos wie eine leere Liste behandelt —
    jede Lookup-Anfrage fällt dann automatisch auf den Live-Mirror-Pfad
    zurück (kein Crash, keine Exception nach außen, kein Unterschied zum
    Verhalten vor Option E)."""
    global _building_cache_entries
    if _building_cache_entries is not None:
        return _building_cache_entries
    with _building_cache_lock:
        if _building_cache_entries is not None:
            return _building_cache_entries
        try:
            raw = json.loads(BUILDING_CACHE_PATH.read_text(encoding="utf-8"))
            entries = raw.get("locations") or []
        except FileNotFoundError:
            logger.info(
                "Lokale Gebäude-Cache-Datei %s existiert noch nicht — "
                "Live-Mirror-Pfad wird für alle Locations genutzt "
                "(GitHub-Actions-Job aus TASK-59 Option E noch nicht gelaufen?)",
                BUILDING_CACHE_PATH,
            )
            entries = []
        except (OSError, ValueError, AttributeError) as e:
            logger.warning(
                "Lokale Gebäude-Cache-Datei %s nicht lesbar (%s) — "
                "Live-Mirror-Pfad wird für alle Locations genutzt",
                BUILDING_CACHE_PATH, e,
            )
            entries = []
        _building_cache_entries = entries
        return _building_cache_entries


def _coords_match(a: Optional[float], b: Optional[float]) -> bool:
    """True, wenn beide Koordinaten gesetzt und innerhalb der Cache-Toleranz
    gleich sind."""
    if a is None or b is None:
        return False
    return abs(a - b) < BUILDING_CACHE_COORD_TOLERANCE_DEG


def _find_local_cache_entry(
    subject_lat: float,
    subject_lon: float,
    observer_lat: Optional[float] = None,
    observer_lon: Optional[float] = None,
) -> Optional[dict]:
    """Sucht in der lokalen Gebäude-Cache-Datei einen Eintrag, dessen Motiv-
    Koordinate (und, falls angegeben, auch dessen Standort-Koordinate) mit den
    übergebenen Werten übereinstimmt. Kein Treffer -> None; der Aufrufer fällt
    dann auf den bisherigen Live-Mirror-Pfad zurück (z.B. neu angelegte
    Location, seit dem letzten Batch-Lauf koordinaten-korrigierte Location,
    oder eine Custom-Location außerhalb des Batch-Exports)."""
    for entry in _load_building_cache():
        if not _coords_match(entry.get("subject_lat"), subject_lat):
            continue
        if not _coords_match(entry.get("subject_lon"), subject_lon):
            continue
        if observer_lat is not None and not _coords_match(entry.get("observer_lat"), observer_lat):
            continue
        if observer_lon is not None and not _coords_match(entry.get("observer_lon"), observer_lon):
            continue
        return entry
    return None


def _nearest_building_nodes(
    subject_lat: float,
    subject_lon: float,
    buildings: List[dict],
) -> Optional[List[Tuple[float, float]]]:
    """Wählt aus einer Liste gecachter Gebäude (je {"nodes": [[lat,lon],...],
    "height_m": float}) das mit dem Schwerpunkt am dichtesten an der Motiv-
    Koordinate — dieselbe Auswahlregel wie im Live-Pfad in
    _fetch_overpass_footprint(). Gibt None zurück, wenn `buildings` leer ist
    oder kein Eintrag mindestens 3 Knoten hat (kein valides Polygon)."""
    best_nodes: Optional[List[Tuple[float, float]]] = None
    best_dist = float("inf")
    for b in buildings:
        raw_nodes = b.get("nodes") or []
        nodes = [(float(n[0]), float(n[1])) for n in raw_nodes if len(n) == 2]
        if len(nodes) < 3:
            continue
        c_lat = sum(n[0] for n in nodes) / len(nodes)
        c_lon = sum(n[1] for n in nodes) / len(nodes)
        d = (c_lat - subject_lat) ** 2 + (c_lon - subject_lon) ** 2
        if d < best_dist:
            best_dist = d
            best_nodes = nodes
    return best_nodes


def _respect_overpass_rate_limit() -> None:
    """Wartet bei Bedarf, bis seit der letzten Overpass-Netzanfrage mindestens
    OVERPASS_RATE_LIMIT_PAUSE_S vergangen ist. Vor JEDER tatsächlichen
    Overpass-Netzanfrage aufrufen (Cache-Treffer gibt es hier nicht)."""
    global _last_overpass_request_ts
    if OVERPASS_RATE_LIMIT_PAUSE_S <= 0:
        return
    with _overpass_rate_limit_lock:
        now = time.monotonic()
        if _last_overpass_request_ts is not None:
            elapsed = now - _last_overpass_request_ts
            wait = OVERPASS_RATE_LIMIT_PAUSE_S - elapsed
            if wait > 0:
                time.sleep(wait)
        _last_overpass_request_ts = time.monotonic()


def _fetch_from_mirrors(query: str, timeout_s: float, log_context: str) -> Optional[dict]:
    """Versucht die gegebene Overpass-Query zuerst (optional) gegen den eigenen
    Server (TASK-59, `OWN_OVERPASS_URL`) und danach nacheinander gegen jeden
    Eintrag in OVERPASS_MIRRORS (je EIN Versuch pro Server, kein Retry auf
    demselben Server). Vor JEDEM Versuch wird _respect_overpass_rate_limit()
    aufgerufen — alle Server (eigener + Mirrors) werden gleich behandelt.

    Ist OWN_OVERPASS_URL nicht gesetzt (heutiger Zustand, Standard), verhält
    sich diese Funktion exakt wie vor TASK-59: nur OVERPASS_MIRRORS wird
    angefragt, gleiche Reihenfolge, gleiche Timeouts.

    Gibt das geparste JSON-Payload des ersten erfolgreichen Servers zurück,
    oder None, wenn alle fehlschlagen (der Aufrufer loggt dann und fällt still
    auf die Bearing-Basis zurück)."""
    import httpx  # lokaler Import: QA ohne Overpass braucht httpx nie

    last_error: Optional[Exception] = None

    if OWN_OVERPASS_URL:
        _respect_overpass_rate_limit()
        try:
            with httpx.Client(timeout=timeout_s, headers=OVERPASS_REQUEST_HEADERS) as client:
                resp = client.post(OWN_OVERPASS_URL, data={"data": query})
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            last_error = e
            # TASK-59: unterscheidbare Log-Meldung speziell für den EIGENEN
            # Server (nicht einen der öffentlichen Mirrors) — Grundlage für
            # eine spätere aktive Benachrichtigung. Kein Alert-Versand hier,
            # das folgt erst wenn der Server existiert (siehe Ticket).
            logger.warning(
                "Eigener Overpass-Server %s für %s fehlgeschlagen (%s) — "
                "Rückfall auf öffentliche Mirrors", OWN_OVERPASS_URL, log_context, e,
            )

    for mirror_url in OVERPASS_MIRRORS:
        _respect_overpass_rate_limit()
        try:
            with httpx.Client(timeout=timeout_s, headers=OVERPASS_REQUEST_HEADERS) as client:
                resp = client.post(mirror_url, data={"data": query})
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            last_error = e
            logger.info("Overpass-Mirror %s für %s fehlgeschlagen (%s)",
                        mirror_url, log_context, e)
    logger.info("Alle Overpass-Mirrors für %s fehlgeschlagen (letzter Fehler: %s)",
                log_context, last_error)
    return None


def _norm(deg: float) -> float:
    """Normalisiert einen Winkel auf [0, 360)."""
    return deg % 360.0


def _clamp_tolerance(tolerance_deg: float) -> float:
    """Begrenzt die Toleranz auf [0, MAX_TOLERANCE_DEG], damit min != max bleibt."""
    return max(0.0, min(tolerance_deg, MAX_TOLERANCE_DEG))


def _range_from_bearing(bearing: float, tolerance_deg: float) -> Tuple[float, float]:
    """Bildet (min, max) aus Bearing ± Toleranz, korrekt über die Nordgrenze.

    Kreuzt das Band Nord (0/360°), wird min > max — das signalisiert dem
    Konsumenten den Wrap-around. Eine Toleranz >= 180° ergäbe einen Vollkreis;
    sie wird auf knapp unter 180° begrenzt, damit min != max bleibt.
    """
    tol = _clamp_tolerance(tolerance_deg)
    lo = _norm(bearing - tol)
    hi = _norm(bearing + tol)
    return round(lo, 4), round(hi, 4)


def compute_bearing_range(
    observer_lat: float,
    observer_lon: float,
    subject_lat: float,
    subject_lon: float,
    tolerance_deg: float = DEFAULT_TOLERANCE_DEG,
) -> Tuple[float, float]:
    """Basis-Idealbereich aus der reinen Sichtlinie Standort→Motiv.

    Deterministisch, ohne Netz. Gibt (ideal_azimuth_min, ideal_azimuth_max).
    """
    bearing = bearing_between(observer_lat, observer_lon, subject_lat, subject_lon)
    return _range_from_bearing(bearing, tolerance_deg)


def _footprint_angular_span(
    observer_lat: float,
    observer_lon: float,
    nodes: List[Tuple[float, float]],
) -> Optional[Tuple[float, float]]:
    """Horizontaler Winkelbereich (von links- bis rechtsaußen) eines Footprints.

    `nodes`: Liste von (lat, lon) der Gebäudeumriss-Punkte. Gibt (min, max) in
    Grad zurück (min > max bei Wrap über Nord) oder None bei zu wenig Punkten.

    Der Bereich wird über die zusammenhängende Bogen-Lücke bestimmt: die größte
    Lücke zwischen aufeinanderfolgenden Peilungen ist der „nicht abgedeckte"
    Sektor; das Komplement ist der vom Standort aus sichtbare Winkelbereich.
    """
    bearings = sorted(
        _norm(bearing_between(observer_lat, observer_lon, lat, lon))
        for lat, lon in nodes
    )
    if len(bearings) < 2:
        return None

    # Größte Lücke auf dem Kreis finden (inkl. Wrap von letztem zu erstem Punkt).
    max_gap = -1.0
    gap_start_idx = 0
    n = len(bearings)
    for i in range(n):
        nxt = bearings[(i + 1) % n]
        gap = (nxt - bearings[i]) % 360.0
        if gap > max_gap:
            max_gap = gap
            gap_start_idx = i

    # Der sichtbare Bereich ist das Komplement der größten Lücke:
    # von dem Punkt NACH der Lücke bis zum Punkt VOR der Lücke (= gap_start).
    visible_max = bearings[gap_start_idx]
    visible_min = bearings[(gap_start_idx + 1) % n]
    return round(visible_min, 4), round(visible_max, 4)


def _fetch_overpass_footprint(
    subject_lat: float,
    subject_lon: float,
    overpass_url: str = OVERPASS_URL,
    timeout_s: float = OVERPASS_TIMEOUT_S,
) -> Optional[List[Tuple[float, float]]]:
    """Holt die Umriss-Knoten des nächstgelegenen OSM-Gebäudes.

    Gibt eine Liste von (lat, lon) zurück oder None bei jedem Fehler/Timeout/
    fehlenden Daten — der Aufrufer fällt dann still auf die Bearing-Basis zurück.

    TASK-59 Option E: Schaut zuerst in der lokalen Batch-Cache-Datei nach
    (_find_local_cache_entry). Ein Treffer dort — auch mit leerer Gebäudeliste,
    was "im letzten Batch-Lauf bestätigt kein Gebäude in der Nähe" bedeutet —
    beendet die Funktion ohne Live-Netzanfrage. Nur bei einem Cache-Miss (z.B.
    neu angelegte oder seither koordinaten-korrigierte Location) läuft der
    bisherige Live-Mirror-Pfad unverändert weiter.
    """
    local_entry = _find_local_cache_entry(subject_lat, subject_lon)
    if local_entry is not None:
        return _nearest_building_nodes(subject_lat, subject_lon, local_entry.get("buildings") or [])

    query = (
        "[out:json][timeout:{t}];"
        "("
        'way(around:{r},{lat},{lon})["building"];'
        ");out geom;"
    ).format(
        t=int(timeout_s),
        r=OVERPASS_SEARCH_RADIUS_M,
        lat=subject_lat,
        lon=subject_lon,
    )
    payload = _fetch_from_mirrors(
        query, timeout_s,
        log_context="Overpass-Footprint ({},{})".format(subject_lat, subject_lon),
    )
    if payload is None:
        return None

    elements = payload.get("elements") or []
    # Nächstgelegenes Gebäude wählen: das mit dem Schwerpunkt am dichtesten
    # an der Motiv-Koordinate (Overpass liefert ggf. mehrere Treffer).
    best_nodes: Optional[List[Tuple[float, float]]] = None
    best_dist = float("inf")
    for el in elements:
        geom = el.get("geometry")
        if not geom or len(geom) < 3:
            continue
        nodes = [(g["lat"], g["lon"]) for g in geom if "lat" in g and "lon" in g]
        if len(nodes) < 3:
            continue
        c_lat = sum(n[0] for n in nodes) / len(nodes)
        c_lon = sum(n[1] for n in nodes) / len(nodes)
        d = (c_lat - subject_lat) ** 2 + (c_lon - subject_lon) ** 2
        if d < best_dist:
            best_dist = d
            best_nodes = nodes
    return best_nodes


def _stitch_way_segments_into_rings(
    segments: List[List[Tuple[float, float]]],
) -> Tuple[List[List[Tuple[float, float]]], List[List[Tuple[float, float]]]]:
    """US-135 Nachbesserung (2026-08-09, realer Fall 'Schloss Pfaueninsel –
    Rundtuerme', Beweisfall Standpunkt 52.429605/13.114616): Grosse,
    mehrteilige Wasserflaechen (Beispiel: relation 173239 'Havel') sind in
    OSM als Multipolygon-RELATION mit vielen einzelnen Member-Way-Segmenten
    gemappt -- KEIN einzelner Member-Way ist fuer sich genommen ein
    geschlossener Ring, erst ALLE Segmente zusammen (an gemeinsamen
    Endknoten aneinandergereiht) ergeben den durchgehenden See-Umriss. Ohne
    diese Zusammensetzung blieb "closed" fuer jedes Segment False und der
    Punkt-in-Polygon-Test in discover/accessibility.py._is_excluded() konnte
    fuer solche Flaechen strukturell nie greifen (nur der 15m-Kantenpuffer
    blieb wirksam, der bei einem Standpunkt hunderte Meter von jeder
    einzelnen Uferkante entfernt nichts bringt).

    Klassisches "Ways-zu-Ringen"-Problem bei OSM-Multipolygon-Relationen:
    Segmente werden an gemeinsamen Endpunkten (exakte Koordinatengleichheit
    -- Overpass liefert fuer denselben OSM-Knoten in "out geom" identische
    lat/lon-Werte je Member) verkettet, bis ein Ring sich schliesst (erster
    == letzter Knoten) oder kein passendes Segment mehr gefunden wird. Es
    kann mehrere unzusammenhaengende Ringe geben (z.B. mehrere getrennte
    Wasserflaechen oder -- Havel-Fall -- der Aussenring PLUS ein separater
    Innenring je Insel; die Rollenzuordnung outer/inner erfolgt beim
    Aufrufer, hier wird nur EINE Rollen-Gruppe auf einmal zusammengesetzt).

    Gibt (geschlossene_ringe, offene_restsegmente) zurueck. Offene
    Restsegmente entstehen z.B. bei einer unvollstaendigen Overpass-Antwort
    (fehlendes Member) -- sie werden vom Aufrufer weiterhin als offene
    water_ways-Eintraege gefuehrt, damit zumindest die bestehende
    Kanten-Distanz-Pruefung (SCOUT_ACCESS_WATER_LINE_BUFFER_M) fuer sie
    greift."""
    remaining: List[List[Tuple[float, float]]] = [
        list(seg) for seg in segments if len(seg) >= 2
    ]
    closed_rings: List[List[Tuple[float, float]]] = []
    leftover: List[List[Tuple[float, float]]] = []

    while remaining:
        ring = remaining.pop(0)
        progress = True
        while progress and ring[0] != ring[-1]:
            progress = False
            for idx, seg in enumerate(remaining):
                if seg[0] == ring[-1]:
                    ring = ring + seg[1:]
                    remaining.pop(idx)
                    progress = True
                    break
                if seg[-1] == ring[-1]:
                    ring = ring + list(reversed(seg))[1:]
                    remaining.pop(idx)
                    progress = True
                    break
                if seg[-1] == ring[0]:
                    ring = seg[:-1] + ring
                    remaining.pop(idx)
                    progress = True
                    break
                if seg[0] == ring[0]:
                    ring = list(reversed(seg))[:-1] + ring
                    remaining.pop(idx)
                    progress = True
                    break
        if len(ring) >= 4 and ring[0] == ring[-1]:
            closed_rings.append(ring)
        else:
            leftover.append(ring)

    return closed_rings, leftover


# US-09: Suchradius/Timeout für Gebäudeabfragen ENTLANG der ganzen Sichtlinie
# (nicht nur am Motiv wie bei TASK-45). Radius wird pro Aufruf anhand der
# tatsächlichen Standort-Motiv-Distanz gewählt (siehe fetch_buildings_along_line).
LINE_OVERPASS_TIMEOUT_S: float = 10.0
# Default-Höhe (m) für Gebäude ohne "height"/"building:levels"-Tag in OSM —
# konservative Annahme (2-3 Stockwerke), damit ein untaggtes Gebäude nicht
# fälschlich als 0m (= "kein Hindernis") gewertet wird.
DEFAULT_BUILDING_HEIGHT_M: float = 9.0
LEVEL_HEIGHT_M: float = 3.0  # m pro Stockwerk, wenn nur building:levels bekannt ist


def _building_height(tags: dict) -> float:
    """Schätzt die Gebäudehöhe aus OSM-Tags. Fällt auf DEFAULT_BUILDING_HEIGHT_M
    zurück, wenn weder "height" noch "building:levels" vorhanden/parsebar ist."""
    height_raw = tags.get("height")
    if height_raw:
        try:
            return float(str(height_raw).replace("m", "").strip())
        except (ValueError, TypeError):
            pass
    levels_raw = tags.get("building:levels")
    if levels_raw:
        try:
            return float(levels_raw) * LEVEL_HEIGHT_M
        except (ValueError, TypeError):
            pass
    return DEFAULT_BUILDING_HEIGHT_M


def fetch_buildings_along_line(
    observer_lat: float,
    observer_lon: float,
    subject_lat: float,
    subject_lon: float,
    overpass_url: str = OVERPASS_URL,
    timeout_s: float = LINE_OVERPASS_TIMEOUT_S,
) -> Optional[List[dict]]:
    """US-09: Holt alle OSM-Gebäude in der Bounding-Box zwischen Standort und
    Motiv (mit kleinem Rand), samt geschätzter Höhe.

    Gibt eine Liste von Dicts {"nodes": [(lat,lon),...], "height_m": float}
    zurück, oder None bei jedem Fehler/Timeout — der Aufrufer wertet das als
    "nicht geprüft", NIE als "frei" (Regel 4 der Spec).

    Wiederverwendet die Overpass-Query-Vorlage aus TASK-45
    (_fetch_overpass_footprint), aber mit Bounding-Box statt Radius-um-Punkt,
    da hier die gesamte Sichtlinie abgedeckt werden muss, nicht nur ein
    40m-Umkreis um das Motiv.

    TASK-59 Option E: Schaut zuerst in der lokalen Batch-Cache-Datei nach
    (_find_local_cache_entry, Abgleich über Standort- UND Motiv-Koordinate).
    Ein Treffer dort — auch mit leerer Gebäudeliste, was "im letzten
    Batch-Lauf bestätigt keine Gebäude in der Umgebung" bedeutet und laut
    evaluate_sightline() korrekt als "geprüft, frei" gilt (im Unterschied zu
    None = "nicht geprüft") — beendet die Funktion ohne Live-Netzanfrage. Nur
    bei einem Cache-Miss läuft der bisherige Live-Mirror-Pfad unverändert weiter.
    """
    local_entry = _find_local_cache_entry(subject_lat, subject_lon, observer_lat, observer_lon)
    if local_entry is not None:
        return [
            {
                "nodes": [(float(n[0]), float(n[1])) for n in (b.get("nodes") or [])],
                "height_m": b.get("height_m", DEFAULT_BUILDING_HEIGHT_M),
            }
            for b in (local_entry.get("buildings") or [])
        ]

    lat_min = min(observer_lat, subject_lat) - 0.001   # ~110m Rand
    lat_max = max(observer_lat, subject_lat) + 0.001
    lon_min = min(observer_lon, subject_lon) - 0.001
    lon_max = max(observer_lon, subject_lon) + 0.001

    query = (
        "[out:json][timeout:{t}];"
        "("
        'way["building"]({s},{w},{n},{e});'
        ");out geom;"
    ).format(
        t=int(timeout_s),
        s=lat_min, w=lon_min, n=lat_max, e=lon_max,
    )
    payload = _fetch_from_mirrors(
        query, timeout_s,
        log_context="Overpass-Linienabfrage ({},{})→({},{})".format(
            observer_lat, observer_lon, subject_lat, subject_lon
        ),
    )
    if payload is None:
        return None

    elements = payload.get("elements") or []
    buildings: List[dict] = []
    for el in elements:
        geom = el.get("geometry")
        if not geom or len(geom) < 3:
            continue
        nodes = [(g["lat"], g["lon"]) for g in geom if "lat" in g and "lon" in g]
        if len(nodes) < 3:
            continue
        tags = el.get("tags") or {}
        buildings.append({
            "nodes": nodes,
            "height_m": _building_height(tags),
        })
    return buildings


def compute_ideal_azimuth_range(
    observer_lat: float,
    observer_lon: float,
    subject_lat: Optional[float],
    subject_lon: Optional[float],
    tolerance_deg: float = DEFAULT_TOLERANCE_DEG,
    use_overpass: bool = False,
    overpass_url: str = OVERPASS_URL,
    overpass_timeout_s: float = OVERPASS_TIMEOUT_S,
) -> Optional[Tuple[float, float]]:
    """Idealen Azimut-Bereich (min, max) ableiten.

    - Fehlt die Motiv-Koordinate → None (kein Schreiben, kein Zufallswert).
    - Basis: Bearing ± Toleranz (deterministisch, ohne Netz).
    - use_overpass=True: versucht, den Bereich auf den Gebäude-Footprint zu
      verbreitern; jeder Fehler fällt still auf die Basis zurück.

    Gibt nie eine Exception nach außen.
    """
    if subject_lat is None or subject_lon is None:
        return None
    if observer_lat is None or observer_lon is None:
        return None

    base = compute_bearing_range(
        observer_lat, observer_lon, subject_lat, subject_lon, tolerance_deg
    )

    if not use_overpass:
        return base

    nodes = _fetch_overpass_footprint(
        subject_lat, subject_lon, overpass_url, overpass_timeout_s
    )
    if not nodes:
        return base

    span = _footprint_angular_span(observer_lat, observer_lon, nodes)
    if not span:
        return base

    # Footprint-Bereich um dieselbe Toleranz puffern, damit Auf-/Untergang am
    # Rand des Motivs noch erfasst wird. Liefert der Footprint einen engeren
    # Bereich als die Bearing-Basis, bleibt mindestens die Basis erhalten.
    span_min, span_max = span
    span_width = (span_max - span_min) % 360.0
    base_width = (base[1] - base[0]) % 360.0
    if span_width < base_width:
        return base
    pad = _clamp_tolerance(tolerance_deg)
    lo = _norm(span_min - pad)
    hi = _norm(span_max + pad)
    return round(lo, 4), round(hi, 4)


def update_location_azimuth(
    store,
    location_id: str,
    observer_lat: float,
    observer_lon: float,
    subject_lat: Optional[float],
    subject_lon: Optional[float],
    tolerance_deg: float = DEFAULT_TOLERANCE_DEG,
    use_overpass: bool = False,
) -> Optional[Tuple[float, float]]:
    """Berechnet den Idealbereich und schreibt ihn in die QA-Werte-Tabelle.

    Respektiert das azimuth_lock: ist es gesetzt, wird nichts geschrieben und
    der gesperrte Bestand bleibt unberührt.

    Rückgabe:
      - (min, max): geschriebener Bereich
      - None: nichts geschrieben (Lock gesetzt ODER keine Motiv-Koordinate ODER
        kein Bereich ableitbar). In keinem Fall fliegt eine Exception.
    """
    state = store.get_qa_state(location_id)
    if state and state.get("azimuth_lock"):
        logger.info("Azimut für %s gesperrt — kein Auto-Update", location_id)
        return None

    rng = compute_ideal_azimuth_range(
        observer_lat, observer_lon, subject_lat, subject_lon,
        tolerance_deg=tolerance_deg, use_overpass=use_overpass,
    )
    if rng is None:
        return None

    store.set_qa_values(
        location_id,
        ideal_azimuth_min=rng[0],
        ideal_azimuth_max=rng[1],
    )
    return rng


# ---------------------------------------------------------------------------
# US-135: Scout-Zugänglichkeits-/Sichtfreiheits-Live-Prüfung (kombinierte
# Overpass-Anfrage + eigener Tage-Cache, Implementierungsoption A)
# ---------------------------------------------------------------------------
# Anders als der Gebäude-Batch-Cache oben (BUILDING_CACHE_PATH) gibt es hier
# KEINEN GitHub-Actions-Commit-Schritt: Scout-Kandidatenkoordinaten sind
# tagesaktuell berechnete Standpunkte, kein fester Bestand aus
# data/locations.py, und stehen daher nicht im Repo. Der Cache unten ist
# reine lokale Laufzeit-Persistenz (JSON-Datei neben BUILDING_CACHE_PATH),
# mehrere Tage gültig (SCOUT_ACCESS_CACHE_TTL_DAYS).

# Suchradius (Meter) um den Scout-Standpunkt für die KOMBINIERTE
# Zugänglichkeits-Live-Anfrage (Wald/Wasser/Bahn/Weg). Größer als
# SCOUT_ACCESS_PATH_RADIUS_M gewählt, damit Wege bis zum vollen AK-Radius
# überhaupt mit abgefragt werden — der fachliche 50m-Schwellwert selbst wird
# danach in Software exakt geprüft (discover/accessibility.py); der
# Netz-Radius hier ist bewusst eine großzügigere Obermenge.
#
# US-135 Nachbesserung (2026-08-09, realer Fall "Schloss Pfaueninsel -
# Rundtuerme"): Overpass liefert bei einer relation[...](around:r,...)-
# Abfrage nur dann UEBERHAUPT Daten der Relation (z.B. der grossen
# Havel-Wasserflaeche, relation 173239), wenn MINDESTENS EIN Member-Knoten
# der Relation innerhalb von r Metern um den Standpunkt liegt -- danach wird
# zwar die GESAMTE Relation zurueckgegeben (inkl. weit entfernter Knoten),
# aber ohne diesen einen "Trigger-Knoten" in Reichweite kommt gar nichts.
# Bei 150m war das fuer real beobachtete Scout-Standpunkte 150-370m vom
# naechsten Wasser-Wegpunkt entfernt NICHT der Fall -- die Havel-Relation
# wurde nie mitgeliefert, wodurch der Ringschluss-Fix (siehe
# _stitch_way_segments_into_rings) fuer genau diese Punkte wirkungslos
# blieb (mangels Daten, nicht mangels Logik -- siehe US-135 Testprotokoll
# 2026-08-09). Auf 500m angehoben, mit Sicherheitsabstand ueber dem
# beobachteten Maximalfall, nach Ruecksprache mit Stephan (2026-08-09).
SCOUT_ACCESS_QUERY_RADIUS_M: int = 500

# Fachlicher AK-Schwellwert (US-135, von Stephan bestätigt 2026-08-07): ein
# öffentlich begehbarer Weg innerhalb dieses Radius um den Standpunkt gilt
# als "Weg in der Nähe" (Regel 2). NICHT identisch mit dem Cluster-Rastermaß
# in discover/accessibility.py (rein technische Lastreduktion, andere
# Konstante, andere Bedeutung).
SCOUT_ACCESS_PATH_RADIUS_M: float = 50.0

# Eigene, dokumentierte technische Näherungswerte (kein AK-Wortlaut) für
# "im Wasser"/"direkt neben Bahngleisen" bei linienförmigen OSM-Objekten
# (Fluss-/Gleismittellinie haben selbst keine Breite in den Rohdaten) —
# kleine Pufferzone um die Mittellinie.
SCOUT_ACCESS_WATER_LINE_BUFFER_M: float = 15.0
SCOUT_ACCESS_RAIL_BUFFER_M: float = 15.0

# US-135 Live-Bug (2026-08-08, Stephans Server-Log server_log_us135.txt.txt):
# 405 von 938 (43%) im Live-Volllauf ausgeblendeten Kandidaten waren NICHT
# wirklich unzugaenglich, sondern nur "nicht pruefbar", weil die kombinierte
# Anfrage (Gebaeude+Wald+Wasser+Bahn+Weg in EINER Query, deutlich mehr Daten
# als die reine Gebaeude-Query mit LINE_OVERPASS_TIMEOUT_S=10.0) bei 10s
# Timeout regelmaessig auf BEIDEN Mirrors mit echtem Read-Timeout gescheitert
# ist (Log-Muster: erster Mirror 504/429, zweiter Mirror "The read operation
# timed out"). Beleg fuer die Datenmenge: Stichprobe aus dem bereits gefuellten
# SCOUT_ACCESS_CACHE_PATH (247 echte Live-Antworten) zeigt Median ~28KB, aber
# p90 ~736KB und Maximum ~1,7MB pro Antwort (grosse Waldflaechen wie
# Grunewald/Tegeler Forst liefern sehr knotenreiche Polygone) -- 10s reichen
# dafuer auf einem ausgelasteten oeffentlichen Mirror oft nicht. 25s ist mehr
# als das Doppelte des bisherigen Werts (grosszuegiger Puffer fuer die groesste
# beobachtete Antwortgroesse), aber bewusst nicht beliebig hoch, damit ein
# einzelner haengender Mirror-Versuch den Cluster-Lauf nicht unnoetig blockiert
# (mit fetch_scout_accessibility_data() jetzt zusaetzlich per asyncio.to_thread
# aus dem Event-Loop ausgelagert, siehe discover/pipeline.py).
SCOUT_ACCESS_TIMEOUT_S: float = 25.0

# Aktive Bahn-/Wegtypen (OSM-Tag-Werte). Bewusst NUR aktiv genutzte Gleise
# (US-135-Annahme, von Stephan bestätigt): reguläre railway=rail/tram/
# light_rail/subway/narrow_gauge/monorail/funicular OHNE disused=yes-Tag.
# Stillgelegte Strecken mit dem OSM-Lifecycle-Präfix disused:railway=*
# tragen gar keinen railway=*-Tag (sondern disused:railway=*) und matchen
# den ["railway"~...]-Filter unten deshalb bereits von selbst nicht — kein
# zusätzlicher Negativfilter dafür nötig, nur das separate disused=yes-
# Sekundär-Tag wird zusätzlich explizit ausgeschlossen.
_SCOUT_ACCESS_RAIL_VALUES: str = "rail|tram|light_rail|subway|narrow_gauge|monorail|funicular"
_SCOUT_ACCESS_PATH_VALUES: str = "footway|path|track|pedestrian|steps|bridleway|cycleway|living_street"

SCOUT_ACCESS_CACHE_PATH: Path = Path(__file__).resolve().parent / "cache" / "scout_accessibility_cache.json"

# Gröbere Koordinatentoleranz als BUILDING_CACHE_COORD_TOLERANCE_DEG
# (1e-5°, ~1m) — passend zum Cluster-Raster aus discover/accessibility.py
# (ACCESSIBILITY_CLUSTER_SIZE_M = 80m): 5e-4° ≈ 55m an der Berlin-Breite,
# deckt damit denselben oder einen direkt benachbarten Cluster ab.
SCOUT_ACCESS_CACHE_COORD_TOLERANCE_DEG: float = 5e-4

# Kein bestehender Cache-TTL-Präzedenzfall im Code gefunden (BUILDING_CACHE
# hat keine TTL, nur wöchentliche GitHub-Actions-Neuerzeugung). Eigener,
# explizit benannter Wert: an TASK-59s wöchentlichem Batch-Rhythmus
# orientiert, damit Standpunkte, die über mehrere Tage wiederkehren
# (US-135-Pre-Mortem: _trigger_discover_debounced() bei jeder
# Location-Bearbeitung), den Live-Call nicht jedes Mal neu auslösen.
SCOUT_ACCESS_CACHE_TTL_DAYS: float = 7.0

# BUG-103: analog zu precompute.py ALGORITHM_VERSION (dort Zeile ~60,
# produktiv bewährt seit BUG-93) — Bump NUR bei Änderungen an der Rohdaten-
# Erzeugung für einen Standpunkt (fetch_scout_accessibility_data(), z.B. dem
# US-135-Ringschluss-Fix vom 09.08.2026), NICHT bei reinen Änderungen an der
# nachgelagerten Filterlogik (is_sightline_blocked_by_*() werten die
# gespeicherten Rohdaten bei jedem Aufruf ohnehin frisch aus, siehe BUG-103
# Architektur-Analyse). Ohne dieses Feld blieb ein bereits vor einem
# Logik-Fix gecachter Eintrag bis zu SCOUT_ACCESS_CACHE_TTL_DAYS unverändert
# gültig — selbst ein Server-Neustart half nicht, weil der Cache erst beim
# ersten tatsächlichen Zugriff danach unverändert von Platte gelesen wird
# (Root Cause, realer Fall Pfaueninsel 08./09.08.2026).
SCOUT_ACCESS_CACHE_VERSION: str = "1.0"

_scout_access_cache_lock = threading.Lock()
_scout_access_cache_entries: Optional[List[dict]] = None


def _load_scout_access_cache() -> List[dict]:
    """Lädt (einmalig, thread-sicher, gecached für die Prozesslaufzeit) den
    lokalen US-135-Zugänglichkeits-Cache. Fehlt/ist fehlerhaft die Datei,
    verhält sich das wie ein leerer Cache (kein Crash, jede Anfrage fällt
    auf den Live-Pfad zurück)."""
    global _scout_access_cache_entries
    if _scout_access_cache_entries is not None:
        return _scout_access_cache_entries
    with _scout_access_cache_lock:
        if _scout_access_cache_entries is not None:
            return _scout_access_cache_entries
        try:
            raw = json.loads(SCOUT_ACCESS_CACHE_PATH.read_text(encoding="utf-8"))
            entries = raw.get("entries") or []
        except FileNotFoundError:
            entries = []
        except (OSError, ValueError, AttributeError) as e:
            logger.warning(
                "US-135 Zugänglichkeits-Cache %s nicht lesbar (%s) — "
                "startet mit leerem Cache", SCOUT_ACCESS_CACHE_PATH, e,
            )
            entries = []
        _scout_access_cache_entries = entries
        return _scout_access_cache_entries


def _save_scout_access_cache() -> None:
    """Schreibt den aktuellen In-Memory-Cache auf Disk. Anders als
    BUILDING_CACHE_PATH KEIN GitHub-Actions-Commit-Schritt — Scout-
    Kandidaten stehen nicht im Repo, dies ist reine lokale
    Laufzeit-Persistenz. Schreibfehler werden geloggt, aber nie nach außen
    geworfen (Cache ist eine Optimierung, kein Korrektheits-Erfordernis)."""
    try:
        SCOUT_ACCESS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {"entries": _scout_access_cache_entries or []}
        SCOUT_ACCESS_CACHE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8",
        )
    except OSError as e:
        logger.warning("US-135 Zugänglichkeits-Cache %s nicht schreibbar (%s)",
                        SCOUT_ACCESS_CACHE_PATH, e)


def _scout_access_coords_match(
    entry: dict,
    observer_lat: float, observer_lon: float,
    subject_lat: float, subject_lon: float,
) -> bool:
    """BUG-103: gemeinsame Koordinaten-Toleranzprüfung für Lese-
    (_find_scout_access_cache_entry, inkl. TTL/Versionsprüfung) und
    Schreibpfad (get_scout_accessibility_data: alten Eintrag für dieselbe
    Koordinate ersetzen statt anhängen) — vermeidet doppelte Toleranz-Logik.
    Bewusst OHNE TTL-/Versionsprüfung: beim Ersetzen soll JEDER, auch ein
    bereits abgelaufener oder versions-veralteter Alteintrag für dieselbe
    Koordinate entfernt werden (BUG-103 AK4)."""
    tol = SCOUT_ACCESS_CACHE_COORD_TOLERANCE_DEG
    if abs((entry.get("observer_lat") or 0.0) - observer_lat) >= tol:
        return False
    if abs((entry.get("observer_lon") or 0.0) - observer_lon) >= tol:
        return False
    if abs((entry.get("subject_lat") or 0.0) - subject_lat) >= tol:
        return False
    if abs((entry.get("subject_lon") or 0.0) - subject_lon) >= tol:
        return False
    return True


def _find_scout_access_cache_entry(
    observer_lat: float, observer_lon: float,
    subject_lat: float, subject_lon: float,
) -> Optional[dict]:
    """Sucht einen noch gültigen (TTL, SCOUT_ACCESS_CACHE_TTL_DAYS; BUG-103:
    UND passender SCOUT_ACCESS_CACHE_VERSION) Treffer innerhalb der groben
    Cluster-Koordinatentoleranz. Kein Treffer -> None, der Aufrufer holt die
    Daten dann live."""
    now = datetime.now(timezone.utc)
    for entry in _load_scout_access_cache():
        if not _scout_access_coords_match(
            entry, observer_lat, observer_lon, subject_lat, subject_lon,
        ):
            continue
        # BUG-103: ein Eintrag aus einer älteren Berechnungslogik-Version
        # (oder ganz ohne Versionsfeld — alle vor diesem Fix gespeicherten
        # Bestandseinträge, AK5) gilt wie ein Cache-Miss, unabhängig von der
        # TTL. Lazy-Check hier beim Lesen, bewusst KEINE Eager-Validierung
        # aller Einträge beim Serverstart (Performance bei ~1,8 GB Cache-
        # Datei, siehe BUG-103 Code-Verifikation).
        if entry.get("algorithm_version") != SCOUT_ACCESS_CACHE_VERSION:
            logger.info(
                "US-135 Zugänglichkeits-Cache-Eintrag verworfen (Versions-"
                "Mismatch: gespeichert=%s, aktuell=%s) für Standpunkt "
                "(%s,%s) / Motiv (%s,%s) — wird live neu geprüft",
                entry.get("algorithm_version"), SCOUT_ACCESS_CACHE_VERSION,
                observer_lat, observer_lon, subject_lat, subject_lon,
            )
            continue
        try:
            cached_at = datetime.fromisoformat(entry.get("cached_at"))
        except (TypeError, ValueError):
            continue
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)
        if (now - cached_at).total_seconds() > SCOUT_ACCESS_CACHE_TTL_DAYS * 86400.0:
            continue
        return entry
    return None


def fetch_scout_accessibility_data(
    observer_lat: float,
    observer_lon: float,
    subject_lat: float,
    subject_lon: float,
    radius_m: float = SCOUT_ACCESS_QUERY_RADIUS_M,
    timeout_s: float = SCOUT_ACCESS_TIMEOUT_S,
) -> Optional[dict]:
    """US-135: EINE kombinierte Live-Overpass-Anfrage für Gebäude (Sichtlinie,
    Bounding-Box Standpunkt<->Motiv, analog fetch_buildings_along_line) UND
    Wald/Wasser/Bahn/Weg (Umkreis um den Standpunkt) — Implementierungs-
    option A statt zwei getrennter Anfragen. Nutzt _fetch_from_mirrors und
    damit denselben geteilten Rate-Limit-Tracker/Mirror-Fallback wie alle
    bestehenden QA-Overpass-Abfragen in diesem Modul.

    Gibt None zurück, wenn ALLE Mirrors fehlschlagen — der Aufrufer
    (discover/accessibility.py, über get_scout_accessibility_data)
    behandelt das als "Prüfung nicht durchführbar" (US-135 Regel 3: im
    Zweifel ausblenden, nie als "frei"/"zugänglich" werten)."""
    lat_min = min(observer_lat, subject_lat) - 0.001
    lat_max = max(observer_lat, subject_lat) + 0.001
    lon_min = min(observer_lon, subject_lon) - 0.001
    lon_max = max(observer_lon, subject_lon) + 0.001

    query = (
        "[out:json][timeout:{t}];"
        "("
        'way["building"]({s},{w},{n},{e});'
        'way["landuse"="forest"](around:{r},{olat},{olon});'
        'way["natural"="wood"](around:{r},{olat},{olon});'
        # US-135 Nachbesserung (2026-08-08, realer Fall "Einsteinturm"):
        # grosse Waldflaechen sind in OSM haeufig als Multipolygon-RELATION
        # gemappt, nicht als einzelner way (Beleg: relation 12981504,
        # landuse=forest, Telegrafenberg-Forst bei Potsdam). Die vorherige
        # way-only-Abfrage fand solche Flaechen nie -- ein Scout-Standpunkt
        # mitten in genau diesem Wald blieb faelschlich als "zugaenglich"
        # im Feed sichtbar (AK3-Verletzung). Ergaenzt um die passenden
        # relation[...]-Klauseln, Parsing der Member-Geometrie unten.
        'relation["landuse"="forest"](around:{r},{olat},{olon});'
        'relation["natural"="wood"](around:{r},{olat},{olon});'
        'way["natural"="water"](around:{r},{olat},{olon});'
        'way["waterway"](around:{r},{olat},{olon});'
        # US-135 Nachbesserung (2026-08-08, realer Fall "Schloss Pfaueninsel
        # - Rundtuerme"): Grosse Seen sind in OSM ebenfalls haeufig als
        # Multipolygon-RELATION gemappt (Beleg: relation 173239, "Havel",
        # natural=water, EIN outer-Ring + ZWEI inner-Ringe fuer die Inseln
        # inkl. Pfaueninsel selbst). Die separate way["natural"="water"]-
        # Antwort oben deckt nur ein kleineres Teilstueck ab, nicht den
        # tatsaechlichen relevanten See-Umriss -- ein per Dreiecksberechnung
        # erzeugter Standpunkt lag dadurch nachweislich INNERHALB des realen
        # Havel-Umrisses (per Punkt-in-Polygon-Test gegen die Relation
        # bestaetigt), blieb aber faelschlich als "zugaenglich" sichtbar
        # (AK4-Verletzung).
        'relation["natural"="water"](around:{r},{olat},{olon});'
        'relation["waterway"](around:{r},{olat},{olon});'
        'way["railway"~"^({rail})$"]["disused"!~"yes"](around:{r},{olat},{olon});'
        'way["highway"~"^({path})$"](around:{r},{olat},{olon});'
        ");out geom;"
    ).format(
        t=int(timeout_s),
        s=lat_min, w=lon_min, n=lat_max, e=lon_max,
        r=int(radius_m), olat=observer_lat, olon=observer_lon,
        rail=_SCOUT_ACCESS_RAIL_VALUES, path=_SCOUT_ACCESS_PATH_VALUES,
    )
    payload = _fetch_from_mirrors(
        query, timeout_s,
        log_context="US-135 Scout-Zugänglichkeit ({},{})".format(observer_lat, observer_lon),
    )
    if payload is None:
        return None

    buildings: List[dict] = []
    forest_ways: List[dict] = []
    water_ways: List[dict] = []
    rail_ways: List[dict] = []
    path_ways: List[dict] = []

    for el in payload.get("elements") or []:
        tags = el.get("tags") or {}

        # US-135 Nachbesserung (2026-08-08): Multipolygon-Relationen (grosse
        # Waelder UND grosse Seen, siehe Kommentare an den relation[...]-
        # Query-Klauseln oben) haben KEINE eigene "geometry" auf oberster
        # Ebene (anders als ways) -- die Geometrie steckt pro Member-Way in
        # "members"[i]["geometry"]. Jeder Member-Way mit eigener Geometrie
        # wird wie ein eigenstaendiger forest_way/water_way behandelt; fuer
        # den hier verwendeten simplen Punkt-in-Polygon-/Kanten-Distanz-Test
        # reicht das aus. Auch role="inner" wird bewusst mitgezaehlt (z.B.
        # Waldlichtungen oder -- Havel-Fall -- Insel-Umrisse INNERHALB eines
        # Sees): das macht den Filter im Zweifel konservativer (schliesst im
        # Grenzfall eher eine Lichtung/Insel mit aus), nie unsicherer --
        # passend zum bestehenden "im Zweifel ausblenden"-Prinzip (Regel 3).
        # Ein Member-Way wird nur als "closed" markiert, wenn sein eigener
        # erster und letzter Knoten uebereinstimmen (ein aus mehreren
        # Member-Ways zusammengesetzter Ring kann das einzeln nicht
        # garantieren) -- die Kanten-Distanz-Pruefung greift trotzdem, auch
        # wenn "closed" False bleibt.
        if el.get("type") == "relation":
            is_forest_rel = tags.get("landuse") == "forest" or tags.get("natural") == "wood"
            is_water_rel = tags.get("natural") == "water" or "waterway" in tags
            if is_forest_rel or is_water_rel:
                # US-135 Nachbesserung (2026-08-09, Havel/Pfaueninsel-Fall):
                # Water-Member werden NICHT mehr einzeln als eigene
                # water_ways-Eintraege durchgereicht -- sie werden zuerst je
                # Rolle (outer/inner) gesammelt und danach ueber
                # _stitch_way_segments_into_rings() zu durchgehenden,
                # geschlossenen Ringen zusammengesetzt (siehe Docstring dort).
                # Wald-Member bleiben unveraendert einzeln (bestehendes,
                # bewusst konservatives Verhalten: jedes Member zaehlt fuer
                # sich als moeglicher Wald-Ausschlussgrund, siehe Kommentar
                # unten "role='inner' wird bewusst mitgezaehlt").
                water_segments_by_role: dict = {}
                for member in el.get("members") or []:
                    m_geom = member.get("geometry")
                    if not m_geom:
                        continue
                    m_nodes = [(g["lat"], g["lon"]) for g in m_geom if "lat" in g and "lon" in g]
                    if len(m_nodes) < 2:
                        continue
                    if is_forest_rel and len(m_nodes) >= 3:
                        forest_ways.append({"nodes": m_nodes})
                    if is_water_rel:
                        role = member.get("role") or "outer"
                        water_segments_by_role.setdefault(role, []).append(m_nodes)

                if is_water_rel:
                    rel_id = el.get("id")
                    for role, segs in water_segments_by_role.items():
                        closed_rings, leftover = _stitch_way_segments_into_rings(segs)
                        for ring in closed_rings:
                            water_ways.append({
                                "nodes": ring,
                                "closed": True,
                                "relation_id": rel_id,
                                "role": role,
                            })
                        for seg in leftover:
                            water_ways.append({
                                "nodes": seg,
                                "closed": len(seg) >= 3 and seg[0] == seg[-1],
                                "relation_id": rel_id,
                                "role": role,
                            })
            continue

        geom = el.get("geometry")
        if not geom:
            continue
        nodes = [(g["lat"], g["lon"]) for g in geom if "lat" in g and "lon" in g]
        if len(nodes) < 2:
            continue

        if "building" in tags:
            if len(nodes) >= 3:
                buildings.append({"nodes": nodes, "height_m": _building_height(tags)})
            continue
        if tags.get("landuse") == "forest" or tags.get("natural") == "wood":
            if len(nodes) >= 3:
                forest_ways.append({"nodes": nodes})
            continue
        if tags.get("natural") == "water" or "waterway" in tags:
            water_ways.append({
                "nodes": nodes,
                "closed": len(nodes) >= 3 and nodes[0] == nodes[-1],
            })
            continue
        if tags.get("railway"):
            rail_ways.append({"nodes": nodes})
            continue
        if tags.get("highway"):
            path_ways.append({"nodes": nodes})
            continue

    return {
        "buildings": buildings,
        "forest_ways": forest_ways,
        "water_ways": water_ways,
        "rail_ways": rail_ways,
        "path_ways": path_ways,
    }


def get_scout_accessibility_data(
    observer_lat: float,
    observer_lon: float,
    subject_lat: float,
    subject_lon: float,
) -> Optional[dict]:
    """US-135: Öffentliche Cache+Live-Funktion für einen Scout-Standpunkt.

    Schaut zuerst im lokalen Tage-Cache nach (SCOUT_ACCESS_CACHE_TTL_DAYS
    gültig, grobe Cluster-Toleranz), sonst genau EINE kombinierte
    Live-Overpass-Anfrage (fetch_scout_accessibility_data) über den
    geteilten Rate-Limit-Tracker. Ergebnis wird bei Erfolg im Cache
    gespeichert; ein Fehlschlag (None) wird NICHT gecacht, damit ein
    späterer Aufruf mit wieder erreichbarem Overpass nicht dauerhaft
    blockiert bleibt.

    Rückgabe: dict mit buildings/forest_ways/water_ways/rail_ways/
    path_ways, oder None wenn die Prüfung nicht durchführbar war
    (Timeout/Fehler) — der Aufrufer behandelt das als "nicht bestätigt"
    (US-135 Regel 3)."""
    cached = _find_scout_access_cache_entry(observer_lat, observer_lon, subject_lat, subject_lon)
    if cached is not None:
        return cached.get("data")

    data = fetch_scout_accessibility_data(observer_lat, observer_lon, subject_lat, subject_lon)
    if data is None:
        return None

    entry = {
        "observer_lat": observer_lat,
        "observer_lon": observer_lon,
        "subject_lat": subject_lat,
        "subject_lon": subject_lon,
        "cached_at": datetime.now(timezone.utc).isoformat(),
        # BUG-103: markiert, mit welchem Berechnungslogik-Stand dieser
        # Eintrag erzeugt wurde — geprüft von _find_scout_access_cache_entry.
        "algorithm_version": SCOUT_ACCESS_CACHE_VERSION,
        "data": data,
    }
    global _scout_access_cache_entries
    with _scout_access_cache_lock:
        if _scout_access_cache_entries is None:
            _scout_access_cache_entries = []
        # BUG-103 AK4: einen etwaigen alten Eintrag für dieselbe Koordinate
        # (unabhängig von dessen TTL/Version) ERSETZEN statt zusätzlich
        # anhängen — behebt neben der Stale-Cache-Ursache auch das
        # unbegrenzte Wachstum der Cache-Datei (Root Cause: ≈1,8 GB bei nur
        # ≈2000 Einträgen, weil bisher jeder Miss nur angehängt wurde).
        # Innerhalb desselben bestehenden _scout_access_cache_lock wie das
        # bisherige Anhängen, kein neuer Race zwischen Lesen und Schreiben.
        _scout_access_cache_entries = [
            e for e in _scout_access_cache_entries
            if not _scout_access_coords_match(
                e, observer_lat, observer_lon, subject_lat, subject_lon,
            )
        ]
        _scout_access_cache_entries.append(entry)
        _save_scout_access_cache()
    return data


def is_sightline_blocked_by_buildings(
    observer_lat: float,
    observer_lon: float,
    subject_lat: float,
    subject_lon: float,
    buildings: List[dict],
) -> bool:
    """US-135 Regel 1: grobe 2D-Sichtlinien-Blockprüfung ohne Geländehöhen-
    profil — bewusst einfacher als der vollständige Sichtachsen-Check aus
    US-09 (calculations/sightline.py), passend zum in der US-135-Analyse
    festgelegten "groben Ausschlussfilter, keine vollständige geometrische
    Sichtachsenberechnung". True, wenn mindestens ein Gebäude zwischen
    Standpunkt und Motiv liegt UND sein horizontaler Winkelbereich (vom
    Standpunkt aus gesehen, wiederverwendet _footprint_angular_span) die
    Peilung zum Motiv vollständig überdeckt."""
    subject_bearing = _norm(bearing_between(observer_lat, observer_lon, subject_lat, subject_lon))
    subject_dist = _scout_access_haversine_m(observer_lat, observer_lon, subject_lat, subject_lon)

    for b in buildings:
        nodes = b.get("nodes") or []
        if len(nodes) < 3:
            continue
        c_lat = sum(n[0] for n in nodes) / len(nodes)
        c_lon = sum(n[1] for n in nodes) / len(nodes)
        dist_to_building = _scout_access_haversine_m(observer_lat, observer_lon, c_lat, c_lon)
        if dist_to_building <= 0 or dist_to_building >= subject_dist:
            continue  # nicht zwischen Standpunkt und Motiv
        span = _footprint_angular_span(observer_lat, observer_lon, nodes)
        if not span:
            continue
        span_min, span_max = span
        width = (span_max - span_min) % 360.0
        offset = (subject_bearing - span_min) % 360.0
        if offset <= width:
            return True
    return False


def is_sightline_blocked_by_vegetation(
    observer_lat: float,
    observer_lon: float,
    subject_lat: float,
    subject_lon: float,
    forest_ways: List[dict],
) -> bool:
    """BUG-101: grobe 2D-Sichtlinien-Blockprüfung durch Wald/Bäume, analog zu
    is_sightline_blocked_by_buildings() — verwendet dieselbe grobe
    Winkelbereichs-Logik (_footprint_angular_span) auf den bereits geladenen
    forest_ways (US-135 fetch_scout_accessibility_data/get_scout_
    accessibility_data), ohne zusätzliche Overpass-Anfrage (BUG-101 AK7).

    Unterschied zu is_sightline_blocked_by_buildings(): dort wird eine
    Distanz von 0 zum Flächenschwerpunkt übersprungen (Gebäude, in denen ein
    Standpunkt liegt, kommen praktisch nicht vor). Bei Wald ist das der
    Regelfall — US-135 Regel 2 kennt den Standpunkt "mitten im Wald" bereits
    für die Zugänglichkeitsprüfung, und BUG-101 AK1 verlangt genau diesen
    Fall auch für die Sichtprüfung ("Standpunkt liegt innerhalb eines
    Wald-Polygons, dessen Winkelbereich die Peilung zum Motiv abdeckt").
    Deshalb wird hier NUR auf "Waldfläche liegt nicht zwischen Standpunkt und
    Motiv" geprüft (dist_to_forest >= subject_dist), nicht zusätzlich auf
    dist_to_forest <= 0.

    True, wenn mindestens eine Waldfläche zwischen Standpunkt und Motiv
    liegt (oder der Standpunkt selbst darin bzw. an ihrem Flächenschwerpunkt
    liegt) UND ihr horizontaler Winkelbereich vom Standpunkt aus gesehen die
    Peilung zum Motiv vollständig überdeckt."""
    subject_bearing = _norm(bearing_between(observer_lat, observer_lon, subject_lat, subject_lon))
    subject_dist = _scout_access_haversine_m(observer_lat, observer_lon, subject_lat, subject_lon)

    for f in forest_ways:
        nodes = f.get("nodes") or []
        if len(nodes) < 3:
            continue
        c_lat = sum(n[0] for n in nodes) / len(nodes)
        c_lon = sum(n[1] for n in nodes) / len(nodes)
        dist_to_forest = _scout_access_haversine_m(observer_lat, observer_lon, c_lat, c_lon)
        if dist_to_forest >= subject_dist:
            continue  # nicht zwischen Standpunkt und Motiv
        span = _footprint_angular_span(observer_lat, observer_lon, nodes)
        if not span:
            continue
        span_min, span_max = span
        width = (span_max - span_min) % 360.0
        offset = (subject_bearing - span_min) % 360.0
        if offset <= width:
            return True
    return False


def _scout_access_haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Lokale Haversine-Distanz (Meter) — eigene kleine Kopie statt Import
    aus discover/pipeline_base.py, um das bestehende Modul-Layering zu
    wahren (data/ importiert bereits discover.geometry für Bearings, aber
    keine Pipeline-Bausteine)."""
    R = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))
