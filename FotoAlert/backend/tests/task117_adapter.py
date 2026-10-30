"""TASK-117 (inkl. TASK-112) — Unterbau der Tests für den Release-Befehl (HILFSMODUL, enthält selbst keine Tests).

Warum es dieses Modul gibt: Die Spec legt das VERHALTEN des Release-Befehls fest (AK1–AK33), aber
bewusst nicht seine Form („Form legt die Umsetzung fest“: Ablage der Ticket-Dateiliste, Name der
gemeinsamen Prüfliste, Wortlaut einzelner Meldungen). Damit die Tests trotzdem vor der Umsetzung
schreibbar sind, steht alles, was nur ein VORSCHLAG dieser Tests ist, gesammelt im Block
„SCHNITTSTELLEN-VORSCHLAG“. Wird bei der Umsetzung anders entschieden, ändern sich nur diese
Konstanten und Helfer (Treiber-Schicht, jede Änderung wird gemeldet) — nicht die Testfälle in
test_task117_release.py.

Übungsablage (Entscheidung 6 vom 24.10.2026): Jeder Test bekommt im pytest-Temp-Ordner
(`tmp_path`, außerhalb des Projekts) eine eigene Welt:
  • „Wegwerf-GitHub“ = leeres Git-Gegenstück (bare repo) `github.git`,
  • „Wegwerf-Repo“ = Klon davon mit Mini-Stand der App (Versionsdateien, Backend-Datei, Doku) und
    einer KOPIE des echten Release-Befehls (das echte Projekt wird nur gelesen),
  • Platzhalter der gemeinsamen Prüfliste, die grün / rot (Block, Test) / „0 Tests“ / „übersprungen“
    meldet, auf Wunsch wartet und protokolliert, welche Dateien sie sah,
  • Python-Attrappe, die eine einstellbare Version meldet (AK2),
  • eigene Git-Konfiguration, eigenes HOME und eigenes TMPDIR (nichts vom Mac/Runner wird benutzt).
Die Welt wird nach JEDEM Test gelöscht — auch bei Fehlschlag und bei Abbruch (Teardown im
`finally` plus atexit-Netz); laufende Befehle werden vorher samt Kindprozessen beendet (AK32).
Git läuft ausschließlich in dieser Welt; vor jedem Git-Aufruf wird geprüft, dass das Ziel in der
Übungsablage liegt und das Hochladeziel das Wegwerf-GitHub ist (AK33).

Python-3.9-kompatibel (Produktion/CI). Keine Abhängigkeit von conftest.py, FastAPI oder Netzwerk.
"""
from __future__ import annotations

import atexit
import hashlib
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

# ════════════════════════════════════════════════════════════════════════════
# ECHTES PROJEKT (wird nur gelesen, nie verändert)
# ════════════════════════════════════════════════════════════════════════════
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJEKT_DIR = BACKEND_DIR.parent                      # FotoAlert/
REPO_ROOT = PROJEKT_DIR.parent                        # Repo-Root (enthält .github/)
ECHTE_GITIGNORE = REPO_ROOT / ".gitignore"
GITHUB_PRUEFBESCHREIBUNG = REPO_ROOT / ".github" / "workflows" / "deploy.yml"

# ════════════════════════════════════════════════════════════════════════════
# AUS DEM TICKET (Spec TASK-117, Entscheidungen 24.10.2026)
# ════════════════════════════════════════════════════════════════════════════
PRUEFBLOECKE = ("Backend", "Oberflächen-Check", "Browser-Tests")    # AK1/AK7/AK13
MELDUNG_NICHTS_NEUES = "Nichts Neues zu veröffentlichen"            # AK18 (wörtlich)
MELDUNG_KEINE_NEUE_VERSION = "keine neue Version"                   # AK26/AK28 (wörtlich)
NOETIGE_PYTHON_VERSION = "3.12"                                     # AK2
VERSIONSDATEIEN = ("FotoAlert/web/index.html", "FotoAlert/web/sw.js")
AUSGANGSVERSION = "1.4.2"                                           # frei gewählt, Übungsablage
NAECHSTE_PATCH_VERSION = "1.4.3"                                    # Handrechnung: patch = +1

# ════════════════════════════════════════════════════════════════════════════
# SCHNITTSTELLEN-VORSCHLAG DIESER TESTS (steht NICHT im Ticket — bei Umsetzung festlegen)
# ════════════════════════════════════════════════════════════════════════════
# Was aus dem echten Projekt in die Übungsablage kopiert wird, damit der Befehl dort läuft.
# Braucht der umgebaute Befehl Hilfsdateien, werden sie hier ergänzt.
BEFEHL_RELPFAD = "FotoAlert/release.sh"
BEFEHL_DATEIEN = (BEFEHL_RELPFAD,)
# Gemeinsame Prüfliste (Spec: „unter FotoAlert/tools/“, Name offen). In der Übungsablage liegt an
# diesem Pfad der Platzhalter — eingecheckt, also Teil „genau der Fassung, die hochgeladen wird“.
PRUEFLISTE_RELPFAD = "FotoAlert/tools/pruefliste.sh"
# Feste Ablage der „Was geht mit“-Liste: eine Datei je Zeile, relativ zum Repo-Root,
# Leerzeilen und Zeilen mit „#“ zählen nicht. Die Ablage selbst ist nicht versioniert
# (in der Übungsablage über .git/info/exclude ausgeschlossen) und geht nicht mit.
TICKETLISTE_RELPFAD = "FotoAlert/release-dateien.txt"
# Der Befehl nennt den Ort des vollständigen Protokolls in einer Zeile „Protokoll: <Pfad>“ (AK7).
PROTOKOLL_MUSTER = re.compile(r"Protokoll[^:\n]*:\s*(\S+)")
# Link zur GitHub-Prüfung in der Abschlussmeldung (AK28).
GITHUB_PRUEFUNG_LINK_MUSTER = re.compile(r"https://github\.com/\S+/actions")
# Maschinenlesbare Ergebnis-Zeilen der Prüfliste, die der Befehl auswertet und in EIGENE Meldungen
# übersetzt (AK7/AK9/AK13) — die Zeilen enthalten nur Kennungen, keine Anzeigenamen, damit bloßes
# Durchreichen der Prüflisten-Ausgabe keinen Test erfüllt:
#   „PRUEFLISTE block=<kennung> start“
#   „PRUEFLISTE block=<kennung> bestanden=<n> fehlgeschlagen=<n> uebersprungen=<n> [rot=<Test>]“
# Der Platzhalter beendet sich bei „0 Tests“ und „übersprungen“ bewusst mit Code 0 (BUG-100-Muster:
# Werkzeug meldet Erfolg, obwohl nichts geprüft wurde) — der Befehl muss das trotzdem als Rot werten.
BLOCK_KENNUNG = {"Backend": "backend", "Oberflächen-Check": "oberflaechen_check", "Browser-Tests": "browser_tests"}
# Geheimnisse bekommt die Prüfliste als Umgebungsvariablen (Mac: aus der lokalen Passwortdatei).
# Sicherungskopie der Ticket-Liste (Backlog), die der Befehl vor dem Hochladen selbst anlegt
# (AK23b; Ablage laut Orchestrator „BACKLOG-Schutz“): _to_delete/BACKLOG.vor_<anlass>_<Zeit>.md
BACKLOG_RELPFAD = "FotoAlert/BACKLOG.md"
SICHERUNGSKOPIE_GLOB = "FotoAlert/_to_delete/BACKLOG.vor_*.md"
_SICHERUNGSKOPIE_RE = re.compile(r"(^|/)_to_delete/BACKLOG\.vor_[^/]*\.md$")
# Python-Attrappe: der Befehl ermittelt die aktive Version über „python3“/„python“ im Suchpfad
# oder über FotoAlert/backend/venv/bin/python3 (beides zeigt in der Übungsablage auf die Attrappe).

# Feste Prüfwerte für Passwörter/Geheimnisse (AK15) — absichtlich unverwechselbar.
PRUEFWERTE = {
    "FOTOALERT_HOST_PASSWORD": "PW-host-T117-q7Zx3",
    "FOTOALERT_USER_PASSWORD": "PW-user-T117-k2Mv9",
    "FOTOALERT_AUTH_SECRET": "SECRET-T117-w5Rn8",
}

BEFEHL_ZEITLIMIT_S = 150          # Obergrenze je Aufruf in der Übungsablage (Platzhalter ist schnell)
WARTEN_ZEITLIMIT_S = 90           # bis der Probelauf den Wartepunkt erreicht

# ════════════════════════════════════════════════════════════════════════════
# PLATZHALTER DER GEMEINSAMEN PRÜFLISTE (Schicht 4, nur Übungsablage)
# ════════════════════════════════════════════════════════════════════════════
_PLATZHALTER_PRUEFLISTE = r"""#!/usr/bin/env bash
# PLATZHALTER der gemeinsamen Prüfliste — nur in der Übungsablage von TASK-117-Tests.
STEUERUNG='__STEUERUNG__'
BERICHT='__BERICHT__'
MODUS=gruen; ROT_BLOCK=backend; ROT_TEST=test_platzhalter_rot; DATEIMUSTER=; WARTEN_AUF=
[ -f "$STEUERUNG" ] && . "$STEUERUNG"
SELBST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOPIE="$(cd "$SELBST_DIR/../.." && pwd)"
{
  echo "LAUF $$"
  echo "CWD $PWD"
  echo "KOPIE $KOPIE"
  echo "ARGS $*"
  (cd "$KOPIE" && find . -path ./.git -prune -o -type f -print | sed 's|^\./||' | sort | sed 's/^/DATEI /')
} >> "$BERICHT"
for V in FOTOALERT_HOST_PASSWORD FOTOALERT_USER_PASSWORD FOTOALERT_AUTH_SECRET; do
  W="${!V}"
  if [ -n "$W" ]; then
    printf '%s' "$W" | cksum > /dev/null   # „nutzt“ den Wert, ohne ihn auszugeben
    echo "GEHEIMNIS $V vorhanden" >> "$BERICHT"
  else
    echo "GEHEIMNIS $V fehlt" >> "$BERICHT"
  fi
done
echo "PRUEFLISTE gestartet args=$*"
if [ -n "$WARTEN_AUF" ]; then
  echo "WARTE" >> "$BERICHT"
  for _ in $(seq 1 900); do [ -f "$WARTEN_AUF" ] && break; sleep 0.1; done
fi
# __ZUSATZSCHRITT__
GESAMT=0
for BLOCK in backend oberflaechen_check browser_tests; do
  echo "PRUEFLISTE block=$BLOCK start"
  B=5; F=0; S=0; ROT=""
  case "$MODUS" in
    rot) if [ "$BLOCK" = "$ROT_BLOCK" ]; then F=1; ROT="$ROT_TEST"; fi ;;
    null_tests) B=0 ;;
    uebersprungen) if [ "$BLOCK" = "$ROT_BLOCK" ]; then B=0; S=3; fi ;;
    rot_wenn_datei)
      if [ "$BLOCK" = backend ] && (cd "$KOPIE" && find . -path ./.git -prune -o -type f -name "$DATEIMUSTER" -print | grep -q .); then
        F=1; ROT="$DATEIMUSTER"
      fi ;;
  esac
  ZEILE="PRUEFLISTE block=$BLOCK bestanden=$B fehlgeschlagen=$F uebersprungen=$S"
  [ -n "$ROT" ] && ZEILE="$ZEILE rot=$ROT"
  echo "$ZEILE"
  echo "BLOCK $ZEILE" >> "$BERICHT"
  [ "$F" -gt 0 ] && GESAMT=1
done
echo "ENDE $GESAMT" >> "$BERICHT"
exit $GESAMT
"""

_ZUSATZSCHRITT = 'echo "ZUSATZSCHRITT ausgefuehrt" >> "$BERICHT"; echo "PRUEFLISTE block=zusatzschritt start"'

_PYTHON_ATTRAPPE = r"""#!/usr/bin/env bash
# Python-Attrappe der TASK-117-Übungsablage: meldet die eingestellte Version, rechnet mit echtem Python.
VERSION="$(cat '__VERSIONSDATEI__')"
ECHT='__ECHT__'
case "$1" in
  --version|-V) echo "Python $VERSION"; exit 0 ;;
  -c)
    T117_CODE="$2"; shift 2
    export T117_CODE T117_VERSION="$VERSION"
    exec "$ECHT" -c '
import os, sys, collections, platform
_v = [int(x) for x in os.environ["T117_VERSION"].split(".")]
_VI = collections.namedtuple("version_info", "major minor micro releaselevel serial")
sys.version_info = _VI(_v[0], _v[1], _v[2], "final", 0)
sys.version = os.environ["T117_VERSION"] + " (Attrappe TASK-117)"
platform.python_version = lambda: os.environ["T117_VERSION"]
_c = os.environ.pop("T117_CODE"); os.environ.pop("T117_VERSION")
sys.argv = ["-c"] + sys.argv[1:]
exec(compile(_c, "<string>", "exec"))
' "$@" ;;
esac
exec "$ECHT" "$@"
"""

_INDEX_HTML = "<!doctype html>\n<html><body>\n<script>\nconst APP_VERSION = '{v}';\n</script>\n</body></html>\n"
_SW_JS = "// Service Worker (Übungsablage)\nconst CACHE_NAME = 'fotoalert-v{v}';\n"

# ════════════════════════════════════════════════════════════════════════════
# AUFRÄUM-NETZ (AK32)
# ════════════════════════════════════════════════════════════════════════════
_OFFENE_ABLAGEN = set()
_OFFENE_PROZESSE = []


def _beende_prozessgruppe(proc):
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass


def _loesche(pfad):
    def _schreibbar(func, p, _exc):
        os.chmod(p, stat.S_IRWXU)
        func(p)
    if Path(pfad).exists():
        shutil.rmtree(pfad, onerror=_schreibbar)


def _alles_aufraeumen():
    for proc in list(_OFFENE_PROZESSE):
        _beende_prozessgruppe(proc)
    for pfad in list(_OFFENE_ABLAGEN):
        _loesche(pfad)


atexit.register(_alles_aufraeumen)


def _liegt_in(pfad, basis):
    try:
        Path(pfad).resolve().relative_to(Path(basis).resolve())
        return True
    except ValueError:
        return False


def _sha(pfad):
    p = Path(pfad)
    if not p.exists():
        return "FEHLT"
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ════════════════════════════════════════════════════════════════════════════
# ERGEBNIS EINES AUFRUFS
# ════════════════════════════════════════════════════════════════════════════
class Ergebnis:
    def __init__(self, code, ausgabe):
        self.code = code
        self.ausgabe = ausgabe

    def zeige(self, grund):
        zeilen = self.ausgabe.strip().splitlines()[-40:]
        return f"{grund}\n— Code {self.code}; letzte Ausgabe des Befehls:\n" + "\n".join(zeilen)


class Hintergrundlauf:
    """Release-Befehl, der im Hintergrund läuft (Doppelstart, Abbruch, Liste vor dem Probelauf)."""

    def __init__(self, proc, ausgabedatei):
        self.proc = proc
        self.ausgabedatei = ausgabedatei

    @property
    def ausgabe(self):
        return self.ausgabedatei.read_text(encoding="utf-8", errors="replace")

    def laeuft(self):
        return self.proc.poll() is None

    def signal(self, sig):
        os.killpg(self.proc.pid, sig)

    def warte_ende(self, zeitlimit=BEFEHL_ZEITLIMIT_S):
        try:
            self.proc.wait(timeout=zeitlimit)
        except subprocess.TimeoutExpired:
            _beende_prozessgruppe(self.proc)
            pytest.fail(f"Befehl endete nicht innerhalb von {zeitlimit} s (danach hart beendet).\n"
                        + self.ausgabe[-3000:])
        return Ergebnis(self.proc.returncode, self.ausgabe)


class Probelauf:
    def __init__(self):
        self.cwd = None
        self.kopie = None
        self.args = ""
        self.dateien = []
        self.bloecke = []
        self.wartet = False
        self.zusatz = False
        self.ende = None
        self.geheimnisse = {}

    def sieht(self, relpfad):
        """True, wenn die Prüfliste die Datei in ihrer Kopie sah (Pfad relativ zum Repo-Root)."""
        kurz = relpfad.split("FotoAlert/", 1)[-1]
        return any(d == relpfad or d.endswith("/" + kurz) or d == kurz for d in self.dateien)


# ════════════════════════════════════════════════════════════════════════════
# DIE ÜBUNGSABLAGE
# ════════════════════════════════════════════════════════════════════════════
class Uebung:
    def __init__(self, root):
        self.root = Path(root)
        self.github = self.root / "github.git"
        self.repo = self.root / "repo"
        self.proj = self.repo / "FotoAlert"
        self.bin = self.root / "bin"
        self.home = self.root / "home"
        self.tmp = self.root / "tmp"
        self.steuerung = self.root / "pruefliste-steuerung.env"
        self.bericht = self.root / "pruefliste-bericht.txt"
        self.weiter_datei = self.root / "weiter"
        self.versionsdatei = self.root / "python-version.txt"
        self.umleitung = str(self.root / "kein-echtes-github") + "/"
        self._laeufe = []
        self.env = None

    # ── Aufbau ──────────────────────────────────────────────────────────────
    def aufbauen(self):
        assert not _liegt_in(self.root, REPO_ROOT), (
            f"Übungsablage {self.root} läge im echten Projekt — abgebrochen (AK33).")
        for d in (self.bin, self.home, self.tmp, self.proj):
            d.mkdir(parents=True, exist_ok=True)
        gitconfig = self.root / "gitconfig"
        gitconfig.write_text(
            "[user]\n\tname = Uebung TASK-117\n\temail = uebung@example.invalid\n"
            "[init]\n\tdefaultBranch = main\n[commit]\n\tgpgsign = false\n"
            "[tag]\n\tgpgsign = false\n[advice]\n\tdetachedHead = false\n"
            # AK33: Jede Adresse des echten GitHub wird technisch auf ein nicht vorhandenes Ziel IN der
            # Übungsablage umgeleitet — ein Hochladen zum echten GitHub ist damit unmöglich.
            f"[url \"{self.umleitung}\"]\n"
            "\tinsteadOf = https://github.com/\n\tinsteadOf = http://github.com/\n"
            "\tinsteadOf = git@github.com:\n\tinsteadOf = ssh://git@github.com/\n"
            "\tinsteadOf = git://github.com/\n"
            "\tpushInsteadOf = https://github.com/\n\tpushInsteadOf = git@github.com:\n"
            "\tpushInsteadOf = ssh://git@github.com/\n", encoding="utf-8")
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("GIT_") and not k.startswith("FOTOALERT_")}
        env.update({
            "HOME": str(self.home),
            "TMPDIR": str(self.tmp),
            "GIT_CONFIG_GLOBAL": str(gitconfig),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "PATH": str(self.bin) + os.pathsep + os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1",
        })
        env.update(PRUEFWERTE)
        self.env = env

        self.python_ist("3.12.7")
        attrappe = (_PYTHON_ATTRAPPE.replace("__VERSIONSDATEI__", str(self.versionsdatei))
                    .replace("__ECHT__", sys.executable))
        venv_bin = self.proj / "backend" / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        for ziel in (self.bin / "python3", self.bin / "python", venv_bin / "python3", venv_bin / "python"):
            ziel.write_text(attrappe, encoding="utf-8")
            ziel.chmod(0o755)

        self._git(["init", "--bare", "-q", str(self.github)], cwd=self.root, pruefe_ziel=False)
        self._git(["init", "-q", str(self.repo)], cwd=self.root, pruefe_ziel=False)

        for rel in BEFEHL_DATEIEN:
            quelle = REPO_ROOT / rel
            assert quelle.is_file(), f"Release-Befehl {quelle} fehlt im Projekt"
            ziel = self.repo / rel
            ziel.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(quelle, ziel)
            ziel.chmod(0o755)
        gitignore = ECHTE_GITIGNORE.read_text(encoding="utf-8") if ECHTE_GITIGNORE.is_file() else ""
        self.schreibe(".gitignore", gitignore + "\nFotoAlert/backend/venv/\n.env\n")
        self.schreibe("FotoAlert/web/index.html", _INDEX_HTML.format(v=AUSGANGSVERSION))
        self.schreibe("FotoAlert/web/sw.js", _SW_JS.format(v=AUSGANGSVERSION))
        self.schreibe("FotoAlert/backend/main.py", "# Backend (Übungsablage)\nANTWORT = 1\n")
        self.schreibe("FotoAlert/backend/helfer.py", "# Helfer (Übungsablage)\nWERT = 1\n")
        self.schreibe("FotoAlert/backend/tests/test_beispiel.py", "def test_beispiel():\n    assert True\n")
        self.schreibe("FotoAlert/backend/data/cache/building_footprints.json", "{}\n")
        self.schreibe("FotoAlert/BACKLOG.md", "# Backlog (Übungsablage)\n")
        self.schreibe("FotoAlert/README.md", "# FotoAlert (Übungsablage)\n")
        prueferliste = (_PLATZHALTER_PRUEFLISTE.replace("__STEUERUNG__", str(self.steuerung))
                        .replace("__BERICHT__", str(self.bericht)))
        self.schreibe(PRUEFLISTE_RELPFAD, prueferliste)
        (self.repo / PRUEFLISTE_RELPFAD).chmod(0o755)
        # Passwortdatei des Macs (AK15, Technische Festlegung „lokale Passwortdatei“) — nie versioniert.
        self.schreibe("FotoAlert/backend/.env",
                      "".join(f"{k}={v}\n" for k, v in PRUEFWERTE.items()))
        with open(self.repo / ".git" / "info" / "exclude", "a", encoding="utf-8") as fh:
            fh.write("\n" + TICKETLISTE_RELPFAD + "\n")

        self.git("add", "-A")
        self.git("commit", "-q", "-m", f"Ausgangsstand v{AUSGANGSVERSION}")
        self.git("tag", f"v{AUSGANGSVERSION}")
        self.git("remote", "add", "origin", str(self.github))
        self.git("push", "-q", "-u", "origin", "main", "--tags")
        self.pruefliste()

    # ── Git, nur in der Übungsablage ────────────────────────────────────────
    def _git(self, args, cwd, pruefe_ziel=True, check=True):
        assert _liegt_in(cwd, self.root), f"Git-Aufruf außerhalb der Übungsablage verweigert: {cwd}"
        if pruefe_ziel and (Path(cwd) / ".git").exists():
            url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=cwd, env=self.env,
                                 capture_output=True, text=True).stdout.strip()
            assert not url or _liegt_in(url, self.root), (
                f"Hochladeziel {url!r} liegt nicht in der Übungsablage (AK33)")
        p = subprocess.run(["git"] + list(args), cwd=cwd, env=self.env, capture_output=True, text=True)
        if check and p.returncode != 0:
            raise AssertionError(f"Vorbereitung in der Übungsablage scheiterte: git {' '.join(args)}\n"
                                 f"{p.stdout}\n{p.stderr}")
        return p.stdout.strip()

    def git(self, *args, check=True):
        return self._git(args, cwd=self.repo, check=check)

    def github_git(self, *args):
        return self._git(["--git-dir", str(self.github)] + list(args), cwd=self.root, pruefe_ziel=False)

    # ── Dateien und Ticket ──────────────────────────────────────────────────
    def schreibe(self, relpfad, inhalt):
        ziel = self.repo / relpfad
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(inhalt, encoding="utf-8")
        return ziel

    def aendere(self, relpfad, zusatz="# geändert für das Ticket\n"):
        ziel = self.repo / relpfad
        alt = ziel.read_text(encoding="utf-8") if ziel.exists() else ""
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(alt + zusatz, encoding="utf-8")
        return ziel

    def lies(self, relpfad):
        return (self.repo / relpfad).read_text(encoding="utf-8")

    def ignoriere(self, relpfad):
        with open(self.repo / ".git" / "info" / "exclude", "a", encoding="utf-8") as fh:
            fh.write(relpfad + "\n")

    def vormerken(self, relpfad, inhalt="# vorgemerkt\n"):
        self.schreibe(relpfad, inhalt)
        self.git("add", relpfad)

    def committe(self, nachricht, *relpfade):
        self.git("add", *relpfade)
        self.git("commit", "-q", "-m", nachricht, "--", *relpfade)
        return self.git("rev-parse", "HEAD")

    def ticketliste(self, *relpfade, roh=None):
        inhalt = roh if roh is not None else "# Ticket-Dateien (Übungsablage)\n" + "".join(p + "\n" for p in relpfade)
        (self.repo / TICKETLISTE_RELPFAD).write_text(inhalt, encoding="utf-8")

    def ticketliste_entfernen(self):
        p = self.repo / TICKETLISTE_RELPFAD
        if p.exists():
            p.unlink()

    def standard_ticket(self):
        """Ticket mit einer geänderten Backend-Datei, korrekt gelistet."""
        self.aendere("FotoAlert/backend/main.py")
        self.ticketliste("FotoAlert/backend/main.py")

    # ── Platzhalter-Prüfliste und Python-Attrappe ───────────────────────────
    def pruefliste(self, modus="gruen", block=None, test=None, dateimuster=None, warten=False):
        zeilen = [f"MODUS={modus}"]
        if block:
            zeilen.append(f"ROT_BLOCK='{BLOCK_KENNUNG.get(block, block)}'")
        if test:
            zeilen.append(f"ROT_TEST='{test}'")
        if dateimuster:
            zeilen.append(f"DATEIMUSTER='{dateimuster}'")
        if warten:
            if self.weiter_datei.exists():
                self.weiter_datei.unlink()
            zeilen.append(f"WARTEN_AUF='{self.weiter_datei}'")
        self.steuerung.write_text("\n".join(zeilen) + "\n", encoding="utf-8")

    def weiter(self):
        self.weiter_datei.write_text("weiter\n", encoding="utf-8")

    def pruefliste_ergaenzen(self):
        """Ändert die eingecheckte Prüfliste: neuer Zusatzschritt (TF-11)."""
        p = self.repo / PRUEFLISTE_RELPFAD
        p.write_text(p.read_text(encoding="utf-8").replace("# __ZUSATZSCHRITT__", _ZUSATZSCHRITT),
                     encoding="utf-8")

    def python_ist(self, version):
        self.versionsdatei.write_text(version, encoding="utf-8")

    def probelaeufe(self):
        if not self.bericht.exists():
            return []
        laeufe = []
        for zeile in self.bericht.read_text(encoding="utf-8").splitlines():
            schluessel, _, rest = zeile.partition(" ")
            if schluessel == "LAUF":
                laeufe.append(Probelauf())
                continue
            if not laeufe:
                continue
            l = laeufe[-1]
            if schluessel == "CWD":
                l.cwd = rest
            elif schluessel == "KOPIE":
                l.kopie = rest
            elif schluessel == "ARGS":
                l.args = rest
            elif schluessel == "DATEI":
                l.dateien.append(rest)
            elif schluessel == "BLOCK":
                l.bloecke.append(rest)
            elif schluessel == "WARTE":
                l.wartet = True
            elif schluessel == "ZUSATZSCHRITT":
                l.zusatz = True
            elif schluessel == "GEHEIMNIS":
                name, _, wert = rest.partition(" ")
                l.geheimnisse[name] = wert
            elif schluessel == "ENDE":
                l.ende = int(rest)
        return laeufe

    # ── Release starten ─────────────────────────────────────────────────────
    def _befehl(self, art, text):
        return ["bash", str(self.repo / BEFEHL_RELPFAD), art, text]

    def release_starten(self, art="patch", text="TASK-117 Probe", eingabe="j\n",
                        zeitlimit=BEFEHL_ZEITLIMIT_S):
        """Startet den Befehl im Vordergrund. eingabe=None: Eingabe geschlossen (keine Tastatur).
        Standard „j“: der heutige Befehl fragt noch Ja/Nein; so zeigt jeder Test sein eigenes
        fehlendes Verhalten statt überall nur AK28. Der umgebaute Befehl ignoriert die Eingabe."""
        proc = subprocess.Popen(
            self._befehl(art, text), cwd=self.proj, env=self.env,
            stdin=subprocess.PIPE if eingabe is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        _OFFENE_PROZESSE.append(proc)
        try:
            out, _ = proc.communicate(input=eingabe.encode() if eingabe is not None else None,
                                      timeout=zeitlimit)
        except subprocess.TimeoutExpired:
            _beende_prozessgruppe(proc)
            pytest.fail(f"Release-Befehl endete nicht innerhalb von {zeitlimit} s (hart beendet).")
        finally:
            _beende_prozessgruppe(proc)
        return Ergebnis(proc.returncode, out.decode("utf-8", errors="replace"))

    def release_im_hintergrund(self, art="patch", text="TASK-117 Probe", eingabe="j\n"):
        ausgabedatei = self.root / f"ausgabe-{len(self._laeufe)}.txt"
        fh = open(ausgabedatei, "wb")
        eingabedatei = self.root / f"eingabe-{len(self._laeufe)}.txt"
        eingabedatei.write_text(eingabe or "", encoding="utf-8")
        ein = open(eingabedatei, "rb") if eingabe is not None else subprocess.DEVNULL
        proc = subprocess.Popen(self._befehl(art, text), cwd=self.proj, env=self.env, stdin=ein,
                                stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        fh.close()
        if eingabe is not None:
            ein.close()
        _OFFENE_PROZESSE.append(proc)
        lauf = Hintergrundlauf(proc, ausgabedatei)
        self._laeufe.append(lauf)
        return lauf

    def warte_auf_probelauf(self, lauf, zeitlimit=WARTEN_ZEITLIMIT_S):
        """Wartet, bis die Prüfliste ihren Wartepunkt erreicht. Endet der Befehl vorher, ist das
        der beobachtete Befund „Probelauf nie gestartet“ (kein Mechanik-Fehler)."""
        frist = time.time() + zeitlimit
        while time.time() < frist:
            if any(l.wartet for l in self.probelaeufe()):
                return
            if not lauf.laeuft():
                pytest.fail("Befund: Der Befehl endete (Code %s), ohne den Probelauf zu starten — "
                            "die Prüfliste wurde nie aufgerufen.\n%s"
                            % (lauf.proc.returncode, "\n".join(lauf.ausgabe.splitlines()[-30:])))
            time.sleep(0.1)
        pytest.fail(f"Befund: Probelauf hat nach {zeitlimit} s seinen Startpunkt nicht erreicht.\n"
                    + "\n".join(lauf.ausgabe.splitlines()[-30:]))

    def beende_laeufe(self):
        for lauf in self._laeufe:
            _beende_prozessgruppe(lauf.proc)

    # ── Beobachten ──────────────────────────────────────────────────────────
    def lokale_version(self):
        m = re.search(r"APP_VERSION = '([0-9.]+)'", self.lies("FotoAlert/web/index.html"))
        return m.group(1) if m else None

    def github_version(self):
        inhalt = self.github_git("show", "main:FotoAlert/web/index.html")
        m = re.search(r"APP_VERSION = '([0-9.]+)'", inhalt)
        return m.group(1) if m else None

    def github_cache_name(self):
        return self.github_git("show", "main:FotoAlert/web/sw.js")

    def github_stand(self):
        return self.github_git("rev-parse", "main")

    def github_tags(self):
        return sorted(self.github_git("tag", "-l").split())

    def github_neue_commits(self, seit):
        out = self.github_git("rev-list", f"{seit}..main")
        return out.split() if out else []

    def github_dateien_zwischen(self, alt, neu):
        out = self.github_git("diff", "--name-only", alt, neu)
        return sorted(out.split("\n")) if out else []

    def github_datei(self, relpfad):
        return self.github_git("show", f"main:{relpfad}")

    def github_zustand(self):
        return {"main": self.github_stand(), "tags": self.github_tags()}

    def lokaler_stand(self):
        return self.git("rev-parse", "HEAD")

    def zustand(self):
        """Alles, was „nichts verändert“ umfasst: eingecheckter Stand, Vormerkungen, Inhalt jeder
        versionierten und jeder neuen (nicht ignorierten) Datei, Tags lokal/GitHub, GitHub-Stand."""
        dateien = self.git("ls-files", "-co", "--exclude-standard").split("\n")
        return {
            "head": self.lokaler_stand(),
            "status": "\n".join(z for z in self.git("status", "--porcelain=v1", "-uall").split("\n")
                                 if not _SICHERUNGSKOPIE_RE.search(z)),
            # Die Backlog-Sicherungskopie (AK23b) zählt nicht als Veränderung.
            "inhalte": {d: _sha(self.repo / d) for d in dateien if d and not _SICHERUNGSKOPIE_RE.search(d)},
            "tags": sorted(self.git("tag", "-l").split()),
            "github": self.github_zustand(),
            "sperrdatei": (self.repo / ".git" / "index.lock").exists(),
        }

    def status_von(self, relpfad):
        return self.git("status", "--porcelain=v1", "--", relpfad)

    def sicherungskopien(self):
        return sorted(self.repo.glob(SICHERUNGSKOPIE_GLOB))

    def protokollpfad(self, ausgabe):
        m = PROTOKOLL_MUSTER.search(ausgabe)
        if not m:
            return None
        roh = m.group(1).strip("'\"`.,;")
        for basis in (Path("/"), self.proj, self.repo):
            p = (basis / roh) if not roh.startswith("/") else Path(roh)
            if p.exists():
                return p
        return Path(roh)


@pytest.fixture
def uebung(tmp_path):
    """Frische Übungsablage je Test; wird im Teardown IMMER gelöscht (AK32)."""
    _OFFENE_ABLAGEN.add(tmp_path)
    u = Uebung(tmp_path / "uebung")
    try:
        u.aufbauen()
        yield u
    finally:
        u.beende_laeufe()
        for proc in list(_OFFENE_PROZESSE):
            _beende_prozessgruppe(proc)
        _loesche(tmp_path)
        _OFFENE_ABLAGEN.discard(tmp_path)
    assert not tmp_path.exists(), f"Übungsablage {tmp_path} blieb nach dem Test liegen (AK32)"


def echter_projektstand():
    """Prüfsummen der Stellen im ECHTEN Projekt, die ein Release verändern würde (nur lesen, kein Git)."""
    stand = {}
    for rel in (BEFEHL_RELPFAD, "FotoAlert/web/index.html", "FotoAlert/web/sw.js",
                TICKETLISTE_RELPFAD, PRUEFLISTE_RELPFAD, ".github/workflows/deploy.yml"):
        stand[rel] = _sha(REPO_ROOT / rel)
    git_dir = REPO_ROOT / ".git"
    if git_dir.is_dir():
        for rel in ("HEAD", "packed-refs"):
            stand[".git/" + rel] = _sha(git_dir / rel)
        for unter in ("refs/heads", "refs/tags"):
            basis = git_dir / unter
            if basis.is_dir():
                for p in sorted(basis.rglob("*")):
                    if p.is_file():
                        stand[".git/" + str(p.relative_to(git_dir))] = _sha(p)
    return stand


_NICHT_ERFASST = {"__pycache__", ".pytest_cache"}


def projektordner_pruefsummen():
    """Prüfsummen über den GANZEN echten Repo-Ordner (inkl. .git): je Datei Größe + Änderungszeit
    (deckt jede Schreiboperation ab, auch bei großen Daten), dazu Inhalts-Prüfsumme der Stellen, die
    ein Release verändern würde. Nur lesen, kein Git. Python-Zwischenablagen bleiben außen vor."""
    stand = {}
    for wurzel, ordner, dateien in os.walk(REPO_ROOT, onerror=lambda e: None):
        ordner[:] = [o for o in ordner if o not in _NICHT_ERFASST]
        for name in dateien:
            p = Path(wurzel) / name
            try:
                st = p.lstat()
                stand[str(p.relative_to(REPO_ROOT))] = (st.st_size, st.st_mtime_ns)
            except OSError:
                stand[str(p.relative_to(REPO_ROOT))] = "unlesbar"
    for rel, wert in echter_projektstand().items():
        stand["sha256:" + rel] = wert
    return stand
