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

import logging
import threading
import time
from typing import List, Optional, Tuple

from discover.geometry import bearing_between

logger = logging.getLogger(__name__)

# Default-Toleranz: Halbe Bandbreite um die Sichtlinie (Grad).
# ±15° ist die konventionelle Vorgabe aus der TASK-45-Spec.
DEFAULT_TOLERANCE_DEG: float = 15.0

# Overpass: öffentlicher Endpoint + kurzes Timeout, damit ein langsamer/down
# Server den QA-Lauf nicht hängen lässt (Pre-Mortem-Gegenmaßnahme).
OVERPASS_URL: str = "https://overpass.kumi.systems/api/interpreter"
# Mirror-Liste für Fallback bei Serverblockade/-ausfall: Kumi zuerst (aktuell
# bestätigt funktionierend), overpass-api.de als Fallback falls Kumi down ist.
OVERPASS_MIRRORS: List[str] = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
OVERPASS_TIMEOUT_S: float = 8.0
# Suchradius um die Motiv-Koordinate für den Gebäude-Footprint (Meter).
OVERPASS_SEARCH_RADIUS_M: int = 40

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
    """Versucht die gegebene Overpass-Query nacheinander gegen jeden Eintrag in
    OVERPASS_MIRRORS (je EIN Versuch pro Mirror, kein Retry auf demselben
    Mirror). Vor JEDEM Versuch wird _respect_overpass_rate_limit() aufgerufen —
    beide Mirrors sind kostenlose Community-Server und werden gleich behandelt.

    Gibt das geparste JSON-Payload des ersten erfolgreichen Mirrors zurück,
    oder None, wenn alle Mirrors fehlschlagen (der Aufrufer loggt dann und
    fällt still auf die Bearing-Basis zurück)."""
    import httpx  # lokaler Import: QA ohne Overpass braucht httpx nie

    last_error: Optional[Exception] = None
    for mirror_url in OVERPASS_MIRRORS:
        _respect_overpass_rate_limit()
        try:
            with httpx.Client(timeout=timeout_s) as client:
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
    """
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
    """
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
