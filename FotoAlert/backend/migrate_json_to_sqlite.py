#!/usr/bin/env python3
"""
FotoAlert — Migration: JSON → SQLite

Liest custom_locations.json und location_overrides.json und überträgt
die Einträge in die SQLite-Datenbank (fotoalert.db).

Idempotent: Bereits vorhandene Einträge (gleiche id) werden übersprungen.
Kann beliebig oft ausgeführt werden ohne Duplikate zu erzeugen.

Aufruf (aus backend/-Verzeichnis):
    python migrate_json_to_sqlite.py

TASK-17: SQLite-Migration + atomare Writes (Fundament)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Sicherstellen dass das backend/-Verzeichnis im Python-Pfad liegt
sys.path.insert(0, str(Path(__file__).parent))

from data.store import LocationStore

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
CUSTOM_LOC_FILE = DATA_DIR / "custom_locations.json"
OVERRIDES_FILE  = DATA_DIR / "location_overrides.json"


def migrate() -> None:
    store = LocationStore()

    # ------------------------------------------------------------------ #
    # 1. custom_locations.json → Tabelle custom_locations
    # ------------------------------------------------------------------ #
    migrated_custom = 0
    skipped_custom  = 0

    if CUSTOM_LOC_FILE.exists():
        try:
            entries: list[dict] = json.loads(
                CUSTOM_LOC_FILE.read_text(encoding="utf-8")
            )
            for entry in entries:
                if store.create_custom_if_not_exists(entry):
                    migrated_custom += 1
                    logger.info("  ✓ Custom Location migriert: %s", entry.get("id"))
                else:
                    skipped_custom += 1
                    logger.info("  – Custom Location bereits vorhanden: %s", entry.get("id"))
        except Exception as exc:
            logger.error("Fehler beim Lesen von %s: %s", CUSTOM_LOC_FILE, exc)
            sys.exit(1)
    else:
        logger.info("custom_locations.json nicht vorhanden — übersprungen.")

    # ------------------------------------------------------------------ #
    # 2. location_overrides.json → Tabelle location_overrides
    # ------------------------------------------------------------------ #
    migrated_overrides = 0
    skipped_overrides  = 0

    if OVERRIDES_FILE.exists():
        try:
            overrides: list[dict] = json.loads(
                OVERRIDES_FILE.read_text(encoding="utf-8")
            )
            for ov in overrides:
                loc_id = ov.get("id")
                if not loc_id:
                    logger.warning("  Override ohne id übersprungen: %s", ov)
                    continue
                fields = {k: v for k, v in ov.items() if k != "id"}
                if store.upsert_override_if_not_exists(loc_id, fields):
                    migrated_overrides += 1
                    logger.info("  ✓ Override migriert: %s", loc_id)
                else:
                    skipped_overrides += 1
                    logger.info("  – Override bereits vorhanden: %s", loc_id)
        except Exception as exc:
            logger.error("Fehler beim Lesen von %s: %s", OVERRIDES_FILE, exc)
            sys.exit(1)
    else:
        logger.info("location_overrides.json nicht vorhanden — übersprungen.")

    # ------------------------------------------------------------------ #
    # 3. Integrity Check
    # ------------------------------------------------------------------ #
    check = store.integrity_check()
    if check != "ok":
        logger.error("PRAGMA integrity_check: %s — DB möglicherweise beschädigt!", check)
        sys.exit(1)

    # ------------------------------------------------------------------ #
    # Ergebnis
    # ------------------------------------------------------------------ #
    logger.info("")
    logger.info("Migration abgeschlossen:")
    logger.info("  Custom Locations: %d migriert, %d bereits vorhanden", migrated_custom, skipped_custom)
    logger.info("  Overrides:        %d migriert, %d bereits vorhanden", migrated_overrides, skipped_overrides)
    logger.info("  Integrity Check:  %s", check)
    logger.info("  DB:               %s", store.db_path)


if __name__ == "__main__":
    migrate()
