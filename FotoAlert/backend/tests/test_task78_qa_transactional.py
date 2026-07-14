"""Tests für TASK-78: QA-Teilerfolg konsistent behandeln (Option B).

Deckt ab, dass `_qa_improve_one()`/`_run_qa_pass()` den Prüf-Eintrag
(`update_qa_checked()`) für einen Ort immer setzen, sobald der Lauf für ihn
abgeschlossen ist UND mindestens ein Teilwert tatsächlich geschrieben wurde —
unabhängig davon, ob ein anderer Teilschritt an einem echten Datenbank-Fehler
gescheitert ist (AK 1/5). Scheitert dagegen bei einem Ort kein einziger Wert
UND mindestens ein Teilschritt an einem echten Fehler, bleibt der Ort
unverändert und fällt erneut an (AK 2). Kein Fehler irgendwo → Verhalten
identisch zum bisherigen Stand (AK 3). Gesperrte Werte bleiben unverändert
übersprungen (AK 4).

Simuliert den Datenbank-Fehler exakt im realen Aufrufpfad der jeweiligen
Teilschritt-Funktion (Monkeypatch auf `store.set_qa_values`, gefiltert nach
dem übergebenen Feldnamen) — nicht isoliert auf Store-Ebene (Pre-Mortem
Szenario 3 im Ticket). Die Beschreibungs-Funktion fängt Exceptions bereits
intern vollständig ab (kein MISTRAL_API_KEY in der Sandbox → schreibt ohnehin
nie etwas) und kann daher nie selbst als "gescheitert" gezählt werden — das
deckt sich mit dem Pre-Mortem des Tickets, das nur Azimut/Brennweite als
mockbare Fehlerpfade nennt.
"""
import asyncio
import os
from pathlib import Path
import sqlite3
import sys

import pytest

os.environ.setdefault("FOTOALERT_NO_BACKGROUND", "1")
os.environ.pop("MISTRAL_API_KEY", None)  # Beschreibungs-Schritt schreibt nie (wie auf Prod)

sys.path.insert(0, str(Path(__file__).parent.parent))

import main
from data.store import LocationStore

pytestmark = [pytest.mark.offline, pytest.mark.regression]


class FakeLoc:
    """Minimale Location mit den Geo-Kernfeldern + id (wie test_task48_qa_cron.py)."""

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
        self.name = "Testspot"
        self.subject_name = "Testmotiv"
        self.category = "sunset"


@pytest.fixture
def store(tmp_path):
    return LocationStore(db_path=tmp_path / "test.db")


def _run(coro):
    """Eigener Event-Loop pro Aufruf — robust gegen geschlossene Loops aus
    vorherigen async-Tests in der Gesamt-Suite (wie test_task48_qa_cron.py)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _patch_pass(monkeypatch, store, locations):
    """Hängt den echten QA-Lauf an Test-Locations + Test-Store, schaltet die
    Drosselung auf 0 und neutralisiert die Single-Flight-Flags. Im Unterschied
    zu test_task48_qa_cron.py wird `_qa_improve_one` NICHT gemockt — wir wollen
    die echte Teilerfolgs-Logik testen."""
    monkeypatch.setattr(main, "LOCATIONS", locations, raising=False)
    monkeypatch.setattr(main, "_store", store, raising=False)
    monkeypatch.setattr(main, "_QA_PASS_THROTTLE_S", 0.0, raising=False)
    main._qa_pass_running = False
    main._precompute_running = False


def _wrap_failing_set_qa_values(store, fail_predicate):
    """Ersetzt store.set_qa_values so, dass es abhängig vom übergebenen
    Feldsatz eine echte SQLite-Exception wirft — simuliert einen
    Datenbank-Fehler exakt im Aufrufpfad des jeweiligen QA-Teilschritts."""
    original = store.set_qa_values

    def wrapper(location_id, **fields):
        if fail_predicate(fields):
            raise sqlite3.OperationalError("database is locked (simulated, TASK-78 test)")
        return original(location_id, **fields)

    return wrapper


# ---------------------------------------------------------------------------
# Test 1 (AK-1): Teilerfolg — ein Wert geschrieben, ein Schritt scheitert an DB-Fehler
# ---------------------------------------------------------------------------

def test_partial_failure_still_advances_checked_entry(monkeypatch, store):
    """AK-1: Azimut schreibt erfolgreich, Brennweite scheitert an simuliertem
    DB-Fehler → nach dem Lauf existiert sowohl der geschriebene Azimut-Wert
    als auch ein neuer Prüf-Eintrag — kein Wert ohne Prüf-Eintrag mehr."""
    loc = FakeLoc("a")
    monkeypatch.setattr(
        store, "set_qa_values",
        _wrap_failing_set_qa_values(store, lambda f: "focal_length_suggestions" in f),
        raising=False,
    )
    _patch_pass(monkeypatch, store, [loc])
    _run(main._run_qa_pass())

    state = store.get_qa_state("a")
    assert state is not None
    assert state["geo_hash"] == main._qa_geo_hash_for(loc)

    values = store.get_qa_values("a")
    assert values is not None
    assert values.get("ideal_azimuth_min") is not None
    assert values.get("focal_length_suggestions") is None  # Brennweite ist gescheitert


# ---------------------------------------------------------------------------
# Test 2 (AK-2): Kompletter Fehlschlag — kein einziger Wert geschrieben
# ---------------------------------------------------------------------------

def test_total_failure_leaves_spot_due(monkeypatch, store):
    """AK-2: Azimut UND Brennweite scheitern an simulierten DB-Fehlern, die
    Beschreibung schreibt (wie auf Prod) ohnehin nie (kein MISTRAL_API_KEY) →
    kein einziger Wert geschrieben. Der Ort bleibt unverändert und gilt
    weiterhin als fällig (kein neuer Prüf-Eintrag)."""
    loc = FakeLoc("a")
    monkeypatch.setattr(
        store, "set_qa_values",
        _wrap_failing_set_qa_values(
            store, lambda f: "ideal_azimuth_min" in f or "focal_length_suggestions" in f
        ),
        raising=False,
    )
    _patch_pass(monkeypatch, store, [loc])
    _run(main._run_qa_pass())

    state = store.get_qa_state("a")
    assert state is None or state.get("geo_hash") is None
    assert store.get_qa_values("a") is None
    # Ort bleibt fällig
    assert [l.id for l, _ in main._qa_select_due([loc], store)] == ["a"]


# ---------------------------------------------------------------------------
# Test 3 (AK-3): Fehlerfreier Lauf — Regression gegen bisheriges Verhalten
# ---------------------------------------------------------------------------

def test_no_failure_behaves_like_before(monkeypatch, store):
    """AK-3: Kein Teilschritt scheitert → Ergebnis identisch zum bisherigen
    Verhalten (Prüf-Eintrag gesetzt, Azimut-Wert geschrieben, übernächster
    Lauf überspringt den Ort). Keine Verhaltensänderung im Normalfall."""
    loc = FakeLoc("a")
    _patch_pass(monkeypatch, store, [loc])
    result = _run(main._run_qa_pass())

    state = store.get_qa_state("a")
    assert state is not None
    assert state["geo_hash"] == main._qa_geo_hash_for(loc)
    values = store.get_qa_values("a")
    assert values is not None
    assert values.get("ideal_azimuth_min") is not None

    assert result["checked"] == 1
    assert result["improved"] == 1
    assert result["failed"] == 0

    # Übernächster Lauf: nichts mehr fällig
    assert main._qa_select_due([loc], store) == []


# ---------------------------------------------------------------------------
# Test 4 (AK-4): Gesperrte Werte weiterhin unverändert übersprungen
# ---------------------------------------------------------------------------

def test_locked_values_still_skipped_and_checked(monkeypatch, store):
    """AK-4: Ein Ort mit gesetztem Lock wird weiterhin unverändert
    übersprungen — die Absicherung ändert nichts am bestehenden
    Sperr-Verhalten. Selbst wenn parallel ein anderer Teilschritt an einem
    DB-Fehler scheitert, bleibt der gesperrte Wert unangetastet."""
    loc = FakeLoc("a")
    store.set_qa_lock("a", "azimuth", True)
    store.set_qa_lock("a", "focal_length", True)
    _patch_pass(monkeypatch, store, [loc])
    _run(main._run_qa_pass())

    state = store.get_qa_state("a")
    assert state["geo_hash"] == main._qa_geo_hash_for(loc)  # weiterhin geprüft
    # Keine QA-Werte geschrieben (Locks respektiert, wie bisher)
    assert store.get_qa_values("a") is None


# ---------------------------------------------------------------------------
# Test 5 (AK-5, Edge Case): Allererster Check eines Ortes, Teilfehler
# ---------------------------------------------------------------------------

def test_first_ever_check_with_partial_failure(monkeypatch, store):
    """Edge Case: Ort ohne jeden vorherigen Prüf-Eintrag (erster Lauf), ein
    Teilschritt scheitert an einem DB-Fehler → kein Wert ohne Prüf-Eintrag,
    genau wie bei einem bereits zuvor geprüften Ort (AK-1 gilt identisch)."""
    loc = FakeLoc("a")
    assert store.get_qa_state("a") is None  # noch nie geprüft
    monkeypatch.setattr(
        store, "set_qa_values",
        _wrap_failing_set_qa_values(store, lambda f: "focal_length_suggestions" in f),
        raising=False,
    )
    _patch_pass(monkeypatch, store, [loc])
    _run(main._run_qa_pass())

    state = store.get_qa_state("a")
    assert state is not None
    assert state["geo_hash"] == main._qa_geo_hash_for(loc)
    values = store.get_qa_values("a")
    assert values is not None
    assert values.get("ideal_azimuth_min") is not None
