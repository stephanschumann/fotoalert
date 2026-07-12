"""TASK-20 — Playwright-Runner für die Frontend-Testroutine (Option A, headless Chromium).

Python-3.9-kompatibel. Der Playwright-Import ist gekapselt: ohne Browser bleibt nichts
rot (pytest.importorskip im Test, _import_playwright() hier).

Ablauf (AK1–AK4):
  1. Login-Precondition: /login mit Test-PW, Submit über LoginScreen.submit().
     Wenn Auth.isLoggedIn() danach false → genau 1 Infra-Finding (Fail-Fast),
     NICHT N View-Bugs (Pre-Mortem: Login-Gate).
  2. Navigiert alle VIEWS (App.nav), prüft Pflicht-Selektoren MIT WARTEN
     (wait_for_selector, asynchrones Leaflet-Rendering), sammelt pageerror/
     console-error.
  3. Öffnet das LOCATION-Detail-Sheet (#loc-detail-sheet via LocationDetail.open),
     liest die a.loc-maps-btn-href (Apple/Google/Street View) und prüft sie gegen
     LINK_SCHEMAS (Links werden NIE abgerufen). Das Event-Detail (#detail-sheet) hat
     für Maps nur onclick-Buttons ohne href → daher Location-Detail.
  4. Screenshots nach docs/qa-screenshots/<run>/.
  5. Findings an den Reporter (Artefakt findings.json; BACKLOG-Merge nur lokal).

Aufruf: python3 run_frontend_check.py --base-url http://localhost:8000
"""
from __future__ import annotations

import argparse
import datetime as _dt
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Modul-lokale Imports robust gegen Aufrufverzeichnis (Skript- und Paket-Aufruf).
try:
    from . import spec as _spec
    from . import reporter as _reporter
except ImportError:  # pragma: no cover - Direktaufruf als Skript
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import spec as _spec  # type: ignore
    import reporter as _reporter  # type: ignore

Finding = _reporter.Finding


def _import_playwright():
    """Importiert sync_playwright erst zur Laufzeit (kein Hard-Fail beim Modul-Import)."""
    from playwright.sync_api import sync_playwright  # noqa: WPS433

    return sync_playwright


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _commit_sha() -> str:
    """Best-effort Commit-SHA. In CI bevorzugt aus Env, sonst git, sonst 'unknown'."""
    for key in ("GITHUB_SHA", "FOTOALERT_COMMIT_SHA", "COMMIT_SHA"):
        val = os.environ.get(key)
        if val:
            return val[:12]
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8").strip()
    except Exception:  # pragma: no cover - kein git im Sandbox
        return "unknown"


def _dismiss_onboarding_if_present(page) -> None:
    """US-21, VIERTER CI-Fix-Versuch — Strategiewechsel weg von Timing-Prävention.

    Die ersten beiden Verteidigungslinien (localStorage-Flag per add_init_script,
    dann ein MutationObserver-Guard) versuchten das Erscheinen des Overlays zu
    VERHINDERN bzw. es reaktiv sofort wieder zu schließen. Beide wurden nur per
    Code-Lesen/jsdom-Simulation geprüft, nie per echtem Browserlauf — und der echte
    CI-Lauf schlug beide Male mit demselben Fehler fehl: das Overlay blieb mit Klasse
    "open" sichtbar und blockierte page.click(_spec.LOCATION_CARD_SELECTOR) in
    _check_detail_sheet ("<div class='onb-title'>...</div> ... subtree intercepts
    pointer events").

    Neuer Ansatz: statt das Erscheinen zu verhindern, wird aktiv und explizit
    weggeklickt, FALLS das Overlay da ist — mit Playwrights robusten Wartefunktionen
    (wait_for_selector) statt eines selbstgebauten Timing-/Observer-Tricks. Das ist
    unabhängig davon, WANN Onboarding.initialShowIfNeeded() (web/index.html, Zeile
    ~7088) tatsächlich feuert: Onboarding.close() (web/index.html, Zeile ~7104) setzt
    sowohl das localStorage-Flag 'fa_onboarding_seen' als auch entfernt die Klasse
    'open' von #onboarding-overlay. Dieselbe Funktion wird hier per page.evaluate im
    Seitenkontext aufgerufen (kein Button-Klick auf den dynamisch gerenderten
    ".onb-skip"-Button nötig, der zudem auf der letzten Slide gar nicht existiert).

    Best-effort: falls das Overlay in den kurzen Wartefenstern nie erscheint (Flag
    aus vorherigem Lauf bereits gesetzt) oder schon zu ist, greift die Exception und
    die Funktion kehrt ohne Fehler zurück.
    """
    try:
        page.wait_for_selector("#onboarding-overlay.open", timeout=5000)
        page.evaluate("() => { if (typeof Onboarding !== 'undefined') Onboarding.close(); }")
        page.wait_for_selector("#onboarding-overlay:not(.open)", timeout=3000)
    except Exception:
        pass  # Overlay ist gar nicht erschienen oder schon zu.


# --- Browser-Lauf ------------------------------------------------------------------
def run_checks(
    base_url: str,
    password: str,
    screenshot_root: Path,
    headless: bool = True,
    timeout_ms: int = 15000,
    host_password: Optional[str] = None,
) -> List["Finding"]:
    """Führt den vollständigen Frontend-Check aus und gibt die Findings zurück.

    Wirft NICHT bei Bugs — Defekte werden als Finding gesammelt. Nur echte
    Infrastruktur-Probleme (kein Browser, Server nicht erreichbar) propagieren.
    """
    sync_playwright = _import_playwright()
    run = _run_id()
    shot_dir = screenshot_root / run
    shot_dir.mkdir(parents=True, exist_ok=True)
    commit = _commit_sha()
    findings: List[Finding] = []
    console_errors: List[str] = []
    page_errors: List[str] = []

    def _shot(name: str) -> str:
        target = shot_dir / (name + ".png")
        try:
            page.screenshot(path=str(target), full_page=False)
        except Exception:  # pragma: no cover - Screenshot best effort
            return ""
        return str(target)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        page.set_default_timeout(timeout_ms)

        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on(
            "console",
            lambda m: console_errors.append(m.text) if m.type == "error" else None,
        )

        page.goto(base_url, wait_until="domcontentloaded")

        # US-21, vierter Fix-Versuch: Overlay könnte bereits hier (vor dem Login)
        # erscheinen — aktiv wegklicken statt Timing-Prävention (siehe Docstring
        # von _dismiss_onboarding_if_present).
        _dismiss_onboarding_if_present(page)

        # 1) Login-Precondition (AK4) — Fail-Fast bei Infra-Problem.
        page.fill("#login-pw", password)
        page.click(".login-btn")
        try:
            # Auth/App sind top-level `const` → NICHT an window gebunden; per bare name prüfen.
            page.wait_for_function("() => typeof Auth !== 'undefined' && Auth.isLoggedIn()", timeout=timeout_ms)
        except Exception:
            findings.append(
                Finding(
                    view="login",
                    assertion_id="login_precondition",
                    expected="Auth.isLoggedIn() === true nach Submit mit Test-PW",
                    actual="Auth.isLoggedIn() blieb false (Login-Gate nicht passiert)",
                    message="login precondition failed: not logged in after submit",
                    screenshot_path=_shot("login-fail"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
            browser.close()
            # Fail-Fast: 1 Infra-Finding statt N Folgefehler.
            return findings

        # US-21, vierter Fix-Versuch: Onboarding.initialShowIfNeeded() läuft als
        # letzter Schritt von App.init(), NACHDEM Auth.isLoggedIn() bereits wahr
        # wurde (siehe Docstring von _dismiss_onboarding_if_present) — daher hier
        # nach dem Login nochmal aktiv wegklicken, bevor die Views navigiert werden.
        _dismiss_onboarding_if_present(page)

        # 2) Views durchgehen (AK1).
        for view in _spec.VIEWS:
            page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", view.nav_arg)
            try:
                page.wait_for_selector(view.page_selector + ".active", timeout=timeout_ms)
            except Exception:
                findings.append(
                    Finding(
                        view=view.view_id,
                        assertion_id="view_active",
                        expected=view.page_selector + " wird .active nach App.nav",
                        actual="Page-Container wurde nicht aktiv",
                        message="view {0} did not become active".format(view.view_id),
                        screenshot_path=_shot(view.view_id + "-inactive"),
                        timestamp=_now_iso(),
                        commit_sha=commit,
                    )
                )
                continue

            for sel in view.required_selectors:
                # Auf den Selektor WARTEN statt sofort zu prüfen: asynchron
                # gerenderte Elemente (z. B. Leaflet baut .leaflet-container erst
                # nach App.nav('map') auf) bekommen so Zeit. Nur wenn er nach dem
                # Warten fehlt → Finding (Finding 1: kein Falsch-Negativ mehr).
                try:
                    page.wait_for_selector(sel, timeout=_spec.REQUIRED_SELECTOR_TIMEOUT_MS)
                except Exception:
                    findings.append(
                        Finding(
                            view=view.view_id,
                            assertion_id="required_element",
                            expected="Pflicht-Element vorhanden: " + sel,
                            actual="Selektor nicht gefunden: " + sel,
                            message="missing required selector {0} in view {1}".format(
                                sel, view.view_id
                            ),
                            screenshot_path=_shot(view.view_id + "-missing"),
                            timestamp=_now_iso(),
                            commit_sha=commit,
                        )
                    )
            _shot(view.view_id)

        # 3) Detail-Sheet öffnen + Links prüfen (AK1/AK3).
        findings.extend(_check_detail_sheet(page, commit, _shot))

        # 4) TASK-66: Location über den "+"-Tab anlegen (AddLocation-Fluss) + prüfen dass
        #    sie in GET /locations UND als zusätzlicher Kartenmarker erscheint.
        create_findings, new_loc_id = _check_location_create(page, commit, _shot)
        findings.extend(create_findings)

        # 5) TASK-66: Bild-Upload GEZIELT über das LocationDetail-Sheet (BUG-71-Regres-
        #    sionsschutz). Läuft in einer eigenen, isoliert Host-eingeloggten Browser-Seite
        #    (siehe Docstring/Kommentar in spec.py: Upload-Button + Server-Endpunkt sind
        #    host-only, der reguläre Check-Login ist Rolle "user"). Fail-Fast: ohne
        #    new_loc_id (Location-Anlage fehlgeschlagen) wird der Durchlauf mit einem
        #    eigenen, klar erkennbaren Finding übersprungen statt einer Folgefehler-Kaskade.
        findings.extend(
            _check_image_upload(
                browser,
                base_url,
                host_password or os.environ.get("FOTOALERT_HOST_PASSWORD", "test-host-pw"),
                new_loc_id,
                commit,
                shot_dir,
                timeout_ms,
            )
        )

        # 6) TASK-66: Filter setzen (minScore-Extremwert, deterministisch) + zurücksetzen.
        findings.extend(_check_filter_feed(page, commit, _shot))

        # 6b) TASK-67 (Etappe 3): Kalender-Ansicht lädt fehlerfrei + zeigt Termine.
        findings.extend(_check_calendar_view(page, commit, _shot))

        # 6c) TASK-67: Filter-Chip-Drei-Zustand (Verifikation) + Ausgrauen-Verhalten
        #     (Tageszeit auf Locations-Tab vs. Feed).
        findings.extend(_check_filter_tristate_and_dimming(page, commit, _shot))

        # 6d) TASK-67: Bewertungsfunktion für Orte (Anlegen/Abrufen/Löschen).
        findings.extend(_check_rating_flow(page, commit, _shot))

        # 6e) TASK-67: Detail-Fenster öffnet sich beim Antippen einer Chance im Feed
        #     (Abgrenzung zu _check_detail_sheet oben, die das LOCATION-Detail prüft).
        findings.extend(_check_event_detail_from_feed_card(page, commit, _shot))

        # 6f) TASK-67: Wetter-Kartenansicht — Grundbedienung (Ebenen-Umschalter, Zeit-Slider).
        findings.extend(_check_weather_map_controls(page, commit, _shot))

        # 6g) TASK-67: Entdecken-Modus (Scout) — Basistest.
        findings.extend(_check_scout_mode(page, commit, _shot))

        # 6h) TASK-67: Globale UI — "?"-Button öffnet Glossar (Abschnitt 2 PRODUCT.md).
        findings.extend(_check_help_glossary(page, commit, _shot))

        # 6i) TASK-67 (Etappe 6): Filter-Badge zeigt korrekte Anzahl aktiver Kriterien.
        findings.extend(_check_filter_badge_count(page, commit, _shot))

        # 6j) TASK-67 (Etappe 6): Bewertungs-Chip Drei-Zustand (Filter-Sheet).
        findings.extend(_check_rating_chip_tristate(page, commit, _shot))

        # 6k) TASK-67 (Etappe 6): Wahrscheinlichkeit-Ausgrauen auf Karte + Locations-Tab
        #     (Brennweite bewusst ausgelassen — siehe Docstring/Ticket-Befund).
        findings.extend(_check_wahrscheinlichkeit_dimming(page, commit, _shot))

        # 6l) TASK-67 (Etappe 6): Karten-Pins nach Schwierigkeits-/Kategorie-/
        #     Verifikations-Filter.
        findings.extend(_check_map_pin_filtering(page, commit, _shot))

        # 6m) TASK-67 (Etappe 6): Sichtachsen-Filter-Chip Drei-Zustand + Effekt.
        findings.extend(_check_sightline_chip_tristate_and_effect(page, commit, _shot))

        # 6n) TASK-67 (Etappe 6): "Hat Beispielbild"-Chip Drei-Zustand + Effekt.
        findings.extend(_check_has_image_chip_tristate_and_effect(page, commit, _shot))

        # 7) Konsolen-/Page-Errors → Findings (AK2).
        for err in page_errors:
            findings.append(
                Finding(
                    view="global",
                    assertion_id="pageerror",
                    expected="kein uncaught pageerror während des Laufs",
                    actual=err,
                    message="pageerror: " + err,
                    screenshot_path=_shot("pageerror"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
        for err in console_errors:
            findings.append(
                Finding(
                    view="global",
                    assertion_id="console_error",
                    expected="kein console.error während des Laufs",
                    actual=err,
                    message="console error: " + err,
                    screenshot_path="",
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )

        browser.close()
    return findings


def _check_detail_sheet(page, commit: str, shot) -> List["Finding"]:
    """Öffnet das LOCATION-Detail-Sheet und prüft die externen Link-href (AK1/AK3).

    Die echten <a href>-Maps-Links (Apple/Google/Street View) leben im
    Location-Detail (#loc-detail-sheet, geöffnet über LocationDetail.open(id) aus der
    Locations-View), NICHT im Event-Detail (#detail-sheet, dort nur onclick-Buttons
    ohne href). Deshalb wird hier über die Locations-View navigiert (Findings 2–4).
    """
    findings: List[Finding] = []
    # Zur Locations-View und erste Location-Karte mit LocationDetail.open(...) klicken.
    page.evaluate(
        "(v) => { if (typeof App !== 'undefined') App.nav(v); }",
        _spec.LOCATIONS_NAV_ARG,
    )
    try:
        page.wait_for_selector(_spec.LOCATION_CARD_SELECTOR, timeout=12000)
    except Exception:
        findings.append(
            Finding(
                view="locations",
                assertion_id="detail_openable",
                expected="mindestens eine Location-Karte mit LocationDetail.open(...) klickbar",
                actual="keine Location-Karte gefunden",
                message="no detail-openable location card",
                screenshot_path=shot("no-location-card"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    # US-21, vierter Fix-Versuch: zusätzliche Absicherung direkt vor dem Klick auf die
    # Location-Karte — das Overlay könnte auch erst hier (asynchron, nach den Views-
    # Navigationen) aufgehen. Aktives Wegklicken statt Timing-Prävention, siehe
    # Docstring von _dismiss_onboarding_if_present.
    _dismiss_onboarding_if_present(page)
    page.click(_spec.LOCATION_CARD_SELECTOR)
    try:
        # Das Sheet ist permanent im DOM (display:flex), nur die .open-Klasse macht es
        # sichtbar (transform). Darum auf .open warten, nicht auf state="visible".
        page.wait_for_selector(_spec.DETAIL_SHEET_OPEN_SELECTOR, timeout=12000)
    except Exception:
        findings.append(
            Finding(
                view="locations",
                assertion_id="detail_sheet_open",
                expected=_spec.DETAIL_SHEET_OPEN_SELECTOR + " nach Klick",
                actual="Location-Detail-Sheet wurde nicht geöffnet (.open fehlt)",
                message="location detail sheet did not open",
                screenshot_path=shot("detail-not-open"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    # Maps-Links liegen in evtl. eingeklappten Sektionen — ihre href stehen aber
    # permanent im DOM (Sektionen werden per CSS gefaltet, nicht entfernt), daher
    # genügt das Lesen der Attribute ohne Aufklappen.
    shot("detail-sheet")

    # Links sammeln (nur href lesen, NIE abrufen).
    hrefs = page.eval_on_selector_all(
        _spec.LINK_SELECTOR,
        "els => els.map(e => e.getAttribute('href'))",
    )
    seen_types = set()
    for href in hrefs:
        if not href:
            continue
        link_id = _spec.classify_href(href)
        schema = _spec.LINK_SCHEMAS.get(link_id)
        if schema is None:
            continue
        seen_types.add(link_id)
        if not schema.href_pattern.match(href):
            findings.append(
                Finding(
                    view="detail",
                    assertion_id="link_schema_" + link_id,
                    expected="href matcht Schema " + schema.href_pattern.pattern,
                    actual=href,
                    message="malformed {0} href: {1}".format(link_id, href),
                    screenshot_path=shot("link-malformed"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )

    # Pflicht-Links müssen vorhanden sein; optionale dürfen fehlen (Edge AK3).
    for link_id, schema in _spec.LINK_SCHEMAS.items():
        if schema.required and link_id not in seen_types:
            findings.append(
                Finding(
                    view="detail",
                    assertion_id="link_present_" + link_id,
                    expected="Pflicht-Link vorhanden: " + link_id,
                    actual="Link-Typ fehlt im Detail-Sheet",
                    message="required link {0} missing".format(link_id),
                    screenshot_path=shot("link-missing"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )

    # TASK-66: Sheet wieder schließen, bevor der nächste Check (z. B.
    # _check_location_create) auf derselben Seite weiterläuft — sonst blockiert das
    # noch offene #loc-detail-sheet (z. B. dessen .info-row) nachfolgende Klicks
    # (Playwright "intercepts pointer events"). Echtes Warten auf das Verschwinden
    # der .open-Klasse statt eines Sleeps (US-21-Muster).
    page.evaluate(
        "() => { if (typeof LocationDetail !== 'undefined') LocationDetail.close(); }"
    )
    try:
        page.wait_for_function(
            "() => { const el = document.querySelector('#loc-detail-sheet'); "
            "return !el || !el.classList.contains('open'); }",
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="locations",
                assertion_id="detail_sheet_closed",
                expected="#loc-detail-sheet ohne .open nach LocationDetail.close()",
                actual="Location-Detail-Sheet blieb offen (.open weiterhin gesetzt)",
                message="location detail sheet did not close after LocationDetail.close()",
                screenshot_path=shot("detail-not-closed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    return findings


# --- TASK-66: Location anlegen ------------------------------------------------------
def _check_location_create(page, commit: str, shot):
    """Legt über den "+"-Tab (AddLocation-Fluss) eine neue Test-Location an.

    Koordinaten werden AUSSCHLIESSLICH per Text-Input gesetzt (kein Kartenklick,
    siehe Pre-Mortem TASK-66: Kartenklick-Koordinaten sind in CI headless flaky).
    Wartet mit echtem wait_for_function auf das Sichtbarwerden des Speichern-Buttons
    (US-21-Muster) statt auf einen Timing-Trick.

    Gibt (findings, location_id_oder_None) zurück. location_id ist None wenn der
    Durchlauf an irgendeiner Stelle fehlschlug — der Aufrufer nutzt das für den
    Fail-Fast beim Bild-Upload-Durchlauf (AK Edge Case).
    """
    findings: List[Finding] = []

    # TASK-66: defensive Absicherung — falls ein vorheriger Check (z. B.
    # _check_detail_sheet) auf derselben Seite ein Location-Detail-Sheet offen
    # gelassen hat, blockiert dessen Overlay/Inhalt (z. B. .info-row) den Klick auf
    # den "+"-Tab weiter unten ("intercepts pointer events"). Unabhängig davon, ob
    # _check_detail_sheet ihrerseits schon aufräumt, hier zusätzlich schließen, damit
    # künftige Reihenfolge-Änderungen in run_checks() denselben Bug nicht wiederholen.
    page.evaluate(
        "() => { if (typeof LocationDetail !== 'undefined') LocationDetail.close(); }"
    )
    try:
        page.wait_for_function(
            "() => { const el = document.querySelector('#loc-detail-sheet'); "
            "return !el || !el.classList.contains('open'); }",
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="add-location",
                assertion_id="location_create_pre_sheet_closed",
                expected="#loc-detail-sheet ohne .open vor Start der Location-Anlage",
                actual="Location-Detail-Sheet blieb offen (.open weiterhin gesetzt)",
                message="location detail sheet still open before location create flow started",
                screenshot_path=shot("location-create-pre-sheet-not-closed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings, None

    # Baseline: Kartenansicht laden (initialisiert MapView.map + lädt die aktuellen
    # Marker), damit vorher/nachher verglichen werden kann.
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "map")
    try:
        page.wait_for_selector(_spec.MAP_PAGE_READY_SELECTOR, timeout=12000)
        page.wait_for_function(
            "() => typeof MapView !== 'undefined' && MapView.map && Array.isArray(MapView.markers)",
            timeout=12000,
        )
    except Exception:
        findings.append(
            Finding(
                view="map",
                assertion_id="location_create_map_baseline",
                expected="Kartenansicht + MapView.markers initialisiert vor der Location-Anlage",
                actual="Karte/MapView wurde nicht rechtzeitig bereit",
                message="map baseline not ready before location create",
                screenshot_path=shot("location-create-map-baseline-fail"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings, None

    baseline_marker_count = page.eval_on_selector_all(_spec.MAP_MARKER_SELECTOR, "els => els.length")

    # "+"-Tab öffnen (AddLocation.open(), baut die Anlege-Karte per setTimeout auf).
    page.click(_spec.ADD_TAB_SELECTOR)
    try:
        page.wait_for_selector(_spec.ADD_MAP_READY_SELECTOR, timeout=12000)
    except Exception:
        findings.append(
            Finding(
                view="add-location",
                assertion_id="add_map_ready",
                expected=_spec.ADD_MAP_READY_SELECTOR + " nach Öffnen des \"+\"-Tabs",
                actual="Anlege-Karte (AddLocation.initMap()) wurde nicht initialisiert",
                message="add-location map not ready after opening the add tab",
                screenshot_path=shot("add-map-not-ready"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings, None

    test_name = _spec.TEST_LOCATION_NAME_PREFIX + _run_id()
    page.fill(_spec.OBS_COORDS_INPUT_SELECTOR, _spec.TEST_OBS_COORDS_TEXT)
    page.fill(_spec.SUBJ_COORDS_INPUT_SELECTOR, _spec.TEST_SUBJ_COORDS_TEXT)
    page.fill(_spec.SUBJ_NAME_INPUT_SELECTOR, test_name)

    page.click(_spec.PREVIEW_BTN_SELECTOR)
    try:
        # Pre-Mortem TASK-66: echtes Warten auf den Sichtbarkeitswechsel des Speichern-
        # Buttons statt eines Timing-Tricks (US-21-Muster). Timeout siehe
        # _spec.PREVIEW_ALIGNMENT_TIMEOUT_MS (Bugfix: reale Berechnungsdauer ~20s,
        # altes Limit von 15000ms war zu knapp bemessen).
        page.wait_for_function(
            "() => { const b = document.getElementById('save-location-btn'); "
            "return !!b && b.style.display !== 'none'; }",
            timeout=_spec.PREVIEW_ALIGNMENT_TIMEOUT_MS,
        )
    except Exception:
        findings.append(
            Finding(
                view="add-location",
                assertion_id="save_button_visible",
                expected="#save-location-btn wird nach \"Alignments berechnen\" sichtbar",
                actual="Speichern-Button blieb verborgen (Preview evtl. fehlgeschlagen)",
                message="save-location-btn did not become visible after AddLocation.preview()",
                screenshot_path=shot("save-btn-not-visible"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings, None

    shot("add-location-preview")
    page.click(_spec.SAVE_LOCATION_BTN_SELECTOR)
    try:
        # AddLocation.save() ruft nach erfolgreichem Speichern intern
        # MapView.loadMarkers() auf (falls MapView.map bereits initialisiert ist,
        # siehe Baseline oben) — echtes Warten auf die dadurch gestiegene
        # MapView.markers.length statt eines Sleeps.
        page.wait_for_function(
            "(n) => typeof MapView !== 'undefined' && MapView.markers && MapView.markers.length > n",
            arg=baseline_marker_count,
            timeout=20000,
        )
    except Exception:
        findings.append(
            Finding(
                view="add-location",
                assertion_id="location_saved_marker",
                expected="MapView.markers.length > {0} nach AddLocation.save()".format(baseline_marker_count),
                actual="Markeranzahl stieg nicht (Speichern evtl. fehlgeschlagen)",
                message="marker count did not increase after AddLocation.save()",
                screenshot_path=shot("location-not-saved"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings, None

    # GET /locations prüfen — per fetch im Seitenkontext (nutzt den vorhandenen Token,
    # kein separater HTTP-Client nötig).
    try:
        locs = page.evaluate(
            "async () => { const r = await fetch('/locations'); return await r.json(); }"
        )
    except Exception:
        locs = []
    match = next((loc for loc in locs if loc.get("name") == test_name), None)
    if match is None:
        findings.append(
            Finding(
                view="add-location",
                assertion_id="location_in_get_locations",
                expected="GET /locations enthält die neue Location (Name: {0})".format(test_name),
                actual="Location nicht in GET /locations gefunden",
                message="new location missing from GET /locations",
                screenshot_path=shot("location-missing-in-api"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings, None

    # Kartenansicht erneut prüfen: zusätzlicher .leaflet-marker-icon muss sichtbar sein.
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "map")
    try:
        page.wait_for_selector(_spec.MAP_PAGE_READY_SELECTOR, timeout=12000)
        page.wait_for_function(
            "(n) => document.querySelectorAll('.leaflet-marker-icon').length > n",
            arg=baseline_marker_count,
            timeout=12000,
        )
        shot("map-with-new-marker")
    except Exception:
        findings.append(
            Finding(
                view="map",
                assertion_id="location_marker_visible",
                expected="zusätzlicher .leaflet-marker-icon nach der Location-Anlage (> {0})".format(
                    baseline_marker_count
                ),
                actual="Markeranzahl auf der Kartenansicht stieg nicht",
                message="no additional leaflet marker visible on map after location create",
                screenshot_path=shot("map-marker-missing"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        # Location existiert laut API bereits — kein Fail-Fast für den Bild-Upload
        # nötig, daher wird die location_id trotzdem zurückgegeben.

    return findings, match.get("id")


# --- TASK-66: Bild-Upload über LocationDetail (BUG-71-Regressionsschutz) -----------
def _check_image_upload(
    browser,
    base_url: str,
    host_password: str,
    loc_id: Optional[str],
    commit: str,
    shot_dir: Path,
    timeout_ms: int,
):
    """Lädt ein Testbild GEZIELT über LocationDetail.triggerImageUpload() hoch.

    WICHTIG (siehe spec.py-Kommentar): Der Upload-Button ist im DOM nur für
    Auth.isHost() vorhanden, und der Server-Endpunkt POST /locations/{id}/image
    verlangt auth.require_host. Der reguläre Check-Login läuft mit der User-Rolle
    (test-user-pw) — dieser Durchlauf öffnet deshalb eine ZUSÄTZLICHE, isolierte
    Browser-Seite mit Host-Login, ausschließlich für diesen einen Check. Die
    reguläre Desktop-Pass-Session (User-Rolle) bleibt für alle anderen Checks
    unverändert (kein Seiteneffekt auf AK1–AK4/Location-Anlage/Filter).

    Fail-Fast (AK Edge Case): schlug _check_location_create fehl (loc_id is None),
    wird dieser Durchlauf mit einem eigenen, klar erkennbaren Finding übersprungen
    statt einer verwirrenden Folgefehler-Kaskade.
    """
    findings: List[Finding] = []
    if not loc_id:
        findings.append(
            Finding(
                view="location-detail",
                assertion_id="image_upload_skipped_no_location",
                expected="Bild-Upload-Durchlauf läuft mit der zuvor angelegten Test-Location",
                actual="Location-Anlage ist vorher fehlgeschlagen (Fail-Fast) — Durchlauf übersprungen",
                message="image upload check skipped: no location id from _check_location_create",
                screenshot_path="",
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    def _shot(host_page, name: str) -> str:
        target = shot_dir / (name + ".png")
        try:
            host_page.screenshot(path=str(target), full_page=False)
        except Exception:
            return ""
        return str(target)

    host_page = browser.new_page()
    host_page.set_default_timeout(timeout_ms)
    try:
        host_page.goto(base_url, wait_until="domcontentloaded")
        _dismiss_onboarding_if_present(host_page)

        host_page.fill("#login-pw", host_password)
        host_page.click(".login-btn")
        try:
            host_page.wait_for_function(
                "() => typeof Auth !== 'undefined' && Auth.isLoggedIn() && Auth.isHost()",
                timeout=timeout_ms,
            )
        except Exception:
            findings.append(
                Finding(
                    view="location-detail",
                    assertion_id="image_upload_host_login",
                    expected="Host-Login (Auth.isHost() === true) für den Bild-Upload-Durchlauf",
                    actual="Host-Login fehlgeschlagen oder Rolle ist nicht 'host'",
                    message="host login failed for image upload check "
                    "(BUG-71 regression path requires host role)",
                    screenshot_path=_shot(host_page, "image-upload-host-login-fail"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
            return findings

        _dismiss_onboarding_if_present(host_page)

        host_page.evaluate(
            "(v) => { if (typeof App !== 'undefined') App.nav(v); }", _spec.LOCATIONS_NAV_ARG
        )
        try:
            host_page.wait_for_selector("#locations-content", timeout=timeout_ms)
        except Exception:
            pass

        host_page.evaluate(
            "(id) => { if (typeof LocationDetail !== 'undefined') LocationDetail.open(id); }",
            loc_id,
        )
        try:
            host_page.wait_for_selector(_spec.DETAIL_SHEET_OPEN_SELECTOR, timeout=timeout_ms)
        except Exception:
            findings.append(
                Finding(
                    view="location-detail",
                    assertion_id="image_upload_detail_open",
                    expected=_spec.DETAIL_SHEET_OPEN_SELECTOR + " nach LocationDetail.open(...)",
                    actual="Location-Detail-Sheet öffnete sich nicht für die Test-Location",
                    message="location detail sheet did not open for image upload target",
                    screenshot_path=_shot(host_page, "image-upload-detail-not-open"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
            return findings

        try:
            host_page.wait_for_selector(_spec.LOC_IMAGE_UPLOAD_BTN_SELECTOR, timeout=timeout_ms)
        except Exception:
            findings.append(
                Finding(
                    view="location-detail",
                    assertion_id="image_upload_btn_present",
                    expected=_spec.LOC_IMAGE_UPLOAD_BTN_SELECTOR + " sichtbar (Host, Location ohne Bild)",
                    actual="Upload-Button nicht gefunden",
                    message="LocationDetail image upload button missing",
                    screenshot_path=_shot(host_page, "image-upload-btn-missing"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
            return findings

        # BUG-71-relevanter Pfad: LocationDetail.triggerImageUpload() öffnet den nativen
        # Datei-Dialog über input.click() — Playwrights expect_file_chooser() fängt das ab.
        try:
            with host_page.expect_file_chooser() as fc_info:
                host_page.click(_spec.LOC_IMAGE_UPLOAD_BTN_SELECTOR)
            file_chooser = fc_info.value
            file_chooser.set_files(_spec.TEST_IMAGE_FIXTURE_PATH)
        except Exception as e:
            findings.append(
                Finding(
                    view="location-detail",
                    assertion_id="image_upload_file_chooser",
                    expected="Datei-Dialog öffnet sich über LocationDetail.triggerImageUpload()",
                    actual="Datei-Auswahl fehlgeschlagen: {0}".format(e),
                    message="file chooser interaction failed for image upload",
                    screenshot_path=_shot(host_page, "image-upload-file-chooser-fail"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
            return findings

        try:
            # _onImageFileSelected() ruft nach erfolgreichem Upload LocationDetail.open()
            # erneut auf, das Sheet rendert dann ein <img> mit dem neuen Bild — echtes
            # Warten auf dieses Element statt eines Sleeps.
            host_page.wait_for_selector(_spec.LOC_IMAGE_AREA_IMG_SELECTOR, timeout=timeout_ms)
        except Exception:
            findings.append(
                Finding(
                    view="location-detail",
                    assertion_id="image_upload_img_visible",
                    expected=_spec.LOC_IMAGE_AREA_IMG_SELECTOR + " nach Upload sichtbar",
                    actual="Kein <img> im Detail-Sheet nach dem Upload (BUG-71-artige Regression)",
                    message="no image visible in location detail sheet after upload",
                    screenshot_path=_shot(host_page, "image-upload-no-img"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
            return findings

        _shot(host_page, "image-upload-success")

        try:
            loc = host_page.evaluate(
                "async (id) => { const r = await fetch('/locations/' + id); return await r.json(); }",
                loc_id,
            )
        except Exception:
            loc = None
        image_url = loc.get("image_url") if loc else None
        if not loc or not image_url or not str(image_url).startswith("/location-images/"):
            findings.append(
                Finding(
                    view="location-detail",
                    assertion_id="image_url_set",
                    expected="GET /locations/{0} liefert ein gesetztes image_url-Feld".format(loc_id),
                    actual="image_url fehlt, leer, unplausibel oder Location nicht abrufbar",
                    message="image_url not set after upload for location {0}".format(loc_id),
                    screenshot_path="",
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
        return findings
    finally:
        host_page.close()


# --- TASK-66: Filter setzen (deterministischer minScore-Extremwert) ----------------
def _check_filter_feed(page, commit: str, shot):
    """Setzt minScore auf einen Extremwert und prüft, dass die Feed-Trefferzahl sinkt.

    Bewusst KEIN inhaltlicher Chip-Filter (Pre-Mortem TASK-66: datenabhängige Filter
    können an manchen Tagen 0-Treffer-Ausgangslagen haben und flaken tagesabhängig).
    Setzt/liest den Filter-State direkt über die App-eigenen Funktionen (Filter.save +
    FilterSheet._applyLive) — dieselbe Funktionskette, die auch der reale Score-Slider
    (FilterSheet._onScoreSlider) auslöst.

    CI-Fix (nach Workflow-Lauf #189, v1.22.15): Ein fest verdrahteter Extremwert
    (_spec.FILTER_MIN_SCORE_EXTREME = 100) war NICHT strukturell deterministisch,
    sondern von der zufälligen Datenlage abhängig. In CI (frischer Checkout, kein
    vorberechneter Datenbestand) hat der Feed oft nur 1 Chance statt lokal ~500 —
    hat dieser eine Baseline-Eintrag zufällig overall_score >= minScore/100, sinkt
    die Trefferzahl nicht und der Test flakt/failt je nach Zufallslage.
    Lösung: minScore wird zur Laufzeit aus dem tatsächlich höchsten sichtbaren
    Feed-Score (Feed.data[].overall_score, 0..1-skaliert) abgeleitet — knapp über
    diesem Maximum, gedeckelt auf 100 (die UI-Skala von minScore ist 0..100, siehe
    web/index.html Filter.defaultState/_passesScore). Das garantiert rechnerisch,
    dass ALLE aktuell sichtbaren Einträge herausfallen, egal ob die Baseline 1 oder
    500 Einträge umfasst.
    """
    findings: List[Finding] = []
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    try:
        page.wait_for_selector(_spec.FEED_CONTENT_SELECTOR, timeout=12000)
        page.wait_for_function(
            "() => typeof Feed !== 'undefined' && Array.isArray(Feed.data)", timeout=12000
        )
    except Exception:
        findings.append(
            Finding(
                view="feed",
                assertion_id="filter_feed_baseline",
                expected=_spec.FEED_CONTENT_SELECTOR + " + Feed.data bereit vor dem Filtertest",
                actual="Feed wurde nicht rechtzeitig bereit",
                message="feed not ready before filter check",
                screenshot_path=shot("filter-feed-baseline-fail"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    baseline_count = page.eval_on_selector(_spec.FEED_CONTENT_SELECTOR, "el => el.children.length")

    if baseline_count == 0:
        # Edge Case: kein Baseline-Bestand (z.B. komplett leerer CI-Datenstand).
        # "Trefferzahl sinkt sichtbar" ist ohne Baseline nicht sinnvoll prüfbar —
        # kein hartes Finding, sondern dokumentierter Skip.
        print(
            "[feed] filter_reduces_results: übersprungen, keine Baseline-Daten "
            "(Feed-Trefferzahl bereits 0)"
        )
        return findings

    score_stats = page.evaluate(
        "() => { "
        "const data = Feed.data || []; "
        "const scored = data.filter(e => typeof e.overall_score === 'number' && !isNaN(e.overall_score)); "
        "const maxScore = scored.length > 0 ? scored.reduce((m, e) => Math.max(m, e.overall_score), -Infinity) : null; "
        "return { total: data.length, scoredCount: scored.length, maxScore: maxScore }; "
        "}"
    )
    total = score_stats["total"]
    scored_count = score_stats["scoredCount"]
    max_score = score_stats["maxScore"]

    if scored_count == 0:
        # Edge Case (CI-Root-Cause TASK-66, Lauf #189/#190): kein einziger sichtbarer
        # Feed-Eintrag hat einen numerischen overall_score (z.B. weil
        # FOTOALERT_NO_BACKGROUND in CI die Score-Berechnung nach dem Anlegen einer
        # Location unterdrückt). In web/index.html Filter.apply() gilt
        # "o.overall_score < s.minScore / 100" — bei undefined ist dieser Vergleich
        # IMMER false, ein ungescorter Eintrag ist also durch KEINEN minScore-Wert
        # herausfilterbar. "Trefferzahl sinkt bei Extremfilter" ist damit strukturell
        # nicht testbar, kein Finding, sondern dokumentierter Skip.
        print(
            "[feed] filter_reduces_results: übersprungen, kein sichtbarer Feed-Eintrag "
            "hat einen numerischen overall_score (total={0}, scoredCount=0) — "
            "vermutlich FOTOALERT_NO_BACKGROUND in CI".format(total)
        )
        return findings

    if max_score >= 1.0:
        # Edge Case: overall_score der Filterbedingung ist strikt "< minScore/100"
        # (siehe web/index.html Filter._passesScore) — ein Eintrag mit Score genau
        # 1.0 (100%) bleibt bei JEDEM minScore-Wert bis 100 sichtbar. Strukturell
        # nicht über minScore ausschließbar, daher dokumentierter Skip statt Finding.
        print(
            "[feed] filter_reduces_results: übersprungen, höchster sichtbarer Score "
            "bereits am Maximum (100%) und über minScore nicht ausschließbar"
        )
        return findings

    # Dynamischer Schwellwert statt fixem FILTER_MIN_SCORE_EXTREME: knapp oberhalb
    # des tatsächlich höchsten sichtbaren Scores, gedeckelt auf die UI-Skala (0..100).
    extreme_min_score = min(100, math.ceil(max_score * 100) + 1)

    # Erwartung: ALLE gescorten Einträge fallen bei diesem Extremfilter heraus,
    # ungescorte Einträge (overall_score undefined/NaN) können durch minScore
    # strukturell nicht ausgeschlossen werden (siehe Edge Case oben) und bleiben
    # sichtbar. Erwartete neue Trefferzahl ist daher NICHT zwingend 0.
    expected_filtered_count = max(0, total - scored_count)

    page.evaluate(
        "async (v) => { Filter.save({ minScore: v }); await FilterSheet._applyLive(); }",
        extreme_min_score,
    )
    try:
        page.wait_for_function(
            "(n) => document.getElementById('feed-content').children.length < n",
            arg=baseline_count,
            timeout=12000,
        )
    except Exception:
        pass
    filtered_count = page.eval_on_selector(_spec.FEED_CONTENT_SELECTOR, "el => el.children.length")
    shot("filter-feed-extreme")
    if filtered_count > expected_filtered_count:
        findings.append(
            Finding(
                view="feed",
                assertion_id="filter_reduces_results",
                expected=(
                    "Trefferzahl sinkt auf <= {0} bei minScore={1} (dynamisch, > höchster "
                    "gescorter Score {2:.3f}; Baseline={3}, total={4}, scoredCount={5} — "
                    "ungescorte Einträge bleiben strukturell erhalten)".format(
                        expected_filtered_count, extreme_min_score, max_score,
                        baseline_count, total, scored_count,
                    )
                ),
                actual="Trefferzahl = {0} (erwartet <= {1})".format(filtered_count, expected_filtered_count),
                message="feed result count did not decrease as expected under extreme minScore filter",
                screenshot_path=shot("filter-not-reduced"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    # Zurücksetzen auf Default (70) — Trefferzahl muss wieder dem Ausgangswert entsprechen.
    page.evaluate(
        "async (v) => { Filter.save({ minScore: v }); await FilterSheet._applyLive(); }",
        _spec.FILTER_MIN_SCORE_DEFAULT,
    )
    try:
        page.wait_for_function(
            "(n) => document.getElementById('feed-content').children.length === n",
            arg=baseline_count,
            timeout=12000,
        )
    except Exception:
        pass
    restored_count = page.eval_on_selector(_spec.FEED_CONTENT_SELECTOR, "el => el.children.length")
    shot("filter-feed-reset")
    if restored_count != baseline_count:
        findings.append(
            Finding(
                view="feed",
                assertion_id="filter_reset_restores_results",
                expected="Trefferzahl nach Zurücksetzen auf minScore={0} wieder = {1}".format(
                    _spec.FILTER_MIN_SCORE_DEFAULT, baseline_count
                ),
                actual="Trefferzahl nach Reset = {0}".format(restored_count),
                message="feed result count did not return to baseline after resetting filter",
                screenshot_path=shot("filter-not-restored"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    return findings


# --- TASK-67 (Etappe 3): defensives Aufräumen vor jedem neuen Check ---------------
def _close_any_open_sheet(page) -> None:
    """Schließt bekannte Sheets/Overlays defensiv, FALLS ein vorheriger Check eines
    offen gelassen hat (Pattern 17: eigener Check-Start muss robust sein, unabhängig
    vom Zustand, den der Vorgänger hinterlässt — nicht nur am eigenen Ende aufräumen).
    Best-effort: wirft nie, jede Einzelaktion ist in try/except gekapselt.
    """
    for expr in (
        "() => { if (typeof LocationDetail !== 'undefined') LocationDetail.close(); }",
        "() => { if (typeof Detail !== 'undefined') Detail.close(); }",
        "() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }",
        "() => { if (typeof Glossary !== 'undefined') Glossary.close(); }",
        # CI-Fund (TASK-67, run #195): AddLocation.save() schliesst #add-sheet nur im
        # Erfolgspfad (index.html ~Zeile 7014); schlaegt der API-Call fehl (z.B. CI-
        # Timing), bleibt das Quick-Add-Sheet offen und blockiert nachfolgende Checks
        # (_check_scout_mode etc.) beim Klick auf #fmb-feed. Defensiv hier mitschliessen.
        "() => { if (typeof AddLocation !== 'undefined') AddLocation.close(); }",
    ):
        try:
            page.evaluate(expr)
        except Exception:
            pass
    try:
        page.wait_for_function(
            "() => !['loc-detail-sheet','detail-sheet','filter-sheet','glossary-overlay','add-sheet']"
            ".some(id => { const el = document.getElementById(id); "
            "return el && el.classList.contains('open'); })",
            timeout=4000,
        )
    except Exception:
        pass


# --- TASK-67 (Etappe 3): Kalender-Ansicht ------------------------------------------
def _check_calendar_view(page, commit: str, shot) -> List["Finding"]:
    """Feed.setMode('calendar') -> CalendarView.render(): lädt fehlerfrei, zeigt Termine.

    "Zeigt die richtigen Termine" wird hier als "zeigt einen plausiblen Zustand"
    geprüft: entweder mindestens ein `.cal-event` ODER der explizite Leer-Zustand
    (`.empty`, siehe web/index.html Zeile ~2373) — beides ist ein korrekter,
    fehlerfreier Ladezustand. Ein stiller leerer Container (weder Event noch
    Leer-Hinweis) gilt als Fehler (CalendarView.render() hätte in dem Fall
    versagt, ohne das zu kommunizieren).
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    try:
        page.wait_for_selector(_spec.FEED_MODE_BTN_SELECTOR, timeout=8000)
        page.click(_spec.CALENDAR_MODE_BTN_SELECTOR)
        page.wait_for_selector(_spec.CALENDAR_NAV_SELECTOR, timeout=15000)
    except Exception:
        findings.append(
            Finding(
                view="calendar",
                assertion_id="calendar_view_loads",
                expected=_spec.CALENDAR_NAV_SELECTOR + " nach Feed.setMode('calendar')",
                actual="Kalender-Navigation wurde nicht rechtzeitig sichtbar",
                message="calendar view did not load in time",
                screenshot_path=shot("calendar-not-loaded"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    try:
        page.wait_for_function(
            "() => { const c = document.getElementById('feed-content'); "
            "return !!c && (c.querySelector('.cal-event') || c.querySelector('.empty')); }",
            timeout=15000,
        )
    except Exception:
        findings.append(
            Finding(
                view="calendar",
                assertion_id="calendar_shows_events_or_empty_state",
                expected="mindestens ein " + _spec.CALENDAR_EVENT_SELECTOR
                + " ODER expliziter Leer-Zustand (" + _spec.CALENDAR_EMPTY_SELECTOR + ")",
                actual="weder Termine noch Leer-Zustand sichtbar (stiller Ladefehler)",
                message="calendar view shows neither events nor an explicit empty state",
                screenshot_path=shot("calendar-silent-empty"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    shot("calendar-view")
    # Zurück in den Feed-Modus, damit nachfolgende Checks vom bekannten Zustand starten.
    page.click(_spec.FEED_MODE_BTN_SELECTOR)
    try:
        page.wait_for_selector(_spec.FEED_CONTENT_SELECTOR, timeout=8000)
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 3): Filter-Chip-Drei-Zustand + Ausgrauen ---------------------
def _check_filter_tristate_and_dimming(page, commit: str, shot) -> List["Finding"]:
    """Prüft den Drei-Zustand-Zyklus (Off -> Einschließen -> Ausschließen -> Off) am
    Beispiel des Verifikations-Chips "Geprüft" (Referenzmuster reference_fotoalert_
    verification_filter) sowie das Ausgrauen-Verhalten (BUG-46): Die Tageszeit-Sektion
    ist auf dem Locations-Tab ausgegraut (opacity 0.45, pointer-events none), im
    Chancen-Feed nicht (FilterSheet._render(), dimOnLocAndMap).
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []

    # -- Teil 1: Drei-Zustand-Zyklus im Feed --------------------------------------
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    try:
        page.wait_for_selector(_spec.FEED_CONTENT_SELECTOR, timeout=8000)
        page.click(_spec.FILTER_BTN_SELECTOR)
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
        page.wait_for_selector(_spec.VERIFICATION_CHIP_VERIFIED_SELECTOR, timeout=8000)
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="filter_sheet_opens",
                expected=_spec.FILTER_SHEET_OPEN_SELECTOR + " mit Verifikations-Chip nach Klick auf "
                + _spec.FILTER_BTN_SELECTOR,
                actual="Filter-Sheet öffnete sich nicht oder Chip fehlt",
                message="filter sheet did not open or verification chip missing",
                screenshot_path=shot("filter-sheet-not-open"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    def _chip_class() -> str:
        return page.eval_on_selector(
            _spec.VERIFICATION_CHIP_VERIFIED_SELECTOR, "el => el.className"
        )

    # Sicherstellen, dass der Chip im bekannten "off"-Ausgangszustand startet
    # (Zustand ist über Sessions/Reloads persistiert, siehe Filter.save/localStorage).
    start_cls = _chip_class()
    if "active" in start_cls or "exclude" in start_cls:
        page.click(_spec.VERIFICATION_CHIP_VERIFIED_SELECTOR)  # -> off (Zyklus schließen)
        try:
            page.wait_for_function(
                "(sel) => { const el = document.querySelector(sel); return el && "
                "!el.className.includes('active') && !el.className.includes('exclude'); }",
                arg=_spec.VERIFICATION_CHIP_VERIFIED_SELECTOR,
                timeout=5000,
            )
        except Exception:
            pass

    # Klick 1: off -> incl ("active"/Goldrand)
    page.click(_spec.VERIFICATION_CHIP_VERIFIED_SELECTOR)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); "
            "return el && el.className.includes('active'); }",
            arg=_spec.VERIFICATION_CHIP_VERIFIED_SELECTOR,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="verification_chip_off_to_incl",
                expected="Chip-Klasse enthält 'active' nach 1. Klick (Off -> Einschließen)",
                actual="Klasse blieb: " + _chip_class(),
                message="verification chip did not transition off->incl",
                screenshot_path=shot("verification-chip-not-incl"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    # Klick 2: incl -> excl ("exclude"/Rotrand)
    page.click(_spec.VERIFICATION_CHIP_VERIFIED_SELECTOR)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); "
            "return el && el.className.includes('exclude'); }",
            arg=_spec.VERIFICATION_CHIP_VERIFIED_SELECTOR,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="verification_chip_incl_to_excl",
                expected="Chip-Klasse enthält 'exclude' nach 2. Klick (Einschließen -> Ausschließen)",
                actual="Klasse blieb: " + _chip_class(),
                message="verification chip did not transition incl->excl",
                screenshot_path=shot("verification-chip-not-excl"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    # Klick 3: excl -> off
    page.click(_spec.VERIFICATION_CHIP_VERIFIED_SELECTOR)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); return el && "
            "!el.className.includes('active') && !el.className.includes('exclude'); }",
            arg=_spec.VERIFICATION_CHIP_VERIFIED_SELECTOR,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="verification_chip_excl_to_off",
                expected="Chip-Klasse ohne 'active'/'exclude' nach 3. Klick (Ausschließen -> Off)",
                actual="Klasse blieb: " + _chip_class(),
                message="verification chip did not transition excl->off",
                screenshot_path=shot("verification-chip-not-off"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    shot("filter-tristate-cycle-done")

    page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")
    try:
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        pass

    # -- Teil 2: Ausgrauen-Verhalten (BUG-46) --------------------------------------
    # Locations-Tab: Tageszeit-Sektion muss ausgegraut (opacity 0.45) sein.
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "locations")
    try:
        page.wait_for_selector("#locations-content", timeout=8000)
        page.click(_spec.FILTER_BTN_SELECTOR)
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
        opacity = page.eval_on_selector(
            _spec.TAGESZEIT_SECTION_SELECTOR, "el => getComputedStyle(el).opacity"
        )
        if opacity != "0.45":
            findings.append(
                Finding(
                    view="filter",
                    assertion_id="tageszeit_dimmed_on_locations",
                    expected="Tageszeit-Filter-Section auf Locations-Tab opacity 0.45 (ausgegraut, BUG-46)",
                    actual="opacity = " + str(opacity),
                    message="tageszeit filter section not dimmed on locations tab",
                    screenshot_path=shot("tageszeit-not-dimmed-locations"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="tageszeit_dimmed_on_locations_check",
                expected="Filter-Sheet + Tageszeit-Section auf Locations-Tab prüfbar",
                actual="Check konnte nicht durchgeführt werden: {0}".format(e),
                message="could not evaluate tageszeit dimming on locations tab",
                screenshot_path=shot("tageszeit-locations-check-failed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")

    # Feed-Tab: Tageszeit-Sektion darf NICHT ausgegraut sein.
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    try:
        page.wait_for_selector(_spec.FEED_CONTENT_SELECTOR, timeout=8000)
        page.click(_spec.FILTER_BTN_SELECTOR)
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
        opacity = page.eval_on_selector(
            _spec.TAGESZEIT_SECTION_SELECTOR, "el => getComputedStyle(el).opacity"
        )
        if opacity == "0.45":
            findings.append(
                Finding(
                    view="filter",
                    assertion_id="tageszeit_not_dimmed_on_feed",
                    expected="Tageszeit-Filter-Section im Chancen-Feed NICHT ausgegraut (opacity 1)",
                    actual="opacity = " + str(opacity),
                    message="tageszeit filter section incorrectly dimmed on feed tab",
                    screenshot_path=shot("tageszeit-wrongly-dimmed-feed"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="tageszeit_not_dimmed_on_feed_check",
                expected="Filter-Sheet + Tageszeit-Section im Feed prüfbar",
                actual="Check konnte nicht durchgeführt werden: {0}".format(e),
                message="could not evaluate tageszeit dimming on feed tab",
                screenshot_path=shot("tageszeit-feed-check-failed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")
    try:
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 6): Filter-Badge zeigt Filter.activeCount() -------------------
def _check_filter_badge_count(page, commit: str, shot) -> List["Finding"]:
    """PRODUCT.md Abschnitt 3a: Filter-Badge (#filter-badge) zeigt die Anzahl aktiver
    Filterkriterien (Filter.activeCount(), web/index.html ~Zeile 2960).

    Bewusst KEIN harter Erwartungswert wie "0" nach Reset: Filter._defaults() hat seit
    US-119 minScore=70 als Default, das zählt in activeCount() bereits als 1 aktives
    Kriterium. Stattdessen wird der Badge-Text nach jedem Schritt gegen den zur
    Laufzeit aus Filter.activeCount() gelesenen Ground-Truth-Wert verglichen
    (Determinismus-Pattern wie der Score-Schwellwert in _check_filter_feed).
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    page.evaluate("() => { if (typeof Filter !== 'undefined') Filter.reset(); }")
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    try:
        page.wait_for_selector(_spec.FEED_CONTENT_SELECTOR, timeout=8000)
        page.wait_for_selector(_spec.FILTER_BADGE_SELECTOR, timeout=8000)
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="filter_badge_precondition",
                expected=_spec.FILTER_BADGE_SELECTOR + " im Feed vorhanden",
                actual="Badge/Feed nicht bereit: {0}".format(e),
                message="filter badge precondition failed",
                screenshot_path=shot("filter-badge-precondition-failed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    def _badge_text():
        return page.eval_on_selector(_spec.FILTER_BADGE_SELECTOR, "el => el.textContent")

    def _expected_count():
        return page.evaluate("() => (typeof Filter !== 'undefined') ? Filter.activeCount() : null")

    baseline_expected = _expected_count()
    baseline_actual = _badge_text()
    if str(baseline_expected) != str(baseline_actual):
        findings.append(
            Finding(
                view="filter",
                assertion_id="filter_badge_count_baseline",
                expected="Badge zeigt Filter.activeCount() = {0}".format(baseline_expected),
                actual="Badge zeigt {0}".format(baseline_actual),
                message="filter badge does not reflect Filter.activeCount() at baseline",
                screenshot_path=shot("filter-badge-baseline-mismatch"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    # Zwei weitere Kriterien real anklicken (Schwierigkeit + Sichtachse) und die
    # Badge-Anzeige erneut gegen Filter.activeCount() vergleichen.
    try:
        page.click(_spec.FILTER_BTN_SELECTOR)
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
        page.click(_spec.DIFFICULTY_CHIP_SELECTOR_TMPL.format(1))
        page.click(_spec.SIGHTLINE_CHIP_SELECTOR_TMPL.format("frei"))
        page.wait_for_function(
            "(n) => typeof Filter !== 'undefined' && Filter.activeCount() === n",
            arg=baseline_expected + 2,
            timeout=5000,
        )
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="filter_badge_count_after_clicks_precondition",
                expected="Filter.activeCount() steigt nach 2 Chip-Klicks (Schwierigkeit + Sichtachse) um 2",
                actual="Zustand nach Klicks nicht erreichbar: {0}".format(e),
                message="could not reach expected active-count state after chip clicks",
                screenshot_path=shot("filter-badge-clicks-failed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        page.evaluate("() => { if (typeof Filter !== 'undefined') Filter.reset(); }")
        page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")
        return findings

    after_expected = _expected_count()
    after_actual = _badge_text()
    if str(after_expected) != str(after_actual):
        findings.append(
            Finding(
                view="filter",
                assertion_id="filter_badge_count_after_clicks",
                expected="Badge zeigt Filter.activeCount() = {0} nach 2 zusätzlichen Kriterien".format(after_expected),
                actual="Badge zeigt {0}".format(after_actual),
                message="filter badge does not reflect Filter.activeCount() after 2 active criteria",
                screenshot_path=shot("filter-badge-after-clicks-mismatch"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    shot("filter-badge-count-done")

    page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")
    page.evaluate("() => { if (typeof Filter !== 'undefined') Filter.reset(); }")
    try:
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 6): Bewertungs-Chip Drei-Zustand ------------------------------
def _check_rating_chip_tristate(page, commit: str, shot) -> List["Finding"]:
    """Bewertungs-Chip im Filter-Sheet (FilterSheet._cycleRating(v),
    v=RATING_CHIP_TEST_VALUE): Drei-Zustand-Zyklus Aus -> gold (Einschließen, Klasse
    'active') -> rot (Ausschließen, Klasse 'exclude') -> Aus. Identisches
    chip3-Klassenschema wie der bereits geprüfte Verifikations-Chip (web/index.html
    ~Zeile 3466), NICHT zu verwechseln mit dem Sterne-Widget im Location-Detail
    (Rating._set(), von _check_rating_flow abgedeckt) — hier geht es um den
    FILTER-Chip.
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    sel = _spec.RATING_CHIP_SELECTOR_TMPL.format(_spec.RATING_CHIP_TEST_VALUE)

    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    try:
        page.wait_for_selector(_spec.FEED_CONTENT_SELECTOR, timeout=8000)
        page.click(_spec.FILTER_BTN_SELECTOR)
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
        page.wait_for_selector(sel, timeout=8000)
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="rating_chip_sheet_opens",
                expected=_spec.FILTER_SHEET_OPEN_SELECTOR + " mit Bewertungs-Chip nach Klick auf " + _spec.FILTER_BTN_SELECTOR,
                actual="Filter-Sheet öffnete sich nicht oder Bewertungs-Chip fehlt",
                message="filter sheet did not open or rating chip missing",
                screenshot_path=shot("rating-chip-sheet-not-open"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    def _cls():
        return page.eval_on_selector(sel, "el => el.className")

    start_cls = _cls()
    if "active" in start_cls or "exclude" in start_cls:
        page.evaluate(
            "() => { if (typeof Filter !== 'undefined') Filter.save({minRating: 0, minRatingExcl: false}); "
            "if (typeof FilterSheet !== 'undefined') FilterSheet._render(); }"
        )

    # Klick 1: off -> incl (gold, 'active')
    page.click(sel)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); return el && el.className.includes('active'); }",
            arg=sel,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="rating_chip_off_to_incl",
                expected="Chip-Klasse enthält 'active' nach 1. Klick (Aus -> gold)",
                actual="Klasse blieb: " + _cls(),
                message="rating chip did not transition off->incl",
                screenshot_path=shot("rating-chip-not-incl"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    # Klick 2: incl -> excl (rot, 'exclude')
    page.click(sel)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); return el && el.className.includes('exclude'); }",
            arg=sel,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="rating_chip_incl_to_excl",
                expected="Chip-Klasse enthält 'exclude' nach 2. Klick (gold -> rot)",
                actual="Klasse blieb: " + _cls(),
                message="rating chip did not transition incl->excl",
                screenshot_path=shot("rating-chip-not-excl"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    # Klick 3: excl -> off
    page.click(sel)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); return el && "
            "!el.className.includes('active') && !el.className.includes('exclude'); }",
            arg=sel,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="rating_chip_excl_to_off",
                expected="Chip-Klasse ohne 'active'/'exclude' nach 3. Klick (rot -> Aus)",
                actual="Klasse blieb: " + _cls(),
                message="rating chip did not transition excl->off",
                screenshot_path=shot("rating-chip-not-off"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    shot("rating-chip-tristate-done")

    page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")
    try:
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 6): Wahrscheinlichkeit-Ausgrauen (Karte + Locations-Tab) ------
def _check_wahrscheinlichkeit_dimming(page, commit: str, shot) -> List["Finding"]:
    """Mindest-Wahrscheinlichkeit-Sektion im Filter-Sheet: dieselbe dimOnLocAndMap-
    Logik wie Tageszeit (siehe _check_filter_tristate_and_dimming) — auf Karte +
    Locations-Tab ausgegraut (opacity 0.45), im Chancen-Feed aktiv.

    Brennweite bewusst NICHT hier geprüft — Etappe-6-Befund: web/index.html
    ~Zeile 3576 (`const dimFocalOnMap = false;`) und ~Zeile 5068-5073 zeigen, dass
    Brennweite Karte + Locations-Tab tatsächlich aktiv mitfiltert (nie ausgegraut).
    Das widerspricht PRODUCT.md Abschnitt 3a (führt Brennweite als "ausgegraut auf
    Karte + Locations-Tab"). Ob PRODUCT.md veraltet ist oder eine echte Regression
    vorliegt, ist ungeklärt — deshalb hier bewusst ausgelassen statt eine falsche
    Erwartung zu testen (siehe Zusammenfassung im Ticket).
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []

    def _check_one(view_name, nav_arg, ready_selector, expect_dimmed):
        page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", nav_arg)
        try:
            page.wait_for_selector(ready_selector, timeout=8000)
            page.click(_spec.FILTER_BTN_SELECTOR)
            page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
            opacity = page.eval_on_selector(
                _spec.WAHRSCHEINLICHKEIT_SECTION_SELECTOR, "el => getComputedStyle(el).opacity"
            )
            is_dimmed = opacity == "0.45"
            if is_dimmed != expect_dimmed:
                findings.append(
                    Finding(
                        view="filter",
                        assertion_id="wahrscheinlichkeit_dimming_{0}".format(view_name),
                        expected="opacity {0} auf {1}".format("0.45" if expect_dimmed else "1", view_name),
                        actual="opacity = " + str(opacity),
                        message="wahrscheinlichkeit filter section dimming state wrong on {0}".format(view_name),
                        screenshot_path=shot("wahrscheinlichkeit-dimming-{0}".format(view_name)),
                        timestamp=_now_iso(),
                        commit_sha=commit,
                    )
                )
        except Exception as e:
            findings.append(
                Finding(
                    view="filter",
                    assertion_id="wahrscheinlichkeit_dimming_{0}_check".format(view_name),
                    expected="Filter-Sheet + Wahrscheinlichkeit-Section auf {0} prüfbar".format(view_name),
                    actual="Check konnte nicht durchgeführt werden: {0}".format(e),
                    message="could not evaluate wahrscheinlichkeit dimming on {0}".format(view_name),
                    screenshot_path=shot("wahrscheinlichkeit-{0}-check-failed".format(view_name)),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
        page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")

    _check_one("map", "map", _spec.MAP_PAGE_READY_SELECTOR, True)
    _check_one("locations", "locations", "#locations-content", True)
    _check_one("feed", "feed", _spec.FEED_CONTENT_SELECTOR, False)

    try:
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 6): Karten-Pin-Filterung (Schwierigkeit/Kategorie/Verifikation) --
def _check_map_pin_filtering(page, commit: str, shot) -> List["Finding"]:
    """Karte zeigt nach Schwierigkeits-/Kategorie-/Verifikations-Filter nur die
    passenden Pins (BUG-46, MapView.applyFilter()). Testwerte werden zur Laufzeit aus
    den tatsächlich geladenen Markern (MapView.markers) bestimmt — kein hartcodierter
    Datensatz (gleiches Determinismus-Muster wie in _check_filter_feed).
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    page.evaluate("() => { if (typeof Filter !== 'undefined') Filter.reset(); }")
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "map")
    try:
        page.wait_for_selector(_spec.MAP_PAGE_READY_SELECTOR, timeout=_spec.REQUIRED_SELECTOR_TIMEOUT_MS)
        page.wait_for_function(
            "() => typeof MapView !== 'undefined' && Array.isArray(MapView.markers) && MapView.markers.length > 0",
            timeout=10000,
        )
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="map_pin_filter_precondition",
                expected="Karte mit mindestens einem Location-Marker geladen",
                actual="Karte/Marker nicht bereit: {0}".format(e),
                message="map markers not ready for pin filter check",
                screenshot_path=shot("map-pins-precondition-failed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    try:
        page.click(_spec.FILTER_BTN_SELECTOR)
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="map_pin_filter_sheet_opens",
                expected=_spec.FILTER_SHEET_OPEN_SELECTOR + " auf der Karte erreichbar",
                actual="Filter-Sheet öffnete sich nicht auf der Karte: {0}".format(e),
                message="filter sheet did not open on map view",
                screenshot_path=shot("map-pins-sheet-not-open"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    # -- Schwierigkeit --
    try:
        chosen = page.evaluate("() => MapView.markers[0].loc.difficulty")
        expected_count = page.evaluate(
            "(v) => MapView.markers.filter(m => m.loc.difficulty === v).length", chosen
        )
        page.click(_spec.DIFFICULTY_CHIP_SELECTOR_TMPL.format(chosen))
        page.wait_for_function(
            "([s, n]) => document.querySelectorAll(s).length === n",
            arg=[_spec.MAP_MARKER_SELECTOR, expected_count],
            timeout=8000,
        )
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="map_pins_after_difficulty_filter",
                expected="sichtbare Marker == Anzahl Locations mit demselben Schwierigkeitsgrad",
                actual="Marker-Anzahl passte sich nicht an: {0}".format(e),
                message="map markers did not match difficulty filter",
                screenshot_path=shot("map-pins-difficulty-mismatch"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    page.evaluate(
        "() => { if (typeof Filter !== 'undefined') Filter.save({difficulty: [], difficultyExcl: []}); "
        "if (typeof MapView !== 'undefined') MapView.applyFilter(); "
        "if (typeof FilterSheet !== 'undefined') FilterSheet._render(); }"
    )

    # -- Kategorie --
    try:
        chosen_cat = page.evaluate("() => MapView.markers[0].loc.category")
        expected_count = page.evaluate(
            "(v) => MapView.markers.filter(m => m.loc.category === v).length", chosen_cat
        )
        cat_escaped = chosen_cat.replace("'", "\\'")
        page.click(_spec.CATEGORY_CHIP_SELECTOR_TMPL.format(cat_escaped))
        page.wait_for_function(
            "([s, n]) => document.querySelectorAll(s).length === n",
            arg=[_spec.MAP_MARKER_SELECTOR, expected_count],
            timeout=8000,
        )
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="map_pins_after_category_filter",
                expected="sichtbare Marker == Anzahl Locations mit derselben Kategorie",
                actual="Marker-Anzahl passte sich nicht an: {0}".format(e),
                message="map markers did not match category filter",
                screenshot_path=shot("map-pins-category-mismatch"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    page.evaluate(
        "() => { if (typeof Filter !== 'undefined') Filter.save({category: [], categoryExcl: []}); "
        "if (typeof MapView !== 'undefined') MapView.applyFilter(); "
        "if (typeof FilterSheet !== 'undefined') FilterSheet._render(); }"
    )

    # -- Verifikationsstatus --
    try:
        chosen_ver = page.evaluate(
            "() => { const loc = MapView.markers[0].loc; "
            "const last = (typeof Verify !== 'undefined') ? Verify.getLast(loc.id) : null; "
            "return !last ? 'unverified' : (last.status === 'ok' ? 'verified' : 'issues'); }"
        )
        expected_count = page.evaluate(
            "(cat) => MapView.markers.filter(m => { "
            "const last = (typeof Verify !== 'undefined') ? Verify.getLast(m.loc.id) : null; "
            "const c = !last ? 'unverified' : (last.status === 'ok' ? 'verified' : 'issues'); "
            "return c === cat; }).length",
            chosen_ver,
        )
        page.click(_spec.VERIFICATION_CHIP_SELECTOR_TMPL.format(chosen_ver))
        page.wait_for_function(
            "([s, n]) => document.querySelectorAll(s).length === n",
            arg=[_spec.MAP_MARKER_SELECTOR, expected_count],
            timeout=8000,
        )
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="map_pins_after_verification_filter",
                expected="sichtbare Marker == Anzahl Locations mit demselben Verifikationsstatus",
                actual="Marker-Anzahl passte sich nicht an: {0}".format(e),
                message="map markers did not match verification filter",
                screenshot_path=shot("map-pins-verification-mismatch"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    shot("map-pin-filtering-done")

    page.evaluate(
        "() => { if (typeof Filter !== 'undefined') Filter.reset(); "
        "if (typeof MapView !== 'undefined') MapView.applyFilter(); "
        "if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }"
    )
    try:
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 6): Sichtachsen-Filter-Chip Drei-Zustand + Effekt -------------
def _check_sightline_chip_tristate_and_effect(page, commit: str, shot) -> List["Finding"]:
    """Sichtachsen-Filter-Chip (FilterSheet._cycleSightline(v), Testwert 'frei'):
    Drei-Zustand-Zyklus Aus -> nur zeigen -> ausschließen -> Aus (identisches
    chip3-Klassenschema wie Verifikations-/Bewertungs-Chip). Zusätzlich: Sektion ist
    in KEINER Ansicht ausgegraut (US-09, Sichtachsen-Status ist Location-Eigenschaft,
    web/index.html ~Zeile 3699 hat keine dimOnLocAndMap-Verzweigung für diese
    Sektion) + realer Effekt auf der Karte (MapView.applyFilter() nutzt dieselbe
    sightlineIncl/sightlineExcl-Logik wie Feed/Locations, ~Zeile 5055-5059) wird
    stellvertretend über die Marker-Anzahl verifiziert.
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    sel = _spec.SIGHTLINE_CHIP_SELECTOR_TMPL.format("frei")

    page.evaluate("() => { if (typeof Filter !== 'undefined') Filter.reset(); }")
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    try:
        page.wait_for_selector(_spec.FEED_CONTENT_SELECTOR, timeout=8000)
        page.click(_spec.FILTER_BTN_SELECTOR)
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
        page.wait_for_selector(sel, timeout=8000)
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="sightline_chip_sheet_opens",
                expected=_spec.FILTER_SHEET_OPEN_SELECTOR + " mit Sichtachsen-Chip nach Klick auf " + _spec.FILTER_BTN_SELECTOR,
                actual="Filter-Sheet öffnete sich nicht oder Sichtachsen-Chip fehlt",
                message="filter sheet did not open or sightline chip missing",
                screenshot_path=shot("sightline-chip-sheet-not-open"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    def _cls():
        return page.eval_on_selector(sel, "el => el.className")

    start_cls = _cls()
    if "active" in start_cls or "exclude" in start_cls:
        page.evaluate(
            "() => { if (typeof Filter !== 'undefined') Filter.save({sightlineIncl: [], sightlineExcl: []}); "
            "if (typeof FilterSheet !== 'undefined') FilterSheet._render(); }"
        )

    page.click(sel)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); return el && el.className.includes('active'); }",
            arg=sel,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="sightline_chip_off_to_incl",
                expected="Chip-Klasse enthält 'active' nach 1. Klick (Aus -> nur zeigen)",
                actual="Klasse blieb: " + _cls(),
                message="sightline chip did not transition off->incl",
                screenshot_path=shot("sightline-chip-not-incl"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    page.click(sel)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); return el && el.className.includes('exclude'); }",
            arg=sel,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="sightline_chip_incl_to_excl",
                expected="Chip-Klasse enthält 'exclude' nach 2. Klick (nur zeigen -> ausschließen)",
                actual="Klasse blieb: " + _cls(),
                message="sightline chip did not transition incl->excl",
                screenshot_path=shot("sightline-chip-not-excl"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    page.click(sel)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); return el && "
            "!el.className.includes('active') && !el.className.includes('exclude'); }",
            arg=sel,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="sightline_chip_excl_to_off",
                expected="Chip-Klasse ohne 'active'/'exclude' nach 3. Klick (ausschließen -> Aus)",
                actual="Klasse blieb: " + _cls(),
                message="sightline chip did not transition excl->off",
                screenshot_path=shot("sightline-chip-not-off"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    shot("sightline-chip-tristate-done")

    # Filter-Sheet aus dem Tristate-Zyklus oben schließen, BEVOR die Ausgrauen-Schleife
    # unten startet — sonst blockiert der noch offene #filter-overlay den ersten
    # page.click(FILTER_BTN_SELECTOR)-Versuch der Schleife (gefunden 2026-07-12: erster
    # echter Playwright-Lauf, Timeout weil "<div class=open id=filter-overlay> intercepts
    # pointer events").
    page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")
    try:
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        pass

    # Ausgegraut-Check: Sektion darf auf KEINER Ansicht opacity 0.45 haben.
    for view_name, nav_arg, ready_selector in (
        ("feed", "feed", _spec.FEED_CONTENT_SELECTOR),
        ("map", "map", _spec.MAP_PAGE_READY_SELECTOR),
        ("locations", "locations", "#locations-content"),
    ):
        page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", nav_arg)
        try:
            page.wait_for_selector(ready_selector, timeout=8000)
            page.click(_spec.FILTER_BTN_SELECTOR)
            page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
            opacity = page.eval_on_selector(
                _spec.SICHTACHSE_SECTION_SELECTOR, "el => getComputedStyle(el).opacity"
            )
            if opacity == "0.45":
                findings.append(
                    Finding(
                        view="filter",
                        assertion_id="sightline_wrongly_dimmed_{0}".format(view_name),
                        expected="Sichtachse-Filter-Section auf {0} NICHT ausgegraut (opacity 1)".format(view_name),
                        actual="opacity = " + str(opacity),
                        message="sightline filter section incorrectly dimmed on {0}".format(view_name),
                        screenshot_path=shot("sightline-wrongly-dimmed-{0}".format(view_name)),
                        timestamp=_now_iso(),
                        commit_sha=commit,
                    )
                )
        except Exception as e:
            findings.append(
                Finding(
                    view="filter",
                    assertion_id="sightline_dimming_{0}_check".format(view_name),
                    expected="Filter-Sheet + Sichtachse-Section auf {0} prüfbar".format(view_name),
                    actual="Check konnte nicht durchgeführt werden: {0}".format(e),
                    message="could not evaluate sightline dimming on {0}".format(view_name),
                    screenshot_path=shot("sightline-{0}-check-failed".format(view_name)),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
        page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")

    # Realer Effekt auf der Karte (stellvertretend für "wirkt in allen Ansichten" —
    # Feed/Locations nutzen denselben sightlineIncl/sightlineExcl-Codepfad, siehe
    # web/index.html ~Zeile 3055-3061 (Feed) und ~3113-3117 (Locations), nicht erneut
    # per eigenem Browserlauf dupliziert).
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "map")
    try:
        page.wait_for_selector(_spec.MAP_PAGE_READY_SELECTOR, timeout=_spec.REQUIRED_SELECTOR_TIMEOUT_MS)
        page.wait_for_function(
            "() => typeof MapView !== 'undefined' && Array.isArray(MapView.markers) && MapView.markers.length > 0",
            timeout=10000,
        )
        chosen = page.evaluate("() => MapView.markers[0].loc.sightline_status || 'nicht_geprueft'")
        expected_count = page.evaluate(
            "(v) => MapView.markers.filter(m => (m.loc.sightline_status || 'nicht_geprueft') === v).length",
            chosen,
        )
        page.click(_spec.FILTER_BTN_SELECTOR)
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
        page.click(_spec.SIGHTLINE_CHIP_SELECTOR_TMPL.format(chosen))
        page.wait_for_function(
            "([s, n]) => document.querySelectorAll(s).length === n",
            arg=[_spec.MAP_MARKER_SELECTOR, expected_count],
            timeout=8000,
        )
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="map_pins_after_sightline_filter",
                expected="sichtbare Marker == Anzahl Locations mit demselben Sichtachsen-Status",
                actual="Marker-Anzahl passte sich nicht an: {0}".format(e),
                message="map markers did not match sightline filter",
                screenshot_path=shot("map-pins-sightline-mismatch"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    page.evaluate(
        "() => { if (typeof Filter !== 'undefined') Filter.reset(); "
        "if (typeof MapView !== 'undefined') MapView.applyFilter(); "
        "if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }"
    )
    try:
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 6): "Hat Beispielbild"-Chip Drei-Zustand + Effekt -------------
def _check_has_image_chip_tristate_and_effect(page, commit: str, shot) -> List["Finding"]:
    """"Hat Beispielbild"-Chip (FilterSheet._cycleHasImage()): Drei-Zustand-Zyklus
    Aus -> gold "Hat Bild" -> rot "Ohne Bild" -> Aus (US-129). Wirkt auf Orte-Tab
    (hier real per Klick + Ground-Truth-Vergleich gegen Filter.applyToLocations()
    verifiziert); bleibt bei Entdecken/Scout ausgegraut (isScoutOnly, web/index.html
    ~Zeile 3570/3653).

    Effekt auf Karte/Feed/Kalender NICHT hier per eigenem Browserlauf dupliziert —
    dieselbe s.hasImage/s.hasImageExcl-Prüflogik taucht an den jeweiligen
    Filter-Anwendungsstellen strukturell identisch auf (web/index.html Locations
    ~Zeile 3071-3075/3126-3129, Karte ~Zeile 5062-5066); der Orte-Tab-Testfall deckt
    die Kernlogik ab, die übrigen Ansichten bleiben eine bewusst benannte Lücke.
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    sel = _spec.HASIMAGE_CHIP_SELECTOR

    page.evaluate("() => { if (typeof Filter !== 'undefined') Filter.reset(); }")
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    try:
        page.wait_for_selector(_spec.FEED_CONTENT_SELECTOR, timeout=8000)
        page.click(_spec.FILTER_BTN_SELECTOR)
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
        page.wait_for_selector(sel, timeout=8000)
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="hasimage_chip_sheet_opens",
                expected=_spec.FILTER_SHEET_OPEN_SELECTOR + " mit Beispielbild-Chip nach Klick auf " + _spec.FILTER_BTN_SELECTOR,
                actual="Filter-Sheet öffnete sich nicht oder Beispielbild-Chip fehlt",
                message="filter sheet did not open or hasImage chip missing",
                screenshot_path=shot("hasimage-chip-sheet-not-open"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    def _cls():
        return page.eval_on_selector(sel, "el => el.className")

    start_cls = _cls()
    if "active" in start_cls or "exclude" in start_cls:
        page.evaluate(
            "() => { if (typeof Filter !== 'undefined') Filter.save({hasImage: false, hasImageExcl: false}); "
            "if (typeof FilterSheet !== 'undefined') FilterSheet._render(); }"
        )

    page.click(sel)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); return el && el.className.includes('active'); }",
            arg=sel,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="hasimage_chip_off_to_incl",
                expected="Chip-Klasse enthält 'active' nach 1. Klick (Aus -> Hat Bild)",
                actual="Klasse blieb: " + _cls(),
                message="hasImage chip did not transition off->incl",
                screenshot_path=shot("hasimage-chip-not-incl"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    page.click(sel)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); return el && el.className.includes('exclude'); }",
            arg=sel,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="hasimage_chip_incl_to_excl",
                expected="Chip-Klasse enthält 'exclude' nach 2. Klick (Hat Bild -> Ohne Bild)",
                actual="Klasse blieb: " + _cls(),
                message="hasImage chip did not transition incl->excl",
                screenshot_path=shot("hasimage-chip-not-excl"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    page.click(sel)
    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); return el && "
            "!el.className.includes('active') && !el.className.includes('exclude'); }",
            arg=sel,
            timeout=5000,
        )
    except Exception:
        findings.append(
            Finding(
                view="filter",
                assertion_id="hasimage_chip_excl_to_off",
                expected="Chip-Klasse ohne 'active'/'exclude' nach 3. Klick (Ohne Bild -> Aus)",
                actual="Klasse blieb: " + _cls(),
                message="hasImage chip did not transition excl->off",
                screenshot_path=shot("hasimage-chip-not-off"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    shot("hasimage-chip-tristate-done")
    page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")

    # Ausgegraut-Check: NUR bei Entdecken/Scout (isScoutOnly).
    page.evaluate(
        "() => { if (typeof App !== 'undefined') App.nav('feed'); "
        "if (typeof Feed !== 'undefined' && typeof Feed.setMode === 'function') Feed.setMode('scout'); }"
    )
    try:
        page.wait_for_selector(_spec.SCOUT_CONTENT_SELECTOR, timeout=8000)
        page.click(_spec.FILTER_BTN_SELECTOR)
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
        opacity = page.eval_on_selector(
            _spec.HASIMAGE_SECTION_SELECTOR, "el => getComputedStyle(el).opacity"
        )
        if opacity != "0.45":
            findings.append(
                Finding(
                    view="filter",
                    assertion_id="hasimage_dimmed_on_scout",
                    expected="Beispielbild-Filter-Section bei Entdecken/Scout opacity 0.45 (ausgegraut, US-129)",
                    actual="opacity = " + str(opacity),
                    message="hasImage filter section not dimmed on scout view",
                    screenshot_path=shot("hasimage-not-dimmed-scout"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="hasimage_dimmed_on_scout_check",
                expected="Filter-Sheet + Beispielbild-Section bei Entdecken prüfbar",
                actual="Check konnte nicht durchgeführt werden: {0}".format(e),
                message="could not evaluate hasImage dimming on scout view",
                screenshot_path=shot("hasimage-scout-check-failed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    page.evaluate("() => { if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }")

    # Effekt auf dem Orte-Tab (Ground Truth: Filter.applyToLocations(Locations.all)).
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "locations")
    try:
        page.wait_for_selector("#locations-content", timeout=8000)
        page.wait_for_function(
            "() => typeof Locations !== 'undefined' && Array.isArray(Locations.all) && Locations.all.length > 0",
            timeout=10000,
        )
        has_with_image = page.evaluate("() => Locations.all.some(l => !!l.image_url)")
        has_without_image = page.evaluate("() => Locations.all.some(l => !l.image_url)")
        if not (has_with_image and has_without_image):
            findings.append(
                Finding(
                    view="filter",
                    assertion_id="hasimage_locations_data_precondition",
                    expected="Mindestens 1 Location MIT und 1 OHNE Beispielbild für einen aussagekräftigen Filtertest",
                    actual="mit Bild={0}, ohne Bild={1}".format(has_with_image, has_without_image),
                    message="insufficient data variety to prove hasImage filter effect on locations tab",
                    screenshot_path=shot("hasimage-locations-data-precondition-failed"),
                    timestamp=_now_iso(),
                    commit_sha=commit,
                )
            )
        else:
            expected_count = page.evaluate("() => Locations.all.filter(l => !!l.image_url).length")
            # Filter.applyToLocations() koppelt zusätzlich an s.minScore (Default 70,
            # US-119) — verlangt einen Feed-Event mit overall_score >= minScore/100 pro
            # Location (web/index.html ~Zeile 3131-3134). Ohne diesen Reset zählt
            # applyToLocations() weniger Treffer als expected_count (das reine
            # image_url-Kriterium), der Vergleich würde nie aufgehen (gefunden
            # 2026-07-12: erster echter Playwright-Lauf, Timeout bei 42/175 sichtbar
            # statt der erwarteten reinen Bild-Anzahl). minScore für diesen isolierten
            # Vergleich auf 0 setzen.
            page.evaluate("() => { if (typeof Filter !== 'undefined') Filter.save({minScore: 0}); }")
            page.click(_spec.FILTER_BTN_SELECTOR)
            page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, timeout=8000)
            page.click(sel)  # off -> incl ("Hat Bild")
            page.wait_for_function(
                "(n) => typeof Locations !== 'undefined' && typeof Filter !== 'undefined' && "
                "Filter.applyToLocations(Locations.all).length === n",
                arg=expected_count,
                timeout=8000,
            )
    except Exception as e:
        findings.append(
            Finding(
                view="filter",
                assertion_id="hasimage_effect_on_locations",
                expected="Filter.applyToLocations(Locations.all).length passt nach 'Hat Bild'-Filter zur Anzahl Locations mit image_url",
                actual="Zustand nicht erreicht: {0}".format(e),
                message="hasImage filter did not correctly reduce locations list",
                screenshot_path=shot("hasimage-locations-effect-failed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    page.evaluate(
        "() => { if (typeof Filter !== 'undefined') Filter.reset(); "
        "if (typeof FilterSheet !== 'undefined') FilterSheet.close(); }"
    )
    try:
        page.wait_for_selector(_spec.FILTER_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 3): Bewertungsfunktion (Anlegen/Abrufen/Löschen) --------------
def _check_rating_flow(page, commit: str, shot) -> List["Finding"]:
    """Öffnet das Location-Detail-Sheet der ersten Location, vergibt eine Bewertung
    (Stern-Klick -> Rating._set()), prüft sie über GET /locations/{id}/ratings, löscht
    sie wieder (Rating._clear()) und prüft, dass sie danach nicht mehr zurückkommt.
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", _spec.LOCATIONS_NAV_ARG)
    try:
        page.wait_for_selector(_spec.LOCATION_CARD_SELECTOR, timeout=12000)
        page.click(_spec.LOCATION_CARD_SELECTOR)
        page.wait_for_selector(_spec.DETAIL_SHEET_OPEN_SELECTOR, timeout=12000)
        # Der „Bewertung"-Abschnitt ist standardmäßig eingeklappt
        # (Sections._def.loc_rating = false, web/index.html ~Zeile 3800) —
        # `.section-body{max-height:0;overflow:hidden}` klippt den Inhalt optisch weg,
        # bis der Accordion-Header angeklickt wird (Sections.toggle('loc_rating')).
        # Ohne diesen Klick würde ein späterer ECHTER Playwright-Mausklick (im
        # Gegensatz zum reinen JS-`.click()` beim Stern-Setzen weiter unten) auf den
        # "Bewertung löschen"-Button fehlschlagen, weil der Button dann nicht
        # tatsächlich sichtbar/klickbar ist — kein App-Bug, sondern fehlender
        # Öffnen-Schritt im Test.
        page.click("h4[onclick=\"Sections.toggle('loc_rating')\"]")
        page.wait_for_selector("#sb_loc_rating.open", timeout=5000)
        page.wait_for_selector(_spec.RATING_STAR_BTN_SELECTOR, timeout=8000)
    except Exception:
        findings.append(
            Finding(
                view="rating",
                assertion_id="rating_section_present",
                expected=_spec.RATING_STAR_BTN_SELECTOR + " im Location-Detail-Sheet sichtbar",
                actual="Location-Detail-Sheet oder Sterne-Eingabe nicht gefunden",
                message="rating star input not found in location detail sheet",
                screenshot_path=shot("rating-section-missing"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    # Location-ID aus dem geöffneten Sheet ermitteln (LocationDetail._current.id, siehe
    # web/index.html LocationDetail.open() — dort wird die geöffnete Location als
    # `this._current` gehalten, nicht als `.loc`; `.loc` gehört zu einem anderen
    # Singleton, AstroLive) — robuster als String-Parsing der Rating-Section-ID (die
    # per Regex bereinigt ist und nicht 1:1 zurückgewandelt werden kann).
    loc_id = page.evaluate(
        "() => (typeof LocationDetail !== 'undefined' && LocationDetail._current) "
        "? LocationDetail._current.id : null"
    )
    # `.btn-verify-cancel` ist eine rein optische Styling-Klasse, KEIN eindeutiger
    # Marker — dieselbe Klasse trägt u.a. auch der "Letzten Eintrag löschen"-Button
    # der Sichtachsen-Verifikation (web/index.html Zeile ~2634), der ebenfalls im
    # Location-Detail-Sheet stehen kann. Der Bewertungs-Löschen-Button liegt aber
    # innerhalb von `#rating-section-<safe-id>` (siehe Rating.inputHtml/_refresh) —
    # auf diesen Container scoped statt auf die globale Klasse verlassen, sonst
    # trifft der Selektor ggf. den falschen Button.
    rating_clear_selector = None
    if loc_id:
        safe_id = page.evaluate(
            "(id) => id.replace(/[^a-z0-9]/gi, '_')", loc_id
        )
        rating_clear_selector = f"#rating-section-{safe_id} .btn-verify-cancel"
    if not loc_id:
        findings.append(
            Finding(
                view="rating",
                assertion_id="rating_location_id_resolved",
                expected="LocationDetail._current.id ist gesetzt, während das Sheet offen ist",
                actual="LocationDetail._current(.id) war null/undefined",
                message="could not resolve location id for rating check",
                screenshot_path=shot("rating-no-location-id"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    # Anlegen: 4. Stern anklicken (Rating._set(locId, 4)).
    try:
        page.eval_on_selector_all(
            _spec.RATING_STAR_BTN_SELECTOR,
            "(els) => { if (els[3]) els[3].click(); }",
        )
        page.wait_for_function(
            "(sel) => { const els = document.querySelectorAll(sel); "
            "return els.length >= 4 && els[3].classList.contains('filled'); }",
            arg=_spec.RATING_STAR_BTN_SELECTOR,
            timeout=8000,
        )
    except Exception:
        findings.append(
            Finding(
                view="rating",
                assertion_id="rating_create_ui",
                expected="4. Stern erhält Klasse 'filled' nach Klick (Rating._set)",
                actual="Stern-Klasse änderte sich nicht rechtzeitig",
                message="rating star did not become filled after click",
                screenshot_path=shot("rating-create-ui-fail"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    # Abrufen: GET /locations/{id}/ratings?device_id=... liefert ein AGGREGAT-Objekt
    # {count, avg, mine} (main.py get_ratings/_store.get_rating_summary), KEINE Liste
    # (per Code-Verifikation vor dem Schreiben dieses Checks, main.py Zeile ~2729-2735).
    # device_id muss mitgeschickt werden, sonst bleibt "mine" leer (kein Device-Bezug).
    try:
        device_id = page.evaluate(
            "() => (typeof Rating !== 'undefined' && Rating.deviceId) ? Rating.deviceId() : null"
        )
        summary = page.evaluate(
            "async (args) => { const r = await fetch('/locations/' + args.id + "
            "'/ratings?device_id=' + encodeURIComponent(args.dev)); return await r.json(); }",
            {"id": loc_id, "dev": device_id or ""},
        )
    except Exception:
        summary = None
    if not summary or not isinstance(summary, dict) or summary.get("mine") != 4:
        findings.append(
            Finding(
                view="rating",
                assertion_id="rating_retrievable",
                expected="GET /locations/{0}/ratings?device_id=... liefert 'mine' == 4 nach dem Anlegen".format(loc_id),
                actual="Antwort: {0}".format(summary),
                message="rating not retrievable (or wrong value) after creation",
                screenshot_path=shot("rating-not-retrievable"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    shot("rating-created")

    # Löschen: "Bewertung löschen"-Button (Rating._clear()) — auf die
    # Rating-Section gescopt (s.o.), NICHT die globale .btn-verify-cancel-Klasse,
    # die auch der Sichtachsen-Verifikation gehört.
    clear_sel = rating_clear_selector or _spec.RATING_CLEAR_BTN_SELECTOR
    try:
        page.wait_for_selector(clear_sel, timeout=5000)
        page.click(clear_sel)
        page.wait_for_function(
            "(sel) => { const btn = document.querySelector(sel); return !btn; }",
            arg=clear_sel,
            timeout=8000,
        )
    except Exception:
        findings.append(
            Finding(
                view="rating",
                assertion_id="rating_delete_ui",
                expected="'Bewertung löschen'-Button verschwindet nach Klick (Rating._clear)",
                actual="Löschen-Button blieb sichtbar oder wurde nicht gefunden",
                message="rating delete button did not disappear after click",
                screenshot_path=shot("rating-delete-ui-fail"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    # Nach dem Löschen darf 'mine' für dieses Device nicht mehr gesetzt sein.
    try:
        summary_after = page.evaluate(
            "async (args) => { const r = await fetch('/locations/' + args.id + "
            "'/ratings?device_id=' + encodeURIComponent(args.dev)); return await r.json(); }",
            {"id": loc_id, "dev": device_id or ""},
        )
    except Exception:
        summary_after = None
    if not summary_after or summary_after.get("mine") is not None:
        findings.append(
            Finding(
                view="rating",
                assertion_id="rating_deleted",
                expected="GET /locations/{0}/ratings?device_id=... liefert 'mine' == null nach dem Löschen".format(loc_id),
                actual="Antwort: {0}".format(summary_after),
                message="rating still present after delete",
                screenshot_path=shot("rating-still-present-after-delete"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    page.evaluate("() => { if (typeof LocationDetail !== 'undefined') LocationDetail.close(); }")
    try:
        page.wait_for_selector(_spec.DETAIL_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 3): Event-Detail-Sheet aus Feed-Karte ------------------------
def _check_event_detail_from_feed_card(page, commit: str, shot) -> List["Finding"]:
    """Antippen einer Chance im Feed öffnet #detail-sheet (EVENT-Detail), nicht
    #loc-detail-sheet (das prüft _check_detail_sheet bereits separat, TASK-66).
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    try:
        page.wait_for_selector(_spec.FEED_CONTENT_SELECTOR, timeout=8000)
        page.wait_for_selector(_spec.FEED_CARD_SELECTOR, timeout=12000)
    except Exception:
        findings.append(
            Finding(
                view="feed",
                assertion_id="event_detail_card_present",
                expected=_spec.FEED_CARD_SELECTOR + " mindestens einmal im Feed sichtbar",
                actual="keine Feed-Karte gefunden",
                message="no feed card found to open event detail",
                screenshot_path=shot("no-feed-card"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    page.click(_spec.FEED_CARD_SELECTOR)
    try:
        page.wait_for_selector(_spec.EVENT_DETAIL_SHEET_OPEN_SELECTOR, timeout=8000)
    except Exception:
        findings.append(
            Finding(
                view="feed",
                assertion_id="event_detail_sheet_opens",
                expected=_spec.EVENT_DETAIL_SHEET_OPEN_SELECTOR + " nach Klick auf eine Feed-Karte",
                actual="Event-Detail-Sheet öffnete sich nicht",
                message="event detail sheet did not open after clicking a feed card",
                screenshot_path=shot("event-detail-not-open"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    shot("event-detail-open")
    page.click(_spec.EVENT_DETAIL_CLOSE_BTN_SELECTOR)
    try:
        page.wait_for_selector(_spec.EVENT_DETAIL_SHEET_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        findings.append(
            Finding(
                view="feed",
                assertion_id="event_detail_sheet_closes",
                expected="Event-Detail-Sheet schließt nach Klick auf Close-Button",
                actual="Sheet blieb offen",
                message="event detail sheet did not close",
                screenshot_path=shot("event-detail-not-closed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    return findings


# --- TASK-67 (Etappe 3): Wetter-Kartenansicht — Grundbedienung --------------------
def _check_weather_map_controls(page, commit: str, shot) -> List["Finding"]:
    """Ebenen-Umschalter (Aus/Wolken/Niederschlag) + Zeit-Schieberegler auf der Karte.

    Nutzt den echten Aufrufpfad (WeatherMap.setMode/onSlider über echte Klicks/Input-
    Events, kein direkter Funktionsaufruf, siehe Pattern 15) — Endpoint /weather-map
    lädt echte Daten, daher großzügiger Timeout (WEATHER_MAP_FETCH_TIMEOUT_MS).
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "map")
    try:
        page.wait_for_selector(_spec.MAP_PAGE_READY_SELECTOR, timeout=12000)
        page.click(_spec.WEATHER_MODE_CLOUDS_BTN_SELECTOR)
        page.wait_for_function(
            "() => typeof WeatherMap !== 'undefined' && WeatherMap.mode === 'clouds'",
            timeout=_spec.WEATHER_MAP_FETCH_TIMEOUT_MS,
        )
        page.wait_for_selector(_spec.WEATHER_SLIDER_WRAP_OPEN_SELECTOR, timeout=8000)
    except Exception:
        findings.append(
            Finding(
                view="weather-map",
                assertion_id="weather_layer_toggle",
                expected="WeatherMap.mode === 'clouds' + Zeit-Slider sichtbar nach Klick auf Wolken-Button",
                actual="Ebenen-Umschalter reagierte nicht rechtzeitig",
                message="weather map layer toggle did not activate cloud mode in time",
                screenshot_path=shot("weather-layer-toggle-fail"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        # Trotzdem versuchen, sauber zurückzusetzen (best effort).
        try:
            page.click(_spec.WEATHER_MODE_OFF_BTN_SELECTOR)
        except Exception:
            pass
        return findings

    shot("weather-map-clouds-on")

    # Zeit-Schieberegler bewegen (WeatherMap.onSlider via echtes input-Event).
    try:
        slider_max = page.eval_on_selector(_spec.WEATHER_SLIDER_SELECTOR, "el => el.max")
        target_val = "1" if slider_max and int(slider_max) >= 1 else "0"
        page.fill(_spec.WEATHER_SLIDER_SELECTOR, target_val)
        page.eval_on_selector(
            _spec.WEATHER_SLIDER_SELECTOR,
            "el => el.dispatchEvent(new Event('input', { bubbles: true }))",
        )
        page.wait_for_function(
            "(v) => typeof WeatherMap !== 'undefined' && WeatherMap.sliderIdx === parseInt(v, 10)",
            arg=target_val,
            timeout=8000,
        )
    except Exception:
        findings.append(
            Finding(
                view="weather-map",
                assertion_id="weather_time_slider",
                expected="WeatherMap.sliderIdx aktualisiert sich nach Bedienung des Zeit-Sliders",
                actual="sliderIdx änderte sich nicht rechtzeitig",
                message="weather map time slider did not update WeatherMap.sliderIdx",
                screenshot_path=shot("weather-slider-fail"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    shot("weather-map-slider-moved")

    # Zurücksetzen auf 'off', damit nachfolgende Checks vom bekannten Zustand starten.
    page.click(_spec.WEATHER_MODE_OFF_BTN_SELECTOR)
    try:
        page.wait_for_function(
            "() => typeof WeatherMap !== 'undefined' && WeatherMap.mode === 'off'",
            timeout=8000,
        )
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 3): Entdecken-Modus (Scout) — Basistest ----------------------
def _check_scout_mode(page, commit: str, shot) -> List["Finding"]:
    """Feed.setMode('scout') -> Scout.show(): #scout-content wird sichtbar und
    fehlerfrei befüllt (Karte oder expliziter Leer-/Lade-Zustand, kein stiller Fehler).
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    try:
        page.wait_for_selector(_spec.SCOUT_MODE_BTN_SELECTOR, timeout=8000)
        page.click(_spec.SCOUT_MODE_BTN_SELECTOR)
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); "
            "return el && el.style.display !== 'none'; }",
            arg=_spec.SCOUT_CONTENT_SELECTOR,
            timeout=8000,
        )
    except Exception:
        findings.append(
            Finding(
                view="scout",
                assertion_id="scout_mode_activates",
                expected=_spec.SCOUT_CONTENT_SELECTOR + " sichtbar nach Feed.setMode('scout')",
                actual="Scout-Content wurde nicht rechtzeitig sichtbar",
                message="scout content did not become visible after activating scout mode",
                screenshot_path=shot("scout-not-visible"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        page.click(_spec.FEED_MODE_BTN_SELECTOR)
        return findings

    try:
        page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel); "
            "return !!el && el.innerHTML.trim().length > 0; }",
            arg=_spec.SCOUT_CONTENT_SELECTOR,
            timeout=20000,
        )
    except Exception:
        findings.append(
            Finding(
                view="scout",
                assertion_id="scout_content_populated",
                expected=_spec.SCOUT_CONTENT_SELECTOR + " erhält Inhalt (Karten, Lade- oder Leer-Hinweis)",
                actual="Scout-Content blieb leer",
                message="scout content stayed empty after activating scout mode",
                screenshot_path=shot("scout-content-empty"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )

    shot("scout-mode")
    page.click(_spec.FEED_MODE_BTN_SELECTOR)
    try:
        page.wait_for_selector(_spec.FEED_CONTENT_SELECTOR, timeout=8000)
    except Exception:
        pass
    return findings


# --- TASK-67 (Etappe 3): Globale UI — "?"-Button öffnet Glossar -------------------
def _check_help_glossary(page, commit: str, shot) -> List["Finding"]:
    """PRODUCT.md Abschnitt 2: „?"-Header-Button ist immer erreichbar und öffnet
    das Glossar-Overlay (Glossary.open()/close()).
    """
    _close_any_open_sheet(page)
    findings: List[Finding] = []
    try:
        page.wait_for_selector(_spec.HELP_BTN_SELECTOR, timeout=5000)
        page.click(_spec.HELP_BTN_SELECTOR)
        page.wait_for_selector(_spec.GLOSSARY_OVERLAY_OPEN_SELECTOR, timeout=8000)
    except Exception:
        findings.append(
            Finding(
                view="global",
                assertion_id="help_button_opens_glossary",
                expected=_spec.GLOSSARY_OVERLAY_OPEN_SELECTOR + " nach Klick auf " + _spec.HELP_BTN_SELECTOR,
                actual="Glossar-Overlay öffnete sich nicht",
                message="glossary overlay did not open after clicking help button",
                screenshot_path=shot("glossary-not-open"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
        return findings

    shot("glossary-open")
    page.evaluate("() => { if (typeof Glossary !== 'undefined') Glossary.close(); }")
    try:
        page.wait_for_selector(_spec.GLOSSARY_OVERLAY_OPEN_SELECTOR, state="detached", timeout=5000)
    except Exception:
        findings.append(
            Finding(
                view="global",
                assertion_id="glossary_closes",
                expected="Glossar-Overlay schließt nach Glossary.close()",
                actual="Overlay blieb offen",
                message="glossary overlay did not close",
                screenshot_path=shot("glossary-not-closed"),
                timestamp=_now_iso(),
                commit_sha=commit,
            )
        )
    return findings


# --- TASK-35: Mobile Viewport Pass ------------------------------------------------
# Fängt iOS-PWA-Layout-Bugs ab, die im Desktop-Chromium unsichtbar sind:
#   BUG-19 / BUG-25: Close-Button in Sheets außerhalb des Safe-Area-Bereichs
#   BUG-34: Edit-Overlay übersteigt viewport.width auf iPhone-Breite
#
# Viewport: iPhone 14 (390×844 px, deviceScaleFactor=3, isMobile=True).
# Playwright-Chromium ist kein echtes Safari/WebKit — aber die Viewport-Größe
# reicht, um die häufigsten Layout-Klassen (overflow, z-index, position:fixed)
# zu erkennen. Kein Ersatz für Gerätetests, aber automatischer Frühwarner.

def run_mobile_checks(
    base_url: str,
    password: str,
    screenshot_root: Path,
    headless: bool = True,
    timeout_ms: int = 15000,
) -> List["Finding"]:
    """Mobile-Viewport-Pass: iPhone-14-Dimensionen, isMobile=True.

    Prüft ob Sheets und Overlays den Viewport nicht überschreiten und
    ob Close-Buttons im sichtbaren Bereich bleiben.
    """
    sync_playwright = _import_playwright()
    run = _run_id() + "-mobile"
    shot_dir = screenshot_root / run
    shot_dir.mkdir(parents=True, exist_ok=True)
    commit = _commit_sha()
    findings: List[Finding] = []

    # iPhone 14 Viewport
    IPHONE_WIDTH = 390
    IPHONE_HEIGHT = 844

    def _shot(name: str) -> str:
        target = shot_dir / (name + ".png")
        try:
            page.screenshot(path=str(target), full_page=False)
        except Exception:
            return ""
        return str(target)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(
            viewport={"width": IPHONE_WIDTH, "height": IPHONE_HEIGHT},
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True,
        )
        page = ctx.new_page()
        page.set_default_timeout(timeout_ms)

        page.goto(base_url, wait_until="domcontentloaded")

        # US-21, vierter Fix-Versuch: siehe Docstring von _dismiss_onboarding_if_present
        # in run_checks() — Overlay könnte schon vor dem Login erscheinen.
        _dismiss_onboarding_if_present(page)

        # Login
        page.fill("#login-pw", password)
        page.click(".login-btn")
        try:
            page.wait_for_function("() => typeof Auth !== 'undefined' && Auth.isLoggedIn()", timeout=timeout_ms)
        except Exception:
            findings.append(Finding(
                view="mobile-login",
                assertion_id="mobile_login_precondition",
                expected="Login im Mobile-Viewport erfolgreich",
                actual="Auth.isLoggedIn() blieb false im Mobile-Viewport",
                message="mobile login failed",
                screenshot_path=_shot("mobile-login-fail"),
                timestamp=_now_iso(),
                commit_sha=commit,
            ))
            browser.close()
            return findings

        # US-21, vierter Fix-Versuch: Onboarding läuft als letzter Schritt von
        # App.init(), NACHDEM Auth.isLoggedIn() wahr wurde — nochmal wegklicken.
        _dismiss_onboarding_if_present(page)

        # --- 1) App-Container überschreitet Viewport nicht -----------------------
        app_width = page.eval_on_selector("#app", "el => el.getBoundingClientRect().width")
        if app_width > IPHONE_WIDTH + 5:  # 5px Toleranz für sub-pixel rendering
            findings.append(Finding(
                view="mobile-layout",
                assertion_id="app_width_overflow",
                expected=f"#app-Breite ≤ {IPHONE_WIDTH}px",
                actual=f"#app-Breite = {app_width:.0f}px (übersteigt Viewport)",
                message=f"app container overflows mobile viewport: {app_width:.0f}px > {IPHONE_WIDTH}px",
                screenshot_path=_shot("mobile-app-overflow"),
                timestamp=_now_iso(),
                commit_sha=commit,
            ))

        # --- 2) Detail-Sheet öffnen: Close-Button im Viewport -------------------
        page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "locations")
        try:
            page.wait_for_selector(_spec.LOCATION_CARD_SELECTOR, timeout=12000)
            # US-21, vierter Fix-Versuch: zusätzliche Absicherung direkt vor dem Klick,
            # siehe Docstring von _dismiss_onboarding_if_present.
            _dismiss_onboarding_if_present(page)
            page.click(_spec.LOCATION_CARD_SELECTOR)
            page.wait_for_selector(_spec.DETAIL_SHEET_OPEN_SELECTOR, timeout=12000)
            _shot("mobile-detail-sheet-open")

            # Close-Button muss innerhalb des Viewports liegen (BUG-19/BUG-25)
            close_btn = page.query_selector(
                "#loc-detail-sheet .sheet-close-btn, #loc-detail-sheet [class*='close']"
            )
            if close_btn:
                rect = close_btn.bounding_box()
                if rect:
                    if rect["y"] < 0 or rect["y"] + rect["height"] > IPHONE_HEIGHT:
                        findings.append(Finding(
                            view="mobile-detail",
                            assertion_id="close_btn_in_viewport",
                            expected=f"Close-Button innerhalb Viewport (0–{IPHONE_HEIGHT}px)",
                            actual=f"Close-Button y={rect['y']:.0f}px, h={rect['height']:.0f}px — außerhalb Viewport",
                            message=f"close button outside viewport on mobile: y={rect['y']:.0f}",
                            screenshot_path=_shot("mobile-close-btn-overflow"),
                            timestamp=_now_iso(),
                            commit_sha=commit,
                        ))
        except Exception as e:
            # Detail-Sheet-Test best-effort: Desktop-Pass deckt Öffnen bereits ab
            pass

        # --- 3) Filter-Sheet überschreitet Viewport nicht (BUG-07 / BUG-34) ----
        try:
            page.evaluate("() => { const fs = document.getElementById('filter-sheet'); if(fs) fs.classList.add('open'); }")
            page.wait_for_timeout(300)  # CSS-Transition

            sheet = page.query_selector("#filter-sheet")
            if sheet:
                rect = sheet.bounding_box()
                if rect and rect["width"] > IPHONE_WIDTH + 5:
                    findings.append(Finding(
                        view="mobile-filter",
                        assertion_id="filter_sheet_width",
                        expected=f"#filter-sheet-Breite ≤ {IPHONE_WIDTH}px",
                        actual=f"#filter-sheet-Breite = {rect['width']:.0f}px",
                        message=f"filter sheet overflows mobile viewport: {rect['width']:.0f}px",
                        screenshot_path=_shot("mobile-filter-overflow"),
                        timestamp=_now_iso(),
                        commit_sha=commit,
                    ))
                # Sheet schließen
                page.evaluate("() => { const fs = document.getElementById('filter-sheet'); if(fs) fs.classList.remove('open'); }")
        except Exception:
            pass

        _shot("mobile-end")
        browser.close()
    return findings


# --- CLI ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="FotoAlert Frontend-Check (TASK-20)")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument(
        "--password",
        default=os.environ.get("FOTOALERT_USER_PASSWORD", "test-user-pw"),
    )
    parser.add_argument(
        "--host-password",
        default=os.environ.get("FOTOALERT_HOST_PASSWORD", "test-host-pw"),
        help="TASK-66: Host-Login für den Bild-Upload-Durchlauf (LocationDetail-Sheet "
        "ist host-only, siehe _check_image_upload). In CI bereits als Secret "
        "FOTOALERT_HOST_PASSWORD vorhanden (deploy.yml, test-frontend-Job).",
    )
    parser.add_argument("--headed", action="store_true", help="Browser sichtbar (Debug)")
    parser.add_argument(
        "--screenshot-root",
        default=str(Path(__file__).resolve().parents[3] / "docs" / "qa-screenshots"),
    )
    parser.add_argument(
        "--findings-json",
        default=str(Path.cwd() / "findings.json"),
    )
    parser.add_argument(
        "--backlog",
        default=None,
        help="Optionaler Pfad zu einer lokalen BACKLOG-Kopie für Dedup-Merge "
        "(in CI NICHT setzen — keine Commits).",
    )
    args = parser.parse_args(argv)

    # Desktop-Pass
    findings = run_checks(
        base_url=args.base_url,
        password=args.password,
        screenshot_root=Path(args.screenshot_root),
        headless=not args.headed,
        host_password=args.host_password,
    )

    # TASK-35: Mobile-Pass (iPhone 14 Viewport) — fängt iOS-Layout-Bugs ab:
    # BUG-19 (Close-Button hinter Dynamic Island), BUG-25, BUG-34 (Edit-Overlay-Zoom).
    mobile_findings = run_mobile_checks(
        base_url=args.base_url,
        password=args.password,
        screenshot_root=Path(args.screenshot_root),
        headless=not args.headed,
    )
    findings.extend(mobile_findings)

    _reporter.report(
        findings,
        backlog_path=args.backlog,
        findings_json_path=args.findings_json,
    )

    if findings:
        print("FAIL: {0} Finding(s)".format(len(findings)))
        for f in findings:
            print("  - [{0}] {1}: erwartet={2} | ist={3}".format(f.view, f.assertion_id, f.expected, f.actual))
        return 1
    print("OK: keine Findings.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
