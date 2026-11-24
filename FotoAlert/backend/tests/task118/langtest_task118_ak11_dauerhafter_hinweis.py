"""BUG-123 · AK-11 · T-14c — LANGTEST: Hinweis bleibt dauerhaft, der Live-Check gibt nach etwa 4 Minuten auf.

Zweck: Obergrenze des längeren Wartens beim Hinweis „wird gerade berechnet, bitte kurz warten“. Der Live-Check
darf im ersten Versuch bis ca. 240 s warten, wiederholt dann nur kurz (40 s) und ist danach rot beim Prüfpunkt
„Kalender“ — er wartet nicht endlos. Ein erster Versuch von nur ca. 150 s muss rot sein.

Aufruf (aus backend/, gezielt mit dem Dateipfad):
    ./venv/bin/python3 -m pytest tests/task118/langtest_task118_ak11_dauerhafter_hinweis.py -v
Dauer: im neuen Verhalten ca. 5 bis 6 Minuten (heute, solange das Verhalten fehlt, ca. 1,5 Minuten, dann rot).

Warum er nicht im Probelauf läuft: Der Dateiname beginnt absichtlich NICHT mit „test_“. Sammelläufe
(`pytest tests/ ...`, Probelauf von release.sh, GitHub) sammeln ihn deshalb nicht ein; es braucht weder
einen Skip noch einen Eintrag in tools/bekannte_uebersprungene_tests.txt. Wer ihn braucht, ruft ihn mit dem
Dateipfad auf. Beim Abschluss-Nachweis von BUG-123 läuft er auf Stephans Mac (Playwright-Chromium nötig;
ohne Chromium wird mit der benannten Bedingung übersprungen, das gilt dann als „offen“, nicht „grün“).

Hilfsmittel werden aus den anderen Dateien importiert, nicht kopiert: Welt/Lauf/Prüfhelfer aus
test_task118_kurztest.py, LangeWelt/welt aus test_task118_nachtrag_bug123.py, Übungsseite aus attrappe_bug123.py.

Zahlen und Herkunft:
    Beobachtung der Seite 270 bis 330 s; Gesamtdauer 230 bis 420 s; Zeitlimit des Unterprozesses 480 s.
"""
from __future__ import annotations

import pytest

from . import schnittstelle as S
from .test_task118_kurztest import Y, _gegenprobe, _pruefe_gescheitert
# welt: Fixture (LangeWelt) der Nachtrag-Datei; als Name hier sichtbar machen, damit pytest sie findet
from .test_task118_nachtrag_bug123 import welt  # noqa: F401

pytestmark = [pytest.mark.frontend, pytest.mark.regression, pytest.mark.requires_full_checkout]

HINWEIS_DAUERHAFT_UNTEN_S = 230    # T-14c: Gesamtdauer des Live-Checks mindestens (240 + 40 + Rest, großzügig nach unten)
HINWEIS_DAUERHAFT_OBEN_S = 420     # T-14c: 240 + 40 + ca. 50 (übrige Prüfpunkte) + Reserve; „nicht endlos“
LIMIT_T14C_S = 480
BEOBACHTUNG_UNTEN_S = 270          # T-14c: Beobachtungsdauer der Seite (1. bis letzter Kalender-Abruf) mindestens
BEOBACHTUNG_OBEN_S = 330           # T-14c: … höchstens
#   Herkunft: Ticket AK-11 / Technische Festlegung: erster Versuch wartet beim Hinweis bis ca. 240 s, die Wiederholung
#   bleibt bei T_KALENDER = 40 s (kurztest.py Z. 89). Die Seite fragt bis zum Schließen des Browsers weiter nach
#   (web/index.html, loadMonth, alle 5 s); der Browser schließt nach dem Prüfpunkt Programmfehler
#   (T_NACHLAUF_FEHLER = 2,5 s, kurztest.py Z. 90). Beobachtung also ca. 240 + 40 + 2,5 ≈ 283 s, daher 270 bis 330 s.
#   Ein erster Versuch von nur ca. 150 s ergäbe ca. 193 s und ist damit rot. Der echte erste Start braucht ca. 216 s
#   (Messung Dienstprotokoll, Ticket Lauf 6: 3:33 bis 3:42 Min ruhig; ersatzweise Entscheidungslog Nr. 17).
#   Hinweis: Die Zahlen sind aus Quelltext und Ticket abgeleitet, noch nicht in einem Browserlauf beobachtet.


@pytest.mark.slow
def test_t14c_ak11_hinweis_bleibt_dauerhaft_live_check_gibt_nach_etwa_vier_minuten_auf(welt):
    """T-14c · AK-11 (Obergrenze) · BUG-123 — Gegeben der Kalender zeigt dauerhaft den Hinweis „wird gerade berechnet“
    und wird nie fertig, wenn der Live-Check läuft, dann wartet er im ersten Versuch bis ca. 240 s, wiederholt
    nur kurz (40 s) und ist danach rot beim Prüfpunkt „Kalender“ — er wartet nicht endlos. Die Seite beobachtet den
    Kalender insgesamt etwa 270 bis 330 Sekunden (ein erster Versuch von nur 150 Sekunden genügt nicht). Der Test
    dauert 5 bis 6 Minuten und läuft nur auf ausdrücklichen Abruf (eigene Datei, wird nicht in Sammelläufen eingesammelt)."""
    _gegenprobe(S.PRUEFPUNKT_KALENDER)
    a = welt.attrappe_b123("hinweis_dauerhaft")
    lauf, dauer, zeitlimit = welt.kurztest_gemessen(a, Y, LIMIT_T14C_S)
    assert not zeitlimit, f"Der Live-Check wartet endlos beim Hinweis (Zeitlimit {LIMIT_T14C_S} s): {lauf!r}"
    assert lauf.code != 0, f"Ein dauerhaft berechnender Kalender darf nicht grün sein: {lauf!r}"
    _pruefe_gescheitert(lauf, S.PRUEFPUNKT_KALENDER)
    assert HINWEIS_DAUERHAFT_UNTEN_S <= dauer <= HINWEIS_DAUERHAFT_OBEN_S, (
        f"Beim Hinweis soll der erste Versuch bis ca. 240 s warten: Gesamtdauer {dauer:.0f} s, erwartet "
        f"{HINWEIS_DAUERHAFT_UNTEN_S} bis {HINWEIS_DAUERHAFT_OBEN_S} s")
    assert a.lage.hinweis_antworten >= 10, "Die Seite hat den Hinweis nur selten gesehen — Test prüft das Warten nicht"
    beobachtet = a.lage.beobachtung_s()
    assert BEOBACHTUNG_UNTEN_S <= beobachtet <= BEOBACHTUNG_OBEN_S, (
        f"Die Seite hat den Kalender {beobachtet:.0f} s beobachtet (erster bis letzter Abruf), erwartet "
        f"{BEOBACHTUNG_UNTEN_S} bis {BEOBACHTUNG_OBEN_S} s — der erste Versuch wartet beim Hinweis zu kurz oder zu lange")
