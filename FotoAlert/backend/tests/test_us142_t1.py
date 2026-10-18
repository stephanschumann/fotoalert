"""US-142 Teilschritt 1 (T1 = nur Oberflaeche) -- Scouts aus der App entfernen.

Freigabe Stephan 2026-10-18: Prototyp der Zwei-Knopf-Leiste freigegeben; Test-Stellen fuer T1
freigegeben. Test-first geschrieben VOR der Aenderung an web/index.html (Rot-Nachweis im Ticket).

Reine Quelltext-Pruefungen (kein Server, kein Browser noetig; Marker offline). Der echte
Browser-Durchlauf (zwei Knoepfe, Breiten 390/1280 px, Wechsel Feed<->Kalender x3 ohne
Konsolenfehler) steht in backend/tests/frontend/run_frontend_check.py.

  S1a  kein Scout-Knopf, kein Scout-Container
  S1b  Umschaltleiste hat genau zwei Knoepfe (14-Tage Feed, Jahreskalender)
  S1c  Moduswechsel (Feed.setMode) greift nicht auf Scout zu (Falle: sonst bricht Feed<->Kalender)
  S1d  kein Scout-Objekt/-Filter/-Karte/-Detail-Speichern/-Session-Labels mehr
  S1e  Frontend loest den Scout-Abruf (/discover) nicht mehr aus
  S1f  im Quelltext kommt weder "Scout" noch "Entdecken" vor (ausser "Locationscout" = Ortsherkunft)
  S1g  Hilfetext zu Feed/Kalender ohne Scout-Bezug
  M1   MUSS BLEIBEN: locationscout_url, Mond-/Sonnen-Alignment-Filter
  X1   Server bleibt in T1 unberuehrt: Endpunkt /discover und Ordner discover/ sind noch da
  J1   Skripte in web/index.html sind syntaktisch gueltig (node --check), falls node vorhanden

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
MAIN = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")


def _ohne_ortsherkunft(text):
    """Entfernt die erlaubte Ortsherkunft 'Locationscout' (hat mit der Scout-Funktion nichts zu tun)."""
    return re.sub(r"locationscout", "", text, flags=re.I)


def test_s1a_kein_scout_knopf_und_container():
    assert 'id="fmb-scout"' not in HTML
    assert 'id="scout-content"' not in HTML
    assert "Feed.setMode('scout')" not in HTML


def test_s1b_umschaltleiste_hat_genau_zwei_knoepfe():
    start = HTML.index('class="feed-mode-bar"')
    ende = HTML.index("</div>", start)
    leiste = HTML[start:ende]
    assert len(re.findall(r'class="fmb-btn', leiste)) == 2, leiste
    assert "14-Tage Feed" in leiste and "Jahreskalender" in leiste


def test_s1c_setmode_ohne_scout():
    start = HTML.index("setMode(m) {")
    block = HTML[start:start + 900]
    assert "scout" not in block.lower()


def test_s1d_kein_scout_objekt_filter_karte():
    for name in ("const Scout =", "applyToScout", "_isScout", "_scoutRaw", "function scoutCard",
                 "_currentScout", "_saveFromDetail", "SESSION_LABELS", "isScoutOnly", "isScoutView"):
        assert name not in HTML, name


def test_s1e_frontend_loest_keinen_scout_abruf_aus():
    assert "'/discover'" not in HTML and '"/discover"' not in HTML and "`/discover" not in HTML
    assert "refresh-discover" not in HTML


def test_s1f_kein_scout_oder_entdecken_im_quelltext():
    rest = _ohne_ortsherkunft(HTML)
    treffer = [(n + 1, z.strip()[:120]) for n, z in enumerate(rest.splitlines())
               if re.search(r"scout|entdecken", z, flags=re.I)]
    assert not treffer, treffer[:10]


def test_s1g_hilfetexte_ohne_scout_bezug():
    assert "Bei Entdecken nicht verf" not in HTML
    assert "Feed, Kalender und Scout" not in HTML
    # der Eintrag zum Unterschied von Feed und Kalender bleibt (umgeschrieben, nicht nur geloescht)
    assert "Wie unterscheiden sich Feed und Kalender?" in HTML


def test_m1_muss_bleiben():
    assert "locationscout_url" in HTML
    assert "Mond-Alignment" in HTML and "Sonnen-Alignment" in HTML


def test_x1_server_bleibt_in_t1_unberuehrt():
    assert '"/discover"' in MAIN
    names = sorted(p.name for p in (ROOT / "backend" / "discover").glob("*.py"))
    assert "geometry.py" in names and len(names) >= 8, names


@pytest.mark.skipif(shutil.which("node") is None, reason="node nicht installiert")
def test_j1_skript_syntaktisch_gueltig():
    teile = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", HTML, flags=re.S)
    assert teile
    with tempfile.TemporaryDirectory() as td:
        for i, t in enumerate(teile):
            p = Path(td) / ("s%d.js" % i)
            p.write_text(t, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
            assert r.returncode == 0, r.stderr[:500]
