"""
FotoAlert – Location Query Engine (TASK-25, Option B)

Standortabhängige, stateless Schicht der On-Demand-Engine.

Nimmt die geozentrische Bahn aus `ephemeris_core` und macht daraus für einen
konkreten Beobachter Höhe/Azimut (reine Trigonometrie), inkl.:
  • topozentrischer Parallaxe (Mond, bis ~1°)  → SHALL-4
  • Event-Rootfinding (Grobraster + Bisektion) statt 1-Min-Scan → SHALL-3
Die Ausgabe ist formatgleich zur Alt-Engine (`AlignmentResult`) → Drop-in.

Refraktion: Wie die Alt-Engine (`apparent().altaz()` ohne Druck/Temperatur)
arbeiten wir mit *airless* Höhen; die ±0,833°-Refraktion steckt – wie bisher –
in den Auf-/Untergangs-Schwellen der Sonnen-/Mondinfo, nicht in alt/az.

Python-3.9-kompatibel.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple

import numpy as np

from . import ephemeris_core as core
from .astronomy import (
    AlignmentResult,
    SubjectAngularProfile,
    _classify_alignment,
    calculate_subject_angular_profile,
)

# Grobraster fürs Rootfinding (Spec: 5–10 min; konservativ 5 min, damit keine
# eng beieinanderliegenden Alignments verschluckt werden – Pre-Mortem).
COARSE_STEP_MIN = 5
# Bisektions-Genauigkeit für den Azimut-Nulldurchgang.
REFINE_SECONDS = 10


# ---------------------------------------------------------------------------
# Topozentrische Horizonttransformation (vektorisierbar via numpy)
# ---------------------------------------------------------------------------

def _observer_geo_terms(lat_deg: float) -> Tuple[float, float]:
    """ρ·sinφ' und ρ·cosφ' nach Meeus (Erdabplattung berücksichtigt)."""
    lat_r = math.radians(lat_deg)
    u = math.atan(0.99664719 * math.tan(lat_r))
    rho_sin = 0.99664719 * math.sin(u)
    rho_cos = math.cos(u)
    return rho_sin, rho_cos


def altaz(
    ra_hours, dec_deg, dist_au, gast_hours,
    lat_deg: float, lon_deg: float, apply_parallax: bool,
):
    """
    Geozentrische scheinbare α/δ → topozentrische airless Höhe/Azimut.
    Akzeptiert Skalare oder numpy-Arrays. Azimut: 0=N, 90=O (wie Skyfield).
    """
    lat_r = math.radians(lat_deg)
    sin_lat, cos_lat = math.sin(lat_r), math.cos(lat_r)

    ra_r = np.radians(np.asarray(ra_hours) * 15.0)
    dec_r = np.radians(np.asarray(dec_deg))
    lst_hours = (np.asarray(gast_hours) + lon_deg / 15.0)
    # Stundenwinkel H = LST − α
    H = np.radians((lst_hours * 15.0)) - ra_r

    if apply_parallax:
        rho_sin, rho_cos = _observer_geo_terms(lat_deg)
        sin_pi = core.EARTH_RADIUS_AU / np.asarray(dist_au)
        cos_dec = np.cos(dec_r)
        # Meeus 40.6 / 40.7: Korrektur in Rektaszension/Deklination
        d_ra = np.arctan2(-rho_cos * sin_pi * np.sin(H),
                          cos_dec - rho_cos * sin_pi * np.cos(H))
        dec_r = np.arctan2((np.sin(dec_r) - rho_sin * sin_pi) * np.cos(d_ra),
                           cos_dec - rho_cos * sin_pi * np.cos(H))
        H = H - d_ra  # H' = H − Δα

    sin_alt = sin_lat * np.sin(dec_r) + cos_lat * np.cos(dec_r) * np.cos(H)
    alt = np.degrees(np.arcsin(np.clip(sin_alt, -1.0, 1.0)))
    # North-based azimuth, clockwise (East positive)
    east = -np.cos(dec_r) * np.sin(H)
    north = np.sin(dec_r) * cos_lat - np.cos(dec_r) * np.cos(H) * sin_lat
    az = np.degrees(np.arctan2(east, north)) % 360.0
    return alt, az


def _altaz_scalar(body, when, lat, lon, apply_parallax):
    ra, dec, dist, gast = core.sample_at(body, when)
    alt, az = altaz(ra, dec, dist, gast, lat, lon, apply_parallax)
    return float(alt), float(az)


def _signed_az_offset(az, target_az: float):
    """Vorzeichenbehaftete Azimut-Differenz in (−180, 180], wrap-sicher."""
    return ((np.asarray(az) - target_az + 180.0) % 360.0) - 180.0


# ---------------------------------------------------------------------------
# Event-Rootfinding: Azimut-Alignment Objekt ↔ Sichtachse Motiv
# ---------------------------------------------------------------------------

def find_precise_alignment_times_v2(
    observer_lat: float, observer_lon: float,
    subject_lat: float, subject_lon: float,
    subject_height_m: float,
    subject_width_m: float,
    target_date: date,
    body: str = "sun",
    az_tolerance_deg: float = 3.0,
    min_quality: float = 0.2,
    resolution_minutes: int = 1,        # nur Signatur-Kompatibilität, ungenutzt
    elevation_difference_m: float = 0.0,
) -> List[AlignmentResult]:
    """
    Drop-in-Ersatz für astronomy.find_precise_alignment_times — gleiche Signatur,
    gleiche Rückgabe (AlignmentResult, sortiert nach Qualität). Statt 1-Min-Scan:
    geozentrischer Track einmal pro Fenster (Hebel 1) + Bisektion (Hebel 2).
    """
    profile = calculate_subject_angular_profile(
        observer_lat, observer_lon, subject_lat, subject_lon,
        subject_height_m, subject_width_m,
        elevation_difference_m=elevation_difference_m,
    )
    apply_par = core.has_parallax(body)

    # Fenster identisch zur Alt-Engine: Sonne 4–21 Uhr, Mond 0–24 Uhr (UTC).
    if body == "moon":
        t0 = datetime(target_date.year, target_date.month, target_date.day, 0, 0, tzinfo=timezone.utc)
        t1 = datetime(target_date.year, target_date.month, target_date.day, 23, 59, tzinfo=timezone.utc)
    else:
        t0 = datetime(target_date.year, target_date.month, target_date.day, 4, 0, tzinfo=timezone.utc)
        t1 = datetime(target_date.year, target_date.month, target_date.day, 21, 0, tzinfo=timezone.utc)

    total_min = (t1 - t0).total_seconds() / 60.0
    n = int(total_min / COARSE_STEP_MIN) + 1
    track = core.compute_track(body, t0, t1, n)

    alt, az = altaz(track.ra_hours, track.dec_deg, track.distance_au,
                    track.gast_hours, observer_lat, observer_lon, apply_par)
    s = _signed_az_offset(az, profile.azimuth_deg)

    grid = [t0 + timedelta(minutes=COARSE_STEP_MIN * i) for i in range(len(s))]

    # Kandidaten-Zeitpunkte sammeln: Nulldurchgänge von s (Azimut trifft Motiv)
    # plus lokale Minima von |s| innerhalb der Toleranz (Grazing ohne Crossing).
    candidates: List[datetime] = []

    def offset_at(when: datetime) -> float:
        _, a = _altaz_scalar(body, when, observer_lat, observer_lon, apply_par)
        return float(_signed_az_offset(a, profile.azimuth_deg))

    for i in range(len(s) - 1):
        s0, s1 = float(s[i]), float(s[i + 1])
        if s0 == 0.0:
            candidates.append(grid[i])
        elif s0 * s1 < 0:
            # Bisektion auf dem vorzeichenwechselnden Intervall
            lo, hi = grid[i], grid[i + 1]
            flo = s0
            while (hi - lo).total_seconds() > REFINE_SECONDS:
                mid = lo + (hi - lo) / 2
                fmid = offset_at(mid)
                if flo * fmid <= 0:
                    hi = mid
                else:
                    lo, flo = mid, fmid
            candidates.append(lo + (hi - lo) / 2)
        else:
            # Grazing: lokales Minimum von |s| im Band, kein Vorzeichenwechsel
            if i == 0:
                continue
            a0, a1, a2 = abs(float(s[i - 1])), abs(s0), abs(s1)
            if a1 <= a0 and a1 <= a2 and a1 <= az_tolerance_deg:
                candidates.append(_ternary_min(offset_at, grid[i - 1], grid[i + 1]))

    # Exakt auswerten, klassifizieren, AlignmentResult bauen
    results: List[AlignmentResult] = []
    for t in candidates:
        a_alt, a_az = _altaz_scalar(body, t, observer_lat, observer_lon, apply_par)
        az_diff = abs(float(_signed_az_offset(a_az, profile.azimuth_deg)))
        if az_diff > az_tolerance_deg or a_alt < -1.0:
            continue
        alignment_type, quality = _classify_alignment(a_alt, profile, az_diff)
        if quality < min_quality:
            continue
        results.append(AlignmentResult(
            time=t.astimezone(timezone.utc),
            body=body,
            alignment_type=alignment_type,
            celestial_azimuth=round(a_az, 2),
            celestial_altitude=round(a_alt, 3),
            azimuth_offset_deg=round(az_diff, 2),
            altitude_offset_deg=round(a_alt - profile.angular_altitude_top_deg, 3),
            quality_score=quality,
            subject_profile=profile,
        ))

    # Duplikate innerhalb 5 Minuten → bestes behalten (wie Alt-Engine)
    results.sort(key=lambda r: r.time)
    unique: List[AlignmentResult] = []
    for r in results:
        if not unique or (r.time - unique[-1].time).total_seconds() > 300:
            unique.append(r)
        elif r.quality_score > unique[-1].quality_score:
            unique[-1] = r

    unique.sort(key=lambda r: -r.quality_score)
    return unique


def _ternary_min(f, lo: datetime, hi: datetime) -> datetime:
    """Minimiert |f| auf [lo, hi] per Ternärsuche bis REFINE_SECONDS."""
    while (hi - lo).total_seconds() > REFINE_SECONDS:
        third = (hi - lo) / 3
        m1 = lo + third
        m2 = hi - third
        if abs(f(m1)) < abs(f(m2)):
            hi = m2
        else:
            lo = m1
    return lo + (hi - lo) / 2
