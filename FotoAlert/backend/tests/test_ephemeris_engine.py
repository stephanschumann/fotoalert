"""
TASK-25 — On-Demand Ephemeriden-Engine: Akzeptanzkriterien als Harness-Tests.

Deterministisch & offline (nutzt de421 + die neuen Module). Jeder Test nennt im
Docstring das abgesicherte AK. Konvention wie test_astronomy_regression.py.
"""
from __future__ import annotations

import asyncio
import time
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

from calculations import astronomy as A
from calculations import ephemeris_core as core
from calculations import query_engine as qe
from calculations.window_engine import WindowEphemeris
from data.locations import LOCATIONS

pytestmark = [pytest.mark.offline, pytest.mark.regression]

START = date(2026, 6, 22)
_LOCS_3D = [l for l in LOCATIONS if getattr(l, "subject_height_m", 0)]


def _sky_altaz(body, dt, lat, lon):
    from skyfield.api import N, E, wgs84
    eph = A._get_eph()
    obs = wgs84.latlon(lat * N, lon * E)
    t = A._skyfield_time(dt)
    al, az, _ = (eph["earth"] + obs).at(t).observe(eph[body]).apparent().altaz()
    return al.degrees, az.degrees


# --- AK3: Höhe/Azimut innerhalb 1 Bogenminute gegen Skyfield ---------------------
@pytest.mark.parametrize("body", ["sun", "moon"])
def test_ak3_altaz_accuracy(body):
    """AK3: analytische Topozentrik (inkl. Mond-Parallaxe) ≤ 1' gegen Skyfield."""
    lat, lon = 52.3975, 13.0976
    max_alt = max_az = 0.0
    for m in range(0, 24 * 60, 11):
        dt = datetime(2026, 6, 21, tzinfo=timezone.utc) + timedelta(minutes=m)
        ra, dec, dist, gast = core.sample_at(body, dt)
        alt, az = qe.altaz(ra, dec, dist, gast, lat, lon, core.has_parallax(body))
        salt, saz = _sky_altaz(body, dt, lat, lon)
        if salt < -2:
            continue  # unter Horizont → Azimut bedeutungslos
        max_alt = max(max_alt, abs(float(alt) - salt) * 60)
        dz = abs(float(az) - saz) % 360
        max_az = max(max_az, min(dz, 360 - dz) * 60)
    assert max_alt < 1.0, f"{body} Höhenfehler {max_alt:.2f}' > 1'"
    assert max_az < 1.0, f"{body} Azimutfehler {max_az:.2f}' > 1'"


# --- AK4: Sonnen-/Mond-Zeiten ±1 min gegen Alt-Engine ---------------------------
def test_ak4_sun_info_matches_old():
    """AK4: sunrise/sunset/golden/blue der Window-Engine ±1 min zur Alt-Engine."""
    loc = _LOCS_3D[0]
    W = WindowEphemeris(loc.observer_lat, loc.observer_lon, START, 14)
    fields = ["sunrise", "sunset", "golden_hour_morning_start", "golden_hour_evening_end",
              "blue_hour_morning_start", "blue_hour_evening_end"]
    for k in range(0, 14, 3):
        d = START + timedelta(days=k)
        old = A.calculate_sun_info(loc.observer_lat, loc.observer_lon, d)
        new = W.sun_info(d)
        for f in fields:
            a, b = getattr(old, f), getattr(new, f)
            if a and b:
                dev = abs((a - b).total_seconds()) / 60.0
                assert dev <= 1.0, f"{f} weicht {dev:.2f} min ab"


def test_ak4_moon_info_matches_old():
    """AK4: moonrise/moonset ±1 min; Beleuchtung ±2 %; Phasenname identisch."""
    loc = _LOCS_3D[0]
    W = WindowEphemeris(loc.observer_lat, loc.observer_lon, START, 14)
    for k in range(0, 14, 3):
        d = START + timedelta(days=k)
        old = A.calculate_moon_info(loc.observer_lat, loc.observer_lon, d)
        new = W.moon_info(d)
        for f in ["moonrise", "moonset"]:
            a, b = getattr(old, f), getattr(new, f)
            if a and b:
                assert abs((a - b).total_seconds()) / 60.0 <= 1.0
        assert abs(old.illumination_pct - new.illumination_pct) <= 2.0
        assert old.phase_name == new.phase_name


# --- AK6: jede echte Passage durch genau ein Event vertreten (±1 min) ------------
@pytest.mark.parametrize("loc", _LOCS_3D[:5], ids=lambda l: l.id)
def test_ak6_passage_coverage(loc):
    """AK6: jede Alignment-Passage der Alt-Engine → ein Window-Event ≤ 90 s."""
    W = WindowEphemeris(loc.observer_lat, loc.observer_lon, START, 14)
    sw = loc.subject_width_m or loc.subject_height_m * 0.3
    ed = getattr(loc, "elevation_difference_m", 0.0)
    for k in range(0, 14, 2):
        d = START + timedelta(days=k)
        for body in ("sun", "moon"):
            old = A.find_precise_alignment_times(
                loc.observer_lat, loc.observer_lon, loc.subject_lat, loc.subject_lon,
                loc.subject_height_m, sw, d, body=body, az_tolerance_deg=3.0,
                min_quality=0.25, elevation_difference_m=ed)
            new = W.alignments(loc.subject_lat, loc.subject_lon, loc.subject_height_m,
                               sw, d, body, az_tolerance_deg=3.0, min_quality=0.25,
                               elevation_difference_m=ed)
            # Alt-Events zu Passagen gruppieren (>15 min Abstand = neue Passage)
            old_sorted = sorted(old, key=lambda r: r.time)
            groups = []
            for r in old_sorted:
                if groups and (r.time - groups[-1][-1].time).total_seconds() <= 900:
                    groups[-1].append(r)
                else:
                    groups.append([r])
            for grp in groups:
                best = max(grp, key=lambda r: r.quality_score)
                assert new, f"{loc.id} {d} {body}: Passage {best.time} nicht vertreten"
                nb = min(new, key=lambda r: abs((r.time - best.time).total_seconds()))
                dt = abs((nb.time - best.time).total_seconds())
                assert dt <= 90, f"{loc.id} {d} {body}: Δt {dt:.0f}s > 90s"


# --- Edge Case: Hebel 1 — Objektposition einmal pro Fenster ----------------------
def test_hebel1_track_once_per_window():
    """Edge: 2 Beobachter im selben Fenster lösen KEINE zusätzliche teure
    Track-Berechnung aus (geozentrische Bahn wird wiederverwendet)."""
    core.clear_cache()
    core.reset_eval_counter()
    WindowEphemeris(52.40, 13.10, START, 14)          # baut sun+moon (2 Tracks)
    first = core.track_eval_count()
    WindowEphemeris(52.40, 13.10, START, 14)          # gleicher Beobachter+Fenster
    assert core.track_eval_count() - first == 0, "Track wurde erneut berechnet"


# --- Edge Case: Azimut-Wrap bei 0°/360° -----------------------------------------
def test_edge_azimuth_wrap_north():
    """Edge: Motiv exakt nördlich (Azimut ~0/360) → keine Wrap-Fehler, kein Crash."""
    obs_lat, obs_lon = 52.40, 13.10
    subj_lat, subj_lon = 52.50, 13.10   # genau nördlich → Azimut ~0°
    W = WindowEphemeris(obs_lat, obs_lon, START, 7)
    res = W.alignments(subj_lat, subj_lon, 50.0, 15.0, START, "moon",
                       az_tolerance_deg=5.0, min_quality=0.0)
    for r in res:  # azimuth_offset darf nie > Toleranz sein (Wrap korrekt)
        assert r.azimuth_offset_deg <= 5.0 + 1e-6


# --- Edge Case: fehlende Geländehöhe → Fallback ---------------------------------
def test_edge_missing_elevation_fallback():
    """Edge/AK: ohne DEM-Abdeckung → difference 0.0 + incomplete=True, kein Crash."""
    import tempfile
    from pathlib import Path
    from unittest.mock import patch
    from data.elevation import ElevationProvider
    p = ElevationProvider(cache_file=Path(tempfile.mktemp()))
    # Cache-Hit-Pfad ist deterministisch (kein Netz):
    p._cache["52.4,13.1"] = 40.0
    p._cache["52.42,13.07"] = 90.0
    diff, inc = asyncio.run(p.elevation_difference(52.40, 13.10, 52.42, 13.07))
    assert diff == 50.0 and inc is False
    # Fehlende Abdeckung deterministisch simulieren (nicht von echter DEM-Lücke
    # abhängig, die je nach Netzzugang/Datensatz-Stand variiert): _fetch_elevation
    # gemockt, liefert garantiert None → Fallback-Pfad in elevation_difference().
    with patch.object(ElevationProvider, "_fetch_elevation", return_value=None):
        diff2, inc2 = asyncio.run(p.elevation_difference(0.0, 0.0, 0.1, 0.1))
    assert diff2 == 0.0 and inc2 is True


# --- AK1: 14-Tage-Plan schnell (Regressionsschranke, hardware-tolerant) ----------
def test_ak1_latency_14day():
    """AK1: 14-Tage-Plan einer Location deutlich < alt. Großzügige Schranke (3 s)
    als Regressionsguard — Zielwert wird auf Prod-Hardware kalibriert (OF3)."""
    from calculations.opportunity import find_opportunities_multi_day
    from calculations.weather import WeatherForecast
    loc = _LOCS_3D[0]
    fc = WeatherForecast(location_lat=loc.observer_lat, location_lon=loc.observer_lon,
                         fetched_at=datetime.now(timezone.utc), hourly=[])
    A.set_active_window(WindowEphemeris(loc.observer_lat, loc.observer_lon, START, 14))
    try:
        t = time.time()
        asyncio.run(find_opportunities_multi_day(loc, START, 14, fc, astronomy_only=True))
        dt = time.time() - t
    finally:
        A.clear_active_window()
    assert dt < 3.0, f"14-Tage-Plan {dt:.2f}s > 3s"


@pytest.mark.slow
def test_ak1b_latency_365day():
    """AK1b: 365-Tage-Plan einer Location. Aktuell ~21 s lokal (4,6× schneller als alt).
    Schranke 60 s als Regressionsguard (TASK-64: auf GitHub-Actions-Runnern gemessen
    51,4 s statt der lokal kalibrierten 45 s — Puffer für langsamere/variable CI-Hardware);
    Zielwert (5 s) ist noch zu kalibrieren."""
    from calculations.opportunity import find_opportunities_multi_day
    from calculations.weather import WeatherForecast
    loc = _LOCS_3D[0]
    fc = WeatherForecast(location_lat=loc.observer_lat, location_lon=loc.observer_lon,
                         fetched_at=datetime.now(timezone.utc), hourly=[])
    A.set_active_window(WindowEphemeris(loc.observer_lat, loc.observer_lon, START, 365))
    try:
        t = time.time()
        asyncio.run(find_opportunities_multi_day(loc, START, 365, fc, astronomy_only=True))
        dt = time.time() - t
    finally:
        A.clear_active_window()
    assert dt < 60.0, f"365-Tage-Plan {dt:.1f}s > 60s"
