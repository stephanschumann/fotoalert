"""
Gemeinsame Bausteine für alle Scout-Pipelines.

Jede körper-spezifische Pipeline (moon_pipeline, sun_pipeline, …) importiert
von hier: ScoutOpportunity, Score-Gewichte, Geometrie-Helfer, Wetter-Cache.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

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


async def get_weather(lat: float, lon: float) -> Optional[WeatherForecast]:
    """Wetter-Forecast mit Positions-Caching (auf 0.1° gerundet)."""
    key = f"{round(lat, 1)},{round(lon, 1)}"
    if key not in _weather_cache:
        try:
            fc = await fetch_weather_forecast(lat, lon, days=14)
            _weather_cache[key] = fc
        except Exception as e:
            log.warning("Wetter-API Fehler für %s: %s", key, e)
            return None
    return _weather_cache.get(key)


def clear_weather_cache() -> None:
    """Vor jedem Pipeline-Run leeren, damit kein Stale-Cache entsteht."""
    _weather_cache.clear()
