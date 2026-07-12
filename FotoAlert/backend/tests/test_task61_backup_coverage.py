"""Tests für TASK-61: Backup-Mechanismus auf alle 8 Datenbank-Tabellen erweitern.

Deckt die sandbox-fähigen Teile von `backend/data/backup.py::_export_to_repo()`
ab (kein echtes Git-Repo in der Sandbox — der volle `backup_after_edit()`- bzw.
`backup_after_precompute()`-Pfad inkl. echtem `git commit`/`push` ist laut
Ticket-Testplan "nicht sinnvoll automatisierbar in der Sandbox" und wird hier
bewusst nicht mitgetestet, analog zu `test_task55_image_backup.py`):

- `_export_to_repo()` exportiert alle 8 Tabellen (nicht mehr nur 2) als je
  eine JSON-Datei mit exaktem Inhalt (AK 1, AK 7, Regressionsschutz).
- Leere Tabellen ergeben gültige leere Listen statt eines Fehlers (AK 5).
- Schlägt eine der neuen `load_all_*`-Methoden fehl, werden die übrigen
  sieben Dateien trotzdem korrekt geschrieben (AK 6, Pre-Mortem Szenario 1 —
  vorher lag ein gemeinsames try/except um die ganze Funktion).
- Dev-Modus bleibt No-Op für beide öffentlichen Trigger-Funktionen
  (`backup_after_edit`, `backup_after_precompute`) — AK 4.

Nicht abgedeckt (siehe Testplan im Ticket): der volle Pfad inkl. echtem
Git-Commit/Push und der tatsächliche Vorberechnungslauf-Trigger-Umfeld — das
braucht `FOTOALERT_ENV=prod` und ein echtes Backup-Repo, das es nur auf dem
Produktivserver gibt.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import data.backup as backup  # noqa: E402
from data.store import LocationStore  # noqa: E402

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# Die 8 vom Export erzeugten Dateinamen (TASK-61).
ALL_EXPORT_FILES = [
    "custom_locations.json",
    "location_overrides.json",
    "location_qa_values.json",
    "location_qa_state.json",
    "location_verifications.json",
    "location_ratings.json",
    "device_tokens.json",
    "camera_profiles.json",
]

# Felder, deren Wert beim Schreiben automatisch mit der aktuellen Uhrzeit
# generiert wird (update_qa_checked/register_device_token) — für den
# Exakt-Vergleich aus Ist- und Soll-Datensatz entfernt, stattdessen separat
# auf "ist ein nicht-leerer String" geprüft.
DYNAMIC_FIELDS = {
    "location_qa_state.json": ["qa_checked_at"],
    "device_tokens.json": ["updated"],
}


def _populate_all_tables(store: LocationStore) -> dict:
    """Befüllt alle 8 Tabellen mit je einer Testzeile (inkl. manueller
    QA-Sperren, AK 3) und gibt die erwarteten Export-Inhalte zurück
    (dynamische Zeitstempel-Felder ausgenommen, siehe DYNAMIC_FIELDS)."""
    custom_loc = {
        "id": "custom_test_1",
        "name": "Test Aussichtspunkt",
        "description": "Schöner Blick auf die Skyline.",
        "category": "SKYLINE",
        "observer_lat": 52.5,
        "observer_lon": 13.4,
        "subject_lat": 52.51,
        "subject_lon": 13.41,
        "subject_name": "Testmotiv",
        "subject_height_m": 10.0,
        "subject_width_m": 5.0,
        "distance_m": 100,
        "focal_length_suggestions": [24, 35],
        "special_notes": "Nur bei Ebbe zugänglich.",
        "difficulty": 2,
        "observer_floor_height_m": 1.5,
    }
    store.create_custom(custom_loc)

    store.upsert_override("base_test_1", name="Override Name", azimuth=180)

    store.set_qa_values(
        "base_test_1",
        description="Auto-generierte Beschreibung.",
        ideal_azimuth_min=100.0,
        ideal_azimuth_max=200.0,
        focal_length_suggestions=[50, 85],
        sightline_status="frei",
        sightline_angle_deg=12.5,
        sightline_checked_at="2026-07-01T08:00:00Z",
    )

    # Manuelle Sperren (AK 3: müssen im gesicherten Datenbestand enthalten sein)
    store.set_qa_lock("base_test_1", "description", True)
    store.set_qa_lock("base_test_1", "azimuth", True)
    store.set_qa_lock("base_test_1", "focal_length", False)
    store.update_qa_checked("base_test_1", "geohash-abc123")

    store.add_verification(
        location_id="base_test_1",
        location_name="Basis Location",
        status="issue",
        issue_type="zugang_versperrt",
        comment="Zaun neu errichtet.",
        date="2026-07-01",
    )

    store.upsert_rating("base_test_1", "device-abc", 5, "2026-07-01T10:00:00Z")

    store.register_device_token(token="tok-123", platform="ios", device_id="dev-xyz")

    store.upsert_camera_profile(
        "dev-xyz", "fullframe", 35, "landscape", "2026-07-01T09:00:00Z"
    )

    return {
        "custom_locations.json": [{
            **custom_loc,
            "ideal_azimuth_min": None,
            "ideal_azimuth_max": None,
            "image_filename": None,
            "image_focus_x": None,
            "image_focus_y": None,
        }],
        "location_overrides.json": [
            {"id": "base_test_1", "name": "Override Name", "azimuth": 180}
        ],
        "location_qa_values.json": [{
            "location_id": "base_test_1",
            "description": "Auto-generierte Beschreibung.",
            "ideal_azimuth_min": 100.0,
            "ideal_azimuth_max": 200.0,
            "focal_length_suggestions": [50, 85],
            "sightline_status": "frei",
            "sightline_angle_deg": 12.5,
            "sightline_checked_at": "2026-07-01T08:00:00Z",
        }],
        "location_qa_state.json": [{
            "location_id": "base_test_1",
            "description_lock": 1,
            "azimuth_lock": 1,
            "focal_length_lock": 0,
            "geo_hash": "geohash-abc123",
            # qa_checked_at: dynamisch, siehe DYNAMIC_FIELDS
        }],
        "location_verifications.json": [{
            "id": 1,
            "location_id": "base_test_1",
            "location_name": "Basis Location",
            "status": "issue",
            "issue_type": "zugang_versperrt",
            "comment": "Zaun neu errichtet.",
            "date": "2026-07-01",
        }],
        "location_ratings.json": [
            {"location_id": "base_test_1", "device_id": "device-abc", "value": 5}
        ],
        "device_tokens.json": [{
            "token": "tok-123",
            "platform": "ios",
            "device_id": "dev-xyz",
            # updated: dynamisch, siehe DYNAMIC_FIELDS
        }],
        "camera_profiles.json": [{
            "device_id": "dev-xyz",
            "sensor": "fullframe",
            "fl": 35,
            "ori": "landscape",
            "updated": "2026-07-01T09:00:00Z",
        }],
    }


def _strip_dynamic(filename: str, records: list) -> list:
    """Entfernt automatisch generierte Zeitstempel-Felder aus den gelesenen
    Datensätzen, nachdem geprüft wurde, dass sie überhaupt vorhanden und
    nicht-leer sind (siehe DYNAMIC_FIELDS)."""
    fields = DYNAMIC_FIELDS.get(filename, [])
    stripped = []
    for rec in records:
        rec = dict(rec)
        for f in fields:
            value = rec.pop(f, None)
            assert isinstance(value, str) and value, (
                f"{filename}: dynamisches Feld '{f}' fehlt oder ist leer: {value!r}"
            )
        stripped.append(rec)
    return stripped


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def export_env(tmp_path, monkeypatch):
    """Richtet ein isoliertes Backup-Repo-Verzeichnis + eine echte
    LocationStore-Instanz gegen eine temporäre SQLite-Datei ein und lenkt den
    internen `LocationStore()`-Aufruf in `_export_to_repo()` (der immer den
    Default-Pfad verwendet) auf dieselbe temporäre Datei um.

    Kein Zugriff auf die aktive Dev-/Prod-Datenbank (BUG-61-Regel) — jede
    Testzeile lebt ausschließlich in dieser tmp_path-Datei.
    """
    repo_dir = tmp_path / "backup-repo"
    repo_dir.mkdir()
    monkeypatch.setattr(backup, "_BACKUP_REPO", repo_dir)

    db_path = tmp_path / "test.db"
    store = LocationStore(db_path=db_path)
    # _export_to_repo() instanziiert intern `LocationStore()` ohne Pfadangabe
    # (Default-Parameter, einmalig beim Modul-Import von store.py gebunden).
    # Um diesen internen Aufruf auf dieselbe Testdatenbank umzulenken, wird
    # der Default-Parameter des Konstruktors direkt gepatcht statt über eine
    # Umgebungsvariable (die _DEFAULT_DB in store.py wäre zu diesem
    # Zeitpunkt bereits gebunden und würde eine Env-Änderung nicht mehr sehen).
    monkeypatch.setattr(LocationStore.__init__, "__defaults__", (db_path,))

    return repo_dir, store


# ---------------------------------------------------------------------------
# AK 1 / AK 7 / Regressionsschutz: alle 8 Tabellen werden exportiert, Inhalt exakt
# ---------------------------------------------------------------------------

def test_export_writes_all_eight_tables_with_exact_content(export_env):
    repo_dir, store = export_env
    expected = _populate_all_tables(store)

    result = backup._export_to_repo()

    assert result is True
    for filename in ALL_EXPORT_FILES:
        path = repo_dir / filename
        assert path.exists(), f"{filename} wurde nicht geschrieben"
        actual = _strip_dynamic(filename, _read_json(path))
        assert actual == expected[filename], f"Inhalt von {filename} weicht vom erwarteten Datensatz ab"


# ---------------------------------------------------------------------------
# AK 5: leere Tabelle -> gültige leere Liste, kein Fehler
# ---------------------------------------------------------------------------

def test_export_with_empty_tables_writes_valid_empty_lists(export_env):
    repo_dir, _store = export_env
    # Keine Testzeilen angelegt — alle 8 Tabellen sind leer.

    result = backup._export_to_repo()

    assert result is True
    for filename in ALL_EXPORT_FILES:
        path = repo_dir / filename
        assert path.exists(), f"{filename} wurde bei leerer Tabelle nicht geschrieben"
        assert _read_json(path) == [], (
            f"{filename} sollte bei leerer Tabelle eine gültige leere Liste enthalten, kein Fehler"
        )


# ---------------------------------------------------------------------------
# AK 6 / Pre-Mortem Szenario 1: einzelne fehlschlagende Tabelle bricht nicht
# die Sicherung der übrigen sieben ab (pro-Tabelle-Kapselung statt einem
# gemeinsamen try/except um die ganze Funktion)
# ---------------------------------------------------------------------------

def test_single_table_failure_does_not_prevent_other_seven(export_env, monkeypatch):
    repo_dir, store = export_env
    expected = _populate_all_tables(store)

    def _boom(self):
        raise sqlite3.OperationalError("Simulierter Lesefehler in location_verifications")

    # Eine der drei NEUEN load_all_*-Methoden (TASK-61) gezielt zum Werfen
    # einer Exception bringen — auf Klassenebene, damit auch die intern in
    # _export_to_repo() neu instanziierte LocationStore-Instanz betroffen ist.
    monkeypatch.setattr(LocationStore, "load_all_verifications", _boom)

    result = backup._export_to_repo()

    assert result is True, "_export_to_repo() darf trotz Einzel-Tabellenfehler nicht insgesamt fehlschlagen"

    # Die fehlgeschlagene Tabelle hat keine (oder eine veraltete) Datei —
    # entscheidend ist, dass die übrigen sieben trotzdem korrekt geschrieben wurden.
    for filename in ALL_EXPORT_FILES:
        if filename == "location_verifications.json":
            continue
        path = repo_dir / filename
        assert path.exists(), f"{filename} fehlt, obwohl nur location_verifications fehlschlagen sollte"
        actual = _strip_dynamic(filename, _read_json(path))
        assert actual == expected[filename], f"Inhalt von {filename} weicht vom erwarteten Datensatz ab"


# ---------------------------------------------------------------------------
# AK 4: Dev-Modus bleibt No-Op — kein Zugriff aufs Backup-Repo, kein Export
# ---------------------------------------------------------------------------

def test_backup_after_edit_is_noop_in_dev_mode(export_env, monkeypatch):
    repo_dir, store = export_env
    _populate_all_tables(store)
    monkeypatch.setattr(backup, "_ENV", "dev")

    backup.backup_after_edit("irrelevant-id")

    for filename in ALL_EXPORT_FILES:
        assert not (repo_dir / filename).exists(), (
            f"{filename} darf im Dev-Modus nicht entstehen (backup_after_edit)"
        )


def test_backup_after_precompute_is_noop_in_dev_mode(export_env, monkeypatch):
    """TASK-61 Option B: backup_after_precompute() ist der neue zweite
    Trigger-Zeitpunkt (Vorberechnungslauf) — muss denselben Dev-Guard wie
    backup_after_edit() haben."""
    repo_dir, store = export_env
    _populate_all_tables(store)
    monkeypatch.setattr(backup, "_ENV", "dev")

    backup.backup_after_precompute()

    for filename in ALL_EXPORT_FILES:
        assert not (repo_dir / filename).exists(), (
            f"{filename} darf im Dev-Modus nicht entstehen (backup_after_precompute)"
        )
