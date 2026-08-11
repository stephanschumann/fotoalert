"""TASK-94 — `_load_custom_locations()` in main.py: kein `coerce_category_value()`-
Fallback, keine Pro-Eintrag-Absicherung.

Root Cause (siehe BACKLOG.md TASK-94): `main.py:_load_custom_locations()` griff beim
Kategorie-Feld weiterhin direkt über `LocationCategory[...]` zu (Enum-Zugriff) statt
über die von BUG-84 eingeführte `coerce_category_value()`-Fallback-Funktion, UND war
nicht pro Eintrag try/except-abgesichert -- ein einzelner beschädigter Kategoriewert
in der `custom_locations`-Tabelle konnte das Laden ALLER NACHFOLGENDEN Custom-
Locations im selben Startup-Batch abbrechen (die Exception verließ die for-Schleife
und wurde erst vom äußeren try/except der Gesamtfunktion aufgefangen). Referenz-
implementierung für die Pro-Eintrag-Absicherung: `backend/precompute.py:
_load_custom_locations()` (BUG-33).

  - AK(a): ein regulärer Custom-Location-Eintrag lädt weiterhin korrekt (kein
    Verhaltensunterschied für den gesunden Fall).
  - AK(b): ein Eintrag mit einem nicht (mehr) zuordenbaren Kategoriewert wird über
    `coerce_category_value()` abgefangen (Fallback SKYLINE) statt eine Exception zu
    werfen -- lädt also trotzdem erfolgreich, kein Absturz.
  - AK(c): ein Eintrag, der trotz `coerce_category_value()`-Fallback aus einem
    ANDEREN Grund nicht in ein gültiges `PhotoLocation`-Objekt überführt werden kann
    (hier: fehlendes Pflichtfeld `observer_lat`, das `coerce_category_value()`
    naturgemäß nicht heilen kann), bricht NICHT das Laden der übrigen, gesunden
    Einträge im selben Batch ab -- er wird übersprungen/geloggt, Einträge davor UND
    danach laden trotzdem.

Direktes Vorlagen-Muster für Fixture-Isolation: `backend/tests/test_bug-84.py`
(eigene, selbst-anlegende/-aufräumende Test-Locations, kein Shared State, siehe
fotoalert-impl Pattern 12). Anders als test_bug-84.py (das über die laufende API
gegen bereits geladene Locations testet) ruft dieser Test `main._load_custom_locations()`
direkt und isoliert auf -- `_store.load_all_custom()` wird dafür mit
`unittest.mock.patch.object` durch kontrollierte, in-memory gebaute Einträge ersetzt,
damit kein SQLite-Schreibzugriff auf `data_dev/fotoalert.db` nötig ist (BUG-61-Pflicht:
keine Mutation der aktiven Dev-Datenbank durch Testläufe).
"""
from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


def _entry(loc_id: str, category="WASSER", **overrides) -> dict:
    """Baut einen vollständigen, gesunden Custom-Location-Eintrag im Rohformat, wie
    es `LocationStore.load_all_custom()` liefert (siehe backend/data/store.py)."""
    base = {
        "id": loc_id,
        "name": f"TASK-94-Test {loc_id}",
        "description": "Testort für test_task-94.py",
        "category": category,
        "observer_lat": 52.5,
        "observer_lon": 13.4,
        "subject_lat": 52.51,
        "subject_lon": 13.41,
        "subject_name": "Testmotiv",
        "subject_height_m": 10,
        "subject_width_m": 5,
        "distance_m": 100,
        "focal_length_suggestions": [],
        "special_notes": "",
        "difficulty": 2,
        "observer_floor_height_m": 0.0,
        "image_filename": None,
        "image_focus_x": None,
        "image_focus_y": None,
    }
    base.update(overrides)
    return base


@pytest.fixture
def cleanup_locations(client):
    """Entfernt am Testende alle IDs wieder aus `main.LOCATIONS`, die dieser Test evtl.
    über `_load_custom_locations()` angehängt hat (egal ob es tatsächlich klappte)."""
    import main

    added_ids: list[str] = []
    yield added_ids
    main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id not in added_ids]


class TestRegulaererEintragLaedtWeiterhinKorrekt:
    """AK(a): kein Verhaltensunterschied für den gesunden Fall."""

    def test_healthy_entry_loads_with_correct_category(self, client, cleanup_locations):
        import main
        from data.locations import LocationCategory

        loc_id = f"custom_task94_healthy_{uuid.uuid4().hex[:8]}"
        cleanup_locations.append(loc_id)
        entries = [_entry(loc_id, category="WASSER")]

        with patch.object(main._store, "load_all_custom", return_value=entries):
            main._load_custom_locations()

        loc = next((l for l in main.LOCATIONS if l.id == loc_id), None)
        assert loc is not None, "gesunder Eintrag wurde nicht geladen"
        assert loc.category == LocationCategory.WASSER
        assert loc.name == entries[0]["name"]


class TestBeschaedigterKategoriewertUeberCoerceAbgefangen:
    """AK(b): coerce_category_value()-Fallback statt Absturz."""

    def test_unresolvable_category_falls_back_via_coerce(self, client, cleanup_locations):
        import main
        from data.locations import LocationCategory

        loc_id = f"custom_task94_badcat_{uuid.uuid4().hex[:8]}"
        cleanup_locations.append(loc_id)
        entries = [_entry(loc_id, category="ALTE_NICHT_MEHR_EXISTIERENDE_KATEGORIE")]

        with patch.object(main._store, "load_all_custom", return_value=entries):
            main._load_custom_locations()  # darf NICHT werfen (vorher: KeyError via LocationCategory[...])

        loc = next((l for l in main.LOCATIONS if l.id == loc_id), None)
        assert loc is not None, "Eintrag mit beschädigter Kategorie wurde nicht geladen"
        assert loc.category == LocationCategory.SKYLINE  # coerce_category_value()-Fallback (BUG-84 AK6)


class TestEinzelnerKaputterEintragBrichtBatchNichtAb:
    """AK(c): ein Eintrag, den selbst coerce_category_value() nicht retten kann
    (hier: fehlendes Pflichtfeld), darf die übrigen, gesunden Einträge im selben
    Batch nicht am Laden hindern -- weder die davor noch die danach."""

    def test_broken_entry_is_skipped_others_still_load(self, client, cleanup_locations):
        import main

        healthy_before_id = f"custom_task94_before_{uuid.uuid4().hex[:8]}"
        broken_id = f"custom_task94_broken_{uuid.uuid4().hex[:8]}"
        healthy_after_id = f"custom_task94_after_{uuid.uuid4().hex[:8]}"
        cleanup_locations.extend([healthy_before_id, broken_id, healthy_after_id])

        broken_entry = _entry(broken_id, category="AUCH_NICHT_ZUORDENBAR")
        del broken_entry["observer_lat"]  # Pflichtfeld fehlt -> KeyError im PhotoLocation-
        # Konstruktor, ein Fehler jenseits dessen, was coerce_category_value() heilen kann.

        entries = [
            _entry(healthy_before_id, category="NATUR"),
            broken_entry,
            _entry(healthy_after_id, category="AUSSICHT"),
        ]

        with patch.object(main._store, "load_all_custom", return_value=entries):
            main._load_custom_locations()  # darf trotz kaputtem Eintrag NICHT werfen

        ids_loaded = {l.id for l in main.LOCATIONS}
        assert healthy_before_id in ids_loaded, "Eintrag VOR dem kaputten wurde nicht geladen (Batch-Abbruch!)"
        assert healthy_after_id in ids_loaded, "Eintrag NACH dem kaputten wurde nicht geladen (Batch-Abbruch!)"
        assert broken_id not in ids_loaded, "kaputter Eintrag wurde fälschlich doch geladen"

    def test_second_call_after_broken_entry_still_loads_new_healthy_entries(self, client, cleanup_locations):
        """Zusatzabsicherung: die Funktion bleibt nach einem übersprungenen Eintrag
        aufrufbar und funktionsfähig für einen FOLGENDEN, unabhängigen Ladevorgang
        (z.B. ein erneuter Server-Neustart) -- kein globaler kaputter Zustand."""
        import main

        broken_id = f"custom_task94_broken2_{uuid.uuid4().hex[:8]}"
        healthy_id = f"custom_task94_healthy2_{uuid.uuid4().hex[:8]}"
        cleanup_locations.extend([broken_id, healthy_id])

        broken_entry = _entry(broken_id)
        del broken_entry["observer_lat"]

        with patch.object(main._store, "load_all_custom", return_value=[broken_entry]):
            main._load_custom_locations()
        assert broken_id not in {l.id for l in main.LOCATIONS}

        with patch.object(main._store, "load_all_custom", return_value=[_entry(healthy_id)]):
            main._load_custom_locations()
        assert healthy_id in {l.id for l in main.LOCATIONS}
