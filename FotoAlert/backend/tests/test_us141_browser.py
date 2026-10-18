"""US-141 (Phase A, 2026-10-14) — Playwright-GERÜST für die Teile, die nur im Browser prüfbar sind.

Status: GERÜST. Nicht gegen eine fertige Oberfläche gelaufen (es gibt sie noch nicht); ohne Browser-Umgebung
werden alle Tests ÜBERSPRUNGEN, nicht rot. Die Texte der Knöpfe stammen aus dem Ticket (Entscheidungen 20/23),
alles andere sind Annahmen — siehe backend/tests/README.md, Abschnitt US-141 Phase A.

Voraussetzung (alles drei, sonst Überspringen mit Begründung):
  - Python-Paket ‚playwright‘ mit installiertem Chromium,
  - ein laufender Entwicklungsserver, Adresse in FOTOALERT_E2E_URL (z. B. http://localhost:8000),
  - FOTOALERT_E2E_HOST_PW = Host-Passwort dieses Entwicklungsservers (nie Produktion).
Der Server muss die Umsetzung von US-141 enthalten; vorher laufen die Tests, soweit sie überhaupt starten, rot.

Geprüft wird (nur im Browser prüfbar): AK-45 (Hinweis nicht wegklickbar), AK-92/AK-101 (Karte zeigt pausierte Orte bei
jedem Ereignisfilter gleich), AK-95 (drei verschiedene Meldungen bei leerem Ergebnis), AK-63 (Nutzer sieht keine Knöpfe).
Nicht hier: Restzeit/Fortschritt (AK-18/19, Live), Wetterkarte (AK-14), geöffnete Zweitfenster (AK-70).

KORREKTUR 2026-10-15 (Stephan hat ausdrücklich erlaubt, genau diese eine Testdatei zu ändern): Drei Annahmen des
Gerüsts passten nicht zur gebauten Oberfläche und sind richtiggestellt (Protokoll, Diff und Begründung:
outputs/2026-10-15_US-141-testkorrektur/):
  1. Das Einführungsfenster beim ersten Start verdeckt den Filterknopf -> jeder Browser-Kontext markiert es vorab
     als gesehen (wie in test_us141_oberflaeche.py).
  2. „Alle Gebiete pausiert“ wurde schon nach dem Ausschalten von nur Berlin und Brandenburg erwartet. Das war ein
     Fehler im Test: bei nur zwei abgeschalteten Gebieten läuft der Rest weiter. Jetzt prüft ein Test, dass die
     Meldung bei zwei ausgeschalteten Gebieten NICHT erscheint und die übrigen Orte weiterlaufen, ein zweiter, dass
     sie erscheint, wenn wirklich ALLE Gebiete aus sind.
  3. Der zweite Tipp auf „Goldene Stunde“ traf eine Feed-Karte statt des Filter-Chips -> Chip und Filterknopf
     werden gezielt im Filter-Fenster gesucht, und die Karten-Tests laufen auf dem Karten-Reiter.
Außerdem stellt jeder Test den Ausgangszustand her und räumt danach auf (alle Gebiete an, angelegte Orte gelöscht),
damit die Tests unabhängig von ihrer Reihenfolge sind.
Python-3.9-kompatibel.
"""
from __future__ import annotations

import os
from urllib.parse import quote

import pytest

pytestmark = [pytest.mark.frontend]

URL = os.environ.get("FOTOALERT_E2E_URL", "").rstrip("/")
PW_HOST = os.environ.get("FOTOALERT_E2E_HOST_PW", "")
PW_NUTZER = os.environ.get("FOTOALERT_E2E_USER_PW", "")


def _playwright():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright ist nicht installiert (ausdrücklich benannte fehlende Voraussetzung)")
    if not URL:
        pytest.skip("FOTOALERT_E2E_URL nicht gesetzt (kein Entwicklungsserver angegeben)")
    return sync_playwright


_ANGELEGT = []   # Orte, die ein Test angelegt hat; die Aufräum-Stufe der Fixture löscht sie wieder


@pytest.fixture
def seite():
    sp = _playwright()
    with sp() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 430, "height": 900})
        # Korrektur 1: Einführungsfenster als gesehen markieren, sonst verdeckt es Filterknopf und Menü
        ctx.add_init_script("try{localStorage.setItem('fa_onboarding_seen','1')}catch(e){}")
        yield ctx
        # Aufräumen: als Host anmelden, angelegte Orte löschen, alle Gebiete wieder einschalten
        if PW_HOST:
            try:
                ctx.request.post(URL + "/login", data={"password": PW_HOST})
                for ort in _ANGELEGT:
                    ctx.request.delete(URL + "/locations/" + ort)
                _alle_an(ctx)
            finally:
                del _ANGELEGT[:]
        browser.close()


def _anmelden(ctx, pw, was):
    if not pw:
        pytest.skip("Passwort für %s nicht gesetzt" % was)
    r = ctx.request.post(URL + "/login", data={"password": pw})
    assert r.ok, "Anmeldung als %s fehlgeschlagen: %s" % (was, r.status)


def _schalte(ctx, land, region, an):
    pfad = "/areas/%s" % quote(land) + ("/%s" % quote(region) if region else "")   # Land allein = Sammelschalter
    r = ctx.request.put(URL + pfad, data={"enabled": an})
    assert r.ok, "Schalten fehlgeschlagen: %s %s" % (r.status, r.text())


def _alle_an(ctx, an=True):
    for land in ctx.request.get(URL + "/areas").json()["laender"]:
        _schalte(ctx, land["name"], None, an)


def _lege_ort_an(ctx, lat, lon, name):
    r = ctx.request.post(URL + "/preview-alignment", data={
        "observer_lat": lat, "observer_lon": lon, "subject_lat": lat + 0.004, "subject_lon": lon + 0.004,
        "subject_name": name, "subject_height_m": 50.0, "subject_width_m": 20.0, "days": 1, "save": True,
        "category": "SKYLINE"})
    assert r.ok, r.text()
    _ANGELEGT.append(r.json()["location_id"])
    return r.json()["location_id"]


def test_hinweis_beim_anlegen_ist_nicht_wegklickbar(seite):
    """AK-45 / Entscheidung 23: Legt der Host einen Ort in einer ausgeschalteten Region an, erscheint der Hinweis mit
    ‚Jetzt aktivieren‘ und ‚Ausgeschaltet lassen‘. Weder Esc noch ein Tipp neben das Fenster noch die Zurück-Taste
    schließen ihn; der Ort bleibt aus, bis eine der beiden Möglichkeiten gewählt wurde."""
    _anmelden(seite, PW_HOST, "Host")
    _alle_an(seite)
    _schalte(seite, "Deutschland", "Brandenburg", False)
    seite_ = seite.new_page()
    seite_.goto(URL)
    # Anlegen über die Anlege-Maske der App: Schritte hängen an der fertigen Oberfläche (Annahme).
    ort = _lege_ort_an(seite, 52.40, 13.05, "E2E Hinweis")
    seite_.reload()
    knopf = seite_.get_by_role("button", name="Jetzt aktivieren")
    knopf.wait_for(timeout=10000)
    seite_.keyboard.press("Escape")
    seite_.mouse.click(5, 5)
    seite_.go_back()
    assert knopf.is_visible(), "Hinweis ließ sich wegklicken"
    assert seite_.get_by_role("button", name="Ausgeschaltet lassen").is_visible()
    orte = {o["id"]: o for o in seite.request.get(URL + "/locations").json()}
    assert orte[ort]["paused"] is True, "Ort ist ohne Wahl nicht ausgeschaltet geblieben"


def test_nutzer_sieht_beim_anlegen_in_pausierter_region_keine_knoepfe(seite):
    """AK-63 / Frage 17 (Annahme): Ein normaler Nutzer sieht ‚Region ist pausiert, der Host muss den Ort freischalten‘,
    aber nicht ‚Jetzt aktivieren‘ und ‚Ausgeschaltet lassen‘."""
    _anmelden(seite, PW_HOST, "Host")
    _alle_an(seite)
    _schalte(seite, "Deutschland", "Brandenburg", False)
    _anmelden(seite, PW_NUTZER, "Nutzer")
    seite_ = seite.new_page()
    seite_.goto(URL)
    _lege_ort_an(seite, 52.41, 13.06, "E2E Nutzer")
    seite_.reload()
    seite_.get_by_text("Host", exact=False).first.wait_for(timeout=10000)
    assert seite_.get_by_role("button", name="Jetzt aktivieren").count() == 0
    assert seite_.get_by_role("button", name="Ausgeschaltet lassen").count() == 0


@pytest.mark.parametrize("modus", ["nur", "ausschliessen"])
def test_karte_zeigt_pausierte_orte_bei_jedem_ereignisfilter_gleich(seite, modus):
    """AK-92 / AK-101: Auf der Karte bleiben die Orte eines ausgeschalteten Landes bei ‚nur Art X‘ und bei
    ‚Art X ausschließen‘ gleichermaßen sichtbar (gedämpft). Die Zahl sichtbarer Markierungen ändert sich dabei nicht."""
    _anmelden(seite, PW_HOST, "Host")
    _alle_an(seite)
    _schalte(seite, "Italien", None, False)
    p = seite.new_page()
    p.goto(URL)
    p.locator("#tab-map").click()                                    # Korrektur 3: Karten-Reiter, dort gibt es keine Feed-Karten
    p.locator(".leaflet-marker-icon").first.wait_for(timeout=15000)
    p.wait_for_timeout(1500)
    vorher = p.locator(".leaflet-marker-icon").count()
    pausiert = p.locator(".marker-paused").count()
    assert vorher > 0, "Karte zeigt keine Markierungen — der Test würde sonst nichts beweisen"
    assert pausiert >= 1, "Italien ist aus, aber kein Ort ist als pausiert gekennzeichnet"
    chip = p.locator("#filter-sheet .filter-chip", has_text="Goldene Stunde").first   # Korrektur 3: Chip im Filter-Fenster
    p.locator("#filter-btn").click()
    chip.wait_for(timeout=10000)
    chip.click()                                                      # ein Tipp = nur Art, zweiter = ausschließen (App-Konvention)
    if modus == "ausschliessen":
        chip.click()
    p.wait_for_timeout(500)
    assert p.locator("#filter-sheet .filter-chip.%s" % ("active" if modus == "nur" else "exclude"),
                     has_text="Goldene Stunde").count() >= 1, "Chip steht nicht im erwarteten Zustand (%s)" % modus
    p.keyboard.press("Escape")
    nachher = p.locator(".leaflet-marker-icon").count()
    assert nachher >= vorher - 0, "pausierte Orte sind bei Filter ‚%s‘ von der Karte verschwunden (%d -> %d)" % (modus, vorher, nachher)
    assert p.locator(".marker-paused").count() == pausiert, "gedämpfte Orte bei Filter ‚%s‘ verschwunden" % modus


def _warte_bis_feed_geladen(p):
    p.wait_for_function("typeof Locations !== 'undefined' && Locations.all && Locations.all.length > 0", timeout=15000)
    p.locator("#feed-content .spinner").wait_for(state="detached", timeout=15000)


def test_zwei_abgeschaltete_gebiete_pausieren_nicht_alles(seite):
    """AK-95 (Gegenprobe): Sind nur zwei Gebiete aus (Berlin, Brandenburg), kann nicht alles pausiert sein — die Meldung
    ‚Alle Gebiete pausiert‘ erscheint NICHT, und die Orte aller übrigen Gebiete laufen weiter."""
    _anmelden(seite, PW_HOST, "Host")
    _alle_an(seite)
    for land, region in (("Deutschland", "Berlin"), ("Deutschland", "Brandenburg")):
        _schalte(seite, land, region, False)
    orte = seite.request.get(URL + "/locations").json()
    pausiert = [o for o in orte if o["paused"]]
    laufen = [o for o in orte if not o["paused"]]
    assert pausiert and all(o["region"] in ("Berlin", "Brandenburg") for o in pausiert), "falsche Orte pausiert"
    assert laufen, "Testdaten haben nur Orte in Berlin/Brandenburg — der Test würde nichts beweisen"
    p = seite.new_page()
    p.goto(URL)
    _warte_bis_feed_geladen(p)
    assert p.evaluate("Gebiete.allPaused()") is False
    assert p.get_by_text("Alle Gebiete pausiert", exact=False).count() == 0, "Meldung erscheint, obwohl nur zwei Gebiete aus sind"


def test_leeres_ergebnis_nennt_die_richtige_ursache(seite):
    """AK-95 / AK-13: Sind wirklich ALLE Gebiete aus, sagt der Feed ‚Alle Gebiete pausiert‘ — nicht ‚keine Chancen gefunden‘."""
    _anmelden(seite, PW_HOST, "Host")
    _alle_an(seite, False)
    p = seite.new_page()
    p.goto(URL)
    p.get_by_text("Alle Gebiete pausiert", exact=False).first.wait_for(timeout=10000)
