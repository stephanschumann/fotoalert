"""TASK-84 (Nacharbeit): Vergessener Spec-Teil aus Option B nachgeholt.

Bei der urspruenglichen Implementierung wurden Leaflet/astronomy-engine bereits von
CDN (cdnjs.cloudflare.com / cdn.jsdelivr.net) auf lokale Vendor-Dateien unter
web/vendor/ umgestellt (web/index.html laedt jetzt von dort). Zwei Teile der Spec
wurden dabei faelschlich als "Scope-Creep" uebersprungen und werden hier nachgeholt:

  1. Die von TASK-82 eingefuehrte Content-Security-Policy in deploy/Caddyfile erlaubte
     weiterhin explizit cdnjs.cloudflare.com und cdn.jsdelivr.net in script-src,
     style-src und connect-src - obwohl diese CDNs seit der Vendor-Umstellung nicht
     mehr gebraucht werden. Die CSP wurde entsprechend verschlankt.
  2. Ein automatisierter Test fuer beide Aenderungen (Vendor-Umstellung + CSP) fehlte.
     Dieser Test hier ist der Nachtrag dazu.

Statische Datei-/Konfig-Checks (Option B) - kein Netzwerk, kein laufender Server noetig.

AKs siehe BACKLOG.md TASK-84 Implementation Spec.
"""
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]

_ROOT = Path(__file__).parent.parent.parent
_INDEX_HTML = _ROOT / "web" / "index.html"
_CADDYFILE = _ROOT / "deploy" / "Caddyfile"

_VENDOR_LEAFLET_JS = _ROOT / "web" / "vendor" / "leaflet" / "leaflet.min.js"
_VENDOR_LEAFLET_CSS = _ROOT / "web" / "vendor" / "leaflet" / "leaflet.min.css"
_VENDOR_ASTRONOMY_JS = _ROOT / "web" / "vendor" / "astronomy-engine" / "astronomy.browser.min.js"

_FORBIDDEN_HOSTS = ("cdnjs.cloudflare.com", "cdn.jsdelivr.net")


def _read_index_html():
    assert _INDEX_HTML.exists(), f"{_INDEX_HTML} nicht gefunden"
    return _INDEX_HTML.read_text(encoding="utf-8")


def _read_caddyfile():
    assert _CADDYFILE.exists(), f"{_CADDYFILE} nicht gefunden"
    return _CADDYFILE.read_text(encoding="utf-8")


def _find_line_containing(source, needle):
    """Gibt die erste Zeile aus source zurueck, die needle enthaelt, oder None."""
    for line in source.splitlines():
        if needle in line:
            return line
    return None


# --- a) web/index.html: die drei betroffenen Tags zeigen auf lokale Pfade ---

def test_index_html_leaflet_css_uses_local_vendor_path():
    line = _find_line_containing(_read_index_html(), "leaflet.min.css")
    assert line is not None, "Kein <link>-Tag fuer leaflet.min.css in web/index.html gefunden"
    assert "/vendor/leaflet/leaflet.min.css" in line, (
        f"leaflet.min.css wird nicht ueber /vendor/leaflet/ geladen: {line!r}"
    )
    for host in _FORBIDDEN_HOSTS:
        assert host not in line, f"leaflet.min.css-Tag verweist noch auf {host}: {line!r}"


def test_index_html_leaflet_js_uses_local_vendor_path():
    line = _find_line_containing(_read_index_html(), "leaflet.min.js")
    assert line is not None, "Kein <script>-Tag fuer leaflet.min.js in web/index.html gefunden"
    assert "/vendor/leaflet/leaflet.min.js" in line, (
        f"leaflet.min.js wird nicht ueber /vendor/leaflet/ geladen: {line!r}"
    )
    for host in _FORBIDDEN_HOSTS:
        assert host not in line, f"leaflet.min.js-Tag verweist noch auf {host}: {line!r}"


def test_index_html_astronomy_engine_js_uses_local_vendor_path():
    line = _find_line_containing(_read_index_html(), "astronomy.browser.min.js")
    assert line is not None, (
        "Kein <script>-Tag fuer astronomy.browser.min.js in web/index.html gefunden"
    )
    assert "/vendor/astronomy-engine/astronomy.browser.min.js" in line, (
        f"astronomy.browser.min.js wird nicht ueber /vendor/astronomy-engine/ geladen: {line!r}"
    )
    for host in _FORBIDDEN_HOSTS:
        assert host not in line, (
            f"astronomy.browser.min.js-Tag verweist noch auf {host}: {line!r}"
        )


def test_index_html_has_no_remaining_cdn_references():
    """Zusaetzliche Absicherung: keine der beiden CDN-Domains taucht ueberhaupt
    noch irgendwo in web/index.html auf."""
    source = _read_index_html()
    for host in _FORBIDDEN_HOSTS:
        assert host not in source, f"{host} kommt noch in web/index.html vor"


# --- b) Vendor-Dateien existieren und sind nicht leer ---

@pytest.mark.parametrize(
    "vendor_file",
    [_VENDOR_LEAFLET_JS, _VENDOR_LEAFLET_CSS, _VENDOR_ASTRONOMY_JS],
    ids=["leaflet.min.js", "leaflet.min.css", "astronomy.browser.min.js"],
)
def test_vendor_file_exists_and_not_empty(vendor_file):
    assert vendor_file.exists(), f"Vendor-Datei fehlt: {vendor_file}"
    assert vendor_file.is_file(), f"Vendor-Pfad ist keine Datei: {vendor_file}"
    assert vendor_file.stat().st_size > 0, f"Vendor-Datei ist leer: {vendor_file}"


# --- c) deploy/Caddyfile: CSP verschlankt, CDN-Domains nicht mehr enthalten ---

def test_caddyfile_no_longer_allows_cdnjs():
    source = _read_caddyfile()
    assert "cdnjs.cloudflare.com" not in source, (
        "deploy/Caddyfile erlaubt cdnjs.cloudflare.com noch immer (CSP nicht verschlankt)"
    )


def test_caddyfile_no_longer_allows_jsdelivr():
    source = _read_caddyfile()
    assert "cdn.jsdelivr.net" not in source, (
        "deploy/Caddyfile erlaubt cdn.jsdelivr.net noch immer (CSP nicht verschlankt)"
    )


def test_caddyfile_csp_still_allows_needed_map_tile_hosts():
    """Regressionsschutz: beim Entfernen der beiden CDN-Hosts duerfen die weiterhin
    benoetigten Kartenkachel-Anbieter aus TASK-82 nicht versehentlich mit entfernt
    werden."""
    source = _read_caddyfile()
    csp_line = _find_line_containing(source, "Content-Security-Policy \"")
    assert csp_line is not None, "Keine Content-Security-Policy-Zeile in deploy/Caddyfile gefunden"
    for host in (
        "tile.openstreetmap.org",
        "server.arcgisonline.com",
        "basemaps.cartocdn.com",
    ):
        assert host in csp_line, f"CSP fehlt weiterhin benoetigter Host {host}: {csp_line!r}"
