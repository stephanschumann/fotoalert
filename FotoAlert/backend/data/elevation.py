"""
FotoAlert – Elevation Provider (TASK-25)

Stellt Geländehöhen hinter einem einheitlichen Interface bereit, damit die
On-Demand-Engine für beliebige Koordinaten den Höhenunterschied Fotograf↔Motiv
bestimmen kann.

Eigenschaften:
  • Persistenter **Tile-Cache** (JSON) — Geländehöhe ändert sich nie → kein TTL.
  • **Fallback**: ist keine Höhe verfügbar (außerhalb der DEM-Abdeckung oder
    Netzfehler), wird `elevation_difference = 0.0` mit Flag `incomplete=True`
    zurückgegeben → die Berechnung läuft weiter, das Ergebnis ist transparent als
    „Höhendaten unvollständig" markiert (kein Crash).

Datenquelle (TASK-26, weltweit): OpenTopoData mit **Dataset-Kette** — EUDEM 25m
(Europa, fein) → SRTM 30m (global ~60°N–56°S) → Mapzen (global, inkl. Pole). Pro
Punkt werden die Datasets der Reihe nach versucht, bis eine Höhe ≠ null kommt; erst
wenn alle leer sind, greift der `incomplete=True`-Fallback.

Python-3.9-kompatibel.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

_TOPODATA_BASE = "https://api.opentopodata.org/v1"
# Reihenfolge = Priorität: feinster/regionaler Datensatz zuerst, dann global.
DATASET_CHAIN: List[str] = ["eudem25m", "srtm30m", "mapzen"]
# OpenTopoData Public-API erlaubt 1 Anfrage/Sekunde. Vor jedem FOLGE-Dataset
# kurz warten, damit die Kette nicht ins 429-Rate-Limit läuft (Europa bleibt
# schnell, weil EUDEM = erster Call ohne Wartezeit). 0 = aus (Self-Hosting).
RATE_LIMIT_PAUSE_S: float = 1.1

_CACHE_FILE = Path(__file__).resolve().parent / "cache" / "elevation_tiles.json"
_CACHE_PRECISION = 4  # ~11 m Raster — fein genug, klein genug für den Cache

# Modul-weiter Rate-Limit-Tracker für Netzanfragen an OpenTopoData: hält den
# Abstand zur letzten tatsächlichen Netzanfrage auch ÜBER mehrere Punkte hinweg
# ein (nicht nur innerhalb der Dataset-Kette eines einzelnen Punkts), z. B. wenn
# elevation_profile() 21 Punkte hintereinander abfragt. Lock macht das gegen
# gleichzeitige async-Aufrufe sicher; Cache-Treffer laufen NIE hier durch.
_rate_limit_lock = asyncio.Lock()
_last_request_ts: Optional[float] = None


async def _respect_rate_limit() -> None:
    """Wartet bei Bedarf, bis seit der letzten Netzanfrage mindestens
    RATE_LIMIT_PAUSE_S vergangen ist. Nur vor tatsächlichen Netzanfragen
    aufrufen (Cache-Treffer dürfen hier nicht durchlaufen)."""
    global _last_request_ts
    if RATE_LIMIT_PAUSE_S <= 0:
        return
    async with _rate_limit_lock:
        loop = asyncio.get_running_loop()
        now = loop.time()
        if _last_request_ts is not None:
            elapsed = now - _last_request_ts
            wait = RATE_LIMIT_PAUSE_S - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
        _last_request_ts = loop.time()


def _key(lat: float, lon: float) -> str:
    return f"{round(lat, _CACHE_PRECISION)},{round(lon, _CACHE_PRECISION)}"


class ElevationProvider:
    """Geländehöhen mit persistentem Tile-Cache + Fallback."""

    def __init__(self, cache_file: Path = _CACHE_FILE):
        self.cache_file = Path(cache_file)
        self._cache: Dict[str, float] = self._load()

    def _load(self) -> Dict[str, float]:
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("Elevation-Tile-Cache unlesbar, starte leer")
        return {}

    def _save(self) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(self._cache), encoding="utf-8")
        except Exception as e:
            logger.warning("Elevation-Tile-Cache nicht schreibbar: %s", e)

    async def _fetch_elevation(self, lat: float, lon: float) -> Optional[float]:
        """Einzelpunkt holen: Dataset-Kette der Reihe nach, bis eine Höhe ≠ null
        kommt (weltweit). None erst, wenn KEIN Dataset Abdeckung hat."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                for dataset in DATASET_CHAIN:
                    await _respect_rate_limit()  # 1 req/s-Limit, auch über Punkte hinweg
                    try:
                        resp = await client.get(f"{_TOPODATA_BASE}/{dataset}",
                                                params={"locations": f"{lat},{lon}"})
                        resp.raise_for_status()
                        results = resp.json().get("results", [])
                        if results and results[0].get("elevation") is not None:
                            return float(results[0]["elevation"])
                    except Exception as e:
                        logger.info("Elevation %s (%s,%s) fehlgeschlagen: %s",
                                    dataset, lat, lon, e)
        except Exception as e:
            logger.info("Elevation-Abruf (%s,%s) abgebrochen: %s", lat, lon, e)
        return None

    async def get_elevation(self, lat: float, lon: float) -> Optional[float]:
        """Geländehöhe in m (Cache → sonst Abruf). None wenn nicht verfügbar."""
        k = _key(lat, lon)
        if k in self._cache:
            return self._cache[k]
        elev = await self._fetch_elevation(lat, lon)
        if elev is not None:
            self._cache[k] = round(elev, 1)
            self._save()
        return elev

    async def elevation_difference(
        self, observer_lat: float, observer_lon: float,
        subject_lat: float, subject_lon: float,
    ) -> Tuple[float, bool]:
        """
        Höhenunterschied Motiv-Basis − Fotograf-Standort (m) + Flag `incomplete`.
        Semantik wie precompute.fetch_elevations: difference = subject − observer.
        Fehlt eine Höhe → (0.0, True): Berechnung läuft weiter, transparent markiert.

        BUG-63: Fotograf- und Motiv-Punkt werden parallel abgefragt
        (asyncio.gather), um die Wartezeit beider Aufrufe zu überlappen. Der
        modulweite Rate-Limit-Lock (_respect_rate_limit, s.o.) wird davon nicht
        umgangen — er sitzt weiterhin vor jedem echten Netzaufruf innerhalb von
        _fetch_elevation() und takted diese unverändert einzeln. Nur die
        Wartezeit AUF den Lock läuft jetzt für beide Punkte parallel.
        """
        obs, sub = await asyncio.gather(
            self.get_elevation(observer_lat, observer_lon),
            self.get_elevation(subject_lat, subject_lon),
        )
        if obs is None or sub is None:
            return 0.0, True
        return round(sub - obs, 1), False

    async def elevation_profile(
        self,
        observer_lat: float, observer_lon: float,
        subject_lat: float, subject_lon: float,
        num_samples: int = 20,
    ) -> Tuple[List[Optional[float]], bool]:
        """
        US-09: Höhenprofil entlang der Sichtlinie Fotograf → Motiv.

        Liefert eine Liste von `num_samples + 1` Geländehöhen (m) für
        äquidistante Zwischenpunkte zwischen Standort (Index 0) und Motiv
        (Index -1), inklusive beider Endpunkte.

        Rückgabe: (heights, incomplete). `incomplete=True` sobald mindestens
        ein ZWISCHEN-Stützpunkt (Index 1..num_samples-1) keine Höhe liefert
        (transparent als „nicht geprüft" markiert, kein stiller 0.0-Fallback
        einzelner Punkte, da eine fehlende Zwischenhöhe das gesamte Profil
        unzuverlässig macht).

        BUG-Fix (US-09, 2026-07-06): Die beiden Endpunkte (Index 0 = Beobachter-
        Standort, Index -1 = Motiv-Standort) fließen NIE in die Hindernis-
        Erkennung ein (siehe evaluate_sightline(): `terrain_heights_m[1:-1]`).
        Sie durften trotzdem `incomplete=True` auslösen, was in der Praxis dazu
        führte, dass der Sichtachsen-Check für praktisch jede Location dauerhaft
        "nicht_geprueft" blieb — OpenTopoData liefert für exakte Standort-/
        Gebäudekoordinaten (oft knapp neben dem DEM-Raster) überdurchschnittlich
        häufig keine Höhe, obwohl alle tatsächlich benötigten Zwischenpunkte
        vollständig vorhanden waren. Jetzt zählen nur noch die Zwischenpunkte.
        """
        from discover.geometry import bearing_between  # lokaler Import: zirkulär vermeiden

        heights: List[Optional[float]] = []
        incomplete = False
        last_idx = num_samples  # Index des letzten Punkts (Liste hat num_samples+1 Einträge)
        for i in range(num_samples + 1):
            frac = i / num_samples
            lat = observer_lat + (subject_lat - observer_lat) * frac
            lon = observer_lon + (subject_lon - observer_lon) * frac
            h = await self.get_elevation(lat, lon)
            if h is None and 0 < i < last_idx:
                incomplete = True
            heights.append(h)
        return heights, incomplete


# Modul-weiter Singleton (teilt den Tile-Cache prozessweit)
provider = ElevationProvider()
