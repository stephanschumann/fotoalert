"""TASK-60 — Regressionstest für die Aufrufreihenfolge nach dem Refactoring von
patch_location() (backend/main.py) in vier Helferfunktionen.

Pre-Mortem-Szenario 1 (BACKLOG.md TASK-60): Wird die Feld-Validierung
(_validate_patch_fields()) versehentlich erst NACH dem target_loc-Lookup aufgerufen,
kippt die Fehlerantwort für PATCH-Requests mit ungültigen Feldwerten gegen eine
nicht-existente loc_id von 422 auf 404 — ein stiller Verhaltenswechsel, kein Crash.
Kein bestehender Test kombinierte bislang "ungültiges Feld" + "nicht-existente
Location" (per Grep in backend/tests/ geprüft, siehe Ticket-Spec/Code-Verifikation).

Konvention (vgl. test_us_128.py/test_bug-61.py): API-Tests laufen gegen den
FastAPI-TestClient (conftest.py, client-Fixture). Kein hartcodierter Location-Fixture
nötig — die relevanten Fälle nutzen bewusst eine nicht-existente loc_id.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]

_NONEXISTENT_LOC_ID = "does_not_exist_task60"


class TestTask60ValidationBeforeExistenceCheck:
    """TASK-60 AK: Prüfreihenfolge bleibt exakt erhalten — Feld-Validierung (422)
    läuft VOR dem Existenz-Check der Location (404)."""

    def test_invalid_coord_on_nonexistent_location_returns_422_not_404(self, client, auth_headers):
        resp = client.patch(
            f"/locations/{_NONEXISTENT_LOC_ID}",
            json={"observer_lat": 999},
            headers=auth_headers,
        )
        assert resp.status_code == 422, resp.text

    def test_invalid_focal_length_on_nonexistent_location_returns_422_not_404(self, client, auth_headers):
        """Zweite, unabhängige Validierungsart (Liste statt Zahl) gegen denselben
        Pre-Mortem-Fall — deckt _validate_patch_fields() über mehr als einen
        Codepfad ab."""
        resp = client.patch(
            f"/locations/{_NONEXISTENT_LOC_ID}",
            json={"focal_length_suggestions": [9999]},
            headers=auth_headers,
        )
        assert resp.status_code == 422, resp.text

    def test_valid_field_on_nonexistent_location_still_returns_404(self, client, auth_headers):
        """Gegenprobe: ohne Validierungsfehler bleibt der 404-Pfad für eine
        nicht-existente Location unverändert erreichbar (kein Kollateralschaden
        durch die neue Aufrufreihenfolge/Helferfunktionen)."""
        resp = client.patch(
            f"/locations/{_NONEXISTENT_LOC_ID}",
            json={"name": "Irrelevanter Name"},
            headers=auth_headers,
        )
        assert resp.status_code == 404, resp.text
