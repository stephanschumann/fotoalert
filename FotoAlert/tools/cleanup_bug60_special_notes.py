"""
FotoAlert — Einmaliges Cleanup: automatische special_notes-Notiz entfernen (BUG-60 / BUG-64)

Vor dem Fix in backend/main.py (_save_alignment_as_location) wurde bei jeder
Quick-Location-Capture-Neuanlage unbedingt der Text
"Automatisch erfasst via Quick Location Capture." in special_notes geschrieben —
auch dann, wenn der Nutzer gar keine eigene Notiz vergeben wollte. Dieses Skript
räumt den dadurch entstandenen Altbestand einmalig auf.

Automatisch bereinigt werden NUR Einträge, deren special_notes EXAKT (zeichengenau,
und ausschließlich) diesem String entspricht — Liste A.

Einträge, die den Zielstring als TEIL eines längeren Textes enthalten (z. B. eigener
Zusatz von Stephan wie "…Quick Location Capture. Zugang nur bei Ebbe.") werden NICHT
automatisch angefasst, sondern separat als Liste B mit vollständigem Hinweise-Text
ausgewiesen (BUG-64-Entscheidung: nicht automatisch überspringen, sondern Stephan
zur Einzelentscheidung vorlegen).

Datenquellen (beide werden geprüft, siehe Memory feedback_live_before_decisions /
reference_sqlite_migrations — sowohl JSON als auch DB prüfen):
  1. backend/data/custom_locations.json  — JSON-Fallback/Legacy-Datei
  2. backend/data/fotoalert.db           — SQLite-Tabelle `custom_locations`
     (TASK-17 hat die JSON-Writes durch die DB ersetzt; es gibt KEINE separate
     Datei "custom_locations.db" — die Tabelle lebt in der gemeinsamen
     fotoalert.db, siehe backend/data/store.py Z.36-40).

Idempotent: ein zweiter Lauf findet keine passenden Einträge mehr und meldet
0 geänderte Einträge, ohne etwas kaputt zu machen. Liste-B-Grenzfälle werden vom
automatischen Lauf nie geschrieben — sie bleiben nach jedem Lauf erneut sichtbar,
bis Stephan sie manuell behandelt hat.

Aufruf (aus dem FotoAlert-Verzeichnis):
    python3 tools/cleanup_bug60_special_notes.py --dry-run   # Probelauf, schreibt NICHTS
    python3 tools/cleanup_bug60_special_notes.py             # echter Lauf (nur Liste A)

Im Dry-Run-Modus wird unter keinen Umständen geschrieben — weder für Liste-A- noch
für Liste-B-Einträge. Der echte Lauf bereinigt ausschließlich Liste A automatisch;
Liste B wird auch im echten Lauf nur berichtet, nie automatisch verändert.

Python-3.9-kompatibel (kein `str | None`, kein `match`-Statement).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import List, Tuple

_TARGET_TEXT = "Automatisch erfasst via Quick Location Capture."

_TOOLS_DIR = Path(__file__).parent
_BACKEND_DIR = _TOOLS_DIR.parent / "backend"
_JSON_PATH = _BACKEND_DIR / "data" / "custom_locations.json"
_DB_PATH = _BACKEND_DIR / "data" / "fotoalert.db"


def clean_json(
    json_path: Path = _JSON_PATH, dry_run: bool = False
) -> Tuple[int, List[Tuple[str, str]]]:
    """
    Setzt special_notes auf "" bei allen Einträgen in json_path, deren
    special_notes exakt (und ausschließlich) _TARGET_TEXT entspricht (Liste A).
    Einträge, die _TARGET_TEXT nur als TEIL eines längeren Textes enthalten
    (Grenzfall, Liste B — z.B. eigener Zusatz von Stephan), werden NIE
    automatisch geschrieben — auch nicht im echten Lauf — sondern nur
    gesammelt und mit vollständigem Text zurückgegeben.

    Rückgabe: (Anzahl Liste-A-Treffer, Liste-B-Grenzfälle als [(id_oder_name, voller_text), ...]).
    Existiert die Datei nicht, wird (0, []) zurückgegeben (kein Fehler).
    """
    if not json_path.exists():
        print(f"  JSON: {json_path} existiert nicht — übersprungen.")
        return 0, []

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"  JSON: unerwartetes Format in {json_path} (kein Array) — übersprungen.")
        return 0, []

    changed = 0
    borderline: List[Tuple[str, str]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        notes = entry.get("special_notes")
        if not isinstance(notes, str):
            continue
        if notes == _TARGET_TEXT:
            changed += 1
            if not dry_run:
                entry["special_notes"] = ""
        elif _TARGET_TEXT in notes:
            # Grenzfall: Zielstring als Teil eines längeren Textes — NIE automatisch anfassen.
            identifier = entry.get("id") or entry.get("name") or "(ohne id/name)"
            borderline.append((str(identifier), notes))

    if changed and not dry_run:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    verb = "würden bereinigt" if dry_run else "bereinigt"
    print(f"  JSON ({json_path.name}): {changed} Eintrag/Einträge (Liste A) {verb}.")
    if borderline:
        print(f"  JSON ({json_path.name}): {len(borderline)} Grenzfall/Grenzfälle (Liste B) gefunden — siehe Report unten.")
    return changed, borderline


def clean_db(
    db_path: Path = _DB_PATH, dry_run: bool = False
) -> Tuple[int, List[Tuple[str, str]]]:
    """
    Setzt special_notes auf '' in der Tabelle custom_locations der SQLite-Datei
    db_path, für alle Zeilen mit exaktem (und ausschließlichem) Match auf
    _TARGET_TEXT (Liste A). Führt vorab ein SELECT aus, um die betroffenen
    Zeilen zu zählen/loggen, bevor das UPDATE läuft (siehe Memory
    reference_sqlite_migrations).

    Zusätzlich wird per LIKE nach Grenzfällen gesucht — Zeilen, die den
    Zielstring als Teil eines längeren Textes enthalten (Liste B). Diese
    werden NIE automatisch geschrieben, auch nicht im echten Lauf.

    Rückgabe: (Anzahl Liste-A-Treffer, Liste-B-Grenzfälle als [(id, voller_text), ...]).
    Existiert die Datei oder Tabelle nicht, wird (0, []) zurückgegeben (kein Fehler).
    """
    if not db_path.exists():
        print(f"  DB: {db_path} existiert nicht — übersprungen.")
        return 0, []

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id FROM custom_locations WHERE special_notes = ?",
                (_TARGET_TEXT,),
            )
            matching_ids = [row[0] for row in cur.fetchall()]

            # Grenzfälle: Zielstring als Teil eines längeren Textes (LIKE '%...%'),
            # aber NICHT die exakten Liste-A-Treffer selbst.
            like_pattern = "%" + _TARGET_TEXT.replace("%", "\\%").replace("_", "\\_") + "%"
            cur.execute(
                "SELECT id, special_notes FROM custom_locations "
                "WHERE special_notes LIKE ? ESCAPE '\\' AND special_notes != ?",
                (like_pattern, _TARGET_TEXT),
            )
            borderline = [(str(row[0]), row[1]) for row in cur.fetchall()]
        except sqlite3.OperationalError as exc:
            print(f"  DB: Tabelle custom_locations nicht vorhanden/lesbar ({exc}) — übersprungen.")
            return 0, []

        changed = len(matching_ids)

        if changed and not dry_run:
            cur.execute(
                "UPDATE custom_locations SET special_notes = '' WHERE special_notes = ?",
                (_TARGET_TEXT,),
            )
            conn.commit()

        verb = "würden bereinigt" if dry_run else "bereinigt"
        print(f"  DB ({db_path.name}, Tabelle custom_locations): {changed} Eintrag/Einträge (Liste A) {verb}.")
        if matching_ids:
            print(f"    Betroffene IDs (Liste A): {', '.join(str(i) for i in matching_ids)}")
        if borderline:
            print(f"  DB ({db_path.name}): {len(borderline)} Grenzfall/Grenzfälle (Liste B) gefunden — siehe Report unten.")
        return changed, borderline
    finally:
        conn.close()


def run(json_path: Path = _JSON_PATH, db_path: Path = _DB_PATH,
        dry_run: bool = False) -> int:
    mode = "Probelauf (--dry-run, keine Schreibvorgänge)" if dry_run else "Live-Lauf"
    print(f"FotoAlert BUG-60/BUG-64 Cleanup — special_notes-Altbestand bereinigen ({mode})")
    print(f'Zielstring (exakter Match, Liste A): "{_TARGET_TEXT}"')
    print()

    json_changed, json_borderline = clean_json(json_path, dry_run=dry_run)
    db_changed, db_borderline = clean_db(db_path, dry_run=dry_run)

    total = json_changed + db_changed
    all_borderline = json_borderline + db_borderline

    print()
    print(f"Liste A — Gesamt: {total} Eintrag/Einträge {'würden automatisch bereinigt' if dry_run else 'automatisch bereinigt'}.")
    print()
    if all_borderline:
        print(f"Liste B — Grenzfälle ({len(all_borderline)}): Platzhaltertext ist Teil eines längeren Textes.")
        print("Diese werden NICHT automatisch verändert — bitte einzeln entscheiden:")
        for identifier, full_text in all_borderline:
            print(f"  - {identifier}: \"{full_text}\"")
    else:
        print("Liste B — Grenzfälle: keine gefunden.")

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
