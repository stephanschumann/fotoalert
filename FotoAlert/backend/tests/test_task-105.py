"""TASK-105 — Python-3.9-EOL blockiert Sicherheitsfixes fuer 4 von 7 TASK-104-Paketen.

Diese Datei deckt NICHT die eigentliche Migration ab (die ist Gegenstand der noch
ausstehenden Implementierungs-Phase, siehe Ampel-Ergebnis: Rot, wartet auf Stephans
Entscheidung ueber Zielversion + Reihenfolge). Sie haelt stattdessen als textbasierte,
dateiinhalt-gepruefte Regressionstests genau die drei Stellen fest, die beim
tatsaechlichen Python-Sprung zwingend im selben Zug mitgeaendert werden muessen
(siehe Pre-Mortem-Szenarien 3/4/5 in BACKLOG.md TASK-105) — sonst driften
CI/Prod/lokale Entwicklungsumgebung auseinander (real bereits einmal passiert:
TASK-83, v1.22.42, GitHub-Actions-Run #253, `asyncio.Semaphore`-Verhaltensunterschied
Python 3.9 vs. 3.10+).

Rot-Nachweis (2026-08-13, echt ausgefuehrt als reines Text-/Regex-Skript ausserhalb
von pytest, da im Analyse-Sandbox kein `pytest`-Modul verfuegbar war): alle drei
Pruefungen schlagen gegen den aktuellen Code-Stand erwartungsgemaess fehl —
`pandas` hat weiterhin keine Obergrenze, beide GitHub-Workflow-Dateien pinnen
weiterhin `python-version: "3.9"`, CLAUDE.md behauptet weiterhin
"Server laeuft **Python 3.9**". Das wird erst gruen, wenn die eigentliche
Migration umgesetzt ist — bewusst rot markiert, kein Implementierungsfehler.

Marker `requires_full_checkout`, da diese Tests Pfade ausserhalb von backend/
(.github/workflows/, CLAUDE.md) auflösen (TASK-96-Konvention).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

FOTOALERT_DIR = Path(__file__).resolve().parents[2]  # .../FotoAlert (App-Ordner)
REPO_ROOT = Path(__file__).resolve().parents[3]  # Repo-Wurzel (enthaelt .github/)

REQUIREMENTS_FILE = FOTOALERT_DIR / "backend" / "requirements.txt"
CLAUDE_MD = FOTOALERT_DIR / "CLAUDE.md"
CI_WORKFLOWS = [
    REPO_ROOT / ".github" / "workflows" / "deploy.yml",
    REPO_ROOT / ".github" / "workflows" / "update-building-data.yml",
]

# TODO(TASK-105-Umsetzung): Sobald Stephan die Zielversion bestaetigt hat
# (Empfehlung der Analyse: 3.12, siehe BACKLOG.md TASK-105), hier einsetzen statt
# nur "nicht mehr 3.9" zu pruefen.
TARGET_PYTHON_VERSION = None  # wird von der Implementierung gesetzt/verifiziert


class TestTask105PythonVersionMigrationConsistency:
    """AK4/AK5/AK6: kein Environment-Drift, keine ungeplanten Mit-Upgrades."""

    def test_ak6_pandas_pin_has_explicit_upper_bound(self):
        """AK6 Edge Case: `pandas` darf beim Python-Sprung nicht ungeprueft auf eine
        neue Hauptversion springen (echter Fund: unter Python 3.12 loest
        `pandas>=2.0.0` auf 3.0.5 auf, waehrend das aktuelle Python-3.9-venv 2.3.3
        installiert hat — siehe Pre-Mortem Szenario 3)."""
        text = REQUIREMENTS_FILE.read_text(encoding="utf-8")
        match = re.search(r"^pandas(\S*)", text, re.MULTILINE)
        assert match, "pandas-Zeile nicht in requirements.txt gefunden"
        pin = match.group(1)
        assert "<" in pin, (
            f"pandas hat weiterhin keine Obergrenze ({pin!r}) — ein Python-Sprung "
            "wuerde ungeprueft pandas 3.x mitziehen (siehe Pre-Mortem Szenario 3)."
        )

    def test_ak4_both_github_workflows_pin_same_non_39_python_version(self):
        """AK4: CI darf nicht auf Python 3.9 pinnen, wenn Prod/lokal bereits
        gewechselt haben — UND beide Workflow-Dateien muessen konsistent sein
        (Pre-Mortem Szenario 4: `update-building-data.yml` wird leicht vergessen,
        wenn nur `deploy.yml` angepasst wird)."""
        pins = set()
        for wf in CI_WORKFLOWS:
            text = wf.read_text(encoding="utf-8")
            found = re.findall(r'python-version:\s*"([^"]+)"', text)
            assert found, f"kein python-version-Pin in {wf.name} gefunden"
            pins.update(found)
            assert "3.9" not in found, (
                f"{wf.name} pinnt weiterhin Python 3.9 — TASK-105-Migration "
                "noch nicht umgesetzt oder diese Datei wurde vergessen."
            )
        assert len(pins) == 1, (
            f"GitHub-Workflows pinnen unterschiedliche Python-Versionen ({pins}) — "
            "CI-Umgebungen driften auseinander (Pre-Mortem Szenario 4)."
        )

    def test_ak5_claude_md_hard_rule_updated(self):
        """AK5: die als harte Projektregel in CLAUDE.md §5 dokumentierte Aussage
        "Server laeuft Python 3.9" muss nach der Migration aktualisiert sein —
        sonst widerspricht die verbindliche Projektdoku dem echten Server-Stand."""
        text = CLAUDE_MD.read_text(encoding="utf-8")
        assert "Server läuft **Python 3.9**" not in text, (
            "CLAUDE.md behauptet weiterhin 'Server läuft Python 3.9' — "
            "nach der TASK-105-Migration muss diese harte Projektregel auf die "
            "tatsächlich verwendete Version aktualisiert werden."
        )
