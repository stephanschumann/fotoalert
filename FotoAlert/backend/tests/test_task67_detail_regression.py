"""TASK-67 Etappe 2 — PRODUCT.md "Pflicht-Regression Detail" (Abschnitt 4), Teil-Automatisierung.

Deckt genau die zwei Punkte aus PRODUCT.md Abschnitt 4 ab, die sich laut Regel 1
(Example Mapping, TASK-67-Analyse) rein über einen API-/Serialisierungs-Datenwert prüfen
lassen — ohne echte Browser-Klick-Interaktion:

  - "Astronomie-Sektion zeigt Sonnenaufgang + Sonnenuntergang mit Uhrzeit + Azimut in
    Grad, wenn vorhanden (US-107)"
  - "Kein Azimut-Wert wenn sunrise_utc/sunset_utc null (kein Placeholder '0°') (US-107)"

Prüft `precompute._serialize()` end-to-end mit einem selbst gebauten, minimalen aber
echten `PhotoOpportunity`/`AstronomyReport`-Objekt (Pattern 12: keine externen Fixtures/
IDs, keine Netzwerk-Calls — `get_body_position()` ist eine reine Skyfield-Berechnung mit
lokalen Ephemeriden-Daten, kein HTTP).

Kein Overlap mit bestehenden Dateien: test_us79_moon_rise_set.py prüft dasselbe Muster für
Mondaufgang/-untergang (moonrise_azimuth/moonset_azimuth) bereits per Quellcode-Grep, aber
keine bestehende Datei ruft precompute._serialize() für den Sonnenaufgang/-untergang-Fall
(sunrise_azimuth/sunset_azimuth, US-107) tatsächlich funktional auf — vor dieser
Implementierung gab es dafür keinen Treffer in backend/tests/*.py.

NICHT Teil dieser Etappe (siehe PRODUCT.md-Referenzen statt Duplikat):
  - "Sheet öffnet sich von unten" / "Alle 12 Sektionen vorhanden, keine doppelt" /
    "Sektionen eingeklappt" / "Close-Button erreichbar" / "FOV-Karte lädt" / Vollbild-Symbole /
    "Zum Kalender"-Download / Street-View-Button-Sichtbarkeit / Sichtachsen-Linienstil —
    echte DOM-/Klick-Zustände, Etappe 3 (Playwright).
  - "Astronomie-Sektion zeigt Mondaufgang + Monduntergang ... Kein Fehler wenn null" —
    bereits automatisiert in test_us79_moon_rise_set.py.
  - "Sichtachsen-Check-Pille sichtbar mit korrekter Farbe/Text" / "Fehlende Höhen-/
    Gebäudedaten -> Status 'Nicht geprüft', niemals 'Frei'" — die Daten-Garantie dahinter
    ist bereits vollständig in test_us09_sightline.py automatisiert (Quelle der Wahrheit:
    evaluate_sightline()/update_location_sightline()); die Pillen-Darstellung selbst ist UI.

Python-3.9-kompatibel (kein `X | None`).
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.locations import PhotoLocation, LocationCategory  # noqa: E402
from calculations.opportunity import PhotoOpportunity, EventType  # noqa: E402
from calculations.astronomy import (  # noqa: E402
    AstronomyReport, SunInfo, MoonInfo, MilkyWayInfo,
)
import precompute  # noqa: E402

pytestmark = [pytest.mark.regression]


@pytest.fixture(autouse=True)
def _chdir_to_backend_for_skyfield(monkeypatch):
    """Kein Fixture-Lückenbug, sondern ein Cwd-Problem: `calculations.astronomy._get_eph()`
    lädt `de421.bsp` per Skyfield-`load("de421.bsp")` relativ zum Prozess-Arbeitsverzeichnis.
    Wird pytest (wie in der Projekt-Konvention) aus `FotoAlert/` gestartet, findet Skyfield
    die Datei dort nicht, versucht sie per HTTP nachzuladen — das scheitert im Sandbox ohne
    Netzwerk, und `_get_body_position_direct()` fängt die Exception still ab und gibt `None`
    zurück. `precompute._serialize()` erwartet dort aber ein `CelestialPosition`-Objekt und
    crasht mit `AttributeError: 'NoneType' object has no attribute 'azimuth'`.

    `de421.bsp` liegt tatsächlich lokal in `backend/` (siehe `ls backend/de421.bsp`) — es
    ist also weiterhin eine rein lokale, deterministische Berechnung ohne Netzwerk-Call
    (Pattern 12), nur das Arbeitsverzeichnis muss für die Dauer dieses Tests stimmen.
    """
    monkeypatch.chdir(Path(__file__).parent.parent)


def _make_location() -> PhotoLocation:
    return PhotoLocation(
        id="test-task67-detail-loc",
        name="TASK-67 Test-Location",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=52.50, observer_lon=13.40,
        subject_lat=52.51, subject_lon=13.41,
        subject_name="Test-Motiv",
    )


def _make_sun_info(sunrise, sunset) -> SunInfo:
    now = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
    return SunInfo(
        date=now.date(), sunrise=sunrise, sunset=sunset,
        golden_hour_morning_start=now, golden_hour_morning_end=now,
        golden_hour_evening_start=now, golden_hour_evening_end=now,
        blue_hour_morning_start=now, blue_hour_morning_end=now,
        blue_hour_evening_start=now, blue_hour_evening_end=now,
        solar_noon=now, day_length_hours=12.0,
    )


def _make_moon_info(moonrise=None, moonset=None) -> MoonInfo:
    return MoonInfo(
        date=date(2026, 6, 21), moonrise=moonrise, moonset=moonset,
        phase_fraction=0.5, phase_name="Vollmond", illumination_pct=99.0,
        azimuth_at_golden_hour=None, altitude_at_golden_hour=None,
    )


def _make_astronomy_report(sunrise=None, sunset=None) -> AstronomyReport:
    return AstronomyReport(
        sun=_make_sun_info(sunrise, sunset),
        moon=_make_moon_info(),
        milky_way=MilkyWayInfo(
            date=date(2026, 6, 21),
            galactic_center_azimuth_at_midnight=None,
            galactic_center_altitude_at_midnight=None,
            best_visibility_start=None, best_visibility_end=None,
            darkness_score=0.0, visible=False,
        ),
    )


def _make_opportunity(astronomy_report) -> PhotoOpportunity:
    loc = _make_location()
    now = datetime(2026, 6, 21, 4, 30, tzinfo=timezone.utc)
    return PhotoOpportunity(
        id="test-task67-detail-opp",
        location=loc,
        event_type=EventType.GOLDEN_HOUR_MORNING,
        title="Test-Chance", description="Test-Beschreibung",
        shoot_time=now, shoot_window_start=now, shoot_window_end=now,
        overall_score=0.8, astronomy_score=0.8, weather_score=0.0, location_score=0.8,
        camera_hints=[], subject_azimuth=90.0,
        celestial_azimuth=90.0, celestial_altitude=5.0, alert_priority=1,
        astronomy_report=astronomy_report,
    )


class TestSunriseSunsetAzimuthPresentWhenAvailable:
    """PRODUCT.md-Punkt: 'Astronomie-Sektion zeigt Sonnenaufgang + Sonnenuntergang mit
    Uhrzeit + Azimut in Grad, wenn vorhanden (US-107)'."""

    def test_serialize_contains_sunrise_and_sunset_azimuth_when_present(self):
        sunrise = datetime(2026, 6, 21, 3, 43, tzinfo=timezone.utc)
        sunset = datetime(2026, 6, 21, 19, 33, tzinfo=timezone.utc)
        report = _make_astronomy_report(sunrise=sunrise, sunset=sunset)
        opp = _make_opportunity(report)

        data = precompute._serialize(opp)

        assert data["sunrise_utc"] == sunrise.isoformat()
        assert data["sunset_utc"] == sunset.isoformat()
        assert data["sunrise_azimuth"] is not None
        assert data["sunset_azimuth"] is not None
        assert 0.0 <= data["sunrise_azimuth"] <= 360.0
        assert 0.0 <= data["sunset_azimuth"] <= 360.0


class TestNoAzimuthPlaceholderWhenSunriseSunsetNull:
    """PRODUCT.md-Punkt: 'Kein Azimut-Wert wenn sunrise_utc/sunset_utc null
    (kein Placeholder "0°") (US-107)'."""

    def test_sunrise_azimuth_is_none_when_sunrise_is_none(self):
        report = _make_astronomy_report(sunrise=None, sunset=None)
        opp = _make_opportunity(report)

        data = precompute._serialize(opp)

        assert data["sunrise_utc"] is None
        assert data["sunrise_azimuth"] is None, (
            "sunrise_azimuth darf bei fehlendem sunrise_utc nicht auf 0.0 "
            "fallbacken (kein stiller Placeholder statt None)"
        )
        assert data["sunrise_azimuth"] != 0.0

    def test_sunset_azimuth_is_none_when_sunset_is_none(self):
        report = _make_astronomy_report(sunrise=None, sunset=None)
        opp = _make_opportunity(report)

        data = precompute._serialize(opp)

        assert data["sunset_utc"] is None
        assert data["sunset_azimuth"] is None, (
            "sunset_azimuth darf bei fehlendem sunset_utc nicht auf 0.0 "
            "fallbacken (kein stiller Placeholder statt None)"
        )
        assert data["sunset_azimuth"] != 0.0

    def test_partial_availability_sunrise_present_sunset_null(self):
        """Edge Case: nur Sonnenaufgang bekannt (z.B. Polarsommer-Übergang) -> nur
        sunrise_azimuth gesetzt, sunset_azimuth bleibt None, kein Crash."""
        sunrise = datetime(2026, 6, 21, 3, 43, tzinfo=timezone.utc)
        report = _make_astronomy_report(sunrise=sunrise, sunset=None)
        opp = _make_opportunity(report)

        data = precompute._serialize(opp)

        assert data["sunrise_azimuth"] is not None
        assert data["sunset_azimuth"] is None
