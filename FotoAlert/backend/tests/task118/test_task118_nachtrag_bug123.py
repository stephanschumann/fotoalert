"""BUG-123 · AK-11 — Live-Check wartet beim Hinweis „wird gerade berechnet“ länger (Nachtrag zu TASK-118).

Testfälle aus der Spec von BUG-123 („Testfall-Liste“, Lauf 6, Entscheidung Stephan 2026-11-23):
T-13 und T-14 (hier in T-14a, T-14b, T-14c aufgeteilt; T-14c steht wegen seiner Dauer von 5 bis 6 Minuten
in langtest_task118_ak11_dauerhafter_hinweis.py) sowie die Prüfung der Wartezeit-Grenze des
Arbeitsablaufs (.github/workflows/deploy.yml, Technische Festlegung Lauf 6).
Geschrieben VOR der Umsetzung (fotoalert-test Teil A); Rot ist für T-13 (und T-14c in der Langtest-Datei) und die deploy.yml-Prüfung
gegen den heutigen Stand beabsichtigt, T-14a/T-14b sind Gegenproben und müssen schon heute grün sein.

Aufbau: Die bestehenden TASK-118-Dateien (eingefroren) werden nur gelesen und benutzt (Welt, Lauf,
Attrappe, Schnittstelle). Neu sind nur diese Datei und attrappe_bug123.py (Übungsseite, die den Kalender
zuerst „wird gerade berechnet“ melden lässt, nie antwortet oder dauerhaft den Hinweis zeigt).
Der Kurztest wird wie in test_task118_kurztest.py als eigener Prozess gegen die Übungsseite gestartet,
hier aber mit eigenem, größerem Zeitlimit, weil das Warten der Zweck von T-13 und T-14c ist.

Browser: Wie dort braucht der Kurztest Playwright-Chromium. Fehlt beides, werden die Browser-Tests mit
genau dieser benannten Bedingung übersprungen (gehören dann in den GitHub-Job mit Browser; „übersprungen“
heißt dort „offen“, nicht „grün“). Die Prüfung der deploy.yml und die Selbstprüfung der Übungsseite brauchen
keinen Browser und laufen immer.

Warum T-13 mit 110 Sekunden statt 60: Der Kurztest wiederholt einen gescheiterten Prüfpunkt genau einmal
(zweiter Versuch, 40 s). Die Seite fragt im Hintergrund weiter nach; wäre der Kalender nach 60 s fertig,
würde schon der HEUTIGE Stand über die Wiederholung (40 s + 40 s) grün werden — der Test würde das neue
Verhalten (im ERSTEN Versuch länger warten) nicht von heute unterscheiden. 110 s liegt klar über beiden
40-s-Versuchen und klar unter den ca. 240 s, die der neue erste Versuch warten darf.
"""
from __future__ import annotations

import http.client
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple

import pytest

from . import schnittstelle as S
from .attrappe_bug123 import HINWEIS_TEXT, VORWAERM_KENNUNG, AttrappenB123, LageB123
# Nur benutzt (nicht verändert): Hilfsklassen und Prüfhelfer der eingefrorenen TASK-118-Datei
from .test_task118_kurztest import (Lauf, Welt, Y, _ANDERE_GEHEIMNISSE, _gegenprobe, _kurztest_bereit,
                                    _pruefe_gescheitert, KURZTEST, REPO_ROOT)

# requires_full_checkout (registriert in backend/pytest.ini, TASK-96): liest .github/workflows/deploy.yml und
# backend/tests/livecheck/kurztest.py ausserhalb von backend/ (wie test_task118_ruecksprung.py)
pytestmark = [pytest.mark.frontend, pytest.mark.regression, pytest.mark.requires_full_checkout]

WORKFLOW = REPO_ROOT / ".github/workflows/deploy.yml"

# ── Zahlen und ihre Herkunft ────────────────────────────────────────────────
HINWEIS_DAUER_S = 110        # T-13: Kalender zeigt so lange den Hinweis; siehe Kopf (Wiederholung 40 s + 40 s = 80 s < 110)
LIMIT_T13_S = 300            # Zeitlimit des Unterprozesses bei T-13 (Spec: Warten bis ca. 240 s ist erlaubt)
OBERGRENZE_ROT_OHNE_HINWEIS_S = 120
#   AK-11 / Ticket: ohne Hinweis rot nach ca. 40 s je Versuch, mit Wiederholung ca. 80 s, dazu die übrigen
#   Prüfpunkte. Erst 150 s (ohne Browser nur geschätzt); nach dem Mac-Lauf der Browser-Tests gesenkt auf 120 s,
#   weil dort gemessen wurde: T-14a 10 s, T-14b 89 s (T-14a/b dauern heute also weit unter 120 s). 120 s trennt klar
#   „wie heute“ (unter 90 s) von „wartet fälschlich wie beim Hinweis“ (ab ca. 240 s im ersten Versuch).


class LangeWelt(Welt):
    """Wie Welt (test_task118_kurztest.py), aber mit erweiterter Übungsseite und eigenem Zeitlimit."""

    def attrappe_b123(self, modus: str, version: str = Y, hinweis_s: float = 0.0) -> AttrappenB123:
        lage = LageB123(version, self.pruefzugang, self.host_passwort)
        lage.kalender_modus = modus
        lage.hinweis_sekunden = hinweis_s
        a = AttrappenB123(lage)
        self._attrappen.append(a)
        return a

    def kurztest_gemessen(self, a, erwartete_version: str, zeitlimit_s: int) -> Tuple[Lauf, float, bool]:
        """„Live-Check läuft“ gegen die Übungsseite. Rückgabe: Lauf, Gesamtdauer in Sekunden, Zeitlimit überschritten?"""
        _kurztest_bereit()
        self._laeufe += 1
        ordner = self.wurzel / f"ergebnis-{self._laeufe}"
        ordner.mkdir()
        env = {k: v for k, v in os.environ.items() if k not in _ANDERE_GEHEIMNISSE}
        env[S.GEHEIMNIS_NAME] = self.pruefzugang
        t0 = time.monotonic()
        try:
            r = subprocess.run([sys.executable, str(KURZTEST), S.KURZTEST_ARG_ADRESSE, a.adresse,
                                S.KURZTEST_ARG_VERSION, erwartete_version, S.KURZTEST_ARG_ERGEBNIS, str(ordner)],
                               cwd=str(self.wurzel), env=env, capture_output=True, timeout=zeitlimit_s)
            return Lauf(r.returncode, r.stdout, r.stderr, ordner), time.monotonic() - t0, False
        except subprocess.TimeoutExpired as e:
            return Lauf(-1, e.stdout or b"", e.stderr or b"", ordner), time.monotonic() - t0, True


@pytest.fixture
def welt():
    w = LangeWelt()
    try:
        yield w
    finally:
        w.abbauen()


def _abruf(adresse: str, pfad: str, kennung: str, timeout_s: float):
    host, port = adresse.replace("http://", "").split(":")
    c = http.client.HTTPConnection(host, int(port), timeout=timeout_s)
    try:
        c.request("GET", pfad, headers={"User-Agent": kennung})
        r = c.getresponse()
        return r.status, r.read().decode("utf-8")
    finally:
        c.close()


# ── Teil 1: Der Live-Check wartet beim Hinweis (T-13) ───────────────────────
def test_t13_ak11_kalender_mit_hinweis_und_erst_nach_langem_warten_fertig_live_check_besteht(welt):
    """T-13 · AK-11 · BUG-123 — Gegeben der Kalender zeigt zuerst den Hinweis „wird gerade berechnet, bitte kurz
    warten“ (mit Ladesymbol) und ist erst nach deutlich mehr als 40 Sekunden (hier 110 s) fertig, wenn der
    Live-Check läuft, dann wartet er im ersten Versuch weiter und besteht beim Prüfpunkt Kalender."""
    a = welt.attrappe_b123("hinweis_dann_fertig", hinweis_s=HINWEIS_DAUER_S)
    lauf, dauer, zeitlimit = welt.kurztest_gemessen(a, Y, LIMIT_T13_S)
    L = a.lage
    assert not zeitlimit, f"Zeitlimit {LIMIT_T13_S} s überschritten: {lauf!r}"
    if lauf.code != 0:
        # Ist er rot, dann muss genau der Prüfpunkt Kalender als gescheitert gemeldet sein (sonst Testmechanik/anderer Fehler)
        _pruefe_gescheitert(lauf, S.PRUEFPUNKT_KALENDER)
    assert lauf.code == 0, (
        f"Der Live-Check muss beim Hinweis „{HINWEIS_TEXT}“ weiterwarten und bestehen (Gesamtdauer {dauer:.0f} s, "
        f"Hinweis-Antworten {L.hinweis_antworten}, fertig geliefert {L.fertig_an_seite}): {lauf!r}")
    # Beleg, dass wirklich gewartet wurde und der fertige Kalender die Seite erreicht hat
    assert L.hinweis_antworten >= 3, f"Die Seite hat den Hinweis kaum gesehen ({L.hinweis_antworten} Antworten)"
    assert L.fertig_an_seite >= 1, "Der fertige Kalender wurde nie an die Seite geliefert"
    assert dauer >= HINWEIS_DAUER_S, f"Lauf endete nach {dauer:.0f} s, vor dem Ende des Hinweises ({HINWEIS_DAUER_S} s)"


# ── Teil 2: Gegenproben — ohne Hinweis bleibt es bei ca. 40 s je Versuch (T-14) ──
def test_t14a_ak11_kalender_mit_fehlermeldung_ohne_hinweis_live_check_rot_ohne_langes_warten(welt):
    """T-14a · AK-11 (Gegenprobe) · BUG-123 — Gegeben der Kalender zeigt eine Fehlermeldung (und nicht den Hinweis
    „wird gerade berechnet“), wenn der Live-Check läuft, dann ist er rot beim Prüfpunkt „Kalender“ und dauert
    insgesamt nicht länger als ca. zwei Versuche à 40 s plus die übrigen Prüfpunkte (unter 120 s)."""
    _gegenprobe(S.PRUEFPUNKT_KALENDER)
    a = welt.attrappe_b123("normal")
    a.lage.kalender_fehler = True
    lauf, dauer, zeitlimit = welt.kurztest_gemessen(a, Y, LIMIT_T13_S)
    assert not zeitlimit, f"Zeitlimit überschritten — der Live-Check wartet bei einer Fehlermeldung zu lange: {lauf!r}"
    assert lauf.code != 0, f"Kalender mit Fehlermeldung darf nicht grün sein: {lauf!r}"
    _pruefe_gescheitert(lauf, S.PRUEFPUNKT_KALENDER)
    assert dauer < OBERGRENZE_ROT_OHNE_HINWEIS_S, (
        f"Bei einer Fehlermeldung (kein Hinweis) darf der Live-Check nicht lange warten: {dauer:.0f} s, "
        f"erlaubt unter {OBERGRENZE_ROT_OHNE_HINWEIS_S} s")
    assert a.lage.hinweis_antworten == 0, "Übungsseite hat den Hinweis gemeldet — Test prüft nicht den Fall ohne Hinweis"


def test_t14b_ak11_kalender_laedt_dauerhaft_ohne_hinweis_live_check_rot_ohne_langes_warten(welt):
    """T-14b · AK-11 (Gegenprobe) · BUG-123 — Gegeben der Kalender bleibt dauerhaft im Zustand „lädt“ (Ladesymbol, aber
    ohne den Hinweis „wird gerade berechnet“, der Server antwortet nie), wenn der Live-Check läuft, dann ist er
    rot beim Prüfpunkt „Kalender“, ca. 40 s je Versuch, insgesamt unter 120 s."""
    _gegenprobe(S.PRUEFPUNKT_KALENDER)
    a = welt.attrappe_b123("haengt")
    lauf, dauer, zeitlimit = welt.kurztest_gemessen(a, Y, LIMIT_T13_S)
    assert not zeitlimit, f"Zeitlimit überschritten — der Live-Check wartet ohne Hinweis zu lange: {lauf!r}"
    assert lauf.code != 0, f"Ein dauerhaft ladender Kalender ohne Hinweis darf nicht grün sein: {lauf!r}"
    _pruefe_gescheitert(lauf, S.PRUEFPUNKT_KALENDER)
    assert dauer < OBERGRENZE_ROT_OHNE_HINWEIS_S, (
        f"Ohne Hinweis darf der Live-Check nicht lange warten: {dauer:.0f} s, erlaubt unter {OBERGRENZE_ROT_OHNE_HINWEIS_S} s")
    assert a.lage.haengende_abrufe >= 1 and a.lage.hinweis_antworten == 0, (
        "Übungsseite hat nicht wie vorgesehen nie geantwortet bzw. den Hinweis gemeldet")


# ── Teil 3: Arbeitsablauf (deploy.yml) — Wartezeit-Grenzen der Schritte ──────
def _schritt_zeilen(text: str, schritt_id: str):
    """Zeilen des Schritts mit `id: <schritt_id>` (vom „- name:“ davor bis zum nächsten „- name:“)."""
    zeilen = text.splitlines()
    treffer = [i for i, z in enumerate(zeilen) if re.match(r"^\s+id:\s*" + re.escape(schritt_id) + r"\s*$", z)]
    assert len(treffer) == 1, f"Schritt mit id „{schritt_id}“ kommt {len(treffer)}-mal vor (erwartet genau 1)"
    start = treffer[0]
    while start >= 0 and not re.match(r"^\s*-\s+name:", zeilen[start]):
        start -= 1
    assert start >= 0, f"Kein „- name:“ vor dem Schritt „{schritt_id}“ gefunden"
    ende = treffer[0] + 1
    while ende < len(zeilen) and not re.match(r"^\s*-\s+name:", zeilen[ende]):
        ende += 1
    return zeilen[start:ende]


def _timeout_minuten(zeilen) -> int:
    werte = []
    for z in zeilen:
        m = re.match(r"^\s+timeout-minutes:\s*(\d+)\s*(?:#.*)?$", z)
        if m:
            werte.append(int(m.group(1)))
    assert len(werte) == 1, f"Erwartet genau ein timeout-minutes im Schritt, gefunden: {werte}\n" + "\n".join(zeilen[:3])
    return werte[0]


def test_t13b_ak11_deploy_yml_live_check_nach_dem_veroeffentlichen_darf_mindestens_6_minuten_laufen():
    """T-13b · AK-11 · BUG-123 (Arbeitsablauf der Veröffentlichung) — Gegeben der Live-Check nach dem Veröffentlichen soll
    beim Hinweis bis ca. 4 Minuten plus Wiederholung und übrige Prüfpunkte warten dürfen, dann darf dieser Schritt
    mindestens 6 Minuten laufen, bevor ihn der Arbeitsablauf abbricht, und der Live-Check nach dem Rücksprung darf
    unverändert nur 3 Minuten laufen."""
    # Technik: Schritte `live1`/`live2` in .github/workflows/deploy.yml, Feld timeout-minutes (Festlegung Lauf 6: 3 → 7 nur live1)
    # Selbstprobe der Textprüfung (Gegenprobe): jeder Schritt bekommt nur seinen eigenen Wert
    probe = ("jobs:\n  x:\n    steps:\n"
             "      - name: Eins\n        id: a\n        timeout-minutes: 7\n"
             "      - name: Zwei\n        id: b\n        timeout-minutes: 3\n"
             "      - name: Drei\n        id: c\n        run: echo\n")
    assert _timeout_minuten(_schritt_zeilen(probe, "a")) == 7
    assert _timeout_minuten(_schritt_zeilen(probe, "b")) == 3
    with pytest.raises(AssertionError):
        _timeout_minuten(_schritt_zeilen(probe, "c"))      # Wert des Nachbarn darf nicht „durchrutschen“

    text = WORKFLOW.read_text(encoding="utf-8")
    live1 = _schritt_zeilen(text, "live1")
    live2 = _schritt_zeilen(text, "live2")
    assert "Live-Check (Kurztest nach dem Veröffentlichen)" in live1[0], f"Schritt live1 heißt anders: {live1[0]!r}"
    assert "Live-Check nach dem Rücksprung" in live2[0], f"Schritt live2 heißt anders: {live2[0]!r}"
    m1 = _timeout_minuten(live1)
    m2 = _timeout_minuten(live2)
    assert m1 >= 6, f"live1 (Live-Check nach dem Veröffentlichen): timeout-minutes ist {m1}, erwartet mindestens 6"
    assert m2 == 3, f"live2 (Live-Check nach dem Rücksprung): timeout-minutes ist {m2}, erwartet unverändert 3"


# ── Selbstprüfung der erweiterten Übungsseite (ohne Browser, läuft immer) ─────
def test_hilfe_uebungsseite_hinweis_dann_fertig_und_vorwaermen_startet_die_uhr_nicht(welt):
    """Selbstprüfung (kein Testfall der Spec) — Gegeben die Übungsseite im Modus „Hinweis, dann fertig (2 s)“, dann
    bekommt das Vorwärmen (Kennung des Live-Checks) „calculating“ ohne die Uhr zu starten, die Seite
    (Browser-Kennung) bekommt „calculating“ und nach 2 s den fertigen Kalender."""
    a = welt.attrappe_b123("hinweis_dann_fertig", hinweis_s=2.0)
    st, body = _abruf(a.adresse, "/calendar?month=1&year=2026", VORWAERM_KENNUNG, 5)
    assert st == 200 and '"calculating"' in body and HINWEIS_TEXT in body
    assert a.lage.erster_browser_abruf is None, "Vorwärmen darf die Uhr nicht starten"
    st, body = _abruf(a.adresse, "/calendar?month=1&year=2026", "Mozilla/5.0 Chrome", 5)
    assert '"calculating"' in body
    time.sleep(2.3)
    st, body = _abruf(a.adresse, "/calendar?month=1&year=2026", "Mozilla/5.0 Chrome", 5)
    assert st == 200 and '"ok"' in body and '"events"' in body and '"calculating"' not in body
    assert (a.lage.vorwaerm_abrufe, a.lage.hinweis_antworten, a.lage.fertig_an_seite) == (1, 1, 1)


def test_hilfe_uebungsseite_haengt_antwortet_der_seite_nie_dem_vorwaermen_sofort(welt):
    """Selbstprüfung (kein Testfall der Spec) — Gegeben die Übungsseite im Modus „hängt“, dann antwortet sie der
    Seite (Browser-Kennung) nicht (Zeitüberschreitung nach 2 s), dem Vorwärmen aber sofort mit dem fertigen Kalender."""
    a = welt.attrappe_b123("haengt")
    st, body = _abruf(a.adresse, "/calendar?month=1&year=2026", VORWAERM_KENNUNG, 5)
    assert st == 200 and '"ok"' in body
    with pytest.raises((socket.timeout, TimeoutError)):
        _abruf(a.adresse, "/calendar?month=1&year=2026", "Mozilla/5.0 Chrome", 2)
    assert a.lage.haengende_abrufe == 1 and a.lage.hinweis_antworten == 0


def test_hilfe_uebungsseite_normal_laesst_die_bestehende_seite_unveraendert(welt):
    """Selbstprüfung (kein Testfall der Spec) — Gegeben die Übungsseite im Modus „normal“, dann antwortet sie wie die
    bestehende Übungsseite: fertig, bzw. mit Fehler 500 bei `kalender_fehler`."""
    a = welt.attrappe_b123("normal")
    st, body = _abruf(a.adresse, "/calendar?month=1&year=2026", "Mozilla/5.0 Chrome", 5)
    assert st == 200 and '"ok"' in body
    a.lage.kalender_fehler = True
    st, body = _abruf(a.adresse, "/calendar?month=1&year=2026", "Mozilla/5.0 Chrome", 5)
    assert st == 500


def test_hilfe_uebungsseite_misst_beobachtungsdauer_vom_ersten_bis_zum_letzten_abruf_der_seite(welt):
    """Selbstprüfung (kein Testfall der Spec) — Gegeben die Übungsseite im Modus „Hinweis bleibt“, dann zählt die
    Beobachtungsdauer vom ersten bis zum letzten Abruf der Seite (nicht des Vorwärmens): ohne Abruf 0 s, nach
    zwei Abrufen im Abstand von 1,2 s etwa 1,2 s."""
    a = welt.attrappe_b123("hinweis_dauerhaft")
    assert a.lage.beobachtung_s() == 0.0
    _abruf(a.adresse, "/calendar?month=1&year=2026", VORWAERM_KENNUNG, 5)
    assert a.lage.beobachtung_s() == 0.0, "Vorwärmen zählt nicht zur Beobachtung der Seite"
    _abruf(a.adresse, "/calendar?month=1&year=2026", "Mozilla/5.0 Chrome", 5)
    time.sleep(1.2)
    _abruf(a.adresse, "/calendar?month=1&year=2026", "Mozilla/5.0 Chrome", 5)
    assert 1.1 <= a.lage.beobachtung_s() <= 2.0, a.lage.beobachtung_s()
