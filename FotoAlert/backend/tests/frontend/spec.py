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
# CI-Fix (Workflow-Lauf #189, v1.22.15): ein fester Extremwert (vormals hier als
# FILTER_MIN_SCORE_EXTREME = 100 hinterlegt) war NICHT strukturell deterministisch —
# bei nur 1 Baseline-Eintrag (frischer CI-Checkout ohne vorberechneten Datenbestand)
# konnte dessen Score zufällig genau am Extremwert liegen, sodass kein Rückgang
# gemessen wurde. Ersetzt durch einen zur Laufzeit aus Feed.data berechneten
# Schwellwert in run_frontend_check.py::_check_filter_feed — der Konstante wurde
# dadurch überflüssig und deshalb entfernt (kein toter Fallback ohne Nutzung).
FEED_CONTENT_SELECTOR = "#feed-content"
FILTER_MIN_SCORE_DEFAULT = 70  # Filter.defaultState() in web/index.html


# --- TASK-67 (Etappe 3): Kalender, Filter-Chips, Bewertung, Detail-Sheet-aus-Feed,
# Wetterkarte, Entdecken-Modus, globale UI/Filter-Grenzfälle ----------------------
# Alle drei Feed-Modi (14-Tage-Feed / Jahreskalender / Scout) werden über dieselbe
# feed-mode-bar innerhalb #page-feed umgeschaltet (Feed.setMode(...)), NICHT über die
# Tab-Bar. Selektoren unten wurden per Grep aus web/index.html verifiziert (Stand
# 2026-07-11), nicht angenommen.

# Kalender-Modus (Feed.setMode('calendar') -> CalendarView.render()).
CALENDAR_MODE_BTN_SELECTOR = "#fmb-calendar"
CALENDAR_NAV_SELECTOR = ".cal-nav"
CALENDAR_EVENT_SELECTOR = ".cal-event"
CALENDAR_EMPTY_SELECTOR = ".empty"

# Scout/Entdecken-Modus (Feed.setMode('scout') -> Scout.show()).
SCOUT_MODE_BTN_SELECTOR = "#fmb-scout"
FEED_MODE_BTN_SELECTOR = "#fmb-feed"
SCOUT_CONTENT_SELECTOR = "#scout-content"

# Filter-Sheet: Drei-Zustand-Chips (chip3-Pattern, web/index.html ab Zeile ~3466).
# Kein eigenes id je Chip — Selektor über das onclick-Attribut (stabil, da Funktions-
# name+Argument Teil der Testabdeckung selbst sind).
FILTER_BTN_SELECTOR = "#filter-btn"
FILTER_SHEET_OPEN_SELECTOR = "#filter-sheet.open"
FILTER_BADGE_SELECTOR = "#filter-badge"
VERIFICATION_CHIP_VERIFIED_SELECTOR = '[onclick="FilterSheet._cycleVerification(\'verified\')"]'
# Tageszeit-Filter-Section wird auf Karte/Locations-Tab ausgegraut (BUG-46,
# dimOnLocAndMap in FilterSheet._render()), auf Feed/Kalender/Scout nicht.
TAGESZEIT_SECTION_SELECTOR = ".filter-section:has(h4:has-text('Tageszeit'))"

# Bewertungsfunktion (Rating-Objekt, web/index.html ab Zeile ~2719): Sterne-Input
# lebt im Location-Detail-Sheet, IDs sind pro Location generiert
# (locationId.replace(/[^a-z0-9]/gi,'_')) -> per Klasse statt fixer ID ansprechen.
RATING_STAR_BTN_SELECTOR = "#loc-detail-sheet .star-input .star-btn"
RATING_CLEAR_BTN_SELECTOR = "#loc-detail-sheet .btn-verify-cancel"
RATING_SECTION_SELECTOR = "#loc-detail-sheet [id^='rating-section-']"

# Detail-Sheet-aus-Feed-Karte (Abgrenzung zu _check_detail_sheet oben, die bewusst
# das LOCATION-Detail prüft): Feed-Karten haben onclick="Detail.open(...)" (Zeile
# ~1876), Klick soll #detail-sheet.open öffnen (NICHT #loc-detail-sheet).
FEED_CARD_SELECTOR = "#feed-content .card"
EVENT_DETAIL_SHEET_OPEN_SELECTOR = "#detail-sheet.open"
EVENT_DETAIL_CLOSE_BTN_SELECTOR = "#detail-sheet .close-btn"

# Wetter-Kartenansicht (WeatherMap-Objekt, web/index.html ab Zeile ~5126): Ebenen-
# Umschalter (Wolken/Niederschlag/Aus) + Zeit-Schieberegler.
WEATHER_MODE_CLOUDS_BTN_SELECTOR = '[onclick="WeatherMap.setMode(\'clouds\')"]'
WEATHER_MODE_OFF_BTN_SELECTOR = '[onclick="WeatherMap.setMode(\'off\')"]'
WEATHER_SLIDER_SELECTOR = "#map-weather-slider"
WEATHER_SLIDER_WRAP_OPEN_SELECTOR = "#map-weather-slider-wrap.open"

# Globale UI (PRODUCT.md Abschnitt 2): "?"-Header-Button öffnet Glossar-Overlay.
HELP_BTN_SELECTOR = "#help-btn"
GLOSSARY_OVERLAY_OPEN_SELECTOR = "#glossary-overlay.open"
GLOSSARY_CLOSE_SELECTOR = "#glossary-overlay"  # onclick=Glossary.close() liegt auf dem Overlay selbst

# Timeout für die Wetterkarten-Datenabfrage (/weather-map?hours=72, DWD/MET-Norway-
# Quelle + PNG-Vorabladen) — großzügig bemessen, da echter Netzwerk-/Serverpfad
# (siehe Pattern 15: Verifikation über den echten Aufrufpfad, nicht isoliert).
WEATHER_MAP_FETCH_TIMEOUT_MS = 20000


# --- TASK-67 (Etappe 6): restliche Filter-Kriterien (Badge, Bewertungs-Chip,
# Wahrscheinlichkeit-Dimming, Karten-Pin-Filterung, Sichtachse, Hat-Beispielbild) ---
# Selektoren per Grep aus web/index.html verifiziert (Stand 2026-07-12), nicht
# angenommen. FilterSheet-Sections sind NICHT in ein mkSec(...)-Accordion gewrappt
# (anders als LocationDetail-Sheet-Sections, siehe Etappe-3/5-Lektion) — kein
# Sections.toggle(...) noetig, um einen Filter-Chip zu erreichen.

# Bewertungs-Chip (Filter-Sheet, FilterSheet._cycleRating(v)) — fixer Testwert v=3.
RATING_CHIP_TEST_VALUE = 3
RATING_CHIP_SELECTOR_TMPL = '[onclick="FilterSheet._cycleRating({0})"]'

# Wahrscheinlichkeit: dieselbe Dimming-Logik wie Tageszeit (dimOnLocAndMap in
# FilterSheet._render(), web/index.html ~Zeile 3574/3582). Brennweite bewusst NICHT
# hier aufgenommen — siehe Etappe-6-Befund im Ticket (web/index.html ~Zeile 3576:
# dimFocalOnMap ist hartcodiert `false`, Brennweite filtert Karte/Locations-Tab
# tatsächlich aktiv mit, ~Zeile 5068-5073 — das widerspricht PRODUCT.md Abschnitt 3a,
# das Brennweite als ausgegraut führt. Rückfrage an Stephan offen, deshalb hier
# bewusst ausgelassen statt eine falsche Erwartung zu testen).
WAHRSCHEINLICHKEIT_SECTION_SELECTOR = ".filter-section:has(h4:has-text('Mindest-Wahrscheinlichkeit'))"

# Sichtachsen-Filter-Chip (vier unabhängige Werte, hier 'frei' als Testwert).
SIGHTLINE_CHIP_SELECTOR_TMPL = '[onclick="FilterSheet._cycleSightline(\'{0}\')"]'
SICHTACHSE_SECTION_SELECTOR = ".filter-section:has(h4:has-text('Sichtachse'))"

# "Hat Beispielbild"-Chip (ein Chip, drei Zustände, FilterSheet._cycleHasImage()).
HASIMAGE_CHIP_SELECTOR = '[onclick="FilterSheet._cycleHasImage()"]'
HASIMAGE_SECTION_SELECTOR = ".filter-section:has(h4:has-text('Beispielbild'))"

# Schwierigkeits-/Kategorie-/Verifikations-Chip-Templates für die Karten-Pin-
# Filterung (_check_map_pin_filtering) — Testwerte werden zur Laufzeit aus den
# tatsächlich geladenen Markern bestimmt (kein hartcodierter Datensatz, gleiches
# Determinismus-Muster wie der Score-Schwellwert in _check_filter_feed).
DIFFICULTY_CHIP_SELECTOR_TMPL = '[onclick="FilterSheet._cycle(\'difficulty\',\'difficultyExcl\',{0})"]'
CATEGORY_CHIP_SELECTOR_TMPL = '[onclick="FilterSheet._cycle(\'category\',\'categoryExcl\',\'{0}\')"]'
VERIFICATION_CHIP_SELECTOR_TMPL = '[onclick="FilterSheet._cycleVerification(\'{0}\')"]'


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
