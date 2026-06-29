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
from calculations.astronomy import get_moon_earth_distance_km, MOON_DIAMETER_KM, get_body_position
from data.locations import LOCATIONS, PhotoLocation, LocationCategory
from data.store import LocationStore

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
    "Neumond",
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


# Felder, die ein Location-Override überschreiben darf — identisch zur Whitelist in
# main.py:_load_location_overrides (TASK-17), damit Server und Recompute denselben Stand sehen.
_OVERRIDE_FIELDS = (
    "observer_lat", "observer_lon", "subject_lat", "subject_lon",
    "name", "description", "observer_floor_height_m", "focal_length_suggestions",
)


def _apply_location_overrides() -> int:
    """
    BUG-29: Wendet die in SQLite persistierten Location-Overrides (Koordinaten-/Name-
    Korrekturen aus `PATCH /locations/{id}`) auf die Basis-`LOCATIONS` an.

    Vorher lud `precompute.py` ausschließlich die hartcodierten Basis-Koordinaten aus
    `data/locations.py` und ignorierte jeden Override. Folge: Nach einer Koordinaten-
    Korrektur rechnete der Recompute (Single **und** nächtlicher Vollkalauf) weiter mit
    den alten Koordinaten → der `coordinates_hash` blieb gleich → 0 Events neu berechnet →
    Feed/Kalender zeigten dauerhaft veraltete GPS-Daten, obwohl die Location-Detail-Ansicht
    (live aus dem Override) bereits korrekt war.

    Spiegelt bewusst die Whitelist + setattr-Logik aus main.py:_load_location_overrides,
    damit Server-Prozess und Recompute-Subprozess denselben Location-Stand verwenden.
    """
    try:
        overrides = LocationStore().load_all_overrides()
    except Exception as exc:
        logger.warning("Location-Overrides nicht ladbar (%s) – rechne mit Basis-Koordinaten", exc)
        return 0

    loc_map = {loc.id: loc for loc in LOCATIONS}
    applied = 0
    for ov in overrides:
        loc = loc_map.get(ov.get("id"))
        if not loc:
            continue
        for field in _OVERRIDE_FIELDS:
            if field in ov:
                try:
                    object.__setattr__(loc, field, ov[field])
                except Exception:
                    setattr(loc, field, ov[field])
        applied += 1
    if applied:
        logger.info("Location-Overrides angewendet: %d (Koordinaten-/Name-Korrekturen)", applied)
    return applied


def _load_custom_locations() -> int:
    """
    BUG-33: Lädt Custom Locations aus SQLite und hängt sie an LOCATIONS.

    main.py ruft _load_custom_locations() beim Start auf und macht Custom Locations
    im Server-Prozess verfügbar. precompute.py läuft jedoch als eigener Subprozess
    mit eigenem LOCATIONS-Import — Custom Locations fehlten deshalb vollständig,
    sodass Single-Recompute und nächtlicher Cron nie Events für sie berechneten.

    Spiegelt bewusst die Logik aus main.py:_load_custom_locations(), damit Server-
    Prozess und Recompute-Subprozess denselben Location-Stand verwenden.
    """
    try:
        entries = LocationStore().load_all_custom()
    except Exception as exc:
        logger.warning("Custom Locations nicht ladbar (%s) – übersprungen", exc)
        return 0

    ids_existing = {loc.id for loc in LOCATIONS}
    added = 0
    for e in entries:
        if e.get("id") in ids_existing:
            continue
        try:
            loc = PhotoLocation(
                id=e["id"], name=e["name"], description=e.get("description", ""),
                category=LocationCategory[e.get("category", "SKYLINE")],
                observer_lat=e["observer_lat"], observer_lon=e["observer_lon"],
                subject_lat=e["subject_lat"], subject_lon=e["subject_lon"],
                subject_name=e.get("subject_name", ""),
                subject_height_m=e.get("subject_height_m", 0),
                subject_width_m=e.get("subject_width_m", 0),
                distance_m=e.get("distance_m", 0),
                focal_length_suggestions=e.get("focal_length_suggestions", []),
                special_notes=e.get("special_notes", ""),
                difficulty=e.get("difficulty", 1),
                observer_floor_height_m=float(e.get("observer_floor_height_m", 0.0)),
            )
            LOCATIONS.append(loc)
            ids_existing.add(loc.id)
            added += 1
        except Exception as exc:
            logger.warning("Custom Location '%s' übersprungen (%s)", e.get("id"), exc)
    if added:
        logger.info("Custom Locations geladen: %d Einträge aus SQLite", added)
    return added


def _set_loc_attr(loc, field, value):
    """setattr-Helfer, der auch bei frozen/slots-Dataclasses funktioniert
    (gleiches Muster wie _apply_location_overrides)."""
    try:
        object.__setattr__(loc, field, value)
    except Exception:
        setattr(loc, field, value)


def _apply_qa_values() -> int:
    """
    TASK-48 (Sichtbarkeits-Fix, BUG-29-Muster): Wendet die auto-generierten
    QA-Felder (Azimut/Brennweite/Beschreibung) auf die Basis-`LOCATIONS` an —
    spiegelt bewusst main.py:_load_qa_values(), damit der Recompute-Subprozess
    denselben Wertstand wie der Live-Server berechnet.

    Ohne diesen Merge sieht der nächtliche Recompute die QA-Werte nicht → Feed/
    Kalender zeigen weiter alte Werte (insb. die künftige Auto-Beschreibung, die
    pro Event in den Feed-Payload eingebettet wird), obwohl die Live-Detail-
    Ansicht bereits korrekt ist.

    Merge-Reihenfolge: Code-Defaults < qa_values < location_overrides — daher
    MUSS dieser Aufruf in main() VOR _apply_location_overrides() stehen, damit ein
    manuell gesetzter Override einen Auto-Wert weiterhin überschreibt (identisch
    zur Startup-Reihenfolge in main.py).

    Unterstützte Felder: description, ideal_azimuth_min/max (→ ideal_azimuth_range),
    focal_length_suggestions.
    """
    try:
        qa_values = LocationStore().load_all_qa_values()
    except Exception as exc:
        logger.warning("QA-Values nicht ladbar (%s) – rechne ohne Auto-Werte", exc)
        return 0
    if not qa_values:
        return 0

    loc_map = {loc.id: loc for loc in LOCATIONS}
    applied = 0
    for qv in qa_values:
        loc = loc_map.get(qv.get("location_id"))
        if not loc:
            continue
        if qv.get("description") is not None:
            _set_loc_attr(loc, "description", qv["description"])
        if qv.get("ideal_azimuth_min") is not None and qv.get("ideal_azimuth_max") is not None:
            _set_loc_attr(loc, "ideal_azimuth_range",
                          (qv["ideal_azimuth_min"], qv["ideal_azimuth_max"]))
        if qv.get("focal_length_suggestions") is not None:
            _set_loc_attr(loc, "focal_length_suggestions", qv["focal_length_suggestions"])
        applied += 1
    if applied:
        logger.info("QA-Values angewendet: %d Locations gepatcht (Auto-Azimut/Brennweite/Beschreibung)", applied)
    return applied


def _compute_body_apparent_size(
    event_type_val: str,
    shoot_time,
    distance_m: float,
) -> tuple[float, float | None, str]:
    """
    Berechnet scheinbaren Körperdurchmesser (m) und Erde-Mond-Distanz.

    Rückgabe: (body_apparent_diameter_m, moon_earth_distance_km, body_name)

    Mond: Winkeldurchmesser aus tatsächlicher Erde-Mond-Distanz (variiert ±7,5%).
    Sonne: Mittlerer Winkeldurchmesser 0,5333° (Variation ±1,7% vernachlässigt).
    """
    is_moon = "Mond" in event_type_val or "Vollmond" in event_type_val
    moon_earth_distance_km: float | None = None

    if is_moon:
        try:
            moon_earth_distance_km = get_moon_earth_distance_km(shoot_time)
            angular_diameter_rad = MOON_DIAMETER_KM / moon_earth_distance_km
        except Exception:
            angular_diameter_rad = math.radians(0.5181)  # Fallback: mittlerer Wert
    else:
        angular_diameter_rad = math.radians(0.5333)      # Sonne: mittlerer Wert

    body_apparent_diameter_m = round(distance_m * angular_diameter_rad, 1)
    body_name = "Mond" if is_moon else "Sonne"
    return body_apparent_diameter_m, moon_earth_distance_km, body_name


def _build_composition_labels(
    altitude_delta: float,
    az_delta: float,
    size_ratio: float,
) -> tuple[str, str, str]:
    """
    Erzeugt menschenlesbare Labels für Höhen-, Azimut- und Größenverhältnis.

    Rückgabe: (alt_label, az_label, ratio_label)
    """
    if abs(altitude_delta) <= 0.5:
        alt_label = "🎯 Exaktes Alignment – Objekt auf Höhe der Motivspitze"
    elif 0.5 < altitude_delta <= 3.0:
        alt_label = "✨ Knapp über dem Motiv"
    elif altitude_delta > 3.0:
        alt_label = "☁️ Hoch über dem Motiv"
    else:
        alt_label = "⬇️ Noch unterhalb der Motivspitze"

    if abs(az_delta) <= 1.0:
        az_label = "Zentral ausgerichtet"
    elif abs(az_delta) <= 5.0:
        direction = "links" if az_delta < 0 else "rechts"
        az_label = f"Leicht {direction} versetzt"
    else:
        direction = "links" if az_delta < 0 else "rechts"
        az_label = f"Deutlich {direction} versetzt"

    if size_ratio >= 0.8:
        ratio_label = "Himmelskörper füllt Motiv fast aus"
    elif size_ratio >= 0.4:
        ratio_label = "Himmelskörper halb so groß wie Motiv"
    elif size_ratio >= 0.15:
        ratio_label = "Himmelskörper deutlich kleiner als Motiv"
    else:
        ratio_label = "Himmelskörper sehr klein relativ zum Motiv"

    return alt_label, az_label, ratio_label


def _composition_analysis(o) -> dict | None:
    """
    US-37: Berechnet die Kompositions-Analyse für Events mit Himmelsobjekt-Position.

    Kernidee: Der Beobachter sieht die Motivspitze unter einem bestimmten Elevationswinkel
    (arctan(Höhendifferenz / Entfernung)). Steht das Himmelsobjekt auf genau diesem Winkel,
    ist das Alignment perfekt – z.B. Mond genau auf Höhe der Fernsehturmspitze.

    BUG-43: subject_height_m ist kein Pflichtfeld mehr. Fehlt es, wird eine partielle
    Analyse ohne höhenabhängige Metriken zurückgegeben (Azimut + lateraler Versatz bleiben
    berechenbar). altitude_delta_deg, vertical_offset_m, size_ratio etc. sind dann None.
    """
    loc = o.location
    if not (loc.distance_m and loc.distance_m > 0
            and o.celestial_altitude is not None and o.celestial_azimuth is not None):
        return None

    d = loc.distance_m
    has_height = bool(loc.subject_height_m and loc.subject_height_m > 0)

    # Höhenabhängige Metriken nur wenn subject_height_m vorhanden (BUG-43)
    if has_height:
        # Höhe der Motivspitze über dem Augen-Niveau des Beobachters
        # US-62: observer_floor_height_m (Dach/Etage) erhöht den Beobachter → Motiv wirkt niedriger
        elev_diff = getattr(loc, "elevation_difference_m", 0.0) or 0.0
        observer_floor_h = getattr(loc, "observer_floor_height_m", 0.0) or 0.0
        height_above_observer = elev_diff - observer_floor_h + loc.subject_height_m

        # Scheinbarer Elevationswinkel der Motivspitze (in Grad)
        subject_apparent_elev_deg = math.degrees(math.atan(height_above_observer / d))

        # Δ Höhe: positiv = Objekt steht höher als Motivspitze, 0° = exaktes Alignment
        altitude_delta = round(o.celestial_altitude - subject_apparent_elev_deg, 2)

        # Vertikaler Versatz (projiziert auf die Motivebene in der Entfernung d)
        vertical_offset_m = round(d * math.tan(math.radians(altitude_delta)), 1)

        # Größenverhältnis: scheinbarer Körperdurchmesser / Motivhöhe
    else:
        subject_apparent_elev_deg = None
        altitude_delta = None
        vertical_offset_m = None

    # Azimut immer berechenbar (unabhängig von subject_height_m)
    az_delta = round(((o.celestial_azimuth - (o.subject_azimuth or 0)) + 180) % 360 - 180, 2)
    lateral_offset_m = round(d * math.tan(math.radians(az_delta)), 1)

    event_type_val = o.event_type.value if hasattr(o.event_type, 'value') else str(o.event_type)
    body_apparent_diameter_m, moon_earth_distance_km, body_name = _compute_body_apparent_size(
        event_type_val, o.shoot_time, d,
    )

    if has_height:
        size_ratio = round(body_apparent_diameter_m / loc.subject_height_m, 3)
        alt_label, az_label, ratio_label = _build_composition_labels(altitude_delta, az_delta, size_ratio)
    else:
        size_ratio = None
        ratio_label = None
        alt_label = None
        _, az_label, _ = _build_composition_labels(0.0, az_delta, 1.0)

    return {
        "subject_apparent_elevation_deg": round(subject_apparent_elev_deg, 2) if subject_apparent_elev_deg is not None else None,
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
        "subject_height_m": loc.subject_height_m if has_height else None,
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
        # US-79: Mondaufgang und Monduntergang mit Azimut
        "moonrise_utc": (
            o.astronomy_report.moon.moonrise.isoformat()
            if o.astronomy_report and o.astronomy_report.moon.moonrise else None
        ),
        "moonset_utc": (
            o.astronomy_report.moon.moonset.isoformat()
            if o.astronomy_report and o.astronomy_report.moon.moonset else None
        ),
        "moonrise_azimuth": (
            round(
                get_body_position(
                    o.location.observer_lat,
                    o.location.observer_lon,
                    "moon",
                    o.astronomy_report.moon.moonrise,
                ).azimuth, 1
            )
            if o.astronomy_report and o.astronomy_report.moon.moonrise else None
        ),
        "moonset_azimuth": (
            round(
                get_body_position(
                    o.location.observer_lat,
                    o.location.observer_lon,
                    "moon",
                    o.astronomy_report.moon.moonset,
                ).azimuth, 1
            )
            if o.astronomy_report and o.astronomy_report.moon.moonset else None
        ),
        # US-107: Sonnenaufgang/-untergang-Azimut (analog moonrise/moonset_azimuth)
        "sunrise_azimuth": (
            round(
                get_body_position(
                    o.location.observer_lat,
                    o.location.observer_lon,
                    "sun",
                    o.astronomy_report.sun.sunrise,
                ).azimuth, 1
            )
            if o.astronomy_report and o.astronomy_report.sun.sunrise else None
        ),
        "sunset_azimuth": (
            round(
                get_body_position(
                    o.location.observer_lat,
                    o.location.observer_lon,
                    "sun",
                    o.astronomy_report.sun.sunset,
                ).azimuth, 1
            )
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

def _load_calendar_cache(
    cal_path,
    force_full: bool,
    location_id: str | None,
) -> tuple[list[dict], dict, str | None]:
    """
    Lädt calendar.json und prüft den Algorithmus-Versions-Stand.

    Rückgabe: (existing_events, existing_meta, cache_version)

    Hinweis: BUG-29-Schutz (Single-Location-Guard, Versions-Warn) liegt bewusst in
    compute_calendar_incremental() — nur der rein lesende Phase-1-Teil wird hier gekapselt.
    """
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

    return existing_events, existing_meta, cache_version


def _init_calendar_pass(
    existing_events: list,
    existing_meta: dict,
    cache_version: str,
    today: date,
    force_full: bool,
    location_id,
) -> tuple:
    """Version-Check, Cache-Reset, Event-Pruning und Location-Selektion.

    Returns: (valid_events, locations_to_process, new_meta, target_range)
             locations_to_process ist None wenn location_id nicht gefunden → Aufrufer returnt früh.
    """
    # Version-Check + ggf. Vollneu-Reset
    if (force_full or cache_version != ALGORITHM_VERSION) and not location_id:
        if force_full:
            logger.info("  ⚙️  --full: Vollständige Neuberechnung erzwungen")
        else:
            logger.info(
                "  ⚠️  Algorithmus-Version geändert (%s → %s) – vollständige Neuberechnung",
                cache_version, ALGORITHM_VERSION,
            )
        existing_events = []
        existing_meta = {}
    elif location_id and not force_full and cache_version != ALGORITHM_VERSION:
        # BUG-29: Single-Location-Recompute darf den gesamten Kalender bei Versions-Differenz
        # NICHT verwerfen – nur diese Location wird neu berechnet (Pre-Mortem #2).
        logger.warning(
            "  Single-Recompute bei Versions-Differenz (%s → %s) – nur %s neu, übrige Locations bleiben",
            cache_version, ALGORITHM_VERSION, location_id,
        )

    # Veraltete Events bereinigen (vor heute)
    today_str = today.isoformat()
    valid_events = [e for e in existing_events if e["shoot_time"][:10] >= today_str]
    pruned = len(existing_events) - len(valid_events)
    if pruned > 0:
        logger.info("  Veraltete Events bereinigt: %d", pruned)

    target_range = {(today + timedelta(days=i)).isoformat() for i in range(365)}

    # BUG-29: Im Single-Location-Modus nur diese eine Location neu berechnen und
    # Events + Meta aller übrigen Locations unverändert übernehmen.
    if location_id:
        locations_to_process = [l for l in LOCATIONS if l.id == location_id]
        if not locations_to_process:
            logger.error("  Kalender Single-Recompute: Location '%s' nicht gefunden", location_id)
            return valid_events, None, existing_meta, target_range
        new_meta = {
            lid: {
                "coordinates_hash": m.get("coordinates_hash"),
                "computed_dates": sorted(set(m.get("computed_dates", [])) & target_range),
            }
            for lid, m in existing_meta.items()
            if lid != location_id
        }
    else:
        locations_to_process = list(LOCATIONS)
        new_meta = {}

    return valid_events, locations_to_process, new_meta, target_range


async def _compute_calendar_for_location(
    loc,
    target_range: set,
    existing_meta: dict,
    idx: int,
    total: int,
) -> tuple:
    """Berechnet Kalender-Events für eine einzelne Location.

    Returns:
        (invalidate, dates_needed, new_events_for_loc, meta_entry)
        - invalidate: True wenn alte Events dieser Location entfernt werden müssen
        - dates_needed: Liste der berechneten Daten (leer = vollständig gecacht)
        - new_events_for_loc: neu berechnete Events
        - meta_entry: dict für new_meta[loc.id]
    """
    coords_hash = _location_hash(loc)
    loc_meta = existing_meta.get(loc.id, {})
    invalidate = False

    if loc_meta.get("coordinates_hash") != coords_hash:
        if loc_meta:
            logger.info("  %s: Koordinaten geändert – komplette Neuberechnung", loc.name)
        invalidate = True
        dates_needed = sorted(target_range)
    else:
        # Nur fehlende Daten berechnen
        computed_set = set(loc_meta.get("computed_dates", []))
        dates_needed = sorted(target_range - computed_set)

    old_computed = set(loc_meta.get("computed_dates", []))

    if not dates_needed:
        # Vollständig gecacht → meta übernehmen, auf target_range beschränken
        meta_entry = {
            "coordinates_hash": coords_hash,
            "computed_dates": sorted(old_computed & target_range),
        }
        return invalidate, dates_needed, [], meta_entry

    skipped = len(target_range) - len(dates_needed)
    logger.info(
        "  Kalender [%d/%d] %s: %d neue Tage (%d gecacht)",
        idx + 1, total, loc.name, len(dates_needed), skipped,
    )

    new_events_for_loc = []
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

    # Meta für diese Location aktualisieren
    all_computed = (old_computed | set(dates_needed)) & target_range
    meta_entry = {
        "coordinates_hash": coords_hash,
        "computed_dates": sorted(all_computed),
    }

    return invalidate, dates_needed, new_events_for_loc, meta_entry


async def compute_calendar_incremental(today: date, force_full: bool = False, location_id: str | None = None) -> tuple[list[dict], dict]:
    """Schicht 2 – Inkrementeller 365-Tage Kalender.

    Täglich: ~1 neuer Tag × N Locations. Neue Location: 365 Tage nur für diese.
    ALGORITHM_VERSION-Bump: einmaliger Vollneu-Lauf.
    Details: _init_calendar_pass, _compute_calendar_for_location.
    """
    cal_path = CACHE_DIR / "calendar.json"
    existing_events, existing_meta, cache_version = _load_calendar_cache(cal_path, force_full, location_id)

    valid_events, locations_to_process, new_meta, target_range = _init_calendar_pass(
        existing_events, existing_meta, cache_version, today, force_full, location_id,
    )
    if locations_to_process is None:
        # BUG-29: Location nicht gefunden → bestehenden Kalender unverändert zurückgeben
        return valid_events, existing_meta

    total_skipped = 0
    total_computed = 0

    for i, loc in enumerate(locations_to_process):
        invalidate, dates_needed, new_events_for_loc, meta_entry = \
            await _compute_calendar_for_location(
                loc, target_range, existing_meta, i, len(locations_to_process),
            )

        total_skipped += len(target_range) - len(dates_needed)
        total_computed += len(dates_needed)

        if invalidate:
            # Koordinaten-Änderung → alte Events dieser Location verwerfen
            valid_events = [e for e in valid_events if e["location_id"] != loc.id]

        valid_events.extend(new_events_for_loc)
        new_meta[loc.id] = meta_entry
        await asyncio.sleep(0)  # Event Loop gelegentlich freigeben

    logger.info("  Zusammenfassung: %d neu berechnet, %d aus Cache", total_computed, total_skipped)
    valid_events.sort(key=lambda r: (r["shoot_time"], -r["overall_score"]))
    return valid_events, new_meta


def _merge_and_write_feed(feed_path, location_id: str, new_events: list, computed_at: str) -> int:
    """Merged neue Events für location_id in bestehende opportunities.json und schreibt sie.

    Returns: Gesamtzahl der gemergten Events.
    """
    existing_events = []
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
    return len(merged)


def _write_calendar_cache(cal_path, calendar: list, computed_meta: dict, computed_at: str) -> None:
    """Schreibt calendar.json mit algorithm_version, computed_at, computed_locations und events."""
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


def _write_feed_cache(feed_path, feed: list, computed_at: str) -> None:
    """Schreibt opportunities.json und loggt einen Health-Alert wenn der Feed zu klein ist."""
    feed_path.write_text(
        json.dumps({"computed_at": computed_at, "opportunities": feed}, ensure_ascii=False),
        encoding="utf-8",
    )
    if len(feed) < HEALTH_FEED_MIN:
        logger.error(
            "🚨 HEALTH-ALERT [%s]: opportunities.json enthält nur %d Event(s) "
            "(Schwellwert: %d). Mögliche Ursachen: Skyfield-Fehler, API-Timeout "
            "oder fehlerhafte Location-Daten. Bitte Logs prüfen.",
            computed_at, len(feed), HEALTH_FEED_MIN,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Hauptfunktion
# ─────────────────────────────────────────────────────────────────────────────

async def _run_single_location_flow(
    location_id: str,
    today: date,
    computed_at: str,
    run_feed: bool,
    run_calendar: bool,
    feed_path,
    elev_path,
    t0: float,
) -> None:
    """Single-Location Recompute (nach Koordinaten-Änderung via PATCH)."""
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
        merged_count = _merge_and_write_feed(feed_path, location_id, new_events, computed_at)
        logger.info(
            "  ✅ Feed: %d neue Events für %s, %d gesamt (%.1fs)",
            len(new_events), loc.name, merged_count, time.time() - t1,
        )

    # BUG-29: Kalender-Cache (calendar.json) für genau diese Location regenerieren.
    # Vorher schrieb der --feed-only-Single-Flow ausschließlich opportunities.json und
    # returnte vor jeder Kalenderberechnung → Chancendetails aus dem Kalender zeigten
    # alte Koordinaten/Astronomie. compute_calendar_incremental(location_id=…) merged
    # nur die Events DIESER Location und lässt alle übrigen unverändert.
    if run_calendar:
        logger.info("  365-Tage Kalender für %s …", loc.name)
        t2 = time.time()
        calendar, computed_meta = await compute_calendar_incremental(
            today, location_id=location_id,
        )
        cal_path = CACHE_DIR / "calendar.json"
        _write_calendar_cache(cal_path, calendar, computed_meta, computed_at)
        logger.info(
            "  ✅ Kalender: %d Events gesamt nach Merge (%.1fs)",
            len(calendar), time.time() - t2,
        )

    logger.info("=== Single-Location Recompute abgeschlossen in %.1fs ===", time.time() - t0)


async def _run_standard_flow(
    today: date,
    computed_at: str,
    run_feed: bool,
    run_calendar: bool,
    force_full: bool,
    feed_path,
    elev_path,
) -> None:
    """Standard-Flow: alle Locations, Elevations → Feed → Kalender."""
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
        _write_feed_cache(feed_path, feed, computed_at)
        logger.info("✅ opportunities.json: %d Events (%.1fs)", len(feed), time.time() - t1)

    # ── Schicht 2b: 365-Tage Kalender (inkrementell) ─────────────────────────
    if run_calendar:
        logger.info("── Astronomy-Cache: Kalender 365 Tage (inkrementell) ")
        t2 = time.time()
        calendar, computed_meta = await compute_calendar_incremental(
            today, force_full=force_full,
        )
        cal_path = CACHE_DIR / "calendar.json"
        _write_calendar_cache(cal_path, calendar, computed_meta, computed_at)
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


async def main(args: argparse.Namespace) -> None:
    t0 = time.time()
    logger.info("=== FotoAlert Vorberechnung startet (Algorithmus v%s) ===", ALGORITHM_VERSION)
    logger.info("%d Locations geladen", len(LOCATIONS))
    # Lade-Reihenfolge gespiegelt von main.py:startup() — Code-Defaults < Custom
    # < qa_values < location_overrides — damit Recompute-Subprozess und Live-Server
    # exakt denselben Location-Stand verwenden.
    # BUG-33: Custom Locations aus SQLite laden — sie fehlen im LOCATIONS-Import aus
    # data/locations.py komplett, da precompute.py als eigener Subprozess läuft.
    _load_custom_locations()
    # TASK-48: Auto-QA-Werte (Azimut/Brennweite/Beschreibung) anwenden, BEVOR die
    # Overrides drüberlaufen — damit ein manueller Override einen Auto-Wert
    # weiterhin überschreibt (identische Merge-Reihenfolge wie im Server-Start).
    _apply_qa_values()
    # BUG-29: Persistierte Koordinaten-/Name-Overrides anwenden, BEVOR irgendetwas
    # berechnet oder gehasht wird — sonst rechnet der Recompute mit den alten Basis-
    # Koordinaten und der coordinates_hash ändert sich nie.
    _apply_location_overrides()
    logger.info("%d Locations nach Custom-Load + QA-Values + Overrides", len(LOCATIONS))

    # TASK-18: Snapshot vor Precompute (lokale Sicherung, 7 Versionen)
    from data import backup as _backup
    _backup.snapshot_before_precompute()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today()
    computed_at = datetime.now(timezone.utc).isoformat()

    run_feed = not args.calendar_only
    run_calendar = not args.feed_only
    location_id: str | None = getattr(args, "location_id", None)
    feed_path = CACHE_DIR / "opportunities.json"
    elev_path = CACHE_DIR / "elevations.json"

    if location_id:
        await _run_single_location_flow(
            location_id=location_id,
            today=today,
            computed_at=computed_at,
            run_feed=run_feed,
            run_calendar=run_calendar,
            feed_path=feed_path,
            elev_path=elev_path,
            t0=t0,
        )
    else:
        await _run_standard_flow(
            today=today,
            computed_at=computed_at,
            run_feed=run_feed,
            run_calendar=run_calendar,
            force_full=args.full,
            feed_path=feed_path,
            elev_path=elev_path,
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
