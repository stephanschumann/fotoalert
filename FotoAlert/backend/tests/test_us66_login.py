"""US-66 — Pflicht-Login mit Rollen-Erkennung (Option B).

Zwei Schichten:
- Offline-Unit-Tests des auth-Moduls (kein App-Startup nötig).
- API-Tests gegen /login und die geschützten Endpoints (TestClient, data_dev).

Test-Credentials werden in conftest.py vor dem App-Import gesetzt:
  host=test-host-pw · user=test-user-pw · secret=test-secret
"""
import pytest

LOC = "custom_1781560330"


# --- Offline: auth-Modul direkt (deterministisch, kein App-Startup) ----------------
@pytest.mark.offline
@pytest.mark.regression
class TestAuthCore:
    def test_password_maps_to_role(self):
        import auth
        assert auth.role_for_password("test-host-pw") == "host"
        assert auth.role_for_password("test-user-pw") == "user"
        assert auth.role_for_password("falsch") is None
        assert auth.role_for_password("") is None

    def test_token_roundtrip(self):
        import auth
        assert auth.role_for_token(auth.issue_token("host")) == "host"
        assert auth.role_for_token(auth.issue_token("user")) == "user"

    def test_tampered_token_rejected(self):
        import auth
        tok = auth.issue_token("user")
        # Rolle hochstufen, Signatur behalten → muss ungültig sein.
        forged = "host." + tok.split(".", 1)[1]
        assert auth.role_for_token(forged) is None
        assert auth.role_for_token("garbage") is None
        assert auth.role_for_token("") is None


# --- API: /login + Endpoint-Schutz -------------------------------------------------
@pytest.mark.api
@pytest.mark.regression
class TestLoginEndpoint:
    def test_host_login(self, client):
        r = client.post("/login", json={"password": "test-host-pw"})
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "host"
        assert r.json()["token"]

    def test_user_login(self, client):
        r = client.post("/login", json={"password": "test-user-pw"})
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "user"

    def test_wrong_password(self, client):
        r = client.post("/login", json={"password": "falsch"})
        assert r.status_code == 401

    def test_empty_password(self, client):
        r = client.post("/login", json={"password": ""})
        assert r.status_code == 401


@pytest.mark.api
@pytest.mark.regression
class TestEndpointProtection:
    def test_protected_endpoint_without_token(self, client):
        # Schreibender Endpoint ohne Token → 401 (Pre-Mortem-Risiko 2 geschlossen).
        r = client.patch(f"/locations/{LOC}", json={"name": "X"})
        assert r.status_code == 401

    def test_protected_endpoint_with_user_token(self, client, auth_headers):
        r = client.patch(f"/locations/{LOC}", json={"name": "Auth-OK"}, headers=auth_headers)
        assert r.status_code == 200, r.text

    def test_host_only_endpoint_blocks_user(self, client, auth_headers):
        # require_host: User-Token auf Admin-Route → 403 (Body läuft nicht).
        r = client.post("/refresh-feed", headers=auth_headers)
        assert r.status_code == 403
