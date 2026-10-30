"""TASK-117 · AK9a — Bekannte, fest aufgelistete Überspring-Gründe im Backend (Entscheidung Stephan 27.10.2026).

AK9a (Spec docs/analyse-entwurf/TASK-117_SPEC.md): Backend-Tests, die aus einem fest aufgelisteten,
bekannten Grund übersprungen werden, machen den Probelauf nicht rot. Jeder übersprungene Test mit
einem NICHT aufgelisteten Grund macht ihn rot und wird mit Grund genannt. Übersprungene Browser-Tests,
ein Block mit 0 Tests und ein fehlendes Werkzeug bleiben nach AK9 immer rot.

Geschrieben VOR der Umsetzung dieses Kriteriums (fotoalert-test Teil A). Nutzt die Übungsablage aus
task117_adapter.py unverändert (eingefroren); alle neuen Hilfen stehen nur in dieser Datei.

SCHNITTSTELLEN-VORSCHLAG DIESER TESTS (steht NICHT im Ticket — bei der Umsetzung festlegen; bei anderer
Form ändern sich nur die Konstanten und Hilfen im Block „Unterbau“ unten, nicht die Testfälle):
  • Feste Liste: FotoAlert/tools/bekannte_uebersprungene_tests.txt — eingecheckt, gehört zu den
    Prüfwerkzeugen; eine Zeile je Eintrag „<Test-ID> | <Grund>“ (Test-ID wie bei pytest relativ zu
    backend/, z. B. tests/test_x.py::test_y), Leerzeilen und Zeilen mit „#“ zählen nicht. Gelesen wird
    die Liste aus genau der geprüften Fassung (saubere Kopie).
  • Die gemeinsame Prüfliste meldet jeden übersprungenen Test maschinenlesbar:
      „PRUEFLISTE block=<kennung> uebersprungen_test=<Test-ID> grund=<Grund bis Zeilenende>“
    (zusätzlich zur Ergebniszeile „PRUEFLISTE block=<kennung> bestanden=… uebersprungen=<n>“).
  • Ein Übersprung gilt als bekannt, wenn Test-ID und Grund mit einem Listeneintrag übereinstimmen
    (Grund: der aufgelistete Text ist im gemeldeten Grund enthalten). Nur im Block „backend“.
  • Der Befehl meldet einen unbekannten Übersprung in einer eigenen Zeile, die Test und Grund nennt.

Testfall-IDs TF-09a–TF-09d sind Vorschläge dieses Test-Agenten (die Spec-Tabelle führt AK9a noch ohne TF).
"""
from __future__ import annotations

import pytest

from task117_adapter import (  # noqa: F401  (uebung ist eine Fixture)
    NAECHSTE_PATCH_VERSION,
    PRUEFLISTE_RELPFAD,
    uebung,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

# ════════════════════════════════════════════════════════════════════════════
# Unterbau (Schnittstellen-Vorschlag, siehe Modul-Docstring)
# ════════════════════════════════════════════════════════════════════════════
LISTE_RELPFAD = "FotoAlert/tools/bekannte_uebersprungene_tests.txt"

BEKANNT_TEST = "tests/test_beispiel.py::test_braucht_ephemeride"
BEKANNT_GRUND = "de421.bsp im Sandbox nicht verfügbar (wie im GitHub-Job test-backend)"
ANDERER_TEST = "tests/test_beispiel.py::test_braucht_modul"
ANDERER_GRUND = "Modul fehlt: shapely"
BROWSER_TEST = "tests/test_bug-80.py::test_kopfzeile"
BROWSER_GRUND = "Playwright nicht installiert"

# Platzhalter der gemeinsamen Prüfliste mit Meldung einzelner übersprungener Tests. Schreibt denselben
# Bericht wie der Platzhalter aus task117_adapter.py (LAUF/KOPIE/DATEI/BLOCK/ENDE), damit
# Uebung.probelaeufe() ihn lesen kann.
_PLATZHALTER = r"""#!/usr/bin/env bash
# PLATZHALTER der gemeinsamen Prüfliste — TASK-117 AK9a, nur Übungsablage.
STEUERUNG='__STEUERUNG__'
BERICHT='__BERICHT__'
UEBERSPRUNGEN_BACKEND=""; UEBERSPRUNGEN_BROWSER=""
[ -f "$STEUERUNG" ] && . "$STEUERUNG"
SELBST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOPIE="$(cd "$SELBST_DIR/../.." && pwd)"
{ echo "LAUF $$"; echo "CWD $PWD"; echo "KOPIE $KOPIE"; echo "ARGS $*"; } >> "$BERICHT"
GESAMT=0
melde() {   # melde <block> <liste "id|grund;id|grund">
  N=0
  IFS=';' read -ra EINTRAEGE <<< "$2"
  for E in "${EINTRAEGE[@]}"; do
    [ -z "$E" ] && continue
    echo "PRUEFLISTE block=$1 uebersprungen_test=${E%%|*} grund=${E#*|}"
    N=$((N + 1))
  done
  ZEILE="PRUEFLISTE block=$1 bestanden=5 fehlgeschlagen=0 uebersprungen=$N"
  echo "$ZEILE"; echo "BLOCK $ZEILE" >> "$BERICHT"
}
echo "PRUEFLISTE block=backend start"; melde backend "$UEBERSPRUNGEN_BACKEND"
echo "PRUEFLISTE block=oberflaechen_check start"; melde oberflaechen_check ""
echo "PRUEFLISTE block=browser_tests start"; melde browser_tests "$UEBERSPRUNGEN_BROWSER"
echo "ENDE $GESAMT" >> "$BERICHT"
exit $GESAMT
"""


def _bereite_vor(u, liste, backend=(), browser=()):
    """Legt Platzhalter-Prüfliste und (falls liste nicht None) die feste Liste als Ausgangsstand an —
    eingecheckt UND auf dem Wegwerf-GitHub, damit sie nicht als fremde Änderung zählen."""
    skript = _PLATZHALTER.replace("__STEUERUNG__", str(u.steuerung)).replace("__BERICHT__", str(u.bericht))
    u.schreibe(PRUEFLISTE_RELPFAD, skript)
    (u.repo / PRUEFLISTE_RELPFAD).chmod(0o755)
    pfade = [PRUEFLISTE_RELPFAD]
    if liste is not None:
        u.schreibe(LISTE_RELPFAD, "# Bekannte Überspring-Gründe (Übungsablage)\n"
                   + "".join(f"{t} | {g}\n" for t, g in liste))
        pfade.append(LISTE_RELPFAD)
    u.committe("Ausgangsstand Prüfwerkzeuge (Übungsablage)", *pfade)
    u.git("push", "-q", "origin", "main")
    fmt = lambda paare: ";".join(f"{t}|{g}" for t, g in paare)   # noqa: E731
    u.steuerung.write_text(f"UEBERSPRUNGEN_BACKEND='{fmt(backend)}'\nUEBERSPRUNGEN_BROWSER='{fmt(browser)}'\n",
                           encoding="utf-8")
    u.standard_ticket()


def _ein_probelauf(u, erg):
    laeufe = u.probelaeufe()
    assert len(laeufe) == 1 and laeufe[0].ende == 0, erg.zeige(
        f"Befund: erwartet genau einen vollständigen Probelauf, gesehen {len(laeufe)}")


def _zeile_nennt(ausgabe, *teile):
    return any(all(t in z for t in teile) for z in ausgabe.splitlines() if not z.startswith("PRUEFLISTE "))


# ════════════════════════════════════════════════════════════════════════════
# Testfälle
# ════════════════════════════════════════════════════════════════════════════

def test_tf09a_ak9a_aufgelisteter_grund_im_backend_laesst_probelauf_gruen(uebung):
    """TASK-117 · TF-09a · AK9a — *Backend-Test wird aus einem fest aufgelisteten, bekannten Grund
    übersprungen* → *Release starten* → *Probelauf grün*, *auf GitHub angekommen*. Quelle: Spec AK9a."""
    u = uebung
    _bereite_vor(u, liste=[(BEKANNT_TEST, BEKANNT_GRUND)], backend=[(BEKANNT_TEST, BEKANNT_GRUND)])
    stand = u.github_stand()
    erg = u.release_starten()
    _ein_probelauf(u, erg)
    assert len(u.github_neue_commits(stand)) == 1, erg.zeige(
        "Befund: Bekannter, aufgelisteter Übersprung machte den Probelauf rot")
    assert u.github_version() == NAECHSTE_PATCH_VERSION, erg.zeige("Befund: Release nicht vollständig angekommen")


@pytest.mark.parametrize("fall", ["anderer_test", "aufgelisteter_test_mit_anderem_grund"])
def test_tf09b_ak9a_nicht_aufgelisteter_grund_macht_probelauf_rot_und_wird_genannt(uebung, fall):
    """TASK-117 · TF-09b · AK9a — *Backend-Test wird aus einem NICHT aufgelisteten Grund übersprungen*
    (anderer Test; oder aufgelisteter Test mit anderem Grund) → *Release starten* → *Probelauf rot*,
    *nichts auf GitHub angekommen*, *Meldung nennt Test und Grund*. Quelle: Spec AK9a."""
    u = uebung
    if fall == "anderer_test":
        test, grund = ANDERER_TEST, ANDERER_GRUND
        uebersprungen = [(BEKANNT_TEST, BEKANNT_GRUND), (test, grund)]   # bekannter + unbekannter Übersprung
    else:
        test, grund = BEKANNT_TEST, ANDERER_GRUND
        uebersprungen = [(test, grund)]
    _bereite_vor(u, liste=[(BEKANNT_TEST, BEKANNT_GRUND)], backend=uebersprungen)
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    assert len(u.probelaeufe()) == 1, erg.zeige("Befund: Probelauf lief nicht")
    assert u.github_zustand() == github_vorher, erg.zeige(
        "Befund: Übersprung mit nicht aufgelistetem Grund wurde als grün gewertet und hochgeladen")
    assert _zeile_nennt(erg.ausgabe, test.split("::")[-1], grund), erg.zeige(
        "Befund: Keine eigene Meldung des Befehls, die den übersprungenen Test und seinen Grund nennt")


@pytest.mark.parametrize("liste", ["fehlt", "leer"])
def test_tf09c_ak9a_ohne_liste_ist_jeder_backend_uebersprung_rot(uebung, liste):
    """TASK-117 · TF-09c · AK9a (Gegenprobe) — *Feste Liste fehlt / ist leer* und *Backend-Test wird
    übersprungen* → *Release starten* → *Probelauf rot*, *nichts auf GitHub angekommen*, *Meldung nennt
    Test und Grund*. Quelle: Spec AK9a (nur aufgelistete Gründe sind erlaubt)."""
    u = uebung
    _bereite_vor(u, liste=None if liste == "fehlt" else [], backend=[(BEKANNT_TEST, BEKANNT_GRUND)])
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    assert len(u.probelaeufe()) == 1, erg.zeige("Befund: Probelauf lief nicht")
    assert u.github_zustand() == github_vorher, erg.zeige(
        f"Befund: Ohne Liste ({liste}) wurde ein Backend-Übersprung als grün gewertet")
    assert _zeile_nennt(erg.ausgabe, BEKANNT_TEST.split("::")[-1], BEKANNT_GRUND), erg.zeige(
        "Befund: Meldung nennt den übersprungenen Test und seinen Grund nicht")


def test_tf09d_ak9a_nicht_aufgelisteter_browser_uebersprung_bleibt_rot(uebung):
    """TASK-117 · TF-09d · AK9a/AK9/AK9b — *Browser-Test wird übersprungen und steht NICHT in der Liste*
    (die Liste enthält andere Einträge, auch einen Backend-Eintrag mit demselben Grund) → *Release
    starten* → *Probelauf rot*, *nichts auf GitHub angekommen*, *Meldung nennt den übersprungenen
    Browser-Block*. Quelle: Spec AK9a/AK9 („Übersprungene Browser-Tests … bleiben nach AK9 rot“),
    angepasst nach AK9b (Entscheidung 30.10.2026): ein aufgelisteter Browser-Übersprung ist nicht mehr
    zwingend rot. Geändert mit ausdrücklicher Freigabe von Stephan am 30.10.2026 (nur dieser Test)."""
    u = uebung
    backend_eintrag = ("tests/test_beispiel.py::test_braucht_playwright_im_backend", BROWSER_GRUND)
    _bereite_vor(u, liste=[backend_eintrag], backend=[backend_eintrag], browser=[(BROWSER_TEST, BROWSER_GRUND)])
    github_vorher = u.github_zustand()
    erg = u.release_starten()
    assert len(u.probelaeufe()) == 1, erg.zeige("Befund: Probelauf lief nicht")
    assert u.github_zustand() == github_vorher, erg.zeige(
        "Befund: Nicht aufgelisteter Browser-Übersprung wurde als grün gewertet und hochgeladen")
    assert _zeile_nennt(erg.ausgabe, "Browser-Tests", "übersprungen"), erg.zeige(
        "Befund: Meldung nennt den übersprungenen Browser-Block nicht")
