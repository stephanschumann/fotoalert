"""
Tests für TASK-46: Automatische Standortbeschreibungen via LLM.

Alle Tests mocken die Mistral-API — kein echter HTTP-Call.
Store wird als einfaches MagicMock simuliert.
"""

from __future__ import annotations

import os
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from data.qa_description import (
    _build_prompt,
    generate_location_description,
    update_location_description,
)


# ---------------------------------------------------------------------------
# Hilfsfunktionen für Store-Mocks
# ---------------------------------------------------------------------------

def _make_store(
    description_lock: int = 0,
    existing_description: Optional[str] = None,
) -> MagicMock:
    """Erzeugt einen minimalen Store-Mock mit konfigurierbarem QA-State."""
    store = MagicMock()
    store.get_qa_state.return_value = {"description_lock": description_lock}
    store.get_qa_values.return_value = {"description": existing_description}
    store.set_qa_values.return_value = None
    return store


# ---------------------------------------------------------------------------
# Tests: _build_prompt
# ---------------------------------------------------------------------------

def test_build_prompt_contains_facts():
    """Prompt muss alle übergebenen Fakten enthalten."""
    result = _build_prompt(
        loc_name="Teufelsberg",
        subject_name="Berliner Dom",
        category="SKYLINE",
        observer_lat=52.4973,
        observer_lon=13.2398,
    )
    assert "Teufelsberg" in result
    assert "Berliner Dom" in result
    assert "SKYLINE" in result


def test_build_prompt_without_coords():
    """Ohne Koordinaten darf der Prompt trotzdem gebaut werden."""
    result = _build_prompt(
        loc_name="Teufelsberg",
        subject_name="Berliner Dom",
        category="SKYLINE",
        observer_lat=None,
        observer_lon=None,
    )
    assert "Teufelsberg" in result
    assert "Berliner Dom" in result


# ---------------------------------------------------------------------------
# Tests: update_location_description
# ---------------------------------------------------------------------------

def test_description_written_when_empty():
    """Leerer Spot ohne Lock: Beschreibung wird generiert und gespeichert."""
    store = _make_store(description_lock=0, existing_description=None)
    with patch(
        "data.qa_description._call_mistral_api",
        return_value="Ein toller Spot.",
    ):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key"}):
            result = update_location_description(
                store, "loc-1", "Teufelsberg", "Berliner Dom", "SKYLINE",
                52.4973, 13.2398,
            )
    assert result == "Ein toller Spot."
    store.set_qa_values.assert_called_once_with("loc-1", description="Ein toller Spot.")


def test_description_lock_respected():
    """Lock gesetzt: weder API aufrufen noch schreiben."""
    store = _make_store(description_lock=1)
    with patch(
        "data.qa_description._call_mistral_api",
        return_value="Würde nicht aufgerufen.",
    ) as mock_api:
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key"}):
            result = update_location_description(
                store, "loc-2", "Spot", "Motiv", "BRIDGE",
                52.0, 13.0,
            )
    assert result is None
    mock_api.assert_not_called()
    store.set_qa_values.assert_not_called()


def test_existing_description_not_overwritten():
    """Vorhandene Beschreibung darf nicht überschrieben werden."""
    store = _make_store(description_lock=0, existing_description="Beste Aussicht")
    with patch(
        "data.qa_description._call_mistral_api",
        return_value="Neuer Text.",
    ) as mock_api:
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key"}):
            result = update_location_description(
                store, "loc-3", "Spot", "Motiv", "URBAN",
                52.0, 13.0,
            )
    assert result is None
    mock_api.assert_not_called()
    store.set_qa_values.assert_not_called()


def test_empty_api_response_not_written():
    """Leere API-Antwort: nichts speichern, None zurückgeben."""
    store = _make_store(description_lock=0, existing_description=None)
    with patch(
        "data.qa_description._call_mistral_api",
        return_value="",
    ):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key"}):
            result = update_location_description(
                store, "loc-4", "Spot", "Motiv", "NATURE",
                52.0, 13.0,
            )
    assert result is None
    store.set_qa_values.assert_not_called()


def test_whitespace_only_response_not_written():
    """Nur-Whitespace API-Antwort: nichts speichern."""
    store = _make_store(description_lock=0, existing_description=None)
    with patch(
        "data.qa_description._call_mistral_api",
        return_value="   \n  ",
    ):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key"}):
            result = update_location_description(
                store, "loc-5", "Spot", "Motiv", "WATER",
                52.0, 13.0,
            )
    assert result is None
    store.set_qa_values.assert_not_called()


def test_api_error_silent():
    """Netzwerkfehler darf keine Exception werfen; None wird zurückgegeben."""
    import httpx

    store = _make_store(description_lock=0, existing_description=None)
    with patch(
        "data.qa_description._call_mistral_api",
        side_effect=httpx.ConnectError("Verbindung verweigert"),
    ):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key"}):
            result = update_location_description(
                store, "loc-6", "Spot", "Motiv", "SKYLINE",
                52.0, 13.0,
            )
    # Kein Exception durch; Rückgabe None
    assert result is None


def test_missing_api_key_skips_silently():
    """Fehlt MISTRAL_API_KEY: None zurück, kein HTTP-Call."""
    store = _make_store(description_lock=0, existing_description=None)
    # Sicherstellen dass der Key nicht gesetzt ist
    env = {k: v for k, v in os.environ.items() if k != "MISTRAL_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        with patch(
            "data.qa_description._call_mistral_api",
        ) as mock_api:
            result = update_location_description(
                store, "loc-7", "Spot", "Motiv", "BRIDGE",
                52.0, 13.0,
            )
    assert result is None
    mock_api.assert_not_called()
    store.set_qa_values.assert_not_called()
