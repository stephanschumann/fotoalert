"""
Tests für TASK-59 Option E: lokale Batch-Cache-Datei statt Live-Overpass-
Anfrage (`backend/data/qa_azimuth.py`).

Alle Tests laufen komplett offline/gemockt — kein echtes Netzwerk, keine
echte PBF-Datei. Deckt ab:
- `_load_building_cache()`: fehlende/fehlerhafte Datei -> leere Liste statt
  Crash (Live-Mirror-Pfad bleibt die einzige Datenquelle in diesem Fall).
- `_find_local_cache_entry()`: Koordinaten-Abgleich mit Toleranz, inkl. dem
  Fall "Koordinate seither geändert -> kein Treffer mehr".
- `_nearest_building_nodes()`: Auswahl des nächstgelegenen Gebäudes.
- Integration in `_fetch_overpass_footprint()` und `fetch_buildings_along_line()`:
  ein Cache-Treffer beendet die Funktion OHNE Live-Netzanfrage (auch bei
  leerer Gebäudeliste = "bestätigt kein Gebäude in der Nähe"); ein Cache-Miss
  lässt den bisherigen Live-Mirror-Pfad unverändert weiterlaufen.

Python-3.9-kompatibel.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data import qa_azimuth

pytestmark = [pytest.mark.offline, pytest.mark.regression]


@pytest.fixture(autouse=True)
def _reset_building_cache_singleton(monkeypatch):
    """Der Modul-Cache (_building_cache_entries) ist ein Prozess-weiter
    Singleton (lazy geladen, einmal pro Prozesslaufzeit) — für isolierte
    Tests vor JEDEM Test auf 'noch nicht geladen' zurücksetzen."""
    monkeypatch.setattr(qa_azimuth, "_building_cache_entries", None)


@pytest.fixture(autouse=True)
def _no_rate_limit_sleep(monkeypatch):
    monkeypatch.setattr(qa_azimuth, "_respect_overpass_rate_limit", lambda: None)


class _FailIfCalledClient:
    """Fake httpx.Client, der bei JEDEM Aufruf fehlschlägt — verwendet um zu
    beweisen, dass eine Funktion bei einem Cache-Treffer GAR KEINE
    Live-Netzanfrage mehr auslöst (calls bleibt leer)."""

    calls: list = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, data=None):
        _FailIfCalledClient.calls.append(url)
        raise httpx.ConnectError("darf hier nie aufgerufen werden")


def _write_cache_file(path: Path, locations: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "generated_at": "2026-08-02T00:00:00Z",
        "source": "test-fixture",
        "radius_m": 200,
        "location_count": len(locations),
        "locations": locations,
    }), encoding="utf-8")


# ---------------------------------------------------------------------------
# _load_building_cache
# ---------------------------------------------------------------------------

def test_load_building_cache_fehlende_datei_gibt_leere_liste(monkeypatch, tmp_path):
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", tmp_path / "does_not_exist.json")

    result = qa_azimuth._load_building_cache()

    assert result == []


def test_load_building_cache_fehlerhaftes_json_gibt_leere_liste_statt_crash(monkeypatch, tmp_path, caplog):
    bad_file = tmp_path / "building_footprints.json"
    bad_file.write_text("{ das ist kein valides JSON", encoding="utf-8")
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", bad_file)

    with caplog.at_level("WARNING", logger="data.qa_azimuth"):
        result = qa_azimuth._load_building_cache()

    assert result == []
    assert any("nicht lesbar" in r.getMessage() for r in caplog.records)


def test_load_building_cache_laedt_gueltige_datei_und_cached_ergebnis(monkeypatch, tmp_path):
    cache_file = tmp_path / "building_footprints.json"
    _write_cache_file(cache_file, [{
        "location_id": "test_loc",
        "observer_lat": 52.5, "observer_lon": 13.4,
        "subject_lat": 52.501, "subject_lon": 13.401,
        "buildings": [],
    }])
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", cache_file)

    first = qa_azimuth._load_building_cache()
    # Datei danach "entfernen" (Pfad ungültig machen) -> zweiter Aufruf muss
    # trotzdem das gecachte Ergebnis liefern, kein erneutes Lesen.
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", tmp_path / "gone.json")
    second = qa_azimuth._load_building_cache()

    assert first == second
    assert len(first) == 1
    assert first[0]["location_id"] == "test_loc"


# ---------------------------------------------------------------------------
# _find_local_cache_entry
# ---------------------------------------------------------------------------

def test_find_local_cache_entry_treffer_bei_gleicher_motiv_koordinate(monkeypatch, tmp_path):
    cache_file = tmp_path / "building_footprints.json"
    _write_cache_file(cache_file, [{
        "location_id": "brandenburger_tor",
        "observer_lat": 52.5162, "observer_lon": 13.3776,
        "subject_lat": 52.5163, "subject_lon": 13.3777,
        "buildings": [{"nodes": [[52.5163, 13.3777], [52.5164, 13.3778], [52.5162, 13.3779]],
                        "height_m": 26.0}],
    }])
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", cache_file)

    entry = qa_azimuth._find_local_cache_entry(52.5163, 13.3777)

    assert entry is not None
    assert entry["location_id"] == "brandenburger_tor"


def test_find_local_cache_entry_kein_treffer_bei_geaenderter_koordinate(monkeypatch, tmp_path):
    """Wurde die Motiv-Koordinate seit dem letzten Batch-Lauf spürbar
    korrigiert (hier: ~1km Versatz), darf KEIN Treffer entstehen — die
    Funktion muss automatisch auf den Live-Pfad zurückfallen."""
    cache_file = tmp_path / "building_footprints.json"
    _write_cache_file(cache_file, [{
        "location_id": "brandenburger_tor",
        "observer_lat": 52.5162, "observer_lon": 13.3776,
        "subject_lat": 52.5163, "subject_lon": 13.3777,
        "buildings": [],
    }])
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", cache_file)

    entry = qa_azimuth._find_local_cache_entry(52.526, 13.388)  # ~1km entfernt

    assert entry is None


def test_find_local_cache_entry_beruecksichtigt_beobachter_koordinate_wenn_angegeben(monkeypatch, tmp_path):
    cache_file = tmp_path / "building_footprints.json"
    _write_cache_file(cache_file, [{
        "location_id": "loc_a",
        "observer_lat": 52.50, "observer_lon": 13.40,
        "subject_lat": 52.51, "subject_lon": 13.41,
        "buildings": [],
    }])
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", cache_file)

    # Motiv-Koordinate stimmt, Standort-Koordinate ist eine andere (z.B. weil
    # zwei Locations dasselbe Motiv von unterschiedlichen Standorten zeigen).
    entry = qa_azimuth._find_local_cache_entry(52.51, 13.41, observer_lat=52.60, observer_lon=13.50)

    assert entry is None


# ---------------------------------------------------------------------------
# _nearest_building_nodes
# ---------------------------------------------------------------------------

def test_nearest_building_nodes_waehlt_naechstgelegenen_schwerpunkt():
    subject_lat, subject_lon = 52.5163, 13.3777
    near = {"nodes": [[52.5163, 13.3777], [52.5164, 13.3778], [52.5162, 13.3779]], "height_m": 10.0}
    far = {"nodes": [[52.60, 13.50], [52.601, 13.501], [52.599, 13.502]], "height_m": 10.0}

    result = qa_azimuth._nearest_building_nodes(subject_lat, subject_lon, [far, near])

    assert result == [(52.5163, 13.3777), (52.5164, 13.3778), (52.5162, 13.3779)]


def test_nearest_building_nodes_leere_liste_gibt_none():
    assert qa_azimuth._nearest_building_nodes(52.5, 13.4, []) is None


def test_nearest_building_nodes_ignoriert_entartetes_polygon_unter_3_knoten():
    degenerate = {"nodes": [[52.5, 13.4], [52.501, 13.401]], "height_m": 5.0}
    assert qa_azimuth._nearest_building_nodes(52.5, 13.4, [degenerate]) is None


# ---------------------------------------------------------------------------
# Integration: _fetch_overpass_footprint nutzt den lokalen Cache primär
# ---------------------------------------------------------------------------

def test_fetch_overpass_footprint_cache_treffer_ruft_kein_live_netz_auf(monkeypatch, tmp_path):
    cache_file = tmp_path / "building_footprints.json"
    _write_cache_file(cache_file, [{
        "location_id": "loc_a",
        "observer_lat": 52.50, "observer_lon": 13.40,
        "subject_lat": 52.51, "subject_lon": 13.41,
        "buildings": [{"nodes": [[52.51, 13.41], [52.5101, 13.4101], [52.5099, 13.4102]],
                        "height_m": 12.0}],
    }])
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", cache_file)
    _FailIfCalledClient.calls = []
    monkeypatch.setattr(httpx, "Client", _FailIfCalledClient)

    result = qa_azimuth._fetch_overpass_footprint(52.51, 13.41)

    assert result == [(52.51, 13.41), (52.5101, 13.4101), (52.5099, 13.4102)]
    assert _FailIfCalledClient.calls == []


def test_fetch_overpass_footprint_cache_treffer_mit_leerer_liste_gibt_none_ohne_live_aufruf(monkeypatch, tmp_path):
    """Ein Cache-Treffer mit bestätigt leerer Gebäudeliste bedeutet 'im letzten
    Batch-Lauf kein Gebäude gefunden' — muss None liefern (wie 'kein Gebäude'
    im Live-Pfad), aber OHNE Live-Netzanfrage."""
    cache_file = tmp_path / "building_footprints.json"
    _write_cache_file(cache_file, [{
        "location_id": "loc_a",
        "observer_lat": 52.50, "observer_lon": 13.40,
        "subject_lat": 52.51, "subject_lon": 13.41,
        "buildings": [],
    }])
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", cache_file)
    _FailIfCalledClient.calls = []
    monkeypatch.setattr(httpx, "Client", _FailIfCalledClient)

    result = qa_azimuth._fetch_overpass_footprint(52.51, 13.41)

    assert result is None
    assert _FailIfCalledClient.calls == []


def test_fetch_overpass_footprint_cache_miss_faellt_auf_live_pfad_zurueck(monkeypatch, tmp_path):
    """Location nicht im Cache (z.B. neu angelegt) -> unveränderter
    Live-Mirror-Pfad wird weiterhin angefragt."""
    cache_file = tmp_path / "building_footprints.json"
    _write_cache_file(cache_file, [])  # leerer Cache, keine bekannten Locations
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", cache_file)
    _FailIfCalledClient.calls = []
    monkeypatch.setattr(httpx, "Client", _FailIfCalledClient)

    result = qa_azimuth._fetch_overpass_footprint(52.51, 13.41)

    assert result is None
    assert _FailIfCalledClient.calls == qa_azimuth.OVERPASS_MIRRORS


# ---------------------------------------------------------------------------
# Integration: fetch_buildings_along_line nutzt den lokalen Cache primär
# ---------------------------------------------------------------------------

def test_fetch_buildings_along_line_cache_treffer_ruft_kein_live_netz_auf(monkeypatch, tmp_path):
    cache_file = tmp_path / "building_footprints.json"
    _write_cache_file(cache_file, [{
        "location_id": "loc_a",
        "observer_lat": 52.50, "observer_lon": 13.40,
        "subject_lat": 52.51, "subject_lon": 13.41,
        "buildings": [{"nodes": [[52.505, 13.405], [52.5051, 13.4051], [52.5049, 13.4052]],
                        "height_m": 15.0}],
    }])
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", cache_file)
    _FailIfCalledClient.calls = []
    monkeypatch.setattr(httpx, "Client", _FailIfCalledClient)

    result = qa_azimuth.fetch_buildings_along_line(52.50, 13.40, 52.51, 13.41)

    assert result == [{"nodes": [(52.505, 13.405), (52.5051, 13.4051), (52.5049, 13.4052)],
                        "height_m": 15.0}]
    assert _FailIfCalledClient.calls == []


def test_fetch_buildings_along_line_cache_treffer_mit_leerer_liste_gibt_leere_liste_ohne_live_aufruf(monkeypatch, tmp_path):
    """Wichtig: hier MUSS [] zurückkommen (nicht None) — evaluate_sightline()
    unterscheidet [] ('geprüft, frei') von None ('nicht geprüft')."""
    cache_file = tmp_path / "building_footprints.json"
    _write_cache_file(cache_file, [{
        "location_id": "loc_a",
        "observer_lat": 52.50, "observer_lon": 13.40,
        "subject_lat": 52.51, "subject_lon": 13.41,
        "buildings": [],
    }])
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", cache_file)
    _FailIfCalledClient.calls = []
    monkeypatch.setattr(httpx, "Client", _FailIfCalledClient)

    result = qa_azimuth.fetch_buildings_along_line(52.50, 13.40, 52.51, 13.41)

    assert result == []
    assert _FailIfCalledClient.calls == []


def test_fetch_buildings_along_line_cache_miss_faellt_auf_live_pfad_zurueck(monkeypatch, tmp_path):
    cache_file = tmp_path / "building_footprints.json"
    _write_cache_file(cache_file, [])
    monkeypatch.setattr(qa_azimuth, "BUILDING_CACHE_PATH", cache_file)
    _FailIfCalledClient.calls = []
    monkeypatch.setattr(httpx, "Client", _FailIfCalledClient)

    result = qa_azimuth.fetch_buildings_along_line(52.50, 13.40, 52.51, 13.41)

    assert result is None
    assert _FailIfCalledClient.calls == qa_azimuth.OVERPASS_MIRRORS
