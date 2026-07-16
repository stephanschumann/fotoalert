"""US-133 — Kartenausschnitt springt bei Koordinaten-Eingabe zur eingegebenen Position.

Hintergrund (siehe BACKLOG.md US-133, Pre-Mortem + Code-Verifikation 2026-07-16):
Beim Anlegen einer neuen Location oder Bearbeiten einer bestehenden Location
aktualisiert die kleine Formular-Karte (Leaflet) zwar den Pin, sobald gültige
Koordinaten eingegeben werden, verschiebt aber den sichtbaren Kartenausschnitt
nicht mit. Weg-Gate-Entscheidung (Stephan, 2026-07-16): Frage 1 (Zoomstufe) =
Option B (aktueller Zoom bleibt erhalten, nur `panTo`), Frage 2 (Zeitpunkt) =
Option B (erst beim Verlassen des Feldes/Blur, nicht live beim Tippen) — beide
gegen die ursprüngliche Empfehlung (Option A/A = live + feste Zoomstufe 14).

Implementiert wurden 4 neue Blur-Handler-Methoden in `web/index.html`:
  - `AddLocation._onObsBlur()`  — Anlegen, Feld "Mein Standort" (Fotograf)
  - `AddLocation._onSubjBlur()` — Anlegen, Feld "Motiv"
  - `LocationDetail._onEditObsBlur()`  — Bearbeiten, Feld "Fotograf-Standort"
  - `LocationDetail._onEditSubjBlur()` — Bearbeiten, Feld "Motiv (Koordinaten)"
Jeder Handler ruft bei vollständiger, gültiger Koordinate `map.panTo([lat,lng])`
auf der jeweiligen kleinen Formular-Karte auf (`AddLocation.map` bzw.
`LocationDetail._editMap`) — ohne Zoom-Änderung. `oninput` bleibt unverändert
nur für das Marker-Update zuständig (Pre-Mortem Szenario 2 entfällt dadurch
strukturell, siehe BACKLOG.md).

Kein Backend-Test möglich: Das Verhalten ist rein clientseitig in
web/index.html (Leaflet `map.panTo()`/`getCenter()`/`getZoom()`, JavaScript).
Es gibt in der aktuellen Backend-Test-Infrastruktur (siehe backend/pytest.ini,
Marker "frontend") keinen Ausführungspfad für isolierte JS-Funktionsaufrufe
ohne echten Browser. Ein Playwright-basierter Test (analog zum etablierten
Muster in `backend/tests/test_bug-80.py`, das per `page.evaluate()`
clientseitigen Kartenzustand vor/nach einem simulierten Blur-Event vergleicht)
wäre technisch möglich, ist aber laut Testplan (BACKLOG.md US-133 ->
Testplan -> Automatisiert) noch nicht als eigener Aufwand nachgezogen worden.
Ein Python-Test, der die Blur-/`panTo`-Logik nachbaut, würde die
Implementierung duplizieren statt die Spec zu testen (Schritt 6b: "Testet
gegen die Spec, nicht gegen die Implementierung").

Diese Datei dokumentiert das bewusst als übersprungenen Platzhalter statt
einen Test zu erzwingen, der ohne echte JS-Ausführung nichts prüfen würde
(siehe fotoalert-analyze Skill, Schritt 6b / Testplan-Regel; analoges Muster
bereits etabliert in test_bug-78.py).

Manueller Testplan (siehe BACKLOG.md US-133 -> Testplan -> Manuell) deckt
AK1 bis AK9 unter http://localhost:8000 ab. Laut Stephan (2026-07-16) wurden
alle 9 Akzeptanzkriterien manuell im Browser getestet und positiv bestätigt.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.frontend, pytest.mark.regression]


@pytest.mark.skip(
    reason=(
        "US-133: Kartenschwenk bei Koordinaten-Eingabe ist rein clientseitig "
        "(web/index.html, AddLocation._onObsBlur/_onSubjBlur, "
        "LocationDetail._onEditObsBlur/_onEditSubjBlur) — kein Playwright-"
        "Ausführungspfad in der Backend-Test-Infrastruktur vorhanden. AKs "
        "wurden manuell unter http://localhost:8000 getestet und am "
        "2026-07-16 positiv bestätigt (siehe BACKLOG.md US-133 -> Testplan -> "
        "Manuell, Schritte 1-7)."
    )
)
def test_map_pans_on_coordinate_field_blur_manual_only():
    """US-133 AK1-AK9: Formular-Karte schwenkt beim Verlassen (Blur) eines
    vollständig eingetippten, gültigen Koordinatenfelds automatisch zur neuen
    Position — Zoomstufe bleibt dabei unverändert; ungültige/leere Eingaben
    lösen keinen Schwenk aus; bestehende Kartenwege bleiben unverändert.

    Kann nicht automatisiert gegen den Backend-Stack getestet werden, da kein
    Server-Endpoint beteiligt ist — die Kartenzentrierung (Leaflet `panTo()`)
    passiert vollständig im Browser, ohne jeden POST/PATCH an den Server.

    Manuelle Testschritte (siehe BACKLOG.md US-133 -> Testplan -> Manuell,
    identisch dokumentiert für eine spätere Playwright-Umstellung):
      1. AK1: Anlegen-Formular öffnen ("+"-Button) -> Feld "Mein Standort"
         mit einer weit entfernten, gültigen Koordinate füllen (z. B.
         "48.8566, 2.3522" für Paris) -> Feld verlassen (Blur) -> erwartet:
         kleine Karte schwenkt automatisch auf Paris, Pin sichtbar, Zoomstufe
         unverändert.
      2. AK2: Gleiches im Feld "Motiv" mit einer anderen weit entfernten
         Koordinate -> erwartet: Karte schwenkt auf die Motiv-Koordinate.
      3. AK3: Bestehende Location öffnen -> Bearbeiten -> Feld
         "Fotograf-Standort" mit weit entfernter Koordinate füllen -> Blur
         -> erwartet: kleine Bearbeiten-Karte schwenkt auf diese Position.
      4. AK4: Gleiches im Feld "Motiv (Koordinaten)" beim Bearbeiten.
      5. Edge Case AK5: unvollständige/ungültige Koordinate eintippen (z. B.
         nur "48,") und Feld verlassen -> erwartet: keine Kartenbewegung,
         bestehende Fehlermeldung erscheint wie bisher.
      6. Edge Case AK6: Feldinhalt komplett löschen und Feld verlassen ->
         erwartet: Karte bleibt an der zuletzt zentrierten Position stehen,
         kein Rücksprung zu einem Standardausschnitt.
      7. Edge Case AK7: bei jedem Schwenk aus Schritt 1-4 bleibt die aktuell
         eingestellte Zoomstufe unverändert (nur `panTo`, kein Zoomwechsel
         auf eine feste Stufe).
      8. Regression AK8: Bearbeiten-Vollbild-Kartenoverlay öffnen, Pin per
         Antippen/Ziehen setzen, wieder schließen -- OHNE vorher etwas in
         ein Koordinatenfeld getippt zu haben -> erwartet: kein unerwarteter
         zusätzlicher Kartensprung der kleinen Karte beim Schließen
         (`closeMapFullscreen()` ruft `_onEditObsInput`/`_onEditSubjInput`
         weiterhin programmatisch auf, nicht die neuen Blur-Handler).
      9. Regression AK9 (PRODUCT.md §12 "Location-Edit"/"Sheet-Open/Close"):
         GPS-Button, Einfügen-Button, Antippen/Ziehen des Pins,
         Satellit/Straße-Umschalter funktionieren in beiden Formularen
         unverändert weiter.
    """
    raise AssertionError(
        "Sollte nie ausgefuehrt werden (skip-marker) — siehe Docstring/Testplan."
    )
