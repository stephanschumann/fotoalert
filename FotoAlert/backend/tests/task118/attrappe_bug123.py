"""BUG-123 (AK-11) — Erweiterung der Übungsseite für den Live-Check (HILFSMODUL, keine Tests).

Warum es dieses Modul gibt: Die bestehende Übungsseite (attrappe.py, eingefroren) kennt beim Kalender nur
„fertig“ und „Fehlermeldung“. Für AK-11 braucht der Live-Check zusätzlich einen Kalender, der zuerst
„wird gerade berechnet“ meldet (wie der echte Server nach dem Neustart, backend/main.py) und erst nach
einer festen Zeit fertig ist, sowie einen Kalender, der nie antwortet (Seite bleibt im Zustand „lädt“,
ohne den Hinweis „wird gerade berechnet“).

Nichts in attrappe.py wird verändert: Die Erweiterung ist eine Unterklasse der Seite (nur /calendar wird
anders beantwortet, alles andere erledigt die bestehende Klasse) und eine Unterklasse der Lage.

Kalender-Verhalten (Einstellung `kalender_modus` der Lage):
  - "normal"               wie bisher (fertig bzw. Fehlermeldung über `kalender_fehler`)
  - "hinweis_dann_fertig"  Abrufe der SEITE (Browser) bekommen status „calculating“ + Hinweistext, bis
                           `hinweis_sekunden` seit dem ersten Browser-Abruf vergangen sind; danach fertig.
  - "hinweis_dauerhaft"    wie oben, aber nie fertig.
  - "haengt"               Abrufe der Seite bekommen nie eine Antwort (Zustand „lädt“, kein Hinweistext).
Das Vorwärmen des Live-Checks (eigener Abruf, Kennung „fotoalert-kurztest“ im User-Agent) wird nie
blockiert und startet die Uhr nicht: es bekommt im Hinweis-Modus ebenfalls „calculating“, im Modus
„haengt“ die normale fertige Antwort — so misst die Zeit nur den Prüfpunkt Kalender der Seite.

Python-3.9-kompatibel, nur Standardbibliothek.
"""
from __future__ import annotations

import threading
import time
from http.server import ThreadingHTTPServer
from typing import Optional
from urllib.parse import urlparse

from .attrappe import Attrappen, Lage, _App, _Fremd

# Hinweistext wie ihn backend/main.py (_KALENDER_HINWEIS) meldet; die Seite zeigt ihren eigenen Text
# („Der Kalender wird gerade berechnet, bitte kurz warten.“), der Server-Text ist nur Begleitinfo.
HINWEIS_TEXT = "Der Kalender wird gerade berechnet, bitte kurz warten."
VORWAERM_KENNUNG = "fotoalert-kurztest"
MODI = ("normal", "hinweis_dann_fertig", "hinweis_dauerhaft", "haengt")


class LageB123(Lage):
    """Lage der Übungsseite plus Kalender-Verhalten und Beobachtungen für AK-11."""

    def __init__(self, version: str, gast_passwort: str, host_passwort: str):
        super().__init__(version, gast_passwort, host_passwort)
        self.kalender_modus = "normal"
        self.hinweis_sekunden = 0.0
        # Beobachtungen
        self.erster_browser_abruf: Optional[float] = None
        self.letzter_browser_abruf: Optional[float] = None   # Zeitpunkt (time.monotonic) des letzten Abrufs der Seite
        self.browser_abrufe = 0
        self.hinweis_antworten = 0          # Antworten „calculating“ an die Seite
        self.fertig_an_seite = 0            # fertige Kalender-Antworten an die Seite
        self.haengende_abrufe = 0           # Abrufe, die absichtlich nie beantwortet wurden
        self.vorwaerm_abrufe = 0
        self.beendet = threading.Event()    # im Abbau gesetzt, gibt hängende Abrufe frei

    def beobachtung_s(self) -> float:
        """Wie lange die Seite den Kalender beobachtet hat: vom ersten bis zum letzten Abruf der Seite (Sekunden)."""
        with self.lock:
            if self.erster_browser_abruf is None or self.letzter_browser_abruf is None:
                return 0.0
            return self.letzter_browser_abruf - self.erster_browser_abruf


class _AppB123(_App):
    def do_GET(self):  # noqa: N802
        if urlparse(self.path).path != "/calendar" or self.lage.kalender_modus == "normal":
            return super().do_GET()
        L = self.lage
        vorwaermen = VORWAERM_KENNUNG in (self.headers.get("User-Agent") or "")
        with L.lock:
            L.anfragen.append("GET /calendar")
            if vorwaermen:
                L.vorwaerm_abrufe += 1
            else:
                L.browser_abrufe += 1
                jetzt = time.monotonic()
                if L.erster_browser_abruf is None:
                    L.erster_browser_abruf = jetzt
                L.letzter_browser_abruf = jetzt
            start = L.erster_browser_abruf
        if L.kalender_modus == "haengt":
            if vorwaermen:
                return self._json(200, L.kalender())
            with L.lock:
                L.haengende_abrufe += 1
            L.beendet.wait(timeout=600)      # nie eine Antwort; der Abbau gibt frei
            return None
        # Hinweis-Modi
        fertig = (not vorwaermen and L.kalender_modus == "hinweis_dann_fertig"
                  and (time.monotonic() - start) >= L.hinweis_sekunden)
        if fertig:
            with L.lock:
                L.fertig_an_seite += 1
            return self._json(200, L.kalender())
        if not vorwaermen:
            with L.lock:
                L.hinweis_antworten += 1
        return self._json(200, {"status": "calculating", "events": [], "total": 0, "message": HINWEIS_TEXT})


class AttrappenB123(Attrappen):
    """Wie Attrappen (attrappe.py), nur mit der erweiterten Seite; stoppe() gibt hängende Abrufe frei."""

    def __init__(self, lage: LageB123):
        self.lage = lage
        fremd_cls = type("Fremd", (_Fremd,), {"lage": lage})
        self._fremd = ThreadingHTTPServer(("127.0.0.1", 0), fremd_cls)
        fremd_adresse = f"http://localhost:{self._fremd.server_address[1]}"
        app_cls = type("AppB123", (_AppB123,), {"lage": lage, "fremd_adresse": fremd_adresse})
        self._app = ThreadingHTTPServer(("127.0.0.1", 0), app_cls)
        self.adresse = f"http://127.0.0.1:{self._app.server_address[1]}"
        self.fremd_adresse = fremd_adresse
        self._faeden = [threading.Thread(target=s.serve_forever, daemon=True) for s in (self._app, self._fremd)]
        for f in self._faeden:
            f.start()

    def stoppe(self) -> None:
        self.lage.beendet.set()
        super().stoppe()
