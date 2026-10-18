"""US-141 Baustein 3 (eigene Ergänzung, 2026-10-15) — was die vorgegebenen Nachlade-Tests nicht abdecken:
  * der gebündelte Rechenlauf selbst (precompute --location-ids): rechnet nur die genannten, aktiven Orte,
    schreibt höchstens EIN Backup je Lauf und meldet seinen Fortschritt in einer kleinen Datei;
  * der Nachtlauf überschreibt nachgeladene Orte nicht (Kollision zwischen Nachtlauf und Nachladen);
  * der gespeicherte Nachlade-Zustand überlebt einen Neustart (auch für Orte, die schon Chancen haben);
  * die Oberfläche bekommt den Fortschritt („x von y Orten bereit“, Restzeit) über /areas und die Antwort
    auf das Schalten; ein fehlgeschlagener Lauf wird ehrlich gemeldet;
  * Ausschalten beendet den laufenden Rechenprozess wirklich.
Alles offline (Prozess-Spion, gestubbte Astronomie), Python-3.9-kompatibel.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import threading

import pytest

from us141_adapter import (  # noqa: F401  (Fixtures)
    ORTE, als_host, host_schaltet_region, ort_id, warte_bis, welt, welt_z,
)
from test_us141_nachladen import _offene_auftraege, _starte_server_neu, nachladen  # noqa: F401

pytestmark = [pytest.mark.api, pytest.mark.regression]

BB = {ort_id("potsdam"), ort_id("cottbus")}
ALLE = {ort_id(k) for k in ORTE}
WARTEZEIT = 8.0


def _gruppenlauf(monkeypatch, welt, ids, feed_only=True):
    """Führt precompute.main mit --location-ids im selben Prozess aus (gestubbte Astronomie, Backup-Zähler)."""
    import precompute as P
    from data import backup as _backup
    gerechnet: list = []
    sicherungen = {"vorher": 0, "nachher": 0}

    async def _fake_opps(loc, *a, **k):
        gerechnet.append(loc.id)
        return []

    async def _fake_hoehen(*a, **k):
        return {}

    def _vorher():
        sicherungen["vorher"] += 1

    def _nachher():
        sicherungen["nachher"] += 1

    monkeypatch.setattr(_backup, "snapshot_before_precompute", _vorher)
    monkeypatch.setattr(_backup, "backup_after_precompute", _nachher)
    monkeypatch.setattr(P, "LocationStore", lambda *a, **k: welt.store)
    monkeypatch.setattr(P, "CACHE_DIR", welt.tmp / "cache")
    monkeypatch.setattr(P, "find_opportunities_multi_day", _fake_opps)
    monkeypatch.setattr(P, "fetch_elevations", _fake_hoehen)
    args = argparse.Namespace(feed_only=feed_only, calendar_only=False, full=False, location_id=None,
                              location_ids=",".join(sorted(ids)))
    asyncio.run(P.main(args))
    return gerechnet, sicherungen, welt.tmp / "cache"


def test_gruppenlauf_rechnet_nur_die_genannten_orte_mit_einem_backup_und_meldet_fortschritt(client, welt_z, monkeypatch):
    """Ein Lauf für Brandenburg: nur Potsdam und Cottbus werden gerechnet, genau ein Backup vorher und eines nachher,
    die Termine der übrigen Orte bleiben in der Feed-Datei, die Fortschrittsdatei nennt beide Orte als fertig."""
    (welt_z.tmp / "cache").mkdir(exist_ok=True)
    feed = welt_z.tmp / "cache" / "opportunities.json"
    termine = welt_z.termine_fuer(list(ORTE.keys()))
    feed.write_text(json.dumps({"computed_at": "2026-10-11T00:00:00+00:00", "opportunities": termine}), encoding="utf-8")
    gerechnet, sicherungen, cache = _gruppenlauf(monkeypatch, welt_z, BB)
    assert set(gerechnet) == BB, "gerechnet wurde für: %s" % sorted(gerechnet)
    assert sicherungen == {"vorher": 1, "nachher": 1}, "mehr als ein Backup je Lauf: %s" % sicherungen
    daten = json.loads(feed.read_text(encoding="utf-8"))
    ids = {e["location_id"] for e in daten["opportunities"]}
    assert not (ids & BB), "alte Termine der neu gerechneten Orte blieben stehen (die Attrappe liefert keine neuen)"
    assert (ALLE - BB) <= ids, "Termine anderer Orte gingen verloren: %s" % sorted((ALLE - BB) - ids)
    fort = json.loads((cache / "nachladen_fortschritt.json").read_text(encoding="utf-8"))
    assert set(fort["fertig"]) == BB and fort["gesamt"] == 2 and not fort["fehler"]


def test_gruppenlauf_rechnet_pausierte_orte_nicht(client, welt_z, monkeypatch):
    """Ist Brandenburg aus, wird es auch dann nicht gerechnet, wenn es in der Liste steht; aktive Orte der Liste schon."""
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    gerechnet, _s, _c = _gruppenlauf(monkeypatch, welt_z, BB | {ort_id("berlin1")})
    assert set(gerechnet) == {ort_id("berlin1")}


def test_nachtlauf_ueberschreibt_waehrend_des_laufs_nachgeladene_orte_nicht(client, welt_z, monkeypatch):
    """Kollision: Der Nachtlauf startet, solange Brandenburg aus ist; mitten im Lauf wird Brandenburg eingeschaltet
    und nachgeladen (die Feed-Datei bekommt dessen Termine). Das Ergebnis des Nachtlaufs darf diese Termine nicht
    löschen."""
    import precompute as P
    from data import backup as _backup
    from data import gebiet_zustand as gz
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    (welt_z.tmp / "cache").mkdir(exist_ok=True)
    feed = welt_z.tmp / "cache" / "opportunities.json"
    feed.write_text(json.dumps({"computed_at": "2026-10-11T00:00:00+00:00", "opportunities": []}), encoding="utf-8")
    zustand = {"schon": False}

    async def _fake_opps(loc, *a, **k):
        if not zustand["schon"]:
            zustand["schon"] = True
            welt_z.store.set_area_states_bulk(gz.eintraege_fuer_region("Deutschland", "Brandenburg", True))
            feed.write_text(json.dumps({"computed_at": "2026-10-15T12:00:00+00:00",
                                        "opportunities": welt_z.termine_fuer(["potsdam", "cottbus"])}), encoding="utf-8")
        return []

    async def _fake_hoehen(*a, **k):
        return {}

    monkeypatch.setattr(_backup, "snapshot_before_precompute", lambda: None)
    monkeypatch.setattr(_backup, "backup_after_precompute", lambda: None)
    monkeypatch.setattr(P, "LocationStore", lambda *a, **k: welt_z.store)
    monkeypatch.setattr(P, "CACHE_DIR", welt_z.tmp / "cache")
    monkeypatch.setattr(P, "find_opportunities_multi_day", _fake_opps)
    monkeypatch.setattr(P, "fetch_elevations", _fake_hoehen)
    asyncio.run(P.main(argparse.Namespace(feed_only=True, calendar_only=False, full=False, location_id=None)))
    ids = {e["location_id"] for e in json.loads(feed.read_text(encoding="utf-8"))["opportunities"]}
    assert BB <= ids, "der Nachtlauf hat nachgeladene Termine überschrieben: %s" % sorted(ids)


def test_gespeicherter_nachlade_zustand_setzt_auch_orte_mit_chancen_nach_dem_neustart_fort(client, welt_z, monkeypatch):
    """Der Server wurde mitten im Nachladen beendet: Cottbus steht als offen in der Datenbank, obwohl alte Termine da
    sind. Nach dem Start wird für Cottbus (und nur dafür) nachgeladen; ein Ort, der nicht mehr aktiv ist, wird aus
    dem gespeicherten Zustand gestrichen."""
    from us141_adapter import ProzessSpion
    s = ProzessSpion()
    s.sperre = threading.Event()
    host_schaltet_region(client, "Vereinigtes Königreich (UK)", "England", False)
    welt_z.setze_feed(welt_z.termine_fuer([k for k in ORTE if k not in ("london1", "london2")]))
    welt_z.store.merke_nachladen([ort_id("cottbus"), ort_id("london1")])
    monkeypatch.setattr(asyncio, "create_subprocess_exec", s.fake_exec)
    import main

    def _pruefen():
        assert s.ids_in_starts({ort_id("cottbus")}) == {ort_id("cottbus")}
        assert not s.ids_in_starts({ort_id("london1"), ort_id("berlin1")})
        assert ort_id("cottbus") in main._recompute_pending

    try:
        _starte_server_neu(welt_z, monkeypatch, nachlaufzeit_s=1.0, pruefe=_pruefen)
    finally:
        s.sperre.set()
    assert ort_id("london1") not in main._store.lade_nachladen(), "pausierter Ort blieb im gespeicherten Zustand"


def test_areas_und_antwort_melden_fortschritt_und_restzeit(client, nachladen):
    """Die Oberfläche sieht den Stand: während des Nachladens aktiv, 2 Orte gesamt, Gebiet Brandenburg, Restzeit
    mindestens eine Minute; die Antwort auf das Einschalten trägt denselben Block. Danach nicht mehr aktiv."""
    s = nachladen.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    nachladen.scharf()
    als_host(client)
    r = client.put("/areas/Deutschland/Brandenburg", json={"enabled": True})
    assert r.status_code == 200, r.text
    assert r.json()["nachladen"]["aktiv"] is True
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    info = client.get("/areas").json()["nachladen"]
    assert info["aktiv"] is True and info["gesamt"] == 2 and info["chancen_bereit"] == 0
    assert info["rest_min"] >= 1
    assert [g["name"] for g in info["gebiete"]] == ["Brandenburg"] and info["gebiete"][0]["gesamt"] == 2
    s.sperre.set()
    assert warte_bis(lambda: client.get("/areas").json()["nachladen"]["aktiv"] is False, WARTEZEIT)
    assert not (_offene_auftraege(client) & BB)


def test_fehlgeschlagener_lauf_wird_in_areas_ehrlich_gemeldet(client, nachladen):
    s = nachladen.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.rc = 1
    nachladen.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: client.get("/areas").json()["nachladen"]["aktiv"] is False and s.beendet >= 1, WARTEZEIT)
    info = client.get("/areas").json()["nachladen"]
    assert info["fehler"], "ein fehlgeschlagener Lauf wird nicht gemeldet"


def test_ausschalten_beendet_den_rechenprozess_wirklich(client, nachladen):
    s = nachladen.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    nachladen.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert warte_bis(lambda: s.abgebrochen >= 1 and s.aktiv == 0, WARTEZEIT), "Prozess lief weiter"
    assert warte_bis(lambda: client.get("/areas").json()["nachladen"]["aktiv"] is False, WARTEZEIT)
