#!/usr/bin/env python3
"""
FotoAlert – Locationscout Import Tool
======================================
Scrapt Locationscout-Listen, filtert nach Architektur/Landschaft,
und fügt ausgewählte Locations zu locations.py hinzu.

Ablauf:
  Schritt 1 – Login (einmalig):
    python3 tools/import_locationscout.py --login

  Schritt 2 – Kandidaten anzeigen:
    python3 tools/import_locationscout.py --preview

  Schritt 3 – Auswählen und importieren:
    python3 tools/import_locationscout.py --import

Voraussetzungen:
  pip install playwright beautifulsoup4
  playwright install chromium
"""

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

TOOLS_DIR   = Path(__file__).parent
PROJECT_DIR = TOOLS_DIR.parent
COOKIES_FILE = TOOLS_DIR / ".locationscout_cookies.json"
CANDIDATES_FILE = TOOLS_DIR / ".locationscout_candidates.json"
LOCATIONS_FILE  = PROJECT_DIR / "backend" / "data" / "locations.py"

LISTS = [
    "https://www.locationscout.net/locations/131-berlin",
    "https://www.locationscout.net/locations/3078-berlin-mitte",
    "https://www.locationscout.net/locations/1175-brandenburg",
]

# Tags die wir BEHALTEN wollen (Architektur & Landschaft)
KEEP_TAGS = {
    "architektur", "architecture", "kirche", "church", "schloss", "castle",
    "brücke", "bridge", "turm", "tower", "skyline", "gebäude", "building",
    "denkmal", "monument", "rathaus", "dom", "kathedrale", "cathedral",
    "industrie", "industrial", "hafen", "harbour", "harbor",
    "landschaft", "landscape", "see", "lake", "fluss", "river", "kanal", "canal",
    "wald", "forest", "feld", "field", "hügel", "hill", "küste", "coast",
    "panorama", "aussicht", "viewpoint", "sonnenuntergang", "sunset", "sunrise",
    "stadtansicht", "cityscape", "reflections", "spiegelung", "wasser", "water",
    "langzeitbelichtung", "long exposure", "nachtaufnahme", "night",
    "herbst", "autumn", "winter", "schnee", "snow",
}

# Tags die zum AUSSCHLUSS führen
SKIP_TAGS = {
    "tiere", "animals", "wildlife", "vögel", "birds", "bird",
    "boot", "boat", "schiff", "ship", "segelboot",
    "blumen", "flowers", "flower", "botanik", "botanical",
    "insekten", "insects", "makro", "macro",
    "portrait", "people", "menschen", "street photography",
    "markt", "market",
}

# Mindestabstand zu bestehenden Locations (Meter)
MIN_DISTANCE_M = 200


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Abstand in Metern zwischen zwei GPS-Punkten."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_existing_locations():
    """Liest bestehende LOCATIONS aus locations.py (observer_lat/lon)."""
    existing = []
    src = LOCATIONS_FILE.read_text(encoding="utf-8")
    # Extrahiere observer_lat / observer_lon Paare
    pairs = re.findall(
        r'observer_lat\s*=\s*([\d.]+).*?observer_lon\s*=\s*([\d.]+)',
        src, re.DOTALL
    )
    for lat, lon in pairs:
        existing.append((float(lat), float(lon)))
    return existing


def is_duplicate(lat, lon, existing) -> bool:
    for elat, elon in existing:
        if haversine(lat, lon, elat, elon) < MIN_DISTANCE_M:
            return True
    return False


def classify_tags(tags: list[str]) -> tuple[bool, str]:
    """
    Gibt (keep, reason) zurück.
    keep=True  → Architektur oder Landschaft
    keep=False → Ausschluss-Kriterium gefunden oder kein relevanter Tag
    """
    tags_lower = {t.lower().strip() for t in tags}

    for skip in SKIP_TAGS:
        if skip in tags_lower:
            return False, f"Ausschluss-Tag: '{skip}'"

    for keep in KEEP_TAGS:
        if keep in tags_lower:
            return True, f"Keep-Tag: '{keep}'"

    # Kein eindeutiger Tag → manuell prüfen
    return False, "Kein passender Tag (manuell prüfen)"


def slugify_id(name: str) -> str:
    """Erstellt eine Python-ID aus dem Namen."""
    s = name.lower()
    s = re.sub(r'[äöüß]', lambda m: {'ä':'ae','ö':'oe','ü':'ue','ß':'ss'}[m.group()], s)
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = s.strip('_')
    return s[:40]


# ---------------------------------------------------------------------------
# Schritt 1: Login
# ---------------------------------------------------------------------------

def cmd_login():
    """Öffnet Browser, wartet auf manuellen Login, speichert Cookies."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright nicht installiert.")
        print("   pip install playwright && playwright install chromium")
        sys.exit(1)

    print("🌐 Browser öffnet sich – bitte bei Locationscout einloggen.")
    print("   Nach dem Login warte ich 5 Sekunden und speichere dann die Cookies.")
    print("   Du kannst auch einfach Enter drücken wenn du eingeloggt bist.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto("https://www.locationscout.net/login")
        page.wait_for_url("**/login", timeout=5000)

        print("Warte auf Login... (Enter drücken wenn fertig)")
        try:
            input()
        except EOFError:
            time.sleep(10)

        # Prüfen ob Login erfolgreich
        current_url = page.url
        if "login" in current_url:
            print("⚠️  Noch auf der Login-Seite. Warte weitere 15 Sekunden...")
            time.sleep(15)

        cookies = ctx.cookies()
        COOKIES_FILE.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
        print(f"✅ {len(cookies)} Cookies gespeichert → {COOKIES_FILE.name}")
        browser.close()


# ---------------------------------------------------------------------------
# Schritt 2: Scraping & Preview
# ---------------------------------------------------------------------------

def scrape_list(page, list_url: str) -> list[dict]:
    """Scrapt eine Locationscout-Listen-URL und gibt Location-Dicts zurück."""
    from bs4 import BeautifulSoup

    print(f"\n📋 Lade Liste: {list_url}")
    page.goto(list_url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(4)  # JS rendern lassen

    # Scroll bis alle Einträge geladen (Infinite Scroll)
    prev_count = 0
    for _ in range(20):  # max 20 Scroll-Runden
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.5)
        count = page.evaluate("document.querySelectorAll('a[href]').length")
        if count == prev_count:
            break
        prev_count = count
        print(f"   {count} Links geladen...")

    html = page.content()

    # Debug: ersten 3000 Zeichen ausgeben damit wir die Struktur sehen
    debug_file = Path(__file__).parent / ".debug_page.html"
    debug_file.write_text(html, encoding="utf-8")
    print(f"   🔍 Seiten-HTML gespeichert → {debug_file} ({len(html)} Zeichen)")

    soup = BeautifulSoup(html, "html.parser")

    # Nur echte Spot-URLs: /germany/{id}-{slug}/{spotid}
    # Beispiel: /germany/5165-haus-der-kulturen-der-welt-berlin/9220
    SPOT_URL_RE = re.compile(r'^/germany/\d+-[a-z0-9\-]+/\d+$')
    all_links = soup.find_all("a", href=True)
    seen_hrefs: set = set()
    cards = []
    for a in all_links:
        h = a.get("href", "").split("?")[0].rstrip("/")
        if SPOT_URL_RE.match(h) and h not in seen_hrefs:
            seen_hrefs.add(h)
            cards.append(a)

    print(f"   → {len(cards)} Spot-Links gefunden (von {len(all_links)} gesamt)")

    locations = []
    seen_urls = set()

    for card in cards:
        try:
            # URL extrahieren
            link = card if card.name == 'a' else card.find("a", href=True)
            if not link:
                continue
            href = link.get("href", "")
            if not href or href in seen_urls:
                continue
            if not any(x in href for x in ["/germany/", "/locations/"]):
                continue
            seen_urls.add(href)
            url = href if href.startswith("http") else f"https://www.locationscout.net{href}"

            # Name
            name_el = card.find(["h2", "h3", "h4", "span"], class_=re.compile(r'title|name|heading', re.I))
            name = name_el.get_text(strip=True) if name_el else link.get_text(strip=True)
            if not name or len(name) < 3:
                continue

            # Tags
            tag_els = card.select("[class*='tag'], [class*='category'], [class*='label']")
            tags = [t.get_text(strip=True) for t in tag_els if t.get_text(strip=True)]

            # Thumbnail
            img = card.find("img")
            thumbnail = img.get("src", img.get("data-src", "")) if img else ""

            locations.append({
                "name": name,
                "url": url,
                "tags": tags,
                "thumbnail": thumbnail,
                "lat": None,
                "lon": None,
                "description": "",
            })
        except Exception:
            continue

    return locations


def fetch_location_detail(page, loc: dict) -> dict:
    """Holt GPS + vollständige Tags von der Detailseite."""
    from bs4 import BeautifulSoup

    try:
        page.goto(loc["url"], wait_until="domcontentloaded", timeout=20000)
        time.sleep(1)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Debug: erste Detailseite speichern
        debug_detail = Path(__file__).parent / ".debug_detail.html"
        if not debug_detail.exists():
            debug_detail.write_text(html, encoding="utf-8")
            print(f"      🔍 Detail-HTML gespeichert → {debug_detail}")

        # 1) Meta-Tags (Open Graph / Schema.org)
        lat = (
            _meta(soup, "place:location:latitude") or
            _meta(soup, "geo.latitude") or
            _json_ld_coord(soup, "latitude")
        )
        lon = (
            _meta(soup, "place:location:longitude") or
            _meta(soup, "geo.longitude") or
            _json_ld_coord(soup, "longitude")
        )

        # 2) data-lat / data-lng Attribute
        if not lat:
            el = soup.find(attrs={"data-lat": True})
            if el:
                lat = el["data-lat"]
                lon = el.get("data-lng") or el.get("data-lon") or el.get("data-long")

        # 3) Leaflet: L.marker([lat, lon]) oder L.latLng(lat, lon)
        if not lat:
            m = re.search(r'L\.(marker|latLng)\(\[?\s*([\d.]+)\s*,\s*([\d.]+)', html)
            if m:
                lat, lon = m.group(2), m.group(3)

        # 4) Google Maps: new google.maps.LatLng(lat, lon)
        if not lat:
            m = re.search(r'LatLng\(\s*([\d.]+)\s*,\s*([\d.]+)', html)
            if m:
                lat, lon = m.group(1), m.group(2)

        # 5) JSON-Strings: "lat":52.xxx oder "latitude":52.xxx
        if not lat:
            m = re.search(r'"lat(?:itude)?"\s*:\s*(5[0-9]\.\d+)', html)  # 50–59 = Deutschland
            if m:
                lat = m.group(1)
        if not lon:
            m = re.search(r'"l(?:ng|on)(?:itude)?"\s*:\s*([\d.]+)', html)
            if m:
                lon = m.group(1)

        # 6) Koordinaten neben Temperatur/Info: "52.51753" "13.36537" im Text
        if not lat:
            m = re.search(r'\b(5[0-9]\.\d{4,})\b.*?\b(1[0-9]\.\d{4,})\b', html)
            if m:
                lat, lon = m.group(1), m.group(2)

        if lat and lon:
            loc["lat"] = float(lat)
            loc["lon"] = float(lon)

        # Alle Tags von der Detailseite
        tag_els = soup.select("[class*='tag'], [class*='category'], [class*='label'], [class*='badge']")
        detail_tags = [t.get_text(strip=True) for t in tag_els if t.get_text(strip=True)]
        loc["tags"] = list(set(loc["tags"] + detail_tags))

        # Beschreibung
        desc_el = soup.find("div", class_=re.compile(r'desc|content|about', re.I))
        if desc_el:
            loc["description"] = desc_el.get_text(separator=" ", strip=True)[:300]

    except Exception as e:
        print(f"   ⚠️  Fehler bei {loc['url']}: {e}")

    return loc


def _meta(soup, name: str):
    tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
    return tag.get("content") if tag else None


def _json_ld_coord(soup, key: str):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                geo = data.get("geo", {})
                if key in geo:
                    return str(geo[key])
        except Exception:
            pass
    return None


def cmd_preview():
    """Scrapt alle Listen und speichert gefilterte Kandidaten."""
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup  # noqa: F401 – Check import
    except ImportError:
        print("❌ Abhängigkeiten fehlen:")
        print("   pip install playwright beautifulsoup4 && playwright install chromium")
        sys.exit(1)

    if not COOKIES_FILE.exists():
        print("❌ Keine Login-Cookies gefunden. Zuerst: python3 tools/import_locationscout.py --login")
        sys.exit(1)

    cookies = json.loads(COOKIES_FILE.read_text())
    existing = load_existing_locations()
    print(f"✅ {len(existing)} bestehende Locations geladen (Duplikat-Radius: {MIN_DISTANCE_M}m)")

    all_locations = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # headed: Cloudflare erkennt headless als Bot
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        # navigator.webdriver = false
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Alle Listen scrapen
        for list_url in LISTS:
            locs = scrape_list(page, list_url)
            all_locations.extend(locs)

        # Duplikate auf URL-Basis entfernen
        seen = set()
        unique = []
        for loc in all_locations:
            if loc["url"] not in seen:
                seen.add(loc["url"])
                unique.append(loc)
        print(f"\n🔍 {len(unique)} einzigartige Locations gefunden")

        # Detailseiten für GPS abrufen
        print("\n📍 GPS-Koordinaten abrufen (kann einige Minuten dauern)...")
        for i, loc in enumerate(unique):
            print(f"   [{i+1}/{len(unique)}] {loc['name'][:50]}", end=" ", flush=True)
            fetch_location_detail(page, loc)
            if loc["lat"]:
                print(f"→ {loc['lat']:.4f}, {loc['lon']:.4f}")
            else:
                print("→ kein GPS")
            time.sleep(0.5)

        browser.close()

    # Filtern
    candidates = []
    skipped = []

    for loc in unique:
        if not loc["lat"] or not loc["lon"]:
            skipped.append((loc["name"], "Kein GPS"))
            continue

        keep, reason = classify_tags(loc["tags"])
        if not keep:
            skipped.append((loc["name"], reason))
            continue

        if is_duplicate(loc["lat"], loc["lon"], existing):
            skipped.append((loc["name"], f"Duplikat (<{MIN_DISTANCE_M}m zu bestehender Location)"))
            continue

        candidates.append({**loc, "keep_reason": reason})

    # Ergebnis speichern
    CANDIDATES_FILE.write_text(json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8")

    # Ausgabe
    print(f"\n{'='*60}")
    print(f"✅ {len(candidates)} Kandidaten nach Filter")
    print(f"⏭  {len(skipped)} übersprungen")
    print(f"{'='*60}\n")

    for i, loc in enumerate(candidates, 1):
        tags_str = ", ".join(loc["tags"][:4]) if loc["tags"] else "–"
        print(f"  [{i:2d}] {loc['name']}")
        print(f"        GPS: {loc['lat']:.5f}, {loc['lon']:.5f}")
        print(f"        Tags: {tags_str}")
        print(f"        URL: {loc['url']}")
        print()

    print(f"💾 Kandidaten gespeichert → {CANDIDATES_FILE.name}")
    print(f"\nNächster Schritt:")
    print(f"  python3 tools/import_locationscout.py --import")


# ---------------------------------------------------------------------------
# Schritt 3: Import
# ---------------------------------------------------------------------------

def cmd_import():
    """Interaktive Auswahl und Schreiben in locations.py."""
    if not CANDIDATES_FILE.exists():
        print("❌ Keine Kandidaten gefunden. Zuerst: python3 tools/import_locationscout.py --preview")
        sys.exit(1)

    candidates = json.loads(CANDIDATES_FILE.read_text(encoding="utf-8"))

    if not candidates:
        print("Keine Kandidaten vorhanden.")
        sys.exit(0)

    # Nochmal anzeigen
    print(f"\n{'='*60}")
    print(f"  {len(candidates)} Kandidaten zur Auswahl")
    print(f"{'='*60}\n")
    for i, loc in enumerate(candidates, 1):
        print(f"  [{i:2d}] {loc['name']}")
        print(f"        {loc['lat']:.5f}, {loc['lon']:.5f} | {', '.join(loc['tags'][:3])}")
        print()

    print("Welche Nummern importieren? (z.B. '1,3,5-8' oder 'alle' oder 'keine')")
    selection = input("→ ").strip().lower()

    if selection in ("keine", "n", ""):
        print("Abgebrochen.")
        sys.exit(0)

    if selection in ("alle", "all", "a"):
        selected = list(range(len(candidates)))
    else:
        selected = []
        for part in selection.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-")
                selected.extend(range(int(a)-1, int(b)))
            else:
                selected.append(int(part)-1)

    chosen = [candidates[i] for i in selected if 0 <= i < len(candidates)]
    print(f"\n✅ {len(chosen)} Locations ausgewählt:\n")

    # Python-Code generieren
    code_blocks = []
    for loc in chosen:
        loc_id = slugify_id(loc["name"])
        # Kategorie bestimmen
        tags_lower = {t.lower() for t in loc["tags"]}
        if any(t in tags_lower for t in ["architektur", "architecture", "kirche", "church",
                                           "schloss", "castle", "brücke", "bridge", "turm",
                                           "tower", "skyline", "denkmal", "gebäude", "building"]):
            category = "ARCHITECTURE"
        else:
            category = "LANDSCAPE"

        tag_str = ", ".join(loc["tags"][:5])
        desc = loc.get("description", "")[:120].replace('"', "'") or f"Importiert von Locationscout."

        block = f'''    PhotoLocation(
        id="{loc_id}",
        name="{loc["name"]}",
        description="{desc}",
        category=LocationCategory.{category},
        observer_lat={loc["lat"]:.5f}, observer_lon={loc["lon"]:.5f},
        subject_lat={loc["lat"]:.5f},  subject_lon={loc["lon"]:.5f},  # TODO: Motiv-GPS verfeinern
        subject_name="{loc["name"]}",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: {tag_str}",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="{loc["url"]}",
        difficulty=2,
    ),'''
        code_blocks.append(block)
        print(f"  • {loc['name']} ({loc['lat']:.4f}, {loc['lon']:.4f})")

    # Vorschau
    print(f"\n{'='*60}")
    print("Generierter Code (wird an LOCATIONS-Liste angehängt):")
    print(f"{'='*60}\n")
    for block in code_blocks:
        print(block)

    # Bestätigung
    print(f"\n⚠️  Soll dieser Code in locations.py geschrieben werden? (ja/nein)")
    confirm = input("→ ").strip().lower()
    if confirm not in ("ja", "j", "yes", "y"):
        print("Abgebrochen – keine Änderungen.")
        sys.exit(0)

    # In locations.py einfügen (vor letzter schließender Klammer der LOCATIONS-Liste)
    src = LOCATIONS_FILE.read_text(encoding="utf-8")
    insert_marker = "]  # Ende LOCATIONS"
    if insert_marker not in src:
        # Fallback: vor letzter eckiger Klammer
        last_bracket = src.rfind("]")
        if last_bracket == -1:
            print("❌ Konnte Einfügeposition in locations.py nicht finden.")
            sys.exit(1)
        insert_pos = last_bracket
        new_src = src[:insert_pos] + "\n" + "\n".join(code_blocks) + "\n" + src[insert_pos:]
    else:
        new_src = src.replace(insert_marker, "\n".join(code_blocks) + "\n" + insert_marker)

    # Backup
    backup = LOCATIONS_FILE.with_suffix(".py.bak")
    backup.write_text(src, encoding="utf-8")
    print(f"💾 Backup → {backup.name}")

    LOCATIONS_FILE.write_text(new_src, encoding="utf-8")
    print(f"✅ {len(chosen)} Locations in locations.py geschrieben!")
    print(f"\n📝 TODO für jede neue Location:")
    print(f"   • subject_lat/lon auf das tatsächliche Motiv setzen (nicht den Standort)")
    print(f"   • subject_height_m und distance_m recherchieren")
    print(f"   • solar_alignment_note und lunar_alignment_note ergänzen")
    print(f"\nDanach: python3 precompute.py  (neu berechnen)")


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="FotoAlert – Locationscout Import")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--login",   action="store_true", help="Browser-Login (einmalig)")
    group.add_argument("--preview", action="store_true", help="Listen scrapen, Kandidaten anzeigen")
    group.add_argument("--import",  dest="do_import", action="store_true", help="Auswählen und in locations.py schreiben")
    args = parser.parse_args()

    if args.login:
        cmd_login()
    elif args.preview:
        cmd_preview()
    elif args.do_import:
        cmd_import()


if __name__ == "__main__":
    main()
