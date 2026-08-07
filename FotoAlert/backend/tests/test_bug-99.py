"""Regressionssuite — BUG-99: Server-Hänger durch Wetterdienst-Rate-Limit in der
täglichen Feed-Vorberechnung.

Analyse-Phase (fotoalert-analyze), 2026-08-03. Ticket: BUG-99.

⚠️ Wichtiger Hinweis zur Ticket-Prämisse (siehe Analyse-Abschnitt im Ticket in
BACKLOG.md, "Sonderfall: Ticket-Prämisse vs. Code"):

Code-Verifikation (main.py, precompute.py, calculations/weather.py, 2026-08-03) zeigt:
- `backend/precompute.py` selbst ruft NIE den Wetterdienst auf — Feed-Events bekommen dort
  nur den Platzhalter `weather_score: 0.0` ("wird zur Laufzeit durch Wetter-Overlay ersetzt").
- Der tatsächliche Wetter-Abruf läuft ausschließlich über `_weather_overlay()` /
  `_fetch_weather_and_aerosol()` / `_run_one_weather_fetch()` in `backend/main.py` — bereits
  gehärtet seit US-131/BUG-83 (asyncio.Semaphore, festes Pacing, Retry-mit-Backoff bei 429).
- Diese EINE Funktion wird identisch von ZWEI Aufrufern verwendet: dem periodischen 3h-Cron
  (`scheduler.add_job(_weather_overlay, "cron", ..., hour="*/3")`, main.py Z. 2177) UND vom
  Abschluss der täglichen/vollen Feed-Vorberechnung (`_run_precompute(mode="full"/"feed")`
  ruft am Ende `await _weather_overlay()` auf, main.py Z. 1644-1645) — es gibt KEINE separate,
  ungehärtete Kopie für den precompute-Pfad, wie die Ticket-Beschreibung unterstellt.
- `/refresh-calendar` (mode="calendar", das, was Stephan bei den zwei beobachteten Läufen
  tatsächlich ausgelöst hat) ruft `_weather_overlay()` GAR NICHT auf (main.py Z. 1644: nur
  `if mode in ("full", "feed")`).

Die im Ticket vermutete "fehlende Härtung im precompute-Pfad" ist damit nicht bestätigt —
diese Suite testet stattdessen die tatsächlich verifizierte Lücke (siehe Pre-Mortem Szenario 1
im Ticket): Der bereits gehärtete Mechanismus begrenzt zwar Nebenläufigkeit (Semaphore) und
Wiederholungen bei HTTP 429 (Retry-Cap), hat aber KEINE Obergrenze für die GESAMTdauer eines
Laufs. Antworten viele Locations dauerhaft nicht rechtzeitig (Timeout statt sauberem 429 —
plausibel genau dann, wenn ein Dienst bereits an seiner Kapazitätsgrenze arbeitet), wartet der
Lauf strikt sequenziell durch alle Semaphore-Runden, ohne Kurzschluss/Abbruch. Das ist der
Kandidat-Mechanismus für den beobachteten "Server-Hänger" (wahrscheinlich ausgelöst durch den
zeitgleich laufenden 3h-Cron-Job, nicht durch `/refresh-calendar` selbst — offene Frage 1 im
Ticket, noch nicht von Stephan bestätigt).
"""
import asyncio
import time
from datetime import datetime, timedelta, timezone

import httpx
import pytest

import main
from calculations.weather import HourlyWeather, WeatherForecast

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _make_near_events(n: int) -> list[dict]:
    """n eindeutige, minimal befüllte Feed-Events (unterschiedliche observer-Koordinaten,
    damit `_plan_weather_fetch_tasks()` sie NICHT dedupliziert). Event-Typ bewusst kein
    Goldene-Stunde-Typ, damit ausschließlich die einfache 'weather'-Abfrage geplant wird
    (kein zusätzlicher Cloud-Mood-/Aerosol-Task nötig, hält den Testaufbau einfach)."""
    events = []
    for i in range(n):
        events.append({
            "observer_lat": 52.0 + i * 0.01,
            "observer_lon": 13.0 + i * 0.01,
            "location_name": f"BUG-99-Test-Location-{i}",
            "event_type": "Sonnenaufgang",  # kein Eintrag in _GOLDEN_HOUR_TYPES
        })
    return events


def test_weather_overlay_run_has_no_overall_time_ceiling(monkeypatch):
    """
    BUG-99 AK1: Ein Wetter-Overlay-Lauf (identisch für 3h-Cron, täglichen
    Feed-Precompute-Abschluss UND Einzel-Location-Fast-Path, s. Docstring oben) muss
    innerhalb einer klar begrenzten Gesamtzeit fertig werden bzw. kontrolliert abbrechen,
    auch wenn der externe Wetterdienst für (fast) alle betroffenen Locations nicht
    rechtzeitig antwortet (simulierter Hänger/Timeout — nicht nur der bereits behandelte
    HTTP-429-Fall).

    Implementierungsphase (2026-08-04): Testet jetzt die ECHTE main.py-Implementierung
    (`_fetch_weather_and_aerosol(near_events, max_total_seconds=...)` mit
    `asyncio.wait_for()` um die Task-Liste + Cancel der noch offenen Tasks bei
    Zeitüberschreitung), nicht mehr nur die isolierte Spike-Simulation
    (test_bug99_spike.py, s. Aufräum-Hinweis dort). Da die reale Produktions-Obergrenze
    (`WEATHER_OVERLAY_MAX_TOTAL_SECONDS`, aktuell 180s nach der BUG-99-Korrektur, s.
    Docstring der Konstante) für einen schnellen Testlauf zu lang wäre, wird sie hier
    gezielt auf einen kleinen Testwert herabgesetzt (Monkeypatch
    der Modulkonstante — wirkt, weil `_fetch_weather_and_aerosol()` den Wert bei
    `max_total_seconds=None` zur AUFRUFZEIT aus der Modulkonstante liest, nicht als
    gebundenen Default-Parameterwert beim Funktionsdefinieren einfriert).

    Rot-Nachweis (Analyse-Phase, 2026-08-03, gegen unreparierten Code, s. auch
    BACKLOG.md BUG-99-Ticket „Testplan"):
        FAILED tests/test_bug-99.py::test_weather_overlay_run_has_no_overall_time_ceiling
        AssertionError: _fetch_weather_and_aerosol() lief 11.3s für 20 durchgehend nicht
        antwortende Locations — erwartet wird ein Abbruch/Kurzschluss spätestens nach
        ~3.0s, nicht ein Warten durch alle 5 Semaphore-Runden (rechnerisch 10.0s).
    Grün-Nachweis (Implementierungsphase, 2026-08-04): s. BACKLOG.md BUG-99-Ticket,
    Abschnitt „Implementierung" — realer pytest-Lauf gegen die reparierte main.py.
    """
    per_call_delay = 2.0
    n_locations = 20
    # BUG-99: klein genug, um den Kurzschluss-Mechanismus innerhalb des Tests sicher
    # auszulösen (deutlich kleiner als per_call_delay), aber groß genug über
    # WEATHER_API_REQUEST_PACING_SECONDS hinaus, um kein Testartefakt zu sein.
    test_ceiling_seconds = 1.0

    async def _slow_hanging_fetch(lat, lon, days=7):
        await asyncio.sleep(per_call_delay)
        raise httpx.TimeoutException("BUG-99 Testsimulation: Wetterdienst antwortet nicht rechtzeitig")

    async def _slow_hanging_aerosol(lat, lon, days=7):
        await asyncio.sleep(per_call_delay)
        raise httpx.TimeoutException("BUG-99 Testsimulation: Aerosol-Dienst antwortet nicht rechtzeitig")

    monkeypatch.setattr(main, "fetch_weather_forecast", _slow_hanging_fetch)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", _slow_hanging_aerosol)
    monkeypatch.setattr(main, "WEATHER_OVERLAY_MAX_TOTAL_SECONDS", test_ceiling_seconds)

    near_events = _make_near_events(n_locations)

    expected_batches = -(-n_locations // main.WEATHER_API_MAX_CONCURRENT_REQUESTS)  # ceil
    theoretical_min_duration = expected_batches * per_call_delay
    # Obergrenze, die der Kurzschluss-/Abbruch-Mechanismus einhalten muss: deutlich
    # kleiner als die ohne Obergrenze unvermeidbare sequenzielle Wartezeit durch alle
    # Runden, aber mit Puffer über test_ceiling_seconds für Cancel-/Scheduling-Overhead.
    acceptable_ceiling = test_ceiling_seconds + main.WEATHER_API_REQUEST_PACING_SECONDS + 1.0

    assert theoretical_min_duration > acceptable_ceiling, (
        "Testaufbau ungültig: gewählte Location-Zahl erzeugt keine Wartezeit über der "
        "geforderten Obergrenze — n_locations erhöhen."
    )

    t0 = time.monotonic()
    asyncio.run(main._fetch_weather_and_aerosol(near_events))
    elapsed = time.monotonic() - t0

    assert elapsed <= acceptable_ceiling, (
        f"_fetch_weather_and_aerosol() lief {elapsed:.1f}s für {n_locations} durchgehend "
        f"nicht antwortende Locations — erwartet wird ein Abbruch/Kurzschluss spätestens "
        f"nach ~{acceptable_ceiling:.1f}s, nicht ein Warten durch alle {expected_batches} "
        f"Semaphore-Runden (rechnerisch {theoretical_min_duration:.1f}s). Genau dieses "
        f"unbegrenzte Wachstum ist der in BUG-99 vermutete Mechanismus hinter dem "
        f"beobachteten Server-Hänger."
    )


def test_weather_overlay_ceiling_keeps_already_succeeded_results(monkeypatch):
    """
    BUG-99 AK2 (Rule 2, Weg-Gate-Entscheidung Stephan „Teilergebnis nutzen"): Wird die
    Gesamtzeit-Obergrenze erreicht, bleiben bereits erfolgreich abgerufene Locations
    erhalten (landen weiterhin in loc_forecasts) — nur die zum Abbruchzeitpunkt noch
    offenen Locations werden abgebrochen und laufen in denselben BUG-77-failed_*-
    Sammelpfad wie ein regulärer Fehlschlag. Kein Absturz, kein stiller Datenverlust der
    bereits erfolgreichen Ergebnisse.
    """
    fast_n = 3
    slow_n = 5
    ceiling = 1.0  # deutlich über WEATHER_API_REQUEST_PACING_SECONDS, deutlich unter dem 5s-Hang

    def _is_fast(lat: float) -> bool:
        # _make_near_events() vergibt observer_lat = 52.0 + i*0.01 für Location i —
        # die ersten `fast_n` Indizes sind hier bewusst als "schnell" markiert,
        # unabhängig von der tatsächlichen Bearbeitungsreihenfolge/Task-Scheduling.
        idx = round((lat - 52.0) / 0.01)
        return idx < fast_n

    async def _dispatch_weather(lat, lon, days=7):
        if _is_fast(lat):
            return {"ok": True, "lat": lat, "lon": lon}
        await asyncio.sleep(5.0)  # weit über `ceiling` — wird beim Erreichen abgebrochen
        return {"never": True}

    monkeypatch.setattr(main, "fetch_weather_forecast", _dispatch_weather)
    monkeypatch.setattr(main, "WEATHER_OVERLAY_MAX_TOTAL_SECONDS", ceiling)

    near_events = _make_near_events(fast_n + slow_n)

    t0 = time.monotonic()
    (
        loc_forecasts, _aerosol_forecasts, _sun_dir_forecasts, _antisolar_dir_forecasts,
        failed_locations, _failed_aerosol, _failed_sun_dir, _failed_antisolar_dir,
    ) = asyncio.run(main._fetch_weather_and_aerosol(near_events))
    elapsed = time.monotonic() - t0

    assert elapsed <= ceiling + main.WEATHER_API_REQUEST_PACING_SECONDS + 1.0, (
        f"Lauf mit Teilergebnis-Erhalt lief {elapsed:.1f}s trotz Obergrenze {ceiling:.1f}s "
        f"— die noch offenen (langsamen) Fetches wurden nicht rechtzeitig abgebrochen."
    )
    assert len(loc_forecasts) == fast_n, (
        f"Erwartet: {fast_n} bereits erfolgreich abgerufene Locations bleiben in "
        f"loc_forecasts erhalten, tatsächlich: {len(loc_forecasts)} "
        f"({list(loc_forecasts.keys())}). Ein verspäteter Abbruch darf bereits "
        f"erfolgreiche Ergebnisse nicht verwerfen (BUG-99 AK2)."
    )
    assert len(failed_locations) == slow_n, (
        f"Erwartet: {slow_n} noch offene (durch die Obergrenze abgebrochene) Locations "
        f"landen im BUG-77-failed_*-Sammelpfad, tatsächlich: {len(failed_locations)} "
        f"({failed_locations})."
    )


def test_weather_overlay_realistic_scale_error_free_run_stays_within_new_ceiling(monkeypatch):
    """
    BUG-99 Korrektur-Nachweis (2026-08-04, nach Verifikationsfund gegen die
    Implementierung): Eine Verifikation gegen `data_dev/fotoalert.db` (60 statische
    Locations + 259 `custom_locations` = 319, NICHT die eingefrorenen 9 aus der alten
    Prod-Kopie) hat gezeigt, dass die ursprüngliche `WEATHER_OVERLAY_MAX_TOTAL_SECONDS`
    von 60s bereits einen völlig FEHLERFREIEN Lauf bei der echten Location-Zahl
    fälschlich abgebrochen hätte (rechnerische Grundzeit ≈104s > 60s). Stephan hat
    daraufhin 180s (3 Min) bestätigt: ≈104s Grundzeit + ≈30s Retry-Puffer +
    ≈25% Sicherheitsmarge.

    Dieser Test bildet GENAU dieses Szenario nach: ein realistisch-großer (proportional
    zur echten Location-Zahl), komplett fehlerfreier Lauf (alle Fetches erfolgreich,
    kein einziger Timeout/429) darf nicht an der Obergrenze scheitern. Um die
    Testlaufzeit praktikabel zu halten, werden die Sekundenwerte um denselben Faktor
    `SCALE` gestaucht — dieselbe Technik wie in den obigen BUG-99-Tests (kleine, aber
    proportionale Zeitwerte statt echter Sekundenzahlen). Die Verhältnisse bleiben dabei
    exakt erhalten:
        reale Grundzeit ≈104s        -> gestaucht: 104s * SCALE
        alte (fehlerhafte) Obergrenze 60s -> 104s > 60s für JEDEN SCALE > 0
        neue, korrigierte Obergrenze 180s -> gestaucht: 180s * SCALE

    Rechnerischer Rot-Nachweis gegen den alten Wert (kein separater Testlauf nötig, da
    linear skaliert): 104s Grundzeit > 60s alte Obergrenze — ein völlig fehlerfreier Lauf
    bei n≈319 Locations wäre mit dem alten Wert IMMER abgebrochen worden, unabhängig vom
    gewählten SCALE. Grün-Nachweis: dieser Test läuft gegen die tatsächliche, korrigierte
    `main.WEATHER_OVERLAY_MAX_TOTAL_SECONDS` (180.0) — 104s < 180s, ausreichend Puffer.
    """
    SCALE = 0.02  # 104s -> ~2.1s Testlaufzeit, Proportion zu 60s/180s bleibt erhalten
    n_locations = 319  # reale Location-Zahl (60 statisch + 259 custom_locations, data_dev/fotoalert.db, 2026-08-04)
    real_baseline_seconds = 104.0  # verifizierte reale Grundzeit für einen fehlerfreien Lauf bei ~n_locations
    real_old_ceiling = 60.0
    real_new_ceiling = 180.0

    assert real_baseline_seconds > real_old_ceiling, (
        "Testannahme verletzt: die reale Grundzeit muesste ueber der alten (fehlerhaften) "
        "Obergrenze liegen, sonst waere der urspruengliche Verifikationsfund hinfaellig."
    )
    assert real_baseline_seconds < real_new_ceiling, (
        "Testannahme verletzt: die neue Obergrenze muesste ueber der realen Grundzeit "
        "liegen, sonst waere 180s falsch gewaehlt."
    )
    assert main.WEATHER_OVERLAY_MAX_TOTAL_SECONDS == real_new_ceiling, (
        f"main.WEATHER_OVERLAY_MAX_TOTAL_SECONDS ist {main.WEATHER_OVERLAY_MAX_TOTAL_SECONDS}, "
        f"erwartet der korrigierte BUG-99-Wert {real_new_ceiling} (180s)."
    )

    # Anzahl Semaphore-Runden bei realer Nebenläufigkeit (main.WEATHER_API_MAX_CONCURRENT_REQUESTS,
    # NICHT monkeypatched) — die gestauchte Grundzeit wird gleichmäßig auf die Runden verteilt,
    # damit die Gesamtzeit näherungsweise proportional mit der Location-Zahl mitwächst (wie im
    # real beobachteten Lauf).
    expected_batches = -(-n_locations // main.WEATHER_API_MAX_CONCURRENT_REQUESTS)  # ceil
    per_batch_delay = (real_baseline_seconds * SCALE) / expected_batches
    scaled_ceiling = real_new_ceiling * SCALE

    async def _fast_success_fetch(lat, lon, days=7):
        await asyncio.sleep(per_batch_delay)
        return _bug99_forecast()

    monkeypatch.setattr(main, "fetch_weather_forecast", _fast_success_fetch)
    # WEATHER_API_REQUEST_PACING_SECONDS ebenfalls mit SCALE stauchen: main._run_one_weather_fetch()
    # wartet nach JEDEM Fetch real diese Pause ab (finally-Block, unabhängig von Erfolg/Fehler,
    # nicht durch das obige Fetch-Mock abgedeckt). Ungestaucht wäre das bei 80 Semaphore-Runden
    # (ceil(319/4)) ein fixer, nicht mit SCALE schrumpfender Anteil von 80 * 0.35s ≈ 28s realer
    # Wartezeit, der jeden Lauf weit über die gestauchte 3.6s-Obergrenze treibt und praktisch
    # jede Location an der Zeit-Obergrenze abbrechen lässt — unabhängig von Maschine/CI-Auslastung
    # (asyncio.sleep ist wall-clock-basiert). Root-Cause-Fund 2026-08-07 nach rotem CI-Lauf
    # trotz lokal grünem Testlauf, siehe Ticket-Historie BUG-89/BUG-99.
    monkeypatch.setattr(main, "WEATHER_API_REQUEST_PACING_SECONDS", main.WEATHER_API_REQUEST_PACING_SECONDS * SCALE)
    # WEATHER_OVERLAY_MAX_TOTAL_SECONDS bewusst NICHT monkeypatched — dieser Test prüft den
    # echten Produktionswert (s. Assertion oben), übergibt aber max_total_seconds explizit
    # gestaucht (main._fetch_weather_and_aerosol() erlaubt das per Parameter, s. Docstring
    # dort), damit derselbe reale 104s-vs-180s-Puffer proportional in Testzeit abläuft, statt
    # den Test tatsächlich 180s lang laufen zu lassen.
    near_events = _make_near_events(n_locations)

    t0 = time.monotonic()
    (
        loc_forecasts, _aerosol_forecasts, _sun_dir_forecasts, _antisolar_dir_forecasts,
        failed_locations, _failed_aerosol, _failed_sun_dir, _failed_antisolar_dir,
    ) = asyncio.run(
        main._fetch_weather_and_aerosol(near_events, max_total_seconds=scaled_ceiling)
    )
    elapsed = time.monotonic() - t0

    assert elapsed <= scaled_ceiling + main.WEATHER_API_REQUEST_PACING_SECONDS + 1.0, (
        f"Realistisch-großer fehlerfreier Lauf ({n_locations} Locations) lief {elapsed:.1f}s "
        f"trotz proportional ausreichender Obergrenze {scaled_ceiling:.2f}s."
    )
    assert len(failed_locations) == 0, (
        f"Erwartet: bei einem komplett fehlerfreien Lauf über {n_locations} Locations werden "
        f"0 Locations abgebrochen, tatsächlich: {len(failed_locations)} ({failed_locations}). "
        f"Das ist exakt der BUG-99-Verifikationsfund: die alte 60s-Obergrenze hätte bei dieser "
        f"Location-Zahl bereits einen fehlerfreien Lauf fälschlich abgebrochen."
    )
    assert len(loc_forecasts) == n_locations, (
        f"Erwartet: alle {n_locations} Locations liefern ein Ergebnis, tatsächlich "
        f"{len(loc_forecasts)} ({sorted(loc_forecasts.keys())[:5]}...)."
    )


def test_refresh_calendar_mode_does_not_invoke_weather_overlay(monkeypatch):
    """
    BUG-99 Prämisse-Check (dokumentiert den Sonderfall aus dem Docstring oben als
    ausführbaren Beweis, kein reiner Prosa-Hinweis): `_run_precompute(mode="calendar")` —
    genau das, was `/refresh-calendar` auslöst und was Stephan bei den zwei beobachteten
    Läufen tatsächlich lief — ruft `_weather_overlay()` NICHT auf. Nur "full"/"feed" tun
    das (main.py Z. 1644). Dieser Test dokumentiert das aktuell korrekte, gewünschte
    Verhalten (sollte bereits GRÜN sein) — er dient als Regressionsschutz, damit eine
    künftige BUG-99-Reparatur diese Abgrenzung nicht versehentlich einreißt (z. B. indem
    "aus Vorsicht" jetzt auch der Kalenderpfad den Wetter-Overlay antriggert).
    """
    calls = {"weather_overlay": 0}

    async def _spy_weather_overlay():
        calls["weather_overlay"] += 1

    async def _fake_subprocess_exec(*args, **kwargs):
        class _FakeProc:
            returncode = 0
            async def communicate(self):
                return (b"", None)
        return _FakeProc()

    monkeypatch.setattr(main, "_weather_overlay", _spy_weather_overlay)
    monkeypatch.setattr(main.asyncio, "create_subprocess_exec", _fake_subprocess_exec)
    monkeypatch.setattr(main, "_load_elevation_cache", lambda: None)
    monkeypatch.setattr(main, "_load_caches", lambda: None)
    monkeypatch.setattr(main, "_drain_recompute_pending", lambda: asyncio.sleep(0))
    monkeypatch.setattr(main, "_precompute_running", False)

    asyncio.run(main._run_precompute(mode="calendar"))

    assert calls["weather_overlay"] == 0, (
        "_run_precompute(mode='calendar') hat _weather_overlay() aufgerufen — das würde "
        "die verifizierte Abgrenzung (Kalender-Refresh triggert keinen Wetter-Abruf) "
        "durchbrechen und die BUG-99-Ursachenanalyse (Prämisse-Korrektur) ungültig machen."
    )


def _bug99_forecast() -> WeatherForecast:
    ref = datetime.now(timezone.utc)
    hours = [
        HourlyWeather(
            time=ref + timedelta(hours=i), cloud_cover_pct=10.0, cloud_cover_low_pct=0.0,
            cloud_cover_mid_pct=0.0, cloud_cover_high_pct=20.0, visibility_m=20000.0,
            precipitation_mm=0.0, precipitation_prob_pct=0.0, wind_speed_kmh=5.0,
            wind_direction_deg=180.0, temperature_c=18.0, dew_point_c=8.0, weather_code=1,
        )
        for i in range(-2, 72)
    ]
    return WeatherForecast(location_lat=52.5, location_lon=13.4,
                            fetched_at=ref, hourly=hours)


def _bug99_event(loc_id: str, loc_name: str, lat: float, lon: float) -> dict:
    shoot = datetime.now(timezone.utc) + timedelta(hours=12)
    return {
        "location_id": loc_id, "location_name": loc_name,
        "observer_lat": lat, "observer_lon": lon,
        "shoot_time": shoot.isoformat(),
        "astronomy_score": 0.8, "overall_score": 0.8,
        "weather_score": 0.0, "weather_description": "",
        "event_type": "Sonnenaufgang",
    }


def test_weather_overlay_ceiling_partial_failure_visible_like_bug77(monkeypatch):
    """
    BUG-99 AK3 (bestehendes BUG-77-Muster wiederverwendet, nicht neu erfunden — Pre-Mortem
    Szenario 4): Ein durch die neue Gesamtzeit-Obergrenze abgebrochener Teil-Lauf muss
    denselben BUG-77-Sichtbarkeits-Mechanismus durchlaufen wie ein regulärer Fehlschlag —
    `main._job_status["weather"]["status"]` wird "error" mit der betroffenen Location im
    Text, während die bereits erfolgreiche Location weiterhin ganz normal ihren Wetterwert
    zeigt. End-to-End über main._weather_overlay() (nicht nur die tiefere
    _fetch_weather_and_aerosol()-Ebene), damit die tatsächliche Sichtbarkeits-Verkabelung
    mitgeprüft wird, nicht nur die Rückgabewerte der tieferen Funktion.
    """
    ok_event = _bug99_event("loc_ok", "Alexanderplatz", lat=52.5, lon=13.4)
    slow_event = _bug99_event("loc_slow", "Teufelsberg", lat=52.5, lon=13.24)
    main._feed_cache = [ok_event, slow_event]
    main._job_status["weather"] = {
        "status": "idle", "last_run": None, "last_error": None, "duration_s": None,
    }
    ceiling = 1.0  # deutlich über WEATHER_API_REQUEST_PACING_SECONDS, deutlich unter dem 5s-Hang

    async def _dispatch(lat, lon, days=7):
        if abs(lat - 52.5) < 0.001 and abs(lon - 13.4) < 0.001:
            return _bug99_forecast()
        await asyncio.sleep(5.0)  # weit über `ceiling` — wird beim Erreichen abgebrochen
        return _bug99_forecast()

    monkeypatch.setattr(main, "fetch_weather_forecast", _dispatch)
    monkeypatch.setattr(main, "WEATHER_OVERLAY_MAX_TOTAL_SECONDS", ceiling)

    try:
        asyncio.run(main._weather_overlay())

        status = main._job_status["weather"]
        assert status["status"] == "error", (
            f"Erwartet: Job-Status 'error' (BUG-77-Muster) nach einem durch die "
            f"Obergrenze abgebrochenen Teil-Lauf, tatsächlich: {status['status']!r}."
        )
        assert "Teufelsberg" in (status["last_error"] or ""), (
            f"Erwartet: die abgebrochene Location im Fehlertext (BUG-77-Muster), "
            f"tatsächlich: {status['last_error']!r}."
        )
        assert ok_event.get("weather_status") == "ok", (
            "Erwartet: die bereits erfolgreiche Location zeigt trotz Abbruch weiterhin "
            "ihren aktuellen Wetterwert (BUG-99 AK2/Rule 2)."
        )
        assert slow_event.get("weather_status") != "ok", (
            "Erwartet: die abgebrochene Location bleibt ohne 'ok'-Wetterstatus."
        )
    finally:
        main._feed_cache = []
        main._job_status["weather"] = {
            "status": "idle", "last_run": None, "last_error": None, "duration_s": None,
        }
