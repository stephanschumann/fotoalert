"""BUG-118 — Gelöschte Orte kommen zurück: die nächtliche Vorberechnung beachtet die
Lösch-Markierung nicht, und beim Löschen bleibt die Feed-Datei auf der Festplatte unverändert.

Diese Tests entstanden in der Analyse-Phase (test-first, 2026-10-11, im Bundle mit US-141)
und beschreiben die ANFORDERUNG, nicht eine bestimmte Umsetzung:
  - AK1: Nach dem Löschen eines Orts (Standard-Ort UND eigener Ort) enthält die Feed-Datei
    auf der Festplatte keine Termine dieses Orts mehr; die Termine der übrigen Orte bleiben.
  - AK2: Nach einem Neustart (Feed-Datei wird neu eingelesen) tauchen die Termine des
    gelöschten Orts nicht wieder auf.
  - AK3: Die Einzel-Neuberechnung eines ANDEREN Orts bringt die Termine des gelöschten
    Orts nicht zurück.
  - AK4: Ein Feed, in dem noch Termine eines gelöschten Standard-Orts stehen (z. B. von
    einem alten Lauf), wird beim Einlesen um diese Termine bereinigt; Termine bestehender
    Orte bleiben.
  - AK5: Die Vorberechnung (eigener Prozess) rechnet gelöschte Standard-Orte nicht mehr
    mit; alle nicht gelöschten Orte (Standard und eigene) rechnet sie weiter.

Alle Tests laufen offline: eigene temporäre Datenbank und Feed-Datei je Test, kein Netz,
keine echte Ephemeride; die echten Cache-Dateien und die geteilte Entwicklungsdatenbank
werden nie angefasst (Test-Isolation laut Orchestrator-Regel).
"""
import argparse
import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

import main
import precompute as P
from data.locations import LOCATIONS as _GETEILTE_LISTE, LocationCategory, PhotoLocation
from data.store import LocationStore

pytestmark = [pytest.mark.offline, pytest.mark.regression]

STD_WEG = "std_test_bug118_weg"
STD_BLEIBT = "std_test_bug118_bleibt"
EIGEN_WEG = "custom_test_bug118_weg"
EIGEN_BLEIBT = "custom_test_bug118_bleibt"


def _ort(loc_id: str) -> PhotoLocation:
    return PhotoLocation(
        id=loc_id, name=f"Testort {loc_id}", description="BUG-118-Testort",
        category=LocationCategory.SKYLINE,
        observer_lat=52.5, observer_lon=13.4,
        subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
    )


def _custom_dict(loc: PhotoLocation) -> dict:
    return {
        "id": loc.id, "name": loc.name, "description": loc.description,
        "category": loc.category.name,
        "observer_lat": loc.observer_lat, "observer_lon": loc.observer_lon,
        "subject_lat": loc.subject_lat, "subject_lon": loc.subject_lon,
        "subject_name": loc.subject_name, "subject_height_m": 0, "subject_width_m": 0,
        "distance_m": 1000, "focal_length_suggestions": [], "special_notes": "",
        "difficulty": 1, "observer_floor_height_m": 0.0,
    }


def _termin(loc_id: str) -> dict:
    zeit = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    return {
        "location_id": loc_id, "location_name": f"Testort {loc_id}", "shoot_time": zeit,
        "overall_score": 0.8, "observer_lat": 52.5, "observer_lon": 13.4,
    }


def _ids_in_feed_datei(pfad) -> set:
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    return {e["location_id"] for e in daten["opportunities"]}


@pytest.fixture
def umgebung(monkeypatch, tmp_path):
    """Isolierte Welt: eigene Datenbank + eigene Feed-Datei mit Terminen aller vier
    Testorte; die Ortsliste der App enthält die vier Testorte."""
    store = LocationStore(db_path=tmp_path / "bug118.db")
    orte = {i: _ort(i) for i in (STD_WEG, STD_BLEIBT, EIGEN_WEG, EIGEN_BLEIBT)}
    store.create_custom(_custom_dict(orte[EIGEN_WEG]))
    store.create_custom(_custom_dict(orte[EIGEN_BLEIBT]))

    feed = tmp_path / "opportunities.json"
    termine = [_termin(i) for i in orte]
    feed.write_text(json.dumps({"computed_at": "2026-10-11T00:00:00+00:00",
                                "opportunities": termine}), encoding="utf-8")

    monkeypatch.setattr(main, "_store", store)
    monkeypatch.setattr(main, "_OPP_CACHE", feed)
    monkeypatch.setattr(main, "LOCATIONS", list(orte.values()))
    monkeypatch.setattr(main, "_feed_cache", list(termine))
    monkeypatch.setattr(main, "_calendar_cache", [])
    monkeypatch.setattr(main, "_NO_BACKGROUND", True)
    return {"store": store, "feed": feed, "orte": orte}


def _loesche(loc_id: str) -> None:
    asyncio.run(main.delete_location(loc_id, _role="host"))


# ---------------------------------------------------------------------------
# AK1 — Löschen räumt auch die Feed-Datei auf der Festplatte auf
# ---------------------------------------------------------------------------

def test_loeschen_standardort_entfernt_termine_aus_feed_datei(umgebung):
    """BUG-118 AK1: Standard-Ort löschen -> Feed-Datei ohne seine Termine, übrige bleiben."""
    _loesche(STD_WEG)
    ids = _ids_in_feed_datei(umgebung["feed"])
    assert STD_WEG not in ids, "Feed-Datei enthält nach dem Löschen noch Termine des gelöschten Standard-Orts"
    assert {STD_BLEIBT, EIGEN_WEG, EIGEN_BLEIBT} <= ids, "Termine anderer Orte dürfen nicht verschwinden"


def test_loeschen_eigener_ort_entfernt_termine_aus_feed_datei(umgebung):
    """BUG-118 AK1 (zweiter Weg): auch bei eigenen Orten bleibt die Feed-Datei sonst unverändert."""
    _loesche(EIGEN_WEG)
    ids = _ids_in_feed_datei(umgebung["feed"])
    assert EIGEN_WEG not in ids, "Feed-Datei enthält nach dem Löschen noch Termine des gelöschten eigenen Orts"
    assert {STD_WEG, STD_BLEIBT, EIGEN_BLEIBT} <= ids


# ---------------------------------------------------------------------------
# AK2 — nach Neustart bleibt der gelöschte Ort weg
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("weg", [STD_WEG, EIGEN_WEG])
def test_nach_neustart_keine_termine_des_geloeschten_orts(umgebung, monkeypatch, weg):
    """BUG-118 AK2: Neustart = Feed-Datei neu einlesen; gelöschter Ort bleibt weg."""
    _loesche(weg)
    monkeypatch.setattr(main, "_feed_cache", [])
    assert main._load_feed_cache() is True
    ids = {e["location_id"] for e in main._feed_cache}
    assert weg not in ids, "Nach dem Neustart sind Termine des gelöschten Orts wieder im Feed"
    assert STD_BLEIBT in ids


# ---------------------------------------------------------------------------
# AK3 — Einzel-Neuberechnung eines anderen Orts bringt nichts zurück
# ---------------------------------------------------------------------------

def test_einzelberechnung_anderer_ort_bringt_geloeschten_ort_nicht_zurueck(umgebung):
    """BUG-118 AK3: Die Einzelberechnung übernimmt die bestehende Feed-Datei und mischt
    die neuen Termine EINES Orts ein — gelöschte Orte dürfen darin nicht mehr stehen."""
    _loesche(STD_WEG)
    P._merge_and_write_feed(umgebung["feed"], STD_BLEIBT, [_termin(STD_BLEIBT)],
                            "2026-10-11T01:00:00+00:00")
    ids = _ids_in_feed_datei(umgebung["feed"])
    assert STD_WEG not in ids, "Einzelberechnung eines anderen Orts hat den gelöschten Ort zurückgebracht"
    assert STD_BLEIBT in ids


# ---------------------------------------------------------------------------
# AK4 — Einlesen sortiert Termine gelöschter Orte aus
# ---------------------------------------------------------------------------

def test_einlesen_sortiert_termine_geloeschter_standardorte_aus(umgebung, monkeypatch):
    """BUG-118 AK4: Die Feed-Datei (z. B. frisch von der Vorberechnung) enthält noch
    Termine eines gelöschten Standard-Orts (Lösch-Markierung gesetzt, Ort nicht mehr in
    der Ortsliste). Beim Einlesen werden sie nicht übernommen."""
    umgebung["store"].upsert_override(STD_WEG, deleted=True)
    monkeypatch.setattr(main, "LOCATIONS", [o for i, o in umgebung["orte"].items() if i != STD_WEG])
    monkeypatch.setattr(main, "_feed_cache", [])
    assert main._load_feed_cache() is True
    ids = {e["location_id"] for e in main._feed_cache}
    assert STD_WEG not in ids, "Termine des gelöschten Standard-Orts wurden eingelesen"
    assert {STD_BLEIBT, EIGEN_WEG, EIGEN_BLEIBT} <= ids, "Termine bestehender Orte müssen erhalten bleiben"


# ---------------------------------------------------------------------------
# AK5 — Vorberechnung (eigener Prozess) beachtet die Lösch-Markierung
# ---------------------------------------------------------------------------

def _vorberechnung_laufen_lassen(monkeypatch, tmp_path, store) -> list:
    """Startet die Vorberechnung (nur Feed, alle Orte) mit gestubbter Astronomie/Netz und
    liefert die IDs aller Orte, für die tatsächlich gerechnet wurde."""
    gerechnet: list = []

    async def _fake_opps(loc, *a, **k):
        gerechnet.append(loc.id)
        return []

    async def _fake_hoehen(*a, **k):
        return {}

    from data import backup as _backup
    monkeypatch.setattr(_backup, "snapshot_before_precompute", lambda: None)
    monkeypatch.setattr(_backup, "backup_after_precompute", lambda: None)
    monkeypatch.setattr(P, "LocationStore", lambda *a, **k: store)
    monkeypatch.setattr(P, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(P, "find_opportunities_multi_day", _fake_opps)
    monkeypatch.setattr(P, "fetch_elevations", _fake_hoehen)

    vorher = list(_GETEILTE_LISTE)
    _GETEILTE_LISTE[:] = [_ort(STD_WEG), _ort(STD_BLEIBT)]
    try:
        args = argparse.Namespace(feed_only=True, calendar_only=False, full=False, location_id=None)
        asyncio.run(P.main(args))
    finally:
        _GETEILTE_LISTE[:] = vorher
    return gerechnet


def test_vorberechnung_rechnet_geloeschten_standardort_nicht_mehr(monkeypatch, tmp_path, umgebung):
    """BUG-118 AK5a: Standard-Ort mit Lösch-Markierung wird von der Vorberechnung nicht
    mehr berechnet (sonst kommen seine Chancen nach dem Nachtlauf zurück)."""
    umgebung["store"].upsert_override(STD_WEG, deleted=True)
    gerechnet = _vorberechnung_laufen_lassen(monkeypatch, tmp_path, umgebung["store"])
    assert STD_WEG not in gerechnet, "Vorberechnung rechnet den gelöschten Standard-Ort weiter mit"


def test_vorberechnung_rechnet_nicht_geloeschte_orte_weiter(monkeypatch, tmp_path, umgebung):
    """BUG-118 AK5b (Gegenfall): Standard-Ort ohne Markierung und eigene Orte werden
    weiterhin berechnet — der Fix darf nicht zu viel ausschließen."""
    umgebung["store"].upsert_override(STD_WEG, deleted=True)
    gerechnet = _vorberechnung_laufen_lassen(monkeypatch, tmp_path, umgebung["store"])
    assert STD_BLEIBT in gerechnet
    assert EIGEN_BLEIBT in gerechnet
