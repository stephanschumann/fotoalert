"""US-141 (Abdeckungs-Check 2026-10-11) — Schreib-Sicherheit der Vorberechnungs-Dateien.

Hintergrund: Der Schalter für Regionen macht Nachlade-Läufe (und damit gleichzeitige
Schreibzugriffe auf die Feed- und Kalenderdatei) deutlich häufiger. Heute schreiben die
Vorberechnungs-Funktionen die Zieldatei direkt, ohne Zwischendatei und ohne Sperre.
Diese Tests beschreiben die ANFORDERUNG, nicht eine bestimmte Umsetzung:
  - A1: Bricht das Schreiben mittendrin ab (Absturz, Platte voll, Prozess beendet), bleibt
    die bisherige Datei vollständig lesbar und unverändert — nie eine halbe Datei.
    (Feed-Merge, Feed komplett, Kalender komplett.)
  - A2: Zwei Schreibläufe, die gleichzeitig Termine verschiedener Orte in den Feed
    einmischen, verlieren keine Termine (kein „zuletzt schreibt gewinnt“).

Bewusst NICHT getestet (braucht Entscheidungen des Weg-Gates): ob ein offener Nachlade-Auftrag
einen Neustart überlebt — dafür muss erst feststehen, WO der Auftrag gespeichert wird.
Alles offline, nur temporäre Dateien.
"""
import json
import pathlib
import threading
import time

import pytest

import precompute as P

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _ev(loc_id: str, n: int = 1):
    return [
        {"location_id": loc_id, "shoot_time": f"2026-10-1{i}T05:00:00+00:00", "overall_score": 0.5}
        for i in range(n)
    ]


def _halb_schreiben_dann_fehler(monkeypatch):
    """Schreibversuch bricht nach der Hälfte der Daten ab (egal in welche Datei)."""
    original = pathlib.Path.write_text

    def kaputt(self, data, *a, **kw):
        original(self, data[: len(data) // 2], *a, **kw)
        raise OSError("Platte voll (Test)")

    monkeypatch.setattr(pathlib.Path, "write_text", kaputt)


def test_a1_feed_merge_abbruch_laesst_alte_datei_ganz(tmp_path, monkeypatch):
    feed = tmp_path / "opportunities.json"
    P._merge_and_write_feed(feed, "a", _ev("a", 3), "t0")
    vorher = feed.read_text(encoding="utf-8")
    _halb_schreiben_dann_fehler(monkeypatch)
    with pytest.raises(OSError):
        P._merge_and_write_feed(feed, "b", _ev("b", 2), "t1")
    monkeypatch.undo()
    assert feed.read_text(encoding="utf-8") == vorher
    assert len(json.loads(vorher)["opportunities"]) == 3


def test_a1_feed_komplett_abbruch_laesst_alte_datei_ganz(tmp_path, monkeypatch):
    feed = tmp_path / "opportunities.json"
    P._write_feed_cache(feed, _ev("a", 3), "t0")
    vorher = feed.read_text(encoding="utf-8")
    _halb_schreiben_dann_fehler(monkeypatch)
    with pytest.raises(OSError):
        P._write_feed_cache(feed, _ev("b", 2), "t1")
    monkeypatch.undo()
    assert json.loads(feed.read_text(encoding="utf-8"))["computed_at"] == "t0"


def test_a1_kalender_abbruch_laesst_alte_datei_ganz(tmp_path, monkeypatch):
    cal = tmp_path / "calendar.json"
    P._write_calendar_cache(cal, _ev("a", 3), {"a": "t0"}, "t0")
    vorher = cal.read_text(encoding="utf-8")
    _halb_schreiben_dann_fehler(monkeypatch)
    with pytest.raises(OSError):
        P._write_calendar_cache(cal, _ev("b", 2), {"b": "t1"}, "t1")
    monkeypatch.undo()
    assert json.loads(cal.read_text(encoding="utf-8"))["computed_at"] == "t0"
    assert cal.read_text(encoding="utf-8") == vorher


def test_a2_gleichzeitiges_einmischen_verliert_keine_termine(tmp_path, monkeypatch):
    """Lauf A liest die Datei und wird angehalten; währenddessen startet Lauf B. Danach
    müssen die Termine BEIDER Orte in der Datei stehen. Ohne Sperre überschreibt A das
    Ergebnis von B. Alle Wartezeiten sind begrenzt, der Test kann nicht hängen bleiben."""
    feed = tmp_path / "opportunities.json"
    P._merge_and_write_feed(feed, "alt", _ev("alt", 1), "t0")

    a_hat_gelesen = threading.Event()
    a_darf_weiter = threading.Event()
    original = pathlib.Path.read_text

    def lesen(self, *a, **kw):
        text = original(self, *a, **kw)
        if self == feed and threading.current_thread().name == "lauf-a":
            a_hat_gelesen.set()
            a_darf_weiter.wait(timeout=2)
        return text

    monkeypatch.setattr(pathlib.Path, "read_text", lesen)
    ta = threading.Thread(target=P._merge_and_write_feed, name="lauf-a",
                          args=(feed, "a", _ev("a", 2), "t1"))
    tb = threading.Thread(target=P._merge_and_write_feed, name="lauf-b",
                          args=(feed, "b", _ev("b", 2), "t2"))
    ta.start()
    a_hat_gelesen.wait(timeout=2)
    tb.start()
    time.sleep(0.3)
    a_darf_weiter.set()
    ta.join(timeout=5)
    tb.join(timeout=5)
    monkeypatch.undo()

    ids = sorted({e["location_id"] for e in json.loads(feed.read_text(encoding="utf-8"))["opportunities"]})
    assert ids == ["a", "alt", "b"], f"Termine verloren gegangen: {ids}"
