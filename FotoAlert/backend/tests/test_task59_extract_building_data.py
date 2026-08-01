"""
Tests für TASK-59 Option E: `backend/tools/extract_building_data.py`.

Komplett offline: kein echtes Netzwerk, keine echte PBF-Datei, kein
osmium-Import nötig (die osmium-Anbindung `_iter_ways_from_pbf` wird hier
NICHT getestet — sie kann ohne echten Netzwerkzugriff/reale PBF-Testdaten in
dieser Sandbox nicht verifiziert werden, siehe Modul-Docstring von
extract_building_data.py und der zugehörige BACKLOG.md-Hinweis, was Stephan
noch selbst prüfen muss).

Getestet wird die Kernlogik, die auf einfachen, osmium-unabhängigen
WayRecord-Objekten arbeitet:
- `extract_buildings_for_locations()`: Radius-Filter (Standort ODER Motiv),
  Ausschluss von Nicht-Gebäuden und entarteten Polygonen, Höhenschätzung.
- `build_output()`: deterministische, sortierte JSON-Struktur.
- `load_known_locations()`: liest echte `data/locations.py`-Koordinaten
  (kein Mock nötig, reiner Datenzugriff ohne Netzwerk).

Python-3.9-kompatibel.
"""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.extract_building_data import (
    KnownLocation,
    WayRecord,
    build_output,
    extract_buildings_for_locations,
    load_known_locations,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression]


_LOC_A = KnownLocation(
    location_id="loc_a",
    observer_lat=52.5000, observer_lon=13.4000,
    subject_lat=52.5010, subject_lon=13.4010,
)
_LOC_B = KnownLocation(
    location_id="loc_b",
    observer_lat=53.0000, observer_lon=14.0000,
    subject_lat=53.0010, subject_lon=14.0010,
)


def _way(way_id, tags, nodes):
    return WayRecord(way_id=way_id, tags=tags, nodes=nodes)


# ---------------------------------------------------------------------------
# extract_buildings_for_locations — Radius-Filter
# ---------------------------------------------------------------------------

def test_gebaeude_nahe_motiv_wird_der_location_zugeordnet():
    building = _way(1, {"building": "yes"}, [
        (52.5010, 13.4010), (52.5011, 13.4011), (52.5009, 13.4012),
    ])  # Schwerpunkt praktisch identisch mit subject von loc_a

    result = extract_buildings_for_locations([building], [_LOC_A, _LOC_B], radius_m=200)

    assert len(result["loc_a"]) == 1
    assert result["loc_b"] == []


def test_gebaeude_nahe_standort_statt_motiv_wird_auch_zugeordnet():
    building = _way(1, {"building": "house"}, [
        (52.5000, 13.4000), (52.5001, 13.4001), (52.4999, 13.4002),
    ])  # nahe observer von loc_a, weit vom subject entfernt (~110m)

    result = extract_buildings_for_locations([building], [_LOC_A], radius_m=200)

    assert len(result["loc_a"]) == 1


def test_gebaeude_ausserhalb_radius_wird_nicht_zugeordnet():
    far_building = _way(1, {"building": "yes"}, [
        (53.5000, 14.5000), (53.5001, 14.5001), (53.4999, 14.5002),
    ])  # weit weg von beiden bekannten Locations

    result = extract_buildings_for_locations([far_building], [_LOC_A, _LOC_B], radius_m=200)

    assert result["loc_a"] == []
    assert result["loc_b"] == []


def test_way_ohne_building_tag_wird_ignoriert():
    non_building = _way(1, {"highway": "residential"}, [
        (52.5010, 13.4010), (52.5011, 13.4011), (52.5009, 13.4012),
    ])

    result = extract_buildings_for_locations([non_building], [_LOC_A], radius_m=200)

    assert result["loc_a"] == []


def test_entartetes_polygon_unter_3_knoten_wird_ignoriert():
    degenerate = _way(1, {"building": "yes"}, [(52.5010, 13.4010), (52.5011, 13.4011)])

    result = extract_buildings_for_locations([degenerate], [_LOC_A], radius_m=200)

    assert result["loc_a"] == []


def test_hoehenschaetzung_aus_height_tag():
    building = _way(1, {"building": "yes", "height": "23.5 m"}, [
        (52.5010, 13.4010), (52.5011, 13.4011), (52.5009, 13.4012),
    ])

    result = extract_buildings_for_locations([building], [_LOC_A], radius_m=200)

    assert result["loc_a"][0]["height_m"] == 23.5


def test_hoehenschaetzung_aus_levels_tag_wenn_height_fehlt():
    building = _way(1, {"building": "yes", "building:levels": "4"}, [
        (52.5010, 13.4010), (52.5011, 13.4011), (52.5009, 13.4012),
    ])

    result = extract_buildings_for_locations([building], [_LOC_A], radius_m=200)

    assert result["loc_a"][0]["height_m"] == 4 * 3.0  # LEVEL_HEIGHT_M


def test_hoehenschaetzung_default_wenn_kein_tag_vorhanden():
    building = _way(1, {"building": "yes"}, [
        (52.5010, 13.4010), (52.5011, 13.4011), (52.5009, 13.4012),
    ])

    result = extract_buildings_for_locations([building], [_LOC_A], radius_m=200)

    assert result["loc_a"][0]["height_m"] == 9.0  # DEFAULT_BUILDING_HEIGHT_M


def test_ein_gebaeude_kann_mehreren_locations_zugeordnet_werden():
    """Zwei Locations, deren Umkreise sich überlappen -> dasselbe Gebäude
    erscheint in beiden Ergebnislisten (Duplizierung ist gewollt, da die
    Lookup-Funktion in qa_azimuth.py pro Location unabhängig nachschlägt)."""
    loc_c = KnownLocation("loc_c", 52.5011, 13.4011, 52.5012, 13.4012)  # fast identisch zu loc_a
    building = _way(1, {"building": "yes"}, [
        (52.5010, 13.4010), (52.5011, 13.4011), (52.5009, 13.4012),
    ])

    result = extract_buildings_for_locations([building], [_LOC_A, loc_c], radius_m=200)

    assert len(result["loc_a"]) == 1
    assert len(result["loc_c"]) == 1


# ---------------------------------------------------------------------------
# build_output
# ---------------------------------------------------------------------------

def test_build_output_struktur_und_sortierung():
    buildings_by_location = {
        "loc_b": [{"nodes": [[53.0, 14.0]], "height_m": 5.0}],
        "loc_a": [],
    }

    output = build_output([_LOC_B, _LOC_A], buildings_by_location, radius_m=200, source_label="test.pbf")

    assert output["location_count"] == 2
    assert output["radius_m"] == 200
    assert output["source"] == "test.pbf"
    assert "generated_at" in output
    # Deterministisch nach location_id sortiert, unabhängig von Eingabereihenfolge.
    assert [l["location_id"] for l in output["locations"]] == ["loc_a", "loc_b"]
    assert output["locations"][0]["buildings"] == []
    assert output["locations"][1]["buildings"] == [{"nodes": [[53.0, 14.0]], "height_m": 5.0}]


def test_build_output_fehlende_location_in_buildings_dict_bekommt_leere_liste():
    output = build_output([_LOC_A], buildings_by_location={}, radius_m=200, source_label="test.pbf")

    assert output["locations"][0]["buildings"] == []


# ---------------------------------------------------------------------------
# load_known_locations — echter Datenzugriff auf data/locations.py, kein Mock
# ---------------------------------------------------------------------------

def test_load_known_locations_liefert_alle_basis_locations_mit_koordinaten():
    from data.locations import LOCATIONS

    result = load_known_locations()

    assert len(result) == len(LOCATIONS)
    ids = {loc.location_id for loc in result}
    assert ids == {loc.id for loc in LOCATIONS}
    first = result[0]
    assert isinstance(first.observer_lat, float)
    assert isinstance(first.subject_lat, float)
