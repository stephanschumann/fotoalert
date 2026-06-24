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


class TestTask24DeviceTokens:
    """TASK-24: Push-Token serverseitig persistieren.

    AK:
    - POST /register-device?token=abc → 200, status == "registered"
    - Zweiter POST gleicher Token → 200, status == "already_registered", kein Doppeleintrag
    - Persistenz: nach Registrierung neue LocationStore-Instanz auf selbe DB → Token vorhanden
    - POST ohne token → 422
    - POST mit leerem Token (token=) → 422
    - platform weggelassen → Default "ios" gespeichert
    """

    import uuid as _uuid
    TOKEN = f"tok-task24-{_uuid.uuid4().hex[:8]}"

    def test_register_new_token(self, client):
        """TASK-24 AK: neuer Token → 200, registered."""
        r = client.post(f"/register-device?token={self.TOKEN}&platform=ios")
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "registered"
        assert r.json()["device_count"] >= 1

    def test_idempotency(self, client):
        """TASK-24 AK: zweiter POST gleicher Token → already_registered, kein Doppel."""
        client.post(f"/register-device?token={self.TOKEN}&platform=ios")
        r = client.post(f"/register-device?token={self.TOKEN}&platform=ios")
        assert r.status_code == 200
        assert r.json()["status"] == "already_registered"

    def test_persistence_across_store_instances(self, client):
        """TASK-24 AK: Token ist nach Registrierung via main._store abrufbar (simuliert Neustart-Persistenz)."""
        import main
        tok = f"{self.TOKEN}-persist"
        client.post(f"/register-device?token={tok}&platform=ios")
        tokens = [t["token"] for t in main._store.load_device_tokens()]
        assert tok in tokens

    def test_default_platform_ios(self, client):
        """TASK-24 AK: platform weggelassen → Default ios gespeichert."""
        import main
        tok = f"{self.TOKEN}-noplatform"
        r = client.post(f"/register-device?token={tok}")
        assert r.status_code == 200
        match = next((t for t in main._store.load_device_tokens() if t["token"] == tok), None)
        assert match is not None
        assert match["platform"] == "ios"

    def test_missing_token_param_rejected(self, client):
        """TASK-24 AK: POST ohne token → 422."""
        r = client.post("/register-device")
        assert r.status_code == 422

    def test_empty_token_rejected(self, client):
        """TASK-24 AK: leerer Token → 422."""
        r = client.post("/register-device?token=")
        assert r.status_code == 422


class TestCameraProfile:
    """US-90: Kamera-Setup serverseitig persistieren.

    AK:
    - POST + GET Roundtrip (Upsert)
    - Zweiter POST gleicher device_id überschreibt (kein Doppeleintrag)
    - GET unbekannte device_id → 200 + {}
    - POST ohne device_id → 422
    - POST fl < 8 oder > 1200 → 422
    - POST sensor unbekannt → 422
    - POST ori unbekannt → 422
    - POST ohne Auth → 401
    - GET ohne Auth → 200 (öffentlich)
    """

    DEVICE = "cam-test-us90"

    def test_post_and_get_roundtrip(self, client, auth_headers):
        """US-90 AK: POST speichert, GET gibt zurück."""
        r = client.post("/camera-profile", headers=auth_headers,
                        json={"device_id": self.DEVICE, "sensor": "fullframe",
                              "fl": 85, "ori": "landscape"})
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["ok"] is True
        assert data["sensor"] == "fullframe"
        assert data["fl"] == 85

        r2 = client.get(f"/camera-profile?device_id={self.DEVICE}")
        assert r2.status_code == 200
        assert r2.json()["sensor"] == "fullframe"
        assert r2.json()["fl"] == 85

    def test_upsert_overwrites(self, client, auth_headers):
        """US-90 AK: zweiter POST gleicher device_id → überschreibt, kein Doppel."""
        client.post("/camera-profile", headers=auth_headers,
                    json={"device_id": self.DEVICE, "sensor": "fullframe", "fl": 85, "ori": "landscape"})
        r = client.post("/camera-profile", headers=auth_headers,
                        json={"device_id": self.DEVICE, "sensor": "mft", "fl": 135, "ori": "portrait"})
        assert r.status_code == 201
        assert r.json()["fl"] == 135
        assert r.json()["sensor"] == "mft"

        r2 = client.get(f"/camera-profile?device_id={self.DEVICE}")
        assert r2.json()["fl"] == 135
        assert r2.json()["sensor"] == "mft"

    def test_get_unknown_device_returns_empty(self, client):
        """US-90 AK: unbekannte device_id → 200 + {}."""
        r = client.get("/camera-profile?device_id=this-device-does-not-exist-us90")
        assert r.status_code == 200
        assert r.json() == {}

    def test_post_without_device_id_rejected(self, client, auth_headers):
        """US-90 AK: POST ohne device_id → 422."""
        r = client.post("/camera-profile", headers=auth_headers,
                        json={"sensor": "fullframe", "fl": 85, "ori": "landscape", "device_id": ""})
        assert r.status_code == 422

    def test_fl_too_small_rejected(self, client, auth_headers):
        """US-90 AK: fl < 8 → 422."""
        r = client.post("/camera-profile", headers=auth_headers,
                        json={"device_id": self.DEVICE, "sensor": "fullframe", "fl": 5, "ori": "landscape"})
        assert r.status_code == 422

    def test_fl_too_large_rejected(self, client, auth_headers):
        """US-90 AK: fl > 1200 → 422."""
        r = client.post("/camera-profile", headers=auth_headers,
                        json={"device_id": self.DEVICE, "sensor": "fullframe", "fl": 1500, "ori": "landscape"})
        assert r.status_code == 422

    def test_invalid_sensor_rejected(self, client, auth_headers):
        """US-90 AK: unbekannter sensor → 422."""
        r = client.post("/camera-profile", headers=auth_headers,
                        json={"device_id": self.DEVICE, "sensor": "bogus", "fl": 85, "ori": "landscape"})
        assert r.status_code == 422

    def test_invalid_ori_rejected(self, client, auth_headers):
        """US-90 AK: ori nicht landscape/portrait → 422."""
        r = client.post("/camera-profile", headers=auth_headers,
                        json={"device_id": self.DEVICE, "sensor": "fullframe", "fl": 85, "ori": "diagonal"})
        assert r.status_code == 422

    def test_post_requires_auth(self, client):
        """US-90 AK: POST ohne Auth → 401."""
        r = client.post("/camera-profile",
                        json={"device_id": self.DEVICE, "sensor": "fullframe", "fl": 85, "ori": "landscape"})
        assert r.status_code == 401

    def test_get_requires_no_auth(self, client):
        """US-90 AK: GET ohne Auth → 200 (öffentlich)."""
        r = client.get(f"/camera-profile?device_id={self.DEVICE}")
        assert r.status_code == 200
