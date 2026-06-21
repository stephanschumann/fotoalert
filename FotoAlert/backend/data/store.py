"""
FotoAlert LocationStore — SQLite-Repository für nutzereditierbare Daten.

Ersetzt die direkten JSON-Schreibzugriffe in main.py.
Alle Writes sind atomar (BEGIN / COMMIT / ROLLBACK).

Tabellen:
  custom_locations      — vom User angelegte Foto-Standorte
  location_overrides    — Koordinaten-/Name-Korrekturen für Standard-Locations
  location_verifications — Vor-Ort-Verifikationen und Problemmeldungen (BUG-26)
  location_ratings       — Sterne-Bewertungen pro Gerät (US-89)

TASK-17: SQLite-Migration + atomare Writes (Fundament)
BUG-26:  location_verifications Tabelle + CRUD
US-89:   location_ratings Tabelle + Upsert/Aggregation
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# TASK-19: FOTOALERT_ENV steuert den Datenpfad (prod → data/, dev → data_dev/)
_ENV = os.getenv("FOTOALERT_ENV", "prod")
_DEFAULT_DB = (
    Path(__file__).parent / "fotoalert.db"               # prod: backend/data/fotoalert.db
    if _ENV == "prod"
    else Path(__file__).parent.parent / "data_dev" / "fotoalert.db"  # dev: backend/data_dev/fotoalert.db
)

_INIT_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS custom_locations (
    id                      TEXT PRIMARY KEY,
    name                    TEXT NOT NULL,
    description             TEXT DEFAULT '',
    category                TEXT DEFAULT 'SKYLINE',
    observer_lat            REAL,
    observer_lon            REAL,
    subject_lat             REAL,
    subject_lon             REAL,
    subject_name            TEXT DEFAULT '',
    subject_height_m        REAL DEFAULT 0,
    subject_width_m         REAL DEFAULT 0,
    distance_m              INTEGER DEFAULT 0,
    focal_length_suggestions TEXT DEFAULT '[]',
    special_notes           TEXT DEFAULT '',
    difficulty              INTEGER DEFAULT 1,
    observer_floor_height_m REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS location_overrides (
    id      TEXT PRIMARY KEY,
    fields  TEXT NOT NULL  -- JSON-Objekt mit den überschriebenen Feldern
);

CREATE TABLE IF NOT EXISTS location_verifications (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id   TEXT    NOT NULL,
    location_name TEXT    DEFAULT '',
    status        TEXT    NOT NULL,   -- 'ok' | 'issue'
    issue_type    TEXT    DEFAULT '',
    comment       TEXT    DEFAULT '',
    date          TEXT    NOT NULL    -- ISO-Datum YYYY-MM-DD
);

CREATE INDEX IF NOT EXISTS idx_verif_location ON location_verifications(location_id);

CREATE TABLE IF NOT EXISTS location_ratings (
    location_id   TEXT    NOT NULL,
    device_id     TEXT    NOT NULL,
    value         INTEGER NOT NULL,   -- 1..5
    updated       TEXT    NOT NULL,   -- ISO-Timestamp
    UNIQUE(location_id, device_id)
);

CREATE INDEX IF NOT EXISTS idx_rating_location ON location_ratings(location_id);
"""


class LocationStore:
    """Zentrale Datenzugriffsschicht für nutzereditierbare Location-Daten."""

    def __init__(self, db_path: Path = _DEFAULT_DB) -> None:
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Interne Hilfsmethoden
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Öffnet eine neue SQLite-Verbindung mit Row-Factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Erstellt Tabellen falls noch nicht vorhanden."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_INIT_SQL)
        logger.info("LocationStore initialisiert: %s", self.db_path)

    # ------------------------------------------------------------------
    # Custom Locations
    # ------------------------------------------------------------------

    def create_custom(self, loc_dict: dict) -> None:
        """Legt eine neue Custom Location an (atomar)."""
        sql = """
            INSERT INTO custom_locations (
                id, name, description, category,
                observer_lat, observer_lon, subject_lat, subject_lon,
                subject_name, subject_height_m, subject_width_m, distance_m,
                focal_length_suggestions, special_notes, difficulty,
                observer_floor_height_m
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        params = (
            loc_dict["id"],
            loc_dict["name"],
            loc_dict.get("description", ""),
            loc_dict.get("category", "SKYLINE"),
            loc_dict["observer_lat"],
            loc_dict["observer_lon"],
            loc_dict["subject_lat"],
            loc_dict["subject_lon"],
            loc_dict.get("subject_name", ""),
            float(loc_dict.get("subject_height_m", 0)),
            float(loc_dict.get("subject_width_m", 0)),
            int(loc_dict.get("distance_m", 0)),
            json.dumps(loc_dict.get("focal_length_suggestions", [])),
            loc_dict.get("special_notes", ""),
            int(loc_dict.get("difficulty", 1)),
            float(loc_dict.get("observer_floor_height_m", 0.0)),
        )
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                conn.execute(sql, params)
                conn.execute("COMMIT")
                logger.info("Custom Location gespeichert: %s", loc_dict["id"])
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def update_custom(self, loc_id: str, **fields) -> bool:
        """
        Aktualisiert einzelne Felder einer Custom Location.
        Gibt True zurück wenn die Location gefunden und geändert wurde.
        focal_length_suggestions (list) wird automatisch serialisiert.
        """
        if not fields:
            return False

        # focal_length_suggestions als JSON speichern
        if "focal_length_suggestions" in fields:
            fields = dict(fields)
            fields["focal_length_suggestions"] = json.dumps(
                fields["focal_length_suggestions"]
            )

        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [loc_id]
        sql = f"UPDATE custom_locations SET {set_clause} WHERE id = ?"

        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                cur = conn.execute(sql, values)
                conn.execute("COMMIT")
                found = cur.rowcount > 0
                if found:
                    logger.info("Custom Location aktualisiert: %s (%s)", loc_id, list(fields.keys()))
                return found
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def delete_custom(self, loc_id: str) -> bool:
        """
        Löscht eine Custom Location aus der DB.
        Gibt True zurück wenn ein Eintrag entfernt wurde.
        """
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                cur = conn.execute(
                    "DELETE FROM custom_locations WHERE id = ?", (loc_id,)
                )
                conn.execute("COMMIT")
                found = cur.rowcount > 0
                if found:
                    logger.info("Custom Location gelöscht: %s", loc_id)
                return found
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def load_all_custom(self) -> list[dict]:
        """Lädt alle Custom Locations als Liste von dicts (für Startup-Load)."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM custom_locations").fetchall()
        result = []
        for row in rows:
            d = dict(row)
            # JSON-Feld deserialisieren
            d["focal_length_suggestions"] = json.loads(
                d.get("focal_length_suggestions") or "[]"
            )
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Location Overrides
    # ------------------------------------------------------------------

    def upsert_override(self, loc_id: str, **fields) -> None:
        """
        Legt einen Override-Eintrag an oder ergänzt ihn.
        Bestehende Felder werden mit den neuen gemergt (nicht überschrieben).
        """
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                existing_row = conn.execute(
                    "SELECT fields FROM location_overrides WHERE id = ?", (loc_id,)
                ).fetchone()

                if existing_row:
                    existing = json.loads(existing_row["fields"])
                    existing.update(fields)
                    conn.execute(
                        "UPDATE location_overrides SET fields = ? WHERE id = ?",
                        (json.dumps(existing, ensure_ascii=False), loc_id),
                    )
                else:
                    conn.execute(
                        "INSERT INTO location_overrides (id, fields) VALUES (?, ?)",
                        (loc_id, json.dumps(fields, ensure_ascii=False)),
                    )
                conn.execute("COMMIT")
                logger.info("Override gespeichert: %s (%s)", loc_id, list(fields.keys()))
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def load_all_overrides(self) -> list[dict]:
        """Lädt alle Overrides als Liste von dicts mit `id` + Feldern flach."""
        with self._connect() as conn:
            rows = conn.execute("SELECT id, fields FROM location_overrides").fetchall()
        result = []
        for row in rows:
            entry = {"id": row["id"]}
            entry.update(json.loads(row["fields"]))
            result.append(entry)
        return result

    # ------------------------------------------------------------------
    # Hilfsmethoden für Migration / Tests
    # ------------------------------------------------------------------

    def create_custom_if_not_exists(self, loc_dict: dict) -> bool:
        """
        INSERT OR IGNORE-Semantik: legt an wenn id noch nicht existiert.
        Gibt True zurück wenn neu angelegt, False wenn bereits vorhanden.
        """
        sql = """
            INSERT OR IGNORE INTO custom_locations (
                id, name, description, category,
                observer_lat, observer_lon, subject_lat, subject_lon,
                subject_name, subject_height_m, subject_width_m, distance_m,
                focal_length_suggestions, special_notes, difficulty,
                observer_floor_height_m
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        params = (
            loc_dict["id"],
            loc_dict["name"],
            loc_dict.get("description", ""),
            loc_dict.get("category", "SKYLINE"),
            loc_dict["observer_lat"],
            loc_dict["observer_lon"],
            loc_dict["subject_lat"],
            loc_dict["subject_lon"],
            loc_dict.get("subject_name", ""),
            float(loc_dict.get("subject_height_m", 0)),
            float(loc_dict.get("subject_width_m", 0)),
            int(loc_dict.get("distance_m", 0)),
            json.dumps(loc_dict.get("focal_length_suggestions", [])),
            loc_dict.get("special_notes", ""),
            int(loc_dict.get("difficulty", 1)),
            float(loc_dict.get("observer_floor_height_m", 0.0)),
        )
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            return cur.rowcount > 0

    def upsert_override_if_not_exists(self, loc_id: str, fields: dict) -> bool:
        """
        INSERT OR IGNORE-Semantik für Overrides.
        Gibt True zurück wenn neu angelegt.
        """
        sql = "INSERT OR IGNORE INTO location_overrides (id, fields) VALUES (?, ?)"
        with self._connect() as conn:
            cur = conn.execute(sql, (loc_id, json.dumps(fields, ensure_ascii=False)))
            return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Location Verifications (BUG-26)
    # ------------------------------------------------------------------

    def add_verification(self, location_id: str, location_name: str,
                         status: str, issue_type: str, comment: str,
                         date: str) -> int:
        """Legt einen neuen Verifikationseintrag an. Gibt die neue ID zurück."""
        sql = """INSERT INTO location_verifications
                 (location_id, location_name, status, issue_type, comment, date)
                 VALUES (?, ?, ?, ?, ?, ?)"""
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                cur = conn.execute(sql, (location_id, location_name, status,
                                         issue_type or "", comment or "", date))
                conn.execute("COMMIT")
                new_id = cur.lastrowid
                logger.info("Verifikation gespeichert: %s (%s) id=%s", location_id, status, new_id)
                return new_id
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def get_verifications(self, location_id: str) -> list:
        """Gibt alle Verifikationen für eine Location zurück (älteste zuerst)."""
        sql = """SELECT id, location_id, location_name, status, issue_type, comment, date
                 FROM location_verifications
                 WHERE location_id = ?
                 ORDER BY id ASC"""
        with self._connect() as conn:
            rows = conn.execute(sql, (location_id,)).fetchall()
        return [dict(row) for row in rows]

    def delete_last_verification(self, location_id: str) -> bool:
        """Löscht den neuesten Eintrag für eine Location. True wenn gefunden."""
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                row = conn.execute(
                    "SELECT id FROM location_verifications WHERE location_id = ? ORDER BY id DESC LIMIT 1",
                    (location_id,)
                ).fetchone()
                if not row:
                    conn.execute("ROLLBACK")
                    return False
                conn.execute("DELETE FROM location_verifications WHERE id = ?", (row["id"],))
                conn.execute("COMMIT")
                logger.info("Letzte Verifikation gelöscht: %s (id=%s)", location_id, row["id"])
                return True
            except Exception:
                conn.execute("ROLLBACK")
                raise

    # ------------------------------------------------------------------
    # Location Ratings (US-89)
    # ------------------------------------------------------------------

    def upsert_rating(self, location_id: str, device_id: str,
                      value: int, updated: str) -> None:
        """
        Speichert/aktualisiert die Bewertung eines Geräts für eine Location.
        Upsert über UNIQUE(location_id, device_id) → ein Gerät = eine Bewertung,
        überschreibbar, keine Doppelzählung (BUG-26-Muster, aber mit ON CONFLICT).
        """
        sql = """INSERT INTO location_ratings (location_id, device_id, value, updated)
                 VALUES (?, ?, ?, ?)
                 ON CONFLICT(location_id, device_id)
                 DO UPDATE SET value = excluded.value, updated = excluded.updated"""
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                conn.execute(sql, (location_id, device_id, int(value), updated))
                conn.execute("COMMIT")
                logger.info("Rating gespeichert: %s device=%s value=%s",
                            location_id, device_id, value)
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def get_rating_summary(self, location_id: str,
                           device_id: Optional[str] = None) -> dict:
        """
        Aggregiert Bewertungen einer Location: {count, avg, mine}.
        avg auf 1 Nachkommastelle, None bei count=0 (NICHT 0 → UI „unbewertet").
        mine = Wert des aufrufenden Geräts oder None.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n, AVG(value) AS a FROM location_ratings "
                "WHERE location_id = ?",
                (location_id,)
            ).fetchone()
            count = row["n"] or 0
            avg = round(row["a"], 1) if count else None

            mine = None
            if device_id:
                mrow = conn.execute(
                    "SELECT value FROM location_ratings "
                    "WHERE location_id = ? AND device_id = ?",
                    (location_id, device_id)
                ).fetchone()
                if mrow:
                    mine = mrow["value"]
        return {"count": count, "avg": avg, "mine": mine}

    def delete_rating(self, location_id: str, device_id: str) -> bool:
        """Löscht die Bewertung eines Geräts für eine Location. True wenn gefunden."""
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                cur = conn.execute(
                    "DELETE FROM location_ratings "
                    "WHERE location_id = ? AND device_id = ?",
                    (location_id, device_id)
                )
                conn.execute("COMMIT")
                found = cur.rowcount > 0
                if found:
                    logger.info("Rating gelöscht: %s device=%s", location_id, device_id)
                return found
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def load_all_ratings(self) -> list:
        """
        Gibt aggregierte Bewertungen aller Locations zurück (Boot-Preload).
        Pro Location: {location_id, count, avg}. avg auf 1 Nachkommastelle,
        None bei count=0 (kommt durch GROUP BY hier nicht vor, aber konsistent).
        Zusätzlich die Roh-Werte je Gerät, damit das Frontend `mine` ableiten kann.
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT location_id, device_id, value FROM location_ratings"
            ).fetchall()
        return [dict(r) for r in rows]

    def integrity_check(self) -> str:
        """Führt PRAGMA integrity_check aus. Gibt 'ok' zurück bei Erfolg."""
        with self._connect() as conn:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            return row[0] if row else "unknown"
