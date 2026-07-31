"""Regressionssuite — BUG-94: Kartentitel bei Wolkenstimmungs-Chancen ("Rote Wolken",
"Goldene Wolken", "Himmelsröte") nannte nicht die Location (Dopplung mit dem
Event-Typ-Badge statt Ortsangabe).

Root Cause (Ticket-Spec, Code-Verifikation 2026-07-30): `backend/main.py` enthielt
drei strukturell identische Builder-Funktionen (`_build_golden_clouds_event()`,
`_build_red_sky_event()`, `_build_red_clouds_event()`), die alle denselben Fehler
machten: `new_event["title"]` wurde auf den reinen Event-Typ-String gesetzt
("Goldene Wolken" / "Himmelsröte" / "Rote Wolken"), ohne Motiv-/Ortsbezug — anders
als andere Chancentypen ("Mond über {Motiv}", `calculations/opportunity.py` Z. 519).

Architektur-Entscheidung (Weg-Gate 2026-07-31, Stephans Vorgabe): Die Titel-Bildung
wird NICHT pro Chancenart einzeln dupliziert, sondern über einen zentralen Baustein
`main._build_opportunity_title(event_type_label, location_id)` erledigt. Jeder
Builder liefert nur noch Event-Typ-Label + location_id, nicht mehr den fertigen
Titel-String selbst. Testfälle 1-3 prüfen das konkrete Titel-Muster je Chancenart
(Einzeltests), Testfall 4 prüft den Fallback bei nicht auflösbarer location_id,
Testfall 5 prüft, dass Titel und Standort-Zeilen-Text sich unterscheiden (verhindert
Rückfall in eine umgekehrte Dopplung), und der KONSISTENZ-WÄCHTER-Test am Ende
durchsucht main.py automatisch (Namensmuster `_build_*_event`, unabhängig von einer
manuell gepflegten Liste) nach jedem Chancenart-Builder, der `new_event["title"]`
setzt, und lässt die Suite rot laufen, falls ein (auch künftig neu hinzugefügter)
Builder den zentralen Baustein nicht verwendet bzw. wieder einen Literal-String
zuweist — ohne dass dafür manuell ein neuer Einzeltest ergänzt werden muss.

Erweiterung (2026-07-31, unabhängige Verifikation + Stephans Entscheidung "jetzt
schließen, nicht verschieben"): Der bisherige Wächter oben deckt nur main.py ab.
Die übrigen Chancenarten (Blaue Stunde, Mond-Alignment, Sonne in Sichtachse,
Milchstraße, Mondauf-/-untergang, Meteore) entstehen über ein zweites, komplett
anderes Baumuster in `calculations/opportunity.py`: dort wird der Titel direkt als
`title=f"..."`-Keyword-Argument bei der `PhotoOpportunity(...)`-Konstruktion gesetzt
(nicht über `new_event["title"]` + zentralen Baustein). Code-Verifikation (nicht nur
Beobachtung) bestätigt: alle 9 dortigen Titel-Zuweisungen referenzieren bereits
`location.name` oder `location.subject_name`. Damit dieses zweite Baumuster künftig
ebenso automatisch gewächtert ist, prüft `test_konsistenz_waechter_opportunity_py_...`
unten per AST-Analyse jede `PhotoOpportunity(...)`-Konstruktion in
`calculations/opportunity.py` auf eine erkennbare Location-/Motiv-Referenz — additiv,
ohne den produktiv laufenden Code der bestehenden Chancenarten anzufassen (Variante A;
Variante B — Umbau auf den main.py-Baustein — wurde verworfen, weil dafür kein
funktionaler Defekt vorliegt und der Umbau unnötiges Regressionsrisiko für bereits
als Done markierte, stabile Chancenarten bedeuten würde).
"""
import ast
import copy
import inspect
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

pytestmark = [pytest.mark.offline, pytest.mark.regression]

_SEED_LOCATION_ID = "test_bug94_seed_9f3a1c"  # siehe conftest.py::ensure_seed_location
_SEED_SUBJECT_NAME = "Test-Motiv"  # conftest.py::_seed_location_dict()


def _make_golden_event(event_type="Goldene Stunde Abend", gcs=0.82, sun_azimuth=278,
                        subject_azimuth=265, cl=40, cm=35, ch=10, location_id=_SEED_LOCATION_ID):
    """Minimaler Event-Dict mit Wetter-Daten, analog zu test_us109.py::_make_golden_event
    (dort für GOLDEN_CLOUDS/RED_SKY etabliert) — hier zusätzlich mit location_id, die
    auf die feste Test-Harness-Location zeigt (ensure_seed_location-Fixture), damit
    der Motiv-Lookup in _build_opportunity_title() einen echten Treffer liefert."""
    return {
        "id": "test-event-1",
        "event_type": event_type,
        "title": event_type,
        "description": "Test",
        "location_id": location_id,
        "location_name": "Test-Harness-Location (custom_1781560330)",
        "observer_lat": 52.5,
        "observer_lon": 13.4,
        "subject_lat": 52.51,
        "subject_lon": 13.41,
        "shoot_time": "2026-07-01T18:00:00+00:00",
        "shoot_window_start": "2026-07-01T17:45:00+00:00",
        "shoot_window_end": "2026-07-01T18:15:00+00:00",
        "astronomy_score": 0.85,
        "weather_score": 0.70,
        "overall_score": 0.79,
        "location_score": 0.90,
        "alert_priority": 1,
        "weather_status": "ok",
        "golden_cloud_score": gcs,
        "golden_cloud_score_sun_dir": gcs,
        "cl_sun_dir": cl,
        "cm_sun_dir": cm,
        "golden_cloud_score_antisolar_dir": gcs,
        "cl_antisolar_dir": cl,
        "cm_antisolar_dir": cm,
        "sunset_azimuth": sun_azimuth,
        "sunrise_azimuth": None,
        "subject_azimuth": subject_azimuth,
        "composition_analysis": None,
        "moon_phase": None,
        "moon_illumination_pct": None,
        "weather_description": "Teilweise bewölkt",
        "weather_details": {
            "temperature_c": 18.0,
            "precipitation_prob_pct": 10,
            "precipitation_mm": 0.0,
            "cloud_cover_pct": cl + cm + ch,
            "cloud_cover_low_pct": cl,
            "cloud_cover_mid_pct": cm,
            "cloud_cover_high_pct": ch,
            "wind_speed_kmh": 10,
            "wind_direction_deg": 270,
            "visibility_m": 15000,
        },
    }


def _make_blue_hour_event(event_type="Blaue Stunde", sun_altitude=-5, ch=45, cl=10,
                           sun_azimuth=280, subject_azimuth=275, location_id=_SEED_LOCATION_ID):
    """Minimaler Event-Dict für RED_CLOUDS (Blaue-Stunde-Pfad, analog test_us_132.py-
    Schwellwerten AK-1: sun_altitude=-5, ch=45>=20, cl=10<30, Azimut-Diff 5°<=30°)."""
    return {
        "id": "test-event-blue-1",
        "event_type": event_type,
        "title": event_type,
        "description": "Test",
        "location_id": location_id,
        "location_name": "Test-Harness-Location (custom_1781560330)",
        "observer_lat": 52.5,
        "observer_lon": 13.4,
        "subject_lat": 52.51,
        "subject_lon": 13.41,
        "shoot_time": "2026-07-01T21:00:00+00:00",
        "shoot_window_start": "2026-07-01T20:45:00+00:00",
        "shoot_window_end": "2026-07-01T21:15:00+00:00",
        "astronomy_score": 0.85,
        "weather_score": 0.70,
        "overall_score": 0.79,
        "location_score": 0.90,
        "alert_priority": 1,
        "weather_status": "ok",
        "golden_cloud_score": None,
        "golden_cloud_score_sun_dir": None,
        "golden_cloud_score_antisolar_dir": None,
        "celestial_altitude": sun_altitude,
        "celestial_azimuth": sun_azimuth,
        "subject_azimuth": subject_azimuth,
        "composition_analysis": None,
        "moon_phase": None,
        "moon_illumination_pct": None,
        "weather_description": "Teilweise bewölkt",
        "weather_details": {
            "temperature_c": 15.0,
            "precipitation_prob_pct": 5,
            "precipitation_mm": 0.0,
            "cloud_cover_pct": cl + ch,
            "cloud_cover_low_pct": cl,
            "cloud_cover_mid_pct": 0,
            "cloud_cover_high_pct": ch,
            "wind_speed_kmh": 8,
            "wind_direction_deg": 260,
            "visibility_m": 20000,
        },
    }


# ---------------------------------------------------------------------------
# Testfälle 1-3: Titel-Muster je Wolkenstimmungs-Chancenart (AK 1+2)
# ---------------------------------------------------------------------------

def test_goldene_wolken_titel_nennt_motiv(ensure_seed_location):
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event()]
    neue, _ = _generate_cloud_mood_events(feed)
    gc = next((e for e in neue if e["event_type"] == "Goldene Wolken"), None)
    assert gc is not None, "GOLDEN_CLOUDS-Event wurde nicht erzeugt"
    assert gc["title"] == f"Goldene Wolken über {_SEED_SUBJECT_NAME}", gc["title"]


def test_himmelsroete_titel_nennt_motiv(ensure_seed_location):
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.85, cl=40, cm=35, subject_azimuth=85)]
    neue, _ = _generate_cloud_mood_events(feed)
    rs = next((e for e in neue if e["event_type"] == "Himmelsröte"), None)
    assert rs is not None, "RED_SKY-Event wurde nicht erzeugt"
    assert rs["title"] == f"Himmelsröte über {_SEED_SUBJECT_NAME}", rs["title"]


def test_rote_wolken_titel_nennt_motiv(ensure_seed_location):
    from main import _generate_cloud_mood_events

    feed = [_make_blue_hour_event()]
    neue, _ = _generate_cloud_mood_events(feed)
    rc = next((e for e in neue if e["event_type"] == "Rote Wolken"), None)
    assert rc is not None, "RED_CLOUDS-Event wurde nicht erzeugt"
    assert rc["title"] == f"Rote Wolken über {_SEED_SUBJECT_NAME}", rc["title"]


# ---------------------------------------------------------------------------
# Testfall 4: Fallback bei nicht auflösbarer location_id (Pre-Mortem Szenario 1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("event_type_label,make_event,build_kwargs", [
    ("Goldene Wolken", _make_golden_event, {}),
    ("Himmelsröte", _make_golden_event, {"gcs": 0.85, "cl": 40, "cm": 35, "subject_azimuth": 85}),
    ("Rote Wolken", _make_blue_hour_event, {}),
], ids=["goldene_wolken", "himmelsroete", "rote_wolken"])
def test_fallback_auf_alten_titel_bei_unbekannter_location_id(event_type_label, make_event, build_kwargs):
    from main import _generate_cloud_mood_events

    event = make_event(location_id="does-not-exist-anywhere", **build_kwargs)
    feed = [event]
    neue, _ = _generate_cloud_mood_events(feed)
    treffer = next((e for e in neue if e["event_type"] == event_type_label), None)
    assert treffer is not None, f"{event_type_label}-Event wurde nicht erzeugt"
    assert treffer["title"] == event_type_label, (
        f"Fallback-Titel falsch: erwartet reinen Event-Typ-Namen '{event_type_label}', "
        f"bekommen '{treffer['title']}' (kein 'undefined'/'None' erlaubt)"
    )
    assert "None" not in treffer["title"] and "undefined" not in treffer["title"]


# ---------------------------------------------------------------------------
# Testfall 5: Titel != Standort-Zeilen-Text (Pre-Mortem Szenario 2 — verhindert
# umgekehrte Dopplung durch versehentliche Nutzung von location.name statt
# location.subject_name)
# ---------------------------------------------------------------------------

def test_titel_ist_nicht_identisch_mit_standort_zeile(ensure_seed_location):
    from main import _generate_cloud_mood_events, get_location_by_id

    feed = [_make_golden_event()]
    neue, _ = _generate_cloud_mood_events(feed)
    gc = next((e for e in neue if e["event_type"] == "Goldene Wolken"), None)
    assert gc is not None
    location = get_location_by_id(_SEED_LOCATION_ID)
    assert location is not None
    # Standort-Zeile zeigt location.name (Vor-Ort-Standpunkt), Titel muss davon abweichen.
    assert gc["title"] != location.name
    assert location.name not in gc["title"]


# ---------------------------------------------------------------------------
# Konsistenz-Wächter: iteriert automatisch über ALLE main.py-Funktionen im
# Namensmuster `_build_*_event`, die new_event["title"] setzen (unabhängig von
# einer manuell gepflegten Liste — ein künftig neu hinzugefügter Chancenart-
# Builder wird automatisch erfasst, ohne dass jemand daran denken muss, einen
# neuen Einzeltest zu schreiben).
# ---------------------------------------------------------------------------

def _title_setting_opportunity_builders():
    """Findet alle Funktionen in main.py, deren Name dem Muster `_build_*_event`
    folgt UND die `new_event["title"]` setzen (= Chancenart-Builder, die einen
    Karten-/Kalender-/Detail-Titel erzeugen). Rein statische Quelltext-Analyse,
    kein Aufruf der Funktionen nötig — funktioniert daher unabhängig davon, ob
    ein Builder überhaupt mit synthetischen Testdaten auslösbar ist."""
    import main

    treffer = []
    for name, func in inspect.getmembers(main, inspect.isfunction):
        if func.__module__ != main.__name__:
            continue  # nur in main.py selbst definierte Funktionen, keine Importe
        if not re.match(r"^_build_.*_event$", name):
            continue
        src = inspect.getsource(func)
        if 'new_event["title"]' in src or "new_event['title']" in src:
            treffer.append((name, src))
    return treffer


def test_konsistenz_waechter_alle_chancenart_builder_nutzen_zentralen_titel_baustein():
    """BUG-94: generischer Wächter-Test — keine Chancenart-Builder-Funktion darf
    new_event["title"] mit einem hartkodierten Literal-String setzen; jede muss den
    zentralen Baustein main._build_opportunity_title() verwenden. Fliegt automatisch
    für jeden künftig neu hinzugefügten Builder mit, ohne Anpassung dieses Tests."""
    builders = _title_setting_opportunity_builders()
    # Mindestens die drei aus BUG-94 bekannten Wolkenstimmungs-Builder müssen erfasst sein
    # — schlägt fehl, falls die Autodiscovery selbst kaputtgeht (z. B. main.py umbenannt).
    gefundene_namen = {name for name, _ in builders}
    erwartet = {"_build_golden_clouds_event", "_build_red_sky_event", "_build_red_clouds_event"}
    assert erwartet.issubset(gefundene_namen), (
        f"Autodiscovery hat nicht alle bekannten Wolkenstimmungs-Builder gefunden. "
        f"Gefunden: {gefundene_namen}, erwartet mindestens: {erwartet}"
    )

    verstoesse = []
    for name, src in builders:
        nutzt_zentralen_baustein = "_build_opportunity_title(" in src
        hat_literal_titel = bool(re.search(r'new_event\["title"\]\s*=\s*"', src))
        if not nutzt_zentralen_baustein or hat_literal_titel:
            verstoesse.append(name)

    assert not verstoesse, (
        f"Folgende Chancenart-Builder setzen new_event['title'] nicht (nur) über den "
        f"zentralen Baustein _build_opportunity_title() — genau die BUG-94-Fehlerklasse "
        f"(Titel dupliziert den Event-Typ statt das Motiv zu nennen): {verstoesse}. "
        f"Bitte new_event['title'] = _build_opportunity_title(new_event['event_type'], "
        f"e.get('location_id')) verwenden statt eines Literal-Strings."
    )


# ---------------------------------------------------------------------------
# Konsistenz-Wächter 2 (2026-07-31): zweites Baumuster in
# calculations/opportunity.py — Titel wird als title=f"..."-Keyword-Argument
# direkt bei der PhotoOpportunity(...)-Konstruktion gesetzt, nicht über
# new_event["title"]. Rein statische AST-Analyse (kein Funktionsaufruf nötig),
# findet automatisch JEDE PhotoOpportunity(...)-Konstruktion in der Datei —
# unabhängig von einer manuell gepflegten Liste. Ein künftig neu hinzugefügter
# Chancenart-Block, der dort ein title=f"..." ohne Location-/Motiv-Referenz
# setzt (oder einen reinen Literal-String statt eines f-Strings), lässt diesen
# Test automatisch rot laufen, ohne dass jemand daran denken muss, einen neuen
# Einzeltest zu schreiben.
# ---------------------------------------------------------------------------

def _opportunity_py_title_keywords():
    """Findet per AST-Analyse alle title=...-Keyword-Argumente in
    PhotoOpportunity(...)-Konstruktoraufrufen in calculations/opportunity.py.
    Gibt eine Liste von (lineno, ast_node) zurück."""
    import calculations.opportunity as opp_module

    quelle = inspect.getsource(opp_module)
    baum = ast.parse(quelle)
    treffer = []
    for node in ast.walk(baum):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name != "PhotoOpportunity":
            continue
        for kw in node.keywords:
            if kw.arg == "title":
                treffer.append((node.lineno, kw.value))
    return treffer


def _references_location_name_or_subject(value_node):
    """True wenn irgendwo im Ausdrucksbaum ein `location.name` oder
    `location.subject_name`-Zugriff vorkommt (location = der Parametername in
    find_opportunities()/find_opportunities_multi_day())."""
    for sub in ast.walk(value_node):
        if isinstance(sub, ast.Attribute) and sub.attr in ("name", "subject_name"):
            if isinstance(sub.value, ast.Name) and sub.value.id == "location":
                return True
    return False


def test_konsistenz_waechter_opportunity_py_alle_titel_haben_location_bezug():
    """BUG-94-Erweiterung: deckt das zweite Titel-Baumuster in
    calculations/opportunity.py ab (siehe Modul-Docstring). Jede
    PhotoOpportunity(...)-Konstruktion muss ein title=f"..." mit einer
    erkennbaren Location-/Motiv-Referenz (location.name oder
    location.subject_name) haben — kein reiner, nicht-interpolierter
    Event-Typ-String (f-String-Pflicht = ast.JoinedStr statt ast.Constant)."""
    treffer = _opportunity_py_title_keywords()

    # Sanity-Check der Autodiscovery selbst: mindestens die zum Zeitpunkt dieser
    # Erweiterung bekannten 9 Konstruktionsstellen müssen gefunden werden — schlägt
    # fehl, falls die AST-Suche kaputtgeht (z.B. PhotoOpportunity umbenannt).
    assert len(treffer) >= 9, (
        f"Autodiscovery hat unerwartet wenige PhotoOpportunity-Titel-Zuweisungen "
        f"gefunden ({len(treffer)}) — evtl. ist die AST-Suche selbst kaputt."
    )

    verstoesse = []
    for lineno, value_node in treffer:
        ist_f_string = isinstance(value_node, ast.JoinedStr)
        hat_location_bezug = _references_location_name_or_subject(value_node)
        if not ist_f_string or not hat_location_bezug:
            segment = ast.dump(value_node)
            verstoesse.append(f"Zeile {lineno}: {segment}")

    assert not verstoesse, (
        "Folgende PhotoOpportunity-Titel in calculations/opportunity.py haben keine "
        "erkennbare Location-/Motiv-Referenz (location.name / location.subject_name) "
        "oder sind kein f-String — potenzielle BUG-94-Fehlerklasse in einem neuen "
        f"Chancenart-Block: {verstoesse}. Bitte title=f\"...{{location.name}}\" bzw. "
        f"title=f\"...{{location.subject_name}}\" verwenden."
    )
