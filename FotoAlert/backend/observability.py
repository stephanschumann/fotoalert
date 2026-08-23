"""
US-38: Fehlerklassifizierer für Hintergrund-Jobs (Observability & Self-Healing).

Ordnet eine rohe Fehlermeldung (aus einem fehlgeschlagenen Job — weather/feed/
calendar/discover/...) anhand einfacher Keyword-Regeln einer festen Fehler-
klasse zu und liefert dazu die betroffenen Dateien + einen Lösungsvorschlag
zum Nachlesen (KEINE automatisch ausgeführte Änderung, Ticket-Kernanforderung).

Python-3.9-kompatibel (Server läuft laut CLAUDE.md §5 weiterhin 3.9-kompatiblen
Code, auch wenn der Produktionsserver selbst inzwischen auf 3.12 läuft) — daher
`Tuple`/`Optional` aus `typing` statt `tuple[...]`/`X | None`.
"""

from typing import Optional, Tuple

# Reihenfolge ist relevant: die erste zutreffende Regel gewinnt.
ERROR_RULES = [
    (("timeout", "timed out"), "Timeout",
     ["backend/calculations/weather.py"], "Timeout bei API-Call — Retry-Logik oder Timeout-Wert erhöhen"),
    (("connectionerror", "connection refused", "name or service not known"), "APIError",
     ["backend/calculations/weather.py"], "API nicht erreichbar — Netzwerk oder API-Status prüfen"),
    (("json", "decode", "corrupt", "invalid"), "DataError",
     ["backend/precompute.py", "backend/main.py"], "Cache-Datei korrupt — Cache löschen und Neuberechnung starten"),
    (("exit 1", "exit 2", "returncode"), "SubprocessError",
     ["backend/precompute.py"], "precompute.py Fehler — stdout-Log prüfen"),
]


def classify_error(msg: str) -> Tuple[str, list, str]:
    """Gibt (error_class, betroffene_files, suggestion) zurück.

    Nicht klassifizierbare Fehler liefern ("Unknown", [], <generischer Hinweis>)
    statt eines geratenen, zu spezifischen Vorschlags (AK: Negativ-Fall).
    """
    lower = (msg or "").lower()
    for keywords, cls, files, suggestion in ERROR_RULES:
        if any(k in lower for k in keywords):
            return cls, files, suggestion
    return "Unknown", [], "Fehler nicht klassifizierbar — bitte Log manuell prüfen"
