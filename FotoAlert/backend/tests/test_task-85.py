"""TASK-85 — Harter Serverstart-Abbruch bei fehlendem FOTOALERT_AUTH_SECRET.

Ziel (Option A, Spec bestätigt): Der bisherige Notwert-String
("fotoalert-dev-secret-change-me") wurde aus auth.py entfernt. Fehlt
FOTOALERT_AUTH_SECRET beim Modul-Laden von auth.py (nicht gesetzt ODER leer),
bricht der Import sofort mit einer klaren RuntimeError-Meldung ab — main.py
importiert auth.py ganz am Anfang, ein Abbruch dort verhindert also, dass
irgendein Endpunkt erreichbar wird.

Der laufende pytest-Prozess selbst hat auth.py bereits (mit gültigem
Test-Secret aus conftest.py) importiert und im sys.modules-Cache — ein
erneutes `import auth` im selben Prozess würde NICHT erneut ausgeführt,
selbst wenn os.environ zwischenzeitlich manipuliert wird. Deshalb wird das
Abbruchverhalten in einem frischen Subprozess geprüft (echter, unverfälschter
Modul-Ladevorgang), nicht durch Cache-Trickserei im Testprozess.
"""
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _run_import_auth(env_overrides: dict) -> subprocess.CompletedProcess:
    """Importiert auth.py in einem frischen Subprozess mit gezielt gesetzter Umgebung.

    env_overrides steuert NUR FOTOALERT_AUTH_SECRET; alle anderen Variablen des
    aktuellen Prozesses (z.B. PATH, PYTHONPATH-relevante Dinge) bleiben erhalten,
    damit der Subprozess dieselbe Python-Umgebung/venv nutzt wie der Testlauf.
    """
    import os

    env = dict(os.environ)
    for key, value in env_overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value

    return subprocess.run(
        [sys.executable, "-c", "import auth"],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestAuthSecretHardAbort:
    def test_missing_secret_aborts_import(self):
        """FOTOALERT_AUTH_SECRET gar nicht gesetzt -> Abbruch mit klarer Meldung."""
        result = _run_import_auth({"FOTOALERT_AUTH_SECRET": None})
        assert result.returncode != 0, (
            f"Import haette abbrechen muessen. stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "RuntimeError" in result.stderr
        assert "FOTOALERT_AUTH_SECRET" in result.stderr

    def test_empty_secret_aborts_import(self):
        """FOTOALERT_AUTH_SECRET gesetzt, aber leerer String -> genauso wie fehlend behandelt."""
        result = _run_import_auth({"FOTOALERT_AUTH_SECRET": ""})
        assert result.returncode != 0, (
            f"Import haette abbrechen muessen. stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "RuntimeError" in result.stderr
        assert "FOTOALERT_AUTH_SECRET" in result.stderr

    def test_set_secret_imports_and_works_normally(self):
        """Gesetztes Geheimnis (beliebiger Wert) -> Import gelingt, Token-Rundlauf funktioniert."""
        result = _run_import_auth({"FOTOALERT_AUTH_SECRET": "irgendein-wert"})
        assert result.returncode == 0, (
            f"Import haette gelingen muessen. stdout={result.stdout!r} stderr={result.stderr!r}"
        )

    def test_no_leftover_fallback_string_in_source(self):
        """Der alte Notwert-String darf im Programmcode nirgends mehr vorkommen."""
        source = (BACKEND_DIR / "auth.py").read_text(encoding="utf-8")
        assert "fotoalert-dev-secret-change-me" not in source

    def test_set_secret_login_flow_still_works(self, client):
        """API-Ebene: mit gesetztem Test-Secret (conftest.py) funktioniert Login wie zuvor.

        Läuft im Haupt-Testprozess (nicht im Subprozess) über die bestehende
        `client`-Fixture, die main.py bereits mit dem in conftest.py gesetzten
        Test-Secret importiert hat.
        """
        r = client.post("/login", json={"password": "test-user-pw"})
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "user"
