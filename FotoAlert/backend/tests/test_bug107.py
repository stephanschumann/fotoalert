"""BUG-107 — job_history.py zeigt Test-Fixture-Daten statt echter Job-Fehler.

Root Cause (verifiziert per Code-Lektüre + echtem SQLite-Datenabgleich gegen
backend/data_dev/fotoalert.db, siehe Analyse-Abschnitt im BUG-107-Ticket in
BACKLOG.md): Tests, die main._job_start()/main._job_error()/main._job_done()
direkt aufrufen (aktuell ausschließlich backend/tests/test_us38.py), schreiben
dabei ungemockt über den Modul-Singleton main._store in die geteilte
backend/data_dev/fotoalert.db (FOTOALERT_ENV=dev, gesetzt in conftest.py
Zeile 15) — dieselbe Datei, aus der tools/job_history.py im Dev-Modus liest.
Die autouse-Fixture `_reset_job_state` in test_us38.py setzt ausschließlich
In-Memory-Zustand (main._job_status/_last_alert) zurück, keine job_runs-Zeilen
in der SQLite-Datei.

Diese Tests beschreiben das GEWÜNSCHTE Verhalten nach dem empfohlenen Fix
(Option A — siehe Ticket: eine session-scoped autouse-Fixture in conftest.py
leitet ausschließlich `main._store.insert_job_run` auf eine Wegwerf-SQLite-
Datei um, alle anderen `_store`-Methoden/Daten bleiben unverändert gegen die
echte Dev-DB). Sie sind bewusst VOR der Implementierung rot (Rot-Nachweis
laut fotoalert-analyze Schritt 6b).

⚠️ Hinweis zur Ausführungsumgebung (Analyse-Phase, 2026-08-21): Ein echter
pytest-Lauf war in der Analyse-Sandbox (device_bash-Bridge) nicht möglich —
das Backend-venv (`backend/venv`) ist ein macOS-ARM-venv (Symlink auf
/opt/homebrew/.../python3.12), die Bridge-VM ist Linux und kann dieses Binary
nicht ausführen; ein direktes `python3 -c "import fastapi"` in der Bridge-VM
bestätigt zusätzlich, dass dort gar kein fastapi-Stack installiert ist. Der
reale Rot-Nachweis (jetzt rot) und später Grün-Nachweis (nach Fix) müssen auf
Stephans Mac-Terminal laufen:
    cd backend && venv/bin/pytest tests/test_bug107.py -v
"""
import logging
import sqlite3
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="FastAPI-Stack nicht installiert – bootstrap_sandbox.sh ausführen")

import main  # noqa: E402  (Import erst nach importorskip)

pytestmark = [pytest.mark.offline, pytest.mark.regression]

_REAL_DEV_DB = Path(__file__).resolve().parent.parent / "data_dev" / "fotoalert.db"

# Byte-identische Fehlermeldungen aus den bestehenden test_us38.py-Testfällen —
# genau diese Strings wurden in den beiden echten, bereits entstandenen
# Clustern vom 19./21.08.2026 in backend/data_dev/fotoalert.db gefunden.
_KNOWN_US38_FIXTURE_MESSAGES = (
    "Connection timed out",
    "Connection timed out again",
    "Connection timed out after 5s",
    "json.decoder.JSONDecodeError: corrupt cache",
)


def _dev_db_row_count() -> int:
    """Zählt job_runs-Zeilen in der ECHTEN geteilten Dev-DB direkt per sqlite3 —
    bewusst NICHT über main._store, das nach dem Fix ggf. bereits umgeleitet ist."""
    if not _REAL_DEV_DB.exists():
        return 0
    conn = sqlite3.connect(str(_REAL_DEV_DB))
    try:
        return conn.execute("SELECT COUNT(*) FROM job_runs").fetchone()[0]
    except sqlite3.OperationalError:
        return 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AK1 — main._job_error()/main._job_done() hinterlassen keine Zeile in der
# geteilten Dev-DB (unabhängig davon, welcher Job/Status/welche Fehlerklasse).
# ---------------------------------------------------------------------------

def test_job_error_call_leaves_shared_dev_db_untouched():
    before = _dev_db_row_count()
    t0 = main._job_start("weather")
    main._job_error("weather", t0, "BUG-107-Testmarker: Connection timed out")
    after = _dev_db_row_count()
    assert after == before, (
        "main._job_error() hat eine neue Zeile in backend/data_dev/fotoalert.db "
        "hinterlassen — die BUG-107-Isolationsmaßnahme fehlt noch oder greift nicht."
    )


def test_job_done_call_leaves_shared_dev_db_untouched():
    before = _dev_db_row_count()
    t0 = main._job_start("weather")
    main._job_done("weather", t0)
    after = _dev_db_row_count()
    assert after == before, (
        "main._job_done() hat eine neue Zeile in backend/data_dev/fotoalert.db "
        "hinterlassen — die BUG-107-Isolationsmaßnahme fehlt noch oder greift nicht."
    )


# ---------------------------------------------------------------------------
# AK1/AK3-Symptom — job_history.py (bzw. ein direkter SQL-Blick auf dieselbe
# Datei) zeigt nach einem Testlauf keine der bekannten test_us38.py-Fixture-
# Meldungen in der echten Dev-DB — genau das Symptom, das den Bug ursprünglich
# auffallen ließ (vgl. Testplan im BUG-107-Ticket: dieser Test deckt AK1 UND
# das AK3-Symptom gemeinsam ab, daher keine eigene AK2-Zuordnung).
# ---------------------------------------------------------------------------

def test_known_us38_fixture_messages_do_not_appear_in_shared_dev_db():
    t0 = main._job_start("weather")
    main._job_error("weather", t0, "Connection timed out")
    t1 = main._job_start("feed")
    main._job_error("feed", t1, "json.decoder.JSONDecodeError: corrupt cache")

    if not _REAL_DEV_DB.exists():
        pytest.skip("keine Dev-DB-Datei vorhanden")
    conn = sqlite3.connect(str(_REAL_DEV_DB))
    try:
        placeholders = ",".join("?" for _ in _KNOWN_US38_FIXTURE_MESSAGES)
        rows = conn.execute(
            f"SELECT error_msg FROM job_runs WHERE error_msg IN ({placeholders})",
            _KNOWN_US38_FIXTURE_MESSAGES,
        ).fetchall()
    finally:
        conn.close()
    assert rows == [], (
        "Bekannte test_us38.py-Fixture-Fehlermeldungen tauchen in der echten Dev-DB "
        f"auf ({rows!r}) — tools/job_history.py würde sie fälschlich als echte "
        "Job-Fehler anzeigen."
    )


# ---------------------------------------------------------------------------
# AK4 (Negativ/Edge Case, Pre-Mortem Szenario 1) — Der bestehende AK14-Fallback
# aus test_us38.py (insert_job_run wirft eine Exception) funktioniert nach der
# Isolationsmaßnahme unverändert: der Job selbst darf trotz kaputtem DB-Insert
# nicht abbrechen, nur ein Log-Fallback greift.
# ---------------------------------------------------------------------------

def test_job_run_insert_failure_still_falls_back_after_isolation(monkeypatch, caplog):
    def _boom(*args, **kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(main._store, "insert_job_run", _boom)
    caplog.set_level(logging.WARNING, logger="main")

    t0 = main._job_start("weather")
    main._job_done("weather", t0)  # darf trotz kaputtem DB-Insert nicht werfen

    assert main._job_status["weather"]["status"] == "done"
    assert any("job_runs" in r.getMessage() for r in caplog.records)


# ---------------------------------------------------------------------------
# AK5 (Regression) — echte Job-Läufe (über main._store.insert_job_run direkt,
# so wie es z.B. main._record_job_run() im Erfolgsfall täte) bleiben weiterhin
# über load_job_runs() lesbar — die Isolationsmaßnahme darf die normale
# Store-Funktionalität für ANDERE Aufrufer (nicht main._store) nicht einschränken.
# ---------------------------------------------------------------------------

def test_load_job_runs_still_works_on_a_fresh_independent_store(tmp_path):
    from data.store import LocationStore

    store = LocationStore(db_path=tmp_path / "independent.db")
    store.insert_job_run("weather", "done", duration_s=12.3)
    rows = store.load_job_runs(days=7)
    assert len(rows) == 1
