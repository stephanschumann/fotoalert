"""
FotoAlert Backup — RPO≈0 + lokale Snapshots

Drei öffentliche Funktionen:

  backup_after_edit(loc_id)       — nach jedem User-Edit; JSON-Export + Bildordner-Sync + git commit/push
  snapshot_before_precompute()    — vor jedem Precompute-Lauf; lokale DB-Kopie (7 Versionen)
  last_backup_age_hours()         — Stunden seit letztem Git-Commit (für Health-Signal US-38)

Dev-Guard: alle Funktionen sind No-Ops wenn FOTOALERT_ENV != "prod".

Backup-Repo-Pfad: Env-Variable FOTOALERT_BACKUP_REPO,
                  Default /opt/fotoalert/backup-repo

TASK-18: Backup RPO≈0 + Restore (privates Git-Repo)
TASK-55: location_images/ huckepack im selben Backup-Zyklus (Unterordner
         location_images/ im Backup-Repo, per Verzeichnis-Sync auf exakten
         Live-Stand gebracht — gelöschte/ersetzte Bilder verschwinden auch
         aus dem aktuellen Sicherungsstand, keine Altstände als Sicherheitsnetz)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

_ENV         = os.getenv("FOTOALERT_ENV", "prod")
_BACKUP_REPO = Path(os.getenv("FOTOALERT_BACKUP_REPO", "/opt/fotoalert/backup-repo"))
_DATA_DIR    = Path(__file__).parent          # backend/data/
_SNAPSHOTS   = _DATA_DIR / "snapshots"
_RETAIN      = 7                               # maximale Anzahl lokaler Snapshots

# TASK-55: Bildordner (US-120) — Live-Quelle und Zielordner im Backup-Repo
_IMAGE_DIR        = _DATA_DIR / "location_images"
_IMAGE_BACKUP_DIR = _BACKUP_REPO / "location_images"


def _is_active() -> bool:
    """Backup nur im Prod-Modus."""
    return _ENV == "prod"


def _repo_ready() -> bool:
    """Prüft ob das Backup-Repo-Verzeichnis existiert und ein Git-Repo ist."""
    return (_BACKUP_REPO / ".git").exists()


# ---------------------------------------------------------------------------
# JSON-Export aus SQLite
# ---------------------------------------------------------------------------

def _export_to_repo() -> bool:
    """
    Exportiert custom_locations + location_overrides als JSON in das Backup-Repo.
    Gibt True zurück bei Erfolg.
    """
    try:
        # Import hier um zirkuläre Abhängigkeiten zu vermeiden
        from data.store import LocationStore
        store = LocationStore()

        custom = store.load_all_custom()
        overrides_raw = store.load_all_overrides()

        # Overrides zurück in List-of-dict mit id als erstem Feld
        overrides = []
        for ov in overrides_raw:
            loc_id = ov.pop("id", None)
            if loc_id:
                overrides.append({"id": loc_id, **ov})

        (_BACKUP_REPO / "custom_locations.json").write_text(
            json.dumps(custom, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (_BACKUP_REPO / "location_overrides.json").write_text(
            json.dumps(overrides, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True
    except Exception as exc:
        logger.error("Backup-Export fehlgeschlagen: %s", exc)
        return False


# ---------------------------------------------------------------------------
# TASK-55: Bildordner-Sync (location_images/)
# ---------------------------------------------------------------------------

def _sync_image_dir_to_repo() -> bool:
    """
    Bringt den Unterordner location_images/ im Backup-Repo exakt auf den
    aktuellen Live-Stand von backend/data/location_images/:
    - neue/geänderte Dateien werden hineinkopiert
    - Dateien, die live nicht mehr existieren (gelöscht/ersetzt), werden aus
      dem Backup-Repo-Unterordner entfernt (kein Sicherheitsnetz für Altstände,
      Ticket-Entscheidung TASK-55)
    Gibt True zurück bei Erfolg (auch wenn location_images/ live leer/nicht
    vorhanden ist — dann wird nur ein leerer Zielordner sichergestellt).
    """
    try:
        _IMAGE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        live_files = set()
        if _IMAGE_DIR.exists():
            live_files = {p.name for p in _IMAGE_DIR.iterdir() if p.is_file()}

            for name in live_files:
                shutil.copy2(_IMAGE_DIR / name, _IMAGE_BACKUP_DIR / name)

        # Alte Dateien im Backup-Repo entfernen, die live nicht mehr existieren
        backup_files = {p.name for p in _IMAGE_BACKUP_DIR.iterdir() if p.is_file()}
        for stale_name in backup_files - live_files:
            (_IMAGE_BACKUP_DIR / stale_name).unlink()

        return True
    except Exception as exc:
        logger.error("Backup-Bildsync fehlgeschlagen: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Git-Operationen
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess:
    """Führt einen Git-Befehl im Backup-Repo aus."""
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _git_commit_and_push(message: str) -> None:
    """
    git add . → git commit → git push.
    Push-Fehler werden geloggt aber nicht weitergeworfen.
    """
    try:
        _git(["add", "."], _BACKUP_REPO)

        # Prüfen ob es etwas zu committen gibt
        status = _git(["status", "--porcelain"], _BACKUP_REPO)
        if not status.stdout.strip():
            logger.debug("Backup: keine Änderungen, kein Commit nötig.")
            return

        result = _git(["commit", "-m", message], _BACKUP_REPO)
        if result.returncode != 0:
            logger.error("Backup-Commit fehlgeschlagen: %s", result.stderr)
            return
        logger.info("Backup-Commit: %s", message)

        push = _git(["push"], _BACKUP_REPO, timeout=60)
        if push.returncode != 0:
            logger.warning("Backup-Push fehlgeschlagen (wird beim nächsten Lauf nachgeholt): %s", push.stderr.strip())
        else:
            logger.info("Backup-Push erfolgreich.")
    except subprocess.TimeoutExpired:
        logger.warning("Backup-Push Timeout — wird beim nächsten Lauf nachgeholt.")
    except Exception as exc:
        logger.error("Backup Git-Fehler: %s", exc)


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------

def backup_after_edit(loc_id: str) -> None:
    """
    Nach jedem User-Edit aufrufen (in asyncio.to_thread, nicht direkt awaiten).
    Exportiert DB als JSON, bringt location_images/ auf den exakten Live-Stand
    (TASK-55 — neue Bilder rein, gelöschte/ersetzte raus) → git commit + push
    ins Backup-Repo. No-Op im Dev-Modus oder wenn Backup-Repo nicht eingerichtet ist.
    """
    if not _is_active():
        return
    if not _repo_ready():
        logger.warning(
            "Backup-Repo nicht gefunden (%s) — Backup übersprungen. "
            "Server-Setup aus TASK-18 Spec durchführen.",
            _BACKUP_REPO,
        )
        return

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not _export_to_repo():
        return
    # TASK-55: Bildordner-Stand mitsichern, bevor committet wird — Fehler hier
    # sollen die JSON-Sicherung nicht verhindern, daher nur geloggt (siehe
    # _sync_image_dir_to_repo, gleiche Fehlerbehandlung wie _export_to_repo).
    _sync_image_dir_to_repo()
    _git_commit_and_push(f"backup: edit {loc_id} {ts}")


def snapshot_before_precompute() -> None:
    """
    Vor jedem Precompute-Lauf aufrufen.
    Kopiert fotoalert.db → data/snapshots/fotoalert_YYYYMMDD_HHMM.db.
    Behält maximal _RETAIN (7) Snapshots, löscht ältere.
    No-Op im Dev-Modus.
    """
    if not _is_active():
        return

    db_path = _DATA_DIR / "fotoalert.db"
    if not db_path.exists():
        logger.warning("snapshot_before_precompute: fotoalert.db nicht gefunden.")
        return

    try:
        _SNAPSHOTS.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        dest = _SNAPSHOTS / f"fotoalert_{ts}.db"
        shutil.copy2(db_path, dest)
        logger.info("Snapshot angelegt: %s", dest.name)

        # Retention: älteste Snapshots löschen wenn mehr als _RETAIN vorhanden
        existing = sorted(_SNAPSHOTS.glob("fotoalert_*.db"), key=lambda p: p.stat().st_mtime)
        while len(existing) > _RETAIN:
            oldest = existing.pop(0)
            oldest.unlink()
            logger.info("Alter Snapshot gelöscht: %s", oldest.name)
    except Exception as exc:
        logger.error("Snapshot fehlgeschlagen: %s", exc)


def last_backup_age_hours() -> float | None:
    """
    Gibt die Stunden seit dem letzten Git-Commit im Backup-Repo zurück.
    Gibt None zurück wenn Repo nicht vorhanden oder leer.
    Für Health-Signal (US-38): Alarm wenn > 25h.
    """
    if not _repo_ready():
        return None
    try:
        result = _git(["log", "--format=%ct", "-1"], _BACKUP_REPO, timeout=5)
        if result.returncode != 0 or not result.stdout.strip():
            return None
        last_ts = int(result.stdout.strip())
        age_hours = (time.time() - last_ts) / 3600
        return round(age_hours, 2)
    except Exception:
        return None
