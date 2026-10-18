"""US-141 (Baustein 2) - Oberflächen-Tests im echten Browser (Playwright/Chromium), NEU, ergänzend zu test_us141_browser.py.

Geprüft werden die Teile, die nur in der fertigen Oberfläche sichtbar sind: Host-Menü „Länder & Regionen“
(Sammelschalter an/aus/teilweise, Ortszahlen), pausierte Orte in Liste und Karte, Zähler „davon n pausiert“,
Feed ohne Chancen pausierter Orte, „Alle Gebiete pausiert“, der nicht wegklickbare Hinweis bei neuen Orten
(Host) und die Meldung „Host muss freischalten“ (Nutzer), kein Host-Menü für Nutzer.

Voraussetzung wie bei test_us141_browser.py (sonst Überspringen mit Begründung): Playwright mit Chromium,
FOTOALERT_E2E_URL (Entwicklungsserver!), FOTOALERT_E2E_HOST_PW, FOTOALERT_E2E_USER_PW. Optional
FOTOALERT_E2E_SHOTS = Ordner für Bildschirmfotos. Die Tests schalten Gebiete um und legen Orte an - nur gegen eine
Entwicklungsinstanz mit Wegwerf-Daten laufen lassen, nie gegen Produktion. Python-3.9-kompatibel.
"""
from __future__ import annotations

import os

import pytest

pytestmark = [pytest.mark.frontend]

URL = os.environ.get("FOTOALERT_E2E_URL", "").rstrip("/")
PW_HOST = os.environ.get("FOTOALERT_E2E_HOST_PW", "")
PW_USER = os.environ.get("FOTOALERT_E2E_USER_PW", "")
SHOTS = os.environ.get("FOTOALERT_E2E_SHOTS", "")


def _pw():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright ist nicht installiert (ausdrücklich benannte fehlende Voraussetzung)")
    if not URL:
        pytest.skip("FOTOALERT_E2E_URL nicht gesetzt (kein Entwicklungsserver angegeben)")
    if not PW_HOST or not PW_USER:
        pytest.skip("Passwörter FOTOALERT_E2E_HOST_PW / FOTOALERT_E2E_USER_PW nicht gesetzt")
    return sync_playwright


@pytest.fixture
def browser():
    sp = _pw()
    with sp() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _kontext(browser, pw):
    ctx = browser.new_context(viewport={"width": 430, "height": 900})
    ctx.add_init_script("try{localStorage.setItem('fa_onboarding_seen','1')}catch(e){}")  # Einführung überspringen
    r = ctx.request.post(URL + "/login", data={"password": pw})
    assert r.ok, "Anmeldung fehlgeschlagen: %s" % r.status
    return ctx


def _foto(page, name):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        page.screenshot(path=os.path.join(SHOTS, name + ".png"))


def _alle_an(ctx):
    for land in ctx.request.get(URL + "/areas").json()["laender"]:
        r = ctx.request.put(URL + "/areas/" + land["name"].replace(" ", "%20"), data={"enabled": True})
        assert r.ok, r.text()


def _schalte(ctx, land, region, an):
    pfad = "/areas/%s" % land + ("/%s" % region if region else "")
    r = ctx.request.put(URL + pfad.replace(" ", "%20"), data={"enabled": an})
    assert r.ok, r.text()


def _orte(ctx):
    return ctx.request.get(URL + "/locations").json()


def _lege_ort_an(ctx, lat, lon, name):
    r = ctx.request.post(URL + "/preview-alignment", data={
        "observer_lat": lat, "observer_lon": lon, "subject_lat": lat + 0.004, "subject_lon": lon + 0.004,
        "subject_name": name, "subject_height_m": 50.0, "subject_width_m": 20.0, "days": 1, "save": True,
        "category": "SKYLINE"})
    assert r.ok, r.text()
    return r.json()["location_id"]


def _loesche(ctx, ort_id):
    ctx.request.delete(URL + "/locations/" + ort_id)


def _menue_offen(page):
    page.locator("#tab-settings").click()
    page.get_by_text("Länder & Regionen").first.click()
    page.locator("#gb-regions.open").wait_for(timeout=10000)
    page.locator(".gb-land").first.wait_for(timeout=10000)


def test_menue_schalter_und_folgen(browser):
    ctx = _kontext(browser, PW_HOST)
    _alle_an(ctx)
    vorher = _orte(ctx)
    n_de = len([o for o in vorher if o["land"] == "Deutschland"])
    assert n_de > 0, "Testdaten ohne Orte in Deutschland"
    page = ctx.new_page()
    page.goto(URL)
    page.locator("#tab-settings").wait_for(timeout=15000)
    _menue_offen(page)
    namen = page.locator(".gb-land .gb-rname").all_inner_texts()
    assert namen[-1] == "Sonstige", namen
    assert namen[:-1] == sorted(namen[:-1], key=lambda s: s.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u")), namen
    _foto(page, "01_menue_alle_an")
    de = page.locator('.gb-land[data-gb-landbox="Deutschland"]')
    sw = de.locator("[data-gb-lsw]")
    assert sw.get_attribute("aria-checked") == "true"
    # Deutschland aufklappen und eine Region ausschalten -> Land steht auf „teilweise“
    de.locator("[data-gb-exp]").click()
    de.locator('[data-gb-reg="Brandenburg"]').click()
    page.wait_for_function("document.querySelector('[data-gb-lsw=\"Deutschland\"]').getAttribute('aria-checked')==='mixed'", timeout=10000)
    assert "teilweise" in de.inner_text()
    _foto(page, "02_menue_teilweise")
    brandenburg = [o for o in _orte(ctx) if o["region"] == "Brandenburg"]
    assert brandenburg and all(o["paused"] for o in brandenburg)
    # Land ausschalten (Sammelschalter) -> aus; Feed hat keine deutschen Chancen mehr
    de.locator("[data-gb-lsw]").click()
    # bei „teilweise“ fragt die App nach
    page.get_by_role("button", name="Alle ausschalten").click()
    page.wait_for_function("document.querySelector('[data-gb-lsw=\"Deutschland\"]').getAttribute('aria-checked')==='false'", timeout=10000)
    _foto(page, "03_menue_land_aus")
    ids_de = {o["id"] for o in _orte(ctx) if o["land"] == "Deutschland"}
    feed = ctx.request.get(URL + "/opportunities?min_score=0.0&days=14").json()
    assert not [e for e in feed if e["location_id"] in ids_de], "Feed liefert noch Chancen pausierter Orte"
    # Zurück zur App: Orte-Liste zeigt Pausenzeichen und Zähler
    page.locator(".gb-head .gb-icon").click()
    page.locator("#tab-locations").click()
    page.locator("#loc-counter").wait_for(timeout=10000)
    zaehler = page.locator("#loc-counter").inner_text()
    assert "davon" in zaehler and "pausiert" in zaehler, zaehler
    assert page.locator("#locations-content .gb-tag-paused").count() >= 1
    _foto(page, "04_liste_pausiert")
    # Karte: pausierte Orte bleiben sichtbar (gedämpft)
    page.locator("#tab-map").click()
    page.locator(".leaflet-marker-icon").first.wait_for(timeout=15000)
    assert page.locator(".marker-paused").count() >= 1, "pausierte Orte fehlen auf der Karte"
    _foto(page, "05_karte")
    _alle_an(ctx)
    ctx.close()


def test_filterzaehler_und_karte_ohne_verschwinden(browser):
    ctx = _kontext(browser, PW_HOST)
    _alle_an(ctx)
    _schalte(ctx, "Italien", None, False)
    page = ctx.new_page()
    page.goto(URL)
    page.locator("#tab-map").click()
    page.locator(".leaflet-marker-icon").first.wait_for(timeout=15000)
    page.wait_for_timeout(1500)
    vorher = page.locator(".leaflet-marker-icon").count()
    pausiert = page.locator(".marker-paused").count()
    assert pausiert >= 1
    page.locator("#filter-btn").click()
    page.get_by_text("Goldene Stunde", exact=False).first.click()   # nur Art
    page.wait_for_timeout(500)
    assert page.locator(".marker-paused").count() == pausiert, "pausierte Orte bei „nur Art“ verschwunden"
    zaehler = page.locator("#filter-result-count").inner_text()
    assert "pausiert" in zaehler, zaehler
    _foto(page, "06_filter_karte_nur")
    page.get_by_text("Goldene Stunde", exact=False).first.click()   # ausschließen
    page.wait_for_timeout(500)
    assert page.locator(".marker-paused").count() == pausiert, "pausierte Orte bei „ausschließen“ verschwunden"
    _foto(page, "07_filter_karte_ausschliessen")
    _alle_an(ctx)
    ctx.close()


def test_hinweis_beim_neuen_ort_host(browser):
    ctx = _kontext(browser, PW_HOST)
    _alle_an(ctx)
    _schalte(ctx, "Deutschland", "Brandenburg", False)
    a = _lege_ort_an(ctx, 52.40, 13.05, "E2E Hinweis A")
    b = _lege_ort_an(ctx, 52.41, 13.06, "E2E Hinweis B")
    try:
        page = ctx.new_page()
        page.goto(URL)
        knopf = page.get_by_role("button", name="Jetzt aktivieren")
        knopf.wait_for(timeout=15000)
        _foto(page, "08_hinweis_host")
        page.keyboard.press("Escape")
        page.mouse.click(5, 5)
        page.go_back()
        assert knopf.is_visible(), "Hinweis ließ sich wegklicken"
        # „Ausgeschaltet lassen“ -> Ort bleibt aus, Hinweis wandert zum nächsten Ort
        page.get_by_role("button", name="Ausgeschaltet lassen").click()
        page.wait_for_timeout(800)
        orte = {o["id"]: o for o in _orte(ctx)}
        gewaehlt = [o for o in (orte[a], orte[b]) if not o["area_undecided"]]
        assert len(gewaehlt) == 1 and gewaehlt[0]["paused"] is True
        # zweiter Ort: „Jetzt aktivieren“ -> Rückfrage mit Ortszahl -> Region an
        knopf.wait_for(timeout=10000)
        knopf.click()
        page.get_by_text("einschalten?", exact=False).wait_for(timeout=10000)
        text = page.locator("#gb-modal").inner_text()
        assert "Orten" in text or "Ort" in text, text
        _foto(page, "09_rueckfrage_ortszahl")
        page.get_by_role("button", name="Region einschalten").click()
        page.wait_for_timeout(1500)
        orte = {o["id"]: o for o in _orte(ctx)}
        assert orte[a]["paused"] is False and orte[b]["paused"] is False
    finally:
        _loesche(ctx, a)
        _loesche(ctx, b)
        _alle_an(ctx)
        ctx.close()


def test_nutzer_ohne_menue_mit_hinweis(browser):
    host = _kontext(browser, PW_HOST)
    _alle_an(host)
    _schalte(host, "Deutschland", "Brandenburg", False)
    ctx = _kontext(browser, PW_USER)
    ort = _lege_ort_an(ctx, 52.42, 13.07, "E2E Nutzer Hinweis")
    try:
        page = ctx.new_page()
        page.goto(URL)
        page.locator("#gb-notice.show").wait_for(timeout=15000)
        assert "Host muss freischalten" in page.locator("#gb-notice").inner_text()
        assert page.get_by_role("button", name="Jetzt aktivieren").count() == 0
        assert page.get_by_role("button", name="Ausgeschaltet lassen").count() == 0
        _foto(page, "10_nutzer_hinweis")
        page.locator("#tab-settings").click()
        page.wait_for_timeout(500)
        assert page.locator("text=Länder & Regionen >> visible=true").count() == 0, "Nutzer sieht das Host-Menü"
        assert ctx.request.get(URL + "/areas").status == 403
        _foto(page, "11_nutzer_einstellungen")
    finally:
        _loesche(host, ort)
        _alle_an(host)
        ctx.close()
        host.close()


def test_alle_gebiete_pausiert_im_feed(browser):
    ctx = _kontext(browser, PW_HOST)
    _alle_an(ctx)
    for land in ctx.request.get(URL + "/areas").json()["laender"]:
        _schalte(ctx, land["name"], None, False)
    try:
        page = ctx.new_page()
        page.goto(URL)
        page.get_by_text("Alle Gebiete pausiert", exact=False).first.wait_for(timeout=15000)
        _foto(page, "12_alle_pausiert_feed")
        page.locator("#tab-settings").click()
        page.get_by_text("Länder & Regionen").first.wait_for(timeout=5000)
        assert "0 von" in page.locator("#gb-settings-summary").inner_text() or "Ländern an" in page.locator("#gb-settings-summary").inner_text()
        _foto(page, "13_einstellungen_alle_aus")
    finally:
        _alle_an(ctx)
        ctx.close()
