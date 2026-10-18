"""US-141 — Refactor-Check, Befunde M1 und M2 (2026-10-15), behoben und abgesichert.

M1  Scheitert die Überwachung des Nachlade-Rechenprozesses mit einer anderen Ausnahme als „Abbruch“, wird der
    Rechenprozess jetzt sicher beendet (erst terminate, nach kurzer Wartezeit kill), BEVOR der Arbeiter weitermacht.
    Der Lauf zählt als fehlgeschlagen (Fehleranzeige im Menü wie bisher). Ein zweiter Prozess startet nie, solange
    der erste noch läuft.
M2  Beim Einschalten eines Gebiets wird die große Feed-Datei nicht mehr im Haupt-Thread der Ereignisschleife
    gelesen, sondern in einem Hintergrund-Thread; das Ergebnis der Umschaltung bleibt gleich.

Alles offline, ohne echte Rechenprozesse. Python-3.9-kompatibel.
"""
from __future__ import annotations

import asyncio
import json
import threading

import pytest

from us141_adapter import (  # noqa: F401  (welt/welt_z sind Fixtures)
    ORTE, ProzessSpion, host_schaltet_region, ort_id, pausierte_ids, warte_bis, welt, welt_z,
)

pytestmark = [pytest.mark.api, pytest.mark.regression]

BB = {ort_id("potsdam"), ort_id("cottbus")}


class _HaengenderProzess:
    """Ein Rechenprozess, der auf Wunsch „sanft“ (terminate) oder erst „hart“ (kill) endet."""

    def __init__(self, reagiert_auf_terminate=True):
        self.pid = 4711
        self.returncode = None
        self.reagiert_auf_terminate = reagiert_auf_terminate
        self.aufrufe = []

    def terminate(self):
        self.aufrufe.append("terminate")
        if self.reagiert_auf_terminate:
            self.returncode = -15

    def kill(self):
        self.aufrufe.append("kill")
        self.returncode = -9

    async def wait(self):
        # Abfrage statt asyncio.Event: ein Event außerhalb der laufenden Schleife anzulegen verhält sich in
        # Python 3.9 anders als ab 3.10
        while self.returncode is None:
            await asyncio.sleep(0.01)
        return self.returncode

    async def communicate(self):
        await self.wait()
        return b"", None


# ── M1: sicheres Beenden ─────────────────────────────────────────────────────

def test_m1_beenden_sanft_wenn_der_prozess_auf_terminate_reagiert():
    import main
    p = _HaengenderProzess(reagiert_auf_terminate=True)
    assert asyncio.run(main._prozess_sicher_beenden(p, 0.5)) is True
    assert p.aufrufe == ["terminate"] and p.returncode == -15


def test_m1_beenden_hart_wenn_terminate_nicht_hilft():
    import main
    p = _HaengenderProzess(reagiert_auf_terminate=False)
    assert asyncio.run(main._prozess_sicher_beenden(p, 0.1)) is True
    assert p.aufrufe == ["terminate", "kill"] and p.returncode == -9


def test_m1_beenden_laesst_fertigen_prozess_in_ruhe():
    import main
    p = _HaengenderProzess()
    p.returncode = 0
    assert asyncio.run(main._prozess_sicher_beenden(p, 0.1)) is True
    assert p.aufrufe == []
    assert asyncio.run(main._prozess_sicher_beenden(None, 0.1)) is True


def test_m1_beenden_wirft_nie_eine_ausnahme(caplog):
    import main

    class _Kaputt(_HaengenderProzess):
        def terminate(self):
            raise OSError("kaputt")

        def kill(self):
            raise OSError("auch kaputt")

        async def wait(self):
            await asyncio.sleep(10)

    assert asyncio.run(main._prozess_sicher_beenden(_Kaputt(), 0.05)) is False


def _vorbereiten_ueberwachung(monkeypatch, tmp_path, proc, gestartet):
    import main

    async def _start(*args, **kwargs):
        gestartet.append(list(args))
        return proc

    monkeypatch.setattr(main.asyncio, "create_subprocess_exec", _start)
    monkeypatch.setattr(main, "_NACHLADEN_FORTSCHRITT", tmp_path / "nachladen_fortschritt.json")
    monkeypatch.setattr(main, "NACHLADEN_ABFRAGE_S", 0.05)
    monkeypatch.setattr(main, "NACHLADEN_BEENDEN_WARTE_S", 0.2)


def test_m1_ausnahme_in_der_ueberwachung_beendet_den_prozess_vor_der_rueckkehr(monkeypatch, tmp_path):
    """Die Überwachung (Fortschritt lesen) scheitert mit einem Fehler, der kein Abbruch ist: Der Rechenprozess muss
    beendet sein, wenn die Funktion zurückkehrt, der Rückgabewert ist „fehlgeschlagen“ (nicht 0 und nicht -1)."""
    import main
    gestartet = []
    p = _HaengenderProzess(reagiert_auf_terminate=True)
    _vorbereiten_ueberwachung(monkeypatch, tmp_path, p, gestartet)

    def _kaputt(pid):
        raise RuntimeError("Fortschritt nicht lesbar (Test)")

    monkeypatch.setattr(main, "_nachladen_lies_fortschritt_voll", _kaputt)

    async def _lauf():
        rc = await main._nachladen_prozess(["a", "b"], "alles")
        return rc, p.returncode          # Zustand des Prozesses im Moment der Rückkehr

    rc, prozess_rc = asyncio.run(_lauf())
    assert len(gestartet) == 1
    assert rc not in (0, -1), "der Lauf muss als fehlgeschlagen zurückkommen, war %r" % rc
    assert prozess_rc is not None, "der Rechenprozess läuft nach der Rückkehr noch"
    assert "terminate" in p.aufrufe


def test_m1_hartnaeckiger_prozess_wird_hart_beendet(monkeypatch, tmp_path):
    import main
    gestartet = []
    p = _HaengenderProzess(reagiert_auf_terminate=False)
    _vorbereiten_ueberwachung(monkeypatch, tmp_path, p, gestartet)
    monkeypatch.setattr(main, "_nachladen_lies_fortschritt_voll", lambda pid: (_ for _ in ()).throw(ValueError("x")))

    async def _lauf():
        rc = await main._nachladen_prozess(["a"], "alles")
        return rc, p.returncode

    rc, prozess_rc = asyncio.run(_lauf())
    assert rc not in (0, -1)
    assert p.aufrufe == ["terminate", "kill"] and prozess_rc == -9


def test_m1_gescheiterte_chancenphase_bleibt_gueltig_wenn_der_feed_schon_fertig_war(monkeypatch, tmp_path):
    """Die Überwachung scheitert erst NACH „Chancen fertig“: das Ergebnis meldet feed_fertig (Chancen bleiben
    gültig, nur der Kalender fehlt) — wie beim Kalender-Fehler im Prozess selbst."""
    import main
    gestartet = []
    p = _HaengenderProzess(reagiert_auf_terminate=True)
    _vorbereiten_ueberwachung(monkeypatch, tmp_path, p, gestartet)
    aufrufe = {"n": 0}

    def _erst_gut_dann_kaputt(pid):
        aufrufe["n"] += 1
        if aufrufe["n"] == 1:
            return {"fertig": [], "feed_fertig": True}
        raise RuntimeError("kaputt (Test)")

    async def _kein_wetter(ids):
        return None

    monkeypatch.setattr(main, "_nachladen_lies_fortschritt_voll", _erst_gut_dann_kaputt)
    monkeypatch.setattr(main, "_nachladen_wetter", _kein_wetter)

    async def _lauf():
        rc = await main._nachladen_prozess(["a"], "alles")
        return rc, dict(main._nachladen_lauf.get("ergebnis") or {})

    rc, ergebnis = asyncio.run(_lauf())
    assert rc not in (0, -1)
    assert ergebnis.get("feed_fertig") is True


def test_m1_arbeiter_zeigt_den_fehler_wie_bisher_und_startet_keinen_zweiten_prozess_parallel(client, welt_z, monkeypatch):
    """Ende-zu-Ende: Einschalten einer Region, die Überwachung scheitert. Der Rechenprozess wird beendet
    (Spion zählt den Abbruch), nie laufen zwei Prozesse gleichzeitig, und das Menü zeigt „Nachladen fehlgeschlagen“."""
    import main

    async def _nichts(*a, **k):
        return None

    async def _wetter_fertig(*a, **k):
        return True

    monkeypatch.setattr(main, "_trigger_discover_debounced", lambda *a, **k: None)
    monkeypatch.setattr(main, "_refresh_discover", _nichts)
    monkeypatch.setattr(main, "_weather_overlay", _nichts)
    monkeypatch.setattr(main, "_weather_overlay_single", _wetter_fertig)
    monkeypatch.setattr(main, "_apply_calendar_delta", _nichts)
    monkeypatch.setattr(main, "NACHLADEN_ABFRAGE_S", 0.05)
    monkeypatch.setattr(main, "NACHLADEN_BEENDEN_WARTE_S", 0.5)

    spion = ProzessSpion()
    spion.sperre = threading.Event()        # der „Prozess“ hängt, bis ihn die Anwendung beendet
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)

    def _kaputt(pid):
        raise RuntimeError("Fortschritt nicht lesbar (Test)")

    monkeypatch.setattr(main, "_NO_BACKGROUND", False)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", spion.fake_exec)
    monkeypatch.setattr(main, "_nachladen_lies_fortschritt_voll", _kaputt)
    try:
        host_schaltet_region(client, "Deutschland", "Brandenburg", True)
        assert warte_bis(lambda: spion.abgebrochen >= 1, 8.0), "der Rechenprozess wurde nicht beendet"
        assert warte_bis(lambda: bool(main._nachladen_info().get("fehler")) or main._nachladen_worker is None, 8.0)
        assert warte_bis(lambda: main._nachladen_worker is None, 8.0)
        assert spion.max_aktiv == 1, "zwei Rechenprozesse gleichzeitig"
        assert spion.aktiv == 0
    finally:
        spion.sperre.set()
    assert not (pausierte_ids(client) & BB), "die Orte bleiben eingeschaltet"


# ── M2: Feed-Datei nicht im Haupt-Thread ─────────────────────────────────────

def test_m2_feed_datei_wird_beim_einschalten_im_hintergrund_thread_gelesen(client, welt_z, monkeypatch):
    """Beim Einschalten läuft das Lesen der Feed-Datei NICHT im Thread der Ereignisschleife; das Einarbeiten in den
    Speicher läuft dort. Beim Ausschalten wird die Datei gar nicht gelesen."""
    import main

    async def _nichts(*a, **k):
        return None

    monkeypatch.setattr(main, "_trigger_discover_debounced", lambda *a, **k: None)
    monkeypatch.setattr(main, "_refresh_discover", _nichts)
    monkeypatch.setattr(main, "_nachladen_anstossen", lambda *a, **k: None)
    thread_lesen, thread_einarbeiten, gelesen = [], [], []
    original_lesen = main._feed_datei_lesen
    original_nach = main._nach_gebietsaenderung

    def _lesen():
        thread_lesen.append(threading.get_ident())
        gelesen.append(1)
        return original_lesen()

    def _nach(vorher, feed_daten=None):
        thread_einarbeiten.append(threading.get_ident())
        return original_nach(vorher, feed_daten)

    monkeypatch.setattr(main, "_feed_datei_lesen", _lesen)
    monkeypatch.setattr(main, "_nach_gebietsaenderung", _nach)

    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert gelesen == [], "beim Ausschalten darf die Feed-Datei nicht gelesen werden"
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert len(thread_lesen) == 1 and len(thread_einarbeiten) == 2
    assert thread_lesen[0] != thread_einarbeiten[-1], "die Feed-Datei wurde im Thread der Ereignisschleife gelesen"


def test_m2_ergebnis_unveraendert_chancen_kommen_zurueck(client, welt_z, monkeypatch):
    """Verhalten wie vorher: Nach Aus und Ein stehen die Chancen der Region wieder im Speicher und in der Antwort."""
    import main

    async def _nichts(*a, **k):
        return None

    monkeypatch.setattr(main, "_trigger_discover_debounced", lambda *a, **k: None)
    monkeypatch.setattr(main, "_refresh_discover", _nichts)
    monkeypatch.setattr(main, "_nachladen_anstossen", lambda *a, **k: None)
    welt_z.setze_feed(welt_z.termine_fuer(list(ORTE.keys())))
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert not ({e["location_id"] for e in main._feed_cache} & BB)
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert BB <= {e["location_id"] for e in main._feed_cache}
    assert not (pausierte_ids(client) & BB)


def test_m2_feed_datei_lesen_fehlt_oder_kaputt(tmp_path, monkeypatch, caplog):
    import logging
    import main
    datei = tmp_path / "opportunities.json"
    monkeypatch.setattr(main, "_OPP_CACHE", datei)
    assert main._feed_datei_lesen() == {}                           # fehlt
    datei.write_text("{kaputt", encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        assert main._feed_datei_lesen() == {}
    assert any("nicht lesbar" in r.getMessage() for r in caplog.records)
    datei.write_text(json.dumps(["keine", "Liste erwartet"]), encoding="utf-8")
    assert main._feed_datei_lesen() == {}
    datei.write_text(json.dumps({"opportunities": []}), encoding="utf-8")
    assert main._feed_datei_lesen() == {"opportunities": []}


def test_m2_feed_wieder_einlesen_mit_uebergebenen_daten_liest_die_datei_nicht(tmp_path, monkeypatch):
    import main
    monkeypatch.setattr(main, "_OPP_CACHE", tmp_path / "gibt_es_nicht.json")
    monkeypatch.setattr(main, "_feed_cache", [])
    daten = {"opportunities": [{"id": "e1", "location_id": "a", "shoot_time": "2026-10-20T05:00:00+00:00"},
                               {"id": "e2", "location_id": "b", "shoot_time": "2026-10-20T05:00:00+00:00"}]}
    assert main._feed_wieder_einlesen({"a"}, daten) == 1
    assert [e["id"] for e in main._feed_cache] == ["e1"]
    assert main._feed_wieder_einlesen(set(), daten) == 0
