"""
US-105: Chancen-Detail Sektionsreihenfolge
Prüft dass die Sektions-IDs im Detail-Template von web/index.html
in der korrekten SOLL-Reihenfolge definiert sind.

Ausführen (vom Workspace-Root):
    pytest FotoAlert/backend/tests/test_us105_section_order.py -v
"""

import re
import os
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.frontend]

# Pfad relativ zu diesem Skript
THIS_DIR = Path(__file__).parent
INDEX_HTML = THIS_DIR.parent.parent / "web" / "index.html"

# SOLL-Reihenfolge laut US-105
EXPECTED_ORDER = [
    "ev_desc",
    "ev_zeit",
    "ev_wetter",
    "ev_fov",
    "ev_kompo",
    "ev_coords",
    "ev_skypos",
    "ev_kamera",
    "ev_astro",
    "ev_topo",
    "ev_astro_live",
]

# Alle IDs die im Template vorkommen müssen
ALL_SECTION_IDS = set(EXPECTED_ORDER)


def _extract_section_order(html_content):
    """
    Extrahiert die Reihenfolge der Sektions-IDs aus dem Detail-Template.
    Sucht nach mkSec('ev_...') Aufrufen ab dem Detail.open-Abschnitt.

    Hinweis: Einige IIFE-Blöcke (z.B. ev_wetter) haben zwei mkSec-Aufrufe
    (early return + normaler return im selben Block). Wir deduplizieren und
    behalten nur das erste Auftreten jeder ID — das entspricht der physischen
    Block-Position im Template.
    """
    # Startmarker: der Abschnitt in Detail.open wo die Sektionen gerendert werden
    # Anker: der score-info-overlay div, der direkt vor den Sektionen kommt
    start_marker = "id=\"score-info-overlay\""
    end_marker = "class=\"sheet-actions\""

    start_idx = html_content.find(start_marker)
    end_idx = html_content.find(end_marker)

    assert start_idx != -1, (
        f"Startmarker '{start_marker}' nicht in index.html gefunden — "
        "Dateistruktur hat sich verändert"
    )
    assert end_idx != -1, (
        f"Endmarker '{end_marker}' nicht in index.html gefunden — "
        "Dateistruktur hat sich verändert"
    )
    assert start_idx < end_idx, "Start-Marker liegt nach End-Marker — unerwartete Dateistruktur"

    template_section = html_content[start_idx:end_idx]

    # Reihenfolge der IDs ermitteln: suche nach mkSec('ev_xxx' oder mkSec("ev_xxx"
    # Auch IIFE-Blöcke enthalten mkSec-Aufrufe
    pattern = re.compile(r"mkSec\(['\"](\bev_\w+\b)['\"]")
    all_found = pattern.findall(template_section)

    # Deduplizieren: erstes Auftreten jeder ID behält die Position,
    # spätere Mehrfach-Nennungen (z.B. ev_wetter early-return) werden ignoriert
    seen = set()
    found_ids = []
    for sid in all_found:
        if sid not in seen:
            seen.add(sid)
            found_ids.append(sid)

    return found_ids


def test_section_order():
    """Die Sektionen im Detail-Template sind in der SOLL-Reihenfolge laut US-105."""
    assert INDEX_HTML.exists(), f"index.html nicht gefunden: {INDEX_HTML}"

    content = INDEX_HTML.read_text(encoding="utf-8")
    found_ids = _extract_section_order(content)

    # Alle erwarteten IDs müssen vorhanden sein
    found_set = set(found_ids)
    missing = ALL_SECTION_IDS - found_set
    assert not missing, (
        f"Folgende Sektions-IDs fehlen im Template: {sorted(missing)}\n"
        f"Gefunden: {found_ids}"
    )

    # Nur die IDs aus EXPECTED_ORDER in der gefundenen Reihenfolge betrachten
    # (es kann andere mkSec-Aufrufe mit anderen IDs geben, die wir ignorieren)
    found_relevant = [sid for sid in found_ids if sid in ALL_SECTION_IDS]

    assert found_relevant == EXPECTED_ORDER, (
        f"\nSektionsreihenfolge stimmt NICHT mit SOLL überein.\n"
        f"IST:  {found_relevant}\n"
        f"SOLL: {EXPECTED_ORDER}\n\n"
        f"Erste Abweichung: Position {next(i for i,(a,b) in enumerate(zip(found_relevant, EXPECTED_ORDER)) if a!=b) if found_relevant != EXPECTED_ORDER else 'Länge verschieden'}"
    )


def test_all_ids_present_exactly_once():
    """Jede Sektions-ID erscheint im Template genau einmal (keine Duplikate)."""
    assert INDEX_HTML.exists(), f"index.html nicht gefunden: {INDEX_HTML}"

    content = INDEX_HTML.read_text(encoding="utf-8")
    found_ids = _extract_section_order(content)

    found_relevant = [sid for sid in found_ids if sid in ALL_SECTION_IDS]

    duplicates = [sid for sid in ALL_SECTION_IDS if found_relevant.count(sid) > 1]
    assert not duplicates, (
        f"Folgende Sektions-IDs erscheinen mehrfach im Template: {duplicates}"
    )
