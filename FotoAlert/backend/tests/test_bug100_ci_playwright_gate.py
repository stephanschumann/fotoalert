"""BUG-100: Absicherung, dass die drei Playwright-pytest-Dateien
(test_bug_85.py, test_bug-80.py, test_task-66.py) im Playwright-/Server-
fähigen `test-frontend`-Job von .github/workflows/deploy.yml real ausgeführt
werden — nicht mehr nur per pytest.importorskip("playwright") bzw. dem
zweiten /health-Erreichbarkeits-Skip lautlos übersprungen.

Rein statischer Wortlaut-/Struktur-Check gegen deploy.yml (kein Netzwerk, kein
echter CI-Lauf, kein Browser) — analog zum bestehenden Muster in
test_bug79_ci_ephemeris_skip.py. Prüft:

1. Alle drei betroffenen Dateien werden zusammen in einem einzigen pytest-
   Aufruf referenziert.
2. Dieser Aufruf steht strukturell NACH dem Schritt "Frontend-Check
   ausführen" und VOR dem Schritt "Dev-Server stoppen" — also innerhalb des
   Zeitfensters, in dem der Dev-Server im `test-frontend`-Job tatsächlich
   läuft. Nur dann greift auch der zweite, im Ticket dokumentierte
   /health-Skip-Mechanismus nicht mehr (Pre-Mortem Szenario 1, BACKLOG.md
   BUG-100: reines Playwright-Install ohne laufenden Server hätte das
   gemeldete Symptom NICHT behoben).

Schlägt fehl, wenn jemand künftig den Schritt "Backend-Playwright-Tests
ausführen" versehentlich entfernt, verschiebt (z.B. hinter "Dev-Server
stoppen") oder die drei Dateinamen aus dem pytest-Aufruf herausnimmt — genau
der stille Rückfall, den BUG-100 behoben hat. Ein echter CI-Lauf, bei dem die
drei Tests tatsächlich als "passed" statt "skipped" im Log erscheinen, bleibt
zusätzlich Teil des manuellen Testplans (BACKLOG.md BUG-100) — dieser Test
prüft nur die statische Struktur, nicht das Laufzeitergebnis.
"""
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]

_TESTS_DIR = Path(__file__).parent
_BACKEND_DIR = _TESTS_DIR.parent
_PROJECT_DIR = _BACKEND_DIR.parent
_REPO_ROOT = _PROJECT_DIR.parent
_DEPLOY_YML = _REPO_ROOT / ".github" / "workflows" / "deploy.yml"

_TARGET_TEST_FILES = [
    "test_bug_85.py",
    "test_bug-80.py",
    "test_task-66.py",
]

_FRONTEND_CHECK_STEP = "Frontend-Check ausführen"
_STOP_SERVER_STEP = "Dev-Server stoppen"


def _read_deploy_yml() -> str:
    assert _DEPLOY_YML.exists(), f"{_DEPLOY_YML} nicht gefunden"
    return _DEPLOY_YML.read_text(encoding="utf-8")


def test_playwright_test_files_referenced_in_deploy_yml():
    """AK1/Regel 1: Alle drei Dateien tauchen (irgendwo) in deploy.yml auf."""
    source = _read_deploy_yml()
    missing = [name for name in _TARGET_TEST_FILES if name not in source]
    assert not missing, (
        f"Folgende Playwright-pytest-Dateien werden in deploy.yml nicht (mehr) "
        f"referenziert — BUG-100-Regression: {missing}"
    )


def test_playwright_test_files_run_between_frontend_check_and_server_stop():
    """AK1/Regel 1/Pre-Mortem Szenario 1: Der pytest-Aufruf für die drei Dateien
    steht strukturell im Zeitfenster, in dem der Dev-Server läuft."""
    source = _read_deploy_yml()

    frontend_check_idx = source.find(_FRONTEND_CHECK_STEP)
    stop_server_idx = source.find(_STOP_SERVER_STEP)
    assert frontend_check_idx != -1, (
        f"Schritt {_FRONTEND_CHECK_STEP!r} nicht in deploy.yml gefunden — "
        "Grundannahme des Guard-Checks verletzt."
    )
    assert stop_server_idx != -1, (
        f"Schritt {_STOP_SERVER_STEP!r} nicht in deploy.yml gefunden — "
        "Grundannahme des Guard-Checks verletzt."
    )
    assert frontend_check_idx < stop_server_idx, (
        f"Erwartete Reihenfolge {_FRONTEND_CHECK_STEP!r} vor {_STOP_SERVER_STEP!r} "
        "nicht gegeben — Grundannahme des Guard-Checks verletzt."
    )

    window = source[frontend_check_idx:stop_server_idx]
    missing = [name for name in _TARGET_TEST_FILES if name not in window]
    assert not missing, (
        "Folgende Playwright-pytest-Dateien werden nicht (mehr) zwischen den "
        f"Schritten {_FRONTEND_CHECK_STEP!r} und {_STOP_SERVER_STEP!r} (laufender "
        f"Dev-Server) in deploy.yml ausgeführt — BUG-100-Regression, die Tests würden "
        f"erneut lautlos am /health-Skip überspringen: {missing}"
    )
