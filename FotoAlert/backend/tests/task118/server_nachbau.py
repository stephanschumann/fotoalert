"""TASK-118 Teststufe 1 — Wegwerf-Nachbau der Server-Seite (HILFSMODUL, keine Tests).

Baut in einem frischen Temp-Ordner AUSSERHALB des Projekts:
  - ein Wegwerf-Git-Projekt („Ursprung“, entspricht GitHub main) mit den Versionen der Tests,
  - eine Server-Kopie davon (entspricht /opt/fotoalert/app), in der die ECHTEN Skripte aus
    FotoAlert/deploy/ des Projekts liegen (feste Server-Pfade auf den Nachbau umgebogen),
  - mitschreibende Platzhalter für Dienst-Neustart (systemctl), Webserver (caddy), sudo, Paket-
    installation (pip), Statusabfrage (curl), journalctl, sleep — und ein ssh, das sofort abbricht.
Kein Netz, kein echter Dienst, kein echtes Git-Repo. Der Ordner wird im Teardown gelöscht,
auch bei Fehlschlag/Abbruch (siehe Fixture in test_task118_ruecksprung.py).

Platzhalter-Modell des Dienstes: Ein Neustart startet die App aus den Dateien, die in diesem
Moment auf der Platte liegen (App-Version aus web/index.html) — genau wie ein echter Neustart.
Die Statusabfrage antwortet, solange die laufende Version nicht als „stumm“ markiert ist.

Python-3.9-kompatibel.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from . import schnittstelle as S

PROJEKT = Path(__file__).resolve().parents[3]          # …/FotoAlert (Projektordner)
REPO_ROOT = PROJEKT.parent
DEPLOY_QUELLE = PROJEKT / "deploy"

_ABSOLUTE_BEFEHLE = re.compile(r"(?<![\w.])/(?:usr/)?s?bin/(sudo|systemctl|caddy|journalctl|ssh|curl)\b")
_VERSION_RE = re.compile(r"const APP_VERSION = '([^']*)'")
_MARKE_RE = re.compile(r"Stand: (\S+)")


class Ergebnis:
    def __init__(self, code: int, ausgabe: str, fehlt: bool = False, befehl: str = ""):
        self.code = code
        self.ausgabe = ausgabe
        self.fehlt = fehlt
        self.befehl = befehl

    def __repr__(self) -> str:  # für lesbare Fehlermeldungen
        letzte = "\n".join(self.ausgabe.strip().splitlines()[-12:])
        return f"<{self.befehl}: Rückgabe {self.code}{' (FEHLT)' if self.fehlt else ''}>\n{letzte}"


def _schreibe(pfad: Path, inhalt: str, ausfuehrbar: bool = False) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(inhalt, encoding="utf-8")
    if ausfuehrbar:
        pfad.chmod(0o755)


class ServerNachbau:
    """Eine Welt je Test. Alle Pfade liegen unter self.wurzel (Temp-Ordner)."""

    def __init__(self, wurzel: Path):
        self.wurzel = wurzel
        self.ursprung = wurzel / "ursprung.git"
        self.entwicklung = wurzel / "entwicklung"
        self.app = wurzel / "opt/fotoalert/app"
        self.caddy_live = wurzel / "etc/caddy/Caddyfile"
        self.bin = wurzel / "bin"
        self.protokoll_datei = wurzel / "protokoll.txt"
        self.laufend_datei = wurzel / "laufend.txt"
        self.stumm_datei = wurzel / "stumm.txt"
        self.home = wurzel / "home"
        self.notizen: List[str] = []
        self._git_cfg = wurzel / "gitconfig"

    # ── Umgebung ────────────────────────────────────────────────────────────
    def umgebung(self) -> dict:
        env = {
            "PATH": f"{self.bin}:/usr/bin:/bin",
            "HOME": str(self.home),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "GIT_CONFIG_GLOBAL": str(self._git_cfg),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "TMPDIR": str(self.wurzel / "tmp"),
        }
        return env

    def _git(self, ort: Path, *args: str) -> str:
        r = subprocess.run(["git", *args], cwd=str(ort), env=self.umgebung(),
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"Nachbau: git {' '.join(args)} scheiterte: {r.stderr.strip()}")
        return r.stdout.strip()

    # ── Aufbau ──────────────────────────────────────────────────────────────
    def aufbauen(self, erste_version: str) -> None:
        for d in (self.bin, self.home, self.wurzel / "tmp", self.caddy_live.parent,
                  self.wurzel / "opt/fotoalert/venv/bin"):
            d.mkdir(parents=True, exist_ok=True)
        _schreibe(self._git_cfg, "[user]\n\tname = Nachbau\n\temail = nachbau@example.invalid\n"
                                 "[init]\n\tdefaultBranch = main\n[advice]\n\tdetachedHead = false\n")
        self.protokoll_datei.write_text("", encoding="utf-8")
        self.stumm_datei.write_text("", encoding="utf-8")
        self._platzhalter()
        subprocess.run(["git", "init", "-q", "--bare", str(self.ursprung)], env=self.umgebung(),
                       check=True, capture_output=True, timeout=60)
        subprocess.run(["git", "clone", "-q", str(self.ursprung), str(self.entwicklung)],
                       env=self.umgebung(), check=True, capture_output=True, timeout=60)
        self._grundstand()
        self._neue_version(erste_version)
        subprocess.run(["git", "clone", "-q", str(self.ursprung), str(self.app)],
                       env=self.umgebung(), check=True, capture_output=True, timeout=60)
        # Ausgangszustand: erste Version ist ausgerollt (Webserver-Einstellungen live, Dienst läuft).
        self._caddy_uebernehmen_wie_einrichtung()
        self.server_neustart()

    def _grundstand(self) -> None:
        e = self.entwicklung
        for name in (".gitignore",):
            q = REPO_ROOT / name
            if q.exists():
                shutil.copy2(q, e / name)
        ziel = e / "FotoAlert/deploy"
        ziel.mkdir(parents=True, exist_ok=True)
        if (PROJEKT / ".gitignore").exists():
            shutil.copy2(PROJEKT / ".gitignore", e / "FotoAlert/.gitignore")
        for quelle in sorted(DEPLOY_QUELLE.iterdir()):
            if not quelle.is_file():
                continue
            if quelle.suffix == ".sh":
                text = quelle.read_text(encoding="utf-8")
                treffer = _ABSOLUTE_BEFEHLE.search(text)
                if treffer:
                    raise RuntimeError(
                        f"Nachbau: {quelle.name} ruft {treffer.group(0)} mit absolutem Pfad auf — "
                        "Platzhalter greifen nicht, Test bricht aus Sicherheitsgründen ab "
                        "(siehe schnittstelle.SERVER_PRAEFIXE).")
                for praefix in S.SERVER_PRAEFIXE:
                    text = text.replace(praefix, str(self.wurzel) + praefix)
                _schreibe(ziel / quelle.name, text, ausfuehrbar=True)
            else:
                shutil.copy2(quelle, ziel / quelle.name)
        _schreibe(e / "FotoAlert/backend/requirements.txt", "# Nachbau: keine Pakete\n")
        _schreibe(e / "FotoAlert/backend/data/.gitkeep", "")

    def _neue_version(self, version: str, webserver_aendern: bool = True, sw_aendern: bool = True) -> None:
        e = self.entwicklung
        _schreibe(e / "FotoAlert/web/index.html",
                  f"<!doctype html>\n<script>\nconst APP_VERSION = '{version}';\n</script>\n")
        sw = e / "FotoAlert/web/sw.js"
        if sw_aendern or not sw.exists():
            _schreibe(sw, f"const CACHE_NAME = 'fotoalert-v{version}';\n// Stand: {version}\n")
        caddy = e / "FotoAlert/deploy/Caddyfile"
        basis = (DEPLOY_QUELLE / "Caddyfile").read_text(encoding="utf-8")
        if webserver_aendern or "Stand:" not in caddy.read_text(encoding="utf-8"):
            _schreibe(caddy, basis.rstrip("\n") + f"\n# Stand: {version}\n")
        _schreibe(e / "FotoAlert/backend/app_stand.txt", version + "\n")
        self._git(e, "add", "-A")
        self._git(e, "commit", "-q", "-m", f"Version {version}")
        self._git(e, "push", "-q", "origin", "HEAD:main")

    def _caddy_uebernehmen_wie_einrichtung(self) -> None:
        text = (self.app / "FotoAlert/deploy/Caddyfile").read_text(encoding="utf-8")
        self.caddy_live.write_text(text.replace("YOUR_DOMAIN", "fotoalert.stephanschumann.com"),
                                   encoding="utf-8")

    def _platzhalter(self) -> None:
        p, laufend, stumm = self.protokoll_datei, self.laufend_datei, self.stumm_datei
        index = self.app / "FotoAlert/web/index.html"
        caddy_live = self.caddy_live
        _schreibe(self.bin / "sudo", '#!/bin/bash\nwhile [[ "${1:-}" == -* ]]; do shift; done\nexec "$@"\n', True)
        _schreibe(self.bin / "systemctl", f"""#!/bin/bash
echo "systemctl $*" >> "{p}"
version() {{ sed -n "s/.*const APP_VERSION = '\\([^']*\\)'.*/\\1/p" "{index}" 2>/dev/null | head -1; }}
case "$1" in
  restart|start)
    case "$2" in
      fotoalert|fotoalert.service)
        v="$(version)"; [ -n "$v" ] || v="unbekannt"
        echo "$v" > "{laufend}"; echo "neustart $v" >> "{p}";;
    esac;;
  reload)
    if [ "$2" = "caddy" ] || [ "$2" = "caddy.service" ]; then
      m="$(sed -n 's/.*Stand: \\([^ ]*\\).*/\\1/p' "{caddy_live}" | tail -1)"
      echo "webserver neu geladen $m" >> "{p}"
    fi;;
  show) echo "*-*-* 03:00:00";;
  is-active) echo "active";;
esac
exit 0
""", True)
        _schreibe(self.bin / "curl", f"""#!/bin/bash
url=""; schreibformat=""; ausgabe=""
while [ $# -gt 0 ]; do
  case "$1" in
    -w) schreibformat="$2"; shift;;
    -o) ausgabe="$2"; shift;;
    http*) url="$1";;
  esac; shift
done
case "$url" in
  */health*)
    v="$(cat "{laufend}" 2>/dev/null)"
    if [ -z "$v" ] || grep -Fqx -- "$v" "{stumm}"; then
      echo "statusabfrage $v stumm" >> "{p}"; exit 7
    fi
    echo "statusabfrage $v 200" >> "{p}"
    body='{{"status":"ok","version":"2.0.0","locations_count":20}}'
    if [ -n "$ausgabe" ] && [ "$ausgabe" != "/dev/null" ]; then echo "$body" > "$ausgabe";
    elif [ -z "$ausgabe" ]; then echo "$body"; fi
    [ -n "$schreibformat" ] && printf "200"
    exit 0;;
  *) echo "netz gesperrt $url" >> "{p}"; exit 6;;
esac
""", True)
        _schreibe(self.bin / "caddy", f'#!/bin/bash\necho "caddy $*" >> "{p}"\nexit 0\n', True)
        _schreibe(self.bin / "journalctl", f'#!/bin/bash\necho "journalctl $*" >> "{p}"\nexit 0\n', True)
        _schreibe(self.bin / "sleep", f'#!/bin/bash\necho "warte $*" >> "{p}"\nexit 0\n', True)
        _schreibe(self.bin / "ssh", f'#!/bin/bash\necho "VERBOTEN ssh $*" >> "{p}"\necho "Nachbau: ssh ist gesperrt" >&2\nexit 255\n', True)
        _schreibe(self.wurzel / "opt/fotoalert/venv/bin/pip", f'#!/bin/bash\necho "pip $*" >> "{p}"\nexit 0\n', True)

    # ── Handlungen (Fachsprache-Schritte der Spec) ─────────────────────────
    def _skript(self, rel: str, args: List[str], eingabe: Optional[str] = None, zusatz_env: Optional[dict] = None) -> Ergebnis:
        pfad = self.app / rel
        befehl = f"{rel} {' '.join(args)}".strip()
        if not pfad.exists():
            return Ergebnis(127, f"{rel} ist auf dem Server nicht vorhanden.", fehlt=True, befehl=befehl)
        env = self.umgebung()
        if zusatz_env:
            env.update(zusatz_env)
        r = subprocess.run(["bash", str(pfad), *args], cwd=str(self.app), env=env,
                           input=eingabe if eingabe is not None else "",
                           capture_output=True, text=True, timeout=90)
        self._protokolliere(f"--- ende {befehl} (rückgabe {r.returncode})")
        return Ergebnis(r.returncode, r.stdout + r.stderr, befehl=befehl)

    def _protokolliere(self, zeile: str) -> None:
        with self.protokoll_datei.open("a", encoding="utf-8") as f:
            f.write(zeile + "\n")

    def markiere(self, text: str) -> int:
        """Setzt eine Marke ins Protokoll und liefert die Zeilennummer (für „danach“-Auswertungen)."""
        self._protokolliere(f"=== {text}")
        return len(self.protokoll())

    def setze_stumm(self, *versionen: str) -> None:
        self.stumm_datei.write_text("".join(v + "\n" for v in versionen), encoding="utf-8")

    def version_ist_live_und_bestaetigt(self, version: str) -> None:
        """Grundlage „Version X ist live und bestätigt“: X läuft; danach wird X als bestätigt vermerkt.
        Kennt der Stand noch keinen Vermerk (Befehl fehlt), wird das notiert — die Grundlage „X läuft“
        bleibt erfüllt; die Vermerk-Wirkung prüfen T15/T28 eigens."""
        assert self.laufende_version() == version, f"Grundlage verfehlt: läuft {self.laufende_version()!r}"
        r = self.bestaetigen()
        if r.fehlt:
            self.notizen.append(f"Vermerk „zuletzt bestätigt“ für {version} nicht möglich: {r.ausgabe}")
        else:
            assert r.code == 0, f"Vermerk für {version} scheiterte: {r!r}"

    def veroeffentliche(self, version: str, stumm: bool = False, webserver_aendern: bool = True,
                        sw_aendern: bool = True) -> Ergebnis:
        """„Version Y wird veröffentlicht“: neuer Code auf main, dann der Veröffentlichungs-Ablauf auf dem Server."""
        if stumm:
            alt = [z for z in self.stumm_datei.read_text(encoding="utf-8").split() if z]
            self.setze_stumm(*(alt + [version]))
        self._neue_version(version, webserver_aendern=webserver_aendern, sw_aendern=sw_aendern)
        self.markiere(f"veroeffentliche {version}")
        return self._skript(S.SKRIPT_VEROEFFENTLICHEN, [])

    def veroeffentliche_erneut_ohne_neuen_code(self) -> Ergebnis:
        self.markiere("veroeffentliche erneut ohne neuen code")
        return self._skript(S.SKRIPT_VEROEFFENTLICHEN, [])

    def ruecksprung_nach_rotem_live_check(self) -> Ergebnis:
        """„App springt zurück“ — der GitHub-Lauf ruft nach rotem Live-Check den automatischen Rücksprung."""
        self.markiere("live-check rot -> automatischer ruecksprung")
        return self._skript(S.SKRIPT_AUTOMATIK, S.ARGS_RUECKSPRUNG, eingabe="")

    def bestaetigen(self) -> Ergebnis:
        """Live-Check (bzw. Vorab-Probe) grün → laufende Version wird als „zuletzt bestätigt“ vermerkt."""
        self.markiere("live-check gruen -> bestaetigen")
        return self._skript(S.SKRIPT_AUTOMATIK, S.ARGS_BESTAETIGEN, eingabe="")

    def manueller_ruecksprung(self, eingabe: str) -> Ergebnis:
        self.markiere("manueller ruecksprung")
        return self._skript(S.SKRIPT_MANUELLER_RUECKSPRUNG, [], eingabe=eingabe)

    def server_neustart(self) -> None:
        """„Server wird neu gestartet“ — der Dienst startet aus den Dateien auf der Platte."""
        subprocess.run([str(self.bin / "systemctl"), "restart", "fotoalert.service"],
                       env=self.umgebung(), check=True, timeout=30)

    def lege_datensatz_an(self, inhalt: str) -> List[Path]:
        """Nutzer legt zwischen Veröffentlichung und Rücksprung Daten an (Datenbank + eigene Orte)."""
        dateien = [self.app / "FotoAlert/backend/data/fotoalert.db",
                   self.app / "FotoAlert/backend/data/custom_locations.json"]
        for d in dateien:
            _schreibe(d, inhalt)
        return dateien

    # ── Beobachtungen ──────────────────────────────────────────────────────
    def laufende_version(self) -> str:
        return self.laufend_datei.read_text(encoding="utf-8").strip() if self.laufend_datei.exists() else ""

    def version_auf_platte(self) -> str:
        m = _VERSION_RE.search((self.app / "FotoAlert/web/index.html").read_text(encoding="utf-8"))
        return m.group(1) if m else ""

    def gespeicherter_stand(self) -> str:
        """App-Version des Stands, den der Server als seinen aktuellen Stand führt (HEAD)."""
        m = _VERSION_RE.search(self._git(self.app, "show", "HEAD:FotoAlert/web/index.html"))
        return m.group(1) if m else ""

    def webserver_stand_live(self) -> str:
        treffer = _MARKE_RE.findall(self.caddy_live.read_text(encoding="utf-8"))
        return treffer[-1] if treffer else ""

    def sw_stand_auf_platte(self) -> str:
        treffer = _MARKE_RE.findall((self.app / "FotoAlert/web/sw.js").read_text(encoding="utf-8"))
        return treffer[-1] if treffer else ""

    def server_abbild(self) -> dict:
        """Fingerabdruck aller Dateien des Server-Nachbaus (App-Ordner samt gespeichertem Stand, Webserver-
        Einstellungen; ohne Temp-Ordner, der einen Neustart nicht übersteht) — zum Nachweis „auf dem Server ist nichts entstanden oder verändert“."""
        import hashlib
        abbild = {}
        for basis in (self.wurzel / "opt", self.wurzel / "etc"):
            for d in sorted(basis.rglob("*")):
                if d.is_file():
                    abbild[str(d.relative_to(self.wurzel))] = hashlib.sha256(d.read_bytes()).hexdigest()
        return abbild

    def protokoll(self) -> List[str]:
        return self.protokoll_datei.read_text(encoding="utf-8").splitlines()

    def neustarts_ab(self, zeile: int) -> List[str]:
        return [z.split(" ", 1)[1] for z in self.protokoll()[zeile:] if z.startswith("neustart ")]

    def webserver_neuladungen_ab(self, zeile: int) -> List[str]:
        return [z for z in self.protokoll()[zeile:] if z.startswith("webserver neu geladen")]

    def statusabfragen_ab(self, zeile: int) -> List[str]:
        return [z for z in self.protokoll()[zeile:] if z.startswith("statusabfrage ")]

    def verbotene_aufrufe(self) -> List[str]:
        return [z for z in self.protokoll() if z.startswith("VERBOTEN") or z.startswith("netz gesperrt")]
