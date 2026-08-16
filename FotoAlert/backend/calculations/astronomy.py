"""
Astronomie-Berechnungen für FotoAlert.
Nutzt Skyfield für präzise Ephemeriden-Berechnungen.

Berechnet:
- Sonne: Aufgang, Untergang, goldene Stunde, blaue Stunde, Azimut/Höhe
- Mond: Aufgang, Untergang, Phase, Azimut/Höhe, Vollmond/Neumond
- Milchstraße: Sichtbarkeit des galaktischen Zentrums
- Planeten: Venus, Mars, Jupiter, Saturn (Abendstern etc.)
- Sonderereignisse: Sonnenfinsternisse, Meteoritenschauer
"""

from __future__ import annotations

import contextvars
import logging
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import numpy as np
from skyfield import almanac, eclipselib
from skyfield.api import N, E, Star, load, wgs84
from skyfield.data import mpc
from skyfield.framelib import ecliptic_frame
from skyfield.units import Angle

logger = logging.getLogger(__name__)


# Skyfield Timescale & Ephemeris (einmalig laden, gecacht)
_ts = load.timescale()
_eph: object | None = None


def _get_eph():
    global _eph
    if _eph is None:
        _eph = load("de421.bsp")
    return _eph


# ---------------------------------------------------------------------------
# TASK-25: On-Demand Window-Engine (optional aktiv)
# Wenn ein WindowEphemeris-Objekt aktiv ist und die Anfrage abdeckt, delegieren
# die Primitive (full_report, body_position, alignment) dorthin — die Tages-
# berechnungen kommen dann aus den vorberechneten Fenster-Arrays statt aus je
# einem Skyfield-Call pro Tag. Kein Import von window_engine hier (duck-typed) →
# kein Zirkelimport.
#
# BUG-63-Nachbesserung (Race-Fix): früher ein einfacher Modul-Global — bei
# echter Nebenläufigkeit (zwei gleichzeitige Requests, z. B. preview_alignment()
# via asyncio.to_thread() während der Event-Loop weiterläuft) konnte Request B
# das Fenster von Request A überschreiben. contextvars.ContextVar ist pro
# asyncio.Task isoliert (jeder Request läuft in Starlette als eigener Task mit
# eigener Kontext-Kopie) und asyncio.to_thread() kopiert den Kontext explizit
# in den Thread (contextvars.copy_context() + ctx.run(), Python 3.9+) — die
# Isolation bleibt also auch über to_thread() hinweg erhalten.
# ---------------------------------------------------------------------------
_active_window: "contextvars.ContextVar" = contextvars.ContextVar("_active_window", default=None)


def set_active_window(w) -> None:
    _active_window.set(w)


def clear_active_window() -> None:
    _active_window.set(None)


def _win_for(lat: float, lon: float, d):
    w = _active_window.get()
    if w is not None and w.covers(lat, lon, d):
        return w
    return None


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

@dataclass
class SunInfo:
    date: date
    sunrise: datetime
    sunset: datetime
    golden_hour_morning_start: datetime
    golden_hour_morning_end: datetime
    golden_hour_evening_start: datetime
    golden_hour_evening_end: datetime
    blue_hour_morning_start: datetime
    blue_hour_morning_end: datetime
    blue_hour_evening_start: datetime
    blue_hour_evening_end: datetime
    solar_noon: datetime
    day_length_hours: float


@dataclass
class MoonInfo:
    date: date
    moonrise: Optional[datetime]
    moonset: Optional[datetime]
    phase_fraction: float          # 0 = Neumond, 0.5 = Vollmond, 1 = Neumond
    phase_name: str
    illumination_pct: float
    azimuth_at_golden_hour: Optional[float]   # Grad
    altitude_at_golden_hour: Optional[float]  # Grad


@dataclass
class CelestialPosition:
    """Azimut und Höhe eines Himmelsobjekts zu einem bestimmten Zeitpunkt."""
    azimuth: float    # 0–360°, Nord=0
    altitude: float   # -90–90°, Horizont=0
    distance_au: Optional[float] = None


@dataclass
class MilkyWayInfo:
    date: date
    galactic_center_azimuth_at_midnight: Optional[float]
    galactic_center_altitude_at_midnight: Optional[float]
    best_visibility_start: Optional[datetime]
    best_visibility_end: Optional[datetime]
    darkness_score: float   # 0–1: wie dunkel ist es (astronomical twilight)
    visible: bool


@dataclass
class MeteorShower:
    name: str
    peak_date: date
    zhr: int   # Zenithal Hourly Rate
    radiant_constellation: str
    active_start: date
    active_end: date


@dataclass
class AstronomyReport:
    sun: SunInfo
    moon: MoonInfo
    milky_way: MilkyWayInfo
    active_meteor_showers: list[MeteorShower] = field(default_factory=list)
    planet_positions: dict[str, CelestialPosition] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Bekannte Meteoritenschauer
# ---------------------------------------------------------------------------

METEOR_SHOWERS: list[MeteorShower] = [
    MeteorShower("Quadrantiden",     date(2024, 1, 3),  120, "Bootes",      date(2024, 1, 1),  date(2024, 1, 5)),
    MeteorShower("Lyriden",          date(2024, 4, 22),  18, "Lyra",        date(2024, 4, 15), date(2024, 4, 25)),
    MeteorShower("Eta-Aquariiden",   date(2024, 5, 5),   50, "Aquarius",    date(2024, 4, 19), date(2024, 5, 28)),
    MeteorShower("Perseiden",        date(2024, 8, 12), 100, "Perseus",     date(2024, 7, 17), date(2024, 8, 24)),
    MeteorShower("Orioniden",        date(2024, 10, 21), 20, "Orion",       date(2024, 10, 2), date(2024, 11, 7)),
    MeteorShower("Leoniden",         date(2024, 11, 17), 15, "Leo",         date(2024, 11, 6), date(2024, 11, 30)),
    MeteorShower("Geminiden",        date(2024, 12, 14), 150, "Gemini",     date(2024, 12, 4), date(2024, 12, 20)),
    MeteorShower("Ursiden",          date(2024, 12, 22), 10, "Ursa Minor",  date(2024, 12, 17), date(2024, 12, 26)),
]


def get_active_meteor_showers(target_date: date) -> list[MeteorShower]:
    """Gibt aktive Meteoritenschauer für ein Datum zurück (Jahr-unabhängig)."""
    active = []
    for shower in METEOR_SHOWERS:
        # Datum auf Ziel-Jahr anpassen
        try:
            peak = shower.peak_date.replace(year=target_date.year)
            start = shower.active_start.replace(year=target_date.year)
            end = shower.active_end.replace(year=target_date.year)
            if end < start:  # Jahreswechsel
                end = end.replace(year=target_date.year + 1)
            if start <= target_date <= end:
                active.append(MeteorShower(
                    shower.name, peak, shower.zhr,
                    shower.radiant_constellation, start, end
                ))
        except ValueError:
            pass
    return active


# ---------------------------------------------------------------------------
# TASK-02: Sonnen-/Mondfinsternisse
#
# Architektur-Entscheidung (Option A, BACKLOG.md TASK-02): analog zu
# METEOR_SHOWERS/get_active_meteor_showers() sind Finsternisse Kalender-
# ereignisse ohne echte Location-Abhängigkeit — die Kontaktzeiten-Suche läuft
# von einem festen Berlin/BB-Referenzpunkt aus (Unterschiede innerhalb der
# Region liegen im Sekundenbereich, fotografisch irrelevant, laut Analyse-Spec).
#
# Anders als bei Meteoritenschauern (reine Datumsarithmetik, beliebig oft
# billig neu aufrufbar) ist die Sonnenfinsternis-Kontaktsuche eine echte,
# vektorisierte Skyfield-Berechnung pro Neumond — und calculate_full_report()
# wird pro Location UND pro Tag aufgerufen. AK-12 (Performance, Pre-Mortem
# Szenario 1) verlangt "einmal pro Precompute-Zeitfenster, nicht pro
# Location". Das wird hier über einen Jahres-Cache erreicht statt über eine
# Umstrukturierung von find_opportunities_multi_day()/precompute.py: die
# erste Anfrage für ein Kalenderjahr löst die teure Berechnung genau einmal
# aus, jede weitere Anfrage (jede Location, jeder Tag desselben Precompute-
# Laufs) ist danach ein billiger Dict-Lookup — siehe test_ak12_* in
# test_task02_eclipses.py, das die tatsächliche Aufrufzahl der teuren
# Jahres-Funktion zählt.
# ---------------------------------------------------------------------------

# Fester Referenzpunkt Berlin/Brandenburg (Analyse-Spec TASK-02): Kontaktzeiten-
# Suche und Sichtbarkeits-Guards laufen von hier aus, nicht pro Location.
BERLIN_REF_LAT = 52.52
BERLIN_REF_LON = 13.405

SUN_RADIUS_KM = 696_000.0
MOON_RADIUS_KM = 1_737.1  # physischer Mondradius (km) — entspricht MOON_DIAMETER_KM/2
                          # weiter unten; hier eigenständig, da diese Konstante vor
                          # MOON_DIAMETER_KM im Modul steht (Definitionsreihenfolge).


@dataclass
class SolarEclipseEvent:
    """Ergebnis der Sonnenfinsternis-Kontaktzeit-Suche für einen Referenzpunkt."""
    date: date
    c1: Optional[datetime]        # erste Berührung (Beginn des Kontaktfensters, UTC)
    c4: Optional[datetime]        # letzte Berührung (Ende des Kontaktfensters, UTC)
    max_time: datetime            # Zeitpunkt der größten Verfinsterung (UTC)
    max_separation_deg: float     # minimale scheinbare Winkeltrennung Sonne–Mond
    is_total: bool                # Mond bedeckt die Sonne vollständig (keine Ringform berücksichtigt)
    visible: bool                 # AK-16: Sonne > 0° Höhe zum Zeitpunkt des Maximums


@dataclass
class LunarEclipseEvent:
    """Ergebnis von skyfield.eclipselib.lunar_eclipses(), gefiltert auf Partial/Total."""
    date: date
    max_time: datetime            # Zeitpunkt der größten Verfinsterung (UTC)
    magnitude: float              # umbral_magnitude laut Skyfield
    is_total: bool
    visible: bool                 # AK-5: Mond > 0° Höhe zum Zeitpunkt des Maximums


def _angular_radius_deg(distance_km: float, body_radius_km: float) -> float:
    """Scheinbarer Winkelradius eines Himmelskörpers aus Entfernung + physischem Radius."""
    return math.degrees(math.asin(min(1.0, body_radius_km / distance_km)))


def _find_new_moons(t0, t1) -> list:
    """Liefert die Skyfield-Zeitpunkte aller Neumonde in [t0, t1]."""
    eph = _get_eph()
    f = almanac.moon_phases(eph)
    times, events = almanac.find_discrete(t0, t1, f)
    return [t for t, e in zip(times, events) if e == 0]


def _solar_eclipse_event_for_new_moon(
    new_moon_dt: datetime, lat: float, lon: float,
) -> Optional[SolarEclipseEvent]:
    """Sucht um einen Neumond-Zeitpunkt herum nach einer Sonnenfinsternis, gesehen
    von (lat, lon). Gibt None zurück, wenn die Winkeltrennung Sonne–Mond die Summe
    der scheinbaren Radien nie unterschreitet (kein Ereignis von diesem Ort aus)."""
    eph = _get_eph()
    observer = wgs84.latlon(lat * N, lon * E)
    earth = eph["earth"]
    sun = eph["sun"]
    moon = eph["moon"]

    t0 = _ts.tt_jd(new_moon_dt.tt - 0.5)  # ±12h um den Neumond
    t1 = _ts.tt_jd(new_moon_dt.tt + 0.5)
    times = _ts.linspace(t0, t1, 1441)  # ~1-Minuten-Auflösung

    app_sun = (earth + observer).at(times).observe(sun).apparent()
    app_moon = (earth + observer).at(times).observe(moon).apparent()
    sep_deg = app_sun.separation_from(app_moon).degrees

    sun_dist_km = app_sun.distance().km
    moon_dist_km = app_moon.distance().km
    sun_r_deg = np.degrees(np.arcsin(np.minimum(1.0, SUN_RADIUS_KM / sun_dist_km)))
    moon_r_deg = np.degrees(np.arcsin(np.minimum(1.0, MOON_RADIUS_KM / moon_dist_km)))
    sum_r_deg = sun_r_deg + moon_r_deg

    mask = sep_deg < sum_r_deg
    indices = np.where(mask)[0]
    if len(indices) == 0:
        return None  # kein Ereignis von diesem Ort aus sichtbar (geometrisch)

    i_min = int(np.argmin(sep_deg))
    max_time = times[i_min].utc_datetime()
    max_sep = float(sep_deg[i_min])
    diff_r_deg = abs(float(moon_r_deg[i_min]) - float(sun_r_deg[i_min]))
    is_total = bool(moon_r_deg[i_min] > sun_r_deg[i_min] and max_sep < diff_r_deg)

    c1 = times[indices[0]].utc_datetime()
    c4 = times[indices[-1]].utc_datetime()

    # AK-16: Sichtbarkeits-Guard — Sonne muss zum Zeitpunkt des Maximums über dem
    # Horizont stehen (symmetrisch zu AK-5 bei Mondfinsternissen).
    sun_pos_max = get_body_position(lat, lon, "sun", max_time)
    visible = bool(sun_pos_max is not None and sun_pos_max.altitude > 0)

    return SolarEclipseEvent(
        date=max_time.date(),
        c1=c1, c4=c4, max_time=max_time,
        max_separation_deg=round(max_sep, 4),
        is_total=is_total,
        visible=visible,
    )


def _compute_solar_eclipses_for_year(year: int, lat: float, lon: float) -> list[SolarEclipseEvent]:
    """Teure Skyfield-Berechnung: alle Sonnenfinsternisse eines Kalenderjahres von
    (lat, lon) aus gesehen. NUR intern über den Jahres-Cache aufrufen (find_solar_eclipses/
    get_solar_eclipse_for_date) — direkte Aufrufe umgehen das AK-12-Caching."""
    t0 = _ts.utc(year - 1, 12, 15)
    t1 = _ts.utc(year + 1, 1, 15)
    events: list[SolarEclipseEvent] = []
    for new_moon_t in _find_new_moons(t0, t1):
        new_moon_dt = new_moon_t.utc_datetime()
        try:
            ev = _solar_eclipse_event_for_new_moon(new_moon_t, lat, lon)
        except Exception as exc:
            # AK-15: ein Fehler bei einem einzelnen Kandidaten darf die übrigen
            # Neumonde des Jahres nicht mit zu Fall bringen — isoliert loggen.
            logger.error(
                "Sonnenfinsternis-Suche für Neumond %s (Jahr %d) fehlgeschlagen: %s: %s",
                new_moon_dt.isoformat(), year, type(exc).__name__, exc,
            )
            continue
        if ev is not None and ev.date.year == year:
            events.append(ev)
    return events


_SOLAR_ECLIPSE_CACHE: dict[tuple, list[SolarEclipseEvent]] = {}


def find_solar_eclipses(
    start_date: date, end_date: date,
    lat: float = BERLIN_REF_LAT, lon: float = BERLIN_REF_LON,
) -> list[SolarEclipseEvent]:
    """Sonnenfinsternisse im Zeitraum [start_date, end_date], gesehen von (lat, lon).

    AK-12: pro (Jahr, gerundete Koordinate) wird die teure Berechnung genau einmal
    ausgeführt und gecacht — beliebig viele Locations/Tage im selben Precompute-Lauf
    teilen sich das Ergebnis."""
    events: list[SolarEclipseEvent] = []
    for year in range(start_date.year, end_date.year + 1):
        key = (year, round(lat, 2), round(lon, 2))
        if key not in _SOLAR_ECLIPSE_CACHE:
            _SOLAR_ECLIPSE_CACHE[key] = _compute_solar_eclipses_for_year(year, lat, lon)
        events.extend(_SOLAR_ECLIPSE_CACHE[key])
    return [e for e in events if start_date <= e.date <= end_date]


def get_solar_eclipse_for_date(
    target_date: date,
    lat: float = BERLIN_REF_LAT, lon: float = BERLIN_REF_LON,
) -> Optional[SolarEclipseEvent]:
    """Liefert die Sonnenfinsternis für genau target_date (oder None)."""
    for ev in find_solar_eclipses(target_date, target_date, lat=lat, lon=lon):
        if ev.date == target_date:
            return ev
    return None


def _compute_lunar_eclipses_for_year(year: int, lat: float, lon: float) -> list[LunarEclipseEvent]:
    """Teure Skyfield-Berechnung: alle Partial/Total-Mondfinsternisse eines Kalender-
    jahres (Penumbral ausgeschlossen, Annahmen-Protokoll TASK-02). NUR intern über den
    Jahres-Cache aufrufen (find_lunar_eclipses/get_lunar_eclipse_for_date)."""
    eph = _get_eph()
    t0 = _ts.utc(year, 1, 1)
    t1 = _ts.utc(year + 1, 1, 1)
    events: list[LunarEclipseEvent] = []
    try:
        times, codes, details = eclipselib.lunar_eclipses(t0, t1, eph)
    except Exception as exc:
        # AK-15: ein Fehler in der Jahres-Suche selbst darf den Gesamtlauf nicht
        # abbrechen — isoliert loggen, keine Mondfinsternisse für dieses Jahr.
        logger.error(
            "Mondfinsternis-Suche für Jahr %d fehlgeschlagen: %s: %s",
            year, type(exc).__name__, exc,
        )
        return events

    for i, (t, code) in enumerate(zip(times, codes)):
        code = int(code)
        if code == 0:
            continue  # Penumbral — bewusst nicht als eigener Typ geführt
        try:
            max_time = t.utc_datetime()
            magnitude = float(details["umbral_magnitude"][i])
            is_total = code == 2
            # AK-5: Sichtbarkeits-Guard — Mond muss zum Zeitpunkt des Maximums über
            # dem Horizont stehen.
            moon_pos_max = get_body_position(lat, lon, "moon", max_time)
            visible = bool(moon_pos_max is not None and moon_pos_max.altitude > 0)
            events.append(LunarEclipseEvent(
                date=max_time.date(),
                max_time=max_time,
                magnitude=round(magnitude, 3),
                is_total=is_total,
                visible=visible,
            ))
        except Exception as exc:
            logger.error(
                "Mondfinsternis-Verarbeitung für %s (Jahr %d) fehlgeschlagen: %s: %s",
                t.utc_iso(), year, type(exc).__name__, exc,
            )
            continue
    return events


_LUNAR_ECLIPSE_CACHE: dict[tuple, list[LunarEclipseEvent]] = {}


def find_lunar_eclipses(
    start_date: date, end_date: date,
    lat: float = BERLIN_REF_LAT, lon: float = BERLIN_REF_LON,
) -> list[LunarEclipseEvent]:
    """Mondfinsternisse (Partial/Total) im Zeitraum [start_date, end_date], Sichtbarkeits-
    Guard bezogen auf (lat, lon). AK-12: pro (Jahr, gerundete Koordinate) gecacht."""
    events: list[LunarEclipseEvent] = []
    for year in range(start_date.year, end_date.year + 1):
        key = (year, round(lat, 2), round(lon, 2))
        if key not in _LUNAR_ECLIPSE_CACHE:
            _LUNAR_ECLIPSE_CACHE[key] = _compute_lunar_eclipses_for_year(year, lat, lon)
        events.extend(_LUNAR_ECLIPSE_CACHE[key])
    return [e for e in events if start_date <= e.date <= end_date]


def get_lunar_eclipse_for_date(
    target_date: date,
    lat: float = BERLIN_REF_LAT, lon: float = BERLIN_REF_LON,
) -> Optional[LunarEclipseEvent]:
    """Liefert die Mondfinsternis für genau target_date (oder None)."""
    for ev in find_lunar_eclipses(target_date, target_date, lat=lat, lon=lon):
        if ev.date == target_date:
            return ev
    return None


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _skyfield_time(dt: datetime) -> object:
    """Wandelt datetime (UTC oder timezone-aware) in Skyfield-Zeit um."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return _ts.from_datetime(dt)


MOON_DIAMETER_KM = 3_474.2     # physischer Monddurchmesser (km)
AU_TO_KM = 149_597_870.7       # 1 Astronomische Einheit in km


def get_moon_earth_distance_km(dt: datetime) -> float:
    """
    Gibt die aktuelle Erde-Mond-Distanz in km via Skyfield zurück.

    Variiert zwischen ~356.500 km (Perigäum) und ~406.700 km (Apogäum).
    Mittlerer Wert: ~384.400 km → Winkeldurchmesser ~31,1 Bogenminuten.

    Verwendet Skyfield's distance.km direkt (kein AU-Umrechnungsfehler).
    """
    eph = _get_eph()
    t = _skyfield_time(dt)
    earth = eph["earth"]
    moon = eph["moon"]
    astrometric = earth.at(t).observe(moon)
    dist_km = astrometric.distance().km
    assert 350_000 < dist_km < 410_000, (
        f"Unplausible Mond-Erde-Distanz: {dist_km:.0f} km "
        f"(Erwartung: 350.000–410.000 km)"
    )
    return dist_km


def _find_sun_altitude_crossing(
    observer, eph, t0, t1, target_altitude_deg: float, rising: bool
) -> Optional[datetime]:
    """Findet den Zeitpunkt, an dem die Sonne eine bestimmte Höhe kreuzt."""
    sun = eph["sun"]
    earth = eph["earth"]

    # Vektorisiert: alle 720 Zeitpunkte in einem einzigen Skyfield-Aufruf
    times = _ts.linspace(t0, t1, 720)  # 12h / 1 min
    astrometric = (earth + observer).at(times).observe(sun)
    alt, _, _ = astrometric.apparent().altaz()
    alts = alt.degrees  # numpy-Array

    target = target_altitude_deg
    tt_arr = times.tt  # numpy-Array der TT-Julianischen Daten
    for i in range(len(alts) - 1):
        if rising:
            if alts[i] <= target < alts[i + 1]:
                frac = (target - alts[i]) / (alts[i + 1] - alts[i])
                t_frac = tt_arr[i] + frac * (tt_arr[i + 1] - tt_arr[i])
                return _ts.tt_jd(float(t_frac)).utc_datetime()
        else:
            if alts[i] >= target > alts[i + 1]:
                frac = (alts[i] - target) / (alts[i] - alts[i + 1])
                t_frac = tt_arr[i] + frac * (tt_arr[i + 1] - tt_arr[i])
                return _ts.tt_jd(float(t_frac)).utc_datetime()
    return None


def _moon_phase_name(fraction: float) -> str:
    if fraction < 0.03 or fraction > 0.97:
        return "Neumond"
    elif fraction < 0.22:
        return "Zunehmende Sichel"
    elif fraction < 0.28:
        return "Erstes Viertel"
    elif fraction < 0.47:
        return "Zunehmender Dreiviertelmond"
    elif fraction < 0.53:
        return "Vollmond"
    elif fraction < 0.72:
        return "Abnehmender Dreiviertelmond"
    elif fraction < 0.78:
        return "Letztes Viertel"
    else:
        return "Abnehmende Sichel"


# ---------------------------------------------------------------------------
# Kern-Berechnungen
# ---------------------------------------------------------------------------

def calculate_sun_info(lat: float, lon: float, target_date: date) -> SunInfo:
    """
    Berechnet alle Sonnen-Informationen für einen Standort und ein Datum.
    Rückgabewerte sind UTC-datetimes.
    """
    eph = _get_eph()
    observer = wgs84.latlon(lat * N, lon * E)
    earth = eph["earth"]
    sun = eph["sun"]

    # Zeitfenster: 12h vor bis 12h nach Mitternacht UTC des Zieldatums
    t0 = _ts.utc(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    t1 = _ts.utc(target_date.year, target_date.month, target_date.day, 23, 59, 59)

    # Sonnenaufgang / -untergang (0° Horizont, inkl. Refraktion ≈ -0.5°)
    f = almanac.sunrise_sunset(eph, observer)
    times, events = almanac.find_discrete(t0, t1, f)

    sunrise = None
    sunset = None
    for t, e in zip(times, events):
        dt = t.utc_datetime()
        if e == 1 and sunrise is None:
            sunrise = dt
        elif e == 0 and sunset is None:
            sunset = dt

    # Fallback falls nicht im Fenster gefunden
    if sunrise is None:
        sunrise = datetime(target_date.year, target_date.month, target_date.day, 6, 0, tzinfo=timezone.utc)
    if sunset is None:
        sunset = datetime(target_date.year, target_date.month, target_date.day, 20, 0, tzinfo=timezone.utc)

    # Solar Noon
    solar_noon_t = t0.tt + (t1.tt - t0.tt) / 2  # Annäherung
    # Präziser: Mitte zwischen Aufgang und Untergang
    if sunrise and sunset:
        mid_tt = (_skyfield_time(sunrise).tt + _skyfield_time(sunset).tt) / 2
        solar_noon = _ts.tt_jd(mid_tt).utc_datetime()
    else:
        solar_noon = datetime(target_date.year, target_date.month, target_date.day, 12, 0, tzinfo=timezone.utc)

    day_length = (sunset - sunrise).total_seconds() / 3600

    # Goldene Stunde: Sonne zwischen -4° und +6° über Horizont
    ghe_morning_start = _find_sun_altitude_crossing(observer, eph, t0, _skyfield_time(sunrise + timedelta(hours=2)), -4.0, True)
    ghe_morning_end = _find_sun_altitude_crossing(observer, eph, t0, _skyfield_time(sunrise + timedelta(hours=2)), 6.0, True)
    ghe_evening_start = _find_sun_altitude_crossing(observer, eph, _skyfield_time(sunset - timedelta(hours=2)), t1, 6.0, False)
    ghe_evening_end = _find_sun_altitude_crossing(observer, eph, _skyfield_time(sunset - timedelta(hours=2)), t1, -4.0, False)

    # Blaue Stunde: Sonne zwischen -6° und -4°
    bh_morning_start = _find_sun_altitude_crossing(observer, eph, t0, _skyfield_time(sunrise + timedelta(hours=1)), -6.0, True)
    bh_morning_end = ghe_morning_start
    bh_evening_start = ghe_evening_end
    bh_evening_end = _find_sun_altitude_crossing(observer, eph, _skyfield_time(sunset - timedelta(hours=1)), t1, -6.0, False)

    # Fallbacks
    def fallback(dt, offset_min):
        if dt is None:
            return sunrise + timedelta(minutes=offset_min) if offset_min > 0 else sunset - timedelta(minutes=-offset_min)
        return dt

    return SunInfo(
        date=target_date,
        sunrise=sunrise,
        sunset=sunset,
        golden_hour_morning_start=ghe_morning_start or (sunrise - timedelta(minutes=20)),
        golden_hour_morning_end=ghe_morning_end or (sunrise + timedelta(minutes=40)),
        golden_hour_evening_start=ghe_evening_start or (sunset - timedelta(minutes=40)),
        golden_hour_evening_end=ghe_evening_end or (sunset + timedelta(minutes=20)),
        blue_hour_morning_start=bh_morning_start or (sunrise - timedelta(minutes=40)),
        blue_hour_morning_end=bh_morning_end or (sunrise - timedelta(minutes=10)),
        blue_hour_evening_start=bh_evening_start or (sunset + timedelta(minutes=10)),
        blue_hour_evening_end=bh_evening_end or (sunset + timedelta(minutes=40)),
        solar_noon=solar_noon,
        day_length_hours=day_length,
    )


def get_sun_position(lat: float, lon: float, dt: datetime) -> CelestialPosition:
    """Azimut und Höhe der Sonne zu einem bestimmten Zeitpunkt."""
    eph = _get_eph()
    observer = wgs84.latlon(lat * N, lon * E)
    earth = eph["earth"]
    sun = eph["sun"]
    t = _skyfield_time(dt)
    astrometric = (earth + observer).at(t).observe(sun)
    alt, az, dist = astrometric.apparent().altaz()
    return CelestialPosition(azimuth=az.degrees, altitude=alt.degrees, distance_au=dist.au)


def calculate_moon_info(
    lat: float, lon: float, target_date: date,
    sun_info: Optional["SunInfo"] = None,
) -> MoonInfo:
    """Berechnet Mond-Informationen: Aufgang, Phase, Beleuchtung.

    TASK-25: ``sun_info`` kann übergeben werden, um die teure Neuberechnung von
    ``calculate_sun_info`` zu vermeiden (identisches Ergebnis, nur schneller).
    """
    eph = _get_eph()
    observer = wgs84.latlon(lat * N, lon * E)
    earth = eph["earth"]
    moon = eph["moon"]
    sun = eph["sun"]

    t0 = _ts.utc(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    t1 = _ts.utc(target_date.year, target_date.month, target_date.day, 23, 59, 59)

    # Mondauf- und untergang
    f = almanac.risings_and_settings(eph, moon, observer)
    times, events = almanac.find_discrete(t0, t1, f)

    moonrise = None
    moonset = None
    for t, e in zip(times, events):
        dt = t.utc_datetime()
        if e == 1 and moonrise is None:
            moonrise = dt
        elif e == 0 and moonset is None:
            moonset = dt

    # Mondphase zur Mitternacht UTC
    t_midnight = _ts.utc(target_date.year, target_date.month, target_date.day, 12, 0, 0)
    moon_pos = (earth + observer).at(t_midnight).observe(moon).apparent()
    sun_pos = (earth + observer).at(t_midnight).observe(sun).apparent()

    # Elongation (Winkelabstand Mond–Sonne) → Phase
    moon_ecl = moon_pos.frame_latlon(ecliptic_frame)
    sun_ecl = sun_pos.frame_latlon(ecliptic_frame)
    elongation = (moon_ecl[1].degrees - sun_ecl[1].degrees) % 360
    phase_fraction = elongation / 360.0

    # Beleuchtung
    illumination = (1 - math.cos(math.radians(elongation))) / 2 * 100

    # Mondposition während goldener Abendstunde (ca. 1h vor Sonnenuntergang)
    if sun_info is None:
        sun_info = calculate_sun_info(lat, lon, target_date)
    gh_time = sun_info.golden_hour_evening_start
    moon_pos_gh = get_body_position(lat, lon, "moon", gh_time)

    return MoonInfo(
        date=target_date,
        moonrise=moonrise,
        moonset=moonset,
        phase_fraction=phase_fraction,
        phase_name=_moon_phase_name(phase_fraction),
        illumination_pct=round(illumination, 1),
        azimuth_at_golden_hour=round(moon_pos_gh.azimuth, 1) if moon_pos_gh else None,
        altitude_at_golden_hour=round(moon_pos_gh.altitude, 1) if moon_pos_gh else None,
    )


def get_body_position(lat: float, lon: float, body: str, dt: datetime) -> Optional[CelestialPosition]:
    """
    Gibt die Position (Azimut, Höhe) eines Himmelskörpers zurück.
    body: 'sun', 'moon', 'venus', 'mars', 'jupiter barycenter', 'saturn barycenter'

    TASK-25: Delegiert an die aktive Window-Engine (Sonne/Mond interpoliert),
    fällt für Planeten/ohne aktives Fenster auf die direkte Skyfield-Rechnung zurück.
    """
    try:
        w = _win_for(lat, lon, dt.astimezone(timezone.utc).date())
    except Exception:
        w = None
    if w is not None:
        pos = w.body_position(body, dt)
        if pos is not None:
            return pos
    return _get_body_position_direct(lat, lon, body, dt)


def _get_body_position_direct(lat: float, lon: float, body: str, dt: datetime) -> Optional[CelestialPosition]:
    """Direkte Skyfield-Berechnung der Body-Position (ohne Window-Delegation)."""
    try:
        eph = _get_eph()
        observer = wgs84.latlon(lat * N, lon * E)
        earth = eph["earth"]
        target = eph[body]
        t = _skyfield_time(dt)
        astrometric = (earth + observer).at(t).observe(target)
        alt, az, dist = astrometric.apparent().altaz()
        return CelestialPosition(azimuth=az.degrees, altitude=alt.degrees, distance_au=dist.au)
    except Exception:
        return None


def calculate_milky_way_info(
    lat: float, lon: float, target_date: date,
    sun_info: Optional["SunInfo"] = None,
    moon_info: Optional["MoonInfo"] = None,
) -> MilkyWayInfo:
    """
    Berechnet die Sichtbarkeit des galaktischen Zentrums.
    Das galaktische Zentrum liegt bei RA 17h 45m, Dec -29°.
    Beste Sichtbarkeit: April–September, nach astronomischer Dämmerung.

    TASK-25: ``sun_info``/``moon_info`` können übergeben werden, um doppelte
    Neuberechnung zu vermeiden (identisches Ergebnis, nur schneller).
    """
    eph = _get_eph()
    observer = wgs84.latlon(lat * N, lon * E)
    earth = eph["earth"]

    # Galaktisches Zentrum (Sagittarius A*)
    galactic_center = Star(ra_hours=17.761, dec_degrees=-28.936)

    # Astronomische Dämmerung: Sonne < -18°
    if sun_info is None:
        sun_info = calculate_sun_info(lat, lon, target_date)

    # Prüfe ob astronomische Dämmerung erreicht wird
    t_eve_end = sun_info.blue_hour_evening_end
    t_morn_start = sun_info.blue_hour_morning_start

    # Position des Galaktischen Zentrums um Mitternacht
    midnight = datetime(target_date.year, target_date.month, target_date.day,
                        22, 0, tzinfo=timezone.utc)
    t_mid = _skyfield_time(midnight)

    astrometric = (earth + observer).at(t_mid).observe(galactic_center)
    alt, az, _ = astrometric.apparent().altaz()

    az_deg = az.degrees
    alt_deg = alt.degrees

    # Sichtbarkeitsfenster: galaktisches Zentrum > 5° Höhe + astronomische Nacht
    visible = alt_deg > 5.0

    # Dunkelscore: Abstand von Vollmond, Jahreszeit (galaktisches Zentrum sichtbar April–Oktober)
    month = target_date.month
    seasonal_factor = 1.0 if 4 <= month <= 9 else 0.3

    # Mondeinfluss
    if moon_info is None:
        moon_info = calculate_moon_info(lat, lon, target_date, sun_info=sun_info)
    moon_factor = 1.0 - (moon_info.illumination_pct / 100) * 0.8

    darkness_score = min(1.0, seasonal_factor * moon_factor * (1.0 if visible else 0.2))

    return MilkyWayInfo(
        date=target_date,
        galactic_center_azimuth_at_midnight=round(az_deg, 1) if visible else None,
        galactic_center_altitude_at_midnight=round(alt_deg, 1) if visible else None,
        best_visibility_start=t_eve_end,
        best_visibility_end=t_morn_start,
        darkness_score=round(darkness_score, 2),
        visible=visible and darkness_score > 0.3,
    )


def calculate_full_report(lat: float, lon: float, target_date: date) -> AstronomyReport:
    """Erstellt einen vollständigen Astronomiebericht für Standort und Datum.

    TASK-25: Bei aktiver Window-Engine werden Sun/Moon/MilkyWay aus den
    vorberechneten Fenster-Arrays abgeleitet (statt je 1 Skyfield-Call/Tag).
    """
    w = _win_for(lat, lon, target_date)
    if w is not None:
        sun = w.sun_info(target_date)
        moon = w.moon_info(target_date, sun_info=sun)
        milky_way = w.milky_way_info(target_date, sun_info=sun, moon_info=moon)
    else:
        sun = calculate_sun_info(lat, lon, target_date)
        moon = calculate_moon_info(lat, lon, target_date, sun_info=sun)
        milky_way = calculate_milky_way_info(lat, lon, target_date, sun_info=sun, moon_info=moon)
    showers = get_active_meteor_showers(target_date)

    # Planeten
    planets = {}
    gh_time = sun.golden_hour_evening_start
    for body, name in [
        ("venus", "Venus"),
        ("mars", "Mars"),
        ("jupiter barycenter", "Jupiter"),
        ("saturn barycenter", "Saturn"),
    ]:
        pos = get_body_position(lat, lon, body, gh_time)
        if pos and pos.altitude > 5:
            planets[name] = pos

    return AstronomyReport(
        sun=sun,
        moon=moon,
        milky_way=milky_way,
        active_meteor_showers=showers,
        planet_positions=planets,
    )


def calculate_azimuth_alignment(
    observer_lat: float, observer_lon: float,
    target_lat: float, target_lon: float,
) -> float:
    """
    Berechnet den Azimut vom Beobachter zum Ziel (Gebäude/Landmark).
    Gibt Grad zurück (0=Nord, 90=Ost, 180=Süd, 270=West).
    """
    d_lon = math.radians(target_lon - observer_lon)
    lat1 = math.radians(observer_lat)
    lat2 = math.radians(target_lat)

    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def calculate_haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Berechnet die Luftlinien-Distanz zwischen zwei GPS-Koordinaten in Metern.
    Nutzt die Haversine-Formel (sphärische Erde, Genauigkeit ~0.3%).
    """
    R = 6_371_000  # Erdradius in Metern
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Vertikale Triangulation – der Kern des 3D-Alignments
# ---------------------------------------------------------------------------

class AlignmentType(str):
    """Beschreibt wo am Motiv das Himmelsobjekt steht."""
    BEHIND_BASE   = "Hinter dem Sockel"      # Objekt nahe Horizont, hinter Basis des Gebäudes
    BEHIND_MID    = "Hinter dem Gebäude"     # Objekt steckt im Gebäude (visuell)
    AT_CROWN      = "An der Spitze"          # Objekt schwebt exakt über der Spitze – der Jackpot
    CLEARING_TOP  = "Knapp über der Spitze"  # Objekt hat Spitze gerade passiert


@dataclass
class SubjectAngularProfile:
    """
    Winkelprofil eines Motivs vom Beobachterstandpunkt aus.

    Beispiel: Fernsehturm (368m), 500m Entfernung
      → ground_distance_m = 500
      → angular_altitude_base_deg  ≈ 0°   (Basis auf Augenhöhe)
      → angular_altitude_top_deg   ≈ arctan(368/500) ≈ 36.3°
      → angular_width_deg          ≈ arctan(30/500)  ≈ 3.4°
    """
    azimuth_deg: float              # Azimut Fotograf → Motiv
    ground_distance_m: float        # Berechnete Distanz (Haversine)
    angular_altitude_base_deg: float   # Höhenwinkel Basis (meist 0°)
    angular_altitude_top_deg: float    # Höhenwinkel Motivspitze
    angular_width_deg: float           # Halbe Winkelbreite des Motivs


@dataclass
class AlignmentResult:
    """Ergebnis eines präzisen 3D-Alignments."""
    time: datetime
    body: str                          # "sun" oder "moon"
    alignment_type: str                # AlignmentType
    celestial_azimuth: float
    celestial_altitude: float
    azimuth_offset_deg: float          # Abweichung vom Motiv-Azimut
    altitude_offset_deg: float         # Abweichung vom Top (negativ = darunter)
    quality_score: float               # 0–1, 1 = perfektes Crown-Alignment
    subject_profile: SubjectAngularProfile


def calculate_subject_angular_profile(
    observer_lat: float, observer_lon: float,
    subject_lat: float, subject_lon: float,
    subject_height_m: float = 0.0,
    subject_width_m: float = 0.0,
    observer_height_m: float = 1.6,       # Augenhöhe Fotograf
    elevation_difference_m: float = 0.0,  # Niveauunterschied Motiv-Basis − Fotograf-Boden
                                           # positiv = Motiv auf höherem Gelände
) -> SubjectAngularProfile:
    """
    Berechnet das vollständige Winkelprofil eines Motivs vom Standpunkt des Fotografen.

    subject_height_m       = tatsächliche Bauwerkshöhe (absolut, z.B. laut Wikipedia)
    elevation_difference_m = Höhe der Motiv-Basis über/unter dem Fotografen-Bodenniveau
                             (positiv = Motiv auf Hügel, negativ = Fotograf erhöht)

    Effektive Winkel-Höhe = subject_height_m + elevation_difference_m − observer_height_m

    Beispiel Babelsberg → Belvedere Pfingstberg:
      ground_distance ≈ 3200m
      subject_height_m = 15m (Turmhöhe)
      elevation_difference_m = +50m (Pfingstberg ~90m NN, Fotograf ~40m NN)
      → effective_height ≈ 15 + 50 − 1.6 = 63.4m
      → angular_altitude_top ≈ arctan(63.4 / 3200) ≈ 1.13°
    """
    azimuth = calculate_azimuth_alignment(observer_lat, observer_lon, subject_lat, subject_lon)
    ground_dist = calculate_haversine_distance(observer_lat, observer_lon, subject_lat, subject_lon)

    effective_height = max(0.0, subject_height_m + elevation_difference_m - observer_height_m)
    alt_top = math.degrees(math.atan2(effective_height, ground_dist)) if ground_dist > 0 else 0.0
    half_width = math.degrees(math.atan2(subject_width_m / 2, ground_dist)) if ground_dist > 0 and subject_width_m > 0 else 1.0

    return SubjectAngularProfile(
        azimuth_deg=round(azimuth, 2),
        ground_distance_m=round(ground_dist, 1),
        angular_altitude_base_deg=0.0,
        angular_altitude_top_deg=round(alt_top, 3),
        angular_width_deg=round(half_width, 3),
    )


def _classify_alignment(
    celestial_alt: float,
    profile: SubjectAngularProfile,
    az_offset: float,
) -> tuple[str, float]:
    """
    Klassifiziert das Alignment und berechnet den Qualitäts-Score.

    Returns: (AlignmentType, quality_score 0–1)
    """
    top = profile.angular_altitude_top_deg
    az_tol = profile.angular_width_deg + 1.5  # Azimut-Toleranz = halbe Breite + 1.5°

    # Azimut-Güte: Gaußsche Kurve, Halbwertsbreite = az_tol
    az_quality = math.exp(-0.5 * (az_offset / max(az_tol, 0.5)) ** 2)

    # Höhen-Klassifikation und -Güte
    if celestial_alt < 0:
        return AlignmentType.BEHIND_BASE, 0.0

    crown_tolerance = max(0.3, top * 0.15)  # 15% der Top-Höhe als Toleranz, min 0.3°

    if abs(celestial_alt - top) <= crown_tolerance:
        # Crown-Alignment: Jackpot
        alt_quality = math.exp(-0.5 * ((celestial_alt - top) / crown_tolerance) ** 2)
        quality = az_quality * alt_quality
        return AlignmentType.AT_CROWN, round(quality, 3)

    elif celestial_alt < top * 0.1:
        # Direkt hinter dem Sockel
        alt_quality = 0.5 * math.exp(-celestial_alt / max(top * 0.1, 0.3))
        return AlignmentType.BEHIND_BASE, round(az_quality * alt_quality, 3)

    elif celestial_alt < top - crown_tolerance:
        # Mitten im Gebäude
        alt_quality = 0.3
        return AlignmentType.BEHIND_MID, round(az_quality * alt_quality, 3)

    elif celestial_alt <= top + crown_tolerance * 3:
        # Knapp über der Spitze
        overshoot = celestial_alt - top
        alt_quality = 0.7 * math.exp(-overshoot / (crown_tolerance * 2))
        return AlignmentType.CLEARING_TOP, round(az_quality * alt_quality, 3)

    else:
        # Zu weit über dem Gebäude
        return AlignmentType.CLEARING_TOP, round(az_quality * 0.1, 3)


def find_precise_alignment_times(
    observer_lat: float, observer_lon: float,
    subject_lat: float, subject_lon: float,
    subject_height_m: float,
    subject_width_m: float,
    target_date: date,
    body: str = "sun",                  # "sun" oder "moon"
    az_tolerance_deg: float = 3.0,
    min_quality: float = 0.2,
    resolution_minutes: int = 1,
    elevation_difference_m: float = 0.0,
) -> list[AlignmentResult]:
    """
    Findet Zeitpunkte für ein präzises 3D-Alignment zwischen Fotograf, Motiv und Himmelsobjekt.

    Im Gegensatz zu find_sun_alignment_times() prüft diese Funktion:
    1. Azimut: Himmelsobjekt nahe der Sichtachse Fotograf → Motiv
    2. Höhe: Himmelsobjekt nahe dem Höhenwinkel der Motivspitze (Crown-Alignment)

    Gibt AlignmentResult-Objekte zurück, sortiert nach Qualitäts-Score (absteigend).

    Beispiel Babelsberg → Belvedere (Pfingstberg):
      observer: (52.3975, 13.0976)
      subject:  (52.4158, 13.0688), height=15m, elevation_difference=+50m
      → effective_height ≈ 63.4m, subject_azimuth ≈ 315°, angular_top ≈ 1.13°
      → Sonne erreicht Azimut 315° im Sommer um ~20:00–20:15 Uhr
      → Bei Höhe ~1.1° = Crown-Alignment, Score ~0.9
    """
    # TASK-25: aktive Window-Engine bevorzugen (ein Event pro Passage, AK6)
    w = _win_for(observer_lat, observer_lon, target_date)
    if w is not None:
        return w.alignments(
            subject_lat, subject_lon, subject_height_m, subject_width_m,
            target_date, body, az_tolerance_deg=az_tolerance_deg,
            min_quality=min_quality, elevation_difference_m=elevation_difference_m,
        )

    profile = calculate_subject_angular_profile(
        observer_lat, observer_lon, subject_lat, subject_lon,
        subject_height_m, subject_width_m,
        elevation_difference_m=elevation_difference_m,
    )

    eph = _get_eph()
    observer = wgs84.latlon(observer_lat * N, observer_lon * E)
    earth = eph["earth"]
    sky_body = eph[body]

    steps = int(17 * 60 / resolution_minutes)  # 4:00–21:00 Uhr
    t0 = _ts.utc(target_date.year, target_date.month, target_date.day, 4, 0, 0)
    t1 = _ts.utc(target_date.year, target_date.month, target_date.day, 21, 0, 0)

    if body == "moon":
        t0 = _ts.utc(target_date.year, target_date.month, target_date.day, 0, 0, 0)
        t1 = _ts.utc(target_date.year, target_date.month, target_date.day, 23, 59, 0)
        steps = int(24 * 60 / resolution_minutes)

    times = _ts.linspace(t0, t1, steps)
    results: list[AlignmentResult] = []

    # Vektorisiert: alle Zeitpunkte in einem einzigen Skyfield-Aufruf
    astrometric = (earth + observer).at(times).observe(sky_body)
    alt_vec, az_vec, _ = astrometric.apparent().altaz()
    az_degs = az_vec.degrees   # numpy-Array
    alt_degs = alt_vec.degrees  # numpy-Array

    # Azimut-Filter und Höhenfilter mit numpy
    az_diffs = np.abs(np.mod(az_degs - profile.azimuth_deg + 180, 360) - 180)
    mask = (az_diffs <= az_tolerance_deg) & (alt_degs >= -1.0)
    indices = np.where(mask)[0]

    for i in indices:
        az_deg = float(az_degs[i])
        alt_deg = float(alt_degs[i])
        az_diff = float(az_diffs[i])
        alignment_type, quality = _classify_alignment(alt_deg, profile, az_diff)
        if quality >= min_quality:
            results.append(AlignmentResult(
                time=times[i].utc_datetime(),
                body=body,
                alignment_type=alignment_type,
                celestial_azimuth=round(az_deg, 2),
                celestial_altitude=round(alt_deg, 3),
                azimuth_offset_deg=round(az_diff, 2),
                altitude_offset_deg=round(alt_deg - profile.angular_altitude_top_deg, 3),
                quality_score=quality,
                subject_profile=profile,
            ))

    # Duplikate innerhalb 5 Minuten → bestes behalten
    results.sort(key=lambda r: r.time)
    unique: list[AlignmentResult] = []
    for r in results:
        if not unique or (r.time - unique[-1].time).total_seconds() > 300:
            unique.append(r)
        elif r.quality_score > unique[-1].quality_score:
            unique[-1] = r

    unique.sort(key=lambda r: -r.quality_score)
    return unique


# ---------------------------------------------------------------------------
# Alte Funktionen (rückwärtskompatibel, delegieren jetzt intern)
# ---------------------------------------------------------------------------

def find_sun_alignment_times(
    observer_lat: float, observer_lon: float,
    target_azimuth: float,
    target_date: date,
    tolerance_deg: float = 2.0,
) -> list[datetime]:
    """
    Findet Zeitpunkte, an denen die Sonne den Ziel-Azimut kreuzt.
    Nur horizontale Prüfung (kein Höhenwinkel-Check).
    Für präzises 3D-Alignment → find_precise_alignment_times() verwenden.
    """
    w = _win_for(observer_lat, observer_lon, target_date)
    if w is not None:
        return w.azimuth_times("sun", target_azimuth, target_date,
                               tolerance_deg=tolerance_deg, alt_min=0.0, hours=(4, 21))

    results = []
    eph = _get_eph()
    observer = wgs84.latlon(observer_lat * N, observer_lon * E)
    earth = eph["earth"]
    sun = eph["sun"]

    t0 = _ts.utc(target_date.year, target_date.month, target_date.day, 4, 0, 0)
    t1 = _ts.utc(target_date.year, target_date.month, target_date.day, 21, 0, 0)
    times = _ts.linspace(t0, t1, 1020)

    # Vektorisiert: alle 1020 Zeitpunkte auf einmal
    astrometric = (earth + observer).at(times).observe(sun)
    alt_vec, az_vec, _ = astrometric.apparent().altaz()
    alt_degs = alt_vec.degrees
    az_degs = az_vec.degrees
    az_diffs = np.abs(np.mod(az_degs - target_azimuth + 180, 360) - 180)
    mask = (alt_degs > 0) & (az_diffs <= tolerance_deg)
    for i in np.where(mask)[0]:
        results.append(times[i].utc_datetime())

    unique = []
    for dt in results:
        if not unique or (dt - unique[-1]).total_seconds() > 300:
            unique.append(dt)
    return unique


def find_moon_alignment_times(
    observer_lat: float, observer_lon: float,
    target_azimuth: float,
    target_date: date,
    tolerance_deg: float = 2.0,
) -> list[datetime]:
    """
    Findet Zeitpunkte, an denen der Mond den Ziel-Azimut kreuzt.
    Für präzises 3D-Alignment → find_precise_alignment_times() verwenden.
    """
    w = _win_for(observer_lat, observer_lon, target_date)
    if w is not None:
        return w.azimuth_times("moon", target_azimuth, target_date,
                               tolerance_deg=tolerance_deg, alt_min=0.0, hours=(0, 24))

    results = []
    eph = _get_eph()
    observer = wgs84.latlon(observer_lat * N, observer_lon * E)
    earth = eph["earth"]
    moon = eph["moon"]

    t0 = _ts.utc(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    t1 = _ts.utc(target_date.year, target_date.month, target_date.day, 23, 59, 0)
    times = _ts.linspace(t0, t1, 1440)

    # Vektorisiert: alle 1440 Zeitpunkte auf einmal
    astrometric = (earth + observer).at(times).observe(moon)
    alt_vec, az_vec, _ = astrometric.apparent().altaz()
    alt_degs = alt_vec.degrees
    az_degs = az_vec.degrees
    az_diffs = np.abs(np.mod(az_degs - target_azimuth + 180, 360) - 180)
    mask = (alt_degs > 0) & (az_diffs <= tolerance_deg)
    for i in np.where(mask)[0]:
        results.append(times[i].utc_datetime())

    unique = []
    for dt in results:
        if not unique or (dt - unique[-1]).total_seconds() > 300:
            unique.append(dt)
    return unique


def calculate_focal_length_for_subject(
    subject_size_m: float,
    distance_m: float,
    sensor_width_mm: float = 36.0,   # Vollformat
    desired_frame_fill_pct: float = 0.3,
) -> float:
    """
    Berechnet die empfohlene Brennweite.
    subject_size_m: Breite/Höhe des Motivs in Metern
    distance_m: Entfernung in Metern
    desired_frame_fill_pct: Wie viel des Bildes soll das Motiv füllen (0-1)
    """
    angular_size_rad = math.atan(subject_size_m / distance_m)
    required_fov_rad = angular_size_rad / desired_frame_fill_pct
    focal_length = (sensor_width_mm / 2) / math.tan(required_fov_rad / 2)
    return round(focal_length, 0)
