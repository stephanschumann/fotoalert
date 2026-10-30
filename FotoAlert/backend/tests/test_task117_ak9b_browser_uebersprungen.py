"""TASK-117 · AK9b — Bekannte, fest aufgelistete Überspring-Gründe gelten auch im Block Browser-Tests
(Entscheidung Stephan 30.10.2026, Befund aus dem zweiten echten Probelauf).

AK9b (Spec docs/analyse-entwurf/TASK-117_SPEC.md): Ein Browser-Test, der aus einem als Paar aus Test und
Grund aufgelisteten Grund übersprungen wird (z. B. Feed ohne bewertete Einträge bei leeren Daten), macht den
Probelauf nicht rot. Jeder nicht aufgelistete Grund, ein fehlendes Browser-Werkzeug und ein Block mit 0 Tests
bleiben nach AK9 immer rot und werden genannt.

Geschrieben VOR der Umsetzung dieses Kriteriums (fotoalert-test Teil A). Nutzt die Übungsablage aus
task117_adapter.py unverändert (eingefroren) und baut — wie test_task117_ak9a_uebersprungen.py (eingefroren) —
einen eigenen Platzhalter der gemeinsamen Prüfliste; alle neuen Hilfen stehen nur in dieser Datei.

SCHNITTSTELLE (übernommen aus AK9a, nichts Neues erfunden): Liste FotoAlert/tools/bekannte_uebersprungene_tests.txt
(„<Test-ID> | <Grund>“, Test-ID relativ zu backend/; der aufgelistete Grund muss im gemeldeten Grund enthalten
sein) und Meldezeile „PRUEFLISTE block=browser_tests uebersprungen_test=<Test-ID> grund=<Grund>“ zusätzlich zur
Ergebniszeile „PRUEFLISTE block=browser_tests bestanden=… fehlgeschlagen=… uebersprungen=<n> [rot=<Grund>]“.
Fehlendes Browser-Werkzeug wird wie im echten Befehl gemeldet: bestanden=0, uebersprungen=1, rot=<Grund>
(„Browser-Werkzeug (playwright) nicht installiert“). Bei anderer Umsetzung ändern sich nur die Konstanten und
Hilfen im Block „Unterbau“, nicht die Testfälle.

Testfall-IDs TF-10a–TF-10d sind Vorschläge dieses Test-Agenten (die Spec-Tabelle führt AK9b noch ohne TF).

HINWEIS: test_task117_ak9a_uebersprungen.py::test_tf09d (eingefroren) erwartet „aufgelisteter Browser-Test →
rot“ und widerspricht AK9b; nach der Umsetzung von AK9b wird dieser Test rot. Das entscheidet Stephan.
"""
from __future__ import annotations

import re

import pytest

from task117_adapter import (  # noqa: F401  (uebung ist eine Fixture)
    NAECHSTE_PATCH_VERSION,
    PRUEFLISTE_RELPFAD,
    uebung,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

# ════════════════════════════════════════════════════════════════════════════
# Unterbau (Schnittstelle laut Modul-Docstring)
# ════════════════════════════════════════════════════════════════════════════
LISTE_RELPFAD = "FotoAlert/tools/bekannte_uebersprungene_tests.txt"

# Beispiel aus der Entscheidung: Feed ohne bewertete Einträge (leere Daten, wie bei GitHub).
BEKANNT_TEST = "tests/test_bug-80.py::test_feed_zeigt_bewertete_eintraege"
BEKANNT_GRUND = "Feed enthält bei leeren Daten keine bewerteten Einträge"
ANDERER_TEST = "tests/test_task-66.py::test_kopfzeile_bleibt_sichtbar"
ANDERER_GRUND = "Seite lädt nicht: Zeitüberschreitung beim Warten auf die Karte"
WERKZEUG_GRUND = "Browser-Werkzeug (playwright) nicht installiert"

_PLATZHALTER = r"""#!/usr/bin/env bash
# PLATZHALTER der gemeinsamen Prüfliste — TASK-117 AK9b, nur Übungsablage.
STEUERUNG='__STEUERUNG__'
BERICHT='__BERICHT__'
UEBERSPRUNGEN_BACKEND=""; UEBERSPRUNGEN_BROWSER=""
BROWSER_BESTANDEN=5; BROWSER_UEBERSPRUNGEN_ZAHL=""; BROWSER_ROT=""
[ -f "$STEUERUNG" ] && . "$STEUERUNG"
SELBST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOPIE="$(cd "$SELBST_DIR/../.." && pwd)"
{ echo "LAUF $$"; echo "CWD $PWD"; echo "KOPIE $KOPIE"; echo "ARGS $*"; } >> "$BERICHT"
GESAMT=0
melde() {   # melde <block> <liste "id|grund;id|grund"> <bestanden> <zahl-override> <rot>
  N=0
  IFS=';' read -ra EINTRAEGE <<< "$2"
  for E in "${EINTRAEGE[@]}"; do
    [ -z "$E" ] && continue
    echo "PRUEFLISTE block=$1 uebersprungen_test=${E%%|*} grund=${E#*|}"
    N=$((N + 1))
  done
  [ -n "$4" ] && N="$4"
  ZEILE="PRUEFLISTE block=$1 bestanden=$3 fehlgeschlagen=0 uebersprungen=$N"
  [ -n "$5" ] && ZEILE="$ZEILE rot=$5"
  echo "$ZEILE"; echo "BLOCK $ZEILE" >> "$BERICHT"
}
echo "PRUEFLISTE block=backend start"; melde backend "$UEBERSPRUNGEN_BACKEND" 5 "" ""
echo "PRUEFLISTE block=oberflaechen_check start"; melde oberflaechen_check "" 5 "" ""
echo "PRUEFLISTE block=browser_tests start"
melde browser_tests "$UEBERSPRUNGEN_BROWSER" "$BROWSER_BESTANDEN" "$BROWSER_UEBERSPRUNGEN_ZAHL" "$BROWSER_ROT"
echo "ENDE $GESAMT" >> "$BERICHT"
exit $GESAMT
"""


def _bereite_vor(u, liste, browser=(), bestanden=5, zahl=None, rot=""):
    """Platzhalter-Prüfliste und feste Liste als Ausgangsstand (eingecheckt UND auf dem Wegwerf-GitHub,
    damit sie nicht als fremde Änderung zählen); steuert, was der Block Browser-Tests meldet."""
    skript = _PLATZHALTER.replace("__STEUERUNG__", str(u.steuerung)).replace("__BERICHT__", str(u.bericht))
    u.schreibe(PRUEFLISTE_RELPFAD, skript)
    (u.repo / PRUEFLISTE_RELPFAD).chmod(0o755)
    u.schreibe(LISTE_RELPFAD, "# Bekannte Überspring-Gründe (Übungsablage)\n"
               + "".join(f"{t} | {g}\n" for t, g in liste))
    u.committe("Ausgangsstand Prüfwerkzeuge (Übungsablage)", PRUEFLISTE_RELPFAD, LISTE_RELPFAD)
    u.git("push", "-q", "origin", "main")
    paare = ";".join(f"{t}|{g}" for t, g in browser)
    u.steuerung.write_text(
        f"UEBERSPRUNGEN_BROWSER='{paare}'\nBROWSER_BESTANDEN={bestanden}\n"
        f"BROWSER_UEBERSPRUNGEN_ZAHL='{'' if zahl is None else zahl}'\nBROWSER_ROT='{rot}'\n",
        encoding="utf-8")
    u.standard_ticket()


def _ein_probelauf(u, erg):
    laeufe = u.probelaeufe()
    assert len(laeufe) == 1 and laeufe[0].ende == 0, erg.zeige(
        f"Befund: erwartet genau einen vollständigen Probelauf, gesehen {len(laeufe)}")


def _zeile_nennt(ausgabe, *teile):
    return any(all(t in z for t in teile) for z in ausgabe.splitlines() if not z.startswith("PRUEFLISTE "))


def _rot_und_nichts_hochgeladen(u, github_vorher, erg, befund):
    assert len(u.probelaeufe()) == 1, erg.zeige("Befund: Probelauf lief nicht")
    assert u.github_zustand() == github_vorher, erg.zeige(befund)


# ════════════════════════════════════════════════════════════════════════════
# Testfälle
# ════════════════════════════════════════════════════════════════════════════

def test_tf10a_ak9b_aufgelistetes_paar_im_browserblock_laesst_probelauf_gruen(uebung):
    """TASK-117 · TF-10a · AK9b — *Browser-Test wird aus einem als Paar (Test + Grund) aufgelisteten Grund
    übersprungen, die übrigen Browser-Tests bestehen* → *Release starten* → *Probelauf grün*, *auf GitHub
    angekommen*. Quelle: Spec AK9b (Entscheidung Stephan 30.10.2026)."""
    u = uebung
    _bereite_vor(u, liste=[(BEKANNT_TEST, BEKANNT_GRUND)], browser=[(BEKANNT_TEST, BEKANNT_GRUND)])
    stand = u.github_stand()
    erg = u.release_starten()
    _ein_probelauf(u, erg)
    assert len(u.github_neue_commits(stand)) == 1, erg.zeige(
        "Befund: Aufgelisteter Browser-Übersprung machte den Probelauf rot")
    assert u.github_version() == NAECHSTE_PATCH_VERSION, erg.zeige("Befund: Release nicht vollständig angekommen")


@pytest.mark.parametrize("fall", ["anderer_test", "aufgelisteter_test_mit_anderem_grund", "bekannter_plus_unbekannter"])
def test_tf10b_ak9b_nicht_aufgelistetes_paar_im_browserblock_macht_rot_und_wird_genannt(uebung, fall):
    """TASK-117 · TF-10b · AK9b — *Browser-Test wird aus einem NICHT aufgelisteten Grund übersprungen*
    (anderer Test; aufgelisteter Test mit anderem Grund; bekannter plus unbekannter Übersprung zusammen) →
    *Release starten* → *Probelauf rot*, *nichts auf GitHub angekommen*, *Meldung nennt Test und Grund*.
    Quelle: Spec AK9b („Jeder nicht aufgelistete Grund … bleibt rot und wird genannt“)."""
    u = uebung
    if fall == "anderer_test":
        test, grund, gemeldet = ANDERER_TEST, ANDERER_GRUND, [(ANDERER_TEST, ANDERER_GRUND)]
    elif fall == "aufgelisteter_test_mit_anderem_grund":
        test, grund, gemeldet = BEKANNT_TEST, ANDERER_GRUND, [(BEKANNT_TEST, ANDERER_GRUND)]
    else:
        test, grund = ANDERER_TEST, ANDERER_GRUND
        gemeldet = [(BEKANNT_TEST, BEKANNT_GRUND), (ANDERER_TEST, ANDERER_GRUND)]
    _bereite_vor(u, liste=[(BEKANNT_TEST, BEKANNT_GRUND)], browser=gemeldet)
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    _rot_und_nichts_hochgeladen(u, github_vorher, erg,
                                "Befund: Browser-Übersprung mit nicht aufgelistetem Grund wurde hochgeladen")
    assert _zeile_nennt(erg.ausgabe, test.split("::")[-1], grund), erg.zeige(
        "Befund: Keine eigene Meldung des Befehls, die den übersprungenen Browser-Test und seinen Grund nennt")


def test_tf10c_ak9b_ohne_liste_ist_jeder_browser_uebersprung_rot(uebung):
    """TASK-117 · TF-10c · AK9b (Gegenprobe) — *Feste Liste ist leer* und *Browser-Test wird übersprungen* →
    *Release starten* → *Probelauf rot*, *nichts auf GitHub angekommen*, *Meldung nennt Test und Grund*.
    Quelle: Spec AK9b (nur aufgelistete Paare sind erlaubt)."""
    u = uebung
    _bereite_vor(u, liste=[], browser=[(BEKANNT_TEST, BEKANNT_GRUND)])
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    _rot_und_nichts_hochgeladen(u, github_vorher, erg, "Befund: Ohne Liste wurde ein Browser-Übersprung hochgeladen")
    assert _zeile_nennt(erg.ausgabe, BEKANNT_TEST.split("::")[-1], BEKANNT_GRUND), erg.zeige(
        "Befund: Meldung nennt den übersprungenen Browser-Test und seinen Grund nicht")


@pytest.mark.parametrize("fall", ["werkzeug_fehlt_mit_passendem_listeneintrag",
                                  "werkzeug_fehlt_ohne_testzeile",
                                  "null_tests_mit_passenden_eintraegen"])
def test_tf10d_ak9b_fehlendes_werkzeug_oder_null_tests_bleiben_rot_trotz_liste(uebung, fall):
    """TASK-117 · TF-10d · AK9b/AK9 — *Browser-Werkzeug fehlt (kein Browser-Test bestanden) bzw. der Block
    hat 0 Tests* und *die Liste hat passende Einträge* → *Release starten* → *Probelauf rot*, *nichts auf
    GitHub angekommen*, *Meldung nennt den Grund*. Quelle: Spec AK9b („ein fehlendes Browser-Werkzeug und
    ein Block mit 0 Tests bleiben nach AK9 immer rot und werden genannt“)."""
    u = uebung
    liste = [(BEKANNT_TEST, BEKANNT_GRUND), ("tests/test_bug_85.py", WERKZEUG_GRUND)]
    if fall == "werkzeug_fehlt_mit_passendem_listeneintrag":
        _bereite_vor(u, liste=liste, browser=[("tests/test_bug_85.py", WERKZEUG_GRUND)],
                     bestanden=0, rot=WERKZEUG_GRUND)
        erwartet = r"Browser-Werkzeug"
    elif fall == "werkzeug_fehlt_ohne_testzeile":
        _bereite_vor(u, liste=liste, bestanden=0, zahl=1, rot=WERKZEUG_GRUND)
        erwartet = r"Browser-Werkzeug"
    else:
        _bereite_vor(u, liste=liste, bestanden=0, zahl=0)
        erwartet = r"keine Tests|0 Tests"
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    _rot_und_nichts_hochgeladen(u, github_vorher, erg,
                                f"Befund: Fall „{fall}“ wurde wegen passender Listeneinträge als grün gewertet")
    assert re.search(erwartet, erg.ausgabe, re.IGNORECASE), erg.zeige(
        f"Befund: Meldung nennt den Grund nicht (erwartet: {erwartet})")


def test_tf10e_ak9b_browserblock_nur_aufgelistete_uebersprunge_ohne_gelaufenen_test_ist_rot(uebung):
    """TASK-117 · TF-10e · AK9b (Klarstellung Stephan 30.10.2026) — *Im Block Browser-Tests läuft kein einziger
    Test (bestanden=0), alle Tests wurden übersprungen und jeder Übersprung steht als Paar in der Liste;
    Browser-Werkzeug ist vorhanden* → *Release starten* → *Probelauf rot*, *nichts auf GitHub angekommen*,
    *Meldung nennt den Browser-Block als „0 Tests“ bzw. ohne gelaufenen Test*. Quelle: Spec AK9b."""
    u = uebung
    paare = [(BEKANNT_TEST, BEKANNT_GRUND), (ANDERER_TEST, ANDERER_GRUND)]
    _bereite_vor(u, liste=paare, browser=paare, bestanden=0)
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    _rot_und_nichts_hochgeladen(u, github_vorher, erg,
                                "Befund: Browser-Block ohne einen gelaufenen Test wurde wegen aufgelisteter Übersprünge hochgeladen")
    assert any("Browser" in z and re.search(r"(?<!\d)0 Tests|ohne gelaufenen Test", z, re.IGNORECASE)
               for z in erg.ausgabe.splitlines()), erg.zeige(
        "Befund: Meldung nennt den Browser-Block nicht als „0 Tests“ bzw. ohne gelaufenen Test")
