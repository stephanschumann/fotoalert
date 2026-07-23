"""
FotoAlert - Rate-Limiting-Hilfsmodul (TASK-86)

Kleine, selbstgebaute In-Memory-Rate-Limit-Loesung fuer den Single-Process-Server
(`--workers 1`, siehe deploy/fotoalert.service). Keine zusaetzliche Abhaengigkeit
(z.B. slowapi) noetig - Muster analog zum bestehenden asyncio.Lock-Gate in
backend/data/elevation.py, hier aber synchron (kein Netzwerk-Warten, nur Zaehlen).

Wiederverwendet an 4 Stellen in backend/main.py:
  1. POST /preview-alignment  - Haeufigkeits-Bremse pro Absenderadresse
  2. POST /login              - Fehlversuch-Drosselung (Lockout) pro Absenderadresse
  3. POST /register-device    - Haeufigkeits-Bremse pro Absenderadresse
  4. (Kalender-Cache-Groessenlimit ist ein separates Problem - eigene, einfache
     OrderedDict-Verdraengung direkt in main.py, kein Rate-Limiter im engeren Sinn)

Weg-Gate-Entscheidung (Stephan, 2026-07-22): Option A - bei Drosselung immer eine
klare 429-Antwort mit Wartezeit (Retry-After-Header + deutscher Klartext), keine
stille Verzoegerung.

Python-3.9-kompatibel.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict, Optional

from fastapi import HTTPException, Request


def client_identity(request: Request) -> str:
    """Absenderadresse fuer Rate-Limiting.

    Der Server laeuft hinter einem Caddy-Reverse-Proxy (siehe deploy/Caddyfile), der
    einzige Hop vor der App - die App selbst ist nur ueber 127.0.0.1 erreichbar
    (deploy/fotoalert.service, --host 127.0.0.1), es gibt keinen weiteren Proxy davor.
    Caddy haengt die von ihm selbst beobachtete Verbindungs-IP nach Standardverhalten
    immer als LETZTEN Eintrag an einen ggf. bereits vorhandenen X-Forwarded-For-Header
    an. Ein Client kann selbst schon einen X-Forwarded-For-Header mit beliebigem Inhalt
    mitschicken (Caddy haengt seine eigene IP dann nur hinten an) - der ERSTE Eintrag
    waere also vom Client frei waehlbar und damit fuer die Rate-Limit-Bremsen wertlos
    (Spoofing-Luecke, TASK-86-Nachbesserung). Deshalb: LETZTER Eintrag = der in dieser
    Ein-Hop-Topologie garantiert von Caddy selbst gesetzte, nicht vom Client faelschbare
    Wert. Ohne Header (z.B. lokaler Dev-Server ohne Proxy, oder Tests) faellt es
    unveraendert auf request.client.host zurueck.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Letzter Eintrag = von Caddy selbst angehaengte, echte Verbindungs-IP;
        # vorangehende Eintraege koennen vom Client frei vorgetaeuscht sein.
        return xff.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


class SlidingWindowRateLimiter:
    """Begrenzt die Aufrufhaeufigkeit pro Schluessel (z.B. Absenderadresse) auf
    `max_calls` innerhalb eines gleitenden Zeitfensters von `window_seconds`.

    Erlaubte Aufrufe werden sofort gezaehlt (kein separates "commit"-Schritt noetig).
    """

    def __init__(self, max_calls: int, window_seconds: float):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = {}

    def _prune(self, key: str, now: float) -> Deque[float]:
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        return hits

    def check(self, key: str) -> Optional[float]:
        """Registriert einen Aufruf, wenn das Limit noch nicht erreicht ist.

        Gibt None zurueck, wenn der Aufruf erlaubt war (wurde sofort gezaehlt).
        Sonst die verbleibende Wartezeit in Sekunden bis zum naechsten erlaubten Aufruf.
        """
        now = time.monotonic()
        hits = self._prune(key, now)
        if len(hits) >= self.max_calls:
            retry_after = self.window_seconds - (now - hits[0])
            return max(retry_after, 0.1)
        hits.append(now)
        return None


class LoginLockout:
    """Zaehlt FEHLGESCHLAGENE Versuche pro Schluessel in einem festen Zeitfenster.

    Anders als SlidingWindowRateLimiter zaehlt hier nur record_failure() - ein
    einzelner erfolgreicher Versuch (record_success()) setzt den Zaehler sofort
    zurueck (AK-5), unabhaengig vom Zeitfenster.
    """

    def __init__(self, max_failures: int, window_seconds: float):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: Dict[str, Deque[float]] = {}

    def _prune(self, key: str, now: float) -> Deque[float]:
        hits = self._failures.setdefault(key, deque())
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        return hits

    def seconds_until_unlocked(self, key: str) -> Optional[float]:
        """None, wenn (noch) nicht gesperrt, sonst verbleibende Sekunden."""
        now = time.monotonic()
        hits = self._prune(key, now)
        if len(hits) >= self.max_failures:
            return max(self.window_seconds - (now - hits[0]), 0.1)
        return None

    def record_failure(self, key: str) -> None:
        now = time.monotonic()
        hits = self._prune(key, now)
        hits.append(now)

    def record_success(self, key: str) -> None:
        self._failures.pop(key, None)


def _raise_rate_limited(retry_after: float) -> None:
    wait_s = int(retry_after) + 1
    raise HTTPException(
        status_code=429,
        detail=f"Zu viele Anfragen, bitte in {wait_s} Sekunden erneut versuchen.",
        headers={"Retry-After": str(wait_s)},
    )


def enforce_rate_limit(limiter: SlidingWindowRateLimiter, request: Request) -> None:
    """Wirft bei ueberschrittenem Limit eine 429 (Option A: klare Meldung + Retry-After).

    Bei erlaubtem Aufruf kehrt die Funktion einfach zurueck (kein Rueckgabewert noetig,
    der Aufruf wurde von check() bereits mitgezaehlt).
    """
    retry_after = limiter.check(client_identity(request))
    if retry_after is not None:
        _raise_rate_limited(retry_after)


def enforce_login_lockout(lockout: LoginLockout, request: Request) -> str:
    """Wirft 429, falls die Absenderadresse aktuell gesperrt ist (AK-4).

    Gibt sonst die Absenderadresse zurueck, damit der Aufrufer sie direkt an
    record_failure()/record_success() weiterreichen kann, ohne sie erneut zu ermitteln.
    """
    key = client_identity(request)
    retry_after = lockout.seconds_until_unlocked(key)
    if retry_after is not None:
        _raise_rate_limited(retry_after)
    return key


# ---------------------------------------------------------------------------
# Geraete-Token-Validierung (TASK-86 AK-6): 20-256 Zeichen, druckbares ASCII/Hex.
# Grosszuegig gewaehlt, weil reale Push-Token-Formate variieren (APNs-Hex-Token
# ~64 Zeichen, aber auch laengere Formate anderer Plattformen sind denkbar).
# ---------------------------------------------------------------------------

DEVICE_TOKEN_MIN_LEN = 20
DEVICE_TOKEN_MAX_LEN = 256


def is_valid_device_token(token: str) -> bool:
    """True, wenn `token` ein plausibles Geraete-Push-Token ist.

    Kriterien (bestaetigt im TASK-86-Weg-Gate): Laenge 20-256 Zeichen, ausschliesslich
    druckbare ASCII-Zeichen (kein Steuerzeichen, kein Whitespace/Newline-Einschleusen).
    """
    if not isinstance(token, str):
        return False
    length = len(token)
    if length < DEVICE_TOKEN_MIN_LEN or length > DEVICE_TOKEN_MAX_LEN:
        return False
    # Druckbares ASCII: Codepoints 33-126 (kein Leerzeichen, keine Steuerzeichen,
    # kein Unicode) - deckt Hex-Token und alphanumerische Token-Formate ab.
    return all(33 <= ord(ch) <= 126 for ch in token)
