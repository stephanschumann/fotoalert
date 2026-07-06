"""Tests für TASK-55: location_images/ huckepack im Server-Backup sichern.

Deckt die sandbox-fähigen Teile der isolierten Sync-Logik in
`backend/data/backup.py::_sync_image_dir_to_repo()` ab (kein echtes Git-
Backup-Repo in der Sandbox vorhanden — `FOTOALERT_ENV != "prod"` macht den
kompletten `backup_after_edit()`-Pfad zum No-Op, daher wird hier die private
Sync-Funktion direkt und isoliert gegen temporäre Verzeichnisse getestet,
nicht über den vollen Prod-Pfad):

- Neues Bild im Live-Ordner wird in den Backup-Ordner kopiert (AK-1).
- Ersetztes/geändertes Bild wird im Backup-Ordner inhaltlich aktualisiert (AK-2).
- Gelöschtes Bild verschwindet auch aus dem aktuellen Sicherungsstand (AK-3/AK-4:
  TASK-55 macht dabei keinen Unterschied zwischen "Bild einzeln gelöscht" und
  "Location komplett gelöscht" — in beiden Fällen existiert die Datei danach
  im Live-Ordner nicht mehr, die Sync-Funktion behandelt das identisch).
- Leerer Live-Ordner räumt den Backup-Ordner komplett leer.
- Fehlender Live-Ordner lässt die Funktion nicht crashen (gibt sauber zurück).

Nicht abgedeckt (siehe Testreport im Ticket): der volle `backup_after_edit()`-
Pfad inkl. echtem Git-Repo, Push und der tatsächliche Upload-/Delete-Endpoint
im Server — das braucht `FOTOALERT_ENV=prod` und ein echtes Backup-Repo, die
es nur auf dem Produktivserver gibt.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import data.backup as backup  # noqa: E402


@pytest.fixture
def image_dirs(tmp_path, monkeypatch):
    """Ersetzt die Modul-Konstanten _IMAGE_DIR / _IMAGE_BACKUP_DIR durch
    temporäre Verzeichnisse, sodass _sync_image_dir_to_repo() isoliert läuft."""
    live_dir = tmp_path / "location_images"
    backup_dir = tmp_path / "backup-repo" / "location_images"
    live_dir.mkdir(parents=True)
    monkeypatch.setattr(backup, "_IMAGE_DIR", live_dir)
    monkeypatch.setattr(backup, "_IMAGE_BACKUP_DIR", backup_dir)
    return live_dir, backup_dir


# ---------------------------------------------------------------------------
# AK-1: neues Bild wird in den Sicherungsort kopiert
# ---------------------------------------------------------------------------

def test_new_image_is_copied_to_backup(image_dirs):
    live_dir, backup_dir = image_dirs
    (live_dir / "loc-1.jpg").write_bytes(b"neues-bild-inhalt")

    result = backup._sync_image_dir_to_repo()

    assert result is True
    assert (backup_dir / "loc-1.jpg").exists()
    assert (backup_dir / "loc-1.jpg").read_bytes() == b"neues-bild-inhalt"


# ---------------------------------------------------------------------------
# AK-2: ersetztes/geändertes Bild wird im Sicherungsort aktualisiert
# ---------------------------------------------------------------------------

def test_replaced_image_content_is_updated_in_backup(image_dirs):
    live_dir, backup_dir = image_dirs
    (live_dir / "loc-1.jpg").write_bytes(b"alte-version")
    backup._sync_image_dir_to_repo()
    assert (backup_dir / "loc-1.jpg").read_bytes() == b"alte-version"

    # Bild wird ersetzt (gleicher Dateiname, neuer Inhalt — analog zum
    # Upload-Endpunkt, der die alte Datei per Rename ersetzt, US-120).
    (live_dir / "loc-1.jpg").write_bytes(b"neue-version")
    result = backup._sync_image_dir_to_repo()

    assert result is True
    assert (backup_dir / "loc-1.jpg").read_bytes() == b"neue-version"


# ---------------------------------------------------------------------------
# AK-3/AK-4: gelöschtes Bild verschwindet aus dem aktuellen Sicherungsstand
# ---------------------------------------------------------------------------

def test_deleted_image_is_removed_from_backup(image_dirs):
    live_dir, backup_dir = image_dirs
    (live_dir / "loc-1.jpg").write_bytes(b"bild-inhalt")
    (live_dir / "loc-2.jpg").write_bytes(b"anderes-bild")
    backup._sync_image_dir_to_repo()
    assert (backup_dir / "loc-1.jpg").exists()
    assert (backup_dir / "loc-2.jpg").exists()

    # Ein Bild wird live gelöscht (Einzel-Bild-Löschung ODER Location-Löschung
    # — für die Sync-Funktion nicht unterscheidbar, beide entfernen die Datei
    # aus dem Live-Ordner).
    (live_dir / "loc-1.jpg").unlink()
    result = backup._sync_image_dir_to_repo()

    assert result is True
    assert not (backup_dir / "loc-1.jpg").exists()
    assert (backup_dir / "loc-2.jpg").exists(), "unverändertes Bild darf nicht mitgelöscht werden"


# ---------------------------------------------------------------------------
# Leerer Live-Ordner räumt den Backup-Ordner komplett leer
# ---------------------------------------------------------------------------

def test_empty_live_dir_results_in_empty_backup_dir(image_dirs):
    live_dir, backup_dir = image_dirs
    (live_dir / "loc-1.jpg").write_bytes(b"bild-1")
    (live_dir / "loc-2.jpg").write_bytes(b"bild-2")
    backup._sync_image_dir_to_repo()
    assert len(list(backup_dir.iterdir())) == 2

    # Alle Live-Bilder verschwinden (z. B. alle betroffenen Locations gelöscht).
    (live_dir / "loc-1.jpg").unlink()
    (live_dir / "loc-2.jpg").unlink()
    result = backup._sync_image_dir_to_repo()

    assert result is True
    assert list(backup_dir.iterdir()) == []


# ---------------------------------------------------------------------------
# Fehlerfall: Live-Ordner existiert nicht — darf nicht crashen
# ---------------------------------------------------------------------------

def test_missing_live_dir_does_not_raise(tmp_path, monkeypatch):
    """AK-6-Analogon auf Funktionsebene: _sync_image_dir_to_repo() prüft
    _IMAGE_DIR.exists() explizit (siehe backup.py Zeile ~115) und wirft bei
    fehlendem Live-Ordner keine Exception. Der Backup-Zielordner wird trotzdem
    angelegt (leer), es findet nur kein Kopiervorgang statt."""
    live_dir = tmp_path / "location_images_existiert_nicht"
    backup_dir = tmp_path / "backup-repo" / "location_images"
    monkeypatch.setattr(backup, "_IMAGE_DIR", live_dir)
    monkeypatch.setattr(backup, "_IMAGE_BACKUP_DIR", backup_dir)
    assert not live_dir.exists()

    result = backup._sync_image_dir_to_repo()

    assert result is True
    assert backup_dir.exists()
    assert list(backup_dir.iterdir()) == []


def test_sync_error_is_caught_and_returns_false_not_raised(image_dirs, monkeypatch):
    """Prüft die tatsächliche Fehlerbehandlung in backup.py: der komplette
    Funktionskörper von _sync_image_dir_to_repo() steht in einem try/except
    Exception, das im Fehlerfall loggt und False zurückgibt (Zeile ~111-129),
    identisch zum bestehenden Muster in _export_to_repo(). Simuliert hier
    einen Fehler beim Kopieren (z. B. Berechtigungsproblem) über ein
    monkeypatch von shutil.copy2, um zu verifizieren dass keine Exception
    nach außen dringt."""
    live_dir, backup_dir = image_dirs
    (live_dir / "loc-1.jpg").write_bytes(b"bild-inhalt")

    def _boom(*args, **kwargs):
        raise OSError("Simulierter Kopierfehler")

    monkeypatch.setattr(backup.shutil, "copy2", _boom)

    result = backup._sync_image_dir_to_repo()  # darf NICHT raisen

    assert result is False


# ---------------------------------------------------------------------------
# Einbindung in backup_after_edit(): No-Op im Dev-Modus (AK-7)
# ---------------------------------------------------------------------------

def test_backup_after_edit_is_noop_in_dev_mode(image_dirs, monkeypatch):
    """AK-7: Im Dev-Modus (FOTOALERT_ENV != prod, Sandbox-Default) darf
    backup_after_edit() den Bildordner gar nicht erst anfassen — _is_active()
    liefert False und die Funktion kehrt vor jedem Dateizugriff zurück."""
    live_dir, backup_dir = image_dirs
    (live_dir / "loc-1.jpg").write_bytes(b"bild-inhalt")
    monkeypatch.setattr(backup, "_ENV", "dev")

    backup.backup_after_edit("irrelevant-id")

    assert not backup_dir.exists(), "im Dev-Modus darf kein Sicherungsordner entstehen"
