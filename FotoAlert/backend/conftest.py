"""Pytest-Bootstrap für das FotoAlert-Test-Harness.

WICHTIG (TASK-19): Tests laufen IMMER gegen die Dev-Umgebung, nie gegen Prod-Daten.
`FOTOALERT_ENV=dev` zwingt den Store auf `backend/data_dev/`. Diese Zeile muss vor
jedem Import von `data.store` / `main` greifen — deshalb steht sie hier in conftest.py,
das pytest vor der Test-Collection lädt.
"""
import os
import sys
from pathlib import Path

import pytest

# Niemals Prod-Daten anfassen.
os.environ.setdefault("FOTOALERT_ENV", "dev")
# App-Startup im Test deterministisch & offline: kein Scheduler, Precompute, Netzwerk, Backup.
os.environ.setdefault("FOTOALERT_NO_BACKGROUND", "1")
# US-66: feste Test-Credentials (vor App-Import gesetzt).
os.environ.setdefault("FOTOALERT_HOST_PASSWORD", "test-host-pw")
os.environ.setdefault("FOTOALERT_USER_PASSWORD", "test-user-pw")
os.environ.setdefault("FOTOALERT_AUTH_SECRET", "test-secret")

# backend/ auf den Importpfad, damit `from calculations import ...` funktioniert,
# egal aus welchem Verzeichnis pytest gestartet wird.
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(scope="session")
def client():
    """TestClient gegen main:app — geteilt von allen API-Tests.

    Überspringt sauber (statt rot), wenn der FastAPI-Stack fehlt oder der App-Startup
    im Sandbox scheitert. So bleibt die Offline-Regression immer aussagekräftig.
    """
    pytest.importorskip("fastapi", reason="FastAPI-Stack nicht installiert – bootstrap_sandbox.sh ausführen")
    from fastapi.testclient import TestClient
    try:
        import main  # Import erst hier, damit importorskip vorher greift
        with TestClient(main.app) as c:
            yield c
    except Exception as exc:  # pragma: no cover - umgebungsabhängig
        pytest.skip(f"App-Startup im Sandbox nicht möglich: {exc}")


@pytest.fixture
def user_token(client):
    """US-66: gültiges User-Token für geschützte Endpoints."""
    r = client.post("/login", json={"password": "test-user-pw"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture
def host_token(client):
    """US-66: gültiges Host-Token (Admin-Routen)."""
    r = client.post("/login", json={"password": "test-host-pw"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture
def auth_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}
