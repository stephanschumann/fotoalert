"""US-128 — Bauwerkshöhe (`subject_height_m`) und Bauwerksbreite (`subject_width_m`)
nachträglich über PATCH /locations/{id} bearbeitbar machen.

Deckt die automatisierbaren Akzeptanzkriterien aus BACKLOG.md ab:
  - PATCH akzeptiert subject_height_m/subject_width_m einzeln oder gemeinsam,
    für Custom- UND Standard-Locations (AK 1-3, 5).
  - Eine Änderung löst recompute_triggered=True aus (AK 4).
  - Validierung: 0 gültig, negativ/Typfehler → 422 (Edge Cases).
  - Standard-Location-Overrides überleben einen Server-Neustart
    (main._load_location_overrides()) UND werden vom precompute-Subprozess
    gesehen (precompute._apply_location_overrides()) — die beiden Pre-Mortem-
    Kernfunde dieser Analyse (BUG-29/BUG-50-Muster, aber an zwei bislang nicht
    im Ticket genannten Stellen).

Diese Tests entstehen VOR der Implementierung (Test-First) und sind daher
initial ROT, bis die Whitelist-Erweiterungen (Option A der Spec) umgesetzt sind:
  1. main.py:patch_location — numeric_fields/recompute_fields
  2. main.py:_load_location_overrides() — Feld-Tupel
  3. precompute.py:_OVERRIDE_FIELDS — Feld-Tupel

Nutzt dieselben Fixtures/Konventionen wie test_us120.py/test_us_125.py/test_us_126.py
(eigene, eindeutige Custom-Location pro Test) sowie das direkte Unit-Test-Muster aus
test_bug29_calendar_single_recompute.py für main._load_location_overrides() und
precompute._apply_location_overrides() (kein API-Roundtrip nötig, deterministisch,
kein Netzwerk-/Subprozesszugriff).
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace as NS

import pytest

pytestmark = [pytest.mark.api]


# ---------------------------------------------------------------------------
# Fixtures — eigene, isolierte Custom-Location pro Test (kein Shared State)
# ---------------------------------------------------------------------------

@pytest.fixture
def test_location_id(client):
    """Legt eine eigene, eindeutige Custom-Location für diesen Test an
    (gleiches Muster wie in test_us120.py/test_us_125.py/test_us_126.py)."""
    import main
    from data.locations import PhotoLocation, LocationCategory

    loc_id = f"custom_test_us128_{uuid.uuid4().hex[:8]}"
    new_loc = PhotoLocation(
        id=loc_id, name="US-128-Test-Location", description="Testort für test_us_128.py",
        category=LocationCategory.SKYLINE,
        observer_lat=52.5, observer_lon=13.4,
        subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
        subject_height_m=98.0, subject_width_m=73.0, distance_m=100,
    )
    main.LOCATIONS.append(new_loc)
    main._save_custom_location(new_loc)

    yield loc_id

    main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
    main._store.delete_custom(loc_id)


# ---------------------------------------------------------------------------
# AK 1-3: PATCH akzeptiert beide Felder, einzeln oder gemeinsam (Custom-Location)
# ---------------------------------------------------------------------------

class TestPatchAcceptsHeightAndWidth:
    def test_height_alone_is_accepted_and_persisted(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_height_m": 105.0},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["subject_height_m"] == 105.0

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc is not None
        assert loc["subject_height_m"] == 105.0

    def test_width_alone_is_accepted_and_persisted(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_width_m": 40.0},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["subject_width_m"] == 40.0

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == test_location_id), None)
        assert loc["subject_width_m"] == 40.0

    def test_height_and_width_together_in_one_request(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_height_m": 110.0, "subject_width_m": 80.0},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()["updated"]
        assert body["subject_height_m"] == 110.0
        assert body["subject_width_m"] == 80.0


# ---------------------------------------------------------------------------
# AK 4: Recompute wird ausgelöst
# ---------------------------------------------------------------------------

class TestRecomputeTriggered:
    def test_height_change_triggers_recompute(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_height_m": 120.0},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["recompute_triggered"] is True

    def test_width_change_triggers_recompute(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_width_m": 50.0},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["recompute_triggered"] is True


# ---------------------------------------------------------------------------
# Edge Cases: Validierung
# ---------------------------------------------------------------------------

class TestValidation:
    def test_zero_height_is_valid(self, client, auth_headers, test_location_id):
        """subject_height_m=0 ist ein realer Bestandswert (z.B. geltow_havelblick,
        Horizont-Ereignis ohne vertikales Motiv) und darf nicht abgelehnt werden."""
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_height_m": 0},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["subject_height_m"] == 0.0

    def test_zero_width_is_valid(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_width_m": 0},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["subject_width_m"] == 0.0

    def test_negative_height_returns_422(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_height_m": -5},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_negative_width_returns_422(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_width_m": -1},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_wrong_type_height_returns_422(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_height_m": "zehn"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_wrong_type_width_returns_422(self, client, auth_headers, test_location_id):
        r = client.patch(
            f"/locations/{test_location_id}",
            json={"subject_width_m": ["nicht", "erlaubt"]},
            headers=auth_headers,
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Pre-Mortem-Kernfund 1: main.py:_load_location_overrides() muss die neuen
# Felder beim (simulierten) Server-Neustart auf Standard-Locations zurückschreiben.
# ---------------------------------------------------------------------------

class TestStandardLocationOverrideReloadSurvivesRestart:
    """Direkter Unit-Test gegen main._load_location_overrides() (gleiches Muster
    wie test_bug29_calendar_single_recompute.py::test_bug29_apply_location_overrides_changes_coordinates),
    kein API-Roundtrip nötig — prüft exakt den in der Analyse gefundenen Whitelist-Fund."""

    def test_reload_applies_persisted_height_and_width_to_standard_location(self, monkeypatch):
        import main as M

        loc = NS(
            id="standard_test_us128", observer_lat=52.5, observer_lon=13.4,
            subject_lat=52.51, subject_lon=13.41,
            subject_height_m=50.0, subject_width_m=20.0,
            name="Basis-Name",
        )
        monkeypatch.setattr(M, "LOCATIONS", [loc])

        class _FakeStore:
            def load_all_overrides(self):
                return [{"id": "standard_test_us128",
                         "subject_height_m": 123.0, "subject_width_m": 45.0}]

        monkeypatch.setattr(M, "_store", _FakeStore())

        M._load_location_overrides()

        assert loc.subject_height_m == 123.0, (
            "Nach Server-Neustart (simuliert) muss der korrigierte Höhenwert aus dem "
            "Override wiederhergestellt werden, nicht der Basiswert."
        )
        assert loc.subject_width_m == 45.0


# ---------------------------------------------------------------------------
# Pre-Mortem-Kernfund 2: precompute.py:_apply_location_overrides() (Subprozess,
# nächtlicher Vollkalauf UND Single-Location-Recompute nach PATCH) muss die
# neuen Felder ebenfalls anwenden — sonst BUG-29-Wiederholung.
# ---------------------------------------------------------------------------

class TestPrecomputeSubprocessSeesHeightAndWidthOverride:
    """Direkter Unit-Test gegen precompute._apply_location_overrides() —
    identisches Muster wie test_bug29_calendar_single_recompute.py."""

    def test_apply_location_overrides_changes_height_and_width(self, monkeypatch):
        import precompute as P

        loc = NS(
            id="standard_test_us128", observer_lat=52.5, observer_lon=13.4,
            subject_lat=52.51, subject_lon=13.41,
            subject_height_m=50.0, subject_width_m=20.0,
            name="Basis-Name",
        )
        monkeypatch.setattr(P, "LOCATIONS", [loc])

        class _FakeStore:
            def load_all_overrides(self):
                return [{"id": "standard_test_us128",
                         "subject_height_m": 88.0, "subject_width_m": 33.0}]

        monkeypatch.setattr(P, "LocationStore", _FakeStore)

        applied = P._apply_location_overrides()

        assert applied == 1
        assert loc.subject_height_m == 88.0, (
            "BUG-29-Muster: Ohne diese Anwendung rechnet der Recompute-Subprozess "
            "(Einzel- UND Vollkalauf) mit dem alten Höhenwert weiter."
        )
        assert loc.subject_width_m == 33.0


# ---------------------------------------------------------------------------
# ❓ Frage 1 (Weg-Gate-Entscheidung 2026-07-10, Stephan wählt Option B):
# Die Magic-Number-Heuristik `subject_height_m == 20 and subject_width_m is None`
# in discover/subjects.py::_is_placeholder() darf eine Location mit KORRIGIERTER,
# recherchierter Höhe von genau 20m nicht mehr fälschlich als Platzhalter ohne
# echte Daten behandeln und aus dem Scout-Tab ausschließen. Die Reparatur ersetzt
# die reine Zahlen-Heuristik durch ein zuverlässiges Merkmal (z.B. ein explizites
# "ist recherchierter Wert"-Flag statt Höhe-exakt-20). Der genaue Attributname
# wird erst bei der Implementierung festgelegt; dieser Test kodiert den Vertrag
# aus der Spec (Attribut hier probeweise `subject_height_researched` genannt) und
# bleibt bis zur Implementierung erwartungsgemäß ROT (AttributeError o.ä.).
# ---------------------------------------------------------------------------

class TestPlaceholderHeuristicHeight20EdgeCase:
    """Deckt das neue AK ab: 'Eine Location mit korrigierter Bauwerkshöhe von
    genau 20 Metern und leerer Breitenangabe erscheint weiterhin korrekt im
    Scout-Tab.' Direkter Unit-Test gegen discover.subjects._is_placeholder(),
    kein API-Roundtrip nötig (gleiches Muster wie die Override-Reload-Tests oben)."""

    def test_researched_height_of_exactly_20_is_not_treated_as_placeholder(self):
        from discover.subjects import _is_placeholder

        loc = NS(
            subject_height_m=20.0,
            subject_width_m=None,
            # Neues, zuverlässiges Merkmal statt Magic-Number-Heuristik: markiert,
            # dass 20m ein bewusst recherchierter/korrigierter Wert ist, kein
            # unbearbeiteter Default-Platzhalter.
            subject_height_researched=True,
        )

        assert _is_placeholder(loc) is False, (
            "Eine Location mit recherchierter Höhe von genau 20m und leerer "
            "Breite darf nicht mehr als Platzhalter gelten und muss im "
            "Scout-Tab sichtbar bleiben (US-128, Frage 1, Option B)."
        )

    def test_unresearched_default_height_of_20_is_still_treated_as_placeholder(self):
        """Regressionsschutz: der ursprüngliche Alt-Grenzfall (echter, unbearbeiteter
        Default-Platzhalter ohne recherchierten Wert) muss weiterhin korrekt als
        Platzhalter erkannt und aus dem Scout-Tab ausgeschlossen werden."""
        from discover.subjects import _is_placeholder

        loc = NS(
            subject_height_m=20.0,
            subject_width_m=None,
            subject_height_researched=False,
        )

        assert _is_placeholder(loc) is True
