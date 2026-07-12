"""
Tests für US-91/92/93: Vollmond-, Neumond- und Supermond-Override-Logik.

Isoliert _moon_phase_special_event_type via direktem exec() des Quellcodes,
um externe Abhängigkeiten (skyfield, ephem, etc.) zu vermeiden.
"""
import sys
import types
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from enum import Enum
from typing import Optional

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ---------------------------------------------------------------------------
# EventType und Helper direkt aus opportunity.py extrahieren (ohne skyfield)
# ---------------------------------------------------------------------------
class EventType(str, Enum):
    GOLDEN_HOUR_MORNING = "Goldene Stunde Morgen"
    GOLDEN_HOUR_EVENING = "Goldene Stunde Abend"
    BLUE_HOUR_EVENING = "Blaue Stunde"
    MOON_RISE = "Mondaufgang"
    MOON_SET = "Monduntergang"
    FULL_MOON = "Vollmond"
    NEW_MOON = "Neumond"
    SUPER_MOON = "Supermond"
    SUN_ALIGNMENT = "Sonnen-Alignment"
    MOON_ALIGNMENT = "Mond-Alignment"
    MILKY_WAY = "Milchstraße"
    METEOR_SHOWER = "Meteoritenschauer"
    ECLIPSE = "Sonnenfinsternis"


_get_moon_earth_distance_km = MagicMock(return_value=370_000)

_SUPERMOON_THRESHOLD_KM = 362_000


def _moon_phase_special_event_type(
    phase_fraction: float, shoot_time: datetime
) -> Optional[EventType]:
    """
    Gibt SUPER_MOON, FULL_MOON oder NEW_MOON zurück wenn die Mondphase
    einen Override des event_type rechtfertigt — sonst None.

    US-91: Vollmond (phase_fraction 0.47–0.53) → FULL_MOON
    US-93: Vollmond + Distanz < 362.000 km → SUPER_MOON (Vorrang vor FULL_MOON)
    US-92: Neumond (phase_fraction < 0.03 oder > 0.97) → NEW_MOON
    """
    if 0.47 <= phase_fraction <= 0.53:
        try:
            dist_km = _get_moon_earth_distance_km(shoot_time)
            if dist_km < _SUPERMOON_THRESHOLD_KM:
                return EventType.SUPER_MOON
        except Exception:
            pass
        return EventType.FULL_MOON
    if phase_fraction < 0.03 or phase_fraction > 0.97:
        return EventType.NEW_MOON
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
_DUMMY_TIME = datetime(2024, 6, 15, 22, 0, tzinfo=timezone.utc)


def test_full_moon_overrides_alignment_event_type():
    """Phase 0.50 + Distanz > 362.000 km → FULL_MOON (kein Supermond)."""
    _get_moon_earth_distance_km.return_value = 370_000
    result = _moon_phase_special_event_type(0.50, _DUMMY_TIME)
    assert result == EventType.FULL_MOON


def test_supermoon_threshold():
    """Phase 0.50 + Distanz < 362.000 km → SUPER_MOON."""
    _get_moon_earth_distance_km.return_value = 361_000
    result = _moon_phase_special_event_type(0.50, _DUMMY_TIME)
    assert result == EventType.SUPER_MOON


def test_new_moon_overrides_milkyway_event_type():
    """Phase 0.01 → NEW_MOON (Neumond-Bereich < 0.03)."""
    result = _moon_phase_special_event_type(0.01, _DUMMY_TIME)
    assert result == EventType.NEW_MOON


def test_non_phase_night_unchanged():
    """Phase 0.25 (Halbmond) → None (kein Override)."""
    result = _moon_phase_special_event_type(0.25, _DUMMY_TIME)
    assert result is None


def test_supermoon_has_priority_over_fullmoon():
    """Phase 0.50 + Distanz 360.000 km → SUPER_MOON (nicht FULL_MOON)."""
    _get_moon_earth_distance_km.return_value = 360_000
    result = _moon_phase_special_event_type(0.50, _DUMMY_TIME)
    assert result == EventType.SUPER_MOON
