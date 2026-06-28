"""Tests für TASK-48: QA-Lauf automatisieren (Änderungen erkennen + planen).

Deckt die sandbox-fähigen Teile ab (kein Scheduler-Live, kein echter Recompute):
- Change-Detection über persistierten Geo-Hash:
    geänderter Hash → Spot fällt an; gleicher Hash → übersprungen;
    nie geprüft (State None) → fällt an.   (AK-1/AK-2/AK-3)
- Fehlversuch schreibt qa_checked_at/geo_hash NICHT fort → erneuter Versuch. (AK-5)
- Erfolg (auch bei gesperrten Werten) schreibt Hash fort, Spot gilt als geprüft. (AK-8)
- Single-Flight: läuft bereits ein QA-Lauf / ein Recompute → kein zweiter Start. (AK-6)
- Fehlerisolierung: ein crashender Spot bricht den Lauf nicht ab. (AK-5)
- precompute._apply_qa_values(): qa_value landet auf der Location,
  Merge-Reihenfolge Code-Defaults < qa_values < Overrides. (AK-4)

Die echten externen Aufrufe (Azimut/Brennweite) werden gemockt — getestet wird die
Steuerlogik, nicht die schon abgedeckten Bausteine (TASK-45/47).
"""
import asyncio
import os
from pathlib import Path
import sys

import pytest

# Startup ohne Scheduler/Netzwerk halten (import main ist sonst harmlos, aber
# wir wollen keine Hintergrundtasks beim Test).
os.environ.setdefault("FOTOALERT_NO_BACKGROUND", "1")

sys.path.insert(0, str(Path(__file__).parent.parent))

import main
from data.store import LocationStore, compute_geo_hash
import precompute


# ---------------------------------------------------------------------------
# Test-Doubles
# ---------------------------------------------------------------------------

class FakeLoc:
    """Minimale Location mit den 7 Geo-Kernfeldern + id."""

    def __init__(self, loc_id, observer_lat=52.5, observer_lon=13.4,
                 subject_lat=52.6, subject_lon=13.5,
                 subject_height_m=100.0, subject_width_m=20.0, distance_m=1000.0):
        self.id = loc_id
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.subject_lat = subject_lat
        self.subject_lon = subject_lon
        self.subject_height_m = subject_height_m
        self.subject_width_m = subject_width_m
        self.distance_m = distance_m


@pytest.fixture
def store(tmp_path):
    return LocationStore(db_path=tmp_path / "test.db")


# ---------------------------------------------------------------------------
# Change-Detection (_qa_select_due)
# ---------------------------------------------------------------------------

def test_never_checked_is_due(store):
    """AK-2: noch nie geprüfter Spot (State None) → fällt an."""
    loc = FakeLoc("a")
    due = main._qa_select_due([loc], store)
    assert [l.id for l, _ in due] == ["a"]


def test_unchanged_checked_is_skipped(store):
    """AK-3: gleicher Hash wie gespeichert → übersprungen."""
    loc = FakeLoc("a")
    store.update_qa_checked("a", main._qa_geo_hash_for(loc))
    due = main._qa_select_due([loc], store)
    assert due == []


def test_changed_geo_is_due(store):
    """AK-1: Geo-Feld geändert → Hash weicht ab → fällt erneut an."""
    loc = FakeLoc("a")
    store.update_qa_checked("a", main._qa_geo_hash_for(loc))
    # Standort umsetzen → neuer Hash
    loc.observer_lat = 52.9
    due = main._qa_select_due([loc], store)
    assert [l.id for l, _ in due] == ["a"]


def test_geo_hash_matches_store_helper(store):
    """_qa_geo_hash_for nutzt dieselbe Feldauswahl wie compute_geo_hash."""
    loc = FakeLoc("a")
    expected = compute_geo_hash(
        loc.observer_lat, loc.observer_lon, loc.subject_lat, loc.subject_lon,
        loc.subject_height_m, loc.subject_width_m, loc.distance_m,
    )
    assert main._qa_geo_hash_for(loc) == expected


# ---------------------------------------------------------------------------
# Fortschreiben nur bei Erfolg (_run_qa_pass)
# ---------------------------------------------------------------------------

def _run(coro):
    """Eigener Event-Loop pro Aufruf — robust gegen geschlossene Loops aus
    vorherigen async-Tests in der Gesamt-Suite."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _patch_pass(monkeypatch, store, locations, improve_fn):
    """Hängt den QA-Lauf an Test-Locations + Test-Store + gemockte Verbesserung,
    schaltet die Drosselung auf 0 und neutralisiert die Single-Flight-Flags."""
    monkeypatch.setattr(main, "LOCATIONS", locations, raising=False)
    monkeypatch.setattr(main, "_store", store, raising=False)
    monkeypatch.setattr(main, "_qa_improve_one", improve_fn, raising=False)
    monkeypatch.setattr(main, "_QA_PASS_THROTTLE_S", 0.0, raising=False)
    main._qa_pass_running = False
    main._precompute_running = False


def test_success_advances_hash(monkeypatch, store):
    """Erfolg → qa_checked_at + geo_hash fortgeschrieben → übernächster Lauf skippt (AK-3)."""
    loc = FakeLoc("a")
    _patch_pass(monkeypatch, store, [loc], lambda l, s: True)
    _run(main._run_qa_pass())
    state = store.get_qa_state("a")
    assert state is not None
    assert state["geo_hash"] == main._qa_geo_hash_for(loc)
    assert state["qa_checked_at"] is not None
    # Übernächster Lauf: nichts mehr fällig
    assert main._qa_select_due([loc], store) == []


def test_failure_does_not_advance_hash(monkeypatch, store):
    """AK-5: harter Fehler → Hash/Zeitstempel NICHT fortgeschrieben → Spot fällt erneut an."""
    loc = FakeLoc("a")
    _patch_pass(monkeypatch, store, [loc], lambda l, s: False)
    _run(main._run_qa_pass())
    state = store.get_qa_state("a")
    assert state is None or state.get("geo_hash") is None
    # Spot ist weiterhin fällig
    assert [l.id for l, _ in main._qa_select_due([loc], store)] == ["a"]


def test_crash_isolated_per_spot(monkeypatch, store):
    """AK-5: ein crashender Spot bricht den Lauf nicht ab; andere werden verarbeitet."""
    locs = [FakeLoc("crash"), FakeLoc("ok")]

    def improve(loc, s):
        if loc.id == "crash":
            raise RuntimeError("Dienst weg")
        return True

    _patch_pass(monkeypatch, store, locs, improve)
    _run(main._run_qa_pass())
    # crash-Spot bleibt ungeprüft, ok-Spot wurde fortgeschrieben
    assert store.get_qa_state("crash") is None or store.get_qa_state("crash").get("geo_hash") is None
    assert store.get_qa_state("ok")["geo_hash"] == main._qa_geo_hash_for(locs[1])


# ---------------------------------------------------------------------------
# Single-Flight (AK-6)
# ---------------------------------------------------------------------------

def test_no_second_pass_while_running(monkeypatch, store):
    """AK-6: läuft bereits ein QA-Lauf → zweiter Start macht nichts."""
    loc = FakeLoc("a")
    calls = {"n": 0}

    def improve(l, s):
        calls["n"] += 1
        return True

    _patch_pass(monkeypatch, store, [loc], improve)
    main._qa_pass_running = True  # simuliert laufenden Lauf
    _run(main._run_qa_pass())
    assert calls["n"] == 0  # kein Durchlauf
    main._qa_pass_running = False


def test_no_pass_during_recompute(monkeypatch, store):
    """AK-6: läuft ein großer Recompute → QA-Lauf startet nicht (kein Überlappen)."""
    loc = FakeLoc("a")
    calls = {"n": 0}
    _patch_pass(monkeypatch, store, [loc], lambda l, s: calls.__setitem__("n", calls["n"] + 1) or True)
    main._precompute_running = True
    _run(main._run_qa_pass())
    assert calls["n"] == 0
    main._precompute_running = False


# ---------------------------------------------------------------------------
# Lock-Robustheit (AK-8) — _qa_improve_one mit gesetzten Locks
# ---------------------------------------------------------------------------

def test_locked_values_still_counted_as_checked(monkeypatch, store):
    """AK-8: beide Werte gesperrt → nichts geschrieben, Spot gilt trotzdem als geprüft.

    Wir nutzen die echte _qa_improve_one mit gesetzten Locks; die update_*-Funktionen
    geben dann None zurück (kein Schreiben), werfen aber nicht → ok=True → Hash fort.
    """
    loc = FakeLoc("a")
    store.set_qa_lock("a", "azimuth", True)
    store.set_qa_lock("a", "focal_length", True)
    monkeypatch.setattr(main, "LOCATIONS", [loc], raising=False)
    monkeypatch.setattr(main, "_store", store, raising=False)
    monkeypatch.setattr(main, "_QA_PASS_THROTTLE_S", 0.0, raising=False)
    main._qa_pass_running = False
    main._precompute_running = False
    _run(main._run_qa_pass())
    state = store.get_qa_state("a")
    assert state["geo_hash"] == main._qa_geo_hash_for(loc)  # geprüft
    # Keine QA-Werte geschrieben (Locks respektiert)
    assert store.get_qa_values("a") is None


# ---------------------------------------------------------------------------
# precompute._apply_qa_values — Sichtbarkeit + Merge-Reihenfolge (AK-4)
# ---------------------------------------------------------------------------

class _PrecomputeLoc:
    def __init__(self, loc_id):
        self.id = loc_id
        self.description = "code-default"
        self.ideal_azimuth_range = None
        self.focal_length_suggestions = []


def test_apply_qa_values_patches_location(monkeypatch, store):
    """AK-4: gesetzter qa_value erscheint auf der Location (fließt damit in Recompute/Feed)."""
    loc = _PrecomputeLoc("a")
    store.set_qa_values("a", description="auto-desc",
                        ideal_azimuth_min=80.0, ideal_azimuth_max=110.0,
                        focal_length_suggestions=[135])
    monkeypatch.setattr(precompute, "LOCATIONS", [loc], raising=False)
    monkeypatch.setattr(precompute, "LocationStore", lambda *a, **k: store, raising=False)
    n = precompute._apply_qa_values()
    assert n == 1
    assert loc.description == "auto-desc"
    assert loc.ideal_azimuth_range == (80.0, 110.0)
    assert loc.focal_length_suggestions == [135]


def test_apply_qa_values_merge_order(monkeypatch, store):
    """AK-4: Merge-Reihenfolge Code-Defaults < qa_values < Overrides.

    qa_values überschreiben Code-Defaults; ein danach angewendeter Override muss
    den qa_value wieder überschreiben (Reihenfolge in main(): qa VOR overrides).
    """
    loc = _PrecomputeLoc("a")
    store.set_qa_values("a", description="auto-desc")
    monkeypatch.setattr(precompute, "LOCATIONS", [loc], raising=False)
    monkeypatch.setattr(precompute, "LocationStore", lambda *a, **k: store, raising=False)
    # 1. qa_values über Code-Default
    precompute._apply_qa_values()
    assert loc.description == "auto-desc"
    # 2. Override simulieren (läuft in main() NACH _apply_qa_values) → gewinnt
    precompute._set_loc_attr(loc, "description", "manual-override")
    assert loc.description == "manual-override"


def test_apply_qa_values_empty_is_noop(monkeypatch, store):
    """Keine qa_values vorhanden → 0 gepatcht, kein Crash."""
    loc = _PrecomputeLoc("a")
    monkeypatch.setattr(precompute, "LOCATIONS", [loc], raising=False)
    monkeypatch.setattr(precompute, "LocationStore", lambda *a, **k: store, raising=False)
    assert precompute._apply_qa_values() == 0
    assert loc.description == "code-default"
