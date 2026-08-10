"""API-Smoke-Test gegen den FastAPI-Stack (data_dev, nie Prod).

Die `client`-Fixture liegt zentral in conftest.py und wird von allen API-Tests geteilt.
Sie überspringt sauber, wenn der Stack fehlt oder der Startup im Sandbox scheitert.
"""
import pytest

pytestmark = [pytest.mark.api]


@pytest.mark.smoke
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"
    assert "version" in body


@pytest.mark.smoke
def test_health_version_is_backend_schema_constant(client):
    """Regressionsschutz (TASK-95): /health.version ist die Backend-/API-
    Schemaversion (main.BACKEND_API_SCHEMA_VERSION), NICHT die App-Release-
    Version aus web/index.html (APP_VERSION). Beide Versionsbegriffe wurden
    vor TASK-95 leicht verwechselt; dieser Test schuetzt davor, dass ein
    kuenftiges Refactoring das /health-Feld versehentlich an APP_VERSION
    koppelt oder die Konstante aus main.py entfernt.
    """
    import main as backend_main

    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("version") == backend_main.BACKEND_API_SCHEMA_VERSION
