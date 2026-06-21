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


class TestBug26Verifications:
    """BUG-26: Verifikationen server-seitig persistieren (nicht nur localStorage).

    AK: POST + GET Roundtrip, DELETE letzter Eintrag, kein Auth für GET,
        ungültiger status → 422.
    """

    LOC_V = "custom_verif_test"

    def test_post_and_get_roundtrip(self, client, auth_headers):
        """BUG-26 AK: POST speichert, GET gibt zurück (älteste zuerst)."""
        client.delete(f"/locations/{self.LOC_V}/verifications/last", headers=auth_headers)  # cleanup
        r = client.post(f"/locations/{self.LOC_V}/verifications", headers=auth_headers,
                        json={"location_name": "Test", "status": "ok",
                              "issue_type": "", "comment": "Super!", "date": "2026-06-21"})
        assert r.status_code == 201, r.text
        assert "id" in r.json()

        r2 = client.get(f"/locations/{self.LOC_V}/verifications")
        assert r2.status_code == 200
        entries = r2.json()
        assert any(e["status"] == "ok" and e["comment"] == "Super!" for e in entries)

    def test_get_all_bulk_endpoint(self, client, auth_headers):
        """BUG-26 AK: GET /verifications gibt alle zurück (Frontend-Preload)."""
        r = client.get("/verifications")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_requires_no_auth(self, client):
        """BUG-26 AK: GET /verifications ist öffentlich."""
        r = client.get("/verifications")
        assert r.status_code == 200

    def test_delete_last(self, client, auth_headers):
        """BUG-26 AK: DELETE /verifications/last entfernt neuesten Eintrag."""
        client.post(f"/locations/{self.LOC_V}/verifications", headers=auth_headers,
                    json={"location_name": "X", "status": "issue",
                          "issue_type": "Zugang gesperrt", "comment": "", "date": "2026-06-21"})
        before = client.get(f"/locations/{self.LOC_V}/verifications").json()
        r = client.delete(f"/locations/{self.LOC_V}/verifications/last", headers=auth_headers)
        assert r.status_code == 200
        after = client.get(f"/locations/{self.LOC_V}/verifications").json()
        assert len(after) == len(before) - 1

    def test_invalid_status_rejected(self, client, auth_headers):
        """BUG-26 Edge Case: ungültiger status → 422."""
        r = client.post(f"/locations/{self.LOC_V}/verifications", headers=auth_headers,
                        json={"status": "maybe", "date": "2026-06-21"})
        assert r.status_code == 422

    def test_missing_comment_accepted(self, client, auth_headers):
        """BUG-26 Edge Case: kein Kommentar → trotzdem gespeichert."""
        r = client.post(f"/locations/{self.LOC_V}/verifications", headers=auth_headers,
                        json={"status": "ok", "date": "2026-06-21"})
        assert r.status_code == 201
