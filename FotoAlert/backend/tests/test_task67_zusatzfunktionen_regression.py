"""TASK-67 (Etappe 3, übernommen aus TASK-69 AK8) — Basistests für die fünf bisher
ungetesteten Zusatzfunktionen: Tagesübersicht, Empfehlungsplan, Adress-Umkehrsuche,
Verarbeitungsstatus-Anzeigen.

Diese fünf Funktionen sind reine Backend-Endpunkte ohne UI-Zustandslogik (keine
Drei-Zustand-Chips, keine Sheets) — deshalb pytest über den FastAPI-TestClient statt
Playwright (Regel 1, TASK-67-Analyse: "unabhängig davon, ob die Prüfung technisch als
Backend-pytest oder als Playwright-Klick-Test läuft"). Jeder Test ist ein reiner
Struktur-/Statuscode-Basistest (AK8: "jeweils mindestens ein automatisierter
Basistest"), kein vollständiger Funktionstest.

Zuordnung Funktionsname -> Endpunkt (aus main.py verifiziert, Stand 2026-07-11):
  - Tagesübersicht         -> GET /opportunities/today (Chancen des heutigen Tages)
                              UND GET /daily-briefing (Tagesbriefing-Zusammenfassung) —
                              beide werden vom Frontend als "Tagesübersicht"-Funktion
                              genutzt, deshalb beide hier abgedeckt statt nur einer.
  - Empfehlungsplan        -> GET /plan (On-Demand-Alignment-Plan für beliebige
                              Koordinaten, TASK-25)
  - Adress-Umkehrsuche     -> GET /reverse-geocode (Nominatim-Reverse-Geocoding)
  - Verarbeitungsstatus-Anzeigen -> GET /job-status + GET /recompute-status

WICHTIG (Adress-Umkehrsuche): reverse_geocode_endpoint ruft einen externen Dienst
(Nominatim) auf; main._reverse_geocode() fängt jeden Fehler ab und liefert bei
Netzwerkproblemen "" zurück (kein Absturz, kein Non-200). Der Test prüft deshalb nur
die Antwortstruktur (Statuscode + Feld "place" vorhanden), NICHT den Inhalt — echte
Netzwerktests laufen laut Projektregel nicht aus der Subagenten-Sandbox, sondern
bestenfalls in CI/an Stephans Terminal mit echter Netzwerkverbindung.
"""
import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


class TestTagesuebersicht:
    """Tagesübersicht: /opportunities/today + /daily-briefing."""

    def test_opportunities_today_returns_list(self, client):
        r = client.get("/opportunities/today")
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) <= 20  # Endpoint deckelt auf Top 20 (main.py get_today_opportunities)

    def test_daily_briefing_returns_expected_shape(self, client):
        r = client.get("/daily-briefing")
        assert r.status_code == 200, r.text
        body = r.json()
        # DailyBriefingOut-Schema: response_model erzwingt bereits die Struktur;
        # Basis-Smoke-Check hier nur auf Statuscode + valides JSON-Objekt.
        assert isinstance(body, dict)

    def test_daily_briefing_accepts_explicit_date(self, client):
        r = client.get("/daily-briefing", params={"target_date": "2026-01-01"})
        assert r.status_code == 200, r.text


class TestEmpfehlungsplan:
    """Empfehlungsplan: /plan (On-Demand-Plan für beliebige Koordinaten, TASK-25)."""

    def test_plan_returns_events_for_berlin_coords(self, client):
        r = client.get(
            "/plan",
            params={
                "observer_lat": 52.5200, "observer_lon": 13.4050,
                "subject_lat": 52.5163, "subject_lon": 13.3777,
                "subject_name": "TASK-67-Test-Motiv",
                "days": 3,
                "min_score": 0.0,
            },
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("status") == "ok"
        assert body.get("on_demand") is True
        assert isinstance(body.get("events"), list)
        assert "elevation_incomplete" in body

    def test_plan_rejects_missing_required_coords(self, client):
        # observer_lat fehlt -> FastAPI-Validierung muss greifen (422), kein 500.
        r = client.get(
            "/plan",
            params={
                "observer_lon": 13.4050,
                "subject_lat": 52.5163, "subject_lon": 13.3777,
            },
        )
        assert r.status_code == 422


class TestAdressUmkehrsuche:
    """Adress-Umkehrsuche: /reverse-geocode (Nominatim, Netzwerkzugriff gekapselt)."""

    def test_reverse_geocode_returns_place_field(self, client):
        r = client.get("/reverse-geocode", params={"lat": 52.5200, "lon": 13.4050})
        assert r.status_code == 200, r.text
        body = r.json()
        assert "place" in body
        assert isinstance(body["place"], str)  # leerer String bei Netzwerkfehler ist gültig

    def test_reverse_geocode_requires_lat_lon(self, client):
        r = client.get("/reverse-geocode", params={"lat": 52.5200})
        assert r.status_code == 422


class TestVerarbeitungsstatusAnzeigen:
    """Verarbeitungsstatus-Anzeigen: /job-status + /recompute-status."""

    def test_job_status_shape(self, client):
        r = client.get("/job-status")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "jobs" in body
        assert "precompute_running" in body
        assert isinstance(body["precompute_running"], bool)

    def test_recompute_status_shape(self, client):
        r = client.get("/recompute-status")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "pending" in body
        assert isinstance(body["pending"], list)
        assert "running" in body
