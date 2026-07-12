"""TASK-67 Etappe 1 — PRODUCT.md "Pflicht-Regression Backend" automatisiert.

Deckt die 5 Punkte aus PRODUCT.md Abschnitt 11 ("Pflicht-Regression Backend") ab,
die bisher nur als manueller curl-Schnellcheck dokumentiert waren:
Health, Locations, Feed (opportunities), Kalender, Scout (discover).

Jeder Test bildet exakt die Prüfung aus dem curl-Einzeiler in PRODUCT.md nach
(gleicher Endpunkt, gleiche Grund-Assertion), aber über den bestehenden
FastAPI-TestClient (`client`-Fixture aus backend/conftest.py) statt über curl,
damit der Check im CI-Gate mitlaufen kann statt nur manuell an Stephans Terminal.

Kein Overlap mit bestehenden Dateien: test_api_smoke.py deckt nur /health ab,
test_api_regression.py deckt andere Endpunkte (PATCH-Recompute, Verifikationen,
Device-Tokens, Kamera-Profil) ab, keine der beiden prüft /opportunities, /calendar
oder /discover als Grundsatz-Schnellcheck.
"""
import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


class TestBackendQuickChecks:
    """PRODUCT.md Abschnitt 11, "Pflicht-Regression Backend" — 5 Punkte."""

    def test_health(self, client):
        """PRODUCT.md-Punkt 1: /health -> status == 'ok'."""
        r = client.get("/health")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "ok"
        assert "version" in body
        assert "locations_count" in body

    def test_locations(self, client):
        """PRODUCT.md-Punkt 2: /locations liefert mehr als 10 Einträge (Basis + Overrides + Custom)."""
        r = client.get("/locations")
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 10

    def test_feed_opportunities(self, client):
        """PRODUCT.md-Punkt 3: /opportunities antwortet mit einer (ggf. leeren) Liste, kein Fehler."""
        r = client.get("/opportunities", params={"min_score": 0.1, "days": 14})
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_calendar(self, client):
        """PRODUCT.md-Punkt 4: /calendar antwortet mit status != Fehler + 'events'-Liste.

        Struktur-Probe (Pattern reference_fotoalert_opportunities_structure):
        /calendar gibt ein dict zurück ({"status", "total", "events", ...}),
        keine flache Liste wie /opportunities.
        """
        r = client.get("/calendar")
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, dict)
        assert body.get("status") in ("ok", "no_cache", "calculating")
        assert isinstance(body.get("events"), list)

    def test_scout_discover(self, client):
        """PRODUCT.md-Punkt 5: /discover (Scout-Ephemeride) antwortet mit status != Fehler + 'opportunities'-Liste.

        Struktur-Probe: /discover gibt ebenfalls ein dict zurück
        ({"status", "opportunities", "total", ...}), keine flache Liste.
        """
        r = client.get("/discover")
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, dict)
        assert body.get("status") in ("ok", "calculating")
        assert isinstance(body.get("opportunities"), list)
