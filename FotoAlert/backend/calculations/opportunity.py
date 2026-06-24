"""
Opportunity-Scoring-Algorithmus.

Kombiniert Astronomie-Daten, Wetterdaten und Locations zu
konkreten Foto-Empfehlungen mit Score, Beschreibung und
technischen Hinweisen (Brennweite, Uhrzeit, Standort).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from calculations.astronomy import (
    AlignmentResult,
    AlignmentType,
    AstronomyReport,
    SubjectAngularProfile,
    calculate_azimuth_alignment,
    calculate_focal_length_for_subject,
    calculate_full_report,
    calculate_subject_angular_profile,
    find_moon_alignment_times,
    find_precise_alignment_times,
    find_sun_alignment_times,
    get_body_position,
    get_moon_earth_distance_km,
)
from calculations.weather import WeatherForecast, calculate_photo_weather_score
from data.locations import PhotoLocation


class EventType(str, Enum):
    GOLDEN_HOUR_MORNING = "Goldene Stunde Morgen"
    GOLDEN_HOUR_EVENING = "Goldene Stunde Abend"
    BLUE_HOUR_EVENING = "Blaue Stunde"
    MOON_RISE = "Mondaufgang"
    MOON_SET = "Monduntergang"
    FULL_MOON = "Vollmond"
    NEW_MOON = "Neumond"
    SUPER_MOON = "Supermond"
    SUN_ALIGNMENT = "Sonnen-Alignment"
    MOON_ALIGNMENT = "Mond-Alignment"
    MILKY_WAY = "Milchstraße"
    METEOR_SHOWER = "Meteoritenschauer"
    ECLIPSE = "Sonnenfinsternis"


@dataclass
class CameraHint:
    focal_length_mm: int
    aperture_suggestion: str       # z.B. "f/8"
    shutter_suggestion: str        # z.B. "1/500s"
    iso_suggestion: str            # z.B. "ISO 400"
    tripod_required: bool = False
    extra_tip: str = ""


@dataclass
class PhotoOpportunity:
    """Eine konkrete Foto-Chance."""
    id: str
    location: PhotoLocation
    event_type: EventType
    title: str
    description: str
    shoot_time: datetime           # Optimale Aufnahmezeit (UTC)
    shoot_window_start: datetime
    shoot_window_end: datetime

    # Scores
    overall_score: float           # 0–1, kombinierter Score
    astronomy_score: float
    weather_score: float
    location_score: float

    # Technische Hinweise
    camera_hints: list[CameraHint] = field(default_factory=list)
    subject_azimuth: Optional[float] = None   # Azimut des Motivs
    celestial_azimuth: Optional[float] = None # Azimut des Himmelsobjekts
    celestial_altitude: Optional[float] = None

    # Kontext
    astronomy_report: Optional[AstronomyReport] = None
    weather_description: str = ""
    alert_priority: int = 0  # 0=niedrig, 1=mittel, 2=hoch, 3=außergewöhnlich


def _score_moon_phase_for_milkyway(phase_fraction: float) -> float:
    """Neumond = ideal für Milchstraße. Vollmond = schlecht."""
    if phase_fraction < 0.1 or phase_fraction > 0.9:
        return 1.0
    elif phase_fraction < 0.2 or phase_fraction > 0.8:
        return 0.7
    elif phase_fraction < 0.4 or phase_fraction > 0.6:
        return 0.3
    else:
        return 0.0  # Vollmond


def _score_moon_phase_for_moonshot(phase_fraction: float) -> float:
    """Vollmond = ideal für Mondfotos."""
    return 1.0 - abs(phase_fraction - 0.5) * 2


# US-91/92/93: Schwelle für Supermond (Vollmond nahe Perigäum)
_SUPERMOON_THRESHOLD_KM = 362_000


def _moon_phase_special_event_type(
    phase_fraction: float, shoot_time: datetime
) -> Optional[EventType]:
    """
    Gibt SUPER_MOON, FULL_MOON oder NEW_MOON zurück wenn die Mondphase
    einen Override des event_type rechtfertigt — sonst None.

    US-91: Vollmond (phase_fraction 0.47–0.53) → FULL_MOON
    US-93: Vollmond + Distanz < 362.000 km → SUPER_MOON (Vorrang vor FULL_MOON)
    US-92: Neumond (phase_fraction < 0.03 oder > 0.97) → NEW_MOON
    """
    if 0.47 <= phase_fraction <= 0.53:
        try:
            dist_km = get_moon_earth_distance_km(shoot_time)
            if dist_km < _SUPERMOON_THRESHOLD_KM:
                return EventType.SUPER_MOON
        except Exception:
            pass
        return EventType.FULL_MOON
    if phase_fraction < 0.03 or phase_fraction > 0.97:
        return EventType.NEW_MOON
    return None


_FOCAL_STEPS = [24, 35, 50, 85, 135, 200, 300, 400, 600]


def _focal_for_location(location: "PhotoLocation", default_mm: int = 50) -> int:
    """
    Berechnet die optimale Brennweite für eine Location.

    Priorität:
    1. focal_length_suggestions[0] – manuell kuratiert, am zuverlässigsten
    2. Berechnung aus subject_height_m × distance_m (25 % Bildausfüllung)
    3. default_mm – eventtyp-spezifischer Fallback
    """
    if location.focal_length_suggestions:
        return location.focal_length_suggestions[0]
    if location.subject_height_m and location.distance_m and location.distance_m > 0:
        raw = calculate_focal_length_for_subject(
            location.subject_height_m,
            location.distance_m,
            desired_frame_fill_pct=0.25,
        )
        return min(_FOCAL_STEPS, key=lambda x: abs(x - raw))
    return default_mm


def _camera_hints_golden_hour(focal_mm: int) -> list[CameraHint]:
    tripod = focal_mm >= 200
    shutter = "1/500s" if focal_mm >= 200 else "1/250s"
    return [
        CameraHint(
            focal_length_mm=focal_mm,
            aperture_suggestion="f/8",
            shutter_suggestion=shutter,
            iso_suggestion="ISO 100–400",
            tripod_required=tripod,
            extra_tip="RAW-Format für maximalen Dynamikumfang. Belichtungsreihe (+/- 1 EV).",
        )
    ]


def _camera_hints_blue_hour(focal_mm: int) -> list[CameraHint]:
    aperture = "f/8" if focal_mm >= 200 else "f/11"
    shutter = "1/30s–2s" if focal_mm >= 200 else "4–30s"
    return [
        CameraHint(
            focal_length_mm=focal_mm,
            aperture_suggestion=aperture,
            shutter_suggestion=shutter,
            iso_suggestion="ISO 100–200",
            tripod_required=True,
            extra_tip="Fernauslöser verwenden. Lichter nicht ausfressen – Belichtung eher knapp halten.",
        )
    ]


def _camera_hints_moon(focal_length_mm: int) -> list[CameraHint]:
    return [
        CameraHint(
            focal_length_mm=focal_length_mm,
            aperture_suggestion="f/8–f/11",
            shutter_suggestion="1/250s–1/1000s",
            iso_suggestion="ISO 200–800",
            tripod_required=True if focal_length_mm >= 300 else False,
            extra_tip="Mond-Belichtung: Sunny-16-Regel angepasst. Mondoberfläche = sonnenbeleuchtet.",
        )
    ]


def _camera_hints_milkyway() -> list[CameraHint]:
    return [
        CameraHint(
            focal_length_mm=20, aperture_suggestion="f/1.8–f/2.8",
            shutter_suggestion="15–25s (500er Regel)",
            iso_suggestion="ISO 3200–6400", tripod_required=True,
            extra_tip="Fokus auf unendlich tagsüber einstellen und markieren. "
                      "Intervallaufnahme für Zeitraffer. Weißabgleich 3800K.",
        )
    ]


def _camera_hints_meteor() -> list[CameraHint]:
    return [
        CameraHint(
            focal_length_mm=14, aperture_suggestion="f/2.8",
            shutter_suggestion="20s", iso_suggestion="ISO 3200",
            tripod_required=True,
            extra_tip="Intervallshooter aktivieren. Fischaugenobjektiv für maximales FOV. "
                      "Radiant im Bildfeld halten, Meteore zeigen weg vom Radiant.",
        )
    ]


def _camera_hints_alignment(focal_mm: int, is_solar: bool = True) -> list[CameraHint]:
    if is_solar:
        return [CameraHint(
            focal_length_mm=focal_mm,
            aperture_suggestion="f/8–f/11",
            shutter_suggestion="1/2000s–1/500s",
            iso_suggestion="ISO 100",
            tripod_required=True,
            extra_tip="NIE ohne ND-Filter in die Sonne schauen! ND 3.8 (ND6400) für direkte Sonnen-Aufnahmen. "
                      "Belichtung für Gebäude oder Sonne separat bestimmen – HDR verwenden.",
        )]
    else:
        return _camera_hints_moon(focal_mm)


# ---------------------------------------------------------------------------
# Helfer: Foto-Lichtfenster (US-36)
# ---------------------------------------------------------------------------

def _in_photo_window(dt: datetime, sun: "SunReport", buffer_min: int = 30) -> bool:
    """True wenn dt innerhalb goldener oder blauer Stunde liegt (±buffer_min Puffer).
    Alignment-Events außerhalb dieser Fenster werden gefiltert (US-36).
    Bürgerliche Dämmerung entspricht ca. golden_hour_start − buffer … blue_hour_end + buffer."""
    buf = timedelta(minutes=buffer_min)
    windows = [
        (sun.golden_hour_morning_start - buf, sun.blue_hour_morning_end   + buf),
        (sun.golden_hour_evening_start - buf, sun.blue_hour_evening_end   + buf),
    ]
    return any(start <= dt <= end for start, end in windows)


# ---------------------------------------------------------------------------
# Score-Helfer: Wetter nur innerhalb von 3 Tagen
# ---------------------------------------------------------------------------

def _w_score(forecast: WeatherForecast, shoot_time: datetime, use_weather: bool) -> float:
    """Wetter-Score: realer Wert wenn ≤ 3 Tage, 0.0 (= unbekannt) wenn weiter entfernt."""
    if not use_weather:
        return 0.0
    w_at = forecast.get_at(shoot_time)
    return calculate_photo_weather_score(w_at) if w_at else 0.0


def _overall(astro: float, weather: float, use_weather: bool) -> float:
    """Gesamt-Score: reine Astronomie wenn Wetter unbekannt, sonst 65/35 gewichtet. Max 1.0."""
    if not use_weather or weather == 0.0:
        return min(1.0, astro)
    return min(1.0, astro * 0.65 + weather * 0.35)


def _weather_label(weather: float, use_weather: bool) -> str:
    """Lesbarer Wettertext für Beschreibungen."""
    if not use_weather:
        return "Wetter noch unbekannt (> 3 Tage)"
    if weather >= 0.8:
        return f"Wetter ideal ({weather:.0%})"
    if weather >= 0.6:
        return f"Wetter gut ({weather:.0%})"
    if weather >= 0.4:
        return f"Wetter mäßig ({weather:.0%})"
    return f"Wetter schwierig ({weather:.0%})"


# ---------------------------------------------------------------------------
# Haupt-Score-Funktion
# ---------------------------------------------------------------------------

async def find_opportunities(
    location: PhotoLocation,
    target_date: date,
    forecast: WeatherForecast,
    min_score: float = 0.35,
    astronomy_only: bool = False,
) -> list[PhotoOpportunity]:
    """
    Findet alle Foto-Chancen für eine Location an einem bestimmten Datum.
    Gibt eine Liste von PhotoOpportunity zurück, absteigend nach Score sortiert.
    astronomy_only=True: Wetter wird grundsätzlich ignoriert (z.B. Jahreskalender).
    """
    opportunities: list[PhotoOpportunity] = []

    # US-01/02: Wetter nur innerhalb von 3 Tagen berücksichtigen
    days_until = (target_date - date.today()).days
    use_weather = (days_until <= 3) and not astronomy_only

    lat = location.observer_lat
    lon = location.observer_lon

    # Astronomie-Bericht
    astro = calculate_full_report(lat, lon, target_date)
    sun = astro.sun
    moon = astro.moon
    mw = astro.milky_way

    # Azimut vom Beobachter zum Motiv
    subject_az = calculate_azimuth_alignment(
        location.observer_lat, location.observer_lon,
        location.subject_lat, location.subject_lon,
    )

    # -----------------------------------------------------------------------
    # 1. GOLDENE STUNDE ABEND
    # -----------------------------------------------------------------------
    gh_eve_start = sun.golden_hour_evening_start
    gh_eve_end = sun.golden_hour_evening_end
    sun_pos_gh = get_body_position(lat, lon, "sun", gh_eve_start)
    sun_alignment_bonus = 0.0
    if sun_pos_gh:
        az_diff = abs((sun_pos_gh.azimuth - subject_az + 180) % 360 - 180)
        if az_diff < 15:
            sun_alignment_bonus = 0.3
        elif az_diff < 30:
            sun_alignment_bonus = 0.15

    a_score = min(1.0, 0.8 + sun_alignment_bonus)
    w_score = _w_score(forecast, gh_eve_start, use_weather)
    overall = _overall(a_score, w_score, use_weather)

    if overall >= min_score:
        focal_mm = _focal_for_location(location, default_mm=50)
        desc = (
            f"Goldene Stunde von {_fmt_time(gh_eve_start)} bis {_fmt_time(gh_eve_end)} (Ortszeit). "
            f"{_weather_label(w_score, use_weather)}."
        )
        if sun_alignment_bonus > 0:
            desc += f" Sonne beleuchtet {location.subject_name} direkt."

        opportunities.append(PhotoOpportunity(
            id=f"{location.id}_golden_eve_{target_date.isoformat()}",
            location=location,
            event_type=EventType.GOLDEN_HOUR_EVENING,
            title=f"Goldene Stunde – {location.name}",
            description=desc,
            shoot_time=gh_eve_start,
            shoot_window_start=gh_eve_start,
            shoot_window_end=gh_eve_end,
            overall_score=round(overall, 2),
            astronomy_score=round(a_score, 2),
            weather_score=round(w_score, 2),
            location_score=1.0,
            camera_hints=_camera_hints_golden_hour(focal_mm),
            subject_azimuth=round(subject_az, 1),
            celestial_azimuth=round(sun_pos_gh.azimuth, 1) if sun_pos_gh else None,
            celestial_altitude=round(sun_pos_gh.altitude, 1) if sun_pos_gh else None,
            astronomy_report=astro,
            weather_description="",
            alert_priority=1 if overall > 0.7 else 0,
        ))

    # -----------------------------------------------------------------------
    # 2. BLAUE STUNDE ABEND
    # -----------------------------------------------------------------------
    bh_start = sun.blue_hour_evening_start
    bh_end = sun.blue_hour_evening_end
    w_score_bh = _w_score(forecast, bh_start, use_weather)
    bh_overall = _overall(0.75, w_score_bh, use_weather)

    if bh_overall >= min_score:
        focal_mm_bh = _focal_for_location(location, default_mm=24)
        opportunities.append(PhotoOpportunity(
            id=f"{location.id}_blue_hour_{target_date.isoformat()}",
            location=location,
            event_type=EventType.BLUE_HOUR_EVENING,
            title=f"Blaue Stunde – {location.name}",
            description=(
                f"Optimales Fenster {_fmt_time(bh_start)}–{_fmt_time(bh_end)} UTC. "
                "Künstliche Beleuchtung trifft Resttageslichts – ideal für illuminierte Gebäude."
            ),
            shoot_time=bh_start,
            shoot_window_start=bh_start,
            shoot_window_end=bh_end,
            overall_score=round(bh_overall, 2),
            astronomy_score=0.75,
            weather_score=round(w_score_bh, 2),
            location_score=1.0,
            camera_hints=_camera_hints_blue_hour(focal_mm_bh),
            subject_azimuth=round(subject_az, 1),
            astronomy_report=astro,
            alert_priority=1 if bh_overall > 0.65 else 0,
        ))

    # -----------------------------------------------------------------------
    # 3. MOND-ALIGNMENT: Mond über/nahe dem Motiv
    # -----------------------------------------------------------------------
    moon_align_times = find_moon_alignment_times(
        lat, lon, subject_az, target_date, tolerance_deg=5.0
    )
    for align_time in moon_align_times:
        # US-36: Nur Events in goldener/blauer Stunde (±30 Min. bürgerliche Dämmerung)
        if not _in_photo_window(align_time, sun):
            continue
        moon_pos = get_body_position(lat, lon, "moon", align_time)
        if moon_pos and moon_pos.altitude > 2:
            w_s = _w_score(forecast, align_time, use_weather)
            phase_score = _score_moon_phase_for_moonshot(moon.phase_fraction)
            a_s = 0.6 + phase_score * 0.4

            # Brennweite berechnen
            focal_mm = 200
            if location.subject_height_m and location.distance_m:
                focal_mm = int(calculate_focal_length_for_subject(
                    location.subject_height_m, location.distance_m, desired_frame_fill_pct=0.4
                ))
                # Abrunden auf gängige Brennweite
                focal_mm = min([50,85,135,200,300,400,600], key=lambda x: abs(x - focal_mm))

            overall_m = _overall(a_s, w_s, use_weather)
            if overall_m >= min_score:
                # US-91/92/93: Vollmond/Supermond/Neumond-Override
                phase_special = _moon_phase_special_event_type(moon.phase_fraction, align_time)
                moon_event_type = phase_special or EventType.MOON_ALIGNMENT
                moon_priority = 3 if phase_special == EventType.SUPER_MOON else (2 if overall_m > 0.75 else 1)
                opportunities.append(PhotoOpportunity(
                    id=f"{location.id}_moon_align_{align_time.strftime('%Y%m%d%H%M')}",
                    location=location,
                    event_type=moon_event_type,
                    title=f"Mond über {location.subject_name}",
                    description=(
                        f"Mond ({moon.phase_name}, {moon.illumination_pct:.0f}% beleuchtet) "
                        f"steht nahe Azimut {subject_az:.0f}° – Sichtachse auf {location.subject_name}. "
                        f"Höhe: {moon_pos.altitude:.1f}°. Empfohlene Brennweite: ~{focal_mm}mm."
                    ),
                    shoot_time=align_time,
                    shoot_window_start=align_time - timedelta(minutes=15),
                    shoot_window_end=align_time + timedelta(minutes=15),
                    overall_score=round(overall_m, 2),
                    astronomy_score=round(a_s, 2),
                    weather_score=round(w_s, 2),
                    location_score=1.0,
                    camera_hints=_camera_hints_moon(focal_mm),
                    subject_azimuth=round(subject_az, 1),
                    celestial_azimuth=round(moon_pos.azimuth, 1),
                    celestial_altitude=round(moon_pos.altitude, 1),
                    astronomy_report=astro,
                    alert_priority=moon_priority,
                ))

    # -----------------------------------------------------------------------
    # 4. PRÄZISES 3D-ALIGNMENT (Sonne UND Mond)
    #    Nutzt jetzt die volle vertikale Triangulation:
    #    Azimut + Höhenwinkel der Motivspitze werden kombiniert geprüft.
    # -----------------------------------------------------------------------
    has_3d_data = (
        location.subject_height_m is not None
        and location.subject_height_m > 0
    )

    if has_3d_data:
        subject_width = location.subject_width_m or (location.subject_height_m * 0.3)

        for body_key, body_label, event_type_val, is_solar in [
            ("sun",  "Sonne", EventType.SUN_ALIGNMENT,  True),
            ("moon", "Mond",  EventType.MOON_ALIGNMENT, False),
        ]:
            precise_results = find_precise_alignment_times(
                lat, lon,
                location.subject_lat, location.subject_lon,
                subject_height_m=location.subject_height_m,
                subject_width_m=subject_width,
                target_date=target_date,
                body=body_key,
                az_tolerance_deg=3.0,
                min_quality=0.25,
                elevation_difference_m=getattr(location, 'elevation_difference_m', 0.0),
            )

            for result in precise_results:
                # Sonnen-Altitude-Filter: nicht zu hoch (kein dramatisches Licht)
                if is_solar and result.celestial_altitude > 20:
                    continue
                # Mond: nur wenn sichtbar (> 0°)
                if not is_solar and result.celestial_altitude < 0:
                    continue
                # Mond-Phase: schlechter Neumond für Mondfotos
                if not is_solar and moon.illumination_pct < 15:
                    continue
                # US-36: Nur Events in goldener/blauer Stunde (±30 Min.)
                if not _in_photo_window(result.time, sun):
                    continue

                w_s = _w_score(forecast, result.time, use_weather)

                # Astronomiebonus: Crown-Alignment ist seltener und wertvoller
                if result.alignment_type == AlignmentType.AT_CROWN:
                    a_s = 0.95
                    priority = 3
                elif result.alignment_type == AlignmentType.CLEARING_TOP:
                    a_s = 0.80
                    priority = 2
                elif result.alignment_type == AlignmentType.BEHIND_MID:
                    a_s = 0.65
                    priority = 1
                else:
                    a_s = 0.50
                    priority = 1

                # Mondphase-Bonus bei Mondfotos
                if not is_solar:
                    phase_bonus = _score_moon_phase_for_moonshot(moon.phase_fraction)
                    a_s = a_s * 0.7 + phase_bonus * 0.3

                overall_3d = _overall(a_s * result.quality_score, w_s, use_weather)
                if overall_3d < min_score:
                    continue

                # Brennweite aus dem Angular-Profil des Motivs
                profile = result.subject_profile
                focal_mm = 200
                if location.subject_height_m and profile.ground_distance_m:
                    raw = calculate_focal_length_for_subject(
                        location.subject_height_m,
                        profile.ground_distance_m,
                        desired_frame_fill_pct=0.35,
                    )
                    focal_mm = min([50,85,135,200,300,400,600], key=lambda x: abs(x - raw))

                is_sunrise = result.time.hour < 12
                align_label = result.alignment_type

                desc = (
                    f"{body_label} steht {align_label} von {location.subject_name} "
                    f"(Azimut {result.celestial_azimuth:.1f}°, Höhe {result.celestial_altitude:.2f}°). "
                    f"Motivspitze bei {profile.angular_altitude_top_deg:.2f}°, "
                    f"Distanz {profile.ground_distance_m:.0f}m. "
                    f"Qualitäts-Score: {result.quality_score:.0%}."
                )
                if is_solar:
                    desc += " ACHTUNG: ND-Filter erforderlich!"

                opp_id = (
                    f"{location.id}_{body_key}_3d_{result.alignment_type[:5]}_"
                    f"{result.time.strftime('%Y%m%d%H%M')}"
                )

                # US-91/92/93: Vollmond/Supermond-Override bei Mond-Events
                final_event_type = event_type_val
                if not is_solar:
                    phase_special = _moon_phase_special_event_type(moon.phase_fraction, result.time)
                    if phase_special in (EventType.FULL_MOON, EventType.SUPER_MOON):
                        final_event_type = phase_special
                        if phase_special == EventType.SUPER_MOON:
                            priority = 3

                opportunities.append(PhotoOpportunity(
                    id=opp_id,
                    location=location,
                    event_type=final_event_type,
                    title=f"{body_label} {align_label} – {location.subject_name}",
                    description=desc,
                    shoot_time=result.time,
                    shoot_window_start=result.time - timedelta(minutes=8),
                    shoot_window_end=result.time + timedelta(minutes=8),
                    overall_score=round(overall_3d, 2),
                    astronomy_score=round(a_s * result.quality_score, 2),
                    weather_score=round(w_s, 2),
                    location_score=1.0,
                    camera_hints=_camera_hints_alignment(focal_mm, is_solar=is_solar),
                    subject_azimuth=round(profile.azimuth_deg, 1),
                    celestial_azimuth=result.celestial_azimuth,
                    celestial_altitude=result.celestial_altitude,
                    astronomy_report=astro,
                    alert_priority=priority,
                ))

    else:
        # Fallback: Nur Azimut-Check (für Locations ohne Gebäudehöhe)
        sun_align_times = find_sun_alignment_times(lat, lon, subject_az, target_date)
        for align_time in sun_align_times:
            # US-36: Nur Events in goldener/blauer Stunde (±30 Min.)
            if not _in_photo_window(align_time, sun):
                continue
            sun_pos = get_body_position(lat, lon, "sun", align_time)
            if sun_pos and 0 < sun_pos.altitude < 15:
                w_s = _w_score(forecast, align_time, use_weather)
                focal_mm = location.focal_length_suggestions[0] if location.focal_length_suggestions else 200
                overall_sa = _overall(0.85, w_s, use_weather)
                if overall_sa >= min_score:
                    opportunities.append(PhotoOpportunity(
                        id=f"{location.id}_sun_azimuth_{align_time.strftime('%Y%m%d%H%M')}",
                        location=location,
                        event_type=EventType.SUN_ALIGNMENT,
                        title=f"Sonne in Sichtachse – {location.subject_name}",
                        description=(
                            f"Sonne auf Azimut {sun_pos.azimuth:.0f}° (Sichtachse zum Motiv). "
                            f"Höhe: {sun_pos.altitude:.1f}°. ACHTUNG: ND-Filter!"
                        ),
                        shoot_time=align_time,
                        shoot_window_start=align_time - timedelta(minutes=5),
                        shoot_window_end=align_time + timedelta(minutes=10),
                        overall_score=round(overall_sa, 2),
                        astronomy_score=0.85,
                        weather_score=round(w_s, 2),
                        location_score=1.0,
                        camera_hints=_camera_hints_alignment(focal_mm, is_solar=True),
                        subject_azimuth=round(subject_az, 1),
                        celestial_azimuth=round(sun_pos.azimuth, 1),
                        celestial_altitude=round(sun_pos.altitude, 1),
                        astronomy_report=astro,
                        alert_priority=2,
                    ))

    # -----------------------------------------------------------------------
    # 5. MILCHSTRASSE (nur bei dunklen Locations)
    # -----------------------------------------------------------------------
    if mw.visible and mw.darkness_score > 0.4:
        w_s = _w_score(forecast, mw.best_visibility_start or datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc), use_weather)
        a_s = mw.darkness_score
        overall_mw = _overall(a_s, w_s, use_weather)

        if overall_mw >= min_score:
            shoot_t = mw.best_visibility_start or datetime.combine(
                target_date, datetime.min.time(), tzinfo=timezone.utc
            ) + timedelta(hours=1)

            # US-92: Neumond-Override bei Milchstraße-Events
            mw_event_type = EventType.MILKY_WAY
            mw_special = _moon_phase_special_event_type(moon.phase_fraction, shoot_t)
            if mw_special == EventType.NEW_MOON:
                mw_event_type = EventType.NEW_MOON

            opportunities.append(PhotoOpportunity(
                id=f"{location.id}_milkyway_{target_date.isoformat()}",
                location=location,
                event_type=mw_event_type,
                title=f"Milchstraße über {location.name}",
                description=(
                    f"Galaktisches Zentrum bei Azimut {mw.galactic_center_azimuth_at_midnight}°, "
                    f"Höhe {mw.galactic_center_altitude_at_midnight}°. "
                    f"Dunkel-Score: {mw.darkness_score:.0%}. Mondphase: {moon.phase_name}."
                ),
                shoot_time=shoot_t,
                shoot_window_start=mw.best_visibility_start or shoot_t,
                shoot_window_end=mw.best_visibility_end or (shoot_t + timedelta(hours=4)),
                overall_score=round(overall_mw, 2),
                astronomy_score=round(a_s, 2),
                weather_score=round(w_s, 2),
                location_score=1.0,
                camera_hints=_camera_hints_milkyway(),
                celestial_azimuth=mw.galactic_center_azimuth_at_midnight,
                celestial_altitude=mw.galactic_center_altitude_at_midnight,
                astronomy_report=astro,
                alert_priority=2 if overall_mw > 0.6 else 1,
            ))

    # -----------------------------------------------------------------------
    # 6. METEORITENSCHAUER
    # -----------------------------------------------------------------------
    for shower in astro.active_meteor_showers:
        days_to_peak = abs((shower.peak_date - target_date).days)
        peak_factor = max(0.3, 1.0 - days_to_peak * 0.15)
        moon_factor = _score_moon_phase_for_milkyway(moon.phase_fraction)

        w_s = _w_score(forecast, datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=1), use_weather)
        a_s = peak_factor * moon_factor
        overall_met = _overall(a_s, w_s, use_weather)

        if overall_met >= min_score:
            midnight_utc = datetime.combine(
                target_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
            )
            opportunities.append(PhotoOpportunity(
                id=f"{location.id}_meteor_{shower.name}_{target_date.isoformat()}",
                location=location,
                event_type=EventType.METEOR_SHOWER,
                title=f"{shower.name} – Meteor-Foto bei {location.name}",
                description=(
                    f"{shower.name}: Maximum {shower.peak_date.strftime('%d. %B')} "
                    f"(ZHR ~{shower.zhr}/h). Radiant im {shower.radiant_constellation}. "
                    f"Mondphase: {moon.phase_name} ({moon.illumination_pct:.0f}%)."
                ),
                shoot_time=midnight_utc,
                shoot_window_start=midnight_utc - timedelta(hours=2),
                shoot_window_end=midnight_utc + timedelta(hours=3),
                overall_score=round(overall_met, 2),
                astronomy_score=round(a_s, 2),
                weather_score=round(w_s, 2),
                location_score=1.0,
                camera_hints=_camera_hints_meteor(),
                astronomy_report=astro,
                alert_priority=2 if days_to_peak <= 1 and moon_factor > 0.7 else 1,
            ))

    # Sortierung nach Gesamtscore (absteigend)
    opportunities.sort(key=lambda o: o.overall_score, reverse=True)
    return opportunities


def _fmt_time(dt: datetime) -> str:
    """Formatiert UTC-Zeit als HH:MM."""
    local = dt + timedelta(hours=2)  # CEST Annäherung (vereinfacht)
    return local.strftime("%H:%M")


async def find_opportunities_multi_day(
    location: PhotoLocation,
    start_date: date,
    days: int,
    forecast: WeatherForecast,
    min_score: float = 0.35,
    astronomy_only: bool = False,
) -> list[PhotoOpportunity]:
    """
    Sucht Foto-Chancen für mehrere Tage und gibt die besten zurück.
    astronomy_only=True: Wetter komplett ignorieren (für Jahreskalender).
    """
    import asyncio as _asyncio
    import os as _os
    from calculations import astronomy as _astro

    # TASK-25: On-Demand Window-Engine (Feature-Flag). Wenn aktiv, werden Sonne/
    # Mond/Milchstraße einmal für das ganze Fenster berechnet (statt pro Tag) →
    # ein 14-Tage-Plan rechnet in Sub-Sekunden (AK1). Standard: aus (Alt-Pfad).
    _use_window = _os.getenv("FOTOALERT_ONDEMAND", "0") == "1"
    _window = None
    if _use_window:
        try:
            from calculations.window_engine import WindowEphemeris
            _window = WindowEphemeris(location.observer_lat, location.observer_lon,
                                      start_date, days)
            _astro.set_active_window(_window)
        except Exception:
            _window = None

    try:
        all_opps: list[PhotoOpportunity] = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            opps = await find_opportunities(location, d, forecast, min_score, astronomy_only=astronomy_only)
            all_opps.extend(opps)
            # Event Loop freigeben alle 7 Tage – verhindert Blocking bei langen Scans
            if i % 7 == 0:
                await _asyncio.sleep(0)
    finally:
        if _window is not None:
            _astro.clear_active_window()

    # Sortierung: Datum aufsteigend, innerhalb eines Tages Score absteigend
    all_opps.sort(key=lambda o: (o.shoot_time.date(), -o.overall_score))
    return all_opps
