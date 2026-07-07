"""
Tests für US-09: Sichtachsen-Check – Hinderniserkennung (Raycast).

Abgedeckte Testplan-Fälle (siehe BACKLOG.md US-09, Abschnitt "Testplan"):
  1. Bekanntes Gebäude in der Sichtlinie -> Status "blockiert".
  2. Freie Sichtlinie -> Status "frei".
  3. Simulierter API-Fehler (Mock-Timeout) -> Status "nicht_geprueft", nie "frei".
  4. Distanz > 5 km mit Erdkrümmungskorrektur -> Ergebnis bleibt konsistent
     mit der Korrekturformel (kein falsches "blockiert" durch einen zu
     geraden, unkorrigierten Sichtstrahl).
  5. Teilweise Verdeckung -> Status "teilweise_verdeckt" mit korrektem
     Grenzwinkel (kleiner als der Zielwinkel zum Motiv).
  6. Fehlende Höhen-/Gebäudedaten -> "nicht_geprueft", niemals stillschweigend
     als "frei" gewertet (Regel 4).
  7. Fehlendes Motiv (keine Koordinaten) -> "nicht_geprueft".
  8. compute_location_sightline(): Höhenprofil-Abfrage wirft Exception (Mock)
     -> "nicht_geprueft" statt Crash/falsches "frei" (End-to-End der Async-Hülle).
  9. update_location_sightline(): Ergebnis wird korrekt in location_qa_values
     persistiert (sightline_status/sightline_angle_deg/sightline_checked_at).
  10. DEFAULT_EYE_HEIGHT_M ist auf 1.8 (von Stephan am 2026-07-06 bestätigt).

Python-3.9-kompatibel (kein `X | None`).
"""
from __future__ import annotations

import asyncio
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from calculations import sightline as sl
from data.store import LocationStore


@pytest.fixture
def store(tmp_path: Path) -> LocationStore:
    return LocationStore(db_path=tmp_path / "test.db")


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

def test_default_eye_height_ist_1_8m():
    """Von Stephan am 2026-07-06 bestätigt/korrigiert (vorher 1.6m im Code)."""
    assert sl.DEFAULT_EYE_HEIGHT_M == 1.8


def test_curvature_threshold_bleibt_5000m():
    """Erdkrümmungs-Schwelle bleibt wie im Code (von Stephan bestätigt)."""
    assert sl.CURVATURE_THRESHOLD_M == 5000.0


# ---------------------------------------------------------------------------
# evaluate_sightline() — reine Berechnung, keine Netzwerk-Calls
# ---------------------------------------------------------------------------

def test_freie_sichtlinie_ohne_hindernisse():
    """Testplan #2: flaches Terrain, keine Gebäude -> Status 'frei'."""
    terrain = [0.0, 0.0, 0.0, 0.0, 0.0]  # komplett eben
    result = sl.evaluate_sightline(
        observer_lat=52.50, observer_lon=13.40, observer_floor_height_m=0.0,
        subject_lat=52.51, subject_lon=13.41, subject_height_m=30.0,
        terrain_heights_m=terrain, terrain_incomplete=False,
        buildings=[], distance_m=1000.0,
    )
    assert result["status"] == "frei"


def test_gebaeude_blockiert_sichtlinie():
    """Testplan #1: 40m hohes Gebäude 200m vor dem Standort, höher als die
    Sichtlinie zum (deutlich niedrigeren) Motiv -> Status 'blockiert'."""
    terrain = [0.0, 0.0, 0.0]  # eben
    buildings = [{
        "nodes": [(52.5009, 13.4009), (52.5009, 13.4011)],  # ~200m nordöstlich vom Standort
        "height_m": 40.0,
    }]
    result = sl.evaluate_sightline(
        observer_lat=52.500, observer_lon=13.400, observer_floor_height_m=0.0,
        subject_lat=52.502, subject_lon=13.402, subject_height_m=5.0,
        terrain_heights_m=terrain, terrain_incomplete=False,
        buildings=buildings, distance_m=300.0,
    )
    assert result["status"] == "blockiert"
    assert result["obstruction_angle_deg"] is not None


def test_teilweise_verdeckung():
    """Testplan #5: Hindernis liegt über 0° (sichtbar über Horizont, ~2°), aber
    klar unterhalb des Zielwinkels zum (hohen, fernen) Motiv (~4,5°) ->
    'teilweise_verdeckt', mit Grenzwinkel kleiner als der Zielwinkel.
    Gebäude ~100m nördlich des Standorts, 5.3m hoch (Werte per Vorab-Rechnung
    gegen evaluate_sightline's eigene Winkelformel bestimmt, siehe Kommentar
    unten — nicht geraten, sondern aus der Formel rückgerechnet)."""
    terrain = [0.0, 0.0, 0.0]
    buildings = [{
        "nodes": [(52.50089831117499, 13.4), (52.50089831117499, 13.40001)],
        "height_m": 5.3,
    }]
    result = sl.evaluate_sightline(
        observer_lat=52.500, observer_lon=13.400, observer_floor_height_m=0.0,
        # Hohes, weit entferntes Motiv -> großer Zielwinkel (~4,5°), das
        # niedrigere Gebäude in der Nähe deckt nur den unteren Teil ab (~2°).
        subject_lat=52.520, subject_lon=13.420, subject_height_m=200.0,
        terrain_heights_m=terrain, terrain_incomplete=False,
        buildings=buildings, distance_m=2500.0,
    )
    assert result["status"] == "teilweise_verdeckt"
    assert result["obstruction_angle_deg"] is not None
    assert result["visible_from_deg"] is not None
    assert 0.0 < result["obstruction_angle_deg"] < 4.5


def test_fehlendes_motiv_liefert_nicht_geprueft():
    """Testplan #7 / Regel 4: keine Motiv-Koordinaten -> 'nicht_geprueft'."""
    result = sl.evaluate_sightline(
        observer_lat=52.50, observer_lon=13.40, observer_floor_height_m=0.0,
        subject_lat=None, subject_lon=None, subject_height_m=None,
        terrain_heights_m=None, terrain_incomplete=False,
        buildings=None, distance_m=None,
    )
    assert result["status"] == "nicht_geprueft"


def test_fehlende_hoehendaten_liefert_nicht_geprueft_nie_frei():
    """Testplan #6 / Regel 4: terrain_incomplete=True (API-Lücke) -> niemals
    stillschweigend 'frei', sondern ehrlich 'nicht_geprueft'."""
    result = sl.evaluate_sightline(
        observer_lat=52.50, observer_lon=13.40, observer_floor_height_m=0.0,
        subject_lat=52.51, subject_lon=13.41, subject_height_m=30.0,
        terrain_heights_m=[0.0, None, 0.0], terrain_incomplete=True,
        buildings=[], distance_m=1000.0,
    )
    assert result["status"] == "nicht_geprueft"
    assert result["status"] != "frei"


def test_fehlende_gebaeudedaten_liefert_nicht_geprueft():
    """Regel 4: buildings=None (Overpass-Fehler) -> 'nicht_geprueft', nicht 'frei'."""
    result = sl.evaluate_sightline(
        observer_lat=52.50, observer_lon=13.40, observer_floor_height_m=0.0,
        subject_lat=52.51, subject_lon=13.41, subject_height_m=30.0,
        terrain_heights_m=[0.0, 0.0, 0.0], terrain_incomplete=False,
        buildings=None, distance_m=1000.0,
    )
    assert result["status"] == "nicht_geprueft"


def test_erdkruemmung_bei_ueber_5km_kein_falsches_blockiert():
    """Testplan #4: Fernmotiv >5km (Bergsilhouette), flaches Zwischenterrain.
    Ohne Erdkrümmungskorrektur würde der Horizont-Verlauf zu gerade gerechnet;
    mit Korrektur sinkt der scheinbare Horizont mit der Distanz ab, sodass ein
    hohes, weit entferntes Motiv nicht fälschlich als 'blockiert' bewertet wird."""
    distance_m = 20000.0  # 20 km, deutlich über der 5km-Schwelle
    terrain = [0.0] * 10  # komplett eben, keine echte Geländeerhebung
    result = sl.evaluate_sightline(
        observer_lat=52.50, observer_lon=13.40, observer_floor_height_m=0.0,
        subject_lat=52.68, subject_lon=13.58, subject_height_m=1000.0,  # Berg
        terrain_heights_m=terrain, terrain_incomplete=False,
        buildings=[], distance_m=distance_m,
    )
    # Kein Hindernis vorhanden (Terrain komplett flach) -> 'frei', unabhängig
    # von der Erdkrümmung (die nur den Zielwinkel zum Motiv beeinflusst, nicht
    # ob ein Hindernis existiert). Wichtiger Beleg: kein Crash, kein 'blockiert'
    # durch eine rein numerische Artefakt-Berechnung.
    assert result["status"] == "frei"

    # Direkter Formel-Test der Krümmungskorrektur: der Effekt muss für 20km
    # deutlich größer sein als für 1km (monoton wachsend, quadratisch in der
    # Distanz) und darf nicht Null sein.
    drop_near = sl._curvature_drop_m(1000.0)
    drop_far = sl._curvature_drop_m(distance_m)
    assert drop_far > drop_near > 0.0
    # Grobe Plausibilität gegen die Standardformel (ohne Refraktion ca. 1.57m/km^2).
    expected_far = ((1.0 - sl.REFRACTION_COEFFICIENT) / (2.0 * sl.EARTH_RADIUS_M)) * distance_m ** 2
    assert math.isclose(drop_far, expected_far, rel_tol=1e-9)


def test_kurzes_profil_liefert_nicht_geprueft():
    """Edge Case: Höhenprofil mit weniger als 2 Punkten -> 'nicht_geprueft'
    statt Crash oder falschem 'frei'."""
    result = sl.evaluate_sightline(
        observer_lat=52.50, observer_lon=13.40, observer_floor_height_m=0.0,
        subject_lat=52.51, subject_lon=13.41, subject_height_m=30.0,
        terrain_heights_m=[0.0], terrain_incomplete=False,
        buildings=[], distance_m=1000.0,
    )
    assert result["status"] == "nicht_geprueft"


# ---------------------------------------------------------------------------
# compute_location_sightline() — Async-Hülle inkl. Fehlerbehandlung (Mocks)
# ---------------------------------------------------------------------------

class _FakeLoc:
    """Minimales Duck-Typing-Objekt analog PhotoLocation/Custom-Location."""
    def __init__(self, **kw):
        self.id = kw.get("id", "test-loc")
        self.observer_lat = kw.get("observer_lat")
        self.observer_lon = kw.get("observer_lon")
        self.subject_lat = kw.get("subject_lat")
        self.subject_lon = kw.get("subject_lon")
        self.subject_height_m = kw.get("subject_height_m")
        self.observer_floor_height_m = kw.get("observer_floor_height_m", 0.0)
        self.distance_m = kw.get("distance_m")


class _FailingElevationProvider:
    """Simuliert Testplan #3: Höhenprofil-Abfrage (OpenTopoData) schlägt fehl
    (z.B. Timeout) -> Ergebnis muss 'nicht_geprueft' sein, nicht 'frei'."""
    async def elevation_profile(self, *args, **kwargs):
        raise TimeoutError("simulierter OpenTopoData-Timeout")


class _OkElevationProvider:
    """Liefert ein flaches, vollständiges Höhenprofil (kein Hindernis)."""
    async def elevation_profile(self, *args, **kwargs):
        return [0.0, 0.0, 0.0, 0.0, 0.0], False


def test_hoehenprofil_fehler_liefert_nicht_geprueft_nie_frei():
    """Testplan #3: simulierter API-Fehler -> 'nicht_geprueft', niemals 'frei'."""
    loc = _FakeLoc(
        observer_lat=52.50, observer_lon=13.40,
        subject_lat=52.51, subject_lon=13.41, subject_height_m=30.0,
    )
    result = asyncio.run(sl.compute_location_sightline(loc, _FailingElevationProvider()))
    assert result["status"] == "nicht_geprueft"
    assert result["status"] != "frei"


def test_fehlende_standort_koordinaten_liefert_nicht_geprueft():
    """Edge Case: Location ohne Beobachter-Koordinaten -> 'nicht_geprueft',
    kein Crash (getattr-Duck-Typing-Pfad)."""
    loc = _FakeLoc(observer_lat=None, observer_lon=None,
                   subject_lat=52.51, subject_lon=13.41)
    result = asyncio.run(sl.compute_location_sightline(loc, _OkElevationProvider()))
    assert result["status"] == "nicht_geprueft"


# ---------------------------------------------------------------------------
# update_location_sightline() — Persistenz im Store (analog qa_azimuth)
# ---------------------------------------------------------------------------

def test_update_location_sightline_persistiert_ergebnis(store: LocationStore, monkeypatch):
    """Testplan #9 (implizit, Regel 3): Ergebnis wird nach location_qa_values
    geschrieben, inkl. Zeitstempel — unabhängig vom Ergebnis (auch bei
    'nicht_geprueft' wird geschrieben, damit sightline_checked_at aktuell ist)."""
    # fetch_buildings_along_line würde einen echten Overpass-Call machen —
    # für den Test durch eine leere Liste ersetzen (kein Netzwerk in Tests).
    monkeypatch.setattr(
        "data.qa_azimuth.fetch_buildings_along_line",
        lambda *a, **kw: [],
    )
    loc = _FakeLoc(
        id="loc-us09-test",
        observer_lat=52.50, observer_lon=13.40,
        subject_lat=52.51, subject_lon=13.41, subject_height_m=30.0,
    )
    result = asyncio.run(sl.update_location_sightline(store, loc, _OkElevationProvider()))
    assert result["status"] == "frei"

    saved = store.get_qa_values("loc-us09-test")
    assert saved is not None
    assert saved["sightline_status"] == "frei"
    assert saved["sightline_checked_at"] is not None


def test_update_location_sightline_speichert_auch_nicht_geprueft(store: LocationStore, monkeypatch):
    """Regel 4 + Persistenz: auch ein 'nicht_geprueft'-Ergebnis wird geschrieben
    (Zeitstempel muss aktuell sein, alte 'blockiert'/'frei'-Anzeige darf nicht
    stillschweigend stehen bleiben ohne dass der Versuch vermerkt wird)."""
    monkeypatch.setattr(
        "data.qa_azimuth.fetch_buildings_along_line",
        lambda *a, **kw: [],
    )
    loc = _FakeLoc(
        id="loc-us09-test-2",
        observer_lat=52.50, observer_lon=13.40,
        subject_lat=52.51, subject_lon=13.41, subject_height_m=30.0,
    )
    result = asyncio.run(sl.update_location_sightline(store, loc, _FailingElevationProvider()))
    assert result["status"] == "nicht_geprueft"

    saved = store.get_qa_values("loc-us09-test-2")
    assert saved is not None
    assert saved["sightline_status"] == "nicht_geprueft"
