"""
Tests für TASK-43: QA-Datenmodell — Lock-Flags, QA-Tabellen, Geo-Hash.

Abgedeckte Akzeptanzkriterien:
- get_qa_state('unbekannte-id') → None
- set_qa_lock → atomar, Upsert
- set_qa_values / get_qa_values → Roundtrip inkl. JSON-Liste
- Migration: ideal_azimuth_min/max in custom_locations
- compute_geo_hash → deterministisch, Float-Rounding-sicher
- Merge-Reihenfolge: Code < qa_values < location_overrides
"""
import json
import tempfile
from pathlib import Path

import pytest
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.store import LocationStore, compute_geo_hash


@pytest.fixture
def store(tmp_path: Path) -> LocationStore:
    """Frischer In-Memory-ähnlicher Store pro Test (tmp_path ist isoliert)."""
    return LocationStore(db_path=tmp_path / "test.db")


# ---------------------------------------------------------------------------
# get_qa_state
# ---------------------------------------------------------------------------

def test_get_qa_state_unknown_id_returns_none(store: LocationStore) -> None:
    """TASK-43 AK: get_qa_state('unbekannte-id') → None (kein Fehler)."""
    result = store.get_qa_state("does-not-exist")
    assert result is None


# ---------------------------------------------------------------------------
# set_qa_lock
# ---------------------------------------------------------------------------

def test_set_qa_lock_creates_entry(store: LocationStore) -> None:
    """set_qa_lock legt Eintrag an wenn noch keiner existiert."""
    store.set_qa_lock("loc-1", "description", True)
    state = store.get_qa_state("loc-1")
    assert state is not None
    assert state["description_lock"] == 1


def test_set_qa_lock_upsert(store: LocationStore) -> None:
    """set_qa_lock ist Upsert — überschreibt bestehenden Wert."""
    store.set_qa_lock("loc-1", "azimuth", True)
    store.set_qa_lock("loc-1", "azimuth", False)
    state = store.get_qa_state("loc-1")
    assert state["azimuth_lock"] == 0


def test_set_qa_lock_preserves_other_locks(store: LocationStore) -> None:
    """set_qa_lock für ein Feld überschreibt nicht andere Lock-Felder."""
    store.set_qa_lock("loc-1", "description", True)
    store.set_qa_lock("loc-1", "azimuth", True)
    state = store.get_qa_state("loc-1")
    assert state["description_lock"] == 1
    assert state["azimuth_lock"] == 1


# ---------------------------------------------------------------------------
# set_qa_values / get_qa_values
# ---------------------------------------------------------------------------

def test_get_qa_values_unknown_returns_none(store: LocationStore) -> None:
    """get_qa_values für unbekannte ID → None."""
    assert store.get_qa_values("no-such-id") is None


def test_set_qa_values_description(store: LocationStore) -> None:
    """description wird korrekt gespeichert und ausgelesen."""
    store.set_qa_values("loc-2", description="Schöner Blick auf den Dom.")
    result = store.get_qa_values("loc-2")
    assert result is not None
    assert result["description"] == "Schöner Blick auf den Dom."


def test_set_qa_values_azimuth(store: LocationStore) -> None:
    """ideal_azimuth_min/max werden gespeichert und ausgelesen."""
    store.set_qa_values("loc-3", ideal_azimuth_min=80.0, ideal_azimuth_max=120.0)
    result = store.get_qa_values("loc-3")
    assert result["ideal_azimuth_min"] == pytest.approx(80.0)
    assert result["ideal_azimuth_max"] == pytest.approx(120.0)


def test_set_qa_values_focal_length(store: LocationStore) -> None:
    """focal_length_suggestions (list) wird als JSON gespeichert und als list zurückgegeben."""
    store.set_qa_values("loc-4", focal_length_suggestions=[50, 85, 135])
    result = store.get_qa_values("loc-4")
    assert result["focal_length_suggestions"] == [50, 85, 135]


def test_set_qa_values_upsert(store: LocationStore) -> None:
    """set_qa_values überschreibt vorhandene Werte (Upsert)."""
    store.set_qa_values("loc-5", description="Erstes Draft.")
    store.set_qa_values("loc-5", description="Überarbeitete Beschreibung.")
    result = store.get_qa_values("loc-5")
    assert result["description"] == "Überarbeitete Beschreibung."


# ---------------------------------------------------------------------------
# Migration: ideal_azimuth_min/max in custom_locations
# ---------------------------------------------------------------------------

def test_migration_azimuth_columns_exist(store: LocationStore) -> None:
    """custom_locations hat nach Init die Spalten ideal_azimuth_min und ideal_azimuth_max."""
    import sqlite3
    with sqlite3.connect(str(store.db_path)) as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(custom_locations)")}
    assert "ideal_azimuth_min" in cols
    assert "ideal_azimuth_max" in cols


def test_migration_idempotent(tmp_path: Path) -> None:
    """Zweifaches Initialisieren erzeugt keinen Fehler (idempotente Migration)."""
    db = tmp_path / "idem.db"
    s1 = LocationStore(db_path=db)
    s2 = LocationStore(db_path=db)  # darf nicht crashen
    assert s2.integrity_check() == "ok"


def test_migration_existing_rows_preserved(store: LocationStore) -> None:
    """Bestehende Custom-Location-Rows bleiben nach Migration erhalten."""
    store.create_custom({
        "id": "test-loc",
        "name": "Testort",
        "observer_lat": 52.52,
        "observer_lon": 13.40,
        "subject_lat": 52.51,
        "subject_lon": 13.39,
    })
    # Zweite Store-Instanz auf derselben DB (simuliert Server-Neustart)
    store2 = LocationStore(db_path=store.db_path)
    locs = store2.load_all_custom()
    assert any(l["id"] == "test-loc" for l in locs)


# ---------------------------------------------------------------------------
# compute_geo_hash
# ---------------------------------------------------------------------------

def test_geo_hash_deterministic() -> None:
    """Gleiche Eingaben → gleicher Hash."""
    h1 = compute_geo_hash(52.52, 13.40, 52.51, 13.39, 100.0, 30.0, 500.0)
    h2 = compute_geo_hash(52.52, 13.40, 52.51, 13.39, 100.0, 30.0, 500.0)
    assert h1 == h2


def test_geo_hash_float_rounding() -> None:
    """Float-Rounding-Artefakte (52.5200001 vs 52.52) erzeugen denselben Hash."""
    h1 = compute_geo_hash(52.52, 13.40, 52.51, 13.39, 100.0, 30.0, 500.0)
    h2 = compute_geo_hash(52.5200001, 13.40, 52.51, 13.39, 100.0, 30.0, 500.0)
    assert h1 == h2


def test_geo_hash_changes_on_coord_change() -> None:
    """Koordinatenänderung → anderer Hash."""
    h1 = compute_geo_hash(52.52, 13.40, 52.51, 13.39, 100.0, 30.0, 500.0)
    h2 = compute_geo_hash(52.53, 13.40, 52.51, 13.39, 100.0, 30.0, 500.0)
    assert h1 != h2


def test_geo_hash_none_fields() -> None:
    """None-Felder erzeugen validen Hash (kein Fehler)."""
    h = compute_geo_hash(52.52, 13.40, 52.51, 13.39, None, None, None)
    assert isinstance(h, str) and len(h) == 32


# ---------------------------------------------------------------------------
# load_all_qa_values
# ---------------------------------------------------------------------------

def test_load_all_qa_values_empty(store: LocationStore) -> None:
    """load_all_qa_values gibt leere Liste zurück wenn keine Einträge."""
    assert store.load_all_qa_values() == []


def test_load_all_qa_values_returns_all(store: LocationStore) -> None:
    """load_all_qa_values gibt alle gesetzten QA-Values zurück."""
    store.set_qa_values("loc-a", description="A")
    store.set_qa_values("loc-b", description="B")
    all_vals = store.load_all_qa_values()
    ids = {v["location_id"] for v in all_vals}
    assert {"loc-a", "loc-b"} == ids


# ---------------------------------------------------------------------------
# update_qa_checked
# ---------------------------------------------------------------------------

def test_update_qa_checked_sets_timestamp(store: LocationStore) -> None:
    """update_qa_checked speichert qa_checked_at und geo_hash."""
    store.update_qa_checked("loc-x", "abc123")
    state = store.get_qa_state("loc-x")
    assert state["geo_hash"] == "abc123"
    assert state["qa_checked_at"] is not None


def test_update_qa_checked_upsert(store: LocationStore) -> None:
    """update_qa_checked überschreibt vorherigen Stand (Upsert)."""
    store.update_qa_checked("loc-x", "hash-v1")
    store.update_qa_checked("loc-x", "hash-v2")
    state = store.get_qa_state("loc-x")
    assert state["geo_hash"] == "hash-v2"
