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
  python3 precompute.py --feed-only --location-ids a,b,c        # US-141: mehrere Orte in einem Lauf (Nachladen)
  python3 precompute.py --feed-only --location-ids a,b,c --mit-kalender   # ... und danach deren Kalender

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
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

# Sicherstellen, dass Imports aus dem Backend-Verzeichnis funktionieren
sys.path.insert(0, str(Path(__file__).parent))

from calculations.opportunity import find_opportunities, find_opportunities_multi_day
from calculations.astronomy import get_moon_earth_distance_km, MOON_DIAMETER_KM, get_body_position
from data.locations import (
    LOCATIONS, PhotoLocation, LocationCategory, coerce_category_value, PRECOMPUTE_OVERRIDE_FIELDS,
)
from data.store import LocationStore
from data import aktiv_regel, cache_io   # US-141/BUG-118: zentrale Aktiv-Regel, sicheres Schreiben
from data import gebiet_zustand as gz     # US-141 Baustein 2: welche Orte sind aktiv (Land/Region an)?

# ─────────────────────────────────────────────────────────────────────────────
# Algorithmus-Version: Bump bei Änderungen an opportunity.py / astronomy.py,
# die andere Ergebnisse für bereits berechnete Tage liefern würden.
# Format: "MAJOR.MINOR" – Minor = kleine Scoring-Anpassung, Major = Struktur.
# ─────────────────────────────────────────────────────────────────────────────
ALGORITHM_VERSION = "1.5"  # TASK-02: 4 Finsternis-Typen — neue Events für bereits
# berechnete Tage (Cache-Invalidierung laut Kommentar oben Zeile 56–57 zwingend nötig,
# sonst überspringt compute_calendar_incremental() alle schon gecachten Datumswerte
# und die neuen Finsternis-Events tauchen nie im Kalender/Feed auf).

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
# (kein Celestial-Tracking auf Motivpunkt → composition_analysis ist None,
#  ODER eine bereits etablierte, bewusst weichere Richtungs-/Zeitprüfung gilt
#  statt der harten ±2°-Präzisionsausrichtung — z.B. Mondaufgang/Monduntergang,
#  deren Zeitpunkt physikalisch fix ist statt gezielt gesucht, BUG-90)
_ALIGNMENT_FILTER_EXEMPT = {
    "Goldene Stunde Morgen",
    "Goldene Stunde Abend",
    "Blaue Stunde",
    "Blaue Stunde Morgen",  # US-132: neuer symmetrischer Morgen-Block
    "Milchstraße",
    "Neumond",
    "Meteoritenschauer",
    "Sonnenfinsternis",
    # TASK-02: drei weitere Finsternis-Typen — kein Celestial-Tracking auf einen
    # Motivpunkt (analog zur bereits bestehenden "Sonnenfinsternis"-Ausnahme direkt
    # darüber), composition_analysis ist für Finsternis-Ereignisse nicht vorhanden.
    "Partielle Sonnenfinsternis",
    "Mondfinsternis",
    "Partielle Mondfinsternis",
    # US-109: Wetter-Overlay-Events (Laufzeit, kein eigener subject_azimuth nötig)
    "Goldene Wolken",
    "Himmelsröte",
    "Rote Wolken",  # US-132
    "Mondaufgang",  # BUG-90: physikalisch fixer Zeitpunkt, ±35°-FRONT-Zone (US-108) bereits Qualitätsschwelle
    "Monduntergang",  # BUG-90
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


# Felder, die ein Location-Override überschreiben darf — jetzt aus
# data/locations.py:LOCATION_FIELD_RULES abgeleitet (US-128: vorher hier hartkodiert
# dupliziert, jetzt eine gemeinsame Quelle mit main.py:_load_location_overrides,
# TASK-17), damit Server und Recompute-Subprozess denselben Stand sehen.
_OVERRIDE_FIELDS = PRECOMPUTE_OVERRIDE_FIELDS


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

    # BUG-118: Standard-Orte mit Lösch-Markierung (Tombstone) aus der Ortsliste nehmen, so wie es
    # main.py:_load_location_overrides beim Serverstart tut. Bisher kannte dieser eigene Prozess die
    # Markierung nicht und rechnete gelöschte Orte jede Nacht weiter — ihre Chancen kamen zurück.
    # Die Frage „gelöscht?“ beantwortet die zentrale Regel (data/aktiv_regel.py).
    geloescht = aktiv_regel.geloeschte_ids(overrides)
    if geloescht:
        LOCATIONS[:] = [l for l in LOCATIONS if l.id not in geloescht]
        logger.info("BUG-118: %d gelöschte Standard-Orte von der Berechnung ausgenommen", len(geloescht))

    loc_map = {loc.id: loc for loc in LOCATIONS}
    applied = 0
    for ov in overrides:
        loc = loc_map.get(ov.get("id"))
        if not loc:
            continue
        # BUG-84: "category" wird als Enum-Member-Name (String) im Override gespeichert --
        # vor dem setattr gezielt zurück in eine LocationCategory-Instanz konvertieren
        # (spiegelt main.py:_load_location_overrides, siehe Docstring oben).
        for field in _OVERRIDE_FIELDS:
            if field not in ov:
                continue
            value = ov[field]
            if field == "category":
                value = coerce_category_value(value)
            # Refactor (BUG-84): dupliziertes try/except object.__setattr__-Muster durch
            # den bereits vorhandenen _set_loc_attr-Helfer ersetzt (unten definiert, gleiche
            # Semantik -- funktioniert auch bei frozen/slots-Dataclasses). Kein Verhaltens-
            # unterschied, nur eine gemeinsame Quelle statt zweier identischer Implementierungen.
            _set_loc_attr(loc, field, value)
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
                land=e.get("land"), region=e.get("region"),   # US-141 (kommt sonst aus den Korrekturen)
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
        # US-09: Sichtachsen-Status/Winkel anwenden (Default bleibt "nicht_geprueft",
        # solange kein QA-Wert gespeichert ist — siehe PhotoLocation-Default).
        if qv.get("sightline_status") is not None:
            _set_loc_attr(loc, "sightline_status", qv["sightline_status"])
        if qv.get("sightline_angle_deg") is not None:
            _set_loc_attr(loc, "sightline_angle_deg", qv["sightline_angle_deg"])
        applied += 1
    if applied:
        logger.info("QA-Values angewendet: %d Locations gepatcht (Auto-Azimut/Brennweite/Beschreibung/Sichtachse)", applied)
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
        # US-09: Sichtachsen-Status der Location (frei/teilweise_verdeckt/blockiert/
        # nicht_geprueft) — wird 1:1 mit dem Event ausgeliefert, damit sowohl
        # Alignment-Events als auch daraus abgeleitete Wetter-Chancen (Himmelsröte,
        # via deepcopy in main._generate_cloud_mood_events) denselben Status tragen.
        "sightline_status": getattr(o.location, 'sightline_status', None) or "nicht_geprueft",
        "sightline_angle_deg": getattr(o.location, 'sightline_angle_deg', None),
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

async def _feed_fuer_ort(loc, today: date) -> list[dict]:
    """14-Tage-Chancen EINES Orts (ohne Wetter), mit dem Schärfezonen-Filter (US-57).
    Wirft bei einem Rechenfehler; der Aufrufer entscheidet, wie er damit umgeht."""
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
    return filtered


async def compute_feed(today: date, gerechnet_ids: "set | None" = None) -> list[dict]:
    """
    14-Tage Astronomy-Feed für alle Locations (ohne Wetter).
    Wird immer komplett neu berechnet – ist schnell und enthält
    den nächsten 2-Wochen-Horizont vollständig aktuell.

    US-141 Baustein 3: Wird `gerechnet_ids` übergeben, trägt die Funktion dort die Nummern aller
    Orte ein, für die sie gerechnet hat (die aktiven zu Beginn des Laufs). Der Schreibschritt
    (_write_feed_cache) braucht das, um Termine von Orten zu behalten, die erst NACH dem Start dieses
    Laufs eingeschaltet und von einem Nachlade-Lauf berechnet wurden.
    """
    results: list[dict] = []
    # US-141 (Gruppe B): Chancen werden nur für AKTIVE Orte berechnet; pausierte Orte (Land oder
    # Region aus) bleiben außen vor. Höhe und Sichtachse (Gruppe A) laufen für alle Orte weiter.
    aktive = gz.aktive_orte(LOCATIONS)
    if gerechnet_ids is not None:
        gerechnet_ids.update(l.id for l in aktive)
    if len(aktive) != len(LOCATIONS):
        logger.info("  US-141: %d von %d Orten pausiert – nicht berechnet", len(LOCATIONS) - len(aktive), len(LOCATIONS))
    for i, loc in enumerate(aktive):
        logger.info("  Feed [%d/%d] %s", i + 1, len(aktive), loc.name)
        try:
            results.extend(await _feed_fuer_ort(loc, today))
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

    Returns: (valid_events, locations_to_process, new_meta, target_range, existing_meta)
             locations_to_process ist None wenn location_id nicht gefunden → Aufrufer returnt früh.
             existing_meta wird zusätzlich zurückgegeben, weil sie bei Versions-Mismatch
             (kein location_id) intern auf {} zurückgesetzt wird (BUG-93: dieser Reset muss
             an den Aufrufer propagiert werden, sonst arbeitet compute_calendar_incremental()
             mit seiner eigenen, nie aktualisierten Kopie weiter).
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
            return valid_events, None, existing_meta, target_range, existing_meta
        new_meta = {
            lid: {
                "coordinates_hash": m.get("coordinates_hash"),
                "computed_dates": sorted(set(m.get("computed_dates", [])) & target_range),
            }
            for lid, m in existing_meta.items()
            if lid != location_id
        }
    else:
        # US-141 (Gruppe B): der Kalender wird nur für aktive Orte gerechnet.
        locations_to_process = gz.aktive_orte(LOCATIONS)
        new_meta = {}

    return valid_events, locations_to_process, new_meta, target_range, existing_meta


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
                loc, d, forecast=None, min_score=0.35, astronomy_only=True,
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

    valid_events, locations_to_process, new_meta, target_range, existing_meta = _init_calendar_pass(
        existing_events, existing_meta, cache_version, today, force_full, location_id,
    )
    # BUG-93: existing_meta wird hier bewusst mit dem von _init_calendar_pass()
    # zurückgegebenen Wert überschrieben (statt der eigenen, oben geladenen Kopie) —
    # nur so kommt ein Versions-Mismatch-Reset ({}) tatsächlich bei der folgenden
    # Location-Schleife an, statt lokal in _init_calendar_pass() zu verpuffen.
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
    # US-141 (AK-59 bis AK-61): Lesen, Mischen und Schreiben passieren unter einer Dateisperre, damit
    # zwei gleichzeitige Läufe (verschiedene Orte) einander keine Termine überschreiben; geschrieben
    # wird atomar (Temp-Datei, fsync, austauschen) — nie eine halbe Datei.
    return _merge_and_write_feed_many(feed_path, {location_id: new_events}, computed_at)


def _write_calendar_cache(cal_path, calendar: list, computed_meta: dict, computed_at: str) -> None:
    """Schreibt calendar.json mit algorithm_version, computed_at, computed_locations und events."""
    # US-141 (AK-59 bis AK-61): unter Dateisperre und atomar schreiben (siehe data/cache_io.py).
    cache_io.gesperrt_atomar_schreiben(
        cal_path,
        json.dumps(
            {
                "algorithm_version": ALGORITHM_VERSION,
                "computed_at": computed_at,
                "computed_locations": computed_meta,
                "events": calendar,
            },
            ensure_ascii=False,
        ),
    )


def _write_calendar_single_delta(cal_path, location_id: str, calendar: list,
                                computed_at: str) -> int:
    """BUG-113: Schreibt zusätzlich zur großen calendar.json eine kleine
    Übergabedatei mit ausschließlich den Kalender-Ereignissen DIESER Location.

    Der laufende Server (main.py::_apply_calendar_delta) übernimmt die Events
    daraus und tauscht sie im Arbeitsspeicher aus, statt die komplette
    calendar.json (aktuell ~1,1 GB) erneut einzulesen — dieses Einlesen hielt
    den Server bisher über die gesamte Lesezeit an (BUG-113 AK3).

    Immer derselbe Dateiname: die Datei ist ein Postfach für genau den zuletzt
    gelaufenen Einzel-Kalenderlauf, kein wachsender Bestand je Standort. Der
    Server prüft `location_id` und Änderungszeit, bevor er sie anwendet.
    """
    events = [e for e in calendar if e.get("location_id") == location_id]
    delta_path = cal_path.parent / "calendar_single_last.json"
    cache_io.gesperrt_atomar_schreiben(
        delta_path,
        json.dumps(
            {"location_id": location_id, "computed_at": computed_at, "events": events},
            ensure_ascii=False,
        ),
    )
    logger.info("  ↳ Übergabedatei %s geschrieben: %d Events für %s",
                delta_path.name, len(events), location_id)
    return len(events)


def _merge_and_write_feed_many(feed_path, neue_je_ort: dict, computed_at: str) -> int:
    """US-141 Baustein 3 (Nachladen): wie _merge_and_write_feed, aber für MEHRERE Orte in einem einzigen
    Schreibvorgang. `neue_je_ort` = {Ort-ID: [Termine]}; die Termine dieser Orte in der Datei werden ersetzt
    (ein Ort mit leerer Liste verliert seine alten Termine), alle übrigen bleiben unberührt.
    Lesen, Mischen, Schreiben passieren unter der Dateisperre aus data/cache_io.py, geschrieben wird atomar.

    Returns: Gesamtzahl der Termine in der Datei danach."""
    ids = set(neue_je_ort)
    with cache_io.gesperrt_aendern(feed_path):
        vorhanden = []
        if feed_path.exists():
            try:
                vorhanden = json.loads(feed_path.read_text(encoding="utf-8")).get("opportunities", [])
            except Exception as exc:
                logger.warning("  Feed-Datei %s nicht lesbar (%s) – sie wird nur mit den neuen Terminen neu geschrieben",
                               feed_path.name, exc)
        gemischt = [e for e in vorhanden if e.get("location_id") not in ids]
        for termine in neue_je_ort.values():
            gemischt.extend(termine)
        gemischt.sort(key=lambda r: (r["shoot_time"], -r["overall_score"]))
        cache_io.atomar_schreiben(
            feed_path,
            json.dumps({"computed_at": computed_at, "opportunities": gemischt}, ensure_ascii=False),
        )
    return len(gemischt)


def _zwischenzeitlich_nachgeladene_termine(feed_path, feed: list, gerechnet_ids: set) -> list:
    """US-141 Baustein 3 (Kollision Nachtlauf <-> Nachladen): Schaltet der Host ein Gebiet NACH dem Start
    dieses Vorberechnungslaufs ein, rechnet der Nachlade-Lauf dessen Orte und schreibt ihre Termine in die
    Feed-Datei. Dieser Lauf kennt die Orte nicht (er hat sie nicht berechnet) und würde die Datei sonst ohne
    sie überschreiben. Darum bleiben beim Schreiben (unter der Sperre) alle Termine erhalten, die jetzt in der
    Datei stehen, zu einem Ort gehören, der JETZT aktiv ist und den dieser Lauf nicht berechnet hat."""
    if not feed_path.exists():
        return feed
    try:
        alt = json.loads(feed_path.read_text(encoding="utf-8")).get("opportunities", [])
    except Exception:
        return feed
    aktiv_jetzt = {l.id for l in gz.aktive_orte(LOCATIONS)}
    behalten = [e for e in alt if e.get("location_id") in aktiv_jetzt and e.get("location_id") not in gerechnet_ids]
    if not behalten:
        return feed
    logger.info("  US-141: %d Termine von Orten, die während des Laufs nachgeladen wurden, bleiben erhalten",
                len(behalten))
    gemischt = list(feed) + behalten
    gemischt.sort(key=lambda r: (r["shoot_time"], -r["overall_score"]))
    return gemischt


def _write_feed_cache(feed_path, feed: list, computed_at: str, gerechnet_ids: "set | None" = None) -> None:
    """Schreibt opportunities.json und loggt einen Health-Alert wenn der Feed zu klein ist.

    US-141 Baustein 3: Mit `gerechnet_ids` (Orte, die dieser Lauf berechnet hat) bleiben zwischenzeitlich
    von einem Nachlade-Lauf geschriebene Termine anderer aktiver Orte erhalten (siehe
    _zwischenzeitlich_nachgeladene_termine). Ohne den Parameter gilt das bisherige Verhalten."""
    # US-141 (AK-59 bis AK-61): unter Dateisperre und atomar schreiben (siehe data/cache_io.py).
    if gerechnet_ids is None:
        cache_io.gesperrt_atomar_schreiben(
            feed_path,
            json.dumps({"computed_at": computed_at, "opportunities": feed}, ensure_ascii=False),
        )
    else:
        with cache_io.gesperrt_aendern(feed_path):
            feed = _zwischenzeitlich_nachgeladene_termine(feed_path, feed, gerechnet_ids)
            cache_io.atomar_schreiben(
                feed_path,
                json.dumps({"computed_at": computed_at, "opportunities": feed}, ensure_ascii=False),
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

async def _refresh_single_location_elevation(
    loc,
    location_id: str,
    computed_at: str,
    elev_path,
) -> None:
    """Elevation für diese Location neu abrufen (Koordinaten geändert), cachen
    und auf DASSELBE `loc`-Objekt patchen (Pre-Mortem-Szenario 1, TASK-41:
    fließt direkt in _composition_analysis() ein — Aufrufreihenfolge Elevation
    → Sichtachse → Feed → Kalender bleibt exakt erhalten).
    Eigenes lokales try/except (Pre-Mortem-Szenario 2, TASK-41): ein Fehler
    hier darf Sichtachse-/Feed-/Kalenderberechnung nicht verhindern."""
    logger.info("  Elevation neu abrufen …")
    try:
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
    except Exception as e:
        logger.warning("  Elevation-Refresh fehlgeschlagen für %s: %s", loc.name, e)


async def _check_single_location_sightline(loc) -> None:
    """US-09: Sichtachsen-Check (Raycast) — einmalig bei Anlegen/Ändern der Location
    (Regel 3 der Spec), NICHT bei jedem täglichen Standard-Precompute-Lauf.
    Eigenes lokales try/except (Pre-Mortem-Szenario 2, TASK-41): ein Fehler hier
    darf Feed-/Kalenderberechnung nicht verhindern."""
    logger.info("  Sichtachsen-Check …")
    try:
        from calculations.sightline import update_location_sightline
        from data.elevation import provider as _elev_provider
        sl_result = await update_location_sightline(LocationStore(), loc, _elev_provider)
        logger.info("  ✅ Sichtachse: %s", sl_result.get("status"))
    except Exception as e:
        logger.warning("  Sichtachsen-Check fehlgeschlagen für %s: %s", loc.name, e)


async def _refresh_single_location_feed(
    loc,
    location_id: str,
    today: date,
    computed_at: str,
    feed_path,
) -> None:
    """14-Tage Feed für diese Location neu berechnen, in opportunities.json mergen
    (bestehende Events anderer Locations bleiben unangetastet) und schreiben."""
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


async def _refresh_single_location_calendar(
    location_id: str,
    today: date,
    computed_at: str,
) -> None:
    """BUG-29: Kalender-Cache (calendar.json) für genau diese Location regenerieren.
    Vorher schrieb der --feed-only-Single-Flow ausschließlich opportunities.json und
    returnte vor jeder Kalenderberechnung → Chancendetails aus dem Kalender zeigten
    alte Koordinaten/Astronomie. compute_calendar_incremental(location_id=…) merged
    nur die Events DIESER Location und lässt alle übrigen unverändert.
    Eigenes lokales try/except (Pre-Mortem-Szenario 2, TASK-41): ein Fehler hier
    darf die zuvor bereits abgeschlossenen Schritte (Elevation, Sichtachse, Feed)
    nicht rückwirkend ungültig machen — der Fehler wird geloggt, die Funktion
    endet, `_run_single_location_flow()` läuft danach normal weiter/aus."""
    logger.info("  365-Tage Kalender für %s …", location_id)
    t2 = time.time()
    try:
        calendar, computed_meta = await compute_calendar_incremental(
            today, location_id=location_id,
        )
        cal_path = CACHE_DIR / "calendar.json"
        _write_calendar_cache(cal_path, calendar, computed_meta, computed_at)
        # BUG-113: zusätzlich das kleine Postfach für den laufenden Server schreiben,
        # damit dieser nur diesen einen Standort austauschen muss statt die ganze
        # Kalenderdatei neu einzulesen.
        # BUG-113 Punkt 6: eigenes try/except — scheitert NUR das Postfach, ist
        # calendar.json bereits korrekt geschrieben; das darf nicht als
        # "Kalenderberechnung fehlgeschlagen" im Protokoll landen.
        try:
            _write_calendar_single_delta(cal_path, location_id, calendar, computed_at)
        except Exception as e:
            logger.warning(
                "  Übergabedatei für %s nicht geschrieben (%s) — Kalender ist berechnet, "
                "der Server übernimmt den neuen Stand erst beim nächsten Voll-Laden",
                location_id, e,
            )
        logger.info(
            "  ✅ Kalender: %d Events gesamt nach Merge (%.1fs)",
            len(calendar), time.time() - t2,
        )
    except Exception as e:
        logger.error("  Kalenderberechnung fehlgeschlagen für %s: %s", location_id, e)


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
    """Single-Location Recompute (nach Koordinaten-Änderung via PATCH).

    Dünne Orchestrierung (TASK-41): ruft die vier Helfer nacheinander in exakt
    derselben Reihenfolge wie zuvor auf — Elevation → Sichtachse → Feed →
    Kalender. Jeder Helfer behält sein eigenes Fehlerhandling; hier bewusst
    KEIN gemeinsames äußeres try/except (Pre-Mortem-Szenario 2)."""
    single_loc_list = [l for l in LOCATIONS if l.id == location_id]
    if not single_loc_list:
        logger.error("Location '%s' nicht gefunden – Abbruch", location_id)
        return
    loc = single_loc_list[0]
    logger.info("── Single-Location Recompute: %s ──", loc.name)
    # US-141: Für einen pausierten Ort (Land oder Region aus) gibt es weder Feed noch Kalender
    # (Gruppe B); Höhe und Sichtachse (Gruppe A) werden trotzdem aufgefrischt.
    if (run_feed or run_calendar) and gz.ist_pausiert(loc):
        logger.info("US-141: %s ist pausiert – nur Höhe und Sichtachse, kein Feed und kein Kalender", loc.name)
        run_feed = False
        run_calendar = False

    await _refresh_single_location_elevation(
        loc=loc, location_id=location_id, computed_at=computed_at, elev_path=elev_path,
    )
    await _check_single_location_sightline(loc=loc)

    if run_feed:
        await _refresh_single_location_feed(
            loc=loc, location_id=location_id, today=today, computed_at=computed_at,
            feed_path=feed_path,
        )

    if run_calendar:
        await _refresh_single_location_calendar(
            location_id=location_id, today=today, computed_at=computed_at,
        )

    logger.info("=== Single-Location Recompute abgeschlossen in %.1fs ===", time.time() - t0)


# ─────────────────────────────────────────────────────────────────────────────
# US-141 (Entscheidung 2026-10-15): Kalender beim Einschalten eines Gebiets sofort mitrechnen
# ─────────────────────────────────────────────────────────────────────────────
# Ablauf im Nachlade-Prozess: erst die Chancen (Feed, in Häppchen), dann der 365-Tage-Kalender NUR für die Orte
# dieses Laufs. Der Kalender wird je Ort einzeln gerechnet (im Arbeitsspeicher) und am Ende in EINEM Schritt in
# calendar.json eingemischt: Datei einmal lesen, die Einträge genau dieser Orte ersetzen, einmal atomar
# zurückschreiben (nicht ein Schreibvorgang je Ort — jeder kostet das Lesen und Schreiben der ganzen, über 1 GB
# großen Datei). Der Kalender-Schritt ist freiwillig: scheitert er (kein Platz, kein Kalender vorhanden, Fehler),
# bleiben Chancen und Wetter gültig, der Nachtlauf holt den Kalender nach.

NACHLADEN_KALENDER_TAGE = 365                       # wie der Nachtlauf: ab heute 365 Tage
NACHLADEN_KALENDER_FENSTER_TAGE = 31                # so viele Tage je Rechenfenster (wie die Monatsberechnung des Servers)
NACHLADEN_KALENDER_POSTFACH_NAME = "calendar_nachladen_last.jsonl"   # Übergabe an den laufenden Server
NACHLADEN_KALENDER_BYTES_JE_ORT = 12 * 1024 * 1024  # grobe Schätzung des Zuwachses je Ort (Platzprüfung vorab)
NACHLADEN_KALENDER_BYTES_JE_TERMIN = 2048           # grobe Schätzung je Termin (Platzprüfung kurz vor dem Schreiben)


class KalenderNachladenFehler(RuntimeError):
    """Der Kalender-Schritt des Nachladens konnte nicht abgeschlossen werden (Text ist für Menschen lesbar)."""


async def _kalender_fuer_ort(loc, today: date) -> list:
    """365-Tage-Kalender EINES Orts (nur Astronomie, Mindestwert 0,35, Schärfezonen-Filter) mit der Fenster-Rechnung
    (WindowEphemeris) — derselbe Weg, den der Server für die Monatsübersicht benutzt, rund zehnmal schneller als
    die Tag-für-Tag-Rechnung des Nachtlaufs. Wirft bei einem Rechenfehler; der Aufrufer entscheidet."""
    from calculations.window_engine import WindowEphemeris
    import calculations.astronomy as _astro

    ergebnis: list = []
    start = today
    rest = NACHLADEN_KALENDER_TAGE
    while rest > 0:
        tage = min(NACHLADEN_KALENDER_FENSTER_TAGE, rest)
        _astro.set_active_window(WindowEphemeris(loc.observer_lat, loc.observer_lon, start, tage))
        try:
            opps = await find_opportunities_multi_day(
                loc, start, tage, None, min_score=0.35, astronomy_only=True,
            )
        finally:
            _astro.clear_active_window()
        ergebnis.extend(e for e in (_serialize(o) for o in opps) if _passes_alignment_filter(e))
        start = start + timedelta(days=tage)
        rest -= tage
        await asyncio.sleep(0)
    return ergebnis


def _hoehen_aus_zwischenspeicher(orte: list, elev_path) -> int:
    """Setzt die gespeicherten Geländehöhen (elevations.json, nur lesen, kein Netz) auf die Orte — wie es der
    Nachtlauf vor der Kalenderrechnung tut. Fehlende Einträge bleiben unberührt. Gibt die Zahl gesetzter Orte zurück."""
    try:
        daten = json.loads(Path(elev_path).read_text(encoding="utf-8")).get("elevations", {})
    except Exception:
        return 0
    n = 0
    for loc in orte:
        eintrag = daten.get(loc.id)
        if not isinstance(eintrag, dict) or "elevation_difference_m" not in eintrag:
            continue
        try:
            object.__setattr__(loc, "elevation_difference_m", eintrag["elevation_difference_m"])
        except Exception:
            setattr(loc, "elevation_difference_m", eintrag["elevation_difference_m"])
        n += 1
    return n


def _kalender_einmischen(cal_path, neue_je_ort: dict, meta_je_ort: dict, computed_at: str) -> int:
    """Mischt die Kalendereinträge der genannten Orte in calendar.json ein (eine Datei lesen, ein Schreibvorgang).

    - Alles geschieht unter der Dateisperre (cache_io): ein gleichzeitiger anderer Schreiber wartet, der nächste
      liest erst danach. Geschrieben wird atomar (Temp-Datei, fsync, austauschen): bricht der Vorgang ab
      (Absturz, beendet, Platte voll), bleibt die bisherige Datei vollständig lesbar und die Temp-Datei wird entfernt.
    - Vorher wird geprüft, ob genug Platz für alte plus neue Datei da ist (cache_io.ZuWenigPlatz statt Absturz).
    - Die Einträge der Orte werden ERSETZT (nicht ergänzt); alle anderen Orte, ihre Meta-Angaben und der
      Algorithmus-Stand der Datei bleiben unverändert (ein veralteter Stand bleibt als veraltet erkennbar,
      damit der Nachtlauf neu rechnet). Meta der Orte: Koordinaten-Prüfsumme + alle 365 Tage als berechnet.
    - Fehlt die Datei oder ist sie nicht lesbar/anders aufgebaut, wird NICHT geschrieben (KalenderNachladenFehler).
    Gibt die Zahl der Termine in der Datei danach zurück."""
    cal_path = Path(cal_path)
    ids = set(neue_je_ort)
    zuwachs = sum(len(v) for v in neue_je_ort.values()) * NACHLADEN_KALENDER_BYTES_JE_TERMIN
    with cache_io.gesperrt_aendern(cal_path):
        if not cal_path.exists():
            raise KalenderNachladenFehler("es gibt noch keine Kalenderdatei (sie entsteht im Nachtlauf)")
        cache_io.pruefe_platz_fuer_atomar(cal_path, zusatz_bytes=zuwachs)
        try:
            daten = json.loads(cal_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise KalenderNachladenFehler("die Kalenderdatei ist nicht lesbar (%s)" % exc)
        termine = daten.get("events") if isinstance(daten, dict) else None
        meta = daten.get("computed_locations") if isinstance(daten, dict) else None
        if not isinstance(termine, list) or not isinstance(meta, dict):
            raise KalenderNachladenFehler("die Kalenderdatei hat einen unerwarteten Aufbau")
        behalten = [e for e in termine if e.get("location_id") not in ids]
        del termine
        for liste in neue_je_ort.values():
            behalten.extend(liste)
        behalten.sort(key=lambda r: (r["shoot_time"], -r["overall_score"]))
        for lid, eintrag in meta_je_ort.items():
            meta[lid] = eintrag
        daten["events"] = behalten
        daten["computed_locations"] = meta
        daten["computed_at"] = computed_at
        cache_io.atomar_schreiben(cal_path, json.dumps(daten, ensure_ascii=False))
    return len(behalten)


def _schreibe_kalender_postfach(cal_dir, neue_je_ort: dict, computed_at: str) -> int:
    """Übergabe an den laufenden Server: eine Zeilendatei (JSON Lines) mit den neuen Kalendereinträgen der Orte —
    Kopfzeile (Prozessnummer, Zeitpunkt, Orte), danach eine Zeile je Ort. Je Zeile lesbar, damit der Server den
    Arbeitsspeicher nicht mit einem einzigen riesigen Einlesen anhält. Gibt die Zahl geschriebener Termine zurück."""
    pfad = Path(cal_dir) / NACHLADEN_KALENDER_POSTFACH_NAME
    zeilen = [json.dumps({"pid": os.getpid(), "computed_at": computed_at, "location_ids": sorted(neue_je_ort)},
                         ensure_ascii=False)]
    n = 0
    for lid in sorted(neue_je_ort):
        zeilen.append(json.dumps({"location_id": lid, "events": neue_je_ort[lid]}, ensure_ascii=False))
        n += len(neue_je_ort[lid])
    cache_io.gesperrt_atomar_schreiben(pfad, "\n".join(zeilen) + "\n")
    return n


async def _kalender_nachladen(orte: list, today: date, computed_at: str, feed_path, cal_path, elev_path,
                              fortschritt) -> None:
    """Der Kalender-Schritt des Nachlade-Laufs für `orte` (aktive Orte dieses Laufs). Meldet seinen Stand über
    `fortschritt(kalender_dict)`. Wirft nie: jeder Fehler wird als Stand "fehler" mit Klartext gemeldet."""
    kal = {"status": "rechnet", "gesamt": len(orte), "fertig": [], "fehler": [], "text": None, "termine": 0,
           "postfach": False}

    def _melde() -> None:
        fortschritt(dict(kal, fertig=list(kal["fertig"]), fehler=list(kal["fehler"])))

    def _ende(status: str, text: "str | None" = None) -> None:
        kal["status"] = status
        kal["text"] = text
        _melde()

    if not orte:
        _ende("uebersprungen", "kein Ort zu rechnen")
        return
    try:
        # früh prüfen (vor der langen Rechnung): gibt es einen Kalender, und reicht der Platz voraussichtlich?
        if not cal_path.exists():
            _ende("uebersprungen", "es gibt noch keine Kalenderdatei (sie entsteht im Nachtlauf)")
            return
        cache_io.pruefe_platz_fuer_atomar(cal_path, zusatz_bytes=len(orte) * NACHLADEN_KALENDER_BYTES_JE_ORT)
        _hoehen_aus_zwischenspeicher(orte, elev_path)
        _melde()
        neue: dict = {}
        meta: dict = {}
        ziel = {(today + timedelta(days=i)).isoformat() for i in range(NACHLADEN_KALENDER_TAGE)}
        for i, loc in enumerate(orte):
            logger.info("  Kalender [%d/%d] %s", i + 1, len(orte), loc.name)
            try:
                neue[loc.id] = await _kalender_fuer_ort(loc, today)
                meta[loc.id] = {"coordinates_hash": _location_hash(loc), "computed_dates": sorted(ziel)}
                kal["fertig"].append(loc.id)
            except Exception as exc:
                kal["fehler"].append(loc.id)
                logger.error("    Kalender-Fehler bei %s: %s – seine bisherigen Einträge bleiben", loc.name, exc)
            _melde()
        # wer inzwischen wieder ausgeschaltet wurde, wird nicht mehr eingemischt
        noch_aktiv = {l.id for l in gz.aktive_orte(orte)}
        for lid in [k for k in neue if k not in noch_aktiv]:
            logger.info("US-141: %s wurde während des Laufs ausgeschaltet – Kalender nicht eingemischt", lid)
            neue.pop(lid, None)
            meta.pop(lid, None)
        if not neue:
            _ende("fehler" if kal["fehler"] else "uebersprungen",
                  "für keinen Ort konnte ein Kalender berechnet werden" if kal["fehler"] else "kein Ort mehr aktiv")
            return
        kal["status"] = "schreibt"
        _melde()
        gesamt = _kalender_einmischen(cal_path, neue, meta, computed_at)
        kal["termine"] = sum(len(v) for v in neue.values())
        logger.info("  ✅ Kalender: %d Orte eingemischt (%d Termine neu, %d in der Datei)", len(neue), kal["termine"], gesamt)
        try:
            _schreibe_kalender_postfach(cal_path.parent, neue, computed_at)
            kal["postfach"] = True
        except Exception as exc:
            logger.warning("  Kalender-Postfach nicht geschrieben (%s) – der Server übernimmt den neuen Stand "
                           "erst beim nächsten Start", exc)
        kal["fertig"] = [k for k in kal["fertig"] if k in neue]
        _ende("fertig")
    except cache_io.ZuWenigPlatz as exc:
        logger.error("US-141: Kalender beim Nachladen übersprungen – %s", exc)
        _ende("fehler", str(exc))
    except KalenderNachladenFehler as exc:
        logger.error("US-141: Kalender beim Nachladen übersprungen – %s", exc)
        _ende("uebersprungen" if "noch keine Kalenderdatei" in str(exc) else "fehler", str(exc))
    except Exception as exc:  # pragma: no cover - letzte Absicherung, der Lauf selbst bleibt gültig
        logger.exception("US-141: Kalender beim Nachladen fehlgeschlagen")
        _ende("fehler", "unerwarteter Fehler: %s" % exc)


NACHLADEN_HAEPPCHEN = 5                         # US-141 Baustein 3: alle 5 Orte wird der Feed freigegeben
NACHLADEN_FORTSCHRITT_NAME = "nachladen_fortschritt.json"   # liegt neben der Feed-Datei; der Server liest sie


def _schreibe_nachlade_fortschritt(feed_path, fertig: list, gesamt: int, fehler: "list | None" = None,
                                   extra: "dict | None" = None) -> None:
    """US-141 Baustein 3: Welche Orte des laufenden Nachlade-Laufs sind in der Feed-Datei fertig?
    Der Server liest die kleine Datei, gibt die fertigen Orte häppchenweise frei und zeigt „x von y
    Orten bereit“. Atomar geschrieben (Leser brauchen keine Sperre); eine Fehlschrift bricht den Lauf nicht ab.

    `extra` (Kalender beim Einschalten): zusätzliche Felder — `feed_fertig` (die Chancen aller Orte sind
    geschrieben, der Server darf das Wetter holen) und `kalender` (Stand des Kalender-Schritts)."""
    try:
        daten = {"pid": os.getpid(), "gesamt": gesamt, "fertig": list(fertig), "fehler": list(fehler or [])}
        if extra:
            daten.update(extra)
        cache_io.atomar_schreiben(
            feed_path.with_name(NACHLADEN_FORTSCHRITT_NAME),
            json.dumps(daten, ensure_ascii=False),
        )
    except Exception as exc:
        logger.warning("  Fortschrittsdatei nicht geschrieben (%s) – der Lauf geht weiter", exc)


async def _run_group_flow(
    location_ids: list,
    today: date,
    computed_at: str,
    feed_path,
    t0: float,
    haeppchen: int = NACHLADEN_HAEPPCHEN,
    mit_feed: bool = True,
    mit_kalender: bool = False,
    cal_path=None,
    elev_path=None,
) -> None:
    """US-141 Baustein 3 (direktes Nachladen): die 14-Tage-Chancen MEHRERER Orte in EINEM Prozess.

    - Nur aktive, nicht gelöschte Orte (zentrale Regel); wer inzwischen wieder pausiert ist, wird übersprungen.
    - Alle `haeppchen` Orte werden die Termine in die Feed-Datei gemischt (unter der Dateisperre, atomar) und
      der Fortschritt vermerkt, damit der Server sie schon vor dem Ende freigeben kann (AK-20).
    - Elevation und Sichtachse gehören NICHT dazu: Höhe und Sichtachse liefen auch im pausierten Zustand weiter.
    - Kalender (Entscheidung 2026-10-15, `mit_kalender`): nach den Chancen werden die 365-Tage-Kalendereinträge
      NUR dieser Orte gerechnet und in einem Schritt in calendar.json eingemischt (siehe _kalender_nachladen).
      `mit_feed=False` (nur Kalender) setzt das Fortsetzen nach einem Neustart um, wenn die Chancen schon stehen.
    - Ein fehlerhafter Ort lässt die anderen weiterlaufen und behält seine bisherigen Termine in der Datei.
    - Sicherung: Der Prozess sichert einmal (in main() am Anfang) – ein Lauf, eine Sicherung (AK-72)."""
    gewollt = [i for i in dict.fromkeys(location_ids) if i]
    karte = {l.id: l for l in LOCATIONS}
    unbekannt = [i for i in gewollt if i not in karte]
    if unbekannt:
        logger.warning("Nachladen: %d unbekannte/gelöschte Orte übersprungen: %s", len(unbekannt), unbekannt)
    orte = [karte[i] for i in gewollt if i in karte]
    aktive = gz.aktive_orte(orte)
    aktive_ids = {l.id for l in aktive}
    for l in orte:
        if l.id not in aktive_ids:
            logger.info("US-141: %s ist pausiert – beim Nachladen übersprungen", l.name)
    logger.info("── Nachladen: %d Orte in einem Lauf ──", len(aktive))
    fertig: list = []
    fehler: list = []
    puffer: dict = {}
    cal_path = cal_path if cal_path is not None else feed_path.with_name("calendar.json")
    elev_path = elev_path if elev_path is not None else feed_path.with_name("elevations.json")
    if not mit_feed:
        # nur Kalender (Fortsetzen nach Neustart): die Chancen dieser Orte stehen schon in der Feed-Datei
        fertig = [l.id for l in aktive]
    _schreibe_nachlade_fortschritt(feed_path, fertig, len(aktive), fehler,
                                   extra={"feed_fertig": True} if not mit_feed else None)

    def _abschicken() -> None:
        if not puffer:
            return
        gesamt = _merge_and_write_feed_many(feed_path, puffer, computed_at)
        fertig.extend(puffer.keys())
        logger.info("  ✅ Feed: %d Orte freigegeben (%d von %d), %d Termine in der Datei",
                    len(puffer), len(fertig), len(aktive), gesamt)
        puffer.clear()
        _schreibe_nachlade_fortschritt(feed_path, fertig, len(aktive), fehler)

    for i, loc in enumerate(aktive if mit_feed else []):
        logger.info("  Nachladen [%d/%d] %s", i + 1, len(aktive), loc.name)
        try:
            puffer[loc.id] = await _feed_fuer_ort(loc, today)
        except Exception as exc:
            fehler.append(loc.id)
            logger.error("    Fehler bei %s: %s – bisherige Termine bleiben", loc.name, exc)
            _schreibe_nachlade_fortschritt(feed_path, fertig, len(aktive), fehler)
        if len(puffer) >= haeppchen:
            _abschicken()
    _abschicken()
    logger.info("=== Nachladen abgeschlossen in %.1fs: %d fertig, %d fehlgeschlagen ===",
                time.time() - t0, len(fertig), len(fehler))
    if aktive and len(fehler) == len(aktive):
        raise RuntimeError("Nachladen: für keinen der %d Orte konnten Chancen berechnet werden" % len(aktive))
    if not mit_kalender:
        return

    # ── Kalender (Entscheidung 2026-10-15): zuletzt, nur für die Orte dieses Laufs ──
    def _kalender_melden(kal: dict) -> None:
        _schreibe_nachlade_fortschritt(feed_path, fertig, len(aktive), fehler,
                                       extra={"feed_fertig": True, "kalender": kal})

    _kalender_melden({"status": "rechnet", "gesamt": len(aktive), "fertig": [], "fehler": [], "text": None,
                      "termine": 0, "postfach": False})
    t_kal = time.time()
    await _kalender_nachladen(aktive, today, computed_at, feed_path, cal_path, elev_path, _kalender_melden)
    logger.info("=== Kalender beim Nachladen abgeschlossen in %.1fs ===", time.time() - t_kal)


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
        gerechnet: set = set()
        feed = await compute_feed(today, gerechnet_ids=gerechnet)
        _write_feed_cache(feed_path, feed, computed_at, gerechnet_ids=gerechnet)
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


def _parse_location_ids(wert) -> list:
    """`--location-ids a,b,c` -> ['a', 'b', 'c'] (Leerstellen und leere Einträge fallen weg)."""
    if not wert:
        return []
    teile = wert if isinstance(wert, (list, tuple)) else str(wert).split(",")
    return [t.strip() for t in teile if t and t.strip()]


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
    # US-141: Zustand der Gebiets-Schalter aus der Datenbank lesen (welche Orte sind pausiert?).
    gz.registriere_quelle(lambda: LocationStore().load_area_states())

    # TASK-18: Snapshot vor Precompute (lokale Sicherung, 7 Versionen)
    from data import backup as _backup
    _backup.snapshot_before_precompute()
    # TASK-61 (Option B): 8-Tabellen-JSON-Export zusätzlich an den bereits
    # regelmäßig laufenden Vorberechnungslauf koppeln — garantiert eine
    # Obergrenze für die Sicherungslücke der 6 neu erfassten Tabellen, auch
    # ohne zwischenzeitlichen Location-Edit.
    _backup.backup_after_precompute()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today()
    computed_at = datetime.now(timezone.utc).isoformat()

    # US-141: --ortsdaten-only = nur Höhe und Sichtachse (Gruppe A), weder Feed noch Kalender.
    ortsdaten_only = bool(getattr(args, "ortsdaten_only", False))
    run_feed = not args.calendar_only and not ortsdaten_only
    run_calendar = not args.feed_only and not ortsdaten_only
    location_id: str | None = getattr(args, "location_id", None)
    # US-141 Baustein 3: --location-ids a,b,c = Nachlade-Lauf für mehrere Orte in EINEM Prozess (nur Feed).
    location_ids = _parse_location_ids(getattr(args, "location_ids", None))
    feed_path = CACHE_DIR / "opportunities.json"
    elev_path = CACHE_DIR / "elevations.json"

    if location_ids:
        if args.calendar_only or ortsdaten_only:
            raise SystemExit("--location-ids gilt für das Nachladen (Chancen, mit --mit-kalender auch der Kalender); "
                             "--calendar-only und --ortsdaten-only gehören nicht dazu.")
        nur_kalender = bool(getattr(args, "nur_kalender", False))
        await _run_group_flow(
            location_ids=location_ids, today=today, computed_at=computed_at, feed_path=feed_path, t0=t0,
            mit_feed=not nur_kalender,
            mit_kalender=bool(getattr(args, "mit_kalender", False)) or nur_kalender,
            cal_path=CACHE_DIR / "calendar.json", elev_path=elev_path,
        )
    elif location_id:
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
    parser.add_argument("--ortsdaten-only", dest="ortsdaten_only", action="store_true",
                        help="US-141: Nur Höhe und Sichtachse (für pausierte Orte), weder Feed noch Kalender")
    parser.add_argument("--full", action="store_true", help="Kalender vollständig neu berechnen (ignoriert Cache)")
    parser.add_argument("--location-id", default=None, help="Nur diese eine Location neu berechnen (Single-Location-Recompute nach PATCH)")
    parser.add_argument("--location-ids", default=None,
                        help="US-141: Nachladen – diese Orte (kommagetrennt) in EINEM Lauf neu berechnen, nur Feed")
    parser.add_argument("--mit-kalender", dest="mit_kalender", action="store_true",
                        help="US-141: beim Nachladen (--location-ids) nach den Chancen auch den 365-Tage-Kalender dieser Orte rechnen")
    parser.add_argument("--nur-kalender", dest="nur_kalender", action="store_true",
                        help="US-141: beim Nachladen (--location-ids) nur den Kalender dieser Orte rechnen (Fortsetzen nach Neustart)")
    args = parser.parse_args()
    if getattr(args, "location_ids", None):
        # US-141: Vom Server beendet (Gebiet wieder ausgeschaltet) -> sauber abbrechen. Eine halb geschriebene
        # Temp-Datei räumt cache_io.atomar_schreiben dabei selbst weg; die Zieldatei bleibt unberührt.
        import signal

        def _beendet(signum, frame):  # pragma: no cover - nur im eigenen Prozess
            raise SystemExit(128 + int(signum))

        signal.signal(signal.SIGTERM, _beendet)
    asyncio.run(main(args))
