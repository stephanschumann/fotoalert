#!/usr/bin/env python3
"""
backlog_verschieben.py (TASK-116) - verwaisten Text unter einem Ticket ins Archiv verschieben.

Verschiebt den Text, der in BACKLOG.md hinter dem Trennstrich "---" unter der "**Quelle:**"-Zeile des
Ausgangstickets bis zum Dateiende steht, unverändert als Anhang ans Ende von BACKLOG-ARCHIVE.md.
Der Fundort wird am Inhalt erkannt, nie an Zeilennummern. Kein Git, nur Standardbibliothek.

Aufruf:
  python tools/backlog_verschieben.py --backlog B --archiv A --ticket TASK-108 --sicherung DIR MODUS
MODUS:
  --pruefen    misst und meldet den Zustand, schreibt nichts
  --ausfuehren sichert beide Dateien, haengt den Anhang ans Archiv, prueft, kuerzt dann den Backlog
  --nachweis   (mit --vorher-backlog/--vorher-archiv) vergleicht vorher/nachher, schreibt nichts
  --bericht    meldet weitere verwaiste Abschnitte, schreibt nichts
Zusaetze: --erwartet-md5 X, --erwartet-zeilen N, --erwartet-text DATEI

Ausgabe: Zeilen "SCHLUESSEL=Wert". Es werden nie Zeileninhalte ausgegeben (nur Zahlen, Prüfsummen,
Zeilennummern, Ticketnummern). Rueckgabewert 0 = in Ordnung, 1 = abgebrochen / rot.
Pruefhaken (nur fuer Tests): T116_ABBRUCH_NACH=sicherung|archiv (Ende mit 99),
T116_HAKEN_NACH_PRUEFUNG=<Skript> (laeuft zwischen Pruefung und Schreiben).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "lint_backlog.py")
KANBAN = os.path.join(HERE, "gen_kanban.py")

ANHANG_BEGINN = "<!-- TASK-116-ANHANG-BEGINN -->"
ANHANG_ENDE = "<!-- TASK-116-ANHANG-ENDE -->"
TEXT_BEGINN = "<!-- TASK-116-TEXT-BEGINN -->"
TEXT_ENDE = "<!-- TASK-116-TEXT-ENDE -->"
MARKEN = (ANHANG_BEGINN, ANHANG_ENDE, TEXT_BEGINN, TEXT_ENDE)

ID_RE = re.compile(r'^###\s+(~~)?\s*([A-Z]+-\d+[a-z]?)\s*[·:\-]')
TICKET_RE = re.compile(r'\b([A-Z]{2,}-\d+)\b')
LINT_RE = re.compile(r'(\d+) Tickets · (\d+) Fehler · (\d+) Warnungen')


class Abbruch(Exception):
    def __init__(self, grund, extra=None):
        Exception.__init__(self, grund)
        self.grund = grund
        self.extra = extra or {}


# ---------------------------------------------------------------- Hilfen
def ausgabe(k, v):
    sys.stdout.write("%s=%s\n" % (k, v))
    sys.stdout.flush()


def md5(b):
    return hashlib.md5(b).hexdigest()


def zeilenzahl(b):
    return b.count(b"\n") + (1 if b and not b.endswith(b"\n") else 0)


def zeichen(b):
    return len(b.decode("utf-8", "replace"))


def lies(pfad):
    with open(pfad, "rb") as f:
        return f.read()


def zeilen_von(b):
    z = b.split(b"\n")
    if z and z[-1] == b"":
        z.pop()
    return z


def ticket_koepfe(text_bytes):
    """Liste (Zeilenindex, ID) aller Ticket-Koepfe."""
    out = []
    for i, z in enumerate(text_bytes.split(b"\n")):
        if z.startswith(b"###"):
            m = ID_RE.match(z.decode("utf-8", "replace"))
            if m:
                out.append((i, m.group(2)))
    return out


def bloecke(b):
    """ID -> Liste der Bloecke (von Kopf bis vor die naechste '### '/'## '-Zeile, hinten ohne Umbrueche)."""
    erg, akt, tid = {}, [], None
    for z in b.decode("utf-8", "replace").split("\n"):
        m = ID_RE.match(z)
        if z.startswith("### ") or z.startswith("## "):
            if tid:
                erg.setdefault(tid, []).append("\n".join(akt).rstrip("\n"))
            akt, tid = [], None
        if m:
            tid = m.group(2)
        if tid:
            akt.append(z)
    if tid:
        erg.setdefault(tid, []).append("\n".join(akt).rstrip("\n"))
    return erg


# ---------------------------------------------------------------- Text finden
def finde_text_start(b, ticket):
    """Byte-Offset, ab dem der Text beginnt (Zeile nach dem Trennstrich unter der Quelle-Zeile)."""
    zeilen = b.split(b"\n")
    offs, o = [], 0
    for z in zeilen:
        offs.append(o)
        o += len(z) + 1
    koepfe = [i for i, tid in ticket_koepfe(b) if tid == ticket]
    if not koepfe:
        raise Abbruch("Ausgangsticket %s im Backlog nicht gefunden" % ticket)
    if len(koepfe) > 1:
        raise Abbruch("Ausgangsticket %s kommt mehrfach im Backlog vor (Fundort nicht eindeutig)" % ticket)
    n = len(zeilen)
    q = None
    for j in range(koepfe[0] + 1, n):
        z = zeilen[j]
        if z.startswith(b"## ") or z.startswith(b"### "):
            break
        if z.startswith(b"**Quelle:**"):
            q = j
            break
    if q is None:
        raise Abbruch("Quelle-Zeile des Ausgangstickets nicht gefunden")
    for j in range(q + 1, n):
        z = zeilen[j]
        if z.strip() == b"---":
            ende = offs[j] + len(z)
            return ende + 1 if ende < len(b) and b[ende:ende + 1] == b"\n" else min(ende, len(b))
        if z.startswith(b"## ") or z.startswith(b"### "):
            break
    raise Abbruch("Trennstrich unter der Quelle-Zeile des Ausgangstickets nicht gefunden")


def anhang_lesen(a):
    """None, wenn kein Anhang; sonst dict(text=bytes, beginn=Byte-Offset der Anfangsmarke)."""
    t = a.decode("utf-8", "replace")
    if t.count(ANHANG_BEGINN) == 0:
        return None
    if t.count(ANHANG_BEGINN) > 1:
        raise Abbruch("Archiv enthaelt mehrere Anhänge (Anfangsmarke mehrfach)")
    teil = a[a.index(ANHANG_BEGINN.encode()):]
    sb = TEXT_BEGINN.encode() + b"\n"
    se = b"\n" + TEXT_ENDE.encode()
    if sb not in teil or se not in teil or ANHANG_ENDE.encode() not in teil:
        raise Abbruch("Anhang im Archiv unvollständig (Marke fehlt)")
    s = teil.index(sb) + len(sb)
    e = teil.index(se, s)
    kopf = teil[:teil.index(sb)].decode("utf-8", "replace")
    return {"text": teil[s:e], "kopf": kopf, "beginn": a.index(ANHANG_BEGINN.encode())}


# ---------------------------------------------------------------- Messungen
def _modul_kanban():
    spec = importlib.util.spec_from_file_location("gen_kanban_t116_werkzeug", KANBAN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def messen(b, a, b_bloecke=None):
    """Misst Backlog+Archiv mit den echten Regeln (Backlog-Pruefung, Board-Spaltenregel)."""
    erg = {"sum_z": zeilenzahl(b) + zeilenzahl(a),
           "sum_c": len(b.decode("utf-8", "replace")) + len(a.decode("utf-8", "replace"))}
    ids = [tid for _, tid in ticket_koepfe(b)] + [tid for _, tid in ticket_koepfe(a)]
    erg["doppelte"] = sorted(set(i for i in ids if ids.count(i) > 1))
    erg["tickets"], erg["fehler"], erg["warnungen"] = "unbekannt", "unbekannt", "unbekannt"
    tmp = tempfile.mkdtemp(prefix="t116_")
    try:
        with open(os.path.join(tmp, "BACKLOG.md"), "wb") as f:
            f.write(b)
        with open(os.path.join(tmp, "BACKLOG-ARCHIVE.md"), "wb") as f:
            f.write(a)
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        p = subprocess.run([sys.executable, LINT, os.path.join(tmp, "BACKLOG.md")], capture_output=True,
                           timeout=300, env=env, cwd=tmp)
        m = LINT_RE.search(p.stdout.decode("utf-8", "replace"))
        if m:
            erg["tickets"], erg["fehler"], erg["warnungen"] = m.group(1), m.group(2), m.group(3)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    lanes = {}
    try:
        mod = _modul_kanban()
        text = b.decode("utf-8") + "\n\n" + a.decode("utf-8")
        for t in mod.parse_backlog(text):
            lanes.setdefault(t["id"], t["lane"])
    except Exception:
        lanes = {}
    erg["lanes"] = lanes
    erg["bloecke"] = dict(bloecke(b if b_bloecke is None else b_bloecke))
    for k, v in bloecke(a).items():
        erg["bloecke"].setdefault(k, []).extend(v)
    return erg


def vergleiche(vor, nach):
    """Liste von Abweichungen (nur Nummern/Namen) zwischen zwei Messungen."""
    abw = []
    if vor["tickets"] != nach["tickets"]:
        abw.append("Ticketzahl vorher %s, nachher %s" % (vor["tickets"], nach["tickets"]))
    for d in nach["doppelte"]:
        if d not in vor["doppelte"]:
            abw.append("doppelte Ticketnummer %s" % d)
    if (vor["fehler"], vor["warnungen"]) != (nach["fehler"], nach["warnungen"]):
        abw.append("Backlog-Pruefung vorher %s Fehler/%s Warnungen, nachher %s/%s"
                   % (vor["fehler"], vor["warnungen"], nach["fehler"], nach["warnungen"]))
    for tid in sorted(set(vor["lanes"]) | set(nach["lanes"])):
        if vor["lanes"].get(tid) != nach["lanes"].get(tid):
            abw.append("Spalte von %s geändert (%s -> %s)" % (tid, vor["lanes"].get(tid), nach["lanes"].get(tid)))
    for tid in sorted(set(vor["bloecke"]) | set(nach["bloecke"])):
        if vor["bloecke"].get(tid) != nach["bloecke"].get(tid):
            abw.append("Ticketblock %s verändert" % tid)
    return abw


def messwerte_ausgeben(m):
    ausgabe("TICKETS", m["tickets"])
    ausgabe("DOPPELTE_IDS", len(m["doppelte"]))
    ausgabe("LINT_FEHLER", m["fehler"])
    ausgabe("LINT_WARNUNGEN", m["warnungen"])
    for tid in sorted(m["lanes"]):
        ausgabe("SPALTE " + tid, m["lanes"][tid])
    ausgabe("SUMME_ZEILEN", m["sum_z"])
    ausgabe("SUMME_ZEICHEN", m["sum_c"])


# ---------------------------------------------------------------- Analyse
def analysiere(b, a, args):
    ts = None
    fehler_text = None
    try:
        ts = finde_text_start(b, args.ticket)
    except Abbruch as e:
        fehler_text = e
    anh = anhang_lesen(a)
    if fehler_text is not None:
        raise fehler_text
    btext = b[ts:]
    if anh is None:
        if not btext:
            raise Abbruch("Text fehlt: unter dem Ausgangsticket steht nichts und im Archiv liegt kein Anhang")
        zustand, text = "noch zu tun", btext
    else:
        if not btext:
            zustand, text = "erledigt", anh["text"]
        elif btext == anh["text"]:
            zustand, text = "Zwischenzustand", btext
        else:
            raise Abbruch("Text im Backlog weicht vom Anhang im Archiv ab (Zustand unklar)")
    return {"ts": ts, "anhang": anh, "text": text, "zustand": zustand}


def erwartungen(text, args):
    if args.erwartet_zeilen is not None and zeilenzahl(text) != args.erwartet_zeilen:
        raise Abbruch("Zeilenzahl des Textes weicht ab (erwartet %d, gefunden %d)"
                      % (args.erwartet_zeilen, zeilenzahl(text)))
    if args.erwartet_md5 is not None and md5(text) != args.erwartet_md5.strip().lower():
        raise Abbruch("Prüfsumme des Textes weicht ab")
    if args.erwartet_text is not None:
        try:
            erw = lies(args.erwartet_text)
        except OSError:
            raise Abbruch("Datei mit dem erwarteten Text nicht lesbar")
        if erw != text:
            ea, ta = erw.split(b"\n"), text.split(b"\n")
            n = 1
            for i in range(min(len(ea), len(ta))):
                if ea[i] != ta[i]:
                    n = i + 1
                    break
            else:
                n = min(len(ea), len(ta)) + 1
            raise Abbruch("Text weicht von der erwarteten Fassung ab", {"ABWEICHENDE_ZEILE": n})


def ausgang_pruefungen(b, text, ts):
    for m in MARKEN:
        if m.encode() in text:
            raise Abbruch("Text enthält eine Anhang-Marke dieses Werkzeugs")
    vorher = b[:ts].count(b"\n")
    for i, z in enumerate(text.split(b"\n")):
        if z.startswith(b"###") and ID_RE.match(z.decode("utf-8", "replace")):
            raise Abbruch("Zeile im Text sieht wie ein Ticket-Kopf aus",
                          {"KOPFARTIGE_ZEILE": vorher + i + 1})


# ---------------------------------------------------------------- Anhang bauen
def zuordnung(text):
    zeilen = zeilen_von(text)
    start = [i for i, z in enumerate(zeilen) if z.startswith(b"## ")]
    reihen = []
    for k, i in enumerate(start):
        ende = (start[k + 1] if k + 1 < len(start) else len(zeilen))  # exklusiv, 0-basiert
        abschnitt = [z.decode("utf-8", "replace") for z in zeilen[i:ende]]
        nennungen = {}
        for z in abschnitt:
            for t in TICKET_RE.findall(z):
                nennungen[t] = nennungen.get(t, 0) + 1
        ueberschrift = abschnitt[0][3:].strip().replace("|", "\\|")
        if not nennungen:
            tickets, urteil = "—", "nicht zugeordnet"
        else:
            tickets = ", ".join("%s (%dx)" % (t, nennungen[t]) for t in sorted(nennungen))
            urteil = "zugeordnet" if sum(1 for v in nennungen.values() if v >= 2) == 1 else "Einschätzung"
        reihen.append("| %d–%d | %s | %s | %s |" % (i + 1, ende, ueberschrift, tickets, urteil))
    return reihen


def anhang_bauen(text, ticket, datum, vorlauf):
    kopf = [
        "## Anhang TASK-116 (Beginn)",
        ANHANG_BEGINN,
        "## Verwaister Text unter %s – verschoben durch TASK-116 am %s" % (ticket, datum),
        "",
        "Herkunft: Backlog, Text direkt unter dem Ticket %s (hinter dem Trennstrich unter der Quelle-Zeile bis"
        " Dateiende), durch TASK-116 ins Archiv verschoben am %s." % (ticket, datum),
        "Zeilen: %d" % zeilenzahl(text),
        "Prüfsumme (MD5): %s" % md5(text),
        "Zeichen: %d" % zeichen(text),
        "",
        "Hinweise:",
        "- Der Text zwischen den Marken TEXT-BEGINN und TEXT-ENDE ist unverändert übernommen (Byte für Byte;"
        " Zeilenzahl und Prüfsumme oben gelten genau für diese Bytes; der eine zusätzliche Zeilenumbruch vor der"
        " Text-Endemarke gehört nicht zum Text).",
        "- Zuordnung ist Einschätzung: Die Liste unten ist nicht bestätigt. \"zugeordnet\" steht nur, wenn ein"
        " Abschnitt genau ein Ticket mindestens zweimal nennt; sonst \"Einschätzung\" oder \"nicht zugeordnet\"."
        " Der Text selbst bleibt davon unberührt.",
        "- Warnung: Das Auslagerungswerkzeug überschreibt bis zur Behebung von TASK-110 das Archiv; ein Lauf"
        " davor würde diesen Anhang entfernen. Bis dahin kein Auslagerungslauf, Sicherung des Archivs aufheben.",
        "",
        "Zuordnungsliste (Textzeile 1 = führende Leerzeile; ein Abschnitt reicht von seiner Überschrift bis vor die"
        " nächste Überschrift):",
        "",
        "| Textzeilen | Überschrift | Genannte Tickets | Einschätzung |",
        "|---|---|---|---|",
    ] + zuordnung(text) + [""]
    teile = [vorlauf, "\n".join(kopf).encode("utf-8"), b"\n", TEXT_BEGINN.encode(), b"\n", text, b"\n",
             TEXT_ENDE.encode(), b"\n", ANHANG_ENDE.encode(), b"\n"]
    return b"".join(teile)


# ---------------------------------------------------------------- Schreiben
def schreibe_ersetzend(pfad, daten):
    d = os.path.dirname(os.path.abspath(pfad))
    tmp = os.path.join(d, "." + os.path.basename(pfad) + ".t116tmp")
    try:
        with open(tmp, "wb") as f:
            f.write(daten)
            f.flush()
            os.fsync(f.fileno())
        try:
            shutil.copymode(pfad, tmp)
        except OSError:
            pass
        os.replace(tmp, pfad)
        return True
    except OSError:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        return False


def archiv_schreiben(pfad, alt, neu):
    if schreibe_ersetzend(pfad, neu):
        return
    with open(pfad, "ab") as f:          # Rueckfall: nur hinten anhaengen
        f.write(neu[len(alt):])
        f.flush()
        os.fsync(f.fileno())


def backlog_schreiben(pfad, neu):
    if schreibe_ersetzend(pfad, neu):
        return
    with open(pfad, "r+b") as f:         # Rueckfall: nur hinten abschneiden
        f.truncate(len(neu))
        f.flush()
        os.fsync(f.fileno())


def sichern(ordner, name, daten, zeit):
    """Legt eine Sicherung an (nie ueberschreiben); gibt die Prüfsumme der Sicherung zurueck."""
    for _ in range(600):
        pfad = os.path.join(ordner, "%s.vor_task116_%s.md" % (name, zeit.strftime("%Y-%m-%d-%H%M")))
        if os.path.exists(pfad):
            if md5(lies(pfad)) == md5(daten):
                return md5(daten)
            zeit = zeit + datetime.timedelta(minutes=1)
            continue
        with open(pfad, "xb") as f:
            f.write(daten)
            f.flush()
            os.fsync(f.fileno())
        if md5(lies(pfad)) != md5(daten):
            raise Abbruch("Sicherungskopie stimmt nicht mit dem Original überein")
        return md5(daten)
    raise Abbruch("Sicherungsname nicht vergebbar")


def haken(name):
    return os.environ.get("T116_ABBRUCH_NACH") == name


# ---------------------------------------------------------------- Modi
def modus_pruefen(args):
    b, a = lies(args.backlog), lies(args.archiv)
    info = analysiere(b, a, args)
    erwartungen(info["text"], args)
    ausgabe("ZUSTAND", info["zustand"])
    ausgabe("TEXT_ZEILEN", zeilenzahl(info["text"]))
    ausgabe("TEXT_ZEICHEN", zeichen(info["text"]))
    ausgabe("TEXT_MD5", md5(info["text"]))
    messwerte_ausgeben(messen(b, a))
    ausgabe("ERGEBNIS", "nur geprueft")
    return 0


def modus_ausfuehren(args):
    b0, a0 = lies(args.backlog), lies(args.archiv)
    info = analysiere(b0, a0, args)
    text = info["text"]
    ausgabe("ZUSTAND", info["zustand"])
    ausgabe("TEXT_ZEILEN", zeilenzahl(text))
    ausgabe("TEXT_ZEICHEN", zeichen(text))
    ausgabe("TEXT_MD5", md5(text))
    if info["zustand"] == "erledigt":
        ausgabe("ERGEBNIS", "bereits erledigt")
        return 0
    erwartungen(text, args)
    if info["zustand"] == "noch zu tun":
        ausgang_pruefungen(b0, text, info["ts"])
    for pfad in (args.backlog, args.archiv):
        if not os.access(pfad, os.W_OK):
            raise Abbruch("Datei nicht beschreibbar: %s" % os.path.basename(pfad))
    datum = datetime.date.today().strftime("%Y-%m-%d")
    # neuen Stand getrennt erzeugen
    if info["zustand"] == "noch zu tun":
        vorlauf = b"" if a0.endswith(b"\n\n") else (b"\n" if a0.endswith(b"\n") else b"\n\n")
        neu_a = a0 + anhang_bauen(text, args.ticket, datum, vorlauf)
    else:
        neu_a = a0
    neu_b = b0[:info["ts"]]
    # Vorab-Prüfung des Ergebnisses (Stand im Speicher, mit den echten Regeln)
    vor = messen(b0, a0, b0[:info["ts"]])
    sim = messen(neu_b, neu_a)
    abw = vergleiche(vor, sim)
    sim_anh = anhang_lesen(neu_a)
    if sim_anh is None or sim_anh["text"] != text:
        abw.append("Anhang im neuen Archiv stimmt nicht mit dem Text überein")
    if neu_b != b0[:info["ts"]] or not neu_a.startswith(a0):
        abw.append("neuer Stand verändert mehr als erlaubt")
    if abw:
        for x in abw:
            ausgabe("ABWEICHUNG", x)
        raise Abbruch("Vorab-Prüfung des neuen Stands ist rot, nichts geschrieben")
    # Sicherungen
    try:
        os.makedirs(args.sicherung, exist_ok=True)
        zeit = datetime.datetime.now()
        sb = sichern(args.sicherung, "BACKLOG", b0, zeit)
        sa = sichern(args.sicherung, "BACKLOG-ARCHIVE", a0, zeit)
    except OSError as e:
        raise Abbruch("Sicherung nicht anlegbar (%s)" % e.__class__.__name__)
    ausgabe("SICHERUNG_BACKLOG_MD5", sb)
    ausgabe("SICHERUNG_ARCHIV_MD5", sa)
    if haken("sicherung"):
        sys.stdout.flush()
        os._exit(99)
    skript = os.environ.get("T116_HAKEN_NACH_PRUEFUNG")
    if skript:
        subprocess.run([sys.executable, skript], timeout=120)
    # fremde Aenderung zwischen Pruefung und Schreiben?
    if md5(lies(args.backlog)) != md5(b0):
        raise Abbruch("Backlog hat sich seit der Prüfung verändert, nichts geschrieben - bitte von vorn beginnen")
    if md5(lies(args.archiv)) != md5(a0):
        raise Abbruch("Archiv hat sich seit der Prüfung verändert, nichts geschrieben - bitte von vorn beginnen")
    # 1. Archiv
    if info["zustand"] == "noch zu tun":
        archiv_schreiben(args.archiv, a0, neu_a)
        nach_a = lies(args.archiv)
        anh = anhang_lesen(nach_a)
        if nach_a != neu_a or anh is None or md5(anh["text"]) != md5(text):
            raise Abbruch("Archiv nach dem Schreiben nicht wie erwartet - Backlog bleibt unberührt")
    if haken("archiv"):
        sys.stdout.flush()
        os._exit(99)
    # 2. Backlog (vorher erneut gegen fremde Aenderung pruefen)
    if md5(lies(args.backlog)) != md5(b0):
        raise Abbruch("Backlog hat sich vor dem Kürzen verändert, nicht gekuerzt (Text steht jetzt in beiden Dateien)")
    backlog_schreiben(args.backlog, neu_b)
    # Nachkontrolle
    b1, a1 = lies(args.backlog), lies(args.archiv)
    nach = messen(b1, a1)
    abw = vergleiche(vor, nach)
    anh = anhang_lesen(a1)
    if b1 != neu_b or anh is None or anh["text"] != text or md5(anh["text"]) != md5(text):
        abw.append("Dateien nach dem Schreiben nicht wie erwartet")
    if abw:
        for x in abw:
            ausgabe("ABWEICHUNG", x)
        ausgabe("NACHWEIS", "rot")
        raise Abbruch("Nachkontrolle rot - Rückweg über die Sicherungen")
    if info["zustand"] == "noch zu tun":
        ausgabe("ERGAENZTE_ZEILEN", nach["sum_z"] - vor["sum_z"])
        ausgabe("ERGAENZTE_ZEICHEN", nach["sum_c"] - vor["sum_c"])
    else:
        ausgabe("ERGAENZTE_ZEILEN", 0)
        ausgabe("ERGAENZTE_ZEICHEN", 0)
    ausgabe("VORHER_SUMME_ZEILEN", vor["sum_z"])
    ausgabe("VORHER_SUMME_ZEICHEN", vor["sum_c"])
    ausgabe("NACHHER_SUMME_ZEILEN", nach["sum_z"])
    ausgabe("NACHHER_SUMME_ZEICHEN", nach["sum_c"])
    ausgabe("TICKETS", nach["tickets"])
    ausgabe("DOPPELTE_IDS", len(nach["doppelte"]))
    ausgabe("LINT_FEHLER", nach["fehler"])
    ausgabe("LINT_WARNUNGEN", nach["warnungen"])
    ausgabe("NACHWEIS", "gruen")
    ausgabe("ERGEBNIS", "ok")
    return 0


def modus_nachweis(args):
    if not args.vorher_backlog or not args.vorher_archiv:
        raise Abbruch("--nachweis braucht --vorher-backlog und --vorher-archiv")
    vb, va = lies(args.vorher_backlog), lies(args.vorher_archiv)
    nb, na = lies(args.backlog), lies(args.archiv)
    abw = []
    vtext, vts = None, None
    try:
        vts = finde_text_start(vb, args.ticket)
        vtext = vb[vts:]
        if not vtext:
            abw.append("Vorher-Backlog enthaelt keinen Text unter %s" % args.ticket)
            vtext = None
    except Abbruch as e:
        abw.append("Vorher-Backlog: " + e.grund)
    try:
        nts = finde_text_start(nb, args.ticket)
        if nb[nts:]:
            abw.append("Backlog endet nicht am Trennstrich von %s" % args.ticket)
    except Abbruch as e:
        abw.append("Backlog: " + e.grund)
    try:
        anh = anhang_lesen(na)
    except Abbruch as e:
        anh = None
        abw.append("Archiv: " + e.grund)
    if anh is None:
        abw.append("Anhang im Archiv fehlt")
    else:
        if vtext is not None and anh["text"] != vtext:
            ea, ta = vtext.split(b"\n"), anh["text"].split(b"\n")
            n = min(len(ea), len(ta)) + 1
            for i in range(min(len(ea), len(ta))):
                if ea[i] != ta[i]:
                    n = i + 1
                    break
            abw.append("Text im Archiv weicht vom Text vorher ab (erste abweichende Zeile %d, Prüfsumme %s statt %s)"
                       % (n, md5(anh["text"]), md5(vtext)))
        mm = re.search(r"^Prüfsumme \(MD5\): ([0-9a-f]{32})$", anh["kopf"], re.M)
        zz = re.search(r"^Zeilen: (\d+)$", anh["kopf"], re.M)
        if not mm or mm.group(1) != md5(anh["text"]):
            abw.append("Prüfsumme im Kopf des Anhangs passt nicht zum Text")
        if not zz or int(zz.group(1)) != zeilenzahl(anh["text"]):
            abw.append("Zeilenzahl im Kopf des Anhangs passt nicht zum Text")
    if not na.startswith(va):
        abw.append("Archiv: bestehender Inhalt wurde verändert (nicht nur ergänzt)")
    vor = messen(vb, va, vb[:vts] if vts is not None else vb)
    nach = messen(nb, na)
    abw += vergleiche(vor, nach)
    messwerte_ausgeben(nach)
    for x in abw:
        ausgabe("ABWEICHUNG", x)
    ausgabe("NACHWEIS", "rot" if abw else "gruen")
    ausgabe("ERGEBNIS", "nur geprueft")
    return 1 if abw else 0


def modus_bericht(args):
    b, a = lies(args.backlog), lies(args.archiv)
    koepfe_b = set(t for _, t in ticket_koepfe(b))
    koepfe_a = set(t for _, t in ticket_koepfe(a))
    try:
        grenze = finde_text_start(b, args.ticket)
        grenze_zeile = b[:grenze].count(b"\n")     # 0-basierter Index der ersten Textzeile
    except Abbruch:
        grenze_zeile = None
    zeilen = [z.decode("utf-8", "replace") for z in b.split(b"\n")]
    funde = []
    i = 0
    while i < len(zeilen):
        if zeilen[i].startswith("## "):
            j = i + 1
            while j < len(zeilen) and not zeilen[j].startswith("## ") and not ID_RE.match(zeilen[j]):
                j += 1
            if grenze_zeile is None or i < grenze_zeile:
                kopfzeile = TICKET_RE.findall(zeilen[i])
                kandidat = None
                if len(set(kopfzeile)) == 1:
                    kandidat = kopfzeile[0]
                else:
                    zaehl = {}
                    for z in zeilen[i:j]:
                        for t in TICKET_RE.findall(z):
                            zaehl[t] = zaehl.get(t, 0) + 1
                    viele = [t for t, v in zaehl.items() if v >= 2]
                    if len(viele) == 1:
                        kandidat = viele[0]
                if kandidat and kandidat in koepfe_a and kandidat not in koepfe_b:
                    funde.append((i + 1, j, kandidat))
            i = j
        else:
            i += 1
    ausgabe("VERWAISTE_ABSCHNITTE", len(funde))
    for von, bis, tid in funde:
        ausgabe("FUND", "Zeile %d (bis %d) gehört zu %s, dessen Kopf nur im Archiv steht" % (von, bis, tid))
    ausgabe("ERGEBNIS", "nur geprueft")
    return 0


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="TASK-116: verwaisten Text ins Archiv verschieben")
    ap.add_argument("--backlog", required=True)
    ap.add_argument("--archiv", required=True)
    ap.add_argument("--ticket", required=True)
    ap.add_argument("--sicherung")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pruefen", action="store_true")
    g.add_argument("--ausfuehren", action="store_true")
    g.add_argument("--nachweis", action="store_true")
    g.add_argument("--bericht", action="store_true")
    ap.add_argument("--vorher-backlog")
    ap.add_argument("--vorher-archiv")
    ap.add_argument("--erwartet-md5")
    ap.add_argument("--erwartet-zeilen", type=int)
    ap.add_argument("--erwartet-text")
    args = ap.parse_args(argv)
    try:
        if args.ausfuehren and not args.sicherung:
            raise Abbruch("--ausfuehren braucht --sicherung")
        if args.pruefen:
            return modus_pruefen(args)
        if args.ausfuehren:
            return modus_ausfuehren(args)
        if args.nachweis:
            return modus_nachweis(args)
        return modus_bericht(args)
    except Abbruch as e:
        for k, v in e.extra.items():
            ausgabe(k, v)
        ausgabe("ERGEBNIS", "abgebrochen")
        ausgabe("GRUND", e.grund)
        sys.stderr.write("Abgebrochen: %s\n" % e.grund)
        return 1


if __name__ == "__main__":
    sys.exit(main())
