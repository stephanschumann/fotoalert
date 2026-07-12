"""BUG-68 — Hinweise-Feld (`special_notes`) und Motivname (`subject_name`) einer
Standard-Location übersteht keinen Server-Neustart und wird nicht vom
precompute-Subprozess gesehen.

Deckt die automatisierbaren Akzeptanzkriterien aus BACKLOG.md ab:
  - AK 1/2: Eine PATCH-Korrektur an special_notes/subject_name einer
    Standard-Location bleibt nach einem (simulierten) Server-Neustart
    sichtbar (main._load_location_overrides()).
  - AK 3/4: Ein Einzel- wie Vollrecompute (precompute._apply_location_overrides())
    überschreibt die Korrektur nicht mit dem alten Basiswert.
  - AK 5: Bei Custom-Locations ändert sich am bestehenden Verhalten nichts
    (Korrektur bleibt stabil, weil sie direkt in der Datei liegt statt über
    den Override-Mechanismus).
  - AK 6: Weder special_notes noch subject_name lösen einen Recompute aus
    (RECOMPUTE_TRIGGER_FIELDS enthält sie nicht — recompute bleibt False).
  - AK 7: Ein bereits vor dem Fix gespeicherter, bisher "schlafender"
    Override-Wert wird nach dem Fix beim Reload erstmals angewendet (kein
    Datenverlust, nur verzögert sichtbar).

Direktes Vorlagen-Muster: backend/tests/test_us_128.py (dieselbe Fehlerklasse,
dasselbe Reload-Testmuster, nur anderes Feld-Paar: special_notes/subject_name
statt subject_height_m/subject_width_m). Kein API-Roundtrip nötig für die
Reload-Tests (Unit-Tests gegen main._load_location_overrides() und
precompute._apply_location_overrides(), gleiches Muster wie
test_bug29_calendar_single_recompute.py).

Diese Tests sind nach dem Fix (Option a — Flag-Flip in LOCATION_FIELD_RULES)
GRÜN. Vor dem Fix (override_reload/precompute_reload jeweils False) wären die
beiden Reload-Klassen ROT.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace as NS

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


# ---------------------------------------------------------------------------
# Fixtures — eigene, isolierte Custom-Location pro Test (kein Shared State)
# ---------------------------------------------------------------------------

@pytest.fixture
def test_location_id(client):
    """Legt eine eigene, eindeutige Custom-Location für diesen Test an
    (gleiches Muster wie in test_us_128.py/test_us120.py/test_us_125.py)."""
    import main
    from data.locations import PhotoLocation, LocationCategory

    loc_id = f"custom_test_bug68_{uuid.uuid4().hex[:8]}"
    new_loc = PhotoLocation(
        id=loc_id, name="BUG-68-Test-Location", description="Testort für test_bug_68.py",
        category=LocationCategory.SKYLINE,
        observer_lat=52.5, observer_lon=13.4,
        subject_lat=52.51, subject_lon=13.41, subject_name="Altes Motiv",
        special_notes="Alter Hinweis", subject_height_m=50.0, subject_width_m=20.0,
        distance_m=100,
    )
    main.LOCATIONS.append(new_loc)
    main._save_custom_location(new_loc)

    yield loc_id

    main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
    main._store.delete_custom(loc_id)


# ---------------------------------------------------------------------------
# AK 5 (Edge Case, Custom-Locations bereits vorher korrekt): PATCH bleibt
# stabil in der eigenen Datei — kein Override-Reload-Mechanismus involviert.
# Regressionsschutz: darf sich durch den Fix nicht ändern.
# ---------------------------------------------------------------------------

class TestPatchAcceptsSpecialNotesAndSubjectName:
    def test_special_notes_alone_is_accepted_and_persisted(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"special_notes": "Neuer korrigierter Hinweis"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["special_notes"] == "Neuer korrigierter Hinweis"

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc is not None
        assert loc["special_notes"] == "Neuer korrigierter Hinweis"

    def test_subject_name_alone_is_accepted_and_persisted(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_name": "Neues korrigiertes Motiv"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["subject_name"] == "Neues korrigiertes Motiv"

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc["subject_name"] == "Neues korrigiertes Motiv"

    def test_special_notes_and_subject_name_together_in_one_request(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"special_notes": "Kombi-Hinweis", "subject_name": "Kombi-Motiv"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()["updated"]
        assert body["special_notes"] == "Kombi-Hinweis"
        assert body["subject_name"] == "Kombi-Motiv"


# ---------------------------------------------------------------------------
# AK 6: Weder special_notes noch subject_name lösen einen Recompute aus —
# dieses Verhalten bleibt durch den Fix unverändert (recompute bleibt False).
# ---------------------------------------------------------------------------

class TestNoRecomputeTriggered:
    def test_special_notes_change_does_not_trigger_recompute(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"special_notes": "Löst keinen Recompute aus"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["recompute_triggered"] is False

    def test_subject_name_change_does_not_trigger_recompute(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_name": "Löst keinen Recompute aus"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["recompute_triggered"] is False


# ---------------------------------------------------------------------------
# AK 1/2 + AK 7 (Pre-Mortem-Kernfund): main.py:_load_location_overrides() muss
# special_notes/subject_name beim (simulierten) Server-Neustart auf
# Standard-Locations zurückschreiben — inkl. bereits vor dem Fix "schlafend"
# gespeicherter Overrides (AK 7: kein Datenverlust, nur verzögert sichtbar).
# ---------------------------------------------------------------------------

class TestStandardLocationOverrideReloadSurvivesRestart:
    """Direkter Unit-Test gegen main._load_location_overrides() (gleiches Muster
    wie test_us_128.py::TestStandardLocationOverrideReloadSurvivesRestart),
    kein API-Roundtrip nötig."""

    def test_reload_applies_persisted_special_notes_and_subject_name_to_standard_location(self, monkeypatch):
        import main as M

        loc = NS(
            id="standard_test_bug68", observer_lat=52.5, observer_lon=13.4,
            subject_lat=52.51, subject_lon=13.41,
            special_notes="Alter Hinweis (Basiswert)",
            subject_name="Alter Name (Basiswert)",
            name="Basis-Name",
        )
        monkeypatch.setattr(M, "LOCATIONS", [loc])

        class _FakeStore:
            def load_all_overrides(self):
                return [{"id": "standard_test_bug68",
                         "special_notes": "Korrigierter Hinweis",
                         "subject_name": "Korrigierter Name"}]

        monkeypatch.setattr(M, "_store", _FakeStore())

        M._load_location_overrides()

        assert loc.special_notes == "Korrigierter Hinweis", (
            "Nach Server-Neustart (simuliert) muss der korrigierte Hinweise-Text "
            "aus dem Override wiederhergestellt werden, nicht der Basiswert "
            "(BUG-68, AK 1)."
        )
        assert loc.subject_name == "Korrigierter Name", (
            "Nach Server-Neustart (simuliert) muss der korrigierte Motivname "
            "aus dem Override wiederhergestellt werden, nicht der Basiswert "
            "(BUG-68, AK 2)."
        )

    def test_reload_applies_pre_existing_dormant_override_after_fix(self, monkeypatch):
        """AK 7: Ein Override-Wert, der schon vor dem Fix in SQLite gespeichert
        wurde (bisher nie zurückgelesen), wird nach dem Fix beim nächsten Reload
        erstmals sichtbar — kein Datenverlust, nur verzögert angewendet."""
        import main as M

        loc = NS(
            id="standard_test_bug68_dormant", observer_lat=52.5, observer_lon=13.4,
            subject_lat=52.51, subject_lon=13.41,
            special_notes="Basiswert, nie überschrieben (vor dem Fix)",
            subject_name="Basisname, nie überschrieben (vor dem Fix)",
            name="Basis-Name",
        )
        monkeypatch.setattr(M, "LOCATIONS", [loc])

        class _FakeStore:
            def load_all_overrides(self):
                # Simuliert einen alten, "schlafenden" Override-Datensatz, der
                # schon vor BUG-68 in SQLite lag, aber vom Reload-Pfad bisher
                # nie gelesen wurde.
                return [{"id": "standard_test_bug68_dormant",
                         "special_notes": "Längst vergessene Korrektur",
                         "subject_name": "Längst vergessener Name"}]

        monkeypatch.setattr(M, "_store", _FakeStore())

        M._load_location_overrides()

        assert loc.special_notes == "Längst vergessene Korrektur"
        assert loc.subject_name == "Längst vergessener Name"


# ---------------------------------------------------------------------------
# AK 3/4: precompute.py:_apply_location_overrides() (Subprozess, nächtlicher
# Vollkalauf UND Single-Location-Recompute nach PATCH) muss special_notes/
# subject_name ebenfalls anwenden — sonst BUG-29-Muster-Wiederholung.
# ---------------------------------------------------------------------------

class TestPrecomputeSubprocessSeesSpecialNotesAndSubjectNameOverride:
    """Direkter Unit-Test gegen precompute._apply_location_overrides() —
    identisches Muster wie test_us_128.py::TestPrecomputeSubprocessSeesHeightAndWidthOverride."""

    def test_apply_location_overrides_changes_special_notes_and_subject_name(self, monkeypatch):
        import precompute as P

        loc = NS(
            id="standard_test_bug68", observer_lat=52.5, observer_lon=13.4,
            subject_lat=52.51, subject_lon=13.41,
            special_notes="Alter Hinweis (Basiswert)",
            subject_name="Alter Name (Basiswert)",
            name="Basis-Name",
        )
        monkeypatch.setattr(P, "LOCATIONS", [loc])

        class _FakeStore:
            def load_all_overrides(self):
                return [{"id": "standard_test_bug68",
                         "special_notes": "Korrigierter Hinweis (precompute)",
                         "subject_name": "Korrigierter Name (precompute)"}]

        monkeypatch.setattr(P, "LocationStore", _FakeStore)

        applied = P._apply_location_overrides()

        assert applied == 1
        assert loc.special_notes == "Korrigierter Hinweis (precompute)", (
            "BUG-29-Muster: Ohne diese Anwendung rechnet der precompute-Subprozess "
            "(Einzel- UND Vollkalauf) mit dem alten Hinweise-Basiswert weiter (AK 3/4)."
        )
        assert loc.subject_name == "Korrigierter Name (precompute)", (
            "BUG-29-Muster: Ohne diese Anwendung rechnet der precompute-Subprozess "
            "mit dem alten Motivname-Basiswert weiter (AK 3/4)."
        )
