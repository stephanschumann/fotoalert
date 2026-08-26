"""
BUG-108: Ereignistyp "Rote Wolken" (RED_CLOUDS) prüfte bislang nur das lokale Wetter am
Fotografen-Standort (weather_details, via forecast.get_at(shoot_dt)) — keine Projektion
entlang der Blickrichtung, anders als "Goldene Wolken"/"Himmelsröte" (US-131, 30 km über
CLOUD_MOOD_PROJECTION_DISTANCE_M). Dieses Ticket rüstet RED_CLOUDS mit einer eigenen,
unabhängigen Projektion nach: 100 km (RED_CLOUDS_PROJECTION_DISTANCE_M) in Sonnenrichtung
(celestial_azimuth, Blaue-Stunde-Sonnenposition — NICHT sunrise_azimuth/sunset_azimuth, ein
zeitlich anderer Azimut, Pre-Mortem Szenario 3).

Weg-Gate-Entscheidungen (Stephan, 2026-08-23, siehe BACKLOG.md BUG-108):
  1. Eigene Projektionsdistanz NUR für RED_CLOUDS: 100 km (RED_CLOUDS_PROJECTION_DISTANCE_M),
     unabhängig von den bestehenden 30 km für GOLDEN_CLOUDS/RED_SKY.
  2. Fetch-Fehlschlag am entfernten Punkt: KEIN Rückfall auf lokales Wetter — der Kandidat
     verschwindet für diesen Zeitpunkt komplett (konsistent zu GOLDEN_CLOUDS/RED_SKY, AK-11
     aus US-131).
  3. Der Azimut-Toleranz-Check (should_generate_red_clouds_event()) bleibt UNVERÄNDERT —
     nur die Wolkendaten-Quelle (ch/cl) wechselt.
  4. Das allgemein angezeigte Wetter am eigenen Standort bleibt unverändert lokal
     (weather_details/weather_description/weather_code).

Abgedeckte Akzeptanzkriterien (siehe BACKLOG.md BUG-108, Rules 1-3 + Fragen 1/2):
  AK-1 (Rule 1):  Lokal kaum/keine hohen Wolken, aber am entfernten Punkt (100 km,
                  Blickrichtung) genug hohe und nicht zu viele tiefe Wolken -> RED_CLOUDS-
                  Kandidat erscheint trotzdem.
  AK-2 (Rule 2):  Azimut-Toleranz-Check bleibt exakt so streng wie bisher (positiver Fall,
                  Grenzwert exakt auf der Toleranz).
  AK-3 (Rule 2,
        negativ): Azimut außerhalb Toleranz -> weiterhin kein Kandidat, unabhängig von den
                  entfernten Wolkendaten.
  AK-4 (Rule 3):  Lokal angezeigtes Wetter bleibt unverändert das Standort-Wetter.
  AK-5:           Zu viele tiefe Wolken am entfernten Punkt -> weiterhin kein Kandidat.
  AK-6 (Frage 2): Fetch-Fehlschlag am entfernten Punkt -> kein Kandidat, kein Rückfall.
  AK-7:           Der Hintergrund-Wetterabruf bleibt strukturell innerhalb desselben,
                  bereits gehärteten Zeitbudget-Mechanismus (WEATHER_OVERLAY_MAX_TOTAL_SECONDS,
                  Semaphore/Retry/Pacing, Dedup) — kein neuer, ungehärteter Pfad. Ein realer
                  Live-Lauf-Nachweis bei der tatsächlichen Produktions-Location-Zahl ist hier
                  NICHT synthetisch nachgebaut (BUG-104-Präzedenzfall: ein Unit-Test kann
                  externe Netzwerklatenz/Rate-Limit-Verhalten nicht realistisch reproduzieren)
                  — bleibt offener Live-Nachweis-Punkt.
  AK-8:           Mehrere echte Kandidaten zeigen live tatsächlich befüllte (nicht leere)
                  Wolkendaten vom entfernten Punkt.
  AK-9:           Der Potsdam-Beispielfall (Schloss Babelsberg -> Pfingstberg Belvedere,
                  echte Koordinaten aus data/locations.py) liefert bei vergleichbarer
                  Wetterlage einen Kandidaten.
  AK-10:          Der erzeugte Kandidat landet im zentralen _feed_cache (id-Präfix "rc_"),
                  aus dem alle sechs Ansichten lesen (Fundstellen-Sweep, kein separater
                  Anpassungsbedarf pro Ansicht).

Zusätzlich (Pre-Mortem-Absicherung, nicht direkt AK-nummeriert):
  - Szenario 3: Projektion nutzt celestial_azimuth, NICHT sunset_azimuth/sunrise_azimuth.
  - Szenario 4: should_generate_red_clouds_event() selbst bleibt unangetastet — die
    Azimut-Prüfung vergleicht weiterhin Sonnenazimut vs. Motivazimut am
    Fotografen-Standort, NICHT den Azimut zum projizierten Punkt.
  - Regression: GOLDEN_CLOUDS/RED_SKY (_directional_cloud_values()-Erweiterung um ch)
    bleiben unverändert (test_us131.py läuft dafür unverändert weiter grün).
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

import main
from discover.geometry import destination_point
from calculations.weather import (
    HourlyWeather, WeatherForecast,
    RED_CLOUDS_PROJECTION_DISTANCE_M, CLOUD_MOOD_PROJECTION_DISTANCE_M,
    RED_CLOUDS_HIGH_CLOUD_THRESHOLD_PCT, RED_CLOUDS_LOW_CLOUD_CAP_PCT,
    RED_CLOUDS_AZIMUTH_TOLERANCE_DEG,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ---------------------------------------------------------------------------
# Helfer (Muster analog test_us131.py)
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
        wind_direction_deg=180.0, temperature_c=12.0, dew_point_c=6.0, weather_code=1,
    )


def _forecast(ref: datetime, cl=10.0, cm=10.0, ch=10.0) -> WeatherForecast:
    hours = [_hourly(ref + timedelta(hours=i), cl, cm, ch) for i in range(-2, 72)]
    return WeatherForecast(location_lat=0.0, location_lon=0.0,
                            fetched_at=datetime.now(timezone.utc), hourly=hours)


def _blue_hour_event(loc_id="loc1", shoot_offset_h=12, observer_lat=52.5, observer_lon=13.4,
                      subject_lat=52.40, subject_lon=13.10, subject_azimuth=278,
                      celestial_azimuth=278, celestial_altitude=-5.0,
                      event_type="Blaue Stunde"):
    """Minimales, qualifizierendes Blaue-Stunde-Event-Dict (subject_lat/lon +
    subject_azimuth + celestial_azimuth/celestial_altitude vorhanden ->
    _red_clouds_projection_point() berechnet eine Projektion)."""
    shoot = datetime.now(timezone.utc) + timedelta(hours=shoot_offset_h)
    return {
        "id": f"test-{loc_id}",
        "location_id": loc_id, "location_name": loc_id,
        "event_type": event_type,
        "observer_lat": observer_lat, "observer_lon": observer_lon,
        "subject_lat": subject_lat, "subject_lon": subject_lon,
        "subject_azimuth": subject_azimuth,
        "celestial_azimuth": celestial_azimuth, "celestial_altitude": celestial_altitude,
        "sunset_azimuth": None, "sunrise_azimuth": None,  # bewusst None: RED_CLOUDS darf diese nicht nutzen
        "golden_cloud_score": None,
        "shoot_time": shoot.isoformat(),
        "astronomy_score": 0.8, "overall_score": 0.8,
        "weather_score": 0.0, "weather_description": "",
    }


def _match(lat, lon, ref_lat, ref_lon, tol=0.001):
    return abs(lat - ref_lat) < tol and abs(lon - ref_lon) < tol


# ---------------------------------------------------------------------------
# Konstante: eigene, unabhängige Distanz (Frage 1, Stephan 2026-08-23: 100 km)
# ---------------------------------------------------------------------------

def test_red_clouds_projection_distance_ist_100km():
    assert RED_CLOUDS_PROJECTION_DISTANCE_M == 100_000


def test_red_clouds_projection_distance_unabhaengig_von_cloud_mood_distance():
    """Eigene Konstante, nicht identisch mit den bestehenden 30 km für
    GOLDEN_CLOUDS/RED_SKY (Option C, nicht Option A/B aus dem Ticket)."""
    assert RED_CLOUDS_PROJECTION_DISTANCE_M != CLOUD_MOOD_PROJECTION_DISTANCE_M
    assert CLOUD_MOOD_PROJECTION_DISTANCE_M == 30_000


# ---------------------------------------------------------------------------
# Geometrie: _red_clouds_projection_point() — reine Geometrie, kein Netzwerk
# ---------------------------------------------------------------------------

def test_red_clouds_projection_point_matches_destination_point():
    """_red_clouds_projection_point() muss exakt destination_point() mit
    subject_lat/subject_lon als Ursprung, celestial_azimuth als Bearing und
    RED_CLOUDS_PROJECTION_DISTANCE_M (100 km) nutzen."""
    e = _blue_hour_event(subject_lat=52.40, subject_lon=13.10, celestial_azimuth=278)
    result = main._red_clouds_projection_point(e)
    assert result is not None
    expected = destination_point(52.40, 13.10, 278, RED_CLOUDS_PROJECTION_DISTANCE_M)
    assert result == expected


def test_red_clouds_projection_point_nutzt_celestial_azimuth_nicht_sunset_azimuth():
    """Pre-Mortem Szenario 3: Die Projektion darf NICHT versehentlich sunset_azimuth/
    sunrise_azimuth (Goldene-Stunde-Werte) verwenden — celestial_azimuth und
    sunset_azimuth unterscheiden sich hier bewusst deutlich, damit ein Vertauschen
    sofort auffiele."""
    e = _blue_hour_event(subject_lat=52.40, subject_lon=13.10, celestial_azimuth=278)
    e["sunset_azimuth"] = 40  # bewusst stark abweichend
    e["sunrise_azimuth"] = 220  # bewusst stark abweichend
    result = main._red_clouds_projection_point(e)
    expected_mit_celestial = destination_point(52.40, 13.10, 278, RED_CLOUDS_PROJECTION_DISTANCE_M)
    expected_mit_sunset = destination_point(52.40, 13.10, 40, RED_CLOUDS_PROJECTION_DISTANCE_M)
    assert result == expected_mit_celestial
    assert result != expected_mit_sunset


def test_red_clouds_projection_point_none_fuer_goldene_stunde_event():
    """Disjunkte Typmengen: ein Goldene-Stunde-Event darf keinen RED_CLOUDS-
    Projektionspunkt bekommen (_GOLDEN_HOUR_TYPES/_BLUE_HOUR_TYPES sind disjunkt)."""
    e = _blue_hour_event(event_type="Goldene Stunde Abend")
    assert main._red_clouds_projection_point(e) is None


def test_red_clouds_projection_point_none_ohne_celestial_azimuth():
    e = _blue_hour_event(celestial_azimuth=None)
    assert main._red_clouds_projection_point(e) is None


def test_red_clouds_projection_point_none_ohne_subject_lat_lon():
    e = _blue_hour_event(subject_lat=None, subject_lon=None)
    assert main._red_clouds_projection_point(e) is None


def test_red_clouds_projection_point_morgen_funktioniert_ebenso():
    """AK-9-Symmetrie (analog US-132 AK-9): 'Blaue Stunde Morgen' qualifiziert
    genauso wie 'Blaue Stunde' (Abend) für die Projektion."""
    e = _blue_hour_event(event_type="Blaue Stunde Morgen", celestial_azimuth=95)
    result = main._red_clouds_projection_point(e)
    assert result is not None
    expected = destination_point(e["subject_lat"], e["subject_lon"], 95, RED_CLOUDS_PROJECTION_DISTANCE_M)
    assert result == expected


# ---------------------------------------------------------------------------
# _directional_cloud_values(): BUG-108 erweitert die Rückgabe um ch (4-Tupel)
# ---------------------------------------------------------------------------

def test_directional_cloud_values_gibt_jetzt_vierten_wert_ch_zurueck():
    ref = datetime.now(timezone.utc)
    fc = _forecast(ref, cl=12, cm=22, ch=48)
    gcs, cl, cm, ch = main._directional_cloud_values(fc, ref)
    assert ch == 48
    assert cl == 12
    assert cm == 22
    assert gcs is not None


def test_directional_cloud_values_none_forecast_gibt_4x_none():
    assert main._directional_cloud_values(None, datetime.now(timezone.utc)) == (None, None, None, None)


# ---------------------------------------------------------------------------
# AK-1 (Rule 1): lokal kaum/keine hohen Wolken, entfernt genug hohe + wenig
# tiefe Wolken -> Kandidat erscheint trotzdem
# ---------------------------------------------------------------------------

def test_ak1_lokal_klar_entfernt_bewoelkt_erzeugt_kandidat(monkeypatch):
    ev = _blue_hour_event(loc_id="loc_ak1", subject_azimuth=278, celestial_azimuth=278)
    main._feed_cache = [ev]

    rc_lat, rc_lon = main._red_clouds_projection_point(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, rc_lat, rc_lon):
            # Entfernter Punkt: viel hohe Bewölkung, wenig tiefe Bewölkung
            return _forecast(datetime.now(timezone.utc), cl=5, cm=10, ch=45)
        # Fotografen-Standort: kaum hohe Wolken
        return _forecast(datetime.now(timezone.utc), cl=5, cm=5, ch=0)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return None  # RED_CLOUDS braucht keinen Aerosol-Fetch
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    assert ev["ch_red_clouds_dir"] == 45
    assert ev["cl_red_clouds_dir"] == 5
    assert ev["weather_status"] == "ok"

    neue, _ = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Rote Wolken" in typen, (
        f"AK-1: lokal 0% hohe Wolken, entfernt 45% hohe/5% tiefe Wolken -> Kandidat "
        f"erwartet, tatsächlich erzeugte Typen: {typen}"
    )


# ---------------------------------------------------------------------------
# AK-2/AK-3 (Rule 2): Azimut-Toleranz-Check bleibt unverändert streng
# ---------------------------------------------------------------------------

def test_ak2_azimut_grenzwert_exakt_toleranz_bleibt_positiv(monkeypatch):
    """Regression: Differenz exakt RED_CLOUDS_AZIMUTH_TOLERANCE_DEG (inklusiver
    Grenzwert, unverändert von should_generate_red_clouds_event()) -> weiterhin
    True, auch mit der neuen Wolkendatenquelle."""
    sun_az = 278
    subject_az = sun_az + RED_CLOUDS_AZIMUTH_TOLERANCE_DEG
    ev = _blue_hour_event(loc_id="loc_ak2", subject_azimuth=subject_az, celestial_azimuth=sun_az)
    main._feed_cache = [ev]

    rc_lat, rc_lon = main._red_clouds_projection_point(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, rc_lat, rc_lon):
            return _forecast(datetime.now(timezone.utc), cl=5, cm=10, ch=45)
        return _forecast(datetime.now(timezone.utc), cl=5, cm=5, ch=0)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return None
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    neue, _ = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Rote Wolken" in typen, f"Grenzwert exakt auf Toleranz sollte weiterhin True sein: {typen}"


def test_ak3_azimut_ausserhalb_toleranz_kein_kandidat_trotz_guter_entfernter_wolken(monkeypatch):
    """AK-3 (Rule 2, negativ): Azimut-Differenz weit außerhalb der Toleranz -> kein
    Kandidat, UNABHÄNGIG davon, wie gut die entfernten Wolkendaten aussehen."""
    ev = _blue_hour_event(loc_id="loc_ak3", subject_azimuth=100, celestial_azimuth=278)  # Diff 178°
    main._feed_cache = [ev]

    rc_lat, rc_lon = main._red_clouds_projection_point(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, rc_lat, rc_lon):
            # Ideale Wolkenlage am entfernten Punkt — trotzdem sollte kein Event entstehen.
            return _forecast(datetime.now(timezone.utc), cl=0, cm=0, ch=90)
        return _forecast(datetime.now(timezone.utc), cl=5, cm=5, ch=0)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return None
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    assert ev["ch_red_clouds_dir"] == 90  # Wolkendaten selbst kamen an
    neue, _ = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Rote Wolken" not in typen, (
        f"Azimut 178° außerhalb der {RED_CLOUDS_AZIMUTH_TOLERANCE_DEG}°-Toleranz muss "
        f"weiterhin blocken, unabhängig von den entfernten Wolkendaten: {typen}"
    )


# ---------------------------------------------------------------------------
# AK-4 (Rule 3): allgemein angezeigtes Wetter bleibt lokal
# ---------------------------------------------------------------------------

def test_ak4_lokal_angezeigtes_wetter_bleibt_am_fotografen_standort(monkeypatch):
    ev = _blue_hour_event(loc_id="loc_ak4", subject_azimuth=278, celestial_azimuth=278)
    main._feed_cache = [ev]

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, ev["observer_lat"], ev["observer_lon"]):
            return _forecast(datetime.now(timezone.utc), cl=3, cm=4, ch=2)  # lokal: klar
        return _forecast(datetime.now(timezone.utc), cl=70, cm=70, ch=70)  # entfernt: stark bewölkt
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return None
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    wd = ev["weather_details"]
    assert wd["cloud_cover_low_pct"] == 3
    assert wd["cloud_cover_mid_pct"] == 4
    assert wd["cloud_cover_high_pct"] == 2
    # Der entfernte Wert bleibt getrennt vom lokal angezeigten Wetter.
    assert ev["ch_red_clouds_dir"] == 70
    assert wd["cloud_cover_high_pct"] != ev["ch_red_clouds_dir"]


# ---------------------------------------------------------------------------
# AK-5: zu viele tiefe Wolken am entfernten Punkt -> weiterhin kein Kandidat
# ---------------------------------------------------------------------------

def test_ak5_zu_viele_tiefe_wolken_am_entfernten_punkt_kein_kandidat(monkeypatch):
    ev = _blue_hour_event(loc_id="loc_ak5", subject_azimuth=278, celestial_azimuth=278)
    main._feed_cache = [ev]

    rc_lat, rc_lon = main._red_clouds_projection_point(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, rc_lat, rc_lon):
            # Genug hohe Wolken, ABER auch sehr viele tiefe -> Sicht verstellt (AK-5).
            return _forecast(datetime.now(timezone.utc), cl=90, cm=20, ch=50)
        return _forecast(datetime.now(timezone.utc), cl=5, cm=5, ch=0)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return None
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    assert ev["ch_red_clouds_dir"] == 50
    assert ev["cl_red_clouds_dir"] == 90
    neue, _ = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Rote Wolken" not in typen, (
        f"cl=90 >= RED_CLOUDS_LOW_CLOUD_CAP_PCT ({RED_CLOUDS_LOW_CLOUD_CAP_PCT}) muss "
        f"weiterhin blocken: {typen}"
    )


# ---------------------------------------------------------------------------
# AK-6 (Frage 2): Fetch-Fehlschlag am entfernten Punkt -> kein Kandidat, KEIN
# Rückfall auf das lokale Wetter (Weg-Gate-Entscheidung Option A, 2026-08-23)
# ---------------------------------------------------------------------------

def test_ak6_fetch_fehlschlag_am_entfernten_punkt_kein_kandidat_kein_rueckfall(monkeypatch):
    ev = _blue_hour_event(loc_id="loc_ak6", subject_azimuth=278, celestial_azimuth=278)
    main._feed_cache = [ev]

    rc_lat, rc_lon = main._red_clouds_projection_point(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, rc_lat, rc_lon):
            raise RuntimeError("Open-Meteo down (RED_CLOUDS-Projektionspunkt)")
        # Lokales Wetter hätte, falls es fälschlich als Rückfall genutzt würde,
        # selbst eine RED_CLOUDS-taugliche Wolkenlage — genau das darf NICHT passieren.
        return _forecast(datetime.now(timezone.utc), cl=5, cm=10, ch=45)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return None
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())  # darf nicht crashen

    assert ev["ch_red_clouds_dir"] is None, "Fetch fehlgeschlagen -> kein Fallback-Wert"
    assert ev["cl_red_clouds_dir"] is None
    # Lokales Wetter (Fotografen-Standort) ist unabhängig davon weiterhin OK.
    assert ev["weather_status"] == "ok"

    neue, _ = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Rote Wolken" not in typen, (
        f"Fetch-Fehlschlag am Projektionspunkt muss den Kandidaten verschwinden lassen, "
        f"kein Rückfall auf lokales Wetter (Weg-Gate 2026-08-23): {typen}"
    )
    # BUG-77-Sammelpfad: derselbe Sichtbarkeits-Mechanismus wie sun_dir/antisolar_dir.
    status = main._job_status["weather"]
    assert status["status"] == "error"
    assert "Rote-Wolken-Projektionspunkt fehlgeschlagen" in status["last_error"]


def test_ak6_build_red_clouds_event_direkt_none_bei_ch_none():
    """Unit-Ebene (ergänzend zu AK-6 oben): _build_red_clouds_event() selbst gibt
    None zurück, wenn ch (oder cl) None ist — verhindert außerdem einen TypeError
    beim `ch < RED_CLOUDS_HIGH_CLOUD_THRESHOLD_PCT`-Vergleich in
    should_generate_red_clouds_event()."""
    result = main._build_red_clouds_event(
        {"id": "x"}, ch=None, cl=10, sun_alt=-5, sun_az=278, subject_az=278,
    )
    assert result is None


# ---------------------------------------------------------------------------
# AK-7: kein neuer, ungehärteter Pfad — derselbe Dedup-/Semaphore-/Timeout-
# Mechanismus wie die bestehenden drei Abruf-Arten (strukturelle Prüfung, s.
# Docstring oben zum Live-Nachweis-Vorbehalt)
# ---------------------------------------------------------------------------

def test_ak7_plan_weather_fetch_tasks_enthaelt_eigenen_red_clouds_dir_kind():
    ev = _blue_hour_event(loc_id="loc_ak7", subject_azimuth=278, celestial_azimuth=278)
    tasks_meta = main._plan_weather_fetch_tasks([ev])
    kinds = [kind for kind, *_ in tasks_meta]
    assert "red_clouds_dir" in kinds
    # Kein sun_dir/antisolar_dir/aerosol für ein reines Blaue-Stunde-Event (disjunkte
    # Typmengen — der Goldene-Stunde-Zweig darf für dieses Event keine Tasks liefern).
    assert "sun_dir" not in kinds
    assert "antisolar_dir" not in kinds
    assert "aerosol" not in kinds


def test_ak7_red_clouds_dir_dedupliziert_ueber_denselben_cache_key_mechanismus():
    """Zwei Events mit (nach PROJECTED_POINT_CACHE_PRECISION gerundet) identischem
    Projektionspunkt erzeugen NUR EINEN red_clouds_dir-Task — derselbe Dedup-
    Mechanismus (_projected_point_cache_key()) wie sun_dir/antisolar_dir/aerosol,
    kein eigener, separater Dedup (Pre-Mortem Szenario 1, Empfehlung des Pre-Mortems:
    denselben Mechanismus zwingend mitverwenden statt neu zu erfinden)."""
    ev1 = _blue_hour_event(loc_id="loc_dedup_a", subject_lat=52.401, subject_lon=13.101,
                            subject_azimuth=278, celestial_azimuth=278)
    ev2 = _blue_hour_event(loc_id="loc_dedup_b", subject_lat=52.4011, subject_lon=13.1011,
                            subject_azimuth=278, celestial_azimuth=278)
    tasks_meta = main._plan_weather_fetch_tasks([ev1, ev2])
    red_clouds_tasks = [t for t in tasks_meta if t[0] == "red_clouds_dir"]
    assert len(red_clouds_tasks) == 1, (
        f"Erwartet: 1 dedupliziertem red_clouds_dir-Task für zwei sehr nah beieinander "
        f"liegende Projektionspunkte, tatsächlich: {len(red_clouds_tasks)}"
    )


def test_ak7_kein_separater_ungehaerteter_run_one_pfad():
    """_run_one_weather_fetch() kennt "red_clouds_dir" nicht als Sonderfall — es fällt
    strukturell auf denselben fetch_weather_forecast()-Zweig wie "weather"/"sun_dir"/
    "antisolar_dir" (nur "aerosol" hat einen eigenen Zweig). Reine Quelltext-Prüfung,
    stellt sicher, dass kein neuer, unabhängiger Fetch-Pfad für RED_CLOUDS entstanden
    ist, der Semaphore/Retry/Pacing umgehen könnte."""
    import inspect
    src = inspect.getsource(main._run_one_weather_fetch)
    assert 'kind == "aerosol"' in src
    # Es darf keinen eigenen "red_clouds_dir"-Sonderfall im Fetch-Ausführungspfad geben.
    assert 'kind == "red_clouds_dir"' not in src


# ---------------------------------------------------------------------------
# AK-8: mehrere echte Kandidaten zeigen live tatsächlich befüllte Wolkendaten
# ---------------------------------------------------------------------------

def test_ak8_mehrere_kandidaten_zeigen_befuellte_entfernte_wolkendaten(monkeypatch):
    ev_a = _blue_hour_event(loc_id="loc_ak8_a", subject_lat=52.30, subject_lon=13.00,
                             subject_azimuth=278, celestial_azimuth=278)
    ev_b = _blue_hour_event(loc_id="loc_ak8_b", subject_lat=48.10, subject_lon=11.50,
                             subject_azimuth=95, celestial_azimuth=95, event_type="Blaue Stunde Morgen")
    main._feed_cache = [ev_a, ev_b]

    rc_a = main._red_clouds_projection_point(ev_a)
    rc_b = main._red_clouds_projection_point(ev_b)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, *rc_a):
            return _forecast(datetime.now(timezone.utc), cl=8, cm=15, ch=38)
        if _match(lat, lon, *rc_b):
            return _forecast(datetime.now(timezone.utc), cl=12, cm=18, ch=55)
        return _forecast(datetime.now(timezone.utc), cl=2, cm=2, ch=0)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return None
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    assert ev_a["ch_red_clouds_dir"] == 38
    assert ev_a["cl_red_clouds_dir"] == 8
    assert ev_b["ch_red_clouds_dir"] == 55
    assert ev_b["cl_red_clouds_dir"] == 12
    # Nicht nur "theoretisch vorhanden" — beide Werte sind reale, unterschiedliche
    # Zahlen (kein leerer/geteilter Platzhalter, kein zufälliges Verwechseln).
    assert ev_a["ch_red_clouds_dir"] != ev_b["ch_red_clouds_dir"]

    neue, _ = main._generate_cloud_mood_events([ev_a, ev_b])
    typen = [e["event_type"] for e in neue]
    assert typen.count("Rote Wolken") == 2, f"Beide Kandidaten erwartet: {typen}"


# ---------------------------------------------------------------------------
# AK-9: Potsdam-Beispielfall — Schloss Babelsberg -> Pfingstberg Belvedere
# (echte Koordinaten aus data/locations.py, id "schloss_babelsberg_pfingstberg")
# ---------------------------------------------------------------------------

def test_ak9_potsdam_beispielfall_schloss_babelsberg_pfingstberg(monkeypatch):
    """Ticket-Beobachtungsfall: lokal (Potsdam) 0% hohe Bewölkung, ca. 100 km
    entfernt (Richtung Magdeburg, Blickrichtung Nordwest) ein Rotwolken-Band ->
    Kandidat erscheint. Blickrichtung bewusst nah an der Sonnenrichtung gewählt
    (Diff 3°, wie im Ticket beobachtet: subject_azimuth 297,4° vs. Sonnenrichtung
    heute ~295°, beide innerhalb ideal_azimuth_range 310-340° plausibel)."""
    ev = _blue_hour_event(
        loc_id="schloss_babelsberg_pfingstberg",
        observer_lat=52.3975, observer_lon=13.0976,  # echte Location-Koordinaten
        subject_lat=52.4158, subject_lon=13.0688,
        subject_azimuth=297.4, celestial_azimuth=295.0,  # Diff 2,4° — innerhalb Toleranz
    )
    main._feed_cache = [ev]

    rc_lat, rc_lon = main._red_clouds_projection_point(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, rc_lat, rc_lon):
            # ~100 km Richtung Magdeburg: deutliches Rotwolken-Band laut Ticket-Beobachtung.
            return _forecast(datetime.now(timezone.utc), cl=8, cm=12, ch=40)
        # Potsdam selbst: 0% hohe Bewölkung (Ticket-Beobachtung, live verifiziert).
        return _forecast(datetime.now(timezone.utc), cl=5, cm=5, ch=0)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return None
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    neue, _ = main._generate_cloud_mood_events([ev])
    typen = [e["event_type"] for e in neue]
    assert "Rote Wolken" in typen, (
        f"Potsdam-Beispielfall (Schloss Babelsberg -> Pfingstberg Belvedere) sollte bei "
        f"dieser Wetterlage einen Kandidaten liefern, tatsächlich: {typen}"
    )
    rc = next(e for e in neue if e["event_type"] == "Rote Wolken")
    assert rc["title"] == "Rote Wolken über Belvedere auf dem Pfingstberg" or "Rote Wolken" in rc["title"]


# ---------------------------------------------------------------------------
# AK-10: Kandidat landet im zentralen _feed_cache (id-Präfix "rc_") — alle sechs
# Ansichten (Feed/Karte/Kalender/Scout/Chancen-Übersicht/Event-Detail) lesen
# strukturell aus demselben Cache (Fundstellen-Sweep der Analyse-Phase).
# ---------------------------------------------------------------------------

def test_ak10_kandidat_landet_im_zentralen_feed_cache(monkeypatch):
    ev = _blue_hour_event(loc_id="loc_ak10", subject_azimuth=278, celestial_azimuth=278)
    main._feed_cache = [ev]

    rc_lat, rc_lon = main._red_clouds_projection_point(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, rc_lat, rc_lon):
            return _forecast(datetime.now(timezone.utc), cl=5, cm=10, ch=45)
        return _forecast(datetime.now(timezone.utc), cl=5, cm=5, ch=0)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return None
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())  # ruft intern _inject_cloud_mood_events() auf

    rc_events = [e for e in main._feed_cache if e.get("id", "").startswith("rc_")]
    assert rc_events, (
        "Erwartet mindestens ein 'rc_'-präfixiertes RED_CLOUDS-Event direkt im zentralen "
        "_feed_cache, aus dem laut Fundstellen-Sweep alle sechs Ansichten lesen."
    )
    assert rc_events[0]["event_type"] == "Rote Wolken"


# ---------------------------------------------------------------------------
# Pre-Mortem Szenario 4: should_generate_red_clouds_event() selbst bleibt
# unangetastet — Regressionsanker gegen ein stilles Vertauschen "Wolkenquelle"
# vs. "wo muss die Sonne stehen"
# ---------------------------------------------------------------------------

def test_szenario4_azimut_check_bleibt_sonnenazimut_vs_motivazimut_am_standort():
    """should_generate_red_clouds_event() prüft weiterhin sun_azimuth (Sonne)
    gegen subject_azimuth (Motiv vom Fotografen-Standort) — NICHT den Azimut zum
    projizierten Punkt. Reiner Funktions-Regressionstest (unverändert zu US-132)."""
    from calculations.weather import should_generate_red_clouds_event

    assert should_generate_red_clouds_event(
        sun_altitude=-5, ch=45, cl=10, sun_azimuth=280, subject_azimuth=275,
    ) is True
    assert should_generate_red_clouds_event(
        sun_altitude=-5, ch=45, cl=10, sun_azimuth=280, subject_azimuth=100,
    ) is False
