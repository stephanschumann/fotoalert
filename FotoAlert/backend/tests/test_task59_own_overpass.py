"""
Tests für TASK-59: Optionaler eigener Overpass-Server (Code-Vorbereitung).

Der eigene Server existiert noch NICHT — Stephan baut ihn erst separat auf.
Diese Tests decken ausschließlich die Code-Vorbereitung in
`backend/data/qa_azimuth.py` ab, komplett gemockt (kein echtes Netzwerk):

- Regressionsschutz: OWN_OVERPASS_URL nicht gesetzt (heutiger Zustand, bis der
  Server existiert) -> exakt dieselbe Mirror-Reihenfolge/Timeouts wie vor
  TASK-59.
- OWN_OVERPASS_URL gesetzt -> wird zuerst versucht; schlägt sie fehl, fällt
  der Code automatisch auf die bestehenden OVERPASS_MIRRORS zurück (von
  Stephan bestätigte Fallback-Entscheidung, TASK-59 Frage 2).
- Antwortet der eigene Server erfolgreich, werden die Mirrors gar nicht erst
  angefragt.
- Schlägt speziell die Anfrage an den eigenen Server fehl, entsteht eine
  unterscheidbare Log-Meldung (Grundlage für eine spätere aktive
  Benachrichtigung — kein Alert-Versand ist Teil dieses Tickets).

Python-3.9-kompatibel.
"""
from __future__ import annotations

from pathlib import Path
import sys

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data import qa_azimuth

pytestmark = [pytest.mark.offline, pytest.mark.regression]

_OWN_URL = "https://own-overpass.example.internal/api/interpreter"


class _RecordingFailClient:
    """Fake httpx.Client: merkt sich die angefragten URLs, schlägt immer fehl
    -> _fetch_from_mirrors() durchläuft die volle Reihenfolge."""

    calls: list = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, data=None):
        _RecordingFailClient.calls.append(url)
        raise httpx.ConnectError("simulierter Verbindungsfehler")


class _SuccessClient:
    """Fake httpx.Client: antwortet beim ersten Aufruf sofort erfolgreich."""

    calls: list = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, data=None):
        _SuccessClient.calls.append(url)

        class _Resp:
            def raise_for_status(self_inner):
                return None

            def json(self_inner):
                return {"elements": []}

        return _Resp()


@pytest.fixture(autouse=True)
def _no_rate_limit_sleep(monkeypatch):
    """Rate-Limiting selbst ist nicht Gegenstand von TASK-59 — hier nur
    entkoppeln, damit die Tests nicht durch echtes time.sleep() verlangsamt
    werden."""
    monkeypatch.setattr(qa_azimuth, "_respect_overpass_rate_limit", lambda: None)


def test_ohne_own_overpass_url_bleibt_mirror_reihenfolge_unveraendert(monkeypatch):
    """Regressionsschutz (Pflicht, TASK-59): OWN_OVERPASS_URL nicht gesetzt
    (Default, heutiger Zustand bis der Server existiert) -> _fetch_from_mirrors()
    ruft exakt OVERPASS_MIRRORS in derselben Reihenfolge auf wie vor TASK-59 —
    keine zusätzliche eigene-Server-Anfrage."""
    monkeypatch.setattr(qa_azimuth, "OWN_OVERPASS_URL", None)
    _RecordingFailClient.calls = []
    monkeypatch.setattr(httpx, "Client", _RecordingFailClient)

    result = qa_azimuth._fetch_from_mirrors("fake-query", 5.0, "test-context")

    assert result is None
    assert _RecordingFailClient.calls == qa_azimuth.OVERPASS_MIRRORS


def test_own_overpass_url_gesetzt_wird_zuerst_versucht_dann_mirror_fallback(monkeypatch):
    """TASK-59 Kernverhalten: Ist OWN_OVERPASS_URL gesetzt, wird sie zuerst
    angefragt. Schlägt sie fehl, fällt der Code automatisch auf die
    bestehenden OVERPASS_MIRRORS zurück (Ausfallverhalten-Variante
    "öffentliche Server bleiben Rückfallebene", von Stephan bestätigt)."""
    monkeypatch.setattr(qa_azimuth, "OWN_OVERPASS_URL", _OWN_URL)
    _RecordingFailClient.calls = []
    monkeypatch.setattr(httpx, "Client", _RecordingFailClient)

    result = qa_azimuth._fetch_from_mirrors("fake-query", 5.0, "test-context")

    assert result is None
    assert _RecordingFailClient.calls == [_OWN_URL] + qa_azimuth.OVERPASS_MIRRORS


def test_own_overpass_url_erfolgreich_mirrors_werden_nicht_angefragt(monkeypatch):
    """Antwortet der eigene Server erfolgreich, werden die Mirrors gar nicht
    erst kontaktiert."""
    monkeypatch.setattr(qa_azimuth, "OWN_OVERPASS_URL", _OWN_URL)
    _SuccessClient.calls = []
    monkeypatch.setattr(httpx, "Client", _SuccessClient)

    result = qa_azimuth._fetch_from_mirrors("fake-query", 5.0, "test-context")

    assert result == {"elements": []}
    assert _SuccessClient.calls == [_OWN_URL]


def test_own_overpass_fehlschlag_erzeugt_unterscheidbare_log_meldung(monkeypatch, caplog):
    """TASK-59: Schlägt speziell die Anfrage an den eigenen Server fehl, muss
    eine unterscheidbare Log-Meldung entstehen (Grundlage für eine spätere
    aktive Benachrichtigung — kein Alert-Versand ist Teil dieses Tickets)."""
    monkeypatch.setattr(qa_azimuth, "OWN_OVERPASS_URL", _OWN_URL)
    monkeypatch.setattr(httpx, "Client", _RecordingFailClient)
    _RecordingFailClient.calls = []

    with caplog.at_level("INFO", logger="data.qa_azimuth"):
        qa_azimuth._fetch_from_mirrors("fake-query", 5.0, "test-context")

    own_server_logs = [r for r in caplog.records if _OWN_URL in r.getMessage()]
    assert len(own_server_logs) == 1
    assert own_server_logs[0].levelname == "WARNING"
    # Muss von den generischen Mirror-Fehlschlag-Logs (INFO) unterscheidbar
    # bleiben, damit eine spätere Alert-Logik gezielt danach filtern kann.
    mirror_logs = [r for r in caplog.records
                   if r.levelname == "INFO" and r.getMessage().startswith("Overpass-Mirror ")]
    assert len(mirror_logs) == len(qa_azimuth.OVERPASS_MIRRORS)


def test_own_overpass_url_leer_string_wird_wie_nicht_gesetzt_behandelt(monkeypatch):
    """Edge Case: ein leerer String (z.B. gesetzte, aber leere Env-Var) muss
    denselben Effekt wie None haben — kein versehentlicher Versuch gegen eine
    leere URL."""
    monkeypatch.setattr(qa_azimuth, "OWN_OVERPASS_URL", "")
    _RecordingFailClient.calls = []
    monkeypatch.setattr(httpx, "Client", _RecordingFailClient)

    qa_azimuth._fetch_from_mirrors("fake-query", 5.0, "test-context")

    assert _RecordingFailClient.calls == qa_azimuth.OVERPASS_MIRRORS
