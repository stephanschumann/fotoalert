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
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from calculations.astronomy import (
    calculate_subject_angular_profile,
    find_precise_alignment_times,
)
from calculations.weather import fetch_weather_forecast, calculate_photo_weather_score, wmo_code_to_description
from data.locations import LOCATIONS, get_location_by_id, PhotoLocation, LocationCategory
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
_CUSTOM_LOC_FILE    = Path(__file__).parent / "data" / "custom_locations.json"
_OVERRIDES_FILE     = Path(__file__).parent / "data" / "location_overrides.json"
_DISCOVER_CACHE     = _CACHE_DIR / "discover.json"


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
    """Lädt gespeicherte Custom-Locations aus JSON und hängt sie an LOCATIONS."""
    if not _CUSTOM_LOC_FILE.exists():
        return
    try:
        entries = json.loads(_CUSTOM_LOC_FILE.read_text(encoding="utf-8"))
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
            logger.info("Custom Locations geladen: %d Einträge aus %s", added, _CUSTOM_LOC_FILE)
    except Exception as exc:
        logger.warning("Fehler beim Laden von custom_locations.json: %s", exc)


def _save_custom_location(loc: PhotoLocation) -> None:
    """Persistiert eine neue Custom-Location in custom_locations.json."""
    try:
        existing: list[dict] = []
        if _CUSTOM_LOC_FILE.exists():
            existing = json.loads(_CUSTOM_LOC_FILE.read_text(encoding="utf-8"))
        existing.append({
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
        _CUSTOM_LOC_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Custom Location gespeichert: %s → %s", loc.id, _CUSTOM_LOC_FILE)
    except Exception as exc:
        logger.error("Fehler beim Speichern von custom_locations.json: %s", exc)

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
    """Aktualisiert Felder einer Custom-Location in custom_locations.json. Gibt True bei Erfolg."""
    try:
        if not _CUSTOM_LOC_FILE.exists():
            return False
        data = json.loads(_CUSTOM_LOC_FILE.read_text(encoding="utf-8"))
        for entry in data:
            if entry.get("id") == loc_id:
                entry.update(fields)
                _CUSTOM_LOC_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                return True
        return False
    except Exception as exc:
        logger.error("Fehler beim Aktualisieren von custom_locations.json: %s", exc)
        return False


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

# Push-Token Store
_device_tokens: list[dict] = []

# Scheduler
scheduler = AsyncIOScheduler(timezone="Europe/Berlin")


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
    global _feed_cache, _calendar_cache, _cache_loaded_at

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

async def _weather_overlay():
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

async def _run_precompute(mode: str = "full"):
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
    TASK-12: Startet precompute.py --feed-only --location-id <loc_id> im Hintergrund.
    Wird automatisch nach PATCH /locations/{id} mit Koordinaten-Änderung aufgerufen.
    Hält den PATCH-Response nicht auf – läuft vollständig asynchron.
    """
    global _precompute_running
    if _precompute_running:
        logger.info("Single-Location Recompute für '%s' übersprungen – Vorberechnung läuft bereits", loc_id)
        return

    _precompute_running = True
    backend_dir = Path(__file__).parent
    logger.info("Starte Single-Location Recompute: %s", loc_id)

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(backend_dir / "precompute.py"),
            "--feed-only", "--location-id", loc_id,
            cwd=str(backend_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        if stdout:
            for line in stdout.decode(errors="replace").splitlines():
                logger.info("  [recompute-single] %s", line)
        if proc.returncode == 0:
            logger.info("Single-Location Recompute abgeschlossen (%s). Lade Feed-Cache neu.", loc_id)
            _load_elevation_cache()
            _load_caches()
        else:
            logger.error("Single-Location Recompute fehlgeschlagen (exit %d) für %s", proc.returncode, loc_id)
    except Exception as e:
        logger.error("Fehler beim Single-Location Recompute für %s: %s", loc_id, e)
    finally:
        _precompute_running = False


# ---------------------------------------------------------------------------
# Startup / Shutdown
# ---------------------------------------------------------------------------

@app.on_event("startup")
def _load_location_overrides() -> None:
    """Wendet location_overrides.json auf alle Locations an (Koordinaten-Overrides für Standard-Locations)."""
    if not _OVERRIDES_FILE.exists():
        return
    try:
        overrides: list[dict] = json.loads(_OVERRIDES_FILE.read_text(encoding="utf-8"))
        loc_map = {loc.id: loc for loc in LOCATIONS}
        applied = 0
        for ov in overrides:
            loc_id = ov.get("id")
            loc = loc_map.get(loc_id)
            if loc:
                for field in ("observer_lat", "observer_lon", "subject_lat", "subject_lon", "name", "description", "observer_floor_height_m", "focal_length_suggestions"):
                    if field in ov:
                        setattr(loc, field, ov[field])
                applied += 1
        if applied:
            logger.info("Location Overrides geladen: %d Einträge aus %s", applied, _OVERRIDES_FILE)
    except Exception as exc:
        logger.warning("Fehler beim Laden von location_overrides.json: %s", exc)


def _save_location_override(loc_id: str, **fields) -> None:
    """Speichert/aktualisiert einen Override-Eintrag für eine beliebige Location."""
    try:
        existing: list[dict] = []
        if _OVERRIDES_FILE.exists():
            existing = json.loads(_OVERRIDES_FILE.read_text(encoding="utf-8"))
        for entry in existing:
            if entry.get("id") == loc_id:
                entry.update(fields)
                break
        else:
            existing.append({"id": loc_id, **fields})
        _OVERRIDES_FILE.parent.mkdir(parents=True, exist_ok=True)
        _OVERRIDES_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.error("Fehler beim Speichern von location_overrides.json: %s", exc)


@app.on_event("startup")
async def startup():
    logger.info("FotoAlert Backend v2 startet (Cache-First)...")

    # 0. Custom Locations laden (persistent gespeicherte User-Spots)
    _load_custom_locations()

    # 0a. Location Overrides laden (Koordinaten-Korrekturen für alle Location-Typen)
    _load_location_overrides()

    # 0b. Geländehöhen-Cache laden und Locations patchen
    _load_elevation_cache()

    # 1. JSON-Caches laden (sofort)
    cache_ok = _load_caches()

    # 2. Wetter-Overlay für T+0..T+3 (schnell, ~5s)
    asyncio.create_task(_weather_overlay())

    # 2b. Scout-Cache laden (falls vorhanden) und ggf. neu berechnen
    _load_discover_cache()
    if not _discover_cache:
        asyncio.create_task(_refresh_discover())

    # 3. Wenn kein Cache vorhanden: Vorberechnung starten
    if not cache_ok:
        logger.warning("Kein Cache gefunden – starte Erstberechnung im Hintergrund (dauert ~2–5 Min.)")
        asyncio.create_task(_run_precompute())

    # Scheduler
    scheduler.add_job(_run_precompute,   "cron", hour=5,  minute=30)   # täglich 05:30
    scheduler.add_job(_weather_overlay,  "cron", minute=0, hour="*/3") # alle 3h
    scheduler.add_job(_refresh_discover, "cron", hour=5,  minute=45)   # täglich 05:45 (nach precompute)
    scheduler.start()
    logger.info("Bereit. Cache: %d Feed-Events, %d Kalender-Events, Scout: %d Chancen",
                len(_feed_cache), len(_calendar_cache),
                _discover_cache.get("count", 0))


@app.on_event("shutdown")
async def shutdown():
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

    result.sort(key=lambda e: (e["shoot_time"], -e["overall_score"]))
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
async def health():
    return HealthOut(
        status="ok",
        version="2.0.0",
        locations_count=len(LOCATIONS),
    )


@app.get("/locations", response_model=list[LocationOut])
async def get_locations(category: Optional[str] = None):
    locs = LOCATIONS
    if category:
        locs = [l for l in locs if l.category.value.lower() == category.lower()]
    return [_loc_to_out(l) for l in locs]


@app.get("/locations/{location_id}", response_model=LocationOut)
async def get_location(location_id: str):
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
):
    """
    Gibt kommende Foto-Chancen zurück (aus vorberechnetem Cache + Wetter-Overlay).
    Wetter wird nur für die nächsten 3 Tage angezeigt.
    """
    if not _feed_cache:
        return []

    results = _filter_feed(min_score, event_type, priority, days, location_id)
    return results[:500]


@app.get("/opportunities/today")
async def get_today_opportunities():
    today = date.today().isoformat()
    result = [
        e for e in _feed_cache
        if e["shoot_time"][:10] == today
    ]
    result.sort(key=lambda e: -e["overall_score"])
    return result[:20]


@app.get("/daily-briefing", response_model=DailyBriefingOut)
async def daily_briefing(target_date: Optional[str] = None):
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


@app.get("/calendar")
async def get_calendar(
    location_id: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    min_score: float = 0.40,
):
    """
    Jahreskalender: astronomy-only Events für alle Locations, 365 Tage.
    month (1–12) + year filtern serverseitig – Clients sollten immer beide
    Parameter übergeben, um den Payload klein zu halten (~1–3 MB / Monat).
    """
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
):
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


@app.post("/refresh-discover")
async def trigger_discover_refresh(background_tasks: BackgroundTasks):
    """Startet die Scout-Pipeline im Hintergrund (~1–3 Min.)."""
    background_tasks.add_task(_refresh_discover)
    return {"status": "started", "message": "Scout-Pipeline gestartet (~1–3 Min.)."}


@app.post("/register-device")
async def register_device(token: str, platform: str = "ios"):
    if any(d["token"] == token for d in _device_tokens):
        return {"status": "already_registered"}
    _device_tokens.append({"token": token, "platform": platform})
    return {"status": "registered", "device_count": len(_device_tokens)}


@app.post("/refresh")
async def trigger_refresh(background_tasks: BackgroundTasks):
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
async def trigger_feed_refresh(background_tasks: BackgroundTasks):
    """US-34: Nur 14-Tage Feed neu berechnen (precompute --feed-only). ~30–60s."""
    if _precompute_running:
        return {"status": "already_running", "message": "Vorberechnung läuft bereits."}
    background_tasks.add_task(_run_precompute, "feed")
    return {"status": "started", "message": "14-Tage Feed wird neu berechnet (~2–5 Min.)."}


@app.post("/refresh-calendar")
async def trigger_calendar_refresh(background_tasks: BackgroundTasks):
    """US-34: Nur Jahreskalender inkrementell neu berechnen. ~1–3 Min."""
    if _precompute_running:
        return {"status": "already_running", "message": "Vorberechnung läuft bereits."}
    background_tasks.add_task(_run_precompute, "calendar")
    return {"status": "started", "message": "Jahreskalender wird inkrementell neu berechnet (~1–3 Min.)."}


@app.post("/weather-refresh")
async def trigger_weather_refresh(background_tasks: BackgroundTasks):
    """
    Aktualisiert nur das Wetter-Overlay (T+3 Tage) im Hintergrund.
    Schnell: ~10–15s. Kein precompute nötig.
    """
    background_tasks.add_task(_weather_overlay)
    return {"status": "started", "message": "Wetter-Overlay gestartet (~10s)."}


@app.get("/job-status")
async def get_job_status():
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


@app.post("/preview-alignment")
async def preview_alignment(req: PreviewAlignmentRequest):
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

    saved = False
    if req.save and req.subject_name and req.subject_name != "Unbenannt":
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
            category=LocationCategory.SKYLINE,
            observer_lat=req.observer_lat, observer_lon=req.observer_lon,
            subject_lat=req.subject_lat, subject_lon=req.subject_lon,
            subject_name=req.subject_name,
            subject_height_m=req.subject_height_m, subject_width_m=req.subject_width_m,
            distance_m=round(profile.ground_distance_m),
            focal_length_suggestions=[focal_length_mm],
            special_notes="Automatisch erfasst via Quick Location Capture.",
            difficulty=1,
        )
        LOCATIONS.append(new_loc)
        _save_custom_location(new_loc)
        saved = True

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
        "saved": saved,
    }


# ---------------------------------------------------------------------------
# Reverse Geocoding + Location-Edit (US-57 / C+B)
# ---------------------------------------------------------------------------

@app.get("/reverse-geocode")
async def reverse_geocode_endpoint(lat: float, lon: float):
    """Gibt Ortsnamen für Koordinaten via Nominatim zurück."""
    place = await _reverse_geocode(lat, lon)
    return {"place": place}


@app.patch("/locations/{loc_id}")
async def patch_location(loc_id: str, body: dict = Body(...)):
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

    return {"ok": True, "updated": allowed, "recompute_triggered": needs_recompute}


# ---------------------------------------------------------------------------
# Static Files (PWA) – muss NACH allen API-Routen kommen
# ---------------------------------------------------------------------------
import os, pathlib
from fastapi.responses import FileResponse

_web_dir = pathlib.Path(__file__).parent.parent / "web"

# sw.js explizit mit no-cache ausliefern, damit Browser-HTTP-Cache
# nie eine veraltete SW-Version einfriert (behebt 304-Problem)
@app.get("/sw.js")
async def service_worker():
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
