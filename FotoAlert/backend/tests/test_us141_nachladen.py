"""US-141 — Direktes Nachladen beim Einschalten, Abbruch beim Ausschalten, Fortsetzen nach Neustart.

Was diese Datei absichert (alles ohne Oberfläche, ohne echte Rechenprozesse, ohne Netz):
  * Einschalten eines Landes/einer Region startet SOFORT einen eigenen Nachladelauf (Entscheidung 2,
    Regel 3, AK-72) — nur für die Orte des eingeschalteten Gebiets, höchstens einer gleichzeitig,
    ein zweites Einschalten wird angehängt, ein laufender Großlauf blockiert ihn nicht.
  * Die Orte stehen sofort als „wird aktualisiert“ in der vorhandenen Liste der offenen Aufträge.
  * Schaltet der Host während des Nachladens wieder aus, wird das Ergebnis verworfen (AK-67).
  * Der Nachtlauf lässt ausgeschaltete Gebiete aus (Regel 1, AK-07).
  * Nach einem Neustart mitten im Nachladen wird für aktive Orte OHNE Chancen fortgesetzt, andere nicht
    (AK-61); der gespeicherte Schalterzustand gilt nach dem Start (AK-71).

So wird „ein Rechenprozess“ beobachtet: ein Spion ersetzt den Prozessstart (asyncio.create_subprocess_exec)
und merkt sich jeden Start von precompute.py mit seinen Argumenten (siehe us141_adapter.ProzessSpion).
Welche Argumente die Umsetzung übergibt, steht nicht im Ticket — die Tests prüfen nur, WELCHE Orte
in den gestarteten Prozessen vorkommen, nicht in welcher Schreibweise.

Annahmen (gehören ins Ready-for-Dev-Gate, siehe Bericht):
  A1 Die Umsetzung startet den Nachladelauf wie alle bisherigen Läufe über asyncio.create_subprocess_exec
     und übergibt die Ort-IDs auf der Kommandozeile (Ticket: „gebündelt in einem Rechenprozess für alle Orte
     der Region, braucht eine Erweiterung ‚mehrere Orte pro Aufruf‘“).
  A2 „wird aktualisiert“ = die vorhandene Liste GET /recompute-status (Ticket: „vorhanden: main.py Z. 4398“).
  A3 Wie bei allen bisherigen Hintergrundläufen gilt FOTOALERT_NO_BACKGROUND=1 als „kein Lauf“; die Tests
     schalten das für die Dauer des Nachladens aus.
  A4 Das Fortsetzen nach Neustart passiert in startup() (Ticket: „Beim Start aktive Orte ohne Chancen erkennen“).
Python-3.9-kompatibel.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import threading

import pytest

from us141_adapter import (  # noqa: F401  (welt/welt_z sind Fixtures)
    ORTE, ProzessSpion, als_host, host_schaltet_land, host_schaltet_region, lies_orte, ort_id,
    pausierte_ids, warte_bis, welt, welt_z, abgemeldet,
)

pytestmark = [pytest.mark.api, pytest.mark.regression]

BB = {ort_id("potsdam"), ort_id("cottbus")}                      # Brandenburg
DE = {ort_id(k) for k, v in ORTE.items() if v[3] == "Deutschland"}
ALLE = {ort_id(k) for k in ORTE}
WARTEZEIT = 8.0


def _offene_auftraege(client) -> set:
    r = client.get("/recompute-status")
    assert r.status_code == 200, r.text
    return set(r.json()["pending"])


class _Nachladen:
    def __init__(self, welt, spion, scharf):
        self.welt = welt
        self.spion = spion
        self.scharf = scharf


@pytest.fixture
def nachladen(client, welt_z, monkeypatch):
    """Bereitet die Welt vor: Entdecken-Neulauf und Wetter werden stillgelegt (nicht Gegenstand dieser
    Tests), der Rechenprozess wird durch den Spion ersetzt. `scharf()` schaltet den Test-Modus
    „keine Hintergrundläufe“ ab — erst NACH dem Vorbereiten des Ausgangszustands aufrufen."""
    import main

    spion = ProzessSpion()

    async def _nichts(*a, **k):
        return None

    async def _wetter_fertig(*a, **k):
        return True

    monkeypatch.setattr(main, "_trigger_discover_debounced", lambda *a, **k: None)
    monkeypatch.setattr(main, "_refresh_discover", _nichts)
    monkeypatch.setattr(main, "_weather_overlay", _nichts)
    monkeypatch.setattr(main, "_weather_overlay_single", _wetter_fertig)
    monkeypatch.setattr(main, "_apply_calendar_delta", _nichts)
    monkeypatch.setattr(main, "_load_caches", lambda *a, **k: main._load_feed_cache())

    def scharf():
        monkeypatch.setattr(main, "_NO_BACKGROUND", False)
        monkeypatch.setattr(asyncio, "create_subprocess_exec", spion.fake_exec)

    n = _Nachladen(welt_z, spion, scharf)
    yield n
    if spion.sperre is not None:
        spion.sperre.set()                  # nichts hängen lassen


def _text_der_starts(spion) -> str:
    return " || ".join(" ".join(str(a) for a in args) for args in spion.starts)


# ── Einschalten startet sofort einen eigenen Lauf ─────────────────────────────

def test_einschalten_startet_sofort_einen_lauf_nur_fuer_die_orte_des_gebiets(client, nachladen):
    """Regel 3 / Entscheidung 2: Wird Brandenburg eingeschaltet, startet sofort EIN Rechenprozess für genau die
    beiden Brandenburger Orte (gebündelt) — nicht für andere Orte, nicht ein Prozess je Ort. Die Antwort an den
    Host wartet nicht auf das Ende; die beiden Orte stehen sofort als „wird aktualisiert“ in der Liste der
    offenen Aufträge und sind nicht mehr pausiert."""
    s = nachladen.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    nachladen.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert s.beendet == 0, "die Antwort auf das Einschalten hat auf das Ende des Nachladens gewartet"
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT), "kein Rechenprozess nach dem Einschalten gestartet"
    assert warte_bis(lambda: BB <= _offene_auftraege(client), WARTEZEIT), \
        "die Orte stehen nicht als „wird aktualisiert“ in /recompute-status: %s" % _offene_auftraege(client)
    assert not (_offene_auftraege(client) & (ALLE - BB)), "fremde Orte stehen als „wird aktualisiert“ da"
    assert not (pausierte_ids(client) & BB), "die Orte sind nach dem Einschalten noch pausiert"
    s.sperre.set()
    assert warte_bis(lambda: s.beendet >= 1, WARTEZEIT)
    assert s.ids_in_starts(BB) == BB, "nicht alle Orte der Region wurden nachgeladen"
    assert not s.ids_in_starts(ALLE - BB), "es wurden auch Orte außerhalb der Region berechnet: %s" % s.ids_in_starts(ALLE - BB)
    assert all(i in " ".join(str(a) for a in s.starts[0]) for i in BB), \
        "der erste Rechenprozess deckt nicht beide Orte gemeinsam ab (kein gebündelter Lauf)"
    assert s.max_aktiv == 1


def test_land_einschalten_ist_genau_ein_lauf_nicht_einer_je_ort(client, nachladen):
    """AK-72: Das Einschalten eines ganzen Landes (Deutschland, 6 Testorte) löst einen Nachladelauf aus, nicht
    einen je Ort. Gezählt werden die gestarteten Rechenprozesse: höchstens zwei (Chancen, danach eventuell
    der Kalender — Ticket: „Kalender zuletzt oder in der Nacht“), der erste deckt alle Orte des Landes ab."""
    s = nachladen.spion
    host_schaltet_land(client, "Deutschland", False)
    nachladen.scharf()
    host_schaltet_land(client, "Deutschland", True)
    assert warte_bis(lambda: s.ids_in_starts(DE) == DE and s.aktiv == 0 and s.beendet >= 1, WARTEZEIT), \
        "Orte des Landes nicht (vollständig) nachgeladen: %s" % s.ids_in_starts(DE)
    assert not s.ids_in_starts(ALLE - DE), "es wurden Orte anderer Länder berechnet"
    assert len(s.starts) <= 2, "%d Rechenprozesse für ein Land — erwartet ein gebündelter Lauf" % len(s.starts)
    assert all(i in " ".join(str(a) for a in s.starts[0]) for i in DE), "erster Prozess nicht gebündelt für alle Orte"
    assert s.max_aktiv == 1


def test_zweites_einschalten_wird_angehaengt_nie_zwei_laeufe_gleichzeitig(client, nachladen):
    """Entscheidung 2 / Pre-Mortem 4: Höchstens EIN Nachladelauf gleichzeitig; schaltet der Host währenddessen
    eine zweite Region ein, wird sie angehängt (läuft danach) und geht nicht verloren."""
    s = nachladen.spion
    host_schaltet_land(client, "Italien", False)
    s.sperre = threading.Event()
    nachladen.scharf()
    host_schaltet_region(client, "Italien", "Trentino-Südtirol", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT), "erster Nachladelauf startet nicht"
    host_schaltet_region(client, "Italien", "Venetien", True)
    assert warte_bis(lambda: ort_id("venedig") in _offene_auftraege(client), WARTEZEIT), \
        "die angehängte Region steht nicht als „wird aktualisiert“ da"
    import time
    time.sleep(0.7)
    assert s.max_aktiv == 1, "zwei Nachladeläufe liefen gleichzeitig"
    assert not s.ids_in_starts({ort_id("venedig")}), "die zweite Region wurde schon gestartet, obwohl der erste Lauf noch läuft"
    s.sperre.set()
    assert warte_bis(lambda: ort_id("venedig") in s.ids_in_starts({ort_id("venedig")}), WARTEZEIT), \
        "die angehängte Region wurde nie nachgeladen"
    assert ort_id("sterzing") in s.ids_in_starts({ort_id("sterzing")})
    assert s.max_aktiv == 1


def test_nachladen_wartet_nicht_auf_einen_laufenden_grosslauf(client, nachladen, monkeypatch):
    """Entscheidung 2: „nicht auf den Nachtlauf warten, nicht hinter anderen Aufträgen anstellen“. Läuft gerade
    ein großer Lauf (die gemeinsame Sperre ist belegt), startet das Nachladen trotzdem sofort."""
    import main
    s = nachladen.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    nachladen.scharf()
    monkeypatch.setattr(main, "_precompute_running", True)
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.ids_in_starts(BB) == BB, WARTEZEIT), \
        "Nachladen hat sich hinter den laufenden Großlauf gestellt"


def test_ausschalten_und_gebiet_ohne_orte_starten_keinen_nachladelauf(client, nachladen):
    """Gegenfall zu Regel 3: Nur das EINschalten lädt nach. Ausschalten startet keinen Rechenprozess; ein Gebiet
    ohne Orte (Norwegen) ebenfalls nicht."""
    import time
    s = nachladen.spion
    nachladen.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    host_schaltet_land(client, "Norwegen", True)
    time.sleep(0.7)
    assert s.starts == [], "unerwarteter Rechenprozess: %s" % _text_der_starts(s)


def test_schutz_fehlschlag_des_nachladens_laesst_die_orte_nicht_haengen(client, nachladen):
    """Ehrlichkeit des Banners (Wirkungs-Tabelle 24): Endet der Rechenprozess mit Fehler, bleibt „wird aktualisiert“
    nicht für immer stehen und die Orte bleiben eingeschaltet (nur die Chancen fehlen bis zum Nachtlauf)."""
    s = nachladen.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.rc = 1
    nachladen.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.beendet >= 1, WARTEZEIT), "kein Rechenprozess gestartet"
    assert warte_bis(lambda: not (_offene_auftraege(client) & BB), WARTEZEIT), \
        "„wird aktualisiert“ bleibt nach fehlgeschlagenem Lauf stehen"
    assert not (pausierte_ids(client) & BB)


# ── Ausschalten während des Nachladens ────────────────────────────────────────

def test_ausschalten_waehrend_des_nachladens_verwirft_das_ergebnis(client, nachladen):
    """AK-67 / Pre-Mortem 15: Wird die Region ausgeschaltet, während für sie gerechnet wird, erlischt „wird
    aktualisiert“, es wird kein weiterer Rechenschritt für diese Orte mehr gestartet (z. B. der Kalender), und
    das fertige Ergebnis taucht nirgends auf — weder im Arbeitsspeicher noch im Feed."""
    import main
    import time
    w = nachladen.welt
    s = nachladen.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)

    def _ergebnis_schreiben(args):
        w.feed.write_text(json.dumps({"computed_at": "2026-10-11T01:00:00+00:00",
                                      "opportunities": w.termine_fuer(["potsdam", "cottbus"])}), encoding="utf-8")

    s.sperre = threading.Event()
    s.beim_ende = _ergebnis_schreiben
    nachladen.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert warte_bis(lambda: not (_offene_auftraege(client) & BB), WARTEZEIT), \
        "„wird aktualisiert“ erlischt nach dem Ausschalten nicht"
    gestartet = len(s.starts)
    s.sperre.set()
    assert warte_bis(lambda: s.aktiv == 0, WARTEZEIT)
    time.sleep(1.0)
    assert len(s.starts) == gestartet, "nach dem Ausschalten wurde noch ein Rechenschritt für die Region gestartet"
    assert not (_offene_auftraege(client) & BB)
    assert not ({e["location_id"] for e in main._feed_cache} & BB), "Ergebnis des abgebrochenen Laufs im Speicher"
    assert not (set(e["location_id"] for e in client.get("/opportunities").json()) & BB), \
        "Ergebnis des abgebrochenen Laufs wird ausgeliefert"
    assert pausierte_ids(client) >= BB


# ── Nachtlauf ─────────────────────────────────────────────────────────────────

def _nachtlauf(monkeypatch, welt) -> list:
    """Startet die Vorberechnung (nur Chancen, alle Orte) wie im Test zu BUG-118 mit gestubbter Astronomie/Netz
    und liefert die IDs aller Orte, für die tatsächlich gerechnet wurde."""
    import precompute as P
    from data import backup as _backup
    gerechnet: list = []

    async def _fake_opps(loc, *a, **k):
        gerechnet.append(loc.id)
        return []

    async def _fake_hoehen(*a, **k):
        return {}

    monkeypatch.setattr(_backup, "snapshot_before_precompute", lambda: None)
    monkeypatch.setattr(_backup, "backup_after_precompute", lambda: None)
    monkeypatch.setattr(P, "LocationStore", lambda *a, **k: welt.store)
    monkeypatch.setattr(P, "CACHE_DIR", welt.tmp / "cache")
    monkeypatch.setattr(P, "find_opportunities_multi_day", _fake_opps)
    monkeypatch.setattr(P, "fetch_elevations", _fake_hoehen)
    args = argparse.Namespace(feed_only=True, calendar_only=False, full=False, location_id=None)
    asyncio.run(P.main(args))
    return gerechnet


def test_nachtlauf_rechnet_ausgeschaltete_gebiete_nicht_und_aktive_weiter(client, welt_z, monkeypatch):
    """Regel 1 / AK-07: Ist Brandenburg aus, rechnet der Nachtlauf (eigener Prozess, liest den gespeicherten
    Zustand) die beiden Orte nicht — alle anderen schon. Nach dem Wieder-Einschalten rechnet er sie wieder mit."""
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    gerechnet = _nachtlauf(monkeypatch, welt_z)
    assert not (set(gerechnet) & BB), "Nachtlauf rechnet ausgeschaltete Orte: %s" % (set(gerechnet) & BB)
    assert (ALLE - BB) <= set(gerechnet), "Nachtlauf lässt aktive Orte aus: %s" % ((ALLE - BB) - set(gerechnet))
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert BB <= set(_nachtlauf(monkeypatch, welt_z)), "Nachtlauf rechnet wieder eingeschaltete Orte nicht mit"


def test_nachtlauf_rechnet_ein_ausgeschaltetes_land_nicht(client, welt_z, monkeypatch):
    """Regel 1 (Beispiel Italien aus): Land aus = keine Berechnung für alle seine Orte."""
    host_schaltet_land(client, "Italien", False)
    gerechnet = set(_nachtlauf(monkeypatch, welt_z))
    assert not (gerechnet & {ort_id("sterzing"), ort_id("venedig")})
    assert ort_id("berlin1") in gerechnet


# ── Neustart ──────────────────────────────────────────────────────────────────

def _starte_server_neu(welt, monkeypatch, nachlaufzeit_s: float = 1.0, pruefe=None, ortsliste_neu=False) -> None:
    """Simuliert einen Neustart: startup() läuft in einer frischen Ereignisschleife; die schweren, netzabhängigen
    Teile (Wetterkarte, Scheduler, Entdecken, Geländehöhen, Kalenderdatei) sind abgeschaltet. Aus der Festplatte
    kommen die Datenbank und die Chancen-Datei; der Arbeitsspeicher wird vorher geleert wie bei einem echten
    Neustart. (Annahme A4: das Fortsetzen hängt an startup().) Mit ortsliste_neu=True wird auch die Ortsliste
    geleert und beim Start wirklich aus der Datenbank gelesen (echter Ladeweg der eigenen Orte)."""
    import main
    from data import locations as _dl
    from data.store import LocationStore

    async def _nichts(*a, **k):
        return None

    monkeypatch.setattr(main, "_NO_BACKGROUND", False)
    monkeypatch.setattr(main, "_store", LocationStore(db_path=welt.tmp / "us141.db"))   # frisch von der Festplatte
    monkeypatch.setattr(main, "_feed_cache", [])
    monkeypatch.setattr(main, "_recompute_pending", set())
    monkeypatch.setattr(main, "_precompute_running", False)
    if ortsliste_neu:
        _dl.LOCATIONS[:] = []
    else:
        monkeypatch.setattr(main, "_load_custom_locations", lambda *a, **k: None)
    for name in ("_startup_integrity_check", "_load_qa_values", "_load_location_overrides",
                 "_load_elevation_cache", "_load_weather_map_cache_from_disk", "_startup_check_discover_schema",
                 "_startup_setup_scheduler"):
        monkeypatch.setattr(main, name, lambda *a, **k: None)
    monkeypatch.setattr(main, "_load_caches", lambda *a, **k: (main._load_feed_cache(), True)[1])
    monkeypatch.setattr(main, "_weather_overlay", _nichts)
    monkeypatch.setattr(main, "_weather_overlay_single", lambda *a, **k: _wahr())
    monkeypatch.setattr(main, "_delayed_build_weather_map", _nichts)
    monkeypatch.setattr(main, "_apply_calendar_delta", _nichts)
    monkeypatch.setattr(main, "_refresh_discover", _nichts)
    monkeypatch.setattr(main, "_trigger_discover_debounced", lambda *a, **k: None)
    schleife = asyncio.new_event_loop()
    try:
        schleife.run_until_complete(main.startup())
        schleife.run_until_complete(asyncio.sleep(nachlaufzeit_s))
        if pruefe is not None:
            pruefe()                 # noch bei laufender Anwendung prüfen, bevor die Schleife abgeräumt wird
    finally:
        try:
            for t in asyncio.all_tasks(schleife):
                t.cancel()
            schleife.run_until_complete(asyncio.sleep(0))
        finally:
            schleife.close()


async def _wahr():
    return True


def test_neustart_setzt_nachladen_fuer_aktive_orte_ohne_chancen_fort(client, welt_z, monkeypatch):
    """AK-61 / Pre-Mortem 13: Ausgangslage wie nach einem Neustart mitten im Nachladen — Cottbus ist aktiv, hat
    aber keine Chancen; alle anderen aktiven Orte haben welche; die zwei Londoner Orte sind pausiert und haben
    keine. Nach dem Start wird nur für Cottbus nachgeladen (nicht für Orte mit Chancen, nicht für pausierte), und
    „wird aktualisiert“ bleibt für Cottbus stehen, solange der Lauf nicht fertig ist."""
    s = ProzessSpion()
    s.sperre = threading.Event()
    host_schaltet_region(client, "Vereinigtes Königreich (UK)", "England", False)
    aktive_mit_chancen = [k for k in ORTE if k not in ("cottbus", "london1", "london2")]
    welt_z.setze_feed(welt_z.termine_fuer(aktive_mit_chancen))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", s.fake_exec)
    import main

    def _pruefen():
        gemeint = s.ids_in_starts(ALLE)
        assert ort_id("cottbus") in gemeint, "Nachladen für den aktiven Ort ohne Chancen wurde nicht fortgesetzt"
        mit = {ort_id(k) for k in aktive_mit_chancen}
        assert not (gemeint & mit), "Orte mit Chancen wurden neu berechnet: %s" % (gemeint & mit)
        assert not (gemeint & {ort_id("london1"), ort_id("london2")}), "pausierte Orte wurden neu berechnet"
        assert ort_id("cottbus") in main._recompute_pending, "„wird aktualisiert“ fehlt für den fortgesetzten Ort"

    try:
        _starte_server_neu(welt_z, monkeypatch, nachlaufzeit_s=1.0, pruefe=_pruefen)
    finally:
        s.sperre.set()


def test_neustart_ohne_fehlende_chancen_startet_kein_nachladen(client, welt_z, monkeypatch):
    """Gegenfall zu AK-61: Haben alle aktiven Orte Chancen, startet der Neustart keinen Rechenprozess."""
    s = ProzessSpion()
    host_schaltet_region(client, "Vereinigtes Königreich (UK)", "England", False)
    welt_z.setze_feed(welt_z.termine_fuer([k for k in ORTE if k not in ("london1", "london2")]))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", s.fake_exec)
    _starte_server_neu(welt_z, monkeypatch, nachlaufzeit_s=0.8)
    assert s.starts == [], "unerwarteter Rechenprozess nach dem Start: %s" % _text_der_starts(s)


def test_nach_neustart_gilt_der_gespeicherte_schalterzustand_auch_fuer_alte_chancen(client, welt_z, monkeypatch):
    """AK-71 / Race R5: Der Schalter ist gespeichert, aber die Chancen-Datei stammt noch aus der Zeit davor
    (Neustart zwischen Speichern und Aufräumen). Nach dem Start (Datenbank frisch gelesen) gilt der neue Zustand:
    im Arbeitsspeicher und in den Antworten stehen keine Chancen der ausgeschalteten Region."""
    import main
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    termine = welt_z.termine_fuer(list(ORTE.keys()))
    welt_z.feed.write_text(json.dumps({"computed_at": "2026-10-11T00:00:00+00:00", "opportunities": termine}),
                           encoding="utf-8")
    s = ProzessSpion()
    monkeypatch.setattr(asyncio, "create_subprocess_exec", s.fake_exec)
    _starte_server_neu(welt_z, monkeypatch, nachlaufzeit_s=0.5)
    assert not ({e["location_id"] for e in main._feed_cache} & BB), "alte Chancen der ausgeschalteten Region im Speicher"
    ids = {e["location_id"] for e in client.get("/opportunities").json()}
    assert not (ids & BB), "alte Chancen der ausgeschalteten Region werden ausgeliefert"
    assert ort_id("berlin1") in ids, "aktive Orte müssen erhalten bleiben"
    assert pausierte_ids(client) >= BB, "gespeicherter Zustand ging beim Neustart verloren"


def test_geloeschter_ort_einer_ausgeschalteten_region_kommt_nicht_zurueck(client, nachladen, monkeypatch):
    """AK-G8: Brandenburg ist aus, der Host löscht Potsdam (pausiert, aber noch da), schaltet Brandenburg wieder
    ein. Das Nachladen berechnet nur Cottbus; der Nachtlauf rechnet Potsdam nicht; nach einem Neustart ist Potsdam
    weder in der Ortsliste noch in den Chancen."""
    import main
    s = nachladen.spion
    w = nachladen.welt
    pid, cid = ort_id("potsdam"), ort_id("cottbus")
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    als_host(client)
    r = client.delete("/locations/" + pid)
    assert r.status_code == 200, r.text
    nachladen.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.ids_in_starts({cid}) == {cid} and s.aktiv == 0, WARTEZEIT), "Cottbus wurde nicht nachgeladen"
    assert pid not in s.ids_in_starts({pid}), "das Nachladen rechnet den gelöschten Ort"
    assert pid not in lies_orte(client)
    assert pid not in _nachtlauf(monkeypatch, w), "der Nachtlauf rechnet den gelöschten Ort"
    s.starts[:] = []
    _starte_server_neu(w, monkeypatch, nachlaufzeit_s=0.5, ortsliste_neu=True)
    assert cid in lies_orte(client), "der Gegenfall fehlt: Cottbus muss nach dem Neustart aus der Datenbank geladen sein"
    assert pid not in lies_orte(client), "der gelöschte Ort ist nach dem Neustart zurück"
    assert pid not in {e["location_id"] for e in main._feed_cache}
    assert pid not in s.ids_in_starts({pid})
