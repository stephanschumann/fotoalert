"""TASK-118 Teststufe 2 — lokale Attrappen-Server für den Kurztest (HILFSMODUL, keine Tests).

Zwei Server, beide nur auf dem eigenen Rechner, im Test gestartet und im Teardown beendet:
  - „App“ unter http://127.0.0.1:<port>: liefert die ECHTEN Seiten aus FotoAlert/web/ (nur gelesen,
    nie verändert; Änderungen nur in der ausgelieferten Kopie im Speicher) und beantwortet die
    Datenabfragen der App mit festen Testdaten in der Form von backend/models/schemas.py.
    Bewusst 127.0.0.1 und nicht „localhost“: auf „localhost“ würde die App ihre Daten bei
    localhost:8000 holen — das könnte Stephans laufender Entwicklungs-Server sein.
  - „Fremdquelle“ unter http://localhost:<port2>: Kartenbilder und ein fremdes Skript
    (steht für Kartendienst/Fremdanbieter). Die Kartenbild-Adressen der App werden in der
    ausgelieferten Seite auf diese Fremdquelle umgebogen — kein Aufruf ins Internet.

Gezielt einstellbares Verhalten (Lage): ausgelieferte App-Version, keine Orte, leerer Feed (immer
oder nur bei der ersten Abfrage), Kalender-Fehler, Statusabfrage „degraded“, Kartenbilder gesperrt,
Programmfehler im eigenen Code, Programmfehler nur aus der Fremdquelle. Die Attrappe zählt
Anmeldeversuche (mit Sperre nach 5 Fehlversuchen in 15 Minuten wie der echte Server),
Feed-Abfragen und jede Daten ändernde Anfrage.

Python-3.9-kompatibel, nur Standardbibliothek.
"""
from __future__ import annotations

import json
import re
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

WEB = Path(__file__).resolve().parents[3] / "web"

_TYPEN = {".html": "text/html; charset=utf-8", ".js": "application/javascript", ".css": "text/css",
          ".json": "application/json", ".png": "image/png", ".svg": "image/svg+xml",
          ".ico": "image/x-icon", ".webmanifest": "application/manifest+json", ".md": "text/plain"}
# 1×1-PNG (transparent) als Kartenbild
_PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
                     "0000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")
_KACHEL_ANBIETER = {
    "https://{s}.tile.openstreetmap.org": "osm",
    "https://{s}.basemaps.cartocdn.com": "carto",
    "https://server.arcgisonline.com": "arcgis",
}
SCHREIBEND = ("POST", "PUT", "PATCH", "DELETE")
NICHT_DATEN = {"/login", "/logout"}   # Anmelden/Abmelden ändert keine Daten der App


def _ort(i: int) -> dict:
    return {
        "id": f"attrappe_ort_{i}", "name": f"Attrappe Ort {i}", "description": "Testort der Attrappe",
        "category": "Skyline", "category_key": "SKYLINE",
        "observer_lat": 52.39 + i * 0.01, "observer_lon": 13.06 + i * 0.01,
        "subject_lat": 52.395 + i * 0.01, "subject_lon": 13.07 + i * 0.01,
        "ideal_azimuth_range": [60.0, 120.0], "subject_name": f"Motiv {i}",
        "subject_height_m": 20.0, "subject_width_m": 10.0, "elevation_difference_m": 0.0,
        "observer_floor_height_m": 0.0, "distance_m": 600.0, "focal_length_suggestions": [50, 85],
        "special_notes": "", "solar_alignment_note": "", "lunar_alignment_note": "", "access_note": "",
        "locationscout_url": "", "difficulty": 1, "possible_bodies": ["sun", "moon"], "image_url": None,
        "image_focus_x": 50.0, "image_focus_y": 50.0, "sightline_status": "nicht_geprueft",
        "sightline_angle_deg": None, "land": "Deutschland", "region": "Brandenburg",
        "paused": False, "area_undecided": False,
    }


def _chance(i: int, ort: dict, zeit: datetime) -> dict:
    iso = zeit.isoformat()
    return {
        "id": f"attrappe_chance_{i}", "location_id": ort["id"], "location_name": ort["name"],
        "event_type": "Goldene Stunde Abend", "title": f"Goldene Stunde am {ort['name']}",
        "description": "Testeintrag der Attrappe", "shoot_time": iso,
        "shoot_window_start": (zeit - timedelta(minutes=20)).isoformat(),
        "shoot_window_end": (zeit + timedelta(minutes=20)).isoformat(),
        "overall_score": 0.97, "astronomy_score": 0.97, "weather_score": 0.97, "location_score": 0.97,
        "camera_hints": [{"focal_length_mm": 85, "aperture_suggestion": "f/8", "shutter_suggestion": "1/250",
                          "iso_suggestion": "100", "tripod_required": False, "extra_tip": ""}],
        "subject_azimuth": 90.0, "celestial_azimuth": 92.0, "celestial_altitude": 3.0, "alert_priority": 2,
        "weather_description": "klar", "moon_phase": None, "moon_illumination_pct": None,
        "elevation_difference_m": 0.0, "sunrise_utc": None, "sunset_utc": None, "sunrise_azimuth": None,
        "sunset_azimuth": 280.0, "golden_cloud_score": None, "sightline_status": "nicht_geprueft",
        "sightline_angle_deg": None,
        "observer_lat": ort["observer_lat"], "observer_lon": ort["observer_lon"],
        "subject_lat": ort["subject_lat"], "subject_lon": ort["subject_lon"],
    }


class Lage:
    """Einstellbares Verhalten + Beobachtungen der Attrappe."""

    def __init__(self, version: str, gast_passwort: str, host_passwort: str):
        self.version = version
        self.gast_passwort = gast_passwort
        self.host_passwort = host_passwort
        self.orte: List[dict] = [_ort(1), _ort(2)]
        self.anzahl_feed = 2
        self.feed_modus = "normal"          # normal | leer | erste_leer | fehler
        self.kalender_fehler = False
        self.status = "ok"                  # ok | degraded
        self.kacheln_gesperrt = False
        self.eigener_programmfehler = False
        self.fremder_programmfehler = False
        self.fremd_kennung = "Fremdquelle-Kartendienst-" + secrets.token_hex(4)
        # Beobachtungen
        self.lock = threading.Lock()
        self.anmeldeversuche: List[dict] = []
        self.gesperrte_versuche = 0
        self.feed_abfragen = 0
        self.schreibende_anfragen: List[str] = []
        self.sitzungen: Dict[str, str] = {}
        self.anfragen: List[str] = []

    # Testdaten
    def feed(self) -> List[dict]:
        with self.lock:
            self.feed_abfragen += 1
            n = self.feed_abfragen
        if self.feed_modus == "leer" or (self.feed_modus == "erste_leer" and n == 1):
            return []
        jetzt = datetime.now(timezone.utc).replace(microsecond=0)
        quellen = self.orte or [_ort(9)]   # Feed bleibt auch ohne Orte gefüllt (Prüfpunkte getrennt)
        return [_chance(i, quellen[i % len(quellen)], jetzt + timedelta(hours=3 + i * 5))
                for i in range(self.anzahl_feed)]

    def kalender(self) -> dict:
        jetzt = datetime.now(timezone.utc).replace(microsecond=0)
        ereignisse = [_chance(100, o, jetzt + timedelta(hours=1)) for o in self.orte[:1]]
        return {"status": "ok", "computed_at": jetzt.isoformat(), "total": len(ereignisse), "events": ereignisse}

    def gesundheit(self) -> dict:
        return {"status": self.status, "version": "2.0.0", "locations_count": len(self.orte),
                "locations_active": len(self.orte),
                "subsystems": {"backend": "ok", "cache": "ok", "cache_age_h": 1.0,
                               "weather": "error" if self.status == "degraded" else "ok", "weather_age_h": 1.0,
                               "backup": "ok", "backup_age_h": 2.0},
                "jobs": {}, "precompute_running": False}

    def fehlversuche_in_15_min(self) -> int:
        grenze = time.time() - 15 * 60
        return sum(1 for v in self.anmeldeversuche if not v["erfolg"] and v["zeit"] >= grenze)


class _Basis(BaseHTTPRequestHandler):
    lage: Lage = None  # type: ignore
    fremd_adresse = ""

    def log_message(self, *args):  # keine Konsolenausgabe
        pass

    def _senden(self, code: int, inhalt: bytes, typ: str, kopf: Optional[dict] = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(inhalt)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (kopf or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(inhalt)

    def _json(self, code: int, daten, kopf: Optional[dict] = None) -> None:
        self._senden(code, json.dumps(daten).encode("utf-8"), "application/json", kopf)

    def _koerper(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        roh = self.rfile.read(n) if n else b""
        try:
            return json.loads(roh.decode("utf-8") or "{}")
        except ValueError:
            return {}


class _App(_Basis):
    def _rolle(self) -> Optional[str]:
        roh = self.headers.get("Cookie") or ""
        m = re.search(r"fa_session=([A-Za-z0-9_-]+)", roh)
        return self.lage.sitzungen.get(m.group(1)) if m else None

    def do_GET(self):  # noqa: N802
        pfad = urlparse(self.path).path
        L = self.lage
        with L.lock:
            L.anfragen.append(f"GET {pfad}")
        api = {
            "/health": lambda: L.gesundheit(),
            "/session": lambda: {"role": self._rolle()},
            "/locations": lambda: L.orte,

            "/opportunities/today": lambda: [],
            "/job-status": lambda: {"jobs": {}, "precompute_running": False},
            "/recompute-status": lambda: {"pending": [], "running": False},
            "/ratings": lambda: [],
            "/verifications": lambda: [],
            "/camera-profile": lambda: {},
            "/weather-map": lambda: {"ready": False},
            "/light-pollution-map": lambda: {"ready": False},
        }
        if pfad == "/opportunities":
            if L.feed_modus == "fehler":
                with L.lock:
                    L.feed_abfragen += 1
                return self._json(500, {"detail": "Attrappe: Feed gestört"})
            return self._json(200, L.feed())
        if pfad == "/calendar":
            if L.kalender_fehler:
                return self._json(500, {"detail": "Attrappe: Kalender gestört"})
            return self._json(200, L.kalender())
        if pfad == "/areas":
            return self._json(403, {"detail": "Nur für Host"})
        if pfad in api:
            return self._json(200, api[pfad]())
        if pfad.startswith("/locations/"):
            lid = pfad.split("/")[2]
            for o in L.orte:
                if o["id"] == lid:
                    return self._json(200, o if pfad.count("/") == 2 else [])
            return self._json(404, {"detail": "Location nicht gefunden."})
        return self._datei(pfad)

    def do_HEAD(self):  # noqa: N802
        self.do_GET()

    def _datei(self, pfad: str):
        if pfad in ("", "/"):
            pfad = "/index.html"
        ziel = (WEB / pfad.lstrip("/")).resolve()
        if WEB.resolve() not in ziel.parents or not ziel.is_file():
            return self._json(404, {"detail": "Not Found"})
        inhalt = ziel.read_bytes()
        if ziel.name == "index.html":
            inhalt = self._seite(inhalt.decode("utf-8")).encode("utf-8")
        elif ziel.name == "sw.js":
            inhalt = re.sub(r"const CACHE_NAME = '[^']*'", f"const CACHE_NAME = 'fotoalert-v{self.lage.version}'",
                            inhalt.decode("utf-8")).encode("utf-8")
        self._senden(200, inhalt, _TYPEN.get(ziel.suffix, "application/octet-stream"))

    def _seite(self, html: str) -> str:
        L = self.lage
        html = re.sub(r"const APP_VERSION = '[^']*'", f"const APP_VERSION = '{L.version}'", html)
        for alt, kurz in _KACHEL_ANBIETER.items():
            html = html.replace(alt, f"{self.fremd_adresse}/kacheln/{kurz}")
        zusatz = ""
        if L.eigener_programmfehler:
            zusatz += ("<script>setTimeout(function(){throw new Error("
                       "'Attrappe: Programmfehler im eigenen FotoAlert-Code');}, 1500);</script>\n")
        if L.fremder_programmfehler:
            zusatz += f'<script src="{self.fremd_adresse}/fremd/kartendienst.js"></script>\n'
        return html.replace("</body>", zusatz + "</body>") if zusatz else html

    def do_POST(self):  # noqa: N802
        pfad = urlparse(self.path).path
        L = self.lage
        koerper = self._koerper()
        with L.lock:
            L.anfragen.append(f"POST {pfad}")
            if pfad not in NICHT_DATEN:
                L.schreibende_anfragen.append(f"POST {pfad}")
        if pfad == "/login":
            with L.lock:
                if L.fehlversuche_in_15_min() >= 5:
                    L.gesperrte_versuche += 1
                    return self._json(429, {"detail": "Zu viele Fehlversuche."})
                pw = koerper.get("password", "")
                rolle = "user" if pw == L.gast_passwort else ("host" if pw == L.host_passwort else None)
                L.anmeldeversuche.append({"zeit": time.time(), "erfolg": rolle is not None, "rolle": rolle,
                                          "passwort_gleich_pruefzugang": pw == L.gast_passwort})
                if not rolle:
                    return self._json(401, {"detail": "Falsches Passwort."})
                kennung = secrets.token_hex(16)
                L.sitzungen[kennung] = rolle
            return self._json(200, {"role": rolle},
                              {"Set-Cookie": f"fa_session={kennung}; Path=/; HttpOnly; SameSite=Lax"})
        if pfad == "/logout":
            return self._json(200, {"status": "ok"}, {"Set-Cookie": "fa_session=; Path=/; Max-Age=0"})
        return self._json(403, {"detail": "Attrappe: schreibende Anfragen nicht erlaubt"})

    def _schreibend(self):
        pfad = urlparse(self.path).path
        self._koerper()
        with self.lage.lock:
            self.lage.anfragen.append(f"{self.command} {pfad}")
            self.lage.schreibende_anfragen.append(f"{self.command} {pfad}")
        return self._json(403, {"detail": "Attrappe: schreibende Anfragen nicht erlaubt"})

    do_PUT = do_PATCH = do_DELETE = _schreibend  # noqa: N815


class _Fremd(_Basis):
    def do_GET(self):  # noqa: N802
        pfad = urlparse(self.path).path
        L = self.lage
        if pfad.startswith("/kacheln/"):
            if L.kacheln_gesperrt:
                return self._senden(503, b"gesperrt", "text/plain")
            return self._senden(200, _PNG, "image/png", {"Access-Control-Allow-Origin": "*"})
        if pfad == "/fremd/kartendienst.js":
            js = ("setTimeout(function(){throw new Error(%s);}, 1500);" % json.dumps(L.fremd_kennung)).encode()
            return self._senden(200, js, "application/javascript", {"Access-Control-Allow-Origin": "*"})
        return self._senden(404, b"", "text/plain")


class Attrappen:
    """Startet App-Attrappe und Fremdquelle; stoppe() beendet beide (Teardown)."""

    def __init__(self, lage: Lage):
        self.lage = lage
        fremd_cls = type("Fremd", (_Fremd,), {"lage": lage})
        self._fremd = ThreadingHTTPServer(("127.0.0.1", 0), fremd_cls)
        fremd_adresse = f"http://localhost:{self._fremd.server_address[1]}"
        app_cls = type("App", (_App,), {"lage": lage, "fremd_adresse": fremd_adresse})
        self._app = ThreadingHTTPServer(("127.0.0.1", 0), app_cls)
        self.adresse = f"http://127.0.0.1:{self._app.server_address[1]}"
        self.fremd_adresse = fremd_adresse
        self._faeden = [threading.Thread(target=s.serve_forever, daemon=True) for s in (self._app, self._fremd)]
        for f in self._faeden:
            f.start()

    def stoppe(self) -> None:
        for s in (self._app, self._fremd):
            s.shutdown()
            s.server_close()
        for f in self._faeden:
            f.join(timeout=5)
