"""
FotoAlert LocationStore — SQLite-Repository für nutzereditierbare Daten.

Ersetzt die direkten JSON-Schreibzugriffe in main.py.
Alle Writes sind atomar (BEGIN / COMMIT / ROLLBACK).

Tabellen:
  custom_locations      — vom User angelegte Foto-Standorte
  location_overrides    — Koordinaten-/Name-Korrekturen für Standard-Locations
  location_verifications — Vor-Ort-Verifikationen und Problemmeldungen (BUG-26)
  location_ratings       — Sterne-Bewertungen pro Gerät (US-89)
  location_qa_state     — Lock-Flags + Change-Detection-Hash pro Location (TASK-43)
  location_qa_values    — Auto-generierte Felder für BASE-Locations (TASK-43)

TASK-17: SQLite-Migration + atomare Writes (Fundament)
BUG-26:  location_verifications Tabelle + CRUD
US-89:   location_ratings Tabelle + Upsert/Aggregation
TASK-43: QA-Datenmodell (Lock-Flags, qa_values, geo_hash)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
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

CREATE TABLE IF NOT EXISTS device_tokens (
    token         TEXT    PRIMARY KEY,
    platform      TEXT    NOT NULL DEFAULT 'ios',
    device_id     TEXT    NOT NULL DEFAULT '',
    updated       TEXT    NOT NULL   -- ISO-Timestamp
);

CREATE TABLE IF NOT EXISTS camera_profiles (
    device_id     TEXT    PRIMARY KEY,
    sensor        TEXT    NOT NULL,
    fl            INTEGER NOT NULL,
    ori           TEXT    NOT NULL,
    updated       TEXT    NOT NULL   -- ISO-Timestamp
);

-- TASK-43: QA-Datenmodell
CREATE TABLE IF NOT EXISTS location_qa_state (
    location_id       TEXT    PRIMARY KEY,
    description_lock  INTEGER DEFAULT 0,   -- 1 = manuell gesperrt, kein Auto-Update
    azimuth_lock      INTEGER DEFAULT 0,
    focal_length_lock INTEGER DEFAULT 0,
    qa_checked_at     TEXT,                -- ISO-Timestamp des letzten QA-Laufs
    geo_hash          TEXT                 -- Hash der Geo-Kernfelder für Change-Detection
);

CREATE TABLE IF NOT EXISTS location_qa_values (
    location_id              TEXT    PRIMARY KEY,
    description              TEXT,
    ideal_azimuth_min        REAL,
    ideal_azimuth_max        REAL,
    focal_length_suggestions TEXT,           -- JSON-Array
    -- US-09: Sichtachsen-Check (Raycast-Hinderniserkennung)
    sightline_status          TEXT,           -- 'frei'|'teilweise_verdeckt'|'blockiert'|'nicht_geprueft'
    sightline_angle_deg       REAL,           -- Verdeckungswinkel (Grad), None wenn nicht ermittelbar
    sightline_checked_at      TEXT            -- ISO-Timestamp des letzten Sichtachsen-Checks
);
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
        """Öffnet eine neue SQLite-Verbindung mit Row-Factory.

        TASK-78: PRAGMA busy_timeout lässt SQLite bei einem gleichzeitigen
        Schreibzugriff bis zu 5s intern warten, statt sofort "database is
        locked" zu werfen — reduziert die Häufigkeit kurzzeitiger Lock-Konflikte
        (Begleitmaßnahme, ersetzt nicht die Konsistenz-Absicherung in
        _qa_improve_one()/_run_qa_pass()).
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Erstellt Tabellen falls noch nicht vorhanden.

        TASK-43: Führt idempotente Spaltenmigration für custom_locations durch
        (ideal_azimuth_min / ideal_azimuth_max). SQLite unterstützt kein
        ALTER TABLE ADD COLUMN IF NOT EXISTS, daher try/except.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_INIT_SQL)
            # TASK-43: Azimut-Spalten in custom_locations ergänzen (idempotent)
            # US-120: image_filename ergänzen (Beispielbild-Verweis für Custom Locations)
            # US-126: image_focus_x/y ergänzen (Fokuspunkt für Bildausschnitt, nullable)
            for col, typedef in [
                ("ideal_azimuth_min", "REAL DEFAULT NULL"),
                ("ideal_azimuth_max", "REAL DEFAULT NULL"),
                ("image_filename", "TEXT DEFAULT NULL"),
                ("image_focus_x", "REAL DEFAULT NULL"),
                ("image_focus_y", "REAL DEFAULT NULL"),
            ]:
                try:
                    conn.execute(
                        f"ALTER TABLE custom_locations ADD COLUMN {col} {typedef}"
                    )
                    conn.commit()
                    logger.info("Migration TASK-43: custom_locations.%s ergänzt", col)
                except sqlite3.OperationalError:
                    pass  # Spalte existiert bereits
            # US-09: Sichtachsen-Spalten in location_qa_values ergänzen (idempotent,
            # gleiches Muster wie oben — nötig für DBs, die vor US-09 angelegt wurden).
            for col, typedef in [
                ("sightline_status", "TEXT DEFAULT NULL"),
                ("sightline_angle_deg", "REAL DEFAULT NULL"),
                ("sightline_checked_at", "TEXT DEFAULT NULL"),
            ]:
                try:
                    conn.execute(
                        f"ALTER TABLE location_qa_values ADD COLUMN {col} {typedef}"
                    )
                    conn.commit()
                    logger.info("Migration US-09: location_qa_values.%s ergänzt", col)
                except sqlite3.OperationalError:
                    pass  # Spalte existiert bereits
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

    def load_all_verifications(self) -> list:
        """TASK-61: Lädt alle Verifikationen aller Locations (für Backup-Export).

        Analog zu get_verifications(location_id), aber ohne Filter auf eine
        einzelne Location — für den vollständigen Backup-Export.
        """
        sql = """SELECT id, location_id, location_name, status, issue_type, comment, date
                 FROM location_verifications
                 ORDER BY id ASC"""
        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()
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

    # ------------------------------------------------------------------
    # Push-Token-Persistenz (TASK-24)
    # ------------------------------------------------------------------

    def register_device_token(
        self,
        token: str,
        platform: str = "ios",
        device_id: str = "",
    ) -> bool:
        """
        Persistiert einen Push-Token (Upsert).
        Gibt True zurück wenn neu angelegt, False wenn bereits vorhanden.
        """
        from datetime import datetime, timezone

        updated = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as conn:
                conn.execute("BEGIN")
                existing = conn.execute(
                    "SELECT token FROM device_tokens WHERE token = ?", (token,)
                ).fetchone()
                if existing:
                    conn.execute("ROLLBACK")
                    return False
                conn.execute(
                    "INSERT INTO device_tokens (token, platform, device_id, updated) "
                    "VALUES (?, ?, ?, ?)",
                    (token, platform, device_id, updated),
                )
                conn.execute("COMMIT")
                return True
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise

    def load_device_tokens(self) -> list:
        """
        Gibt alle registrierten Push-Token zurück.
        Form: [{"token": str, "platform": str, "device_id": str, "updated": str}]
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT token, platform, device_id, updated FROM device_tokens"
            ).fetchall()
        return [dict(r) for r in rows]

    def device_token_count(self) -> int:
        """Anzahl der persistierten Push-Token."""
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM device_tokens").fetchone()
        return row[0] if row else 0

    # ------------------------------------------------------------------
    # Camera Profiles (US-90)
    # ------------------------------------------------------------------

    _VALID_SENSORS = {"fullframe", "apsc_canon", "apsc_sony", "mft", "one_inch"}
    _VALID_ORI = {"landscape", "portrait"}

    def upsert_camera_profile(
        self,
        device_id: str,
        sensor: str,
        fl: int,
        ori: str,
        updated: str,
    ) -> None:
        """
        Speichert/aktualisiert das Kamera-Profil eines Geräts (Upsert).
        PRIMARY KEY device_id → 1 Gerät = 1 Profil, überschreibbar.
        """
        sql = """INSERT INTO camera_profiles (device_id, sensor, fl, ori, updated)
                 VALUES (?, ?, ?, ?, ?)
                 ON CONFLICT(device_id)
                 DO UPDATE SET sensor = excluded.sensor,
                               fl = excluded.fl,
                               ori = excluded.ori,
                               updated = excluded.updated"""
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                conn.execute(sql, (device_id, sensor, int(fl), ori, updated))
                conn.execute("COMMIT")
                logger.info("CameraProfile gespeichert: device=%s sensor=%s fl=%s ori=%s",
                            device_id, sensor, fl, ori)
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def get_camera_profile(self, device_id: str) -> Optional[dict]:
        """
        Gibt das Kamera-Profil eines Geräts zurück, oder None wenn unbekannt.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT sensor, fl, ori FROM camera_profiles WHERE device_id = ?",
                (device_id,)
            ).fetchone()
        return dict(row) if row else None

    def load_all_camera_profiles(self) -> list:
        """TASK-61: Lädt alle Kamera-Profile aller Geräte (für Backup-Export).

        Analog zu get_camera_profile(device_id), aber ohne Filter auf ein
        einzelnes Gerät — für den vollständigen Backup-Export.
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT device_id, sensor, fl, ori, updated FROM camera_profiles"
            ).fetchall()
        return [dict(row) for row in rows]

    def integrity_check(self) -> list[str]:
        """Führt PRAGMA integrity_check aus.

        BUG-70: liest per fetchall() statt fetchone(), damit bei mehreren
        Fehlermeldungen (z.B. mehrere betroffene Zeilen/Tabellen) alle erfasst
        werden — vorher wurde nur die erste Zeile zurückgegeben, weitere
        Fehler blieben unsichtbar.

        Gibt eine Liste zurück. Bei Erfolg `["ok"]`, sonst eine Zeile pro
        gemeldetem Integritätsproblem.

        BUG-70-Nachfix: PRAGMA integrity_check kann bei ausreichend schwerer
        Korruption selbst eine sqlite3.DatabaseError ("database disk image
        is malformed") werfen statt sauber Zeilen zurückzugeben. Diese
        Exception wurde bisher NICHT abgefangen und propagierte ungefangen
        nach oben — das hätte den Serverstart zum Absturz gebracht, obwohl
        die alte (vor-BUG-70) Implementierung in diesem Fall nur einen
        stillen Fehler produzierte. Damit die neue laute Fehlerbehandlung
        (AK-7) eine Verbesserung bleibt und keine Verschlechterung, fangen
        wir hier ab und melden das Problem als Teil der Ergebnisliste.
        """
        try:
            with self._connect() as conn:
                rows = conn.execute("PRAGMA integrity_check").fetchall()
                return [row[0] for row in rows] if rows else ["unknown"]
        except sqlite3.DatabaseError as e:
            return [f"integrity_check fehlgeschlagen: {e}"]
        except sqlite3.Error as e:
            return [f"integrity_check fehlgeschlagen: {e}"]

    # ------------------------------------------------------------------
    # TASK-43: QA-Datenmodell — Lock-Flags, QA-Values, Geo-Hash
    # ------------------------------------------------------------------

    def get_qa_state(self, location_id: str) -> Optional[dict]:
        """Gibt den QA-Zustand einer Location zurück, oder None wenn noch nie geprüft."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM location_qa_state WHERE location_id = ?",
                (location_id,),
            ).fetchone()
        return dict(row) if row else None

    def load_all_qa_state(self) -> list:
        """TASK-61: Lädt den QA-Zustand aller Locations (für Backup-Export).

        Enthält u.a. die manuellen Sperren (description_lock/azimuth_lock/
        focal_length_lock). Analog zu get_qa_state(location_id), aber ohne
        Filter auf eine einzelne Location — für den vollständigen Backup-Export.
        """
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM location_qa_state").fetchall()
        return [dict(row) for row in rows]

    def set_qa_lock(self, location_id: str, field: str, locked: bool) -> None:
        """Setzt Lock-Flag für ein auto-generierbares Feld (Upsert).

        field: 'description' | 'azimuth' | 'focal_length'
        locked: True = manuell gesperrt, kein Auto-Update; False = freigegeben
        """
        col = f"{field}_lock"
        value = 1 if locked else 0
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                conn.execute(
                    f"""INSERT INTO location_qa_state (location_id, {col})
                        VALUES (?, ?)
                        ON CONFLICT(location_id) DO UPDATE SET {col} = excluded.{col}""",
                    (location_id, value),
                )
                conn.execute("COMMIT")
                logger.info(
                    "QA-Lock %s=%s für %s gesetzt", col, value, location_id
                )
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def update_qa_checked(self, location_id: str, geo_hash: str) -> None:
        """Aktualisiert qa_checked_at und geo_hash nach einem QA-Lauf (Upsert)."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                conn.execute(
                    """INSERT INTO location_qa_state
                           (location_id, qa_checked_at, geo_hash)
                       VALUES (?, ?, ?)
                       ON CONFLICT(location_id) DO UPDATE SET
                           qa_checked_at = excluded.qa_checked_at,
                           geo_hash      = excluded.geo_hash""",
                    (location_id, now, geo_hash),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def get_qa_values(self, location_id: str) -> Optional[dict]:
        """Gibt auto-generierte Felder für eine Location zurück, oder None."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM location_qa_values WHERE location_id = ?",
                (location_id,),
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("focal_length_suggestions"):
            d["focal_length_suggestions"] = json.loads(d["focal_length_suggestions"])
        return d

    def set_qa_values(self, location_id: str, **fields) -> None:
        """Speichert auto-generierte Felder für eine Location (Upsert).

        Unterstützte Felder: description, ideal_azimuth_min, ideal_azimuth_max,
        focal_length_suggestions (list → JSON), sightline_status,
        sightline_angle_deg, sightline_checked_at.
        """
        if not fields:
            return
        if "focal_length_suggestions" in fields:
            fields = dict(fields)
            fields["focal_length_suggestions"] = json.dumps(
                fields["focal_length_suggestions"]
            )
        cols = ", ".join(["location_id"] + list(fields.keys()))
        placeholders = ", ".join(["?"] * (1 + len(fields)))
        updates = ", ".join(f"{k} = excluded.{k}" for k in fields)
        sql = (
            f"INSERT INTO location_qa_values ({cols}) VALUES ({placeholders}) "
            f"ON CONFLICT(location_id) DO UPDATE SET {updates}"
        )
        params = [location_id] + list(fields.values())
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                conn.execute(sql, params)
                conn.execute("COMMIT")
                logger.info("QA-Values gesetzt für %s: %s", location_id, list(fields.keys()))
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def load_all_qa_values(self) -> list:
        """Lädt alle QA-Values für den Merge beim Server-Start."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM location_qa_values").fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d.get("focal_length_suggestions"):
                d["focal_length_suggestions"] = json.loads(d["focal_length_suggestions"])
            result.append(d)
        return result


# ---------------------------------------------------------------------------
# TASK-43: Geo-Hash-Berechnung (Modul-Ebene, auch ohne Store-Instanz nutzbar)
# ---------------------------------------------------------------------------

def compute_geo_hash(
    observer_lat: Optional[float],
    observer_lon: Optional[float],
    subject_lat: Optional[float],
    subject_lon: Optional[float],
    subject_height_m: Optional[float],
    subject_width_m: Optional[float],
    distance_m: Optional[float],
) -> str:
    """Deterministischer MD5-Hash der Geo-Kernfelder für Change-Detection.

    Inputs werden auf 6 Dezimalstellen gerundet um Float-Rounding-Artefakte
    zu vermeiden (52.5200001 == 52.52 nach Rounding).
    """
    def _fmt(v: Optional[float]) -> str:
        return f"{round(v, 6):.6f}" if v is not None else "None"

    raw = "|".join([
        _fmt(observer_lat), _fmt(observer_lon),
        _fmt(subject_lat), _fmt(subject_lon),
        _fmt(subject_height_m), _fmt(subject_width_m), _fmt(distance_m),
    ])
    return hashlib.md5(raw.encode()).hexdigest()
