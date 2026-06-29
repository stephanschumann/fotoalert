"""
FotoAlert – Auto-Erzeugung von Standortbeschreibungen via LLM (TASK-46)

Erzeugt für Locations ohne kuratierte Beschreibung automatisch einen kurzen
deutschen Text aus den vorhandenen Fakten (Name, Motiv, Kategorie, Koordinaten).

Strategie:
  • Faktenbasierter Prompt → Mistral Chat API per httpx (kein SDK).
  • API-Key aus Umgebungsvariable MISTRAL_API_KEY — wird nie geloggt.
  • Bei fehlendem Key, Netzfehler oder leerem Ergebnis: None zurück, kein Crash.
  • Respektiert description_lock: ist er gesetzt, wird nichts geschrieben.

Python-3.9-kompatibel.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Mistral Chat API Endpunkt (OpenAI-kompatibel)
MISTRAL_API_URL: str = "https://api.mistral.ai/v1/chat/completions"
# Free-Tier-Modell — ausreichend für kurze Texte
MISTRAL_MODEL: str = "mistral-small-latest"
# Maximale Antwort-Tokens (2–3 Sätze brauchen selten mehr als 150)
MISTRAL_MAX_TOKENS: int = 150
# HTTP-Timeout in Sekunden — wie Overpass in qa_azimuth
MISTRAL_TIMEOUT_S: float = 10.0


def _build_prompt(
    loc_name: str,
    subject_name: str,
    category: str,
    observer_lat: Optional[float],
    observer_lon: Optional[float],
) -> str:
    """Baut einen strikten Fakten-Prompt für die Beschreibungs-Generierung.

    Nur die übergebenen Fakten dürfen im Prompt stehen — keine Erfindungen.
    Koordinaten werden nur eingebunden wenn vorhanden.
    """
    coord_info = ""
    if observer_lat is not None and observer_lon is not None:
        coord_info = f" Der Fotografen-Standort liegt bei {observer_lat:.5f}°N, {observer_lon:.5f}°E."

    prompt = (
        "Du bist ein sachkundiger Fotografie-Guide. "
        "Schreibe eine kurze, nüchterne Standortbeschreibung auf Deutsch (maximal 2–3 Sätze). "
        "Benutze NUR die folgenden Fakten — erfinde nichts dazu:\n\n"
        f"- Standortname: {loc_name}\n"
        f"- Motiv: {subject_name}\n"
        f"- Kategorie: {category}\n"
        f"{coord_info}\n\n"
        "Keine Werbung, keine Wertungen, keine Fakten die nicht oben stehen. "
        "Schreibe nur den Beschreibungstext, keine Überschrift."
    )
    return prompt


def _call_mistral_api(
    prompt: str,
    api_key: str,
    timeout_s: float = MISTRAL_TIMEOUT_S,
) -> Optional[str]:
    """Sendet den Prompt an die Mistral Chat API und gibt den Text zurück.

    Gibt None zurück bei:
      - Netzwerkfehler / Timeout
      - HTTP-Fehler (4xx / 5xx)
      - Unerwartetem Response-Format
    Der API-Key wird nie geloggt.
    """
    try:
        import httpx  # lokaler Import wie in qa_azimuth

        headers = {
            "Authorization": "Bearer " + api_key,
            "content-type": "application/json",
        }
        payload = {
            "model": MISTRAL_MODEL,
            "max_tokens": MISTRAL_MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(MISTRAL_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # Antwort-Text aus der OpenAI-kompatiblen Chat-Struktur extrahieren
        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            logger.info("Mistral-API: unerwartetes choices-Format")
            return None
        text = choices[0].get("message", {}).get("content", "")
        return text if text else None

    except Exception as exc:  # noqa: BLE001 — bewusst: jeder Fehler → None
        logger.info("Mistral-API nicht erreichbar: %s", type(exc).__name__)
        return None


def generate_location_description(
    name: str,
    subject: str,
    category: str,
    lat: Optional[float],
    lon: Optional[float],
) -> Optional[str]:
    """Erzeugt eine Beschreibung via Mistral API.

    Liest den API-Key aus der Umgebungsvariable MISTRAL_API_KEY.
    Gibt None zurück wenn kein Key gesetzt, API nicht erreichbar oder
    Antwort leer/nur Whitespace.
    """
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        logger.info("MISTRAL_API_KEY nicht gesetzt — Beschreibungs-Generierung übersprungen")
        return None

    prompt = _build_prompt(name, subject, category, lat, lon)
    text = _call_mistral_api(prompt, api_key)
    if not text or not text.strip():
        return None
    return text.strip()


def update_location_description(
    store,
    location_id: str,
    name: str,
    subject: str,
    category: str,
    lat: Optional[float],
    lon: Optional[float],
) -> Optional[str]:
    """Berechnet eine Beschreibung und schreibt sie in die QA-Werte-Tabelle.

    Respektiert description_lock: ist er gesetzt, wird nichts geschrieben.
    Schreibt auch nichts wenn bereits eine Beschreibung vorhanden ist.

    Rückgabe:
      - str: geschriebene Beschreibung
      - None: nichts geschrieben (Lock gesetzt, bereits vorhanden, API-Fehler,
        leere Antwort). Wirft nie eine Exception.
    """
    try:
        state = store.get_qa_state(location_id)
        if state and state.get("description_lock"):
            logger.info("Beschreibung für %s gesperrt — kein Auto-Update", location_id)
            return None

        # Bereits vorhandene Beschreibung nicht überschreiben
        qa_values = store.get_qa_values(location_id)
        if qa_values and qa_values.get("description"):
            logger.info("Beschreibung für %s bereits vorhanden — übersprungen", location_id)
            return None

        text = generate_location_description(name, subject, category, lat, lon)
        if not text:
            return None

        store.set_qa_values(location_id, description=text)
        logger.info("Beschreibung für %s gesetzt (%d Zeichen)", location_id, len(text))
        return text

    except Exception as exc:  # noqa: BLE001 — kein Exception-Durchreichen
        logger.warning("QA-Beschreibung für %s fehlgeschlagen: %s", location_id, exc)
        return None
