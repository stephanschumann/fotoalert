"""BUG-123 · T-12 (AK-10): Der neue Messmodus für die Zeit nach dem Neustart gibt keine Geheimnisse preis.

Testfall der Spec in BACKLOG.md (Abschnitt „Analyse & Spec (BUG-123)“, Testfall-Liste T-12). Die Spec sagt „mit gültigen
Zugangsdaten“; festgelegt (2026-11-22): Der Modus braucht keine Zugangsdaten (nur lesende Abrufe ohne Anmeldung),
geprüft wird deshalb „mit gesetzten Geheimnissen in der Umgebung“.

Test-Agent (Orchestrator Phase 3), geschrieben VOR der Umsetzung, Nachbesserung 2026-11-22 (Versuch 2).

Isolation: kein echtes Netz, kein echtes SSH. Eine kleine Übungs-Gegenstelle auf dem eigenen Rechner beantwortet die
Abfragen des Modus; das SSH-Programm ist durch eine Attrappe ersetzt, die ein festes Übungs-Protokoll liefert; alles,
was der Modus schreibt, landet in einem Wegwerf-Ordner. Die Geheimnisse sind erfundene, eindeutige Platzhalter-Werte.
"""
# ───────────────────────────────────────────────────────────────────────────────
# Technik (Schicht 3/4), bewusst außerhalb der Fachsprache:
#  - Aufruf (Festlegung 2026-11-22): python3 tools/live_messung.py bug123 --ausgabe <Ordner>; nur lesend (GET);
#    erste Ausgabezeile „Ausgabeordner (<Pfad>)“; Messdatei bug123_<Zeitstempel>.csv mit Spalten zeit, pfad, status,
#    dauer_s; am Ende eine Schlusszusammenfassung mit dem größten Wert je Abfrage; Takt/Dauer über die Umgebungswerte
#    FA_B123_TAKT_S (Standard 2) und FA_B123_DAUER_S (Standard 600); das Dienst-Protokoll holt der Modus per lesendem
#    SSH und legt es im Ausgabeordner ab.
#  - Test-Schalter des Werkzeugs: FA_LIVE_MESSUNG_SERVERCHECK_AUS, FA_BASE_URL, FA_SSH_BIN, FA_SSH_ZIEL.
# ───────────────────────────────────────────────────────────────────────────────
import csv
import json
import os
import re
import stat
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

WERKZEUG = Path(__file__).resolve().parents[2] / "tools" / "live_messung.py"
PROTOKOLL_MARKE = "T123-PROTOKOLLZEILE-eindeutig"

# Erfundene Platzhalter-Geheimnisse: Name der Einstellung -> eindeutiger Wert
GEHEIMNISSE = {
    "FOTOALERT_HOST_PASSWORD": "T123-GEHEIM-host-pw-7f3a9c41",
    "FOTOALERT_USER_PASSWORD": "T123-GEHEIM-user-pw-2b8e5d10",
    "FOTOALERT_AUTH_SECRET": "T123-GEHEIM-auth-secret-9c4d7a62",
    "FA_UEBUNG_API_KEY": "T123-GEHEIM-api-key-5e1f8b33",
    "FA_UEBUNG_TOKEN": "T123-GEHEIM-token-a60c2d97",
}


# ═══════════════════════════ Übungswelt und Treiber ═══════════════════════════
class _Gegenstelle(object):
    """Kleine Übungs-Gegenstelle auf dem eigenen Rechner: beantwortet jede Abfrage mit einer kleinen, gültigen Antwort
    und merkt sich Art und Pfad jeder Anfrage."""

    def __init__(self):
        self.anfragen = []      # (Art, Pfad)
        gegenstelle = self

        class _Behandler(BaseHTTPRequestHandler):
            def _antworten(self):
                gegenstelle.anfragen.append((self.command, self.path))
                body = json.dumps({"status": "ok", "opportunities": [], "jobs": {}, "events": []}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)

            do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = _antworten

            def log_message(self, *a):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Behandler)
        self.url = "http://127.0.0.1:%d" % self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *a):
        self.server.shutdown()
        self.server.server_close()


def _messlauf(tmp_path, gegenstelle_url, dauer_s="3", takt_s="1"):
    """Lässt den Messmodus mit gesetzten Geheimnissen bis zum regulären Ende laufen.
    Gibt (Rückgabecode, Ausgabe, Ausgabeordner) zurück."""
    ssh_attrappe = tmp_path / "ssh_attrappe.sh"
    ssh_attrappe.write_text('#!/bin/sh\ncat > /dev/null\necho "%s"\n' % PROTOKOLL_MARKE, encoding="utf-8")
    ssh_attrappe.chmod(ssh_attrappe.stat().st_mode | stat.S_IXUSR)
    ausgabe = tmp_path / "ausgabe"
    env = dict(os.environ)
    env.update(GEHEIMNISSE)
    env.update({
        "FA_SSH_BIN": str(ssh_attrappe),
        "FA_SSH_ZIEL": "attrappe",
        "FA_LIVE_MESSUNG_SERVERCHECK_AUS": "1",
        "FA_BASE_URL": gegenstelle_url,
        "FA_B123_DAUER_S": dauer_s,
        "FA_B123_TAKT_S": takt_s,
    })
    p = subprocess.run([sys.executable, "-u", str(WERKZEUG), "bug123", "--ausgabe", str(ausgabe)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=env, timeout=90)
    return p.returncode, p.stdout + p.stderr, ausgabe


def _alle_dateien_als_text(ordner):
    texte = {}
    if ordner.exists():
        for f in sorted(ordner.rglob("*")):
            if f.is_file():
                texte[f.name] = f.read_bytes().decode("utf-8", "replace")
    return texte


def _gefundene_geheimnisse(ausgabe_text, dateien):
    """Namen aller Einstellungen, deren Wert irgendwo in Ausgabe oder Dateien steht."""
    gesamt = ausgabe_text + "\n" + "\n".join(dateien.values())
    return sorted(name for name, wert in GEHEIMNISSE.items() if wert in gesamt)


def _messzeilen(dateien):
    """Zeilen der Messdatei als Liste von Wörterbüchern (leer, wenn es keine Messdatei gibt)."""
    namen = [n for n in dateien if re.match(r"^bug123_.+\.csv$", n)]
    if not namen:
        return []
    return list(csv.DictReader(dateien[namen[0]].splitlines()))


def _zahlen(zeile):
    return [float(z.replace(",", ".")) for z in re.findall(r"\d+(?:[.,]\d+)?", zeile)]


def _luecken_im_messlauf(ausgabe_text, dateien):
    """Alle Mängel eines Messlaufs als Liste von Sätzen (leer = in Ordnung)."""
    maengel = []
    erste = (ausgabe_text.splitlines() or [""])[0]
    if not re.match(r"^Ausgabeordner \(.+\)", erste):
        maengel.append("Die erste Ausgabezeile ist nicht „Ausgabeordner (…)“: %r" % erste[:80])
    zeilen = _messzeilen(dateien)
    if len(zeilen) < 2:
        maengel.append("Die Messdatei hat %d Messzeilen (erwartet mindestens 2 bei 3 s Dauer und 1 s Takt)." % len(zeilen))
        return maengel
    if set(zeilen[0].keys()) != {"zeit", "pfad", "status", "dauer_s"}:
        maengel.append("Die Spalten der Messdatei sind %r statt zeit, pfad, status, dauer_s." % sorted(zeilen[0].keys()))
        return maengel
    # Schlusszusammenfassung: je Abfrage eine Zeile mit dem Pfad und dem größten Wert
    nach_ende = ausgabe_text.splitlines()[1:]
    for pfad in sorted({z["pfad"] for z in zeilen}):
        groesster = max(float(z["dauer_s"].replace(",", ".")) for z in zeilen if z["pfad"] == pfad)
        passend = [z for z in nach_ende if pfad in z and any(abs(x - groesster) <= 0.05 for x in _zahlen(z.replace(pfad, "")))]
        if not passend:
            maengel.append("Die Schlusszusammenfassung nennt für die Abfrage %r nicht den größten Wert %.3f." % (pfad, groesster))
    if not any(PROTOKOLL_MARKE in text for name, text in dateien.items() if not name.endswith(".csv")):
        maengel.append("Das Dienst-Protokoll wurde nicht im Ausgabeordner abgelegt.")
    return maengel


# ═════════════════════════════════ Testfälle ═════════════════════════════════
def test_t12_ak10_messmodus_gibt_keine_geheimnisse_aus(tmp_path):
    """T-12 · AK-10 · BUG-123
    Angenommen der neue Messmodus läuft kurz bis zu seinem regulären Ende, während Passwörter, ein Schlüssel, ein Token
    und ein Geheimnis in der Umgebung gesetzt sind,
    dann hat er wirklich gemessen (Messzeilen in der Messdatei, Schlusszusammenfassung am Ende, Protokoll abgelegt),
    er hat nur lesend abgefragt, und kein Wert eines Geheimnisses steht in der Ausgabe, in der Messdatei oder im
    abgelegten Protokoll; nur die Namen der Einstellungen dürfen vorkommen."""
    with _Gegenstelle() as gegenstelle:
        code, text, ausgabe = _messlauf(tmp_path, gegenstelle.url)
    dateien = _alle_dateien_als_text(ausgabe)
    assert "Ausgabeordner (" in text, (
        "Der neue Messmodus existiert nicht (das Werkzeug zeigt nur seine Aufrufhilfe). Ausgabe (Anfang): %r" % text[:200])
    assert code == 0, "Der Messmodus endete nicht regulär (Rückgabe %d). Ausgabe (Ende): %r" % (code, text[-300:])
    assert _luecken_im_messlauf(text, dateien) == [], "Der Messlauf ist unvollständig: %s" % _luecken_im_messlauf(text, dateien)
    assert gegenstelle.anfragen, "Der Modus hat nichts abgefragt."
    assert {art for art, _ in gegenstelle.anfragen} == {"GET"}, (
        "Der Messmodus darf nur lesend abfragen, gefunden: %r" % sorted({a for a, _ in gegenstelle.anfragen}))
    gefunden = _gefundene_geheimnisse(text, dateien)
    assert not gefunden, "Geheimnisse tauchen in Ausgabe, Messdatei oder Protokoll auf (Einstellungen: %s)." % ", ".join(gefunden)


def test_t12_gegenprobe_suche_und_messlauf_pruefung_schlagen_wirklich_an():
    """T-12 · AK-10 (Gegenprobe der Prüfung selbst) · BUG-123
    Angenommen ein leerer Durchlauf (keine Messzeilen, keine Zusammenfassung) und ein Durchlauf, in den absichtlich ein
    Geheimnis eingeschleust wurde,
    dann erkennt die Prüfung den leeren Durchlauf als unvollständig und findet das eingeschleuste Geheimnis,
    während ein sauberer, vollständiger Durchlauf bestanden wird."""
    # leerer Durchlauf: nur Kopfzeile, Messdatei ohne Zeilen
    leer = _luecken_im_messlauf("Ausgabeordner (/x)\n", {"bug123_1.csv": "zeit,pfad,status,dauer_s\n"})
    assert leer and any("Messzeilen" in m for m in leer)
    # sauberer Durchlauf
    csv_text = "zeit,pfad,status,dauer_s\n1,/health,200,0.120\n2,/health,200,0.300\n3,/,200,0.050\n4,/,200,0.040\n"
    ausgabe = "Ausgabeordner (/x)\nGroesster Wert je Abfrage:\n  /health  0.300 s\n  /  0.050 s\n"
    dateien = {"bug123_1.csv": csv_text, "protokoll.txt": PROTOKOLL_MARKE}
    assert _luecken_im_messlauf(ausgabe, dateien) == []
    assert _gefundene_geheimnisse(ausgabe, dateien) == []
    # Zusammenfassung mit falschem Größtwert wird bemängelt
    falsch = _luecken_im_messlauf(ausgabe.replace("0.300", "0.120"), dateien)
    assert any("größten Wert" in m for m in falsch)
    # eingeschleustes Geheimnis wird gefunden (in der Ausgabe und in einer Datei)
    wert = GEHEIMNISSE["FOTOALERT_AUTH_SECRET"]
    assert _gefundene_geheimnisse(ausgabe + wert, dateien) == ["FOTOALERT_AUTH_SECRET"]
    dateien2 = dict(dateien, **{"protokoll.txt": PROTOKOLL_MARKE + " " + GEHEIMNISSE["FA_UEBUNG_TOKEN"]})
    assert _gefundene_geheimnisse(ausgabe, dateien2) == ["FA_UEBUNG_TOKEN"]
