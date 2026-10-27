"""TASK-116 — Backlog bereinigen: verwaisten Text unter dem Ausgangsticket ins Archiv verschieben.

Verbindliche Spec: Ticket TASK-116 in BACKLOG.md (AK1–AK19, Testfälle TF-01 … TF-20).
Geschrieben VOR der Umsetzung (fotoalert-test Teil A). Das Werkzeug gibt es noch nicht; jeder Test
hier scheitert deshalb mit „Werkzeug fehlt noch“, bis der Umsetzer es baut.

Ausführung: Jeder Test baut kleine, feste, künstliche Übungsdateien (Backlog + Archiv + Sicherungs-
ordner) im pytest-Temp-Ordner und startet das Werkzeug als eigenen Prozess. Geprüft wird nur sichtbare
Wirkung: Dateien vorher/nachher, Ausgabe, Rückgabewert. Das echte Backlog wird nie gelesen oder
verändert (Test-Isolation). Keine Uhrzeit, kein Netz, kein Git. Erwartete Werte (Zeilen, Zeichen,
Prüfsumme, Spalten) kommen aus der Übungswelt, die dieser Test selbst aufbaut, nicht aus dem Werkzeug.
Gelesen werden nur die echten Regeln der Backlog-Prüfung und der Board-Erzeugung (tools/), nie
verändert (TF-20).

Automatisch hier: TF-01 … TF-20. TF-20 steht in zwei Tests (AK5 und AK8), weil jeder Test zu genau
einem Kriterium gehört.

Spätere Prüfungen (nicht automatisch in dieser Datei — wer/wann/wie):
  • TF-21 (AK2, AK3, AK5, AK13) einmalig durch den Umsetzer an einer KOPIE der echten Dateien, im Ticket
    protokolliert: genau 554 Zeilen, 78.657 Zeichen, Prüfsumme f0bae246229e6b136aa9d62c4ca25915,
    Ticketzahl vorher = nachher, Backlog-Prüfung 0 Fehler / 0 Warnungen. Nie im Dauer-Testlauf,
    nie am Original.

SCHNITTSTELLE (VERBINDLICH für den Umsetzer; ebenso im Ticket TASK-116 festgeschrieben): Werkzeugname,
Modi, Ausgabe-Schlüssel, Anhang-Marken und Prüfhaken unten sind Teil der Vorgabe. Der Umsetzer baut das
Werkzeug genau so und ändert diese Tests nie. Hält er eine Abweichung für nötig, meldet er das; Stephan
entscheidet.
  Aufruf:  python tools/backlog_verschieben.py --backlog B --archiv A --ticket TASK-905 --sicherung DIR MODUS
  MODUS:   --pruefen (schreibt nichts) | --ausfuehren | --nachweis (mit --vorher-backlog/--vorher-archiv)
           | --bericht (weitere verwaiste Abschnitte, schreibt nichts)
  Zusätze: --erwartet-md5 X, --erwartet-zeilen N, --erwartet-text DATEI
  Ausgabe: Zeilen „SCHLÜSSEL=Wert“; Schlüssel ZUSTAND (noch zu tun | Zwischenzustand | erledigt),
           TEXT_ZEILEN, TEXT_ZEICHEN, TEXT_MD5, TICKETS, DOPPELTE_IDS, LINT_FEHLER, LINT_WARNUNGEN,
           „SPALTE <ID>“, SUMME_ZEILEN, SUMME_ZEICHEN, ERGAENZTE_ZEILEN, ERGAENZTE_ZEICHEN,
           ERGEBNIS (ok | bereits erledigt | abgebrochen | nur geprueft), GRUND, ABWEICHENDE_ZEILE,
           KOPFARTIGE_ZEILE (Zeilennummer in der Backlog-Datei), NACHWEIS (gruen | rot), ABWEICHUNG,
           VERWAISTE_ABSCHNITTE, FUND, SICHERUNG_BACKLOG_MD5 und SICHERUNG_ARCHIV_MD5 (Prüfsummen der
           beiden Sicherungskopien, Protokoll zu AK7). Rückgabewert 0 = in Ordnung, 1 = abgebrochen / rot.
           Ausgegeben werden nie Zeileninhalte.
  Text:    der Text beginnt in der Zeile nach dem Trennstrich „---“ unter der „**Quelle:**“-Zeile des
           Ausgangstickets und läuft bis Dateiende; Prüfsumme (MD5) und Zeilenzahl über genau diese Bytes.
  Anhang im Archiv (am Dateiende angehängt):
           <!-- TASK-116-ANHANG-BEGINN -->  Kopf  <!-- TASK-116-TEXT-BEGINN -->
           Text  \\n  <!-- TASK-116-TEXT-ENDE -->  <!-- TASK-116-ANHANG-ENDE -->
           (vor der Endemarke steht genau ein zusätzlicher Zeilenumbruch, der beim Herauslösen entfällt)
  Kopf des Anhangs: feste Zeilen „Zeilen: <N>“ und „Prüfsumme (MD5): <32 Hex>“ (je eine eigene Zeile),
           Überschrift „## … TASK-116 …“ mit Datum JJJJ-MM-TT, Herkunft (Ticketnummer des Ausgangstickets),
           „unverändert übernommen“, „Zuordnung ist Einschätzung“, „nicht bestätigt“, Warnung zu TASK-110;
           Zuordnungsliste als Tabelle mit den vier Spalten
           | Textzeilen | Überschrift | Genannte Tickets | Einschätzung |, Textzeilen als „von–bis“
           (Zeile 1 des Textes = führende Leerzeile; ein Abschnitt reicht von seiner Überschrift bis vor die
           nächste Überschrift); „zugeordnet“ nur bei genau einem Ticket mit mindestens zwei Nennungen
           im Abschnitt (Entscheidung Stephan 2026-10-26), sonst „Einschätzung“.
  Sicherungen: <SICHERUNGSORDNER>/BACKLOG.vor_task116_JJJJ-MM-TT-HHMM.md und
           BACKLOG-ARCHIVE.vor_task116_JJJJ-MM-TT-HHMM.md
  Prüfhaken (bewusst im Werkzeug vorgesehen, nur für Tests): Umgebung T116_ABBRUCH_NACH=sicherung|archiv beendet das Werkzeug mit
           Rückgabewert 99 unmittelbar nach diesem Schritt; T116_HAKEN_NACH_PRUEFUNG=<Skript> wird
           zwischen Prüfung und Schreiben mit Python gestartet (simuliert einen fremden Schreiber).

Python-3.9-kompatibel (Produktion/CI). Keine Abhängigkeit von conftest.py, FastAPI oder Netzwerk.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

PROJEKT_DIR = Path(__file__).resolve().parent.parent.parent          # FotoAlert/
WERKZEUG = PROJEKT_DIR / "tools" / "backlog_verschieben.py"            # Schnittstelle: verbindlich
LINT = PROJEKT_DIR / "tools" / "lint_backlog.py"                       # echte Regeln, nur gelesen
KANBAN = PROJEKT_DIR / "tools" / "gen_kanban.py"                       # echte Regeln, nur gelesen
AUSGANGSTICKET = "TASK-905"

ANHANG_BEGINN = "<!-- TASK-116-ANHANG-BEGINN -->"
ANHANG_ENDE = "<!-- TASK-116-ANHANG-ENDE -->"
TEXT_BEGINN = "<!-- TASK-116-TEXT-BEGINN -->"
TEXT_ENDE = "<!-- TASK-116-TEXT-ENDE -->"

# ══════════════════════════════════════════════════════════════════
# ÜBUNGSWELT (fest, künstlich; Zählung von Hand: siehe Asserts in welt_ist_gesund)
# ══════════════════════════════════════════════════════════════════
# Spalten von Hand aus den Status-Feldern bzw. Archiv-Markierungen abgeleitet (nicht aus dem Werkzeug):
SPALTEN_VON_HAND = {
    "TASK-901": "analysis", "TASK-902": "inprogress", "TASK-903": "waiting_decision",
    "TASK-904": "inbox", "TASK-905": "inbox",
    "TASK-951": "done", "TASK-952": "done", "TASK-953": "done",
}

# Der fremde Text: 14 Zeilen von Hand gezählt, Zeile 1 = führende Leerzeile, 3 Hauptabschnitte („## “).
FREMD_ZEILEN = [
    "",
    "## Analyse (2026-08-10)",
    "Sicherheitspunkte a bis c zu TASK-801: Abhängigkeiten prüfen. Umlaute äöüß — ✅",
    "TASK-801 verlangt eine Prüfung; laut TASK-801 sind drei Pakete betroffen.",
    "",
    "### Example Mapping",
    "- Regel: nichts geht verloren",
    "",
    "## Zwischenstand Schritt 1",
    "Keine Ticketnummer in diesem Abschnitt.",
    "Zeile mit Leerzeichen am Ende:   ",
    "",
    "## Abschluss (2026-08-11)",
    "Siehe auch TASK-802 (nur als Verweis).",
]
FREMD_ANZAHL_ZEILEN = 14
GEHEIMNIS = "abc123xyz"


def _ticket(tid, titel, status, marker=" ", extra=""):
    return (
        "### %s · %s `[%s]`\n\n| Feld | Wert |\n|------|------|\n| **Typ** | Task |\n"
        "| **Status** | %s |\n\n**Beschreibung:** Übungstext zu %s.\n%s\n---\n\n"
        % (tid, titel, marker, status, tid, extra)
    )


def eigener_teil(fueller=0):
    extra = "".join("Füllzeile %d\n" % i for i in range(fueller))
    teile = [
        "# Backlog (Übung)\n\n## Offene Tickets\n\n",
        _ticket("TASK-901", "Erstes Ticket", "In Analysis", " ", extra),
        _ticket("TASK-902", "Zweites Ticket", "In Progress", "~"),
        _ticket("TASK-903", "Drittes Ticket", "Wartet auf Entscheidung"),
        _ticket("TASK-904", "Viertes Ticket", "ToDo"),
    ]
    ausgang = (
        "### %s · Ausgangsticket `[ ]`\n\n| Feld | Wert |\n|------|------|\n| **Typ** | Task |\n"
        "| **Status** | ToDo |\n\n**Beschreibung:** Eigener Text des Ausgangstickets.\n\n"
        "**Quelle:** Übung (Prüfbericht).\n\n---\n" % AUSGANGSTICKET
    )
    return "".join(teile) + ausgang


# Die echte Backlog-Prüfung wacht über das Epic TASK-92 und seine 12 Kinder (Verlust-Wächter E4);
# die Übungswelt enthält sie deshalb als erledigte Archivtickets (sonst wäre jede Übung „rot“).
EPIC_KINDER = ["TASK-82", "BUG-81", "TASK-83", "TASK-84", "TASK-85", "TASK-86", "TASK-87", "TASK-88",
               "TASK-89", "TASK-90", "TASK-91", "BUG-82"]
ANZAHL_TICKETS = 21   # 5 Backlog + 3 Archiv + Epic TASK-92 + 12 Kinder (von Hand gezählt)


def _epic_bloecke():
    out = ("### TASK-92 · Epic (Übung) `[x]`\n\n| Feld | Wert |\n|------|------|\n| **Typ** | Epic |\n"
           "| **Status** | Done |\n\n---\n\n")
    for k in EPIC_KINDER:
        out += ("### %s · Kind (Übung) `[x]`\n\n| Feld | Wert |\n|------|------|\n| **Typ** | Task |\n"
                "| **Status** | Done |\n| **Epic** | TASK-92 |\n\n---\n\n" % k)
    return out


ARCHIV = (
    "# Archiv (Übung)\n\n## Archiv\n\n"
    "### TASK-951 · Erledigt mit Status `[x]`\n\n| Feld | Wert |\n|------|------|\n| **Status** | Done |\n\n"
    "**Beschreibung:** Archivkopf 951.\n\n---\n\n"
    "### ~~TASK-952 · Durchgestrichen ohne Status~~\n\n**Beschreibung:** Archivkopf 952.\n\n---\n\n"
    "### TASK-953 · Marker ohne Status `[x]`\n\n**Beschreibung:** Archivkopf 953.\n\n---\n\n"
    + _epic_bloecke()
)
for _k in ["TASK-92"] + EPIC_KINDER:
    SPALTEN_VON_HAND[_k] = "done"


def fremd_text(zeilen=None, schluss_umbruch=True):
    z = FREMD_ZEILEN if zeilen is None else zeilen
    return ("\n".join(z) + ("\n" if schluss_umbruch else "")).encode("utf-8")


class Welt:
    def __init__(self, tmp, backlog_bytes, archiv_bytes, text_bytes, eigen_bytes):
        self.tmp = tmp
        self.backlog = tmp / "BACKLOG.md"
        self.archiv = tmp / "BACKLOG-ARCHIVE.md"
        self.sicherung = tmp / "sicherung"
        self.sicherung.mkdir()
        self.backlog.write_bytes(backlog_bytes)
        self.archiv.write_bytes(archiv_bytes)
        self.text = text_bytes
        self.eigen = eigen_bytes
        self.backlog0 = backlog_bytes
        self.archiv0 = archiv_bytes

    def lies(self, pfad=None):
        return (pfad or self.backlog).read_bytes()


def baue_welt(tmp, zeilen=None, schluss_umbruch=True, fueller=0, eigen=None):
    eigen_b = (eigen if eigen is not None else eigener_teil(fueller)).encode("utf-8")
    text_b = fremd_text(zeilen, schluss_umbruch)
    return Welt(tmp, eigen_b + text_b, ARCHIV.encode("utf-8"), text_b, eigen_b)


@pytest.fixture
def welt(tmp_path):
    return baue_welt(tmp_path)


# ══════════════════════════════════════════════════════════════════
# HILFEN (Treiber-Schicht: bedienen und beobachten, legen nie selbst ein Ergebnis fest)
# ══════════════════════════════════════════════════════════════════
def md5(b):
    return hashlib.md5(b).hexdigest()


def zeilenzahl(b):
    return b.count(b"\n") + (1 if b and not b.endswith(b"\n") else 0)


def lauf(welt, *args, env=None, sicherung=None, mit_pfaden=True):
    """Startet das Werkzeug. Fehlt es noch -> Test scheitert mit klarer Meldung (Verhalten fehlt)."""
    if not WERKZEUG.exists():
        pytest.fail("Werkzeug fehlt noch: %s gibt es noch nicht (TASK-116 noch nicht umgesetzt)" % WERKZEUG.name)
    cmd = [sys.executable, str(WERKZEUG)]
    if mit_pfaden:
        cmd += ["--backlog", str(welt.backlog), "--archiv", str(welt.archiv), "--ticket", AUSGANGSTICKET,
                "--sicherung", str(sicherung if sicherung is not None else welt.sicherung)]
    cmd += list(args)
    e = {k: v for k, v in os.environ.items() if not k.startswith("T116_")}
    e["PYTHONIOENCODING"] = "utf-8"
    e["HOME"] = str(welt.tmp)
    if env:
        e.update(env)
    p = subprocess.run(cmd, cwd=str(welt.tmp), env=e, capture_output=True, timeout=120)
    p.out = p.stdout.decode("utf-8", "replace")
    p.err = p.stderr.decode("utf-8", "replace")
    p.alles = p.out + "\n" + p.err
    p.kv = {}
    for z in p.out.splitlines():
        m = re.match(r"^([A-ZÄÖÜ0-9_]+(?: [A-Za-z0-9-]+)?)=(.*)$", z)
        if m and m.group(1) not in p.kv:
            p.kv[m.group(1)] = m.group(2).strip()
    return p


def pruefen(welt, *zusatz):
    return lauf(welt, "--pruefen", *zusatz)


def ausfuehren(welt, *zusatz, **kw):
    return lauf(welt, "--ausfuehren", *zusatz, **kw)


def nachweis(welt, vorher_backlog, vorher_archiv):
    return lauf(welt, "--nachweis", "--vorher-backlog", str(vorher_backlog), "--vorher-archiv", str(vorher_archiv))


def kopie_vorher(welt):
    b = welt.tmp / "vorher_BACKLOG.md"
    a = welt.tmp / "vorher_ARCHIV.md"
    b.write_bytes(welt.lies(welt.backlog))
    a.write_bytes(welt.lies(welt.archiv))
    return b, a


def anhang(archiv_bytes):
    t = archiv_bytes.decode("utf-8")
    i = t.find(ANHANG_BEGINN)
    assert i >= 0, "Anhang-Anfangsmarke fehlt im Archiv"
    return t[i:]


def text_aus_anhang(archiv_bytes):
    a = anhang(archiv_bytes)
    s = a.index(TEXT_BEGINN + "\n") + len(TEXT_BEGINN) + 1
    e = a.index("\n" + TEXT_ENDE)
    return a[s:e].encode("utf-8")


def kopf_aus_anhang(archiv_bytes):
    a = anhang(archiv_bytes)
    return a[: a.index(TEXT_BEGINN)]


def lint(pfad):
    p = subprocess.run([sys.executable, str(LINT), str(pfad)], capture_output=True, timeout=60)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def kanban_karten(backlog_bytes, archiv_bytes):
    spec = importlib.util.spec_from_file_location("gen_kanban_t116", str(KANBAN))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    text = backlog_bytes.decode("utf-8") + "\n\n" + archiv_bytes.decode("utf-8")
    return {t["id"]: t for t in mod.parse_backlog(text)}


def bloecke(text):
    """Ticketblöcke: von „### <ID> ·“ bis zur nächsten „### “- oder „## “-Zeile, hinten ohne Zeilenumbrüche."""
    ergebnis, aktuell, tid = {}, [], None
    for z in text.split("\n"):
        m = re.match(r"^###\s+(?:~~)?\s*([A-Z]+-\d+[a-z]?)\s*[·:\-]", z)
        if z.startswith("### ") or z.startswith("## "):
            if tid:
                ergebnis[tid] = "\n".join(aktuell).rstrip("\n")
            aktuell, tid = [], None
        if m:
            tid = m.group(1)
        if tid:
            aktuell.append(z)
    if tid:
        ergebnis[tid] = "\n".join(aktuell).rstrip("\n")
    return ergebnis


def welt_ist_gesund(welt, ticketzahl=ANZAHL_TICKETS):
    """Vorbedingung: Übungswelt ist gültig (echte Backlog-Prüfung sauber, Spalten wie von Hand erwartet)."""
    rc, ausgabe = lint(welt.backlog)
    assert rc == 0, "Übungswelt nicht lint-sauber: " + ausgabe
    assert "%d Tickets · 0 Fehler · 0 Warnungen" % ticketzahl in ausgabe, ausgabe
    karten = kanban_karten(welt.lies(welt.backlog), welt.lies(welt.archiv))
    for tid, spalte in SPALTEN_VON_HAND.items():
        assert karten[tid]["lane"] == spalte, (tid, karten[tid]["lane"], spalte)


def spalten(p):
    return {k.split(" ", 1)[1]: v for k, v in p.kv.items() if k.startswith("SPALTE ")}


def gesamtzeilen_und_zeichen(welt):
    b, a = welt.lies(welt.backlog), welt.lies(welt.archiv)
    return (zeilenzahl(b) + zeilenzahl(a),
            len(b.decode("utf-8")) + len(a.decode("utf-8")))


def sicherungsdateien(welt):
    return sorted(p.name for p in welt.sicherung.iterdir())


def aufbau_pruefen():
    assert len(FREMD_ZEILEN) == FREMD_ANZAHL_ZEILEN
    assert sum(1 for z in FREMD_ZEILEN if z.startswith("## ")) == 3


# ══════════════════════════════════════════════════════════════════
# TF-01 · AK1
# ══════════════════════════════════════════════════════════════════
def test_tf01_ak1_backlog_endet_mit_dem_trennstrich_des_tickets(welt):
    """TF-01 · AK1 · TASK-116
    Angenommen ein Übungsbacklog mit einem Ticket, dessen eigener Text mit „Quelle“ und Trennstrich endet,
    und darunter drei fremde Abschnitte. Wenn das Werkzeug ausführt. Dann endet der Backlog mit dem
    Trennstrich des Tickets; kein Zeichen der fremden Abschnitte steht mehr darin."""
    aufbau_pruefen()
    welt_ist_gesund(welt)
    p = ausfuehren(welt)
    assert p.returncode == 0, p.alles
    nach = welt.lies(welt.backlog)
    assert nach == welt.eigen
    assert nach.endswith(b"**Quelle:** \xc3\x9cbung (Pr\xc3\xbcfbericht).\n\n---\n")
    for z in FREMD_ZEILEN:
        if z.strip():
            assert z not in nach.decode("utf-8")


# ══════════════════════════════════════════════════════════════════
# TF-02 · AK2
# ══════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("schluss_umbruch", [True, False], ids=["mit_Schlussumbruch", "ohne_Schlussumbruch"])
def test_tf02_ak2_pruefsumme_im_archiv_gleich_wie_vorher(tmp_path, schluss_umbruch):
    """TF-02 · AK2 · TASK-116
    Angenommen dasselbe Übungsbacklog (Prüfsumme vorher aus den bekannten Textbytes gebildet). Wenn
    verschoben wurde. Dann ist die Prüfsumme des Anhangs im Archiv gleich der von vorher, Byte für Byte
    (auch ohne Schlusszeilenumbruch am Dateiende)."""
    w = baue_welt(tmp_path, schluss_umbruch=schluss_umbruch)
    soll = md5(w.text)
    p = ausfuehren(w)
    assert p.returncode == 0, p.alles
    im_archiv = text_aus_anhang(w.lies(w.archiv))
    assert im_archiv == w.text
    assert md5(im_archiv) == soll
    q = pruefen(w)
    assert q.kv.get("TEXT_MD5") == soll
    assert q.kv.get("TEXT_ZEILEN") == str(FREMD_ANZAHL_ZEILEN)


def test_tf02_ak2_gegenprobe_veraendertes_zeichen_macht_pruefung_rot(welt):
    """TF-02 · AK2 · TASK-116 · Gegenprobe
    Wenn nach dem Verschieben ein einziges Zeichen im Anhang des Archivs verändert wird, meldet die
    Nachweis-Prüfung Rot."""
    b0, a0 = kopie_vorher(welt)
    assert ausfuehren(welt).returncode == 0
    gut = nachweis(welt, b0, a0)
    assert gut.kv.get("NACHWEIS") == "gruen", gut.alles
    a = welt.lies(welt.archiv)
    i = a.index("verloren".encode())
    welt.archiv.write_bytes(a[:i] + b"X" + a[i + 1:])
    schlecht = nachweis(welt, b0, a0)
    assert schlecht.returncode == 1
    assert schlecht.kv.get("NACHWEIS") == "rot", schlecht.alles


# ══════════════════════════════════════════════════════════════════
# TF-03 · AK3
# ══════════════════════════════════════════════════════════════════
def test_tf03_ak3_summe_nachher_gleich_vorher_plus_ergaenzte_zeilen(welt):
    """TF-03 · AK3 · TASK-116
    Angenommen Übungsdateien mit bekannter Zeilen- und Zeichenzahl. Wenn verschoben wurde. Dann ist die
    Summe aus Backlog und Archiv nachher gleich vorher plus der gemeldeten Anzahl ergänzter Kopf-,
    Hinweis- und Listenzeilen (Zeilen und Zeichen)."""
    z0, c0 = gesamtzeilen_und_zeichen(welt)
    vorher = pruefen(welt)
    assert vorher.kv.get("SUMME_ZEILEN") == str(z0), vorher.alles
    assert vorher.kv.get("SUMME_ZEICHEN") == str(c0)
    p = ausfuehren(welt)
    assert p.returncode == 0, p.alles
    z1, c1 = gesamtzeilen_und_zeichen(welt)
    ergaenzt_z = int(p.kv["ERGAENZTE_ZEILEN"])
    ergaenzt_c = int(p.kv["ERGAENZTE_ZEICHEN"])
    assert ergaenzt_z > 0 and ergaenzt_c > 0
    assert z1 == z0 + ergaenzt_z
    assert c1 == c0 + ergaenzt_c


# ══════════════════════════════════════════════════════════════════
# TF-04 · AK4
# ══════════════════════════════════════════════════════════════════
def test_tf04_ak4_alle_ticketbloecke_unveraendert(welt):
    """TF-04 · AK4 · TASK-116
    Angenommen Übungsdateien mit fünf Tickets im Backlog (darunter das Ausgangsticket) und drei (plus Epic-Wächter-Tickets) im Archiv.
    Wenn verschoben wurde. Dann sind alle Ticketblöcke Zeichen für Zeichen unverändert (am Ende ohne
    Leerzeilen verglichen)."""
    vor = dict(bloecke(welt.lies(welt.backlog).decode("utf-8")))
    vor.update(bloecke(welt.lies(welt.archiv).decode("utf-8")))
    assert len(vor) == ANZAHL_TICKETS
    assert ausfuehren(welt).returncode == 0
    nach = dict(bloecke(welt.lies(welt.backlog).decode("utf-8")))
    nach.update(bloecke(welt.lies(welt.archiv).decode("utf-8")))
    assert nach.keys() == vor.keys()
    for tid in vor:
        assert nach[tid] == vor[tid], tid


def test_tf04_ak4_gegenprobe_veraenderter_anderer_block_macht_pruefung_rot(welt):
    """TF-04 · AK4 · TASK-116 · Gegenprobe
    Wird nach dem Verschieben ein anderer Ticketblock absichtlich verändert, meldet die Prüfung Rot und
    nennt das betroffene Ticket."""
    b0, a0 = kopie_vorher(welt)
    assert ausfuehren(welt).returncode == 0
    t = welt.lies(welt.backlog).decode("utf-8").replace("Übungstext zu TASK-902.", "Übungstext zu TASK-902 (verändert).")
    welt.backlog.write_bytes(t.encode("utf-8"))
    p = nachweis(welt, b0, a0)
    assert p.returncode == 1
    assert p.kv.get("NACHWEIS") == "rot"
    assert "TASK-902" in p.alles


# ══════════════════════════════════════════════════════════════════
# TF-05 · AK5
# ══════════════════════════════════════════════════════════════════
def test_tf05_ak5_ticketzahl_gleich_keine_doppelten_nummern_pruefung_sauber(welt):
    """TF-05 · AK5 · TASK-116
    Angenommen Übungsdateien mit 21 Tickets (8 eigene + Epic-Wächter-Tickets). Wenn verschoben wurde. Dann zählt die Prüfung weiterhin
    21 Tickets, keine doppelte Nummer, 0 Fehler, 0 Warnungen — vorher und nachher."""
    welt_ist_gesund(welt)
    vorher = pruefen(welt)
    assert ausfuehren(welt).returncode == 0
    nachher = pruefen(welt)
    for p in (vorher, nachher):
        assert p.kv.get("TICKETS") == str(ANZAHL_TICKETS), p.alles
        assert p.kv.get("DOPPELTE_IDS") == "0"
        assert p.kv.get("LINT_FEHLER") == "0"
        assert p.kv.get("LINT_WARNUNGEN") == "0"


def test_tf05_ak5_gegenprobe_doppelter_ticketkopf_macht_pruefung_rot(welt):
    """TF-05 · AK5 · TASK-116 · Gegenprobe
    Ein absichtlich doppelter Ticketkopf macht die Nachweis-Prüfung Rot."""
    b0, a0 = kopie_vorher(welt)
    assert ausfuehren(welt).returncode == 0
    with open(welt.backlog, "ab") as f:
        f.write(_ticket("TASK-901", "Doppelt", "ToDo").encode("utf-8"))
    p = nachweis(welt, b0, a0)
    assert p.returncode == 1
    assert p.kv.get("NACHWEIS") == "rot", p.alles
    assert "TASK-901" in p.alles


# ══════════════════════════════════════════════════════════════════
# TF-06 · AK6
# ══════════════════════════════════════════════════════════════════
TF06_ZEILEN = [
    "",                                                  # 1
    "## Erster Abschnitt",                               # 2
    "TASK-801 wird hier genannt.",                       # 3
    "Noch einmal TASK-801 als Beleg.",                   # 4
    "",                                                  # 5
    "## Zweiter Abschnitt",                              # 6
    "Nur ein Verweis: siehe TASK-802.",                  # 7
    "",                                                  # 8
    "## Dritter Abschnitt",                              # 9
    "TASK-803 und TASK-804 stehen hier.",                # 10
    "Wieder TASK-803 sowie TASK-804.",                   # 11
    "",                                                  # 12
    "## Vierter Abschnitt",                              # 13
    "Keine Ticketnummer.",                               # 14
]


def test_tf06_ak6_zuordnungsliste_ehrlich_und_nicht_bestaetigt(tmp_path):
    """TF-06 · AK6 · TASK-116 (Regel Stephan 2026-10-26: „zugeordnet“ nur, wenn ein Abschnitt genau ein
    Ticket mindestens zweimal nennt)
    Angenommen ein Übungstext mit vier Abschnitten: der erste nennt „TASK-801“ genau zweimal, der zweite
    nennt „TASK-802“ genau einmal (nur als Verweis), der dritte nennt zwei verschiedene Tickets
    („TASK-803“ und „TASK-804“) je zweimal, der vierte nennt keine Ticketnummer. Wenn verschoben wurde.
    Dann listet die Zuordnungsliste alle vier Abschnitte mit ihren Textzeilen (von–bis, Zeile 1 = führende
    Leerzeile) und den genannten Nummern; nur der erste steht als „zugeordnet“, die übrigen als
    „Einschätzung“ oder „nicht zugeordnet“; die Liste trägt den Vermerk „nicht bestätigt“ und erfindet
    keine Ticketnummer."""
    assert len(TF06_ZEILEN) == 14
    w = baue_welt(tmp_path, zeilen=TF06_ZEILEN)
    assert ausfuehren(w).returncode == 0
    kopf = kopf_aus_anhang(w.lies(w.archiv))
    assert "nicht bestätigt" in kopf
    erwartet = {  # von Hand: Überschrift -> (Textzeilen von-bis)
        "Erster Abschnitt": (2, 5), "Zweiter Abschnitt": (6, 8),
        "Dritter Abschnitt": (9, 12), "Vierter Abschnitt": (13, 14),
    }
    zeilen = {}
    for z in kopf.splitlines():
        if z.startswith("|"):
            zellen = [c.strip() for c in z.strip().strip("|").split("|")]
            for name in erwartet:
                if len(zellen) == 4 and name in zellen[1]:
                    zeilen[name] = zellen
    assert set(zeilen) == set(erwartet), kopf
    for name, (von, bis) in erwartet.items():
        m = re.fullmatch(r"(\d+)\s*[–-]\s*(\d+)", zeilen[name][0])
        assert m, "Spalte Textzeilen unlesbar: %r" % zeilen[name][0]
        assert (int(m.group(1)), int(m.group(2))) == (von, bis), (name, zeilen[name][0])
    assert "TASK-801" in zeilen["Erster Abschnitt"][2] and zeilen["Erster Abschnitt"][3] == "zugeordnet"
    assert "TASK-802" in zeilen["Zweiter Abschnitt"][2]
    assert "TASK-803" in zeilen["Dritter Abschnitt"][2] and "TASK-804" in zeilen["Dritter Abschnitt"][2]
    assert "TASK-" not in zeilen["Vierter Abschnitt"][2]
    for name in ("Zweiter Abschnitt", "Dritter Abschnitt", "Vierter Abschnitt"):
        assert zeilen[name][3] in ("Einschätzung", "nicht zugeordnet"), (name, zeilen[name])
    for name, z in zeilen.items():
        assert AUSGANGSTICKET not in " ".join(z)  # nichts erfunden


# ══════════════════════════════════════════════════════════════════
# TF-07 · AK7
# ══════════════════════════════════════════════════════════════════
def test_tf07_ak7_sicherungen_vor_der_ersten_aenderung_und_nichts_geloescht(welt):
    """TF-07 · AK7 · TASK-116
    Angenommen Übungsdateien und zwei ältere Sicherungen im Sicherungsordner. Wenn das Werkzeug ausführt.
    Dann liegen vor der ersten Änderung zwei Sicherungskopien mit Zeitstempel im Namen und gleicher
    Prüfsumme wie die Originale (die Ausgabe nennt beide Prüfsummen im Protokoll); das Werkzeug löscht keine Sicherung (auch nicht ältere)."""
    (welt.sicherung / "BACKLOG.vor_task116_2026-01-01-0000.md").write_bytes(b"alt 1\n")
    (welt.sicherung / "BACKLOG-ARCHIVE.vor_task116_2026-01-01-0000.md").write_bytes(b"alt 2\n")
    ordner_vorher = sicherungsdateien(welt)
    p = ausfuehren(welt, env={"T116_ABBRUCH_NACH": "sicherung"})
    assert p.returncode == 99, p.alles
    assert welt.lies(welt.backlog) == welt.backlog0 and welt.lies(welt.archiv) == welt.archiv0
    neu = [n for n in sicherungsdateien(welt) if n not in ordner_vorher]
    b = [n for n in neu if re.fullmatch(r"BACKLOG\.vor_task116_\d{4}-\d{2}-\d{2}-\d{4}\.md", n)]
    a = [n for n in neu if re.fullmatch(r"BACKLOG-ARCHIVE\.vor_task116_\d{4}-\d{2}-\d{2}-\d{4}\.md", n)]
    assert len(b) == 1 and len(a) == 1, neu
    assert md5((welt.sicherung / b[0]).read_bytes()) == md5(welt.backlog0)
    assert md5((welt.sicherung / a[0]).read_bytes()) == md5(welt.archiv0)
    # Protokoll: die Ausgabe nennt die Prüfsummen beider Sicherungen
    assert p.kv.get("SICHERUNG_BACKLOG_MD5") == md5(welt.backlog0), p.alles
    assert p.kv.get("SICHERUNG_ARCHIV_MD5") == md5(welt.archiv0), p.alles
    q = ausfuehren(welt)
    assert q.returncode == 0, q.alles
    for n in ordner_vorher + b + a:
        assert (welt.sicherung / n).exists(), "Sicherung gelöscht: " + n


# ══════════════════════════════════════════════════════════════════
# TF-08 · AK8
# ══════════════════════════════════════════════════════════════════
def test_tf08_ak8_jede_karte_in_derselben_spalte_und_karte_zeigt_nur_beschreibung(welt):
    """TF-08 · AK8 · TASK-116
    Angenommen Übungsdateien mit Tickets in verschiedenen Spalten, darunter zwei Archivtickets ohne
    Status-Feld. Wenn verschoben wurde. Dann steht jede Karte in derselben Spalte wie vorher (Spalten von
    Hand erwartet); die Karte des Ausgangstickets zeigt nur ihre Beschreibung."""
    vorher = pruefen(welt)
    assert spalten(vorher) == SPALTEN_VON_HAND, vorher.alles
    karten_vorher = kanban_karten(welt.lies(welt.backlog), welt.lies(welt.archiv))
    assert {k: v["lane"] for k, v in karten_vorher.items()} == SPALTEN_VON_HAND
    # Vorbedingung: vor dem Verschieben steht der fremde Text im Backlog hinter dem Ausgangsticket
    assert "## Analyse (2026-08-10)" in welt.lies(welt.backlog).decode("utf-8")
    assert karten_vorher[AUSGANGSTICKET]["body"].rstrip().endswith("---")
    assert ausfuehren(welt).returncode == 0
    nachher = pruefen(welt)
    assert spalten(nachher) == SPALTEN_VON_HAND, nachher.alles
    karten = kanban_karten(welt.lies(welt.backlog), welt.lies(welt.archiv))
    assert {k: v["lane"] for k, v in karten.items()} == SPALTEN_VON_HAND
    assert set(karten) == set(karten_vorher)
    body = karten[AUSGANGSTICKET]["body"]
    # Die Archiv-Überschrift der Übungswelt hängt beim Zusammenfügen am Körper des letzten Backlog-Tickets
    # (schon vor dem Verschieben, unabhängig vom Werkzeug); sie ist kein Teil des Tickettexts.
    zeilen = body.rstrip().split("\n")
    if zeilen and zeilen[-1].strip() == "# Archiv (Übung)":
        zeilen = zeilen[:-1]
    assert "\n".join(zeilen).rstrip().endswith("---"), body
    # Eigener Text bleibt, der verschobene fremde Text ist vollständig aus dem Körper verschwunden
    assert "Eigener Text des Ausgangstickets." in body
    assert "**Quelle:** Übung (Prüfbericht)." in body
    for marke in ("Analyse (2026-08-10)", "Sicherheitspunkte a bis c", "Example Mapping",
                  "Zwischenstand Schritt 1", "Abschluss (2026-08-11)", "Siehe auch TASK-802"):
        assert marke not in body, marke
    # Alle anderen Karten haben unveränderten Körper
    for tid, k in karten.items():
        if tid != AUSGANGSTICKET:
            assert k["body"] == karten_vorher[tid]["body"], tid


def test_tf08_ak8_gegenprobe_spaltenwechsel_macht_messung_rot(welt):
    """TF-08 · AK8 · TASK-116 · Gegenprobe
    Wechselt in der Probe eine Karte die Spalte, meldet die Messung Rot und nennt die Karte."""
    b0, a0 = kopie_vorher(welt)
    assert ausfuehren(welt).returncode == 0
    t = welt.lies(welt.backlog).decode("utf-8").replace("| **Status** | In Analysis |", "| **Status** | In Test |")
    welt.backlog.write_bytes(t.encode("utf-8"))
    p = nachweis(welt, b0, a0)
    assert p.returncode == 1
    assert p.kv.get("NACHWEIS") == "rot"
    assert "TASK-901" in p.alles


# ══════════════════════════════════════════════════════════════════
# TF-09 · AK9
# ══════════════════════════════════════════════════════════════════
def test_tf09_ak9_fremde_aenderung_zwischen_pruefung_und_schreiben_verhindert_schreiben(welt):
    """TF-09 · AK9 · TASK-116
    Angenommen die Übungsdatei des Backlogs wird zwischen Prüfung und Schreiben von außen um eine Zeile
    ergänzt. Wenn das Werkzeug schreiben will. Dann schreibt es nichts, beide Dateien sind byte-gleich
    zum Zustand nach der fremden Ergänzung, und die Meldung nennt die Veränderung."""
    haken = welt.tmp / "fremder_schreiber.py"
    haken.write_text(
        "import sys\nwith open(%r, 'ab') as f:\n    f.write('Fremde Ergänzung\\n'.encode('utf-8'))\n" % str(welt.backlog),
        encoding="utf-8",
    )
    p = ausfuehren(welt, env={"T116_HAKEN_NACH_PRUEFUNG": str(haken)})
    assert p.returncode == 1, p.alles
    assert p.kv.get("ERGEBNIS") == "abgebrochen"
    assert "veränder" in p.alles.lower()
    assert welt.lies(welt.backlog) == welt.backlog0 + "Fremde Ergänzung\n".encode("utf-8")
    assert welt.lies(welt.archiv) == welt.archiv0


# ══════════════════════════════════════════════════════════════════
# TF-10 · AK10
# ══════════════════════════════════════════════════════════════════
def test_tf10_ak10_rueckweg_ueber_die_sicherungen(welt):
    """TF-10 · AK10 · TASK-116
    Angenommen verschoben wurde. Wenn die Sicherungen zurückgespielt werden. Dann haben beide Dateien
    wieder die Prüfsummen von vorher (und das Werkzeug erkennt den Zustand wieder als „noch zu tun“)."""
    soll_b, soll_a = md5(welt.backlog0), md5(welt.archiv0)
    assert ausfuehren(welt).returncode == 0
    assert md5(welt.lies(welt.backlog)) != soll_b
    for n in sicherungsdateien(welt):
        ziel = welt.backlog if n.startswith("BACKLOG.vor_") else welt.archiv
        ziel.write_bytes((welt.sicherung / n).read_bytes())
    assert md5(welt.lies(welt.backlog)) == soll_b
    assert md5(welt.lies(welt.archiv)) == soll_a
    assert pruefen(welt).kv.get("ZUSTAND") == "noch zu tun"


# ══════════════════════════════════════════════════════════════════
# TF-11 · AK11
# ══════════════════════════════════════════════════════════════════
def _nichts_veraendert(welt, p):
    assert p.returncode == 1, p.alles
    assert p.kv.get("ERGEBNIS") == "abgebrochen", p.alles
    assert p.kv.get("GRUND"), "Meldung ohne Grund: " + p.alles
    assert welt.lies(welt.backlog) == welt.backlog0
    assert welt.lies(welt.archiv) == welt.archiv0


def test_tf11a_ak11_text_fehlt_ganz(tmp_path):
    """TF-11a · AK11 · TASK-116
    Der fremde Text fehlt ganz (Backlog endet mit dem Trennstrich, im Archiv liegt kein Anhang). Dann sind
    beide Dateien unverändert und die Meldung nennt den Grund."""
    w = baue_welt(tmp_path)
    w.backlog.write_bytes(w.eigen)
    w.backlog0 = w.eigen
    _nichts_veraendert(w, ausfuehren(w))


def test_tf11b_ak11_text_kommt_mehrfach_vor(tmp_path):
    """TF-11b · AK11 · TASK-116
    Das Ausgangsticket kommt zweimal im Backlog vor (Fundort nicht eindeutig). Dann sind beide Dateien
    unverändert und die Meldung nennt „mehrfach“ als Grund."""
    w = baue_welt(tmp_path)
    ausgang = w.eigen.decode("utf-8")
    block = ausgang[ausgang.index("### %s" % AUSGANGSTICKET):]
    doppelt = (ausgang.replace("### %s" % AUSGANGSTICKET, block + "\n### %s" % AUSGANGSTICKET, 1)).encode("utf-8") + w.text
    w.backlog.write_bytes(doppelt)
    w.backlog0 = doppelt
    p = ausfuehren(w)
    _nichts_veraendert(w, p)
    assert "mehrfach" in p.alles.lower()


def test_tf11c_ak11_abweichende_zeile_wird_mit_nummer_genannt_ohne_inhalt(welt):
    """TF-11c · AK11 · TASK-116
    Eine Zeile des Textes weicht von der erwarteten Fassung ab (Zeile 7). Dann sind beide Dateien
    unverändert; die Meldung nennt die Nummer der ersten abweichenden Zeile, nicht deren Inhalt."""
    erwartet = list(FREMD_ZEILEN)
    erwartet[6] = "- Regel: ANDERER-INHALT-4711"
    datei = welt.tmp / "erwartet.txt"
    datei.write_bytes(fremd_text(erwartet))
    p = ausfuehren(welt, "--erwartet-text", str(datei))
    _nichts_veraendert(welt, p)
    assert p.kv.get("ABWEICHENDE_ZEILE") == "7", p.alles
    assert "nichts geht verloren" not in p.alles
    assert "ANDERER-INHALT-4711" not in p.alles


def test_tf11d_ak11_datei_nicht_beschreibbar_oder_sicherung_nicht_anlegbar(welt):
    """TF-11d · AK11 · TASK-116
    Das Archiv ist schreibgeschützt. Dann sind beide Dateien unverändert und die Meldung nennt den Grund.
    Wo Schreibschutz technisch nicht herstellbar ist (z. B. als Administrator), gilt ersatzweise: der
    Sicherungsordner ist nicht anlegbar (liegt unterhalb einer gewöhnlichen Datei) — im Protokoll benannt."""
    os.chmod(str(welt.archiv), stat.S_IREAD)
    if os.access(str(welt.archiv), os.W_OK):
        os.chmod(str(welt.archiv), stat.S_IREAD | stat.S_IWRITE)
        datei = welt.tmp / "gewoehnliche_datei"
        datei.write_bytes(b"x")
        p = ausfuehren(welt, sicherung=datei / "unterordner")
    else:
        try:
            p = ausfuehren(welt)
        finally:
            os.chmod(str(welt.archiv), stat.S_IREAD | stat.S_IWRITE)
    _nichts_veraendert(welt, p)


def test_tf11e_ak11_abweichende_zeilenzahl(welt):
    """TF-11e · AK11 · TASK-116
    Die Zeilenzahl des Textes weicht von der erwarteten ab (erwartet 99, tatsächlich 14). Dann sind beide
    Dateien unverändert und die Meldung nennt „Zeilen“ als Grund."""
    p = ausfuehren(welt, "--erwartet-zeilen", "99")
    _nichts_veraendert(welt, p)
    assert "zeilen" in p.kv["GRUND"].lower(), p.alles


def test_tf11f_ak11_abweichende_pruefsumme(welt):
    """TF-11f · AK11 · TASK-116
    Die Prüfsumme des Textes weicht von der erwarteten ab. Dann sind beide Dateien unverändert und die
    Meldung nennt „Prüfsumme“ als Grund. Gegenstück: mit der richtigen Prüfsumme und Zeilenzahl läuft der
    Vorgang durch."""
    p = ausfuehren(welt, "--erwartet-md5", "0" * 32)
    _nichts_veraendert(welt, p)
    assert "prüfsumme" in p.kv["GRUND"].lower(), p.alles
    q = ausfuehren(welt, "--erwartet-md5", md5(welt.text), "--erwartet-zeilen", str(FREMD_ANZAHL_ZEILEN))
    assert q.returncode == 0, q.alles


def test_tf11g_ak11_backlog_nicht_beschreibbar_oder_sicherung_nicht_anlegbar(welt):
    """TF-11g · AK11 · TASK-116
    Der Backlog ist schreibgeschützt. Dann sind beide Dateien unverändert und die Meldung nennt den Grund.
    Wo Schreibschutz technisch nicht herstellbar ist (z. B. als Administrator), gilt ersatzweise: der
    Sicherungsordner ist nicht anlegbar — im Protokoll benannt."""
    os.chmod(str(welt.backlog), stat.S_IREAD)
    if os.access(str(welt.backlog), os.W_OK):
        os.chmod(str(welt.backlog), stat.S_IREAD | stat.S_IWRITE)
        datei = welt.tmp / "gewoehnliche_datei"
        datei.write_bytes(b"x")
        p = ausfuehren(welt, sicherung=datei / "unterordner")
    else:
        try:
            p = ausfuehren(welt)
        finally:
            os.chmod(str(welt.backlog), stat.S_IREAD | stat.S_IWRITE)
    _nichts_veraendert(welt, p)


# ══════════════════════════════════════════════════════════════════
# TF-12 · AK12
# ══════════════════════════════════════════════════════════════════
def _bericht_welt(tmp, mit_fund):
    kopf = "# Backlog (Übung)\n\n## Offene Tickets\n\n" + _ticket("TASK-901", "Erstes", "In Analysis")
    if mit_fund:
        zusatz = "## Analyse (TASK-950)\n\nKörper eines längst erledigten Tickets, der Kopf liegt nur im Archiv.\n"
    else:
        zusatz = "## Analyse (TASK-901)\n\nGehört zum aktiven Ticket TASK-901.\n"
    archiv = ARCHIV + "\n### TASK-950 · Nur der Kopf im Archiv `[x]`\n\n| Feld | Wert |\n|------|------|\n| **Status** | Done |\n\n---\n"
    w = baue_welt(tmp, eigen=kopf + zusatz)
    w.backlog.write_bytes((kopf + zusatz).encode("utf-8"))
    w.archiv.write_bytes(archiv.encode("utf-8"))
    w.backlog0, w.archiv0 = w.lies(w.backlog), w.lies(w.archiv)
    zeile = (kopf + zusatz).split("\n").index(zusatz.split("\n")[0]) + 1
    return w, zeile


def test_tf12_ak12_weiterer_verwaister_abschnitt_wird_gemeldet_nicht_verschoben(tmp_path):
    """TF-12 · AK12 · TASK-116
    Angenommen eine Übung mit einem zweiten verwaisten Abschnitt (Ticket-Kopf nur im Archiv, Körper im
    Backlog) hinter einem anderen Ticket. Wenn der Bericht läuft. Dann wird der Fund mit Fundstelle
    gemeldet und nicht verschoben (beide Dateien bleiben byte-gleich)."""
    w, zeile = _bericht_welt(tmp_path, mit_fund=True)
    p = lauf(w, "--bericht")
    assert p.returncode == 0, p.alles
    assert p.kv.get("VERWAISTE_ABSCHNITTE") == "1", p.alles
    fund = [z for z in p.out.splitlines() if z.startswith("FUND")]
    assert len(fund) == 1 and "TASK-950" in fund[0] and str(zeile) in fund[0], p.alles
    assert w.lies(w.backlog) == w.backlog0 and w.lies(w.archiv) == w.archiv0


def test_tf12_ak12_ohne_weiteren_fund_meldet_der_bericht_null(tmp_path):
    """TF-12 · AK12 · TASK-116
    Und in einer Übung ohne weiteren Fund (der Abschnitt gehört zu einem aktiven Ticket) meldet der
    Bericht „0“."""
    w, _ = _bericht_welt(tmp_path, mit_fund=False)
    p = lauf(w, "--bericht")
    assert p.returncode == 0, p.alles
    assert p.kv.get("VERWAISTE_ABSCHNITTE") == "0", p.alles
    assert not [z for z in p.out.splitlines() if z.startswith("FUND")]


# ══════════════════════════════════════════════════════════════════
# TF-13 · AK13
# ══════════════════════════════════════════════════════════════════
def test_tf13_ak13_text_wird_am_inhalt_gefunden_nicht_an_zeilennummern(tmp_path):
    """TF-13 · AK13 · TASK-116
    Angenommen dasselbe Übungsbacklog, aber mit 300 zusätzlichen Zeilen weiter oben. Wenn verschoben
    wird. Dann wird derselbe Text gefunden und verschoben, ohne dass eine Zeilennummer angegeben wurde."""
    w = baue_welt(tmp_path, fueller=300)
    assert zeilenzahl(w.backlog0) > 300 + 14
    p = ausfuehren(w)
    assert p.returncode == 0, p.alles
    assert text_aus_anhang(w.lies(w.archiv)) == w.text
    assert w.lies(w.backlog) == w.eigen


# ══════════════════════════════════════════════════════════════════
# TF-14 · AK14
# ══════════════════════════════════════════════════════════════════
def test_tf14_ak14_abbruch_nach_archiv_text_in_beiden_dateien_nie_in_keiner(welt):
    """TF-14 · AK14 · TASK-116
    Angenommen der Vorgang wird nach dem Schreiben des Archivs, vor dem Kürzen des Backlogs abgebrochen.
    Dann steht der Text im Archiv und noch im Backlog (nie in keiner); das Archiv ist vollständig und
    lesbar (Anhang mit Endemarke, echte Backlog-Prüfung sauber)."""
    p = ausfuehren(welt, env={"T116_ABBRUCH_NACH": "archiv"})
    assert p.returncode == 99, p.alles
    assert welt.lies(welt.backlog) == welt.backlog0
    archiv = welt.lies(welt.archiv)
    assert archiv.startswith(welt.archiv0) and archiv != welt.archiv0
    assert text_aus_anhang(archiv) == welt.text
    assert anhang(archiv).rstrip().endswith(ANHANG_ENDE)
    rc, ausgabe = lint(welt.backlog)
    assert rc == 0, ausgabe


def test_tf14_ak14_abbruch_vor_dem_ersten_schreiben_laesst_beide_dateien_unveraendert(welt):
    """TF-14 · AK14 · TASK-116 · zweiter Fall
    Abbruch vor dem ersten Schreiben (nach der Sicherung) → beide Dateien unverändert."""
    p = ausfuehren(welt, env={"T116_ABBRUCH_NACH": "sicherung"})
    assert p.returncode == 99, p.alles
    assert welt.lies(welt.backlog) == welt.backlog0
    assert welt.lies(welt.archiv) == welt.archiv0


# ══════════════════════════════════════════════════════════════════
# TF-15 · AK15
# ══════════════════════════════════════════════════════════════════
def test_tf15_ak15_zweiter_lauf_meldet_bereits_erledigt_und_aendert_nichts(welt):
    """TF-15 · AK15 · TASK-116
    Angenommen verschoben wurde. Wenn das Werkzeug erneut läuft. Dann meldet es „bereits erledigt“ und
    beide Dateien bleiben byte-gleich."""
    assert ausfuehren(welt).returncode == 0
    b1, a1 = welt.lies(welt.backlog), welt.lies(welt.archiv)
    ordner = sicherungsdateien(welt)
    p = ausfuehren(welt)
    assert p.returncode == 0, p.alles
    assert p.kv.get("ERGEBNIS") == "bereits erledigt", p.alles
    assert welt.lies(welt.backlog) == b1 and welt.lies(welt.archiv) == a1
    assert sicherungsdateien(welt) == ordner


def test_tf15_ak15_nach_abbruch_kuerzt_der_naechste_lauf_nur_den_backlog(welt):
    """TF-15 · AK15 · TASK-116
    Und nach dem Abbruch aus TF-14 kürzt der nächste Lauf nur den Backlog, ohne zweiten Anhang; das Archiv
    enthält genau einen Anhang und bleibt byte-gleich zum Zustand nach dem Abbruch."""
    assert ausfuehren(welt, env={"T116_ABBRUCH_NACH": "archiv"}).returncode == 99
    archiv_nach_abbruch = welt.lies(welt.archiv)
    assert pruefen(welt).kv.get("ZUSTAND") == "Zwischenzustand"
    p = ausfuehren(welt)
    assert p.returncode == 0, p.alles
    assert welt.lies(welt.backlog) == welt.eigen
    assert welt.lies(welt.archiv) == archiv_nach_abbruch
    assert welt.lies(welt.archiv).decode("utf-8").count(ANHANG_BEGINN) == 1


# ══════════════════════════════════════════════════════════════════
# TF-16 · AK16
# ══════════════════════════════════════════════════════════════════
def test_tf16_ak16_anhang_hat_kopf_hinweise_und_endemarke(welt):
    """TF-16 · AK16 · TASK-116
    Angenommen verschoben wurde. Dann beginnt der Anhang mit Überschrift (Datum, Herkunft TASK-116),
    nennt Zeilenzahl, Prüfsumme, „unverändert übernommen“, „Zuordnung ist Einschätzung“ und die Warnung
    zu TASK-110, und endet mit einer Endemarke; der Text zwischen Kopf und Endemarke hat die Prüfsumme
    von vorher."""
    soll = md5(welt.text)
    assert ausfuehren(welt).returncode == 0
    archiv = welt.lies(welt.archiv)
    a = anhang(archiv)
    kopf = kopf_aus_anhang(archiv)
    assert re.search(r"^## .*TASK-116.*\d{4}-\d{2}-\d{2}", kopf, re.M) or (
        re.search(r"^## .*TASK-116", kopf, re.M) and re.search(r"\d{4}-\d{2}-\d{2}", kopf))
    assert AUSGANGSTICKET in kopf
    assert re.search(r"^Zeilen: %d$" % FREMD_ANZAHL_ZEILEN, kopf, re.M), kopf
    assert re.search(r"^Prüfsumme \(MD5\): %s$" % soll, kopf, re.M), kopf
    assert "unverändert übernommen" in kopf
    assert "Zuordnung ist Einschätzung" in kopf
    assert "TASK-110" in kopf and "Auslagerungswerkzeug" in kopf and "überschreibt" in kopf
    assert a.rstrip().endswith(ANHANG_ENDE)
    assert TEXT_ENDE in a
    assert md5(text_aus_anhang(archiv)) == soll


# ══════════════════════════════════════════════════════════════════
# TF-17 · AK17
# ══════════════════════════════════════════════════════════════════
def _zustand_herstellen(welt, zustand):
    if zustand == "Zwischenzustand":
        assert ausfuehren(welt, env={"T116_ABBRUCH_NACH": "archiv"}).returncode == 99
    elif zustand == "erledigt":
        assert ausfuehren(welt).returncode == 0


@pytest.mark.parametrize("zustand", ["noch zu tun", "Zwischenzustand", "erledigt"])
def test_tf17_ak17_pruefmodus_nennt_zustand_und_messwerte_und_schreibt_nichts(welt, zustand):
    """TF-17 · AK17 · TASK-116
    Angenommen Übungsdateien in den drei Zuständen „noch zu tun“, „Zwischenzustand“, „erledigt“. Wenn nur
    geprüft wird. Dann nennt das Werkzeug den richtigen Zustand mit allen Messwerten (Prüfsumme, Zeilen-
    und Zeichensumme, Ticketzahl, Spalten, Ergebnis der Backlog-Prüfung), beide Dateien sind danach
    byte-gleich zu vorher, und der Satz der Ausgabe-Schlüssel ist in jedem Zustand derselbe."""
    _zustand_herstellen(welt, zustand)
    b, a = welt.lies(welt.backlog), welt.lies(welt.archiv)
    ordner = sicherungsdateien(welt)
    p = pruefen(welt)
    assert p.returncode == 0, p.alles
    assert p.kv.get("ZUSTAND") == zustand, p.alles
    for schluessel in ("TEXT_MD5", "TEXT_ZEILEN", "TEXT_ZEICHEN", "SUMME_ZEILEN", "SUMME_ZEICHEN",
                       "TICKETS", "DOPPELTE_IDS", "LINT_FEHLER", "LINT_WARNUNGEN"):
        assert schluessel in p.kv, (schluessel, p.alles)
    assert p.kv["TEXT_MD5"] == md5(welt.text)
    assert len(spalten(p)) == ANZAHL_TICKETS
    assert welt.lies(welt.backlog) == b and welt.lies(welt.archiv) == a
    assert sicherungsdateien(welt) == ordner
    referenz = pruefen(baue_welt(_frische_welt(welt)))
    assert sorted(k for k in p.kv if not k.startswith("SPALTE ")) == sorted(k for k in referenz.kv if not k.startswith("SPALTE "))


def _frische_welt(welt):
    sub = welt.tmp / "referenz"
    sub.mkdir()
    return sub


# ══════════════════════════════════════════════════════════════════
# TF-18 · AK18
# ══════════════════════════════════════════════════════════════════
def test_tf18_ak18_geheimnis_erscheint_nie_in_ausgabe_oder_protokoll(tmp_path):
    """TF-18 · AK18 · TASK-116
    Angenommen ein Übungstext enthält eine Zeile mit „Passwort: abc123xyz“. Wenn das Werkzeug verschiebt,
    prüft und bei einer Abweichung abbricht. Dann kommt „abc123xyz“ in keiner Ausgabe und in keinem
    Protokoll vor (die Sicherungs- und Datenkopien selbst sind ausgenommen)."""
    zeilen = list(FREMD_ZEILEN) + ["Passwort: %s" % GEHEIMNIS]
    w = baue_welt(tmp_path, zeilen=zeilen)
    erwartet = list(zeilen)
    erwartet[-1] = "Passwort: anders"
    ek = w.tmp / "erwartet.txt"
    ek.write_bytes(fremd_text(erwartet))
    ausgaben = []
    ausgaben.append(pruefen(w))
    abbruch = ausfuehren(w, "--erwartet-text", str(ek))
    assert abbruch.returncode == 1, abbruch.alles
    ausgaben.append(abbruch)
    ausgaben.append(ausfuehren(w))
    ausgaben.append(pruefen(w))
    for p in ausgaben:
        assert GEHEIMNIS not in p.alles
    kopien = {w.backlog.name, w.archiv.name, "erwartet.txt"}
    for pfad in w.tmp.rglob("*"):
        if pfad.is_file() and pfad.name not in kopien and not re.match(r"(BACKLOG|BACKLOG-ARCHIVE)\.vor_task116_", pfad.name):
            assert GEHEIMNIS.encode() not in pfad.read_bytes(), "Geheimnis in Protokolldatei: %s" % pfad.name


# ══════════════════════════════════════════════════════════════════
# TF-19 · AK19
# ══════════════════════════════════════════════════════════════════
def test_tf19_ak19_kopfartige_zeile_im_text_bricht_vor_jeder_aenderung_ab(tmp_path):
    """TF-19 · AK19 · TASK-116
    Angenommen ein Übungstext enthält eine Zeile, die wie ein Ticket-Kopf aussieht. Wenn das Werkzeug
    ausführt. Dann bricht es vor jeder Änderung ab, nennt die Zeilennummer (in der Backlog-Datei), beide
    Dateien unverändert."""
    zeilen = list(FREMD_ZEILEN)
    zeilen.insert(6, "### TASK-777 · Sieht aus wie ein Ticket-Kopf")
    w = baue_welt(tmp_path, zeilen=zeilen)
    erwartete_zeile = zeilenzahl(w.eigen) + 7
    p = ausfuehren(w)
    _nichts_veraendert(w, p)
    assert p.kv.get("KOPFARTIGE_ZEILE") == str(erwartete_zeile), p.alles


# ══════════════════════════════════════════════════════════════════
# TF-20 · AK5 und AK8 (Brücke zu den echten Regeln)
# ══════════════════════════════════════════════════════════════════
def test_tf20_ak5_echte_backlog_pruefung_meldet_nachher_dasselbe_wie_vorher(welt):
    """TF-20 · AK5 · TASK-116
    Angenommen die Übungsdateien nach dem Verschieben. Wenn die echte Backlog-Prüfung auf sie angewandt
    wird. Dann meldet sie dasselbe wie vor dem Verschieben (21 Tickets, 0 Fehler, 0 Warnungen)."""
    rc0, aus0 = lint(welt.backlog)
    assert rc0 == 0 and "%d Tickets · 0 Fehler · 0 Warnungen" % ANZAHL_TICKETS in aus0, aus0
    assert ausfuehren(welt).returncode == 0
    rc1, aus1 = lint(welt.backlog)
    assert rc1 == 0 and aus1 == aus0, aus1


def test_tf20_ak8_echte_spaltenregel_des_boards_ordnet_nachher_gleich_zu_wie_vorher(welt):
    """TF-20 · AK8 · TASK-116
    Angenommen die Übungsdateien nach dem Verschieben. Wenn die echte Spaltenregel des Boards auf sie
    angewandt wird. Dann ordnet sie jede Karte derselben Spalte zu wie vor dem Verschieben."""
    vorher = {k: v["lane"] for k, v in kanban_karten(welt.backlog0, welt.archiv0).items()}
    assert vorher == SPALTEN_VON_HAND
    assert ausfuehren(welt).returncode == 0
    nachher = {k: v["lane"] for k, v in kanban_karten(welt.lies(welt.backlog), welt.lies(welt.archiv)).items()}
    assert nachher == vorher
