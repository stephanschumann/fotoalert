"""BUG-85 (korrigierter Scope, 2026-07-28) — Kopfzeile (`#header-subtitle`)
aktualisiert sich nicht, wenn der KOMPLETTE 14-Tage-Feed (über alle aktiven
Filter) auf 0 Treffer reduziert wird.

⚠️ WICHTIGE SCOPE-KORREKTUR (Stephan, 2026-07-28): Der ursprüngliche BUG-85-Scope
("englischer Platzhaltertext 'Capture moments that matter.' ist ein Sprachfehler")
beruhte auf einer FALSCHEN Prämisse. Dieser Satz ist bewusst so gewollt (Stephans
Produkt-Tagline) und KEIN Bug — weder an der statischen HTML-Stelle (`web/index.html`
Zeile 1191) noch im dynamischen Fallback in `Feed.render()` (Zeile 2171, Fall
"kein Treffer nur für 'Heute', aber Datensatz insgesamt nicht leer"). Die alten
Tests dieser Datei (AK1-AK4, Edge-Case), die genau das als Fehler behandelten, sind
damit hinfällig und wurden komplett ersetzt.

Der ECHTE, von Stephan bestätigte Bug (Pre-Mortem Szenario 3 der ursprünglichen
Analyse) ist dieser:

  `web/index.html`, `Feed.render()`, Zeile 2092-2172 (Code-Verifikation
  2026-07-28, wortgleich gelesen):
    - Zeile 2095: `const data = Filter.apply(this.data);` — `data` ist das Ergebnis
      NACH Anwendung ALLER aktiven Filter auf den KOMPLETTEN 14-Tage-Rohdatensatz
      (`this.data`), nicht nur auf die Teilmenge "Heute".
    - Zeile 2097: `if (!data.length) {` — dieser Zweig greift, wenn der gefilterte
      14-Tage-Feed INSGESAMT leer ist (nicht nur "Heute" leer, sonst aber Treffer
      vorhanden — das wäre der andere, unveränderte Fall aus Zeile 2171).
    - Innerhalb dieses Zweigs gibt es zwei `return`-Stellen (Zeile ~2119 BUG-32-
      Soft-Fallback für Routine-Events, Zeile ~2130 generischer Empty-State) —
      BEIDE liegen VOR der Kopfzeilen-Aktualisierung in Zeile 2169-2171, der
      EINZIGEN Stelle, an der `render()` `#header-subtitle` überhaupt setzt.
    - Konsequenz: In diesem Sonderfall wird `#header-subtitle` von `render()`
      GAR NICHT angefasst — die Kopfzeile bleibt auf dem zuletzt gültigen (unter
      Umständen veralteten) Text stehen, z. B. einer alten Trefferzahl aus einem
      früheren, nicht-leeren Zustand. Kein Sprachfehler, sondern ein
      Aktualitäts-/Stale-State-Bug.

  Bewusst AUSSERHALB des BUG-32-Soft-Fallback-Zweigs (Zeile ~2103-2119) getestet:
  dort werden trotz `data.length === 0` tatsächlich Karten angezeigt (Routine-
  Events) — das ist kein "0 Treffer"-Zustand im Sinne von Stephans Bestätigung
  und laut Spec (BACKLOG.md BUG-85, Scope-Abschnitt) bewusst NICHT Teil dieses
  Tickets.

✅ FRAGE 1 BEANTWORTET (Stephan, 2026-07-28, siehe BACKLOG.md BUG-85): Die
Kopfzeile bekommt für diesen Sonderfall einen EIGENEN, bewusst kurz gehaltenen,
dafür geschriebenen Text — NICHT die bestehende Body-Leertext-Nachricht
(Variable `msg` in `Feed.render()`, angezeigt in `.empty p`) wiederverwendet.
Grund: die Body-Nachricht kann je nach Filter-/Suchzustand deutlich länger
werden ("Filter aktiv: 3 Chancen, 0 entsprechen den Kriterien.") und hätte bei
Wiederverwendung in der Kopfzeile erneut das BUG-80-Höhensprung-Risiko
reproduziert. Der konkrete, finale Wortlaut ist Implementierungsdetail (Vorschlag
in BACKLOG.md: "Keine Chancen in den nächsten 14 Tagen." bzw. bei aktivem Filter
"Filter: keine Treffer.") und wird deshalb weiterhin NICHT als feste
String-Erwartung geprüft. Stattdessen prüft diese Datei zwei wortlaut-
unabhängige Kernanforderungen: (1) der Kopfzeilentext ändert sich sichtbar
gegenüber dem alten Stand, UND (2) der neue Kopfzeilentext ist NICHT identisch
mit der Body-Leertext-Nachricht — das operationalisiert Stephans Entscheidung
gegen die Body-Text-Wiederverwendung, ohne den finalen Wortlaut vorwegzunehmen.

Rot-Nachweis in dieser Sandbox: Kein laufender Dev-Server/Playwright verfügbar
(siehe Skip unten). Als Ersatz-Nachweis wurde die exakte `render()`-Methode
(Zeile 2092-2172) wortgleich aus `web/index.html` extrahiert und unter Node.js
mit einer minimalen Stub-Umgebung ausgeführt: Baseline-Render mit 1 Treffer
"Heute" setzt die Kopfzeile korrekt auf den dynamischen Text; ein anschließender
Filterwechsel, der den KOMPLETTEN gefilterten Datensatz auf 0 reduziert
(`Filter.apply` liefert `[]`), lässt die Kopfzeile UNVERÄNDERT auf dem alten Text
stehen — der Test schlägt (erwartungsgemäß) fehl. Dieser Node-Nachweis lief nur
als lokale Verifikation der Analyse-Phase und ist nicht Teil des Testbestands.
"""
from __future__ import annotations

import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

pytest.importorskip("playwright")

sys.path.insert(0, str(Path(__file__).resolve().parent / "frontend"))
import run_frontend_check as rfc  # noqa: E402

pytestmark = [pytest.mark.frontend, pytest.mark.regression]

BASE_URL = os.environ.get("FOTOALERT_TEST_BASE_URL", "http://localhost:8000")
USER_PASSWORD = os.environ.get("FOTOALERT_USER_PASSWORD", "test-user-pw")

SUBTITLE_SELECTOR = "#header-subtitle"
ENGLISH_TAGLINE = "Capture moments that matter."  # bewusster Produkt-Text, KEIN Bug

# Nicht in Feed._ROUTINE_TYPES enthalten (siehe web/index.html) -> löst den
# BUG-32-Soft-Fallback-Zweig NICHT aus, wenn er als einziger Typ vorhanden ist
# und weggefiltert wird (Voraussetzung, um Zeile 2097 über den generischen
# Empty-Branch statt den Soft-Fallback zu erreichen).
NON_ROUTINE_EVENT_TYPE = "Milchstraße"
OTHER_NON_ROUTINE_EVENT_TYPE = "Mond-Alignment"


def _server_reachable() -> bool:
    try:
        with urllib.request.urlopen(BASE_URL + "/health", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


if not _server_reachable():
    pytest.skip(
        "Kein laufender Dev-Server unter {0} erreichbar — BUG-85-Test braucht "
        "einen echten Server (Playwright/Browser-Rendering nötig). "
        "Übersprungen, nicht rot.".format(BASE_URL),
        allow_module_level=True,
    )


def _login_and_reach_feed(page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    rfc._dismiss_onboarding_if_present(page)
    page.fill("#login-pw", USER_PASSWORD)
    page.click(".login-btn")
    try:
        page.wait_for_function(
            "() => typeof Auth !== 'undefined' && Auth.isLoggedIn()", timeout=15000
        )
    except Exception:
        pytest.skip(
            "Login fehlgeschlagen (Auth.isLoggedIn() blieb false) — "
            "kein App-Zugriff möglich, BUG-85-Test übersprungen."
        )
    rfc._dismiss_onboarding_if_present(page)
    page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
    page.wait_for_selector("#feed-content", timeout=12000)
    page.wait_for_function(
        "() => typeof Feed !== 'undefined' && Array.isArray(Feed.data)", timeout=12000
    )


def _inject_today_entry(page, event_type: str, overall_score: float = 0.9):
    """Ersetzt `Feed.data` durch genau 1 synthetischen Eintrag für "Heute" mit dem
    angegebenen `event_type` — erzeugt einen definierten, nicht-leeren
    Ausgangszustand (Baseline "Heute: 1 Chancen · Bester Score X%")."""
    page.evaluate(
        """(args) => {
            const [eventType, score] = args;
            const now = new Date();
            Feed.data = [{
                event_type: eventType,
                shoot_time: now.toISOString(),
                overall_score: score,
                alert_priority: 0,
                title: 'Test-Chance (BUG-85)',
                location_id: 999999,
                location_name: 'Testort',
                weather_status: 'none',
                weather_score: 0,
            }];
        }""",
        [event_type, overall_score],
    )


def _inject_tomorrow_only_entry(page, event_type: str):
    """Ersetzt `Feed.data` durch genau 1 synthetischen Eintrag für "Morgen" (nie
    "Heute") — für den weiterhin gültigen (nicht gebuggten) Tagline-Fall.

    BUG-105: Der Zielzeitpunkt wird bewusst in Python berechnet, nicht im
    Browser-JS von `page.evaluate()` — das liefe in der lokalen Zeitzone des
    Test-Runners (in CI UTC), während die App "Heute"/"Morgen" fest gegen
    Europe/Berlin klassifiziert (`formatDate()` in web/index.html). Um das
    frühere Risikofenster um die Berliner Tagesgrenze (~22:00-00:00 UTC)
    strukturell auszuschließen, liegt der Zielzeitpunkt auf Berlin-Mittag
    (12:00) — maximaler 12h-Sicherheitsabstand zur Tagesgrenze in beide
    Richtungen, übersteht auch den Sommerzeit-Wechsel. Ein künftiger Rotlauf
    dieses Tests ist damit kein Zeitzonen-Fehlalarm mehr, sondern eine echte
    Regression."""
    berlin_tomorrow_noon = (
        datetime.now(ZoneInfo("Europe/Berlin")) + timedelta(days=1)
    ).replace(hour=12, minute=0, second=0, microsecond=0)
    tomorrow_iso = berlin_tomorrow_noon.isoformat()
    page.evaluate(
        """(args) => {
            const [eventType, shootTime] = args;
            Feed.data = [{
                event_type: eventType,
                shoot_time: shootTime,
                overall_score: 0.9,
                alert_priority: 0,
                title: 'Test-Chance (BUG-85)',
                location_id: 999999,
                location_name: 'Testort',
                weather_status: 'none',
                weather_score: 0,
            }];
        }""",
        [event_type, tomorrow_iso],
    )


def _reset_filter_to_default(page):
    page.evaluate(
        "async () => { Filter.save({ eventTypes: [], eventTypesExcl: [] }); "
        "await FilterSheet._applyLive(); }"
    )


def test_bug85_full_feed_filtered_to_zero_header_must_not_stay_stale():
    """DER korrigierte BUG-85-Kernfall (Pre-Mortem Szenario 3, von Stephan
    bestätigt): Reduziert ein Filter den KOMPLETTEN 14-Tage-Feed (nicht nur
    "Heute") auf 0 Treffer, darf die Kopfzeile NICHT auf dem zuvor gesetzten
    Text stehen bleiben.

    Bewusst KEINE feste String-Erwartung an den neuen Text (finaler Wortlaut
    ist laut Frage-1-Entscheidung in BACKLOG.md Implementierungsdetail) — aber
    zwei wortlaut-unabhängige Kernanforderungen: (1) der Text muss sich
    sichtbar ändern, (2) der neue Kopfzeilentext darf NICHT identisch mit der
    Body-Leertext-Nachricht (`.empty p`) sein — das prüft Stephans Entscheidung
    für einen eigenen, dedizierten Kopfzeilentext statt einer Wiederverwendung
    des Body-Texts (BUG-80-Höhenrisiko).
    """
    sync_playwright = rfc._import_playwright()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(15000)
        try:
            _login_and_reach_feed(page)
            _reset_filter_to_default(page)

            # Baseline: 1 Treffer "Heute" -> Kopfzeile zeigt den dynamischen
            # Text (definierter, nicht-leerer Vorzustand).
            _inject_today_entry(page, NON_ROUTINE_EVENT_TYPE, 0.9)
            page.evaluate("() => Feed.render()")
            page.wait_for_timeout(200)
            stale_text = page.eval_on_selector(SUBTITLE_SELECTOR, "el => el.textContent")
            assert "Heute: 1 Chancen" in stale_text, (
                "Testvoraussetzung verletzt: Baseline-Text nicht wie erwartet "
                "gesetzt ('{0}').".format(stale_text)
            )

            # Auslöser: echter Filter-Codepfad (wie ein Chip-Klick), der den
            # EINZIGEN vorhandenen Eintrag ausschließt -> Filter.apply(Feed.data)
            # liefert [] -> kompletter 14-Tage-Feed gefiltert = 0 Treffer.
            page.evaluate(
                """async (otherType) => {
                    Filter.save({ eventTypes: [otherType] });
                    await FilterSheet._applyLive();
                }""",
                OTHER_NON_ROUTINE_EVENT_TYPE,
            )
            page.wait_for_timeout(300)

            new_text = page.eval_on_selector(SUBTITLE_SELECTOR, "el => el.textContent")

            assert new_text != stale_text, (
                "BUG-85 (korrigierter Scope) reproduziert: Kopfzeile blieb nach "
                "vollständig leerem gefiltertem 14-Tage-Feed unverändert auf dem "
                "alten Text stehen ('{0}'), statt sich auf einen neuen, zum "
                "leeren Zustand passenden Text zu ändern.".format(stale_text)
            )

            # Frage-1-Entscheidung (Stephan, 2026-07-28): eigener, dedizierter
            # Kopfzeilentext — KEINE Wiederverwendung der Body-Leertext-Nachricht
            # (Variable `msg` in Feed.render(), angezeigt in `.empty p`). Prüft
            # die Entscheidung wortlaut-unabhängig, ohne den finalen Wortlaut
            # vorwegzunehmen.
            body_empty_text = page.eval_on_selector(".empty p", "el => el.textContent")
            assert new_text != body_empty_text, (
                "Kopfzeilentext ('{0}') ist identisch mit der Body-Leertext-"
                "Nachricht ('{1}') — laut Stephans Entscheidung zu Frage 1 "
                "(BACKLOG.md BUG-85) soll die Kopfzeile einen EIGENEN, bewusst "
                "kurzen Text zeigen und NICHT die Body-Nachricht wiederverwenden "
                "(vermeidet das BUG-80-Höhensprung-Risiko).".format(
                    new_text, body_empty_text
                )
            )
        finally:
            browser.close()


def test_bug85_regression_today_only_empty_tagline_is_intentional():
    """Regressions-Schutz (NICHT der Bug — siehe Modul-Docstring): Ist nur "Heute"
    leer, aber der gefilterte 14-Tage-Feed insgesamt NICHT leer, bleibt der
    englische Tagline-Fallback weiterhin sichtbar — das ist Stephans bestätigtes,
    gewolltes Verhalten. Dieser Test schützt davor, dass eine künftige Änderung
    diesen (fälschlich für einen Bug gehaltenen) Fall versehentlich "mitfixt".
    """
    sync_playwright = rfc._import_playwright()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(15000)
        try:
            _login_and_reach_feed(page)
            _reset_filter_to_default(page)
            _inject_tomorrow_only_entry(page, NON_ROUTINE_EVENT_TYPE)
            page.evaluate("() => Feed.render()")
            page.wait_for_timeout(200)

            text = page.eval_on_selector(SUBTITLE_SELECTOR, "el => el.textContent")

            assert text == ENGLISH_TAGLINE, (
                "Regression: der bewusst gewollte Tagline-Fallback für 'Heute "
                "leer, insgesamt nicht leer' wurde verändert (jetzt: '{0}') — "
                "das war laut Stephans Bestätigung (2026-07-28) kein Bug und "
                "sollte durch dieses Ticket nicht angefasst werden.".format(text)
            )
        finally:
            browser.close()


def test_bug85_regression_static_placeholder_unchanged():
    """Regressions-Schutz: Der statische HTML-Platzhalter (Zeile 1191) bleibt
    unverändert die englische Tagline — reiner HTTP-Check, kein Browser nötig.
    Kein Bug (siehe Modul-Docstring); dieser Test verhindert, dass die
    korrigierte Implementierung diese bewusst gewollte Stelle versehentlich
    mitändert."""
    with urllib.request.urlopen(BASE_URL, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    import re
    m = re.search(r'id="header-subtitle"[^>]*>([^<]*)<', html)
    assert m is not None, "#header-subtitle-Element nicht im initialen HTML gefunden."
    static_text = m.group(1)

    assert static_text == ENGLISH_TAGLINE, (
        "Regression: statischer HTML-Platzhalter in #header-subtitle wurde "
        "verändert (jetzt: '{0}') — das ist Stephans bewusste Produkt-Tagline, "
        "kein Bug, sollte durch dieses Ticket nicht angefasst werden.".format(static_text)
    )
