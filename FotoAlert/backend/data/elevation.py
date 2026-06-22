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

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

_TOPODATA_BASE = "https://api.opentopodata.org/v1"
# Reihenfolge = Priorität: feinster/regionaler Datensatz zuerst, dann global.
DATASET_CHAIN: List[str] = ["eudem25m", "srtm30m", "mapzen"]

_CACHE_FILE = Path(__file__).resolve().parent / "cache" / "elevation_tiles.json"
_CACHE_PRECISION = 4  # ~11 m Raster — fein genug, klein genug für den Cache


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
        """
        obs = await self.get_elevation(observer_lat, observer_lon)
        sub = await self.get_elevation(subject_lat, subject_lon)
        if obs is None or sub is None:
            return 0.0, True
        return round(sub - obs, 1), False


# Modul-weiter Singleton (teilt den Tile-Cache prozessweit)
provider = ElevationProvider()
