"""BUG-47 — Einstellungsseite zeigt falsche Rolle nach Host-Login.

Root Cause: Das Token kodiert die Rolle im Format "<rolle>.<hmac>".
Das Frontend liest die Rolle aus einem separaten localStorage-Key (fa_role).
Fehlt dieser Key (z.B. nach Safari ITP Storage-Bereinigung), zeigt die
Einstellungsseite "User" statt "Host" — obwohl das Token die korrekte Rolle enthält.

Diese Tests verifizieren die Backend-seitig testbaren Aspekte:
1. /login gibt für das Host-Passwort role="host" zurück.
2. Das Token-Format kodiert die Rolle als erstes Segment ("host.<hmac>").
3. Die Rolle aus dem Token-Prefix stimmt mit der zurückgegebenen Rolle überein.

Rein-frontendige Aspekte (localStorage-Ableitung, Settings-Rendering) sind
in manuellen Tests abgedeckt — siehe Testplan im Ticket.
"""
from __future__ import annotations

import pytest


VALID_ROLES = ("host", "user")


# ---------------------------------------------------------------------------
# Offline: auth-Modul direkt (kein App-Startup nötig)
# ---------------------------------------------------------------------------

@pytest.mark.offline
@pytest.mark.regression
class TestTokenRoleEncoding:
    """Das Token kodiert die Rolle als erstes Segment vor dem ersten Punkt."""

    def test_host_token_prefix_is_host(self):
        """issue_token('host') erzeugt ein Token das mit 'host.' beginnt."""
        import auth
        token = auth.issue_token("host")
        assert token.startswith("host."), (
            f"Token-Prefix sollte 'host' sein, ist aber: {token.split('.')[0]!r}"
        )

    def test_user_token_prefix_is_user(self):
        """issue_token('user') erzeugt ein Token das mit 'user.' beginnt."""
        import auth
        token = auth.issue_token("user")
        assert token.startswith("user."), (
            f"Token-Prefix sollte 'user' sein, ist aber: {token.split('.')[0]!r}"
        )

    def test_token_prefix_matches_role_for_token(self):
        """Prefix des Tokens stimmt mit role_for_token() überein."""
        import auth
        for role in VALID_ROLES:
            token = auth.issue_token(role)
            prefix = token.split(".")[0]
            decoded = auth.role_for_token(token)
            assert prefix == decoded == role, (
                f"Für Rolle {role!r}: Prefix={prefix!r}, decoded={decoded!r}"
            )

    def test_token_has_exactly_one_dot_separator(self):
        """Token hat mindestens einen Punkt (Format '<rolle>.<hmac>')."""
        import auth
        for role in VALID_ROLES:
            token = auth.issue_token(role)
            assert "." in token, f"Token für Rolle {role!r} enthält keinen Punkt: {token!r}"
            # Prefix muss eine gültige Rolle sein
            prefix = token.partition(".")[0]
            assert prefix in VALID_ROLES, (
                f"Token-Prefix {prefix!r} ist keine gültige Rolle"
            )

    def test_role_extraction_from_token_is_robust(self):
        """Rollenableitung aus Token: nur 'host' und 'user' sind gültige Prefixe."""
        import auth
        # Ungültige Tokens dürfen keine Rolle liefern
        assert auth.role_for_token("admin.abc") is None
        assert auth.role_for_token("") is None
        assert auth.role_for_token("host") is None  # kein Punkt
        assert auth.role_for_token(".abc") is None   # leerer Prefix


# ---------------------------------------------------------------------------
# API: /login gibt korrekte Rolle + Token zurück (BUG-47 Kernfall)
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
class TestLoginRoleResponse:
    """BUG-47: /login muss role='host' zurückgeben wenn das Host-Passwort korrekt ist."""

    def test_host_login_returns_role_host(self, client):
        """Host-Login: response enthält role='host'."""
        r = client.post("/login", json={"password": "test-host-pw"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["role"] == "host", (
            f"Erwartete role='host', bekam {data['role']!r}. "
            "Das ist der BUG-47-Kernfall: falsche Rolle nach Host-Login."
        )

    def test_host_login_token_encodes_host_role(self, client):
        """Host-Login: Token-Prefix ist 'host' — Frontend kann Rolle daraus ableiten."""
        r = client.post("/login", json={"password": "test-host-pw"})
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        prefix = token.partition(".")[0]
        assert prefix == "host", (
            f"Token-Prefix sollte 'host' sein, ist {prefix!r}. "
            "Frontend-Rollenableitung aus Token würde fehlschlagen."
        )

    def test_host_login_role_matches_token_prefix(self, client):
        """Host-Login: role im Response stimmt mit Token-Prefix überein (Konsistenz)."""
        r = client.post("/login", json={"password": "test-host-pw"})
        assert r.status_code == 200, r.text
        data = r.json()
        token_prefix = data["token"].partition(".")[0]
        assert data["role"] == token_prefix, (
            f"role={data['role']!r} stimmt nicht mit Token-Prefix {token_prefix!r} überein."
        )

    def test_user_login_returns_role_user(self, client):
        """User-Login: response enthält role='user' (Regression)."""
        r = client.post("/login", json={"password": "test-user-pw"})
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "user"

    def test_user_login_token_encodes_user_role(self, client):
        """User-Login: Token-Prefix ist 'user'."""
        r = client.post("/login", json={"password": "test-user-pw"})
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        prefix = token.partition(".")[0]
        assert prefix == "user", (
            f"Token-Prefix sollte 'user' sein, ist {prefix!r}."
        )
