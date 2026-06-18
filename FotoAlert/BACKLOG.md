# FotoAlert – Backlog

> Ideen, Verbesserungen und offene Aufgaben.  
> Claude liest diese Datei am Anfang jedes Chats und erinnert dich an offene Punkte.
>
> **Typen:** `US-XX` User Story (Feature) · `TASK-XX` Aufgabe (kein User Value) · `BUG-XX` Fehler (Problemlösung)  
> **Status:** `[ ]` offen · `[~]` in Arbeit · `[x]` erledigt  
> **Workflow:** Claude setzt auf `[~]` bei Implementierungsbeginn. `[x]` + Verschiebung nach ✅ Erledigt nur nach expliziter Bestätigung durch Stephan.

---

## 🐛 BugFixes

### BUG-17 · Vollbild-Nutzung: Safe Area & App-Hintergrundfarbe `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-17 16:22 |
| **In Progress seit** | 2026-06-17 17:10 |
| **Abgeschlossen** | 2026-06-17 17:45 |

**Beschreibung:**
Die PWA nutzt den iPhone-Bildschirm nicht vollständig aus. Oben gibt es einen zu großen Abstand zwischen der Statusleiste (Uhrzeit, Kamera, Batterie/WLAN) und dem App-Header – der Hintergrund füllt diese Zone mit der falschen Farbe. Unten zeigt der Bereich hinter dem Tab-Menü Schwarz statt der App-Hintergrundfarbe, und das Menü sitzt zu nah an der Home-Indicator-Linie.

**Scope:**
- Eingeschlossen: `viewport-fit=cover` in `<meta name="viewport">`, `env(safe-area-inset-top)` auf Header, `env(safe-area-inset-bottom)` auf Tab-Bar, `background-color` auf `html`/`body`
- Ausgeschlossen: Inhaltliche Layout-Änderungen, Sheets/Modals (sofern nicht direkt betroffen)

**Akzeptanzkriterien:**
- [x] `html` und `body` tragen die App-Dunkelfarbe – kein schwarzer Streifen oben oder unten sichtbar
- [x] App-Content/Header reicht oben hinter die Statusleiste (`viewport-fit=cover` + `padding-top: env(safe-area-inset-top)`)
- [x] Tab-Menü hat unten ausreichend Abstand zur Home-Indicator-Linie (`padding-bottom: env(safe-area-inset-bottom)`)
- [x] Kein Content wird durch Statusleiste oder Home-Indicator verdeckt (Tappability vollständig erhalten)
- [x] Auf iPhone in Safari PWA-Modus getestet und visuell bestätigt

**Analyse & Planung** *(vor Implementierungsbeginn ausfüllen):*
- [x] `<meta name="viewport">` in `web/index.html` prüfen – `viewport-fit=cover` bereits gesetzt ✅
- [x] `html`, `body`, `#app` auf aktuelle `background-color` prüfen – `background: var(--bg)` bereits korrekt ✅
- [x] Header-Element und dessen `padding-top` prüfen – war **hardcoded `52px`** ❌ → Fix: `calc(env(safe-area-inset-top, 0px) + 12px)`
- [x] Tab-Bar/Bottom-Nav und deren `padding-bottom` prüfen – nutzte `var(--safe-b)` (CSS-Variable mit `env()`) → Safari-Bug-Risiko; Fix: `env()` direkt inlinen
- [x] `#search-bar`-Overlay (Zeile 68): fehlte `padding-top` → Fix ergänzt

**Testplan:**
- [x] Manuelle Testschritte: App auf iPhone in Safari als PWA geprüft – visuell bestätigt ✅
- [x] Unit Tests: nicht anwendbar (rein visuell/CSS)

**Scope-Änderungen** *(chronologisches Log):*
*(leer bei Erstellung)*

**Implementierungsnotizen:**
- `#header padding-top`: `52px` → `calc(env(safe-area-inset-top, 0px) + 12px)` — passt sich dynamisch an alle iPhone-Modelle an (Dynamic Island: ~59px, Standard-Notch: ~47px, Desktop-Override: 20px bleibt)
- `#tab-bar`: `var(--safe-b)` durch direkte `env(safe-area-inset-bottom, 0px)` ersetzt — umgeht Safari-Bug mit `env()` in Custom Properties
- `#search-bar`: `padding: 0 16px` → `padding: calc(env(safe-area-inset-top, 0px) + 4px) 16px 4px` — verhindert Überlappung mit Statusleiste wenn Suche offen

---


### BUG-18 · Mond-Erde-Distanz: Anzeige zeigt ~370 km statt ~384.400 km `[x]`

| Feld | Wert |
|------|------|
| **Status** | Done |
| **In Progress seit** | 2026-06-17 18:00 |
| **Abgeschlossen** | 2026-06-18 |

**Root Cause:** Frontend dividierte `moon_earth_distance_km` (korrekt in km im Cache, z.B. 364.312) durch 1000 → zeigte ~364 statt 364.312.  
**Fix:** `/1000` in `web/index.html` entfernt · `astronomy.py` auf `distance.km` direkt umgestellt · Assertion `350_000 < dist_km < 410_000` ergänzt.

### BUG-19 · iPhone: Close-Button in Sheets nicht erreichbar `[x]`

| Feld | Wert |
|------|------|
| **Status** | Done |
| **In Progress seit** | 2026-06-17 18:00 |
| **Abgeschlossen** | 2026-06-18 |

**Root Cause:** (a) Close-Button in scrollbaren Sheets scrollte mit Inhalt weg. (b) `#add-sheet`-Header zu nah an Dynamic Island. Safari WebKit Compositor-Bug: `position:sticky` + `z-index` in `overflow-y:auto` rendert unter Leaflet-Tiles.  
**Fix:** Alle Sheets (`#filter-sheet`, `#detail-sheet`, `#loc-detail-sheet`) auf Flexbox umgestellt – nur Content-Div scrollt. Header/Footer mit `flex-shrink:0`. `.add-header` mit `env(safe-area-inset-top)`.

### BUG-20 · PIN-Typen in FOV-Karte inkonsistent mit Legende `[x]`

| Feld | Wert |
|------|------|
| **Status** | Done |
| **In Progress seit** | 2026-06-17 18:00 |
| **Abgeschlossen** | 2026-06-18 |

**Root Cause:** FOV-Karte, Edit-Karte, AddLocation-Karte nutzten je unterschiedliche Marker-Typen ohne zentrales Objekt.  
**Fix:** `MapMarkers`-Objekt eingeführt – Fotograf-Standort: SVG-Tropfen mit weißem Kern (goldener Drop-Pin), Motiv: SVG-Kreuzmarke mit weißem Mittelpunkt. Alle Karten, Labels und Legende zeigen identische SVG-Icons. v1.4.17.

### BUG-21 · Brennweiten-Eingabe: Kein Komma auf iOS-Tastatur `[ ]`
> **Problem:** Das Eingabefeld für Brennweite öffnet auf iOS eine numerische Tastatur ohne Komma-Taste.
>
> **Entscheidung: Option B – Tag-Chips**
> Alle vier Lösungsoptionen dokumentiert, Option B wird implementiert:
>
> - **Option A – `inputmode="decimal"`:** Zeigt auf iOS den Dezimalpunkt. Einfachste Lösung, kein nativer Komma-Key auf deutschen Tastaturen.
> - **Option B – Tag-Chips (GEWÄHLT):** Horizontaler Chip-Slider mit Standardbrennweiten. Kein Tastatur-Problem, Touch-optimiert, schnelle Auswahl.
> - **Option C – Stepper:** +-/−-Buttons. Umständlich bei großen Werten (600mm).
> - **Option D – Hybrid:** Chip-Schnellauswahl + „Andere…"-Eingabefeld. Maximale Flexibilität, höchster Aufwand.
>
> **Chip-Werte (Option B):** 10, 14, 20, 24, 28, 35, 50, 85, 100, 135, 200, 300, 400, 500, 600 mm
>
> **Akzeptanzkriterien:**
> - Horizontaler Chip-Slider mit allen 15 Werten (10–600 mm)
> - Aktiver Chip visuell hervorgehoben
> - Auswahl speichert `focal_length_mm` direkt (kein Submit nötig)
> - Standardwert: zuletzt verwendete Brennweite oder 50 mm als Default
> - Chips passen auf iPhone-SE-Breite; Overflow horizontal scrollbar
> - Filter-Panel aktualisiert Ergebnisse direkt nach Chip-Tap
>
> **Abhängigkeiten:** US-32[x] (Filter-System)

### BUG-22 · Änderungen in Locationdetails ohne Effekt auf Chancen `[ ]`
> **Problem:** Nach dem Bearbeiten von Location-Feldern (außer Koordinaten) werden Chancen-Berechnungen nicht neu ausgelöst. Nutzer sehen veraltete Scores.
>
> **Differenzierung:**
> - **`lat`/`lon` (Koordinaten):** Recompute via TASK-12[x] bereits implementiert → Regressionsprüfung
> - **`focal_length_mm`:** Beeinflusst FOV → Pre-Compute nötig; prüfen ob TASK-12 das abdeckt
> - **`observer_floor_height_m` (US-62):** Beeinflusst Elevation-Winkel → Recompute nötig
> - **`name`/`description`:** Kein Recompute nötig – erwartetes Verhalten
>
> **Akzeptanzkriterien:**
> - PATCH auf `focal_length_mm` triggert Hintergrund-Recompute (TASK-12-Mechanismus erweitern oder prüfen)
> - PATCH auf `observer_floor_height_m` (nach US-62) triggert ebenfalls Recompute
> - PATCH auf `name`/`description` triggert KEINEN Recompute
> - Nach Recompute: Feed und Kalender zeigen aktualisierte Scores
> - API-Log zeigt Recompute-Task-Start nach Focal-Length-PATCH (technischer Nachweis)
>
> **Abhängigkeiten:** TASK-12[x], US-62

### BUG-23 · Kartenfilter-Sync: Eventtyp-Filter wirkt nicht in Kartenansicht `[ ]`
> **Problem:** Der Eventtyp-Filter (z.B. „Mond-Alignment") im Filterpanel hat keinen Effekt auf die Kartenansicht. Alle Location-Pins erscheinen unabhängig vom Filter.
>
> **Lösungskonzept:** In der Kartenansicht wird der Filter semantisch neu interpretiert: nicht „zeige nur Events dieses Typs", sondern **„zeige nur Locations, für die dieser Eventtyp astronomisch möglich ist"** (standortbasierte Filterung).
>
> **Technische Basis:** US-35[x] berechnet `possible_bodies` pro Location. Daraus folgt, welche Event-Typen an einem Ort prinzipiell möglich sind.
>
> **Mapping Eventtyp → `possible_bodies`:**
>
> | Eventtyp-Filter | Bedingung |
> |---|---|
> | Mond-Alignment | `"moon" in possible_bodies` |
> | Sonnen-Alignment | `"sun" in possible_bodies` |
> | Mondaufgang/-untergang | `"moon" in possible_bodies` |
> | Sonnenaufgang/-untergang | `"sun" in possible_bodies` |
> | Goldene/Blaue Stunde | alle Locations (Sonne immer vorhanden) |
>
> **Wichtig:** Nur der Eventtyp-Filter ist in der Karte aktiv. Der Chancenwahrscheinlichkeits-Filter (%-Slider) wird in der Kartenansicht ausgegraut mit Hinweis „Nur in Listen-Ansicht verfügbar".
>
> **Akzeptanzkriterien:**
> - Eventtyp-Filter „Mond-Alignment": Karte zeigt nur Locations mit `"moon" in possible_bodies`
> - Chancenwahrscheinlichkeits-Filter in Kartenansicht visuell ausgegraut, Tooltip „Nur in Listen-Ansicht verfügbar"
> - Filter-Zustand bleibt beim Wechsel Karte ↔ Feed erhalten
> - Kein Filter aktiv: alle Location-Pins sichtbar (wie bisher)
>
> **Abhängigkeiten:** US-35[x], US-32[x]

### BUG-14 · Jahres- & 14-Tage-Kalender leer nach Cron-Lauf `[ ]`
> **Problem:** Am 2026-06-17 um 6:20 Uhr waren Jahreskalender und 14-Tage-Kalender nach dem Cron-Lauf komplett leer. Root Cause unbekannt.
>
> **Hypothesen:**
> 1. Cron-Startzeit (aktuell 5:30 Uhr) führt zu Race Condition mit Sonnenaufgangsdaten für den aktuellen Tag
> 2. Fehler in der Astronomieberechnung (Skyfield) für diesen Kalendertag
> 3. Open-Meteo API-Timeout während des Cron-Laufs → leere Wetterdaten → keine Events generiert
> 4. Schreibfehler in `calendar.json` / `feed.json` (Permissions oder Disk-Full)
>
> **Akzeptanzkriterien:**
> - Root Cause identifiziert und dokumentiert
> - Fix deployed, Cron-Lauf produziert vollständige Kalender-Daten
> - Health-Alert: wenn nach Cron-Lauf `calendar.json` < 10 Events enthält → Fehler-Logeintrag mit Zeitstempel
> - Regression-Test: mind. 5 Events für nächste 14 Tage und 30 Events im Jahreskalender nach Cron-Lauf
>
> **Priorität:** Hoch – korrupte Kalender-Daten machen die App unbrauchbar
>
> **Abhängigkeiten:** TASK-15 (Cron-Zeit auf 0:01 Uhr als möglicher Fix)

### ~~BUG-10 · Mond-Alignments fehlen im 365-Tage-Kalender~~ `[x]`
> **Root Cause (gefunden 2026-06-18):**
> Zwei kombinierte Probleme:
>
> **1. Payload zu groß:** `calendar.json` = 149 MB, 84.045 Events. Der Browser lädt den `/calendar`-Endpoint nie vollständig — der Jahreskalender bleibt leer, weil die API-Antwort zu groß ist. Das 14-Tage-Feed (`opportunities.json`, 4,8 MB) hat keine solche Einschränkung.
>
> **2. Staler Cache:** `algorithm_version=None` → Cache wurde vor Einführung des `_in_photo_window`-Filters gebaut. Mond-Alignment-Events entstanden daher ganztägig (08–21h lokal) statt nur während der goldenen/blauen Stunde (20–21h). Das machte den Cache 3× größer als nötig.
>
> **Fix:**
> - `precompute.py`: `ALGORITHM_VERSION` "1.1" → "1.2" → erzwingt vollständige Cache-Neuberechnung mit `_in_photo_window`-Filter
> - `main.py`: `/calendar`-Endpoint erhält `year`-Parameter (zusätzlich zu `month`)
> - `index.html`: `CalendarView` lädt pro Monat (`?month=X&year=Y`) statt alle 365 Tage auf einmal; Monatscache als `_monthCache: Map` im Client
>
> **Betroffene Dateien:** `precompute.py`, `main.py`, `web/index.html`
>
> **Status:** ✅ Abgeschlossen 2026-06-18 — getestet, Mond-Alignments im Jahreskalender sichtbar, month-based loading funktioniert.


### ~~BUG-11 · App-Icon weicht vom App-Screen ab~~ `[x]`
> **Problem:** Das KI-generierte App-Icon passte nicht zum Look des App-Screens.
> **Fix:** Icon.png (Leica-Kamera) aus App-Screen als Basis; alle PWA-Größen (192×192, 512×512) neu generiert; Manifest-Pfade aktualisiert.
> **Version:** v1.4.9

### ~~BUG-12 · Fremddateien auf Server entfernen~~ `[x]`
> **Problem:** `kanban.html` und `BACKLOG.md` waren öffentlich über den Webserver abrufbar.
> **Fix:** `deploy.sh` löscht nach jedem `git pull` alle `*.md` und nicht-`index.html` HTML-Dateien aus `web/`.
> **Version:** v1.4.9

### ~~BUG-13 · Slider im Filterpanel unterschiedlich breit~~ `[x]`
> **Problem:** Brennweite-Slider und Wahrscheinlichkeits-Slider hatten unterschiedliche Breiten.
> **Referenz:** Breite des Wahrscheinlichkeits-Sliders ist maßgebend; Brennweite-Slider wird angepasst.
> **Fix:** `.dual-range-wrap` erhält `padding: 0 11px` — Thumbs fluchten jetzt mit nativem Slider-Track.
> **Version:** v1.4.9

### ~~BUG-15 · Kartenansicht startet nicht in Standardansicht~~ `[x]`
> **Problem:** Kartenansicht startete im Satellitenmodus statt OSM-Standard (Enabler: US-46).
> **Fix:** `MapView.init()` initialisiert `layers.standard` (OpenStreetMap) als Default-Layer; Satellit/Nacht nur auf Nutzerauswahl.
> **Version:** v1.4.9

### ~~BUG-16 · Karten-Overlay „Details"-Link öffnet Gesamtübersicht~~ `[x]`
> **Problem:** Der „Details"-Link im Pin-Popup öffnete die allgemeine Location-Übersicht statt das Location-Detail-Sheet der angeklickten Location.
> **Fix:** `LocationDetail.open(loc.id)` direkt aus Karten-Popup aufgerufen.
> **Version:** v1.4.9

### ~~BUG-07 · Sheets überschreiten iPhone-Breite auf Desktop~~ `[x]`
> **Als Fotograf** möchte ich, dass Detail- und Änderungsansichten dieselbe Breite wie der iPhone-App-Container haben, damit das Layout auf Desktop-Bildschirmen konsistent aussieht.
>
> **Ursache:** `#detail-sheet`, `#loc-detail-sheet`, `#filter-sheet`, `#add-sheet` nutzen `position: fixed; left: 0; right: 0` und spannen damit die volle Viewport-Breite. Auf Desktop (`min-width: 600px`) ist `#app` auf `max-width: 480px; margin: 0 auto` beschränkt, die Sheets ignorieren das.
>
> **Betroffene Datei:** `web/index.html` → `@media (min-width: 600px)` Block
>
> **Fix:** Sheets auf `left: 50%; width: 480px; right: auto; margin-left: -240px` setzen (kein `translateX`, damit bestehende `translateY`-Animation weiter funktioniert).
>
> **Akzeptanzkriterien:**
> - Alle Sheets (Event-Detail, Location-Detail, Filter, AddLocation) brechen auf Desktop nicht aus dem 480px Container heraus
> - Slide-Animationen funktionieren unverändert
> - Mobile (< 600px): kein Unterschied

### ~~BUG-05 · Feed zeigt Events mit abgelaufener Shoot-Window-Ende-Zeit~~ `[x]`
> **Als Fotograf** möchte ich im 14-Tage-Feed nur Ereignisse sehen, deren Aufnahmefenster noch nicht abgelaufen ist, damit ich keine verpassten Chancen in der Liste habe und mich auf tatsächlich noch erreichbare Events konzentrieren kann.
>
> **Problem:** Der aktuelle Backend-Filter entfernt Events erst 1 Stunde nach `shoot_time` aus dem Feed. Events, deren `shoot_window_end` bereits vergangen ist, bleiben bis zu dieser Toleranzgrenze sichtbar – auch wenn das Aufnahmefenster längst geschlossen ist.
>
> **Betroffene Datei:** `backend/main.py` → `_filter_feed()`
>
> **Akzeptanzkriterien:**
> - Backend-Filter: Event wird übersprungen wenn `shoot_window_end < now_utc` (statt bisherigem `shoot_time − 1h`)
> - Fallback wenn `shoot_window_end` fehlt oder null: `shoot_time + 30 min` als implizites Fenster-Ende
> - Jahreskalender-Tab **nicht** betroffen – dort bleiben vergangene Events für die Jahresübersicht erhalten
> - Kein separater Frontend-Filter nötig; die API liefert direkt bereinigte Ergebnisse
> - Manuelle Prüfung: Event mit `shoot_window_end` = vor 5 Min → nicht mehr im Feed; `shoot_window_end` = in 5 Min → noch sichtbar

### ~~BUG-04 · Brennweiten-Filter: Dual-Handle Range-Slider~~ `[x]`
> **Als Fotograf** möchte ich den Brennweiten-Filter über einen einzelnen Slider mit zwei Handles bedienen können, sodass ich visuell einen Bereich (z. B. 100–300 mm) einschließe und Werte außerhalb klar als exkludiert erkenne – ohne zwei separate Schieberegler kombinieren zu müssen.
>
> **Problem:** BUG-01 (erledigt) hat den Brennweiten-Filter als zwei separate `<input type="range">`-Elemente (Von/Bis) implementiert. Das ist funktional, aber UX-schwach: kein gemeinsamer Track, kein visuelles Exklusionsmuster, keine Überlappungsprüfung.
>
> **Betroffene Dateien:** `web/index.html` → `FilterSheet` (Slider-HTML + `_onFocalSlider` / `_onFocalMaxSlider`)
>
> **Akzeptanzkriterien:**
> - Zwei separate Slider (Von/Bis) durch einen Custom Dual-Handle Range-Slider auf einem gemeinsamen Track ersetzen
> - Bereich **zwischen** den Handles: farblich aktiv hervorgehoben (gold/orange)
> - Bereich **außerhalb** beider Handles: grau ausgegraut (visuell „exkludiert")
> - Handles können sich nicht überlappen (linker Handle ≤ rechter Handle zwingend)
> - Default: linker Handle bei 0 mm (kein Minimum), rechter Handle bei 600 mm (kein Maximum)
> - Dynamisches Label zeigt aktuellen Bereich: z. B. „100 mm – 300 mm" · bei Default: „Alle Brennweiten"
> - Filter-Logik unverändert: Events ohne Kamera-Hint im Bereich [min, max] werden ausgeblendet
> - Bei Default-Werten (0/600): kein Brennweiten-Filter aktiv, Badge zählt 0

### ~~BUG-03 · Scheinbare Größe des Himmelsobjekts wird zu groß berechnet~~ `[x]`
> **Als Fotograf** möchte ich in der Kompositions-Analyse eine korrekte Angabe des scheinbaren Durchmessers von Sonne und Mond erhalten, damit ich das Größenverhältnis zum Motiv realistisch einschätzen und die Bildkomposition planen kann.
>
> **Problem:** Der angezeigte Wert `body_apparent_diameter_m` in der Sektion „🎯 Kompositions-Analyse" erscheint größer als erwartet. Mögliche Ursachen: (a) `d` ist Horizontaldistanz statt Schrägdistanz, (b) Winkelgröße oder Formelparameter falsch, (c) Darstellungsfehler im Frontend.
>
> **Betroffene Datei:** `backend/precompute.py` → `_composition_analysis()`, Zeile 121
>
> **Aktuelle Formel:**
> ```python
> body_apparent_diameter_m = d * math.tan(math.radians(angular_diameter_deg / 2)) * 2
> # d = loc.distance_m (Horizontaldistanz)
> # angular_diameter_deg: Mond 0.5181°, Sonne 0.5333°
> ```
>
> **Akzeptanzkriterien:**
> - Referenzwerte dokumentieren: Mond (Ø 0.5181°) bei 2.000 m Horizontal → erwartet ~18,1 m; bei 5.000 m → ~45,2 m
> - Prüfen ob Schrägdistanz (`d_slant = sqrt(d_horizontal² + height_above_observer²)`) korrekteres Ergebnis liefert (bei großen Höhenunterschieden > 50 m relevant)
> - Vergleich mit gemeldeten Ist-Werten von Stephan – konkrete Location + beobachteten Wert als Referenz nutzen
> - Winkelgrößen gegen aktuelle Ephemeridenwerte validieren (Mond-Ø 29,4′–33,5′, Mittel ~31,1′)
> - Falls Fix nötig: Formel korrigieren, Kommentar im Code aktualisieren, betroffene Locations neu berechnen (`python3 precompute.py --feed-only`)
> - Nach Fix: `size_ratio` und `ratio_label` bleiben plausibel (Mond kann nicht größer als Motiv wirken bei typischen Distanzen > 1 km)

### ~~BUG-02 · Suche filtert Jahreskalender nicht~~ `[x]`
> **Problem:** Die Suchleiste (Lupe im Header) funktioniert im 14-Tage-Feed korrekt, hat aber keinen Effekt im 365-Tage-Jahreskalender.
>
> **Ursache:** `Search.onInput()` und `Search.close()` riefen immer `Feed.render()` auf, nie `CalendarView.render()`. Zudem hatte `CalendarView.render()` keinen Suchfilter.
>
> **Fix:** `Search._triggerRender()` wählt je nach `Feed.mode` den richtigen Renderer. `CalendarView.render()` filtert jetzt nach `Search.query` (location_name + title + event_type). Status-Zeile zeigt aktive Suche an. v1.1.8.

### ~~BUG-08 · Mindest-Wahrscheinlichkeits-Filter filtert nicht korrekt~~ `[x]`
> **Problem:** Wenn im Filter-Sheet unter „Mindest-Score" ein Wert ≥ 85 % eingestellt ist, erscheinen im Feed trotzdem Events mit deutlich niedrigerer Wahrscheinlichkeit (z. B. 59 %). Der Filter hat keinen Effekt.
>
> **Ursachen (v1.4.1):**
> 1. `id="score-val"` Kollision: Settings-Seite und FilterSheet nutzten dieselbe ID; `getElementById` traf den Settings-Eintrag → Label aktualisierte sich nicht
> 2. Settings-Slider setzte `CFG.minScore` auf 0.85 → Backend lieferte nur Events ≥ 0.85 → FilterSheet-Filter auf 85% hatte keinen sichtbaren Effekt
> 3. Locations-Tab: kein Filter angewandt
>
> **Fix (v1.4.1):**
> - FilterSheet-Label umbenannt auf `filter-score-val`
> - Settings-„Mindest-Score"-Slider entfernt (war redundant + Ursache des Konflikts)
> - `Filter.applyToLocations()` ergänzt; überall im Locations-Render-Pfad verdrahtet
> - `App.nav('locations')`, `Locations.load()`, `Locations.filter()` wenden Filter an

### ~~BUG-09 · Inkonsistente Marker-Symbole zwischen FOV-Karte und Edit-Karte~~ `[x]`
> **Problem:** Die Karte in der Sektion „📐 Karte & Blickwinkel" (US-58) verwendet andere Marker als die Edit-Karte (US-60) und die „Neue Location"-Karte (US-56). Dadurch ist unklar, welcher Pin den Fotografen-Standort und welcher das Motiv markiert.
>
> **Ist-Zustand:**
> - **Edit-Karte / AddLocation:** Fotograf = oranges `circleMarker` + oranges `L.divIcon` (Kreis mit weißem Rand); Motiv = Standard-Leaflet-Pin (blau)
> - **FOV-Karte (US-58):** Fotograf = oranges `circleMarker` #FF6600; Motiv = goldenes `circleMarker` #E8A020
>
> **Ziel:** Alle Leaflet-Karten der App verwenden einheitliche, klar unterscheidbare Marker für Fotograf-Standort und Motiv-Standort.
>
> **Akzeptanzkriterien:**
> - Definierte Marker-Spec (z. B. Fotograf = 📷-Icon oder orange Raute, Motiv = 🎯-Icon oder gold Stern) in einem zentralen `MapMarkers`-Objekt oder CSS-Klassen
> - FOV-Karte, Edit-Karte (LocationDetail), AddLocation-Karte – alle nutzen dieselben Marker-Definitionen
> - Marker sind groß genug für Fingertip-Interaktion (≥ 22 px) und klar beschriftet oder mit Legende versehen
> - Visuell sofort erkennbar: kein weiteres Nachdenken nötig, welcher Pin was bedeutet

### ~~BUG-01 · Brennweite-Empfehlung passt nicht zur Motiventfernung~~ `[x]`
> **Problem:** Die vorgeschlagenen Brennweiten entsprechen nicht der tatsächlichen Entfernung zwischen Beobachter und Motiv. Beispiel: Schloss Babelsberg vom Pfingstberg → Empfehlung 50 mm, obwohl die Distanz ein Teleobjektiv erfordern würde.
>
> **Ursache (Hypothese):** Die Kamera-Hints werden vermutlich pauschal pro Event-Typ vergeben und berücksichtigen nicht die in der Location hinterlegte `distance_m` zwischen Observer und Subject.
>
> **Akzeptanzkriterien:**
> - Brennweiten-Empfehlung wird aus der tatsächlichen Motiventfernung (`distance_m`) berechnet
> - Annäherungswerte: < 500 m → Weitwinkel/Standard, 500 m–2 km → Standard/Tele, > 2 km → Tele/Supertele
> - Betroffene Datei: `calculations/opportunity.py` (Camera Hints Generierung)
> - Verifizierung am Beispiel Pfingstberg → Schloss Babelsberg (Distanz prüfen, Empfehlung plausibel?)
> - **Filter:** Im kombinierten Filter-Sheet wird ein Brennweiten-Slider ergänzt, mit dem der User Chancen nach minimaler/maximaler empfohlener Brennweite filtern kann (z. B. „nur Chancen mit ≥ 200 mm")
> - **Verifikation:** Bei einer negativen Standortverifikation erscheint „Brennweite falsch" als auswählbare Problemkategorie, damit fehlerhafte Brennweitenangaben gezielt gemeldet und korrigiert werden können

---

## 🔴 Hoch – Kern-Features


### ~~US-32 · Kombiniertes Filter-System~~ `[x]`
> **Als Fotograf** möchte ich den Feed nach mehreren Kriterien gleichzeitig filtern können, um nur die für mich relevanten Events zu sehen.
>
> **UI:** Filter-Icon links neben dem Refresh-Button im oberen Header → öffnet ein Modal/Bottom-Sheet mit allen Filtergruppen. Aktive Filter werden als Badge-Zahl am Filter-Icon angezeigt. „Alle zurücksetzen"-Button im Modal.
>
> **Filtergruppen (kombinierbar):**
> - **Eventtyp** – Vollmond · Neumond · Blutmond · Goldene Stunde · Blaue Stunde · Milchstraße · Mondaufgang · Monduntergang · Sonnenaufgang · Sonnenuntergang · Sonnenfinsternis · Mondfinsternis · Komet · Meteoritenschauer (Mehrfachauswahl)
> - **Schwierigkeitsgrad** – Leicht / Mittel / Schwer (Mehrfachauswahl; 1 = öffentlich, 2 = Planung nötig, 3 = Genehmigung)
> - **Mindest-Score** – Slider ≥ 60 / ≥ 75 / ≥ 90 % (wirkt auf Gesamt-Score)
> - **Entfernung** – GPS-basiert: < 5 / 15 / 30 / 50 km von meinem Standort (mit Erlaubnis-Dialog)
> - **Verifikationsstatus** – Alle / Nur geprüfte Locations / Noch nicht geprüft / Mit gemeldeten Problemen
>
> **Akzeptanzkriterien:**
> - Filter-State bleibt nach App-Reload erhalten (localStorage)
> - Entfernung auf Event-Card sichtbar, wenn GPS-Filter aktiv
> - Anzahl aktiver Filter als Badge am Filter-Button
>
> *Ersetzt und vereint: US-18 (Umkreissuche), US-19 (Eventtyp-Filter), US-20 (Schwierigkeitsgrad-Filter), US-27 (Wahrscheinlichkeits-Filter)*

### ~~US-53 · Live-Textsuche im Feed~~ `[x]`
> **Als Fotograf** möchte ich im Feed nach Locations oder Chancen suchen können, indem ich Text eingebe – die Liste filtert sich dabei live beim Tippen, sodass ich schnell zu einem bekannten Standort navigieren kann.
>
> **UI:**
> - Such-Icon im Header (Lupe) → tippt man darauf, erscheint ein Eingabefeld das die gesamte Breite einnimmt (Header-Titel verschwindet, Abbrechen-Button rechts)
> - Während der Eingabe: Liste zeigt nur noch Events, deren Location-Name die getippten Zeichen enthält (Substring-Match, case-insensitive)
> - Treffer: Location-Name-Text wird nicht highlighted (Keep-It-Simple für v1)
> - Bei leerem Feld oder Abbrechen: volle ungefilterte Liste (inkl. aktive Filter bleiben erhalten)
> - Suche und Filter-Sheet sind kombinierbar: beide aktiv → AND-Verknüpfung
>
> **Akzeptanzkriterien:**
> - Suche reagiert sofort beim Tippen (kein Debounce nötig bei clientseitigem Filter)
> - Schließen per Abbrechen-Button oder Escape-Taste
> - Suchfeld-State wird NICHT in localStorage persistiert (immer leer beim App-Start)
> - Badge am Filter-Icon ändert sich nicht durch aktive Suche (Suche ≠ Filter)

### US-56 · Location-Capture: Koordinaten per Text-Eingabe erfassen `[x]`
> **Als App-Host** möchte ich beim Erfassen neuer Locations GPS-Koordinaten auch direkt per Text eingeben oder einfügen können, damit ich bekannte Koordinaten (z.B. aus Google Maps, Komoot oder einer Recherche) ohne Karten-Klick übernehmen kann.
>
> **Hintergrund:** US-05 ✅ implementiert Karten-Klick + GPS-Button als Eingabemethoden. Für Koordinaten aus externen Quellen (z.B. kopierter Dezimalgrad-String „52.51234, 13.40123") fehlt ein direktes Eingabefeld.
>
> **Akzeptanzkriterien:**
> - Im „Neue Location"-Formular: Textfelder für Breiten- und Längengrad direkt neben den Karten-Buttons (Fotograf-Standort + Motiv)
> - Eingabe akzeptiert Dezimalgrad (z.B. `52.51234`) und DMS-Format (z.B. `52°30'44.4"N`) – letzteres wird auto-konvertiert
> - Clipboard-Paste-Button (`📋`): liest `navigator.clipboard.readText()`, parst `lat, lon`-Paare aus bekannten Formaten (Google Maps, Apple Maps, DMS), und setzt Observer oder Subject direkt
> - Nach manueller Eingabe: Karten-Marker und Verbindungslinie werden aktualisiert (gleiche Logik wie Karten-Klick)
> - Validierung: ungültige Koordinaten (außerhalb ±90°/±180°) zeigen Inline-Fehlermeldung
> - Kein Backend-Änderungsbedarf – rein frontend

### ~~US-61 · Navigation: Event-Detail → Location-Detail~~ `[x]`
> **Als User** möchte ich aus der Event-Detailansicht direkt zur Detailansicht der zugehörigen Location wechseln können, um dort Informationen nachzuschlagen oder Bearbeitungen vorzunehmen, ohne die App neu navigieren zu müssen.
>
> **Akzeptanzkriterien:**
> - Im Event-Detail-Sheet: Button „📍 Zur Location" neben oder unter dem Location-Namen
> - Klick: Event-Detail schließt, Location-Detail der zugehörigen Location öffnet sich
> - Rücknavigation: einfaches Schließen des Location-Details (kein dedizierter Zurück-Button nötig)
> - Funktioniert für alle Location-Typen (custom_ und Standard-Locations)
> - Kein Backend-Call nötig — `location_id` ist in jedem Event-Objekt vorhanden

### ~~US-60 · Koordinaten-Bearbeitung in Location/Event Detail + einheitliches Eingabefeld~~ `[x]`
> **Als Fotograf** möchte ich Fotograf-Standort und Motiv-Standort sowohl in bestehenden Locations als auch beim Anlegen neuer Locations direkt auf der Karte oder über ein einheitliches Koordinatenfeld bearbeiten können.
>
> **Akzeptanzkriterien:**
>
> **Bearbeitung in Location-Detail (alle Locations):**
> - ✏️-Button aktiviert Bearbeitungsmodus für Koordinaten (gilt für **alle** Locations, nicht nur custom_)
> - Im Bearbeitungsmodus: Karte erscheint (Leaflet, Satellit), Fotograf-Pin und Motiv-Pin sind verschiebbar (Drag-and-Drop)
> - Koordinaten auch direkt per kombiniertem Eingabefeld bearbeitbar (s.u.)
> - Separate „Speichern"-Aktion; Abbrechen verwirft Änderungen
> - Backend: PATCH-Endpoint für `observer_lat/lon` und `subject_lat/lon` für alle Location-IDs; Nicht-Custom-Locations werden in `location_overrides.json` persistiert, die beim Start geladen und auf die Basis-Locations angewendet werden
> - Nach Speichern: Location-Update-Routine — distance, bearing, azimuth_range, focal_length neu berechnen
>
> **Vereinheitlichtes Koordinatenfeld (Refactor US-56):**
> - Ein einzelnes Textfeld statt zwei getrennter Felder für Breite/Länge
> - Erkannte Formate: `52.40747, 13.09279` · `52°24'26.9"N, 13°05'33.8"E` · `52.40747° N, 13.09279° O` · vollständige Google-Maps/Apple-Maps/Komoot-Strings
> - Nach Parse: Karten-Marker springt auf eingegebene Position, Inline-Validierung bei ungültigen Werten
> - Gilt in **AddLocation** (löst 2-Felder-Eingabe ab) sowie im **Bearbeitungsmodus** des Location-Details

### ~~US-59 · Aufklappbare Sektionen in Detail-Ansichten~~ `[x]`
> **Als Fotograf** möchte ich die Informationssektionen in Location- und Event-Detailansichten einzeln auf- und zuklappen können, damit ich mich auf die für mich relevanten Informationen konzentrieren kann ohne von der Gesamtmenge überfordert zu werden.
>
> **Akzeptanzkriterien:**
> - Alle benannten Sektionen in Event-Detail (Standort & Topographie, Kompositions-Analyse, Wetter, Kamera-Hints) und Location-Detail (Astronomie-Möglichkeiten, Verifikations-Timeline, GPS-Daten) haben einen Toggle (Chevron ▾/▸ rechts in der Sektionsüberschrift)
> - **Default:** Alle Sektionen zugeklappt — nur Überschriften sichtbar; Ausnahme: Score-Leiste und Haupt-Infos bleiben offen
> - Zustand pro Sektion persistent in `localStorage` (`sectionStates`)
> - Toggle-Animation: smooth max-height-Transition (200ms)
> - Bestehende Sektionen inhaltlich unverändert

### ~~US-58 · Kamera-Sichtfeld-Visualisierung auf Karte~~ `[x]`
> **Als Fotograf** möchte ich in der Location- oder Chancen-Detailansicht auf einer Karte den Fotografen-Standort und den Motiv-Standort sehen, mein Kamera-Setup konfigurieren (Sensor, Brennweite, Format) und daraus den Blickwinkel als Kegel auf der Karte angezeigt bekommen, damit ich die mögliche Bildkomposition bereits am Schreibtisch einschätzen kann.
>
> **Akzeptanzkriterien:**
> - Neue Sektion „📐 Karte & Blickwinkel" in Location-Detail und Event-Detail (aufklappbar per US-59)
> - Karte zeigt: Fotograf-Pin (orange), Motiv-Pin (gold), Sichtachse (Linie), FOV-Kegel (transparentes Dreieck bis zur Motiventfernung)
> - **Kamera-Konfigurationspanel** (persistent in localStorage `cameraProfile`):
>   - Sensorformat: Vollformat (36×24mm), APS-C Canon (22.3×14.9mm), APS-C Sony/Nikon (23.5×15.6mm), Micro Four Thirds (17.3×13mm), 1"-Sensor (13.2×8.8mm)
>   - Brennweite: numerisches Eingabefeld, Wertebereich **8–1200 mm**
>   - Ausrichtung: Querformat / Hochformat
> - FOV-Berechnung: `FOV_h = 2 × arctan(Sensorbreite / (2 × Brennweite))` horizontal; Kegel auf Karte bis Motivdistanz
> - Anzeige: Öffnungswinkel in Grad (z.B. „FOV: 8,2°") + Bildbreite am Motiv in Metern
> - Karte: Leaflet.js Satellit, Zoom-Controls
> - Kein Backend-Call nötig (Frontend-Berechnung auf bestehenden Locationdaten)

### US-57 · Alignment-Qualitätsfilter: 2°-Schärfezone `[ ]`
> **Als Fotograf** möchte ich, dass nur Himmelsereignisse im Feed erscheinen, die sich innerhalb eines definierten Toleranzbereichs (Azimuth + Höhe) der Sichtachse zum Motiv befinden, damit ausschließlich fotografisch relevante Alignments angezeigt werden.
>
> **Hintergrund:** US-37 ✅ berechnet und zeigt `azimuth_delta_deg` und `altitude_delta_deg` bereits an. Diese Story nutzt diese Werte als Hard-Filter in der Event-Generierung.
>
> **Akzeptanzkriterien:**
> - In `precompute.py` → `_composition_analysis()`: Events mit `|azimuth_delta_deg| > ALIGNMENT_TOLERANCE_DEG` ODER `|altitude_delta_deg| > ALIGNMENT_TOLERANCE_DEG` werden nicht als Feed-Event erzeugt
> - Default-Schwellwert: `ALIGNMENT_TOLERANCE_DEG = 2.0` als Konstante in `precompute.py` (konfigurierbar)
> - Ausnahmen (kein Azimuth-Filter): Goldene Stunde, Blaue Stunde, Milchstraße, Meteoritenschauer, Finsternisse
> - Jahreskalender: gleiche Filterung
> - `ALGORITHM_VERSION` erhöhen → inkrementeller Cache wird neu berechnet beim nächsten `--feed-only`
> - Frontend: US-37-Labels bleiben unverändert; durch den Filter erscheinen ☁️-Events (> 3°) nicht mehr im Feed

### US-40 · Feed-Qualität: Tägliche Routine-Events ausblenden `[ ]`
> **Als Fotograf** möchte ich im Chancen-Tab nicht täglich auf Goldene Stunde und Blaue Stunde hingewiesen werden, da diese jeden Tag auftreten und keine besonderen Ereignisse wie Mondaufgang oder Vollmond sind.
>
> **Hintergrund:** US-03 hat Goldene & Blaue Stunde als technische Events eingeführt – diese Zeitfenster bleiben für den Tageszeit-Filter und die Detail-Anzeige erhalten. Im Feed-Tab sollen sie aber standardmäßig nicht als eigenständige Chancen erscheinen.
>
> **Akzeptanzkriterien:**
> - Goldene Stunde (Morgen/Abend) und Blaue Stunde werden im Feed-Tab standardmäßig nicht angezeigt
> - Nutzer können sie über den Eventtyp-Filter explizit einblenden (opt-in)
> - Tageszeit-Filter und Detail-Anzeige (Golden/Blue Hour Zeitfenster) bleiben unberührt
> - Jahreskalender-Tab: Routine-Events dort ebenfalls ausblenden oder klar als Dauerläufer kennzeichnen
>
> *Differenziert von US-03 ✅ (technische Berechnung bleibt) und US-36 (betrifft Alignment-Events, nicht Routine-Events)*

### US-33 · Developer Tool: Locationscout Import-Management
> **Als App-Host** möchte ich neue Locations aus Locationscout-Listen komfortabel importieren und bereits abgelehnte Spots dauerhaft ausschließen können.
>
> **Akzeptanzkriterien:**
> - Backend-Endpoint oder CLI-Tool zum Import aus bekannten Locationscout-Listen (gespeicherte URLs)
> - Import via Link: beliebige Locationscout-URL angeben → automatischer Scan + GPS-Extraktion
> - Abgelehnte Locations werden in einer Exclusion-List gespeichert und nicht erneut vorgeschlagen
> - Neue Kandidaten werden als „Import-Vorschlag" markiert und zur Prüfung angezeigt
> - Deduplizierung gegen bestehende Locations (< 300m Abstand → Warnung)
>
> *Erweiterung von US-12 (einmaliger Import, erledigt) → jetzt als dauerhaftes Management-Tool*

### US-34 · Job-Orchestrierung & Incremental Updates `[~]`
> **Als App-Host** möchte ich, dass alle Hintergrund-Jobs effizient und bedarfsgesteuert laufen und ich sie gezielt manuell anstoßen kann, um Rechenzeit zu sparen und stets aktuelle Daten zu haben.
>
> **Job-Typen und Strategien:**
> - **Jahreskalender (365 Tage):** Wird nur neu berechnet wenn Daten fehlen, bei Erstinstallation, bei erkannten Fehlern oder auf explizite Anforderung. Keine tägliche Neuberechnung.
> - **14-Tage Astronomy-Feed:** Täglich früh morgens (z.B. 05:30 Uhr) neu berechnet. Nur Astronomie, kein Wetter.
> - **3-Tage Wetter-integrierter Plan (Rolling Forecast):** Kombiniert Astronomy-Feed mit Open-Meteo-Wetterdaten. Aktualisierungsfrequenz steigt je näher das Event kommt: T-14 bis T-4 → 1× täglich; T-3 bis T-1 → alle 6 Stunden; T-0 bis T+12h → stündlich. Ermöglicht präzise Go/No-Go-Entscheidungen.
> - **Locationscout-Check:** Regelmäßige Prüfung bekannter Listen auf neue Locations → Kandidaten vorschlagen, abgelehnte nicht erneut anzeigen (koordiniert mit US-33).
> - **Elevation-Cache:** Nur für neue Locations ohne Eintrag fetchen, nie überschreiben.
>
> **Akzeptanzkriterien:**
> - Alle Jobs sind einzeln auslösbar (CLI oder Admin-Endpoint)
> - **PWA-Refresh-Menü:** Der Refresh-Button in der App öffnet ein Untermenü mit einzeln auslösbaren Aktionen: Wetter aktualisieren · 14-Tage-Feed neu berechnen · Jahreskalender neu berechnen · Locationscout-Scan starten. Jobs können parallel angestoßen werden; Status (läuft / fertig / Fehler) wird inline angezeigt.
> - Job-Status und letzte Laufzeit sind einsehbar
> - Fehlgeschlagene Jobs werden geloggt und lösen Observability-Alert aus (koordiniert mit US-38)

### US-38 · Observability & Self-Healing
> **Als App-Host** möchte ich die problemlose Funktionsweise der App überwachen und Fehler sofort identifizieren, damit ich die User Experience jederzeit sicherstellen kann.
>
> **Akzeptanzkriterien:**
> - Health-Check-Endpoint `/health` mit Status aller Subsysteme (Backend, Cache, Jobs, Wetter-API)
> - Strukturiertes Logging aller Jobs und API-Calls (Zeitstempel, Dauer, Status, Fehlercode)
> - Automatische Fehlererkennung: fehlerhafte Jobs werden klassifiziert (Timeout / API-Fehler / Datenfehler)
> - Bei erkanntem Fehler: automatisch generierter Lösungsvorschlag als Spec (Beschreibung + betroffene Dateien + empfohlene Maßnahme) – kein automatisches Implementieren
> - Alert-Mechanismus (Log-Eintrag, optional: lokale Push-Notification oder E-Mail)
> - Dashboard oder CLI-Befehl zur Übersicht aller Job-Läufe und Fehler der letzten 7 Tage
>
> *Vereint: Traceability (Fehlererkennung + Lösungsspecs) + Observability (Monitoring + Alerts)*

### US-39 · Resilient Deployment / Rollback
> **Als App-Host** möchte ich bei der Einführung neuer Features oder Fixes jederzeit auf die letzte funktionierende Version zurückrollen können, damit nie die gesamte App verloren geht.
>
> **Akzeptanzkriterien:**
> - Git-basiertes Versioning: jeder Deploy-Stand ist als Tag oder Branch nachvollziehbar
> - Rollback-Anleitung dokumentiert (welcher Befehl, welcher Stand)
> - Cache-Kompatibilität: Rollback bricht keine bestehenden JSON-Caches (oder migriert sie)
> - Optionale Datensicherung vor jedem Precompute-Lauf (Snapshot der cache/-Dateien)

### TASK-13 · PWA auf iPhone: Öffentliches Hosting & Remote-Zugriff `[ ]`
> **Als App-Host** möchte ich die App auf meinem iPhone 14 Pro nutzen können — von überall, nicht nur im Heimnetz — ohne eine native iOS-App zu bauen.
>
> **Ausgangslage:** App läuft aktuell auf `localhost:8000` (Mac). Für mobilen Zugriff braucht es HTTPS (Pflicht für PWA/Service Worker auf iOS) und eine öffentlich erreichbare URL.
>
> **Konzept & Hosting-Optionen (zu evaluieren):**
>
> **Option A – Cloudflare Tunnel (empfohlen für Einstieg):**
> - `cloudflared tunnel` auf dem Mac: tunnelt localhost → öffentliche HTTPS-URL ohne Portweiterleitung
> - Kostenlos, SSL automatisch, funktioniert auch hinter NAT/Router
> - Nachteil: Mac muss laufen; bei Neustart Tunnel-Daemon neu starten
>
> **Option B – VPS (Hetzner CX11, ~4 €/Monat):**
> - Eigener Linux-Server, App in Docker, Caddy als Reverse Proxy (automatisches Let's Encrypt SSL)
> - Eigene Domain (`fotoalert.yourname.de`) → DNS auf VPS
> - Vorteil: 24/7 verfügbar, unabhängig vom Mac; empfohlen wenn Nutzung täglich/unterwegs
>
> **Gemeinsame Anforderungen (beide Optionen):**
> - FastAPI Backend über HTTPS erreichbar
> - Service Worker funktioniert auf iPhone Safari (HTTPS ist Voraussetzung)
> - Hintergrund-Jobs (precompute Cron) laufen automatisch beim Systemstart
> - Persistente Daten (`custom_locations.json`, `cache/`, `location_overrides.json`) überleben Restarts
> - Push Notifications funktionieren auf iPhone (VAPID-Setup geprüft)
> - Basis-Authentifizierung (HTTP Basic Auth oder IP-Whitelist) empfohlen — App enthält persönliche Spots
>
> **Akzeptanzkriterien:**
> - App über HTTPS-URL auf iPhone Safari aufrufbar
> - „Zum Homescreen hinzufügen" → App startet ohne Safari-Chrome (PWA-Modus)
> - Alle Features funktionieren mobil: Feed, Kalender, Locations, Filter, Location-Detail, Edit
> - Offline-Fallback (Service Worker) funktioniert
> - Cron-Job läuft täglich 05:30 Uhr ohne manuelle Intervention
> - Konzept-Dokument: Wahl der Hosting-Option + Setup-Anleitung (Schritt-für-Schritt)
>
> **Abhängigkeiten:** TASK-14 hängt von diesem Task ab (CI/CD braucht Deployment-Ziel)

### TASK-14 · Automatische Deployment Pipeline `[ ]`
> **Als App-Host** möchte ich Code-Änderungen mit minimalem manuellen Aufwand veröffentlichen können — ohne fehlerträchtige manuelle Schritte wie SW-Version bumpen, Dateien kopieren oder Server neustarten.
>
> **Ziel:** Ein `git push` (oder ein einzelner CLI-Befehl) deployt die neue Version vollautomatisch auf den Server, bumpt die SW-Cache-Version, startet den Service neu und prüft die Verfügbarkeit.
>
> **Akzeptanzkriterien:**
>
> **Deployment-Trigger:**
> - `git push origin main` → automatischer Deploy (via GitHub Actions oder lokales Deploy-Script)
> - Alternativ: `./deploy.sh` als einzelner Befehl vom lokalen Mac
>
> **Deployment-Schritte (automatisiert):**
> 1. `git pull` auf Server
> 2. `CACHE_NAME` in `sw.js` automatisch inkrementiert (z.B. via `sed` mit Versions-Tag aus Git)
> 3. Python-Dependencies prüfen (`pip install -r requirements.txt`)
> 4. FastAPI-Prozess graceful restart (systemd `reload` oder `kill -HUP`)
> 5. Health-Check: GET `/health` → 200 OK erwartet
> 6. Rollback bei Fehler: letzter Git-Stand automatisch wiederhergestellt
>
> **Datensicherheit:**
> - Persistent Files (`custom_locations.json`, `cache/`, `location_overrides.json`) werden NICHT überschrieben
> - Umgebungsvariablen (falls vorhanden) in `.env`-Datei außerhalb Git
>
> **Rollback:**
> - `./rollback.sh` (oder `git revert + deploy`) stellt vorherigen Stand her in < 2 Min.
>
> **Dokumentation:**
> - README-Sektion „Deployment" mit vollständiger Anleitung
> - Welche Dateien auf dem Server liegen (persistent vs. deploybar)
>
> **Abhängigkeiten:** TASK-13 (braucht Deploy-Ziel), US-39 (Rollback-Strategie baut hierauf auf)


### TASK-15 · Jahreskalender-Cron-Zeit auf 0:01 Uhr ändern `[~]`
> **Als App-Host** möchte ich den Cron-Job für die Jahres- und 14-Tage-Kalenderberechnung auf 0:01 Uhr ändern, damit die Daten um Mitternacht aktualisiert werden (statt 5:30 Uhr morgens).
>
> **Akzeptanzkriterien:**
> - Cron-Ausdruck: `30 5 * * *` → `1 0 * * *`
> - Kein Konflikt mit anderen Cron-Jobs (US-34 Rolling-Forecast)
> - Nach Änderung: Cron-Lauf um 0:01 Uhr im Log nachweisbar
>
> **Abhängigkeiten:** BUG-14 (möglicherweise verwandter Fehler), US-34[~]

### US-04 · Kalender-Integration für geplante Fotowalks
> **Als Fotograf** möchte ich mit einem Tap einen Kalender-Eintrag für ein geplantes Foto-Event erstellen.
>
> **Akzeptanzkriterien:**
> - „In Kalender eintragen"-Button in der Detail-Ansicht
> - Eintrag enthält: Titel, Ort (GPS), Zeitfenster, Kamera-Hinweise
> - Web: `.ics`-Datei Download (Apple Calendar, Google Calendar)
> - Erinnerung 30/60/120 Min. vorher

### US-06 · Gespeicherte Locations verwalten
> **Als Fotograf** möchte ich meine selbst erfassten Locations bearbeiten, mit Notizen versehen und löschen können.
>
> **Akzeptanzkriterien:**
> - Eigene Locations als „Meine Spots" markiert
> - Bearbeiten: Name, Beschreibung, Höhe
> - Löschen mit Bestätigung
> - Export als JSON

### US-62 · Höhenkorrektur Fotografenstandort (Dach, Etage) `[ ]`
> **Als Fotograf** möchte ich angeben können, dass ich mich nicht auf Bodenniveau befinde (z. B. auf einem Dach oder in der 20. Etage eines Hochhauses), damit die Triangulation und Kompositions-Analyse korrekte Winkel für meine tatsächliche Augenhöhe berechnet.
>
> **Hintergrund:** `observer_elevation_m` wird via OpenTopoData aus dem Geländemodell am GPS-Standort bezogen. Ein Fotograf auf dem Dach eines 60 m hohen Gebäudes hat eine effektive Augenhöhe von `terrain_elevation_m + 60 m`. Die Formel für `observer_elevation_angle_deg = arctan((subject_elevation_m + subject_height_m − observer_elevation_m) / distance_m)` wird dadurch signifikant beeinflusst — und damit alle davon abhängigen Berechnungen (FOV-Karte, Kompositions-Analyse, possible_bodies).
>
> **Differenzierung zu US-60 ✅:** US-60 editiert Lat/Lon-Koordinaten. Diese Story ergänzt den vertikalen Offset am Beobachterstandort.
>
> **Akzeptanzkriterien:**
> - Neues Feld `observer_floor_height_m` (Typ: float, Default: 0.0) in Location-Datenmodell und `custom_locations.json` / `location_overrides.json`
> - Im Location-Detail → Bearbeitungsmodus (Erweiterung des US-60-Edit-Flows): Eingabefeld „Höhe über Gelände (m)" mit Hilfetext „z. B. 60 m für Dach eines 6-Geschossers"
> - Validierung: Wert ≥ 0, numerisch
> - Backend: PATCH `/locations/{id}` um `observer_floor_height_m` erweitern; Nicht-Custom-Locations via `location_overrides.json`
> - In `precompute.py`: effektive Observer-Höhe = `observer_elevation_m + (observer_floor_height_m or 0.0)` in allen Berechnungen
> - Nach Speichern: Hintergrund-Recompute via TASK-12-Mechanismus (berührt Kompositions-Analyse, FOV-Kegel, possible_bodies)
> - Anzeige im Location-Detail (GPS-Sektion): „Geländehöhe: 45 m + 60 m Gebäude = eff. 105 m NN"
> - Gilt für eigene Locations UND Standard-Locations (via location_overrides.json, identisches Muster wie US-60)
>
> **Abhängigkeiten:** US-60 ✅, TASK-12 ✅


### US-64 · Live Astro-Visualisierung (PhotoPills-like) `[ ]`
> **Als Fotograf** möchte ich in Echtzeit sehen, wo sich Sonne und Mond am Himmel befinden, und diese Position relativ zu meinem Fotostandort und Motiv visualisiert bekommen.
>
> **Hintergrund:** FotoAlert hat Skyfield-Engine und Location-Paare. Diese Story ergänzt einen Live-Modus der die aktuelle Himmelsposition anzeigt und mit Locationdaten überlagert.
>
> **Akzeptanzkriterien:**
> - Neuer API-Endpoint `GET /astro/live?location_id=X&ts=ISO8601`: liefert Azimut + Elevation für Sonne, Mond (und Milchstraßenzentrum) zum angegebenen Timestamp
> - Frontend: Fotograf-Pin + Motiv-Pin auf Karte (aus Location-Daten); visuelle Bogenbahn Sonne/Mond überlagert
> - Live-Modus: automatische Aktualisierung alle 60 Sekunden; Uhrzeit-Slider zum Scrubben durch den Tag
> - Wenn Azimut des Himmelsobjekts innerhalb `ideal_azimuth_range`: grünes Highlight / Alignment-Indikator
> - Keine AR, kein Exif – reine Karten- + Winkel-Visualisierung
>
> **Sequenzierung:**
> ```
> US-35[x] (possible_bodies) ──┐
> US-37[x] (azimuth_delta)   ──┴─→ US-64 (Live Astro)
> ```
>
> **Abhängigkeiten:** US-35[x], US-37[x]

### US-65 · Automatisches Backup der App-Daten `[ ]`
> **Als App-Host** möchte ich, dass wichtige App-Daten automatisch gesichert werden, damit bei Serverfehlern oder unbeabsichtigtem Überschreiben kein Datenverlust entsteht.
>
> **Scope:** Backup persistenter Nutzdaten (Code liegt in Git).
>
> **Akzeptanzkriterien:**
> - **Quellen:** `custom_locations.json`, `location_overrides.json` (optional: `cache/` als Snapshot)
> - **Trigger:** täglich via Cron (0:00 Uhr) + change-getriggert nach jedem PATCH/POST/DELETE auf Location-Endpoints
> - **Retention:** 7 Versionen rolling; älteste Version wird automatisch gelöscht
> - **Speicherort:** `backup/YYYY-MM-DD_HHmm/` auf Server, außerhalb Git-Repo
> - **Restore:** `./restore.sh YYYY-MM-DD_HHmm` stellt Backup-Stand wieder her
> - Logeintrag bei erfolgreichem Backup; Alert wenn Backup seit >25h ausgeblieben
>
> **Abhängigkeiten:** TASK-14, TASK-15 (Cron-Koordination)

### US-66 · Host-Login für exklusive Funktionen `[ ]`
> **Als App-Host** möchte ich mich mit einem Passwort in der App identifizieren können, damit ich Zugang zu administrativen Funktionen erhalte (Location-Bearbeitung, Debug-Info), die für normale Nutzer nicht sichtbar sind.
>
> **Akzeptanzkriterien:**
> - Login-Dialog (Modal) erreichbar über verstecktes Trigger-Element (z.B. Mehrfach-Tap auf App-Header)
> - Eingabe: Passwort-Feld (kein Username)
> - Backend: `POST /auth/host` – Passwort-Vergleich via `bcrypt.checkpw()` gegen serverseitig gespeicherten Hash
> - Bei Erfolg: Session-Token (JWT, 24h Laufzeit) im HTTP-only Cookie; Frontend erkennt Auth-Status
> - **Passwort-Speicherung im Client:** nach Nutzer-Zustimmung sicherer Systemspeicher: Apple Keychain (iOS/macOS), Android Keystore, Windows Credential Manager – über Web Credential Management API (`navigator.credentials`) wo verfügbar
> - Host-Modus: Admin-Badge im Header, Location-Bearbeitungs-Buttons sichtbar, Debug-Overlay erreichbar
> - Logout: Button im Host-Menü; Session-Token gelöscht
>
> **Sequenzierung:**
> ```
> US-66 (Host-Login) ──→ US-68 (Host-Approval Workflow)
> US-63[x] (Location-Edit) ←── erweitert durch US-66 (nur Host sichtbar)
> ```
>
> **Abhängigkeiten:** keine (eigenständig implementierbar)

### US-67 · Chancendetails: Azimut und Höhe relativ zur Motivspitze `[ ]`
> **Als Fotograf** möchte ich bei einem Alignment-Event in verständlicher Sprache lesen, wo das Himmelsobjekt relativ zu meinem Motiv erscheint – z.B. „Mond 3° links neben dem Kirchturm, 5° darüber".
>
> **Hintergrund:** US-37[x] berechnet `azimuth_delta_deg` und `altitude_delta_deg`. Diese Rohwerte liegen im Cache vor, werden aber nur als Zahlen angezeigt.
>
> **Akzeptanzkriterien:**
> - Im Event-Detail-Sheet: neue Sektion „Himmelsposition" mit Beschreibungstext:
>   - `azimuth_delta < 0` → „links", `> 0` → „rechts"; `altitude_delta > 0` → „darüber", `< 0` → „darunter"
>   - Schwellwerte: < 0.5° → „nahezu exakt auf dem Motiv"; 0.5–2° → „leicht"; > 5° → „deutlich"
>   - Absoluter Azimut + Elevation als Sekundärinfo (für erfahrene Nutzer)
> - Nur bei Alignment-Events (Mond-Alignment, Sonnen-Alignment); nicht bei Goldene Stunde, Mondaufgang etc.
> - Immer relativ zum Motiv (nicht zur Kamera oder zum Norden)
>
> **Abhängigkeiten:** US-37[x]

### US-68 · Host-Approval Workflow für Location-Änderungen `[ ]`
> **Als normaler Nutzer** möchte ich Änderungsvorschläge für eine Location einreichen können, die erst nach Bestätigung durch den Host sichtbar werden.
>
> **Hintergrund:** US-63[x] erlaubt vollständiges Bearbeiten. Diese Story fügt einen Review-Gate ein: Änderungen von Nicht-Host-Nutzern werden als Vorschläge gespeichert.
>
> **Akzeptanzkriterien:**
> - Nicht-Host-Nutzer sehen „Änderung vorschlagen"-Button (statt direktem Edit)
> - Vorschlag wird als `pending_override` in `location_overrides.json` gespeichert (Status: `pending`)
> - Host-Dashboard (nach US-66-Login): Liste aller offenen Vorschläge mit Diff-Ansicht (alt ↔ neu)
> - Host-Aktionen: „Annehmen" (Status `approved`, Wert übernommen) oder „Ablehnen" (Status `rejected`)
> - Nach Annahme: Hintergrund-Recompute via TASK-12-Mechanismus
> - Nicht-Host-Nutzer sehen an betroffener Location Hinweis „Vorschlag ausstehend"
>
> **Sequenzierung:**
> ```
> US-63[x] (Location-Edit-UI) ──┐
> US-66 (Host-Login Auth)      ──┴─→ US-68 (Approval Workflow)
> TASK-12[x] (Auto-Recompute) ──────→ US-68 (nach Approval)
> ```
>
> **Abhängigkeiten:** US-63[x], US-66, TASK-12[x]

### US-69 · Kartenansicht auf aktuellen GPS-Standort zentrieren `[ ]`
> **Als Fotograf vor Ort** möchte ich die Kartenansicht mit einem Tap auf meinen GPS-Standort zentrieren, damit ich schnell sehe, welche Fotostandorte in meiner Nähe liegen.
>
> **Akzeptanzkriterien:**
> - „Mein Standort"-Button (Standort-Icon) in der Kartenansicht
> - Tap: Karte zentriert auf aktuellen GPS-Standort (`navigator.geolocation.getCurrentPosition`), Zoom-Level 13
> - GPS-Marker: blauer Puls-Punkt auf aktueller Position
> - Wenn GPS-Berechtigung nicht erteilt: Anfrage; bei Ablehnung Toast „GPS-Zugriff nicht erlaubt"
> - GPS-Koordinaten werden NICHT gespeichert (kein Tracking)
> - GPS-Logik orientiert sich an US-32[x] (Standortnähe-Filter)
>
> **Abhängigkeiten:** US-32[x]

### US-17 · Lieblingslocations (Favorites)
> **Als Fotograf** möchte ich Locations als Favoriten markieren können, **damit ich** meinen persönlichen Kern-Spotpool schnell filtern kann.
>
> **Akzeptanzkriterien:**
> - Herz-/Stern-Icon auf jeder Location und jedem Event-Card
> - Filter-Chip „Nur Favoriten" im Feed (integriert in US-32 Filter-System)
> - Favoriten werden lokal gespeichert (localStorage / PWA)
> - Favoriten-Tab oder Section im Locations-Menü

### US-26 · Sprachumschaltung DE / EN
> **Als Fotograf** möchte ich die App zwischen Deutsch und Englisch umschalten können, **damit ich** sie auch mit internationalen Fotografie-Gästen nutzen kann.
>
> **Akzeptanzkriterien:**
> - Sprach-Toggle in den Einstellungen (DE / EN)
> - Alle Labels, Event-Typen, Beschreibungen und Fehlermeldungen übersetzt
> - Gewählte Sprache bleibt nach App-Neustart erhalten
> - Locations-Beschreibungen: Fallback auf Deutsch wenn EN fehlt

### US-21 · App-Beschreibung & Onboarding
> **Als neuer Nutzer** möchte ich verstehen wie FotoAlert funktioniert – was die Scores bedeuten, wie Schwierigkeitsgrade definiert sind, und wie ich die App optimal nutze.
>
> **Akzeptanzkriterien:**
> - Onboarding-Screen beim ersten Start (3–4 Slides)
> - „?" Info-Button im Header → erklärt Score-System, Schwierigkeitsgrade, Event-Typen
> - Jeder Score-Wert (Astronomie, Wetter, Gesamt) hat ein Tooltip mit Erklärung
> - Glossar: Was ist ein Alignment? Was bedeutet Quality-Score?



### US-07 · Goldene Wolken & Himmelsröte Scoring `[ ]`
> **Als Fotograf** möchte ich für Goldene-Stunde-Events eine Einschätzung der Wolkenstimmungsqualität sehen – ob Bedingungen für dramatische goldene Wolken oder leuchtende Himmelsröte vorliegen – damit ich Go/No-Go-Entscheidungen noch gezielter treffen kann.
>
> **Hintergrund:** US-42 [x] zeigt bereits Gesamtbewölkung als Prozentwert. Dieses Ticket erweitert das um eine qualitative Einschätzung auf Basis der Wolkenhöhenschichtung: tiefe Wolken blockieren das Licht, mittlere und hohe Wolken reflektieren und färben es golden/rot.
>
> **Nicht in Scope:** Nebel (DWD Nebel-Gitter, eigenständiges Folge-Ticket), sternenklare Nacht (→ TASK-09 Bortle-Karte)
>
> **Differenzierung zu US-42 [x]:** US-42 zeigt vorhandene Open-Meteo-Felder (Gesamtbewölkung) an. US-07 berechnet einen neuen Score aus drei Wolkenhöhenparametern (`cloudcover_low/mid/high`), die bisher nicht abgerufen werden.
>
> **API-Entscheidung:** Open-Meteo (bereits integriert) wird um `cloudcover_low`, `cloudcover_mid`, `cloudcover_high` erweitert. Sunsethue API als optionaler Enrichment-Layer möglich, aber nicht nötig: Eigenberechnung liefert ausreichende Qualität ohne neue externe Abhängigkeit. Quellen: [Open-Meteo](https://open-meteo.com/), [Sunsethue](https://sunsethue.com/dev-api)
>
> **Sequenzierung:**
> ```
> US-42 [x] (Basis Wetter-Anzeige + Open-Meteo Integration)
>   └→ US-07 (Goldene Wolken & Himmelsröte Scoring)  ← kein Blocker, direkt implementierbar
>           └→ US-55 [x] (Score-Erklärungen via ⓘ), ggf. Erweiterung um golden_cloud_score-Info
>           └→ US-07b (Nebel & atmosphärische Sonderbedingungen, zukünftiges Ticket)
> ```
>
> **Akzeptanzkriterien:**
>
> **Backend – Datenerhebung:**
> - Open-Meteo hourly-Request um `cloudcover_low`, `cloudcover_mid`, `cloudcover_high` erweitert (nur Parameter ergänzen, kein separater API-Call)
> - Neue Felder werden im bestehenden Wetter-Cache mitgespeichert und im Event-Objekt mitgegeben
> - Betroffene Datei: `backend/weather.py` o.ä. (wo aktuell Open-Meteo aufgerufen wird)
>
> **Backend – Scoring-Algorithmus `_golden_cloud_score(cl, cm, ch) → float`:**
> - Input: `cloudcover_low` (cl), `cloudcover_mid` (cm), `cloudcover_high` (ch), jeweils 0–100 %
> - Output: Score 0.0–1.0
> - Logik:
>   - `cl > 80 %` → Score ≤ 0.10 (niedrige Wolken blockieren Licht vollständig)
>   - Mittlere + hohe Bewölkung < 10 % → Score ≤ 0.20 (klarer Himmel, nichts zum Einfärben)
>   - Mittlere + hohe Bewölkung > 90 % → Score ≤ 0.25 (gleichmäßige Decke, diffuses Licht)
>   - Sweet Spot: mittlere + hohe Bewölkung 25–65 %, niedrige Wolken < 30 % → Score 0.70–1.0
>   - Penalty: jeder Prozentpunkt niedrige Wolken über 30 % reduziert den Score graduell (exponentiell)
> - Score wird **nur** für Events innerhalb Goldener/Blauer Stunde (±30 Min.) berechnet – für andere Event-Typen `null`
> - Neue Konstante `GOLDEN_CLOUD_VERSION` in `precompute.py` → erzwingt Cache-Neuberechnung nach erstem Deployment
>
> **Backend – Integration in Gesamt-Score:**
> - Für Goldene-Stunde-Events: `weather_score` bekommt Bonus wenn `golden_cloud_score ≥ 0.7` (+5–10 Prozentpunkte, gedeckelt bei 1.0)
> - Für alle anderen Event-Typen: kein Einfluss auf bestehende Scoring-Logik
> - `ALGORITHM_VERSION` erhöhen → erzwingt inkrementelle Cache-Neuberechnung
>
> **Frontend – Anzeige im Event-Detail:**
> - Neues Label in der Wetter-Sektion: „🌅 Wolkenstimmung" mit 4 Qualitätsstufen:
>   - Score ≥ 0.75 → `🌅 Exzellent` (goldorange)
>   - Score ≥ 0.50 → `✨ Gut` (gelb)
>   - Score ≥ 0.25 → `🌤 Mäßig` (grau-gelb)
>   - Score < 0.25  → `⛅ Gering` (grau)
> - Nur angezeigt wenn Wetter-Overlay aktiv (T-3, identisch zu US-42 [x])
> - Nur angezeigt für Goldene-Stunde- und Blaue-Stunde-Events (bei anderen Event-Typen ausgeblendet)
> - ⓘ-Tooltip erklärt die drei Wolkenschichten kurz (analog zu US-55 [x] Score-Erklärungen)
>
> **Frontend – Feed-Card:**
> - Kein neues Badge nötig – Score fließt über weather_score-Bonus bereits in den Gesamt-Score ein
>
> **Tests:**
> - Manuelle Verifikation scattered clouds: `cl=5, cm=40, ch=30` → Score ≥ 0.70
> - Manuelle Verifikation Hochdrucklage: `cl=0, cm=0, ch=0` → Score ≤ 0.20
> - Manuelle Verifikation bedeckter Himmel: `cl=90, cm=80, ch=70` → Score ≤ 0.10
>
> *Folge-Ticket: US-07b Nebel & atmosphärische Sonderbedingungen (DWD Nebel-Gitter, Sichtweite) — noch nicht erstellt*

### US-08 · GPX-Export (Apple Maps / Google Maps)
> **Status:** Maps-Links für Fotograf-Standort und Motiv sind bereits in der Event-Detailansicht implementiert.
>
> **Offen:** „Alle Locations exportieren" als `.gpx`-Datei
>
> *Navigation & Fahrtzeit-Indikation → US-51 (separate Story)*

### US-09 · Sichtachsen-Check – Hinderniserkennung
> Raycast-Algorithmus via OpenTopoData + OSM Buildings. Technisch aufwendig, hohe Priorität für Genauigkeit.

### US-10 · Polarlichter / Aurora-Warnung
> NOAA SWPC Kp-Index, Push bei Kp ≥ 5. *(Offen)*

### US-11 · Bauarbeiten & Sperrungen
> Manuelles Crowdsourcing + Berlin Open Data API. *(Offen)*

---

## 🟡 Mittel – Daten & Integration

### ~~US-35 · Locationdetails: nur astronomisch mögliche Event-Typen anzeigen~~ `[x]`
> **Als Fotograf** möchte ich in der Location-Detailansicht nur die Himmelsobjekte als mögliche Events sehen, die an diesem Standort astronomisch tatsächlich erreichbar sind.
>
> **Akzeptanzkriterien:**
> - Sonne, Mond und Milchstraße werden nur als mögliche Events angezeigt, wenn Azimut und Sichtachse der Location ein Alignment prinzipiell erlauben
> - Berechnung basiert auf `ideal_azimuth_range` + Auf-/Untergangsazimuten des jeweiligen Objekts für Berlin/BB
> - Unmögliche Event-Typen werden ausgeblendet (nicht nur ausgegraut)
> - Hinweis wenn für eine Location keine der drei Kategorien möglich ist

### ~~US-36 · Event-Qualitätsschwelle: Mond/Sonne-Alignments nur in Dämmerung~~ `[x]`
> **Als Fotograf** möchte ich Mond- und Sonne-Alignment-Events nur dann angezeigt bekommen, wenn sie in der goldenen oder blauen Stunde stattfinden, da nur dann optimales Licht für das Foto herrscht.
>
> **Betroffene Event-Typen:** Mondaufgang/-untergang über Motiv, Sonnenaufgang/-untergang über Motiv, Mondscheibe-Alignment
>
> **Nicht betroffen:** Mondfinsternis, Sonnenfinsternis (auch partiell), Sonnenstern – diese sind unabhängig von der Tageszeit wertvoll.
>
> **Akzeptanzkriterien:**
> - Events außerhalb goldener/blauer Stunde (bürgerliche Dämmerung ±30 Min.) werden bei der Generierung gefiltert, nicht erst im Frontend
> - Bestehende Events im Cache werden beim nächsten Precompute-Lauf bereinigt
> - Filterlogik in `opportunity.py` dokumentiert

### ~~US-55 · Score-Erklärungen via Info-Overlay~~ `[x]`
> **Als Fotograf** möchte ich verstehen, wie die Scores (Gesamt, Astronomie, Wetter) berechnet werden, ohne die App zu verlassen, damit ich die Qualitätsbewertung einer Chance einordnen kann.
>
> **UI:** Kleiner ⓘ-Button (Kreis mit „i") neben jedem Score-Label in der Score-Leiste des Event-Detail-Sheets. Beim Klicken öffnet sich ein Overlay mit Erklärung der Berechnungsformel. Schließbar per ×-Button oder Tap auf den Hintergrund.
>
> **Akzeptanzkriterien:**
> - Gesamt-Score-Erklärung: Gewichtungsformel (Astronomie × 65% + Wetter × 35% bzw. nur Astronomie wenn > T-3)
> - Astronomie-Score-Erklärung: Punktewerte pro Event-Typ (Golden Hour, Mond-Phase, 3D-Alignment, Milchstraße)
> - Wetter-Score-Erklärung: Bewertungskriterien (Wolken, Cirrus, Regen, Nebel) + T-3-Hinweis
> - Overlay schließt bei Klick auf × oder auf den dunklen Hintergrund
> - Keine neuen Backend-Anfragen nötig (rein frontend)
>
> Implementiert in v1.2.1.

### ~~US-37 · Himmelsobjekt-Position relativ zum Motiv~~ `[x]`
> **Als Fotograf** möchte ich wissen, ob das Himmelsobjekt genau auf Höhe meines Motivs steht – zum Beispiel der Mond exakt auf Höhe der Fernsehturmspitze – und wie weit es seitlich davon abweicht, damit ich die Bildkomposition beurteilen kann.
>
> **Kern-Idee:** Der Beobachter sieht das Motiv unter einem bestimmten Elevationswinkel (arctan(Motivhöhe / Entfernung)). Steht das Himmelsobjekt auf genau diesem Winkel, befindet es sich „auf Höhe der Motivspitze" – der perfekte Kompositions-Moment.
>
> **Berechnung:**
> - **Scheinbare Motivhöhe** (observer_elevation_angle_deg):
>   `arctan((subject_elevation_m + subject_height_m - observer_elevation_m) / distance_m)`
> - **Höhenversatz** (altitude_delta_deg):
>   `object_altitude_deg − observer_elevation_angle_deg`
>   → positiv = Objekt steht höher als Motivspitze, 0° = Objekt genau auf Motivspitze, negativ = Objekt noch unterhalb
> - **Seitliche Abweichung** (azimuth_delta_deg):
>   `object_azimuth_deg − ideal_azimuth_deg` (vorzeichenbehaftet, − = links, + = rechts)
>
> **Qualitätslabels (altitude_delta_deg):**
> - `|Δ| ≤ 0.5°` → 🎯 „Exaktes Alignment – Objekt auf Höhe der Motivspitze"
> - `0.5° < Δ ≤ 3°` → ✨ „Knapp über dem Motiv"
> - `Δ > 3°` → ☁️ „Hoch über dem Motiv (X.X°)"
> - `Δ < −0.5°` → ⬇️ „Noch unterhalb der Motivspitze"
>
> **Seitliche Abweichung Labels (azimuth_delta_deg):**
> - `|Δ| ≤ 1°` → „Zentral"
> - `1° < |Δ| ≤ 5°` → „Leicht links/rechts versetzt (X.X°)"
> - `|Δ| > 5°` → „Deutlich versetzt – kein Alignment"
>
> **Daten-Voraussetzungen (in `PhotoLocation`):**
> - `observer_lat`, `observer_lon`, `observer_elevation_m` (Standpunkt Fotograf)
> - `subject_lat`, `subject_lon`, `subject_elevation_m` (Fuß des Motivs)
> - `subject_height_m` (Höhe des Motivs, z.B. Fernsehturmspitze = 368 m)
> - `distance_m` (bereits vorhanden)
>
> **Ausgabe im Event-Detail:**
> - Neue Sektion „🎯 Kompositions-Analyse" im Detail-Sheet
> - Höhenversatz in Grad mit Label + seitliche Abweichung in Grad mit Label
> - Nur anzeigen wenn `subject_height_m` vorhanden
> - Gilt für Sonne und Mond

### ~~US-41 · Event-Detail: Physische Entfernung & Topographie~~ `[x]`

### ~~US-42 · Event-Detail: Erweiterte Wetterdaten~~ `[x]`
> **Als Fotograf** möchte ich in der Chancen-Detailansicht konkrete Wetterdaten sehen – nicht nur einen Score – damit ich eine Go/No-Go-Entscheidung treffen kann, ohne die App zu verlassen.
>
> **Akzeptanzkriterien:**
> - Temperatur (°C) zum Shoot-Zeitpunkt
> - Regenwahrscheinlichkeit (%)
> - Wolkenbedeckung (%) mit grober Einschätzung (klar / leicht bewölkt / bedeckt)
> - Nebelwarnung wenn Sichtweite < 1 km (aus Open-Meteo `visibility`-Feld)
> - Windstärke (km/h oder Beaufort) und Windrichtung
> - Daten nur angezeigt wenn Wetter-Overlay aktiv (innerhalb T-3 Tage)
>
> *Differenziert von US-07 (Wetter-Scoring-Erweiterung = Algorithmus) — diese Story betrifft ausschließlich die Anzeige bereits vorhandener Open-Meteo-Felder im Detail-Sheet*

### US-50 · Nutzungsanalyse (Analytics) via Matomo `[ ]`
> **Als App-Host** möchte ich das häufigste Nutzungsverhalten meiner User verstehen, damit ich wertvolle Features priorisieren und wenig genutzte Funktionen verbessern oder entfernen kann.
>
> **Werkzeug:** Matomo (Open Source, selbst-gehostet, DSGVO-konform, kostenlos)
>
> **Akzeptanzkriterien:**
> - Matomo-Instanz eingerichtet (Docker oder managed)
> - Tracking-Script in der PWA eingebunden (Page Views, Tab-Wechsel, Filter-Nutzung, Detail-Öffnungen)
> - Events getracked: Location-Detail öffnen, Event-Detail öffnen, Verifikation abschicken, Filter setzen, Kalender-Tab öffnen
> - Dashboard zeigt: meistbesuchte Locations, meistgenutzte Filter, Verweildauer pro Tab, Gerättypen
> - Kein personenbezogenes Tracking (IP anonymisiert, kein Cross-Site)
>
> *Kein Overlap mit bestehendem Backlog.*

### US-51 · Navigation & Fahrtzeit zum Fotostandort `[ ]`
> **Als App-User** möchte ich eine Wegplanung von meiner aktuellen Position zum Fotograf-Standort starten können und vorab sehen wie lange ich aktuell dorthin bräuchte, damit ich rechtzeitig vor Ort bin.
>
> **Verfügbar:** In Locationdetails + Chancendetails
>
> **Akzeptanzkriterien:**
> - „🧭 Route planen"-Button in Location-Detail und Event-Detail-Sheet
> - Öffnet bevorzugte Navigations-App (Apple Maps / Google Maps / Waze) mit vorausgefülltem Ziel (Observer-Koordinaten)
> - In-App Fahrtzeit-Indikation: Schätzung der aktuellen Fahrtzeit per Google Maps Distance Matrix API oder Apple MapKit JS (nur wenn GPS-Erlaubnis vorhanden)
> - Fallback wenn kein GPS: nur Navigation-Button ohne Zeitschätzung
> - Anzeige: „~23 Min. mit dem Auto" inline unter dem Standort-Label
>
> *Differenziert von US-08 (Maps-Link = Einzel-Tap, bereits implementiert) – diese Story ergänzt In-App Fahrtzeit + expliziten Route-CTA.*

### US-52 · Smarte Abfahrts-Erinnerung (distanzbasiert) `[ ]`
> **Als Fotograf** möchte ich eine Push-Notification erhalten, die auf meiner aktuellen Entfernung zum Fotostandort basiert, sodass ich pünktlich zum Shoot-Zeitpunkt vor Ort bin – ohne selbst berechnen zu müssen wann ich losmuss.
>
> **Akzeptanzkriterien:**
> - System berechnet: Shoot-Zeit − geschätzte Fahrtzeit (aktuelle Distanz) − konfigurierbarer Puffer (z. B. +15 Min.)
> - Notification: „Jetzt losfahren für Goldene Stunde um 20:47 – du brauchst ~38 Min."
> - Distanz-Abfrage beim Aktivieren der Erinnerung (einmalig, nicht dauerhaft im Hintergrund)
> - Unterstützte Puffer: +0 / +15 / +30 Min. (konfigurierbar in Einstellungen)
> - Fallback wenn kein GPS: fester Vorlauf aus US-44 greift stattdessen
> - Koordiniert mit US-44 (manuelle Vorlaufzeit) – Smart Mode ergänzt, ersetzt nicht
>
> *Differenziert von US-44 (manuelle Vorlaufzeit 15/30/60/120 Min.) – diese Story ist automatisch und distanzbasiert.*

### US-25 · Duplikate identifizieren (Host-Tool)
> **Als Host** möchte ich Locations mit ähnlichem GPS-Standort und überlappenden Motiven finden und zur Bereinigung vorgeschlagen bekommen.
>
> **Akzeptanzkriterien:**
> - CLI-Tool oder Backend-Endpoint `/admin/duplicates`
> - Findet Locations < 300m Abstand voneinander
> - Zeigt Paarweise: Name A / Name B · Entfernung · Azimut-Differenz
> - Empfiehlt: „Zusammenführen" (gleicher Spot, verschiedene Standpunkte) oder „Löschen" (echter Duplikat)
> - Output als tabellarische Übersicht oder JSON

### ~~TASK-12 · Automatische Neuberechnung nach Koordinaten-Änderung~~ `[x]`
> **Hintergrund:** US-60 ✅ speichert geänderte Koordinaten sofort in `location_overrides.json` / `custom_locations.json`. Die davon abhängigen Berechnungen (`distance_m`, `bearing`, `azimuth_range`, `focal_length_suggestions`, `solar_alignment_note`, `lunar_alignment_note`, `elevation_difference_m`, `possible_bodies`, alle zugehörigen Events) werden jedoch NICHT sofort aktualisiert – sie sind bis zum nächsten Cron-Lauf (täglich 05:30) veraltet.
>
> **Differenzierung zu US-34 (Job-Orchestrierung [~]):** US-34 implementiert ein PWA-Refresh-Menü für manuelle Job-Auslösung und geplante Cron-Jobs. Dieser TASK ergänzt US-34 um einen **automatischen, einzel-Location-spezifischen Recompute direkt nach dem Speichern**, ohne dass der User aktiv werden muss.
>
> **Akzeptanzkriterien:**
> - Backend: Nach erfolgreichem `PATCH /locations/{id}` wird asynchron `_run_precompute(location_ids=[id])` getriggert (nur diese eine Location, nicht alle)
> - Der PATCH-Response ist sofort verfügbar (kein Warten auf Recompute) – Recompute läuft im Hintergrund via `asyncio.create_task()`
> - Elevation-Daten werden bei Koordinaten-Änderung neu abgerufen (OpenTopoData) und im Elevation-Cache aktualisiert
> - Nach Abschluss des Hintergrund-Recomputes sind im Feed neue Events für diese Location sichtbar (kein manuelles Reload nötig, ggf. Pull-to-Refresh)
> - Fehler im Hintergrund-Recompute werden geloggt, brechen aber den ursprünglichen PATCH nicht ab
> - Manueller Fallback bleibt bestehen: `python3 precompute.py --feed-only` im Backend-Terminal
>
> *Ergänzt US-34 (manuelle Auslösung) – ist unabhängig davon implementierbar und sollte vorher umgesetzt werden*

### TASK-11 · Impressum & Copyright einbauen `[ ]`
> Impressum-Seite in der PWA ergänzen (erreichbar über Einstellungen oder Footer).
>
> **Inhalt:**
> - Copyright-Hinweis: „© 2026 Stephan Schumann – Alle Rechte vorbehalten"
> - Angaben gemäß § 5 TMG (Name, Adresse, Kontakt)
> - Hinweis auf verwendete APIs (OpenTopoData, Open-Meteo, Skyfield) mit Lizenzen
> - Datenschutzhinweis (kein Tracking, GPS nur bei Erlaubnis, keine Server-seitige Speicherung persönlicher Daten)
>
> *Rechtlich empfohlen für öffentlich zugängliche Web-Apps.*

### TASK-01 · Kometen-Integration `[ ]`
> NASA JPL Horizons API anbinden für aktuelle Kometen-Positionen und -Sichtbarkeit.

### TASK-02 · Sonnenfinsternisse berechnen `[ ]`
> Skyfield-Berechnung der Kontakte (C1–C4) für Berlin/BB-Region.

### TASK-03 · Feuerwerk-Events `[ ]`
> Manuelle Events für wiederkehrende Feuerwerke: Silvester, Pyronale, Havel in Flammen.

### TASK-04 · Weitere Locations erfassen `[ ]`
> Schloss Cecilienhof, Pfaueninsel, Kloster Chorin, Feldsteinkirchen Uckermark, Seelower Höhen. Locationscout-Scroll-Limit von 12 aufheben.

### TASK-05 · Design-Spec dokumentieren `[ ]`
> `DESIGN.md` mit allen CSS-Tokens, Abständen, Komponenten-Regeln anlegen. *(Design ist eingefroren, Dokumentation fehlt noch)*

---

## 🟢 Niedrig – App-Verbesserungen

### US-43 · Apple Watch Komplikation `[ ]`
> **Als Fotograf** möchte ich die nächste Foto-Chance direkt auf meiner Apple Watch sehen, ohne die App zu öffnen.

### US-44 · Push-Notification Vorlaufzeit konfigurieren `[ ]`
> **Als Fotograf** möchte ich selbst festlegen, wie früh ich vor einem Event benachrichtigt werde (15 / 30 / 60 / 120 Min.).

### US-45 · Wochenvorschau-Widget `[ ]`
> **Als Fotograf** möchte ich die Top-3 Chancen der Woche als iOS-Homescreen-Widget sehen.

### US-46 · Karten-Ansichtsmodi `[ ]`
> **Als Fotograf** möchte ich zwischen Standard-, Satelliten- und Nacht-Ansicht auf der Karte wechseln können.

### TASK-06 · AR-Overlay: Sonnenbahn über Kamera-Live-Preview `[ ]`
> Sonnenbahn als AR-Overlay über dem Kamera-Bild einblenden.

### TASK-07 · Export als PhotoPills-Bookmark `[ ]`
> Location-Daten im PhotoPills-kompatiblen Format exportieren.

### TASK-08 · Wetter-Radar-Overlay `[ ]`
> DWD-Radar als Overlay auf der Karte einblenden.

### TASK-09 · Bortle-Karte `[ ]`
> Lichtverschmutzungs-Overlay für Milchstraßen-Locations (Bortle-Skala).

---

## 💡 Ideen / Langfristig

### US-47 · KI-Kompositions-Vorschläge `[ ]`
> **Als Fotograf** möchte ich automatisch generierte Bildausschnitt-Empfehlungen basierend auf Azimut und Gebäudeform erhalten.

### US-48 · Community-Locations `[ ]`
> **Als Fotograf** möchte ich eigene Spots einreichen, die nach Prüfung durch den Host in die App aufgenommen werden.

### US-49 · Historische Alignments `[ ]`
> **Als Fotograf** möchte ich sehen, welche Alignments an einem Spot in den letzten 5 Jahren stattgefunden haben.

### TASK-10 · Astronomisches Twilight für Milchstraße `[ ]`
> Nautische vs. astronomische Dämmerung in der Berechnung unterscheiden (relevant für Milchstraßen-Sichtbarkeit).

---

## ✅ Erledigt

- [x] Projektstruktur & Architektur (Backend + iOS)
- [x] Astronomie-Engine (Sonne, Mond, Milchstraße, Meteoritenschauer) via Skyfield
- [x] **Skyfield-Vektorisierung** – Alle Berechnungsloops auf numpy-Arrays umgestellt (~40× Speed-up)
- [x] Wetter-Integration via Open-Meteo (kostenlos, kein API-Key)
- [x] Locations-Datenbank Berlin/Brandenburg (55 Spots inkl. 12 Locationscout-Imports)
- [x] Opportunity-Scoring-Algorithmus (Azimut + Höhenwinkel + Wetter)
- [x] **Vertikale Triangulation** – 3D-Alignment, Crown/Mid/Base-Klassifikation
- [x] FastAPI Backend + täglicher Scheduler
- [x] iOS App SwiftUI (Feed, Karte, Detail, Einstellungen)
- [x] **PWA Web-App** – SPA mit Service Worker, offline-fähig, installierbar
- [x] **Cache-First Architektur** – precompute.py + JSON-Cache, Weather-Overlay stündlich
- [x] **Feed-Deduplizierung** – Beste Event pro Location+Typ+Tag
- [x] **GPS-Koordinaten in Detailansicht** – Fotograf-Standort + Motiv mit Maps-Links
- [x] **US-01** Frühwarnung astronomische Events 14 Tage im Voraus
- [x] **US-02** Wetter-Overlay ab T-3
- [x] **US-03** Goldene & Blaue Stunde als eigenständige Events
- [x] **US-05** Quick Location Capture – 2-Schritt-Karten-Klick, GPS-Button, Persistenz in custom_locations.json
- [x] **US-12** Locationscout-Import – Login, Scraping, GPS-Extraktion, Filter, Import-Tool (einmaliger Import; dauerhaftes Management → US-33)
- [x] **US-13** Jahreskalender – 365-Tage-Vorausschau, gecacht, Kalender-Tab in PWA
- [x] **US-14** Street View Vorschau – „👁 Street View"-Button, Google Maps URL API mit heading=Azimut
- [x] **US-15** Cache-First Architektur
- [x] **US-18/19/20/27** Einzelfilter (Umkreis, Eventtyp, Schwierigkeit, Wahrscheinlichkeit) – zusammengeführt in US-32 (Kombiniertes Filter-System)
- [x] **US-23** Standort-Verifikation – „✓ Vor Ort geprüft"-Button, Kommentarfeld, localStorage, Badge auf Card und Detail
- [x] **US-28** Schließen-Button Detail-Sheet – ✕-Button im Header, Auto-Close nach Verify
- [x] **US-29** Location-Namen Datenqualität – Standortnamen beschreiben Perspektive, nicht Event. Nikolaikirche Potsdam umbenannt + Koordinaten korrigiert (52.40409°N, 13.04519°E). „Sunset over Wittstock" → „Wittstock – Stadtmauer & Westskyline".
- [x] **US-22** Locationmenü – Detailansicht pro Standort. Anklickbare Location-Cards, Detail-Sheet mit GPS/Maps/Street View/Azimut/Events, Nordhinweis-Warnung bei unmöglichem Azimutbereich.
- [x] **US-30** Standort-Verifikation erweitert – Positiv & Negativ mit Timeline. Array-basierte Historie, Zähler, Datumsanzeige, Gründe für negative Verifikationen, kompakte Timeline-Ansicht.
- [x] **US-31** Niveaudifferenz aus Topographiedaten – OpenTopoData EUDEM 25m, elevation_difference_m in Berechnung + Location-Detail + Event-Detail angezeigt (|Δ| > 2m).
- [x] **US-32** Kombiniertes Filter-System – 6 Gruppen: Eventtyp, Tageszeit (Morgens/Tagsüber/Abends/Nacht per Skyfield), Mindest-Score Slider, Schwierigkeitsgrad, GPS-Entfernung, Verifikationsstatus. localStorage-Persistenz, Badge am Icon. v1.1.2.
- [x] **US-41** Physische Entfernung & Topographie im Event-Detail – Haversine-Distanz (m/km) + Niveaudifferenz (EUDEM 25m, |Δ| > 2m). Sektion „📏 Standort & Topographie". v1.1.1.
- [x] **US-24** Starrating – 1–5 Sterne pro Location, Rating-Objekt in localStorage, interaktiver Sterne-Input im Location-Detail, Anzeige auf Location-Card + Feed-Card. SW v19.
- [x] **BUG-01** Brennweite-Empfehlung – `_focal_for_location()` aus distance_m (25%-Fill), camera hints parametrisiert, Min+Max-Brennweite-Filter (zwei Slider), „Brennweite falsch" in Verifikation. v1.1.3.
- [x] **US-53** Live-Textsuche im Feed – Lupe im Header, Suchbar-Overlay, Substring-Match (case-insensitive) auf Location-Name, AND mit Filtern, Escape/Abbrechen. v1.1.4.
- [x] **US-36** Alignment-Events nur in Dämmerung – `_in_photo_window()` in opportunity.py filtert alle 3 Alignment-Sektionen (Mond, 3D-Präzise, Sonne-Fallback) auf goldene/blaue Stunde ±30 Min. 78% der daytime-Alignments bereinigt. Cache-Neuberechnung erforderlich.
- [x] **BUG-02** Suche filtert Jahreskalender nicht – `Search._triggerRender()` mode-aware, `CalendarView.render()` mit Suchfilter + Hinweis in Status-Zeile. v1.1.8.
- [x] **US-42** Erweiterte Wetterdaten im Event-Detail – Temperatur, Wolken, Regen, Wind, Sichtweite, Nebelwarnung, Cirrus-Bonus. Nur bei T-3 Wetter-Overlay. v1.2.0.
- [x] **US-37** Kompositions-Analyse im Event-Detail – Höhenversatz (arctan) + Azimut-Delta zu Motivspitze, Labels (🎯 Exakt / ✨ Knapp über / ☁️ Hoch über / ⬇️ Unterhalb), scheinbarer Himmelsobjektdurchmesser. `_composition_analysis()` in precompute.py.
- [x] **US-55** Score-Erklärungen via ⓘ-Overlay – Gesamt/Astronomie/Wetter-Score je mit Info-Button im Detail-Sheet. Overlay mit Berechnungsformel, × und Hintergrund-Tap zum Schließen. v1.2.1.
- [x] **US-35** Locationdetails: astronomisch unmögliche Event-Typen ausgeblendet – `_compute_possible_bodies()` in main.py berechnet per observer_lat+ideal_azimuth_range via cos(Az)=sin(δ)/cos(φ) welche Körper (sun/moon/milkyway) jemals im Sichtbereich aufgehen. `possible_bodies` in LocationOut-Schema. Frontend: Chips (grün=möglich/durchgestrichen=unmöglich), alignment_notes nur wenn Körper möglich, Warntext bei Treffer. v1.2.2.
- [x] **US-56** Location-Capture: Koordinaten per Text-Eingabe – Textfelder für lat/lon, 📋 Clipboard-Paste (Dezimal + DMS), Karten-Marker-Update, Inline-Validierung. Fullscreen-Karte (Satellit, Zoom, Crosshair). Reverse Geocoding (Nominatim) für Auto-Beschreibung. Edit-Funktion (✏️) für Custom Locations via PATCH-Endpoint. v1.3.x.
- [x] **BUG-06** Header-Suche filtert Locations-Tab nicht – `Search._triggerRender()` um Locations-Branch erweitert: `if (App.current === 'locations') Locations.filter(query)`. v1.3.3.
- [x] **US-58** Kamera-Sichtfeld-Visualisierung – Sektion „📐 Karte & Blickwinkel" in Location- + Event-Detail. Leaflet Satellit, Fotograf-Pin (orange), Motiv-Pin (gold), Sichtachse, FOV-Kegel. Sensor/Brennweite/Ausrichtung persistent in localStorage. v1.3.9.
- [x] **US-59** Aufklappbare Sektionen – `mkSec()` Helper + `Sections` Objekt mit localStorage-Persistenz, Chevron-Animation, alle Event- und Location-Detail-Sektionen konvertiert (8 + 7). v1.3.8.
- [x] **US-61** Navigation Event-Detail → Location-Detail – Location-Name im Event-Detail-Sheet als klickbarer Button (→ öffnet LocationDetail, schließt Event-Detail). v1.3.7.
- [x] **US-60** Koordinaten-Bearbeitung + einheitliches Eingabefeld – ✏️ für alle Locations (nicht nur custom_), einheitliches Koordinatenfeld (Dezimal + DMS), Mini-Karte mit draggbaren Markern, location_overrides.json für Standard-Locations. @app.on_event("startup") Fix für _load_caches(). v1.3.6/1.3.7.
- [x] **BUG-07** Sheets überschreiten iPhone-Breite auf Desktop – `@media (min-width:600px)`: left:50%; width:480px; margin-left:-240px. v1.3.5.
- [x] **BUG-08** Mindest-Wahrscheinlichkeits-Filter ohne Wirkung – ID-Kollision `score-val` → `filter-score-val`, CFG.minScore-Konflikt mit altem fa_min_score-LocalStorage (hardcode 0.35), fehlende `Filter.applyToLocations()` im Locations-Tab. Live-Filter via `_applyLive()` + `_applyLiveDebounced()`. v1.4.1/1.4.2.
- [x] **BUG-09** Inkonsistente Marker-Symbole – Einheitliche Marker über alle Leaflet-Karten: Fotograf = orange circleMarker #FF6600, Motiv = gold circleMarker #E8A020. v1.4.2.
- [x] **TASK-12** Automatische Neuberechnung nach Koordinaten-Änderung – Nach PATCH `/locations/{id}` asynchroner `_run_precompute(location_ids=[id])` via `asyncio.create_task()`; Elevation-Cache-Update inklusive. v1.4.2.
- [x] **BUG-05** Feed zeigt Events nach Shoot-Window-Ende – `_filter_feed()`: `shoot_window_end < now_utc` als Cutoff, Fallback +30 min. v1.3.5.
- [x] **BUG-04** Brennweiten-Filter Dual-Handle Range-Slider – Custom Slider mit aktivem Bereich (gold) zwischen Handles, Außenbereiche grau. v1.3.5.
- [x] **BUG-02** Suche filtert Jahreskalender nicht – `Search._triggerRender()` mode-aware, CalendarView.render() mit Suchfilter. v1.1.8.
- [x] **BUG-01** Brennweite-Empfehlung passt nicht zur Motiventfernung – `_focal_for_location()` aus distance_m, Min+Max-Filter, „Brennweite falsch" in Verifikation. v1.1.3.
- [x] **BUG-03** Scheinbare Größe des Himmelsobjekts zu groß – `get_moon_earth_distance_km()` via Skyfield de421.bsp für tatsächliche Mond–Erde-Distanz zum Shoot-Zeitpunkt. Formel korrigiert: `angular_diameter_rad = MOON_DIAMETER_KM / moon_earth_distance_km`. Distanz im Detail-Sheet als Fußnote. `ALGORITHM_VERSION = "1.1"`. v1.3.4.

### BUG-24 · Kartenpanel-Filter erscheint auf Mac hinter der Leaflet-Karte `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-17 |
| **In Progress seit** | 2026-06-17 |
| **Abgeschlossen** | 2026-06-17 |

**Beschreibung:**
Im Karten-Tab erscheint das Filter-Sheet auf Mac (Chrome + Safari) hinter der Leaflet-Karte und kann nicht bedient werden. Auf iPhone Safari (PWA-Standalone) funktioniert es korrekt.

**Root Cause:**
`#page-map` hatte `position: absolute; z-index: auto` und bildete **keinen eigenen Stacking-Context**. Dadurch participierten alle Leaflet-Panes direkt im Root-Stacking-Context mit ihren internen z-index-Werten (`.leaflet-tile-pane` z=200, `.leaflet-marker-pane` z=600, `#map-layer-toggle` z=1000). Das `#filter-sheet` (z=105) lag damit unter den Leaflet-Panes. Auf iPhone (PWA-Standalone) verhindert ein separater Compositing-Layer das Leaking.

**Fix:**
```css
/* BUG-24: isolation:isolate schließt alle Leaflet-z-indices ein → #filter-sheet (z=105) erscheint darüber */
#page-map { padding: 0 !important; isolation: isolate; }
```
`isolation: isolate` erzwingt einen neuen Stacking-Context für `#page-map` ohne z-index-Wert zu ändern. Alle Leaflet-z-indices sind damit eingeschlossen. `#filter-sheet` (z=105) erscheint im Parent-Context darüber.

**Akzeptanzkriterien:**
- [x] Filter-Sheet erscheint auf Mac Chrome und Safari über der Leaflet-Karte
- [x] Filter-Sheet erscheint weiterhin korrekt auf iPhone Safari
- [x] Karteninteraktion (Panning, Zoom, Marker-Klick) unverändert
- [x] Layer-Toggle (Nacht/Standard/Satellit) bleibt funktionsfähig

**Datei:** `web/index.html` — CSS-Regel `#page-map`
