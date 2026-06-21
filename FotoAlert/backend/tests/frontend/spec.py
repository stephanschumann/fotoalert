"""TASK-20 — Spezifikation der zu prüfenden Frontend-Views und Link-Schemata.

Reine Datentabelle, kein Browser. Trennt das *Was wird geprüft* (hier) vom *Wie*
(run_frontend_check.py). Quelle der Wahrheit sind die realen IDs/Klassen aus
web/index.html (Stand 2026-06-20):
  - Views: #page-feed / #page-map / #page-locations / #page-settings, aktiviert
    über App.nav('feed'|'map'|'locations'|'settings'); Tab-Bar #tab-bar.
  - Detail-Sheet: #detail-sheet mit Maps-Links .loc-maps-btn, Locationscout optional.
  - Externe Links (nur href geprüft, nie abgerufen):
      Apple Maps   https://maps.apple.com/?ll=...
      Google Maps  https://www.google.com/maps?q=...
      Street View  https://www.google.com/maps/@?api=1&map_action=pano&...
      Locationscout (optional, beliebige URL des Hosts)
"""
from __future__ import annotations

import re
from typing import Dict, List, NamedTuple, Pattern


class ViewSpec(NamedTuple):
    """Eine prüfbare View: wie sie aktiviert wird und welche Elemente Pflicht sind."""

    view_id: str            # logischer Name, zugleich assertion-Namespace
    nav_arg: str            # Argument für App.nav(...)
    page_selector: str      # Container, der nach Navigation .active sein muss
    required_selectors: List[str]   # Pflicht-Schlüsselelemente (CSS)


class LinkSchema(NamedTuple):
    """Ein externer Link-Typ: CSS-Treffer + erwartetes URL-Schema (Regex)."""

    link_id: str
    href_pattern: "Pattern[str]"
    required: bool          # False => Fehlen ist erlaubt (Edge, AK3)


# --- Views -------------------------------------------------------------------------
# Tab-Bar ist auf jeder View Pflicht; #map braucht den Leaflet-Container.
VIEWS: List[ViewSpec] = [
    ViewSpec(
        view_id="feed",
        nav_arg="feed",
        page_selector="#page-feed",
        required_selectors=["#tab-bar", "#feed-content", ".feed-mode-bar"],
    ),
    ViewSpec(
        view_id="map",
        nav_arg="map",
        page_selector="#page-map",
        # Leaflet macht das #map-Element SELBST zum Container (L.map('map') hängt die
        # Klasse `leaflet-container` an #map, nicht an ein Kind) → Selektor OHNE Leerzeichen.
        required_selectors=["#tab-bar", "#map", "#map.leaflet-container"],
    ),
    ViewSpec(
        view_id="locations",
        nav_arg="locations",
        page_selector="#page-locations",
        required_selectors=["#tab-bar", "#locations-content"],
    ),
    ViewSpec(
        view_id="settings",
        nav_arg="settings",
        page_selector="#page-settings",
        required_selectors=["#tab-bar", "#settings-content"],
    ),
]


# --- Externe Link-Schemata ---------------------------------------------------------
# Reihenfolge der Query-Parameter ist im Frontend fix; Pattern bleibt aber tolerant
# gegenüber zusätzlichen Parametern. Koordinaten sind volatil → nur Form, nicht Wert.
_NUM = r"-?\d+(?:\.\d+)?"

LINK_SCHEMAS: Dict[str, LinkSchema] = {
    "apple_maps": LinkSchema(
        link_id="apple_maps",
        href_pattern=re.compile(
            r"^https://maps\.apple\.com/\?ll=" + _NUM + r"," + _NUM + r"(?:&|$)"
        ),
        required=True,
    ),
    "google_maps": LinkSchema(
        link_id="google_maps",
        href_pattern=re.compile(
            r"^https://www\.google\.com/maps\?q=" + _NUM + r"," + _NUM + r"$"
        ),
        required=True,
    ),
    "street_view": LinkSchema(
        link_id="street_view",
        href_pattern=re.compile(
            r"^https://www\.google\.com/maps/@\?api=1&map_action=pano"
            r"&viewpoint=" + _NUM + r"," + _NUM + r"&heading=\d+"
        ),
        required=True,
    ),
    "locationscout": LinkSchema(
        link_id="locationscout",
        # Optional (Edge AK3): nur Wohlgeformtheit, Host-URL kann variieren.
        href_pattern=re.compile(r"^https?://\S+$"),
        required=False,
    ),
}


# Timeout (ms) für die Pflicht-Selektor-Prüfung. Asynchron gerenderte Elemente
# (Leaflet baut #map .leaflet-container erst nach App.nav('map') auf) brauchen Zeit;
# wait_for_selector mit diesem Timeout verhindert Falsch-Negative (Finding 1).
REQUIRED_SELECTOR_TIMEOUT_MS = 8000

# Externe Maps-/SV-Links liegen im LOCATION-Detail (#loc-detail-sheet), das über
# LocationDetail.open(id) aus der Locations-View geöffnet wird. Dort sind es echte
# <a class="loc-maps-btn" href=...>-Links (Apple/Google/Street View). Das EVENT-Detail
# (#detail-sheet) hat dafür nur <button onclick=window.open(...)> ohne href → daher
# wird hier bewusst das Location-Detail geprüft (Findings 2–4).
DETAIL_SHEET_SELECTOR = "#loc-detail-sheet"
LINK_SELECTOR = "#loc-detail-sheet a.loc-maps-btn"

# Das Location-Detail-Sheet wird über die Locations-View geöffnet: App.nav('locations'),
# dann Klick auf eine Location-Karte (onclick="LocationDetail.open('<id>')").
LOCATIONS_NAV_ARG = "locations"
LOCATION_CARD_SELECTOR = "#locations-content [onclick^='LocationDetail.open']"
# Das Sheet ist im DOM permanent vorhanden; sichtbar wird es über die Klasse .open.
DETAIL_SHEET_OPEN_SELECTOR = "#loc-detail-sheet.open"


def classify_href(href: str) -> str:
    """Ordnet eine href einem Link-Typ zu (rein lexikalisch, kein Abruf).

    Gibt den link_id zurück, dessen Präfix passt, sonst 'unknown'.
    """
    if href.startswith("https://maps.apple.com/"):
        return "apple_maps"
    if href.startswith("https://www.google.com/maps/@?"):
        return "street_view"
    if href.startswith("https://www.google.com/maps?q="):
        return "google_maps"
    return "locationscout"
