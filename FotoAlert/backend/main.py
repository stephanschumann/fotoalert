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
import math
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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
from calculations.weather import fetch_weather_forecast, calculate_photo_weather_score, wmo_code_to_description
from data.locations import LOCATIONS, get_location_by_id, PhotoLocation, LocationCategory
from data.store import LocationStore
from data import backup
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
    description="Intelligente Foto-Chancen für Berlin & Brandenburg",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
_precompute_running: bool = False
_recompute_pending:  set  = set()   # BUG-35: IDs mit laufendem/ausstehendem Recompute

# Job-Status-Tracking (US-34)
_job_status: dict = {
    "weather":  {"status": "idle", "last_run": None, "last_error": None, "duration_s": None},
    "feed":     {"status": "idle", "last_run": None, "last_error": None, "duration_s": None},
    "calendar": {"status": "idle", "last_run": None, "last_error": None, "duration_s": None},
}

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
    """Ergänzt subject_lat/lon aus LOCATIONS falls im Cache noch nicht vorhanden."""
    loc_map = {loc.id: loc for loc in LOCATIONS}
    for e in events:
        if "subject_lat" not in e:
            loc = loc_map.get(e.get("location_id", ""))
            if loc:
                e["subject_lat"] = loc.subject_lat
                e["subject_lon"] = loc.subject_lon


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

    # BUG-35: Pending-Cleanup — IDs entfernen die jetzt Events im Feed haben
    if _recompute_pending:
        ids_in_feed = {e["location_id"] for e in _feed_cache}
        cleared = _recompute_pending & ids_in_feed
        _recompute_pending -= ids_in_feed
        if cleared:
            logger.info("Recompute-Pending bereinigt: %s", cleared)

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
    """Führt die Scout-Pipeline aus und aktualisiert _discover_cache."""
    global _discover_cache
    from discover.pipeline import refresh_discover_cache
    try:
        logger.info("Scout-Pipeline startet...")
        await refresh_discover_cache(_DISCOVER_CACHE)
        _load_discover_cache()
    except Exception as e:
        logger.error("Scout-Pipeline fehlgeschlagen: %s", e)


# ---------------------------------------------------------------------------
# Wetter-Overlay
# ---------------------------------------------------------------------------

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
        return

    # Unique Locations aus den nahen Events
    seen: set[str] = set()
    loc_forecasts: dict[str, object] = {}
    for e in near_events:
        key = f"{e['observer_lat']:.3f},{e['observer_lon']:.3f}"
        if key not in seen:
            seen.add(key)
            try:
                fc = await fetch_weather_forecast(e["observer_lat"], e["observer_lon"], days=7)
                loc_forecasts[key] = fc
                logger.info("  Wetter für %s: OK", e["location_name"])
            except Exception as err:
                logger.warning("  Wetter für %s fehlgeschlagen: %s", e["location_name"], err)

    # Scores in _feed_cache aktualisieren
    updated = 0
    for e in _feed_cache:
        shoot_dt = datetime.fromisoformat(e["shoot_time"])
        if shoot_dt > cutoff or shoot_dt < now_utc - timedelta(hours=1):
            # Außerhalb T+3: Wetter unbekannt zurücksetzen
            e["weather_score"] = 0.0
            e["overall_score"] = e["astronomy_score"]
            continue

        key = f"{e['observer_lat']:.3f},{e['observer_lon']:.3f}"
        fc  = loc_forecasts.get(key)
        if not fc:
            continue

        w_at = fc.get_at(shoot_dt)
        if w_at:
            w_score = calculate_photo_weather_score(w_at)
            e["weather_score"]  = round(w_score, 3)
            e["overall_score"]  = round(e["astronomy_score"] * 0.65 + w_score * 0.35, 3)
            e["weather_description"] = wmo_code_to_description(w_at.weather_code) if hasattr(w_at, "weather_code") else ""
            e["weather_details"] = {
                "temperature_c":        round(w_at.temperature_c, 1),
                "precipitation_prob_pct": round(w_at.precipitation_prob_pct),
                "precipitation_mm":     round(w_at.precipitation_mm, 1),
                "cloud_cover_pct":      round(w_at.cloud_cover_pct),
                "cloud_cover_high_pct": round(w_at.cloud_cover_high_pct),
                "wind_speed_kmh":       round(w_at.wind_speed_kmh),
                "wind_direction_deg":   round(w_at.wind_direction_deg),
                "visibility_m":         round(w_at.visibility_m),
            }
            updated += 1

    _weather_updated_at = now_utc
    logger.info("Wetter-Overlay: %d Events aktualisiert (%d unique Locations)", updated, len(seen))
    _job_done("weather", t0)


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


async def _run_precompute_single(loc_id: str) -> None:
    """
    TASK-12 / BUG-29: Startet precompute.py --location-id <loc_id> im Hintergrund.
    Wird automatisch nach PATCH /locations/{id} mit Koordinaten-Änderung aufgerufen.
    Hält den PATCH-Response nicht auf – läuft vollständig asynchron.

    BUG-29: Ohne --feed-only regeneriert der Single-Flow jetzt sowohl den Feed
    (opportunities.json) ALS AUCH den Kalender (calendar.json) für genau diese
    Location – vorher blieb der Kalender-Snapshot bis zum nächtlichen Vollkalender
    veraltet, sodass Chancendetails aus dem Kalender alte Koordinaten zeigten.
    """
    global _precompute_running
    if _NO_BACKGROUND:
        logger.info("FOTOALERT_NO_BACKGROUND=1 → Single-Location Recompute für '%s' übersprungen (Test-Modus).", loc_id)
        return
    if _precompute_running:
        logger.info("Single-Location Recompute für '%s' übersprungen – Vorberechnung läuft bereits", loc_id)
        return

    _precompute_running = True
    backend_dir = Path(__file__).parent
    logger.info("Starte Single-Location Recompute: %s", loc_id)

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(backend_dir / "precompute.py"),
            "--location-id", loc_id,
            cwd=str(backend_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        if stdout:
            for line in stdout.decode(errors="replace").splitlines():
                logger.info("  [recompute-single] %s", line)
        if proc.returncode == 0:
            logger.info("Single-Location Recompute abgeschlossen (%s). Lade Feed- und Kalender-Cache neu.", loc_id)
            _load_elevation_cache()
            _load_caches()
        else:
            logger.error("Single-Location Recompute fehlgeschlagen (exit %d) für %s", proc.returncode, loc_id)
            _recompute_pending.discard(loc_id)  # BUG-35: bei Fehler aus pending entfernen
    except Exception as e:
        logger.error("Fehler beim Single-Location Recompute für %s: %s", loc_id, e)
        _recompute_pending.discard(loc_id)  # BUG-35: bei Exception aus pending entfernen
    finally:
        _precompute_running = False


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
                for field in ("observer_lat", "observer_lon", "subject_lat", "subject_lon",
                              "name", "description", "observer_floor_height_m",
                              "focal_length_suggestions"):
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


@app.on_event("startup")
async def startup() -> None:
    logger.info("FotoAlert Backend v2 startet (Cache-First)...")

    # 0. Custom Locations laden (persistent gespeicherte User-Spots)
    _load_custom_locations()

    # 0a. Location Overrides laden (Koordinaten-Korrekturen für alle Location-Typen)
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

    # 2b. Scout-Cache laden (falls vorhanden) und ggf. neu berechnen
    _load_discover_cache()
    # Schema-Check: US-81 migrierte moon_* → body_*. Alter Cache hat kein body_name-Feld
    # → erzwingt Neuberechnung damit das Frontend nicht undefined° anzeigt.
    _first_opp = (_discover_cache.get("opportunities") or [{}])[0]
    if not _discover_cache or "body_name" not in _first_opp:
        if _discover_cache:
            logger.info("Scout-Cache hat altes Schema (moon_*) — starte Neuberechnung (US-81).")
        asyncio.create_task(_refresh_discover())

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
        async def _prewarm_calendar() -> None:
            d = date.today()
            try:
                await _compute_month_all_locations(d.year, d.month)
                logger.info("On-Demand-Kalender vorgewärmt: %d-%02d", d.year, d.month)
            except Exception as e:
                logger.error("Kalender-Pre-Warm fehlgeschlagen: %s", e)
        asyncio.create_task(_prewarm_calendar())

    # Scheduler — functools.partial bleibt eine Coroutine-Funktion (APScheduler
    # awaitet sie korrekt; ein lambda täte das nicht).
    import functools as _functools
    scheduler.add_job(_functools.partial(_run_precompute, _precompute_mode),
                      "cron", hour=5, minute=30)   # täglich 05:30 (On-Demand: nur Feed)
    scheduler.add_job(_weather_overlay,  "cron", minute=0, hour="*/3") # alle 3h
    scheduler.add_job(_refresh_discover, "cron", hour=5,  minute=45)   # täglich 05:45 (nach precompute)
    scheduler.start()
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

    # BUG-32: Non-Routine-Events (Mond, Milchstraße, Sonnen-Alignment) zuerst sortieren,
    # damit sie nicht durch den :500-Cap verdrängt werden.
    _ROUTINE_TYPES = {'Goldene Stunde Morgen', 'Goldene Stunde Abend', 'Blaue Stunde'}
    result.sort(key=lambda e: (
        1 if e["event_type"] in _ROUTINE_TYPES else 0,
        e["shoot_time"],
        -e["overall_score"],
    ))
    return result


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


@app.post("/login")
async def login(body: dict = Body(...)) -> dict:
    """US-66: Pflicht-Login. Passwort → Rolle (host/user) + stateless Token.

    Kein Username, kein Rollen-Auswahlfeld — die Rolle ergibt sich aus dem Passwort.
    """
    password = (body or {}).get("password", "")
    role = auth.role_for_password(password)
    if not role:
        raise HTTPException(status_code=401, detail="Falsches Passwort.")
    return {"role": role, "token": auth.issue_token(role)}


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
        id=f"custom_{int(datetime.now().timestamp())}",
        name=f"📍 {req.subject_name}",
        description=desc,
        category=LocationCategory[req.category] if req.category in LocationCategory.__members__ else LocationCategory.SKYLINE,  # US-76
        observer_lat=req.observer_lat, observer_lon=req.observer_lon,
        subject_lat=req.subject_lat, subject_lon=req.subject_lon,
        subject_name=req.subject_name,
        subject_height_m=req.subject_height_m, subject_width_m=req.subject_width_m,
        distance_m=dist_m,
        focal_length_suggestions=[focal_length_mm],
        special_notes="Automatisch erfasst via Quick Location Capture.",
        difficulty=1,
    )
    LOCATIONS.append(new_loc)
    _save_custom_location(new_loc)
    # BUG-35: Recompute als pending markieren bevor Task startet
    _recompute_pending.add(new_loc.id)
    # TASK-17: Recompute-Hook auch für neue Custom Locations triggern (war vorher missing)
    asyncio.create_task(_run_precompute_single(new_loc.id))
    # TASK-18: Backup nach Create
    asyncio.create_task(asyncio.to_thread(backup.backup_after_edit, new_loc.id))
    return new_loc.id


@app.post("/preview-alignment")
async def preview_alignment(req: PreviewAlignmentRequest, _role: str = Depends(auth.require_auth)) -> dict:
    if not (-90 <= req.observer_lat <= 90 and -180 <= req.observer_lon <= 180):
        raise HTTPException(status_code=400, detail="Ungültige Fotograf-Koordinaten.")
    if not (-90 <= req.subject_lat <= 90 and -180 <= req.subject_lon <= 180):
        raise HTTPException(status_code=400, detail="Ungültige Motiv-Koordinaten.")

    profile = calculate_subject_angular_profile(
        observer_lat=req.observer_lat, observer_lon=req.observer_lon,
        subject_lat=req.subject_lat, subject_lon=req.subject_lon,
        subject_height_m=req.subject_height_m, subject_width_m=req.subject_width_m,
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
    all_alignments = []

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
                all_alignments.extend(aligns)
            except Exception as e:
                logger.debug("Alignment-Fehler %s %s: %s", body, target_date, e)

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
    """BUG-35: Gibt IDs zurück für die ein Recompute noch aussteht (in-memory, kein Auth nötig)."""
    return {"pending": list(_recompute_pending), "running": _precompute_running}


# ---------------------------------------------------------------------------
# Reverse Geocoding + Location-Edit (US-57 / C+B)
# ---------------------------------------------------------------------------

@app.get("/reverse-geocode")
async def reverse_geocode_endpoint(lat: float, lon: float) -> dict:
    """Gibt Ortsnamen für Koordinaten via Nominatim zurück."""
    place = await _reverse_geocode(lat, lon)
    return {"place": place}


@app.patch("/locations/{loc_id}")
async def patch_location(loc_id: str, body: dict = Body(...), _role: str = Depends(auth.require_auth)) -> dict:
    """Aktualisiert Felder einer Location (alle Typen; Koordinaten + Name + Beschreibung + Höhenkorrektur)."""
    coord_fields    = {"observer_lat", "observer_lon", "subject_lat", "subject_lon"}
    text_fields     = {"name", "description"}
    numeric_fields  = {"observer_floor_height_m"}       # US-62
    list_fields     = {"focal_length_suggestions"}       # BUG-22: list[int], beeinflusst camera_hints
    recompute_fields = coord_fields | {"observer_floor_height_m", "focal_length_suggestions"}
    all_allowed_fields = coord_fields | text_fields | numeric_fields | list_fields
    allowed = {k: v for k, v in body.items() if k in all_allowed_fields}
    if not allowed:
        raise HTTPException(status_code=400, detail="Keine gültigen Felder (name, description, observer_lat/lon, subject_lat/lon, observer_floor_height_m, focal_length_suggestions).")

    # Koordinaten validieren
    for f in coord_fields & allowed.keys():
        val = allowed[f]
        if not isinstance(val, (int, float)):
            raise HTTPException(status_code=422, detail=f"{f} muss eine Zahl sein.")
        if "lat" in f and not (-90 <= val <= 90):
            raise HTTPException(status_code=422, detail=f"{f} außerhalb ±90°.")
        if "lon" in f and not (-180 <= val <= 180):
            raise HTTPException(status_code=422, detail=f"{f} außerhalb ±180°.")

    # observer_floor_height_m validieren (US-62)
    if "observer_floor_height_m" in allowed:
        val = allowed["observer_floor_height_m"]
        if not isinstance(val, (int, float)):
            raise HTTPException(status_code=422, detail="observer_floor_height_m muss eine Zahl sein.")
        if val < 0:
            raise HTTPException(status_code=422, detail="observer_floor_height_m muss ≥ 0 sein.")
        allowed["observer_floor_height_m"] = float(val)

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

    # In-Memory-Location suchen
    target_loc = next((l for l in LOCATIONS if l.id == loc_id), None)
    if not target_loc:
        raise HTTPException(status_code=404, detail="Location nicht gefunden.")

    if loc_id.startswith("custom_"):
        ok = _update_custom_location_file(loc_id, **allowed)
        if not ok:
            raise HTTPException(status_code=404, detail="Custom Location nicht in Datei gefunden.")
    else:
        # Standard-Location: Overrides in location_overrides.json persistieren
        _save_location_override(loc_id, **allowed)

    # In-Memory-Liste aktualisieren
    for k, v in allowed.items():
        setattr(target_loc, k, v)

    # TASK-12: Koordinaten oder observer_floor_height_m geändert → Single-Location Recompute
    needs_recompute = bool(recompute_fields & allowed.keys())
    if needs_recompute:
        logger.info("Recompute-relevante Felder für '%s' geändert – starte Single-Location Recompute", loc_id)
        asyncio.create_task(_run_precompute_single(loc_id))

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

    if loc_id.startswith("custom_"):
        ok = _store.delete_custom(loc_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Custom Location nicht in DB gefunden.")
    else:
        # Standard-Location: Tombstone damit der Neustart sie herausfiltert
        _store.upsert_override(loc_id, deleted=True)

    # Aus In-Memory-Liste entfernen
    LOCATIONS[:] = [l for l in LOCATIONS if l.id != loc_id]

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

if _web_dir.exists():
    app.mount("/", StaticFiles(directory=str(_web_dir), html=True), name="web")
    logger.info("PWA Web-App wird ausgeliefert aus: %s", _web_dir)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
