"""
Scout-Tab Pipeline: Sonnen-Alignment-Chancen.

Gleiche Apex-Geometrie wie moon_pipeline:
  d = apex_effective_m / tan(sun_alt)
  Standpunkt = Motiv → Gegenrichtung der Sonne

Unterschiede zum Mond:
  - S_phase = 1.0 (Sonne immer voll beleuchtet — v2: atmosphärisches Scoring → US-82)
  - S_alignment: Gaußkurve um 4° Optimum (flache Sonne direkt über Motivspitze = dramatisch)
  - body_illumination_pct = None
  - Alt-Gate: ≥ 0.5° (Sonne gerade über Horizont; bei golden hour typisch 0–8°)
"""
from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta
from typing import Optional

from calculations.astronomy import CelestialPosition, calculate_sun_info, get_body_position
from calculations.weather import calculate_photo_weather_score
from discover.geometry import destination_point
from discover.pipeline_base import (
    W_ALIGNMENT, W_PHASE, W_LICHT, W_KOMPOSITION, W_WETTER,
    ScoutOpportunity,
    is_new_perspective, sample_window, compute_d,
    score_licht, score_komposition, weather_desc, get_weather,
)
from discover.subjects import SUBJECTS, DiscoverSubject

log = logging.getLogger(__name__)

_SUN_REF_LAT = 52.52
_SUN_REF_LON = 13.40

SUN_ALT_MIN_DEG = 0.5        # Sonne muss sichtbar über Horizont sein
SUN_ANGULAR_DIAM_DEG = 0.53  # Mittlerer Sonnendurchmesser in Bogengrad


# ---------------------------------------------------------------------------
# Sonnen-spezifische Berechnungen
# ---------------------------------------------------------------------------

def _focal_length(d_m: float, subject: DiscoverSubject) -> float:
    """Brennweite so dass Sonne + Motivspitze ~15° Bildwinkel füllen (KB-Vollformat)."""
    subject_angle_deg = math.degrees(math.atan(subject.apex_effective_m / d_m))
    desired_fov_v_deg = max(subject_angle_deg * 2 + SUN_ANGULAR_DIAM_DEG * 2, 4.0)
    sensor_half_mm = 12.0
    f = sensor_half_mm / math.tan(math.radians(desired_fov_v_deg / 2))
    return round(f / 10) * 10


def _score_alignment(sun_alt_deg: float) -> float:
    """
    Gaußkurve um 4° Optimum: flache Sonne direkt über Motivspitze ist am dramatischsten.
    Sigma=8° → breite Toleranz, da Sonne bei golden hour ohnehin nur 0–8° hoch ist.
    """
    if sun_alt_deg < SUN_ALT_MIN_DEG:
        return 0.0
    opt, sigma = 4.0, 8.0
    return math.exp(-((sun_alt_deg - opt) ** 2) / (2 * sigma ** 2))


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

async def run(days: int = 14) -> list[ScoutOpportunity]:
    """Berechnet Sonnen-Alignment-Chancen für die nächsten `days` Tage."""
    today = date.today()
    all_opportunities: list[ScoutOpportunity] = []

    # Lichtfenster für alle Tage
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

    log.info("[Sonne] Pipeline läuft (%d Motive × %d Tage)...", len(SUBJECTS), days)

    for subject in SUBJECTS:
        weather_fc = await get_weather(subject.lat, subject.lon)
        sun_pos_cache: dict[datetime, Optional[CelestialPosition]] = {}

        for day_str, sessions in day_sessions.items():
            for session_name, timestamps in sessions.items():
                best: Optional[ScoutOpportunity] = None

                for dt in timestamps:
                    if dt not in sun_pos_cache:
                        sun_pos_cache[dt] = get_body_position(
                            subject.lat, subject.lon, "sun", dt
                        )
                    sun_pos = sun_pos_cache.get(dt)
                    if sun_pos is None or sun_pos.altitude < SUN_ALT_MIN_DEG:
                        continue

                    d = compute_d(subject.apex_effective_m, sun_pos.altitude, SUN_ALT_MIN_DEG)
                    if d is None:
                        continue

                    standpoint_bearing = (sun_pos.azimuth + 180.0) % 360.0
                    sp_lat, sp_lon = destination_point(subject.lat, subject.lon, standpoint_bearing, d)
                    if not is_new_perspective(sp_lat, sp_lon, subject.id):
                        continue

                    weather_score, w_desc = 0.5, "Unbekannt"
                    if weather_fc is not None:
                        hw = weather_fc.get_at(dt)
                        if hw is not None:
                            weather_score = min(1.0, calculate_photo_weather_score(hw))
                            w_desc = weather_desc(hw)

                    sa = _score_alignment(sun_pos.altitude)
                    # S_phase = 1.0: Sonne immer voll beleuchtet
                    # v2: atmosphärisches Rötlichkeits-Scoring → US-82
                    sp_ = 1.0
                    sl = score_licht(session_name)
                    sk = score_komposition(subject.subject_width_m, d, SUN_ANGULAR_DIAM_DEG)
                    total = (W_ALIGNMENT * sa + W_PHASE * sp_ + W_LICHT * sl
                             + W_KOMPOSITION * sk + W_WETTER * weather_score)

                    opp = ScoutOpportunity(
                        body_name="sun",
                        subject_id=subject.id,
                        subject_name=subject.name,
                        subject_lat=subject.lat,
                        subject_lon=subject.lon,
                        day=day_str,
                        session=session_name,
                        dt_utc=dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        body_azimuth_deg=round(sun_pos.azimuth, 1),
                        body_altitude_deg=round(sun_pos.altitude, 1),
                        body_illumination_pct=None,
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

    log.info("[Sonne] %d Chancen gefunden.", len(all_opportunities))
    return all_opportunities
