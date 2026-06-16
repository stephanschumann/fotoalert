"""
FotoAlert – Geo-Layer Standalone (Schicht 1)

Aktualisiert nur den Elevations-Cache (data/cache/elevations.json),
ohne den Astronomy-Cache (calendar.json) oder den Feed anzufassen.

Wann ausführen:
  - Nach dem Hinzufügen einer neuen Location (um Geländehöhen zu holen)
  - Wenn OpenTopoData-Daten für eine Location fehlen oder korrigiert werden sollen

Ausführung:
  cd FotoAlert/backend
  python3 precompute_geo.py

Um eine einzelne Location neu zu fetchen (Cache-Eintrag löschen → neu holen):
  Entferne den Eintrag manuell aus data/cache/elevations.json, dann dieses Skript.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Geo-Layer aus precompute.py wiederverwenden
from precompute import CACHE_DIR, fetch_elevations
import asyncio
import json
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("=== FotoAlert Geo-Cache Refresh ===")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    computed_at = datetime.now(timezone.utc).isoformat()

    elevations = await fetch_elevations()

    elev_path = CACHE_DIR / "elevations.json"
    elev_path.write_text(
        json.dumps({"computed_at": computed_at, "elevations": elevations},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("✅ elevations.json: %d Locations gespeichert", len(elevations))
    logger.info("=== Geo-Cache Refresh abgeschlossen ===")


if __name__ == "__main__":
    asyncio.run(main())
