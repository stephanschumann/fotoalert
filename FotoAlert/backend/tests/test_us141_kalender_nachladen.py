"""US-141 (Entscheidung vom 2026-10-15) — Kalender beim Einschalten eines Gebiets sofort mitrechnen.

Was diese Datei absichert (alles offline: gestubbte Rechnung, Wegwerf-Dateien, Prozess-Spion; die echte, über
1 GB große calendar.json wird nie angefasst):

  Rechenprozess (precompute --location-ids … --mit-kalender / --nur-kalender)
    * rechnet den Kalender NUR für die aktiven Orte des Laufs und mischt ihn in EINEM Schreibvorgang in
      calendar.json ein (nicht je Ort); die Einträge dieser Orte werden ersetzt, alle anderen Orte, ihre
      Angaben und der Algorithmus-Stand der Datei bleiben unverändert;
    * höchstens ein Backup je Lauf (vorher/nachher je eines) — der Kalender-Schritt macht kein eigenes;
    * fehlt die Kalenderdatei oder ist sie unbrauchbar, wird nichts geschrieben und nichts erzeugt;
    * zu wenig Platz: Fehlermeldung statt Absturz, Datei unverändert, Chancen bleiben gültig;
    * Abbruch/Schreibfehler mitten im Schreiben: bisherige Datei unversehrt, keine Temp-Datei übrig;
    * Kollision: ein anderer Schreiber unter der Dateisperre geht nicht verloren;
    * wer während des Laufs ausgeschaltet wurde, wird nicht eingemischt.
  Server
    * startet weiterhin EINEN Prozess mit allen Orten (jetzt mit --mit-kalender), holt das Wetter, sobald die
      Chancen stehen (gleichzeitig mit dem Kalender), zeigt den Kalender-Schritt im Fortschritt, übernimmt den
      eingemischten Kalender ohne die große Datei neu einzulesen;
    * Fehler im Kalender-Schritt machen Chancen und Wetter nicht ungültig und werden ehrlich gemeldet;
    * Ausschalten während der Kalender-Phase beendet den Prozess, nichts bleibt „aktiv“, nichts wird übernommen;
    * nach einem Neustart wird nur noch der fehlende Kalender nachgeholt (--nur-kalender).

Python-3.9-kompatibel.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import threading
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from us141_adapter import (  # noqa: F401  (Fixtures)
    ORTE, als_host, host_schaltet_region, ort_id, termin, warte_bis, welt, welt_z,
)
from test_us141_nachladen import _starte_server_neu, nachladen  # noqa: F401

pytestmark = [pytest.mark.api, pytest.mark.regression]

BB = {ort_id("potsdam"), ort_id("cottbus")}
ALLE = {ort_id(k) for k in ORTE}
WARTEZEIT = 8.0
POSTFACH = "calendar_nachladen_last.jsonl"


# ── Hilfen für die Läufe im selben Prozess ───────────────────────────────────

def _zeit(tage: int, stunde: int = 12) -> datetime:
    return datetime.combine(date.today(), datetime.min.time()).replace(hour=stunde, tzinfo=timezone.utc) + timedelta(days=tage)


def _kalender_datei(welt, version: str = "0.9") -> Path:
    """Legt eine kleine Wegwerf-calendar.json an: alle Testorte mit je zwei Terminen, Meta je Ort."""
    cache = welt.tmp / "cache"
    cache.mkdir(exist_ok=True)
    pfad = cache / "calendar.json"
    termine = []
    meta = {}
    for k in ORTE:
        lid = ort_id(k)
        for n in (1, 2):
            termine.append(termin(lid, zeit=_zeit(n), nr=n, typ="ALT_" + k))
        meta[lid] = {"coordinates_hash": "alt-" + k, "computed_dates": ["2026-10-01"]}
    termine.sort(key=lambda r: (r["shoot_time"], -r["overall_score"]))
    pfad.write_text(json.dumps({"algorithm_version": version, "computed_at": "2026-10-11T00:00:00+00:00",
                                "computed_locations": meta, "events": termine}, ensure_ascii=False), encoding="utf-8")
    return pfad


def _lauf(monkeypatch, welt, ids, mit_kalender=True, nur_kalender=False, kalender_fn=None, feed_vorhanden=True):
    """Führt precompute.main mit --location-ids im selben Prozess aus (gestubbte Rechnung, Backup-Zähler).
    Gibt (Feed-Rechnungen, Kalender-Rechnungen, Backups, Cache-Ordner) zurück."""
    import precompute as P
    from data import backup as _backup
    from data import gebiet_zustand as _gz
    # P.main meldet seine eigene Quelle des Gebiets-Zustands an; nach dem Test muss die vorherige zurückkommen
    monkeypatch.setattr(_gz, "_quelle", _gz._quelle)
    feed_gerechnet: list = []
    kal_gerechnet: list = []
    sicherungen = {"vorher": 0, "nachher": 0}

    async def _fake_opps(loc, *a, **k):
        feed_gerechnet.append(loc.id)
        return []

    async def _fake_kalender(loc, today):
        kal_gerechnet.append(loc.id)
        if kalender_fn is not None:
            return kalender_fn(loc, today)
        return [termin(loc.id, zeit=_zeit(n), nr=n, typ="NEU_" + loc.id[-6:]) for n in (3, 4, 5)]

    async def _fake_hoehen(*a, **k):
        return {}

    def _zaehle(schluessel):
        def f():
            sicherungen[schluessel] += 1
        return f

    monkeypatch.setattr(_backup, "snapshot_before_precompute", _zaehle("vorher"))
    monkeypatch.setattr(_backup, "backup_after_precompute", _zaehle("nachher"))
    monkeypatch.setattr(P, "LocationStore", lambda *a, **k: welt.store)
    monkeypatch.setattr(P, "CACHE_DIR", welt.tmp / "cache")
    monkeypatch.setattr(P, "find_opportunities_multi_day", _fake_opps)
    monkeypatch.setattr(P, "_kalender_fuer_ort", _fake_kalender)
    monkeypatch.setattr(P, "fetch_elevations", _fake_hoehen)
    (welt.tmp / "cache").mkdir(exist_ok=True)
    if feed_vorhanden:
        (welt.tmp / "cache" / "opportunities.json").write_text(
            json.dumps({"computed_at": "2026-10-11T00:00:00+00:00", "opportunities": welt.termine_fuer(list(ORTE))}),
            encoding="utf-8")
    args = argparse.Namespace(feed_only=True, calendar_only=False, full=False, location_id=None,
                              location_ids=",".join(sorted(ids)), mit_kalender=mit_kalender, nur_kalender=nur_kalender)
    asyncio.run(P.main(args))
    return feed_gerechnet, kal_gerechnet, sicherungen, welt.tmp / "cache"


def _lies(pfad: Path) -> dict:
    return json.loads(pfad.read_text(encoding="utf-8"))


def _fortschritt(cache: Path) -> dict:
    return _lies(cache / "nachladen_fortschritt.json")


# ── Rechenprozess ────────────────────────────────────────────────────────────

def test_kalender_wird_nur_fuer_die_orte_des_gebiets_gerechnet_und_ersetzt_nur_deren_eintraege(client, welt_z, monkeypatch):
    """Brandenburg: Chancen UND Kalender nur für Potsdam und Cottbus. In calendar.json sind danach die alten Einträge
    dieser beiden Orte weg und die neuen da; alle übrigen Orte, ihre Angaben und der Algorithmus-Stand sind
    unverändert; die Datei ist weiterhin nach Zeit sortiert; die Angaben der beiden Orte stehen auf „365 Tage fertig“."""
    import precompute as P
    cal = _kalender_datei(welt_z, version="0.9")
    vorher = _lies(cal)
    feed_g, kal_g, _s, cache = _lauf(monkeypatch, welt_z, BB)
    assert set(feed_g) == BB and set(kal_g) == BB, "gerechnet: Chancen %s, Kalender %s" % (sorted(feed_g), sorted(kal_g))
    nachher = _lies(cal)
    assert nachher["algorithm_version"] == "0.9", "der Algorithmus-Stand der Datei darf nicht überschrieben werden"
    ids = {e["location_id"] for e in nachher["events"]}
    assert ids == ALLE
    for lid in BB:
        eigene = [e for e in nachher["events"] if e["location_id"] == lid]
        assert len(eigene) == 3 and all(e["event_type"].startswith("NEU_") for e in eigene), "Einträge nicht ersetzt: %s" % lid
    fremd_vorher = [e for e in vorher["events"] if e["location_id"] not in BB]
    fremd_nachher = [e for e in nachher["events"] if e["location_id"] not in BB]
    assert fremd_nachher == fremd_vorher, "Einträge anderer Orte wurden verändert"
    keys = [(e["shoot_time"], -e["overall_score"]) for e in nachher["events"]]
    assert keys == sorted(keys), "Kalender nicht mehr nach Zeit sortiert"
    for lid in ALLE - BB:
        assert nachher["computed_locations"][lid] == vorher["computed_locations"][lid]
    heute = date.today()
    erwartet = sorted((heute + timedelta(days=i)).isoformat() for i in range(365))
    for lid in BB:
        m = nachher["computed_locations"][lid]
        loc = welt_z.orte[[k for k in ORTE if ort_id(k) == lid][0]]
        assert m["coordinates_hash"] == P._location_hash(loc)
        assert m["computed_dates"] == erwartet
    assert nachher["computed_at"] != vorher["computed_at"]


def test_ein_schreibvorgang_fuer_die_kalenderdatei_und_ein_backup_je_lauf(client, welt_z, monkeypatch):
    """Zwei Orte, aber nur EIN Schreibvorgang auf calendar.json (kein Schreiben je Ort) und höchstens je ein Backup
    vorher und nachher — der Kalender-Schritt löst kein weiteres aus."""
    from data import cache_io
    _kalender_datei(welt_z)
    echt = cache_io.atomar_schreiben
    schreibvorgaenge = []

    def spion(pfad, text, encoding="utf-8"):
        schreibvorgaenge.append(Path(pfad).name)
        return echt(pfad, text, encoding)

    monkeypatch.setattr(cache_io, "atomar_schreiben", spion)
    _f, _k, sicherungen, _c = _lauf(monkeypatch, welt_z, BB)
    assert schreibvorgaenge.count("calendar.json") == 1, "calendar.json wurde %d-mal geschrieben: %s" % (
        schreibvorgaenge.count("calendar.json"), schreibvorgaenge)
    assert sicherungen == {"vorher": 1, "nachher": 1}, "mehr als ein Backup je Lauf: %s" % sicherungen


def test_ohne_mit_kalender_bleibt_alles_wie_bei_baustein_3(client, welt_z, monkeypatch):
    """Ohne --mit-kalender wird kein Kalender gerechnet und calendar.json nicht angefasst (bisheriges Verhalten)."""
    cal = _kalender_datei(welt_z)
    roh = cal.read_bytes()
    _f, kal_g, _s, cache = _lauf(monkeypatch, welt_z, BB, mit_kalender=False)
    assert kal_g == []
    assert cal.read_bytes() == roh
    assert "kalender" not in _fortschritt(cache)


def test_fortschrittsdatei_meldet_chancen_fertig_und_kalenderstand(client, welt_z, monkeypatch):
    """Die Fortschrittsdatei trägt am Ende `feed_fertig` und den Kalenderstand (fertig, beide Orte, Postfach)."""
    _kalender_datei(welt_z)
    _f, _k, _s, cache = _lauf(monkeypatch, welt_z, BB)
    fort = _fortschritt(cache)
    assert set(fort["fertig"]) == BB and fort["feed_fertig"] is True
    kal = fort["kalender"]
    assert kal["status"] == "fertig" and set(kal["fertig"]) == BB and kal["gesamt"] == 2 and kal["postfach"] is True
    assert kal["termine"] == 6 and not kal["fehler"]


def test_postfach_fuer_den_server_enthaelt_genau_die_neuen_eintraege(client, welt_z, monkeypatch):
    """Das Postfach (Zeilendatei) hat eine Kopfzeile mit Prozessnummer und je Ort eine Zeile mit dessen Terminen."""
    cal = _kalender_datei(welt_z)
    _lauf(monkeypatch, welt_z, BB)
    zeilen = (cal.parent / POSTFACH).read_text(encoding="utf-8").strip().splitlines()
    kopf = json.loads(zeilen[0])
    assert kopf["pid"] == os.getpid() and set(kopf["location_ids"]) == BB
    je_ort = {json.loads(z)["location_id"]: json.loads(z)["events"] for z in zeilen[1:]}
    assert set(je_ort) == BB and all(len(v) == 3 for v in je_ort.values())
    in_datei = {e["id"] for e in _lies(cal)["events"] if e["location_id"] in BB}
    assert {e["id"] for v in je_ort.values() for e in v} == in_datei


def test_nur_kalender_rechnet_keine_chancen_neu(client, welt_z, monkeypatch):
    """Fortsetzen nach einem Neustart: --nur-kalender rechnet den Kalender, aber nicht noch einmal die Chancen."""
    cal = _kalender_datei(welt_z)
    feed = welt_z.tmp / "cache" / "opportunities.json"
    feed_g, kal_g, sicherungen, cache = _lauf(monkeypatch, welt_z, {ort_id("cottbus")}, mit_kalender=False, nur_kalender=True)
    assert feed_g == [] and kal_g == [ort_id("cottbus")]
    assert _fortschritt(cache)["kalender"]["status"] == "fertig"
    assert sicherungen == {"vorher": 1, "nachher": 1}
    assert len([e for e in _lies(cal)["events"] if e["location_id"] == ort_id("cottbus")]) == 3
    assert {e["location_id"] for e in _lies(feed)["opportunities"]} == ALLE, "die Chancen-Datei wurde verändert"


def test_fehlende_kalenderdatei_wird_nicht_erzeugt_und_chancen_bleiben(client, welt_z, monkeypatch):
    """Gibt es noch keine calendar.json, entsteht keine unvollständige (nur das Gebiet); der Schritt wird übersprungen,
    es wird nichts gerechnet, die Chancen sind trotzdem fertig."""
    (welt_z.tmp / "cache").mkdir(exist_ok=True)
    feed_g, kal_g, _s, cache = _lauf(monkeypatch, welt_z, BB)
    assert not (cache / "calendar.json").exists()
    assert kal_g == [] and set(feed_g) == BB
    assert _fortschritt(cache)["kalender"]["status"] == "uebersprungen"


def test_kaputte_kalenderdatei_bleibt_unveraendert(client, welt_z, monkeypatch):
    cache = welt_z.tmp / "cache"
    cache.mkdir(exist_ok=True)
    (cache / "calendar.json").write_text('{"algorithm_version": "1.5", "events": [ {"abgeschnitten', encoding="utf-8")
    roh = (cache / "calendar.json").read_bytes()
    _lauf(monkeypatch, welt_z, BB)
    assert (cache / "calendar.json").read_bytes() == roh
    kal = _fortschritt(cache)["kalender"]
    assert kal["status"] == "fehler" and "nicht lesbar" in kal["text"]
    assert not list(cache.glob("calendar.json.tmp-*"))


def test_zu_wenig_platz_ergibt_fehlermeldung_statt_absturz(client, welt_z, monkeypatch):
    """Ist weniger Platz frei als für das atomare Neuschreiben nötig (alte + neue Datei), wird NICHTS gerechnet und
    geschrieben; der Lauf endet ohne Absturz, die Fortschrittsdatei nennt den Grund, die Chancen sind fertig."""
    from data import cache_io
    cal = _kalender_datei(welt_z)
    roh = cal.read_bytes()
    monkeypatch.setattr(cache_io.shutil, "disk_usage", lambda p: SimpleNamespace(total=10 ** 9, used=10 ** 9 - 1000, free=1000))
    feed_g, kal_g, _s, cache = _lauf(monkeypatch, welt_z, BB)
    assert set(feed_g) == BB
    assert kal_g == [], "es wurde gerechnet, obwohl der Platz nicht reicht"
    assert cal.read_bytes() == roh
    kal = _fortschritt(cache)["kalender"]
    assert kal["status"] == "fehler" and "Speicherplatz" in kal["text"], kal
    assert set(_fortschritt(cache)["fertig"]) == BB


def test_platzpruefung_rechnet_alte_und_neue_datei_zusammen(tmp_path):
    from data import cache_io
    datei = tmp_path / "gross.json"
    datei.write_bytes(b"x" * 1000)
    frei = cache_io.shutil.disk_usage(str(tmp_path)).free
    cache_io.pruefe_platz_fuer_atomar(datei, zusatz_bytes=0, reserve_bytes=0)            # reicht
    with pytest.raises(cache_io.ZuWenigPlatz):
        cache_io.pruefe_platz_fuer_atomar(datei, zusatz_bytes=frei + 10 ** 6, reserve_bytes=0)   # reicht nicht


def test_schreibfehler_mitten_im_schreiben_laesst_die_alte_datei_unversehrt(client, welt_z, monkeypatch):
    """Platte läuft beim Austauschen voll (os.replace scheitert): bisherige Datei bytegleich, keine Temp-Datei,
    der Lauf endet mit Fehlerstand statt mit einer halben Datei."""
    cal = _kalender_datei(welt_z)
    roh = cal.read_bytes()
    echt = os.replace

    def kaputt(quelle, ziel, *a, **k):
        if str(ziel).endswith("calendar.json"):
            raise OSError(28, "No space left on device")
        return echt(quelle, ziel, *a, **k)

    monkeypatch.setattr(os, "replace", kaputt)
    _f, _k, _s, cache = _lauf(monkeypatch, welt_z, BB)
    assert cal.read_bytes() == roh
    assert not list(cache.glob("calendar.json.tmp-*")), "Temp-Datei blieb liegen"
    assert _fortschritt(cache)["kalender"]["status"] == "fehler"


def test_abbruch_durch_den_server_mitten_im_schreiben_hinterlaesst_keine_halben_daten(client, welt_z, monkeypatch):
    """Der Server beendet den Prozess (Gebiet wieder ausgeschaltet): der Prozess bekommt ein Beenden-Signal, das als
    SystemExit ankommt. Passiert das mitten im Schreiben, bleibt die bisherige Datei bytegleich, die Temp-Datei
    wird entfernt, und das Beenden wird NICHT verschluckt."""
    cal = _kalender_datei(welt_z)
    roh = cal.read_bytes()
    echt = os.fsync

    def unterbrochen(fd):
        raise SystemExit(143)

    monkeypatch.setattr(os, "fsync", unterbrochen)
    with pytest.raises(SystemExit):
        _lauf(monkeypatch, welt_z, BB)
    monkeypatch.setattr(os, "fsync", echt)
    assert cal.read_bytes() == roh
    assert not list(cal.parent.glob("calendar.json.tmp-*")), "halbe Temp-Datei blieb liegen"


def test_wer_waehrend_des_laufs_ausgeschaltet_wurde_wird_nicht_eingemischt(client, welt_z, monkeypatch):
    """Brandenburg wird ausgeschaltet, während der Kalender gerechnet wird: es wird nichts eingemischt (die Datei bleibt
    bytegleich), obwohl der Prozess noch bis zum Ende lief."""
    from data import gebiet_zustand as gz
    cal = _kalender_datei(welt_z)
    roh = cal.read_bytes()

    def und_aus(loc, today):
        welt_z.store.set_area_states_bulk(gz.eintraege_fuer_region("Deutschland", "Brandenburg", False))
        return [termin(loc.id, zeit=_zeit(3), nr=3)]

    _f, kal_g, _s, cache = _lauf(monkeypatch, welt_z, BB, kalender_fn=und_aus)
    assert set(kal_g) == BB
    assert cal.read_bytes() == roh, "ein ausgeschalteter Ort wurde eingemischt"
    assert _fortschritt(cache)["kalender"]["status"] == "uebersprungen"


def test_kollision_ein_anderer_schreiber_unter_der_sperre_geht_nicht_verloren(client, welt_z):
    """Zwei Schreiber: Der eine hält die Sperre und ergänzt einen Termin eines anderen Orts; der Kalender-Schritt
    muss warten und liest danach den neuen Stand — sein Ergebnis enthält beide Änderungen."""
    import precompute as P
    from data import cache_io
    cal = _kalender_datei(welt_z)
    neu = {ort_id("potsdam"): [termin(ort_id("potsdam"), zeit=_zeit(9), nr=9)]}
    meta = {ort_id("potsdam"): {"coordinates_hash": "x", "computed_dates": []}}
    fertig = threading.Event()
    fehler = []

    def merge():
        try:
            P._kalender_einmischen(cal, neu, meta, "2026-10-15T00:00:00+00:00")
        except Exception as exc:                   # pragma: no cover - nur bei Fehler
            fehler.append(exc)
        finally:
            fertig.set()

    fremd = termin(ort_id("berlin1"), zeit=_zeit(7), nr=77, typ="FREMD")
    with cache_io.datei_sperre(cal):
        t = threading.Thread(target=merge)
        t.start()
        time.sleep(0.4)
        assert not fertig.is_set(), "der Kalender-Schritt hat nicht auf die Sperre gewartet"
        daten = _lies(cal)
        daten["events"].append(fremd)
        cache_io.atomar_schreiben(cal, json.dumps(daten))
    assert fertig.wait(10) and not fehler, fehler
    t.join()
    ids = {e["id"] for e in _lies(cal)["events"]}
    assert fremd["id"] in ids, "der Termin des anderen Schreibers ging verloren"
    assert neu[ort_id("potsdam")][0]["id"] in ids


def test_fenster_rechnung_liefert_termine_im_geforderten_zeitraum(client, welt_z, monkeypatch):
    """Die echte Fensterrechnung (ohne Stub) für einen Ort: Termine nur im Zeitraum, alle für diesen Ort, serialisiert."""
    import precompute as P
    monkeypatch.setattr(P, "NACHLADEN_KALENDER_TAGE", 3)
    loc = welt_z.orte["potsdam"]
    termine = asyncio.run(P._kalender_fuer_ort(loc, date.today()))
    assert termine, "für drei Tage wurde kein einziger Termin gefunden"
    grenze = (date.today() + timedelta(days=3)).isoformat()
    assert all(e["location_id"] == loc.id for e in termine)
    assert all(date.today().isoformat() <= e["shoot_time"][:10] <= grenze for e in termine), \
        sorted({e["shoot_time"][:10] for e in termine})


def test_hoehen_aus_dem_zwischenspeicher_werden_ohne_netz_gesetzt(tmp_path):
    import precompute as P
    ort = SimpleNamespace(id="a", elevation_difference_m=None)
    ohne = SimpleNamespace(id="b", elevation_difference_m=None)
    datei = tmp_path / "elevations.json"
    datei.write_text(json.dumps({"elevations": {"a": {"elevation_difference_m": 12.5}}}), encoding="utf-8")
    assert P._hoehen_aus_zwischenspeicher([ort, ohne], datei) == 1
    assert ort.elevation_difference_m == 12.5 and ohne.elevation_difference_m is None
    assert P._hoehen_aus_zwischenspeicher([ort], tmp_path / "gibt_es_nicht.json") == 0


# ── Speicher (gemerkter Zustand) ─────────────────────────────────────────────

def test_gemerkter_kalenderzustand_ueberlebt_in_der_datenbank(client, welt_z):
    s = welt_z.store
    s.merke_nachladen_kalender([ort_id("potsdam"), ort_id("cottbus")])
    assert s.lade_nachladen_kalender() == BB
    s.vergiss_nachladen_kalender([ort_id("potsdam")])
    assert s.lade_nachladen_kalender() == {ort_id("cottbus")}
    assert s.lade_nachladen() == set(), "der Kalenderzustand darf den Chancen-Zustand nicht berühren"


# ── Server ───────────────────────────────────────────────────────────────────

def _fort_schreiben(main, **felder):
    daten = {"pid": 4711, "gesamt": 2, "fertig": [], "fehler": []}
    daten.update(felder)
    main._NACHLADEN_FORTSCHRITT.write_text(json.dumps(daten), encoding="utf-8")


def _kal(status, fertig=(), text=None, fehler=(), postfach=False):
    return {"status": status, "gesamt": 2, "fertig": list(fertig), "fehler": list(fehler), "text": text,
            "termine": 0, "postfach": postfach}


@pytest.fixture
def kalender_server(client, nachladen, monkeypatch):
    """Wie `nachladen`, zusätzlich: Postfach und Fortschrittsdatei liegen in einem Wegwerf-Ordner."""
    import main
    cache = nachladen.welt.tmp / "cache"
    cache.mkdir(exist_ok=True)
    monkeypatch.setattr(main, "_CAL_CACHE", cache / "calendar.json")
    monkeypatch.setattr(main, "_NACHLADEN_FORTSCHRITT", cache / "nachladen_fortschritt.json")
    nachladen.cache = cache
    return nachladen


def _info(client):
    return client.get("/areas").json()["nachladen"]


def test_server_startet_einen_prozess_mit_kalender_fuer_alle_orte(client, kalender_server):
    s = kalender_server.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    kalender_server.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.beendet >= 1 and s.aktiv == 0, WARTEZEIT)
    assert len(s.starts) == 1, "mehr als ein Rechenprozess für ein Gebiet: %d" % len(s.starts)
    text = " ".join(str(a) for a in s.starts[0])
    assert "--location-ids" in text and "--mit-kalender" in text and all(i in text for i in BB)
    assert "--nur-kalender" not in text


def test_wetter_laeuft_waehrend_der_kalender_gerechnet_wird_und_der_kalender_wird_uebernommen(client, kalender_server):
    """Ablauf mit simuliertem Rechenprozess: Chancen fertig -> Wetter startet SOFORT (Prozess läuft noch), der Fortschritt
    nennt den Kalender-Schritt (x von y), danach übernimmt der Server die eingemischten Kalendereinträge der Orte in den
    Arbeitsspeicher, ohne die Datei zu laden; die anderen Orte bleiben, die Reihenfolge bleibt; der gemerkte
    Kalenderzustand ist am Ende leer."""
    import main
    welt = kalender_server.welt
    s = kalender_server.spion
    andere = [termin(ort_id("berlin1"), zeit=_zeit(2), nr=1), termin(ort_id("muenchen"), zeit=_zeit(8), nr=2)]
    alt_bb = [termin(i, zeit=_zeit(4), nr=1, typ="ALT") for i in BB]
    welt.setze_kalender(andere + alt_bb)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    kalender_server.scharf()
    als_host(client)
    assert client.put("/areas/Deutschland/Brandenburg", json={"enabled": True}).status_code == 200
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    assert main._store.lade_nachladen_kalender() == BB, "der offene Kalender wurde nicht gemerkt"
    # 1) Chancen fertig, Kalender rechnet
    _fort_schreiben(main, fertig=sorted(BB), feed_fertig=True, kalender=_kal("rechnet"))
    assert warte_bis(lambda: _info(client)["wetter_bereit"] == 2, WARTEZEIT), _info(client)
    info = _info(client)
    assert s.aktiv == 1, "der Prozess war schon zu Ende — das Wetter hätte gleichzeitig laufen sollen"
    assert info["aktiv"] is True and info["phase"] == "kalender" and info["kalender_aktiv"] is True
    assert info["kalender_gesamt"] == 2 and info["kalender_bereit"] == 0 and info["chancen_bereit"] == 2
    assert info["rest_min"] >= 1
    # 2) Kalender eingemischt: Postfach + Stand
    neue = {i: [termin(i, zeit=_zeit(n), nr=n, typ="NEU") for n in (3, 5)] for i in BB}
    zeilen = [json.dumps({"pid": 4711, "computed_at": "2026-10-15T12:00:00+00:00", "location_ids": sorted(BB)})]
    zeilen += [json.dumps({"location_id": i, "events": ev}) for i, ev in neue.items()]
    (kalender_server.cache / POSTFACH).write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    _fort_schreiben(main, fertig=sorted(BB), feed_fertig=True, kalender=_kal("fertig", fertig=sorted(BB), postfach=True))
    assert warte_bis(lambda: {e["location_id"] for e in main._calendar_cache if e["event_type"] == "NEU"} == BB, WARTEZEIT), \
        "der Kalender der Orte wurde nicht in den Arbeitsspeicher übernommen"
    cache = main._calendar_cache
    assert not [e for e in cache if e["event_type"] == "ALT"], "alte Einträge der Orte blieben stehen"
    assert {e["id"] for e in andere} <= {e["id"] for e in cache}, "Einträge anderer Orte gingen verloren"
    assert [e["shoot_time"] for e in cache] == sorted(e["shoot_time"] for e in cache)
    assert main._calendar_computed_at == "2026-10-15T12:00:00+00:00"
    s.sperre.set()
    assert warte_bis(lambda: _info(client)["aktiv"] is False and s.beendet >= 1, WARTEZEIT)
    assert _info(client)["fehler"] in (None, "")
    assert main._store.lade_nachladen_kalender() == set() and main._store.lade_nachladen() == set()


def test_kalenderfehler_macht_chancen_und_wetter_nicht_ungueltig(client, kalender_server):
    """Meldet der Prozess einen Kalenderfehler (z. B. zu wenig Platz), bleiben die Orte eingeschaltet, Chancen und Wetter
    sind fertig; das Menü meldet den Kalender ehrlich (nicht „Nachladen fehlgeschlagen“); der gemerkte Zustand ist leer."""
    import main
    s = kalender_server.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    kalender_server.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    _fort_schreiben(main, fertig=sorted(BB), feed_fertig=True,
                    kalender=_kal("fehler", text="zu wenig freier Speicherplatz für calendar.json: gebraucht werden etwa 2.9 GB, frei sind 0.1 GB"))
    assert warte_bis(lambda: _info(client)["wetter_bereit"] == 2, WARTEZEIT)
    s.sperre.set()
    assert warte_bis(lambda: _info(client)["aktiv"] is False and s.beendet >= 1, WARTEZEIT)
    fehler = _info(client)["fehler"]
    assert fehler and "Kalender" in fehler and "Speicherplatz" in fehler and "Nachladen fehlgeschlagen" not in fehler, fehler
    assert not (main._pausierte_ort_ids() & BB), "die Orte wurden wegen des Kalenderfehlers wieder pausiert"
    assert main._store.lade_nachladen_kalender() == set()


def test_prozess_stirbt_im_kalender_schritt_chancen_bleiben_gueltig(client, kalender_server):
    """Rückgabewert ungleich 0, nachdem die Chancen schon fertig gemeldet waren (z. B. zu wenig Arbeitsspeicher beim
    Einlesen der großen Kalenderdatei): Chancen und Wetter gelten, es wird nur der Kalender als fehlend gemeldet."""
    import main
    s = kalender_server.spion
    s.rc = 137
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    kalender_server.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    _fort_schreiben(main, fertig=sorted(BB), feed_fertig=True, kalender=_kal("rechnet"))
    assert warte_bis(lambda: _info(client)["wetter_bereit"] == 2, WARTEZEIT)
    s.sperre.set()
    assert warte_bis(lambda: _info(client)["aktiv"] is False and s.beendet >= 1, WARTEZEIT)
    fehler = _info(client)["fehler"]
    assert fehler and "Kalender" in fehler and "Nachladen fehlgeschlagen" not in fehler, fehler
    assert main._store.lade_nachladen_kalender() == set()


def test_ausschalten_waehrend_der_kalenderphase_beendet_den_prozess_und_uebernimmt_nichts(client, kalender_server):
    import main
    welt = kalender_server.welt
    s = kalender_server.spion
    vorher = [termin(ort_id("berlin1"), zeit=_zeit(2), nr=1)]
    welt.setze_kalender(vorher)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    kalender_server.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    _fort_schreiben(main, fertig=sorted(BB), feed_fertig=True, kalender=_kal("rechnet"))
    assert warte_bis(lambda: _info(client)["phase"] == "kalender" or _info(client)["wetter_bereit"] == 2, WARTEZEIT)
    # ein Postfach liegt schon da (Prozess war fast fertig) — nach dem Ausschalten darf es nicht übernommen werden
    neue = [termin(i, zeit=_zeit(3), nr=3, typ="NEU") for i in BB]
    (kalender_server.cache / POSTFACH).write_text(
        json.dumps({"pid": 4711, "computed_at": "x", "location_ids": sorted(BB)}) + "\n"
        + "\n".join(json.dumps({"location_id": e["location_id"], "events": [e]}) for e in neue) + "\n", encoding="utf-8")
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert warte_bis(lambda: s.abgebrochen >= 1 and s.aktiv == 0, WARTEZEIT), "Prozess lief weiter"
    assert warte_bis(lambda: _info(client)["aktiv"] is False, WARTEZEIT)
    assert not [e for e in main._calendar_cache if e["event_type"] == "NEU"], "ein ausgeschaltetes Gebiet wurde übernommen"
    assert main._store.lade_nachladen_kalender() == set() and main._store.lade_nachladen() == set()
    assert not (main._recompute_pending & BB)


def test_nach_neustart_wird_nur_der_fehlende_kalender_nachgeholt(client, welt_z, monkeypatch):
    """Der Server wurde im Kalender-Schritt beendet: Cottbus steht als „Kalender offen“, seine Chancen stehen schon.
    Nach dem Start läuft ein Prozess nur mit --nur-kalender und nur für Cottbus (keine neue Chancenrechnung für
    Potsdam und keine für Cottbus)."""
    from us141_adapter import ProzessSpion
    s = ProzessSpion()
    s.sperre = threading.Event()
    welt_z.setze_feed(welt_z.termine_fuer(list(ORTE)))
    welt_z.store.merke_nachladen_kalender([ort_id("cottbus")])
    monkeypatch.setattr(asyncio, "create_subprocess_exec", s.fake_exec)
    import main

    def _pruefen():
        assert s.aktiv == 1 and len(s.starts) == 1, s.starts
        text = " ".join(str(a) for a in s.starts[0])
        assert "--nur-kalender" in text and ort_id("cottbus") in text and ort_id("potsdam") not in text
        assert "--feed-only" not in text

    try:
        _starte_server_neu(welt_z, monkeypatch, nachlaufzeit_s=1.0, pruefe=_pruefen)
    finally:
        s.sperre.set()


def test_nach_neustart_ort_mit_offenen_chancen_und_kalender_laeuft_komplett(client, welt_z, monkeypatch):
    """Fehlen bei einem Ort Chancen UND Kalender, läuft er im vollen Modus (Chancen, Wetter, Kalender) — nicht nur Kalender."""
    from us141_adapter import ProzessSpion
    s = ProzessSpion()
    s.sperre = threading.Event()
    welt_z.setze_feed(welt_z.termine_fuer([k for k in ORTE if k != "cottbus"]))
    welt_z.store.merke_nachladen([ort_id("cottbus")])
    welt_z.store.merke_nachladen_kalender([ort_id("cottbus")])
    monkeypatch.setattr(asyncio, "create_subprocess_exec", s.fake_exec)

    def _pruefen():
        assert len(s.starts) == 1, s.starts
        text = " ".join(str(a) for a in s.starts[0])
        assert "--mit-kalender" in text and "--feed-only" in text and "--nur-kalender" not in text

    try:
        _starte_server_neu(welt_z, monkeypatch, nachlaufzeit_s=1.0, pruefe=_pruefen)
    finally:
        s.sperre.set()


def test_postfach_wird_nur_vom_eigenen_prozess_uebernommen_und_laedt_nie_die_ganze_datei(client, welt_z, monkeypatch):
    """Ein veraltetes Postfach (andere Prozessnummer) wird ignoriert; ist der Kalender im Arbeitsspeicher leer, wird die
    große Datei NICHT neu eingelesen (das hielte den Server an)."""
    import main
    cache = welt_z.tmp / "cache"
    cache.mkdir(exist_ok=True)
    monkeypatch.setattr(main, "_CAL_CACHE", cache / "calendar.json")
    (cache / POSTFACH).write_text(
        json.dumps({"pid": 1, "computed_at": "x", "location_ids": ["a"]}) + "\n"
        + json.dumps({"location_id": ort_id("potsdam"), "events": [termin(ort_id("potsdam"), zeit=_zeit(2))]}) + "\n",
        encoding="utf-8")
    welt_z.setze_kalender([termin(ort_id("berlin1"), zeit=_zeit(1))])
    assert asyncio.run(main._apply_calendar_nachladen([ort_id("potsdam")], pid=2)) is False
    assert [e["location_id"] for e in main._calendar_cache] == [ort_id("berlin1")]
    welt_z.setze_kalender([])
    aufgerufen = []
    monkeypatch.setattr(main, "_load_calendar_cache", lambda *a, **k: aufgerufen.append(1))
    assert asyncio.run(main._apply_calendar_nachladen([ort_id("potsdam")], pid=1)) is False
    assert not aufgerufen and main._calendar_cache == []


# ── Oberfläche (nur der Text, kein Browser) ──────────────────────────────────

@pytest.mark.requires_full_checkout
def test_fortschrittstext_nennt_den_kalender_schritt():
    html = (Path(__file__).resolve().parent.parent.parent / "web" / "index.html").read_text(encoding="utf-8")
    assert "Kalender wird ergänzt" in html
    assert "Wetter folgt" in html and "Wetter wird geholt" in html     # die bisherigen Texte bleiben
