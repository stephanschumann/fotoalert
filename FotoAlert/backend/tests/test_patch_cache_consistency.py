"""TASK-34 — Cache-Konsistenz nach PATCH /locations/{id}.

Absicherung der Root-Cause von BUG-29 / BUG-30: nach einem Koordinaten- oder
Name-PATCH müssen die API-Endpoints die neuen Werte zurückliefern — nicht die
alten Basis-Werte aus data/locations.py.

Konvention (vgl. test_astronomy_regression.py):
  - Jeder Test nennt im Docstring die Ticket-ID, deren AK er absichert.
  - `pytestmark = offline` wo kein Netz/Ephemeriden nötig ist.
  - API-Tests laufen gegen den FastAPI-TestClient (conftest.py, client-Fixture).

Warum diese Tests?
  BUG-29 Root-Cause: precompute.py lud Basis-Koordinaten aus data/locations.py
  und ignorierte SQLite-Overrides. Folge: Nach PATCH mit neuen Koordinaten zeigten
  Kalender und Feed weiter die alten Werte. Der coordinates_hash blieb gleich →
  "0 neu berechnet" im Log, keine Fehlermeldung.
  BUG-30: PATCH auf `name` persistierte nicht korrekt (Override-Merge-Lücke).

  Diese Tests stellen sicher, dass PATCH → GET immer konsistent ist.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]

# Custom-Location aus data_dev (via TASK-19-Seed).
# Muss in data_dev vorhanden sein — wird in conftest.py auf dev-Umgebung festgelegt.
LOC = "custom_1781560330"


class TestBug30NamePersistence:
    """BUG-30: PATCH auf `name` muss nach GET sichtbar sein.

    AK: Nach PATCH {"name": "X"} liefert GET /locations für diese ID name == "X".
    AK: description und andere Felder bleiben unverändert (Override-Merge ersetzt nicht überschreibt).
    AK: Erneuter PATCH {"name": "Y"} überschreibt, GET liefert "Y" (kein Append-Bug).
    """

    def test_name_patch_visible_in_get(self, client, auth_headers):
        """BUG-30 AK: PATCH name → GET locations gibt neuen Namen zurück."""
        new_name = "BUG30-Test-Standort"
        r = client.patch(f"/locations/{LOC}", json={"name": new_name}, headers=auth_headers)
        assert r.status_code == 200, f"PATCH fehlgeschlagen: {r.text}"

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == LOC), None)
        assert loc is not None, f"Location {LOC} nicht in GET /locations gefunden"
        assert loc["name"] == new_name, (
            f"Name nach PATCH: '{loc['name']}' — erwartet: '{new_name}'. "
            f"Mögliche Regression von BUG-30 (Override-Merge-Lücke)."
        )

    def test_name_patch_does_not_overwrite_other_fields(self, client, auth_headers):
        """BUG-30 AK: PATCH name lässt description unberührt (Merge, kein Replace)."""
        # Erst description setzen
        desc = "Test-Beschreibung bleibt erhalten"
        client.patch(f"/locations/{LOC}", json={"description": desc}, headers=auth_headers)

        # Dann nur name patchen
        client.patch(f"/locations/{LOC}", json={"name": "Nur-Name-Patch"}, headers=auth_headers)

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == LOC), None)
        assert loc is not None
        assert loc.get("description") == desc, (
            f"Description nach reinem Name-PATCH verändert: '{loc.get('description')}'. "
            "Regression von BUG-30 Override-Merge."
        )

    def test_second_name_patch_overwrites_first(self, client, auth_headers):
        """BUG-30 AK: Zweiter Name-PATCH überschreibt den ersten (kein Append-Bug)."""
        client.patch(f"/locations/{LOC}", json={"name": "Erster Name"}, headers=auth_headers)
        client.patch(f"/locations/{LOC}", json={"name": "Zweiter Name"}, headers=auth_headers)

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == LOC), None)
        assert loc is not None
        assert loc["name"] == "Zweiter Name", (
            f"Erwartet 'Zweiter Name', bekam '{loc['name']}'. Append-Regression."
        )


class TestBug29CoordinatesConsistency:
    """BUG-29 Root-Cause: Koordinaten-PATCH muss in GET sichtbar sein.

    AK (API-Ebene): Nach PATCH observer_lat/lon liefert GET /locations die neuen Werte.
    AK: recompute_triggered ist True (Trigger wurde ausgelöst).
    AK: Andere Locations in GET /locations bleiben unverändert (kein Kollateral-Schaden).

    Hinweis: Die Kalender-/Feed-Konsistenz (astronomische Neuberechnung) wird durch
    test_bug29_calendar_single_recompute.py abgesichert. Dieser Test prüft nur die
    Persistenz-Ebene (PATCH → GET-Roundtrip) ohne Ephemeriden-Zugriff.
    """

    def test_coordinates_patch_visible_in_get(self, client, auth_headers):
        """BUG-29 AK: Neue Koordinaten erscheinen in GET /locations."""
        new_lat = 52.5100
        new_lon = 13.4200

        r = client.patch(
            f"/locations/{LOC}",
            json={"observer_lat": new_lat, "observer_lon": new_lon},
            headers=auth_headers,
        )
        assert r.status_code == 200, f"PATCH fehlgeschlagen: {r.text}"
        assert r.json().get("recompute_triggered") is True, (
            "Koordinaten-PATCH sollte recompute_triggered=True setzen."
        )

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == LOC), None)
        assert loc is not None
        assert abs(loc["observer_lat"] - new_lat) < 0.0001, (
            f"observer_lat nach PATCH: {loc['observer_lat']} — erwartet ~{new_lat}. "
            "Mögliche Regression von BUG-29 (Overrides nicht persistiert)."
        )
        assert abs(loc["observer_lon"] - new_lon) < 0.0001, (
            f"observer_lon nach PATCH: {loc['observer_lon']} — erwartet ~{new_lon}."
        )

    def test_coordinates_patch_does_not_affect_other_locations(self, client, auth_headers):
        """BUG-29 AK: PATCH auf eine Location lässt andere unberührt."""
        # Alle Locations vor dem PATCH laden
        before = {l["id"]: l for l in client.get("/locations").json()}

        # PATCH auf unsere Test-Location
        client.patch(
            f"/locations/{LOC}",
            json={"observer_lat": 52.5200},
            headers=auth_headers,
        )

        # Alle anderen Locations prüfen
        after = {l["id"]: l for l in client.get("/locations").json()}
        for loc_id, before_loc in before.items():
            if loc_id == LOC:
                continue
            after_loc = after.get(loc_id)
            assert after_loc is not None, f"Location {loc_id} nach PATCH verschwunden"
            assert after_loc.get("observer_lat") == before_loc.get("observer_lat"), (
                f"observer_lat von {loc_id} nach PATCH auf {LOC} verändert — Kollateral-Schaden."
            )

    def test_patch_invalid_coordinates_rejected(self, client, auth_headers):
        """Edge Case: Koordinaten außerhalb des gültigen Bereichs → 422 (keine Persistenz)."""
        r = client.patch(
            f"/locations/{LOC}",
            json={"observer_lat": 999.0, "observer_lon": 13.40},
            headers=auth_headers,
        )
        assert r.status_code in (400, 422), (
            f"Ungültige Koordinaten (lat=999) sollten abgelehnt werden, bekam {r.status_code}."
        )
