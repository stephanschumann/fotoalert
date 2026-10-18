"""
BUG-117 Nachfunde (Prüfbericht 2026-10-18, mittlere Funde 1 und 2). Tests VOR der Korrektur geschrieben.

Fund 1: Wird der Feed neu geladen, während ein Wetterlauf von der Notbremse beendet wird, bekam der neue
        Feed bis zum nächsten 3-Stunden-Takt kein Wetter (der vorgemerkte Nachlauf entfiel).
Fund 2: Der Scout-Verbrauch (Anfragen des Entdecken-Scouts) wurde bei einem zweiten Buchen ohne neue Anfragen
        ein zweites Mal auf den Tagesstand gebucht (Zähler wurde nur bei Pipeline-Start zurückgesetzt).

Isolation wie in test_bug117.py: Attrappen, kein Netzwerk, Wegwerf-Cache-Ordner.
"""
import asyncio

import pytest

import main
from data import wetter_speicher
from discover import pipeline_base
from tests.test_bug117 import Attrappe, _feed, _err429, isoliert, attrappe  # noqa: F401  (Fixtures wiederverwendet)

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def test_fund1_neuer_feed_bekommt_nach_notbremse_trotzdem_sein_wetter(attrappe, monkeypatch):
    """Fund 1 (BUG-117): Lauf 1 wird von der Notbremse beendet (Dienst lehnt alles ab). Währenddessen wird ein
    neuer Feed geladen und ein zweiter Auslöser (Vorberechnung) gemeldet. Der Dienst erholt sich danach. Soll:
    der neue Feed bekommt sein Wetter trotzdem (ein Nachlauf), und es läuft nie mehr als ein Lauf gleichzeitig."""
    phase = {"laeufe": 0, "gleichzeitig": 0, "max": 0}
    original = main._weather_overlay_lauf

    async def zaehlend(triggered_by="cron"):
        phase["laeufe"] += 1
        phase["gleichzeitig"] += 1
        phase["max"] = max(phase["max"], phase["gleichzeitig"])
        try:
            return await original(triggered_by)
        finally:
            phase["gleichzeitig"] -= 1

    monkeypatch.setattr(main, "_weather_overlay_lauf", zaehlend)
    attrappe.dauer = 0.02
    attrappe.regel = lambda art, lat, lon: _err429() if phase["laeufe"] == 1 else None

    async def szenario():
        main._feed_cache = _feed(60)
        lauf1 = asyncio.ensure_future(main._weather_overlay("cron"))
        await asyncio.sleep(0.05)                 # Lauf 1 ist mitten im Gange
        main._feed_cache = _feed(60)              # Vorberechnung lädt den Feed neu (ohne Wetter)
        await main._weather_overlay()             # zweiter Auslöser: wird nur vorgemerkt
        await lauf1

    asyncio.run(szenario())
    assert phase["max"] == 1, "AK-6 verletzt: %d Läufe gleichzeitig" % phase["max"]
    ohne = [e for e in main._feed_cache if not e.get("weather_score")]
    assert not ohne, "%d von %d Terminen des neuen Feeds ohne Wetter (Nachlauf entfallen)" % (len(ohne), len(main._feed_cache))


def test_fund2_scout_verbrauch_wird_genau_einmal_gebucht(isoliert, monkeypatch):
    """Fund 2 (BUG-117): 10 Scout-Anfragen werden gebucht. Wird danach OHNE neue Anfragen noch einmal gebucht
    (z. B. nächster Durchgang bricht vor dem Zähler-Zurücksetzen ab), darf der Tagesstand nicht weiter steigen.
    Neue Anfragen danach werden wieder gebucht (nichts geht verloren)."""
    monkeypatch.setattr(main, "_wetter_speicher_erlaubt", lambda: True)
    with pipeline_base._zaehler_lock:
        pipeline_base._zaehler["anfragen"] = 10
        pipeline_base._zaehler["abgelehnt"] = 2

    def scout_stand():
        return wetter_speicher.tagesstand_lesen(isoliert).get("scout", {}).get("anfragen", 0)

    main._wetter_scout_buchen()
    assert scout_stand() == 10
    main._wetter_scout_buchen()
    assert scout_stand() == 10, "Doppelt gebucht: Tagesstand Scout steht auf %d statt 10" % scout_stand()
    with pipeline_base._zaehler_lock:
        pipeline_base._zaehler["anfragen"] += 3
    main._wetter_scout_buchen()
    assert scout_stand() == 13, "Neue Anfragen gingen verloren: Stand %d statt 13" % scout_stand()
    with pipeline_base._zaehler_lock:
        pipeline_base._zaehler["anfragen"] = 0
        pipeline_base._zaehler["abgelehnt"] = 0
