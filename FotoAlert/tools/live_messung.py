#!/usr/bin/env python3
"""live_messung.py - Messung fuer BUG-119 (Feed nach Neustart) und BUG-117 (Wetterlauf-Zaehler) auf dem Produktivserver.

Läuft auf dem Mac (nicht auf dem Server); holt Serverdaten selbst per SSH.
Dauerhafte Fassung von _to_delete/messung_117_119/messung_117_119.py. Nur Standardbibliothek, Python 3.7 bis 3.12.

NUR LESEND: HTTP-GET auf /health, /job-status, /opportunities; per SSH nur lesende Befehle
(date, systemctl show, journalctl, sqlite im Nur-Lese-Modus, cat der Tagesstand-Datei).
Kein Neustart, keine Aenderung auf dem Server - das Skript startet NIE neu. Keine Passwoerter/Tokens in Dateien:
SSH fragt selbst nach dem Passwort bzw. nutzt Stephans Schluessel.

Aufruf (Mac, aus dem Projektordner FotoAlert/FotoAlert/):
  python3 tools/live_messung.py vorher
  python3 tools/live_messung.py beobachten [MINUTEN] [SEKUNDEN_ABSTAND]
  python3 tools/live_messung.py nachher
  python3 tools/live_messung.py bug117            (nur Server-Zaehler, z. B. nach einem Wiederholungslauf)
  python3 tools/live_messung.py wdh_vorher        (Berechnungsstand des Feeds, laufende Jobs, naechste Planlaeufe, Warnungen, Feed-Schnappschuss)
  python3 tools/live_messung.py wdh_beobachten [MAX_MIN]   (alle 2 s ueber den Neustart, danach alle 30 s bis Wetterlauf-Ende; Standard 45 min)
  python3 tools/live_messung.py wdh_nachher       (wartet automatisch auf das Wetterlauf-Ende, zweiter Feed-Schnappschuss, Vergleich, Server-Log)
  python3 tools/live_messung.py bug123            (BUG-123: Antwortzeiten nach einem Neustart, nur lesend, siehe unten)
  Zusatzoption (ueberall): --ausgabe ORDNER       (statt des Standard-Ausgabeordners)

Kurzanleitung - Reihenfolge der Schritte (Wiederholungsmessung):
  1. Vorher-Pruefung:            wdh_vorher         (Terminal 1; Ergebnis "keine Warnung" abwarten)
  2. Beobachtung, zweites Terminal: wdh_beobachten  (Terminal 2; starten und laufen lassen, es wartet auf den Neustart)
  3. Neustart per SSH auf dem Server (macht Stephan selbst, NIE dieses Skript)
  4. Nachher:                    wdh_nachher        (Terminal 1; sofort nach dem Neustart starten)
  Neustart und Warten sind getrennte Schritte: Der Neustart ist ein einzelner Befehl auf dem Server; danach braucht der
  Wetterlauf noch Minuten bis zum Ende. wdh_nachher wartet selbst - nicht erneut neu starten.

Neustartzeitpunkt-Regel: nach Ende der Wetterkarte (~43 min nach Planlaufbeginn), >35 min vor dem naechsten Planlauf
(Wetter-Cron Minute 19 alle 3 h Berlin; Vorberechnung 05:30 Berlin).
  Fundstellen in backend/main.py: Scheduler laeuft in Europe/Berlin (Z. 509); Wetter-Planlauf Minute 19 alle 3 h
  (Z. 2066-2072 und 4509); Vorberechnung taeglich 05:30 (Z. 4507-4508); Wetterkarte Minute 39 alle 3 h (Z. 4510);
  Entdecken/Scout taeglich 05:45 (Z. 4511); QA-Lauf taeglich 01:00 (Z. 4506); Wiederholungsversuch "notbremse-retry" (Z. 2080).

Ausgabeordner: Standard FotoAlert/_to_delete/messung_<JJJJ-MM-TT>/ (relativ zum Projektordner, ueber den Skriptpfad
  ermittelt; wird bei Bedarf angelegt). Ueberschreibbar: Option --ausgabe ORDNER oder Umgebungsvariable FA_OUT
  (Option hat Vorrang). Dateinamen unveraendert. Ist fuer wdh_beobachten/wdh_nachher im Tagesordner noch kein
  wdh_stand_vorher.json, wird der Ordner von GESTERN verwendet, falls dort eines liegt (Messung ueber Mitternacht).

Technische Sperre: Existiert das Verzeichnis /opt/fotoalert, ist das der Server -> Abbruch mit Exit-Code 2 und der Meldung
  "Dies ist der Server - dieses Skript gehoert auf den Mac". NUR FUER TESTS umgehbar mit FA_LIVE_MESSUNG_SERVERCHECK_AUS=1;
  der Pruefpfad laesst sich nur fuer Tests per FA_LIVE_MESSUNG_SERVERPFAD aendern. Im Echtbetrieb beides nicht setzen.

Warnung "Kein Neustart erkannt - Messung nicht gewertet": in wdh_beobachten, wenn bis zum Ende keine Zeile mit HTTP 502 gesehen
  wurde UND die SSH-Pruefung keinen neuen Dienststart gegenueber wdh_vorher zeigt; in wdh_nachher, wenn die SSH-Pruefung keinen
  neuen Dienststart belegt. Sie steht im Terminal und in der Datei (Beobachtungsdatei bzw. Zusammenfassung).

Rueckgabecodes: 0 in Ordnung, 1 Zeitlimit (wdh_nachher), 2 Aufruf-/Umgebungsfehler oder Server-Sperre, 3 Warnung
  (wdh_vorher: Neustart nicht empfohlen; wdh_beobachten/wdh_nachher: Kein Neustart erkannt).
Zwischen wdh_vorher und wdh_nachher wird der Server von Stephan neu gestartet.
"""
import ast
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from collections import Counter

try:
    from zoneinfo import ZoneInfo
    BERLIN = ZoneInfo("Europe/Berlin")
except Exception:  # pragma: no cover
    BERLIN = timezone.utc

HIER = os.path.dirname(os.path.abspath(__file__))
PROJEKT = os.path.dirname(HIER)  # tools/ liegt direkt im Projektordner (FotoAlert/FotoAlert/)
OUT = None  # Ausgabeordner, wird in main() gesetzt (siehe ausgabeordner_bestimmen)
SERVER_PFAD = os.environ.get("FA_LIVE_MESSUNG_SERVERPFAD", "/opt/fotoalert")  # nur fuer Tests aenderbar
SERVERCHECK_AUS = os.environ.get("FA_LIVE_MESSUNG_SERVERCHECK_AUS") == "1"      # nur fuer Tests
KEIN_NEUSTART = "Kein Neustart erkannt – Messung nicht gewertet"
BASIS = os.environ.get("FA_BASE_URL", "https://fotoalert.stephanschumann.com").rstrip("/")
SSH_ZIEL = os.environ.get("FA_SSH_ZIEL", "root@167.233.138.36")
SSH_BIN = os.environ.get("FA_SSH_BIN", "ssh")
APP = os.environ.get("FA_REMOTE_APP", "/opt/fotoalert/app/FotoAlert/backend")
VENV_PY = os.environ.get("FA_REMOTE_PY", "/opt/fotoalert/venv/bin/python3")
SCHWELLE = 0.70
# Die App fragt /opportunities?min_score=<CFG.minScore>&days=14 (web/index.html Z. 2258); CFG.minScore = 0.3 (Z. 7224)
FEED_PFAD = "/opportunities?min_score=0.3&days=14"


def jetzt_utc():
    return datetime.now(timezone.utc)


def stempel():
    return jetzt_utc().strftime("%Y%m%dT%H%M%SZ")


def schreiben(name, text):
    pfad = os.path.join(OUT, name)
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(text)
    print("  geschrieben:", pfad)
    return pfad


def http_get(pfad, timeout=60):
    """Gibt (status, sekunden, body_bytes, fehlertext) zurueck."""
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(BASIS + pfad, headers={"User-Agent": "fotoalert-messung-117-119"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return r.status, time.monotonic() - t0, body, ""
    except urllib.error.HTTPError as e:
        return e.code, time.monotonic() - t0, b"", "HTTPError %s" % e.code
    except Exception as e:  # Verbindung abgelehnt, Zeitueberschreitung, ...
        return 0, time.monotonic() - t0, b"", "%s: %s" % (type(e).__name__, e)


def json_oder_none(body):
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def parse_zeit(s):
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)  # Cache shoot_time ist UTC
    return d


def feed_auswerten(liste, jetzt=None):
    """Kennzahlen eines Feeds. Wetter-Etikett = weather_status (backend/main.py), 'ok' = Wetter eingerechnet."""
    jetzt = jetzt or jetzt_utc()
    heute = jetzt.astimezone(BERLIN).date()
    morgen = heute + timedelta(days=1)
    z = {"gesamt": len(liste), "kappung_500_erreicht": len(liste) >= 500,
         "datum_heute_berlin": heute.isoformat(), "datum_morgen_berlin": morgen.isoformat()}
    ab70 = {"heute": 0, "morgen": 0}
    wetter = {"heute": Counter(), "morgen": Counter(), "uebermorgen": Counter()}
    wetter_ab70 = Counter()
    besondere_ids = 0
    besondere_typen = Counter()
    prio2 = 0
    prio2_ab70 = 0
    for e in liste:
        try:
            tag = parse_zeit(e["shoot_time"]).astimezone(BERLIN).date()
        except Exception:
            continue
        score = float(e.get("overall_score") or 0)
        st = e.get("weather_status") or "(fehlt)"
        name = {heute: "heute", morgen: "morgen", heute + timedelta(days=2): "uebermorgen"}.get(tag)
        if name:
            wetter[name][st] += 1
        if score >= SCHWELLE:
            if tag == heute:
                ab70["heute"] += 1
            elif tag == morgen:
                ab70["morgen"] += 1
            if name:
                wetter_ab70[st] += 1
        i = str(e.get("id", ""))
        if i.startswith(("gc_", "rs_", "rc_")):
            besondere_ids += 1
            besondere_typen[e.get("event_type", "?")] += 1
        if (e.get("alert_priority") or 0) >= 2:
            prio2 += 1
            if score >= SCHWELLE:
                prio2_ab70 += 1
    z["chancen_ab_70_heute"] = ab70["heute"]
    z["chancen_ab_70_morgen"] = ab70["morgen"]
    z["wetter_etikett_je_tag"] = {k: dict(v) for k, v in wetter.items()}
    z["wetter_etikett_der_chancen_ab_70_naechste_3_tage"] = dict(wetter_ab70)
    z["besondere_ereignisse_ids_gc_rs_rc"] = besondere_ids
    z["besondere_ereignisse_typen"] = dict(besondere_typen)
    z["alert_prio_ab_2_alle"] = prio2
    z["alert_prio_ab_2_und_ab_70"] = prio2_ab70
    return z


def feed_holen(label):
    st, sek, body, fehler = http_get(FEED_PFAD, timeout=120)
    if st != 200:
        return None, {"fehler": "Feed HTTP %s %s" % (st, fehler), "sekunden": round(sek, 2)}
    liste = json_oder_none(body)
    if not isinstance(liste, list):
        return None, {"fehler": "Feed ist keine Liste", "sekunden": round(sek, 2)}
    schreiben("bug119_%s_feed.json" % label, json.dumps(liste, ensure_ascii=False))
    k = feed_auswerten(liste)
    k["sekunden"] = round(sek, 2)
    return liste, k


def health_kurz(d):
    if not isinstance(d, dict):
        return {}
    sub = d.get("subsystems") or {}
    jobs = d.get("jobs") or {}
    w = jobs.get("weather") or {}
    return {"status": d.get("status"), "wetter_subsystem": sub.get("weather"),
            "wetter_alter_h": sub.get("weather_age_h"), "wetter_job": w.get("status"),
            "wetter_job_last_run": w.get("last_run"), "wetter_job_dauer_s": w.get("duration_s"),
            "wetter_job_fehler": (w.get("last_error") or "")[:300] or None,
            "orte_aktiv": d.get("locations_active")}


# ---------------------------------------------------------------- Server (nur lesend, per SSH)
REMOTE = r'''
set -u
APP="__APP__"
PY="__PY__"
SEIT="__SEIT__"
echo "== server_zeit_utc"; date -u +%FT%TZ
echo "== dienst"; systemctl show fotoalert -p ActiveState -p ActiveEnterTimestamp -p MainPID 2>&1
echo "== job_runs_weather"
"$PY" - "$APP" "$SEIT" <<'PYEND'
import sqlite3, sys, subprocess
app, seit = sys.argv[1], sys.argv[2]
try:
    c = sqlite3.connect("file:%s/data/fotoalert.db?mode=ro" % app, uri=True)
    ts_von = subprocess.run(["date", "-u", "-d", seit, "+%Y-%m-%dT%H:%M:%S"], capture_output=True, text=True).stdout.strip()
    for r in c.execute("SELECT ts, job, status, duration_s, error_class, error_msg FROM job_runs WHERE job='weather' AND ts >= ? ORDER BY ts DESC", (ts_von,)):
        print(repr(r))
except Exception as e:
    print("FEHLER job_runs:", type(e).__name__, e)
PYEND
echo "== tagesstand"
cat "$APP/data/cache/weather_tagesstand.json" 2>&1; echo
echo "== journal_gefiltert"
journalctl -u fotoalert --since "$SEIT" --no-pager -o short-iso 2>&1 \
  | grep -E 'BUG-117|BUG-119|Wetter-Overlay-Lauf|Wetterlauf |Notbremse|Feed-Cache geladen|Application startup|Started fotoalert|Stopped fotoalert' \
  | grep -v 'fehlgeschlagen: Server error' | cut -c1-700
echo "== journal_zaehlung"
echo -n "fehler_503_einzelabrufe="; journalctl -u fotoalert --since "$SEIT" --no-pager 2>/dev/null | grep -c "Server error '503"
echo -n "fehler_429_einzelabrufe="; journalctl -u fotoalert --since "$SEIT" --no-pager 2>/dev/null | grep -c "Server error '429\|429 Too Many"
echo "== ende"
'''


def ssh_ausfuehren(skript, timeout=300):
    cmd = [SSH_BIN]
    if SSH_BIN == "ssh":
        cmd += ["-o", "ControlMaster=auto", "-o", "ControlPath=/tmp/fa_messung_%C", "-o", "ControlPersist=15m",
                "-o", "ConnectTimeout=20"]
    cmd += [SSH_ZIEL, "bash", "-s"]
    p = subprocess.run(cmd, input=skript, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def server_holen(label, seit):
    skript = REMOTE.replace("__APP__", APP).replace("__PY__", VENV_PY).replace("__SEIT__", seit)
    try:
        rc, out, err = ssh_ausfuehren(skript)
    except Exception as e:
        schreiben("bug117_%s_server.txt" % label, "SSH-FEHLER: %s\n" % e)
        return None
    schreiben("bug117_%s_server.txt" % label, out + ("\n--- stderr ---\n" + err if err.strip() else ""))
    if rc != 0:
        print("  WARNUNG: SSH Rueckgabecode", rc, err.strip()[:200])
    return out


def abschnitt(text, name):
    m = re.search(r"== %s\n(.*?)(?=\n== |\Z)" % re.escape(name), text, re.S)
    return m.group(1) if m else ""


def server_auswerten(text):
    z = {}
    if not text:
        return {"fehler": "keine Server-Ausgabe"}
    zeilen = [l for l in abschnitt(text, "job_runs_weather").splitlines() if l.startswith("(")]
    runs = []
    for l in zeilen:
        try:
            runs.append(ast.literal_eval(l))  # reine Tupel-Literale aus repr()
        except Exception:
            pass
    z["weather_laeufe_im_zeitraum"] = len(runs)
    z["weather_laeufe_done"] = sum(1 for r in runs if r[2] == "done")
    z["weather_laeufe_error"] = sum(1 for r in runs if r[2] == "error")
    z["weather_laeufe_error_mit_notbremse_text"] = sum(1 for r in runs if r[2] == "error" and r[5] and "vorzeitig beendet" in r[5])
    z["letzte_5_laeufe"] = [(r[0], r[2], r[3]) for r in runs[:5]]
    j = abschnitt(text, "journal_gefiltert")
    z["journal_notbremse_zeilen"] = len(re.findall(r"BUG-117: Notbremse", j))
    z["journal_laeufe_gestartet_je_ausloeser"] = dict(Counter(re.findall(r"Wetter-Overlay-Lauf gestartet \(Ausl.ser: ([^)]*)\)", j)))
    zl = re.findall(r"Wetterlauf Ortswetter[^\n]*?: (\d+) Anfragen, davon (\d+) abgelehnt", j)
    z["zaehlzeilen_ortswetter"] = len(zl)
    z["abgelehnt_429_summe_laut_zaehlzeilen"] = sum(int(b) for a, b in zl)
    z["anfragen_summe_laut_zaehlzeilen"] = sum(int(a) for a, b in zl)
    z["zaehlzeilen_mit_tagesstand"] = len(re.findall(r"Wetterlauf Ortswetter[^\n]*Tagesstand", j))
    z["bug119_aufleg_zeilen"] = re.findall(r"(\S+) .*?(BUG-119: Wetter wieder aufgelegt.*)", j)
    z["feed_cache_geladen_zeilen"] = len(re.findall(r"Feed-Cache geladen", j))
    zz = abschnitt(text, "journal_zaehlung")
    for k in ("fehler_503_einzelabrufe", "fehler_429_einzelabrufe"):
        m = re.search(k + r"=(\d+)", zz)
        z[k] = int(m.group(1)) if m else None
    ts = abschnitt(text, "tagesstand").strip()
    z["tagesstand_datei"] = json_oder_none(ts.encode()) if ts.startswith("{") else ts[:200]
    d = z["tagesstand_datei"]
    if isinstance(d, dict):
        try:
            g = d["ortswetter"]["gewichtet"] + d["scout"]["gewichtet"]
            z["tagesstand_prozent_von_10000"] = round(g / 100.0, 1)  # Limit 10.000 laut wetter_speicher.TAGESLIMIT-Ausgabe
        except Exception:
            pass
    return z


def planlauf_anteil_zeile(text):
    """TASK-127 (AK-11): Eine Zeile "Planlaeufe N, davon mit Notbremse M (P %)" aus der gespeicherten Server-Ausgabe.
    Planlauf = Lauf mit Ausloeser "cron"; die Notbremse zaehlt nur, wenn sie im selben Lauf steht (Start-Laeufe und
    Wiederholungen zaehlen nicht mit). Ohne Planlauf kein Prozentwert. Nur lesend."""
    j = abschnitt(text or "", "journal_gefiltert")
    start = re.compile(r"Wetter-Overlay-Lauf gestartet \(Ausl.ser: ([^)]*)\)")
    aktuell, plan, mit = None, 0, 0
    for zeile in j.splitlines():
        m = start.search(zeile)
        if m:
            aktuell = m.group(1).strip()
            if aktuell == "cron":
                plan += 1
                mit_notbremse = False
            continue
        if aktuell == "cron" and "BUG-117: Notbremse" in zeile and not mit_notbremse:
            mit_notbremse = True
            mit += 1
    if plan == 0:
        return "Planl\u00e4ufe 0, davon mit Notbremse 0"
    return "Planl\u00e4ufe %d, davon mit Notbremse %d (%d %%)" % (plan, mit, int(100.0 * mit / plan + 0.5))


def ausgeben(titel, d):
    return "== %s\n%s\n" % (titel, json.dumps(d, ensure_ascii=False, indent=2, default=str))


# ---------------------------------------------------------------- Modi
def snapshot(label, seit):
    print("Snapshot '%s' ..." % label)
    zeit = stempel()
    bericht = ["Messung %s  (UTC %s)\nBasis: %s\n" % (label, zeit, BASIS)]
    st, sek, body, fehler = http_get("/health")
    h = json_oder_none(body)
    schreiben("bug119_%s_health.json" % label, body.decode("utf-8", "replace") if body else fehler)
    bericht.append(ausgeben("health (HTTP %s, %.3f s)" % (st, sek), health_kurz(h) or fehler))
    st2, sek2, body2, fehler2 = http_get("/job-status")
    js = json_oder_none(body2)
    schreiben("bug119_%s_job-status.json" % label, body2.decode("utf-8", "replace") if body2 else fehler2)
    if isinstance(js, dict):
        laufend = [k for k, v in (js.get("jobs") or {}).items() if isinstance(v, dict) and v.get("status") == "running"]
        bericht.append(ausgeben("job-status (HTTP %s): Jobs im Status running" % st2, laufend or "keine"))
        if laufend:
            print("  HINWEIS: laufende Jobs:", laufend, "- Zeitmessungen sind dann verfaelscht (Memory feedback_server_tempo_messung)")
    else:
        bericht.append(ausgeben("job-status", "HTTP %s %s" % (st2, fehler2)))
    liste, kennz = feed_holen(label)
    bericht.append(ausgeben("feed (BUG-119 AK-1/AK-3/AK-9)", kennz))
    text = server_holen(label, seit)
    bericht.append(ausgeben("server (BUG-117 / BUG-119 Log)", server_auswerten(text)))
    bericht.append(planlauf_anteil_zeile(text) + "\n")
    schreiben("zusammenfassung_%s_%s.txt" % (label, zeit), "\n".join(bericht))
    if label == "vorher":
        schreiben("marker_vorher_utc.txt", jetzt_utc().strftime("%Y-%m-%d %H:%M:%S") + " UTC\n")
    print("\n".join(bericht)[:6000])


def beobachten(minuten, abstand):
    name = "beobachten_%s.txt" % stempel()
    pfad = os.path.join(OUT, name)
    ende = time.monotonic() + minuten * 60
    print("Beobachte %s Minuten alle %s s -> %s  (Abbruch: Strg+C)" % (minuten, abstand, pfad))
    with open(pfad, "w", encoding="utf-8") as f:
        f.write("zeit_utc\thealth_http\thealth_sek\thealth_status\twetter_subsystem\twetter_job\twetter_job_last_run\t"
                "feed_http\tfeed_sek\tfeed_gesamt\tab70_heute\tab70_morgen\twetter_ok_naechste3tage_ab70\twetter_andere_naechste3tage_ab70\tbesondere_ids\tfehler\n")
        f.flush()
        try:
            while time.monotonic() < ende:
                t0 = time.monotonic()
                st, sek, body, fehler = http_get("/health", timeout=30)
                h = health_kurz(json_oder_none(body))
                fs, fsek, fbody, ffehler = http_get(FEED_PFAD, timeout=60)
                k = {}
                if fs == 200:
                    l = json_oder_none(fbody)
                    if isinstance(l, list):
                        k = feed_auswerten(l)
                w3 = k.get("wetter_etikett_der_chancen_ab_70_naechste_3_tage", {})
                zeile = [jetzt_utc().strftime("%H:%M:%S"), st, "%.3f" % sek, h.get("status"), h.get("wetter_subsystem"),
                         h.get("wetter_job"), h.get("wetter_job_last_run"), fs, "%.3f" % fsek, k.get("gesamt"),
                         k.get("chancen_ab_70_heute"), k.get("chancen_ab_70_morgen"), w3.get("ok", 0) if k else None,
                         (sum(v for a, v in w3.items() if a != "ok") if k else None), k.get("besondere_ereignisse_ids_gc_rs_rc"),
                         (fehler or ffehler)]
                f.write("\t".join("" if v is None else str(v) for v in zeile) + "\n")
                f.flush()
                rest = abstand - (time.monotonic() - t0)
                if rest > 0:
                    time.sleep(rest)
        except KeyboardInterrupt:
            print("abgebrochen")
    print("fertig:", pfad)


# ================================================================ Wiederholungsmessung (Dateien mit Praefix wdh_)
# Neue Modi: wdh_vorher, wdh_beobachten, wdh_nachher. Die vier alten Modi (vorher, beobachten, nachher, bug117)
# sind unveraendert. Auch hier: NUR LESEND, kein Neustart, keine Passwoerter/Tokens in Dateien.
# Ablauf-Schwellen und Takte sind ueber FA_WDH_* ueberschreibbar (nur fuer Tests gedacht, Standardwerte = Vorgabe).
WDH_WARN_MIN = float(os.environ.get("FA_WDH_WARN_MIN", "25"))            # Warnung: weniger als so viele Minuten bis zum Planlauf
WDH_EMPF_MIN = float(os.environ.get("FA_WDH_EMPF_MIN", "35"))            # empfohlener Mindestabstand (Startlauf + Wetterkarte laufen ~30 min)
WDH_TAKT_SCHNELL = float(os.environ.get("FA_WDH_TAKT_SCHNELL", "2"))     # Beobachtung bis kurz nach dem Neustart
WDH_TAKT_LANGSAM = float(os.environ.get("FA_WDH_TAKT_LANGSAM", "30"))    # danach bis Lauf-Ende
WDH_SCHNELL_NACH_START_S = float(os.environ.get("FA_WDH_SCHNELL_NACH_START_S", "60"))  # so lange nach "Server wieder da" noch schnell
WDH_WARTE_TAKT = float(os.environ.get("FA_WDH_WARTE_TAKT", "15"))        # Abstand beim Warten in wdh_nachher
WDH_RUHE_S = float(os.environ.get("FA_WDH_RUHE_S", "90"))                # so lange darf kein Wetterlauf "running" sein, bis das Ende gilt
WDH_MAX_MIN = float(os.environ.get("FA_WDH_MAX_MIN", "45"))              # Obergrenze fuers Warten/Beobachten
WDH_LOG_VORLAUF_S = int(os.environ.get("FA_WDH_LOG_VORLAUF_S", "15"))    # Log beginnt so viele Sekunden vor dem Neustart (Herunterfahren)
BERLIN_OK = BERLIN is not timezone.utc
BESONDERE_PRAEFIX = ("gc_", "rs_", "rc_")

# (Name, Stunden in Berliner Zeit, Minute, Fundstelle) - APScheduler laeuft in Europe/Berlin (backend/main.py Z. 509)
WDH_PLAN = [
    ("Wetter-Planlauf (alle 3 h, Minute 19)", tuple(range(0, 24, 3)), 19, "backend/main.py Z. 4509 und 2066-2072"),
    ("Vorberechnung (taeglich 05:30)", (5,), 30, "backend/main.py Z. 4507-4508"),
    ("Wetterkarte (alle 3 h, Minute 39, dauert ~17-23 min)", tuple(range(0, 24, 3)), 39, "backend/main.py Z. 4510"),
    ("Entdecken/Scout (taeglich 05:45)", (5,), 45, "backend/main.py Z. 4511"),
    ("QA-Lauf (taeglich 01:00)", (1,), 0, "backend/main.py Z. 4506"),
]


def wdh_jetzt():
    s = os.environ.get("FA_WDH_JETZT")  # nur fuer Tests
    return parse_zeit(s) if s else jetzt_utc()


def wdh_naechster(jetzt, stunden, minute):
    """Naechster Zeitpunkt nach `jetzt` (aware, Berliner Zeit), dessen Berliner Stunde in `stunden` liegt, zur Minute `minute`."""
    t = jetzt.astimezone(BERLIN).replace(minute=minute, second=0, microsecond=0).astimezone(timezone.utc)
    for _ in range(24 * 3):
        lt = t.astimezone(BERLIN)
        if t > jetzt and lt.hour in stunden:
            return lt
        t += timedelta(hours=1)
    return None


def wdh_plan_pruefen(jetzt, laufende_jobs, precompute_laeuft):
    """Gibt (zeilen, warnungen) zurueck. Warnung: weniger als WDH_WARN_MIN Minuten bis zu einem Planlauf, oder ein Job laeuft."""
    zeilen, warn = [], []
    if not BERLIN_OK:
        warn.append("WARNUNG: Zeitzone Europe/Berlin ist in diesem Python nicht verfuegbar - Planzeiten unten sind UNSICHER "
                    "(Abhilfe: python3 -m pip install tzdata).")
    zeilen.append("Jetzt: %s UTC = %s Berlin" % (jetzt.strftime("%Y-%m-%d %H:%M:%S"),
                                                   jetzt.astimezone(BERLIN).strftime("%Y-%m-%d %H:%M:%S %Z")))
    for name, stunden, minute, beleg in WDH_PLAN:
        n = wdh_naechster(jetzt, stunden, minute)
        if n is None:
            zeilen.append("%s: nicht berechenbar" % name)
            continue
        rest = (n - jetzt).total_seconds() / 60.0
        zeilen.append("%s: naechster Lauf %s Berlin = %s UTC, in %.0f min  (Beleg: %s)" % (
            name, n.strftime("%a %d.%m. %H:%M"), n.astimezone(timezone.utc).strftime("%H:%M"), rest, beleg))
        if rest < WDH_WARN_MIN:
            warn.append("WARNUNG: %s in %.0f min (weniger als %.0f min) - Neustart jetzt NICHT empfohlen." % (name, rest, WDH_WARN_MIN))
        elif rest < WDH_EMPF_MIN:
            zeilen.append("   Hinweis: nur %.0f min Abstand (empfohlen mindestens %.0f min)." % (rest, WDH_EMPF_MIN))
    if laufende_jobs:
        warn.append("WARNUNG: Jobs laufen gerade: %s - Neustart jetzt NICHT empfohlen (bricht sie ab)." % ", ".join(laufende_jobs))
    if precompute_laeuft:
        warn.append("WARNUNG: Vorberechnung (precompute) laeuft gerade - Neustart jetzt NICHT empfohlen.")
    return zeilen, warn


def wdh_jobs_laufend(jobs):
    return sorted(k for k, v in (jobs or {}).items() if isinstance(v, dict) and v.get("status") == "running")


def wdh_abschnitte(text):
    """Zerlegt die Server-Ausgabe an Zeilen, die mit '== ' beginnen (leere Abschnitte bleiben leer)."""
    d, name = {}, None
    for l in (text or "").splitlines():
        if l.startswith("== "):
            name = l[3:].strip()
            d[name] = []
        elif name is not None:
            d[name].append(l)
    return d


# ---- Server lesend: Feed-Stand (Datei + Speicher-Stand aus dem Journal), Dienst-Start
REMOTE_WDH_STAND = r'''
set -u
APP="__APP__"
PY="__PY__"
echo "== server_zeit_utc"; date -u +%FT%TZ
echo "== dienst"; systemctl show fotoalert -p ActiveState -p ActiveEnterTimestamp -p MainPID 2>&1
echo "== dienst_start_utc"
E=$(date -u -d "$(systemctl show fotoalert -p ActiveEnterTimestamp --value)" +%s 2>/dev/null)
if [ -n "$E" ]; then date -u -d "@$E" '+%Y-%m-%d %H:%M:%S'; fi
echo "== feed_datei"
"$PY" - "$APP/data/cache/opportunities.json" <<'PYEND'
import json, os, sys, datetime
p = sys.argv[1]
try:
    st = os.stat(p)
    d = json.load(open(p, encoding="utf-8"))
    print(json.dumps({"mtime_utc": datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat(),
                      "bytes": st.st_size,
                      "computed_at": d.get("computed_at") if isinstance(d, dict) else None,
                      "anzahl": len(d.get("opportunities", [])) if isinstance(d, dict) else None}))
except Exception as e:
    print(json.dumps({"fehler": "%s: %s" % (type(e).__name__, e)}))
PYEND
J=$(journalctl -u fotoalert --since "3 days ago" --no-pager -o short-iso 2>&1 | grep -E 'Feed-Cache geladen|Wetter-Overlay-Lauf gestartet|Wetterlauf Ortswetter' | cut -c1-420)
echo "== journal_feed_geladen"; printf '%s\n' "$J" | grep 'Feed-Cache geladen' | tail -n 3
echo "== journal_wetterlauf"; printf '%s\n' "$J" | grep -E 'Wetter-Overlay-Lauf gestartet|Wetterlauf Ortswetter' | tail -n 6
echo "== ende"
'''

# ---- Server lesend: Log ab Neustart (ohne HTTP-Request-Zeilen)
REMOTE_WDH_LOG = r'''
set -u
echo "== server_zeit_utc"; date -u +%FT%TZ
echo "== dienst"; systemctl show fotoalert -p ActiveState -p ActiveEnterTimestamp -p MainPID 2>&1
E=$(date -u -d "$(systemctl show fotoalert -p ActiveEnterTimestamp --value)" +%s 2>/dev/null)
if [ -z "$E" ]; then echo "== fehler"; echo "ActiveEnterTimestamp nicht lesbar"; echo "== ende"; exit 0; fi
SEIT=$(date -u -d "@$((E - __VORLAUF__))" '+%Y-%m-%d %H:%M:%S UTC')
echo "== seit"; echo "$SEIT"
HTTPRE='HTTP Request: |- "(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) [^"]*" [0-9]{3}'
J=$(journalctl -u fotoalert --since "$SEIT" --no-pager -o short-iso 2>&1)
echo "== http_ausgelassen"; printf '%s\n' "$J" | grep -c -E "$HTTPRE"
echo "== log"; printf '%s\n' "$J" | grep -v -E "$HTTPRE"
echo "== ende"
'''


def wdh_ssh(skript, timeout=300):
    cmd = [SSH_BIN]
    if SSH_BIN == "ssh":
        cmd += ["-o", "ControlMaster=auto", "-o", "ControlPath=/tmp/fa_messung_%C", "-o", "ControlPersist=15m",
                "-o", "ConnectTimeout=20"]
    cmd += [SSH_ZIEL, "bash", "-s"]
    try:
        p = subprocess.run(cmd, input=skript, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return -1, "", "%s: %s" % (type(e).__name__, e)


RE_GELADEN = re.compile(r"^(\S+) .*Feed-Cache geladen: (\d+) Events \(berechnet: ([^)]*)\)")


def wdh_stand_holen():
    """Liest den Feed-Stand vom Server (nur lesend). Gibt dict zurueck; bei Fehler {'fehler': ...}."""
    skript = REMOTE_WDH_STAND.replace("__APP__", APP).replace("__PY__", VENV_PY)
    rc, out, err = wdh_ssh(skript)
    if rc != 0 and not out:
        return {"fehler": "SSH Rueckgabecode %s: %s" % (rc, (err or "").strip()[:200])}
    ab = wdh_abschnitte(out)
    z = {"server_zeit_utc": " ".join(ab.get("server_zeit_utc", [])).strip()}
    for l in ab.get("dienst", []):
        if "=" in l:
            k, v = l.split("=", 1)
            z[{"ActiveState": "dienst_status", "ActiveEnterTimestamp": "dienst_aktiv_seit_roh", "MainPID": "main_pid"}.get(k.strip(), k.strip())] = v.strip()
    z["dienst_aktiv_seit_utc"] = " ".join(ab.get("dienst_start_utc", [])).strip() or None
    fd = json_oder_none("\n".join(ab.get("feed_datei", [])).encode("utf-8"))
    z["feed_datei"] = fd if isinstance(fd, dict) else {"fehler": "nicht lesbar"}
    geladen = []
    for l in ab.get("journal_feed_geladen", []):
        m = RE_GELADEN.match(l)
        if m:
            geladen.append({"zeit": m.group(1), "events": int(m.group(2)), "berechnet": m.group(3)})
    z["journal_feed_geladen"] = geladen
    z["journal_wetterlauf"] = [l[:260] for l in ab.get("journal_wetterlauf", []) if l.strip()]
    return z


def wdh_stand_zeilen(z):
    if z.get("fehler"):
        return ["Server-Stand NICHT lesbar: %s" % z["fehler"]]
    fd = z.get("feed_datei") or {}
    zl = ["Server-Zeit (UTC): %s | Dienst seit (UTC): %s | Haupt-PID: %s" % (z.get("server_zeit_utc"), z.get("dienst_aktiv_seit_utc"), z.get("main_pid")),
          "Feed-Datei auf der Platte: berechnet (computed_at) = %s | geaendert (mtime) = %s | Eintraege = %s" % (
              fd.get("computed_at"), fd.get("mtime_utc"), fd.get("anzahl"))]
    if fd.get("fehler"):
        zl.append("   Feed-Datei nicht lesbar: %s" % fd["fehler"])
    g = z.get("journal_feed_geladen") or []
    if g:
        zl.append("Feed im Arbeitsspeicher (letzte Zeile 'Feed-Cache geladen' im Journal): geladen %s, %d Events, berechnet = %s" % (
            g[-1]["zeit"], g[-1]["events"], g[-1]["berechnet"]))
    else:
        zl.append("Feed im Arbeitsspeicher: keine Zeile 'Feed-Cache geladen' in den letzten 3 Tagen im Journal gefunden (nicht belegt)")
    return zl


def wdh_feed_holen(dateiname, timeout=120):
    st, sek, body, fehler = http_get(FEED_PFAD, timeout=timeout)
    if st != 200:
        return None, {"fehler": "Feed HTTP %s %s" % (st, fehler), "sekunden": round(sek, 2)}
    liste = json_oder_none(body)
    if not isinstance(liste, list):
        return None, {"fehler": "Feed ist keine Liste", "sekunden": round(sek, 2)}
    schreiben(dateiname, json.dumps(liste, ensure_ascii=False))
    k = feed_auswerten(liste)
    k["sekunden"] = round(sek, 2)
    return liste, k


def wdh_typ_quoten(liste):
    return dict(Counter(str(e.get("event_type", "?")) for e in liste))


# ---- Feed-Vergleich eintragsweise nach id
def _num(x):
    try:
        return None if x is None else float(x)
    except Exception:
        return None


def wdh_feed_vergleich(a, b, name_a, name_b, bezug_b):
    """Vergleicht zwei Feed-Listen eintragsweise nach id. Eintraege mit gc_/rs_/rc_ (Zufalls-IDs) sind nicht zuordenbar."""
    L = []
    A = {str(e.get("id", "")): e for e in a}
    B = {str(e.get("id", "")): e for e in b}
    besond = lambda i: i.startswith(BESONDERE_PRAEFIX)
    ia = {i for i in A if not besond(i)}
    ib = {i for i in B if not besond(i)}
    gem = sorted(ia & ib)
    L.append("Eintraege: %s = %d | %s = %d | gemeinsam (ohne gc_/rs_/rc_) = %d | nur in %s = %d | nur in %s = %d" % (
        name_a, len(a), name_b, len(b), len(gem), name_a, len(ia - ib), name_b, len(ib - ia)))
    ba = Counter(i[:3] for i in A if besond(i))
    bb = Counter(i[:3] for i in B if besond(i))
    L.append("Besondere Ereignisse (gc_/rs_/rc_, Zufalls-IDs, nicht zuordenbar): %s = %s | %s = %s" % (name_a, dict(ba), name_b, dict(bb)))
    ta, tb = Counter(str(e.get("event_type", "?")) for e in a), Counter(str(e.get("event_type", "?")) for e in b)
    typen = sorted(set(ta) | set(tb), key=lambda t: (-max(ta[t], tb[t]), t))
    gleich = all(ta[t] == tb[t] for t in typen)
    L.append("500er-Kappung: %s %s | %s %s" % (name_a, "erreicht" if len(a) >= 500 else "nicht erreicht", name_b, "erreicht" if len(b) >= 500 else "nicht erreicht"))
    L.append("Typ-Quoten identisch: %s" % ("JA" if gleich else "NEIN"))
    for t in typen:
        L.append("   %-34s %4d -> %4d  (%+d)" % (t, ta[t], tb[t], tb[t] - ta[t]))
    for feld in ("weather_score", "overall_score"):
        geaendert, hoeher, niedriger, fehlt = 0, 0, 0, 0
        maxd = 0.0
        for i in gem:
            va, vb = _num(A[i].get(feld)), _num(B[i].get(feld))
            if va is None or vb is None:
                if va is not vb:
                    fehlt += 1
                continue
            d = vb - va
            if abs(d) > 1e-9:
                geaendert += 1
                hoeher += d > 0
                niedriger += d < 0
                maxd = max(maxd, abs(d))
        L.append("%s: geaendert bei %d von %d gemeinsamen (hoeher %d, niedriger %d, groesste Aenderung %.3f; Feld nur auf einer Seite vorhanden: %d)" % (
            feld, geaendert, len(gem), hoeher, niedriger, maxd, fehlt))
    grenze = bezug_b + timedelta(days=3)
    uebergang = Counter()
    for i in gem:
        sa = A[i].get("weather_status") or "(fehlt)"
        sb = B[i].get("weather_status") or "(fehlt)"
        try:
            fern = parse_zeit(B[i]["shoot_time"]) > grenze
        except Exception:
            fern = None
        uebergang[(sa, sb, {True: "jenseits T+3", False: "innerhalb T+3", None: "Zeit unbekannt"}[fern])] += 1
    aend = {k: v for k, v in uebergang.items() if k[0] != k[1]}
    L.append("weather_status geaendert bei %d von %d gemeinsamen. Uebergaenge %s -> %s (T+3 = Zeitpunkt von %s + 3 Tage):" % (
        sum(aend.values()), len(gem), name_a, name_b, name_b))
    for (sa, sb, wo), n in sorted(uebergang.items(), key=lambda kv: -kv[1]):
        L.append("   %-8s -> %-8s %-15s %5d%s" % (sa, sb, wo, n, "" if sa != sb else "  (unveraendert)"))
    gr = []
    for i in gem:
        va, vb = _num(A[i].get("overall_score")), _num(B[i].get("overall_score"))
        if va is not None and vb is not None and abs(vb - va) > 1e-9:
            gr.append((abs(vb - va), i, va, vb))
    gr.sort(reverse=True)
    if gr:
        L.append("Groesste Aenderungen overall_score (bis 10):")
        for d, i, va, vb in gr[:10]:
            L.append("   %s | %s | %s | %.3f -> %.3f | weather_status %s -> %s" % (
                i, A[i].get("event_type"), str(A[i].get("shoot_time"))[:16], va, vb,
                A[i].get("weather_status") or "(fehlt)", B[i].get("weather_status") or "(fehlt)"))
    return L


# ---- Server-Log auswerten (ohne HTTP-Request-Zeilen)
RE_ISO = re.compile(r"^(\d{4}-\d\d-\d\d)T(\d\d:\d\d:\d\d)")


def _lz(l):
    m = RE_ISO.match(l)
    return (m.group(1) + " " + m.group(2)) if m else "?"


def _kurz_url(u):
    return re.sub(r"for url '[^']*'", "for url '...'", u)[:220]


def wdh_log_auswerten(text):
    ab = wdh_abschnitte(text)
    zeilen = [l for l in ab.get("log", []) if l.strip()]
    z = {"fehler": " ".join(ab.get("fehler", [])).strip() or None,
         "seit": " ".join(ab.get("seit", [])).strip(),
         "dienst": [l.strip() for l in ab.get("dienst", [])],
         "http_zeilen_ausgelassen": None}
    try:
        z["http_zeilen_ausgelassen"] = int(" ".join(ab.get("http_ausgelassen", [])).strip())
    except Exception:
        pass
    starts, zaehl, ergeb, fehler_orte, aufleg, geladen, notbremse = [], [], [], [], [], [], []
    retry_angesetzt = 0
    marken = {}
    for l in zeilen:
        m = re.search(r"Wetter-Overlay-Lauf gestartet \(Ausl.ser: ([^)]*)\)", l)
        if m:
            starts.append((_lz(l), m.group(1)))
        m = re.search(r"Wetterlauf Ortswetter \(Ausl.ser: ([^)]*)\): (\d+) Anfragen, davon (\d+) abgelehnt \(429\), Anteil ([\d,.]+) %\D{0,6}Dauer ([\d,.]+) s", l)
        if m:
            zaehl.append({"zeit": _lz(l), "ausloeser": m.group(1), "anfragen": int(m.group(2)), "abgelehnt": int(m.group(3)),
                          "dauer_s": m.group(5), "zeile": l[l.index("Wetterlauf Ortswetter"):][:600]})
        m = re.search(r'(\{"event": "job_(?:run|error)".*\})\s*$', l)
        if m:
            try:
                d = json.loads(m.group(1))
                if d.get("job") == "weather":
                    ergeb.append({"zeit": _lz(l), "status": d.get("status"), "dauer_s": d.get("duration_s"),
                                  "fehlerklasse": d.get("error_class"), "meldung": d.get("error_msg")})
            except Exception:
                pass
        m = re.search(r"WARNING\s+(\w+) f.r (.+?) fehlgeschlagen:\s*(.*)$", l)
        if m:
            fehler_orte.append({"zeit": _lz(l), "art": m.group(1), "ort": m.group(2), "ursache": _kurz_url(m.group(3).strip()) or "(Log-Zeile ohne Ursachentext)"})
        m = re.search(r"BUG-119: Wetter wieder aufgelegt \(Ausl.ser: ([^)]*)\): (\d+) Termine mit gespeichertem Wetter, (\d+) ohne\s+\S+\s+Dauer ([\d,.]+) s", l)
        if m:
            aufleg.append({"zeit": _lz(l), "ausloeser": m.group(1), "mit": int(m.group(2)), "ohne": int(m.group(3)), "dauer_s": m.group(4)})
        m = RE_GELADEN.match(l)
        if m:
            geladen.append({"zeit": _lz(l), "events": int(m.group(2)), "berechnet": m.group(3)})
        if "BUG-117: Notbremse" in l:
            notbremse.append(l[:300])
        if "Wiederholungsversuch des Wetterlaufs" in l and "angesetzt" in l:
            retry_angesetzt += 1
            notbremse.append(l[:300])
        for key, muster in (("gestartet", "Started fotoalert.service"), ("bereit", " Bereit. Cache:"),
                            ("startup_fertig", "Application startup complete")):
            if muster in l and key not in marken:
                marken[key] = _lz(l)
    retry_gestartet = sum(1 for s in starts if s[1] == WEATHER_RETRY_TRIGGER_NAME)
    z.update({"starts": starts, "zaehlzeilen": zaehl, "ergebnisse": ergeb, "fehler_orte": fehler_orte, "aufleg": aufleg,
              "feed_geladen": geladen, "notbremse": notbremse, "marken": marken,
              "retry_offen": retry_angesetzt > retry_gestartet})
    z["beendet"] = bool(starts) and len(zaehl) >= len(starts) and not z["retry_offen"]
    z["zeilen_gesamt"] = len(zeilen)
    # Log bis zum Ende des (letzten) Wetterlaufs
    idx = None
    if z["beendet"]:
        for i, l in enumerate(zeilen):
            if "Wetterlauf Ortswetter (" in l:
                idx = i
    z["zeilen_bis_ende"] = zeilen[:idx + 1] if idx is not None else zeilen
    return z


WEATHER_RETRY_TRIGGER_NAME = "notbremse-retry"   # backend/main.py Z. 2080


def wdh_log_zeilen(lg):
    """Text fuer die Zusammenfassung - ohne HTTP-Request-Zeilen und ohne die 'Wetter fuer <Ort>: OK'-Zeilen."""
    if lg.get("fehler"):
        return ["Log NICHT gezogen: %s" % lg["fehler"]]
    L = ["Log ab (UTC): %s | ausgelassene HTTP-Zeilen (httpx-Wetterabrufe und App-Zugriffe): %s | Log-Zeilen ohne diese: %d" % (
        lg.get("seit"), lg.get("http_zeilen_ausgelassen"), lg.get("zeilen_gesamt", 0))]
    mk = lg.get("marken", {})
    L.append("Neustart im Log: 'Started' %s | 'Bereit' %s | 'Application startup complete' %s" % (mk.get("gestartet"), mk.get("bereit"), mk.get("startup_fertig")))
    L.append("")
    L.append("-- Wetterlaeufe im Log (Start, Zaehlzeile, Ergebnis je Lauf) --")
    st, zl, er = lg["starts"], lg["zaehlzeilen"], lg["ergebnisse"]
    for k in range(max(len(st), len(zl), len(er))):
        s = st[k] if k < len(st) else None
        z = zl[k] if k < len(zl) else None
        e = er[k] if k < len(er) else None
        L.append("Lauf %d: Start %s (Ausloeser: %s)" % (k + 1, s[0] if s else "?", s[1] if s else "?"))
        if e:
            L.append("   Ergebnis: %s um %s UTC, Dauer %s s%s" % (e["status"], e["zeit"], e["dauer_s"],
                                                              (" | Fehlerklasse %s" % e["fehlerklasse"]) if e["fehlerklasse"] else ""))
            if e["meldung"]:
                L.append("   Meldung: %s" % _kurz_url(e["meldung"]))
        else:
            L.append("   Ergebnis: keine Zeile 'job_run'/'job_error' fuer den Lauf gefunden")
        if z:
            L.append("   Zaehlzeile: %s" % z["zeile"])
        else:
            L.append("   Zaehlzeile: (noch) nicht im Log - Lauf nicht beendet?")
    if len(st) != len(zl):
        L.append("HINWEIS: %d Start-Zeilen, aber %d Zaehlzeilen -> mindestens ein Lauf ist nicht (sichtbar) beendet." % (len(st), len(zl)))
    L.append("")
    L.append("-- Fehlgeschlagene Abrufe je Ort (Zeile 'WARNING <Art> fuer <Ort> fehlgeschlagen') --")
    if lg["fehler_orte"]:
        for f in lg["fehler_orte"]:
            L.append("   %s | %s | %s | Ursache: %s" % (f["zeit"], f["art"], f["ort"], f["ursache"]))
        L.append("   Summe nach Ursache: %s" % dict(Counter(f["ursache"] for f in lg["fehler_orte"])))
    else:
        L.append("   keine")
    L.append("")
    L.append("-- BUG-119: 'Wetter wieder aufgelegt' (Ausloeser, Zahlen, Dauer) --")
    for a in lg["aufleg"] or []:
        L.append("   %s | Ausloeser %s | %d Termine mit gespeichertem Wetter, %d ohne | Dauer %s s" % (a["zeit"], a["ausloeser"], a["mit"], a["ohne"], a["dauer_s"]))
    if not lg["aufleg"]:
        L.append("   keine Zeile gefunden")
    else:
        try:
            gr = max(float(x["dauer_s"].replace(",", ".")) for x in lg["aufleg"])
            L.append("   Laengste Dauer: %.1f s (AK-12: Schwelle 3 s ist laut Ticket nur eine Annahme)" % gr)
        except Exception:
            pass
    L.append("")
    L.append("-- Feed-Cache geladen (Zeile mit 'berechnet') --")
    for g in lg["feed_geladen"] or []:
        L.append("   %s | %d Events | berechnet %s" % (g["zeit"], g["events"], g["berechnet"]))
    if not lg["feed_geladen"]:
        L.append("   keine Zeile gefunden")
    if lg["notbremse"]:
        L.append("")
        L.append("-- Notbremse / Wiederholungsversuch --")
        L.extend("   " + n for n in lg["notbremse"])
    L.append("")
    L.append("Wetterlauf laut Log beendet: %s%s" % ("JA" if lg["beendet"] else "NEIN", " (Wiederholungsversuch noch offen)" if lg.get("retry_offen") else ""))
    return L


# ---- Modus wdh_vorher
def wdh_vorher():
    zeit = stempel()
    jetzt = wdh_jetzt()
    bericht = ["Wiederholungsmessung VORHER  (UTC %s)\nBasis: %s\n" % (zeit, BASIS)]
    warn = []
    print("wdh_vorher: Gesundheits- und Job-Abfrage ...")
    st, sek, body, fehler = http_get("/health")
    h = json_oder_none(body)
    schreiben("wdh_vorher_health.json", body.decode("utf-8", "replace") if body else fehler)
    bericht.append(ausgeben("health (HTTP %s, %.3f s)" % (st, sek), health_kurz(h) or fehler))
    st2, sek2, body2, fehler2 = http_get("/job-status")
    js = json_oder_none(body2)
    schreiben("wdh_vorher_job-status.json", body2.decode("utf-8", "replace") if body2 else fehler2)
    laufend, pre = [], False
    if isinstance(js, dict):
        laufend = wdh_jobs_laufend(js.get("jobs"))
        pre = bool(js.get("precompute_running"))
        bericht.append(ausgeben("job-status (HTTP %s): Jobs im Status running / precompute_running" % st2, {"running": laufend or "keine", "precompute_running": pre}))
    else:
        warn.append("WARNUNG: /job-status nicht lesbar (HTTP %s %s) - laufende Jobs unbekannt." % (st2, fehler2))
        bericht.append(ausgeben("job-status", "HTTP %s %s" % (st2, fehler2)))
    print("wdh_vorher: Feed holen ...")
    liste, kennz = wdh_feed_holen("wdh_vorher_feed.json")
    bericht.append(ausgeben("feed (Kennzahlen)", kennz))
    if liste is not None:
        bericht.append(ausgeben("feed Typ-Quoten (event_type)", wdh_typ_quoten(liste)))
    else:
        warn.append("WARNUNG: Feed konnte nicht geholt werden: %s" % kennz.get("fehler"))
    print("wdh_vorher: Feed-Stand am Server lesen (SSH, nur lesend) ...")
    stand = wdh_stand_holen()
    bericht.append("== feed-Berechnungsstand und Dienst\n" + "\n".join(wdh_stand_zeilen(stand)) + "\n")
    if stand.get("fehler"):
        warn.append("WARNUNG: Berechnungsstand des Feeds nicht lesbar (%s) - Vergleichbarkeit spaeter nicht pruefbar." % stand["fehler"])
    else:
        fd = stand.get("feed_datei") or {}
        g = stand.get("journal_feed_geladen") or []
        if fd.get("computed_at") and g and fd["computed_at"][:16] != g[-1]["berechnet"][:16]:
            warn.append("WARNUNG: Die Feed-DATEI auf der Platte (berechnet %s) ist ein ANDERER Stand als der Feed im ARBEITSSPEICHER (berechnet %s, "
                        "geladen %s). Ein Neustart laedt die Datei -> Vorher und Nachher waeren verschiedene Berechnungsstaende "
                        "(Problem 1 der ersten Messung). Besser warten, bis Datei und Speicher uebereinstimmen." % (fd["computed_at"][:16], g[-1]["berechnet"][:16], g[-1]["zeit"]))
        if not g:
            warn.append("WARNUNG: Kein 'Feed-Cache geladen' im Journal der letzten 3 Tage - Speicher-Stand nicht belegt.")
    plan, w2 = wdh_plan_pruefen(jetzt, laufend, pre)
    warn.extend(w2)
    bericht.append("== Planlaeufe (APScheduler, Berliner Zeit; Fundstellen in Klammern)\n" + "\n".join(plan) + "\n")
    bericht.append("Empfohlenes Fenster fuer den Neustart (Berliner Zeit, je 3-Stunden-Zyklus H = 0, 3, 6, ... 21): fruehestens um H+1:02 "
                   "(Wetterkarte um :39 ist nach 17 bis 23 Minuten fertig); spaetestens um H+2:44 (%.0f min vor H+3:19); "
                   "nicht in der Naehe von 05:30 (Vorberechnung).\n" % WDH_EMPF_MIN)
    stand_datei = {"zeit_utc": jetzt_utc().isoformat(), "stempel": zeit, "warnungen": warn, "stand": stand,
                   "laufende_jobs": laufend, "precompute_running": pre,
                   "feed_kennzahlen": kennz, "feed_typ_quoten": wdh_typ_quoten(liste) if liste is not None else None}
    schreiben("wdh_stand_vorher.json", json.dumps(stand_datei, ensure_ascii=False, indent=2, default=str))
    if warn:
        bericht.append("== ERGEBNIS: %d WARNUNG(EN) - NEUSTART JETZT NICHT EMPFOHLEN\n%s\n" % (len(warn), "\n".join(warn)))
    else:
        bericht.append("== ERGEBNIS: keine Warnung - Neustart kann jetzt erfolgen (danach sofort wdh_nachher starten).\n")
    schreiben("wdh_zusammenfassung_vorher_%s.txt" % zeit, "\n".join(bericht))
    print("\n".join(bericht)[:7000])
    return 3 if warn else 0


def wdh_neustart_per_ssh():
    """Vergleicht den Dienststart laut SSH mit dem in wdh_stand_vorher.json. Gibt (bewiesen?, Text) zurueck."""
    try:
        with open(os.path.join(OUT, "wdh_stand_vorher.json"), encoding="utf-8") as fh:
            vor = ((json.load(fh).get("stand")) or {}).get("dienst_aktiv_seit_utc")
    except Exception as e:
        return False, "wdh_stand_vorher.json nicht lesbar (%s: %s)" % (type(e).__name__, e)
    if not vor:
        return False, "in wdh_stand_vorher.json steht kein Dienststart"
    jetzt = wdh_stand_holen()
    if jetzt.get("fehler"):
        return False, "SSH-Pruefung nicht moeglich: %s" % jetzt["fehler"]
    neu = jetzt.get("dienst_aktiv_seit_utc")
    if not neu:
        return False, "SSH lieferte keinen Dienststart"
    if neu == vor:
        return False, "Dienst laeuft weiter seit %s UTC - derselbe Start wie bei wdh_vorher" % neu
    return True, "Dienst startete laut SSH um %s UTC (bei wdh_vorher: %s UTC)" % (neu, vor)


# ---- Modus wdh_beobachten
def wdh_beobachten(max_min):
    name = "wdh_beobachten_%s.txt" % stempel()
    pfad = os.path.join(OUT, name)
    t_ende = time.monotonic() + max_min * 60
    ausfall = False
    zurueck = None
    lauf_gesehen = False
    ruhe_seit = None
    nachstart_gespeichert = False
    ausfall_502 = False
    grund = "Zeitlimit erreicht"
    print("Beobachte (alle %g s, ab %g s nach 'Server wieder da' alle %g s) bis Wetterlauf-Ende, hoechstens %g min -> %s  (Abbruch: Strg+C)" % (
        WDH_TAKT_SCHNELL, WDH_SCHNELL_NACH_START_S, WDH_TAKT_LANGSAM, max_min, pfad))
    with open(pfad, "w", encoding="utf-8") as f:
        f.write("zeit_utc\ttakt_s\thealth_http\thealth_sek\thealth_status\twetter_job\twetter_job_last_run\tkarte_job\tlaufende_jobs\t"
                "feed_http\tfeed_sek\tfeed_gesamt\tab70_heute\tab70_morgen\twetter_ok_naechste3tage_ab70\twetter_andere_naechste3tage_ab70\tbesondere_ids\tfehler\n")
        f.flush()

        def ereignis(text):
            zeile = "# %s UTC  %s" % (jetzt_utc().strftime("%H:%M:%S"), text)
            f.write(zeile + "\n")
            f.flush()
            print(zeile)
        try:
            while time.monotonic() < t_ende:
                t0 = time.monotonic()
                st, sek, body, fehler = http_get("/health", timeout=30)
                h = json_oder_none(body) if st == 200 else None
                hk = health_kurz(h)
                jobs = (h or {}).get("jobs") or {}
                wj = (jobs.get("weather") or {}).get("status")
                karte = (jobs.get("weather-map") or {}).get("status")
                laufend = wdh_jobs_laufend(jobs)
                fs, fsek, fbody, ffehler = http_get(FEED_PFAD, timeout=60)
                liste = json_oder_none(fbody) if fs == 200 else None
                k = feed_auswerten(liste) if isinstance(liste, list) else {}
                jetzt = time.monotonic()
                if st == 502:
                    ausfall_502 = True
                if st != 200:
                    if not ausfall or zurueck is not None:
                        ereignis("Server nicht erreichbar (HTTP %s) - Neustart erkannt" % st)
                    ausfall, zurueck, lauf_gesehen, ruhe_seit = True, None, False, None
                    nachstart_gespeichert = False
                elif ausfall and zurueck is None:
                    zurueck = jetzt
                    ereignis("Server wieder erreichbar (Wetter-Job: %s)" % wj)
                if zurueck is not None and not nachstart_gespeichert and isinstance(liste, list):
                    schreiben("wdh_nachstart_feed.json", json.dumps(liste, ensure_ascii=False))
                    nachstart_gespeichert = True
                    ereignis("erster Feed nach dem Neustart gespeichert (%d Eintraege)" % len(liste))
                takt = WDH_TAKT_LANGSAM if (zurueck is not None and jetzt - zurueck >= WDH_SCHNELL_NACH_START_S) else WDH_TAKT_SCHNELL
                w3 = k.get("wetter_etikett_der_chancen_ab_70_naechste_3_tage", {})
                zeile = [jetzt_utc().strftime("%H:%M:%S"), "%g" % takt, st, "%.3f" % sek, hk.get("status"), wj, hk.get("wetter_job_last_run"), karte,
                         ",".join(laufend), fs, "%.3f" % fsek, k.get("gesamt"), k.get("chancen_ab_70_heute"), k.get("chancen_ab_70_morgen"),
                         (w3.get("ok", 0) if k else None), (sum(v for a, v in w3.items() if a != "ok") if k else None),
                         k.get("besondere_ereignisse_ids_gc_rs_rc"), (fehler or ffehler)]
                f.write("\t".join("" if v is None else str(v) for v in zeile) + "\n")
                f.flush()
                # Ende des Wetterlaufs nach dem Neustart
                if zurueck is not None and st == 200:
                    if wj == "running":
                        if not lauf_gesehen:
                            ereignis("Wetterlauf laeuft (Status running)")
                        lauf_gesehen, ruhe_seit = True, None
                    else:
                        if ruhe_seit is None and (lauf_gesehen or jetzt - zurueck >= max(WDH_RUHE_S, 120.0)):
                            ruhe_seit = jetzt
                            ereignis("Wetter-Job nicht mehr 'running' (Status %s, %s)" % (wj, "Lauf war gesehen" if lauf_gesehen else "Lauf nie als running gesehen - sehr kurz?"))
                        if ruhe_seit is not None and jetzt - ruhe_seit >= WDH_RUHE_S:
                            grund = "Wetterlauf beendet (Status %s, seit %.0f s kein neuer Lauf)" % (wj, jetzt - ruhe_seit)
                            ereignis(grund)
                            break
                rest = takt - (time.monotonic() - t0)
                if rest > 0:
                    time.sleep(rest)
        except KeyboardInterrupt:
            grund = "abgebrochen (Strg+C)"
            ereignis(grund)
        if grund == "Zeitlimit erreicht":
            ereignis(grund + " - Ende der Beobachtung, Wetterlauf-Ende nicht gesehen")
        neustart = ausfall_502
        if neustart:
            ereignis("Neustart erkannt: HTTP 502 gesehen")
        else:
            print("Keine Zeile mit HTTP 502 gesehen - pruefe per SSH, ob der Dienst seit wdh_vorher neu gestartet wurde ...")
            neustart, text = wdh_neustart_per_ssh()
            if neustart:
                ereignis("Neustart erkannt: " + text)
        if not neustart:
            ereignis("WARNUNG: %s (%s)" % (KEIN_NEUSTART, text))
    print("fertig:", pfad)
    return 0 if neustart else 3


# ---- Modus wdh_nachher
def wdh_nachher():
    zeit = stempel()
    t_start = time.monotonic()
    t_max = t_start + WDH_MAX_MIN * 60
    pfad_stand = os.path.join(OUT, "wdh_stand_vorher.json")
    try:
        with open(pfad_stand, encoding="utf-8") as fh:
            vor = json.load(fh)
    except Exception as e:
        print("FEHLER: wdh_stand_vorher.json fehlt/unlesbar (%s). Zuerst 'wdh_vorher' ausfuehren." % e)
        return 2
    vor_stand = vor.get("stand") or {}
    print("wdh_nachher: pruefe per SSH, ob seit 'wdh_vorher' ein Neustart stattfand ...")
    jetzt_stand = wdh_stand_holen()
    if jetzt_stand.get("fehler"):
        print("FEHLER: SSH-Stand nicht lesbar: %s" % jetzt_stand["fehler"])
        return 2
    if vor_stand.get("dienst_aktiv_seit_utc") and vor_stand.get("dienst_aktiv_seit_utc") == jetzt_stand.get("dienst_aktiv_seit_utc") \
            and os.environ.get("FA_WDH_OHNE_NEUSTART") != "1":
        print(KEIN_NEUSTART)
        print("FEHLER: Dienst laeuft seit %s UTC - derselbe Start wie bei 'wdh_vorher'. Es fand kein Neustart statt. "
              "(Zum Testen ohne Neustart: FA_WDH_OHNE_NEUSTART=1)" % jetzt_stand.get("dienst_aktiv_seit_utc"))
        return 2
    neustart_belegt = bool(vor_stand.get("dienst_aktiv_seit_utc") and jetzt_stand.get("dienst_aktiv_seit_utc")
                           and vor_stand["dienst_aktiv_seit_utc"] != jetzt_stand["dienst_aktiv_seit_utc"])
    if not neustart_belegt:
        print("WARNUNG: " + KEIN_NEUSTART + " (Dienststart laut SSH nicht als neu belegt; Messung laeuft trotzdem weiter)")
    # ---- Warten bis Wetterlauf beendet (Status aus /job-status), dann Gegenprobe im Server-Log
    ereignisse = []

    def ereignis(t):
        z = "%s UTC  %s" % (jetzt_utc().strftime("%H:%M:%S"), t)
        ereignisse.append(z)
        print(z)

    zurueck = None
    lauf_gesehen = False
    ruhe_seit = None
    letzter_status = None
    ende_http = None
    lg = None
    log_text = ""
    zeitlimit = False
    print("wdh_nachher: warte auf das Ende des Wetterlaufs (hoechstens %.0f min, Abfrage alle %.0f s) ..." % (WDH_MAX_MIN, WDH_WARTE_TAKT))
    while True:
        if time.monotonic() > t_max:
            zeitlimit = True
            ereignis("Zeitlimit (%.0f min) erreicht - Wetterlauf-Ende nicht bestaetigt" % WDH_MAX_MIN)
            break
        st, sek, body, fehler = http_get("/job-status", timeout=30)
        js = json_oder_none(body) if st == 200 else None
        jetzt = time.monotonic()
        if isinstance(js, dict):
            if zurueck is None:
                zurueck = jetzt
                ereignis("Server antwortet (/job-status)")
            w = (js.get("jobs") or {}).get("weather") or {}
            letzter_status = w.get("status")
            if letzter_status == "running":
                if not lauf_gesehen:
                    ereignis("Wetterlauf laeuft (Status running)")
                lauf_gesehen, ruhe_seit = True, None
            elif ruhe_seit is None and (lauf_gesehen or jetzt - zurueck >= max(WDH_RUHE_S, 120.0)):
                ruhe_seit = jetzt
                ereignis("Wetter-Job nicht mehr 'running' (Status %s%s)" % (letzter_status, "" if lauf_gesehen else ", nie als running gesehen - sehr kurz?"))
            if ruhe_seit is not None and jetzt - ruhe_seit >= WDH_RUHE_S:
                ende_http = jetzt_utc()
                ereignis("kein Wetterlauf mehr seit %.0f s (Status %s) - pruefe das Server-Log" % (jetzt - ruhe_seit, letzter_status))
                rc, out, err = wdh_ssh(REMOTE_WDH_LOG.replace("__VORLAUF__", str(WDH_LOG_VORLAUF_S)))
                log_text = out
                lg = wdh_log_auswerten(out)
                if lg.get("fehler") or (rc != 0 and not out):
                    ereignis("Server-Log nicht lesbar (%s) - Ende nur per HTTP belegt" % (lg.get("fehler") or err.strip()[:150]))
                    break
                if lg["beendet"]:
                    ereignis("Server-Log bestaetigt: %d Wetterlauf/-laeufe beendet" % len(lg["starts"]))
                    break
                ereignis("Server-Log: Lauf noch nicht beendet (Starts %d, Zaehlzeilen %d%s) - warte weiter" % (
                    len(lg["starts"]), len(lg["zaehlzeilen"]), ", Wiederholungsversuch offen" if lg.get("retry_offen") else ""))
                ruhe_seit = None
                lauf_gesehen = lauf_gesehen or bool(lg["starts"])
        else:
            if zurueck is not None:
                ereignis("Server nicht erreichbar (HTTP %s) - warte" % st)
            zurueck, lauf_gesehen, ruhe_seit = None, False, None
        time.sleep(WDH_WARTE_TAKT)
    # ---- zweiter Schnappschuss
    print("wdh_nachher: Schnappschuss nach Lauf-Ende ...")
    bericht = ["Wiederholungsmessung NACHHER  (UTC %s)\nBasis: %s\n" % (zeit, BASIS)]
    if not neustart_belegt:
        bericht.append("== WARNUNG: %s\n(Dienststart vorher: %s, jetzt: %s)\n" % (
            KEIN_NEUSTART, vor_stand.get("dienst_aktiv_seit_utc"), jetzt_stand.get("dienst_aktiv_seit_utc")))
    bericht.append("== Ablauf\n" + "\n".join(ereignisse) + "\n")
    st, sek, body, fehler = http_get("/health")
    h = json_oder_none(body)
    schreiben("wdh_nachher_health.json", body.decode("utf-8", "replace") if body else fehler)
    bericht.append(ausgeben("health (HTTP %s, %.3f s)" % (st, sek), health_kurz(h) or fehler))
    st2, sek2, body2, fehler2 = http_get("/job-status")
    js = json_oder_none(body2)
    schreiben("wdh_nachher_job-status.json", body2.decode("utf-8", "replace") if body2 else fehler2)
    if isinstance(js, dict):
        lf = wdh_jobs_laufend(js.get("jobs"))
        bericht.append(ausgeben("job-status (HTTP %s): Jobs im Status running beim Schnappschuss" % st2, {"running": lf or "keine", "precompute_running": js.get("precompute_running")}))
        if lf:
            bericht.append("HINWEIS: Beim Schnappschuss laufen noch Jobs (%s). Typisch: Wetterkarte (~17-23 min nach Neustart). "
                           "Sie aendern den Feed nicht, verfaelschen aber Antwortzeiten.\n" % ", ".join(lf))
    liste_n, kennz_n = wdh_feed_holen("wdh_nachher_feed.json")
    bericht.append(ausgeben("feed nachher (Kennzahlen)", kennz_n))
    if liste_n is not None:
        bericht.append(ausgeben("feed nachher Typ-Quoten", wdh_typ_quoten(liste_n)))
    stand_n = wdh_stand_holen()
    bericht.append("== feed-Berechnungsstand und Dienst (nachher)\n" + "\n".join(wdh_stand_zeilen(stand_n)) + "\n")
    # ---- Berechnungsstaende
    zeilen = []
    fdv = (vor_stand.get("feed_datei") or {})
    gv = (vor_stand.get("journal_feed_geladen") or [])
    fdn = (stand_n.get("feed_datei") or {})
    gl = (lg or {}).get("feed_geladen") or []
    staende = [("vorher: Datei (computed_at)", fdv.get("computed_at")),
               ("vorher: Speicher (letztes 'Feed-Cache geladen')", gv[-1]["berechnet"] if gv else None),
               ("nachher: erstes 'Feed-Cache geladen' nach Neustart", gl[0]["berechnet"] if gl else None),
               ("nachher: letztes 'Feed-Cache geladen' im Log", gl[-1]["berechnet"] if gl else None),
               ("nachher: Datei (computed_at)", fdn.get("computed_at"))]
    werte = [(n, v[:16] if v else None) for n, v in staende]
    for n, v in staende:
        zeilen.append("   %-52s %s" % (n, v))
    fehlend = [n for n, v in werte if v is None]
    verschieden = sorted(set(v for n, v in werte if v))
    if fehlend:
        urteil = "NICHT BELEGT (fehlt: %s)" % "; ".join(fehlend)
    elif len(verschieden) == 1:
        urteil = "JA - alle fuenf Angaben zeigen denselben Stand (%s)" % verschieden[0]
    else:
        urteil = "NEIN - verschiedene Staende: %s -> Vorher/Nachher NICHT streng vergleichbar" % ", ".join(verschieden)
    bericht.append("== Gleiche Berechnungsstaende (auf die Minute)?  %s\n%s\n" % (urteil, "\n".join(zeilen)))
    # ---- Vergleiche
    bezug = jetzt_utc()
    liste_v = None
    try:
        with open(os.path.join(OUT, "wdh_vorher_feed.json"), encoding="utf-8") as fh:
            liste_v = json.load(fh)
    except Exception as e:
        bericht.append("== Vergleich: wdh_vorher_feed.json nicht lesbar (%s)\n" % e)
    liste_s = None
    p_s = os.path.join(OUT, "wdh_nachstart_feed.json")
    try:
        t_vor = parse_zeit(vor["zeit_utc"]).timestamp()
        if os.path.getmtime(p_s) >= t_vor:
            with open(p_s, encoding="utf-8") as fh:
                liste_s = json.load(fh)
    except Exception:
        liste_s = None
    if liste_n is not None and liste_v is not None:
        bericht.append("== Vergleich VORHER -> NACHHER (eintragsweise nach id)\n" + "\n".join(wdh_feed_vergleich(liste_v, liste_n, "vorher", "nachher", bezug)) + "\n")
    if liste_n is not None and liste_s is not None and liste_v is not None:
        bericht.append("== Vergleich VORHER -> NACH-START (erster Feed nach dem Neustart, aus wdh_beobachten)\n" + "\n".join(wdh_feed_vergleich(liste_v, liste_s, "vorher", "nach-start", bezug)) + "\n")
        bericht.append("== Vergleich NACH-START -> NACHHER (was aendert der Wetterlauf?)\n" + "\n".join(wdh_feed_vergleich(liste_s, liste_n, "nach-start", "nachher", bezug)) + "\n")
    elif liste_s is None:
        bericht.append("== Nach-Start-Feed: nicht vorhanden/veraltet (wdh_beobachten lief nicht oder hat den Neustart nicht gesehen) - nur Vorher/Nachher verglichen\n")
    # ---- Server-Log
    if lg is not None:
        schreiben("wdh_server_log_ab_neustart.txt",
                  "# Journal des Dienstes fotoalert ab %s (UTC) bis Ende des Wetterlaufs; HTTP-Request-Zeilen (%s Stueck) entfernt\n%s\n" % (
                      lg.get("seit"), lg.get("http_zeilen_ausgelassen"), "\n".join(lg["zeilen_bis_ende"])))
        bericht.append("== Server-Log ab Neustart (lesend gezogen, ohne HTTP-Request-Zeilen)\n" + "\n".join(wdh_log_zeilen(lg)) + "\n")
    else:
        bericht.append("== Server-Log: nicht gezogen (Wetterlauf-Ende per HTTP nicht erreicht)\n")
    if zeitlimit:
        bericht.append("ACHTUNG: Zeitlimit erreicht, der Wetterlauf war nicht nachweislich beendet - Feed-Schnappschuss ist KEIN Stand nach Lauf-Ende.\n")
    if not neustart_belegt:
        bericht.append("WARNUNG: " + KEIN_NEUSTART + "\n")
    schreiben("wdh_zusammenfassung_nachher_%s.txt" % zeit, "\n".join(bericht))
    print("\n".join(bericht)[:9000])
    if not neustart_belegt:
        print("WARNUNG: " + KEIN_NEUSTART)
        return 3
    return 1 if zeitlimit else 0


# ---------------------------------------------------------------- BUG-123: Antwortzeiten nach dem Neustart (nur GET)
B123_TAKT_S = float(os.environ.get("FA_B123_TAKT_S", "2"))
B123_DAUER_S = float(os.environ.get("FA_B123_DAUER_S", "600"))
B123_KONTROLLE = os.environ.get("FA_B123_KONTROLLE") == "1"
B123_TIMEOUT_S = 60
B123_PARALLEL_KALENDER = 3          # gleichzeitige Kalender-Abrufe im ersten Takt nach "wieder erreichbar"
B123_PFADE_FEST = ["/health", "/job-status", "/", FEED_PFAD, "/weather-map?hours=72"]   # Statusabfrage, Jobs, Startseite, Feed, Karte
B123_GEHEIM_NAME = re.compile(r"(PASS|SECRET|TOKEN|KEY|PWD)", re.I)
B123_GEHEIM_ZUWEISUNG = re.compile(r"(?i)((?:pass\w*|secret\w*|token\w*|api[_-]?key\w*|pwd)\s*[=:]\s*)\S+")


def b123_geheimnisse_entfernen(text):
    """Schwaerzt Werte von Umgebungseinstellungen mit Namen wie *PASS*/*SECRET*/*TOKEN*/*KEY* und Zuweisungen dieser Art
    (AK-10): Ausgabe und Dateien dieses Modus duerfen nie ein Geheimnis enthalten."""
    for name, wert in os.environ.items():
        if B123_GEHEIM_NAME.search(name) and len(wert) >= 6:
            text = text.replace(wert, "***")
    return B123_GEHEIM_ZUWEISUNG.sub(lambda m: m.group(1) + "***", text)


def b123_kalender_pfad():
    heute = datetime.now()
    return "/calendar?month=%d&year=%d" % (heute.month, heute.year)


B123_DIENST_SKRIPT = "systemctl show fotoalert -p ActiveEnterTimestamp -p MainPID --no-pager"   # nur lesend


def b123_dienststand_lesen():
    """Liest per lesendem SSH Startzeitpunkt und Hauptprozess des Dienstes. None = nicht lesbar (nie raten)."""
    try:
        rc, out, _err = wdh_ssh(B123_DIENST_SKRIPT, timeout=40)
    except Exception:
        return None
    if rc != 0 or not out:
        return None
    werte = {}
    for zeile in out.splitlines():
        if "=" in zeile:
            k, v = zeile.split("=", 1)
            werte[k.strip()] = v.strip()
    if "MainPID" not in werte or "ActiveEnterTimestamp" not in werte:
        return None
    return (werte["ActiveEnterTimestamp"], werte["MainPID"])


def b123_neustart_urteil(vorher, jetzt):
    """'ja' nur, wenn Startzeitpunkt oder Hauptprozess belegt anders sind; 'nein' wenn gleich;
    'nicht pruefbar', wenn einer der beiden Staende fehlt."""
    if vorher is None or jetzt is None:
        return "nicht pruefbar"
    return "nein" if vorher == jetzt else "ja"


def b123_messen(pfad, zeile_schreiben):
    t_zeit = jetzt_utc().strftime("%H:%M:%S")
    st, sek, _body, _fehler = http_get(pfad, timeout=B123_TIMEOUT_S)
    zeile_schreiben(t_zeit, pfad, st, sek)
    return st, sek


def bug123():
    import threading
    pfad_csv = os.path.join(OUT, "bug123_%s.csv" % stempel())
    sperre = threading.Lock()
    groesste = {}
    datei = open(pfad_csv, "w", encoding="utf-8", newline="")
    datei.write("zeit,pfad,status,dauer_s\n")
    datei.flush()

    def zeile_schreiben(zeit, pfad, status, sek):
        with sperre:
            datei.write("%s,%s,%s,%.3f\n" % (zeit, pfad.replace(",", "%2C"), status, sek))
            datei.flush()
            groesste[pfad] = max(groesste.get(pfad, 0.0), sek)

    kal = b123_kalender_pfad()
    print("Messung BUG-123: Takt %g s, Dauer %g s%s -> %s  (nur lesende Abrufe, Abbruch: Strg+C)" % (
        B123_TAKT_S, B123_DAUER_S, ", Kontrollmessung ohne Neustart" if B123_KONTROLLE else "", pfad_csv))
    if not B123_KONTROLLE:
        print("Jetzt den Neustart auf dem Server ausloesen (macht Stephan selbst, nie dieses Skript).")
    threads = []
    ausfall, zurueck_gesehen = False, False
    stand_start = b123_dienststand_lesen()       # Startzeitpunkt/Hauptprozess des Dienstes vor der Messung (lesendes SSH)
    neustart_urteil = "nicht pruefbar" if stand_start is None else "nein"
    langsam_gemeldet = False
    t_ende = time.monotonic() + B123_DAUER_S
    takt = 0
    try:
        while time.monotonic() < t_ende:
            t0 = time.monotonic()
            takt += 1
            # Statusabfrage zuerst und gleich ausgewertet: so ist "wieder erreichbar" schon in diesem Takt bekannt
            st, _sek = b123_messen("/health", zeile_schreiben)
            burst = 0
            if st != 200:
                if not ausfall:
                    # Neustart nur melden, wenn er per lesendem SSH belegt ist (anderer Startzeitpunkt/Hauptprozess)
                    urteil = b123_neustart_urteil(stand_start, b123_dienststand_lesen())
                    zeit_txt = jetzt_utc().strftime("%H:%M:%S")
                    if urteil == "ja":
                        print("# %s UTC  Server nicht erreichbar (HTTP %s) - Neustart erkannt" % (zeit_txt, st))
                        ausfall = True
                        neustart_urteil = "ja"
                    elif urteil == "nein":
                        if not langsam_gemeldet:
                            print("# %s UTC  /health antwortet nicht rechtzeitig (HTTP %s, kein Neustart belegt)" % (zeit_txt, st))
                            langsam_gemeldet = True
                    else:
                        if not langsam_gemeldet:
                            print("# %s UTC  /health antwortet nicht (HTTP %s) - Neustart nicht belegbar (SSH-Stand nicht lesbar)" % (zeit_txt, st))
                            langsam_gemeldet = True
            else:
                langsam_gemeldet = False
            if st == 200 and ausfall and not zurueck_gesehen:
                zurueck_gesehen = True
                burst = B123_PARALLEL_KALENDER
                print("# %s UTC  Server wieder erreichbar - %d gleichzeitige Kalender-Abrufe" % (jetzt_utc().strftime("%H:%M:%S"), burst))
            anzahl_kalender = burst if burst else 1
            ziele = [p for p in B123_PFADE_FEST if p != "/health"] + [kal] * anzahl_kalender
            for pfad in ziele:
                t = threading.Thread(target=b123_messen, args=(pfad, zeile_schreiben), daemon=True)
                t.start()
                threads.append(t)
            rest = B123_TAKT_S - (time.monotonic() - t0)
            if rest > 0:
                time.sleep(rest)
    except KeyboardInterrupt:
        print("Abgebrochen (Strg+C) - bisherige Messwerte werden ausgewertet.")
    for t in threads:
        t.join(timeout=B123_TIMEOUT_S + 5)
    with sperre:
        datei.close()
    # Dienst-Protokoll (lesendes SSH, mit Zeitstempeln) als Textdatei im Ausgabeordner
    rc, out, err = wdh_ssh(REMOTE_WDH_LOG.replace("__VORLAUF__", str(WDH_LOG_VORLAUF_S)), timeout=120)
    protokoll = b123_geheimnisse_entfernen(out or "") if rc == 0 else \
        b123_geheimnisse_entfernen("Dienst-Protokoll nicht lesbar (SSH-Rueckgabe %s): %s" % (rc, (err or "")[-300:]))
    pfad_log = os.path.join(OUT, "bug123_dienst_protokoll_%s.txt" % stempel())
    with open(pfad_log, "w", encoding="utf-8") as f:
        f.write(protokoll)
    rechnungen = len(re.findall(r"BUG-123 Monatsrechnung gestartet", protokoll))
    print("")
    print("Schlusszusammenfassung - groesster Wert je Abfrage (Sekunden):")
    for pfad in sorted(groesste):
        print("  %s  %.3f s" % (b123_geheimnisse_entfernen(pfad), groesste[pfad]))
    print("Messdatei: %s" % pfad_csv)
    print("Dienst-Protokoll: %s  (Monatsrechnungen mit Startzeile: %d)" % (pfad_log, rechnungen))
    if neustart_urteil != "ja" and stand_start is not None:
        # auch ein Neustart, den /health nie als Fehler gezeigt hat, wird belegt (anderer Startzeitpunkt/Hauptprozess)
        neustart_urteil = b123_neustart_urteil(stand_start, b123_dienststand_lesen())
    print("Ereignis: Neustart belegt: %s" % neustart_urteil.replace("pruefbar", "prüfbar"))
    if not B123_KONTROLLE and not zurueck_gesehen:
        print("Hinweis: " + KEIN_NEUSTART)
    return 0


def serverpruefung():
    """Technische Sperre: auf dem Server (Verzeichnis /opt/fotoalert vorhanden) nicht laufen. True = Abbruch noetig."""
    if SERVERCHECK_AUS or not os.path.isdir(SERVER_PFAD):
        return False
    print("Dies ist der Server – dieses Skript gehört auf den Mac.\n"
          "(Verzeichnis %s existiert. Das Skript holt die Serverdaten selbst per SSH vom Mac aus.)" % SERVER_PFAD, file=sys.stderr)
    return True


def standard_ausgabeordner(tag=None):
    return os.path.join(PROJEKT, "_to_delete", "messung_" + (tag or datetime.now()).strftime("%Y-%m-%d"))


def ausgabeordner_bestimmen(modus, option):
    """Rangfolge: Option --ausgabe, Umgebungsvariable FA_OUT, Standard _to_delete/messung_<Datum>. Gibt (Pfad, Herkunft) zurueck."""
    if option:
        return option, "Option --ausgabe"
    if os.environ.get("FA_OUT"):
        return os.environ["FA_OUT"], "Umgebungsvariable FA_OUT"
    heute = standard_ausgabeordner()
    if modus in ("wdh_beobachten", "wdh_nachher") and not os.path.isfile(os.path.join(heute, "wdh_stand_vorher.json")):
        gestern = standard_ausgabeordner(datetime.now() - timedelta(days=1))
        if os.path.isfile(os.path.join(gestern, "wdh_stand_vorher.json")):
            return gestern, "Standard (Ordner von gestern, weil dort wdh_vorher lief)"
    return heute, "Standard"


def optionen_lesen(argv):
    """Trennt --ausgabe ORDNER / --ausgabe=ORDNER von den uebrigen Argumenten. Gibt (rest, ausgabe) zurueck; ausgabe False = Wert fehlt."""
    rest, ausgabe, i = [], None, 0
    while i < len(argv):
        a = argv[i]
        if a == "--ausgabe":
            if i + 1 >= len(argv):
                return rest, False
            ausgabe, i = argv[i + 1], i + 2
        elif a.startswith("--ausgabe="):
            ausgabe, i = a.split("=", 1)[1], i + 1
        else:
            rest.append(a)
            i += 1
    return rest, ausgabe


def main():
    global OUT
    if serverpruefung():
        return 2
    args, ausgabe = optionen_lesen(sys.argv[1:])
    modi = ("vorher", "nachher", "beobachten", "bug117", "wdh_vorher", "wdh_beobachten", "wdh_nachher", "bug123")
    if ausgabe is False:
        print("FEHLER: Option --ausgabe braucht einen Ordner.")
        return 2
    if not args or args[0] not in modi:
        print(__doc__)
        return 2
    modus = args[0]
    OUT, herkunft = ausgabeordner_bestimmen(modus, ausgabe)
    try:
        os.makedirs(OUT, exist_ok=True)
    except OSError as e:
        print("FEHLER: Ausgabeordner %s nicht anlegbar: %s" % (OUT, e))
        return 2
    print("Ausgabeordner (%s): %s" % (herkunft, OUT))
    if modus == "beobachten":
        minuten = float(args[1]) if len(args) > 1 else 5
        abstand = float(args[2]) if len(args) > 2 else 3
        beobachten(minuten, abstand)
    elif modus == "wdh_vorher":
        return wdh_vorher()
    elif modus == "wdh_beobachten":
        return wdh_beobachten(float(args[1]) if len(args) > 1 else WDH_MAX_MIN)
    elif modus == "wdh_nachher":
        return wdh_nachher()
    elif modus == "bug123":
        return bug123()
    elif modus == "vorher":
        snapshot("vorher", os.environ.get("FA_SEIT", "3 days ago"))
    elif modus == "nachher":
        seit = os.environ.get("FA_SEIT", "3 days ago")
        snapshot("nachher", seit)
    else:
        text = server_holen("nur_server_" + stempel(), os.environ.get("FA_SEIT", "3 days ago"))
        print(ausgeben("server", server_auswerten(text)))
        print(planlauf_anteil_zeile(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
