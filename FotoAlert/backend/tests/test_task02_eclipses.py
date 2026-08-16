"""TASK-02: Sonnenfinsternisse + Mondfinsternisse (vier Typen, Berlin/BB-Region).

Ticket TASK-02, Option A (Skyfield-Kontaktsuche für Sonne, `eclipselib.lunar_eclipses()`
für Mond, einmal pro Precompute-Zeitfenster via Jahres-Cache statt pro Location, AK-12).

Jeder Test hier ist aus einem Akzeptanzkriterium des Tickets abgeleitet und prüft, wo
irgend möglich, gegen ein REALES, extern verifizierbares Ereignis statt gegen einen
synthetischen Wert (Pre-Mortem Szenario 2: "kein automatischer Test kann einen subtilen
Geometriefehler zuverlässig selbst aufdecken, ohne gegen ein bekanntes reales Ereignis
geprüft zu werden"):

- Sonnenfinsternis 12.08.2026: laut Analyse-Spec live-verifiziert (Skyfield 1.49 +
  de421.bsp) — von Berlin aus PARTIELL (Sonne-Mond-Trennung ≈0,075° um 18:08 UTC,
  Sonnenhöhe ≈3,3°), von Reykjavik (64,1466°N/21,9426°W, auf der Totalitätsbahn) aus TOTAL
  (Quelle: Wikipedia "Solar eclipse of August 12, 2026" — Maximum global ≈17:47 UTC vor
  Islands Westküste; hier via eigener Skyfield-Berechnung für Reykjavik reproduziert).
- Sonnenfinsternis 08.04.2024 (Nordamerika, real total dort): von Berlin aus geometrisch
  ein Kontaktfenster, aber Sonne dort zu dieser Uhrzeit unter dem Horizont (Berlin-Abend/
  Nacht) — AK-16-Guard-Testfall.
- Mondfinsternisse 07.09.2025 (total, Wikipedia "September 2025 lunar eclipse": Maximum
  18:11:43 UTC), 18.09.2024 (partiell) und 14.03.2025 (total, aber Maximum tagsüber in
  Berlin -> Mond unter Horizont, AK-5-Guard-Testfall) sowie 25.03.2024 (penumbral, muss
  laut Annahmen-Protokoll ausgeschlossen bleiben) — alle direkt über Skyfields eigene
  `eclipselib.lunar_eclipses()` gegen den Ephemeris-Datensatz nachvollzogen.

Marker: `online`, weil `_get_eph()` `de421.bsp` lädt (liegt lokal in backend/, aber wie bei
den bestehenden Astronomie-Tests als "online" markiert, siehe test_astronomy_regression.py).
"""
import asyncio
import math
import logging
import time
from datetime import date, datetime, timezone

import pytest

from calculations import astronomy as A
from calculations.opportunity import EventType, find_opportunities
from data.locations import PhotoLocation, LocationCategory

import precompute as P

pytestmark = [pytest.mark.regression, pytest.mark.online]

BERLIN_LAT = 52.52
BERLIN_LON = 13.405
REYKJAVIK_LAT = 64.1466
REYKJAVIK_LON = -21.9426


# ---------------------------------------------------------------------------
# AK-13 (Datenqualität, Pre-Mortem Szenario 2+3): Referenzereignis 12.08.2026
# ---------------------------------------------------------------------------

def test_ak13_solar_eclipse_2026_08_12_berlin_matches_live_reference():
    events = A.find_solar_eclipses(date(2026, 8, 10), date(2026, 8, 14), lat=BERLIN_LAT, lon=BERLIN_LON)
    assert len(events) == 1, f"Erwartet genau 1 Sonnenfinsternis im Fenster, bekam {len(events)}"
    ev = events[0]
    assert ev.date == date(2026, 8, 12)
    # Live-Referenz aus der Analyse-Spec: ≈0,0748° um 18:08 UTC, Sonnenhöhe ≈3,37°.
    assert math.isclose(ev.max_separation_deg, 0.0748, abs_tol=0.02), ev.max_separation_deg
    assert ev.max_time.hour == 18 and abs(ev.max_time.minute - 8) <= 5, ev.max_time


# --- AK-1/AK-2: Klassifizierung total vs. partiell (Sonne) -------------------------

def test_ak2_solar_eclipse_2026_08_12_berlin_is_partial_not_total():
    events = A.find_solar_eclipses(date(2026, 8, 10), date(2026, 8, 14), lat=BERLIN_LAT, lon=BERLIN_LON)
    ev = events[0]
    assert ev.is_total is False, "Berlin liegt nicht auf der Totalitätsbahn (Pre-Mortem Szenario 3)"
    assert ev.visible is True


def test_ak1_solar_eclipse_2026_08_12_reykjavik_is_total():
    """Pre-Mortem Szenario 3: Totalität für Berlin praktisch nie -> Code-Pfad gegen
    einen Ort auf der realen Totalitätsbahn desselben Ereignisses verifizieren.

    HINWEIS (Lücken-Schließung 2026-08-14): Es gibt hier bewusst KEIN Opportunity-
    Integrationstest-Pendant (analog test_ak2_opportunity_has_partial_solar_eclipse_type/
    test_ak3_opportunity_has_lunar_eclipse_type). Grund: `find_opportunities()` ruft
    `get_solar_eclipse_for_date(target_date)` in opportunity.py OHNE lat/lon auf, das
    Ergebnis basiert also immer auf dem festen Berlin/BB-Referenzpunkt
    (BERLIN_REF_LAT/BERLIN_REF_LON in astronomy.py), unabhängig davon, welche
    PhotoLocation (auch mit eigenen, abweichenden observer_lat/observer_lon wie hier
    Reykjavik) an find_opportunities() übergeben wird. Ein Opportunity-Objekt mit
    EventType.ECLIPSE (Totalität) kann dieser Code-Pfad für den praktisch relevanten
    Planungshorizont daher nie erzeugen, weil Berlin selbst laut Pre-Mortem Szenario 3
    nie Totalität erreicht — das ist im Ticket explizit als "kein Bug, sondern zu
    dokumentierender Zustand" festgehalten. Ein Test, der hier trotzdem eine
    PhotoOpportunity mit EventType.ECLIPSE erwartet, würde entweder real fehlschlagen
    oder nur durch Monkeypatchen der lat/lon-Weitergabe künstlich zum Bestehen gebracht
    -- beides wäre kein ehrlicher Beleg für echtes Produktionsverhalten. Diese Lücke ist
    daher NICHT über einen neuen Test geschlossen, sondern hier dokumentiert; siehe
    BACKLOG.md TASK-02 für die volle Einordnung."""
    events = A.find_solar_eclipses(date(2026, 8, 10), date(2026, 8, 14), lat=REYKJAVIK_LAT, lon=REYKJAVIK_LON)
    assert len(events) == 1
    ev = events[0]
    assert ev.is_total is True
    assert ev.visible is True


# --- Edge Case AK-16: Sichtbarkeits-Guard Sonnenfinsternis --------------------------

def test_ak16_solar_eclipse_invisible_when_sun_below_horizon():
    """Reale totale Sonnenfinsternis 08.04.2024 (Nordamerika) — von Berlin aus rein
    geometrisch ein Kontaktfenster, aber dort zu dieser Uhrzeit Nacht (Sonne < 0°)."""
    events = A.find_solar_eclipses(date(2024, 4, 6), date(2024, 4, 10), lat=BERLIN_LAT, lon=BERLIN_LON)
    assert len(events) == 1, "Geometrisches Kontaktfenster muss trotzdem gefunden werden"
    ev = events[0]
    assert ev.visible is False, "Sonne unter dem Horizont -> darf keine Foto-Chance ergeben"


# --- Edge Case AK-11: leeres Zeitfenster --------------------------------------------

def test_ak11_no_solar_eclipse_in_ordinary_window():
    events = A.find_solar_eclipses(date(2026, 1, 1), date(2026, 1, 31), lat=BERLIN_LAT, lon=BERLIN_LON)
    assert events == []


def test_ak11_no_lunar_eclipse_in_ordinary_window():
    events = A.find_lunar_eclipses(date(2026, 1, 1), date(2026, 1, 31), lat=BERLIN_LAT, lon=BERLIN_LON)
    assert events == []


# --- AK-3/AK-4: Klassifizierung total vs. partiell (Mond) ---------------------------

def test_ak3_lunar_eclipse_total_visible_2025_09_07():
    """Real: totale Mondfinsternis 07.09.2025, Maximum 18:11:43 UTC (Wikipedia
    "September 2025 lunar eclipse"), in Berlin bei Mondaufgang sichtbar."""
    events = A.find_lunar_eclipses(date(2025, 9, 1), date(2025, 9, 15), lat=BERLIN_LAT, lon=BERLIN_LON)
    assert len(events) == 1
    ev = events[0]
    assert ev.date == date(2025, 9, 7)
    assert ev.is_total is True
    assert ev.visible is True
    assert ev.max_time.hour == 18 and abs(ev.max_time.minute - 11) <= 5, ev.max_time


def test_ak4_lunar_eclipse_partial_visible_2024_09_18():
    """Real: partielle Mondfinsternis 18.09.2024, in Berlin sichtbar (Mond hoch am Himmel)."""
    events = A.find_lunar_eclipses(date(2024, 9, 10), date(2024, 9, 25), lat=BERLIN_LAT, lon=BERLIN_LON)
    assert len(events) == 1
    ev = events[0]
    assert ev.is_total is False
    assert ev.visible is True


# --- Edge Case AK-5: Sichtbarkeits-Guard Mondfinsternis -----------------------------

def test_ak5_lunar_eclipse_guard_moon_below_horizon_2025_03_14():
    """Real: totale Mondfinsternis 14.03.2025 — Maximum liegt tagsüber in Berlin,
    Mond dort zu diesem Zeitpunkt unter dem Horizont (Pre-Mortem Szenario 4)."""
    events = A.find_lunar_eclipses(date(2025, 3, 10), date(2025, 3, 20), lat=BERLIN_LAT, lon=BERLIN_LON)
    assert len(events) == 1
    ev = events[0]
    assert ev.is_total is True
    assert ev.visible is False, "Mond unter dem Horizont -> darf keine Foto-Chance ergeben"


def test_penumbral_lunar_eclipses_are_excluded():
    """Annahmen-Protokoll: penumbrale Mondfinsternisse werden NICHT als eigener Typ
    geführt. Real: 25.03.2024 war eine reine penumbrale Mondfinsternis."""
    events = A.find_lunar_eclipses(date(2024, 3, 20), date(2024, 3, 30), lat=BERLIN_LAT, lon=BERLIN_LON)
    assert events == [], "Penumbrale Mondfinsternis darf nicht als Partial/Total auftauchen"


# ---------------------------------------------------------------------------
# AK-12 (Performance, Pre-Mortem Szenario 1): Kontaktzeiten-Suche läuft einmal
# pro Zeitfenster (hier: pro Kalenderjahr gecacht), nicht pro Location/Aufruf.
# ---------------------------------------------------------------------------

def test_ak12_solar_eclipse_search_is_cached_per_year(monkeypatch):
    # Sauberer Ausgangszustand: andere Tests in dieser Session können den Jahres-Cache
    # für 2026/Berlin bereits gefüllt haben (das ist ja genau der gewünschte Effekt des
    # Caches) — für eine ehrliche "wird nur 1x berechnet"-Aussage hier isoliert zurücksetzen.
    monkeypatch.setattr(A, "_SOLAR_ECLIPSE_CACHE", {})
    calls = []
    original = A._compute_solar_eclipses_for_year

    def _counting(year, lat, lon):
        calls.append(year)
        return original(year, lat, lon)

    monkeypatch.setattr(A, "_compute_solar_eclipses_for_year", _counting)
    # Simuliert 3 verschiedene Locations (wie im Precompute-Batch), die alle im selben
    # Zeitfenster/Jahr nach Finsternissen fragen.
    A.find_solar_eclipses(date(2026, 8, 1), date(2026, 8, 20), lat=BERLIN_LAT, lon=BERLIN_LON)
    A.get_solar_eclipse_for_date(date(2026, 8, 12), lat=BERLIN_LAT, lon=BERLIN_LON)
    A.get_solar_eclipse_for_date(date(2026, 8, 5), lat=BERLIN_LAT, lon=BERLIN_LON)
    assert len(calls) == 1, f"Erwartet 1 echte Berechnung pro Jahr (gecacht), bekam {len(calls)}: {calls}"


def test_ak12_lunar_eclipse_search_is_cached_per_year(monkeypatch):
    monkeypatch.setattr(A, "_LUNAR_ECLIPSE_CACHE", {})
    calls = []
    original = A._compute_lunar_eclipses_for_year

    def _counting(year, lat, lon):
        calls.append(year)
        return original(year, lat, lon)

    monkeypatch.setattr(A, "_compute_lunar_eclipses_for_year", _counting)
    # Alle drei Abfragen liegen im selben Jahr 2025 -> genau 1 echte Berechnung erwartet
    # (die 07.09. und 14.03. sind beide 2025, also derselbe Cache-Key).
    A.find_lunar_eclipses(date(2025, 9, 1), date(2025, 9, 15), lat=BERLIN_LAT, lon=BERLIN_LON)
    A.get_lunar_eclipse_for_date(date(2025, 9, 7), lat=BERLIN_LAT, lon=BERLIN_LON)
    A.get_lunar_eclipse_for_date(date(2025, 3, 14), lat=BERLIN_LAT, lon=BERLIN_LON)
    assert len(calls) == 1, f"Erwartet 1 Berechnung für Jahr 2025 (gecacht), bekam {calls}"


def test_ak12_solar_eclipse_search_uncached_vs_cached_timing_in_seconds(monkeypatch):
    """AK-12 wörtlich verlangt eine "Vorher/Nachher-Messung in Sekunden". Die beiden
    Tests oben belegen nur die Aufrufzahl (1x statt 3x) — hier zusätzlich eine echte
    Zeitmessung mit `time.perf_counter()`, die zeigt: (a) der zweite (gecachte) Aufruf
    für dasselbe Jahr ist um mindestens eine Größenordnung schneller als der erste
    (ungecachte) Aufruf, und (b) der gecachte Pfad ist absolut so schnell, dass auch
    200 Locations im selben Precompute-Zeitfenster (realistische Location-Zahl laut
    Ticket-Pre-Mortem Szenario 1) nicht spürbar ins Gewicht fallen — während ein
    fälschlich pro-Location statt pro-Zeitfenster implementierter (also stets
    ungecachter) Lauf bei 200 Locations bereits klar spürbar wäre. Bewusst robuste,
    relative statt eng-absolute Schwellen, um auf einer langsameren Maschine nicht zu
    flackern."""
    monkeypatch.setattr(A, "_SOLAR_ECLIPSE_CACHE", {})

    t0 = time.perf_counter()
    A.find_solar_eclipses(date(2026, 1, 1), date(2026, 12, 31), lat=BERLIN_LAT, lon=BERLIN_LON)
    uncached_seconds = time.perf_counter() - t0

    t1 = time.perf_counter()
    A.find_solar_eclipses(date(2026, 1, 1), date(2026, 12, 31), lat=BERLIN_LAT, lon=BERLIN_LON)
    cached_seconds = time.perf_counter() - t1

    # (a) Cache muss einen deutlichen, mind. eine Größenordnung großen Vorteil bringen.
    assert cached_seconds * 10 < uncached_seconds, (
        f"Gecachter Aufruf ist nicht deutlich schneller als der ungecachte Erstaufruf: "
        f"uncached={uncached_seconds:.4f}s, cached={cached_seconds:.4f}s"
    )
    # (b) Gecachter Pfad bleibt bei 200 Locations (Pre-Mortem Szenario 1) unauffällig.
    assert cached_seconds * 200 < 1.0, (
        f"200x gecachter Aufruf wäre bereits spürbar: {cached_seconds * 200:.3f}s "
        f"({cached_seconds:.4f}s je Aufruf)"
    )
    # Dokumentiert das eigentliche Pre-Mortem-Risiko (Szenario 1): würde die teure
    # Kontaktsuche fälschlich pro Location statt einmal pro Zeitfenster laufen, wäre
    # das bei 200 Locations klar spürbar -- genau deshalb ist das Einmal-pro-Fenster-
    # Muster (belegt durch die beiden Cache-Zähl-Tests oben) performancekritisch.
    naive_200x_seconds = uncached_seconds * 200
    assert naive_200x_seconds > cached_seconds * 200, (
        "Ein naiver Pro-Location-Lauf müsste messbar teurer sein als der gecachte Batch-Lauf"
    )


# ---------------------------------------------------------------------------
# AK-14 (Regression): bestehende Alignment-Filter-Ausnahmen bleiben erhalten,
# die drei neuen Typen kommen hinzu.
# ---------------------------------------------------------------------------

def test_ak14_alignment_filter_exempt_contains_existing_and_new_eclipse_types():
    exempt = P._ALIGNMENT_FILTER_EXEMPT
    # Bestehend (vor TASK-02) — darf nicht verschwinden.
    assert "Sonnenfinsternis" in exempt
    assert "Mond-Alignment" not in exempt  # Mond-Alignment ist NICHT exempt (bewusst, US-57)
    # Neu durch TASK-02.
    assert EventType.PARTIAL_SOLAR_ECLIPSE.value in exempt
    assert EventType.LUNAR_ECLIPSE.value in exempt
    assert EventType.PARTIAL_LUNAR_ECLIPSE.value in exempt


# ---------------------------------------------------------------------------
# AK-15 (Beobachtbarkeit im Fehlerfall): Ein Fehler bei einem einzelnen Datum
# bricht die Gesamtberechnung nicht ab und wird mit Datum+Fehlerart geloggt.
# ---------------------------------------------------------------------------

def test_ak15_single_candidate_error_does_not_abort_whole_year_and_is_logged(monkeypatch, caplog):
    original = A._solar_eclipse_event_for_new_moon
    call_count = {"n": 0}

    def _boom(new_moon_dt, lat, lon):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ValueError("simulierter numerischer Randfall (TASK-02 AK-15-Test)")
        return original(new_moon_dt, lat, lon)

    monkeypatch.setattr(A, "_solar_eclipse_event_for_new_moon", _boom)
    with caplog.at_level(logging.ERROR, logger="calculations.astronomy"):
        # 2026 hat mehrere Neumonde; der erste (fehlschlagende) darf den Rest nicht kippen.
        events = A._compute_solar_eclipses_for_year(2026, BERLIN_LAT, BERLIN_LON)

    # Trotz simuliertem Fehler beim ersten Kandidaten: das reale Ereignis vom 12.08.2026
    # muss weiterhin gefunden werden (Gesamtlauf nicht abgebrochen).
    assert any(e.date == date(2026, 8, 12) for e in events), (
        "Ein Fehler bei einem Neumond-Kandidaten darf die übrigen nicht verhindern"
    )
    error_logs = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert error_logs, "Fehler muss geloggt werden (AK-15: Datum + Fehlerart)"
    assert any("ValueError" in r.message or "ValueError" in str(r.exc_info) for r in error_logs), (
        "Log-Eintrag muss die Fehlerart enthalten"
    )
    assert any("2026" in r.message for r in error_logs), "Log-Eintrag muss das betroffene Datum/Jahr enthalten"


# ---------------------------------------------------------------------------
# Integrationsebene (opportunity.py): AK-1..AK-4 als tatsächliche PhotoOpportunity
# ---------------------------------------------------------------------------

def _make_berlin_location() -> PhotoLocation:
    return PhotoLocation(
        id="task02-test-loc",
        name="TASK-02 Test-Location",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=BERLIN_LAT, observer_lon=BERLIN_LON,
        subject_lat=52.5163, subject_lon=13.3777,
        subject_name="Test-Motiv",
    )


def test_ak2_opportunity_has_partial_solar_eclipse_type():
    loc = _make_berlin_location()
    opps = asyncio.run(find_opportunities(loc, date(2026, 8, 12), forecast=None, min_score=0.1, astronomy_only=True))
    types = [o.event_type for o in opps]
    assert EventType.PARTIAL_SOLAR_ECLIPSE in types, f"Erwartet PARTIAL_SOLAR_ECLIPSE in {types}"


def test_ak3_opportunity_has_lunar_eclipse_type():
    loc = _make_berlin_location()
    opps = asyncio.run(find_opportunities(loc, date(2025, 9, 7), forecast=None, min_score=0.1, astronomy_only=True))
    types = [o.event_type for o in opps]
    assert EventType.LUNAR_ECLIPSE in types, f"Erwartet LUNAR_ECLIPSE in {types}"


def test_ak4_opportunity_has_partial_lunar_eclipse_type():
    """Fehlendes Pendant zu test_ak3_opportunity_has_lunar_eclipse_type (Lücken-Schließung
    2026-08-14): bestätigt, dass für das reale partielle Mondfinsternis-Referenzereignis
    vom 18.09.2024 tatsächlich eine PhotoOpportunity mit EventType.PARTIAL_LUNAR_ECLIPSE
    entsteht — nicht nur die Astronomie-Ebene (s. test_ak4_lunar_eclipse_partial_visible_
    2024_09_18 oben). Anders als beim AK-1/Reykjavik-Fall (s. Hinweis dort) fällt die
    Berlin-Test-Location hier mit dem hartcodierten Berlin/BB-Referenzpunkt zusammen, mit
    dem opportunity.py get_lunar_eclipse_for_date() aufruft — der Test ist damit ein
    echter End-to-End-Beleg für AK-4, kein Näherungswert."""
    loc = _make_berlin_location()
    opps = asyncio.run(find_opportunities(loc, date(2024, 9, 18), forecast=None, min_score=0.1, astronomy_only=True))
    types = [o.event_type for o in opps]
    assert EventType.PARTIAL_LUNAR_ECLIPSE in types, f"Erwartet PARTIAL_LUNAR_ECLIPSE in {types}"


def test_ak5_opportunity_has_no_lunar_eclipse_when_invisible():
    loc = _make_berlin_location()
    opps = asyncio.run(find_opportunities(loc, date(2025, 3, 14), forecast=None, min_score=0.1, astronomy_only=True))
    types = [o.event_type for o in opps]
    assert EventType.LUNAR_ECLIPSE not in types, f"Mond unter Horizont -> keine Foto-Chance, bekam {types}"
    assert EventType.PARTIAL_LUNAR_ECLIPSE not in types
