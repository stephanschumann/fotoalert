"""US-138 (England/London), AK18 — Feed-Deckel 500 behaelt England-Chancen zuerst.

Problem: /opportunities liefert hoechstens 500 Chancen; haeufige Event-Typen/Orte
verdraengten die wenigen London-Chancen. Neu: main._filter_feed behaelt bei der Kappung
alle Chancen von England-Orten (is_england auf observer_lat/observer_lon) zuerst und fuellt
mit den uebrigen in der bisherigen Reihenfolge (Round-Robin pro Event-Typ nach Score)
bis 500 auf. Die Ausgabe bleibt nach Zeit sortiert.

Getestet:
  T1  England-Chancen (niedriger Score) bleiben trotz 700 staerkerer Berliner Chancen erhalten
  T2  Gesamtzahl <= 500 (auch bei mehr als 500 England-Chancen)
  T3  ohne England-Orte identisch zum bisherigen Ergebnis (Referenz-Nachbau der alten Logik,
      mehrere Event-Typen, mehr als 500 Chancen)
  T4  Ausgabe bleibt nach Zeit sortiert
  T5  Nicht-England-Auswahl = bisherige Round-Robin-Reihenfolge ohne die England-Chancen
  T6  Eintraege ohne Koordinaten gelten als "nicht England" (bisheriges Verhalten)

Python-3.9-kompatibel.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import main  # noqa: E402

pytestmark = [pytest.mark.offline, pytest.mark.regression]

LONDON = (51.5, -0.12)
BERLIN = (52.52, 13.40)
_NOW = datetime.now(timezone.utc)


def _ev(i, typ, score, coords, prefix):
    t = _NOW + timedelta(hours=1 + (i % 1000) * 0.3)
    ev = {
        "id": "%s-%d" % (prefix, i),
        "location_id": "%s-%d" % (prefix, i),   # je Chance eigener Ort: Dedup greift nicht
        "event_type": typ,
        "overall_score": score,
        "alert_priority": 1,
        "shoot_time": t.isoformat(),
        "shoot_window_end": (t + timedelta(minutes=30)).isoformat(),
    }
    if coords is not None:
        ev["observer_lat"], ev["observer_lon"] = coords
    return ev


def _alt(events):
    """Referenz: die bisherige Logik (vor US-138 AK18) unveraendert nachgebaut."""
    result = sorted(main._dedup_best_per_day(list(events)), key=lambda e: -e["overall_score"])
    groups = {}
    for e in result:
        groups.setdefault(e["event_type"], []).append(e)
    keys = list(groups)
    idx = {t: 0 for t in keys}
    sel = []
    while len(sel) < 500:
        added = False
        for t in keys:
            if len(sel) >= 500:
                break
            if idx[t] < len(groups[t]):
                sel.append(groups[t][idx[t]])
                idx[t] += 1
                added = True
        if not added:
            break
    sel.sort(key=lambda e: e["shoot_time"])
    return sel


def _run(monkeypatch, events):
    monkeypatch.setattr(main, "_feed_cache", events, raising=False)
    return main._filter_feed(0.2, None, None, 14, None)


def _berlin(n, score_base=0.9):
    types = ["GOLDEN_HOUR", "BLUE_HOUR", "SUNRISE"]
    return [_ev(i, types[i % 3], score_base - (i % 50) * 0.001, BERLIN, "ber") for i in range(n)]


def test_t1_england_bleibt_trotz_ueberzahl(monkeypatch):
    london = [_ev(1000 + i, "GOLDEN_HOUR", 0.40, LONDON, "lon") for i in range(5)]
    res = _run(monkeypatch, _berlin(700) + london)
    ids = {e["id"] for e in res}
    for e in london:
        assert e["id"] in ids
    assert len(res) == 500


def test_t2_gesamtzahl_hoechstens_500(monkeypatch):
    london = [_ev(i, "GOLDEN_HOUR", 0.5, LONDON, "lon") for i in range(650)]
    res = _run(monkeypatch, _berlin(300) + london)
    assert len(res) == 500
    assert all(e["id"].startswith("lon") for e in res)


def test_t3_ohne_england_identisch_zu_bisher(monkeypatch):
    events = _berlin(900) + [_ev(2000 + i, "MOON_RISE", 0.3, BERLIN, "mr") for i in range(30)]
    assert _run(monkeypatch, events) == _alt(events)
    assert len(_alt(events)) == 500
    kurz = _berlin(40)
    assert _run(monkeypatch, kurz) == _alt(kurz)


def test_t4_ausgabe_nach_zeit_sortiert(monkeypatch):
    london = [_ev(1000 + i, "BLUE_HOUR", 0.4, LONDON, "lon") for i in range(10)]
    res = _run(monkeypatch, _berlin(700) + london)
    zeiten = [e["shoot_time"] for e in res]
    assert zeiten == sorted(zeiten)


def test_t5_rest_in_bisheriger_reihenfolge(monkeypatch):
    london = [_ev(1000 + i, "GOLDEN_HOUR", 0.4, LONDON, "lon") for i in range(20)]
    ber = _berlin(700)
    res = _run(monkeypatch, ber + london)
    # Rest = die ersten 480 der bisherigen Round-Robin-Reihenfolge der Berliner Chancen
    ref = sorted(main._dedup_best_per_day(list(ber)), key=lambda e: -e["overall_score"])
    groups = {}
    for e in ref:
        groups.setdefault(e["event_type"], []).append(e)
    order, i = [], 0
    while any(i < len(g) for g in groups.values()):
        for g in groups.values():
            if i < len(g):
                order.append(g[i])
        i += 1
    erwartet = {e["id"] for e in order[:480]} | {e["id"] for e in london}
    assert {e["id"] for e in res} == erwartet


def test_t6_ohne_koordinaten_ist_nicht_england(monkeypatch):
    events = [_ev(i, "GOLDEN_HOUR", 0.9 - i * 0.0005, None, "x") for i in range(700)]
    assert _run(monkeypatch, events) == _alt(events)
