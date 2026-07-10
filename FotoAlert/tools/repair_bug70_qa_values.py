#!/usr/bin/env python3
"""
BUG-70: Reparaturskript für eine beschädigte SQLite-Tabelle.

Hintergrund: Auf dem Produktionsserver meldete `PRAGMA integrity_check` eine
B-Tree-Korruption in der Tabelle `location_qa_values` (Rowid-Reihenfolge
kaputt, zugehöriger Auto-Index fehlt komplett). Root-Cause-Verdacht laut
BACKLOG.md BUG-70: ein harter OOM-Kill des uvicorn-Prozesses während eines
Schreibvorgangs auf genau diese Tabelle.

Vorgehen (Option A aus der Analyse — gezielte Reparatur statt Totalverlust):
  1. Sicherheitskopie der übergebenen DB-Datei (VOR jeder Änderung).
  2. Zeilenweises, fehler-isoliertes Auslesen der Zieltabelle (Schema wird
     dynamisch aus sqlite_master/PRAGMA table_info gelesen, nicht hart
     angenommen) — ein kaputter Bereich bricht nicht den gesamten Lesevorgang
     ab, sondern wird übersprungen und protokolliert.
  3. Neuaufbau der Tabelle unter einem neuen Namen (`<table>_new`) mit
     identischem Schema, Übernahme aller erfolgreich gelesenen Zeilen,
     Wiederherstellung etwaiger expliziter Indizes.
  4. Tausch: alte (kaputte) Tabelle wird zu `<table>_old_corrupt` umbenannt
     (NICHT gelöscht), die neue Tabelle wird auf den Originalnamen umbenannt.
  5. Abschließender `PRAGMA integrity_check` + Zusammenfassung.

Sicherheitsprinzipien:
  - Es wird NIE automatisch etwas gelöscht. Die alte Tabelle bleibt als
    `_old_corrupt` erhalten, bis sie manuell geprüft und freigegeben wird.
  - Ohne `--commit` läuft ausschließlich ein Trockenlauf: alle Schritte
    werden innerhalb einer Transaktion ausgeführt (inkl. Zwischen-Check),
    am Ende aber per ROLLBACK verworfen. Nichts wird "scharf", bis das
    Flag explizit gesetzt wird.
  - Existieren `<table>_new` oder `<table>_old_corrupt` bereits (z.B. Rest
    eines vorherigen Laufs), bricht das Skript ab, statt sie zu überschreiben
    oder zu löschen.

Verwendung:
    # Trockenlauf / Report (empfohlen als erster Schritt):
    python3 repair_bug70_qa_values.py /pfad/zur/fotoalert.db

    # Reparatur tatsächlich committen:
    python3 repair_bug70_qa_values.py /pfad/zur/fotoalert.db --commit

    # Andere Tabelle reparieren (Default: location_qa_values):
    python3 repair_bug70_qa_values.py /pfad/zur/fotoalert.db --table location_qa_values --commit
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("repair_bug70")

NEW_SUFFIX = "_new"
OLD_SUFFIX = "_old_corrupt"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "BUG-70: Repariert eine beschädigte SQLite-Tabelle durch Neuaufbau "
            "aus den lesbaren Zeilen. Ohne --commit NUR Trockenlauf/Report."
        )
    )
    p.add_argument(
        "db_path",
        type=Path,
        help="Pfad zur SQLite-Datenbankdatei (Pflichtangabe, kein Default hart codiert).",
    )
    p.add_argument(
        "--table",
        default="location_qa_values",
        help="Name der zu reparierenden Tabelle (Default: location_qa_values, das BUG-70-Ziel).",
    )
    p.add_argument(
        "--commit",
        action="store_true",
        help="Änderungen tatsächlich committen. Ohne dieses Flag: reiner Trockenlauf (Rollback am Ende).",
    )
    p.add_argument(
        "--max-skip",
        type=int,
        default=1000,
        help="Sicherheitsgrenze: maximale Anzahl übersprungener/defekter Zeilen bevor abgebrochen wird.",
    )
    return p.parse_args()


def backup_db(db_path: Path) -> Path:
    """Legt VOR jeder Änderung eine Sicherheitskopie mit Zeitstempel an."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}.backup_{ts}{db_path.suffix}")
    shutil.copy2(db_path, backup_path)
    logger.info("Sicherheitskopie angelegt: %s", backup_path)
    return backup_path


def get_create_table_sql(conn: sqlite3.Connection, table: str) -> Optional[str]:
    """Liest das originale CREATE-TABLE-Statement aus sqlite_master (nicht hart annehmen)."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row[0] if row else None


def get_index_sqls(conn: sqlite3.Connection, table: str) -> List[Tuple[str, str]]:
    """Liest alle EXPLIZIT angelegten Indizes der Tabelle (Auto-Indizes für
    PRIMARY KEY/UNIQUE haben sql=NULL und werden von SQLite beim Neuanlegen
    der Tabelle automatisch mit erzeugt, brauchen also keine separate
    Wiederherstellung)."""
    rows = conn.execute(
        "SELECT name, sql FROM sqlite_master "
        "WHERE type='index' AND tbl_name=? AND sql IS NOT NULL",
        (table,),
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def get_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    """Liest die Spaltennamen per PRAGMA table_info (nicht hart annehmen)."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if not rows:
        raise RuntimeError(
            f"Tabelle '{table}' nicht gefunden oder ohne Spalten (PRAGMA table_info leer)."
        )
    return [r[1] for r in rows]


def rename_table_in_create_sql(create_sql: str, old_name: str, new_name: str) -> str:
    """Ersetzt NUR den Tabellennamen im CREATE-TABLE-Statement, Rest bleibt identisch."""
    pattern = re.compile(
        r'(CREATE TABLE\s+(?:IF NOT EXISTS\s+)?)([`"\[]?)' + re.escape(old_name) + r'([`"\]]?)',
        re.IGNORECASE,
    )
    new_sql, n = pattern.subn(
        lambda m: f"{m.group(1)}{m.group(2)}{new_name}{m.group(3)}", create_sql, count=1
    )
    if n != 1:
        raise RuntimeError(
            f"Tabellenname '{old_name}' konnte im CREATE-TABLE-Statement nicht "
            f"eindeutig ersetzt werden: {create_sql!r}"
        )
    return new_sql


def try_count(conn: sqlite3.Connection, table: str) -> Optional[int]:
    """Best-Effort Zeilenzahl VOR der Reparatur. None wenn nicht ermittelbar
    (z.B. weil schon COUNT(*) auf die Korruption trifft)."""
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return row[0] if row else None
    except sqlite3.DatabaseError as exc:
        logger.warning("Zeilen vorher nicht ermittelbar (SELECT COUNT(*) schlug fehl): %s", exc)
        return None


def read_rows_resilient(
    conn: sqlite3.Connection, table: str, columns: List[str], max_skip: int
) -> Tuple[List[tuple], int, int, List[int]]:
    """
    Liest die Tabelle zeilenweise über eine Rowid-Fenstertechnik statt eines
    einzelnen `fetchall()`.

    BUG-70-Anforderung: `fetchall()` bricht beim ersten kaputten Bereich den
    gesamten Lesevorgang ab. Diese Funktion nutzt stattdessen `fetchone()` in
    einer Schleife mit try/except — schlägt ein `fetchone()` fehl (kaputte
    Seite), wird eine NEUE Abfrage ab der nächsten rowid gestartet, statt
    abzubrechen. So bleiben spätere, intakte Zeilen erreichbar.

    Einschränkung (wichtig, siehe Rückmeldung an Stephan): SQLite liefert bei
    B-Tree-Korruption keine exakte Rowid der fehlerhaften Zeile zurück. Die
    hier verwendete "eine rowid weiter versuchen"-Strategie ist Best-Effort —
    die geloggten "verlorenen" rowids markieren die Position, an der neu
    angesetzt wurde, nicht zwingend exakt die eine kaputte Zeile. Bei der
    real diagnostizierten Korruption (Rowid-Reihenfolge selbst kaputt, siehe
    BACKLOG.md BUG-70) kann das ORDER-BY-rowid-Fenster zusätzlich betroffen
    sein — dieses Skript kann das nur begrenzt kompensieren.

    Rückgabe: (gute_zeilen, ok_count, fail_count, lost_rowids)
    gute_zeilen ist eine Liste von Tupeln in Spaltenreihenfolge (OHNE rowid).
    """
    good_rows: List[tuple] = []
    ok_count = 0
    fail_count = 0
    lost_rowids: List[int] = []
    min_rowid = -1  # wir wollen rowid > min_rowid
    skips_used = 0

    col_list = ", ".join(columns)
    while True:
        try:
            cur = conn.execute(
                f"SELECT rowid, {col_list} FROM {table} WHERE rowid > ? ORDER BY rowid",
                (min_rowid,),
            )
        except sqlite3.DatabaseError as exc:
            logger.error("Konnte keine neue Abfrage ab rowid>%s starten: %s", min_rowid, exc)
            break

        while True:
            try:
                row = cur.fetchone()
            except sqlite3.DatabaseError as exc:
                fail_count += 1
                skips_used += 1
                suspect_rowid = min_rowid + 1
                lost_rowids.append(suspect_rowid)
                logger.warning(
                    "Zeile bei rowid=%s nicht lesbar (%s) - uebersprungen (%d/%d)",
                    suspect_rowid, exc, skips_used, max_skip,
                )
                min_rowid = suspect_rowid
                if skips_used >= max_skip:
                    logger.error(
                        "Maximale Anzahl uebersprungener Zeilen (%d) erreicht - "
                        "breche Lesevorgang ab.", max_skip,
                    )
                    return good_rows, ok_count, fail_count, lost_rowids
                break  # neue Abfrage mit erhoehtem min_rowid starten (aeussere Schleife)

            if row is None:
                return good_rows, ok_count, fail_count, lost_rowids

            good_rows.append(row[1:])
            ok_count += 1
            min_rowid = row[0]


def main() -> int:
    args = parse_args()
    db_path: Path = args.db_path
    table = args.table
    new_table = f"{table}{NEW_SUFFIX}"
    old_table = f"{table}{OLD_SUFFIX}"

    if not db_path.exists():
        logger.error("Datenbankdatei nicht gefunden: %s", db_path)
        return 2

    # 1. Sicherheitskopie VOR jeder Aenderung.
    backup_db(db_path)

    conn = sqlite3.connect(str(db_path))
    try:
        # Schema lesen (nicht hart annehmen).
        create_sql = get_create_table_sql(conn, table)
        if not create_sql:
            logger.error("Tabelle '%s' existiert nicht in %s.", table, db_path)
            return 2
        if "without rowid" in create_sql.lower():
            logger.error(
                "Tabelle '%s' ist WITHOUT ROWID angelegt — die rowid-basierte "
                "Fenstertechnik dieses Skripts greift hier nicht. Abbruch, "
                "kein Fallback implementiert.", table,
            )
            return 2

        existing_tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if new_table in existing_tables or old_table in existing_tables:
            logger.error(
                "Tabelle '%s' oder '%s' existiert bereits — vermutlich Rest eines "
                "vorherigen Laufs. Abbruch OHNE Aenderung, damit nichts ueberschrieben "
                "oder geloescht wird. Bitte manuell pruefen.",
                new_table, old_table,
            )
            return 3

        columns = get_columns(conn, table)
        index_sqls = get_index_sqls(conn, table)
        logger.info(
            "Schema gelesen: %s (%d Spalten, %d expliziter Index/e: %s)",
            table, len(columns), len(index_sqls), [n for n, _ in index_sqls],
        )

        rows_before = try_count(conn, table)
        logger.info(
            "Zeilen vorher (SELECT COUNT(*)): %s",
            rows_before if rows_before is not None else "nicht ermittelbar",
        )

        good_rows, ok_count, fail_count, lost_rowids = read_rows_resilient(
            conn, table, columns, args.max_skip
        )
        logger.info(
            "Lesevorgang abgeschlossen: %d Zeilen erfolgreich, %d Zeilen fehlgeschlagen",
            ok_count, fail_count,
        )

        # 2. Reparatur in einer Transaktion (Commit nur mit --commit).
        preview_check: List[str] = []
        conn.execute("BEGIN")
        try:
            new_create_sql = rename_table_in_create_sql(create_sql, table, new_table)
            conn.execute(new_create_sql)

            col_list = ", ".join(columns)
            placeholders = ", ".join(["?"] * len(columns))
            insert_sql = f"INSERT INTO {new_table} ({col_list}) VALUES ({placeholders})"
            inserted = 0
            for row in good_rows:
                conn.execute(insert_sql, row)
                inserted += 1
            logger.info("%d Zeilen in %s kopiert.", inserted, new_table)

            conn.execute(f"ALTER TABLE {table} RENAME TO {old_table}")
            conn.execute(f"ALTER TABLE {new_table} RENAME TO {table}")
            logger.info(
                "Tabellen getauscht: %s -> %s (aufbewahrt), %s -> %s (aktiv)",
                table, old_table, new_table, table,
            )

            for idx_name, idx_sql in index_sqls:
                conn.execute(idx_sql)
                logger.info("Index neu aufgebaut: %s", idx_name)

            preview_rows = conn.execute("PRAGMA integrity_check").fetchall()
            preview_check = [r[0] for r in preview_rows]
            logger.info(
                "PRAGMA integrity_check (Vorschau INNERHALB der Transaktion, vor "
                "Commit/Rollback-Entscheidung): %s", preview_check,
            )

            if args.commit:
                conn.commit()
                logger.info("COMMIT ausgefuehrt — Aenderungen sind dauerhaft.")
            else:
                conn.rollback()
                logger.info(
                    "TROCKENLAUF — keine Aenderung committet (Rollback). "
                    "--commit setzen fuer einen echten Lauf."
                )
        except Exception:
            conn.rollback()
            logger.error(
                "Fehler waehrend der Reparatur — Transaktion zurueckgerollt, "
                "keine Aenderung uebernommen."
            )
            raise

        # 3. Abschliessender Integritaetscheck: reflektiert den TATSAECHLICHEN
        # Datei-Zustand nach Commit-Entscheidung (bei Trockenlauf also wieder
        # der urspruengliche, ggf. weiterhin kaputte Zustand).
        final_rows = conn.execute("PRAGMA integrity_check").fetchall()
        final_check = [r[0] for r in final_rows]

        print("\n" + "=" * 72)
        print(f"BUG-70 Reparatur-Report — {'COMMIT' if args.commit else 'TROCKENLAUF (kein COMMIT)'}")
        print("=" * 72)
        print(f"Datenbank:                 {db_path}")
        print(f"Tabelle:                   {table}")
        print(f"Zeilen vorher:             {rows_before if rows_before is not None else 'nicht ermittelbar'}")
        print(f"Erfolgreich gelesen:       {ok_count}")
        print(f"Fehlgeschlagen (verloren): {fail_count}")
        if lost_rowids:
            print(f"Verlorene rowids (Best-Effort-Position): {lost_rowids}")
        print(f"Integritaetscheck-Vorschau (nach Reparatur, vor Commit-Entscheidung): {preview_check}")
        print(f"Integritaetscheck (finaler Datei-Zustand nach diesem Lauf):          {final_check}")
        print("=" * 72)
        if not args.commit:
            print(
                "Kein --commit gesetzt: Es wurde NICHTS dauerhaft veraendert. "
                "Der obige 'finale' Check zeigt daher weiterhin den ORIGINAL-Zustand."
            )
        print("=" * 72 + "\n")

        if args.commit and final_check != ["ok"]:
            logger.error("Integritaetscheck nach Reparatur ist NICHT 'ok': %s", final_check)
            return 1
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
