"""TASK-118 — Schnittstelle zwischen den Tests und der künftigen Umsetzung (HILFSMODUL, keine Tests).

Warum es dieses Modul gibt: Die Spec legt fest, WAS geschehen muss (Vorab-Probe, Kurztest,
Rücksprung auf die zuletzt bestätigte Version, Marke „zuletzt bestätigt“ als kleine Statusdatei
auf dem Server, Geheimnis FOTOALERT_LIVECHECK_PASSWORD), aber nicht, WIE die Teile aufgerufen
werden. Damit die Tests vor der Umsetzung schreibbar sind, steht alles, was nur ein VORSCHLAG
dieser Tests ist, gesammelt im Block „SCHNITTSTELLEN-VORSCHLAG“. Wird beim Weg-/Ready-Gate anders
entschieden, ändern sich nur die Konstanten hier — nicht die einzelnen Testfälle.
(Gleiches Muster wie tests/us141_adapter.py.)

Python-3.9-kompatibel (Produktion/CI).
"""
from __future__ import annotations

import re
import unicodedata

# ════════════════════════════════════════════════════════════════════════════
# AUS DER SPEC (verbindlich)
# ════════════════════════════════════════════════════════════════════════════
GEHEIMNIS_NAME = "FOTOALERT_LIVECHECK_PASSWORD"            # Umsetzungsschritt 5, AK3, AK28
MELDUNG_NICHT_EINSATZBEREIT = "Prüfung nicht einsatzbereit"  # AK2 (Meldung des GitHub-Laufs → Stufe 3)
MELDUNG_RUECKSPRUNG_FEHLGESCHLAGEN = "Rücksprung fehlgeschlagen – manueller Eingriff nötig"  # AK22
GRUND_FALSCHE_VERSION = "falsche Version live"              # AK6
# Prüfpunkt-Bezeichnungen, wie sie die Testfall-Liste nennt (T2, T9, T10, T12, T12a)
PRUEFPUNKT_KARTE = "Karte"
PRUEFPUNKT_FEED = "Feed"
PRUEFPUNKT_KALENDER = "Kalender"
PRUEFPUNKT_PROGRAMMFEHLER = "Programmfehler"
PRUEFPUNKT_VERSION = "Version"
PRUEFPUNKT_ANMELDUNG = "Anmeldung"
ALLE_PRUEFPUNKTE = (PRUEFPUNKT_VERSION, PRUEFPUNKT_ANMELDUNG, PRUEFPUNKT_KARTE, PRUEFPUNKT_FEED,
                    PRUEFPUNKT_KALENDER, PRUEFPUNKT_PROGRAMMFEHLER)
LIMIT_FEHLVERSUCHE = 5                                      # AK4: Anmeldesperre 5 Fehlversuche / 15 Minuten
GRENZE_MINUTEN_GESAMT = 10                                  # AK20 (Messung → Stufe 3/4)

# ════════════════════════════════════════════════════════════════════════════
# SCHNITTSTELLEN-VORSCHLAG DIESER TESTS (steht NICHT in der Spec — Freigabe offen)
# ════════════════════════════════════════════════════════════════════════════
# Server-Seite (Teststufe 1). Pfade relativ zum Repo-Root auf dem Server (/opt/fotoalert/app).
SKRIPT_VEROEFFENTLICHEN = "FotoAlert/deploy/deploy.sh"      # besteht; „Version Y wird veröffentlicht“
SKRIPT_MANUELLER_RUECKSPRUNG = "FotoAlert/deploy/rollback.sh"  # besteht; fragt [j/N] (AK32)
SKRIPT_AUTOMATIK = "FotoAlert/deploy/ruecksprung.sh"        # NEU (Vorschlag), nicht-interaktiv:
ARGS_RUECKSPRUNG = ["zurueck"]                              #   … zurueck     → auf „zuletzt bestätigt“ zurück, ohne Rückfrage
ARGS_BESTAETIGEN = ["bestaetigen"]                          #   … bestaetigen → laufende Version als „zuletzt bestätigt“ vermerken
# Feste Server-Pfade: Die Wegwerf-Kopie ersetzt in allen *.sh unter deploy/ diese Präfixe durch
# Ordner im Nachbau (so laufen heutiger Stand und Umsetzung gleich). Die Umsetzung muss deshalb
# alle Server-Pfade (auch die Statusdatei der Marke) unter diesen Präfixen halten und Befehle
# (sudo, systemctl, caddy, curl, journalctl) über den Suchpfad aufrufen, nicht mit absolutem Pfad.
SERVER_PRAEFIXE = ["/opt/fotoalert", "/etc/caddy", "/tmp/fotoalert_"]
# „Aktueller Stand des Servers“ = der Stand, den das Git-Arbeitsverzeichnis auf dem Server als
# HEAD führt (darauf setzt jedes erneute Ziehen und jeder Neustart auf — Befund B2/B4).

# Kurztest (Teststufe 2): Aufruf als eigenes Programm, Ergebnis über den Rückgabewert.
KURZTEST = "FotoAlert/backend/tests/livecheck/kurztest.py"  # NEU (Vorschlag), rein lesend
KURZTEST_ARG_ADRESSE = "--adresse"                          # öffentliche Adresse (hier: Attrappe)
KURZTEST_ARG_VERSION = "--erwartete-version"                # App-Version, die live sein soll (AK6)
KURZTEST_ARG_ERGEBNIS = "--ergebnis-ordner"                 # Ergebnisdateien + Bildschirmfotos (AK25, AK29)
# Rückgabewert 0 = alle sechs Prüfpunkte bestanden; ≠ 0 = gescheitert. Die Begründung (Prüfpunkt,
# Grund, Fremdfehler) steht in der Ausgabe ODER in Textdateien im Ergebnis-Ordner — die Tests
# durchsuchen beides. Eine Wiederholung eines Prüfpunkts fragt die Daten neu ab (AK11).
KURZTEST_ZEITLIMIT_S = 170
# Fehlerzeile (Vorschlag, fest): Je gescheitertem Prüfpunkt (auch nach der Wiederholung) genau eine eigene
# Zeile „gescheitert: <Prüfpunkt>“ mit einem Namen aus ALLE_PRUEFPUNKTE — in der Ausgabe oder einer Textdatei
# im Ergebnis-Ordner. Bestandene Prüfpunkte erscheinen nie in dieser Form.
FEHLERZEILE = "gescheitert: {pruefpunkt}"
_FEHLERZEILE_RE = re.compile(r"(?m)^[ \t]*gescheitert:[ \t]*(.+?)[ \t]*$")


def gescheiterte_pruefpunkte(text: str) -> set:
    """Alle Prüfpunkte, die der Kurztest in der festen Fehlerzeile als gescheitert meldet."""
    return {m.group(1) for m in _FEHLERZEILE_RE.finditer(text or "")}                                  # je Lauf in diesen Tests


def normalisiert(text: str) -> str:
    """Vergleichsform für Meldungstexte: Kleinschreibung, Gedankenstriche → '-', Leerraum vereinheitlicht."""
    t = unicodedata.normalize("NFC", text or "").lower()
    t = t.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", t)


def enthaelt_meldung(text: str, meldung: str) -> bool:
    return normalisiert(meldung) in normalisiert(text)
