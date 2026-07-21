"""
BUG-83: Wolkenwert-Abruf (Sonnenrichtung/Gegenrichtung) schlug beim manuellen
Wetter-Update für einen Großteil aller Locations mit HTTP 429 (Too Many
Requests) fehl, weil diese beiden Abruf-Arten pro Location bis zu 6x häufiger
entstehen als der normale Wetter-Abruf und sich über den gesamten Lauf
verteilen (siehe BACKLOG.md BUG-83, Code-Verifikation) — derselbe Drosselungs-
Mechanismus wie TASK-75, hier nur granularer sichtbar.

Weg-Gate-Entscheidung (Stephan, 2026-07-21): Option A (Drosselung neu
kalibrieren: WEATHER_API_MAX_CONCURRENT_REQUESTS 5→4,
WEATHER_API_REQUEST_PACING_SECONDS 0.15→0.25) ergänzt um Option B (Retry mit
steigender Wartezeit bei HTTP 429 in _run_one_weather_fetch(), einheitlich für
ALLE Abruf-Arten — Pre-Mortem Szenario 3: keine zwei unterschiedlich robusten
Pfade in derselben Funktion). Kein zusätzlicher gezielter Nach-Versuch nur für
zuvor fehlgeschlagene Locations (Pre-Mortem Szenario 5, Option A gewählt) — der
reguläre 3h-Cronlauf holt das nach.

Abgedeckte Akzeptanzkriterien (siehe BACKLOG.md BUG-83):
  - Option-A-Parameter sind auf die neu gewählten, konservativeren Werte
    gesetzt (Regressionsanker gegen versehentliches Zurücksetzen).
  - Ein einzelner HTTP 429 wird automatisch mit steigender Wartezeit wiederholt
    (1-2x), bevor der Task endgültig fehlschlägt — einheitlich für
    weather/aerosol/sun_dir/antisolar_dir.
  - Andere Fehler (Timeout, sonstiger HTTP-Status, generische Exception)
    werden NICHT wiederholt — keine Regression zum bestehenden
    BUG-77-Sichtbarkeits-Mechanismus (sofortiger, sichtbarer Fehlschlag).
  - Ein dauerhafter 429 (Retries ausgeschöpft) bleibt weiterhin ein sichtbarer,
    verständlicher Fehler im Job-Status (BUG-77-Regression).
  - Die allgemeinen Wetterwerte am Fotografen-Standort sind durch die Änderung
    unverändert korrekt (kein Seiteneffekt der Retry-/Kalibrierungsänderung).
"""
import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import pytest

import main
from calculations.weather import HourlyWeather, WeatherForecast, HourlyAerosol, AerosolForecast

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ---------------------------------------------------------------------------
# Helfer (bewusst self-contained pro Pattern 12 — keine geteilten Fixtures/IDs
# mit anderen Testdateien wie test_us131.py, auch wenn die Muster ähnlich sind)
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


def _http_error(status_code: int) -> httpx.HTTPStatusError:
    """Baut einen echten httpx.HTTPStatusError (kein Mock-Ersatz), damit die
    Retry-Logik in main._run_one_weather_fetch() denselben Exception-Typ sieht
    wie response.raise_for_status() ihn in calculations/weather.py wirft."""
    request = httpx.Request("GET", "https://api.open-meteo.com/v1/forecast")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError(f"HTTP {status_code}", request=request, response=response)


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
# Option A: neu justierte Drossel-Parameter (Regressionsanker)
# ---------------------------------------------------------------------------

def test_option_a_max_concurrent_requests_auf_4_gesenkt():
    """5 -> 4: eine Stufe konservativer als die TASK-75-Kombination, die bei der
    aggregierten Messung 4,8% ergab, aber laut BUG-83-Analyse für
    Sonnenrichtung/Gegenrichtung trotzdem >95% Fehlschläge produzierte."""
    assert main.WEATHER_API_MAX_CONCURRENT_REQUESTS == 4


def test_option_a_pacing_auf_0_25_angehoben():
    """0.15s -> 0.25s: senkt den gedeckelten Maximaldurchsatz von ca. 33,3 auf
    ca. 16 Requests/Sekunde (siehe main.py-Docstring für die Herleitung)."""
    assert main.WEATHER_API_REQUEST_PACING_SECONDS == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# Option B: Retry-Konstanten (Regressionsanker)
# ---------------------------------------------------------------------------

def test_option_b_max_retries_ist_2():
    assert main.WEATHER_API_MAX_RETRIES_ON_429 == 2


def test_option_b_backoff_basis_ist_1_sekunde():
    assert main.WEATHER_API_RETRY_BACKOFF_BASE_SECONDS == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Retry-Mechanismus: unmittelbar an _run_one_weather_fetch() geprüft (isolierter
# Aufruf mit echtem asyncio.Semaphore, kein Netzwerk -- fetch_weather_forecast
# ist gemockt)
# ---------------------------------------------------------------------------

def test_retry_bei_429_erfolgreich_nach_einem_versuch(monkeypatch):
    calls = {"n": 0}

    async def flaky(lat, lon, days=7):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _http_error(429)
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", flaky)

    sem = asyncio.Semaphore(1)
    result = _run(main._run_one_weather_fetch("weather", 52.5, 13.4, sem))

    assert calls["n"] == 2, "Erster Versuch 429, zweiter Versuch (Retry) erfolgreich -- genau 2 Calls erwartet"
    assert isinstance(result, WeatherForecast)


def test_retry_bei_429_erfolgreich_erst_nach_beiden_versuchen(monkeypatch):
    calls = {"n": 0}

    async def flaky(lat, lon, days=7):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise _http_error(429)
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", flaky)

    sem = asyncio.Semaphore(1)
    result = _run(main._run_one_weather_fetch("weather", 52.5, 13.4, sem))

    assert calls["n"] == 3, "Initialer Call + 2 Retries = 3 Calls, dritter erfolgreich"
    assert isinstance(result, WeatherForecast)


def test_retry_gibt_nach_ausgeschoepften_versuchen_endgueltig_auf(monkeypatch):
    calls = {"n": 0}

    async def always_429(lat, lon, days=7):
        calls["n"] += 1
        raise _http_error(429)
    monkeypatch.setattr(main, "fetch_weather_forecast", always_429)

    sem = asyncio.Semaphore(1)
    with pytest.raises(httpx.HTTPStatusError):
        _run(main._run_one_weather_fetch("weather", 52.5, 13.4, sem))

    assert calls["n"] == 1 + main.WEATHER_API_MAX_RETRIES_ON_429, (
        "Bei dauerhaftem 429 muessen genau initial+2 Retries versucht werden, "
        "dann endgueltig fehlschlagen"
    )


def test_kein_retry_bei_generischer_exception_bug77_regression(monkeypatch):
    """Regression: ein Timeout/eine generische Exception (kein 429) darf NICHT
    wiederholt werden -- sofortiger, sichtbarer Fehlschlag bleibt wie vor
    BUG-83 (BUG-77-Sichtbarkeits-Mechanismus)."""
    calls = {"n": 0}

    async def failing(lat, lon, days=7):
        calls["n"] += 1
        raise RuntimeError("Timeout o.ae. (kein 429)")
    monkeypatch.setattr(main, "fetch_weather_forecast", failing)

    sem = asyncio.Semaphore(1)
    with pytest.raises(RuntimeError):
        _run(main._run_one_weather_fetch("weather", 52.5, 13.4, sem))

    assert calls["n"] == 1, "Kein Retry bei generischer Exception -- genau 1 Call"


def test_kein_retry_bei_anderem_http_status(monkeypatch):
    """Regression: ein HTTP-Fehler ungleich 429 (z.B. 500) wird ebenfalls NICHT
    wiederholt -- die Retry-Logik ist gezielt auf 429 beschraenkt."""
    calls = {"n": 0}

    async def failing(lat, lon, days=7):
        calls["n"] += 1
        raise _http_error(500)
    monkeypatch.setattr(main, "fetch_weather_forecast", failing)

    sem = asyncio.Semaphore(1)
    with pytest.raises(httpx.HTTPStatusError):
        _run(main._run_one_weather_fetch("weather", 52.5, 13.4, sem))

    assert calls["n"] == 1, "Kein Retry bei HTTP 500 -- genau 1 Call"


def test_retry_gilt_auch_fuer_aerosol_kind(monkeypatch):
    """Pre-Mortem Szenario 3: derselbe Retry-Mechanismus muss auch fuer
    kind='aerosol' greifen, nicht nur fuer 'weather' -- alle Abruf-Arten teilen
    sich denselben Helfer."""
    calls = {"n": 0}

    async def flaky_aerosol(lat, lon, days=7):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _http_error(429)
        return _aerosol_forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_aerosol_forecast", flaky_aerosol)

    sem = asyncio.Semaphore(1)
    result = _run(main._run_one_weather_fetch("aerosol", 52.5, 13.4, sem))

    assert calls["n"] == 2
    assert isinstance(result, AerosolForecast)


def test_backoff_wartezeit_steigt_und_pacing_folgt_am_ende(monkeypatch):
    """Statt echter Wanduhrzeit (flaky in CI, analog US-131-2.-Nachtrag-Muster):
    main.asyncio.sleep patchen und pruefen, dass die Backoff-Wartezeit pro
    Retry steigt (1x, dann 2x Basiswert) und danach GENAU EINMAL das normale
    Pacing folgt -- nicht mehrfach, weil der finally-Block ausserhalb der
    Retry-Schleife liegt."""
    calls = {"n": 0}

    async def flaky(lat, lon, days=7):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise _http_error(429)
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", flaky)

    sleep_calls = []

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)
    monkeypatch.setattr(main.asyncio, "sleep", fake_sleep)

    sem = asyncio.Semaphore(1)
    _run(main._run_one_weather_fetch("weather", 52.5, 13.4, sem))

    assert sleep_calls == [
        main.WEATHER_API_RETRY_BACKOFF_BASE_SECONDS * 1,
        main.WEATHER_API_RETRY_BACKOFF_BASE_SECONDS * 2,
        main.WEATHER_API_REQUEST_PACING_SECONDS,
    ], f"Erwartete steigende Backoff-Zeiten gefolgt von genau einem Pacing-Sleep, bekam: {sleep_calls}"


def test_pacing_laeuft_auch_wenn_retries_endgueltig_scheitern(monkeypatch):
    """Der bestehende US-131-Pacing-Vertrag (finally läuft IMMER) muss auch bei
    endgueltig ausgeschoepften Retries erhalten bleiben."""
    async def always_429(lat, lon, days=7):
        raise _http_error(429)
    monkeypatch.setattr(main, "fetch_weather_forecast", always_429)

    sleep_calls = []

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)
    monkeypatch.setattr(main.asyncio, "sleep", fake_sleep)

    sem = asyncio.Semaphore(1)
    with pytest.raises(httpx.HTTPStatusError):
        _run(main._run_one_weather_fetch("weather", 52.5, 13.4, sem))

    assert sleep_calls[-1] == main.WEATHER_API_REQUEST_PACING_SECONDS, (
        "Pacing-Sleep muss auch nach endgueltig ausgeschoepften Retries als "
        "letzter Sleep-Aufruf erfolgen (finally-Block, US-131-Vertrag)"
    )


# ---------------------------------------------------------------------------
# End-to-End über _weather_overlay(): Sonnenrichtung/Gegenrichtung erholen
# sich von einem transienten 429 (das eigentliche BUG-83-Symptom)
# ---------------------------------------------------------------------------

def test_sonnenrichtung_und_gegenrichtung_erholen_sich_von_transientem_429(monkeypatch):
    """Kernszenario BUG-83: Sonnenrichtung- und Gegenrichtung-Abruf schlagen
    beim ERSTEN Versuch mit 429 fehl (wie im Live-Betrieb beobachtet), erholen
    sich aber dank Retry -- das Event bekommt trotzdem gueltige Wolkenwerte
    statt 'Signal nicht verfuegbar'."""
    ev = _golden_event(loc_id="loc_bug83_retry", subject_azimuth=98)
    main._feed_cache = [ev]
    (sun_lat, sun_lon), (anti_lat, anti_lon) = main._cloud_mood_projection_points(ev)

    failed_once = {"sun": False, "anti": False}

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, sun_lat, sun_lon) and not failed_once["sun"]:
            failed_once["sun"] = True
            raise _http_error(429)
        if _match(lat, lon, anti_lat, anti_lon) and not failed_once["anti"]:
            failed_once["anti"] = True
            raise _http_error(429)
        return _forecast(datetime.now(timezone.utc), cl=25, cm=45, ch=35)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.05)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())

    assert failed_once["sun"] is True and failed_once["anti"] is True, "Testaufbau ungueltig: 429 wurde nie ausgeloest"
    assert ev["golden_cloud_score_sun_dir"] is not None, "Sonnenrichtung sollte sich dank Retry erholen"
    assert ev["golden_cloud_score_antisolar_dir"] is not None, "Gegenrichtung sollte sich dank Retry erholen"
    assert main._job_status["weather"]["status"] == "done", "Kein sichtbarer Fehler mehr, da Retry gegriffen hat"


def test_dauerhafter_429_bleibt_sichtbarer_fehler_bug77_regression(monkeypatch):
    """Regression: schlägt der 429 auch nach ausgeschoepften Retries dauerhaft
    fehl, bleibt das bestehende BUG-77-Sichtbarkeits-Verhalten unveraendert --
    verstaendliche Fehlermeldung im Job-Status, kein stiller Fehlschlag."""
    ev = _golden_event(loc_id="loc_bug83_persistent429", subject_azimuth=265)
    main._feed_cache = [ev]
    (sun_lat, sun_lon), (_anti_lat, _anti_lon) = main._cloud_mood_projection_points(ev)

    async def fake_weather(lat, lon, days=7):
        if _match(lat, lon, sun_lat, sun_lon):
            raise _http_error(429)
        return _forecast(datetime.now(timezone.utc), cl=10, cm=50, ch=20)
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_weather)

    async def fake_aerosol(lat, lon, days=7):
        return _aerosol_forecast(datetime.now(timezone.utc), aod=0.05)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", fake_aerosol)

    _run(main._weather_overlay())  # darf nicht crashen

    assert ev["golden_cloud_score_sun_dir"] is None
    status = main._job_status["weather"]
    assert status["status"] == "error"
    assert "Wolkenwert Sonnenrichtung fehlgeschlagen für" in status["last_error"]
    assert ev["location_name"] in status["last_error"]


def test_allgemeine_wetteranzeige_am_fotografen_standort_unveraendert(monkeypatch):
    """Regression (AK): die allgemeinen Wetterwerte am Fotografen-Standort
    bleiben durch Kalibrierung + Retry unveraendert korrekt -- kein
    Seiteneffekt der BUG-83-Aenderung auf den unauffaellig laufenden
    Wetter-Abruf-Pfad."""
    ev = _golden_event(loc_id="loc_bug83_general_weather")
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
    assert main._job_status["weather"]["status"] == "done"
