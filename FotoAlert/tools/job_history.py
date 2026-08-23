#!/usr/bin/env python3
"""
job_history.py — US-38: CLI-Übersicht der Job-History (job_runs-Tabelle).

Nutzung:
    python3 tools/job_history.py [--days 7] [--job weather] [--errors-only]

Zero-Dependency-CLI (nur sqlite3/argparse/datetime/os/pathlib aus der
Standardbibliothek, Implementation Spec Schritt 6) — liest die SQLite-DB
direkt, ohne backend/-Code zu importieren (kein fastapi/pydantic nötig).

Exit-Codes:
  0 — Tabelle ausgegeben
  1 — keine Job-History-Daten gefunden (frische Installation, AK12)
  2 — ungültige CLI-Argumente (z.B. --days <= 0 oder nicht-numerisch, AK15)
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple


def _default_db_path() -> Path:
    """Gleiche Env-gesteuerte Pfadlogik wie backend/data/store.py
    (FOTOALERT_ENV=prod -> backend/data/fotoalert.db, sonst backend/data_dev/)."""
    env = os.getenv("FOTOALERT_ENV", "prod")
    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    if env == "prod":
        return backend_dir / "data" / "fotoalert.db"
    return backend_dir / "data_dev" / "fotoalert.db"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="US-38: Zeigt die Job-History (job_runs) der letzten N Tage.",
    )
    parser.add_argument(
        "--days", default="7",
        help="Anzahl Tage zurück, positive ganze Zahl (Standard: 7).",
    )
    parser.add_argument(
        "--job", default=None,
        help="Nur diesen Job anzeigen (z.B. weather, feed, calendar, discover, backup).",
    )
    parser.add_argument(
        "--errors-only", action="store_true",
        help="Nur fehlgeschlagene Läufe anzeigen.",
    )
    parser.add_argument(
        "--db", default=None,
        help="Pfad zur SQLite-Datenbank (Override, v.a. für Tests).",
    )
    return parser


def validate_days(raw: str) -> int:
    """AK15: ungültiger --days-Wert -> verständliche ValueError-Meldung statt Absturz."""
    try:
        days = int(str(raw).strip())
    except (TypeError, ValueError):
        raise ValueError(f"--days muss eine ganze Zahl sein, erhalten: '{raw}'")
    if days <= 0:
        raise ValueError(f"--days muss eine positive ganze Zahl sein, erhalten: {days}")
    return days


def fetch_job_runs(
    db_path: Path,
    days: int,
    job: Optional[str] = None,
    errors_only: bool = False,
) -> List[Tuple]:
    """Liest job_runs der letzten `days` Tage. Fehlt die DB-Datei komplett
    (frische Installation, vor dem ersten Job-Lauf), gibt es einfach [] zurück
    (AK12: klare Meldung statt Stacktrace)."""
    if not db_path.exists():
        return []

    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    sql = (
        "SELECT job, ts, duration_s, status, error_class "
        "FROM job_runs WHERE ts >= ?"
    )
    params: list = [since]
    if job:
        sql += " AND job = ?"
        params.append(job)
    if errors_only:
        sql += " AND status = 'error'"
    sql += " ORDER BY ts DESC"

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        # z.B. job_runs-Tabelle existiert noch nicht (ganz frische DB ohne
        # jemals gelaufenen Job) -> wie "keine Daten" behandeln.
        return []
    finally:
        conn.close()
    return rows


def format_table(rows: List[Tuple]) -> str:
    header = f"{'JOB':<14}{'ZEITSTEMPEL':<22}{'DAUER(s)':<10}{'STATUS':<8}{'FEHLERKLASSE':<14}"
    lines = [header, "-" * len(header)]
    for job, ts, duration_s, status, error_class in rows:
        dur = f"{duration_s:.1f}" if duration_s is not None else "-"
        lines.append(
            f"{job:<14}{ts:<22}{dur:<10}{status:<8}{(error_class or '-'):<14}"
        )
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        days = validate_days(args.days)
    except ValueError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2

    db_path = Path(args.db) if args.db else _default_db_path()
    rows = fetch_job_runs(db_path, days, job=args.job, errors_only=args.errors_only)

    if not rows:
        print("Keine Job-History-Daten gefunden.")
        return 1

    print(format_table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
