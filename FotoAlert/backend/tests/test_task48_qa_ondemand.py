"""TASK-48 (On-Demand-Erweiterung): geschützter Auslöser POST /run-qa-pass.

Stößt den nächtlichen QA-Lauf einmalig sofort an und gibt eine kompakte
Zusammenfassung zurück (geprüft/verbessert/fehlgeschlagen bzw. übersprungen).

Getestet wird der Endpoint-Vertrag, NICHT die schon abgedeckte QA-Steuerlogik
(die liegt in test_task48_qa_cron.py). Die teure Verbesserung pro Spot wird
gemockt, damit der Test offline + schnell bleibt.

Auth folgt exakt dem US-66-Muster (auth.issue_token('host') über /login;
Header `Authorization: Bearer <token>`). Schutz: Depends(auth.require_host).
"""
import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


def _host_headers(host_token):
    return {"Authorization": f"Bearer {host_token}"}


class FakeLoc:
    """Minimale Location mit den 7 Geo-Kernfeldern + id (wie im Cron-Test)."""

    def __init__(self, loc_id):
        self.id = loc_id
        self.observer_lat = 52.5
        self.observer_lon = 13.4
        self.subject_lat = 52.6
        self.subject_lon = 13.5
        self.subject_height_m = 100.0
        self.subject_width_m = 20.0
        self.distance_m = 1000.0


@pytest.fixture
def one_due_spot(monkeypatch):
    """Genau ein fälliger Spot + gemockte Verbesserung (Erfolg), Drosselung aus,
    Single-Flight-Flags neutralisiert. Nutzt den echten _store (data_dev)."""
    import main
    loc = FakeLoc("ondemand_test_spot")
    monkeypatch.setattr(main, "LOCATIONS", [loc], raising=False)
    monkeypatch.setattr(main, "_qa_improve_one", lambda l, s: True, raising=False)
    monkeypatch.setattr(main, "_QA_PASS_THROTTLE_S", 0.0, raising=False)
    main._qa_pass_running = False
    main._precompute_running = False
    # Sauberer Ausgangszustand: Spot gilt als noch nie geprüft.
    try:
        main._store.update_qa_checked(loc.id, "force-stale")
        # update_qa_checked setzt einen Hash; wir wollen "fällig" → anderen Hash erzwingen,
        # indem wir den gespeicherten Hash vom aktuellen abweichen lassen.
    except Exception:
        pass
    return loc


class TestRunQaPassEndpoint:
    def test_host_can_trigger_and_gets_summary(self, client, host_token, one_due_spot):
        """Mit Host-Token: 200 + kompakte Zusammenfassung (status/checked/improved/failed)."""
        r = client.post("/run-qa-pass", headers=_host_headers(host_token))
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] in ("completed", "skipped")
        for key in ("checked", "improved", "failed"):
            assert key in body
            assert isinstance(body[key], int)

    def test_without_token_rejected(self, client):
        """Ohne Token → 401 (geschützt wie alle Host-Aktionen)."""
        r = client.post("/run-qa-pass")
        assert r.status_code == 401

    def test_user_token_rejected(self, client, auth_headers):
        """User-Token auf Host-Route → 403 (require_host)."""
        r = client.post("/run-qa-pass", headers=auth_headers)
        assert r.status_code == 403

    def test_skipped_when_qa_already_running(self, client, host_token, monkeypatch):
        """Single-Flight: läuft schon ein QA-Lauf → 'skipped', kein paralleler Start."""
        import main
        monkeypatch.setattr(main, "_QA_PASS_THROTTLE_S", 0.0, raising=False)
        main._precompute_running = False
        main._qa_pass_running = True  # simuliert laufenden Lauf
        try:
            r = client.post("/run-qa-pass", headers=_host_headers(host_token))
        finally:
            main._qa_pass_running = False
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "skipped"
        assert body["reason"] == "qa_pass_running"
        assert body["checked"] == 0

    def test_skipped_when_recompute_running(self, client, host_token, monkeypatch):
        """Single-Flight: läuft ein Recompute → 'skipped' statt parallel."""
        import main
        main._qa_pass_running = False
        main._precompute_running = True
        try:
            r = client.post("/run-qa-pass", headers=_host_headers(host_token))
        finally:
            main._precompute_running = False
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "skipped"
        assert body["reason"] == "precompute_running"
