"""BUG-61 — Motiv-Sektion im Location-Detail zeigt nach Umbenennung weiterhin
den alten Motivnamen.

Root Cause (verifiziert): PATCH /locations/{id} akzeptierte `subject_name`
nicht in der Menge der erlaubten Text-Felder (`text_fields` in main.py,
`patch_location`). Der neue Motivname wurde dadurch serverseitig still
verworfen, obwohl die App "Speichern erfolgreich" meldete — persistiert und
danach angezeigt wurde weiterhin der alte Wert. Der clientseitige
Reload-Mechanismus (BUG-30-Muster: Locations.all neu laden, Sheet neu
aufbauen) funktioniert korrekt, hatte aber nichts Neues zu laden.

Konvention (vgl. test_patch_cache_consistency.py): Jeder Test nennt im
Docstring die Ticket-ID, deren AK er absichert. API-Tests laufen gegen den
FastAPI-TestClient (conftest.py, client-Fixture).
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]

# Custom-Location aus data_dev (via TASK-19-Seed).
LOC = "custom_1781560330"


@pytest.fixture(autouse=True)
def _seed_test_location(ensure_seed_location):
    """Stellt custom_1781560330 vor jedem Test dieser Datei sicher (conftest.py).

    Lokaler autouse-Wrapper statt globalem autouse in conftest.py: der Seed
    ist nur für diese vier Dateien relevant, die die ID hart referenzieren.
    """


class TestBug61SubjectNamePersistence:
    """BUG-61: PATCH auf `subject_name` muss nach GET sichtbar sein.

    AK: Nach PATCH {"subject_name": "X"} liefert GET /locations für diese ID
        subject_name == "X".
    AK: Regression BUG-30: PATCH auf `name` (Location-Name) funktioniert
        weiterhin unverändert wie bisher, unabhängig von subject_name.
    """

    def test_subject_name_patch_visible_in_get(self, client, auth_headers):
        """BUG-61 AK: PATCH subject_name -> GET locations gibt neuen Motivnamen zurück."""
        new_subject_name = "Havelblick von der Wublitzbrücke"
        r = client.patch(
            f"/locations/{LOC}",
            json={"subject_name": new_subject_name},
            headers=auth_headers,
        )
        assert r.status_code == 200, f"PATCH fehlgeschlagen: {r.text}"

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == LOC), None)
        assert loc is not None, f"Location {LOC} nicht in GET /locations gefunden"
        assert loc["subject_name"] == new_subject_name, (
            f"Motivname nach PATCH: '{loc.get('subject_name')}' — erwartet: "
            f"'{new_subject_name}'. Root Cause BUG-61: subject_name fehlte in "
            f"der Server-Whitelist erlaubter Text-Felder."
        )

    def test_subject_name_patch_does_not_overwrite_other_fields(self, client, auth_headers):
        """BUG-61 AK: PATCH subject_name lässt name/description unberührt (Merge, kein Replace)."""
        desc = "Test-Beschreibung bleibt erhalten (BUG-61)"
        client.patch(f"/locations/{LOC}", json={"description": desc}, headers=auth_headers)

        r = client.patch(
            f"/locations/{LOC}",
            json={"subject_name": "Nur-Motiv-Test"},
            headers=auth_headers,
        )
        assert r.status_code == 200, f"PATCH fehlgeschlagen: {r.text}"

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == LOC), None)
        assert loc["description"] == desc, (
            "PATCH subject_name darf description nicht überschreiben (Merge, kein Replace)."
        )

    def test_location_name_patch_still_works_regression_bug30(self, client, auth_headers):
        """BUG-61 Regressionscheck: BUG-30-Fix für Location-Namen bleibt unverändert korrekt.

        Die Korrektur für subject_name darf den bereits funktionierenden
        Location-Namen-Fix (BUG-30) nicht beeinträchtigen.
        """
        new_name = "BUG61-Regression-Standortname"
        r = client.patch(f"/locations/{LOC}", json={"name": new_name}, headers=auth_headers)
        assert r.status_code == 200, f"PATCH fehlgeschlagen: {r.text}"

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == LOC), None)
        assert loc is not None, f"Location {LOC} nicht in GET /locations gefunden"
        assert loc["name"] == new_name, (
            f"Regression von BUG-30: Location-Name nach PATCH: '{loc['name']}' — "
            f"erwartet: '{new_name}'."
        )
