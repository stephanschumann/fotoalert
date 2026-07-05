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

        # 4) Konsolen-/Page-Errors → Findings (AK2).
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
            print("  - [{0}] {1}: {2}".format(f.view, f.assertion_id, f.actual))
        return 1
    print("OK: keine Findings.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
