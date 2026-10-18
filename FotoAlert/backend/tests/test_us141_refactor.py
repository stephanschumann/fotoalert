"""US-141 / BUG-118 — Refactor-Check (2026-10-15): Absicherung der Stellen, die beim Aufräumen
zusammengeführt wurden und bisher keinen eigenen Test hatten. Es wird nur VERHALTEN geprüft, das vor und
nach dem Aufräumen gleich sein muss (nichts Neues):

  - die drei „Merklisten“ im Speicher (offene Entscheidung, Nachladen, Kalender-Nachladen) arbeiten
    unabhängig voneinander,
  - Einzel-Einmischen in die Feed-Datei = Einmischen für mehrere Orte mit einem Ort,
  - Austausch der Kalendertermine EINES Orts im Arbeitsspeicher (Sortierung bleibt, andere Orte bleiben),
  - die Fortschrittsdatei des Nachladens (fertige Orte, fremder Prozess, kaputte Datei).

Alles offline, nur temporäre Dateien und Datenbanken.
"""
import json
import logging

import pytest

import main
import precompute as P
from data.store import LocationStore

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _ev(loc_id, tage):
    return [{"location_id": loc_id, "shoot_time": "2026-10-%02dT05:00:00+00:00" % t, "overall_score": 0.5}
            for t in tage]


# ── Merklisten im Speicher ───────────────────────────────────────────────────

def test_merklisten_sind_voneinander_unabhaengig(tmp_path):
    s = LocationStore(tmp_path / "t.db")
    s.mark_area_undecided("u1")
    assert s.merke_nachladen(["n1", "n2"]) == 2
    assert s.merke_nachladen_kalender(["k1"]) == 1
    assert s.load_area_undecided() == {"u1"}
    assert s.lade_nachladen() == {"n1", "n2"}
    assert s.lade_nachladen_kalender() == {"k1"}


def test_merklisten_vergessen_und_doppelt_merken(tmp_path):
    s = LocationStore(tmp_path / "t.db")
    s.merke_nachladen(["n1", "n2"])
    s.merke_nachladen(["n1"])                      # doppelt: bleibt eine Zeile
    assert s.lade_nachladen() == {"n1", "n2"}
    assert s.vergiss_nachladen(["n1"]) == 1
    assert s.lade_nachladen() == {"n2"}
    s.merke_nachladen_kalender(["k1", "k2"])
    s.vergiss_nachladen_kalender(["k1"])
    assert s.lade_nachladen_kalender() == {"k2"}
    s.mark_area_undecided("u1")
    s.mark_area_undecided("u2")
    assert s.clear_area_undecided(["u1"]) == 1
    assert s.load_area_undecided() == {"u2"}


def test_merklisten_leere_eingabe_aendert_nichts(tmp_path):
    s = LocationStore(tmp_path / "t.db")
    s.merke_nachladen(["n1"])
    assert s.merke_nachladen([]) == 0
    assert s.vergiss_nachladen([]) == 0
    assert s.clear_area_undecided([]) == 0
    assert s.merke_nachladen_kalender([]) == 0
    assert s.vergiss_nachladen_kalender(()) == 0
    assert s.lade_nachladen() == {"n1"}


# ── Feed-Datei: ein Ort ──────────────────────────────────────────────────────

def test_feed_einzelort_ersetzt_nur_diesen_ort_und_sortiert(tmp_path):
    feed = tmp_path / "opportunities.json"
    P._merge_and_write_feed(feed, "a", _ev("a", [3, 1]), "t0")
    P._merge_and_write_feed(feed, "b", _ev("b", [2]), "t1")
    gesamt = P._merge_and_write_feed(feed, "a", _ev("a", [5]), "t2")      # a wird ersetzt
    daten = json.loads(feed.read_text(encoding="utf-8"))
    assert gesamt == 2 and daten["computed_at"] == "t2"
    assert [(e["location_id"], e["shoot_time"][8:10]) for e in daten["opportunities"]] == [("b", "02"), ("a", "05")]


def test_feed_unlesbare_datei_wird_mit_warnung_nur_mit_neuen_terminen_geschrieben(tmp_path, caplog):
    feed = tmp_path / "opportunities.json"
    feed.write_text("{kaputt", encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        gesamt = P._merge_and_write_feed(feed, "a", _ev("a", [1]), "t0")
    assert gesamt == 1
    assert len(json.loads(feed.read_text(encoding="utf-8"))["opportunities"]) == 1
    assert any("nicht lesbar" in r.getMessage() for r in caplog.records)


# ── Kalender im Arbeitsspeicher: ein Ort ─────────────────────────────────────

def test_kalender_austausch_eines_orts_behaelt_andere_und_sortierung(monkeypatch):
    def ev(loc, tag, score):
        return {"location_id": loc, "shoot_time": "2026-10-%02dT05:00:00+00:00" % tag, "overall_score": score,
                "date": "2026-10-%02d" % tag}
    alt = [ev("a", 1, .5), ev("b", 2, .5), ev("a", 4, .5), ev("b", 6, .5)]
    alt.sort(key=main._calendar_sort_key)
    monkeypatch.setattr(main, "_calendar_cache", alt)
    n = main._swap_calendar_events("a", [ev("a", 5, .7), ev("a", 3, .7)])
    assert n == 2
    ids = [(e["location_id"], e["shoot_time"][8:10]) for e in main._calendar_cache]
    assert ids == [("b", "02"), ("a", "03"), ("a", "05"), ("b", "06")]


# ── Fortschrittsdatei des Nachladens ─────────────────────────────────────────

def test_fortschritt_lesen(tmp_path, monkeypatch):
    datei = tmp_path / "nachladen_fortschritt.json"
    monkeypatch.setattr(main, "_NACHLADEN_FORTSCHRITT", datei)
    assert main._nachladen_lies_fortschritt(None) == []                     # Datei fehlt
    datei.write_text("{kaputt", encoding="utf-8")
    assert main._nachladen_lies_fortschritt(None) == []                     # kaputt
    datei.write_text(json.dumps({"pid": 7, "fertig": ["a", "b"]}), encoding="utf-8")
    assert main._nachladen_lies_fortschritt(None) == ["a", "b"]             # ohne Prozess-Filter
    assert main._nachladen_lies_fortschritt(7) == ["a", "b"]
    assert main._nachladen_lies_fortschritt(8) == []                        # fremder Prozess
    datei.write_text(json.dumps(["kein", "dict"]), encoding="utf-8")
    assert main._nachladen_lies_fortschritt_voll(None) == {}
