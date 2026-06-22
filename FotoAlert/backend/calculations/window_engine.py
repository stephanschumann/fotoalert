"""
FotoAlert – Window Engine (TASK-25, Option B, AK1-Pfad)

On-Demand-Berechnung eines kompletten Plans (mehrere Tage) für EINEN Beobachter,
ohne Batch-Vorberechnung. Kernidee: die geozentrischen Bahnen von Sonne, Mond und
galaktischem Zentrum werden für das GANZE Fenster in je einem Skyfield-Call
berechnet (statt pro Tag neu), per-Beobachter einmal in alt/az transformiert
(reine numpy-Trigonometrie), und alle Tages-Primitive (SunInfo, MoonInfo,
MilkyWayInfo, Body-Position, Alignments) werden daraus abgeleitet.

Messung (14 Tage, eine Location): 3 Tracks ~0,2 s, Trig <1 ms → Plan < 500 ms (AK1).

Alignment-Semantik (AK6, von Stephan 2026-06-22 freigegeben): EIN Event pro
echter Passage am Qualitätsmaximum (±1 min), keine bit-genaue Nachbildung der
alten 1-Min-Raster-Aufzählung.

Die Engine wird über `astronomy.set_active_window(...)` aktiviert; die bestehenden
Primitive in `astronomy.py`/`opportunity.py` delegieren dann hierher — die
Scoring-/Ausgabe-Logik in `find_opportunities` bleibt unangetastet (AK7).

Python-3.9-kompatibel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np

from . import ephemeris_core as core
from . import query_engine as qe
from .astronomy import (
    AlignmentResult,
    CelestialPosition,
    MilkyWayInfo,
    MoonInfo,
    SunInfo,
    _classify_alignment,
    _moon_phase_name,
    calculate_subject_angular_profile,
    get_active_meteor_showers,
)

_OBLIQUITY_DEG = 23.4393  # mittlere Ekliptikschiefe (ausreichend für Phase)


def _interp_angle(x, xp, deg_values):
    """Winkel-Interpolation (Grad) über sin/cos → wrap-sicher."""
    rad = np.radians(deg_values)
    s = np.interp(x, xp, np.sin(rad))
    c = np.interp(x, xp, np.cos(rad))
    return np.degrees(np.arctan2(s, c)) % 360.0


@dataclass
class _BodyArrays:
    alt: np.ndarray
    az: np.ndarray
    ra_hours: np.ndarray
    dec_deg: np.ndarray
    dist_au: np.ndarray


class WindowEphemeris:
    """Vorberechnete Bahnen + per-Beobachter alt/az für ein Zeitfenster."""

    def __init__(self, lat: float, lon: float, start_date: date, days: int,
                 coarse_step_min: int = 10):
        self.lat = lat
        self.lon = lon
        self.start_date = start_date
        self.days = days
        self.step = coarse_step_min
        self.t0 = datetime(start_date.year, start_date.month, start_date.day,
                           0, 0, tzinfo=timezone.utc)
        t1 = self.t0 + timedelta(days=days)
        self.n = int(days * 24 * 60 / coarse_step_min) + 1
        self.minutes = np.arange(self.n, dtype=float) * coarse_step_min
        self._t1 = t1
        self._bodies: Dict[str, _BodyArrays] = {}
        # Sonne + Mond eager (fast immer gebraucht); Milchstraße lazy
        # (nur bei sichtbarem GC / explizitem Bedarf) → spart ~1/3 Aufbauzeit.
        for body in ("sun", "moon"):
            self._build(body)

    def _build(self, body: str) -> "_BodyArrays":
        tr = core.compute_track(body, self.t0, self._t1, self.n)
        alt, az = qe.altaz(tr.ra_hours, tr.dec_deg, tr.distance_au,
                           tr.gast_hours, self.lat, self.lon, core.has_parallax(body))
        arr = _BodyArrays(
            alt=np.asarray(alt), az=np.asarray(az),
            ra_hours=tr.ra_hours, dec_deg=tr.dec_deg, dist_au=tr.distance_au,
        )
        self._bodies[body] = arr
        return arr

    def _body(self, key: str) -> "_BodyArrays":
        arr = self._bodies.get(key)
        if arr is None:
            arr = self._build(key)
        return arr

    # ---- Abdeckung -------------------------------------------------------
    def covers(self, lat: float, lon: float, d: date) -> bool:
        return (abs(lat - self.lat) < 1e-9 and abs(lon - self.lon) < 1e-9
                and self.start_date <= d < self.start_date + timedelta(days=self.days))

    def _abs_minutes(self, dt: datetime) -> float:
        return (dt.astimezone(timezone.utc) - self.t0).total_seconds() / 60.0

    # ---- Body-Position (interpoliert) ------------------------------------
    def body_position(self, body: str, dt: datetime) -> Optional[CelestialPosition]:
        key = "milkyway" if body == "milkyway" else body
        if key not in ("sun", "moon", "milkyway"):
            from .astronomy import _get_body_position_direct as _gbp  # planets etc.
            return _gbp(self.lat, self.lon, body, dt)
        b = self._body(key)
        m = self._abs_minutes(dt)
        alt = float(np.interp(m, self.minutes, b.alt))
        az = float(_interp_angle(m, self.minutes, b.az))
        dist = float(np.interp(m, self.minutes, b.dist_au))
        return CelestialPosition(azimuth=az, altitude=alt, distance_au=dist)

    # ---- Crossing-Finder auf dem Höhen-Array -----------------------------
    def _day_slice(self, d: date):
        k = (d - self.start_date).days
        lo = k * (24 * 60 // self.step)
        hi = lo + (24 * 60 // self.step) + 1
        return lo, min(hi, self.n)

    def _crossing(self, body: str, d: date, threshold: float, rising: bool,
                  after: Optional[datetime] = None,
                  before: Optional[datetime] = None) -> Optional[datetime]:
        b = self._bodies[body]
        lo, hi = self._day_slice(d)
        mins = self.minutes[lo:hi]
        alt = b.alt[lo:hi]
        g = alt - threshold
        a_min = self._abs_minutes(after) if after else mins[0]
        b_min = self._abs_minutes(before) if before else mins[-1]
        for i in range(len(g) - 1):
            if mins[i] < a_min - self.step or mins[i] > b_min:
                continue
            g0, g1 = g[i], g[i + 1]
            if g0 == 0.0:
                return self.t0 + timedelta(minutes=float(mins[i]))
            cross_up = g0 < 0 <= g1
            cross_dn = g0 > 0 >= g1
            if (rising and cross_up) or (not rising and cross_dn):
                # lineare Interpolation des Nulldurchgangs
                frac = g0 / (g0 - g1)
                mcross = mins[i] + frac * self.step
                if a_min - 1e-6 <= mcross <= b_min + 1e-6:
                    return self.t0 + timedelta(minutes=float(mcross))
        return None

    # ---- SunInfo ---------------------------------------------------------
    def sun_info(self, d: date) -> SunInfo:
        ymd = (d.year, d.month, d.day)
        sunrise = self._crossing("sun", d, -0.8333, True)
        sunset = self._crossing("sun", d, -0.8333, False,
                                after=(sunrise or self.t0))
        if sunrise is None:
            sunrise = datetime(*ymd, 6, 0, tzinfo=timezone.utc)
        if sunset is None:
            sunset = datetime(*ymd, 20, 0, tzinfo=timezone.utc)
        mid = sunrise + (sunset - sunrise) / 2
        day_length = (sunset - sunrise).total_seconds() / 3600

        ghe_m_start = self._crossing("sun", d, -4.0, True, before=sunrise + timedelta(hours=2))
        ghe_m_end = self._crossing("sun", d, 6.0, True, before=sunrise + timedelta(hours=2))
        ghe_e_start = self._crossing("sun", d, 6.0, False, after=sunset - timedelta(hours=2))
        ghe_e_end = self._crossing("sun", d, -4.0, False, after=sunset - timedelta(hours=2))
        bh_m_start = self._crossing("sun", d, -6.0, True, before=sunrise + timedelta(hours=1))
        bh_e_end = self._crossing("sun", d, -6.0, False, after=sunset - timedelta(hours=1))

        return SunInfo(
            date=d, sunrise=sunrise, sunset=sunset,
            golden_hour_morning_start=ghe_m_start or (sunrise - timedelta(minutes=20)),
            golden_hour_morning_end=ghe_m_end or (sunrise + timedelta(minutes=40)),
            golden_hour_evening_start=ghe_e_start or (sunset - timedelta(minutes=40)),
            golden_hour_evening_end=ghe_e_end or (sunset + timedelta(minutes=20)),
            blue_hour_morning_start=bh_m_start or (sunrise - timedelta(minutes=40)),
            blue_hour_morning_end=ghe_m_start or (sunrise - timedelta(minutes=10)),
            blue_hour_evening_start=ghe_e_end or (sunset + timedelta(minutes=10)),
            blue_hour_evening_end=bh_e_end or (sunset + timedelta(minutes=40)),
            solar_noon=mid, day_length_hours=day_length,
        )

    # ---- MoonInfo --------------------------------------------------------
    def _ecliptic_lon(self, body: str, m: float) -> float:
        b = self._bodies[body]
        ra = math.radians(float(np.interp(m, self.minutes, b.ra_hours)) * 15.0)
        dec = math.radians(float(np.interp(m, self.minutes, b.dec_deg)))
        eps = math.radians(_OBLIQUITY_DEG)
        lam = math.atan2(math.sin(ra) * math.cos(eps) + math.tan(dec) * math.sin(eps),
                         math.cos(ra))
        return math.degrees(lam) % 360.0

    def moon_info(self, d: date, sun_info: Optional[SunInfo] = None) -> MoonInfo:
        moonrise = self._crossing("moon", d, -0.5667, True)
        moonset = self._crossing("moon", d, -0.5667, False, after=(moonrise or self.t0))
        # Phase zur Mitternacht (12:00 UTC, wie Alt-Engine)
        m_noon = self._abs_minutes(datetime(d.year, d.month, d.day, 12, 0, tzinfo=timezone.utc))
        elong = (self._ecliptic_lon("moon", m_noon) - self._ecliptic_lon("sun", m_noon)) % 360
        phase_fraction = elong / 360.0
        illumination = (1 - math.cos(math.radians(elong))) / 2 * 100

        if sun_info is None:
            sun_info = self.sun_info(d)
        gh_time = sun_info.golden_hour_evening_start
        mpos = self.body_position("moon", gh_time)
        return MoonInfo(
            date=d, moonrise=moonrise, moonset=moonset,
            phase_fraction=phase_fraction,
            phase_name=_moon_phase_name(phase_fraction),
            illumination_pct=round(illumination, 1),
            azimuth_at_golden_hour=round(mpos.azimuth, 1) if mpos else None,
            altitude_at_golden_hour=round(mpos.altitude, 1) if mpos else None,
        )

    # ---- MilkyWayInfo ----------------------------------------------------
    def milky_way_info(self, d: date, sun_info: Optional[SunInfo] = None,
                       moon_info: Optional[MoonInfo] = None) -> MilkyWayInfo:
        if sun_info is None:
            sun_info = self.sun_info(d)
        if moon_info is None:
            moon_info = self.moon_info(d, sun_info=sun_info)
        midnight = datetime(d.year, d.month, d.day, 22, 0, tzinfo=timezone.utc)
        gc = self.body_position("milkyway", midnight)
        az_deg, alt_deg = gc.azimuth, gc.altitude
        visible = alt_deg > 5.0
        seasonal = 1.0 if 4 <= d.month <= 9 else 0.3
        moon_factor = 1.0 - (moon_info.illumination_pct / 100) * 0.8
        darkness = min(1.0, seasonal * moon_factor * (1.0 if visible else 0.2))
        return MilkyWayInfo(
            date=d,
            galactic_center_azimuth_at_midnight=round(az_deg, 1) if visible else None,
            galactic_center_altitude_at_midnight=round(alt_deg, 1) if visible else None,
            best_visibility_start=sun_info.blue_hour_evening_end,
            best_visibility_end=sun_info.blue_hour_morning_start,
            darkness_score=round(darkness, 2),
            visible=visible and darkness > 0.3,
        )

    # ---- Alignment: ein Event pro Passage am Qualitätsmaximum (AK6) ------
    def alignments(self, subject_lat: float, subject_lon: float,
                   subject_height_m: float, subject_width_m: float,
                   d: date, body: str, az_tolerance_deg: float = 3.0,
                   min_quality: float = 0.2, elevation_difference_m: float = 0.0,
                   ) -> List[AlignmentResult]:
        profile = calculate_subject_angular_profile(
            self.lat, self.lon, subject_lat, subject_lon,
            subject_height_m, subject_width_m,
            elevation_difference_m=elevation_difference_m,
        )
        b = self._bodies["moon" if body == "moon" else "sun"]
        lo, hi = self._day_slice(d)
        # Sonne wie Alt-Engine nur 4–21 Uhr betrachten
        mins = self.minutes[lo:hi]
        alt = b.alt[lo:hi]
        az = b.az[lo:hi]
        if body != "moon":
            day_min0 = (d - self.start_date).days * 24 * 60
            in_win = (mins >= day_min0 + 4 * 60) & (mins <= day_min0 + 21 * 60)
            mins, alt, az = mins[in_win], alt[in_win], az[in_win]

        azoff = np.abs((az - profile.azimuth_deg + 180) % 360 - 180)
        in_band = (azoff <= az_tolerance_deg) & (alt >= -1.0)

        # Tagesfenster-Grenzen (wie Alt-Engine: Mond 0–23:59, Sonne 4–21 Uhr).
        # Der feine Scan darf NICHT über die Tagesgrenze laufen, sonst würde ein
        # Event nahe Mitternacht auf zwei Tagen emittiert (Plan-Duplikat).
        day0 = (d - self.start_date).days * 24 * 60
        if body == "moon":
            day_lo, day_hi = day0, day0 + 24 * 60 - 1
        else:
            day_lo, day_hi = day0 + 4 * 60, day0 + 21 * 60

        results: List[AlignmentResult] = []
        i = 0
        N = len(in_band)
        while i < N:
            if not in_band[i]:
                i += 1
                continue
            j = i
            while j + 1 < N and in_band[j + 1]:
                j += 1
            # Passage [i..j] → bestes in-band Sample per feinem 1-Min-Scan
            res = self._best_in_passage(
                body, profile, mins[i], mins[j], az_tolerance_deg, min_quality,
                day_lo, day_hi)
            if res is not None:
                results.append(res)
            i = j + 1

        results.sort(key=lambda r: -r.quality_score)
        return results

    # ---- Azimut-Kreuzungen (für find_sun/moon_alignment_times) -----------
    # Reproduziert die Alt-Semantik exakt: 1-Min-Raster (hier per Interpolation
    # aus dem 5-Min-Array, da alt/az glatt sind), Maske alt>alt_min & az≤tol,
    # Dedup pro 5 Min. So bleiben die minutengenauen Opportunity-IDs erhalten.
    def azimuth_times(self, body: str, target_az: float, d: date,
                      tolerance_deg: float = 2.0, alt_min: float = 0.0,
                      hours=(0, 24)) -> List[datetime]:
        b = self._bodies["moon" if body == "moon" else "sun"]
        lo, hi = self._day_slice(d)
        mins = self.minutes[lo:hi]
        day0 = (d - self.start_date).days * 24 * 60
        fine = np.arange(day0 + hours[0] * 60, day0 + hours[1] * 60, 1.0)
        alt = np.interp(fine, mins, b.alt[lo:hi])
        az = _interp_angle(fine, mins, b.az[lo:hi])
        azdiff = np.abs((az - target_az + 180) % 360 - 180)
        mask = (alt > alt_min) & (azdiff <= tolerance_deg)
        # AK6-Semantik: pro zusammenhängender Passage EIN Event an der engsten
        # Azimut-Annäherung (statt Mehrfach-Events durch 5-Min-Dedup).
        out: List[datetime] = []
        i, N = 0, len(mask)
        while i < N:
            if not mask[i]:
                i += 1
                continue
            j = i
            while j + 1 < N and mask[j + 1]:
                j += 1
            seg = azdiff[i:j + 1]
            best = i + int(np.argmin(seg))
            out.append(self.t0 + timedelta(minutes=float(fine[best])))
            i = j + 1
        return out

    def _quality_at(self, body, profile, m: float):
        dt = self.t0 + timedelta(minutes=float(m))
        pos = self.body_position(body, dt)
        azoff = abs((pos.azimuth - profile.azimuth_deg + 180) % 360 - 180)
        atype, q = _classify_alignment(pos.altitude, profile, azoff)
        return dt, pos, azoff, atype, q

    def _best_in_passage(self, body, profile, m_lo: float, m_hi: float,
                         az_tol: float, min_q: float,
                         day_lo: float = None, day_hi: float = None):
        # Feiner 1-Min-Scan über [m_lo-step, m_hi+step]; bestes gültiges (in-band,
        # alt>=-1, q>=min_q) Sample am Qualitätsmaximum. Robust gegen monotone
        # Qualitätsverläufe (Peak am Rand) — entspricht OLD „bester Sample".
        best = None
        m = m_lo - self.step
        end = m_hi + self.step
        if day_lo is not None:
            m = max(m, day_lo)
        if day_hi is not None:
            end = min(end, day_hi)
        while m <= end + 1e-9:
            dt, pos, azoff, atype, q = self._quality_at(body, profile, m)
            if azoff <= az_tol and pos.altitude >= -1.0 and q >= min_q:
                if best is None or q > best[4]:
                    best = (dt, pos, azoff, atype, q)
            m += 1.0
        if best is None:
            return None
        dt, pos, azoff, atype, q = best
        return AlignmentResult(
            time=dt, body=body, alignment_type=atype,
            celestial_azimuth=round(pos.azimuth, 2),
            celestial_altitude=round(pos.altitude, 3),
            azimuth_offset_deg=round(azoff, 2),
            altitude_offset_deg=round(pos.altitude - profile.angular_altitude_top_deg, 3),
            quality_score=q, subject_profile=profile,
        )
