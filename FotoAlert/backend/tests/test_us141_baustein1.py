"""US-141 Baustein 1 (Ergänzung zur Umsetzung): Speicher-Tabelle für den Ein-/Aus-Zustand je Land und
Region, Sammelschalter-Ableitung aus dem Gespeicherten, einmalige Übernahme (Migration) und die
Schreib-Hilfen für Feed/Kalender (Dateisperre, atomares Schreiben, Aufräumen nach dem Löschen).

Diese Tests prüfen nur, was in Baustein 1 gebaut ist; die Schalter-Adressen, das Menü und das
direkte Nachladen (Baustein 2/3) haben eigene Dateien. Alle Tests laufen offline mit eigener
temporärer Datenbank bzw. Datei, ohne die echten Cache-Dateien oder die Entwicklungsdatenbank.
"""
import json
import threading
from pathlib import Path

import pytest

from data import aktiv_regel, cache_io, gebiete, regionen
from data.store import LocationStore

pytestmark = [pytest.mark.offline, pytest.mark.regression]

ORTE = [
    {"id": "a", "lat": 52.52, "lon": 13.40},                 # Berlin
    {"id": "b", "lat": 51.5, "lon": -0.12},                  # London
    {"id": "c", "lat": -30.0, "lon": 20.0},                  # Sonstige
    {"id": "d", "lat": 48.2, "lon": 16.4, "deleted": True},  # Wien, aber gelöscht
]


@pytest.fixture
def store(tmp_path):
    return LocationStore(tmp_path / "t.db")


def test_tabelle_speichert_und_liest_zustand(store):
    assert store.load_area_states() == {"laender": {}, "regionen": {}}
    store.set_area_state("Deutschland", "Bayern", False)
    store.set_area_state("Sonstige", "", False)
    z = store.load_area_states()
    assert z["regionen"] == {("Deutschland", "Bayern"): False}
    assert z["laender"] == {"Sonstige": False}
    store.set_area_state("Deutschland", "Bayern", True)   # überschreibt
    assert store.load_area_states()["regionen"][("Deutschland", "Bayern")] is True
    assert store.area_state_count() == 2


def test_sammelschalter_aus_gespeichertem_zustand(store):
    regs = regionen.REGIONEN["Deutschland"]
    assert aktiv_regel.land_zustand("Deutschland", regs, store.load_area_states()) == "an"
    store.set_area_state("Deutschland", "Berlin", False)
    assert aktiv_regel.land_zustand("Deutschland", regs, store.load_area_states()) == "teilweise"
    store.set_area_states_bulk([("Deutschland", r, False) for r in regs])
    assert aktiv_regel.land_zustand("Deutschland", regs, store.load_area_states()) == "aus"


def test_startzustand_nur_belegte_gebiete_an():
    e = {(l, r): a for (l, r, a) in gebiete.standard_zustaende(ORTE)}
    assert e[("Deutschland", "Berlin")] is True
    assert e[(regionen.LAND_UK, "England")] is True
    assert e[("Sonstige", "")] is True
    assert e[("Österreich", "Wien")] is False   # nur ein gelöschter Ort dort
    assert e[("Deutschland", "Bayern")] is False
    assert len(e) == 121


def test_migration_ist_wiederholbar_und_ueberschreibt_nichts(store):
    r1 = gebiete.migriere_gebietszustand(store, ORTE)
    assert r1["neu"] > 0 and r1["sicherung"] is not None
    assert Path(r1["sicherung"]).exists()
    store.set_area_state("Deutschland", "Berlin", False)   # jemand hat geschaltet
    r2 = gebiete.migriere_gebietszustand(store, ORTE)
    assert r2["neu"] == 0 and r2["sicherung"] is None
    assert store.load_area_states()["regionen"][("Deutschland", "Berlin")] is False


def test_migration_aendert_keine_ortsdaten(store):
    import sqlite3
    store.upsert_override("x1", name="Test")
    def inhalt():
        with sqlite3.connect(str(store.db_path)) as c:
            return (c.execute("SELECT id, fields FROM location_overrides").fetchall(),
                    c.execute("SELECT COUNT(*) FROM custom_locations").fetchone())
    vorher = inhalt()
    gebiete.migriere_gebietszustand(store, ORTE)
    assert inhalt() == vorher and vorher[0]


def test_atomares_schreiben_laesst_alte_datei_bei_fehler(tmp_path, monkeypatch):
    f = tmp_path / "feed.json"
    cache_io.atomar_schreiben(f, "alt")
    def kaputt(self, *a, **k):
        raise OSError("Platte voll")
    monkeypatch.setattr(Path, "write_text", kaputt)
    with pytest.raises(OSError):
        cache_io.atomar_schreiben(f, "neu")
    monkeypatch.undo()
    assert f.read_text() == "alt"
    assert not [p for p in tmp_path.iterdir() if ".tmp-" in p.name]


def test_gleichzeitige_schreiber_verlieren_nichts(tmp_path):
    f = tmp_path / "zaehler.json"
    f.write_text("0")
    def arbeit():
        for _ in range(25):
            with cache_io.gesperrt_aendern(f):
                n = int(f.read_text())
                cache_io.atomar_schreiben(f, str(n + 1))
    ts = [threading.Thread(target=arbeit) for _ in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert int(f.read_text()) == 100


def test_orte_aus_feed_entfernen(tmp_path):
    f = tmp_path / "opportunities.json"
    f.write_text(json.dumps({"computed_at": "x", "opportunities": [
        {"location_id": "a", "n": 1}, {"location_id": "b", "n": 2}, {"location_id": "a", "n": 3}]}))
    assert cache_io.orte_aus_feed_entfernen(f, ["a"]) == 2
    d = json.loads(f.read_text())
    assert d["computed_at"] == "x" and [e["location_id"] for e in d["opportunities"]] == ["b"]
    assert cache_io.orte_aus_feed_entfernen(f, ["a"]) == 0
    assert cache_io.orte_aus_feed_entfernen(tmp_path / "fehlt.json", ["a"]) == 0
