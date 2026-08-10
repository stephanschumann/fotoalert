"""TASK-96: Automatisierter Konsistenz-Test fuer den Marker `requires_full_checkout`.

Hintergrund: `offline` bedeutet nur "deterministisch, ohne Netzwerk/externe Dienste" -
es garantiert NICHT, dass ein Test auch bei einem Teil-Checkout laeuft, der nur
`backend/` enthaelt (z.B. CI-Job oder Sandbox-Abzug mit schmaler Datei-Auswahl). Sechs
Testdateien loesen Pfade relativ zum Repo-Root ausserhalb von `backend/` auf (`web/`,
`deploy/`, `tools/`, `docs/`) und brechen deshalb bei einem Backend-only-Checkout, obwohl
sie als `offline`/`frontend` markiert sind: `test_task84.py`,
`test_task89_caddy_log_permissions.py`, `test_us105_section_order.py`,
`test_us79_moon_rise_set.py` (verifiziert in der TASK-96-Analyse, 2026-08-09/10),
`test_task53_dev_sync.py`, `test_task-66.py` (nachtraeglich per Verifikations-Review am
2026-08-10 gefunden - die urspruengliche Heuristik unten erkannte nur `web`/`deploy`,
nicht `tools`/`docs`).

Dieser Test:
  1. Scannt alle *.py-Dateien in backend/tests/ heuristisch danach, ob sie einen
     Path-Join mit dem Literal "web" oder "deploy" enthalten (= Repo-Root-Abhaengigkeit
     ausserhalb von backend/, wo es diese Verzeichnisse nicht gibt).
  2. Prueft, dass jede so gefundene Datei den Marker `requires_full_checkout` traegt
     (Modul-`pytestmark` oder Funktionsdekorator) - schuetzt kuenftige, strukturell
     gleiche Testdateien davor, unbemerkt unmarkiert zu bleiben (Pre-Mortem-Szenario D
     der TASK-96-Analyse).
  3. Prueft die vier konkret bekannten Faelle explizit (Positivkontrolle).
  4. Prueft die Erkennungslogik selbst gegen synthetische Beispiel-Quelltexte, damit die
     Fehlermeldung im echten Verstossfall nachweislich aussagekraeftig ist (AK4:
     Negativfall-Fehlermeldung) und der Test nicht nur zufaellig gruen ist, weil gerade
     kein realer Verstoss existiert.

Analog zum TASK-79-Muster (`test_task79_readme_marker_sync.py`), das die README-
Tabellen-Vollstaendigkeit gegen alle vorhandenen Testdateien absichert - hier wird
stattdessen die Marker-Konsistenz gegen die tatsaechliche Pfadaufloesung im Quelltext
jeder Testdatei automatisiert abgesichert.
"""

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]

TESTS_DIR = Path(__file__).parent
THIS_FILE = Path(__file__).name

# Im TASK-96-Ticket verifizierte Faelle (Positivkontrolle in
# test_known_full_checkout_file_carries_marker unten). Diese Liste ist bewusst kein
# Ersatz fuer die generische Heuristik in test_no_test_file_escapes_backend_without_the_marker
# - sie dient nur als zusaetzlicher, expliziter Nachweis fuer die vier konkret bekannten Dateien.
KNOWN_FULL_CHECKOUT_FILES = {
    "test_task84.py",
    "test_task89_caddy_log_permissions.py",
    "test_us105_section_order.py",
    "test_us79_moon_rise_set.py",
    "test_task53_dev_sync.py",
    "test_task-66.py",
}

# Heuristik: ein Path-Join mit dem String-Literal "web", "deploy", "tools" oder "docs"
# (in beide Richtungen, da pathlib's `/`-Operator in beide Reihenfolgen auftauchen kann)
# deutet auf einen Pfad hin, der ausserhalb von backend/ aufgeloest wird - dort
# existieren keine gleichnamigen Verzeichnisse. Erweitert am 2026-08-10 (Verifikations-
# Review TASK-96) um "tools"/"docs", nachdem test_task53_dev_sync.py (sys.path-Import aus
# Repo-Root-tools/) und test_task-66.py (Screenshot-Pfad unter Repo-Root-docs/) als real
# unmarkierte Faelle derselben Fehlerklasse gefunden wurden - die Heuristik bleibt eine
# feste Literal-Liste, kein Ersatz fuer eine vollstaendige Analyse jeder neuen Datei.
_ESCAPES_BACKEND_RE = re.compile(
    r"""["'](?:web|deploy|tools|docs)["']\s*/|/\s*["'](?:web|deploy|tools|docs)["']"""
)


def _escapes_backend(source: str) -> bool:
    return bool(_ESCAPES_BACKEND_RE.search(source))


def _has_requires_full_checkout_marker(source: str) -> bool:
    return "requires_full_checkout" in source


def _all_test_file_sources():
    """Liefert {dateiname: quelltext} fuer alle *.py-Dateien in backend/tests/,
    ausser dieser Datei selbst (die die Markernamen nur textuell referenziert)."""
    sources = {}
    for path in sorted(TESTS_DIR.glob("*.py")):
        if path.name == THIS_FILE:
            continue
        sources[path.name] = path.read_text(encoding="utf-8")
    return sources


def test_requires_full_checkout_marker_is_registered_in_pytest_ini():
    """Der Marker muss in pytest.ini registriert sein, sonst warnt pytest bei jedem Lauf
    (PytestUnknownMarkWarning) - Marker werden in diesem Projekt in pytest.ini
    registriert, nicht in conftest.py."""
    pytest_ini = TESTS_DIR.parent / "pytest.ini"
    assert pytest_ini.exists(), f"{pytest_ini} nicht gefunden"
    ini_source = pytest_ini.read_text(encoding="utf-8")
    assert re.search(r"^\s*requires_full_checkout\s*:", ini_source, re.MULTILINE), (
        "Marker 'requires_full_checkout' ist nicht in pytest.ini registriert."
    )


@pytest.mark.parametrize("filename", sorted(KNOWN_FULL_CHECKOUT_FILES))
def test_known_full_checkout_file_carries_marker(filename):
    """Positivkontrolle: die vier im TASK-96-Ticket verifizierten Dateien tragen den
    Marker tatsaechlich."""
    path = TESTS_DIR / filename
    assert path.exists(), f"{path} nicht gefunden - TASK-96-Referenzdatei fehlt/umbenannt"
    source = path.read_text(encoding="utf-8")
    assert _has_requires_full_checkout_marker(source), (
        f"{filename} loest laut TASK-96-Analyse Pfade ausserhalb von backend/ auf, "
        f"traegt aber nicht den Marker 'requires_full_checkout'."
    )


def test_no_test_file_escapes_backend_without_the_marker():
    """Kernabsicherung (Pre-Mortem-Szenario D): jede Testdatei, die per Heuristik einen
    Pfad ausserhalb von backend/ aufloest (Path-Join mit "web"/"deploy"), muss den
    Marker 'requires_full_checkout' tragen - auch kuenftige, noch nicht existierende
    Testdateien mit derselben Struktur werden dadurch automatisch erfasst, nicht nur
    die vier aktuell bekannten Faelle."""
    unmarked_violations = sorted(
        filename
        for filename, source in _all_test_file_sources().items()
        if _escapes_backend(source) and not _has_requires_full_checkout_marker(source)
    )

    assert not unmarked_violations, (
        "Folgende Testdateien loesen Pfade ausserhalb von backend/ auf (web/, deploy/), "
        f"tragen aber nicht den Marker 'requires_full_checkout': {unmarked_violations}. "
        "Diese Tests brechen bei einem Teil-Checkout, der nur backend/ enthaelt, obwohl "
        "sie evtl. als 'offline' markiert sind - siehe backend/tests/README.md, "
        "Abschnitt zum Marker 'requires_full_checkout' (TASK-96)."
    )


def test_detection_heuristic_flags_a_synthetic_unmarked_violation():
    """Negativfall (AK4): die Erkennungslogik selbst muss einen offensichtlichen
    Verstoss klar erkennen - unabhaengig davon, ob im echten Repo gerade zufaellig kein
    unmarkierter Fall existiert. Das haelt test_no_test_file_escapes_backend_without_the_marker
    aussagekraeftig, statt trivial immer gruen zu sein, nur weil KNOWN_FULL_CHECKOUT_FILES
    aktuell vollstaendig gepflegt ist."""
    synthetic_violation_source = (
        "from pathlib import Path\n"
        "ROOT = Path(__file__).parent.parent.parent\n"
        "INDEX = ROOT / \"web\" / \"index.html\"\n"
    )
    synthetic_marked_source = (
        "from pathlib import Path\n"
        "import pytest\n"
        "pytestmark = [pytest.mark.offline, pytest.mark.requires_full_checkout]\n"
        "ROOT = Path(__file__).parent.parent.parent\n"
        "INDEX = ROOT / \"web\" / \"index.html\"\n"
    )
    synthetic_backend_only_source = (
        "from pathlib import Path\n"
        "HERE = Path(__file__).parent\n"
        "CONFIG = HERE / \"fixtures\" / \"config.json\"\n"
    )

    assert _escapes_backend(synthetic_violation_source), (
        "Erkennungslogik haette den Repo-Root-Pfad im synthetischen Verstoss-Beispiel "
        "erkennen muessen (Path-Join mit 'web')."
    )
    assert not _has_requires_full_checkout_marker(synthetic_violation_source), (
        "Testaufbau-Fehler: das Verstoss-Beispiel sollte den Marker NICHT enthalten."
    )

    assert not (
        _escapes_backend(synthetic_marked_source)
        and not _has_requires_full_checkout_marker(synthetic_marked_source)
    ), "Erkennungslogik haette dieses synthetisch markierte Beispiel nicht als Verstoss werten duerfen."

    assert not _escapes_backend(synthetic_backend_only_source), (
        "Erkennungslogik haette dieses rein backend-interne Beispiel nicht als "
        "Repo-Root-Abhaengigkeit werten duerfen (kein 'web'/'deploy'-Pfadsegment)."
    )


def test_readme_documents_requires_full_checkout_marker():
    """AK: README-Abschnitt 'Schichten' erklaert, dass 'offline' NICHT teil-checkout-faehig
    bedeutet, und dokumentiert den neuen Marker 'requires_full_checkout'."""
    readme = (TESTS_DIR / "README.md").read_text(encoding="utf-8")
    assert "requires_full_checkout" in readme, (
        "backend/tests/README.md dokumentiert den Marker 'requires_full_checkout' nicht."
    )
    assert "Teil-Checkout" in readme or "teil-checkout" in readme.lower(), (
        "backend/tests/README.md erklaert nicht, dass 'offline' und Teil-Checkout-Faehigkeit "
        "zwei unabhaengige Eigenschaften sind (TASK-96, AK2)."
    )
