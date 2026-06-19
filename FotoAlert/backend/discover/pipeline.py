"""
Scout-Tab Pipeline: Ephemeride für Mond-Alignment-Chancen.

Ablauf für jeden der nächsten 14 Tage:
  1. Lichtfenster bestimmen (goldene + blaue Stunde, morgens + abends)
  2. Mond-Positionen im 15-min-Raster per Motiv berechnen
     (topozentrisch korrekt: Subject-Koordinaten statt Berlin-Zentrum-Approximation)
  3. Standpunkt-Distanz d = apex_effective_m / tan(alt_moon) berechnen
  4. Standpunkt S via destination_point(Motiv → Mond-Gegenrichtung, d)
  5. d-Gate: 100 m ≤ d ≤ 13.000 m, moon_alt ≥ 5°
  6. Score berechnen
  7. Je Motiv/Tag/Session: nur bestes Ergebnis behalten (Dedup)
  8. Wetter-Score ergänzen (open-meteo, async)
  9. Als JSON speichern
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from calculations.astronomy import CelestialPosition, calculate_sun_info, get_body_position
from calculations.weather import WeatherForecast, calculate_photo_weather_score, fetch_weather_forecast
from discover.geometry import bearing_between, destination_point
from discover.subjects import SUBJECTS, DiscoverSubject

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

# Berliner Zentrum: nur für Sonnen-Lichtfenster (Variation < 1 min über 50 km)
_SUN_REF_LAT = 52.52
_SUN_REF_LON = 13.40

D_MIN_M = 100.0        # Mindestdistanz Standpunkt–Motiv
D_MAX_M = 13_000.0     # Maximaldistanz
MOON_ALT_MIN_DEG = 5.0  # Mond muss sichtbar über Horizont sein
SAMPLE_INTERVAL_MIN = 15  # Minuten zwischen Samplings

MOON_ANGULAR_DIAM_DEG = 0.52  # Mittlerer Monddurchmesser in Bogengrad

# Score-Gewichte (gemäß Spec US-70)
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
    subject_id: str
    subject_name: str
    subject_lat: float
    subject_lon: float
    day: str                   # ISO date, z.B. "2026-06-20"
    session: str               # "golden_morning" | "blue_morning" | "golden_evening" | "blue_evening"
    dt_utc: str                # ISO datetime UTC des besten Moments
    moon_azimuth_deg: float    # Azimut des Mondes vom Motiv aus
    moon_altitude_deg: float   # Höhe des Mondes über Horizont
    moon_illumination_pct: float
    distance_m: float          # Standpunkt–Motiv-Distanz
    standpoint_lat: float
    standpoint_lon: float
    focal_length_equiv_mm: float   # geschätzte Brennweite (KB-Äquivalent)
    score: float               # 0–1 Gesamt-Score
    score_alignment: float
    score_phase: float
    score_licht: float
    score_komposition: float
    score_wetter: float
    weather_description: str


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _sample_window(start: Optional[datetime], end: Optional[datetime]) -> list[datetime]:
    """Alle 15-Minuten-Zeitpunkte innerhalb eines Lichtfensters."""
    if start is None or end is None or end <= start:
        return []
    result = []
    t = start
    while t <= end:
        result.append(t)
        t += timedelta(minutes=SAMPLE_INTERVAL_MIN)
    return result


def _moon_illumination(phase_fraction: float) -> float:
    """Beleuchtungsanteil aus Phasen-Fraction (0=Neumond, 0.5=Vollmond, 1=Neumond)."""
    # phase_fraction → Illuminationsanteil: cos²(π * phase_fraction) geht nicht,
    # korrekte Formel: illumination = (1 - cos(2π * phase_fraction)) / 2
    return (1.0 - math.cos(2 * math.pi * phase_fraction)) / 2.0


def _compute_d(subject: DiscoverSubject, moon_alt_deg: float) -> Optional[float]:
    """
    Horizontalentfernung, von der der Mond genau über der Motivspitze erscheint.
    d = apex_effective_m / tan(moon_altitude)
    Gibt None zurück wenn d außerhalb [D_MIN_M, D_MAX_M].
    """
    if moon_alt_deg <= 0.5:
        return None
    if subject.apex_effective_m <= 0:
        return None   # Motiv nicht höher als Beobachter — Inversberechnung nicht sinnvoll
    alt_rad = math.radians(moon_alt_deg)
    d = subject.apex_effective_m / math.tan(alt_rad)
    if D_MIN_M <= d <= D_MAX_M:
        return d
    return None


def _focal_length_for_moon(d_m: float, subject: DiscoverSubject) -> float:
    """
    Schätzt die optimale Brennweite (KB-Äquivalent, mm),
    so dass Mond und Motiv zusammen ~20% des Bildwinkels füllen.
    Ziel: Mond und Motivspitze füllen ~10° des vertikalen Bildwinkels.
    Sensorgröße: 24mm (KB-Vollformat vertikal).
    """
    # Winkelhöhe des Motivs vom Standpunkt:
    subject_angle_deg = math.degrees(math.atan(subject.apex_effective_m / d_m))
    # Wir wollen, dass Motiv + Moon zusammen in ~15° Bildwinkel passen
    desired_fov_v_deg = max(subject_angle_deg * 2 + MOON_ANGULAR_DIAM_DEG * 2, 4.0)
    # f = sensor_half / tan(fov/2) → KB vertikal = 24 mm
    sensor_half_mm = 12.0
    f = sensor_half_mm / math.tan(math.radians(desired_fov_v_deg / 2))
    return round(f / 10) * 10  # auf 10mm runden


def _score_alignment(moon_alt_deg: float) -> float:
    """
    Alignment-Score: Mond nahe 20–40° Höhe optimal (gute Geometrie,
    nicht zu hoch = zu nah, nicht zu flach = zu weit).
    """
    if moon_alt_deg < MOON_ALT_MIN_DEG:
        return 0.0
    # Gaußförmige Kurve um 25°
    opt = 25.0
    sigma = 20.0
    return math.exp(-((moon_alt_deg - opt) ** 2) / (2 * sigma ** 2))


def _score_phase(illumination_pct: float) -> float:
    """Mond-Phasen-Score: Vollmond = 1.0, Neumond = 0.0."""
    # Leichte Bevorzugung von 70–100%: dramatisch, aber auch Sichel fotogen
    x = illumination_pct / 100.0
    if x >= 0.7:
        return 1.0
    if x >= 0.4:
        return 0.7 + (x - 0.4) / 0.3 * 0.3
    return x / 0.4 * 0.7


def _score_licht(session: str) -> float:
    """Lichtqualitäts-Score nach Tageszeit und Session."""
    return {
        "golden_evening": 1.00,
        "golden_morning": 0.90,
        "blue_evening":   0.80,
        "blue_morning":   0.70,
    }.get(session, 0.5)


def _score_komposition(subject: DiscoverSubject, d_m: float) -> float:
    """
    Kompositions-Score: wie gut passt das Seitenverhältnis von Mond und Motiv?
    subject_angular_width / moon_angular_diameter → ideal 0.5–3.0
    """
    if d_m <= 0:
        return 0.0
    subject_ang = math.degrees(2 * math.atan(subject.subject_width_m / 2 / d_m))
    ratio = subject_ang / MOON_ANGULAR_DIAM_DEG
    # Optimum bei ratio=1.5, breite Toleranz
    if 0.5 <= ratio <= 3.0:
        return 1.0 - abs(ratio - 1.5) / 3.0
    elif ratio < 0.5:
        return ratio / 0.5 * 0.7  # Motiv sehr klein
    else:
        return max(0.0, 1.0 - (ratio - 3.0) / 5.0)  # Motiv sehr groß


def _compute_score(
    moon_alt: float,
    illumination_pct: float,
    session: str,
    subject: DiscoverSubject,
    d_m: float,
    weather_score: float,
) -> tuple[float, float, float, float, float]:
    """Gibt (total, s_align, s_phase, s_licht, s_kompo) zurück."""
    sa = _score_alignment(moon_alt)
    sp = _score_phase(illumination_pct)
    sl = _score_licht(session)
    sk = _score_komposition(subject, d_m)
    sw = weather_score

    # Gate: Horizont (moon alt ≥ 5°) → bereits gefiltert; Lichtfenster → per Definition
    total = W_ALIGNMENT * sa + W_PHASE * sp + W_LICHT * sl + W_KOMPOSITION * sk + W_WETTER * sw
    return total, sa, sp, sl, sk


# ---------------------------------------------------------------------------
# Wetter (gecacht pro Standort)
# ---------------------------------------------------------------------------

_weather_cache: dict[str, WeatherForecast] = {}


async def _get_weather(lat: float, lon: float) -> Optional[WeatherForecast]:
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


# ---------------------------------------------------------------------------
# Kern-Pipeline
# ---------------------------------------------------------------------------

async def run_pipeline(days: int = 14) -> list[ScoutOpportunity]:
    """
    Berechnet alle Scout-Chancen für die nächsten `days` Tage.
    Gibt eine nach Score absteigende Liste zurück.
    """
    today = date.today()
    all_opportunities: list[ScoutOpportunity] = []

    # --- Schritt 1: Alle Sampling-Zeitpunkte für die nächsten 14 Tage sammeln ---
    # Format: {day_str: {"golden_morning": [...], "blue_morning": [...], ...}}
    day_sessions: dict[str, dict[str, list[datetime]]] = {}

    log.info("Berechne Lichtfenster für %d Tage...", days)
    for delta in range(days):
        d = today + timedelta(days=delta)
        sun = calculate_sun_info(_SUN_REF_LAT, _SUN_REF_LON, d)
        sessions = {
            "blue_morning":   _sample_window(sun.blue_hour_morning_start,  sun.blue_hour_morning_end),
            "golden_morning": _sample_window(sun.golden_hour_morning_start, sun.golden_hour_morning_end),
            "golden_evening": _sample_window(sun.golden_hour_evening_start, sun.golden_hour_evening_end),
            "blue_evening":   _sample_window(sun.blue_hour_evening_start,   sun.blue_hour_evening_end),
        }
        day_sessions[d.isoformat()] = sessions

    # --- Schritt 2: Wetter-Forecasts für alle Subjekte vorab laden (parallel) ---
    # Mondpositionen werden per Subject in Schritt 3 berechnet (topozentrisch korrekt).
    log.info("Lade Wetter-Forecasts für %d Motive...", len(SUBJECTS))
    weather_tasks = {
        s.id: asyncio.create_task(_get_weather(s.lat, s.lon)) for s in SUBJECTS
    }
    await asyncio.gather(*weather_tasks.values(), return_exceptions=True)

    # --- Schritt 3–7: Je Motiv, Tag, Session, Zeitpunkt ---
    log.info("Pipeline läuft (%d Motive × %d Tage)...", len(SUBJECTS), days)

    for subject in SUBJECTS:
        weather_fc = await _get_weather(subject.lat, subject.lon)

        # Mondpositionen für dieses Motiv an dessen tatsächlichen Koordinaten berechnen.
        # Cache: pro Subject einmal aufgebaut, über alle Tage/Sessions wiederverwendet.
        moon_pos_cache: dict[datetime, Optional[CelestialPosition]] = {}

        for day_str, sessions in day_sessions.items():
            for session_name, timestamps in sessions.items():
                # Bestes Ergebnis für diese Kombination (Motiv/Tag/Session)
                best: Optional[ScoutOpportunity] = None

                for dt in timestamps:
                    if dt not in moon_pos_cache:
                        moon_pos_cache[dt] = get_body_position(
                            subject.lat, subject.lon, "moon", dt
                        )
                    moon = moon_pos_cache.get(dt)
                    if moon is None:
                        continue
                    if moon.altitude < MOON_ALT_MIN_DEG:
                        continue

                    # Distanz berechnen
                    d = _compute_d(subject, moon.altitude)
                    if d is None:
                        continue

                    # Standpunkt: gegenüberliegende Seite des Motivs
                    standpoint_bearing = (moon.azimuth + 180.0) % 360.0
                    sp_lat, sp_lon = destination_point(subject.lat, subject.lon, standpoint_bearing, d)

                    # Mond-Beleuchtung (aus Skyfield moon.distance_au → phase aus Astronomie-Modul)
                    # Vereinfachung: Illumination über skyfield nicht direkt verfügbar via get_body_position.
                    # Wir nutzen eine Annäherung über den Phase-Fraction aus der Mondphase des Tages.
                    illumination_pct = _approx_illumination(dt)

                    # Wetter-Score
                    weather_score = 0.5  # Default
                    weather_description = "Unbekannt"
                    if weather_fc is not None:
                        hw = weather_fc.get_at(dt)
                        if hw is not None:
                            weather_score = min(1.0, calculate_photo_weather_score(hw))
                            weather_description = _weather_desc(hw)

                    # Score
                    total, sa, sp_, sl, sk = _compute_score(
                        moon.altitude, illumination_pct, session_name,
                        subject, d, weather_score
                    )

                    focal = _focal_length_for_moon(d, subject)

                    opp = ScoutOpportunity(
                        subject_id=subject.id,
                        subject_name=subject.name,
                        subject_lat=subject.lat,
                        subject_lon=subject.lon,
                        day=day_str,
                        session=session_name,
                        dt_utc=dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        moon_azimuth_deg=round(moon.azimuth, 1),
                        moon_altitude_deg=round(moon.altitude, 1),
                        moon_illumination_pct=round(illumination_pct, 1),
                        distance_m=round(d, 0),
                        standpoint_lat=round(sp_lat, 6),
                        standpoint_lon=round(sp_lon, 6),
                        focal_length_equiv_mm=focal,
                        score=round(total, 4),
                        score_alignment=round(sa, 4),
                        score_phase=round(sp_, 4),
                        score_licht=round(sl, 4),
                        score_komposition=round(sk, 4),
                        score_wetter=round(weather_score, 4),
                        weather_description=weather_description,
                    )

                    if best is None or total > best.score:
                        best = opp

                if best is not None:
                    all_opportunities.append(best)

    # Absteigende Sortierung nach Score
    all_opportunities.sort(key=lambda o: o.score, reverse=True)
    log.info("Pipeline abgeschlossen: %d Chancen gefunden.", len(all_opportunities))
    return all_opportunities


# ---------------------------------------------------------------------------
# Hilfsfunktionen für Wetter & Mondphase
# ---------------------------------------------------------------------------

def _approx_illumination(dt: datetime) -> float:
    """
    Approximiert die Mondbeleuchtung in % für einen Zeitpunkt.
    Nutzt einen vereinfachten synodischen Mondzyklus (29.53 Tage).
    Referenz-Vollmond: 2024-01-25 17:54 UTC
    """
    REF_FULL_MOON = datetime(2024, 1, 25, 17, 54, tzinfo=timezone.utc)
    SYNODIC_PERIOD_DAYS = 29.530589
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    elapsed = (dt - REF_FULL_MOON).total_seconds() / 86400
    phase_fraction = (elapsed % SYNODIC_PERIOD_DAYS) / SYNODIC_PERIOD_DAYS
    # phase_fraction: 0 = Vollmond, 0.5 = Neumond
    illumination = (1.0 + math.cos(2 * math.pi * phase_fraction)) / 2.0
    return round(illumination * 100, 1)


def _weather_desc(hw) -> str:
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
# Cache-Schreib-Funktion
# ---------------------------------------------------------------------------

async def refresh_discover_cache(cache_path: Path) -> list[dict]:
    """
    Führt die Pipeline aus und schreibt das Ergebnis in die Cache-Datei.
    Gibt die Rohdaten als dict-Liste zurück.
    """
    _weather_cache.clear()
    opportunities = await run_pipeline()
    data = [asdict(o) for o in opportunities]
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "count": len(data),
                "opportunities": data,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    log.info("discover.json geschrieben: %d Chancen", len(data))
    return data


# ---------------------------------------------------------------------------
# CLI-Schnelltest
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )

    async def _main():
        cache_path = Path(__file__).parent.parent / "cache" / "discover.json"
        data = await refresh_discover_cache(cache_path)
        print(f"\n=== Top 5 Scout-Chancen ===")
        for o in data[:5]:
            print(
                f"  {o['day']} {o['session']:18s} | {o['subject_name']:30s} | "
                f"Mond {o['moon_altitude_deg']:5.1f}° az {o['moon_azimuth_deg']:5.1f}° | "
                f"d={o['distance_m']:6.0f}m | Score {o['score']:.3f} | "
                f"f={o['focal_length_equiv_mm']}mm"
            )

    asyncio.run(_main())
