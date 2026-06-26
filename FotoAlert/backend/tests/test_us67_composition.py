"""Regressionssuite — US-67: Himmelsposition (Datengrundlage).

Sichert die *Datengrundlage* der US-67-Frontend-Sektion „🧭 Himmelsposition" ab:
`precompute._composition_analysis` muss die seitlichen/vertikalen Versätze mit
korrektem Vorzeichen liefern (negativ az_delta → Objekt links → negativer
lateral_offset) und für Setups ohne Motivgeometrie `None` zurückgeben — denn das
Frontend gated die Sektion exakt an `composition_analysis != null`.

Der Frontend-Textbau selbst (links/rechts/darüber/darunter, Schwellwörter) ist nicht
pytest-bar; hier wird die Logik der Werte abgesichert, auf die der Text aufbaut.

Konvention (vgl. test_astronomy_regression.py): Docstring jedes Tests nennt das
Ticket. Determinismus: Es werden ausschließlich Sonnen-Setups verwendet — die
nutzen einen festen Winkeldurchmesser und lösen keinen Ephemeriden-Zugriff aus.
"""
from types import SimpleNamespace as NS

import pytest

import precompute as P

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _make_event(*, subject_height_m=50.0, distance_m=1000.0,
                celestial_altitude=5.0, celestial_azimuth=178.0,
                subject_azimuth=180.0, event_type="Sonnen-Alignment"):
    """Minimales Opportunity-Mock, das _composition_analysis konsumiert.

    Geometrie der Defaults: Motivspitze (50 m auf 1000 m) erscheint unter ~2,86°.
    celestial_altitude 5° → Objekt steht darüber (altitude_delta > 0).
    celestial_azimuth 178° vs. subject_azimuth 180° → az_delta = -2° → Objekt links.
    """
    loc = NS(
        subject_height_m=subject_height_m,
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
        shoot_time=None,  # nur im Mond-Zweig benötigt
    )


# --- US-67: Vorzeichen seitlich — Objekt links → negativer lateral_offset ---------
# AK (Pre-Mortem): Backend-Konvention az_delta = celestial − subject (−180…+180);
# negativ = Objekt westlich/links der Sichtachse. Das Frontend übernimmt das Vorzeichen.
def test_us67_lateral_offset_negative_when_object_left():
    """US-67: az_delta < 0 (Objekt links) ⇒ lateral_offset_m < 0."""
    ca = P._composition_analysis(_make_event(celestial_azimuth=178.0, subject_azimuth=180.0))
    assert ca is not None
    assert ca["azimuth_delta_deg"] < 0, "Objekt links → az_delta muss negativ sein"
    assert ca["lateral_offset_m"] < 0, "links → lateral_offset_m muss negativ sein"


# --- US-67: Vorzeichen seitlich — Objekt rechts → positiver lateral_offset ---------
def test_us67_lateral_offset_positive_when_object_right():
    """US-67: az_delta > 0 (Objekt rechts) ⇒ lateral_offset_m > 0."""
    ca = P._composition_analysis(_make_event(celestial_azimuth=182.0, subject_azimuth=180.0))
    assert ca is not None
    assert ca["azimuth_delta_deg"] > 0, "Objekt rechts → az_delta muss positiv sein"
    assert ca["lateral_offset_m"] > 0, "rechts → lateral_offset_m muss positiv sein"


# --- US-67: Vorzeichen vertikal — Objekt über Motivspitze → positiver vertical_offset
def test_us67_vertical_offset_sign_matches_altitude_delta():
    """US-67: Objekt über der Motivspitze ⇒ altitude_delta_deg > 0 und vertical_offset_m > 0;
    Objekt darunter ⇒ beide negativ."""
    above = P._composition_analysis(_make_event(celestial_altitude=5.0))   # > 2,86°
    below = P._composition_analysis(_make_event(celestial_altitude=1.0))   # < 2,86°
    assert above["altitude_delta_deg"] > 0 and above["vertical_offset_m"] > 0
    assert below["altitude_delta_deg"] < 0 and below["vertical_offset_m"] < 0


# --- US-67: body_name aus Event-Typ abgeleitet (nie hartkodiert) ------------------
def test_us67_body_name_sun_for_sun_event():
    """US-67: Sonnen-Event ⇒ body_name == 'Sonne'."""
    ca = P._composition_analysis(_make_event(event_type="Sonnen-Alignment"))
    assert ca["body_name"] == "Sonne"


# --- US-67: Gate — ohne distance_m liefert die Analyse None -------------------------
# AK: Ohne gültige distance_m ist kein metrischer Versatz berechenbar → None.
# Hinweis: subject_height_m=None liefert seit BUG-43 eine partielle Analyse (nicht None).
@pytest.mark.parametrize("missing", [
    {"distance_m": None},
    {"distance_m": 0.0},
])
def test_us67_returns_none_without_distance(missing):
    """US-67/BUG-43: Ohne gültige distance_m ⇒ composition_analysis is None."""
    ca = P._composition_analysis(_make_event(**missing))
    assert ca is None


# --- US-67: vertikaler Versatz kommt aus dem Cache (d·tan(altitude_delta)) ---------
# AK (Pre-Mortem): Meter nicht im Frontend neu rechnen — Backend liefert sie konsistent.
# Hier: Plausibilitätsanker, dass der gecachte Wert der Geometrie entspricht.
def test_us67_vertical_offset_matches_geometry():
    """US-67: vertical_offset_m ≈ distance_m · tan(altitude_delta_deg)."""
    import math
    ca = P._composition_analysis(_make_event(distance_m=1000.0, celestial_altitude=5.0))
    expected = 1000.0 * math.tan(math.radians(ca["altitude_delta_deg"]))
    assert abs(ca["vertical_offset_m"] - expected) < 0.5
