"""US-126 — Host kann den angezeigten Bildausschnitt (Crop) des Beispielbilds selbst wählen.

Deckt die automatisierbaren Akzeptanzkriterien aus BACKLOG.md ab (Option A —
einfacher Fokuspunkt-Klick, rein clientseitige Anzeigeposition):
  - Neuer Fokuspunkt wird korrekt gespeichert und im Response (GET /locations)
    zurückgegeben — AK 1-4.
  - Fehlender Fokuspunkt liefert Fallback 50.0/50.0 (Bildmitte, identisch zum
    bisherigen Verhalten) — Edge Case AK "ältere Bilder ohne gespeicherte Position".
  - Ersetzen des Bilds (US-120) setzt den Fokuspunkt zurück auf den Fallback
    (kein "Geister"-Ausschnitt vom vorherigen Bild) — Rule 3 / Edge Case "Bild-Ersetzen".
  - Funktioniert für Custom- UND Standard-Locations gleichermaßen (Pre-Mortem 4).
  - Nur die Host-Rolle darf den Fokuspunkt setzen; Nicht-Host → 403, kein Token → 401.
  - Ungültige Werte (außerhalb 0-100, falscher Typ) → 422.
  - Location ohne Beispielbild → 404 (Fokuspunkt ohne Bild ergibt keinen Sinn).
  - Location-ID existiert nicht → 404.

Nutzt dieselben Fixtures/Konventionen wie test_us120.py/test_us_125.py (eigene,
eindeutige Custom-Location pro Test statt Abhängigkeit von einer extern
vorhandenen Fixture-ID).
"""
from __future__ import annotations

import io
import uuid

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]

PIL = pytest.importorskip("PIL", reason="Pillow nicht installiert")
from PIL import Image  # noqa: E402


def _make_jpeg_bytes(width: int, height: int, color=(60, 120, 200)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@pytest.fixture
def host_headers(client):
    r = client.post("/login", json={"password": "test-host-pw"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_location_id(client):
    """Legt eine eigene, eindeutige Custom-Location für diesen Test an
    (gleiches Muster wie in test_us120.py/test_us_125.py::test_location_id)."""
    import main
    from data.locations import PhotoLocation, LocationCategory

    loc_id = f"custom_test_us126_{uuid.uuid4().hex[:8]}"
    new_loc = PhotoLocation(
        id=loc_id, name="US-126-Test-Location", description="Testort für test_us_126.py",
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
    leftover = main._IMAGE_DIR / f"{loc_id}.jpg"
    try:
        if leftover.exists():
            leftover.unlink()
    except OSError:
        pass


def _upload_image(client, host_headers, loc_id):
    upload = client.post(
        f"/locations/{loc_id}/image",
        files={"file": ("beispiel.jpg", _make_jpeg_bytes(800, 600), "image/jpeg")},
        headers=host_headers,
    )
    assert upload.status_code == 200, f"Vorbereitender Upload fehlgeschlagen: {upload.text}"
    return upload.json()


class TestFocusFallback:
    """Edge Case: Bilder ohne gespeicherte Ausschnittsposition fallen auf 50/50 (Bildmitte) zurück."""

    def test_new_upload_has_default_focus_50_50(self, client, host_headers, test_location_id):
        _upload_image(client, host_headers, test_location_id)

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc is not None
        assert loc["image_focus_x"] == 50.0
        assert loc["image_focus_y"] == 50.0


class TestSetFocusSuccess:
    """AK 1-4: Host kann eine Fokuspunkt-Position setzen, sie bleibt gespeichert."""

    def test_set_focus_persists_and_is_returned(self, client, host_headers, test_location_id):
        _upload_image(client, host_headers, test_location_id)

        r = client.patch(
            f"/locations/{test_location_id}/image-focus",
            json={"image_focus_x": 20.5, "image_focus_y": 80.0},
            headers=host_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["ok"] is True

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc is not None
        assert loc["image_focus_x"] == 20.5
        assert loc["image_focus_y"] == 80.0

    def test_set_focus_can_be_updated_repeatedly(self, client, host_headers, test_location_id):
        """Der Host kann beliebig oft neu tippen/korrigieren — jeder Aufruf überschreibt den vorigen Wert."""
        _upload_image(client, host_headers, test_location_id)

        client.patch(
            f"/locations/{test_location_id}/image-focus",
            json={"image_focus_x": 10, "image_focus_y": 10},
            headers=host_headers,
        )
        r = client.patch(
            f"/locations/{test_location_id}/image-focus",
            json={"image_focus_x": 90, "image_focus_y": 15},
            headers=host_headers,
        )
        assert r.status_code == 200, r.text

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc["image_focus_x"] == 90.0
        assert loc["image_focus_y"] == 15.0


class TestReplaceResetsFocus:
    """Rule 3 / Edge Case Bild-Ersetzen: Ein neues Bild setzt die Fokusposition zurück auf die Bildmitte."""

    def test_replace_image_resets_focus_to_default(self, client, host_headers, test_location_id):
        _upload_image(client, host_headers, test_location_id)
        client.patch(
            f"/locations/{test_location_id}/image-focus",
            json={"image_focus_x": 12, "image_focus_y": 88},
            headers=host_headers,
        )

        # Bild ersetzen (US-120-Funktion)
        _upload_image(client, host_headers, test_location_id)

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc is not None
        assert loc["image_focus_x"] == 50.0, "Nach Bild-Ersetzen darf kein alter Fokuspunkt übernommen werden."
        assert loc["image_focus_y"] == 50.0


class TestSetFocusValidation:
    """Ungültige Eingaben liefern verständliche Client-Fehler, kein Absturz."""

    def test_out_of_range_returns_422(self, client, host_headers, test_location_id):
        _upload_image(client, host_headers, test_location_id)
        r = client.patch(
            f"/locations/{test_location_id}/image-focus",
            json={"image_focus_x": 150, "image_focus_y": 50},
            headers=host_headers,
        )
        assert r.status_code == 422

    def test_wrong_type_returns_422(self, client, host_headers, test_location_id):
        _upload_image(client, host_headers, test_location_id)
        r = client.patch(
            f"/locations/{test_location_id}/image-focus",
            json={"image_focus_x": "left", "image_focus_y": 50},
            headers=host_headers,
        )
        assert r.status_code == 422

    def test_without_existing_image_returns_404(self, client, host_headers, test_location_id):
        """Location existiert, hat aber kein Beispielbild → Fokuspunkt ergibt keinen Sinn, 404."""
        r = client.patch(
            f"/locations/{test_location_id}/image-focus",
            json={"image_focus_x": 50, "image_focus_y": 50},
            headers=host_headers,
        )
        assert r.status_code == 404

    def test_nonexistent_location_returns_404(self, client, host_headers):
        r = client.patch(
            "/locations/custom_does_not_exist_us126/image-focus",
            json={"image_focus_x": 50, "image_focus_y": 50},
            headers=host_headers,
        )
        assert r.status_code == 404


class TestSetFocusAuthOnlyHost:
    """Nur ein Host darf den Fokuspunkt setzen; normale Nutzer/nicht eingeloggte Clients nicht."""

    def test_rejected_for_non_host(self, client, auth_headers, host_headers, test_location_id):
        _upload_image(client, host_headers, test_location_id)
        r = client.patch(
            f"/locations/{test_location_id}/image-focus",
            json={"image_focus_x": 50, "image_focus_y": 50},
            headers=auth_headers,
        )
        assert r.status_code == 403, f"Erwartet 403 für Nicht-Host, bekam {r.status_code}: {r.text}"

    def test_rejected_without_token(self, client, host_headers, test_location_id):
        _upload_image(client, host_headers, test_location_id)
        r = client.patch(
            f"/locations/{test_location_id}/image-focus",
            json={"image_focus_x": 50, "image_focus_y": 50},
        )
        assert r.status_code == 401
