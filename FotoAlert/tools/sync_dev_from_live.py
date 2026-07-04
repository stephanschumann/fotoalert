"""
FotoAlert — Live-Datenbank nach Dev spiegeln (TASK-53)

Manuell von Stephans Mac aus gestartetes Werkzeug. Holt die aktuelle
Live-Datenbankdatei vom Hetzner-Server (nur lesend) und ersetzt damit die
lokale Dev-Datenbank (backend/data_dev/fotoalert.db).

Richtung ist fest verdrahtet: Live -> Dev. Es gibt bewusst KEINE
Kommandozeilen-Parameter, die Quelle/Ziel oder die Richtung ändern könnten
(Pre-Mortem Szenario 2). Die Live-Seite wird ausschließlich per `scp` gelesen,
niemals beschrieben.

Ablauf:
  1. Alte Dev-DB automatisch mit Zeitstempel wegsichern (Snapshot, max. 5
     Stände, analog backend/data/backup.py::snapshot_before_precompute()).
  2. Live-DB-Datei per `scp` über den Server-User `fotoalert-server` in eine
     temporäre Datei im selben Zielverzeichnis herunterladen (NICHT root,
     siehe Memory feedback_fotoalert_server_users).
  3. Nur bei vollständigem Download: temporäre Datei atomar (os.replace) an
     die Stelle der alten Dev-DB verschieben. Bricht der Download ab, bleibt
     die alte Dev-DB unverändert (Edge Case Verbindungsabbruch, AK-4/AK-5).
  4. Zusammenfassung ausgeben: Zeilenzahl je Kerntabelle vorher/nachher.

Aufruf (auf Stephans Mac, aus dem FotoAlert-Verzeichnis):
    python3 tools/sync_dev_from_live.py

Voraussetzung: SSH-Host-Alias "fotoalert-server" ist in ~/.ssh/config auf den
User fotoalert-server @ 167.233.138.36 konfiguriert (bestehende Konvention,
siehe Memory feedback_fotoalert_server_users / reference_fotoalert_server_paths).

Python-3.9-kompatibel (kein `str | None`, kein `match`-Statement).

TASK-53: Live-Nutzerdaten periodisch nach Dev spiegeln (Option A, v1-Slice:
manuell auf Zuruf, keine Cron-Automatisierung).
"""

from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Feste Konfiguration — bewusst keine CLI-Parameter für diese Werte.
# ---------------------------------------------------------------------------

# Quelle: IMMER Live, IMMER lesend. Server-User laut Memory
# feedback_fotoalert_server_users: fotoalert-server, nicht root.
_SSH_HOST = "fotoalert-server"
_LIVE_DB_PATH = "/opt/fotoalert/app/FotoAlert/backend/data/fotoalert.db"

# Ziel: IMMER die lokale Dev-DB (Pfadauflösung analog backend/data/store.py
# Z.34-40 bei FOTOALERT_ENV != "prod").
_TOOLS_DIR = Path(__file__).parent
_BACKEND_DIR = _TOOLS_DIR.parent / "backend"
_DEV_DB_PATH = _BACKEND_DIR / "data_dev" / "fotoalert.db"

# Snapshot-Ablage + Aufbewahrung, analog backend/data/backup.py (dort 7,
# hier 5 gemäß Ticket-Spec "z.B. letzte 5 Stände").
_SNAPSHOT_DIR = _BACKEND_DIR / "data_dev" / "snapshots"
_RETAIN = 5

# Tabellen für die Abschluss-Zusammenfassung (Standorte, Bewertungen,
# Meldungen — siehe backend/data/store.py Tabellenliste).
_SUMMARY_TABLES = [
    "custom_locations",
    "location_overrides",
    "location_verifications",
    "location_ratings",
]


class SyncError(Exception):
    """Eigene Fehlerklasse für alle Abbruch-Fälle dieses Werkzeugs."""


# ---------------------------------------------------------------------------
# Schritt 1 — Dev-DB wegsichern (Snapshot-Prinzip wie backup.py)
# ---------------------------------------------------------------------------

def snapshot_dev_db(dev_db_path: Path = _DEV_DB_PATH,
                     snapshot_dir: Path = _SNAPSHOT_DIR,
                     retain: int = _RETAIN) -> Optional[Path]:
    """
    Kopiert die aktuelle Dev-DB nach snapshot_dir mit Zeitstempel im Namen.
    Behält maximal `retain` Snapshots, löscht die ältesten zuerst.

    Gibt den Pfad des neuen Snapshots zurück, oder None wenn keine Dev-DB
    existiert (z.B. beim allerersten Lauf — kein Fehler, nur nichts zu sichern).
    """
    if not dev_db_path.exists():
        return None

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = snapshot_dir / f"fotoalert_dev_{ts}.db"
    shutil.copy2(dev_db_path, dest)

    existing = sorted(snapshot_dir.glob("fotoalert_dev_*.db"), key=lambda p: p.stat().st_mtime)
    while len(existing) > retain:
        oldest = existing.pop(0)
        oldest.unlink()

    return dest


# ---------------------------------------------------------------------------
# Schritt 2 — Live-DB per scp holen (nur lesend auf der Live-Seite)
# ---------------------------------------------------------------------------

def fetch_live_db(dest_tmp_path: Path,
                   ssh_host: str = _SSH_HOST,
                   live_db_path: str = _LIVE_DB_PATH) -> None:
    """
    Lädt die Live-DB-Datei per scp in dest_tmp_path herunter.
    Wirft SyncError bei jedem Fehlschlag (Verbindungsabbruch, Timeout,
    Permission denied etc.) — der Aufrufer entscheidet dann, dass die alte
    Dev-DB unangetastet bleibt.

    Quelle ist immer `ssh_host:live_db_path` (Live, lesend). Es gibt keinen
    Parameter, der Quelle und Ziel vertauschen könnte.
    """
    remote_spec = f"{ssh_host}:{live_db_path}"
    try:
        result = subprocess.run(
            ["scp", "-o", "ConnectTimeout=15", remote_spec, str(dest_tmp_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        raise SyncError(
            "Verbindung zum Live-Server ist beim Kopieren abgebrochen (Timeout). "
            "Die lokale Dev-Datenbank wurde nicht verändert."
        )
    except FileNotFoundError:
        raise SyncError(
            "Das Kommandozeilenwerkzeug 'scp' wurde nicht gefunden. "
            "Die lokale Dev-Datenbank wurde nicht verändert."
        )

    if result.returncode != 0:
        raise SyncError(
            "Live-Datenbank konnte nicht geholt werden (scp-Fehler): "
            f"{result.stderr.strip()}. Die lokale Dev-Datenbank wurde nicht verändert."
        )

    if not dest_tmp_path.exists() or dest_tmp_path.stat().st_size == 0:
        raise SyncError(
            "Live-Datenbank wurde scheinbar übertragen, die Zieldatei ist aber leer "
            "oder fehlt. Die lokale Dev-Datenbank wurde nicht verändert."
        )


# ---------------------------------------------------------------------------
# Schritt 3 — Atomarer Ersatz
# ---------------------------------------------------------------------------

def replace_dev_db(tmp_path: Path, dev_db_path: Path = _DEV_DB_PATH) -> None:
    """
    Ersetzt dev_db_path atomar durch tmp_path (os.replace = eine
    Dateisystem-Operation, kein Zwischenzustand mit halber Datei).

    Zusätzlich werden ggf. vorhandene WAL/SHM-Begleitdateien der alten Dev-DB
    entfernt, damit SQLite beim nächsten Öffnen nicht versehentlich alte
    WAL-Daten mit der neuen DB-Datei vermischt.
    """
    dev_db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.replace(dev_db_path)

    for suffix in ("-wal", "-shm"):
        stale = Path(str(dev_db_path) + suffix)
        if stale.exists():
            stale.unlink()


# ---------------------------------------------------------------------------
# Zusammenfassung — Zeilenzahl je Kerntabelle
# ---------------------------------------------------------------------------

def count_rows(db_path: Path, tables: Optional[list] = None) -> Dict[str, Optional[int]]:
    """
    Liefert {tabellenname: anzahl_zeilen} für die übergebenen Tabellen.
    Fehlt eine Tabelle oder existiert die Datei nicht, steht dort None statt
    eines Absturzes (z.B. beim allerersten Lauf ohne vorherige Dev-DB).
    """
    if tables is None:
        tables = _SUMMARY_TABLES

    counts: Dict[str, Optional[int]] = {}
    if not db_path.exists():
        return {t: None for t in tables}

    conn = sqlite3.connect(str(db_path))
    try:
        for table in tables:
            try:
                cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cur.fetchone()[0]
            except sqlite3.OperationalError:
                counts[table] = None
    finally:
        conn.close()
    return counts


def format_summary(before: Dict[str, Optional[int]], after: Dict[str, Optional[int]]) -> str:
    lines = ["Zusammenfassung (Zeilen je Tabelle, vorher -> nachher):"]
    for table in _SUMMARY_TABLES:
        b = before.get(table)
        a = after.get(table)
        b_str = "–" if b is None else str(b)
        a_str = "–" if a is None else str(a)
        lines.append(f"  {table}: {b_str} -> {a_str}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Orchestrierung
# ---------------------------------------------------------------------------

def run_sync() -> int:
    """
    Führt den kompletten Sync-Ablauf aus. Gibt einen Exit-Code zurück
    (0 = Erfolg, 1 = Fehler) statt sys.exit direkt aufzurufen, damit die
    Funktion auch aus Tests heraus aufrufbar bleibt.
    """
    print(f"FotoAlert Dev-Sync (TASK-53) — Quelle: {_SSH_HOST}:{_LIVE_DB_PATH}")
    print(f"Ziel: {_DEV_DB_PATH}")
    print()

    before_counts = count_rows(_DEV_DB_PATH)

    print("Schritt 1/3: Aktuelle Dev-Datenbank wegsichern ...")
    try:
        snapshot_path = snapshot_dev_db()
    except OSError as exc:
        print(f"FEHLER: Sicherung der Dev-Datenbank fehlgeschlagen: {exc}")
        print("Abbruch — Live-Server wurde nicht kontaktiert.")
        return 1

    if snapshot_path is None:
        print("  Keine bestehende Dev-Datenbank gefunden — nichts zu sichern (erster Lauf).")
    else:
        print(f"  Gesichert nach: {snapshot_path}")

    print("Schritt 2/3: Live-Datenbank holen (nur lesend, ssh-User: fotoalert-server) ...")
    tmp_path = _DEV_DB_PATH.parent / f"{_DEV_DB_PATH.name}.incoming.tmp"
    try:
        fetch_live_db(tmp_path)
    except SyncError as exc:
        print(f"FEHLER: {exc}")
        if tmp_path.exists():
            tmp_path.unlink()
        return 1

    print("Schritt 3/3: Dev-Datenbank ersetzen ...")
    try:
        replace_dev_db(tmp_path)
    except OSError as exc:
        print(f"FEHLER beim Ersetzen der Dev-Datenbank: {exc}")
        print("Die heruntergeladene Live-Kopie liegt weiterhin unter:")
        print(f"  {tmp_path}")
        print("Die bisherige Dev-Datenbank wurde nicht angetastet.")
        return 1

    after_counts = count_rows(_DEV_DB_PATH)

    print()
    print(format_summary(before_counts, after_counts))
    print()
    print("Sync erfolgreich abgeschlossen. Live wurde ausschließlich lesend angefasst.")
    return 0


def main() -> int:
    try:
        return run_sync()
    except KeyboardInterrupt:
        print("\nAbgebrochen durch Nutzer. Die Dev-Datenbank wurde nicht verändert "
              "(Ersetzen geschieht erst nach vollständigem Download).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
