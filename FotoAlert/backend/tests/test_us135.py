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
    faelschlicher Ausschluss guter, aber technisch bewaldeter Spots)."""
    c = _make_candidate(standpoint_lat=52.5000, standpoint_lon=13.4000)
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
