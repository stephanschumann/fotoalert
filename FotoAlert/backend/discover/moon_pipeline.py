"""
Scout-Tab Pipeline: Mond-Alignment-Chancen.

Ablauf für jeden der nächsten 14 Tage:
  1. Lichtfenster bestimmen (goldene + blaue Stunde, morgens + abends)
  2. Mond-Positionen im 15-min-Raster per Motiv berechnen (topozentrisch korrekt)
  3. Standpunkt-Distanz d = apex_effective_m / tan(alt_moon) berechnen
  4. Standpunkt S via destination_point(Motiv → Mond-Gegenrichtung, d)
  5. d-Gate: 100 m ≤ d ≤ 13.000 m, moon_alt ≥ 5°
  6. Score berechnen
  7. Je Motiv/Tag/Session: nur bestes Ergebnis behalten (Dedup)
  8. Wetter-Score ergänzen
"""
from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from calculations.astronomy import CelestialPosition, calculate_sun_info, get_body_position
from calculations.weather import calculate_photo_weather_score
from discover.geometry import destination_point
from discover.pipeline_base import (
    D_MIN_M, D_MAX_M,
    W_ALIGNMENT, W_PHASE, W_LICHT, W_KOMPOSITION, W_WETTER,
    ScoutOpportunity,
    is_new_perspective, sample_window, compute_d,
    score_licht, score_komposition, weather_desc, get_weather,
)
from discover.subjects import SUBJECTS, DiscoverSubject

log = logging.getLogger(__name__)

# Berliner Zentrum: für Sonnen-Lichtfenster (Variation < 1 min über 50 km)
_SUN_REF_LAT = 52.52
_SUN_REF_LON = 13.40

MOON_ALT_MIN_DEG = 5.0
MOON_ANGULAR_DIAM_DEG = 0.52


# ---------------------------------------------------------------------------
# Mond-spezifische Berechnungen
# ---------------------------------------------------------------------------

def _approx_illumination(dt: datetime) -> float:
    """
    Approximiert die Mondbeleuchtung in % für einen Zeitpunkt.
    Nutzt vereinfachten synodischen Mondzyklus (29.53 Tage).
    Referenz-Vollmond: 2024-01-25 17:54 UTC
    """
    REF_FULL_MOON = datetime(2024, 1, 25, 17, 54, tzinfo=timezone.utc)
    SYNODIC_PERIOD_DAYS = 29.530589
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    elapsed = (dt - REF_FULL_MOON).total_seconds() / 86400
    phase_fraction = (elapsed % SYNODIC_PERIOD_DAYS) / SYNODIC_PERIOD_DAYS
    illumination = (1.0 + math.cos(2 * math.pi * phase_fraction)) / 2.0
    return round(illumination * 100, 1)


def _focal_length(d_m: float, subject: DiscoverSubject) -> float:
    """Brennweite so dass Mond + Motivspitze ~15° Bildwinkel füllen (KB-Vollformat)."""
    subject_angle_deg = math.degrees(math.atan(subject.apex_effective_m / d_m))
    desired_fov_v_deg = max(subject_angle_deg * 2 + MOON_ANGULAR_DIAM_DEG * 2, 4.0)
    sensor_half_mm = 12.0
    f = sensor_half_mm / math.tan(math.radians(desired_fov_v_deg / 2))
    return round(f / 10) * 10


def _score_alignment(moon_alt_deg: float) -> float:
    """Gaußkurve um 25° Optimum: gute Geometrie, nicht zu nah, nicht zu flach."""
    if moon_alt_deg < MOON_ALT_MIN_DEG:
        return 0.0
    opt, sigma = 25.0, 20.0
    return math.exp(-((moon_alt_deg - opt) ** 2) / (2 * sigma ** 2))


def _score_phase(illumination_pct: float) -> float:
    """Mond-Phasen-Score: Vollmond = 1.0, Neumond = 0.0."""
    x = illumination_pct / 100.0
    if x >= 0.7:
        return 1.0
    if x >= 0.4:
        return 0.7 + (x - 0.4) / 0.3 * 0.3
    return x / 0.4 * 0.7


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

async def run(days: int = 14) -> list[ScoutOpportunity]:
    """Berechnet Mond-Alignment-Chancen für die nächsten `days` Tage."""
    today = date.today()
    all_opportunities: list[ScoutOpportunity] = []

    # Lichtfenster für alle Tage (Sonnen-Position nur einmal pro Tag nötig)
    day_sessions: dict[str, dict[str, list[datetime]]] = {}
    for delta in range(days):
        d = today + timedelta(days=delta)
        sun = calculate_sun_info(_SUN_REF_LAT, _SUN_REF_LON, d)
        day_sessions[d.isoformat()] = {
            "blue_morning":   sample_window(sun.blue_hour_morning_start,  sun.blue_hour_morning_end),
            "golden_morning": sample_window(sun.golden_hour_morning_start, sun.golden_hour_morning_end),
            "golden_evening": sample_window(sun.golden_hour_evening_start, sun.golden_hour_evening_end),
            "blue_evening":   sample_window(sun.blue_hour_evening_start,   sun.blue_hour_evening_end),
        }

    log.info("[Mond] Pipeline läuft (%d Motive × %d Tage)...", len(SUBJECTS), days)

    for subject in SUBJECTS:
        weather_fc = await get_weather(subject.lat, subject.lon)
        moon_pos_cache: dict[datetime, Optional[CelestialPosition]] = {}

        for day_str, sessions in day_sessions.items():
            for session_name, timestamps in sessions.items():
                best: Optional[ScoutOpportunity] = None

                for dt in timestamps:
                    if dt not in moon_pos_cache:
                        moon_pos_cache[dt] = get_body_position(
                            subject.lat, subject.lon, "moon", dt
                        )
                    moon = moon_pos_cache.get(dt)
                    if moon is None or moon.altitude < MOON_ALT_MIN_DEG:
                        continue

                    d = compute_d(subject.apex_effective_m, moon.altitude, MOON_ALT_MIN_DEG)
                    if d is None:
                        continue

                    standpoint_bearing = (moon.azimuth + 180.0) % 360.0
                    sp_lat, sp_lon = destination_point(subject.lat, subject.lon, standpoint_bearing, d)
                    if not is_new_perspective(sp_lat, sp_lon, subject.id):
                        continue

                    illumination_pct = _approx_illumination(dt)
                    weather_score, w_desc = 0.5, "Unbekannt"
                    if weather_fc is not None:
                        hw = weather_fc.get_at(dt)
                        if hw is not None:
                            weather_score = min(1.0, calculate_photo_weather_score(hw))
                            w_desc = weather_desc(hw)

                    sa = _score_alignment(moon.altitude)
                    sp_ = _score_phase(illumination_pct)
                    sl = score_licht(session_name)
                    sk = score_komposition(subject.subject_width_m, d, MOON_ANGULAR_DIAM_DEG)
                    total = (W_ALIGNMENT * sa + W_PHASE * sp_ + W_LICHT * sl
                             + W_KOMPOSITION * sk + W_WETTER * weather_score)

                    opp = ScoutOpportunity(
                        body_name="moon",
                        subject_id=subject.id,
                        subject_name=subject.name,
                        subject_lat=subject.lat,
                        subject_lon=subject.lon,
                        day=day_str,
                        session=session_name,
                        dt_utc=dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        body_azimuth_deg=round(moon.azimuth, 1),
                        body_altitude_deg=round(moon.altitude, 1),
                        body_illumination_pct=round(illumination_pct, 1),
                        distance_m=round(d, 0),
                        standpoint_lat=round(sp_lat, 6),
                        standpoint_lon=round(sp_lon, 6),
                        focal_length_equiv_mm=_focal_length(d, subject),
                        score=round(total, 4),
                        score_alignment=round(sa, 4),
                        score_phase=round(sp_, 4),
                        score_licht=round(sl, 4),
                        score_komposition=round(sk, 4),
                        score_wetter=round(weather_score, 4),
                        weather_description=w_desc,
                    )
                    if best is None or total > best.score:
                        best = opp

                if best is not None:
                    all_opportunities.append(best)

    log.info("[Mond] %d Chancen gefunden.", len(all_opportunities))
    return all_opportunities
