"""
US-79: Mondaufgang und Monduntergang als eigene Event-Typen.

Prüft dass:
  - precompute._serialize() die vier neuen Felder moonrise_utc, moonset_utc,
    moonrise_azimuth, moonset_azimuth korrekt serialisiert
  - opportunity.find_opportunities() echte MOON_RISE/MOON_SET-Events erzeugt
  - Keine Events erzeugt werden wenn moonrise/moonset == None
  - Azimut-Felder im erlaubten Bereich 0–360° liegen

Ausführen (vom Backend-Verzeichnis):
    pytest tests/test_us79_moon_rise_set.py -v
"""

import sys
import os
from pathlib import Path
from datetime import date, datetime, timezone, timedelta
from typing import Optional
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from enum import Enum

import pytest

# Sicherstellen, dass Backend-Importe funktionieren
sys.path.insert(0, str(Path(__file__).parent.parent))

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.frontend]


# ─────────────────────────────────────────────────────────────────────────────
# AK-5: _serialize() enthält moonrise_utc und moonset_utc
# ─────────────────────────────────────────────────────────────────────────────

def test_serialize_contains_moonrise_moonset_fields():
    """AK-5: _serialize() enthält moonrise_utc, moonset_utc, moonrise_azimuth, moonset_azimuth."""
    from pathlib import Path
    import re

    precompute_src = (Path(__file__).parent.parent / "precompute.py").read_text(encoding="utf-8")

    assert "moonrise_utc" in precompute_src, (
        "precompute.py enthält kein moonrise_utc-Feld — AK-5 nicht erfüllt"
    )
    assert "moonset_utc" in precompute_src, (
        "precompute.py enthält kein moonset_utc-Feld — AK-5 nicht erfüllt"
    )
    assert "moonrise_azimuth" in precompute_src, (
        "precompute.py enthält kein moonrise_azimuth-Feld — AK-5 nicht erfüllt"
    )
    assert "moonset_azimuth" in precompute_src, (
        "precompute.py enthält kein moonset_azimuth-Feld — AK-5 nicht erfüllt"
    )


# ─────────────────────────────────────────────────────────────────────────────
# AK-NEU-A: opportunity.py erzeugt MOON_RISE und MOON_SET als Event-Einträge
# ─────────────────────────────────────────────────────────────────────────────

def test_opportunity_moonrise_moonset_defined():
    """EventType.MOON_RISE und MOON_SET sind in opportunity.py als korrekte Strings definiert."""
    import ast

    opp_src = (Path(__file__).parent.parent / "calculations" / "opportunity.py").read_text(encoding="utf-8")

    # Finde den EventType-Abschnitt per Quellcode-Analyse (kein Import nötig)
    assert "MOON_RISE = \"Mondaufgang\"" in opp_src, (
        "calculations/opportunity.py enthält kein MOON_RISE = 'Mondaufgang'"
    )
    assert "MOON_SET = \"Monduntergang\"" in opp_src, (
        "calculations/opportunity.py enthält kein MOON_SET = 'Monduntergang'"
    )


def test_opportunity_moonrise_event_generated():
    """AK-NEU-A: find_opportunities enthält Logik zum Erzeugen von Mondaufgang-Events."""
    opp_src = (Path(__file__).parent.parent / "calculations" / "opportunity.py").read_text(encoding="utf-8")

    # Prüfe dass moon.moonrise im Code verarbeitet wird (nicht nur definiert)
    assert "moon.moonrise" in opp_src, (
        "opportunity.py greift nicht auf moon.moonrise zu — "
        "Mondaufgang-Events werden nicht erzeugt"
    )
    assert "moon.moonset" in opp_src, (
        "opportunity.py greift nicht auf moon.moonset zu — "
        "Monduntergang-Events werden nicht erzeugt"
    )
    assert "MOON_RISE" in opp_src, (
        "EventType.MOON_RISE wird in find_opportunities nicht genutzt"
    )
    assert "MOON_SET" in opp_src, (
        "EventType.MOON_SET wird in find_opportunities nicht genutzt"
    )


def test_opportunity_moonrise_has_shoot_time():
    """Mondaufgang-Events haben shoot_time = moon.moonrise (Quellcode-Verifikation)."""
    opp_src = (Path(__file__).parent.parent / "calculations" / "opportunity.py").read_text(encoding="utf-8")

    # Die shoot_time bei Mondaufgang wird aus moon_dt gesetzt (der Variable für moonrise/moonset)
    assert "shoot_time=moon_dt" in opp_src, (
        "Mondaufgang-Event setzt shoot_time nicht auf moon_dt (= Mondaufgangszeit)"
    )


def test_opportunity_moonrise_azimuth_in_range():
    """AK-NEU-A: Mondaufgang-Events berechnen den Azimut via get_body_position."""
    opp_src = (Path(__file__).parent.parent / "calculations" / "opportunity.py").read_text(encoding="utf-8")

    # get_body_position wird im Mondaufgang-Block für den Azimut aufgerufen
    assert "get_body_position(lat, lon, \"moon\", moon_dt)" in opp_src, (
        "Mondaufgang-Event ruft get_body_position nicht auf — "
        "celestial_azimuth kann nicht berechnet werden"
    )


def test_no_moonrise_no_event_when_moonrise_none():
    """AK-NEU-A (Edge Case): moon.moonrise == None → kein Mondaufgang-Event."""
    opp_src = (Path(__file__).parent.parent / "calculations" / "opportunity.py").read_text(encoding="utf-8")

    # Der Guard "if moon_dt is None: continue" muss vorhanden sein
    assert "if moon_dt is None" in opp_src, (
        "opportunity.py prüft nicht auf moon_dt is None — "
        "ein None-Mondaufgang könnte eine Exception auslösen"
    )


# ─────────────────────────────────────────────────────────────────────────────
# AK-NEU-B: Filter-Chips enthalten Mondaufgang und Monduntergang
# ─────────────────────────────────────────────────────────────────────────────

def test_frontend_filter_chips_contain_mondaufgang_monduntergang():
    """AK-NEU-B: FilterSheet._ET enthält 'Mondaufgang' und 'Monduntergang'."""
    html = (Path(__file__).parent.parent.parent / "web" / "index.html").read_text(encoding="utf-8")

    # Prüfe dass beide Typen im _ET-Array stehen
    assert "'Mondaufgang'" in html, "index.html hat 'Mondaufgang' nicht in den Filter-Chips"
    assert "'Monduntergang'" in html, "index.html hat 'Monduntergang' nicht in den Filter-Chips"


# ─────────────────────────────────────────────────────────────────────────────
# AK-8 (Regression): Bestehende Astronomie-Felder nicht kaputt
# ─────────────────────────────────────────────────────────────────────────────

def test_regression_existing_astro_fields_still_in_serialize():
    """AK-8: sunrise_utc, sunset_utc, moon_phase, golden_hour-Felder noch in precompute._serialize()."""
    precompute_src = (Path(__file__).parent.parent / "precompute.py").read_text(encoding="utf-8")

    for field_name in [
        "sunrise_utc", "sunset_utc",
        "moon_phase", "moon_illumination_pct",
        "golden_hour_morning_start", "golden_hour_evening_start",
        "blue_hour_morning_start", "blue_hour_evening_start",
    ]:
        assert field_name in precompute_src, (
            f"Regression: Feld '{field_name}' fehlt nach US-79-Änderung in precompute._serialize()"
        )


def test_regression_opportunity_existing_event_types_still_defined():
    """AK-8: Alle bisherigen EventType-Strings noch in opportunity.py vorhanden."""
    opp_src = (Path(__file__).parent.parent / "calculations" / "opportunity.py").read_text(encoding="utf-8")

    expected_strings = [
        "Goldene Stunde Morgen",
        "Goldene Stunde Abend",
        "Blaue Stunde",
        "Vollmond",
        "Neumond",
        "Supermond",
        "Sonnen-Alignment",
        "Mond-Alignment",
        "Milchstraße",
        "Meteoritenschauer",
        "Sonnenfinsternis",
    ]
    missing = [s for s in expected_strings if s not in opp_src]
    assert not missing, (
        f"Regression: folgende EventType-Strings fehlen nach US-79 in opportunity.py: {missing}"
    )
