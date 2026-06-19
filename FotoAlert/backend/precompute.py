"""
FotoAlert – Vorberechnungs-Skript (Drei-Schichten-Cache)

Schicht 1 – Geo-Cache (elevations.json):
  Geländehöhen per OpenTopoData, einmal pro Location, inkrementell.
  Separate Ausführung: python3 precompute_geo.py

Schicht 2 – Astronomy-Cache (calendar.json):
  Astronomische Daten + Chancen für 365 Tage, INKREMENTELL.
  Nur fehlende Location×Datum-Paare werden neu berechnet.
  Täglicher Cron: ~1 neuer Tag × N Locations (statt 365 × N komplett).
  Neue Location: nur diese Location für 365 Tage.
  Version-Bump (ALGORITHM_VERSION) → erzwingt vollständige Neuberechnung.

Schicht 3 – Wetter-Overlay:
  Wetterdaten werden zur Laufzeit in main.py per Open-Meteo angewendet.

Ausführung:
  cd FotoAlert/backend
  python3 precompute.py                           # Feed + inkrementeller Kalender
  python3 precompute.py --feed-only               # Nur 14-Tage Feed
  python3 precompute.py --calendar-only           # Nur Kalender (inkrementell)
  python3 precompute.py --full                    # Kalender vollständig neu berechnen
  python3 precompute.py --feed-only --location-id pfingstberg  # Nur eine Location

Automatisch täglich per Cron (00:01 Uhr UTC):
  1 0 * * * cd "/Users/stephan/Claude/Projects/Foto Location Guide/FotoAlert/backend" && python3 precompute.py >> logs/precompute.log 2>&1
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import math
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

# Sicherstellen, dass Imports aus dem Backend-Verzeichnis funktionieren
sys.path.insert(0, str(Path(__file__).parent))

from calculations.opportunity import find_opportunities, find_opportunities_multi_day
from calculations.astronomy import get_moon_earth_distance_km, MOON_DIAMETER_KM
from data.locations import LOCATIONS

# ─────────────────────────────────────────────────────────────────────────────
# Algorithmus-Version: Bump bei Änderungen an opportunity.py / astronomy.py,
# die andere Ergebnisse für bereits berechnete Tage liefern würden.
# Format: "MAJOR.MINOR" – Minor = kleine Scoring-Anpassung, Major = Struktur.
# ─────────────────────────────────────────────────────────────────────────────
ALGORITHM_VERSION = "1.3"  # US-57: Alignment-Qualitätsfilter (2°-Schärfezone)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "data" / "cache"

# ─────────────────────────────────────────────────────────────────────────────
# US-57: Alignment-Qualitätsfilter
# Nur Events innerhalb der Schärfezone werden in Feed und Kalender aufgenommen.
# ─────────────────────────────────────────────────────────────────────────────
ALIGNMENT_TOLERANCE_DEG = 2.0  # Maximale Abweichung in Azimut und Höhe

# ─────────────────────────────────────────────────────────────────────────────
# BUG-14: Health-Alert Schwellwerte
# Wenn nach dem Cron-Lauf weniger Events als diese Mindestwerte vorhanden sind,
# wird ein ERROR-Log erzeugt — damit Probleme nicht still bleiben.
# ─────────────────────────────────────────────────────────────────────────────
HEALTH_FEED_MIN      = 5   # Feed: mindestens 5 Events für 14 Tage
HEALTH_CAL_MIN       = 10  # Kalender: kritischer Schwellwert (ERROR)
REGRESSION_CAL_MIN   = 30  # Kalender: Regression-Schwellwert (WARNING)

# Eventtypen, die KEINEN Alignment-Filter erhalten
# (kein Celestial-Tracking auf Motivpunkt → composition_analysis ist None)
_ALIGNMENT_FILTER_EXEMPT = {
    "Goldene Stunde Morgen",
    "Goldene Stunde Abend",
    "Blaue Stunde",
    "Milchstraße",
    "Meteoritenschauer",
    "Sonnenfinsternis",
}


def _passes_alignment_filter(event_dict: dict) -> bool:
    """
    US-57: Gibt True zurück, wenn das Event den Alignment-Qualitätsfilter besteht.

    Logik:
    - Exempt-Types (Goldene/Blaue Stunde, Milchstraße usw.) → immer True
    - composition_analysis fehlt (None) → kein Deltawert verfügbar → True (Pass)
    - Sonst: |azimuth_delta_deg| ≤ TOLERANCE AND |altitude_delta_deg| ≤ TOLERANCE
    """
    event_type = event_dict.get("event_type", "")
    if event_type in _ALIGNMENT_FILTER_EXEMPT:
        return True

    ca = event_dict.get("composition_analysis")
    if ca is None:
        return True  # Kein Alignment-Datensatz vorhanden → kein Filter

    az_delta = ca.get("azimuth_delta_deg")
    alt_delta = ca.get("altitude_delta_deg")
    if az_delta is None or alt_delta is None:
        return True

    return abs(az_delta) <= ALIGNMENT_TOLERANCE_DEG and abs(alt_delta) <= ALIGNMENT_TOLERANCE_DEG


# ─────────────────────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────────────────────────────────────

def _location_hash(loc) -> str:
    """
    Kurzer Hash der Observer-Koordinaten einer Location.
    Ändert sich dieser Hash, werden alle Cache-Einträge für diese Location
    verworfen und neu berechnet.
    """
    raw = f"{loc.observer_lat:.6f},{loc.observer_lon:.6f}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]


def _composition_analysis(o) -> dict | None:
    """
    US-37: Berechnet die Kompositions-Analyse für Events mit Himmelsobjekt-Position.

    Kernidee: Der Beobachter sieht die Motivspitze unter einem bestimmten Elevationswinkel
    (arctan(Höhendifferenz / Entfernung)). Steht das Himmelsobjekt auf genau diesem Winkel,
    ist das Alignment perfekt – z.B. Mond genau auf Höhe der Fernsehturmspitze.

    Zusätzlich wird der scheinbare Durchmesser des Himmelskörpers in Metern (projiziert auf
    die Motivebene) berechnet, um das Größenverhältnis zum Motiv anzugeben.
    """
    loc = o.location
    if not (loc.subject_height_m and loc.distance_m and loc.distance_m > 0
            and o.celestial_altitude is not None and o.celestial_azimuth is not None):
        return None

    d = loc.distance_m

    # Höhe der Motivspitze über dem Augen-Niveau des Beobachters
    # US-62: observer_floor_height_m (Dach/Etage) erhöht den Beobachter → Motiv wirkt niedriger
    elev_diff = getattr(loc, "elevation_difference_m", 0.0) or 0.0
    observer_floor_h = getattr(loc, "observer_floor_height_m", 0.0) or 0.0
    height_above_observer = elev_diff - observer_floor_h + loc.subject_height_m

    # Scheinbarer Elevationswinkel der Motivspitze (in Grad)
    subject_apparent_elev_deg = math.degrees(math.atan(height_above_observer / d))

    # Δ Höhe: positiv = Objekt steht höher als Motivspitze, 0° = exaktes Alignment
    altitude_delta = round(o.celestial_altitude - subject_apparent_elev_deg, 2)

    # Azimut-Differenz (vorzeichenbehaftet, −180…+180)
    az_delta = round(((o.celestial_azimuth - (o.subject_azimuth or 0)) + 180) % 360 - 180, 2)

    # Metrische Versätze (projiziert auf die Motivebene in der Entfernung d)
    vertical_offset_m = round(d * math.tan(math.radians(altitude_delta)), 1)
    lateral_offset_m  = round(d * math.tan(math.radians(az_delta)), 1)

    # Scheinbarer Durchmesser des Himmelskörpers in Metern:
    #   apparent_size_m = distance_to_subject_m × angular_diameter_rad
    # Formel nach Stephan: tan(θ) ≈ θ für kleine Winkel (< 1°).
    #
    # Mond: Winkeldurchmesser wird aus der tatsächlichen Erde-Mond-Distanz
    #        zur Eventzeit berechnet (variiert ±7,5%: 356.500–406.700 km).
    # Sonne: Mittlerer Winkeldurchmesser 0,5333° (Variation ±1,7% vernachlässigt).
    event_type_val = o.event_type.value if hasattr(o.event_type, 'value') else str(o.event_type)
    is_moon = "Mond" in event_type_val or "Vollmond" in event_type_val

    moon_earth_distance_km: float | None = None
    if is_moon:
        try:
            moon_earth_distance_km = get_moon_earth_distance_km(o.shoot_time)
            # Winkeldurchmesser (rad) = physischer Durchmesser / Distanz
            angular_diameter_rad = MOON_DIAMETER_KM / moon_earth_distance_km
        except Exception:
            angular_diameter_rad = math.radians(0.5181)  # Fallback: mittlerer Wert
    else:
        angular_diameter_rad = math.radians(0.5333)      # Sonne: mittlerer Wert

    body_apparent_diameter_m = round(d * angular_diameter_rad, 1)

    # Größenverhältnis: scheinbarer Körperdurchmesser / Motivhöhe
    size_ratio = round(body_apparent_diameter_m / loc.subject_height_m, 3)

    # Höhen-Label
    if abs(altitude_delta) <= 0.5:
        alt_label = "🎯 Exaktes Alignment – Objekt auf Höhe der Motivspitze"
    elif 0.5 < altitude_delta <= 3.0:
        alt_label = "✨ Knapp über dem Motiv"
    elif altitude_delta > 3.0:
        alt_label = "☁️ Hoch über dem Motiv"
    else:
        alt_label = "⬇️ Noch unterhalb der Motivspitze"

    # Azimut-Label
    if abs(az_delta) <= 1.0:
        az_label = "Zentral ausgerichtet"
    elif abs(az_delta) <= 5.0:
        direction = "links" if az_delta < 0 else "rechts"
        az_label = f"Leicht {direction} versetzt"
    else:
        direction = "links" if az_delta < 0 else "rechts"
        az_label = f"Deutlich {direction} versetzt"

    # Verhältnis-Label
    if size_ratio >= 0.8:
        ratio_label = "Himmelskörper füllt Motiv fast aus"
    elif size_ratio >= 0.4:
        ratio_label = "Himmelskörper halb so groß wie Motiv"
    elif size_ratio >= 0.15:
        ratio_label = "Himmelskörper deutlich kleiner als Motiv"
    else:
        ratio_label = "Himmelskörper sehr klein relativ zum Motiv"

    body_name = "Mond" if is_moon else "Sonne"

    return {
        "subject_apparent_elevation_deg": round(subject_apparent_elev_deg, 2),
        "altitude_delta_deg": altitude_delta,
        "azimuth_delta_deg": az_delta,
        "vertical_offset_m": vertical_offset_m,
        "lateral_offset_m": lateral_offset_m,
        "body_apparent_diameter_m": body_apparent_diameter_m,
        "body_name": body_name,
        "size_ratio": size_ratio,
        "ratio_label": ratio_label,
        "altitude_label": alt_label,
        "azimuth_label": az_label,
        "moon_earth_distance_km": round(moon_earth_distance_km) if moon_earth_distance_km else None,
        "subject_height_m": loc.subject_height_m,
    }


def _serialize(o) -> dict:
    """Serialisiert ein PhotoOpportunity-Objekt als JSON-kompatibles Dict."""
    return {
        "id": o.id,
        "location_id": o.location.id,
        "location_name": o.location.name,
        "observer_lat": o.location.observer_lat,
        "observer_lon": o.location.observer_lon,
        "subject_lat": o.location.subject_lat,
        "subject_lon": o.location.subject_lon,
        "event_type": o.event_type.value,
        "title": o.title,
        "description": o.description,
        "shoot_time": o.shoot_time.isoformat(),
        "shoot_window_start": o.shoot_window_start.isoformat() if o.shoot_window_start else None,
        "shoot_window_end": o.shoot_window_end.isoformat() if o.shoot_window_end else None,
        "overall_score": round(min(1.0, o.overall_score), 3),
        "astronomy_score": round(min(1.0, o.astronomy_score), 3),
        "weather_score": 0.0,   # wird zur Laufzeit durch Wetter-Overlay ersetzt
        "location_score": round(o.location_score, 3),
        "camera_hints": [
            {
                "focal_length_mm": h.focal_length_mm,
                "aperture_suggestion": h.aperture_suggestion,
                "shutter_suggestion": h.shutter_suggestion,
                "iso_suggestion": h.iso_suggestion,
                "tripod_required": h.tripod_required,
                "extra_tip": h.extra_tip,
            }
            for h in (o.camera_hints or [])
        ],
        "subject_azimuth": o.subject_azimuth,
        "celestial_azimuth": o.celestial_azimuth,
        "celestial_altitude": o.celestial_altitude,
        "alert_priority": o.alert_priority,
        "weather_description": "",
        "elevation_difference_m": getattr(o.location, 'elevation_difference_m', 0.0),
        "moon_phase": o.astronomy_report.moon.phase_name if o.astronomy_report else None,
        "moon_illumination_pct": (
            round(o.astronomy_report.moon.illumination_pct, 1)
            if o.astronomy_report else None
        ),
        "sunrise_utc": (
            o.astronomy_report.sun.sunrise.isoformat()
            if o.astronomy_report and o.astronomy_report.sun.sunrise else None
        ),
        "sunset_utc": (
            o.astronomy_report.sun.sunset.isoformat()
            if o.astronomy_report and o.astronomy_report.sun.sunset else None
        ),
        # Golden hour & Blue hour – exakte Skyfield-Zeiten pro Location (für Filter + Detail)
        "golden_hour_morning_start": (
            o.astronomy_report.sun.golden_hour_morning_start.isoformat()
            if o.astronomy_report else None
        ),
        "golden_hour_morning_end": (
            o.astronomy_report.sun.golden_hour_morning_end.isoformat()
            if o.astronomy_report else None
        ),
        "golden_hour_evening_start": (
            o.astronomy_report.sun.golden_hour_evening_start.isoformat()
            if o.astronomy_report else None
        ),
        "golden_hour_evening_end": (
            o.astronomy_report.sun.golden_hour_evening_end.isoformat()
            if o.astronomy_report else None
        ),
        "blue_hour_morning_start": (
            o.astronomy_report.sun.blue_hour_morning_start.isoformat()
            if o.astronomy_report else None
        ),
        "blue_hour_morning_end": (
            o.astronomy_report.sun.blue_hour_morning_end.isoformat()
            if o.astronomy_report else None
        ),
        "blue_hour_evening_start": (
            o.astronomy_report.sun.blue_hour_evening_start.isoformat()
            if o.astronomy_report else None
        ),
        "blue_hour_evening_end": (
            o.astronomy_report.sun.blue_hour_evening_end.isoformat()
            if o.astronomy_report else None
        ),
        "composition_analysis": _composition_analysis(o),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Schicht 1: Geo-Cache (Elevations)
# ─────────────────────────────────────────────────────────────────────────────

async def fetch_elevations(force_refetch_ids: set[str] | None = None) -> dict:
    """
    Schicht 1 – Geo-Cache: Geländehöhen per OpenTopoData (EUDEM 25m).
    Berechnet elevation_difference_m = subject_elevation - observer_elevation.
    Inkrementell: nur Locations ohne Cache-Eintrag werden neu abgerufen.
    Gibt dict location_id → {observer_m, subject_m, difference_m} zurück.
    """
    TOPODATA_URL = "https://api.opentopodata.org/v1/eudem25m"
    results: dict[str, dict] = {}

    # Bestehenden Cache laden (nur fehlende Locations neu fetchen)
    elev_path = CACHE_DIR / "elevations.json"
    existing: dict[str, dict] = {}
    if elev_path.exists():
        try:
            existing = json.loads(elev_path.read_text(encoding="utf-8")).get("elevations", {})
        except Exception:
            pass

    # Locations mit subject-Koordinaten, die noch nicht im Cache sind
    # (oder in force_refetch_ids → Koordinaten geändert, Elevation neu abrufen)
    to_fetch = [
        loc for loc in LOCATIONS
        if loc.subject_lat is not None and loc.subject_lon is not None
        and (loc.id not in existing or (force_refetch_ids and loc.id in force_refetch_ids))
    ]

    if not to_fetch:
        logger.info("  Elevation-Cache vollständig, kein API-Abruf nötig")
        return existing

    logger.info("  Fetche Geländehöhen für %d Locations von OpenTopoData …", len(to_fetch))

    # OpenTopoData: max 100 Locations pro Request, beide Punkte (observer + subject) je Location
    BATCH = 40  # 40 Locations × 2 Punkte = 80 Koordinaten pro Request
    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(0, len(to_fetch), BATCH):
            batch = to_fetch[i:i + BATCH]
            # Koordinaten: observer zuerst, dann subject (alternierend)
            coords = "|".join(
                f"{loc.observer_lat},{loc.observer_lon}|{loc.subject_lat},{loc.subject_lon}"
                for loc in batch
            )
            try:
                resp = await client.get(TOPODATA_URL, params={"locations": coords})
                resp.raise_for_status()
                data = resp.json()
                elevs = data.get("results", [])
                for j, loc in enumerate(batch):
                    obs_elev = elevs[j * 2]["elevation"] if j * 2 < len(elevs) else None
                    sub_elev = elevs[j * 2 + 1]["elevation"] if j * 2 + 1 < len(elevs) else None
                    if obs_elev is not None and sub_elev is not None:
                        diff = round(sub_elev - obs_elev, 1)
                        results[loc.id] = {
                            "observer_elevation_m": round(obs_elev, 1),
                            "subject_elevation_m": round(sub_elev, 1),
                            "elevation_difference_m": diff,
                        }
                        logger.info(
                            "    %s: obs=%.1fm sub=%.1fm Δ=%+.1fm",
                            loc.name, obs_elev, sub_elev, diff,
                        )
                    else:
                        logger.warning("    %s: unvollständige Antwort", loc.name)
            except Exception as e:
                logger.error("  OpenTopoData Batch-Fehler: %s", e)
            await asyncio.sleep(1.1)  # Rate-Limit: 1 Req/s

    # Existierende Einträge + neue zusammenführen
    merged = {**existing, **results}
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# Schicht 2a: 14-Tage Feed (nicht inkrementell – immer frisch)
# ─────────────────────────────────────────────────────────────────────────────

async def compute_feed(today: date) -> list[dict]:
    """
    14-Tage Astronomy-Feed für alle Locations (ohne Wetter).
    Wird immer komplett neu berechnet – ist schnell und enthält
    den nächsten 2-Wochen-Horizont vollständig aktuell.
    """
    results: list[dict] = []
    for i, loc in enumerate(LOCATIONS):
        logger.info("  Feed [%d/%d] %s", i + 1, len(LOCATIONS), loc.name)
        try:
            opps = await find_opportunities_multi_day(
                loc, today, days=14,
                forecast=None, min_score=0.30,
                astronomy_only=True,
            )
            serialized = [_serialize(o) for o in opps]
            filtered = [e for e in serialized if _passes_alignment_filter(e)]
            skipped = len(serialized) - len(filtered)
            if skipped:
                logger.info("    US-57: %d Event(s) außerhalb ±%.0f°-Schärfezone gefiltert", skipped, ALIGNMENT_TOLERANCE_DEG)
            results.extend(filtered)
        except Exception as e:
            logger.error("    Fehler bei %s: %s", loc.name, e)
    results.sort(key=lambda r: (r["shoot_time"], -r["overall_score"]))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Schicht 2b: 365-Tage Kalender (INKREMENTELL)
# ─────────────────────────────────────────────────────────────────────────────

async def compute_calendar_incremental(today: date, force_full: bool = False) -> tuple[list[dict], dict]:
    """
    Schicht 2 – Astronomy-Cache: Inkrementeller 365-Tage Kalender.

    Logik:
    - Lädt vorhandenen calendar.json Cache
    - Prüft algorithm_version: Mismatch → alles verwerfen (force_full)
    - Pro Location: prüft coordinates_hash → Koordinaten geändert → Location neu
    - Berechnet nur fehlende Location×Datum-Kombinationen
    - Bereinigt Events vor heute (veraltet)
    - Gibt (events_list, computed_locations_meta) zurück

    Ergebnis:
    - Täglich: ~1 neuer Tag × N Locations (statt 365 × N)
    - Neue Location: 365 Tage nur für diese Location
    - ALGORITHM_VERSION-Bump: einmaliger Vollneu-Lauf
    """
    cal_path = CACHE_DIR / "calendar.json"

    # Cache laden
    existing_events: list[dict] = []
    existing_meta: dict = {}
    cache_version: str | None = None

    if cal_path.exists() and not force_full:
        try:
            cached = json.loads(cal_path.read_text(encoding="utf-8"))
            cache_version = cached.get("algorithm_version")
            existing_events = cached.get("events", [])
            existing_meta = cached.get("computed_locations", {})
            logger.info("  Cache geladen: %d Events, Version %s", len(existing_events), cache_version)
        except Exception as e:
            logger.warning("  Kalender-Cache nicht lesbar: %s – Neuberechnung", e)

    # Version-Check
    if force_full or cache_version != ALGORITHM_VERSION:
        if force_full:
            logger.info("  ⚙️  --full: Vollständige Neuberechnung erzwungen")
        else:
            logger.info(
                "  ⚠️  Algorithmus-Version geändert (%s → %s) – vollständige Neuberechnung",
                cache_version, ALGORITHM_VERSION,
            )
        existing_events = []
        existing_meta = {}

    # Ziel-Datumsbereich: heute bis heute+364
    target_range: set[str] = {(today + timedelta(days=i)).isoformat() for i in range(365)}
    today_str = today.isoformat()

    # Veraltete Events bereinigen (vor heute)
    valid_events = [e for e in existing_events if e["shoot_time"][:10] >= today_str]
    pruned = len(existing_events) - len(valid_events)
    if pruned > 0:
        logger.info("  Veraltete Events bereinigt: %d", pruned)

    new_meta: dict = {}
    total_skipped = 0
    total_computed = 0

    for i, loc in enumerate(LOCATIONS):
        coords_hash = _location_hash(loc)
        loc_meta = existing_meta.get(loc.id, {})

        # Koordinaten-Änderung → alle alten Events dieser Location verwerfen
        if loc_meta.get("coordinates_hash") != coords_hash:
            if loc_meta:
                logger.info("  %s: Koordinaten geändert – komplette Neuberechnung", loc.name)
            valid_events = [e for e in valid_events if e["location_id"] != loc.id]
            dates_needed = sorted(target_range)
        else:
            # Nur fehlende Daten berechnen
            computed_set: set[str] = set(loc_meta.get("computed_dates", []))
            dates_needed = sorted(target_range - computed_set)

        skipped = len(target_range) - len(dates_needed)
        total_skipped += skipped
        total_computed += len(dates_needed)

        if not dates_needed:
            # Vollständig gecacht → meta übernehmen, auf target_range beschränken
            old_computed = set(loc_meta.get("computed_dates", []))
            new_meta[loc.id] = {
                "coordinates_hash": coords_hash,
                "computed_dates": sorted(old_computed & target_range),
            }
            continue

        logger.info(
            "  Kalender [%d/%d] %s: %d neue Tage (%d gecacht)",
            i + 1, len(LOCATIONS), loc.name, len(dates_needed), skipped,
        )

        new_events_for_loc: list[dict] = []
        for d_str in dates_needed:
            d = date.fromisoformat(d_str)
            try:
                opps = await find_opportunities(
                    loc, d, forecast=None, min_score=0.40, astronomy_only=True,
                )
                new_events_for_loc.extend(
                    e for e in (_serialize(o) for o in opps)
                    if _passes_alignment_filter(e)
                )
            except Exception as e:
                logger.error("    Fehler %s %s: %s", loc.name, d_str, e)

        valid_events.extend(new_events_for_loc)

        # Meta für diese Location aktualisieren
        old_computed = set(loc_meta.get("computed_dates", []))
        all_computed = (old_computed | set(dates_needed)) & target_range
        new_meta[loc.id] = {
            "coordinates_hash": coords_hash,
            "computed_dates": sorted(all_computed),
        }

        # Event Loop gelegentlich freigeben
        await asyncio.sleep(0)

    logger.info(
        "  Zusammenfassung: %d neu berechnet, %d aus Cache",
        total_computed, total_skipped,
    )

    # Sortierung: Zeit aufsteigend, bei Gleichstand Score absteigend
    valid_events.sort(key=lambda r: (r["shoot_time"], -r["overall_score"]))
    return valid_events, new_meta


# ─────────────────────────────────────────────────────────────────────────────
# Hauptfunktion
# ─────────────────────────────────────────────────────────────────────────────

async def main(args: argparse.Namespace) -> None:
    t0 = time.time()
    logger.info("=== FotoAlert Vorberechnung startet (Algorithmus v%s) ===", ALGORITHM_VERSION)
    logger.info("%d Locations geladen", len(LOCATIONS))

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today()
    computed_at = datetime.now(timezone.utc).isoformat()

    run_feed = not args.calendar_only
    run_calendar = not args.feed_only
    location_id: str | None = getattr(args, "location_id", None)
    feed_path = CACHE_DIR / "opportunities.json"
    elev_path = CACHE_DIR / "elevations.json"

    # ── SINGLE-LOCATION FLOW (nach Koordinaten-Änderung via PATCH) ──────────
    if location_id:
        single_loc_list = [l for l in LOCATIONS if l.id == location_id]
        if not single_loc_list:
            logger.error("Location '%s' nicht gefunden – Abbruch", location_id)
            return
        loc = single_loc_list[0]
        logger.info("── Single-Location Recompute: %s ──", loc.name)

        # Elevation für diese Location neu abrufen (Koordinaten geändert)
        logger.info("  Elevation neu abrufen …")
        elevations = await fetch_elevations(force_refetch_ids={location_id})
        elev_path.write_text(
            json.dumps({"computed_at": computed_at, "elevations": elevations},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if location_id in elevations:
            elev_val = elevations[location_id]["elevation_difference_m"]
            try:
                object.__setattr__(loc, "elevation_difference_m", elev_val)
            except Exception:
                setattr(loc, "elevation_difference_m", elev_val)
            logger.info("  ✅ Elevation: Δ%+.1f m", elev_val)

        if run_feed:
            logger.info("  14-Tage Feed für %s …", loc.name)
            t1 = time.time()
            try:
                opps = await find_opportunities_multi_day(
                    loc, today, days=14, forecast=None, min_score=0.30, astronomy_only=True,
                )
                new_events = [_serialize(o) for o in opps]
            except Exception as e:
                logger.error("  Fehler: %s", e)
                new_events = []
            # Merge: bestehende Events für andere Locations behalten, diese ersetzen
            existing_events: list[dict] = []
            if feed_path.exists():
                try:
                    existing_events = json.loads(feed_path.read_text(encoding="utf-8")).get("opportunities", [])
                except Exception:
                    pass
            merged = [e for e in existing_events if e["location_id"] != location_id] + new_events
            merged.sort(key=lambda r: (r["shoot_time"], -r["overall_score"]))
            feed_path.write_text(
                json.dumps({"computed_at": computed_at, "opportunities": merged}, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info(
                "  ✅ Feed: %d neue Events für %s, %d gesamt (%.1fs)",
                len(new_events), loc.name, len(merged), time.time() - t1,
            )
        logger.info("=== Single-Location Recompute abgeschlossen in %.1fs ===", time.time() - t0)
        return  # Single-Location-Flow abgeschlossen

    # ── STANDARD FLOW (alle Locations) ──────────────────────────────────────
    # ── Schicht 1: Geo-Cache (Elevations) ────────────────────────────────────
    logger.info("── Geo-Cache: Geländehöhen (OpenTopoData EUDEM 25m) ──")
    t_elev = time.time()
    elevations = await fetch_elevations()
    elev_path.write_text(
        json.dumps({"computed_at": computed_at, "elevations": elevations},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("✅ elevations.json: %d Locations (%.1fs)", len(elevations), time.time() - t_elev)

    # Locations mit gecachten Elevationen patchen
    elev_by_id = {lid: v["elevation_difference_m"] for lid, v in elevations.items()}
    for loc in LOCATIONS:
        if loc.id in elev_by_id:
            try:
                object.__setattr__(loc, "elevation_difference_m", elev_by_id[loc.id])
            except Exception:
                setattr(loc, "elevation_difference_m", elev_by_id[loc.id])

    # ── Schicht 2a: 14-Tage Feed ─────────────────────────────────────────────
    if run_feed:
        logger.info("── Astronomy-Feed: 14 Tage (komplett frisch) ────────")
        t1 = time.time()
        feed = await compute_feed(today)
        feed_path.write_text(
            json.dumps({"computed_at": computed_at, "opportunities": feed},
                       ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("✅ opportunities.json: %d Events (%.1fs)", len(feed), time.time() - t1)
        # BUG-14: Health-Alert Feed
        if len(feed) < HEALTH_FEED_MIN:
            logger.error(
                "🚨 HEALTH-ALERT [%s]: opportunities.json enthält nur %d Event(s) "
                "(Schwellwert: %d). Mögliche Ursachen: Skyfield-Fehler, API-Timeout "
                "oder fehlerhafte Location-Daten. Bitte Logs prüfen.",
                computed_at, len(feed), HEALTH_FEED_MIN,
            )

    # ── Schicht 2b: 365-Tage Kalender (inkrementell) ─────────────────────────
    if run_calendar:
        logger.info("── Astronomy-Cache: Kalender 365 Tage (inkrementell) ")
        t2 = time.time()
        calendar, computed_meta = await compute_calendar_incremental(
            today, force_full=args.full
        )
        cal_path = CACHE_DIR / "calendar.json"
        cal_path.write_text(
            json.dumps(
                {
                    "algorithm_version": ALGORITHM_VERSION,
                    "computed_at": computed_at,
                    "computed_locations": computed_meta,
                    "events": calendar,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        logger.info("✅ calendar.json: %d Events (%.1fs)", len(calendar), time.time() - t2)
        # BUG-14: Health-Alert Kalender
        if len(calendar) < HEALTH_CAL_MIN:
            logger.error(
                "🚨 HEALTH-ALERT [%s]: calendar.json enthält nur %d Event(s) "
                "(kritischer Schwellwert: %d). Kalender ist praktisch leer — "
                "Jahresansicht in der App wird leer sein. Bitte Logs prüfen.",
                computed_at, len(calendar), HEALTH_CAL_MIN,
            )
        elif len(calendar) < REGRESSION_CAL_MIN:
            logger.warning(
                "⚠️  HEALTH-WARN [%s]: calendar.json enthält nur %d Event(s) "
                "(Regression-Schwellwert: %d). Erwartet werden ≥ %d Events.",
                computed_at, len(calendar), REGRESSION_CAL_MIN, REGRESSION_CAL_MIN,
            )

    logger.info("=== Vorberechnung abgeschlossen in %.1fs ===", time.time() - t0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FotoAlert Vorberechnung")
    parser.add_argument("--feed-only", action="store_true", help="Nur 14-Tage Feed berechnen")
    parser.add_argument("--calendar-only", action="store_true", help="Nur Kalender berechnen")
    parser.add_argument("--full", action="store_true", help="Kalender vollständig neu berechnen (ignoriert Cache)")
    parser.add_argument("--location-id", default=None, help="Nur diese eine Location neu berechnen (Single-Location-Recompute nach PATCH)")
    args = parser.parse_args()
    asyncio.run(main(args))
