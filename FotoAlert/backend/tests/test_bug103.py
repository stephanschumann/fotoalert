"""
BUG-103 - Scout-Zugänglichkeits-Cache (Kartendaten) prüft beim Wiederverwenden
gespeicherter Einträge nicht, ob sie zum aktuellen Programmstand
(Berechnungslogik-Version) passen.

Tests für die BUG-103-Erweiterung von backend/data/qa_azimuth.py:
SCOUT_ACCESS_CACHE_VERSION (neue Modul-Konstante, analog precompute.py
ALGORITHM_VERSION), _find_scout_access_cache_entry() (zusätzliche
Versions-Prüfung beim Lesen -- Mismatch/fehlendes Feld = Cache-Miss) und
get_scout_accessibility_data() (Versions-Tag beim Schreiben + Ersetzen eines
alten Eintrags für dieselbe Koordinate statt Anhängen).

Keine echten Overpass-Netzwerkaufrufe: qa_azimuth.fetch_scout_accessibility_
data() wird direkt gemonkeypatcht (Marker: offline), analog dem bestehenden
Cache-Testmuster in test_us135.py (dort wird eine Ebene tiefer, auf
httpx.Client, gemockt -- hier reicht die höhere Ebene, weil BUG-103
ausschließlich die Cache-Schicht betrifft, nicht die Overpass-Abfrage
selbst). Aus den BUG-103-Akzeptanzkriterien abgeleitet (Marker: regression).

Rührt NIE die reale, ~1,8 GB große Produktions-Cache-Datei an -- jeder Test
biegt SCOUT_ACCESS_CACHE_PATH per monkeypatch auf tmp_path um und arbeitet
nur mit kleinen synthetischen Cache-Dateien.

Python-3.9-kompatibel.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data import qa_azimuth

pytestmark = [pytest.mark.offline, pytest.mark.regression]


@pytest.fixture(autouse=True)
def _reset_scout_access_cache_singleton(monkeypatch):
    """Der Modul-Cache (_scout_access_cache_entries) ist ein Prozess-weiter
    Singleton (lazy geladen) -- fuer isolierte Tests vor JEDEM Test auf
    'noch nicht geladen' zuruecksetzen (analog test_us135.py)."""
    monkeypatch.setattr(qa_azimuth, "_scout_access_cache_entries", None)


def _empty_data():
    return {"buildings": [], "forest_ways": [], "water_ways": [], "rail_ways": [], "path_ways": []}


def _write_cache_file(path: Path, entries: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")


def _stale_entry(
    observer_lat=52.4296, observer_lon=13.1146,
    subject_lat=52.4300, subject_lon=13.1150,
    algorithm_version=None, cached_at=None,
):
    """Ein Cache-Eintrag im Bestandsformat -- analog dem realen
    Pfaueninsel-Fund vom 08.08.2026 (algorithm_version=None -> Feld fehlt
    komplett, exakt wie alle heute bereits gespeicherten Einträge)."""
    entry = {
        "observer_lat": observer_lat,
        "observer_lon": observer_lon,
        "subject_lat": subject_lat,
        "subject_lon": subject_lon,
        "cached_at": cached_at or datetime.now(timezone.utc).isoformat(),
        "data": _empty_data(),
    }
    if algorithm_version is not None:
        entry["algorithm_version"] = algorithm_version
    return entry


def _counting_fetch(payload=None):
    calls = {"n": 0}

    def _fetch(observer_lat, observer_lon, subject_lat, subject_lon):
        calls["n"] += 1
        return payload if payload is not None else _empty_data()

    return _fetch, calls


# ---------------------------------------------------------------------------
# AK1/AK2/AK5: Eintrag mit fehlendem oder altem Versionsfeld = Cache-Miss
# ---------------------------------------------------------------------------

def test_bug103_eintrag_ohne_versionsfeld_wird_wie_miss_behandelt(monkeypatch, tmp_path):
    """AK1/AK2/AK5: Ein Bestandseintrag ganz ohne algorithm_version-Feld
    (exakt das reale Pfaueninsel-Format) gilt beim allerersten Zugriff nach
    dem Fix sofort als ungültig -- kein Absturz, sondern ein live neu
    ausgeführter Abruf, ganz ohne TTL-Ablauf oder manuelles Löschen."""
    cache_path = tmp_path / "scout_access.json"
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", cache_path)
    _write_cache_file(cache_path, [_stale_entry(algorithm_version=None)])

    fetch, calls = _counting_fetch()
    monkeypatch.setattr(qa_azimuth, "fetch_scout_accessibility_data", fetch)

    result = qa_azimuth.get_scout_accessibility_data(52.4296, 13.1146, 52.4300, 13.1150)

    assert result == _empty_data()
    assert calls["n"] == 1  # live neu geprüft statt stillschweigend den alten Eintrag zu nutzen


def test_bug103_eintrag_mit_alter_version_wird_wie_miss_behandelt(monkeypatch, tmp_path):
    """AK1/AK2: Ein Eintrag mit einer expliziten, aber älteren
    algorithm_version gilt ebenfalls als Mismatch -- nicht nur der
    versionslose Bestandsfall (AK5)."""
    cache_path = tmp_path / "scout_access.json"
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", cache_path)
    _write_cache_file(cache_path, [_stale_entry(algorithm_version="0.9")])

    fetch, calls = _counting_fetch()
    monkeypatch.setattr(qa_azimuth, "fetch_scout_accessibility_data", fetch)

    qa_azimuth.get_scout_accessibility_data(52.4296, 13.1146, 52.4300, 13.1150)

    assert calls["n"] == 1


# ---------------------------------------------------------------------------
# AK3/AK7: aktuelle Version + gültige TTL bleibt normal wiederverwendet
# (Regressionsschutz gegen Überinvalidierung)
# ---------------------------------------------------------------------------

def test_bug103_eintrag_mit_aktueller_version_bleibt_gecacht_kein_live_call(monkeypatch, tmp_path):
    """AK3/AK7: ein Eintrag, dessen algorithm_version zum aktuellen
    SCOUT_ACCESS_CACHE_VERSION passt und dessen TTL noch nicht abgelaufen
    ist, wird weiterhin ganz normal wiederverwendet -- kein unnötiger
    Live-Call bei einem reinen Server-Neustart oder einer x-beliebigen
    Codeänderung ohne Versions-Bump."""
    cache_path = tmp_path / "scout_access.json"
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", cache_path)
    _write_cache_file(cache_path, [_stale_entry(
        algorithm_version=qa_azimuth.SCOUT_ACCESS_CACHE_VERSION,
    )])

    fetch, calls = _counting_fetch()
    monkeypatch.setattr(qa_azimuth, "fetch_scout_accessibility_data", fetch)

    result = qa_azimuth.get_scout_accessibility_data(52.4296, 13.1146, 52.4300, 13.1150)

    assert result == _empty_data()
    assert calls["n"] == 0  # kein Live-Call -- Cache-Treffer verwendet


# ---------------------------------------------------------------------------
# AK4: Ersetzen statt Anhängen (behebt nebenbei das Dateiwachstum)
# ---------------------------------------------------------------------------

def test_bug103_neuer_eintrag_ersetzt_alten_statt_anzuhaengen(monkeypatch, tmp_path):
    """AK4: Nach einer erfolgreichen Neuprüfung (ausgelöst durch den
    Versions-Mismatch des alten Eintrags) enthält die Cache-Datei für diese
    Koordinate genau EINEN Eintrag, nicht zwei -- behebt das unbegrenzte
    Dateiwachstum (Root Cause: ≈1,8 GB durch reines Anhängen)."""
    cache_path = tmp_path / "scout_access.json"
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", cache_path)
    _write_cache_file(cache_path, [_stale_entry(algorithm_version=None)])

    fetch, _ = _counting_fetch()
    monkeypatch.setattr(qa_azimuth, "fetch_scout_accessibility_data", fetch)

    qa_azimuth.get_scout_accessibility_data(52.4296, 13.1146, 52.4300, 13.1150)

    on_disk = json.loads(cache_path.read_text(encoding="utf-8"))
    matching = [
        e for e in on_disk["entries"]
        if abs(e["observer_lat"] - 52.4296) < 1e-6 and abs(e["subject_lat"] - 52.4300) < 1e-6
    ]
    assert len(matching) == 1
    assert matching[0]["algorithm_version"] == qa_azimuth.SCOUT_ACCESS_CACHE_VERSION


def test_bug103_neuer_eintrag_fuer_andere_koordinate_bleibt_zusaetzlich_bestehen(monkeypatch, tmp_path):
    """Gegenprobe zu AK4: das Ersetzen darf sich NUR auf dieselbe Koordinate
    beziehen -- ein bestehender, gültiger Eintrag für einen anderen
    Standpunkt bleibt unangetastet erhalten (kein versehentlicher
    Datenverlust anderer Koordinaten)."""
    cache_path = tmp_path / "scout_access.json"
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", cache_path)
    other_entry = _stale_entry(
        observer_lat=53.0, observer_lon=14.0, subject_lat=53.001, subject_lon=14.001,
        algorithm_version=qa_azimuth.SCOUT_ACCESS_CACHE_VERSION,
    )
    _write_cache_file(cache_path, [
        _stale_entry(algorithm_version=None),
        other_entry,
    ])

    fetch, _ = _counting_fetch()
    monkeypatch.setattr(qa_azimuth, "fetch_scout_accessibility_data", fetch)

    qa_azimuth.get_scout_accessibility_data(52.4296, 13.1146, 52.4300, 13.1150)

    on_disk = json.loads(cache_path.read_text(encoding="utf-8"))
    assert len(on_disk["entries"]) == 2
    others = [e for e in on_disk["entries"] if abs(e["observer_lat"] - 53.0) < 1e-6]
    assert len(others) == 1


# ---------------------------------------------------------------------------
# AK6: Live-Prüfung nach Versions-Mismatch schlägt fehl -> kein Rückfall auf
# die veralteten Daten
# ---------------------------------------------------------------------------

def test_bug103_live_fehlschlag_nach_versions_mismatch_faellt_nicht_auf_alte_daten_zurueck(monkeypatch, tmp_path):
    """AK6 Edge Case: Kann für einen Punkt mit veraltetem Eintrag keine neue
    Live-Prüfung durchgeführt werden, bleibt der Punkt wie bisher 'nicht
    prüfbar' (None) -- kein Rückfall auf die als ungültig verworfenen alten
    Daten."""
    cache_path = tmp_path / "scout_access.json"
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", cache_path)
    _write_cache_file(cache_path, [_stale_entry(algorithm_version=None)])

    def _always_fail(*args, **kwargs):
        return None

    monkeypatch.setattr(qa_azimuth, "fetch_scout_accessibility_data", _always_fail)

    result = qa_azimuth.get_scout_accessibility_data(52.4296, 13.1146, 52.4300, 13.1150)

    assert result is None


# ---------------------------------------------------------------------------
# AK8: Log-Zeile beim Verwerfen
# ---------------------------------------------------------------------------

def test_bug103_verwurf_wegen_versions_mismatch_wird_geloggt(monkeypatch, tmp_path, caplog):
    """AK8: Wird ein Eintrag wegen Versions-Mismatch verworfen, ist das im
    Server-Log nachvollziehbar (Zeitpunkt, betroffener Punkt) -- nicht nur
    ein stiller Fallback ohne jede Spur."""
    cache_path = tmp_path / "scout_access.json"
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", cache_path)
    _write_cache_file(cache_path, [_stale_entry(algorithm_version="0.1")])

    fetch, _ = _counting_fetch()
    monkeypatch.setattr(qa_azimuth, "fetch_scout_accessibility_data", fetch)

    with caplog.at_level(logging.INFO, logger=qa_azimuth.logger.name):
        qa_azimuth.get_scout_accessibility_data(52.4296, 13.1146, 52.4300, 13.1150)

    assert any(
        "Versions" in r.message and "verworfen" in r.message
        for r in caplog.records
    )


# ---------------------------------------------------------------------------
# Direkte Unit-Tests von _find_scout_access_cache_entry() ohne Umweg über die
# öffentliche get_scout_accessibility_data()
# ---------------------------------------------------------------------------

def test_bug103_find_cache_entry_direkt_none_bei_versions_mismatch(monkeypatch, tmp_path):
    cache_path = tmp_path / "scout_access.json"
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", cache_path)
    _write_cache_file(cache_path, [_stale_entry(algorithm_version=None)])

    found = qa_azimuth._find_scout_access_cache_entry(52.4296, 13.1146, 52.4300, 13.1150)

    assert found is None


def test_bug103_find_cache_entry_direkt_treffer_bei_passender_version(monkeypatch, tmp_path):
    cache_path = tmp_path / "scout_access.json"
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", cache_path)
    _write_cache_file(cache_path, [_stale_entry(
        algorithm_version=qa_azimuth.SCOUT_ACCESS_CACHE_VERSION,
    )])

    found = qa_azimuth._find_scout_access_cache_entry(52.4296, 13.1146, 52.4300, 13.1150)

    assert found is not None
    assert found["algorithm_version"] == qa_azimuth.SCOUT_ACCESS_CACHE_VERSION
