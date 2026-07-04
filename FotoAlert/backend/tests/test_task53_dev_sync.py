"""Tests für TASK-53: Live-Nutzerdaten periodisch nach Dev spiegeln.

Deckt die sandbox-fähigen Teile ab (kein echter SSH/SCP-Zugriff auf den
Hetzner-Live-Server möglich, daher wird `subprocess.run` gemockt):

- Sicherungsfunktion legt vor dem Ersetzen eine Zeitstempel-Kopie der alten
  Dev-DB an, mit Aufbewahrungslimit (AK-4).
- Atomarer Ersatz: nach simuliertem "Download" enthält die Dev-DB exakt den
  Inhalt der Quelldatei, alte Dev-only-Einträge sind weg (AK-1/AK-2).
- Verbindungsabbruch beim Kopieren lässt die alte Dev-DB unangetastet zurück,
  kein korrupter Zwischenzustand (Edge Case, AK-4/AK-5).
- Zusammenfassung zählt Zeilen je Kerntabelle korrekt (AK-5).
- Kein echter SSH/SCP-Verbindungstest gegen den Live-Server — das ist ein
  manueller Testschritt für Stephan (siehe Testplan im BACKLOG.md-Ticket).
"""

from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

import sync_dev_from_live as sync_tool


# ---------------------------------------------------------------------------
# Hilfsfunktionen für Test-Datenbanken
# ---------------------------------------------------------------------------

def _make_db(path: Path, custom_location_ids):
    """Legt eine minimale SQLite-Datei mit einer custom_locations-Tabelle an
    und füllt sie mit den übergebenen IDs (id ist Primärschlüssel/TEXT)."""
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "CREATE TABLE custom_locations (id TEXT PRIMARY KEY, name TEXT)"
        )
        conn.execute(
            "CREATE TABLE location_overrides (id TEXT PRIMARY KEY, name TEXT)"
        )
        conn.execute(
            "CREATE TABLE location_verifications (id INTEGER PRIMARY KEY, location_id TEXT)"
        )
        conn.execute(
            "CREATE TABLE location_ratings (id INTEGER PRIMARY KEY, location_id TEXT, stars INTEGER)"
        )
        for loc_id in custom_location_ids:
            conn.execute(
                "INSERT INTO custom_locations (id, name) VALUES (?, ?)",
                (loc_id, f"Location {loc_id}"),
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schritt 1 — Snapshot-Funktion (AK-4)
# ---------------------------------------------------------------------------

def test_snapshot_creates_timestamped_copy(tmp_path):
    dev_db = tmp_path / "fotoalert.db"
    _make_db(dev_db, ["dev-only-1"])
    snapshot_dir = tmp_path / "snapshots"

    result = sync_tool.snapshot_dev_db(dev_db_path=dev_db, snapshot_dir=snapshot_dir, retain=5)

    assert result is not None
    assert result.exists()
    assert result.parent == snapshot_dir
    # Ursprüngliche Dev-DB bleibt unverändert liegen (Snapshot ist eine Kopie)
    assert dev_db.exists()


def test_snapshot_noop_when_no_dev_db_exists(tmp_path):
    dev_db = tmp_path / "fotoalert.db"  # existiert nicht
    snapshot_dir = tmp_path / "snapshots"

    result = sync_tool.snapshot_dev_db(dev_db_path=dev_db, snapshot_dir=snapshot_dir, retain=5)

    assert result is None
    assert not snapshot_dir.exists() or list(snapshot_dir.glob("*")) == []


def test_snapshot_retention_keeps_only_last_n(tmp_path):
    dev_db = tmp_path / "fotoalert.db"
    _make_db(dev_db, ["x"])
    snapshot_dir = tmp_path / "snapshots"

    created = []
    for i in range(8):
        # Eindeutige mtimes erzwingen, damit die Sortierung nach Alter stabil ist.
        result = sync_tool.snapshot_dev_db(dev_db_path=dev_db, snapshot_dir=snapshot_dir, retain=5)
        created.append(result)
        # Zeitstempel im Dateinamen hat Sekundenauflösung; für den Test reicht
        # es, mtime künstlich zu erhöhen statt echt zu warten.
        result_stat = result.stat()
        import os
        os.utime(result, (result_stat.st_atime, result_stat.st_mtime + i))

    remaining = sorted(snapshot_dir.glob("fotoalert_dev_*.db"))
    assert len(remaining) <= 5, "Retention muss auf maximal 5 Snapshots begrenzen (AK-4)"


# ---------------------------------------------------------------------------
# Schritt 2/3 — Fetch (gemockt) + atomarer Ersatz (AK-1, AK-2)
# ---------------------------------------------------------------------------

def test_replace_dev_db_matches_source_exactly(tmp_path):
    """AK-1/AK-2: Nach dem Ersetzen entspricht die Dev-DB exakt der Quelle;
    alte Dev-only-Einträge sind weg."""
    dev_db = tmp_path / "data_dev" / "fotoalert.db"
    dev_db.parent.mkdir(parents=True)
    _make_db(dev_db, ["dev-only-standort"])  # simulierter alter Dev-Testdaten-Stand

    # Simulierte "Live"-Quelle mit anderem Inhalt.
    live_like = tmp_path / "live_fetched.db"
    _make_db(live_like, ["live-standort-1", "live-standort-2"])

    tmp_incoming = dev_db.parent / f"{dev_db.name}.incoming.tmp"
    shutil.copy2(live_like, tmp_incoming)  # steht für einen erfolgreichen "Download"

    sync_tool.replace_dev_db(tmp_incoming, dev_db_path=dev_db)

    conn = sqlite3.connect(str(dev_db))
    try:
        ids = {row[0] for row in conn.execute("SELECT id FROM custom_locations")}
    finally:
        conn.close()

    assert ids == {"live-standort-1", "live-standort-2"}
    assert "dev-only-standort" not in ids
    assert not tmp_incoming.exists(), "temporäre Datei muss nach os.replace verschwunden sein"


def test_replace_dev_db_removes_stale_wal_shm(tmp_path):
    """Alte WAL/SHM-Begleitdateien der vorigen Dev-DB dürfen nach dem Ersetzen
    nicht mit der neuen Datenbankdatei vermischt werden."""
    dev_db = tmp_path / "fotoalert.db"
    _make_db(dev_db, ["a"])
    (Path(str(dev_db) + "-wal")).write_bytes(b"stale-wal")
    (Path(str(dev_db) + "-shm")).write_bytes(b"stale-shm")

    live_like = tmp_path / "live_fetched.db"
    _make_db(live_like, ["b"])
    tmp_incoming = dev_db.parent / f"{dev_db.name}.incoming.tmp"
    shutil.copy2(live_like, tmp_incoming)

    sync_tool.replace_dev_db(tmp_incoming, dev_db_path=dev_db)

    assert not Path(str(dev_db) + "-wal").exists()
    assert not Path(str(dev_db) + "-shm").exists()


# ---------------------------------------------------------------------------
# Edge Case — Verbindungsabbruch (AK-4/AK-5, Edge Case aus dem Ticket)
# ---------------------------------------------------------------------------

def test_fetch_live_db_raises_on_scp_failure(monkeypatch, tmp_path):
    """Schlägt scp fehl (z.B. Verbindungsabbruch), muss fetch_live_db einen
    SyncError werfen statt eine (halbe/leere) Zieldatei als Erfolg zu werten."""

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args, returncode=1, stdout="", stderr="ssh: connect to host timed out"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    dest = tmp_path / "fotoalert.db.incoming.tmp"
    with pytest.raises(sync_tool.SyncError):
        sync_tool.fetch_live_db(dest)


def test_fetch_live_db_raises_on_timeout(monkeypatch, tmp_path):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="scp", timeout=120)

    monkeypatch.setattr(subprocess, "run", fake_run)

    dest = tmp_path / "fotoalert.db.incoming.tmp"
    with pytest.raises(sync_tool.SyncError):
        sync_tool.fetch_live_db(dest)


def test_connection_abort_leaves_old_dev_db_untouched(monkeypatch, tmp_path):
    """End-to-End-Simulation des Edge Case aus dem Ticket: Verbindung bricht
    während der Übertragung ab -> Dev bleibt beim alten (weggesicherten)
    Stand, kein korrupter Zwischenzustand."""
    dev_db = tmp_path / "backend" / "data_dev" / "fotoalert.db"
    dev_db.parent.mkdir(parents=True)
    _make_db(dev_db, ["alter-dev-stand"])

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="scp", timeout=120)

    monkeypatch.setattr(subprocess, "run", fake_run)

    tmp_incoming = dev_db.parent / f"{dev_db.name}.incoming.tmp"
    with pytest.raises(sync_tool.SyncError):
        sync_tool.fetch_live_db(tmp_incoming)

    # Die alte Dev-DB darf durch den fehlgeschlagenen Fetch nicht angefasst
    # worden sein - replace_dev_db wurde ja nie erreicht.
    assert dev_db.exists()
    conn = sqlite3.connect(str(dev_db))
    try:
        ids = {row[0] for row in conn.execute("SELECT id FROM custom_locations")}
    finally:
        conn.close()
    assert ids == {"alter-dev-stand"}


def test_fetch_live_db_raises_when_destination_empty(monkeypatch, tmp_path):
    """Auch ein technisch 'erfolgreicher' scp-Aufruf (returncode 0), der aber
    keine oder eine leere Datei hinterlässt, darf nicht als Erfolg gelten."""

    dest = tmp_path / "fotoalert.db.incoming.tmp"

    def fake_run(*args, **kwargs):
        # Zieldatei absichtlich nicht anlegen, simuliert Abbruch nach
        # positivem Verbindungsaufbau aber vor vollständigem Transfer.
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(sync_tool.SyncError):
        sync_tool.fetch_live_db(dest)


# ---------------------------------------------------------------------------
# Zusammenfassung (AK-5)
# ---------------------------------------------------------------------------

def test_count_rows_reports_table_counts(tmp_path):
    db = tmp_path / "fotoalert.db"
    _make_db(db, ["a", "b", "c"])

    counts = sync_tool.count_rows(db, tables=["custom_locations", "location_ratings"])

    assert counts["custom_locations"] == 3
    assert counts["location_ratings"] == 0


def test_count_rows_none_when_db_missing(tmp_path):
    db = tmp_path / "does_not_exist.db"
    counts = sync_tool.count_rows(db, tables=["custom_locations"])
    assert counts["custom_locations"] is None


def test_format_summary_shows_before_and_after():
    before = {"custom_locations": 5, "location_overrides": 0,
              "location_verifications": 2, "location_ratings": 1}
    after = {"custom_locations": 20, "location_overrides": 3,
             "location_verifications": 8, "location_ratings": 4}

    text = sync_tool.format_summary(before, after)

    assert "5 -> 20" in text
    assert "custom_locations" in text
