"""US-125 — Host kann ein hochgeladenes Beispielbild einer Location eigenständig löschen.

Deckt die automatisierbaren Akzeptanzkriterien aus BACKLOG.md ab:
  - Nach erfolgreichem Löschen ist die Bilddatei physisch nicht mehr vorhanden
    (nicht nur der Verweis in der Location entfernt) — AK 5.
  - Nur die Host-Rolle darf löschen; Nicht-Host → 403, kein Token → 401 — AK 6.
  - Löschen einer Location ohne aktuell vorhandenes Bild → verständlicher Fehler,
    kein Absturz — Edge Case AK 7.
  - Löschen bei einer nicht existierenden Location-ID → 404 — Edge Case AK 8.
  - Nach dem Löschen zeigt GET /locations für diese Location keine image_url mehr.

Nutzt dieselben Fixtures/Konventionen wie backend/tests/test_us120.py (eigene,
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


def _make_jpeg_bytes(width: int, height: int, color=(200, 60, 60)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@pytest.fixture
def host_headers(client):
    """TASK-83: /login setzt ein Cookie auf dem geteilten `client` statt einen
    Header-Token zurückzugeben — Folge-Requests auf demselben `client` sind dadurch
    automatisch authentifiziert. Der leere Header-Dict bleibt aus Kompatibilität zu
    bestehenden `headers=host_headers`-Aufrufen bestehen (kein-op, harmlos)."""
    r = client.post("/login", json={"password": "test-host-pw"})
    assert r.status_code == 200, r.text
    return {}


@pytest.fixture
def test_location_id(client):
    """Legt eine eigene, eindeutige Custom-Location für diesen Test an
    (gleiches Muster wie in test_us120.py::test_location_id)."""
    import main
    from data.locations import PhotoLocation, LocationCategory

    loc_id = f"custom_test_us125_{uuid.uuid4().hex[:8]}"
    new_loc = PhotoLocation(
        id=loc_id, name="US-125-Test-Location", description="Testort für test_us_125.py",
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


class TestDeleteImageSuccess:
    """AK 3/4/5: Erfolgreiches Löschen entfernt Verweis UND Datei, Location zeigt danach kein Bild mehr."""

    def test_delete_removes_image_url_and_file(self, client, host_headers, test_location_id):
        upload = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("beispiel.jpg", _make_jpeg_bytes(800, 600), "image/jpeg")},
            headers=host_headers,
        )
        assert upload.status_code == 200, f"Vorbereitender Upload fehlgeschlagen: {upload.text}"
        image_url = upload.json()["image_url"]

        # Datei ist vor dem Löschen abrufbar
        before = client.get(image_url)
        assert before.status_code == 200

        r = client.delete(f"/locations/{test_location_id}/image", headers=host_headers)
        assert r.status_code == 200, f"Löschen fehlgeschlagen: {r.text}"
        assert r.json()["ok"] is True

        # AK 3: Location zeigt danach keine image_url mehr
        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc is not None
        assert not loc.get("image_url"), "Nach dem Löschen darf keine image_url mehr gesetzt sein."

        # AK 5: Datei ist physisch wirklich weg, nicht nur der Verweis entfernt
        after = client.get(image_url)
        assert after.status_code == 404, (
            "Bilddatei ist über die alte Adresse noch abrufbar — physisches Löschen fehlt."
        )


class TestDeleteImageAuthOnlyHost:
    """AK 6: Nur ein Host darf löschen; normale Nutzer/nicht eingeloggte Clients nicht."""

    def test_delete_rejected_for_non_host(self, client, host_headers, test_location_id):
        upload = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("beispiel.jpg", _make_jpeg_bytes(800, 600), "image/jpeg")},
            headers=host_headers,
        )
        assert upload.status_code == 200, f"Vorbereitender Upload fehlgeschlagen: {upload.text}"

        # TASK-83: Cookie-Auth ist ambient auf `client` — der Host-Cookie aus dem
        # vorbereitenden Upload muss für den Nicht-Host-Check explizit auf 'user'
        # umgeschaltet werden (ein reiner Authorization-Header wie zuvor würde den
        # noch gültigen Host-Cookie nicht überstimmen).
        login = client.post("/login", json={"password": "test-user-pw"})
        assert login.status_code == 200, login.text
        r = client.delete(f"/locations/{test_location_id}/image")
        assert r.status_code == 403, f"Erwartet 403 für Nicht-Host, bekam {r.status_code}: {r.text}"

    def test_delete_rejected_without_token(self, client, host_headers, test_location_id):
        upload = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("beispiel.jpg", _make_jpeg_bytes(800, 600), "image/jpeg")},
            headers=host_headers,
        )
        assert upload.status_code == 200, f"Vorbereitender Upload fehlgeschlagen: {upload.text}"

        # TASK-83: Der Host-Cookie aus dem vorbereitenden Upload lebt sonst auf
        # `client` weiter — für den "ohne Auth"-Check muss er explizit entfernt werden.
        client.cookies.clear()
        r = client.delete(f"/locations/{test_location_id}/image")
        assert r.status_code == 401


class TestDeleteImageEdgeCases:
    """Edge-AKs 7/8: Löschen ohne vorhandenes Bild bzw. bei nicht existierender Location."""

    def test_delete_without_existing_image_returns_clear_error(self, client, host_headers, test_location_id):
        """AK 7: Location existiert, hat aber aktuell kein Beispielbild → verständlicher Fehler, kein 500."""
        r = client.delete(f"/locations/{test_location_id}/image", headers=host_headers)
        assert r.status_code in (400, 404), (
            f"Erwartet einen klaren Client-Fehler (400/404) statt Serverfehler, bekam {r.status_code}: {r.text}"
        )
        assert r.status_code < 500

    def test_delete_for_nonexistent_location_returns_404(self, client, host_headers):
        """AK 8: Location-ID existiert gar nicht → 404 'Location nicht gefunden'."""
        r = client.delete("/locations/custom_does_not_exist_us125/image", headers=host_headers)
        assert r.status_code == 404
