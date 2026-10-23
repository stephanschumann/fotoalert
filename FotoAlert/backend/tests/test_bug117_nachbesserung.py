"""
BUG-117 Nachbesserung: (1) Wetterlauf startet zur Minute 7 statt zur vollen Stunde, (2) nach einem Lauf, den die
Notbremse beendet hat, wird genau EIN Wiederholungsversuch nach ca. 12 Minuten angesetzt.

Isolation wie in test_bug117.py: Attrappen für den Wetterdienst (kein Netzwerk), Wegwerf-Cache-Ordner,
der Planer wird durch eine Attrappe ersetzt (nichts wird wirklich eingeplant).
"""
import asyncio
from datetime import datetime, timedelta

import pytest

import main
from tests.test_bug117 import Attrappe, _feed, _err429, isoliert, attrappe  # noqa: F401  (Fixtures wiederverwendet)

pytestmark = [pytest.mark.offline, pytest.mark.regression]


class PlanerAttrappe:
    def __init__(self, running=True):
        self.running = running
        self.jobs = []        # (func, trigger, kwargs-dict)

    def add_job(self, func, trigger=None, **kw):
        self.jobs.append((func, trigger, kw))

    def start(self):
        self.running = True


@pytest.fixture
def planer(monkeypatch, isoliert):
    # 'isoliert' = Wegwerf-Cache-Ordner und frischer Tageszähler (wie in test_bug117.py), sonst hängt das Ergebnis
    # vom Zustand auf der Platte ab (lokal anders als in der CI).
    p = PlanerAttrappe()
    monkeypatch.setattr(main, "scheduler", p)
    monkeypatch.setattr(main, "_weather_retry_verbraucht", False)
    return p


def _retry_jobs(planer):
    return [j for j in planer.jobs if j[1] == "date"]


def _berlin(h, m):
    # Immer der HEUTIGE Berliner Tag: Die Test-Termine (_feed) liegen relativ zur echten Uhr; ein festes Datum
    # rückte sie mit der Zeit aus dem Vorhersagefenster (Test lief nur am Tag der Erstellung).
    from zoneinfo import ZoneInfo
    heute = datetime.now(ZoneInfo("Europe/Berlin")).date()
    return datetime(heute.year, heute.month, heute.day, h, m, 0, tzinfo=ZoneInfo("Europe/Berlin"))


def _feste_uhr(monkeypatch, jetzt):
    """Setzt datetime.now(...) in main auf einen festen Zeitpunkt."""
    class Uhr(datetime):
        @classmethod
        def now(cls, tz=None):
            return jetzt.astimezone(tz) if tz else jetzt.replace(tzinfo=None)
    monkeypatch.setattr(main, "datetime", Uhr)


def test_planer_eintrag_wetterlauf_startet_minute_7_alle_3_stunden():
    """Der Planer-Eintrag für den Wetterlauf nutzt Minute 7 (nicht 0), alle 3 Stunden, Berliner Zeit."""
    p = PlanerAttrappe(running=False)
    orig = main.scheduler
    main.scheduler = p
    try:
        main._startup_setup_scheduler("feed")
    finally:
        main.scheduler = orig
    eintrag = [j for j in p.jobs if j[0] is main._weather_overlay]
    assert len(eintrag) == 1
    _, trigger, kw = eintrag[0]
    assert trigger == "cron" and kw["minute"] == 7 and kw["hour"] == "*/3", kw
    assert main.WEATHER_CRON_MINUTE == 7
    karte = [j for j in p.jobs if j[0] is main._build_weather_map][0]
    assert karte[2]["minute"] == 27, "Karten-Overlay bei Minute 27 (20 Minuten nach dem Wetterlauf)"


def test_naechster_planlauf_ist_minute_7_und_stunde_durch_3_teilbar():
    assert main._naechster_planlauf(_berlin(21, 30)).strftime("%H:%M") == "00:07" or \
        main._naechster_planlauf(_berlin(21, 30)).hour == 0
    assert main._naechster_planlauf(_berlin(9, 6)).strftime("%H:%M") == "09:07"
    assert main._naechster_planlauf(_berlin(9, 7)).strftime("%H:%M") == "12:07"
    assert main._naechster_planlauf(_berlin(10, 30)).strftime("%H:%M") == "12:07"


def test_konstante_wartezeit_ist_720_sekunden():
    assert main.WEATHER_NOTBREMSE_RETRY_DELAY_S == 720


def test_retry_wird_nach_notbremse_angesetzt(attrappe, planer, monkeypatch):
    """Notbremse -> genau ein einmaliger Planer-Eintrag, ca. 12 Minuten später, Auslöser notbremse-retry."""
    _feste_uhr(monkeypatch, _berlin(10, 30))     # nächster Plan-Lauf 12:07 = 97 Min entfernt
    attrappe.regel = lambda art, lat, lon: _err429()
    main._feed_cache = _feed(40)
    asyncio.run(main._weather_overlay())
    jobs = _retry_jobs(planer)
    assert len(jobs) == 1, planer.jobs
    func, _, kw = jobs[0]
    assert func is main._weather_overlay
    assert kw["kwargs"] == {"triggered_by": "notbremse-retry"}
    assert kw["run_date"] == _berlin(10, 30) + timedelta(seconds=720)


def test_kein_retry_ohne_notbremse(attrappe, planer, monkeypatch):
    _feste_uhr(monkeypatch, _berlin(10, 30))
    main._feed_cache = _feed(10)
    asyncio.run(main._weather_overlay())
    assert _retry_jobs(planer) == []


def test_retry_nur_einmal_auch_wenn_retry_wieder_notbremse(attrappe, planer, monkeypatch):
    """Der Retry-Lauf endet wieder mit Notbremse: kein zweiter Retry; erst der nächste planmäßige Lauf (cron) darf
    wieder einen ansetzen."""
    _feste_uhr(monkeypatch, _berlin(10, 30))
    attrappe.regel = lambda art, lat, lon: _err429()
    main._feed_cache = _feed(40)
    asyncio.run(main._weather_overlay(triggered_by="cron"))
    assert len(_retry_jobs(planer)) == 1
    asyncio.run(main._weather_overlay(triggered_by="notbremse-retry"))
    assert len(_retry_jobs(planer)) == 1, "Retry nach Retry darf es nicht geben"
    main._feed_cache = _feed(40)
    asyncio.run(main._weather_overlay(triggered_by="nachlauf"))
    assert len(_retry_jobs(planer)) == 1, "auch kein Retry über einen anderen Auslöser im selben Zyklus"
    asyncio.run(main._weather_overlay(triggered_by="cron"))
    assert len(_retry_jobs(planer)) == 2, "nächster planmäßiger Lauf darf wieder einen Retry bekommen"


def test_kein_retry_wenn_planlauf_innerhalb_20_minuten(attrappe, planer, monkeypatch):
    _feste_uhr(monkeypatch, _berlin(11, 50))     # nächster Plan-Lauf 12:07 = 17 Min entfernt
    attrappe.regel = lambda art, lat, lon: _err429()
    main._feed_cache = _feed(40)
    asyncio.run(main._weather_overlay())
    assert _retry_jobs(planer) == []
    assert "12:07" in (main._job_status["weather"]["last_error"] or ""), main._job_status["weather"]["last_error"]


def test_retry_bei_genau_ueber_20_minuten_bis_planlauf(attrappe, planer, monkeypatch):
    _feste_uhr(monkeypatch, _berlin(11, 46))     # 21 Min bis 12:07
    attrappe.regel = lambda art, lat, lon: _err429()
    main._feed_cache = _feed(40)
    asyncio.run(main._weather_overlay())
    assert len(_retry_jobs(planer)) == 1


def test_kein_retry_wenn_planer_nicht_laeuft(attrappe, monkeypatch):
    """Test-/Offline-Modus ohne laufenden Planer: nichts wird angesetzt, nichts bricht ab."""
    p = PlanerAttrappe(running=False)
    monkeypatch.setattr(main, "scheduler", p)
    monkeypatch.setattr(main, "_weather_retry_verbraucht", False)
    attrappe.regel = lambda art, lat, lon: _err429()
    main._feed_cache = _feed(40)
    asyncio.run(main._weather_overlay())
    assert p.jobs == []


def test_retry_laeuft_nie_parallel_zu_laufendem_lauf(attrappe, planer, monkeypatch):
    """Kommt der Retry-Auslöser, während ein Lauf läuft, startet er keinen zweiten Lauf (Lauf-Sperre)."""
    gleichzeitig = {"jetzt": 0, "max": 0}
    original = main._weather_overlay_lauf

    async def zaehlend(triggered_by="cron"):
        gleichzeitig["jetzt"] += 1
        gleichzeitig["max"] = max(gleichzeitig["max"], gleichzeitig["jetzt"])
        try:
            return await original(triggered_by)
        finally:
            gleichzeitig["jetzt"] -= 1

    monkeypatch.setattr(main, "_weather_overlay_lauf", zaehlend)
    attrappe.dauer = 0.02

    async def szenario():
        main._feed_cache = _feed(30)
        l1 = asyncio.ensure_future(main._weather_overlay("cron"))
        await asyncio.sleep(0.05)
        await main._weather_overlay(triggered_by="notbremse-retry")   # kommt mitten im Lauf
        await l1

    asyncio.run(szenario())
    assert gleichzeitig["max"] == 1


def test_statustext_nennt_retry_zeit_wenn_vorgesehen(attrappe, planer, monkeypatch):
    _feste_uhr(monkeypatch, _berlin(10, 30))
    attrappe.regel = lambda art, lat, lon: _err429()
    main._feed_cache = _feed(40)
    asyncio.run(main._weather_overlay())
    text = main._job_status["weather"]["last_error"] or ""
    assert "Nächster Versuch ca. 10:42 Uhr" in text and "Wiederholungsversuch" in text, text


def test_statustext_nennt_naechsten_planlauf_wenn_kein_retry(attrappe, planer, monkeypatch):
    _feste_uhr(monkeypatch, _berlin(10, 30))
    attrappe.regel = lambda art, lat, lon: _err429()
    main._feed_cache = _feed(40)
    asyncio.run(main._weather_overlay(triggered_by="notbremse-retry"))
    text = main._job_status["weather"]["last_error"] or ""
    assert "Nächster Versuch ca. 12:07 Uhr" in text and "Wiederholungsversuch" not in text, text


def test_nachlauf_mechanismus_bleibt_unveraendert(attrappe, planer, monkeypatch):
    """Ein während des Laufs vorgemerkter Nachlauf läuft weiterhin nacheinander (Schutz für Nachfund 1)."""
    laeufe = {"n": 0}
    original = main._weather_overlay_lauf

    async def zaehlend(triggered_by="cron"):
        laeufe["n"] += 1
        return await original(triggered_by)

    monkeypatch.setattr(main, "_weather_overlay_lauf", zaehlend)
    attrappe.dauer = 0.02

    async def szenario():
        main._feed_cache = _feed(10)
        l1 = asyncio.ensure_future(main._weather_overlay("cron"))
        await asyncio.sleep(0.05)
        await main._weather_overlay()
        await l1

    asyncio.run(szenario())
    assert laeufe["n"] == 2
