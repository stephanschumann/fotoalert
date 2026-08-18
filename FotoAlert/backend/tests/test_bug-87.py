"""BUG-87: Badge-Wortlaut "Geprüft"/"Nicht geprüft" wurde für zwei unabhängige
Status-Konzepte wiederverwendet (Verifikation vs. Sichtachsen-Datenverfuegbarkeit).

Fix: der Anzeige-Text fuer den Sichtachsen-Status `nicht_geprueft` wurde an den vier
betroffenen Frontend-Fundstellen von "Nicht geprueft" auf "Daten fehlen" geaendert:
  1. SIGHTLINE_LABELS.nicht_geprueft (Single-Source-Konstante)
  2. FilterSheet sightlineChips-Array (umgestellt von Hardcode-Literal auf Referenz
     auf SIGHTLINE_LABELS.nicht_geprueft - behebt zugleich eine DRY-Verletzung)
  3. ElementInfo._sightlineStatus-Popup-Text
  4. ElementInfo-Filterbeschreibung "sichtachsenstatus"

Der Verifikations-Wortlaut ("Geprueft"/"Nicht geprueft" fuer die Vor-Ort-Verifikation
durch den Host) bleibt an allen Stellen unveraendert (FilterSheet verChips-Array,
ElementInfo._verification-Popup, Filterbeschreibung "verifikationsstatus"). Der interne
Status-Wert 'nicht_geprueft' (Datenmodell, Filter-Logik, BUG-88-Eskalationsvergleich in
sightlineTagHtml()) bleibt ebenfalls unveraendert - nur der sichtbare Text aendert sich.

Statischer Text-Check auf web/index.html (kein Browser, kein laufender Server noetig).

AKs siehe BACKLOG.md BUG-87 Implementation Spec.

TASK-96-Hinweis: Diese Datei loest Pfade relativ zum Repo-Root ausserhalb von backend/
auf (web/) und bricht deshalb bei einem Checkout, der nur backend/ enthaelt. Deshalb
zusaetzlich mit `requires_full_checkout` markiert (siehe backend/tests/README.md).
"""
import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

_ROOT = Path(__file__).parent.parent.parent
_INDEX_HTML = _ROOT / "web" / "index.html"


def _read_index_html():
    assert _INDEX_HTML.exists(), f"{_INDEX_HTML} nicht gefunden"
    return _INDEX_HTML.read_text(encoding="utf-8")


def _find_line_containing(source, needle):
    """Gibt die erste Zeile aus source zurueck, die needle enthaelt, oder None."""
    for line in source.splitlines():
        if needle in line:
            return line
    return None


def _find_lines_containing(source, needle):
    """Gibt alle Zeilen aus source zurueck, die needle enthalten."""
    return [line for line in source.splitlines() if needle in line]


# --- a) SIGHTLINE_LABELS enthaelt 'Daten fehlen' statt 'Nicht geprueft' ---

def test_sightline_labels_uses_daten_fehlen():
    source = _read_index_html()
    line = _find_line_containing(source, "nicht_geprueft: 'Daten fehlen',")
    assert line is not None, (
        "SIGHTLINE_LABELS.nicht_geprueft zeigt nicht 'Daten fehlen' "
        "(erwartete Zeile 'nicht_geprueft: 'Daten fehlen',' nicht gefunden)"
    )


def test_sightline_labels_block_no_longer_says_nicht_geprueft():
    """Der SIGHTLINE_LABELS-Objektliteral-Block selbst darf den alten Text nicht
    mehr enthalten (enger gefasst als der globale Regressionsschutz unten, damit
    ein Fehlschlag hier gezielt auf diese Konstante zeigt)."""
    source = _read_index_html()
    match = re.search(r"const SIGHTLINE_LABELS = \{(.*?)\};", source, re.S)
    assert match is not None, "SIGHTLINE_LABELS-Objektliteral nicht gefunden"
    block = match.group(1)
    assert "Nicht geprüft" not in block, (
        f"SIGHTLINE_LABELS enthaelt noch den alten Text 'Nicht geprüft': {block!r}"
    )
    assert "Daten fehlen" in block, "SIGHTLINE_LABELS enthaelt nicht 'Daten fehlen'"


# --- b) FilterSheet sightlineChips referenziert SIGHTLINE_LABELS.nicht_geprueft ---

def test_filtersheet_sightline_chip_references_sightline_labels_constant():
    source = _read_index_html()
    line = _find_line_containing(source, "['nicht_geprueft',")
    assert line is not None, "sightlineChips-Zeile fuer 'nicht_geprueft' nicht gefunden"
    assert "SIGHTLINE_LABELS.nicht_geprueft" in line, (
        f"FilterSheet sightlineChips-Chip fuer 'nicht_geprueft' referenziert nicht "
        f"SIGHTLINE_LABELS.nicht_geprueft (noch Hardcode-Literal?): {line!r}"
    )
    assert "'Nicht geprüft'" not in line, (
        f"FilterSheet sightlineChips-Chip enthaelt noch das alte Hardcode-Literal: {line!r}"
    )


# --- c) Popup-Text und Filterbeschreibung enthalten 'Daten fehlen' ---

def test_elementinfo_sightlinestatus_popup_uses_daten_fehlen():
    source = _read_index_html()
    match = re.search(
        r"_sightlineStatus:\s*\{.*?\n\s*\},",
        source,
        re.S,
    )
    assert match is not None, "_sightlineStatus-Block in ElementInfo nicht gefunden"
    block = match.group(0)
    assert "<b>Daten fehlen:</b>" in block, (
        f"_sightlineStatus-Popup nennt nicht mehr '<b>Daten fehlen:</b>': {block!r}"
    )
    assert "Nicht geprüft" not in block, (
        f"_sightlineStatus-Popup enthaelt noch den alten Text 'Nicht geprüft': {block!r}"
    )


def test_elementinfo_sichtachsenstatus_filterdescription_uses_daten_fehlen():
    source = _read_index_html()
    match = re.search(
        r"sichtachsenstatus:\s*\{.*?\n\s*\},",
        source,
        re.S,
    )
    assert match is not None, "sichtachsenstatus-Filterbeschreibung nicht gefunden"
    block = match.group(0)
    assert "Frei/Teilweise verdeckt/Blockiert/Daten fehlen." in block, (
        f"sichtachsenstatus-Filterbeschreibung nennt nicht 'Daten fehlen': {block!r}"
    )
    assert "Nicht geprüft" not in block, (
        f"sichtachsenstatus-Filterbeschreibung enthaelt noch den alten Text: {block!r}"
    )


# --- d) Regressionsschutz: Verifikations-Fundstellen bleiben unveraendert ---

def test_verification_filter_chip_still_says_nicht_geprueft():
    source = _read_index_html()
    line = _find_line_containing(source, "['unverified',")
    assert line is not None, "verChips-Zeile fuer 'unverified' nicht gefunden"
    assert "'Nicht geprüft'" in line, (
        f"Verifikations-FilterSheet-Chip 'unverified' wurde faelschlich mitgeaendert "
        f"(soll unveraendert 'Nicht geprüft' bleiben): {line!r}"
    )


def test_elementinfo_verification_popup_still_says_nicht_geprueft():
    source = _read_index_html()
    match = re.search(
        r"_verification:\s*\{.*?\n\s*\},",
        source,
        re.S,
    )
    assert match is not None, "_verification-Block in ElementInfo nicht gefunden"
    block = match.group(0)
    assert "<b>Nicht geprüft:</b>" in block, (
        f"_verification-Popup wurde faelschlich mitgeaendert "
        f"(soll unveraendert '<b>Nicht geprüft:</b>' bleiben): {block!r}"
    )


def test_verifikationsstatus_filterdescription_still_mentions_nicht_geprueft():
    source = _read_index_html()
    match = re.search(
        r"verifikationsstatus:\s*\{.*?\n\s*\},",
        source,
        re.S,
    )
    assert match is not None, "verifikationsstatus-Filterbeschreibung nicht gefunden"
    block = match.group(0)
    assert "Geprüft/Nicht geprüft/Probleme" in block, (
        f"verifikationsstatus-Filterbeschreibung wurde faelschlich mitgeaendert: {block!r}"
    )


def test_exactly_two_nicht_geprueft_occurrences_remain():
    """Globaler Regressionsschutz aus dem Fundstellen-Sweep: nach dem Fix duerfen nur
    noch die beiden bewusst unveraenderten Verifikations-Fundstellen den Text
    'Nicht geprüft' enthalten (verChips-Array, _verification-Popup) - alle vier
    Sichtachsen-Fundstellen sind auf 'Daten fehlen' umgestellt. Die dritte,
    unveraenderte Erwaehnung in der Aufzaehlung "Geprüft/Nicht geprüft/Probleme"
    (verifikationsstatus-Filterbeschreibung) zaehlt als dritter erlaubter Treffer."""
    source = _read_index_html()
    lines = _find_lines_containing(source, "Nicht geprüft")
    assert len(lines) == 3, (
        f"Erwartet genau 3 verbleibende Vorkommen von 'Nicht geprüft' "
        f"(2x Verifikations-Chip/Popup + 1x Verifikations-Filterbeschreibungssatz), "
        f"gefunden: {len(lines)}\n" + "\n".join(lines)
    )


# --- e) Regressionsschutz: interner String-Key 'nicht_geprueft' bleibt im Code unveraendert ---

def test_sightline_tag_html_still_compares_against_internal_key():
    """sightlineTagHtml() vergleicht weiterhin gegen den internen String-Key
    'nicht_geprueft' (nicht gegen den Anzeige-Text) - insbesondere die
    BUG-88-Eskalationslogik (escalate=true) haengt an diesem Key."""
    source = _read_index_html()
    assert "s === 'nicht_geprueft'" in source, (
        "Interner Vergleich s === 'nicht_geprueft' (BUG-88-Eskalationslogik in "
        "sightlineTagHtml()) nicht mehr gefunden - wurde der interne Key versehentlich "
        "mitgeaendert?"
    )
    assert "SIGHTLINE_LABELS[s] || SIGHTLINE_LABELS.nicht_geprueft" in source, (
        "Fallback-Lookup SIGHTLINE_LABELS[s] || SIGHTLINE_LABELS.nicht_geprueft in "
        "sightlineTagHtml() nicht mehr gefunden"
    )


def test_sightline_status_fallback_key_unchanged():
    """Der Fallback 'status || 'nicht_geprueft'' (fehlender sightline_status wird wie
    nicht_geprueft behandelt) bleibt als interner Key bestehen - betrifft u.a.
    oppCard(), Detail.open() und LocationDetail."""
    source = _read_index_html()
    fallback_occurrences = source.count("|| 'nicht_geprueft'")
    assert fallback_occurrences >= 3, (
        f"Erwartet mindestens 3 Fallback-Stellen '|| 'nicht_geprueft'' im Code, "
        f"gefunden: {fallback_occurrences}"
    )
