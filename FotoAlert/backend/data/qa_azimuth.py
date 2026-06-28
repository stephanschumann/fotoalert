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
from typing import List, Optional, Tuple

from discover.geometry import bearing_between

logger = logging.getLogger(__name__)

# Default-Toleranz: Halbe Bandbreite um die Sichtlinie (Grad).
# ±15° ist die konventionelle Vorgabe aus der TASK-45-Spec.
DEFAULT_TOLERANCE_DEG: float = 15.0

# Overpass: öffentlicher Endpoint + kurzes Timeout, damit ein langsamer/down
# Server den QA-Lauf nicht hängen lässt (Pre-Mortem-Gegenmaßnahme).
OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT_S: float = 8.0
# Suchradius um die Motiv-Koordinate für den Gebäude-Footprint (Meter).
OVERPASS_SEARCH_RADIUS_M: int = 40

# Obergrenze für die Toleranz: knapp unter 180°, damit ein gepuffertes Band nie
# zum Vollkreis (min == max) entartet.
MAX_TOLERANCE_DEG: float = 179.999


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
    try:
        import httpx  # lokaler Import: QA ohne Overpass braucht httpx nie

        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(overpass_url, data={"data": query})
            resp.raise_for_status()
            payload = resp.json()
    except Exception as e:  # noqa: BLE001 — bewusst: jeder Fehler → Fallback
        logger.info("Overpass-Footprint (%s,%s) nicht abrufbar: %s",
                    subject_lat, subject_lon, e)
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
