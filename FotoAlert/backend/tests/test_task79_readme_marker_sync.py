"""TASK-79: Test-Doku backend/tests/README.md muss die BUG-79-Testrealität widerspiegeln.

Statischer Text-Check (kein Netzwerk, kein echter Testlauf) gegen backend/tests/README.md:
prüft, dass die Marker-Tabelle den neuen Test test_bug79_ci_ephemeris_skip.py auflistet
und dass die Zeile zu test_astronomy_regression.py nicht mehr ausschließlich "offline"
behauptet, obwohl die Datei seit BUG-79 vier @pytest.mark.online-Tests enthält.

AKs siehe BACKLOG.md TASK-79 Implementation Spec (AK1, AK3).
"""
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]

_README = Path(__file__).parent / "README.md"
_TABLE_HEADER = "| Datei | Bereich |"


def _read_readme() -> str:
    assert _README.exists(), f"{_README} nicht gefunden"
    return _README.read_text(encoding="utf-8")


def _table_section(source: str) -> str:
    """Gibt den README-Text ab dem Tabellen-Header zurück.

    Wichtig: test_astronomy_regression.py wird auch im Fließtext vor der Tabelle
    (Konventions-Absatz) erwähnt — ein ungerichteter source.find() würde also die
    falsche (nicht-tabellarische) Stelle treffen. Deshalb wird gezielt erst ab dem
    Tabellen-Header gesucht.
    """
    idx = source.find(_TABLE_HEADER)
    assert idx != -1, f"Marker-Tabellen-Header {_TABLE_HEADER!r} nicht in README.md gefunden"
    return source[idx:]


def test_readme_lists_bug79_ephemeris_skip_test():
    """AK3: test_bug79_ci_ephemeris_skip.py ist in der Marker-Tabelle erwähnt."""
    table = _table_section(_read_readme())
    assert "test_bug79_ci_ephemeris_skip.py" in table, (
        "backend/tests/README.md erwähnt test_bug79_ci_ephemeris_skip.py nicht in der "
        "Marker-Tabelle — TASK-79 AK3 nicht erfüllt."
    )


def test_readme_astronomy_regression_row_mentions_online():
    """AK1: Die Tabellenzeile zu test_astronomy_regression.py behauptet nicht mehr
    ausschließlich 'offline' — seit BUG-79 enthält die Datei 4 online-Tests."""
    table = _table_section(_read_readme())
    idx = table.find("test_astronomy_regression.py")
    assert idx != -1, "test_astronomy_regression.py nicht in der Marker-Tabelle gefunden"

    line_start = table.rfind("\n", 0, idx) + 1
    line_end = table.find("\n", idx)
    row = table[line_start:line_end]

    assert "online" in row, (
        f"Tabellenzeile zu test_astronomy_regression.py nennt kein 'online': {row!r} — "
        "TASK-79 AK1 nicht erfüllt (Datei enthält seit BUG-79 vier online-Tests)."
    )


def test_all_test_files_listed_in_readme_table():
    """TASK-79 (Option B, Weg-Gate 2026-07-15) — letztes AK: jede *.py-Testdatei in
    backend/tests/ hat eine eigene Zeile in der README-Marker-Tabelle.

    Reiner Existenz-Check je Dateiname (kein inhaltlicher Marker-Abgleich — das bleibt
    laut Analyse-Spec bewusst manuelle Sorgfaltspflicht, da eine automatisierte
    inhaltliche Prüfung aller Zeilen unverhältnismäßig aufwendig wäre).
    """
    tests_dir = Path(__file__).parent
    excluded_names = {"__init__.py", "conftest.py"}
    py_files = sorted(
        p.name for p in tests_dir.glob("*.py")
        if p.is_file() and p.name not in excluded_names
    )
    assert py_files, "Keine *.py-Testdateien in backend/tests/ gefunden — Glob-Pfad prüfen."

    table = _table_section(_read_readme())
    missing = [name for name in py_files if name not in table]
    assert not missing, (
        "Folgende Testdateien in backend/tests/ fehlen als Zeile in der README-"
        f"Marker-Tabelle: {', '.join(missing)}"
    )
