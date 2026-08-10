"""
BUG-104: Direktionale Wolkenwerte (golden_cloud_score_sun_dir/_antisolar_dir)
bleiben bei realistischer Location-Zahl dauerhaft null.

Root Cause (Analyse-Phase, code- UND live-verifiziert per AK1, 2026-08-09):
_plan_weather_fetch_tasks() dedupliziert die richtungsspezifischen
Wolkenwert-Fetches (sun_dir/antisolar_dir/aerosol, US-131) pro projiziertem
Punkt, gerundet auf 3 Nachkommastellen. Weil die projizierten Punkte
(destination_point() 30 km hinter dem Motiv) sich pro Event leicht
unterscheiden, dedupliziert diese Rundung kaum — bis zu 6x mehr Einzel-Tasks
pro Location als die regulären Wetter-Fetches (die 1x pro Location
deduplizieren, da sie direkt am unveränderten Fotografen-Standort hängen).
Bei ~315-319 Locations führt das zu 1176-1580 Einzel-Requests, die das harte
WEATHER_OVERLAY_MAX_TOTAL_SECONDS-Zeitbudget (180.0s, BUG-99) sprengen — der
Lauf bricht ab, bevor die direktionalen Werte je gesetzt werden. Live
bestätigt (AK1): alle 500 aktuellen Chancen hatten golden_cloud_score_sun_dir/
_antisolar_dir = null, auch dort wo das allgemeine Wetter schon vollständig
geladen war.

Umsetzung (Option A, risikoärmste der 3 analysierten Optionen): Rundung des
Projektions-Cache-Keys von 3 auf 2 Nachkommastellen vergröbert
(main.PROJECTED_POINT_CACHE_PRECISION), OHNE die bereits durch echte
Incidents kalibrierten Throttling-Konstanten (WEATHER_API_MAX_CONCURRENT_
REQUESTS, WEATHER_OVERLAY_MAX_TOTAL_SECONDS) anzufassen. Die neue Konstante
wird an BEIDEN betroffenen Stellen verwendet — _plan_weather_fetch_tasks()
(Task-Planung) UND _lookup_projected_forecasts() (Task-Lookup) — weil ein
Auseinanderlaufen der Rundung zwischen den beiden Stellen den Fetch "ins
Leere laufen" lässt (Plan erzeugt Key A, Lookup sucht Key B).

Abgedeckte Akzeptanzkriterien (siehe BACKLOG.md BUG-104):
  AK2 (Kernverhalten): Nach dem Fix bekommen Referenz-Chancen nicht-null
      direktionale Werte — UND die Zahl der geplanten Einzel-Tasks sinkt
      dabei tatsächlich deutlich (der eigentliche Fix-Mechanismus, nicht nur
      das Symptom).
  AK3 (Regressionsschutz): Bei dauerhaftem Fetch-Fehlschlag bleibt der Wert
      None — kein stiller Fallback auf golden_cloud_score (den separaten,
      am Fotografen-Standort verankerten Legacy-Wert, main.py Z. ~554).
  AK4 (Negativfall): Nicht-Golden-Hour-Events behalten weiterhin None,
      unverändert durch die Präzisionsänderung.
  AK7 (Konsistenz): Der 3h-Cron-Pfad (_weather_overlay()) und der Fast-Path
      (_weather_overlay_single()) verhalten sich konsistent — inkl. eines
      direkten Nachweises, dass Planung (_plan_weather_fetch_tasks()) und
      Lookup (_lookup_projected_forecasts()) exakt dieselbe Rundung
      verwenden (der konkrete BUG-104-Fehlermodus, falls beide je wieder
      auseinanderlaufen).
  AK8 (Rundungstoleranz): Der vergröberte Projektionspunkt bleibt innerhalb
      von <2km vom exakten Punkt entfernt.

AK5a (Performance, Gesamtlaufzeit <180s bei ~315-319 Locations) und AK5b
(Rate-Limit-Sicherheit, aggregierte 429-Rate nicht wesentlich über der
BUG-83-Referenz ~4,8%) werden hier bewusst NICHT als eigener synthetischer
Performance-Test nachgebaut — ein Unit-Test kann weder echte Netzwerklatenz
noch echtes Rate-Limit-Verhalten des externen Wetterdienstes realistisch
reproduzieren, ein erzwungener "Fake-Performance-Test" würde nur Schein-
sicherheit liefern. Stattdessen sind sie abgedeckt durch:
  - die bestehenden BUG-99-Regressionstests (test_bug-99.py), die
    WEATHER_OVERLAY_MAX_TOTAL_SECONDS bei realistischer Location-Zahl
    (319) exakt gegenrechnen und unverändert grün bleiben (diese Suite
    fasst die Konstante selbst nicht an),
  - die bestehenden BUG-83-Regressionstests (test_bug83.py), die die
    Drosselungs-/Retry-Parameter (WEATHER_API_MAX_CONCURRENT_REQUESTS,
    Backoff bei HTTP 429) unverändert gegenprüfen,
  - den bereits erbrachten Live-Nachweis aus AK1 (siehe BACKLOG.md
    BUG-104-Ticket) als Ist-Zustand-Beleg für den Fehlermechanismus, gegen
    den dieser Fix wirkt.
Dieser Testfile deckt AK2/AK3/AK4/AK7/AK8 ab; die drei genannten
Regressionsdateien (test_bug-99.py, test_bug83.py, test_us131.py) laufen
zusätzlich unverändert als Pflicht-Regression gegen die geänderte main.py.
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

import main
from discover.pipeline_base import haversine_m
from calculations.weather import (
    HourlyWeather, WeatherForecast, HourlyAerosol, AerosolForecast,
    calculate_golden_cloud_score,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ---------------------------------------------------------------------------
# Helfer (Muster analog test_us131.py/test_bug-99.py)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_state():
    main._feed_cache = []
    main._job_status["weather"] = {
        "status": "idle", "last_run": None, "last_error": None, "duration_s": None,
    }
    yield
    main._feed_cache = []
    main._job_status["weather"] = {
        "status": "idle", "last_run": None, "last_error": None, "duration_s": None,
    }


def _hourly(t: datetime, cl=10.0, cm=10.0, ch=10.0) -> HourlyWeather:
    return HourlyWeather(
        time=t, cloud_cover_pct=cl + cm + ch, cloud_cover_low_pct=cl,
        cloud_cover_mid_pct=cm, cloud_cover_high_pct=ch, visibility_m=20000.0,
        precipitation_mm=0.0, precipitation_prob_pct=0.0, wind_speed_kmh=5.0,
        wind_direction_deg=180.0, temperature_c=18.0, dew_point_c=8.0, weather_code=1,
    )


def _forecast(ref: datetime, cl=10.0, cm=10.0, ch=10.0) -> WeatherForecast:
    hours = [_hourly(ref + timedelta(hours=i), cl, cm, ch) for i in range(-2, 72)]
    return WeatherForecast(location_lat=0.0, location_lon=0.0,
                            fetched_at=datetime.now(timezone.utc), hourly=hours)


def _aerosol_hourly(t: datetime, aod=0.05) -> HourlyAerosol:
    return HourlyAerosol(time=t, aerosol_optical_depth=aod)


def _aerosol_forecast(ref: datetime, aod=0.05) -> AerosolForecast:
    hours = [_aerosol_hourly(ref + timedelta(hours=i), aod) for i in range(-2, 72)]
    return AerosolForecast(location_lat=0.0, location_lon=0.0,
                            fetched_at=datetime.now(timezone.utc), hourly=hours)


def _golden_event(loc_id, observer_lat=52.5, observer_lon=13.4,
                   subject_lat=52.40, subject_lon=13.10, subject_azimuth=98,
                   sunset_azimuth=278, event_type="Goldene Stunde Abend",
                   shoot_offset_h=12):
    """Minimales, qualifizierendes Goldene-Stunde-Event-Dict (analog
    test_us131.py::_golden_event) — subject_lat/lon + subject_azimuth +
    sunset_azimuth vorhanden, damit _cloud_mood_projection_points() eine
    Projektion berechnet."""
    shoot = datetime.now(timezone.utc) + timedelta(hours=shoot_offset_h)
    return {
        "id": f"test-{loc_id}",
        "location_id": loc_id, "location_name": loc_id,
        "event_type": event_type,
        "observer_lat": observer_lat, "observer_lon": observer_lon,
        "subject_lat": subject_lat, "subject_lon": subject_lon,
        "subject_azimuth": subject_azimuth,
        "sunset_azimuth": sunset_azimuth, "sunrise_azimuth": None,
        "shoot_time": shoot.isoformat(),
        "astronomy_score": 0.8, "overall_score": 0.8,
        "weather_score": 0.0, "weather_description": "",
    }


def _match(lat, lon, ref_lat, ref_lon, tol=0.001):
    return abs(lat - ref_lat) < tol and abs(lon - ref_lon) < tol


# ---------------------------------------------------------------------------
# Regressionsanker: die neue Konstante existiert und steht auf 2
# ---------------------------------------------------------------------------

def test_projected_point_cache_precision_ist_2():
    assert main.PROJECTED_POINT_CACHE_PRECISION == 2, (
        "BUG-104-Fix erwartet main.PROJECTED_POINT_CACHE_PRECISION == 2 "
        "(von 3 auf 2 Nachkommastellen vergröbert, Option A)."
    )


# ---------------------------------------------------------------------------
# AK7 (Kern-Fehlermodus): Planung (_plan_weather_fetch_tasks) und Lookup
# (_lookup_projected_forecasts) MÜSSEN exakt dieselbe Rundung verwenden —
# sonst greift der Fetch beim Lookup ins Leere (genau das war neben der
# reinen Task-Explosion die zweite betroffene Stelle laut Ticket).
# ---------------------------------------------------------------------------

def test_plan_und_lookup_verwenden_identische_rundung():
    events = [
        _golden_event("loc_a", subject_lat=52.401, subject_lon=13.101),
        _golden_event("loc_b", subject_lat=52.403, subject_lon=13.104),
        _golden_event("loc_c", subject_lat=52.406, subject_lon=13.108),
    ]

    tasks_meta = main._plan_weather_fetch_tasks(events)

    sun_dir_forecasts = {}
    antisolar_dir_forecasts = {}
    aerosol_forecasts = {}
    ref = datetime.now(timezone.utc)
    for kind, key, _lat, _lon, _name in tasks_meta:
        if kind == "sun_dir":
            sun_dir_forecasts[key] = _forecast(ref, cl=10, cm=20, ch=15)
        elif kind == "antisolar_dir":
            antisolar_dir_forecasts[key] = _forecast(ref, cl=15, cm=25, ch=10)
        elif kind == "aerosol":
            aerosol_forecasts[key] = _aerosol_forecast(ref, aod=0.1)

    for e in events:
        sun_fc, anti_fc, aero_fc = main._lookup_projected_forecasts(
            e, sun_dir_forecasts, antisolar_dir_forecasts, aerosol_forecasts
        )
        assert sun_fc is not None, (
            f"Lookup fand für {e['location_id']} keinen sun_dir-Forecast unter dem "
            f"von _plan_weather_fetch_tasks() erzeugten Key — Plan und Lookup laufen "
            f"auseinander (BUG-104-Kernfehlermodus, Konsistenz-Regel aus AK7)."
        )
        assert anti_fc is not None, (
            f"Lookup fand für {e['location_id']} keinen antisolar_dir-Forecast unter "
            f"dem von _plan_weather_fetch_tasks() erzeugten Key."
        )
        assert aero_fc is not None, (
            f"Lookup fand für {e['location_id']} keinen aerosol-Forecast unter dem "
            f"von _plan_weather_fetch_tasks() erzeugten Key."
        )


# ---------------------------------------------------------------------------
# AK2: dichte Cluster projizierter Punkte (wie sie bei ~315-319 realen
# Locations mit knapp benachbarten Sichtachsen entstehen) werden nach dem
# Fix zu deutlich weniger Einzel-Tasks dedupliziert — UND die betroffenen
# Referenz-Chancen bekommen am Ende nicht-null direktionale Werte.
# ---------------------------------------------------------------------------

def test_ak2_dichter_punkt_cluster_wird_stark_dedupliziert_und_liefert_werte(monkeypatch):
    # 7 Events mit fein gestaffeltem subject_lat (Delta 0.0004°) — bewusst so
    # gewählt, dass sich die daraus projizierten Sonnenrichtungs-/Gegenrichtungs-
    # punkte (BEIDE Richtungen, nicht nur eine) bei der ALTEN 3-Dezimalstellen-
    # Rundung noch in mehrere unterschiedliche Tasks aufsplitten würden, bei der
    # NEUEN 2-Dezimalstellen-Rundung aber jeweils in denselben Bucket fallen
    # (identische Sichtachse, nur der Fotografen-nahe subject_lat-Wert wird
    # minimal variiert). Konkrete Werte empirisch anhand der echten
    # destination_point()-Geometrie ermittelt (s. Testaufbau-Vorbedingung unten,
    # die das für BEIDE Richtungen unabhängig prüft statt es nur anzunehmen).
    n = 7
    events = [
        _golden_event(f"loc_cluster_{i}", subject_lat=52.44 + i * 0.0004, subject_lon=13.1000)
        for i in range(n)
    ]

    # Testaufbau-Vorbedingung selbst verifizieren (analog BUG-99-Testmuster
    # "Testaufbau ungültig"-Assertion), für BEIDE Richtungen unabhängig: die
    # ALTE 3-Dezimalstellen-Rundung hätte hier tatsächlich mehrere
    # unterschiedliche Keys erzeugt, die NEUE 2-Dezimalstellen-Rundung genau
    # einen — sowohl für sun_dir als auch für antisolar_dir.
    old_precision_sun_keys, new_precision_sun_keys = set(), set()
    old_precision_anti_keys, new_precision_anti_keys = set(), set()
    for e in events:
        (sun_lat, sun_lon), (anti_lat, anti_lon) = main._cloud_mood_projection_points(e)
        old_precision_sun_keys.add(f"{sun_lat:.3f},{sun_lon:.3f}")
        new_precision_sun_keys.add(f"{sun_lat:.2f},{sun_lon:.2f}")
        old_precision_anti_keys.add(f"{anti_lat:.3f},{anti_lon:.3f}")
        new_precision_anti_keys.add(f"{anti_lat:.2f},{anti_lon:.2f}")

    assert len(old_precision_sun_keys) > 1 and len(old_precision_anti_keys) > 1, (
        "Testaufbau ungültig: die gewählten subject_lat-Deltas erzeugen bei "
        "3-Dezimalstellen-Rundung für sun_dir/antisolar_dir keine unterschiedlichen "
        f"Keys (sun={len(old_precision_sun_keys)}, anti={len(old_precision_anti_keys)}) "
        "— Delta erhöhen."
    )
    assert len(new_precision_sun_keys) == 1 and len(new_precision_anti_keys) == 1, (
        "Testaufbau ungültig: die gewählten subject_lat-Deltas erzeugen bei "
        "2-Dezimalstellen-Rundung für sun_dir und/oder antisolar_dir mehr als einen "
        f"Key (sun={len(new_precision_sun_keys)}, anti={len(new_precision_anti_keys)}, "
        "Cluster zu breit gestreut oder straddled eine Bucket-Grenze) — Delta "
        "verkleinern oder Basiswert anpassen."
    )

    # Produktionscode: _plan_weather_fetch_tasks() muss denselben, stark
    # deduplizierten Task-Count liefern wie new_precision_keys oben.
    tasks_meta = main._plan_weather_fetch_tasks(events)
    sun_dir_tasks = [t for t in tasks_meta if t[0] == "sun_dir"]
    antisolar_dir_tasks = [t for t in tasks_meta if t[0] == "antisolar_dir"]

    assert len(sun_dir_tasks) == 1, (
        f"Erwartet: {n} eng benachbarte Events werden nach dem BUG-104-Fix zu genau "
        f"1 sun_dir-Task dedupliziert, tatsächlich: {len(sun_dir_tasks)} "
        f"({[t[1] for t in sun_dir_tasks]}). Das ist der eigentliche Fix-Mechanismus "
        f"— ohne ihn würde die Task-Zahl mit der Location-Zahl mitwachsen und bei "
        f"realistischer Skala (~319 Locations) das Zeitbudget sprengen (AK1/AK5a)."
    )
    assert len(antisolar_dir_tasks) == 1, (
        f"Erwartet: genau 1 antisolar_dir-Task für den Cluster, tatsächlich: "
        f"{len(antisolar_dir_tasks)}."
    )

    # End-to-End: main._weather_overlay() mit gezähltem Fetch-Mock — die
    # Referenz-Chancen müssen am Ende NICHT-NULL direktionale Werte tragen
    # (AK2 Kernbehauptung), UND der Fetch darf pro Richtung nur so oft
    # aufgerufen werden, wie es dedupliziert eindeutige Keys gibt (nicht 1x
    # pro Event).
    main._feed_cache = list(events)
    call_counts = {"weather": 0, "aerosol": 0}

    async def fake_weather(lat, lon, days=7):
        call_counts["weather"] += 1
        return _forecast(datetime.now(timezone.utc), cl=10, cm=50, ch=20)

    async def fake_aerosol(lat, lon, days=7):
        call_counts["aerosol"] += 1
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.1)

    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    asyncio.run(main._weather_overlay())

    for e in events:
        assert e["golden_cloud_score_sun_dir"] is not None, (
            f"{e['location_id']}: golden_cloud_score_sun_dir ist weiterhin null nach "
            f"dem BUG-104-Fix — genau das war das gemeldete Symptom (AK2)."
        )
        assert e["golden_cloud_score_antisolar_dir"] is not None, (
            f"{e['location_id']}: golden_cloud_score_antisolar_dir ist weiterhin null "
            f"nach dem BUG-104-Fix (AK2)."
        )

    # weather-Calls: 1x observer-Standort (identisch für alle Events, s.
    # _golden_event Default) + 1x je dedupliziertem sun_dir/antisolar_dir-Key.
    assert call_counts["weather"] <= 3, (
        f"Erwartet höchstens 3 weather-Fetch-Aufrufe (1x Fotografen-Standort + "
        f"1x sun_dir + 1x antisolar_dir, alle für den Cluster dedupliziert), "
        f"tatsächlich: {call_counts['weather']}. Ohne die BUG-104-Dedup-Korrektur "
        f"wäre hier ein Aufruf pro Event zu erwarten gewesen ({n}+ Aufrufe)."
    )


# ---------------------------------------------------------------------------
# AK3 (Regressionsschutz): dauerhafter Fetch-Fehlschlag am projizierten
# Sonnenrichtungspunkt -> golden_cloud_score_sun_dir bleibt None, KEIN
# stiller Fallback auf den separaten, am Fotografen-Standort verankerten
# Legacy-Wert golden_cloud_score.
# ---------------------------------------------------------------------------

def test_ak3_dauerhafter_fehlschlag_bleibt_none_kein_fallback_auf_golden_cloud_score(monkeypatch):
    ev = _golden_event("loc_ak3", subject_azimuth=265)  # GOLDEN_CLOUDS-Richtung
    main._feed_cache = [ev]

    (sun_lat, sun_lon), (_anti_lat, _anti_lon) = main._cloud_mood_projection_points(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, sun_lat, sun_lon):
            raise RuntimeError("BUG-104-Testsimulation: dauerhafter Fehlschlag am Sonnenrichtungspunkt")
        # Fotografen-Standort UND Gegenrichtung liefern bewusst einen klar von 0
        # verschiedenen, leicht erkennbaren Wert — falls golden_cloud_score_sun_dir
        # doch (fälschlich) auf einen dieser Werte zurückfiele, wäre das hier sichtbar.
        return _forecast(datetime.now(timezone.utc), cl=5, cm=5, ch=90)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.1)

    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    asyncio.run(main._weather_overlay())  # darf nicht crashen

    assert ev["golden_cloud_score_sun_dir"] is None, (
        "Erwartet: dauerhaft fehlgeschlagener Fetch am Sonnenrichtungspunkt lässt "
        "golden_cloud_score_sun_dir None (AK3) — kein Fallback."
    )
    assert ev["cl_sun_dir"] is None
    assert ev["cm_sun_dir"] is None
    # Der separate Fotografen-Standort-Legacy-Wert existiert weiterhin (unabhängiger
    # Fetch, main.py e["golden_cloud_score"]) — genau DAS ist der Wert, auf den ein
    # stiller Fallback fälschlich zurückfallen könnte. golden_cloud_score_sun_dir
    # darf ihn nicht übernehmen.
    assert ev.get("golden_cloud_score") is not None, (
        "Testaufbau ungültig: der Fotografen-Standort-Fetch (golden_cloud_score) "
        "sollte in diesem Test erfolgreich sein, damit ein möglicher stiller "
        "Fallback überhaupt erkennbar wäre."
    )
    assert ev["golden_cloud_score_sun_dir"] != ev["golden_cloud_score"], (
        "golden_cloud_score_sun_dir darf bei einem fehlgeschlagenen Fetch niemals "
        "den Fotografen-Standort-Legacy-Wert golden_cloud_score übernehmen "
        "(BUG-104 AK3, kein stiller Fallback)."
    )


# ---------------------------------------------------------------------------
# AK4 (Negativfall): Nicht-Golden-Hour-Events behalten weiterhin None,
# unverändert durch die Präzisionsänderung.
# ---------------------------------------------------------------------------

def test_ak4_nicht_golden_hour_event_bleibt_none(monkeypatch):
    ev = {
        "id": "test-loc_ak4", "location_id": "loc_ak4", "location_name": "loc_ak4",
        "event_type": "Sonnenaufgang",  # kein Goldene-Stunde-Typ
        "observer_lat": 52.5, "observer_lon": 13.4,
        "shoot_time": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat(),
        "astronomy_score": 0.8, "overall_score": 0.8,
        "weather_score": 0.0, "weather_description": "",
    }
    main._feed_cache = [ev]

    calls = {"weather": 0, "aerosol": 0}

    async def fake_weather(lat, lon, days=7):
        calls["weather"] += 1
        return _forecast(datetime.now(timezone.utc), cl=10, cm=50, ch=20)

    async def fake_aerosol(lat, lon, days=7):
        calls["aerosol"] += 1
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.5)

    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    asyncio.run(main._weather_overlay())

    assert ev.get("golden_cloud_score_sun_dir") is None, (
        "Ein Nicht-Golden-Hour-Event darf auch nach dem BUG-104-Fix keinen "
        "golden_cloud_score_sun_dir-Wert bekommen (AK4)."
    )
    assert ev.get("golden_cloud_score_antisolar_dir") is None, (
        "Ein Nicht-Golden-Hour-Event darf auch nach dem BUG-104-Fix keinen "
        "golden_cloud_score_antisolar_dir-Wert bekommen (AK4)."
    )
    assert calls["aerosol"] == 0, (
        "Für ein Nicht-Golden-Hour-Event darf gar kein Aerosol-/Projektions-Fetch "
        "ausgelöst werden (keine Projektion berechnet)."
    )


# ---------------------------------------------------------------------------
# AK7: Fast-Path (_weather_overlay_single) und Cronlauf (_weather_overlay)
# liefern nach der Präzisionsänderung weiterhin identische Ergebnisse.
# ---------------------------------------------------------------------------

def test_ak7_fastpath_und_cronlauf_liefern_identische_werte_nach_praezisionsaenderung(monkeypatch):
    ev = _golden_event("loc_ak7", subject_azimuth=0)  # weder Sonnen- noch Gegenrichtung -> Original-Event bleibt erhalten
    main._feed_cache = [ev]

    (sun_lat, sun_lon), (anti_lat, anti_lon) = main._cloud_mood_projection_points(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, sun_lat, sun_lon):
            return _forecast(datetime.now(timezone.utc), cl=10, cm=50, ch=20)
        if _match(lat, lon, anti_lat, anti_lon):
            return _forecast(datetime.now(timezone.utc), cl=25, cm=45, ch=35)
        return _forecast(datetime.now(timezone.utc), cl=60, cm=60, ch=60)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.4)

    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    asyncio.run(main._weather_overlay())
    cron_result = {
        "gcs_sun": ev["golden_cloud_score_sun_dir"],
        "gcs_anti": ev["golden_cloud_score_antisolar_dir"],
        "cl_sun": ev["cl_sun_dir"], "cm_sun": ev["cm_sun_dir"],
        "cl_anti": ev["cl_antisolar_dir"], "cm_anti": ev["cm_antisolar_dir"],
    }
    assert cron_result["gcs_sun"] is not None
    assert cron_result["gcs_anti"] is not None

    for k in ("golden_cloud_score_sun_dir", "cl_sun_dir", "cm_sun_dir",
              "golden_cloud_score_antisolar_dir", "cl_antisolar_dir", "cm_antisolar_dir"):
        ev[k] = None

    ready = asyncio.run(main._weather_overlay_single("loc_ak7"))
    assert ready is True

    assert ev["golden_cloud_score_sun_dir"] == cron_result["gcs_sun"], (
        "Fast-Path liefert nach der BUG-104-Präzisionsänderung einen anderen "
        "golden_cloud_score_sun_dir-Wert als der Cronlauf (AK7-Verletzung)."
    )
    assert ev["golden_cloud_score_antisolar_dir"] == cron_result["gcs_anti"]
    assert ev["cl_sun_dir"] == cron_result["cl_sun"]
    assert ev["cm_sun_dir"] == cron_result["cm_sun"]
    assert ev["cl_antisolar_dir"] == cron_result["cl_anti"]
    assert ev["cm_antisolar_dir"] == cron_result["cm_anti"]


# ---------------------------------------------------------------------------
# AK8: der vergröberte (auf main.PROJECTED_POINT_CACHE_PRECISION gerundete)
# Projektionspunkt bleibt innerhalb von <2km vom exakten Punkt.
# ---------------------------------------------------------------------------

def test_ak8_rundungsfehler_bei_2_dezimalstellen_bleibt_unter_2km():
    # Worst-Case-Punkte je Breitengrad: der Rundungsfehler pro Achse ist
    # maximal ±0.5 * 10^-PRECISION Grad (Rundung auf den nächsten Bucket-
    # Mittelpunkt). Für PRECISION=2 also maximal ±0.005° je Achse — hier
    # bewusst als Worst-Case in beiden Achsen gleichzeitig konstruiert
    # (nicht nur zufällig gewählte Punkte).
    precision = main.PROJECTED_POINT_CACHE_PRECISION
    half_step = 0.5 * (10 ** -precision)

    # Repräsentative Breitengrade: Äquator (größter Meter-pro-Grad-Wert bei
    # Longitude), Berlin/FotoAlert-Kernregion (~52.5°), hoher Norden (~65°).
    test_latitudes = [0.0, 52.5163, 65.0]

    for lat in test_latitudes:
        lon = 13.3777
        # Punkt knapp INNERHALB eines Rundungs-Buckets, dessen gerundeter
        # Wert um den maximal möglichen Betrag abweicht.
        exact_lat = lat + half_step - 1e-9
        exact_lon = lon + half_step - 1e-9
        rounded_key = f"{exact_lat:.{precision}f},{exact_lon:.{precision}f}"
        rounded_lat, rounded_lon = (float(v) for v in rounded_key.split(","))

        dist_m = haversine_m(exact_lat, exact_lon, rounded_lat, rounded_lon)

        assert dist_m < 2000.0, (
            f"Rundungsfehler bei Breitengrad {lat}°: {dist_m:.1f}m zwischen exaktem "
            f"Punkt ({exact_lat:.6f},{exact_lon:.6f}) und gerundetem Punkt "
            f"({rounded_lat},{rounded_lon}) — erwartet <2000m (AK8)."
        )
