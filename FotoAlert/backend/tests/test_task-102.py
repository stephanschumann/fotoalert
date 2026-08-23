"""TASK-102 — Sicherheits-Härtungen Teil 1: interne Fehlermeldungen, Upload-Prüfreihenfolge.

Deckt die beiden automatisierbaren Teilaufgaben ab:

(a) GET /job-status ist unauthentifiziert erreichbar. `_job_error()` darf dort keinen
    rohen Python-Exception-Text (str(e)/str(exc)) mehr sichtbar machen — weder aus dem
    precompute-Subprozess-Fehlerpfad (_run_precompute) noch aus dem manuellen
    Sichtachsen-Refresh (_run_sightline_refresh). Der volle technische Text muss
    weiterhin per logger.error() im Server-Log landen (nicht ersatzlos verloren gehen).

(c) POST /locations/{id}/image (upload_location_image) darf die Upload-Größe nicht
    mehr erst NACH vollständigem Einlesen der Datei prüfen (await file.read() ohne
    Limit), sondern muss in Chunks lesen und spätestens einen Chunk über
    _IMAGE_HARD_LIMIT_BYTES abbrechen — ohne den Rest einer überdimensionierten Datei
    noch einzulesen. Bestehendes Verhalten für gültige Uploads bis zur Grenze bleibt
    unverändert (Regressionsgefahr: US-120/US-126 hängen an diesem Endpunkt, siehe
    test_us120.py/test_us_126.py — diese Datei dupliziert deren AKs bewusst NICHT,
    sondern deckt nur die TASK-102-spezifischen Aspekte ab).
"""
from __future__ import annotations

import asyncio
import io
import logging
import uuid

import pytest

import main

pytestmark = [pytest.mark.regression]


def _idle_job() -> dict:
    return {
        "status": "idle", "last_run": None, "last_error": None,
        "duration_s": None, "error_class": None, "spec": None,
    }


@pytest.fixture(autouse=True)
def _reset_job_status():
    """BUG-107-Nachtrag (CI-Fund, 2026-08-23): beide TestXxxErrorNoRawLeak-Faelle unten
    rufen main._run_precompute()/main._run_sightline_refresh() real auf und setzen dabei
    main._job_status["feed"]/["sightlines"] auf "error" — ohne Reset blieb das nach diesem
    Testmodul im geteilten Modul-Global main._job_status stehen. main.health() (US-38)
    meldete dadurch fuer ALLE spaeter in derselben Sitzung laufenden Tests (u.a. test_health
    in test_task67_backend_regression.py) faelschlich "degraded" statt "ok" — die Luecke
    existierte schon vor US-38, wurde aber erst durch dessen neue any_job_error-Pruefung
    in /health sichtbar. Muster identisch zu test_us38.py::_reset_job_state /
    test_bug107.py::_reset_job_status."""
    for key in ("feed", "sightlines"):
        main._job_status[key] = _idle_job()
    yield
    for key in ("feed", "sightlines"):
        main._job_status[key] = _idle_job()


# ---------------------------------------------------------------------------
# (a) Teil 1: precompute-Subprozess-Fehler (_run_precompute) — Job-Status ohne
#     rohen Exception-Text, voller Text weiterhin im Server-Log.
# ---------------------------------------------------------------------------

class TestPrecomputeSubprocessErrorNoRawLeak:
    """AK (a): _run_precompute() darf bei einem internen Fehler beim Starten des
    precompute.py-Subprozesses keinen rohen str(e) mehr in _job_status ablegen —
    dieser Wert wird per GET /job-status unauthentifiziert öffentlich ausgeliefert."""

    @pytest.mark.offline
    def test_generic_message_in_job_status_raw_text_in_log(self, monkeypatch, caplog):
        sentinel = f"SENTINEL_PRECOMPUTE_DETAIL_{uuid.uuid4().hex[:8]} /internal/pfad/geheim"

        async def _raise_subprocess_exec(*args, **kwargs):
            raise RuntimeError(sentinel)

        monkeypatch.setattr(main.asyncio, "create_subprocess_exec", _raise_subprocess_exec)
        monkeypatch.setattr(main, "_precompute_running", False)

        with caplog.at_level(logging.ERROR, logger="main"):
            asyncio.run(main._run_precompute(mode="feed"))

        status = main._job_status["feed"]
        assert status["status"] == "error"
        last_error = status["last_error"]
        assert last_error, "last_error sollte bei einem Fehler nicht leer sein."
        assert sentinel not in last_error, (
            f"Roher Exception-Text landete weiterhin im öffentlich per GET /job-status "
            f"abrufbaren last_error: {last_error!r}"
        )
        # Voller technischer Text darf nicht ersatzlos verloren gehen — muss im
        # Server-Log stehen (logger.error, siehe conftest/caplog).
        assert sentinel in caplog.text, (
            "Der volle Exception-Text wurde nicht per logger.error() geloggt — "
            "TASK-102 verlangt Protokollierung, nicht stilles Verschlucken."
        )


# ---------------------------------------------------------------------------
# (a) Teil 2: Sichtachsen-Refresh (_run_sightline_refresh) — Job-Status ohne
#     rohen Exception-Text, voller Text weiterhin im Server-Log.
# ---------------------------------------------------------------------------

class TestSightlineRefreshErrorNoRawLeak:
    """AK (a): _run_sightline_refresh() darf bei einem internen Fehler (hier:
    _load_qa_values()) keinen rohen str(exc) mehr in _job_status ablegen."""

    @pytest.mark.offline
    def test_generic_message_in_job_status_raw_text_in_log(self, monkeypatch, caplog):
        sentinel = f"SENTINEL_SIGHTLINE_DETAIL_{uuid.uuid4().hex[:8]} /internal/pfad/geheim"

        # Leere LOCATIONS-Liste: die innere Schleife (die pro Location externe
        # Overpass-/OpenTopoData-Aufrufe machen würde) darf hier nicht laufen —
        # der Fehler soll gezielt aus _load_qa_values() kommen, deterministisch
        # und ohne Netzwerk/Sleep-Verzögerung.
        monkeypatch.setattr(main, "LOCATIONS", [])

        def _raise_load_qa_values():
            raise RuntimeError(sentinel)

        monkeypatch.setattr(main, "_load_qa_values", _raise_load_qa_values)
        monkeypatch.setattr(main, "_sightline_refresh_running", False)

        with caplog.at_level(logging.ERROR, logger="main"):
            asyncio.run(main._run_sightline_refresh())

        status = main._job_status["sightlines"]
        assert status["status"] == "error"
        last_error = status["last_error"]
        assert last_error, "last_error sollte bei einem Fehler nicht leer sein."
        assert sentinel not in last_error, (
            f"Roher Exception-Text landete weiterhin im öffentlich per GET /job-status "
            f"abrufbaren last_error: {last_error!r}"
        )
        assert sentinel in caplog.text, (
            "Der volle Exception-Text wurde nicht per logger.error() geloggt — "
            "TASK-102 verlangt Protokollierung, nicht stilles Verschlucken."
        )


# ---------------------------------------------------------------------------
# (c) Upload-Größenprüfung: Streaming-Read mit frühem Abbruch statt erst
#     vollständigem Einlesen.
# ---------------------------------------------------------------------------

PIL = pytest.importorskip("PIL", reason="Pillow nicht installiert")
from PIL import Image  # noqa: E402


def _make_noise_jpeg_bytes(width: int, height: int, sigma: float = 60) -> bytes:
    """Rauschbild statt Fläche: JPEG-Kompression greift bei echtem Rauschen kaum,
    damit die erzeugte Datei zuverlässig > 1 MB bleibt (im Gegensatz zu einer
    einfarbigen Fläche, die JPEG fast beliebig klein komprimiert) — wird gebraucht,
    um den Mehr-Chunk-Pfad (> _IMAGE_UPLOAD_CHUNK_BYTES) mit einem tatsächlich
    gültigen, deutlich über 1 MB liegenden Bild zu testen."""
    img = Image.effect_noise((width, height), sigma).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@pytest.fixture
def host_headers(client):
    r = client.post("/login", json={"password": "test-host-pw"})
    assert r.status_code == 200, r.text
    return {}


@pytest.fixture
def upload_test_location_id(client):
    """Eigene, eindeutige Custom-Location für diese Datei (analog test_us120.py
    test_location_id-Fixture, absichtlich nicht importiert/geteilt, um diese Datei
    unabhängig von test_us120.py lauffähig zu halten)."""
    from data.locations import PhotoLocation, LocationCategory

    loc_id = f"custom_test_task102_{uuid.uuid4().hex[:8]}"
    new_loc = PhotoLocation(
        id=loc_id, name="TASK-102-Test-Location", description="Testort für test_task-102.py",
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


class TestUploadStreamingSizeCheck:
    """AK (c): Größe wird in Chunks geprüft, bevor die komplette Datei im Speicher
    liegt — kein unbegrenztes await file.read() mehr vor der Größenprüfung."""

    @pytest.mark.api
    def test_valid_upload_still_succeeds_unchanged(self, client, host_headers, upload_test_location_id):
        """Regression: ein normaler, gültiger Upload (mehrere Chunks, da > 1 MB
        Chunk-Größe) funktioniert nach der Umstellung unverändert."""
        img_bytes = _make_noise_jpeg_bytes(1600, 1200)
        assert len(img_bytes) > main._IMAGE_UPLOAD_CHUNK_BYTES, (
            "Testbild muss > 1 Chunk groß sein, sonst wird der Mehr-Chunk-Pfad nicht geprüft."
        )
        r = client.post(
            f"/locations/{upload_test_location_id}/image",
            files={"file": ("gross_aber_gueltig.jpg", img_bytes, "image/jpeg")},
            headers=host_headers,
        )
        assert r.status_code == 200, f"Gültiger Upload sollte weiterhin funktionieren: {r.text}"
        body = r.json()
        assert body["ok"] is True
        assert body["image_url"].startswith("/location-images/")

    @pytest.mark.api
    def test_oversized_upload_still_rejected_with_413(self, client, host_headers, upload_test_location_id):
        """Regression zu test_us120.py::test_upload_over_hard_limit_rejected: 413
        bleibt bestehen, jetzt über den Streaming-Pfad."""
        oversized = b"\xff\xd8\xff" + b"0" * (main._IMAGE_HARD_LIMIT_BYTES + 1024)
        r = client.post(
            f"/locations/{upload_test_location_id}/image",
            files={"file": ("riesig.jpg", oversized, "image/jpeg")},
            headers=host_headers,
        )
        assert r.status_code == 413, f"Erwartet 413, bekam {r.status_code}: {r.text}"

    @pytest.mark.api
    def test_oversized_upload_reads_in_bounded_chunks_not_whole_file(
        self, client, host_headers, upload_test_location_id, monkeypatch
    ):
        """Kern-AK (c): Der Endpunkt liest nachweislich in begrenzten Chunks
        (main._IMAGE_UPLOAD_CHUNK_BYTES) statt mit einem einzigen unbegrenzten
        await file.read() — und bricht ab, sobald die Summe das Limit übersteigt,
        ohne den Rest einer weit überdimensionierten Datei noch anzufordern.

        Spy auf UploadFile.read(): erfasst jede angeforderte Chunk-Größe. Ein
        unbegrenzter Aufruf (kein size-Argument / size=-1) darf nicht vorkommen,
        und die Gesamtzahl angeforderter Bytes muss deutlich unter der tatsächlichen
        (viel größeren) Dateigröße bleiben.

        Gepatcht wird sowohl `fastapi.UploadFile.read` als auch
        `starlette.datastructures.UploadFile.read`: welche der beiden Klassen zur
        Laufzeit tatsächlich instanziiert wird, hängt von der FastAPI-/Starlette-
        Version ab (verifiziert: in der hier installierten Version ist das zur
        Laufzeit tatsächlich verwendete Objekt eine `starlette.datastructures.
        UploadFile`-Instanz, nicht die `fastapi`-Unterklasse — ein Patch nur auf
        `fastapi.UploadFile` allein würde deshalb nie greifen).
        """
        import fastapi
        import starlette.datastructures as starlette_ds

        calls: list[int] = []
        orig_read_fastapi = fastapi.UploadFile.__dict__["read"]
        orig_read_starlette = starlette_ds.UploadFile.__dict__["read"]

        def _make_spy(orig):
            async def spy_read(self, size: int = -1):
                calls.append(size)
                return await orig(self, size)
            return spy_read

        monkeypatch.setattr(fastapi.UploadFile, "read", _make_spy(orig_read_fastapi))
        monkeypatch.setattr(starlette_ds.UploadFile, "read", _make_spy(orig_read_starlette))

        # Deutlich über dem Hard-Limit (Hard-Limit + 10 MB), damit ein Vollständig-
        # Einlesen-vor-Prüfung-Bug hier klar sichtbar würde (viel mehr angeforderte
        # Bytes als beim frühen Abbruch).
        oversized_extra = 10 * 1024 * 1024
        oversized = b"\xff\xd8\xff" + b"0" * (main._IMAGE_HARD_LIMIT_BYTES + oversized_extra)

        r = client.post(
            f"/locations/{upload_test_location_id}/image",
            files={"file": ("riesig_chunk_check.jpg", oversized, "image/jpeg")},
            headers=host_headers,
        )
        assert r.status_code == 413, f"Erwartet 413, bekam {r.status_code}: {r.text}"

        assert calls, "UploadFile.read() wurde nie aufgerufen — Endpunkt-Logik geändert?"
        assert -1 not in calls, (
            f"Mindestens ein unbegrenzter file.read()-Aufruf (size=-1) gefunden: {calls} — "
            "das würde die komplette Datei auf einen Schlag in den Speicher laden."
        )
        assert all(c == main._IMAGE_UPLOAD_CHUNK_BYTES for c in calls), (
            f"Erwartet ausschließlich Chunk-Größe {main._IMAGE_UPLOAD_CHUNK_BYTES}, "
            f"gefunden: {calls}"
        )

        total_requested = sum(calls)
        assert total_requested < len(oversized), (
            "Es wurden mindestens so viele Bytes angefordert wie die Gesamtdatei groß ist — "
            "kein Hinweis auf frühen Abbruch."
        )
        # Nach spätestens einem Chunk über dem Hard-Limit muss abgebrochen worden sein:
        # Gesamtanforderung darf nicht wesentlich über Hard-Limit + 1 Chunk liegen.
        assert total_requested <= main._IMAGE_HARD_LIMIT_BYTES + main._IMAGE_UPLOAD_CHUNK_BYTES, (
            f"Es wurden {total_requested} Bytes angefordert — deutlich mehr als Hard-Limit "
            f"({main._IMAGE_HARD_LIMIT_BYTES}) + ein Chunk ({main._IMAGE_UPLOAD_CHUNK_BYTES}). "
            "Kein früher Abbruch erkennbar."
        )
