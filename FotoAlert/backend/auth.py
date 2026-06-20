"""US-66 — Pflicht-Login mit Rollen-Erkennung (Host / User), Option B.

(Python-3.9-kompatibel: `from __future__ import annotations` macht Annotationen wie
`str | None` / `dict[str, str]` zu Strings, sodass sie auf 3.9 nicht zur Laufzeit
ausgewertet werden.)

Bewusst einfach gehalten (v1-Entscheidung: kein bcrypt/JWT):
- Zwei Passwörter kommen aus der Umgebung (`.env` auf dem Server), nie aus dem Frontend.
- Das Token ist **stateless**: `"<role>.<hmac_sha256(secret, role)>"`. Dadurch übersteht eine
  Session den Server-Neustart (kein In-Memory-Store nötig) und bleibt bis zum Logout gültig
  (Logout = Client verwirft das Token). Verifikation rein serverseitig.

Grenze (dokumentiert, v1): Tokens sind rollen- statt nutzergebunden und nur durch Wechsel von
`FOTOALERT_AUTH_SECRET` global widerrufbar. Für die aktuelle Nutzerbasis akzeptiert; bei Bedarf
später auf signierte, ablaufende Tokens erweiterbar.
"""
from __future__ import annotations

import hashlib
import hmac
import os

from fastapi import Depends, Header, HTTPException

VALID_ROLES = ("host", "user")


def _secret() -> str:
    return os.getenv("FOTOALERT_AUTH_SECRET", "fotoalert-dev-secret-change-me")


def _passwords() -> dict[str, str]:
    """Rolle → erwartetes Passwort (leer = Rolle deaktiviert)."""
    return {
        "host": os.getenv("FOTOALERT_HOST_PASSWORD", ""),
        "user": os.getenv("FOTOALERT_USER_PASSWORD", ""),
    }


def role_for_password(password: str) -> str | None:
    """Gibt die Rolle zurück, deren Passwort übereinstimmt — sonst None."""
    if not password:
        return None
    for role, expected in _passwords().items():
        if expected and hmac.compare_digest(password, expected):
            return role
    return None


def issue_token(role: str) -> str:
    sig = hmac.new(_secret().encode(), role.encode(), hashlib.sha256).hexdigest()
    return f"{role}.{sig}"


def role_for_token(token: str) -> str | None:
    if not token or "." not in token:
        return None
    role, _, sig = token.partition(".")
    if role not in VALID_ROLES:
        return None
    expected = hmac.new(_secret().encode(), role.encode(), hashlib.sha256).hexdigest()
    return role if hmac.compare_digest(sig, expected) else None


# --- FastAPI-Dependencies --------------------------------------------------------

def require_auth(authorization: str = Header(default="")) -> str:
    """Verlangt ein gültiges Bearer-Token; gibt die Rolle zurück oder 401."""
    token = authorization[7:].strip() if authorization[:7].lower() == "bearer " else authorization.strip()
    role = role_for_token(token)
    if not role:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt oder ungültiges Token.")
    return role


def require_host(role: str = Depends(require_auth)) -> str:
    """Verlangt die Host-Rolle (Admin-Aktionen); sonst 403."""
    if role != "host":
        raise HTTPException(status_code=403, detail="Diese Aktion ist nur für den Host.")
    return role
