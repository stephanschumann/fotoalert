"""TASK-103 — Bearbeiten gespeicherter Orte auf Host beschränken (Anlegen bleibt für User).

Root Cause / Change: PATCH /locations/{loc_id} (main.py, patch_location) verlangte
bisher nur auth.require_auth (jede eingeloggte Rolle). TASK-103 stellt das auf
auth.require_host um — identisch zum bereits bestehenden Muster bei
DELETE /locations/{loc_id} und den Bild-Endpunkten. Anlegen neuer Orte über
POST /preview-alignment (save=true) bleibt unverändert auf auth.require_auth und
damit für die User-Rolle weiterhin möglich (TASK-103 betrifft nur das Bearbeiten
bestehender Orte, nicht das Anlegen).

Diese Datei bündelt die Akzeptanzkriterien des Tickets explizit an einem Ort.
Die einzelnen AKs sind zusätzlich (mit fachlichem Kontext) in den jeweils
betroffenen Bestandstestdateien verankert:
  - test_us66_login.py::TestEndpointProtection (AK1 + AK2, Rollen-Vertrag)
  - test_api_regression.py::TestBug22RecomputeWhitelist (host_headers-Umstellung)
  - test_patch_cache_consistency.py, test_bug-61.py (host_headers-Umstellung)
  - test_task-83.py (Cookie-Login-Passwort-Umstellung)
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]

LOC = "custom_1781560330"


@pytest.fixture(autouse=True)
def _seed_test_location(ensure_seed_location):
    """Stellt custom_1781560330 sicher (siehe test_api_regression.py, gleiches Muster)."""


class TestTask103PatchLocationHostOnly:
    """AK1 + AK2 + AK4: Rollen-Vertrag für PATCH /locations/{id}."""

    def test_ak1_patch_with_user_access_is_forbidden(self, client, auth_headers):
        """AK1: PATCH mit User-Zugang → 403 (nicht mehr 200 wie vor TASK-103)."""
        r = client.patch(f"/locations/{LOC}", json={"name": "TASK-103 User-Versuch"}, headers=auth_headers)
        assert r.status_code == 403, r.text

    def test_ak2_patch_with_host_access_still_succeeds(self, client, host_headers):
        """AK2: PATCH mit Host-Zugang → weiterhin 200, Feldänderung wirkt (GET spiegelt sie)."""
        new_name = "TASK-103 Host-Edit"
        r = client.patch(f"/locations/{LOC}", json={"name": new_name}, headers=host_headers)
        assert r.status_code == 200, r.text

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == LOC), None)
        assert loc is not None, f"Location {LOC} nicht in GET /locations gefunden"
        assert loc["name"] == new_name, (
            f"Name nach Host-PATCH: '{loc['name']}' — erwartet: '{new_name}'."
        )

    def test_ak4_patch_without_any_token_still_401_not_403(self, client):
        """AK4: PATCH ganz ohne Token → weiterhin 401 (nicht 403) — TASK-67-Pflicht-
        regression darf nicht brechen. require_host hängt von require_auth ab, das
        VOR der Rollenprüfung greift: fehlt das Sitzungs-Cookie komplett, muss die
        Antwort weiterhin "nicht eingeloggt" (401) sein, nicht "falsche Rolle" (403)."""
        r = client.patch(f"/locations/{LOC}", json={"name": "TASK-103 ohne Token"})
        assert r.status_code == 401, r.text


class TestTask103CreateLocationUnaffected:
    """AK3: Neuen Standort anlegen bleibt für User-Zugang unverändert möglich —
    reiner Regressionscheck, POST /preview-alignment wurde durch TASK-103 nicht
    angefasst (main.py: weiterhin auth.require_auth, nicht auth.require_host)."""

    def test_ak3_save_new_location_with_user_access_still_works(self, client, auth_headers):
        payload = {
            "observer_lat": 52.4300,
            "observer_lon": 13.5300,
            "subject_lat": 52.4350,
            "subject_lon": 13.5350,
            "subject_name": "TASK-103 Neuer-Standort-Test",
            "subject_height_m": 0.0,
            "subject_width_m": 0.0,
            "days": 1,
            "save": True,
        }
        r = client.post("/preview-alignment", json=payload, headers=auth_headers)
        assert r.status_code == 200, r.text

        locations = client.get("/locations").json()
        assert any(l.get("subject_name") == "TASK-103 Neuer-Standort-Test" for l in locations), (
            "Neu angelegter Standort (User-Zugang) nicht in GET /locations gefunden — "
            "AK3-Regression: Anlegen sollte durch TASK-103 nicht betroffen sein."
        )
