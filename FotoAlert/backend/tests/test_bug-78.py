"""BUG-78 — Koordinaten-Eingabefeld "Mein Standort (Fotograf)" akzeptiert kein
Apple-Maps-Format (deutsche Lokalisierung).

Root Cause (verifiziert 2026-07-14, siehe BACKLOG.md Analyse-Section BUG-78):
Das Feld "Mein Standort (Fotograf)" (id="obs-coords") im "Neue Location"-Sheet
und das Feld "Motiv" (id="subj-coords") nutzen beide die gemeinsame
Parse-Funktion `AddLocation._parseCoords(text)` in web/index.html, Zeile
6946-6965. Diese Funktion erkennt aktuell nur zwei Formate:
  1. Dezimalgrad mit Punkt als Trennzeichen ("52.4, 13.1")
  2. DMS mit Grad/Minute/Sekunde und N/S/E/W (52°30'44.4"N, ...)
Das von Apple Maps (deutsche Lokalisierung) gelieferte Format
("46,64770° N, 11,71666° O" — Komma als Dezimaltrennzeichen, ° direkt am
Wert, ausgeschriebene Himmelsrichtung inkl. deutschem "O" für Ost) fällt in
keinen der beiden Zweige und wird daher komplett abgelehnt.

Kein Backend-Test möglich: Das Parsing ist rein clientseitig in
web/index.html (`AddLocation._parseCoords()`, JavaScript). Es gibt in der
aktuellen Backend-Test-Infrastruktur (siehe backend/pytest.ini, Marker
"frontend") keinen Ausführungspfad für isolierte JS-Funktionsaufrufe ohne
echten Browser — die vorhandenen `frontend`-Marker-Tests in
backend/tests/frontend/ (z.B. run_frontend_check.py, spec.py) prüfen echte
Browser-Klickpfade per Playwright gegen einen laufenden Server, nicht
einzelne JS-Funktionen in Isolation. Ein Python-Test, der die Regex-Logik
von _parseCoords() nachbaut, würde die Implementierung duplizieren statt
die Spec zu testen (Schritt 6b: "Testet gegen die Spec, nicht gegen die
Implementierung") — und wäre zudem an eine der beiden noch offenen
Implementierungsoptionen (Normalisierung vs. dritter Regex-Zweig, siehe
BACKLOG.md) gebunden, die erst nach dem Weg-Gate feststeht.

Diese Datei dokumentiert das bewusst als übersprungenen Platzhalter statt
einen Test zu erzwingen, der ohne echte JS-Ausführung nichts prüfen würde
(siehe fotoalert-analyze Skill, Schritt 6b / Testplan-Regel).

Manueller Testplan (siehe BACKLOG.md BUG-78 -> Testplan -> Manuell) deckt
AK-1 bis AK-6 unter http://localhost:8000 ab.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.frontend, pytest.mark.regression]


@pytest.mark.skip(
    reason=(
        "BUG-78: Parsing ist rein clientseitig (web/index.html, "
        "AddLocation._parseCoords()) — kein Node/Playwright-Ausführungspfad "
        "fuer isolierte JS-Funktionsaufrufe in der Backend-Test-Infrastruktur "
        "vorhanden. AKs werden manuell unter http://localhost:8000 getestet "
        "(siehe BACKLOG.md BUG-78 -> Testplan -> Manuell, Schritte 1-8)."
    )
)
def test_apple_maps_format_accepted_manual_only():
    """BUG-78 AK-1/AK-2: Apple-Maps-Format ("46,64770° N, 11,71666° O") wird
    akzeptiert und korrekt in Dezimalgrad (inkl. Vorzeichen bei S/W)
    umgewandelt.

    Kann nicht automatisiert gegen den Backend-Stack getestet werden, da
    kein Server-Endpoint beteiligt ist — die Konvertierung passiert
    vollstaendig im Browser, bevor irgendein POST/PATCH an den Server geht.
    """
    raise AssertionError(
        "Sollte nie ausgefuehrt werden (skip-marker) — siehe Docstring/Testplan."
    )
