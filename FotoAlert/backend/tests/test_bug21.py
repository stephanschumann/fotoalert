"""BUG-21: Brennweiten-Eingabe -- Kein Komma auf iOS-Tastatur.

Weg-Gate-Entscheidung Stephan (2026-09-04): Option A --
`inputmode="decimal"` am bestehenden #edit-focal-Feld (web/index.html) plus
Parser-Haertung in saveEdit() (Komma UND Semikolon als Trennzeichen). Keine
Backend-/Schema-Aenderung noetig -- focal_length_suggestions bleibt eine
Liste (backend/models/schemas.py:43, backend/data/locations.py:92),
Server-Validierung (backend/main.py, _validate_patch_fields(), BUG-22)
bleibt unveraendert (8-1200mm, keine Obergrenze der Anzahl).

Zwei Testgruppen, analog den im Ticket genannten Vorlagen:

1. Statischer Source-Check auf web/index.html (Muster test_bug109.py) --
   AK1 (inputmode="decimal" statt "numeric") und AK5 (Split-Regex akzeptiert
   Komma UND Semikolon). Kein Browser/Server noetig; deckt NICHT AK6 ab
   (echte iOS-Tastatur-Darstellung ist ein manueller Geraetetest, siehe
   BACKLOG.md BUG-21 Testplan -- bewusst nicht automatisierbar).

2. API-Regressionstest (Muster test_bug-84.py) -- PATCH mit
   focal_length_suggestions inkl. Mehrfachwert UND einem Wert ausserhalb
   einer evtl. kuratierten Liste (800mm) wird unveraendert persistiert und
   ueber GET zurueckgeliefert (AK2, AK3), sowie eine leere Liste bleibt
   fehlerfrei speicherbar (AK4).

AKs siehe BACKLOG.md BUG-21, "Akzeptanzkriterien (final, Option A)".

TASK-96-Hinweis: Testgruppe 1 loest einen Pfad ausserhalb von backend/ auf
(web/index.html) und ist deshalb zusaetzlich mit requires_full_checkout
markiert (siehe backend/tests/README.md, gleiches Muster wie test_bug109.py).
"""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest

_ROOT = Path(__file__).parent.parent.parent
_INDEX_HTML = _ROOT / "web" / "index.html"


def _read_index_html():
    assert _INDEX_HTML.exists(), f"{_INDEX_HTML} nicht gefunden"
    return _INDEX_HTML.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Testgruppe 1 -- statischer Source-Check (AK1, AK5). Kein Server/Browser.
# ---------------------------------------------------------------------------

@pytest.mark.offline
@pytest.mark.regression
@pytest.mark.requires_full_checkout
class TestEditFocalInputAndParser:
    def test_ak1_edit_focal_uses_decimal_inputmode(self):
        src = _read_index_html()
        assert 'id="edit-focal" type="text" inputmode="decimal"' in src, (
            "#edit-focal nutzt nicht (mehr) inputmode=\"decimal\" -- ohne dieses "
            "Attribut zeigt iOS Safari weiterhin die rein numerische Tastatur ohne "
            "Komma-Taste (AK1/AK6, BUG-21 noch nicht behoben)."
        )

    def test_ak1_edit_focal_no_longer_uses_numeric_inputmode(self):
        src = _read_index_html()
        assert 'id="edit-focal" type="text" inputmode="numeric"' not in src, (
            "#edit-focal nutzt weiterhin inputmode=\"numeric\" -- das ist exakt der "
            "im Ticket beschriebene Bug (keine Komma-Taste auf iOS)."
        )

    def test_ak5_focal_parser_splits_on_comma_and_semicolon(self):
        src = _read_index_html()
        assert "focalRaw.split(/[,;]/)" in src, (
            "saveEdit()-Parser fuer die Brennweiten-Eingabe splittet nicht (mehr) "
            "tolerant auf Komma UND Semikolon -- AK5 (Pre-Mortem Szenario 3+4) noch "
            "nicht behoben."
        )

    def test_ak5_focal_parser_no_longer_splits_on_comma_only(self):
        src = _read_index_html()
        assert "focalRaw.split(',')" not in src, (
            "saveEdit()-Parser splittet die Brennweiten-Eingabe weiterhin nur auf "
            "Komma -- ein Semikolon als Trennzeichen wuerde weiterhin stillschweigend "
            "Werte verschlucken (Pre-Mortem Szenario 4)."
        )


# ---------------------------------------------------------------------------
# Testgruppe 2 -- API-Regression: Mehrfachwerte inkl. Ausreisser (800mm) und
# leere Liste bleiben unveraendert persistiert (AK2, AK3, AK4).
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
class TestFocalLengthSuggestionsPersistUnchanged:
    @pytest.fixture
    def custom_location_id(self, client):
        """Eigene, selbst-anlegende Test-Location (fotoalert-impl Pattern 12) --
        Ausgangswert bewusst mit einem Wert ausserhalb einer evtl. kuratierten
        Standardwerteliste (800mm, real 1x in der Datenbasis vorhanden, siehe
        BACKLOG.md BUG-21 Code-Verifikation)."""
        import main
        from data.locations import PhotoLocation, LocationCategory

        loc_id = f"custom_test_bug21_{uuid.uuid4().hex[:8]}"
        new_loc = PhotoLocation(
            id=loc_id, name="BUG-21-Test-Location",
            description="Testort fuer test_bug21.py",
            category=LocationCategory.SKYLINE,
            observer_lat=52.5, observer_lon=13.4,
            subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
            focal_length_suggestions=[400, 600, 800],
        )
        main.LOCATIONS.append(new_loc)
        main._save_custom_location(new_loc)

        yield loc_id

        main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
        main._store.delete_custom(loc_id)

    def test_ak3_multi_value_patch_including_outlier_persists_unchanged(self, client, host_headers, custom_location_id):
        """AK2/AK3: mehrere gleichzeitige Werte inkl. eines Werts ausserhalb einer
        evtl. kuratierten Liste (800mm) werden unveraendert gespeichert und ueber
        GET (Liste UND Einzelabruf, entspricht erneutem Oeffnen) zurueckgeliefert."""
        r = client.patch(
            f"/locations/{custom_location_id}",
            json={"focal_length_suggestions": [24, 35, 70, 800]},
            headers=host_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["focal_length_suggestions"] == [24, 35, 70, 800]

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == custom_location_id), None)
        assert loc is not None
        assert loc["focal_length_suggestions"] == [24, 35, 70, 800]

        single = client.get(f"/locations/{custom_location_id}").json()
        assert single["focal_length_suggestions"] == [24, 35, 70, 800]

    def test_ak2_unchanged_multi_value_location_keeps_all_values(self, client, host_headers, custom_location_id):
        """AK2 (Negativ-/Edge-Case aus Regel 2): Formular oeffnen+speichern ohne
        Aenderung an der Brennweite darf die vorhandenen Werte nicht reduzieren."""
        r = client.patch(
            f"/locations/{custom_location_id}",
            json={"name": "BUG-21-Test-Location (unveraendert)"},
            headers=host_headers,
        )
        assert r.status_code == 200, r.text
        assert "focal_length_suggestions" not in r.json()["updated"]

        loc = client.get(f"/locations/{custom_location_id}").json()
        assert loc["focal_length_suggestions"] == [400, 600, 800]  # Fixture-Ausgangswert

    def test_ak4_empty_list_persists_as_empty_list_without_error(self, client, host_headers, custom_location_id):
        """AK4: leeres Feld/keine Auswahl speichert weiterhin eine leere Liste,
        kein Fehler."""
        r = client.patch(
            f"/locations/{custom_location_id}",
            json={"focal_length_suggestions": []},
            headers=host_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["focal_length_suggestions"] == []

        loc = client.get(f"/locations/{custom_location_id}").json()
        assert loc["focal_length_suggestions"] == []


# ---------------------------------------------------------------------------
# Nicht automatisiert abgedeckt (siehe BACKLOG.md BUG-21 Testplan, "Manuell"):
#
# - AK6: dass ein echtes iPhone mit deutschem Tastatur-Layout beim Fokussieren
#   von #edit-focal tatsaechlich eine Komma-Taste anzeigt. Browser-Simulation
#   zeigt keine echte iOS-Tastatur -- bewusst nicht automatisierbar, siehe
#   Pre-Mortem Szenario 3.
# ---------------------------------------------------------------------------
