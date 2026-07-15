"""TASK-41 — Regressionstest für die Extraktion von _run_single_location_flow()
(backend/precompute.py) in vier Helferfunktionen: Elevation, Sichtachse, Feed,
Kalender.

Kein bestehender Test rief main()/`_run_single_location_flow()` mit
--location-id direkt auf (Pre-Mortem-Szenario 4, TASK-41-Spec). Diese Suite
schließt die Lücke und sichert zusätzlich zwei konkrete Refactoring-Risiken ab:
- Szenario 1: die neu abgerufene Elevation wird auf DASSELBE loc-Objekt
  gepatcht (nicht auf eine Kopie) — Voraussetzung für die Alignment-Berechnung
  in _composition_analysis().
- Szenario 2: jeder der vier Helfer behält sein eigenes lokales try/except —
  ein Fehler im Sichtachsen-Check darf Feed- und Kalenderberechnung NICHT
  verhindern (kein gemeinsames äußeres try/except über mehrere Helfer).

Konvention (vgl. test_bug29_calendar_single_recompute.py): gestubbte
Astronomie-/Elevation-/Sightline-Funktionen + isolierter CACHE_DIR (tmp_path)
— kein Netzwerk-/DB-Zugriff, keine Mutation der aktiven Dev-DB (BUG-61).
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date
from types import SimpleNamespace as NS

import pytest

import precompute as P
import calculations.sightline as sightline_mod
from data import backup as backup_mod

pytestmark = [pytest.mark.offline, pytest.mark.regression]

_LOC_ID = "task41_test_loc"
_OTHER_LOC_ID = "task41_other_loc"


# ── Test-Doubles (Muster aus test_bug29_calendar_single_recompute.py) ─────────

def _loc(loc_id, *, observer_lat=52.5, observer_lon=13.4):
    """Minimale Location: _location_hash nutzt observer_lat/lon, _serialize den Rest."""
    return NS(
        id=loc_id,
        name=f"Loc {loc_id}",
        observer_lat=observer_lat,
        observer_lon=observer_lon,
        subject_lat=observer_lat + 0.001,
        subject_lon=observer_lon + 0.001,
        elevation_difference_m=None,
    )


def _fake_serialize(o):
    loc = o.loc
    return {
        "id": f"{loc.id}-{o.d.isoformat()}",
        "location_id": loc.id,
        "location_name": loc.name,
        "observer_lat": loc.observer_lat,
        "observer_lon": loc.observer_lon,
        "event_type": "Mond-Alignment",
        "shoot_time": f"{o.d.isoformat()}T20:00:00+00:00",
        "overall_score": 0.9,
        "composition_analysis": None,  # -> _passes_alignment_filter == True
    }


async def _fake_find_opportunities(loc, d, *args, **kwargs):
    """Wird intern von compute_calendar_incremental() aufgerufen."""
    return [NS(loc=loc, d=d)]


async def _fake_find_opportunities_multi_day(loc, today, *args, **kwargs):
    """Wird von _refresh_single_location_feed() aufgerufen."""
    return [NS(loc=loc, d=today)]


def _make_args(location_id):
    return argparse.Namespace(
        feed_only=False, calendar_only=False, full=False, location_id=location_id,
    )


@pytest.fixture
def sightline_calls(monkeypatch):
    """Stubt update_location_sightline() und zeichnet Aufrufe auf (keine echte DB/Store)."""
    calls = []

    async def _fake_update_location_sightline(store, loc, elevation_provider):
        calls.append(loc.id)
        return {"status": "ok"}

    monkeypatch.setattr(sightline_mod, "update_location_sightline", _fake_update_location_sightline)
    return calls


@pytest.fixture
def patched(tmp_path, monkeypatch, sightline_calls):
    """Isolierter CACHE_DIR + gestubbte Astronomie/Elevation/Sightline/Backup-Seiteneffekte.

    main() lädt vor dem eigentlichen Flow Custom-Locations/QA-Werte/Overrides und
    schreibt Backups — für diesen Test irrelevant und potenziell DB-mutierend
    (BUG-61), deshalb no-op.
    """
    monkeypatch.setattr(P, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(P, "find_opportunities", _fake_find_opportunities)
    monkeypatch.setattr(P, "find_opportunities_multi_day", _fake_find_opportunities_multi_day)
    monkeypatch.setattr(P, "_serialize", _fake_serialize)

    async def _fake_fetch_elevations(force_refetch_ids=None):
        return {_LOC_ID: {"elevation_difference_m": 12.3}}

    monkeypatch.setattr(P, "fetch_elevations", _fake_fetch_elevations)

    class _FakeStore:
        def load_all_overrides(self):
            return []

    monkeypatch.setattr(P, "LocationStore", _FakeStore)

    monkeypatch.setattr(P, "_load_custom_locations", lambda: 0)
    monkeypatch.setattr(P, "_apply_qa_values", lambda: 0)
    monkeypatch.setattr(P, "_apply_location_overrides", lambda: 0)
    monkeypatch.setattr(backup_mod, "snapshot_before_precompute", lambda: None)
    monkeypatch.setattr(backup_mod, "backup_after_precompute", lambda: None)

    loc = _loc(_LOC_ID)
    other = _loc(_OTHER_LOC_ID)
    monkeypatch.setattr(P, "LOCATIONS", [loc, other])

    return NS(loc=loc, other=other, cache_dir=tmp_path)


def _seed_other_location_cache(cache_dir, today):
    """Legt bestehende Feed-/Kalender-Einträge für _OTHER_LOC_ID an (Edge-Case-Baseline:
    andere Locations müssen nach dem Single-Recompute unverändert bleiben)."""
    other_feed_event = {
        "id": f"{_OTHER_LOC_ID}-{today.isoformat()}",
        "location_id": _OTHER_LOC_ID,
        "location_name": "Loc other",
        "event_type": "Mond-Alignment",
        "shoot_time": f"{today.isoformat()}T18:00:00+00:00",
        "overall_score": 0.5,
    }
    (cache_dir / "opportunities.json").write_text(
        json.dumps({"computed_at": "x", "opportunities": [other_feed_event]}),
        encoding="utf-8",
    )
    other_cal_event = dict(other_feed_event)
    (cache_dir / "calendar.json").write_text(
        json.dumps({
            "algorithm_version": P.ALGORITHM_VERSION,
            "computed_at": "x",
            "computed_locations": {
                _OTHER_LOC_ID: {"coordinates_hash": "x", "computed_dates": [today.isoformat()]},
            },
            "events": [other_cal_event],
        }),
        encoding="utf-8",
    )
    return other_feed_event, other_cal_event


# ── TASK-41 Testplan: main() mit --location-id führt alle vier Schritte aus ───
def test_task41_single_location_flow_runs_all_four_steps(patched, sightline_calls):
    """TASK-41 AK-1/Edge Case: main() mit --location-id führt Elevation-Patch,
    Sichtachsen-Check, Feed-Merge und Kalender-Merge für GENAU diese eine
    Location aus; andere Locations bleiben im Cache unverändert."""
    today = date.today()
    other_feed_event, other_cal_event = _seed_other_location_cache(patched.cache_dir, today)

    asyncio.run(P.main(_make_args(_LOC_ID)))

    # Szenario 1: Elevation auf dasselbe loc-Objekt gepatcht (nicht auf eine Kopie)
    assert patched.loc.elevation_difference_m == 12.3

    # Sichtachsen-Check wurde für die Location ausgeführt
    assert _LOC_ID in sightline_calls

    # Feed-Merge: neue Location im Feed, andere Location unangetastet
    feed = json.loads((patched.cache_dir / "opportunities.json").read_text(encoding="utf-8"))
    feed_ids = {e["location_id"] for e in feed["opportunities"]}
    assert _LOC_ID in feed_ids
    assert _OTHER_LOC_ID in feed_ids
    other_feed_after = next(e for e in feed["opportunities"] if e["location_id"] == _OTHER_LOC_ID)
    assert other_feed_after == other_feed_event, "andere Location darf im Feed unverändert bleiben"

    # Kalender-Merge: neue Location im Kalender, andere Location unangetastet
    calendar = json.loads((patched.cache_dir / "calendar.json").read_text(encoding="utf-8"))
    cal_ids = {e["location_id"] for e in calendar["events"]}
    assert _LOC_ID in cal_ids
    assert _OTHER_LOC_ID in cal_ids
    other_cal_after = next(e for e in calendar["events"] if e["location_id"] == _OTHER_LOC_ID)
    assert other_cal_after == other_cal_event, "andere Location darf im Kalender unverändert bleiben"
    assert set(calendar["computed_locations"].keys()) == {_LOC_ID, _OTHER_LOC_ID}


# ── Pre-Mortem-Szenario 2: kein gemeinsames äußeres try/except über die Helfer ─
def test_task41_sightline_failure_does_not_abort_feed_and_calendar(patched, monkeypatch):
    """Pre-Mortem-Szenario 2 (TASK-41): Ein Fehler im Sichtachsen-Check (eigenes
    try/except) darf Feed- und Kalenderberechnung NICHT verhindern — wäre bei
    der Extraktion versehentlich ein gemeinsames äußeres try/except über mehrere
    Helfer gelegt worden, würde dieser Test rot."""
    async def _raising_sightline(store, loc, elevation_provider):
        raise RuntimeError("Overpass nicht erreichbar")

    monkeypatch.setattr(sightline_mod, "update_location_sightline", _raising_sightline)

    asyncio.run(P.main(_make_args(_LOC_ID)))

    feed = json.loads((patched.cache_dir / "opportunities.json").read_text(encoding="utf-8"))
    assert any(e["location_id"] == _LOC_ID for e in feed["opportunities"]), \
        "Feed muss trotz Sichtachsen-Fehler berechnet werden"

    calendar = json.loads((patched.cache_dir / "calendar.json").read_text(encoding="utf-8"))
    assert any(e["location_id"] == _LOC_ID for e in calendar["events"]), \
        "Kalender muss trotz Sichtachsen-Fehler berechnet werden"

    # Elevation lief vor dem Sichtachsen-Check und ist trotzdem gepatcht
    assert patched.loc.elevation_difference_m == 12.3


# ── Nachbesserung (unabhängige Verifikation 2026-07-14): Elevation-Helfer ─────
def test_task41_elevation_failure_does_not_abort_sightline_feed_and_calendar(patched, monkeypatch, sightline_calls):
    """Pre-Mortem-Szenario 2 (TASK-41), Nachbesserung: `_refresh_single_location_elevation`
    hatte laut unabhängiger Verifikation KEIN eigenes try/except — ein Fehler dort
    propagierte ungefangen und brach Sichtachse/Feed/Kalender ab. Nach dem Fix muss
    ein Elevation-Fehler geloggt werden und die drei nachfolgenden Schritte trotzdem
    laufen."""
    async def _raising_fetch_elevations(force_refetch_ids=None):
        raise RuntimeError("Elevation-API nicht erreichbar")

    monkeypatch.setattr(P, "fetch_elevations", _raising_fetch_elevations)

    # main() darf trotz Elevation-Fehler nicht crashen
    asyncio.run(P.main(_make_args(_LOC_ID)))

    # Elevation-Fehler → loc.elevation_difference_m bleibt unverändert (None, Fixture-Default)
    assert patched.loc.elevation_difference_m is None

    # Sichtachsen-Check lief trotzdem
    assert _LOC_ID in sightline_calls

    # Feed muss trotz Elevation-Fehler berechnet werden
    feed = json.loads((patched.cache_dir / "opportunities.json").read_text(encoding="utf-8"))
    assert any(e["location_id"] == _LOC_ID for e in feed["opportunities"]), \
        "Feed muss trotz Elevation-Fehler berechnet werden"

    # Kalender muss trotz Elevation-Fehler berechnet werden
    calendar = json.loads((patched.cache_dir / "calendar.json").read_text(encoding="utf-8"))
    assert any(e["location_id"] == _LOC_ID for e in calendar["events"]), \
        "Kalender muss trotz Elevation-Fehler berechnet werden"


# ── Nachbesserung (unabhängige Verifikation 2026-07-14): Kalender-Helfer ──────
def test_task41_calendar_failure_is_isolated_and_keeps_prior_steps_intact(patched, monkeypatch, sightline_calls):
    """Pre-Mortem-Szenario 2 (TASK-41), Nachbesserung: `_refresh_single_location_calendar`
    hatte laut unabhängiger Verifikation KEIN eigenes try/except. Ein Fehler in der
    Kalenderberechnung (letzter Schritt) darf weder main() crashen lassen noch die
    bereits abgeschlossenen vorherigen Schritte (Elevation-Patch, Sichtachse, Feed)
    rückwirkend ungültig machen."""
    other_feed_event, other_cal_event = _seed_other_location_cache(patched.cache_dir, date.today())

    async def _raising_compute_calendar_incremental(today, location_id=None):
        raise RuntimeError("Kalenderberechnung fehlgeschlagen")

    monkeypatch.setattr(P, "compute_calendar_incremental", _raising_compute_calendar_incremental)

    # main() darf trotz Kalender-Fehler nicht crashen
    asyncio.run(P.main(_make_args(_LOC_ID)))

    # Vorherige Schritte bleiben unberührt vom Kalender-Fehler
    assert patched.loc.elevation_difference_m == 12.3
    assert _LOC_ID in sightline_calls

    feed = json.loads((patched.cache_dir / "opportunities.json").read_text(encoding="utf-8"))
    assert any(e["location_id"] == _LOC_ID for e in feed["opportunities"]), \
        "Feed muss trotz nachfolgendem Kalender-Fehler berechnet bleiben"

    # Kalender-Datei bleibt unverändert (kein Merge, kein Absturz vor dem Schreiben) —
    # die vor dem Fehler bestehende andere Location bleibt erhalten
    calendar = json.loads((patched.cache_dir / "calendar.json").read_text(encoding="utf-8"))
    assert not any(e["location_id"] == _LOC_ID for e in calendar["events"]), \
        "Kalender-Eintrag für die fehlgeschlagene Location darf nicht auftauchen"
    assert any(e["location_id"] == _OTHER_LOC_ID for e in calendar["events"]), \
        "Bestehender Kalender-Eintrag der anderen Location bleibt unangetastet"
