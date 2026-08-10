"""TASK-97 (AK4) — Regressionsguard: FOTOALERT_ENV: dev bleibt im Job-env-Block
von .github/workflows/deploy.yml (Job `test-frontend`).

Hintergrund: Ursachenkategorie 3 der TASK-97-Analyse (BACKLOG.md) — die
Cookie/Secure-Flag-Klasse aus der TASK-83-Historie ist bereits strukturell
abgesichert (FOTOALERT_ENV: dev im Job-env-Block, siehe backend/main.py
_COOKIE_SECURE), aber bislang durch KEINEN Test gegen versehentliches
Entfernen geschützt. Ohne dieses Env-Flag würde `Response.set_cookie(...,
secure=True)` im Dev-CI-Job greifen — ein Cookie mit `Secure`-Flag wird von
Playwright-Chromium über reines HTTP (http://localhost:8000) verworfen, und
genau das erzeugt exakt das Symptom aus CI-Run #277: `Auth.isLoggedIn()`
bleibt nach dem Login-Submit false, ohne dass das Passwort selbst falsch war.

Rein statischer Wortlaut-/Struktur-Check gegen deploy.yml (kein Netzwerk,
kein echter CI-Lauf, kein Browser) — analog zum bestehenden Muster in
test_bug100_ci_playwright_gate.py. Prüft:

1. `.github/workflows/deploy.yml` ist auffindbar (Grundannahme des Checks).
2. Der Job `test-frontend:` existiert weiterhin als eigener Top-Level-Job.
3. `FOTOALERT_ENV: dev` steht strukturell INNERHALB des `test-frontend`-Jobs
   (zwischen dessen Start und dem nächsten Top-Level-Job `test-backend:`) —
   nicht irgendwo anders im File.

Schlägt fehl, wenn jemand künftig FOTOALERT_ENV aus dem env-Block entfernt,
seinen Wert von "dev" ändert, oder den gesamten env-Block aus dem
test-frontend-Job verschiebt/löscht — genau der stille Rückfall, den AK4
verhindern soll. Ein echter CI-Lauf mit tatsächlich erfolgreichem Login
bleibt zusätzlich Teil der bestehenden Frontend-Check-Verifikation selbst
(dieser Test prüft nur die statische Struktur, nicht das Laufzeitergebnis).
"""
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _find_deploy_yml() -> Path:
    """Sucht .github/workflows/deploy.yml ab dieser Testdatei aufwärts.

    Bewusst pfad-robust (statt fester Parent-Zählung wie `.parent.parent...`):
    die Tiefe zwischen backend/tests/ und dem Repo-Root unterscheidet sich
    zwischen einer isolierten Arbeitskopie (z. B. _worktrees/TASK-97/) und dem
    vollständigen Repo (…/FotoAlert/FotoAlert/backend/tests/ mit .github/ zwei
    Ebenen über FotoAlert/) — die Suche funktioniert in beiden Fällen.
    """
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parent.parents):
        candidate = parent / ".github" / "workflows" / "deploy.yml"
        if candidate.exists():
            return candidate
    raise AssertionError(
        ".github/workflows/deploy.yml wurde ausgehend von {0} in keinem "
        "übergeordneten Verzeichnis gefunden — Grundannahme des Guard-Checks "
        "verletzt.".format(here)
    )


def _read_deploy_yml() -> str:
    return _find_deploy_yml().read_text(encoding="utf-8")


_TEST_FRONTEND_JOB = "test-frontend:"
_TEST_BACKEND_JOB = "test-backend:"
_ENV_LINE = "FOTOALERT_ENV: dev"


def test_test_frontend_job_exists():
    """Grundannahme des Guard-Checks: der Job selbst existiert weiterhin."""
    source = _read_deploy_yml()
    assert _TEST_FRONTEND_JOB in source, (
        "Job {0!r} nicht (mehr) in deploy.yml gefunden — Grundannahme des "
        "Guard-Checks verletzt.".format(_TEST_FRONTEND_JOB)
    )


def test_fotoalert_env_dev_stays_in_test_frontend_job():
    """AK4: FOTOALERT_ENV: dev bleibt im env-Block des test-frontend-Jobs.

    Ohne dieses Flag setzt backend/main.py (_COOKIE_SECURE) das Sitzungscookie
    mit Secure-Flag — über reines HTTP im CI-Job wird ein solches Cookie vom
    Browser verworfen, und der Login-Precondition-Check schlägt mit demselben
    Symptom fehl wie in CI-Run #277 (Auth.isLoggedIn() bleibt false).
    """
    source = _read_deploy_yml()

    frontend_idx = source.find(_TEST_FRONTEND_JOB)
    assert frontend_idx != -1, (
        "Job {0!r} nicht in deploy.yml gefunden — Grundannahme des "
        "Guard-Checks verletzt.".format(_TEST_FRONTEND_JOB)
    )

    backend_idx = source.find(_TEST_BACKEND_JOB, frontend_idx)
    assert backend_idx != -1, (
        "Job {0!r} nicht nach {1!r} in deploy.yml gefunden — Grundannahme "
        "des Guard-Checks verletzt.".format(_TEST_BACKEND_JOB, _TEST_FRONTEND_JOB)
    )
    assert frontend_idx < backend_idx, (
        "Erwartete Reihenfolge {0!r} vor {1!r} nicht gegeben — Grundannahme "
        "des Guard-Checks verletzt.".format(_TEST_FRONTEND_JOB, _TEST_BACKEND_JOB)
    )

    window = source[frontend_idx:backend_idx]
    assert _ENV_LINE in window, (
        "{0!r} fehlt (oder wurde geändert) im env-Block des {1!r}-Jobs in "
        "deploy.yml — TASK-97/TASK-83-Regression: ohne dieses Flag würde "
        "backend/main.py (_COOKIE_SECURE) das Sitzungscookie im CI-Dev-Job "
        "mit Secure-Flag setzen, das über reines HTTP verworfen wird "
        "(exaktes Symptom von CI-Run #277: Auth.isLoggedIn() bleibt "
        "false).".format(_ENV_LINE, _TEST_FRONTEND_JOB)
    )
