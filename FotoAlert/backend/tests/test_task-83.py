"""TASK-83 — Login-Ticket vor Skript-Zugriff schützen (HttpOnly-Cookie statt Browser-Speicher).

Spec-Vertrag (siehe BACKLOG.md TASK-83, Analyse vom 2026-07-16):
- POST /login setzt ein Set-Cookie `fa_session` mit HttpOnly, SameSite=Lax, Path=/.
  Secure wird NUR in Produktion gesetzt (Nachtrag 2026-07-16, Safari-Fund: Safari
  akzeptiert Secure-Cookies ueber http://localhost nicht, Chrome macht dort still eine
  Ausnahme) — Tests laufen ueber FOTOALERT_ENV=dev (conftest.py) und erwarten daher KEIN
  Secure-Attribut. Die JSON-Response enthaelt NUR NOCH `role`, kein `token`-Feld mehr (das
  Ticket darf nie im JS-lesbaren Response-Body landen — genau das war die Luecke, die
  dieses Ticket schliesst).
- Geschuetzte Endpunkte (require_auth/require_host) lesen ausschliesslich das Cookie,
  KEIN Authorization-Header-Fallback (Weg-Gate-Teilentscheidung 3: iOS sendet ohnehin
  keinen Auth-Header, main.py:2610 — kein Fallback-Transport noetig).
- Ein alter Bearer-Token (Vor-Migration-Mechanismus) wird nach dem Umbau NICHT mehr
  akzeptiert -> Zwangs-Logout aller bestehenden Sessions (Weg-Gate-Teilentscheidung 1).
- POST /logout ist ein NEUER Endpoint, der das Cookie serverseitig verfallen laesst
  (Max-Age=0) — JS kann ein HttpOnly-Cookie nicht selbst loeschen; das bisherige
  Auth.logout() in web/index.html:1693 raeumt bislang nur localStorage auf.
- CORS: allow_origins wird eine explizite Liste (Prod-Domain + http://localhost:8000)
  statt Wildcard "*" — Wildcard + allow_credentials=True ist von der Fetch-Spec verboten
  und wuerde nach dem Umbau JEDEN Login serverseitig scheitern lassen (Pre-Mortem-Risiko 1
  im Ticket).

Diese Tests sind bewusst VOR der Implementierung geschrieben (Test-First-Prinzip) und
schlagen gegen den aktuellen IST-Zustand rot fehl: require_auth liest bisher nur den
Authorization-Header (backend/auth.py:67-73), main.py:98-103 setzt CORS auf
allow_origins=["*"] ohne allow_credentials, /logout existiert nicht. Das ist erwartet;
die Implementierungsphase macht sie gruen.

fa_api-Allow-Liste (Backend-Adresse im Settings-Sheet) ist eine rein frontend-seitige
Aenderung (web/index.html:7332-7334, kein serverseitiger Gegenpart) — analog zum bereits
etablierten Muster in test_bug47.py wird dieser Aspekt NICHT hier, sondern manuell im
Testplan des Tickets abgedeckt (siehe BACKLOG.md TASK-83 -> Testplan -> Manuell, Punkt 3).

Cookie-Isolation (Pre-Mortem-Risiko 5 im Ticket): backend/conftest.py's `client`-Fixture
ist session-scoped und teilt eine Cookie-Jar ueber ALLE Testdateien hinweg. Sobald /login
ein Cookie setzt, wuerde ein "ohne Cookie -> 401"-Test auf dem geteilten `client` nach
einem vorherigen Login in derselben Session faelschlich gruen laufen (das Cookie waere
noch da). Deshalb bauen alle "kein Auth" / "Cookie nach Login" Tests hier bewusst einen
EIGENEN, isolierten TestClient auf statt den geteilten `client`-Fixture zu verwenden — und
kontaminieren damit auch nicht die Cookie-Jar des geteilten Fixtures fuer andere Testdateien.
"""
from __future__ import annotations

import pytest

LOC = "custom_1781560330"
COOKIE_NAME = "fa_session"


def _fresh_client():
    """Eigener, isolierter TestClient — siehe Docstring oben (Cookie-Isolation).

    base_url=https zwingend: httpx' Cookie-Jar verwirft ein Secure-Cookie sonst beim
    naechsten Request, weil TestClient ohne explizites base_url "http://testserver"
    nutzt (kein Fehler im Server -- reine Testumgebungs-Emulation von "echtes https
    wie auf fotoalert.stephanschumann.com").
    """
    import main
    from fastapi.testclient import TestClient
    return TestClient(main.app, base_url="https://testserver")


# --- AK: Login setzt HttpOnly/Secure/SameSite=Lax-Cookie, kein Token im Body -------
@pytest.mark.api
@pytest.mark.regression
class TestLoginSetsHttpOnlyCookie:
    def test_login_sets_cookie_with_security_attributes(self, client):
        r = client.post("/login", json={"password": "test-host-pw"})
        assert r.status_code == 200, r.text
        set_cookie = r.headers.get("set-cookie", "")
        assert COOKIE_NAME in set_cookie, (
            f"Erwartet ein Set-Cookie fuer {COOKIE_NAME!r}, erhalten: {set_cookie!r}"
        )
        lowered = set_cookie.lower()
        assert "httponly" in lowered, f"Cookie fehlt HttpOnly: {set_cookie!r}"
        # TASK-83 Nachtrag (Safari-Fund 2026-07-16): Secure wird nur in Produktion gesetzt,
        # nicht im Dev-Modus (Safari akzeptiert Secure-Cookies über http://localhost nicht,
        # Chrome macht dort still eine Ausnahme). conftest.py setzt FOTOALERT_ENV=dev fuer
        # den gesamten Testlauf -> hier MUSS Secure fehlen, nicht "irgendein Wert ok".
        assert "secure" not in lowered, (
            f"Im Dev-Modus (FOTOALERT_ENV=dev) darf Secure NICHT gesetzt sein, sonst "
            f"funktioniert der Login lokal in Safari nicht: {set_cookie!r}"
        )
        assert "samesite=lax" in lowered, f"Cookie fehlt SameSite=Lax: {set_cookie!r}"

    @pytest.mark.smoke
    def test_login_response_body_has_no_token_field(self, client):
        r = client.post("/login", json={"password": "test-user-pw"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert "token" not in body, (
            "Das Sitzungs-Ticket darf nicht mehr im JS-lesbaren Antwort-Body stehen "
            f"(genau das war die BUG-Luecke) — Body war: {body!r}"
        )
        assert body.get("role") == "user"

    def test_wrong_password_sets_no_cookie(self, client):
        r = client.post("/login", json={"password": "falsch"})
        assert r.status_code == 401
        assert COOKIE_NAME not in r.headers.get("set-cookie", "")


# --- AK: geschuetzter Endpunkt ohne Cookie -> 401, mit Cookie -> 200 ----------------
@pytest.mark.api
@pytest.mark.regression
class TestCookieAuthProtectsEndpoints:
    @pytest.fixture(autouse=True)
    def _seed_test_location(self, ensure_seed_location):
        pass

    def test_request_without_cookie_is_rejected(self):
        with _fresh_client() as fresh:
            r = fresh.patch(f"/locations/{LOC}", json={"name": "X"})
            assert r.status_code == 401

    def test_request_with_cookie_after_login_succeeds_without_header(self):
        """Login + PATCH im selben (isolierten) Client teilen die Cookie-Jar automatisch —
        kein Authorization-Header noetig, das Cookie traegt die Sitzung."""
        with _fresh_client() as c:
            login = c.post("/login", json={"password": "test-user-pw"})
            assert login.status_code == 200, login.text
            r = c.patch(f"/locations/{LOC}", json={"name": "Cookie-Auth-OK"})
            assert r.status_code == 200, r.text

    def test_host_only_route_still_blocks_user_cookie(self):
        with _fresh_client() as c:
            login = c.post("/login", json={"password": "test-user-pw"})
            assert login.status_code == 200, login.text
            r = c.post("/refresh-feed")
            assert r.status_code == 403


# --- AK: Zwangs-Logout — alter Bearer-Header-Mechanismus wird nicht mehr akzeptiert --
@pytest.mark.api
@pytest.mark.regression
class TestOldBearerTokenRejectedAfterMigration:
    def test_old_style_authorization_header_alone_no_longer_authenticates(self, user_token):
        """user_token ist ein gueltig signiertes Token (altes Format) — nach dem Umbau
        gibt es dafuer keinen Header-Lesepfad mehr (Weg-Gate-Entscheidung 3: kein
        Fallback). Ohne begleitendes Cookie muss der Request weiterhin scheitern."""
        with _fresh_client() as fresh:
            r = fresh.patch(
                f"/locations/{LOC}",
                json={"name": "Sollte nicht durchgehen"},
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert r.status_code == 401, (
                "Ein reiner Authorization-Header darf nach dem Umbau NICHT mehr "
                "authentifizieren — das ist der Kern des Zwangs-Logouts."
            )


# --- AK: POST /logout laesst das Cookie serverseitig verfallen ---------------------
@pytest.mark.api
@pytest.mark.regression
class TestLogoutInvalidatesCookie:
    @pytest.fixture(autouse=True)
    def _seed_test_location(self, ensure_seed_location):
        pass

    def test_logout_expires_cookie_and_blocks_further_requests(self):
        with _fresh_client() as c:
            login = c.post("/login", json={"password": "test-user-pw"})
            assert login.status_code == 200, login.text

            logout = c.post("/logout")
            assert logout.status_code == 200, logout.text
            set_cookie = logout.headers.get("set-cookie", "")
            assert COOKIE_NAME in set_cookie
            assert "max-age=0" in set_cookie.lower() or "01 jan 1970" in set_cookie.lower(), (
                f"/logout muss das Cookie ablaufen lassen, Header war: {set_cookie!r}"
            )

            r = c.patch(f"/locations/{LOC}", json={"name": "Nach Logout"})
            assert r.status_code == 401


# --- AK: CORS erlaubt Credentials nur fuer explizite, bekannte Origins -------------
@pytest.mark.api
@pytest.mark.regression
class TestCorsAllowsCredentialsOnlyForKnownOrigins:
    """Wildcard (`allow_origins=["*"]`) + `allow_credentials=True` ist per Fetch-Spec
    verboten und fuehrt dazu, dass Browser JEDE Cookie-Antwort verwerfen (Pre-Mortem-
    Risiko 1 im Ticket). Die Umstellung auf eine explizite Origin-Liste ist daher fuer
    Cookie-Auth zwingend, nicht optional."""

    def test_known_origin_gets_credentialed_cors_headers(self, client):
        r = client.get("/health", headers={"Origin": "http://localhost:8000"})
        allow_origin = r.headers.get("access-control-allow-origin", "")
        allow_creds = r.headers.get("access-control-allow-credentials", "")
        assert allow_origin != "*", (
            "Wildcard-Origin mit Credentials ist von der Fetch-Spec verboten — "
            "der Browser wuerde die Cookie-Antwort verwerfen."
        )
        assert allow_origin == "http://localhost:8000"
        assert allow_creds.lower() == "true"

    def test_unknown_origin_gets_no_credentialed_cors_headers(self, client):
        r = client.get("/health", headers={"Origin": "https://evil.example.com"})
        allow_origin = r.headers.get("access-control-allow-origin", "")
        assert allow_origin != "https://evil.example.com", (
            "Eine fremde Origin darf keine Credential-CORS-Freigabe erhalten."
        )
