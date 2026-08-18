"""
BUG-102: Motiv-Koordinaten (SUBJECTS) frieren beim Serverstart ein — Scout-
Chancen ignorieren nachträgliche Koordinatenkorrekturen bis zum Neustart.

Ticket: BACKLOG.md, BUG-102 (Option A — In-Place-Mutation der bestehenden
Container, empfohlene/umgesetzte Option).

Root Cause: `SUBJECTS, EXCLUSION_ZONES = build_subjects()` in
backend/discover/subjects.py wurde bisher einmalig beim ersten Modul-Import
berechnet. `moon_pipeline.py`, `sun_pipeline.py` UND `pipeline_base.py`
(dritte, im Ticket ursprünglich nicht genannte Importstelle) binden beim
eigenen `from discover.subjects import SUBJECTS`/`EXCLUSION_ZONES` jeweils
einen eigenen Namen an das zum Importzeitpunkt gültige Objekt. Eine einfache
Neuzuweisung in subjects.py hätte diese drei bereits gebundenen Namen NICHT
erreicht (Python-Importsemantik) — deshalb mutiert `refresh_subjects()` die
bestehenden Container IN-PLACE (Objektidentität bleibt erhalten), statt sie
neu zuzuweisen.

Diese Datei sichert genau dieses Mutations-Verhalten ab (Pre-Mortem Szenario
1 aus dem Ticket: "Fix ersetzt die Zuweisung statt zu mutieren -> Konsumenten
bleiben beim alten Objekt hängen, Bug bleibt real, nur unsichtbar").
"""
from __future__ import annotations

import time

import pytest

from discover import subjects as subjects_module
from discover.subjects import DiscoverSubject


pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _fake_subject(id_suffix: str = "test", lat: float = 52.5, lon: float = 13.4) -> DiscoverSubject:
    return DiscoverSubject(
        id=f"bug102_fake_{id_suffix}",
        name="BUG-102 Test-Motiv",
        kategorie="🏙 Skyline",
        lat=lat,
        lon=lon,
        structure_height_m=100.0,
        terrain_offset_m=0.0,
        subject_width_m=30.0,
        hoehe_confidence="mittel",
    )


@pytest.fixture(autouse=True)
def _restore_real_subjects():
    """Jeder Test in dieser Datei darf SUBJECTS/EXCLUSION_ZONES/SUBJECT_BY_ID
    per Monkeypatch von build_subjects() mit Fake-Daten befüllen
    (refresh_subjects() mutiert in-place, s.u.). Nach jedem Test wird der
    echte Stand aus dem aktuellen LOCATIONS-Bestand wiederhergestellt, damit
    andere Testdateien, die im selben Prozess NACH dieser Datei laufen,
    wieder reale Produktionsdaten sehen statt der hier verwendeten
    Fake-Motive (kein Seiteneffekt auf andere Suiten). monkeypatch.undo()
    läuft vor dieser Teardown (pytest: LIFO-Reihenfolge, autouse-Fixture
    wurde zuerst aufgesetzt), build_subjects() ist an dieser Stelle also
    bereits wieder die echte Funktion.
    """
    yield
    subjects_module.refresh_subjects()


class _FakeConsumerModule:
    """Simuliert exakt die Import-Semantik von moon_pipeline.py/sun_pipeline.py/
    pipeline_base.py: `from discover.subjects import SUBJECTS` bindet einen
    Namen im Zielmodul an das zum Importzeitpunkt aktuelle Objekt. Eine
    einfache Variablenzuweisung `self.SUBJECTS = subjects_module.SUBJECTS`
    erzeugt exakt dieselbe Namensbindungs-Semantik wie ein
    `from ... import ...` — beides bindet lediglich einen neuen Namen an
    dasselbe Objekt, ohne es zu kopieren.
    """

    def __init__(self):
        self.SUBJECTS = subjects_module.SUBJECTS
        self.EXCLUSION_ZONES = subjects_module.EXCLUSION_ZONES


# ---------------------------------------------------------------------------
# Basis-Anker (AK1/AK2)
# ---------------------------------------------------------------------------

def test_refresh_subjects_recomputes_from_current_locations(monkeypatch):
    """Nach einer Motiv-Koordinatenänderung liefert der nächste
    refresh_subjects()-Aufruf tatsächlich neue Werte."""
    fake = _fake_subject("basis")
    monkeypatch.setattr(subjects_module, "build_subjects", lambda: ([fake], {fake.id: [(1.0, 2.0)]}))

    subjects_module.refresh_subjects()

    assert subjects_module.SUBJECTS == [fake]
    assert subjects_module.EXCLUSION_ZONES == {fake.id: [(1.0, 2.0)]}
    assert subjects_module.SUBJECT_BY_ID == {fake.id: fake}


# ---------------------------------------------------------------------------
# Kerntest gegen das Mutations-Risiko (Pre-Mortem Szenario 1)
# ---------------------------------------------------------------------------

def test_refresh_subjects_mutates_in_place_object_identity_preserved(monkeypatch):
    """SUBJECTS/EXCLUSION_ZONES/SUBJECT_BY_ID bleiben nach refresh_subjects()
    dieselben Objekte (id() unverändert) — nur ihr INHALT ändert sich. Das
    ist der Kernmechanismus, der die drei Konsumenten-Module erreicht, ohne
    dass diese selbst geändert werden müssen."""
    subjects_id_before = id(subjects_module.SUBJECTS)
    zones_id_before = id(subjects_module.EXCLUSION_ZONES)
    by_id_id_before = id(subjects_module.SUBJECT_BY_ID)

    fake = _fake_subject("identity")
    monkeypatch.setattr(subjects_module, "build_subjects", lambda: ([fake], {fake.id: [(3.0, 4.0)]}))
    subjects_module.refresh_subjects()

    assert id(subjects_module.SUBJECTS) == subjects_id_before
    assert id(subjects_module.EXCLUSION_ZONES) == zones_id_before
    assert id(subjects_module.SUBJECT_BY_ID) == by_id_id_before
    # Inhalt hat sich trotzdem geändert:
    assert subjects_module.SUBJECTS == [fake]


def test_naive_reassignment_would_break_object_identity_control():
    """Kontrolltest (beweist, dass der Identitäts-Test oben wirklich etwas
    prüft): eine NEUZUWEISUNG — der nicht gewählte, falsche Fix-Ansatz aus
    dem Pre-Mortem — ändert die Objektidentität. Genau das darf
    refresh_subjects() NICHT tun."""
    a = [1, 2, 3]
    a_id = id(a)

    a = [4, 5, 6]  # Neuzuweisung, kein In-Place-Mutieren

    assert id(a) != a_id


def test_refresh_subjects_propagates_to_a_previously_bound_reference(monkeypatch):
    """Simuliert exakt, was moon_pipeline.py/sun_pipeline.py/pipeline_base.py
    beim eigenen `from discover.subjects import SUBJECTS, EXCLUSION_ZONES`
    Modul-Import tun: einen Namen an das zu diesem Zeitpunkt gültige Objekt
    binden. Beweist, dass genau dieser bereits gebundene Name nach einem
    refresh_subjects()-Aufruf automatisch die neuen Werte sieht — ohne dass
    das 'Konsumenten-Modul' selbst geändert oder neu importiert werden muss.
    """
    consumer = _FakeConsumerModule()  # bindet wie beim echten Modul-Import

    fake = _fake_subject("consumer")
    monkeypatch.setattr(subjects_module, "build_subjects", lambda: ([fake], {fake.id: [(5.0, 6.0)]}))
    subjects_module.refresh_subjects()

    assert consumer.SUBJECTS == [fake]
    assert consumer.EXCLUSION_ZONES == {fake.id: [(5.0, 6.0)]}
    assert consumer.SUBJECTS is subjects_module.SUBJECTS
    assert consumer.EXCLUSION_ZONES is subjects_module.EXCLUSION_ZONES


# ---------------------------------------------------------------------------
# Echte Konsumenten-Module: moon_pipeline.py / sun_pipeline.py / pipeline_base.py
# ---------------------------------------------------------------------------

def test_refresh_subjects_propagates_to_real_moon_and_sun_pipeline_modules(monkeypatch):
    """Importiert die ECHTEN drei Konsumenten-Module (nicht nur eine
    Simulation) und prüft, dass ihre beim Modul-Import gebundenen
    SUBJECTS/EXCLUSION_ZONES-Namen nach refresh_subjects() die neuen Werte
    zeigen. Übersprungen, wenn die schweren Pipeline-Abhängigkeiten
    (skyfield/numpy für astronomy.py, httpx für weather.py) in der aktuellen
    Umgebung nicht installiert sind — läuft real in der vollen
    Dev-Umgebung (backend/venv, siehe bootstrap_sandbox.sh)."""
    pytest.importorskip("skyfield", reason="moon_pipeline/sun_pipeline brauchen skyfield (calculations.astronomy)")
    pytest.importorskip("httpx", reason="pipeline_base braucht httpx (calculations.weather)")

    from discover import moon_pipeline, sun_pipeline, pipeline_base

    fake = _fake_subject("real_modules")
    monkeypatch.setattr(subjects_module, "build_subjects", lambda: ([fake], {fake.id: [(7.0, 8.0)]}))
    subjects_module.refresh_subjects()

    assert moon_pipeline.SUBJECTS == [fake]
    assert sun_pipeline.SUBJECTS == [fake]
    assert pipeline_base.EXCLUSION_ZONES == {fake.id: [(7.0, 8.0)]}

    # Objektidentität: dieselben Listen-/Dict-Objekte wie in subjects.py, nicht
    # nur zufällig gleicher Inhalt.
    assert moon_pipeline.SUBJECTS is subjects_module.SUBJECTS
    assert sun_pipeline.SUBJECTS is subjects_module.SUBJECTS
    assert pipeline_base.EXCLUSION_ZONES is subjects_module.EXCLUSION_ZONES


# ---------------------------------------------------------------------------
# AK3: Ausschlusszonen (bekannte Fotografen-Standorte) — nicht nur die
# Motiv-Koordinate (Pre-Mortem Szenario 3)
# ---------------------------------------------------------------------------

def test_refresh_subjects_updates_exclusion_zones_used_by_is_new_perspective(monkeypatch):
    """AK3 + Pre-Mortem Szenario 3: ein verschobener bekannter
    Fotografen-Standort muss auch in der Ausschlusszonen-Prüfung
    (is_new_perspective(), pipeline_base.py) ankommen — nicht nur in der
    Motiv-Koordinate selbst."""
    pytest.importorskip("skyfield")
    pytest.importorskip("httpx")

    from discover import pipeline_base

    fake = _fake_subject("zones")
    old_observer = (52.0, 13.0)
    new_observer = (52.1, 13.1)  # > SCOUT_MIN_NEW_DISTANCE_M (150m) von old_observer entfernt

    # Alter Stand: old_observer ist bekannter Standpunkt -> zu nah -> keine neue Perspektive.
    monkeypatch.setattr(subjects_module, "build_subjects", lambda: ([fake], {fake.id: [old_observer]}))
    subjects_module.refresh_subjects()
    assert pipeline_base.is_new_perspective(old_observer[0], old_observer[1], fake.id) is False

    # Standort wurde verschoben -> nächster Lauf ruft refresh_subjects() erneut auf.
    monkeypatch.setattr(subjects_module, "build_subjects", lambda: ([fake], {fake.id: [new_observer]}))
    subjects_module.refresh_subjects()

    # Alte Sperrzone ist weg: der alte Standpunkt gilt jetzt wieder als neue Perspektive.
    assert pipeline_base.is_new_perspective(old_observer[0], old_observer[1], fake.id) is True
    # Neue Sperrzone gilt: der neue Standpunkt selbst ist weiterhin gesperrt.
    assert pipeline_base.is_new_perspective(new_observer[0], new_observer[1], fake.id) is False


# ---------------------------------------------------------------------------
# AK5: mehrere Korrekturen kurz hintereinander -- kein Zwischenstand
# ---------------------------------------------------------------------------

def test_refresh_subjects_multiple_rapid_corrections_only_last_wins(monkeypatch):
    """AK5 Edge Case: mehrere Korrekturen vor Laufbeginn — nur die zuletzt
    gespeicherte Koordinate zählt, kein halbfertiger Zwischenstand."""
    fake_v1 = _fake_subject("multi", lat=1.0, lon=1.0)
    fake_v2 = DiscoverSubject(
        id=fake_v1.id, name=fake_v1.name, kategorie=fake_v1.kategorie,
        lat=99.0, lon=99.0, structure_height_m=fake_v1.structure_height_m,
        terrain_offset_m=fake_v1.terrain_offset_m, subject_width_m=fake_v1.subject_width_m,
        hoehe_confidence=fake_v1.hoehe_confidence,
    )

    calls = {"n": 0}

    def fake_build():
        calls["n"] += 1
        # In der echten App liest build_subjects() bei jedem Aufruf frisch aus
        # LOCATIONS -- hier simuliert durch: erster Aufruf liefert v1, jeder
        # weitere liefert v2 (die "zuletzt gespeicherte" Koordinate).
        return ([fake_v1] if calls["n"] == 1 else [fake_v2]), {}

    monkeypatch.setattr(subjects_module, "build_subjects", fake_build)

    subjects_module.refresh_subjects()
    subjects_module.refresh_subjects()
    subjects_module.refresh_subjects()

    assert subjects_module.SUBJECTS == [fake_v2]
    assert subjects_module.SUBJECTS[0].lat == 99.0


# ---------------------------------------------------------------------------
# AK6: unveränderte Daten -> identisches Ergebnis (Regressionsschutz)
# ---------------------------------------------------------------------------

def test_refresh_subjects_no_data_change_yields_identical_result():
    """AK6: verändert sich zwischen zwei Läufen nichts an den Standort-Daten,
    unterscheidet sich das Ergebnis inhaltlich nicht — reiner
    Regressionsschutz gegen die bestehende, unveränderte Berechnungslogik."""
    before_subjects = list(subjects_module.SUBJECTS)
    before_zones = dict(subjects_module.EXCLUSION_ZONES)

    subjects_module.refresh_subjects()

    assert subjects_module.SUBJECTS == before_subjects
    assert subjects_module.EXCLUSION_ZONES == before_zones


# ---------------------------------------------------------------------------
# Performance-Sanity
# ---------------------------------------------------------------------------

def test_refresh_subjects_is_fast_enough_for_every_run():
    """Performance-Sanity: die Neuberechnung ist real gemessen ~0.4ms teuer
    (siehe BACKLOG.md BUG-102, Code-Verifikation) — deutlich billiger als ein
    kompletter Scout-Lauf (Minuten). Großzügige Obergrenze (2s), um in
    unterschiedlich schnellen CI-/Sandbox-Umgebungen nicht flaky zu sein,
    ohne eine echte Performance-Regression zu übersehen."""
    start = time.monotonic()
    subjects_module.refresh_subjects()
    elapsed = time.monotonic() - start

    assert elapsed < 2.0, f"refresh_subjects() dauerte {elapsed:.3f}s -- unerwartet teuer"


# ---------------------------------------------------------------------------
# Aufrufstelle: run_pipeline() ruft refresh_subjects() am Lauf-Einstiegspunkt
# ---------------------------------------------------------------------------

def test_pipeline_run_pipeline_calls_refresh_subjects_at_start(monkeypatch):
    """Pre-Mortem Szenario 2 (Rebuild muss synchron am gemeinsamen
    Lauf-Einstiegspunkt passieren, kein zweiter Aufrufpfad): prüft, dass
    discover.pipeline.run_pipeline() tatsächlich subjects.refresh_subjects()
    aufruft — nicht nur, dass die Funktion irgendwo existiert."""
    pytest.importorskip("skyfield")
    pytest.importorskip("httpx")

    import asyncio
    from discover import pipeline as pipeline_module

    calls = {"n": 0}

    def _fake_refresh_subjects():
        calls["n"] += 1

    async def _fake_moon_run(days):
        return []

    async def _fake_sun_run(days):
        return []

    monkeypatch.setattr(pipeline_module, "refresh_subjects", _fake_refresh_subjects)
    # Restliche Pipeline-Ausführung nicht real laufen lassen (kein Netzwerk/Wetter
    # in diesem Test) — nur der Aufruf von refresh_subjects() wird geprüft.
    monkeypatch.setattr(pipeline_module.moon_pipeline, "run", _fake_moon_run)
    monkeypatch.setattr(pipeline_module.sun_pipeline, "run", _fake_sun_run)
    monkeypatch.setattr(pipeline_module, "filter_accessible_candidates", lambda opps: opps)

    asyncio.run(pipeline_module.run_pipeline(days=1))

    assert calls["n"] == 1
