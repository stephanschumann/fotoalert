"""US-106 — Geänderte oder neue Location sofort komplett nutzbar.

Deckt die freigegebenen Optionen ab (Teil1=A gezieltes Wetter, Teil2=A
debounced Scout mit Single-Flight + Dirty, Teil3=A Pending-Queue mit Nachlauf
und Wetter-gekoppeltem Banner).

Die echten Netz-/Subprozess-Pfade sind gemockt; getestet wird die Steuerlogik
in main.py (kein Open-Meteo, kein precompute.py-Subprozess, keine Scout-Pipeline).
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

import main
from calculations.weather import HourlyWeather, WeatherForecast


# ---------------------------------------------------------------------------
# Helfer
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


def _event(loc_id: str, shoot_offset_h: float, lat=52.5, lon=13.4) -> dict:
    shoot = datetime.now(timezone.utc) + timedelta(hours=shoot_offset_h)
    return {
        "location_id": loc_id, "location_name": loc_id,
        "observer_lat": lat, "observer_lon": lon,
        "shoot_time": shoot.isoformat(),
        "astronomy_score": 0.8, "overall_score": 0.8,
        "weather_score": 0.0, "weather_description": "",
    }


@pytest.fixture(autouse=True)
def _reset_state():
    """Globalen Zustand zwischen Tests sauber halten."""
    main._feed_cache = []
    main._recompute_pending = set()
    main._precompute_running = False
    main._scout_running = False
    main._scout_dirty = False
    yield
    main._feed_cache = []
    main._recompute_pending = set()
    main._precompute_running = False


def _run(coro):
    # Eigene Event-Loop pro Aufruf: robust, auch wenn ein vorheriger Test (z.B.
    # TestClient) die Default-Loop geschlossen hat.
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# AK (c) — gezieltes Wetter setzt Score nur für DIE eine Location
# ---------------------------------------------------------------------------

def test_single_weather_overlay_only_target_location(monkeypatch):
    target = _event("loc_target", 12)   # in T+3
    other  = _event("loc_other", 12, lat=48.0, lon=11.0)
    main._feed_cache = [target, other]

    async def fake_fetch(lat, lon, days=7):
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_fetch)

    ready = _run(main._weather_overlay_single("loc_target"))

    assert ready is True
    assert target["weather_status"] == "ok"
    assert target["weather_score"] > 0
    # Andere Location wurde NICHT angefasst.
    assert other.get("weather_status") is None
    assert other["weather_score"] == 0.0


def test_single_weather_overlay_marks_far_future_as_none(monkeypatch):
    near = _event("loc_a", 12)          # in T+3
    far  = _event("loc_a", 24 * 5)      # > 3 Tage → kein Wetter
    main._feed_cache = [near, far]

    async def fake_fetch(lat, lon, days=7):
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_fetch)

    ready = _run(main._weather_overlay_single("loc_a"))

    assert ready is True
    assert near["weather_status"] == "ok"
    # Edge: weit in der Zukunft → "noch kein Wetter", nicht "lädt ewig".
    assert far["weather_status"] == "none"
    assert far["weather_score"] == 0.0


def test_single_weather_overlay_no_events_is_ready():
    main._feed_cache = [_event("other", 12)]
    ready = _run(main._weather_overlay_single("loc_without_events"))
    assert ready is True  # nichts nachzuladen → fertig


# ---------------------------------------------------------------------------
# AK (a)+(b) — Pending erst nach Wetter freigeben (lügendes Banner verhindern)
# ---------------------------------------------------------------------------

def test_pending_released_only_after_weather(monkeypatch):
    ev = _event("loc_x", 12)
    main._feed_cache = [ev]
    main._recompute_pending = {"loc_x"}

    async def fake_fetch(lat, lon, days=7):
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_fetch)

    # Simuliert das Ende von _recompute_one: erst Wetter, dann finalize.
    ready = _run(main._weather_overlay_single("loc_x"))
    assert ready is True
    assert "loc_x" in main._recompute_pending  # noch nicht freigegeben
    main._finalize_pending("loc_x")
    assert "loc_x" not in main._recompute_pending


def test_pending_stays_when_weather_fetch_fails(monkeypatch):
    ev = _event("loc_y", 12)
    main._feed_cache = [ev]
    main._recompute_pending = {"loc_y"}

    async def failing_fetch(lat, lon, days=7):
        raise RuntimeError("Open-Meteo down")
    monkeypatch.setattr(main, "fetch_weather_forecast", failing_fetch)

    ready = _run(main._weather_overlay_single("loc_y"))
    assert ready is False
    # Banner bleibt ehrlich sichtbar → Pending NICHT freigeben.
    assert "loc_y" in main._recompute_pending


# ---------------------------------------------------------------------------
# Nachbesserung — Reihenfolge: Feed+Wetter → Freigabe → DANACH Kalender
# (Banner darf NICHT auf den 365-Tage-Kalender warten)
# ---------------------------------------------------------------------------

def test_recompute_order_releases_pending_before_calendar(monkeypatch):
    """Belegt: nach Feed+Wetter ist die Location freigegeben (Banner weg),
    BEVOR der Kalender-Schritt läuft; der Kalender läuft danach."""
    ev = _event("loc_z", 12)
    main._feed_cache = [ev]
    main._recompute_pending = {"loc_z"}

    events = []  # zeichnet die Abfolge auf

    async def fake_subproc(loc_id, flag, tag):
        # Beim Kalender-Schritt prüfen, ob das Pending zu diesem Zeitpunkt schon
        # freigegeben war (= Banner schon weg, ohne auf den Kalender zu warten).
        events.append((flag, "pending" if loc_id in main._recompute_pending else "released"))
        return 0
    monkeypatch.setattr(main, "_run_precompute_single_subproc", fake_subproc)
    monkeypatch.setattr(main, "_load_elevation_cache", lambda: None)
    monkeypatch.setattr(main, "_load_caches", lambda: None)

    async def fake_fetch(lat, lon, days=7):
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_fetch)

    _run(main._recompute_one("loc_z"))

    # Erst Feed, dann Kalender:
    assert [f for f, _ in events] == ["--feed-only", "--calendar-only"]
    # Beim Feed-Schritt war noch pending, beim Kalender-Schritt bereits freigegeben:
    assert events[0] == ("--feed-only", "pending")
    assert events[1] == ("--calendar-only", "released")
    # Am Ende ist die Location nicht mehr pending.
    assert "loc_z" not in main._recompute_pending


def test_recompute_calendar_failure_keeps_release(monkeypatch):
    """Kalender-Fehler darf die bereits erfolgte Feed/Wetter-Freigabe NICHT
    zurücknehmen."""
    ev = _event("loc_q", 12)
    main._feed_cache = [ev]
    main._recompute_pending = {"loc_q"}

    async def fake_subproc(loc_id, flag, tag):
        return 0 if flag == "--feed-only" else 1  # Kalender schlägt fehl
    monkeypatch.setattr(main, "_run_precompute_single_subproc", fake_subproc)
    monkeypatch.setattr(main, "_load_elevation_cache", lambda: None)
    monkeypatch.setattr(main, "_load_caches", lambda: None)

    async def fake_fetch(lat, lon, days=7):
        return _forecast(datetime.now(timezone.utc))
    monkeypatch.setattr(main, "fetch_weather_forecast", fake_fetch)

    _run(main._recompute_one("loc_q"))

    # Feed+Wetter standen → freigegeben; Kalender-Fehler nimmt das NICHT zurück.
    assert "loc_q" not in main._recompute_pending


def test_recompute_weather_fail_keeps_pending_but_runs_calendar(monkeypatch):
    """Wetter-Fehler → Location bleibt pending (Banner ehrlich), Kalender wird
    trotzdem nachgezogen (er hängt nicht am Wetter)."""
    ev = _event("loc_w", 12)
    main._feed_cache = [ev]
    main._recompute_pending = {"loc_w"}

    flags = []

    async def fake_subproc(loc_id, flag, tag):
        flags.append(flag)
        return 0
    monkeypatch.setattr(main, "_run_precompute_single_subproc", fake_subproc)
    monkeypatch.setattr(main, "_load_elevation_cache", lambda: None)
    monkeypatch.setattr(main, "_load_caches", lambda: None)

    async def failing_fetch(lat, lon, days=7):
        raise RuntimeError("Open-Meteo down")
    monkeypatch.setattr(main, "fetch_weather_forecast", failing_fetch)

    _run(main._recompute_one("loc_w"))

    # Wetter fehlgeschlagen → bleibt pending; Kalender lief trotzdem.
    assert "loc_w" in main._recompute_pending
    assert flags == ["--feed-only", "--calendar-only"]


def test_recompute_feed_failure_drops_pending_and_skips_calendar(monkeypatch):
    """Feed-Fehler → kein Kalenderlauf, Pending wird verworfen (kein Banner-Hänger)."""
    ev = _event("loc_f", 12)
    main._feed_cache = [ev]
    main._recompute_pending = {"loc_f"}

    flags = []

    async def fake_subproc(loc_id, flag, tag):
        flags.append(flag)
        return 1 if flag == "--feed-only" else 0  # Feed schlägt fehl
    monkeypatch.setattr(main, "_run_precompute_single_subproc", fake_subproc)
    monkeypatch.setattr(main, "_load_elevation_cache", lambda: None)
    monkeypatch.setattr(main, "_load_caches", lambda: None)

    _run(main._recompute_one("loc_f"))

    assert flags == ["--feed-only"]            # Kalender NICHT gestartet
    assert "loc_f" not in main._recompute_pending


# ---------------------------------------------------------------------------
# AK (Edge/Teil3) — Skip während Großlauf wird nachgeholt (kein stiller Verlust)
# ---------------------------------------------------------------------------

def test_single_recompute_deferred_during_running_job(monkeypatch):
    # _NO_BACKGROUND ist im Test-Harness gesetzt; die Defer-Logik greift nur in
    # Produktion → für diesen Test deaktivieren.
    monkeypatch.setattr(main, "_NO_BACKGROUND", False)
    main._precompute_running = True   # Großlauf läuft
    _run(main._run_precompute_single("loc_deferred"))
    # Nicht verworfen — bleibt pending für den Nachlauf am Lauf-Ende.
    assert "loc_deferred" in main._recompute_pending
    assert main._precompute_running is True  # Großlauf weiterhin unangetastet


def test_drain_processes_pending_sequentially(monkeypatch):
    main._recompute_pending = {"loc_1", "loc_2"}
    processed = []

    async def fake_recompute_one(loc_id):
        processed.append(loc_id)
        main._recompute_pending.discard(loc_id)
    monkeypatch.setattr(main, "_recompute_one", fake_recompute_one)
    # Drain ruft _run_precompute_single(_allow_drain=False) → das ruft _recompute_one.
    # _NO_BACKGROUND ist im Test gesetzt → wir umgehen den Guard, indem wir direkt drainen.
    monkeypatch.setattr(main, "_NO_BACKGROUND", False)

    _run(main._drain_recompute_pending())

    assert set(processed) == {"loc_1", "loc_2"}
    assert main._recompute_pending == set()


# ---------------------------------------------------------------------------
# AK (d) — Scout: Single-Flight (kein Doppellauf) + Dirty-Nachlauf
# ---------------------------------------------------------------------------

def test_scout_single_flight_no_parallel_run(monkeypatch):
    calls = {"n": 0}

    async def fake_refresh(cache_path):
        calls["n"] += 1
        await asyncio.sleep(0.05)   # Lauf dauert ein bisschen

    import discover.pipeline as pipeline
    monkeypatch.setattr(pipeline, "refresh_discover_cache", fake_refresh)
    monkeypatch.setattr(main, "_load_discover_cache", lambda: None)

    async def scenario():
        # Zwei gleichzeitige Trigger → nur EIN Lauf, der zweite setzt nur dirty.
        t1 = asyncio.create_task(main._refresh_discover())
        await asyncio.sleep(0)        # t1 startet, _scout_running=True
        await main._refresh_discover() # zweiter Aufruf während t1 läuft
        await t1

    _run(scenario())
    # Single-Flight: der zweite parallele Aufruf hat KEINEN zweiten Lauf gestartet,
    # aber dirty gesetzt → genau ein Nachlauf. Insgesamt 2 Läufe (Original + 1 Nachlauf),
    # nie zwei parallel.
    assert calls["n"] == 2
    assert main._scout_running is False


def test_scout_dirty_triggers_exactly_one_followup(monkeypatch):
    calls = {"n": 0}

    async def fake_refresh(cache_path):
        calls["n"] += 1
        # Während des ersten Laufs einmal dirty markieren.
        if calls["n"] == 1:
            main._scout_dirty = True
        await asyncio.sleep(0)

    import discover.pipeline as pipeline
    monkeypatch.setattr(pipeline, "refresh_discover_cache", fake_refresh)
    monkeypatch.setattr(main, "_load_discover_cache", lambda: None)

    _run(main._refresh_discover())
    # Erster Lauf + genau ein Nachlauf wegen dirty = 2; danach kein weiterer.
    assert calls["n"] == 2
    assert main._scout_dirty is False
    assert main._scout_running is False
