"""TASK-67 (Etappe 3, übernommen aus TASK-69 AK3) — Bewertungsfunktion für Orte:
Anlegen, Abrufen, Löschen einer Bewertung.

API-Ebene (FastAPI-TestClient) als zuverlässige Ergänzung zum Playwright-UI-Fluss in
backend/tests/frontend/run_frontend_check.py::_check_rating_flow (der die Stern-
Klicks und Rating._set()/_clear() im echten Browser prüft). Diese Datei prüft
denselben Vertrag auf Endpunkt-Ebene, unabhängig von Timing/Rendering.

Selbst-anlegende Fixture (Pattern 12, siehe test_us120.py::test_location_id) statt
einer angenommenen, extern vorhandenen Location-ID.

Verifizierte Endpunkt-Signaturen (main.py, Stand 2026-07-11):
  GET    /locations/{loc_id}/ratings?device_id=...  -> {count, avg, mine}  (Aggregat, KEINE Liste!)
  POST   /locations/{loc_id}/ratings   {value, device_id}  -> 201, {ok, count, avg, mine}
  DELETE /locations/{loc_id}/ratings?device_id=...   -> 200, {ok, count, avg, mine}
  GET    /ratings  -> Liste ALLER Roh-Bewertungen (kein Auth, Frontend-Boot-Cache)
Beide POST/DELETE verlangen auth.require_auth (Depends) — jeder eingeloggte Token
(User oder Host) reicht, kein Host-only-Endpunkt (Unterschied zum Bild-Upload).
Nutzt die bestehende `auth_headers`-Fixture aus backend/conftest.py (User-Token)
statt einer eigenen, redundanten Login-Fixture.
"""
from __future__ import annotations

import uuid

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.fixture
def test_location_id(client):
    """Eigene, eindeutige Custom-Location nur für diese Testdatei (Pattern 12)."""
    import main
    from data.locations import PhotoLocation, LocationCategory

    loc_id = f"custom_test_task67_rating_{uuid.uuid4().hex[:8]}"
    new_loc = PhotoLocation(
        id=loc_id, name="TASK-67-Rating-Test-Location", description="Testort für test_task67_ratings_regression.py",
        category=LocationCategory.SKYLINE,
        observer_lat=52.5, observer_lon=13.4,
        subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
        subject_height_m=0.0, subject_width_m=0.0, distance_m=100,
    )
    main.LOCATIONS.append(new_loc)
    main._save_custom_location(new_loc)

    yield loc_id

    main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
    main._store.delete_custom(loc_id)
    try:
        main._store.delete_rating(loc_id, "test-task67-device")
    except Exception:
        pass


class TestRatingCrud:
    def test_no_rating_initially(self, client, test_location_id):
        r = client.get(f"/locations/{test_location_id}/ratings", params={"device_id": "test-task67-device"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["count"] == 0
        assert body["avg"] is None
        assert body["mine"] is None

    def test_create_rating(self, client, test_location_id, auth_headers):
        r = client.post(
            f"/locations/{test_location_id}/ratings",
            json={"value": 4, "device_id": "test-task67-device"},
            headers=auth_headers,
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["ok"] is True
        assert body["mine"] == 4
        assert body["count"] == 1

    def test_retrieve_created_rating(self, client, test_location_id, auth_headers):
        client.post(
            f"/locations/{test_location_id}/ratings",
            json={"value": 5, "device_id": "test-task67-device"},
            headers=auth_headers,
        )
        r = client.get(f"/locations/{test_location_id}/ratings", params={"device_id": "test-task67-device"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["mine"] == 5
        assert body["count"] == 1
        assert body["avg"] == 5.0

    def test_update_existing_rating_is_upsert(self, client, test_location_id, auth_headers):
        client.post(
            f"/locations/{test_location_id}/ratings",
            json={"value": 2, "device_id": "test-task67-device"},
            headers=auth_headers,
        )
        r = client.post(
            f"/locations/{test_location_id}/ratings",
            json={"value": 5, "device_id": "test-task67-device"},
            headers=auth_headers,
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["mine"] == 5
        assert body["count"] == 1  # Upsert, kein zweiter Datensatz

    def test_delete_rating(self, client, test_location_id, auth_headers):
        client.post(
            f"/locations/{test_location_id}/ratings",
            json={"value": 3, "device_id": "test-task67-device"},
            headers=auth_headers,
        )
        r = client.delete(
            f"/locations/{test_location_id}/ratings",
            params={"device_id": "test-task67-device"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["mine"] is None
        assert body["count"] == 0

        # Erneutes Abrufen bestätigt: Bewertung bleibt gelöscht.
        r2 = client.get(f"/locations/{test_location_id}/ratings", params={"device_id": "test-task67-device"})
        assert r2.json()["mine"] is None

    def test_create_without_token_rejected(self, client, test_location_id):
        r = client.post(
            f"/locations/{test_location_id}/ratings",
            json={"value": 4, "device_id": "test-task67-device"},
        )
        assert r.status_code == 401

    def test_delete_without_token_rejected(self, client, test_location_id):
        r = client.delete(
            f"/locations/{test_location_id}/ratings",
            params={"device_id": "test-task67-device"},
        )
        assert r.status_code == 401

    def test_out_of_range_value_rejected(self, client, test_location_id, auth_headers):
        r = client.post(
            f"/locations/{test_location_id}/ratings",
            json={"value": 6, "device_id": "test-task67-device"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_missing_device_id_rejected(self, client, test_location_id, auth_headers):
        r = client.post(
            f"/locations/{test_location_id}/ratings",
            json={"value": 4, "device_id": ""},
            headers=auth_headers,
        )
        assert r.status_code == 422
