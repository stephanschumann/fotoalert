"""
FotoAlert — Einmaliges Cleanup: automatische special_notes-Notiz entfernen (BUG-60)

Vor dem Fix in backend/main.py (_save_alignment_as_location) wurde bei jeder
Quick-Location-Capture-Neuanlage unbedingt der Text
"Automatisch erfasst via Quick Location Capture." in special_notes geschrieben —
auch dann, wenn der Nutzer gar keine eigene Notiz vergeben wollte. Dieses Skript
räumt den dadurch entstandenen Altbestand einmalig auf.

Betrifft NUR Einträge, deren special_notes EXAKT (zeichengenau) diesem String
entspricht. Eigene oder abweichende Notizen (auch mit demselben Text plus
zusätzlichen Anmerkungen) werden NICHT angefasst.

Datenquellen (beide werden geprüft, siehe Memory feedback_live_before_decisions /
reference_sqlite_migrations — sowohl JSON als auch DB prüfen):
  1. backend/data/custom_locations.json  — JSON-Fallback/Legacy-Datei
  2. backend/data/fotoalert.db           — SQLite-Tabelle `custom_locations`
     (TASK-17 hat die JSON-Writes durch die DB ersetzt; es gibt KEINE separate
     Datei "custom_locations.db" — die Tabelle lebt in der gemeinsamen
     fotoalert.db, siehe backend/data/store.py Z.36-40).

Idempotent: ein zweiter Lauf findet keine passenden Einträge mehr und meldet
0 geänderte Einträge, ohne etwas kaputt zu machen.

Aufruf (aus dem FotoAlert-Verzeichnis):
    python3 tools/cleanup_bug60_special_notes.py
    python3 tools/cleanup_bug60_special_notes.py --dry-run

Python-3.9-kompatibel (kein `str | None`, kein `match`-Statement).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional

_TARGET_TEXT = "Automatisch erfasst via Quick Location Capture."

_TOOLS_DIR = Path(__file__).parent
_BACKEND_DIR = _TOOLS_DIR.parent / "backend"
_JSON_PATH = _BACKEND_DIR / "data" / "custom_locations.json"
_DB_PATH = _BACKEND_DIR / "data" / "fotoalert.db"


def clean_json(json_path: Path = _JSON_PATH, dry_run: bool = False) -> int:
    """
    Setzt special_notes auf "" bei allen Einträgen in json_path, deren
    special_notes exakt _TARGET_TEXT entspricht. Gibt die Anzahl geänderter
    Einträge zurück. Existiert die Datei nicht, wird 0 zurückgegeben (kein Fehler).
    """
    if not json_path.exists():
        print(f"  JSON: {json_path} existiert nicht — übersprungen.")
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"  JSON: unerwartetes Format in {json_path} (kein Array) — übersprungen.")
        return 0

    changed = 0
    for entry in data:
        if isinstance(entry, dict) and entry.get("special_notes") == _TARGET_TEXT:
            changed += 1
            if not dry_run:
                entry["special_notes"] = ""

    if changed and not dry_run:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    verb = "würden bereinigt" if dry_run else "bereinigt"
    print(f"  JSON ({json_path.name}): {changed} Eintrag/Einträge {verb}.")
    return changed


def clean_db(db_path: Path = _DB_PATH, dry_run: bool = False) -> int:
    """
    Setzt special_notes auf '' in der Tabelle custom_locations der SQLite-Datei
    db_path, für alle Zeilen mit exaktem Match auf _TARGET_TEXT.
    Führt vorab ein SELECT aus, um die betroffenen Zeilen zu zählen/loggen,
    bevor das UPDATE läuft (siehe Memory reference_sqlite_migrations).
    Existiert die Datei oder Tabelle nicht, wird 0 zurückgegeben (kein Fehler).
    """
    if not db_path.exists():
        print(f"  DB: {db_path} existiert nicht — übersprungen.")
        return 0

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id FROM custom_locations WHERE special_notes = ?",
                (_TARGET_TEXT,),
            )
        except sqlite3.OperationalError as exc:
            print(f"  DB: Tabelle custom_locations nicht vorhanden/lesbar ({exc}) — übersprungen.")
            return 0

        matching_ids = [row[0] for row in cur.fetchall()]
        changed = len(matching_ids)

        if changed and not dry_run:
            cur.execute(
                "UPDATE custom_locations SET special_notes = '' WHERE special_notes = ?",
                (_TARGET_TEXT,),
            )
            conn.commit()

        verb = "würden bereinigt" if dry_run else "bereinigt"
        print(f"  DB ({db_path.name}, Tabelle custom_locations): {changed} Eintrag/Einträge {verb}.")
        if matching_ids:
            print(f"    Betroffene IDs: {', '.join(matching_ids)}")
        return changed
    finally:
        conn.close()


def run(json_path: Path = _JSON_PATH, db_path: Path = _DB_PATH,
        dry_run: bool = False) -> int:
    mode = "Probelauf (--dry-run, keine Schreibvorgänge)" if dry_run else "Live-Lauf"
    print(f"FotoAlert BUG-60 Cleanup — special_notes-Altbestand bereinigen ({mode})")
    print(f'Zielstring (exakter Match): "{_TARGET_TEXT}"')
    print()

    json_changed = clean_json(json_path, dry_run=dry_run)
    db_changed = clean_db(db_path, dry_run=dry_run)

    total = json_changed + db_changed
    print()
    print(f"Gesamt: {total} Eintrag/Einträge {'würden bereinigt' if dry_run else 'bereinigt'}.")
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Nur zählen/anzeigen, nichts schreiben.",
    )
    args = parser.parse_args()

    run(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
