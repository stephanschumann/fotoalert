"""
Tests fuer BUG-112: `extract_buildings_for_locations()` in
`backend/tools/extract_building_data.py` crasht mit TypeError, sobald eine
Location mit subject_lat=None/subject_lon=None (13 der 60 Basis-Locations,
reine Panorama-/Landschaftsmotive seit BUG-98 Kategorie 1) in der Iteration
erreicht wird, weil `_haversine_m()` fuer den near_subject-Vergleich
ungeprueft mit None aufgerufen wird.

Komplett offline, keine PBF/osmium-Abhaengigkeit (analog
test_task59_extract_building_data.py).

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
    extract_buildings_for_locations,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _way(way_id, tags, nodes):
    return WayRecord(way_id=way_id, tags=tags, nodes=nodes)


# Location OHNE Motivkoordinaten (Panorama-/Landschaftsmotiv, BUG-98 Kategorie 1)
_LOC_KEIN_MOTIV = KnownLocation(
    location_id="loc_kein_motiv",
    observer_lat=52.5000, observer_lon=13.4000,
    subject_lat=None, subject_lon=None,
)

# Location MIT Motivkoordinaten (unveraendertes Verhalten, Regressionsschutz)
_LOC_MIT_MOTIV = KnownLocation(
    location_id="loc_mit_motiv",
    observer_lat=53.0000, observer_lon=14.0000,
    subject_lat=53.0010, subject_lon=14.0010,
)


def test_bug112_location_ohne_motivkoordinaten_crasht_nicht_ak1_ak4():
    """AK1/AK4: Ein Lauf ueber eine Location mit subject_lat=None darf keine
    Exception werfen (Root Cause des Bugs: TypeError in _haversine_m)."""
    building = _way(1, {"building": "yes"}, [
        (52.5000, 13.4000), (52.5001, 13.4001), (52.4999, 13.4002),
    ])  # Schwerpunkt praktisch identisch mit observer von _LOC_KEIN_MOTIV

    # Diese Zeile ist der Rot-Nachweis: vor dem Fix wirft sie TypeError.
    result = extract_buildings_for_locations([building], [_LOC_KEIN_MOTIV], radius_m=200)

    assert isinstance(result, dict)


def test_bug112_gebaeude_nahe_standort_wird_trotz_fehlendem_motiv_zugeordnet_ak2():
    """AK2: near_observer bleibt fuer Locations ohne Motivkoordinaten
    unveraendert funktionsfaehig — Gebaeude nahe observer_lat/lon wird
    weiterhin zugeordnet."""
    building = _way(1, {"building": "house"}, [
        (52.5000, 13.4000), (52.5001, 13.4001), (52.4999, 13.4002),
    ])  # nahe observer von _LOC_KEIN_MOTIV

    result = extract_buildings_for_locations([building], [_LOC_KEIN_MOTIV], radius_m=200)

    assert len(result["loc_kein_motiv"]) == 1


def test_bug112_gebaeude_fern_von_observer_wird_bei_fehlendem_motiv_nicht_zugeordnet_ak3():
    """AK3: Fuer eine Location ohne Motivkoordinaten wird die
    Motiv-Naehe-Pruefung sicher uebersprungen (liefert kein False-Positive)
    — ein Gebaeude, das weder nahe observer liegt noch (da subject fehlt)
    ueber near_subject greifen kann, bleibt unzugeordnet."""
    far_building = _way(1, {"building": "yes"}, [
        (53.5000, 14.5000), (53.5001, 14.5001), (53.4999, 14.5002),
    ])  # weit weg vom observer von _LOC_KEIN_MOTIV, subject existiert nicht

    result = extract_buildings_for_locations([far_building], [_LOC_KEIN_MOTIV], radius_m=200)

    assert result["loc_kein_motiv"] == []


def test_bug112_gemischte_locations_werden_alle_vollstaendig_verarbeitet_ak4():
    """AK4 (Edge Case): Eine Mischung aus Locations mit und ohne
    Motivkoordinaten im selben Lauf laesst den Lauf nicht abbrechen —
    unabhaengig von der Position der None-Location in der Liste."""
    building_bei_motiv = _way(1, {"building": "yes"}, [
        (53.0010, 13.9999), (53.0011, 14.0001), (53.0009, 14.0002),
    ])  # nahe subject von _LOC_MIT_MOTIV
    building_bei_observer_ohne_motiv = _way(2, {"building": "house"}, [
        (52.5000, 13.4000), (52.5001, 13.4001), (52.4999, 13.4002),
    ])  # nahe observer von _LOC_KEIN_MOTIV

    # _LOC_KEIN_MOTIV zuerst in der Liste — genau der Fall, der laut Ticket
    # das gesamte Skript sofort abbrechen laesst, sobald die Iteration ihn
    # erreicht.
    result = extract_buildings_for_locations(
        [building_bei_motiv, building_bei_observer_ohne_motiv],
        [_LOC_KEIN_MOTIV, _LOC_MIT_MOTIV],
        radius_m=200,
    )

    assert len(result["loc_kein_motiv"]) == 1
    assert len(result["loc_mit_motiv"]) == 1


def test_bug112_locations_mit_motivkoordinaten_verhalten_sich_unveraendert_ak5():
    """AK5 (Regression): Fuer Locations MIT Motivkoordinaten aendert der Fix
    nichts — near_subject wird weiterhin korrekt ueber die tatsaechliche
    Distanz zum Motiv berechnet (identisch zu
    test_task59_extract_building_data.test_gebaeude_nahe_motiv_wird_der_location_zugeordnet)."""
    building_bei_motiv = _way(1, {"building": "yes"}, [
        (53.0010, 13.9999), (53.0011, 14.0001), (53.0009, 14.0002),
    ])
    far_building = _way(2, {"building": "yes"}, [
        (10.0, 10.0), (10.0001, 10.0001), (9.9999, 10.0002),
    ])

    result = extract_buildings_for_locations(
        [building_bei_motiv, far_building], [_LOC_MIT_MOTIV], radius_m=200,
    )

    assert len(result["loc_mit_motiv"]) == 1


def test_bug112_known_location_type_hint_erlaubt_optional_subject_koordinaten_ak6():
    """AK6 (Architektur/Konsistenz): `KnownLocation.subject_lat`/`subject_lon`
    sind als `Optional[float]` typisiert, passend zu den tatsaechlichen
    Laufzeitwerten, die `load_known_locations()` aus `data/locations.py`
    durchreicht (dort ebenfalls `Optional[float]`, siehe
    `backend/data/locations.py`). Ein `float`-Hint waere irrefuehrend, da er
    bereits heute nicht der Realitaet entspricht."""
    import typing
    hints = typing.get_type_hints(KnownLocation)

    assert hints["subject_lat"] == typing.Optional[float]
    assert hints["subject_lon"] == typing.Optional[float]
