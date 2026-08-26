"""Regressionssuite — BUG-106: Wetter-Overlay-Job kollidiert beim Server-Start mit dem
Wetter-Karten-Bau-Job um Ressourcen und stößt dadurch eher an das bestehende
Zeitbudget-Sicherheitsnetz (WEATHER_OVERLAY_MAX_TOTAL_SECONDS, urspruenglich 180s
durch BUG-99, Wert seit BUG-108 = 1500.0s).

Implementierungsphase, 2026-08-16. Ticket: BUG-106.

Wichtiger Hinweis zur Ticket-Prämisse (siehe Analyse-Abschnitt im Ticket in
BACKLOG.md, "Code-Verifikation"): Die ursprünglich im Ticket vermutete Ursache
("kalter In-Memory-Cache nach Neustart", `PROJECTED_POINT_CACHE_PRECISION`) wurde
per Code-Lesung widerlegt — es gibt keinen persistenten Cache zwischen zwei
Wetter-Overlay-Läufen, jene Konstante ist nur eine Rundungskonstante innerhalb
EINES Laufs. Die tatsächlich verifizierte Ursache ist Ressourcen-Konkurrenz
zwischen den beiden beim Server-Start gleichzeitig gefeuerten Hintergrund-Tasks
`_weather_overlay()` und `_build_weather_map()` — im 3h-Cron ist dafür bewusst ein
20-Minuten-Abstand eingebaut (minute=0 vs. minute=20), der beim Start bisher fehlte.

Diese Suite testet die Option-B-Implementierung: eine kurze Verzögerung des
Karten-Bau-Starts beim Server-Start (Regel 1 im Ticket) sowie eine unterscheidbare
Log-Zeile für start- vs. cron-ausgelöste Wetter-Overlay-Läufe (AK4).
"""
import asyncio
import logging

import pytest

import main

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ---------------------------------------------------------------------------
# AK1 / Regel 1 — Start-Lauf und Karten-Bau starten beim Server-Start nicht mehr
# zeitgleich, sondern mit einer kurzen Verzögerung dazwischen.
# ---------------------------------------------------------------------------

def test_delayed_build_weather_map_sleeps_before_building(monkeypatch):
    """BUG-106 AK1: `_delayed_build_weather_map()` (der beim Start statt eines
    direkten `_build_weather_map()`-Tasks verwendete Wrapper) muss ERST die
    konfigurierte Verzögerung abwarten und darf `_build_weather_map()` selbst
    danach aufrufen — nicht umgekehrt und nicht gleichzeitig.
    """
    call_order = []

    async def _fake_sleep(seconds):
        call_order.append(("sleep", seconds))

    async def _fake_build_weather_map():
        call_order.append(("build", None))

    monkeypatch.setattr(main.asyncio, "sleep", _fake_sleep)
    monkeypatch.setattr(main, "_build_weather_map", _fake_build_weather_map)

    asyncio.run(main._delayed_build_weather_map())

    assert call_order == [
        ("sleep", main._STARTUP_WEATHER_MAP_DELAY_S),
        ("build", None),
    ], (
        f"Erwartet: erst asyncio.sleep({main._STARTUP_WEATHER_MAP_DELAY_S}), dann "
        f"_build_weather_map() — tatsächliche Reihenfolge: {call_order}. Ohne diese "
        f"Verzögerung starten Wetter-Overlay und Karten-Bau beim Server-Start wieder "
        f"zeitgleich (BUG-106-Kernursache: Ressourcen-Konkurrenz)."
    )


def test_startup_weather_map_delay_is_short_but_positive():
    """BUG-106 Pre-Mortem: Die Verzögerung muss > 0s sein (sonst kein Fix), aber
    "deutlich unter einer Minute" bleiben (Pre-Mortem-Gegenmaßnahme — die Wetter-
    Karte darf nach einem Neustart nicht unnötig lange "noch nicht bereit" zeigen)
    und ausdrücklich NICHT den vollen 20-Minuten-Cron-Abstand kopieren (der ist nur
    für den eingeschwungenen 3h-Rhythmus begründet, nicht für den Start-Pfad)."""
    assert main._STARTUP_WEATHER_MAP_DELAY_S > 0, (
        "Verzögerung muss positiv sein, sonst starten beide Jobs weiterhin zeitgleich."
    )
    assert main._STARTUP_WEATHER_MAP_DELAY_S < 60, (
        f"Verzögerung ({main._STARTUP_WEATHER_MAP_DELAY_S}s) sollte deutlich unter "
        f"einer Minute bleiben (Pre-Mortem-Gegenmaßnahme gegen eine spürbar länger "
        f"'noch nicht bereit' wirkende Wetter-Karte nach Neustart)."
    )


def test_startup_uses_delayed_wrapper_not_direct_build_weather_map_task():
    """BUG-106 Regel 1 (strukturell): `startup()` darf `_build_weather_map()` nicht
    mehr direkt als eigenen Task feuern, sondern nur noch über den verzögernden
    Wrapper `_delayed_build_weather_map()` — sonst wäre die Entkopplung nur auf dem
    Papier vorhanden. Quelltext-Prüfung statt Ausführung, weil `startup()` selbst
    (App-Lifecycle-Hook, `_NO_BACKGROUND`-Kurzschluss in Tests) hier bewusst nicht
    direkt ausgeführt wird.
    """
    import inspect
    src = inspect.getsource(main.startup)
    assert "_delayed_build_weather_map()" in src, (
        "startup() muss _build_weather_map() über den verzögernden Wrapper "
        "_delayed_build_weather_map() starten, nicht direkt."
    )
    assert "asyncio.create_task(_build_weather_map())" not in src, (
        "startup() feuert _build_weather_map() weiterhin direkt/unverzögert — "
        "die BUG-106-Entkopplung wäre damit wirkungslos."
    )


# ---------------------------------------------------------------------------
# AK5 / Regression — der bestehende 20-Minuten-Abstand im 3h-Cron bleibt
# unverändert bestehen; nur der Start-Pfad wird angepasst.
# ---------------------------------------------------------------------------

def test_cron_schedule_keeps_existing_20_minute_gap(monkeypatch):
    """BUG-106 AK5 (Regression): `_startup_setup_scheduler()` muss weiterhin
    `_weather_overlay` auf Minute 0 und `_build_weather_map` auf Minute 20 jeder
    3-Stunden-Periode legen — exakt das bereits bestehende, bewusst gewählte
    Muster, an dem dieses Ticket nichts ändern soll (Scope: nur der Start-Pfad).
    """
    added_jobs = []

    class _FakeScheduler:
        def add_job(self, func, trigger, **kwargs):
            added_jobs.append((getattr(func, "__name__", func), trigger, kwargs))

        def start(self):
            pass

    monkeypatch.setattr(main, "scheduler", _FakeScheduler())

    main._startup_setup_scheduler("full")

    weather_jobs = [j for j in added_jobs if j[0] == "_weather_overlay"]
    map_jobs = [j for j in added_jobs if j[0] == "_build_weather_map"]

    assert len(weather_jobs) == 1, f"Erwartet genau einen _weather_overlay-Cron-Job, gefunden: {weather_jobs}"
    assert len(map_jobs) == 1, f"Erwartet genau einen _build_weather_map-Cron-Job, gefunden: {map_jobs}"

    _, w_trigger, w_kwargs = weather_jobs[0]
    _, m_trigger, m_kwargs = map_jobs[0]

    assert w_trigger == "cron" and w_kwargs.get("hour") == "*/3" and w_kwargs.get("minute") == 0, (
        f"_weather_overlay-Cron-Job veraendert: trigger={w_trigger!r}, kwargs={w_kwargs} "
        f"— erwartet minute=0, hour='*/3' (unveraendert seit BUG-99/US-112)."
    )
    assert m_trigger == "cron" and m_kwargs.get("hour") == "*/3" and m_kwargs.get("minute") == 20, (
        f"_build_weather_map-Cron-Job veraendert: trigger={m_trigger!r}, kwargs={m_kwargs} "
        f"— erwartet minute=20, hour='*/3' (bestehender 20-Minuten-Abstand, unveraendert)."
    )


# ---------------------------------------------------------------------------
# AK4 — ein durch einen Neustart ausgelöster Wetter-Lauf ist im Server-Log als
# solcher erkennbar (Verwechslungsschutz mit einem echten API-Ausfall).
# ---------------------------------------------------------------------------

def test_weather_overlay_logs_startup_trigger(caplog):
    """BUG-106 AK4: Ein mit triggered_by="startup" gestarteter Wetter-Overlay-Lauf
    erzeugt eine Log-Zeile, die ihn eindeutig als Start-ausgelöst kennzeichnet."""
    main._feed_cache = []  # schneller Rückkehrpfad, Log-Zeile steht davor
    try:
        with caplog.at_level(logging.INFO, logger="main"):
            asyncio.run(main._weather_overlay(triggered_by="startup"))
    finally:
        main._feed_cache = []

    matches = [r for r in caplog.records if "startup" in r.message and "Auslöser" in r.message]
    assert matches, (
        f"Erwartet eine Log-Zeile, die den Lauf als 'startup'-ausgelöst kennzeichnet "
        f"(AK4), tatsächliche INFO-Logs: {[r.message for r in caplog.records]}"
    )


def test_weather_overlay_logs_cron_trigger_by_default(caplog):
    """BUG-106 AK4 (Gegenprobe): Ohne explizites triggered_by (wie vom bestehenden
    3h-Cron-Job aufgerufen) bleibt die Log-Zeile auf den bisherigen/Default-Wert
    "cron" — ein Start-ausgelöster Abbruch darf nicht mit einem regulären
    Cron-Lauf verwechselbar aussehen, und umgekehrt darf der Default-Fall nicht
    fälschlich als "startup" geloggt werden."""
    main._feed_cache = []
    try:
        with caplog.at_level(logging.INFO, logger="main"):
            asyncio.run(main._weather_overlay())  # kein triggered_by -> Default
    finally:
        main._feed_cache = []

    matches = [r for r in caplog.records if "Auslöser" in r.message]
    assert matches, f"Erwartet eine Auslöser-Log-Zeile, tatsächliche INFO-Logs: {[r.message for r in caplog.records]}"
    assert all("startup" not in r.message for r in matches), (
        f"Ein Cron-/Default-Lauf darf nicht als 'startup' geloggt werden: {[r.message for r in matches]}"
    )
    assert any("cron" in r.message for r in matches), (
        f"Erwartet 'cron' als Default-Auslöser-Bezeichnung: {[r.message for r in matches]}"
    )


def test_weather_overlay_startup_call_site_passes_triggered_by(monkeypatch):
    """BUG-106 AK4 (strukturell): `startup()` muss `_weather_overlay(triggered_by=
    "startup")` aufrufen, nicht den parameterlosen Default — sonst würde ein
    Start-Lauf im Log fälschlich wie ein regulärer Cron-Lauf aussehen."""
    import inspect
    src = inspect.getsource(main.startup)
    assert 'triggered_by="startup"' in src, (
        "startup() muss _weather_overlay(triggered_by=\"startup\") aufrufen, damit "
        "AK4 (Unterscheidbarkeit im Log) tatsächlich beim Start greift."
    )


# ---------------------------------------------------------------------------
# Regel 3 / AK3 — das bestehende Zeitbudget-Sicherheitsnetz (urspruenglich BUG-99,
# Wert seit BUG-108 = 1500.0s) selbst bleibt unveraendert; dieses Ticket aendert nur
# die Startbedingungen.
# ---------------------------------------------------------------------------

def test_weather_overlay_max_total_seconds_unchanged_by_bug106():
    """BUG-106 Scope-Abgrenzung: Das bestehende Zeitbudget-Sicherheitsnetz
    (WEATHER_OVERLAY_MAX_TOTAL_SECONDS, aktuell 1500.0s seit BUG-108; urspruenglich
    180s durch BUG-99) wird von diesem Ticket ausdrücklich NICHT verändert (Option B
    ändert nur das Timing der beiden Start-Tasks, nicht das Sicherheitsnetz selbst)."""
    assert main.WEATHER_OVERLAY_MAX_TOTAL_SECONDS == 1500.0, (
        f"WEATHER_OVERLAY_MAX_TOTAL_SECONDS wurde veraendert "
        f"({main.WEATHER_OVERLAY_MAX_TOTAL_SECONDS}) — BUG-106 darf das bestehende "
        f"Zeitbudget-Sicherheitsnetz nicht anfassen (siehe Ticket-Scope)."
    )
