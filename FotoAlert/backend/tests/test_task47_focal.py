"""
Tests für TASK-47: Brennweiten-Empfehlung automatisch aus Motivhöhe + Entfernung.

Abgedeckte Akzeptanzkriterien:
- Plausible, gerasterte Empfehlung; weiter entferntes Motiv → längere Brennweite
  (Monotonie in der Entfernung — die im Bestand verwendete Geometrie).        *(AK 1, 6)*
- Ergebnis liegt immer auf der bekannten Staffel _FOCAL_STEPS.                  *(AK 6)*
- Extrem-Eingaben (Mini-Entfernung / Riesen-Motiv) ergeben keinen absurden
  Wert jenseits des Rasters, sondern bleiben auf der Staffel.                   *(AK 6)*
- focal_length_lock wird respektiert → kein Schreiben.                         *(AK 2)*
- Bereits kuratierte Liste → kein Auto-Schreiben.                              *(AK 3)*
- Fehlende Höhe / fehlende Entfernung / Entfernung 0 → None, kein Schreiben,
  kein Crash.                                                                  *(AK 4)*
- Zwei identische Läufe → identisches Ergebnis (Determinismus).                *(AK 5)*

Hinweis zur Geometrie (bewusst aus dem Bestand wiederverwendet, Option A):
Die Formel `calculate_focal_length_for_subject` lässt die Brennweite mit der
ENTFERNUNG steigen (weiter weg → länger) und mit der MotivHÖHE fallen (größeres
Motiv füllt das Bild bei kürzerer Brennweite). Die Monotonie-Prüfung deckt
deshalb die Entfernungs-Richtung ab — den im Live-Fallback identischen Rechenweg.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.store import LocationStore
from data import qa_focal
from calculations.opportunity import _FOCAL_STEPS

pytestmark = [pytest.mark.offline, pytest.mark.regression]


@pytest.fixture
def store(tmp_path: Path) -> LocationStore:
    return LocationStore(db_path=tmp_path / "test.db")


# ---------------------------------------------------------------------------
# Plausible Empfehlung + Rasterung
# ---------------------------------------------------------------------------

def test_suggestion_is_on_focal_steps() -> None:
    """Jede Empfehlung liegt auf der bekannten Brennweiten-Staffel."""
    result = qa_focal.compute_focal_suggestion(20.0, 80.0)
    assert result is not None
    assert len(result) == 1  # eine Brennweite, keine Spanne (Annahme A2)
    assert result[0] in _FOCAL_STEPS


def test_farther_subject_gets_longer_focal() -> None:
    """Weiter entferntes Motiv → längere (oder gleich lange) Brennweite."""
    near = qa_focal.compute_focal_suggestion(20.0, 30.0)
    far = qa_focal.compute_focal_suggestion(20.0, 80.0)
    farther = qa_focal.compute_focal_suggestion(20.0, 300.0)
    assert near is not None and far is not None and farther is not None
    # Monotonie in der Entfernung (Geometrie des Bestands).
    assert near[0] <= far[0] <= farther[0]
    # Mindestens ein echter Anstieg über die Spanne (kein konstanter Wert).
    assert farther[0] > near[0]


# ---------------------------------------------------------------------------
# Extrem-Eingaben bleiben auf dem Raster
# ---------------------------------------------------------------------------

def test_extreme_inputs_stay_on_steps() -> None:
    """Mini-Entfernung / Riesen-Motiv → kein absurder Wert, sondern Staffel."""
    # Riesiges Motiv extrem nah → Rohwert entgleist; muss trotzdem auf der
    # Staffel landen (kein negativer / absurd langer Wert).
    huge_near = qa_focal.compute_focal_suggestion(100.0, 0.5)
    assert huge_near is not None
    assert huge_near[0] in _FOCAL_STEPS
    # Sehr weit entfernt → höchstens der größte Staffel-Wert.
    very_far = qa_focal.compute_focal_suggestion(5.0, 5000.0)
    assert very_far is not None
    assert very_far[0] in _FOCAL_STEPS
    assert very_far[0] <= max(_FOCAL_STEPS)


# ---------------------------------------------------------------------------
# Fehlende / ungültige Daten → None, kein Crash
# ---------------------------------------------------------------------------

def test_missing_height_returns_none() -> None:
    assert qa_focal.compute_focal_suggestion(None, 100.0) is None


def test_missing_distance_returns_none() -> None:
    assert qa_focal.compute_focal_suggestion(10.0, None) is None


def test_zero_distance_returns_none_no_crash() -> None:
    """Entfernung 0 → None statt Division durch null."""
    assert qa_focal.compute_focal_suggestion(10.0, 0.0) is None


def test_zero_height_returns_none() -> None:
    assert qa_focal.compute_focal_suggestion(0.0, 100.0) is None


def test_negative_values_return_none() -> None:
    assert qa_focal.compute_focal_suggestion(-5.0, 100.0) is None
    assert qa_focal.compute_focal_suggestion(10.0, -100.0) is None


# ---------------------------------------------------------------------------
# Determinismus
# ---------------------------------------------------------------------------

def test_deterministic_two_runs() -> None:
    """Zwei Läufe auf identischem Input → identisches Ergebnis."""
    r1 = qa_focal.compute_focal_suggestion(15.0, 250.0)
    r2 = qa_focal.compute_focal_suggestion(15.0, 250.0)
    assert r1 == r2


def test_deterministic_via_store(store: LocationStore) -> None:
    """Zwei Läufe auf demselben Spot → identischer gespeicherter Wert.

    Der erste Lauf schreibt; der zweite findet bereits eine Liste vor und lässt
    sie unangetastet (AK 3). Maßgeblich ist: der gespeicherte Wert ändert sich
    nicht (kein Zufall, keine Schwankung — AK 5).
    """
    r1 = qa_focal.update_location_focal(store, "spot-1", 15.0, 250.0)
    assert r1 is not None
    stored_after_first = store.get_qa_values("spot-1")["focal_length_suggestions"]
    qa_focal.update_location_focal(store, "spot-1", 15.0, 250.0)
    stored_after_second = store.get_qa_values("spot-1")["focal_length_suggestions"]
    assert stored_after_first == stored_after_second == r1


# ---------------------------------------------------------------------------
# Schreiben / Lock / kuratierte Liste
# ---------------------------------------------------------------------------

def test_unlocked_empty_is_written(store: LocationStore) -> None:
    """Ohne Lock und ohne kuratierte Liste wird der Auto-Wert geschrieben."""
    result = qa_focal.update_location_focal(store, "spot-open", 20.0, 80.0)
    assert result is not None
    vals = store.get_qa_values("spot-open")
    assert vals is not None
    assert vals["focal_length_suggestions"] == result


def test_lock_is_respected(store: LocationStore) -> None:
    """Gesperrte Brennweite wird vom Auto-Lauf nicht überschrieben."""
    store.set_qa_values("spot-locked", focal_length_suggestions=[85])
    store.set_qa_lock("spot-locked", "focal_length", True)

    result = qa_focal.update_location_focal(store, "spot-locked", 20.0, 80.0)
    assert result is None  # nichts geschrieben
    vals = store.get_qa_values("spot-locked")
    assert vals["focal_length_suggestions"] == [85]


def test_existing_curated_list_not_overwritten(store: LocationStore) -> None:
    """Vorhandene kuratierte Liste bleibt; Auto-Wert drängt sich nicht dazwischen."""
    store.set_qa_values("spot-curated", focal_length_suggestions=[50, 85, 135])
    result = qa_focal.update_location_focal(store, "spot-curated", 20.0, 80.0)
    assert result is None
    vals = store.get_qa_values("spot-curated")
    assert vals["focal_length_suggestions"] == [50, 85, 135]


def test_missing_data_writes_nothing(store: LocationStore) -> None:
    """update_location_focal ohne Höhe/Entfernung → nichts in der DB."""
    assert qa_focal.update_location_focal(store, "spot-noh", None, 80.0) is None
    assert qa_focal.update_location_focal(store, "spot-nod", 20.0, None) is None
    assert qa_focal.update_location_focal(store, "spot-zero", 20.0, 0.0) is None
    assert store.get_qa_values("spot-noh") is None
    assert store.get_qa_values("spot-nod") is None
    assert store.get_qa_values("spot-zero") is None
