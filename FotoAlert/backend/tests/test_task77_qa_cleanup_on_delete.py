"""TASK-77 — Cleanup bei Location-Löschung: location_qa_state/location_qa_values mitentfernen.

Deckt die automatisierbaren Akzeptanzkriterien aus BACKLOG.md ab (Entscheidung Option B):
  - Rule 1 (hartes Löschen, Custom Location): eine bereits QA-geprüfte Custom Location wird
    gelöscht → danach keine QA-Zeilen (location_qa_state/location_qa_values) mehr vorhanden.
  - AK Grenzfall (Option B, Softlöschen/Tombstone einer Standard-Location): gleiches Verhalten
    beim Tombstone-Zweig, nicht nur beim harten Löschen.
  - Edge Case: Location ohne je gesetzte QA-Werte wird gelöscht → kein Fehler, Response weiterhin
    Erfolg (Rule 1, negatives Beispiel).

Rule 2 (Fehlerbehandlung: DB-Ausnahme bei der QA-Bereinigung blockiert die Löschung nicht) wird
in dieser Datei nicht end-to-end gegen main.py getestet (dafür müsste _store.delete_qa auf
Modulebene gemockt werden, was main._delete_location_qa_data ohnehin bereits kapselt) — siehe
Rückmeldung an den Orchestrator.

Konvention (Pattern 12 aus fotoalert-impl-Skill): eigene, selbst-anlegende Test-Locations,
kein Rückgriff auf fremde/vorausgesetzte IDs. Verwendet main._store direkt gegen main.LOCATIONS,
gleiches Muster wie test_us120.py::TestDeleteRemovesImageFile.
"""
from __future__ import annotations

import uuid

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.fixture
def host_headers(client):
    r = client.post("/login", json={"password": "test-host-pw"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _make_photo_location(loc_id: str):
    from data.locations import PhotoLocation, LocationCategory

    return PhotoLocation(
        id=loc_id, name="TASK-77-Testort", description="Testort für test_task77_qa_cleanup_on_delete.py",
        category=LocationCategory.SKYLINE,
        observer_lat=52.5, observer_lon=13.4,
        subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
        subject_height_m=0.0, subject_width_m=0.0, distance_m=100,
    )


class TestQaCleanupOnHardDelete:
    """Rule 1 — Custom Location (hartes Löschen) entfernt QA-Zustand + QA-Werte."""

    def test_qa_rows_gone_after_custom_delete(self, client, host_headers):
        import main

        loc_id = f"custom_task77_{uuid.uuid4().hex[:8]}"
        new_loc = _make_photo_location(loc_id)
        main.LOCATIONS.append(new_loc)
        main._save_custom_location(new_loc)

        # QA-Daten vorab setzen (simuliert: Location wurde bereits automatisch geprüft).
        main._store.set_qa_values(
            loc_id,
            description="Schöner Blick.",
            ideal_azimuth_min=80.0,
            ideal_azimuth_max=120.0,
            focal_length_suggestions=[50, 85],
        )
        main._store.set_qa_lock(loc_id, "description", True)

        try:
            assert main._store.get_qa_values(loc_id) is not None, "Testvoraussetzung: QA-Werte müssen vor dem Löschen existieren."
            assert main._store.get_qa_state(loc_id) is not None, "Testvoraussetzung: QA-Zustand muss vor dem Löschen existieren."

            del_r = client.delete(f"/locations/{loc_id}", headers=host_headers)
            assert del_r.status_code == 200, f"DELETE fehlgeschlagen: {del_r.text}"
            assert del_r.json()["deleted"] is True

            assert main._store.get_qa_values(loc_id) is None, (
                "QA-Werte sollten nach dem Löschen einer Custom Location entfernt sein."
            )
            assert main._store.get_qa_state(loc_id) is None, (
                "QA-Zustand sollte nach dem Löschen einer Custom Location entfernt sein."
            )
        finally:
            main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
            main._store.delete_custom(loc_id)
            main._store.delete_qa(loc_id)  # Best-effort, falls die Assertion vorher fehlschlug.


class TestQaCleanupOnTombstone:
    """AK Grenzfall (Option B) — Standard-Location-Softlöschen (Tombstone) entfernt ebenfalls QA-Daten."""

    def test_qa_rows_gone_after_standard_tombstone(self, client, host_headers):
        import main

        # Standard-Location: ID ohne "custom_"-Präfix, direkt in main.LOCATIONS eingehängt
        # (kein create_custom/kein Persistieren in custom_locations — genau wie eine echte
        # Basis-Location, die nur aus data/locations.py + Overrides zusammengesetzt wird).
        loc_id = f"task77_standard_{uuid.uuid4().hex[:8]}"
        new_loc = _make_photo_location(loc_id)
        main.LOCATIONS.append(new_loc)

        main._store.set_qa_values(loc_id, description="Automatisch generierte Beschreibung.")
        main._store.set_qa_lock(loc_id, "azimuth", True)

        try:
            assert main._store.get_qa_values(loc_id) is not None
            assert main._store.get_qa_state(loc_id) is not None

            del_r = client.delete(f"/locations/{loc_id}", headers=host_headers)
            assert del_r.status_code == 200, f"DELETE (Tombstone) fehlgeschlagen: {del_r.text}"
            assert del_r.json()["deleted"] is True

            assert main._store.get_qa_values(loc_id) is None, (
                "QA-Werte sollten nach dem Softlöschen (Tombstone) einer Standard-Location entfernt sein."
            )
            assert main._store.get_qa_state(loc_id) is None, (
                "QA-Zustand sollte nach dem Softlöschen (Tombstone) einer Standard-Location entfernt sein."
            )

            # Location selbst ist per Tombstone als entfernt markiert (in-memory sofort weg).
            locations = client.get("/locations").json()
            assert not any(l["id"] == loc_id for l in locations)
        finally:
            main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
            main._store.delete_qa(loc_id)  # Best-effort, falls die Assertion vorher fehlschlug.
            # Kein delete_override() im Code (nur upsert_override) — Tombstone-Zeile direkt
            # per Rohzugriff entfernen, damit kein Testartefakt in location_overrides bleibt.
            try:
                with main._store._connect() as conn:
                    conn.execute("DELETE FROM location_overrides WHERE id = ?", (loc_id,))
                    conn.commit()
            except Exception:
                pass  # Best-effort-Cleanup, blockiert den Testlauf nicht.


class TestQaCleanupEdgeCaseNoQaData:
    """Rule 1, negatives Beispiel — Location ohne je gesetzte QA-Werte: kein Fehler beim Löschen."""

    def test_delete_without_prior_qa_data_still_succeeds(self, client, host_headers):
        import main

        loc_id = f"custom_task77_noqa_{uuid.uuid4().hex[:8]}"
        new_loc = _make_photo_location(loc_id)
        main.LOCATIONS.append(new_loc)
        main._save_custom_location(new_loc)

        try:
            # Testvoraussetzung: garantiert keine QA-Daten für diese frische ID vorhanden.
            assert main._store.get_qa_values(loc_id) is None
            assert main._store.get_qa_state(loc_id) is None

            del_r = client.delete(f"/locations/{loc_id}", headers=host_headers)
            assert del_r.status_code == 200, f"DELETE ohne vorherige QA-Daten sollte trotzdem erfolgreich sein: {del_r.text}"
            assert del_r.json()["deleted"] is True
        finally:
            main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
            main._store.delete_custom(loc_id)
