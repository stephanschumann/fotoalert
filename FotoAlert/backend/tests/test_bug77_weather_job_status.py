"""BUG-77 — Live-Wetter-Abruf für Himmelsröte scheitert still (nur Warning-Log,
keine Sichtbarkeit).

Deckt Rule 1 (Teilausfall → Fehlerzustand + betroffene Locations im Text,
erfolgreiche Locations trotzdem aktualisiert), Rule 2 (Totalausfall →
Fehlerzustand), Rule 3 (Regression: alles ok → weiterhin "done") und
Rule 4 (Edge Case: keine Events in T+3 → weiterhin "done") ab.

Monkeypatch-Ansatz analog zu test_us106.py: fetch_weather_forecast wird durch
eine Fake-Funktion ersetzt, die für gezielt ausgewählte Locations eine
Exception wirft. Getestet wird ausschließlich die Steuerlogik in
_weather_overlay() (main.py) — kein echter Open-Meteo-Call.
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

import main
from calculations.weather import HourlyWeather, WeatherForecast

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ---------------------------------------------------------------------------
# Helfer (identisch zum Muster in test_us106.py)
# ---------------------------------------------------------------------------

def _hourly(t: datetime, cloud=10.0) -> HourlyWeather:
    return HourlyWeather(
        time=t, cloud_cover_pct=cloud, cloud_cover_low_pct=0.0,
        cloud_cover_mid_pct=0.0, cloud_cover_high_pct=20.0, visibility_m=20000.0,
        precipitation_mm=0.0, precipitation_prob_pct=0.0, wind_speed_kmh=5.0,
        wind_direction_deg=180.0, temperature_c=18.0, dew_point_c=8.0, weather_code=1,
    )


def _forecast(ref: datetime) -> WeatherForecast:
    hours = [_hourly(ref + timedelta(hours=i)) for i in range(-2, 72)]
    return WeatherForecast(location_lat=52.5, location_lon=13.4,
                           fetched_at=datetime.now(timezone.utc), hourly=hours)


def _event(loc_id: str, loc_name: str, shoot_offset_h: float, lat: float, lon: float) -> dict:
    shoot = datetime.now(timezone.utc) + timedelta(hours=shoot_offset_h)
    return {
        "location_id": loc_id, "location_name": loc_name,
        "observer_lat": lat, "observer_lon": lon,
        "shoot_time": shoot.isoformat(),
        "astronomy_score": 0.8, "overall_score": 0.8,
        "weather_score": 0.0, "weather_description": "",
    }


@pytest.fixture(autouse=True)
def _reset_state():
    """Globalen Zustand zwischen Tests sauber halten (Muster: test_us106.py)."""
    main._feed_cache = []
    main._job_status["weather"] = {
        "status": "idle", "last_run": None, "last_error": None, "duration_s": None,
    }
    yield
    main._feed_cache = []
    main._job_status["weather"] = {
        "status": "idle", "last_run": None, "last_error": None, "duration_s": None,
    }


def _run(coro):
    # Eigene Event-Loop pro Aufruf: robust, auch wenn ein vorheriger Test
    # (z.B. TestClient) die Default-Loop geschlossen hat.
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Rule 1 — Teilausfall → Fehlerzustand, betroffene Location im Text,
# erfolgreiche Location trotzdem aktualisiert
# ---------------------------------------------------------------------------

def test_partial_failure_sets_error_status_with_location_name(monkeypatch):
    ok_1  = _event("loc_ok1", "Alexanderplatz", 12, lat=52.5, lon=13.4)
    ok_2  = _event("loc_ok2", "Tempelhofer Feld", 12, lat=52.47, lon=13.4)
    bad   = _event("loc_bad", "Teufelsberg", 12, lat=52.5, lon=13.24)
    main._feed_cache = [ok_1, ok_2, bad]

    async def fake_fetch(lat, lon, days=7):
        if abs(lat - 52.5) < 0.001 and abs(lon - 13.24) < 0.001:
            raise RuntimeError("Open-Meteo down")
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_fetch)

    _run(main._weather_overlay())

    status = main._job_status["weather"]
    assert status["status"] == "error"
    assert "Teufelsberg" in status["last_error"]
    # Die erfolgreichen Locations wurden trotzdem ganz normal aktualisiert.
    assert ok_1["weather_status"] == "ok"
    assert ok_1["weather_score"] > 0
    assert ok_2["weather_status"] == "ok"
    assert ok_2["weather_score"] > 0
    # Die fehlgeschlagene Location bleibt ohne Wetter (kein "ok").
    assert bad.get("weather_status") != "ok"


def test_partial_failure_truncates_names_after_five(monkeypatch):
    events = []
    for i in range(7):
        lat = 50.0 + i  # jede Location bekommt eine eigene, eindeutige Koordinate
        events.append(_event(f"loc_{i}", f"Standort{i}", 12, lat=lat, lon=10.0))
    main._feed_cache = events

    async def failing_fetch(lat, lon, days=7):
        raise RuntimeError("Open-Meteo komplett down")
    monkeypatch.setattr(main, "fetch_weather_forecast", failing_fetch)

    _run(main._weather_overlay())

    status = main._job_status["weather"]
    assert status["status"] == "error"
    assert "…und 2 weitere" in status["last_error"]
    for i in range(5):
        assert f"Standort{i}" in status["last_error"]


# ---------------------------------------------------------------------------
# Rule 2 — Totalausfall → Fehlerzustand (kein Sonderfall ggü. Teilausfall)
# ---------------------------------------------------------------------------

def test_total_failure_sets_error_status(monkeypatch):
    ev_1 = _event("loc_1", "Standort A", 12, lat=52.5, lon=13.4)
    ev_2 = _event("loc_2", "Standort B", 12, lat=48.0, lon=11.0)
    main._feed_cache = [ev_1, ev_2]

    async def failing_fetch(lat, lon, days=7):
        raise RuntimeError("Open-Meteo down")
    monkeypatch.setattr(main, "fetch_weather_forecast", failing_fetch)

    _run(main._weather_overlay())

    status = main._job_status["weather"]
    assert status["status"] == "error"
    assert "Standort A" in status["last_error"]
    assert "Standort B" in status["last_error"]
    # Keine Location bekommt aktualisiertes Wetter.
    assert ev_1.get("weather_status") != "ok"
    assert ev_2.get("weather_status") != "ok"


# ---------------------------------------------------------------------------
# Rule 3 (Regression) — alles ok → weiterhin "done", kein Fehlertext
# ---------------------------------------------------------------------------

def test_all_success_keeps_done_status(monkeypatch):
    ev_1 = _event("loc_1", "Standort A", 12, lat=52.5, lon=13.4)
    ev_2 = _event("loc_2", "Standort B", 12, lat=48.0, lon=11.0)
    main._feed_cache = [ev_1, ev_2]

    async def fake_fetch(lat, lon, days=7):
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_fetch)

    _run(main._weather_overlay())

    status = main._job_status["weather"]
    assert status["status"] == "done"
    assert status["last_error"] is None
    assert ev_1["weather_status"] == "ok"
    assert ev_2["weather_status"] == "ok"


# ---------------------------------------------------------------------------
# Rule 4 (Edge Case, bereits bestehend) — keine Events in T+3 → weiterhin "done"
# ---------------------------------------------------------------------------

def test_no_near_events_keeps_done_status(monkeypatch):
    # Event weit in der Zukunft, außerhalb T+3 → near_events bleibt leer.
    far = _event("loc_far", "Weit weg", 24 * 10, lat=52.5, lon=13.4)
    main._feed_cache = [far]

    called = {"n": 0}

    async def fake_fetch(lat, lon, days=7):
        called["n"] += 1
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_fetch)

    _run(main._weather_overlay())

    status = main._job_status["weather"]
    assert status["status"] == "done"
    assert status["last_error"] is None
    assert called["n"] == 0  # kein Abruf nötig/versucht


def test_empty_feed_cache_keeps_done_status():
    main._feed_cache = []
    _run(main._weather_overlay())
    status = main._job_status["weather"]
    assert status["status"] == "done"
    assert status["last_error"] is None
