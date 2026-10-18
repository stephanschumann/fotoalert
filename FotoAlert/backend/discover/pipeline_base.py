"""
Gemeinsame Bausteine für alle Scout-Pipelines.

Jede körper-spezifische Pipeline (moon_pipeline, sun_pipeline, …) importiert
von hier: ScoutOpportunity, Score-Gewichte, Geometrie-Helfer, Wetter-Cache.
"""
from __future__ import annotations

import logging
import math
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from calculations.ortszeit import is_england
from calculations.weather import WeatherForecast, calculate_photo_weather_score, fetch_weather_forecast
from discover.subjects import EXCLUSION_ZONES

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

D_MIN_M = 100.0               # Mindestdistanz Standpunkt–Motiv
D_MAX_M = 13_000.0            # Maximaldistanz
SAMPLE_INTERVAL_MIN = 15      # Minuten zwischen Samplings

# Scout-Exklusion: berechneter Standpunkt muss mindestens diesen Abstand
# zu allen bekannten Fotografen-Standorten desselben Motivs haben.
SCOUT_MIN_NEW_DISTANCE_M = 150.0

# Score-Gewichte — gleich für alle Körper in v1
W_ALIGNMENT   = 0.35
W_PHASE       = 0.15
W_LICHT       = 0.15
W_KOMPOSITION = 0.20
W_WETTER      = 0.15


# ---------------------------------------------------------------------------
# Datenmodell
# ---------------------------------------------------------------------------

@dataclass
class ScoutOpportunity:
    body_name: str                          # "moon" | "sun"
    subject_id: str
    subject_name: str
    subject_lat: float
    subject_lon: float
    day: str                                # ISO date, z.B. "2026-06-20"
    session: str                            # "golden_morning" | "blue_morning" | …
    dt_utc: str                             # ISO datetime UTC des besten Moments
    body_azimuth_deg: float                 # Azimut des Körpers vom Motiv aus
    body_altitude_deg: float                # Höhe des Körpers über Horizont
    body_illumination_pct: Optional[float]  # None für Sonne (immer voll beleuchtet)
    distance_m: float                       # Standpunkt–Motiv-Distanz
    standpoint_lat: float
    standpoint_lon: float
    focal_length_equiv_mm: float            # geschätzte Brennweite (KB-Äquivalent)
    score: float                            # 0–1 Gesamt-Score
    score_alignment: float
    score_phase: float
    score_licht: float
    score_komposition: float
    score_wetter: float
    weather_description: str


# ---------------------------------------------------------------------------
# Geometrie & Filterung
# ---------------------------------------------------------------------------

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Entfernung in Metern zwischen zwei GPS-Punkten."""
    R = 6_371_000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def is_new_perspective(sp_lat: float, sp_lon: float, subject_id: str) -> bool:
    """True wenn der Scout-Standpunkt ≥ SCOUT_MIN_NEW_DISTANCE_M von allen
    bekannten Fotografen-Standorten dieses Motivs entfernt ist."""
    known = EXCLUSION_ZONES.get(subject_id, [])
    for obs_lat, obs_lon in known:
        if haversine_m(sp_lat, sp_lon, obs_lat, obs_lon) < SCOUT_MIN_NEW_DISTANCE_M:
            return False
    return True


def sample_window(start: Optional[datetime], end: Optional[datetime]) -> list[datetime]:
    """Alle 15-Minuten-Zeitpunkte innerhalb eines Lichtfensters."""
    if start is None or end is None or end <= start:
        return []
    result = []
    t = start
    while t <= end:
        result.append(t)
        t += timedelta(minutes=SAMPLE_INTERVAL_MIN)
    return result


# US-138 (Schritt 3): Bezugspunkt fuer die Lichtfenster (Blaue/Goldene Stunde).
# Bisher fest Berlin fuer alle Motive; in England liegen die Sonnenzeiten (UTC) bis zu
# rund 54 min daneben. Annahme: England-Motive (Regel aus calculations/ortszeit.py) nutzen
# ihre eigenen Koordinaten, auf ein Viertelgrad-Raster gerundet (Sonnenzeit-Fehler < 1 min;
# so teilen sich die Londoner Motive wenige Bezugspunkte -> kaum Mehr-Rechenzeit), alle anderen Berlin.
LIGHT_REF_BERLIN = (52.52, 13.40)


def light_reference(lat: float, lon: float) -> tuple:
    """Bezugspunkt (lat, lon) fuer die Lichtfenster eines Motivs."""
    if is_england(lat, lon):
        return (round(lat * 4) / 4, round(lon * 4) / 4)
    return LIGHT_REF_BERLIN


def build_day_sessions(sun_info_fn, ref_lat: float, ref_lon: float, today: date, days: int) -> dict:
    """Lichtfenster-Zeitpunkte je Tag und Session fuer einen Bezugspunkt.

    sun_info_fn: calculate_sun_info (von der Pipeline uebergeben, damit Tests sie dort ersetzen koennen).
    """
    out: dict = {}
    for delta in range(days):
        d = today + timedelta(days=delta)
        sun = sun_info_fn(ref_lat, ref_lon, d)
        out[d.isoformat()] = {
            "blue_morning":   sample_window(sun.blue_hour_morning_start,  sun.blue_hour_morning_end),
            "golden_morning": sample_window(sun.golden_hour_morning_start, sun.golden_hour_morning_end),
            "golden_evening": sample_window(sun.golden_hour_evening_start, sun.golden_hour_evening_end),
            "blue_evening":   sample_window(sun.blue_hour_evening_start,   sun.blue_hour_evening_end),
        }
    return out


def compute_d(apex_effective_m: float, body_alt_deg: float, alt_min_deg: float) -> Optional[float]:
    """
    Horizontalentfernung, von der der Himmelskörper genau über der Motivspitze erscheint.
    d = apex_effective_m / tan(body_altitude)
    Gibt None zurück wenn d außerhalb [D_MIN_M, D_MAX_M] oder Altitude zu niedrig.
    """
    if body_alt_deg <= alt_min_deg:
        return None
    if apex_effective_m <= 0:
        return None
    alt_rad = math.radians(body_alt_deg)
    d = apex_effective_m / math.tan(alt_rad)
    if D_MIN_M <= d <= D_MAX_M:
        return d
    return None


# ---------------------------------------------------------------------------
# Scoring-Hilfsfunktionen (körper-unabhängig)
# ---------------------------------------------------------------------------

def score_licht(session: str) -> float:
    """Lichtqualitäts-Score nach Tageszeit und Session."""
    return {
        "golden_evening": 1.00,
        "golden_morning": 0.90,
        "blue_evening":   0.80,
        "blue_morning":   0.70,
    }.get(session, 0.5)


def score_komposition(subject_width_m: float, d_m: float, body_angular_diam_deg: float) -> float:
    """
    Kompositions-Score: wie gut passt das Seitenverhältnis von Körper und Motiv?
    Optimum: subject_angular_width / body_angular_diameter ≈ 1.5
    """
    if d_m <= 0:
        return 0.0
    subject_ang = math.degrees(2 * math.atan(subject_width_m / 2 / d_m))
    ratio = subject_ang / body_angular_diam_deg
    if 0.5 <= ratio <= 3.0:
        return 1.0 - abs(ratio - 1.5) / 3.0
    elif ratio < 0.5:
        return ratio / 0.5 * 0.7
    else:
        return max(0.0, 1.0 - (ratio - 3.0) / 5.0)


def weather_desc(hw) -> str:
    """Kurze Wetter-Beschreibung für UI."""
    cc = hw.cloud_cover_pct
    rain = hw.precipitation_prob_pct
    if rain > 60:
        return "Regen wahrscheinlich"
    if cc < 20:
        return "Klarer Himmel"
    if cc < 50:
        return "Teilweise bewölkt"
    if cc < 80:
        return "Überwiegend bewölkt"
    return "Bedeckt"


# ---------------------------------------------------------------------------
# Wetter-Cache (geteilt über alle Pipelines innerhalb eines Runs)
# ---------------------------------------------------------------------------

_weather_cache: dict[str, WeatherForecast] = {}

# US-141 Baustein 3 (AK-104/105): Zähler der Wetteranfragen des Scouts (Entdecken). Der Scout
# schöpft aus demselben Kontingent wie der Ortswetter-Lauf, wird aber getrennt ausgewiesen.
# Jede Anfrage zählt (auch fehlgeschlagene); abgelehnte = HTTP 429. Läuft in Worker-Threads,
# darum mit Sperre. Zurückgesetzt wird beim Leeren des Wetter-Caches (Beginn eines Scout-Laufs).
_zaehler_lock = threading.Lock()
_zaehler = {"anfragen": 0, "abgelehnt": 0, "start": time.monotonic()}


def _ist_429(exc: BaseException) -> bool:
    antwort = getattr(exc, "response", None)
    return getattr(antwort, "status_code", None) == 429


async def get_weather(lat: float, lon: float) -> Optional[WeatherForecast]:
    """Wetter-Forecast mit Positions-Caching (auf 0.1° gerundet)."""
    key = f"{round(lat, 1)},{round(lon, 1)}"
    if key not in _weather_cache:
        with _zaehler_lock:
            _zaehler["anfragen"] += 1
        try:
            fc = await fetch_weather_forecast(lat, lon, days=14)
            _weather_cache[key] = fc
        except Exception as e:
            if _ist_429(e):
                with _zaehler_lock:
                    _zaehler["abgelehnt"] += 1
            log.warning("Wetter-API Fehler für %s: %s", key, e)
            return None
    return _weather_cache.get(key)


def zaehlzeile(pipeline: str) -> str:
    """Text der Zählzeile des Scouts (Entdecken): bisher gestellte Anfragen im laufenden Scout-Lauf,
    davon abgelehnte (429), Anteil in Prozent, Dauer. Enthält keine Ortsnamen."""
    with _zaehler_lock:
        n, a, t0 = _zaehler["anfragen"], _zaehler["abgelehnt"], _zaehler["start"]
    anteil = (100.0 * a / n) if n else 0.0
    return ("Entdecken (Scout) %s: im Scout-Lauf bisher gesamt %d Anfragen, davon %d abgelehnt (429), "
            "Anteil %s %% · Dauer %s s") % (
        pipeline, n, a, ("%.1f" % anteil).replace(".", ","), ("%.1f" % (time.monotonic() - t0)).replace(".", ","))


def zaehler_entnehmen() -> tuple:
    """BUG-117 Nachfund 2: liefert (Anfragen, abgelehnt) seit der letzten Entnahme und setzt beide auf null,
    in einem Schritt unter der Sperre. So wird jede Scout-Anfrage genau einmal auf den Tagesstand gebucht
    (nicht doppelt, wenn ein Durchgang abbricht, und nichts geht zwischen Lesen und Zurücksetzen verloren).
    Die Zählzeile des laufenden Scout-Laufs ist davon nicht betroffen (Entnahme erst nach dem Lauf)."""
    with _zaehler_lock:
        n, a = _zaehler["anfragen"], _zaehler["abgelehnt"]
        _zaehler["anfragen"] = 0
        _zaehler["abgelehnt"] = 0
    return n, a


def clear_weather_cache() -> None:
    """Vor jedem Pipeline-Run leeren, damit kein Stale-Cache entsteht (und die Anfragen-Zähler neu beginnen)."""
    _weather_cache.clear()
    with _zaehler_lock:
        _zaehler["anfragen"] = 0
        _zaehler["abgelehnt"] = 0
        _zaehler["start"] = time.monotonic()
