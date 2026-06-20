"""API-Smoke-Test gegen den FastAPI-Stack (data_dev, nie Prod).

Die `client`-Fixture liegt zentral in conftest.py und wird von allen API-Tests geteilt.
Sie überspringt sauber, wenn der Stack fehlt oder der Startup im Sandbox scheitert.
"""
import pytest

pytestmark = [pytest.mark.api]


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"
    assert "version" in body
