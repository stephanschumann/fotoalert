"""TASK-118 — Echter Live-Check mit automatischem Rücksprung: Teststufe 1 (Wegwerf-Nachbau, offline).

Testfälle aus der Spec (docs/analyse-entwurf/TASK-118_SPEC.md, „Testfall-Liste“), Stufe 1:
T15, T17, T18, T19, T20, T21, T22, T23 (Stufen-1-Teil), T25, T26, T27, T28 (Stufen-1-Teil), T36.
Geschrieben VOR der Umsetzung (fotoalert-test Teil A); Rot ist gegen den heutigen Stand beabsichtigt,
wo das Verhalten fehlt.

Aufbau: Jeder Test bekommt einen eigenen Wegwerf-Nachbau der Server-Seite (server_nachbau.py) in
einem Temp-Ordner außerhalb des Projekts — Wegwerf-Git-Projekt mit den Versionen X („gut“),
Y („kaputt 1“), Z („kaputt 2“) — hier als App-Versionen 1.26.1, 1.27.0, 1.28.0, die echten Skripte aus FotoAlert/deploy/, mitschreibende Platzhalter
für Dienst-Neustart, Webserver, Statusabfrage. Der Ordner wird im Teardown gelöscht, auch bei
Fehlschlag. Kein Netz, kein SSH, kein echtes Repo, keine Geheimnisse.

Zwei Auslöser für einen Rücksprung werden unterschieden:
  - „Server bleibt stumm“: die neue Version antwortet nach dem Neustart nicht (heute schon vorhanden,
    AK23) — der Veröffentlichungs-Ablauf springt selbst zurück.
  - „Live-Check rot“: die neue Version antwortet, der Kurztest von GitHub aus scheitert; der GitHub-Lauf
    ruft dann den automatischen Rücksprung auf dem Server (neu, AK15).
Wie Rücksprung und Vermerk aufgerufen werden, ist ein Vorschlag dieser Tests: schnittstelle.py.

Voraussetzungen: bash, git, GNU-Werkzeuge (Linux/GitHub-Runner; das heutige deploy.sh nutzt `sed -i`
ohne Suffix, das auf macOS nicht läuft).
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from . import schnittstelle as S
from .server_nachbau import ServerNachbau

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

X, Y, Z = "1.26.1", "1.27.0", "1.28.0"   # „gut“, „kaputt 1“, „kaputt 2“
SERVER_STUMM = "server_stumm"
LIVE_CHECK_ROT = "live_check_rot"
AUSLOESER = pytest.mark.parametrize("ausloeser", [SERVER_STUMM, LIVE_CHECK_ROT],
                                    ids=["ausloeser_server_bleibt_stumm", "ausloeser_live_check_rot"])


@pytest.fixture
def welt():
    """Eigener Wegwerf-Nachbau je Test; wird im Teardown gelöscht (auch bei Fehlschlag/Abbruch)."""
    assert shutil.which("git") and shutil.which("bash"), "Teststufe 1 braucht git und bash"
    wurzel = Path(tempfile.mkdtemp(prefix="fa118-nachbau-"))
    try:
        w = ServerNachbau(wurzel)
        w.aufbauen(X)
        yield w
        assert not w.verbotene_aufrufe(), f"Nachbau hat Netz/SSH versucht: {w.verbotene_aufrufe()}"
    finally:
        shutil.rmtree(wurzel, ignore_errors=True)


def _zustand(w: ServerNachbau) -> str:
    return (f"läuft={w.laufende_version()!r}, Dateien={w.version_auf_platte()!r}, "
            f"gespeicherter Stand={w.gespeicherter_stand()!r}, Notizen={w.notizen}")


def _scheitert(w: ServerNachbau, version: str, ausloeser: str):
    """„Version V wird veröffentlicht“ + „Live-Check scheitert“ (je nach Auslöser) → „App springt zurück“."""
    if ausloeser == SERVER_STUMM:
        erg = w.veroeffentliche(version, stumm=True)
        assert erg.code != 0, f"Veröffentlichung einer stummen Version darf nicht grün enden: {erg!r}"
        return erg
    erg = w.veroeffentliche(version)
    assert erg.code == 0, f"Grundlage verfehlt — Veröffentlichung von {version} scheiterte: {erg!r}"
    assert w.laufende_version() == version, f"Grundlage verfehlt — {version} läuft nicht: {_zustand(w)}"
    r = w.ruecksprung_nach_rotem_live_check()
    assert not r.fehlt, (
        "Verhalten fehlt: Nach rotem Live-Check gibt es keinen automatischen Rücksprung auf dem Server "
        f"({S.SKRIPT_AUTOMATIK} {' '.join(S.ARGS_RUECKSPRUNG)}). {_zustand(w)}")
    return r


# ── AK13 ────────────────────────────────────────────────────────────────────
def test_t15_ak13_bestandener_live_check_vermerkt_neue_version_als_zuletzt_bestaetigt(welt):
    """T15 · AK13 · TASK-118 — Gegeben X ist live und bestätigt, wenn Y veröffentlicht wird und alle
    Prüfpunkte bestehen, dann bleibt Y live und die Marke „zuletzt bestätigt“ zeigt Y: Scheitert danach Z,
    landet die App auf Y (nicht auf X). Der grüne GitHub-Lauf selbst → Stufe 3."""
    welt.version_ist_live_und_bestaetigt(X)
    erg = welt.veroeffentliche(Y)
    assert erg.code == 0, f"Veröffentlichung von Y scheiterte: {erg!r}"
    r = welt.bestaetigen()
    assert not r.fehlt, f"Verhalten fehlt: Vermerk „zuletzt bestätigt“ nach grünem Live-Check ({r.ausgabe})"
    assert r.code == 0, f"Vermerk für Y scheiterte: {r!r}"
    assert welt.laufende_version() == Y, f"Y muss live bleiben: {_zustand(welt)}"
    _scheitert(welt, Z, LIVE_CHECK_ROT)
    assert welt.laufende_version() == Y and welt.gespeicherter_stand() == Y, (
        f"Marke „zuletzt bestätigt“ zeigt nicht Y — nach Scheitern von Z erwartet Y: {_zustand(welt)}")


# ── AK15 ────────────────────────────────────────────────────────────────────
@AUSLOESER
def test_t17_ak15_nach_gescheitertem_live_check_laeuft_die_zuletzt_bestaetigte_version(welt, ausloeser):
    """T17 · AK15 · TASK-118 — Gegeben X ist live und bestätigt, wenn Y veröffentlicht wird und scheitert,
    dann springt die App ohne Rückfrage zurück und danach läuft X (Dienst und Dateien).

    Beim Auslöser „Server bleibt stumm“ grün gegen den heutigen Stand — bestehendes Verhalten (Spec-Klarstellung
    24.10.2026): Antwortet die neue Version nicht, holt die App schon heute die vorherige Version zurück und
    startet sie; hier ist die vorherige zugleich die bestätigte. Gegenprobe (24.10.2026, Wegwerf-Kopie mit
    falscher Erwartung „danach läuft Y“): rot — der Test erkennt also eine ausbleibende Rückkehr zu X.
    Beim Auslöser „Live-Check rot“ rot (automatischer Rücksprung fehlt)."""
    welt.version_ist_live_und_bestaetigt(X)
    _scheitert(welt, Y, ausloeser)
    assert welt.laufende_version() == X and welt.version_auf_platte() == X, (
        f"Nach dem Rücksprung muss X laufen: {_zustand(welt)}")


# ── AK16 ────────────────────────────────────────────────────────────────────
@AUSLOESER
def test_t18_ak16_zwei_gescheiterte_veroeffentlichungen_landen_beide_auf_derselben_bestaetigten_version(welt, ausloeser):
    """T18 · AK16 · TASK-118 — Gegeben X ist live und bestätigt, wenn Y scheitert und danach Z scheitert,
    dann läuft nach beiden Rücksprüngen X — nie Y (Y hat ihren eigenen Live-Check nicht bestanden)."""
    welt.version_ist_live_und_bestaetigt(X)
    _scheitert(welt, Y, ausloeser)
    assert welt.laufende_version() == X, f"Nach dem ersten Rücksprung muss X laufen: {_zustand(welt)}"
    ab = len(welt.protokoll())
    _scheitert(welt, Z, ausloeser)
    gestartet = welt.neustarts_ab(ab)
    assert Y not in gestartet, f"Beim Rücksprung von Z wurde die gescheiterte Version Y gestartet: {gestartet}; {_zustand(welt)}"
    assert welt.laufende_version() == X, f"Nach dem zweiten Rücksprung muss X laufen: {_zustand(welt)}"


# ── AK17 ────────────────────────────────────────────────────────────────────
@AUSLOESER
def test_t19_ak17_nach_ruecksprung_und_server_neustart_laeuft_die_zurueckgeholte_version(welt, ausloeser):
    """T19 · AK17 · TASK-118 — Gegeben die App ist nach dem Scheitern von Y auf X zurückgesprungen, wenn der
    Server neu gestartet wird, dann läuft X.

    Beim Auslöser „Server bleibt stumm“ grün gegen den heutigen Stand — bestehendes Verhalten: Beim Rücksprung
    liegen schon heute die Dateien der zurückgeholten Version auf dem Server, und ein Neustart startet die App
    aus genau diesen Dateien, ohne neuen Code zu holen. Die Lücke „der Server merkt sich die kaputte Version“
    zeigt sich erst, wenn die Veröffentlichung erneut angestoßen wird (T20), und am aktuellen Stand des Servers
    (T21). Gegenprobe (24.10.2026, Wegwerf-Kopie mit falscher Erwartung „nach dem Neustart läuft Y“): rot.
    Beim Auslöser „Live-Check rot“ rot (automatischer Rücksprung fehlt)."""
    welt.version_ist_live_und_bestaetigt(X)
    _scheitert(welt, Y, ausloeser)
    welt.server_neustart()
    assert welt.laufende_version() == X, f"Nach dem Server-Neustart muss X laufen: {_zustand(welt)}"


@AUSLOESER
def test_t20_ak17_erneutes_anstossen_ohne_neuen_code_bringt_die_kaputte_version_nicht_still_zurueck(welt, ausloeser):
    """T20 · AK17 · TASK-118 — Gegeben die App ist nach dem Scheitern von Y auf X zurückgesprungen, wenn die
    Veröffentlichung ohne neuen Code erneut angestoßen wird, dann läuft Y nicht ungeprüft: Entweder X bleibt
    (Dienst, Dateien und gespeicherter Stand), oder Y wird erneut vollständig veröffentlicht (Neustart mit Y und
    anschließende Statusabfrage, danach prüft der Live-Check erneut). Auch ein anschließender Server-Neustart
    bringt Y nicht still zurück."""
    welt.version_ist_live_und_bestaetigt(X)
    _scheitert(welt, Y, ausloeser)
    ab = welt.markiere("erneut anstossen")
    erneut = welt.veroeffentliche_erneut_ohne_neuen_code()
    nach_erneut = _zustand(welt)
    neustarts = welt.neustarts_ab(ab)
    x_bleibt = (welt.laufende_version() == X and welt.version_auf_platte() == X
                and welt.gespeicherter_stand() == X)
    y_erneut_geprueft = False
    if Y in neustarts:
        nach_start_y = welt.protokoll()[ab:]
        idx = max(i for i, z in enumerate(nach_start_y) if z == f"neustart {Y}")
        y_erneut_geprueft = any(z.startswith(f"statusabfrage {Y}") for z in nach_start_y[idx:])
    welt.server_neustart()
    nach_neustart = welt.laufende_version()
    assert x_bleibt or y_erneut_geprueft, (
        "Nach erneutem Anstoßen läuft Y ungeprüft bzw. liegt Y still auf der Platte: "
        f"{nach_erneut}; Neustarts danach={neustarts}; Ausgabe: {erneut!r}")
    assert x_bleibt is False or nach_neustart == X, (
        f"Nach anschließendem Server-Neustart läuft {nach_neustart!r} statt X: {_zustand(welt)}")


@AUSLOESER
def test_t21_ak17_nach_ruecksprung_fuehrt_der_server_die_zurueckgeholte_version_als_aktuellen_stand(welt, ausloeser):
    """T21 · AK17 · TASK-118 — Gegeben die App ist nach dem Scheitern von Y auf X zurückgesprungen, dann führt
    der Server X als seinen aktuellen Stand (den Stand, auf dem jedes weitere Ziehen und jeder Neustart aufsetzt),
    nicht Y."""
    welt.version_ist_live_und_bestaetigt(X)
    _scheitert(welt, Y, ausloeser)
    assert welt.gespeicherter_stand() == X, f"Server führt nicht X als aktuellen Stand: {_zustand(welt)}"


# ── AK18 ────────────────────────────────────────────────────────────────────
def test_t22_ak18_ruecksprung_setzt_webserver_einstellungen_und_service_worker_auf_stand_x(welt):
    """T22 · AK18 · TASK-118 — Gegeben X ist live und bestätigt und Y bringt geänderte Webserver-Einstellungen
    und eine geänderte Service-Worker-Datei mit, wenn Y veröffentlicht wird und der Live-Check scheitert, dann
    sind nach dem Rücksprung beide wieder auf Stand X und der Webserver wurde neu geladen."""
    welt.version_ist_live_und_bestaetigt(X)
    erg = welt.veroeffentliche(Y, webserver_aendern=True, sw_aendern=True)
    assert erg.code == 0, f"Veröffentlichung von Y scheiterte: {erg!r}"
    assert welt.webserver_stand_live() == Y, "Grundlage verfehlt: Webserver-Einstellungen von Y nicht übernommen"
    ab = len(welt.protokoll())
    r = welt.ruecksprung_nach_rotem_live_check()
    assert not r.fehlt, ("Verhalten fehlt: Nach rotem Live-Check gibt es keinen automatischen Rücksprung "
                         f"({S.SKRIPT_AUTOMATIK}). Webserver-Stand={welt.webserver_stand_live()!r}")
    assert welt.webserver_stand_live() == X, f"Webserver-Einstellungen nicht auf X: {welt.webserver_stand_live()!r}"
    assert welt.sw_stand_auf_platte() == X, f"Service-Worker-Datei nicht auf X: {welt.sw_stand_auf_platte()!r}"
    neuladungen = welt.webserver_neuladungen_ab(ab)
    assert neuladungen and neuladungen[-1].endswith(f" {X}"), f"Webserver nicht mit Stand X neu geladen: {neuladungen}"


# ── AK19 ────────────────────────────────────────────────────────────────────
def test_t23_ak19_ruecksprung_meldet_die_zurueckgeholte_version_fuer_den_erneuten_kurztest(welt):
    """T23 (Stufen-1-Teil) · AK19 · TASK-118 — Gegeben X ist live und bestätigt, wenn Y veröffentlicht wird,
    der Live-Check scheitert und die App zurückspringt, dann läuft X, und der Rücksprung meldet die
    zurückgeholte Version X und dass er gelungen ist — damit läuft der erneute Kurztest gegen genau X und sein
    Ergebnis kommt in die Meldung. (Kurztest-Lauf und Meldung im GitHub-Lauf → Stufe 3.)"""
    welt.version_ist_live_und_bestaetigt(X)
    r = _scheitert(welt, Y, LIVE_CHECK_ROT)
    assert welt.laufende_version() == X, f"Rücksprung nicht auf X: {_zustand(welt)}"
    assert r.code == 0, f"Gelungener Rücksprung muss als gelungen zurückkommen: {r!r}"
    assert X in r.ausgabe, f"Rücksprung meldet die zurückgeholte Version {X} nicht (Ziel für den erneuten Kurztest): {r!r}"


# ── AK21 ────────────────────────────────────────────────────────────────────
@AUSLOESER
def test_t25_ak21_ruecksprung_laesst_die_daten_der_nutzer_unangetastet(welt, ausloeser):
    """T25 · AK21 · TASK-118 — Gegeben X ist live und bestätigt, wenn Nutzer Daten anlegen und danach auf X
    zurückgesprungen wird, dann sind die Daten unverändert vorhanden; die Datenbank wurde nicht angefasst.
    (Auslöser „Server bleibt stumm“: der Rücksprung folgt im selben Ablauf, die Daten liegen daher schon vor
    der Veröffentlichung; Auslöser „Live-Check rot“: Daten entstehen zwischen Veröffentlichung und Rücksprung.)

    Beim Auslöser „Server bleibt stumm“ grün gegen den heutigen Stand — bestehendes Verhalten (Spec-Klarstellung
    24.10.2026): Der heutige Rücksprung setzt nur die App zurück, Nutzerdaten bleiben liegen. Gegenprobe
    (24.10.2026, Wegwerf-Kopie mit falscher Erwartung „Daten sind danach verändert“): rot.
    Beim Auslöser „Live-Check rot“ rot (automatischer Rücksprung fehlt)."""
    welt.version_ist_live_und_bestaetigt(X)
    inhalt = "datensatz-zwischen-veroeffentlichung-und-ruecksprung\n"
    if ausloeser == SERVER_STUMM:
        dateien = welt.lege_datensatz_an(inhalt)
        vorher = {d: d.stat().st_mtime_ns for d in dateien}
        _scheitert(welt, Y, ausloeser)
    else:
        erg = welt.veroeffentliche(Y)
        assert erg.code == 0, f"Veröffentlichung von Y scheiterte: {erg!r}"
        dateien = welt.lege_datensatz_an(inhalt)
        vorher = {d: d.stat().st_mtime_ns for d in dateien}
        r = welt.ruecksprung_nach_rotem_live_check()
        assert not r.fehlt, f"Verhalten fehlt: kein automatischer Rücksprung nach rotem Live-Check ({S.SKRIPT_AUTOMATIK})"
    assert welt.laufende_version() == X, f"Rücksprung nicht erfolgt: {_zustand(welt)}"
    for d in dateien:
        assert d.exists(), f"Daten nach dem Rücksprung verschwunden: {d.name}"
        assert d.read_text(encoding="utf-8") == inhalt, f"Daten nach dem Rücksprung verändert: {d.name}"
        assert d.stat().st_mtime_ns == vorher[d], f"Datei wurde beim Rücksprung angefasst: {d.name}"


# ── AK22 ────────────────────────────────────────────────────────────────────
@AUSLOESER
def test_t26_ak22_stummer_dienst_nach_ruecksprung_meldet_fehlschlag_ohne_weiteren_ruecksprung(welt, ausloeser):
    """T26 · AK22 · TASK-118 — Gegeben X ist live und bestätigt, wenn nach dem Scheitern von Y auch die
    zurückgeholte Version stumm bleibt, dann endet der Ablauf rot mit der Meldung „Rücksprung fehlgeschlagen –
    manueller Eingriff nötig“, und es folgt kein weiterer automatischer Rücksprung (keine andere Version wird
    gestartet)."""
    welt.version_ist_live_und_bestaetigt(X)
    if ausloeser == SERVER_STUMM:
        welt.setze_stumm(X)
        ab = len(welt.protokoll())
        erg = welt.veroeffentliche(Y, stumm=True)
        gestartet = welt.neustarts_ab(ab)
        assert gestartet[:1] == [Y], f"Grundlage verfehlt: Y wurde nicht gestartet: {gestartet}"
        nach_ruecksprung = gestartet[1:]
    else:
        erg0 = welt.veroeffentliche(Y)
        assert erg0.code == 0, f"Veröffentlichung von Y scheiterte: {erg0!r}"
        welt.setze_stumm(X)
        ab = len(welt.protokoll())
        erg = welt.ruecksprung_nach_rotem_live_check()
        assert not erg.fehlt, f"Verhalten fehlt: kein automatischer Rücksprung nach rotem Live-Check ({S.SKRIPT_AUTOMATIK})"
        nach_ruecksprung = welt.neustarts_ab(ab)
    assert erg.code != 0, f"Ablauf muss rot enden: {erg!r}"
    assert S.enthaelt_meldung(erg.ausgabe, S.MELDUNG_RUECKSPRUNG_FEHLGESCHLAGEN), (
        f"Meldung „{S.MELDUNG_RUECKSPRUNG_FEHLGESCHLAGEN}“ fehlt: {erg!r}")
    assert nach_ruecksprung and set(nach_ruecksprung) == {X}, (
        f"Nach dem Rücksprung darf nur X gestartet werden (kein weiterer Rücksprung): {nach_ruecksprung}")


# ── AK23 ────────────────────────────────────────────────────────────────────
def test_t27_ak23_stummer_server_springt_auf_die_zuletzt_bestaetigte_statt_die_vorherige_version(welt):
    """T27 · AK23 · TASK-118 — Gegeben X ist live und bestätigt und Y wurde danach veröffentlicht, aber nie
    bestätigt (kein Live-Check-Ergebnis), wenn Z veröffentlicht wird und der Server nach dem Neustart gar nicht
    antwortet, dann springt die App auf X zurück — die zuletzt bestätigte, nicht die vorherige Version — und der
    Server führt X als aktuellen Stand (gleiche Wirkung wie AK17)."""
    welt.version_ist_live_und_bestaetigt(X)
    erg = welt.veroeffentliche(Y)
    assert erg.code == 0, f"Veröffentlichung von Y scheiterte: {erg!r}"
    _scheitert(welt, Z, SERVER_STUMM)
    assert welt.laufende_version() == X, f"Erwartet Rücksprung auf die zuletzt bestätigte X: {_zustand(welt)}"
    assert welt.gespeicherter_stand() == X, f"Server führt nicht X als aktuellen Stand: {_zustand(welt)}"


# ── AK24 ────────────────────────────────────────────────────────────────────
def test_t28_ak24_ohne_marke_gilt_die_laufende_version_nach_bestandener_vorab_probe_als_bestaetigt(welt):
    """T28 (Stufen-1-Teil) · AK24 · TASK-118 — Gegeben es gibt noch keine bestätigte Version und X läuft, wenn
    die Vorab-Probe gegen X besteht, dann entsteht auf dem Server die Marke „zuletzt bestätigt“ und X gilt als
    bestätigt: Scheitert anschließend Y, läuft wieder X.

    Zweig „Vorab-Probe rot → keine Marke, nichts veröffentlicht“ bewusst NICHT in Stufe 1 (entschieden in der
    Test-Prüfung, Runde 3): Bei roter Vorab-Probe erreicht den Server keine Handlung — der Lauf endet vorher.
    Eine Server-Prüfung „danach unverändert“ hätte zwischen vorher und nachher keine Handlung und wäre immer
    erfüllt. Belegt wird der Zweig dort, wo er beobachtbar ist: dass die Vorab-Probe rot endet, im
    Stufen-2-Teil (Kurztest-Bereich); dass der Lauf danach weder vermerkt noch veröffentlicht, im GitHub-Ablauf
    (Stufe 3, zusammen mit T2)."""
    assert welt.laufende_version() == X
    vorher = welt.server_abbild()
    r = welt.bestaetigen()   # Vorab-Probe grün → Vermerk
    assert not r.fehlt, f"Verhalten fehlt: Vermerk „zuletzt bestätigt“ nach bestandener Vorab-Probe ({r.ausgabe})"
    assert r.code == 0, f"Vermerk scheiterte: {r!r}"
    assert welt.server_abbild() != vorher, "Nach bestandener Vorab-Probe ist keine Marke „zuletzt bestätigt“ entstanden"
    _scheitert(welt, Y, LIVE_CHECK_ROT)
    assert welt.laufende_version() == X and welt.gespeicherter_stand() == X, f"X gilt nicht als bestätigt: {_zustand(welt)}"


# ── AK32 ────────────────────────────────────────────────────────────────────
def test_t36_ak32_manueller_ruecksprung_fragt_weiter_nach_automatischer_laeuft_ohne_eingabe(welt):
    """T36 · AK32 · TASK-118 — Gegeben X ist live und bestätigt und Y ist veröffentlicht, wenn Stephan von Hand
    zurückspringt, dann geschieht ohne Zustimmung nichts (keine Antwort oder „n“ → alles unverändert, die
    Rückfrage existiert weiter), mit Zustimmung („j“) springt die App tatsächlich auf X zurück (Dienst und
    gespeicherter Stand). Der automatische Rücksprung läuft dagegen ohne jede Eingabe durch: Nach Scheitern von
    Z läuft wieder X."""
    welt.version_ist_live_und_bestaetigt(X)
    erg = welt.veroeffentliche(Y)
    assert erg.code == 0, f"Veröffentlichung von Y scheiterte: {erg!r}"
    for antwort in ("", "n\n"):
        m = welt.manueller_ruecksprung(eingabe=antwort)
        assert not m.fehlt, "Manueller Rücksprung ist nicht mehr vorhanden"
        assert welt.laufende_version() == Y and welt.gespeicherter_stand() == Y, (
            f"Manueller Rücksprung ohne Zustimmung (Antwort {antwort!r}) hat etwas verändert: {_zustand(welt)}; {m!r}")
    j = welt.manueller_ruecksprung(eingabe="j\n")
    assert (welt.laufende_version(), welt.version_auf_platte(), welt.gespeicherter_stand()) == (X, X, X), (
        f"Manueller Rücksprung mit Zustimmung hat nicht auf X zurückgesprungen: {_zustand(welt)}; {j!r}")
    erg = welt.veroeffentliche(Z)
    assert erg.code == 0, f"Veröffentlichung von Z scheiterte: {erg!r}"
    a = welt.ruecksprung_nach_rotem_live_check()
    assert not a.fehlt, f"Verhalten fehlt: automatischer Rücksprung ohne Eingabe ({S.SKRIPT_AUTOMATIK})"
    assert welt.laufende_version() == X, f"Automatischer Rücksprung ohne Eingabe nicht durchgelaufen: {_zustand(welt)}; {a!r}"
