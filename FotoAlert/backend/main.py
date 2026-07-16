"""
FotoAlert Backend – FastAPI Hauptanwendung (Cache-First Architektur)

Startup-Ablauf:
  1. JSON-Cache laden (< 100ms)        → App sofort nutzbar
  2. Wetter-Overlay für T+0..T+3       → nur wenige API-Calls, ~5–10s
  3. Fertig

Hintergrund (täglich 05:30):
  precompute.py läuft als Subprocess → schreibt neue JSON-Caches → Server lädt nach

Endpoints:
  GET  /health                   Server-Status
  GET  /locations                Alle Locations
  GET  /locations/{id}           Einzelne Location
  GET  /opportunities            Kommende Foto-Chancen (14 Tage, mit Wetter)
  GET  /opportunities/today      Chancen für heute
  GET  /daily-briefing           Tages-Briefing (top 10)
  GET  /calendar                 Jahreskalender (365 Tage, nur Astronomie)
  POST /register-device          Push-Token registrieren
  POST /preview-alignment        Alignment-Vorschau für zwei GPS-Punkte (US-05)
  POST /refresh                  Manueller Refresh (startet precompute.py)
"""

from __future__ import annotations

import asyncio
import json
import logging
import copy as _copy
import math
import subprocess
import sys
import uuid as _uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Depends, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# US-120: Beispielbild-Upload — Verkleinerung, Kompression, EXIF-Ausrichtungskorrektur
import io as _io
from PIL import Image, ImageOps, UnidentifiedImageError

# US-66: .env laden, damit Login-Passwörter & Auth-Secret aus backend/.env kommen
# (python-dotenv ist in requirements; load_dotenv überschreibt bereits gesetzte Env-Vars nicht).
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import auth  # US-66: Login/Token/Rollen (Option B)

from calculations.astronomy import (
    calculate_subject_angular_profile,
    find_precise_alignment_times,
)
from calculations.weather import fetch_weather_forecast, fetch_aerosol_forecast, RED_SKY_AOD_THRESHOLD, CLOUD_MOOD_PROJECTION_DISTANCE_M, calculate_photo_weather_score, wmo_code_to_description, calculate_golden_cloud_score, should_generate_golden_clouds_event, should_generate_red_sky_event, should_generate_red_clouds_event
from calculations import weather_grib  # US-112: DWD ICON + MET Norway → weicher PNG-Overlay
from calculations import sightline as sightline_calc  # US-09: Sichtachsen-Check (Raycast)
from discover.geometry import destination_point  # US-131: Projektion Wolken-/Dunstabfrage entlang Sichtachse
from data.locations import (
    LOCATIONS, get_location_by_id, PhotoLocation, LocationCategory,
    COORD_FIELDS, TEXT_FIELDS, NUMERIC_FIELDS, LIST_FIELDS,
    PATCHABLE_LOCATION_FIELDS, RECOMPUTE_TRIGGER_FIELDS, OVERRIDE_RELOAD_FIELDS,
)
from data.store import LocationStore, compute_geo_hash
from data import backup
from data import qa_azimuth, qa_focal, qa_description  # TASK-45/46/47: Auto-QA (Azimut, Beschreibung, Brennweite)
from data.elevation import provider as _elevation_provider  # US-09: Höhenprofil für Sichtachsen-Check
from models.schemas import (
    CameraHintOut,
    DailyBriefingOut,
    HealthOut,
    LocationOut,
    OpportunityOut,
)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FotoAlert API",
    description="Intelligente Foto-Chancen",
    version="2.0.0",
)

# TASK-83: explizite Origin-Liste statt Wildcard — Voraussetzung für allow_credentials=True
# (Wildcard + Credentials ist per Fetch-Spec verboten, der Browser würde jede Cookie-Antwort
# verwerfen). Prod-Domain + lokaler Dev-Server, siehe deploy/setup_server.sh (DOMAIN).
_ALLOWED_ORIGINS = [
    "https://fotoalert.stephanschumann.com",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Cache-Pfade
# ---------------------------------------------------------------------------

_CACHE_DIR          = Path(__file__).parent / "data" / "cache"
_OPP_CACHE          = _CACHE_DIR / "opportunities.json"
_CAL_CACHE          = _CACHE_DIR / "calendar.json"
_ELEV_CACHE         = _CACHE_DIR / "elevations.json"
_DISCOVER_CACHE     = _CACHE_DIR / "discover.json"

# US-120: Beispielbild-Verzeichnis (Host-Upload pro Location, ein Bild, ersetzt beim erneuten Upload)
_IMAGE_DIR          = Path(__file__).parent / "data" / "location_images"
_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
_IMAGE_MAX_UPLOAD_BYTES = 1 * 1024 * 1024        # 1 MB: bis hier angenommen, automatisch komprimiert
_IMAGE_HARD_LIMIT_BYTES = 20 * 1024 * 1024       # 20 MB: darüber klare Ablehnung ohne Verarbeitung
_IMAGE_TARGET_BYTES     = 500 * 1024             # ~500 KB Zielgröße nach Kompression
_IMAGE_MAX_DIMENSION_PX = 2000                   # lange Kante nach Verkleinerung

# TASK-17: Zentraler SQLite-Store für nutzereditierbare Daten
_store = LocationStore()


def _load_elevation_cache() -> None:
    """Lädt gecachte Geländehöhen und patcht alle Location-Objekte."""
    if not _ELEV_CACHE.exists():
        return
    try:
        elevations: dict = json.loads(_ELEV_CACHE.read_text(encoding="utf-8")).get("elevations", {})
        loc_map = {loc.id: loc for loc in LOCATIONS}
        patched = 0
        for loc_id, data in elevations.items():
            loc = loc_map.get(loc_id)
            if loc:
                loc.elevation_difference_m = data["elevation_difference_m"]
                patched += 1
        if patched:
            logger.info("Geländehöhen geladen: %d Locations aus elevations.json", patched)
    except Exception as exc:
        logger.warning("Fehler beim Laden von elevations.json: %s", exc)


def _load_custom_locations() -> None:
    """Lädt gespeicherte Custom-Locations aus SQLite und hängt sie an LOCATIONS.
    TASK-17: ersetzt JSON-basiertes Laden.
    Fallback: falls DB leer und JSON noch vorhanden, migriert automatisch.
    """
    try:
        entries = _store.load_all_custom()

        # Fallback: wenn DB leer ist und JSON noch vorhanden → automatisch migrieren
        if not entries:
            _json_file = Path(__file__).parent / "data" / "custom_locations.json"
            if _json_file.exists():
                import json as _json
                raw = _json.loads(_json_file.read_text(encoding="utf-8"))
                for e in raw:
                    _store.create_custom_if_not_exists(e)
                entries = _store.load_all_custom()
                if entries:
                    logger.info("Custom Locations auto-migriert aus JSON: %d Einträge", len(entries))

        ids_existing = {loc.id for loc in LOCATIONS}
        added = 0
        for e in entries:
            if e.get("id") in ids_existing:
                continue
            loc = PhotoLocation(
                id=e["id"], name=e["name"], description=e.get("description", ""),
                category=LocationCategory[e.get("category", "SKYLINE")],
                observer_lat=e["observer_lat"], observer_lon=e["observer_lon"],
                subject_lat=e["subject_lat"], subject_lon=e["subject_lon"],
                subject_name=e.get("subject_name", ""), subject_height_m=e.get("subject_height_m", 0),
                subject_width_m=e.get("subject_width_m", 0), distance_m=e.get("distance_m", 0),
                focal_length_suggestions=e.get("focal_length_suggestions", []),
                special_notes=e.get("special_notes", ""), difficulty=e.get("difficulty", 1),
                observer_floor_height_m=float(e.get("observer_floor_height_m", 0.0)),
                image_filename=e.get("image_filename"),
                image_focus_x=e.get("image_focus_x"),
                image_focus_y=e.get("image_focus_y"),
            )
            LOCATIONS.append(loc)
            ids_existing.add(loc.id)
            added += 1
        if added:
            logger.info("Custom Locations geladen: %d Einträge aus SQLite", added)
    except Exception as exc:
        logger.warning("Fehler beim Laden der Custom Locations: %s", exc)


def _save_custom_location(loc: PhotoLocation) -> None:
    """Persistiert eine neue Custom-Location in SQLite (TASK-17: ersetzt JSON-Write)."""
    _store.create_custom({
        "id": loc.id, "name": loc.name, "description": loc.description,
        "category": loc.category.name,
        "observer_lat": loc.observer_lat, "observer_lon": loc.observer_lon,
        "subject_lat": loc.subject_lat, "subject_lon": loc.subject_lon,
        "subject_name": loc.subject_name, "subject_height_m": loc.subject_height_m,
        "subject_width_m": loc.subject_width_m, "distance_m": loc.distance_m,
        "focal_length_suggestions": loc.focal_length_suggestions,
        "special_notes": loc.special_notes, "difficulty": loc.difficulty,
        "observer_floor_height_m": loc.observer_floor_height_m,
    })

async def _reverse_geocode(lat: float, lon: float) -> str:
    """Gibt einen kurzen Ortsnamen via Nominatim zurück (leer bei Fehler)."""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"format": "jsonv2", "lat": lat, "lon": lon, "zoom": 16},
                headers={"User-Agent": "FotoAlert/1.3 (personal)"},
                timeout=5.0,
            )
            data = r.json()
            addr = data.get("address", {})
            for key in ("suburb", "neighbourhood", "quarter", "village", "hamlet", "town", "city_district", "city"):
                if addr.get(key):
                    return addr[key]
            return data.get("name", "")
    except Exception as exc:
        logger.debug("Reverse Geocoding fehlgeschlagen: %s", exc)
        return ""


def _update_custom_location_file(loc_id: str, **fields) -> bool:
    """Aktualisiert Felder einer Custom-Location in SQLite (TASK-17: ersetzt JSON-Write)."""
    return _store.update_custom(loc_id, **fields)


# ---------------------------------------------------------------------------
# In-Memory State
# ---------------------------------------------------------------------------

# Flache Listen von dicts (aus JSON geladen, Wetter-Felder werden überschrieben)
_feed_cache:     list[dict] = []   # 14-Tage Feed
_calendar_cache: list[dict] = []   # 365-Tage Kalender
_discover_cache: dict       = {}   # Scout-Tab (Mond-Alignment-Chancen)

_cache_loaded_at:   Optional[datetime] = None
_weather_updated_at: Optional[datetime] = None

# US-112: Wetter-Karten-Overlay (DWD ICON-D2/-EU + MET Norway → PNG je Stunde).
# Prozess-Cache: Metadaten (bounds, hourly_times, Quellen) + PNG-Bytes je Stunde
# pro Feld. Wird vom Hintergrund-Job gefüllt; /weather-map liefert Metadaten,
# /weather-map/png/{field}/{idx} die einzelnen Bilder. TTL via _weather_map_updated_at.
_weather_map_cache: Optional[dict] = None           # {bounds, hourly_times, sources, attribution, n_points}
_weather_map_png:   dict = {"cloud": [], "precip": []}  # Listen Optional[bytes] je Stunde
_weather_map_updated_at: Optional[datetime] = None
_weather_map_building: bool = False
_WEATHER_MAP_TTL = timedelta(hours=1)               # Modell-Overlay 1 h gültig
_precompute_running: bool = False
_recompute_pending:  set  = set()   # BUG-35: IDs mit laufendem/ausstehendem Recompute

# TASK-48: Single-Flight-Guard für den nächtlichen QA-Lauf (Azimut/Brennweite
# auto-verbessern). Analog zu _precompute_running; verhindert Doppelläufe und
# Überlappung mit dem großen Recompute.
_qa_pass_running: bool = False
# TASK-48: Drosselungs-Parameter (Pause zwischen Spots, Schutz externer Dienste).
_QA_PASS_THROTTLE_S: float = 1.0

# US-106 Teil 2: Scout-Volllauf nach Location-Änderung entprellt anstoßen.
_scout_running: bool = False              # Single-Flight-Guard (kein Doppellauf)
_scout_dirty:   bool = False             # Nachlauf-Flag (während Lauf erneut geändert)
_scout_debounce_task: Optional["asyncio.Task"] = None
_SCOUT_DEBOUNCE_S: float = 90.0          # Fenster für mehrere schnelle Edits (Zielzeit < 2–3 Min)

# Job-Status-Tracking (US-34)
_job_status: dict = {
    "weather":  {"status": "idle", "last_run": None, "last_error": None, "duration_s": None},
    "feed":     {"status": "idle", "last_run": None, "last_error": None, "duration_s": None},
    "calendar": {"status": "idle", "last_run": None, "last_error": None, "duration_s": None},
    "weather-map": {"status": "idle", "last_run": None, "last_error": None, "duration_s": None},  # US-112
    "sightlines": {"status": "idle", "last_run": None, "last_error": None, "duration_s": None},  # US-09
}

# US-09: Single-Flight-Guard für den manuellen Sichtachsen-Refresh (analog zu
# _precompute_running/_qa_pass_running — verhindert parallele Läufe).
_sightline_refresh_running: bool = False

def _job_start(job: str) -> float:
    """Markiert Job als laufend, gibt Startzeit zurück."""
    import time as _time
    _job_status[job]["status"] = "running"
    _job_status[job]["last_error"] = None
    return _time.monotonic()

def _job_done(job: str, t0: float) -> None:
    """Markiert Job als fertig."""
    import time as _time
    _job_status[job]["status"] = "done"
    _job_status[job]["last_run"] = datetime.now(timezone.utc).isoformat()
    _job_status[job]["duration_s"] = round(_time.monotonic() - t0, 1)

def _job_error(job: str, t0: float, msg: str) -> None:
    """Markiert Job als fehlgeschlagen."""
    import time as _time
    _job_status[job]["status"] = "error"
    _job_status[job]["last_run"] = datetime.now(timezone.utc).isoformat()
    _job_status[job]["duration_s"] = round(_time.monotonic() - t0, 1)
    _job_status[job]["last_error"] = msg

# Scheduler
scheduler = AsyncIOScheduler(timezone="Europe/Berlin")

# Test-/Sandbox-Modus (Test-Harness, PIPELINE.md Schritt 3): Wenn FOTOALERT_NO_BACKGROUND=1
# gesetzt ist, startet der App-Startup ohne Scheduler, Precompute und Netzwerk-Tasks.
# Damit lässt sich die App im Sandbox deterministisch und offline hochfahren (TestClient).
# Prod-Verhalten bleibt unverändert, solange das Flag nicht gesetzt ist.
import os as _os
_NO_BACKGROUND = _os.getenv("FOTOALERT_NO_BACKGROUND") == "1"


# ---------------------------------------------------------------------------
# Cache laden
# ---------------------------------------------------------------------------

def _backfill_coords(events: list[dict]) -> None:
    """Ergänzt subject_lat/lon aus LOCATIONS falls im Cache noch nicht vorhanden.

    US-09: Ergänzt zusätzlich sightline_status/-angle, falls der Cache aus einem
    Stand vor diesem Ticket geladen wird (Feld fehlt komplett im JSON) — sonst
    würde ein alter Cache-Eintrag ohne das Feld fälschlich als "nicht_geprueft"
    im Frontend interpretiert werden erst NACH dem nächsten Precompute-Lauf.
    """
    loc_map = {loc.id: loc for loc in LOCATIONS}
    for e in events:
        if "subject_lat" not in e:
            loc = loc_map.get(e.get("location_id", ""))
            if loc:
                e["subject_lat"] = loc.subject_lat
                e["subject_lon"] = loc.subject_lon
        if "sightline_status" not in e:
            loc = loc_map.get(e.get("location_id", ""))
            e["sightline_status"] = getattr(loc, "sightline_status", None) or "nicht_geprueft" if loc else "nicht_geprueft"
            e["sightline_angle_deg"] = getattr(loc, "sightline_angle_deg", None) if loc else None


def _load_caches() -> bool:
    """
    Lädt die vorberechneten JSON-Caches von Disk.
    Gibt True zurück wenn mindestens der Feed-Cache gefunden wurde.
    """
    global _feed_cache, _calendar_cache, _cache_loaded_at, _recompute_pending

    found = False

    if _OPP_CACHE.exists():
        try:
            data = json.loads(_OPP_CACHE.read_text(encoding="utf-8"))
            _feed_cache = data.get("opportunities", [])
            _backfill_coords(_feed_cache)
            logger.info("Feed-Cache geladen: %d Events (berechnet: %s)",
                        len(_feed_cache), data.get("computed_at", "?")[:16])
            found = True
        except Exception as e:
            logger.error("Fehler beim Laden von opportunities.json: %s", e)
    else:
        logger.warning("opportunities.json nicht gefunden – Cache leer")

    if _CAL_CACHE.exists():
        try:
            data = json.loads(_CAL_CACHE.read_text(encoding="utf-8"))
            _calendar_cache = data.get("events", [])
            logger.info("Kalender-Cache geladen: %d Events", len(_calendar_cache))
        except Exception as e:
            logger.error("Fehler beim Laden von calendar.json: %s", e)

    _cache_loaded_at = datetime.now(timezone.utc)

    # US-106: Pending NICHT mehr hier freigeben.
    # Früher (BUG-35) wurde eine ID aus _recompute_pending entfernt, sobald sie
    # nach dem Feed-Write im Feed-Cache auftauchte — also BEVOR das Wetter für
    # die Location nachgeladen war. Dadurch verschwand das "wird aktualisiert"-
    # Banner zu früh (lügendes Banner). Die Freigabe passiert jetzt erst in
    # _finalize_pending(), wenn Feed UND Wetter für die Location stehen.

    return found


def _load_discover_cache() -> None:
    """Lädt Scout-Cache (discover.json) von Disk falls vorhanden."""
    global _discover_cache
    if not _DISCOVER_CACHE.exists():
        return
    try:
        _discover_cache = json.loads(_DISCOVER_CACHE.read_text(encoding="utf-8"))
        logger.info("Scout-Cache geladen: %d Chancen (berechnet: %s)",
                    _discover_cache.get("count", 0),
                    str(_discover_cache.get("generated_at", "?"))[:16])
    except Exception as e:
        logger.error("Fehler beim Laden von discover.json: %s", e)


async def _refresh_discover() -> None:
    """
    Führt die Scout-Pipeline (Volllauf) aus und aktualisiert _discover_cache.

    US-106 Teil 2: Single-Flight + Dirty-Nachlauf. Der Scout existiert NUR als
    Volllauf (keine location_id-Unterstützung). Damit eine Location-Änderung den
    Scout zeitnah aktualisiert, ohne bei mehreren schnellen Edits mehrere teure
    parallele Läufe zu starten:
      - läuft bereits ein Scout-Lauf → nur das Dirty-Flag setzen (Nachlauf),
        statt einen zweiten Lauf parallel zu starten;
      - nach jedem Lauf wird geprüft, ob währenddessen etwas dirty wurde, und
        genau EIN Nachlauf gemacht.
    """
    global _discover_cache, _scout_running, _scout_dirty
    from discover.pipeline import refresh_discover_cache

    if _scout_running:
        # Single-Flight: kein zweiter paralleler Volllauf. Nachlauf vormerken.
        _scout_dirty = True
        logger.info("Scout-Pipeline läuft bereits – Nachlauf vorgemerkt (dirty).")
        return

    _scout_running = True
    try:
        while True:
            _scout_dirty = False
            try:
                logger.info("Scout-Pipeline startet (Volllauf)...")
                await refresh_discover_cache(_DISCOVER_CACHE)
                _load_discover_cache()
            except Exception as e:
                logger.error("Scout-Pipeline fehlgeschlagen: %s", e)
            # US-106: Wurde während des Laufs erneut eine Änderung gemeldet → genau
            # ein Nachlauf, dann fertig.
            if not _scout_dirty:
                break
            logger.info("Scout-Pipeline: Dirty-Flag gesetzt → genau ein Nachlauf.")
    finally:
        _scout_running = False


def _trigger_discover_debounced() -> None:
    """
    US-106 Teil 2: Entprellter Trigger für den Scout-Volllauf nach einer
    Location-Änderung. Mehrere schnelle Edits werden zu EINEM Lauf zusammengefasst
    (Debounce-Fenster _SCOUT_DEBOUNCE_S). Der eigentliche Lauf ist durch
    _refresh_discover Single-Flight-geschützt.
    """
    global _scout_debounce_task, _scout_dirty
    if _NO_BACKGROUND:
        return

    # Läuft gerade ein Scout-Lauf, reicht das Dirty-Flag (Nachlauf nach Lauf-Ende).
    if _scout_running:
        _scout_dirty = True
        logger.info("Scout-Trigger während laufendem Lauf → dirty (Nachlauf).")
        return

    # Bestehenden Debounce-Timer zurücksetzen (Edits zusammenfassen).
    if _scout_debounce_task and not _scout_debounce_task.done():
        _scout_debounce_task.cancel()

    async def _delayed() -> None:
        try:
            await asyncio.sleep(_SCOUT_DEBOUNCE_S)
        except asyncio.CancelledError:
            return
        await _refresh_discover()

    _scout_debounce_task = asyncio.create_task(_delayed())
    logger.info("Scout-Refresh in %.0fs angestoßen (debounced).", _SCOUT_DEBOUNCE_S)


# ---------------------------------------------------------------------------
# Wetter-Overlay
# ---------------------------------------------------------------------------

def _apply_weather_to_event(
    e: dict,
    forecast: object,
    now_utc: datetime,
    cutoff: datetime,
    aerosol_forecast: object = None,
    sun_dir_forecast: object = None,
    antisolar_dir_forecast: object = None,
) -> bool:
    """
    US-106: Wetter-Anwendung für GENAU EIN Feed-Event (DRY-Helfer für Voll- und
    Single-Overlay). Setzt zusätzlich e["weather_status"]:
      - "none": Event außerhalb T+3 → planmäßig kein Wetter (nicht "lädt ewig").
      - "ok":   echtes Wetter aufgespielt.
    Bei "none" und fehlendem Forecast bleibt weather_status unverändert "lädt"
    (kein Status → Frontend zeigt "wird nachgeladen", solange Location pending ist).
    Gibt True zurück, wenn echtes Wetter ("ok") gesetzt wurde.

    US-130: aerosol_forecast ist optional (Default None), repräsentiert seit US-131 den
    Dunstwert am GEGENRICHTUNGS-/Antisolar-projizierten Punkt (nicht mehr am
    Fotografen-Standort) — fehlt er (Aerosol-Abruf nicht verfügbar/fehlgeschlagen, AK-5),
    bleibt weather_details["aerosol_optical_depth"] None und should_generate_red_sky_event()
    fällt sauber auf den reinen Wolken-Check zurück, ohne dass diese Funktion hier einen
    Fehler wirft.

    US-131 (Option B, Weg-Gate 2026-07-13): sun_dir_forecast/antisolar_dir_forecast sind
    optional (Default None) — Wetter-Forecasts an den beiden entlang der Sichtachse
    projizierten Punkten (Sonnenrichtung bzw. Gegenrichtung/Antisolarpunkt, jeweils
    CLOUD_MOOD_PROJECTION_DISTANCE_M hinter dem Motiv). Daraus werden zwei GETRENNTE
    golden_cloud_score/cl/cm-Werte berechnet (entkoppelt die bisher geteilte Berechnung,
    Pre-Mortem Szenario 2): e["golden_cloud_score_sun_dir"]/e["cl_sun_dir"]/e["cm_sun_dir"]
    füttert künftig GOLDEN_CLOUDS, e["golden_cloud_score_antisolar_dir"]/
    e["cl_antisolar_dir"]/e["cm_antisolar_dir"] füttert künftig RED_SKY. Schlägt einer der
    beiden Fetches fehl (Forecast None oder kein Datenpunkt), bleibt das jeweilige Tripel
    None — kein Fallback auf den Fotografen-Standort-Wert (AK-11).

    Der bestehende e["golden_cloud_score"] (Fotografen-Standort, aus `forecast`/`w_at`)
    bleibt UNVERÄNDERT bestehen — er wird weiterhin für den weather_score-Bonus (unten)
    und für das bestehende, von diesem Ticket nicht berührte US-07-Wolkenstimmungs-Filter
    im Frontend (`o.golden_cloud_score`) benötigt (AK-2: allgemeine Wetteranzeige bleibt
    am Fotografen-Standort verankert).
    """
    shoot_dt = datetime.fromisoformat(e["shoot_time"])
    if shoot_dt > cutoff or shoot_dt < now_utc - timedelta(hours=1):
        # Außerhalb T+3: planmäßig kein Wetter (Forecast reicht nur ~7 Tage).
        e["weather_score"]  = 0.0
        e["overall_score"]  = e["astronomy_score"]
        e["weather_status"] = "none"
        return False

    if not forecast:
        return False

    w_at = forecast.get_at(shoot_dt)
    if not w_at:
        return False

    w_score, gcs = _weather_score_with_golden_bonus(e.get("event_type", ""), w_at)

    e["weather_score"]     = round(w_score, 3)
    e["overall_score"]     = round(e["astronomy_score"] * 0.65 + w_score * 0.35, 3)
    e["golden_cloud_score"] = round(gcs, 3) if gcs is not None else None
    e["weather_description"] = wmo_code_to_description(w_at.weather_code) if hasattr(w_at, "weather_code") else ""
    e["weather_details"] = _build_weather_details_dict(w_at, aerosol_forecast, shoot_dt)

    # US-131 (AK-8/9/11): entkoppelte Wolkenwerte GOLDEN_CLOUDS/RED_SKY — je eigener
    # Forecast-Parameter, keine geteilten Zwischenvariablen (Pre-Mortem TASK-76).
    gcs_sun_dir, cl_sun_dir, cm_sun_dir = _directional_cloud_values(sun_dir_forecast, shoot_dt)
    gcs_antisolar_dir, cl_antisolar_dir, cm_antisolar_dir = _directional_cloud_values(antisolar_dir_forecast, shoot_dt)

    e["golden_cloud_score_sun_dir"] = gcs_sun_dir
    e["cl_sun_dir"] = cl_sun_dir
    e["cm_sun_dir"] = cm_sun_dir
    e["golden_cloud_score_antisolar_dir"] = gcs_antisolar_dir
    e["cl_antisolar_dir"] = cl_antisolar_dir
    e["cm_antisolar_dir"] = cm_antisolar_dir

    e["weather_status"] = "ok"
    return True


def _weather_score_with_golden_bonus(event_type: str, w_at) -> tuple:
    """
    TASK-76 (aus _apply_weather_to_event extrahiert): Foto-Wetter-Score plus
    optionaler Golden-Cloud-Score-Bonus für die Goldene Stunde (Fotografen-
    Standort-Werte aus `w_at`) — unverändert von den Sonnenrichtungs-/
    Gegenrichtungs-Werten aus _directional_cloud_values().

    US-07: Bonus auf weather_score wenn gcs >= 0.7 (+5 Pp, gedeckelt bei 1.0).
    Nur +5 (nicht +10) wegen Cirrus-Doppelbewertung mit calculate_photo_weather_score.
    gcs bleibt None außerhalb der Goldenen Stunde.

    Gibt zurück: (w_score, gcs)
    """
    w_score = calculate_photo_weather_score(w_at)
    if event_type in _GOLDEN_HOUR_TYPES:
        gcs = calculate_golden_cloud_score(
            w_at.cloud_cover_low_pct,
            w_at.cloud_cover_mid_pct,
            w_at.cloud_cover_high_pct,
        )
        if gcs >= 0.7:
            w_score = min(1.0, w_score + 0.05)
    else:
        gcs = None
    return w_score, gcs


def _build_weather_details_dict(w_at, aerosol_forecast: object, shoot_dt: datetime) -> dict:
    """
    TASK-76 (aus _apply_weather_to_event extrahiert): Baut das weather_details-Dict
    für ein Event (Fotografen-Standort-Wetterwerte aus `w_at`) inkl.
    aerosol_optical_depth.

    US-130: Aerosol-Optische-Dicke (Dunst-Signal) — None wenn kein Abruf/kein
    Datenpunkt verfügbar (AK-5, kein Fehler dadurch). US-131: seit Option B am
    Gegenrichtungs-/Antisolar-projizierten Punkt abgefragt (`aerosol_forecast`),
    nicht mehr am Fotografen-Standort.
    """
    details = {
        "temperature_c":        round(w_at.temperature_c, 1),
        "precipitation_prob_pct": round(w_at.precipitation_prob_pct),
        "precipitation_mm":     round(w_at.precipitation_mm, 1),
        "cloud_cover_pct":      round(w_at.cloud_cover_pct),
        "cloud_cover_low_pct":  round(w_at.cloud_cover_low_pct),
        "cloud_cover_mid_pct":  round(w_at.cloud_cover_mid_pct),
        "cloud_cover_high_pct": round(w_at.cloud_cover_high_pct),
        "wind_speed_kmh":       round(w_at.wind_speed_kmh),
        "wind_direction_deg":   round(w_at.wind_direction_deg),
        "visibility_m":         round(w_at.visibility_m),
    }
    aod_value = None
    if aerosol_forecast is not None:
        a_at = aerosol_forecast.get_at(shoot_dt)
        if a_at is not None and a_at.aerosol_optical_depth is not None:
            aod_value = round(a_at.aerosol_optical_depth, 3)
    details["aerosol_optical_depth"] = aod_value
    return details


def _directional_cloud_values(dir_forecast: object, shoot_dt: datetime) -> tuple:
    """
    TASK-76 (aus _apply_weather_to_event extrahiert): Berechnet
    (golden_cloud_score, cl, cm) für EINEN projizierten Punkt (Sonnenrichtung ODER
    Gegenrichtung/Antisolarpunkt) — für beide Richtungen separat mit jeweils
    eigenem `dir_forecast`-Parameter aufgerufen (US-131 AK-11: keine geteilten
    Zwischenvariablen zwischen den beiden Aufrufen, siehe Pre-Mortem TASK-76).

    Gibt (None, None, None) zurück, wenn kein Forecast vorhanden ist oder kein
    Datenpunkt zum Aufnahmezeitpunkt existiert — kein Fallback auf einen anderen
    Wert.
    """
    if dir_forecast is None:
        return None, None, None
    w = dir_forecast.get_at(shoot_dt)
    if w is None:
        return None, None, None
    gcs = calculate_golden_cloud_score(
        w.cloud_cover_low_pct, w.cloud_cover_mid_pct, w.cloud_cover_high_pct,
    )
    return round(gcs, 3), round(w.cloud_cover_low_pct), round(w.cloud_cover_mid_pct)


_GOLDEN_HOUR_TYPES = {"Goldene Stunde Morgen", "Goldene Stunde Abend"}
_BLUE_HOUR_TYPES = {"Blaue Stunde Morgen", "Blaue Stunde"}
"""US-132: Blaue-Stunde-Event-Typen, aus denen RED_CLOUDS-Events erzeugt werden
können (Sonne bereits unter dem Horizont) — Pendant zu _GOLDEN_HOUR_TYPES."""


def _cloud_mood_projection_points(e):
    """
    US-131 (Option B, Weg-Gate 2026-07-13): Berechnet die beiden entlang der Sichtachse
    projizierten Punkte, an denen Wolken-/Dunstwerte statt am Fotografen-Standort
    abgefragt werden — Sonnenrichtung (füttert GOLDEN_CLOUDS) und Gegenrichtung/
    Antisolarpunkt (füttert RED_SKY), jeweils CLOUD_MOOD_PROJECTION_DISTANCE_M (30 km)
    hinter dem Motiv (subject_lat/subject_lon als Ursprung, destination_point()
    unverändert aus discover.geometry wiederverwendet).

    Gemeinsamer Helfer für _fetch_weather_and_aerosol() (Cronlauf, _weather_overlay())
    und _weather_overlay_single() (Fast-Path) — beide Pfade rufen exakt diese Funktion
    auf, damit sie für dieselbe Location/denselben Event-Zeitpunkt denselben
    projizierten Punkt berechnen (AK-4/AK-10, TASK-73-Analog, Pre-Mortem Szenario 3).

    Gibt None zurück, wenn das Event kein qualifizierendes Goldene-Stunde-Event ist
    oder subject_lat/subject_lon/subject_azimuth/sunrise_azimuth/sunset_azimuth fehlen
    (AK-6: kein Fehler, die Projektion wird in diesem Fall gar nicht erst berechnet).

    Gibt bei Erfolg zurück: ((sun_dir_lat, sun_dir_lon), (antisolar_dir_lat, antisolar_dir_lon))
    """
    if e.get("event_type") not in _GOLDEN_HOUR_TYPES:
        return None

    subject_lat = e.get("subject_lat")
    subject_lon = e.get("subject_lon")
    subject_az = e.get("subject_azimuth")
    if subject_lat is None or subject_lon is None or subject_az is None:
        return None

    # Sonnen-Azimut: Morgen → sunrise_azimuth, Abend → sunset_azimuth
    if e.get("event_type") == "Goldene Stunde Morgen":
        sun_az = e.get("sunrise_azimuth")
    else:
        sun_az = e.get("sunset_azimuth")
    if sun_az is None:
        return None

    antisolar_az = (sun_az + 180) % 360
    sun_dir_point = destination_point(subject_lat, subject_lon, sun_az, CLOUD_MOOD_PROJECTION_DISTANCE_M)
    antisolar_dir_point = destination_point(subject_lat, subject_lon, antisolar_az, CLOUD_MOOD_PROJECTION_DISTANCE_M)
    return sun_dir_point, antisolar_dir_point


def _lookup_projected_forecasts(e, sun_dir_forecasts, antisolar_dir_forecasts, aerosol_forecasts):
    """
    US-131 (Refactor-Check 2026-07-14): gemeinsamer Helfer für _weather_overlay() und
    _weather_overlay_single() — beide schlugen bislang identisch (Copy-Paste) den
    projizierten Sonnenrichtungs-/Gegenrichtungspunkt eines Events in den bereits über
    _fetch_weather_and_aerosol() abgerufenen Forecast-Dicts nach. Reines Nachschlagen,
    keine Verhaltensänderung (AK-4/AK-10 bleiben durch den gemeinsamen Helfer erhalten).

    Gibt (sun_fc, anti_fc, aero_fc) zurück; alle drei None, wenn das Event kein
    qualifizierendes Goldene-Stunde-Event ist (_cloud_mood_projection_points() gibt
    dann None zurück) oder der jeweilige Fetch fehlgeschlagen ist.
    """
    proj = _cloud_mood_projection_points(e)
    if proj is None:
        return None, None, None
    (sun_lat, sun_lon), (anti_lat, anti_lon) = proj
    sun_key = f"{sun_lat:.3f},{sun_lon:.3f}"
    anti_key = f"{anti_lat:.3f},{anti_lon:.3f}"
    sun_fc = sun_dir_forecasts.get(sun_key)
    anti_fc = antisolar_dir_forecasts.get(anti_key)
    aero_fc = aerosol_forecasts.get(anti_key)
    return sun_fc, anti_fc, aero_fc


def _cloud_mood_inputs(e):
    """
    TASK-74/US-131: Prüft Eligibility eines Events für Cloud-Mood-Generierung (US-109)
    und extrahiert die Eingangswerte für die RED_SKY-Prüfung (GOLDEN_CLOUDS liest seine
    Eingangswerte seit US-131 direkt in _build_golden_clouds_event, s.u.).
    Gibt None zurück, wenn das Event nicht eligible ist (kein Goldene-Stunde-Event,
    kein echtes Wetter-Overlay oder fehlende Wetterdetails).

    US-131 (Option B): liest den entkoppelten, in Gegenrichtung/Antisolarpunkt
    projizierten Wolkenwert (golden_cloud_score_antisolar_dir/cl_antisolar_dir/
    cm_antisolar_dir) statt des bisherigen, am Fotografen-Standort geteilten
    golden_cloud_score/cl/cm. Anders als zuvor wird NICHT mehr auf "gcs is None"
    gegated — schlägt der Fetch am Gegenrichtungspunkt fehl, bleibt
    golden_cloud_score_antisolar_dir None und _build_red_sky_event() gibt dafür
    selbst None zurück (AK-11, kein Absturz).

    Gibt bei Eligibility das Tupel (gcs, wd, cl, cm, aod, sun_az, subject_az) zurück
    — gcs/cl/cm beziehen sich jetzt auf den Antisolar-/Gegenrichtungspunkt (RED_SKY).
    """
    if e.get("event_type") not in _GOLDEN_HOUR_TYPES:
        return None
    if e.get("weather_status") != "ok":
        return None

    wd = e.get("weather_details")
    if not wd:
        return None

    gcs = e.get("golden_cloud_score_antisolar_dir")  # US-131: Gegenrichtung statt Fotografen-Standort
    cl = e.get("cl_antisolar_dir")
    cm = e.get("cm_antisolar_dir")
    aod = wd.get("aerosol_optical_depth")  # US-130/US-131: None wenn nicht verfügbar (AK-5)

    # Sonnen-Azimut: Morgen → sunrise_azimuth, Abend → sunset_azimuth
    if e.get("event_type") == "Goldene Stunde Morgen":
        sun_az = e.get("sunrise_azimuth")
    else:
        sun_az = e.get("sunset_azimuth")

    subject_az = e.get("subject_azimuth")

    return gcs, wd, cl, cm, aod, sun_az, subject_az


def _build_golden_clouds_event(e):
    """
    TASK-74 (aus _generate_cloud_mood_events extrahiert): Baut das GOLDEN_CLOUDS-
    Event-Dict (AK-1, AK-12), oder gibt None zurück wenn die Bedingung nicht erfüllt ist.

    US-131 (Option B, AK-8): nutzt den in Sonnenrichtung projizierten
    golden_cloud_score_sun_dir statt des bisherigen, am Fotografen-Standort geteilten
    golden_cloud_score. Fehlt er (Fetch fehlgeschlagen/nicht berechnet), gibt es analog
    zum bestehenden sun_az/subject_az-Guard kein GOLDEN_CLOUDS-Event (AK-11).
    """
    gcs = e.get("golden_cloud_score_sun_dir")  # US-131: Sonnenrichtung statt Fotografen-Standort
    if e.get("event_type") == "Goldene Stunde Morgen":
        sun_az = e.get("sunrise_azimuth")
    else:
        sun_az = e.get("sunset_azimuth")
    subject_az = e.get("subject_azimuth")

    if gcs is None or sun_az is None or subject_az is None:
        return None
    if not should_generate_golden_clouds_event(gcs, sun_az, subject_az):
        return None

    new_event = _copy.deepcopy(e)
    new_event["id"] = "gc_" + _uuid.uuid4().hex[:12]
    new_event["event_type"] = "Goldene Wolken"
    new_event["title"] = "Goldene Wolken"
    new_event["description"] = (
        "Die Sonne geht in Motivrichtung auf oder unter und trifft auf "
        "Wolkenschichten, die das Licht warm-golden einfärben. "
        "Ideal für dramatische Himmelsstimmungen direkt über dem Motiv."
    )
    new_event["alert_priority"] = 2
    return new_event


def _build_red_sky_event(e, aod, cl, cm, sun_az, subject_az):
    """
    TASK-74 (aus _generate_cloud_mood_events extrahiert): Baut das RED_SKY-Event-Dict
    inkl. US-130-Text-Verzweigung (AK-4, US-113: Sichtachsen-Filter, US-130:
    ODER-Verknüpfung mit Aerosol-/Dunst-Signal) — unabhängig von GOLDEN_CLOUDS.
    Gibt None zurück wenn die Bedingung nicht erfüllt ist.

    US-131 (Option B, AK-9): gcs/cl/cm (via _cloud_mood_inputs übergeben) und aod
    stammen jetzt vom Gegenrichtungs-/Antisolarpunkt (getrennt von der
    GOLDEN_CLOUDS-Sonnenrichtungsprojektion, Entkopplung Pre-Mortem Szenario 2).
    gcs=None (Fetch fehlgeschlagen) → kein RED_SKY-Event (AK-11, kein Absturz — cl/cm
    stammen aus derselben Quelle wie gcs und sind dann ebenfalls None).
    """
    gcs = e.get("golden_cloud_score_antisolar_dir")  # US-131: Gegenrichtung statt Fotografen-Standort
    if gcs is None:
        return None
    if not should_generate_red_sky_event(gcs, cl, cm, sun_az, subject_az, aerosol_optical_depth=aod):
        return None

    new_event = _copy.deepcopy(e)
    new_event["id"] = "rs_" + _uuid.uuid4().hex[:12]
    new_event["event_type"] = "Himmelsröte"
    new_event["title"] = "Himmelsröte"
    # US-130 AK-2: Dunst nur dann als Auslöser benennen, wenn die Wolkenbedingung
    # selbst NICHT ausgereicht hätte (sonst bleibt der bisherige Wolken-Text
    # unverändert — Regression/Rule 3, Wolkenbedingung hat immer Vorrang im Text).
    aerosol_war_ausloeser = (
        aod is not None
        and aod >= RED_SKY_AOD_THRESHOLD
        and (cl + cm) < 60
    )
    if aerosol_war_ausloeser:
        new_event["description"] = (
            "Die Sonne geht auf oder unter, und am Himmel gegenüber der Sonne — in "
            "Motivrichtung — sorgt ein hoher Dunst-/Aerosolanteil in der Atmosphäre "
            "(Gegendämmerung) für eine intensive rot-orange Einfärbung — auch ohne "
            "ausreichende Wolkendecke. Ideal für dramatische Himmelsstimmungen direkt "
            "über dem Motiv."
        )
    else:
        new_event["description"] = (
            "Die Sonne geht auf oder unter, und am Himmel gegenüber der Sonne — in "
            "Motivrichtung — trifft das gestreute Licht (Gegendämmerung) auf tiefe und "
            "mittlere Wolkenschichten, die intensiv rot-orange eingefärbt werden. Ideal "
            "für dramatische Himmelsstimmungen direkt über dem Motiv."
        )
    new_event["alert_priority"] = 2
    return new_event


def _red_clouds_inputs(e):
    """
    US-132: Prüft Eligibility eines Events für RED_CLOUDS-Generierung und
    extrahiert die Eingangswerte. Gibt None zurück, wenn das Event nicht eligible
    ist (kein Blaue-Stunde-Event, kein echtes Wetter-Overlay, fehlende
    Wetterdetails). Pre-Mortem Szenario 3: nutzt bewusst NICHT golden_cloud_score
    (bleibt für "Blaue Stunde" immer None), sondern greift direkt auf
    cloud_cover_high_pct/cloud_cover_low_pct zu.

    Gibt bei Eligibility das Tupel (ch, cl, sun_alt, sun_az, subject_az) zurück.
    """
    if e.get("event_type") not in _BLUE_HOUR_TYPES:
        return None
    if e.get("weather_status") != "ok":
        return None

    wd = e.get("weather_details")
    if not wd:
        return None

    ch = wd.get("cloud_cover_high_pct", 0)
    cl = wd.get("cloud_cover_low_pct", 0)

    # US-132/Pre-Mortem Szenario 2: Sonnenazimut/-höhe kommen aus celestial_azimuth/
    # celestial_altitude (opportunity.py-Ergänzung Blaue-Stunde-Block Morgen+Abend),
    # NICHT aus sunrise_azimuth/sunset_azimuth (das sind GOLDEN_CLOUDS-Felder).
    sun_alt = e.get("celestial_altitude")
    sun_az = e.get("celestial_azimuth")
    subject_az = e.get("subject_azimuth")

    return ch, cl, sun_alt, sun_az, subject_az


def _build_red_clouds_event(e, ch, cl, sun_alt, sun_az, subject_az):
    """
    US-132: Baut das RED_CLOUDS-Event-Dict ("Rote Wolken"), oder gibt None zurück
    wenn die Bedingung nicht erfüllt ist (siehe BACKLOG.md US-132 Rules 1-4).

    Pre-Mortem Szenario 1: sun_altitude wird explizit geprüft (nicht nur über den
    Event-Typ-Namen abgeleitet) — should_generate_red_clouds_event() macht diesen
    Check selbst hart (sun_altitude >= 0 → False), zusätzlich zur Eligibility-Prüfung
    über _BLUE_HOUR_TYPES.
    """
    if sun_alt is None or sun_az is None or subject_az is None:
        return None
    if not should_generate_red_clouds_event(
        sun_altitude=sun_alt, ch=ch, cl=cl, sun_azimuth=sun_az, subject_azimuth=subject_az
    ):
        return None

    new_event = _copy.deepcopy(e)
    new_event["id"] = "rc_" + _uuid.uuid4().hex[:12]
    new_event["event_type"] = "Rote Wolken"
    new_event["title"] = "Rote Wolken"
    new_event["description"] = (
        "Die Sonne steht bereits unter dem Horizont, doch hohe Wolken (Cirrus) in "
        "Motivrichtung werden noch direkt angestrahlt und färben sich kräftig "
        "rot-purpurn. Anders als Himmelsröte (Blick gegenüber der Sonne) liegt der "
        "Blick hier in Sonnenrichtung — wie bei Goldener Stunde, nur nachdem die "
        "Sonne bereits untergegangen ist."
    )
    new_event["alert_priority"] = 2
    return new_event


def _generate_cloud_mood_events(feed_cache):
    """
    US-109/US-132: Erzeugt GOLDEN_CLOUDS-, RED_SKY- und RED_CLOUDS-Events aus
    Goldene-Stunde- bzw. Blaue-Stunde-Events mit echtem Wetter-Overlay
    (weather_status == "ok").

    Gibt ein Tupel zurück:
      - neue_events: Liste neuer Event-Dicts (Goldene Wolken / Himmelsröte /
        Rote Wolken)
      - zu_entfernende_ids: Set von Event-IDs der unterdrückten Goldene-Stunde-Events
        (AK-10: wenn GOLDEN_CLOUDS erzeugt wird, fliegt das Original raus). Das
        "Blaue Stunde"-Original wird bei RED_CLOUDS bewusst NICHT unterdrückt —
        analog zu RED_SKY, das ebenfalls additiv zur Goldene-Stunde-Karte auftritt.
    """
    neue_events = []
    zu_entfernende_ids = set()

    for e in feed_cache:
        inputs = _cloud_mood_inputs(e)
        if inputs is not None:
            gcs, wd, cl, cm, aod, sun_az, subject_az = inputs

            # GOLDEN_CLOUDS prüfen (AK-1, AK-12)
            golden_event = _build_golden_clouds_event(e)
            if golden_event is not None:
                neue_events.append(golden_event)
                # AK-10: Original-Goldene-Stunde-Karte unterdrücken
                zu_entfernende_ids.add(e["id"])

            # RED_SKY prüfen — unabhängig von GOLDEN_CLOUDS
            red_sky_event = _build_red_sky_event(e, aod, cl, cm, sun_az, subject_az)
            if red_sky_event is not None:
                neue_events.append(red_sky_event)
            continue

        # US-132: Blaue-Stunde-Events separat prüfen (eigener Eligibility-Pfad,
        # da golden_cloud_score für diese Events immer None ist, Pre-Mortem Szenario 3)
        red_clouds_inputs = _red_clouds_inputs(e)
        if red_clouds_inputs is None:
            continue
        ch, cl, sun_alt, sun_az, subject_az = red_clouds_inputs
        red_clouds_event = _build_red_clouds_event(e, ch, cl, sun_alt, sun_az, subject_az)
        if red_clouds_event is not None:
            neue_events.append(red_clouds_event)

    return neue_events, zu_entfernende_ids


def _inject_cloud_mood_events() -> None:
    """
    US-109/US-132: Liest _feed_cache, generiert GOLDEN_CLOUDS-/Himmelsröte-/
    RED_CLOUDS-Events und schreibt das Ergebnis zurück in _feed_cache (in-place).
    Entfernt zuvor alle bereits injizierten Cloud-Mood-Events (id-Präfix gc_/rs_/rc_),
    damit wiederholte Wetter-Overlay-Läufe keine Duplikate erzeugen.
    """
    global _feed_cache
    # Alte Cloud-Mood-Events aus vorherigen Wetter-Overlay-Läufen entfernen
    _feed_cache = [
        e for e in _feed_cache
        if not (
            e.get("id", "").startswith("gc_")
            or e.get("id", "").startswith("rs_")
            or e.get("id", "").startswith("rc_")
        )
    ]
    neue_events, zu_entfernende_ids = _generate_cloud_mood_events(_feed_cache)
    if zu_entfernende_ids:
        _feed_cache = [e for e in _feed_cache if e["id"] not in zu_entfernende_ids]
    _feed_cache.extend(neue_events)
    if neue_events:
        logger.info(
            "US-109 Cloud-Mood: %d neue Events erzeugt, %d Goldene-Stunde-Events unterdrückt",
            len(neue_events), len(zu_entfernende_ids),
        )


WEATHER_API_MAX_CONCURRENT_REQUESTS = 5
"""
US-131 Nachtrag (Weg-Gate 2026-07-13, gemessener Befund): Ein einzelner
/weather-refresh-Lauf auf dem lokalen Dev-Server erzeugte 339 parallele Requests an
api.open-meteo.com/v1/forecast, von denen 106 (~31%) mit HTTP 429 (Too Many Requests)
abgelehnt wurden — exakt das im Pre-Mortem (Szenario 4 "Netzwerk-Explosion bei vollem
Umfang") vorhergesagte Risiko, weil Option B die externen API-Aufrufe pro Location auf
bis zu 8 erhöht (Wetter am Fotografen-Standort + bis zu drei weitere Wetter-/
Aerosol-Abfragen pro qualifizierendem Goldene-Stunde-Event).

Begrenzt die Anzahl GLEICHZEITIG tatsächlich laufender Requests an fetch_weather_forecast()/
fetch_aerosol_forecast() über ein asyncio.Semaphore (s. u.) — asyncio.gather() plant
weiterhin ALLE Calls ein, aber es laufen nie mehr als dieser Wert parallel. Konservativ
gewählter, konkreter Wert 5 statt eines vermuteten exakten Open-Meteo-Limits (keine
verifizierbare Rate-Limit-Doku ohne Internetzugriff verfügbar) — deutlich unter der
Größenordnung, die die 31%-Fehlerquote produziert hat, und leicht nach oben/unten
anpassbar, falls der Live-Smoke-Test (Stephan, gegen die echte API) noch Anpassungsbedarf
zeigt. Gilt für BEIDE Pfade (Cronlauf _weather_overlay() UND Fast-Path
_weather_overlay_single()), da beide ausschließlich über _fetch_weather_and_aerosol()
laufen (AK-4/AK-10-Konsistenzmuster).

US-131 2. Nachtrag (2. Live-Messung, gemessener Befund): Mit der Semaphore allein
(WEATHER_API_MAX_CONCURRENT_REQUESTS=5, aber ohne zeitliches Pacing) blieb die
429-Quote bei einem zweiten realen Lauf gegen api.open-meteo.com weiterhin hoch:
1186 Requests, davon 253 mit HTTP 429 (~21%) — Verbesserung gegenüber den 31% ohne
jede Drosselung, aber nicht ausreichend. Erklärung: Die Semaphore begrenzt nur, WIE
VIELE Requests gleichzeitig laufen, nicht WIE SCHNELL ein frei gewordener Slot sofort
wieder einen neuen Request abfeuert — bei einem kurzen Zeitfenster-Limit (z. B. pro
Sekunde) reicht reine Nebenläufigkeits-Begrenzung ohne Pacing nicht. Siehe
WEATHER_API_REQUEST_PACING_SECONDS für das ergänzte zeitliche Pacing.
"""


WEATHER_API_REQUEST_PACING_SECONDS = 0.15
"""
US-131 2. Nachtrag: Zusätzlich zur Nebenläufigkeits-Begrenzung (s.
WEATHER_API_MAX_CONCURRENT_REQUESTS) erzwingt dieser Wert einen Mindestabstand
zwischen zwei tatsächlichen API-Calls in DEMSELBEN Semaphore-Slot: Nach jedem
Abschluss (Erfolg ODER Fehler) von fetch_weather_forecast()/fetch_aerosol_forecast()
wartet _run_one_weather_fetch() diese Zeit, BEVOR die Semaphore wieder freigegeben wird — so kann
ein frei gewordener Slot nicht sofort wieder feuern.

Konservativer Startwert (KEIN verifiziertes exaktes Open-Meteo-Rate-Limit, da ohne
Internetzugriff aus der Sandbox nicht nachschlagbar) — 0.15s, begründet über
Überschlagsrechnung: Bei WEATHER_API_MAX_CONCURRENT_REQUESTS=5 parallelen Slots liegt
der durch das Pacing allein gedeckelte Maximaldurchsatz bei
5 Slots × (1 Request / 0.15s) = ca. 33,3 Requests/Sekunde. Das ist deutlich unter der
Größenordnung, die zur 21%-Fehlerquote im 2. Live-Lauf geführt hat, verlangsamt den
Wetter-Overlay-Lauf (2869 Events im letzten Lauf) aber nicht übermäßig, da die Pacing-
Wartezeit parallel über alle 5 Slots anfällt statt seriell über alle Requests. Muss
ggf. nach dem 3. Live-Smoke-Test (Stephan, gegen die echte API) noch angepasst werden.
"""


async def _fetch_weather_and_aerosol(near_events) -> tuple[dict, dict, dict, dict, list, list, list, list]:
    """
    TASK-74 (aus _weather_overlay extrahiert): Holt für jede unique Location aus
    near_events Wetter- und Aerosol-Forecast parallel via asyncio.gather.

    US-130 (Pre-Mortem Szenario 4): Wetter- und Aerosol-Abruf parallelisieren statt
    seriell, damit der zusätzliche Aerosol-Call nicht die Latenz des ohnehin
    migränosen Wetter-Overlay-Pfads verdoppelt.

    US-131 (Option B, Weg-Gate 2026-07-13): Zusätzlich zum bestehenden, am
    Fotografen-Standort verankerten Wetter-Abruf (unverändert, füttert
    weather_score/weather_details, AK-2) werden pro qualifizierendem
    Goldene-Stunde-Event (_cloud_mood_projection_points(), gemeinsamer Helfer mit
    _weather_overlay_single() für AK-4/AK-10-Konsistenz) bis zu drei weitere Abfragen
    an den beiden projizierten Punkten eingeplant: Wetter (cl/cm/ch) in Sonnenrichtung
    (füttert GOLDEN_CLOUDS) und Wetter + Aerosol/Dunst in Gegenrichtung/Antisolarpunkt
    (füttert RED_SKY). Der bisher am Fotografen-Standort abgefragte Dunstwert (US-130)
    entfällt — die Aerosolabfrage läuft seit US-131 ausschließlich am
    Gegenrichtungspunkt. Alle Abfragen laufen in EINEM gemeinsamen asyncio.gather,
    dedupliziert nach der jeweils abgefragten (gerundeten) Koordinate.

    US-131 Nachtrag (gemessener 429-Befund, s. WEATHER_API_MAX_CONCURRENT_REQUESTS):
    asyncio.gather() plant weiterhin ALLE Calls gleichzeitig ein, aber ein
    asyncio.Semaphore begrenzt, wie viele davon tatsächlich parallel gegen die externe
    API laufen — drosselt die externen HTTP-Requests, ohne die Gesamtlogik/Reihenfolge
    zu ändern.

    Gibt zurück: (loc_forecasts, aerosol_forecasts, sun_dir_forecasts,
    antisolar_dir_forecasts, failed_locations, failed_aerosol_locations,
    failed_sun_dir_locations, failed_antisolar_dir_locations)
    """
    tasks_meta = _plan_weather_fetch_tasks(near_events)

    # US-131 Nachtrag: Drosselt die Anzahl GLEICHZEITIG laufender externer Requests
    # (s. WEATHER_API_MAX_CONCURRENT_REQUESTS) — asyncio.gather() plant weiterhin
    # ALLE Calls ein, das Semaphore lässt aber nie mehr als die konfigurierte
    # Obergrenze tatsächlich parallel gegen die Open-Meteo-API laufen. Zusätzliches
    # zeitliches Pacing (s. _run_one_weather_fetch()) erzwingt einen Mindestabstand
    # zwischen zwei Calls in DEMSELBEN Slot (WEATHER_API_REQUEST_PACING_SECONDS).
    semaphore = asyncio.Semaphore(WEATHER_API_MAX_CONCURRENT_REQUESTS)

    results = await asyncio.gather(
        *[_run_one_weather_fetch(kind, lat, lon, semaphore) for (kind, _key, lat, lon, _name) in tasks_meta],
        return_exceptions=True,
    )

    return _collect_weather_fetch_results(tasks_meta, results)


def _plan_weather_fetch_tasks(near_events) -> list:
    """
    TASK-76 (aus _fetch_weather_and_aerosol extrahiert): Plant die abzurufenden
    Wetter-/Aerosol-/Richtungs-Tasks für `near_events`, dedupliziert pro
    Art+Koordinate.

    Gibt tasks_meta zurück: Liste aus (kind, key, lat, lon, location_name) je
    geplantem Abruf.
    """
    tasks_meta: list = []
    seen: dict = {"weather": set(), "aerosol": set(), "sun_dir": set(), "antisolar_dir": set()}

    for e in near_events:
        obs_key = f"{e['observer_lat']:.3f},{e['observer_lon']:.3f}"
        if obs_key not in seen["weather"]:
            seen["weather"].add(obs_key)
            tasks_meta.append(("weather", obs_key, e["observer_lat"], e["observer_lon"], e["location_name"]))

        proj = _cloud_mood_projection_points(e)
        if proj is None:
            continue
        (sun_lat, sun_lon), (anti_lat, anti_lon) = proj
        sun_key = f"{sun_lat:.3f},{sun_lon:.3f}"
        anti_key = f"{anti_lat:.3f},{anti_lon:.3f}"
        if sun_key not in seen["sun_dir"]:
            seen["sun_dir"].add(sun_key)
            tasks_meta.append(("sun_dir", sun_key, sun_lat, sun_lon, e["location_name"]))
        if anti_key not in seen["antisolar_dir"]:
            seen["antisolar_dir"].add(anti_key)
            tasks_meta.append(("antisolar_dir", anti_key, anti_lat, anti_lon, e["location_name"]))
        if anti_key not in seen["aerosol"]:
            seen["aerosol"].add(anti_key)
            tasks_meta.append(("aerosol", anti_key, anti_lat, anti_lon, e["location_name"]))

    return tasks_meta


async def _run_one_weather_fetch(kind: str, lat: float, lon: float, semaphore: "asyncio.Semaphore"):
    """
    TASK-76 (aus _fetch_weather_and_aerosol._run_one extrahiert): Führt EINEN
    Wetter-/Aerosol-Fetch gedrosselt über `semaphore` aus (explizit als Parameter,
    nicht als Closure — Pre-Mortem TASK-76: die try/finally-Pacing-Struktur bleibt
    dabei unverändert 1:1 erhalten).

    US-131 2. Nachtrag: Der `finally`-Block pausiert IMMER um
    WEATHER_API_REQUEST_PACING_SECONDS — bei Erfolg UND bei Fehlschlag — bevor die
    Semaphore wieder freigegeben wird, damit ein frei gewordener Slot nicht sofort
    wieder feuert. Ein fehlgeschlagener Call zählt bei der externen API ebenfalls
    als Request.
    """
    async with semaphore:
        try:
            if kind == "aerosol":
                return await fetch_aerosol_forecast(lat, lon, days=7)
            return await fetch_weather_forecast(lat, lon, days=7)
        finally:
            await asyncio.sleep(WEATHER_API_REQUEST_PACING_SECONDS)


def _collect_weather_fetch_results(tasks_meta, results) -> tuple:
    """
    TASK-76 (aus _fetch_weather_and_aerosol extrahiert): Ordnet die
    asyncio.gather-Ergebnisse `results` anhand von `tasks_meta` (per zip, gleiche
    Reihenfolge/Liste wie beim gather-Aufruf — Pre-Mortem TASK-76: sonst werden
    Ergebnisse falschen Locations/Kinds zugeordnet) den passenden
    Forecast-Dicts/Fehl-Listen zu.

    Gibt zurück: (loc_forecasts, aerosol_forecasts, sun_dir_forecasts,
    antisolar_dir_forecasts, failed_locations, failed_aerosol_locations,
    failed_sun_dir_locations, failed_antisolar_dir_locations)
    """
    loc_forecasts: dict = {}  # Fotografen-Standort-Wetter
    aerosol_forecasts: dict = {}  # US-130/US-131: am Gegenrichtungs-/Antisolarpunkt
    sun_dir_forecasts: dict = {}  # US-131: Wetter in Sonnenrichtung (GOLDEN_CLOUDS)
    antisolar_dir_forecasts: dict = {}  # US-131: Wetter in Gegenrichtung (RED_SKY)
    failed_locations: list = []  # BUG-77: fehlgeschlagener Wetter-Abruf
    failed_aerosol_locations: list = []  # US-130: fehlgeschlagener Aerosol-Abruf
    failed_sun_dir_locations: list = []  # US-131: fehlgeschlagener Wolken-Abruf Sonnenrichtung
    failed_antisolar_dir_locations: list = []  # US-131: fehlgeschlagener Wolken-Abruf Gegenrichtung

    for (kind, key, _lat, _lon, name), result in zip(tasks_meta, results):
        if isinstance(result, Exception):
            logger.warning("  %s für %s fehlgeschlagen: %s", kind, name, result)
            if kind == "weather":
                failed_locations.append(name)
            elif kind == "aerosol":
                # US-130 AK-5: Ein fehlgeschlagener Aerosol-Abruf ist NICHT fatal — RED_SKY
                # fällt für diese Location sauber auf den reinen Wolken-Check zurück.
                failed_aerosol_locations.append(name)
            elif kind == "sun_dir":
                # US-131 AK-11: Fehlgeschlagener Wolken-Abruf in Sonnenrichtung ist NICHT
                # fatal — GOLDEN_CLOUDS gilt für dieses Event als "Signal nicht verfügbar",
                # kein Fallback auf den Fotografen-Standort-Wert.
                failed_sun_dir_locations.append(name)
            else:  # antisolar_dir
                failed_antisolar_dir_locations.append(name)
            continue

        if kind == "weather":
            loc_forecasts[key] = result
            logger.info("  Wetter für %s: OK", name)
        elif kind == "aerosol":
            aerosol_forecasts[key] = result
        elif kind == "sun_dir":
            sun_dir_forecasts[key] = result
        else:  # antisolar_dir
            antisolar_dir_forecasts[key] = result

    return (
        loc_forecasts, aerosol_forecasts, sun_dir_forecasts, antisolar_dir_forecasts,
        failed_locations, failed_aerosol_locations, failed_sun_dir_locations, failed_antisolar_dir_locations,
    )


def _build_weather_error_message(
    failed_locations, failed_aerosol_locations,
    failed_sun_dir_locations=None, failed_antisolar_dir_locations=None,
) -> str | None:
    """
    TASK-74 (aus _weather_overlay extrahiert): Baut die BUG-77/US-130/US-131-Fehlermeldung
    für Teil-/Totalausfall des Wetter-, Aerosol- und/oder Wolken-Projektions-Abrufs.
    Gibt None zurück, wenn alle Listen leer sind (kein Fehler).

    US-131: failed_sun_dir_locations/failed_antisolar_dir_locations sind optional
    (Default None → wie leere Liste behandelt), damit bestehende Aufrufer mit der
    alten 2-Parameter-Signatur (BUG-77/US-130) unverändert weiterlaufen.
    """
    failed_sun_dir_locations = failed_sun_dir_locations or []
    failed_antisolar_dir_locations = failed_antisolar_dir_locations or []
    if (
        not failed_locations
        and not failed_aerosol_locations
        and not failed_sun_dir_locations
        and not failed_antisolar_dir_locations
    ):
        return None
    parts = []
    if failed_locations:
        names = ", ".join(failed_locations[:5])
        if len(failed_locations) > 5:
            names += f" …und {len(failed_locations) - 5} weitere"
        parts.append(f"Wetterdaten fehlgeschlagen für: {names}")
    if failed_aerosol_locations:
        names = ", ".join(failed_aerosol_locations[:5])
        if len(failed_aerosol_locations) > 5:
            names += f" …und {len(failed_aerosol_locations) - 5} weitere"
        parts.append(f"Aerosoldaten fehlgeschlagen für: {names}")
    if failed_sun_dir_locations:
        names = ", ".join(failed_sun_dir_locations[:5])
        if len(failed_sun_dir_locations) > 5:
            names += f" …und {len(failed_sun_dir_locations) - 5} weitere"
        parts.append(f"Wolkenwert Sonnenrichtung fehlgeschlagen für: {names}")
    if failed_antisolar_dir_locations:
        names = ", ".join(failed_antisolar_dir_locations[:5])
        if len(failed_antisolar_dir_locations) > 5:
            names += f" …und {len(failed_antisolar_dir_locations) - 5} weitere"
        parts.append(f"Wolkenwert Gegenrichtung fehlgeschlagen für: {names}")
    return "Wetter: Fehler — " + "; ".join(parts)


async def _weather_overlay() -> None:
    """
    Holt Wetter-Daten für Events in den nächsten 3 Tagen und
    aktualisiert weather_score + overall_score in _feed_cache.
    Schnell: nur wenige Locations, nur 7-Tage-Forecast.
    """
    global _weather_updated_at

    t0 = _job_start("weather")
    if not _feed_cache:
        _job_done("weather", t0)
        return

    now_utc = datetime.now(timezone.utc)
    cutoff  = now_utc + timedelta(days=3)

    # Relevante Events: nächste 3 Tage
    near_events = [
        e for e in _feed_cache
        if datetime.fromisoformat(e["shoot_time"]) <= cutoff
        and datetime.fromisoformat(e["shoot_time"]) >= now_utc - timedelta(hours=1)
    ]

    if not near_events:
        logger.info("Wetter-Overlay: keine Events in T+3, übersprungen")
        _weather_updated_at = now_utc
        _job_done("weather", t0)
        return

    (
        loc_forecasts, aerosol_forecasts, sun_dir_forecasts, antisolar_dir_forecasts,
        failed_locations, failed_aerosol_locations, failed_sun_dir_locations, failed_antisolar_dir_locations,
    ) = await _fetch_weather_and_aerosol(near_events)
    # Anzahl unique Locations: jede unique Location landet entweder in loc_forecasts
    # (Wetter-Abruf erfolgreich) oder in failed_locations (fehlgeschlagen) — disjunkt.
    unique_location_count = len(loc_forecasts) + len(failed_locations)

    # Scores in _feed_cache aktualisieren
    updated = 0
    for e in _feed_cache:
        key = f"{e['observer_lat']:.3f},{e['observer_lon']:.3f}"
        # US-131: pro Event den projizierten Sonnenrichtungs-/Gegenrichtungspunkt
        # nachschlagen (gemeinsamer Helfer mit _weather_overlay_single(), AK-4/AK-10;
        # Refactor-Check 2026-07-14: vorher hier dupliziert).
        sun_fc, anti_fc, aero_fc = _lookup_projected_forecasts(
            e, sun_dir_forecasts, antisolar_dir_forecasts, aerosol_forecasts
        )
        if _apply_weather_to_event(e, loc_forecasts.get(key), now_utc, cutoff, aero_fc, sun_fc, anti_fc):
            updated += 1

    # US-109: GOLDEN_CLOUDS- und Himmelsröte-Events erzeugen
    _inject_cloud_mood_events()

    _weather_updated_at = now_utc
    logger.info("Wetter-Overlay: %d Events aktualisiert (%d unique Locations)", updated, unique_location_count)

    # BUG-77: Teil- oder Totalausfall des Wetter-Abrufs sichtbar machen, statt
    # unbedingt "done" zu melden — bestehenden Statuswert "error" wiederverwenden.
    # US-130/US-131: Aerosol- und Wolken-Projektions-Ausfälle laufen über denselben
    # Sichtbarkeits-Mechanismus mit, damit ein Ausfall der Wetter-/Air-Quality-API an
    # den projizierten Punkten nicht denselben stillen Fehler reproduziert, den BUG-77
    # für den Wetter-Abruf behoben hat.
    error_msg = _build_weather_error_message(
        failed_locations, failed_aerosol_locations, failed_sun_dir_locations, failed_antisolar_dir_locations,
    )
    if error_msg is not None:
        _job_error("weather", t0, error_msg)
    else:
        _job_done("weather", t0)


async def _weather_overlay_single(loc_id: str) -> bool:
    """
    US-106 Teil 1: Gezieltes Wetter-Nachladen für GENAU EINE Location.
    Holt den 7-Tage-Forecast für die Koordinaten dieser Location und spielt das
    Wetter nur auf deren Feed-Events auf (alle anderen Locations unberührt).
    So steht das Wetter Sekunden nach einer Standort-Änderung, ohne einen teuren
    Voll-Overlay über alle Locations und ohne doppelte Fremd-Fetches.
    TASK-73: holt den Aerosol-Forecast parallel dazu ab; schlägt nur der
    Aerosol-Abruf fehl, bleibt das Wetter-Ergebnis trotzdem gültig.

    US-131 (Option B, AK-4/AK-10): nutzt seit dieser Änderung denselben
    _fetch_weather_and_aerosol()-Helfer wie der Cronlauf (_weather_overlay()) für
    Wetter-, Aerosol- UND die beiden neuen Wolken-Projektions-Abrufe — garantiert,
    dass Fast-Path und Cronlauf für dieselbe Location/denselben Event-Zeitpunkt
    identische projizierte Punkte und Ergebnisse liefern (kein TASK-73-artiges
    Auseinanderlaufen).

    Gibt True zurück, wenn für die Location nichts mehr offen ist (alle ihre
    Events in T+3 haben echtes Wetter ODER es gibt keine Events in T+3).
    """
    own_events = [e for e in _feed_cache if e.get("location_id") == loc_id]
    if not own_events:
        # Keine Events → es gibt nichts nachzuladen; Location gilt als fertig.
        return True

    now_utc = datetime.now(timezone.utc)
    cutoff  = now_utc + timedelta(days=3)

    near_events = [
        e for e in own_events
        if now_utc - timedelta(hours=1) <= datetime.fromisoformat(e["shoot_time"]) <= cutoff
    ]

    # Events außerhalb T+3 sauber als "noch kein Wetter" markieren. Wir nutzen den
    # DRY-Helfer (forecast=None): für Out-of-Window-Events setzt er exakt
    # weather_score=0 / overall_score=astronomy_score / weather_status="none" und
    # kehrt sofort zurück, ohne das (hier noch nicht geladene) Wetter zu brauchen.
    for e in own_events:
        shoot_dt = datetime.fromisoformat(e["shoot_time"])
        if shoot_dt > cutoff or shoot_dt < now_utc - timedelta(hours=1):
            _apply_weather_to_event(e, None, now_utc, cutoff)

    if not near_events:
        # Alle Events liegen außerhalb des Forecast-Fensters → fertig, kein Fetch.
        return True

    (
        loc_forecasts, aerosol_forecasts, sun_dir_forecasts, antisolar_dir_forecasts,
        failed_locations, _failed_aerosol_locations, _failed_sun_dir_locations, _failed_antisolar_dir_locations,
    ) = await _fetch_weather_and_aerosol(near_events)

    ref = near_events[0]
    ref_key = f"{ref['observer_lat']:.3f},{ref['observer_lon']:.3f}"
    fc = loc_forecasts.get(ref_key)
    if fc is None:
        logger.warning("US-106 Single-Wetter für %s fehlgeschlagen: %s", loc_id, failed_locations)
        return False

    all_ok = True
    for e in near_events:
        # US-131: pro Event den projizierten Sonnenrichtungs-/Gegenrichtungspunkt
        # nachschlagen (gemeinsamer Helfer mit _weather_overlay(), AK-4/AK-10;
        # Refactor-Check 2026-07-14: vorher hier dupliziert).
        sun_fc, anti_fc, aero_fc = _lookup_projected_forecasts(
            e, sun_dir_forecasts, antisolar_dir_forecasts, aerosol_forecasts
        )
        if not _apply_weather_to_event(e, fc, now_utc, cutoff, aero_fc, sun_fc, anti_fc):
            all_ok = False
    logger.info("US-106 Single-Wetter für %s: %d/%d Events in T+3 aktualisiert",
                loc_id, sum(1 for e in near_events if e.get("weather_status") == "ok"), len(near_events))
    # US-109: Cloud-Mood-Events nach Einzel-Wetter ebenfalls aktualisieren
    _inject_cloud_mood_events()
    return all_ok


async def _build_weather_map() -> None:
    """US-112: Baut das Wetter-Karten-Overlay (weicher Verlauf) im Hintergrund.

    Lädt DWD ICON-D2 (0–48 h) + ICON-EU (48–72 h) + MET Norway (Norwegen),
    interpoliert je Stunde zu einem PNG (Wolken + Niederschlag) und legt alles im
    Prozess-Cache ab. Robust: fällt eine Quelle aus, bleiben die anderen gültig.
    Wird nie aus dem Request-Pfad direkt awaited (kann ~Sekunden bis Minuten dauern).
    """
    global _weather_map_cache, _weather_map_png, _weather_map_updated_at, _weather_map_building

    if _weather_map_building:
        return
    _weather_map_building = True
    t0 = _job_start("weather-map")
    try:
        ua = "FotoAlert/%s (https://github.com/  kontakt: stephanschumann@me.com)" % app.version
        async with httpx.AsyncClient(follow_redirects=True) as client:
            overlay = await weather_grib.build_weather_overlay(client, n_hours=72, user_agent=ua)

        # PNGs je Feld/Stunde rendern (CPU-lastig → in Thread auslagern)
        cloud_pngs = await asyncio.to_thread(weather_grib.render_all_pngs, overlay, "cloud")
        precip_pngs = await asyncio.to_thread(weather_grib.render_all_pngs, overlay, "precip")

        _weather_map_png = {"cloud": cloud_pngs, "precip": precip_pngs}
        _weather_map_cache = {
            "bounds": weather_grib.overlay_bounds(),
            "hourly_times": overlay["hourly_times"],
            "sources": overlay["sources"],
            "n_points": overlay["n_points"],
            "attribution": "Daten: DWD · MET Norway (CC BY 4.0)",
            "attribution_url": "https://www.met.no/en/free-meteorological-data",
        }
        _weather_map_updated_at = datetime.now(timezone.utc)
        logger.info("US-112 Wetter-Karte gebaut: %d Stützpunkte, Quellen=%s",
                    overlay["n_points"], overlay["sources"])
        _job_done("weather-map", t0)
    except Exception as exc:
        logger.warning("US-112 Wetter-Karten-Bau fehlgeschlagen: %s", exc)
        _job_done("weather-map", t0)
    finally:
        _weather_map_building = False


def _finalize_pending(loc_id: str) -> None:
    """
    US-106 Teil 3: Eine Location erst dann aus _recompute_pending freigeben, wenn
    Feed UND Wetter für sie stehen. Wird nach dem gezielten Wetter-Nachladen
    aufgerufen. Damit verschwindet das "wird aktualisiert"-Banner im Frontend
    erst, wenn die Location wirklich vollständig fertig ist.
    """
    _recompute_pending.discard(loc_id)
    logger.info("US-106 Pending freigegeben (Feed+Wetter fertig): %s", loc_id)


# ---------------------------------------------------------------------------
# Vorberechnung (precompute.py als Subprocess)
# ---------------------------------------------------------------------------

async def _run_precompute(mode: str = "full") -> None:
    """
    Startet precompute.py als Subprocess (ohne Event-Loop-Blocking).
    mode: "full" (feed+calendar) | "feed" (nur 14-Tage) | "calendar" (nur Jahreskalender)
    Nach Abschluss werden die JSON-Caches neu geladen.
    """
    global _precompute_running
    if _precompute_running:
        logger.info("Vorberechnung läuft bereits, übersprungen")
        return

    # Job-Keys für Status-Tracking
    job_keys = ["feed", "calendar"] if mode == "full" else [mode]
    t0s = {j: _job_start(j) for j in job_keys}

    _precompute_running = True
    backend_dir = Path(__file__).parent
    logger.info("Starte Vorberechnung (precompute.py, mode=%s)...", mode)

    args = [sys.executable, str(backend_dir / "precompute.py")]
    if mode == "feed":
        args.append("--feed-only")
    elif mode == "calendar":
        args.append("--calendar-only")

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(backend_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        if stdout:
            for line in stdout.decode(errors="replace").splitlines():
                logger.info("  [precompute] %s", line)
        if proc.returncode == 0:
            logger.info("Vorberechnung abgeschlossen (mode=%s). Lade Caches neu...", mode)
            _load_elevation_cache()
            _load_caches()
            if mode in ("full", "feed"):
                await _weather_overlay()
            for j, t0 in t0s.items():
                _job_done(j, t0)
        else:
            msg = f"exit {proc.returncode}"
            logger.error("Vorberechnung fehlgeschlagen (%s)", msg)
            for j, t0 in t0s.items():
                _job_error(j, t0, msg)
    except Exception as e:
        logger.error("Fehler beim Starten von precompute.py: %s", e)
        for j, t0 in t0s.items():
            _job_error(j, t0, str(e))
    finally:
        _precompute_running = False
        # US-106 Teil 3: Offene Einzel-Neuberechnungen, die während dieses
        # Großlaufs per Single-Flight-Guard übersprungen wurden, jetzt am
        # Lauf-Ende nachholen — keine still verlorene Änderung.
        await _drain_recompute_pending()


async def _drain_recompute_pending() -> None:
    """
    US-106 Teil 3: Arbeitet offene _recompute_pending-IDs sequenziell ab.
    Wird am Ende jedes großen Laufs UND am Ende eines Einzel-Laufs aufgerufen.
    Single-Flight: läuft gerade schon eine Berechnung (z.B. ein neuer Großlauf
    startete), brechen wir ab — der jeweils laufende Prozess holt die offenen
    IDs an seinem eigenen Lauf-Ende nach. Schutz gegen Endlos-Rekursion durch
    das _precompute_running-Gate in _run_precompute_single (übersprungene IDs
    bleiben pending und werden beim nächsten Drain erneut versucht).
    """
    if _NO_BACKGROUND:
        return
    # Snapshot, damit parallele Änderungen die Iteration nicht stören.
    for loc_id in list(_recompute_pending):
        if _precompute_running:
            logger.info("US-106 Drain pausiert – Berechnung läuft bereits; offene IDs: %s",
                        list(_recompute_pending))
            return
        if loc_id not in _recompute_pending:
            continue  # zwischenzeitlich fertig geworden
        logger.info("US-106 Nachhol-Lauf für ausstehende Location: %s", loc_id)
        await _run_precompute_single(loc_id, _allow_drain=False)


# ---------------------------------------------------------------------------
# TASK-48 — Nächtlicher QA-Lauf: Änderungen erkennen + Auto-Verbesserungen anstoßen
# ---------------------------------------------------------------------------

def _qa_geo_hash_for(loc) -> str:
    """Aktueller Geo-Fingerabdruck einer Location aus ihren 7 Geo-Kernfeldern.

    Identische Feldauswahl wie compute_geo_hash (store.py). getattr mit Default
    None, damit fehlende Felder (z.B. ältere Custom-Locations) nicht crashen.
    """
    return compute_geo_hash(
        getattr(loc, "observer_lat", None),
        getattr(loc, "observer_lon", None),
        getattr(loc, "subject_lat", None),
        getattr(loc, "subject_lon", None),
        getattr(loc, "subject_height_m", None),
        getattr(loc, "subject_width_m", None),
        getattr(loc, "distance_m", None),
    )


def _qa_select_due(locations, store) -> list:
    """Wählt die Spots aus, die einen QA-Lauf brauchen (Change-Detection).

    Ein Spot fällt an, wenn er noch nie geprüft wurde (kein QA-State bzw. kein
    gespeicherter geo_hash) ODER wenn sein aktueller Geo-Hash vom gespeicherten
    abweicht. Unveränderte, bereits geprüfte Spots werden übersprungen.

    Rückgabe: Liste von (loc, current_hash)-Tupeln.
    """
    due = []
    for loc in locations:
        current = _qa_geo_hash_for(loc)
        try:
            state = store.get_qa_state(loc.id)
        except Exception as exc:
            logger.warning("QA-State für %s nicht lesbar (%s) – Spot fällt an", loc.id, exc)
            state = None
        stored = state.get("geo_hash") if state else None
        if stored is None or stored != current:
            due.append((loc, current))
    return due


def _qa_improve_one(loc, store) -> bool:
    """Stößt die fertigen Auto-Verbesserungen für GENAU EINEN Spot an (synchron).

    Wird über asyncio.to_thread aus dem Job aufgerufen, damit die (potenziell
    blockierende) Rechen-/Netzarbeit nicht im Event-Loop läuft.

    Stößt Azimut (TASK-45) + Brennweite (TASK-47) + Beschreibung (TASK-46) an. Alle respektieren ihre
    eigenen Locks und werfen nie aus reinem "nichts zu tun"-Grund (Lock gesetzt,
    keine Daten, bereits kuratiert) — das gilt weiterhin trotzdem als geprüft.

    TASK-78 (Option B): Ein einzelner Teilschritt kann trotzdem an einem echten
    Datenbank-Fehler scheitern (Exception aus store.set_qa_values()). Damit ein
    bereits erfolgreich geschriebener Teilwert eines anderen Schritts nie ohne
    zugehörigen Prüf-Eintrag zurückbleibt (verwaiste location_qa_values-Zeile),
    gilt: Der Lauf für diesen Ort gilt als "abzuschließen" (Prüf-Eintrag setzen),
    sobald mindestens ein Teilwert tatsächlich geschrieben wurde oder gar kein
    Teilschritt einen echten Fehler hatte. Nur wenn KEIN einziger Wert geschrieben
    wurde UND mindestens ein Teilschritt an einer Exception gescheitert ist,
    bleibt der Fortschritt aus — der Ort bleibt vollständig unverändert und fällt
    beim nächsten Lauf erneut an (Regel 2 im Ticket). Die Beschreibungs-Funktion
    fängt Exceptions bereits intern vollständig ab (gibt None zurück, wirft nie);
    sie kann also nie selbst als "gescheitert" gezählt werden — nur Azimut und
    Brennweite können hier eine echte Exception auslösen.

    Rückgabe: True, wenn der Prüf-Eintrag für den Ort gesetzt werden soll,
    False wenn der Ort komplett unverändert bleiben und erneut anfallen soll.
    """
    azimuth_ok = True
    focal_ok = True
    wrote_value = False
    try:
        azimuth_result = qa_azimuth.update_location_azimuth(
            store, loc.id,
            getattr(loc, "observer_lat", None),
            getattr(loc, "observer_lon", None),
            getattr(loc, "subject_lat", None),
            getattr(loc, "subject_lon", None),
        )
        if azimuth_result is not None:
            wrote_value = True
    except Exception as exc:
        logger.warning("QA-Azimut für %s fehlgeschlagen: %s", loc.id, exc)
        azimuth_ok = False
    try:
        focal_result = qa_focal.update_location_focal(
            store, loc.id,
            getattr(loc, "subject_height_m", None),
            getattr(loc, "distance_m", None),
        )
        if focal_result is not None:
            wrote_value = True
    except Exception as exc:
        logger.warning("QA-Brennweite für %s fehlgeschlagen: %s", loc.id, exc)
        focal_ok = False
    try:
        result = qa_description.update_location_description(
            store, loc.id,
            getattr(loc, "name", "") or "",
            getattr(loc, "subject_name", "") or "",
            getattr(loc, "category", "") or "",
            getattr(loc, "observer_lat", None),
            getattr(loc, "observer_lon", None),
        )
        if result is not None:
            wrote_value = True
            logger.info("QA-Beschreibung für %s erzeugt", loc.id)
    except Exception as exc:
        # Praktisch unerreichbar (update_location_description faengt intern
        # bereits alles ab) — als Sicherheitsnetz dennoch abgesichert.
        logger.warning("QA-Beschreibung für %s fehlgeschlagen: %s", loc.id, exc)
    return wrote_value or (azimuth_ok and focal_ok)


async def _run_qa_pass() -> Optional[dict]:
    """TASK-48: Nächtlicher QA-Lauf.

    Verbessert nur die Spots, deren Geo-Fingerabdruck sich geändert hat oder die
    noch nie geprüft wurden (Change-Detection über persistierten Geo-Hash).
    Schwere Arbeit pro Spot wird via asyncio.to_thread aus dem Event-Loop
    ausgelagert; zwischen den Spots eine kurze Pause (Drosselung externer
    Dienste). Single-Flight + Respekt vor laufendem Recompute.

    Nach einem abgeschlossenen Spot: qa_checked_at + geo_hash fortschreiben,
    sobald _qa_improve_one() True liefert — das ist laut TASK-78 (Option B)
    bereits der Fall, wenn mindestens ein Teilwert geschrieben wurde, auch wenn
    ein anderer Teilschritt an einem DB-Fehler gescheitert ist (kein Wert bleibt
    ohne Prüf-Eintrag zurück). Nur wenn gar kein Wert geschrieben wurde UND
    mindestens ein Teilschritt echt fehlgeschlagen ist, bleibt der Fortschritt
    aus → der Spot fällt beim nächsten Lauf erneut an.
    Ein Ausfall bei einem Spot bricht den Lauf nicht ab (try/except pro Spot).

    Rückgabe (TASK-48 On-Demand): eine kompakte Zusammenfassung als dict
    {"status", "checked", "improved", "failed"}. Der Scheduler ruft die Funktion
    weiterhin ohne Argumente auf und ignoriert den Rückgabewert — das bestehende
    Verhalten (Logs/Flags) bleibt unverändert; die Rückgabe ist rein additiv.
    """
    global _qa_pass_running

    # AK-6: nicht überlappen — weder mit einem zweiten QA-Lauf noch mit dem Recompute.
    if _qa_pass_running:
        logger.info("QA-Lauf läuft bereits, übersprungen")
        return {"status": "skipped", "reason": "qa_pass_running",
                "checked": 0, "improved": 0, "failed": 0}
    if _precompute_running:
        logger.info("QA-Lauf übersprungen — Neuberechnung läuft (wird nächste Nacht nachgeholt)")
        return {"status": "skipped", "reason": "precompute_running",
                "checked": 0, "improved": 0, "failed": 0}

    _qa_pass_running = True
    logger.info("Starte QA-Lauf (TASK-48)...")
    checked = 0
    improved = 0
    failed = 0
    try:
        due = _qa_select_due(LOCATIONS, _store)
        logger.info("QA-Lauf: %d von %d Spots fällig (geändert/neu)", len(due), len(LOCATIONS))
        for loc, current_hash in due:
            # AK-6: Falls inzwischen ein großer Recompute angelaufen ist, sauber
            # abbrechen — die offenen Spots fallen beim nächsten QA-Lauf erneut an
            # (kein verlorener Stand, da Hash nur bei Erfolg fortgeschrieben wird).
            if _precompute_running:
                logger.info("QA-Lauf pausiert — Neuberechnung gestartet; Rest fällt nächste Nacht an")
                break
            try:
                ok = await asyncio.to_thread(_qa_improve_one, loc, _store)
                if ok:
                    # AK-1/AK-3/AK-8: Erfolg → Hash + Zeitstempel fortschreiben,
                    # auch wenn nur ein Lock-Spot „nichts geschrieben" hat.
                    _store.update_qa_checked(loc.id, current_hash)
                    checked += 1
                    improved += 1
                else:
                    # AK-5: harter Fehler → NICHT fortschreiben, erneut versuchen.
                    failed += 1
            except Exception as exc:
                # Fehlerisolierung pro Spot (Lauf bricht nie ganz ab).
                logger.warning("QA-Lauf: Spot %s übersprungen (%s)", loc.id, exc)
                failed += 1
            # AK-7: Drosselung — kurze Pause zwischen Spots.
            if _QA_PASS_THROTTLE_S > 0:
                await asyncio.sleep(_QA_PASS_THROTTLE_S)
        logger.info("QA-Lauf fertig: %d geprüft, %d verbessert, %d fehlgeschlagen", checked, improved, failed)
    except Exception as exc:
        logger.error("QA-Lauf abgebrochen (unerwartet): %s", exc)
    finally:
        _qa_pass_running = False
    return {"status": "completed", "checked": checked, "improved": improved, "failed": failed}


async def _run_precompute_single_subproc(loc_id: str, flag: str, tag: str) -> int:
    """
    US-106 (Nachbesserung): Startet precompute.py --location-id <loc_id> mit genau
    EINEM Teil-Flag (--feed-only oder --calendar-only) als Subprozess.
    Gibt den Exit-Code zurück (oder -1 bei Start-Fehler). Loggt die Subprozess-
    Ausgabe mit dem Tag, damit Feed- und Kalender-Schritt im Log unterscheidbar sind.
    """
    backend_dir = Path(__file__).parent
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(backend_dir / "precompute.py"),
            "--location-id", loc_id, flag,
            cwd=str(backend_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        if stdout:
            for line in stdout.decode(errors="replace").splitlines():
                logger.info("  [%s] %s", tag, line)
        return proc.returncode if proc.returncode is not None else -1
    except Exception as e:
        logger.error("Fehler beim Start von precompute.py (%s) für %s: %s", tag, loc_id, e)
        return -1


async def _recompute_one(loc_id: str) -> None:
    """
    US-106 (Nachbesserung): Kern der Einzel-Neuberechnung OHNE Single-Flight-Guard/Drain.

    Reihenfolge nach Stephans Entscheidung „Feed + Wetter sofort, Kalender im
    Hintergrund":
      1. Einzel-FEED schnell rechnen (precompute.py --location-id --feed-only),
         Caches laden, gezieltes Wetter für genau diese Location aufspielen.
         Sobald Feed UND Wetter stehen → _finalize_pending → Banner verschwindet
         in Sekunden (vorher hing es ~10 Min am 365-Tage-Kalender).
      2. DANACH den 365-Tage-KALENDER für genau diese Location nachziehen
         (precompute.py --location-id --calendar-only). Dieser Schritt läuft noch
         innerhalb desselben _precompute_running-Gates (kein zweiter schwerer
         Kalenderlauf parallel), hält aber die bereits erfolgte Freigabe/das
         Banner NICHT mehr auf. Kalender-Fehler nehmen die Feed/Wetter-Freigabe
         NICHT zurück.

    Schlägt das gezielte Wetter fehl → Location bleibt pending (Banner bleibt
    ehrlich), nächster Drain/Cron versucht es erneut. Der Kalender wird trotzdem
    nachgezogen (er hängt nicht am Wetter), die FREIGABE erfolgt aber erst, wenn
    das Wetter steht.
    """
    logger.info("Starte Single-Location Recompute: %s", loc_id)

    # --- Schritt 1: Feed schnell + gezieltes Wetter + Freigabe -----------------
    rc_feed = await _run_precompute_single_subproc(loc_id, "--feed-only", "recompute-feed")
    if rc_feed != 0:
        logger.error("Single-Location FEED fehlgeschlagen (exit %d) für %s", rc_feed, loc_id)
        _recompute_pending.discard(loc_id)
        return

    logger.info("Single-Location FEED abgeschlossen (%s). Lade Feed-Cache neu.", loc_id)
    _load_elevation_cache()
    _load_caches()

    # US-106 Teil 1: gezielt Wetter für genau diese Location nachladen.
    weather_ready = await _weather_overlay_single(loc_id)
    if weather_ready:
        # US-106 Teil 3: jetzt freigeben (Feed UND Wetter stehen) – Banner weg in Sekunden.
        _finalize_pending(loc_id)
    else:
        # Wetter (noch) nicht aufspielbar → Location bleibt pending; ehrliches
        # Banner bleibt sichtbar, nächster Drain/Cron versucht es erneut.
        logger.info("US-106 %s bleibt pending – Wetter noch nicht vollständig.", loc_id)

    # --- Schritt 2: 365-Tage-Kalender im Hintergrund nachziehen ----------------
    # Hält die Freigabe oben NICHT auf. Ein Fehler hier nimmt die bereits
    # erfolgte Feed/Wetter-Freigabe NICHT zurück (kein _recompute_pending-Eingriff).
    logger.info("US-106 Ziehe 365-Tage-Kalender für %s im Hintergrund nach …", loc_id)
    rc_cal = await _run_precompute_single_subproc(loc_id, "--calendar-only", "recompute-calendar")
    if rc_cal != 0:
        logger.error("Single-Location KALENDER fehlgeschlagen (exit %d) für %s – "
                     "Feed/Wetter bleiben freigegeben, Kalender zeigt vorerst den alten Stand.",
                     rc_cal, loc_id)
        return
    logger.info("Single-Location KALENDER abgeschlossen (%s). Lade Kalender-Cache neu.", loc_id)
    _load_caches()


async def _run_precompute_single(loc_id: str, _allow_drain: bool = True) -> None:
    """
    TASK-12 / BUG-29: Startet precompute.py --location-id <loc_id> im Hintergrund.
    Wird automatisch nach PATCH /locations/{id} mit Koordinaten-Änderung aufgerufen.
    Hält den PATCH-Response nicht auf – läuft vollständig asynchron.

    BUG-29: Ohne --feed-only regeneriert der Single-Flow jetzt sowohl den Feed
    (opportunities.json) ALS AUCH den Kalender (calendar.json) für genau diese
    Location.

    US-106 Teil 3: Wird die Berechnung wegen eines laufenden Großlaufs
    übersprungen, geht die Änderung NICHT verloren — die ID bleibt in
    _recompute_pending und wird am Ende des laufenden Laufs nachgeholt
    (siehe _drain_recompute_pending). Nach erfolgreicher Einzel-Berechnung
    arbeitet dieser Lauf selbst noch offene Pending-IDs ab (_allow_drain).
    """
    global _precompute_running
    if _NO_BACKGROUND:
        logger.info("FOTOALERT_NO_BACKGROUND=1 → Single-Location Recompute für '%s' übersprungen (Test-Modus).", loc_id)
        return
    if _precompute_running:
        # US-106: NICHT mehr stillschweigend verwerfen. ID bleibt pending und
        # wird am Lauf-Ende des aktuell laufenden Prozesses nachgeholt.
        _recompute_pending.add(loc_id)
        logger.info("Single-Location Recompute für '%s' verschoben – Berechnung läuft bereits (bleibt pending)", loc_id)
        return

    _precompute_running = True
    try:
        await _recompute_one(loc_id)
    finally:
        _precompute_running = False
        if _allow_drain:
            await _drain_recompute_pending()


# ---------------------------------------------------------------------------
# Startup / Shutdown
# ---------------------------------------------------------------------------

def _load_location_overrides() -> None:
    """Wendet Location-Overrides aus SQLite auf alle Locations an.
    TASK-17: ersetzt JSON-basiertes Laden.
    Fallback: falls DB leer und JSON noch vorhanden, migriert automatisch.
    """
    try:
        overrides = _store.load_all_overrides()

        # Fallback: DB leer → aus JSON migrieren
        if not overrides:
            _json_file = Path(__file__).parent / "data" / "location_overrides.json"
            if _json_file.exists():
                import json as _json
                raw = _json.loads(_json_file.read_text(encoding="utf-8"))
                for ov in raw:
                    loc_id = ov.get("id")
                    if loc_id:
                        fields = {k: v for k, v in ov.items() if k != "id"}
                        _store.upsert_override_if_not_exists(loc_id, fields)
                overrides = _store.load_all_overrides()
                if overrides:
                    logger.info("Location Overrides auto-migriert aus JSON: %d Einträge", len(overrides))

        # US-68 Slice 1: Tombstoned Locations vor dem Mapping herausfiltern
        tombstoned_ids = {ov["id"] for ov in overrides if ov.get("deleted")}
        if tombstoned_ids:
            LOCATIONS[:] = [l for l in LOCATIONS if l.id not in tombstoned_ids]
            logger.info("Tombstoned Locations beim Start entfernt: %s", tombstoned_ids)

        loc_map = {loc.id: loc for loc in LOCATIONS}
        applied = 0
        for ov in overrides:
            loc_id = ov.get("id")
            if ov.get("deleted"):
                continue  # Tombstone – kein Feld-Apply
            loc = loc_map.get(loc_id)
            if loc:
                # US-128: Feld-Tupel jetzt aus data/locations.py:LOCATION_FIELD_RULES
                # abgeleitet (OVERRIDE_RELOAD_FIELDS) statt hier hartkodiert dupliziert.
                for field in OVERRIDE_RELOAD_FIELDS:
                    if field in ov:
                        setattr(loc, field, ov[field])
                applied += 1
        if applied:
            logger.info("Location Overrides geladen: %d Einträge aus SQLite", applied)
    except Exception as exc:
        logger.warning("Fehler beim Laden der Location Overrides: %s", exc)


def _save_location_override(loc_id: str, **fields) -> None:
    """Speichert/aktualisiert einen Override-Eintrag in SQLite (TASK-17: ersetzt JSON-Write)."""
    _store.upsert_override(loc_id, **fields)


def _load_qa_values() -> None:
    """TASK-43: Wendet auto-generierte QA-Felder auf alle Locations an.

    Merge-Reihenfolge: Code-Defaults < qa_values < location_overrides.
    qa_values überschreiben also Standardwerte aus locations.py, werden aber
    selbst durch manuell gesetzte location_overrides überschrieben.

    Unterstützte Felder: description, ideal_azimuth_min/max, focal_length_suggestions.
    """
    try:
        qa_values = _store.load_all_qa_values()
        if not qa_values:
            return
        loc_map = {loc.id: loc for loc in LOCATIONS}
        applied = 0
        for qv in qa_values:
            loc_id = qv.get("location_id")
            loc = loc_map.get(loc_id)
            if not loc:
                continue
            if qv.get("description") is not None:
                loc.description = qv["description"]
            if qv.get("ideal_azimuth_min") is not None and qv.get("ideal_azimuth_max") is not None:
                loc.ideal_azimuth_range = (qv["ideal_azimuth_min"], qv["ideal_azimuth_max"])
            if qv.get("focal_length_suggestions") is not None:
                loc.focal_length_suggestions = qv["focal_length_suggestions"]
            # US-09: Sichtachsen-Status/Winkel anwenden (Default "nicht_geprueft"
            # bleibt bestehen, solange kein QA-Wert gespeichert ist).
            if qv.get("sightline_status") is not None:
                loc.sightline_status = qv["sightline_status"]
            if qv.get("sightline_angle_deg") is not None:
                loc.sightline_angle_deg = qv["sightline_angle_deg"]
            applied += 1
        if applied:
            logger.info("QA-Values geladen: %d Locations gepatcht", applied)
    except Exception as exc:
        # BUG-70: war zuvor logger.warning — eine korrupte location_qa_values-Tabelle
        # (SQLite "database disk image is malformed") blieb dadurch beim routinemäßigen
        # Log-Blick unsichtbar. Jetzt ERROR + zusätzlicher Integritätscheck zur Einordnung.
        check = _store.integrity_check()
        logger.error(
            "Fehler beim Laden der QA-Values: %s | PRAGMA integrity_check: %s",
            exc, check,
        )


def _startup_integrity_check() -> None:
    """TASK-51: aus startup() ausgelagert (Schritt 1), Verhalten unverändert.

    BUG-70: genereller Integritätscheck der SQLite-Datenbank beim Start —
    unabhängig von einem konkreten Ladefehler (z.B. QA-Values). Eine "malformed"-
    Datenbank soll beim routinemäßigen Log-Blick auffallen, nicht erst bei einer
    Ad-hoc-Diagnose wie beim ursprünglichen Vorfall.
    """
    try:
        _startup_check = _store.integrity_check()
        if _startup_check != ["ok"]:
            logger.error(
                "PRAGMA integrity_check meldet Abweichungen beim Server-Start "
                "(DB: %s): %s — mindestens eine Tabelle/Seite ist beschädigt. "
                "Bitte zeitnah prüfen (siehe BUG-70).",
                _store.db_path, _startup_check,
            )
    except Exception as _exc:
        logger.error("Startup-Integritätscheck konnte nicht ausgeführt werden: %s", _exc)


def _startup_check_discover_schema() -> None:
    """TASK-51: aus startup() ausgelagert (Schritt 6), Verhalten unverändert.

    Scout-Cache laden (falls vorhanden) und ggf. neu berechnen.
    Schema-Check: US-81 migrierte moon_* → body_*. Alter Cache hat kein body_name-Feld
    → erzwingt Neuberechnung damit das Frontend nicht undefined° anzeigt.
    """
    _load_discover_cache()
    _first_opp = (_discover_cache.get("opportunities") or [{}])[0]
    if not _discover_cache or "body_name" not in _first_opp:
        if _discover_cache:
            logger.info("Scout-Cache hat altes Schema (moon_*) — starte Neuberechnung (US-81).")
        asyncio.create_task(_refresh_discover())


async def _prewarm_calendar() -> None:
    """TASK-51: aus startup() ausgelagert (Schritt 9, vormals verschachtelte Closure).

    On-Demand: aktuellen Monat (alle Locations) im Hintergrund vorwärmen, damit
    die Kalender-Monatsübersicht beim ersten Aufruf sofort da ist (statt ~30 s).
    """
    d = date.today()
    try:
        await _compute_month_all_locations(d.year, d.month)
        logger.info("On-Demand-Kalender vorgewärmt: %d-%02d", d.year, d.month)
    except Exception as e:
        logger.error("Kalender-Pre-Warm fehlgeschlagen: %s", e)


def _startup_setup_scheduler(_precompute_mode: str) -> None:
    """TASK-51: aus startup() ausgelagert (Schritt 10), Verhalten unverändert.

    Scheduler — functools.partial bleibt eine Coroutine-Funktion (APScheduler
    awaitet sie korrekt; ein lambda täte das nicht).
    """
    import functools as _functools
    # TASK-48: Nächtlicher QA-Lauf um 05:15 — bewusst 15 Min VOR dem Recompute
    # (05:30), damit frisch verbesserte Auto-Werte beim Recompute schon vorliegen
    # und über _apply_qa_values() in Feed/Kalender einfließen.
    scheduler.add_job(_run_qa_pass, "cron", hour=1, minute=0)   # täglich 01:00 (großer Puffer vor Recompute 05:30)
    scheduler.add_job(_functools.partial(_run_precompute, _precompute_mode),
                      "cron", hour=5, minute=30)   # täglich 05:30 (On-Demand: nur Feed)
    scheduler.add_job(_weather_overlay,  "cron", minute=0, hour="*/3") # alle 3h
    scheduler.add_job(_build_weather_map, "cron", minute=20, hour="*/3") # US-112: Karten-Overlay alle 3h
    scheduler.add_job(_refresh_discover, "cron", hour=5,  minute=45)   # täglich 05:45 (nach precompute)
    scheduler.start()


@app.on_event("startup")
async def startup() -> None:
    logger.info("FotoAlert Backend v2 startet (Cache-First)...")

    _startup_integrity_check()

    # 0. Custom Locations laden (persistent gespeicherte User-Spots)
    _load_custom_locations()

    # 0a. QA-Values laden (auto-generierte Felder, TASK-43)
    # Reihenfolge: Code-Defaults < qa_values < location_overrides
    _load_qa_values()

    # 0b. Location Overrides laden (Koordinaten-Korrekturen für alle Location-Typen)
    _load_location_overrides()

    # 0b. Geländehöhen-Cache laden und Locations patchen
    _load_elevation_cache()

    # 1. JSON-Caches laden (sofort)
    cache_ok = _load_caches()

    # Test-/Sandbox-Modus: hier abbrechen — keine Hintergrundjobs, kein Netzwerk, kein
    # Scheduler. Synchron geladene Daten (Locations, Overrides, Caches) stehen den
    # Endpoints zur Verfügung; alles Asynchrone/Periodische wird übersprungen.
    if _NO_BACKGROUND:
        logger.info("FOTOALERT_NO_BACKGROUND=1 → Startup ohne Scheduler/Precompute/Netzwerk (Test-Modus).")
        return

    # 2. Wetter-Overlay für T+0..T+3 (schnell, ~5s)
    asyncio.create_task(_weather_overlay())

    # US-112: Wetter-Karten-Overlay (DWD ICON + MET Norway → PNG je Stunde) im
    # Hintergrund vorbauen, damit der Map-Tab beim ersten Einschalten schon Daten hat.
    asyncio.create_task(_build_weather_map())

    # 2b. Scout-Cache laden (falls vorhanden) und ggf. neu berechnen
    _startup_check_discover_schema()

    # TASK-25 / AK5 (Option A): Im On-Demand-Modus wird der schwere 365-Tage-
    # Kalender NICHT mehr vorberechnet (kommt live über /calendar). Es bleibt nur
    # ein leichter 14-Tage-Feed-Refresh (für den schnellen Startbildschirm), der
    # dank Window-Engine in Minuten statt Stunden läuft. Default (Flag aus) =
    # bisheriges Verhalten (full).
    _ondemand = os.getenv("FOTOALERT_ONDEMAND", "0") == "1"
    _precompute_mode = "feed" if _ondemand else "full"

    # 3. Wenn kein Cache vorhanden: Vorberechnung starten
    if not cache_ok:
        logger.warning("Kein Cache gefunden – starte Erstberechnung im Hintergrund "
                       "(Modus=%s)", _precompute_mode)
        asyncio.create_task(_run_precompute(_precompute_mode))

    # On-Demand: aktuellen Monat (alle Locations) im Hintergrund vorwärmen, damit
    # die Kalender-Monatsübersicht beim ersten Aufruf sofort da ist (statt ~30 s).
    if _ondemand:
        asyncio.create_task(_prewarm_calendar())

    _startup_setup_scheduler(_precompute_mode)
    logger.info("Bereit. Cache: %d Feed-Events, %d Kalender-Events, Scout: %d Chancen",
                len(_feed_cache), len(_calendar_cache),
                _discover_cache.get("count", 0))


@app.on_event("shutdown")
async def shutdown() -> None:
    # Im Test-/Sandbox-Modus wurde der Scheduler nie gestartet → nicht herunterfahren.
    if not _NO_BACKGROUND and scheduler.running:
        scheduler.shutdown()


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _compute_possible_bodies(observer_lat: float, ideal_azimuth_range: list | None) -> list[str]:
    """
    US-35: Berechnet welche Himmelskörper (sun/moon/milkyway) jemals im
    ideal_azimuth_range sichtbar sein können, basierend auf der geografischen
    Breite des Beobachters.

    Formel für Auf-/Untergangsazimut bei Altitude = 0:
        cos(Az) = sin(δ) / cos(φ)
    wobei δ = Deklination des Körpers, φ = Beobachterbreite.

    Aufgangsazimut Az ∈ [0°,180°] (Ost-Halbkugel).
    Untergangsazimut = 360° – Az (Symmetrie um N-S-Achse).
    """
    if not ideal_azimuth_range or len(ideal_azimuth_range) < 2:
        return ["sun", "moon", "milkyway"]

    az_lo, az_hi = float(ideal_azimuth_range[0]), float(ideal_azimuth_range[1])
    cos_lat = math.cos(math.radians(observer_lat))
    if cos_lat < 1e-9:
        return ["sun", "moon", "milkyway"]  # Pol – Sonderfälle ignorieren

    def _rise_set_ranges(dec_min_deg: float, dec_max_deg: float) -> list[tuple[float, float]]:
        """Aufgangs- und Untergangsazimut-Band für den Deklinationsbereich."""
        rise_azs = []
        for dec_deg in (dec_min_deg, dec_max_deg):
            val = math.sin(math.radians(dec_deg)) / cos_lat
            val = max(-1.0, min(1.0, val))
            rise_azs.append(math.degrees(math.acos(val)))
        rise_lo, rise_hi = min(rise_azs), max(rise_azs)
        set_lo, set_hi   = 360.0 - rise_hi, 360.0 - rise_lo
        return [(rise_lo, rise_hi), (set_lo, set_hi)]

    def _overlaps(lo: float, hi: float, ranges: list[tuple[float, float]]) -> bool:
        """Prüft ob das Segment [lo, hi] (auf dem 0-360-Kreis) eine Range schneidet."""
        for r_lo, r_hi in ranges:
            if lo <= hi:                   # normales Segment
                if lo <= r_hi and hi >= r_lo:
                    return True
            else:                          # Wrap-around durch Nord
                if lo <= r_hi or hi >= r_lo:
                    return True
        return False

    possible: list[str] = []

    # Sonne: Deklination -23.44° bis +23.44° (Solstitien)
    if _overlaps(az_lo, az_hi, _rise_set_ranges(-23.44, 23.44)):
        possible.append("sun")

    # Mond: Deklination -(23.44+5.14)° bis +(23.44+5.14)° (Sonnenbahn ± Mondinklination)
    if _overlaps(az_lo, az_hi, _rise_set_ranges(-28.58, 28.58)):
        possible.append("moon")

    # Milchstraße: Galaktisches Zentrum (Sgr A*) hat δ ≈ -29°.
    # An mittleren Breiten (~52°N) erscheint es im Bereich ~130°–230° (SE bis SW).
    # Großzügiger Puffer ±10° berücksichtigt galaktische Ebene.
    if _overlaps(az_lo, az_hi, [(120.0, 240.0)]):
        possible.append("milkyway")

    return possible


def _loc_to_out(loc) -> LocationOut:
    az_range = list(loc.ideal_azimuth_range) if getattr(loc, 'ideal_azimuth_range', None) else None
    return LocationOut(
        id=loc.id,
        name=loc.name,
        description=loc.description,
        category=loc.category.value,
        observer_lat=loc.observer_lat,
        observer_lon=loc.observer_lon,
        subject_lat=getattr(loc, 'subject_lat', None),
        subject_lon=getattr(loc, 'subject_lon', None),
        ideal_azimuth_range=az_range,
        subject_name=loc.subject_name,
        subject_height_m=loc.subject_height_m,
        subject_width_m=getattr(loc, 'subject_width_m', None),  # US-128
        elevation_difference_m=getattr(loc, 'elevation_difference_m', 0.0),
        observer_floor_height_m=getattr(loc, 'observer_floor_height_m', 0.0),
        distance_m=loc.distance_m,
        focal_length_suggestions=loc.focal_length_suggestions,
        special_notes=loc.special_notes,
        solar_alignment_note=loc.solar_alignment_note,
        lunar_alignment_note=loc.lunar_alignment_note,
        access_note=loc.access_note,
        locationscout_url=loc.locationscout_url,
        difficulty=loc.difficulty,
        possible_bodies=_compute_possible_bodies(loc.observer_lat, az_range),
        image_url=f"/location-images/{loc.image_filename}" if getattr(loc, "image_filename", None) else None,
        # US-126: Fallback auf 50/50 (Bildmitte), falls kein Fokuspunkt gespeichert ist
        image_focus_x=getattr(loc, "image_focus_x", None) if getattr(loc, "image_focus_x", None) is not None else 50.0,
        image_focus_y=getattr(loc, "image_focus_y", None) if getattr(loc, "image_focus_y", None) is not None else 50.0,
        # US-09: Sichtachsen-Status/Winkel (Default "nicht_geprueft", siehe PhotoLocation)
        sightline_status=getattr(loc, "sightline_status", None) or "nicht_geprueft",
        sightline_angle_deg=getattr(loc, "sightline_angle_deg", None),
    )


def _filter_feed(
    min_score: float,
    event_type: Optional[str],
    priority: Optional[int],
    days: int,
    location_id: Optional[str],
) -> list[dict]:
    now_utc = datetime.now(timezone.utc)
    cutoff  = now_utc + timedelta(days=min(days, 14))

    result = []
    for e in _feed_cache:
        shoot_dt = datetime.fromisoformat(e["shoot_time"])
        # BUG-05: shoot_window_end als Cutoff verwenden (Fallback: shoot_time + 30 min)
        window_end_str = e.get("shoot_window_end")
        window_end = datetime.fromisoformat(window_end_str) if window_end_str else shoot_dt + timedelta(minutes=30)
        if window_end < now_utc:
            continue
        if shoot_dt > cutoff:
            continue
        if e["overall_score"] < min_score:
            continue
        if event_type and e["event_type"].lower() != event_type.lower():
            continue
        if priority is not None and e["alert_priority"] < priority:
            continue
        if location_id and e["location_id"] != location_id:
            continue
        result.append(e)

    # Deduplizierung: pro (location_id + event_type + Tag) nur das beste Event
    result = _dedup_best_per_day(result)

    # BUG-48: Round-Robin pro Event-Typ damit kein Typ den :500-Cap dominiert.
    # 1. Alle Events nach Score absteigend sortieren (Round-Robin nimmt immer den besten noch verfügbaren)
    result.sort(key=lambda e: -e["overall_score"])

    # 2. Nach event_type gruppieren (Reihenfolge der Typen = erster Auftritt im Score-Sort)
    # dict ist seit Python 3.7 insertion-ordered — OrderedDict nicht nötig
    _CAP = 500
    groups: dict = {}
    for e in result:
        t = e["event_type"]
        if t not in groups:
            groups[t] = []
        groups[t].append(e)

    # 3. Reihum je 1 Event pro Typ nehmen bis Cap erreicht
    type_keys = list(groups.keys())
    indices = {t: 0 for t in type_keys}
    selected = []
    while len(selected) < _CAP:
        added_any = False
        for t in type_keys:
            if len(selected) >= _CAP:
                break
            idx = indices[t]
            if idx < len(groups[t]):
                selected.append(groups[t][idx])
                indices[t] = idx + 1
                added_any = True
        if not added_any:
            break

    # 4. Ergebnis zeitlich sortieren für die Ausgabe
    selected.sort(key=lambda e: e["shoot_time"])
    return selected


def _dedup_best_per_day(events: list[dict]) -> list[dict]:
    """
    Pro Location + Event-Typ + Kalendertag nur das Event mit dem höchsten Score behalten.
    Verhindert Mehrfachanzeige desselben Motivs im Abstand weniger Minuten.
    """
    best: dict[str, dict] = {}
    for e in events:
        day = e["shoot_time"][:10]  # "2026-06-14"
        key = f"{e['location_id']}|{e['event_type']}|{day}"
        if key not in best or e["overall_score"] > best[key]["overall_score"]:
            best[key] = e
    return list(best.values())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(
        status="ok",
        version="2.0.0",
        locations_count=len(LOCATIONS),
    )


@app.get("/locations", response_model=list[LocationOut])
async def get_locations(category: Optional[str] = None) -> list[LocationOut]:
    locs = LOCATIONS
    if category:
        locs = [l for l in locs if l.category.value.lower() == category.lower()]
    return [_loc_to_out(l) for l in locs]


@app.get("/locations/{location_id}", response_model=LocationOut)
async def get_location(location_id: str) -> LocationOut:
    loc = get_location_by_id(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail=f"Location '{location_id}' nicht gefunden.")
    return _loc_to_out(loc)


@app.get("/opportunities")
async def get_opportunities(
    min_score: float = 0.35,
    event_type: Optional[str] = None,
    priority: Optional[int] = None,
    days: int = 14,
    location_id: Optional[str] = None,
) -> list[dict]:
    """
    Gibt kommende Foto-Chancen zurück (aus vorberechnetem Cache + Wetter-Overlay).
    Wetter wird nur für die nächsten 3 Tage angezeigt.
    """
    if not _feed_cache:
        return []

    results = _filter_feed(min_score, event_type, priority, days, location_id)
    return results[:500]


@app.get("/opportunities/today")
async def get_today_opportunities() -> list[dict]:
    today = date.today().isoformat()
    result = [
        e for e in _feed_cache
        if e["shoot_time"][:10] == today
    ]
    result.sort(key=lambda e: -e["overall_score"])
    return result[:20]


@app.get("/plan")
async def get_plan(
    observer_lat: float, observer_lon: float,
    subject_lat: float, subject_lon: float,
    subject_name: str = "Motiv",
    subject_height_m: float = 0.0,
    subject_width_m: float = 0.0,
    elevation_difference_m: Optional[float] = None,
    observer_floor_height_m: float = 0.0,
    days: int = 14,
    min_score: float = 0.35,
) -> dict:
    """
    TASK-25 / AK2: On-Demand-Plan für **beliebige** Koordinaten weltweit — ohne
    dass die Location vorab angelegt sein muss. Nutzt die Window-Engine (eine
    Ephemeride fürs ganze Fenster) → Sub-Sekunden pro Lokation, stateless.

    Geländehöhe: wird automatisch über den Elevation-Provider aufgelöst, wenn
    `elevation_difference_m` nicht angegeben ist. Fehlt die DEM-Abdeckung, läuft
    die Rechnung mit 0 weiter und `elevation_incomplete=true` markiert das.
    """
    from datetime import date as _date
    from data.locations import PhotoLocation, LocationCategory
    from data.elevation import provider as _elev
    from calculations.opportunity import find_opportunities_multi_day as _fomd
    from calculations.window_engine import WindowEphemeris
    from precompute import _serialize
    import calculations.astronomy as _astro

    elevation_incomplete = False
    if elevation_difference_m is None:
        elevation_difference_m, elevation_incomplete = await _elev.elevation_difference(
            observer_lat, observer_lon, subject_lat, subject_lon)

    loc = PhotoLocation(
        id="adhoc", name=subject_name, description="On-demand plan",
        category=LocationCategory.SKYLINE,
        observer_lat=observer_lat, observer_lon=observer_lon,
        subject_lat=subject_lat, subject_lon=subject_lon, subject_name=subject_name,
        subject_height_m=subject_height_m or None,
        subject_width_m=subject_width_m or None,
        elevation_difference_m=elevation_difference_m,
        observer_floor_height_m=observer_floor_height_m,
    )
    start = _date.today()
    # Window-Engine für genau dieses Fenster erzwingen (unabhängig vom Env-Flag)
    _astro.set_active_window(WindowEphemeris(observer_lat, observer_lon, start, days))
    try:
        opps = await _fomd(loc, start, days, None, min_score=min_score, astronomy_only=True)
    finally:
        _astro.clear_active_window()
    return {"status": "ok", "on_demand": True, "days": days,
            "elevation_difference_m": elevation_difference_m,
            "elevation_incomplete": elevation_incomplete,
            "count": len(opps), "events": [_serialize(o) for o in opps]}


@app.get("/daily-briefing", response_model=DailyBriefingOut)
async def daily_briefing(target_date: Optional[str] = None) -> DailyBriefingOut:
    d = date.fromisoformat(target_date) if target_date else date.today()
    day_str = d.isoformat()

    day_opps = [e for e in _feed_cache if e["shoot_time"][:10] == day_str]
    day_opps.sort(key=lambda e: (-e["alert_priority"], -e["overall_score"]))
    top10 = day_opps[:10]

    high_prio = [e for e in day_opps if e["alert_priority"] >= 2]
    best_score = max((e["overall_score"] for e in day_opps), default=0.0)

    if not top10:
        summary = f"Für {d.strftime('%d. %B')} wurden keine Foto-Chancen gefunden."
    elif high_prio:
        summary = (f"{len(high_prio)} besondere Ereignisse am {d.strftime('%d. %B')}: "
                   + ", ".join(e["title"] for e in high_prio[:3]))
    else:
        t = top10[0]["title"] if top10 else "–"
        summary = (f"{len(day_opps)} Foto-Chancen am {d.strftime('%d. %B')} – "
                   f"Bester Score: {best_score:.0%}. Top: {t}")

    # Konvertierung zu OpportunityOut für DailyBriefingOut
    def _to_opp_out(e: dict) -> OpportunityOut:
        return OpportunityOut(
            id=e["id"], location_id=e["location_id"], location_name=e["location_name"],
            event_type=e["event_type"], title=e["title"], description=e["description"],
            shoot_time=e["shoot_time"], shoot_window_start=e.get("shoot_window_start") or e["shoot_time"],
            shoot_window_end=e.get("shoot_window_end") or e["shoot_time"],
            overall_score=e["overall_score"], astronomy_score=e["astronomy_score"],
            weather_score=e["weather_score"], location_score=e.get("location_score", 1.0),
            camera_hints=[CameraHintOut(**h) for h in e.get("camera_hints", [])],
            subject_azimuth=e.get("subject_azimuth"), celestial_azimuth=e.get("celestial_azimuth"),
            celestial_altitude=e.get("celestial_altitude"), alert_priority=e["alert_priority"],
            weather_description=e.get("weather_description", ""),
            moon_phase=e.get("moon_phase"), moon_illumination_pct=e.get("moon_illumination_pct"),
            elevation_difference_m=e.get("elevation_difference_m"),
            sunrise_utc=e.get("sunrise_utc"), sunset_utc=e.get("sunset_utc"),
            golden_hour_morning_start=e.get("golden_hour_morning_start"),
            golden_hour_morning_end=e.get("golden_hour_morning_end"),
            golden_hour_evening_start=e.get("golden_hour_evening_start"),
            golden_hour_evening_end=e.get("golden_hour_evening_end"),
            blue_hour_morning_start=e.get("blue_hour_morning_start"),
            blue_hour_morning_end=e.get("blue_hour_morning_end"),
            blue_hour_evening_start=e.get("blue_hour_evening_start"),
            blue_hour_evening_end=e.get("blue_hour_evening_end"),
        )

    return DailyBriefingOut(
        date=d.isoformat(),
        location_count=len(set(e["location_id"] for e in day_opps)),
        top_opportunities=[_to_opp_out(e) for e in top10],
        highest_score=round(best_score, 2),
        alert_count=len(high_prio),
        summary=summary,
    )


# TASK-25 / AK5: In-Memory-Cache für die On-Demand-Monatsübersicht (alle Locations).
# Ersetzt den 365×N-Batch: ein Monat wird bei Bedarf einmal gerechnet (Window-Engine)
# und gecacht; Pre-Warm beim Start hält die gängigen Monate sofort verfügbar.
_ondemand_month_cache: dict[str, list] = {}


async def _compute_location_month(loc, year: int, month: int, min_score: float) -> list:
    """Serialisierte, gefilterte Kalender-Events EINER Location für einen Monat
    (On-Demand via Window-Engine)."""
    import calendar as _cal
    from datetime import date as _date
    from calculations.opportunity import find_opportunities_multi_day as _fomd
    from calculations.window_engine import WindowEphemeris
    from precompute import _serialize, _passes_alignment_filter
    import calculations.astronomy as _astro

    ndays = _cal.monthrange(year, month)[1]
    start = _date(year, month, 1)
    _astro.set_active_window(WindowEphemeris(loc.observer_lat, loc.observer_lon, start, ndays))
    try:
        opps = await _fomd(loc, start, ndays, None, min_score=min_score, astronomy_only=True)
    finally:
        _astro.clear_active_window()
    return [e for e in (_serialize(o) for o in opps) if _passes_alignment_filter(e)]


async def _compute_month_all_locations(year: int, month: int, min_score: float = 0.40) -> list:
    """Monatsübersicht über ALLE Locations (On-Demand, gecacht). Ersetzt den
    365-Tage-Batch durch eine bedarfsgesteuerte, schnelle Monatsberechnung."""
    import asyncio as _asyncio
    from data.locations import LOCATIONS as _LOCS
    key = f"{year}-{month:02d}-{min_score}"
    if key in _ondemand_month_cache:
        return _ondemand_month_cache[key]
    events: list = []
    for i, loc in enumerate(_LOCS):
        try:
            events.extend(await _compute_location_month(loc, year, month, min_score))
        except Exception as e:
            logger.error("On-Demand-Kalender %s %s-%s: %s", loc.id, year, month, e)
        if i % 8 == 0:
            await _asyncio.sleep(0)   # Event-Loop nicht blockieren
    _ondemand_month_cache[key] = events
    return events


@app.get("/calendar")
async def get_calendar(
    location_id: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    min_score: float = 0.40,
) -> dict:
    """
    Jahreskalender: astronomy-only Events für alle Locations, 365 Tage.
    month (1–12) + year filtern serverseitig – Clients sollten immer beide
    Parameter übergeben, um den Payload klein zu halten (~1–3 MB / Monat).

    TASK-25 / AK5: Bei aktivem On-Demand-Flag und gesetzter location_id wird der
    Kalender für genau diese Location + Monat **live** berechnet (Window-Engine),
    ohne dass ein 365×N-Batch nötig ist.
    """
    if os.getenv("FOTOALERT_ONDEMAND", "0") == "1" and month and year:
        from data.locations import LOCATIONS as _LOCS
        if location_id:
            loc = next((l for l in _LOCS if l.id == location_id), None)
            if loc is None:
                return {"status": "not_found", "events": [], "total": 0,
                        "message": f"Location {location_id} unbekannt."}
            events = await _compute_location_month(loc, year, month, min_score)
        else:
            # Alle Locations: aus dem Monats-Cache (oder bei Bedarf einmal rechnen)
            events = await _compute_month_all_locations(year, month, min_score)
        return {"status": "ok", "on_demand": True, "computed_at": None,
                "total": len(events), "events": events}

    if not _calendar_cache:
        if _precompute_running:
            return {"status": "calculating", "events": [], "total": 0,
                    "message": "Erstberechnung läuft. Bitte in 2–5 Minuten neu laden."}
        return {"status": "no_cache", "events": [], "total": 0,
                "message": "Kein Kalender-Cache. Starte /refresh um die Berechnung anzustoßen."}

    events = _calendar_cache
    if location_id:
        events = [e for e in events if e["location_id"] == location_id]
    if month:
        events = [e for e in events if int(e["shoot_time"][5:7]) == month]
    if year:
        events = [e for e in events if int(e["shoot_time"][:4]) == year]
    if min_score != 0.40:
        events = [e for e in events if e["overall_score"] >= min_score]

    return {
        "status": "ok",
        "computed_at": (json.loads(_CAL_CACHE.read_text())["computed_at"]
                        if _CAL_CACHE.exists() else None),
        "total": len(events),
        "events": events,
    }


@app.get("/discover")
async def get_discover(
    min_score: float = 0.0,
    subject_id: Optional[str] = None,
    days: int = 14,
) -> dict:
    """
    Scout-Tab: Mond-Alignment-Chancen für die nächsten 14 Tage.
    Gibt vorberechnete Chancen aus dem Cache zurück.
    """
    if not _discover_cache:
        return {
            "status": "calculating",
            "opportunities": [],
            "total": 0,
            "generated_at": None,
            "message": "Scout-Pipeline läuft noch. Bitte in 1–2 Minuten neu laden.",
        }

    opps = list(_discover_cache.get("opportunities", []))
    cutoff = (date.today() + timedelta(days=days)).isoformat()

    if subject_id:
        opps = [o for o in opps if o["subject_id"] == subject_id]
    if min_score > 0:
        opps = [o for o in opps if o["score"] >= min_score]
    opps = [o for o in opps if o["day"] <= cutoff]

    return {
        "status": "ok",
        "generated_at": _discover_cache.get("generated_at"),
        "total": len(opps),
        "opportunities": opps,
    }


# TASK-83 ⚠️ Annahme (von Stephan im Weg-Gate bestätigt): 30 Tage Cookie-Lebensdauer,
# erhält die bisherige, praktisch unbegrenzte localStorage-Persistenz näherungsweise.
_SESSION_MAX_AGE_S = 60 * 60 * 24 * 30  # 30 Tage

# TASK-83 Nachtrag (Safari-Fund, Stephans manueller Test 2026-07-16): Die Pre-Mortem-
# Annahme im Ticket (MDN: Secure-Cookies funktionieren auch über http://localhost) galt
# NICHT für jeden Browser — Chrome macht für localhost stillschweigend eine Ausnahme,
# Safari nicht: das Cookie erscheint dort einfach nicht im Speicher-Tab, ohne
# Konsolen-Fehler. Produktion ist nicht betroffen (echtes HTTPS via Caddy). Secure daher
# nur in Prod hart erzwingen (nicht verhandelbar), im Dev-Modus weglassen — siehe
# TASK-19-Muster (`FOTOALERT_ENV`, data/store.py) für dieselbe dev/prod-Unterscheidung.
_COOKIE_SECURE = _os.getenv("FOTOALERT_ENV", "prod") == "prod"


@app.post("/login")
async def login(response: Response, body: dict = Body(...)) -> dict:
    """US-66/TASK-83: Pflicht-Login. Passwort → Rolle (host/user) + HttpOnly-Sitzungscookie.

    Kein Username, kein Rollen-Auswahlfeld — die Rolle ergibt sich aus dem Passwort.
    TASK-83: Das Sitzungs-Ticket wandert vom JS-lesbaren Response-Body (bisher `token`)
    in ein HttpOnly/Secure/SameSite=Lax-Cookie — ein XSS-Skript kann es dadurch nicht
    mehr direkt auslesen. Kein Authorization-Header-Fallback (Weg-Gate-Entscheidung 3).
    """
    password = (body or {}).get("password", "")
    role = auth.role_for_password(password)
    if not role:
        raise HTTPException(status_code=401, detail="Falsches Passwort.")
    response.set_cookie(
        key=auth.SESSION_COOKIE_NAME,
        value=auth.issue_token(role),
        max_age=_SESSION_MAX_AGE_S,
        path="/",
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
    )
    return {"role": role}


@app.post("/logout")
async def logout(response: Response) -> dict:
    """TASK-83: Neuer Endpoint — lässt das Sitzungscookie serverseitig verfallen.

    JS kann ein HttpOnly-Cookie nicht selbst löschen; bislang räumte Auth.logout() im
    Frontend nur localStorage auf (Cookie hätte weitergelebt). Max-Age=0 verfällt das
    Cookie sofort beim Client.
    """
    response.delete_cookie(
        key=auth.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
    )
    return {"status": "ok"}


@app.post("/refresh-discover")
async def trigger_discover_refresh(background_tasks: BackgroundTasks, _role: str = Depends(auth.require_host)) -> dict:
    """Startet die Scout-Pipeline im Hintergrund (~1–3 Min.)."""
    background_tasks.add_task(_refresh_discover)
    return {"status": "started", "message": "Scout-Pipeline gestartet (~1–3 Min.)."}


@app.post("/register-device")
async def register_device(token: str, platform: str = "ios") -> dict:
    # US-66: bewusst NICHT geschützt — die native iOS-App ist noch nicht login-fähig.
    # TASK-24: Token wird jetzt in SQLite persistiert (nicht mehr im RAM).
    # Auth-Schutz nachziehen, sobald die iOS-App ein Token sendet (Folge-Ticket).
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="token ist erforderlich.")
    is_new = _store.register_device_token(token=token, platform=platform)
    if not is_new:
        return {"status": "already_registered"}
    return {"status": "registered", "device_count": _store.device_token_count()}


@app.post("/refresh")
async def trigger_refresh(background_tasks: BackgroundTasks, _role: str = Depends(auth.require_host)) -> dict:
    """
    Startet eine volle Vorberechnung (precompute.py, feed+calendar) im Hintergrund.
    Dauert 2–5 Minuten. Danach werden die Caches automatisch neu geladen.
    """
    if _precompute_running:
        return {"status": "already_running", "message": "Vorberechnung läuft bereits."}
    background_tasks.add_task(_run_precompute, "full")
    return {"status": "started",
            "message": "Vorberechnung gestartet. Daten in ~2–5 Min. aktuell."}


@app.post("/refresh-feed")
async def trigger_feed_refresh(background_tasks: BackgroundTasks, _role: str = Depends(auth.require_host)) -> dict:
    """US-34: Nur 14-Tage Feed neu berechnen (precompute --feed-only). ~30–60s."""
    if _precompute_running:
        return {"status": "already_running", "message": "Vorberechnung läuft bereits."}
    background_tasks.add_task(_run_precompute, "feed")
    return {"status": "started", "message": "14-Tage Feed wird neu berechnet (~2–5 Min.)."}


@app.post("/refresh-calendar")
async def trigger_calendar_refresh(background_tasks: BackgroundTasks, _role: str = Depends(auth.require_host)) -> dict:
    """US-34: Nur Jahreskalender inkrementell neu berechnen. ~1–3 Min."""
    if _precompute_running:
        return {"status": "already_running", "message": "Vorberechnung läuft bereits."}
    background_tasks.add_task(_run_precompute, "calendar")
    return {"status": "started", "message": "Jahreskalender wird inkrementell neu berechnet (~1–3 Min.)."}


@app.post("/weather-refresh")
async def trigger_weather_refresh(background_tasks: BackgroundTasks, _role: str = Depends(auth.require_host)) -> dict:
    """
    Aktualisiert nur das Wetter-Overlay (T+3 Tage) im Hintergrund.
    Schnell: ~10–15s. Kein precompute nötig.
    """
    background_tasks.add_task(_weather_overlay)
    return {"status": "started", "message": "Wetter-Overlay gestartet (~10s)."}


async def _run_sightline_refresh() -> None:
    """US-09: Manueller Refresh — Sichtachsen-Check für ALLE Locations neu ausführen.

    Analog zu _weather_overlay (Hintergrund-Job, Status via _job_status).
    Läuft sequenziell mit kurzer Pause zwischen Locations (Drosselung der
    externen Overpass-/OpenTopoData-Aufrufe, gleiches Muster wie der
    nächtliche QA-Lauf _QA_PASS_THROTTLE_S) — kein paralleler Sturm auf die
    beiden externen Dienste.
    """
    global _sightline_refresh_running
    t0 = _job_start("sightlines")
    _sightline_refresh_running = True
    try:
        for loc in LOCATIONS:
            try:
                await sightline_calc.update_location_sightline(_store, loc, _elevation_provider)
            except Exception as exc:
                logger.warning("Sichtachsen-Refresh: %s übersprungen (%s)", loc.id, exc)
            await asyncio.sleep(1.0)  # Drosselung externer Dienste
        # Aktualisierten Stand aus dem Store erneut auf LOCATIONS anwenden (Konsistenz
        # mit dem Start-Verhalten von _load_qa_values) und Feed/Kalender-Caches neu laden,
        # damit die neuen Werte sofort in Feed/Kalender-Events sichtbar sind.
        _load_qa_values()
        _load_caches()
        _job_done("sightlines", t0)
    except Exception as exc:
        _job_error("sightlines", t0, str(exc))
        logger.error("Sichtachsen-Refresh fehlgeschlagen: %s", exc)
    finally:
        _sightline_refresh_running = False


@app.post("/sightline-refresh")
async def trigger_sightline_refresh(background_tasks: BackgroundTasks, _role: str = Depends(auth.require_host)) -> dict:
    """US-09: Stößt den Sichtachsen-Check für alle Locations manuell neu an
    (Host-only, analog zu /weather-refresh/-feed/-calendar). Dauert je nach
    Location-Anzahl mehrere Minuten (sequenzielle externe Calls, gedrosselt)."""
    if _sightline_refresh_running:
        return {"status": "already_running", "message": "Sichtachsen-Check läuft bereits."}
    background_tasks.add_task(_run_sightline_refresh)
    return {"status": "started", "message": "Sichtachsen-Check gestartet (kann mehrere Minuten dauern)."}


@app.get("/weather-map")
async def weather_map(hours: int = 72) -> dict:
    """US-112: Metadaten des Wetter-Karten-Overlays (weicher Verlauf, PNG je Stunde).

    Liefert Bounds (für L.imageOverlay), die gemeinsame 72-h-Stundenachse (UTC),
    Quellen-Status, Attribution und — pro Feld — die PNG-URLs je Stunde. Die
    Bilder selbst kommen über /weather-map/png/{field}/{idx}.

    Cache-Verhalten: Ist der Prozess-Cache frisch (< TTL), wird er direkt
    zurückgegeben (kein neuer Fetch). Sonst wird der Bau im Hintergrund
    angestoßen; bis er fertig ist liefert der Endpoint den (ggf. leeren) Stand
    mit `ready=false`, statt den Request zu blockieren.
    """
    global _weather_map_updated_at

    now = datetime.now(timezone.utc)
    fresh = (
        _weather_map_cache is not None
        and _weather_map_updated_at is not None
        and (now - _weather_map_updated_at) < _WEATHER_MAP_TTL
    )

    if not fresh and not _weather_map_building and not _NO_BACKGROUND:
        # Hintergrund-Bau anstoßen (blockiert den Request nicht)
        asyncio.create_task(_build_weather_map())

    if _weather_map_cache is None:
        # Noch nichts gebaut → leere, aber gültige Antwort (Frontend zeigt Hinweis)
        return {
            "ready": False,
            "bounds": weather_grib.overlay_bounds(),
            "hourly_times": [],
            "frames": {"clouds": [], "precip": []},
            "attribution": "Daten: DWD · MET Norway (CC BY 4.0)",
            "attribution_url": "https://www.met.no/en/free-meteorological-data",
            "sources": {"icon_d2": 0, "icon_eu": 0, "met": 0},
        }

    n = len(_weather_map_cache["hourly_times"])
    cloud = _weather_map_png.get("cloud", [])
    precip = _weather_map_png.get("precip", [])
    frames = {
        "clouds": [
            ("/weather-map/png/cloud/%d" % i) if (i < len(cloud) and cloud[i]) else None
            for i in range(n)
        ],
        "precip": [
            ("/weather-map/png/precip/%d" % i) if (i < len(precip) and precip[i]) else None
            for i in range(n)
        ],
    }
    return {
        "ready": True,
        "bounds": _weather_map_cache["bounds"],
        "hourly_times": _weather_map_cache["hourly_times"],
        "frames": frames,
        "attribution": _weather_map_cache["attribution"],
        "attribution_url": _weather_map_cache["attribution_url"],
        "sources": _weather_map_cache["sources"],
        "fetched_at": _weather_map_updated_at.isoformat() if _weather_map_updated_at else None,
    }


@app.get("/weather-map/png/{field}/{idx}")
async def weather_map_png(field: str, idx: int):
    """US-112: Liefert das interpolierte PNG einer Stunde (RGBA, weicher Verlauf)."""
    from fastapi import Response
    if field not in ("cloud", "precip"):
        raise HTTPException(status_code=404, detail="Unbekanntes Feld")
    frames = _weather_map_png.get(field, [])
    if idx < 0 or idx >= len(frames) or not frames[idx]:
        raise HTTPException(status_code=404, detail="Kein Bild für diese Stunde")
    return Response(
        content=frames[idx],
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=1800"},
    )


@app.post("/run-qa-pass")
async def trigger_qa_pass(_role: str = Depends(auth.require_host)) -> dict:
    """TASK-48 (On-Demand): Stößt den nächtlichen QA-Lauf einmalig sofort an.

    Damit lässt sich der QA-Lauf lokal/operativ testen, ohne bis 01:00 zu warten.
    Geschützt wie alle Host-/Admin-Aktionen (Depends(auth.require_host) → Host-Token,
    sonst 401/403). Läuft synchron und gibt eine kompakte Zusammenfassung zurück.

    Single-Flight bleibt: läuft bereits ein QA-Lauf oder ein Recompute, antwortet
    _run_qa_pass() mit status="skipped" (kein paralleler Start).
    """
    summary = await _run_qa_pass()
    if summary is None:
        # Defensiv — _run_qa_pass liefert seit TASK-48 immer ein dict.
        summary = {"status": "completed", "checked": 0, "improved": 0, "failed": 0}
    return summary


@app.get("/job-status")
async def get_job_status() -> dict:
    """US-34: Gibt den aktuellen Status aller Hintergrund-Jobs zurück."""
    return {
        "jobs": _job_status,
        "precompute_running": _precompute_running,
    }


# ---------------------------------------------------------------------------
# US-05: Quick Location Capture
# ---------------------------------------------------------------------------

class PreviewAlignmentRequest(BaseModel):
    observer_lat: float
    observer_lon: float
    subject_lat: float
    subject_lon: float
    subject_name: str = "Unbenannt"
    subject_height_m: float = 0.0
    subject_width_m: float = 0.0
    days: int = 14
    save: bool = False
    category: str = "SKYLINE"  # US-76: LocationCategory-Key, Default = SKYLINE
    special_notes: str = ""  # BUG-65: optionaler Hinweise-Text aus der Anlage-Maske


async def _save_alignment_as_location(
    req: "PreviewAlignmentRequest",
    profile,
    focal_length_mm: int,
) -> Optional[str]:
    """
    Speichert das Alignment-Ergebnis als neue Custom Location.

    Triggert Recompute-Hook (TASK-17) und Backup-Task (TASK-18).
    BUG-35: Gibt die location_id zurück wenn gespeichert, None wenn Bedingung nicht erfüllt.
    """
    if not (req.save and req.subject_name and req.subject_name != "Unbenannt"):
        return None

    place = await _reverse_geocode(req.observer_lat, req.observer_lon)
    dist_m = round(profile.ground_distance_m)
    dist_txt = f"{dist_m // 1000},{dist_m % 1000 // 100} km" if dist_m >= 1000 else f"{dist_m} m"
    if place:
        desc = f"Blick vom {place} auf {req.subject_name}, {dist_txt} Entfernung."
    else:
        desc = f"Sichtachse auf {req.subject_name}, {dist_txt} Entfernung."

    new_loc = PhotoLocation(
        id=f"custom_{int(datetime.now().timestamp() * 1000)}",
        name=req.subject_name,
        description=desc,
        category=LocationCategory[req.category] if req.category in LocationCategory.__members__ else LocationCategory.SKYLINE,  # US-76
        observer_lat=req.observer_lat, observer_lon=req.observer_lon,
        subject_lat=req.subject_lat, subject_lon=req.subject_lon,
        subject_name=req.subject_name,
        subject_height_m=req.subject_height_m, subject_width_m=req.subject_width_m,
        distance_m=dist_m,
        focal_length_suggestions=[focal_length_mm],
        special_notes=req.special_notes,  # BUG-65: Nutzer-Hinweistext aus der Anlage-Maske durchreichen (BUG-60: weiterhin keine automatische Notiz)
        difficulty=1,
    )
    LOCATIONS.append(new_loc)
    _save_custom_location(new_loc)
    # BUG-35: Recompute als pending markieren bevor Task startet
    _recompute_pending.add(new_loc.id)
    # TASK-17: Recompute-Hook auch für neue Custom Locations triggern (war vorher missing)
    asyncio.create_task(_run_precompute_single(new_loc.id))
    # US-106 Teil 2: neue Location zeitnah auch im Entdecken-Bereich
    _trigger_discover_debounced()
    # TASK-18: Backup nach Create
    asyncio.create_task(asyncio.to_thread(backup.backup_after_edit, new_loc.id))
    return new_loc.id


@app.post("/preview-alignment")
async def preview_alignment(req: PreviewAlignmentRequest, _role: str = Depends(auth.require_auth)) -> dict:
    if not (-90 <= req.observer_lat <= 90 and -180 <= req.observer_lon <= 180):
        raise HTTPException(status_code=400, detail="Ungültige Fotograf-Koordinaten.")
    if not (-90 <= req.subject_lat <= 90 and -180 <= req.subject_lon <= 180):
        raise HTTPException(status_code=400, detail="Ungültige Motiv-Koordinaten.")

    # BUG-66: Geländeunterschied genau einmal pro Anfrage ermitteln (nicht in der
    # Alignment-Schleife weiter unten) und in die Winkelberechnung einfließen lassen.
    # Fehlende DEM-Abdeckung liefert automatisch (0.0, incomplete=True) statt Crash.
    elevation_difference_m, _elevation_incomplete = await _elevation_provider.elevation_difference(
        req.observer_lat, req.observer_lon, req.subject_lat, req.subject_lon)

    profile = calculate_subject_angular_profile(
        observer_lat=req.observer_lat, observer_lon=req.observer_lon,
        subject_lat=req.subject_lat, subject_lon=req.subject_lon,
        subject_height_m=req.subject_height_m, subject_width_m=req.subject_width_m,
        elevation_difference_m=elevation_difference_m,
    )

    if profile.angular_width_deg > 0.01:
        half_fov_rad = math.radians(profile.angular_width_deg * 5 / 2)
        fl_ideal = (36 / 2) / math.tan(half_fov_rad)
        standard_fls = [28, 35, 50, 75, 90, 135, 200, 280, 400, 560]
        focal_length_mm = min(standard_fls, key=lambda f: abs(f - fl_ideal))
    elif profile.ground_distance_m < 500:
        focal_length_mm = 50
    elif profile.ground_distance_m < 2000:
        focal_length_mm = 135
    else:
        focal_length_mm = 280

    today = date.today()
    days = min(req.days, 14)

    def _compute_alignments() -> list:
        # BUG-63 Option A (TASK-48-Muster): reine Rechenschleife, wird unten per
        # asyncio.to_thread aus dem Event-Loop ausgelagert — zusätzliche
        # Absicherung, falls sie unter Last doch spürbar blockiert.
        result = []
        for body in ("sun", "moon"):
            for day_offset in range(days):
                target_date = today + timedelta(days=day_offset)
                try:
                    aligns = find_precise_alignment_times(
                        observer_lat=req.observer_lat, observer_lon=req.observer_lon,
                        subject_lat=req.subject_lat, subject_lon=req.subject_lon,
                        subject_height_m=req.subject_height_m, subject_width_m=req.subject_width_m,
                        target_date=target_date, body=body,
                        az_tolerance_deg=4.0, min_quality=0.15,
                    )
                    result.extend(aligns)
                except Exception as e:
                    logger.debug("Alignment-Fehler %s %s: %s", body, target_date, e)
        return result

    # BUG-63 Option B: Fenster-Engine aktivieren (Muster wie main.py ~2381/~2468),
    # damit find_precise_alignment_times() den schnellen, bereits vorhandenen
    # WindowEphemeris-Pfad statt des langsameren Alt-Pfads nutzt. try/finally
    # garantiert, dass der globale Fenster-State auch bei einer Exception
    # zurückgesetzt wird (Pre-Mortem-Szenario 4).
    from calculations.window_engine import WindowEphemeris
    import calculations.astronomy as _astro
    _astro.set_active_window(WindowEphemeris(req.observer_lat, req.observer_lon, today, days))
    try:
        all_alignments = await asyncio.to_thread(_compute_alignments)
    finally:
        _astro.clear_active_window()

    all_alignments.sort(key=lambda a: a.time)

    saved = await _save_alignment_as_location(req, profile, focal_length_mm)

    return {
        "profile": {
            "azimuth_deg": round(profile.azimuth_deg, 2),
            "ground_distance_m": round(profile.ground_distance_m, 1),
            "angular_altitude_base_deg": round(profile.angular_altitude_base_deg, 3),
            "angular_altitude_top_deg": round(profile.angular_altitude_top_deg, 3),
            "angular_width_deg": round(profile.angular_width_deg, 3),
        },
        "focal_length_mm": focal_length_mm,
        "alignments": [
            {
                "time": a.time.isoformat(),
                "body": a.body,
                "alignment_type": a.alignment_type,
                "celestial_azimuth": round(a.celestial_azimuth, 2),
                "celestial_altitude": round(a.celestial_altitude, 3),
                "azimuth_offset_deg": round(a.azimuth_offset_deg, 2),
                "altitude_offset_deg": round(a.altitude_offset_deg, 3),
                "quality_score": round(a.quality_score, 3),
            }
            for a in all_alignments[:30]
        ],
        "saved": saved is not None,
        "location_id": saved,  # BUG-35: ID für Frontend-Polling
    }


# ---------------------------------------------------------------------------
# BUG-35: Recompute-Status-Endpoint
# ---------------------------------------------------------------------------

@app.get("/recompute-status")
async def recompute_status() -> dict:
    """BUG-35 / US-106: Gibt IDs zurück für die ein Recompute noch aussteht.

    US-106: Eine ID bleibt jetzt so lange in 'pending', bis für die Location
    Feed UND Wetter stehen (nicht mehr schon nach dem Feed-Write). Das Frontend-
    Banner ('wird aktualisiert') folgt dieser Liste und verschwindet daher erst,
    wenn die Location wirklich vollständig fertig ist. In-memory, kein Auth nötig.
    """
    return {"pending": list(_recompute_pending), "running": _precompute_running}


# ---------------------------------------------------------------------------
# Reverse Geocoding + Location-Edit (US-57 / C+B)
# ---------------------------------------------------------------------------

@app.get("/reverse-geocode")
async def reverse_geocode_endpoint(lat: float, lon: float) -> dict:
    """Gibt Ortsnamen für Koordinaten via Nominatim zurück."""
    place = await _reverse_geocode(lat, lon)
    return {"place": place}


# ---------------------------------------------------------------------------
# US-120: Beispielbild-Upload (nur Host) — Datei-Upload statt JSON-PATCH
# ---------------------------------------------------------------------------

def _process_uploaded_image(raw: bytes) -> bytes:
    """
    Verarbeitet ein hochgeladenes Bild serverseitig (Pre-Mortem 1 + Rule 3):
    - EXIF-Ausrichtungskorrektur (ImageOps.exif_transpose): dreht die Pixel gemäß
      der im Foto gespeicherten Kamera-Ausrichtung, statt sich auf das (von vielen
      Anzeigeprogrammen ignorierte) EXIF-Orientation-Tag zu verlassen.
    - Verkleinerung auf max. _IMAGE_MAX_DIMENSION_PX an der langen Kante.
    - Iterative JPEG-Kompression bis ca. _IMAGE_TARGET_BYTES erreicht ist.
    Wirft ValueError bei ungültigen/nicht dekodierbaren Bilddaten (→ 400 im Endpoint).
    """
    try:
        img = Image.open(_io.BytesIO(raw))
        img.load()  # erzwingt vollständiges Decodieren (deckt kaputte/Fake-Bilddateien auf)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Datei ist kein gültiges Bild: {exc}") from exc

    # EXIF-Ausrichtung anwenden, dann Tag entfernen (Pixel sind jetzt schon richtig herum)
    img = ImageOps.exif_transpose(img)

    # In RGB konvertieren (JPEG kennt kein Alpha/Palette; PNG mit Transparenz → weißer Hintergrund)
    if img.mode not in ("RGB", "L"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1])
        else:
            bg.paste(img.convert("RGB"))
        img = bg
    elif img.mode == "L":
        img = img.convert("RGB")

    # Auf sinnvolle Maximalmaße verkleinern (Seitenverhältnis bleibt erhalten)
    if max(img.size) > _IMAGE_MAX_DIMENSION_PX:
        img.thumbnail((_IMAGE_MAX_DIMENSION_PX, _IMAGE_MAX_DIMENSION_PX), Image.LANCZOS)

    # Iterative Qualitätsreduktion bis Zielgröße erreicht oder Qualität-Untergrenze
    quality = 88
    buf = _io.BytesIO()
    while True:
        buf.seek(0)
        buf.truncate(0)
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        if buf.tell() <= _IMAGE_TARGET_BYTES or quality <= 40:
            break
        quality -= 8

    return buf.getvalue()


def _resolve_location_image_dir_name(loc_id: str) -> str:
    """Dateiname für das Beispielbild einer Location (eindeutig, kollisionsfrei)."""
    return f"{loc_id}.jpg"


def _delete_location_image_file(filename: Optional[str]) -> None:
    """Löscht eine vorhandene Bilddatei aktiv (Pre-Mortem 2: keine verwaisten Dateien)."""
    if not filename:
        return
    try:
        path = _IMAGE_DIR / filename
        if path.exists():
            path.unlink()
            logger.info("Altes Beispielbild gelöscht: %s", filename)
    except Exception as exc:
        logger.warning("Konnte altes Beispielbild nicht löschen (%s): %s", filename, exc)


def _delete_location_qa_data(loc_id: str) -> None:
    """TASK-77: Entfernt QA-Zustand/-Werte einer gelöschten Location (best effort,
    gleiches Muster wie _delete_location_image_file — schlägt der Aufruf fehl,
    wird nur gewarnt, der restliche Löschvorgang bleibt unberührt)."""
    try:
        _store.delete_qa(loc_id)
    except Exception as exc:
        logger.warning("Konnte QA-Daten nicht entfernen (%s): %s", loc_id, exc)


@app.post("/locations/{loc_id}/image")
async def upload_location_image(
    loc_id: str,
    file: UploadFile = File(...),
    _role: str = Depends(auth.require_host),
) -> dict:
    """
    US-120: Lädt ein Beispielbild für eine Location hoch (nur Host).
    - Nimmt Dateien bis zur harten Obergrenze an (_IMAGE_HARD_LIMIT_BYTES), lehnt
      deutlich überdimensionierte Uploads klar ab, bevor Rechenzeit investiert wird.
    - Verarbeitet das Bild serverseitig (EXIF-Ausrichtung, Verkleinerung, Kompression).
    - Speichert die Datei zuerst vollständig auf der Festplatte, aktualisiert danach
      erst den Verweis in der Location (Pre-Mortem 3: keine Lese-vor-Schreib-Lücke).
    - Löscht die alte Bilddatei aktiv, falls vorhanden (Pre-Mortem 2).
    """
    target_loc = next((l for l in LOCATIONS if l.id == loc_id), None)
    if not target_loc:
        raise HTTPException(status_code=404, detail="Location nicht gefunden.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Datei ist leer.")
    if len(raw) > _IMAGE_HARD_LIMIT_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Datei zu groß ({len(raw) // 1024} KB). Maximal {_IMAGE_HARD_LIMIT_BYTES // (1024*1024)} MB pro Upload erlaubt.",
        )

    try:
        processed = _process_uploaded_image(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    old_filename = getattr(target_loc, "image_filename", None)
    new_filename = _resolve_location_image_dir_name(loc_id)
    new_path = _IMAGE_DIR / new_filename

    # Erst vollständig schreiben, dann Verweis aktualisieren (Pre-Mortem 3)
    tmp_path = new_path.with_suffix(".tmp")
    tmp_path.write_bytes(processed)
    tmp_path.replace(new_path)  # atomarer Rename auf demselben Dateisystem

    # Verweis in der Location aktualisieren (beide Location-Arten).
    # US-126 Rule 3: Fokuspunkt bezieht sich auf das alte Bild und wird bei jedem
    # Ersetzen zurückgesetzt (NULL → Anzeige fällt auf Bildmitte 50/50 zurück),
    # damit kein "Geister"-Ausschnitt vom vorherigen Bild übernommen wird.
    if loc_id.startswith("custom_"):
        _store.update_custom(loc_id, image_filename=new_filename, image_focus_x=None, image_focus_y=None)
    else:
        _save_location_override(loc_id, image_filename=new_filename, image_focus_x=None, image_focus_y=None)
    target_loc.image_filename = new_filename
    target_loc.image_focus_x = None
    target_loc.image_focus_y = None

    # Alte Datei erst NACH erfolgreichem Ersetzen löschen, und nur wenn sie
    # tatsächlich einen anderen Namen hatte (hier immer gleich, da Dateiname == loc_id;
    # Pre-Mortem 2 bleibt trotzdem relevant falls das Namensschema sich künftig ändert)
    if old_filename and old_filename != new_filename:
        _delete_location_image_file(old_filename)

    if not _NO_BACKGROUND:
        asyncio.create_task(asyncio.to_thread(backup.backup_after_edit, loc_id))

    logger.info("Beispielbild hochgeladen für %s: %s (%d Bytes)", loc_id, new_filename, len(processed))
    return {"ok": True, "image_url": f"/location-images/{new_filename}", "size_bytes": len(processed)}


@app.delete("/locations/{loc_id}/image")
async def delete_location_image(loc_id: str, _role: str = Depends(auth.require_host)) -> dict:
    """
    US-125: Löscht das Beispielbild einer Location eigenständig (nur Host),
    ohne dass gleich die ganze Location gelöscht oder ein Ersatzbild hochgeladen
    werden muss.
    - Wiederverwendet die in US-120 gebaute _delete_location_image_file() (Pre-Mortem 2:
      keine verwaisten Dateien), statt eine eigene Lösch-Logik zu duplizieren.
    - Setzt image_filename auf der Location zurück (beide Location-Arten), analog zum
      bestehenden Aktualisierungs-Muster in upload_location_image / delete_location.
    - Edge Case (AK 7): Location ohne aktuell vorhandenes Bild → 404 statt Absturz.
    - Edge Case (AK 8): Location-ID existiert nicht → 404 "Location nicht gefunden".
    """
    target_loc = next((l for l in LOCATIONS if l.id == loc_id), None)
    if not target_loc:
        raise HTTPException(status_code=404, detail="Location nicht gefunden.")

    old_filename = getattr(target_loc, "image_filename", None)
    if not old_filename:
        raise HTTPException(status_code=404, detail="Diese Location hat aktuell kein Beispielbild.")

    # Verweis zuerst zurücksetzen (beide Location-Arten), danach Datei löschen —
    # gleiche Reihenfolge wie beim Ersetzen/Location-Löschen bereits etabliert.
    if loc_id.startswith("custom_"):
        _store.update_custom(loc_id, image_filename=None)
    else:
        _save_location_override(loc_id, image_filename=None)
    target_loc.image_filename = None

    _delete_location_image_file(old_filename)

    if not _NO_BACKGROUND:
        asyncio.create_task(asyncio.to_thread(backup.backup_after_edit, loc_id))

    logger.info("Beispielbild gelöscht für %s: %s", loc_id, old_filename)
    return {"ok": True, "deleted": True}


@app.patch("/locations/{loc_id}/image-focus")
async def update_location_image_focus(
    loc_id: str, body: dict = Body(...), _role: str = Depends(auth.require_host)
) -> dict:
    """
    US-126: Setzt/aktualisiert den Fokuspunkt für den angezeigten Bildausschnitt
    (nur Host). Rein clientseitige Anzeigeposition — das Originalbild bleibt
    unverändert, es wird nur die Position (Prozentwerte 0-100) persistiert.
    - Jederzeit nutzbar, auch nachträglich für Bilder, die schon vor diesem Ticket
      hochgeladen wurden (kein Kopplung an den Upload-Vorgang).
    - Gilt für Custom- UND Standard-Locations gleichermaßen (analog image_filename).
    - Edge Case: Location ohne Beispielbild → 404 (Fokuspunkt ohne Bild ergibt keinen Sinn).
    """
    target_loc = next((l for l in LOCATIONS if l.id == loc_id), None)
    if not target_loc:
        raise HTTPException(status_code=404, detail="Location nicht gefunden.")

    if not getattr(target_loc, "image_filename", None):
        raise HTTPException(status_code=404, detail="Diese Location hat aktuell kein Beispielbild.")

    x = body.get("image_focus_x")
    y = body.get("image_focus_y")
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise HTTPException(status_code=422, detail="image_focus_x/image_focus_y müssen Zahlen sein.")
    if not (0 <= x <= 100) or not (0 <= y <= 100):
        raise HTTPException(status_code=422, detail="image_focus_x/image_focus_y müssen zwischen 0 und 100 liegen.")
    x, y = float(x), float(y)

    if loc_id.startswith("custom_"):
        _store.update_custom(loc_id, image_focus_x=x, image_focus_y=y)
    else:
        _save_location_override(loc_id, image_focus_x=x, image_focus_y=y)
    target_loc.image_focus_x = x
    target_loc.image_focus_y = y

    if not _NO_BACKGROUND:
        asyncio.create_task(asyncio.to_thread(backup.backup_after_edit, loc_id))

    logger.info("Bildausschnitt-Fokuspunkt gesetzt für %s: (%.1f, %.1f)", loc_id, x, y)
    return {"ok": True, "image_focus_x": x, "image_focus_y": y}


def _validate_patch_fields(allowed: dict) -> dict:
    """TASK-60 (aus patch_location extrahiert): Validiert + normalisiert die PATCH-Feldwerte
    (Koordinaten ±90°/±180°, numerische Felder inkl. float-Cast, focal_length_suggestions
    inkl. int-Cast 8–1200mm). Wirft HTTPException(422) bei ungültigen Werten. Gibt den
    normalisierten Dict zurück — MUSS vor dem target_loc-Lookup in patch_location() aufgerufen
    werden, sonst kippt die Fehler-Präzedenz für ungültige Felder gegen eine nicht-existente
    loc_id von 422 auf 404."""
    # Koordinaten validieren
    for f in COORD_FIELDS & allowed.keys():
        val = allowed[f]
        if not isinstance(val, (int, float)):
            raise HTTPException(status_code=422, detail=f"{f} muss eine Zahl sein.")
        if "lat" in f and not (-90 <= val <= 90):
            raise HTTPException(status_code=422, detail=f"{f} außerhalb ±90°.")
        if "lon" in f and not (-180 <= val <= 180):
            raise HTTPException(status_code=422, detail=f"{f} außerhalb ±180°.")

    # Numerische Felder validieren: observer_floor_height_m (US-62), subject_height_m/
    # subject_width_m (US-128) — Zahl, ≥ 0, 0 ist ein gültiger Bestandswert (z.B.
    # geltow_havelblick ohne vertikales Motiv).
    for f in NUMERIC_FIELDS & allowed.keys():
        val = allowed[f]
        if not isinstance(val, (int, float)):
            raise HTTPException(status_code=422, detail=f"{f} muss eine Zahl sein.")
        if val < 0:
            raise HTTPException(status_code=422, detail=f"{f} muss ≥ 0 sein.")
        allowed[f] = float(val)

    # focal_length_suggestions validieren (BUG-22)
    if "focal_length_suggestions" in allowed:
        val = allowed["focal_length_suggestions"]
        if not isinstance(val, list):
            raise HTTPException(status_code=422, detail="focal_length_suggestions muss eine Liste sein.")
        parsed = []
        for v in val:
            if not isinstance(v, (int, float)) or not (8 <= v <= 1200):
                raise HTTPException(status_code=422, detail=f"Brennweite {v} ungültig (8–1200 mm).")
            parsed.append(int(v))
        allowed["focal_length_suggestions"] = parsed

    return allowed


def _compute_patch_persist_fields(allowed: dict) -> dict:
    """TASK-60 (aus patch_location extrahiert): US-128 (Frage 1, Option B) — eine bewusste
    Korrektur von subject_height_m markiert den Wert als recherchiert, nicht mehr als
    unbearbeiteten Locationscout-Import-Platzhalter (discover/subjects.py:_is_placeholder()).
    Bewusst getrennt von `allowed` gehalten, damit dieser interne Seiteneffekt-Flag nicht in
    der API-Response ("updated") auftaucht."""
    if "subject_height_m" in allowed:
        return dict(allowed, subject_height_researched=True)
    return allowed


def _persist_location_patch(loc_id: str, persist_fields: dict) -> None:
    """TASK-60 (aus patch_location extrahiert): Custom-/Standard-Location-Verzweigung für die
    Persistierung eines PATCH. Wirft HTTPException(404) wenn eine Custom-Location nicht in der
    Datei/DB gefunden wird."""
    if loc_id.startswith("custom_"):
        # subject_height_researched ist keine Spalte in custom_locations (Custom-Locations
        # werden nie mit False angelegt, Default bleibt beim Neu-Laden ohnehin True) — nicht an
        # die dynamische SQL-UPDATE-Kwargs durchreichen, sonst "no such column"-Fehler.
        db_fields = {k: v for k, v in persist_fields.items() if k != "subject_height_researched"}
        ok = _update_custom_location_file(loc_id, **db_fields)
        if not ok:
            raise HTTPException(status_code=404, detail="Custom Location nicht in Datei gefunden.")
    else:
        # Standard-Location: Overrides in SQLite persistieren (location_overrides speichert
        # Felder generisch als JSON-Blob, kein Schema-Problem für subject_height_researched).
        _save_location_override(loc_id, **persist_fields)


def _trigger_patch_recompute(loc_id: str, allowed: dict) -> bool:
    """TASK-60 (aus patch_location extrahiert): TASK-12 — Koordinaten oder
    observer_floor_height_m geändert → Single-Location Recompute anstoßen. Gibt
    needs_recompute für die Response zurück."""
    needs_recompute = bool(RECOMPUTE_TRIGGER_FIELDS & allowed.keys())
    if needs_recompute:
        logger.info("Recompute-relevante Felder für '%s' geändert – starte Single-Location Recompute", loc_id)
        _recompute_pending.add(loc_id)  # US-106: sofort pending, damit Banner ehrlich bleibt
        asyncio.create_task(_run_precompute_single(loc_id))
        _trigger_discover_debounced()  # US-106 Teil 2: Entdecken zieht zeitnah nach
    return needs_recompute


@app.patch("/locations/{loc_id}")
async def patch_location(loc_id: str, body: dict = Body(...), _role: str = Depends(auth.require_auth)) -> dict:
    """Aktualisiert Felder einer Location (alle Typen; Koordinaten + Name + Beschreibung + Höhenkorrektur)."""
    # US-128: Die drei vormals redundant gepflegten Feld-Listen (hier + main.py
    # _load_location_overrides + precompute.py _OVERRIDE_FIELDS) sind jetzt aus
    # data/locations.py:LOCATION_FIELD_RULES abgeleitet (eine gemeinsame Quelle).
    all_allowed_fields = PATCHABLE_LOCATION_FIELDS
    allowed = {k: v for k, v in body.items() if k in all_allowed_fields}
    if not allowed:
        raise HTTPException(status_code=400, detail="Keine gültigen Felder (name, description, special_notes, subject_name, observer_lat/lon, subject_lat/lon, observer_floor_height_m, subject_height_m, subject_width_m, focal_length_suggestions).")

    # TASK-60: Validierung MUSS vor dem target_loc-Lookup laufen — sonst kippt die
    # Fehlerantwort für ungültige Felder bei einer nicht-existenten loc_id von 422 auf 404.
    allowed = _validate_patch_fields(allowed)

    # In-Memory-Location suchen
    target_loc = next((l for l in LOCATIONS if l.id == loc_id), None)
    if not target_loc:
        raise HTTPException(status_code=404, detail="Location nicht gefunden.")

    persist_fields = _compute_patch_persist_fields(allowed)
    _persist_location_patch(loc_id, persist_fields)

    # In-Memory-Liste aktualisieren (inkl. Seiteneffekt-Flag, falls gesetzt)
    for k, v in persist_fields.items():
        setattr(target_loc, k, v)

    needs_recompute = _trigger_patch_recompute(loc_id, allowed)

    # TASK-18: Backup nach jedem erfolgreichen Edit (im Test-Modus aus – keine Git-Operationen)
    if not _NO_BACKGROUND:
        asyncio.create_task(asyncio.to_thread(backup.backup_after_edit, loc_id))

    return {"ok": True, "updated": allowed, "recompute_triggered": needs_recompute}


# ---------------------------------------------------------------------------
# Location Delete (US-68 Slice 1 — nur Host)
# ---------------------------------------------------------------------------

@app.delete("/locations/{loc_id}", status_code=200)
async def delete_location(loc_id: str, _role: str = Depends(auth.require_host)) -> dict:
    """
    US-68 Slice 1: Löscht eine Location sofort (nur Host, kein Approval).
    - Custom Locations: aus SQLite entfernen.
    - Standard Locations: Tombstone-Override setzen (deleted=True); beim nächsten
      Server-Start wird die Location in _load_location_overrides herausgefiltert.
    In beiden Fällen: sofort aus LOCATIONS und Feed-/Kalender-Cache entfernen.
    """
    global _feed_cache, _calendar_cache

    target = next((l for l in LOCATIONS if l.id == loc_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Location nicht gefunden.")

    # US-120-Nachtrag: Dateiname des Beispielbilds vor dem Löschen sichern,
    # damit die zugehörige Datei danach mitentfernt werden kann (beide Location-Arten).
    image_filename = getattr(target, "image_filename", None)

    if loc_id.startswith("custom_"):
        ok = _store.delete_custom(loc_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Custom Location nicht in DB gefunden.")
    else:
        # Standard-Location: Tombstone damit der Neustart sie herausfiltert
        _store.upsert_override(loc_id, deleted=True)

    # TASK-77: QA-Zustand/-Werte für beide Löscharten gemeinsam bereinigen
    # (best effort, siehe _delete_location_qa_data — blockiert den Löschvorgang nicht)
    _delete_location_qa_data(loc_id)

    # Aus In-Memory-Liste entfernen
    LOCATIONS[:] = [l for l in LOCATIONS if l.id != loc_id]

    # US-120-Nachtrag: verwaiste Bilddatei entfernen, falls vorhanden (Pre-Mortem 2,
    # gleiches Muster wie beim Ersetzen eines Bildes in upload_location_image)
    _delete_location_image_file(image_filename)

    # Feed- und Kalender-Cache bereinigen (Events dieser Location)
    _feed_cache     = [e for e in _feed_cache     if e.get("location_id") != loc_id]
    _calendar_cache = [e for e in _calendar_cache if e.get("location_id") != loc_id]

    if not _NO_BACKGROUND:
        asyncio.create_task(asyncio.to_thread(backup.backup_after_edit, loc_id))

    logger.info("Location gelöscht (Host): %s", loc_id)
    return {"ok": True, "deleted": True, "id": loc_id}


# ---------------------------------------------------------------------------
# Location Verifications (BUG-26)
# ---------------------------------------------------------------------------

class VerificationIn(BaseModel):
    location_name: str = ""
    status: str          # 'ok' | 'issue'
    issue_type: str = ""
    comment: str = ""
    date: str            # YYYY-MM-DD


@app.get("/verifications")
async def get_all_verifications() -> list[dict]:
    """Gibt alle Verifikationen (alle Locations) zurück — für Frontend-Cache-Preload. Kein Auth."""
    with _store._connect() as conn:
        rows = conn.execute(
            "SELECT id, location_id, location_name, status, issue_type, comment, date "
            "FROM location_verifications ORDER BY id ASC"
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/locations/{loc_id}/verifications")
async def get_verifications(loc_id: str) -> list[dict]:
    """Gibt alle Verifikationen für eine Location zurück (älteste zuerst). Kein Auth nötig."""
    return _store.get_verifications(loc_id)


@app.post("/locations/{loc_id}/verifications", status_code=201)
async def add_verification(loc_id: str, body: VerificationIn,
                           _role: str = Depends(auth.require_auth)) -> dict:
    """Speichert eine neue Verifikation (user + host)."""
    if body.status not in ("ok", "issue"):
        raise HTTPException(status_code=422, detail="status muss 'ok' oder 'issue' sein.")
    new_id = _store.add_verification(
        location_id=loc_id,
        location_name=body.location_name,
        status=body.status,
        issue_type=body.issue_type,
        comment=body.comment,
        date=body.date,
    )
    return {"ok": True, "id": new_id}


@app.delete("/locations/{loc_id}/verifications/last", status_code=200)
async def delete_last_verification(loc_id: str, _role: str = Depends(auth.require_auth)) -> dict:
    """Löscht den neuesten Verifikationseintrag für eine Location."""
    found = _store.delete_last_verification(loc_id)
    if not found:
        raise HTTPException(status_code=404, detail="Keine Verifikation gefunden.")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Location Ratings (US-89)
# ---------------------------------------------------------------------------

class RatingIn(BaseModel):
    value: int
    device_id: str


@app.get("/ratings")
async def get_all_ratings() -> list[dict]:
    """
    Gibt alle Roh-Bewertungen (alle Locations, alle Geräte) zurück —
    für den Frontend-Boot-Cache. Kein Auth. Frontend aggregiert client-seitig
    und leitet `mine` aus dem eigenen device_id ab (analog /verifications).
    """
    return _store.load_all_ratings()


@app.get("/locations/{loc_id}/ratings")
async def get_ratings(loc_id: str, device_id: str = "") -> dict:
    """
    Aggregat einer Location: {count, avg, mine}. Kein Auth.
    avg auf 1 Nachkommastelle, null bei count=0. mine = Wert des Geräts oder null.
    """
    return _store.get_rating_summary(loc_id, device_id or None)


@app.post("/locations/{loc_id}/ratings", status_code=201)
async def upsert_rating(loc_id: str, body: RatingIn,
                        _role: str = Depends(auth.require_auth)) -> dict:
    """Speichert/aktualisiert die Bewertung eines Geräts (Upsert). value 1–5."""
    if body.value < 1 or body.value > 5:
        raise HTTPException(status_code=422, detail="value muss zwischen 1 und 5 liegen.")
    if not body.device_id:
        raise HTTPException(status_code=422, detail="device_id ist erforderlich.")
    updated = datetime.now(timezone.utc).isoformat()
    _store.upsert_rating(
        location_id=loc_id,
        device_id=body.device_id,
        value=body.value,
        updated=updated,
    )
    return {"ok": True, **_store.get_rating_summary(loc_id, body.device_id)}


@app.delete("/locations/{loc_id}/ratings", status_code=200)
async def delete_rating(loc_id: str, device_id: str = "",
                        _role: str = Depends(auth.require_auth)) -> dict:
    """Löscht die Bewertung des aufrufenden Geräts. device_id als Query-Param."""
    if not device_id:
        raise HTTPException(status_code=422, detail="device_id ist erforderlich.")
    _store.delete_rating(loc_id, device_id)
    return {"ok": True, **_store.get_rating_summary(loc_id, device_id)}


# ---------------------------------------------------------------------------
# Camera Profiles (US-90)
# ---------------------------------------------------------------------------

_VALID_SENSORS = {"fullframe", "apsc_canon", "apsc_sony", "mft", "one_inch"}
_VALID_ORI = {"landscape", "portrait"}


class CameraProfileIn(BaseModel):
    device_id: str
    sensor: str
    fl: int
    ori: str


@app.get("/camera-profile")
async def get_camera_profile(device_id: str = "") -> dict:
    """
    Gibt das Kamera-Profil eines Geräts zurück.
    Unbekanntes Gerät → {} (HTTP 200, kein 404 — Frontend fällt auf Default zurück).
    Kein Auth erforderlich.
    """
    if not device_id:
        return {}
    profile = _store.get_camera_profile(device_id)
    return profile if profile is not None else {}


@app.post("/camera-profile", status_code=201)
async def upsert_camera_profile(
    body: CameraProfileIn,
    _role: str = Depends(auth.require_auth),
) -> dict:
    """Speichert/aktualisiert das Kamera-Profil eines Geräts (Upsert). Auth erforderlich."""
    if not body.device_id:
        raise HTTPException(status_code=422, detail="device_id ist erforderlich.")
    if body.sensor not in _VALID_SENSORS:
        raise HTTPException(
            status_code=422,
            detail=f"sensor muss einer von {sorted(_VALID_SENSORS)} sein."
        )
    if body.fl < 8 or body.fl > 1200:
        raise HTTPException(status_code=422, detail="fl muss zwischen 8 und 1200 liegen.")
    if body.ori not in _VALID_ORI:
        raise HTTPException(
            status_code=422,
            detail=f"ori muss einer von {sorted(_VALID_ORI)} sein."
        )
    updated = datetime.now(timezone.utc).isoformat()
    _store.upsert_camera_profile(
        device_id=body.device_id,
        sensor=body.sensor,
        fl=body.fl,
        ori=body.ori,
        updated=updated,
    )
    return {"ok": True, "sensor": body.sensor, "fl": body.fl, "ori": body.ori}


# ---------------------------------------------------------------------------
# Static Files (PWA) – muss NACH allen API-Routen kommen
# ---------------------------------------------------------------------------
import os, pathlib
from fastapi.responses import FileResponse

_web_dir = pathlib.Path(__file__).parent.parent / "web"

# sw.js explizit mit no-cache ausliefern, damit Browser-HTTP-Cache
# nie eine veraltete SW-Version einfriert (behebt 304-Problem)
@app.get("/sw.js")
async def service_worker() -> FileResponse:
    return FileResponse(
        str(_web_dir / "sw.js"),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )

# US-120: Beispielbilder ausliefern — eigenes Verzeichnis, eigener Mount-Punkt,
# muss ebenfalls vor dem catch-all "/"-Mount stehen (StaticFiles matcht sonst nie).
# Cache-Control: Bild wird beim Ersetzen umbenannt? Nein (fester Dateiname je Location) —
# daher kurze TTL statt "immutable", damit ein Ersetzen zeitnah im Browser ankommt.
app.mount(
    "/location-images",
    StaticFiles(directory=str(_IMAGE_DIR)),
    name="location-images",
)

if _web_dir.exists():
    app.mount("/", StaticFiles(directory=str(_web_dir), html=True), name="web")
    logger.info("PWA Web-App wird ausgeliefert aus: %s", _web_dir)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
