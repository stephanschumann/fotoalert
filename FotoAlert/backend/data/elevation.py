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

Datenquelle: heute OpenTopoData **EUDEM 25m (nur Europa)**. Der weltweite DEM
(Copernicus GLO-30 / SRTM) ist als Folge-Ticket (TASK-26) geplant — er wird genau
hier hinter `_fetch_elevation` ausgetauscht, der Rest bleibt unverändert.

Python-3.9-kompatibel.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# EUDEM 25m (Europa). Weltweit-Wechsel → TASK-26.
TOPODATA_URL = "https://api.opentopodata.org/v1/eudem25m"

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
        """Einzelpunkt von der DEM-Quelle holen. None bei Fehler/keine Abdeckung."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(TOPODATA_URL, params={"locations": f"{lat},{lon}"})
                resp.raise_for_status()
                results = resp.json().get("results", [])
                if results and results[0].get("elevation") is not None:
                    return float(results[0]["elevation"])
        except Exception as e:
            logger.info("Elevation-Abruf fehlgeschlagen (%s,%s): %s", lat, lon, e)
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
