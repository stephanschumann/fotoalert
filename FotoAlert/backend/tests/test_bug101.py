"""
BUG-101 - Scout-Zugaenglichkeitspruefung erkennt nur Gebaeude-Verdeckung,
keine Baeume/Wald in der Sichtachse zum Motiv.

Tests fuer die neue Funktion qa_azimuth.is_sightline_blocked_by_vegetation()
und ihre Integration in discover/accessibility.py::filter_accessible_
candidates() (Aufruf NACH der bestehenden Gebaeude-Sichtpruefung, VOR
_is_excluded()). Alle Overpass-Antworten sind gemockt -- kein echter
Netzwerkzugriff im Test (Marker: offline). Aus den BUG-101-
Akzeptanzkriterien abgeleitet (Marker: regression).

Python-3.9-kompatibel.
"""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data import qa_azimuth
from discover import accessibility
from discover.pipeline_base import ScoutOpportunity

pytestmark = [pytest.mark.offline, pytest.mark.regression]


@pytest.fixture(autouse=True)
def _reset_scout_access_cache_singleton(monkeypatch):
    """Siehe test_us135.py: Modul-Cache vor jedem Test zuruecksetzen."""
    monkeypatch.setattr(qa_azimuth, "_scout_access_cache_entries", None)


def _make_candidate(
    standpoint_lat=52.5000, standpoint_lon=13.4000,
    subject_lat=52.5100, subject_lon=13.4000,
    subject_id="testmotiv",
):
    """Minimaler ScoutOpportunity-Testkandidat, analog test_us135.py."""
    return ScoutOpportunity(
        body_name="moon",
        subject_id=subject_id,
        subject_name="Test-Motiv",
        subject_lat=subject_lat,
        subject_lon=subject_lon,
        day="2026-08-10",
        session="golden_evening",
        dt_utc="2026-08-10T18:00:00Z",
        body_azimuth_deg=180.0,
        body_altitude_deg=10.0,
        body_illumination_pct=None,
        distance_m=200.0,
        standpoint_lat=standpoint_lat,
        standpoint_lon=standpoint_lon,
        focal_length_equiv_mm=50.0,
        score=0.8,
        score_alignment=0.8,
        score_phase=0.8,
        score_licht=0.8,
        score_komposition=0.8,
        score_wetter=0.8,
        weather_description="Klarer Himmel",
    )


def _empty_data():
    return {"buildings": [], "forest_ways": [], "water_ways": [], "rail_ways": [], "path_ways": []}


# Wald-Polygon, das den Standard-Standpunkt (52.5000, 13.4000) exakt umgibt
# (Flaechenschwerpunkt == Standpunkt) -- deckt AK1 ("Standpunkt liegt
# innerhalb eines Wald-Polygons") ab. Peilung nach Norden (52.5100, 13.4000,
# der Standard-Motivwert von _make_candidate oben) liegt klar innerhalb des
# blockierten Winkelbereichs dieses Polygons (verifiziert, kein Grenzfall).
_FOREST_UM_STANDPUNKT = {"nodes": [
    (52.4990, 13.3990), (52.4990, 13.4010),
    (52.5010, 13.4010), (52.5010, 13.3990),
]}

# Wald-Polygon noerdlich des Standpunkts, das NICHT den Standpunkt enthaelt,
# aber zwischen Standpunkt (52.5000, 13.4000) und einem weiter entfernten
# Motiv (52.5100, 13.4000) liegt -- deckt AK2 ab.
_FOREST_ZWISCHEN_STANDPUNKT_UND_MOTIV = {"nodes": [
    (52.5010, 13.3990), (52.5010, 13.4010),
    (52.5020, 13.4010), (52.5020, 13.3990),
]}

# Wald-Polygon seitlich (westlich) versetzt -- liegt weder auf dem
# Standpunkt noch auf der Sichtlinie zum noerdlichen Motiv -- Gegenprobe
# fuer AK3.
_FOREST_ABSEITS = {"nodes": [
    (52.5010, 13.3800), (52.5010, 13.3820),
    (52.5020, 13.3820), (52.5020, 13.3800),
]}


# ---------------------------------------------------------------------------
# AK1: Standpunkt liegt innerhalb einer Waldflaeche, deren Winkelbereich die
# Peilung zum Motiv abdeckt -> Kandidat erscheint nicht mehr in der Liste.
# ---------------------------------------------------------------------------

def test_bug101_standpoint_im_wald_blockiert_sicht_wird_ausgeblendet(monkeypatch):
    """BUG-101 AK1: Standpunkt liegt mitten in einer Waldflaeche, deren
    Winkelbereich (dieselbe Berechnung wie bei Gebaeuden) die Peilung zum
    Motiv vollstaendig abdeckt -> Kandidat wird ausgeblendet."""
    c = _make_candidate()  # standpoint (52.5000,13.4000), subject (52.5100,13.4000) noerdlich
    data = _empty_data()
    data["forest_ways"] = [_FOREST_UM_STANDPUNKT]
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: data)

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


def test_bug101_is_sightline_blocked_by_vegetation_direkt_standpunkt_im_schwerpunkt(monkeypatch):
    """BUG-101 (Root-Cause-Regression): is_sightline_blocked_by_vegetation()
    prueft eine Waldflaeche weiterhin, wenn ihr Flaechenschwerpunkt exakt auf
    dem Standpunkt liegt (Distanz 0) -- anders als
    is_sightline_blocked_by_buildings(), die diesen Fall uebersprungen haette
    (dist_to_building <= 0). Ohne diese bewusste Abweichung wuerde AK1 fuer
    einen Standpunkt genau im Zentrum einer (ggf. kleinen/symmetrischen)
    Waldflaeche nie ausloesen."""
    blocked = qa_azimuth.is_sightline_blocked_by_vegetation(
        52.5000, 13.4000, 52.5100, 13.4000, [_FOREST_UM_STANDPUNKT],
    )
    assert blocked is True


# ---------------------------------------------------------------------------
# AK2: Standpunkt liegt ausserhalb jeder Waldflaeche, aber eine Waldflaeche
# liegt auf der Sichtlinie zu einem weiter entfernten Motiv -> ausgeblendet.
# ---------------------------------------------------------------------------

def test_bug101_wald_zwischen_standpunkt_und_entfernterem_motiv_wird_ausgeblendet(monkeypatch):
    """BUG-101 AK2: Standpunkt liegt ausserhalb jeder Waldflaeche, aber eine
    Waldflaeche zwischen Standpunkt und einem weiter entfernten Motiv
    blockiert die Sichtlinie -> Kandidat wird ausgeblendet."""
    c = _make_candidate()  # standpoint (52.5000,13.4000), subject (52.5100,13.4000)
    data = _empty_data()
    data["forest_ways"] = [_FOREST_ZWISCHEN_STANDPUNKT_UND_MOTIV]
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: data)

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


# ---------------------------------------------------------------------------
# AK3: Gegenprobe -- tatsaechlich freie Sicht (weder Wald- noch
# Gebaeudeverdeckung) -> Kandidat bleibt weiterhin sichtbar.
# ---------------------------------------------------------------------------

def test_bug101_wald_abseits_der_sichtlinie_bleibt_in_liste(monkeypatch):
    """BUG-101 AK3: Eine Waldflaeche existiert im Umkreis, liegt aber weder
    auf dem Standpunkt noch auf der Sichtlinie zum Motiv -> unveraendertes
    Verhalten, Kandidat bleibt in der Liste."""
    c = _make_candidate()  # standpoint (52.5000,13.4000), subject (52.5100,13.4000)
    data = _empty_data()
    data["forest_ways"] = [_FOREST_ABSEITS]
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: data)

    result = accessibility.filter_accessible_candidates([c])

    assert result == [c]


# ---------------------------------------------------------------------------
# AK4: Die neue Sichtpruefung wirkt ZUSAETZLICH zur bestehenden US-135-
# Wald+Weg-Zugaenglichkeitspruefung, nicht anstelle davon -- ein Standpunkt
# im Wald mit begehbarem Weg in der Naehe (bislang "zugaenglich"), aber ohne
# freie Sicht zum Motiv, erscheint trotzdem nicht mehr in der Liste.
# ---------------------------------------------------------------------------

def test_bug101_wald_mit_weg_aber_ohne_freie_sicht_wird_trotzdem_ausgeblendet(monkeypatch):
    """BUG-101 AK4: Standpunkt liegt im Wald, ein begehbarer Weg liegt
    innerhalb des bestaetigten 50m-Radius (US-135 Regel 2 wuerde ihn allein
    als 'zugaenglich' werten), aber die Sicht zum Motiv ist durch dieselbe
    Waldflaeche blockiert -> Kandidat wird trotzdem ausgeblendet, weil die
    neue BUG-101-Sichtpruefung zusaetzlich zur bestehenden
    Zugaenglichkeitspruefung wirkt."""
    c = _make_candidate()  # standpoint (52.5000,13.4000), subject (52.5100,13.4000)
    nearby_path = {"nodes": [(52.50005, 13.40005), (52.5002, 13.4002)]}
    data = _empty_data()
    data["forest_ways"] = [_FOREST_UM_STANDPUNKT]
    data["path_ways"] = [nearby_path]
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: data)

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


# ---------------------------------------------------------------------------
# AK7: Die neue Wald-Sichtpruefung loest keine zusaetzliche Live-Datenabfrage
# pro Kandidat/Cluster aus -- sie nutzt dieselbe bereits geladene
# Kartendaten-Antwort wie die Gebaeude-Sichtpruefung.
# ---------------------------------------------------------------------------

def test_bug101_keine_zusaetzliche_live_abfrage_durch_waldpruefung(monkeypatch):
    """BUG-101 AK7: Ein Kandidaten-Cluster, dessen geladene Daten eine
    sichtblockierende Waldflaeche enthalten, loest weiterhin genau EINEN
    Aufruf von get_scout_accessibility_data() aus -- die neue lokale
    Wald-Sichtpruefung fuehrt zu keinem zusaetzlichen Netzwerk-/Cache-Call."""
    call_count = {"n": 0}

    def _counting(**kw):
        call_count["n"] += 1
        data = _empty_data()
        data["forest_ways"] = [_FOREST_UM_STANDPUNKT]
        return data

    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data", _counting)

    c = _make_candidate()

    result = accessibility.filter_accessible_candidates([c])

    assert call_count["n"] == 1
    assert result == []  # Sichtblockade durch Wald bestaetigt gleichzeitig AK1 erneut


# ---------------------------------------------------------------------------
# AK6 (Gegenprobe/Abgrenzung): Die neue Pruefung ist ausschliesslich in
# discover/accessibility.py verdrahtet -- is_sightline_blocked_by_vegetation
# selbst hat keine Kenntnis von US-09/calculations/sightline.py und wird von
# dort auch nicht aufgerufen (reine Existenzpruefung, kein Import-Fehler).
# ---------------------------------------------------------------------------

def test_bug101_neue_funktion_existiert_und_ist_isoliert_aufrufbar():
    """BUG-101 AK6 (Abgrenzung): is_sightline_blocked_by_vegetation() ist
    eine eigenstaendige, ohne Nebenwirkungen aufrufbare Funktion in
    qa_azimuth.py -- unabhaengig von der bestehenden Sichtachsenpruefung
    fuer gespeicherte Standorte (calculations/sightline.py, US-09), die von
    diesem Ticket unberuehrt bleibt."""
    assert callable(qa_azimuth.is_sightline_blocked_by_vegetation)
    # Leere forest_ways-Liste -> nie eine Blockade, kein Crash (Negativfall).
    assert qa_azimuth.is_sightline_blocked_by_vegetation(
        52.5000, 13.4000, 52.5100, 13.4000, [],
    ) is False
