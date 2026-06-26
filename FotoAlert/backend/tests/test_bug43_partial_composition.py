"""Regressionssuite — BUG-43: Partielle Kompositions-Analyse ohne Motivhöhe.

Sichert ab, dass _composition_analysis auch ohne subject_height_m eine partielle
Analyse zurückgibt (azimuth_delta_deg + lateral_offset_m bleiben berechenbar),
anstatt None zu liefern. Höhenabhängige Felder (altitude_delta_deg, vertical_offset_m,
size_ratio, subject_apparent_elevation_deg) sind in diesem Fall None.

Konvention: Sonnen-Setup → fixer Winkeldurchmesser, kein Ephemeriden-Zugriff.
"""
from types import SimpleNamespace as NS

import pytest

import precompute as P

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _make_event_no_height(*, distance_m=3200.0, celestial_altitude=8.7,
                           celestial_azimuth=157.8, subject_azimuth=157.8,
                           event_type="Sonnen-Alignment"):
    """Mock-Event ohne subject_height_m (= BUG-43-Szenario)."""
    loc = NS(
        subject_height_m=None,
        distance_m=distance_m,
        elevation_difference_m=0.0,
        observer_floor_height_m=0.0,
    )
    return NS(
        location=loc,
        celestial_altitude=celestial_altitude,
        celestial_azimuth=celestial_azimuth,
        subject_azimuth=subject_azimuth,
        event_type=event_type,
        shoot_time=None,
    )


# --- BUG-43: Partielle Analyse wird zurückgegeben (nicht None) --------------------
def test_bug43_partial_result_not_none():
    """BUG-43: Ohne subject_height_m ⇒ composition_analysis ist nicht None."""
    ca = P._composition_analysis(_make_event_no_height())
    assert ca is not None, "Partielle Analyse erwartet, aber None erhalten"


# --- BUG-43: Azimut-Felder sind vorhanden ----------------------------------------
def test_bug43_azimuth_fields_present():
    """BUG-43: azimuth_delta_deg und lateral_offset_m sind berechnet (nicht None)."""
    ca = P._composition_analysis(_make_event_no_height(
        celestial_azimuth=160.0, subject_azimuth=157.0
    ))
    assert ca["azimuth_delta_deg"] is not None
    assert ca["lateral_offset_m"] is not None


# --- BUG-43: Lateral-Vorzeichen korrekt -----------------------------------------
def test_bug43_lateral_sign_correct():
    """BUG-43: az_delta < 0 → lateral_offset_m < 0 (Objekt links), auch ohne Höhe."""
    ca = P._composition_analysis(_make_event_no_height(
        celestial_azimuth=155.0, subject_azimuth=157.0
    ))
    assert ca["azimuth_delta_deg"] < 0
    assert ca["lateral_offset_m"] < 0


# --- BUG-43: Höhenabhängige Felder sind None ------------------------------------
def test_bug43_height_fields_are_none():
    """BUG-43: altitude_delta_deg, vertical_offset_m, size_ratio, subject_apparent_elevation_deg
    sind None wenn kein subject_height_m vorhanden."""
    ca = P._composition_analysis(_make_event_no_height())
    assert ca["altitude_delta_deg"] is None
    assert ca["vertical_offset_m"] is None
    assert ca["size_ratio"] is None
    assert ca["subject_apparent_elevation_deg"] is None
    assert ca["subject_height_m"] is None


# --- BUG-43: Kein ZeroDivisionError bei subject_height_m = 0 -------------------
def test_bug43_no_zero_division_with_height_zero():
    """BUG-43: subject_height_m = 0 (explizit) → kein ZeroDivisionError, partielle Analyse."""
    loc = NS(subject_height_m=0, distance_m=1000.0,
             elevation_difference_m=0.0, observer_floor_height_m=0.0)
    event = NS(location=loc, celestial_altitude=5.0, celestial_azimuth=180.0,
               subject_azimuth=180.0, event_type="Sonnen-Alignment", shoot_time=None)
    ca = P._composition_analysis(event)
    assert ca is not None
    assert ca["altitude_delta_deg"] is None  # 0 wird wie fehlend behandelt


# --- BUG-43: _passes_alignment_filter — partielle Analyse passiert Filter --------
def test_bug43_alignment_filter_passes_partial():
    """BUG-43: Partielle CA (altitude_delta_deg=None) → _passes_alignment_filter gibt True."""
    partial_ca = {
        "azimuth_delta_deg": 2.5,
        "altitude_delta_deg": None,
    }
    event_dict = {"event_type": "Mond-Alignment", "composition_analysis": partial_ca}
    assert P._passes_alignment_filter(event_dict) is True
