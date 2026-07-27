"""BUG-84 — Kategorie UND Schwierigkeitsgrad im Bearbeiten-Formular: falsche
Vorbelegung und wirkungsloses Speichern.

Root Cause (siehe BACKLOG.md BUG-84, "Code-Verifikation"): `LocationOut` lieferte
kein `category_key`-Feld (das Frontend-Dropdown las es trotzdem -> immer Default),
UND `category`/`difficulty` fehlten in `LOCATION_FIELD_RULES`
(`backend/data/locations.py`) -> ein PATCH mit diesen Feldern wurde von
`patch_location()` still verworfen, obwohl die App "✓ Location aktualisiert" meldete.

Deckt die automatisierbaren Akzeptanzkriterien aus BACKLOG.md ab (Backend-
Persistenzverhalten). Reine Formular-VORBELEGUNG im Frontend-JS (welches DOM-
Element beim Öffnen des Sheets welchen Wert zeigt) ist in diesem
Backend-Testlauf NICHT automatisiert abgedeckt -- dafür bräuchte es einen
Browser-/DOM-Test (Playwright, siehe backend/tests/frontend/). Was automatisiert
IST: dass die API die korrekten Werte liefert (category_key + difficulty), auf
denen die Vorbelegung im Frontend beruht -- also die Datengrundlage, nicht das
Rendering selbst. Siehe Kommentar am Dateiende für die manuelle Restprüfung.

  - AK1/AK2 (Vorbelegung + Regressionsschutz): GET /locations liefert für eine
    Location mit von Skyline/2 abweichender Kategorie+Schwierigkeit die
    tatsächlich gespeicherten Werte inkl. `category_key` (vorher nie geliefert).
  - AK3 (Speichern wirkt tatsächlich): PATCH mit neuer category/difficulty wird
    übernommen, sichtbar in der Liste (GET /locations) UND im Einzelabruf
    (GET /locations/{id}, entspricht "erneutem Öffnen"), für BEIDE
    Persistenzpfade (Custom- UND Standard-Location, Pre-Mortem Szenario 2).
  - AK4 (Unverändert bleibt unverändert): PATCH ohne category/difficulty lässt
    beide Werte exakt unverändert.
  - AK5 (Fehlerfall): ein ungültiger category-/difficulty-Wert liefert 422 mit
    Fehlermeldung, der bisherige gespeicherte Wert bleibt unverändert (kein
    falscher Erfolg).
  - AK6 (Edge Case): ein nicht zuordenbarer, in der Datenbasis liegender
    Kategorie-Wert (z.B. Altlast aus der Zeit vor diesem Fix) lässt GET
    /locations weiterhin für ALLE Locations erfolgreich antworten und liefert
    für die betroffene Location einen sinnvollen Standardwert (SKYLINE), statt
    mit 500 abzubrechen (Pre-Mortem Szenario 1 -- Enum-Cast-Absturz).
  - Regressionstest (Pre-Mortem-Frühwarnung, explizit gefordert): GET /locations
    bleibt nach einer category-Änderung für ALLE bestehenden Locations gültig,
    nicht nur für die geänderte.

Direktes Vorlagen-Muster: backend/tests/test_bug_68.py (gleiche Fehlerklasse --
Feld fehlte in der PATCH-Whitelist --, gleiches Test-Setup: eigene, selbst-
anlegende Location-Fixture + API-Roundtrip über den TestClient, siehe
fotoalert-impl Pattern 12).
"""
from __future__ import annotations

import uuid

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


# ---------------------------------------------------------------------------
# Fixtures — eigene, isolierte Test-Locations pro Pfad (kein Shared State,
# fotoalert-impl Pattern 12). Kategorie WASSER + Schwierigkeit 3 bewusst NICHT
# identisch mit dem bisherigen Formular-Default (SKYLINE/2) gewählt (AK2) --
# sonst sieht der ursprüngliche Bug "zufällig richtig" aus.
# ---------------------------------------------------------------------------

@pytest.fixture
def custom_location_id(client):
    """Custom-Location (SQLite custom_locations-Tabelle, eigener Persistenzpfad)."""
    import main
    from data.locations import PhotoLocation, LocationCategory

    loc_id = f"custom_test_bug84_{uuid.uuid4().hex[:8]}"
    new_loc = PhotoLocation(
        id=loc_id, name="BUG-84-Test-Location (Custom)",
        description="Testort für test_bug-84.py",
        category=LocationCategory.WASSER,
        observer_lat=52.5, observer_lon=13.4,
        subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
        difficulty=3,
    )
    main.LOCATIONS.append(new_loc)
    main._save_custom_location(new_loc)

    yield loc_id

    main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
    main._store.delete_custom(loc_id)


@pytest.fixture
def standard_location_id(client):
    """'Standard'-Location (kein 'custom_'-Präfix) direkt in main.LOCATIONS --
    Pre-Mortem Szenario 2: PATCHes auf Standard-Locations persistieren über
    einen komplett anderen Pfad (_save_location_override() -> SQLite
    location_overrides-Tabelle als JSON-Blob) als Custom-Locations. Eigene
    direkte API-Roundtrip-Abdeckung, um eine Divergenz zwischen beiden Pfaden
    nicht nur über Custom-Locations "mitzutesten"."""
    import main
    from data.locations import PhotoLocation, LocationCategory

    loc_id = f"standard_test_bug84_{uuid.uuid4().hex[:8]}"
    new_loc = PhotoLocation(
        id=loc_id, name="BUG-84-Test-Location (Standard)",
        description="Testort für test_bug-84.py",
        category=LocationCategory.WASSER,
        observer_lat=52.5, observer_lon=13.4,
        subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
        difficulty=3,
    )
    main.LOCATIONS.append(new_loc)

    yield loc_id

    main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
    # Kein delete_override() im Code (nur upsert_override) -- Override-Zeile direkt
    # per Rohzugriff entfernen, damit kein Testartefakt in location_overrides bleibt
    # (gleiches Muster wie test_task77_qa_cleanup_on_delete.py).
    try:
        with main._store._connect() as conn:
            conn.execute("DELETE FROM location_overrides WHERE id = ?", (loc_id,))
            conn.commit()
    except Exception:
        pass


_BOTH_PATHS = ["custom_location_id", "standard_location_id"]


# ---------------------------------------------------------------------------
# AK1/AK2 — Vorbelegungs-Datengrundlage: category_key + difficulty korrekt
# geliefert, geprüft an einer Location mit Nicht-Default-Werten.
# ---------------------------------------------------------------------------

class TestGetLiefertEchteWerte:
    @pytest.mark.parametrize("loc_id_fixture", _BOTH_PATHS)
    def test_category_key_and_difficulty_match_stored_values(self, client, loc_id_fixture, request):
        loc_id = request.getfixturevalue(loc_id_fixture)

        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == loc_id), None)
        assert loc is not None
        assert loc["category"] == "Wasser & Spiegelung"
        assert loc["category_key"] == "WASSER"
        assert loc["difficulty"] == 3

        single = client.get(f"/locations/{loc_id}").json()
        assert single["category_key"] == "WASSER"
        assert single["difficulty"] == 3


# ---------------------------------------------------------------------------
# AK3 — Speichern wirkt tatsächlich, für BEIDE Persistenzpfade.
# ---------------------------------------------------------------------------

class TestPatchWirktTatsaechlich:
    @pytest.mark.parametrize("loc_id_fixture", _BOTH_PATHS)
    def test_category_and_difficulty_change_is_persisted(self, client, auth_headers, loc_id_fixture, request):
        loc_id = request.getfixturevalue(loc_id_fixture)

        r = client.patch(
            f"/locations/{loc_id}",
            json={"category": "MILCHSTRASSE", "difficulty": 1},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["category"] == "MILCHSTRASSE"
        assert r.json()["updated"]["difficulty"] == 1

        # Sichtbar in der Liste ...
        locations = client.get("/locations").json()
        loc = next((l for l in locations if l["id"] == loc_id), None)
        assert loc["category"] == "Milchstraße & Astro"
        assert loc["category_key"] == "MILCHSTRASSE"
        assert loc["difficulty"] == 1

        # ... UND beim erneuten Öffnen (GET /locations/{id}, entspricht dem
        # erneuten Öffnen des Bearbeiten-Formulars nach einem Reload).
        single = client.get(f"/locations/{loc_id}").json()
        assert single["category_key"] == "MILCHSTRASSE"
        assert single["difficulty"] == 1

    def test_only_category_changed_difficulty_left_alone(self, client, auth_headers, custom_location_id):
        """Nur ein Feld ändern -- das andere darf nicht mitverändert werden."""
        r = client.patch(
            f"/locations/{custom_location_id}",
            json={"category": "NATUR"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text

        loc = client.get(f"/locations/{custom_location_id}").json()
        assert loc["category_key"] == "NATUR"
        assert loc["difficulty"] == 3  # unverändert vom Fixture-Ausgangswert


# ---------------------------------------------------------------------------
# AK4 — Unverändert bleibt unverändert: ein PATCH, der category/difficulty gar
# nicht anfasst, darf beide Werte nicht mitverändern.
# ---------------------------------------------------------------------------

class TestUnveraendertBleibtUnveraendert:
    def test_patch_without_category_or_difficulty_leaves_both_untouched(self, client, auth_headers, custom_location_id):
        r = client.patch(
            f"/locations/{custom_location_id}",
            json={"name": "Nur der Name ändert sich"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert "category" not in r.json()["updated"]
        assert "difficulty" not in r.json()["updated"]

        loc = client.get(f"/locations/{custom_location_id}").json()
        assert loc["name"] == "Nur der Name ändert sich"
        assert loc["category_key"] == "WASSER"
        assert loc["difficulty"] == 3


# ---------------------------------------------------------------------------
# AK5 — Fehlerfall: ungültiger Wert -> 422 + ehrliche Fehlermeldung, bisheriger
# gespeicherter Wert bleibt für einen erneuten Versuch erhalten.
# ---------------------------------------------------------------------------

class TestFehlerfallLaesstAltenWertUnangetastet:
    def test_unknown_category_value_is_rejected_with_422(self, client, auth_headers, custom_location_id):
        r = client.patch(
            f"/locations/{custom_location_id}",
            json={"category": "REGENBOGEN_UNTERWASSER"},
            headers=auth_headers,
        )
        assert r.status_code == 422, r.text
        assert r.json().get("detail")

        loc = client.get(f"/locations/{custom_location_id}").json()
        assert loc["category_key"] == "WASSER"  # unverändert, kein falscher Erfolg

    @pytest.mark.parametrize("bad_difficulty", [0, 4, -1, "sehr schwer"])
    def test_out_of_range_difficulty_is_rejected_with_422(self, client, auth_headers, custom_location_id, bad_difficulty):
        r = client.patch(
            f"/locations/{custom_location_id}",
            json={"difficulty": bad_difficulty},
            headers=auth_headers,
        )
        assert r.status_code == 422, r.text

        loc = client.get(f"/locations/{custom_location_id}").json()
        assert loc["difficulty"] == 3  # unverändert, kein falscher Erfolg


# ---------------------------------------------------------------------------
# AK6 + Pre-Mortem Szenario 1 (Frühwarnung, explizit gefordert): ein nicht
# zuordenbarer Kategorie-Wert in der Datenbasis darf weder das Formular
# unbenutzbar machen noch GET /locations für ALLE Locations crashen.
# ---------------------------------------------------------------------------

class TestNichtZuordenbarerServerwertCrashtNicht:
    def test_corrupted_category_on_one_location_falls_back_and_does_not_break_get_all(self, client, custom_location_id):
        """Simuliert eine Altlast: irgendein Code-Pfad (z.B. eine Override-Zeile aus
        der Zeit vor diesem Fix) hat einen rohen, nicht zuordenbaren String direkt
        in loc.category geschrieben, statt einer LocationCategory-Instanz -- genau
        das Pre-Mortem-Szenario 1 aus BACKLOG.md BUG-84."""
        import main

        loc = next(l for l in main.LOCATIONS if l.id == custom_location_id)
        loc.category = "NICHT_ZUORDENBARER_ALTWERT"  # roher String, kein Enum

        # Die GESAMTE Liste (alle Locations, nicht nur die manipulierte) muss
        # weiterhin fehlerfrei antworten -- das ist der eigentliche Kern von
        # Pre-Mortem Szenario 1 (ein einzelner kaputter Wert darf nicht ALLE
        # Locations mit 500 abschießen).
        r = client.get("/locations")
        assert r.status_code == 200, r.text

        broken = next(l for l in r.json() if l["id"] == custom_location_id)
        assert broken["category_key"] == "SKYLINE"  # sinnvoller Standardwert
        assert broken["category"] == "Skyline & Architektur"

        # Auch der Einzelabruf bleibt benutzbar (Formular darf nicht "unbenutzbar" werden).
        single = client.get(f"/locations/{custom_location_id}")
        assert single.status_code == 200, single.text
        assert single.json()["category_key"] == "SKYLINE"


# ---------------------------------------------------------------------------
# Nicht automatisiert abgedeckt (siehe Docstring oben):
#
# - Dass das Bearbeiten-Formular-Dropdown/die Radio-Buttons im Browser beim
#   Öffnen VISUELL die richtige Option vorauswählen (DOM-Zustand von
#   web/index.html:LocationDetail.openEdit()). Die API-seitige Datengrundlage
#   dafür (category_key + difficulty korrekt geliefert) ist oben abgedeckt
#   (TestGetLiefertEchteWerte) -- das tatsächliche Rendering im Browser bleibt
#   ein manueller Test (siehe BACKLOG.md BUG-84 Testplan, "Manuell").
# - Dass ein fehlgeschlagenes Speichern (Netzwerkfehler) die im Formular
#   getroffene Auswahl im DOM erhält (AK5, Browser-Zustand) -- serverseitig ist
#   hier nur geprüft, dass ein abgelehnter PATCH den GESPEICHERTEN Wert nicht
#   verändert; dass das Eingabefeld im Browser nach einem Fehler seinen Wert
#   behält, ist ein DOM-/JS-Verhalten von web/index.html:saveEdit() (catch-Block
#   rendert das Formular nicht neu) und bleibt ebenfalls ein manueller Test.
# ---------------------------------------------------------------------------
