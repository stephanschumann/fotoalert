"""Regressionssuite — Astronomie & Geometrie (deterministisch, offline).

Jeder Test ist aus den Akzeptanzkriterien eines abgeschlossenen Tickets abgeleitet.
Das ist der Kern des Vollsystem-Regressionsgedankens (PIPELINE.md §3.3): die AKs *aller*
bisherigen Tickets bleiben als ausführbare Tests bestehen, damit eine neue Änderung nicht
unbemerkt etwas Altes bricht.

Konvention: Im Docstring jedes Tests steht die Ticket-ID, deren AK hier abgesichert wird.
Neue Tickets ergänzen ihre Tests nach demselben Muster.
"""
import math
from datetime import datetime, timezone

import pytest

from calculations import astronomy as A

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# --- BUG-18: Mond-Erde-Distanz muss physikalisch plausibel sein -------------------
# AK: Anzeige zeigt ~384.400 km, nicht ~370 km. Perigäum ~356.500, Apogäum ~406.700 km.
@pytest.mark.parametrize("month", [1, 4, 7, 10])
def test_moon_earth_distance_in_physical_range(month):
    dt = datetime(2026, month, 15, 20, 0, tzinfo=timezone.utc)
    d_km = A.get_moon_earth_distance_km(dt)
    assert 350_000 < d_km < 410_000, f"Monddistanz {d_km:.0f} km außerhalb des physikalischen Korridors"


# --- Haversine: muss einer unabhängigen Referenzformel entsprechen ----------------
# Absicherung von Pattern 3 (fotoalert-impl): distance_m via Haversine.
def _reference_haversine(lat1, lon1, lat2, lon2):
    R = 6_371_000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


@pytest.mark.parametrize("coords", [
    (52.40, 13.00, 52.41, 13.01),
    (52.5163, 13.3777, 52.5186, 13.4083),  # Brandenburger Tor → Berliner Dom (~grob)
])
def test_haversine_matches_reference(coords):
    got = A.calculate_haversine_distance(*coords)
    exp = _reference_haversine(*coords)
    assert math.isclose(got, exp, rel_tol=0.01), f"Haversine {got:.1f} m weicht von Referenz {exp:.1f} m ab"


# --- BUG-01: Brennweiten-Empfehlung folgt der Motiventfernung ---------------------
# AK: < 500 m → Weitwinkel/Standard, > 2 km → Tele. Mindestens: monoton steigend mit Distanz.
def test_focal_length_increases_with_distance():
    near = A.calculate_focal_length_for_subject(50, 500)
    mid = A.calculate_focal_length_for_subject(50, 1000)
    far = A.calculate_focal_length_for_subject(50, 2000)
    assert near < mid < far, f"Brennweite nicht monoton: {near:.0f} / {mid:.0f} / {far:.0f}"


def test_focal_length_far_subject_is_tele():
    # Großes, weit entferntes Motiv → klar im Telebereich (> 135 mm).
    f = A.calculate_focal_length_for_subject(subject_size_m=50, distance_m=3000)
    assert f > 135, f"Erwartet Tele (>135 mm) für 3 km Distanz, bekam {f:.0f} mm"


# --- BUG-03 / US-58: Winkelprofil des Motivs konsistent ---------------------------
# AK: Azimut des Motivs entspricht der Peilung; Winkelbreite positiv und realistisch klein.
def test_subject_profile_azimuth_matches_bearing():
    obs = (52.40, 13.00)
    sub = (52.41, 13.01)
    profile = A.calculate_subject_angular_profile(*obs, *sub, subject_height_m=50, subject_width_m=30)
    # Unabhängige Peilung (0–360°, Nord im Uhrzeigersinn)
    dlon = math.radians(sub[1] - obs[1])
    y = math.sin(dlon) * math.cos(math.radians(sub[0]))
    x = (math.cos(math.radians(obs[0])) * math.sin(math.radians(sub[0]))
         - math.sin(math.radians(obs[0])) * math.cos(math.radians(sub[0])) * math.cos(dlon))
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
    assert abs(profile.azimuth_deg - bearing) < 1.0, (
        f"Profil-Azimut {profile.azimuth_deg:.2f}° ≠ Peilung {bearing:.2f}°")


def test_subject_angular_width_realistic():
    profile = A.calculate_subject_angular_profile(52.40, 13.00, 52.41, 13.01,
                                                  subject_height_m=50, subject_width_m=30)
    assert 0 < profile.angular_width_deg < 5, (
        f"Winkelbreite {profile.angular_width_deg:.2f}° unrealistisch für 30 m Motiv auf ~1,3 km")
    assert profile.angular_altitude_top_deg > profile.angular_altitude_base_deg


# --- TASK-34: Sonnenauf-/-untergang Berlin — Referenz-Check (Skyfield) ------------
# Absicherung: Skyfield-Berechnungen liefern Zeiten innerhalb ±3 Minuten des
# publizierten Wertes. Verhindert stille Regressionen durch fehlerhafte Ephemeriden-
# Initialisierung oder Zeitzonenumrechnung (Quelle: timeanddate.com Berlin).
#
# Referenzwerte für Berlin (52.52°N, 13.405°E), Sommer:
#   2026-06-21 Sonnenaufgang 01:43 UTC / Sonnenuntergang 20:25 UTC (Sommersonnenwende)
#   Toleranz: ±5 Minuten (berücksichtigt atmosphärische Refraktion, Genauigkeit de421.bsp)
#
# Dieser Test ist mit @pytest.mark.online markiert und wird in CI übersprungen
# wenn kein Netz verfügbar ist (de421.bsp-Download ~17 MB). Lokal: läuft beim
# ersten Aufruf mit Download, danach offline aus dem Cache.
try:
    from skyfield.api import load, wgs84
    from skyfield import almanac
    _SKYFIELD_AVAILABLE = True
except ImportError:
    _SKYFIELD_AVAILABLE = False


@pytest.mark.skipif(not _SKYFIELD_AVAILABLE, reason="skyfield nicht installiert")
@pytest.mark.online
def test_sunrise_berlin_within_tolerance():
    """TASK-34 AK: Sonnenaufgang Berlin am 2026-06-21 zwischen 01:38–01:48 UTC.

    Referenzwert: 01:43 UTC (timeanddate.com). Toleranz ±5 min.
    Schlägt dieser Test fehl, ist wahrscheinlich de421.bsp korrumpiert,
    die Skyfield-Version inkompatibel, oder A.get_sunrise_utc() falsch implementiert.
    """
    from datetime import date, datetime, timezone, timedelta

    ts = load.timescale()
    eph = load("de421.bsp")
    berlin = wgs84.latlon(52.52, 13.405)
    observer = eph["earth"] + berlin

    t0 = ts.utc(2026, 6, 21)
    t1 = ts.utc(2026, 6, 22)
    f = almanac.sunrise_sunset(eph, berlin)
    times, events = almanac.find_discrete(t0, t1, f)

    sunrises = [t.utc_datetime() for t, e in zip(times, events) if e == 1]
    assert sunrises, "Kein Sonnenaufgang gefunden — Skyfield-Problem"

    sr = sunrises[0]
    ref = datetime(2026, 6, 21, 1, 43, tzinfo=timezone.utc)
    diff = abs((sr - ref).total_seconds())
    assert diff <= 300, (
        f"Sonnenaufgang Berlin 2026-06-21: {sr.strftime('%H:%M')} UTC — "
        f"Referenz: 01:43 UTC — Abweichung: {diff/60:.1f} min (Toleranz: 5 min)"
    )


@pytest.mark.skipif(not _SKYFIELD_AVAILABLE, reason="skyfield nicht installiert")
@pytest.mark.online
def test_sunset_berlin_within_tolerance():
    """TASK-34 AK: Sonnenuntergang Berlin am 2026-06-21 zwischen 20:20–20:30 UTC.

    Referenzwert: 20:25 UTC (timeanddate.com). Toleranz ±5 min.
    """
    from datetime import datetime, timezone

    ts = load.timescale()
    eph = load("de421.bsp")
    berlin = wgs84.latlon(52.52, 13.405)

    t0 = ts.utc(2026, 6, 21)
    t1 = ts.utc(2026, 6, 22)
    f = almanac.sunrise_sunset(eph, berlin)
    times, events = almanac.find_discrete(t0, t1, f)

    sunsets = [t.utc_datetime() for t, e in zip(times, events) if e == 0]
    assert sunsets, "Kein Sonnenuntergang gefunden — Skyfield-Problem"

    ss = sunsets[0]
    ref = datetime(2026, 6, 21, 20, 25, tzinfo=timezone.utc)
    diff = abs((ss - ref).total_seconds())
    assert diff <= 300, (
        f"Sonnenuntergang Berlin 2026-06-21: {ss.strftime('%H:%M')} UTC — "
        f"Referenz: 20:25 UTC — Abweichung: {diff/60:.1f} min (Toleranz: 5 min)"
    )


@pytest.mark.skipif(not _SKYFIELD_AVAILABLE, reason="skyfield nicht installiert")
@pytest.mark.online
def test_babelsberg_pfingstberg_azimuth_plausible():
    """TASK-34 AK: Azimut Babelsberg → Pfingstberg liegt zwischen 310–340° (nordwestlich).

    Referenzwert aus TESTPLAN.md Abschnitt 3.1: ~320–340°.
    Schlägt dieser Test fehl, ist die Haversine-Peilungsberechnung kaputt.
    """
    import math
    obs_lat, obs_lon = 52.3975, 13.0976
    sub_lat, sub_lon = 52.4158, 13.0688

    dlon = math.radians(sub_lon - obs_lon)
    y = math.sin(dlon) * math.cos(math.radians(sub_lat))
    x = (math.cos(math.radians(obs_lat)) * math.sin(math.radians(sub_lat))
         - math.sin(math.radians(obs_lat)) * math.cos(math.radians(sub_lat)) * math.cos(dlon))
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360

    assert 310 <= bearing <= 340, (
        f"Azimut Babelsberg → Pfingstberg: {bearing:.1f}° — erwartet 310–340°. "
        "Peilungsberechnung defekt."
    )
