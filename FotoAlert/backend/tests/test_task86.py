"""TASK-86 — Offene Endpunkte gegen Missbrauch härten (Last, Login-Bremse, CORS).

Ticket: BACKLOG.md ### TASK-86. Realer Scope (siehe Analyse im Ticket): zwei der
fünf ursprünglich benannten Teilprobleme (Zeitraum-Deckelung von /preview-alignment,
CORS-Origin-Allowlist) waren bereits vor diesem Ticket gelöst — hier nur noch als
Regression abgesichert (AK-8/AK-9). Neu: Häufigkeits-Bremse /preview-alignment
(AK-1), Kalender-Cache-Normalisierung + Höchstgröße (AK-2/AK-3), Login-Lockout
(AK-4/AK-5), Geräte-Token-Validierung + Häufigkeits-Bremse (AK-6/AK-7).

Zwei Schichten:
- Offline-Unit-Tests von backend/rate_limit.py (deterministisch, kein App-Startup
  nötig, kein Netzwerk).
- API-Tests gegen /login, /register-device, /preview-alignment, /health (TestClient,
  data_dev). Da main._preview_alignment_limiter / main._login_lockout /
  main._register_device_limiter Modul-weite Singletons sind, die über die gesamte
  Testsession (auch über andere Testdateien hinweg) bestehen bleiben, und der
  `client`-Fixture in conftest.py session-scoped ist (ohne X-Forwarded-For fällt
  request.client.host bei TestClient immer auf denselben Wert zurück): jeder
  Testfall, der eine Bremse tatsächlich auslösen will, nutzt eine eigene, im
  gesamten Testlauf einmalige X-Forwarded-For-Adresse, damit sich weder die
  Tests dieser Datei noch andere Testdateien gegenseitig über den geteilten
  Zähler-State beeinflussen. Für dieselbe Absicherung werden Schwellen-Tests
  zusätzlich mit einem frisch injizierten Limiter (kleines eigenes max_calls)
  statt des echten Produktions-Limiters (20/60s bzw. 10/60s) ausgeführt, damit
  der Test nicht 20+ echte Requests braucht, um die Schwelle zu erreichen.

Python-3.9-kompatibel (kein `X | None`).
"""
from __future__ import annotations

import time
import uuid

import pytest


# ---------------------------------------------------------------------------
# Offline: rate_limit-Modul direkt (kein App-Startup, kein Netzwerk)
# ---------------------------------------------------------------------------

@pytest.mark.offline
@pytest.mark.regression
class TestSlidingWindowRateLimiter:
    """AK-1 (Grundmechanismus, hier generisch statt gebunden an /preview-alignment,
    das Zusammenspiel mit dem echten Endpoint prüft TestPreviewAlignmentRateLimit)."""

    def test_allows_up_to_configured_max_then_blocks(self):
        import rate_limit
        limiter = rate_limit.SlidingWindowRateLimiter(max_calls=20, window_seconds=60)
        for _ in range(20):
            assert limiter.check("addr-a") is None
        retry_after = limiter.check("addr-a")
        assert retry_after is not None and retry_after > 0

    def test_different_keys_are_independent(self):
        import rate_limit
        limiter = rate_limit.SlidingWindowRateLimiter(max_calls=1, window_seconds=60)
        assert limiter.check("addr-a") is None
        # Andere Absenderadresse darf von der Bremse der ersten nicht betroffen sein.
        assert limiter.check("addr-b") is None

    def test_window_expiry_allows_again(self):
        import rate_limit
        limiter = rate_limit.SlidingWindowRateLimiter(max_calls=1, window_seconds=0.05)
        assert limiter.check("addr-c") is None
        assert limiter.check("addr-c") is not None
        time.sleep(0.12)
        assert limiter.check("addr-c") is None


@pytest.mark.offline
@pytest.mark.regression
class TestLoginLockout:
    """AK-4/AK-5: Login-Drosselung + Reset bei Erfolg, auf Modul-Ebene (deterministisch,
    ohne TestClient/HTTP)."""

    def test_ak4_locks_after_max_failures(self):
        import rate_limit
        lockout = rate_limit.LoginLockout(max_failures=5, window_seconds=15 * 60)
        key = "addr-login-a"
        assert lockout.seconds_until_unlocked(key) is None
        for _ in range(5):
            lockout.record_failure(key)
        retry_after = lockout.seconds_until_unlocked(key)
        assert retry_after is not None and retry_after > 0

    def test_ak5_success_resets_counter(self):
        import rate_limit
        lockout = rate_limit.LoginLockout(max_failures=5, window_seconds=15 * 60)
        key = "addr-login-b"
        for _ in range(5):
            lockout.record_failure(key)
        assert lockout.seconds_until_unlocked(key) is not None
        lockout.record_success(key)
        assert lockout.seconds_until_unlocked(key) is None

    def test_ak5_window_expiry_also_unlocks(self):
        import rate_limit
        lockout = rate_limit.LoginLockout(max_failures=1, window_seconds=0.05)
        key = "addr-login-c"
        lockout.record_failure(key)
        assert lockout.seconds_until_unlocked(key) is not None
        time.sleep(0.12)
        assert lockout.seconds_until_unlocked(key) is None


@pytest.mark.offline
@pytest.mark.regression
class TestDeviceTokenValidation:
    """AK-6: Format-Validierung (20–256 Zeichen, druckbares ASCII)."""

    def test_minimum_and_maximum_length_accepted(self):
        import rate_limit
        assert rate_limit.is_valid_device_token("a" * 20) is True
        assert rate_limit.is_valid_device_token("a" * 256) is True

    def test_too_short_rejected(self):
        import rate_limit
        assert rate_limit.is_valid_device_token("a" * 19) is False

    def test_too_long_rejected(self):
        import rate_limit
        assert rate_limit.is_valid_device_token("a" * 257) is False

    def test_empty_rejected(self):
        import rate_limit
        assert rate_limit.is_valid_device_token("") is False

    def test_non_printable_characters_rejected(self):
        import rate_limit
        assert rate_limit.is_valid_device_token(("a" * 24) + "\n") is False
        assert rate_limit.is_valid_device_token(("a" * 24) + " ") is False


@pytest.mark.offline
@pytest.mark.regression
class TestClientIdentity:
    """client_identity(): nutzt X-Forwarded-For (von Caddy gesetzt, siehe
    deploy/Caddyfile reverse_proxy), sonst Fallback auf request.client.host.

    Verwendet wird der LETZTE Eintrag des Headers, nicht der erste (Nachbesserung
    nach unabhaengigem Sicherheits-Befund, siehe TestClientIdentitySpoofingResistance
    unten fuer die Begruendung/den Missbrauchsfall)."""

    def test_prefers_x_forwarded_for_last_entry(self):
        import rate_limit
        from starlette.requests import Request

        scope = {
            "type": "http",
            "headers": [(b"x-forwarded-for", b"203.0.113.5, 10.0.0.1")],
            "client": ("127.0.0.1", 12345),
        }
        request = Request(scope)
        # Letzter Eintrag ("10.0.0.1") = der von Caddy selbst angehaengte Wert,
        # nicht der erste ("203.0.113.5"), der vom Client selbst gesetzt sein koennte.
        assert rate_limit.client_identity(request) == "10.0.0.1"

    def test_falls_back_to_client_host_without_header(self):
        import rate_limit
        from starlette.requests import Request

        scope = {"type": "http", "headers": [], "client": ("198.51.100.7", 12345)}
        request = Request(scope)
        assert rate_limit.client_identity(request) == "198.51.100.7"


@pytest.mark.offline
@pytest.mark.regression
class TestClientIdentitySpoofingResistance:
    """Nachbesserung eines unabhaengig bestaetigten Sicherheits-Befunds: In der
    Ein-Hop-Topologie (Caddy -> App nur ueber 127.0.0.1, siehe
    deploy/fotoalert.service) haengt Caddy die von ihm selbst beobachtete
    Verbindungs-IP stets als LETZTEN Eintrag an einen ggf. bereits vom Client
    mitgeschickten X-Forwarded-For-Header an. Wuerde client_identity() weiterhin
    den ERSTEN Eintrag lesen, koennte ein Angreifer bei jeder Anfrage einen
    beliebigen, frei erfundenen ersten Eintrag mitschicken und sich damit vor
    allen drei adressbasierten Bremsen (AK-1, AK-4, AK-7) als "immer neuer
    Absender" ausgeben. Diese Tests belegen, dass genau das jetzt nicht mehr
    moeglich ist."""

    def test_module_level_last_entry_used_not_first_spoofed_entry(self):
        """(a) Ein gespoofter erster Eintrag wird ignoriert - massgeblich ist der
        letzte, von Caddy angehaengte Eintrag."""
        import rate_limit
        from starlette.requests import Request

        scope = {
            "type": "http",
            "headers": [(b"x-forwarded-for", b"9.9.9.9, 203.0.113.5")],
            "client": ("127.0.0.1", 12345),
        }
        request = Request(scope)
        assert rate_limit.client_identity(request) == "203.0.113.5"

    def test_ak4_login_lockout_still_triggers_despite_changing_spoofed_first_entry(
        self, client
    ):
        """(b) Der eigentliche Beweis der Schliessung: zwei (bzw. mehrere) Anfragen
        mit demselben "echten" letzten Eintrag, aber jedes Mal einem ANDEREN,
        frei erfundenen ersten Eintrag, werden weiterhin als DIESELBE
        Absenderadresse behandelt - der Login-Lockout (AK-4) greift trotz
        wechselndem vorgetaeuschtem ersten Wert, ein Angreifer kann sich also
        nicht mehr durch staendig wechselnde vorgebliche Absenderadressen der
        Sperre entziehen."""
        real_last_hop = f"203.0.113.{uuid.uuid4().int % 200 + 1}"

        for i in range(5):
            spoofed_first_entry = f"9.9.9.{i}"
            headers = {
                "X-Forwarded-For": f"{spoofed_first_entry}, {real_last_hop}"
            }
            r = client.post(
                "/login", json={"password": "falsch"}, headers=headers
            )
            assert r.status_code == 401, r.text

        # Sechster Versuch, wieder mit einem NEUEN gespooften ersten Eintrag:
        # ohne den Fix waere das eine "neue" Absenderadresse und der Login-Lockout
        # wuerde die Sperre umgehen lassen. Mit dem Fix bleibt die Absenderadresse
        # (letzter Eintrag) unveraendert -> die Sperre greift trotzdem.
        headers_6 = {
            "X-Forwarded-For": f"9.9.9.99, {real_last_hop}"
        }
        r6 = client.post(
            "/login", json={"password": "falsch"}, headers=headers_6
        )
        assert r6.status_code == 429, r6.text
        assert "Retry-After" in r6.headers

        # Selbst mit korrektem Passwort und wieder einem neuen gespooften ersten
        # Eintrag bleibt die Sperre wirksam, solange der echte letzte Eintrag
        # gleich bleibt.
        headers_7 = {
            "X-Forwarded-For": f"9.9.9.100, {real_last_hop}"
        }
        r7 = client.post(
            "/login", json={"password": "test-host-pw"}, headers=headers_7
        )
        assert r7.status_code == 429, r7.text


# ---------------------------------------------------------------------------
# API: /preview-alignment (AK-1, AK-8 Regression)
# ---------------------------------------------------------------------------

_OBSERVER_LAT, _OBSERVER_LON = 52.3975, 13.0976
_SUBJECT_LAT, _SUBJECT_LON = 52.4158, 13.0688
_ELEVATION_DIFF_M = 50.0


def _preview_payload(**overrides):
    payload = {
        "observer_lat": _OBSERVER_LAT,
        "observer_lon": _OBSERVER_LON,
        "subject_lat": _SUBJECT_LAT,
        "subject_lon": _SUBJECT_LON,
        "subject_name": "Unbenannt",  # save=False -> wird nie gespeichert
        "subject_height_m": 15.0,
        "subject_width_m": 10.0,
        "days": 3,
        "save": False,
    }
    payload.update(overrides)
    return payload


def _login_as_host(client):
    r = client.post("/login", json={"password": "test-host-pw"})
    assert r.status_code == 200, r.text


@pytest.fixture
def _mock_elevation(monkeypatch):
    """Kein echter Netzwerkaufruf gegen opentopodata.org (Muster wie test_bug63.py)."""
    from data.elevation import provider

    async def _fake_elevation_difference(*args, **kwargs):
        return _ELEVATION_DIFF_M, False

    monkeypatch.setattr(provider, "elevation_difference", _fake_elevation_difference)


@pytest.mark.api
@pytest.mark.regression
class TestPreviewAlignmentRateLimit:
    def test_ak1_blocks_after_threshold_then_recovers_for_other_address(
        self, client, monkeypatch, _mock_elevation
    ):
        import rate_limit
        import main

        _login_as_host(client)
        # Eigener, kleiner Limiter statt der echten 20/60s-Schwelle injiziert, damit
        # der Test nicht 21 echte Berechnungen braucht, um die Bremse auszulösen.
        monkeypatch.setattr(
            main,
            "_preview_alignment_limiter",
            rate_limit.SlidingWindowRateLimiter(max_calls=1, window_seconds=60),
        )
        headers_a = {"X-Forwarded-For": f"198.51.100.{uuid.uuid4().int % 200 + 1}"}
        r1 = client.post("/preview-alignment", json=_preview_payload(), headers=headers_a)
        assert r1.status_code == 200, r1.text
        r2 = client.post("/preview-alignment", json=_preview_payload(), headers=headers_a)
        assert r2.status_code == 429, r2.text
        assert "Retry-After" in r2.headers
        assert "erneut versuchen" in r2.json()["detail"]

        # Andere Absenderadresse ist von der Bremse der ersten unberührt (normale
        # gelegentliche Nutzung anderer Nutzer bleibt funktionsfähig).
        headers_b = {"X-Forwarded-For": f"198.51.100.{uuid.uuid4().int % 200 + 101}"}
        r3 = client.post("/preview-alignment", json=_preview_payload(), headers=headers_b)
        assert r3.status_code == 200, r3.text


@pytest.mark.api
@pytest.mark.regression
class TestPreviewAlignmentDaysCapRegression:
    """AK-8: Zeitraum-Deckelung (`days = min(req.days, 14)`, BUG-63) bleibt durch
    dieses Ticket unverändert — ein Aufruf mit days=100 liefert exakt dasselbe
    Ergebnis wie einer mit days=14."""

    def test_ak8_days_over_14_is_still_capped(self, client, _mock_elevation):
        _login_as_host(client)
        headers = {"X-Forwarded-For": f"198.51.100.{uuid.uuid4().int % 200 + 1}"}
        r_14 = client.post(
            "/preview-alignment", json=_preview_payload(days=14), headers=headers
        )
        assert r_14.status_code == 200, r_14.text
        headers2 = {"X-Forwarded-For": f"198.51.100.{uuid.uuid4().int % 200 + 1}"}
        r_100 = client.post(
            "/preview-alignment", json=_preview_payload(days=100), headers=headers2
        )
        assert r_100.status_code == 200, r_100.text
        assert r_14.json() == r_100.json(), (
            "days=100 muss weiterhin auf 14 gedeckelt werden (BUG-63) — dieses Ticket "
            "aendert daran nichts (AK-8, Regression)."
        )


# ---------------------------------------------------------------------------
# API: /login (AK-4, AK-5)
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
class TestLoginEndpointLockout:
    def test_ak4_locked_out_after_five_failures_without_checking_password(self, client):
        headers = {"X-Forwarded-For": f"203.0.113.{uuid.uuid4().int % 200 + 1}"}
        for _ in range(5):
            r = client.post(
                "/login", json={"password": "falsch"}, headers=headers
            )
            assert r.status_code == 401, r.text
        r6 = client.post("/login", json={"password": "falsch"}, headers=headers)
        assert r6.status_code == 429, r6.text
        assert "Retry-After" in r6.headers
        # Auch ein KORREKTES Passwort wird jetzt abgewiesen, ohne geprüft zu werden.
        r7 = client.post(
            "/login", json={"password": "test-host-pw"}, headers=headers
        )
        assert r7.status_code == 429, r7.text

    def test_ak5_successful_login_resets_failure_counter(self, client):
        headers = {"X-Forwarded-For": f"203.0.113.{uuid.uuid4().int % 200 + 1}"}
        for _ in range(4):
            r = client.post("/login", json={"password": "falsch"}, headers=headers)
            assert r.status_code == 401, r.text
        r_ok = client.post(
            "/login", json={"password": "test-host-pw"}, headers=headers
        )
        assert r_ok.status_code == 200, r_ok.text
        # Zähler ist zurückgesetzt -> vier weitere Fehlversuche sperren noch nicht.
        for _ in range(4):
            r = client.post("/login", json={"password": "falsch"}, headers=headers)
            assert r.status_code == 401, r.text

    def test_ak5_correct_password_still_accepted_below_threshold(self, client):
        headers = {"X-Forwarded-For": f"203.0.113.{uuid.uuid4().int % 200 + 1}"}
        for _ in range(2):
            r = client.post("/login", json={"password": "falsch"}, headers=headers)
            assert r.status_code == 401, r.text
        r_ok = client.post(
            "/login", json={"password": "test-user-pw"}, headers=headers
        )
        assert r_ok.status_code == 200, r_ok.text
        assert r_ok.json()["role"] == "user"


# ---------------------------------------------------------------------------
# API: /register-device (AK-6, AK-7)
# ---------------------------------------------------------------------------

def _random_valid_token() -> str:
    # 32 Hex-Zeichen (druckbares ASCII, > 20 Zeichen), eindeutig pro Aufruf.
    return uuid.uuid4().hex + uuid.uuid4().hex


@pytest.mark.api
@pytest.mark.regression
class TestRegisterDeviceValidationAndRateLimit:
    def _cleanup_token(self, token: str) -> None:
        import main

        with main._store._connect() as conn:
            conn.execute("DELETE FROM device_tokens WHERE token = ?", (token,))

    def test_ak6_implausible_token_rejected_without_db_entry(self, client):
        import main

        before = main._store.device_token_count()
        r = client.post(
            "/register-device", params={"token": "zu-kurz", "platform": "ios"}
        )
        assert r.status_code == 422, r.text
        after = main._store.device_token_count()
        assert after == before, "Ungültiges Token darf KEINEN DB-Eintrag erzeugen (AK-6)."

    def test_ak6_too_long_token_rejected(self, client):
        r = client.post(
            "/register-device",
            params={"token": "a" * 5000, "platform": "ios"},
        )
        assert r.status_code == 422, r.text

    def test_ak6_valid_token_registers_normally(self, client):
        token = _random_valid_token()
        try:
            r = client.post(
                "/register-device", params={"token": token, "platform": "ios"}
            )
            assert r.status_code == 200, r.text
            assert r.json()["status"] == "registered"
        finally:
            self._cleanup_token(token)

    def test_ak7_rate_limit_blocks_further_registrations_same_address(
        self, client, monkeypatch
    ):
        import rate_limit
        import main

        monkeypatch.setattr(
            main,
            "_register_device_limiter",
            rate_limit.SlidingWindowRateLimiter(max_calls=1, window_seconds=60),
        )
        headers = {"X-Forwarded-For": f"192.0.2.{uuid.uuid4().int % 200 + 1}"}
        token1 = _random_valid_token()
        token2 = _random_valid_token()
        try:
            r1 = client.post(
                "/register-device",
                params={"token": token1, "platform": "ios"},
                headers=headers,
            )
            assert r1.status_code == 200, r1.text
            r2 = client.post(
                "/register-device",
                params={"token": token2, "platform": "ios"},
                headers=headers,
            )
            assert r2.status_code == 429, r2.text
            assert "Retry-After" in r2.headers
        finally:
            self._cleanup_token(token1)
            self._cleanup_token(token2)

    def test_ak7_single_normal_registration_unaffected(self, client):
        """Eine einzelne, normale Geräte-Registrierung (z.B. beim App-Start) bleibt
        von der Häufigkeits-Bremse unberührt (Edge Case aus AK-7)."""
        token = _random_valid_token()
        headers = {"X-Forwarded-For": f"192.0.2.{uuid.uuid4().int % 200 + 101}"}
        try:
            r = client.post(
                "/register-device",
                params={"token": token, "platform": "ios"},
                headers=headers,
            )
            assert r.status_code == 200, r.text
        finally:
            self._cleanup_token(token)


# ---------------------------------------------------------------------------
# Kalender-Cache-Normalisierung + Höchstgröße (AK-2, AK-3)
# ---------------------------------------------------------------------------

@pytest.mark.offline
@pytest.mark.regression
class TestCalendarCacheNormalizationAndSize:
    @pytest.fixture(autouse=True)
    def _mock_month_computation(self, monkeypatch):
        import main

        async def _fake_compute_location_month(loc, year, month, min_score):
            return [{"loc": loc.id, "min_score": min_score}]

        monkeypatch.setattr(main, "_compute_location_month", _fake_compute_location_month)
        main._ondemand_month_cache.clear()
        yield
        main._ondemand_month_cache.clear()

    def test_ak2_near_identical_min_score_shares_cache_entry(self):
        import asyncio
        import main

        events_a = asyncio.run(main._compute_month_all_locations(2031, 3, 0.40))
        assert len(main._ondemand_month_cache) == 1
        events_b = asyncio.run(main._compute_month_all_locations(2031, 3, 0.4000001))
        assert len(main._ondemand_month_cache) == 1, (
            "Score-Unterschied < 0.01 muss denselben Cache-Eintrag treffen (AK-2), "
            "der Zwischenspeicher darf dadurch nicht wachsen."
        )
        assert events_a == events_b

    def test_ak2_distinguishable_min_score_gets_own_entry(self):
        import asyncio
        import main

        asyncio.run(main._compute_month_all_locations(2031, 4, 0.10))
        assert len(main._ondemand_month_cache) == 1
        asyncio.run(main._compute_month_all_locations(2031, 4, 0.90))
        assert len(main._ondemand_month_cache) == 2, (
            "Deutlich unterschiedliche Score-Schwellen dürfen NICHT denselben "
            "Cache-Eintrag treffen."
        )

    def test_ak3_cache_evicts_oldest_entry_beyond_max_size(self):
        import asyncio
        import main

        max_size = main._ONDEMAND_MONTH_CACHE_MAX_SIZE
        first_key = "2020-01-0.01"
        asyncio.run(main._compute_month_all_locations(2020, 1, 0.01))
        assert first_key in main._ondemand_month_cache
        for i in range(max_size):
            asyncio.run(main._compute_month_all_locations(2020, 2, round(0.01 * (i + 1), 2)))
        assert len(main._ondemand_month_cache) == max_size, (
            "Der Zwischenspeicher darf die konfigurierte Höchstgröße nicht überschreiten."
        )
        assert first_key not in main._ondemand_month_cache, (
            "Der älteste Eintrag muss verdrängt worden sein (FIFO, AK-3)."
        )


# ---------------------------------------------------------------------------
# CORS-Regression (AK-9) — unverändert seit TASK-83, hier nur abgesichert
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
class TestCorsRegressionUnchanged:
    def test_ak9_known_origin_still_gets_credentialed_cors_headers(self, client):
        r = client.get("/health", headers={"Origin": "http://localhost:8000"})
        assert r.headers.get("access-control-allow-origin") == "http://localhost:8000"
        assert r.headers.get("access-control-allow-credentials", "").lower() == "true"

    def test_ak9_unknown_origin_still_gets_no_cors_headers(self, client):
        r = client.get("/health", headers={"Origin": "https://evil.example.com"})
        allow_origin = r.headers.get("access-control-allow-origin", "")
        assert allow_origin != "https://evil.example.com"
