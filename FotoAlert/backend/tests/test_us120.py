"""US-120 — Beispielbild pro Location hochladen (Host-Upload, Kompression, EXIF-Ausrichtung).

Deckt die automatisierbaren Akzeptanzkriterien aus BACKLOG.md ab:
  - Nur Host darf hochladen (Nicht-Host → 403).
  - Erfolgreicher Upload liefert danach einen Bildverweis in GET /locations.
  - Erneuter Upload ersetzt den vorherigen Verweis (kein zweites Bild).
  - Nach dem Ersetzen ist die alte Bilddatei physisch nicht mehr vorhanden (Pre-Mortem 2).
  - Upload über der harten Obergrenze wird abgelehnt (413), ohne Verarbeitung.
  - Ungültige Datei (kein echtes Bild trotz Endung) wird abgelehnt (400).
  - EXIF-Ausrichtungskorrektur: ein mit Orientation-Tag "gedrehtes" Bild kommt
    nach der Verarbeitung mit vertauschten Dimensionen heraus (Pixel tatsächlich gedreht).

Testbilder werden zur Laufzeit mit Pillow erzeugt (keine Bild-Fixtures im Repo nötig).
"""
from __future__ import annotations

import io
import uuid

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]

PIL = pytest.importorskip("PIL", reason="Pillow nicht installiert")
from PIL import Image  # noqa: E402


def _make_jpeg_bytes(width: int, height: int, color=(200, 60, 60)) -> bytes:
    """Erzeugt ein einfaches JPEG in Speicher (kein Orientation-Tag)."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _make_jpeg_with_orientation(width: int, height: int, orientation: int) -> bytes:
    """
    Erzeugt ein JPEG mit gesetztem EXIF-Orientation-Tag (Tag 0x0112).
    orientation=6 entspricht "im Uhrzeigersinn um 90° gedreht aufgenommen"
    (klassischer Hochformat-Handyfoto-Fall: Pixel liegen quer, Tag sagt "drehen").
    """
    img = Image.new("RGB", (width, height), (60, 120, 200))
    exif = img.getexif()
    exif[0x0112] = orientation  # Orientation-Tag
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90, exif=exif)
    return buf.getvalue()


@pytest.fixture
def host_headers(client):
    r = client.post("/login", json={"password": "test-host-pw"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_location_id(client):
    """Legt eine eigene, eindeutige Custom-Location für diesen Test an (statt sich auf
    eine extern in der Dev-DB vorhandene Fixture-ID zu verlassen — diese existierte
    nach einem DB-Reset nicht mehr, wodurch alle Upload-Tests mit 404 scheiterten).

    Nutzt denselben Weg wie main.py an anderer Stelle im Code für Custom Locations
    vorsieht (siehe main._save_custom_location + main.LOCATIONS.append in
    TestDeleteRemovesImageFile weiter unten in dieser Datei): ein PhotoLocation-Objekt
    wird in main.LOCATIONS (In-Memory-Liste, die der Upload-Endpoint für die
    404-Prüfung durchsucht) eingehängt und über main._save_custom_location in SQLite
    persistiert (main.py Zeile ~185: _store.create_custom(...)).

    Teardown: main._store.delete_custom(loc_id) existiert (data/store.py,
    LocationStore.delete_custom) und wird nach dem Test aufgerufen. Für
    location_overrides gibt es dagegen keine Remove/Delete-Funktion im Code
    (nur upsert_override) — hier nicht relevant, da diese Fixture ausschließlich
    eine Custom Location (custom_-Präfix) anlegt, keinen Override-Eintrag.
    """
    import main
    from data.locations import PhotoLocation, LocationCategory

    loc_id = f"custom_test_us120_{uuid.uuid4().hex[:8]}"
    new_loc = PhotoLocation(
        id=loc_id, name="US-120-Test-Location", description="Testort für test_us120.py",
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
    # Best-Effort: evtl. hochgeladene Bilddatei mit aufräumen (Sandbox-Mounts können
    # unlink() verweigern, dasselbe Best-Effort-Muster wie TestDeleteRemovesImageFile).
    leftover = main._IMAGE_DIR / f"{loc_id}.jpg"
    try:
        if leftover.exists():
            leftover.unlink()
    except OSError:
        pass


class TestUploadAuthOnlyHost:
    """AK: Nur ein Host darf hochladen/ersetzen; normale Nutzer sehen/dürfen das nicht."""

    def test_upload_rejected_for_non_host(self, client, auth_headers, test_location_id):
        """Edge-AK: Upload durch Nicht-Host (normaler User-Token) wird mit 403 abgelehnt."""
        img_bytes = _make_jpeg_bytes(800, 600)
        r = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        assert r.status_code == 403, f"Erwartet 403 für Nicht-Host, bekam {r.status_code}: {r.text}"

    def test_upload_rejected_without_token(self, client, test_location_id):
        """Ohne jedes Token: 401 (nicht eingeloggt)."""
        img_bytes = _make_jpeg_bytes(800, 600)
        r = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        )
        assert r.status_code == 401


class TestUploadSuccess:
    """AK: Erfolgreicher Host-Upload → Bild ist danach im Location-Datensatz sichtbar."""

    def test_upload_success_sets_image_url(self, client, host_headers, test_location_id):
        """Nach Upload liefert GET /locations für diese ID eine image_url."""
        img_bytes = _make_jpeg_bytes(1200, 900)
        r = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("beispiel.jpg", img_bytes, "image/jpeg")},
            headers=host_headers,
        )
        assert r.status_code == 200, f"Upload fehlgeschlagen: {r.text}"
        body = r.json()
        assert body["ok"] is True
        assert body["image_url"].startswith("/location-images/")

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc is not None
        assert loc["image_url"] == body["image_url"], (
            "GET /locations liefert nicht dieselbe image_url wie der Upload-Response."
        )

        # Datei muss tatsächlich abrufbar sein (StaticFiles-Mount)
        img_r = client.get(loc["image_url"])
        assert img_r.status_code == 200
        assert img_r.headers["content-type"].startswith("image/")

    def test_upload_compresses_large_image(self, client, host_headers, test_location_id):
        """AK: Großes Bild wird automatisch verkleinert (Ergebnis spürbar kleiner)."""
        # 3000x2000 RGB unkomprimiert wäre ~18 MB roh; als JPEG kleiner, aber immer noch groß.
        img_bytes = _make_jpeg_bytes(3000, 2000)
        r = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("big.jpg", img_bytes, "image/jpeg")},
            headers=host_headers,
        )
        assert r.status_code == 200, r.text
        result_size = r.json()["size_bytes"]
        assert result_size < len(img_bytes), (
            "Verarbeitetes Bild sollte kleiner sein als das (bereits JPEG-komprimierte) Original."
        )
        # Zielgröße ist ~500 KB; großzügige Toleranz nach oben für die Qualitäts-Untergrenze.
        assert result_size < 700 * 1024, f"Ergebnis {result_size} Bytes liegt deutlich über der Zielgröße."


class TestUploadReplace:
    """AK: Erneuter Upload ersetzt das bisherige Bild vollständig (Pre-Mortem 2)."""

    def test_second_upload_replaces_reference(self, client, host_headers, test_location_id):
        """Zweiter Upload überschreibt image_url (kein zweites Bild / keine Galerie)."""
        first = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("erst.jpg", _make_jpeg_bytes(800, 600, (10, 10, 10)), "image/jpeg")},
            headers=host_headers,
        )
        assert first.status_code == 200
        first_url = first.json()["image_url"]

        second = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("zweite.jpg", _make_jpeg_bytes(800, 600, (250, 250, 250)), "image/jpeg")},
            headers=host_headers,
        )
        assert second.status_code == 200
        second_url = second.json()["image_url"]

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc["image_url"] == second_url, "Nach zweitem Upload muss die neue URL aktiv sein."
        # Beim gewählten Dateinamensschema (Dateiname = Location-ID) ist die URL stabil;
        # entscheidend ist, dass der Inhalt tatsächlich ersetzt wurde:
        img_r = client.get(second_url)
        assert img_r.status_code == 200

    def test_old_file_deleted_on_replace(self, client, host_headers, test_location_id, tmp_path_factory):
        """Pre-Mortem 2: Nach dem Ersetzen ist die alte Bilddatei nicht mehr vorhanden.

        Da beide Uploads für dieselbe Location denselben Zieldateinamen (loc_id.jpg)
        verwenden, reicht "es liegt genau eine Datei vor" allein nicht als Beweis, dass
        wirklich ersetzt wurde: bei einer nicht existierenden Location (404, kein Upload
        passiert) wäre die Dateizahl 0, nicht 1 — die Assertion würde also auch in einem
        kaputten Zustand fehlschlagen (und schlug genau deshalb vorher fehl, als LOC auf
        eine nicht mehr existierende Dev-Seed-ID zeigte). Sie ist damit kein
        Falsch-Positiv-Fall, prüft aber den eigentlichen Kern (Inhalt wurde ersetzt)
        nicht direkt. Das holen wir hier explizit nach: erst altes Bild hochladen und
        dessen Inhalt merken, dann neues (unterscheidbares) Bild hochladen und
        sicherstellen, dass die verbleibende Datei den NEUEN Inhalt hat, nicht den alten.
        """
        import main

        old_bytes = _make_jpeg_bytes(640, 480, color=(10, 10, 10))
        first = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("a.jpg", old_bytes, "image/jpeg")},
            headers=host_headers,
        )
        assert first.status_code == 200, f"Erster Upload fehlgeschlagen: {first.text}"

        new_bytes = _make_jpeg_bytes(640, 480, color=(250, 250, 250))
        second = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("b.jpg", new_bytes, "image/jpeg")},
            headers=host_headers,
        )
        assert second.status_code == 200, f"Zweiter Upload fehlgeschlagen: {second.text}"
        second_url = second.json()["image_url"]

        matching = list(main._IMAGE_DIR.glob(f"{test_location_id}*"))
        tmp_files = [p for p in matching if p.suffix == ".tmp"]
        assert not tmp_files, f"Verwaiste .tmp-Dateien gefunden: {tmp_files}"
        assert len(matching) == 1, (
            f"Erwartet genau eine Bilddatei für {test_location_id}, gefunden: {matching}"
        )

        # Inhaltsprüfung: die verbliebene Datei muss den NEUEN Inhalt tragen, nicht den alten.
        remaining_bytes = matching[0].read_bytes()
        remaining_img = Image.open(io.BytesIO(remaining_bytes)).convert("RGB")
        sampled_pixel = remaining_img.getpixel((remaining_img.width // 2, remaining_img.height // 2))
        # Helles Ausgangsbild (250,250,250) bleibt nach JPEG-Kompression deutlich heller
        # als das dunkle Ausgangsbild (10,10,10) — grober, aber robuster Unterschied.
        assert sampled_pixel[0] > 150, (
            f"Verbleibende Datei scheint noch den ALTEN (dunklen) Bildinhalt zu haben: "
            f"Pixel {sampled_pixel} — erwartet hellen Pixel vom neuen Upload."
        )

        img_r = client.get(second_url)
        assert img_r.status_code == 200, "Neue Datei muss über die zurückgegebene URL abrufbar sein."


class TestUploadValidation:
    """Edge-AKs: Größenobergrenze und ungültige Dateien."""

    def test_upload_over_hard_limit_rejected(self, client, host_headers, test_location_id):
        """Edge-AK: Datei weit über der vertretbaren Obergrenze → klare Fehlermeldung, kein Hang."""
        import main

        oversized = b"\xff\xd8\xff" + b"0" * (main._IMAGE_HARD_LIMIT_BYTES + 1024)
        r = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("riesig.jpg", oversized, "image/jpeg")},
            headers=host_headers,
        )
        assert r.status_code == 413, f"Erwartet 413 bei Überschreitung, bekam {r.status_code}: {r.text}"

    def test_upload_invalid_file_rejected(self, client, host_headers, test_location_id):
        """Edge-AK: Datei mit .jpg-Endung, aber kein gültiger Bildinhalt → 400."""
        fake = b"%PDF-1.4 dies ist kein Bild, nur Text mit .jpg-Endung"
        r = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("fake.jpg", fake, "image/jpeg")},
            headers=host_headers,
        )
        assert r.status_code == 400, f"Erwartet 400 für ungültige Bilddatei, bekam {r.status_code}: {r.text}"

    def test_upload_unknown_location_rejected(self, client, host_headers):
        """Upload für nicht existierende Location-ID → 404."""
        r = client.post(
            "/locations/does_not_exist_12345/image",
            files={"file": ("x.jpg", _make_jpeg_bytes(400, 300), "image/jpeg")},
            headers=host_headers,
        )
        assert r.status_code == 404


class TestDeleteRemovesImageFile:
    """US-120-Nachtrag (2026-07-04): Löschen einer Location entfernt auch ihre Bilddatei."""

    def test_delete_custom_location_removes_image_file(self, client, host_headers):
        """Custom Location mit hochgeladenem Bild löschen → Bilddatei physisch weg, kein 500er."""
        import main
        from data.locations import PhotoLocation, LocationCategory

        loc_id = "custom_us120_delete_test"
        new_loc = PhotoLocation(
            id=loc_id, name="Löschtest-Location", description="Testort für US-120-Nachtrag",
            category=LocationCategory.SKYLINE,
            observer_lat=52.5, observer_lon=13.4,
            subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
            subject_height_m=0.0, subject_width_m=0.0, distance_m=100,
        )
        main.LOCATIONS.append(new_loc)
        main._save_custom_location(new_loc)

        try:
            # Beispielbild hochladen
            upload = client.post(
                f"/locations/{loc_id}/image",
                files={"file": ("test.jpg", _make_jpeg_bytes(640, 480), "image/jpeg")},
                headers=host_headers,
            )
            assert upload.status_code == 200, f"Upload fehlgeschlagen: {upload.text}"
            image_url = upload.json()["image_url"]
            image_filename = image_url.rsplit("/", 1)[-1]
            image_path = main._IMAGE_DIR / image_filename
            assert image_path.exists(), "Bilddatei sollte nach Upload existieren."

            # Location löschen
            del_r = client.delete(f"/locations/{loc_id}", headers=host_headers)
            assert del_r.status_code == 200, f"DELETE fehlgeschlagen: {del_r.text}"
            assert del_r.json()["deleted"] is True

            # Bilddatei muss danach weg sein (keine verwaiste Datei)
            assert not image_path.exists(), (
                "Bilddatei sollte nach dem Löschen der Location nicht mehr existieren."
            )

            # Location selbst ist wirklich weg
            locations = client.get("/locations").json()
            assert not any(l["id"] == loc_id for l in locations)
        finally:
            # Aufräumen, falls DELETE fehlschlägt und die Location/Datei stehen bleibt
            main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
            main._store.delete_custom(loc_id)
            leftover = main._IMAGE_DIR / f"{loc_id}.jpg"
            try:
                if leftover.exists():
                    leftover.unlink()
            except OSError:
                pass  # Sandbox-Mounts können unlink() verweigern; Cleanup ist Best-Effort

    def test_delete_location_without_image_still_works(self, client, host_headers):
        """Edge-AK: Löschen einer Location OHNE Bild funktioniert weiterhin fehlerfrei (kein 500er)."""
        import main
        from data.locations import PhotoLocation, LocationCategory

        loc_id = "custom_us120_delete_no_image_test"
        new_loc = PhotoLocation(
            id=loc_id, name="Löschtest ohne Bild", description="Testort ohne Beispielbild",
            category=LocationCategory.SKYLINE,
            observer_lat=52.5, observer_lon=13.4,
            subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
            subject_height_m=0.0, subject_width_m=0.0, distance_m=100,
        )
        main.LOCATIONS.append(new_loc)
        main._save_custom_location(new_loc)

        try:
            del_r = client.delete(f"/locations/{loc_id}", headers=host_headers)
            assert del_r.status_code == 200, f"DELETE fehlgeschlagen: {del_r.text}"
            assert del_r.json()["deleted"] is True
        finally:
            main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
            main._store.delete_custom(loc_id)


class TestExifOrientation:
    """Pre-Mortem 1 / AK: Verdreht aufgenommene Fotos erscheinen nach dem Upload richtig herum."""

    def test_exif_orientation_is_applied_to_pixels(self, client, host_headers, test_location_id):
        """
        Orientation=6 (90° im Uhrzeigersinn drehen) auf einem 1200x800-Bild (Querformat-
        Pixel) muss nach der Verarbeitung zu einem 800x1200-Ergebnis (Hochformat-Pixel)
        führen — die Drehung wurde also tatsächlich in die Pixel übernommen, nicht nur
        als Tag durchgereicht (das hätte width/height unverändert gelassen).
        """
        img_bytes = _make_jpeg_with_orientation(1200, 800, orientation=6)
        r = client.post(
            f"/locations/{test_location_id}/image",
            files={"file": ("gedreht.jpg", img_bytes, "image/jpeg")},
            headers=host_headers,
        )
        assert r.status_code == 200, r.text

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        img_r = client.get(loc["image_url"])
        result_img = Image.open(io.BytesIO(img_r.content))
        assert result_img.height > result_img.width, (
            f"Erwartet Hochformat nach EXIF-Rotation (Orientation=6), "
            f"bekam {result_img.width}x{result_img.height} — Ausrichtungskorrektur fehlt."
        )
