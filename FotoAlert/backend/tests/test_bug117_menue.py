"""BUG-117 AK-6 (Oberfläche, 2026-10-18): Meldet der Server beim Wetter-Knopf „Wetterlauf läuft bereits.“
(status = already_running, Feld message), zeigt die Zeile im Aktualisieren-Menü genau diesen Satz statt
„Gestartet…“ und behält ihn auch nach dem ersten Abfragen des Job-Status, solange der Lauf läuft.

Nur im Browser prüfbar. Ohne Playwright, ohne FOTOALERT_E2E_URL oder ohne FOTOALERT_E2E_HOST_PW (Entwicklungsserver,
nie Produktion) werden die Tests ÜBERSPRUNGEN, nicht rot. Die Serverantworten für den Wetter-Knopf und den Job-Status
werden im Browser durch Attrappen ersetzt — es wird kein Wetterlauf ausgelöst und kein Wetterdienst angefragt.
Marker: frontend. Python-3.9-kompatibel. Neue Datei; bestehende Tests unverändert.
"""
from __future__ import annotations

import json
import os

import pytest

pytestmark = [pytest.mark.frontend, pytest.mark.regression]

URL = os.environ.get("FOTOALERT_E2E_URL", "").rstrip("/")
PW_HOST = os.environ.get("FOTOALERT_E2E_HOST_PW", "")


@pytest.fixture
def seite():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright ist nicht installiert (ausdrücklich benannte fehlende Voraussetzung)")
    if not URL or not PW_HOST:
        pytest.skip("FOTOALERT_E2E_URL / FOTOALERT_E2E_HOST_PW nicht gesetzt (kein Entwicklungsserver angegeben)")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 430, "height": 900}, service_workers="block")
        ctx.add_init_script("try{localStorage.setItem('fa_onboarding_seen','1')}catch(e){}")
        r = ctx.request.post(URL + "/login", data={"password": PW_HOST})
        assert r.ok, "Anmeldung als Host fehlgeschlagen: %s" % r.status
        yield ctx
        browser.close()


def _attrappen(page, job_status):
    def wetter(route):
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"status": "already_running", "message": "Wetterlauf läuft bereits."}))

    def status(route):
        antwort = route.fetch()
        daten = antwort.json()
        daten["jobs"]["weather"] = job_status
        route.fulfill(status=200, content_type="application/json", body=json.dumps(daten))
    page.route("**/weather-refresh", wetter)
    page.route("**/job-status", status)


def test_laeuft_bereits_hinweis_bleibt_waehrend_der_lauf_laeuft(seite):
    page = seite.new_page()
    _attrappen(page, {"status": "running", "last_run": None, "last_error": None, "duration_s": None})
    page.goto(URL)
    page.wait_for_function("typeof RefreshMenu !== 'undefined'")
    page.evaluate("RefreshMenu.trigger('weather')")
    zeile = page.locator("#rms-weather")
    page.wait_for_function("document.getElementById('rms-weather').textContent.includes('läuft bereits')", timeout=5000)
    assert "Gestartet" not in zeile.inner_text()
    page.wait_for_timeout(3800)           # nach dem ersten Abfragen des Job-Status (alle 3 Sekunden)
    assert "Wetterlauf läuft bereits." in zeile.inner_text(), "Hinweis wurde vom Abfragen überschrieben"
    assert "running" in page.locator("#rmi-weather").get_attribute("class")


def test_hinweis_verschwindet_wenn_der_lauf_beendet_ist(seite):
    page = seite.new_page()
    _attrappen(page, {"status": "done", "last_run": "2026-10-18T10:00:00+00:00", "last_error": None, "duration_s": 9})
    page.goto(URL)
    page.wait_for_function("typeof RefreshMenu !== 'undefined'")
    page.evaluate("RefreshMenu.trigger('weather')")
    page.wait_for_timeout(3800)
    assert "läuft bereits" not in page.locator("#rms-weather").inner_text()
    assert "running" not in page.locator("#rmi-weather").get_attribute("class")
