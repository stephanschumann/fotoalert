"""Tests für TASK-54: dauerhafter Festplatten-Cache für Wetterkarten-PNGs.

Weg-Gate-Entscheidung (Stephan, 2026-08-16): Option A — leichtgewichtiger
Disk-Cache nach dem bestehenden `_load_caches()`/`_load_discover_cache()`-Muster.

Deckt AK1–AK6 aus dem Ticket ab:
  - AK1: Nach einem Neustart mit vorherigem erfolgreichem Kartenbau zeigt der
    Karten-Tab sofort die zuletzt gebaute Karte (kein Warten auf Neuaufbau).
  - AK2: Ohne vorherigen Bau (frischer Server) verhält sich alles wie heute
    (`ready:false`), kein neuer Fehlerzustand.
  - AK3: Der geladene Stand wird weiterhin nach dem bestehenden Rhythmus
    (30-s-Start-Verzögerung, 1-h-TTL, 3-h-Cron) automatisch aktualisiert.
  - AK4: Eine beschädigte/unlesbare Cache-Datei lässt den Server nicht
    abstürzen, sondern fällt robust auf den Ist-Zustand zurück (mit Log-Hinweis).
  - AK5: Der Disk-Cache belegt dauerhaft nur eine konstante Speichermenge
    (feste Overwrite-Semantik, keine wachsende Historie).
  - AK6: Die bestehenden Verträge von /weather-map und
    /weather-map/png/{field}/{idx} bleiben unverändert (rein additiver Disk-Cache).

Alle Tests laufen deterministisch und offline (isolierter tmp_path-Cache-Ordner,
kein echter Netzwerk-/GRIB-Abruf, keine Berührung des echten Dev-Cache-Ordners
— Pattern 12: Test-Fixtures immer selbst-anlegend, nie externe/echte Ablagen
voraussetzen). Der echte Modul-Konstanten-Pfad `main._WEATHER_MAP_CACHE_DIR`/
`main._WEATHER_MAP_CACHE_META` wird je Test per monkeypatch auf ein tmp_path-
Verzeichnis umgebogen.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import pytest

import main

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _run(coro):
    """Eigene, frische Event-Loop pro Aufruf (Muster: test_us106.py/test_bug77_
    weather_job_status.py) — robust unabhängig von der session-scoped TestClient-
    Loop und vermeidet, `asyncio.create_task` global zu monkeypatchen (das würde
    auch die TestClient-eigene Loop treffen)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Fixtures / Helfer
# ---------------------------------------------------------------------------

@pytest.fixture
def weather_map_cache_paths(tmp_path, monkeypatch):
    """Isoliert den Disk-Cache-Ordner in ein temporäres Verzeichnis (nie den
    echten backend/data/cache/weather_map/-Ordner anfassen)."""
    cache_dir = tmp_path / "weather_map"
    meta = cache_dir / "meta.json"
    monkeypatch.setattr(main, "_WEATHER_MAP_CACHE_DIR", cache_dir)
    monkeypatch.setattr(main, "_WEATHER_MAP_CACHE_META", meta)
    return cache_dir, meta


@pytest.fixture(autouse=True)
def _reset_weather_map_globals(monkeypatch):
    """Jeder Test startet mit einem sauberen, dem Ist-Zustand vor jedem Bau
    entsprechenden Ausgangszustand (None/leer) — unabhängig von der Reihenfolge
    oder was ein vorheriger Test im Prozess-Cache hinterlassen hat."""
    monkeypatch.setattr(main, "_weather_map_cache", None)
    monkeypatch.setattr(main, "_weather_map_png", {"cloud": [], "precip": []})
    monkeypatch.setattr(main, "_weather_map_updated_at", None)
    yield


def _seed_in_memory_build(monkeypatch, n=3, ts=None):
    """Simuliert einen erfolgreich abgeschlossenen `_build_weather_map()`-Lauf,
    ohne echten GRIB-/MET-Abruf: befüllt exakt die drei Prozess-Cache-Globals,
    die `_build_weather_map()` im Erfolgspfad selbst setzt."""
    ts = ts or datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)
    bounds = [[43.0, 3.0], [71.5, 21.0]]
    hourly_times = [f"2026-08-16T{h:02d}:00:00+00:00" for h in range(n)]
    cloud_pngs = [b"\x89PNG\r\n\x1a\nCLOUD" + str(i).encode() for i in range(n)]
    # Ein absichtlich fehlendes Bild (None) — testet, dass Lücken (z.B. eine
    # Quelle war für diese Stunde nicht verfügbar) den Roundtrip nicht stören.
    precip_pngs = [
        None if i == 1 else b"\x89PNG\r\n\x1a\nPRECIP" + str(i).encode()
        for i in range(n)
    ]
    weather_map_cache = {
        "bounds": bounds,
        "hourly_times": hourly_times,
        "sources": {"icon_d2": 10, "icon_eu": 5, "met": 3},
        "n_points": 18,
        "attribution": "Daten: DWD · MET Norway (CC BY 4.0)",
        "attribution_url": "https://www.met.no/en/free-meteorological-data",
    }
    weather_map_png = {"cloud": cloud_pngs, "precip": precip_pngs}
    monkeypatch.setattr(main, "_weather_map_cache", weather_map_cache)
    monkeypatch.setattr(main, "_weather_map_png", weather_map_png)
    monkeypatch.setattr(main, "_weather_map_updated_at", ts)
    return weather_map_cache, weather_map_png, ts


def _clear_in_memory(monkeypatch):
    """Simuliert einen Server-Neustart: Prozess-Cache ist wieder leer, bevor
    `_load_weather_map_cache_from_disk()` (der neue Startschritt) läuft."""
    monkeypatch.setattr(main, "_weather_map_cache", None)
    monkeypatch.setattr(main, "_weather_map_png", {"cloud": [], "precip": []})
    monkeypatch.setattr(main, "_weather_map_updated_at", None)


# ---------------------------------------------------------------------------
# AK1 — Sofort-Anzeige nach Neustart bei vorhandenem Cache
# ---------------------------------------------------------------------------

def test_task54_startup_loads_last_successful_map_from_disk(weather_map_cache_paths, monkeypatch):
    """AK1: Gab es vor einem (simulierten) Neustart mindestens einen
    erfolgreichen Kartenbau, füllt `_load_weather_map_cache_from_disk()` den
    Prozess-Cache sofort wieder mit exakt diesem Stand — ohne auf den nächsten
    Hintergrund-Bau zu warten."""
    weather_map_cache, weather_map_png, ts = _seed_in_memory_build(monkeypatch, n=3)

    # 1. Erfolgreicher Bau persistiert sich selbst (Aufruf im Erfolgspfad von
    #    _build_weather_map(), hier direkt aufgerufen, um den Bau nicht mit
    #    echten GRIB-/MET-Abrufen simulieren zu müssen).
    main._persist_weather_map_cache()

    # 2. Server-Neustart: Prozess-Cache ist wieder leer.
    _clear_in_memory(monkeypatch)
    assert main._weather_map_cache is None

    # 3. Neuer Startschritt lädt den zuletzt persistierten Stand zurück.
    loaded = main._load_weather_map_cache_from_disk()

    assert loaded is True
    assert main._weather_map_cache is not None
    assert main._weather_map_cache["bounds"] == weather_map_cache["bounds"]
    assert main._weather_map_cache["hourly_times"] == weather_map_cache["hourly_times"]
    assert main._weather_map_cache["sources"] == weather_map_cache["sources"]
    assert main._weather_map_cache["attribution"] == weather_map_cache["attribution"]
    assert main._weather_map_cache["attribution_url"] == weather_map_cache["attribution_url"]
    assert main._weather_map_png["cloud"] == weather_map_png["cloud"]
    assert main._weather_map_png["precip"] == weather_map_png["precip"]  # inkl. None-Lücke
    assert main._weather_map_updated_at == ts


def test_task54_startup_calls_load_from_disk_between_load_caches_and_no_background():
    """AK1 (strukturell): `startup()` muss `_load_weather_map_cache_from_disk()`
    NACH `_load_caches()` aufrufen, aber VOR dem `_NO_BACKGROUND`-Kurzschluss —
    exakt der Ladezeitpunkt, den die anderen synchron geladenen Caches
    (`_load_caches()`, analog `_load_discover_cache()`) bereits nutzen. Ohne
    diese Reihenfolge würde der Disk-Cache im Test-/Sandbox-Modus (in dem alles
    Asynchrone übersprungen wird) nie geladen."""
    import inspect
    src = inspect.getsource(main.startup)
    assert "_load_weather_map_cache_from_disk()" in src, (
        "startup() ruft _load_weather_map_cache_from_disk() nicht auf."
    )
    load_caches_idx = src.index("_load_caches()")
    load_disk_idx = src.index("_load_weather_map_cache_from_disk()")
    no_background_idx = src.index("_NO_BACKGROUND")
    assert load_caches_idx < load_disk_idx < no_background_idx, (
        "_load_weather_map_cache_from_disk() muss zwischen _load_caches() und dem "
        "_NO_BACKGROUND-Abbruch aufgerufen werden (gleicher Ladezeitpunkt wie die "
        "anderen Start-Caches)."
    )


# ---------------------------------------------------------------------------
# AK2 — Edge Case: kein vorheriger Bau (Leerzustand bleibt unverändert)
# ---------------------------------------------------------------------------

def test_task54_startup_without_prior_build_behaves_like_today(weather_map_cache_paths, client):
    """AK2: Gab es vor dem (simulierten) Neustart noch nie einen erfolgreichen
    Kartenbau (frischer Server ohne Cache-Historie — Cache-Ordner existiert gar
    nicht), verhält sich der Server nach `_load_weather_map_cache_from_disk()`
    exakt wie heute: `ready:false`, kein neuer Fehlerzustand."""
    cache_dir, meta = weather_map_cache_paths
    assert not meta.exists()  # ganz frischer Server: keine Cache-Historie

    loaded = main._load_weather_map_cache_from_disk()

    assert loaded is False
    assert main._weather_map_cache is None
    assert main._weather_map_png == {"cloud": [], "precip": []}
    assert main._weather_map_updated_at is None

    # Endpoint verhält sich exakt wie im bisherigen Leerzustand (US-112, unverändert).
    r = client.get("/weather-map?hours=72")
    assert r.status_code == 200
    body = r.json()
    assert body["ready"] is False
    assert body["hourly_times"] == []
    assert body["frames"] == {"clouds": [], "precip": []}


# ---------------------------------------------------------------------------
# AK3 — Hintergrund-Aktualisierung bleibt unverändert (Rhythmus/Timing)
# ---------------------------------------------------------------------------

def test_task54_background_refresh_unaffected_by_disk_cache(weather_map_cache_paths, monkeypatch):
    """AK3: Ein aus dem Disk-Cache geladener (ggf. veralteter) Stand friert
    nicht ein — die bestehende TTL-/Lazy-Trigger-Logik in GET /weather-map
    stößt bei Überschreiten der TTL weiterhin wie bisher einen Hintergrund-Bau
    an. Die Rhythmus-Konstanten selbst (30-s-Start-Verzögerung, 1-h-TTL) bleiben
    durch dieses Ticket unverändert (reine Regression, kein neues Verhalten).

    Ruft die Endpoint-Coroutine direkt auf (kein TestClient/ASGI) und wartet den
    dabei per `asyncio.create_task()` gefeuerten Fire-and-Forget-Rebuild-Task
    explizit ab, statt sich auf ein Timing-Race zu verlassen. `_NO_BACKGROUND`
    (im Test-Harness global gesetzt, conftest.py) unterdrückt den Lazy-Trigger
    bewusst für ALLE Endpoints im Sandbox-Testbetrieb — für diesen einen Test
    wird der Guard testweise deaktiviert, um die dahinterliegende, unveränderte
    Trigger-Logik selbst zu prüfen (identisches Muster wie test_us106.py,
    `test_single_recompute_deferred_during_running_job`/`test_drain_processes_
    pending_sequentially`)."""
    monkeypatch.setattr(main, "_NO_BACKGROUND", False)

    # Rhythmus-Konstanten unverändert (TASK-54 ändert nur den Startzustand, nicht
    # das Timing selbst).
    assert main._WEATHER_MAP_TTL == timedelta(hours=1)
    assert main._STARTUP_WEATHER_MAP_DELAY_S == 30.0

    # Aus dem Disk-Cache geladener Stand mit einem absichtlich abgelaufenen
    # Zeitstempel (älter als die TTL) simulieren.
    stale_ts = datetime.now(timezone.utc) - timedelta(hours=2)
    _seed_in_memory_build(monkeypatch, n=2, ts=stale_ts)

    build_calls = {"n": 0}

    async def _fake_build():
        build_calls["n"] += 1

    monkeypatch.setattr(main, "_weather_map_building", False)
    monkeypatch.setattr(main, "_build_weather_map", _fake_build)

    async def scenario():
        result = await main.weather_map(hours=72)
        pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if pending:
            await asyncio.gather(*pending)
        return result

    body = _run(scenario())

    assert body["ready"] is True  # geladener Stand bleibt nutzbar, während im Hintergrund neu gebaut wird
    assert build_calls["n"] == 1, (
        "Ein aus dem Disk-Cache geladener, abgelaufener Stand muss weiterhin "
        "denselben Lazy-Rebuild-Trigger auslösen wie ein normal gealterter "
        "Prozess-Cache-Stand — der Disk-Cache darf das bestehende Timing nicht "
        "einfrieren."
    )


# ---------------------------------------------------------------------------
# AK4 — Edge Case: korrupte/fehlende Cache-Datei → robuster Fallback + Log
# ---------------------------------------------------------------------------

def test_task54_corrupt_cache_file_falls_back_gracefully(weather_map_cache_paths, caplog):
    """AK4: Ist die Cache-Datei beschädigt/unlesbar, darf `_load_weather_map_cache_from_disk()`
    weder eine Exception nach außen werfen noch die Modul-Globals in einen
    inkonsistenten Zustand bringen — sie bleiben unverändert (None/leer), exakt
    wie im Leerzustand (AK2), plus ein Log-Hinweis auf den Ladefehler."""
    cache_dir, meta = weather_map_cache_paths
    cache_dir.mkdir(parents=True, exist_ok=True)
    meta.write_bytes(b"\x00\x01das-ist-kein-json{{{")  # absichtlich kaputt

    with caplog.at_level(logging.WARNING, logger="main"):
        loaded = main._load_weather_map_cache_from_disk()

    assert loaded is False
    assert main._weather_map_cache is None
    assert main._weather_map_png == {"cloud": [], "precip": []}
    assert main._weather_map_updated_at is None

    warnings = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
    assert warnings, (
        "Ein Ladefehler bei korrupter Cache-Datei muss geloggt werden (AK4), "
        "damit ein Admin/Betreiber ihn im Server-Log erkennen kann."
    )


def test_task54_missing_referenced_image_file_does_not_crash(weather_map_cache_paths, monkeypatch):
    """AK4 (Randfall): Die Metadaten-Datei ist gültig, aber ein darin
    referenziertes Bild fehlt auf der Platte (z.B. unvollständiger Schreib-
    vorgang vor einem harten Absturz, Pre-Mortem-Szenario 1). Das darf nicht
    crashen — die fehlende Stunde bleibt einfach `None` (identisch zum
    bestehenden Lücken-Verhalten im Prozess-Cache selbst, s. AK1-Test)."""
    weather_map_cache, weather_map_png, ts = _seed_in_memory_build(monkeypatch, n=3)
    main._persist_weather_map_cache()
    cache_dir, meta = weather_map_cache_paths
    # Ein bereits geschriebenes Bild nachträglich löschen (simuliert eine Lücke).
    (cache_dir / "cloud" / "0.png").unlink()

    _clear_in_memory(monkeypatch)
    loaded = main._load_weather_map_cache_from_disk()

    assert loaded is True  # Metadaten waren gültig — kein Totalausfall wegen einer Lücke
    assert main._weather_map_png["cloud"][0] is None
    assert main._weather_map_png["cloud"][2] == weather_map_png["cloud"][2]


# ---------------------------------------------------------------------------
# AK5 — konstanter Speicherbedarf (feste Overwrite-Semantik, keine Historie)
# ---------------------------------------------------------------------------

def test_task54_cache_size_stays_constant_across_rebuilds(weather_map_cache_paths, monkeypatch):
    """AK5: Mehrere aufeinanderfolgende Bauläufe dürfen die Cache-Ablage nicht
    anwachsen lassen — jeder Bau überschreibt/ersetzt vollständig den
    vorherigen Stand (keine Rotation/Historie wie bei den DB-Snapshots)."""
    cache_dir, meta = weather_map_cache_paths

    # Lauf 1: 5 Stunden.
    _seed_in_memory_build(monkeypatch, n=5)
    main._persist_weather_map_cache()
    files_after_run1 = sorted(p.name for p in (cache_dir / "cloud").glob("*.png"))
    assert len(files_after_run1) == 5

    # Lauf 2: nur noch 2 Stunden (z.B. kürzere Datenlage) — alte Dateien aus
    # Lauf 1 dürfen NICHT liegen bleiben, sonst wächst die Ablage über die Zeit
    # (Pre-Mortem-Szenario 5).
    _seed_in_memory_build(monkeypatch, n=2)
    main._persist_weather_map_cache()
    files_after_run2 = sorted(p.name for p in (cache_dir / "cloud").glob("*.png"))
    assert len(files_after_run2) == 2, (
        f"Nach Lauf 2 (n=2) liegen noch {len(files_after_run2)} Bilder in der "
        f"Cache-Ablage ({files_after_run2}) — alte Bilder aus Lauf 1 wurden nicht "
        f"entfernt, die Ablage würde über die Zeit unbegrenzt wachsen."
    )

    # Lauf 3: wieder 5 Stunden — Größe bleibt in derselben Größenordnung, kein
    # kumulatives Wachstum über mehrere Läufe hinweg.
    _seed_in_memory_build(monkeypatch, n=5)
    main._persist_weather_map_cache()
    files_after_run3 = sorted(p.name for p in (cache_dir / "cloud").glob("*.png"))
    assert len(files_after_run3) == 5


# ---------------------------------------------------------------------------
# AK6 — bestehende Endpoint-Verträge von /weather-map und
# /weather-map/png/{field}/{idx} bleiben unverändert (rein additiver Disk-Cache)
# ---------------------------------------------------------------------------

def test_task54_endpoint_contract_unchanged(weather_map_cache_paths, monkeypatch, client):
    """AK6: Response-Struktur, `ready`-Feld, `fetched_at`-Feld und das
    Fehlerverhalten bei unbekanntem Feld/Index bleiben exakt wie vor diesem
    Ticket — der Disk-Cache ist rein additiv zum Startzustand, keine Änderung
    an den Endpoints selbst."""
    weather_map_cache, weather_map_png, ts = _seed_in_memory_build(monkeypatch, n=2)
    main._persist_weather_map_cache()  # Disk-Cache existiert nun zusätzlich

    r = client.get("/weather-map?hours=72")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {
        "ready", "bounds", "hourly_times", "frames", "attribution",
        "attribution_url", "sources", "fetched_at",
    }
    assert body["ready"] is True
    assert body["bounds"] == weather_map_cache["bounds"]
    assert body["frames"]["clouds"][0] == "/weather-map/png/cloud/0"
    assert body["frames"]["precip"][1] is None  # absichtliche Lücke bleibt null, kein Fake-Pfad
    assert body["fetched_at"] == ts.isoformat()

    r_png = client.get("/weather-map/png/cloud/0")
    assert r_png.status_code == 200
    assert r_png.headers["content-type"] == "image/png"
    assert r_png.content == weather_map_png["cloud"][0]

    # Fehlerverhalten unverändert: unbekanntes Feld / Index außerhalb des Bereichs → 404.
    assert client.get("/weather-map/png/bogus/0").status_code == 404
    assert client.get("/weather-map/png/cloud/99").status_code == 404
