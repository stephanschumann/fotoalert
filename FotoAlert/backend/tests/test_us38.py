"""US-38 — Observability & Self-Healing.

Ein pytest-Fall pro Akzeptanzkriterium aus BACKLOG.md (Ticket US-38,
Weg-Gate-Freigabe 2026-08-17, Option A + SQLite-Persistenz Hybrid), plus die
drei explizit in der Negativ-/Randfall-Checkliste genannten Edge Cases
(Alert-Debounce-Grenze bei genau 1h, ungültiger --days-Parameter,
job_runs-Insert-Fehler bricht den Job nicht ab).

Marker offline + regression + requires_full_checkout (TASK-96: laedt tools/job_history.py
per Repo-Root-relativem Pfad, s.u. _TOOLS_DIR - bricht bei Backend-only-Checkout).
Die Fehlerklassifizierer-Tests
(observability.classify_error) sind zusätzlich als smoke markiert — Kernpfad
für die Fehlerdiagnose, sollen im schnellen Vorlauf mitlaufen.

Muster (geteilter Zustand über Module-Dicts, autouse-Reset-Fixture, `_run()`
für Coroutinen) übernommen von test_bug77_weather_job_status.py.
"""
import asyncio
import importlib.util
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import main
import observability
from data.store import LocationStore

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

_TOOLS_DIR = Path(__file__).resolve().parent.parent.parent / "tools"
_JOB_KEYS = ("weather", "feed", "calendar", "weather-map", "sightlines", "discover")


def _load_job_history_module():
    """Lädt tools/job_history.py als eigenständiges Modul (liegt außerhalb von
    backend/, daher kein normaler Package-Import — Zero-Dependency-CLI, siehe
    Implementation Spec Schritt 6)."""
    spec = importlib.util.spec_from_file_location("job_history", _TOOLS_DIR / "job_history.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(coro):
    # Eigene Event-Loop pro Aufruf: robust, auch wenn ein vorheriger Test
    # (z.B. TestClient) die Default-Loop geschlossen hat.
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _idle_job() -> dict:
    return {
        "status": "idle", "last_run": None, "last_error": None,
        "duration_s": None, "error_class": None, "spec": None,
    }


@pytest.fixture(autouse=True)
def _reset_job_state():
    """Isoliert _job_status/_last_alert/_precompute_running zwischen Tests —
    alles geteilte Module-Globals in main.py."""
    for key in _JOB_KEYS:
        main._job_status[key] = _idle_job()
    main._last_alert.clear()
    main._precompute_running = False
    yield
    for key in _JOB_KEYS:
        main._job_status[key] = _idle_job()
    main._last_alert.clear()
    main._precompute_running = False


# ---------------------------------------------------------------------------
# AK1 — /health liefert je Teilsystem einen eigenen Status
# ---------------------------------------------------------------------------

def test_health_reports_per_subsystem_status(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    subs = body["subsystems"]
    allowed = {"ok", "degraded", "error", "building", "running", "unknown"}
    for key in ("backend", "cache", "weather", "backup"):
        assert key in subs
        assert subs[key] in allowed, f"unerwarteter Status '{subs[key]}' für Teilsystem '{key}'"


# ---------------------------------------------------------------------------
# AK2 — mind. ein Teilsystem im Fehler-/Aufbau-Zustand → Gesamtstatus
# "degraded", HTTP bleibt 200 OK
# ---------------------------------------------------------------------------

def test_health_degraded_on_job_error(client):
    main._job_status["feed"]["status"] = "error"
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "degraded"


def test_health_degraded_on_building_subsystem(client):
    main._precompute_running = True
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "degraded"
    assert body["subsystems"]["cache"] == "building"


# ---------------------------------------------------------------------------
# AK3 — Backup-Status zeigt Stunden seit letztem Backup (US-34-Anbindung)
# ---------------------------------------------------------------------------

def test_health_backup_age_hours(client, monkeypatch):
    monkeypatch.setattr(main.backup, "last_backup_age_hours", lambda: 4.5)
    r = client.get("/health")
    body = r.json()
    assert body["subsystems"]["backup_age_h"] == 4.5
    assert body["subsystems"]["backup"] == "ok"


def test_health_backup_unknown_when_no_backup(client, monkeypatch):
    monkeypatch.setattr(main.backup, "last_backup_age_hours", lambda: None)
    r = client.get("/health")
    body = r.json()
    assert body["subsystems"]["backup"] == "unknown"
    assert body["subsystems"]["backup_age_h"] is None


# ---------------------------------------------------------------------------
# AK4 — Scout-/Discover-Job erscheint mit eigenem Status in /health
# ---------------------------------------------------------------------------

def test_health_includes_discover_job(client):
    r = client.get("/health")
    assert "discover" in r.json()["jobs"]


def test_refresh_discover_tracks_job_status(monkeypatch):
    """_refresh_discover() muss selbst _job_start/_job_done aufrufen — vorher
    war "discover" in /health komplett unsichtbar (Fundstellen-Sweep US-38)."""
    async def fake_refresh(cache_path):
        return None

    import discover.pipeline as pipeline_mod
    monkeypatch.setattr(pipeline_mod, "refresh_discover_cache", fake_refresh)
    monkeypatch.setattr(main, "_load_discover_cache", lambda: None)

    assert main._job_status["discover"]["status"] == "idle"
    _run(main._refresh_discover())
    assert main._job_status["discover"]["status"] == "done"
    assert main._job_status["discover"]["last_run"] is not None


# ---------------------------------------------------------------------------
# AK5 — jeder Job-Lauf erzeugt strukturierten Log-Eintrag (Zeitstempel,
# Jobname, Dauer, Status)
# ---------------------------------------------------------------------------

def test_job_done_and_error_create_structured_log_entries(caplog):
    caplog.set_level(logging.INFO, logger="main")

    t0 = main._job_start("weather")
    main._job_done("weather", t0)

    t1 = main._job_start("calendar")
    main._job_error("calendar", t1, "Connection timed out")

    import json as _json
    done_payloads = [
        _json.loads(r.getMessage()) for r in caplog.records
        if r.name == "main" and r.getMessage().startswith("{") and '"job_run"' in r.getMessage()
    ]
    error_payloads = [
        _json.loads(r.getMessage()) for r in caplog.records
        if r.name == "main" and r.getMessage().startswith("{") and '"job_error"' in r.getMessage()
    ]

    assert any(p["job"] == "weather" and p["status"] == "done" and "ts" in p and "duration_s" in p
               for p in done_payloads)
    assert any(p["job"] == "calendar" and p["status"] == "error" and "ts" in p and "duration_s" in p
               for p in error_payloads)


# ---------------------------------------------------------------------------
# AK6 — Fehlerursache wird automatisch klassifiziert
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.parametrize("msg,expected_class", [
    ("Connection timed out after 30s", "Timeout"),
    ("socket.gaierror: Name or service not known", "APIError"),
    ("json.decoder.JSONDecodeError: Expecting value", "DataError"),
    ("precompute.py exited with returncode 1", "SubprocessError"),
])
def test_classify_error_known_classes(msg, expected_class):
    error_class, files, suggestion = observability.classify_error(msg)
    assert error_class == expected_class
    assert files, "erwarte mind. eine betroffene Datei bei klassifiziertem Fehler"
    assert suggestion


# ---------------------------------------------------------------------------
# AK7 — Negativ: nicht klassifizierbarer Fehler → "Unknown" mit Original-
# meldung, kein falscher spezifischer Vorschlag
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_classify_error_unknown_no_false_positive():
    error_class, files, suggestion = observability.classify_error(
        "Voellig unerwarteter interner Zustand X42 ohne bekanntes Muster"
    )
    assert error_class == "Unknown"
    assert files == []
    assert suggestion == "Fehler nicht klassifizierbar — bitte Log manuell prüfen"


# ---------------------------------------------------------------------------
# AK8 — klassifizierter Fehler → Lösungsvorschlag mit betroffenen Dateien +
# Maßnahme, nur zum Nachlesen (main._job_status[...]["spec"])
# ---------------------------------------------------------------------------

def test_job_error_stores_spec_suggestion_for_classified_error():
    t0 = main._job_start("weather")
    main._job_error("weather", t0, "Connection timed out after 5s")

    js = main._job_status["weather"]
    assert js["error_class"] == "Timeout"
    assert js["spec"] is not None
    assert js["spec"]["files"] == ["backend/calculations/weather.py"]
    assert "Retry" in js["spec"]["suggestion"] or "Timeout" in js["spec"]["suggestion"]


# ---------------------------------------------------------------------------
# AK9 — wiederholter Fehlschlag in kurzer Folge → nur begrenzter Alarm pro
# Stunde (Debounce)
# ---------------------------------------------------------------------------

def test_alert_debounce_limits_repeated_failures(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "_send_alert_email",
                         lambda job, ec, msg, spec: calls.append((job, ec)))

    t0 = main._job_start("weather")
    main._job_error("weather", t0, "Connection timed out")
    t1 = main._job_start("weather")
    main._job_error("weather", t1, "Connection timed out again")

    assert len(calls) == 1, "zweiter Fehlschlag kurz danach darf keinen zweiten Alarm auslösen"


# Edge Case (Negativ-Checkliste): Alert-Debounce-Grenze bei genau 1h.
def test_alert_debounce_boundary_59_vs_61_minutes(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "_send_alert_email", lambda job, ec, msg, spec: calls.append(1))
    now = datetime.now(timezone.utc)

    main._last_alert["weather"] = now - timedelta(minutes=59)
    main._maybe_alert("weather", "Timeout", "x", {"files": [], "suggestion": "y"})
    assert len(calls) == 0, "59 Minuten Abstand → noch debounced, kein Alarm"

    main._last_alert["weather"] = now - timedelta(minutes=61)
    main._maybe_alert("weather", "Timeout", "x", {"files": [], "suggestion": "y"})
    assert len(calls) == 1, "61 Minuten Abstand → Debounce-Fenster abgelaufen, Alarm erlaubt"


def test_alert_debounce_exactly_one_hour_still_debounced(monkeypatch):
    """Implementation Spec Schritt 4: Alert nur wenn `now - _last_alert[job] >
    timedelta(hours=1)` — bei GENAU 1h (nicht strikt größer) bleibt es debounced."""
    calls = []
    monkeypatch.setattr(main, "_send_alert_email", lambda *a, **k: calls.append(1))
    now = datetime.now(timezone.utc)
    main._last_alert["weather"] = now - timedelta(hours=1)
    main._maybe_alert("weather", "Timeout", "x", {"files": [], "suggestion": "y"}, now=now)
    assert len(calls) == 0


# ---------------------------------------------------------------------------
# AK10 — keine E-Mail-Adresse konfiguriert → Fehler-Log-Eintrag funktioniert
# trotzdem normal weiter, kein Absturz
# ---------------------------------------------------------------------------

def test_job_error_without_alert_email_configured(monkeypatch):
    monkeypatch.delenv("FOTOALERT_ALERT_EMAIL", raising=False)
    smtp_calls = []
    import smtplib
    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **k: smtp_calls.append(1))

    t0 = main._job_start("weather")
    main._job_error("weather", t0, "Connection timed out")  # darf nicht werfen

    assert smtp_calls == [], "ohne FOTOALERT_ALERT_EMAIL darf gar kein SMTP-Versuch stattfinden"
    assert main._job_status["weather"]["status"] == "error"
    assert main._job_status["weather"]["last_error"] == "Connection timed out"


# ---------------------------------------------------------------------------
# AK11 — CLI zeigt Tabelle aller Job-Läufe der letzten 7 Tage, auch nach
# einem Server-Neustart (SQLite-Persistenz)
# ---------------------------------------------------------------------------

def test_cli_job_history_survives_restart(tmp_path):
    job_history = _load_job_history_module()
    db_path = tmp_path / "fotoalert.db"

    # "vor dem Neustart": ein Store-Objekt schreibt Job-Läufe.
    store1 = LocationStore(db_path=db_path)
    store1.insert_job_run("weather", "done", duration_s=1.1)
    store1.insert_job_run("feed", "error", duration_s=0.4, error_class="Timeout",
                           error_msg="x", spec_suggestion="y")
    del store1  # simuliert Prozessende — die Daten leben nur noch in der Datei

    # "nach dem Neustart": frischer Zugriff, rein über die CLI/SQLite-Datei.
    rows = job_history.fetch_job_runs(db_path, days=7)
    assert len(rows) == 2
    table = job_history.format_table(rows)
    assert "weather" in table
    assert "feed" in table
    assert "Timeout" in table


# ---------------------------------------------------------------------------
# AK12 — Negativ: keine Job-History vorhanden (frische Installation) → klare
# CLI-Meldung statt leerer/kryptischer Ausgabe
# ---------------------------------------------------------------------------

def test_cli_job_history_empty_shows_clear_message(tmp_path, capsys):
    job_history = _load_job_history_module()
    db_path = tmp_path / "nonexistent_fotoalert.db"

    exit_code = job_history.main(["--db", str(db_path)])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "Keine Job-History-Daten gefunden" in out


# ---------------------------------------------------------------------------
# AK13 — Edge Case: zwei gleichzeitig fehlschlagende Jobs bekommen je eigene
# Fehlerklassifizierung/Vorschlag
# ---------------------------------------------------------------------------

def test_two_simultaneous_job_failures_get_independent_classification():
    t0_weather = main._job_start("weather")
    t0_feed = main._job_start("feed")

    main._job_error("weather", t0_weather, "Connection timed out")
    main._job_error("feed", t0_feed, "json.decoder.JSONDecodeError: corrupt cache")

    assert main._job_status["weather"]["error_class"] == "Timeout"
    assert main._job_status["feed"]["error_class"] == "DataError"
    assert main._job_status["weather"]["spec"] != main._job_status["feed"]["spec"]


# ---------------------------------------------------------------------------
# AK14 — Edge Case: Schlägt der job_runs-Insert selbst fehl, bricht der Job
# selbst nicht ab, nur Log-Fallback
# ---------------------------------------------------------------------------

def test_job_run_insert_failure_falls_back_to_log_only(monkeypatch, caplog):
    def _boom(*args, **kwargs):
        raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(main._store, "insert_job_run", _boom)
    caplog.set_level(logging.WARNING, logger="main")

    t0 = main._job_start("weather")
    main._job_done("weather", t0)  # darf trotz kaputtem DB-Insert nicht werfen

    assert main._job_status["weather"]["status"] == "done"
    assert any("job_runs" in r.getMessage() for r in caplog.records)


def test_job_run_insert_failure_falls_back_to_log_only_on_error(monkeypatch, caplog):
    """Gleiches Edge Case, aber für den Fehlerpfad (_job_error) statt _job_done —
    beide Aufrufer nutzen denselben _record_job_run()-Fallback."""
    def _boom(*args, **kwargs):
        raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(main._store, "insert_job_run", _boom)
    monkeypatch.setattr(main, "_send_alert_email", lambda *a, **k: None)
    caplog.set_level(logging.WARNING, logger="main")

    t0 = main._job_start("weather")
    main._job_error("weather", t0, "Connection timed out")  # darf nicht werfen

    assert main._job_status["weather"]["status"] == "error"
    assert any("job_runs" in r.getMessage() for r in caplog.records)


# ---------------------------------------------------------------------------
# AK15 — Edge Case: ungültiger --days-Parameter → verständliche
# Fehlermeldung statt Absturz
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_value", ["-1", "0", "abc", "3.5"])
def test_cli_invalid_days_shows_clear_error(bad_value, capsys):
    job_history = _load_job_history_module()
    exit_code = job_history.main(["--days", bad_value])
    err = capsys.readouterr().err

    assert exit_code == 2
    assert "Fehler:" in err
    assert "Traceback" not in err


# ---------------------------------------------------------------------------
# Bonus-Regression (Testplan-Manuellschritt automatisiert): bestehende
# Konsumenten, die nur `status`/`version`/`locations_count` lesen (z.B.
# deploy/deploy.sh), funktionieren nach der US-38-Erweiterung unverändert.
# ---------------------------------------------------------------------------

def test_health_backward_compatible_fields_still_present(client):
    r = client.get("/health")
    body = r.json()
    assert "status" in body
    assert "version" in body
    assert "locations_count" in body
