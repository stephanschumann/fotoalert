"""API-Regressionssuite — Endpoint-Verhalten aus Akzeptanzkriterien (data_dev, nie Prod).

Wie test_astronomy_regression.py, aber auf Endpoint-Ebene über den FastAPI-TestClient.
Jeder Test nennt im Docstring die Ticket-ID, deren AK er absichert.
"""
import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]

# Location aus data_dev (siehe TASK-19-Seed). Custom-Location, damit der PATCH-Schreibpfad
# (Store/SQLite) mitgetestet wird.
LOC = "custom_1781560330"


class TestBug22RecomputeWhitelist:
    """BUG-22: Nur recompute-relevante Felder lösen einen Recompute aus.

    Seit US-66 (Option B) ist PATCH /locations/{id} geschützt → alle Requests
    authentifiziert (auth_headers-Fixture).

    AK:
    - PATCH auf focal_length_suggestions  → recompute_triggered True
    - PATCH auf observer_floor_height_m   → recompute_triggered True
    - PATCH auf name/description          → recompute_triggered False
    """

    def test_focal_length_triggers_recompute(self, client, auth_headers):
        r = client.patch(f"/locations/{LOC}", json={"focal_length_suggestions": [50, 135]}, headers=auth_headers)
        assert r.status_code == 200, r.text
        assert r.json()["recompute_triggered"] is True

    def test_floor_height_triggers_recompute(self, client, auth_headers):
        r = client.patch(f"/locations/{LOC}", json={"observer_floor_height_m": 12.0}, headers=auth_headers)
        assert r.status_code == 200, r.text
        assert r.json()["recompute_triggered"] is True

    def test_name_does_not_trigger_recompute(self, client, auth_headers):
        r = client.patch(f"/locations/{LOC}", json={"name": "Harness-Testname"}, headers=auth_headers)
        assert r.status_code == 200, r.text
        assert r.json()["recompute_triggered"] is False

    def test_unknown_field_rejected(self, client, auth_headers):
        # Edge Case: kein einziges gültiges Feld → 400, kein stiller Erfolg.
        r = client.patch(f"/locations/{LOC}", json={"voellig_unbekannt": 1}, headers=auth_headers)
        assert r.status_code == 400

    def test_invalid_focal_length_rejected(self, client, auth_headers):
        # Edge Case: Brennweite außerhalb 8–1200 mm → 422 (BUG-22-Validierung).
        r = client.patch(f"/locations/{LOC}", json={"focal_length_suggestions": [5000]}, headers=auth_headers)
        assert r.status_code == 422
