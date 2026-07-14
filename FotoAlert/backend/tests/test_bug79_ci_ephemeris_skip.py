"""BUG-79: Absicherung der CI-Ephemeriden-Download-Fixes.

Zwei rein statische Prüfungen (kein Netzwerkzugriff, kein Live-Download, kein
echter Skyfield-Aufruf):

1. AK3 — der alte, irreführende Kommentar in test_astronomy_regression.py
   (Z. 110-112 vor diesem Fix), der eine nicht existierende Skip-Logik für
   @pytest.mark.online-Tests behauptete, darf nicht mehr vorkommen.
2. AK4 / Pre-Mortem-Szenario 2 — kein @pytest.mark.offline-markierter Test in
   test_astronomy_regression.py darf transitiv einen bekannten
   `_get_eph()`-Aufrufpfad aus calculations/astronomy.py nutzen (Marker würde sonst
   „deterministisch, ohne Netzwerk" behaupten, obwohl der Test einen ungemockten
   de421.bsp-Zugriff auslöst).

AK1/AK2/AK6 (Cache-/Timeout-Wirkung in echtem GitHub Actions) sind laut Testplan in
BACKLOG.md BUG-79 nicht sinnvoll lokal simulierbar und werden manuell im CI-Log
verifiziert — hier bewusst nicht nachgebaut.
"""
import ast
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]

_TESTS_DIR = Path(__file__).parent
_REGRESSION_TEST_FILE = _TESTS_DIR / "test_astronomy_regression.py"
_ASTRONOMY_MODULE_FILE = _TESTS_DIR.parent / "calculations" / "astronomy.py"

# Wortlaut aus der ursprünglichen, fälschlichen Kommentar-Behauptung (vor BUG-79).
_OLD_MISLEADING_PHRASES = [
    "wird in CI übersprungen",
    "wenn kein Netz verfügbar ist",
]


def test_misleading_ci_skip_comment_removed():
    """AK3: Die alte, irreführende Formulierung ist aus dem Kommentar entfernt."""
    assert _REGRESSION_TEST_FILE.exists(), f"{_REGRESSION_TEST_FILE} nicht gefunden"
    source = _REGRESSION_TEST_FILE.read_text(encoding="utf-8")
    for phrase in _OLD_MISLEADING_PHRASES:
        assert phrase not in source, (
            f"Alte irreführende Formulierung {phrase!r} noch in "
            f"{_REGRESSION_TEST_FILE.name} gefunden — BUG-79 AK3 nicht erfüllt."
        )


def _decorator_marker_name(dec):
    """Gibt 'offline'/'online'/... zurück für Decorators der Form pytest.mark.<name>(...)."""
    node = dec
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute):
        if node.value.attr == "mark":
            return node.attr
    return None


def _functions_calling_get_eph(module_source):
    """Top-Level-Funktionsnamen in astronomy.py, die `_get_eph()` direkt aufrufen.

    Das ist der bekannte Netzwerk-/Datei-Ladepfad (skyfield.api.load("de421.bsp")).
    """
    tree = ast.parse(module_source)
    calling = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for inner in ast.walk(node):
                if (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Name)
                    and inner.func.id == "_get_eph"
                ):
                    calling.add(node.name)
                    break
    return calling


def _offline_marked_tests(test_source):
    """Gibt {Testfunktionsname: Quelltext} für alle @pytest.mark.offline-Tests zurück."""
    tree = ast.parse(test_source)
    result = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if _decorator_marker_name(dec) == "offline":
                result[node.name] = ast.get_source_segment(test_source, node) or ""
                break
    return result


def test_no_offline_marked_test_uses_known_get_eph_path():
    """AK4/Szenario 2: kein offline-Test ruft einen bekannten _get_eph()-Pfad auf.

    Leichtgewichtiger Text-/AST-Check (kein echter Funktionsaufruf, kein Netzwerk):
    ermittelt aus calculations/astronomy.py, welche Top-Level-Funktionen `_get_eph()`
    direkt aufrufen, und prüft, ob eine @pytest.mark.offline-markierte Testfunktion in
    test_astronomy_regression.py eine dieser Funktionen über den Modul-Alias `A.` aufruft.
    """
    assert _ASTRONOMY_MODULE_FILE.exists(), f"{_ASTRONOMY_MODULE_FILE} nicht gefunden"
    astronomy_source = _ASTRONOMY_MODULE_FILE.read_text(encoding="utf-8")
    risky_functions = _functions_calling_get_eph(astronomy_source)

    # Selbstschutz: schlägt der Check hier fehl, ist der AST-Scan kaputt, nicht der Code.
    assert risky_functions, (
        "Erwartet mindestens eine Funktion in astronomy.py, die _get_eph() direkt "
        "aufruft (z.B. get_moon_earth_distance_km) — der Scan selbst liefert nichts."
    )

    test_source = _REGRESSION_TEST_FILE.read_text(encoding="utf-8")
    offline_tests = _offline_marked_tests(test_source)

    offenders = []
    for name, src in offline_tests.items():
        for fn in risky_functions:
            if f"A.{fn}(" in src:
                offenders.append((name, fn))

    assert not offenders, (
        "Folgende @pytest.mark.offline-Tests rufen einen bekannten _get_eph()-Pfad "
        f"auf (Marker-Widerspruch, BUG-79 AK4): {offenders}"
    )
