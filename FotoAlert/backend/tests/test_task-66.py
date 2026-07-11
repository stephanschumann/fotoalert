"""TASK-66 — pytest-Wrapper für die drei neuen Klick-Durchläufe im Playwright-Check.

Analog zum bestehenden Test-Harness-Muster (backend/tests/frontend/test_reporter.py):
`pytest.importorskip("playwright")` kapselt den Import, damit die Sandbox (ohne
installiertes Playwright) nicht rot wird. Zusätzlich wird hier — weil diese Tests
einen ECHTEN laufenden Dev-Server brauchen (Login, API-Schreiboperationen, Leaflet-
Rendering) — vor dem eigentlichen Lauf per /health geprüft, ob unter BASE_URL
überhaupt ein Server erreichbar ist; ist keiner erreichbar, wird das komplette Modul
übersprungen (kein Server-Start durch die Tests selbst, siehe run_frontend.sh für den
lokalen/CI-Start-Wrapper).

Deckt die drei neuen `_check_*`-Funktionen aus run_frontend_check.py End-to-End über
den vollständigen `run_checks()`-Lauf ab:
  - _check_location_create  (Regel 1 — Location anlegen + Kartenmarker)
  - _check_image_upload     (Regel 2 — Bild-Upload über LocationDetail, BUG-71)
  - _check_filter_feed      (Regel 3 — minScore-Extremfilter + Reset)

sowie den Fail-Fast-Edge-Case (Regel „Location-Anlage fehlgeschlagen → Bild-Upload
wird übersprungen, kein Folgefehler") isoliert per Direktaufruf mit einer präparierten
Fake-Page (kein Server/Browser nötig für diesen einen Fall).
"""
from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("playwright")

sys.path.insert(0, str(Path(__file__).resolve().parent / "frontend"))
import run_frontend_check as rfc  # noqa: E402
import spec as _spec  # noqa: E402

pytestmark = [pytest.mark.frontend, pytest.mark.regression]

BASE_URL = os.environ.get("FOTOALERT_TEST_BASE_URL", "http://localhost:8000")
USER_PASSWORD = os.environ.get("FOTOALERT_USER_PASSWORD", "test-user-pw")
HOST_PASSWORD = os.environ.get("FOTOALERT_HOST_PASSWORD", "test-host-pw")


def _server_reachable() -> bool:
    try:
        with urllib.request.urlopen(BASE_URL + "/health", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


if not _server_reachable():
    pytest.skip(
        "Kein laufender Dev-Server unter {0} erreichbar — TASK-66-E2E-Durchläufe "
        "brauchen einen echten Server (siehe backend/tests/run_frontend.sh). "
        "Übersprungen, nicht rot.".format(BASE_URL),
        allow_module_level=True,
    )


# --- Fixture-Datei existiert und ist ein valides Bild (AK Frage 2 → Option A) -------
def test_image_fixture_exists_and_is_valid_jpeg():
    fixture = Path(_spec.TEST_IMAGE_FIXTURE_PATH)
    assert fixture.is_file(), "Test-Fixture-Bild fehlt: " + str(fixture)
    with open(fixture, "rb") as f:
        header = f.read(3)
    # JPEG-Magic-Bytes: FF D8 FF
    assert header == b"\xff\xd8\xff", "Fixture-Datei ist kein valides JPEG"


# --- End-to-End: die drei neuen Durchläufe über den vollen run_checks()-Lauf --------
def test_task66_click_flows_end_to_end():
    """Führt den vollständigen Desktop-Pass aus und prüft, dass keine der drei neuen
    TASK-66-Prüfungen (Location anlegen / Bild-Upload / Filter) ein Finding erzeugt.

    Andere (bereits bestehende) Findings aus AK1–AK4 werden hier bewusst NICHT
    zusätzlich geprüft — das deckt test_reporter.py / der bestehende Smoke-Check
    bereits ab. Dieser Test ist gezielt auf die TASK-66-Assertion-IDs fokussiert.
    """
    findings = rfc.run_checks(
        base_url=BASE_URL,
        password=USER_PASSWORD,
        screenshot_root=Path(__file__).resolve().parents[2] / "docs" / "qa-screenshots",
        headless=True,
        host_password=HOST_PASSWORD,
    )

    task66_prefixes = (
        "location_create_map_baseline",
        "add_map_ready",
        "save_button_visible",
        "location_saved_marker",
        "location_in_get_locations",
        "location_marker_visible",
        "image_upload_skipped_no_location",
        "image_upload_host_login",
        "image_upload_detail_open",
        "image_upload_btn_present",
        "image_upload_file_chooser",
        "image_upload_img_visible",
        "image_url_set",
        "filter_feed_baseline",
        "filter_reduces_results",
        "filter_reset_restores_results",
    )
    task66_findings = [f for f in findings if f.assertion_id in task66_prefixes]
    assert not task66_findings, "TASK-66-Durchläufe meldeten Findings: {0}".format(
        [(f.assertion_id, f.actual) for f in task66_findings]
    )


# --- Fail-Fast-Edge-Case: Bild-Upload wird ohne Location-ID sauber übersprungen -----
def test_image_upload_skipped_without_location_id():
    """Regel „Location-Anlage fehlgeschlagen → Bild-Upload-Durchlauf wird mit einem
    eigenen Finding übersprungen statt Folgefehler-Kaskade" — isoliert geprüft, ohne
    Server/Browser: _check_image_upload(loc_id=None) darf nie versuchen, eine zweite
    Browser-Seite zu öffnen, sondern muss sofort mit genau einem Finding zurückkehren.
    """
    findings = rfc._check_image_upload(
        browser=None,  # darf bei loc_id=None gar nicht erst angefasst werden
        base_url=BASE_URL,
        host_password=HOST_PASSWORD,
        loc_id=None,
        commit="test-sha",
        shot_dir=Path("/tmp"),
        timeout_ms=1000,
    )
    assert len(findings) == 1
    assert findings[0].assertion_id == "image_upload_skipped_no_location"
