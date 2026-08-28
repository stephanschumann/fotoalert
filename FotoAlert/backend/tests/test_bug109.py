"""BUG-109: "Warum Rote Wolken?"-Erklaerungstext auf der Event-Detail-Ansicht zeigt den
Wolkenwert vom Fotografen-Standort (o.weather_details.cloud_cover_high_pct/low_pct)
statt vom 100-km-Projektionspunkt in Sonnenrichtung (o.ch_red_clouds_dir/cl_red_clouds_dir),
der tatsaechlich ueber should_generate_red_clouds_event() (backend/calculations/weather.py)
entscheidet, ob die "Rote Wolken"-Chance ueberhaupt erzeugt wird.

Betroffene Datei: web/index.html, isRedClouds-Block (Detail.open()-Erklaerungssektion
"Warum Rote Wolken?", Zeilen ~4858-4902 zum Zeitpunkt der Analyse 2026-08-25).

Statischer Text-/Source-Check auf web/index.html (kein Browser, kein laufender Server
noetig) -- exakt dasselbe Vorgehen wie test_bug-87.py. Bewusst NICHT als Playwright-
Browser-Test (frontend-Marker) umgesetzt, weil der eigentliche Fix eine reine
Feldnamen-Korrektur ist (welches JS-Property gelesen wird), keine neue Laufzeit-Logik --
ein Source-Assert deckt das direkt und ohne Server-Abhaengigkeit ab.

Cross-Ticket-Abhaengigkeit (Schritt 3, Pflicht-Check, analog BUG-107/US-38-Retro):
o.ch_red_clouds_dir/o.cl_red_clouds_dir existieren als Backend-Felder AUSSCHLIESSLICH im
noch nicht gemergten BUG-108-Worktree (_worktrees/BUG-108/backend/main.py,
_apply_weather_to_event()) -- im aktuell gepushten/Hauptordner-main.py (Stand 2026-08-25,
grep-verifiziert: 0 Treffer fuer "ch_red_clouds_dir") existieren sie NICHT. Dieser Test
selbst hat KEINE Python-Abhaengigkeit zu backend/main.py (reiner web/index.html-Source-
Check) und ist deshalb unabhaengig vom BUG-108-Mergestand rot/gruen zu bekommen. Die
FUNKTIONALE Wirkung des Fixes (tatsaechlich befuellte, korrekte Zahlen im Browser) bleibt
trotzdem an BUG-108 gebunden: manuelle/Live-Verifikation dieses Tickets darf erst
erfolgen, wenn BUG-108s Backend-Aenderung live ist -- siehe BACKLOG.md BUG-109 Testplan.

AKs siehe BACKLOG.md BUG-109 Implementation Spec.

TASK-96-Hinweis: Diese Datei loest Pfade relativ zum Repo-Root ausserhalb von backend/
auf (web/) und bricht deshalb bei einem Checkout, der nur backend/ enthaelt. Deshalb
zusaetzlich mit `requires_full_checkout` markiert (siehe backend/tests/README.md).
Bewusst NICHT im BUG-108-Worktree abgelegt (_worktrees/BUG-108/backend/tests/), weil
der dortige Checkout ausschliesslich backend/ enthaelt (kein web/-Ordner) -- der
Standard-Pfad-Trick `Path(__file__).parent.parent.parent / "web" / "index.html"`
(wie in test_bug-87.py) wuerde dort ins Leere laufen. web/index.html ist ohnehin kein
Bestandteil des BUG-108-Worktrees (git worktree isoliert dort nur backend/) -- die
Aenderung selbst kann und sollte deshalb unabhaengig vom Worktree im Hauptordner
gemacht werden (siehe BACKLOG.md BUG-109, Implementierungsoptionen/Empfehlung).
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


def _extract_block(source, start_marker, end_marker):
    """Extrahiert den Quelltext zwischen (inkl.) start_marker und dem naechsten
    Auftreten von end_marker danach. Bricht den Test kontrolliert ab (assert),
    wenn einer der Marker nicht (mehr) gefunden wird -- typischerweise weil sich
    die Struktur des Blocks veraendert hat und die Extraktion selbst angepasst
    werden muss, statt einen falschen Treffer stillschweigend zu akzeptieren."""
    start = source.find(start_marker)
    assert start != -1, f"Marker nicht gefunden: {start_marker!r}"
    end = source.find(end_marker, start)
    assert end != -1, f"End-Marker nicht gefunden nach {start_marker!r}: {end_marker!r}"
    return source[start:end]


def _red_clouds_block(source):
    return _extract_block(source, "if (isRedClouds) {", "\n        return '';")


def _red_sky_block(source):
    return _extract_block(source, "if (isRedSky) {", "\n        if (isRedClouds) {")


def _golden_clouds_block(source):
    return _extract_block(source, "if (isGoldenClouds) {", "\n        if (isRedSky) {")


def _wetter_section_block(source):
    # "Wetter zum Shoot-Zeitpunkt"-Sektion (allgemeines Wetter, bleibt laut BUG-108
    # Rule 3 unveraendert am Fotografen-Standort verankert) -- unabhaengiger Block,
    # deutlich VOR der "Warum ...?"-Erklaerungssektion im Markup.
    return _extract_block(
        source,
        "const wd = o.weather_details;",
        "const isGoldenClouds = ",
    )


# --- AK1: "Warum Rote Wolken?" liest ch/cl vom Projektionspunkt, nicht vom Standort ---

def test_ak1_red_clouds_block_reads_ch_from_projection_point_field():
    block = _red_clouds_block(_read_index_html())
    assert "o.ch_red_clouds_dir" in block, (
        "isRedClouds-Block liest 'ch' nicht (mehr) aus o.ch_red_clouds_dir "
        "(dem 100-km-Projektionspunkt in Sonnenrichtung, der tatsaechlich ueber "
        "should_generate_red_clouds_event() entscheidet) -- Fix (noch) nicht vorhanden."
    )


def test_ak1_red_clouds_block_reads_cl_from_projection_point_field():
    block = _red_clouds_block(_read_index_html())
    assert "o.cl_red_clouds_dir" in block, (
        "isRedClouds-Block liest 'cl' nicht (mehr) aus o.cl_red_clouds_dir "
        "(Projektionspunkt) -- Fix (noch) nicht vorhanden."
    )


# --- AK2 (Negativ-/Polaritaets-Gegenstueck zu AK1): der alte, falsche Wert darf im
#     Warum-Block nicht mehr als Quelle fuer ch/cl auftauchen ---

def test_ak2_red_clouds_block_no_longer_reads_local_weather_details_for_ch_cl():
    block = _red_clouds_block(_read_index_html())
    assert "wd.cloud_cover_high_pct" not in block, (
        "isRedClouds-Block liest 'ch' weiterhin aus wd.cloud_cover_high_pct "
        "(Fotografen-Standort) -- genau das ist der BUG-109-Kernbefund, noch nicht behoben."
    )
    assert "wd.cloud_cover_low_pct" not in block, (
        "isRedClouds-Block liest 'cl' weiterhin aus wd.cloud_cover_low_pct "
        "(Fotografen-Standort) -- genau das ist der BUG-109-Kernbefund, noch nicht behoben."
    )


# --- AK3 (Regression/Abwaertskompatibilitaet): die allgemeine "Wetter zum
#     Shoot-Zeitpunkt"-Sektion bleibt unveraendert am eigenen Standort verankert ---

def test_ak3_general_weather_section_still_shows_local_cloud_values():
    block = _wetter_section_block(_read_index_html())
    assert "wd.cloud_cover_high_pct" in block, (
        "Die allgemeine Wetter-Sektion zeigt 'Hohe Wolken' nicht mehr aus "
        "wd.cloud_cover_high_pct (Fotografen-Standort) -- BUG-109 darf diese Sektion "
        "nicht veraendern (BUG-108 Rule 3, unveraendert uebernommen)."
    )
    assert "wd.cloud_cover_low_pct" in block, (
        "Die allgemeine Wetter-Sektion zeigt 'Tiefe Wolken' nicht mehr aus "
        "wd.cloud_cover_low_pct (Fotografen-Standort) -- BUG-109 darf diese Sektion "
        "nicht veraendern (BUG-108 Rule 3, unveraendert uebernommen)."
    )


# --- AK4 (Regression/Scope-Abgrenzung): "Warum Goldene Wolken?" und "Warum
#     Himmelsroete?" bleiben durch diesen Fix unveraendert (nur der RED_CLOUDS-Block
#     wird angefasst; Himmelsroete hat denselben Bugmuster-Verdacht, ist aber laut
#     BACKLOG.md BUG-109 bewusst NICHT Teil dieses Tickets -- eigenes Ticket empfohlen) ---

def test_ak4_himmelsroete_block_unchanged_by_this_ticket():
    block = _red_sky_block(_read_index_html())
    assert "wd.cloud_cover_low_pct" in block and "wd.cloud_cover_mid_pct" in block, (
        "Der isRedSky-Block wurde veraendert (liest cl/cm nicht mehr aus "
        "wd.cloud_cover_low_pct/mid_pct). BUG-109 deckt NUR den RED_CLOUDS-Block ab "
        "-- eine Aenderung hier waere Scope-Creep ueber dieses Ticket hinaus (siehe "
        "BACKLOG.md BUG-109, Fundstellen-Sweep: derselbe Bugmuster-Verdacht besteht "
        "fuer Himmelsroete, ist aber als eigenes, separates Ticket empfohlen)."
    )


def test_ak4_goldene_wolken_block_unchanged_by_this_ticket():
    block = _golden_clouds_block(_read_index_html())
    assert "dirRow + motifRow + diffRow" in block, (
        "Der isGoldenClouds-Block wurde unerwartet veraendert -- BUG-109 betrifft "
        "ausschliesslich den RED_CLOUDS-Block."
    )


# --- AK6 (Fehlerfall/Robustheit): die bestehenden Null-Guards fuer die chRow/clRow-
#     Anzeige bleiben erhalten -- fehlen die Projektionspunkt-Felder (z.B. weil noch
#     gegen den Hauptordner-Server vor BUG-108 getestet wird), verschwinden nur die
#     Zeilen, es gibt keinen Absturz ---

def test_ak6_null_guards_for_ch_and_cl_rows_preserved():
    block = _red_clouds_block(_read_index_html())
    assert re.search(r"const chRow = \(ch != null\)", block), (
        "Der (ch != null)-Guard vor chRow fehlt -- ohne diesen Guard wuerde eine "
        "fehlende Projektionspunkt-Antwort (z.B. Fetch fehlgeschlagen, oder Test "
        "gegen den noch nicht auf BUG-108 aktualisierten Hauptordner-Server) zu "
        "'undefined %'-Text statt einer sauber ausgeblendeten Zeile fuehren."
    )
    assert re.search(r"const clRow = \(cl != null\)", block), (
        "Der (cl != null)-Guard vor clRow fehlt (siehe chRow-Test)."
    )


if __name__ == "__main__":
    src = _read_index_html()
    print("--- isRedClouds-Block (aktueller Stand) ---")
    print(_red_clouds_block(src))
