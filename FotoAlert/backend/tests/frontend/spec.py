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
from pathlib import Path
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

# Timeout (ms) für das Warten auf #save-location-btn nach Klick auf "Alignments
# berechnen" in _check_location_create (TASK-66). POST /preview-alignment fragt
# Geländehöhen ab und sucht Sonne-/Mond-Alignments über 14 Tage — Stephan hat die
# reale Dauer lokal mit ~20s gemessen (altes Timeout von 15000ms war zu knapp,
# führte zu Falsch-Negativen). 35000ms = gemessene Dauer + Sicherheitspuffer für
# langsamere Umgebungen (z. B. CI).
PREVIEW_ALIGNMENT_TIMEOUT_MS = 35000

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


# --- TASK-66: echte Klick-Durchläufe (Location anlegen / Bild-Upload / Filter) -----
# Regel 1 — Location anlegen über den "+"-Tab (AddLocation-Fluss). Koordinaten werden
# per Text-Input gesetzt (KEIN Kartenklick, siehe Pre-Mortem TASK-66), erst danach wird
# "Alignments berechnen" und "Location dauerhaft speichern" geklickt.
ADD_TAB_SELECTOR = "#tab-add"
ADD_MAP_READY_SELECTOR = "#add-map.leaflet-container"
OBS_COORDS_INPUT_SELECTOR = "#obs-coords"
SUBJ_COORDS_INPUT_SELECTOR = "#subj-coords"
SUBJ_NAME_INPUT_SELECTOR = "#subj-name"
PREVIEW_BTN_SELECTOR = '[onclick="AddLocation.preview()"]'
SAVE_LOCATION_BTN_SELECTOR = "#save-location-btn"
# Beliebige, aber gültige Berlin-Koordinaten (Dezimalformat, von AddLocation._parseCoords
# unterstützt) — Distanz zwischen den beiden Punkten reicht für eine Alignment-Vorschau.
TEST_OBS_COORDS_TEXT = "52.4900, 13.3900"
TEST_SUBJ_COORDS_TEXT = "52.5050, 13.4200"
TEST_LOCATION_NAME_PREFIX = "E2E-Test-Location-"

# Kartenansicht: Marker-Icons werden von Leaflet als .leaflet-marker-icon gerendert
# (L.divIcon in MapView.loadMarkers()). Anzahl vorher/nachher vergleichen (kein Cleanup
# nötig, siehe Entscheidung Frage 1 im Ticket — jeder CI-Lauf startet mit frischer DB).
MAP_PAGE_READY_SELECTOR = "#map.leaflet-container"
MAP_MARKER_SELECTOR = ".leaflet-marker-icon"

# Regel 2 — Bild-Upload GEZIELT über das LocationDetail-Sheet (BUG-71-Regressionsschutz).
# WICHTIG: Der Upload-Button ist nur für Auth.isHost() im DOM (_imageAreaHtml in
# web/index.html), UND der Server-Endpunkt POST /locations/{id}/image verlangt
# auth.require_host — der reguläre Test-Login des bestehenden Checks (test-user-pw,
# Rolle "user") kann diesen Pfad technisch nicht erreichen. _check_image_upload() öffnet
# deshalb eine ZUSÄTZLICHE, isolierte Browser-Seite mit Host-Login, ausschließlich für
# diesen einen Durchlauf — die reguläre Desktop-Pass-Session (User-Rolle) bleibt für
# alle anderen Checks unverändert.
LOC_IMAGE_UPLOAD_BTN_SELECTOR = "#loc-detail-sheet .loc-image-upload-btn"
LOC_IMAGE_AREA_IMG_SELECTOR = "#loc-detail-sheet .loc-image-area img"
TEST_IMAGE_FIXTURE_PATH = str(Path(__file__).resolve().parent / "fixtures" / "test-image.jpg")

# Regel 3 — Filter setzen: minScore auf einen deterministischen Extremwert setzen
# (unabhängig von der aktuellen Live-Datenlage, siehe Frage 3 / Pre-Mortem TASK-66).
FEED_CONTENT_SELECTOR = "#feed-content"
FILTER_MIN_SCORE_EXTREME = 100
FILTER_MIN_SCORE_DEFAULT = 70  # Filter.defaultState() in web/index.html


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
