"""Regressionssuite — BUG-90: Kompositions-Analyse fehlt bei Mondaufgang-/
Monduntergang-Ereignissen (fehlende Geometriedaten celestial_altitude).

Root Cause (Ticket-Spec, Code-Verifikation 2026-07-28): `backend/calculations/
opportunity.py`, Block "5b. MONDAUFGANG UND MONDUNTERGANG" (Zeilen 748-796)
setzt `celestial_azimuth`, aber nicht `celestial_altitude` in der
`PhotoOpportunity`-Erzeugung — dadurch bleibt `precompute._composition_analysis()`
für diese beiden Event-Typen immer `None` (Guard: `celestial_altitude is not
None`). Zusätzlich fehlen "Mondaufgang"/"Monduntergang" bislang in
`precompute._ALIGNMENT_FILTER_EXEMPT` — sobald `celestial_altitude` ergänzt
wird, würde ohne diese Erweiterung die neu aktive ±2°-Präzisionsprüfung die
meisten dieser (physikalisch fixen) Events aus Feed/Kalender/Monatsübersicht
herausfiltern (Pre-Mortem-Szenario "Stiller Sichtbarkeits-Kollaps").

Test-First (Option A, Weg-Gate 2026-07-28): Test 1 und Test 4 sind vor der
Implementierung ROT und belegen die beiden Lücken direkt. Test 2/3/5 prüfen
`precompute._composition_analysis()` selbst — diese Funktion ist bereits
vollständig generisch (kein event_type-Gate, siehe Code-Verifikation im
Ticket), sie sind deshalb bereits GRÜN und dienen ab der Implementierung als
Regressionsschutz für AK2/AK3/AK4/AK6.

Konvention (vgl. test_us67_composition.py / test_bug43_partial_composition.py):
NS-Mock-Events wie dort, hier mit event_type "Mondaufgang"/"Monduntergang".
`shoot_time=None` + `monkeypatch` auf `get_moon_earth_distance_km` verhindern
echten Ephemeriden-/Netzwerkzugriff (vgl. test_astronomy_regression.py-Kommentar
zu den dortigen @pytest.mark.online-Tests, die genau diesen Aufrufpfad nutzen).
"""
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

import precompute as P

pytestmark = [pytest.mark.offline, pytest.mark.regression]

_OPP_SRC_PATH = Path(__file__).parent.parent / "calculations" / "opportunity.py"


def _moonrise_moonset_block_source() -> str:
    """Isoliert den Quelltext-Block '5b. MONDAUFGANG UND MONDUNTERGANG' aus opportunity.py."""
    src = _OPP_SRC_PATH.read_text(encoding="utf-8")
    start = src.index("5b. MONDAUFGANG UND MONDUNTERGANG")
    end = src.index("# 6. METEORITENSCHAUER", start)
    return src[start:end]


def _make_moon_rise_set_event(*, event_type="Mondaufgang", distance_m=1200.0,
                               subject_height_m=None, celestial_altitude=6.0,
                               celestial_azimuth=181.5, subject_azimuth=180.0):
    """Mock-Event für Mondaufgang/Monduntergang (analog test_us67/test_bug43-Muster)."""
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
        shoot_time=None,  # Mond-Zweig in _compute_body_apparent_size fängt None ab (kein Netzwerk)
    )


# --- Test 1 (AK1/AK2-Vorbedingung): celestial_altitude wird im Block 5b gesetzt ---
def test_bug90_moonrise_moonset_block_sets_celestial_altitude():
    """BUG-90 AK1: Die PhotoOpportunity-Erzeugung für Mondaufgang/Monduntergang setzt
    celestial_altitude analog zu celestial_azimuth (Referenz: Mond-Alignment Zeile 535,
    3D-Alignment Zeile 662) — sonst bleibt composition_analysis für diese Events
    dauerhaft None, weil precompute._composition_analysis() celestial_altitude als
    Pflicht-Guard verlangt."""
    block = _moonrise_moonset_block_source()
    assert "celestial_altitude=" in block, (
        "Block '5b. MONDAUFGANG UND MONDUNTERGANG' in opportunity.py setzt "
        "celestial_altitude nicht in der PhotoOpportunity(...)-Erzeugung — "
        "composition_analysis bleibt für Mondaufgang/Monduntergang dauerhaft None (BUG-90)."
    )


# --- Test 2 (AK2/AK3): Kompositions-Analyse mit Höhen- UND Seitenversatz ---
def test_bug90_composition_analysis_with_subject_height(monkeypatch):
    """BUG-90 AK2/AK3: Liegt celestial_altitude vor UND ist eine Motivhöhe hinterlegt,
    liefert _composition_analysis() für ein Mondaufgang-Event sowohl vertical_offset_m
    als auch lateral_offset_m (beide nicht None)."""
    monkeypatch.setattr(P, "get_moon_earth_distance_km", lambda dt: 384_400.0)
    ca = P._composition_analysis(_make_moon_rise_set_event(
        event_type="Mondaufgang", subject_height_m=25.0, distance_m=1500.0,
    ))
    assert ca is not None, "composition_analysis ist None, obwohl celestial_altitude + distance_m vorliegen"
    assert ca["vertical_offset_m"] is not None
    assert ca["lateral_offset_m"] is not None


# --- Test 3 (AK4): nur Seitenversatz ohne hinterlegte Motivhöhe ---
def test_bug90_composition_analysis_without_subject_height(monkeypatch):
    """BUG-90 AK4 (Edge Case): Ohne subject_height_m liefert _composition_analysis() für
    ein Monduntergang-Event weiterhin lateral_offset_m, aber vertical_offset_m/
    altitude_delta_deg sind None — kein leeres/kaputtes Feld (BUG-43-Verhalten gilt
    unverändert auch für diesen Event-Typ)."""
    monkeypatch.setattr(P, "get_moon_earth_distance_km", lambda dt: 384_400.0)
    ca = P._composition_analysis(_make_moon_rise_set_event(
        event_type="Monduntergang", subject_height_m=None, distance_m=900.0,
    ))
    assert ca is not None
    assert ca["lateral_offset_m"] is not None
    assert ca["vertical_offset_m"] is None
    assert ca["altitude_delta_deg"] is None


# --- Test 4 (AK5, Regressionsschutz): Exempt-Set schützt vor der ±2°-Präzisionsprüfung ---
def test_bug90_alignment_filter_exempts_moonrise_moonset():
    """BUG-90 AK5 / Pre-Mortem 'Stiller Sichtbarkeits-Kollaps': _passes_alignment_filter()
    muss ein Mondaufgang-/Monduntergang-Event auch dann durchlassen, wenn dessen
    composition_analysis-Deltas > 2° liegen — weil deren Zeitpunkt physikalisch fix ist
    (nicht gezielt auf enge Ausrichtung gesucht wie bei Mond-/3D-Alignment). Ohne die
    Exempt-Set-Erweiterung würden die meisten dieser Events nach der
    celestial_altitude-Ergänzung unbeabsichtigt aus Feed/Kalender/Monatsübersicht
    verschwinden — genau der Regressionsbug, den Option A verhindern soll."""
    ca_out_of_tolerance = {"azimuth_delta_deg": 12.0, "altitude_delta_deg": 9.0}
    for event_type in ("Mondaufgang", "Monduntergang"):
        event_dict = {"event_type": event_type, "composition_analysis": ca_out_of_tolerance}
        assert P._passes_alignment_filter(event_dict) is True, (
            f"'{event_type}' fällt bei > 2°-Deltas durch den Alignment-Filter — "
            f"fehlt noch in precompute._ALIGNMENT_FILTER_EXEMPT (BUG-90)."
        )


# --- Test 5 (AK6): keine Kompositions-Analyse ohne Motiv-Entfernung ---
def test_bug90_composition_analysis_none_without_distance(monkeypatch):
    """BUG-90 AK6 (Edge Case): Hat die Location keine hinterlegte distance_m, bleibt
    _composition_analysis() für Mondaufgang/Monduntergang weiterhin None — kein Absturz."""
    monkeypatch.setattr(P, "get_moon_earth_distance_km", lambda dt: 384_400.0)
    ca = P._composition_analysis(_make_moon_rise_set_event(
        event_type="Mondaufgang", distance_m=None,
    ))
    assert ca is None
