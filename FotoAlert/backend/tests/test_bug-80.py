"""BUG-80 — Kopfzeile (`#header`) darf beim Wechsel der Infozeile nicht springen.

Hintergrund (siehe BACKLOG.md BUG-80, Pre-Mortem + Code-Verifikation 2026-07-15):
`web/index.html` setzt den Text von `#header-subtitle` ausschließlich in
`Feed.render()` (Zeile ~2106f.) — je nach Filterergebnis wechselt der Text zwischen
dem kurzen Standardtext „Capture moments that matter." und einem längeren,
dynamischen Text „Heute: X Chancen · Bester Score Y%". `#header` hat keine feste
Höhe (`display:flex; flex-shrink:0`, keine `min-height`), daher ändert ein
Textlängenwechsel die Kopfzeilenhöhe sichtbar (der eigentliche Bug).

Dieser Test ist bewusst EIN eigenständiger, self-contained Playwright-Test (nicht
über `run_frontend_check.run_checks()` eingehängt) — die Analyse-Phase fügt keine
neue Prüf-Funktion in `run_frontend_check.py` ein (das wäre bereits Implementierung),
sondern nur diesen Testfall, der schon VOR dem Fix rot ist und nach dem Fix grün wird
(Test-First, siehe Skill fotoalert-analyze Schritt 6b).

Deterministischer Auslöser (kein inhaltlicher Chip-Filter, Pre-Mortem TASK-66 lehrt:
inhaltliche Filter können tagesabhängig 0-Treffer-Ausgangslagen haben und flaken):
Wie in `_check_filter_feed` (run_frontend_check.py, TASK-66) wird `minScore` zur
Laufzeit auf einen Wert knapp über dem höchsten sichtbaren `overall_score` gesetzt
(`Filter.save({minScore: v}); await FilterSheet._applyLive();`) — das ist exakt der
Codepfad, den auch der reale Filter-Sheet-Slider auslöst, und verändert die "Heute"-
Trefferzahl deterministisch, ohne von der zufälligen Tagesdatenlage abzuhängen.

CI-Datenumfeld-Hinweis (siehe Pre-Mortem BUG-80): Ändert sich der Infozeilen-Text
durch den Filterwechsel NICHT (z. B. weil im frischen CI-Environment für „Heute"
ohnehin 0 Chancen vorhanden sind und der Standardtext vorher wie nachher steht),
wird der Test als dokumentierter Skip behandelt statt als falsch-grüner Pass — der
Sprung-Fall wäre in diesem Datenumfeld gar nicht ausgelöst worden.

Toleranz: 1px (Sub-Pixel-Rundung durch den Browser).
"""
from __future__ import annotations

import math
import os
import sys
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("playwright")

sys.path.insert(0, str(Path(__file__).resolve().parent / "frontend"))
import run_frontend_check as rfc  # noqa: E402

pytestmark = [pytest.mark.frontend, pytest.mark.regression]

BASE_URL = os.environ.get("FOTOALERT_TEST_BASE_URL", "http://localhost:8000")
USER_PASSWORD = os.environ.get("FOTOALERT_USER_PASSWORD", "test-user-pw")

# AK2: schmaler Bildschirm (iPhone-SE/Mini-Klasse) — genau die Breite, auf der der
# lange Infotext am ehesten umbricht und der Sprung am wahrscheinlichsten auftritt.
NARROW_VIEWPORT = {"width": 375, "height": 812}

HEADER_SELECTOR = "#header"
SUBTITLE_SELECTOR = "#header-subtitle"

# Toleranz gegen Sub-Pixel-Rundung des Browsers (AK1: "≤ 1px").
HEIGHT_TOLERANCE_PX = 1.0


def _server_reachable() -> bool:
    try:
        with urllib.request.urlopen(BASE_URL + "/health", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


if not _server_reachable():
    pytest.skip(
        "Kein laufender Dev-Server unter {0} erreichbar — BUG-80-Layout-Test "
        "braucht einen echten Server (Playwright/Browser-Rendering nötig). "
        "Übersprungen, nicht rot.".format(BASE_URL),
        allow_module_level=True,
    )


def test_bug80_header_height_stable_after_filter_change():
    """AK1 + AK2: Kopfzeilenhöhe bleibt beim Infozeilen-Textwechsel konstant.

    Ablauf:
      1. Login, Feed-Tab, schmaler Viewport (375px, AK2).
      2. Baseline messen: `#header`-Höhe + `#header-subtitle`-Text.
      3. Deterministischer Filterwechsel (`Filter.save` + `FilterSheet._applyLive()`,
         identischer Codepfad wie der reale Score-Slider) — verändert die
         "Heute"-Trefferzahl unabhängig von der Tagesdatenlage.
      4. Erneut messen: Höhe darf sich um höchstens 1px ändern (AK1), UNABHÄNGIG
         davon ob der Text kürzer oder länger geworden ist.
      5. Reset auf Default-Filter: Höhe muss wieder der Baseline entsprechen.

    Edge Case (AK3 / CI-Datenumfeld, siehe Pre-Mortem): Ändert der Filterwechsel den
    Infozeilen-Text NICHT (z. B. leeres CI-Environment ohne "Heute"-Chancen), ist der
    Sprung-Fall in diesem Datenumfeld gar nicht auslösbar — dokumentierter Skip statt
    falsch-grünem Pass.
    """
    sync_playwright = rfc._import_playwright()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size(NARROW_VIEWPORT)
        page.set_default_timeout(15000)
        try:
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
                    "kein App-Zugriff möglich, BUG-80-Test übersprungen."
                )
            rfc._dismiss_onboarding_if_present(page)

            page.evaluate("(v) => { if (typeof App !== 'undefined') App.nav(v); }", "feed")
            page.wait_for_selector("#feed-content", timeout=12000)
            page.wait_for_function(
                "() => typeof Feed !== 'undefined' && Array.isArray(Feed.data)", timeout=12000
            )

            baseline_height = page.eval_on_selector(
                HEADER_SELECTOR, "el => el.getBoundingClientRect().height"
            )
            baseline_text = page.eval_on_selector(SUBTITLE_SELECTOR, "el => el.textContent")

            # Deterministischer Auslöser: höchsten sichtbaren overall_score ermitteln
            # und minScore knapp darüber setzen (identischer Mechanismus + Begründung
            # wie _check_filter_feed in run_frontend_check.py, TASK-66).
            score_stats = page.evaluate(
                "() => { "
                "const data = Feed.data || []; "
                "const scored = data.filter(e => typeof e.overall_score === 'number' && !isNaN(e.overall_score)); "
                "const maxScore = scored.length > 0 ? scored.reduce((m, e) => Math.max(m, e.overall_score), -Infinity) : null; "
                "return { scoredCount: scored.length, maxScore: maxScore }; "
                "}"
            )
            if score_stats["scoredCount"] == 0 or (
                score_stats["maxScore"] is not None and score_stats["maxScore"] >= 1.0
            ):
                pytest.skip(
                    "Kein Feed-Eintrag mit ausschließbarem overall_score (scoredCount={0}, "
                    "maxScore={1}) — Filterwechsel kann die 'Heute'-Trefferzahl in diesem "
                    "Datenumfeld strukturell nicht verändern (vgl. TASK-66-Edge-Case). "
                    "BUG-80-Sprung-Fall in diesem Lauf nicht auslösbar.".format(
                        score_stats["scoredCount"], score_stats["maxScore"]
                    )
                )

            extreme_min_score = min(100, math.ceil(score_stats["maxScore"] * 100) + 1)
            page.evaluate(
                "async (v) => { Filter.save({ minScore: v }); await FilterSheet._applyLive(); }",
                extreme_min_score,
            )
            page.wait_for_timeout(300)  # kurze Renderzeit für Feed.render()

            filtered_text = page.eval_on_selector(SUBTITLE_SELECTOR, "el => el.textContent")

            if filtered_text == baseline_text:
                pytest.skip(
                    "Infozeilen-Text änderte sich durch den Filterwechsel nicht "
                    "('{0}' vor und nach) — CI-Datenumfeld ohne 'Heute'-Chancen, "
                    "Sprung-Fall in diesem Lauf nicht auslösbar (siehe Pre-Mortem "
                    "CI-Datenumfeld-Check).".format(baseline_text)
                )

            filtered_height = page.eval_on_selector(
                HEADER_SELECTOR, "el => el.getBoundingClientRect().height"
            )

            # Reset auf Default, damit die Baseline für den zweiten Vergleich gilt.
            page.evaluate(
                "async (v) => { Filter.save({ minScore: v }); await FilterSheet._applyLive(); }",
                rfc._spec.FILTER_MIN_SCORE_DEFAULT,
            )
            page.wait_for_timeout(300)
            reset_height = page.eval_on_selector(
                HEADER_SELECTOR, "el => el.getBoundingClientRect().height"
            )

            assert abs(filtered_height - baseline_height) <= HEIGHT_TOLERANCE_PX, (
                "Kopfzeile ('#header') aenderte ihre Hoehe beim Textwechsel: "
                "baseline={0:.1f}px ('{1}'), gefiltert={2:.1f}px ('{3}') — "
                "Differenz > {4}px Toleranz (BUG-80)".format(
                    baseline_height, baseline_text, filtered_height, filtered_text,
                    HEIGHT_TOLERANCE_PX,
                )
            )
            assert abs(reset_height - baseline_height) <= HEIGHT_TOLERANCE_PX, (
                "Kopfzeile kehrte nach Filter-Reset nicht zur Baseline-Hoehe zurueck: "
                "baseline={0:.1f}px, nach Reset={1:.1f}px".format(baseline_height, reset_height)
            )
        finally:
            browser.close()
