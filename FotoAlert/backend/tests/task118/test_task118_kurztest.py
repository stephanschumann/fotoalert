"""TASK-118 — Echter Live-Check: Teststufe 2 (Kurztest gegen lokale Attrappen-Server).

Testfälle aus der Spec (docs/analyse-entwurf/TASK-118_SPEC.md, „Testfall-Liste“), Stufe 2:
T2, T3, T4, T28 (Stufen-2-Teil), T15 (Stufen-2-Teil), T6, T7, T8, T9, T10, T10b, T11, T12, T12a, T12b, T13, T14, T16, T32, T33.
Geschrieben VOR der Umsetzung (fotoalert-test Teil A); Rot ist gegen den heutigen Stand beabsichtigt.

Aufbau: Je Test eigene Attrappen (attrappe.py) — die echte App-Oberfläche aus FotoAlert/web/ mit festen
Testdaten, dazu eine „Fremdquelle“ für Kartenbilder/Fremdskript. Beide nur auf 127.0.0.1/localhost, im Test
gestartet und im Teardown beendet; Ergebnis-Ordner im Temp-Ordner, im Teardown gelöscht. Kein Aufruf der
echten Seite, kein Internet, kein echtes Geheimnis (der Prüf-Zugang ist ein Zufallswert je Test).
Aufruf des Kurztests: Vorschlag in schnittstelle.py.

Browser: Der Kurztest braucht Playwright-Chromium. Fehlt der Kurztest, ist der Test rot (Verhalten fehlt).
Ist der Kurztest vorhanden, aber in der Umgebung kein Chromium installiert, wird mit genau dieser benannten
Bedingung übersprungen — diese Läufe gehören in den GitHub-Job mit Browser (Frontend-Check); übersprungen
heißt dort „offen“, nicht „grün“.
"""
from __future__ import annotations

import copy
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from . import schnittstelle as S
from .attrappe import Attrappen, Lage

pytestmark = [pytest.mark.frontend, pytest.mark.regression]

REPO_ROOT = Path(__file__).resolve().parents[4]
KURZTEST = REPO_ROOT / S.KURZTEST
WORKFLOW = REPO_ROOT / ".github/workflows/deploy.yml"
X, Y = "1.26.1", "1.27.0"
_ANDERE_GEHEIMNISSE = ("FOTOALERT_USER_PASSWORD", "FOTOALERT_HOST_PASSWORD", "FOTOALERT_AUTH_SECRET",
                       S.GEHEIMNIS_NAME)


def _kurztest_bereit() -> None:
    assert KURZTEST.is_file(), f"Verhalten fehlt: Der rein lesende Kurztest ({S.KURZTEST}) ist nicht vorhanden."
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Bedingung: Playwright nicht installiert — Kurztest-Lauf gehört in den GitHub-Job mit Browser (offen)")
    with sync_playwright() as p:
        pfad = p.chromium.executable_path
    if not pfad or not Path(pfad).exists():
        pytest.skip("Bedingung: Playwright-Chromium nicht installiert — Kurztest-Lauf gehört in den GitHub-Job mit Browser (offen)")


class Lauf:
    def __init__(self, code: int, stdout: bytes, stderr: bytes, ordner: Path):
        self.code, self.stdout, self.stderr, self.ordner = code, stdout, stderr, ordner

    def text(self) -> str:
        teile = [self.stdout.decode("utf-8", "replace"), self.stderr.decode("utf-8", "replace")]
        for d in sorted(self.ordner.rglob("*")):
            if d.is_file():
                try:
                    teile.append(d.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    pass
        return "\n".join(teile)

    def alle_bytes(self):
        yield "Ausgabe", self.stdout + self.stderr
        for d in sorted(self.ordner.rglob("*")):
            if d.is_file():
                yield str(d.relative_to(self.ordner)), d.read_bytes()

    def bildschirmfotos(self):
        return [d for d in self.ordner.rglob("*") if d.suffix.lower() in (".png", ".jpg", ".jpeg")]

    def __repr__(self) -> str:
        return f"<Kurztest Rückgabe {self.code}>\n" + "\n".join(self.text().strip().splitlines()[-15:])


class Welt:
    """Attrappen + Ergebnis-Ordner eines Tests; räumt im Teardown alles ab."""

    def __init__(self):
        self.wurzel = Path(tempfile.mkdtemp(prefix="fa118-kurztest-"))
        self.pruefzugang = "pruefzugang-test-" + os.urandom(6).hex()
        self.host_passwort = "host-test-" + os.urandom(6).hex()
        self._attrappen = []
        self._laeufe = 0

    def attrappe(self, version: str = X) -> Attrappen:
        a = Attrappen(Lage(version, self.pruefzugang, self.host_passwort))
        self._attrappen.append(a)
        return a

    def kurztest(self, a: Attrappen, erwartete_version: str, geheimnis: object = True, zusatz_env: dict = None) -> Lauf:
        """„Live-Check läuft“ (bzw. „Vorab-Probe läuft“) gegen die Attrappe."""
        _kurztest_bereit()
        self._laeufe += 1
        ordner = self.wurzel / f"ergebnis-{self._laeufe}"
        ordner.mkdir()
        env = {k: v for k, v in os.environ.items() if k not in _ANDERE_GEHEIMNISSE}
        if geheimnis is True:
            env[S.GEHEIMNIS_NAME] = self.pruefzugang
        elif isinstance(geheimnis, str):
            env[S.GEHEIMNIS_NAME] = geheimnis
        env.update(zusatz_env or {})
        r = subprocess.run([sys.executable, str(KURZTEST), S.KURZTEST_ARG_ADRESSE, a.adresse,
                            S.KURZTEST_ARG_VERSION, erwartete_version, S.KURZTEST_ARG_ERGEBNIS, str(ordner)],
                           cwd=str(self.wurzel), env=env, capture_output=True, timeout=S.KURZTEST_ZEITLIMIT_S)
        return Lauf(r.returncode, r.stdout, r.stderr, ordner)

    def abbauen(self) -> None:
        for a in self._attrappen:
            a.stoppe()
        shutil.rmtree(self.wurzel, ignore_errors=True)


@pytest.fixture
def welt():
    w = Welt()
    try:
        yield w
    finally:
        w.abbauen()


def _nennt(lauf: Lauf, text: str) -> bool:
    return S.enthaelt_meldung(lauf.text(), text)


def _scheitert_genau_an(text: str, pruefpunkt: str) -> bool:
    """Wahr nur, wenn der Kurztest in der festen Fehlerzeile genau diesen einen Prüfpunkt als gescheitert meldet."""
    return S.gescheiterte_pruefpunkte(text) == {pruefpunkt}


def _gegenprobe(pruefpunkt: str) -> None:
    """Gegenprobe der Prüfung selbst (läuft in jedem betroffenen Test, auch ohne Kurztest): Ein anderer
    gescheiterter Prüfpunkt, ein zusätzlich gescheiterter Prüfpunkt oder die bloße Erwähnung des Namens
    bestehen die Prüfung NICHT; nur die Fehlerzeile genau dieses Prüfpunkts besteht sie."""
    zeile = S.FEHLERZEILE.format(pruefpunkt=pruefpunkt)
    assert _scheitert_genau_an(f"Kurztest\n{zeile}\n", pruefpunkt), "Gegenprobe: richtige Fehlerzeile nicht erkannt"
    for anderer in S.ALLE_PRUEFPUNKTE:
        if anderer == pruefpunkt:
            continue
        falsch = S.FEHLERZEILE.format(pruefpunkt=anderer)
        assert not _scheitert_genau_an(f"{falsch}\n{pruefpunkt} geprüft\n", pruefpunkt), f"Gegenprobe: {anderer} besteht"
        assert not _scheitert_genau_an(f"{zeile}\n{falsch}\n", pruefpunkt), f"Gegenprobe: zusätzlich {anderer} besteht"
    assert not _scheitert_genau_an(f"{pruefpunkt}: bestanden\nPrüfpunkt {pruefpunkt} gescheitert?\n", pruefpunkt), (
        "Gegenprobe: bloße Erwähnung besteht")


def _pruefe_gescheitert(lauf: Lauf, pruefpunkt: str) -> None:
    assert _scheitert_genau_an(lauf.text(), pruefpunkt), (
        f"Erwartet genau „{S.FEHLERZEILE.format(pruefpunkt=pruefpunkt)}“, gemeldet als gescheitert: "
        f"{sorted(S.gescheiterte_pruefpunkte(lauf.text()))}; {lauf!r}")


# ── Vorab-Probe ─────────────────────────────────────────────────────────────
def test_t2_ak2_vorab_probe_scheitert_beim_pruefpunkt_karte(welt):
    """T2 (Stufen-2-Teil) · AK2 · TASK-118 — Gegeben die noch laufende Version X zeigt auf der Karte keine Orte,
    wenn die Vorab-Probe gegen X läuft, dann scheitert sie und nennt den Prüfpunkt „Karte“.
    („Nichts veröffentlicht, Lauf rot, Meldung ‚Prüfung nicht einsatzbereit‘“ → Stufe 3.)"""
    _gegenprobe(S.PRUEFPUNKT_KARTE)
    a = welt.attrappe(X)
    a.lage.orte = []
    lauf = welt.kurztest(a, X)
    assert lauf.code != 0, f"Vorab-Probe muss scheitern: {lauf!r}"
    _pruefe_gescheitert(lauf, S.PRUEFPUNKT_KARTE)


@pytest.mark.parametrize("geheimnis", [None, ""], ids=["pruefzugang_nicht_angelegt", "pruefzugang_leer"])
def test_t3_ak3_fehlender_pruefzugang_scheitert_sofort_ohne_anmeldeversuch(welt, geheimnis):
    """T3 (Stufen-2-Teil) · AK3 · TASK-118 — Gegeben der Prüf-Zugang ist nicht angelegt oder leer, wenn die
    Vorab-Probe läuft, dann scheitert sie, ohne dass die Seite einen einzigen Anmeldeversuch sieht, und die
    Meldung nennt den Namen des Geheimnisses."""
    a = welt.attrappe(X)
    lauf = welt.kurztest(a, X, geheimnis=geheimnis)
    assert lauf.code != 0, f"Ohne Prüf-Zugang muss der Kurztest scheitern: {lauf!r}"
    assert a.lage.anmeldeversuche == [], f"Anmeldeversuche trotz fehlendem Prüf-Zugang: {a.lage.anmeldeversuche}"
    assert S.GEHEIMNIS_NAME in lauf.text(), f"Meldung nennt {S.GEHEIMNIS_NAME} nicht: {lauf!r}"


def test_t4_ak4_ungueltiger_pruefzugang_hoechstens_ein_anmeldeversuch_je_lauf(welt):
    """T4 · AK4 · TASK-118 — Gegeben der Prüf-Zugang ist ungültig, wenn der Kurztest dreimal nacheinander läuft,
    dann sieht die Seite je Lauf genau einen Anmeldeversuch, und die Anmeldesperre (5 Fehlversuche in
    15 Minuten) wird nicht ausgelöst."""
    a = welt.attrappe(X)
    for n in (1, 2, 3):
        lauf = welt.kurztest(a, X, geheimnis="falscher-pruefzugang-" + os.urandom(4).hex())
        assert lauf.code != 0, f"Lauf {n}: ungültiger Prüf-Zugang muss scheitern: {lauf!r}"
        assert len(a.lage.anmeldeversuche) == n, (
            f"Lauf {n}: erwartet insgesamt {n} Anmeldeversuch(e), gesehen {len(a.lage.anmeldeversuche)}")
    assert a.lage.gesperrte_versuche == 0 and a.lage.fehlversuche_in_15_min() < S.LIMIT_FEHLVERSUCHE


def test_t28_ak24_vorab_probe_gegen_die_laufende_version_entscheidet_ueber_die_bestaetigung(welt):
    """T28 (Stufen-2-Teil) · AK24 · TASK-118 — Gegeben es gibt noch keine bestätigte Version: Besteht die
    Vorab-Probe gegen die laufende Version, endet sie grün (Grundlage für „gilt als bestätigt“); scheitert sie,
    endet sie rot (kein Vermerk, nichts wird veröffentlicht). In beiden Fällen verändert sie nichts an der Seite."""
    gut = welt.attrappe(X)
    gruen = welt.kurztest(gut, X)
    assert gruen.code == 0, f"Vorab-Probe gegen funktionierende laufende Version muss grün sein: {gruen!r}"
    kaputt = welt.attrappe(X)
    kaputt.lage.kalender_fehler = True
    rot = welt.kurztest(kaputt, X)
    assert rot.code != 0, f"Gescheiterte Vorab-Probe muss rot enden: {rot!r}"
    assert gut.lage.schreibende_anfragen == [] and kaputt.lage.schreibende_anfragen == [], (
        f"Vorab-Probe hat Daten ändernde Anfragen gestellt: {gut.lage.schreibende_anfragen + kaputt.lage.schreibende_anfragen}")


def test_t15_ak13_alle_pruefpunkte_bestehen_live_check_gruen_neue_version_bleibt(welt):
    """T15 (Stufen-2-Teil) · AK13 · TASK-118 — Gegeben die neue Version Y ist live und funktioniert, wenn der
    Live-Check läuft, dann bestehen alle sechs Prüfpunkte und er endet grün (Grundlage für „Y bleibt live und
    wird als zuletzt bestätigt vermerkt“, Stufen-1-Teil); die Seite liefert danach unverändert Y aus und hat keine
    Daten ändernde Anfrage gesehen. (Grüner GitHub-Lauf → Stufe 3.)"""
    a = welt.attrappe(Y)
    lauf = welt.kurztest(a, Y)
    assert lauf.code == 0, f"Alle Prüfpunkte bestehen → Live-Check muss grün enden: {lauf!r}"
    for grund in (S.GRUND_FALSCHE_VERSION, S.MELDUNG_NICHT_EINSATZBEREIT):
        assert not _nennt(lauf, grund), f"Grüner Live-Check meldet „{grund}“: {lauf!r}"
    assert a.lage.version == Y and a.lage.schreibende_anfragen == [], (
        f"Live-Check hat etwas verändert: {a.lage.schreibende_anfragen}")


# ── Prüfpunkt 1: Version ───────────────────────────────────────────────────
def test_t6_ak6_seite_liefert_noch_die_alte_version_live_check_rot_falsche_version_live(welt):
    """T6 · AK6 · TASK-118 — Gegeben die Seite liefert noch Version X aus, erwartet ist Y, wenn der Live-Check
    läuft, dann ist er rot mit dem Grund „falsche Version live“."""
    _gegenprobe(S.PRUEFPUNKT_VERSION)
    a = welt.attrappe(X)
    lauf = welt.kurztest(a, Y)
    assert lauf.code != 0, f"Alte Version darf nicht grün sein: {lauf!r}"
    assert _nennt(lauf, S.GRUND_FALSCHE_VERSION), f"Grund „{S.GRUND_FALSCHE_VERSION}“ fehlt: {lauf!r}"
    _pruefe_gescheitert(lauf, S.PRUEFPUNKT_VERSION)


def test_t7_ak6_seite_liefert_die_erwartete_version_pruefpunkt_version_gruen(welt):
    """T7 · AK6 · TASK-118 — Gegeben die Seite liefert Y aus und alles andere funktioniert, wenn der Live-Check
    mit Erwartung Y läuft, dann besteht er (Prüfpunkt 1 grün, kein „falsche Version live“)."""
    a = welt.attrappe(Y)
    lauf = welt.kurztest(a, Y)
    assert lauf.code == 0, f"Live-Check muss bestehen: {lauf!r}"
    assert not _nennt(lauf, S.GRUND_FALSCHE_VERSION), f"Fälschlich „falsche Version live“: {lauf!r}"


# ── Prüfpunkt 2: Anmeldung ─────────────────────────────────────────────────
def test_t8_ak7_gueltiger_pruefzugang_anmeldung_gelingt_mit_gast_rolle(welt):
    """T8 · AK7 (und AK14: nur Gast-Rechte) · TASK-118 — Gegeben ein gültiger Prüf-Zugang, wenn der Live-Check
    läuft, dann gelingt die Anmeldung genau einmal mit der Gast-Rolle, nie mit Host-Rechten, und der Live-Check
    besteht."""
    a = welt.attrappe(Y)
    lauf = welt.kurztest(a, Y)
    assert lauf.code == 0, f"Live-Check muss bestehen: {lauf!r}"
    erfolgreich = [v for v in a.lage.anmeldeversuche if v["erfolg"]]
    assert len(erfolgreich) == 1 and erfolgreich[0]["rolle"] == "user", f"Anmeldungen: {a.lage.anmeldeversuche}"
    assert not any(v["rolle"] == "host" for v in a.lage.anmeldeversuche)


# ── Prüfpunkte 3–5: Karte, Feed, Kalender ──────────────────────────────────
def test_t9_ak8_karte_ohne_orte_live_check_rot_beim_pruefpunkt_karte(welt):
    """T9 · AK8 · TASK-118 — Gegeben die Version ist erreichbar, aber die Karte zeigt keine Orte, wenn der
    Live-Check läuft, dann ist er rot beim Prüfpunkt „Karte“."""
    _gegenprobe(S.PRUEFPUNKT_KARTE)
    a = welt.attrappe(Y)
    a.lage.orte = []
    lauf = welt.kurztest(a, Y)
    assert lauf.code != 0, f"Karte ohne Orte darf nicht grün sein: {lauf!r}"
    _pruefe_gescheitert(lauf, S.PRUEFPUNKT_KARTE)


def test_t10_ak9_feed_ohne_eintraege_live_check_rot_beim_pruefpunkt_feed(welt):
    """T10 · AK9 · TASK-118 — Gegeben der Feed hat keine Einträge, wenn der Live-Check läuft, dann ist er rot
    beim Prüfpunkt „Feed“."""
    _gegenprobe(S.PRUEFPUNKT_FEED)
    a = welt.attrappe(Y)
    a.lage.feed_modus = "leer"
    lauf = welt.kurztest(a, Y)
    assert lauf.code != 0, f"Leerer Feed darf nicht grün sein: {lauf!r}"
    _pruefe_gescheitert(lauf, S.PRUEFPUNKT_FEED)


def test_t10b_ak9_feed_meldet_einen_fehler_live_check_rot_beim_pruefpunkt_feed(welt):
    """T10b (ergänzt nach Test-Prüfung 24.10.2026) · AK9 „ohne Fehlermeldung“ · TASK-118 — Gegeben der Feed
    meldet beim Laden einen Fehler, wenn der Live-Check läuft, dann ist er rot beim Prüfpunkt „Feed“."""
    _gegenprobe(S.PRUEFPUNKT_FEED)
    a = welt.attrappe(Y)
    a.lage.feed_modus = "fehler"
    lauf = welt.kurztest(a, Y)
    assert lauf.code != 0, f"Feed mit Fehlermeldung darf nicht grün sein: {lauf!r}"
    _pruefe_gescheitert(lauf, S.PRUEFPUNKT_FEED)


def test_t11_ak9_feed_mit_genau_einem_eintrag_pruefpunkt_feed_gruen(welt):
    """T11 · AK9 · TASK-118 — Gegeben der Feed hat genau einen Eintrag (mehr wird bewusst nicht verlangt),
    wenn der Live-Check läuft, dann besteht er."""
    a = welt.attrappe(Y)
    a.lage.anzahl_feed = 1
    lauf = welt.kurztest(a, Y)
    assert lauf.code == 0, f"Feed mit einem Eintrag muss bestehen: {lauf!r}"


def test_t12_ak10_kalender_mit_fehlermeldung_live_check_rot_beim_pruefpunkt_kalender(welt):
    """T12 · AK10 · TASK-118 — Gegeben der Kalender zeigt eine Fehlermeldung, wenn der Live-Check läuft, dann
    ist er rot beim Prüfpunkt „Kalender“."""
    _gegenprobe(S.PRUEFPUNKT_KALENDER)
    a = welt.attrappe(Y)
    a.lage.kalender_fehler = True
    lauf = welt.kurztest(a, Y)
    assert lauf.code != 0, f"Kalender-Fehler darf nicht grün sein: {lauf!r}"
    _pruefe_gescheitert(lauf, S.PRUEFPUNKT_KALENDER)


# ── Prüfpunkt 6: Programmfehler (AK10a) ────────────────────────────────────
def test_t12a_ak10a_programmfehler_im_eigenen_code_live_check_rot(welt):
    """T12a · AK10a · TASK-118 — Gegeben auf einer geprüften Seite tritt ein Programmfehler aus dem eigenen
    FotoAlert-Code auf, wenn der Live-Check läuft, dann ist er rot beim Prüfpunkt „Programmfehler“."""
    _gegenprobe(S.PRUEFPUNKT_PROGRAMMFEHLER)
    a = welt.attrappe(Y)
    a.lage.eigener_programmfehler = True
    lauf = welt.kurztest(a, Y)
    assert lauf.code != 0, f"Programmfehler im eigenen Code darf nicht grün sein: {lauf!r}"
    _pruefe_gescheitert(lauf, S.PRUEFPUNKT_PROGRAMMFEHLER)


def test_t12b_ak10a_programmfehler_nur_aus_fremder_quelle_gruen_und_in_der_meldung(welt):
    """T12b · AK10a · TASK-118 — Gegeben nur eine fremde Quelle (Kartendienst) meldet einen Programmfehler und
    alle übrigen Prüfpunkte bestehen, wenn der Live-Check läuft, dann ist er grün (kein Rücksprung), und der
    fremde Fehler steht in der Meldung."""
    a = welt.attrappe(Y)
    a.lage.fremder_programmfehler = True
    lauf = welt.kurztest(a, Y)
    assert lauf.code == 0, f"Fehler nur aus fremder Quelle darf nicht rot machen: {lauf!r}"
    # Die Fehlermeldung der Fremdquelle enthält eine Zufallskennung, die nur im geworfenen Fehler steht —
    # nicht in Adressen oder Ladeprotokollen der Kartenbilder. Steht sie in der Meldung, ist der Fehler
    # als Fehler aufgeführt; Rückgabe 0 heißt „bestanden, kein Rücksprung“.
    assert a.lage.fremd_kennung in lauf.text(), (
        f"Programmfehler der fremden Quelle ist nicht als Fehler in der Meldung aufgeführt: {lauf!r}")


# ── Wiederholung (AK11) und Fehlalarm-Schutz (AK12) ────────────────────────
def test_t13_ak11_gescheiterter_pruefpunkt_wird_genau_einmal_wiederholt(welt):
    """T13 · AK11 · TASK-118 — Gegeben ein Prüfpunkt scheitert einmal und besteht bei der Wiederholung, dann ist
    der Live-Check grün; scheitert er zweimal, ist er rot; einen dritten Versuch gibt es nie. (Gemessen an den
    Feed-Abfragen: ein bestandener Durchgang braucht k Abfragen; mit Wiederholung höchstens 2·k.)"""
    gut = welt.attrappe(Y)
    assert welt.kurztest(gut, Y).code == 0, "Grundlage verfehlt: Kurztest gegen die gute Attrappe nicht grün"
    k = gut.lage.feed_abfragen
    assert k >= 1, "Grundlage verfehlt: Kurztest hat den Feed nie abgefragt"

    einmal = welt.attrappe(Y)
    einmal.lage.feed_modus = "erste_leer"
    lauf1 = welt.kurztest(einmal, Y)
    assert lauf1.code == 0, f"Einmal gescheitert, bei Wiederholung bestanden → grün erwartet: {lauf1!r}"
    assert einmal.lage.feed_abfragen <= 2 * k, f"Mehr als eine Wiederholung: {einmal.lage.feed_abfragen} > 2·{k}"

    zweimal = welt.attrappe(Y)
    zweimal.lage.feed_modus = "leer"
    lauf2 = welt.kurztest(zweimal, Y)
    assert lauf2.code != 0, f"Zweimal gescheitert → rot erwartet: {lauf2!r}"
    n = zweimal.lage.feed_abfragen
    assert k < n <= 2 * k, f"Erwartet genau eine Wiederholung (k={k} < n ≤ 2·k), gesehen n={n}"


def test_t14_ak12_degraded_und_gesperrte_fremd_kartenbilder_kein_grund_fuer_rot(welt):
    """T14 · AK12 · TASK-118 — Gegeben die Server-Statusabfrage meldet „degraded“ und Kartenbilder fremder
    Anbieter sind gesperrt, die sechs Prüfpunkte bestehen aber, wenn der Live-Check läuft, dann ist er grün
    (kein Rücksprung)."""
    a = welt.attrappe(Y)
    a.lage.status = "degraded"
    a.lage.kacheln_gesperrt = True
    lauf = welt.kurztest(a, Y)
    assert lauf.code == 0, f"„degraded“/fremde Kartenbilder allein dürfen nicht rot machen: {lauf!r}"


# ── Nur lesen (AK14) ───────────────────────────────────────────────────────
def test_t16_ak14_kurztest_veraendert_keine_daten(welt):
    """T16 · AK14 · TASK-118 — Gegeben die App hat Orte und Feed-Einträge, wenn der Live-Check läuft, dann ist
    der Datenbestand danach unverändert: Die Seite sieht keine einzige Daten ändernde Anfrage (Orte, Bilder,
    Bewertungen, Einstellungen); nur Anmelden/Abmelden."""
    a = welt.attrappe(Y)
    vorher = copy.deepcopy(a.lage.orte)
    lauf = welt.kurztest(a, Y)
    assert lauf.code == 0, f"Live-Check muss bestehen: {lauf!r}"
    assert a.lage.schreibende_anfragen == [], f"Daten ändernde Anfragen: {a.lage.schreibende_anfragen}"
    assert a.lage.orte == vorher


# ── Sicherheit des Zugangs (AK28, AK29) ────────────────────────────────────
# Stand der bestehenden Geheimnis-Verwendungen in .github/workflows/deploy.yml vor TASK-118 (gelesen 24.10.2026).
# Jede Zeile muss unverändert bleiben (AK28: bestehende Geheimnisse unverändert).
_BESTEHENDE_GEHEIMNIS_ZEILEN = [
    "FOTOALERT_HOST_PASSWORD: ${{ secrets.FOTOALERT_HOST_PASSWORD }}",
    "FOTOALERT_USER_PASSWORD: ${{ secrets.FOTOALERT_USER_PASSWORD }}",
    "FOTOALERT_AUTH_SECRET: ${{ secrets.FOTOALERT_AUTH_SECRET }}",
    'echo "${{ secrets.DEPLOY_SSH_KEY }}" > ~/.ssh/deploy_key',
    'echo "${{ secrets.SERVER_KNOWN_HOSTS }}" >> ~/.ssh/known_hosts',
    '"${{ secrets.SERVER_USER }}@${{ secrets.SERVER_IP }}" \\',
]
_TESTSERVER_GEHEIMNISSE = ("FOTOALERT_USER_PASSWORD", "FOTOALERT_HOST_PASSWORD", "FOTOALERT_AUTH_SECRET")
_DURCHSUCHT = {".py", ".sh", ".yml", ".yaml", ".md", ".json", ".txt", ".html", ".js", ".cfg", ".ini", ".toml",
               ".env", ".example", ".service", ".feature"}
_AUSGENOMMEN = {".git", "venv", "node_modules", "__pycache__", "data", "data_dev", "cache", "_worktrees",
                "_to_delete", "vendor", "ios"}
# Name des Geheimnisses mit einem direkt zugewiesenen Wert (nicht: ${{ secrets.… }}, $VARIABLE, os.environ…)
_ZUWEISUNG = re.compile(re.escape(S.GEHEIMNIS_NAME) + r"""["']?\s*[:=]\s*(?!["']?\$|["']?\s*$|os\.environ)(\S+)""")


def _projektdateien():
    for ordner, unterordner, dateien in os.walk(REPO_ROOT):
        unterordner[:] = [u for u in unterordner if u not in _AUSGENOMMEN]
        for name in dateien:
            d = Path(ordner) / name
            if (d.suffix in _DURCHSUCHT or name.startswith(".env")) and d.is_file() and d.stat().st_size < 2_000_000:
                yield d


def _schritte(ablauf: str):
    """Teilt den GitHub-Ablauf in Schritte (je „- name:“-Block)."""
    teile = re.split(r"(?m)^\s*- name:", ablauf)
    return teile[1:]


def test_t32_ak28_live_check_nutzt_nur_das_eigene_geheimnis(welt):
    """T32 (Stufen-2-Teil) · AK28 · TASK-118 — Für den Live-Check gibt es ein eigenes Geheimnis
    FOTOALERT_LIVECHECK_PASSWORD, das nur der Live-Check benutzt:
    (1) Kein Passwortwert steht in einer Projektdatei — keine Datei weist dem Geheimnis einen Wert zu, und ist
        der echte Wert in der Testumgebung vorhanden (GitHub), kommt er in keiner Projektdatei vor.
    (2) Die bestehenden Geheimnisse bleiben unverändert: jede bisherige Verwendung im GitHub-Ablauf steht
        unverändert da; die Schritte des Live-Checks verwenden keins der Test-Server-Geheimnisse.
    (3) Der Kurztest meldet sich nie mit den Test-Server-Geheimnissen an — auch nicht, wenn nur diese vorhanden
        sind —, sondern ausschließlich mit dem eigenen Prüf-Zugang.
    (Dass die bei GitHub hinterlegten Werte selbst unverändert sind, sieht nur Stephan → Stufe 3.)"""
    echter_wert = os.environ.get(S.GEHEIMNIS_NAME, "").encode("utf-8")
    funde = []
    for d in _projektdateien():
        inhalt = d.read_bytes()
        rel = str(d.relative_to(REPO_ROOT))
        if echter_wert and echter_wert in inhalt:
            funde.append(f"{rel}: enthält den Wert des Geheimnisses")
        for nr, zeile in enumerate(inhalt.decode("utf-8", "replace").splitlines(), 1):
            if _ZUWEISUNG.search(zeile):
                funde.append(f"{rel}:{nr}: weist {S.GEHEIMNIS_NAME} einen Wert zu")   # Wert nie ausgeben
    assert funde == [], f"Passwort steht in Projektdateien: {funde}"

    ablauf = WORKFLOW.read_text(encoding="utf-8")
    zeilen = {z.strip() for z in ablauf.splitlines()}
    fehlend = [z for z in _BESTEHENDE_GEHEIMNIS_ZEILEN if z.strip() not in zeilen]
    assert fehlend == [], f"Bestehende Geheimnis-Verwendung verändert/entfernt: {fehlend}"
    live = [t for t in _schritte(ablauf) if f"secrets.{S.GEHEIMNIS_NAME}" in t]
    assert live, f"Verhalten fehlt: kein Schritt in deploy.yml nutzt secrets.{S.GEHEIMNIS_NAME}"
    for t in live:
        name = t.strip().splitlines()[0]
        benutzt = [g for g in _TESTSERVER_GEHEIMNISSE if f"secrets.{g}" in t]
        assert not benutzt, f"Live-Check-Schritt „{name}“ benutzt Test-Server-Geheimnisse: {benutzt}"

    a = welt.attrappe(Y)
    nur_fremde = welt.kurztest(a, Y, geheimnis=None, zusatz_env={
        "FOTOALERT_USER_PASSWORD": welt.pruefzugang, "FOTOALERT_HOST_PASSWORD": welt.host_passwort})
    assert nur_fremde.code != 0 and a.lage.anmeldeversuche == [], (
        f"Kurztest hat sich mit Test-Server-Geheimnissen angemeldet: {a.lage.anmeldeversuche}; {nur_fremde!r}")
    lauf = welt.kurztest(a, Y)
    assert lauf.code == 0, f"Live-Check mit eigenem Prüf-Zugang muss bestehen: {lauf!r}"
    assert a.lage.anmeldeversuche and all(v["passwort_gleich_pruefzugang"] for v in a.lage.anmeldeversuche)


def test_t33_ak29_geheimnis_erscheint_nirgends_im_klartext(welt):
    """T33 (Stufen-2-Teil) · AK29 · TASK-118 — Gegeben ein bestandener und ein gescheiterter Live-Check (mit
    Bildschirmfoto), dann enthält weder die Ausgabe noch eine Ergebnisdatei noch ein Bildschirmfoto den Wert des
    Prüf-Zugangs (0 Treffer). (Text-/Pixelprüfung des sichtbaren Eingabefelds auf dem Bildschirmfoto → Stufe 3.)"""
    gut = welt.attrappe(Y)
    kaputt = welt.attrappe(Y)
    kaputt.lage.orte = []
    laeufe = [welt.kurztest(gut, Y), welt.kurztest(kaputt, Y)]
    assert laeufe[0].code == 0 and laeufe[1].code != 0, f"Grundlage verfehlt: {laeufe!r}"
    assert laeufe[1].bildschirmfotos(), "Gescheiterter Live-Check hat kein Bildschirmfoto abgelegt (AK25/AK29)"
    wert = welt.pruefzugang.encode("utf-8")
    treffer = [name for lauf in laeufe for name, inhalt in lauf.alle_bytes() if wert in inhalt]
    assert treffer == [], f"Prüf-Zugang im Klartext gefunden in: {treffer}"
