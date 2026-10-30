"""TASK-117 (inkl. TASK-112) — Probelauf vor dem Hochladen: Tests des Release-Befehls von außen.

Verbindliche Spec: docs/analyse-entwurf/TASK-117_SPEC.md (= Spec-Abschnitt im Ticket), Testfall-Liste
TF-01 … TF-36. Geschrieben VOR der Umsetzung (fotoalert-test Teil A); gegen den unveränderten Befehl
müssen die Verhaltens-Tests rot sein.

Ausführung: Jeder Test baut eine Übungsablage im pytest-Temp-Ordner (Wegwerf-Repo + Wegwerf-GitHub +
Platzhalter der gemeinsamen Prüfliste), startet darin eine KOPIE des echten Befehls und prüft nur
sichtbare Wirkung: Ausgabe, Protokoll, Versionsnummer, was auf dem Wegwerf-GitHub ankam, was die
Prüfliste sah. Unterbau und Schnittstellen-Vorschlag: task117_adapter.py.

Automatisch hier: TF-02–TF-04, TF-06–TF-11, TF-13, TF-15, TF-17–TF-36 (laut Testplan der Spec) sowie
TF-37 zu AK23a und TF-38 zu AK23b; TF-26 gehört seit der Klarstellung nach Modus T zu AK23a (neu nach Stephans Entscheidung „liegen lassen“, 24.10.2026; TF-25/TF-26 an das
präzisierte AK23 angepasst).

Spätere Prüfungen (nicht automatisch in dieser Datei — wer/wann/wie):
  • TF-01 (AK1)  nur auf Stephans Mac, echte Prüfliste: Protokoll zeigt Backend-Testsuite,
                 Oberflächen-Check und Browser-Tests als gelaufen (Messlauf bei der Umsetzung).
  • TF-05 (AK5)  nur auf Stephans Mac, echte Prüfliste: Prüfsumme der Entwicklungsdatenbank vorher =
                 nachher; Ortszahl im Probelauf = 0.
  • TF-12 (AK10) beim ersten GitHub-Lauf nach dem Umbau: Testanzahl und Ergebnis je Prüf-Job gegen
                 den letzten Lauf vor dem Umbau.
  • TF-13 (AK11) Ergänzung nur auf dem Mac mit echter Prüfliste: Probelauf protokolliert die
                 verwendete Browser-Werkzeug-Version (hier nur der Dateivergleich).
  • TF-14 (AK12) nur auf Stephans Mac: lokaler Entwicklungsserver antwortet nach grünem und rotem
                 Probelauf weiter, kein Testserver bleibt übrig (Prozessliste vorher/nachher).
  • TF-16 (AK14) nur auf Stephans Mac: Probelauf-Dauer ≤ 10 min, Dauer ins Ticket, Stephan melden.
  • TF-17 (AK15) Ergänzung nur auf dem Mac mit echter Prüfliste (Server- und Testprotokolle).
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from task117_adapter import (  # noqa: F401  (uebung ist eine Fixture)
    AUSGANGSVERSION,
    BACKLOG_RELPFAD,
    BEFEHL_RELPFAD,
    GITHUB_PRUEFBESCHREIBUNG,
    GITHUB_PRUEFUNG_LINK_MUSTER,
    MELDUNG_KEINE_NEUE_VERSION,
    MELDUNG_NICHTS_NEUES,
    NAECHSTE_PATCH_VERSION,
    PRUEFBLOECKE,
    PRUEFLISTE_RELPFAD,
    PRUEFWERTE,
    REPO_ROOT,
    VERSIONSDATEIEN,
    projektordner_pruefsummen,
    uebung,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

TESTS_DIR = Path(__file__).resolve().parent


def _nichts_veraendert(u, vorher, erg, was="Befehl"):
    nachher = u.zustand()
    assert nachher == vorher, erg.zeige(
        f"Befund: {was} hat etwas verändert, obwohl er vor jeder Änderung abbrechen muss "
        f"(geändert: {[k for k in vorher if vorher[k] != nachher[k]]})")


def _kein_probelauf(u, erg):
    assert u.probelaeufe() == [], erg.zeige(
        "Befund: Der Probelauf lief, obwohl der Befehl vorher hätte abbrechen müssen")


def _genau_ein_probelauf(u, erg):
    laeufe = u.probelaeufe()
    assert len(laeufe) == 1, erg.zeige(
        f"Befund: erwartet genau einen Probelauf über die gemeinsame Prüfliste, gesehen {len(laeufe)}")
    return laeufe[0]


# ═════════════════════════════════════════════════════════════════════════════
# A · Probelauf vor dem Hochladen
# ═════════════════════════════════════════════════════════════════════════════

def test_tf02_ak2_andere_python_version_bricht_vor_jeder_aenderung_ab(uebung):
    """TASK-117 · TF-02 · AK2 — *Mac hat Python 3.11 aktiv* → *Release starten* →
    *Abbruch „Python 3.12 nötig, 3.11 gefunden“*, *nichts verändert*. Quelle: Spec AK2."""
    u = uebung
    u.standard_ticket()
    u.python_ist("3.11.9")
    vorher = u.zustand()
    erg = u.release_starten()
    assert re.search(r"\b3\.12\b", erg.ausgabe) and re.search(r"\b3\.11(\.9)?\b", erg.ausgabe), erg.zeige(
        "Befund: Meldung nennt nicht die gefundene (3.11) und die nötige (3.12) Python-Version")
    _nichts_veraendert(u, vorher, erg)
    _kein_probelauf(u, erg)


def test_tf03_ak3_nicht_mitgehende_rote_testdatei_beeinflusst_probelauf_nicht(uebung):
    """TASK-117 · TF-03 · AK3 — *Nicht mitgehende rote Testdatei liegt im Arbeitsordner* →
    *Release starten* → *Probelauf grün*, Datei nicht in der gesehenen Dateiliste. Quelle: Spec AK3."""
    u = uebung
    u.standard_ticket()
    rote = "FotoAlert/backend/tests/test_lokal_rot.py"
    u.ignoriere(rote)
    u.schreibe(rote, "def test_lokal_rot():\n    assert False\n")
    u.pruefliste(modus="rot_wenn_datei", dateimuster="test_lokal_rot.py")
    stand = u.github_stand()
    erg = u.release_starten()
    lauf = _genau_ein_probelauf(u, erg)
    assert lauf.dateien, erg.zeige("Befund: Prüfliste sah gar keine Dateien")
    assert not lauf.sieht(rote), erg.zeige(
        "Befund: Die nicht mitgehende Datei war im Probelauf enthalten (Probelauf prüfte nicht genau die Upload-Fassung)")
    assert lauf.ende == 0, erg.zeige("Befund: Probelauf wurde rot")
    assert len(u.github_neue_commits(stand)) == 1, erg.zeige("Befund: Nach grünem Probelauf kam nichts auf GitHub an")


def test_tf04_ak4_mitgehende_rote_testdatei_macht_probelauf_rot(uebung):
    """TASK-117 · TF-04 · AK4 — *Mitgehende rote Testdatei* → *Release starten* → *Probelauf rot*,
    *nichts auf GitHub angekommen*. Quelle: Spec AK4 (Polarität zu AK3)."""
    u = uebung
    rote = "FotoAlert/backend/tests/test_ticket_rot.py"
    u.schreibe(rote, "def test_ticket_rot():\n    assert False\n")
    u.ticketliste(rote)
    u.pruefliste(modus="rot_wenn_datei", dateimuster="test_ticket_rot.py")
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    lauf = _genau_ein_probelauf(u, erg)
    assert lauf.sieht(rote), erg.zeige("Befund: Die mitgehende Testdatei fehlte im Probelauf")
    assert lauf.ende == 1, erg.zeige("Befund: Probelauf wurde nicht rot")
    assert u.github_zustand() == github_vorher, erg.zeige("Befund: Trotz rotem Probelauf kam etwas auf GitHub an")


def test_tf06_ak6_rote_pruefung_laedt_nichts_hoch(uebung):
    """TASK-117 · TF-06 · AK6 — *Prüfliste meldet rot* → *Release starten* → *nichts auf GitHub
    angekommen* (Stand des Wegwerf-GitHub vorher = nachher). Quelle: Spec AK6."""
    u = uebung
    u.standard_ticket()
    u.pruefliste(modus="rot", block="Backend", test="test_irgendwas_rot")
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    _genau_ein_probelauf(u, erg)
    assert u.github_zustand() == github_vorher, erg.zeige("Befund: Trotz rotem Probelauf kam etwas auf GitHub an")


def test_tf07_ak7_rot_meldung_nennt_block_test_und_protokollort(uebung):
    """TASK-117 · TF-07 · AK7 — *Prüfliste meldet rot im Block Oberflächen-Check, Test X* →
    *Release starten* → *Meldung nennt Block, Test X und Protokollpfad*; Protokoll existiert dort.
    Quelle: Spec AK7."""
    u = uebung
    u.standard_ticket()
    u.pruefliste(modus="rot", block="Oberflächen-Check", test="test_karte_zeigt_orte")
    erg = u.release_starten()
    _genau_ein_probelauf(u, erg)
    # Die Prüfliste liefert nur Kennungen („block=oberflaechen_check … rot=…“); der Befehl muss daraus
    # eine eigene Meldung machen, die Prüfblock (Anzeigename) und Test gemeinsam nennt.
    assert any("Oberflächen-Check" in z and "test_karte_zeigt_orte" in z for z in erg.ausgabe.splitlines()), erg.zeige(
        "Befund: Keine eigene Meldung des Befehls, die den roten Prüfblock und den Test nennt")
    pfad = u.protokollpfad(erg.ausgabe)
    assert pfad is not None, erg.zeige("Befund: Meldung nennt keinen Ort des vollständigen Protokolls")
    assert pfad.is_file(), erg.zeige(f"Befund: Genanntes Protokoll {pfad} existiert nicht")


def test_tf08_ak8_nach_rot_alles_wie_vorher_und_neustart_zaehlt_genau_einmal(uebung):
    """TASK-117 · TF-08 · AK8 — *Prüfliste rot* → *Release starten* → *Versionsnummer alt, nichts
    eingecheckt* → *Prüfliste grün* → *Release starten* → *Version genau +1*.
    Quelle: Spec AK8; Handrechnung 1.4.2 + patch = 1.4.3."""
    u = uebung
    u.standard_ticket()
    u.pruefliste(modus="rot", block="Browser-Tests", test="test_login")
    vorher = u.zustand()
    erg = u.release_starten()
    _genau_ein_probelauf(u, erg)
    _nichts_veraendert(u, vorher, erg, was="Roter Probelauf")
    u.pruefliste(modus="gruen")
    erg2 = u.release_starten()
    assert u.github_version() == NAECHSTE_PATCH_VERSION, erg2.zeige(
        f"Befund: Nach Reparatur ist die Version auf GitHub {u.github_version()}, erwartet {NAECHSTE_PATCH_VERSION}")
    assert u.lokale_version() == NAECHSTE_PATCH_VERSION, erg2.zeige("Befund: lokale Version nicht genau +1")


def test_tf09_ak9_keine_tests_gefunden_gilt_als_rot(uebung):
    """TASK-117 · TF-09 · AK9 — *Prüfliste findet keine Tests* → *Release starten* → *als rot
    gewertet*, Grund genannt. Quelle: Spec AK9 (BUG-100-Muster: Werkzeug meldet Erfolg)."""
    u = uebung
    u.standard_ticket()
    u.pruefliste(modus="null_tests")
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    _genau_ein_probelauf(u, erg)
    assert u.github_zustand() == github_vorher, erg.zeige("Befund: „0 Tests“ wurde als grün gewertet und hochgeladen")
    assert re.search(r"keine Tests|0 Tests", erg.ausgabe, re.IGNORECASE), erg.zeige(
        "Befund: Meldung nennt den Grund „keine Tests gefunden“ nicht")


def test_tf10_ak9_uebersprungene_browser_tests_gelten_als_rot(uebung):
    """TASK-117 · TF-10 · AK9 — *Prüfliste meldet Browser-Tests übersprungen* → *Release starten* →
    *als rot gewertet*, Grund genannt. Quelle: Spec AK9."""
    u = uebung
    u.standard_ticket()
    u.pruefliste(modus="uebersprungen", block="Browser-Tests")
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    _genau_ein_probelauf(u, erg)
    assert u.github_zustand() == github_vorher, erg.zeige("Befund: Übersprungene Tests wurden als grün gewertet")
    assert re.search(r"Browser-Tests[^\n]*übersprungen|übersprungen[^\n]*Browser-Tests", erg.ausgabe), erg.zeige(
        "Befund: Meldung nennt nicht, dass die Browser-Tests übersprungen wurden")


def _job_abschnitt(text, job):
    m = re.search(rf"^  {re.escape(job)}:\s*$(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)", text, re.M | re.S)
    return m.group(1) if m else None


def test_tf11_ak10_mac_und_github_rufen_dieselbe_pruefliste_auf():
    """TASK-117 · TF-11 · AK10 (Teil Dateivergleich) — *Mac-Probelauf und GitHub-Prüfung* →
    *rufen dieselbe Prüfliste auf*. Quelle: Spec AK10, Entscheidung 5."""
    beschreibung = GITHUB_PRUEFBESCHREIBUNG.read_text(encoding="utf-8")
    name = PRUEFLISTE_RELPFAD.split("/")[-1]
    for job in ("test-frontend", "test-backend"):
        abschnitt = _job_abschnitt(beschreibung, job)
        assert abschnitt is not None, f"Prüf-Job {job} fehlt in der GitHub-Prüfbeschreibung"
        assert name in abschnitt, (
            f"Befund: GitHub-Prüf-Job {job} ruft die gemeinsame Prüfliste ({PRUEFLISTE_RELPFAD}) nicht auf")
    befehl = (REPO_ROOT / BEFEHL_RELPFAD).read_text(encoding="utf-8")
    assert name in befehl, f"Befund: Der Release-Befehl ruft die gemeinsame Prüfliste ({PRUEFLISTE_RELPFAD}) nicht auf"


def test_tf11_ak10_ergaenzter_pruefschritt_laeuft_im_mac_probelauf_mit(uebung):
    """TASK-117 · TF-11 · AK10 (Teil Übungsablage) — *GitHub-Prüfliste bekommt Zusatzschritt* →
    *Mac-Probelauf führt ihn aus*. Quelle: Spec AK10."""
    u = uebung
    u.pruefliste_ergaenzen()
    u.ticketliste(PRUEFLISTE_RELPFAD)
    erg = u.release_starten()
    lauf = _genau_ein_probelauf(u, erg)
    assert lauf.zusatz, erg.zeige("Befund: Der ergänzte Prüfschritt lief im Probelauf nicht mit")


def test_tf13_ak11_browser_werkzeug_fest_und_gleich_auf_mac_und_github():
    """TASK-117 · TF-13 · AK11 (Teil Dateivergleich) — *Browser-Werkzeug-Version auf Mac und in
    GitHub-Prüfung* → *beide gleich und fest eingestellt*. Quelle: Spec AK11, Entscheidung 5."""
    beschreibung = GITHUB_PRUEFBESCHREIBUNG.read_text(encoding="utf-8")
    ungebunden = [z.strip() for z in beschreibung.splitlines()
                  if re.search(r"pip install\b.*\bplaywright\b(?!\s*==)", z)]
    assert not ungebunden, f"Befund: GitHub installiert das Browser-Werkzeug ohne feste Version: {ungebunden}"
    quellen = [GITHUB_PRUEFBESCHREIBUNG, REPO_ROOT / BEFEHL_RELPFAD, REPO_ROOT / PRUEFLISTE_RELPFAD]
    quellen += sorted((REPO_ROOT / "FotoAlert" / "backend").glob("requirements*.txt"))
    versionen = {}
    for q in quellen:
        if q.is_file():
            for v in re.findall(r"playwright==([0-9][0-9A-Za-z.]*)", q.read_text(encoding="utf-8")):
                versionen.setdefault(v, []).append(q.name)
    assert versionen, "Befund: Nirgends ist eine feste Version des Browser-Werkzeugs eingestellt"
    assert len(versionen) == 1, f"Befund: Unterschiedliche Versionen des Browser-Werkzeugs: {versionen}"
    mac_seite = {BEFEHL_RELPFAD.split("/")[-1], PRUEFLISTE_RELPFAD.split("/")[-1]} | {
        q.name for q in quellen if q.name.startswith("requirements")}
    (fundorte,) = versionen.values()
    assert mac_seite & set(fundorte), (
        f"Befund: Die Mac-Seite (Befehl, gemeinsame Prüfliste oder requirements) stellt die Version nicht fest ein; "
        f"gefunden nur in {fundorte}")


def test_tf15_ak13_fortschritt_je_pruefblock_und_gesamtdauer(uebung):
    """TASK-117 · TF-15 · AK13 — *Release starten* → *Anzeige je laufendem Prüfblock* und
    *Gesamtdauer am Ende*. Quelle: Spec AK13."""
    u = uebung
    u.standard_ticket()
    erg = u.release_starten()
    _genau_ein_probelauf(u, erg)
    fehlend = [b for b in PRUEFBLOECKE if b not in erg.ausgabe]
    assert not fehlend, erg.zeige(f"Befund: Anzeige nennt diese Prüfblöcke nicht: {fehlend}")
    assert re.search(r"Gesamtdauer[^\n]*\d", erg.ausgabe), erg.zeige("Befund: Keine Gesamtdauer am Ende")


@pytest.mark.parametrize("ausgang", ["gruen", "rot"])
def test_tf17_ak15_keine_geheimnisse_in_ausgabe_und_protokollen(uebung, ausgang):
    """TASK-117 · TF-17 · AK15 — *Passwörter und Geheimnisse mit bekannten Prüfwerten gesetzt* →
    *Release starten* (grün und rot) → *kein Prüfwert in Ausgabe, Protokoll, Server- und
    Testprotokollen*. Quelle: Spec AK15, Pre-Mortem S8."""
    u = uebung
    u.standard_ticket()
    if ausgang == "rot":
        u.pruefliste(modus="rot", block="Oberflächen-Check", test="test_login")
    erg = u.release_starten()
    lauf = _genau_ein_probelauf(u, erg)
    assert lauf.ende is not None, erg.zeige("Befund: Probelauf lief nicht zu Ende")
    fehlend = [n for n in PRUEFWERTE if lauf.geheimnisse.get(n) != "vorhanden"]
    assert not fehlend, erg.zeige(f"Befund: Die Prüfliste bekam diese Geheimnisse nicht und konnte sie nicht nutzen: {fehlend}")
    texte = {"Ausgabe": erg.ausgabe, "Aufruf der Prüfliste": lauf.args}
    pfad = u.protokollpfad(erg.ausgabe)
    assert pfad is not None and pfad.is_file(), erg.zeige("Befund: Kein Protokoll genannt/vorhanden")
    kandidaten = {pfad} | {p for p in pfad.parent.iterdir() if p.is_file() and p.name != ".env"}
    kandidaten |= {p for p in u.tmp.rglob("*") if p.is_file()}
    for p in kandidaten:
        texte[str(p)] = p.read_text(encoding="utf-8", errors="replace")
    funde = [(wo, name) for wo, t in texte.items() for name, wert in PRUEFWERTE.items() if wert in t]
    assert not funde, f"Befund: Geheimnis-Prüfwerte sichtbar: {funde}"


@pytest.mark.parametrize("ausgang", ["gruen", "rot", "abbruch"])
def test_tf18_ak16_pruefkopie_entfernt_protokoll_bleibt(uebung, ausgang):
    """TASK-117 · TF-18 · AK16 — *Release starten* (grün / rot / Abbruch) → *keine Prüfkopie mehr
    vorhanden*, *Protokoll vorhanden*. Quelle: Spec AK16 (technische Festlegung 24.10.2026)."""
    u = uebung
    u.standard_ticket()
    if ausgang == "rot":
        u.pruefliste(modus="rot")
    if ausgang == "abbruch":
        u.pruefliste(warten=True)
        lauf_bg = u.release_im_hintergrund()
        u.warte_auf_probelauf(lauf_bg)
        lauf_bg.signal(signal.SIGINT)
        erg = lauf_bg.warte_ende(60)
    else:
        erg = u.release_starten()
    lauf = _genau_ein_probelauf(u, erg)
    assert lauf.kopie, erg.zeige("Befund: Probelauf ohne erkennbare Prüfkopie")
    assert not Path(lauf.kopie).exists(), erg.zeige(f"Befund: Prüfkopie {lauf.kopie} blieb liegen")
    pfad = u.protokollpfad(erg.ausgabe)
    assert pfad is not None and pfad.is_file(), erg.zeige("Befund: Protokoll fehlt nach dem Probelauf")


# ═════════════════════════════════════════════════════════════════════════════
# B · Ein Befehl, nichts Fremdes, nichts doppelt (inkl. TASK-112)
# ═════════════════════════════════════════════════════════════════════════════

def test_tf19_ak17_liste_was_live_geht_vor_dem_probelauf_und_im_protokoll(uebung):
    """TASK-117 · TF-19 · AK17 — *Zwei Ticket-Dateien und ein unveröffentlichter Ticket-Commit* →
    *Release starten* → *Liste zeigt genau diese*, *Protokoll enthält sie*, Liste erscheint vor dem
    Probelauf. Quelle: Spec AK17 (TASK-112 Punkt 2)."""
    u = uebung
    u.aendere("FotoAlert/backend/helfer.py")
    u.committe("TASK-117 Zwischenstand Helfer", "FotoAlert/backend/helfer.py")
    u.aendere("FotoAlert/backend/main.py")
    u.schreibe("FotoAlert/backend/tests/test_neu.py", "def test_neu():\n    assert True\n")
    erwartet = ["FotoAlert/backend/main.py", "FotoAlert/backend/tests/test_neu.py", "TASK-117 Zwischenstand Helfer"]
    u.ticketliste("FotoAlert/backend/main.py", "FotoAlert/backend/tests/test_neu.py", "FotoAlert/backend/helfer.py")
    u.pruefliste(warten=True)
    lauf_bg = u.release_im_hintergrund()
    u.warte_auf_probelauf(lauf_bg)
    bis_probelauf = lauf_bg.ausgabe
    u.weiter()
    erg = lauf_bg.warte_ende()
    fehlend = [e for e in erwartet if e not in bis_probelauf]
    assert not fehlend, erg.zeige(f"Befund: Vor dem Probelauf fehlte in der Liste: {fehlend}")
    assert "FotoAlert/README.md" not in bis_probelauf, erg.zeige("Befund: Liste nennt eine nicht mitgehende Datei")
    pfad = u.protokollpfad(erg.ausgabe)
    assert pfad is not None and pfad.is_file(), erg.zeige("Befund: Kein Protokoll")
    protokoll = pfad.read_text(encoding="utf-8", errors="replace")
    fehlend = [e for e in erwartet if e not in protokoll]
    assert not fehlend, erg.zeige(f"Befund: Im Protokoll fehlt: {fehlend}")


def test_tf20_ak18_nichts_neues_bricht_ab_ohne_version_und_upload(uebung):
    """TASK-117 · TF-20 · AK18 — *Erfolgreiches Release* → *Release erneut starten* →
    *„Nichts Neues zu veröffentlichen“*, *keine neue Version*, *nichts auf GitHub angekommen*.
    Quelle: Spec AK18 (TASK-112 Punkt 1)."""
    u = uebung
    u.standard_ticket()
    erg1 = u.release_starten()
    assert u.github_version() == NAECHSTE_PATCH_VERSION, erg1.zeige("Vorbedingung: erstes Release nicht erfolgreich")
    github_vorher = u.github_zustand()
    version_vorher = u.lokale_version()
    erg2 = u.release_starten()
    assert MELDUNG_NICHTS_NEUES in erg2.ausgabe, erg2.zeige(f"Befund: Meldung „{MELDUNG_NICHTS_NEUES}“ fehlt")
    assert u.lokale_version() == version_vorher, erg2.zeige("Befund: Zweiter Start zählte die Version hoch")
    assert u.github_zustand() == github_vorher, erg2.zeige("Befund: Zweiter Start lud etwas hoch")


def test_tf21_ak19_doppelstart_bricht_sofort_ab_erster_laeuft_weiter(uebung):
    """TASK-117 · TF-21 · AK19 — *Release läuft* (Platzhalter-Prüfliste wartet) → *Release ein zweites
    Mal starten* → *zweiter Aufruf bricht sofort ab*, *erster endet normal*. Quelle: Spec AK19."""
    u = uebung
    u.standard_ticket()
    stand = u.github_stand()
    u.pruefliste(warten=True)
    erster = u.release_im_hintergrund()
    u.warte_auf_probelauf(erster)
    vorher = u.zustand()
    t0 = time.time()
    zweiter = u.release_starten(zeitlimit=60)
    dauer = time.time() - t0
    assert dauer < 20, zweiter.zeige(f"Befund: Zweiter Aufruf brach nicht sofort ab ({dauer:.0f} s)")
    assert zweiter.code != 0, zweiter.zeige("Befund: Zweiter Aufruf meldete Erfolg statt Abbruch")
    _nichts_veraendert(u, vorher, zweiter, was="Zweiter Aufruf")
    assert len(u.probelaeufe()) == 1, zweiter.zeige("Befund: Zweiter Aufruf startete einen eigenen Probelauf")
    u.weiter()
    erg1 = erster.warte_ende()
    assert erg1.code == 0, erg1.zeige("Befund: Erster Aufruf endete nicht normal")
    assert len(u.github_neue_commits(stand)) == 1, erg1.zeige("Befund: Erster Aufruf lud nicht genau einen Stand hoch")


def test_tf22_ak20_github_hat_neueren_stand_abbruch_erst_holen(uebung):
    """TASK-117 · TF-22 · AK20 — *GitHub hat einen neueren Stand* → *Release starten* →
    *Abbruch „erst holen“*, *nichts verändert*. Quelle: Spec AK20 (Gebäudedaten-Update)."""
    u = uebung
    bot = u.root / "bot"
    u._git(["clone", "-q", str(u.github), str(bot)], cwd=u.root, pruefe_ziel=False)
    (bot / "FotoAlert/backend/data/cache/building_footprints.json").write_text('{"neu": 1}\n', encoding="utf-8")
    u._git(["commit", "-q", "-am", "Gebäudedaten-Update (Bot)"], cwd=bot)
    u._git(["push", "-q", "origin", "main"], cwd=bot)
    u.standard_ticket()
    vorher = u.zustand()
    erg = u.release_starten()
    assert re.search(r"\b(holen|geholt|abholen)\b", erg.ausgabe, re.IGNORECASE), erg.zeige(
        "Befund: Meldung sagt nicht, dass zuerst geholt werden muss")
    _nichts_veraendert(u, vorher, erg)
    _kein_probelauf(u, erg)


def test_tf23_ak21_git_sperrdatei_bricht_vor_jeder_aenderung_ab(uebung):
    """TASK-117 · TF-23 · AK21 — *Git-Sperrdatei liegt vor* → *Release starten* → *Abbruch mit
    Hinweis*, *nichts verändert*. Quelle: Spec AK21."""
    u = uebung
    u.standard_ticket()
    (u.repo / ".git" / "index.lock").write_text("", encoding="utf-8")
    vorher = u.zustand()
    erg = u.release_starten()
    assert re.search(r"Sperrdatei|gesperrt|blockiert", erg.ausgabe), erg.zeige(
        "Befund: Kein verständlicher Hinweis auf die Git-Sperre")
    _nichts_veraendert(u, vorher, erg)
    _kein_probelauf(u, erg)


def test_tf24_ak22_ticket_und_version_in_genau_einem_upload(uebung):
    """TASK-117 · TF-24 · AK22 — *Ticket mit Code-, Test- und Doku-Datei gelistet* → *Release starten*
    → *auf GitHub genau ein neuer Stand* mit genau diesen Dateien und der neuen Versionsnummer.
    Quelle: Spec AK22, Entscheidung 1."""
    u = uebung
    ticket = ["FotoAlert/BACKLOG.md", "FotoAlert/backend/main.py", "FotoAlert/backend/tests/test_neu.py"]
    u.aendere("FotoAlert/backend/main.py")
    u.schreibe("FotoAlert/backend/tests/test_neu.py", "def test_neu():\n    assert True\n")
    u.aendere("FotoAlert/BACKLOG.md", "- TASK-117 erledigt\n")
    u.ticketliste(*ticket)
    stand = u.github_stand()
    erg = u.release_starten()
    neu = u.github_neue_commits(stand)
    assert len(neu) == 1, erg.zeige(f"Befund: Auf GitHub kamen {len(neu)} neue Stände an, erwartet genau 1")
    dateien = u.github_dateien_zwischen(stand, neu[0])
    assert dateien == sorted(ticket + list(VERSIONSDATEIEN)), erg.zeige(
        f"Befund: Der Upload enthielt {dateien}, erwartet genau Ticket-Dateien + Versionsdateien")
    assert u.github_version() == NAECHSTE_PATCH_VERSION, erg.zeige("Befund: Neue Versionsnummer fehlt im Upload")


def test_tf25_ak23_fremde_aenderung_in_ticket_datei_wuerde_mitgehen_abbruch(uebung):
    """TASK-117 · TF-25 · AK23 (präzisiert 24.10.2026) — *Eine Datei der Ticket-Liste enthält zusätzlich
    Änderungen eines anderen Tickets, schon als Commit vorgemerkt* → *Release starten* → *Abbruch,
    Grund genannt* (die fremde Änderung würde tatsächlich mit hochgehen), *nichts verändert*.
    Quelle: Spec AK23 („fremde, schon vorgemerkte Commits“). Annahme dieses Tests: „fremd“ = Commit
    trägt die ID eines anderen Tickets."""
    u = uebung
    u.aendere("FotoAlert/backend/main.py", "ANDERES_TICKET = 1\n")
    u.committe("BUG-998 andere Arbeit in main.py", "FotoAlert/backend/main.py")
    u.standard_ticket()
    vorher = u.zustand()
    erg = u.release_starten()
    assert "BUG-998" in erg.ausgabe, erg.zeige("Befund: Fremde Änderung, die mit hochginge, wird nicht genannt")
    _nichts_veraendert(u, vorher, erg)
    _kein_probelauf(u, erg)


def test_tf26_ak23a_fremde_vorgemerkte_datei_bleibt_hier(uebung):
    """TASK-117 · TF-26 · AK23a (Klarstellung 24.10.2026 nach Modus T) — *Fremde, schon vorgemerkte Datei,
    nicht auf der Ticket-Liste* → *Release starten* → *kein Abbruch*, *Release mit Probelauf*, *die Datei
    kommt nicht bei GitHub an, bleibt im Arbeitsordner unverändert* (auch weiterhin vorgemerkt) *und
    erscheint in der Vorschau unter „bleibt hier“*. Quelle: Spec AK23a, Entscheidung „liegen lassen“."""
    u = uebung
    u.standard_ticket()
    fremd = "FotoAlert/backend/fremd.py"
    u.vormerken(fremd, "# fremde Arbeit, vorgemerkt\n")
    status_vorher = u.status_von(fremd)
    stand = u.github_stand()
    u.pruefliste(warten=True)
    lauf_bg = u.release_im_hintergrund()
    u.warte_auf_probelauf(lauf_bg)
    vorschau = lauf_bg.ausgabe
    u.weiter()
    erg = lauf_bg.warte_ende()
    _genau_ein_probelauf(u, erg)
    neu = u.github_neue_commits(stand)
    assert len(neu) == 1, erg.zeige("Befund: Ticket kam nicht (genau einmal) auf GitHub an")
    assert fremd not in u.github_dateien_zwischen(stand, neu[0]), erg.zeige("Befund: Fremde vorgemerkte Datei ging mit hoch")
    assert u.lies(fremd) == "# fremde Arbeit, vorgemerkt\n", erg.zeige("Befund: Fremde Datei im Arbeitsordner verändert")
    assert u.status_von(fremd) == status_vorher, erg.zeige(
        f"Befund: Vormerkung der fremden Datei verändert ({status_vorher!r} → {u.status_von(fremd)!r})")
    teil = vorschau.split("bleibt hier, wird nicht veröffentlicht", 1)
    assert len(teil) == 2 and "fremd.py" in teil[1], erg.zeige(
        "Befund: Vorschau führt die fremde Datei nicht unter „bleibt hier, wird nicht veröffentlicht“")


def test_tf37_ak23a_fremde_neue_und_geaenderte_dateien_bleiben_hier(uebung):
    """TASK-117 · TF-37 (neu) · AK23a — *Neue und geänderte Dateien anderer, unveröffentlichter Arbeit,
    nicht gelistet, nicht ausgeschlossen* → *Release starten* → *kein Abbruch*, *Ticket kommt auf GitHub
    an ohne diese Dateien*, Dateien liegen unverändert im Arbeitsordner, *Vorschau führt sie unter
    „bleibt hier, wird nicht veröffentlicht“ auf* (vor dem Probelauf). Quelle: Spec AK23a
    (Entscheidung Stephan 24.10.2026)."""
    u = uebung
    u.standard_ticket()
    neu_datei, geaendert = "FotoAlert/backend/andere_arbeit.py", "FotoAlert/README.md"
    u.schreibe(neu_datei, "# andere Arbeit, neu\n")
    u.aendere(geaendert, "andere Arbeit, geändert\n")
    inhalte = {neu_datei: u.lies(neu_datei), geaendert: u.lies(geaendert)}
    stand = u.github_stand()
    u.pruefliste(warten=True)
    lauf_bg = u.release_im_hintergrund()
    u.warte_auf_probelauf(lauf_bg)
    vorschau = lauf_bg.ausgabe
    u.weiter()
    erg = lauf_bg.warte_ende()
    lauf = _genau_ein_probelauf(u, erg)
    assert not lauf.sieht(neu_datei), erg.zeige("Befund: Fremde neue Datei war im Probelauf enthalten")
    neu = u.github_neue_commits(stand)
    assert len(neu) == 1, erg.zeige("Befund: Ticket kam nicht (genau einmal) auf GitHub an")
    hoch = u.github_dateien_zwischen(stand, neu[0])
    assert neu_datei not in hoch and geaendert not in hoch, erg.zeige(f"Befund: Fremdes ging mit hoch: {hoch}")
    assert {d: u.lies(d) for d in inhalte} == inhalte, erg.zeige("Befund: Fremde Dateien im Arbeitsordner verändert")
    teil = vorschau.split("bleibt hier, wird nicht veröffentlicht", 1)
    assert len(teil) == 2, erg.zeige("Befund: Vorschau ohne Abschnitt „bleibt hier, wird nicht veröffentlicht“")
    fehlend = [d for d in (neu_datei, geaendert) if d.split("/")[-1] not in teil[1]]
    assert not fehlend, erg.zeige(f"Befund: Unter „bleibt hier“ fehlt: {fehlend}")


def test_tf38_ak23b_backlog_geht_immer_vollstaendig_mit(uebung):
    """TASK-117 · TF-38 (neu) · AK23b — *Backlog enthält neben dem Ticket auch Einträge anderer Tickets
    und steht nicht auf der Ticket-Liste* → *Release starten* → *kein Abbruch als „fremd“*, *Backlog
    kommt vollständig (mit allen Einträgen) zusammen mit dem Ticket auf GitHub an*.
    *Vor dem Hochladen legt der Befehl selbst eine Sicherungskopie des Backlogs an* (Ort
    _to_delete/BACKLOG.vor_<anlass>_<Zeit>.md, Inhalt = Backlog vor dem Hochladen).
    Quelle: Spec AK23b (Entscheidung Stephan 24.10.2026, Urheber der Kopie: technische Festlegung)."""
    u = uebung
    u.standard_ticket()
    u.aendere("FotoAlert/BACKLOG.md", "- TASK-117 in Arbeit\n- BUG-997 andere Arbeit (Intake)\n")
    backlog = u.lies("FotoAlert/BACKLOG.md")
    stand = u.github_stand()
    erg = u.release_starten()
    neu = u.github_neue_commits(stand)
    assert len(neu) == 1, erg.zeige("Befund: Release brach wegen des Backlogs ab oder lud nicht genau einmal hoch")
    hoch = u.github_dateien_zwischen(stand, neu[0])
    assert "FotoAlert/BACKLOG.md" in hoch and "FotoAlert/backend/main.py" in hoch, erg.zeige(
        f"Befund: Backlog bzw. Ticket fehlt im Upload: {hoch}")
    assert u.github_datei(BACKLOG_RELPFAD) + "\n" == backlog or u.github_datei(BACKLOG_RELPFAD) == backlog, \
        erg.zeige("Befund: Backlog kam nicht vollständig an")
    kopien = u.sicherungskopien()
    assert kopien, erg.zeige("Befund: Der Befehl legte vor dem Hochladen keine Sicherungskopie des Backlogs an "
                             "(_to_delete/BACKLOG.vor_<anlass>_<Zeit>.md)")
    assert any(k.read_text(encoding="utf-8") == backlog for k in kopien), erg.zeige(
        "Befund: Sicherungskopie entspricht nicht dem Backlog vor dem Hochladen")


def test_tf27_ak24_fremder_unveroeffentlichter_commit_bricht_ab_und_wird_genannt(uebung):
    """TASK-117 · TF-27 · AK24 — *Fremder unveröffentlichter Commit* → *Release starten* → *Abbruch,
    Commit genannt*. Quelle: Spec AK24 (BUG-113: fremder Zwischen-Commit bei v1.23.1)."""
    u = uebung
    u.aendere("FotoAlert/README.md")
    u.committe("BUG-999 fremder Zwischenstand", "FotoAlert/README.md")
    u.standard_ticket()
    vorher = u.zustand()
    erg = u.release_starten()
    assert "BUG-999" in erg.ausgabe, erg.zeige("Befund: Fremder Commit wird nicht genannt")
    _nichts_veraendert(u, vorher, erg)
    _kein_probelauf(u, erg)


@pytest.mark.parametrize("fall", ["fehlt", "leer", "nennt_nicht_vorhandene_datei"])
def test_tf28_ak25_ticket_dateiliste_fehlt_leer_oder_falsch_bricht_ab(uebung, fall):
    """TASK-117 · TF-28 · AK25 — *Ticket-Dateiliste fehlt* / *ist leer* / *nennt nicht vorhandene
    Datei* → *Release starten* → jeweils *Abbruch mit Hinweis*, *nichts verändert*. Quelle: Spec AK25."""
    u = uebung
    u.aendere("FotoAlert/backend/main.py")
    liste = r"(Ticket-?)?Datei-?[Ll]iste|Ticket-?[Ll]iste|Liste der (Ticket-)?Dateien"
    if fall == "fehlt":
        u.ticketliste_entfernen()
        grund = r"fehlt|nicht gefunden|nicht vorhanden|existiert nicht"
    elif fall == "leer":
        u.ticketliste(roh="# nur ein Kommentar\n\n")
        grund = r"\bleer\b|keine Dateien|enthält keine"
    else:
        u.ticketliste("FotoAlert/backend/main.py", "FotoAlert/backend/gibt_es_nicht.py")
        liste = r"gibt_es_nicht\.py"
        grund = r"gibt es nicht|nicht vorhanden|fehlt|nicht gefunden|existiert nicht"
    vorher = u.zustand()
    erg = u.release_starten()
    # Hinweis = EINE Zeile, die die Liste (bzw. die fehlende Datei) und den Grund zusammen nennt.
    assert any(re.search(liste, z, re.IGNORECASE) and re.search(grund, z, re.IGNORECASE)
               for z in erg.ausgabe.splitlines()), erg.zeige(f"Befund: Kein Hinweis zur Ticket-Dateiliste (Fall {fall})")
    _nichts_veraendert(u, vorher, erg)
    _kein_probelauf(u, erg)


def test_tf29_ak26_nur_doku_vollstaendiger_probelauf_ohne_neue_version(uebung):
    """TASK-117 · TF-29 · AK26 — *Nur Doku geändert* → *Release starten* → *Probelauf läuft
    vollständig*, *auf GitHub angekommen*, *Versionsnummer unverändert*, Meldung „keine neue Version“.
    Quelle: Spec AK26, Entscheidung 2, Annahme „Doku = nur .md“ (bestätigt 24.10.2026)."""
    u = uebung
    u.aendere("FotoAlert/BACKLOG.md", "- TASK-117 Done\n")
    u.ticketliste("FotoAlert/BACKLOG.md")
    stand = u.github_stand()
    erg = u.release_starten()
    lauf = _genau_ein_probelauf(u, erg)
    assert lauf.ende == 0 and len(lauf.bloecke) == len(PRUEFBLOECKE), erg.zeige("Befund: Probelauf nicht vollständig")
    neu = u.github_neue_commits(stand)
    assert neu and "FotoAlert/BACKLOG.md" in u.github_dateien_zwischen(stand, neu[-1]), erg.zeige(
        "Befund: Doku-Änderung kam nicht auf GitHub an")
    assert u.github_version() == AUSGANGSVERSION, erg.zeige("Befund: Reine Doku-Änderung bekam eine neue Versionsnummer")
    assert MELDUNG_KEINE_NEUE_VERSION.lower() in erg.ausgabe.lower(), erg.zeige(f"Befund: Meldung „{MELDUNG_KEINE_NEUE_VERSION}“ fehlt")


def test_tf30_ak27_nur_backend_bekommt_neue_version(uebung):
    """TASK-117 · TF-30 · AK27 — *Nur Backend geändert* → *Release starten* → *Versionsnummer +1*.
    Quelle: Spec AK27 (Polarität zu AK26); Handrechnung 1.4.2 + patch = 1.4.3."""
    u = uebung
    u.standard_ticket()
    erg = u.release_starten()
    _genau_ein_probelauf(u, erg)
    assert u.github_version() == NAECHSTE_PATCH_VERSION, erg.zeige(
        f"Befund: Version auf GitHub {u.github_version()}, erwartet {NAECHSTE_PATCH_VERSION}")


def test_tf31_ak28_ohne_rueckfrage_hochladen_und_abschlussmeldung(uebung):
    """TASK-117 · TF-31 · AK28 — *Prüfliste grün* → *Release starten* ohne Eingabe → *auf GitHub
    angekommen ohne Rückfrage*; Abschlussmeldung mit Version, Commits, Link. Quelle: Spec AK28,
    Entscheidung 3."""
    u = uebung
    u.aendere("FotoAlert/backend/helfer.py")
    u.committe("TASK-117 Zwischenstand Helfer", "FotoAlert/backend/helfer.py")
    u.standard_ticket()
    u.ticketliste("FotoAlert/backend/main.py", "FotoAlert/backend/helfer.py")
    u.pruefliste(warten=True)
    lauf_bg = u.release_im_hintergrund(eingabe=None)
    u.warte_auf_probelauf(lauf_bg)
    bis_probelauf = len(lauf_bg.ausgabe)
    u.weiter()
    erg = lauf_bg.warte_ende()
    abschluss = erg.ausgabe[bis_probelauf:]          # nur, was nach dem Probelauf kam
    assert u.github_version() == NAECHSTE_PATCH_VERSION, erg.zeige("Befund: Ohne Eingabe kam nichts auf GitHub an")
    assert "[j/N]" not in erg.ausgabe, erg.zeige("Befund: Befehl stellt noch eine Ja/Nein-Rückfrage")
    assert NAECHSTE_PATCH_VERSION in abschluss, erg.zeige("Befund: Abschlussmeldung nennt die Version nicht")
    assert "TASK-117 Zwischenstand Helfer" in abschluss, erg.zeige("Befund: Abschlussmeldung nennt die Commits nicht")
    assert GITHUB_PRUEFUNG_LINK_MUSTER.search(abschluss), erg.zeige("Befund: Abschlussmeldung ohne Link zur GitHub-Prüfung")


@pytest.mark.parametrize("sig", [pytest.param("SIGINT", id="tastenkombination_abbruch"),
                                 pytest.param("SIGHUP", id="fenster_schliessen")])
def test_tf32_ak29_abbruch_mittendrin_hinterlaesst_nichts_halbes(uebung, sig):
    """TASK-117 · TF-32 · AK29 — *Probelauf läuft* → *Stephan bricht ab* (Abbruch-Tastenkombination =
    SIGINT, Fenster schließen = SIGHUP) → *Versionsnummer alt, nichts eingecheckt, keine Sperre übrig*
    → *Release starten* → *läuft normal*. Quelle: Spec AK29, Pre-Mortem S2."""
    u = uebung
    u.standard_ticket()
    vorher = u.zustand()
    u.pruefliste(warten=True)
    lauf_bg = u.release_im_hintergrund()
    u.warte_auf_probelauf(lauf_bg)
    lauf_bg.signal(getattr(signal, sig))
    erg = lauf_bg.warte_ende(60)
    _nichts_veraendert(u, vorher, erg, was=f"Abbruch ({sig})")
    u.pruefliste(modus="gruen")
    erg2 = u.release_starten()
    assert u.github_version() == NAECHSTE_PATCH_VERSION, erg2.zeige("Befund: Nächster Start nach Abbruch lief nicht normal")


def test_tf33_ak30_github_nicht_erreichbar_bricht_vor_jeder_aenderung_ab(uebung):
    """TASK-117 · TF-33 · AK30 — *GitHub nicht erreichbar* → *Release starten* → *Abbruch mit
    Meldung*, *nichts verändert*. Quelle: Spec AK30."""
    u = uebung
    u.standard_ticket()
    u.git("remote", "set-url", "origin", str(u.root / "nicht-erreichbar.git"))
    vorher = u.zustand()
    erg = u.release_starten()
    assert any("GitHub" in z and "erreichbar" in z for z in erg.ausgabe.splitlines()), erg.zeige(
        "Befund: Keine verständliche Meldung „GitHub nicht erreichbar“")
    _nichts_veraendert(u, vorher, erg)
    _kein_probelauf(u, erg)


def _hook(u, ref_muster):
    hook = u.github / "hooks" / "update"
    hook.write_text(f'#!/bin/sh\ncase "$1" in {ref_muster}) echo "abgelehnt (Übung)"; exit 1;; esac\nexit 0\n',
                    encoding="utf-8")
    hook.chmod(0o755)
    return hook


@pytest.mark.parametrize("fall", ["merge_konflikt", "version_vergeben", "hochladen_scheitert",
                                  "kennzeichen_scheitert"])
def test_tf34_ak31_bisherige_absicherungen_bleiben(uebung, fall):
    """TASK-117 · TF-34 · AK31 — *Merge-Konflikt* / *Version schon vergeben* / *Hochladen scheitert* /
    *Versionskennzeichen scheitert* → jeweils bisheriges Verhalten (Abbruch bzw. Zurücksetzen bzw.
    Anleitung). Quelle: Spec AK31 (TASK-88/TASK-98, heutiger Befehl)."""
    u = uebung
    if fall == "merge_konflikt":
        u.git("checkout", "-q", "-b", "nebenzweig")
        u.aendere("FotoAlert/backend/main.py", "NEBEN = 1\n")
        u.committe("Nebenzweig", "FotoAlert/backend/main.py")
        u.git("checkout", "-q", "main")
        u.aendere("FotoAlert/backend/main.py", "HAUPT = 1\n")
        u.committe("TASK-117 Hauptzweig", "FotoAlert/backend/main.py")
        u.git("merge", "-q", "nebenzweig", check=False)
        u.ticketliste("FotoAlert/backend/main.py")
        vorher = u.zustand()
        erg = u.release_starten()
        assert "Merge-Konflikt" in erg.ausgabe, erg.zeige("Befund: Kein Abbruch wegen Merge-Konflikt")
        _nichts_veraendert(u, vorher, erg)
        return
    u.standard_ticket()
    if fall == "version_vergeben":
        u.git("tag", f"v{NAECHSTE_PATCH_VERSION}", "HEAD")
        u.git("push", "-q", "origin", f"v{NAECHSTE_PATCH_VERSION}")
        u.git("tag", "-d", f"v{NAECHSTE_PATCH_VERSION}")
        vorher = u.zustand()
        erg = u.release_starten()
        assert "existiert bereits" in erg.ausgabe, erg.zeige("Befund: Kein Abbruch bei schon vergebener Version")
        _nichts_veraendert(u, vorher, erg)
        return
    if fall == "hochladen_scheitert":
        hook = _hook(u, "refs/heads/main")
        vorher = u.zustand()
        erg = u.release_starten()
        assert "fehlgeschlagen" in erg.ausgabe, erg.zeige("Befund: Gescheitertes Hochladen nicht gemeldet")
        _nichts_veraendert(u, vorher, erg, was="Gescheitertes Hochladen")
        hook.unlink()
        erg2 = u.release_starten()
        assert u.github_version() == NAECHSTE_PATCH_VERSION, erg2.zeige(
            "Befund: Nach Zurücksetzen zählte der Neustart nicht genau einmal hoch")
        return
    _hook(u, "refs/tags/*")
    erg = u.release_starten()
    assert u.github_version() == NAECHSTE_PATCH_VERSION, erg.zeige("Vorbedingung: Hochladen des Stands klappte nicht")
    # Die Anleitung selbst (heutiger Wortlaut „Bitte manuell nachholen:“ + Befehl auf eigener Zeile) —
    # nicht die Fehlerzeile, die den gescheiterten Befehl in Anführungszeichen zitiert.
    anleitung = re.compile(rf'nachholen[^\n]*\n(?:[^\n]*\n){{0,2}}\s*git push origin "?v{re.escape(NAECHSTE_PATCH_VERSION)}"?\s*$',
                           re.IGNORECASE | re.MULTILINE)
    assert anleitung.search(erg.ausgabe), erg.zeige("Befund: Keine Anleitung zum Nachholen des Versionskennzeichens")


# ═════════════════════════════════════════════════════════════════════════════
# C · Tests dieses Befehls
# ═════════════════════════════════════════════════════════════════════════════

_INNERER_TEST = '''
import time
from pathlib import Path
MARKE = Path(r"{marke}")

def test_innen(uebung):
    MARKE.write_text(str(uebung.root), encoding="utf-8")
    {koerper}
'''


@pytest.mark.parametrize("variante", ["gruen", "rot", "abbruch"])
def test_tf35_ak32_uebungsablagen_nach_jedem_testlauf_geloescht(uebung, variante):
    """TASK-117 · TF-35 · AK32 — *Testlauf grün* / *Testlauf mit absichtlich rotem Test* /
    *Testlauf abgebrochen* → jeweils *keine Übungsablage mehr im Temp-Ordner*. Quelle: Spec AK32,
    Entscheidung 6. (Prüft den Unterbau dieser Tests; darf heute schon grün sein.)"""
    u = uebung
    innen = u.root / "innen"
    basetemp = u.root / "innen-temp"
    marke = u.root / "innen-marke.txt"
    innen.mkdir()
    (innen / "pytest.ini").write_text("[pytest]\naddopts = -q\n", encoding="utf-8")
    (innen / "conftest.py").write_text(
        f"import sys\nsys.path.insert(0, r\"{TESTS_DIR}\")\nfrom task117_adapter import uebung  # noqa: F401\n",
        encoding="utf-8")
    koerper = {"gruen": "assert uebung.lokale_version()",
               "rot": "assert False, 'absichtlich rot'",
               "abbruch": "time.sleep(120)"}[variante]
    (innen / "test_innen.py").write_text(_INNERER_TEST.format(marke=marke, koerper=koerper), encoding="utf-8")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.Popen(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-c", str(innen / "pytest.ini"),
         "--rootdir", str(innen), "--basetemp", str(basetemp), str(innen / "test_innen.py")],
        cwd=str(innen), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        if variante == "abbruch":
            frist = time.time() + 60
            while not marke.exists() and time.time() < frist and proc.poll() is None:
                time.sleep(0.1)
            assert marke.exists(), "Innerer Testlauf erreichte den Test nicht"
            time.sleep(0.3)
            os.kill(proc.pid, signal.SIGINT)
        out, _ = proc.communicate(timeout=90)
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
    ausgabe = out.decode("utf-8", errors="replace")
    erwartet = {"gruen": 0, "rot": 1, "abbruch": 2}[variante]
    assert proc.returncode == erwartet, f"Innerer Lauf endete mit {proc.returncode}, erwartet {erwartet}\n{ausgabe}"
    ablage = Path(marke.read_text(encoding="utf-8"))
    assert not ablage.exists(), f"Befund: Übungsablage {ablage} blieb nach Lauf „{variante}“ liegen\n{ausgabe}"
    reste = [str(p) for p in basetemp.rglob("*") if p.is_file()] if basetemp.exists() else []
    assert not reste, f"Befund: Im Temp-Ordner blieben Dateien liegen: {reste[:10]}"


def test_tf36_ak33_echtes_projekt_und_echtes_github_bleiben_unberuehrt(uebung):
    """TASK-117 · TF-36 · AK33 — *Testsuite des Befehls läuft* → *Projektordner unverändert*
    (Prüfsummen des ganzen Repo-Ordners vorher = nachher), *echtes GitHub ohne neuen Stand*
    (jede github.com-Adresse ist in der Übungsablage technisch umgeleitet), *Hochladeziel jedes
    Testfalls ist die Übungsablage*. Quelle: Spec AK33, Pre-Mortem S6. (Die Hochladeziel-Prüfung steckt
    zusätzlich vor jedem Git-Aufruf im Unterbau.)"""
    u = uebung
    p = subprocess.run(["git", "ls-remote", "https://github.com/stephanschumann/fotoalert"], cwd=str(u.repo),
                       env=u.env, capture_output=True, text=True, timeout=30)
    assert p.returncode != 0 and "kein-echtes-github" in (p.stderr + p.stdout), (
        f"Echtes GitHub ist in der Übungsablage nicht umgeleitet: {p.stderr!r}")
    u.standard_ticket()
    stand = u.github_stand()
    ziel = u.git("remote", "get-url", "origin")
    assert Path(ziel).resolve() == u.github.resolve(), f"Hochladeziel {ziel} ist nicht das Wegwerf-GitHub"
    echt_vorher = projektordner_pruefsummen()
    erg = u.release_starten()
    echt_nachher = projektordner_pruefsummen()
    assert len(u.github_neue_commits(stand)) == 1, erg.zeige(
        "Befund: Das Release kam nicht im Wegwerf-GitHub an (Hochladeziel des Testfalls)")
    geaendert = sorted(k for k in set(echt_vorher) | set(echt_nachher) if echt_vorher.get(k) != echt_nachher.get(k))
    assert not geaendert, f"Befund: Im echten Projektordner verändert/neu/weg: {geaendert[:20]}"
