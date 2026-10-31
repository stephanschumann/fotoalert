"""TASK-117 · AK5/AK10 — Oberflächen-Check und Browser-Tests sehen im Probelauf einen leeren Datenbestand,
auch wenn der Backend-Block vorher in derselben Prüfkopie Testdaten angelegt hat.

Befund (Analyse 30.10.2026, von Stephan am 31.10.2026 als in TASK-117 zu behebender Fehler bestätigt): Im
Mac-Probelauf laufen alle Prüfblöcke nacheinander in EINER sauberen Kopie. Der Backend-Block legt dabei über
die Testumgebung (Entwicklungsumgebung, Datenablage der Kopie) eigene Orte und Korrekturen an; danach startet
der Testserver für Oberflächen-Check und Browser-Tests auf genau diesen Daten (Server-Log des Probelaufs vom
30.10.: „Custom Locations geladen: 5“, „Overrides: 3“). Bei GitHub laufen die Blöcke auf getrennten Rechnern,
der Testserver startet dort mit 0 eigenen Orten. AK5 („Probelauf startet mit leerem Datenbestand wie bei
GitHub“) und AK10 („dieselben Prüfungen wie bei GitHub“) sind damit verletzt; TF-05 verlangt zusätzlich, dass
die Ortszahl im Probelauf protokolliert wird.

Geschrieben VOR der Umsetzung (fotoalert-test Teil A). Testfall-ID TF-05a ist ein Vorschlag dieses
Test-Agenten (automatisierter Teil von TF-05; TF-05 selbst bleibt der Messlauf auf Stephans Mac).

WAS ECHT IST UND WAS PLATZHALTER: Geprüft wird die ECHTE gemeinsame Prüfliste (Kopie von
FotoAlert/tools/pruefliste.sh samt ihrem Plugin) mit dem ECHTEN Datenspeicher (Kopie von
backend/data/store.py, er wählt die Datenablage wie die App nach der Umgebung). Ersetzt sind nur:
  • die Backend-Tests durch EINEN Platzhalter-Test, der — wie die echte Testumgebung (Entwicklungsumgebung als
    Vorgabe) — 5 eigene Orte und 3 Korrekturen in der Datenablage der Kopie anlegt,
  • der App-Server durch einen Platzhalter, der beim Start wie die App die Daten aus dem Datenspeicher lädt,
    dieselben Log-Zeilen schreibt und über /health die Gesamtzahl der Orte meldet (der Platzhalter hat keine
    fest eingebauten Orte, Gesamtzahl = eigene Orte),
  • Oberflächen-Check und die drei Browser-Testdateien durch Platzhalter, die nur notieren, welchen
    Datenbestand der Testserver ihnen zeigt (sie schreiben nichts in die Ausgabe der Prüfliste),
  • das Browser-Werkzeug durch einen Versionseintrag in genau der fest eingestellten Version.
Alles liegt in einer Wegwerf-Kopie im pytest-Temp-Ordner (außerhalb des Projekts), wird nach dem Test immer
gelöscht (auch bei Fehlschlag) und braucht kein Git. Wiederverwendet aus task117_adapter.py (unverändert):
Projektpfade, Ergebnis-Anzeige, Aufräum-Netz.

Erwartete Werte (unabhängige Quellen): 0 eigene Orte und 0 Korrekturen — Spec AK5/TF-05 („Ortszahl im
Probelauf protokolliert = 0“) und GitHub-Prüfbeschreibung (getrennte Jobs/Rechner, frischer Checkout ohne
Daten). 5 Orte / 3 Korrekturen als Vorbedingung — Server-Log des Probelaufs vom 30.10.2026, Zeilen 6/7.
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys

import pytest

from task117_adapter import (
    BACKEND_DIR,
    PRUEFLISTE_RELPFAD,
    REPO_ROOT,
    Ergebnis,
    _OFFENE_ABLAGEN,
    _OFFENE_PROZESSE,
    _beende_prozessgruppe,
    _liegt_in,
    _loesche,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

# ════════════════════════════════════════════════════════════════════════════
# Unterbau (nur in dieser Datei)
# ════════════════════════════════════════════════════════════════════════════
ANGELEGTE_ORTE = 5          # Server-Log Probelauf 30.10.2026, Z. 6
ANGELEGTE_KORREKTUREN = 3   # Server-Log Probelauf 30.10.2026, Z. 7
ERWARTET_ORTE = 0           # Spec AK5/TF-05, GitHub: getrennte Rechner
ERWARTET_KORREKTUREN = 0
BROWSER_TESTDATEIEN = ("test_bug_85.py", "test_bug-80.py", "test_task-66.py")   # Block Browser-Tests
ZEITLIMIT_S = 170

# Ortszahl-Zeile: die Zahl steht unmittelbar am Ortswort — „<n> Orte“ / „<n> eigene Orte“ oder
# „Orte: <n>“ / „eigene Orte: <n>“ / „Ortszahl: <n>“ — als eigenständige Zahl („Port“ zählt nicht: Wortgrenze).
_ORTSWORT = r"(?:eigene\s+)?(?:orte?|standorte?|locations?)"


def _nennt_ortszahl(zeile, n):
    vorn = r"(?<![\w.])%d\s+%s\b" % (n, _ORTSWORT)
    hinten = r"\b(?:%s|ortszahl)\s*[:=]\s*%d(?![\w.])" % (_ORTSWORT, n)
    return re.search(r"(?i)" + vorn, zeile) is not None or re.search(r"(?i)" + hinten, zeile) is not None

_CONFTEST = '''"""Platzhalter-Testumgebung (TASK-117 AK5): wie die echte conftest.py — Entwicklungsumgebung als Vorgabe."""
import os
import sys
from pathlib import Path

os.environ.setdefault("FOTOALERT_ENV", "dev")
sys.path.insert(0, str(Path(__file__).resolve().parent))
'''

_BACKEND_TEST = '''"""Platzhalter der Backend-Tests (TASK-117 AK5): legt wie die echten Tests Daten in der Datenablage an."""
import os

from data.store import LocationStore


def test_backend_block_legt_testdaten_an():
    s = LocationStore()
    for i in range(__ORTE__):
        s.create_custom_if_not_exists({
            "id": "t117_platzhalter_%d" % i, "name": "Platzhalter %d" % i,
            "observer_lat": 52.4 + i / 100, "observer_lon": 13.0, "subject_lat": 52.41, "subject_lon": 13.01,
        })
    for i in range(__KORREKTUREN__):
        s.upsert_override("t117_platzhalter_%d" % i, name="Platzhalter korrigiert %d" % i)
    with open(os.environ["T117_BERICHT"], "a", encoding="utf-8") as fh:
        fh.write("BACKEND eigene=%d korrekturen=%d umgebung=%s ablage=%s\\n" % (
            len(s.load_all_custom()), len(s.load_all_overrides()), os.environ.get("FOTOALERT_ENV"), s.db_path))
'''

_SERVER = '''"""Platzhalter des App-Servers (TASK-117 AK5): lädt beim Start wie die App die Daten aus dem Datenspeicher."""
import json

from data.store import LocationStore

_store = LocationStore()
_EIGENE = len(_store.load_all_custom())
_KORREKTUREN = len(_store.load_all_overrides())
print("LocationStore initialisiert: %s" % _store.db_path, flush=True)
if _EIGENE:
    print("Custom Locations geladen: %d Einträge aus SQLite" % _EIGENE, flush=True)
if _KORREKTUREN:
    print("Location Overrides geladen: %d Einträge aus SQLite" % _KORREKTUREN, flush=True)


async def app(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            m = await receive()
            if m["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif m["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
    if scope["type"] != "http":
        return
    if scope["path"] == "/health":
        inhalt, code = {"status": "ok", "version": "platzhalter", "locations_count": _EIGENE}, 200
    elif scope["path"] == "/platzhalter/datenbestand":
        inhalt, code = {"eigene": _EIGENE, "korrekturen": _KORREKTUREN}, 200
    else:
        inhalt, code = {"detail": "Not Found"}, 404
    await send({"type": "http.response.start", "status": code,
                "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": json.dumps(inhalt).encode()})
'''

_NOTIZ = '''
def _notiere(art, basis):
    import json, os, urllib.request
    try:
        with urllib.request.urlopen(basis.rstrip("/") + "/platzhalter/datenbestand", timeout=5) as r:
            d = json.load(r)
    except OSError:
        return False          # kein Testserver erreichbar (z. B. im Backend-Block)
    with open(os.environ["T117_BERICHT"], "a", encoding="utf-8") as fh:
        fh.write("%s eigene=%d korrekturen=%d\\n" % (art, d["eigene"], d["korrekturen"]))
    return True
'''

_OBERFLAECHEN_CHECK = '"""Platzhalter Oberflächen-Check (TASK-117 AK5)."""\nimport sys\n' + _NOTIZ + '''

if __name__ == "__main__":
    basis = sys.argv[sys.argv.index("--base-url") + 1]
    sys.exit(0 if _notiere("OBERFLAECHE", basis) else 3)
'''

_BROWSER_TEST = '"""Platzhalter Browser-Testdatei (TASK-117 AK5)."""\nimport os\n' + _NOTIZ + '''

def test_platzhalter_browserpruefung():
    _notiere("BROWSER __DATEI__", os.environ.get("FOTOALERT_TEST_BASE_URL", "http://127.0.0.1:9"))
'''


def _freier_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _baue_pruefkopie(kopie):
    """Wegwerf-Kopie mit der echten Prüfliste, dem echten Datenspeicher und den Platzhaltern."""
    proj = kopie / "FotoAlert"
    tools, backend = proj / "tools", proj / "backend"
    tools.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / PRUEFLISTE_RELPFAD, tools / "pruefliste.sh")
    shutil.copytree(REPO_ROOT / "FotoAlert/tools/pruefliste_plugin", tools / "pruefliste_plugin",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (backend / "data").mkdir(parents=True)
    for rel in ("data/__init__.py", "data/store.py", "requirements-browser.txt"):
        shutil.copy2(BACKEND_DIR / rel, backend / rel)
    (backend / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n", encoding="utf-8")
    (backend / "conftest.py").write_text(_CONFTEST, encoding="utf-8")
    (backend / "main.py").write_text(_SERVER, encoding="utf-8")
    (backend / "tests" / "frontend").mkdir(parents=True)
    (backend / "tests" / "test_platzhalter_backend.py").write_text(
        _BACKEND_TEST.replace("__ORTE__", str(ANGELEGTE_ORTE))
        .replace("__KORREKTUREN__", str(ANGELEGTE_KORREKTUREN)), encoding="utf-8")
    (backend / "tests" / "frontend" / "run_frontend_check.py").write_text(_OBERFLAECHEN_CHECK, encoding="utf-8")
    for name in BROWSER_TESTDATEIEN:
        (backend / "tests" / name).write_text(_BROWSER_TEST.replace("__DATEI__", name), encoding="utf-8")
    # Browser-Werkzeug in genau der fest eingestellten Version (nur Versionseintrag, kein Browser).
    soll = re.search(r"playwright==([0-9][0-9A-Za-z.]*)",
                     (backend / "requirements-browser.txt").read_text(encoding="utf-8"))
    assert soll, "Vorbereitung: fest eingestellte Version des Browser-Werkzeugs nicht gefunden"
    eintrag = kopie.parent / "werkzeug" / f"playwright-{soll.group(1)}.dist-info"
    eintrag.mkdir(parents=True)
    (eintrag / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: playwright\nVersion: {soll.group(1)}\n", encoding="utf-8")
    return eintrag.parent


def _pruefliste_laufen_lassen(kopie, werkzeug, ablage, bericht):
    """Ruft die Prüfliste der Kopie so auf wie der Probelauf des Release-Befehls (alle drei Blöcke)."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("FOTOALERT_", "PRUEFLISTE_", "PYTEST_"))}
    env.update({
        "PRUEFLISTE_PYTHON": sys.executable,
        "PRUEFLISTE_PORT": str(_freier_port()),
        "PRUEFLISTE_ABLAGE": str(ablage),
        "PYTHONPATH": str(werkzeug),
        "PYTHONDONTWRITEBYTECODE": "1",
        "T117_BERICHT": str(bericht),
    })
    proc = subprocess.Popen(["bash", str(kopie / PRUEFLISTE_RELPFAD)], cwd=kopie, env=env,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            start_new_session=True)
    _OFFENE_PROZESSE.append(proc)
    try:
        out, _ = proc.communicate(timeout=ZEITLIMIT_S)
    except subprocess.TimeoutExpired:
        _beende_prozessgruppe(proc)
        pytest.fail(f"Prüfliste endete nicht innerhalb von {ZEITLIMIT_S} s (hart beendet).")
    finally:
        _beende_prozessgruppe(proc)
    return Ergebnis(proc.returncode, out.decode("utf-8", errors="replace"))


def _notizen(bericht, art):
    """Notizen der Platzhalter einer Art als Liste von {Schlüssel: Wert, 'zeile': Rohzeile}."""
    if not bericht.exists():
        return []
    aus = []
    for z in bericht.read_text(encoding="utf-8").splitlines():
        if z.startswith(art + " "):
            d = dict(t.split("=", 1) for t in z.split()[1:] if "=" in t)
            d["zeile"] = z
            aus.append(d)
    return aus


@pytest.fixture
def pruefkopie(tmp_path):
    """Wegwerf-Kopie im pytest-Temp-Ordner; wird im Teardown IMMER gelöscht."""
    basis = tmp_path / "t117_ak5"
    assert not _liegt_in(basis, REPO_ROOT), f"Wegwerf-Kopie {basis} läge im Projekt — abgebrochen"
    _OFFENE_ABLAGEN.add(basis)
    try:
        yield basis
    finally:
        for proc in list(_OFFENE_PROZESSE):
            _beende_prozessgruppe(proc)
        _loesche(basis)
        _OFFENE_ABLAGEN.discard(basis)
    assert not basis.exists(), f"Wegwerf-Kopie {basis} blieb nach dem Test liegen"


# ════════════════════════════════════════════════════════════════════════════
# Testfall
# ════════════════════════════════════════════════════════════════════════════

def test_tf05a_ak5_ak10_testserver_sieht_trotz_backend_testdaten_leeren_datenbestand(pruefkopie):
    """TASK-117 · TF-05a · AK5, AK10 — *Prüfkopie ohne Daten* und *der Backend-Block legt darin 5 eigene Orte
    und 3 Korrekturen an* → *Probelauf läuft alle drei Prüfblöcke nacheinander in derselben Kopie* →
    *Oberflächen-Check und Browser-Tests sehen einen leeren Datenbestand (0 eigene Orte, 0 Korrekturen) wie bei
    GitHub*; *die Ausgabe des Probelaufs nennt die Ortszahl des Testservers (0)*.
    Quelle der Erwartung: Spec AK5/TF-05, GitHub-Prüfbeschreibung (getrennte Rechner je Job)."""
    kopie = pruefkopie / "kopie"
    ablage, bericht = pruefkopie / "ablage", pruefkopie / "bericht.txt"
    werkzeug = _baue_pruefkopie(kopie)
    erg = _pruefliste_laufen_lassen(kopie, werkzeug, ablage, bericht)
    server_log = ablage / "fotoalert-ci-server.log"
    log = server_log.read_text(encoding="utf-8", errors="replace") if server_log.exists() else "(kein Server-Log)"

    def zeige(grund):
        notizen = bericht.read_text(encoding="utf-8") if bericht.exists() else "(keine)"
        return (erg.zeige(grund) + "\n— Notizen der Platzhalter:\n" + notizen
                + "\n— Server-Log:\n" + "\n".join(log.splitlines()[:15]))

    # Vorbedingung: Der Backend-Block hat in derselben Kopie wirklich Daten angelegt.
    backend = _notizen(bericht, "BACKEND")
    assert backend and int(backend[-1]["eigene"]) == ANGELEGTE_ORTE \
        and int(backend[-1]["korrekturen"]) == ANGELEGTE_KORREKTUREN, zeige(
            "Vorbedingung nicht erfüllt: Der Backend-Block hat in der Prüfkopie keine Testdaten angelegt")

    # Oberflächen-Check und Browser-Tests haben den Testserver erreicht.
    oberflaeche = _notizen(bericht, "OBERFLAECHE")
    browser = _notizen(bericht, "BROWSER")
    assert oberflaeche, zeige("Befund: Der Oberflächen-Check hat den Testserver nie erreicht")
    assert sorted(b["zeile"].split()[1] for b in browser) == sorted(BROWSER_TESTDATEIEN), zeige(
        "Befund: Nicht alle Browser-Testdateien haben den Testserver erreicht")

    # Kern von AK5/AK10: leerer Datenbestand wie bei GitHub.
    for n in oberflaeche + browser:
        orte, korrekturen = int(n["eigene"]), int(n["korrekturen"])
        assert (orte, korrekturen) == (ERWARTET_ORTE, ERWARTET_KORREKTUREN), zeige(
            f"Befund: Der Testserver für Oberflächen-Check und Browser-Tests sah die Testdaten des Backend-Blocks "
            f"({orte} eigene Orte, {korrekturen} Korrekturen) statt eines leeren Datenbestands wie bei GitHub "
            f"(erwartet {ERWARTET_ORTE} eigene Orte, {ERWARTET_KORREKTUREN} Korrekturen)")

    # TF-05: Ortszahl des Testservers steht in der Ausgabe des Probelaufs.
    assert any(_nennt_ortszahl(z, ERWARTET_ORTE) for z in erg.ausgabe.splitlines()), zeige(
        f"Befund: Die Ausgabe des Probelaufs nennt nicht, wie viele Orte der Testserver geladen hat "
        f"(erwartet eine Zeile mit der Ortszahl {ERWARTET_ORTE})")
