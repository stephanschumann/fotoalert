"""TASK-89: Caddy-Logdatei-Berechtigung bei Server-Neuaufbau prüfen/absichern.

Reiner Text-/Grep-Check gegen deploy/setup_server.sh. Verifiziert NICHT das
tatsächliche Server-Verhalten (das zeigt sich erst bei einem echten
Server-Neuaufbau) — sondern nur, dass das Skript den vorsorglichen
mkdir/touch/chown-Block für /var/log/caddy VOR dem Caddy-Reload enthält, damit
`caddy validate` (root) die Logdatei aus deploy/Caddyfile nie mehr mit
root-Besitzrechten anlegen kann, bevor der unprivilegierte "caddy"-User sie
öffnet (siehe BACKLOG.md TASK-89 / Fund aus TASK-82-Testphase).

TASK-96-Hinweis: Diese Datei ist trotz `offline`-Markierung NICHT teil-checkout-faehig -
DEPLOY_DIR loest einen Pfad relativ zum Repo-Root ausserhalb von backend/ auf und bricht
deshalb bei einem Checkout, der nur backend/ enthaelt. Deshalb zusaetzlich mit
`requires_full_checkout` markiert (siehe backend/tests/README.md).
"""

import re
from pathlib import Path

import pytest

# TASK-96: DEPLOY_DIR loest hier bewusst ausserhalb von backend/ auf (Repo-Root) -
# deshalb Modul-weiter `requires_full_checkout`-Marker unten zusaetzlich zu `offline`.
DEPLOY_DIR = Path(__file__).resolve().parents[2] / "deploy"
SETUP_SCRIPT = DEPLOY_DIR / "setup_server.sh"

pytestmark = pytest.mark.requires_full_checkout


@pytest.fixture(scope="module")
def setup_script_text() -> str:
    assert SETUP_SCRIPT.exists(), f"deploy/setup_server.sh nicht gefunden unter {SETUP_SCRIPT}"
    return SETUP_SCRIPT.read_text(encoding="utf-8")


@pytest.mark.offline
@pytest.mark.regression
def test_creates_caddy_log_dir_with_correct_owner(setup_script_text: str) -> None:
    """setup_server.sh muss /var/log/caddy anlegen und caddy:caddy zuweisen."""
    assert "mkdir -p /var/log/caddy" in setup_script_text
    assert re.search(r"chown\s+-R\s+caddy:caddy\s+/var/log/caddy", setup_script_text), (
        "Erwarte 'chown -R caddy:caddy /var/log/caddy' im Skript, "
        "damit die Caddy-Logdatei nicht mit root-Rechten entsteht."
    )


@pytest.mark.offline
@pytest.mark.regression
def test_log_dir_fix_runs_before_caddy_reload(setup_script_text: str) -> None:
    """Der chown-Block muss VOR dem Caddy-Reload/-Restart stehen.

    Sonst könnte ein `caddy validate`/reload-Aufruf die Logdatei bereits vor
    der Korrektur root-owned anlegen (Reihenfolge ist der eigentliche Kern
    des TASK-89-Fixes, nicht nur die reine Anwesenheit der Befehle).
    """
    chown_pos = setup_script_text.find("chown -R caddy:caddy /var/log/caddy")
    reload_pos = setup_script_text.find("systemctl reload caddy")

    assert chown_pos != -1, "chown-Fix für /var/log/caddy fehlt im Skript."
    assert reload_pos != -1, "'systemctl reload caddy'-Aufruf fehlt im Skript."
    assert chown_pos < reload_pos, (
        "Der chown-Fix für /var/log/caddy muss vor dem Caddy-Reload im Skript stehen."
    )


@pytest.mark.offline
@pytest.mark.regression
def test_log_dir_fix_runs_after_caddy_package_install(setup_script_text: str) -> None:
    """Der chown-Block darf erst NACH der Caddy-Paketinstallation laufen.

    Andernfalls existiert der System-User 'caddy' (angelegt vom apt-Paket)
    zum Zeitpunkt des chown noch nicht -> Skript bricht wegen `set -euo
    pipefail` an dieser Stelle hart ab (Pre-Mortem-Szenario 1 aus der
    TASK-89-Analyse).
    """
    caddy_install_pos = setup_script_text.find("apt-get install -y -qq caddy")
    chown_pos = setup_script_text.find("chown -R caddy:caddy /var/log/caddy")

    assert caddy_install_pos != -1, "Caddy-apt-Installationszeile nicht gefunden."
    assert chown_pos != -1, "chown-Fix für /var/log/caddy fehlt im Skript."
    assert caddy_install_pos < chown_pos, (
        "Die Caddy-Paketinstallation (die den System-User 'caddy' anlegt) muss "
        "vor dem chown-Fix stehen, sonst existiert der User noch nicht."
    )
