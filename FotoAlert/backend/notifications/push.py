"""
Apple Push Notification Service (APNs) Integration.

Sendet lokale Push-Notifications an registrierte iOS-Geräte.
Nutzt JWT-basierte Authentifizierung (APNs Provider API).

Voraussetzungen:
- Apple Developer Account
- APNs Auth Key (.p8 Datei) von developer.apple.com
- Key ID und Team ID aus dem Developer Portal
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import httpx
import jwt  # PyJWT

logger = logging.getLogger(__name__)

# Konfiguration aus Umgebungsvariablen
APNS_KEY_ID = os.getenv("APNS_KEY_ID", "")           # 10-stellige Key-ID
APNS_TEAM_ID = os.getenv("APNS_TEAM_ID", "")         # 10-stellige Team-ID
APNS_KEY_PATH = os.getenv("APNS_KEY_PATH", "")       # Pfad zur .p8 Datei
APNS_BUNDLE_ID = os.getenv("APNS_BUNDLE_ID", "de.fotoalert.app")
APNS_PRODUCTION = os.getenv("APNS_PRODUCTION", "false").lower() == "true"

APNS_HOST = (
    "https://api.push.apple.com"
    if APNS_PRODUCTION
    else "https://api.sandbox.push.apple.com"
)

_jwt_token: Optional[str] = None
_jwt_expires: float = 0


def _get_jwt_token() -> str:
    """Erstellt oder erneuert den APNs JWT-Token (gültig 60 Minuten)."""
    global _jwt_token, _jwt_expires

    now = time.time()
    if _jwt_token and now < _jwt_expires - 60:
        return _jwt_token

    if not APNS_KEY_PATH or not Path(APNS_KEY_PATH).exists():
        logger.warning("APNs Key-Datei nicht gefunden: %s", APNS_KEY_PATH)
        return ""

    private_key = Path(APNS_KEY_PATH).read_text()
    payload = {
        "iss": APNS_TEAM_ID,
        "iat": int(now),
    }
    headers = {
        "alg": "ES256",
        "kid": APNS_KEY_ID,
    }
    _jwt_token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
    _jwt_expires = now + 3600  # 1 Stunde
    return _jwt_token


async def send_push_notification(
    device_token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
    badge: int = 1,
) -> bool:
    """
    Sendet eine Push-Notification an ein iOS-Gerät.

    Returns True bei Erfolg, False bei Fehler.
    """
    token = _get_jwt_token()
    if not token:
        logger.warning("Push-Notification nicht gesendet – APNs nicht konfiguriert.")
        return False

    headers = {
        "authorization": f"bearer {token}",
        "apns-topic": APNS_BUNDLE_ID,
        "apns-push-type": "alert",
        "apns-priority": "10",
    }

    payload = {
        "aps": {
            "alert": {
                "title": title,
                "body": body,
            },
            "badge": badge,
            "sound": "default",
        }
    }
    if data:
        payload.update(data)

    url = f"{APNS_HOST}/3/device/{device_token}"

    try:
        async with httpx.AsyncClient(http2=True, timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                logger.info("Push-Notification gesendet an ...%s", device_token[-8:])
                return True
            else:
                error = response.json().get("reason", "Unbekannt")
                logger.error("APNs-Fehler %s: %s", response.status_code, error)
                return False
    except Exception as e:
        logger.error("Push-Notification Fehler: %s", e)
        return False


async def send_photo_opportunity_notification(
    device_token: str,
    opportunity_title: str,
    shoot_time_str: str,
    location_name: str,
    score: float,
    opportunity_id: str,
) -> bool:
    """Spezialisierte Notification für Foto-Chancen."""
    title = f"📸 {opportunity_title}"
    body = f"{location_name} · {shoot_time_str} · Score {score:.0%}"
    data = {
        "opportunity_id": opportunity_id,
        "deep_link": f"fotoalert://opportunity/{opportunity_id}",
    }
    return await send_push_notification(device_token, title, body, data=data)
