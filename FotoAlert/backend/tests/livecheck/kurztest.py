#!/usr/bin/env python3
"""TASK-118 — Kurztest für den Live-Check (rein lesend).

Ruft die App über ihre öffentliche Adresse auf, in einem frisch gestarteten Browser ohne
Zwischenspeicher, und prüft sechs Punkte: Version, Anmeldung, Karte, Feed, Kalender, Programmfehler.

Aufruf:
    python kurztest.py --adresse <https://…> --erwartete-version <x.y.z> --ergebnis-ordner <ordner>
Der Prüf-Zugang (Gast-Passwort) kommt ausschließlich aus der Umgebungsvariable
FOTOALERT_LIVECHECK_PASSWORD (bei GitHub: eigenes Geheimnis). Er steht in keiner Datei und wird in
Ausgabe, Ergebnisdateien und Bildschirmfotos nie im Klartext gezeigt.

Rückgabewert: 0 = alle sechs Prüfpunkte bestanden · 1 = mindestens ein Prüfpunkt gescheitert ·
2 = nicht einsatzbereit (Prüf-Zugang fehlt, Browser nicht startbar, falscher Aufruf).
Je gescheitertem Prüfpunkt gibt es genau eine Zeile „gescheitert: <Prüfpunkt>“ (Ausgabe und Datei
kurztest-ergebnis.txt im Ergebnis-Ordner), darunter eingerückt der Grund.

Regeln (Ticket TASK-118):
  - Rein lesend: Anfragen, die Daten ändern, stellt dieser Test nie; die einzige Ausnahme ist das
    Anmelden mit Gast-Rechten (AK14).
  - Höchstens ein Anmeldeversuch beim Server pro Lauf, nie ein zweiter nach einer Ablehnung (AK4).
  - Vor dem ersten Prüfpunkt wartet der Kurztest (Bereitschaftsphase, höchstens T_BEREITSCHAFT_S), bis
    die Startseite antwortet — direkt nach einem Dienst-Neustart ist die echte Seite oft kurz stumm.
    Antwortet sie nie, scheitert der Prüfpunkt Version wie bisher mit „Seite nicht erreichbar“.
  - Danach, nur wenn die Seite bereit ist, wärmt der Kurztest den Kalender vor (Vorwärm-Phase,
    warte_auf_kalender_vorwaermen): ein einziger lesender GET auf /calendar für den aktuellen Monat,
    Körper vollständig gelesen, damit der Server fertig rechnet und zwischenspeichert (nach einem
    Neustart rechnet er den Monat sonst live, ~30 s, im Browser-Prüfpunkt zu langsam). Die Vorwärm-Phase
    setzt NIE ein Ergebnis; sie schreibt nur eine Hinweiszeile. Der Prüfpunkt Kalender bleibt streng.
  - Jeder andere gescheiterte Prüfpunkt wird genau einmal wiederholt (AK11); die Wiederholung fragt
    die Daten neu ab.
  - Fehler aus fremden Quellen (z. B. Kartendienst) lösen kein Scheitern aus, stehen aber in der
    Meldung (AK10a). Kartenbilder fremder Anbieter und „degraded“ der Statusabfrage zählen nicht (AK12).
  - Die Anmeldung steckt allein in anmelden() (wegen US-136: ein späteres Prüfkonto ändert nur dort).
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional
from urllib.parse import urlparse

GEHEIMNIS_NAME = "FOTOALERT_LIVECHECK_PASSWORD"

PP_VERSION = "Version"
PP_ANMELDUNG = "Anmeldung"
PP_KARTE = "Karte"
PP_FEED = "Feed"
PP_KALENDER = "Kalender"
PP_PROGRAMMFEHLER = "Programmfehler"

GRUND_FALSCHE_VERSION = "falsche Version live"

EXIT_OK, EXIT_GESCHEITERT, EXIT_NICHT_EINSATZBEREIT = 0, 1, 2

# Wartezeiten (Millisekunden). Direkt nach einem Dienst-Neustart (Veröffentlichen oder Rücksprung) ist
# die echte Seite für eine Weile langsam (große Zwischenspeicher-Dateien); die Werte sind deshalb
# großzügig. Obergrenze: Ein Kurztest-Schritt im GitHub-Lauf darf höchstens 3 Minuten dauern
# (timeout-minutes in deploy.yml) — Rechnung für die stumme Seite (gerechnet, nicht gemessen):
# 5 s Pause + Bereitschaft (höchstens T_BEREITSCHAFT_S + 8 s = 98 s) + Prüfpunkt Version (2 × T_SEITE + 3 s)
# + Bildschirmfoto (T_SEITE) ≈ 166 s im ungünstigsten Fall (gemessen mit 90 s Bereitschaft: 153,7 s).
# Grenzen: Schritt-Limit in deploy.yml 180 s, Test-Zeitlimit (schnittstelle.py) 170 s, alle drei Schritte
# zusammen 600 s. Vorwärm-Phase (Kalender), alles „gerechnet, nicht gemessen“:
#  (a) stumme Seite: Die Seite wird nie bereit, die Vorwärm-Phase läuft nicht → unverändert 153,7 s
#      (gemessen), gerechnet höchstens 166 s. Keine Verschlechterung.
#  (b) Seite antwortet, Kalender aber kalt: Bereitschaft + Vorwärmen enden zusammen spätestens bei
#      VORWAERM_BIS_S = 100 s nach Start (die Obergrenze T_VORWAERM_S = 60 s wird entsprechend
#      gekürzt; bleiben weniger als VORWAERM_MIN_S = 15 s übrig, wird nicht vorgewärmt).
#      Danach, wenn der Kalender warm ist: Browser starten/Version ≈ 5 s, Anmeldung ≈ 6 s,
#      Willkommensfenster 4 s, Karte ≈ 5 s, Feed ≈ 5 s, Kalender ≈ 20 s (warm: 40 MB in 16–17 s am echten
#      Server gemessen, nur das Laden), Programmfehler 2,5 s, Beenden ≈ 2 s → rund 50 s, in Summe
#      ≈ 150 s. Kalter Server beim Vorwärmen: ~30 s Rechnen + ~17 s Übertragung ≈ 47 s < 60 s.
#      Eng wird es, wenn die Seite erst spät antwortet (Bereitschaft nahe 90 s → Vorwärmen wird dann
#      auf ~10 s gekürzt, entfällt) oder wenn der Prüfpunkt Kalender trotzdem einmal wiederholt werden
#      muss (+ bis zu 2 × 40 s): dann können 170 s überschritten werden; das gilt als roter Lauf.
#  (c) Erster Start einer neuen Version ohne fertige Monatsdatei (BUG-123, AK-11): Die Seite zeigt dann den
#      Hinweis „wird gerade berechnet“. Läuft das Warten im ersten Versuch des Prüfpunkts Kalender in die
#      Zeitüberschreitung und steht dieser Hinweis noch auf der Seite, wartet der Test weiter, insgesamt bis
#      T_KALENDER_BERECHNUNG_MS = 240 s. Rechnung für diesen Fall (gerechnet, nicht gemessen):
#      5 s Pause + Bereitschaft (bis ca. 98 s) + Version/Anmeldung/Karte/Feed ≈ 30 s + Kalender 40 s
#      + bis zu 6 s Suche nach dem Hinweis (liegen NICHT innerhalb der 240 s) + weitere 200 s
#      (T_KALENDER_BERECHNUNG_MS - T_KALENDER) + Wiederholung 40 s + 10 s (Programmfehler, Beenden)
#      ≈ 429 s, wenn alles bis zum Anschlag läuft (gerechnet, nicht gemessen). Das liegt über dem
#      Schritt-Limit von 420 s (deploy.yml, Schritt live1, 7 Minuten): Bei voll ausgereizter Bereitschaft
#      UND voll ausgeschöpfter Berechnungszeit reicht das Limit nicht; ohne Bereitschaftsverzug (≈ 5–10 s
#      statt 98 s) sind es ≈ 340 s. Ohne Hinweis kommen im ersten Versuch bis zu 6 s Suchzeit zu den 40 s
#      hinzu (ca. 46 s); in der Wiederholung wird nicht gesucht (40 s). Die 170-s-Grenze (schnittstelle.py
#      KURZTEST_ZEITLIMIT_S) gilt für Übungsseiten ohne Hinweis unverändert: Ohne Hinweis (Fehlermeldung,
#      Kalender hängt ohne Hinweistext) bleibt es bei 40 s (erster Versuch ca. 46 s) und in der Wiederholung
#      bei 40 s.
T_SEITE = 20000
T_ANMELDUNG = 30000
T_KARTE_MARKER = 12000
T_FEED = 25000
T_KALENDER = 40000   # bewusst unverändert streng: nach dem Vorwärmen ist das Laden ≈ 17–20 s
T_NACHLAUF_FEHLER = 2500   # Zeit, in der verzögerte Programmfehler noch auftauchen dürfen
# Erster Start einer neuen Version ohne fertige Monatsdatei (BUG-123, AK-11): Die Seite zeigt den Hinweis
# „wird gerade berechnet“, der Kalender ist erst nach der ersten Monatsrechnung fertig. Die dauert nach einem
# Neustart ohne Datei ca. 3,6 Minuten = 216 s (Messung im Dienstprotokoll über 7 Tage: 15 Rechnungen, jeweils
# 3:33 bis 3:42 Minuten). Gesamtwartezeit des ERSTEN Versuchs, nur wenn der Hinweis noch zu sehen ist: ca. 240 s.
T_KALENDER_BERECHNUNG_MS = 240000

# Bereitschaftsphase vor dem ersten Prüfpunkt (Sekunden)
T_BEREITSCHAFT_S = 90        # so lange wird auf die erste Antwort der Startseite gewartet
BEREITSCHAFT_PAUSE_S = 3     # Pause zwischen zwei Abfragen
BEREITSCHAFT_ANFRAGE_S = 8   # Wartezeit einer einzelnen Abfrage

# Vorwärm-Phase Kalender (Sekunden; nie ein Ergebnis, nur ein Hinweis im Protokoll)
T_VORWAERM_S = 60            # Obergrenze für Antwort und vollständiges Lesen des Körpers
VORWAERM_BIS_S = 100         # Bereitschaft + Vorwärmen enden spätestens so viele Sekunden nach Start
VORWAERM_MIN_S = 15          # bleibt weniger Zeit, wird nicht vorgewärmt
VORWAERM_LESE_S = 5          # Wartezeit je Lesevorgang, sobald die Antwort begonnen hat

_URL_RE = re.compile(r"https?://[^\s)'\"]+")


class Bericht:
    """Sammelt alle Ausgaben; jede Zeile läuft durch die Maskierung des Geheimnisses."""

    def __init__(self, ordner: Path, geheimnis: str):
        self.ordner = ordner
        self.geheimnis = geheimnis
        self.zeilen: List[str] = []
        self.bestanden: List[str] = []
        self.gescheitert: dict = {}
        self.fremdfehler: List[str] = []
        self.version_gesehen: Optional[str] = None
        self.start = time.monotonic()

    def maske(self, text: str) -> str:
        if self.geheimnis:
            text = text.replace(self.geheimnis, "***")
        return text

    def zeile(self, text: str) -> None:
        t = self.maske(text)
        self.zeilen.append(t)
        print(t, flush=True)

    def ok(self, pruefpunkt: str) -> None:
        self.bestanden.append(pruefpunkt)
        self.zeile(f"bestanden: {pruefpunkt}")

    def fehl(self, pruefpunkt: str, grund: str) -> None:
        self.gescheitert[pruefpunkt] = grund
        self.zeile(f"gescheitert: {pruefpunkt}")
        self.zeile(f"    Grund: {grund}")

    def speichere(self, exitcode: int) -> None:
        try:
            self.ordner.mkdir(parents=True, exist_ok=True)
            dauer = round(time.monotonic() - self.start, 1)
            (self.ordner / "kurztest-ergebnis.txt").write_text(
                "\n".join(self.zeilen) + f"\nDauer: {dauer} s\nRückgabewert: {exitcode}\n", encoding="utf-8")
            daten = {
                "ok": exitcode == EXIT_OK, "rueckgabewert": exitcode, "dauer_s": dauer,
                "version_gesehen": self.version_gesehen,
                "bestanden": self.bestanden, "gescheitert": self.gescheitert,
                "fremdfehler": self.fremdfehler,
            }
            (self.ordner / "kurztest-ergebnis.json").write_text(
                self.maske(json.dumps(daten, ensure_ascii=False, indent=2)), encoding="utf-8")
        except OSError as e:  # Ergebnis-Ordner nicht beschreibbar: Ausgabe bleibt maßgeblich
            print(f"Hinweis: Ergebnisdateien nicht geschrieben ({e.__class__.__name__})", flush=True)


# ── Fehlerbeobachtung im Browser ────────────────────────────────────────────────
_INIT_SKRIPT = """
(() => {
  window.__fa_toasts = [];
  const beobachte = () => {
    const el = document.getElementById('toast');
    if (!el) { return false; }
    new MutationObserver(() => { if (el.textContent) window.__fa_toasts.push(el.textContent); })
      .observe(el, { childList: true, characterData: true, subtree: true });
    return true;
  };
  document.addEventListener('DOMContentLoaded', beobachte);
})();
"""


def _herkunft(stack: str, eigene_origin: str) -> str:
    """„eigen“ wenn mindestens ein Stapel-Eintrag von der geprüften Seite stammt, „fremd“ wenn alle
    erkennbaren Einträge von anderen Adressen kommen; ohne erkennbare Adresse zählt der Fehler als eigen."""
    urls = _URL_RE.findall(stack or "")
    if not urls:
        return "eigen"
    for u in urls:
        p = urlparse(u)
        if f"{p.scheme}://{p.netloc}" == eigene_origin:
            return "eigen"
    return "fremd"


def warte_auf_bereitschaft(adresse: str, bericht: Bericht) -> bool:
    """Bereitschaftsphase (rein lesend): Fragt die Startseite wiederholt ab, bis sie antwortet.

    „Antwortet“ heißt: eine HTTP-Antwort unter 500. Keine Antwort, Verbindungsfehler und 5xx (z. B.
    Webserver läuft, App noch nicht) zählen als „noch nicht bereit“. Nach höchstens T_BEREITSCHAFT_S
    wird aufgegeben; der Prüfpunkt Version scheitert dann wie bisher mit „Seite nicht erreichbar“.
    Die Abfrage geht direkt (ohne Umgebungs-Proxy), wie der Browser des Kurztests auch."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = adresse.rstrip("/") + "/"
    start = time.monotonic()
    versuch = 0
    while True:
        versuch += 1
        rest = T_BEREITSCHAFT_S - (time.monotonic() - start)
        status: Optional[int] = None
        try:
            with opener.open(url, timeout=max(1.0, min(float(BEREITSCHAFT_ANFRAGE_S), rest))) as r:
                status = r.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception:
            status = None
        dauer = time.monotonic() - start
        if status is not None and status < 500:
            if versuch > 1:
                bericht.zeile(f"Hinweis: Die Seite antwortet erst nach {dauer:.0f} s (Versuch {versuch}); "
                              "die Prüfpunkte beginnen jetzt.")
            return True
        if dauer + BEREITSCHAFT_PAUSE_S >= T_BEREITSCHAFT_S:
            bericht.zeile(f"Hinweis: Die Seite antwortet auch nach {dauer:.0f} s nicht "
                          f"({'keine Antwort' if status is None else 'HTTP ' + str(status)}).")
            return False
        time.sleep(BEREITSCHAFT_PAUSE_S)


def warte_auf_kalender_vorwaermen(adresse: str, bericht: Bericht) -> None:
    """Vorwärm-Phase (rein lesend): Ein einziger GET auf /calendar für den aktuellen Monat.

    Der Körper wird vollständig gelesen, damit der Server den Monat fertig rechnet und zwischenspeichert.
    Monat und Jahr nimmt das Frontend (web/index.html, CalendarView: new Date().getMonth()+1 / getFullYear())
    aus der Ortszeit des Browsers; hier ebenso aus der Ortszeit des Läufers. Ohne Anmeldung, ohne
    Umgebungs-Proxy (wie warte_auf_bereitschaft). Setzt nie ein Ergebnis: nur eine Hinweiszeile mit
    Dauer und Bytes oder dem Grund, warum es nicht geklappt hat. Die Bytes sind die übertragenen
    (bei Kompression also weniger als der entpackte Körper)."""
    jetzt_s = time.monotonic() - bericht.start
    frei = min(float(T_VORWAERM_S), VORWAERM_BIS_S - jetzt_s)
    if frei < VORWAERM_MIN_S:
        bericht.zeile(f"Hinweis: Kalender nicht vorgewärmt (nur noch {max(frei, 0):.0f} s im Zeitplan).")
        return
    jetzt = datetime.now()
    p = urlparse(adresse.rstrip("/"))
    pfad = (p.path or "") + f"/calendar?month={jetzt.month}&year={jetzt.year}"
    start = time.monotonic()
    conn = None
    try:
        klasse = http.client.HTTPSConnection if p.scheme == "https" else http.client.HTTPConnection
        conn = klasse(p.netloc, timeout=frei)
        conn.request("GET", pfad, headers={"Accept": "application/json", "Accept-Encoding": "gzip",
                                           "User-Agent": "fotoalert-kurztest"})
        antwort = conn.getresponse()
        n = 0
        while True:
            rest = frei - (time.monotonic() - start)
            if rest <= 0:
                raise TimeoutError("Obergrenze erreicht")
            if conn.sock is not None:
                conn.sock.settimeout(max(0.5, min(float(VORWAERM_LESE_S), rest)))
            stueck = antwort.read(1 << 20)
            if not stueck:
                break
            n += len(stueck)
        dauer = time.monotonic() - start
        if antwort.status >= 400:
            bericht.zeile(f"Hinweis: Kalender-Vorwärmen: HTTP {antwort.status} nach {dauer:.1f} s ({n} Bytes).")
        else:
            bericht.zeile(f"Hinweis: Kalender vorgewärmt in {dauer:.1f} s ({n} Bytes, HTTP {antwort.status}).")
    except Exception as e:  # nur ein Hinweis, nie ein Ergebnis
        dauer = time.monotonic() - start
        art = "Zeitüberschreitung" if isinstance(e, TimeoutError) else e.__class__.__name__
        bericht.zeile(f"Hinweis: Kalender-Vorwärmen nicht abgeschlossen nach {dauer:.1f} s ({art}).")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


class Sitzung:
    """Der frische Browser und alles, was er beobachtet."""

    def __init__(self, page, context, adresse: str):
        self.page = page
        self.context = context
        self.adresse = adresse.rstrip("/")
        p = urlparse(self.adresse)
        self.origin = f"{p.scheme}://{p.netloc}"
        self.eigene_fehler: List[str] = []
        self.fremde_fehler: List[str] = []
        self.antworten: List[tuple] = []   # (Zeitstempel, Methode, Pfad, Status)
        self.login_antworten: List[int] = []
        page.on("pageerror", self._seitenfehler)
        page.on("response", self._antwort)

    def _seitenfehler(self, e) -> None:
        text = (getattr(e, "message", None) or str(e)).strip()
        stack = getattr(e, "stack", "") or ""
        if _herkunft(stack, self.origin) == "eigen":
            self.eigene_fehler.append(text[:300])
        else:
            self.fremde_fehler.append(text[:300])

    def _antwort(self, r) -> None:
        try:
            pfad = urlparse(r.url).path
            if r.url.startswith(self.origin):
                self.antworten.append((time.monotonic(), r.request.method, pfad, r.status))
                if r.request.method == "POST" and pfad.endswith("/login"):
                    self.login_antworten.append(r.status)
        except Exception:
            pass

    def antworten_seit(self, t0: float, pfad_ende: str) -> List[int]:
        return [s for (t, m, p, s) in self.antworten if t >= t0 and p.endswith(pfad_ende)]

    def toasts(self) -> List[str]:
        try:
            return list(self.page.evaluate("() => window.__fa_toasts || []"))
        except Exception:
            return []


def _foto(sitzung: Sitzung, bericht: Bericht, name: str) -> None:
    try:
        bericht.ordner.mkdir(parents=True, exist_ok=True)
        ziel = bericht.ordner / f"fehler-{name}.png"
        sitzung.page.screenshot(path=str(ziel), full_page=False)
    except Exception:
        pass


def _onboarding_schliessen(page, warte_ms: int) -> None:
    """Das Willkommens-Overlay (falls erschienen) wegklicken, damit es nichts verdeckt."""
    try:
        page.wait_for_selector("#onboarding-overlay.open", timeout=warte_ms)
        page.evaluate("() => { if (typeof Onboarding !== 'undefined') Onboarding.close(); }")
        page.wait_for_selector("#onboarding-overlay:not(.open)", timeout=3000)
    except Exception:
        pass


# ── Prüfpunkt 1: Version ────────────────────────────────────────────────────────
def _lese_version(page) -> Optional[str]:
    try:
        page.wait_for_function("() => typeof APP_VERSION !== 'undefined'", timeout=T_SEITE)
        return page.evaluate("() => APP_VERSION")
    except Exception:
        return None


def pruefe_version(s: Sitzung, bericht: Bericht, erwartet: str, versuch: int) -> Optional[str]:
    try:
        if versuch == 1:
            s.page.goto(s.adresse + "/", wait_until="domcontentloaded", timeout=T_SEITE)
        else:
            time.sleep(3)
            s.page.goto(s.adresse + "/", wait_until="domcontentloaded", timeout=T_SEITE)
    except Exception as e:
        return f"Seite nicht erreichbar ({e.__class__.__name__})"
    gesehen = _lese_version(s.page)
    bericht.version_gesehen = gesehen
    if gesehen is None:
        return "Die Seite zeigt keine App-Version (Seite unvollständig geladen?)"
    if gesehen != erwartet:
        return f"{GRUND_FALSCHE_VERSION}: erwartet {erwartet}, gesehen {gesehen}"
    return None


# ── Prüfpunkt 2: Anmeldung (einziger Baustein, der sich anmeldet — US-136) ─────────
def anmelden(s: Sitzung, bericht: Bericht, passwort: str) -> Optional[str]:
    """Meldet sich mit dem Prüf-Zugang an. Liefert None bei Erfolg, sonst den Grund.

    Höchstens ein Versuch, der den Server erreicht: Nach einer Ablehnung (4xx) kein zweiter Versuch (AK4).
    Nur wenn der Server nie geantwortet hat oder mit 5xx antwortete (kein Passwortfehler), folgt einmal
    ein weiterer Versuch (AK11)."""
    page = s.page
    for versuch in (1, 2):
        _onboarding_schliessen(page, 1500)
        vorher = len(s.login_antworten)
        try:
            page.wait_for_selector("#login-pw", state="visible", timeout=T_SEITE)
            page.fill("#login-pw", passwort)
            page.click(".login-btn")
            page.wait_for_function(
                "() => (typeof Auth !== 'undefined' && Auth.isLoggedIn()) || "
                "((document.getElementById('login-err')||{}).textContent||'').length > 0",
                timeout=T_ANMELDUNG)
        except Exception:
            pass
        neu = s.login_antworten[vorher:]
        status = neu[-1] if neu else None
        angemeldet = False
        try:
            angemeldet = bool(page.evaluate("() => typeof Auth !== 'undefined' && Auth.isLoggedIn()"))
        except Exception:
            pass
        if angemeldet and status == 200:
            rolle = None
            try:
                rolle = page.evaluate("() => CFG.role")
            except Exception:
                pass
            if rolle == "host":
                return "Der Prüf-Zugang hat Host-Rechte; erwartet sind Gast-Rechte (der Live-Check darf nur lesen)"
            return None
        # Passwortfeld leeren, bevor irgendein Bildschirmfoto entsteht
        try:
            page.fill("#login-pw", "")
        except Exception:
            pass
        if status == 429:
            return "Anmeldesperre aktiv (zu viele Fehlversuche); kein weiterer Versuch"
        if status is not None and 400 <= status < 500:
            return f"Die Seite lehnt den Prüf-Zugang ab (HTTP {status}); kein zweiter Anmeldeversuch"
        if versuch == 2:
            if status is None:
                return "Anmeldung ohne Antwort der Seite (zweimal)"
            return f"Anmeldung scheitert (HTTP {status}, zweimal)"
        bericht.zeile("Hinweis: Anmeldung hat den Server nicht erreicht oder Serverfehler — ein weiterer Versuch")
        time.sleep(3)
    return "Anmeldung scheitert"


# ── Prüfpunkt 3: Karte ──────────────────────────────────────────────────────────
_MARKER = '#map .leaflet-marker-icon svg[viewBox="0 0 28 38"]'


def pruefe_karte(s: Sitzung, bericht: Bericht, versuch: int) -> Optional[str]:
    page = s.page
    try:
        if versuch == 1:
            page.click("#tab-map")
        else:
            page.evaluate("() => MapView.loadMarkers()")   # Daten neu abfragen
        page.wait_for_selector("#page-map.active #map.leaflet-container", timeout=T_SEITE)
    except Exception as e:
        return f"Die Karte öffnet sich nicht ({e.__class__.__name__})"
    try:
        page.wait_for_selector(_MARKER, timeout=T_KARTE_MARKER)
    except Exception:
        return "Die Karte zeigt keine einzige Ortsmarkierung"
    return None


# ── Prüfpunkt 4: Feed ───────────────────────────────────────────────────────────
# Gezählt werden die Einträge, die der Server liefert (Feed.data) — nicht die Karten nach den
# Standard-Filtern der Oberfläche: Die blenden Routine-Ereignisse aus und könnten an einem ruhigen
# Tag einen funktionierenden Feed leer aussehen lassen. Zusätzlich darf die Oberfläche keine
# Fehlermeldung zeigen.
_FEED_BEREIT = """() => {
  const c = document.querySelector('#feed-content');
  if (!c) return false;
  if (typeof Feed !== 'undefined' && Feed.data && Feed.data.length > 0) return true;
  if (c.querySelector('.spinner')) return false;
  return c.children.length > 0;
}"""


def pruefe_feed(s: Sitzung, bericht: Bericht, versuch: int) -> Optional[str]:
    page = s.page
    try:
        if versuch == 1:
            page.click("#tab-feed")
            page.evaluate("() => { if (Feed.mode !== 'feed') Feed.setMode('feed'); }")
        else:
            page.evaluate("() => { if (Feed.mode !== 'feed') Feed.setMode('feed'); return Feed.load(); }")
        page.wait_for_function(_FEED_BEREIT, timeout=T_FEED)
    except Exception as e:
        return f"Der Feed lädt nicht ({e.__class__.__name__})"
    n = page.evaluate("() => (typeof Feed !== 'undefined' && Feed.data) ? Feed.data.length : 0")
    text = page.evaluate("() => (document.querySelector('#feed-content')||{}).innerText || ''")
    if "nicht erreichbar" in text:
        return "Der Feed zeigt eine Fehlermeldung (Backend nicht erreichbar)"
    if n < 1:
        return "Der Feed zeigt keinen einzigen Eintrag"
    return None


# ── Prüfpunkt 5: Kalender ───────────────────────────────────────────────────────
_KALENDER_BEREIT = """() => {
  const c = document.querySelector('#feed-content');
  return !!(c && c.querySelector('.cal-nav') && !c.querySelector('.spinner'));
}"""


# Hinweis der Seite beim ersten Start ohne Monatsdatei (web/index.html, CalendarView.loadMonth):
# „Der Kalender wird gerade berechnet, bitte kurz warten.“ mit Ladesymbol, im Bereich #feed-content.
# Das übliche Laden („Jahreskalender wird geladen…“) und Fehlermeldungen enthalten diesen Satz nicht.
HINWEIS_BERECHNUNG = "wird gerade berechnet"


# Erkennung des Hinweises nicht als Momentaufnahme: nach der Zeitüberschreitung bis zu HINWEIS_SUCHE_S lang
# alle HINWEIS_SUCHE_TAKT_MS erneut prüfen (Ausnahmen in evaluate und ein fehlendes #feed-content zählen
# nur für diese eine Prüfung als „nicht gesehen“).
HINWEIS_SUCHE_S = 6
HINWEIS_SUCHE_TAKT_MS = 500


def _hinweis_lesen(page):
    """Liefert (Text von #feed-content, Name der Ausnahmeklasse oder None)."""
    try:
        text = page.evaluate("() => (document.querySelector('#feed-content') || {}).innerText || ''")
    except Exception as e:
        return "", e.__class__.__name__
    return (text if isinstance(text, str) else ""), None


def _zeigt_berechnungshinweis(page, bericht: Bericht, t0: float) -> bool:
    ende = time.monotonic() + HINWEIS_SUCHE_S
    text, ausnahme = "", None
    while True:
        text, ausnahme = _hinweis_lesen(page)
        if HINWEIS_BERECHNUNG in text:
            return True
        if time.monotonic() >= ende:
            break
        page.wait_for_timeout(HINWEIS_SUCHE_TAKT_MS)
    # Nur zur Erklärung, ohne Einfluss auf das Ergebnis (bericht.zeile maskiert Geheimnisse).
    dauer = time.monotonic() - t0
    if ausnahme:
        bericht.zeile(f"Hinweis: Berechnungshinweis nicht prüfbar nach {dauer:.0f} s "
                      f"(Ausnahme in evaluate: {ausnahme}).")
    else:
        anfang = " ".join(text.split())[:80]
        bericht.zeile(f"Hinweis: Kein Berechnungshinweis sichtbar nach {dauer:.0f} s "
                      f"(Seitentext beginnt mit: {anfang}).")
    return False


def pruefe_kalender(s: Sitzung, bericht: Bericht, versuch: int) -> Optional[str]:
    page = s.page
    t0 = time.monotonic()
    n_toasts = len(s.toasts())
    try:
        page.click("#tab-feed")
        if versuch == 2:
            page.evaluate("() => { try { CalendarView._monthCache.clear(); } catch (e) {} }")   # Daten neu abfragen
            page.evaluate("() => Feed.setMode('feed')")
        page.click("#fmb-calendar")
        try:
            page.wait_for_function(_KALENDER_BEREIT, timeout=T_KALENDER)
        except Exception:
            # Nur im ersten Versuch und nur, wenn die Seite noch den Hinweis „wird gerade berechnet“ zeigt:
            # weiterwarten bis zur Gesamtzeit T_KALENDER_BERECHNUNG_MS (BUG-123, AK-11). Sonst bleibt es
            # bei der Zeitüberschreitung nach T_KALENDER (Fehlermeldung, hängender Kalender ohne Hinweis, Wiederholung).
            if versuch != 1 or not _zeigt_berechnungshinweis(page, bericht, t0):
                raise
            try:
                page.wait_for_function(_KALENDER_BEREIT, timeout=T_KALENDER_BERECHNUNG_MS - T_KALENDER)
            except Exception:
                bericht.zeile(f"Hinweis: Der Kalender zeigte „wird gerade berechnet“ und war nach "
                              f"{time.monotonic() - t0:.0f} s noch nicht fertig.")
                raise
            bericht.zeile(f"Hinweis: Der Kalender zeigte „wird gerade berechnet“ und war nach "
                          f"{time.monotonic() - t0:.0f} s fertig.")
    except Exception as e:
        return f"Der Kalender öffnet sich nicht ({e.__class__.__name__})"
    page.wait_for_timeout(500)
    fehler = [st for st in s.antworten_seit(t0, "/calendar") if st >= 400]
    if fehler:
        return f"Der Kalender meldet einen Fehler (HTTP {fehler[0]})"
    for t in s.toasts()[n_toasts:]:
        if "konnte nicht geladen" in t or "Fehler" in t:
            return f"Der Kalender zeigt eine Fehlermeldung ({t[:80]})"
    return None


# ── Prüfpunkt 6: Programmfehler ─────────────────────────────────────────────────
def pruefe_programmfehler(s: Sitzung, bericht: Bericht, versuch: int) -> Optional[str]:
    page = s.page
    if versuch == 2:
        # Wiederholung: Seite neu laden (Sitzungscookie bleibt, kein zweiter Anmeldeversuch) und die
        # geprüften Seiten erneut öffnen — ein dauerhafter Fehler tritt dabei wieder auf.
        s.eigene_fehler.clear()
        try:
            page.reload(wait_until="domcontentloaded", timeout=T_SEITE)
            page.wait_for_function("() => typeof Auth !== 'undefined' && Auth.isLoggedIn()", timeout=T_SEITE)
            _onboarding_schliessen(page, 1500)
        except Exception as e:
            return f"Die Seite lädt nach dem Neuladen nicht ({e.__class__.__name__})"
        for ziel in ("#tab-map", "#tab-feed"):
            try:
                page.click(ziel)
            except Exception:
                pass
    page.wait_for_timeout(T_NACHLAUF_FEHLER)
    if s.eigene_fehler:
        return "Programmfehler im FotoAlert-Code: " + " | ".join(dict.fromkeys(s.eigene_fehler))[:400]
    return None


# ── Ablauf ──────────────────────────────────────────────────────────────────────
def mit_wiederholung(bericht: Bericht, s: Optional[Sitzung], name: str,
                     pruefung: Callable[[int], Optional[str]]) -> bool:
    """Führt einen Prüfpunkt aus; scheitert er, genau eine Wiederholung (AK11)."""
    grund = pruefung(1)
    if grund is not None:
        bericht.zeile(f"Wiederholung für {name} (erster Versuch: {grund})")
        grund = pruefung(2)
    if grund is None:
        bericht.ok(name)
        return True
    bericht.fehl(name, grund)
    if s is not None:
        _foto(s, bericht, name)
    return False


def lauf(adresse: str, erwartete_version: str, ordner: Path) -> int:
    passwort = os.environ.get(GEHEIMNIS_NAME, "")
    bericht = Bericht(ordner, passwort)
    bericht.zeile(f"Kurztest gegen {adresse}, erwartete Version {erwartete_version}")

    if not passwort.strip():
        bericht.fehl(PP_ANMELDUNG,
                     f"Prüf-Zugang fehlt: Das Geheimnis {GEHEIMNIS_NAME} ist nicht angelegt oder leer. "
                     "Es wurde kein Anmeldeversuch gemacht.")
        bericht.zeile("Ergebnis: nicht einsatzbereit")
        bericht.speichere(EXIT_NICHT_EINSATZBEREIT)
        return EXIT_NICHT_EINSATZBEREIT

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        bericht.zeile("Ergebnis: nicht einsatzbereit — Playwright ist nicht installiert")
        bericht.speichere(EXIT_NICHT_EINSATZBEREIT)
        return EXIT_NICHT_EINSATZBEREIT

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True)
        except Exception as e:
            bericht.zeile(f"Ergebnis: nicht einsatzbereit — Browser startet nicht ({e.__class__.__name__})")
            bericht.speichere(EXIT_NICHT_EINSATZBEREIT)
            return EXIT_NICHT_EINSATZBEREIT
        try:
            # frischer Browser: neuer Kontext ohne Zwischenspeicher, Service Worker gesperrt,
            # keine Berechtigungen (kein Standort)
            context = browser.new_context(service_workers="block", viewport={"width": 430, "height": 900})
            context.set_default_timeout(T_SEITE)
            context.add_init_script(_INIT_SKRIPT)
            page = context.new_page()
            s = Sitzung(page, context, adresse)

            # 0 Bereitschaft: erst warten, bis die Seite (z. B. nach einem Dienst-Neustart) antwortet
            bereit = warte_auf_bereitschaft(adresse, bericht)

            # 0b Kalender vorwärmen (nur lesend, nur wenn die Seite bereit ist, setzt nie ein Ergebnis)
            if bereit:
                warte_auf_kalender_vorwaermen(adresse, bericht)

            # 1 Version
            mit_wiederholung(bericht, s, PP_VERSION,
                             lambda v: pruefe_version(s, bericht, erwartete_version, v))
            seite_da = bericht.version_gesehen is not None

            # 2 Anmeldung (ohne erreichbare Seite nicht möglich)
            angemeldet = False
            if seite_da:
                grund = anmelden(s, bericht, passwort)
                if grund is None:
                    bericht.ok(PP_ANMELDUNG)
                    angemeldet = True
                    _onboarding_schliessen(page, 4000)
                else:
                    bericht.fehl(PP_ANMELDUNG, grund)
                    _foto(s, bericht, PP_ANMELDUNG)
            else:
                bericht.fehl(PP_ANMELDUNG, "nicht geprüft, weil die Seite nicht geladen werden konnte")

            # 3–5 Karte, Feed, Kalender, 6 Programmfehler (nur angemeldet möglich)
            if angemeldet:
                mit_wiederholung(bericht, s, PP_KARTE, lambda v: pruefe_karte(s, bericht, v))
                mit_wiederholung(bericht, s, PP_FEED, lambda v: pruefe_feed(s, bericht, v))
                mit_wiederholung(bericht, s, PP_KALENDER, lambda v: pruefe_kalender(s, bericht, v))
                mit_wiederholung(bericht, s, PP_PROGRAMMFEHLER, lambda v: pruefe_programmfehler(s, bericht, v))
            else:
                for pp in (PP_KARTE, PP_FEED, PP_KALENDER, PP_PROGRAMMFEHLER):
                    bericht.fehl(pp, "nicht geprüft, weil die Anmeldung fehlschlug")

            # Fehler aus fremden Quellen: kein Scheitern, aber in der Meldung
            for text in dict.fromkeys(s.fremde_fehler):
                bericht.fremdfehler.append(text)
                bericht.zeile(f"Hinweis (fremde Quelle, kein Rücksprung): {text}")
        finally:
            browser.close()

    if bericht.gescheitert:
        bericht.zeile("Ergebnis: Kurztest nicht bestanden")
        code = EXIT_GESCHEITERT
    else:
        bericht.zeile("Ergebnis: alle sechs Prüfpunkte bestanden")
        code = EXIT_OK
    bericht.speichere(code)
    return code


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="TASK-118 Kurztest (rein lesend)")
    ap.add_argument("--adresse", required=True, help="öffentliche Adresse der App")
    ap.add_argument("--erwartete-version", required=True, help="App-Version, die live sein soll")
    ap.add_argument("--ergebnis-ordner", required=True, help="Ordner für Ergebnisdateien und Bildschirmfotos")
    a = ap.parse_args(argv)
    return lauf(a.adresse, a.erwartete_version, Path(a.ergebnis_ordner))


if __name__ == "__main__":
    sys.exit(main())
