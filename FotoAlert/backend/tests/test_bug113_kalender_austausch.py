"""BUG-113 (Ergänzung zur Umsetzung, Weg B Schritt 2) — Korrektheit des
Kalender-Austauschs je Standort.

`test_bug113.py` (aus der Analyse-Phase, unverändert) misst ausschließlich, dass
der Server nicht mehr stehenbleibt. Diese Datei schließt die inhaltliche Lücke
dazu: Pre-Mortem Szenario 2 des Tickets ("Kalender/Feed veraltet oder doppelt").
Geprüft wird, dass der neue Austauschweg genau die Ereignisse des geänderten
Standorts ersetzt, die Sortierung erhält, fremde Standorte unangetastet lässt
und bei fehlender/veralteter/fremder Übergabedatei nichts kaputt macht.

Alle Tests laufen offline: kein Netz, kein Subprozess, keine großen Dateien.
"""
import asyncio
import json

import pytest

import main

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _ev(loc_id: str, shoot_time: str, score: float) -> dict:
    return {"location_id": loc_id, "shoot_time": shoot_time, "overall_score": score}


def _bestand() -> list:
    """Bestand wie in calendar.json: nach (shoot_time, -overall_score) sortiert."""
    return [
        _ev("alt_a", "2026-10-01T05:00:00+00:00", 0.9),
        _ev("neu_x", "2026-10-01T06:00:00+00:00", 0.4),   # alter Stand von neu_x
        _ev("alt_b", "2026-10-02T05:00:00+00:00", 0.8),
        _ev("neu_x", "2026-10-03T05:00:00+00:00", 0.3),   # alter Stand von neu_x
        _ev("alt_a", "2026-10-04T05:00:00+00:00", 0.7),
    ]


def _schreibe_postfach(tmp_path, loc_id: str, events: list):
    kal = tmp_path / "calendar.json"
    kal.write_text("{}", encoding="utf-8")
    postfach = tmp_path / main._CAL_SINGLE_DELTA_NAME
    postfach.write_text(
        json.dumps({"location_id": loc_id, "computed_at": "2026-09-19T00:00:00+00:00",
                    "events": events}, ensure_ascii=False),
        encoding="utf-8",
    )
    return kal, postfach


def test_austausch_ersetzt_nur_den_einen_standort_und_haelt_die_sortierung(monkeypatch, tmp_path):
    """BUG-113 AK4/Pre-Mortem 2: Nach dem Austausch stehen genau die neuen Ereignisse
    des geänderten Standorts im Kalender — keine Dubletten, keine verlorenen fremden
    Ereignisse, Sortierung wie in calendar.json."""
    neue = [
        _ev("neu_x", "2026-10-01T07:00:00+00:00", 0.95),
        _ev("neu_x", "2026-10-05T05:00:00+00:00", 0.6),
    ]
    kal, _ = _schreibe_postfach(tmp_path, "neu_x", neue)
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    monkeypatch.setattr(main, "_calendar_cache", _bestand())

    assert asyncio.run(main._apply_calendar_delta("neu_x")) is True

    cache = main._calendar_cache
    eigene = [e for e in cache if e["location_id"] == "neu_x"]
    fremde = [e for e in cache if e["location_id"] != "neu_x"]
    assert eigene == neue, "Ereignisse des geänderten Standorts nicht sauber ersetzt"
    assert len(fremde) == 3, "Ereignisse anderer Standorte wurden verändert"
    assert [e["shoot_time"] for e in cache] == sorted(e["shoot_time"] for e in cache), \
        "Kalender ist nach dem Austausch nicht mehr aufsteigend nach Zeit sortiert"


def test_austausch_ohne_postfach_laesst_den_kalender_unveraendert(monkeypatch, tmp_path):
    """BUG-113 AK6 (Fehlerfall): Fehlt die Übergabedatei (z. B. abgebrochene
    Kalenderberechnung), bleibt der Kalender im Arbeitsspeicher exakt wie er war —
    und es wird KEIN Vollneuladen der großen Datei ausgelöst."""
    kal = tmp_path / "calendar.json"
    kal.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    vorher = _bestand()
    monkeypatch.setattr(main, "_calendar_cache", list(vorher))

    assert asyncio.run(main._apply_calendar_delta("neu_x")) is False
    assert main._calendar_cache == vorher


def test_austausch_ignoriert_postfach_eines_anderen_standorts(monkeypatch, tmp_path):
    """BUG-113: Gehört die Übergabedatei zu einem anderen Standort (Reihenfolge-
    Kollision zweier Läufe), wird sie nicht angewendet."""
    kal, _ = _schreibe_postfach(tmp_path, "ganz_anderer", [_ev("ganz_anderer", "2026-10-01T05:00:00+00:00", 1.0)])
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    vorher = _bestand()
    monkeypatch.setattr(main, "_calendar_cache", list(vorher))

    assert asyncio.run(main._apply_calendar_delta("neu_x")) is False
    assert main._calendar_cache == vorher


def test_austausch_ignoriert_veraltetes_postfach(monkeypatch, tmp_path):
    """BUG-113: Ein Postfach, das älter ist als der gerade gelaufene Kalenderlauf,
    stammt aus einem früheren Lauf und darf nicht angewendet werden."""
    import time
    kal, postfach = _schreibe_postfach(tmp_path, "neu_x", [_ev("neu_x", "2026-10-09T05:00:00+00:00", 1.0)])
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    vorher = _bestand()
    monkeypatch.setattr(main, "_calendar_cache", list(vorher))

    # Lauf hat erst NACH dem Schreiben des Postfachs begonnen → Postfach ist veraltet.
    assert asyncio.run(main._apply_calendar_delta("neu_x", min_mtime=time.time() + 60)) is False
    assert main._calendar_cache == vorher


def test_precompute_schreibt_postfach_mit_nur_dieser_location(tmp_path):
    """BUG-113: precompute.py legt neben calendar.json das kleine Postfach an und
    nimmt dort ausschließlich die Ereignisse des gerade gerechneten Standorts auf."""
    import precompute

    cal_path = tmp_path / "calendar.json"
    calendar = _bestand()
    anzahl = precompute._write_calendar_single_delta(
        cal_path, "neu_x", calendar, "2026-09-19T00:00:00+00:00",
    )
    postfach = tmp_path / "calendar_single_last.json"
    assert postfach.exists(), "Übergabedatei wurde nicht geschrieben"
    data = json.loads(postfach.read_text(encoding="utf-8"))
    assert data["location_id"] == "neu_x"
    assert anzahl == 2 and len(data["events"]) == 2
    assert all(e["location_id"] == "neu_x" for e in data["events"])
    assert postfach.name == main._CAL_SINGLE_DELTA_NAME, \
        "Dateiname weicht zwischen precompute.py und main.py ab"
