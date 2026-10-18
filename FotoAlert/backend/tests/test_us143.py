"""US-143 (Option B, Weg-Gate Stephan 2026-10-18) -- Willkommens-Slides (Onboarding) ganz entfernen.

Test-first geschrieben VOR der Aenderung an web/index.html (Rot-Nachweis im Ticket).
Reine Quelltext-Pruefungen (kein Server, kein Browser; Marker offline). Der echte Browser-Durchlauf
(frisches Geraet, kein Slide nach dem Login, Glossar ohne Eintrag, Feed<->Kalender x3) wurde separat
per Chrome-Integration geprueft.

  A1  kein automatischer Start nach dem Login (kein initialShowIfNeeded, kein Aufruf im Boot)
  A2  Glossar hat keinen Eintrag "Onboarding erneut ansehen" und keine Sonderbehandlung dafuer
  A3  Overlay-Element, Stil und Code (Onboarding-Objekt, Slides, onb-Klassen) sind weg
  A4  Merker fa_onboarding_seen wird weder gelesen noch geschrieben
  A5  keine Aufrufer-Reste (Onboarding.* irgendwo)
  A6  Texte der Slides sind weg (Titel der 4 Slides)
  A7  Hilfetext enthaelt keinen Verweis mehr auf "Onboarding"
  S1  SCHUTZ: Host-Dialog "Neuer Ort in ausgeschaltetem Gebiet" und Balken "Host muss freischalten" bleiben
  S2  SCHUTZ: Glossar bleibt benutzbar (Glossary-Objekt, Scores/Kernbegriffe-Eintraege, "?"-Knopf)
  S3  SCHUTZ: US-142-Stand unberuehrt (Umschaltleiste mit genau zwei Knoepfen, kein Scout)
  J1  Skripte in web/index.html sind syntaktisch gueltig (node --check), falls node vorhanden

Python 3.9-kompatibel.
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

ROOT = Path(__file__).resolve().parent.parent.parent
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")


def test_a1_kein_automatischer_start_nach_dem_login():
    """US-143 AK1/AK2/AK4: App-Start stoesst kein Onboarding mehr an."""
    assert "initialShowIfNeeded" not in HTML


def test_a2_glossar_ohne_onboarding_eintrag():
    """US-143 AK5: Glossar enthaelt keinen Eintrag zum erneuten Ansehen."""
    assert "Onboarding erneut ansehen" not in HTML
    assert "special: 'onboarding'" not in HTML
    assert "e.special" not in HTML
    assert "section: 'Einführung'" not in HTML


def test_a3_overlay_stil_und_code_entfernt():
    """US-143 AK6: Overlay, Stil und Code der Slides sind vollstaendig weg."""
    assert 'id="onboarding-overlay"' not in HTML
    assert 'id="onboarding-screen"' not in HTML
    assert "#onboarding-overlay" not in HTML
    assert "const Onboarding" not in HTML
    assert not re.search(r"\.onb-[a-z]+", HTML)
    assert "onb-" not in HTML


def test_a4_merker_wird_nicht_mehr_gelesen_oder_geschrieben():
    """US-143 AK7: Der alte Merker im Geraetespeicher wird nicht mehr angefasst."""
    assert "fa_onboarding_seen" not in HTML


def test_a5_keine_aufrufer_reste():
    """US-143 AK8: Kein Aufruf Onboarding.xyz mehr (auch nicht in HTML-Attributen)."""
    assert not re.search(r"Onboarding\s*\.", HTML)
    assert "Onboarding" not in HTML


def test_a6_slide_texte_entfernt():
    """US-143 AK9: Die Slide-Texte sind weg."""
    for s in ("Willkommen bei FotoAlert", "Scores auf einen Blick",
              "Schwierigkeitsgrade &amp; Event-Typen", "Hilfe ist immer griffbereit"):
        assert s not in HTML, s


def test_a7_kein_verweis_auf_einfuehrung_im_ui():
    """US-143 AK6: Auch der Kommentar-/Textrest 'Einfuehrungs-Slides' ist weg."""
    assert "Einführungs-Slides" not in HTML
    assert "Willkommens-Slides" not in HTML


def test_s1_schutz_host_dialog_und_balken_bleiben():
    """US-143 AK10 (Abgrenzung zu US-141)."""
    for s in ("checkUndecided", "Neuer Ort in ausgeschaltetem Gebiet", 'id="gb-notice"',
              "Host muss freischalten", "Gebiete.afterLoad()"):
        assert s in HTML, s


def test_s2_schutz_glossar_bleibt_benutzbar():
    """US-143 AK5 (Gegenprobe): Glossar selbst und seine uebrigen Eintraege bleiben."""
    assert "const Glossary" in HTML
    assert 'id="help-btn"' in HTML
    for s in ("Gesamt-Score", "Astronomie-Score", "Schwierigkeitsgrade", "Verifikationsstatus",
              "Wie unterscheiden sich Feed und Kalender?", "Wie funktionieren die Filter?"):
        assert s in HTML, s
    assert "glossary-item-" in HTML and "Glossary.toggle(" in HTML


def test_s3_schutz_us142_stand_unberuehrt():
    """US-143 AK11 (Release-Bundle mit US-142): zwei Knoepfe, kein Scout."""
    assert 'id="fmb-scout"' not in HTML
    knoepfe = re.findall(r'<button[^>]*class="fmb-btn[^"]*"', HTML)
    assert len(knoepfe) == 2, knoepfe
    rest = re.sub(r"locationscout", "", HTML, flags=re.I)
    assert not re.search(r"scout", rest, flags=re.I)


def test_j1_skripte_syntaktisch_gueltig():
    node = shutil.which("node")
    if not node:
        pytest.skip("node nicht vorhanden")
    skripte = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", HTML, flags=re.S)
    assert skripte
    for i, code in enumerate(skripte):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ("s%d.js" % i)
            p.write_text(code, encoding="utf-8")
            r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
            assert r.returncode == 0, r.stderr[:500]
