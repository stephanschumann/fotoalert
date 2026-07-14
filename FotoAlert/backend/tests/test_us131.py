"""
US-131: Wolken-/Dunstabfrage für Himmelsröte (RED_SKY) & Goldene Wolken
(GOLDEN_CLOUDS) — Projektion entlang der Sichtachse statt Fotografen-Standort.

Weg-Gate-Entscheidung (Stephan, 2026-07-13): Option B — vollständig. Sowohl
GOLDEN_CLOUDS als auch RED_SKY fragen künftig Wetter-/Dunstdaten an einem
projizierten Punkt entlang der Sichtachse ab (30 km hinter dem Motiv,
CLOUD_MOOD_PROJECTION_DISTANCE_M), nicht mehr am Fotografen-Standort. Das
entkoppelt die bisher geteilte golden_cloud_score-Berechnung: eine Wolkenprojektion
in Sonnenrichtung (füttert GOLDEN_CLOUDS), eine getrennte in Gegenrichtung/
Antisolarpunkt (füttert RED_SKY). Fehlerverhalten: kein Fallback auf den
Fotografen-Standort-Wert bei fehlgeschlagenem Abruf am projizierten Punkt
("Signal nicht verfügbar", analog zum bestehenden failed_aerosol_locations-Muster).

Abgedeckte Akzeptanzkriterien (siehe BACKLOG.md US-131):
  AK-1:  Dunstwert für RED_SKY stammt vom Gegenrichtungs-/Antisolar-Punkt, nicht
         vom Fotografen-Standort.
  AK-2 (Regression): weather_score/weather_details (außer den Cloud-Mood-Feldern)
         bleiben am Fotografen-Standort verankert.
  AK-3/AK-8: GOLDEN_CLOUDS nutzt den in Sonnenrichtung projizierten Wolkenwert.
  AK-4/AK-10: Fast-Path (_weather_overlay_single) und Cronlauf (_weather_overlay)
         berechnen identische projizierte Punkte/Ergebnisse.
  AK-5:  Fehlgeschlagener Dunst-Abruf am projizierten Punkt → Rückfall auf reinen
         Wolken-Check, Location in failed_aerosol_locations/Job-Status.
  AK-6:  Fehlender subject_azimuth/sunrise_azimuth/sunset_azimuth → keine
         Projektion, kein Fehler.
  AK-7:  Dunstwert exakt auf RED_SKY_AOD_THRESHOLD am projizierten Punkt → Karte
         erscheint (inklusiver Grenzwert).
  AK-9:  RED_SKY-Wolkenbedingung nutzt den Gegenrichtungswert, nicht den
         Sonnenrichtungs- oder Standortwert (Entkopplungs-Nachweis).
  AK-11: Fehlgeschlagener Abruf an einem der beiden projizierten Wolkenpunkte →
         betroffener Wert bleibt None, kein Fallback, kein Absturz.
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

import main
from discover.geometry import destination_point
from calculations.weather import (
    HourlyWeather, WeatherForecast, HourlyAerosol, AerosolForecast,
    RED_SKY_AOD_THRESHOLD, CLOUD_MOOD_PROJECTION_DISTANCE_M,
    calculate_golden_cloud_score,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ---------------------------------------------------------------------------
# Helfer (Muster analog test_us106.py/test_bug77_weather_job_status.py)
# ---------------------------------------------------------------------------

def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


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


def _golden_event(loc_id="loc1", shoot_offset_h=12, observer_lat=52.5, observer_lon=13.4,
                   subject_lat=52.40, subject_lon=13.10, subject_azimuth=98,
                   sunset_azimuth=278, event_type="Goldene Stunde Abend"):
    """Minimales, qualifizierendes Goldene-Stunde-Event-Dict (subject_lat/lon +
    subject_azimuth + sunset_azimuth vorhanden -> _cloud_mood_projection_points()
    berechnet eine Projektion, AK-6-Gegenprobe)."""
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
# Geometrie: destination_point()/_cloud_mood_projection_points() — reine
# Geometrie, kein Netzwerk (Grundlage für AK-1/AK-7/AK-8/AK-9)
# ---------------------------------------------------------------------------

def test_destination_point_bekannter_fall():
    """Regressions-Anker: destination_point() liefert für einen festen Testfall
    (Fernsehturm-Beispiel aus discover/geometry.py) weiterhin denselben Wert —
    reine Geometrie, keine Änderung an der Funktion selbst durch dieses Ticket.
    Wert per direktem Aufruf verifiziert (nicht aus dem Docstring übernommen, da
    dessen Beispielwert einer abweichenden Rundung/Version entspricht)."""
    lat, lon = destination_point(52.5208, 13.4094, 298.4, 5640)
    assert round(lat, 3) == 52.545
    assert round(lon, 3) == 13.336


def test_projection_distance_ist_30km():
    assert CLOUD_MOOD_PROJECTION_DISTANCE_M == 30_000


def test_cloud_mood_projection_points_matches_destination_point():
    """_cloud_mood_projection_points() muss exakt destination_point() mit
    subject_lat/subject_lon als Ursprung, Sonnen-/Gegenrichtungs-Bearing und
    CLOUD_MOOD_PROJECTION_DISTANCE_M (30 km) nutzen (AK-1/AK-8-Grundlage)."""
    e = _golden_event(subject_lat=52.40, subject_lon=13.10, sunset_azimuth=278, subject_azimuth=98)
    result = main._cloud_mood_projection_points(e)
    assert result is not None
    sun_dir, antisolar_dir = result
    expected_sun = destination_point(52.40, 13.10, 278, CLOUD_MOOD_PROJECTION_DISTANCE_M)
    expected_anti = destination_point(52.40, 13.10, 98, CLOUD_MOOD_PROJECTION_DISTANCE_M)
    assert sun_dir == expected_sun
    assert antisolar_dir == expected_anti


def test_cloud_mood_projection_points_morgen_nutzt_sunrise_azimuth():
    e = _golden_event(event_type="Goldene Stunde Morgen", subject_azimuth=278)
    e["sunrise_azimuth"] = 98
    e["sunset_azimuth"] = None
    result = main._cloud_mood_projection_points(e)
    assert result is not None
    sun_dir, _antisolar_dir = result
    expected_sun = destination_point(e["subject_lat"], e["subject_lon"], 98, CLOUD_MOOD_PROJECTION_DISTANCE_M)
    assert sun_dir == expected_sun


# AK-6: fehlende Eingabewerte -> keine Projektion, kein Fehler
def test_cloud_mood_projection_points_none_ohne_subject_azimuth():
    e = _golden_event(subject_azimuth=None)
    assert main._cloud_mood_projection_points(e) is None


def test_cloud_mood_projection_points_none_ohne_sun_azimuth():
    e = _golden_event(sunset_azimuth=None)
    assert main._cloud_mood_projection_points(e) is None


def test_cloud_mood_projection_points_none_ohne_subject_lat_lon():
    e = _golden_event(subject_lat=None, subject_lon=None)
    assert main._cloud_mood_projection_points(e) is None


def test_cloud_mood_projection_points_none_fuer_nicht_goldene_stunde():
    e = _golden_event(event_type="Blaue Stunde")
    assert main._cloud_mood_projection_points(e) is None


def test_ak6_fehlender_subject_azimuth_keine_projektion_kein_fehler(monkeypatch):
    """AK-6: Fehlt subject_azimuth, entsteht wie bisher kein RED_SKY-Event — die
    Projektion wird gar nicht erst berechnet, kein Fehler durch fehlende
    Eingabewerte (auch kein unnötiger Aerosol-/Wolken-Fetch)."""
    ev = _golden_event(loc_id="loc_ak6", subject_azimuth=None)
    main._feed_cache = [ev]

    async def fake_weather(lat, lon, days=7):
        return _forecast(datetime.now(timezone.utc), cl=40, cm=35, ch=10)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    calls = {"aerosol": 0}

    async def fake_aerosol(lat, lon, days=7):
        calls["aerosol"] += 1
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.5)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    assert calls["aerosol"] == 0, "Ohne subject_azimuth darf gar kein Aerosol-Call erfolgen"
    assert ev["golden_cloud_score_sun_dir"] is None
    assert ev["golden_cloud_score_antisolar_dir"] is None
    assert main._job_status["weather"]["status"] == "done"


# ---------------------------------------------------------------------------
# AK-1/AK-2: Dunstwert stammt vom projizierten Punkt, allgemeine Wetteranzeige
# bleibt am Fotografen-Standort verankert
# ---------------------------------------------------------------------------

def test_ak1_aerosol_wert_stammt_von_projiziertem_punkt(monkeypatch):
    """AK-1: Fotografen-Standort und projizierter Gegenrichtungspunkt liefern
    unterschiedliche Aerosolwerte (X vs. Y) -> im Event landet Y (projiziert)."""
    ev = _golden_event(loc_id="loc_ak1")
    main._feed_cache = [ev]

    (_sun_lat, _sun_lon), (anti_lat, anti_lon) = main._cloud_mood_projection_points(ev)

    async def fake_weather(lat, lon, days=7):
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        if _match(lat, lon, anti_lat, anti_lon):
            return _aerosol_forecast(datetime.now(timezone.utc), aod=0.45)  # Y: projiziert
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.05)  # X: Fotografen-Standort
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    assert ev["weather_details"]["aerosol_optical_depth"] == 0.45


def test_ak2_allgemeine_wetteranzeige_bleibt_am_fotografen_standort(monkeypatch):
    """AK-2 (Regression): weather_details (Wolkenwerte etc.) bleiben am
    Fotografen-Standort verankert, auch wenn Sonnen-/Gegenrichtungspunkt klar
    unterschiedliche Werte liefern (kein stiller Seiteneffekt, Pre-Mortem Szenario 1)."""
    ev = _golden_event(loc_id="loc_ak2")
    main._feed_cache = [ev]

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, ev["observer_lat"], ev["observer_lon"]):
            return _forecast(datetime.now(timezone.utc), cl=5, cm=5, ch=5)
        return _forecast(datetime.now(timezone.utc), cl=80, cm=80, ch=80)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.05)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    wd = ev["weather_details"]
    assert wd["cloud_cover_low_pct"] == 5
    assert wd["cloud_cover_mid_pct"] == 5
    assert wd["cloud_cover_high_pct"] == 5


# ---------------------------------------------------------------------------
# AK-3/AK-8/AK-9: entkoppelte Wolkenwerte für GOLDEN_CLOUDS (Sonnenrichtung)
# und RED_SKY (Gegenrichtung) — kein Vertauschen (Pre-Mortem Szenario 2)
# ---------------------------------------------------------------------------

def test_ak8_golden_clouds_nutzt_sonnenrichtungswert(monkeypatch):
    """AK-3/AK-8: GOLDEN_CLOUDS-Score stammt vom Sonnenrichtungspunkt, nicht vom
    Fotografen-Standort oder der Gegenrichtung."""
    ev = _golden_event(loc_id="loc_ak8", subject_azimuth=265)  # GOLDEN_CLOUDS-Richtung (Diff 13° zu 278°)
    main._feed_cache = [ev]

    (sun_lat, sun_lon), (anti_lat, anti_lon) = main._cloud_mood_projection_points(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, sun_lat, sun_lon):
            return _forecast(datetime.now(timezone.utc), cl=10, cm=50, ch=20)  # hoher GCS
        if _match(lat, lon, anti_lat, anti_lon):
            return _forecast(datetime.now(timezone.utc), cl=95, cm=95, ch=95)  # niedriger GCS (cl>80)
        return _forecast(datetime.now(timezone.utc), cl=50, cm=50, ch=50)  # Fotografen-Standort
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.05)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    expected_sun = calculate_golden_cloud_score(10, 50, 20)
    assert ev["golden_cloud_score_sun_dir"] == round(expected_sun, 3)
    assert ev["golden_cloud_score_sun_dir"] >= 0.70
    assert ev["golden_cloud_score_sun_dir"] != ev["golden_cloud_score_antisolar_dir"]

    neue, entfernte = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Goldene Wolken" in typen, f"GOLDEN_CLOUDS fehlt. Erzeugte Typen: {typen}"
    assert ev["id"] in entfernte


def test_ak9_red_sky_nutzt_gegenrichtungswert_kein_vertauschen(monkeypatch):
    """AK-9: RED_SKY-Wolkenbedingung stammt vom Gegenrichtungspunkt (Antisolarpunkt),
    getrennt von der GOLDEN_CLOUDS-Sonnenrichtungsprojektion. Sonnenrichtungs- und
    Gegenrichtungswert unterscheiden sich deutlich im Testfall, ohne dass sich die
    beiden Event-Ergebnisse vertauschen (Entkopplungs-Nachweis, Pre-Mortem Szenario 2)."""
    ev = _golden_event(loc_id="loc_ak9", subject_azimuth=98)  # RED_SKY-Richtung (Antisolarpunkt von 278°)
    main._feed_cache = [ev]

    (sun_lat, sun_lon), (anti_lat, anti_lon) = main._cloud_mood_projection_points(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, sun_lat, sun_lon):
            return _forecast(datetime.now(timezone.utc), cl=95, cm=95, ch=95)  # niedriger GCS (irrelevant fuer RED_SKY)
        if _match(lat, lon, anti_lat, anti_lon):
            return _forecast(datetime.now(timezone.utc), cl=25, cm=45, ch=35)  # hoher GCS + cl+cm>=60
        return _forecast(datetime.now(timezone.utc), cl=50, cm=50, ch=50)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.05)  # unter Schwelle, nur Wolkenzweig relevant
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    expected_anti = calculate_golden_cloud_score(25, 45, 35)
    assert ev["golden_cloud_score_antisolar_dir"] == round(expected_anti, 3)
    assert ev["golden_cloud_score_antisolar_dir"] >= 0.80
    assert ev["cl_antisolar_dir"] + ev["cm_antisolar_dir"] >= 60
    # Kein Vertauschen: Sonnenrichtungswert bleibt klar unterschiedlich (niedrig).
    assert ev["golden_cloud_score_sun_dir"] != ev["golden_cloud_score_antisolar_dir"]

    neue, _entfernte = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" in typen, f"Himmelsröte fehlt. Erzeugte Typen: {typen}"
    assert "Goldene Wolken" not in typen, "GOLDEN_CLOUDS haette bei dieser Sichtachse nicht erscheinen duerfen"


# ---------------------------------------------------------------------------
# AK-7: Dunstwert exakt auf dem Schwellenwert am projizierten Punkt
# ---------------------------------------------------------------------------

def test_ak7_dunst_genau_auf_schwellenwert_am_projizierten_punkt(monkeypatch):
    """AK-7: Aerosolwert exakt RED_SKY_AOD_THRESHOLD am Gegenrichtungspunkt, KEINE
    ausreichende Wolkenbedingung (cl+cm<60) -> Karte erscheint trotzdem (inklusiver
    Grenzwert, reiner Dunst-Zweig)."""
    ev = _golden_event(loc_id="loc_ak7", subject_azimuth=98)
    main._feed_cache = [ev]

    (_sun_lat, _sun_lon), (anti_lat, anti_lon) = main._cloud_mood_projection_points(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, anti_lat, anti_lon):
            # gcs >= 0.80 (Sweet Spot), aber cl+cm=50 < 60 -> nur Dunst-Zweig kann ausloesen.
            return _forecast(datetime.now(timezone.utc), cl=5, cm=45, ch=35)
        return _forecast(datetime.now(timezone.utc), cl=5, cm=5, ch=5)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=RED_SKY_AOD_THRESHOLD)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    assert ev["golden_cloud_score_antisolar_dir"] >= 0.80
    assert ev["cl_antisolar_dir"] + ev["cm_antisolar_dir"] < 60
    assert ev["weather_details"]["aerosol_optical_depth"] == RED_SKY_AOD_THRESHOLD

    neue, _ = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" in typen, f"Himmelsröte haette trotz Grenzwert erscheinen muessen: {typen}"


# ---------------------------------------------------------------------------
# AK-5: Fehlgeschlagener Dunst-Abruf am projizierten Punkt -> Rückfall auf
# reinen Wolken-Check, sichtbar im Job-Status (failed_aerosol_locations)
# ---------------------------------------------------------------------------

def test_ak5_fehlgeschlagener_dunst_faellt_auf_wolken_zurueck(monkeypatch):
    ev = _golden_event(loc_id="loc_ak5", subject_azimuth=98)
    main._feed_cache = [ev]

    async def fake_weather(lat, lon, days=7):
        # cl=25,cm=45,ch=35 an ALLEN Punkten: gcs >= 0.80 (Sweet Spot) UND cl+cm=70>=60
        # (Wolkenbedingung), damit RED_SKY unabhängig vom (hier fehlschlagenden) Dunst
        # weiterhin über den reinen Wolken-Zweig ausgeloest wird.
        return _forecast(datetime.now(timezone.utc), cl=25, cm=45, ch=35)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def failing_aerosol(lat, lon, days=7):
        raise RuntimeError("Air-Quality-API down")
    monkeypatch.setattr(main, "fetch_aerosol_forecast", failing_aerosol)

    _run(main._weather_overlay())

    assert ev["weather_details"]["aerosol_optical_depth"] is None
    assert ev["golden_cloud_score_antisolar_dir"] >= 0.80
    assert ev["cl_antisolar_dir"] + ev["cm_antisolar_dir"] >= 60
    status = main._job_status["weather"]
    assert status["status"] == "error"
    assert ev["location_name"] in status["last_error"]
    assert "Aerosoldaten fehlgeschlagen für" in status["last_error"]

    neue, _ = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" in typen, "Wolkenbedingung allein haette weiterhin ausloesen muessen"


# ---------------------------------------------------------------------------
# AK-11: Fehlgeschlagener Abruf an einem der beiden projizierten Wolkenpunkte
# -> betroffener Wert bleibt None, kein Fallback, kein Absturz
# ---------------------------------------------------------------------------

def test_ak11_fehlgeschlagener_wolken_abruf_sonnenrichtung(monkeypatch):
    ev = _golden_event(loc_id="loc_ak11a", subject_azimuth=265)  # GOLDEN_CLOUDS-Richtung
    main._feed_cache = [ev]

    (sun_lat, sun_lon), (_anti_lat, _anti_lon) = main._cloud_mood_projection_points(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, sun_lat, sun_lon):
            raise RuntimeError("Open-Meteo down (Sonnenrichtung)")
        return _forecast(datetime.now(timezone.utc), cl=25, cm=45, ch=35)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.05)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())  # darf nicht crashen

    # Sonnenrichtung fehlgeschlagen -> None, kein Fallback auf einen anderen Wert.
    assert ev["golden_cloud_score_sun_dir"] is None
    assert ev["cl_sun_dir"] is None
    assert ev["cm_sun_dir"] is None
    # Gegenrichtung unbeeinträchtigt (unabhängiger Fetch).
    assert ev["golden_cloud_score_antisolar_dir"] is not None
    # Allgemeines Wetter (Fotografen-Standort) unbeeinträchtigt.
    assert ev["weather_status"] == "ok"

    neue, _ = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Goldene Wolken" not in typen, "Signal nicht verfuegbar -> kein GOLDEN_CLOUDS-Event"


def test_ak11_fehlgeschlagener_wolken_abruf_gegenrichtung(monkeypatch):
    ev = _golden_event(loc_id="loc_ak11b", subject_azimuth=98)  # RED_SKY-Richtung
    main._feed_cache = [ev]

    (_sun_lat, _sun_lon), (anti_lat, anti_lon) = main._cloud_mood_projection_points(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, anti_lat, anti_lon):
            raise RuntimeError("Open-Meteo down (Gegenrichtung)")
        return _forecast(datetime.now(timezone.utc), cl=10, cm=50, ch=20)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.9)  # hoch, aber gcs=None blockt trotzdem
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())  # darf nicht crashen

    assert ev["golden_cloud_score_antisolar_dir"] is None
    assert ev["cl_antisolar_dir"] is None
    assert ev["cm_antisolar_dir"] is None
    assert ev["weather_status"] == "ok"

    neue, _ = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" not in typen, "Signal nicht verfuegbar -> kein RED_SKY-Event, auch bei hohem Aerosolwert"


# ---------------------------------------------------------------------------
# AK-4/AK-10: Fast-Path und Cronlauf liefern identische Projektion/Ergebnisse
# ---------------------------------------------------------------------------

def test_ak4_ak10_fastpath_und_cronlauf_liefern_identische_projektion(monkeypatch):
    # subject_azimuth=0 matcht bewusst WEDER die Sonnenrichtung (278°) NOCH die
    # Gegenrichtung (98°) -> weder GOLDEN_CLOUDS noch RED_SKY werden erzeugt, das
    # Original-Event bleibt unveraendert (nicht per AK-10/US-109 aus _feed_cache
    # entfernt) und damit fuer den direkten Cronlauf-vs-Fast-Path-Vergleich am
    # selben Dict-Objekt verfuegbar. Die Projektion selbst haengt nicht von
    # subject_azimuth ab (nur die Richtungspruefung fuer die Event-Erzeugung).
    ev = _golden_event(loc_id="loc_ak10", subject_azimuth=0)
    main._feed_cache = [ev]

    (sun_lat, sun_lon), (anti_lat, anti_lon) = main._cloud_mood_projection_points(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, sun_lat, sun_lon):
            return _forecast(datetime.now(timezone.utc), cl=10, cm=50, ch=20)
        if _match(lat, lon, anti_lat, anti_lon):
            return _forecast(datetime.now(timezone.utc), cl=25, cm=45, ch=35)
        return _forecast(datetime.now(timezone.utc), cl=60, cm=60, ch=60)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.4)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())
    cron_result = {
        "gcs_sun": ev["golden_cloud_score_sun_dir"],
        "gcs_anti": ev["golden_cloud_score_antisolar_dir"],
        "cl_sun": ev["cl_sun_dir"], "cm_sun": ev["cm_sun_dir"],
        "cl_anti": ev["cl_antisolar_dir"], "cm_anti": ev["cm_antisolar_dir"],
        "aod": ev["weather_details"]["aerosol_optical_depth"],
    }
    assert cron_result["gcs_sun"] is not None
    assert cron_result["gcs_anti"] is not None
    assert cron_result["aod"] is not None

    # Zustand zuruecksetzen, Fast-Path erneut mit identischen Mocks laufen lassen.
    for k in ("golden_cloud_score_sun_dir", "cl_sun_dir", "cm_sun_dir",
              "golden_cloud_score_antisolar_dir", "cl_antisolar_dir", "cm_antisolar_dir"):
        ev[k] = None
    ev["weather_details"]["aerosol_optical_depth"] = None
    ev["weather_status"] = None

    ready = _run(main._weather_overlay_single("loc_ak10"))
    assert ready is True

    assert ev["golden_cloud_score_sun_dir"] == cron_result["gcs_sun"]
    assert ev["golden_cloud_score_antisolar_dir"] == cron_result["gcs_anti"]
    assert ev["cl_sun_dir"] == cron_result["cl_sun"]
    assert ev["cm_sun_dir"] == cron_result["cm_sun"]
    assert ev["cl_antisolar_dir"] == cron_result["cl_anti"]
    assert ev["cm_antisolar_dir"] == cron_result["cm_anti"]
    assert ev["weather_details"]["aerosol_optical_depth"] == cron_result["aod"]


# ---------------------------------------------------------------------------
# Regression: _build_weather_error_message() bleibt mit alter 2-Parameter-
# Signatur (BUG-77/US-130) aufrufbar (neue Parameter optional)
# ---------------------------------------------------------------------------

def test_build_weather_error_message_bleibt_2_arg_kompatibel():
    msg = main._build_weather_error_message(["Standort A"], [])
    assert msg is not None
    assert "Wetterdaten fehlgeschlagen für: Standort A" in msg
    assert main._build_weather_error_message([], []) is None


# ---------------------------------------------------------------------------
# US-131-Nachtrag (2026-07-13, Weg-Gate-Nachtrag Stephan): Der bestehende
# US-07-Wolkenstimmungs-Filter/die Detail-Sheet-Anzeige im Frontend
# (web/index.html, Funktion cloudMoodScoreFor(), genutzt in Filter.apply() und
# im Detail-Sheet) wurde von e["golden_cloud_score"] (unprojiziert, Fotografen-
# Standort) auf die beiden entkoppelten projizierten Felder umgestellt:
#   - "Goldene Stunde Morgen"/"Goldene Stunde Abend"/"Goldene Wolken"
#     -> golden_cloud_score_sun_dir (Sonnenrichtung)
#   - "Himmelsröte" -> golden_cloud_score_antisolar_dir (Gegenrichtung/Antisolar)
#   - "Rote Wolken" (US-132/RED_CLOUDS) führt bewusst KEINEN Wolkenstimmung-Wert
#     (golden_cloud_score bleibt für Blaue-Stunde-Events immer None, siehe
#     _red_clouds_inputs()-Docstring, Pre-Mortem Szenario 3) -> Frontend fällt in
#     diesem Fall auf golden_cloud_score zurück, das ebenfalls None ist, und
#     blendet das Event wie bisher unverändert aus der Wolkenstimmung-Anzeige aus.
#
# Diese Umstellung ist reines Frontend-JS (kein zusätzlicher Backend-Code, siehe
# main.get_opportunities()/_filter_feed() unten). Die folgenden Tests sichern
# die Backend-seitige Voraussetzung dafür ab: GET /opportunities gibt rohe
# dicts zurück (kein Pydantic-Response-Schema, das die neuen Felder
# herausfiltern könnte) -- die projizierten Felder kommen unverändert im
# API-Response an, für alle betroffenen Event-Typen.
# ---------------------------------------------------------------------------

def test_nachtrag_opportunities_response_enthaelt_projizierte_felder_ungekuerzt():
    """/opportunities liefert golden_cloud_score_sun_dir UND
    golden_cloud_score_antisolar_dir unverändert mit aus (kein Response-Schema
    kürzt sie heraus) -- Voraussetzung dafür, dass cloudMoodScoreFor() im
    Frontend sie überhaupt lesen kann. Der alte, unprojizierte
    golden_cloud_score bleibt zusätzlich erhalten (Regression, wird von anderen
    Stellen im Backend weiterhin genutzt, s. AK-2 oben)."""
    ev = _golden_event(loc_id="loc_nachtrag_a", event_type="Goldene Wolken")
    ev["golden_cloud_score_sun_dir"] = 0.91
    ev["golden_cloud_score_antisolar_dir"] = 0.12
    ev["golden_cloud_score"] = 0.5
    main._feed_cache = [ev]

    result = _run(main.get_opportunities(min_score=0.0, days=14))

    assert len(result) == 1
    out = result[0]
    assert out["golden_cloud_score_sun_dir"] == 0.91
    assert out["golden_cloud_score_antisolar_dir"] == 0.12
    assert out["golden_cloud_score"] == 0.5


def test_nachtrag_himmelsroete_und_rote_wolken_ueber_opportunities_ungekuerzt():
    """'Himmelsröte' liefert den Gegenrichtungswert unverändert; 'Rote Wolken'
    (RED_CLOUDS/US-132) führt weiterhin keinen golden_cloud_score-Wert (bleibt
    None) -- beide Zustände kommen unverändert im API-Response an, als
    Datengrundlage für die frontend-seitige Fallback-Logik in
    cloudMoodScoreFor()."""
    ev_rs = _golden_event(loc_id="loc_nachtrag_b", event_type="Himmelsröte")
    ev_rs["golden_cloud_score_sun_dir"] = 0.10
    ev_rs["golden_cloud_score_antisolar_dir"] = 0.88

    ev_rc = _golden_event(loc_id="loc_nachtrag_c", event_type="Rote Wolken")
    ev_rc["golden_cloud_score"] = None
    ev_rc["golden_cloud_score_sun_dir"] = None
    ev_rc["golden_cloud_score_antisolar_dir"] = None

    main._feed_cache = [ev_rs, ev_rc]

    result = _run(main.get_opportunities(min_score=0.0, days=14))
    by_id = {o["location_id"]: o for o in result}

    assert by_id["loc_nachtrag_b"]["golden_cloud_score_antisolar_dir"] == 0.88
    assert by_id["loc_nachtrag_c"]["golden_cloud_score"] is None
    assert by_id["loc_nachtrag_c"]["golden_cloud_score_sun_dir"] is None
    assert by_id["loc_nachtrag_c"]["golden_cloud_score_antisolar_dir"] is None


# ---------------------------------------------------------------------------
# US-131-Nachtrag (2026-07-13, gemessener Befund): 339 parallele Requests an
# api.open-meteo.com in einem einzigen /weather-refresh-Lauf, davon 106 (~31%)
# mit HTTP 429 abgelehnt. Entschärfung: asyncio.Semaphore begrenzt die Anzahl
# GLEICHZEITIG laufender fetch_weather_forecast()/fetch_aerosol_forecast()-Calls
# in _fetch_weather_and_aerosol() auf WEATHER_API_MAX_CONCURRENT_REQUESTS.
# asyncio.gather() plant weiterhin ALLE Calls ein (keine Funktionsänderung an der
# Gesamtlogik) -- nur die tatsächliche Gleichzeitigkeit wird gedrosselt.
# ---------------------------------------------------------------------------

def test_nachtrag_max_concurrent_requests_konstante_ist_konservativ_gesetzt():
    """Konservativer, benannter Grenzwert (analog CLOUD_MOOD_PROJECTION_DISTANCE_M-
    Muster) -- kein exaktes Open-Meteo-Limit recherchiert (nicht verifizierbar ohne
    Internetzugriff), sondern bewusst niedrig gewählter, leicht änderbarer Wert."""
    assert main.WEATHER_API_MAX_CONCURRENT_REQUESTS == 5


def test_nachtrag_drosselung_cronlauf_ueberschreitet_obergrenze_nie(monkeypatch):
    """Cronlauf (_weather_overlay): Viele Locations mit jeweils eigener Koordinate
    (kein Dedup) erzeugen deutlich mehr als WEATHER_API_MAX_CONCURRENT_REQUESTS
    eingeplante Wetter-/Sonnenrichtungs-/Gegenrichtungs-/Aerosol-Calls. Die gemockten
    Fetch-Funktionen zählen die tatsächlich gleichzeitig laufenden Aufrufe (Zähler
    hoch vor einem asyncio.sleep, runter danach) -- der gemessene Höchstwert darf die
    konfigurierte Obergrenze nie überschreiten, muss sie aber tatsächlich erreichen
    (sonst würde das Semaphore nichts drosseln, sondern zu aggressiv serialisieren)."""
    events = [
        _golden_event(
            loc_id=f"loc_throttle_{i}",
            observer_lat=50.0 + i * 0.7,
            observer_lon=10.0 + i * 0.7,
            subject_lat=50.0 + i * 0.7 - 0.15,
            subject_lon=10.0 + i * 0.7 - 0.15,
        )
        for i in range(20)
    ]
    main._feed_cache = events

    concurrency = {"current": 0, "max": 0}

    async def fake_weather(lat, lon, days=7):
        concurrency["current"] += 1
        concurrency["max"] = max(concurrency["max"], concurrency["current"])
        await asyncio.sleep(0.01)
        concurrency["current"] -= 1
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        concurrency["current"] += 1
        concurrency["max"] = max(concurrency["max"], concurrency["current"])
        await asyncio.sleep(0.01)
        concurrency["current"] -= 1
        return _aerosol_forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    assert concurrency["max"] <= main.WEATHER_API_MAX_CONCURRENT_REQUESTS, (
        f"Es liefen {concurrency['max']} Requests gleichzeitig -- "
        f"mehr als die konfigurierte Obergrenze {main.WEATHER_API_MAX_CONCURRENT_REQUESTS}"
    )
    assert concurrency["max"] == main.WEATHER_API_MAX_CONCURRENT_REQUESTS, (
        "Semaphore serialisiert zu stark -- Obergrenze wurde nie ausgeschöpft, "
        "obwohl deutlich mehr Tasks eingeplant waren"
    )


def test_nachtrag_drosselung_fastpath_ueberschreitet_obergrenze_nie(monkeypatch):
    """Fast-Path (_weather_overlay_single): mehrere Goldene-Stunde-Events derselben
    Location zu unterschiedlichen Zeitpunkten/mit unterschiedlichen Sichtachsen
    erzeugen ebenfalls mehr als WEATHER_API_MAX_CONCURRENT_REQUESTS eingeplante
    Calls (Wetter + je Event Sonnenrichtung/Gegenrichtung/Aerosol an eigenen
    projizierten Punkten). Nachweis, dass die Drosselung -- weil beide Pfade
    exakt denselben _fetch_weather_and_aerosol()-Helfer nutzen (AK-4/AK-10) --
    auch für den Fast-Path gilt, nicht nur für den Cronlauf."""
    loc_id = "loc_throttle_single"
    events = [
        _golden_event(
            loc_id=loc_id,
            shoot_offset_h=6 + i,
            subject_lat=52.40 + i * 0.05,
            subject_lon=13.10 + i * 0.05,
            subject_azimuth=98 + i,
            sunset_azimuth=278 + i,
        )
        for i in range(10)
    ]
    main._feed_cache = events

    concurrency = {"current": 0, "max": 0}

    async def fake_weather(lat, lon, days=7):
        concurrency["current"] += 1
        concurrency["max"] = max(concurrency["max"], concurrency["current"])
        await asyncio.sleep(0.01)
        concurrency["current"] -= 1
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        concurrency["current"] += 1
        concurrency["max"] = max(concurrency["max"], concurrency["current"])
        await asyncio.sleep(0.01)
        concurrency["current"] -= 1
        return _aerosol_forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    ready = _run(main._weather_overlay_single(loc_id))

    assert ready is True
    assert concurrency["max"] <= main.WEATHER_API_MAX_CONCURRENT_REQUESTS, (
        f"Fast-Path: {concurrency['max']} Requests gleichzeitig -- "
        f"mehr als die konfigurierte Obergrenze {main.WEATHER_API_MAX_CONCURRENT_REQUESTS}"
    )
    assert concurrency["max"] == main.WEATHER_API_MAX_CONCURRENT_REQUESTS, (
        "Semaphore serialisiert zu stark -- Obergrenze wurde im Fast-Path nie "
        "ausgeschöpft, obwohl deutlich mehr Tasks eingeplant waren"
    )


# ---------------------------------------------------------------------------
# US-131 2. Nachtrag (2026-07-13, 2. Live-Messung): Semaphore allein (ohne
# Pacing) reichte real weiterhin nicht -- 1186 Requests, davon 253 mit HTTP 429
# (~21%), gegen die echte Open-Meteo-API. Die Semaphore begrenzt nur, WIE VIELE
# Requests gleichzeitig laufen, nicht WIE SCHNELL ein frei gewordener Slot sofort
# wieder einen neuen Request abfeuert. Ergänzung: WEATHER_API_REQUEST_PACING_SECONDS
# erzwingt einen Mindestabstand zwischen zwei Calls IM SELBEN Slot (asyncio.sleep
# NACH dem Fetch, VOR Freigabe der Semaphore, s. main._run_one()).
#
# Zeit-Tests mit echter Wanduhrzeit wären in CI timing-empfindlich (flaky) --
# stattdessen wird main.asyncio.sleep gemockt und geprüft, DASS und MIT WELCHEM
# Wert es aufgerufen wird (robustes Muster laut Weg-Gate-Entscheidung).
# ---------------------------------------------------------------------------

def test_nachtrag_pacing_konstante_ist_konservativ_gesetzt():
    """Benannter, konservativer Startwert -- kein exaktes Open-Meteo-Zeitfenster-
    Limit recherchiert (nicht verifizierbar ohne Internetzugriff), bewusst klein
    und leicht änderbar (analog WEATHER_API_MAX_CONCURRENT_REQUESTS-Muster).
    Überschlagsrechnung (s. Docstring in main.py): 5 parallele Slots x
    (1 Request / 0.15s) = ca. 33 Requests/Sekunde Pacing-Obergrenze."""
    assert main.WEATHER_API_REQUEST_PACING_SECONDS == pytest.approx(0.15)


def test_nachtrag_pacing_sleep_folgt_auf_jeden_erfolgreichen_fetch_call(monkeypatch):
    """Statt echte Wanduhrzeit zu stoppen (flaky in CI): main.asyncio.sleep patchen
    und aufzeichnen, mit welchem Wert es aufgerufen wird. Jeder tatsächliche
    fetch_weather_forecast()/fetch_aerosol_forecast()-Call muss von genau einem
    asyncio.sleep(WEATHER_API_REQUEST_PACING_SECONDS)-Aufruf gefolgt sein, BEVOR
    der nächste Call im selben Slot starten kann (Pacing INNERHALB des Semaphore-
    Blocks, nach dem Fetch, s. main._run_one())."""
    events = [
        _golden_event(
            loc_id=f"loc_pacing_{i}",
            observer_lat=50.0 + i * 0.7,
            observer_lon=10.0 + i * 0.7,
            subject_lat=50.0 + i * 0.7 - 0.15,
            subject_lon=10.0 + i * 0.7 - 0.15,
        )
        for i in range(6)
    ]
    main._feed_cache = events

    sleep_calls = []

    async def fake_weather(lat, lon, days=7):
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)
        # Kein echtes Warten -- Test bleibt schnell, es wird nur der Aufruf-Wert
        # geprüft (robustes Muster statt echter Wanduhrzeit-Messung).
    monkeypatch.setattr(main.asyncio, "sleep", fake_sleep)

    _run(main._weather_overlay())

    assert len(sleep_calls) > 0, (
        "asyncio.sleep wurde beim Pacing nie aufgerufen -- Mindestabstand zwischen "
        "aufeinanderfolgenden Requests fehlt"
    )
    assert all(s == main.WEATHER_API_REQUEST_PACING_SECONDS for s in sleep_calls), (
        f"Pacing-Sleep wurde nicht durchgängig mit WEATHER_API_REQUEST_PACING_SECONDS "
        f"({main.WEATHER_API_REQUEST_PACING_SECONDS}) aufgerufen: {sleep_calls}"
    )


def test_nachtrag_pacing_gilt_auch_bei_fehlgeschlagenem_fetch(monkeypatch):
    """try/finally um den Fetch-Call in main._run_one() stellt sicher, dass das
    Pacing-Sleep auch nach einem fehlgeschlagenen Request läuft -- ein
    fehlgeschlagener Call (z. B. 429/Timeout) zählt bei der externen API ebenfalls
    als Request und darf den Slot nicht sofort wieder freigeben."""
    events = [_golden_event(loc_id="loc_pacing_fail")]
    main._feed_cache = events

    sleep_calls = []

    async def failing_weather(lat, lon, days=7):
        raise RuntimeError("simulierter Fetch-Fehler (analog HTTP 429)")
    monkeypatch.setattr(main, "fetch_weather_forecast", failing_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)
    monkeypatch.setattr(main.asyncio, "sleep", fake_sleep)

    _run(main._weather_overlay())

    assert len(sleep_calls) > 0, (
        "Pacing-Sleep wurde bei fehlgeschlagenem Fetch übersprungen -- "
        "try/finally in main._run_one() fehlt oder ist fehlerhaft"
    )
    assert all(s == main.WEATHER_API_REQUEST_PACING_SECONDS for s in sleep_calls)


def test_nachtrag_pacing_gilt_auch_im_fastpath(monkeypatch):
    """Fast-Path (_weather_overlay_single) nutzt exakt denselben _run_one()-Helfer
    wie der Cronlauf (AK-4/AK-10-Konsistenzmuster) -- Nachweis, dass das Pacing
    automatisch auch hier greift, nicht nur im Cronlauf."""
    loc_id = "loc_pacing_single"
    events = [
        _golden_event(
            loc_id=loc_id,
            shoot_offset_h=6 + i,
            subject_lat=52.40 + i * 0.05,
            subject_lon=13.10 + i * 0.05,
            subject_azimuth=98 + i,
            sunset_azimuth=278 + i,
        )
        for i in range(4)
    ]
    main._feed_cache = events

    sleep_calls = []

    async def fake_weather(lat, lon, days=7):
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)
    monkeypatch.setattr(main.asyncio, "sleep", fake_sleep)

    ready = _run(main._weather_overlay_single(loc_id))

    assert ready is True
    assert len(sleep_calls) > 0, (
        "Fast-Path: asyncio.sleep wurde beim Pacing nie aufgerufen"
    )
    assert all(s == main.WEATHER_API_REQUEST_PACING_SECONDS for s in sleep_calls)
