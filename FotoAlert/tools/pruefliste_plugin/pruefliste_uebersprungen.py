"""pytest-Plugin der gemeinsamen Prüfliste (TASK-117, AK9a) — ändert keinen Test, meldet nur.

Schreibt jeden übersprungenen Test (auch ganze, beim Sammeln übersprungene Testdateien) als Zeile
„<Test-ID><TAB><Grund>“ in die Datei aus der Umgebungsvariable PRUEFLISTE_UEBERSPRUNGEN_DATEI.
Die Prüfliste (tools/pruefliste.sh) macht daraus die Zeilen
„PRUEFLISTE block=<kennung> uebersprungen_test=<Test-ID> grund=<Grund>“, die release.sh gegen
die feste Liste tools/bekannte_uebersprungene_tests.txt prüft. Python-3.9-kompatibel.
"""
import os


def _grund(report):
    lr = report.longrepr
    text = str(lr[2]) if isinstance(lr, tuple) and len(lr) == 3 else str(lr)
    if text.startswith("Skipped: "):
        text = text[len("Skipped: "):]
    return " ".join(text.split())


def _melde(report):
    ziel = os.environ.get("PRUEFLISTE_UEBERSPRUNGEN_DATEI")
    if not ziel or not report.skipped or hasattr(report, "wasxfail"):
        return
    with open(ziel, "a", encoding="utf-8") as fh:
        fh.write("%s\t%s\n" % (report.nodeid, _grund(report)))


def pytest_runtest_logreport(report):
    if report.when in ("setup", "call"):
        _melde(report)


def pytest_collectreport(report):
    _melde(report)
