"""
BUG-66 — "Höhenwinkel Spitze" in der Location-Anlage-Vorschau zeigt immer 0°,
weil der Geländeunterschied (elevation_difference_m) im Endpoint
POST /preview-alignment (backend/main.py, Funktion preview_alignment) nie
automatisch ermittelt und an calculate_subject_angular_profile() übergeben wird.

Spec-Bezug (BACKLOG.md, Ticket BUG-66, Akzeptanzkriterien):
  1. Location mit echtem Höhenunterschied -> "Höhenwinkel Spitze" nach
     "Alignments berechnen" ist ungleich 0° und spiegelt den Unterschied wider.
  2. Location ohne nennenswerten Höhenunterschied -> Wert bleibt nahe 0°
     (kein falscher Ausschlag).
  3. Keine Höhendaten für die Gegend verfügbar -> kein Crash, sinnvoller
     Rückfallwert (0°) statt 500er.
  4. Regressionsschutz zu BUG-63 (Endpoint blockiert ca. 20-25s): der neue
     Geländeunterschied-Abruf darf NICHT pro Alignment-Iteration (Tag x
     Himmelskörper) erneut aufgerufen werden, sondern genau einmal pro
     Preview-Anfrage (sonst Vervielfachung der externen Netzwerk-Calls).

Diese Tests spiegeln die Spec, nicht die (noch nicht existierende)
Implementierung — sie schlagen aktuell erwartungsgemäß fehl (TDD), bis
preview_alignment() den bestehenden Elevation-Mechanismus (siehe /plan-
Endpoint, backend/main.py ~Zeile 1642-1645, und data/elevation.py,
ElevationProvider.elevation_difference()) auch im Anlage-Vorschau-Pfad nutzt.

Python-3.9-kompatibel (kein `X | None`).
"""
from __future__ import annotations

import math

import pytest

from data.elevation import ElevationProvider, provider

pytestmark = [pytest.mark.api, pytest.mark.regression]


def _cache_key(lat: float, lon: float) -> str:
    """Muss exakt zu data.elevation._key() passen (round auf 4 Nachkommastellen)."""
    return f"{round(lat, 4)},{round(lon, 4)}"


def _preview_payload(observer_lat, observer_lon, subject_lat, subject_lon, **overrides):
    payload = {
        "observer_lat": observer_lat,
        "observer_lon": observer_lon,
        "subject_lat": subject_lat,
        "subject_lon": subject_lon,
        "subject_name": "Unbenannt",  # Default -> save=False speichert nie (main.py _save_alignment_as_location)
        "subject_height_m": 0.0,
        "subject_width_m": 0.0,
        "days": 1,
        "save": False,
    }
    payload.update(overrides)
    return payload


class TestAngularAltitudeReflectsElevationDifference:
    """AK 1: echter Geländeunterschied fließt in den Winkel ein (nicht mehr 0°)."""

    def test_known_elevation_difference_produces_nonzero_angle(self, client, auth_headers, monkeypatch):
        observer_lat, observer_lon = 52.1000, 13.0000
        subject_lat, subject_lon = 52.1200, 13.0300

        # Deterministisch, kein Netzwerk: Cache-Einträge direkt setzen (Muster aus
        # test_ephemeris_engine.py::test_edge_missing_elevation_fallback).
        monkeypatch.setitem(provider._cache, _cache_key(observer_lat, observer_lon), 40.0)
        monkeypatch.setitem(provider._cache, _cache_key(subject_lat, subject_lon), 140.0)
        # -> elevation_difference_m = 140.0 - 40.0 = 100.0

        payload = _preview_payload(observer_lat, observer_lon, subject_lat, subject_lon)
        r = client.post("/preview-alignment", json=payload, headers=auth_headers)
        assert r.status_code == 200, r.text
        profile = r.json()["profile"]

        assert profile["angular_altitude_top_deg"] != 0.0, (
            "Trotz 100m Geländeunterschied bleibt der Winkel bei 0° - "
            "elevation_difference_m wird offenbar weiterhin nicht einbezogen."
        )
        # Formel aus calculate_subject_angular_profile() gegen die bekannte
        # Differenz (100.0m) und die vom Endpoint selbst gelieferte Distanz
        # nachrechnen (kein geratener Distanzwert):
        ground_distance_m = profile["ground_distance_m"]
        observer_height_m = 1.6  # Augenhöhe Fotograf, Funktionsdefault
        effective_height = max(0.0, 0.0 + 100.0 - observer_height_m)
        expected_deg = math.degrees(math.atan2(effective_height, ground_distance_m))
        assert math.isclose(profile["angular_altitude_top_deg"], expected_deg, abs_tol=0.01), (
            f"Erwartet ~{expected_deg:.3f}° (100m Geländeunterschied berücksichtigt), "
            f"bekam {profile['angular_altitude_top_deg']}°."
        )


class TestAngularAltitudeStaysNearZeroWithoutElevationDifference:
    """AK 2: kein nennenswerter Geländeunterschied -> Wert bleibt nahe 0°."""

    def test_equal_elevations_keep_angle_at_zero(self, client, auth_headers, monkeypatch):
        observer_lat, observer_lon = 52.2000, 13.1000
        subject_lat, subject_lon = 52.2050, 13.1050

        monkeypatch.setitem(provider._cache, _cache_key(observer_lat, observer_lon), 55.0)
        monkeypatch.setitem(provider._cache, _cache_key(subject_lat, subject_lon), 55.0)
        # -> elevation_difference_m = 0.0

        payload = _preview_payload(observer_lat, observer_lon, subject_lat, subject_lon)
        r = client.post("/preview-alignment", json=payload, headers=auth_headers)
        assert r.status_code == 200, r.text
        profile = r.json()["profile"]

        assert profile["angular_altitude_top_deg"] == 0.0, (
            "Ohne Geländeunterschied und ohne Motivhöhe sollte der Winkel bei 0° "
            f"bleiben, bekam {profile['angular_altitude_top_deg']}° (falscher Ausschlag)."
        )


class TestMissingElevationCoverageFallsBackWithoutCrash:
    """AK 3: fehlende Höhendaten (DEM-Lücke) -> kein Crash, Rückfallwert 0°."""

    def test_missing_dem_coverage_returns_200_with_zero_fallback(self, client, auth_headers, monkeypatch):
        observer_lat, observer_lon = 10.0000, 10.0000
        subject_lat, subject_lon = 10.0100, 10.0100

        # Sicherstellen, dass diese Koordinaten NICHT bereits im (prozessweiten)
        # Tile-Cache stehen, damit der Lookup wirklich bei _fetch_elevation landet.
        monkeypatch.delitem(provider._cache, _cache_key(observer_lat, observer_lon), raising=False)
        monkeypatch.delitem(provider._cache, _cache_key(subject_lat, subject_lon), raising=False)
        # Fehlende DEM-Abdeckung deterministisch simulieren (kein echter Netzwerk-Call):
        monkeypatch.setattr(ElevationProvider, "_fetch_elevation",
                             lambda self, lat, lon: _none_coro())

        payload = _preview_payload(observer_lat, observer_lon, subject_lat, subject_lon)
        r = client.post("/preview-alignment", json=payload, headers=auth_headers)

        assert r.status_code == 200, (
            f"Fehlende Höhendaten dürfen die Vorschau nicht crashen lassen, bekam {r.status_code}: {r.text}"
        )
        assert r.json()["profile"]["angular_altitude_top_deg"] == 0.0


async def _none_coro():
    return None


class TestElevationLookupHappensOncePerRequest:
    """AK 4 / Pre-Mortem BUG-63: der Geländeunterschied-Abruf darf pro Anfrage
    nur EINMAL passieren, nicht einmal pro (Himmelskörper x Tag)-Iteration in
    der Alignment-Schleife von preview_alignment(). Sonst vervielfacht sich der
    externe Netzwerk-Call und verschärft die bereits bekannte Blockade aus BUG-63."""

    def test_elevation_difference_called_at_most_once(self, client, auth_headers, monkeypatch):
        observer_lat, observer_lon = 52.3000, 13.2000
        subject_lat, subject_lon = 52.3100, 13.2100

        call_count = {"n": 0}
        original = provider.elevation_difference

        async def _counting(*args, **kwargs):
            call_count["n"] += 1
            return 25.0, False

        monkeypatch.setattr(provider, "elevation_difference", _counting)

        # days=3 -> Alignment-Schleife läuft 2 (sun/moon) x 3 Tage = 6 Iterationen.
        # Ein fälschlich in der Schleife platzierter Abruf würde call_count auf
        # bis zu 6 hochtreiben statt bei 1 zu bleiben.
        payload = _preview_payload(observer_lat, observer_lon, subject_lat, subject_lon, days=3)
        r = client.post("/preview-alignment", json=payload, headers=auth_headers)
        assert r.status_code == 200, r.text

        assert call_count["n"] == 1, (
            f"elevation_difference() wurde {call_count['n']}x aufgerufen, erwartet genau 1x "
            "pro Anfrage (Regressionsschutz BUG-63: keine Mehrfach-Netzwerk-Calls pro Preview)."
        )
