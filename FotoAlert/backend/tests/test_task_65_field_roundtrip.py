"""TASK-65 — Generischer Feld-Rundreise-Test für alle Location-Felder.

Deckt die dreimal aufgetretene Fehlerklasse „Feld fehlt in einer Whitelist ->
Änderung wird beim nächsten Server-Neustart/precompute-Lauf still verworfen"
(BUG-50, BUG-61, BUG-68) generisch ab — auch für Felder, die es heute noch gar
nicht gibt (Option C aus der Analyse-Phase, siehe BACKLOG.md TASK-65):

  1. Vollständigkeits-Check (Rule 1 / AK 1): Jedes Feld auf der `PhotoLocation`-
     Datenklasse muss entweder in `LOCATION_FIELD_RULES` oder auf der
     begründeten `FIELD_EXCEPTIONS`-Liste stehen. Der Anker ist bewusst
     `dataclasses.fields(PhotoLocation)` — NICHT `LOCATION_FIELD_RULES` selbst
     (Pre-Mortem Szenario 1: sonst wäre der Test blind für ein komplett
     vergessenes Feld, genau die BUG-50/61/68-Fehlerklasse).

  2. Parametrisierter Rundreise-Test (Rule 2/3) über `LOCATION_FIELD_RULES.items()`
     mit „kind"-bewusster Testwert-Erzeugung, getrennt für:
       - Standard-Location + main._load_location_overrides() (Server-Neustart)
       - Standard-Location + precompute._apply_location_overrides() (precompute)
       - Custom-Location  + main._load_custom_locations() (Server-Neustart)
       - Custom-Location  + precompute._load_custom_locations() (precompute)

Unit-Test-Muster wie `test_bug_68.py`: kein echter Serverneustart, kein echter
precompute-Subprozess, kein echter API-Roundtrip nötig — alles über
monkeypatch gegen die realen Reload-Funktionen. Dadurch bleibt der komplette
Lauf im Sekundenbereich (AK 8) und hinterlässt keine echten Locations (AK 9,
hier sogar ganz ohne echte SQLite-Schreibvorgänge, da mit Fake-Stores gegen
main.LOCATIONS/precompute.LOCATIONS gearbeitet wird statt gegen data_dev/).
"""
from __future__ import annotations

import dataclasses

import pytest

from data.locations import PhotoLocation, LOCATION_FIELD_RULES

pytestmark = [pytest.mark.api]


# ---------------------------------------------------------------------------
# Ausnahmeliste (Pre-Mortem Szenario 2 / AK 5): Felder, die bewusst NICHT über
# den generischen PATCH-Endpoint laufen bzw. nie eine App-seitige Host-Eingabe
# sind. Jede Ausnahme mit Grund + Fundstelle kommentiert, damit der
# Vollständigkeits-Check nicht "dauer-rot" wird (siehe Pre-Mortem).
# ---------------------------------------------------------------------------
FIELD_EXCEPTIONS: dict[str, str] = {
    "id": "Primärschlüssel, strukturell, nie über den generischen PATCH-Endpoint änderbar.",
    "category": "Enum, wird nur bei Anlage gesetzt; kein PATCH-Pfad in main.py:patch_location.",
    "elevation_difference_m": "Wird serverseitig aus DEM-Höhendaten berechnet (main.py:_elevation_provider), kein Host-Eingabefeld.",
    "distance_m": "Rein informativer, berechneter Wert; kein PATCH-Pfad in main.py:patch_location vorgesehen.",
    "best_times": "Liste, kein PATCH-Pfad in main.py:patch_location vorgesehen (nur Code-Pflege/Locationscout-Import).",
    "ideal_azimuth_range": "Wird von der nächtlichen QA-Automatik gesetzt (main.py:_load_qa_values / TASK-48), kein Host-PATCH-Pfad.",
    "solar_alignment_note": "Freitext, aber kein PATCH-Pfad in main.py:patch_location vorgesehen (nur Code-Pflege in data/locations.py).",
    "lunar_alignment_note": "Freitext, aber kein PATCH-Pfad in main.py:patch_location vorgesehen (nur Code-Pflege in data/locations.py).",
    "access_note": "Freitext, aber kein PATCH-Pfad in main.py:patch_location vorgesehen (nur Code-Pflege in data/locations.py).",
    "locationscout_url": "Freitext, aber kein PATCH-Pfad in main.py:patch_location vorgesehen (nur Code-Pflege in data/locations.py).",
    "difficulty": "Nur bei Anlage/Custom-Location-Erstellung gesetzt; kein PATCH-Pfad in main.py:patch_location vorgesehen.",
    "sightline_status": "Wird ausschließlich vom Sichtachsen-Check gesetzt (US-09, /sightline-refresh), kein Host-PATCH-Pfad.",
    "sightline_angle_deg": "Wird ausschließlich vom Sichtachsen-Check gesetzt (US-09, /sightline-refresh), kein Host-PATCH-Pfad.",
}

# Custom-Locations haben keine subject_height_researched-Spalte (main.py:patch_location
# entfernt das Feld für loc_id.startswith("custom_") explizit aus den DB-Kwargs, siehe
# Kommentar dort) und main._load_custom_locations()/precompute._load_custom_locations()
# rekonstruieren es folgerichtig nicht aus dem gespeicherten Custom-Location-Datensatz.
# Für den Custom-Location-Pfad (Rule 4) ist dieses Feld daher keine Regressionslücke,
# sondern bestehendes, dokumentiertes Verhalten -> von den Custom-Parametrisierungen
# ausgenommen (mit Grund, analog zu FIELD_EXCEPTIONS oben).
CUSTOM_PATH_EXCLUDED_FIELDS = {"subject_height_researched"}


def _missing_fields(existing_field_names, rules_keys, exception_keys):
    """Kernlogik des Vollständigkeits-Checks, isoliert testbar (AK 6 Edge Case)."""
    covered = set(rules_keys) | set(exception_keys)
    return sorted(set(existing_field_names) - covered)


# ---------------------------------------------------------------------------
# Rule 1 / AK 1 + AK 6 (Edge Case: fehlendes Feld) — Vollständigkeits-Check
# ---------------------------------------------------------------------------

class TestFieldCompletenessAgainstDataclass:
    def test_every_dataclass_field_is_ruled_or_excepted(self):
        all_fields = {f.name for f in dataclasses.fields(PhotoLocation)}
        missing = _missing_fields(all_fields, LOCATION_FIELD_RULES.keys(), FIELD_EXCEPTIONS.keys())
        assert not missing, (
            f"Feld(er) auf PhotoLocation ohne Eintrag in LOCATION_FIELD_RULES "
            f"(data/locations.py) oder in FIELD_EXCEPTIONS (diese Datei): {missing}. "
            "Jedes Datenmodell-Feld muss an einer der beiden Stellen auftauchen -- "
            "sonst wiederholt sich die BUG-50/61/68-Fehlerklasse (Feld komplett vergessen)."
        )

    def test_no_field_is_both_ruled_and_excepted(self):
        overlap = set(LOCATION_FIELD_RULES.keys()) & set(FIELD_EXCEPTIONS.keys())
        assert not overlap, f"Feld(er) gleichzeitig in Tabelle UND Ausnahmeliste: {sorted(overlap)}"

    def test_completeness_check_detects_a_synthetically_missing_field(self):
        """AK 6 (Edge Case): Beweist, dass die Check-Logik selbst ein fehlendes Feld
        erkennt -- ohne die echte Dataclass anfassen zu müssen. Simuliert genau den
        BUG-50/61/68-Fall: ein Feld existiert im Datenmodell, taucht aber weder in
        der Regel-Tabelle noch in der Ausnahmeliste auf."""
        synthetic_fields = {"observer_lat", "name", "weather_confidence"}  # letzteres "neu, vergessen"
        missing = _missing_fields(synthetic_fields, LOCATION_FIELD_RULES.keys(), FIELD_EXCEPTIONS.keys())
        assert missing == ["weather_confidence"], (
            "Die Vollständigkeits-Check-Logik muss ein Feld, das weder in der Tabelle "
            "noch auf der Ausnahmeliste steht, mit Klarnamen melden."
        )


# ---------------------------------------------------------------------------
# Kind-bewusste Testwert-Erzeugung (Pre-Mortem Szenario 3): vermeidet, dass ein
# generischer Dummy-Wert (z.B. String auf einem Koordinatenfeld) die Rundreise
# an der falschen Stelle scheitern lässt.
# ---------------------------------------------------------------------------

def _test_values(kind: str, field_name: str):
    """Liefert (alter_wert, neuer_wert) passend zum Feld-"kind"."""
    if kind == "coord":
        if field_name.endswith("_lat"):
            return 52.5000, 52.5321
        return 13.4000, 13.4567
    if kind == "numeric":
        return 12.0, 88.0
    if kind == "text":
        return "Alter Testwert (TASK-65)", "Neuer Testwert (TASK-65)"
    if kind == "list":
        return [24, 35], [50, 85, 135]
    if kind == "image":
        if field_name == "image_filename":
            return "alt_task65.jpg", "neu_task65.jpg"
        return 20.0, 77.0  # image_focus_x/y: Prozentwerte 0-100
    if kind == "flag":
        return False, True
    raise ValueError(f"Unbekannter Feld-'kind': {kind!r} (Feld: {field_name})")


_ALL_FIELDS = sorted(LOCATION_FIELD_RULES.items())
_CUSTOM_PATH_FIELDS = sorted(
    (f, r) for f, r in LOCATION_FIELD_RULES.items() if f not in CUSTOM_PATH_EXCLUDED_FIELDS
)


# ---------------------------------------------------------------------------
# Rule 2 / AK 2 + AK 7 (Edge Case: falsches Flag) — Standard-Location,
# Server-Neustart-Rundreise über main._load_location_overrides().
# ---------------------------------------------------------------------------

class TestStandardLocationOverrideReloadRoundtrip:
    @pytest.mark.parametrize("field_name,rule", _ALL_FIELDS, ids=[f for f, _ in _ALL_FIELDS])
    def test_field_survives_simulated_restart(self, field_name, rule, monkeypatch):
        import main as M
        from types import SimpleNamespace as NS

        old_val, new_val = _test_values(rule["kind"], field_name)
        loc = NS(id="standard_test_task65", **{field_name: old_val})
        monkeypatch.setattr(M, "LOCATIONS", [loc])

        class _FakeStore:
            def load_all_overrides(self):
                return [{"id": "standard_test_task65", field_name: new_val}]

        monkeypatch.setattr(M, "_store", _FakeStore())

        M._load_location_overrides()

        if rule["override_reload"]:
            assert getattr(loc, field_name) == new_val, (
                f"Feld '{field_name}' hat override_reload=True in LOCATION_FIELD_RULES, "
                "überlebt aber keinen simulierten Server-Neustart "
                "(main._load_location_overrides) -- Regressionsschutz für BUG-68."
            )
        else:
            assert getattr(loc, field_name) == old_val, (
                f"Feld '{field_name}' hat override_reload=False -- der alte Wert muss "
                "unverändert bleiben (bewusste Ausnahme, z.B. image_filename)."
            )


# ---------------------------------------------------------------------------
# Rule 3 / AK 3 -- Standard-Location, precompute-Rundreise über
# precompute._apply_location_overrides().
# ---------------------------------------------------------------------------

class TestStandardLocationPrecomputeReloadRoundtrip:
    @pytest.mark.parametrize("field_name,rule", _ALL_FIELDS, ids=[f for f, _ in _ALL_FIELDS])
    def test_field_survives_simulated_precompute_run(self, field_name, rule, monkeypatch):
        import precompute as P
        from types import SimpleNamespace as NS

        old_val, new_val = _test_values(rule["kind"], field_name)
        loc = NS(id="standard_test_task65_pc", **{field_name: old_val})
        monkeypatch.setattr(P, "LOCATIONS", [loc])

        class _FakeStore:
            def load_all_overrides(self):
                return [{"id": "standard_test_task65_pc", field_name: new_val}]

        monkeypatch.setattr(P, "LocationStore", _FakeStore)

        applied = P._apply_location_overrides()

        assert applied == 1
        if rule["precompute_reload"]:
            assert getattr(loc, field_name) == new_val, (
                f"Feld '{field_name}' hat precompute_reload=True in LOCATION_FIELD_RULES, "
                "der precompute-Subprozess rechnet aber weiter mit dem alten Wert "
                "(precompute._apply_location_overrides) -- BUG-29/BUG-68-Muster."
            )
        else:
            assert getattr(loc, field_name) == old_val, (
                f"Feld '{field_name}' hat precompute_reload=False -- das ist eine bewusste, "
                "dokumentierte Ausnahme (z.B. image_filename), der alte Wert muss bestehen "
                "bleiben. Kein Fehlalarm laut AK 5/Pre-Mortem Szenario 2."
            )


# ---------------------------------------------------------------------------
# Rule 4 / AK 4 -- Custom-Location-Pfad, komplett anderer Speicherweg
# (main._load_custom_locations() bzw. precompute._load_custom_locations()
# rekonstruieren die Location jeweils frisch aus dem gespeicherten Datensatz,
# statt Overrides per setattr auf ein bestehendes Objekt anzuwenden).
# ---------------------------------------------------------------------------

def _base_custom_entry(field_name: str, value) -> dict:
    """Vollständiger, gültiger Custom-Location-Datensatz mit einem einzelnen
    überschriebenen Feld -- entspricht dem, was main._load_custom_locations()/
    precompute._load_custom_locations() aus der SQLite custom_locations-Tabelle
    lesen (siehe main.py:_load_custom_locations, precompute.py:_load_custom_locations)."""
    base = {
        "id": "custom_test_task65",
        "name": "TASK-65 Custom-Location",
        "description": "Testort für test_task_65_field_roundtrip.py",
        "category": "SKYLINE",
        "observer_lat": 52.5000,
        "observer_lon": 13.4000,
        "subject_lat": 52.5100,
        "subject_lon": 13.4100,
        "subject_name": "Basis-Motiv",
        "subject_height_m": 10.0,
        "subject_width_m": 5.0,
        "distance_m": 100,
        "focal_length_suggestions": [24, 35],
        "special_notes": "Basis-Hinweis",
        "difficulty": 1,
        "observer_floor_height_m": 0.0,
        "image_filename": "basis_task65.jpg",
        "image_focus_x": 30.0,
        "image_focus_y": 30.0,
    }
    base[field_name] = value
    return base


class TestCustomLocationOverrideReloadRoundtrip:
    """Rule 4 / AK 4: main._load_custom_locations() rekonstruiert die Location
    komplett neu aus dem gespeicherten Custom-Location-Datensatz -- Regressionsschutz
    dafür, dass ein Feld beim Server-Neustart nicht auf einen Konstruktor-Default
    zurückfällt, obwohl es gespeichert wurde."""

    @pytest.mark.parametrize(
        "field_name,rule", _CUSTOM_PATH_FIELDS, ids=[f for f, _ in _CUSTOM_PATH_FIELDS]
    )
    def test_field_survives_simulated_restart(self, field_name, rule, monkeypatch):
        import main as M

        old_val, new_val = _test_values(rule["kind"], field_name)
        entry = _base_custom_entry(field_name, new_val)
        monkeypatch.setattr(M, "LOCATIONS", [])

        class _FakeStore:
            def load_all_custom(self):
                return [entry]

        monkeypatch.setattr(M, "_store", _FakeStore())

        M._load_custom_locations()

        loc = next((l for l in M.LOCATIONS if l.id == entry["id"]), None)
        assert loc is not None, "Custom-Location wurde nicht aus dem Fake-Store geladen."
        assert getattr(loc, field_name) == new_val, (
            f"Feld '{field_name}' einer Custom-Location überlebt keinen simulierten "
            "Server-Neustart (main._load_custom_locations) -- Custom-Locations nutzen "
            "einen eigenen Speicherweg (Rule 4), unabhängig von der Override-Tabelle."
        )


class TestCustomLocationPrecomputeReloadRoundtrip:
    """Rule 4 / AK 3+4: precompute._load_custom_locations() ist der eigene
    Nachlade-Pfad des Recompute-Subprozesses für Custom-Locations (seit BUG-33)
    -- Korrektur ggü. der überholten Annahme "precompute sieht keine
    Custom-Locations" (siehe reference_fotoalert_precompute_dataload)."""

    @pytest.mark.parametrize(
        "field_name,rule", _CUSTOM_PATH_FIELDS, ids=[f for f, _ in _CUSTOM_PATH_FIELDS]
    )
    def test_field_survives_simulated_precompute_run(self, field_name, rule, monkeypatch):
        import precompute as P

        old_val, new_val = _test_values(rule["kind"], field_name)
        entry = _base_custom_entry(field_name, new_val)
        monkeypatch.setattr(P, "LOCATIONS", [])

        class _FakeStore:
            def load_all_custom(self):
                return [entry]

        monkeypatch.setattr(P, "LocationStore", _FakeStore)

        added = P._load_custom_locations()

        loc = next((l for l in P.LOCATIONS if l.id == entry["id"]), None)
        assert loc is not None, "Custom-Location wurde nicht in den precompute-Subprozess geladen."

        # precompute._load_custom_locations() rekonstruiert die PhotoLocation NICHT mit
        # image_filename/image_focus_x/y (kind "image", precompute_reload=False) und
        # unabhängig davon nie mit subject_height_researched (siehe
        # CUSTOM_PATH_EXCLUDED_FIELDS) -- für diese Felder ist "precompute sieht NICHT
        # den neuen Wert" das korrekte, dokumentierte Verhalten (kein Fehlalarm).
        if rule["precompute_reload"] and rule["kind"] != "image":
            assert added == 1
            assert getattr(loc, field_name) == new_val, (
                f"Feld '{field_name}' einer Custom-Location wird vom precompute-Subprozess "
                "nicht mit dem neuen Wert gesehen (precompute._load_custom_locations) -- "
                "BUG-33-Muster-Wiederholung."
            )
        else:
            actual = getattr(loc, field_name, None)
            assert actual != new_val, (
                f"Feld '{field_name}' hat precompute_reload=False (oder ist ein Bild-Feld) "
                "-- precompute darf den neuen Wert nicht sehen. Wenn dieser Assert fehlschlägt, "
                "wurde das Feld inzwischen precompute-reload-fähig gemacht, ohne die Regel-"
                "Tabelle bzw. diesen Testfall anzupassen."
            )
