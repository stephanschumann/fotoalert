"""TASK-106 — Sichtachsen-Lauf (`_run_sightline_refresh`) darf den Server am Ende
nicht anhalten (Test-first, geschrieben in der Analyse-Phase 2026-10-09).

Hintergrund: Am Ende des manuell angestoßenen Sichtachsen-Checks ruft der Lauf
`_load_caches()` direkt im Hauptstrang des Servers auf. Das liest u. a. die sehr große
calendar.json (echt ~1,1 GB) ein und hält den Server so lange an. Ein bloßer Umzug in
einen Nebenstrang (asyncio.to_thread) genügt dafür NICHT (BUG-113-Messung: 1,31 -> 1,06 s,
`json.loads` hält den GIL) — empfohlener Weg (Option B): am Ende nur noch den kleinen Feed
im Nebenstrang neu laden, die große Kalenderdatei NICHT erneut einlesen.

Abgedeckt (Akzeptanzkriterien aus dem Ticket-Block "Analyse TASK-106"):
- AK1  Server steht beim Neuladen am Ende nie länger als 0,5 s am Stück.
- AK2  Kalender wird am Ende nicht erneut komplett eingelesen und bleibt im Speicher.
- AK3  Feed wird weiterhin neu geladen — aber nicht im Hauptstrang.
- AK4  Job endet "done", die Sperre gegen Doppelstart gilt bis zum Schluss und wird frei.
- AK5  Defekte Feed-Datei: alter Feed bleibt, Server bleibt bedienbar, Job hängt nicht.
- AK6  Unerwarteter Fehler beim Neuladen: neutrale Meldung im Job-Status, Details im Log.
- AK7  Gleichzeitige Leser sehen nie eine halbe Feed-Liste (nur alt oder komplett neu).

Alle Tests laufen offline: keine echten Cache-Dateien (Pfade zeigen auf tmp_path), kein
Netz, keine Locations. Python-3.9-kompatibel; asyncio-Objekte werden nur innerhalb
laufender Event-Loops erzeugt.
"""
import asyncio
import json
import logging
import threading
import time
import uuid

import pytest

import main

pytestmark = [pytest.mark.offline, pytest.mark.regression]

MAX_STILLSTAND_S = 0.5


def _idle_job() -> dict:
    return {
        "status": "idle", "last_run": None, "last_error": None,
        "duration_s": None, "error_class": None, "spec": None,
    }


@pytest.fixture
def lauf(monkeypatch, tmp_path):
    """Gemeinsame Vorbereitung: keine Locations (keine externen Aufrufe, kein Sleep),
    Cache-Pfade auf leeres tmp_path (nie die echten Dateien), Job-Status sauber."""
    monkeypatch.setattr(main, "LOCATIONS", [])
    monkeypatch.setattr(main, "_load_qa_values", lambda: None)
    monkeypatch.setattr(main, "_CAL_CACHE", tmp_path / "calendar.json")
    monkeypatch.setattr(main, "_OPP_CACHE", tmp_path / "opportunities.json")
    monkeypatch.setattr(main, "_sightline_refresh_running", False)
    monkeypatch.setitem(main._job_status, "sightlines", _idle_job())
    return tmp_path


async def _messe_stillstand(arbeit) -> float:
    """Ticker alle 20 ms; Rückgabe = längster Stillstand des Event-Loops."""
    tick = 0.02
    luecken = []
    stop = asyncio.Event()

    async def ticker():
        last = time.perf_counter()
        while not stop.is_set():
            await asyncio.sleep(tick)
            now = time.perf_counter()
            luecken.append(now - last - tick)
            last = now

    t = asyncio.create_task(ticker())
    await asyncio.sleep(0.1)
    try:
        await arbeit()
    finally:
        stop.set()
        await t
    return max(luecken) if luecken else 0.0


class _Spion:
    """Ersetzt einen Lader; merkt sich Aufrufe, Thread und Sperrzustand."""

    def __init__(self, dauer_s: float = 0.0, fehler: Exception = None):
        self.dauer_s = dauer_s
        self.fehler = fehler
        self.aufrufe = []   # (thread_id, sperre_aktiv)

    def __call__(self, *a, **k):
        self.aufrufe.append((threading.get_ident(), main._sightline_refresh_running))
        if self.dauer_s:
            time.sleep(self.dauer_s)   # gibt den GIL frei, wie echtes Datei-Lesen
        if self.fehler is not None:
            raise self.fehler
        return True


def _spione(monkeypatch, feed_dauer_s=0.0, feed_fehler=None):
    feed = _Spion(feed_dauer_s, feed_fehler)
    kal = _Spion()
    monkeypatch.setattr(main, "_load_feed_cache", feed)
    monkeypatch.setattr(main, "_load_calendar_cache", kal)
    return feed, kal


# AK1 ------------------------------------------------------------------------

def test_ak1_neuladen_am_ende_haelt_server_nicht_an(lauf, monkeypatch):
    """Ein 0,6 s langes Einlesen (Platzhalter für den echten Feed) darf den
    Event-Loop nicht am Stück anhalten (erlaubt: 0,5 s). Rot gegen den Ist-Stand,
    weil `_load_caches()` dort direkt im Hauptstrang läuft."""
    _spione(monkeypatch, feed_dauer_s=0.6)
    stillstand = asyncio.run(_messe_stillstand(main._run_sightline_refresh))
    assert stillstand <= MAX_STILLSTAND_S, (
        f"Sichtachsen-Lauf hielt den Server {stillstand:.2f} s am Stück an "
        f"(erlaubt: {MAX_STILLSTAND_S} s) — TASK-106 AK1 nicht erfüllt."
    )


# AK2 ------------------------------------------------------------------------

def test_ak2_kalender_wird_am_ende_nicht_erneut_eingelesen(lauf, monkeypatch):
    """Die große Kalenderdatei wird beim Sichtachsen-Lauf nicht neu gelesen; der
    Kalender im Arbeitsspeicher bleibt unverändert erhalten."""
    _, kal = _spione(monkeypatch)
    vorhanden = [{"location_id": "loc_a", "shoot_time": "2026-10-10T05:00:00+00:00",
                  "overall_score": 0.5}]
    monkeypatch.setattr(main, "_calendar_cache", vorhanden)
    asyncio.run(main._run_sightline_refresh())
    assert kal.aufrufe == [], "Kalenderdatei wurde beim Sichtachsen-Lauf erneut eingelesen"
    assert main._calendar_cache is vorhanden and len(main._calendar_cache) == 1


# AK3 ------------------------------------------------------------------------

def test_ak3_feed_wird_neu_geladen_aber_nicht_im_hauptstrang(lauf, monkeypatch):
    feed, _ = _spione(monkeypatch)
    loop_thread = {}

    async def lauf_und_merke():
        loop_thread["id"] = threading.get_ident()
        await main._run_sightline_refresh()

    asyncio.run(lauf_und_merke())
    assert len(feed.aufrufe) == 1, "Feed wurde nicht (genau einmal) neu geladen"
    assert feed.aufrufe[0][0] != loop_thread["id"], \
        "Feed-Neuladen lief im Hauptstrang des Servers statt im Nebenstrang"


# AK4 ------------------------------------------------------------------------

def test_ak4_job_endet_done_sperre_gilt_bis_zum_schluss_und_wird_frei(lauf, monkeypatch):
    feed, _ = _spione(monkeypatch)
    asyncio.run(main._run_sightline_refresh())
    assert main._job_status["sightlines"]["status"] == "done"
    assert feed.aufrufe[0][1] is True, "Sperre gegen Doppelstart galt beim Neuladen nicht mehr"
    assert main._sightline_refresh_running is False, "Sperre blieb nach dem Lauf hängen"


# AK5 ------------------------------------------------------------------------

def test_ak5_defekte_feed_datei_alter_stand_bleibt_job_haengt_nicht(lauf, monkeypatch):
    """Echter Feed-Lader gegen eine kaputte Datei in tmp_path: der bisherige Feed
    bleibt im Speicher, der Lauf endet sauber."""
    (lauf / "opportunities.json").write_text("{kaputt", encoding="utf-8")
    alt = [{"id": "alt_1", "shoot_time": "2026-10-10T05:00:00+00:00"}]
    monkeypatch.setattr(main, "_feed_cache", alt)
    monkeypatch.setattr(main, "_load_calendar_cache", _Spion())
    asyncio.run(main._run_sightline_refresh())
    assert main._feed_cache == alt, "alter Feed ging bei defekter Datei verloren"
    assert main._job_status["sightlines"]["status"] == "done"
    assert main._sightline_refresh_running is False


# AK6 ------------------------------------------------------------------------

def test_ak6_unerwarteter_fehler_neutrale_meldung_details_im_log(lauf, monkeypatch, caplog):
    sentinel = "SENTINEL_T106_%s /interner/pfad" % uuid.uuid4().hex[:8]
    _spione(monkeypatch, feed_fehler=RuntimeError(sentinel))
    with caplog.at_level(logging.ERROR, logger="main"):
        asyncio.run(main._run_sightline_refresh())
    status = main._job_status["sightlines"]
    assert status["status"] == "error"
    assert status["last_error"] and sentinel not in status["last_error"]
    assert sentinel in caplog.text
    assert main._sightline_refresh_running is False


# AK7 ------------------------------------------------------------------------

def test_ak7_gleichzeitige_leser_sehen_nie_eine_halbe_feed_liste(lauf, monkeypatch):
    """Echter Feed-Lader, 30 000 Termine in tmp_path. Ein Leser fragt während des
    Neuladens ständig die Länge ab: erlaubt sind nur 'alt' (3) oder 'komplett neu'."""
    n_neu = 30000
    neu = [{"id": "e%d" % i, "location_id": "x", "shoot_time": "2026-10-10T05:00:00+00:00",
            "subject_lat": 52.0, "subject_lon": 13.0, "sightline_status": "frei",
            "sightline_angle_deg": 1.0} for i in range(n_neu)]
    (lauf / "opportunities.json").write_text(
        json.dumps({"opportunities": neu, "computed_at": "2026-10-09T00:00:00+00:00"}),
        encoding="utf-8")
    monkeypatch.setattr(main, "_feed_cache", [{"id": "a%d" % i} for i in range(3)])
    monkeypatch.setattr(main, "_load_calendar_cache", _Spion())
    gesehen = set()

    async def arbeit():
        stop = asyncio.Event()

        async def leser():
            while not stop.is_set():
                gesehen.add(len(main._feed_cache))
                await asyncio.sleep(0)

        t = asyncio.create_task(leser())
        try:
            await main._run_sightline_refresh()
        finally:
            stop.set()
            await t

    asyncio.run(arbeit())
    assert gesehen <= {3, n_neu}, "Leser sah eine halbe Liste: %s" % sorted(gesehen)
    assert len(main._feed_cache) == n_neu
