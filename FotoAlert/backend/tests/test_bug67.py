"""
BUG-67 - Neu angelegte Location erscheint nicht direkt in Karte oder Locations-Liste.

Root Cause (Analyse 2026-07-09, Code-Verifikation):
  Das eigentliche Rendering-Problem sitzt rein im Frontend (web/index.html):
  - AddLocation.save() ruft nach dem Speichern zwar Locations.load() und
    Feed.load() auf, aber nie MapView.loadMarkers() -> die Kartenmarker
    werden nur beim allerersten MapView.init()-Aufruf geladen (frueher
    Return "if (this.map) return;"), danach nie wieder automatisch.
  - Ob die Locations-Liste tatsächlich betroffen ist, war beim Code-Lesen
    nicht abschliessend zu klaeren (Locations.load() rendert eigentlich
    direkt neu) - als offene Frage an Stephan zurueckgespiegelt.

Dieser Testfall deckt NICHT den Frontend-Renderpfad ab (dafuer gibt es
keinen automatisierten Test-Harness in diesem Projekt), sondern sichert
die Backend-Voraussetzung ab, auf der der Frontend-Fix aufbaut: Eine per
POST /preview-alignment (save=true) neu angelegte Location muss SOFORT
(synchron, ohne Wartezeit/Race) ueber GET /locations abrufbar sein - sonst
wuerde selbst ein korrekter Frontend-Reload-Fix die Location nicht finden.

Spec-Bezug (BACKLOG.md, Ticket BUG-67, Akzeptanzkriterien):
  AK „Nach dem Speichern ist die neue Location sofort ueber GET /locations
  auffindbar" - Regressionsschutz, falls _save_alignment_as_location()
  jemals auf einen asynchronen/verzoegerten Schreibpfad umgestellt wird.

Python-3.9-kompatibel (kein `X | None`).
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.api]


def _save_payload(observer_lat, observer_lon, subject_lat, subject_lon, subject_name, **overrides):
    payload = {
        "observer_lat": observer_lat,
        "observer_lon": observer_lon,
        "subject_lat": subject_lat,
        "subject_lon": subject_lon,
        "subject_name": subject_name,  # != "Unbenannt" ist Pflicht damit gespeichert wird
        "subject_height_m": 0.0,
        "subject_width_m": 0.0,
        "days": 1,
        "save": True,
    }
    payload.update(overrides)
    return payload


class TestNewLocationImmediatelyAvailableViaGetLocations:
    """AK: Neu gespeicherte Location ist sofort (ohne Verzoegerung) ueber
    GET /locations auffindbar - Backend-Voraussetzung fuer den Frontend-Fix."""

    def test_saved_location_appears_immediately_in_locations_list(self, client, auth_headers):
        observer_lat, observer_lon = 52.4000, 13.5000
        subject_lat, subject_lon = 52.4050, 13.5050
        subject_name = "BUG-67 Testmotiv"

        payload = _save_payload(observer_lat, observer_lon, subject_lat, subject_lon, subject_name)
        r = client.post("/preview-alignment", json=payload, headers=auth_headers)
        assert r.status_code == 200, r.text
        body = r.json()

        assert body["saved"] is True, "Location wurde nicht als gespeichert markiert."
        new_id = body["location_id"]
        assert new_id, "Keine location_id im Response - Frontend kann nicht pollen/nachladen."

        # Sofort danach abrufen - kein sleep, keine Wartezeit: muss synchron sichtbar sein.
        r2 = client.get("/locations")
        assert r2.status_code == 200, r2.text
        ids = [loc["id"] for loc in r2.json()]
        assert new_id in ids, (
            f"Neu gespeicherte Location {new_id} fehlt direkt nach dem Speichern in GET /locations - "
            "ein Frontend-Reload-Fix koennte die Location dann trotzdem nicht finden."
        )

    def test_saved_location_has_expected_name_and_coordinates(self, client, auth_headers):
        observer_lat, observer_lon = 52.4100, 13.5100
        subject_lat, subject_lon = 52.4150, 13.5150
        subject_name = "BUG-67 Testmotiv 2"

        payload = _save_payload(observer_lat, observer_lon, subject_lat, subject_lon, subject_name)
        r = client.post("/preview-alignment", json=payload, headers=auth_headers)
        assert r.status_code == 200, r.text
        new_id = r.json()["location_id"]

        r2 = client.get("/locations")
        matches = [loc for loc in r2.json() if loc["id"] == new_id]
        assert len(matches) == 1, f"Erwartet genau 1 Treffer fuer {new_id}, bekam {len(matches)}."
        loc = matches[0]
        assert loc["name"] == subject_name
        assert loc["observer_lat"] == pytest.approx(observer_lat)
        assert loc["observer_lon"] == pytest.approx(observer_lon)
