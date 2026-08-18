"""
US-135 - Scout: Nur zugaengliche Standorte mit freier Sicht vorschlagen.

Tests fuer backend/discover/accessibility.py (Clusterung + Filterentscheidung)
und die neuen US-135-Funktionen in backend/data/qa_azimuth.py (kombinierte
Overpass-Live-Anfrage + Tage-Cache, Implementierungsoption A). Alle
Overpass-Antworten sind gemockt -- kein echter Netzwerkzugriff im Test
(Marker: offline). Aus den US-135-Akzeptanzkriterien abgeleitet
(Marker: regression).

Python-3.9-kompatibel.
"""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path
import sys

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data import qa_azimuth
from discover import accessibility
from discover.pipeline_base import ScoutOpportunity

pytestmark = [pytest.mark.offline, pytest.mark.regression]


@pytest.fixture(autouse=True)
def _reset_scout_access_cache_singleton(monkeypatch):
    """Der Modul-Cache (_scout_access_cache_entries) ist ein Prozess-weiter
    Singleton (lazy geladen) -- fuer isolierte Tests vor JEDEM Test auf
    'noch nicht geladen' zuruecksetzen (analog test_task59_local_building_cache.py)."""
    monkeypatch.setattr(qa_azimuth, "_scout_access_cache_entries", None)


@pytest.fixture(autouse=True)
def _no_rate_limit_sleep(monkeypatch):
    monkeypatch.setattr(qa_azimuth, "OVERPASS_RATE_LIMIT_PAUSE_S", 0.0)


def _make_candidate(
    standpoint_lat=52.5000, standpoint_lon=13.4000,
    subject_lat=52.5010, subject_lon=13.4010,
    subject_id="testmotiv",
):
    """Minimaler ScoutOpportunity-Testkandidat -- nur die fuer US-135
    relevanten Felder werden ausgewertet, die uebrigen sind Platzhalter."""
    return ScoutOpportunity(
        body_name="moon",
        subject_id=subject_id,
        subject_name="Test-Motiv",
        subject_lat=subject_lat,
        subject_lon=subject_lon,
        day="2026-08-10",
        session="golden_evening",
        dt_utc="2026-08-10T18:00:00Z",
        body_azimuth_deg=180.0,
        body_altitude_deg=10.0,
        body_illumination_pct=None,
        distance_m=200.0,
        standpoint_lat=standpoint_lat,
        standpoint_lon=standpoint_lon,
        focal_length_equiv_mm=50.0,
        score=0.8,
        score_alignment=0.8,
        score_phase=0.8,
        score_licht=0.8,
        score_komposition=0.8,
        score_wetter=0.8,
        weather_description="Klarer Himmel",
    )


def _empty_data():
    return {"buildings": [], "forest_ways": [], "water_ways": [], "rail_ways": [], "path_ways": []}


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    """Fake httpx.Client, der immer die gleiche Payload liefert und die
    gesendete Query (im 'data'-Feld des POST-Aufrufs) fuer Assertions
    zwischenspeichert -- Vorbild: test_task59_local_building_cache.py /
    test_task59_own_overpass.py."""
    last_query = None

    def __init__(self, payload=None, *args, **kwargs):
        self._payload = payload if payload is not None else {"elements": []}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, data=None, **kwargs):
        _FakeClient.last_query = (data or {}).get("data", "")
        return _FakeResponse(self._payload)


def _client_factory(payload):
    def _factory(*args, **kwargs):
        return _FakeClient(payload=payload)
    return _factory


class _AlwaysFailClient:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, *args, **kwargs):
        raise httpx.ConnectError("simulierter Overpass-Ausfall")


# ---------------------------------------------------------------------------
# AK1: freie Sicht + zugaenglich -> Kandidat bleibt in der Liste
# ---------------------------------------------------------------------------

def test_us135_frei_und_zugaenglich_bleibt_in_liste(monkeypatch):
    """US-135 AK1: Ein Scout-Vorschlag mit laut Live-Pruefung freier Sicht
    und ohne Ausschlussmerkmal erscheint in der Scout-Liste."""
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: _empty_data())
    c = _make_candidate()

    result = accessibility.filter_accessible_candidates([c])

    assert result == [c]


# ---------------------------------------------------------------------------
# AK2: Sichtlinie komplett durch Gebaeude blockiert -> ausgeblendet
# ---------------------------------------------------------------------------

def test_us135_sicht_durch_gebaeude_blockiert_wird_ausgeblendet(monkeypatch):
    """US-135 AK2: Ein Kandidat, dessen Sicht laut Live-Pruefung komplett
    durch ein Gebaeude blockiert ist, erscheint NICHT in der Liste."""
    c = _make_candidate(standpoint_lat=52.5000, standpoint_lon=13.4000,
                         subject_lat=52.5010, subject_lon=13.4000)
    # Breites Gebaeude direkt zwischen Standpunkt und Motiv (~55m noerdlich,
    # ~135m breit) -- ueberdeckt die Peilung zum Motiv vollstaendig.
    blocking_building = {
        "nodes": [
            (52.5004, 13.3990), (52.5004, 13.4010),
            (52.5006, 13.4010), (52.5006, 13.3990),
        ],
        "height_m": 20.0,
    }
    data = _empty_data()
    data["buildings"] = [blocking_building]
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: data)

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


# ---------------------------------------------------------------------------
# AK3: mitten im Wald ohne Weg -> ausgeblendet / mit Weg -> bleibt
# ---------------------------------------------------------------------------

def test_us135_wald_ohne_weg_wird_ausgeblendet(monkeypatch):
    """US-135 AK3: Ein Scout-Vorschlag mitten im Wald ohne erkennbaren Weg
    in der Naehe erscheint nicht in der Scout-Liste."""
    c = _make_candidate(standpoint_lat=52.5000, standpoint_lon=13.4000)
    forest_polygon = {"nodes": [
        (52.4990, 13.3990), (52.4990, 13.4010),
        (52.5010, 13.4010), (52.5010, 13.3990),
    ]}
    data = _empty_data()
    data["forest_ways"] = [forest_polygon]
    # kein path_ways-Eintrag -> kein Weg in der Naehe
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: data)

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


def test_us135_wald_mit_weg_in_der_naehe_bleibt_in_liste(monkeypatch):
    """US-135 Regel 2 (Beispiel 'Lichtung am Wegesrand'): Standpunkt liegt
    zwar in einer Waldflaeche, aber ein begehbarer Weg liegt innerhalb des
    bestaetigten 50m-Radius -> Kandidat bleibt in der Liste (kein
    faelschlicher Ausschluss guter, aber technisch bewaldeter Spots).

    BUG-101-Pflicht-Korrektur: Das Motiv wird hier bewusst EXPLIZIT auf
    (52.5000, 13.4100) gesetzt (statt der bisherigen Default-Koordinate aus
    _make_candidate, die zufaellig exakt auf einem Eckpunkt des unten
    definierten Wald-Polygons lag -- (52.5010, 13.4010)). Diese Eckpunkt-
    Deckungsgleichheit fuehrte dazu, dass die neue, seit BUG-101 zusaetzlich
    aufgerufene Sichtpruefung is_sightline_blocked_by_vegetation() (siehe
    accessibility.filter_accessible_candidates()) die Peilung zum Motiv
    faelschlich als exakt auf der Grenze des Wald-Winkelbereichs liegend
    einstufte und den Kandidaten faelschlich blockierte -- unabhaengig von
    der hier eigentlich getesteten Wald+Weg-Zugaenglichkeitsregel (US-135
    Regel 2). Die neue Motiv-Koordinate liegt klar ausserhalb der
    Wald-Bounding-Box (lat 52.4990-52.5010, lon 13.3990-13.4010) und
    ausserhalb des blockierten Winkelbereichs, sodass ausschliesslich die
    fachlich beabsichtigte Wald+Weg-Regel geprueft wird, nicht die neue
    BUG-101-Sichtpruefung."""
    c = _make_candidate(standpoint_lat=52.5000, standpoint_lon=13.4000,
                         subject_lat=52.5000, subject_lon=13.4100)
    forest_polygon = {"nodes": [
        (52.4990, 13.3990), (52.4990, 13.4010),
        (52.5010, 13.4010), (52.5010, 13.3990),
    ]}
    nearby_path = {"nodes": [(52.50005, 13.40005), (52.5002, 13.4002)]}
    data = _empty_data()
    data["forest_ways"] = [forest_polygon]
    data["path_ways"] = [nearby_path]
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: data)

    result = accessibility.filter_accessible_candidates([c])

    assert result == [c]


# ---------------------------------------------------------------------------
# AK4: im Wasser / auf-neben Bahngleisen -> ausgeblendet
# ---------------------------------------------------------------------------

def test_us135_im_wasser_wird_ausgeblendet(monkeypatch):
    """US-135 AK4: Ein Scout-Vorschlag im Wasser erscheint nicht in der
    Scout-Liste."""
    c = _make_candidate(standpoint_lat=52.5000, standpoint_lon=13.4000)
    water_polygon = {
        "nodes": [
            (52.4990, 13.3990), (52.4990, 13.4010),
            (52.5010, 13.4010), (52.5010, 13.3990),
        ],
        "closed": True,
    }
    data = _empty_data()
    data["water_ways"] = [water_polygon]
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: data)

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


def test_us135_neben_bahngleis_wird_ausgeblendet(monkeypatch):
    """US-135 AK4: Ein Scout-Vorschlag direkt neben Bahngleisen erscheint
    nicht in der Scout-Liste."""
    c = _make_candidate(standpoint_lat=52.5000, standpoint_lon=13.4000)
    rail_line = {"nodes": [(52.50002, 13.40002), (52.5010, 13.4010)]}
    data = _empty_data()
    data["rail_ways"] = [rail_line]
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: data)

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


# ---------------------------------------------------------------------------
# Edge Cases: Pruefung nicht durchfuehrbar -> im Zweifel ausblenden, kein
# Absturz (US-135 Regel 3 / Stephan-Entscheidung).
# ---------------------------------------------------------------------------

def test_us135_pruefung_nicht_durchfuehrbar_wird_ausgeblendet(monkeypatch):
    """US-135 Edge Case: Kann die kombinierte Live-Pruefung fuer einen
    Kandidaten nicht durchgefuehrt werden (None-Rueckgabe = Timeout/alle
    Mirrors fehlgeschlagen), wird der Kandidat ausgeblendet -- kein Label,
    keine Fehlermeldung, kein Absturz."""
    c = _make_candidate()
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: None)

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


def test_us135_exception_bei_pruefung_fuehrt_nicht_zum_absturz(monkeypatch):
    """US-135 Edge Case: Wirft die Live-Pruefung selbst eine Exception (z.B.
    unerwarteter Fehler), stuerzt filter_accessible_candidates nicht ab,
    sondern blendet den betroffenen Kandidaten aus."""
    def _boom(**kw):
        raise RuntimeError("simulierter Fehler")

    c = _make_candidate()
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data", _boom)

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


def test_us135_teilausfall_mehrerer_kandidaten_kein_absturz(monkeypatch):
    """US-135 Edge Case: Sind fuer mehrere Kandidaten unterschiedlicher
    Cluster Pruefungen nicht durchfuehrbar, bleibt insgesamt nur die
    tatsaechlich bestaetigte Teilmenge uebrig -- kein Absturz, kein
    Fehlerzustand (entspricht dem Verhalten 'Tag ohne gute Chancen')."""
    ok_candidate = _make_candidate(
        standpoint_lat=52.5000, standpoint_lon=13.4000, subject_id="motiv_a",
    )
    failing_candidate = _make_candidate(
        standpoint_lat=52.6000, standpoint_lon=13.6000, subject_id="motiv_b",
    )

    def _fake(observer_lat=None, observer_lon=None, subject_lat=None, subject_lon=None, **kw):
        if abs(observer_lat - 52.6000) < 1e-6:
            return None
        return _empty_data()

    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data", _fake)

    result = accessibility.filter_accessible_candidates([ok_candidate, failing_candidate])

    assert result == [ok_candidate]


# ---------------------------------------------------------------------------
# Cluster-Cache-Wiederverwendung (Implementierungsoption A): zwei nahe
# Kandidaten (gleiches Motiv) -> nur EIN Live-/Cache-Call.
# ---------------------------------------------------------------------------

def test_us135_zwei_nahe_kandidaten_nur_ein_live_call(monkeypatch):
    """US-135 Testplan: Zwei Scout-Kandidaten mit fast identischem
    Standpunkt (deutlich unter ACCESSIBILITY_CLUSTER_SIZE_M, gleiches
    Motiv) loesen nur EINE kombinierte Live-/Cache-Pruefung aus, nicht
    zwei -- Clusterung aus Implementierungsoption A."""
    call_count = {"n": 0}

    def _counting(**kw):
        call_count["n"] += 1
        return _empty_data()

    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data", _counting)

    c1 = _make_candidate(standpoint_lat=52.50000, standpoint_lon=13.40000, subject_id="motiv_x")
    c2 = _make_candidate(standpoint_lat=52.50015, standpoint_lon=13.40000, subject_id="motiv_x")  # ~17m entfernt

    result = accessibility.filter_accessible_candidates([c1, c2])

    assert call_count["n"] == 1
    assert result == [c1, c2]


def test_us135_weit_entfernte_kandidaten_zwei_live_calls(monkeypatch):
    """Gegenprobe zum Cluster-Test: liegen zwei Kandidaten deutlich weiter
    als ACCESSIBILITY_CLUSTER_SIZE_M auseinander, werden sie NICHT
    zusammengefasst -- je Cluster ein eigener Live-/Cache-Call."""
    call_count = {"n": 0}

    def _counting(**kw):
        call_count["n"] += 1
        return _empty_data()

    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data", _counting)

    c1 = _make_candidate(standpoint_lat=52.5000, standpoint_lon=13.4000, subject_id="motiv_y")
    c2 = _make_candidate(standpoint_lat=52.5100, standpoint_lon=13.4100, subject_id="motiv_y")

    accessibility.filter_accessible_candidates([c1, c2])

    assert call_count["n"] == 2


def test_us135_unterschiedliches_motiv_am_gleichen_standpunkt_zwei_calls(monkeypatch):
    """Zwei Kandidaten mit (fast) identischem Standpunkt, aber
    UNTERSCHIEDLICHEM Motiv, werden NICHT zusammengefasst -- die Sichtlinie
    haengt vom Motiv ab und darf nicht ueber Motive hinweg geteilt werden."""
    call_count = {"n": 0}

    def _counting(**kw):
        call_count["n"] += 1
        return _empty_data()

    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data", _counting)

    c1 = _make_candidate(standpoint_lat=52.5000, standpoint_lon=13.4000, subject_id="motiv_a")
    c2 = _make_candidate(standpoint_lat=52.5000, standpoint_lon=13.4000, subject_id="motiv_b")

    accessibility.filter_accessible_candidates([c1, c2])

    assert call_count["n"] == 2


# ---------------------------------------------------------------------------
# Geteilter Rate-Limit-Tracker: fetch_scout_accessibility_data() nutzt
# (ueber _fetch_from_mirrors) _respect_overpass_rate_limit() -- keinen
# zweiten, unabhaengigen Limiter.
# ---------------------------------------------------------------------------

def test_us135_nutzt_geteilten_rate_limit_tracker(monkeypatch):
    """US-135 Testplan: fetch_scout_accessibility_data() ruft ueber
    _fetch_from_mirrors() denselben geteilten Rate-Limit-Tracker
    _respect_overpass_rate_limit() auf wie die bestehenden QA-Abfragen
    (TASK-45/US-09) -- kein zweiter, unabhaengiger Limiter."""
    calls = {"n": 0}
    orig = qa_azimuth._respect_overpass_rate_limit

    def _spy():
        calls["n"] += 1
        orig()

    monkeypatch.setattr(qa_azimuth, "_respect_overpass_rate_limit", _spy)
    monkeypatch.setattr(httpx, "Client", _client_factory({"elements": []}))

    result = qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)

    assert result == _empty_data()
    assert calls["n"] >= 1


def test_us135_kombinierte_anfrage_ordnet_elemente_richtig_zu(monkeypatch):
    """fetch_scout_accessibility_data() ordnet die Elemente EINER
    kombinierten Overpass-Antwort korrekt nach Tag den fuenf Kategorien zu
    (Gebaeude/Wald/Wasser/Bahn/Weg) -- eine Anfrage, mehrere
    Ergebnis-Kategorien (Implementierungsoption A statt getrennter
    Einzelanfragen)."""
    elements = [
        {"tags": {"building": "yes"}, "geometry": [
            {"lat": 52.5001, "lon": 13.4001}, {"lat": 52.5001, "lon": 13.4003},
            {"lat": 52.5003, "lon": 13.4003},
        ]},
        {"tags": {"landuse": "forest"}, "geometry": [
            {"lat": 52.4990, "lon": 13.3990}, {"lat": 52.4990, "lon": 13.4010},
            {"lat": 52.5010, "lon": 13.4010},
        ]},
        {"tags": {"natural": "water"}, "geometry": [
            {"lat": 52.4980, "lon": 13.3980}, {"lat": 52.4980, "lon": 13.3990},
            {"lat": 52.4990, "lon": 13.3990},
        ]},
        {"tags": {"railway": "rail"}, "geometry": [
            {"lat": 52.5020, "lon": 13.4020}, {"lat": 52.5021, "lon": 13.4021},
        ]},
        {"tags": {"highway": "footway"}, "geometry": [
            {"lat": 52.5000, "lon": 13.4000}, {"lat": 52.5001, "lon": 13.4001},
        ]},
    ]
    monkeypatch.setattr(httpx, "Client", _client_factory({"elements": elements}))

    result = qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)

    assert len(result["buildings"]) == 1
    assert len(result["forest_ways"]) == 1
    assert len(result["water_ways"]) == 1
    assert len(result["rail_ways"]) == 1
    assert len(result["path_ways"]) == 1


def test_us135_overpass_query_schliesst_stillgelegte_gleise_aus(monkeypatch):
    """US-135-Annahme (von Stephan bestaetigt): Nur aktiv genutzte Gleise
    zaehlen als Ausschlussgrund. Die gebaute Overpass-Query filtert daher
    railway=rail/tram/... UND schliesst das disused=yes-Sekundaer-Tag
    explizit aus; stillgelegte Strecken mit dem OSM-Lifecycle-Praefix
    disused:railway=* tragen ohnehin keinen railway=*-Tag und matchen den
    Filter gar nicht erst (kein zusaetzlicher Negativfilter dafuer noetig)."""
    monkeypatch.setattr(httpx, "Client", _client_factory({"elements": []}))

    qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)

    query = _FakeClient.last_query
    assert '"railway"~"^(rail|tram|light_rail' in query
    assert '"disused"!~"yes"' in query


class _FirstMirrorTimesOutSecondSucceedsClient:
    """Fake httpx.Client, dessen post() je nach angefragter URL unterschiedlich
    reagiert: der ERSTE Mirror (OVERPASS_MIRRORS[0], overpass-api.de) scheitert
    mit einem echten httpx.ReadTimeout (Nachbau des Live-Log-Fehlerbilds vom
    2026-08-08: 'The read operation timed out'), der ZWEITE Mirror
    (OVERPASS_MIRRORS[1], kumi.systems) liefert erfolgreich Daten. Anders als
    test_us135_alle_mirrors_fehlgeschlagen_gibt_none (beide Mirrors scheitern)
    prueft dieser Test den eigentlichen Fallback-Erfolgsfall fuer die NEUE
    kombinierte US-135-Anfrage."""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, data=None, **kwargs):
        if url == qa_azimuth.OVERPASS_MIRRORS[0]:
            raise httpx.ReadTimeout("simulierter Timeout wie im US-135-Live-Log")
        return _FakeResponse({"elements": []})


def test_us135_erster_mirror_timeout_zweiter_mirror_liefert_daten(monkeypatch):
    """US-135 Live-Bug (2026-08-08, Root-Cause-Verifikation): fetch_scout_
    accessibility_data() nutzt (ueber die bereits bestehende _fetch_from_
    mirrors()) denselben Mirror-Fallback wie die etablierte Gebaeudeabfrage --
    scheitert der erste Mirror mit einem Timeout, liefert der zweite Mirror
    trotzdem ein echtes Ergebnis zurueck (kein None / 'nicht pruefbar'), OHNE
    dass dafuer neuer Fallback-Code noetig war."""
    monkeypatch.setattr(httpx, "Client", _FirstMirrorTimesOutSecondSucceedsClient)

    result = qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)

    assert result == _empty_data()


def test_us135_scout_filter_laeuft_in_threadpool_blockiert_event_loop_nicht(monkeypatch):
    """US-135 Live-Bug (2026-08-08): Im Live-Volllauf blockierte die
    synchrone, netzlastige filter_accessible_candidates()-Ausfuehrung
    (~52 Minuten) den gesamten asyncio-Event-Loop -- nachweislich im
    Server-Log auch /health betroffen sowie ein verpasster geplanter Job
    ('Run time of job ... was missed'). Regressionsschutz: discover.pipeline.
    run_pipeline() muss den Aufruf ueber asyncio.to_thread in einen
    Worker-Thread auslagern (exakt das bestehende Muster aus
    main.py::_run_qa_pass), NICHT direkt im Event-Loop-Thread ausfuehren."""
    from discover import pipeline as pipeline_module
    from discover import moon_pipeline, sun_pipeline

    async def _empty_run(days):
        return []

    monkeypatch.setattr(moon_pipeline, "run", _empty_run)
    monkeypatch.setattr(sun_pipeline, "run", _empty_run)

    calls = {"in_worker_thread": 0, "in_event_loop_thread": 0}

    def _spy_filter(candidates):
        if threading.current_thread() is threading.main_thread():
            calls["in_event_loop_thread"] += 1
        else:
            calls["in_worker_thread"] += 1
        return list(candidates)

    monkeypatch.setattr(pipeline_module, "filter_accessible_candidates", _spy_filter)

    asyncio.run(pipeline_module.run_pipeline(days=1))

    assert calls["in_worker_thread"] == 1
    assert calls["in_event_loop_thread"] == 0


def test_us135_alle_mirrors_fehlgeschlagen_gibt_none(monkeypatch):
    """fetch_scout_accessibility_data() gibt None zurueck, wenn ALLE
    Overpass-Mirrors fehlschlagen -- der Aufrufer (get_scout_accessibility_data
    bzw. discover/accessibility.py) behandelt das als 'nicht pruefbar', nie
    als 'frei'/'zugaenglich' (US-135 Regel 3)."""
    monkeypatch.setattr(httpx, "Client", _AlwaysFailClient)

    result = qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)

    assert result is None


# ---------------------------------------------------------------------------
# Cache: get_scout_accessibility_data() nutzt den lokalen Tage-Cache und
# vermeidet einen zweiten Live-Call fuer denselben (bzw. einen innerhalb der
# Cache-Toleranz liegenden) Standpunkt.
# ---------------------------------------------------------------------------

def test_us135_get_scout_accessibility_data_nutzt_cache_beim_zweiten_aufruf(monkeypatch, tmp_path):
    """Ein zweiter Aufruf von get_scout_accessibility_data() fuer denselben
    Standpunkt liest aus dem lokalen Cache statt erneut live zu fragen."""
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", tmp_path / "scout_access.json")

    live_calls = {"n": 0}

    def _counting_factory(*args, **kwargs):
        live_calls["n"] += 1
        return _FakeClient(payload={"elements": []})

    monkeypatch.setattr(httpx, "Client", _counting_factory)

    first = qa_azimuth.get_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)
    second = qa_azimuth.get_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)

    assert first == _empty_data()
    assert second == _empty_data()
    assert live_calls["n"] == 1


def test_us135_get_scout_accessibility_data_none_bei_fehlschlag_kein_cache_eintrag(monkeypatch, tmp_path):
    """Schlaegt die Live-Pruefung fehl (None), wird NICHTS gecacht -- ein
    spaeterer Aufruf mit funktionierendem Netzwerk darf nicht durch einen
    faelschlich dauerhaften 'nicht pruefbar'-Cache-Eintrag blockiert werden."""
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", tmp_path / "scout_access.json")
    monkeypatch.setattr(httpx, "Client", _AlwaysFailClient)

    result = qa_azimuth.get_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)
    assert result is None

    monkeypatch.setattr(httpx, "Client", _client_factory({"elements": []}))
    result2 = qa_azimuth.get_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)
    assert result2 == _empty_data()


# ---------------------------------------------------------------------------
# US-135 Nachbesserung (2026-08-08, Stephans Live-Befund im Scout-Detail-
# Sheet, zwei reale Faelle): "Einsteinturm" (Standpunkt mitten in einem als
# Multipolygon-RELATION gemappten Wald, relation 12981504) und "Schloss
# Pfaueninsel - Rundtuerme" (Standpunkt am/im Havel-Ufer, Knoten-Distanz 94m
# statt tatsaechlicher Kanten-Distanz <10m). Beide AK3/AK4-Verletzungen liefen
# trotz aller 20 zuvor gruenen Tests durch, weil kein bestehender Test einen
# als Relation gemappten Wald oder ein sparsam beknotetes, aber raeumlich
# grosses Way-Polygon simulierte -- echte Testabdeckungsluecke, kein reiner
# Zufallsfehlschlag.
# ---------------------------------------------------------------------------

def test_us135_wald_als_relation_gemappt_wird_erkannt(monkeypatch):
    """Root Cause 1 (Einsteinturm): Ein Waldgebiet, das in OSM als
    Multipolygon-RELATION (landuse=forest) statt als einzelner way gemappt
    ist, wurde von der vorherigen way-only-Abfrage komplett uebersehen --
    forest_ways blieb leer, der Standpunkt faelschlich 'zugaenglich'. Nach
    dem Fix zaehlt die Geometrie der Relations-Member-Ways als forest_ways."""
    elements = [
        {
            "type": "relation",
            "tags": {"landuse": "forest", "type": "multipolygon"},
            "members": [
                {
                    "type": "way", "role": "outer",
                    "geometry": [
                        {"lat": 52.4990, "lon": 13.3990}, {"lat": 52.4990, "lon": 13.4010},
                        {"lat": 52.5010, "lon": 13.4010}, {"lat": 52.5010, "lon": 13.3990},
                    ],
                },
            ],
        },
    ]
    monkeypatch.setattr(httpx, "Client", _client_factory({"elements": elements}))

    result = qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)

    assert len(result["forest_ways"]) == 1
    assert len(result["forest_ways"][0]["nodes"]) == 4


def test_us135_relation_ohne_forest_tag_wird_ignoriert(monkeypatch):
    """Gegenprobe: eine Relation, die NICHT landuse=forest/natural=wood
    traegt (z.B. eine andere Multipolygon-Art), darf nicht versehentlich als
    Wald gezaehlt werden."""
    elements = [
        {
            "type": "relation",
            "tags": {"type": "multipolygon", "landuse": "residential"},
            "members": [
                {"type": "way", "role": "outer", "geometry": [
                    {"lat": 52.4990, "lon": 13.3990}, {"lat": 52.4990, "lon": 13.4010},
                    {"lat": 52.5010, "lon": 13.4010},
                ]},
            ],
        },
    ]
    monkeypatch.setattr(httpx, "Client", _client_factory({"elements": elements}))

    result = qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)

    assert result["forest_ways"] == []


def test_us135_wald_relation_ohne_weg_wird_end_to_end_ausgeblendet(monkeypatch, tmp_path):
    """End-to-End (accessibility.py + qa_azimuth.py zusammen): Ein Standpunkt
    mitten in einem NUR als Relation gemappten Wald, ohne Weg in der Naehe,
    wird durch filter_accessible_candidates() ausgeblendet -- Regressionsschutz
    fuer den realen Einsteinturm-Fall."""
    c = _make_candidate(standpoint_lat=52.5000, standpoint_lon=13.4000)
    elements = [
        {
            "type": "relation",
            "tags": {"landuse": "forest", "type": "multipolygon"},
            "members": [
                {"type": "way", "role": "outer", "geometry": [
                    {"lat": 52.4990, "lon": 13.3990}, {"lat": 52.4990, "lon": 13.4010},
                    {"lat": 52.5010, "lon": 13.4010}, {"lat": 52.5010, "lon": 13.3990},
                ]},
            ],
        },
    ]
    monkeypatch.setattr(httpx, "Client", _client_factory({"elements": elements}))
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", tmp_path / "scout_access.json")

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


def test_us135_wasser_kante_zwischen_sparsen_knoten_wird_erkannt(monkeypatch):
    """Root Cause 2 (Schloss Pfaueninsel): Ein sparsam beknotetes, aber
    raeumlich grosses Wasser-Polygon hat einen Standpunkt, der nur ~8m
    senkrecht von einer KANTE entfernt liegt, aber die beiden begrenzenden
    KNOTEN sind je ~300m entfernt (>> 15m-Puffer). Die reine
    Knoten-Distanz-Pruefung (vor dem Fix) liess den Standpunkt faelschlich
    als 'zugaenglich' durch; die Kanten-Distanz-Pruefung (nach dem Fix)
    erkennt die echte Naehe zum Ufer. Koordinaten rechnerisch verifiziert
    (nicht geschaetzt): Knoten-Distanz ~299,8m je Endpunkt, Kanten-Distanz
    exakt 8,0m."""
    c = _make_candidate(standpoint_lat=52.42820, standpoint_lon=13.10934)
    water_polygon = {
        "nodes": [
            (52.42827186489399, 13.1049203020685),
            (52.42827186489399, 13.1137596979315),
        ],
        "closed": False,
    }
    data = _empty_data()
    data["water_ways"] = [water_polygon]
    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data",
                         lambda **kw: data)

    # Gegenprobe: die alte reine Knoten-Distanz waere hier deutlich groesser
    # als der 15m-Puffer gewesen -- erst die Kanten-Distanz erkennt die Naehe.
    node_distance = min(
        accessibility._haversine_m(52.42820, 13.10934, n_lat, n_lon)
        for n_lat, n_lon in water_polygon["nodes"]
    )
    assert node_distance > qa_azimuth.SCOUT_ACCESS_WATER_LINE_BUFFER_M

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


def test_us135_cluster_verdikt_gilt_nicht_pauschal_fuer_alle_mitglieder(monkeypatch):
    """US-135 Nachbesserung (2026-08-08, realer Fall Schloss Pfaueninsel,
    Cluster mit 7 Mitgliedern Tage 10.-16.8.): Ein Cluster buendelt NUR die
    Overpass-Anfrage (ACCESSIBILITY_CLUSTER_SIZE_M), nicht das Verdikt.
    Liegt der Repraesentant (erstes Mitglied) an Land, ein anderes Mitglied
    derselben 80m-Rasterzelle aber nachweislich im Wasser, darf NUR das
    tatsaechlich zugaengliche Mitglied in der Ergebnisliste bleiben --
    Regressionsschutz gegen das vorherige Verhalten (accepted.extend(members)
    fuer die GESAMTE Zelle anhand nur des Repraesentanten-Verdikts)."""
    call_count = {"n": 0}

    # c1 = Repraesentant (erstes Mitglied), liegt AUSSERHALB des Wasser-
    # Polygons UND ausserhalb des 15m-Wasserlinienpuffers
    # (qa_azimuth.SCOUT_ACCESS_WATER_LINE_BUFFER_M) -- lat=52.49985 liegt
    # rund 28m suedlich der Polygon-Suedkante (lat=52.50010), damit greift
    # weder die Flaechen- noch die Linienpuffer-Pruefung in _is_excluded().
    c1 = _make_candidate(standpoint_lat=52.49985, standpoint_lon=13.40000,
                          subject_id="motiv_cluster_mixed")
    # c2 = zweites Mitglied derselben 80m-Zelle (~33m entfernt), liegt
    # INNERHALB des Wasser-Polygons.
    c2 = _make_candidate(standpoint_lat=52.50015, standpoint_lon=13.40000,
                          subject_id="motiv_cluster_mixed")

    # Geschlossenes Wasser-Polygon, das NUR c2 umschliesst; c1 liegt bewusst
    # deutlich (>15m Pufferabstand) suedlich davon (Polygon beginnt erst bei
    # lat=52.50010).
    water_polygon = {
        "nodes": [
            (52.50010, 13.39995), (52.50010, 13.40005),
            (52.50020, 13.40005), (52.50020, 13.39995),
            (52.50010, 13.39995),
        ],
        "closed": True,
    }
    data = _empty_data()
    data["water_ways"] = [water_polygon]

    def _counting(**kw):
        call_count["n"] += 1
        return data

    monkeypatch.setattr(accessibility.qa_azimuth, "get_scout_accessibility_data", _counting)

    # Gegenprobe: c1 liegt wirklich ausserhalb des Polygons UND ausserhalb
    # des 15m-Linienpuffers, c2 wirklich innerhalb des Polygons (belegt die
    # Testkonstruktion, nicht nur behauptet).
    assert accessibility._point_in_polygon(52.49985, 13.40000, water_polygon["nodes"]) is False
    assert accessibility._min_distance_to_ways_m(52.49985, 13.40000, [water_polygon]) > qa_azimuth.SCOUT_ACCESS_WATER_LINE_BUFFER_M
    assert accessibility._point_in_polygon(52.50015, 13.40000, water_polygon["nodes"]) is True

    result = accessibility.filter_accessible_candidates([c1, c2])

    # Cluster-Buendelung bleibt erhalten: weiterhin nur EIN Live-/Cache-Call
    # fuer beide Mitglieder derselben Zelle.
    assert call_count["n"] == 1
    # Aber das Verdikt ist jetzt PRO MITGLIED korrekt: nur c1 (an Land)
    # bleibt in der Liste, c2 (im Wasser) wird ausgeblendet.
    assert result == [c1]


# ---------------------------------------------------------------------------
# US-135 Nachbesserung (2026-08-09, Beweisfall Standpunkt
# 52.429605/13.114616, Motiv "Schloss Pfaueninsel - Rundtuerme"): Grosse,
# mehrteilige Wasserflaechen wie die Havel sind in OSM als Multipolygon-
# RELATION mit vielen Member-Way-SEGMENTEN gemappt (Beleg: relation 173239
# "Havel", natural=water, Pfaueninsel als inner-Ring). Der gecachte
# Overpass-Rohdaten-Eintrag fuer den Beweisfall enthaelt ~280 water_ways-
# Segmente, ausnahmslos mit "closed": false -- KEIN einzelnes Segment ist
# fuer sich ein geschlossener Ring, nur ALLE zusammen ergeben den
# durchgehenden See-Umriss. Vor diesem Fix blieb "closed" fuer jedes Segment
# False, der Punkt-in-Polygon-Test in accessibility.py._is_excluded() konnte
# daher fuer solche Flaechen strukturell nie greifen. Die Tests unten
# bilden diese Topologie bewusst vereinfacht (zwei Quadrate statt 280
# Havel-Segmente) nach, decken aber denselben Fehlermechanismus ab: ein
# Aussenring aus mehreren OFFENEN Segmenten, PLUS ein separater Innenring
# (Insel, role="inner") -- die Pfaueninsel selbst darf nach der
# Ringzusammensetzung nicht faelschlich als Wasser gelten.
# ---------------------------------------------------------------------------

def _havel_relation_elements(rel_id=173239):
    """Vereinfachte Nachbildung der Havel-Relations-Topologie: ein
    Aussenring (Quadrat, lat 52.500-52.504 / lon 13.400-13.404) aus VIER
    einzelnen OFFENEN 2-Knoten-Segmenten (role='outer', wie die realen
    Havel-Member-Ways -- keines davon ist fuer sich geschlossen), plus ein
    kleineres Innenring-Quadrat (Insel, lat 52.501-52.502 / lon
    13.401-13.402, role='inner') ebenfalls aus vier offenen Segmenten."""
    return [
        {
            "type": "relation",
            "id": rel_id,
            "tags": {"natural": "water", "type": "multipolygon"},
            "members": [
                # Aussenring (Havel-Ufer) -- vier offene Segmente A-B-C-D-A
                {"type": "way", "role": "outer", "geometry": [
                    {"lat": 52.500, "lon": 13.400}, {"lat": 52.500, "lon": 13.404},
                ]},
                {"type": "way", "role": "outer", "geometry": [
                    {"lat": 52.500, "lon": 13.404}, {"lat": 52.504, "lon": 13.404},
                ]},
                {"type": "way", "role": "outer", "geometry": [
                    {"lat": 52.504, "lon": 13.404}, {"lat": 52.504, "lon": 13.400},
                ]},
                {"type": "way", "role": "outer", "geometry": [
                    {"lat": 52.504, "lon": 13.400}, {"lat": 52.500, "lon": 13.400},
                ]},
                # Innenring (Insel, z.B. Pfaueninsel) -- vier offene Segmente E-F-G-H-E
                {"type": "way", "role": "inner", "geometry": [
                    {"lat": 52.501, "lon": 13.401}, {"lat": 52.501, "lon": 13.402},
                ]},
                {"type": "way", "role": "inner", "geometry": [
                    {"lat": 52.501, "lon": 13.402}, {"lat": 52.502, "lon": 13.402},
                ]},
                {"type": "way", "role": "inner", "geometry": [
                    {"lat": 52.502, "lon": 13.402}, {"lat": 52.502, "lon": 13.401},
                ]},
                {"type": "way", "role": "inner", "geometry": [
                    {"lat": 52.502, "lon": 13.401}, {"lat": 52.501, "lon": 13.401},
                ]},
            ],
        },
    ]


def test_us135_wasser_relation_aus_offenen_segmenten_wird_zu_ring_zusammengesetzt(monkeypatch):
    """Root Cause 3 (Havel/Pfaueninsel): fetch_scout_accessibility_data()
    muss die vier offenen Aussenring-Segmente der Relation zu EINEM
    geschlossenen Ring zusammensetzen (nicht vier separate, allesamt
    'closed': false Eintraege wie vor dem Fix) -- und denselben Schritt
    unabhaengig fuer den Innenring (Insel)."""
    monkeypatch.setattr(httpx, "Client", _client_factory({"elements": _havel_relation_elements()}))

    result = qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)

    water_ways = result["water_ways"]
    # Zwei geschlossene Ringe: Aussenring (outer) + Innenring/Insel (inner) --
    # keine acht Einzelsegmente mehr, keines davon mehr mit "closed": false.
    assert len(water_ways) == 2
    assert all(w["closed"] is True for w in water_ways)
    assert all(w["relation_id"] == 173239 for w in water_ways)
    roles = sorted(w["role"] for w in water_ways)
    assert roles == ["inner", "outer"]
    for w in water_ways:
        nodes = w["nodes"]
        assert len(nodes) == 5  # 4 distinct Eckpunkte + Wiederholung des Startknotens
        assert nodes[0] == nodes[-1]


def test_us135_havel_beweisfall_mehrteilige_wasserflaeche_schliesst_standpunkt_aus(monkeypatch, tmp_path):
    """Der eigentliche Beweisfall (End-to-End, accessibility.py + qa_azimuth.py
    zusammen): ein Standpunkt tief im rekonstruierten Aussenring, weit von
    jeder einzelnen Uferkante entfernt (> SCOUT_ACCESS_WATER_LINE_BUFFER_M
    zu jedem Segment, sonst wuerde schon der bisherige Kantenpuffer greifen
    und der Test nichts ueber die Ringzusammensetzung beweisen), wird durch
    filter_accessible_candidates() ausgeblendet -- vor dem Fix blieb dieser
    Standpunkt faelschlich 'zugaenglich', weil kein Segment 'closed': true
    war und der Punkt-in-Polygon-Test nie griff."""
    # Standpunkt in der noerdlichen Haelfte des Sees, deutlich suedlich der
    # Insel und deutlich (>15m) von jeder der acht Kantenlinien entfernt --
    # nur ueber den zusammengesetzten Ring als 'im Wasser' erkennbar.
    c = _make_candidate(standpoint_lat=52.5005, standpoint_lon=13.4035)
    monkeypatch.setattr(httpx, "Client", _client_factory({"elements": _havel_relation_elements()}))
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", tmp_path / "scout_access.json")

    # Gegenprobe: der Standpunkt liegt wirklich weit von jeder Einzelkante
    # entfernt -- der alte 15m-Kantenpuffer allein haette hier NICHT gegriffen.
    data = qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)
    edge_distance = accessibility._min_distance_to_ways_m(
        52.5005, 13.4035, data["water_ways"],
    )
    assert edge_distance > qa_azimuth.SCOUT_ACCESS_WATER_LINE_BUFFER_M

    result = accessibility.filter_accessible_candidates([c])

    assert result == []


def test_us135_insel_im_wasserpolygon_bleibt_zugaenglich(monkeypatch, tmp_path):
    """Gegenprobe zum Havel-Beweisfall: ein Standpunkt AUF der Insel
    (innerhalb des inner-Rings, z.B. nahe dem Schloss auf der Pfaueninsel)
    darf NICHT faelschlich als Wasser ausgeschlossen werden, obwohl er auch
    innerhalb des Aussenrings liegt -- die Loch-Regel (gerade Anzahl
    umschliessender Ringe derselben Relation = kein Wasser) muss greifen,
    sonst wuerde die gesamte Insel faelschlich als Wasser markiert."""
    c = _make_candidate(standpoint_lat=52.5015, standpoint_lon=13.4015)
    monkeypatch.setattr(httpx, "Client", _client_factory({"elements": _havel_relation_elements()}))
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", tmp_path / "scout_access.json")

    # Gegenprobe: der Insel-Punkt liegt tatsaechlich sowohl im Aussenring
    # ALS AUCH im Innenring (das ist der Fall, der ohne Loch-Regel
    # faelschlich als Wasser gezaehlt wuerde).
    data = qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)
    outer = next(w for w in data["water_ways"] if w["role"] == "outer")
    inner = next(w for w in data["water_ways"] if w["role"] == "inner")
    assert accessibility._point_in_polygon(52.5015, 13.4015, outer["nodes"]) is True
    assert accessibility._point_in_polygon(52.5015, 13.4015, inner["nodes"]) is True

    result = accessibility.filter_accessible_candidates([c])

    assert result == [c]


# ---------------------------------------------------------------------------
# US-135 Randfall-Nachbesserung (2026-08-09, Zweitpruefung): Rekonstruktion
# des Aussenrings scheitert (unvollstaendige Overpass-Antwort -> offene
# Restsegmente), waehrend der Innenring (Insel) trotzdem erfolgreich
# geschlossen wird. Vor dieser Nachbesserung landete in diesem Fall NUR der
# Innenring in der Ring-Gruppe der Relation -- die Gerade-Ungerade-Regel
# zaehlte fuer einen Punkt AUF der Insel enclosing_count=1 (ungerade) und
# schloss ihn faelschlich als "im Wasser" aus, obwohl es Land ist.
# ---------------------------------------------------------------------------

def _havel_relation_elements_outer_unvollstaendig(rel_id=173239):
    """Wie _havel_relation_elements(), aber das letzte Aussenring-Segment
    (D-A, schliesst das Aussenring-Quadrat) fehlt -- simuliert eine
    unvollstaendige Overpass-Antwort (fehlendes Member-Way). Die restlichen
    drei Aussenring-Segmente lassen sich zu A-B-C-D verketten, aber NICHT
    schliessen (bleiben als offenes Restsegment/"closed": False). Der
    Innenring (Insel) ist vollstaendig und wird weiterhin erfolgreich zu
    einem geschlossenen Ring zusammengesetzt."""
    elements = _havel_relation_elements(rel_id=rel_id)
    members = elements[0]["members"]
    # Das vierte Mitglied (Index 3) ist das schliessende Aussenring-Segment
    # D-A -- entfernen, um die Rekonstruktion des Aussenrings scheitern zu
    # lassen, ohne den Innenring anzutasten.
    assert members[3]["role"] == "outer"
    del members[3]
    return elements


def test_us135_insel_ohne_rekonstruierbaren_aussenring_bleibt_zugaenglich(monkeypatch, tmp_path):
    """Randfall (Zweitpruefung, nicht der urspruengliche Havel-Bug): Scheitert
    die Rekonstruktion des Aussenrings einer Relation komplett (hier: ein
    Member-Way fehlt, drei offene Restsegmente bleiben 'closed': False),
    aber der Innenring (Insel) wird trotzdem erfolgreich geschlossen, darf
    ein Standpunkt AUF der Insel NICHT allein aufgrund des Innenrings als
    'im Wasser' ausgeschlossen werden -- die Gerade-Ungerade-Lochregel darf
    ohne geschlossenen Aussenring nicht greifen. Der Fall degradiert
    stattdessen defensiv auf den bestehenden 15m-Kantenpuffer."""
    c = _make_candidate(standpoint_lat=52.5015, standpoint_lon=13.4015)
    monkeypatch.setattr(
        httpx, "Client",
        _client_factory({"elements": _havel_relation_elements_outer_unvollstaendig()}),
    )
    monkeypatch.setattr(qa_azimuth, "SCOUT_ACCESS_CACHE_PATH", tmp_path / "scout_access.json")

    # Vorbedingung pruefen: kein geschlossener Outer-Ring mehr fuer die
    # Relation, aber der Inner-Ring (Insel) ist weiterhin geschlossen -- und
    # der Standpunkt liegt tatsaechlich innerhalb dieses Innenrings (das ist
    # exakt der Fall, der ohne die Randfall-Nachbesserung faelschlich als
    # Wasser gezaehlt wuerde).
    data = qa_azimuth.fetch_scout_accessibility_data(52.5000, 13.4000, 52.5010, 13.4010)
    outer_ways = [w for w in data["water_ways"] if w["role"] == "outer"]
    inner_ways = [w for w in data["water_ways"] if w["role"] == "inner"]
    assert all(w["closed"] is False for w in outer_ways)
    assert len(inner_ways) == 1
    assert inner_ways[0]["closed"] is True
    assert accessibility._point_in_polygon(52.5015, 13.4015, inner_ways[0]["nodes"]) is True

    result = accessibility.filter_accessible_candidates([c])

    assert result == [c]
