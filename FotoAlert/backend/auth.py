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

from fastapi import Cookie, Depends, HTTPException

VALID_ROLES = ("host", "user")

# TASK-83: Name des HttpOnly-Sitzungscookies (loest den Authorization-Header ab).
SESSION_COOKIE_NAME = "fa_session"


def _load_secret() -> str:
    """TASK-85: Kein Notwert-Fallback mehr. Fehlt `FOTOALERT_AUTH_SECRET` (nicht
    gesetzt oder leer), bricht der Import dieses Moduls sofort mit einer klaren
    Fehlermeldung ab — und damit auch der Import von main.py (das auth.py ganz
    am Anfang importiert), noch bevor die App startet oder ein Endpunkt bindet.

    Bewusste Inkonsistenz (Pre-Mortem TASK-85): Fehlende Rollen-Passwörter
    (`_passwords()` unten) werden weiterhin weich behandelt — die betroffene
    Rolle ist dann einfach deaktiviert, kein Abbruch. Das Auth-Secret ist die
    kryptographische Signaturbasis für ALLE Sitzungs-Tickets; ein Notwert-Fallback
    dort ermöglicht ein frei berechenbares Admin-Ticket ganz ohne Passwort. Diese
    Asymmetrie ist Absicht, kein Bug: einzelne Rollen dürfen fehlen, das Secret nicht.
    """
    value = os.environ.get("FOTOALERT_AUTH_SECRET", "")
    if not value:
        raise RuntimeError(
            "FOTOALERT_AUTH_SECRET ist nicht gesetzt (oder leer). "
            "Diese Umgebungsvariable muss vor dem Start des Servers gesetzt "
            "werden — es gibt keinen Notwert-Fallback mehr."
        )
    return value


# Wird einmal beim Modul-Laden ausgewertet (siehe _load_secret-Docstring),
# nicht erst beim ersten Token-Aufruf.
_SECRET = _load_secret()


def _secret() -> str:
    return _SECRET


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

def require_auth(fa_session: str = Cookie(default="")) -> str:
    """TASK-83: Verlangt ein gültiges Sitzungs-Cookie; gibt die Rolle zurück oder 401.

    Kein Authorization-Header-Fallback mehr (Weg-Gate-Entscheidung 3) — ein alter,
    vor der Migration ausgestellter Bearer-Token authentifiziert dadurch bewusst nicht
    mehr (Zwangs-Logout aller bestehenden Sessions, Weg-Gate-Entscheidung 1). Der
    Parametername `fa_session` muss exakt dem Cookie-Namen (SESSION_COOKIE_NAME)
    entsprechen, da FastAPI den Cookie standardmäßig über den Parameternamen liest.
    """
    role = role_for_token(fa_session)
    if not role:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt oder ungültiges Token.")
    return role


def require_host(role: str = Depends(require_auth)) -> str:
    """Verlangt die Host-Rolle (Admin-Aktionen); sonst 403."""
    if role != "host":
        raise HTTPException(status_code=403, detail="Diese Aktion ist nur für den Host.")
    return role
