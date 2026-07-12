"""TASK-67 Etappe 1 — PRODUCT.md "Pflicht-Regression Auth" automatisiert.

Deckt die 5 Punkte aus PRODUCT.md Abschnitt 10 ("Pflicht-Regression Auth") ab.

Basis-Coverage für Login-Endpoint (Host/User-Passwort -> Rolle), Token-Rundlauf und
Endpunktschutz existiert bereits in test_us66_login.py — diese Datei baut das NICHT
doppelt, sondern konsolidiert/referenziert und ergänzt nur die noch fehlenden Punkte.

Wichtiger Hinweis zur Test-Tiefe: Die Rollen-Anzeige im Frontend (welche Tabs sichtbar
sind, ob "Host" oder "User" im Einstellungen-Tab steht) ist laut BUG-47 eine reine 1:1-
Ableitung aus dem Token-Präfix (`CFG.role`-Getter, kein Fallback auf einen separaten
State). Die Tests hier prüfen deshalb den serverseitigen Vertrag, auf dem diese
Ableitung beruht (Rollenvergabe durch /login, Token-Decodierung, Endpunktschutz) —
das ist mit reinem pytest/TestClient prüfbar. Die sichtbare DOM-Ebene (tatsächlich
gerenderter Tab, tatsächlich angezeigter Text "Host"/"User") ist nicht Teil dieser
Etappe (nur Backend+Auth, kein Playwright-Scope) und müsste bei Bedarf über eine
Erweiterung von backend/tests/frontend/run_frontend_check.py (TASK-66-Muster)
nachgezogen werden — das wäre eine bewusste Scope-Erweiterung, keine stille Lücke.
"""
import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]

LOC = "custom_1781560330"


@pytest.fixture(autouse=True)
def _seed_test_location(ensure_seed_location):
    """Stellt custom_1781560330 sicher (siehe test_api_regression.py, gleiches Muster)."""


# --- PRODUCT.md-Punkt 1: Nicht-eingeloggter Zugriff -> Login-Screen erscheint ------
# Serverseitiger Vertrag dahinter: ohne gültigen Token wird KEINE Rolle vergeben,
# und ein geschützter Endpunkt lehnt den Zugriff ab -> genau das ist die Bedingung,
# unter der das Frontend (Auth.isLoggedIn() === false) den Login-Screen zeigt.
class TestNoSessionMeansNoRole:
    def test_missing_token_yields_no_role(self):
        import auth
        assert auth.role_for_token("") is None

    def test_garbage_token_yields_no_role(self):
        import auth
        assert auth.role_for_token("not-a-real-token") is None

    # Der eigentliche "geschützter Endpoint ohne Token -> 401"-Beleg (identischer
    # PATCH-Call) deckt sowohl diesen Punkt als auch PRODUCT.md-Punkt 5 ab — siehe
    # TestProtectedEndpointRejectsMissingToken weiter unten, absichtlich nicht
    # dupliziert (Refactor-Check 2026-07-12, s. BACKLOG.md TASK-67).


# --- PRODUCT.md-Punkt 2 + 3: Host sieht alle Tabs / User sieht "User" -------------
# Der Rollen-Wert im Token ist die alleinige Quelle für die Frontend-Anzeige.
# Backend-Vertrag: /login liefert für das Host-Passwort role="host", für das
# User-Passwort role="user"; ein host-only-Endpunkt ist mit User-Token gesperrt,
# mit Host-Token erreichbar.
class TestRoleFromLogin:
    def test_host_login_yields_host_role(self, client):
        r = client.post("/login", json={"password": "test-host-pw"})
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "host"

    def test_user_login_yields_user_role(self, client):
        r = client.post("/login", json={"password": "test-user-pw"})
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "user"

    def test_host_only_route_reachable_with_host_token(self, client, host_token, monkeypatch):
        # CI-Fund (2026-07-12, Workflow-Lauf #198): /refresh-feed plant per
        # BackgroundTasks.add_task(_run_precompute, "feed") einen ECHTEN
        # precompute.py-Subprozess (kompletter 14-Tage-Feed, alle Locations).
        # Starlettes TestClient führt BackgroundTasks synchron VOR der Rückgabe
        # von client.post() aus — ohne Mock würde dieser Test also einen echten,
        # mehrminütigen Berechnungslauf anstoßen (in CI bis zum 15-Minuten-Timeout
        # der Backend-Test-Suite). Geprüft werden soll hier nur der Auth-Vertrag
        # ("mit Host-Token nicht gesperrt"), nicht die Berechnung selbst — die hat
        # test_us106.py bereits mit demselben Mock-Muster abgedeckt.
        import main
        async def _fake_run_precompute(mode: str = "full") -> None:
            return None
        monkeypatch.setattr(main, "_run_precompute", _fake_run_precompute)
        r = client.post("/refresh-feed", headers={"Authorization": f"Bearer {host_token}"})
        assert r.status_code != 403

    def test_host_only_route_blocked_for_user_token(self, client, auth_headers):
        r = client.post("/refresh-feed", headers=auth_headers)
        assert r.status_code == 403


# --- PRODUCT.md-Punkt 4: Rolle übersteht Reload -----------------------------------
# Ein App-Reload liest lediglich den bereits im localStorage persistierten Token
# erneut und decodiert ihn neu (kein neuer /login-Call). Vertrag: mehrfaches,
# unabhängiges Decodieren desselben Tokens liefert stabil dieselbe Rolle.
class TestRoleSurvivesReload:
    def test_token_decodes_stable_across_repeated_reads(self):
        import auth
        token = auth.issue_token("host")
        # Jeder Aufruf simuliert einen Reload, der den Token neu aus dem
        # localStorage liest und neu decodiert.
        assert auth.role_for_token(token) == "host"
        assert auth.role_for_token(token) == "host"
        assert auth.role_for_token(token) == "host"

    def test_user_token_decodes_stable_across_repeated_reads(self):
        import auth
        token = auth.issue_token("user")
        assert auth.role_for_token(token) == "user"
        assert auth.role_for_token(token) == "user"


# --- PRODUCT.md-Punkt 5: Geschützter Endpoint ohne Token -> 401 -------------------
class TestProtectedEndpointRejectsMissingToken:
    def test_patch_locations_without_token(self, client):
        r = client.patch(f"/locations/{LOC}", json={"name": "X"})
        assert r.status_code == 401
