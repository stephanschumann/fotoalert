"""US-141 (Entscheidung vom 2026-10-17) — Im Live-Modus wird beim Nachladen eines Gebiets KEIN Kalender mitgerechnet.

Hintergrund: Live (FOTOALERT_ONDEMAND == "1") rechnet der Server /calendar selbst und liest calendar.json nicht; die
Datei ist dort sehr groß, das Einmischen bräuchte ein Vielfaches an Arbeitsspeicher. Deshalb:

  Live-Modus
    * der Rechenprozess wird ohne --mit-kalender gestartet (nur Chancen; das Wetter holt der Server wie immer);
    * calendar.json und der Kalender im Arbeitsspeicher bleiben byte-gleich / unverändert, kein Postfach wird übernommen;
    * im Menü gibt es keinen Kalender-Schritt (kalender_aktiv False, kalender_gesamt 0); der Lauf gilt nach Chancen + Wetter
      als fertig;
    * es wird kein offener Kalender gemerkt; ein von früher gemerkter offener Kalender löst nach einem Neustart
      keinen Nachholauf (--nur-kalender) aus, sondern wird verworfen (kein endloses Wiederaufnehmen);
    * Fortsetzen nach Neustart (Chancen offen) und Abbruch durch Ausschalten funktionieren wie bisher.
  Lokal (ohne Live-Modus)
    * unverändert: --mit-kalender, Kalender-Schritt im Menü, offener Kalender wird gemerkt.

Alles offline (Prozess-Spion, Wegwerf-Dateien); die echte calendar.json wird nie angefasst. Python-3.9-kompatibel.
"""
from __future__ import annotations

import asyncio
import json
import threading

import pytest

from us141_adapter import (  # noqa: F401  (Fixtures)
    ORTE, als_host, host_schaltet_region, ort_id, termin, warte_bis, welt, welt_z,
)
from test_us141_nachladen import _starte_server_neu, nachladen  # noqa: F401
from test_us141_kalender_nachladen import (  # noqa: F401
    BB, POSTFACH, WARTEZEIT, _fort_schreiben, _info, _kal, _kalender_datei, _zeit, kalender_server,
)

pytestmark = [pytest.mark.api, pytest.mark.regression]


def _text(spion, nr: int = 0) -> str:
    return " ".join(str(a) for a in spion.starts[nr])


def _live(monkeypatch):
    monkeypatch.setenv("FOTOALERT_ONDEMAND", "1")


def _lokal(monkeypatch):
    monkeypatch.delenv("FOTOALERT_ONDEMAND", raising=False)


# ── Live: Einschalten ────────────────────────────────────────────────────────

def test_live_einschalten_startet_prozess_ohne_kalender_und_merkt_keinen_kalender(client, kalender_server, monkeypatch):
    import main
    _live(monkeypatch)
    s = kalender_server.spion
    kal_datei = _kalender_datei(kalender_server.welt)
    roh = kal_datei.read_bytes()
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    kalender_server.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    assert len(s.starts) == 1
    text = _text(s)
    assert "--location-ids" in text and "--feed-only" in text and all(i in text for i in BB)
    assert "--mit-kalender" not in text and "--nur-kalender" not in text, text
    assert main._store.lade_nachladen_kalender() == set(), "live darf kein offener Kalender gemerkt werden"
    assert main._store.lade_nachladen() == BB
    info = _info(client)
    assert info["kalender_aktiv"] is False and info["kalender_gesamt"] == 0 and info["kalender_bereit"] == 0
    s.sperre.set()
    assert warte_bis(lambda: _info(client)["aktiv"] is False and s.beendet >= 1, WARTEZEIT)
    assert kal_datei.read_bytes() == roh, "calendar.json wurde im Live-Modus verändert"


def test_live_lauf_ist_nach_chancen_und_wetter_fertig_ohne_kalender_schritt(client, kalender_server, monkeypatch):
    """Fortschritt: Chancen -> Wetter, nie ein Kalender-Schritt; nach dem Ende des Prozesses ist alles leer, kein Fehler,
    der Kalender im Arbeitsspeicher und calendar.json sind unverändert, ein (fremdes) Postfach wird nicht übernommen."""
    import main
    _live(monkeypatch)
    welt = kalender_server.welt
    s = kalender_server.spion
    kal_datei = _kalender_datei(welt)
    roh = kal_datei.read_bytes()
    andere = [termin(ort_id("berlin1"), zeit=_zeit(2), nr=1)]
    welt.setze_kalender(andere)
    vorher_cache = list(main._calendar_cache)
    # ein Postfach, das ein Kalender-Schritt hinterlassen hätte: es darf nicht übernommen werden
    (kalender_server.cache / POSTFACH).write_text(
        json.dumps({"pid": 4711, "computed_at": "x", "location_ids": sorted(BB)}) + "\n"
        + "\n".join(json.dumps({"location_id": i, "events": [termin(i, zeit=_zeit(3), nr=3, typ="NEU")]}) for i in sorted(BB)) + "\n",
        encoding="utf-8")
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    kalender_server.scharf()
    als_host(client)
    assert client.put("/areas/Deutschland/Brandenburg", json={"enabled": True}).status_code == 200
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    _fort_schreiben(main, fertig=sorted(BB), feed_fertig=True)
    assert warte_bis(lambda: _info(client)["wetter_bereit"] == 2, WARTEZEIT), _info(client)
    info = _info(client)
    assert info["aktiv"] is True and info["phase"] == "wetter"
    assert info["kalender_aktiv"] is False and info["kalender_gesamt"] == 0
    s.sperre.set()
    assert warte_bis(lambda: _info(client)["aktiv"] is False and s.beendet >= 1, WARTEZEIT)
    assert _info(client)["fehler"] in (None, "")
    assert main._store.lade_nachladen_kalender() == set() and main._store.lade_nachladen() == set()
    assert main._calendar_cache == vorher_cache, "der Kalender im Arbeitsspeicher wurde im Live-Modus verändert"
    assert kal_datei.read_bytes() == roh, "calendar.json wurde im Live-Modus verändert"
    assert not (main._pausierte_ort_ids() & BB)


def test_live_prozessende_mit_fehler_nach_den_chancen_meldet_keinen_kalenderfehler(client, kalender_server, monkeypatch):
    import main
    _live(monkeypatch)
    s = kalender_server.spion
    s.rc = 137
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    kalender_server.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    _fort_schreiben(main, fertig=sorted(BB), feed_fertig=True)
    assert warte_bis(lambda: _info(client)["wetter_bereit"] == 2, WARTEZEIT)
    s.sperre.set()
    assert warte_bis(lambda: _info(client)["aktiv"] is False and s.beendet >= 1, WARTEZEIT)
    assert "Kalender" not in (_info(client)["fehler"] or "")
    assert main._store.lade_nachladen_kalender() == set()


# ── Live: Abbruch ────────────────────────────────────────────────────────────

def test_live_ausschalten_waehrend_des_nachladens_beendet_den_prozess(client, kalender_server, monkeypatch):
    import main
    _live(monkeypatch)
    s = kalender_server.spion
    kal_datei = _kalender_datei(kalender_server.welt)
    roh = kal_datei.read_bytes()
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    kalender_server.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert warte_bis(lambda: s.abgebrochen >= 1 and s.aktiv == 0, WARTEZEIT), "Prozess lief weiter"
    assert warte_bis(lambda: _info(client)["aktiv"] is False, WARTEZEIT)
    assert main._store.lade_nachladen_kalender() == set() and main._store.lade_nachladen() == set()
    assert not (main._recompute_pending & BB)
    assert kal_datei.read_bytes() == roh


# ── Live: Neustart ───────────────────────────────────────────────────────────

def test_live_neustart_mit_altem_offenen_kalender_startet_keinen_nachholauf_und_verwirft_ihn(client, welt_z, monkeypatch):
    """Zustand von früher (lokaler Lauf): Cottbus steht als „Kalender offen“, seine Chancen stehen. Live startet nach dem
    Start KEIN Prozess (kein --nur-kalender), der gemerkte Zustand ist danach weg — ein zweiter Start findet nichts mehr."""
    from us141_adapter import ProzessSpion
    import main
    _live(monkeypatch)
    s = ProzessSpion()
    s.sperre = threading.Event()
    welt_z.setze_feed(welt_z.termine_fuer(list(ORTE)))
    welt_z.store.merke_nachladen_kalender([ort_id("cottbus"), ort_id("potsdam")])
    monkeypatch.setattr(asyncio, "create_subprocess_exec", s.fake_exec)

    def _pruefen():
        assert s.starts == [], "live wurde ein Prozess gestartet: %r" % (s.starts,)

    try:
        _starte_server_neu(welt_z, monkeypatch, nachlaufzeit_s=1.0, pruefe=_pruefen)
    finally:
        s.sperre.set()
    assert welt_z.store.lade_nachladen_kalender() == set(), "der alte offene Kalender wurde nicht verworfen"
    assert s.starts == []


def test_live_neustart_mit_offenen_chancen_setzt_fort_ohne_kalender(client, welt_z, monkeypatch):
    from us141_adapter import ProzessSpion
    _live(monkeypatch)
    s = ProzessSpion()
    s.sperre = threading.Event()
    welt_z.setze_feed(welt_z.termine_fuer([k for k in ORTE if k != "cottbus"]))
    welt_z.store.merke_nachladen([ort_id("cottbus")])
    welt_z.store.merke_nachladen_kalender([ort_id("cottbus")])      # Rest eines früheren lokalen Laufs
    monkeypatch.setattr(asyncio, "create_subprocess_exec", s.fake_exec)

    def _pruefen():
        assert len(s.starts) == 1, s.starts
        text = _text(s)
        assert "--feed-only" in text and ort_id("cottbus") in text
        assert "--mit-kalender" not in text and "--nur-kalender" not in text, text

    try:
        _starte_server_neu(welt_z, monkeypatch, nachlaufzeit_s=1.0, pruefe=_pruefen)
    finally:
        s.sperre.set()
    assert welt_z.store.lade_nachladen_kalender() == set()


def test_live_kalender_modus_direkt_angestossen_startet_nichts(client, welt_z, monkeypatch):
    """Selbst ein direkter Aufruf mit modus="kalender" startet live keinen Prozess und merkt nichts."""
    from us141_adapter import ProzessSpion
    import main
    _live(monkeypatch)
    s = ProzessSpion()
    monkeypatch.setattr(main, "_NO_BACKGROUND", False)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", s.fake_exec)
    welt_z.store.merke_nachladen_kalender([ort_id("cottbus")])

    async def _lauf():
        main._nachladen_anstossen([ort_id("cottbus")], quelle="Test", modus="kalender")
        await asyncio.sleep(0.3)

    asyncio.new_event_loop().run_until_complete(_lauf())
    assert s.starts == []
    assert main._store.lade_nachladen_kalender() == set()


# ── Lokal (ohne Live-Modus): unverändert ─────────────────────────────────────

@pytest.mark.parametrize("wert", [None, "0", ""])
def test_lokal_einschalten_rechnet_den_kalender_mit(client, kalender_server, monkeypatch, wert):
    import main
    if wert is None:
        _lokal(monkeypatch)
    else:
        monkeypatch.setenv("FOTOALERT_ONDEMAND", wert)
    s = kalender_server.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    kalender_server.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    text = _text(s)
    assert "--feed-only" in text and "--mit-kalender" in text and all(i in text for i in BB)
    assert main._store.lade_nachladen_kalender() == BB
    _fort_schreiben(main, fertig=sorted(BB), feed_fertig=True, kalender=_kal("rechnet"))
    assert warte_bis(lambda: _info(client)["kalender_aktiv"] is True, WARTEZEIT), _info(client)
    assert _info(client)["kalender_gesamt"] == 2
    s.sperre.set()
    assert warte_bis(lambda: _info(client)["aktiv"] is False and s.beendet >= 1, WARTEZEIT)


def test_lokal_neustart_holt_offenen_kalender_nach(client, welt_z, monkeypatch):
    from us141_adapter import ProzessSpion
    _lokal(monkeypatch)
    s = ProzessSpion()
    s.sperre = threading.Event()
    welt_z.setze_feed(welt_z.termine_fuer(list(ORTE)))
    welt_z.store.merke_nachladen_kalender([ort_id("cottbus")])
    monkeypatch.setattr(asyncio, "create_subprocess_exec", s.fake_exec)

    def _pruefen():
        assert len(s.starts) == 1, s.starts
        text = _text(s)
        assert "--nur-kalender" in text and ort_id("cottbus") in text and "--feed-only" not in text

    try:
        _starte_server_neu(welt_z, monkeypatch, nachlaufzeit_s=1.0, pruefe=_pruefen)
    finally:
        s.sperre.set()
