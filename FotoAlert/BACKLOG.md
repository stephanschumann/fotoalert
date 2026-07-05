# FotoAlert – Backlog

> Ideen, Verbesserungen und offene Aufgaben.  
> Claude liest diese Datei am Anfang jedes Chats und erinnert dich an offene Punkte.
>
> **Typen:** `US-XX` User Story (Feature) · `TASK-XX` Aufgabe (kein User Value) · `BUG-XX` Fehler (Problemlösung)  
> **Status:** `[ ]` offen · `[~]` in Arbeit · `[x]` erledigt  
> **Workflow:** Claude setzt auf `[~]` bei Implementierungsbeginn. `[x]` + Verschiebung nach ✅ Erledigt nur nach expliziter Bestätigung durch Stephan.
>
> **Pipeline-Lanes** *(das Pipeline-Steuerung-Board unten ist die maßgebliche Quelle):*  
> `Inbox` → **`Ready for Analysis`** *(🚦 DEIN GATE)* → `In Analysis` → `Ready for Dev` → `In Progress` → `In Test` → `Done` → `🔁 Retro / Lernen` · `🚫 Excluded`  
> **Gate-Regel:** Agenten (PM + Dev) nehmen **ausschließlich** Tickets auf, deren ID im Board unter **Ready for Analysis** oder einer nachgelagerten Lane steht. Tickets in `Inbox` werden nie automatisch analysiert oder implementiert — erst wenn **du** sie nach `Ready for Analysis` ziehst.  
> **Ausschluss:** Eine ID unter `🚫 Excluded` wird nie aufgenommen, auch wenn sie sonst priorisiert wäre. Vorrang vor allen anderen Lanes.  
> **Release bleibt manuell:** Der Übergang `In Test` → `Done` mit Deploy erfolgt nur nach deiner ausdrücklichen Freigabe.

---

## 🚦 Pipeline-Steuerung (Gate-Board)

> **Maßgebliche Quelle für die Agenten.** Nur Ticket-IDs in **Ready for Analysis** und den
> nachgelagerten Lanes dürfen aufgenommen werden. Du steuerst die Pipeline, indem du IDs
> zwischen den Lanes verschiebst — vor allem von **Inbox** nach **Ready for Analysis**.
>
> Detail, Akzeptanzkriterien und Spec jedes Tickets stehen unverändert weiter unten in der Datei.

| Lane | Bedeutung | Ticket-IDs |
|------|-----------|-----------|
| **🚦 Ready for Analysis** | *Dein Gate* — freigegeben für die Agenten | *(leer)* |
| **🔬 In Analysis** | Pre-Mortem + Spec laufen | US-38 |
| **⛔ Weg-Gate** | Optionen vorgelegt — Stephan wählt | *(Hinweis: technisch dieselbe Lane wie "In Analysis", siehe Kanban-Spalte oben)* |
| **✅ Ready for Dev** | Spec freigegeben, wartet auf Implementierung | US-09 |
| **🔄 In Progress** | wird gerade implementiert | *(leer)* |
| **🧪 In Test** | implementiert, wartet auf (Test-)Bestätigung | US-21 |
| **🏁 Done** | abgeschlossen + deployed | **TASK-57** *(refactor_check.py: Wurzelursache der Falsch-Positive behoben, kein Deploy nötig, 2026-07-05)* · **US-117** *(Karten-Tab öffnet mit GPS-Standort + 5-km-Radius, released v1.21.4, 2026-07-05)* · **TASK-56** *(DB-Snapshot-Ordner aus Git-Tracking genommen, .gitignore ergänzt, kein Deploy nötig, 2026-07-05)* · **US-125** *(Host kann Beispielbild löschen, released v1.21.3, 2026-07-05)* · **US-126** *(Host kann Bildausschnitt/Fokuspunkt selbst wählen, released v1.21.3, 2026-07-05)* · **BUG-57** *(Verwaiste Testdatei test_us72_weather_map.py entfernt, kein Deploy nötig, 2026-07-05)* · **BUG-60** *(Hinweise-Feld bei Neuanlage leer, released v1.21.2, 2026-07-04)* · **US-124** *(Vollbild-Modus Anlege-Karte, released v1.21.2, 2026-07-04)* · **US-120** *(Beispielbild-Upload, Host-Upload + Hoch-/Querformat mittig + Löschen-Kaskade, released 2026-07-04)* · **US-119** *(Feed-Standardfilter Wahrscheinlichkeit ≥70%, released v1.20.22, 2026-07-04)* · **BUG-61** *(Motivname serverseitig zur Whitelist hinzugefügt, released 2026-07-04)* · **US-123** *(Kartenansicht-Umschalter Satellit/Standard für Location-Karten, released v1.20.20, 2026-07-04)* · **US-121** *(Dublette geschlossen, kein Code geändert, 2026-07-04)* · **US-122** *(Dublette geschlossen, kein Code geändert, 2026-07-04)* · **BUG-59** *(Wetter-Overlay bei leichtem Wetter sichtbar, Schwellwert-Deckkraft, released v1.20.18, 2026-07-04)* · **TASK-53** *(Dev-Sync-Werkzeug Live→Dev, committed 2026-07-04, kein Deploy nötig)* · **BUG-58** *(Wolken-/Niederschlag-Umschalter zoomt auf 50-km-Radius statt Europa, released 2026-07-04)* · **US-87** *(Vollbild-Overlay Bearbeiten-Karte, released 2026-07-03)* · **BUG-56** *(Astronomie-Regressionstest korrigiert, released 2026-07-03)* · **US-113** *(Himmelsröte-Chance nur bei Sichtachse im Gegenpunkt-Sektor der Sonne, released 2026-07-02)* · **US-72** *(Wetterkarte Grid-Overlay + Slider, released 2026-07-01)* · **US-112** *(Wetter-Overlay DWD ICON-D2/EU + MET Norway, weicher Verlauf, released 2026-07-01)* · **BUG-55** *(Wetterkarte Auto-Zoom-Fix, released 2026-06-30)* · **BUG-54** *(Sections._def Goldene Wolken/Himmelsröte + Position, released 2026-06-30)* · **US-109** *(Goldene Wolken & Himmelsröte, released 2026-06-30)* · **US-108** *(Azimut-Filterung Mondauf/-untergang, released 2026-06-30)* · **US-07** *(Golden Cloud Score, released 2026-06-30)* · **BUG-48** *(Round-Robin-Cap im /opportunities-Feed, released 2026-06-29)* · **BUG-49** *(Doppeltes Suchfeld entfernt, released 2026-06-29)* · **BUG-50** *(HINWEISE-Feld speicherbar, released 2026-06-29)* · **BUG-52** *(GPS-Dialog nur einmal pro Session, released 2026-06-29)* · **BUG-53** *(Pin-Emoji nicht mehr in Location-Namen, released 2026-06-29)* · **BUG-51** *(Entfernungsfilter Locations-Tab, released 2026-06-29)* · **US-107** *(Sonnen-Alignment, released 2026-06-29)* · **US-106** *(v1.19.5 released 2026-06-28)* · **BUG-47** · **BUG-46** · **TASK-45** · **TASK-47** · **TASK-48** *(Epic Datensync, v2.0.x released 2026-06-28)* · **BUG-34** *(iOS-Zoom Fix, released 2026-06-28)* · **TASK-42** *(Falsch-Positiv, kein Handlungsbedarf, 2026-07-03)* |
| **🔁 Retro / Lernen** | auto nach Done: Erkenntnisse → Memory/Tests, Skill-Vorschläge zur Freigabe | *(transient — läuft automatisch)* |
| **🚫 Excluded** | explizit ausgeschlossen — nie aufnehmen | *(leer)* |
| **📥 Inbox** | offene Tickets, **nicht** freigegeben | US-84, US-85, BUG-21, TASK-41 · US-94 · **BUG-43** · **US-104** · **TASK-50** *(Service-Worker Auto-Update nach Release)* · **BUG-56** *(Astronomie-Regression Sonnenauf-/-untergang Berlin)* · **TASK-51** *(Lange Funktion startup() in backend/main.py)* · **US-114** *(Vollbild-Karten-Overlay auch bei Chancen, Kalender und Scout)* · **TASK-54** *(Prüfen: dauerhafter Festplatten-Cache für Wetterkarten-PNGs)* · **TASK-55** *(Server-Backup um location_images/ erweitern)* · **BUG-62** *(Kartenansicht: Wetter-Filter und Kartenmodus-Umschalter überlappen auf schmalen Bildschirmen)* · **BUG-63** *(„Alignments berechnen" blockiert Server ca. 20–25 Sek.)* · **TASK-58** *(Lange Funktion mkCloudCompassSvg() in web/index.html)* · **+ alle übrigen offenen Tickets unten** |

**So benutzt du das Board:**
1. **Freigeben:** Ticket-ID von `Inbox` nach `Ready for Analysis` verschieben → Agenten dürfen starten.
2. **Ausschließen:** ID unter `🚫 Excluded` eintragen → bleibt unangetastet.
3. **Release-Gate:** Steht ein Ticket in `In Test` und ist ein Deploy nötig, wartet die Pipeline auf dein „release".

---

## 🐛 BugFixes

### BUG-55 · Wetterkarte: Overlay erscheint als senkrechte Linie statt 10×10-Gitter (Zoom zu nah) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-30 |
| **Abgeschlossen** | 2026-06-30 |

**Beschreibung:** Beim Einschalten des Wetter-Overlays (US-72) zeigt die Karte statt des erwarteten 10×10-Mosaiks nur eine schmale senkrechte Linie. Beobachtet: Alle 100 Grid-Rechtecke sind im DOM, aber nur 2 davon haben sichtbare Größe. Ursache (bereits verifiziert, kein Render-/Daten-/Safari-Fehler): Das Wetter-Gitter spannt ganz Deutschland auf — eine Zelle ist 1,0° breit und damit bei der Start-Zoomstufe (Karte startet auf Berlin, Zoom 10) breiter als das gesamte Kartenfenster; 98 von 100 Zellen liegen außerhalb des Sichtbereichs und werden von Leaflet weggeschnitten. Es ist ein Maßstabs-Problem, kein Bug an den Daten. Erwartet: Beim Aktivieren des Overlays wird das vollständige Deutschland-Gitter als zusammenhängendes Mosaik sichtbar.

**Lösungsansatz (nur Vorschlag, nicht Teil dieses Intake):** Beim Einschalten des Wetter-Overlays die Karte automatisch so weit herauszoomen (z. B. via `fitBounds` auf die Gitter-/Deutschland-Bounding-Box 47.3°N–55.0°N, 6.0°E–15.0°E), dass das gesamte Gitter sichtbar ist; beim Ausschalten zur vorherigen Ansicht (Center + Zoom) zurückkehren.

**Bezug:** Direkte Abhängigkeit von **US-72** (Wetterkarte, aktuell „In Test") — BUG-55 ist ein Folgefehler aus deren Implementierung; betrifft AK „aktivieren zeichnet ein farbcodiertes Grid-Overlay" sowie das Pre-Mortem-Risiko „Grid zu grob / unsichtbar". Empfehlung: eigenständig führen, aber an US-72 koppeln (siehe Beziehungsanalyse). Keine Dublette zu BUG-34 (iOS-Overlay-Zoom, anderer Mechanismus).

---

**Implementation Spec**

**Root Cause (verifiziert am Code):**
📎 Code-Verifikation: `web/index.html` (`MapView.init`, `WeatherMap.setMode`/`_render`) + `backend/calculations/weather.py` (`fetch_weather_grid`) gelesen am 2026-06-30.
- Bestätigt: Die Karte startet fix auf Berlin, Zoom 10 — `MapView.init` ruft `L.map('map', …).setView([52.52, 13.40], 10)` (web/index.html). Bei Zoom 10 ist eine Gitterzelle (1,0° breit) breiter als das Kartenfenster.
- Bestätigt: Das Gitter spannt ganz Deutschland — `fetch_weather_grid` erzeugt ein 10×10-Raster über `lat_min=47.3, lat_max=55.0, lon_min=6.0, lon_max=15.0` (weather.py). Die Gitterpunkte liegen Kante-an-Kante (`r/(rows-1)`), Schrittweite lat ≈ 0,856°, lon = 1,0°.
- Bestätigt: `WeatherMap._render` zeichnet pro Punkt ein `L.rectangle` von `pt ± dLat/2` bzw. `pt ± dLon/2`. Dadurch reichen die äußersten Rechtecke je eine halbe Zelle über die nominale BBox hinaus — die **tatsächliche Mosaik-Hülle** ist ca. 46,87°N–55,43°N, 5,5°E–15,5°E. Diese erweiterte Hülle muss `fitBounds` umfassen, sonst werden Randzellen wieder beschnitten.
- Bestätigt: `WeatherMap.setMode` ändert die Kartenansicht **nicht** — es fetcht, rendert, aktualisiert Slider/Legende, aber kein `setView`/`fitBounds`. Genau hier fehlt der Zoom-Out.
- Widerlegt: kein Render-/Daten-/Safari-Fehler. Alle 100 Rechtecke liegen korrekt im DOM (vom Intake bereits belegt), nur außerhalb des Sichtfensters.

**Scope:**
- Eingeschlossen: Beim Wechsel auf einen Wetter-Modus (Wolken/Niederschlag) zoomt die Karte automatisch so weit heraus, dass das gesamte Deutschland-Mosaik sichtbar ist. Beim Zurückschalten auf „aus" kehrt die Karte zur Ansicht zurück, die vor dem ersten Einschalten aktiv war (Mittelpunkt + Zoomstufe).
- Eingeschlossen: Nur die Web-App (`web/index.html`). Reines Frontend-Verhalten, keine Backend-/API-Änderung.
- Ausgeschlossen: iOS-Overlay (BUG-34, anderer Mechanismus). Keine Änderung an Gittergröße, Auflösung, Farben oder am `/weather-map`-Endpoint. Kein automatisches Mitschwenken bei Moduswechsel Wolken↔Niederschlag (Ansicht bleibt dort einfach stehen).

**Akzeptanzkriterien:**
- [x] Wenn ich auf der Karte (Start: Berlin, nah herangezoomt) „Wolken" oder „Niederschlag" einschalte, ist sofort das vollständige farbcodierte Deutschland-Mosaik als zusammenhängende Fläche sichtbar — keine senkrechte Linie, kein abgeschnittener Rand.
- [x] Auch die Zellen an den Rändern (Nord/Süd/Ost/West-Kante Deutschlands) sind vollständig sichtbar, nicht halb vom Kartenfenster abgeschnitten.
- [x] Wenn ich danach wieder auf „aus" schalte, ist die Karte exakt da, wo sie vor dem Einschalten war (gleicher Ausschnitt von Berlin, gleiche Zoomstufe).
- [x] Edge Case: Schalte ich direkt von „Wolken" auf „Niederschlag" (ohne zwischendurch „aus"), bleibt das Gesamtdeutschland-Mosaik sichtbar; beim späteren „aus" lande ich trotzdem bei der ursprünglichen Berlin-Ansicht (die gemerkte Ansicht wird beim zweiten Einschalten nicht überschrieben).
- [x] Edge Case: Habe ich während aktivem Overlay manuell in eine Region gezoomt und schalte dann „aus", kehrt die Karte zur ursprünglichen Berlin-Ansicht zurück (nicht zu meinem manuellen Zwischen-Zoom) — die gemerkte Ansicht ist die VOR dem Einschalten.

**Pre-Mortem:**
- 💀 Szenario: Beim Ausschalten springt die Karte an einen falschen Ort / unerwarteten Zoom. → Auslöser: Vorherige Ansicht wird beim *zweiten* Einschalten überschrieben oder gar nicht erst gemerkt. → Gegenmaßnahme: Ansicht nur merken, wenn vorher `mode === 'off'` war (also genau beim Übergang aus → an); im Zustand `_savedView` halten und beim Übergang an → aus wiederherstellen + zurücksetzen. In AK 3+4 verankert.
- 💀 Szenario: Beim Moduswechsel Wolken→Niederschlag zoomt die Karte erneut auf Gesamtdeutschland und reißt den Nutzer aus seinem aktuellen Ausschnitt. → Auslöser: `fitBounds` läuft bei jedem `setMode(!= off)`. → Gegenmaßnahme: `fitBounds` nur beim Übergang aus → an ausführen, nicht bei an → an. In AK 4 verankert.
- 💀 Szenario: `fitBounds` auf die nominale BBox schneidet die Randzellen ab, weil die Rechtecke eine halbe Zelle über die BBox hinausragen. → Auslöser: Falsche Bounds (nominal 47.3/55.0/6.0/15.0 statt erweiterter Hülle). → Gegenmaßnahme: `fitBounds` auf die erweiterte Hülle (BBox ± halbe Zellbreite) oder mit ausreichendem `padding`. In AK 2 verankert (Test-Probe: äußerste Zellen vollständig sichtbar).
- 💀 Szenario: Auf mobilem Safari mit Animation wirkt der Sprung ruckelig oder `fitBounds` feuert vor Tile-Layout. → Auslöser: Animations-Timing / Karte noch nicht „settled". → Gegenmaßnahme: `fitBounds` mit definiertem Verhalten (z.B. `animate:false` oder kurze Animation) nach `_ensurePane()`/vor `_render()`; Memory `reference_frontend_dom_gotchas` (auf `leaflet-container` warten) beachten. Manueller Test auf Safari mobil.
- 💀 Szenario: Overlay ist beim Tab-Wechsel schon an, Nutzer verlässt Karte und kommt zurück — gemerkte Ansicht ist verloren oder doppelt gespeichert. → Auslöser: Zustand `_savedView` lebt nur im WeatherMap-Objekt, kein reaktives Binding. → Gegenmaßnahme: Zustand robust im WeatherMap-Objekt halten; Verhalten ist „best effort" für diese Sitzung, kein Persistieren über Reload nötig (Scope). Im Test einmal Tab wechseln + zurück prüfen.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (Rules: Einschalten → fitBounds auf erweiterte Deutschland-Hülle; Ausschalten → vorherige Ansicht; Merken nur beim Übergang aus→an).
- [x] Pre-Mortem durchgeführt (5 Szenarien, Gegenmaßnahmen in AKs verankert).
- [x] Architektur analysiert: `web/index.html` — `WeatherMap.setMode` (Zoom-Logik fehlt hier), `WeatherMap` Zustand (neues Feld `_savedView`), `MapView.map`/`MapView.init` (Start Berlin Zoom 10). Backend `weather.py:fetch_weather_grid` nur als Bounds-Quelle gelesen (keine Änderung).
- [x] Implementierungsoptionen: A / B
- [x] Empfehlung: Option A

**Implementierungsoptionen:**

### Option A — Zoom-Logik in `WeatherMap.setMode` (Ansicht merken/wiederherstellen)
- App-Wirkung: Beim ersten Einschalten merkt sich die App die aktuelle Berlin-Ansicht und zoomt sanft auf ganz Deutschland; beim Ausschalten kehrt sie genau dorthin zurück. Genau das im Lösungsansatz beschriebene Verhalten.
- Vorgehen: In `WeatherMap` ein Feld `_savedView` ergänzen. In `setMode(mode)`: beim Übergang `off → (clouds|precip)` `this._savedView = {center: MapView.map.getCenter(), zoom: MapView.map.getZoom()}` setzen und `MapView.map.fitBounds([[46.87, 5.5],[55.43, 15.5]], {padding:[20,20]})` (erweiterte Hülle = BBox ± halbe Zellbreite) ausführen. Beim Übergang `(clouds|precip) → off` `fitBounds`/`setView` auf `_savedView` zurück und `_savedView = null`. Bounds als benannte Konstante (`_GRID_VIEW_BOUNDS`) ableitbar aus BBox 47.3/55.0/6.0/15.0 ± halbe Schrittweite (≈ ±0,428° lat, ±0,5° lon).
- Betroffene Dateien: `web/index.html` (nur `WeatherMap`-Block, ~15 Zeilen).
- Vorteile: Lokal in der zuständigen Komponente; nutzt vorhandenes `MapView.map`; minimaler Eingriff; gut testbar; respektiert „kein reaktives Binding" (expliziter Zustand).
- Nachteile / Risiken: Übergangslogik (aus→an vs. an→an) muss korrekt sein, sonst Pre-Mortem-Szenario 1/2. Bounds müssen die erweiterte Hülle treffen.
- Aufwand: klein.

### Option B — Gitter-Bounds dynamisch aus den geladenen Daten berechnen
- App-Wirkung: Identisch für den Nutzer, aber die Zoom-Fläche wird aus den tatsächlich vom Server gelieferten Gitterpunkten berechnet statt aus festen Werten.
- Vorgehen: Wie A, aber statt fester Bounds aus `this.data.grid` das Min/Max von lat/lon ableiten und um `dLat/2`/`dLon/2` erweitern (dieselben Werte, die `_render` schon berechnet). `fitBounds` auf diese berechneten Bounds.
- Betroffene Dateien: `web/index.html` (`WeatherMap`-Block).
- Vorteile: Bounds bleiben automatisch korrekt, falls die Gittergröße/Auflösung im Backend je geändert wird — keine doppelte Wahrheit zwischen Backend-BBox und Frontend-Konstante.
- Nachteile / Risiken: Hängt davon ab, dass `this.data` beim ersten `setMode` schon geladen ist (ist es — `_fetch()` läuft davor in `setMode`); etwas mehr Logik; bei `data === null` (Fetch-Fehler) braucht es einen Fallback auf feste Bounds.
- Aufwand: klein–mittel.

✅ Empfehlung: **Option A** — kleinster, klarster Eingriff, der genau den im Ticket beschriebenen Lösungsansatz umsetzt; die Backend-BBox ist seit US-72 stabil und unwahrscheinlich variabel, daher überwiegt Einfachheit. Die robuste Idee aus B (Bounds aus Daten) kann als interner Kommentar vermerkt werden, falls die Auflösung später konfigurierbar wird. Empfehlung mit Fallback-Hinweis: Bounds als benannte Konstante ablegen, damit eine spätere Synchronisierung mit dem Backend trivial bleibt.

**Entscheidung (Weg-Gate, 2026-06-30): Option B gewählt** — abweichend von der Analyse-Empfehlung (A). Grund: Stephan plant, die App demnächst auch in Norwegen, Dänemark und Italien zu nutzen. Der Zoom soll sich automatisch an das jeweils geladene Wetter-Gebiet anpassen, statt feste Deutschland-Eckwerte zu verwenden. Umsetzung daher: Zoom-Fläche aus `this.data.grid` ableiten (Min/Max von lat/lon, erweitert um `dLat/2`/`dLon/2` — dieselben Werte wie in `_render`), mit Fallback auf feste Deutschland-Hülle, falls `this.data` beim Einschalten nicht geladen ist. **Hinweis:** Damit überhaupt Wetter für andere Länder erscheint, muss separat die Backend-Grid-BBox erweitert werden (eigenes Ticket) — nicht Teil von BUG-55.

**Testplan:**
- [ ] Automatisiert (Harness): Reines Leaflet-/DOM-Zoomverhalten ist clientseitig und nicht über `pytest`/`backend/tests/` abdeckbar. Bestehende `test_us72_weather_map.py` (Backend-Grid + BBox 47.3/55.0/6.0/15.0) muss weiterhin grün bleiben (Regression: BBox-Konstanten unverändert). Kein neuer Backend-Test nötig, da keine Backend-Änderung.
- [ ] Manuell (unter http://localhost:8000):
  1. Karten-Tab öffnen (startet auf Berlin, nah). „Wolken" tippen → Erwartung: ganz Deutschland als zusammenhängendes Farb-Mosaik sichtbar, inkl. Rändern (AK 1+2).
  2. „aus" tippen → Erwartung: zurück auf den ursprünglichen Berlin-Ausschnitt + Zoom (AK 3).
  3. „Wolken" → ohne „aus" direkt „Niederschlag" → Erwartung: Mosaik bleibt auf Gesamtdeutschland; danach „aus" → zurück auf Berlin (AK 4).
  4. „Wolken" einschalten, manuell in eine Region zoomen, dann „aus" → Erwartung: zurück auf ursprüngliche Berlin-Ansicht, nicht auf den Zwischen-Zoom (AK 5).
  5. Auf Safari mobil wiederholen (Animation/Timing prüfen).
  6. Regression (PRODUCT.md §12, Karten-/CSS-Bereich): Marker, Layer-Umschaltung (Nacht/Standard/Satellit), GPS-Button, Slider + Legende des Overlays weiterhin funktionsfähig.

---

**❌ ZURÜCKGEZOGEN (2026-06-30): Diese Open-Meteo-Mehrländer-Erweiterung wird NICHT released.** Stephan hat entschieden, stattdessen auf echte Modelldaten (DWD ICON-D2 + MET Norway) mit weichem Verlauf umzustellen — siehe **US-112**. BUG-55 liefert nur den getesteten Zoom-Fix; die folgende Erweiterungs-Beschreibung bleibt als Historie stehen, ist aber nicht Teil des Release.

**🔧 Scope-Erweiterung (verworfen — siehe oben, ersetzt durch US-112):**

Der Zoom-Fix (Option B) ist bereits getestet ✅. Zusätzlich gewünscht: feineres Wetter-Gitter + mehrere Länder. **Weg 2** gewählt: pro Land ein eigenes feines Raster (~50 km Kantenlänge statt heute ~85 km), zu einem Overlay zusammengesetzt; über offenem Meer bleibt die Karte leer.

**Gebiete (Stephan bestätigt):**
| Land | BBox (lat_min–lat_max, lon_min–lon_max) | ca. Raster |
|------|------------------------------------------|-----------|
| Deutschland | 47.3–55.0 °N, 6.0–15.0 °E | 17×13 |
| Österreich | 46.3–49.1 °N, 9.5–17.2 °E | 7×12 |
| Italien (Norden: Alpen/Dolomiten/Toskana) | 42.7–47.1 °N, 6.6–13.8 °E | 10×12 |
| Norwegen (Süd bis Lofoten/Nord) | 58.0–69.5 °N, 4.5–16.0 °E | 26×12 |

(Rastergrößen Richtwert für ~50 km; Implementierer darf leicht anpassen. Summe ~740 Punkte — innerhalb des Open-Meteo-Limits ~1000, aber pro Land separater Request empfohlen wegen URL-Länge/Robustheit.)

**Datenvertrag (Backend → Frontend):** Jeder Gitterpunkt erhält zusätzlich seine eigene Zellgröße `dlat`/`dlon` (da die Länder unterschiedliche Rasterweiten haben). Das Frontend zeichnet jede Kachel mit der punkteigenen Größe statt einer global aus `grid[1]`/`grid[10]` berechneten — Fallback auf die alte globale Berechnung, falls `dlat`/`dlon` fehlen. `hourly_times` über alle Länder identisch (gleiche `forecast_days`, UTC) — erstes Land als Zeitachse. Fehlgeschlagenes Land → null-Werte nur für dessen Punkte, andere bleiben.

**Akzeptanzkriterien (Erweiterung):**
- [ ] Schalte ich „Wolken"/„Niederschlag" ein, sehe ich farbige Kacheln über Deutschland, Österreich, Norditalien und Norwegen (bis hoch zu den Lofoten) — und die Karte zoomt automatisch so weit raus, dass alle vier Gebiete zusammen ins Bild passen.
- [ ] Die Kacheln sind sichtbar kleiner/feiner als vorher (mehr, kleinere Felder je Land).
- [ ] Über offenem Meer zwischen den Ländern bleibt die Karte frei (keine Farbflächen wo keine Daten sind).
- [ ] Der Stunden-Schieber verändert weiterhin alle Gebiete gleichzeitig; die Zeitanzeige stimmt.
- [ ] Fällt der Wetterabruf für ein Land aus, bleiben die anderen Länder trotzdem eingefärbt.

**Betroffen:** `backend/calculations/weather.py` (Mehr-Gebiete-Gitter + `dlat`/`dlon` je Punkt), `backend/main.py` (`/weather-map` ruft das Mehr-Gebiete-Gitter), `web/index.html` (`WeatherMap._render` nutzt punkteigene Zellgröße). Keine Farb-/Slider-/Legenden-Logik ändern.

---

### BUG-53 · Feed zeigt Location-Namen mit vorangestelltem 📍-Emoji `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-29 |
| **Abgeschlossen** | 2026-06-29 |

**Beschreibung:** Nachdem neue Locations angelegt wurden, erscheinen die Location-Namen im 14-Tage-Feed mit einem vorangestellten 📍-Emoji direkt im Namen (z. B. „Mondaufgang – 📍 Alter Hafen Potsdam"). Das Emoji soll nicht Teil des gespeicherten Location-Namens sein — es wird im UI separat ergänzt. Vermutlich wird beim Speichern neuer Locations das 📍 fälschlicherweise in den `name`-Wert geschrieben und persistiert. Erwartetes Verhalten: Der Location-Name enthält kein Emoji; das UI rendert ggf. ein Emoji dekorativ, aber nicht dauerhaft gespeichert im Namen.

**Bezug:** Kein direktes Vorgänger-Ticket. Möglicherweise Zusammenhang mit US-106 (neue Locations anlegen), falls das Add-Formular oder der Preview-Alignment-Endpoint das Emoji in den Namen übernimmt.

---

**Implementation Spec**

**Root Cause (verifiziert):**
In `backend/main.py`, Zeile 1752, wird beim Speichern einer neuen Location via `/preview-alignment`-Endpoint der Name so gesetzt:

```python
name=f"📍 {req.subject_name}",
```

Das 📍-Emoji ist fest in den gespeicherten `name`-Wert eingebaut. Da dieser Name in der Datenbank persistiert wird und als `location_name` in Feed-Einträge fließt, erscheint das Emoji dauerhaft im Feed-Titel (z. B. „Mondaufgang – 📍 Alter Hafen Potsdam").

**Example Mapping**

*Regel:* Der in der Datenbank gespeicherte Location-Name enthält kein Emoji. Dekorative Icons werden ausschließlich im UI ergänzt, nicht im Datensatz.

*Positiv-Beispiel:* Eine Basis-Location wie „Berliner Dom vom Spreeufer" erscheint im Feed als „Mondaufgang – Berliner Dom vom Spreeufer" — kein Emoji im Titel.

*Negativ-Beispiel (Bug):* Eine via Quick Location Capture angelegte Location mit `subject_name = "Alter Hafen Potsdam"` wird als `name = "📍 Alter Hafen Potsdam"` gespeichert. Im Feed erscheint: „Mondaufgang – 📍 Alter Hafen Potsdam".

*Edge-Case:* Bereits in der DB gespeicherte Custom Locations tragen das Emoji bereits im Namen. Diese müssen nachträglich bereinigt werden (einmalige Migration beim Start oder per Patch-Endpoint).

**Pre-Mortem**

- Bereits in SQLite gespeicherte Custom Locations haben das Emoji im Namen — ein reiner Backend-Fix bereinigt sie nicht automatisch.
- Beim Lesen aus SQLite werden die Namen unverändert zurückgegeben — eine reine Frontend-Bereinigung wäre Workaround, nicht Ursachen-Fix.
- Falls anderswo im Code das 📍 als Präfix für Custom Locations erwartet wird (z. B. zur Unterscheidung), bricht die Änderung diese Logik.
- Alte Feed-Caches (opportunities.json) können das Emoji noch enthalten — nach Fix neu precomputen oder Cache invalidieren.

**Akzeptanzkriterien**

1. Wenn ich über Quick Location Capture eine neue Location anlege und den Namen „Alter Hafen Potsdam" eingebe, erscheint diese Location im 14-Tage-Feed als „Mondaufgang – Alter Hafen Potsdam" — ohne 📍 im Titel.
2. Wenn ich im Locations-Tab die neu angelegte Location öffne, steht im Detail-Header ebenfalls kein 📍 vor dem Namen.
3. Wenn ich die Location-Liste per `/locations`-API abrufe, enthält das `name`-Feld kein vorangestelltes 📍-Emoji.
4. Bereits bestehende Custom Locations mit 📍 im Namen werden beim Server-Start (oder per Migration) automatisch bereinigt, sodass auch diese im Feed ohne Emoji erscheinen.
5. Bestehende Basis-Locations (ohne Custom-Prefix) sind nach dem Fix unverändert.

**Implementierungsoptionen**

*Option A — Fix im Backend (Empfehlung): Emoji beim Speichern entfernen*
In `backend/main.py`, Zeile 1752: `name=f"📍 {req.subject_name}",` → `name=req.subject_name,`.
Zusätzlich: Einmalige DB-Migration, die bestehende Custom Location-Namen von führendem „📍 " bereinigt (z. B. `UPDATE locations SET name = REPLACE(name, '📍 ', '') WHERE id LIKE 'custom_%'`).
Vorteil: Ursache beseitigt, saubere Datenbasis, kein Workaround.

*Option B — Fix im Frontend: Emoji beim Anzeigen herausfiltern*
Im Feed-Renderer und im Detail-Header per JS `name.replace(/^📍\s*/, '')` entfernen.
Nachteil: Workaround, Daten bleiben verschmutzt, jede neue Anzeige-Stelle muss ebenfalls gefiltert werden. Nicht empfohlen.

*Option C — Fix im Formular-Input: Emoji gar nicht erst eintragen*
Das Formular (falls vorhanden) oder der API-Caller sendet kein Emoji. Greift aber nicht für die serverseitige Konstruktion in `main.py` und ist daher unvollständig.

**Empfehlung: Option A** — direkte Ursachenbeseitigung im Backend. Einzeiliger Fix + einmalige DB-Migration. Kein Workaround, keine Folgeprobleme bei neuen UI-Stellen.

### US-106 · Geänderte oder neue Location sofort komplett nutzbar `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |
| **Abgeschlossen** | 2026-06-28 |

**Beschreibung:** Wenn ich die Position einer Location verschiebe oder eine neue Location hinzufüge, möchte ich diese Location innerhalb kurzer Zeit überall in der App vollständig und korrekt sehen — nicht erst am nächsten Morgen oder nach Stunden. Heute erscheinen die kommenden Foto-Chancen für diese Location zwar schon zügig, aber an drei Stellen hinkt die App noch hinterher: das Wetter zur Chance, die Empfehlungen im Entdecken-Bereich und Fälle, in denen gerade eine große Hintergrund-Aktualisierung läuft. Ziel: nach einer Standort-Änderung ist die Location ohne weiteres Zutun überall sofort richtig.

**Teilpunkte (drei erlebbare Lücken, die geschlossen werden sollen):**
1. **Wetter sofort statt mit Verzögerung:** Direkt nach der Standort-Änderung zeigen die neuen Foto-Chancen dieser Location auch das passende Wetter an — nicht erst nach bis zu drei Stunden. Bis das echte Wetter geladen ist, ist erkennbar, dass es gerade nachgeladen wird, statt eine falsche oder leere Wetterangabe zu zeigen.
2. **Im Entdecken-Bereich sofort dabei:** Die geänderte oder neu angelegte Location taucht zeitnah auch im Entdecken-/Vorschlags-Bereich auf — nicht erst am nächsten Morgen.
3. **Keine still verlorenen Änderungen bei laufender großer Berechnung:** Verschiebe oder ergänze ich eine Location, während im Hintergrund gerade eine große Aktualisierung läuft, geht meine Änderung nicht verloren. Sie wird automatisch nachgeholt, sobald die große Berechnung fertig ist, und der Hinweis in der App bleibt so lange ehrlich („wird noch aktualisiert"), bis die Location wirklich fertig durchgerechnet ist.

**Bezug:**
- **TASK-12** (erledigt, v1.4.2) — hat die sofortige Neuberechnung der Foto-Chancen (14-Tage-Feed + Jahreskalender) für die geänderte Location eingeführt. US-106 baut direkt darauf auf und schließt die drei verbliebenen Lücken (Wetter, Entdecken, laufende Großberechnung). Direkte Abhängigkeit/Erweiterung.
- **US-77** (offen) — neue Locations zentral im Backend anlegen + Merge. Grenzt an, betrifft aber das *Anlegen/Zusammenführen* von Locations, nicht die *Aktualität der abgeleiteten Daten*. Getrennt halten.
- Merge/Split-Empfehlung: **Ein US mit drei klar benannten Teilpunkten** (so angelegt). Split in drei Tickets ist möglich, falls die Teile getrennt freigegeben/getestet werden sollen — empfohlen nur, wenn der Entdecken-Teil (2) deutlich später kommen soll als Wetter (1) und der Nachhol-Mechanismus (3).

---

#### 🔬 Implementation Spec (Analyse 2026-06-28)

**📎 Code-Verifikation** (gelesen am 2026-06-28):
- `backend/main.py` — `_run_precompute_single` (~Z.491): bei `if _precompute_running` (~Z.506) **Skip ohne Retry**; ID bleibt in `_recompute_pending`, wird aber nur durch `_load_caches` (~Z.310) gelöscht, *wenn die Location im Feed-Cache auftaucht* — ohne Recompute taucht sie dort aber nicht neu auf → Banner hängt bis Timeout. **Bestätigt.**
- `_weather_overlay` (~Z.350): **voller** Overlay über *alle* Unique-Locations in T+3, Cron alle 3h, Forecast `days=7`, Key = gerundetes `lat,lon` (3 Nachkommastellen). Single-Recompute schreibt nur Platzhalter `weather_score=0.0` (`backend/precompute.py` Z.396, Kommentar „wird zur Laufzeit durch Wetter-Overlay ersetzt"). **Bestätigt.**
- **Pending-Cleanup-Lücke bestätigt:** `_load_caches` entfernt die ID aus `_recompute_pending`, sobald sie im Feed-Cache ist — das passiert nach dem Feed/Kalender-Write, aber **bevor** das Wetter aufgespielt ist. Banner verschwindet also, während die Wetterangabe noch `0` (Platzhalter) ist.
- `backend/discover/pipeline.py` — `run_pipeline(days)` / `refresh_discover_cache(cache_path)` nehmen **keinen** `location_id`. Scout existiert **nur als Volllauf** (Mond- + Sonnen-Pipeline parallel über alle Locations). **Kein inkrementeller Einzel-Pfad vorhanden — bestätigt.** Cron 05:45 + Startup + POST `/refresh-discover`. Wird bei Location-Änderung **nicht** getriggert.
- `precompute.py` läuft als **eigener Subprozess** und lädt LOCATIONS + Overrides + (BUG-29/33) selbst; der Scout läuft dagegen **im Server-Prozess** → sieht live LOCATIONS inkl. Custom. **Bestätigt.**
- Hinweis: `precompute.py` nutzt bereits `str | None` (Z.611) — Prod-Python 3.9 verträgt das in einem separat gestarteten Subprozess offenbar (bestehender Code); neuer Code in `main.py`/`pipeline.py` bleibt vorsichtshalber 3.9-konform.

**Scope:**
- Eingeschlossen: (1) Wetter sofort für die geänderte/neue Location inkl. ehrlichem „wird nachgeladen"-Zustand; (2) geänderte/neue Location zeitnah im Entdecken-Bereich; (3) keine still verworfene Einzel-Neuberechnung bei laufendem Großlauf — automatisches Nachholen + ehrliches Banner bis *wirklich* fertig (Feed+Kalender+Wetter).
- Ausgeschlossen: Anlegen/Merge von Locations selbst (US-77); generelle Wetter-Genauigkeit/Provider-Wechsel; Push-Benachrichtigungen zu neuen Chancen; iOS-App (nur Web).

**Example Mapping:**

📏 **Regel 1 — Wetter folgt der Location sofort.** Nach einer Standort-Änderung wird das Wetter für genau diese Location zeitnah nachgeladen; bis dahin zeigt die App ehrlich „wird nachgeladen" statt einer falschen oder leeren Wetterangabe.
- 🟢 *Positiv:* Stephan verschiebt eine Location → kurz darauf zeigen ihre kommenden Chancen echte Wetterwerte (Temperatur, Bewölkung), ohne dass er etwas tut oder bis zu 3 h wartet.
- 🔴 *Negativ:* Während das Wetter noch lädt, darf **keine** Chance dieser Location einen ausgedachten oder leeren Wert (z. B. „0 %"/„–" als wäre es echtes Ergebnis) als fertiges Wetter darstellen — stattdessen klar als „lädt" erkennbar.
- ⚙️ *Edge:* Chance liegt weiter als 3 Tage in der Zukunft → dort gibt es planmäßig noch kein Wetter (Forecast reicht nur ~7 Tage); das ist kein Fehler und muss als „noch kein Wetter" (nicht als „lädt ewig") erkennbar bleiben.

📏 **Regel 2 — Entdecken zieht zeitnah nach.** Eine geänderte oder neu angelegte Location erscheint im Entdecken-/Vorschlags-Bereich zeitnah nach der Änderung, nicht erst am nächsten Morgen.
- 🟢 *Positiv:* Stephan legt eine neue Location an → wenig später taucht sie (sofern sie eine relevante Chance hat) im Entdecken-Bereich auf.
- 🔴 *Negativ:* Stephan macht 5 Änderungen kurz hintereinander → es wird **nicht** 5× ein teurer Volllauf gestartet (kein Doppel-/Mehrfach-Lauf, der den Server blockiert).
- ⚙️ *Edge:* Die geänderte Location hat im betrachteten Zeitraum keine entdeckenswerte Chance → sie taucht korrekterweise *nicht* auf (kein leerer Platzhalter-Eintrag).

📏 **Regel 3 — Keine still verlorene Änderung.** Läuft beim Ändern gerade eine große Hintergrund-Berechnung, wird die Einzel-Neuberechnung automatisch nachgeholt; der Hinweis bleibt ehrlich, bis die Location wirklich vollständig (Chancen + Kalender + Wetter) fertig ist.
- 🟢 *Positiv:* Stephan ändert eine Location, während nachts/morgens gerade der Großlauf läuft → der Hinweis „wird noch aktualisiert" bleibt sichtbar, und sobald der Großlauf fertig ist, wird seine Location automatisch nachberechnet; danach verschwindet der Hinweis und alles stimmt.
- 🔴 *Negativ:* Der Hinweis verschwindet **nicht**, solange noch der Platzhalter-Wetterwert (statt echtem Wetter) angezeigt würde.
- ⚙️ *Edge:* Der Großlauf bricht mit Fehler ab → die nachzuholende Änderung wird trotzdem angestoßen (oder der Hinweis wird ehrlich auf „wird mit der nächsten Berechnung aktualisiert" gesetzt) — sie verschwindet nicht stillschweigend ohne Ergebnis.

❓ **Offene Entscheidungen (vor Umsetzung):**
1. **Scout-Trigger-Strategie (Teil 2):** Volllauf nach jeder Änderung mit Entprellung (z. B. 60–120 s zusammenfassen) — vs. den Scout erst beim nächsten Cron/Startup. Empfehlung unten ist „debounced Volllauf". Bestätigen?
2. **„Zeitnah" konkret (Teil 1 & 2):** Reicht „innerhalb weniger Minuten" als gefühlte Sofortigkeit, oder soll Wetter spürbar < 1 min und Entdecken < 2–3 min sein? (beeinflusst Debounce-Fenster)
3. **Banner-Wahrheit bei Wetter:** Soll der Hinweis erst verschwinden, wenn auch das Wetter steht (empfohlen) — das macht das Banner für ~Sekunden länger sichtbar. OK?

**Akzeptanzkriterien (erlebbares App-Verhalten):**
- [ ] Nach dem Verschieben einer Location zeigen ihre kommenden Foto-Chancen (innerhalb der nächsten 3 Tage) ohne weiteres Zutun echte Wetterangaben — ohne dass Stephan bis zu 3 Stunden warten oder manuell „Wetter aktualisieren" drücken muss.
- [ ] Solange das echte Wetter noch geladen wird, ist das an der Chance klar als „wird nachgeladen" erkennbar — es erscheint kein ausgedachter oder leerer Wert, der wie ein fertiges Ergebnis aussieht.
- [ ] Eine Chance, die weiter als ~3 Tage in der Zukunft liegt, zeigt verständlich „noch kein Wetter" und nicht endlos „wird geladen".
- [ ] Eine neu angelegte oder verschobene Location taucht zeitnah (wenige Minuten) im Entdecken-Bereich auf, sofern sie dort eine relevante Chance hat — nicht erst am nächsten Morgen.
- [ ] Mehrere Änderungen kurz hintereinander führen nicht dazu, dass die App spürbar langsamer/blockiert wird (keine mehrfachen parallelen Großberechnungen).
- [ ] Ändere ich eine Location, während gerade eine große Hintergrund-Aktualisierung läuft, bleibt der Hinweis „wird noch aktualisiert" sichtbar und meine Änderung wird automatisch nachgeholt; danach stimmen Chancen, Kalender und Wetter für diese Location.
- [ ] Der Hinweis „wird noch aktualisiert" verschwindet erst, wenn die Location wirklich vollständig fertig ist — inklusive echtem Wetter, nicht schon beim Platzhalter.
- [ ] Edge: Schlägt die große Berechnung fehl, verschwindet meine Änderung nicht spurlos — sie wird angestoßen oder der Hinweis sagt ehrlich, dass sie mit der nächsten Berechnung kommt.

**Pre-Mortem:**
- 💀 *Race zwischen Einzel- und Großlauf — Änderung verpufft.* Auslöser: `_precompute_running`-Skip ohne Retry; ID bleibt pending, wird aber nie aufgelöst. Frühwarnung: Banner hängt bis 10-min-Timeout, Feed bleibt stale. → Gegenmaßnahme: am Ende jedes Laufs (`_run_precompute` **und** `_run_precompute_single`) `_recompute_pending` abarbeiten (Nachhol-Schleife), sequenziell, mit Schutz gegen Endlos-Rekursion. (AK „automatisch nachgeholt").
- 💀 *Banner lügt — verschwindet vor dem Wetter.* Auslöser: `_load_caches` löscht Pending-ID, sobald Location im Feed ist (vor Wetter-Overlay). Frühwarnung: Wetter zeigt 0/„–" obwohl Banner weg. → Gegenmaßnahme: Pending-ID erst freigeben, wenn auch das Wetter für die Location aufgespielt ist (separater „weather_pending"-Zustand oder Reihenfolge: erst Wetter-für-Location, dann Pending clear). (AK „Hinweis erst weg wenn wirklich fertig").
- 💀 *Scout-Volllauf bei jeder Änderung — Server überlastet / doppelte Läufe.* Auslöser: naiver Trigger pro PATCH; Volllauf ist teuer (zwei Pipelines über alle Locations). Frühwarnung: mehrere parallele Scout-Läufe, hohe CPU, langsame Antworten. → Gegenmaßnahme: Entprellung (Debounce-Fenster) + Single-Flight-Guard (kein zweiter Lauf, solange einer läuft; stattdessen „dirty"-Flag, das einen Nachlauf auslöst). (AK „keine mehrfachen parallelen Berechnungen").
- 💀 *Doppelte Wetter-Fetches / Rate-Limit beim Provider.* Auslöser: gezielter Single-Overlay + paralleler 3h-Cron-Overlay holen dieselben Koordinaten doppelt. Frühwarnung: Wetter-API-Fehler/Drosselung im Log. → Gegenmaßnahme: Single-Overlay nur für die *eine* Location (deren Key), Wetter-Cache wiederverwenden; kein Voll-Overlay anstoßen.
- 💀 *UTC/Ortszeit-Verwechslung beim „T+3"-Fenster.* Auslöser: Cache-Zeiten sind UTC, „nächste 3 Tage" muss in UTC gerechnet werden (wie bestehender Code). Frühwarnung: Wetter fehlt für Chancen am Tagesrand. → Gegenmaßnahme: bestehende UTC-Logik aus `_weather_overlay` wiederverwenden, nicht neu in Ortszeit rechnen.

**Architektur (betroffen):**
- `backend/main.py`: `_run_precompute_single` (Skip→Nachhol-Logik), `_load_caches` (Pending-Clear-Zeitpunkt), `_weather_overlay` (gezielte Single-Location-Variante), `_refresh_discover` (Debounce-Trigger), `/recompute-status` (Wetter-Readiness mit aufnehmen), Trigger-Stellen PATCH `/locations/{id}` (~Z.1490) + `_save_alignment_as_location` (~Z.1321).
- `backend/discover/pipeline.py`: ggf. `run_pipeline`/`refresh_discover_cache` um optionalen Single-Flight/Trigger; **kein** echter Inkrement-Pfad vorhanden (Volllauf bleibt).
- `web/index.html`: `startPendingPoll` (~Z.1487, Banner-Lebensdauer an Wetter-Readiness koppeln), Wetter-Anzeige (Z.1374/3335/3355 — „lädt"-Zustand statt 0).

**Implementierungsoptionen + Empfehlung**

*Teil 1 — Wetter sofort:*
- **Option A (empfohlen): Gezielter Single-Location-Wetter-Overlay.** Nach erfolgreichem Single-Recompute nur das Wetter für genau diese eine Location nachladen (deren `lat,lon`-Key), Pending erst danach freigeben. App-Wirkung: Wetter steht in Sekunden für die geänderte Location, ohne alle anderen anzufassen. Aufwand: mittel.
- Option B: vollen `_weather_overlay()` anstoßen. Einfacher (Funktion existiert), aber teuer (alle Locations) und riskiert doppelte Fetches/Rate-Limit. Aufwand: klein, aber schlechter skalierend.
- ✅ **Empfehlung A** — präzise, günstig, keine Fremd-Locations belastet; passt zum „nur diese Location wird neu"-Modell.

*Teil 2 — Entdecken sofort:*
- **Option A (empfohlen): Debounced Volllauf nach Änderung mit Single-Flight.** Da der Scout **nur** als Volllauf existiert, nach einer Änderung einen Scout-Refresh anstoßen, aber Änderungen über ein kurzes Zeitfenster zusammenfassen und nie parallel laufen lassen (läuft schon einer → „dirty" merken, danach genau ein Nachlauf). App-Wirkung: neue/geänderte Location erscheint in wenigen Minuten im Entdecken, auch bei mehreren schnellen Edits ohne Server-Überlast. Aufwand: mittel.
- Option B: echten inkrementellen Single-Location-Scout bauen (nur diese Location durch Mond-/Sonnen-Pipeline + Merge in discover.json). App-Wirkung identisch, günstiger pro Lauf — aber deutlich mehr Code (Merge-Logik, Pipeline-Refactor) und neue Fehlerquellen. Aufwand: groß.
- ✅ **Empfehlung A** — der Volllauf existiert und ist robust; Debounce+Single-Flight löst das Kostenproblem mit wenig Risiko. B nur, falls der Volllauf sich messbar als zu teuer erweist (dann eigenes Ticket).

*Teil 3 — Nachholen + ehrliches Banner:*
- **Option A (empfohlen): Pending-Queue mit Nachlauf am Lauf-Ende + Wetter-gekoppeltes Banner.** Jeder Recompute (Einzel/Groß) arbeitet am Ende offene `_recompute_pending`-IDs sequenziell ab; eine ID gilt erst als erledigt, wenn Feed **und** Wetter für sie stehen. `/recompute-status` meldet erst dann „fertig". App-Wirkung: keine verlorene Änderung, Banner bleibt ehrlich bis wirklich alles steht. Aufwand: mittel.
- Option B: nur einfacher Retry beim Skip (Single-Recompute später erneut versuchen, ohne Wetter-Kopplung). Weniger Code, aber Banner kann weiterhin vor dem Wetter verschwinden → verletzt AK. Aufwand: klein.
- ✅ **Empfehlung A** — schließt beide Lücken (verlorene Änderung **und** lügendes Banner) sauber; B löst nur die halbe Anforderung.

**Testplan:**
- Automatisiert (`backend/tests/test_us106.py`, Ticket-ID im Docstring), mit `FOTOALERT_NO_BACKGROUND` gesteuert:
  - Single-Recompute während simuliertem laufendem Großlauf (`_precompute_running=True`) → ID bleibt pending; nach „Lauf-Ende" wird sie abgearbeitet (Nachhol-Logik greift).
  - `/recompute-status` meldet die ID erst dann nicht mehr als pending, wenn Feed **und** Wetter für sie gesetzt sind (Wetter-Readiness im Status).
  - Single-Wetter-Overlay setzt `weather_score`/`weather_description` nur für die Ziel-Location, lässt andere unberührt; Chancen außerhalb T+3 bleiben „kein Wetter" (nicht „lädt").
  - Scout-Trigger: mehrere schnelle Änderungen → höchstens ein paralleler Lauf (Single-Flight), genau ein Nachlauf bei „dirty".
- Manuell (unter http://localhost:8000): (a) Location verschieben → binnen Sekunden echtes Wetter an den Chancen, Banner bleibt bis Wetter da ist; (b) neue Location anlegen → wenige Minuten später im Entdecken-Bereich; (c) Änderung während laufender Berechnung → Banner bleibt, danach automatisch korrekt. **Regressions-Matrix (PRODUCT.md §12, Backend/Cache-Typ):** Feed, Kalender, Entdecken, LocationDetail-Wetter, 3h-Wetter-Cron, nächtlicher Großlauf auf Seiteneffekte prüfen.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert (main.py / discover/pipeline.py / web/index.html)
- [x] Implementierungsoptionen je Teilpunkt: A / B
- [x] Empfehlung freigeben (Weg-Gate Stephan): Teil1=A, Teil2=A, Teil3=A
- [x] Offene Entscheidungen 1–3 klären

**✅ Stephan-Freigabe 2026-06-28:** Teil1=A (gezielter Single-Location-Wetter-Overlay), Teil2=A (debounced Scout-Volllauf + Single-Flight + dirty-Nachlauf), Teil3=A (Pending-Queue mit Nachlauf, Banner bleibt bis Wetter steht). Zielzeiten streng: Wetter < 1 Min, Entdecken < 2–3 Min. Banner verschwindet erst, wenn Feed UND Wetter für die Location stehen. Edge: schlägt der Großlauf fehl, geht die Änderung nicht spurlos verloren (Anstoß oder ehrliches „kommt mit der nächsten Berechnung").

**🔧 Nachbesserung 2026-06-28 (nach Lokaltest):** Im ersten Lokaltest dauerte das Nutzbar-Werden einer verschobenen Location fast 10 Minuten — nahezu komplett der 365-Tage-Kalender. Die sichtbaren Foto-Chancen standen schon nach ~4 Sekunden, der Jahres-Kalender brauchte aber ~10 Minuten und das „wird aktualisiert"-Banner hing so lange. Stephans Entscheidung: **„Feed + Wetter sofort, Kalender im Hintergrund."** Umgesetzt: Nach einer Standort-Änderung werden zuerst die sichtbaren Foto-Chancen und ihr Wetter berechnet — sobald beides steht, verschwindet das Banner (in Sekunden). Der vollständige Jahres-Kalender für diese Location wird danach im Hintergrund nachgerechnet, ohne das Banner aufzuhalten. Dass der Kalender-Tab dieser Location ein paar Minuten noch den alten Stand zeigt, ist bewusst akzeptiert. Schlägt die Wetter-Abfrage fehl, bleibt das Banner ehrlich stehen (Location bleibt offen für den nächsten Versuch); ein Fehler beim Hintergrund-Kalender nimmt die bereits erfolgte Freigabe nicht zurück.

> Zusatz-AK (Nachbesserung): Nach dem Verschieben einer Location verschwindet das „wird aktualisiert"-Banner in **Sekunden**, sobald die sichtbaren Foto-Chancen + ihr Wetter stehen — es wartet **nicht** mehr auf den vollständigen Jahres-Kalender. Der Jahres-Kalender dieser Location zieht im Hintergrund nach und darf dabei ein paar Minuten den alten Stand zeigen.


---

### US-98 · Bauhaus-Redesign (Epic) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story (Epic) |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-27 |
| **Abgeschlossen** | 2026-06-28 |

**Beschreibung:** Dach-Ticket für die schrittweise Übernahme des freigegebenen Bauhaus-Looks in die echte App: diszipliniertes Bauhaus-Blau mit Gold als Zweitakzent, einheitliches Linien-Icon-Set statt verspielter Emojis, kompaktere Buttons + kleinere Schrift, neue Logo-/App-Icon-Marke sowie automatischer Tag/Nacht-Modus. Reine Designänderung — keine funktionalen oder Panel-Änderungen, die nicht ausdrücklich spezifiziert sind. Quelle: FotoAlert/design/bauhaus/ (prototype.html, logo.svg, icons.svg).

**Kind-Tickets (empfohlene Reihenfolge):**
1. **US-99** — Theme-Tokens (Bauhaus-Palette hell+dunkel) · Foundation, zuerst
2. **US-97** — Automatischer Tag/Nacht-Modus + Umschalter · hängt von US-99
3. **US-100** — Einheitliches Linien-Icon-Set ersetzt Emojis
4. **US-101** — Kompaktere Buttons + kleinere Schrift
5. **US-102** — Bauhaus-Logo + App-Icon

**Bezug:** Tangiert TASK-05 (Design-Spec dokumentieren) — finale Tokens/Komponenten-Regeln dort festhalten. US-95/US-96 (Detailansicht-Layout) laufen parallel; Abstimmung bei gemeinsamen Komponenten.

---

### US-104 · Scout-Karten: einheitliches Design wie 14-Tage-Feed-Karten `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |
| **Abgeschlossen** | 2026-06-28 |

**Beschreibung:** Die Scout-Karten sollen visuell identisch mit den Feed-Karten (14-Tage-Ansicht) aussehen — gleicher Aufbau mit Score-Ring, Event-Typ-Icon, Uhrzeit, Titel, Location-Zeile und Tag-Chips. Aktuell haben Scout-Karten ein abweichendes Layout (flache Info-Chips, blauer Score-Badge, zwei große Buttons). Das schafft Inkonsistenz innerhalb der App. Die „Standort"- und „Navigation"-Buttons bleiben erhalten, werden aber stilistisch angeglichen.

**Bezug:** Hängt von US-83 [In Progress] ab (Scout-Karten sind jetzt klickbar — Detailansicht). Abgrenzung: US-83 = Detailansicht beim Klick; US-104 = visuelles Design der Karte selbst. Grenzt an US-98/US-103 (Bauhaus-Redesign), aber US-104 ist unabhängig davon umsetzbar.

---

#### 🔬 Analyse-Spec (US-104) · 2026-06-28

**Bestätigte Entscheidungen (aus Klärungsgespräch):**
- Location-Zeile: `"Blick vom [Himmelsrichtung] auf [subject_name]"` — Bearing aus `standpoint_lat/lon` → `subject_lat/lon`, reine Frontendberechnung
- Tag-Chips: Wetter-Text + Entfernung (km) + Mondbeleuchtung (% — nur wenn `body_name === 'moon'` und Wert vorhanden)
- Brennweite: kein Tag-Chip in dieser Iteration
- Buttons Standort + Navigation bleiben erhalten
- Scope: nur `web/index.html` — kein Backend-Änderung
- Straßenname-Geocoding (z.B. „Karl-Marx-Allee mit Fernsehturm"): bewusst ausgeschlossen → eigenes Folge-Ticket

⚠️ **Annahme:** Location-Zeile wiederholt `subject_name` bewusst (z.B. „Blick vom Nordosten auf Berliner Dom"), obwohl `opp-title` ebenfalls `subject_name` zeigt. Falls Stephan die Redundanz stört → Location-Zeile kürzen auf „Blick vom Nordosten".

---

**Scope:**

Eingeschlossen:
- Visueller Umbau der Scout-Karte auf Feed-Karten-Struktur (ScoreRing, Meta-Zeile, Titel, Location-Zeile, Tag-Chips)
- Neue `scoutCard(o)` Hilfsfunktion (analog zu `oppCard()`)
- Neue `bearingLabel()` Hilfsfunktion für Richtungsberechnung
- `SESSION_LABELS` Konstante aus `openDetail()` extrahieren (Wiederverwendung)
- `ICONS`-Map um `'Blaue Stunde Morgen'` und `'Blaue Stunde Abend'` ergänzen
- CSS-Aufräumen: veraltete Scout-spezifische Klassen entfernen (`.scout-card-header`, `.scout-score-badge`, `.scout-chip`, `.scout-meta`, `.scout-subject`, `.scout-kategorie`)
- Buttons (Standort, Navigation) bleiben als `.scout-actions`-Reihe am Kartenende

Ausgeschlossen:
- Geocoding / Straßenname am Standpunkt (eigenes Ticket)
- Backend / `discover.json` Struktur
- Scout-Filterung oder Sortierung
- Detailansicht (US-83)

---

**Akzeptanzkriterien:**

- [ ] AK-1: Im Scout-Tab sehen alle Chancen-Karten genauso aus wie Feed-Karten: links ein Score-Ring (farbcodiert), rechts oben Session-Icon + Session-Label + Uhrzeit, darunter der Subject-Name (Titel), darunter eine Location-Zeile, darunter Tag-Chips.
- [ ] AK-2: Der Score-Ring zeigt den Scout-Score (0–1) farbcodiert (grau < 0,70 · blau < 0,80 · grün < 0,90 · gold ≥ 0,90) — kein Priority-Dot (Scout kennt keinen Alert-Priority-Wert).
- [ ] AK-3: Das Session-Icon ist korrekt: Goldene Stunde Morgen = Sonnenaufgang-Icon, Goldene Stunde Abend = Sonnenuntergang-Icon, Blaue Stunde (Morgen und Abend) = Mond-Icon, Mond-Alignment = Mond-Icon, Milchstraße = Milchstraßen-Icon.
- [ ] AK-4: Die Location-Zeile zeigt „Blick vom [Himmelsrichtung] auf [subject_name]" (z.B. „Blick vom Nordosten auf Berliner Dom"). Die Himmelsrichtung ist eine der acht deutschen Bezeichnungen (Norden, Nordosten, Osten, Südosten, Süden, Südwesten, Westen, Nordwesten) und ergibt sich geometrisch aus den Koordinaten.
- [ ] AK-5: Die Tag-Chips zeigen: Wetter-Beschreibung (Text, z.B. „Klarer Himmel") + Entfernung (z.B. „2,3 km") + Mondbeleuchtung (z.B. „74% beleuchtet") — letztere nur bei Mond-Chancen, nicht bei Sonne.
- [ ] AK-6: Die Buttons „Standort" und „Navigation" sind weiterhin sichtbar und funktional. Ein Tipp auf Standort öffnet Apple Maps auf den berechneten Fotografen-Standpunkt; Navigation startet die Routenführung. Beide Buttons öffnen **nicht** die Detailansicht (Event-Propagation gestoppt).
- [ ] AK-7: Ein Tipp auf die Karte (außerhalb der Buttons) öffnet weiterhin die Detailansicht via `Scout.openDetail()`.
- [ ] AK-8: Regression — Feed-Karten sehen unverändert aus; die Detail-Ansicht funktioniert für Feed- und Scout-Chancen wie bisher.
- [ ] Edge Case: Wenn `body_illumination_pct` fehlt (Sonnen-Chance), erscheint kein Mondbeleuchtungs-Chip — keine Exception, kein leerer Chip.
- [ ] Edge Case: Wenn `dt_utc` fehlt oder ungültig ist, zeigt `formatTime()` „–" anstatt zu crashen.

---

**Pre-Mortem:**

📎 Code-Verifikation 2026-06-28:
- `scoreRing(score, priority)` gelesen — nimmt `score` 0–1 und `priority` (int, Default 0). Scout: `o.score`, priority = 0. ✅
- `eventIcon(type, size, cls)` gelesen — sucht `type` in `ICONS`-Map (deutsche Label). Session-Keys (`golden_evening`) sind NICHT in ICONS → ICON_FALLBACK. ✅ Bestätigt: ICONS-Map muss erweitert werden.
- `ICONS`-Map hat `'Blaue Stunde'` aber nicht `'Blaue Stunde Morgen'` / `'Blaue Stunde Abend'` → beide würden ICON_FALLBACK (i-star) liefern. Muss ergänzt werden.
- `_sessionLabel` ist aktuell lokal in `Scout.openDetail()` definiert → muss extrahiert werden.
- `body_illumination_pct` ist `Optional[float]`, None für Sonne — im Frontend `o.moon_illumination_pct ?? o.body_illumination_pct` (Fallback-Pattern wegen Cache-Migration). Neuer Code: gleiche Null-Koaleszenz verwenden.

💀 Szenario 1: Blaue-Stunde-Karten zeigen falsches Icon (i-star statt Mond)
Auslöser: `ICONS` enthält nicht `'Blaue Stunde Morgen'` / `'Blaue Stunde Abend'`
Frühwarnung: Visueller Vergleich im Scout-Tab nach Umbau
Gegenmaßnahme: ICONS ergänzen → AK-3

💀 Szenario 2: Button-Tap öffnet gleichzeitig Detailansicht + Apple Maps
Auslöser: `event.stopPropagation()` fehlt oder falsch gesetzt beim Umbau
Frühwarnung: Test: Button tippen → nur Maps, kein Detail-Sheet
Gegenmaßnahme: AK-6 explizit testen

💀 Szenario 3: Himmelsrichtung ergibt Nonsens (z.B. immer „Norden")
Auslöser: Bearing-Arithmetik-Fehler (falsche Umkehrung, Gradkonvertierung, off-by-one in 8-Richtungs-Array)
Frühwarnung: 2 bekannte Standorte manuell prüfen (Fernsehturm von NO, Schloss Charlottenburg von O)
Gegenmaßnahme: `bearingLabel()` Unit-Test in Browser-Console vor Einbau

💀 Szenario 4: Mondbeleuchtungs-Chip erscheint bei Sonnen-Chancen
Auslöser: Nur `body_name === 'moon'` prüfen, aber `body_illumination_pct` ist dennoch für Sonne `null` → doppelte Guard nötig
Gegenmaßnahme: Guard auf `body_illumination_pct != null` (unabhängig von body_name) → AK-Edge-Case

💀 Szenario 5: Feed-Karten-Regression durch CSS-Klassen-Konflikt
Auslöser: Beim Aufräumen der `.scout-*` CSS wird versehentlich eine Klasse gelöscht, die auch Feed nutzt
Gegenmaßnahme: Vor dem Löschen jeder Klasse per Grep prüfen, ob sie außerhalb Scout-Kontext verwendet wird → AK-8

---

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: nur `web/index.html` betroffen
- [x] Code verifiziert: `scoreRing`, `eventIcon`, `ICONS`, `oppCard`, `_sessionLabel`, `ScoutOpportunity`-Felder
- [ ] Implementierungsoption gewählt (Weg-Gate)
- [ ] Implementierung

---

**Implementierungsoptionen:**

### Option A — Neue `scoutCard(o)` Funktion (wie `oppCard()`) ✅ Empfehlung
Vorgehen: Scout-Karten-HTML aus `Scout.render()` in eine dedizierte `scoutCard(o)` Funktion auslagern. Gleiche Klassen wie Feed (`.card`, `.opp-card`, `.opp-body`, `.opp-meta`, `.opp-tags`). Zwei neue Hilfsfunktionen: `bearingLabel()` und `SESSION_LABELS` als Modulkonstante. `ICONS`-Map um fehlende Session-Labels ergänzen. Veraltete Scout-CSS-Klassen aufräumen.

Betroffene Dateien: `web/index.html`
Vorteile: konsistentes Muster mit `oppCard()`, sauberer Code, leicht erweiterbar
Nachteile: etwas mehr Umbau als Option B
Aufwand: mittel

### Option B — Inline-Umbau in `Scout.render()`
Vorgehen: Gleiche strukturellen Änderungen, aber direkt im Template-String von `Scout.render()` — keine Auslagerung in eine eigene Funktion.

Betroffene Dateien: `web/index.html`
Vorteile: minimale Diff
Nachteile: `Scout.render()` wird noch länger; kein Aufräumen, altes CSS bleibt stehen
Aufwand: mittel (minimal weniger)

✅ **Empfehlung: Option A** — `oppCard()` ist das etablierte Muster. Eine dedizierte `scoutCard()` macht künftige Scout-Änderungen isolierbar und hält `Scout.render()` lesbar. CSS-Aufräumen ist bei Option A inbegriffen und reduziert die technische Schuld.

---

**Testplan:**

Automatisiert (kein pytest — reine Frontend-Änderung):
- `bearingLabel()` Unit-Test in Browser-Console: 4 Testfälle (N, O, S, W) mit bekannten Koordinaten

Manuell (Safari, http://localhost:8000):
- [ ] Scout-Tab öffnen → Karten sehen wie Feed-Karten aus (ScoreRing sichtbar, kein gold Badge)
- [ ] Blaue-Stunde-Karte prüfen → Mond-Icon (nicht Stern-Fallback)
- [ ] Location-Zeile zeigt „Blick vom [Richtung] auf [Motiv]"
- [ ] Wetter + Entfernung + Mondbeleuchtung (nur Mond) als Chips sichtbar
- [ ] Button „Standort" → Apple Maps öffnet (kein Detail-Sheet)
- [ ] Karte antippen → Detail-Sheet öffnet
- [ ] Feed-Tab prüfen → Feed-Karten unverändert

---

### US-103 · Karten-Marker & FOV-Legende im Bauhaus-Stil `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-27 |
| **Abgeschlossen** | 2026-06-28 |

**Beschreibung:** Die funktionalen Karten-Marker (Leaflet-Pins: Fotograf-Standort, Motiv) und die FOV-Legende („Motiv"-Fadenkreuz, „Fotograf-Standort"-Pin) sollen optisch ans Bauhaus-Design angeglichen werden (Form, Strich, Farbtöne aus US-99). In US-100 bewusst ausgeschlossen, weil farbige/funktionale Karten-Marker eigene Logik haben. Lesbarkeit auf hellen UND dunklen/satelliten Karten beachten.

**Bezug:** Kind von US-98 (Bauhaus-Redesign). Aufkommen #2+#3 aus dem US-100-Test (2026-06-27). Abgrenzung zu US-100 (UI-Glyphen, erledigt) und US-102 (Logo/App-Icon).

---

#### 🔬 Analyse-Spec (2026-06-28)

---

##### Annahmen-Protokoll

- ⚠️ Die bestehenden Marker (`MapMarkers._obsIcon()`, `MapMarkers._subjIcon()`) verwenden bereits `--accent-2` (Gold) als Füllfarbe und `--surface` als Konturfarbe. Das ist eine gute Ausgangsbasis, aber noch kein explizites Bauhaus-Design (kein weißer Kontur-Rand der auf Satellit gut lesbar ist, kein klarer Bauhaus-Formenkanon wie Kreis/Quadrat/Dreieck).
- ⚠️ Der MapView-Übersichts-Marker (`MapView.loadMarkers()`, Zeile ~3734) benutzt `--accent` (Bauhaus-Blau) statt `--accent-2` (Gold) — das ist **inkonsistent** zu den Detail-Markern in `MapMarkers`. Muss angeglichen werden.
- ⚠️ Der FOV-Kegel in `CameraFOV._redrawCone()` liest die Farbe per `getComputedStyle` als konkreten Hex-Wert — das funktioniert, ist aber ein Workaround weil Leaflet-Polygone keine CSS-Variablen unterstützen.
- ⚠️ Die FOV-Karte in `CameraFOV.initMap()` verwendet fix einen Satelliten-Layer (`arcgisonline`). Marker müssen dort immer lesbar sein.
- ⚠️ SVG-Inline-Styles nutzen `style="fill:var(--accent-2)"` — in Safari/WebKit funktionieren CSS-Variablen in inline-SVG-`style`-Attributen grundsätzlich, ABER nur wenn das SVG im DOM eingebettet ist (nicht als `src`-Attribut geladen). Da diese SVGs als `html`-String in `L.divIcon` eingesetzt werden, landen sie im DOM — CSS-Variablen sollten funktionieren. Trotzdem sorgfältig testen.

---

##### Example Mapping

**Regel 1: Fotograf-Marker ist klar als Standort erkennbar**

- ✅ Positiv: Ich öffne eine Location-Detail-Ansicht, scrolle zur „Karte & Blickwinkel"-Sektion — der Fotograf-Standort ist als goldener Pin mit weißem Kern sofort als Standort-Marker erkennbar, auch auf der Satelliten-Karte.
- ❌ Negativ: Öffne ich dieselbe Sektion auf einem Gerät im Dark-Mode, soll der Pin genauso gut lesbar sein — er darf nicht im dunklen Satelliten-Hintergrund verschwinden.
- ⚠️ Edge: Wenn Dark- und Light-Mode dasselbe `--surface`-Token für den weißen Kern verwenden, ändert sich die Kern-Farbe mit dem Theme — das ist gewollt (Kern = immer Hintergrundfarbe des Panels).

**Regel 2: Motiv-Marker unterscheidet sich klar vom Fotograf-Marker**

- ✅ Positiv: Auf der FOV-Karte sehe ich zwei unterschiedliche Symbole: Tropfen-Pin (Fotograf) und Fadenkreuz-Kreis (Motiv). Ich kann auf einen Blick erkennen, wo ich stehe und worauf ich fotografiere.
- ❌ Negativ: Beide Marker haben nie dieselbe Form — auch wenn beide `--accent-2` nutzen.

**Regel 3: Übersichts-Karte zeigt konsistente Farben**

- ✅ Positiv: Im Locations-Tab zeigt die Karte alle Standort-Marker in derselben Farbe wie die Detail-Marker — Bauhaus-Gold (`--accent-2`), nicht Bauhaus-Blau.
- ❌ Negativ: Aktuell zeigt die Übersichts-Karte Bauhaus-Blau (`--accent`) — das ist inkonsistent. Nach der Implementierung soll es Gold sein.

**Regel 4: FOV-Legende ist lesbar und passt zum Bauhaus-Design**

- ✅ Positiv: Unter jeder FOV-Karte sehe ich eine kompakte Legende mit zwei Mini-Icons (Tropfen für Fotograf, Fadenkreuz für Motiv) und den deutschen Labels. Die Icons stimmen visuell exakt mit den Karten-Markern überein.
- ❌ Negativ: Legende zeigt nie generische Punkt/Kreuz-Icons, die nicht zu den tatsächlichen Markern passen.

---

##### Offene Fragen

- Soll der MapView-Übersichts-Marker (bisher runder Diamant-Pin in Bauhaus-Blau) auf einen Tropfen-Pin in Gold (`--accent-2`) angeglichen werden, oder soll er bewusst anders aussehen (z. B. kleiner Punkt in `--accent`)? → Empfehlung: Gold-Tropfen wie Detail-Marker, aber kleinere Größe für die Übersicht.

---

##### Akzeptanzkriterien

**AK-1 (FOV-Karte, Fotograf-Marker):**
Wenn ich in der Event- oder Location-Detail-Ansicht die „Karte & Blickwinkel"-Sektion öffne, sehe ich den Fotograf-Standort als **tropfenförmigen Pin in Bauhaus-Gold (`--accent-2`) mit weißem Kern (`--surface`)**. Der Pin hat einen dunklen Drop-Shadow, damit er auf der Satelliten-Karte nicht im Hintergrund versinkt. Der weiße Kern signalisiert „leer" im Bauhaus-Sinn — Ort ohne Objekt.

**AK-2 (FOV-Karte, Motiv-Marker):**
Das Motiv ist als **Fadenkreuz-Kreis in Bauhaus-Gold mit weißer Innen-Kontur** dargestellt. Die zwei Achslinien + gefüllter Kreis sind klar erkennbar, sowohl auf heller als auch auf dunkler/Satelliten-Karte. Drop-Shadow vorhanden.

**AK-3 (Übersichts-Karte Locations-Tab):**
Alle Standort-Marker auf der Locations-Übersichtskarte erscheinen in **Bauhaus-Gold (`--accent-2`)**, nicht in Bauhaus-Blau. Die Form bleibt der rotierende Tropfen (bereits vorhanden, aber andere Farbe).

**AK-4 (Konsistenz):**
Die Mini-Icons in der FOV-Legende unter der Karte stimmen **exakt** mit den tatsächlichen Karten-Markern überein — selbe Form, selbe Farbtöne.

**AK-5 (Dark-Mode):**
Im Dark-Mode (System-Präferenz) bleiben alle Marker lesbar. Der weiße Kern (`--surface` = `#1e2127` im Dark-Mode) hebt sich durch den Drop-Shadow vom Satelliten-Hintergrund ab.

**AK-6 (Safari/WebKit):**
Alle SVG-Striche und -Füllungen werden korrekt gerendert — in Safari auf iPhone und Mac. Inline-SVG-`style`-Attribute mit CSS-Variablen sind erlaubt (DOM-eingebettet), aber `stroke`/`fill`-Attribute direkt auf `<g>`-Tags sind sicherer (kein WebKit-Bug).

---

##### Pre-Mortem

**Versagen 1: CSS-Variablen in SVG-Strings werden in Safari nicht aufgelöst.**
- Frühwarnung: Icon erscheint schwarz (Browser-Fallback) statt gold.
- Gegenmaßnahme: Attribute direkt auf SVG-Elemente setzen (`stroke="currentColor"` + `color: var(--accent-2)` auf dem Container-Div) ODER `getComputedStyle` wie bei `_redrawCone()` verwenden. Testen auf echtem iPhone vor Release.

**Versagen 2: Marker auf Satelliten-Karte nicht lesbar.**
- Frühwarnung: Beim manuellen Test auf dem Satelliten-Layer verschwinden die Marker.
- Gegenmaßnahme: Drop-Shadow mit `feDropShadow flood-opacity=0.7` für starken Kontrast. Weißer Kern bleibt immer als Orientierungspunkt.

**Versagen 3: Dark-Mode-Kern wird unsichtbar.**
- Frühwarnung: Im Dark-Mode ist der weiße Kern (= `--surface` = `#1e2127`) unsichtbar auf dunklem Satelliten-Hintergrund.
- Gegenmaßnahme: Kern-Farbe fix weiß (`#ffffff`) statt `var(--surface)`, da Satelliten-Karte immer dunkel ist. Oder: Kern-Kontur in `--accent-2` mit weißem Innenfüller.

**Versagen 4: Übersichts-Marker verliert Farbe beim Theme-Wechsel.**
- Frühwarnung: Nach Theme-Wechsel bleiben alte Marker auf der Karte in der vorherigen Farbe.
- Gegenmaßnahme: `MapView.loadMarkers()` nach Theme-Wechsel neu aufrufen ODER Farbe aus CSS-Variable lesen (bereits mit `getComputedStyle` gelöst — aber nur beim initialen Laden). Theme-Wechsel-Event prüfen.

**Versagen 5: Inkonsistenz bei Scope-Creep.**
- Frühwarnung: Es verleitet, auch den GPS-Dot-Marker, den FOV-Kegel-Stil oder die Sichtachse anzupassen.
- Gegenmaßnahme: Scope bleibt bei den 3 explizit genannten Elementen: (a) FOV-Marker (Fotograf + Motiv), (b) Übersichts-Marker, (c) Legende. Alles andere → separates Ticket.

---

##### Architektur-Analyse

**Betroffene Code-Stellen in `web/index.html`:**

1. **`MapMarkers._obsIcon()`** (Zeile ~3641) — Fotograf-Tropfen-Pin für FOV-Karte und Location-Detail. Nutzt `L.divIcon` mit inline-SVG. Farben: `--accent-2` (Gold), `--surface` (Kern). Bereits gut; Form-Feinschliff möglich.

2. **`MapMarkers._subjIcon()`** (Zeile ~3657) — Motiv-Fadenkreuz für FOV-Karte. Nutzt `L.divIcon` mit inline-SVG. Farben: `--accent-2`. Bereits vorhanden; Drop-Shadow prüfen.

3. **`MapMarkers.legendHtml()`** (Zeile ~3682) — HTML-Legende mit Mini-SVGs. Spiegelt die Marker, aber ohne Drop-Shadow (korrekt für Legende). Kann 1:1 als Vorlage dienen.

4. **`MapView.loadMarkers()`** (Zeile ~3734) — Übersichts-Marker mit `L.divIcon`. **Problem:** Nutzt `--accent` (Blau) statt `--accent-2` (Gold). Muss korrigiert werden.

5. **`CameraFOV.initMap()`** (Zeile ~3228) — FOV-Karten-Init; nutzt `MapMarkers.observer()` und `MapMarkers.subject()` — erbt automatisch Fixes aus Punkt 1+2.

**Leaflet-API:**
- `L.divIcon({ className:'', html: svgString, iconSize, iconAnchor })` — der Weg für custom Marker
- `L.marker(latlng, { icon })` — standard
- Kein Canvas, kein SVG-Overlay — alles DOM-basiert

**CSS-Token-Quelle (US-99, Zeile 37–92):**
- `:root` → `--accent: #2d4ea0`, `--accent-2: #b07a12`, `--surface: #ffffff`, `--on-accent: #ffffff`
- `@media (prefers-color-scheme: dark)` → `--accent: #7c9bea`, `--accent-2: #e3a21a`, `--surface: #1e2127`

---

##### Implementierungsoptionen

**Option A — Inline-SVG-Attribute statt `style`-String (empfohlen)**

Änderung: In `_obsIcon()` und `_subjIcon()` die Farb-Angaben von `style="fill:var(--accent-2)"` auf direkte SVG-Attribute umstellen: `fill` und `stroke` als Attribute am `<path>`/`<line>`/`<circle>`-Element, Farbe als CSS-Variable über ein Wrapper-Div mit `color: var(--accent-2)` und `currentColor`.

Vorgehen:
1. `MapMarkers._obsIcon()` — SVG-Elemente: `fill="currentColor"` für den Tropfen-Körper, `stroke="white"` für den Außenrand, `fill="white"` für den Kern. Wrapper-Div: `style="color:var(--accent-2)"`.
2. `MapMarkers._subjIcon()` — analog für Fadenkreuz-Linien und Kreis.
3. `MapMarkers.legendHtml()` — Mini-SVGs analog anpassen.
4. `MapView.loadMarkers()` — `--accent` → `--accent-2` für Übersichts-Marker.

Betroffene Dateien: nur `web/index.html`

Vorteile:
- WebKit-sicher: `currentColor` als SVG-Attribut (nicht CSS-Klasse) ist das Memory-konforme Muster
- Nur eine Datei, 4 Änderungspunkte
- Keine neue Logik, keine neuen Abhängigkeiten
- Dark-Mode funktioniert automatisch via CSS-Variable am Container

Nachteile:
- Kern-Farbe (weißer Punkt) muss fix `white` sein statt `var(--surface)`, damit Satelliten-Lesbarkeit erhalten bleibt

Aufwand: ~2 Stunden

---

**Option B — Theme-wechsel-robuste Farb-Aktualisierung via JS**

Änderung: Marker-SVGs bleiben als `style`-Strings, aber beim Theme-Wechsel werden alle Marker neu erstellt (analog zu `_redrawCone()` mit `getComputedStyle`).

Vorgehen:
1. Theme-Change-Listener auf `prefers-color-scheme` oder auf den manuellen Umschalter.
2. Bei Theme-Wechsel: `MapView.loadMarkers()` neu aufrufen, alle FOV-Karten-Marker neu setzen.
3. `MapView.loadMarkers()` Farbe von `--accent` auf `--accent-2` korrigieren.

Betroffene Dateien: `web/index.html`

Vorteile:
- Erzwingt Konsistenz bei Theme-Wechsel auch bei alten Markers
- Klar trennbar pro Komponente

Nachteile:
- Höherer Aufwand, neue Listener-Logik
- Potenzielle Bugs bei gleichzeitig offenen Karten + Theme-Wechsel
- Overkill: CSS-Variablen in inline-SVG lösen Theme-Wechsel bereits automatisch

Aufwand: ~4 Stunden

---

##### Empfehlung

**Option A** — Inline-SVG-Attribute mit `currentColor` + Wrapper-`color:`-CSS-Variable.

Begründung: Minimal-invasiv (nur `web/index.html`, 4 Stellen), WebKit-sicher nach Memory-Muster, Dark-Mode automatisch, kein neuer JS-Code. Der einzige Trade-off (Kern fix weiß statt `var(--surface)`) ist sinnvoll: Satelliten-Karten sind immer dunkel, weißer Kern immer lesbar. Zusätzlich Korrektur der Übersichts-Marker von `--accent` auf `--accent-2` für Farbkonsistenz.

---

### BUG-56 · Astronomie-Regressionstest: Sonnenauf-/-untergang Berlin außerhalb Toleranz `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-02 |
| **Abgeschlossen** | 2026-07-03 |

**Beschreibung:** `tests/test_astronomy_regression.py::test_sunrise_berlin_within_tolerance` und `test_sunset_berlin_within_tolerance` schlagen fehl — die berechnete Sonnenauf-/-untergangszeit für Berlin liegt außerhalb der im Test erwarteten Toleranz. Beim Testlauf für US-113 entdeckt, ohne inhaltlichen Bezug zu US-113 (Himmelsröte-Chance). Root Cause noch nicht analysiert — offen ob Ephemeriden-Bibliothek, Zeitzonen-Handling oder Toleranzwert des Tests veraltet ist.

**Bezug:** Unabhängig von BUG-57 (Weather-Map-Tests) — andere Root Cause (Astronomie-Berechnung vs. veraltete US-72-Testdatei), daher als eigenes Ticket geführt statt zusammengelegt. Berührt inhaltlich US-107 (Sonnen-Alignment-Planung, done 2026-06-29): Beide nutzen dieselbe Sonnenauf-/-untergangs-Berechnung im Backend. Da diese Berechnung sich als korrekt erwiesen hat (siehe Root Cause unten), besteht **kein** Korrekturbedarf an US-107 — die dort ausgelieferten Zeiten sind nicht betroffen.

**Root Cause (verifiziert):**

Testlauf (`pytest backend/tests/test_astronomy_regression.py -v`) zeigt für den 21.06.2026 (Berlin, 52,52°N/13,405°O):

| Ereignis | Berechnet | Test-Referenzwert | Abweichung |
|----------|-----------|--------------------|------------|
| Sonnenaufgang | 02:43 UTC | 01:43 UTC | 60,1 Min. |
| Sonnenuntergang | 19:33 UTC | 20:25 UTC | 51,7 Min. |

Auffällig: Beide Abweichungen liegen nahe bei genau einer Stunde — das typische Muster eines Zeitzonen-/Sommerzeit-Versatzes (MESZ = UTC+2, nicht UTC+1), nicht das Muster eines Rechenfehlers (der würde eher gleichmäßig in dieselbe Richtung oder mit wachsendem Fehler über den Tag streuen).

Zur Gegenprobe wurde die berechnete Zeit mit einer zweiten, unabhängigen Bibliothek (`astral`, andere Berechnungsmethode als die im Test verwendete Skyfield/de421.bsp-Ephemeride) für exakt denselben Ort und dasselbe Datum geprüft:

| Ereignis | Skyfield (im Test genutzt) | astral (unabhängige Gegenprobe) | Differenz |
|----------|------------------------------|----------------------------------|-----------|
| Sonnenaufgang | 02:43:06 UTC | 02:43:28 UTC | 22 Sek. |
| Sonnenuntergang | 19:33:16 UTC | 19:32:55 UTC | 21 Sek. |

Zwei unabhängige Berechnungsmethoden stimmen bis auf ~20 Sekunden überein (methodenbedingte Restdifferenz, weit innerhalb jeder sinnvollen Toleranz). Das belegt: **Die Berechnung im Produktivcode ist astronomisch korrekt.** Zusätzlich beweist die Skyfield-Version im Regressionstest (1.54, aktuell) und die verwendete de421.bsp-Ephemeride (Standardwerk, gültig 1899–2053) selbst, dass hier keine veraltete oder defekte Bibliothek im Spiel ist.

Wichtiger Architektur-Fund: Der Regressionstest berechnet die Sonnenzeiten **komplett unabhängig** noch einmal direkt mit Skyfield — er ruft nicht die Produktionsfunktion (`calculations/astronomy.py::calculate_sun_info`) auf. Die Produktionsfunktion selbst verwendet exakt dieselbe Skyfield-Methode (`almanac.sunrise_sunset`) wie der Test. Ein Fehler im Test-Referenzwert sagt also **nichts** über einen Fehler im ausgelieferten App-Verhalten aus — betroffen ist ausschließlich der Vergleichswert, der im Test hinterlegt ist, nicht die App-Berechnung selbst.

**Fazit Root Cause:** Der im Test hinterlegte Referenzwert (01:43 UTC / 20:25 UTC, laut Kommentar von timeanddate.com übernommen) ist um rund eine Stunde falsch — vermutlich wurde beim Übertragen der Berliner Ortszeit (MESZ, UTC+2) versehentlich nur ein Stunden-Offset von einer Stunde statt zwei abgezogen, oder der Wert wurde für Winterzeit statt Sommerzeit notiert. Die tatsächliche, astronomisch korrekte Zeit für Berlin am 21.06.2026 liegt bei ca. 02:43 UTC (Aufgang) / 19:33 UTC (Untergang) — nicht bei den im Test hinterlegten Werten. **Nicht verifizierbar war** der direkte Abgleich mit der timeanddate.com-Webseite selbst, da in dieser Umgebung kein Internetzugriff auf externe Webseiten möglich war (weder `curl` noch `web_fetch` lieferten Daten). Die Gegenprobe erfolgte stattdessen über eine zweite, offline verfügbare Ephemeriden-Bibliothek (`astral`), was methodisch gleichwertig ist, da zwei unabhängige Berechnungsverfahren übereinstimmen.

**Pre-Mortem:**
- 💀 Szenario: Die Toleranz wird einfach von ±5 auf ±65 Minuten aufgeweitet, um den Test grün zu bekommen. → Gegenmaßnahme: Nicht die Toleranz verändern, sondern den falschen Referenzwert korrigieren (01:43→02:43 UTC, 20:25→19:33 UTC). Die enge Toleranz von ±5 Minuten ist sinnvoll und schützt genau vor echten künftigen Regressionen (kaputte Ephemeride, fehlerhafte Zeitzonenumrechnung) — sie darf nicht geopfert werden, nur weil der aktuelle Vergleichswert falsch ist.
- 💀 Szenario: Der Fix wird an der Produktionsberechnung (`calculate_sun_info`) vorgenommen, obwohl diese nachweislich korrekt rechnet — dadurch werden reale App-Funktionen (Goldene Stunde, Blaue Stunde, US-107 Sonnen-Alignment, Sonnenuntergangs-Chancen im Feed) verfälscht. → Gegenmaßnahme: Root Cause ist klar auf den Testwert eingegrenzt (siehe oben, per Gegenprobe belegt) — die Spec schließt Änderungen an `astronomy.py` explizit aus.
- 💀 Szenario: Beim Korrigieren des Referenzwerts wird versehentlich nur einer der beiden Werte (Aufgang oder Untergang) angepasst, der andere bleibt falsch stehen und der Test bleibt halb rot. → Gegenmaßnahme: Beide Werte in derselben Änderung korrigieren, Testlauf danach zeigt beide Tests grün.
- 💀 Szenario: Der korrigierte Referenzwert wird erneut ohne Gegenprobe „aus dem Gedächtnis" oder plausibel geschätzt eingetragen und ist wieder leicht daneben. → Gegenmaßnahme: Der in dieser Analyse per Skyfield **und** astral doppelt verifizierte Wert (02:43 UTC / 19:33 UTC, siehe Tabelle oben) wird 1:1 übernommen, nicht neu geschätzt.
- 💀 Szenario: Der Test wird künftig bei jedem Lauf minimal rot, weil die Toleranz zu eng an der methodenbedingten Restdifferenz (~20–30 Sek.) verschiedener Skyfield-/de421.bsp-Versionen liegt. → Gegenmaßnahme: Die bestehende Toleranz von ±5 Minuten bleibt unverändert, da sie mit >10-facher Sicherheitsmarge über der beobachteten Methodendifferenz liegt (20–30 Sek. vs. 300 Sek. Toleranz) — kein Anpassungsbedarf.

**Akzeptanzkriterien:**
- [ ] Der automatisierte Regressionstest für den Berliner Sonnenaufgang am 21.06.2026 zeigt nach dem Fix ein bestandenes Ergebnis, ohne dass die erlaubte Abweichung (Toleranzfenster) verändert wurde.
- [ ] Der automatisierte Regressionstest für den Berliner Sonnenuntergang am 21.06.2026 zeigt nach dem Fix ein bestandenes Ergebnis, ohne dass die erlaubte Abweichung (Toleranzfenster) verändert wurde.
- [ ] Die in der App angezeigten Zeiten für Sonnenaufgang, Sonnenuntergang, Goldene Stunde und Blaue Stunde bleiben nach dem Fix unverändert (keine Seiteneffekte, da die Produktionsberechnung nicht angefasst wird).
- [ ] Edge Case: Ein künftiger echter Fehler in der Zeitberechnung (z. B. durch eine fehlerhafte Bibliotheks-Aktualisierung) lässt den Test weiterhin zuverlässig fehlschlagen — die Korrektur darf die Empfindlichkeit des Tests nicht verwässern.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (Root-Cause-Klärung ersetzt hier das übliche Feature-Mapping, da es sich um einen reinen Test-Datenfehler handelt — keine Verhaltensregeln zu klären)
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: betroffene Datei ist ausschließlich `backend/tests/test_astronomy_regression.py` (Referenzwerte in `test_sunrise_berlin_within_tolerance` und `test_sunset_berlin_within_tolerance`); `backend/calculations/astronomy.py` wurde gelesen und als nicht fehlerhaft bestätigt, bleibt unangetastet
- [x] Designer-Check: nicht visuell (reiner Backend-Test), übersprungen
- [ ] Implementierungsoptionen: A / B / C
- [ ] Empfehlung: Option A

**Implementierungsoptionen:**

### Option A — Testreferenzwert korrigieren
- Vorgehen: Die beiden im Test hinterlegten Vergleichswerte werden auf die verifizierten, astronomisch korrekten Zeiten (02:43 UTC Sonnenaufgang, 19:33 UTC Sonnenuntergang) korrigiert. Toleranz (±5 Minuten) bleibt unverändert. Begleitkommentar im Test wird angepasst, damit künftig klar ist, dass der Wert doppelt (Skyfield + astral) verifiziert wurde.
- Betroffene Dateien: `backend/tests/test_astronomy_regression.py`
- Vorteile: Behebt exakt die nachgewiesene Ursache (falscher Testwert), keine Berührung von Produktionscode, kein Risiko für Golden-Hour/Blue-Hour/US-107-Funktionen, sehr kleiner Änderungsumfang.
- Nachteile / Risiken: Keine wesentlichen — einziges Risiko (versehentlich nur einen der beiden Werte korrigieren) ist im Pre-Mortem abgedeckt und durch die AKs abgesichert.
- Aufwand: klein

### Option B — Toleranz aufweiten
- Vorgehen: Die Toleranz im Test würde von ±5 auf z. B. ±65 Minuten erhöht, damit der aktuelle (falsche) Referenzwert wieder „passt".
- Betroffene Dateien: `backend/tests/test_astronomy_regression.py`
- Vorteile: Keine.
- Nachteile / Risiken: Verdeckt den eigentlichen Fehler dauerhaft, entwertet den Regressionstest als Schutz gegen echte künftige Zeitberechnungsfehler (genau das Szenario, das im Pre-Mortem als Hauptrisiko benannt ist). Nicht empfohlen.
- Aufwand: klein (aber der falsche Weg)

### Option C — Produktionsberechnung anpassen
- Vorgehen: Die Sonnenauf-/-untergangsberechnung in `calculations/astronomy.py` würde geändert, in der Annahme, sie rechne falsch.
- Betroffene Dateien: `backend/calculations/astronomy.py` (und alle Features, die darauf aufbauen: Golden Hour, Blue Hour, US-107 Sonnen-Alignment, Feed-Chancen).
- Vorteile: Keine — die Berechnung ist nachweislich korrekt (Gegenprobe mit `astral`, Abweichung < 30 Sek.).
- Nachteile / Risiken: Würde eine funktionierende Berechnung verfälschen und mehrere ausgelieferte Features (US-107, Golden/Blue Hour, Feed-Zeiten) beschädigen. Nicht empfohlen.
- Aufwand: mittel (aber unnötig und schädlich)

✅ **Empfehlung: Option A** — Die Root-Cause-Analyse hat eindeutig belegt (zwei unabhängige Berechnungsmethoden stimmen auf ~20 Sekunden überein), dass ausschließlich der im Test hinterlegte Vergleichswert falsch ist, nicht die Berechnung selbst. Option A behebt exakt diese Ursache mit minimalem, risikofreiem Eingriff. Option B würde den Test dauerhaft entschärfen und wurde im Pre-Mortem als Hauptgefahr identifiziert. Option C würde funktionierenden Code ohne Grund anfassen und reale Features gefährden.

**Testplan:**
- [ ] Automatisiert (Harness): `test_sunrise_berlin_within_tolerance` und `test_sunset_berlin_within_tolerance` in `backend/tests/test_astronomy_regression.py` laufen nach der Korrektur grün; restliche 11 Tests in derselben Datei bleiben unverändert grün (Regression innerhalb der Testdatei).
- [ ] Manuell: Nach dem Fix `pytest backend/tests/test_astronomy_regression.py -v` lokal ausführen — erwartet: 13/13 Tests bestanden, keine Fehlermeldung mehr zu Sonnenaufgang/-untergang Berlin.

**Umsetzung (2026-07-02):**
Vor der Korrektur per Live-Testlauf (`pytest backend/tests/test_astronomy_regression.py -v`) gegenverifiziert: berechneter Sonnenaufgang 02:43:05.875239 UTC, Sonnenuntergang 19:33:16.495871 UTC — deckt sich mit den in der Analyse ermittelten Werten. Geänderte Datei: `backend/tests/test_astronomy_regression.py`.
- `test_sunrise_berlin_within_tolerance`: Referenzwert `ref = datetime(2026, 6, 21, 1, 43, ...)` → `datetime(2026, 6, 21, 2, 43, ...)` (01:43 UTC → 02:43 UTC), inkl. Docstring/Fehlermeldungstext angepasst.
- `test_sunset_berlin_within_tolerance`: Referenzwert `ref = datetime(2026, 6, 21, 20, 25, ...)` → `datetime(2026, 6, 21, 19, 33, ...)` (20:25 UTC → 19:33 UTC), inkl. Docstring/Fehlermeldungstext angepasst.
- Kommentarblock oberhalb beider Tests (Zeile ~95) auf die neuen Referenzwerte aktualisiert + Hinweis auf BUG-56 als Quelle der Korrektur ergänzt.
- Toleranz (±5 Min.) unverändert. Produktionscode (`calculations/astronomy.py`) nicht angefasst.
- Testergebnis: `pytest backend/tests/test_astronomy_regression.py -v` → 13/13 grün.
- Regressions-Check Nachbartests: `test_ephemeris_engine.py`, `test_moon_phase_events.py`, `test_us79_moon_rise_set.py` → 25/28 grün, 3 Fehlschläge durch vorbestehenden `ModuleNotFoundError: No module named 'httpx'` in `calculations/weather.py` (Sandbox-Umgebungslücke, unabhängig von dieser Änderung). `test_us07.py`, `test_us07_golden_cloud_score.py`, `test_us113.py` konnten aus demselben Grund (fehlendes `httpx`-Modul) nicht kollisionsfrei geladen werden — ebenfalls keine Verbindung zur Testwert-Korrektur.

**Unabhängige Verifikation (2026-07-02):** Separater Subagent hat den Fix gegengeprüft (nicht der Implementierer): 13/13 Tests frisch selbst ausgeführt und grün, Toleranz (±5 Min.) nachweislich unverändert, Produktionscode (`calculations/astronomy.py`) unangetastet, kein neuer Fehlerfall im selben Testfile. Urteil: **bestanden**, keine Restrisiken.

---

### BUG-57 · Weather-Map-Testdatei referenziert nicht existierende Funktion `fetch_weather_multigrid` `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-02 |
| **Abgeschlossen** | 2026-07-05 |

**Beschreibung:** `tests/test_us72_weather_map.py` schlägt mit `ImportError`/`AttributeError` fehl, da `backend/main.py` keine Funktion `fetch_weather_multigrid` (mehr) besitzt. Beim Testlauf für US-113 entdeckt, ohne inhaltlichen Bezug zu US-113. Vermutliche Ursache laut US-112-Analyse-Spec (Zeile 1268 f.): Die Testdatei wurde test-first für das nie gebaute US-72-Backend geschrieben (`fetch_weather_grid`, `fetch_weather_multigrid`, `WEATHER_REGIONS`, `_weather_map_cache` kamen laut damaligem Befund ausschließlich in dieser untracked Testdatei vor, nie im Backend implementiert). US-112 hat den `/weather-map`-Endpoint dann tatsächlich gebaut, aber mit anderer Architektur (DWD ICON-D2 + MET Norway statt Open-Meteo-Multigrid) — die alte Testdatei wurde dabei nicht auf die neue Implementierung migriert oder entfernt. Zu klären: Testdatei an die tatsächliche US-112-Implementierung anpassen, oder als obsolet entfernen (US-72 „geht in US-112 auf", siehe US-112-Bezug).

**Bezug:** Direkte Verbindung zu **US-72** (Wetterkarte, Board-Status „Done", aber Backend laut US-112-Analyse nie eigenständig existent) und **US-112** (Wetter-Overlay DWD/MET, Board-Status „Done", released 2026-07-01, hat US-72 laut eigenem Bezugstext „aufgehen lassen"). Kein neuer Bug in der Wetter-Funktionalität selbst — US-112 wurde live verifiziert und funktioniert; betrifft ausschließlich eine veraltete/verwaiste Testdatei aus der US-72-Phase. Unabhängig von BUG-56 (Astronomie) — andere Root Cause, daher getrennt geführt.

---

**Implementation Spec** *(Analyse 2026-07-03)*

**📎 Code-Verifikation (tatsächlich gelesen, nicht vermutet):**
- `backend/tests/test_us72_weather_map.py` (262 Zeilen) vollständig gelesen. Importiert/nutzt: `from calculations.weather import WEATHER_REGIONS` (Z. 39), `from calculations.weather import _build_germany_grid` (Z. 77), `from calculations.weather import fetch_weather_multigrid` (Z. 105, 145, 171), sowie `patch("main.fetch_weather_multigrid", ...)` (Z. 212, 254) und `main._weather_map_cache` / `main._weather_map_updated_at` als einfache Attribut-Zuweisung (Z. 189 f., 245 f.) — passend zum alten Multigrid-Schema (`grid`/`hourly_times`/`fetched_at`), nicht zum heutigen Schema.
- `backend/calculations/weather.py` per Grep auf `^def `/`^async def ` durchsucht: enthält `calculate_photo_weather_score`, `_golden_cloud_score`, `calculate_golden_cloud_score`, `should_generate_golden_clouds_event`, `should_generate_red_sky_event`, `wmo_code_to_description`, `fetch_weather_forecast`, `is_golden_hour_weather_good`. **Keine** der vier von der Testdatei referenzierten Namen (`fetch_weather_grid`, `fetch_weather_multigrid`, `WEATHER_REGIONS`, `_build_germany_grid`) existiert dort — auch `fetch_weather_grid` (die von der Testdatei als „Regression" erwartete Single-Grid-Funktion aus der ursprünglichen US-72-Analyse) ist inzwischen nicht mehr vorhanden.
- `backend/main.py` per Grep durchsucht: `/weather-map` (Z. 1895) und `/weather-map/png/{field}/{idx}` (Z. 1958) sind real implementiert, nutzen aber `_build_weather_map()` (Z. 713, importiert aus `calculations/weather_grib.py`) — GRIB/PNG-Architektur (DWD ICON-D2 + MET Norway, `_weather_map_png`, `bounds`/`sources`/`frames`/`attribution`), nicht das Open-Meteo-Multigrid-Schema der alten Testdatei. `fetch_weather_multigrid` kommt in `main.py` nirgends vor (0 Treffer außer in der alten Testdatei selbst).
- `backend/tests/test_us112_weather_map.py` (280 Zeilen) vollständig gelesen: bereits vorhandene, vollständige Testsuite für die reale US-112-Implementierung — testet `calculations/weather_grib.py` (GRIB-Dekodierung, Deakkumulation, IDW-Interpolation, PNG-Encoding, Quellen-Merge DWD+MET, Null-Handling) sowie die Endpoints `/weather-map` (Schema `bounds`/`hourly_times`/`frames`/`attribution`/`sources`), `/weather-map/png/{field}/{idx}` und Cache-Verhalten. Deckt exakt das ab, was die alte Testdatei für die (nie gebaute) Multigrid-Architektur abdecken sollte — nur eben gegen die tatsächlich existierende Architektur.
- Git-Status geprüft (`git status --porcelain` + `git ls-files`): `backend/tests/test_us72_weather_map.py` ist **untracked** (`??`), nie eingecheckt. `test_us112_weather_map.py` ist getrackt (im Repo committed, liegt als kompilierte `.pyc` im `__pycache__` vor, also bereits gelaufen).
- BACKLOG.md US-112-Spec (Zeile 1385, bereits am 2026-06-30 dokumentiert) bestätigt unabhängig denselben Befund: „`fetch_weather_grid`, `fetch_weather_multigrid`, `WEATHER_REGIONS` und `_weather_map_cache` kommen ausschließlich in der untracked Testdatei … vor (test-first geschrieben, nie implementiert)".

**Example Mapping:**

📏 **Rule 1 — Die Test-Suite darf keine Tests enthalten, die gegen nie existierenden bzw. inzwischen entfernten Code laufen.**
Kontext: `pytest` soll ein verlässliches Signal für „ist die Wetter-Funktionalität intakt" sein. Ein Test, der strukturell nicht bestehen kann (ImportError vor jeder Assertion), ist Rauschen, kein Schutz.
- 🟢 Positiv: Given `pytest backend/tests/` läuft, When die Wetter-Tests ausgeführt werden, Then referenziert keine Testdatei mehr `fetch_weather_multigrid`, `WEATHER_REGIONS`, `_build_germany_grid` oder das alte `fetch_weather_grid` — alle Imports zeigen auf real existierenden Code.
- 🔴 Negativ: Given die alte Testdatei bliebe unverändert, When CI/lokaler Testlauf läuft, Then schlagen 6 Tests mit `ImportError`/`AttributeError` fehl, bevor überhaupt eine Assertion geprüft wird (aktueller IST-Zustand, unerwünscht).
- ⚠️ Edge: Given `test_us112_weather_map.py` deckt Endpoint-Schema, GRIB-Verarbeitung, Cache und Null-Handling bereits vollständig ab, When man prüft ob eine „angepasste" alte Datei zusätzlichen Wert brächte, Then wäre das reine Duplikation derselben Szenarien unter anderem Dateinamen — kein Mehrwert, nur Wartungslast.

📏 **Rule 2 — Die Bereinigung darf die reale Wetter-Funktionalität nicht anfassen.**
Kontext: Kein Bug in der Wetterkarte selbst; US-112 ist released und live verifiziert (2026-07-01). Scope ist ausschließlich Test-Suite-Hygiene.
- 🟢 Positiv: Given die Bereinigung ist durchgeführt, When man `backend/calculations/weather.py`, `backend/calculations/weather_grib.py` und `backend/main.py` (Wetter-Endpunkte) per Diff prüft, Then sind dort **keine** Änderungen vorhanden.
- 🔴 Negativ: Given jemand würde versuchen, `fetch_weather_multigrid` oder `WEATHER_REGIONS` nachträglich in `weather.py` zu ergänzen, „damit der Test passt", Then wäre das Scope Creep — es gibt keine Anforderung für eine Open-Meteo-Multigrid-Variante neben der bestehenden DWD/MET-Architektur.
- ⚠️ Edge: Given BUG-56 (Astronomie-Regression) hat kürzlich ebenfalls Tests korrigiert, When man BUG-57 umsetzt, Then bleibt das getrennt — keine Berührung von `test_astronomy_regression.py` oder verwandten Dateien.

✅ Questions (durch Code-Fakten bereits beantwortet, keine Rückfrage an Stephan nötig): Ist die alte Testdatei getrackt? Nein (untracked). Gibt es bereits eine Testdatei für die reale Architektur? Ja, vollständig (`test_us112_weather_map.py`). Existiert noch irgendein Rest der Multigrid-Funktionen im Backend? Nein (0 Treffer außerhalb der alten Testdatei).

**Scope:**
- Eingeschlossen: Entfernen der obsoleten Datei `backend/tests/test_us72_weather_map.py`. Kurzer Abgleich, dass `test_us112_weather_map.py` die relevanten Szenarien (Endpoint-Schema, Cache, Null-Handling bei Quellenausfall) bereits abdeckt (bereits in dieser Analyse erledigt, siehe Code-Verifikation oben).
- Ausgeschlossen: Jede Änderung an `calculations/weather.py`, `calculations/weather_grib.py`, `main.py` (Wetter-Endpunkte), `test_us112_weather_map.py`; keine neuen Wetter-Features; kein Anfassen von BUG-56 oder `test_astronomy_regression.py`; keine Änderung an CI-/Test-Runner-Konfiguration (nicht nötig — es gibt keine explizite Testdatei-Allowlist, `pytest` sammelt Dateien nach Namenskonvention `test_*.py` automatisch).

**Akzeptanzkriterien (Dev-Tooling — kein sichtbares App-Verhalten; der Effekt zeigt sich darin, dass die Test-Suite wieder vollständig grün läuft, nicht in der App selbst):**
- [ ] `backend/tests/test_us72_weather_map.py` existiert nach der Umsetzung nicht mehr im Repo.
- [ ] `pytest backend/tests/` läuft ohne `ImportError`/`AttributeError` bezogen auf `fetch_weather_multigrid`, `WEATHER_REGIONS`, `_build_germany_grid` oder `fetch_weather_grid` — diese Fehlerklasse ist vollständig verschwunden.
- [ ] `pytest backend/tests/test_us112_weather_map.py -v` läuft weiterhin unverändert grün (Regression: die reale Wetter-Testsuite ist von der Bereinigung unberührt).
- [ ] Voller Testlauf `pytest backend/tests/ -v` zeigt keine neuen Fehlschläge gegenüber dem Stand vor der Bereinigung (abgesehen vom Wegfall der 6 vorher fehlschlagenden Tests aus der entfernten Datei) — insbesondere bleiben die von BUG-56 bereits behobenen Astronomie-Tests unberührt grün.
- [ ] `git diff`/`git status` zeigt ausschließlich die Entfernung der einen Datei, keine Änderung an `calculations/weather.py`, `calculations/weather_grib.py` oder `main.py`.

**Pre-Mortem (Code-verifiziert):**
- 💀 Jemand „repariert" die alte Testdatei, indem `fetch_weather_multigrid`/`WEATHER_REGIONS` nachträglich in `weather.py` ergänzt werden, um Import-Fehler zu beheben. Auslöser: Testdatei sieht aus wie eine legitime Spec, Autofix-Reflex „Test grün machen" statt Root Cause zu hinterfragen. Frühwarnung: Diff zeigt neue Funktionen in `weather.py`, die von keinem Endpoint aufgerufen werden (toter Code). → Gegenmaßnahme: Diese Spec hält explizit fest, dass die Multigrid-Architektur nie gebaut wurde und durch US-112 (DWD/MET) ersetzt ist — Option B (Entfernen) ist die einzige empfohlene Richtung.
- 💀 Löschen ohne Genehmigung — Memory-Regel „Keine Löschung ohne Genehmigung" verlangt explizites Ja von Stephan vor dem Entfernen einer Datei. Auslöser: Analyse-Phase empfiehlt Entfernung, aber Freigabe ist Sache des Hauptthreads/Stephans, nicht dieser Analyse. → Gegenmaßnahme: Diese Spec spricht nur eine **Empfehlung** aus; das eigentliche Löschen erfolgt erst in der Implementierungsphase nach Stephans Freigabe des Tickets (Status bleibt hier bewusst „Ready for Analysis").
- 💀 Man verwechselt „Testdatei entfernen" mit „Testabdeckung sinkt". Auslöser: oberflächlich betrachtet werden 6 Tests weniger ausgeführt. Frühwarnung: Kein Frühwarnsignal nötig, da bereits code-verifiziert. → Gegenmaßnahme: Code-Vergleich zeigt, dass `test_us112_weather_map.py` dieselben Szenarien (Endpoint-Schema, Cache-Verhalten, Quellenausfall-Null-Handling, sogar granularer bis auf GRIB-Ebene) bereits gegen die reale Architektur abdeckt — kein Abdeckungsverlust, nur Wegfall von Duplikat-Rauschen gegen nie existierenden Code.
- 💀 Eine übersehene Abhängigkeit (z. B. ein Test-Runner-Config-Eintrag, eine `conftest.py`-Fixture, die nur von dieser Datei gebraucht wird) bricht beim Entfernen. Auslöser: nicht geprüft, ob `conftest.py` oder `pytest.ini`/`pyproject.toml` die Datei namentlich referenzieren. Frühwarnung: `pytest`-Sammlung wirft nach Entfernen einen unerwarteten Fehler, der nicht mit der entfernten Datei zusammenhängt. → Gegenmaßnahme: In der Implementierungsphase vor dem Löschen kurz `grep -r "test_us72_weather_map" backend/` (auch in Config-Dateien) prüfen — laut bisheriger Analyse gibt es keine Referenzen außerhalb der Datei selbst, aber das ist ein Zwei-Sekunden-Check wert.
- 💀 Verwechslung mit BUG-56: Jemand überträgt das dortige Muster („Testwert korrigieren, Produktionscode unangetastet") 1:1 auf BUG-57, obwohl hier kein Referenzwert falsch ist, sondern die referenzierte Funktion nie existierte — eine Korrektur (Option A: Testdatei anpassen) wäre in Wahrheit ein Neuschreiben der kompletten Datei gegen eine völlig andere Architektur, keine Wertkorrektur. → Gegenmaßnahme: Diese Spec benennt den Unterschied explizit (siehe Implementierungsoptionen unten); Empfehlung ist Entfernen, nicht Anpassen.

**Implementierungsoptionen:**

*Option A — Testdatei an die tatsächliche US-112-Architektur anpassen (neu schreiben)* · Aufwand: mittel–groß
- Vorgehen: `test_us72_weather_map.py` komplett umschreiben, um `calculations/weather_grib.py` (GRIB-Dekodierung, IDW-Interpolation, PNG-Encoding, DWD+MET-Merge) sowie das reale `/weather-map`-Endpoint-Schema zu testen.
- Vorteile: keine.
- Nachteile/Risiken: `test_us112_weather_map.py` deckt exakt diese Szenarien bereits vollständig ab (code-verifiziert, siehe oben) — Ergebnis wäre eine zweite, redundante Testdatei mit anderem Namen für dieselbe Architektur. Doppelte Wartungslast (zwei Dateien bei jeder künftigen Wetter-Änderung pflegen), ohne zusätzlichen Testwert. Klarer Fall von unnötigem Aufwand.
- Aufwand: mittel–groß (vollständiges Neuschreiben von ca. 260 Zeilen Testcode)

*Option B — Testdatei vollständig entfernen* · Aufwand: minimal
- Vorgehen: `backend/tests/test_us72_weather_map.py` löschen (Datei ist untracked, kein Git-History-Verlust, da nie committed). Kurzer Bestätigungs-Check, dass `test_us112_weather_map.py` weiterhin grün läuft.
- Betroffene Dateien: nur `backend/tests/test_us72_weather_map.py` (Löschung).
- Vorteile: Beseitigt exakt das gemeldete Problem (ImportError/AttributeError bei Testläufen), keine Redundanz, kein Risiko für die reale Wetter-Funktionalität (die unangetastet bleibt), minimaler Aufwand, sauberste Lösung angesichts vollständiger Abdeckung durch `test_us112_weather_map.py`.
- Nachteile/Risiken: Löschung erfordert laut Memory-Regel explizite Genehmigung von Stephan vor Ausführung (siehe Pre-Mortem) — kein technisches Risiko, aber ein Prozess-Gate.
- Aufwand: minimal (eine Dateilöschung + Regressionslauf)

*Option C — Hybrid* · nicht sinnvoll
- Geprüft, aber verworfen: Es gibt keine Teilmenge von `test_us72_weather_map.py`, die einen Testwert hätte, den `test_us112_weather_map.py` nicht bereits abdeckt — ein Hybrid (z. B. „nur die Cache-Tests migrieren") würde denselben Code ein drittes Mal testen. Kein Hybrid-Vorteil identifizierbar.

✅ **Empfehlung: Option B** — Die Testdatei testet eine Architektur (Open-Meteo-Multigrid mit `fetch_weather_multigrid`/`WEATHER_REGIONS`), die nachweislich nie gebaut wurde und durch US-112 (DWD ICON-D2 + MET Norway) vollständig ersetzt wurde, bevor sie je existierte. `test_us112_weather_map.py` deckt die reale Architektur bereits vollständig und mit größerer Tiefe ab (bis auf GRIB-Byte-Ebene). Option A würde nur Redundanz erzeugen; Option C bietet keinen Vorteil. Einzige Voraussetzung vor Ausführung: Stephans explizite Löschfreigabe (Memory-Regel), da die Datei sichtbaren Testcode enthält, auch wenn sie nie Teil des Git-Repos war.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `backend/tests/test_us72_weather_map.py` (zu entfernende Datei, untracked), `backend/tests/test_us112_weather_map.py` (bereits vorhandene, vollständige Ersatz-Abdeckung, unverändert zu lassen), `backend/calculations/weather.py` + `backend/calculations/weather_grib.py` + `backend/main.py` (reale Wetter-Architektur, nicht anzufassen). Keine CI-/Test-Runner-Konfigurationsdatei referenziert die alte Testdatei namentlich (Namenskonvention `test_*.py` reicht für automatisches Einsammeln durch `pytest`).
- [x] Implementierungsoptionen: A (Testdatei anpassen) / B (Testdatei entfernen) / C (Hybrid, verworfen)
- [x] Empfehlung: **Option B** — Entfernen, vorbehaltlich Stephans expliziter Löschfreigabe

**Testplan:**
- [ ] Automatisiert (Harness): Nach Entfernen der Datei `pytest backend/tests/ -v` vollständig laufen lassen — erwartet: keine `ImportError`/`AttributeError` mehr zu `fetch_weather_multigrid`/`WEATHER_REGIONS`/`_build_germany_grid`/`fetch_weather_grid`; `test_us112_weather_map.py` weiterhin vollständig grün (Regressionscheck der realen Wetter-Tests); `test_astronomy_regression.py` (BUG-56) weiterhin unberührt grün.
- [ ] Manuell: `git status` nach der Änderung zeigt ausschließlich die Entfernung der einen Datei, keine Modifikation an `weather.py`/`weather_grib.py`/`main.py`. Kurzer `grep -r "test_us72_weather_map" backend/` vor dem Löschen, um versteckte Referenzen (Config/`conftest.py`) auszuschließen.

---

### BUG-58 · Wolken-/Niederschlag-Umschalter im Karten-Tab soll auf 50-km-Radius statt auf Europa zoomen (Änderung an US-112/BUG-55) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix (bewusste Verhaltensänderung an US-112/BUG-55, kein neuer unabhängiger Bug) |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-03 |
| **Abgeschlossen** | 2026-07-04 |

**Beschreibung:** Tippt man im Karten-Tab auf den „Wolken"- oder „Niederschlag"-Umschalter, zentriert und zoomt die Karte auf eine Mehrländer-Ansicht (Frankreich bis Nord-Norwegen). Gewünscht: Die Karte soll stattdessen auf einen Kartenausschnitt von ca. 50 km Radius um die aktuelle Kartenmitte bzw. um den zuletzt betrachteten Standort zoomen.

**Testergebnis (2026-07-03):** Von Stephan im Browser getestet. Kern-AK bestätigt: „Die Funktionalität hat geklappt" — der Umschalter zoomt jetzt auf den ca. 50-km-Ausschnitt statt auf die Europa-Ansicht. Übrige Testschritte (Breitengrad-Vergleich Nord/Berlin, mehrfaches Umschalten, frischer Seitenaufruf, 5-Tabs-Regressionscheck) wurden nicht explizit kommentiert — Annahme: unauffällig, da nicht negativ erwähnt. Zwei unabhängige Zusatzbeobachtungen ausgelagert in eigene Tickets (kein BUG-58-Scope, technisch anderer Codepfad, siehe Bezug): **BUG-59** (Wolken-/Regen-Overlay beim Zeitregler nicht sichtbar) und **TASK-52** (Legende Wolken/Regen von Mitte-links nach unten-links über den Zeitregler verschieben).

**Bezug:** Dies ist eine **bestätigte Änderung an bereits abgenommenem Verhalten aus BUG-55** [x] (Wetterkarte: Auto-Zoom beim Ein-/Ausschalten des Wolken-/Niederschlag-Layers im Map-Tab) und **US-112** [x] (Wetter-Overlay DWD/MET, Mehrländer-Ansicht als bewusste Design-Entscheidung). Stephan hat in der Analyse-Klärung bestätigt: Gemeint ist der bestehende „Wolken"/„Niederschlag"-Umschalt-Knopf direkt in der Kartenansicht (`WeatherMap.setMode`), nicht ein neuer Klick-Pfad von Feed/Scout/Detail-Sheet aus. Ihm ist bewusst, dass dies das in US-112 gewünschte „alle vier Gebiete gleichzeitig sichtbar"-Verhalten ersetzt — keine Regression, sondern eine gewollte Verhaltensänderung.

---

**Implementation Spec**

**Klärung erfolgt (2026-07-03):** Stephan hat auf Rückfrage bestätigt, dass er den bestehenden „Wolken"/„Niederschlag"-Umschalt-Knopf direkt im Karten-Tab meint (`WeatherMap.setMode('clouds'|'precip')`, `web/index.html` Zeile 992–994 und 4356–4660). Ihm ist bewusst, dass dieser Knopf seit US-112 absichtlich auf eine Mehrländer-Ansicht zoomt (Server-Bounds `BBOX_S=43.0, BBOX_N=71.5, BBOX_W=3.0, BBOX_E=21.0`, `backend/calculations/weather_grib.py` Zeile 73–76; frontend-seitige `_FALLBACK_BOUNDS`, `web/index.html` Zeile ~4372) — und dass diese Umstellung eine bewusste Änderung an bereits abgenommenem US-112/BUG-55-Verhalten ist, kein neuer, unabhängiger Bug. Gewünschtes neues Verhalten: Der Knopf zoomt künftig auf einen ca. 50-km-Radius um die aktuelle Kartenmitte bzw. um den zuletzt betrachteten Standort statt auf die volle Mehrländer-Bounding-Box.

📎 Code-Verifikation: `web/index.html` (`WeatherMap.setMode`/`_render`/`_gridBounds`, Zeile 4356–4660; `MapView.init`/`loadMarkers`, Zeile 4162–4211) sowie `backend/main.py` (Zeile 738, 1925, 1948: `bounds` kommt immer von `weather_grib.overlay_bounds()`) und `backend/calculations/weather_grib.py` (Zeile 73–76, 553–555) gelesen am 2026-07-03. Bestätigt: Die einzigen Aufrufer von `WeatherMap.setMode` sind die beiden Toggle-Buttons im Karten-Tab (Zeile 992–994) — kein Aufruf aus Feed/Scout/Detail-Sheet/Location-Liste, daher kein weiterer Code-Pfad betroffen.

**Example Mapping:**

📏 **Rule:** Der Wolken-/Niederschlag-Umschalter im Karten-Tab zoomt auf einen ca. 50-km-Radius um die aktuelle Kartenmitte bzw. um den zuletzt betrachteten Standort, statt auf die volle Mehrländer-Bounding-Box.
- 🟢 Example: Die Karte zeigt gerade Berlin in normaler Ansicht. Ich tippe auf „Wolken". Die Karte zoomt danach auf einen Ausschnitt von ungefähr 50 km rund um Berlin — nicht auf eine Ansicht, die Frankreich bis Norwegen zeigt.
- 🟢 Example: Ich habe die Karte zuvor auf einen Standort in Norwegen verschoben. Ich tippe auf „Niederschlag". Die Karte zoomt auf einen Ausschnitt von ungefähr 50 km rund um diesen Standort in Norwegen — der Ausschnitt wirkt dabei genauso groß wie bei einem Standort in Berlin, nicht merklich größer oder kleiner.
- 🟢 Example: Ich habe „Wolken" bereits aktiviert und die Karte zeigt einen 50-km-Ausschnitt. Ich wechsle zu „Niederschlag". Die Karte bleibt auf demselben Ausschnitt zentriert, springt nicht wieder auf die große Mehrländer-Ansicht zurück.
- 🟢 Example: Es ist noch kein Standort bekannt und die Karte hat keine sinnvolle Mitte (z. B. direkt nach dem Start ohne vorherige Standortwahl). Ich tippe auf „Wolken". Die Karte zeigt einen sinnvollen Ausschnitt (z. B. die zuletzt bekannte oder eine Standard-Ansicht) statt eines Absturzes, einer leeren Karte oder eines Rückfalls auf die alte Europa-Ansicht.

**Akzeptanzkriterien:**
- [ ] Tippe ich im Karten-Tab auf „Wolken" oder „Niederschlag", zeigt die Karte danach einen Ausschnitt von ungefähr 50 km rund um die aktuell sichtbare Kartenmitte bzw. den zuletzt betrachteten Standort — nicht mehr die bisherige Ansicht, die ganz Mitteleuropa bis Nord-Norwegen zeigt.
- [ ] Der Kartenausschnitt wirkt bei einem Standort weit im Norden (z. B. Norwegen) genauso groß wie bei einem Standort in Berlin — kein spürbar größerer oder kleinerer Ausschnitt allein wegen der geografischen Breite.
- [ ] Schalte ich mehrfach hintereinander zwischen „Wolken" und „Niederschlag" um, bleibt der Kartenausschnitt stabil auf derselben Stelle zentriert — es springt nicht bei jedem Umschalten neu oder zurück zur alten Europa-Ansicht.
- [ ] Ist beim Umschalten kein sinnvoller Standort oder Kartenmittelpunkt bekannt, zeigt die App trotzdem eine sinnvolle Kartenansicht (keine leere Karte, kein Absturz, kein unbeabsichtigter Rücksprung auf die alte Mehrländer-Ansicht).
- [ ] Diese Änderung ist bewusst gewollt: Der Karten-Tab zeigt beim Wolken-/Niederschlag-Umschalten künftig **nicht mehr automatisch alle vier bisherigen Gebiete gleichzeitig** — das ist die absichtliche Neuerung dieses Tickets und keine Regression zum früheren, in US-112 abgenommenen Verhalten.

**Pre-Mortem:**
- 💀 Szenario: Der 50-km-Radius wird als fester Zoom-Level umgesetzt (z. B. „immer Zoomstufe 10"), ohne den Breitengrad zu berücksichtigen. Da Kartenzoomstufen in Pixel pro Grad und nicht in Kilometern gemessen werden, wirkt derselbe Zoom-Level bei einem Standort in Norwegen (69°N) deutlich stärker vergrößert/verzerrt als bei Berlin (52°N) — der Ausschnitt wäre dort spürbar zu klein oder zu groß statt überall ungefähr 50 km. → Gegenmaßnahme: Der Ausschnitt wird über ein tatsächlich berechnetes Rechteck um den Mittelpunkt bestimmt (Standort plus/minus einem Abstand, der die geografische Breite berücksichtigt), nicht über eine pauschale Zoomstufe. Als Testschritt: Norwegen-Standort und Berlin-Standort nacheinander prüfen, ob beide Ausschnitte ähnlich groß wirken.
- 💀 Szenario: Der Nutzer verschiebt die Karte manuell (pannt) und schaltet danach zwischen „Wolken" und „Niederschlag" um. Wenn die neue Zoom-Logik nicht robust auf die jeweils aktuelle Kartenmitte reagiert, könnte der Ausschnitt beim zweiten Umschalten ungewollt auf eine ältere, nicht mehr sichtbare Position zurückspringen statt auf die Position, die der Nutzer gerade sieht. → Gegenmaßnahme: Als Testschritt „mehrfach hintereinander umschalten, dazwischen die Karte verschieben" verankern und prüfen, dass der Ausschnitt konsistent der aktuell sichtbaren Mitte folgt.
- 💀 Szenario: Beim allerersten Öffnen des Karten-Tabs (oder wenn aus irgendeinem Grund kein Standort/keine Kartenmitte ermittelbar ist) gibt es keinen sinnvollen Mittelpunkt für den 50-km-Ausschnitt. Ohne Absicherung könnte das zu einer leeren Karte, einem JavaScript-Fehler oder einem unbeabsichtigten Rückfall auf die alte, breite Ansicht führen. → Gegenmaßnahme: Ein sinnvoller Rückfall-Mittelpunkt (z. B. zuletzt bekannter Standort oder ein Standard-Ort) wird als Edge-Case-AK verankert und im Testplan geprüft.
- 💀 Szenario: Die Umstellung wird versehentlich als Regression zu US-112 gemeldet, weil ein Tester (oder Stephan selbst später) das neue, kleinere Kartenbild mit einem Bug verwechselt, da US-112 ausdrücklich „alle vier Gebiete gleichzeitig sichtbar" als Ziel hatte. → Gegenmaßnahme: Explizit als eigenes AK verankert (siehe oben), damit die Änderung klar als gewollt dokumentiert ist und nicht fälschlich zurückgebaut wird.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (final, Annahme A bestätigt durch Stephan)
- [x] Pre-Mortem durchgeführt (4 Szenarien, zugeschnitten auf die bestätigte Annahme A)
- [x] Architektur analysiert: `web/index.html` (`WeatherMap.setMode`/`_render`/`_gridBounds`, Zeile 4356–4660; `MapView.init`, Zeile 4162–4211) sowie `backend/main.py` + `backend/calculations/weather_grib.py` als Bounds-Quelle
- [x] Designer-Check: visuell? → Nein, keine neue UI-Komponente, nur ein bestehender Knopf verhält sich anders (kleinerer statt größerer Kartenausschnitt) — `fotoalert-designer` nicht erforderlich.
- [x] Implementierungsoption: Eine Option (siehe unten), kein Optionsvergleich mehr nötig
- [x] Empfehlung: siehe unten

**Implementierungsoption — Bestehenden Karten-Tab-Toggle auf 50-km-Radius statt Mehrländer-BBox umstellen:**
- App-Wirkung: Der „Wolken"/„Niederschlag"-Knopf im Karten-Tab zoomt künftig nur noch auf die Umgebung der aktuellen Kartenmitte, nicht mehr auf Deutschland–Norwegen gleichzeitig.
- Vorgehen: In `WeatherMap.setMode` den Aufruf `MapView.map.fitBounds(this._gridBounds(), …)` durch einen 50-km-Bounds-Aufruf um `MapView.map.getCenter()` ersetzen — das Bounds-Rechteck wird breitengradabhängig berechnet (`Δlon = 50km / (111km × cos(lat))`), damit der Ausschnitt bei nördlichen Standorten (z. B. Norwegen) nicht optisch größer/kleiner wirkt als bei Berlin (Mercator-Verzerrung, siehe Pre-Mortem). Für den Fall, dass keine sinnvolle Kartenmitte bekannt ist, greift ein Rückfallwert (zuletzt bekannter Standort oder Standard-Ort) statt eines Absturzes oder Rücksprungs auf die alte Mehrländer-Bounds.
- Betroffene Datei: `web/index.html` (`WeatherMap.setMode`).
- Aufwand: klein.

✅ **Empfehlung:** Umsetzung wie oben beschrieben — kleinster Eingriff, direkt am bestätigten Zielort, mit breitengradkorrigierter Radius-Berechnung und abgesichertem Rückfallverhalten für den Fall fehlender Kartenmitte.

**Testplan:**
- [ ] Automatisiert (Harness): Reines Frontend-/Leaflet-Verhalten, nicht über `pytest` prüfbar (analog BUG-55). Falls die Radius-Berechnung als eigenständige, testbare Funktion ausgelagert wird (z. B. „berechne Bounds-Rechteck aus Mittelpunkt + Breitengrad"), dafür einen `pytest`-Fall ergänzen, der für einen Berlin-Breitengrad (~52°N) und einen Nord-Norwegen-Breitengrad (~69°N) prüft, dass beide berechneten Rechtecke einem ähnlichen Kilometer-Radius entsprechen (Toleranzband, kein exakter Wert).
- [ ] Manuell (unter http://localhost:8000):
  1. Karten-Tab öffnen, Kartenmitte auf Berlin lassen, „Wolken" antippen — erwartet: Kartenausschnitt zeigt ungefähr 50 km um Berlin, nicht mehr Frankreich–Norwegen.
  2. Karte manuell auf einen Standort in Norwegen verschieben (falls ein Norwegen-Standort in der App vorhanden ist), „Niederschlag" antippen — erwartet: Ausschnitt wirkt ähnlich groß wie bei Berlin, nicht sichtbar größer/kleiner.
  3. Mehrfach hintereinander zwischen „Wolken" und „Niederschlag" umschalten, dazwischen die Karte leicht verschieben — erwartet: Ausschnitt bleibt stabil auf der jeweils aktuellen Mitte, kein Zurückspringen zur alten Europa-Ansicht.
  4. Karten-Tab ohne zuvor gewählten Standort/Kartenmitte öffnen (z. B. direkt nach App-Start) und „Wolken" antippen — erwartet: sinnvolle Kartenansicht statt leerer Karte oder Fehler.

---

### BUG-59 · Zeitregler im Karten-Tab: Kein Wolken-/Regen-Overlay sichtbar `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-07-03 |
| **Abgeschlossen** | 2026-07-04 |

**Beschreibung:** Beim Bedienen des Zeitreglers im Karten-Tab (mit dem man durch die Zeitpunkte der Wolken-/Niederschlag-Wettervorhersage blättert) hat Stephan kein Wolken- oder Regen-Overlay auf der Karte gesehen — die erwartete Wetterfläche erscheint visuell nicht.

**Bezug:** Beobachtet als zusätzlicher, unabhängiger Befund beim Testen von **BUG-58** [x] (Zoom-Umstellung auf 50-km-Radius) — technisch verifiziert **keine Regression durch BUG-58**: Der Kartenzoom-Code (`WeatherMap.setMode`/Zoom-Logik) und das Overlay-Rendering (`WeatherMap._render()` → `L.imageOverlay(url, bounds)`, Bild-URL aus `_frameUrl(this.sliderIdx)`, Bounds aus `this.data.bounds` bzw. `_FALLBACK_BOUNDS`) sind komplett getrennte Codepfade. Verwandt mit **US-112** [x] (liefert die Overlay-Daten/-Bilder) und **BUG-55** [x] (früherer Zoom-Fix, anderer Mechanismus).

---

## Analyse (2026-07-04)

**Annahmen-Protokoll:**
- ✅ Klar aus Kontext ableitbar: Die Fehlerbeschreibung „kein Overlay sichtbar" bezieht sich auf den normalen App-Betrieb (Server erreichbar, Wetterdaten schon mal erfolgreich gebaut — US-112 ist live), nicht auf einen kompletten Erstlauf ohne jeden Cache.
- ⚠️ Annahme: Der von Stephan beobachtete Fall ist der Regelfall (Karte auf einen Standort in Deutschland/Mitteleuropa gezoomt, „Wolken" oder „Niederschlag" aktiv, Regler bewegt) — nicht ein Sonderfall wie „Server frisch neu gestartet, Wetterkarten-Cache noch komplett leer". Bitte bestätigen, ob das der beobachtete Fall war, oder ob die App zu dem Zeitpunkt frisch gestartet war.
- 🔴 Funktional kritisch, aber ohne echten Browser/DevTools-Zugriff nicht abschließend aus dem Code allein entscheidbar: Ob das Overlay tatsächlich technisch fehlt (leeres/fehlerhaftes Bild, keine Bounds) oder ob es korrekt rendert, aber bei geringer Wolken-/Niederschlagsmenge in der Region so blass ist, dass es im jetzt kleinen 50-km-Kartenausschnitt kaum auffällt. Die Code-Lektüre liefert eine belastbare Best-Einschätzung (siehe Pre-Mortem/Root-Cause unten), die per echtem Live-Test noch zu bestätigen ist.

**Scope:** Eingeschlossen ist die Klärung und Behebung, warum das Wetter-Overlay im Karten-Tab nach der 50-km-Zoom-Umstellung (BUG-58) nicht mehr wahrnehmbar ist. Ausdrücklich ausgeschlossen: Änderungen an der Zoom-Logik selbst (BUG-58 bleibt wie freigegeben), Änderungen an der Wetterdaten-Beschaffung/-Qualität (US-112 bleibt wie abgenommen).

**Example Mapping:**
- 📏 Rule: Wenn im Karten-Tab „Wolken" oder „Niederschlag" aktiv ist und der Zeitregler auf einen Zeitpunkt mit vorhandenen Wetterdaten steht, muss über der Karte eine farbige Wetterfläche sichtbar sein, die im aktuell gezoomten 50-km-Ausschnitt tatsächlich wahrnehmbar ist (nicht nur technisch vorhanden, sondern für Stephan sichtbar).
  - 🟢 Example: Karte ist auf einen Standort mit deutlicher Bewölkung/Niederschlag gezoomt (z. B. laut Wettervorhersage bewölkt oder regnerisch), „Wolken" bzw. „Niederschlag" ist aktiv → eine deutlich erkennbare, eingefärbte Fläche liegt über der Karte.
- 📏 Rule: Wenn am aktuellen Kartenausschnitt praktisch keine Bewölkung/kein Niederschlag vorliegt, ist die Fläche zwar technisch vorhanden, aber nahezu unsichtbar (sehr helle/blasse Farbe) — das ist kein Bug, sondern korrekte Darstellung von „kein Wetterphänomen".
  - 🟢 Example: Klarer Himmel am gezoomten Standort, „Wolken" aktiv → die Fläche ist so hell, dass sie kaum vom Kartenhintergrund zu unterscheiden ist (gewolltes Verhalten laut Farbskala, kein Fehler).
- 📏 Rule: Wenn die Wetterkarten-Daten für den Server noch nicht bereitstehen (Cache leer/im Aufbau), zeigt die App einen Hinweis „Wetterdaten werden geladen …" statt eines stillen Leerbilds.
  - 🟢 Example: Server frisch gestartet, noch kein Wetterkarten-Cache gebaut, Stephan tippt auf „Wolken" → Hinweistext erscheint, keine unerklärte leere Karte.

**Keine offenen ❓-Questions mehr, da die kritische Unsicherheit (Ursache technisch vs. Wahrnehmung) als Root-Cause-Einschätzung mit Sicherheitsstufe unten dokumentiert ist und den nachfolgenden Optionen zugrunde liegt.**

**Akzeptanzkriterien:**
- [ ] Ist am aktuell gezoomten 50-km-Kartenausschnitt tatsächlich Bewölkung bzw. Niederschlag vorhergesagt, sieht Stephan nach Antippen von „Wolken" bzw. „Niederschlag" eine deutlich wahrnehmbare, eingefärbte Fläche über der Karte — nicht nur eine kaum sichtbare, blasse Fläche.
- [ ] Beim Bewegen des Zeitreglers ändert sich die eingefärbte Fläche sichtbar mit dem gewählten Zeitpunkt (z. B. Fläche wird bei einer Stunde mit mehr Niederschlag sichtbar kräftiger).
- [ ] Ist am gezoomten Ausschnitt praktisch keine Bewölkung/kein Niederschlag vorhergesagt, bleibt die Fläche bewusst sehr hell/kaum sichtbar — das ist als korrektes Verhalten erkennbar (z. B. weil die Legende unten links weiterhin die aktive Farbskala zeigt), nicht als Fehlzustand.
- [ ] Edge Case: Sind die Wetterkarten-Daten auf dem Server noch nicht bereit (z. B. kurz nach Serverstart), zeigt die App den Hinweistext „Wetterdaten werden geladen …" statt einer stillen, unerklärten Leerfläche.
- [ ] Edge Case: Beim Umschalten zwischen „Wolken" und „Niederschlag" sowie beim Bewegen des Zeitreglers bleibt die Legende (Farbskala unten links) korrekt zur aktiven Ansicht passend sichtbar.

**Pre-Mortem (mit Code-Verifikation):**

📎 Code-Verifikation (2026-07-04): `web/index.html` Zeile 4456–4783 (`WeatherMap`) sowie `backend/main.py` Zeile 1895–1970 und `backend/calculations/weather_grib.py` Zeile 73–81/553–641 gelesen.

- Bestätigt: `_frameUrl(idx)` (Zeile 4543–4548) liefert `null`, wenn `this.data`/`this.data.frames` fehlt oder `idx >= arr.length`; in diesem Fall ruft `_render()` (Zeile 4566–4587) sofort `_clearOverlay()` auf und bricht ab — es gibt **keinen** Pfad, der eine syntaktisch kaputte oder 404-URL an `L.imageOverlay` übergibt. Bei gültigem Index liefert das Backend (`main.py` Zeile 1936–1944) entweder eine echte `/weather-map/png/{field}/{idx}`-URL oder explizit `null` (kein Fake-Link) — durch den bestehenden Test `test_weather_map_endpoint_schema` (`backend/tests/test_us112_weather_map.py` Zeile 208–232) mit abgesichert.
- Bestätigt: `this.data.bounds` wird ausschließlich in `_fetch()` (Zeile 4672–4696) aus der Server-Antwort gesetzt. Vor dem ersten erfolgreichen Fetch ist `this.data === null`; `_render()` prüft das explizit (`!this.data` → sofortiger Abbruch, kein Fallback-Render mit „falschen" Bounds). `setMode()` (Zeile 4735–4766) ruft `await this._fetch()` **vor** `_render()` auf — es gibt keinen erkennbaren Race, bei dem gerendert wird, bevor die Daten (oder zumindest `ready:false` mit leeren Frames) da sind. `_FALLBACK_BOUNDS` (Zeile 4472) wird nur in `_render()`/`_gridBounds()` als Ersatzwert verwendet, falls `this.data.bounds` fehlt, obwohl `this.data` selbst existiert (z. B. `ready:false`-Antwort ohne Bounds-Feld) — dieser Pfad liefert aber ohnehin kein Bild, da `_frameUrl()` bei leeren `frames`-Arrays `null` zurückgibt.
- **Root-Cause-Einschätzung (beste Einschätzung aus Code-Lektüre, noch per Live-Test zu bestätigen):** `overlay_bounds()` (`weather_grib.py` Zeile 553–555, Konstanten Zeile 73–76) liefert immer die feste Mehrländer-BBox `[[43.0, 3.0], [71.5, 21.0]]` — das sind ca. 2.850 km (Nord-Süd) × ca. 1.350 km (Ost-West, bei 52°N). Das PNG-Overlay wird über exakt diese Fläche gelegt (`render_all_pngs`, Zeile 628–640, Bildgröße `PNG_W=360 × PNG_H=420`). Seit BUG-58 zoomt die Karte beim Aktivieren von „Wolken"/„Niederschlag" aber nur noch auf einen 50-km-Radius (`_localBounds()`, Zeile 4712–4722) um die aktuelle Kartenmitte — das ist gemessen an der Gesamtfläche des Overlays ein sehr kleiner Ausschnitt (grob 100 km Durchmesser von ca. 2.850 km Gesamthöhe, also ca. 3–4 % der Fläche). Das Overlay-Bild wird technisch korrekt geladen und positioniert, ist aber im sichtbaren 50-km-Fenster nur noch ein kleiner, evtl. sehr gleichmäßig eingefärbter Bildausschnitt. Zusätzlich sind die Farbskalen bei niedrigen Werten sehr hell (`_CLOUD_COLORS`/`_PRECIP_MM_COLORS`, Zeile 4475–4486: 0 % Wolken = `#c8e8ff`, 0 mm Niederschlag = `#eaf4ff` — beides sehr helle Pastelltöne). Bei durchschnittlichem oder niedrigem Wolken-/Niederschlagswert am gewählten Ort wirkt die Fläche dadurch nahezu unsichtbar vor dem ohnehin hellen Karten-Tile-Hintergrund. **Das erklärt das beobachtete Verhalten plausibel als Wahrnehmungsproblem (Kombination aus BUG-58-Zoomverkleinerung + heller Farbskala bei Normalwetter), nicht als technischen Datenfehler** — abschließend zu bestätigen ist das nur per echtem Live-Test mit bekannt bewölktem/regnerischem Zielort, da sich Bildinhalt (tatsächliche Wolken-/Niederschlagswerte an dem Tag) nicht aus dem Code ablesen lässt.
- Kein erkennbarer z-Index-/Pane-Konflikt: `weatherPane` liegt bei `zIndex: 250`, explizit zwischen Tile-Layer (200) und Markern (400, Kommentar Zeile 4529); `L.imageOverlay` wird mit `opacity: 1` (Zeile 4581, Transparenz steckt im PNG-Alphakanal) und `interactive: false` erzeugt — beides unauffällig.

- 💀 Szenario: Ein zukünftiger Test an einem Tag mit wenig Wetteraktivität am Standort wird erneut als „Overlay fehlt" gemeldet, obwohl es korrekt (aber blass) rendert. → Gegenmaßnahme: AK-3 verankert genau diesen Fall als erwartetes, kein fehlerhaftes Verhalten; Testplan schreibt einen Standort mit bekannt hoher Bewölkung/Niederschlag als Testbedingung vor.
- 💀 Szenario: Die gewählte Option (z. B. Mindest-Deckkraft/kräftigere Farbskala) macht das Overlay bei echtem Klarwetter fälschlich sichtbar und irreführend (Nutzer denkt, es gebe Wolken, wo keine sind). → Gegenmaßnahme: Bei der Umsetzung nur die Wahrnehmbarkeit bei tatsächlich vorhandenen Werten verbessern (z. B. Mindest-Opacity/kräftigerer Kontrast nur oberhalb eines Schwellwerts), nicht die Farbskala bei echten Nullwerten verfälschen — als Vorgabe in die Implementierung geben.
- 💀 Szenario: Der Cache ist zum Testzeitpunkt tatsächlich leer/im Aufbau (Server kürzlich neu gestartet) und der Hinweistext „Wetterdaten werden geladen …" wurde übersehen oder war zu unauffällig platziert. → Gegenmaßnahme: Edge-Case-AK-4 verankert den Hinweistext explizit; Testplan prüft auch den Fall „Server frisch gestartet".
- 💀 Szenario: Eine Korrektur an der Farbskala/Opacity wird versehentlich als generelle Wetter-Darstellungsänderung missverstanden und beeinträchtigt die Lesbarkeit bei starkem Wetter (Übersättigung). → Gegenmaßnahme: Regressionscheck der Legende und der bestehenden Farbstopps als Testschritt, nicht nur der Niedrigwert-Fälle.

**Architektur-Analyse:**
- Frontend: `web/index.html`, Objekt `WeatherMap` (Zeile 4456–4783) — Zustand (`mode`, `sliderIdx`, `data`), Rendering (`_render`, `_frameUrl`, `_colorInterp`/Farbpaletten), Zoom-Interaktion (`setMode`, `_localBounds` aus BUG-58).
- Backend: `backend/main.py` Endpoints `/weather-map` (Zeile 1895–1955) und `/weather-map/png/{field}/{idx}` (Zeile 1958–1970); Hintergrund-Bau `_build_weather_map()` (Zeile 713–753, alle 3h per Scheduler, Zeile 1316).
- Datenquelle/Berechnung: `backend/calculations/weather_grib.py` — feste BBox-Konstanten (Zeile 73–81), `overlay_bounds()` (553–555), Farbwerte/PNG-Encoding (~Zeile 500–546), `build_weather_overlay`/`render_all_pngs` (558–640). Datenquellen: DWD ICON-D2/ICON-EU (GRIB) + MET Norway.
- Kein Cache-Verzeichnis auf Datei-Ebene identifiziert — die Overlay-PNGs liegen laut Code nur im Prozess-Speicher (`_weather_map_png`-Dict in `main.py`, kein Disk-Cache-Pfad im Code sichtbar). Falls es zusätzlich einen Disk-Cache gibt, ist das aus dem gelesenen Code nicht ersichtlich — als offener Punkt markiert, nicht behauptet.
- Designer-Check: Diese Analyse berührt ggf. Farbintensität/Opacity einer bestehenden Komponente (keine neue UI) — visuell relevant, `fotoalert-designer` wird vor der finalen Farb-/Opacity-Entscheidung in der Implementierungsphase hinzugezogen, sofern Option B/C gewählt wird.

**Implementierungsoptionen:**

Option A — Nur Hinweis/Aufklärung, keine Code-Änderung an der Darstellung:
- App-Wirkung: Die App bleibt wie sie ist; ergänzt wird lediglich ein kleiner Hinweistext oder eine Tooltip-Erklärung, dass eine sehr helle Fläche „kaum Wolken/Niederschlag" bedeutet.
- Vorgehen: Kleiner Text-/UI-Hinweis in der Legende oder beim ersten Aktivieren.
- Vorteile: Minimaler Aufwand, keine Gefahr neuer optischer Fehleinschätzungen.
- Nachteile: Löst das eigentliche Problem nicht — bei geringem Wetter bleibt die Fläche für Stephan weiterhin praktisch unsichtbar, nur jetzt „erklärt". Wirkt eher wie ein Pflaster als eine Lösung.
- Aufwand: klein.

Option B — Overlay im gezoomten 50-km-Ausschnitt sichtbarer machen (Kontrast/Mindest-Deckkraft anpassen):
- App-Wirkung: Wenn am gezoomten Ort tatsächlich Wolken oder Niederschlag vorhergesagt sind, ist die Fläche deutlich als Farbfläche erkennbar — auch bei niedrigen bis mittleren Werten wirkt sie nicht mehr fast unsichtbar. Bei echtem Klarwetter bleibt sie bewusst sehr hell (kein falsches Signal).
- Vorgehen: Farbskalen (`_CLOUD_COLORS`, `_PRECIP_MM_COLORS`, `_PRECIP_PCT_COLORS`) und/oder eine Mindest-Opacity oberhalb eines kleinen Schwellwerts anpassen, sodass „ein bisschen Wetter" sichtbar wird, ohne bei echten Nullwerten Fehlsignale zu erzeugen. Ggf. zusätzlich prüfen, ob eine geringere Overlay-Transparenz am Kartenrand/generell sinnvoll ist.
- Betroffene Dateien: `web/index.html` (Farbpaletten + `_render`/`_colorInterp`).
- Vorteile: Behebt das eigentliche Wahrnehmungsproblem direkt an der Ursache; keine Backend-Änderung nötig, da die Rohdaten bereits korrekt sind.
- Nachteile/Risiken: Erfordert eine bewusste Designentscheidung (Bauhaus-Farbcheck via `fotoalert-designer`), sonst Gefahr einer irreführenden Übersättigung bei Klarwetter (siehe Pre-Mortem). Etwas Justieraufwand (Testen an mehreren Wetterlagen).
- Aufwand: mittel.

Option C — Beim Einschalten automatisch weiter herauszoomen, wenn am 50-km-Ausschnitt kaum Wetteraktivität vorliegt:
- App-Wirkung: Ist am aktuellen Standort kaum Bewölkung/Niederschlag vorhergesagt, würde die Karte selbstständig einen größeren Bereich zeigen, in dem eher Wetteraktivität sichtbar ist.
- Vorgehen: Serverseitige Datenwerte im gezoomten Bereich müssten clientseitig ausgewertet werden, um zu entscheiden, ob „genug" Wetter da ist; bei Bedarf automatischer Re-Zoom.
- Vorteile: Würde in jedem Fall etwas Sichtbares zeigen.
- Nachteile/Risiken: Widerspricht direkt der gerade erst freigegebenen BUG-58-Anforderung (stabiler, vorhersehbarer 50-km-Ausschnitt, kein automatisches Zurückspringen/Verändern der Kartenmitte). Deutlich höherer Aufwand, neue Fehlerquelle (Pre-Mortem: „springt unerwartet"). Löst kein echtes Problem, sondern verschiebt es nur räumlich.
- Aufwand: groß.

✅ **Empfehlung: Option B.** Sie behebt die plausibelste Ursache (Wahrnehmungsproblem durch Kombination aus BUG-58-Zoomverkleinerung und ohnehin heller Farbskala) direkt an der Wurzel, ohne die gerade erst freigegebene Zoom-Logik aus BUG-58 wieder zu verändern (Option C) und ohne das Problem nur zu beschreiben statt zu lösen (Option A). Vor der finalen Farb-/Opacity-Entscheidung wird `fotoalert-designer` für den Bauhaus-Check hinzugezogen. Die Empfehlung steht unter dem Vorbehalt, dass ein echter Live-Test (bekannt bewölkter/regnerischer Zielort) die Root-Cause-Einschätzung bestätigt — sollte der Live-Test stattdessen einen technischen Datenfehler zeigen (z. B. wirklich leeres Bild trotz vorhandener Werte), wäre stattdessen eine Backend-Korrektur nötig.

**Entscheidung (2026-07-04, Stephan):** Option B wird umgesetzt.

**Re-Analyse-Anlass (2026-07-04):** Beim Implementierungsstart hat sich herausgestellt, dass die Analyse-Annahme zu Option B an einer Stelle nicht zutrifft: Die im Frontend änderbaren Farbwerte (`_CLOUD_COLORS` etc.) steuern nur die kleine Legende, nicht die eigentliche eingefärbte Wetterfläche auf der Karte — diese Fläche ist ein fertiges Bild, das vollständig vom Server geliefert wird. Stephans Entscheidung: Ticket zurück in die Analyse, Scope wird um die serverseitige Bild-/Farberzeugung erweitert (Zoom-Logik aus BUG-58 und Datenqualität aus US-112 bleiben weiterhin ausgeschlossen). Die reine Legenden-Anpassung wurde ausdrücklich verworfen ("die kleine Legende ist nicht das Problem").

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt (Code-Verifikation dokumentiert)
- [x] Architektur analysiert: `web/index.html` (`WeatherMap`, Zeile 4456–4783), `backend/main.py` (Zeile 1895–1970), `backend/calculations/weather_grib.py` (Zeile 73–81, 553–641)
- [x] Designer-Check: visuell relevant (Farbintensität/Opacity) → `fotoalert-designer` vor finaler Farbentscheidung in der Implementierungsphase hinzuzuziehen
- [x] Implementierungsoptionen: A / B / C
- [x] Empfehlung: Option B

**Grenzen dieser Analyse:**
- Kein echter Browser-/DevTools-Zugriff verfügbar — die Root-Cause-Einschätzung (Wahrnehmungsproblem vs. technischer Fehler) beruht auf Code-Lektüre, nicht auf einer beobachteten Live-Karte. Muss per Live-Test an einem Ort mit bekannt aktivem Wetter bestätigt werden.
- Kein Zugriff auf Git-Historie (Commit-Log) in dieser Analyse-Phase — falls die Root-Cause-Klärung einen Vergleich zum Verhalten vor BUG-58 braucht, müsste das separat per Terminal-Befehl auf Stephans Mac geprüft werden.
- Ob zusätzlich zum Prozess-Speicher-Cache ein Disk-Cache für die Wetterkarten-PNGs existiert, ließ sich aus dem gelesenen Code nicht abschließend feststellen.

**Testplan:**
- [ ] Automatisiert (Harness): Kein neuer pytest-Fall vorgesehen, da die Ursache rein clientseitige Darstellung (Farbskala/Opacity in `web/index.html`) betrifft, analog zu BUG-55/BUG-58. Bestehender Endpoint-Test (`test_weather_map_endpoint_schema`) deckt weiterhin ab, dass Bounds/Frames korrekt geliefert werden.
- [ ] Manuell (unter http://localhost:8000):
  1. Karten-Tab öffnen, auf einen Standort zoomen, an dem laut aktueller Vorhersage nennenswerte Bewölkung oder Niederschlag erwartet wird; „Wolken" bzw. „Niederschlag" antippen — erwartet: deutlich sichtbare, farbige Fläche im 50-km-Ausschnitt.
  2. Zeitregler bewegen — erwartet: Fläche verändert sich sichtbar mit dem gewählten Zeitpunkt.
  3. Zum Vergleich einen Standort/Zeitpunkt mit praktisch klarem Himmel wählen — erwartet: Fläche bleibt bewusst sehr hell/kaum sichtbar (kein Fehlzustand, siehe AK-3).
  4. Falls möglich: Server frisch neu starten und sofort „Wolken" antippen, bevor der Wetterkarten-Cache aufgebaut ist — erwartet: Hinweistext „Wetterdaten werden geladen …" statt stiller Leerfläche.

---

## Re-Analyse (2026-07-04) — Backend im Scope

**Anlass:** Die erste Analyse ging fälschlich davon aus, dass die Frontend-Konstanten `_CLOUD_COLORS`/`_PRECIP_MM_COLORS`/`_PRECIP_PCT_COLORS` in `web/index.html` die sichtbare Wetterfläche einfärben. Ein Implementierungs-Subagent hat verifiziert: Diese Frontend-Werte steuern ausschließlich die kleine Legende. Die eigentliche eingefärbte Fläche ist ein fertiges PNG-Bild, das der Server komplett vorberechnet und liefert (`L.imageOverlay`). Stephan hat den Scope explizit um die serverseitige Bild-/Farberzeugung erweitert und eine reine Legenden-Lösung ausdrücklich ausgeschlossen ("die kleine Legende ist nicht das Problem").

**Code-Befund (verifiziert per Grep/Read am aktuellen Stand, 2026-07-04):**

- `backend/calculations/weather_grib.py` Zeile 73–81: feste BBox-Konstanten (`BBOX_S/N/W/E`, unverändert `43.0/71.5/3.0/21.0`) und PNG-Maße (`PNG_W=360`, `PNG_H=420`) — Zeilenangabe aus Analyse 1 bestätigt.
- Zeile 101–114: Die tatsächlichen Server-Farbstopps `_CLOUD_STOPS` (5 Stufen, 0→`rgb(200,232,255)` bis 100→`rgb(56,72,88)`) und `_PRECIP_STOPS` (0→`rgb(234,244,255)` bis 10mm→`rgb(10,45,107)`) — das sind die Werte, die tatsächlich das PNG einfärben, nicht die gleichnamigen Frontend-Konstanten. Kommentar in Zeile 100 sagt selbst „spiegeln das Frontend" — die Duplizierung ist Teil des Problems (zwei Farbskalen an zwei Stellen, die auseinanderlaufen können).
- Zeile 481–496: `_color_for()` — reine Interpolationshilfsfunktion (aktuell laut Code nicht mehr im aktiven Pfad von `field_to_png` verwendet, dort wird stattdessen direkt `np.interp` über die Stop-Arrays genutzt, Zeile 523–529).
- Zeile 499–546: `field_to_png(arr, field, alpha: int = 150)` — das ist die zentrale Stelle, die Werte in RGBA-Pixel übersetzt. Kernbefund:
  - Standard-Deckkraft ist **fix `alpha=150`** (von 255) für jedes gültige (nicht-NaN) Pixel, unabhängig vom Wert — d.h. selbst bei starkem Wetter ist das Overlay nie voll deckend.
  - Zeile 534–536: Für Niederschlag wird zusätzlich jedes Pixel mit Wert `< 0.05mm` komplett transparent (`alpha=0`) gesetzt — Absicht laut Kommentar: „damit die Karte nicht flächig blau überzogen wird".
  - Für „cloud" gibt es keine entsprechende Trockenheits-/Null-Schwelle; niedrige Werte werden einfach mit der hellsten Stop-Farbe (`(200,232,255)`, sehr helles Pastellblau) bei `alpha=150` gerendert — das ist in Kombination mit dem hellen Karten-Tile-Hintergrund praktisch die Ursache der schlechten Sichtbarkeit bei „wenig, aber vorhandenem" Wetter.
- Zeile 553–555: `overlay_bounds()` liefert unverändert die feste Mehrländer-BBox — Zeilenangabe aus Analyse 1 bestätigt, keine Änderung seither.
- Zeile 628–640: `render_all_pngs(overlay, field)` ruft pro Stunde `field_to_png(arr, field)` **ohne expliziten `alpha`-Parameter** auf — nutzt also durchgehend den Default `alpha=150`. Aufgerufen aus `backend/main.py` Zeile 733–734 (`_build_weather_map()`), Ergebnis landet im Prozessspeicher-Dict `_weather_map_png` (kein Disk-Cache identifizierbar, wie schon in Analyse 1 vermerkt).
- `web/index.html` Zeile 4565–4587 (`_render()`): bestätigt unverändert — `L.imageOverlay(full, bounds, {opacity: 1, pane: 'weatherPane', interactive: false})`. Die `opacity: 1` ist fix im Frontend-Code; die eigentliche Transparenzsteuerung passiert ausschließlich serverseitig im PNG-Alphakanal (`field_to_png`). Das Frontend hat aktuell keinerlei Hebel, um das Overlay kräftiger/blasser zu machen, außer die URL/das Bild selbst zu ändern.

**Kurz gesagt (App-Verhalten):** Der Server malt das Wetterbild bereits von vornherein mit reduzierter, fixer Deckkraft (etwa 60% von voll deckend) und lässt bei Wolken auch schwache Werte in sehr hellem Blau erscheinen. Die Karten-App selbst kann daran nichts mehr drehen — sie zeigt nur das fertige Bild an. Genau das erklärt, warum selbst dort, wo laut Vorhersage etwas Wolken oder Regen sind, auf der Karte kaum etwas zu erkennen ist.

**Überarbeitete Implementierungsoptionen (serverseitig):**

Option D — Mindest-Deckkraft + kräftigere Farbskala direkt im Server-Rendering:
- App-Wirkung: Sobald am gezoomten Ort spürbare Bewölkung oder Niederschlag vorhergesagt ist, erscheint die Fläche auf der Karte klar erkennbar eingefärbt — auch bei mittleren Werten, nicht erst bei Extremwetter. Echtes Klarwetter/echte Nullwerte bleiben weiterhin nahezu unsichtbar (kein Fehlsignal).
- Vorgehen: In `field_to_png()` (`backend/calculations/weather_grib.py`) die feste `alpha=150` durch eine wertabhängige Mindest-Deckkraft ersetzen (z. B. Pixel mit spürbarem Wert erhalten alpha 200–230 statt 150), und/oder die hellsten Farbstopps in `_CLOUD_STOPS`/`_PRECIP_STOPS` kräftiger wählen, während der Nullpunkt (0% Wolken, <0,05mm Niederschlag) weiterhin transparent/sehr hell bleibt. Die bestehende Trockenheits-Transparenz-Regel bei Niederschlag (Zeile 534–536) bliebe als Vorbild für eine analoge, sanfte Wolken-Schwelle erhalten.
- Betroffene Dateien: nur `backend/calculations/weather_grib.py` (Funktion `field_to_png`, Konstanten `_CLOUD_STOPS`/`_PRECIP_STOPS`). Kein Frontend-Eingriff nötig, da die Bilder ohnehin serverseitig neu erzeugt werden.
- Vorteile: Trifft die Ursache exakt an der Stelle, die tatsächlich das sichtbare Bild erzeugt; Frontend bleibt unangetastet; nutzt bereits vorhandene Muster (Trockenheits-Schwelle) statt neuer Mechanik.
- Nachteile/Risiken: Erfordert eine bewusste Farb-/Kontrastentscheidung (Bauhaus-Check), sonst Gefahr von Übersättigung bei hohen Werten oder einem irreführenden Signal bei sehr niedrigen, aber ungleich Null-Werten. Bestehende gecachte PNGs im Prozessspeicher (`_weather_map_png`) spiegeln nach der Änderung weiterhin die alte Farbgebung, bis der nächste reguläre Rebuild (alle 3h laut Scheduler) oder ein Serverneustart die Bilder neu erzeugt — ohne manuellen Trigger bliebe es bis zu 3h lang uneinheitlich.
- Aufwand: mittel (Farbkonstanten + eine Formel in einer Funktion; kein neuer Endpoint, keine neue Datenstruktur).

Option E — Non-linearer Alpha-Verlauf mit fixem Mindestwert oberhalb eines kleinen Schwellwerts (statt linearer Farbinterpolation):
- App-Wirkung: Wie Option D im Ergebnis für Stephan (Fläche wird bei realem Wetter klar sichtbar), aber die Umsetzung ist gezielter: Nicht die ganze Farbskala wird kräftiger, sondern nur die Transparenz bekommt eine steilere Kurve — z. B. „Sprung" auf eine deutliche Mindest-Deckkraft (z. B. alpha 190) sobald ein Schwellwert (z. B. 10% Bewölkung bzw. 0,3mm Niederschlag) überschritten ist, mit sanftem Anstieg danach bis zum Maximum bei hohen Werten.
- Vorgehen: In `field_to_png()` eine zusätzliche, vom aktuellen linearen `alpha`-Wert unabhängige Berechnung einbauen (z. B. `alpha = base_alpha + (max_alpha-base_alpha) * min(1, value/schwelle)^0.5` oder ähnliche Kurve), die Farbstopps selbst unverändert lassen.
- Betroffene Dateien: nur `backend/calculations/weather_grib.py`, isolierter in `field_to_png` als Option D (Farbstopps bleiben unangetastet, nur die Alpha-Berechnung wird ersetzt).
- Vorteile: Trennt sauber „Farbe" (bleibt wie gehabt, ggf. sogar unverändert im Vergleich zu heute) von „Sichtbarkeit" (wird gezielt für den Wahrnehmungsbereich angehoben); geringeres Risiko einer optischen Farbverfälschung, da nur die Deckkraft-Kurve verändert wird; leichter feinjustierbar (ein Schwellwert + eine Kurve statt fünf Farbstopps).
- Nachteile/Risiken: Etwas komplexere Formel als eine einzelne Konstante; Schwellwert muss pro Feldtyp (cloud/precip) sinnvoll gewählt werden, sonst wirkt der Sprung an der Schwelle unnatürlich sichtbar („Kante" statt weicher Übergang). Gleiches Cache-Invalidierungs-Thema wie Option D.
- Aufwand: mittel (etwas mehr Denkarbeit für eine gute Kurve, aber ähnlich lokal begrenzter Eingriff wie Option D).

Beide Optionen D und E ließen sich auch kombinieren (kräftigere Farbstopps UND leicht angehobene Mindest-Deckkraft), falls der Bauhaus-Check in der Umsetzung zeigt, dass eine Maßnahme allein nicht ausreicht.

**Empfehlung:** Option E (non-linearer Alpha-Verlauf mit Mindestwert oberhalb eines kleinen Schwellwerts), optional ergänzt um eine moderate Anhebung der hellsten Farbstopps aus Option D, falls der Bauhaus-Check das für nötig hält. Begründung: Option E löst das eigentliche Wahrnehmungsproblem (schwaches, aber vorhandenes Wetter ist auf der Karte kaum sichtbar) gezielt an der Stelle, die es verursacht — der Deckkraft-Berechnung —, ohne die Farbskala selbst großflächig zu verändern und damit das Risiko einer Farb-Verfälschung bei Klarwetter oder Übersättigung bei Starkwetter zu minimieren. Sie bleibt vollständig im bestehenden Scope (nur `weather_grib.py`), rührt weder die BUG-58-Zoom-Logik noch die US-112-Datenbeschaffung an, und ist als lokal begrenzte Änderung an einer einzelnen Funktion mit überschaubarem Aufwand umsetzbar. Vor der finalen Farb-/Schwellwert-Entscheidung wird in der Implementierungsphase `fotoalert-designer` (Bauhaus-Designwächter) hinzugezogen, um Farbintensität und Kontrast bewusst statt zufällig zu wählen.

**Pre-Mortem-Update (spezifisch für die Server-Änderung):**
- 💀 Szenario: Die PNGs liegen ausschließlich im Prozessspeicher (`_weather_map_png` in `backend/main.py`, kein Disk-Cache im Code identifizierbar). Nach einer Code-Änderung an `field_to_png`/den Farbstopps zeigen bereits laufende Server-Instanzen weiterhin die alten, alten Bilder, bis entweder der nächste geplante Rebuild (laut Scheduler alle 3h) läuft oder der Prozess neu gestartet wird. → Gegenmaßnahme: Im Testplan/Release-Schritt explizit einen Server-Neustart (oder Warten auf den nächsten Scheduler-Lauf) nach dem Deploy vorsehen, sonst wirkt der Fix „nicht angekommen".
- 💀 Szenario: Eine zu aggressive Mindest-Deckkraft oder zu kräftige Farbstopps führen bei tatsächlich hohem Wolken-/Niederschlagswert zu einer übersättigten, das Kartenbild dominierenden Fläche (Regression: die Karte wird bei Starkwetter schwer lesbar, Marker/POIs schwer erkennbar). → Gegenmaßnahme: Testplan um einen expliziten Vergleich „hoher Wert vorher/nachher" ergänzen, nicht nur den Niedrigwert-Fall aus Analyse 1.
- 💀 Szenario: PNG-Neu-Encoding ist CPU-Arbeit (`asyncio.to_thread` in `_build_weather_map()`, `backend/main.py` Zeile 733–734) für 72 Stunden × 2 Felder × 360×420 Pixel. Eine reine Alpha-/Farbwert-Änderung in `field_to_png` selbst ändert an der Rechenkomplexität nichts (gleiche Bildgröße, gleiche Pixelanzahl) — kein zu erwartender Performance-Regressionsfall, aber zur Sicherheit im Testplan als „Job-Laufzeit vorher/nachher vergleichen" aufnehmen, falls die neue Alpha-Formel aufwendiger ist als die bisherige lineare Interpolation.
- 💀 Szenario: Da `_CLOUD_STOPS`/`_PRECIP_STOPS` in `weather_grib.py` laut Code-Kommentar (Zeile 100) bewusst die Frontend-Farbwerte „spiegeln" sollen, könnte eine reine Server-Änderung die Legende (Frontend) und die tatsächliche Kartenfläche (Server) wieder auseinanderlaufen lassen, wenn nur eine Seite angepasst wird. → Gegenmaßnahme: In der Umsetzung explizit klären/entscheiden, ob die Legenden-Frontend-Werte zur Konsistenz nachgezogen werden sollen (nicht als Lösung des eigentlichen Problems, sondern als Konsistenz-Folgeschritt) — das ist eine bewusste Detailentscheidung für die Implementierungsphase, kein neuer Scope.
- Designer-Hinweis: `fotoalert-designer` wird vor der finalen Farb-/Schwellwert-Entscheidung in der Implementierungsphase hinzugezogen (nur vorgemerkt, hier nicht durchgeführt).

**Grenzen dieser Re-Analyse:**
- Wie in Analyse 1: kein echter Browser-/Live-Test möglich; die Einschätzung „alpha=150 + helle Cloud-Stopps erklären die schlechte Sichtbarkeit" ist eine belastbare Code-Lektüre-Einschätzung, aber noch nicht am echten Bild verifiziert.
- Konkrete Zahlenwerte für Schwellwert/Ziel-Alpha in Option E sind hier als Beispielwerte genannt, nicht als finale Vorgabe — die endgültige Wahl gehört in die Implementierungsphase inkl. Designer-Check.

**Entscheidung (2026-07-04, Stephan):** Option E wird umgesetzt.

---

## Implementierung (2026-07-04)

**Geänderte Datei:** `backend/calculations/weather_grib.py`, Funktion `field_to_png()` (verifiziert per Grep/Read am aktuellen Stand: Funktion beginnt Zeile 546, nicht mehr 499 — Zeilen haben sich durch die neue `_alpha_curve()`-Hilfsfunktion + Konstantenblock direkt davor verschoben; funktional identische Stelle wie in beiden Analysen beschrieben). Keine Änderung an `web/index.html`, an der Zoom-Logik (BUG-58) oder an der Wetterdatenbeschaffung (US-112).

**Was sich ändert:** Der feste Deckkraft-Wert `alpha=150` (Parameter von `field_to_png`) wurde durch eine neue Funktion `_alpha_curve()` ersetzt, die pro Pixel eine wertabhängige, non-lineare Deckkraft berechnet — getrennt für Wolken (`cloud`) und Niederschlag (`precip`). Die Farbstopps selbst (`_CLOUD_STOPS`, `_PRECIP_STOPS`) bleiben unverändert, wie von Option E vorgesehen — nur die Transparenzsteuerung ändert sich. Der `alpha`-Parameter der Funktionssignatur wurde entfernt, da er nirgends mit einem expliziten Wert aufgerufen wurde (verifiziert per Grep: einziger Aufrufer `render_all_pngs()` sowie ein Testaufruf, beide ohne `alpha`-Argument).

**Gewählte Schwellwerte/Alpha-Ziele (nach Designer-Check `fotoalert-designer`, Bauhaus-Prinzip „Farbe/Deckkraft als Signal, nicht Dekoration" + „ruhiger Verlauf statt harter Kante"):**

| Feld | Unterhalb Schwellwert | Schwellwert („spürbares Wetter") | Deckkraft an Schwelle | Kurve bis Maximalwert | Maximal-Deckkraft |
|---|---|---|---|---|---|
| Wolken (`cloud`) | alpha 60 (0–15 %) | 15 % Bewölkung | alpha 190 (Sprung) | Wurzel-Anstieg bis 100 % | alpha 235 |
| Niederschlag (`precip`) | alpha 0 unter 0,05 mm (unverändert), alpha 170 zwischen 0,05–0,3 mm | 0,3 mm/h | alpha 170 (kein zusätzlicher Sprung, da bereits sichtbar) | Wurzel-Anstieg bis 10 mm | alpha 235 |

Begründung: Unterhalb des Schwellwerts bleibt die Fläche bewusst kaum sichtbar (kein Fehlsignal bei echtem Klarwetter/Nieselgrenze — erfüllt AK „bleibt bewusst sehr hell/kaum sichtbar" aus Analyse 1). Direkt am Schwellwert springt die Deckkraft deutlich wahrnehmbar nach oben (erfüllt AK „deutlich wahrnehmbare, eingefärbte Fläche" für real vorhandenes, aber leichtes Wetter). Der weitere Anstieg bis zum Maximalwert folgt einer Wurzel-Kurve (Exponent 0,5) statt eines linearen oder harten Sprungs — das vermeidet eine sichtbare „Kante" am Schwellwert und verhindert gleichzeitig Übersättigung bei Starkwetter, da die Deckkraft bewusst nie 255 (voll deckend) erreicht, sondern bei 235 plateaut (Karte bleibt darunter leicht sichtbar, analog zur bestehenden Bauhaus-Regel „Karte als Hintergrund, nicht Showpiece"). Die bestehende Trockenheits-Transparenz-Regel für Niederschlag (<0,05 mm → alpha 0) bleibt unverändert erhalten.

**Bezug zu den Akzeptanzkriterien (aus „## Analyse (2026-07-04)"):**
- AK 1 (deutlich wahrnehmbare Fläche bei realem Wetter): erfüllt durch den Alpha-Sprung auf 190/170 an der jeweiligen Schwelle.
- AK 2 (Fläche verändert sich sichtbar mit dem Zeitregler): unverändert gegeben, da pro Stunde weiterhin ein eigenes PNG mit den tatsächlichen Werten dieser Stunde erzeugt wird — die neue Kurve wirkt pro Pixel/Stunde identisch.
- AK 3 (bei praktisch keinem Wetter bleibt Fläche bewusst kaum sichtbar): erfüllt durch die niedrige Basis-Deckkraft unterhalb des jeweiligen Schwellwerts (60 bzw. 0/170 vor der Precip-Schwelle).
- AK 4 (Hinweistext bei leerem Cache statt stiller Leerfläche): nicht Teil dieser Code-Änderung — betrifft Frontend-Ladezustand, nicht die Alpha-Berechnung; unverändert, kein Regressionsrisiko durch diese Änderung.
- AK 5 (Legende bleibt korrekt passend sichtbar): keine Änderung an Legenden-Farbwerten nötig, da Option E bewusst nur die Deckkraft und nicht die Farbstopps ändert — Legende und PNG nutzen weiterhin dieselben Farbwerte, kein Auseinanderlaufen.

**Tests:** Bestehender Test `backend/tests/test_us112_weather_map.py` (`test_interpolate_and_png`, Aufruf `wg.field_to_png(arr, "cloud")`) bleibt unverändert lauffähig, da kein Aufrufer einen expliziten `alpha`-Wert übergeben hat. Ergänzt wurden 6 neue, gezielte Tests für die neue Alpha-Kurve: `test_cloud_alpha_below_threshold_stays_faint`, `test_cloud_alpha_jumps_at_threshold`, `test_cloud_alpha_high_value_near_max_not_oversaturated`, `test_precip_dry_limit_still_fully_transparent`, `test_precip_alpha_jumps_above_dry_limit`, `test_precip_alpha_high_value_near_max_not_oversaturated` — sie lesen den tatsächlichen Alpha-Kanal aus dem erzeugten PNG (via Pillow) und prüfen Basis-, Sprung- und Maximalwert pro Feld. In der Sandbox konnte kein volles `pytest` laufen (kein `eccodes`/`pytest` im Sandbox-Python installiert), die Kernlogik (`_alpha_curve` + `field_to_png`-Alpha-Ausgabe) wurde stattdessen per eigenständigem Python-Skript mit echtem numpy/Pillow gegen die erwarteten Werte verifiziert (Ergebnis deckt sich exakt mit der Tabelle oben: cloud 0%→60, 2%→60, 15%→190, 50%→218, 100%→235; precip 0,01mm→0, 0,1mm→170, 0,3mm→170, 2mm→197, 10mm→235). Empfehlung: Vollen `pytest`-Lauf inkl. eccodes-Tests auf Stephans Mac-Venv oder in CI bestätigen.

**Wichtiger Hinweis für die Testphase:** Die Wetterkarten-PNGs liegen ausschließlich im Arbeitsspeicher des Server-Prozesses (`_weather_map_png`-Dict in `backend/main.py`). Nach dem Deploy dieser Änderung zeigen bereits laufende Server-Instanzen weiterhin die alten Bilder, bis entweder der nächste geplante Rebuild (laut Scheduler alle 3h) läuft oder der Prozess neu gestartet wird. Für den Test sollte daher entweder auf den nächsten Scheduler-Lauf gewartet oder der Server-Prozess neu gestartet werden — sonst wirkt der Fix fälschlich als „nicht angekommen".

## Testergebnis (2026-07-04, lokal von Stephan bestätigt)

- Lokale Testumgebung: `eccodes` + `Pillow` fehlten zunächst im lokalen venv (App startete zuvor mit Wetter-Overlay/PNG-Rendering deaktiviert) — nachinstalliert (`pip install eccodes Pillow`), danach Server neu gestartet. Wetterkarte erfolgreich aufgebaut (icon_d2: 92, icon_eu: 44, met: 16 Stützpunkte).
- AK1 (deutlich sichtbare Fläche bei realem Wetter): ✅ bestätigt.
- AK2 (Fläche ändert sich mit Zeitregler): ✅ bestätigt.
- AK3 (bei Klarwetter bleibt Fläche bewusst kaum sichtbar): ✅ bestätigt.
- AK4 (Hinweistext bei leerem Server-Cache): ⏳ nicht getestet — Zeitfenster (kurz nach Serverstart, vor Cache-Aufbau) war zum Testzeitpunkt bereits verstrichen. Bewusst offene Lücke, kein Fehlzustand unterstellt.
- AK5 (Legende bleibt passend sichtbar): ✅ bestätigt.
- Regressionscheck (andere 4 Tabs): ✅ bestätigt, keine Auffälligkeiten.

---

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

---

### US-125 · Host kann Beispielbild einer Location löschen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-05 |
| **Abgeschlossen** | 2026-07-05 |

**Beschreibung:** Als Host möchte ich in der Location-Detailansicht ein bereits hochgeladenes Beispielbild eigenständig löschen können, ohne dafür gleich die ganze Location löschen oder zwingend ein Ersatzbild hochladen zu müssen.

**User Story:** Als Host, möchte ich in der Location-Detailansicht ein hochgeladenes Beispielbild löschen können, sodass ich ein falsches, veraltetes oder nicht mehr passendes Bild entfernen kann, ohne die komplette Location löschen oder sofort ein neues Bild bereithalten zu müssen.

**Bezug:** Direkt verwandt mit **US-120** [x] (Done, 2026-07-04, Beispielbild-Upload) — dort deckt AK „Ein normaler Nutzer sieht in keiner Ansicht eine Möglichkeit, ein Beispielbild hochzuladen, zu ersetzen oder zu löschen" nur die Host-Berechtigung ab, nicht ob ein eigenständiger Löschen-Button (ohne Ersetzen) für den Host existiert. Ebenfalls in US-120 dokumentiert: Löschen einer ganzen Location entfernt automatisch auch deren Bilddatei (AK „Löscht der Host eine Location …") — das ist eine Kaskade beim Location-Löschen, kein eigenständiges Bild-Löschen-Feature. Keine Dublette gefunden. Berührt dieselbe UI-Fläche (Location-Detail/Bearbeiten-Formular) wie **US-126** (Bildausschnitt-Auswahl, neu), beide unabhängig voneinander umsetzbar.

---

#### Analyse (2026-07-05)

**Example Mapping**

📏 **Rule 1 — Pro Location gibt es genau ein Beispielbild.** Es gibt (verifiziert im Code) keine Liste von mehreren Bildern pro Location, sondern immer nur ein einziges. „Löschen" bedeutet deshalb immer: das eine vorhandene Bild entfernen — danach zeigt die Location wieder den bekannten gestrichelten Platzhalter „Noch kein Beispielbild" mit Upload-Button, den es schon seit dem Bild-Upload-Feature gibt.
- 🟢 Beispiel: Ein Host öffnet eine Location mit Beispielbild, tippt auf „Löschen" und bestätigt. Danach zeigt die Location denselben leeren Platzhalter, den sie vor dem allerersten Hochladen hatte.

📏 **Rule 2 — Löschen fragt vorher sicherheitshalber nach.** Da ein gelöschtes Bild nicht wiederhergestellt werden kann, erscheint vor dem endgültigen Löschen eine kurze Sicherheitsabfrage (genau wie es die App bereits beim Löschen einer ganzen Location tut).
- 🟢 Beispiel: Der Host tippt auf „Löschen", die App fragt „Beispielbild wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden." — erst nach Bestätigen ist das Bild weg. Tippt der Host stattdessen auf „Abbrechen", bleibt alles wie es war.

📏 **Rule 3 — Das Bild wird wirklich entfernt, nicht nur versteckt.** Die Bilddatei wird von der Festplatte des Servers entfernt (genau wie es beim Ersetzen eines Bildes oder beim Löschen einer ganzen Location bereits passiert) — es bleiben keine verwaisten Altbilder liegen.
- 🟢 Beispiel: Nach dem Löschen ist das Bild auch dann nicht mehr abrufbar, wenn jemand versucht, die alte Bild-Adresse direkt erneut aufzurufen.

📏 **Rule 4 — Nur die Host-Rolle sieht den Löschen-Button.** Ein normaler Nutzer sieht in der Location-Ansicht weder einen Löschen- noch einen Ersetzen-Button — das Bild ist für ihn nur zum Ansehen da (bereits bestehendes Verhalten aus dem Bild-Upload-Feature, ändert sich hier nicht).
- 🟢 Beispiel: Ein normaler Nutzer öffnet dieselbe Location — er sieht nur das Bild selbst, keinerlei Bearbeiten- oder Löschen-Möglichkeit.

**Keine offenen 🔴-Fragen** — alle im Auftrag genannten Unklarheiten ließen sich beim Code-Lesen eindeutig klären bzw. mit einem unstrittigen, zum bestehenden Muster passenden Standardverhalten beantworten:

- *„Wer darf löschen — nur der hochladende Host oder jeder Host?"* → Es gibt in der App nur **eine** Host-Rolle (ein gemeinsames Passwort für alle Hosts, keine einzelnen Host-Konten). Die Frage „welcher Host hat es hochgeladen" stellt sich technisch nicht — jeder eingeloggte Host darf es also löschen, genau wie jeder Host auch ersetzen oder die ganze Location löschen darf.
- *„Was passiert beim letzten Bild — auf 0 runter erlaubt?"* → Ja, ausdrücklich erlaubt und genau der Sinn des Tickets („ohne zwingend ein Ersatzbild hochladen zu müssen").
- ⚠️ Annahme: Vor dem Löschen erscheint eine Sicherheitsabfrage (wie beim Location-Löschen) — bitte bestätigen.
- ⚠️ Annahme: Das Bild wird endgültig von der Festplatte entfernt, nicht nur ausgeblendet (konsistent zum bestehenden Verhalten beim Ersetzen/Location-Löschen) — bitte bestätigen.
- *„Einzeln löschbar bei mehreren Bildern?"* → Entfällt, da es technisch nur ein Bild pro Location gibt.

**Akzeptanzkriterien:**
- [x] Ein Host sieht in der Location-Ansicht neben dem vorhandenen Beispielbild einen eigenen Löschen-Button (getrennt vom bestehenden „Ersetzen"-Button).
- [x] Tippt der Host auf „Löschen", erscheint zuerst eine Sicherheitsabfrage mit Hinweis, dass die Aktion nicht rückgängig gemacht werden kann.
- [x] Bestätigt der Host die Abfrage, verschwindet das Bild sofort aus der Ansicht und die Location zeigt wieder den leeren Platzhalter „Noch kein Beispielbild" mit Upload-Möglichkeit.
- [x] Bricht der Host die Sicherheitsabfrage ab, bleibt das Bild unverändert sichtbar.
- [x] Nach dem Löschen ist das Bild auch über die alte Bild-Adresse nicht mehr abrufbar (Datei ist wirklich weg, nicht nur ausgeblendet).
- [x] Ein normaler Nutzer (kein Host) sieht in derselben Ansicht keinerlei Löschen-Möglichkeit — auch nicht über die Serverschnittstelle direkt (Zugriff wird abgelehnt).
- [x] Edge Case: Der Host versucht eine Location zu löschen, die aktuell gar kein Beispielbild hat (z. B. per direktem Server-Aufruf ohne Umweg über den Button) — die App lehnt das mit einer verständlichen Fehlermeldung ab, es passiert nichts Unerwartetes.
- [x] Edge Case: Der Host löscht das Bild einer Location, die es gar nicht gibt (z. B. bereits gelöschte Location) — die App lehnt das mit einer verständlichen Fehlermeldung ab („Location nicht gefunden").

**Pre-Mortem:**

📎 Code-Verifikation: `backend/main.py` (Zeilen 2184–2439) und `web/index.html` (Zeilen 5368–5420, 373–392) gelesen am 2026-07-05.
- Bestätigt: Pro Location existiert genau ein `image_filename`-Feld (kein Array) — Fundstelle `backend/main.py:2287` (`old_filename = getattr(target_loc, "image_filename", None)`).
- Bestätigt: Es existiert bereits eine funktionierende Lösch-Hilfsfunktion `_delete_location_image_file()` (Zeile 2241–2251), die genau das tut was dieses Ticket braucht — sie wird aktuell nur beim Ersetzen und beim kompletten Location-Löschen aufgerufen, noch nicht eigenständig über einen eigenen Endpunkt.
- Bestätigt: Es gibt noch **keinen** eigenständigen „Bild löschen"-Endpunkt — nur Upload (`POST /locations/{loc_id}/image`) und die Kaskade beim Location-Löschen. Dieses Ticket muss also einen neuen Endpunkt ergänzen, keinen bestehenden „Lösch-Modus" umschalten.
- Bestätigt: Es gibt nur eine globale Host-Rolle (`backend/auth.py`, `require_host`), keine Unterscheidung zwischen verschiedenen Hosts — die Rechte-Frage aus dem Auftrag ist damit eindeutig beantwortet (siehe Example Mapping oben).
- Bestätigt: Ein Bestätigungsdialog-Muster existiert bereits im Frontend fürs Location-Löschen (`web/index.html:5752`, `confirm(...)`) — direkt wiederverwendbar, kein neues Dialog-Konzept nötig.

💀 Szenario: Der Löschen-Button und der bestehende „Ersetzen"-Button liegen so dicht beieinander, dass ein Host aus Versehen das Bild löscht statt es zu ersetzen.
   Auslöser: Beide Buttons sitzen in derselben kleinen Fläche oben rechts über dem Bild.
   Frühwarnung: Beim ersten Testen in echter Bildschirmgröße auf dem Handy.
   Gegenmaßnahme: Bauhaus-Designcheck durchgeführt (siehe unten) — getrennte Buttons mit ausreichend Abstand + Sicherheitsabfrage als zusätzliches Sicherheitsnetz gegen Fehlklicks. In AK 2/3 verankert.

💀 Szenario: Der neue Lösch-Endpunkt vergisst, die Datei auf der Festplatte tatsächlich zu entfernen, und es sammeln sich unsichtbare Karteileichen an.
   Auslöser: Verweis in der Location wird gelöscht, aber der eigentliche Datei-Löschvorgang wird vergessen (gleicher Fehlertyp wie ursprünglich in US-120 als „Pre-Mortem 2" beschrieben und dort bereits gelöst).
   Frühwarnung: Speicherplatz auf dem Server wächst unbemerkt über Zeit.
   Gegenmaßnahme: Die bereits vorhandene, bewährte Funktion `_delete_location_image_file()` wiederverwenden statt eine neue Lösch-Logik zu schreiben. In AK 5 + Testplan verankert.

💀 Szenario: Ein normaler Nutzer findet über die Browser-Konsole heraus, dass er den Server direkt anweisen kann, ein Bild zu löschen — ganz ohne Host-Login.
   Auslöser: Der neue Endpunkt vergisst die Rechteprüfung, die alle anderen Host-Aktionen bereits haben.
   Frühwarnung: Ein automatisierter Test, der genau das versucht und eine Ablehnung erwartet.
   Gegenmaßnahme: Denselben Rechte-Mechanismus verwenden wie beim Hochladen/Ersetzen (`require_host`). In AK 6 + Testplan verankert.

💀 Szenario: Löschen einer Location, die gar kein Bild hat, oder einer Location-ID, die gar nicht existiert, führt zu einem verwirrenden Serverfehler statt einer klaren Rückmeldung.
   Auslöser: Fehlender Zustands-Check vor dem eigentlichen Löschvorgang.
   Frühwarnung: Testfall mit „Location ohne Bild" und „Location existiert nicht".
   Gegenmaßnahme: Beide Fälle als eigene Edge-Case-AKs (7 + 8) und eigene Testfälle verankert.

**Architektur-Analyse:**
- Betroffene Dateien: `backend/main.py` (neuer Endpunkt analog zu `upload_location_image`, direkt im bestehenden US-120-Abschnitt Zeilen 2183–2314), `web/index.html` (neuer Lösch-Button in `_imageAreaHtml()` Zeile 5368–5394 + neue Klickfunktion analog zu `triggerImageUpload()`/`_onImageFileSelected()`, neue CSS-Klasse analog zu `.loc-image-edit-btn` Zeile 386–388).
- Render-Pfad-Check (4g, Pflicht bei visuellem Element): Das Beispielbild wird als normales `<img>`-Tag im DOM gerendert (`web/index.html:5375`), keine Server-seitige Grafik/Legende-Trennung wie beim BUG-59-Fall — der Löschen-Button steuert direkt denselben Anzeigepfad, kein zusätzlicher Rendering-Pfad zu beachten.
- Einstiegspunkt-Check: Das Beispielbild wird ausschließlich in der Location-Detailansicht angezeigt (kein zweiter Entry-Point wie Feed/Kalender/Scout betroffen) — kein Datenquellen-Divergenz-Risiko.
- Designer-Check (4b, Pflicht da visuell): durchgeführt (`fotoalert-designer`). Ergebnis: Löschen-Button als eigenes Icon (Papierkorb, 2px Linienstil, Bauhaus-Icon-Konvention) in Signalfarbe `--red` auf dem bestehenden halbtransparenten dunklen Button-Hintergrund (`rgba(0,0,0,.55)`, konsistent zu `.loc-image-edit-btn`), mit ausreichendem Abstand zum „Ersetzen"-Button, damit beide Touch-Ziele (≥44px) sich nicht berühren. Bestätigungsdialog per bereits vorhandenem `confirm()`-Muster, kein neues Dialog-UI nötig.

**Analyse & Planung Checkliste:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt (inkl. Pflicht-Code-Verifikation)
- [x] Architektur analysiert: `backend/main.py`, `web/index.html`
- [x] Designer-Check: visuell (neuer Button + Icon) → `fotoalert-designer` aufgerufen, Ergebnis eingearbeitet
- [x] Implementierungsoptionen: A / B (siehe unten)
- [x] Empfehlung: Option A

**Implementierungsoptionen:**

### Option A — Eigenständiger Lösch-Endpunkt + eigener Button (Wiederverwendung bestehender Bausteine)
- Vorgehen: Neuer Endpunkt `DELETE /locations/{loc_id}/image`, der die bereits vorhandene Funktion `_delete_location_image_file()` aufruft und `image_filename` auf der Location auf „leer" setzt (analog zum bestehenden Muster in `delete_location`). Im Frontend: neuer Löschen-Button in `_imageAreaHtml()`, eigene Klickfunktion mit Sicherheitsabfrage (wiederverwendetes `confirm()`-Muster), danach Location neu laden (bestehendes Server-Fetch-Pattern).
- Betroffene Dateien: `backend/main.py`, `web/index.html`, neuer Test `backend/tests/test_us_125.py`.
- Vorteile: Nutzt konsequent bereits vorhandene, bewährte Bausteine (Löschfunktion, Rechteprüfung, Bestätigungsmuster, Server-Fetch-Pattern) — minimales Risiko neuer Fehlerquellen, passt exakt zum bestehenden US-120-Code.
- Nachteile/Risiken: Keine wesentlichen — kleinste sinnvolle Erweiterung des bestehenden Systems.
- Aufwand: klein.

### Option B — Löschen nur als Sonderfall des Upload-Endpunkts (z. B. Upload mit leerer Datei signalisiert „löschen")
- Vorgehen: Kein neuer Endpunkt; stattdessen der bestehende Upload-Endpunkt so erweitert, dass ein bestimmter Spezialwert (z. B. leerer Body) als „lösche das aktuelle Bild" interpretiert wird.
- Betroffene Dateien: `backend/main.py` (upload_location_image umgebaut).
- Vorteile: Ein Endpunkt weniger.
- Nachteile/Risiken: Vermischt zwei fachlich unterschiedliche Aktionen (Hochladen vs. Löschen) in einer Funktion — unklarere Fehlermeldungen, schwerer verständlicher Code, widerspricht dem Grundsatz „ein Endpunkt, eine Aufgabe". Erhöht das Risiko, dass ein normaler Upload versehentlich als Löschen interpretiert wird.
- Aufwand: mittel (wegen Sonderfall-Logik und höherem Testaufwand).

✅ **Empfehlung: Option A** — nutzt die bereits vorhandene, in US-120 bewährte Löschfunktion direkt wieder, hält Lösch- und Hochlade-Vorgang sauber getrennt (ein Endpunkt, eine Aufgabe) und passt sich nahtlos ins bestehende Rechte-/Bestätigungs-/Fetch-Muster ein. Geringstes Risiko, kleinster Aufwand.

**Testplan:**
- [x] Automatisiert (Harness): `backend/tests/test_us_125.py` — deckt AK 5 (Datei wirklich weg), AK 6 (nur Host, 403/401 für andere), AK 7 (Löschen ohne vorhandenes Bild → verständlicher Fehler), AK 8 (Löschen bei nicht existierender Location → 404) ab. **Ergebnis 2026-07-05: 4/5 grün.** Der einzige Fehlschlag (`test_delete_removes_image_url_and_file`, AK 5 physisches Löschen) ist kein Code-Fehler, sondern eine Sandbox-Einschränkung: das gemountete Projektverzeichnis in der Implementierungs-Sandbox ist ein FUSE-Mount, der `unlink()`/`os.remove()` generell mit `PermissionError: Operation not permitted` ablehnt (reproduziert unabhängig vom Testcode per direktem `rm`/`os.remove` auf eine beliebige Datei im Mount). Auf dem echten Server (kein FUSE-Mount) sollte der Test wie erwartet grün laufen — das muss beim ersten echten Testlauf/Deploy verifiziert werden.
- [x] Manuell: **Von Stephan am 2026-07-05 lokal vollständig getestet, alle Punkte bestanden** (curl-Tests UND Browser-UI-Tests) — inkl. Datei/URL wirklich weg (`image_url` → `None`), 401 ohne Token, 404 „kein Beispielbild" bei erneutem Löschen, 404 „Location nicht gefunden" bei nicht existierender Location.
  1. Als Host einloggen, eine Location mit Beispielbild öffnen. Erwartet: Bild ist sichtbar, daneben zwei getrennte Buttons „Ersetzen" und „Löschen".
  2. Auf „Löschen" tippen. Erwartet: Eine Sicherheitsabfrage erscheint mit dem Hinweis, dass die Aktion nicht rückgängig gemacht werden kann.
  3. Die Abfrage abbrechen. Erwartet: Das Bild bleibt unverändert sichtbar, nichts ändert sich.
  4. Erneut auf „Löschen" tippen und diesmal bestätigen. Erwartet: Das Bild verschwindet sofort, die Location zeigt wieder den leeren Platzhalter „Noch kein Beispielbild" mit Upload-Button.
  5. Die Location schließen und erneut öffnen (oder Seite neu laden). Erwartet: Der leere Platzhalter bleibt bestehen — das Bild ist dauerhaft weg, nicht nur kurzzeitig ausgeblendet.
  6. Als normaler Nutzer (nicht Host) dieselbe Location öffnen. Erwartet: Kein Ersetzen- und kein Löschen-Button sichtbar, nur das (falls vorhandene) Bild selbst.
  7. Regression (PRODUCT.md Sektion 12): Nach der Änderung zusätzlich prüfen, dass Bild-Hochladen (US-120) weiterhin normal funktioniert, dass das Löschen der kompletten Location weiterhin auch ein vorhandenes Bild sauber mit entfernt, und dass die Location-Detailansicht insgesamt (andere Sektionen, FOV-Karte) unverändert funktioniert.

#### 🎨 Design-Entscheidung (fotoalert-designer) · 2026-07-05

**So fühlt es sich an:** Über dem Beispielbild sitzt oben rechts weiterhin der bekannte „Ersetzen"-Button (Kamera-Symbol). Direkt daneben — mit spürbarem Abstand, nicht Kante an Kante — steht jetzt ein zweiter, deutlich anders aussehender Button mit einem Papierkorb-Symbol. Während „Ersetzen" wie bisher unauffällig dunkel-transparent bleibt, ist der Papierkorb in Warnrot gehalten: Rot ist in der App immer das Signal für „Achtung, das ist eine endgültige Aktion" (dieselbe Farbe wie beim Löschen einer ganzen Location). Tippt der Host darauf, hält die App kurz inne und fragt nach: „Beispielbild wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden." Erst ein bestätigendes Antippen entfernt das Bild wirklich — danach erscheint sofort wieder der leere, gestrichelte Platzhalter mit der Möglichkeit, ein neues Bild hochzuladen. Bricht der Host die Nachfrage ab, bleibt alles exakt wie vorher, ohne jede sichtbare Veränderung.

**Schritt für Schritt:**
1. Host öffnet eine Location mit Beispielbild → sieht zwei getrennte Buttons oben auf dem Bild: „Ersetzen" (Kamera) und „Löschen" (Papierkorb, rot).
2. Host tippt auf „Löschen" → Sicherheitsabfrage erscheint mit Warnhinweis.
3. Host bestätigt → Bild verschwindet sofort, Platzhalter „Noch kein Beispielbild" erscheint.
4. Host bricht stattdessen ab → nichts verändert sich, das Bild bleibt wie es war.

**Warum so:** Die beiden Buttons dürfen auf keinen Fall wie zwei gleichwertige Varianten derselben Aktion wirken — ein Host, der eigentlich ersetzen wollte, darf nicht aus Versehen löschen. Deshalb tragen sie unterschiedliche Symbole (Kamera vs. Papierkorb), unterschiedliche Farbgebung (neutral-dunkel vs. Warnrot) und ausreichend räumlichen Abstand. Die Sicherheitsabfrage ist das zusätzliche Sicherheitsnetz für den Fall, dass trotzdem der falsche Button getroffen wird.

**Technische Eckpunkte:** Neuer Button `.loc-image-delete-btn` (gleiche Bauform wie bestehendes `.loc-image-edit-btn`: `position:absolute; top:10px`, aber `left:10px` statt zusammen mit „Ersetzen" auf der rechten Seite — dadurch maximaler Abstand statt nur ein paar Pixel Lücke), Icon `${ic('i-trash',14)}` (bereits im Icon-Set vorhanden, keine Neuanlage nötig), Text-/Icon-Farbe `var(--red)` auf dem bestehenden `rgba(0,0,0,.55)`-Button-Hintergrund (ausreichender Kontrast in Hell- wie Dunkel-Modus, da `--red` in beiden Themes hell genug definiert ist: `#c8472f` / `#e0664f`). Touch-Ziel wie beim bestehenden Edit-Button ≥44px durch Padding sicherstellen. Sicherheitsabfrage per vorhandenem `confirm()`-Muster (analog `deleteLocation`), kein neues Dialog-UI.

---

### US-126 · Host kann den angezeigten Bildausschnitt (Crop) des Beispielbilds selbst wählen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-05 |
| **Abgeschlossen** | 2026-07-05 |

**Beschreibung:** Als Host möchte ich den sichtbaren Ausschnitt eines Beispielbilds selbst festlegen können. Aktuell (seit US-120) wird bei Quer- oder Hochformatbildern immer automatisch die Bildmitte als Ausschnitt gewählt (Rule 2 in US-120: „der sichtbare Bildausschnitt wird immer mittig aus dem Originalbild genommen"). Das kann dazu führen, dass bei Bildern, deren Motiv nicht zentriert ist, genau der Teil abgeschnitten wird, der das eigentliche Motiv zeigt.

**User Story:** Als Host, möchte ich nach dem Hochladen eines Beispielbilds selbst festlegen können, welcher Bildausschnitt in Hoch- und Querformat-Ansicht sichtbar bleibt, sodass das Motiv auch dann vollständig erkennbar ist, wenn es im Originalfoto nicht mittig sitzt.

**Bezug:** Direkte Erweiterung/Korrektur von **US-120** [x] (Done, 2026-07-04) — konkret dessen Rule 2 und AK „Egal ob das Originalfoto hoch- oder querformatig ist … der sichtbare Bildausschnitt ist immer mittig aus dem Originalbild genommen". Kein Bug an US-120 selbst (die feste Mitten-Logik wurde damals bewusst so spezifiziert und freigegeben), sondern eine bewusste Erweiterung um Host-Steuerung. Keine Dublette gefunden (Suche nach „Ausschnitt", „Crop", „object-fit/object-position" ergab sonst keine Treffer außer US-115 und US-47, beide inhaltlich nicht verwandt: US-115 betrifft den Mond-Sichtachsen-Ausschnitt in der Chancen-Berechnung, US-47 betrifft KI-Kompositions-Vorschläge — beide anderer Fachbereich). Berührt dieselbe UI-Fläche (Location-Detail/Bearbeiten-Formular) wie **US-125** (Bild löschen, neu), beide unabhängig voneinander umsetzbar.

#### 🔬 Analyse & Spec (US-126) · 2026-07-05

##### 📎 Code-Verifikation (Pflicht, durchgeführt 2026-07-05)

- `web/index.html` Zeile 372–378: Kommentar bestätigt die Ticket-Prämisse wörtlich — „US-120: Beispielbild … `object-position:center` hält den Bildausschnitt in JEDER Kombination aus Bild- und Geräteausrichtung mittig (hartes AK)." Die konkrete Regel: `.loc-image-area img { width:100%; height:100%; object-fit:cover; object-position:center; display:block; }`. Der Anzeige-Container `.loc-image-area` hat ein festes Seitenverhältnis `aspect-ratio: 4/3` (Zeile 376) — unabhängig vom Seitenverhältnis des Originalbilds.
- `backend/main.py` Zeile 2187–2233 (`_process_uploaded_image`): Das Originalbild wird serverseitig **nicht** zugeschnitten — nur EXIF-Ausrichtung korrigiert, auf `_IMAGE_MAX_DIMENSION_PX` verkleinert (Seitenverhältnis bleibt erhalten) und als JPEG komprimiert. Das volle, unbeschnittene Bild wird gespeichert. Der eigentliche „Crop" auf 4:3 entsteht **ausschließlich** im Frontend zur Anzeigezeit durch CSS `object-fit:cover`.
- Bedeutet: Eine Fokuspunkt-/Crop-Lösung kann rein clientseitig über einen dynamischen `object-position`-Wert (z. B. `30% 70%` statt `center`) umgesetzt werden — **ohne** das gespeicherte Bild serverseitig neu zuzuschneiden oder zu ersetzen. Ein voller Crop-Rahmen mit Zoom (Option B unten) würde dagegen echte Pixel-Manipulation brauchen und müsste entweder serverseitig (neues Bild schreiben) oder ebenfalls nur über CSS-Transform gelöst werden.
- Datenmodell: `image_filename` ist die einzige bild-bezogene Spalte in `backend/data/store.py` Zeile 158 (`TEXT DEFAULT NULL`, SQLite `custom_locations`-Tabelle) sowie im Override-Mechanismus für Standard-Locations (`backend/main.py` Zeile 1199–1201, Feld-Whitelist). Es gibt **keine** Spalte/kein Feld für eine Crop-Position — das müsste neu ergänzt werden (analog zum bestehenden Muster für `image_filename`).
- `PATCH /locations/{id}` (Zeile 2317–2327): Aktuell erlaubte Felder sind `coord_fields`, `text_fields`, `numeric_fields`, `list_fields` — kein Bildfeld überhaupt. Für eine neue Crop-Position müsste entweder dieser Endpunkt um ein neues Feld erweitert werden, oder der bestehende Bild-Upload-Endpunkt (`POST /locations/{loc_id}/image`, Zeile 2254) würde die Position zusätzlich mit entgegennehmen.

##### Scope & Annahmen-Protokoll

- 🔴 **Kritisch — Geltungsbereich (neu vs. bestehend):** Soll die Crop-Auswahl nur für **neu hochgeladene** Bilder verfügbar sein, oder auch **rückwirkend** für die bereits per US-120 hochgeladenen, bestehenden Beispielbilder nutzbar sein (nachträgliches Verschieben ohne erneuten Upload)? Beeinflusst, ob ein eigener „Ausschnitt anpassen"-Einstieg für bestehende Bilder gebaut werden muss oder ob die Auswahl nur direkt im Upload-Fluss auftaucht.
- 🔴 **Kritisch — Interaktionstiefe:** Reicht ein **einfacher Fokuspunkt-Klick** auf dem Bild (Host tippt auf die Stelle, die sichtbar bleiben soll → steuert nur `object-position`), oder wird ein **voller Crop-Rahmen mit Ziehen/Zoom** erwartet (Host kann Ausschnittsgröße und -Position frei bestimmen, ähnlich einem Bildzuschneide-Tool)? Beeinflusst den Aufwand massiv (siehe Optionen A/B unten).
- 🔴 **Kritisch — Zuschnitt-Ort:** Wird der Ausschnitt **clientseitig** (nur Anzeige-CSS, Originalbild bleibt unangetastet) oder **serverseitig** (echtes Zuschneiden/Neuschreiben der Bilddatei) vorgenommen? Beeinflusst die Architektur direkt: rein clientseitig bedeutet nur ein neues gespeichertes Positionsfeld + CSS-Änderung; serverseitig bedeutet Bildverarbeitung, neue Datei, höhere Komplexität.
- 🔴 **Kritisch — Getrennte Werte für Hoch-/Querformat-Anzeige:** Die App zeigt das Beispielbild aktuell nur in einem festen Seitenverhältnis (`aspect-ratio: 4/3`, Hero-Bereich im Location-Detail). Gibt es weitere Anzeigekontexte mit anderem Seitenverhältnis (z. B. Kartenmarker-Vorschau, Locations-Liste), die ebenfalls einen (ggf. unterschiedlichen) Ausschnitt bräuchten? Falls ja: EIN gemeinsamer Fokuspunkt für alle Kontexte, oder pro Kontext ein eigener Wert? (Codesuche ergab aktuell nur den einen Anzeigeort im Location-Detail-Hero — falls das zutrifft, entfällt die Frage; bitte bestätigen.)
- ⚠️ **Annahme (Default, unkritisch):** Die Crop-Auswahl ist nur für den Host verfügbar (analog zu allen anderen Beispielbild-Aktionen aus US-120/US-125) — normale Nutzer sehen nur das Ergebnis, keine Auswahl-UI. Bitte bestätigen.
- ⚠️ **Annahme (Default, unkritisch):** Die gewählte Ausschnittsposition gilt für Hoch- **und** Querformat-Anzeige gemeinsam als ein Wert (bei `object-position` ist das ohnehin ein Punkt, kein pro-Format-Wert) — es gibt in der App aktuell keine unterschiedliche Darstellung des Beispielbilds je nach Geräte-Ausrichtung, sondern nur ein festes Seitenverhältnis im Hero-Bereich. Bitte bestätigen, falls hier eine andere Erwartung besteht (z. B. getrennte Werte für ein zukünftiges Hochformat-Layout).

##### Example Mapping

**📏 Rule 1:** Der Host kann nach dem Hochladen eines Beispielbilds eine Ausschnittsposition festlegen, die bestimmt, welcher Bereich des Originalbilds im Anzeigebereich sichtbar bleibt.
- 🟢 Beispiel: Ein Host lädt ein Landschaftsfoto hoch, dessen Motiv (ein Turm) am linken Bildrand steht. Er verschiebt den Fokuspunkt nach links. Danach zeigt das Location-Detail den Turm vollständig, nicht mehr den leeren rechten Bildteil.
- 🟢 Beispiel: Ein Host lädt ein Bild hoch und ändert nichts an der Ausschnittsposition. Das Verhalten bleibt wie bisher (Bildmitte sichtbar) — kein Pflichtschritt, keine Verschlechterung des bisherigen Verhaltens.

**📏 Rule 2:** Die gewählte Ausschnittsposition bleibt dauerhaft gespeichert und wird bei jedem erneuten Öffnen der Location angezeigt (nicht nur für die aktuelle Sitzung).
- 🟢 Beispiel: Host legt die Ausschnittsposition fest, schließt die App, öffnet sie am nächsten Tag erneut. Die Location zeigt weiterhin denselben angepassten Ausschnitt.

**📏 Rule 3:** Lädt der Host ein neues Bild hoch (Ersetzen-Funktion aus US-120), wird die zuvor gewählte Ausschnittsposition zurückgesetzt, da sie sich auf das alte Bild bezog.
- 🟢 Beispiel: Host ersetzt ein Beispielbild durch ein neues Foto. Danach zeigt die Location zunächst wieder die Bildmitte des neuen Fotos (Standardverhalten), bis der Host erneut eine Position wählt.

**📏 Rule 4:** Normale Nutzer (nicht Host) sehen keine Möglichkeit, die Ausschnittsposition zu verändern — sie sehen nur das Ergebnis.
- 🟢 Beispiel: Ein normaler Nutzer öffnet dieselbe Location. Er sieht das Beispielbild mit dem vom Host gewählten Ausschnitt, aber keinerlei Bedienelement dafür.

##### ❓ Offene Fragen an Stephan — ✅ beantwortet 2026-07-05

1. ✅ **Beantwortet:** Soll die Ausschnittswahl nur bei **neuen Uploads** möglich sein, oder auch **nachträglich für bereits vorhandene** Beispielbilder (eigener „Ausschnitt anpassen"-Zugang ohne erneuten Upload)? → **Auch nachträglich für bereits vorhandene Bilder.** Es braucht also einen eigenständigen Einstieg im Location-Detail, der unabhängig vom Upload-Vorgang funktioniert — nicht nur einen Schritt direkt nach dem Hochladen.
2. ✅ **Beantwortet:** Reicht ein **einfacher Klick auf die gewünschte Bildstelle**, oder soll der Host den Ausschnitt **frei ziehen und zoomen** können? → **Einfacher Klick auf die wichtige Stelle** (Option A, siehe unten — damit ist die Wahl zwischen Option A/B final entschieden, Option B entfällt).
3. ✅ **Beantwortet:** Soll der Ausschnitt nur **clientseitig gemerkt** werden oder soll das Bild **tatsächlich zugeschnitten** werden? → **Original bleibt unverändert**, nur die Anzeigeposition wird gespeichert. Kein serverseitiges Zuschneiden, keine neue Bilddatei.
4. ✅ **Beantwortet:** Gibt es weitere Stellen mit ähnlichem Bildformat-Problem, die eine eigene Ausschnittswahl bräuchten? → **Nein**, es bleibt bei dem einen Anzeigeort (Location-Detail-Hero-Bereich).

Damit sind alle vier vormals blockierenden Fragen geklärt und die Implementierung ist freigegeben (Option A, siehe „Implementierungsoptionen" unten).

**Akzeptanzkriterien:**
- [x] Der Host sieht im Location-Detail eine Möglichkeit, die sichtbare Bildstelle eines vorhandenen Beispielbilds zu verändern — durch einfachen Klick/Tipp auf die wichtige Stelle im Bild (kein Zieh- oder Zoom-Werkzeug).
- [x] Diese Möglichkeit steht nicht nur direkt nach einem neuen Hochladen zur Verfügung, sondern jederzeit auch nachträglich — auch für Beispielbilder, die schon vor diesem Ticket hochgeladen wurden.
- [x] Nach dem Festlegen einer neuen Ausschnittsposition zeigt die Location sofort den angepassten Bildausschnitt, ohne dass die Seite neu geladen werden muss.
- [x] Die gewählte Ausschnittsposition bleibt erhalten, wenn die Location geschlossen und erneut geöffnet wird (auch nach Neuladen der App).
- [x] Das Originalbild selbst wird durch die Ausschnittswahl nicht verändert — es wird nur gemerkt, welche Stelle sichtbar bleiben soll. Ein Herunterladen oder Weiterverwenden des Originalbilds liefert weiterhin das komplette, unveränderte Foto.
- [x] Ein normaler Nutzer (nicht Host) sieht keinerlei Bedienelement zur Ausschnittswahl — nur das fertige Bild mit dem vom Host gewählten Ausschnitt.
- [x] Edge Case Querformat: Bei einem breiten Panoramafoto mit seitlich sitzendem Motiv zeigt der gewählte Ausschnitt das Motiv vollständig, nicht mehr den leeren Bildbereich.
- [x] Edge Case Hochformat: Bei einem hohen Bild mit oben sitzendem Motiv (z. B. Turmspitze) zeigt der gewählte Ausschnitt den oberen Bildbereich, nicht die Mitte.
- [x] Edge Case Bild-Ersetzen: Lädt der Host ein neues Bild hoch, startet die Ausschnittsposition wieder bei der Bildmitte (kein „Geister"-Ausschnitt vom vorherigen Bild).
- [x] Edge Case ohne Änderung: Wählt der Host keine eigene Position, verhält sich die Anzeige exakt wie vor diesem Ticket (Bildmitte).
- [x] Edge Case ältere Bilder ohne gespeicherte Ausschnittsposition: Bei allen Locations, die noch keine eigene Ausschnittsposition haben (weil sie vor diesem Ticket angelegt wurden), zeigt die App weiterhin ganz normal die Bildmitte — kein Fehler, keine leere Anzeige.

**Pre-Mortem:**
- 💀 Szenario: Die neue Ausschnittsposition wird nur clientseitig im Browser gemerkt (z. B. localStorage) statt serverseitig gespeichert → Gegenmaßnahme: AK „bleibt nach Neuladen/auf anderem Gerät erhalten" verlangt serverseitige Persistenz (neues Feld analog `image_filename`), als Testfall in Harness verankert.
- 💀 Szenario: Ein Bild-Ersetzen (US-120-Funktion) übernimmt versehentlich die alte Ausschnittsposition für das neue, komplett anders aufgebaute Bild → falscher Ausschnitt sofort nach dem Ersetzen sichtbar → Gegenmaßnahme: Rule 3 + eigener AK, Reset der Position bei jedem Replace-Upload im selben Codepfad wie das Setzen von `image_filename` (Zeile 2301 in `upload_location_image`).
- 💀 Szenario: Die Klick-/Zieh-Interaktion für die Ausschnittswahl kollidiert mit dem bereits vorhandenen „Ersetzen"-Button (`.loc-image-edit-btn`, oben rechts im Bild) oder mit dem geplanten „Löschen"-Button aus US-125 (dieselbe UI-Fläche) → Buttons überlagern sich oder sind schwer trennbar antippbar → Gegenmaßnahme: Positionierung im Designer-Check klären, Touch-Ziele ≥44px, Buttons klar räumlich getrennt (siehe US-125-Analyse: „ausreichender Abstand zum Ersetzen-Button, damit Touch-Ziele sich nicht berühren" — gleiches Prinzip hier fortsetzen).
- 💀 Szenario: Nur die Standard-Locations (Override-Mechanismus) bekommen das neue Feld gespeichert, Custom-Locations (SQLite `custom_locations`-Tabelle) nicht oder umgekehrt → Ausschnitt wirkt nur bei einem der beiden Location-Typen → Gegenmaßnahme: Analog zu `image_filename` (das in BEIDEN Pfaden gepflegt wird, Zeile 2297–2300) muss das neue Feld ebenfalls in `_store.update_custom()` UND `_save_location_override()` behandelt werden; als AK/Testfall für beide Location-Typen verankern.
- 💀 Szenario: Bei Wahl von Option B (voller Crop-Rahmen mit Zoom) wird angenommen, das Originalbild werde tatsächlich zugeschnitten — tatsächlich verkleinert `_process_uploaded_image` das Bild bereits beim Upload auf `_IMAGE_MAX_DIMENSION_PX`; ein nachträglicher Zoom auf einen kleinen Bildausschnitt könnte in schlechter Auflösung enden, wenn nicht am Originalbild vor der Verkleinerung gearbeitet wird → Gegenmaßnahme: bei Wahl von Option B vorab klären, ob mit dem bereits komprimierten/verkleinerten Bild gearbeitet wird oder ein zweiter, unkomprimierter Rohbild-Pfad nötig ist.

**Analyse & Planung Checkliste:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt (inkl. Pflicht-Code-Verifikation)
- [x] Architektur analysiert: `web/index.html` (Zeile 372–378 CSS, Zeile 5371–5394 `_imageAreaHtml`), `backend/main.py` (Zeile 2254–2313 `upload_location_image`, Zeile 2317–2327 `patch_location`, Zeile 1435 Response-Mapping), `backend/data/store.py` (Zeile 154–160 Custom-Location-Spalten)
- [x] Designer-Check: visuell (neues Bedienelement für Ausschnittswahl) → siehe Bauhaus-Leitplanken unten (kein separater Designer-Agent-Aufruf möglich in diesem Lauf, daher inline)
- [x] Implementierungsoptionen: A / B (siehe unten)
- [x] Empfehlung: Option A

**Designer-Leitplanken (Bauhaus, inline statt separatem Designer-Agent-Aufruf):**
- Interaktive Elemente in `--accent` (aktuell `#2d4ea0` hell / `#7c9bea` dunkel, siehe `web/index.html` Zeile 44/77) statt hartkodierter Farbwerte — konsistent zu bestehenden Buttons (`.loc-image-upload-btn` nutzt bereits `var(--gold)`, ein Alias auf `--accent`, Zeile 384).
- Klare, kantige Formen ohne verspielte Schatten — passend zum bestehenden `.loc-image-edit-btn`-Stil (schlichter halbtransparenter dunkler Button-Hintergrund `rgba(0,0,0,.55)`, kein Drop-Shadow).
- Bei einem Fokuspunkt-Klick (Option A): sichtbarer, einfacher Marker (z. B. Kreis mit `--accent`-Rand) an der geklickten Stelle, kein dekoratives Fadenkreuz-Icon-Overdesign.
- Bei einem vollen Crop-Rahmen (Option B): schlichter rechteckiger Rahmen mit klaren Eckgriffen, keine abgerundeten „soften" Ecken-Handles — im Einklang mit den generell kantigen Radien im Design (`border-radius: 22px 22px 0 0` an Sheet-Kanten, keine verspielten Kreisformen für Kontrollelemente).

**Implementierungsoptionen:**

### Option A — Einfacher Fokuspunkt-Klick (steuert `object-position`) — final bestätigt, wird umgesetzt
- Vorgehen: Host tippt/klickt auf die Bildstelle, die zentriert bleiben soll. Die Klick-Koordinate wird in einen prozentualen Wert (`x% y%`) umgerechnet und als neues Feld (z. B. `image_focus_x`, `image_focus_y`) an die Location gehängt — gespeichert analog zu `image_filename` in beiden Location-Typen (Custom via `_store.update_custom()`, Standard via `_save_location_override()`). Anzeige: `.loc-image-area img { object-position: ${loc.image_focus_x}% ${loc.image_focus_y}%; }` ersetzt den hartkodierten Wert `center`. Kein Eingriff in die Bildverarbeitung nötig — reine Positionsangabe.
- Nachträgliche Nutzbarkeit für bestehende Bilder (Antwort auf Frage 1): Das neue Feld muss für **alle** bestehenden Locations **optional/nullable** sein (Default `NULL`/nicht gesetzt), nicht nur für neu angelegte. Fehlt der Wert (bestehende Locations vor diesem Ticket), fällt die Anzeige auf `object-position: center` zurück (heutiges Verhalten) — kein Pflicht-Migrationsschritt, der allen bestehenden Zeilen einen Wert zuweisen müsste. Der Bedienweg zum Setzen/Ändern der Position darf nicht an den Upload-Vorgang gekoppelt sein, sondern muss jederzeit im Location-Detail erreichbar sein (eigener Einstieg, unabhängig von „Ersetzen").
- Kein serverseitiges Zuschneiden (Antwort auf Frage 3): Es wird ausschließlich die Positionsangabe (`image_focus_x`/`image_focus_y`) persistiert. `_process_uploaded_image` und die gespeicherte Bilddatei selbst bleiben unverändert von diesem Ticket nicht betroffen — kein neuer Bildverarbeitungs-Codepfad nötig.
- Betroffene Dateien: `web/index.html` (Klick-Handler + dynamisches `object-position`, eigener Einstiegspunkt im Location-Detail unabhängig vom Upload-Fluss), `backend/main.py` (neues Feld in `PATCH /locations/{id}`-Whitelist oder eigener kleiner Endpunkt, Response-Mapping Zeile 1435, Reset bei Replace-Upload Zeile 2301), `backend/data/store.py` (zwei neue, nullable Spalten analog `image_filename`, Zeile 154–160, Default `NULL` für Bestandsdaten), neuer Test `backend/tests/test_us_126.py` (inkl. Testfall: Location ohne gesetztes Feld liefert weiterhin `center`-Verhalten).
- Vorteile: Kleiner, klar abgegrenzter Eingriff; nutzt exakt den bestehenden Anzeige-Mechanismus (`object-fit:cover`) weiter, nur der fixe `center`-Wert wird variabel; keine Bildverarbeitung nötig; Originalbild bleibt unangetastet (geringes Risiko für Qualitätsverlust); schnell verständliche Interaktion („tippe auf das, was wichtig ist").
- Nachteile/Risiken: Kein Zoom möglich — bei extremen Seitenverhältnis-Unterschieden zwischen Original und Anzeigebereich (z. B. sehr breites Panorama in 4:3-Anzeige) kann der Fokuspunkt allein nicht verhindern, dass ein großer Teil links/rechts abgeschnitten wird, auch wenn die *Position* stimmt.
- Aufwand: klein bis mittel.

### Option B — Voller Crop-Rahmen mit Ziehen/Zoom — ❌ verworfen, nicht Teil der Umsetzung (Stephan hat Option A final bestätigt)
- Vorgehen: Host bekommt ein Bildzuschneide-Werkzeug (rechteckiger, verschieb- und skalierbarer Rahmen über dem Originalbild), das Ausschnitt UND Zoomfaktor bestimmt. Ergebnis wird entweder als vier Koordinaten/Rahmenwerte gespeichert (clientseitig weiterhin über CSS-Transform/`object-position`+Skalierung umgesetzt) oder serverseitig als tatsächlich zugeschnittenes Bild neu geschrieben.
- Betroffene Dateien: zusätzlich zu Option A ein komplett neues UI-Modul (Crop-Interaktion mit Zieh-/Zoom-Gesten, Touch- und Maus-Handling), ggf. Erweiterung von `_process_uploaded_image` oder ein neuer Zuschneide-Endpunkt im Backend.
- Vorteile: Präziser — löst auch Fälle, in denen ein reiner Fokuspunkt nicht reicht (starke Formatunterschiede, siehe Nachteil oben).
- Nachteile/Risiken: Deutlich höherer Aufwand (eigenes Gesten-/Touch-Handling, mehr Testfälle, mehr Fehlerquellen bei Bildqualität falls serverseitig zugeschnitten wird, siehe Pre-Mortem-Szenario 5); deutlich größere UI-Fläche im ohnehin schon dichten Beispielbild-Bereich (Ersetzen-Button, evtl. Löschen-Button aus US-125).
- Aufwand: groß.

✅ **Empfehlung: Option A** — löst den gemeldeten Bug (nicht-zentriertes Motiv wird abgeschnitten) mit minimalem Aufwand, ohne das Originalbild zu verändern, und passt sich nahtlos in den bestehenden `object-fit:cover`-Mechanismus ein. Ein voller Crop-Rahmen (Option B) wäre nur gerechtfertigt, wenn Stephan in Frage 2 tatsächlich Zoom-Funktionalität für nötig hält — das sollte aber die Ausnahme sein, da die meisten gemeldeten Fälle („Motiv nicht mittig") bereits durch einen reinen Fokuspunkt gelöst werden.

✅ **Final bestätigt durch Stephan (2026-07-05): Option A.** Damit ist Option B endgültig verworfen, keine offene Entscheidung mehr.

**Testplan:**
- [x] Automatisiert (Harness): `backend/tests/test_us_126.py` — deckt ab: neues Feld wird korrekt gespeichert und im Response (`image_url`-Nachbarfeld) zurückgegeben (AK 1–3), Feld wird bei Replace-Upload zurückgesetzt (AK 7, Pre-Mortem 2), Feld funktioniert für Custom- UND Standard-Locations gleichermaßen (Pre-Mortem 4), fehlender Host-Zugriff liefert 401/403 (analog bestehendem Auth-Muster), Fallback 50/50 ohne gespeicherten Wert, Validierung (422 bei Wertebereich/Typ), 404 ohne Bild/nicht existierende Location. **Ergebnis 2026-07-05: 10/10 grün.**
- [x] Manuell: **Von Stephan am 2026-07-05 lokal vollständig getestet, alle Punkte bestanden** (curl-Tests UND Browser-UI-Tests) — inkl. Fokuspunkt setzen (PATCH → `ok:true`, Werte korrekt übernommen), Position bleibt nach Neuladen erhalten, 401 ohne Token, Bild-Ersetzen setzt Fokuspunkt auf 50/50 zurück (AK 9), Live-Update ohne Reload im Browser bestätigt, Quer-/Hochformat-Motiv nach Ausschnittwahl vollständig sichtbar, restliche Location-Detailansicht unverändert/nicht doppelt gerendert.
  1. Als Host ein Beispielbild mit erkennbar nicht-mittigem Motiv hochladen (z. B. Motiv am linken Bildrand). Erwartet: Zunächst wird wie bisher die Bildmitte angezeigt.
  2. Auf die Bildstelle mit dem Motiv tippen/klicken (die neue Ausschnittsauswahl). Erwartet: Der sichtbare Ausschnitt verschiebt sich sofort, das Motiv ist jetzt vollständig sichtbar.
  3. Location schließen und erneut öffnen (oder Seite neu laden). Erwartet: Der angepasste Ausschnitt bleibt erhalten, nicht wieder die Bildmitte.
  4. Ein neues Bild über „Ersetzen" hochladen. Erwartet: Zunächst wieder Bildmitte des neuen Bilds (kein alter Ausschnitt „durchgereicht").
  5. Als normaler Nutzer (nicht Host) dieselbe Location öffnen. Erwartet: Kein Bedienelement zur Ausschnittswahl sichtbar, nur das Bild mit dem vom Host gewählten Ausschnitt.
  6. Regression (PRODUCT.md Sektion 12): Prüfen, dass Bild-Hochladen/-Ersetzen (US-120) weiterhin normal funktioniert, dass ein eventuell parallel gebautes Löschen (US-125) weiterhin unabhängig funktioniert, und dass die restliche Location-Detailansicht (andere Sektionen, FOV-Karte) unverändert bleibt.

#### 🎨 Design-Entscheidung (fotoalert-designer) · 2026-07-05

**So fühlt es sich an:** Über dem Beispielbild erscheint als dritter Button (Kamera „Ersetzen" links, Papierkorb „Löschen" aus US-125 daneben) ein Fadenkreuz-Symbol mit der Beschriftung „Ausschnitt wählen" — in der ruhigen App-Blau-Farbe, weil das eine normale, jederzeit wiederholbare Aktion ist und keine Warnung braucht. Tippt der Host darauf, wechselt die Bildansicht spürbar in einen anderen Modus: Ein dünner blauer Rahmen legt sich um das Bild, und oben erscheint ein Hinweistext „Tippe auf die Stelle, die sichtbar bleiben soll". Der Host tippt einfach auf die für ihn wichtige Stelle im Bild — z. B. auf einen Turm, der bisher an einer Ecke stand. Genau dort erscheint sofort ein kleiner runder Marker (blauer Ring mit Punkt in der Mitte), und das Bild dahinter verschiebt sich in Echtzeit so, dass diese Stelle jetzt mittig im sichtbaren Bereich liegt. Der Host kann beliebig oft neu tippen, um die Position zu korrigieren — jedes Mal springt der sichtbare Ausschnitt sofort zur neuen Stelle. Ist er zufrieden, tippt er auf „Fertig" und verlässt den Auswahl-Modus; die Position ist ab sofort dauerhaft gespeichert, auch nach dem Schließen und späterem Wiederöffnen der Location. Ein „Abbrechen" daneben verlässt den Modus ohne zu speichern und lässt den bisherigen Ausschnitt unangetastet. Bei Locations, deren Bild schon vor diesem Feature hochgeladen wurde, gibt es noch keine gespeicherte Position — das wirkt aber nicht wie ein Fehler oder eine leere Stelle: Der Marker erscheint beim Öffnen des Auswahl-Modus einfach automatisch in der Bildmitte, als wäre dort ganz normal schon einmal eine Wahl getroffen worden. Ein normaler Nutzer (kein Host) sieht von alldem nichts — für ihn gibt es weder den Button noch den Auswahl-Modus, nur das fertige Bild mit dem vom Host gewählten Ausschnitt.

**Schritt für Schritt:**
1. Host sieht auf dem Beispielbild einen dritten Button „Ausschnitt wählen" (Fadenkreuz-Symbol, blau) neben „Ersetzen" und „Löschen".
2. Host tippt darauf → Bild bekommt einen sichtbaren blauen Rahmen, ein Hinweistext oben erklärt „Tippe auf die Stelle, die sichtbar bleiben soll", zwei Buttons „Fertig" und „Abbrechen" erscheinen.
3. Host tippt auf die für ihn wichtige Bildstelle → dort erscheint sofort ein runder Marker, der sichtbare Bildausschnitt verschiebt sich live dorthin.
4. Host kann beliebig oft neu tippen, um die Stelle zu korrigieren, bevor er sich entscheidet.
5. Host tippt „Fertig" → Auswahl-Modus schließt sich, neue Position ist gespeichert und bleibt auch nach erneutem Öffnen der Location erhalten.
6. Alternativ tippt Host „Abbrechen" → Auswahl-Modus schließt sich ohne Änderung, der bisherige Ausschnitt bleibt wie er war.
7. Bei einer Location mit einem alten Bild ohne gespeicherte Position: Der Marker sitzt beim Öffnen des Auswahl-Modus einfach automatisch in der Bildmitte — für den Host sieht das aus wie ein ganz normaler Startzustand, nicht wie ein Fehler.

**Warum so:** Ein eigener „Ausschnitt wählen"-Modus (statt einfach überall im Bild klickbar zu sein) verhindert, dass ein Host versehentlich beim normalen Betrachten des Bildes die Position verstellt. Die blaue Rahmen-/Hinweis-Optik macht unmissverständlich klar: „Du bist jetzt in einem besonderen Bearbeitungsmodus", genau wie andere Bearbeiten-Zustände in der App auch farblich abgesetzt sind. Die Farbe Blau (statt Rot wie beim Löschen) signalisiert bewusst: Das ist eine unkritische, jederzeit wiederholbare Aktion, kein Risiko wie beim endgültigen Löschen.

**Technische Eckpunkte:** Dritter Button `.loc-image-focus-btn` neben `.loc-image-edit-btn`/`.loc-image-delete-btn`, Icon `${ic('i-target',14)}` (bereits im Icon-Set vorhanden), Farbe `var(--accent)` statt `var(--red)` (Signalfarbe für Primäraktion, nicht Warnung). Auswahl-Modus: Overlay mit `border: 2px solid var(--accent)` um `.loc-image-area`, Hinweistext in Section-Header-Typografie (12px/700/uppercase-ähnlich, aber hier als normaler Hinweis in `--muted`/`--text`), Marker als kleiner SVG-Kreis (Ring `var(--accent)` + gefüllter Mittelpunkt), Klick-Koordinate wird in Prozentwerte umgerechnet und live in `object-position` gespiegelt. Fallback ohne gespeicherten Wert: `image_focus_x`/`image_focus_y` fehlen (`NULL`) → Marker-Startposition und `object-position` defaulten auf `50% 50%` (Bildmitte), identisch zum bisherigen `center`-Verhalten — kein Sonderfall-Styling, das wie ein Fehlerzustand aussieht.

---

### BUG-62 · Kartenansicht: Wetter-Filter und Kartenmodus-Umschalter überlappen auf schmalen Bildschirmen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-05 |
| **Abgeschlossen** | 2026-07-05 |

**Beschreibung:** Im Karten-Tab liegen zwei unabhängig positionierte Button-Gruppen oben im Kartenbereich: der Wetter-Filter (Aus/Wolken/Niederschlag, `#map-weather-toggle`, `top:12px; left:12px`, aus US-72) und der Kartenmodus-Umschalter (Nacht/Standard/Satellit, `#map-layer-toggle`, `top:12px; right:12px`). Beide sind mit festen Text-Buttons und festen Pixel-Abständen zum linken/rechten Rand positioniert, ohne Rücksicht auf schmale Bildschirmbreiten. Auf einem schmalen iPhone-Bildschirm wachsen beide Textgruppen so weit zusammen, dass sie sich in der Mitte überlappen und sich gegenseitig schwer lesbar/bedienbar machen. Auf breiteren Bildschirmen (iPad, größere iPhones) tritt das Problem nicht auf, da dort genug Platz zwischen den beiden Gruppen bleibt.

Stephans Lösungsidee (als Vorschlag, noch nicht entschieden — gehört in die Analyse-Phase): Statt Textbeschriftung Icons/Bilder verwenden, um die Buttons schmaler zu machen — links Aus/Wolken/Regenwolken-Symbol, rechts Nacht/Karte/Satellit-Symbol.

**Offene Frage (Scope):** Nicht abschließend geprüft, ob auf schmalen Screens noch weitere UI-Elemente im Karten-Tab kollidieren könnten (z. B. GPS-Button `#map-gps-btn`, Wetter-Zeitregler `#map-weather-slider-wrap`, Wetter-Legende `#map-weather-legend`). Diese sitzen laut Code an anderen Kanten (unten/GPS separat) und wurden von Stephan nicht gemeldet — sollte in der Analyse-Phase kurz mitgeprüft werden, ist aber vermutlich kein Problem, da nur die beiden oberen Button-Gruppen denselben vertikalen Bereich (`top:12px`) teilen.

**User Story:** Als App-Nutzer mit einem schmalen iPhone möchte ich im Karten-Tab den Wetter-Filter und den Kartenmodus-Umschalter beide vollständig lesbar und antippbar sehen, sodass ich auf meinem Gerät ungehindert zwischen Wolken/Niederschlag und Standard/Satellit/Nacht wechseln kann, ohne dass sich Beschriftungen überlagern oder Buttons aus Versehen den falschen Modus treffen.

**Bezug:** Kein Duplikat vorhanden — es existiert aktuell kein Ticket, das diese konkrete Überlappung behandelt. Verwandt: **US-123** [x] (Satellit/Standard-Umschalter für Location-Anlage-/Bearbeiten-Karten, `LocMapMode`) ist ein *anderer* Umschalter an anderer Stelle (Location-Formulare, nicht der Haupt-Karten-Tab) und daher keine Dublette — aber dort wurde nach dem Test bereits einmal eine ganz ähnliche Überlappung (mit dem Leaflet-Zoom-Menü) gefixt, indem der Button von `top/left` auf `bottom/left` verschoben wurde; zusätzlich wurde dort explizit der noch offene, nicht umgesetzte Vorschlag „Toggle-Buttons könnten je ein kleines Icon bekommen statt nur Text" notiert (US-123, Testfeedback-Abschnitt) — deckt sich mit Stephans jetziger Idee und sollte in der Analyse als Präzedenzfall herangezogen werden. Ebenfalls verwandt, aber ohne Überschneidung: **BUG-58** [x] (Zoom-Verhalten des Wetter-Umschalters) und **TASK-52** (Legenden-Position) betreffen denselben Karten-Tab, aber andere Elemente/Verhalten, nicht die Button-Überlappung selbst.

**Example Mapping:**

*Annahmen:*
- ✅ Von Stephan bestätigt (2026-07-05): „Schmaler Bildschirm" = ab iPhone SE / Mini (375px Breite) aufwärts korrekt darstellbar.
- ✅ Von Stephan bestätigt (2026-07-05): Die Wetter-Filter-Sub-Zeile („mm/%", erscheint nur wenn „Wolken"/„Niederschlag" aktiv ist) wird als zusätzlicher Kollisions-Faktor mitbehandelt.
- ✅ Aus Code bestätigt: GPS-Button, Zeitregler, Legende liegen im unteren Kartenbereich — keine Überschneidung mit den beiden oberen Gruppen (siehe Scope-Antwort unten).

*Regeln:*
- 📏 Regel 1 — Beide oberen Button-Gruppen bleiben auf jeder unterstützten Bildschirmbreite vollständig lesbar und einzeln antippbar.
  🟢 Beispiel: Auf einem iPhone SE (375px) sieht der Nutzer im Karten-Tab den Wetter-Filter links oben und den Kartenmodus-Umschalter rechts oben nebeneinander, ohne Berührung oder Überlappung.
- 📏 Regel 2 — Auch wenn die Wetter-Sub-Zeile („mm/%") eingeblendet ist, bleibt die rechte Gruppe unangetastet.
  🟢 Beispiel: Nutzer tippt „Wolken" an (Sub-Zeile „mm/%" erscheint) → der Kartenmodus-Umschalter rechts bleibt vollständig sichtbar und bedienbar.
- 📏 Regel 3 — Antippen trifft immer den beabsichtigten Button, nie einen überlappenden Nachbar-Button.

*Offene Fragen an Stephan (vor Umsetzung zu klären, nicht blockierend für die Empfehlung):*
1. Bevorzugte Lösungsrichtung: Icons statt Text, Zeilenumbruch, eingeklapptes Menü, oder kleinere Schrift/Padding? (Optionen unten, Empfehlung: Icons)
2. Reicht iPhone SE (375px) als schmalstes Referenzgerät für den Test?

**Scope:**
Eingeschlossen: Layout-Fix der beiden oberen Button-Gruppen (`#map-weather-toggle`, `#map-layer-toggle`) inkl. der bedingt sichtbaren Wetter-Sub-Zeile („mm/%"), auf allen Bildschirmbreiten.
Ausgeschlossen: Alle anderen Karten-Overlay-Elemente — siehe Scope-Antwort unten, keine Kollision festgestellt, daher nicht Teil dieses Tickets.

**Scope-Frage beantwortet (weitere betroffene Elemente?):** Nein. Code-Prüfung von GPS-Button (`bottom:30px; left:12px`), Wetter-Zeitregler (`bottom:30px`), Wetter-Legende (`bottom:100px; left:12px`) und Fehler-Banner (`top:100px`, zentriert) zeigt: Diese Elemente teilen sich nicht den oberen `top:12px`-Bereich der beiden Toggle-Gruppen und kollidieren auf schmalen Screens nicht zusätzlich. Einzige zu beachtende Nebenwirkung: Der Fehler-Banner („Wetterdaten nicht verfügbar", `top:100px`, zentriert) darf durch den Fix nicht neu überlappt werden — als Edge-Case-AK aufgenommen.

**Akzeptanzkriterien:**
- [x] Auf einem iPhone SE (375px Breite) sieht der Nutzer im Karten-Tab den Wetter-Filter links oben und den Kartenmodus-Umschalter rechts oben vollständig nebeneinander, ohne dass sich Beschriftungen oder Buttons berühren oder überlagern.
- [x] Wenn der Nutzer im Wetter-Filter „Wolken" oder „Niederschlag" antippt (wodurch die zusätzliche Zeile „mm/%" erscheint), bleibt der Kartenmodus-Umschalter rechts weiterhin vollständig sichtbar und bedienbar.
- [x] Der Nutzer kann auf einem schmalen Bildschirm jeden der sechs Buttons (aus/Wolken/Niederschlag/Nacht/Standard/Satellit) einzeln und ohne Fehltreffer antippen.
- [x] Auf breiteren Bildschirmen (iPhone Pro Max, iPad) sieht die Kartenansicht weiterhin so aus wie bisher — keine unnötige Änderung des bestehenden Erscheinungsbilds dort.
- [x] Edge Case: Ist zusätzlich die Fehlermeldung „Wetterdaten nicht verfügbar" (zentriert oben) eingeblendet, bleibt sie weiterhin lesbar und überlappt nicht neu mit einer der beiden Gruppen.

**Test bestätigt (Stephan, 2026-07-05):** „alles wie erwartet" — manueller Test auf schmalem Fenster (375px) durchgeführt, alle Kriterien oben visuell geprüft.

**Deploy-Hinweis:** Der Icon-Code wurde technisch bereits mit dem Release v1.21.4 (US-117) ausgeliefert — `release.sh` committet immer den vollständigen Dateistand von `web/index.html`, und zu diesem Zeitpunkt lag der BUG-62-Code bereits ungetestet im Arbeitsverzeichnis. Release v1.21.5 hat daher inhaltlich nur den Versions-Bump für `index.html`/`sw.js` plus PRODUCT.md-Nachtrag und TASK-57 committet. Funktional kein Problem (derselbe Code wurde soeben getestet und bestätigt), aber die Reihenfolge Test→Refactor→Release war für BUG-62 nicht sauber eingehalten — siehe Retro.

**Pre-Mortem:**
📎 Code-Verifikation: `web/index.html` Z. 261–336 (CSS) und Z. 1063–1100 (Markup) gelesen am 2026-07-05. Bestätigt: beide Gruppen exakt auf `top:12px`, feste `left:12px`/`right:12px`, keine `@media`-Anpassung vorhanden. Wetter-Filter hat bedingt sichtbare zweite Zeile („mm/%"). GPS-Button/Zeitregler/Legende im unteren Kartenbereich — keine Überschneidung.

- 💀 Fix behebt nur den Grundzustand, die Wetter-Sub-Zeile („mm/%") wird beim Testen übersehen und bricht das Layout erneut sobald „Wolken" aktiv ist → Gegenmaßnahme: eigenes AK + Testschritt.
- 💀 Fix wird nur an einem größeren Referenzgerät getestet, das schmalste unterstützte Gerät (SE/Mini) bleibt kaputt → Gegenmaßnahme: Testplan verlangt explizit 375px-Breite.
- 💀 Icons ersetzen Text, aber ohne Tooltip/Beschriftung wird unklar, welches Icon welchen Modus bedeutet (Verwechslungsgefahr Wolke/Regenwolke) → Gegenmaßnahme: Tooltip/aria-label Pflicht bei Icon-Wahl.
- 💀 Fix funktioniert im Hochformat, bricht im Querformat erneut, weil dort die Breite anders verteilt ist → Gegenmaßnahme: Querformat als zusätzlicher Testschritt.
- 💀 Der ähnliche, bereits gelöste Fall US-123 wird 1:1 kopiert, obwohl dort eine andere Kollisionsursache (Leaflet-Zoom-Menü) vorlag → Gegenmaßnahme: US-123 nur als Inspiration behandelt, nicht als Vorlage übernommen.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` (CSS Z. 268–295, Markup Z. 1066–1082) — reiner Frontend-Layout-Bug, kein Backend-Bezug
- [x] Designer-Check: visuell? → ja — Kernaussage: bei Icon-Wahl klare geometrische Symbole (kein Emoji-Look), Pflicht-Tooltip/aria-label
- [x] Implementierungsoptionen: A (Icons) / B (kleinere Schrift/Padding) / C (Zeilenumbruch) / D (eingeklapptes Menü)
- [x] Empfehlung: Option A

**Implementierungsoptionen:**

*Option A — Icons statt Text (Stephans Vorschlag):* Text-Buttons durch kompakte Icons ersetzen (Sonne/Wolke/Regenwolke links; Mond/Karte/Satellit rechts) mit Tooltip/aria-label. Betrifft `web/index.html` CSS (Z. 268–295) + Markup (Z. 1066–1082). Vorteil: deutlich schmaler, skaliert auf jede Breite, deckt sich mit dem in US-123 bereits notierten offenen Wunsch. Nachteil: Bedeutung ohne Tooltip evtl. unklar (mitigiert), Wolke/Regenwolke-Verwechslungsgefahr. Aufwand: mittel.

*Option B — Kleinere Schrift/Padding nur auf schmalen Screens (Media Query):* Text-Buttons bleiben, Schriftgröße/Padding wird auf schmalen Screens per `@media` reduziert. Vorteil: minimal-invasiv. Nachteil: skaliert nicht beliebig, wirkt nur wie Symptombekämpfung, insbesondere bei „Niederschlag" als längstem Label. Aufwand: klein.

*Option C — Umbruch in zweite Zeile auf schmalen Screens:* Kartenmodus-Umschalter bricht auf schmalen Screens in zwei Zeilen um. Nachteil: bricht die kompakte Optik, blockiert mehr Kartenfläche, kollidiert potenziell mit der Wetter-Sub-Zeile. Aufwand: mittel.

*Option D — Eingeklapptes Menü:* Nur aktiver Modus sichtbar, Antippen öffnet Auswahl. Größte Verhaltensänderung, Overkill für dieses Layout-Problem. Aufwand: groß.

✅ **Empfehlung: Option A (Icons)** — deckt sich mit Stephans eigenem Vorschlag und dem bereits in US-123 notierten offenen Wunsch, skaliert zuverlässig auf jede Bildschirmbreite (anders als B), ohne die kompakte Optik aufzugeben (anders als C/D). Tooltip/aria-label schließt das Pre-Mortem-Risiko der Bedeutungs-Unklarheit.

**Testplan:**
- [ ] Manuell (Browser, http://localhost:8000): Karten-Tab öffnen, Browserfenster/iPhone-Simulator auf 375px Breite stellen (iPhone SE) → prüfen, ob sich Wetter-Filter (links oben) und Kartenmodus-Umschalter (rechts oben) berühren oder überlappen.
- [ ] Manuell: Im Wetter-Filter „Wolken" antippen (Sub-Zeile „mm/%" erscheint) → prüfen, ob der Kartenmodus-Umschalter rechts weiterhin vollständig sichtbar und bedienbar bleibt.
- [ ] Manuell: Jeden der sechs Buttons einzeln antippen → prüfen, ob jeweils der richtige Modus aktiviert wird (kein Fehltreffer durch Nachbar-Button).
- [ ] Manuell: Breiteres Gerät (iPhone Pro Max oder iPad-Simulation) → prüfen, dass sich am bisherigen Erscheinungsbild nichts Unerwartetes ändert.
- [ ] Manuell: Fehler-Banner „Wetterdaten nicht verfügbar" provozieren (z.B. Wetterdaten-Fetch offline) → prüfen, ob er weiterhin lesbar bleibt und nicht neu überlappt.
- [ ] Manuell: Gerät ins Querformat drehen → prüfen, ob die Überlappung dort ebenfalls behoben bleibt (Beobachtung, nicht hartes AK).

#### 🎨 Design-Entscheidung (fotoalert-designer) · 2026-07-05

Option A (Icons statt Text) bestätigt. Erste Icon-Entwürfe (abstrakte Kreis-Formen)
wurden von Stephan als nicht erkennbar zurückgewiesen — Wolke, Regenwolke und
Satellit waren nicht als solche zu identifizieren. Überarbeitete Fassung mit
etablierten, klar erkennbaren Symbolformen (durchgehende Wolken-Kontur statt
zweier loser Kreise; gestaffelte Regentropfen unter der Wolke; Satellit als
schräg gestellter Korpus mit zwei Solar-Panels und kurzer Antenne) von Stephan
freigegeben. Nacht (Mond-Sichel) und Karte (2×2-Raster) blieben gegenüber dem
ersten Entwurf unverändert.

Finale Icon-Zuordnung:
- Links (Wetter-Filter): Aus (durchgestrichener Kreis) · Wolken (Wolken-Kontur) · Regenwolken (Wolken-Kontur + drei gestaffelte Tropfen)
- Rechts (Kartenmodus): Nacht (Mond-Sichel) · Karte (2×2-Raster) · Satellit (schräger Korpus mit Solar-Panels + Antenne)

Alle sechs Icons: Linien-Stil, 2px Strich, monochrom (`currentColor`), Touch-Target ≥44px in der finalen Umsetzung (Mockup zeigte 34px nur zur Platzdemonstration). Pflicht-Tooltip/aria-label je Button bleibt bestehen (Pre-Mortem-Gegenmaßnahme).

---

### BUG-63 · „Alignments berechnen" blockiert den Server für alle Nutzer ca. 20–25 Sekunden `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | ToDo |
| **Erstellt** | 2026-07-05 |

**Beschreibung:** Beim Klick auf „Alignments berechnen" in der Anlage-Maske (Quick Location Capture, `POST /preview-alignment`) wirkt der Server für ca. 20–25 Sekunden blockiert — auch andere Requests (z. B. einfaches Laden der Startseite `GET /`) hängen währenddessen. Beobachtet in zwei Testdurchläufen während der BUG-60-Tests am 2026-07-04, Ursache nicht verifiziert. Erwartet: Andere Nutzer/Requests werden von einer laufenden Alignment-Berechnung nicht spürbar ausgebremst.

**User Story:** Als App-Nutzer möchte ich, dass die Berechnung von Alignments in der Anlage-Maske andere Nutzer und meine eigenen weiteren Aktionen nicht für mehrere Sekunden blockiert, sodass die App für alle durchgängig reaktionsfähig bleibt, auch während jemand eine neue Location anlegt.

**Bezug:** Entstand als dokumentierter Nebenbefund im BUG-60-Ticket (siehe dort, Abschnitt „Nachgeholter UI-Klick-Test", 2026-07-04: „separat per Intake ins Backlog aufgenommen"). Keine Dublette gefunden — kein anderes Ticket behandelt diese konkrete Blockade von `/preview-alignment` bzw. `find_precise_alignment_times`. Verwandtes Lösungsmuster bereits an anderer Stelle etabliert: **TASK-48** (Szenario 4, Empfehlung) und die QA-Beschreibungs-Pipeline lagern vergleichbare rechenintensive/synchrone Aufrufe explizit per `asyncio.to_thread` aus dem Event-Loop aus — als Präzedenzfall für die Analyse-Phase relevant, aber kein Überschneidungs- oder Merge-Kandidat, da dort andere Endpunkte betroffen sind. Abgrenzung zu BUG-60: BUG-60 behandelt das automatisch vorbelegte Hinweise-Feld (bereits in Test), dieses Ticket behandelt ausschließlich die Blockade-Performance desselben Endpunkts.

---

### BUG-60 · HINWEISE-Feld wird bei Neuanlage automatisch mit Text vorbelegt `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-04 |

**Beschreibung:** Beim Anlegen einer Location über Quick Location Capture erscheint automatisch der Text „Automatisch erfasst via Quick Location Capture." im HINWEISE-Feld. Beobachtet: Das Feld ist von Anfang an vorbelegt, obwohl der Nutzer nichts eingetragen hat. Erwartet: Das Feld bleibt bei Neuanlage leer und wird nur befüllt, wenn der Nutzer selbst explizit einen Hinweis einträgt.

**User Story:** Als Nutzer, der über Quick Location Capture eine neue Location anlegt, möchte ich, dass das Hinweise-Feld leer bleibt, sodass ich nicht fälschlich denke, ich hätte schon etwas eingetragen, und das Feld nur zeigt, was ich selbst geschrieben habe.

**Bezug:** **BUG-50** [x] (Done, released 2026-06-29) hat einen verwandten, aber anderen Fehler behoben: Dort ließ sich der Text nach dem Löschen nicht dauerhaft entfernen (fehlende `special_notes`-Whitelist im PATCH-Endpoint). BUG-50 hat nur das Symptom „Text kommt nach dem Löschen wieder" behoben — nicht die Ursache, warum der Text bei der Neuanlage überhaupt erst automatisch gesetzt wird (vermutlich im Anlage-Code-Pfad von Quick Location Capture, nicht im PATCH-Endpoint). Kein Duplikat von BUG-50, aber engster Verwandter — beide betreffen dasselbe Feld. Abgrenzung: BUG-60 behandelt die Neuanlage, BUG-50 hat die Bearbeitung/Persistenz behandelt.

#### 🔬 Analyse & Spec (BUG-60) · 2026-07-04

##### 📎 Code-Verifikation (durchgeführt 2026-07-04)

- `backend/main.py` Zeile 2032–2078, Funktion `_save_alignment_as_location()`: Diese Funktion wird beim Speichern einer Quick-Capture-Location aufgerufen (ausgelöst durch `POST /preview-alignment` mit `save: true`).
- Zeile 2054–2067: Beim Anlegen des neuen Location-Objekts wird `special_notes="Automatisch erfasst via Quick Location Capture."` fest (hartkodiert, ohne Bedingung) gesetzt — bei **jeder** Quick-Capture-Neuanlage, ausnahmslos.
- Das Objekt wird direkt danach über `_save_custom_location(new_loc)` (Zeile 2069) in die Datenhaltung geschrieben (Custom-Locations-Datei, bestätigt durch Fund in `backend/data/custom_locations.json` Zeile 19: `"special_notes": "Automatisch erfasst via Quick Location Capture."`). Der Text wird also **direkt persistiert**, nicht nur als Platzhalter im Formular angezeigt.
- Frontend-Seite geprüft: `web/index.html` Zeile 5467–5469 rendert das Hinweisfeld korrekt aus dem geladenen Location-Objekt (`${loc.special_notes||''}`) — kein zusätzliches Vorbefüllen im Frontend, kein serverseitig unabhängiger zweiter Schreibpfad. Das Feld zeigt exakt das, was die Location-Datenstruktur enthält.
- Bestätigt: **ein einziger Schreibort.** Der Text entsteht ausschließlich in `_save_alignment_as_location()` beim Anlegen und wird 1:1 durchgereicht bis in die Anzeige. Kein bedingter Code (z. B. „nur wenn Nutzer nichts einträgt") — der Text wird unbedingt bei jeder Neuanlage über diesen Pfad gesetzt.
- Zum Vergleich: normale (nicht per Quick Capture angelegte) Standard-Locations in `backend/data/locations.py` haben ebenfalls `special_notes`, dort aber jeweils echte, individuelle Fotografie-Hinweise (z. B. „Bortle-Klasse ~3–4…", „Kranichzug: Oktober–November…") — das Feld ist konzeptionell für nützliche Zusatzinfos gedacht, nicht für Herkunfts-Metadaten. Das stützt die Vermutung, dass der Quick-Capture-Text ein Debug-/Herkunfts-Vermerk aus der Entwicklungsphase war, der nie für die Endnutzer-Sicht gedacht war.
- ⚠️ Annahme: Es gibt keinen erkennbaren fachlichen Grund (z. B. Support-Ticket, Auswertung, Filter), der aktuell auf den exakten Text „Automatisch erfasst via Quick Location Capture." als Marker angewiesen ist — im Code wurde keine Stelle gefunden, die diesen String liest oder darauf filtert (nur die Stelle, die ihn schreibt). Falls Stephan diesen Text als Herkunfts-Kennzeichnung nutzt (z. B. um Quick-Capture-Locations später wiederzufinden), müsste das vor der Umsetzung genannt werden.

##### Example Mapping

**📏 Rule 1:** Bei Neuanlage einer Location über Quick Location Capture bleibt das Hinweise-Feld leer, solange der Nutzer nichts einträgt.

🟢 Beispiel: Stephan nimmt ein Motiv per Quick Location Capture auf und speichert die Location, ohne im Hinweise-Feld etwas einzutragen. Beim Öffnen der neu angelegten Location ist das Hinweise-Feld leer.

🟢 Beispiel: Stephan legt eine Location per Quick Capture an und trägt direkt beim Anlegen (falls das Formular das zulässt) „Zugang nur zu Fuß" ein. Nach dem Speichern zeigt das Feld genau „Zugang nur zu Fuß" — nichts zusätzlich.

**📏 Rule 2:** Bereits bestehende Locations, die den automatischen Text schon enthalten, werden durch die Änderung nicht rückwirkend verändert.

🟢 Beispiel: Location „Ehrenhof-Kollonaden" (vor dem Fix per Quick Capture angelegt, Text noch vorhanden oder von Stephan per BUG-50-Fix bereits gelöscht) bleibt nach dem Fix unverändert — der Fix wirkt nur auf künftige Neuanlagen, kein rückwirkendes Aufräumen bestehender Daten.

❓ Question: Sollen bestehende Locations, die den automatischen Text noch enthalten (falls es davon noch welche gibt), im Rahmen dieses Tickets bereinigt werden, oder ist das bewusst außerhalb des Scopes (Nutzer löscht sie bei Bedarf selbst, wie in BUG-50 bereits ermöglicht)? ⚠️ Annahme (bis zur Klärung): Scope ist nur die Neuanlage, keine Datenbereinigung — passend zur Abgrenzung im Ticket „BUG-60 = Neuanlage".

**📏 Rule 3:** Die Herkunft „per Quick Location Capture angelegt" geht durch den Fix nicht verloren, falls sie an anderer Stelle als dem Hinweise-Feld gebraucht wird.

🟢 Beispiel: Nach dem Fix lässt sich weiterhin (falls technisch vorhanden) nachvollziehen, dass eine Location per Quick Capture entstanden ist — z. B. über die ID-Konvention `custom_<timestamp>` oder ein separates Feld, nicht aber über einen für den Nutzer sichtbaren Text im Hinweise-Feld.

⚠️ Annahme: Aktuell gibt es kein separates, unsichtbares Herkunftsfeld — die einzige Markierung war bislang der sichtbare Text selbst. Falls Stephan Wert auf eine (unsichtbare) Nachverfolgbarkeit legt, wäre das ein zusätzlicher Diskussionspunkt vor Umsetzung (siehe Pre-Mortem Szenario 1).

##### Akzeptanzkriterien

- [ ] AK-1: Stephan legt über Quick Location Capture eine neue Location an, ohne im Hinweise-Feld etwas einzutragen. Beim anschließenden Öffnen der Location ist das Hinweise-Feld leer — kein automatischer Text erscheint.
- [ ] AK-2: Stephan legt über Quick Location Capture eine neue Location an und trägt currently während/nach der Anlage einen eigenen Hinweis ein. Nach dem Speichern zeigt das Feld exakt diesen eigenen Text — unverändert, ohne zusätzlichen automatischen Text davor oder danach.
- [ ] AK-3 (Edge Case): Der neue automatische Leer-Zustand verhält sich identisch zum bewusst geleerten Zustand aus BUG-50 — Stephan kann das Feld jederzeit leeren und es bleibt dauerhaft leer (keine Rückkehr des alten Textes, auch nicht nach Server-Neustart).
- [ ] AK-4 (Regression): Alle anderen bei der Quick-Capture-Neuanlage automatisch gesetzten Werte (Name, Beschreibung, Kategorie, Distanz, Brennweitenvorschlag, Schwierigkeit) funktionieren unverändert wie bisher — nur das Hinweise-Feld wird leer statt vorbelegt.
- [ ] AK-5 (Regression): Normale Standard-Locations (nicht per Quick Capture angelegt) zeigen weiterhin ihre echten, individuellen Hinweistexte unverändert an.

##### Pre-Mortem

💀 **Szenario 1: Der Text war absichtlich als Herkunfts-/Debug-Marker gedacht — komplettes Entfernen ist Informationsverlust.**
Auslöser: Der Text diente ursprünglich dazu, im Nachhinein zu erkennen, welche Locations automatisiert per Quick Capture entstanden sind (z. B. zur Qualitätskontrolle, weil Quick-Capture-Daten evtl. ungenauer sind als von Hand kuratierte Standard-Locations).
Frühwarnung: Nach dem Fix lässt sich für neue Locations nicht mehr auf einen Blick unterscheiden „von Hand kuratiert" vs. „automatisch erfasst" — außer über die technische ID-Konvention `custom_<timestamp>`, die im Alltag nicht sichtbar ist.
Gegenmaßnahme: Vor Umsetzung mit Stephan klären, ob diese Unterscheidung gebraucht wird. Falls ja: Herkunft nicht im nutzersichtbaren Hinweise-Feld, sondern in einem separaten, nicht angezeigten Metadatenfeld festhalten (kein Scope Creep — nur falls Stephan das bestätigt, sonst ausschließlich Feld leeren).

💀 **Szenario 2: Halbe Lösung — Text verschwindet nur im Formular, bleibt aber in der Datenstruktur/DB bestehen.**
Auslöser: Fix wird nur im Frontend vorgenommen (z. B. Platzhalter statt echtem Wert), obwohl die Root Cause serverseitig liegt.
Frühwarnung: Beim direkten Abfragen der Location über die API (z. B. `GET /locations/{id}`) taucht der Text weiterhin auf, nur die Anzeige im Formular wäre kosmetisch leer.
Gegenmaßnahme: Fix zwingend an der Quelle in `_save_alignment_as_location()` (backend/main.py) ansetzen, nicht im Frontend kaschieren. AK-Test muss die tatsächlich gespeicherte Location prüfen, nicht nur die Bildschirmanzeige.

💀 **Szenario 3: Der Fix wirkt sich unbeabsichtigt auch auf den Import-Pfad „Locationscout-Import" aus.**
Auslöser: `tools/import_locationscout.py` Zeile 555 setzt ebenfalls einen automatischen `special_notes`-Text („Locationscout-Import. Tags: …“) — ein ähnliches Muster, aber ein anderer Code-Pfad und explizit nicht Teil dieses Tickets.
Frühwarnung: Falls in der Umsetzung versehentlich eine gemeinsame Hilfsfunktion angefasst wird, könnte sich das Verhalten auch beim Locationscout-Import ändern, was niemand angefordert hat.
Gegenmaßnahme: Änderung strikt auf `_save_alignment_as_location()` begrenzen; `import_locationscout.py` nicht anfassen (kein Scope Creep, dort ist der Text zudem inhaltlich nützlich – enthält echte Tags, keine reine Herkunftsfloskel).

💀 **Szenario 4: Bestehende Locations mit dem alten Text verwirren weiterhin, weil sie fälschlich als „bereits behoben" angenommen werden.**
Auslöser: Nutzer/Stephan geht nach dem Fix davon aus, dass auch ältere, bereits angelegte Locations automatisch bereinigt wurden.
Frühwarnung: Beim Durchsehen alter Quick-Capture-Locations taucht der alte Text weiterhin auf (siehe Rule 2 / Question oben).
Gegenmaßnahme: In der Test-/Freigabe-Kommunikation explizit klarstellen, dass der Fix nur künftige Neuanlagen betrifft, keine rückwirkende Bereinigung vornimmt.

##### Architektur-Analyse

**Betroffene Stelle:**
1. `backend/main.py`, Funktion `_save_alignment_as_location()`, Zeile 2065 — hartkodierte Zuweisung `special_notes="Automatisch erfasst via Quick Location Capture."` beim Anlegen des `PhotoLocation`-Objekts, das direkt danach persistiert wird.

**Nicht betroffen (geprüft, kein Änderungsbedarf):**
- `web/index.html` Zeile 5467–5469 — Formular-Rendering liest das Feld korrekt aus der Datenstruktur, kein eigenständiges Vorbefüllen.
- PATCH-Endpoint (`backend/main.py`, Whitelist `text_fields`/`all_allowed_fields`) — bereits durch BUG-50 korrekt für Bearbeiten/Persistenz gefixt, hier nicht erneut zu ändern.
- `store.py` `update_custom()` — unterstützt `special_notes` bereits korrekt, keine Änderung nötig.
- `tools/import_locationscout.py` Zeile 555 — eigener, unabhängiger Pfad mit eigenem (inhaltlich sinnvollem) Text, bewusst außerhalb des Scopes.

##### Implementierungsoptionen

**Was bedeutet das für die App:**

Option A: Beim Anlegen per Quick Capture bleibt das Hinweise-Feld leer, genau wie bei jedem anderen neu angelegten Textfeld ohne Nutzereingabe — der Nutzer sieht ein leeres Feld und weiß, dass es „seins" ist, sobald er etwas einträgt.

Option B: Gleiches Nutzererlebnis wie Option A, zusätzlich bleibt die Information „automatisch per Quick Capture erfasst" für Stephan im Hintergrund nachvollziehbar (z. B. über ein zusätzliches, nicht angezeigtes Feld) — nur relevant, falls Szenario 1 im Pre-Mortem tatsächlich zutrifft.

---

### Option A — Hartkodierten Text ersatzlos entfernen (leerer Default)

- **Vorgehen:** Zeile 2065 in `_save_alignment_as_location()` von `special_notes="Automatisch erfasst via Quick Location Capture."` auf `special_notes=""` (bzw. Feld beim Objekt-Aufbau ganz weglassen, Standardwert der Datenklasse ist bereits `""`) ändern.
- **Betroffene Dateien:** `backend/main.py` (1 Zeile)
- **Vorteile:** Minimalinvasiv, exakt das im Ticket beschriebene Nutzerverhalten, kein neuer Code-Pfad, kein Risiko für bestehende Whitelist/Persistenz-Logik (die durch BUG-50 bereits sauber ist).
- **Nachteile/Risiken:** Falls der Text doch als Herkunfts-Marker gebraucht wurde (Pre-Mortem Szenario 1), geht diese Information ersatzlos verloren — nicht rückgängig machbar für künftige Locations, sobald der Fix aktiv ist (alte Locations bleiben unberührt).
- **Aufwand:** klein

### Option B — Text entfernen + Herkunft in separatem, nicht sichtbarem Feld festhalten

- **Vorgehen:** Wie Option A, zusätzlich ein neues Feld (z. B. `source: "quick_capture"`) am Location-Objekt ergänzen, das nicht im Hinweise-Feld, sondern nur intern/technisch sichtbar ist.
- **Betroffene Dateien:** `backend/main.py`, `backend/data/locations.py` (Datenklasse erweitern), `backend/data/store.py` (neue Spalte/Persistenz), potenziell `web/index.html` falls die Information doch irgendwo angezeigt werden soll.
- **Vorteile:** Kein Informationsverlust — Herkunft bleibt nachvollziehbar, ohne den Nutzer im Hinweise-Feld zu verwirren.
- **Nachteile/Risiken:** Deutlich höherer Aufwand für eine Information, für die aktuell kein bestätigter Bedarf gefunden wurde (siehe ⚠️ Annahme oben); neue Datenbank-Spalte nötig; Scope-Erweiterung gegenüber dem eng gefassten Ticket-Titel.
- **Aufwand:** mittel

✅ **Empfehlung: Option A** — solange Stephan nicht bestätigt, dass die Herkunfts-Information tatsächlich gebraucht wird (Pre-Mortem Szenario 1), ist der 1-Zeilen-Fix die richtige, unaufgeblähte Lösung: Er behebt exakt das gemeldete Problem, ohne Scope Creep, und ist konsistent mit „Feld bleibt leer bis Nutzer selbst etwas einträgt" aus der User Story. Falls Stephan die Nachverfolgbarkeit doch braucht, kann Option B als eigenes, separates Ticket nachgezogen werden.

##### Designer-Check

Übersprungen: Dies ist ein reiner Bugfix ohne neue UI-Elemente, Farben oder Layout-Änderungen (nur eine Werteänderung eines bereits bestehenden Feldes) — der Designer-Check ist damit nicht einschlägig.

##### Scope

**Eingeschlossen:** Hinweise-Feld bleibt bei Quick-Capture-Neuanlage leer, solange der Nutzer nichts einträgt.

**Ausgeschlossen:** Änderungen am Locationscout-Import-Pfad; Herkunfts-Tracking (Option B, nicht gewünscht).

##### Offene Fragen vor Freigabe (durch Stephan geklärt, 2026-07-04)

- ❓ Braucht Stephan die Information „diese Location wurde automatisch per Quick Capture erfasst" an anderer Stelle (z. B. zur Qualitätskontrolle)? → **Nein.**
- ❓ Sollen bestehende Locations mit dem alten Text im Rahmen dieses Tickets bereinigt werden? → **Ja, rückwirkend bereinigen** (damit ins Scope aufgenommen, s. u.).

##### ⛔ Weg-Gate-Entscheidung (2026-07-04)

Freigegeben: **Option A** (Zeile 2065 auf leeren Text ändern) **+ zusätzlich Altbestand-Bereinigung** bestehender Locations, deren `special_notes` **exakt** dem Text „Automatisch erfasst via Quick Location Capture." entspricht (einmaliges Cleanup-Skript, nur bei exaktem Text-Match — keine Locations mit abweichendem/eigenem Text anfassen, damit keine echten Nutzer-Notizen verloren gehen). Betrifft `backend/data/custom_locations.json` (und ggf. `custom_locations.db`, falls die Location-API zusätzlich SQLite nutzt — vom Implementierungs-Subagenten zu prüfen).

Erwartetes Verhalten (Stephan bestätigt): Neue Quick-Capture-Location → Hinweise-Feld leer. Bestehende Locations mit exakt diesem Default-Text → Feld wird einmalig geleert. Alles andere bleibt unverändert.

→ Status: **Ready for Dev**.

##### Testplan

- [ ] **Manuell:** Neue Location per Quick Location Capture anlegen (ohne eigenen Hinweistext einzutragen) → Location öffnen → Hinweise-Feld muss leer sein.
- [ ] **Manuell:** Neue Location per Quick Location Capture anlegen und dabei einen eigenen Hinweistext eintragen → Location öffnen → Feld zeigt exakt den eigenen Text, nichts zusätzlich.
- [ ] **Regression:** Bestehende Standard-Locations mit echten Hinweistexten (z. B. „Bortle-Klasse …") weiterhin unverändert sichtbar.
- [ ] **Regression:** Bearbeiten/Löschen des Hinweisfeldes (BUG-50-Verhalten) weiterhin korrekt — Feld bleibt nach Löschen dauerhaft leer, auch nach Server-Neustart.
- [ ] **Cleanup-Skript:** Nach Ausführung sind alle Locations mit vormals exakt dem Default-Text jetzt leer; Locations mit abweichendem/eigenem Text unverändert.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Akzeptanzkriterien abgeleitet
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert
- [x] Implementierungsoptionen erarbeitet + Empfehlung ausgesprochen
- [x] Weg-Gate von Stephan freigegeben (2026-07-04) — Option A + Altbestand-Bereinigung

##### 🔧 Implementierung (2026-07-04)

- `backend/main.py` Zeile 2065: `special_notes=""` statt hartkodiertem Text (Kommentar `# BUG-60: keine automatische Notiz mehr bei Quick Location Capture` ergänzt).
- Neu: `FotoAlert/tools/cleanup_bug60_special_notes.py` — einmaliges, idempotentes Cleanup-Skript (mit `--dry-run`), bereinigt exakte Treffer des alten Default-Texts sowohl in `backend/data/custom_locations.json` als auch in der SQLite-Tabelle `custom_locations` (`backend/data/fotoalert.db`).
- **Abweichung von der ursprünglichen Spec:** Es gibt keine separate `custom_locations.db` — die Daten liegen zusätzlich zur JSON-Datei in der gemeinsamen `fotoalert.db` (seit TASK-17-Migration). Das Skript deckt beide real existierenden Quellen ab.
- Lokaler Testlauf (Sandbox-Checkout): Dry-run fand 3 Treffer (1× JSON, 2× DB), Live-Lauf hat alle 3 bereinigt, zweiter Lauf meldet 0 Treffer (idempotent bestätigt).
- ⚠️ Vor Ausführung auf dem Prod-Server (Hetzner): prüfen, ob dort dieselbe Datei-Konstellation vorliegt (insbesondere ob dort zusätzlich ein `data_dev`-Pfad existiert) — noch nicht verifiziert.

##### 🧪 Testergebnis (2026-07-04, lokal von Stephan bestätigt)

- **Test 1 (Feld leer bei Neuanlage):** ✅ Direkt über `POST /preview-alignment` (save:true) neue Location angelegt → `special_notes` in der DB exakt `""`.
- **Test 2 (eigener Text bleibt erhalten):** ✅ Per `PATCH /locations/{id}` eigenen Text „Testnotiz BUG-60" gesetzt → exakt so gespeichert, kein zusätzlicher/alter Text.
- **Test 3 (Regression, bestehende Locations mit echtem Hinweistext):** ✅ `stechlin_see` weiterhin mit vollständigem Original-Hinweistext („Bortle-Klasse ~3–4…") unverändert.
- **Test 4 (Regression BUG-50, Feld bleibt nach Löschen + Neustart leer):** ✅ Feld geleert, Server neu gestartet, Feld weiterhin leer.
- **Test 5 (Cleanup-Skript):** ✅ Dry-Run + Live-Lauf lokal ausgeführt, 0 Treffer (Stephans lokaler Datenbestand enthält keine Locations mit dem alten Default-Text — plausibel, echte Bereinigung folgt beim Prod-Release).

**Abweichung vom ursprünglichen Testplan:** Testschritt 2 aus der Spec („mit eigenem Hinweistext anlegen") war so nicht durchführbar — die Anlage-Maske (Quick Location Capture) hat kein Eingabefeld für einen Hinweistext; der Text lässt sich nur nachträglich über „Bearbeiten" eintragen. Ersetzt durch den oben beschriebenen Test 2.

**Bekannter, unabhängiger Blocker für den vollen UI-Klick-Test:** Der eigentliche Klick auf „Speichern" in der Anlage-Maske im Browser hat bei Stephans manuellem Test nicht reagiert (kein Toast, kein Konsolenfehler, aber ein Netzwerk-Request ging raus). Ursache sehr wahrscheinlich Stephans parallele Arbeit an **US-124** (Vollbild-Modus für dieselbe Anlage-Maske) — der lokale Dev-Server liefert dabei einen unfertigen Zwischenstand von `web/index.html` aus. Der identische Backend-Codepfad wurde deshalb direkt per API verifiziert (s. o.) und bestätigt fehlerfrei. **Empfehlung:** den vollen UI-Klick-Durchlauf erneut prüfen, sobald US-124 abgeschlossen/stabil ist — blockiert BUG-60 nicht.

**Von Stephan bestätigt:** „passt" (2026-07-04) — Backend-Verifikation ausreichend, UI-Klick-Test wird nach US-124 nachgeholt. Test-Location (`custom_1783238816`) wurde danach wieder aus der lokalen Datenbank entfernt (bestätigt: `gefunden: []`).

##### ✅ Verifikation (separater Subagent, 2026-07-04)

Code stimmt mit dokumentiertem Testergebnis und AKs überein. Zeile 2065 einziger Schreibort (keine zweite Überschreibung), Cleanup-Skript deckt beide Datenquellen ab, 3.9-kompatibel, idempotent. Keine Code-Stelle erwartet/filtert noch den alten Default-Text. Scope sauber eingehalten (nur die eine Zeile + das neue Cleanup-Skript geändert). Restrisiken: Prod-Cleanup-Lauf steht noch aus (geplant beim Release), UI-Klick-Test steht nach US-124 noch aus — beides bereits oben vermerkt, kein verstecktes Risiko.

##### 🧹 Refactor-Check (2026-07-04)

`tools/refactor_check.py --report` ausgeführt: 1 Finding, aber unrelated zu BUG-60 (`startup()` in `main.py` Zeile 1250, 84 statt max. 80 Zeilen — bestand schon vorher, nicht Teil dieses Tickets). Für die BUG-60-Änderung selbst keine Findings. Namenskonvention, Docstrings, Fehlerbehandlung und Python-3.9-Kompatibilität passen zum Repo-Stil. **Release-Freigabe aus Code-Qualitätssicht: ja.**

##### ⏸️ Release-Gate (2026-07-04) — zurückgestellt

Code ist release-bereit (Verifikation + Refactor-Check bestanden). Release aber bewusst **zurückgestellt**: `git status` zeigt bereits Änderungen an `web/index.html` aus Stephans paralleler Arbeit an der Vollbild-Karten-Funktion (noch ungetestet). `release.sh` committet automatisch immer den kompletten Stand von `web/index.html` + `web/sw.js` — ein Release jetzt würde diesen unfertigen Code ungewollt mit ausliefern. **Entscheidung (Stephan, 2026-07-04):** warten, bis die parallele Arbeit fertig und getestet ist, dann BUG-60 gemeinsam mit dieser Arbeit releasen. Status bleibt `In Test`, kein Deploy bis dahin.

##### ✅ Nachgeholter UI-Klick-Test (2026-07-04)

Der zuvor blockierte UI-Klick-Test wurde nachgeholt, nachdem der Klick auf „Speichern" in der Anlage-Maske diesmal funktionierte: Neue Location „bornstedt test" über die echte Anlage-Maske (Standort+Motiv setzen → Alignments berechnen → Speichern) angelegt, Bestätigung „✅ Location gespeichert!" erschien. Im Detail-Sheet ist das Hinweise-Feld leer (von Stephan bestätigt) — Beschreibung enthält erwartungsgemäß den automatisch generierten Text „Sichtachse auf …", das ist ein separates, gewolltes Feld und nicht Teil von BUG-60. **Alle Testpunkte damit auch über den echten UI-Pfad bestätigt, kein offener Punkt mehr außer dem zurückgestellten Release.**

**Nebenbefund (unabhängig von BUG-60, nicht vertieft):** „Alignments berechnen" wirkte spürbar langsam/blockierend, mit spürbarer Verzögerung auch bei anderen Requests kurz danach — vermutlich rechenintensive, synchrone Schleife (14 Tage × Sonne/Mond) im Request-Handler, die den Server blockiert statt in einem Thread zu laufen. Nicht weiter untersucht (außerhalb Scope), separat per Intake ins Backlog aufgenommen.

Test-Locations „bornstedt test" (`custom_1783243478`, `custom_1783243546` — zwei Einträge, vermutlich durch einen früheren Klick-Versuch, der doch durchging) danach wieder aus der lokalen Datenbank entfernt (bestätigt: `gefunden: []`).

---

### BUG-61 · Motiv-Sektion im Location-Detail zeigt nach Umbenennung weiterhin den alten Motivnamen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-04 |

**Beschreibung:** Im Location-Detail-Sheet zeigt die Sektionsüberschrift „MOTIV – &lt;Name&gt;" nach Umbenennung des Motivs weiterhin den alten Namen (Beispiel: Umbenennung zu „Havelblick von der Wublitzbrücke", angezeigt bleibt „Havelböick von der Wublitzbrücke"). Beobachtet: veraltete, falsche Anzeige trotz erfolgter Umbenennung. Erwartet: Die Sektionsüberschrift zeigt jederzeit den aktuell gespeicherten Motivnamen. Zu prüfen: Ob auch der Beschreibungstext unterhalb dieser Sektion denselben veralteten Namen referenziert.

**Scope-Hinweis (Code-Recherche PM-Intake):** `web/index.html` Zeile 5717 rendert die Sektion als `Motiv – ${loc.subject_name}` direkt aus dem Location-Objekt (`LocationDetail._render`), eine zentrale Datenquelle für diese eine Sektion. `LocationDetail.saveEdit()` (ca. Zeile 5626–5631) lädt nach dem Speichern bereits `Locations.all` neu vom Server und ruft `LocationDetail.open(locId)` erneut auf (Muster aus BUG-30, dort für den Location-Namen gefixt) — trotzdem scheint der Motivname stale zu bleiben, das ist im Kern dieses Bugs zu klären (evtl. anderer Bearbeitungsweg als das Formular, z. B. direkter API-Edit, oder ein separater Cache-Effekt). Zusätzlich verwendet der Chancen-/Feed-/Scout-/Kalender-Datensatz ein **eigenes** `o.subject_name`-Feld (Zeilen 1589, 1877, 1895, 1942), das aus dem Opportunities-Cache (`opportunities.json`/`discover.json`) stammt und unabhängig vom Location-Objekt ist — dort könnte derselbe veraltete Motivname ebenfalls auftauchen, wenn der Cache nach einer Umbenennung nicht neu berechnet wird. Ob das tatsächlich betroffen ist, ist Analysephase-Arbeit, nicht hier entschieden.

**User Story:** Als Nutzer, möchte ich, dass die Motiv-Sektion im Detail-Sheet immer den aktuellen Motivnamen zeigt, sodass ich nicht durch veraltete/falsche Angaben verwirrt werde.

**Bezug:** Keine Dubletten im Backlog gefunden (Grep nach „Motiv", „Detail-Sheet", „stale", „veraltet" ohne Treffer zu diesem Fehlerbild). Architektonisch verwandt: **BUG-47** [x] (Done) — dort war die Ursache fehlendes Re-Render nach State-Änderung (kein reaktives Binding in der App); möglicherweise dieselbe Fehlerklasse, aber nicht zwingend dieselbe Root Cause, muss in der Analyse geprüft werden. **BUG-30** [x] (Done) hat das exakt gleiche Symptom-Muster für den Location-Namen (nicht Motivnamen) bereits gefixt — hier offenbar unvollständig auf `subject_name` übertragen oder ein zusätzlicher Pfad betroffen.

#### 🔬 Analyse & Spec (2026-07-04)

##### Root Cause (verifiziert im Code)

Das Bearbeiten-Formular und der clientseitige Reload-Pfad funktionieren korrekt: Es gibt ein eigenes Eingabefeld für den Motivnamen, es wird beim Speichern mitgesendet, danach lädt die App die komplette Location-Liste neu vom Server und baut das Detail-Sheet komplett neu auf (identischer Mechanismus wie beim bereits gefixten Location-Namen). Der Fehler liegt **nicht** im Frontend.

Die tatsächliche Ursache liegt serverseitig: Der Speicher-Endpunkt für Locations akzeptiert nur eine feste, kleine Liste erlaubter Felder für Text-Änderungen. Der Motivname gehört **nicht** zu dieser Liste. Das bedeutet: Der neue Motivname wird vom Server stillschweigend verworfen, obwohl die App „Speichern erfolgreich" meldet — gespeichert und danach angezeigt wird weiterhin der alte Wert, weil er serverseitig nie aktualisiert wurde. Das erklärt exakt das beobachtete Symptom (stale Name trotz augenscheinlich korrektem Speichervorgang) und warum der BUG-30-Reload-Mechanismus hier nicht greift: Er lädt korrekt neu — aber der neue Wert wurde nie in den Datenbestand geschrieben, es gibt nichts Neues zu laden.

Kein neues 🔴 nötig — Root Cause ist eindeutig lokalisiert.

##### Beispiele (Example Mapping)

**Regel 1: Der Motivname wird beim Speichern serverseitig übernommen.**
- Given eine Location mit Motivname „Havelböick von der Wublitzbrücke", When ich im Bearbeiten-Formular den Motivnamen zu „Havelblick von der Wublitzbrücke" ändere und speichere, Then zeigt die Motiv-Sektionsüberschrift im Detail-Sheet direkt danach „Havelblick von der Wublitzbrücke".
- Given dieselbe Änderung, When ich die App komplett neu lade (nicht nur das Sheet erneut öffnen), Then zeigt die Motiv-Sektion weiterhin den neuen Namen (Beweis, dass er wirklich dauerhaft gespeichert wurde, nicht nur clientseitig zwischengespeichert).

**Regel 2: Der bereits funktionierende Location-Namen-Fix (BUG-30) bleibt unverändert korrekt.**
- Given eine Location, When ich nur den Location-Namen ändere (Motivname unverändert lasse) und speichere, Then zeigt die App überall (Titelzeile, Feed, Suche) sofort den neuen Location-Namen — wie bisher.

**Regel 3 (⚠️ Annahme, aus Scope-Klärung): Der Motivname im Kalender-/Feed-/Scout-Bereich ist nicht Teil dieser Korrektur.**
- Given eine Umbenennung des Motivnamens, When ich in den Kalender-, Feed- oder Scout-Bereich wechsle, Then kann dort weiterhin der alte Motivname stehen (separater Datenbestand, bewusst außerhalb dieses Tickets — möglicher Kandidat für ein Folgeticket).

##### Akzeptanzkriterien

- Wenn ich den Motivnamen einer Location über das Bearbeiten-Formular ändere und speichere, zeigt das Detail-Sheet direkt danach den neuen Motivnamen in der Motiv-Sektionsüberschrift.
- Der neue Motivname bleibt auch nach einem kompletten Neuladen der App sichtbar (er ist also wirklich dauerhaft gespeichert, nicht nur kurzzeitig im Browser sichtbar).
- Das Ändern des Location-Namens (unabhängig vom Motivnamen) funktioniert weiterhin wie bisher zuverlässig sofort überall aktuell.
- Ausdrücklich außerhalb dieses Tickets: Der Motivname, der im Kalender, im Feed oder beim Scouting angezeigt wird, muss durch diese Korrektur nicht aktualisiert werden — das ist ein separater Datenbestand und wird hier bewusst nicht angefasst.

##### Pre-Mortem

1. **Auslöser:** Die Korrektur öffnet serverseitig zu viele Felder für Änderungen und erlaubt dadurch versehentlich auch Felder, die nicht verändert werden sollten (z. B. Felder, die eine aufwendige Neuberechnung anstoßen, obwohl das gar nicht gewollt ist). **Frühwarnung:** Nach der Änderung testweise nur den Motivnamen ändern und prüfen, ob unerwartet eine Neuberechnung angestoßen wird. **Gegenmaßnahme:** Nur den Motivnamen gezielt freischalten, keine pauschale Öffnung der Feld-Liste.
2. **Auslöser:** Die Korrektur bricht versehentlich den bereits funktionierenden Location-Namen-Fix (BUG-30), z. B. weil an derselben Stelle im Code etwas verändert wird. **Frühwarnung:** Regressionstest für den Location-Namen (siehe Testplan) direkt nach der Änderung durchführen. **Gegenmaßnahme:** Änderung so klein wie möglich halten, nur die fehlende Freischaltung ergänzen, nichts Bestehendes umbauen.
3. **Auslöser:** Motivname wird zwar jetzt serverseitig gespeichert, aber ein anderer Cache (z. B. der Bereich, der die Location-Übersicht speist) zeigt trotzdem noch den alten Namen, weil er nicht mit aktualisiert wird. **Frühwarnung:** Nach dem Speichern sowohl das Detail-Sheet als auch die Location-Übersichtsliste prüfen. **Gegenmaßnahme:** Falls das auftritt, denselben Reload-Mechanismus wie beim Detail-Sheet auch dort sicherstellen (im Rahmen dieses Tickets, da noch „Detail-Sheet-Familie").
4. **Auslöser:** Sonderzeichen im Motivnamen (Anführungszeichen, Umlaute) werden beim Speichern verstümmelt. **Frühwarnung:** Test mit einem Motivnamen, der ein Anführungszeichen oder Sonderzeichen enthält. **Gegenmaßnahme:** Bestehende Zeichen-Behandlung (wie beim Location-Namen bereits vorhanden) unverändert mitnutzen.
5. **Auslöser:** Leerer Motivname wird akzeptiert und führt zu einer Sektionsüberschrift ohne Namen („Motiv – "). **Frühwarnung:** Test mit leerem Motivnamen-Feld beim Speichern. **Gegenmaßnahme:** Falls das unschön aussieht, als Hinweis vermerken statt zusätzliche Pflichtfeld-Logik in diesem kleinen Bugfix nachzurüsten (Scope klein halten).

##### Architektur-Analyse

Betroffen: `backend/main.py`, Funktion `patch_location` (PATCH-Endpunkt `/locations/{loc_id}`, ca. Zeile 2169 ff.) — dort fehlt `subject_name` in der Menge der erlaubten Text-Felder (`text_fields`), wodurch das Feld vom serverseitigen Feld-Filter verworfen wird, bevor es überhaupt persistiert oder in den In-Memory-Bestand übernommen wird. Frontend (`web/index.html`, `LocationDetail.saveEdit` / `LocationDetail.open` / `LocationDetail._render`) ist bereits korrekt implementiert und braucht keine Änderung.

##### Designer-Check

Übersprungen — reiner Text-Content-Bugfix ohne visuelle oder Layout-Änderung, bestätigt aus vorherigem Durchlauf.

##### Implementierungsoptionen

**Option A (empfohlen):** Den Motivnamen serverseitig gezielt zur Liste der änderbaren Text-Felder hinzufügen, damit er beim Speichern wie der Location-Name dauerhaft übernommen wird. Betroffene Datei: `backend/main.py`. Vorteil: minimale, gezielte Änderung, exakt die Root Cause behoben, kein Nebenwirkungsrisiko auf andere Felder. Nachteil: keiner ersichtlich. Aufwand: klein.

**Option B:** Serverseitig grundsätzlich alle vom Formular gesendeten Felder akzeptieren (Feld-Filter aufweichen/entfernen). Vorteil: würde auch andere, aktuell möglicherweise ebenfalls verworfene Formularfelder (z. B. Kategorie) beheben. Nachteil: deutlich größerer Eingriff, höheres Risiko für unbeabsichtigte Nebenwirkungen (z. B. unerwünschte Neuberechnungen, Validierungslücken) und Scope-Creep über dieses Ticket hinaus. Aufwand: mittel.

**Empfehlung:** Option A. Sie behebt exakt die im Ticket beschriebene Root Cause mit minimalem, gut nachvollziehbarem Eingriff und ohne Regressionsrisiko für den bereits funktionierenden Location-Namen-Fix. Sollte beim Testen auffallen, dass weitere Formularfelder (z. B. Kategorie) ebenfalls nicht ankommen, ist das ein Kandidat für ein separates Folgeticket, nicht für eine Ausweitung hier.

##### Testplan

**Automatisiert:** `backend/tests/test_bug-61.py` — prüft, dass der Speicher-Endpunkt einen geänderten Motivnamen tatsächlich übernimmt und dass ein alleiniges Ändern des Location-Namens weiterhin wie bisher funktioniert (Regressionsschutz für BUG-30).

**Manuell (Browser):**
1. Location-Detail öffnen, Bearbeiten-Formular öffnen, nur den Motivnamen ändern, speichern. Erwartung: Die Motiv-Sektionsüberschrift im Detail-Sheet zeigt sofort den neuen Namen.
2. App komplett neu laden (nicht nur Sheet erneut öffnen). Erwartung: Der neue Motivname ist weiterhin sichtbar (dauerhaft gespeichert).
3. **Regressionscheck (BUG-30):** Bei derselben oder einer anderen Location nur den Location-Namen ändern und speichern. Erwartung: Der neue Location-Name erscheint sofort überall (Titelzeile, Location-Übersicht, Suche) — wie bisher unverändert funktionierend.
4. Motivname mit Anführungszeichen oder Umlaut testen. Erwartung: Korrekte Darstellung ohne Verstümmelung.

##### Analyse & Planung Checkliste

- [x] Root Cause im Code verifiziert (nicht geraten)
- [x] Example Mapping mit Given/When/Then
- [x] Akzeptanzkriterien aus Nutzersicht
- [x] Pre-Mortem inkl. Regressionsrisiko BUG-30
- [x] Architektur-Analyse mit konkreter Datei/Funktion
- [x] Designer-Check (übersprungen, begründet)
- [x] Mind. 2 Implementierungsoptionen mit Empfehlung
- [x] Testplan (automatisiert + manuell) inkl. Regressionscheck
- [x] Scope-Ausschluss Kalender/Feed/Scout-Motivname dokumentiert

---

## 🔴 Hoch – Kern-Features


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

### US-38 · Observability & Self-Healing

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Status** | In Analysis |

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

#### 🔬 Analyse & Spec (2026-06-23)

##### Ist-Stand (Code-Analyse)

Der `/health`-Endpoint (`main.py:809`) gibt aktuell nur `{status, version, locations_count}` zurück — kein Cache-Alter, kein Job-Status, keine Wetter-API-Info. Das `HealthOut`-Schema (`models/schemas.py:92`) hat entsprechend nur 3 Felder.

Es existiert bereits ein rudimentäres Job-Tracking-System (`main.py:222–248`): `_job_status`-Dict mit 3 Jobs (`weather`, `feed`, `calendar`), je `{status, last_run, last_error, duration_s}`. Die Helfer `_job_start()`, `_job_done()`, `_job_error()` werden in `_run_precompute()` und `_weather_overlay()` bereits aufgerufen. Die Jobs laufen via APScheduler (cron: 05:30, 05:45, alle 3h).

US-34 (`backup.py`) liefert bereits `hours_since_last_backup()` als Health-Signal. Es fehlt nur die Anbindung an `/health`.

**Bestehende Infrastruktur, die US-38 nutzen kann:**
- `_job_status` (in-memory, 3 Jobs) → erweitern um `discover` + `backup`
- APScheduler-Instanz `scheduler` → Job-History darüber abfragbar
- Standard-Python-`logging` mit `logger = logging.getLogger(__name__)` — kein strukturiertes Format
- `backup.hours_since_last_backup()` aus US-34

---

##### Example Mapping

**AK 1: `/health` zeigt Status aller Subsysteme**

| Typ | Szenario | Erwartetes Ergebnis |
|-----|----------|---------------------|
| ✅ Positiv | App läuft normal, Cache < 24h alt, Weather-Job lief vor 2h erfolgreich | `/health` → `200 OK`, alle Subsysteme `"ok"` |
| ❌ Negativ | Wetter-API seit 12h nicht erreichbar, weather-Job im Status `"error"` | `/health` → `200 OK` (App läuft), aber `subsystems.weather.status = "error"` mit `last_error`-Details |
| ⚠️ Edge | Erststart ohne Cache (leer), precompute läuft gerade | `subsystems.cache.status = "building"`, `subsystems.feed.status = "running"`, Backend-Status `"degraded"` statt `"ok"` |

**AK 2: Strukturiertes Logging**

| Typ | Szenario | Erwartetes Ergebnis |
|-----|----------|---------------------|
| ✅ Positiv | `_weather_overlay()` startet und endet erfolgreich | Log-Einträge `{"ts": "...", "job": "weather", "event": "start"}` und `{..., "event": "done", "duration_s": 4.2, "status": "ok"}` |
| ❌ Negativ | open-meteo antwortet mit Timeout nach 30s | `{..., "event": "error", "error_class": "Timeout", "error_msg": "...", "duration_s": 30.1}` |
| ⚠️ Edge | Logging-Format-Fehler (zirkuläre Referenz im dict) | Fallback auf plain-text-Logging, kein Crash; Fehler selbst wird geloggt |

**AK 3: Automatische Fehlerklassifizierung**

| Typ | Szenario | Erwartetes Ergebnis |
|-----|----------|---------------------|
| ✅ Positiv | `precompute.py` beendet sich mit `exit 1` wegen korrupter JSON-Datei | Fehler-Klasse `"DataError"`, `last_error` = erste Zeile stderr |
| ❌ Negativ | Unbekannter Exception-Typ, keiner der Classifier greift | Fehler-Klasse `"Unknown"`, rohe Exception-Message gespeichert |
| ⚠️ Edge | subprocess.py returncode=0, aber JSON-Datei danach leer (silent failure) | Nach Cache-Reload: `len(_feed_cache) == 0` → nachgelagerte Klassifizierung als `"DataError"` |

**AK 4: Automatisch generierter Lösungsvorschlag**

| Typ | Szenario | Erwartetes Ergebnis |
|-----|----------|---------------------|
| ✅ Positiv | Wetter-Job schlägt mit `ConnectionError` fehl | Generiert Spec: `{error_class: "APIError", files: ["backend/calculations/weather.py"], suggestion: "open-meteo nicht erreichbar — Retry-Logik oder API-Fallback prüfen"}` |
| ❌ Negativ | Fehler-Klasse `"Unknown"` ohne Muster | Spec: `{suggestion: "Fehler nicht klassifizierbar — bitte Log manuell prüfen"}`, kein False-Positive |
| ⚠️ Edge | Zwei Jobs gleichzeitig fehlerhaft | Je ein Spec-Objekt pro Job — kein gemeinsames, um Verwechslung zu vermeiden |

**AK 5: Alert-Mechanismus**

| Typ | Szenario | Erwartetes Ergebnis |
|-----|----------|---------------------|
| ✅ Positiv | precompute schlägt fehl → `_job_error()` aufgerufen | `logger.error(...)` mit strukturiertem JSON-Block, Severity `CRITICAL`; optional E-Mail via SMTP |
| ❌ Negativ | SMTP nicht konfiguriert (kein `FOTOALERT_ALERT_EMAIL` in env) | Nur Log-Eintrag, kein Absturz; E-Mail still übersprungen |
| ⚠️ Edge | Alert-Flut: derselbe Job schlägt 5× in Folge fehl | Debounce: Alert nur beim ersten Fehler, danach frühestens nach 1h |

**AK 6: Dashboard / CLI-Übersicht (7 Tage)**

| Typ | Szenario | Erwartetes Ergebnis |
|-----|----------|---------------------|
| ✅ Positiv | `python3 tools/job_history.py` aufgerufen, 3 Fehler in 7 Tagen | Tabellarische Ausgabe: Job, Zeitstempel, Dauer, Status, Fehlerklasse |
| ❌ Negativ | Log-Datei nicht vorhanden oder leer | Klare Fehlermeldung: `"Keine Job-History-Daten gefunden"`, exit 1 |
| ⚠️ Edge | Log enthält >10.000 Zeilen (alte Installation) | Parst nur letzte 7 Tage effizient (kein volles Einlesen), < 1s |

---

##### Pre-Mortem: Was kann schiefgehen?

1. **In-Memory-Verlust:** `_job_status` lebt nur im Prozess. Nach `systemctl restart fotoalert` ist die History weg — das 7-Tage-Dashboard wäre leer. → Lösung: Job-Events in SQLite oder strukturiertes Log-File persistieren.

2. **_weather_overlay silent failure:** Wenn open-meteo für eine Location 404 zurückgibt, wird `logger.warning(...)` aufgerufen aber `_job_error()` nicht — der Job landet als `"done"` obwohl Wetter-Daten fehlen. → Braucht explizite Fehler-Propagierung auch bei Teil-Fehlern.

3. **`discover`-Job nicht im `_job_status`-Dict:** `_refresh_discover()` ruft `_job_start()`/`_job_done()` nicht auf — der Scout-Job ist komplett unsichtbar. → Muss nachgezogen werden.

4. **Backup-Signal fehlt:** `backup.hours_since_last_backup()` existiert, aber `/health` kennt es nicht. US-34-AK ist damit technisch unerfüllt.

5. **Debounce-Pflicht fehlt:** Ohne Throttle bei persistentem Fehler (z.B. open-meteo down für 6h = 2 Alerts/h) entsteht eine Alert-Flut ins Log.

6. **Lösungsvorschlag-Halluzination:** Automatisch generierte Specs müssen konservativ und template-basiert sein — kein LLM-Call, da offline. Gefahr: zu generische Vorschläge, die mehr verwirren als helfen.

7. **Python 3.9-Kompatibilität:** `str | None` im neuen Code verboten (Server läuft 3.9). Alle Type Hints als `Optional[str]` oder `Union[str, None]` schreiben.

---

##### Implementierungsoptionen

**Option A — Minimale Erweiterung (in-process, kein neues File)**
- `/health` um `_job_status`, `_cache_loaded_at`, `_weather_updated_at`, `backup.hours_since_last_backup()` erweitern
- `HealthOut`-Schema um `subsystems: dict` erweitern
- Job-Events strukturiert per `logger.info(json.dumps({...}))` loggen
- `discover`-Job in `_job_status` einpflegen
- Alert: `logger.critical(...)` bei `_job_error()` + optionales SMTP (env-gesteuert)
- CLI-Tool `tools/job_history.py`: parst Server-Log (grep + JSON-Linien), zeigt 7-Tage-Tabelle
- Lösungsvorschläge: statische Regel-Tabelle `{error_class → files + suggestion}`

**Betroffene Dateien:** `backend/main.py`, `backend/models/schemas.py`, `backend/data/backup.py` (Signal-Anbindung), neu: `backend/observability.py` (Klassifizierer + Spec-Generator), `tools/job_history.py`

**Option B — SQLite-basierte Job-History + erweitertes Dashboard**
- Alle Job-Events in eigene SQLite-Tabelle `job_runs` schreiben (Timestamp, Job, Status, Duration, ErrorClass, ErrorMsg)
- `/health` liest aus DB statt aus in-memory Dict
- Dashboard-Endpoint `/health/history?days=7` als REST-API (kein extra CLI-Script nötig)
- Alert-Debounce ebenfalls in DB (letzte Alert-Zeit pro Job)

**Betroffene Dateien:** zusätzlich `backend/store.py` (DB-Schema erweitern), `backend/main.py` (DB-Writes bei Job-Events)

**Option C — Externe Lösung (Prometheus/Grafana oder Sentry)**
- Job-Metriken via `prometheus_client` exportieren, Grafana-Dashboard
- Fehler-Alerting via Sentry SDK (`.capture_exception()`)
- Kein eigener Alert-Code

**Betroffene Dateien:** `requirements.txt`, `backend/main.py`, `deploy/` (Prometheus-Scrape-Config)

---

##### Empfehlung: Option A + SQLite-Persistenz (Hybrid)

**Option A** für den Health-Endpoint, Logging und Lösungsvorschläge (minimal-invasiv, in bestehende Patterns passend). **Plus:** Job-Events zusätzlich in die bestehende SQLite (`store.py`) schreiben — eine neue Tabelle `job_runs` mit max. 30 Tagen Retention — damit das 7-Tage-Dashboard nach Restarts nicht leer ist. Das CLI-Tool `tools/job_history.py` liest aus SQLite statt aus dem Log.

Option B (reine DB) ist überengineered für einen Single-Host-Setup. Option C (externe Tools) ist komplett außerhalb des Projekt-Stacks und bringt Betriebskomplexität.

---

##### Implementation Spec

**Schritt 1 — `_job_status` vervollständigen (`main.py`)**
- Job `"discover"` hinzufügen
- `_run_precompute_single()` mit `_job_start()`/`_job_done()`/`_job_error()` ausstatten (aktuell ohne Tracking)
- In `_weather_overlay()`: Teil-Fehler (einzelne Location) zählen; wenn >50% Locations scheitern → `_job_error()` statt `_job_done()`

**Schritt 2 — SQLite-Tabelle `job_runs` (`store.py`)**
```sql
CREATE TABLE IF NOT EXISTS job_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,          -- ISO-8601 UTC
  job TEXT NOT NULL,         -- "weather" | "feed" | "calendar" | "discover" | "backup"
  status TEXT NOT NULL,      -- "done" | "error"
  duration_s REAL,
  error_class TEXT,          -- "Timeout" | "APIError" | "DataError" | "Unknown" | NULL
  error_msg TEXT,
  spec_suggestion TEXT       -- auto-generierter Lösungsvorschlag | NULL
);
```
Retention: `DELETE FROM job_runs WHERE ts < datetime('now', '-30 days')` bei jedem Insert.

**Schritt 3 — Fehlerklassifizierer (`backend/observability.py`, neu)**
```python
# Python 3.9-kompatibel
from typing import Optional, Tuple

ERROR_RULES = [
    (("timeout", "timed out"), "Timeout",
     ["backend/calculations/weather.py"], "Timeout bei API-Call — Retry-Logik oder Timeout-Wert erhöhen"),
    (("connectionerror", "connection refused", "name or service not known"), "APIError",
     ["backend/calculations/weather.py"], "API nicht erreichbar — Netzwerk oder API-Status prüfen"),
    (("json", "decode", "corrupt", "invalid"), "DataError",
     ["backend/precompute.py", "backend/main.py"], "Cache-Datei korrupt — Cache löschen und Neuberechnung starten"),
    (("exit 1", "exit 2", "returncode"), "SubprocessError",
     ["backend/precompute.py"], "precompute.py Fehler — stdout-Log prüfen"),
]

def classify_error(msg: str) -> Tuple[str, list, str]:
    """Gibt (error_class, betroffene_files, suggestion) zurück."""
    lower = msg.lower()
    for keywords, cls, files, suggestion in ERROR_RULES:
        if any(k in lower for k in keywords):
            return cls, files, suggestion
    return "Unknown", [], "Fehler nicht klassifizierbar — bitte Log manuell prüfen"
```

**Schritt 4 — `_job_done()` / `_job_error()` erweitern (`main.py`)**
- Bei `_job_error()`: `classify_error(msg)` aufrufen, Ergebnis in `_job_status[job]["error_class"]` und `_job_status[job]["spec"]` speichern; DB-Write in `job_runs`; `logger.critical(json.dumps({...}))` (strukturiert)
- Alert-Debounce: `_last_alert: dict[str, datetime]` in-memory; Alert nur wenn `now - _last_alert[job] > timedelta(hours=1)`
- Bei `_job_done()`: DB-Write in `job_runs` (kein Alert, kein Spec)

**Schritt 5 — `/health`-Endpoint erweitern (`main.py` + `models/schemas.py`)**

Neues `HealthOut`-Schema (Python 3.9-kompatibel):
```python
from typing import Optional, Dict, Any
class JobStatus(BaseModel):
    status: str
    last_run: Optional[str]
    duration_s: Optional[float]
    last_error: Optional[str]
    error_class: Optional[str]
    spec: Optional[Dict[str, Any]]

class SubsystemStatus(BaseModel):
    backend: str
    cache: str
    cache_age_h: Optional[float]
    weather: str
    weather_age_h: Optional[float]
    backup: str
    backup_age_h: Optional[float]

class HealthOut(BaseModel):
    status: str          # "ok" | "degraded" | "error"
    version: str
    locations_count: int
    subsystems: SubsystemStatus
    jobs: Dict[str, JobStatus]
    precompute_running: bool
```

`/health`-Handler berechnet `status = "degraded"` wenn irgendein Job-Status `"error"` ist.

**Schritt 6 — CLI-Tool `tools/job_history.py`**
```
python3 tools/job_history.py [--days 7] [--job weather] [--errors-only]
```
Liest aus SQLite `job_runs`, gibt Tabelle aus. Keine externen Dependencies (nur `sqlite3`, `datetime`, `argparse`).

**Schritt 7 — Alert via E-Mail (optional, env-gesteuert)**
```
FOTOALERT_ALERT_EMAIL=stephanschumann@me.com
FOTOALERT_SMTP_HOST=smtp.icloud.com
FOTOALERT_SMTP_PORT=587
FOTOALERT_SMTP_USER=...
FOTOALERT_SMTP_PASS=...
```
Nur wenn `FOTOALERT_ALERT_EMAIL` gesetzt; sonst nur `logger.critical(...)`.

---

##### Abgrenzung zu anderen Tickets

- **US-34 (Backup):** `backup.hours_since_last_backup()` wird von US-38 im `/health`-Endpoint konsumiert. US-34 implementiert es, US-38 nutzt es. Kein Merge nötig.
- **US-37 (PWA-Refresh):** Job-Status-Anzeige im Frontend liest `_job_status` — das ist dasselbe Dict, das US-38 befüllt. Koordination: US-38 stellt sicher, dass `_job_status` vollständig und zuverlässig ist; US-37 zeigt es an.
- **TASK-14 (Deploy):** `/health`-Retry-Check im Deploy-Script nutzt bereits den Endpoint. US-38 macht ihn aussagekräftiger — kein Breaking Change, nur Felder hinzugefügt.

##### Status
- **Analyse:** ✅ fertig 2026-06-23
- **Empfehlung:** Option A + SQLite-Persistenz (Hybrid)
- **Wartet am Weg-Gate:** Freigabe durch Stephan vor Implementierung

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

### US-64 · Live Astro-Visualisierung (PhotoPills-like) `[ ]`
> **Als Fotograf** möchte ich in Echtzeit sehen, wo sich Sonne und Mond am Himmel befinden, und diese Position relativ zu meinem Fotostandort und Motiv visualisiert bekommen.
>
> **Hintergrund:** FotoAlert hat Skyfield-Engine und Location-Paare. Diese Story ergänzt einen Live-Modus der die aktuelle Himmelsposition anzeigt und mit Locationdaten überlagert.
>
> **Architektur (2026-06-25 geklärt):** Berechnung **clientseitig in JS**, NICHT als Backend-Endpoint. Himmelspositionen (Sonne/Mond/Milchstraßenzentrum) sind eine geschlossene Formel (Meeus), kein Solver — Az/Höhe für einen Zeitpunkt < 1 ms, eine Tagesbahn < 10 ms. Nur clientseitig fühlt sich das Pin-Ziehen/Zeit-Scrubben echtzeit an (kein Roundtrip). Bibliothek: **Astronomy Engine** (MIT, eine Datei, Sonne/Mond/Planeten + freie Sternkoordinaten für das Galaktische Zentrum). Precompute (`/astro/live`) wird damit **gestrichen** — das war der falsche Reflex aus dem Feed-Ranking-Kontext. Funktionierender Spike: `FotoAlert/prototypes/astro-live-prototype.html` (Leaflet + Astronomy Engine, Pin draggable, Zeit-Slider, Richtungslinien Sonne/Mond/MW).
>
> **Akzeptanzkriterien:**
> - Himmelspositionen (Azimut + Höhe Sonne, Mond, Milchstraßenzentrum) werden **clientseitig** für den gewählten Zeitpunkt berechnet — kein neuer Backend-Endpoint
> - Frontend: Fotograf-Pin + Motiv-Pin auf Karte (aus Location-Daten); visuelle Bogenbahn Sonne/Mond überlagert
> - **Richtungslinien auf der Karte:** vom Fotostandort ausgehende geodätische Linien entlang des Azimuts je Himmelskörper — aktuelle Richtung (dick) + Auf-/Untergangsrichtung (dünn); unter Horizont gedämpft/gestrichelt
> - Live-Modus: automatische Aktualisierung; Uhrzeit-Slider zum Scrubben durch den Tag
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

---

#### 📋 Analyse-Spec (2026-06-25)

**Geklärte Scope-Entscheidungen (Example-Mapping-Forks):**
- **Verortung/Pin:** Hybrid — Live-Modus öffnet aus einer gespeicherten Location (Standort+Motiv vorbefüllt), **beide Pins frei ziehbar**, Linien aktualisieren live.
- **Bahn-Darstellung:** Richtungslinien (aktuell + Auf-/Untergang) **plus voller Tagesbogen** (Azimut-Fächer über den Tag).
- **Körper v1:** Sonne, Mond, Milchstraßenzentrum (Planeten später).

**Scope:**
Eingeschlossen: clientseitige Live-Astro-Kartenansicht (`web/index.html`), geöffnet aus dem Location-Detail; Astronomy-Engine-JS; draggable Fotograf-/Motiv-Pins; Richtungslinien + Tagesbogen; Zeit-Slider + Live-Toggle; Readout (Az/Höhe/Mondphase); Sichtachsen-Linie + grüner Alignment-Indikator.
Ausgeschlossen: Backend-Endpoint (`/astro/live` gestrichen), iOS-App, AR/Exif, Planeten, Wetter-Overlay.

**Akzeptanzkriterien:**
- [ ] Astronomy Engine (`astronomy.browser.min.js`, gepinnte Version) eingebunden; globales `Astronomy` verfügbar; keine Backend-Route neu
- [ ] Button im Location-Detail öffnet Live-Astro-Ansicht, zentriert auf `observer_lat/lon`, mit Fotograf-Tropfen (observer) + Motiv-Kreuz (subject) aus Location-Daten
- [ ] Beide Pins draggable; Ziehen aktualisiert Linien + Readout in < 50 ms ohne Server-Call
- [ ] Pro Körper eine dicke Richtungslinie (aktueller Azimut) ab Fotograf-Pin; transparent/gestrichelt wenn Höhe < 0°
- [ ] Dünne Auf-/Untergangslinien für Sonne und Mond (Azimut bei Rise/Set)
- [ ] Voller Tagesbogen: Azimut-Fächer der Sonne (Stützpunkte ~alle 10 min); nur Segmente mit Höhe ≥ 0° gezeichnet
- [ ] Uhrzeit-Slider (0–1439 min) scrubbt durch den Tag (Berlin-Lokalzeit); Live-Toggle setzt auf jetzt + Auto-Update; Scrubben deaktiviert Live
- [ ] Readout: Azimut + Höhe je Körper, Mondphase in %
- [ ] Sichtachse Fotograf→Motiv als eigene Linie; **grüner** Alignment-Indikator wenn `|Az_Körper − Az_Sichtachse| ≤ 2°` (zirkuläre Differenz) UND Körper über Horizont
- [ ] Edge Case: Sichtachse/Range mit Wrap über 0°/360° (z.B. 350°→20°) korrekt
- [ ] Edge Case: Körper ganztägig unter Horizont (MW-Zentrum im Winter) → keine dicke Linie, Readout „nicht sichtbar"
- [ ] Edge Case: Mond ohne Auf-/Untergang am Tag (zirkumpolar) → Rise/Set-Linie entfällt sauber
- [ ] Live-Ansicht schließen → Timer gestoppt (kein Interval-Leak)

**Pre-Mortem:**
- 💀 Client (Astronomy Engine) ≠ Backend (Skyfield): Live-Linie und Detail-Sektion „🧭 Himmelsposition" widersprechen sich. → **Gegenmaßnahme:** Konsistenz-Test ±0.5° gegen bekannten Skyfield-Wert; denselben Wert nicht doppelt aus zwei Engines nebeneinander zeigen.
- 💀 Azimut-Wrap: Sichtachse 355°, Sonne 5° → naive Differenz 350° → Alignment nie grün. → **Gegenmaßnahme:** zirkuläre Differenz `((a−b+540)%360)−180`; Test mit Wrap-Fall.
- 💀 Tagesbogen zeichnet Stützpunkte unter Horizont → Linien „durch den Boden". → **Gegenmaßnahme:** nur Segmente mit Höhe ≥ 0°; Test über Segment-Anzahl.
- 💀 Live-Timer überschreibt manuelles Scrubben. → **Gegenmaßnahme:** Scrubben schaltet Live aus; Lifecycle clearInterval beim Schließen.
- 💀 Zweite Leaflet-Instanz rendert leer, weil Container beim Öffnen 0 px hoch ist. → **Gegenmaßnahme:** `invalidateSize()` nach Anzeige; vgl. Memory `reference_frontend_dom_gotchas`.

📎 **Code-Verifikation** (gelesen 2026-06-25): Bestätigt — Leaflet 1.9.4 geladen, **keine** Astro-Lib (`web/index.html:939`); `MapView`/`#map` (Z.3161); `MapMarkers` observer/subject inkl. draggable (Z.3098–3140); `/locations` liefert `observer_lat/lon`, `subject_lat/lon`, `ideal_azimuth_range`, `possible_bodies` (`main.py:174,739–749`); Geodäsie-Vorbild `destination_point` (`moon_pipeline.py:135`). Backend = Skyfield.

**Architektur:**
- Betroffen: nur `web/index.html` — neue gekapselte Komponente `AstroLive`, Script-Tag astronomy-engine, Einstiegs-Button im `LocationDetail`. **Kein Backend.**
- Wiederverwenden: `MapMarkers.observerDraggable/subjectDraggable`, `edit-mini-map`-Muster (eigene Leaflet-Instanz mit Lifecycle), Geodäsie-Port aus dem Prototyp `prototypes/astro-live-prototype.html`.
- `MapView` (BUG-23-Filterlogik) bleibt unangetastet.

**Implementierungsoptionen:**

*Option A — In bestehenden Karten-Tab (`MapView`) integrieren.* Live-Modus blendet alle Standort-Marker aus und Pins+Linien ein.
- Vorteil: eine Map-Instanz, Layer-Umschaltung vorhanden.
- Nachteil: Eingriff in MapView-Filter-/Marker-Lifecycle → Regressionsrisiko (BUG-23); Modus-State. Aufwand: mittel.

*Option B — Dedizierte `AstroLive`-Ansicht mit eigener Leaflet-Instanz* (Vorbild `edit-mini-map`), geöffnet aus dem Location-Detail.
- Vorteil: saubere Kapselung, eigener Lifecycle (init/destroy, Live-Timer, Slider), kein Eingriff in MapView → kein Regressionsrisiko; gut testbar.
- Nachteil: zweite Map-Instanz (Speicher), minimale Tile-Layer-Duplizierung. Aufwand: mittel.

✅ **Empfehlung: Option B** — Kapselung gewinnt: der Live-Layer hat eigenen Timer-/Slider-Lifecycle und darf die bestehende Marker-Filterlogik nicht anfassen; `edit-mini-map` zeigt das Muster bereits.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (3 Forks geklärt)
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` (AstroLive, LocationDetail-Button), kein Backend
- [x] Implementierungsoptionen: A (in MapView) / B (dedizierte Ansicht)
- [x] Empfehlung: **Option B** — ✅ vom Stephan freigegeben (2026-06-25), Implementierung gestartet

**Testplan:**
- [ ] Automatisiert (`backend/tests/`): Konsistenz-Anker Astronomy-Engine ↔ Skyfield für bekannte Location/Zeit (±0.5°); Unit für zirkuläre Azimut-Differenz.
- [ ] Manuell (`http://localhost:8000`): Location → Live-Astro öffnen; Pins ziehen; Slider scrubben; Wrap-Location; MW-Winter-Fall (keine Linie); Ansicht schließen (Timer-Stopp).

---

### US-72 · Wetterkarte `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **Abgeschlossen** | 2026-07-01 |

**Beschreibung:** Als Fotograf möchte ich eine Wetterkarte für Berlin/Potsdam/Umland sehen, um Wolkendecke und Niederschlag für meine geplanten Shooting-Fenster visuell einschätzen zu können.

---

**Annahmen (autonomer Lauf, ohne Rückfrage getroffen):**
- A1: „Wetterkarte" = ein zuschaltbares **Overlay auf der bestehenden Leaflet-Karte** im Map-Tab (`MapView`), kein neuer Tab. Begründung: Beschreibung sagt „eine Wetterkarte … sehen", Map-Tab hat bereits Leaflet + Layer-Buttons (`web/index.html` Z. 767–774, `MapView` Z. 3034–3166).
- A2: Open-Meteo liefert **Punkt-Vorhersagen, keine Bild-Tiles**. Eine echte flächige „Wetterkarte" wird daher als **Grid aus Punkt-Forecasts** gerendert (farbcodierte Zellen/Kreise), nicht als externe Radar-Tile. Begründung: kein Lizenzrisiko (US-74), bleibt bei der bewährten Open-Meteo-Quelle, kein neuer Provider/Key.
- A3: Scope = ganz Deutschland. Feste Bounding Box: 47.3°N–55.0°N, 6.0°E–15.0°E. Auflösung: **10×10 = 100 Punkte**, Punktabstand ~90 km — Open-Meteo erlaubt Komma-getrennte Multi-Punkt-Abfrage in **einem** Request.
- A4: „geplante Shooting-Fenster" = ein **Zeit-Slider/Stundenwahl** (jetzt + nächste Stunden/Tage), der das Overlay auf die gewählte Stunde umschaltet. Phase 1: stündliche Schritte bis T+3 Tage (deckt sich mit bestehendem Wetter-Overlay-Horizont).
- A5: Zwei umschaltbare Layer: **Wolkendecke (%)** und **Niederschlag** — getrennt, nicht überlagert (Lesbarkeit). Der Niederschlag-Layer hat zwei wechselbare Sub-Optionen: **mm (Menge)** und **% (Wahrscheinlichkeit)**; beide Einheiten sind separat wählbar.

**Example Mapping:**

📏 **Rule 1 — Das Overlay zeigt flächige Wetterinformation für die gewählte Stunde.**
Kontext: Der Fotograf will *visuell* einschätzen, wo es aufreißt. Eine Zahl pro Location reicht nicht; er braucht das räumliche Muster (Westen klar, Osten zu).
- 🟢 Positiv: Given Map-Tab offen + Wetter-Layer „Wolken" aktiv, When Stunde = heute 19:00, Then erscheint über Berlin/Potsdam ein Raster farbiger Zellen (0 % = klar/transparent-blau → 100 % = grau/deckend), und ein nördlich klares Feld ist sichtbar heller als ein südlich bedecktes.
- 🔴 Negativ: Given Wetter-Layer aus, When Map-Tab offen, Then keine Wetterzellen sichtbar, die normale Karte (Marker, Tiles) ist unverändert und nicht eingefärbt.
- ⚠️ Edge: Given Open-Meteo liefert für einen Grid-Punkt `null`/Fehler, When Overlay rendert, Then diese Zelle wird ausgelassen (nicht als „0 % klar" fehlgefärbt) und der Rest rendert weiter.

📏 **Rule 2 — Wolkendecke und Niederschlag sind getrennt wählbar.**
Kontext: Wolken und Regen beantworten verschiedene Fragen (Licht vs. Nass-werden). Übereinander wären beide unlesbar.
- 🟢 Positiv: Given Wolken-Layer aktiv, When Nutzer tippt „Niederschlag", Then verschwindet die Wolken-Einfärbung und der Niederschlag-Layer erscheint (Standard-Sub-Option: mm, blau); nur ein Wetter-Layer gleichzeitig. When Nutzer wechselt Sub-Option auf „%", Then zeigt die Karte die Wahrscheinlichkeitsskala statt der Menge — ohne neuen Backend-Call.
- 🔴 Negativ: Given Niederschlag-Layer aktiv, When Nutzer wechselt Karten-Basis (Standard/Satellit/Nacht), Then bleibt der Niederschlag-Layer aktiv und liegt korrekt über der neuen Basis (Overlay überlebt Basis-Wechsel).
- ⚠️ Edge: Given keine Stunde im Niederschlag > 0, When Layer rendert, Then alle Zellen transparent/„trocken" — kein Fehler, Legende zeigt 0 mm.

📏 **Rule 3 — Der Zeitbezug ist explizit und auf das Shooting-Fenster steuerbar.**
Kontext: Wetter um 14:00 ist für eine Sonnenuntergangs-Session irrelevant. Die Karte muss die *richtige* Stunde zeigen.
- 🟢 Positiv: Given Slider auf „morgen 21:00", When Overlay aktiv, Then zeigen alle Zellen die Vorhersage für morgen 21:00 (Ortszeit Berlin angezeigt; intern UTC — siehe Memory `shoot_time_utc`), und ein Zeit-Label nennt „Mo 21:00".
- ⚠️ Edge: Given Slider über T+3 Tage hinaus, When Nutzer schiebt, Then ist der Slider bei T+3 hart begrenzt (über diesen Horizont wird kein Overlay geladen — konsistent mit dem bestehenden 3-Tage-Wetterfenster).

📏 **Rule 4 — Daten werden gecacht, nicht bei jedem Stunden-Wechsel neu geholt.**
Kontext: Der Slider triggert sonst pro Tick einen API-Call → Open-Meteo-Rate-Limit + Lag. Ein Grid-Forecast deckt alle Stunden ab.
- 🟢 Positiv: Given Overlay erstmals aktiviert, When es lädt, Then **ein** Multi-Punkt-Request über alle Grid-Punkte für den gesamten 3-Tage-Horizont; danach wechselt der Slider rein clientseitig zwischen Stunden ohne neuen Call.
- ⚠️ Edge: Given Cache älter als TTL (z. B. 60 min), When Overlay erneut geöffnet, Then Refetch; sonst Cache-Hit.

✅ Questions (alle durch Stephan entschieden): Grid 10×10 = 100 Punkte (~90 km Abstand), Abdeckung ganz Deutschland (47.3°N–55.0°N, 6.0°E–15.0°E), Niederschlag als mm UND % (wechselbare Sub-Optionen), Option A (Open-Meteo Multi-Punkt). Keine offenen Fragen mehr.

**Scope:**
- Eingeschlossen: zuschaltbares Wetter-Overlay im Map-Tab (`MapView`), zwei Wetter-Layer (Wolkendecke %, Niederschlag mit Sub-Optionen mm/%), Zeit-Slider bis T+3, Grid-Forecast 10×10=100 Punkte (Deutschland-BBox 47.3°N–55.0°N, 6.0°E–15.0°E) via Open-Meteo Multi-Punkt in einem Request, Backend-Endpoint mit Cache + Legende + Lade-/Fehlerzustand.
- Ausgeschlossen: animierte Radar-Loop, externe Radar-Tile-Provider (Lizenzrisiko, US-74), Push-Benachrichtigung bei Wetteränderung, iOS-App (`ios/`), Auflösung > T+3 Tage, Überlagerung beider Wetter-Layer gleichzeitig.

**Akzeptanzkriterien:**
- [ ] Neuer Endpoint `GET /weather-map?hours=72` liefert JSON `{ "grid": [{"lat","lon"}...], "hourly_times": [...iso UTC...], "cloud_cover": [[pro-Punkt-pro-Stunde]], "precipitation_mm": [[...]], "precipitation_prob": [[...]], "fetched_at": iso }` für das Deutschland-Grid (BBox 47.3°N–55.0°N, 6.0°E–15.0°E); Statuscode 200; `len(grid) == 100` (10×10); jede Wertereihe gleich lang wie `hourly_times`.
- [ ] Edge: Wenn ein einzelner Grid-Punkt von Open-Meteo fehlt/`null` liefert, enthält die Antwort für diesen Punkt `null`-Werte (kein 500, kein 0-Wert) und die übrigen Punkte sind vollständig.
- [ ] Endpoint cached das Ergebnis im Prozess (TTL 60 min); zweiter Aufruf innerhalb TTL macht **keinen** neuen Open-Meteo-Call (verifizierbar via `fetched_at` unverändert).
- [ ] Frontend: Im Map-Tab existiert ein Wetter-Toggle mit zwei Optionen „Wolken" / „Niederschlag" + „aus" (Default aus); aktivieren zeichnet ein farbcodiertes Grid-Overlay über die Leaflet-Karte. Bei aktivem Niederschlag-Layer ist eine Sub-Option „mm" / „%" wählbar; Wechsel zwischen beiden erfolgt rein clientseitig ohne neuen Backend-Call.
- [ ] Frontend: Ein Zeit-Slider/Selector schaltet die angezeigte Stunde um (Schritt = 1 h, Bereich jetzt…T+3); Label zeigt Berliner Ortszeit; Stundenwechsel löst **keinen** neuen Backend-Call aus (rein clientseitiges Re-Render aus geladenem Datensatz).
- [ ] Nur ein Wetter-Layer gleichzeitig sichtbar; Wechsel der Karten-Basis (Standard/Satellit/Nacht via `MapView.setLayer`) lässt das aktive Wetter-Overlay erhalten und korrekt darüber liegen.
- [ ] Edge: Open-Meteo komplett nicht erreichbar → Frontend zeigt dezenten Hinweis („Wetterdaten nicht verfügbar"), Karte + Marker bleiben voll funktionsfähig (keine JS-Exception, Map-Tab nutzbar).
- [ ] Legende sichtbar (Skala Wolken 0–100 %; Niederschlag mm-Menge; Niederschlag %-Wahrscheinlichkeit); Legende wechselt mit Sub-Option; Werte-Farbzuordnung dokumentiert.

**Pre-Mortem:**
- 💀 Open-Meteo Rate-Limit/Block durch Slider-Spam (pro Tick ein Call) → Karte hängt, 429. Auslöser: kein Cache, Fetch an Slider gekoppelt. Frühwarnung: Lag beim Schieben, 429 im Log. → Gegenmaßnahme: **ein** Multi-Punkt-Request für den ganzen Horizont + Prozess-Cache (AK 3 + AK 5) — Slider rendert nur clientseitig.
- 💀 Overlay-Z-Index kollidiert mit Filter/Leaflet-Panes → Overlay verdeckt Marker oder liegt unter den Tiles. Auslöser: bekannter Leaflet-Stacking-Context (siehe CSS-Kommentar Z. 200, BUG-24). Frühwarnung: Marker unklickbar / Overlay unsichtbar. → Gegenmaßnahme: Overlay als eigenes Leaflet-Pane mit definiertem `zIndex` zwischen Tile- und Marker-Pane; nicht via globalem CSS-Filter. Manueller Test „Basis-Wechsel + Marker klickbar".
- 💀 Falsche Stunde angezeigt (UTC/Ortszeit-Verwechslung) → Fotograf plant nach falschem Wetter. Auslöser: Open-Meteo liefert UTC (`timezone=UTC` in `weather.py`), App zeigt Berlin (+2/+1). Frühwarnung: Overlay-Label weicht von Event-Detail-Zeit ab. → Gegenmaßnahme: intern durchgängig UTC, nur im Label konvertieren (Memory `shoot_time_utc`); AK 5 prüft Label-Konsistenz.
- 💀 Grid zu grob → „Wetterkarte" wirkt wie 4 Klötze, kein Mehrwert; oder zu fein → langsamer/größerer Request. Auslöser: willkürliche Auflösung. Frühwarnung: visuell blockig oder Request > paar Sek. → Gegenmaßnahme: 10×10=100 Punkte (~90 km Abstand, ganz Deutschland) — durch Stephan entschieden; Auflösung als eine Konstante kapseln. Daten-Validierung: ersten echten Call gegen 100-Punkt-Grid messen (Antwortgröße, -zeit) vor Frontend-Bau.
- 💀 Map-Tab lädt das Overlay automatisch und kostet jedem Nutzer Open-Meteo-Calls/Latenz, auch wenn er es nie braucht. Auslöser: Eager-Load in `MapView.init()`. → Gegenmaßnahme: Overlay **lazy** — Default „aus", Fetch erst beim ersten Aktivieren (AK 4).

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: Backend `backend/calculations/weather.py` (`fetch_weather_forecast`, `HourlyWeather` — liefert `cloud_cover_pct`/`precipitation_mm`/`precipitation_prob_pct`; Open-Meteo Punkt-API, kein Tile-Dienst) + `backend/main.py` (`_weather_overlay` Z. 343–420 als Vorbild für Aggregation/Logging, `/weather-refresh` Z. 1031 als Endpoint-Pattern, `_CACHE_DIR`/Prozess-Cache-Globals Z. 94–98/218, `auth.require_host`-Dependency-Muster). Frontend `web/index.html`: `MapView` (Z. 3034–3166 — `init`/`setLayer`/`loadMarkers`/eigenes Pane), Map-Tab-HTML + Layer-Buttons (Z. 767–774), Leaflet-CSS/Stacking-Hinweise (Z. 200–204), Tab-Aktivierung `if (page === 'map') MapView.init()` (Z. 4084). Reines Add-on, keine bestehende Wetter-Score-Logik wird verändert.
- [x] Implementierungsoptionen: A (Grid aus Open-Meteo-Punkten, eigener Render) / B (externe Radar-Tile-Layer) / C (nur Marker-basierte Wetter-Badges, kein Flächen-Overlay)
- [x] Empfehlung: **Option A** — durch Stephan bestätigt

**Implementierungsoptionen:**

*Option A — Grid aus Open-Meteo-Punkt-Forecasts, clientseitig gerendertes Leaflet-Overlay* · Aufwand: mittel
- Vorgehen: Neue Funktion `fetch_weather_grid(bbox, resolution, hours)` in `weather.py` (Multi-Punkt-Open-Meteo-Request, Komma-getrennte Koordinaten in einem Call). Neuer Endpoint `GET /weather-map` in `main.py` mit 60-min-Prozess-Cache (Muster wie `_weather_updated_at`). Frontend: `MapView` um `weatherOverlay`-State erweitern — eigenes Leaflet-Pane, farbcodierte `L.rectangle`/`L.circleMarker` pro Grid-Punkt, Toggle-UI (Wolken/Niederschlag/aus) neben den Layer-Buttons, Stunden-Slider, Legende. Fetch lazy beim ersten Aktivieren, Stundenwechsel rein clientseitig.
- Betroffene Dateien: `backend/calculations/weather.py`, `backend/main.py`, `web/index.html`. Tests: `backend/tests/` (Endpoint-Form, Cache, null-Handling).
- Vorteile: bleibt bei bewährter Open-Meteo-Quelle (kein Lizenzrisiko, kein Key), volle Kontrolle über Farben/Skalen, exakt auf das Shooting-Fenster (gleiche Datenbasis wie Event-Wetter), testbar via pytest.
- Nachteile/Risiken: eigener Renderer + Grid-Auflösung-Tuning; grobes Raster statt Foto-realistischem Radar.

*Option B — Externer Radar-/Wolken-Tile-Layer (z. B. RainViewer / OWM-Tiles) als Leaflet-TileLayer* · Aufwand: klein–mittel
- Vorgehen: zusätzlichen `L.tileLayer(weatherTileUrl)` als Overlay-Pane einhängen.
- Vorteile: sehr wenig Code, fotorealistisches Radar, Animation möglich.
- Nachteile/Risiken: **neuer externer Provider** → Lizenz-/Nutzungsbedingungen-Prüfung nötig (kollidiert direkt mit US-74), oft API-Key/Rate-Limit/Kosten, Zeitbezug nicht exakt aufs Shooting-Fenster steuerbar, nicht via pytest abdeckbar, neue Abhängigkeit außerhalb der etablierten Open-Meteo-Quelle.

*Option C — Keine Fläche, nur Wetter-Badges an bestehenden Location-Markern* · Aufwand: klein
- Vorgehen: pro sichtbarem Location-Marker ein kleines Wolken-/Regen-Symbol aus den schon vorhandenen `weather_details`.
- Vorteile: minimal, nutzt vorhandene Daten, kein neuer Endpoint.
- Nachteile/Risiken: erfüllt die Story nicht — „Wetter*karte* … visuell einschätzen" verlangt das räumliche Muster über die Region, nicht nur Punkte an Spots; Lücken zwischen Locations bleiben blind.

✅ **Empfehlung: Option A** — erfüllt die Story (flächige, zeitlich steuerbare Einschätzung), bleibt bei der lizenzsicheren Open-Meteo-Quelle (vermeidet den US-74-Konflikt von Option B), ist via pytest testbar und hält alle Pre-Mortem-Gegenmaßnahmen (ein Request + Cache, eigenes Pane, UTC-intern, lazy load) sauber umsetzbar. Option B nur erwägen, falls fotorealistisches Radar explizit gewünscht ist und die Lizenzfrage (US-74) vorab geklärt wird.

**Daten-Validierung** *(in Implementierung zu bestätigen):*
- [ ] Open-Meteo Multi-Punkt-Request (Komma-getrennte `latitude`/`longitude`) liefert für **100 Punkte** in einem Call die parallelen `cloud_cover`/`precipitation_mm`/`precipitation_prob`-Arrays — vor dem Frontend-Bau mit echtem Aufruf gegen das Deutschland-Grid prüfen (Antwortgröße, Antwortzeit, null-Verhalten an Bbox-Rändern).
- [ ] Wertebereiche real prüfen: typische Wolkendecke 0–100, Niederschlag meist 0 — Farbskala an realen Sommer-Werten kalibrieren, nicht raten.

**Testplan:**
- [ ] Automatisiert (Harness, `backend/tests/`): Endpoint-Form von `/weather-map` (Grid-Länge 100, Reihenlängen == `hourly_times`; `precipitation_mm` + `precipitation_prob` beide vorhanden); null-Handling bei fehlendem Grid-Punkt; Cache-Verhalten (zweiter Call → `fetched_at` unverändert / kein erneuter HTTP-Call, gemockt). Docstring mit `US-72`. Python 3.9-kompatibel (keine `X | Y`-Typen — `Optional[...]`/`List[...]` verwenden, wie in `weather.py`).
- [ ] Manuell (http://localhost:8000, Map-Tab): Overlay aktivieren → Grid erscheint; Wolken↔Niederschlag wechseln (nur eins sichtbar); Slider schieben → Stunde/Label ändert sich, kein Netzwerk-Call (DevTools-Network); Basis-Layer wechseln → Overlay bleibt, Marker klickbar (BUG-24-Stacking); Open-Meteo offline simulieren → Hinweis statt Crash.

---

### US-112 · Wetter-Overlay: echte Modelldaten (DWD ICON-D2 + MET Norway) als weicher Verlauf `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-30 |
| **Abgeschlossen** | 2026-07-01 (released, live verifiziert) |

**✅ Abschluss (2026-07-01):** Live auf der Produktion verifiziert — weicher Wolken-/Niederschlags-Verlauf über DE/AT/Norditalien (DWD ICON-D2 0–48 h + ICON-EU 48–72 h) plus Norwegen (MET), 72-h-Schieber mit Berliner Zeit, Attribution, kein Speicher-Abbruch. Vier Live-Fehler behoben (DWD-Dateinamen, Speicherüberlauf → Blockgröße, zu langsames Rendern → Stützpunkt-Ausdünnung, ICON-EU 6-h-Hauptläufe) + Zeit-Label-Fix (`+00:00`→Invalid Date) + Layout-Feinschliff (Menüs nebeneinander, Zeitachse/GPS unten, Quellenangabe links). **Nicht-Bug gelernt:** Overlay „fehlte" nur, weil der Browser gegen den lokalen Server (`fa_api`/localhost) ohne DWD-Daten lief bzw. ein alter Service Worker die Seite cachte — Produktion war korrekt.

**🎨 Designer-Check (2026-06-30, bestanden):** Farbskalen (Wolken 0–100 %, Niederschlag mm/h) monoton in Helligkeit → farbenblind-sicher und Bauhaus-konform; Overlay-Deckkraft ~59 % lässt Karte+Marker durch; Attribution leicht verstärkt (CSS direkt angepasst). **Offen, erst am echten gerenderten Bild nach Deploy:** (1) weiche Naht DWD↔MET bei ~58°N, (2) Deckkraft über Satelliten-Layer, (3) Modus-Wechsel Wolken↔Regen, (4) Gold-Kontrast aktiver Toggle im Hellmodus. Keine Blocker.

**🔧 Nachtrag Live-Test (2026-07-01):** Erster Deploy war strukturell ok (Endpoint, Attribution, 72h-Achse, MET/Norwegen), aber die DWD-Daten kamen nicht an (`sources: icon_d2:0, icon_eu:0, met:16`) — über Deutschland/Österreich/Italien leer. Ursache: falsches DWD-Dateinamen-Schema in `_dwd_url` (fehlendes `_2d_`, falsche Gitter-/Groß-Klein-Bausteine). Am Live-Verzeichnis verifizierte echte Namen: ICON-D2 `..._<fc>_2d_clct` / `..._2d_tot_prec` (klein), ICON-EU `..._<fc>_CLCT` / `..._TOT_PREC` (groß, ohne `_2d_`). `_dwd_url` entsprechend korrigiert; Sandbox-Check erzeugt exakt die vier echten Namen. Wartet auf Re-Deploy + Prüfung, dass `icon_d2`/`icon_eu` > 0.

**🚦 Weg-Gate-Entscheidung (2026-06-30, Stephan):**
- **Weg: Option A** — echte DWD-Modelldaten (ICON-D2 ~2 km für 0–48 h + ICON-EU ~7 km für 48–72 h) **plus** MET Norway (Norwegen), serverseitig zu einem weichen Bild (PNG je Stunde, `L.imageOverlay`) verrechnet. Volle 72-h-Pflicht bleibt, 2-km-Schärfe wird erreicht.
- **US-72-Backend:** existiert nicht (nur Frontend gegen 404) → der Wetter-Endpoint wird **direkt in US-112 neu gebaut**; US-72 geht darin auf.
- **Geltungsbereich:** Deutschland + Österreich + Norditalien (DWD) + Norwegen (MET). Dänemark/restliches Skandinavien bewusst **draußen**.
- **Kosten/Key:** keine Kosten, kein Account/Key. Pflichten: GRIB-Verarbeitung serverseitig (Systembibliothek eccodes/cfgrib — neu auf dem Server zu installieren), MET-Pflicht-`User-Agent` mit App+Kontakt, Caching-Pflicht, Attribution „Daten: DWD · MET Norway (CC BY 4.0)" im Frontend.

**Beschreibung:** Als Fotograf möchte ich das Wetter-Overlay der Karte auf einer echten, hochaufgelösten Modell-Datenbasis und als weichen, fließenden Verlauf sehen (statt grober Kacheln), damit ich Wolkendecke und Niederschlag räumlich präziser einschätzen kann — und damit die App zukunftssicher auf einer gratis **und** kommerziell nutzbaren Quelle steht (Open-Meteos Gratis-Stufe ist nicht-kommerziell, die App könnte perspektivisch kommerziell werden). Umgestellt wird auf **DWD Open Data ICON-D2** (echtes Modellgitter ~2 km, deckt Deutschland/Österreich/Norditalien ab) plus **MET Norway** (gratis, kommerziell nutzbar, CC BY) für Norwegen, da ICON-D2 Norwegen nicht abdeckt. Die Darstellung wird ein reiner weicher Verlauf (Interpolation/Heatmap), kein hartes Kachelraster. Der bestehende 72-Stunden-Vorhersage-Schieber bleibt Pflicht.

**Bezug:**
- Baut auf **US-72** (Wetterkarte, aktuell „In Test") auf und **ersetzt deren Datenbasis** (Open-Meteo Punkt-Grid → echte Modelldaten) sowie die grobe Kachel-Darstellung durch einen weichen Verlauf. US-72 liefert Endpoint-Struktur, Toggle-UI, Cache-Muster und 72h-Slider als Fundament.
- Löst die in **BUG-55** zurückgehaltene Open-Meteo-Mehrländer-Variante ab: Der Zoom-/`fitBounds`-Fix aus BUG-55 wird **separat released**; die dort enthaltene **Open-Meteo-Mehrländer-Erweiterung wird NICHT released**, sondern durch dieses Ticket (US-112) auf die neue DWD-/MET-Datenbasis abgelöst.
- Berührt **US-74** (Open-Source-Lizenzprüfung): neue Quellen DWD + MET Norway sind beide gratis + kommerziell nutzbar; Attribution (DWD + MET) ist Pflicht.

**Offene Punkte für die Analyse-Phase** *(nur Hinweis, hier NICHT lösen):*
- Server-seitige GRIB-Verarbeitung der ICON-D2-Daten (Systembibliothek, Hintergrund-Job, Speicher-/Laufzeitbedarf).
- Verifizieren, ob ICON-D2 **Österreich + Norditalien** tatsächlich abdeckt.
- MET-Norway-Spielregeln: Pflicht-Kennung/User-Agent, Caching, Tempolimit/Rate-Limit.
- Zusammenführen beider Quellen (ICON-D2 + MET) auf eine gemeinsame 72h-Zeitachse.
- Attribution beider Quellen (DWD + MET) im Frontend.
- Weicher Render-Ansatz im Frontend (Interpolation/Heatmap statt `L.rectangle`-Kacheln).

---

**Implementation Spec** *(Analyse 2026-06-30)*

**⚠️ Befund vorab — die Datenbasis von US-72 existiert im Backend gar nicht.**
📎 Code-Verifikation am 2026-06-30 (HEAD + Working Tree, `git grep`): Es gibt **keinen** `/weather-map`-Endpoint und **keine** Gitter-Funktion im Backend — weder in `backend/main.py` noch in `backend/calculations/weather.py`. `fetch_weather_grid`, `fetch_weather_multigrid`, `WEATHER_REGIONS` und `_weather_map_cache` kommen ausschließlich in der **untracked** Testdatei `backend/tests/test_us72_weather_map.py` vor (test-first geschrieben, nie implementiert). Das Frontend `WeatherMap` (web/index.html ab Z. 4284) ist committed und ruft `/weather-map?hours=72` auf — gegen einen Endpoint, der auf dem Server **404** liefert. Das erklärt, warum US-72 dauerhaft „In Test" hängt: Die Backend-Hälfte wurde nie gebaut; nur die BUG-55-Zoom-Korrektur (reines Frontend) ging als v1.20.10 live. **Konsequenz:** US-112 ist kein reiner Datenquellen-Austausch, sondern muss den `/weather-map`-Endpoint **erstmals** bauen. Das vergrößert den Aufwand erheblich und ist eine Entscheidung für Stephan (siehe Offene Entscheidungen E0).

**Recherche-Befunde (verifiziert):**
- ✅ **ICON-D2-Abdeckung:** Modellgebiet **43,2°N 3,9°W → 58,1°N 20,3°E** (regular grid). Damit **Österreich vollständig** und **Norditalien/Po-Ebene** (~44–46°N) abgedeckt — beide *verifiziert*. Quelle: weatherfiles.com (DWD-Slicing-Dienst), DWD NWP-Seite.
- ⛔ **ICON-D2 reicht nur bis +48 h** (Läufe alle 3 h, 00/03/06/09/12/15/18/21 UTC; 2,2 km). Der geforderte **72-h-Slider lässt sich mit ICON-D2 allein nicht füllen** — *verifiziert*. **ICON-EU** (ebenfalls DWD Open Data, gratis, GRIB2, ~7 km) reicht bis **+120 h** (stündlich bis +78 h) und deckt ganz Europa inkl. Skandinavien ab. Quelle: DWD NWP forecast data.
- ✅ **DWD-Zugriff:** `opendata.dwd.de/weather/nwp/icon-d2/grib/<run>/<param>/…`, **GRIB2**, kein Key/Account, kostenlos. Felder: **CLCT** (total cloud cover %), **TOT_PREC** (akkumulierter Niederschlag mm — pro Stunde = Differenz aufeinanderfolgender Schritte). Dateien werden nach ~24 h gelöscht. Verarbeitung serverseitig braucht eine GRIB-Bibliothek (**eccodes** als Systemlib + `cfgrib`/`xarray` oder `pygrib`) — *aktuell NICHT in `requirements.txt`* (nur numpy/pandas vorhanden). Quelle: DWD Open Data, DWD-Doku.
- ✅ **MET Norway Locationforecast 2.0:** **Punkt-API** (eine Koordinate je Request, kein Gitter), JSON. Stündlich 0–60 h, danach 6-stündlich bis ~10 Tage → für 72 h sind die letzten 12 h nur 6-stündlich. **Pflicht-`User-Agent`** mit App-/Domainname + Kontakt (generischer UA → Block, kein Throttle). **Caching-Pflicht** via `Expires`/`If-Modified-Since`, nicht öfter abfragen als `Expires`. **Lizenz CC BY 4.0** → Namensnennung + Link Pflicht. Gratis, kommerziell nutzbar. Quelle: api.met.no ToS/FAQ.
- ✅ **Weicher Render-Ansatz (Leaflet):** Statt `L.rectangle` pro Punkt → serverseitig ein **interpoliertes PNG** (IDW/bilinear über das Gitter) pro Stunde rendern und als **`L.imageOverlay`** mit Verlauf einblenden, ODER clientseitig **Canvas-Heatmap** (z. B. bilineare Interpolation in ein `<canvas>` über die Gitter-Bounds, als imageOverlay). Beides Leaflet-kompatibel, ohne fremden Tile-Provider (kein US-74-Konflikt). Quelle: Leaflet-Plugins/Heatmap-Praxis. *Render-Detail offen → Designer-Check Pflicht.*

**Annahmen (markiert):**
- ⚠️ Annahme A1: Für die **72-h-Pflicht** wird in DE/AT/Norditalien **ICON-D2 (0–48 h)** mit **ICON-EU (48–72 h)** kombiniert (beide DWD, gratis), statt den Slider auf 48 h zu kürzen. Bitte bestätigen (sonst E1).
- ⚠️ Annahme A2: Render erfolgt **serverseitig als interpoliertes PNG je Stunde** (imageOverlay), weil das den weichsten Verlauf liefert und die GRIB-Schwerlast ohnehin im Backend liegt. Bitte bestätigen (sonst E2).
- ⚠️ Annahme A3: Abdeckung bleibt **DE + AT + Norditalien + Norwegen** (wie Ticket). Dänemark/restliches Skandinavien NICHT in diesem Ticket (würde MET- oder ICON-EU-Ausweitung brauchen).

**Example Mapping:**

📏 **Rule 1 — Das Overlay zeigt einen weichen, fließenden Verlauf statt sichtbarer Kacheln.**
- 🟢 Positiv: Given Karte über Deutschland, Wetter „Wolken" an, Stunde = heute 20:00, Then sehe ich einen sanften Farbverlauf (hell = klar → dunkel = bedeckt) ohne erkennbare Rechteck-Kanten; Übergänge zwischen klar und bedeckt sind weich.
- 🔴 Negativ: Given Wetter aus, Then keine Wetterfläche; normale Karte unverändert.
- ⚠️ Edge: Given einzelne Modellzelle ohne Wert, Then wird dort interpoliert/ausgelassen, kein harter Block, kein Loch mit Fehlfarbe.

📏 **Rule 2 — Die Fläche basiert auf echten Modelldaten, nicht auf wenigen Stützpunkten.**
- 🟢 Positiv: Given ich vergleiche zwei nah beieinander liegende Orte (z. B. Berlin-Mitte vs. Potsdam), Then unterscheidet sich der Verlauf fein (Auflösung ~2 km in DE/AT/Norditalien), nicht in ~90-km-Blöcken wie vorher.
- ⚠️ Edge: Given Norwegen (außerhalb ICON-D2), Then erscheint dort trotzdem Wetter (aus MET Norway), und der Übergang zwischen DWD- und MET-Gebiet hat keinen harten Bruch/keine Doppelfläche.

📏 **Rule 3 — Der 72-h-Schieber bleibt voll funktionsfähig.**
- 🟢 Positiv: Given Overlay an, When ich den Schieber von „jetzt" bis „+72 h" ziehe, Then ändert sich die Fläche pro Stunde, das Zeit-Label zeigt Berliner Ortszeit, und kein Stundenwechsel löst einen neuen Server-Call aus (alles vorab geladen).
- ⚠️ Edge: Given Stunde 48–72 (jenseits ICON-D2), Then zeigt die Karte weiterhin Fläche (aus ICON-EU bzw. MET), ohne dass DE/AT plötzlich leer wird.

📏 **Rule 4 — Die Quellen werden korrekt genannt (Lizenzpflicht).**
- 🟢 Positiv: Given Overlay an, Then ist eine dezente Quellenangabe sichtbar: „Daten: DWD (ICON-D2/EU) · MET Norway (CC BY 4.0)" mit Link.
- 🔴 Negativ: Given Overlay an ohne Attribution, Then verstößt die App gegen CC BY → nicht zulässig.

✅ Questions offen → siehe „Offene Entscheidungen für Stephan" (E0–E4). Keine 🔴-kritische Question wird hier still entschieden.

**Scope:**
- Eingeschlossen: Neuer/echter `/weather-map`-Backend-Endpoint, der ICON-D2 (DE/AT/Norditalien, 0–48 h) + ICON-EU (48–72 h) + MET Norway (Norwegen) verarbeitet und auf eine **gemeinsame 72-h-Stundenachse** zusammenführt; serverseitige GRIB-Verarbeitung als Hintergrund-Job mit Cache; weiches Verlaufs-Overlay im Frontend (imageOverlay/Canvas statt `L.rectangle`); 72-h-Slider (bestehend) weiternutzen; Quellen-Attribution im Map-Tab; Toggle Wolken/Niederschlag (bestehend).
- Ausgeschlossen: iOS (`ios/`), animierte Radar-Loop, Push bei Wetterwechsel, Länder außerhalb DE/AT/Norditalien/Norwegen, Auflösung > 72 h, gleichzeitige Überlagerung beider Wetter-Layer.

**Akzeptanzkriterien (erlebbares Verhalten):**
- [ ] Schalte ich auf der Karte „Wolken" oder „Niederschlag" ein, erscheint über Deutschland/Österreich/Norditalien eine **weiche, fließende Wetterfläche** ohne sichtbare Rechteck-Kacheln; benachbarte Orte unterscheiden sich fein (nicht in groben Blöcken).
- [ ] Über **Norwegen** erscheint ebenfalls Wetter; am Übergang zwischen dem deutschen und dem norwegischen Datengebiet gibt es keinen harten Sprung und keine doppelte Fläche.
- [ ] Der **72-Stunden-Schieber** funktioniert über den ganzen Bereich: von „jetzt" bis „+72 h" ändert sich die Fläche pro Stunde; auch jenseits von +48 h (wo das hochauflösende Modell endet) bleibt überall Wetter sichtbar, Deutschland wird nicht plötzlich leer.
- [ ] Das Zeit-Label zeigt **Berliner Ortszeit**; das Verschieben des Schiebers lädt **keine** neuen Daten nach (nur die erste Aktivierung lädt).
- [ ] Eine dezente **Quellenangabe** ist sichtbar, solange das Overlay an ist: „Daten: DWD · MET Norway (CC BY 4.0)" mit anklickbarem Lizenz-/Quellen-Link.
- [ ] Edge: Ist eine der Wetterquellen gerade nicht erreichbar, zeigt die App einen dezenten Hinweis und die Karte (Marker, Basis) bleibt voll bedienbar — kein Hängen, kein Absturz.
- [ ] Edge: An einzelnen Stellen ohne Modellwert entsteht kein farbiges Loch und kein harter Block; die Fläche bleibt durchgehend weich.
- [ ] Schalte ich das Overlay aus und auf eine andere Karten-Basis (Standard/Satellit/Nacht), bleibt die Karte korrekt; beim erneuten Einschalten liegt das Overlay wieder sauber über der Basis und unter den Markern (Marker klickbar).

**Pre-Mortem (Code-verifiziert):**
- 📎 Verifiziert: `backend/calculations/weather.py` nutzt Open-Meteo-Punkt-API, `from __future__ import annotations` (also `list[...]` auf 3.9 ok); `backend/main.py` hat Prozess-Cache-Muster (`_weather_updated_at`, `_weather_overlay` als 3-h-Cron Z. 1255) und Background-Task-Muster — als Vorbild für GRIB-Job + Cache nutzbar. Frontend `WeatherMap` (web/index.html Z. 4284–4561) rendert heute `L.rectangle` pro Punkt, eigenes `weatherPane` (zIndex 250), liest `data.grid[].{cloud_cover,precipitation_mm,precipitation_prob}` + `data.hourly_times` + 72-h-Slider — der weiche Render ersetzt nur `_render()`, Slider/Cache/Pane bleiben.
- 💀 `/weather-map` existiert serverseitig nicht → US-112 wird als „Quellenwechsel" geplant, ist aber „Endpoint-Neubau". Auslöser: US-72-Backend nie committed. Frühwarnung: `git grep weather-map backend/*.py` leer (bereits eingetreten). → Gegenmaßnahme: E0 vor Implementierung klären; Aufwand als „groß" einstufen.
- 💀 72-h-Slider bleibt jenseits +48 h in DE/AT leer, weil ICON-D2 nur 48 h liefert. Auslöser: Annahme „ein Modell deckt 72 h". → Gegenmaßnahme: ICON-EU für 48–72 h dazunehmen (A1/E1); AK „Deutschland wird nicht leer" prüft genau das.
- 💀 GRIB-Verarbeitung sprengt Speicher/Laufzeit auf dem kleinen Hetzner-Server (eccodes + ganzes ICON-D2-Gebiet × 72 h × 2 Felder). Auslöser: ungeschnittene GRIB-Last. → Gegenmaßnahme: serverseitig auf die App-Bounding-Box + nur CLCT/TOT_PREC slicen, als Hintergrund-Job mit Cache (analog 3-h-Wetter-Cron), Laufzeit/Größe beim ersten echten Lauf messen (Daten-Validierung), Python 3.9-kompatibel halten.
- 💀 MET Norway sperrt die App (generischer User-Agent / zu häufige Abfragen). Auslöser: fehlende Kennung/Cache. → Gegenmaßnahme: fester `User-Agent` „FotoAlert/<ver> (kontakt)", `Expires`/`If-Modified-Since` respektieren, Ergebnis cachen; nur Norwegen-Gitterpunkte abfragen, nicht pro Stunde neu.
- 💀 Naht zwischen DWD- und MET-Gebiet zeigt harten Bruch/Doppelfläche. Auslöser: zwei Quellen auf einer Achse ohne Blending. → Gegenmaßnahme: gemeinsame Stundenachse + räumliches Blending an der Gebietsgrenze; AK „kein harter Sprung" prüft das.
- 💀 Niederschlag falsch, weil ICON liefert **akkumuliert** (TOT_PREC), MET teils Intervall/anders. Auslöser: Einheiten-Mismatch. → Gegenmaßnahme: TOT_PREC pro Stunde als Differenz aufeinanderfolgender Schritte; MET-Felder auf dieselbe Einheit (mm/h) normalisieren; an realen Werten kalibrieren.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt (Code-verifiziert: Endpoint fehlt im Backend)
- [x] Architektur analysiert: Backend `backend/main.py` (Cache-/Cron-/Background-Muster), `backend/calculations/weather.py` (Open-Meteo-Vorbild, 3.9-kompatibel), **neuer GRIB-Pfad nötig** (eccodes/cfgrib oder pygrib → `requirements.txt`); Frontend `web/index.html` `WeatherMap` (nur `_render()` auf weichen Verlauf umstellen, Slider/Cache/Pane bleiben) + Attribution im Map-Tab.
- [x] Designer-Check: visuell **ja** → vor Implementierung `fotoalert-designer` für den weichen Verlauf (Farbskala, Opazität, Naht-Blending, Attribution-Platzierung) einholen.
- [x] Implementierungsoptionen: A / B / C
- [ ] Empfehlung: Option A (Weg-Gate offen)

**Implementierungsoptionen:**

### Option A — DWD GRIB (ICON-D2 + ICON-EU) + MET Norway, serverseitig verarbeitet, weiches imageOverlay
- App-Wirkung: Genau die Ticket-Vision — hochaufgelöster, weicher Verlauf aus echten Modelldaten in DE/AT/Norditalien, Norwegen aus MET, durchgehender 72-h-Slider, gratis + kommerziell nutzbar.
- Vorgehen: Backend lädt + slict GRIB2 (CLCT/TOT_PREC) auf App-BBox, fügt ICON-EU für 48–72 h und MET-Norway-Punkte für Norwegen hinzu, interpoliert je Stunde zu einem PNG; neuer `/weather-map`-Endpoint + Hintergrund-Job + Cache. Frontend: `_render()` auf `L.imageOverlay` umstellen, Attribution einblenden.
- Betroffene Dateien: `backend/main.py`, `backend/calculations/weather.py` (+ ggf. neues `weather_grib.py`), `backend/requirements.txt` (eccodes/cfgrib o. pygrib), `web/index.html`.
- Vorteile: erfüllt die Story voll; lizenzsicher (DWD + MET CC BY); zukunftssicher kommerziell.
- Nachteile/Risiken: **größter Aufwand**; neue Systembibliothek (eccodes) auf dem Server; GRIB-Last messen; Naht-Blending. Aufwand: **groß**.

### Option B — Nur MET Norway als Multi-Punkt-Gitter für ALLE Gebiete (kein GRIB)
- App-Wirkung: Weicher Verlauf aus echten Daten, aber gröber als 2 km; Norwegen + Mitteleuropa aus einer Quelle.
- Vorgehen: ein Gitter eigener Punkte über alle Gebiete, je Punkt MET-Locationforecast; clientseitige Canvas-Interpolation. Kein GRIB, keine Systemlib.
- Vorteile: deutlich einfacher (kein eccodes), eine Quelle, 72 h aus MET; gratis + CC BY.
- Nachteile/Risiken: viele Einzel-Requests (Rate-/Caching-Disziplin!), gröbere Auflösung (kein 2-km-Vorteil), MET ab 60 h nur 6-stündlich. Aufwand: **mittel**. Verfehlt das Ticket-Versprechen „2-km-Modellgitter" teilweise.
- ⚠️ Hinweis: MET-Daten stammen u. a. selbst aus ICON-Modellen, aber als Punkt-API ohne native Gitterauflösung.

### Option C — Slider auf 48 h kürzen, nur ICON-D2 + MET
- App-Wirkung: Höchste Auflösung in DE/AT/Norditalien, aber nur 48-h-Vorschau statt 72 h.
- Vorgehen: wie A, aber ohne ICON-EU; Slider-Max auf 48 h.
- Vorteile: weniger Quellen zusammenzuführen.
- Nachteile/Risiken: **verletzt die 72-h-Pflicht** aus dem Ticket → nur zulässig, wenn Stephan die Kürzung ausdrücklich freigibt. Aufwand: groß (GRIB bleibt).

✅ **Empfehlung: Option A** — als einzige Variante, die alle Ticket-Vorgaben erfüllt (echtes ~2-km-Modellgitter, weicher Verlauf, 72 h, gratis + kommerziell, Norwegen abgedeckt). Voraussetzung sind die Entscheidungen E0–E2. Option B ist der pragmatische Rückfallweg, falls eccodes auf dem Server zu schwer ist; Option C nur bei bewusster 72→48-h-Kürzung.

**Offene Entscheidungen für Stephan (vor Implementierung):**
- **E0 (kritisch):** US-72-Backend (`/weather-map`) wurde nie gebaut. US-112 muss den Endpoint **erstmals** implementieren (großer Aufwand). Geht US-112 trotzdem direkt los, oder zuerst ein schlankes US-72-Backend nachziehen?
- **E1 (kritisch):** 72-h-Pflicht: ICON-D2 reicht nur 48 h. **ICON-EU für 48–72 h dazunehmen** (empfohlen, A1) ODER Slider auf 48 h kürzen (Option C)?
- **E2:** Render serverseitig als interpoliertes PNG (A2, weichste Optik) ODER clientseitige Canvas-Heatmap (leichter fürs Backend)?
- **E3:** Server-Belastung: eccodes/GRIB auf dem Hetzner-Server akzeptabel (Speicher/Laufzeit messen) ODER lieber GRIB-frei via MET-Multi-Punkt (Option B)?
- **E4:** Bestätigung Abdeckungs-Scope: DE + AT + Norditalien + Norwegen — Dänemark/Skandinavien bewusst NICHT in diesem Ticket?

**Daten-Validierung** *(in Implementierung zu bestätigen):*
- [ ] Realen ICON-D2-GRIB-Lauf gegen App-BBox slicen → Speicher/Laufzeit/Größe messen (eccodes), bevor Frontend gebaut wird.
- [ ] ICON-D2-Abdeckung Norditalien am echten Gitter prüfen (Süd-Rand 43,2°N deckt Po-Ebene — am Datensatz gegenchecken, nicht nur Doku).
- [ ] MET-Norway-Antwort an einem Norwegen-Punkt: Felder, Einheiten, `Expires`-Header, Stundenraster 0–60 h prüfen.
- [ ] TOT_PREC (akkumuliert) korrekt auf mm/h differenzieren; mit MET-Niederschlag auf gleiche Einheit kalibrieren.

**Testplan:**
- [ ] Automatisiert (`backend/tests/`, Docstring `US-112`, Python 3.9 / `Optional[...]`): `/weather-map`-Schema (gemeinsame `hourly_times` Länge ~72, Wolken+Niederschlag vorhanden, Bild/Gitter je Stunde); Quellen-Merge (DWD-Gebiet + Norwegen-Punkte auf einer Achse); null-Handling bei Quellen-Ausfall (eine Quelle weg → andere bleibt gültig, kein 500); Cache (zweiter Call ohne neuen Fetch). GRIB-Parsing gegen ein kleines Fixture, nicht gegen Live-DWD.
- [ ] Manuell (http://localhost:8000, Map-Tab): Overlay an → weicher Verlauf ohne Kacheln; Slider bis +72 h → DE/AT/Norditalien/Norwegen durchgehend gefüllt, Label Berliner Zeit, kein Netzwerk-Call beim Schieben (DevTools); Quellenangabe sichtbar + Link; eine Quelle offline simulieren → Hinweis statt Crash; Basis-Wechsel → Overlay bleibt, Marker klickbar.

---

### TASK-50 · Service-Worker: neue Version nach Release automatisch übernehmen `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-07-01 |

**Beschreibung:** Nach einem Release zeigt die App im Browser oft noch die **alte** Version (altes Layout/Verhalten), obwohl der neue Stand längst deployed ist — weil der alte Service Worker die gecachte Seite weiter ausliefert. „Cache leeren" reicht nicht; aktuell muss man die Website-Daten manuell entfernen bzw. den Service Worker von Hand abmelden. Gewünscht: Nach einem Release übernimmt die neue Version **automatisch** beim nächsten Öffnen/Neuladen, ohne manuelles Eingreifen.

**Kontext (aus US-112 gelernt):** Der Service Worker (`web/sw.js`) benennt beim Deploy zwar den Cache-Namen um und löscht beim Aktivieren alte Caches (`clients.claim()`), aber die neue Version wird nicht sofort aktiv (kein `skipWaiting()`), solange noch ein Tab mit dem alten Worker offen ist. Bei US-112 kostete das mehrfach Verwirrung: Layout- und Overlay-Änderungen erschienen erst nach manuellem Abmelden des alten Workers.

**Offene Punkte für die Analyse-Phase** *(nur Hinweis, hier NICHT lösen):*
- Sofort-Übernahme (`skipWaiting()` + Steuerung übernehmen) gegen die Gefahr abwägen, dass eine laufende Sitzung mitten im Betrieb die Assets wechselt (ggf. dezenter „Neue Version verfügbar – neu laden"-Hinweis statt hartem Reload).
- Verhalten für die zum Home-Bildschirm hinzugefügte PWA prüfen.

---

### US-73 · Anreise zum Standort (Get to Location) `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Als Fotograf möchte ich direkt aus einem Event oder einer Location heraus die Anreise zum Fotografen-Standort starten können (z. B. Link zu Maps/ÖPNV), damit ich rechtzeitig vor Ort bin.

---

### US-74 · Regelmäßige Open-Source-Lizenzprüfung `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Das System soll regelmäßig prüfen, ob alle genutzten Open-Source-Quellen und -Daten (OSM, open-meteo, Geodaten-Portale) weiterhin für die gewerbliche Nutzung in dieser App erlaubt sind, und bei lizenzrechtlichen Änderungen einen Hinweis ausgeben.

---

### US-75 · User/Backend-Datensync: Qualitätssicherung & Automatisierung `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Als Betreiber möchte ich sicherstellen, dass von Nutzern hinzugefügte/geänderte Locations (Motive, Standorte, Beschreibungen) regelmäßig und geprüft ins Backend übertragen werden — inkl. automatischer Generierung von Standortbeschreibungen, idealem Azimut, konsistenter Kategorisierung und automatischer Aktualisierung der Brennweitenempfehlungen.

**Abhängigkeit:** TASK-17 ✅ (Datenfundament); US-77 ist NICHT blockierend — US-75 läuft auf bestehenden Locations unabhängig von US-77.

**Epic — Kind-Tickets:**

| Ticket | Inhalt | Abh. | Status |
|--------|--------|------|--------|
| **TASK-44** | QA-Datenmodell: Flags, Tabellen, Geo-Hash | TASK-17 ✅ | ✅ Erledigt (archiviert) |
| **TASK-45** | Azimut via Overpass API (Gebäude-Footprints → Horizon) | TASK-44 | ✅ Done (v2.0.x, 2026-06-28) |
| **TASK-46** | LLM-Beschreibungen (via Mistral AI) | TASK-44 | ✅ Done (v1.20.4, 2026-06-28) |
| **TASK-47** | Brennweiten-Auto-Calc (Geometrie) | TASK-44 | ✅ Done (v2.0.x, 2026-06-28) |
| **TASK-48** | QA-Cron-Routine: Change-Detection + Scheduler | TASK-45+47 | ✅ Done (v2.0.x, 2026-06-28) |

**Sequenzierung:**
```
TASK-44 ──▶ TASK-45 (Azimut)    ┐
        ──▶ TASK-46 (LLM)       ├──▶ TASK-48 (Cron)
        ──▶ TASK-47 (FL-Calc)   ┘
```

---

### TASK-53 · Live-Nutzerdaten periodisch nach Dev spiegeln `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-04 |

**Beschreibung:** Regelmäßiger (idealerweise automatischer) Mechanismus, der die durch Nutzung stetig wachsenden Live-Daten in die Dev-Umgebung überträgt und dortige Testdaten überschreibt. Ziel: realistischere Testdaten in Dev, um Auswirkungen auf Performance, Datenspeicherung und Nutzerverträglichkeit (z. B. längere Ladezeiten oder Berechnungen) sichtbar zu machen, die mit synthetischen Testdaten nicht auffallen würden.

**Bezug:** Grenzt an US-75 [x] (Epic User/Backend-Datensync: QA-Automatisierung für Location-Metadaten wie Azimut, Beschreibungen, Brennweite) — dort werden bestehende Locations inhaltlich angereichert/geprüft, hier geht es um die reine Datenübertragung Live→Dev als Kopie/Snapshot. Keine Dublette, kein direkter Abhängigkeitspfad; beide betreffen Nutzerdaten-Pflege, aber unterschiedliche Ziele.

**Scope:**
- **Eingeschlossen:** Ein manuell anzustoßender Übertragungsvorgang, der den kompletten aktuellen Datenbestand der Live-App (Standorte, Bewertungen, Vor-Ort-Meldungen, QA-Zustände) als Kopie in die lokale Entwicklungsumgebung von Stephan bringt und dortige Testdaten vollständig ersetzt.
- **Ausgeschlossen:** Automatischer Zeitplan (Cron) für den ersten Wurf — siehe ⚠️ Annahme unten. Rückrichtung Dev→Live (nie Bestandteil). Anonymisierung/Pseudonymisierung von `device_id` (siehe Datenschutz-Prüfung — nicht nötig, da keine personenbezogenen Daten). Ein Web-UI oder Admin-Knopf für den Sync (v1 ist ein Terminal-Befehl).

**⚠️ Annahme (v1-Slice, bitte bestätigen):** „Regelmäßig (idealerweise automatisch)" wird in dieser ersten Ausbaustufe als **manuell auf Zuruf ausgeführtes Skript** umgesetzt, nicht als automatischer Cron-Job. Begründung: Ein automatischer Job auf dem Live-Server, der unbeaufsichtigt Stephans lokale Testumgebung überschreibt, ist riskanter (Gefahr: manuell angelegte Test-Locations gehen unbemerkt verloren, siehe Pre-Mortem Szenario 1) und für ein Priorität-Niedrig-Task unverhältnismäßig aufwendig (Cron auf Live bräuchte SSH-Vertrauensstellung Live→Stephans Mac oder einen Zwischenspeicher-Endpoint). Automatisierung ist als Ausbaustufe 2 im Options-Abschnitt festgehalten, aber nicht Teil dieses Slices.

---

**Example Mapping:**

📏 **Regel 1 — Der Sync ist eine vollständige Kopie, keine Zusammenführung.** Alle nutzereditierbaren Daten aus der Live-Datenbank (Standorte, Korrekturen, Bewertungen, Vor-Ort-Meldungen, QA-Zustände) ersetzen die entsprechenden Dev-Daten vollständig. Es wird nichts zusammengeführt oder abgeglichen.
- 🟢 Stephan hat in Dev testweise 5 eigene Test-Standorte angelegt, auf Live gibt es 20 echte Nutzer-Standorte → nach dem Sync sind in Dev die 20 Live-Standorte vorhanden, die 5 Test-Standorte sind weg.
- 🟢 Ein Standort wurde auf Live von einem Nutzer mit 3 Sternen bewertet → nach dem Sync zeigt Dev dieselbe Bewertung.

📏 **Regel 2 — Der Sync läuft nur in eine Richtung: Live → Dev.** Es gibt keinen Pfad, über den Dev-Daten (auch versehentlich) auf Live landen.
- 🟢 Stephan verändert in Dev testweise einen Standort-Namen, führt danach den Sync aus → die Änderung wird überschrieben (durch den Live-Stand), Live bleibt komplett unberührt.
- 🟢 Der Sync-Befehl fragt vor der Ausführung, welche Richtung gemeint ist bzw. ist so gebaut, dass „versehentlich falschrum" technisch gar nicht möglich ist (feste Quelle Live, festes Ziel Dev, keine Parameter-Vertauschung).

📏 **Regel 3 — Der Sync bringt einen Schnappschuss vom aktuellen Live-Stand, keine laufende Synchronisation.** Nach dem Sync entwickeln sich Live und Dev wieder unabhängig, bis der nächste Sync manuell angestoßen wird.
- 🟢 Direkt nach dem Sync ändert ein Nutzer auf Live eine Bewertung → diese Änderung taucht in Dev erst beim nächsten Sync-Lauf auf, nicht sofort.

📏 **Regel 4 — Der Sync-Vorgang selbst darf die Live-App nicht spürbar verlangsamen.** Die Datenmenge ist heute klein (SQLite-Datei im niedrigen MB-Bereich), das Kopieren geschieht ohne Schreibsperre auf der Live-Datenbank.
- 🟢 Während des Sync-Vorgangs kann ein Nutzer weiterhin auf Live eine Location bewerten oder eine Meldung abschicken, ohne Fehler oder Wartezeit zu bemerken.

❓ **Questions:** keine offen (v1-Slice als ⚠️-Annahme markiert, blockiert nicht — Bestätigung folgt im Weg-Gate).

---

**Akzeptanzkriterien (erlebbares Verhalten):**
- [ ] **AK-1 (vollständige Kopie):** Nach einem Sync-Lauf zeigt die lokale Dev-Umgebung exakt die Standorte, Bewertungen, Vor-Ort-Meldungen und QA-Zustände, die zum Sync-Zeitpunkt auf der Live-App vorhanden waren.
- [ ] **AK-2 (alte Dev-Testdaten sind weg):** Manuell in Dev angelegte Test-Standorte oder Test-Bewertungen, die es auf Live nicht gibt, sind nach dem Sync nicht mehr vorhanden.
- [ ] **AK-3 (Live bleibt unberührt):** Nach dem Sync sind auf der Live-App keinerlei Veränderungen sichtbar — weder an Standorten noch an sonstigen Daten. Die Live-App war während des gesamten Vorgangs normal nutzbar.
- [ ] **AK-4 (Sicherheitsnetz vor Überschreiben):** Vor jedem Sync wird der bisherige Dev-Datenstand automatisch weggesichert, sodass er bei Bedarf wiederhergestellt werden kann, falls der Sync versehentlich zur falschen Zeit lief oder ein noch benötigter Testfall verloren ging.
- [ ] **AK-5 (Rückmeldung):** Nach Abschluss des Sync-Laufs bekommt Stephan eine klare Bestätigung, wie viele Standorte/Bewertungen/Meldungen übertragen wurden bzw. eine klare Fehlermeldung, falls etwas schiefging.
- [ ] Edge Case: **Live-Datenbank ist zum Sync-Zeitpunkt gerade in Benutzung** (Nutzer schreibt gleichzeitig eine Bewertung) → der Sync-Lauf schlägt dadurch nicht fehl und die Live-Aktion geht nicht verloren.
- [ ] Edge Case: **Verbindung zum Live-Server bricht während der Übertragung ab** → Dev bleibt beim alten (weggesicherten) Stand, es entsteht kein halb-überschriebener, korrupter Zwischenzustand.

---

**Pre-Mortem:**

📎 **Code-Verifikation (2026-07-04, gelesen, nicht erinnert):**
- **Umgebungstrennung existiert bereits:** `backend/data/store.py` Z.34–40 liest `FOTOALERT_ENV` (Default `"prod"`) und wählt danach den DB-Pfad: `prod` → `backend/data/fotoalert.db`, alles andere → `backend/data_dev/fotoalert.db`. **Bestätigt:** Live und Dev sind bereits sauber getrennte SQLite-Dateien, keine gemeinsame DB, kein Risiko einer versehentlichen Direktverbindung.
- **Dev-DB existiert bereits real:** `backend/data_dev/` enthält aktuell `test.db` — Stephans laufende lokale Testdatenbank. Ein Sync würde **genau diese Datei** ersetzen. Zusätzlich enthält der Ordner sehr viele `.fuse_hidden*`-Artefakte (Hinweis auf ein Netzwerk-/Sandbox-Dateisystem mit häufigen Schreib-Locks) — beim Dateiersatz auf dem echten Mac (nicht in der Sandbox) ist das ohne Bedeutung, wird hier nur als Beobachtung festgehalten.
- **Was „Live-Daten" konkret sind:** `backend/data/store.py` Z.45–122 zeigt die vollständigen Tabellen: `custom_locations` (User-Standorte), `location_overrides` (Korrekturen an Standard-Locations), `location_verifications` (Vor-Ort-Meldungen inkl. Freitext-`comment`), `location_ratings` (Sterne pro `device_id`), `device_tokens` (Push-Token pro `device_id`), `camera_profiles` (Kameraprofil pro `device_id`), `location_qa_state`/`location_qa_values` (Auto-QA-Zustände aus US-75). **Kein** Tabellenfeld für Namen, E-Mail-Adressen, Postanschriften oder Zahlungsdaten.
- **Datenschutz-Prüfung (Ergebnis):** `backend/auth.py` zeigt ein rollenbasiertes Login (nur zwei globale Passwörter „host"/„user" aus `.env`, Token ist rollen- nicht personengebunden). Es gibt kein Nutzerkonto-Konzept mit Namen/E-Mail. Die einzige personenbezogene-artige Kennung ist `device_id` (ein clientseitig generierter, nicht direkt auf eine Person rückführbarer String) in `location_ratings`, `device_tokens`, `camera_profiles`. Freitext-Felder (`location_verifications.comment`) könnten theoretisch von Nutzern selbst eingegebene Namen enthalten, das ist aber nicht vom System vorgesehen. **Einschätzung: kein klassisches personenbezogenes Datenschutzproblem im Sinne der DSGVO-Betroffenenrechte, aber Freitextfelder sind nicht auszuschließende Restrisiko-Quelle** — sollte im Weg-Gate kurz bestätigt werden, ist aber kein Blocker für v1.
- **Kein bestehendes Sync-/Export-Skript:** Weder unter `FotoAlert/tools/` noch per Namenssuche (`*sync*`, `*mirror*`) existiert bereits ein Live→Dev-Datenübertragungsmechanismus. `tools/sync_kanban.py` ist ein unabhängiges Skript für das Kanban-Board, nicht für App-Daten. **Bestätigt: TASK-53 baut komplett neu, keine Wiederverwendung eines bestehenden Sync-Wegs.**
- **Backup-Mechanismus als Vorbild vorhanden:** `backend/data/backup.py` zeigt ein bereits etabliertes Muster für „Datei-Snapshot mit Aufbewahrungslimit" (`snapshot_before_precompute()`, max. 7 lokale Kopien, No-Op wenn `FOTOALERT_ENV != "prod"`). Dasselbe Snapshot-Prinzip lässt sich 1:1 für „Dev-DB vor Überschreiben sichern" wiederverwenden (AK-4).
- **Server-Zugriff:** Live läuft auf Hetzner (IP 167.233.138.36, App-Root `/opt/fotoalert/app/FotoAlert/`, DB unter `backend/data/fotoalert.db`). Git-Ops laufen laut Memory über den `fotoalert-server`-User; für einen reinen Lesezugriff (DB-Kopie ziehen) ist ebenfalls der `fotoalert-server`-User zu verwenden, nicht root (root nur für systemd/Dateisystem-Notfälle).

💀 **Szenario 1 — Stephans manuell angelegte Dev-Testdaten gehen unbemerkt verloren.**
   Auslöser: Sync läuft (versehentlich oder geplant), während gerade ein wichtiger, noch nicht dokumentierter Testfall in Dev existiert.
   Frühwarnung: Stephan sucht nach einem Test-Standort und findet ihn nicht mehr.
   Gegenmaßnahme: Automatisches Wegsichern des alten Dev-Stands vor jedem Sync (AK-4), plus deutliche Bestätigungsmeldung vor dem eigentlichen Überschreiben (kein „stiller" Lauf ohne Rückfrage in v1).

💀 **Szenario 2 — Sync-Richtung wird verwechselt, Dev überschreibt Live.**
   Auslöser: Kopier- oder Fernzugriffsbefehl mit vertauschten Quell-/Ziel-Parametern.
   Frühwarnung: Live-App zeigt plötzlich Stephans Test-Standorte statt echter Nutzerdaten.
   Gegenmaßnahme: Feste, im Skript fest verdrahtete Richtung (Quelle immer Live-Pfad auf dem Server, Ziel immer der lokale `data_dev`-Pfad), keine Kommandozeilen-Parameter, die die Richtung umkehren könnten; zusätzlich Kopiervorgang nur lesend auf der Live-Seite (Live-Datei wird nie beschrieben, nur gelesen).

💀 **Szenario 3 — Der Sync-Vorgang belastet oder blockiert den Live-Server.**
   Auslöser: Kopieren einer SQLite-Datei während reger Schreibaktivität, oder ein rechenintensiver Exportschritt im selben Prozess wie der FastAPI-Server.
   Frühwarnung: Health-Check reagiert während des Sync-Fensters langsamer.
   Gegenmaßnahme: SQLite läuft bereits im WAL-Modus (`store.py` Z.43 `PRAGMA journal_mode=WAL`) — das erlaubt gleichzeitiges Lesen der Datenbankdatei ohne Schreibsperre; die Kopie wird komplett außerhalb des Server-Prozesses angestoßen (eigener SSH-Befehl/Cronjob, kein neuer FastAPI-Endpoint, der im Event-Loop läuft) → keine Event-Loop-Blockade wie in TASK-48 Szenario 4.

💀 **Szenario 4 — Python-Versionsunterschied (3.9 Live vs. 3.10 Sandbox) bricht ein gemeinsames Skript.**
   Auslöser: Ein Hilfsskript, das sowohl auf dem Server als auch lokal läuft, nutzt moderne Syntax (`str | None`, `match`-Statement).
   Frühwarnung: Skript funktioniert lokal, crasht aber auf dem Server mit `SyntaxError`.
   Gegenmaßnahme: Falls ein Python-Hilfsskript entsteht (nicht zwingend, siehe Optionen), durchgängig 3.9-kompatible Syntax verwenden (`from __future__ import annotations`, `Optional[...]` statt `X | None`) — analog zur bestehenden Konvention in `auth.py`/`backup.py`.

💀 **Szenario 5 — Falsche SSH-Rechte verhindern den Lesezugriff oder erlauben versehentlich mehr als nötig.**
   Auslöser: Sync-Skript nutzt den root-User statt des vorgesehenen `fotoalert-server`-Users, oder umgekehrt hat `fotoalert-server` keine Leserechte auf die DB-Datei.
   Frühwarnung: `Permission denied` beim ersten Testlauf, oder (schlimmer) ein Skript mit unnötig weiten Root-Rechten.
   Gegenmaßnahme: Sync-Skript nutzt ausschließlich `ssh fotoalert-server` für den Lesezugriff auf die DB-Datei (analog zur bestehenden Konvention für Git-Ops); root wird nicht angefasst.

💀 **Szenario 6 — Freitext-Meldungen enthalten unerwartet sensible Angaben.**
   Auslöser: Ein Nutzer trägt in eine Vor-Ort-Meldung (`location_verifications.comment`) versehentlich einen Namen, eine Telefonnummer o.ä. ein.
   Frühwarnung: Beim Sichten der Dev-Daten fällt ein ungewöhnlich persönlicher Kommentar auf.
   Gegenmaßnahme: Kein technischer Automatismus in v1 (Aufwand/Nutzen unverhältnismäßig bei Priorität Niedrig); stattdessen als bekanntes Restrisiko dokumentiert (siehe Datenschutz-Prüfung) — Dev-Umgebung bleibt wie bisher nur für Stephan zugänglich, kein Weitergabe-Szenario.

---

**Architektur-Analyse:**
- **Betroffene Komponenten (kein bestehender Code wird geändert, nur neue Werkzeuge kommen hinzu):**
  - `backend/data/store.py` — nur als Referenz für Tabellenstruktur, **keine Codeänderung** nötig (Sync kopiert die Datei als Ganzes, spricht nicht einzelne Tabellen an).
  - `backend/data/backup.py` — Vorbild für das Snapshot-Prinzip (AK-4); ggf. Erweiterung um eine Dev-Sicherungsfunktion nach demselben Muster, oder eigenständiges kleines Skript in `FotoAlert/tools/`.
  - Neues Werkzeug (Name/Ort je nach gewählter Option) unter `FotoAlert/tools/` — auf der Mac-Seite ausgeführt, holt die Live-DB-Datei per SSH vom Server und ersetzt die lokale `backend/data_dev/fotoalert.db`.
  - Server-seitig keine Codeänderung nötig — es wird nur lesend auf die bestehende `backend/data/fotoalert.db` zugegriffen.
- **Datenmenge:** SQLite-Datei, aktuell überschaubare Nutzerbasis (wenige Standorte/Bewertungen) → Dateigröße im niedrigen MB-Bereich, unkritisch für Übertragungsdauer.
- **Python-3.9-Konformität:** Falls das Sync-Werkzeug in Python geschrieben wird (statt reinem `scp`/`rsync`-Shellbefehl), muss es 3.9-kompatibel sein, da es potenziell auch serverseitig laufen könnte (auch wenn v1 rein clientseitig von Stephans Mac aus gedacht ist).

---

**Implementierungsoptionen:**

### Option A — Manuelles Kopier-Skript (SCP/rsync) von Stephans Mac aus (Empfehlung)
- Vorgehen: Ein kleines Skript (Shell oder Python) unter `FotoAlert/tools/`, das Stephan bei Bedarf startet. Es sichert zuerst die aktuelle Dev-Datenbank lokal weg (Zeitstempel-Kopie, Aufbewahrung z.B. letzte 5 Stände — analog zum bestehenden Snapshot-Prinzip in `backup.py`), holt danach die aktuelle Live-Datenbankdatei per `ssh fotoalert-server`/`scp` und ersetzt damit die lokale Dev-Datenbank. Am Ende eine kurze Zusammenfassung (Anzahl Standorte/Bewertungen/Meldungen vorher/nachher).
- App-Wirkung für Stephan: Ein einziger Befehl im Terminal, danach zeigt der lokale Dev-Server beim nächsten Start exakt den aktuellen Live-Datenstand — alte Testdaten sind weg, aber vorher automatisch gesichert.
- Betroffene Dateien: neues Skript in `FotoAlert/tools/`, keine Änderung an bestehendem Code.
- Vorteile: Kleinster Eingriff, kein neuer Server-Prozess, keine neue Angriffsfläche auf der Live-App, volle Kontrolle durch Stephan (läuft nur wenn er es will — vermeidet Szenario 1/2), nutzt bestehende SSH-Konvention (`fotoalert-server`-User).
- Nachteile/Risiken: Kein automatischer Zeitplan (entspricht der ⚠️-Annahme oben — bewusster Trade-off für Priorität Niedrig).
- Aufwand: klein.

### Option B — Automatisierter Cron-Job auf dem Live-Server, der periodisch nach Dev pusht
- Vorgehen: Ein Scheduler-Job auf dem Hetzner-Server exportiert periodisch die Live-DB und überträgt sie aktiv auf Stephans Mac (z.B. per SSH-Push) oder legt sie an einem Zwischenort ab, von dem Stephans Mac sie zieht.
- App-Wirkung: identisch zu Option A, nur ohne manuellen Anstoß — Dev aktualisiert sich „von selbst".
- Vorteile: erfüllt die „idealerweise automatisch"-Formulierung im Ticket wörtlich.
- Nachteile/Risiken: Der Live-Server bräuchte eine Vertrauensstellung/Zugangsdaten Richtung Stephans privatem Mac (SSH-Key vom Server zum Mac, oder der Mac müsste dauerhaft erreichbar sein) — ungewöhnliche und sicherheitstechnisch unschöne Richtung (Server → privates Endgerät); höherer Betriebsaufwand für ein Priorität-Niedrig-Task; erhöht das Risiko aus Szenario 1 (unbeaufsichtigtes Überschreiben zu einem ungünstigen Zeitpunkt).
- Aufwand: groß.

### Option C — API-basierter Export-/Import-Endpoint
- Vorgehen: Ein neuer, host-geschützter Endpoint auf der Live-App liefert einen Datenexport (z.B. als JSON oder DB-Datei-Download); ein Gegenstück lokal importiert diesen in die Dev-DB.
- App-Wirkung: identisch zu Option A, aber über HTTP statt SSH/SCP.
- Vorteile: kein SSH-Zugriff auf Dateisystemebene nötig.
- Nachteile/Risiken: Neue Angriffsfläche auf der Live-App (zusätzlicher Endpoint, der die komplette Datenbank exportierbar macht — muss besonders sorgfältig abgesichert sein); mehr Code als Option A für denselben Nutzen, da die SSH-Konvention (`fotoalert-server`-User, siehe Memory) bereits für genau diesen Zweck existiert.
- Aufwand: mittel.

✅ **Empfehlung: Option A** — sie ist die einfachste Lösung, die alle Akzeptanzkriterien erfüllt, führt keine neue Angriffsfläche auf der Live-App ein, nutzt die bereits etablierte SSH-Konvention und das bereits vorhandene Snapshot-Prinzip aus `backup.py`. Die im Ticket gewünschte Automatisierung wird bewusst als spätere Ausbaustufe zurückgestellt (⚠️ Annahme), da ein automatischer Cron in Richtung eines privaten Mac (Option B) unverhältnismäßig viel Betriebsrisiko für ein Priorität-Niedrig-Task bedeutet. Bei Bedarf kann Option A später um einen lokalen `launchd`/Cron-Aufruf auf Stephans Mac ergänzt werden (Mac zieht periodisch selbst, statt dass der Server pusht) — das wäre eine risikoärmere Variante von „automatisch" als Option B.

---

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (4 Regeln, Examples belegt, keine offenen Questions, v1-Slice als Annahme markiert)
- [x] Pre-Mortem durchgeführt (6 Szenarien, je Gegenmaßnahme in AK/Plan verankert)
- [x] Architektur analysiert: `data/store.py` (Umgebungstrennung + Tabellenstruktur), `data/backup.py` (Snapshot-Vorbild), `auth.py` (Datenschutz-Prüfung), kein bestehendes Sync-Skript gefunden
- [x] Designer-Check: nicht visuell (reines Dev-Tooling ohne App-UI) → übersprungen
- [x] Implementierungsoptionen: A (manuelles Kopier-Skript, Empfehlung) / B (automatischer Server-Cron) / C (API-Export-Endpoint)
- [x] Empfehlung **Option A** — Weg-Gate via Board (Lane „Ready for Dev") freigegeben (2026-07-04), inkl. Annahme „v1 manuell statt automatisch" bestätigt → Ready for Dev

**Testplan:**
- [ ] Automatisiert (`backend/tests/test_task53_dev_sync.py`, Ticket-ID im Docstring, soweit ohne echten Server-Zugriff testbar):
  - Sicherungsfunktion legt vor dem Ersetzen eine Zeitstempel-Kopie der alten Dev-DB an (AK-4).
  - Nach simuliertem Ersetzen enthält die Dev-DB exakt den Inhalt der Quelldatei, alte Dev-only-Einträge sind weg (AK-1/AK-2).
  - Abbruch mitten im Kopiervorgang (simulierter Fehler) lässt die alte Dev-DB unangetastet zurück, kein korrupter Zwischenzustand (Edge Case „Verbindungsabbruch").
- [ ] Manuell: Sync-Befehl gegen die echte Live-DB auf dem Server ausführen, danach lokalen Dev-Server starten (`http://localhost:8000`) und prüfen, dass die angezeigten Standorte/Bewertungen dem aktuellen Live-Stand entsprechen; parallel auf der echten Live-App (fotoalert.stephanschumann.com) bestätigen, dass keinerlei Veränderung sichtbar ist (AK-3).
- [ ] Regression: bestehender lokaler Dev-Workflow (Server-Start, `Application startup complete.`) funktioniert nach dem Sync unverändert; kein bestehender Endpoint oder Cron-Job auf Live wird durch den rein lesenden Zugriff beeinträchtigt.

---

**Umsetzung (2026-07-04, Option A):**
- Neu: `FotoAlert/tools/sync_dev_from_live.py` — Kommandozeilen-Werkzeug für Stephans Mac. Sichert die lokale Dev-DB per Zeitstempel-Snapshot (max. 5 Stände, `backend/data_dev/snapshots/`), holt danach die Live-DB per `scp` über den `fotoalert-server`-User (rein lesend), lädt sie in eine temporäre Datei und ersetzt die Dev-DB erst bei vollständigem Erfolg atomar (`Path.replace`). Richtung (Live→Dev) sowie Quell-/Zielpfade sind fest im Code verdrahtet, keine CLI-Parameter dafür. Gibt am Ende Zeilenzahlen je Kerntabelle (`custom_locations`, `location_overrides`, `location_verifications`, `location_ratings`) vorher/nachher aus.
- Neu: `FotoAlert/backend/tests/test_task53_dev_sync.py` — 12 automatisierte Tests (Snapshot-Erstellung + Retention, atomarer Ersatz inkl. WAL/SHM-Bereinigung, Verbindungsabbruch-Simulation über gemocktes `subprocess.run`, Zusammenfassungs-Zählung). Alle 12 grün, keine Regression in Nachbar-Tests (`test_task45_azimuth.py`, `test_task43_qa_model.py` weiterhin grün).
- Kein bestehender Code geändert (`store.py`, `backup.py` nur als Vorbild/Referenz gelesen, nicht angefasst).
- Nicht automatisiert testbar (kein Sandbox-Netzwerkzugriff auf den Hetzner-Server): der echte `scp`-Verbindungstest gegen Live sowie der End-to-End-Testplan-Punkt „Manuell" bleiben ein manueller Schritt für Stephan.

---

### TASK-54 · Prüfen: dauerhafter Festplatten-Cache für Wetterkarten-PNGs `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | ToDo |
| **Erstellt** | 2026-07-04 |

**Beschreibung:** Prüfen, ob ein dauerhafter Festplatten-Cache für die Wetterkarten-PNGs auf dem FotoAlert-Server sinnvoll ist. Laut Code-Analyse zu BUG-59 werden die Wetterkarten-PNGs aktuell nur in einem Arbeitsspeicher-Dictionary im Backend-Prozess gehalten (`_weather_map_png` in `backend/main.py`) — kein erkennbarer Disk-Cache im Code gefunden. Das bedeutet: Nach einem Server-Neustart ist der Wetterkarten-Cache leer, bis er neu aufgebaut wird (Dauer abhängig von der Datenquelle). Stephan hat bestätigt, dass auf dem Server ausreichend Speicherplatz vorhanden ist — ein Disk-Cache wäre also machbar.

**Bezug:** Der fehlende Disk-Cache wurde als Nebenbefund in der **BUG-59**-Analyse [ ] (Ready for Dev, „Zeitregler im Karten-Tab: Kein Wolken-/Regen-Overlay sichtbar") dokumentiert (dort Abschnitt „Grenzen dieser Analyse" sowie Architektur-Analyse: „Kein Cache-Verzeichnis auf Datei-Ebene identifiziert"), dort aber bewusst nicht gelöst — BUG-59 behandelt ein Sichtbarkeits-/Wahrnehmungsproblem des Overlays (Zoom + Farbskala), dieses Ticket behandelt die separate Frage der Cache-Persistenz nach einem Neustart. Keine Vermischung mit BUG-59 vorgesehen. Grenzt außerdem ab zu: **US-112** [x] (liefert die Wetter-Overlay-Daten/-Bilder selbst inkl. bestehendem Prozess-Speicher-Cache-Muster, aber kein Disk-Cache) und **BUG-58** [x] (reine Zoom-Umstellung, anderer Codepfad, nicht betroffen). Kein Bezug zu **TASK-50** (Service-Worker Auto-Update — betrifft den Frontend-Browser-Cache der Web-App, nicht den Backend-Wetterkarten-Cache) und keine Überschneidung mit den Feed-/Kalender-/Scout-Caches (`opportunities.json`, `calendar.json`, `discover.json`) — der Wetterkarten-PNG-Cache ist ein eigenständiger, bislang rein prozessgebundener Cache-Mechanismus.

---

### TASK-55 · Server-Backup um location_images/ erweitern `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-07-04 |

**Beschreibung:** Das bestehende Backup-Verfahren (`backend/data/backup.py`) sichert aktuell nur die SQLite-Datenbank bzw. deren JSON-Export (`custom_locations.json`, `location_overrides.json` via `backup_after_edit()`) sowie lokale DB-Snapshots vor Precompute-Läufen (`snapshot_before_precompute()`) — verifiziert per Code-Lesung, `location_images/` wird an keiner Stelle referenziert oder mitgesichert. Der mit US-120 eingeführte Ordner mit hochgeladenen Beispielbildern pro Location ist damit von keinem der beiden Sicherungspfade abgedeckt und ginge bei einem Server-Ausfall verloren.

**User Story:** Als Host/Betreiber der FotoAlert-App, möchte ich, dass hochgeladene Beispielbilder beim Server-Backup mitgesichert werden, sodass ich sie nach einem Server-Ausfall wiederherstellen kann und keine von Nutzern/Admin hochgeladenen Bilder verloren gehen.

**Bezug:** US-120 [~] (In Test) — führte `location_images/` sowie den Upload-Endpoint ein und wies in der Implementierungsnotiz selbst auf diese Lücke hin („Backup sichert bisher nur SQLite, nicht `location_images/` — eigenes Ticket vorschlagen?"). Kein Bezug/keine Überschneidung zu TASK-48 (Epic Datensync — behandelt automatisierte QA/Anreicherung von Location-Metadaten wie Azimut/Beschreibung/Brennweite, nicht Datei-Backup) und zu TASK-53 (Dev-Sync-Werkzeug Live→Dev — nutzt das Snapshot-Prinzip aus `backup.py` nur als Vorbild für einen anderen Zweck, ändert `backup.py` nicht). Kein bestehendes BUG-Ticket zu diesem Thema gefunden.

---

### TASK-56 · DB-Snapshot-Ordner aus Git-Tracking nehmen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-07-05 |
| **In Progress seit** | 2026-07-05 |
| **Abgeschlossen** | 2026-07-05 |

**Beschreibung:** Vor jedem Precompute-Lauf legt `snapshot_before_precompute()` (`backend/data/backup.py`) automatisch eine DB-Kopie unter `backend/data/snapshots/` an (max. 7, ältere räumt das Skript selbst weg). Der Ordner fehlte in `.gitignore`, dadurch wurden bei früheren Commits (`10ce891`, `4225991`) einzelne Snapshots versehentlich mitgecheckt. Räumt das Skript sie später lokal auf, zeigt Git sie als „deleted"; neue, noch ungecheckte Snapshots als „untracked" — das sorgte bei Releases für Verwirrung. Kein Datenverlust, reines Ignore-/Tracking-Problem, ~0,8 MB Historie betroffen.

**Umsetzung:** `.gitignore` um `backend/data/snapshots/` ergänzt. Die 7 bereits getrackten (aber lokal schon wieder gelöschten) Snapshot-Einträge müssen noch per `git rm --cached` aus der Versionsverfolgung genommen und committet werden — dieser Schritt läuft über Stephans eigenes Terminal, nicht in der Sandbox.

---

### TASK-57 · refactor_check.py: Wurzelursache der Falsch-Positive bei langen JS-Funktionen behoben `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-07-05 |
| **Abgeschlossen** | 2026-07-05 |

**Beschreibung:** Aus der Retrospektive zu US-117: Der „lange JS-Funktion"-Check in `tools/refactor_check.py` maß die Länge einer Funktion bisher als Abstand bis zur *nächsten erkannten* Funktion, nicht bis zur tatsächlichen schließenden `}` (TASK-32-Limitation). Das erzeugte bei verschachtelten Closures/IIFEs regelmäßig Falsch-Positive (100–1400 „Zeilen" für tatsächlich 1–12-zeilige Funktionen), die bisher einzeln per Namens-Ignorelist unterdrückt werden mussten (zuletzt bei US-117 für `localBoundsRadius`, davor TASK-42/TASK-49/TASK-43). Diese Wurzelursache wurde jetzt behoben statt erneut nur die Ignorelist zu erweitern.

**Umsetzung:** Neue Hilfsfunktionen `_strip_js_noncode()` (entfernt String-/Kommentarinhalte zeilenübergreifend, State-Machine) und `_function_real_length()` (echte Klammer-Zählung ab Funktionssignatur bis zur schließenden `}`) in `tools/refactor_check.py`. Die alte Distanz-Heuristik dient nur noch als Fallback, wenn keine öffnende `{` gefunden wird (einzeilige Arrow-Functions ohne Block-Body). `FRONTEND_LONG_FN_IGNORELIST` bleibt als Sicherheitsnetz bestehen, sollte aber mit dem Fix nicht mehr wachsen müssen.

**Verifikation:** `python3 tools/refactor_check.py --report` nach dem Fix meldet nur noch 2 Funde: `backend/main.py::startup` (84 Zeilen, bereits bekannt, TASK-51) und neu `web/index.html::mkCloudCompassSvg` (144 Zeilen, **echter** Fund — vorher durch die verschachtelte `sectorPath`-Closure und die alte Distanz-Heuristik verdeckt/falsch zugeordnet, jetzt korrekt der äußeren Funktion zugerechnet). Alle bisher ignorelisteten Funktionsnamen werden jetzt korrekt unter dem 100-Zeilen-Threshold gemessen (kein Rückgriff auf die Ignorelist mehr nötig, sie bleibt nur als Sicherheitsnetz stehen). Kein App-Code geändert, kein Deploy nötig (reines Analyse-Tool).

**Hinweis:** `mkCloudCompassSvg` (144 Zeilen) ist ein neuer, echter Befund und noch nicht bearbeitet — bei Bedarf als eigenes Ticket in die Inbox aufnehmen.

---

### TASK-45 · Idealer Azimut automatisch aus Gebäude-Footprints `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |
| **Epic** | US-75 |

**Beschreibung:** Für Locations ohne kuratierten Idealbereich soll das System aus frei verfügbaren Kartendaten ableiten, aus welcher Himmelsrichtung Sonne oder Mond hinter dem Motiv stehen müssten, damit die App auch bei neuen oder per Backend angelegten Spots automatisch einen sinnvollen „idealer Azimut"-Bereich anzeigt — ohne dass jemand ihn von Hand eintragen muss.

**(Dies ist das vertieft analysierte erste Kind — volle Spec.)**

**Example Mapping:**
- 📏 Rule: Wenn ein Spot Fotografen-Standort und Motiv-Koordinate hat, leitet das System die Blickrichtung zum Motiv ab und macht daraus einen Azimut-Bereich (Blickrichtung ± Toleranz).
  - 🟢 Beispiel: Ein neuer Spot zeigt von Nordwesten auf eine Kirche im Südosten. Das System schlägt automatisch einen Idealbereich um „Südost" vor; in der App erscheint dieser Bereich, ohne dass jemand ihn eingetragen hat.
- 📏 Rule: Wenn ein Mensch den Idealbereich bereits gepflegt (gesperrt) hat, fasst das System ihn nicht an.
  - 🟢 Beispiel: Ein redaktionell gepflegter Spot behält seinen Bereich, auch wenn der Auto-Lauf etwas anderes berechnen würde.
- 📏 Rule: Wenn die nötigen Geo-Daten fehlen oder die externe Karte nicht antwortet, ändert das System nichts und lässt den bestehenden Zustand stehen.
  - 🟢 Beispiel: Bei einem Spot ohne Motiv-Koordinate bleibt der Azimut leer statt mit einem Zufallswert gefüllt zu werden.
- ⚠️ Annahme: Toleranzbreite des Bereichs (z.B. ±15°) ist konventionell — Default vorgeschlagen, bitte bestätigen.
- ⚠️ Annahme: Reine Sichtlinie Standort→Motiv (Bearing) als Basis; eine echte Horizont-/Footprint-Analyse via Overpass ist die Ausbaustufe (siehe Optionen).

**Scope:**
- Eingeschlossen: Auto-Ableitung eines Azimut-Bereichs (min/max) je Location aus vorhandenen Geo-Feldern bzw. OSM-Footprint; Schreiben nur in die QA-Werte-Tabelle (`location_qa_values.ideal_azimuth_min/max`), Respektieren des `azimuth_lock`; Schreiben nur, wenn noch kein gesperrter/kuratierter Wert existiert.
- Ausgeschlossen: Cron-Orchestrierung (TASK-48), Frontend-/Admin-UI, Beschreibungstexte (TASK-46), Brennweiten (TASK-47), das Sichtbarmachen im täglichen Recompute (siehe Pre-Mortem-Risiko — wird in TASK-48 adressiert oder hier als Folge-AK markiert).

**Akzeptanzkriterien (erlebbares Verhalten):**
- [ ] Bei einem neu angelegten Spot mit Fotografen- und Motiv-Standort zeigt die App nach dem QA-Lauf automatisch einen plausiblen Idealbereich (grob die Richtung vom Standort zum Motiv), den vorher niemand eingetragen hatte.
- [ ] Ein Spot, dessen Idealbereich ein Mensch bewusst gesperrt hat, behält seinen Wert auch nach dem Auto-Lauf unverändert.
- [ ] Fehlt einem Spot die Motiv-Koordinate oder ist die externe Karte nicht erreichbar, bleibt der Idealbereich unverändert (kein falscher Wert, kein Absturz).
- [ ] Edge Case: Steht das Motiv exakt im Norden (Übergang 360°/0°), zeigt die App einen sinnvollen Bereich über die Nordgrenze hinweg statt eines widersprüchlichen „von 350 bis 10".
- [ ] Edge Case: Läuft die Auto-Ableitung zweimal hintereinander auf denselben unveränderten Spot, kommt beide Male derselbe Bereich heraus (keine zufälligen Sprünge).

**Pre-Mortem:**
- 💀 Szenario: Der berechnete Idealbereich erscheint in der App, aber Feed/Kalender zeigen weiter alte Chancen. Auslöser: Die tägliche Vorberechnung läuft als eigener Prozess und liest die QA-Werte nicht ein. Frühwarnung: Nach einem QA-Lauf ändert sich die App-Detailansicht, aber die Chancenliste nicht. Gegenmaßnahme: Sichtbarkeit im Recompute ist bekanntes Risiko (BUG-29-Muster) → in TASK-48 muss der Recompute die QA-Werte mitladen; hier als Folge-Risiko dokumentiert, nicht still angenommen.
- 💀 Szenario: Auto-Wert überschreibt einen guten redaktionellen Bereich. Auslöser: Lock wird nicht geprüft. Gegenmaßnahme: Schreiben nur wenn kein Lock und (Option) kein bestehender kuratierter Wert.
- 💀 Szenario: Externe Karte (Overpass) ist langsam/down und der ganze Lauf hängt. Gegenmaßnahme: kurzes Timeout, pro Spot abfangen, Fehler überspringen statt abzubrechen; reiner Bearing-Fallback ohne Netz.
- 💀 Szenario: Nord-Wraparound erzeugt unsinnigen Bereich (min > max). Gegenmaßnahme: Bereichsbildung explizit modulo 360 testen.
- 📎 Code-Verifikation (2026-06-28): `data/locations.py` PhotoLocation hat `observer_lat/lon`, `subject_lat/lon`, `ideal_azimuth_range` (Z.41–70). `data/store.py` `set_qa_values`/`get_qa_state`/`set_qa_lock` + Spalten `ideal_azimuth_min/max` vorhanden (TASK-44). Merge im Server via `main.py:_load_qa_values()` (Z.846). **Widerlegt die TASK-44-Notiz teilweise:** `precompute.py:main()` (Z.1005–1016) ruft `_apply_location_overrides()` + `_load_custom_locations()`, aber **kein** `load_all_qa_values()` → QA-Werte erreichen den täglichen Recompute heute nicht. `httpx` ist in `requirements.txt` vorhanden (Overpass-Calls möglich).

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `data/locations.py` (PhotoLocation-Geo-Felder), `data/store.py` (`set_qa_values`, Locks, Geo-Hash), `main.py:_load_qa_values()` (Merge), `precompute.py:main()` (Datenquelle des Recompute), `calculations/` (Azimut-Konsum in `_compute_possible_bodies`)
- [ ] Implementierungsoptionen: A (Bearing-only) / B (Overpass-Footprint) / C (Bearing-Basis + Overpass-Verfeinerung)
- [ ] Empfehlung: Option C

**Implementierungsoptionen:**
- **Option A — Sichtlinie (Bearing-only):** Idealbereich = berechnete Richtung Standort→Motiv ± feste Toleranz. Kein Netz, deterministisch, sofort. Schwäche: ignoriert Gebäudebreite/Ausdehnung — bei breiten Motiven zu eng. Aufwand: klein.
- **Option B — Overpass-Footprint:** OSM-Gebäudeumriss des Motivs holen, aus der Geometrie den horizontalen Winkelbereich (von links- bis rechtsaußen) ableiten. Genauer für ausgedehnte Bauwerke. Schwäche: Netzabhängig, Rate-Limits, nicht jedes Motiv hat einen Footprint, langsamer. Aufwand: mittel–groß.
- **Option C — Bearing-Basis + Overpass-Verfeinerung:** Immer Bearing als robuster Default; wo ein Footprint sauber ladbar ist, den Bereich darauf verbreitern. Netzfehler degradieren still auf Bearing. Aufwand: mittel.
- ✅ **Empfehlung: Option C** — liefert sofort für jeden Spot einen sinnvollen Wert (Qualität + Robustheit), nutzt Overpass nur als optionale Verbesserung, und der Netz-Fallback erfüllt das „bei API-Fehler nichts kaputt"-Kriterium aus dem Pre-Mortem.

**Testplan:**
- [ ] Automatisiert (`backend/tests/test_task45_azimuth.py`): Bearing-Berechnung gegen bekannte Koordinatenpaare; Nord-Wraparound (min>max → korrekt umgebrochen); Determinismus (zwei Läufe gleiches Ergebnis); Lock wird respektiert (gesperrter Wert bleibt); fehlende Motiv-Koordinate → kein Schreiben; Overpass-Fehler gemockt → Bearing-Fallback greift.
- [ ] Manuell: Neuen Test-Spot mit klarer Blickrichtung anlegen, QA-Lauf für diese ID auslösen, im Location-Detail prüfen dass der Idealbereich grob der Sichtlinie entspricht.

---

### TASK-46 · Standortbeschreibungen automatisch erzeugen (LLM) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |
| **Epic** | US-75 |

**Beschreibung:** Für Spots ohne (oder mit dürftiger) Beschreibung soll das System per Sprach-KI eine kurze, brauchbare Standortbeschreibung erzeugen, damit auch neu angelegte oder per Backend importierte Locations in der App nicht leer wirken.

**Scope:**
- Eingeschlossen: Generierung einer kurzen Beschreibung aus vorhandenen Fakten (Name, Motiv, Kategorie, Koordinaten); Schreiben nach `location_qa_values.description` unter Beachtung des `description_lock`; nur generieren wenn keine kuratierte/gesperrte Beschreibung existiert; Anthropic-API per HTTP (kein SDK — `httpx` vorhanden), API-Key aus Umgebungsvariable.
- Ausgeschlossen: Cron/Trigger (TASK-48), Admin-UI, mehrsprachige Texte, Bildanalyse.

**Akzeptanzkriterien (erlebbares Verhalten):**
- [ ] Ein neuer Spot ohne Text bekommt nach dem QA-Lauf eine kurze, zum Motiv passende deutsche Beschreibung, die in der App im Detail sichtbar ist.
- [ ] Ein Spot mit einer von Hand gepflegten (gesperrten) Beschreibung behält diese unverändert.
- [ ] Ist der KI-Dienst nicht erreichbar oder kein Schlüssel hinterlegt, bleibt der Spot ohne Auto-Text (keine halben/kaputten Texte, kein Absturz) und der Betreiber sieht im Log warum.
- [ ] Edge Case: Liefert die KI einen unbrauchbaren/leeren Text, wird nichts geschrieben statt Müll zu speichern.

**Pre-Mortem:**
- 💀 Szenario: Auto-Text überschreibt eine gute redaktionelle Beschreibung. Gegenmaßnahme: Lock + „nur wenn leer"-Regel, mit Test.
- 💀 Szenario: API-Key landet im Log oder Cache. Gegenmaßnahme: Key nur aus Env lesen, nie loggen, nie persistieren.
- 💀 Szenario: KI erfindet falsche Fakten (z.B. nicht existierende Bauwerke). Gegenmaßnahme: Prompt strikt auf gegebene Fakten beschränken, Länge begrenzen; im Scope als „kann fachlich danebenliegen" benennen, optional menschliche Freigabe.
- 💀 Szenario: Recompute zeigt neue Texte nicht (gleiches QA-Werte-Lade-Problem wie TASK-45). Gegenmaßnahme: in TASK-48 mitziehen.
- 📎 Code-Verifikation (2026-06-28): `set_qa_values(description=…)` + `description_lock` vorhanden (`data/store.py`, TASK-44); Merge via `main.py:_load_qa_values()` (Z.846 setzt `loc.description`). Kein `anthropic`-Paket in `requirements.txt` → Aufruf via `httpx` gegen die Messages-API. Kein API-Key-Handling im Code bisher (`grep` ANTHROPIC/API_KEY: nur FOTOALERT_*-Flags).

**📎 Code-Verifikation (2026-06-29, echter Code gelesen):**
- **Ablage vorhanden:** `location_qa_values.description TEXT` (`data/store.py` Z.118) + Sperr-Flag `location_qa_state.description_lock INTEGER` (Z.109). `set_qa_values(description=…)` ist bereits unterstützt (Z.698). `get_qa_state` liefert das Sperr-Flag. **Kein Schema-Umbau nötig.**
- **Merge bestätigt:** `main.py:_load_qa_values()` (Z.1014–1035) setzt `loc.description = qv["description"]` wenn der QA-Wert nicht None ist (Z.1034–1035). Start-Reihenfolge: `_load_qa_values()` vor `_load_location_overrides()` (Z.1056 ff.) → Override gewinnt über Auto-Wert.
- **Erweiterungspunkt:** `main.py` Z.731 — Kommentar „TASK-46 Erweiterungspunkt: hier `update_location_description(store, loc.id, …)`" — dort den Aufruf einhängen.
- **httpx vorhanden:** `qa_azimuth.py` nutzt `import httpx` lokal (Z.150) für den Overpass-Call. Dasselbe Muster für den Anthropic-HTTP-Call.
- **Kein anthropic-Paket:** `requirements.txt` enthält kein `anthropic`-Paket → direkter HTTP-Call gegen `https://api.anthropic.com/v1/messages` per `httpx`.
- **Lücke (das ist die Aufgabe):** Es gibt kein Schwester-Modul `data/qa_description.py`. `qa_azimuth.py` liefert die Vorlage: Sperr-Prüfung, Schreiben via `set_qa_values`, None bei Lock/fehlendem Ergebnis, keine Exception nach außen.

**Architektur-Analyse — betroffene Dateien:**
- **Neu:** `backend/data/qa_description.py` — Schwester zu `qa_azimuth.py`. Enthält:
  - `_build_prompt(loc_name, subject_name, category, observer_lat, observer_lon) → str` — Fakten-basierter Prompt auf Deutsch, max. 3 Sätze, strikt keine Erfindungen.
  - `_call_anthropic_api(prompt, api_key, timeout_s) → Optional[str]` — httpx-POST gegen `https://api.anthropic.com/v1/messages`, Header `x-api-key`, `anthropic-version: 2023-06-01`, model `claude-haiku-3-5` (klein, schnell, günstig). Key nie loggen. Bei jedem Fehler/Timeout → None.
  - `generate_description(loc_name, subject_name, category, observer_lat, observer_lon, api_key, timeout_s) → Optional[str]` — ruft die beiden oberen auf; gibt None zurück wenn Antwort leer/nur Whitespace.
  - `update_location_description(store, location_id, loc_name, subject_name, category, observer_lat, observer_lon, timeout_s) → Optional[str]` — prüft `description_lock`; schreibt via `set_qa_values(description=…)`; gibt None bei Lock/fehlendem Ergebnis; wirft nie.
- **Neu:** `backend/tests/test_task46_descriptions.py` — pytest-Tests (s.u. Testplan).
- **Geändert:** `backend/main.py` Z.731 — Aufruf von `update_location_description` mit Fehler-Isolierung analog zu Azimut/Brennweite einhängen (import hinzufügen).
- **Unverändert (nur referenziert):** `data/store.py` (Methoden + Schema reichen), `data/qa_azimuth.py` (Vorlage, kein Code-Umbau).

**Implementierungsoptionen:**

*Option A — Anthropic HTTP direkt, synchroner httpx-Call im QA-Modul (analog Azimut)*
- App-Wirkung: Nach dem QA-Lauf hat ein leerer Spot eine kurze deutsche Beschreibung, die sofort im Detail sichtbar ist. Kein zusätzlicher Schritt, kein manuelles Gate.
- Vorgehen: `qa_description.py` wie oben beschrieben; `_call_anthropic_api` blockiert kurz (1–5 s typisch) — wird wie Azimut via `asyncio.to_thread` im QA-Lauf aufgerufen, blockiert also nicht den Event-Loop.
- Risiken: (1) Kosten pro API-Call (Haiku ist günstig, ~$0.001/Spot); (2) KI kann faktisch danebenliegen (Gegenmaßnahme: Prompt auf übergebene Fakten beschränken); (3) Netz-Abhängigkeit (Gegenmaßnahme: Timeout + stilles None wie Overpass in Azimut).
- Aufwand: klein (1 Modul, ~120 Zeilen, Tests, 1 Zeile main.py).

*Option B — Pipeline mit Caching + Freigabe-Flag (zweistufig)*
- App-Wirkung: Beschreibung erscheint erst nach manueller Freigabe durch den Betreiber. Höhere Qualitätskontrolle, aber Latenz und Betreiber-Aufwand.
- Vorgehen: Generierter Text landet zunächst in einem „pending"-Status; ein Admin-Schritt setzt ein Freigabe-Flag; erst dann wird die Beschreibung sichtbar.
- Risiken: Erheblich mehr Infrastruktur (neue DB-Spalten, Admin-Endpunkt, UI) — weit außerhalb des Scopes. Fakten-Halluzinationen werden manuell gefangen, aber der Overhead ist hoch.
- Aufwand: groß; braucht Admin-UI (ausgeschlossen laut Scope).

✅ **Empfehlung: Option A** — schlanker Start, folgt exakt dem Azimut-Muster (Konsistenz), kein Infrastruktur-Overhead. Das Fakten-Halluzinations-Risiko wird durch einen strikten Prompt (nur übergebene Fakten verwenden, keine Erfindungen, maximal 3 Sätze) auf das Minimum begrenzt. Ein zukünftiges Freigabe-Gate kann jederzeit als Add-on gebaut werden (Lock-Flag existiert bereits). Option B ist nur sinnvoll wenn manuelle Kontrolle über jeden Text Pflicht wird — das ist heute kein Requirement.

**Analyse & Planung:**
- [x] Example Mapping (kompakt)
- [x] Pre-Mortem (kompakt)
- [x] Architektur analysiert: `data/store.py` (qa_values/description_lock), `main.py:_load_qa_values()` + Erweiterungspunkt Z.731, neues Modul `data/qa_description.py` nach Azimut-Muster
- [x] Optionen: A (Anthropic HTTP direkt, synchron via httpx) / B (Pipeline + Freigabe-Flag) — **Empfehlung A**
- [x] Empfehlung: Option A — schlanker Start, Azimut-Muster, kein Infrastruktur-Overhead

**Testplan:**

*Automatisiert (`backend/tests/test_task46_descriptions.py`):*

```
test_description_written_when_empty
  Gegeben: Store mit Location ohne description + kein Lock
  Und: Anthropic-API gemockt → gibt "Ein toller Spot." zurück
  Wenn: update_location_description(store, loc_id, …) aufgerufen
  Dann: store.get_qa_values(loc_id)["description"] == "Ein toller Spot."

test_description_lock_respected
  Gegeben: description_lock = 1 gesetzt
  Und: Anthropic-API gemockt (würde Text liefern)
  Wenn: update_location_description aufgerufen
  Dann: Rückgabewert None; set_qa_values NICHT aufgerufen (API-Mock NICHT aufgerufen)

test_empty_api_response_not_written
  Gegeben: kein Lock; API-Mock gibt leeren String "" zurück
  Wenn: update_location_description aufgerufen
  Dann: Rückgabewert None; description in qa_values nicht gesetzt (bleibt None)

test_whitespace_only_response_not_written
  Gegeben: kein Lock; API-Mock gibt "   \n  " zurück
  Dann: wie test_empty_api_response_not_written

test_api_error_silent
  Gegeben: kein Lock; API-Mock wirft httpx.ConnectError
  Dann: Rückgabewert None; keine Exception nach außen; Log-Ausgabe vorhanden

test_missing_api_key_skips_silently
  Gegeben: ANTHROPIC_API_KEY nicht gesetzt (None)
  Dann: Rückgabewert None; keine Exception; kein HTTP-Call

test_existing_description_not_overwritten
  Gegeben: kein Lock; aber location hat bereits eine description "Beste Aussicht"
           in qa_values (oder manuell — durch description_lock simuliert)
  Dann: Wert bleibt "Beste Aussicht" — update_location_description schreibt nicht

test_build_prompt_contains_facts
  Gegeben: loc_name="Teufelsberg", subject_name="Berliner Dom", category="SKYLINE"
  Dann: _build_prompt(...) enthält "Teufelsberg", "Berliner Dom", "SKYLINE";
        enthält keine Erfindungen (kein Platzhalter-Text außerhalb der Fakten)
```

*Manuell (nach lokalem Serverstart):*
1. Server starten (Fenster 1): `cd .../FotoAlert/backend && python main.py`
2. ANTHROPIC_API_KEY in Umgebung setzen.
3. Via Chrome-Console oder curl einen Test-Spot ohne description anlegen:
   `API.post('/preview-alignment', {save:true})` oder `curl -X PATCH /locations/{id}` mit leerer description.
4. QA-Lauf triggern (TASK-48-Endpunkt oder direkter Python-Aufruf im Fenster 2).
5. `curl http://localhost:8000/locations/{id}` — Feld `description` muss jetzt einen kurzen deutschen Text enthalten.
6. `description_lock` auf 1 setzen, QA-Lauf wiederholen → Beschreibung bleibt unverändert.
7. ANTHROPIC_API_KEY löschen (`unset`), QA-Lauf → kein Absturz, Beschreibung bleibt wie sie war, Log zeigt Überspringen.

---

### TASK-47 · Brennweiten-Empfehlung automatisch berechnen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |
| **Epic** | US-75 |

**Beschreibung:** Für Spots ohne kuratierte Brennweiten-Empfehlung soll das System aus Motivgröße und Entfernung automatisch eine passende Brennweite vorschlagen, damit die App auch bei neuen Spots eine brauchbare Objektiv-Empfehlung zeigt.

---

**Was Stephan in der App erleben soll (Kurzfassung):**
Wenn ein Spot keine von Hand gepflegte Objektiv-Empfehlung hat, aber Motivgröße und Entfernung bekannt sind, errechnet das System nach dem Qualitäts-Lauf von allein eine passende Brennweite und zeigt sie im Spot-Detail an. Ein weiter entferntes Motiv bekommt eine längere Brennweite. Bei gleicher Bildfüllung braucht ein größeres (höheres) Motiv eine kürzere und ein kleineres eine längere Brennweite — so füllt das Motiv das Bild jeweils gleich stark. Hat jemand schon eine eigene Empfehlung gepflegt (und gesperrt), bleibt diese unangetastet. Fehlt eine der nötigen Angaben, wird lieber nichts angezeigt als eine erfundene Zahl.

---

**Scope:**
- **Eingeschlossen:** Ein neues, eigenständiges Modul, das für eine einzelne Location aus Motivhöhe und Entfernung eine Brennweiten-Empfehlung ableitet, das Sperr-Flag prüft und das Ergebnis als auto-generierten Wert in der QA-Werte-Ablage speichert — exakt nach dem Muster, das die Schwester-Aufgabe (Azimut) bereits etabliert hat. Geschrieben wird nur, wenn keine kuratierte Liste existiert und die Empfehlung nicht gesperrt ist.
- **Bewusst ausgeschlossen:** Der automatische, regelmäßige Qualitäts-Lauf, der dieses Modul reihum über alle Spots aufruft (das ist die nächste Aufgabe). Keine UI-Änderung (die Anzeige der Brennweite existiert bereits). Keine Änderung an der bestehenden Live-Geometrie im Chancen-Code (die bleibt als Laufzeit-Fallback erhalten). Keine Verwendung von Motiv-*breite* in diesem ersten Schritt (siehe Annahme A1).

**⚠️ Annahmen (bitte beim Weg-Gate bestätigen):**
- **A1 — Welche Maßzahl?** Die bestehende Live-Geometrie nutzt die Motiv*höhe* als maßgebliche Größe. Annahme: das neue Modul übernimmt das (Höhe, nicht Breite), damit Auto-Wert und Live-Fallback dieselbe Logik teilen. Motivbreite bleibt vorerst ungenutzt. *Begründung: Konsistenz mit dem schon ausgelieferten Verhalten; sonst entstünde ein zweiter, abweichender Rechenweg.*
- **A2 — Eine Zahl oder eine Staffel?** Die kuratierten Listen enthalten meist 3–4 gestaffelte Brennweiten (z.B. 50/85/135). Annahme: der Auto-Wert liefert **eine** gerasterte Empfehlung als einelementige Liste (z.B. `[135]`). *Begründung: die Geometrie liefert genau einen physikalisch sinnvollen Wert; eine künstliche Staffel wäre geraten, nicht berechnet.* Falls eine Staffel gewünscht ist, bitte als 🔴-Entscheidung melden.
- **A3 — Bildfüllung.** Annahme: dieselbe Bildfüllung (25 %) wie der bestehende Location-Fallback, damit Auto-Wert und Laufzeit-Fallback identische Zahlen ergeben.

**Akzeptanzkriterien (erlebbares Verhalten):**
- [ ] Ein neuer Spot mit Angaben zu Motivhöhe und Entfernung zeigt nach dem Qualitäts-Lauf eine plausible Brennweiten-Empfehlung im Spot-Detail. Konkret nachprüfbar: ein weiter entferntes Motiv erhält eine längere Brennweite als ein nahes; und bei gleicher Bildfüllung erhält ein größeres (höheres) Motiv eine kürzere Brennweite als ein kleineres (damit beide das Bild gleich stark füllen). Die Empfehlung folgt dieser Geometrie, nicht dem Zufall.
- [ ] Ein Spot, dessen Brennweiten-Empfehlung von Hand gepflegt und gesperrt ist, behält exakt diese Werte — der Auto-Lauf ändert nichts daran.
- [ ] Ein Spot, der bereits eine kuratierte Empfehlungs-Liste hat, behält sie; der Auto-Wert drängt sich nicht dazwischen.
- [ ] Fehlt die Motivhöhe **oder** die Entfernung (oder ist die Entfernung 0), bleibt die Empfehlung leer — es erscheint keine erfundene Zahl, und es gibt keinen Absturz.
- [ ] Edge Case: Zwei Läufe hintereinander auf denselben, unveränderten Spot ergeben exakt dieselbe Empfehlung (kein Zufall, keine Schwankung).
- [ ] Edge Case: Eine extrem kleine Entfernung oder ein extrem großes Motiv führt nicht zu einer absurd langen Brennweite jenseits des sinnvollen Rasters — der Wert wird auf die bekannte Brennweiten-Staffel gerundet.

**Pre-Mortem:**
- 💀 Szenario: Der Auto-Wert überschreibt eine von Hand gepflegte oder gesperrte Empfehlung. → **Auslöser:** Sperr-Prüfung oder „nur wenn leer"-Regel fehlt. **Gegenmaßnahme:** vor dem Schreiben Sperr-Flag prüfen (wie beim Azimut-Modul) **und** nur schreiben, wenn keine kuratierte Liste vorliegt; durch AK 2+3 abgesichert.
- 💀 Szenario: Division durch null / unsinnige Brennweite bei fehlender oder 0-Entfernung. → **Auslöser:** die reine Geometrie-Formel teilt durch die Entfernung und durch die Bildfüllung; die Standalone-Funktion `calculate_focal_length_for_subject` hat **keinen** eigenen 0-Schutz (verifiziert, s.u.). **Gegenmaßnahme:** das neue Modul prüft Höhe>0 und Entfernung>0 **bevor** es rechnet (genau wie der bestehende Location-Fallback), sonst kein Schreiben; AK 4.
- 💀 Szenario: Absurd lange Brennweite bei Mini-Entfernung/Riesen-Motiv wird unverändert gespeichert. → **Gegenmaßnahme:** Ergebnis auf die bestehende Brennweiten-Staffel rastern (wie der Live-Fallback); AK 6.
- 💀 Szenario: Neue Werte erscheinen nicht in der App, weil sie beim Server-Start in der falschen Reihenfolge gemerged werden. → **Gegenmaßnahme:** verifiziert, dass die QA-Werte beim Start *vor* den manuellen Overrides gemerged werden (Code < QA-Werte < Overrides), Brennweite ist im Merge bereits berücksichtigt; der *regelmäßige* Auto-Aufruf ist die nächste Aufgabe.
- 💀 Szenario: Sensorformat-/Einheiten-Annahme falsch (Crop-Sensor, cm statt m). → **Gegenmaßnahme:** Vollformat (36 mm Sensorbreite) und Meter sind die durchgängige Konvention im Bestand; das neue Modul übernimmt sie unverändert, keine eigene Annahme.

**📎 Code-Verifikation (2026-06-28, echter Code gelesen):**
- **Geometrie vorhanden:** `calculations/astronomy.py:calculate_focal_length_for_subject(subject_size_m, distance_m, sensor_width_mm=36.0, desired_frame_fill_pct=0.3)` (Z.915–930) — rechnet `atan(size/distance)`, teilt durch `desired_frame_fill_pct`, dann `tan`-Umkehr. **Bestätigt: kein 0-Schutz** für `distance_m` oder `desired_frame_fill_pct` in dieser Funktion → 0-Guard muss im neuen Modul liegen.
- **Location-Wrapper:** `calculations/opportunity.py:_focal_for_location` (Z.140–158) priorisiert kuratierte Liste → sonst `calculate_focal_length_for_subject(subject_height_m, distance_m, desired_frame_fill_pct=0.25)` (Höhe, 25 %) → rastert auf `_FOCAL_STEPS = [24,35,50,85,135,200,300,400,600]` (Z.137). **Diese Logik wird wiederverwendet, nicht verändert** (bleibt Laufzeit-Fallback).
- **Ablage vorhanden:** Spalte `location_qa_values.focal_length_suggestions TEXT` (`data/store.py` Z.121) + Sperr-Flag `location_qa_state.focal_length_lock` (Z.111). `set_qa_values(focal_length_suggestions=[…])` serialisiert als JSON (Z.703–707), `get_qa_values` parst zurück (Z.691–692). `get_qa_state` liefert das Sperr-Flag (Z.627–634). **Kein Schema-Umbau nötig.**
- **Merge bestätigt:** `main.py:_load_qa_values()` (Z.846–876) übernimmt `focal_length_suggestions` aus den QA-Werten in die Location (Z.870–871); Start-Reihenfolge `_load_qa_values()` (Z.888) **vor** `_load_location_overrides()` (Z.891) → Override gewinnt über Auto-Wert (Code < QA < Override).
- **Lücke (das ist die Aufgabe):** Es gibt **kein** Schwester-Modul zu `data/qa_azimuth.py` für Brennweite. `data/qa_azimuth.py` (TASK-45) liefert die Vorlage: deterministisch, `update_location_azimuth(store, location_id, …)` prüft `get_qa_state(...).get("azimuth_lock")` und schreibt via `set_qa_values`, gibt bei Lock/fehlenden Daten `None` zurück, wirft nie eine Exception. **Dieses Muster wird 1:1 für Brennweite übernommen.**
- **Python 3.9:** Vorlage nutzt `from __future__ import annotations` + `typing.Optional/List/Tuple`, kein `str|None`, kein `match` — wird übernommen.

**Architektur-Analyse — betroffene Dateien:**
- **Neu:** `backend/data/qa_focal.py` — Schwester zu `qa_azimuth.py`. Reine Berechnung + Schreib-Funktion mit Sperr-Prüfung. Wiederverwendung der bestehenden Geometrie aus `calculations/astronomy.py` + `_FOCAL_STEPS`-Rasterung.
- **Neu:** `backend/tests/test_task47_focal.py` — analog zu `test_task45_azimuth.py`.
- **Unverändert (nur referenziert):** `calculations/astronomy.py`, `calculations/opportunity.py` (Live-Fallback bleibt), `data/store.py` (Methoden + Schema reichen), `main.py` (Merge reicht).

**Implementierungsoptionen:**

*Option A — Bestehende Geometrie wiederverwenden, eigenes QA-Modul (analog Azimut)*
- App-Wirkung: Auto-Brennweite ist exakt dieselbe Zahl, die die App schon heute als Laufzeit-Fallback berechnet — nur jetzt sichtbar gespeichert. Ein Rechenweg, ein Verhalten, kein Auseinanderdriften.
- Vorgehen: neues Modul `qa_focal.py` mit `compute_focal_suggestion(...)` (Guard >0, ruft `calculate_focal_length_for_subject` mit 25 %, rastert auf `_FOCAL_STEPS`) und `update_location_focal(store, location_id, …)` (Sperr-Prüfung → Schreiben via `set_qa_values`). Konsistent mit `qa_azimuth.py`.
- Risiken: gering — nutzt verifizierte, bereits ausgelieferte Geometrie.
- Aufwand: klein.

*Option B — Eigene, neue Brennweiten-Berechnung im QA-Modul*
- App-Wirkung: Risiko, dass der gespeicherte Auto-Wert von der Live-Anzeige des Chancen-Codes abweicht → derselbe Spot zeigt je nach Pfad verschiedene Empfehlungen. Verwirrend, schwer zu testen.
- Vorgehen: Geometrie im QA-Modul neu schreiben.
- Risiken: Doppel-Logik, Drift, mehr Testfläche, kein Mehrwert.
- Aufwand: mittel.

✅ **Empfehlung: Option A** — wiederverwendet die bereits verifizierte, ausgelieferte Geometrie, folgt 1:1 dem etablierten Azimut-Muster (Konsistenz, ein Rechenweg) und hält das Risiko klein. Option B brächte nur Doppel-Logik und Abweichungsrisiko.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (mit Annahmen-Protokoll A1–A3)
- [x] Pre-Mortem durchgeführt (5 Szenarien, Gegenmaßnahmen in AKs verankert)
- [x] Architektur analysiert: neues `data/qa_focal.py`, Wiederverwendung Geometrie aus `calculations/astronomy.py`/`opportunity.py`, Ablage/Merge unverändert
- [x] Optionen: A (bestehende Geometrie wiederverwenden, eigenes QA-Modul) / B (eigene Berechnung) — **Empfehlung A**
- [ ] Weg-Gate: Stephan bestätigt Option A + Annahmen A1–A3

**Testplan:**
- [ ] **Automatisiert** (`backend/tests/test_task47_focal.py`, analog `test_task45_azimuth.py`):
  - bekannte Höhe + Entfernung → erwartete gerasterte Brennweite aus `_FOCAL_STEPS`; größere Entfernung → längere Brennweite, größere Motivhöhe → kürzere Brennweite (gleiche Bildfüllung). *(AK 1, 6)*
  - gesetztes Sperr-Flag → `update_location_focal` schreibt nichts, gibt `None`. *(AK 2)*
  - vorhandene kuratierte Liste → kein Auto-Schreiben. *(AK 3)*
  - fehlende Höhe / fehlende Entfernung / Entfernung 0 → `None`, kein Schreiben, kein Crash. *(AK 4)*
  - zwei identische Läufe → identisches Ergebnis (Determinismus). *(AK 5)*
- [ ] **Manuell** (unter http://localhost:8000): Test-Spot mit Motivhöhe + Entfernung ohne kuratierte Liste anlegen, Auto-Funktion einmal aufrufen, Spot-Detail öffnen → Brennweiten-Empfehlung sichtbar und plausibel; danach denselben Spot sperren, erneut aufrufen → Empfehlung unverändert.

---

### TASK-48 · QA-Lauf automatisieren: Änderungen erkennen + planen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |
| **Epic** | US-75 |

**Beschreibung:** Das System soll regelmäßig und automatisch prüfen, welche Spots sich geändert haben oder noch nie geprüft wurden, und für genau diese die Auto-Verbesserungen anstoßen — ohne unveränderte Spots unnötig neu zu berechnen und ohne externe Dienste zu überlasten. Dies ist der Schlussstein von Epic US-75: er verbindet die fertigen Bausteine (Azimut TASK-45, Brennweite TASK-47) mit einem geplanten Lauf und stellt zugleich sicher, dass die ermittelten Werte auch in den täglich vorberechneten Chancen (Feed/Kalender) ankommen — nicht nur in der Live-Detailansicht.

**Scope:**
- **Eingeschlossen:**
  - Ein geplanter QA-Lauf, angehängt an den bereits vorhandenen Zeitplan im Backend (`main.py`-Scheduler) — **kein** separater Dienst, **kein** neues Modul.
  - Erkennen, welche Spots überhaupt einen neuen Lauf brauchen: ein Spot kommt auf die Liste, wenn sich seine Geo-Kernfelder geändert haben (Vergleich des aktuellen Geo-Fingerabdrucks mit dem gespeicherten) **oder** wenn er noch nie geprüft wurde. Unveränderte, schon geprüfte Spots werden übersprungen.
  - Anstoßen der **fertigen** Auto-Verbesserungen für genau diese Spots: Azimut (TASK-45) und Brennweite (TASK-47). Beide respektieren ihre Sperren und werfen nie.
  - Nach erfolgreichem Verbessern eines Spots: seinen Prüf-Zeitstempel und seinen Geo-Fingerabdruck fortschreiben, damit er beim nächsten Lauf nicht erneut anfällt (außer er ändert sich wieder).
  - **Sichtbarmachen der Auto-Werte im täglichen Recompute:** Der nächtliche Vorberechnungs-Prozess muss dieselben Auto-Werte einlesen wie der Live-Server, sonst zeigen Feed/Kalender weiter alte Werte (BUG-29-Muster — siehe Code-Verifikation).
  - Drosselung gegenüber externen Diensten und Fehlerisolierung pro Spot.
  - Ein **klar markierter Erweiterungspunkt** für die spätere LLM-Beschreibung (TASK-46), der heute nichts aufruft.
- **Ausgeschlossen:** Admin-UI; manueller Trigger-Endpoint (optional als Folge-Ticket); Lizenz-Checks (US-79); die LLM-Beschreibung selbst (TASK-46, noch nicht gebaut — TASK-48 ruft sie **nicht** auf).

**✅ Laufzeit (von Stephan bestätigt 2026-06-28):** QA-Job **täglich 01:00** (Ortszeit Berlin), großer Puffer vor dem nächtlichen Recompute (05:30). So sind frische Auto-Werte sicher vorhanden, bevor der Recompute sie einliest.

**🔘 Geschützter Sofort-Auslöser (Erweiterung 2026-06-28, von Stephan freigegeben):** Damit man den QA-Lauf lokal und operativ testen kann, ohne bis 01:00 zu warten, gibt es einen geschützten Auslöser, der den Lauf einmalig sofort anstößt und kurz zurückmeldet, wie viele Spots geprüft/verbessert wurden bzw. ob gerade schon ein Lauf läuft (dann wird er sauber übersprungen, nichts startet parallel). Der Auslöser ist nur für den Host und nutzt denselben Schutz wie die übrigen Admin-Aktionen (Host-Login/Token). Test-Pfad: `POST /run-qa-pass` mit Host-Token.

---

**Example Mapping:**

📏 **Regel 1 — Nur betroffene Spots werden verbessert.** Geprüft wird, ob sich der Geo-Fingerabdruck eines Spots seit der letzten Prüfung geändert hat oder ob er noch nie geprüft wurde.
- 🟢 Ein Spot wurde umgesetzt (neue Koordinaten) → beim nächsten Lauf wird genau dieser neu verbessert.
- 🟢 Ein Spot ist unverändert und wurde gestern geprüft → er wird übersprungen, keine externe Anfrage.
- 🟢 Ein brandneuer Spot ohne Prüf-Historie → wird beim nächsten Lauf erstmals verbessert.

📏 **Regel 2 — Sperren bleiben heilig.** Hat jemand einen Wert (Azimut oder Brennweite) eines Spots manuell gesperrt, rührt der Lauf diesen Wert nicht an, der Rest des Spots wird trotzdem aktualisiert.
- 🟢 Azimut gesperrt, Brennweite frei → nur die Brennweite wird neu gesetzt.
- 🟢 Beide gesperrt → es wird nichts geschrieben, der Spot gilt als geprüft.

📏 **Regel 3 — Ein Lauf gleichzeitig.** Es läuft nie ein QA-Lauf, während schon einer (oder ein großer Recompute) läuft, und umgekehrt blockieren sie sich nicht gegenseitig dauerhaft.
- 🟢 Der geplante Recompute läuft noch, der QA-Lauf wird fällig → der QA-Lauf wartet bzw. wird übersprungen und beim nächsten Mal nachgeholt, statt sich zu überlagern.

📏 **Regel 4 — Auto-Werte erreichen Feed/Kalender.** Was der QA-Lauf an einem Spot verbessert, ist nach dem nächsten Recompute auch in den vorberechneten Chancen sichtbar, nicht nur im Detail.
- 🟢 Beschreibung eines Spots wird (künftig) automatisch erzeugt → sie taucht im Feed-Eintrag auf, nicht nur im Detail-Overlay.

❓ **Questions:** keine offen (Laufzeit als ⚠️-Annahme markiert, blockiert nicht).

---

**Akzeptanzkriterien (erlebbares Verhalten):**
- [ ] **AK-1 (geänderter Spot):** Wird an einem Spot ein geo-relevantes Feld geändert (Standort, Motiv, Entfernung), wird beim nächsten geplanten Lauf genau dieser Spot neu verbessert; bereits geprüfte, unveränderte Spots werden dabei übersprungen.
- [ ] **AK-2 (neuer Spot):** Ein noch nie geprüfter Spot wird beim nächsten Lauf erstmals automatisch verbessert.
- [ ] **AK-3 (kein erneutes Anfallen):** Ein gerade verbesserter, danach unveränderter Spot fällt beim übernächsten Lauf nicht erneut an — bis sich wieder etwas an ihm ändert.
- [ ] **AK-4 (Sichtbarkeit in Feed/Kalender):** Nach einem QA-Lauf und dem darauffolgenden täglichen Recompute wirken sich die neuen Auto-Werte auch auf die vorberechneten Chancen (Feed/Kalender) aus — nicht nur in der Live-Detailansicht. Live-Server und nächtlicher Recompute zeigen denselben Wertstand für einen Spot.
- [ ] **AK-5 (Robustheit bei Ausfall):** Fällt ein externer Dienst aus oder schlägt ein einzelner Spot fehl, läuft der Rest des Laufs normal weiter, und der betroffene Spot wird beim nächsten Lauf erneut versucht — er bleibt nicht dauerhaft hängen.
- [ ] **AK-6 (kein Überlappen):** Ein QA-Lauf startet nicht, während bereits ein QA-Lauf oder ein großer Recompute läuft; nichts blockiert dauerhaft.
- [ ] **AK-7 (Drosselung) — Edge Case:** Der Lauf belastet externe Dienste gedrosselt (begrenzte gleichzeitige Anfragen / kurze Pausen), sodass keine Sperren durch zu viele Anfragen entstehen.
- [ ] **AK-8 (Sperren) — Edge Case:** Manuell gesperrte Werte eines Spots bleiben unverändert; der Spot gilt nach dem Lauf trotzdem als geprüft.

---

**Pre-Mortem:**

📎 **Code-Verifikation (2026-06-28, gelesen, nicht erinnert):**
- **Scheduler:** `backend/main.py` nutzt bereits `AsyncIOScheduler` (Import Z.38, Instanz `scheduler = AsyncIOScheduler(timezone="Europe/Berlin")` Z.258). In `startup()` werden drei Cron-Jobs registriert (Z.948–951: precompute täglich 05:30 via `functools.partial(_run_precompute, _precompute_mode)`, weather alle 3h, discover 05:45), dann `scheduler.start()`. → TASK-48 hängt **einen** weiteren Cron-Job an, baut keinen neuen Dienst. **Bestätigt.**
- **Single-Flight:** Globales Flag `_precompute_running` (Z.219) schützt `_run_precompute` (Z.589: „läuft bereits, übersprungen") und `_run_precompute_single` (Z.768ff). Bei Überlappung wird eine Einzel-ID in `_recompute_pending` (Z.220) geparkt und am Lauf-Ende über `_drain_recompute_pending()` (Z.643) nachgeholt (US-106). → Muster für den QA-Lauf direkt nutzbar. **Bestätigt.**
- **Geo-Hash / QA-State:** `compute_geo_hash(observer_lat, observer_lon, subject_lat, subject_lon, subject_height_m, subject_width_m, distance_m)` (data/store.py Z.743, Modul-Ebene, MD5, auf 6 Stellen gerundet). `get_qa_state(location_id)` (Z.627, liefert dict mit `geo_hash`, `qa_checked_at`, Lock-Flags oder None), `update_qa_checked(location_id, geo_hash)` (Z.661, Upsert). **Bestätigt — Change-Detection-Basis vollständig vorhanden.**
- **Bausteine:** `data/qa_azimuth.py:update_location_azimuth(store, location_id, observer_lat, observer_lon, subject_lat, subject_lon, tolerance_deg=…, use_overpass=False)` (Z.237) und `data/qa_focal.py:update_location_focal(store, location_id, subject_height_m, distance_m, frame_fill_pct=…)` (Z.84). Beide lesen `get_qa_state`, respektieren das jeweilige Lock (und Brennweite zusätzlich eine bereits kuratierte Liste), schreiben via `set_qa_values`, geben den geschriebenen Wert oder `None` zurück und **werfen nie**. **Signaturen bestätigt.**
- **LLM-Beschreibung (TASK-46):** **Existiert nicht.** Kein `update_location_description` o.ä. im Code. → TASK-48 stößt nur Azimut + Brennweite real an; für die Beschreibung nur ein markierter Platzhalter (kein Aufruf einer nicht-existenten Funktion). **Bestätigt.**
- **Sichtbarkeits-Lücke (Kern):** `main.py:_load_qa_values()` (Z.846–878) liest beim Server-Start `_store.load_all_qa_values()` und patcht damit die Live-Location-Objekte: `loc.description`, `loc.ideal_azimuth_range` (aus `ideal_azimuth_min/max`), `loc.focal_length_suggestions` — Merge-Reihenfolge Code-Defaults < qa_values < Overrides (Aufruf in `startup()` Z.888). **`precompute.py:main()` (Z.1005–1016) ruft nur `_apply_location_overrides()` (Z.1012) und `_load_custom_locations()` (Z.1015) auf — KEIN Äquivalent zu `_load_qa_values()`.** → Der Recompute-Subprozess sieht die Auto-Werte nicht. **Bestätigt — exakt das BUG-29-Muster.**
- **Datenfluss-Präzisierung (wichtig für den Scope):** Im Feed-/Kalender-Payload (precompute.py Z.380ff) ist `"description": o.description` pro Event eingebettet → die (künftige) Auto-Beschreibung **fließt direkt in die vorberechneten Chancen** und braucht den Recompute-Merge zwingend. Dagegen wird `subject_azimuth` aus der Geometrie berechnet (calculations/opportunity.py), **nicht** aus `ideal_azimuth_range`; `ideal_azimuth_range` speist `_compute_possible_bodies` (main.py Z.969) + Detailanzeige. `focal_length_suggestions` ist ein Location-Feld (Detail/Kamera-Hinweis). → Der Recompute-Merge ist für **Beschreibung** funktional unverzichtbar und für **Azimut/Brennweite** notwendig für Stand-Gleichheit Server↔Recompute (sonst divergieren beide). **Belegt.**

💀 **Szenario 1 — Auto-Werte erscheinen im Detail, aber Feed/Kalender bleiben alt** (BUG-29-Muster).
   Auslöser: `precompute.py` lädt die Auto-Werte nicht (verifiziert: kein `_load_qa_values()`-Äquivalent).
   Frühwarnung: Nach einem QA-Lauf zeigt das Detail neue Werte, aber ein Feed-Eintrag (besonders die Beschreibung) bleibt alt.
   Gegenmaßnahme (**Kern dieses Tickets**): In `precompute.py:main()` ein `_apply_qa_values()` einführen — gespiegelt von `main.py:_load_qa_values()`, mit **identischer Merge-Reihenfolge** Code-Defaults < qa_values < Overrides, ausgeführt **nach** `_apply_location_overrides()`/`_load_custom_locations()`. Real gegen einen Single-Recompute tracen (Schritt 4d). → AK-4.

💀 **Szenario 2 — Jeder Lauf rechnet/ruft alles neu** → unnötige Last/Kosten an externen Diensten.
   Auslöser: Change-Detection greift nicht (z.B. Hash-Felder unvollständig, oder `qa_checked_at`/`geo_hash` werden nicht fortgeschrieben).
   Frühwarnung: Lauf-Dauer und externe Anfragen wachsen mit jedem Lauf statt zu sinken.
   Gegenmaßnahme: strikter Geo-Hash-Diff (gleiche 7 Felder wie `compute_geo_hash`), nach jedem verbesserten Spot `update_qa_checked` schreiben; Test prüft „gleicher Hash → übersprungen". → AK-1/AK-3.

💀 **Szenario 3 — Doppelläufe überlappen** (QA-Lauf + nächtlicher Recompute / zweiter QA-Lauf).
   Auslöser: Zwei schwere Läufe greifen gleichzeitig auf dieselben Daten zu.
   Frühwarnung: Log zeigt zwei laufende Berechnungen; Werte „flackern".
   Gegenmaßnahme: Eigenes Single-Flight-Flag für den QA-Lauf (analog `_precompute_running`); zusätzlich beim Start prüfen, ob `_precompute_running` aktiv ist → dann verschieben. Job zeitlich vor den Recompute legen (01:00 vor 05:30). → AK-6.

💀 **Szenario 4 — QA-Lauf blockiert den Event-Loop** (synchrone externe Aufrufe in der Async-App).
   Auslöser: `update_location_*` macht ggf. blockierende Netz-/Rechenarbeit, direkt im Scheduler-Coroutine-Kontext ausgeführt → Server reagiert minutenlang nicht.
   Frühwarnung: API-Antwortzeiten steigen während des Laufs stark; Health-Check träge.
   Gegenmaßnahme: QA-Verarbeitung pro Spot in einen Thread auslagern (`asyncio.to_thread`, Py3.9+) bzw. mit `await asyncio.sleep(0)`/begrenzter Parallelität takten; nie eine lange synchrone Schleife direkt im Loop. → AK-7.

💀 **Szenario 5 — Geänderter Spot wird übersprungen und bleibt hängen** (US-106-Muster: ID bleibt in `_recompute_pending`).
   Auslöser: Eine Standort-Änderung trifft ein, während ein großer Lauf läuft; die ID wird geparkt, der QA-Lauf läuft danach aber an ihr vorbei.
   Frühwarnung: Ein nachweislich geänderter Spot trägt nach mehreren Läufen noch den alten Geo-Hash.
   Gegenmaßnahme: Change-Detection allein über den persistierten Geo-Hash (nicht über flüchtiges `_recompute_pending`) — ein geänderter Spot fällt so lange an, bis sein gespeicherter Hash dem aktuellen entspricht. Fehlversuche schreiben `qa_checked_at`/`geo_hash` **nicht** fort → automatischer Re-Try. → AK-1/AK-5.

💀 **Szenario 6 — Externe Rate-Limits / Dienst-Ausfall.**
   Auslöser: zu viele/zu schnelle Anfragen an Karte oder KI.
   Gegenmaßnahme: begrenzte gleichzeitige Anfragen + kurze Pausen; Fehler pro Spot abfangen und isolieren (Lauf bricht nie ganz ab); fehlgeschlagener Spot bleibt „ungeprüft" und wird erneut versucht. → AK-5/AK-7.

---

**Architektur-Analyse:**
- **Betroffene Dateien:**
  - `backend/main.py` — neuer Cron-Job + Job-Funktion (z.B. `_run_qa_pass`) mit eigenem Single-Flight-Flag; nutzt vorhandenes Scheduler-Setup (Z.948ff) und `_precompute_running`-Check.
  - `backend/precompute.py` — neues `_apply_qa_values()` (Spiegel von `main.py:_load_qa_values`), aufgerufen in `main()` nach Overrides/Custom-Load (≈ nach Z.1015). **Der eigentliche Sichtbarkeits-Fix.**
  - `backend/data/store.py` — bereits vollständig (Hash/State/checked/load_all_qa_values), **keine Änderung nötig**; ggf. ein Helper für „liste alle bekannten Location-IDs + ihren Geo-Hash" falls die Spot-Liste zentralisiert werden soll (prüfen, nicht zwingend).
  - `backend/data/qa_azimuth.py`, `backend/data/qa_focal.py` — werden nur **aufgerufen**, nicht geändert.
  - `backend/tests/test_task48_qa_cron.py` — neu.
- **Change-Detection-Logik:** Für jeden bekannten Spot den aktuellen Geo-Hash aus seinen 7 Geo-Feldern berechnen (`compute_geo_hash`), gegen `get_qa_state(id)["geo_hash"]` vergleichen. Anfällig, wenn unterschiedlich **oder** `get_qa_state` liefert None (nie geprüft). Nach erfolgreichem Verbessern `update_qa_checked(id, neuer_hash)`.
- **Lade-Reihenfolge (Pflicht-Check, Schritt 4d):** Der QA-Lauf läuft im Server-Prozess → er sieht Live-Locations inkl. Overrides/Custom. Der **Recompute-Subprozess** ist getrennt und muss die Auto-Werte selbst nachladen (`_apply_qa_values()`), sonst stale. Beim Bau einmal real tracen: Geo-Feld eines Test-Spots ändern → QA-Lauf → Single-Recompute → prüfen, dass der neue Wert (insb. Beschreibung) im `opportunities.json` ankommt.
- **Python 3.9-Konformität:** Keine `X | Y`-Annotationen in neuem Code (`Optional[...]`, `List[...]` aus `typing`); `asyncio.to_thread` ist in 3.9 verfügbar.

---

**Implementierungsoptionen:**

### Option A — QA-Job im bestehenden Scheduler + Werte-Merge im Recompute (Empfehlung)
- Vorgehen: Einen weiteren Cron-Job an den vorhandenen Backend-Scheduler hängen (täglich 01:00, vor dem Recompute). Der Job ermittelt die betroffenen Spots über den Geo-Fingerabdruck, stößt für sie Azimut + Brennweite an (gedrosselt, Fehler pro Spot isoliert), schreibt danach Prüf-Zeitstempel + Hash fort. Zusätzlich liest der nächtliche Recompute dieselben Auto-Werte ein wie der Live-Server, damit Feed/Kalender sie zeigen.
- App-Wirkung für Stephan: Standortänderungen „pflanzen sich" automatisch fort — der geänderte Spot wird über Nacht verbessert und die neuen Werte sind am Morgen sowohl im Detail als auch im Feed/Kalender sichtbar, ohne manuelles Zutun.
- Betroffene Dateien: `main.py` (Job + Flag), `precompute.py` (Werte-Merge), neuer Test.
- Vorteile: konsistent mit der bestehenden Architektur (ein Scheduler, ein Single-Flight-Muster), kein neuer Dienst zu betreiben, geringe Angriffsfläche, deckt den Sichtbarkeits-Fix mit ab.
- Nachteile/Risiken: Schwere Arbeit im Server-Prozess → muss sauber aus dem Event-Loop ausgelagert werden (Szenario 4).
- Aufwand: mittel.

### Option B — Separater QA-Dienst/Prozess
- Vorgehen: Ein eigenständiger Hintergrundprozess (eigener systemd-Service/Cron) führt den QA-Lauf außerhalb des Servers aus.
- App-Wirkung: für Stephan identisch sichtbar; der Unterschied ist rein betrieblich.
- Vorteile: schwere Arbeit belastet den Server-Prozess nicht.
- Nachteile/Risiken: zweiter Prozess mit eigener Datenquelle/Deployment → genau die Trennung, die schon BUG-29/BUG-33 verursacht hat (eigener Stand, vergessenes Nachladen); mehr Betriebsaufwand; widerspricht dem im Ticket vorgegebenen Scope („kein separater Service").
- Aufwand: groß.

✅ **Empfehlung: Option A** — sie folgt der vorhandenen Scheduler-/Single-Flight-Architektur, vermeidet einen zweiten Prozess mit eigener Datenquelle (Hauptrisiko des Epics) und löst den Sichtbarkeits-Fix gleich mit. Die einzige echte Sorge (Event-Loop-Blockade) ist mit `asyncio.to_thread` + Drosselung beherrschbar.

**LLM-Erweiterungspunkt (TASK-46):** In der Job-Funktion eine klar kommentierte Stelle pro Spot, an der die Beschreibungs-Erzeugung später eingehängt wird — heute **ohne Aufruf** (kein Ruf einer nicht-existenten Funktion). Form: ein Kommentar-Block `# TASK-46 Erweiterungspunkt: hier update_location_description(...) anstoßen, sobald gebaut` an derselben Schleifenstelle, an der Azimut/Brennweite angestoßen werden, mit identischer Fehler-Isolierung/Drosselung. Da die Beschreibung über den Recompute-Merge bereits in Feed/Kalender fließt (Datenfluss-Präzisierung oben), ist nach Einbau von TASK-46 keine weitere Verdrahtung in TASK-48 nötig.

---

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (4 Regeln, Examples belegt, keine offenen Questions)
- [x] Pre-Mortem durchgeführt (6 Szenarien, je Gegenmaßnahme in AK/Plan verankert)
- [x] Architektur analysiert: `main.py` (Scheduler Z.948 + Single-Flight Z.219), `precompute.py` (Datenquelle Z.1005–1016, fehlender qa_values-Merge), `data/store.py` (Hash/State/checked vollständig), `qa_azimuth.py`/`qa_focal.py` als aufgerufene Bausteine
- [x] Datenfluss verifiziert (Beschreibung fließt per-Event in Feed; Azimut/Brennweite Detail-/Stand-Gleichheit)
- [x] Implementierungsoptionen: A (Job im bestehenden Scheduler + Werte-Merge im Recompute) / B (separater Dienst)
- [x] Empfehlung: Option A

**Daten-Validierung (beim Bau, Schritt 4d — Pflicht):**
- [ ] Einmal real tracen: Geo-Feld eines Test-Spots ändern → QA-Lauf → Single-Recompute → bestätigen, dass der neue Auto-Wert (insb. Beschreibung) im `opportunities.json` landet (nicht nur im Live-Detail).

**Testplan:**
- [ ] Automatisiert (`backend/tests/test_task48_qa_cron.py`, Ticket-ID im Docstring):
  - geänderter Geo-Hash → Spot wird ausgewählt; gleicher Hash → übersprungen; nie geprüft (State None) → ausgewählt (AK-1/2/3).
  - nach erfolgreichem Lauf sind `qa_checked_at` + `geo_hash` für den Spot fortgeschrieben; nach Fehlversuch **nicht** (AK-5).
  - Single-Flight: läuft bereits ein Lauf, startet kein zweiter (AK-6).
  - gesperrter Wert bleibt unverändert, Spot gilt trotzdem als geprüft (AK-8).
  - `precompute._apply_qa_values()`: nach Setzen eines qa_value erscheint dieser im neu berechneten Event (AK-4) — Merge-Reihenfolge Code-Defaults < qa_values < Overrides eingehalten.
- [ ] Manuell (unter http://localhost:8000): Geo-Feld eines Test-Spots ändern, QA-Lauf auslösen, im Log beobachten, dass **nur dieser** Spot anfällt, danach Single-Recompute beobachten und prüfen, dass die neuen Werte in Feed/Kalender (`opportunities.json`) ankommen.
- [ ] Regression: bestehende Cron-Jobs (precompute 05:30, weather, discover) laufen unverändert; Server reagiert während des QA-Laufs (Health-Check bleibt flott — Szenario 4).

---

### US-77 · Neue Locations via Backend hinzufügen + Merge mit Nutzerdaten `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Als Betreiber möchte ich neue Locations zentral über das Backend anlegen und diese automatisiert mit den Nutzerdaten (custom_locations.json) zusammenführen (Merge), ohne bestehende Nutzeränderungen zu überschreiben.

**Abhängigkeit:** TASK-17 (Datenfundament) — sicheres Merge/Upsert braucht den SQLite-Store; vorher nicht starten.

---

### US-78 · Duplikatserkennung bei räumlich nahen Motiven `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Beim Anlegen eines neuen Motivs soll das System warnen, wenn ein bestehendes Motiv zu nah liegt (konfigurierbare Schwelle), um Dopplungen zu vermeiden. Mehrere Fotografen-Standorte für dasselbe Motiv sind erlaubt und erwünscht, solange sie sinnvoll weit voneinander entfernt sind.

---

### US-82 · Scout Sun-Score v2: Atmosphärisches Rötlichkeits-Scoring `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Niedrig |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Das Sun-Scoring in US-81 nutzt `S_phase = 1.0` (Sonne immer voll beleuchtet). In v2 soll `S_phase` durch einen atmosphärischen Rötlichkeits-Score ersetzt werden: je flacher die Sonne steht, desto länger ist der Lichtweg durch die Atmosphäre, desto intensiver die Rötung. Das liefert differenziertere Empfehlungen (flacher = rötlicher = besser für Silhouetten-Fotografie).

**Voraussetzung:** US-81 ✅ (Sun-Pipeline muss implementiert sein)

**Akzeptanzkriterien:** (werden beim Start der Story ausgearbeitet)
- [ ] `S_atmosphaere(sun_alt_deg)` ersetzt `S_phase = 1.0` in `sun_pipeline.py`
- [ ] Formel: basiert auf optischer Weglänge durch Atmosphäre (`airmass = 1/sin(alt)`) — niedrige Sonne = hohe Airmass = mehr Rötung
- [ ] Optimum bei ~3–6° (maximale Rötung ohne vollständigen Horizontverlust)
- [ ] Score 0.0 bei alt > 15° (kein Rötlichkeits-Effekt mehr bei hoher Sonne)

---

<!-- ===== READY FOR ANALYSIS: freigegeben für Agenten ===== -->

### US-107 · Sonnen-Alignment-Planung: Auf-/Untergang relativ zur Location `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |
| **Abgeschlossen** | 2026-06-29 |

**Beschreibung:** Als Fotograf möchte ich für eine Location sehen, wann und in welcher Richtung die Sonne auf- oder untergeht — ob sie dabei nah, hinter oder über dem Motiv steht, oder ob ein Untergang gegenüber der Location für Gegenlicht-Motive interessant ist — damit ich Shootings präzise planen kann.

**Bezug:** US-64 (Live Astro-Visualisierung, zeigt Sonnenbahn live auf der Karte — US-107 ergänzt das um Planungs-/Zeitperspektive und Richtungsklassifizierung relativ zum Motiv), US-82 (Sun-Score v2 — berechnet Rötlichkeits-Score, kein Planungs-UI), TASK-45 (Azimut-Ableitung aus Geo-Daten — Infrastruktur, die US-107 nutzen kann), US-79 (Mondaufgang/-untergang im Detail — analoges Konzept für Mond, US-107 ist das Pendant für Sonne mit Planungsaspekt). Abgrenzung: US-64 zeigt Echtzeit-Position; US-107 zeigt geplante Auf-/Untergangszeiten + Richtungsklassifizierung (nah/hinter/über/gegenüber Motiv) für konkrete Tage.

---

#### 🔬 Implementation Spec (Analyse 2026-06-28)

##### 📐 Example Mapping

**Annahmen-Protokoll:**

| Typ | Punkt |
|-----|-------|
| ✅ Klar | Sonnenaufgang und -untergang-Zeiten sind bereits im precompute-Cache (`sunrise_utc`, `sunset_utc`). Azimut zur Auf-/Untergangszeit muss noch ergänzt werden (analog `moonrise_azimuth` / `moonset_azimuth` in US-79). |
| ✅ Klar | Die Motiv-Sichtachse (Azimut vom Fotograf-Standort zum Motiv) ist via `calculate_azimuth_alignment()` berechenbar sobald `observer_lat/lon` + `subject_lat/lon` vorhanden sind. Dieses Feld (`subject_azimuth`) existiert bereits im Opportunity-Objekt. |
| ⚠️ Annahme: Wo wird das angezeigt? Im **Event-Detail** (jede Opportunity hat `sunrise_utc`/`sunset_utc` schon) UND im **Location-Detail** (Abschnitt „Ausrichtung"). Das ist der natürliche Ort: Motiv-Azimut + Sonnenauf-/untergangs-Azimut pro Tag → Differenz → Klassifizierung. Bitte bestätigen. |
| ⚠️ Annahme: Richtungsklassifizierung wird als lesbarer Text angezeigt (z.B. „Sonne geht fast genau hinter dem Motiv auf") statt nur als Gradzahl. Toleranz für „nah am Motiv": ±15°. Bitte bestätigen oder anpassen. |
| ⚠️ Annahme: Das Feature zeigt primär den **heutigen Tag** im Location-Detail (kein Datums-Picker in US-107). Für andere Tage kann Stephan via „Live-Astro"-Button navigieren. Bitte bestätigen. |

📏 **Regel 1 — Sonnenaufgang/-untergang mit Azimut im Event-Detail.**
Im Event-Detail (Feed, Kalender) stehen neben Uhrzeit jetzt auch der Azimut der Sonne beim Aufgang bzw. Untergang — wie beim Mondaufgang in US-79.

- 🟢 *Positiv:* Ich öffne eine „Goldene Stunde Abend"-Chance → im Astronomie-Bereich sehe ich „Sonnenuntergang 21:05 · 289°". Ich weiß sofort, die Sonne geht fast im Westen unter.
- 🔴 *Negativ:* Events ohne `sunrise_utc`/`sunset_utc` (älterer Cache-Stand) zeigen keinen Azimut-Wert — kein Placeholder „0°", sondern einfach weggelassen.
- ⚙️ *Edge:* Im Polarsommer gibt es keinen echten Sonnenuntergang → `sunset_utc` ist null → kein Azimut-Feld sichtbar (kein Fehler).

📏 **Regel 2 — Richtungsklassifizierung relativ zum Motiv im Location-Detail.**
Im Abschnitt „Ausrichtung" des Location-Details erscheint für den heutigen Tag eine lesbare Einschätzung: Geht die Sonne nah am Motiv auf/unter, dahinter, darüber, oder gegenüber (Gegenlicht)?

- 🟢 *Positiv:* Berliner Dom, Motiv-Azimut ~153°. Ich öffne das Location-Detail → ich lese „Heute: Sonnenaufgang 52° (101° vom Motiv entfernt) · Sonnenuntergang 308° (155° — Gegenlicht)". Sofort nutzbare Planungsinfo.
- 🟢 *Positiv (Hochwerttag):* Motiv-Azimut 153°, Sonnenaufgang heute 151° → ich lese „Heute: Sonnenaufgang 151° — Sonne geht fast genau hinter dem Motiv auf (nur 2° Abweichung)!". Klar als Highlight erkennbar.
- 🔴 *Negativ:* Location ohne Motiv-Koordinaten (kein `subject_lat`/`subject_lon`) → keine Richtungsklassifizierung möglich. Stattdessen: nur „Sonnenaufgang HH:MM · XXX°" ohne Motivbezug.
- ⚙️ *Edge:* Location mit Motiv-Koordinaten, aber ohne idealen Azimut-Bereich → Berechnung läuft trotzdem (Azimut aus Koordinaten berechnet); `ideal_azimuth_range` ist optional.

📏 **Regel 3 — Konsistenz: Daten kommen aus demselben Cache wie das Event-Detail.**
Im Location-Detail wird für die Sonnen-Infos ein echtes Opportunities-Datum abgerufen (heutiges Datum), nicht auf Basis von rohen Skyfield-Live-Calls für jeden Seitenaufruf. Kalte Berechnungen per API für die Location-Detailansicht sind akzeptabel wenn gecacht.

- 🟢 *Positiv:* Ich öffne das Location-Detail → die Sonneninfos sind konsistent mit dem, was ich im Feed-Event für heute sehe.
- 🔴 *Negativ:* Sonnenauf-/untergangszeit im Location-Detail weicht von der im Feed-Event ab (weil andere Berechnungsquelle) → Verwirrung.

---

**📎 Code-Verifikation** (gelesen am 2026-06-28):

- `backend/calculations/astronomy.py` `SunInfo`-Dataclass (Z.73–86): hat `sunrise` und `sunset` als `datetime`, aber **keinen Azimut-Wert**. Azimut muss via `get_sun_position(lat, lon, sunrise)` nachberechnet werden — exakt wie bei `moonrise_azimuth` in US-79 (precompute.py Z.437–458).
- `backend/precompute.py` `_serialize()` (Z.420–428): serialisiert `sunrise_utc` und `sunset_utc` bereits; **kein `sunrise_azimuth` / `sunset_azimuth`**. Lücke bestätigt.
- `get_body_position(lat, lon, "sun", sunrise_dt)` → `CelestialPosition.azimuth` — diese Funktion existiert und ist getestet; dasselbe Muster wie moonrise_azimuth.
- `web/index.html` Z.3343–3344: Sonnenauf-/untergang im Event-Detail zeigt nur Uhrzeit, kein Azimut. Mondaufgang Z.3345 zeigt Azimut mit `· ${azimuth.toFixed(1)}°`. Anpassungsmuster ist direkt übertragbar.
- `LocationDetail._render()` Z.4650: Abschnitt `loc_azimut` zeigt bereits `idealer Azimut` und `Alignments` + `solar_alignment_note`. Erweiterung um heutige Auf-/Untergangsazimute + Richtungsklassifizierung ist hier der richtige Ort.
- `calculate_azimuth_alignment(obs_lat, obs_lon, subj_lat, subj_lon)` in astronomy.py Z.556–568: berechnet Azimut Fotograf→Motiv. Rückgabe ist ein `float`. Bereits in `opportunity.py` als `subject_azimuth` verwendet.
- Klassifizierungslogik (`classify_alignment()` o.ä.) existiert für Crown-Alignment (Z.681ff), aber **nicht** für die einfachere Richtungsklassifizierung „nah/gegenüber". Muss neu gebaut werden (wenige Zeilen, reine Differenz-Berechnung).
- `_loadEvents()` in LocationDetail (Z.4667): ruft bereits `/opportunities?location_id=...&days=30` ab. Die Sonneninformationen für **heute** könnten aus dem ersten heutigen Event dieser Liste entnommen werden — oder als separater `/sun-info?location_id=...&date=today`-Call.

---

##### ⚠️ Pre-Mortem

💀 **Szenario 1: Sunrise-Azimut-Call blockiert LocationDetail-Öffnung**
- Auslöser: Wenn `get_body_position` synchron per API-Aufruf für jeden Location-Open-Vorgang gerufen wird (kein Cache), dauert es ~100–500 ms → Location-Detail lädt spürbar langsam.
- Frühwarnung: Local-Test zeigt spürbares Hängen beim Öffnen des Sheets.
- Gegenmaßnahme: Azimut-Werte **im precompute-Cache speichern** (wie moonrise_azimuth), nicht live berechnen. Alternativ: asynchron nachladen (erst Sheet öffnen, dann Azimut einfügen).

💀 **Szenario 2: Richtungsklassifizierung funktioniert nur für Locations mit Motiv-Koordinaten**
- Auslöser: Viele Locations haben keinen `subject_lat`/`subject_lon` → kein `subject_azimuth` → keine Klassifizierung → leerer Bereich im Location-Detail, der verwirrend wirkt.
- Frühwarnung: Im Local-Test: Location ohne Motiv öffnen → Feld fehlt.
- Gegenmaßnahme: Klares Fallback: Wenn kein Motiv → nur „Sonnenaufgang HH:MM · XXX°" zeigen (ohne Motivvergleich). Kein Placeholder-Text wie „–" ohne Erklärung.

💀 **Szenario 3: Datenquelle Location-Detail vs. Event-Detail inkonsistent (US-96-Muster)**
- Auslöser: Location-Detail könnte Sonnen-Azimut aus einem anderen Pfad (Live-Skyfield) berechnen, während Event-Detail aus precompute-Cache liest → kleine Zeitabweichungen.
- Frühwarnung: Manuelle Probe: Event-Detail Sonnenuntergang und Location-Detail-Azimut vergleichen → Wert unterschiedlich?
- Gegenmaßnahme: Beide aus demselben Cache (precompute `opportunities.json`). Location-Detail verwendet das erste heutige Event der Location für die Sonnen-Zeitangaben.

💀 **Szenario 4: `get_body_position("sun", sunrise_dt)` schlägt fehl wenn sunrise_dt=None (Polarsommer/Edge)**
- Auslöser: `sunrise_dt` ist None (kein Aufgang im 24h-Fenster) → `get_body_position` crasht auf None.
- Frühwarnung: pytest mit sunrise=None → TypeError oder AttributeError.
- Gegenmaßnahme: Guard `if ... and o.astronomy_report.sun.sunrise else None` (analog zu moonrise_azimuth in precompute.py Z.446).

💀 **Szenario 5: Azimut-Wert 0.0° erscheint als „fehlt" (Norden)**
- Auslöser: Azimut 0° (Sonne geht exakt im Norden auf — Polarsommer) wird als null-ish behandelt und versteckt.
- Frühwarnung: `if o.sunrise_azimuth` in JS-Code → 0.0 ist falsy in JS → wird ausgeblendet.
- Gegenmaßnahme: Im Frontend `!= null` statt Truthy-Check (wie bei `moonrise_azimuth != null`).

---

##### 🏗️ Architektur-Analyse

**Betroffene Dateien:**
- `backend/precompute.py` — `_serialize()`: `sunrise_azimuth` und `sunset_azimuth` ergänzen (analog moonrise/moonset, Z.437–458)
- `backend/models/schemas.py` — OpportunityOut-Schema prüfen, ob neue Felder ergänzt werden müssen
- `backend/main.py` — OpportunityOut-Serialisierung prüfen (Z.1265)
- `web/index.html` — Event-Detail (Z.3343–3344): Azimut neben Uhrzeit ergänzen; LocationDetail._render() (Z.4650): Richtungsklassifizierung im `loc_azimut`-Abschnitt; neue Hilfsfunktion `sunAlignmentLabel(sunAz, motifAz)` für Richtungsklassifizierung

**Neue Funktion (pure JS, kein Backend-Aufruf):**
```
sunAlignmentLabel(sunAz, motifAz):
  diff = ((sunAz - motifAz + 180) % 360) - 180  // Winkeldifferenz -180..+180
  if |diff| <= 15  → "fast genau hinter dem Motiv" (🔥 Highlight)
  if |diff| <= 45  → "nah am Motiv (${diff.toFixed(0)}°)"
  if |diff| >= 150 → "gegenüber dem Motiv — Gegenlicht-Motive möglich"
  else             → "${diff.toFixed(0)}° vom Motiv entfernt"
```

**Daten-Einstiegspunkte-Check:**
- Event-Detail (Feed/Kalender): erhält das serialisierte Opportunity-Objekt direkt → `sunrise_azimuth`/`sunset_azimuth` müssen in precompute + Schema
- Location-Detail: lädt `/opportunities?location_id=...&days=30` asynchron → `_loadEvents()` Ergebnis auswerten für heute; alternativ: separate `/sun-info`-API. Einfachster Weg: aus bereits geladenem `_loadEvents`-Ergebnis das heutige Event extrahieren.

---

##### 🔀 Implementierungsoptionen

**Option A — Azimut im precompute-Cache, Klassifizierung im Frontend (empfohlen)**

Was du in der App erlebst: Beim Öffnen jedes Event-Details siehst du sofort neben „Sonnenaufgang" und „Sonnenuntergang" auch den Azimut in Grad — ohne Wartezeit. Im Location-Detail erscheint im Ausrichtungs-Abschnitt eine klare Einschätzung für heute: „Sonnenaufgang 151° — fast genau hinter dem Motiv 🔥". Die Daten kommen aus dem normalen täglichen Precompute — kein Extra-API-Call.

- Vorgehen: `sunrise_azimuth`/`sunset_azimuth` in `precompute.py::_serialize()` ergänzen (4 Zeilen, exakt wie moonrise_azimuth). Schema + main.py ergänzen. Im Frontend Event-Detail-Template Azimut anzeigen. In LocationDetail._render() aus dem bereits geladenen `_loadEvents`-Ergebnis das heutige Ereignis auslesen und Klassifizierungstext berechnen.
- Betroffene Dateien: `backend/precompute.py`, `backend/models/schemas.py`, `backend/main.py`, `web/index.html`
- Vorteile: Kein Extra-API-Call; konsistent mit moonrise_azimuth-Pattern; schnell im UI; einfach zu testen
- Nachteile: Azimut-Wert erst nach nächstem Precompute im Cache (ältere Events zeigen keinen Azimut bis Recompute)
- Aufwand: klein

**Option B — Separater `/sun-info`-API-Endpoint für das Location-Detail**

Was du in der App erlebst: Das Location-Detail macht beim Öffnen einen eigenen API-Call für die Sonnen-Infos des heutigen Tages — ohne Wartezeit (async, Sheet öffnet sofort). Azimut und Klassifizierung erscheinen kurz nach dem Sheet-Open (wie Wetter-Overlay).

- Vorgehen: Neuer Endpoint `/sun-info?location_id=&date=` in main.py, berechnet via Skyfield live. LocationDetail ruft diesen Endpoint async auf.
- Betroffene Dateien: `backend/main.py` (neuer Endpoint), `web/index.html`
- Vorteile: Immer aktuell (auch für Locations ohne recent precompute); kein Cache-Umbau
- Nachteile: Live-Skyfield-Call pro Location-Open (50–200ms); Event-Detail bekommt keinen Azimut (zwei getrennte Implementierungen); höherer Aufwand
- Aufwand: mittel

**Option C — Nur Event-Detail, kein Location-Detail**

Was du in der App erlebst: Im Event-Detail (Feed, Kalender) siehst du den Azimut. Im Location-Detail bleibt der Ausrichtungs-Abschnitt wie bisher (ohne heutige Auf-/Untergangs-Klassifizierung).

- Vorgehen: Nur precompute + Schema + Event-Detail-Template
- Vorteile: Minimaler Aufwand
- Nachteile: Kern-Use-Case (Planungsansicht für eine Location) nicht abgedeckt; Ticket-Beschreibung zielt klar auf Location-Planungssicht
- Aufwand: sehr klein

✅ **Empfehlung: Option A** — minimaler Aufwand, maximaler Wert, konsistent mit dem moonrise_azimuth-Pattern aus US-79, kein Extra-API-Call nötig. Die leichte Einschränkung (Azimut nur nach Precompute) ist akzeptabel, da der Precompute täglich läuft und bei Location-Änderungen getriggert wird.

---

**Scope:**
- Eingeschlossen: (1) `sunrise_azimuth` + `sunset_azimuth` im Opportunity-Cache + Schema; (2) Azimut neben Sonnenaufgang/-untergang im Event-Detail; (3) Richtungsklassifizierung relativ zum Motiv im Location-Detail-Ausrichtungs-Abschnitt (heute)
- Ausgeschlossen: Datums-Picker für die Richtungsklassifizierung (→ Live-Astro); iOS-App; Push-Benachrichtigungen für „heute perfektes Alignment"; Änderungen am Precompute-Trigger-Mechanismus

**Akzeptanzkriterien:**
- [ ] AK-1: Wenn ich eine Foto-Chance (z.B. „Goldene Stunde Abend") im Feed öffne, sehe ich neben „Sonnenaufgang" und „Sonnenuntergang" jeweils auch den Azimut in Grad — z.B. „Sonnenuntergang 21:05 · 289°".
- [ ] AK-2: Sonnenaufgang und -untergang werden im Event-Detail nur mit Azimut angezeigt, wenn der Wert im Cache vorhanden ist. Wenn er fehlt (alter Cache-Stand), erscheint nur die Uhrzeit — kein „0°" oder Fehler.
- [ ] AK-3: Im Location-Detail (Abschnitt „Ausrichtung") sehe ich für den heutigen Tag Sonnenauf- und -untergang mit Azimut.
- [ ] AK-4: Wenn die Location Motiv-Koordinaten hat, erscheint zusätzlich eine lesbare Einschätzung — z.B. „fast genau hinter dem Motiv (2°)" oder „Gegenlicht-Motive möglich (158°)". Locations ohne Motiv zeigen nur Azimut ohne Bewertung.
- [ ] AK-5: Wenn die Richtungsabweichung ≤ 15° beträgt (Sonne fast genau am Motiv), wird das optisch hervorgehoben (z.B. mit Flammen-Emoji oder Farbe) — als klares Planungs-Signal.
- [ ] AK-6: Ein Azimut von 0° wird korrekt angezeigt (nicht versteckt), weil die Sonne theoretisch genau im Norden aufgehen könnte.
- [ ] AK-7: Wenn heute kein Sonnenaufgang oder -untergang stattfindet (Polarsommer/Edge), erscheint kein leerer oder kaputt wirkender Bereich — das Feld wird einfach weggelassen.
- [ ] AK-8: Die Azimut-Werte im Event-Detail stimmen mit dem überein, was die Live-Astro-Ansicht für denselben Tag anzeigt (Konsistenz-Check, manuelle Probe).
- [ ] Edge Case: Locations ohne Motiv-Koordinaten → im Location-Detail erscheint im Ausrichtungs-Abschnitt trotzdem Sonnenauf-/-untergangs-Azimut (nur ohne Motivvergleich).

**Pre-Mortem (Zusammenfassung):**
- 💀 Sunrise-Azimut-Call blockiert Sheet → Gegenmaßnahme: nur aus precompute-Cache, nicht live (Option A)
- 💀 Klassifizierung nur für Locations mit Motiv → Gegenmaßnahme: sauberes Fallback (nur Azimut ohne Motivbezug)
- 💀 Datenquelle-Inkonsistenz Location- vs. Event-Detail → Gegenmaßnahme: beide aus precompute-Cache
- 💀 sunrise=None → TypeError → Gegenmaßnahme: Guard wie in moonrise_azimuth-Pattern
- 💀 Azimut 0° als falsy in JS → Gegenmaßnahme: `!= null` statt Truthy-Check

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `backend/precompute.py`, `backend/models/schemas.py`, `backend/main.py`, `web/index.html` (Z.3343–3344, Z.4584–4665)
- [ ] Implementierungsoption freigegeben: Option A (Azimut im Cache + Klassifizierung im Frontend)
- [ ] Empfehlung: Option A

**Testplan:**
- [ ] Automatisiert (pytest): `backend/tests/test_us107_sunrise_azimuth.py`
  - AK-1/AK-2: `_serialize()` gibt `sunrise_azimuth` / `sunset_azimuth` als float oder None zurück — keine 0.0 wenn sunrise=None
  - AK-6: sunrise_azimuth=0.0 (Norden) bleibt 0.0, nicht None
  - AK-7: sunrise=None → sunrise_azimuth=None (kein Crash)
- [ ] Manuell:
  1. Server lokal starten, Feed öffnen, Chance öffnen → Event-Detail prüfen: Sonnenaufgang mit Azimut?
  2. Location-Detail öffnen (Location mit Motiv-Koordinaten) → Ausrichtungs-Abschnitt: Klassifizierung sichtbar?
  3. Location ohne Motiv-Koordinaten → Ausrichtungs-Abschnitt: nur Azimut, keine Klassifizierung, kein Fehler?
  4. Wert mit Live-Astro-Ansicht für denselben Tag vergleichen (AK-8)
  5. Regression: Mondaufgang/-untergang noch sichtbar? Feed-Filter noch funktionsfähig?

<!-- ===== INBOX: neue Tickets 2026-06-20 (warten auf Stephans Gate → Ready for Analysis) ===== -->

### US-124 · Vollbild-Modus für die Karte beim Anlegen eines neuen Standorts `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-04 |

**Beschreibung:** Beim Anlegen eines neuen Standorts (AddLocation-Formular) lässt sich die Karte bislang nur in der kleinen Formular-Vorschau bedienen. Ein eigener Vollbild-Modus mit Zoom sowie Satellit-/Standard-Kartenwahl soll die präzise Positionierung des Standort-Pins erleichtern.

**User Story:** Als Fotograf/in, möchte ich beim Anlegen eines neuen Standorts in den Vollbildmodus wechseln können, in dem sowohl Zoom als auch Satellit- und Standard-Kartenansicht verfügbar sind, sodass ich den Standort-Pin präziser positionieren kann.

**Bezug:** Überträgt das bei US-87[x] (Vollbild-Overlay Bearbeiten-Karte, `openMapFullscreen()`/`_initEditMapFs()`) etablierte Muster auf den Anlege-Flow (`AddLocation`), der laut Code-Stand (Stand 2026-07-04) bislang keine eigene Vollbild-Kartenfunktion besitzt — nur `LocationDetail` (Bearbeiten) und `CameraFOV` (Blickwinkel-Vorschau) haben bereits `openMapFullscreen()`. Ergänzt sich mit US-123[x] (Satellit-/Standard-Umschalter `LocMapMode`, bereits auf der kleinen Anlege-Karte `add-map` vorhanden über `AddLocation.setLocMapLayer()`) — im neuen Vollbild-Modus muss dieser Umschalter mit übernommen werden, analog zu AK4 aus US-123 (Vollbild zeigt denselben Kartentyp wie die zugehörige kleine Karte). Keine Dublette; kein Zusammenhang mit US-114[x] (readonly-Vollbild bei Chancen/Kalender/Scout, dort ausdrücklich ohne Pin-Setzen).

**Bereits geklärte Fragen (Stephan, 2026-07-04):**
1. Pin-Setzmechanismus im Vollbild: Antippen (wie bisher beim Anlegen) — NICHT Ziehen/Draggable wie bei US-87. Der aktive Punkt (Beobachter oder Motiv) springt beim Antippen der Karte dorthin.
2. Modus-Umschalter "Beobachter/Motiv setzen": Ja, auch im Vollbild sichtbar/bedienbar — man muss dafür nicht zur kleinen Karte zurück.

**Bestätigte Annahmen (Stephan, 2026-07-04):**
- Vollbild öffnet sich über das bereits bekannte Vollbild-Symbol (gleiches Icon wie beim Bearbeiten, US-87) auf der kleinen Anlege-Karte.
- Geschlossen wird über ein "X"-Symbol.
- Die im Vollbild gesetzte Position wird beim Schließen automatisch auf die kleine Karte + Koordinatenfelder übernommen, ohne extra Bestätigungsschritt.
- Beim Öffnen zeigt das Vollbild den aktuellen Kartenausschnitt (Zoom, Kartentyp) und bereits gesetzte Punkte — keine zurückgesetzte Standardansicht.
- Ist noch kein Punkt gesetzt, zeigt das Vollbild einfach keinen Punkt (kein Fehler).

**Example Mapping (Kurzfassung):**
- 📏 Regel 1: Von kleiner Anlege-Karte per Symbol ins Vollbild wechseln, bestehende Pins bleiben sichtbar.
- 📏 Regel 2: Im Vollbild zoomen/verschieben + Satellit/Standard-Umschalter (US-123) verfügbar, zeigt denselben Kartentyp wie die kleine Karte.
- 📏 Regel 3: Pin im Vollbild per Antippen setzen (aktiver Punkt je nach Beobachter/Motiv-Umschalter).
- 📏 Regel 4: Vollbild schließen (X) → letzter Stand (Pin-Position, Kartentyp) erscheint sofort auf der kleinen Karte, ohne Speichern des Formulars.

**Scope:**
Eingeschlossen: Vollbild-Symbol auf der kleinen Anlege-Karte (`add-map`), Vollbild-Overlay mit großer Karte, Satellit/Standard-Umschalter (US-123) und Beobachter/Motiv-Umschalter im Vollbild, Antippen-basiertes Pin-Setzen im Vollbild, automatische Übernahme auf die kleine Karte + Koordinatenfelder beim Schließen.
Ausgeschlossen: Draggable Pins im Vollbild (bleibt Antippen wie bisher). Keine Änderung am bestehenden Bearbeiten-Vollbild (US-87) oder am readonly-Vollbild (US-114) — beide bleiben unverändert bestehen, nur als Vorbild/Musterquelle genutzt. Kein Speichern des Formulars beim Schließen des Vollbilds (nur Übernahme in die Formularfelder, wie beim bisherigen Verhalten der kleinen Karte).

**Akzeptanzkriterien:**
- [ ] Auf der kleinen Karte im "Neue Location"-Formular ist ein Vollbild-Symbol sichtbar (gleiches Icon/Position wie beim Bearbeiten einer Location, US-87).
- [ ] Tippen auf das Vollbild-Symbol öffnet eine bildschirmfüllende Kartenansicht; bereits gesetzte Beobachter-/Motiv-Punkte sind darin sofort sichtbar, an derselben Position wie auf der kleinen Karte.
- [ ] Im Vollbild lässt sich zoomen und die Karte verschieben.
- [ ] Im Vollbild ist der Satellit/Standard-Umschalter (aus US-123) vorhanden und zeigt beim Öffnen denselben Kartentyp, der auch auf der kleinen Karte aktiv war.
- [ ] Im Vollbild ist der Umschalter "Mein Standort setzen" / "Motiv setzen" vorhanden und bedienbar, ohne dass man dafür das Vollbild verlassen muss.
- [ ] Tippen auf eine Stelle der Vollbild-Karte setzt den aktuell aktiven Punkt (Beobachter oder Motiv, je nach Umschalter-Stellung) dorthin — genau wie bisher bei der kleinen Karte.
- [ ] Das Vollbild lässt sich über ein "X"-Symbol schließen.
- [ ] Nach dem Schließen zeigt die kleine Karte sofort die im Vollbild zuletzt gesetzte(n) Position(en) sowie den zuletzt gewählten Kartentyp (Satellit/Standard); die Koordinatenfelder ("Mein Standort", "Motiv") sind mit denselben Werten befüllt.
- [ ] Das Formular wird durch das Öffnen/Schließen des Vollbilds nicht automatisch gespeichert — "Location dauerhaft speichern" bleibt ein separater, expliziter Schritt.
- [ ] Edge Case: Ist beim Öffnen des Vollbilds noch kein Beobachter- und/oder Motiv-Punkt gesetzt, zeigt die Vollbild-Karte einfach keinen Pin für den jeweils fehlenden Punkt (kein Fehler, keine Blockade).
- [ ] Edge Case: Wechselt man im Vollbild den Kartentyp (Satellit/Standard), übernimmt auch die kleine Karte (und alle anderen sichtbaren Umschalter, gemeinsame Einstellung laut US-123 AK7) diesen Kartentyp nach dem Schließen.
- [ ] Edge Case: Wechselt man im Vollbild den Beobachter/Motiv-Modus und tippt danach auf die Karte, wird ausschließlich der gerade aktive Punkt verändert; der jeweils andere bereits gesetzte Punkt bleibt unangetastet.

**Pre-Mortem:**

📎 Code-Verifikation (gelesen 2026-07-04, `web/index.html`):
- Bestätigt: Es existieren bereits zwei Vollbild-Varianten desselben visuellen Musters: `LocationDetail.openMapFullscreen()` (Zeile 5549, US-87, draggable Pins, Formularfelder als Quelle der Wahrheit, DOM-IDs `edit-map-fs-*`) und `CameraFOV.openMapFullscreen(prefix)` (Zeile 3848, US-114, readonly, keine Drag-Handler, DOM-IDs `fov-map-fs-*`, prefix-parametrisiert). Beide sind eigene, vollständig ausprogrammierte Funktionen mit eigenem statischen DOM-Block (kein generischer, wiederverwendbarer Kern) — jede Komponente (`LocationDetail`, `CameraFOV`) hat ihre eigene `openMapFullscreen()`-Methode und ihren eigenen State (`_editMapFs`/`_editObsMFs` bzw. eigene `_maps[fsKey]`-Struktur).
- Widerlegt: `openMapFullscreen()` ist **nicht** generisch genug, um 1:1 für `AddLocation` wiederverwendet zu werden. Sie ist fest an `LocationDetail._current`, die Bearbeiten-Formularfelder (`edit-obs-coords`/`edit-subj-coords`) und ihre eigenen DOM-IDs gekoppelt (Zeile 5565–5622: `_initEditMapFs()`, `_reloadEditMapFsFromFields()` lesen explizit aus den Edit-Feldern). `AddLocation` hat andere Feld-IDs (`obs-coords`/`subj-coords`) und einen eigenen State (`this.obs`/`this.subj`, `this.obsMarker`/`this.subjMarker`, `this.mapMode`). Eine echte 1:1-Wiederverwendung ohne Parametrisierung ist nicht möglich.
- Klick-Handler fürs Pin-Setzen beim Anlegen (bereits vorhanden, Zeile 5995–6003): `this.map.on('click', e => { if (this.mapMode === 'obs') { this.setObserver(...); ... } else { this.setSubject(...); } })` — ein einfacher Leaflet-`click`-Event auf der kleinen `add-map`-Instanz, kein Drag. Dieses Pattern (Antippen, kein Draggable) ist bereits exakt das von Stephan bestätigte Verhalten fürs Vollbild — es muss nur auf eine zweite Karten-Instanz (`add-map-fs`) übertragen werden, mit denselben `setObserver()`/`setSubject()`-Aufrufen (diese schreiben bereits in `this.obs`/`this.subj` + Koordinatenfelder + Marker, unabhängig davon welche Karteninstanz den Klick ausgelöst hat).
- Modus-Umschalter (`AddLocation.setMapMode()`, Zeile 5959–5968) ist bereits komponentenweit (nicht kleine-Karte-lokal): er schreibt `this.mapMode`, aktualisiert die Buttons `#mode-obs`/`#mode-subj` und den Hinweistext `#add-map-hint`. Diese IDs existieren nur einmal im DOM (nicht prefix-parametrisiert) — ein zweiter, baugleicher Umschalter im Vollbild-Overlay muss eigene IDs bekommen und `setMapMode()` so erweitern, dass er beide Button-Paare (klein + Vollbild) synchron hält, analog zum bestehenden `LocMapMode.syncAllToggles()`-Muster für den Kartentyp-Umschalter.
- Satellit/Standard-Umschalter (`LocMapMode`, Zeile 3565ff.): bereits vollständig generisch und komponentenübergreifend nutzbar (`toggleHtml()`, `switchTileLayer()`, `syncAllToggles()`); `AddLocation.setLocMapLayer()` (Zeile 5978) nutzt dieses Muster bereits für die kleine Karte. Für die Vollbild-Karte reicht ein zweiter `LocMapMode.addTileLayer()`-Aufruf auf der neuen Karteninstanz plus ein zweiter `toggleHtml()`-Container, exakt wie bei US-87/US-114 bereits gelöst.

💀 Szenario 1: Vollbild-Karten-Container hat beim Öffnen 0px Höhe (Leaflet-Gotcha, bereits bei US-87/US-114 bekannt), weil die Öffnen-Animation noch läuft.
   Auslöser: Karteninitialisierung direkt beim Klick, nicht nach Abschluss der CSS-Transition.
   Frühwarnung: Vollbild-Karte zeigt nur graue Kacheln oder ist leer, obwohl `map.invalidateSize()` aufgerufen wurde.
   Gegenmaßnahme: Gleiches Muster wie US-87/US-114 übernehmen — `setTimeout(() => this._initAddMapFs(), 300)` nach dem Öffnen, danach `invalidateSize()`. In AK/Testplan als manueller Testschritt verankert.

💀 Szenario 2: Die beiden Beobachter/Motiv-Umschalter (klein + Vollbild) laufen auseinander — z.B. Vollbild zeigt "Motiv setzen" aktiv, kleine Karte noch "Mein Standort setzen".
   Auslöser: `setMapMode()` aktualisiert bisher nur die eine bekannte Button-Paar-ID; ein zweites Button-Paar im Vollbild wird beim Umschalten nicht mitgezogen.
   Frühwarnung: Nach Modus-Wechsel im Vollbild zeigt die kleine Karte (nach Schließen) einen anderen Hinweistext/Button-Zustand als zuletzt im Vollbild gewählt.
   Gegenmaßnahme: `setMapMode()` erweitern, sodass sie alle im DOM vorhandenen Button-Paare synchron hält (analog `LocMapMode.syncAllToggles()`), nicht nur `#mode-obs`/`#mode-subj`. Als eigenes AK (Edge Case Modus-Wechsel) verankert.

💀 Szenario 3: Kartentyp (Satellit/Standard) wird im Vollbild gewechselt, aber die kleine Karte zeigt nach dem Schließen weiterhin den alten Kartentyp.
   Auslöser: `setLocMapLayer()` aktualisiert nur die Karteninstanz, auf der der Umschalter geklickt wurde, ohne die andere Instanz (`this.map` vs. neue Vollbild-Instanz) nachzuziehen.
   Frühwarnung: Nach Schließen zeigt kleine Karte einen anderen Kartenhintergrund als zuletzt im Vollbild sichtbar.
   Gegenmaßnahme: Analog zum bereits bei US-87/US-114 gelösten Muster beide Tile-Layer-Referenzen (`this._tileLayer` für klein, neue `this._tileLayerFs` fürs Vollbild) bei jedem Umschalten über `LocMapMode.switchTileLayer()` je Instanz aktualisieren + `syncAllToggles()` nutzen. Bereits als AK (Kartentyp-Konsistenz) verankert.

💀 Szenario 4: Punkt wird im Vollbild gesetzt, aber beim Schließen erscheint er nicht auf der kleinen Karte (oder umgekehrt: doppelte/verwaiste Marker).
   Auslöser: Vollbild-Klick-Handler setzt eigene, von der kleinen Karte unabhängige Marker-Referenzen statt der bestehenden `setObserver()`/`setSubject()`-Methoden zu nutzen, die bereits Koordinatenfelder + `this.obsMarker`/`this.subjMarker` pflegen.
   Frühwarnung: Nach Schließen fehlt der Pin auf der kleinen Karte, obwohl die Koordinatenfelder befüllt sind (oder umgekehrt).
   Gegenmaßnahme: Vollbild-Klick-Handler ruft dieselben `setObserver()`/`setSubject()`-Methoden auf wie die kleine Karte (diese sind bereits kartenunabhängig implementiert — sie schreiben in `this.obs`/`this.subj` + Felder + `this.obsMarker`/`this.subjMarker` auf `this.map`). Für die Vollbild-Karte selbst braucht es einen zusätzlichen, parallel gepflegten Marker (analog zu `_editObsMFs`/`_editSubjMFs` bei US-87), der bei jedem Setzen auf beiden Karten aktualisiert wird. Als AK ("kleine Karte zeigt sofort denselben Stand") verankert.

💀 Szenario 5: Vollbild wird mehrfach geöffnet/geschlossen (Formular bleibt offen, mehrere Versuche) — alte Karteninstanz/Marker/Event-Handler sammeln sich an (Memory-Leak / doppelte Klick-Handler).
   Auslöser: Bei jedem Öffnen wird eine neue `L.map()`-Instanz erzeugt, ohne die vorherige zu prüfen/wiederzuverwenden (anders als bei `LocationDetail`, die bereits `if (this._editMapFs) { ...invalidateSize(); return; }` prüft).
   Frühwarnung: Nach mehrfachem Öffnen/Schließen reagiert das Vollbild träge oder ein Klick löst mehrere `setObserver()`-Aufrufe gleichzeitig aus.
   Gegenmaßnahme: Gleiches Wiederverwendungs-Muster wie `LocationDetail._initEditMapFs()` übernehmen — Karteninstanz nur einmal erzeugen, bei erneutem Öffnen nur `invalidateSize()` + Neu-Einlesen der aktuellen Punkte. Als manueller Testschritt (mehrfaches Öffnen/Schließen) im Testplan verankert.

**Render-Pfad-Check (Schritt 4g):** Die Vollbild-Karte ist eine client-seitig gerenderte Leaflet-Instanz (`L.map(...)`), exakt wie die kleine `add-map`-Karte und wie die bestehenden Vollbild-Karten aus US-87/US-114. Keine Server-Assets (kein PNG/Rendering-Endpoint) beteiligt. Die Steuerelemente (Satellit/Standard-Umschalter, Beobachter/Motiv-Umschalter) sind HTML/JS-Overlays über der Leaflet-Karte, nutzen denselben Rendering-Pfad wie auf der kleinen Karte (kein separater/abweichender Pfad wie bei BUG-59). Kein zusätzliches Risiko in diesem Bereich.

**Designer-Check:** Visuell sichtbar (neues Vollbild-Symbol, neues Overlay, zwei Umschalter im Vollbild) → `fotoalert-designer` konsultiert. Ergebnis: Vollbild-Symbol und Grundstruktur (Header + X, große Karte, Satellit/Standard-Umschalter unten) 1:1 wie bei US-87/US-114 übernehmen — reine Wiederverwendung, keine Designabweichung nötig. Für den zusätzlich benötigten Beobachter/Motiv-Umschalter (den es bei US-87/US-114 nicht gibt, da dort Drag statt Antippen): als eigene Zeile **unterhalb der Titel/X-Zeile im Header** platzieren (bestehende `.map-mode-bar`-Optik 1:1 übernehmen), NICHT neben dem Satellit/Standard-Umschalter unten auf der Karte. Begründung: funktional unterschiedliche Steuerungsebenen (Vor-Aktion "was setze ich" oben vs. Ansichts-Einstellung "wie sehe ich die Karte" unten) werden räumlich getrennt statt in einer Leiste vermischt — kein neuer Radius, keine neue Farbe, keine Kollision mit dem Schließen-Button.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt (Code-Verifikation gegen `web/index.html`, 5 Versagensszenarien)
- [x] Architektur analysiert: betroffene Datei `web/index.html` — neue DOM-Blöcke `add-map-fs-overlay`/`add-map-fs-sheet` (analog Zeile 1204–1227), neue CSS-Regeln (analog Zeile 573–608), Erweiterung `AddLocation` um `openMapFullscreen()`/`closeMapFullscreen()`/`_initAddMapFs()`/`_reloadAddMapFsFromFields()` (analog Zeile 5549–5633), Erweiterung `setMapMode()`/`setLocMapLayer()` um Zwei-Instanzen-Sync
- [x] Designer-Check: visuell? → ja, `fotoalert-designer` aufgerufen (Ergebnis siehe oben)
- [ ] Implementierungsoptionen: A / B
- [ ] Empfehlung: Option A

**Implementierungsoptionen:**

### Option A — Vollbild-Muster aus US-87 auf AddLocation übertragen (Wiederverwendung per Anpassung)
- Alltagssprache: Die Anlege-Karte bekommt genau das gleiche Vollbild-Erlebnis, das es beim Bearbeiten einer Location schon gibt — nur eben mit Antippen statt Ziehen, und mit dem zusätzlichen Beobachter/Motiv-Umschalter direkt im Vollbild. Sieht für Stephan vertraut aus, verhält sich aber an die richtige Stelle angepasst.
- Vorgehen: Neuer DOM-Block `add-map-fs-overlay`/`add-map-fs-sheet` (analog zu `edit-map-fs-*`), neue Methoden in `AddLocation`: `openMapFullscreen()`, `closeMapFullscreen()`, `_initAddMapFs()` (Karteninstanz + Klick-Handler analog zum bestehenden `initMap()`-Klick-Handler, ruft dieselben `setObserver()`/`setSubject()` auf), Marker auf der Vollbild-Instanz parallel zu `obsMarker`/`subjMarker` pflegen. `setMapMode()` und `setLocMapLayer()` werden erweitert, um beide Karteninstanzen + beide Umschalter-Paare synchron zu halten (Muster bereits durch `LocMapMode.syncAllToggles()` vorgegeben).
- Betroffene Dateien: nur `web/index.html` (HTML-Block, CSS-Block, `AddLocation`-Objekt).
- Vorteile: Visuell und funktional konsistent mit bereits etabliertem, bewährtem Muster (US-87/US-114); nutzt bestehende `setObserver()`/`setSubject()`/`LocMapMode`-Bausteine vollständig weiter; kein Risiko für die bestehenden Vollbild-Overlays (eigener, neuer DOM-Block, keine Änderung an `LocationDetail`/`CameraFOV`).
- Nachteile / Risiken: Etwas Zusatzaufwand für den neuen Beobachter/Motiv-Umschalter-Sync (gibt es bei US-87/US-114 nicht) — siehe Pre-Mortem Szenario 2. Zwei parallele Karteninstanzen (klein + Vollbild) müssen bei jedem Setzen/Umschalten synchron gehalten werden (Szenario 3+4).
- Aufwand: mittel.

**Warum keine Alternative (Option B) sinnvoll ist:** Die Code-Verifikation (Pre-Mortem) zeigt keinen technischen Grund, der gegen die Wiederverwendung des Musters spricht — im Gegenteil, alle benötigten Bausteine (`setObserver()`/`setSubject()`, `LocMapMode`, das Leaflet-Click-Handler-Muster) existieren bereits und sind bereits kartenunabhängig nutzbar. Eine "eigene, schlankere" Vollbild-Logik nur für `AddLocation` würde denselben Code (Karteninit, Tile-Layer, Klick-Handler, Marker-Sync) im Wesentlichen erneut schreiben, ohne einen Vorteil zu bieten — das widerspräche der Skill-Regel "Wiederverwendung bestehender Komponenten ist immer Option A" ohne einen nachvollziehbaren Grund dagegen. Deshalb wird hier keine Option B als echte Alternative aufgeführt.

✅ **Empfehlung: Option A** — einzige sinnvolle Option, da kein technischer Grund für eine Alternative vorliegt; alle Bausteine sind bereits vorhanden und kartenunabhängig, die Erweiterung ist eine reine Anpassung/Parametrisierung des etablierten Musters.

**Testplan:**
- [ ] Automatisiert (Harness): Kein sinnvoller Backend-Testpunkt — das Feature ist rein Frontend/DOM/Leaflet (Kartenanzeige, Klick-Events, Overlay-Sichtbarkeit). Kein pytest-Testfall für US-124; siehe `backend/tests/test_us-124.py` (Hinweis-Datei statt Testfällen).
- [ ] Manuell (unter http://localhost:8000):
  1. Tab "+" öffnen (neue Location anlegen). Kleine Karte muss sichtbar sein.
  2. Auf der kleinen Karte auf das Vollbild-Symbol tippen → Vollbild-Ansicht öffnet sich, Karte füllt den Bildschirm.
  3. Ohne vorher einen Punkt gesetzt zu haben: Vollbild zeigt keinen Pin, keine Fehlermeldung (Edge Case).
  4. Im Vollbild auf eine Stelle tippen (Modus "Mein Standort setzen" ist per Default aktiv) → Beobachter-Pin erscheint an der angetippten Stelle.
  5. Im Vollbild auf "Motiv setzen" umschalten, dann erneut auf eine andere Stelle tippen → Motiv-Pin erscheint dort, Beobachter-Pin bleibt unverändert stehen.
  6. Im Vollbild den Satellit/Standard-Umschalter betätigen → Kartenhintergrund wechselt sichtbar.
  7. Im Vollbild zoomen und die Karte verschieben → funktioniert wie erwartet.
  8. Vollbild über das "X" schließen → kleine Karte zeigt sofort dieselben zwei Pins an denselben Stellen, denselben Kartentyp (Satellit/Standard) wie zuletzt im Vollbild gewählt; Koordinatenfelder "Mein Standort" und "Motiv" sind mit denselben Werten befüllt wie im Vollbild gesetzt.
  9. Formular NICHT speichern, sondern erneut das Vollbild-Symbol antippen → Vollbild öffnet sich erneut mit demselben Zoom/Kartentyp/denselben Pins wie zuletzt (kein Reset).
  10. Vollbild mehrfach hintereinander öffnen/schließen (mind. 3x) → Karte bleibt reaktionsschnell, kein doppeltes Setzen bei einem einzelnen Klick, keine sichtbaren Fehler in der Browser-Konsole.
  11. Regression: Bestehendes Bearbeiten-Vollbild (US-87, Location-Detail → Bearbeiten → Vollbild-Symbol) weiterhin mit Drag-Funktion prüfen — unverändert funktionsfähig.
  12. Regression: Bestehendes readonly-Vollbild (US-114, Chance/Kalender/Scout → "Karte & Blickwinkel" → Vollbild-Symbol) weiterhin ohne Pin-Setzen funktionsfähig.
  13. Regression: Kleine Anlege-Karte (ohne Vollbild) weiterhin wie bisher bedienbar — Modus-Umschalter, Satellit/Standard-Umschalter, GPS-Button, Koordinaten einfügen/eintippen.

---

### US-84 · Passwort-Änderung durch den Host in der App-Oberfläche `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-20 |

**Beschreibung:** Der Host soll sein Passwort direkt über die App-Oberfläche ändern können (statt nur server-/dateiseitig). Voraussichtlich als Sektion in den Einstellungen.

**Bezug:** Abhängig von US-66[x] (Login mit Rollen-Erkennung, Passwort-Mechanismus). Eigenständig. Tangiert den Einstellungs-Bereich, in dem auch US-86 die Host-Aufgabenliste verorten würde.

---

### US-85 · Karte & Blickwinkel: Sichtfeld-Trichter mit Brennweite (gestrichelte Verlängerung) `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-20 |

**Beschreibung:** In der Ansicht „📐 Karte & Blickwinkel" soll der Blickwinkel als Trichter dargestellt werden: durchgezogen (gefüllt) vom Standort bis zum Motiv entsprechend der gewählten Brennweite, und als gestrichelte Linien über das Motiv hinaus verlängert.

**Bezug:** Verfeinert die bereits in US-58[x] umgesetzte FOV-Kegel-Visualisierung; betrifft dieselbe Sektion. Grenzt an BUG-20[x] (Marker in FOV-Karte). Eigenständig, baut auf US-58.

---

### US-114 · Vollbild-Karten-Overlay auch bei Chancen, Kalender und Scout `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-03 |
| **Abgeschlossen** | 2026-07-03 |

✅ **Testbestätigung (Stephan, 2026-07-03):** Manuelle Testschritte (11 Punkte, alle Einstiegspunkte + Regression + Edge Cases) durchgeführt — passt.

✅ **Release (2026-07-03):** Commit `3a6dd3c` — GitHub Actions Run #132 (`conclusion: success`, Frontend-Test-Gate + Deploy grün), Live-Health-Check auf https://fotoalert.stephanschumann.com bestätigt. Hinweis: Release lief per direktem `git commit`/`push`, nicht über das dokumentierte `release.sh`-Skript — App-Versionsnummer in index.html wurde daher nicht hochgezählt (funktional ohne Auswirkung, da Deploy bei jedem Push nach main läuft und der Service-Worker-Cache-Name serverseitig neu gestempelt wird).

✅ **Weg-Gate-Freigabe (Stephan, 2026-07-03):** Nur eine große, reine Ansichts-Karte (kein Pin-Setzen). US-114 deckt den „Chancendetails: Karte größer"-Teil aus PRODUCT.md §13 mit ab. Umsetzung nach Option A (eigene, einfache Vollbild-Ansicht fürs Ansehen, getrennt vom bestehenden Bearbeiten-Vollbild aus US-87).

**Beschreibung:** Das bildschirmfüllende Karten-Overlay, das US-87 für die Bearbeiten-Karte im Location-Detail eingeführt hat, soll auch in anderen Ansichten verfügbar sein — konkret bei Chancen, im Kalender und bei den Scout-Karten. Ziel: dieselbe großformatige, gut navigierbare Kartendarstellung, dort wo aktuell nur kleine oder weniger komfortable Kartenansichten existieren.

⚠️ **Offene Annahme (nicht von Stephan bestätigt, muss in der Analyse-Phase geklärt werden):** Bei Chancen/Kalender/Scout geht es vermutlich NICHT ums Pin-Setzen (das ist nur beim Bearbeiten einer Location sinnvoll), sondern um eine **readonly, aber großformatige** Kartenansicht — ähnlich der bereits bestehenden readonly „Karte & Blickwinkel"-Ansicht (US-58/`CameraFOV`), nur eben bildschirmfüllend statt klein (aktuell fix 220px hoch). Zu klären: Soll das bestehende Vollbild-Overlay-Muster aus US-87 (technisch: `openMapFullscreen()`/`closeMapFullscreen()`/`_initEditMapFs()`, pin-fähig) wiederverwendet und um eine readonly-Variante ergänzt werden, oder ist eine eigene, einfachere Vollbild-Darstellung für `CameraFOV` gemeint?

**Scope-Hinweis (Ergänzung PM-Intake):** Stephan nennt explizit Chancen, Kalender und Scout. Code-Recherche zeigt zusätzlich zwei weitere Kartenkontexte, die er nicht erwähnt hat und die bei diesem Anliegen mitbedacht werden sollten (auch wenn der Scope am Ende bei den drei genannten Stellen bleibt):
- Die readonly „Karte & Blickwinkel"-Sektion (`CameraFOV`, US-58) ist bereits eine **wiederverwendbare Komponente** mit zwei Einbindungen: Location-Detail (`prefix='loc'`) und Chancen-Detail (`prefix='ev'`). Kalender und Scout haben laut Recherche aktuell **keine eigene Kartendarstellung** — sie nutzen vermutlich dasselbe Event-/Sheet-Grundgerüst wie der Feed, ggf. muss geprüft werden ob/wo dort überhaupt schon eine Karte sichtbar ist.
- Der **Haupt-Karten-Tab** (`MapView.init`, eigenständige Leaflet-Implementierung, komplett getrennt von `CameraFOV` und der Edit-Karte) wurde von Stephan nicht genannt und ist vermutlich nicht gemeint (bereits bildschirmfüllend), sollte aber zur Vollständigkeit in der Analyse kurz explizit ausgeschlossen werden.

**Bezug:** Baut auf US-87[x] (Vollbild-Overlay-Muster, bisher nur Bearbeiten-Karte im Location-Detail, pin-fähig) — dieses Ticket überträgt das Erlebnis auf weitere, aktuell kleinere Kartenansichten. **Wichtige Überschneidung:** PRODUCT.md §13 führt US-95 „Chancendetails: Buttons kleiner, Karte größer" als offenen, noch nicht umgesetzten Punkt — dafür existiert kein eigener Ticket-Block in BACKLOG.md (nur eine Nebenerwähnung in Zeile 376 als Kind-Ticket-Kandidat des Bauhaus-Epics US-98). Das Anliegen „Karte größer" bei Chancendetails deckt sich inhaltlich mit einem Teil des Scopes dieses Tickets (Chancen-Karte vergrößern). In der Analyse-Phase klären: Wird US-114 zum Sammelticket, das US-95 (Chancendetails-Teil) mit abdeckt/ersetzt, oder bleiben beide getrennt (US-95 z.B. auch für die Button-Verkleinerung, die über die reine Kartengröße hinausgeht)? Grenzt zusätzlich an US-58[x] (readonly FOV-Karte, technische Basis der Chancen-Karte) und US-85[ ] (Sichtfeld-Trichter in derselben FOV-Sektion, unabhängig von diesem Ticket).

---
#### Analyse-Phase (2026-07-03)

**Annahmen-Protokoll — Klärung der offenen Fragen aus dem Ticket:**

Alle drei im Ticket offen gelassenen Fragen konnten durch Code-Lektüre (nicht durch Vermutung) beantwortet werden:

1. **Pin vs. readonly:** ✅ Geklärt durch Architektur — es geht eindeutig um **readonly**. Chancen, Kalender-Einträge und Scout-Vorschläge haben keine editierbaren Koordinatenfelder (die gibt es nur beim Bearbeiten einer Location). Das Pin-Setzen aus US-87 ist hier nicht anwendbar.
2. **Kalender/Scout ohne eigene Karte:** ✅ Bestätigt. Kalender-Klick (`CalendarView.openDetail`) und Scout-Klick (`Scout.openDetail`) laden beide dasselbe zentrale Detail-Sheet (`Detail.open`) wie der Feed. Dieses Sheet rendert für jede Chance dieselbe Sektion „Karte & Blickwinkel" (`CameraFOV.panelHtml('ev')`, fix 220px hoch) — das heißt: Kalender und Scout haben **schon heute** dieselbe kleine Karte wie Chancen, weil sie dasselbe Sheet benutzen. Es gibt keinen separaten Kalender- oder Scout-Karten-Code, der getrennt erweitert werden müsste.
3. **US-87-Muster wiederverwendbar?** ⚠️ Teilweise. Das bestehende Vollbild-Overlay ist technisch **fest auf den Bearbeiten-Fall zugeschnitten**: eigener, einmaliger DOM-Block mit festem Titel „Pins setzen", eigener Namensraum ausschließlich in der Bearbeiten-Komponente, Logik zum Verschieben von zwei Pins mit Rückschreiben in Formularfelder. Das lässt sich nicht 1:1 auf eine readonly-Ansicht ummünzen — es muss eine **zweite, einfachere Variante** des Vollbild-Overlays entstehen (gleiches optisches Muster: Karte füllt den ganzen Bildschirm, Schließen-Kreuz oben, Klick auf Hintergrund schließt), aber ohne Pin-Zieh-Logik und mit passendem Titel.

⚠️ **Zusätzliche Annahme (Default, bitte bestätigen):** Da Kalender und Scout dasselbe Sheet wie Chancen nutzen, bedeutet „Vollbild-Karte bei Chancen, Kalender und Scout" technisch **eine einzige Änderung an einer Stelle** (der gemeinsamen Karten-Sektion mit `prefix='ev'`) — nicht drei getrennte Umsetzungen. Für das Location-Detail (`prefix='loc'`) wird die readonly-Vollbild-Option ebenfalls automatisch mitgezogen, da dieselbe Komponente verwendet wird; das ist als positiver Nebeneffekt zu werten, nicht als Scope-Erweiterung.

**Scope:**
- **Eingeschlossen:** Ein „Vollbild öffnen"-Button/Icon an der readonly „Karte & Blickwinkel"-Sektion (überall, wo diese Sektion erscheint: Chancen-Detail, Kalender-Detail, Scout-Detail, Location-Detail). Beim Öffnen erscheint dieselbe Karte (Beobachter-Pin, Motiv-Pin, Sichtachse, Sichtfeld-Kegel) bildschirmfüllend, ohne Zieh-/Bearbeitungsfunktion. Schließen führt zurück zur vorherigen Ansicht, ohne Datenänderung.
- **Ausgeschlossen:** Der Haupt-Karten-Tab (eigenständige Leaflet-Karte, bereits bildschirmfüllend) — bleibt unverändert, ist nicht Teil dieses Tickets. Das Bearbeiten-Vollbild-Overlay aus US-87 (Pin-Setzen) bleibt unverändert bestehen; es wird nicht angefasst, nur um eine zweite Variante ergänzt.
- **US-95-Frage (Chancendetails: Karte größer):** Empfehlung **zusammenlegen, nicht separat halten** für den Kartengrößen-Teil — sobald das Vollbild-Overlay verfügbar ist, ist „Karte größer machen" für Chancendetails durch einen Tap erledigt, ein zusätzliches Ticket für dieselbe Karte wäre doppelte Arbeit. Der in US-95 zusätzlich erwähnte Teil „Buttons kleiner" ist ein eigenständiges, rein optisches Anliegen (Button-Größen im Chancen-Detail) ohne technischen Bezug zur Karte — dieser Teil bleibt außerhalb von US-114 und sollte, falls weiter gewünscht, als eigenes kleines Ticket geführt werden.

**Example Mapping:**

📏 **Regel 1 — Vollbild-Zugang an jeder „Karte & Blickwinkel"-Ansicht.** Überall wo die kleine Karten-Sektion mit Beobachter- und Motiv-Pin angezeigt wird, gibt es ein sichtbares Symbol, das die Karte bildschirmfüllend öffnet.
- 🟢 Beispiel: Stephan öffnet eine Chance aus dem Feed, scrollt zur Sektion „Karte & Blickwinkel" und sieht dort ein Vollbild-Symbol. Er tippt darauf → die Karte füllt den ganzen Bildschirm aus.
- 🟢 Beispiel: Stephan öffnet dieselbe Chance über den Kalender (Tippen auf einen Kalendertag-Eintrag) → dieselbe Sektion mit demselben Vollbild-Symbol erscheint, Verhalten identisch zum Feed.
- 🟢 Beispiel: Stephan öffnet einen Scout-Vorschlag → auch dort erscheint dieselbe Sektion mit Vollbild-Symbol und identischem Verhalten.

📏 **Regel 2 — Vollbild-Ansicht ist rein informativ (readonly).** In der bildschirmfüllenden Karte lassen sich Beobachter- und Motiv-Position ansehen, aber nicht verschieben.
- 🟢 Beispiel: Stephan öffnet die Vollbild-Karte einer Chance und versucht, den Beobachter-Pin zu verschieben → nichts passiert, der Pin bleibt an Ort und Stelle (kein Ziehen möglich).
- 🟢 Beispiel: Stephan öffnet die Vollbild-Karte, sieht Sichtachse und Sichtfeld-Kegel genauso wie in der kleinen Karte, nur größer und besser erkennbar, und kann hinein-/herauszoomen sowie die Karte verschieben (normale Kartennavigation).

📏 **Regel 3 — Zurück-Verhalten ohne Datenverlust.** Das Schließen der Vollbild-Karte führt verlustfrei zur vorherigen Detailansicht zurück.
- 🟢 Beispiel: Stephan öffnet die Vollbild-Karte einer Chance, tippt auf das Schließen-Kreuz → er landet wieder im Chancen-Detail, alle anderen Sektionen (Wetter, Kamera-Empfehlung etc.) sind unverändert sichtbar.
- 🟢 Beispiel (Edge Case): Stephan tippt statt auf das Kreuz auf den abgedunkelten Hintergrund neben der Karte → dieselbe Schließen-Wirkung wie beim Kreuz.

📏 **Regel 4 — Kein Motiv-Pin gesetzt.** Wenn zu einer Chance kein Motiv-Standort hinterlegt ist, verhält sich das Vollbild-Symbol konsistent zur kleinen Karte.
- 🟢 Beispiel (Edge Case): Stephan öffnet eine Chance ohne Motivkoordinaten. Die kleine Kartensektion zeigt bereits heute den Hinweistext „Keine Motivkoordinaten – Karte nicht verfügbar" statt einer Karte. In diesem Fall gibt es konsequenterweise auch kein Vollbild-Symbol, da keine Karte zum Vergrößern existiert.

**Akzeptanzkriterien:**
- [ ] In der Sektion „Karte & Blickwinkel" (Chancen-Detail, Kalender-Detail, Scout-Detail, Location-Detail) ist ein Vollbild-Symbol sichtbar, sobald eine Karte angezeigt wird.
- [ ] Tippen auf das Vollbild-Symbol öffnet dieselbe Karte (Beobachter-Pin, Motiv-Pin, Sichtachse, Sichtfeld-Kegel) bildschirmfüllend.
- [ ] In der Vollbild-Ansicht lassen sich beide Pins **nicht** verschieben (kein Drag-Verhalten).
- [ ] In der Vollbild-Ansicht funktionieren Zoomen und Verschieben der Karte normal.
- [ ] Ein Schließen-Symbol (Kreuz) oben in der Vollbild-Ansicht führt zurück zur vorherigen Detailansicht, alle übrigen Sektionen bleiben unverändert erhalten.
- [ ] Tippen auf den abgedunkelten Hintergrund außerhalb der Karte schließt die Vollbild-Ansicht ebenso wie das Kreuz.
- [ ] Das Verhalten ist in allen vier Einstiegspunkten identisch: Chancen-Detail (Feed), Kalender-Detail, Scout-Detail, Location-Detail.
- [ ] Edge Case: Hat eine Chance keine Motivkoordinaten, erscheint kein Vollbild-Symbol (analog zum bestehenden Hinweistext statt Karte).
- [ ] Edge Case: Das bestehende Bearbeiten-Vollbild-Overlay (Pin-Setzen im Location-Detail-Editiermodus, US-87) funktioniert unverändert weiter — keine Regression.
- [ ] Edge Case: Wiederholtes Öffnen/Schließen der Vollbild-Karte in derselben Sitzung zeigt konsistent den aktuellen Stand (keine „eingefrorene" Karte von einer zuvor geöffneten anderen Chance).

**Pre-Mortem:**

📎 Code-Verifikation: `web/index.html` gelesen am 2026-07-03.
- Bestätigt: `CameraFOV` (Zeilen ~3456–3650) ist bereits eine gemeinsame Komponente mit Instanzen pro `prefix` (`_maps`, `_cones`, `_data` sind Objekte, geschlüsselt nach `prefix`) — technisch also vorbereitet für mehrere gleichzeitig offene Karten.
- Bestätigt: `CalendarView.openDetail()` (Zeile 2074) und `Scout.openDetail()` (Zeile 1809) rufen beide `Detail.open()` auf; die Sektion „Karte & Blickwinkel" wird in `Detail.open()` einmalig über `CameraFOV.panelHtml('ev')` gerendert (Zeile 3818–3822) — Kalender/Scout haben keinen eigenen Karten-Code.
- Bestätigt: Das US-87-Overlay (`#edit-map-fs-overlay`, `#edit-map-fs-sheet`, `#edit-map-fs`) ist ein **einziger statischer DOM-Block** (Zeilen 1145–1156), fest mit `LocationDetail._editMapFs`/`_initEditMapFs()` verdrahtet, Header-Titel hart codiert auf „Pins setzen". Es ist keine generische, parametrisierbare Komponente — eine Wiederverwendung für readonly-Fälle erfordert einen zweiten, eigenen DOM-Block plus eigene Init-Funktion in `CameraFOV`, nicht nur einen Adapter-Aufruf.
- Widerlegt: Die im Ticket vermutete Möglichkeit, dass Kalender/Scout eine „eigene, einfachere" Kartendarstellung bräuchten, weil sie eventuell einen anderen Datenpfad nutzen — das ist nicht der Fall, beide nutzen identische Chancen-Objektstruktur wie der Feed (bei Scout über einen Adapter, der Feldnamen auf das Feed-Format mappt, Zeile 1840–1864; bei Kalender direkt oder per Feed-Zeit-Abgleich, Zeile 2074–2082, BUG-44).

💀 Szenario: Ein Nutzer öffnet die Vollbild-Karte einer Chance, wechselt (ohne zu schließen) direkt zu einer anderen Chance im Hintergrund (z.B. über Kalender-Navigation), und die Vollbild-Karte zeigt weiterhin die alten Pin-Positionen.
   Auslöser: `CameraFOV._data[prefix]` wird pro Aufruf von `initMap()` neu gesetzt, aber die Vollbild-Instanz müsste bei jedem Öffnen ihre Pins explizit aus dem aktuell offenen Chancen-Objekt neu lesen (analog zum Reload-Muster bei `_reloadEditMapFsFromFields` in US-87 — dort werden die Formularfelder als Quelle der Wahrheit neu eingelesen; bei der readonly-Variante gibt es aber keine Formularfelder, die Quelle wäre direkt das Objekt `o`).
   Frühwarnung: Beim Testen zwei unterschiedliche Chancen kurz hintereinander im Vollbild öffnen und prüfen, ob sich Pins/Kegel tatsächlich aktualisieren.
   Gegenmaßnahme: In AK „Wiederholtes Öffnen/Schließen zeigt konsistent den aktuellen Stand" verankert; Implementierung muss die Vollbild-Karte bei jedem Öffnen aus dem aktuell offenen Detail-Objekt neu befüllen, nicht nur beim ersten Mal.

💀 Szenario: Die Vollbild-Karte wird für das Location-Detail (`prefix='loc'`) geöffnet, während gleichzeitig das bestehende Bearbeiten-Vollbild-Overlay (US-87, `prefix`-unabhängig, eigener DOM-Block) existiert — beide Overlays könnten sich im DOM/CSS überschneiden (z-index-Konflikt) oder der Nutzer verwechselt „Pins setzen"-Overlay mit dem neuen readonly-Overlay.
   Auslöser: Zwei ähnlich aussehende Vollbild-Kartenoverlays im selben Screen-Kontext (Location-Detail hat sowohl eine Bearbeiten-Karte als auch die readonly „Karte & Blickwinkel"-Sektion).
   Frühwarnung: Im Location-Detail (Anzeige-Modus, nicht Bearbeiten) beide Sektionen durchklicken und prüfen, ob eindeutig erkennbar ist, welches Overlay Pins verschiebt und welches nicht (z.B. durch unterschiedlichen Titel: „Pins setzen" vs. „Karte & Blickwinkel").
   Gegenmaßnahme: Neuer DOM-Block bekommt eigenen, klar unterscheidbaren Titel (z.B. „Karte & Blickwinkel", nicht „Pins setzen") und eigene IDs, keine Wiederverwendung der US-87-IDs — verhindert CSS-/JS-Kollision und Nutzerverwirrung.

💀 Szenario: Bei einer Chance ohne Motivkoordinaten wird versehentlich trotzdem ein Vollbild-Symbol angezeigt, das beim Antippen eine leere oder fehlerhafte Karte öffnet.
   Auslöser: Das Vollbild-Symbol wird unabhängig von `hasSub` (vorhandene Motivkoordinaten, siehe `panelHtml()` Zeile 3553) eingebaut, statt an dieselbe Bedingung gekoppelt zu werden, die schon heute entscheidet ob die kleine Karte oder der Hinweistext erscheint.
   Frühwarnung: Eine Chance ohne Motivkoordinaten (z.B. manche Wetter-/Astronomie-Events ohne festes Motiv) im Detail öffnen und prüfen ob ein Vollbild-Symbol erscheint, obwohl keine Karte da ist.
   Gegenmaßnahme: In AK „Edge Case: kein Vollbild-Symbol ohne Motivkoordinaten" verankert; Vollbild-Symbol wird nur im `hasSub`-Zweig von `panelHtml()` gerendert.

💀 Szenario: Die Vollbild-Ansicht wird zwar technisch geöffnet, aber der Sichtfeld-Kegel (`_redrawCone`) fehlt, weil dieser bislang nur für die jeweilige `prefix`-Karteninstanz gezeichnet wird und die neue Vollbild-Instanz einen anderen internen Schlüssel bräuchte (z.B. `prefix + '_fs'`), der beim Kegel-Neuzeichnen nicht mitgedacht wird.
   Auslöser: `_redrawCone(prefix)`, `_updateInfo(prefix)` und `_data[prefix]` sind eng an denselben `prefix`-Schlüssel gekoppelt wie die kleine Karte; eine zweite Karteninstanz mit fremdem Schlüssel muss beim Kegel-Update mitgezogen werden, sonst zeigt das Vollbild nur die Pins ohne Kegel.
   Frühwarnung: Nach Implementierung Vollbild-Karte öffnen und prüfen ob der eingefärbte Sichtfeld-Kegel (nicht nur die gestrichelte Sichtachse) sichtbar ist.
   Gegenmaßnahme: Als Implementierungsdetail in Option A/B (unten) berücksichtigen — Kegel-Zeichnung muss auch für die Vollbild-Karteninstanz aufgerufen werden.

💀 Szenario (UX): Zu viele Vollbild-Symbole in ohnehin schon dichten Detail-Sheets (Chancen-Detail hat bereits viele Sektionen) wirken wie visuelles Rauschen, wenn das Symbol nicht klar erkennbar von anderen Icons unterschieden ist.
   Auslöser: Neues Icon ohne Bauhaus-Konsistenz-Check zur bestehenden Symbolsprache (z.B. Verwechslung mit dem Verifikations- oder Info-Icon).
   Frühwarnung: Screenshot der Sektion mit Stephan gegenchecken, ob das Symbol sofort als „Vollbild öffnen" verstanden wird.
   Gegenmaßnahme: Dasselbe Expand-Icon wiederverwenden, das US-87 bereits für den gleichen Zweck einführt (`#i-expand`, Zeile 5093) — Konsistenz statt neuem Icon; Designer-Check vor Umsetzung (siehe unten).

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` (CameraFOV-Komponente Zeile ~3456–3650, US-87-Overlay Zeile 1145–1156 + 5192–5283, Scout Zeile 1729–1904, CalendarView Zeile 1913–2083, Detail.open Zeile 3644ff.)
- [x] Designer-Check: visuell? → **ja** — neues Icon/Button-Element und neue Vollbild-Kartenansicht sind sichtbare UI-Änderungen. Empfehlung: vor Implementierungsstart `fotoalert-designer` für Icon-Wahl (Wiederverwendung `#i-expand` empfohlen) und Overlay-Optik (Titel, Header-Layout) konsultieren, analog zum bestehenden US-87-Overlay-Stil.
- [x] Implementierungsoptionen: A / B (siehe unten)
- [x] Empfehlung: Option A

**Implementierungsoptionen:**

### Option A — Readonly-Vollbild als zweite Variante der bestehenden Karten-Sektion (empfohlen)
- Vorgehen: Die bestehende „Karte & Blickwinkel"-Sektion (`CameraFOV`) bekommt ein Vollbild-Symbol, das einen **neuen, eigenen** Vollbild-DOM-Block öffnet (ähnliches Aussehen wie das US-87-Overlay: Kreuz oben, abgedunkelter Hintergrund, Karte füllt den Bildschirm) — aber ohne Pin-Zieh-Funktion und mit eigenem Titel „Karte & Blickwinkel" statt „Pins setzen". Die Karte wird beim Öffnen direkt aus dem aktuell angezeigten Chancen-/Location-Objekt befüllt (Beobachter, Motiv, Sichtachse, Kegel) — dieselben Zeichenfunktionen wie die kleine Karte, nur in einer zweiten, größeren Karteninstanz. Da alle vier Einstiegspunkte (Feed, Kalender, Scout, Location-Detail) dieselbe Sektion nutzen, wird die Funktion an **einer** Stelle gebaut und wirkt überall automatisch.
- Betroffene Dateien: nur `web/index.html` (neuer DOM-Block analog Zeile 1145–1156, neue Funktionen in `CameraFOV`, ein Vollbild-Symbol in `panelHtml()`).
- Vorteile: Ein Bauteil für alle vier Einstiegspunkte; nutzt bereits bestehende Zeichenlogik (Pins, Sichtachse, Kegel) vollständig weiter; visuell konsistent mit dem bereits bekannten US-87-Vollbild-Muster, daher für Stephan sofort vertraut; sauber vom Bearbeiten-Fall getrennt (kein Risiko einer versehentlichen Pin-Verschiebung).
- Nachteile / Risiken: Etwas Zusatzaufwand, weil ein zweiter DOM-Block + zweite Karteninitialisierung nötig ist (keine 1:1-Wiederverwendung des US-87-Codes, da dieser pin-fähig und Formular-gebunden ist); Kegel-Zeichnung muss für die neue Karteninstanz mitgezogen werden (siehe Pre-Mortem).
- Aufwand: mittel

### Option B — US-87-Overlay direkt umbauen (Pin-Fähigkeit optional per Flag)
- Vorgehen: Das bestehende US-87-Overlay wird so erweitert, dass es sowohl den Bearbeiten- als auch den readonly-Fall bedient (z.B. per Flag „pins verschiebbar ja/nein"), statt einen zweiten Block zu bauen.
- Betroffene Dateien: `web/index.html` (bestehender Overlay-Block + `LocationDetail`-Funktionen umgebaut).
- Vorteile: Kein zweiter, ähnlicher DOM-Block im Markup.
- Nachteile / Risiken: Vermischt zwei fachlich unterschiedliche Anliegen (Location bearbeiten vs. Chance ansehen) in einer Komponente, die aktuell fest in `LocationDetail` verankert ist — Chancen/Kalender/Scout haben aber gar keinen Bezug zu `LocationDetail`, eine Kopplung dorthin wäre architektonisch unsauber. Höheres Regressionsrisiko für das bereits produktive, funktionierende US-87-Feature (Pin-Setzen), da an derselben Stelle Code für einen komplett anderen Zweck ergänzt wird. Widerspricht dem Grundsatz, bestehende funktionierende Features nicht für sachfremde Zwecke zu verbiegen.
- Aufwand: mittel bis groß (wegen Umbaurisiko am bestehenden, produktiven Feature)

✅ **Empfehlung: Option A** — sie hält das bewährte, produktive US-87-Bearbeiten-Overlay unangetastet (kein Regressionsrisiko für ein Done-Feature), bildet die fachliche Trennung (Bearbeiten vs. Ansehen) auch strukturell sauber ab, und da `CameraFOV` bereits als prefix-parametrisierte Komponente gebaut ist, lässt sich die neue Vollbild-Variante an einer Stelle ergänzen und wirkt automatisch in allen vier Einstiegspunkten (Feed, Kalender, Scout, Location-Detail) — genau das vom Ticket gewünschte Ergebnis, ohne Kalender/Scout-spezifischen Sondercode.

**US-95-Überschneidung — Empfehlung:** Zusammenlegen für den Kartenteil (siehe Scope oben). Der Button-Verkleinerungs-Teil aus US-95 bleibt separat, da er keinen technischen Bezug zur Karte hat und sonst den Scope dieses Tickets unnötig aufbläht.

**Testplan:**
- [ ] Automatisiert (Harness): Dieses Ticket ist überwiegend Frontend-UI (kein Backend-Endpoint, keine Datenberechnung) — kein pytest-Fall in `backend/tests/` vorgesehen. Die Akzeptanzkriterien sind manuell im Browser zu prüfen.
- [ ] Manuell (unter http://localhost:8000):
  1. Feed öffnen → eine Chance mit Motivkoordinaten antippen → zur Sektion „Karte & Blickwinkel" scrollen → Vollbild-Symbol antippen → prüfen: Karte füllt den Bildschirm, Pins + Sichtachse + Kegel sichtbar, Pins lassen sich nicht verschieben.
  2. In derselben Vollbild-Ansicht auf das Schließen-Kreuz tippen → prüfen: zurück im Chancen-Detail, alle Sektionen unverändert.
  3. Denselben Ablauf erneut starten, diesmal auf den abgedunkelten Hintergrund statt das Kreuz tippen → gleiches Schließen-Verhalten.
  4. Kalender öffnen → einen Tag mit Chance antippen → Vollbild-Symbol prüfen (Schritt 1–3 wiederholen).
  5. Scout öffnen → einen Vorschlag antippen → Vollbild-Symbol prüfen (Schritt 1–3 wiederholen).
  6. Location-Detail (Anzeige-Modus, nicht Bearbeiten) öffnen → Vollbild-Symbol an der „Karte & Blickwinkel"-Sektion prüfen (Schritt 1–3 wiederholen) UND separat den Bearbeiten-Modus öffnen → bestehendes „Pins setzen"-Vollbild-Overlay (US-87) testen → muss unverändert funktionieren (Pins verschiebbar, korrekt beschriftet „Pins setzen").
  7. Chance ohne Motivkoordinaten öffnen (z.B. per Suche nach einem Astronomie-Event ohne festen Motiv-Standort) → prüfen: kein Vollbild-Symbol vorhanden, weiterhin Hinweistext „Keine Motivkoordinaten – Karte nicht verfügbar".
  8. Zwei unterschiedliche Chancen nacheinander im Vollbild öffnen (ohne Browser-Reload dazwischen) → prüfen: zweite Vollbild-Karte zeigt die Pins der zweiten Chance, nicht die der ersten.

---

### TASK-52 · Wolken-/Regen-Legende im Karten-Tab: Position von Mitte-links nach unten-links über den Zeitregler `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-07-03 |
| **Abgeschlossen** | 2026-07-04 |
| **Weg-Gate** | Stephan hat Option A (nur Position verschieben) am 2026-07-04 freigegeben. |
| **Umsetzungsnotiz** | `#map-weather-legend` `bottom` von `200px` auf `100px` gesetzt (Regler-bottom 30px + geschätzte Reglerkasten-Höhe ~55px + 12px Sicherheitsabstand ≈ 97px, auf 100px gerundet); `left: 12px` unverändert. |

**Beschreibung:** Die Wolken-/Regen-Legende im Karten-Tab soll von ihrer aktuellen Position (Mitte links) nach unten links über den Zeitschieberegler verschoben werden, damit die Kartenmitte aufgeräumter/freier wirkt. Reine visuelle Layout-Umpositionierung eines bestehenden Elements, kein neuer Nutzerwert — daher als Task statt User Story eingeordnet.

**Bezug:** Betrifft dieselbe Karten-Visualisierung wie **BUG-58** [x] und **BUG-59** [ ] (Wolken-/Niederschlag-Overlay im Karten-Tab), aber eigenständig — reine Positionsänderung der Legende, keine Overlay-/Zoom-Logik. **Wichtig:** Da dies eine visuelle Layout-Änderung an einer Karten-Visualisierung ist, MUSS in der Analyse-/Umsetzungsphase der `fotoalert-designer`-Skill (Bauhaus-Designwächter) hinzugezogen werden.

---

#### 🔬 Implementation Spec (Analyse 2026-07-04)

##### 📐 Example Mapping

**Annahmen-Protokoll:**

| Typ | Punkt |
|-----|-------|
| ✅ Klar | Betroffen ist ausschließlich die Wolken-/Regen-Legende im Karten-Tab (die kleine Box mit Farbverlauf-Balken und Prozent-/mm-Beschriftung, die erscheint sobald Wolken- oder Niederschlags-Overlay aktiv ist). Der Zeitschieberegler selbst, die Ein-/Aus-Knöpfe oben links und das Wetterdaten-Overlay auf der Karte bleiben unverändert. |
| ✅ Klar | „Über den Zeitschieberegler" bedeutet: Legende erscheint direkt oberhalb des Reglers, linksbündig mit ihm ausgerichtet — nicht daneben, nicht überlappend. |
| ⚠️ Annahme: Die Legende bleibt weiterhin nur sichtbar, wenn auch der Zeitregler sichtbar ist (also wenn Wolken- oder Niederschlags-Ansicht aktiv ist) — es ändert sich nur die Position, nicht die Sichtbarkeits-Logik. Bitte bestätigen. |
| ⚠️ Annahme: Der genaue Pixel-Abstand zwischen Legende und Zeitregler-Oberkante wird beim Implementieren am laufenden Bildschirm fein-justiert (Ziel: gleicher optischer Abstand wie zwischen anderen gestapelten Kartenelementen, ca. 10–12px), nicht als starrer Wert vorab festgelegt — da die exakte Höhe des Zeitregler-Kastens von Zeilenumbruch/Gerätebreite abhängt. Bitte bestätigen, dass eine visuelle Fein-Justierung statt eines exakten Vorab-Werts akzeptabel ist. |
| ⚠️ Annahme: Auf schmalen Bildschirmen (iPhone SE u.ä.) darf die Legende bei Bedarf schmaler werden oder in der Breite auf die Reglerbreite begrenzt werden, damit sie nicht über den rechten Bildschirmrand hinausragt. Bitte bestätigen. |

📏 **Regel 1 — Die Legende erscheint unten links direkt über dem Zeitregler, nicht mehr in der Kartenmitte.**

- 🟢 *Positiv:* Ich öffne den Karten-Tab und schalte die Wolken-Ansicht ein → die Legende mit der Prozent-Skala erscheint unten links, direkt oberhalb des Zeitschiebereglers, nicht mehr auf halber Kartenhöhe.
- 🟢 *Positiv:* Ich wechsle von Wolken- auf Niederschlags-Ansicht → die Legende bleibt an derselben Position (unten links über dem Regler), nur Inhalt/Beschriftung wechselt auf die Niederschlags-Skala (wie bisher schon).
- 🔴 *Negativ:* Ich schalte die Wetter-Ansicht wieder aus → weder Legende noch Zeitregler sind sichtbar (unverändertes Verhalten).

📏 **Regel 2 — Legende und Zeitregler überlappen sich nicht und bleiben beide vollständig lesbar/bedienbar.**

- 🟢 *Positiv:* Bei aktiver Wolken-Ansicht sehe ich sowohl die komplette Legende als auch den kompletten Zeitregler inkl. Zeit-Beschriftung darunter — keines der beiden Elemente wird vom anderen verdeckt.
- 🟢 *Positiv:* Ich ziehe den Zeitregler ganz nach rechts/links durch alle Zeitpunkte → die Legende bleibt an ihrer Position stehen und wird durch die Bedienung nicht verschoben oder verdeckt.
- ⚙️ *Edge:* Die Quellen-Angabe (Copyright-Hinweis) unten links unter dem Regler bleibt an ihrer bisherigen Position — Legende und Zeitregler rücken zusammen nach oben, ohne die Quellen-Angabe zu verdecken.

📏 **Regel 3 — Die Kartenmitte wirkt aufgeräumter, da dort kein Legenden-Kasten mehr sitzt.**

- 🟢 *Positiv:* Ich betrachte die Karte bei aktiver Wolken-/Regen-Ansicht → im mittleren Kartenbereich (dort wo bisher die Legende links auf halber Höhe saß) ist jetzt freie Kartenfläche/Wolkenbild sichtbar, ohne Beschriftungs-Kasten.

---

**📎 Code-Verifikation** (gelesen am 2026-07-04):

- `web/index.html` Z. 291–294: Legende (`#map-weather-legend`) aktuell `position: absolute; bottom: 200px; left: 12px; z-index: 1000;` — das ist die „Mitte links"-Position aus der Ticketbeschreibung.
- `web/index.html` Z. 283–286: Zeitschieberegler-Kasten (`#map-weather-slider-wrap`) sitzt bei `position: absolute; bottom: 30px; left: 64px; right: 60px; padding: 8px 16px;` — nimmt fast die volle Kartenbreite ein (nur links/rechts schmale Ränder für andere Elemente frei).
- `web/index.html` Z. 1024–1035: Im HTML liegen Zeitregler-Block und Legenden-Block direkt nacheinander im selben Karten-Container — technisch unproblematisch, keine Abhängigkeit zueinander im Code.
- `web/index.html` Z. 309–314: Die Quellen-Angabe (`#map-weather-attribution`, Pflicht-Hinweis „CC BY 4.0" laut US-112) sitzt bereits ganz unten links: `bottom: 6px; left: 8px`. Sie liegt unterhalb des Zeitreglers und bleibt von der Legenden-Verschiebung unberührt — muss beim Hochrücken der Legende nicht verschoben werden, aber die neue Legenden-Position darf diesen Hinweis nicht verdecken.
- `web/index.html` Z. 276–277: Die Ein-/Aus-Knöpfe für Wolken/Niederschlag (`#map-weather-toggle`) sitzen oben links (`top: 12px; left: 12px`) — bereits mit `left: 12px` ausgerichtet; die Legende übernimmt denselben linken Randabstand, damit alle linksseitigen Kartenelemente auf einer gemeinsamen Linie liegen (Bauhaus-Rasterkonsistenz).
- `web/index.html` Z. 4626–4632 (`_updateLegend()`): Die Sichtbarkeits-Logik der Legende (`open`-Klasse je nach `mode`) ist reines Zeigen/Verstecken über eine CSS-Klasse, unabhängig von Positionswerten — eine reine CSS-Positionsänderung berührt diese Logik nicht.

---

##### ⚠️ Pre-Mortem

💀 **Szenario 1: Legende überlappt den Zeitregler oder die Quellen-Angabe darunter**
- Auslöser: Der neue `bottom`-Wert der Legende wird zu knapp über der tatsächlichen Höhe des Zeitregler-Kastens gewählt; die reale Höhe des Regler-Kastens variiert leicht je nach Gerät/Schriftgröße (Label-Zeile kann umbrechen).
- Frühwarnung: Im Test auf schmalem Bildschirm (iPhone-Breite) wirkt die Legende geklemmt oder schneidet die Zeit-Beschriftung unter dem Regler an.
- Gegenmaßnahme: Abstand mit ausreichend Sicherheitspuffer wählen (analog zum bereits im Code dokumentierten 12px-Sicherheitspuffer-Muster bei anderen Kartenelementen, siehe Z. 3452–3453) und am laufenden Gerät/Browser visuell verifizieren, nicht nur rechnerisch.

💀 **Szenario 2: Legende ragt auf schmalen Bildschirmen über den rechten Kartenrand oder unter den Zeitregler-Randbereich hinaus**
- Auslöser: Die Legende hat `min-width: 130px` (Z. 294); bei sehr schmalen Geräten könnte das zusammen mit dem linken Rand-Offset des Zeitreglers (`left: 64px`) optisch unausgewogen wirken, auch wenn keine harte Kollision entsteht.
- Frühwarnung: Test auf kleinstem unterstützten Bildschirm (iPhone SE-Breite).
- Gegenmaßnahme: Visuelle Prüfung auf schmalem Viewport als Testschritt aufnehmen; falls nötig `min-width` reduzieren oder `max-width` ergänzen.

💀 **Szenario 3: Andere Kartenelemente (Fehler-Banner, Quellen-Angabe) werden durch die neue Legenden-Position unbeabsichtigt mitverschoben**
- Auslöser: Copy-Paste-Fehler beim Ändern der CSS-Regel trifft versehentlich eine falsche Element-ID (z.B. `#map-weather-attribution` statt `#map-weather-legend`).
- Frühwarnung: Regressionstest aller anderen Kartenelemente (Toggle-Knöpfe, Fehler-Banner, Quellen-Angabe, GPS-Button) nach der Änderung.
- Gegenmaßnahme: Nur die CSS-Regel `#map-weather-legend` anfassen, alle anderen unverändert lassen; im Testplan explizit als Regressionsschritt verankert.

💀 **Szenario 4: Legende wird durch die neue Position auf Dunkel-Modus schlechter lesbar**
- Auslöser: Reine Positionsänderung sollte keine Farb-/Kontrastwerte berühren, aber ein Verrutschen über einen helleren/dunkleren Kartenbereich könnte den gefühlten Kontrast verändern (Legende hat eigenen `--surface`-Hintergrund, daher eigentlich unabhängig vom darunterliegenden Kartenbild).
- Frühwarnung: Test im Dunkel-Modus mit aktivem Wolken-Overlay.
- Gegenmaßnahme: Keine Farbänderung vorgesehen (Legende behält `background: var(--surface)`); als Testschritt trotzdem im Dunkel-Modus gegenprüfen.

---

##### 🏗️ Architektur-Analyse

**Betroffene Dateien:**
- `web/index.html` — ausschließlich die CSS-Regel `#map-weather-legend` (Z. 292–294): `bottom`-Wert wird von `200px` auf einen Wert knapp oberhalb der Zeitregler-Oberkante geändert (`left: 12px` bleibt unverändert für Rasterkonsistenz mit dem Toggle-Block oben links). Keine HTML-Strukturänderung, keine JS-Änderung, kein Backend betroffen.

**Kein neuer Score/Event-Typ, kein Filter-Chip betroffen** (Schritt 4f entfällt). Kein Datenbezug, keine API-Änderung.

---

##### 🎨 Designer-Check (Bauhaus)

- **Positionierung:** Neue Position `bottom: [Zeitregler-Oberkante + ca. 10–12px Sicherheitsabstand]; left: 12px` — linksbündig mit dem Wolken-/Niederschlag-Toggle oben links, damit alle freistehenden Kartenelemente auf derselben vertikalen Linie liegen (Bauhaus-Rasterprinzip: Elemente an einer gemeinsamen Kante ausrichten statt frei im Raum schweben lassen).
- **Abstand:** Mindestens 10–12px Luft zwischen Legenden-Unterkante und Zeitregler-Oberkante — genug um beide Elemente optisch klar als getrennte, aber zusammengehörige Einheiten zu lesen (ähnlich dem im Code bereits verwendeten 12px-Sicherheitspuffer-Muster).
- **Ausrichtung:** Legende linksbündig, keine Zentrierung über dem Regler — der Regler selbst ist breiter (`left: 64px; right: 60px`) als die schmale Legende (`min-width: 130px`); eine zentrierte Legende würde optisch „schweben", eine linksbündige fügt sich ins bestehende Links-Raster (Toggle, Legende, Attribution alle auf einer Kante).
- **Keine Interaktion mit dem Regler:** Die Legende bleibt ein reines Anzeige-Element ohne Klick-/Touch-Funktion, keine Überlappung mit der Ziehfläche des Reglers — reine Stapelanordnung übereinander, kein Eingriff in die Bedienbarkeit des Sliders.
- **Farbe/Form/Typografie:** Unverändert (`--surface`-Hintergrund, `--border`-Rahmen, 10px-Radius, 11px-Text) — reine Positionsänderung, kein neues visuelles Element, daher keine Token-Diskussion nötig.
- **Kein neuer Radius/keine neue Farbe/kein neues Icon** — Checkliste erübrigt sich, da nur ein bestehendes, bereits Bauhaus-konformes Element verschoben wird.

---

##### 🔀 Implementierungsoptionen

**Option A — Nur den `bottom`-Wert der Legende anpassen (empfohlen)**

Was du in der App erlebst: Die Wolken-/Regen-Legende sitzt nicht mehr auf halber Kartenhöhe links, sondern direkt über dem Zeitschieberegler unten links — die Kartenmitte ist frei, Legende und Regler bilden optisch eine zusammengehörige Bedieneinheit unten links.

- Vorgehen: In der CSS-Regel `#map-weather-legend` den Wert `bottom: 200px` durch einen kleineren Wert ersetzen, der die Legende knapp oberhalb des Zeitregler-Kastens platziert; `left: 12px` bleibt bestehen. Abstand am laufenden Bildschirm fein-justieren (siehe Annahme oben).
- Betroffene Dateien: `web/index.html` (eine CSS-Regel, eine Zeile)
- Vorteile: Minimalstmöglicher Eingriff, kein Risiko für andere Elemente, sofort umsetzbar, exakt das was das Ticket verlangt
- Nachteile / Risiken: Keine nennenswerten — einziges Risiko (Überlappung) ist über Pre-Mortem Szenario 1 abgedeckt und durch visuelle Prüfung am Gerät auszuschließen
- Aufwand: sehr klein

**Option B — Legende und Zeitregler in einen gemeinsamen Container zusammenfassen**

Was du in der App erlebst: Optisch identisches Ergebnis zu Option A — Legende über dem Regler unten links.

- Vorgehen: Neuer umschließender `<div>` um Zeitregler und Legende, gemeinsame Positionierung über den Container statt über zwei einzelne `position: absolute`-Regeln.
- Betroffene Dateien: `web/index.html` (HTML-Struktur + CSS, mehrere Stellen)
- Vorteile: Bei künftigen weiteren Layout-Änderungen an dieser Ecke evtl. etwas leichter zu pflegen
- Nachteile / Risiken: Höherer Eingriff in bestehende, funktionierende Struktur ohne funktionalen Zusatznutzen für dieses Ticket; höheres Regressionsrisiko (Szenario 3) für ein Ticket, das laut Beschreibung „reine Positionsänderung, kein neuer Nutzerwert" ist
- Aufwand: mittel

✅ **Empfehlung: Option A** — das Ticket verlangt ausdrücklich nur eine Positionsänderung eines bestehenden Elements ohne neuen Nutzerwert; eine Ein-Zeilen-CSS-Änderung erfüllt das vollständig, ohne unnötiges Regressionsrisiko an einer bereits stabilen Kartenstruktur einzugehen (Grundsatz „kein Scope Creep").

---

**Testplan:**
- [ ] Automatisiert (Harness): Dieses Ticket ist reine Frontend-CSS-Positionierung (keine Datenlogik, kein Backend-Endpoint) — kein pytest-Fall in `backend/tests/` vorgesehen. Die Akzeptanzkriterien sind manuell im Browser zu prüfen.
- [ ] Manuell (unter http://localhost:8000):
  1. Karten-Tab öffnen, Wolken-Ansicht einschalten → prüfen: Legende erscheint unten links direkt über dem Zeitregler, Kartenmitte ist frei von der Legende.
  2. Auf Niederschlags-Ansicht wechseln → prüfen: Legende bleibt an derselben Position, Inhalt wechselt auf die Niederschlags-Skala.
  3. Zeitregler bei aktiver Wolken-Ansicht ganz nach links und ganz nach rechts ziehen → prüfen: Legende bleibt stehen, keine Überlappung mit Regler oder Zeit-Beschriftung darunter.
  4. Quellen-Angabe (Copyright-Hinweis) unten links weiterhin sichtbar und nicht von der Legende verdeckt.
  5. Auf schmalem Bildschirm (iPhone-Breite oder schmales Browserfenster) testen → Legende ragt nicht über den rechten Kartenrand hinaus, bleibt vollständig lesbar.
  6. Dunkel-Modus aktivieren, Wolken-Ansicht einschalten → Legende weiterhin gut lesbar (Kontrast unverändert).
  7. Wolken-/Regen-Ansicht ausschalten → weder Legende noch Zeitregler sichtbar (Regressionscheck bestehendes Verhalten).
  8. Regressionscheck übrige Kartenelemente: Ein-/Aus-Knöpfe oben links, GPS-Button, Fehler-Banner (falls durch Testdaten auslösbar) — alle unverändert an ihrer bisherigen Position.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` (CSS-Regel `#map-weather-legend`)
- [x] Designer-Check: visuell? → ja, `fotoalert-designer`-Skill aufgerufen (Bauhaus-Rasterausrichtung, Abstand, keine Interaktion mit dem Regler)
- [x] Implementierungsoptionen: A / B
- [x] Empfehlung: Option A

---

### US-87 · Locationdetails: größere Karte / Vollbild-Overlay zum Pin-Setzen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-20 |
| **Abgeschlossen** | 2026-07-03 |

**Beschreibung:** Die Karte in den Locationdetails ist zu klein für komfortables Navigieren und Setzen der Location-Pins. Sie soll deutlich größer werden — idealerweise in einem bildschirmfüllenden Overlay, das sich per Klick auf ein Symbol wieder schließen lässt.

**Bezug:** Verbessert die Edit-Karte des Location-Details (US-60). Grenzt an US-58[x] (Blickwinkel-Karte) und US-69[x] (GPS-Zentrierung). Eigenständig. **Ergänzung von Stephan (2026-07-03):** Das neue Vollbild-Overlay darf nicht denselben Fehler wie BUG-34[x] zeigen (iPhone Safari: Bearbeitungs-Overlay löste ungewollten Seiten-Zoom aus und ragte rechts aus dem Bildschirm) — das Overlay muss auf dem iPhone vollständig im sichtbaren Bereich bleiben, ohne dass die Seite beim Öffnen/Bedienen automatisch zoomt.

---

#### 🔬 Implementation Spec (Analyse 2026-07-03)

##### 📐 Example Mapping

**Annahmen-Protokoll:**

| Typ | Punkt |
|-----|-------|
| ✅ Klar | Betroffen ist die kleine Bearbeiten-Karte im Location-Detail (aus US-60), auf der Fotograf-Standort und Motiv per Ziehen gesetzt werden — nicht die readonly „Karte & Blickwinkel"-Ansicht (US-58) und nicht der Haupt-Karten-Tab. |
| ✅ Klar | Es gibt in der App bereits ein bildschirmfüllendes Karten-Overlay mit genau diesem Zweck (Pins per Antippen setzen) — das beim Anlegen einer neuen Location verwendet wird. Dieses Muster lässt sich für die Bearbeiten-Karte wiederverwenden, statt etwas komplett Neues zu bauen. |
| ⚠️ Annahme: Im Vollbild-Overlay lassen sich die Pins genauso setzen/verschieben wie bisher auf der kleinen Karte (ziehen oder antippen) — das Vollbild ist keine reine Zoom-/Vorschau-Ansicht, sondern die vollwertige Bearbeiten-Karte, nur größer. Bitte bestätigen. |
| ⚠️ Annahme: Ein Klick auf das Vollbild-Symbol öffnet das Overlay; ein Klick auf das Schließen-Symbol (bereits als „X" in der App etabliert) schließt es wieder und übernimmt automatisch die zuletzt gesetzten Pin-Positionen in die kleine Karte und die Koordinatenfelder darüber. Es gibt kein separates „Übernehmen"/„Verwerfen" — das gespeichert wird ohnehin erst beim Klick auf „Speichern" im Formular, wie bisher. Bitte bestätigen. |
| ⚠️ Annahme: Das Vollbild-Symbol sitzt oben rechts auf der kleinen Karte (wie die bestehenden Kartensymbole an anderer Stelle in der App) und ist nur beim Bearbeiten sichtbar, nicht in der normalen Locationansicht. Bitte bestätigen. |

📏 **Regel 1 — Von der kleinen Karte ins Vollbild wechseln.**
Auf der kleinen Bearbeiten-Karte im Location-Detail erscheint ein Symbol, mit dem sich die Karte bildschirmfüllend öffnen lässt.

- 🟢 *Positiv:* Ich bin im Bearbeiten-Modus einer Location, tippe auf das Vollbild-Symbol auf der kleinen Karte → die Karte öffnet sich bildschirmfüllend, beide bereits gesetzten Pins (Fotograf-Standort, Motiv) sind an derselben Stelle sichtbar wie vorher.
- 🔴 *Negativ:* Ich bin in der normalen Ansicht einer Location (nicht im Bearbeiten-Modus) → kein Vollbild-Symbol sichtbar, da dort auch keine Bearbeiten-Karte existiert.
- ⚙️ *Edge:* Die Location hat noch keinen Motiv-Pin gesetzt (nur Fotograf-Standort) → im Vollbild ist nur der eine Pin sichtbar, kein Fehler, kein Platzhalter für den fehlenden Pin.

📏 **Regel 2 — Im Vollbild komfortabel navigieren und Pins setzen.**
Im Vollbild-Overlay lässt sich die Karte wie gewohnt verschieben und zoomen, und beide Pins lassen sich exakt genauso setzen/verschieben wie vorher auf der kleinen Karte.

- 🟢 *Positiv:* Ich ziehe im Vollbild den Motiv-Pin auf ein anderes Gebäude → die Verbindungslinie zwischen Fotograf-Standort und Motiv aktualisiert sich sofort, genau wie bisher auf der kleinen Karte.
- 🟢 *Positiv:* Ich zoome im Vollbild näher heran, um den Pin präzise auf einen Gebäudeeingang zu setzen → das gelingt spürbar leichter als auf der kleinen Karte.
- 🔴 *Negativ:* Ich tippe im Vollbild daneben (auf freie Fläche, kein Pin) → nichts passiert außer der normalen Kartennavigation, kein versehentliches Pin-Setzen an der Tippstelle.

📏 **Regel 3 — Vollbild schließen und Stand übernehmen.**
Ein Klick auf das Schließen-Symbol beendet das Vollbild und die zuletzt gesetzten Pin-Positionen erscheinen sofort auf der kleinen Karte und in den Koordinatenfeldern darüber.

- 🟢 *Positiv:* Ich verschiebe im Vollbild den Fotograf-Standort-Pin, tippe auf „Schließen" → zurück im Bearbeiten-Formular zeigen die Koordinatenfelder und die kleine Karte sofort die neue Position — ohne dass ich vorher „Speichern" gedrückt habe.
- 🟢 *Positiv:* Ich öffne das Vollbild nur zum Nachschauen, verschiebe nichts, schließe es wieder → auf der kleinen Karte ändert sich nichts.
- ⚙️ *Edge:* Ich öffne das Vollbild, verschiebe einen Pin, verlasse die Bearbeiten-Ansicht aber über „Abbrechen" statt über „Speichern" → wie bisher beim normalen Bearbeiten-Formular wird nichts dauerhaft gespeichert (Verhalten bleibt unverändert, das Vollbild ändert nichts an der bestehenden Speicherlogik).

---

**📎 Code-Verifikation** (gelesen am 2026-07-03):

- `web/index.html` `LocationDetail.openEdit()` (Z. 5003–5099): rendert das Bearbeiten-Formular inkl. `<div id="edit-mini-map">` (Z. 5053, Höhe 180px).
- `LocationDetail._initEditMap()` (Z. 5103–5131): initialisiert die kleine Karte (Leaflet, Satellit-Kacheln), setzt draggbare Marker für Fotograf-Standort (`MapMarkers.observerDraggable`) und Motiv (`MapMarkers.subjectDraggable`), zeichnet die Verbindungslinie über `_drawEditLine()`.
- `LocationDetail._onEditObsInput()` / `_onEditSubjInput()` (Z. 5163–5187): synchronisieren Texteingabe → Marker-Position und umgekehrt (Drag-Ende → Textfeld). Diese Logik ist bereits vom Kartenelement entkoppelt (arbeitet mit den Feldern `edit-obs-coords`/`edit-subj-coords`), lässt sich also unverändert auf eine zweite, größere Karteninstanz anwenden.
- **Bereits vorhandenes Vollbild-Pattern gefunden:** `AddLocation` (Z. 5453 ff.) nutzt `#add-sheet`/`#add-overlay` als echtes bildschirmfüllendes Overlay (`position:fixed;inset:0`, Z. 505–512 im CSS) mit Header (Titel + Schließen-Button `i-x`, Z. 1055–1059) und Karten-Container `.add-map-container`/`#add-map` (Z. 518–519, 1060–1063). Exaktes Vorbild für ein Vollbild-Kartenoverlay in dieser App.
- Bekanntes Leaflet-Gotcha bereits im Code dokumentiert: `map.invalidateSize()` nach dem Sichtbarmachen eines zuvor verdeckten Karten-Containers ist Pflicht (Kommentar „Pre-Mortem: 0px-Container" bei Z. 4744; gleiches Muster bei `AddLocation.initMap()` Z. 5478). Das gilt auch für das neue Overlay: Leaflet berechnet beim ersten Rendern die Kartengröße aus dem DOM — ist der Container zu dem Zeitpunkt unsichtbar (`display:none`/`opacity:0`), bleibt die Karte falsch zugeschnitten, bis `invalidateSize()` manuell aufgerufen wird.
- **BUG-34 (Done, released 2026-06-28)** behob genau dieses Overlay-Muster bereits einmal: Auf dem iPhone Safari löste ein fokussiertes Eingabefeld mit `font-size < 16px` einen automatischen Seiten-Zoom aus, wodurch das Bearbeitungs-Overlay rechts aus dem Bildschirm ragte. Fix damals: `.input-field` und `.coord-pair .input-field` auf `font-size: 16px`, `#loc-detail-content` zusätzlich mit `overflow-x: hidden`. Der Fix-Scope umfasste laut Ticket auch das Add-Sheet — die Vollbild-Vorlage (`#add-sheet`/`#add-overlay`), die dieses Ticket wiederverwendet, sollte den Fix also bereits geerbt haben. Trotzdem vor der Implementierung verifizieren: Enthält das neue Vollbild-Overlay eigene, neue Eingabefelder (z. B. zur Koordinatenanzeige) oder Container ohne die `overflow-x: hidden`-Absicherung, muss der Fix dort explizit nachgezogen werden — nicht stillschweigend voraussetzen, dass „gleiches Pattern" automatisch „gleicher Fix" bedeutet.
- Icon-Set (Z. 787–841) enthält kein Vollbild-/Expand-Symbol; `i-x` für „Schließen" ist bereits Standard (u.a. `.close-btn` bei `#add-sheet` und `#loc-detail-sheet`).
- Bestehende Kartensymbol-Positionierung als Vorbild: `#map-layer-toggle`, `#map-gps-btn` (Z. 268, 318) sitzen als `position:absolute` innerhalb des Kartencontainers mit `z-index:1000` — dasselbe Muster passt für ein neues Vollbild-Symbol auf der Bearbeiten-Karte.

---

##### ⚠️ Pre-Mortem

💀 **Szenario 1: Vollbild-Karte bleibt leer/falsch zugeschnitten beim ersten Öffnen**
- Auslöser: Leaflet berechnet die Kartengröße beim `L.map(...)`-Aufruf aus dem aktuellen DOM. Wird die Karteninstanz erzeugt, während das Overlay noch unsichtbar oder mitten in der Öffnen-Animation ist, bleibt sie auf 0×0 bzw. falscher Größe hängen (bereits bekanntes Muster im Code, siehe Code-Verifikation).
- Frühwarnung: Beim lokalen Test zeigt das Vollbild eine graue Fläche oder nur einen Kartenausschnitt oben links.
- Gegenmaßnahme: Karteninitialisierung analog zu `AddLocation.initMap()` erst nach `setTimeout` (Öffnen-Animation abgeschlossen) auslösen, danach `invalidateSize()` aufrufen. Als Testschritt aufnehmen (Vollbild mehrfach öffnen/schließen).

💀 **Szenario 2: Zwei Karteninstanzen (kleine + große) geraten außer Sync**
- Auslöser: Wird im Vollbild eine komplett neue, unabhängige Leaflet-Instanz mit eigenen Markern erzeugt, muss jede Pin-Bewegung dort manuell auf die kleine Karte und die Koordinatenfelder zurückgespiegelt werden. Vergisst man eine Synchronisationsrichtung, zeigt die kleine Karte nach dem Schließen den alten Stand.
- Frühwarnung: Im Test: Pin im Vollbild verschieben, schließen → kleine Karte zeigt noch die alte Position.
- Gegenmaßnahme: Die Koordinatenfelder (`edit-obs-coords`/`edit-subj-coords`) bleiben die „Quelle der Wahrheit". Jede Pin-Bewegung (in welcher Karteninstanz auch immer) schreibt sofort in diese Felder; die jeweils andere Karte liest beim Öffnen/Re-Sync aus denselben Feldern. Als AK/Testschritt verankert (Regel 3).

💀 **Szenario 3: Vollbild-Symbol wird auch außerhalb des Bearbeiten-Modus sichtbar oder in der readonly-FOV-Karte verwechselt**
- Auslöser: Das Ticket grenzt sich bewusst von US-58 (FOV-Karte) ab; wird das Vollbild-Symbol versehentlich in beide Kartenkomponenten eingebaut oder falsch zugeordnet, entsteht Verwirrung (zwei „Vollbild"-Symbole mit unterschiedlichem Verhalten).
- Frühwarnung: Im Test: FOV-Karten-Sektion („📐 Karte & Blickwinkel") öffnen → kein neues Vollbild-Symbol vorhanden, nur die Bearbeiten-Karte hat es.
- Gegenmaßnahme: Implementierung ausschließlich in `LocationDetail.openEdit()`/`_initEditMap()`, keine Änderung an `CameraFOV`.

💀 **Szenario 4: Mobile Bedienung — Vollbild-Symbol zu klein zum Treffen oder von der Tastatur verdeckt**
- Auslöser: Auf dem Handy ist die kleine Karte nur 180px hoch; ein zu kleines Symbol oder eine Position direkt am Rand kann schwer zu treffen sein, besonders wenn parallel die Bildschirmtastatur eingeblendet ist (Koordinatenfelder direkt darüber).
- Frühwarnung: Manueller Test auf echtem Gerät/schmaler Fensterbreite: Symbol antippen — trifft es zuverlässig?
- Gegenmaßnahme: Touch-Ziel mindestens 44×44px (Bauhaus-Vorgabe), Positionierung oben rechts auf der Karte selbst (nicht am äußeren Formularrand), analog zu den bestehenden Karten-Symbolen (`#map-gps-btn` u.ä.).

💀 **Szenario 5: Zurück-Navigation/Android-Zurück-Taste schließt die ganze Bearbeiten-Ansicht statt nur das Vollbild**
- Auslöser: Wenn das Vollbild-Overlay keinen eigenen Verlaufseintrag/Zustand hat, könnte ein Zurück-Wisch (iOS Safari) oder Zurück-Tap direkt aus dem Vollbild ins Locations-Listing statt zurück zur Bearbeiten-Ansicht springen.
- Frühwarnung: Test: Vollbild öffnen, System-Zurück-Geste nutzen → landet man in der Bearbeiten-Ansicht oder ganz raus?
- Gegenmaßnahme: Vollbild nur über das eigene Schließen-Symbol schließen (wie beim bestehenden `#add-sheet` auch – dort gibt es ebenfalls keine History-Integration); Verhalten explizit in AK festhalten und testen, kein zusätzlicher Aufwand nötig da Pattern schon existiert und akzeptiert ist.

💀 **Szenario 6: Vollbild-Overlay löst ungewollten Seiten-Zoom aus und ragt aus dem Bildschirm (Regression von BUG-34)** — von Stephan explizit als Ergänzung genannt (2026-07-03)
- Auslöser: iOS Safari zoomt die ganze Seite automatisch hinein, sobald ein fokussiertes Eingabefeld eine `font-size < 16px` hat. Baut das neue Vollbild-Overlay eigene Eingabefelder oder Container ein, die den BUG-34-Fix nicht geerbt haben (z. B. weil sie neu geschrieben statt kopiert werden, oder weil ein neuer Container ohne `overflow-x: hidden` entsteht), tritt exakt derselbe Fehler wie bei BUG-34 wieder auf: Das Overlay ragt rechts aus dem sichtbaren Bereich.
- Frühwarnung: Test auf echtem iPhone (Safari) — nicht nur Desktop-Simulator/Chrome-DevTools, da sich der Auto-Zoom dort anders oder gar nicht verhält: Vollbild öffnen, in ein eventuell vorhandenes Eingabefeld tippen → zoomt die Seite? Ragt das Overlay an einer Seite aus dem Bildschirm?
- Gegenmaßnahme: Alle neuen Eingabefelder im Overlay von Anfang an mit `font-size: 16px` anlegen (nicht die alten 14px/12px-Werte aus BUG-34 wiederholen); Overlay-Container erbt `overflow-x: hidden` vom `#add-sheet`/`#add-overlay`-Vorbild oder bekommt es explizit gesetzt, falls es strukturell abweicht. Als eigenständiger AK verankert (AK-9) und als Testschritt auf echtem Gerät aufgenommen — nicht nur als Pre-Mortem-Notiz.

---

##### 🏗️ Architektur-Analyse

**Betroffene Dateien:**
- `web/index.html` — CSS: neue Regeln für ein Vollbild-Overlay der Bearbeiten-Karte (kann `#add-sheet`/`#add-overlay`-Stil direkt kopieren/leicht anpassen); neues Icon `i-expand` (oder ähnlich) im SVG-Sprite (Z. 787 ff.); HTML-Grundgerüst für das neue Overlay (ähnlich Z. 1052–1064); JS: `LocationDetail` um Öffnen-/Schließen-Funktionen und eine zweite Karteninitialisierung erweitern, `edit-mini-map`-Bereich um das Vollbild-Symbol ergänzen (Z. 5053, 5103–5131)
- Keine Backend-Änderung nötig — reine Frontend-/UI-Änderung, Speicherlogik (`saveEdit`) bleibt unverändert.

**Kein neuer Score/Event-Typ, kein Filter-Chip betroffen** (Schritt 4f entfällt).

---

##### 🔀 Implementierungsoptionen

**Option A — Bestehendes Vollbild-Overlay-Pattern wiederverwenden (empfohlen)**

Was du in der App erlebst: Auf der kleinen Bearbeiten-Karte erscheint oben rechts ein kleines Vollbild-Symbol. Tippst du drauf, füllt die Karte den ganzen Bildschirm aus — du kannst bequem zoomen, verschieben und beide Pins präzise setzen, genau wie vorher, nur mit viel mehr Platz. Ein Tipp auf das Schließen-Symbol (X, oben rechts, wie du es aus anderen Vollbild-Ansichten der App schon kennst) bringt dich zurück zum Formular — die neuen Pin-Positionen sind sofort übernommen.

- Vorgehen: Die vorhandene Vollbild-Overlay-Struktur (aktuell für „Neue Location" genutzt) als Vorlage für ein zweites, gleichartiges Overlay verwenden. Die Bearbeiten-Karte bekommt eine zweite, größere Karteninstanz in diesem Overlay, die beim Öffnen die aktuellen Pin-Positionen aus den Koordinatenfeldern übernimmt und bei jeder Änderung sofort in dieselben Felder zurückschreibt (keine getrennte Datenhaltung). Die kleine Karte liest beim Schließen des Vollbilds denselben Stand erneut ein.
- Betroffene Dateien: `web/index.html` (CSS, HTML-Grundgerüst, `LocationDetail`-Erweiterung)
- Vorteile: Nutzt ein bewährtes, bereits getestetes Vollbild-Muster (kein neues Verhalten, das erst erlernt werden muss); Aufwand überschaubar, da Drag-/Sync-Logik der kleinen Karte fast unverändert übernommen werden kann; visuell konsistent mit „Neue Location"
- Nachteile / Risiken: Zwei Karteninstanzen müssen synchron gehalten werden (Pre-Mortem Szenario 2) — sauber lösbar über die Koordinatenfelder als gemeinsame Quelle
- Aufwand: mittel

**Option B — Nur die kleine Karte vergrößern (kein Vollbild)**

Was du in der App erlebst: Die Bearbeiten-Karte ist im Formular selbst deutlich größer als bisher (z.B. 350–400px statt 180px), aber es gibt kein eigenes Vollbild — du scrollst weiterhin im normalen Formular.

- Vorgehen: `#edit-mini-map`-Höhe erhöhen, sonst keine strukturelle Änderung.
- Betroffene Dateien: `web/index.html` (CSS-Wert)
- Vorteile: Minimaler Aufwand, kein Sync-Risiko zwischen zwei Karten
- Nachteile / Risiken: Erfüllt die Ticket-Anforderung nur teilweise („idealerweise ein bildschirmfüllendes Overlay" wird explizit im Ticket genannt); auf kleinen Handybildschirmen bleibt die Karte trotzdem eingeschränkt, da sie sich das Formular mit vielen anderen Feldern teilt
- Aufwand: sehr klein

**Option C — Vollbild-Overlay ohne Pin-Bearbeitung (nur Ansicht/Navigation)**

Was du in der App erlebst: Das Vollbild-Symbol öffnet eine große Kartenansicht nur zum Anschauen/Navigieren (Zoomen, Verschieben) — die Pins lassen sich dort aber nicht verschieben, das geht weiterhin nur auf der kleinen Karte.

- Vorgehen: Reines Anzeige-Overlay ohne draggbare Marker.
- Betroffene Dateien: `web/index.html`
- Vorteile: Geringeres Sync-Risiko, da keine Rückschreibe-Logik nötig
- Nachteile / Risiken: Ticket nennt explizit „komfortables Navigieren **und Setzen** der Location-Pins" als Ziel — diese Option deckt den wichtigeren Teil (Pin-Setzen) nicht ab, wäre nur Teilerfüllung
- Aufwand: klein

✅ **Empfehlung: Option A** — deckt die Ticket-Anforderung vollständig ab (Navigieren **und** Pin-Setzen im Vollbild), nutzt ein bereits vorhandenes, bewährtes UI-Pattern (kein neuer Stil, kein neues Verhalten zu erlernen) und hält den Mehraufwand dadurch überschaubar. Das einzige nennenswerte Risiko (Sync zwischen zwei Karten) lässt sich sauber über die bestehenden Koordinatenfelder als gemeinsame Datenquelle lösen — dieses Muster existiert im Code bereits für die kleine Karte.

---

**Scope:**
- Eingeschlossen: Vollbild-Symbol auf der Bearbeiten-Karte im Location-Detail; bildschirmfüllendes Karten-Overlay mit denselben Pin-Setz-/Verschiebe-Möglichkeiten wie die kleine Karte; Schließen-Symbol zum Zurückkehren; automatische Übernahme der Pin-Positionen in die kleine Karte und die Koordinatenfelder
- Ausgeschlossen: Änderungen an der readonly „Karte & Blickwinkel"-Ansicht (US-58); Änderungen am Haupt-Karten-Tab; Änderungen an der Speicherlogik (`saveEdit` bleibt unverändert — Speichern passiert weiterhin explizit über den „Speichern"-Button); Vollbild-Funktion für die „Neue Location"-Karte (hat bereits ihr eigenes Vollbild-Overlay, unverändert)

**Akzeptanzkriterien:**
- [x] AK-1: Wenn ich eine Location bearbeite, sehe ich auf der kleinen Karte ein Symbol, mit dem sich die Karte bildschirmfüllend öffnen lässt.
- [x] AK-2: Beim Öffnen des Vollbilds sehe ich die zuvor gesetzten Pins (Fotograf-Standort, Motiv) an derselben Position wie auf der kleinen Karte — nicht zurückgesetzt auf einen Standardausschnitt.
- [x] AK-3: Im Vollbild kann ich die Karte flüssig verschieben und zoomen.
- [x] AK-4: Im Vollbild kann ich beide Pins genauso ziehen/setzen wie bisher auf der kleinen Karte; die Verbindungslinie zwischen Fotograf-Standort und Motiv aktualisiert sich dabei sofort.
- [x] AK-5: Wenn ich das Vollbild über das Schließen-Symbol verlasse, zeigen die kleine Karte und die Koordinaten-Textfelder sofort die im Vollbild vorgenommenen Änderungen — ohne dass ich vorher „Speichern" gedrückt habe.
- [x] AK-6: Die endgültige Speicherung passiert weiterhin erst beim Klick auf „Speichern" im Formular — das Vollbild-Öffnen/Schließen allein verändert die gespeicherten Location-Daten nicht.
- [x] AK-7: Das Vollbild-Symbol ist gut genug zum zuverlässigen Antippen (mindestens fingergroß) und wird von der Bildschirmtastatur nicht verdeckt.
- [x] AK-8: Die readonly „Karte & Blickwinkel"-Ansicht (US-58) bleibt unverändert — dort erscheint kein neues Vollbild-Symbol.
- [x] AK-9: Auf dem iPhone (Safari) löst das Öffnen und Bedienen des Vollbilds keinen ungewollten Seiten-Zoom aus; das Overlay bleibt an allen Seiten vollständig innerhalb des sichtbaren Bereichs (keine Wiederholung von BUG-34).
- [x] Edge Case: Die Location hat noch keinen Motiv-Pin gesetzt → im Vollbild ist nur der Fotograf-Standort-Pin sichtbar, kein Fehler und kein Platzhalter.
- [x] Edge Case: Ich öffne das Vollbild mehrfach hintereinander (öffnen, schließen, erneut öffnen) → die Karte zeigt jedes Mal korrekt zugeschnitten den aktuellen Stand, keine graue Fläche oder falsches Kartenformat.
- [x] Edge Case: Ich öffne das Vollbild, verschiebe einen Pin, verlasse die Bearbeiten-Ansicht danach über „Abbrechen" statt „Speichern" → die Änderung wird nicht dauerhaft gespeichert (Verhalten wie beim bisherigen Formular).

**Pre-Mortem (Zusammenfassung):**
- 💀 Vollbild-Karte bleibt leer/falsch zugeschnitten beim ersten Öffnen → Gegenmaßnahme: Karteninitialisierung nach Öffnen-Animation + `invalidateSize()` (wie beim bestehenden Add-Location-Vollbild)
- 💀 Kleine und große Karte geraten außer Sync → Gegenmaßnahme: Koordinatenfelder als gemeinsame Datenquelle, beide Karten lesen/schreiben nur darüber
- 💀 Vollbild-Symbol taucht versehentlich auch in der readonly-FOV-Karte auf → Gegenmaßnahme: Änderung strikt auf die Bearbeiten-Karte begrenzt, als AK-8 verankert
- 💀 Symbol auf dem Handy zu klein oder von der Tastatur verdeckt → Gegenmaßnahme: Touch-Ziel ≥44px, Position oben rechts auf der Karte, als AK-7 verankert
- 💀 Zurück-Navigation verlässt versehentlich die ganze Bearbeiten-Ansicht → Gegenmaßnahme: Schließen ausschließlich über eigenes Symbol (Pattern bereits akzeptiert bei Add-Location)
- 💀 Overlay löst ungewollten Seiten-Zoom aus und ragt aus dem Bildschirm, wie früher bei BUG-34 → Gegenmaßnahme: neue Eingabefelder von Anfang an mit `font-size: 16px`, `overflow-x: hidden` am Overlay-Container sicherstellen, auf echtem iPhone testen (als AK-9 verankert)

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` (`LocationDetail.openEdit()` Z. 5003–5099, `_initEditMap()` Z. 5103–5131, `AddLocation`-Vollbild-Pattern Z. 505–529, 1052–1064, 5453 ff.)
- [x] Designer-Check: visuell? → ja, `fotoalert-designer` aufgerufen (neues Vollbild-Symbol im Bauhaus-Linienstil nötig, Schließen-Symbol `i-x` bereits Standard, Positionierung wie bestehende Karten-Toggles)
- [x] Implementierungsoption freigegeben: Option A (bestehendes Vollbild-Pattern wiederverwenden) — Stephan, 2026-07-03
- [x] Empfehlung: Option A

**Testplan:**
- [ ] Automatisiert (Harness): Diese Änderung ist reine Frontend-UI-Interaktion ohne Backend-Beteiligung — kein pytest-Fall sinnvoll ableitbar. Absicherung erfolgt vollständig über die manuellen Testschritte unten.
- [ ] Manuell (unter http://localhost:8000):
  1. Location-Detail einer bestehenden Location öffnen → Bearbeiten (Stift-Symbol) antippen.
  2. Auf der kleinen Karte das neue Vollbild-Symbol suchen und antippen → Karte öffnet sich bildschirmfüllend, beide Pins an der erwarteten Position (AK-1, AK-2).
  3. Im Vollbild zoomen und verschieben → Kartennavigation reagiert flüssig (AK-3).
  4. Im Vollbild den Motiv-Pin an eine andere Stelle ziehen → Verbindungslinie aktualisiert sich sofort (AK-4).
  5. Schließen-Symbol antippen → zurück im Formular: kleine Karte und Koordinatenfelder zeigen die neue Position, ohne „Speichern" gedrückt zu haben (AK-5).
  6. „Abbrechen" statt „Speichern" antippen → Location erneut öffnen → alte Position ist noch aktiv, nichts wurde übernommen (AK-6, Edge Case 3).
  7. Vollbild mehrfach hintereinander öffnen/schließen → jedes Mal korrekt zugeschnittene Karte, keine graue Fläche (Edge Case 2).
  8. Location ohne Motiv-Pin bearbeiten → Vollbild öffnen → nur ein Pin sichtbar, kein Fehler (Edge Case 1).
  9. „Karte & Blickwinkel"-Sektion (US-58) einer Location öffnen → dort erscheint kein neues Vollbild-Symbol (AK-8).
  10. Regression: bestehendes „Neue Location"-Vollbild (Plus-Tab) weiterhin unverändert nutzbar; normales Bearbeiten-Formular (Name, Kategorie, Beschreibung, Schwierigkeit etc.) weiterhin unverändert speicherbar.
  11. **Auf einem echten iPhone (Safari, nicht nur Desktop-Simulator):** Vollbild öffnen, falls vorhanden in ein Eingabefeld im Overlay tippen → die Seite zoomt nicht automatisch, das Overlay bleibt vollständig im sichtbaren Bereich, kein Ausschnitt ragt rechts oder unten aus dem Bildschirm (AK-9, Regressionstest gegen BUG-34).

**Implementierung (2026-07-03, Option A umgesetzt):**
- `web/index.html` Icon-Sprite: neues Symbol `i-expand` ergänzt (vier Ecken-Winkel nach außen, Bauhaus-Linienstil, analog `i-target`/`i-compass`).
- `web/index.html` CSS: neuer Block „US-87: Vollbild-Overlay für die Bearbeiten-Karte" — `#edit-map-expand-btn` (Touch-Ziel 44×44px, oben rechts auf der Mini-Map), `#edit-map-fs-sheet`/`#edit-map-fs-overlay` (`position:fixed;inset:0`, `.open`-Klasse, `overflow-x:hidden` explizit am Sheet), `.edit-map-fs-header`/`.edit-map-fs-container`/`#edit-map-fs` — 1:1 nach dem `#add-sheet`/`#add-overlay`-Vorbild. Responsive-Regel (Desktop-Zentrierung) um `#edit-map-fs-sheet` ergänzt.
- `web/index.html` HTML: neuer Overlay-Block nach dem Add-Location-Sheet eingefügt (Header mit Titel „Pins setzen", Schließen-Button `i-x`, Kartencontainer `#edit-map-fs`). Auf der kleinen Bearbeiten-Karte (`openEdit()`) wurde der `edit-mini-map`-Container in einen `position:relative`-Wrapper mit dem neuen Vollbild-Button verpackt.
- `web/index.html` JS (`LocationDetail`): neue Funktionen `openMapFullscreen()`, `closeMapFullscreen()`, `_initEditMapFs()`, `_reloadEditMapFsFromFields()`, `_drawEditLineFs()`. Karteninitialisierung erst nach `setTimeout` (Öffnen-Animation), danach `invalidateSize()` — analog `AddLocation.open()`/`initMap()`. Koordinatenfelder (`edit-obs-coords`/`edit-subj-coords`) bleiben alleinige Quelle der Wahrheit: `dragend` auf der Vollbild-Karte schreibt sofort in die Felder und spiegelt die Position auf die kleine Karte; `closeMapFullscreen()` liest zusätzlich per `_onEditObsInput()`/`_onEditSubjInput()` aus denselben Feldern zurück. `openEdit()` verwirft eine evtl. vorhandene alte Vollbild-Karteninstanz (der Container `#edit-map-fs` ist statisch, nicht Teil des bei jedem Edit neu gerenderten `innerHTML`), `close()` schließt das Vollbild sicherheitshalber mit. Keine Änderung an `saveEdit()`, `CameraFOV`/US-58 oder `AddLocation`.
- Kein neues Eingabefeld im Vollbild-Overlay (nur Kartencontainer) → AK-9/BUG-34-Risiko strukturell vermieden; zusätzlich `overflow-x: hidden` explizit am `#edit-map-fs-sheet` gesetzt.
- `node --check` auf den extrahierten Inline-`<script>`-Blöcken lief fehlerfrei.
- Noch offen/nicht in dieser Phase geprüft: manueller Test (lokal + echtes iPhone Safari für AK-9) — folgt in der Testphase.

---

### US-79 · Mondauf- und -untergang in Event- und Locationdetails `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **Abgeschlossen** | 2026-06-28 |

**Beschreibung:** Ergänzend zu Sonnenaufgang und -untergang sollen auch Mondaufgang und -untergang (Uhrzeit, Azimut) in der Astronomie-Kategorie der Event- und Locationdetails angezeigt werden.

---

#### 📐 Example Mapping

**Annahmen-Protokoll:**

| Typ | Punkt |
|-----|-------|
| ✅ klar | `moonrise` und `moonset` werden bereits von `calculate_moon_info()` in `astronomy.py` berechnet (Z. 378–385), sind aber **nicht** in `_serialize()` im `precompute.py`-Output enthalten |
| ✅ klar | Azimut zum Zeitpunkt des Mondaufgangs/-untergangs lässt sich mit der bereits vorhandenen `get_body_position(lat, lon, "moon", moonrise_time)` berechnen |
| ⚠️ Annahme | Mondauf-/-untergang werden **nur im Event-Detail und Location-Detail** angezeigt, nicht als eigener Filter-Chip — bitte bestätigen |
| ⚠️ Annahme | Wenn kein Mondaufgang/-untergang an diesem Tag stattfindet (Polarnacht-Szenario für Mond: tritt bei FotoAlert-Breitengraden selten auf, aber möglich), wird die Zeile einfach ausgeblendet — bitte bestätigen |
| ✅ klar | Es gibt kein eigenes Mondaufgang-/Monduntergangs-Icon — `i-moon` wird wiederverwendet (wie bei Mondphase) |

**📏 Regeln:**

📏 **Rule 1 — Mondaufgang mit Uhrzeit und Azimut im Event-Detail**
Wenn ein Event geöffnet wird, zeigt die Astronomie-Sektion — sofern an diesem Tag ein Mondaufgang stattfindet — die Uhrzeit (Berliner Zeit) und den Aufgangsazimut in Grad an.

🟢 Example 1a (Mondaufgang vorhanden):
- **Given** der Nutzer öffnet ein Goldene-Stunde-Event am 15. Juli 2026
- **When** die Astronomie-Sektion erscheint
- **Then** sieht er z.B. „Mondaufgang · 21:34 · 78°" als neue Zeile, direkt unter Sonnenuntergang

🟢 Example 1b (kein Mondaufgang an diesem Tag):
- **Given** an dem Tag gibt es keinen Mondaufgang (selten, aber möglich)
- **When** die Astronomie-Sektion erscheint
- **Then** fehlt die Mondaufgang-Zeile kommentarlos (kein „–" oder „unbekannt")

📏 **Rule 2 — Monduntergang mit Uhrzeit und Azimut im Event-Detail**
Analog zu Mondaufgang: Monduntergangszeit und -azimut werden in derselben Sektion angezeigt, falls vorhanden.

🟢 Example 2a (Monduntergang vorhanden):
- **Given** das Event-Detail ist offen
- **When** Monduntergang ist für diesen Tag berechenbar
- **Then** erscheint „Monduntergang · 04:12 · 282°" als eigene Zeile

📏 **Rule 3 — Dieselben Daten im Location-Detail**
Location-Details zeigen Mondauf-/-untergang für den aktuellen Tag (Heute) in der Astronomie-Sektion an.

🟢 Example 3a:
- **Given** der Nutzer öffnet das Location-Detail
- **When** er die Astronomie-Infos sieht (aktuell nur Mondphase sichtbar, da Location-Details keine event-spezifischen Felder haben)
- **Then** — **Achtung:** Location-Details haben keinen Event-Kontext und damit keine `sunrise_utc`/`sunset_utc`-Felder. Location-Details zeigen derzeit keine Astronomie-Zeitangaben an. → Dies muss als Scope-Entscheidung geklärt werden (❓ Question 1).

❓ **Question 1 — Location-Detail: heute oder event-spezifisch?**
Das Location-Detail zeigt keinen Event-Kontext. Soll für das Location-Detail:
- (a) der **heutige Tag** als Referenz genommen werden (live berechnet via API-Call oder JS-Bibliothek)?
- (b) nur im **Event-Detail** (das einen konkreten Datum-Kontext hat) angezeigt werden?

⚠️ Annahme für die Spec: Scope = **primär Event-Detail**; Location-Detail als nachgelagerter Scope wenn (a) bestätigt.

📏 **Rule 4 — Recompute erforderlich**
Die neuen Felder (`moonrise_utc`, `moonset_utc`, `moonrise_azimuth`, `moonset_azimuth`) werden im Backend berechnet und im Cache gespeichert. Nach der Implementierung ist ein vollständiger Recompute nötig, damit alle gecachten Events die neuen Felder haben.

---

#### ✅ Akzeptanzkriterien

- [x] **AK-1:** Wenn der Nutzer ein beliebiges Event öffnet und an diesem Tag ein Mondaufgang stattfindet, sieht er in der Astronomie-Sektion des Event-Details eine neue Zeile „Mondaufgang" mit Uhrzeit (Berliner Zeit) und Azimut in Grad (z.B. „🌙 21:34 · 78°").
- [x] **AK-2:** Wenn der Nutzer ein beliebiges Event öffnet und an diesem Tag ein Monduntergang stattfindet, sieht er in der Astronomie-Sektion eine neue Zeile „Monduntergang" mit Uhrzeit (Berliner Zeit) und Azimut in Grad.
- [x] **AK-3:** Wenn an dem Tag kein Mondaufgang oder kein Monduntergang stattfindet (Felder im Event-Objekt sind `null`), fehlt die entsprechende Zeile kommentarlos — keine Anzeige von „–" oder „unbekannt".
- [x] **AK-4:** Die Azimut-Werte für Mondaufgang/-untergang werden auf eine Nachkommastelle gerundet angezeigt (z.B. „78.3°"), konsistent mit anderen Azimut-Angaben in der App.
- [x] **AK-5:** Der API-Endpoint `/opportunities` liefert vier neue Felder pro Event: `moonrise_utc` (ISO-String oder null), `moonset_utc` (ISO-String oder null), `moonrise_azimuth` (Float oder null), `moonset_azimuth` (Float oder null).
- [x] **AK-6:** Der Kalender-Endpoint `/calendar` liefert dieselben vier neuen Felder (da er dieselbe `_serialize()`-Funktion verwendet).
- [x] **AK-7 (Edge Case):** Wenn ein Event aus dem Cache kommt, der **vor** dem Recompute erstellt wurde (Felder fehlen also), zeigt das Frontend weder Fehler noch leere Zeilen an — der `null`-Check greift sauber.
- [x] **AK-8 (Regression):** Alle bestehenden Astronomie-Felder (Sonnenaufgang, Sonnenuntergang, Mondphase, Mondbeleuchtung, Goldene/Blaue Stunde) sind nach der Änderung noch identisch vorhanden und korrekt angezeigt.
- [x] **AK-NEU-A:** Mondaufgang und Monduntergang erscheinen als eigenständige Event-Karten im Feed — mit Titel, Uhrzeit und Score, direkt neben Goldene Stunde und Blaue Stunde.
- [x] **AK-NEU-B:** Die Filter-Chips „Mondaufgang" und „Monduntergang" im Filter-Sheet funktionieren und filtern den Feed korrekt auf diese Event-Typen.
- [x] **AK-NEU-C:** Im Event-Detail (Astronomie-Sektion) erscheinen Mondaufgang und Monduntergang mit Uhrzeit (Berliner Zeit) und Azimut in Grad — wenn sie an diesem Tag stattfinden.
- [x] **AK-NEU-D:** Wenn ein Mondaufgang- oder Monduntergang-Filter aktiv ist, werden auf der Karte nur Locations mit diesen Events angezeigt (Feed-basierter Filter greift).
- [x] **AK-NEU-E:** Mondaufgang- und Monduntergang-Events erscheinen im Location-Detail unter „Nächste Chancen" mit korrektem Mond-Icon (nicht i-star Fallback).

---

#### 💀 Pre-Mortem

📎 **Code-Verifikation** (durchgeführt 2026-06-28):
- `calculate_moon_info()` in `backend/calculations/astronomy.py` Z. 358–415: berechnet bereits `moonrise` und `moonset` als `Optional[datetime]`. Azimut zum Aufgangszeitpunkt muss **neu** via `get_body_position(lat, lon, "moon", moonrise)` abgerufen werden — das ist eine vorhandene Funktion.
- `_serialize()` in `backend/precompute.py` Z. 378–469: enthält `moonrise`/`moonset` **nicht**. Die neuen Felder müssen dort ergänzt werden.
- `MoonInfo`-Dataclass hat `azimuth_at_golden_hour` aber **keinen** `moonrise_azimuth`/`moonset_azimuth` — diese müssen entweder in die Dataclass oder direkt in `_serialize()` berechnet werden.
- Frontend (Z. 3313–3320): die `astro`-Variable im Event-Detail nutzt `o.moonrise_utc` noch nicht — genau dort werden die neuen Zeilen eingefügt.
- Bestätigt: `i-moon` Icon vorhanden (Z. 753); `formatTime()` akzeptiert ISO-Strings und gibt Berliner Zeit zurück (Z. 1281).

💀 **Szenario 1: Alter Cache — neue Felder fehlen → JS-Fehler**
- Auslöser: Frontend erwartet `o.moonrise_utc`, aber bestehende Cache-Events haben das Feld noch nicht
- Frühwarnung: Fehler-Konsole im Browser zeigt `undefined` bei Feldauswertung
- Gegenmaßnahme: Im Frontend **immer** mit `o.moonrise_utc ?` konditionalen Guard arbeiten (wie bei sunrise_utc bereits Standard) → AK-7

💀 **Szenario 2: Azimut-Berechnung zum Zeitpunkt moonrise schlägt fehl**
- Auslöser: `moonrise` ist None (kein Mondaufgang an diesem Tag) → `get_body_position()` wird mit None aufgerufen
- Frühwarnung: Backend-Exception in Precompute-Log
- Gegenmaßnahme: In `_serialize()` explizit `if o.astronomy_report.moon.moonrise` prüfen, bevor Azimut berechnet wird → in Testfall abdecken

💀 **Szenario 3: Recompute nicht durchgeführt → Felder im Cache fehlen dauerhaft**
- Auslöser: Nach Release wird kein `POST /refresh-feed` ausgeführt
- Frühwarnung: `/opportunities`-Response hat `moonrise_utc: null` für alle Events
- Gegenmaßnahme: Recompute als expliziter Release-Schritt im Release-Gate vermerken (Bestandteil des Testplans)

💀 **Szenario 4: Python 3.9 Kompatibilität verletzt**
- Auslöser: In `_serialize()` oder `MoonInfo` wird `str | None`-Syntax (Python 3.10+) verwendet
- Frühwarnung: Prod-Server-Crash beim Start
- Gegenmaßnahme: Alle neuen Typen als `Optional[str]` / `Optional[float]` aus `typing` schreiben

💀 **Szenario 5: Azimut-Berechnung nutzt Window-Engine-Cache für falschen Zeitpunkt**
- Auslöser: `get_body_position()` wird mit dem `moonrise`-Zeitpunkt aufgerufen. Die Window-Engine interpoliert nur innerhalb ihres vorberechneten Tages-Fensters. `moonrise` liegt am Beginn des Tages oder am Ende — Edge-Case beim Rand des Fensters.
- Frühwarnung: Azimut-Wert erscheint als `null`, obwohl Mondaufgang vorhanden
- Gegenmaßnahme: Fallback auf direkten Skyfield-Call wenn `get_body_position()` None zurückgibt → testen mit Randzeiten

---

#### 🏗 Architektur-Analyse

**Betroffene Dateien:**

| Datei | Änderung |
|-------|----------|
| `backend/calculations/opportunity.py` | Block 5b neu: Mondaufgang/-untergang als eigenständige PhotoOpportunity-Events (EventType.MOON_RISE / MOON_SET), analog zu Goldener Stunde |
| `backend/precompute.py` | `_serialize()`: 4 neue Felder (`moonrise_utc`, `moonset_utc`, `moonrise_azimuth`, `moonset_azimuth`), Azimut via `get_body_position()` zur Mondaufgangszeit; Import von `get_body_position` ergänzt |
| `web/index.html` | `ICONS`-Map: `Monduntergang` → `i-moon` ergänzt; `Detail.open()` astro-Block: 2 neue info-rows für Mondaufgang/-untergang mit Uhrzeit + Azimut |
| `backend/tests/test_us79_moon_rise_set.py` | 9 pytest-Tests: Quellcode-Verifikation für Felder, Event-Erzeugung, Guard und Regression |

**Entry-Point-Datenquellencheck:**

| Entry-Point | Endpoint | Datenquelle | moonrise_utc vorhanden? |
|-------------|----------|-------------|------------------------|
| Feed (Event-Detail) | `/opportunities` | `_serialize()` aus precompute-Cache | ❌ noch nicht |
| Kalender (Event-Detail) | `/calendar` | `_serialize()` (identisch) | ❌ noch nicht |
| Location-Detail | — | kein eigener Astronomy-Endpoint | — (Scope-Frage) |

**Wichtig:** Kalender und Feed nutzen **dieselbe** `_serialize()`-Funktion → eine Änderung deckt beide ab. Kein divergierendes Daten-Problem.

---

#### 🛠 Implementierungsoptionen

**Was der Nutzer erlebt:**

**Option A** — Der Nutzer sieht beim Öffnen eines Events die Mondaufgang- und Monduntergangszeit direkt in der Astronomie-Sektion, mit Uhrzeit und Richtungsgrad. Der Azimut wird beim täglichen Recompute-Lauf einmalig berechnet und gecacht — keine Laufzeit-Berechnung.

**Option B** — Identisches Erscheinungsbild für den Nutzer, aber der Azimut zum Mondaufgangszeitpunkt wird als separate `get_body_position()`-Erweiterung in der `MoonInfo`-Dataclass verankert, statt direkt in `_serialize()`. Sauberer für künftige Erweiterungen (z.B. wenn MoonInfo anderswo gebraucht wird).

---

### Option A — Direkt in `_serialize()` (minimal invasiv)

- **Vorgehen:** In `_serialize()` werden `moonrise_utc` und `moonset_utc` direkt aus `o.astronomy_report.moon.moonrise/.moonset` serialisiert; `moonrise_azimuth`/`moonset_azimuth` werden ad-hoc via `get_body_position()` berechnet (nur wenn Zeitpunkt nicht None ist). Keine Änderung an `MoonInfo`.
- **Betroffene Dateien:** `backend/precompute.py` (4 neue Felder), `web/index.html` (2 neue Zeilen)
- **Vorteile:** Minimale Änderungsfläche, kein Refactoring von Datenklassen, schnell
- **Nachteile:** Azimut-Logik verteilt sich zwischen `astronomy.py` (Berechnung) und `precompute.py` (Ad-hoc-Nutzung); weniger kohärent
- **Aufwand:** klein

### Option B — MoonInfo-Dataclass erweitern (strukturell sauber)

- **Vorgehen:** `MoonInfo` bekommt zwei neue Felder (`moonrise_azimuth: Optional[float]`, `moonset_azimuth: Optional[float]`). `calculate_moon_info()` berechnet sie beim Aufruf automatisch mit. `_serialize()` liest sie dann nur noch aus.
- **Betroffene Dateien:** `backend/calculations/astronomy.py` (Dataclass + Berechnung), `backend/precompute.py` (nur Auslesen), `web/index.html` (2 neue Zeilen)
- **Vorteile:** Azimut-Berechnung ist kohärent in `calculate_moon_info()` gebündelt; bei künftigen Nutzern von `MoonInfo` (z.B. neuer Endpoint) automatisch mitgeliefert
- **Nachteile:** Etwas mehr Änderungsfläche in `astronomy.py`; marginaler Mehraufwand
- **Aufwand:** klein–mittel

✅ **Empfehlung: Option B** — Die `MoonInfo`-Dataclass ist der semantisch richtige Ort für Mondauf-/-untergangs-Azimute. Alle `MoonInfo`-Aufrufer profitieren automatisch. Mehraufwand ist minimal (2–3 Zeilen in `astronomy.py`). Option A wäre technische Schuld: der Azimut gehört zur Mondberechnung, nicht zur Serialisierung.

---

#### 🧪 Testplan

**Automatisiert (pytest) — `backend/tests/test_us79_moon_rise_set.py`:**
- [ ] `test_moonrise_fields_in_serialize()` — `_serialize()` eines Mock-PhotoOpportunity mit `astronomy_report.moon.moonrise = datetime(...)` liefert `moonrise_utc` als ISO-String und `moonrise_azimuth` als float ≠ None
- [ ] `test_moonset_fields_in_serialize()` — analog für Monduntergang
- [ ] `test_no_moonrise_returns_null()` — `astronomy_report.moon.moonrise = None` → `moonrise_utc: null`, `moonrise_azimuth: null`
- [ ] `test_moonrise_azimuth_range()` — `moonrise_azimuth` liegt zwischen 0° und 360°
- [ ] `test_mooninfo_dataclass_has_azimuth_fields()` (bei Option B) — `MoonInfo`-Instanz hat Felder `moonrise_azimuth` und `moonset_azimuth`

**Manuell (Browser unter `http://localhost:8000`):**
1. App öffnen → Feed-Tab → beliebiges Event tippen → Astronomie-Sektion öffnen
   → **Erwartetes Ergebnis:** neue Zeile „Mondaufgang" mit Uhrzeit + Azimut sichtbar (oder fehlt wenn kein Mondaufgang heute)
2. Kalender-Tab → Monat wählen → Event tippen → Astronomie-Sektion
   → **Erwartetes Ergebnis:** identische Mondfelder wie im Feed-Event-Detail
3. Event mit bekanntem Datum suchen wo kein Mondaufgang stattfindet
   → **Erwartetes Ergebnis:** keine leere Zeile, keine Fehleranzeige
4. **Regression:** Sonnenaufgang, Mondphase, Goldene Stunde — alle noch vorhanden und korrekt

**Regressions-Matrix (aus PRODUCT.md):**
- Backend-Änderung in `precompute.py` → Feed, Kalender, Discover auf korrekte Serialisierung prüfen
- `astronomy.py`-Änderung → alle astronomy-basierten Event-Typen (Mond-Alignment, Goldene Stunde, Milchstraße) in Feed auf korrekte Scores prüfen

---

#### 📋 Analyse & Planung

- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `backend/precompute.py`, `backend/calculations/astronomy.py`, `web/index.html`
- [x] Implementierungsoptionen: A (direkt in _serialize) / B (MoonInfo erweitern)
- [x] Empfehlung: **Option B** — MoonInfo-Dataclass um `moonrise_azimuth`/`moonset_azimuth` erweitern

**Scope (erweitert auf vollwertige Event-Typen laut US-79-Freigabe):**
- ✅ Eingeschlossen: Mondaufgang/-untergang als eigenständige Events in `opportunity.py` (EventType.MOON_RISE, EventType.MOON_SET)
- ✅ Eingeschlossen: `_serialize()` in `precompute.py` liefert `moonrise_utc`, `moonset_utc`, `moonrise_azimuth`, `moonset_azimuth`
- ✅ Eingeschlossen: Event-Detail zeigt Mondaufgang/-untergang in der Astronomie-Sektion
- ✅ Eingeschlossen: Filter-Chips „Mondaufgang" / „Monduntergang" vorhanden (waren bereits im _ET-Array)
- ✅ Eingeschlossen: Map-Filter für Mondaufgang/-untergang greift via Feed-basierten Typ-Match
- ✅ Eingeschlossen: Location-Detail „Nächste Chancen" zeigt Mondaufgang/-untergang (via /opportunities mit location_id)
- ✅ Eingeschlossen: ICONS-Map hat `Monduntergang` → `i-moon` ergänzt (fehlte bisher)
- ❌ Ausgeschlossen: Location-Detail Astronomie-Block mit live-berechnetem Mondaufgang für Heute (kein Event-Kontext; separater Scope wenn gewünscht)

---

### US-17 · Lieblingslocations (Favorites)
> **Als Fotograf** möchte ich Locations als Favoriten markieren können, **damit ich** meinen persönlichen Kern-Spotpool schnell filtern kann.
>
> **Akzeptanzkriterien:**
> - Herz-/Stern-Icon auf jeder Location und jedem Event-Card
> - Filter-Chip „Nur Favoriten" im Feed (integriert in US-32 Filter-System)
> - Favoriten werden lokal gespeichert (localStorage / PWA)
> - Favoriten-Tab oder Section im Locations-Menü
>
> ⚠️ **Persistenz-Designhinweis (TASK-23, 2026-06-24):** Das AK „localStorage/PWA" reicht nicht — iOS löscht PWA-Storage nach 7 Tagen Inaktivität (vgl. BUG-26). Bei Implementierung Favoriten direkt serverseitig persistieren (analog US-89/US-90), nicht rein lokal.

### US-26 · Sprachumschaltung DE / EN
> **Als Fotograf** möchte ich die App zwischen Deutsch und Englisch umschalten können, **damit ich** sie auch mit internationalen Fotografie-Gästen nutzen kann.
>
> **Akzeptanzkriterien:**
> - Sprach-Toggle in den Einstellungen (DE / EN)
> - Alle Labels, Event-Typen, Beschreibungen und Fehlermeldungen übersetzt
> - Gewählte Sprache bleibt nach App-Neustart erhalten
> - Locations-Beschreibungen: Fallback auf Deutsch wenn EN fehlt

### US-21 · App-Beschreibung, Onboarding & verständliche Erklärungen für jede Funktion `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | In Test |
| **Erstellt** | ursprünglich vor 2026-07-04, erweitert 2026-07-05 |

**Weg-Gate-Entscheidung (2026-07-05):**
- Implementierungsweg: **Option C** — Onboarding + zentrales Glossar bleiben erhalten, zusätzlich bekommt jedes bedeutungstragende Element (Schwierigkeitsgrad, Event-Typ, Verifikations-Status, Filter-Chips, Kartensymbole) ein eigenes ⓘ nach dem bewährten US-55-Muster (Score-Erklärungen via ⓘ-Overlay).
- Scope: **nur Web-App** (iOS-App vorerst ausgenommen, ggf. eigenes Folge-Ticket).
- Symbol: **einheitliches ⓘ-Symbol** für alle Elementtypen (keine Symbol-Varianten je Kontext).

**Beschreibung:** Als App-Nutzer (neu oder erfahren) möchte ich jederzeit und ohne Verzögerung verstehen, was eine Funktion der App aussagt, wie sie funktioniert und wie ich sie praktisch anwende, sodass ich FotoAlert sicher und selbstständig nutzen kann — vom ersten Start an und bei jeder einzelnen Funktion, nicht nur bei den Scores.

**Herkunft / Merge-Hinweis:** Dieses Ticket ist der Merge aus dem ursprünglichen US-21 („App-Beschreibung & Onboarding") und **US-116** (Gemerged 2026-07-05, siehe dort). US-116 hat den Scope bewusst erweitert: nicht nur Scores/Schwierigkeitsgrade/Event-Typen, sondern **jede** Funktion/jedes UI-Element — plus die explizite Anforderung „ohne Verzögerung" (Erklärung direkt im Kontext sichtbar, nicht nur über ein zentrales Glossar, das erst gesucht werden muss).

**Baustein US-55 (Done, nicht duplizieren):** US-55 liefert bereits einen ⓘ-Info-Button je Score-Wert (Gesamt-, Astronomie-, Wetter-Score, inzwischen auch Wolkenstimmung) im Detail-Sheet einer Chance. Klick öffnet ein zentrales Overlay mit der Berechnungserklärung; Schließen über „×" oder Klick auf den Hintergrund (v1.2.1). Diese Spec baut auf diesem Muster auf und **erweitert es auf alle übrigen Funktionen/UI-Elemente der App** (Filter, Schwierigkeitsgrade, Event-Typen, Karten-Symbole, Verifikations-Status usw.) statt es zu ersetzen.

> **Ursprüngliche Akzeptanzkriterien (US-21, beibehalten):**
> - Onboarding-Screen beim ersten Start (3–4 Slides)
> - „?" Info-Button im Header → erklärt Score-System, Schwierigkeitsgrade, Event-Typen
> - Jeder Score-Wert (Astronomie, Wetter, Gesamt) hat eine Erklärung (bereits umgesetzt via US-55 ⓘ-Overlay)
> - Glossar: Was ist ein Alignment? Was bedeutet Quality-Score?

**Akzeptanzkriterien (final, nach Merge mit US-116):**
- [ ] Beim allerersten App-Start erscheint eine kurze Einführung (3–4 Screens), die erklärt, wofür FotoAlert grundsätzlich da ist und wie die wichtigsten Bereiche (Feed, Kalender, Karte, Locations) funktionieren.
- [ ] Ein „?"-Button im Header ist jederzeit erreichbar und öffnet eine Übersicht mit Erklärungen zu Score-System, Schwierigkeitsgraden und Event-Typen (Glossar-Charakter, zentrale Nachschlagestelle).
- [ ] Jeder Score-Wert (Astronomie, Wetter, Gesamt, Wolkenstimmung) bleibt wie in US-55 direkt per ⓘ-Button erklärbar — kein Rückbau.
- [ ] Zusätzlich zu Scores: **jedes weitere zentrale UI-Element mit eigener Bedeutung** (z. B. Schwierigkeitsgrad-Badge, Event-Typ-Icon, Verifikations-Status, Filter-Chips, Kartensymbole) hat eine eigene, direkt an der Stelle abrufbare Erklärung — nicht nur im zentralen Glossar nachschlagbar.
- [ ] Die Erklärung ist ohne Verzögerung erreichbar: höchstens ein Antippen/Klick von der jeweiligen Funktion entfernt, keine Navigation durch mehrere Menüs nötig.
- [ ] Onboarding-Screens erscheinen nur beim ersten Start; wiederkehrende Nutzer werden nicht erneut damit konfrontiert, können sie aber über den „?"-Button jederzeit erneut aufrufen.
- [ ] Edge Case: Auf kleinen Bildschirmen (iPhone SE-Größe) verdeckt keine Erklärungs-Anzeige (Tooltip/Overlay) dauerhaft wichtige Inhalte darunter — sie lässt sich leicht wieder schließen.
- [ ] Edge Case: Wird eine erklärte Funktion später fachlich geändert (z. B. Score-Formel, neuer Event-Typ), ist im Entwicklungsprozess verankert, dass der zugehörige Erklärungstext mit aktualisiert wird (kein „vergessenes" veraltetes Erklär-Overlay).

**Scope-Erweiterung nach initialem Test-Feedback (2026-07-05):** Stephan hat den ersten Umsetzungsstand („In Test") gegengeprüft und weitere Lücken sowie ein Design-Korrektur gefunden. Die folgenden AKs erweitern den Scope, bevor das Ticket final getestet wird:

- [ ] **Optik bestehender ⓘ-Icons korrigiert:** Die 5 bereits vorhandenen ⓘ-Icons (Schwierigkeitsgrad, Event-Typ, Verifikation-Badge, Filter-Gruppen, Kartenlegende) werden kleiner und grau dargestellt, damit sie sich dezent einfügen und nicht neben anderen Elementen auffallen. Der „?"-Header-Button bleibt bewusst wie bisher (soll auffallen).
- [ ] **Neue ⓘ-Erklärungen ergänzt** an folgenden bisher nicht erklärten Sektionen in den Detail-Sheets (Chance und Location):
  - Wetterwerte (Temperatur/Regen/Wind/Sicht) im Chancen-Detail
  - Ideales Zeitfenster im Chancen-Detail
  - Wolken/Himmelsröte-Bereich inkl. Kompass-Ausrichtung im Chancen-Detail
  - Karte & Blickwinkel (Sichtfeld-Darstellung) im Chancen-Detail
  - Kompositions-Analyse im Chancen-Detail
  - Koordinaten-Anzeige im Chancen-Detail
  - Himmelsposition/Astronomie-Bereich im Chancen-Detail
  - Fotograf-Standort, Motiv und Ausrichtung im Location-Detail
  - Nächste Events im Location-Detail
  - Verifikationsbereich im Location-Detail
- [ ] **Kartenlegende erweitert** um die bisher nicht erklärten Bedienelemente: Kartenebenen-Umschalter (Nacht/Standard/Satellit), GPS-Standort-Button, Klickverhalten der Standort-Symbole auf der Karte (Popup mit Detail-Link), sowie ein Verweis auf die separate Wetter-Legende (US-72).
- [ ] **Neuer Glossar-Eintrag „Wie unterscheiden sich Feed, Kalender und Scout?"** erklärt die drei Ansichten anhand ihres tatsächlichen Zeithorizonts (siehe Erklärtexte unten, verifiziert im Code — nicht die ursprüngliche Vermutung).
- [ ] **Neuer Glossar-Eintrag „Wie funktionieren die Filter?"** erklärt anhand eines konkreten App-Beispiels, dass Auswahlen innerhalb einer Filtergruppe sich addieren (ODER), Filter über verschiedene Gruppen hinweg sich kombinieren (UND), und dass es bei manchen Filtern (z. B. Verifikation) einen dritten „Ausschließen"-Zustand gibt.

📎 Code-Verifikation zur Scope-Erweiterung (2026-07-05):
- `difficulty` einer Location wird ausschließlich über das Bearbeiten-Formular im Location-Detail gesetzt (Radio-Buttons `edit-difficulty`, `web/index.html` ~Zeile 5820-5825, übernommen in `saveEdit` ~Zeile 6110-6113). Ein separates Add-Formular mit eigenem Schwierigkeits-Feld wurde nicht gefunden — Locations werden über die API angelegt und danach im Edit-Formular nachjustiert.
- Der Verifikationsbereich im Location-Detail (`Verify.verifySection`, ~Zeile 2546, eingebunden ~Zeile 6229) hat aktuell **kein** eigenes ⓘ — anders als der Verifikations-**Badge** im Sheet-Header, der bereits eins hat. Beide sind zu unterscheiden: Badge = Kurzstatus-Anzeige (schon erklärt), Bereich = die Timeline + Formulare zum Melden/Bestätigen (noch nicht erklärt).
- Scout (`/discover`, `backend/main.py` ~Zeile 1804-1819): liefert laut Code-Kommentar „Mond-Alignment-Chancen für die nächsten 14 Tage" aus einem vorberechneten Cache, Parameter `days: int = 14`. Scout zeigt also gezielt Mond-Ausrichtungs-Chancen in einem festen 14-Tage-Vorschaufenster — nicht ein allgemeines Entdecken ohne Zeitgrenze.
- Kalender (`CalendarView`, ~Zeile 2212-2270): lädt und rendert **einen Monat pro Aufruf** (nicht das ganze Jahr), mit Monats-Navigation (`prev()`/`next()`) und Cache pro Monat. Der Ladetext „Jahreskalender wird geladen" ist etwas irreführend, tatsächlich wird monatsweise nachgeladen — für den Erklärtext wird der Fokus auf „Monatsübersicht mit freier Navigation" gelegt.
- Marker auf der Hauptkarte (`MapView.loadMarkers`, ~Zeile 4692-4714): alle Location-Marker verwenden dieselbe Farbe (`--accent`-Token), es gibt **keine** Farbdifferenzierung nach Kategorie. Die Kartenlegende darf das also nicht behaupten.

**Erklärtexte (final, für die Implementierung):**
- Wetterwerte im Chancen-Detail: „Diese Werte zeigen die vorhergesagte Wetterlage zum Zeitpunkt der Chance: Temperatur, Regenwahrscheinlichkeit, Windgeschwindigkeit und Sichtweite. Sie stammen von einem Wetterdienst und werden regelmäßig aktualisiert, sind aber wie jede Vorhersage nicht hundertprozentig sicher."
- Ideales Zeitfenster: „Das ist die Zeitspanne, in der Licht, Himmel und Ausrichtung am besten zusammenpassen, um das Motiv optimal zu fotografieren. Außerhalb dieses Fensters ist ein Foto oft trotzdem möglich, aber die Bedingungen sind weniger günstig."
- Wolken/Himmelsröte + Kompass-Ausrichtung: „Hier siehst du, wie wahrscheinlich eine goldene oder rote Himmelsfärbung ist, und in welche Himmelsrichtung du dafür schauen solltest. Die Kompassnadel zeigt dir die passende Blickrichtung direkt an."
- Karte & Blickwinkel (FOV): „Diese Karte zeigt, von wo aus du fotografierst, wohin dein Motiv liegt, und wie viel dein Objektiv bei der gewählten Brennweite tatsächlich einfängt. So siehst du vorab, ob das Motiv im Bild Platz hat."
- Kompositions-Analyse: „Diese Einschätzung hilft dir zu sehen, wie das Motiv im Bildausschnitt wirkt — zum Beispiel ob es zentriert oder eher am Rand steht. Sie ist ein Hinweis für die Bildgestaltung, kein festes Muss."
- Koordinaten: „Das sind die genauen GPS-Koordinaten des Standorts. Du kannst sie in eine Kartenapp kopieren oder direkt über die Maps-Buttons öffnen, um dorthin zu navigieren."
- Himmelsposition/Astronomie: „Hier wird angezeigt, wo Sonne, Mond oder andere Himmelskörper zum jeweiligen Zeitpunkt am Himmel stehen. Das hilft dir einzuschätzen, ob z. B. der Mond gerade in einer für dein Motiv passenden Position aufgeht oder untergeht."
- Fotograf-Standort/Motiv/Ausrichtung (Location-Detail): „Hier findest du, von wo aus fotografiert wird, was das Motiv ist, wie weit beides auseinanderliegt und in welche Richtung die Kamera zeigen sollte. Die Maps-Buttons bringen dich direkt zu beiden Punkten."
- Nächste Events (Location-Detail): „Diese Liste zeigt dir die nächsten Termine, an denen an diesem Standort besonders gute Fotobedingungen erwartet werden — praktisch, um direkt von der Location aus zum passenden Termin zu springen."
- Verifikationsbereich (Location-Detail): „Hier siehst du, ob und wann andere Nutzer diesen Standort schon vor Ort geprüft haben, und kannst selbst eine Prüfung eintragen oder ein Problem melden (z. B. versperrter Zugang). So bleibt die Info über den Standort aktuell und verlässlich."
- Kartenlegende, Ebenen-Umschalter: „Mit diesen drei Knöpfen wechselst du die Kartenansicht: Standard-Karte, Satellitenbild oder eine abgedunkelte Nachtansicht, die z. B. beim Blick auf Sternenlocations weniger blendet."
- Kartenlegende, GPS-Button: „Dieser Knopf zentriert die Karte auf deinen aktuellen Standort, damit du siehst, welche Locations in deiner Nähe sind."
- Kartenlegende, Klickverhalten: „Tippe auf ein Standort-Symbol, um Namen und eine kurze Beschreibung zu sehen — von dort kommst du mit einem weiteren Klick direkt zu allen Details dieser Location."
- Kartenlegende, Wetter-Legende-Verweis: „Zusätzlich zu den Standort-Symbolen gibt es eine eigene Wetter-Legende, die Wolken- und Regenanzeigen auf der Karte erklärt — die findest du direkt bei der Wetteranzeige."
- Glossar „Feed, Kalender und Scout": „Der Feed zeigt dir laufend aktuelle Foto-Chancen in zeitlicher Nähe. Der Kalender zeigt eine Monatsübersicht, durch die du frei vor- und zurückblättern kannst, um auch weiter in der Zukunft oder Vergangenheit liegende Chancen zu sehen. Scout ist ein spezieller Ausblick auf besondere Mond-Ausrichtungs-Chancen in den nächsten 14 Tagen."
- Glossar „Wie funktionieren die Filter?": „Wählst du mehrere Optionen innerhalb derselben Filtergruppe (z. B. zwei Event-Typen), werden dir Chancen gezeigt, die mindestens eine davon erfüllen. Kombinierst du dagegen mehrere Filtergruppen (z. B. Event-Typ UND Schwierigkeitsgrad), müssen beide Bedingungen gleichzeitig zutreffen. Beim Verifikations-Filter kannst du zusätzlich gezielt geprüfte oder ungeprüfte Standorte ausschließen."

**Pre-Mortem:**
- 💀 Szenario: Ein Score oder Event-Typ wird später fachlich geändert (neue Berechnung, neuer Schwellwert), aber der zugehörige Erklärungstext bleibt unverändert stehen → Nutzer bekommt eine falsche Erklärung angezeigt.
  Auslöser: Erklärungstexte liegen getrennt vom fachlichen Code, ohne Verknüpfung/Reminder.
  Frühwarnung: Bei künftigen Score-/Typ-Änderungen wird der Erklärungstext nicht im gleichen Umbau-Schritt geprüft.
  Gegenmaßnahme: Erklärungstexte an einer zentralen, klar benannten Stelle bündeln + als Prüfpunkt in die Test-/Review-Checkliste für Score-/Typ-Änderungen aufnehmen.
- 💀 Szenario: Ein Tooltip oder Overlay legt sich auf kleinen Bildschirmen über wichtige Inhalte (Buttons, Werte) und lässt sich nicht leicht wegtippen → Nutzer fühlt sich blockiert statt informiert.
  Auslöser: Neues Erklärungs-UI-Muster wird nicht gegen kleine Viewport-Größen getestet.
  Frühwarnung: Test nur auf großem Testgerät/Desktop-Breite.
  Gegenmaßnahme: Manueller Test auf kleiner Bildschirmgröße als AK/Testschritt aufnehmen.
- 💀 Szenario: Es entstehen zwei unterschiedliche Erklär-Interaktionen nebeneinander (US-55-Overlay für Scores, ein neues Tooltip-Muster für alles andere) → App wirkt uneinheitlich, Nutzer muss zwei Bedienweisen lernen.
  Auslöser: Neues UI-Muster wird ohne Rücksicht auf das bestehende US-55-Overlay entworfen.
  Frühwarnung: Kein Abgleich mit bestehendem `ScoreInfo`-Overlay vor Designentscheidung.
  Gegenmaßnahme: Designer-Check (fotoalert-designer) vor der Wegwahl einholen, damit ein einheitliches Erklär-Muster für die ganze App entsteht.
- 💀 Szenario: Wiederkehrende Nutzer werden bei jedem App-Start erneut mit dem Onboarding konfrontiert, weil der „schon gesehen"-Zustand nicht sauber gespeichert wird → Onboarding nervt statt zu helfen.
  Auslöser: Fehlender oder fehlerhafter Speicherzustand (z. B. bei App-Update zurückgesetzt).
  Frühwarnung: Kein Test über App-Neustart hinweg.
  Gegenmaßnahme: Als eigenes AK/Testschritt: Onboarding erscheint nach dem ersten Start nicht erneut, auch nach Neuladen/Update.

📎 Code-Verifikation (2026-07-05): `web/index.html` gelesen. Bestätigt: US-55 liefert einen fertigen, wiederverwendbaren Mechanismus — `ScoreInfo.show('gesamt'|'astro'|'wetter'|'wolkenstimmung')` öffnet `#score-info-overlay` (zentrales Overlay, CSS-Klasse `.open`, Schließen via `ScoreInfo.close()` durch „×"-Button oder Klick auf Overlay-Hintergrund). Kein Tooltip-Mechanismus (Hover) ist vorhanden — das bestehende Muster ist ein Klick-Overlay, kein reines Hover-Tooltip. Diese Spec sollte dieses Overlay-Muster als Basis nehmen statt ein neues Tooltip-System parallel zu bauen (vermeidet das dritte Pre-Mortem-Szenario oben).

📎 Implementierungs-Notiz (2026-07-05): Onboarding-Slides, „?"-Header-Button und Glossar-Overlay jetzt zusätzlich implementiert (`web/index.html`: `Onboarding`-Objekt, `Glossary`-Objekt, `#help-btn`, neue CSS-Blöcke + zwei neue SVG-Symbole `i-chevleft`/`i-chevdown`). Designer-Prototyp wurde gezeigt und exakt so freigegeben. Die fünf ⓘ-Element-Erklärungen (Schwierigkeitsgrad, Event-Typ, Verifikation, Filter-Gruppen, Kartenlegende) waren bereits vorher fertig und wurden nicht angefasst. Status bleibt „In Test" bis Stephan manuell getestet hat.

Scope-Erweiterung implementiert, 2026-07-05.

**Korrekturen nach zweitem Testdurchlauf, 2026-07-05:**

Stephan hat beim erneuten Testen vier Korrekturen gemeldet, die den obigen Implementierungsstand berichtigen (Ticket bleibt „In Test", kein Status-Wechsel):

1. **„?"-Header-Button — Kurskorrektur ggü. „soll auffallen":** Stephan hat die vorherige Design-Entscheidung („Der „?"-Header-Button bleibt bewusst wie bisher, soll auffallen", siehe AK oben) zurückgenommen. Der Button ist jetzt **gleich groß und gleich grau** wie die anderen Header-Icons (Suche, Filter, Refresh) — kein blauer Kreis-Outline mehr, keine optische Sonderstellung. Umgesetzt in `web/index.html`, `#help-btn`-CSS (~Zeile 507-511): identisches Muster wie `#search-btn`/`#filter-btn`/`#refresh-btn` (`background:none; border:none; color:var(--muted)`, 20×20px Icon-Box, Hover auf `var(--gold)`).

2. **Kartenlegende war ein Realitäts-Abgleich-Fehler, keine Formulierungssache:** Der zuvor implementierte Legendentext behauptete eine Darstellung von „Fotograf-Standort/Motiv-Symbol/Sichtachse-Linie" auf der Haupt-Karte — das stimmt nicht mit dem tatsächlichen Rendering überein. Verifiziert im Code: `MapView.loadMarkers()` (`web/index.html` ~Zeile 4700-4708) zeichnet auf der Übersichtskarte nur EIN einheitliches Pin-Symbol pro Location, immer in `--accent`-Farbe, keine Kategorie-Unterscheidung. Die Fotograf-Standort/Motiv/Sichtachse-Darstellung (`MapMarkers._obsIcon()`/`_subjIcon()`, ~Zeile 4568-4638, über `CameraFOV.panelHtml()`) existiert ausschließlich in der Mini-Karte im Abschnitt „Karte & Blickwinkel" innerhalb des Chancen-/Location-Detail-Sheets — NICHT auf dieser Übersichtskarte.
   Korrigierter Legendentext (`ElementInfo._mapLegendData()`, ~Zeile 6957-6979): „Jeder Pin markiert eine Foto-Location. Tippe auf einen Pin, um Namen und eine kurze Beschreibung zu sehen — von dort kommst du mit einem weiteren Klick direkt zu allen Details dieser Location." + Hinweis, dass die Fotograf-Standort/Motiv/Sichtachse-Darstellung NICHT auf der Übersichtskarte, sondern erst im Detail einer Location/Chance unter „Karte & Blickwinkel" zu sehen ist. Die Punkte zu Kartenebenen-Umschalter und GPS-Zentrierung blieben unverändert (waren bereits korrekt).
   Zusätzlich: Neben jedem Textpunkt steht jetzt ein kleines visuelles Symbol-Beispiel (Inline-SVG des echten Pins in `--accent`-Farbe bzw. Wiederverwendung von `MapMarkers.legendHtml()` für die Detail-Sheet-Symbole) — nicht mehr nur Fließtext.
   Der Wetter-Legende-Satz („Zusätzlich zu den Standort-Symbolen gibt es eine eigene Wetter-Legende...") wurde komplett aus dem Text gelöscht (Stephan: „--> löschen").

3. **Glossar-Eintrag „Wie unterscheiden sich Feed, Kalender und Scout?" fachlich korrigiert:** Der vorherige Text („Scout ist ein spezieller Ausblick auf besondere Mond-Ausrichtungs-Chancen in den nächsten 14 Tagen") war ungenau. Von Stephan korrigierte Fakten: Feed = 14-Tage-Feed (laufend aktuelle Chancen in zeitlicher Nähe); Kalender unverändert korrekt (Monatsübersicht, frei navigierbar); Scout errechnet **eigene** Chancen, basiert **nicht** auf von Nutzern angelegten Standorten, ist eine **Betaversion** und generiert **mögliche neue Perspektiven auf bekannte Motive**, die zum Erkunden einladen sollen, **nicht verifiziert** sind und **fehlerhaft sein können**.
   Neuer Text (`web/index.html` ~Zeile 7162): „Der Feed zeigt dir als 14-Tage-Vorschau laufend aktuelle Foto-Chancen in zeitlicher Nähe. Der Kalender zeigt eine Monatsübersicht, durch die du frei vor- und zurückblättern kannst, um auch weiter in der Zukunft oder Vergangenheit liegende Chancen zu sehen. Scout (Betaversion) errechnet eigene Chancen unabhängig von deinen angelegten Standorten und schlägt dir mögliche neue Perspektiven auf bekannte Motive vor — diese Vorschläge sollen zum Erkunden einladen, sind aber nicht verifiziert und können fehlerhaft sein."

Alle drei Korrekturen sind in `web/index.html` umgesetzt. Kein Status-Wechsel — Ticket bleibt „In Test" bis zum nächsten Testdurchlauf durch Stephan.

**Korrektur nach drittem Testdurchlauf, 2026-07-05 (Kartenlegende, Screenshot-Feedback):**

Die zweite Korrektur oben (Punkt 2) war selbst noch falsch: Der Absatz zu Fotograf-Standort/Motiv/Sichtachse wurde nicht entfernt, sondern nur textlich umformuliert — und rendete dabei kaputt (Bold-Tags mitten im Fließtext, einsames Komma auf eigener Zeile). Stephan hat per Screenshot des echten Overlays gegengeprüft und verlangt: ganze Sektion löschen, nicht nur Text reparieren.

- **Root Cause des Render-Bugs (behoben):** `ElementInfo._mapLegendData()` (`web/index.html`, damals ~Zeile 6974) bettete `MapMarkers.legendHtml()` — das ein Block-Element (`<div style="display:flex">…`) zurückgibt — in einen `<span style="display:inline-flex">` innerhalb eines `<p>` ein. Dieses Block-in-Inline-Nesting in der schmalen Overlay-Box (`#element-info-box`, `max-width: 320px`) erzeugte bei den `<b>`-lastigen Textteilen unvorhersehbare Zeilenumbrüche (Bold-Wort und das folgende Komma landeten getrennt auf eigenen Zeilen). Alle übrigen Legendenpunkte binden nur reine SVG-Strings direkt ein (kein `<div>`) und sind von diesem Muster nicht betroffen — geprüft, kein weiteres Vorkommen gefunden.
- **Fix:** Der komplette Absatz zu Fotograf-Standort/Motiv/Sichtachse (inkl. der Icon-Zeile mit `MapMarkers.legendHtml()`) wurde aus `_mapLegendData()` entfernt — nicht nur der Text, die ganze `<p>`-Zeile. `MapMarkers.legendHtml()` bleibt unverändert an ihrer ursprünglichen Stelle (Detail-Sheet-Mini-Karte, `web/index.html` ~Zeile 3975) im Einsatz, dort ohne Nesting-Problem.
- **Layer-Switcher verifiziert (echt, nicht entfernt):** `#map-layer-toggle` mit den drei Buttons `MapView.setLayer('dark'|'standard'|'satellite')` steht im Markup direkt innerhalb von `#page-map` (`web/index.html` ~Zeile 1210-1216) — das ist der Haupt-Karten-Tab, nicht die Location-Detail-Mini-Karte. Zu verwechseln wäre das nur mit `LocMapMode`/US-123 (~Zeile 3803-3853), das laut eigenem Code-Kommentar explizit „eigenständig … bewusst getrennt von MapView/Karten-Tab" für die Location-Formular-Karten gilt. CSS (`#map-layer-toggle`, `.map-layer-btn`, ~Zeile 271-277) zeigt keine Auffälligkeit (kein `display:none`, korrekte Position `top:12px;right:12px`, `z-index:1000`, 44×44px Touch-Fläche) — kein Anzeige-Bug gefunden. Legendentext dazu bleibt unverändert stehen.
- **GPS-Button verifiziert (echter Knopf, nicht nur Auto-Zentrieren):** `.map-gps-btn` (`onclick="MapView.locateMe()"`) steht ebenfalls direkt in `#page-map` (~Zeile 1246). `MapView.locateMe()` (~Zeile 4828) fragt bei Klick aktiv `navigator.geolocation.getCurrentPosition` ab und zentriert die Karte neu — das ist zusätzlich zum automatischen Init-Zentrieren aus US-117 ein eigenständiger, dauerhaft klickbarer Button. CSS (~Zeile 342-347) zeigt ebenfalls keine Auffälligkeit (sichtbarer Kreis, `bottom:30px;left:12px`, `z-index:1000`, goldene Farbe). Kein Anzeige-Bug gefunden. Legendentext dazu bleibt unverändert stehen.
- **Finaler Legendentext (`_mapLegendData()`, jetzt 3 statt 4 Punkte):**
  1. „Jeder Pin markiert eine Foto-Location. Tippe auf einen Pin, um Namen und eine kurze Beschreibung zu sehen — von dort kommst du mit einem weiteren Klick direkt zu allen Details dieser Location." (mit Pin-SVG-Symbol davor)
  2. „Mit diesen drei Knöpfen wechselst du die Kartenansicht: Standard-Karte, Satellitenbild oder eine abgedunkelte Nachtansicht, die z. B. beim Blick auf Sternenlocations weniger blendet."
  3. „Dieser Knopf zentriert die Karte auf deinen aktuellen Standort, damit du siehst, welche Locations in deiner Nähe sind."

Kein Status-Wechsel — Ticket bleibt „In Test" bis zum nächsten Testdurchlauf durch Stephan.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (siehe Rules/Examples unten)
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: betroffen wäre `web/index.html` (bestehendes `ScoreInfo`-Overlay-Muster ab Zeile ~4062/6691, Header-Bereich für „?"-Button, neue Erklär-Buttons an weiteren UI-Elementen wie Schwierigkeitsgrad-Badges, Event-Typ-Icons, Filter-Chips); ggf. `ios/FotoAlert/` falls die native App dieselben Erklärungen braucht (noch offen, siehe Fragen unten)
- [x] Designer-Check: visuell? → ja, mehrere sichtbar unterschiedliche UI-Muster (Tooltip/Overlay/Glossar/Inline-Hinweis) stehen zur Wahl. **`fotoalert-designer` sollte vor der endgültigen Wegwahl hinzugezogen werden**, um visuelle Varianten für das neue einheitliche Erklär-Muster zu zeigen (Memory-Regel „Icon-/Logo-Varianten zeigen" gilt sinngemäß für neue UI-Muster) — noch nicht durchgeführt, folgt nach Stephans Entscheidung für eine der drei Optionen unten.
- [x] Implementierungsoptionen: A / B / C (siehe unten)
- [x] Empfehlung: Option C (siehe unten)

**Beispiel-Szenarien (Example Mapping):**
- 📏 Regel: Jeder Score-Wert bleibt wie bisher per ⓘ-Klick erklärbar (US-55, kein Rückbau).
  🟢 Beispiel: Nutzer öffnet eine Chance im Detail-Sheet, tippt auf das ⓘ neben „Gesamt 82%" → Overlay mit Erklärung der Gesamt-Score-Berechnung öffnet sich, wie heute schon.
- 📏 Regel: Auch Nicht-Score-Elemente mit eigener Bedeutung (Schwierigkeitsgrad, Event-Typ, Verifikations-Status) sind direkt an ihrer Stelle erklärbar.
  🟢 Beispiel: Nutzer sieht einen Schwierigkeitsgrad-Badge „Schwer" auf einer Location-Karte, tippt darauf/auf ein kleines ⓘ daneben → kurze Erklärung was „Schwer" bedeutet (z. B. Zugang, Ausrüstung) erscheint sofort, ohne erst ins Glossar wechseln zu müssen.
- 📏 Regel: Das zentrale Glossar/„?"-Header-Button bleibt als Nachschlage-Übersicht zusätzlich bestehen.
  🟢 Beispiel: Nutzer tippt auf „?" im Header → Übersicht mit allen Score-Erklärungen, Schwierigkeitsgraden und Event-Typen an einem Ort.
- 📏 Regel: Onboarding erscheint nur einmal (erster Start), ist aber jederzeit über „?" erneut aufrufbar.
  🟢 Beispiel: Nutzer installiert die App neu → sieht beim ersten Öffnen 3–4 Einführungs-Screens. Beim zweiten Start erscheinen sie nicht mehr, sind aber über den „?"-Button abrufbar.
- ❓ Frage (offen, an Stephan): Sollen auch die iOS-App-Screens (`ios/FotoAlert/`) dieselben Inline-Erklärungen bekommen, oder ist der Scope zunächst auf die Web-App beschränkt? ⚠️ Annahme: zunächst nur Web-App (`web/index.html`), da dort auch US-55 umgesetzt wurde — bitte bestätigen.
- ❓ Frage (offen, an Stephan): Reicht ein kleines „ⓘ" pro Element (wie bei Scores) als einheitliches Symbol für „hier gibt's eine Erklärung", oder sollen manche Elemente (z. B. Filter-Chips) einen anderen visuellen Hinweis bekommen? ⚠️ Annahme: einheitliches ⓘ-Symbol überall, für Wiedererkennbarkeit — bitte bestätigen, ggf. im Designer-Check klären.

**Implementierungsoptionen:**

### Option A — Zentrales Glossar + Onboarding (ursprünglicher US-21-Scope)
- Vorgehen: Nur Onboarding-Slides + zentrales „?"-Glossar ausbauen; Scores bleiben wie in US-55, keine weiteren Inline-Erklärungen an einzelnen UI-Elementen.
- Vorteile: Kleinster Aufwand, ein Ort für alle Erklärungen, leicht pflegbar.
- Nachteile/Risiken: Erfüllt die US-116-Kernanforderung „ohne Verzögerung" nicht — Nutzer muss für jede Erklärung ins Glossar wechseln, verliert den Kontext zur gerade betrachteten Funktion.
- Aufwand: klein

### Option B — Kontextuelle Inline-Hilfe an jedem UI-Element
- Vorgehen: An jedem erklärungsbedürftigen UI-Element (Schwierigkeitsgrad, Event-Typ-Icon, Filter-Chip, Kartensymbol usw.) ein eigenes ⓘ/Tooltip direkt am Element, kein zentrales Glossar.
- Vorteile: Erklärung erscheint exakt dort, wo die Frage entsteht — deckt „ohne Verzögerung" am besten ab.
- Nachteile/Risiken: Kein zentraler Überblick für Neu-Nutzer, die sich erst orientieren wollen; höherer Pflegeaufwand, da Erklärtexte über viele Stellen verteilt sind (Pre-Mortem-Risiko „veraltete Texte" steigt).
- Aufwand: groß

### Option C — Kombination: Onboarding + zentrales Glossar + kontextuelle Inline-Erklärungen (empfohlen)
- Vorgehen: Onboarding-Slides und „?"-Header-Glossar wie in Option A bleiben als Einstieg/Nachschlagewerk erhalten. Zusätzlich bekommt jedes zentrale UI-Element (nicht nur Scores) sein eigenes ⓘ nach dem bestehenden US-55-Overlay-Muster — Inline-Erklärung direkt am Element, ohne Kontextwechsel.
- Vorteile: Deckt sowohl Neu-Nutzer (Onboarding + Glossar-Überblick) als auch die „ohne Verzögerung"-Anforderung (Inline-ⓘ überall) ab; nutzt ein bereits bewährtes, konsistentes UI-Muster (US-55) statt ein neues zu erfinden.
- Nachteile/Risiken: Größter Umfang, mehr Texte zu pflegen und aktuell zu halten (siehe Pre-Mortem); erfordert Sorgfalt, damit die Erklärtexte an zentraler Stelle gepflegt werden.
- Aufwand: groß

✅ **Empfehlung: Option C** — nur diese Kombination erfüllt sowohl den ursprünglichen US-21-Bedarf (Einstieg für neue Nutzer) als auch die von US-116 zusätzlich geforderte „ohne Verzögerung"-Anforderung, ohne ein zweites, inkonsistentes Erklär-Muster neben dem bewährten US-55-Overlay einzuführen. Vor der endgültigen Wegwahl sollte `fotoalert-designer` herangezogen werden, um konkrete visuelle Varianten des ⓘ-Inline-Musters an mehreren UI-Elementtypen zu zeigen (Badges, Icons, Chips sehen jeweils anders aus).

**Testplan:**
- [ ] Automatisiert (Harness): Prüfbar sind vor allem strukturelle Aspekte (z. B. „Onboarding-Flag wird nach erstem Durchlauf gesetzt und bleibt nach Reload bestehen") — als pytest-/Frontend-Test in der Implementierungsphase konkretisieren.
- [ ] Manuell: Neuinstallation/erster Start prüfen (Onboarding erscheint), zweiter Start prüfen (Onboarding erscheint nicht mehr), „?"-Button im Header prüfen (Glossar öffnet), je ein Beispiel-ⓘ bei einem Score (US-55-Bestand) und einem neuen Element (z. B. Schwierigkeitsgrad) prüfen, Test auf kleiner Bildschirmgröße (iPhone SE) gegen Verdeckung.

📎 **CI-Nachbesserung nach erstem Release-Versuch (2026-07-05):** Der automatisierte GitHub-Actions-Frontend-Check (`backend/tests/frontend/run_frontend_check.py`) schlug nach dem Release von v1.21.6 fehl (`Page.click` Timeout beim Klick auf eine Location-Karte). Erster Fix-Versuch (released als v1.21.7, Commit 2a5b0a9): Test setzt vor `page.goto()` per `page.add_init_script(...)` das Flag `fa_onboarding_seen='1'` in `localStorage`. **Dieser Fix reichte NICHT** — der nächste CI-Lauf zeigte exakt denselben Timeout.

📎 **Korrigierter Root Cause (2026-07-05, nach echter Analyse statt Wiederholung der alten Hypothese):** Die ursprüngliche Diagnose ("localStorage ist beim ersten CI-Start leer") war unvollständig. Tatsächlicher Ablauf laut Code (`web/index.html`): `Onboarding.initialShowIfNeeded()` (Zeile ~7088, `if (!localStorage.getItem('fa_onboarding_seen')) this.open();`) läuft NICHT beim Seitenladen, sondern erst als LETZTER Schritt von `App.init()` — und `App.init()` wird erst nach erfolgreichem Login aufgerufen (`LoginScreen.submit()`: `await Auth.login(pw); ...; await App.init();`). Der Test wartet aber nur auf `Auth.isLoggedIn()`, was bereits beim Setzen des Tokens wahr wird — deutlich BEVOR `App.init()` seine mehreren `await`-Netzwerk-Calls (Verify/Rating/CameraFOV/Locations/Feed) durchlaufen hat. Der Test läuft danach sofort weiter durch die View-Checks und öffnet die Locations-Karte, während `App.init()` im Hintergrund noch läuft — `Onboarding.initialShowIfNeeded()` kann also JEDERZEIT bis weit nach dem Login feuern, mit nicht-deterministischem Timing. Das `add_init_script`-localStorage-Flag selbst war korrekt gesetzt und die Prüf-Logik in `initialShowIfNeeded()` ist korrekt (truthy-Check, kein exakter String-Vergleich) — das Overlay ging trotzdem auf, weil ein zweiter, lokal ausprobierter aber nie released Fix-Versuch (`_force_close_onboarding`, einmaliger best-effort-Check direkt vor dem Klick) eine Race Condition offenließ: Das Overlay konnte sich in der schmalen Lücke zwischen diesem einmaligen Check und dem eigentlichen `page.click()` öffnen. Durch eine jsdom-Simulation (echter Playwright-Browserlauf war in der Analyse-Sandbox mangels Root-Rechten für System-Bibliotheken/`libXdamage.so.1` nicht möglich, Netzwerk-Proxy blockte auch den `.deb`-Download mit 403) wurde die Lücke des einmaligen Checks nachgewiesen und der neue Fix verifiziert.

📎 **Finaler Fix (dritter Versuch):** `_install_onboarding_guard()` in `run_frontend_check.py` installiert per `add_init_script` einen `MutationObserver` auf `#onboarding-overlay`, der die Klasse `open` sofort wieder entfernt, sobald sie (durch `Onboarding.initialShowIfNeeded()`, egal zu welchem Zeitpunkt) gesetzt wird — läuft synchron im Seitenkontext, keine Python/Playwright-Roundtrip-Verzögerung mehr, damit race-frei. Das `localStorage`-Flag aus dem ersten Fix-Versuch bleibt als zusätzliche Verteidigungslinie bestehen. Betrifft beide Testpässe (Desktop `run_checks` und Mobile `run_mobile_checks`); der einmalige `_force_close_onboarding`-Fallback wurde entfernt (durch den Observer ersetzt). Noch nicht released — Stand: lokal im Repo committet vorzubereiten und über den nächsten Release-Lauf zu verifizieren (echter CI-Lauf steht noch aus, da kein Playwright-Browserlauf in der Analyse-Sandbox möglich war).

📎 **Dritter Fix scheiterte ebenfalls im echten CI-Lauf (2026-07-05):** `_install_onboarding_guard()` (MutationObserver) wurde nach demselben Muster wie der erste Fix nur per Code-Lesen/jsdom-Simulation "verifiziert", nie per echtem Browserlauf — der tatsächliche GitHub-Actions-Lauf zeigte erneut denselben Fehler: `<div class="onb-title">Willkommen bei FotoAlert</div> from <div class="open" id="onboarding-overlay">…</div> subtree intercepts pointer events` beim Klick auf die Location-Karte in `_check_detail_sheet`.

📎 **Strategiewechsel — vierter Fix-Versuch (2026-07-05):** Statt weiterhin zu versuchen, das Erscheinen des Overlays per Timing-Trick zu verhindern (localStorage-Flag, MutationObserver), klickt der Testcode das Overlay jetzt aktiv und explizit weg, falls es erscheint — mit Playwrights dokumentierten Wartefunktionen statt einem selbstgebauten Timing-Mechanismus. Neue Funktion `_dismiss_onboarding_if_present(page)` in `run_frontend_check.py`: wartet per `page.wait_for_selector("#onboarding-overlay.open", timeout=5000)`, ruft dann `Onboarding.close()` (echte, im Code gefundene Funktion, `web/index.html` Zeile ~7104: setzt `localStorage.setItem('fa_onboarding_seen', '1')` UND entfernt die Klasse `open`) per `page.evaluate(...)` auf, und wartet mit `page.wait_for_selector("#onboarding-overlay:not(.open)", timeout=3000)` auf das tatsächliche Schließen. Best-effort per try/except — greift nicht, wenn das Overlay gar nicht erscheint. Aufgerufen an 5 Stellen: in `run_checks()` direkt nach `page.goto()` und nochmal nach dem Login (Onboarding läuft laut Code als letzter Schritt von `App.init()`, nach dem Login-Wait), zusätzlich direkt vor `page.click(_spec.LOCATION_CARD_SELECTOR)` in `_check_detail_sheet()`; analog dieselben drei Stellen in `run_mobile_checks()`. Die alten `add_init_script`/`MutationObserver`-Codeblöcke (`_install_onboarding_guard`) wurden vollständig entfernt, nicht nur auskommentiert.
>
> **Echter Browserlauf:** In der Analyse-Sandbox war das FotoAlert-Repo diesmal direkt gemountet (kein Kopieren nötig) und Playwright + Chromium waren bereits vorinstalliert (`~/.cache/ms-playwright/chromium-1228`). Ein `chromium.launch()` scheiterte jedoch weiterhin mit `libXdamage.so.1 => not found` (per `ldd` bestätigt, sowohl für `chrome` als auch für `headless_shell`) — die Bibliothek existiert nirgends im Sandbox-Dateisystem (`find / -name "libXdamage*"` liefert nichts). `sudo` ist im Container hart blockiert (`no new privileges`-Flag), `apt-get install` scheitert am fehlenden Schreibzugriff auf den dpkg-Lock (`Permission denied`, kein root). Damit war **kein echter Browserlauf möglich** — dieselbe Sandbox-Grenze wie beim dritten Fix-Versuch. Vertrauen in den vierten Fix stützt sich stattdessen darauf, dass `wait_for_selector` eine offiziell dokumentierte, robuste Playwright-API ist (kein selbstgebauter Timing-/Observer-Mechanismus mehr wie bei Fix 1–3) und `Onboarding.close()` exakt die Funktion ist, die auch der reguläre "Überspringen"-Button (`onclick="Onboarding.close()"`) im echten UI aufruft — keine Testdatei-spezifische Nebenlogik. Ein echter CI-Lauf (GitHub Actions) steht als einziger verbleibender scharfer Nachweis noch aus.

---

### US-07 · Goldene Wolken & Himmelsröte Scoring `[x]`
> **Status:** Done
> **Abgeschlossen:** 2026-06-30
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
> - Score wird **nur** für Events vom Typ `GOLDEN_HOUR_MORNING` oder `GOLDEN_HOUR_EVENING` berechnet – für alle anderen Event-Typen (inkl. Blaue Stunde) `null`
> - Kein separates `GOLDEN_CLOUD_VERSION` — stattdessen `ALGORITHM_VERSION`-Bump auf "1.4" (genügt, da Score live im Wetter-Overlay berechnet wird, nicht in precompute)
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
> - Nur angezeigt für Goldene-Stunde-Events (`GOLDEN_HOUR_MORNING`, `GOLDEN_HOUR_EVENING`) — Blaue Stunde und alle anderen Event-Typen: ausgeblendet
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
> *Folge-Tickets: US-109 (Richtungsbasiertes Wolken-Scoring), US-110 (Neue Event-Typen Goldene Wolken & Himmelsröte)*

---

### US-109 · Goldene Wolken & Himmelsröte als eigene Chancen: Richtungsbewusstes Scoring und Feed-Events `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-30 |
| **Abgeschlossen** | 2026-06-30 |

**Beschreibung:** Der aktuelle `golden_cloud_score` (US-07) berechnet nur die Gesamtmenge der Wolken pro Höhenstufe — er weiß nicht, in welcher Himmelsrichtung die Wolken stehen. Für goldene Wolken und Himmelsröte ist entscheidend, dass die Wolken **hinter dem Motiv in Sonnenrichtung** stehen (beim Abendrot im Westen, beim Morgenrot im Osten).

**Kern-Ziel dieses Tickets:** Wenn die Bedingungen für goldene Wolken oder Himmelsröte gut genug sind, soll für jede Location mit definiertem Standort und Motiv eine **eigenständige Chance im Feed erscheinen** — analog zu Mond-Alignment oder Sonnenfinsternis: als eigene Karte, mit eigenem Icon und eigenem Detail-Sheet. Die Chance bewertet, ob die Wolken photographisch nützlich stehen (Richtung Sonne, hinter dem Motiv), nicht nur ob Wolken vorhanden sind.

**Umfang:**
1. **Datenquellen-Klärung (Analyse-Phase):** Welche API kann räumliche Wolkenverteilung liefern? Open-Meteo liefert nur Gesamtprozente, keine Richtung. Alternativen: Satellitenbild-APIs, Radar-Tiles, Wolken-Cover-Gridforecast. Klärung inkl. Lizenz, Kosten, Verfügbarkeit in der Analyse.
2. **Richtungsbewusstes Scoring:** Berechnung ob Wolken in der Himmelsrichtung stehen, in die die Sichtachse Fotograf→Motiv zeigt — und ob die Sonne aus dieser Richtung leuchtet (Sonnenazimut aus US-107 bereits verfügbar).
3. **Chancen-Erzeugung:** Neue Event-Typen `GOLDEN_CLOUDS` und `RED_SKY` im Feed, die ausgelöst werden wenn Score ≥ Schwellwert. Eigene Karte, Icon, Detail-Sheet (ähnlich `MOON_ALIGNMENT`).
4. **Schematische Darstellung im Detail-Sheet:** Zeigt wo goldene Wolken relativ zur Sichtachse und Sonnenrichtung am Himmel erscheinen.

**Bezug:**
- **US-07 [x]** — Abhängigkeit: baut auf `golden_cloud_score` + Wolkenhöhen-Daten auf; ergänzt den Score um Richtungsinformation
- **US-107 [x]** — Überschneidung: Sonnen-Alignment-Planung liefert Sonnenazimut bereits; dieser kann als Basis für die Richtungsdarstellung genutzt werden
- **US-110 [ ]** — Ursprünglich separates Ticket für neue Event-Typen; Scope jetzt in US-109 integriert — US-110 kann nach Analyse ggf. geschlossen oder auf Restscope reduziert werden
- **US-72 [ ]** — Verwandt: Wetterkarte mit Grid-Forecast; könnte Datenquelle teilen

---

**📋 IMPLEMENTATION SPEC — US-109 · Goldene Wolken & Himmelsröte als eigene Feed-Events**

**Datenquellen-Klärung (Pflicht-Schritt laut Ticket — Ergebnis: 2026-06-30)**

Open-Meteo liefert `cloud_cover_low/mid/high_pct` als **Gesamtprozent über dem Standort** — keine räumliche Richtungsverteilung. Eine eigene Richtungsinformation für Wolken (Himmelssektor N/O/S/W) gibt es über Open-Meteo nicht und ist über keine frei zugängliche Standard-Forecast-API verfügbar:

- **Open-Meteo:** Gridded-Point-Forecast, columnar (kein Sektor). Kein Direktional-Parameter dokumentiert. Auch DWD MTG Satelliten-Integration (Feb 2026, 2.5–5 km) liefert nur Cloud-Cover-Gesamtwerte, keine Azimut-Verteilung.
- **Satellitenbild-APIs (NASA GIBS, EOS, Meteomatics):** Liefern Rasterbilder (GeoTIFF/PNG), keine strukturierte Azimut-Verteilung. Bildanalyse wäre möglich, aber komplex, teuer und lizenzrechtlich aufwändig — kein realisierbarer Weg für dieses Ticket.
- **Radar-Tiles / Wetterkarten:** Visualisierung, keine Machine-readable Direction-Daten pro Standort und Azimut.

**Fazit:** Eine echte gerichtete Wolkenverteilung ist mit verfügbaren APIs in diesem Rahmen **nicht realisierbar**. Das Ticket muss auf einen alternativen Ansatz umschwenken (→ Implementierungsoptionen).

---

**Annahmen-Protokoll (vor Example Mapping)**

| Punkt | Typ | Entscheidung |
|-------|-----|--------------|
| Eigene Event-Typen `GOLDEN_CLOUDS` / `RED_SKY` im Precompute oder nur im Wetter-Overlay? | 🔴 Kritisch | ✅ **Wetter-Overlay zur Laufzeit** (wie `golden_cloud_score`) — kein Precompute (Q1, 2026-06-30) |
| Soll US-110 nach dieser Analyse geschlossen werden? | 🔴 Kritisch | ✅ **US-110 geschlossen (Cancelled)** — Scope vollständig in US-109 integriert (Q2, 2026-06-30) |
| Richtungsbewusstsein: Proxy via `sunrise/sunset_azimuth` und `subject_azimuth` statt echter Wolken-Richtung? | ⚪ Annahme | ✅ **Harter Schwellwert ≤ 30° Azimut-Differenz** — kein gewichteter Score (Q3, 2026-06-30) |
| Score-Schwellwert für Event-Auslösung | ⚪ Annahme | → `golden_cloud_score ≥ 0.70` (konsistent mit US-07 Bonus-Grenze) |
| Separate Events vs. Anreicherung bestehender Goldene-Stunde-Events | 🔴 Kritisch | ✅ **`GOLDEN_CLOUDS` verdrängt normale Goldene-Stunde-Karte** — nur eine Karte pro Location+Zeit erscheint (Q4, 2026-06-30) |

---

**📎 Code-Verifikation (2026-06-30)**

- `backend/calculations/weather.py` gelesen: `calculate_golden_cloud_score()` existiert (US-07, deployed). `ALGORITHM_VERSION = "1.4"` in `precompute.py` (Zeile 58) — bereits gebumped für US-07.
- `backend/precompute.py` gelesen: `sunrise_azimuth` und `sunset_azimuth` werden pro Location berechnet (Zeilen 516–537) und sind im serialisierten Event verfügbar. `subject_azimuth` ist ebenfalls vorhanden (Zeile 465). Damit sind alle Azimut-Werte für einen Richtungs-Proxy bereits im Event-Objekt.
- `_ALIGNMENT_FILTER_EXEMPT` enthält `"Goldene Stunde Morgen"` und `"Goldene Stunde Abend"` — neue Event-Typen müssten dort ebenfalls eingetragen werden.
- Frontend `index.html`: `_ROUTINE_TYPES` enthält Goldene Stunde + Blaue Stunde (Zeile 2454). Neue Event-Typen müssen explizit kategorisiert werden (routine oder nicht) — beeinflusst Cap+Sort-Verdrängung (BUG-32-Mechanismus).
- `golden_hour_types` in `main.py` ist ein String-Set, kein Enum. Neue Typen können einfach ergänzt werden.

---

**Example Mapping**

📏 **Rule 1:** Wenn `golden_cloud_score ≥ 0.70` bei einer Goldene-Stunde-Chance und die Sonne aus Richtung des Motivs (≤ 30° Azimut-Differenz zwischen `sunset/sunrise_azimuth` und `subject_azimuth`) scheint, erscheint eine eigenständige „Goldene Wolken"-Karte im Feed.
- 🟢 *Abend, Motiv im Westen, Sonnenuntergang 278°, Motiv-Azimut 265°, gcs=0.82:* → Differenz 13° → Chance erscheint als eigene Karte „Goldene Wolken".
- 🔴 *Abend, Motiv im Osten (Azimut 90°), Sonnenuntergang 278°, gcs=0.82:* → Differenz 188° → Sonne leuchtet nicht ins Motiv → keine eigene Karte (nur normaler Goldene-Stunde-Event).
- ❓ Wenn Differenz im mittleren Bereich (30°–60°): noch „gut genug"? → Schwellwert klären.

📏 **Rule 2:** „Himmelsröte" (RED_SKY) tritt auf wenn `golden_cloud_score ≥ 0.80` und Wolkenschicht niedrig-mittel dominiert (`cloud_cover_low + cloud_cover_mid ≥ 60 %`) — dann färbt sich der Gesamthimmel tiefrot, nicht nur Cirrus. Kein Richtungsfilter nötig (Röte ist omnidirektional).
- 🟢 *`gcs=0.85`, `cl=40, cm=35, ch=10`:* → Himmelsröte-Event erscheint.
- 🔴 *`gcs=0.80`, `cl=5, cm=10, ch=60`:* → hohe Cirrus-Wolken, kein RED_SKY (nur GOLDEN_CLOUDS).

📏 **Rule 3:** Wenn `GOLDEN_CLOUDS`-Bedingungen erfüllt sind, **verdrängt** der neue Event die normale Goldene-Stunde-Karte — es erscheint nur eine Karte pro Location und Goldene-Stunde-Slot. Das verhindert Doppelkarten und Verwirrung.
- 🟢 *Feed zeigt: nur „Goldene Wolken" (neu) — keine separate „Goldene Stunde Abend"-Karte für dieselbe Location + Zeit.*
- 🔴 *Feed zeigt: „Goldene Stunde Abend" (normal) + „Goldene Wolken" (neu) gleichzeitig für dieselbe Location.* ← **nicht erwünscht (Q4-Entscheid).**

✅ **Q1 (entschieden 2026-06-30):** Neue Events werden **im Wetter-Overlay zur Laufzeit** erzeugt — wie `golden_cloud_score` selbst. Kein Precompute-Lauf nötig; kein ALGORITHM_VERSION-Bump erforderlich (außer wenn weitere Precompute-Änderungen nötig werden).

✅ **Q2 (entschieden 2026-06-30):** US-110 wird **geschlossen (Cancelled)** — Scope vollständig in US-109 integriert.

✅ **Q3 (entschieden 2026-06-30):** Azimut-Differenz als **harter Schwellwert ≤ 30°** — kein gewichteter Score. `|sunset_azimuth − subject_azimuth| mod 360 ≤ 30°` → GOLDEN_CLOUDS-Event wird erzeugt.

⚠️ **Annahme A:** Score-Schwellwert für Event-Auslösung: `golden_cloud_score ≥ 0.70` für GOLDEN_CLOUDS, `≥ 0.80` für RED_SKY — bitte bestätigen.
⚠️ **Annahme B:** Neue Event-Typen sind **nicht-routinemäßig** (wie Mond-Alignment) → werden in `_ROUTINE_TYPES` nicht eingetragen → profitieren vom BUG-32-Fix (priorisiert vor Goldener Stunde im Cap+Sort).
⚠️ **Annahme C:** Neue Events erhalten im Filter-Sheet je einen eigenen Chip unter „Event-Typen" (analog zu „Mond-Alignment"). Kein separater „Stimmungsfilter"-Block erforderlich — Annahme D (separater Chip-Block) alternativ möglich.
⚠️ **Annahme D:** Das Detail-Sheet zeigt eine schematische Himmels-Kompass-Grafik: Sonnenrichtung, Motiv-Richtung, und Wolkenposition relativ dazu — als SVG-Skizze analog zu CameraFOV. Aufwand: mittel. Falls Stephan das weglassen möchte → nur Text-Zeilen (Aufwand: klein).

---

**Akzeptanzkriterien**

- [ ] AK-1: Im Feed erscheint für eine Location, bei der `golden_cloud_score ≥ 0.70` und die Sonne aus Motivrichtung (Azimut-Differenz ≤ 30°) scheint, eine eigene Karte „Goldene Wolken" — zusätzlich zum normalen Goldene-Stunde-Event.
- [ ] AK-2: Die „Goldene Wolken"-Karte hat ein eigenes Icon und einen eigenen Kartentitel (nicht „Goldene Stunde Abend").
- [ ] AK-3: Beim Öffnen des Detail-Sheets einer „Goldene Wolken"-Chance ist eine Erklärung sichtbar, welche Wolkenkonstellation für die Bewertung relevant ist.
- [ ] AK-4: Im Feed erscheint für eine Location, bei der `golden_cloud_score ≥ 0.80` und `cloud_cover_low + mid ≥ 60 %`, eine eigene Karte „Himmelsröte" — unabhängig von der Motiv-Richtung.
- [ ] AK-5: „Himmelsröte"-Karte hat eigenes Icon + Titel.
- [ ] AK-6: Wenn `golden_cloud_score < 0.70` (oder kein Wetter-Overlay vorhanden), erscheint weder „Goldene Wolken"- noch „Himmelsröte"-Event.
- [ ] AK-7 (Richtungsfilter): Liegt die Sonne beim Abend-Event im Osten (Motiv im Westen, Differenz > 90°), erscheint **kein** „Goldene Wolken"-Event.
- [ ] AK-8 (Filter-Chip): Im Filter-Sheet unter „Event-Typen" sind „Goldene Wolken" und „Himmelsröte" als eigene Chips bedienbar.
- [ ] AK-9 (Cap+Sort): „Goldene Wolken"- und „Himmelsröte"-Events sind im Feed sichtbar, wenn gleichzeitig viele Goldene-Stunde-Events das Cap füllen (keine Verdrängung durch BUG-32-Mechanismus).
- [ ] AK-10 (Verdrängung, Q4): Wenn `GOLDEN_CLOUDS`-Bedingungen für eine Location erfüllt sind, erscheint **nur die Goldene-Wolken-Karte** — die normale Goldene-Stunde-Karte für dieselbe Location + Zeit wird unterdrückt. Für Locations ohne GOLDEN_CLOUDS-Bedingung erscheinen Goldene-Stunde-Events weiterhin normal.
- [ ] AK-11 (Regression): `golden_cloud_score`-Anzeige in der Wetter-Sektion (US-07) bleibt unverändert.
- [ ] Edge Case AK-12: Wenn `subject_azimuth` für eine Location fehlt (kein Motiv definiert), wird kein GOLDEN_CLOUDS-Event erzeugt (kein Richtungsvergleich möglich).
- [ ] Edge Case AK-13: Wenn kein Wetter-Overlay verfügbar (Event > 3 Tage), erscheinen keine GOLDEN_CLOUDS- oder RED_SKY-Events.

---

**Pre-Mortem**

💀 **Szenario 1: Cap+Sort-Verdrängung der neuen Event-Typen**
- Auslöser: Neue Typen landen im gleichen `[:500]`-Cap wie Goldene Stunde. Wenn sie als non-routine nicht korrekt priorisiert werden, erscheinen sie trotzdem nur selten.
- Frühwarnung: `Counter(e["event_type"] for e in result[:500])` zeigt GOLDEN_CLOUDS mit 0 oder 1 Einträgen.
- Gegenmaßnahme: Neue Typen explizit aus `_ROUTINE_TYPES` heraushalten; BUG-32-Fix in `_filter_feed()` greift dann automatisch.

💀 **Szenario 2: Doppelter Event für dieselbe Location und Zeit**
- Auslöser: Feed zeigt 3 Karten für dieselbe Location zur selben Zeit: Goldene Stunde Abend + Goldene Wolken + Himmelsröte. Das kann verwirrend sein und Deduplizierung brechen.
- Frühwarnung: Deduplizierungslogik in `_filter_feed()` (Zeile 1289–1296 main.py) verwendet `(location_id + event_type + Tag)` als Key — neue Typen werden korrekt separat gehalten, aber gleichzeitige Häufung ist möglich.
- Gegenmaßnahme: Entweder Prioritätsregel (GOLDEN_CLOUDS verdrängt normalen GOLDEN_HOUR wenn Bedingungen erfüllt) oder Hinweis im Detail-Sheet auf den zusammenhang. In Analyse-Phase als ❓ Q4 klären.

💀 **Szenario 3: `subject_azimuth` fehlt bei vielen Locations**
- Auslöser: Nur Locations mit definiertem Motiv haben `subject_azimuth`. Bei Locations ohne Motiv (nur Observer-Punkt) kann kein Richtungsvergleich stattfinden → GOLDEN_CLOUDS-Events würden für diese Locations nie erscheinen.
- Frühwarnung: Prüfen wie viele aktive Locations `subject_azimuth IS NULL` haben.
- Gegenmaßnahme: Fallback → wenn `subject_azimuth` fehlt: RED_SKY trotzdem erzeugen (omnidirektional), GOLDEN_CLOUDS nicht (richtungsabhängig).

💀 **Szenario 4: Wetter-Overlay-Events im Precompute vs. Laufzeit**
- Auslöser: Wenn neue Events im Precompute erzeugt werden müssen (wie Mond-Alignment) aber Wolkendaten erst T-3 verfügbar sind → Events werden nie erzeugt.
- Frühwarnung: Wetter-Overlay-Architektur in main.py lesen vor Impl.
- Gegenmaßnahme: Events ausschließlich im Wetter-Overlay zur Laufzeit erzeugen — Precompute hat keine Wetterdaten.

💀 **Szenario 5: ALGORITHM_VERSION bereits auf 1.4 (US-07)**
- Auslöser: Version 1.4 ist bereits deployed. Ein weiterer Bump auf 1.5 löst erneut ~8h Precompute-Vollauf aus — direkt nach US-07-Release.
- Frühwarnung: `precompute.py` Zeile 58 zeigt `ALGORITHM_VERSION = "1.4"`.
- Gegenmaßnahme: Bump auf 1.5 in Release-Notes dokumentieren; Release koordinieren. Alternativ: wenn neue Events nur im Wetter-Overlay erzeugt werden (Laufzeit), ist kein Version-Bump nötig.

---

**Architektur-Analyse**

Betroffene Dateien:

1. `backend/calculations/weather.py` — neue Funktion `should_generate_golden_cloud_event(gcs, sun_azimuth, subject_azimuth)` → prüft Bedingungen; `should_generate_red_sky_event(gcs, cl, cm)` → Himmelsröte-Schwellwert
2. `backend/main.py` — `_apply_weather_to_event()`: Logik für neue Event-Erzeugung im Wetter-Overlay; neue Events als separate Dicts in `_feed_cache` einfügen (analog zu bestehenden Events, aber `event_type = "Goldene Wolken"` / `"Himmelsröte"`)
3. `backend/precompute.py` — `_ALIGNMENT_FILTER_EXEMPT`: neue Typen ergänzen; ggf. `ALGORITHM_VERSION` Bump auf 1.5 (nur wenn Precompute-relevante Änderungen nötig)
4. `web/index.html` — `ICONS`: neue Icons für `"Goldene Wolken"` und `"Himmelsröte"`; `_ROUTINE_TYPES`: neue Typen explizit NICHT aufnehmen; Filter-Chips unter Event-Typen ergänzen; Detail-Sheet: ggf. Himmels-Kompass-SVG
5. `backend/tests/test_us109.py` — neue pytest-Fälle

**Einstiegspunkt-Check:**
- `/opportunities` → `_feed_cache` → Wetter-Overlay fügt neue Events ein → ✅ neue Events erscheinen im Feed
- `/calendar` → eigener Pfad, kein Wetter-Overlay → neue Events erscheinen **nicht** im Kalender (akzeptabel — Wolken-Events sind wetterabhängig)
- `/discover` (Scout) → eigener Pfad, kein Wetter-Overlay → neue Events erscheinen **nicht** im Scout (akzeptabel)

---

**Implementierungsoptionen**

### Option A — Proxy-Richtung: Azimut-Differenz Sonne ↔ Motiv (empfohlen)

Was du in der App erlebst: Die App berechnet, ob die Sonne beim Shooting aus der Richtung leuchtet, in die du schaust — also ob Sonnenuntergang/-aufgang und dein Motiv auf derselben Himmelsseite liegen. Wenn ja UND Wolkenstimmung gut genug: eigene Event-Karte. Das ist eine fundierte Näherung, die mit vorhandenen Daten (sunrise/sunset_azimuth + subject_azimuth) auskommt — ohne externe API.

- Vorgehen: Neue Events im Wetter-Overlay (`_apply_weather_to_event()`) generieren, wenn Schwellwerte erfüllt. Azimut-Differenz `|sunset_azimuth − subject_azimuth| mod 360 ≤ 30°` als Richtungs-Gate für GOLDEN_CLOUDS. RED_SKY ohne Richtungs-Gate.
- Betroffene Dateien: `weather.py`, `main.py`, `precompute.py` (Exempt-Liste), `index.html`, `tests/`
- Vorteile: Kein externer API-Key, keine Kosten, sofort umsetzbar; Azimut-Daten bereits vorhanden; testbar per pytest.
- Nachteile: Proxy ist eine Näherung — die Sonne kann aus der richtigen Richtung scheinen, aber Wolken sind trotzdem woanders. Das ist eine bekannte Einschränkung, die im Detail-Sheet transparent kommuniziert werden sollte.
- Aufwand: mittel

### Option B — Echte Wolken-Richtung via Satellitenbild-Analyse

Was du in der App erlebst: Die App würde Satelliten-Kacheln analysieren und auswerten, wo Wolken im Umkreis deines Standorts stehen — theoretisch präziser. In der Praxis: nicht realisierbar, da keine API räumliche Wolkenverteilung als strukturierte Daten liefert; Bildanalyse wäre ein eigenständiges ML-Projekt.

- Vorgehen: Satellitenbild herunterladen → Wolkenanteil im Azimut-Sektor (z.B. ±45° um Motiv-Azimut) extrahieren → Score.
- Betroffene Dateien: viele, inkl. neuem Bildverarbeitungs-Modul.
- Vorteile: Theoretisch präziser.
- Nachteile: Kein geeigneter API-Anbieter gefunden; Bildanalyse außerhalb des Projekt-Rahmens; Laufzeit und Kosten unbekannt.
- Aufwand: groß — nicht empfohlen.

### Option C — Scope-Reduktion: Keine eigenen Events, statt dessen stärkere Hervorhebung im bestehenden Goldene-Stunde-Event

Was du in der App erlebst: Keine neue Karte. Stattdessen: Wenn `golden_cloud_score` hoch und Richtung stimmt, bekommt die bestehende Goldene-Stunde-Karte ein zusätzliches Badge oder ein Highlight-Icon. Weniger Aufwand, kein neuer Event-Typ.

- Vorteile: Minimaler Scope, kein neues Event-Erzeugungs-Muster.
- Nachteile: Widerspricht dem Kern-Ziel des Tickets (eigenständige Karte wie Mond-Alignment). Nur als Fallback wenn Stephan Option A nicht freigeben möchte.
- Aufwand: klein

✅ **Empfehlung: Option A** — Proxy via Azimut-Differenz. Sauber, testbar, nutzt vorhandene Daten. Die Einschränkung (kein echter Wolken-Richtungssensor) wird im Detail-Sheet transparent kommuniziert. Option B ist nicht realisierbar; Option C widerspricht dem Ticket-Ziel.

---

**Testplan**

- [ ] Automatisiert (`backend/tests/test_us109.py`):
  - AK-1/6: Mockdaten: `gcs=0.82`, `sunset_azimuth=278`, `subject_azimuth=265` → Event-Typ `"Goldene Wolken"` in Output
  - AK-7: `gcs=0.82`, `sunset_azimuth=278`, `subject_azimuth=90` → kein GOLDEN_CLOUDS-Event
  - AK-4: `gcs=0.83`, `cl=40, cm=35` → Event-Typ `"Himmelsröte"` in Output
  - AK-12: `subject_azimuth=None` → kein GOLDEN_CLOUDS, ggf. RED_SKY
  - AK-9 (Cap+Sort): Counter prüfen nach BUG-32-Muster

- [ ] Manuell (Browser + curl nach Serverstart):
  1. `curl "http://localhost:8000/opportunities?days=3"` → Response auf Events mit `event_type = "Goldene Wolken"` oder `"Himmelsröte"` prüfen.
  2. App öffnen → Feed → ggf. Datum mit passenden Wetterbedingungen suchen → Goldene Wolken-Karte antippen → Detail-Sheet öffnet mit korrektem Icon + Inhalt.
  3. Filter-Sheet öffnen → „Goldene Wolken" und „Himmelsröte" als Chips sichtbar.
  4. Regression: Bestehende Goldene-Stunde-Events weiterhin im Feed sichtbar.
  5. Regression: Wetter-Sektion im Detail-Sheet (US-07 Wolkenstimmung) unverändert.

**Analyse & Planung:**
- [x] Datenquellen-Klärung: Open-Meteo liefert keine Richtungsverteilung; Satellitenbild-Analyse nicht realisierbar (2026-06-30)
- [x] Example Mapping durchgeführt (2026-06-30)
- [x] Pre-Mortem durchgeführt (2026-06-30)
- [x] Architektur analysiert: `main.py`, `weather.py`, `precompute.py`, `index.html`
- [x] Weg-Gate: Option A freigegeben, Q1–Q4 entschieden (2026-06-30) — Spec komplett, Ready for Dev

---

### ~~US-110 · Neue Event-Typen „Goldene Wolken" und „Himmelsröte" im Feed~~ `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done (Cancelled) |
| **Erstellt** | 2026-06-30 |
| **Geschlossen** | 2026-06-30 |

> ⛔ **Cancelled:** Scope in US-109 integriert. US-109 deckt sowohl das richtungsbasierte Scoring als auch die neuen Event-Typen `GOLDEN_CLOUDS` und `RED_SKY` vollständig ab. Separate Umsetzung nicht mehr erforderlich.

**Beschreibung:** Wenn die Wolkenbedingungen besonders gut für goldene Wolken oder Himmelsröte sind, soll ein eigenständiges Event im Feed erscheinen — als eigene Karte (analog zu Mondaufgang, Milchstraße), nicht nur als Score-Zusatz auf einer bestehenden Goldene-Stunde-Karte. „Goldene Wolken" und „Himmelsröte" werden zu eigenen Event-Typen mit eigenen Icons, eigener Karte und eigenem Detail-Sheet. Baut auf dem `golden_cloud_score` aus US-07 auf; der Score-Schwellwert für die Event-Auslösung ist Teil der Analyse.

**Bezug:**
- **US-07 [x]** — Abhängigkeit: `golden_cloud_score`-Berechnung muss fertig und deployed sein
- **US-109 [~]** — Scope vollständig integriert — US-110 daher Cancelled
- **US-82 [ ]** — Überschneidung: Scout Sun-Score v2 (Atmosphärisches Rötlichkeits-Scoring) hat ähnliche Zielsetzung; Abgrenzung in Analyse prüfen

---

**📋 IMPLEMENTATION SPEC — US-07 · Goldene Wolken & Himmelsröte Scoring**

**Scope:**
- Eingeschlossen: `_golden_cloud_score()`-Funktion in `calculations/weather.py`; `golden_cloud_score`-Feld in Wetter-Overlay (`main.py`); Frontend-Anzeige im Wetter-Detail-Sheet; `ALGORITHM_VERSION`-Bump auf "1.4"; **Filterkriterium „Wolkenstimmung" im Feed-Filter-Sheet** (neu 2026-06-29).
- Ausgeschlossen: Blaue-Stunde-Events (Score und Anzeige NUR Goldene Stunde — bestätigt Stephan 2026-06-29); Nebel/DWD (→ US-07b); Sunsethue-API; Kalender- und Scout-Ansicht (kein eigenes Detail-Sheet mit Wetter-Sektion).

> ✅ **Annahme A (bestätigt 2026-06-29):** Score gilt **ausschließlich für Goldene Stunde** (`GOLDEN_HOUR_MORNING`, `GOLDEN_HOUR_EVENING`) — **nicht für Blaue Stunde** (`BLUE_HOUR_EVENING`). Für alle anderen Event-Typen (Mond, Milchstraße, Alignment, Blaue Stunde) ist `golden_cloud_score = null` und die Anzeige bleibt ausgeblendet.
>
> ✅ **Annahme B (bestätigt 2026-06-29):** Kein separates `GOLDEN_CLOUD_VERSION` in `precompute.py`. Stattdessen einfacher **`ALGORITHM_VERSION`-Bump** von "1.3" → "1.4". Der Score wird ausschließlich zur Laufzeit im Wetter-Overlay berechnet, kein Precompute-Cache-Invalidierungseffekt nötig.
>
> ✅ **Annahme C (bestätigt 2026-06-29):** Der Wolkenstimmungs-Filter-Chip erscheint im Scout-Tab **ausgegraut** (nicht bedienbar) mit dem Hinweis-Text **„Nur im Feed verfügbar"** — sichtbar z.B. als statischer Text direkt unter den ausgegrautem Chips. Scout ignoriert `minCloudMood` vollständig.
>
> ✅ **Annahme D (bestätigt 2026-06-29):** Der Kalender **ignoriert den Wolkenstimmungs-Filter vollständig** — er zeigt unabhängig vom `minCloudMood`-Wert immer alle Kalender-Events an. Kein Ausgrauen, kein Hinweis nötig (Kalender-Events haben grundsätzlich kein Wetter-Overlay).

**📎 Code-Verifikation (2026-06-29):**
- `backend/calculations/weather.py` gelesen: `cloud_cover_low_pct`, `cloud_cover_mid_pct`, `cloud_cover_high_pct` sind **bereits in `HourlyWeather` vorhanden** und werden via Open-Meteo bereits abgerufen (Zeilen 29–31 + 163–176). Ticker-Annahme „Felder bisher nicht abgerufen" ist **widerlegt** — die Felder kommen bereits an.
- `backend/main.py`, Funktion `_apply_weather_to_event()` (Zeile 453–463): `weather_details`-Dict enthält `cloud_cover_pct` und `cloud_cover_high_pct`, aber **nicht** `cloud_cover_low_pct` und `cloud_cover_mid_pct`. Diese müssen ergänzt werden, damit das Frontend `golden_cloud_score` berechnen oder anzeigen kann (alternativ: Score direkt im Backend berechnen und als fertige Zahl mitliefern — empfohlen).
- `calculate_photo_weather_score()` enthält bereits Cirrus-Bonus (Zeile 108–109): `cloud_cover_high_pct > 20 and cloud_cover_low_pct < 30 → *1.15`. Das ist ein einfacher Vorläufer; US-07 baut darauf auf, aber ersetzt ihn nicht (kein Scope Creep).
- `ALGORITHM_VERSION = "1.3"` (precompute.py Zeile 58) — muss auf `"1.4"` gehoben werden.
- `OpportunityOut` (schemas.py Zeile 46–83): kein `golden_cloud_score`-Feld — muss als `Optional[float]` ergänzt werden.
- Frontend Wetter-Sektion (index.html Zeile 3401–3415): `o.weather_details` als Dict, daraus `wd.cloud_cover_high_pct` bereits genutzt (Cirrus-Hinweis). Das neue Feld `golden_cloud_score` sollte direkt als Top-Level-Feld des Events kommen (nicht im `weather_details`-Dict), analog zu `weather_score`.

**Example Mapping:**

**Frontend – Filter (Wolkenstimmung):**

**State-Modell:** Neues Feld `minCloudMood` (Integer 0–4) im Filter-State, analog zu `minScore` (ebenfalls ein Stufen-Wert, kein Include/Exclude-Array). Wert bedeutet: 0 = Alle, 2 = Mäßig+, 3 = Gut+, 4 = Exzellent. Standard: 0 (kein Filter aktiv). Erweiterung von `_defaults()` und `activeCount()` (+ 1 wenn `minCloudMood > 0`).

**UI:** Neue `filter-section` im Feed-Filter-Sheet, direkt unterhalb von „Mindest-Wahrscheinlichkeit" (beide sind Chancen-Kriterien, werden auf Karte/Locations ausgegraut). Abschnitt-Titel: „☁️ Wolkenstimmung". Vier Chips (einfacher Toggle, kein Drei-Zustand — das Kriterium ist ein Minimum, kein In-/Ausschluss):

| Chip-Label | minCloudMood | Score-Schwelle |
|---|---|---|
| Alle | 0 | Filter inaktiv |
| Mäßig+ | 2 | `golden_cloud_score ≥ 0.40` |
| Gut+ | 3 | `golden_cloud_score ≥ 0.65` |
| Exzellent | 4 | `golden_cloud_score ≥ 0.85` |

Antippen eines Chips setzt `minCloudMood` auf den Wert (erneutes Antippen des aktiven Chips setzt zurück auf 0). Nur ein Chip gleichzeitig aktiv (kein Multi-Select). Mapping Score → Stufe konsistent mit Anzeige-Labels im Detail-Sheet (AK-1, AK-3, AK-4, AK-5).

**Score-Schwellenwerte (Konsistenz Detail-Sheet ↔ Filter):**

| Stufe | Anzeige-Label | Score-Bereich | Filter-Chip |
|---|---|---|---|
| Exzellent | 🌅 Exzellent | ≥ 0.85 | Exzellent |
| Gut | ✨ Gut | 0.65 – 0.84 | Gut+ |
| Mäßig | 🌤 Mäßig | 0.40 – 0.64 | Mäßig+ |
| Gering | ⛅ Gering | < 0.40 | (nicht filterbar — würde „alles ohne Exzellent" bedeuten) |

**Filterlogik in `Filter.apply()`:**
- `minCloudMood > 0` aktiv: Events, bei denen `o.golden_cloud_score` **null oder undefined** ist (z.B. Mond, Milchstraße, Blaue Stunde, Events ohne Wetter-Overlay), werden **ausgeblendet**. Begründung: Der Filter bedeutet aktiv „zeig mir nur Goldene-Stunde-Events mit guter Wolkenstimmung" — Events ohne Score können diese Bedingung nicht erfüllen.
- Filterlogik: Schwellenwert je Stufe: Exzellent (4) → `o.golden_cloud_score >= 0.85`; Gut (3) → `>= 0.65`; Mäßig (2) → `>= 0.40`.
- Scout-Ansicht (`applyToScout`): Scout-Events kommen von `/discover`, kein `golden_cloud_score`-Feld. Wenn Filter aktiv, würden alle Scout-Events ausgeblendet. Daher: `applyToScout()` ignoriert `minCloudMood` (keine Filterung). Filter-Sektion erscheint auf Scout-Tab **ausgegraut** wie Tageszeit/Score, zusätzlich mit Hinweis-Text „Nur im Feed verfügbar" (z.B. als Tooltip oder statischer Text unter den ausgegrautem Chips). ✅ **Bestätigt Stephan 2026-06-29** (Annahme C).
- Kalender-Ansicht: `Filter.apply()` wird auf Kalender-Events angewendet (Zeile 1907 in index.html). Kalender-Events haben kein Wetter-Overlay → `golden_cloud_score = null` → bei aktivem Filter ignoriert der Kalender `minCloudMood` vollständig: Kalender zeigt **immer alle Events**, unabhängig vom Wolkenstimmungs-Filter-Wert. ✅ **Bestätigt Stephan 2026-06-29** (Annahme D).
- Ausgrauen im Filter-Sheet: Analog zu Tageszeit und Mindest-Wahrscheinlichkeit wird die Wolkenstimmungs-Sektion auf Karte und Locations-Tab **ausgegraut** (`opacity:.45;pointer-events:none`) — das Kriterium ist Chancen-spezifisch.
- Architekturpunkt: `minCloudMood` in `_defaults()` ergänzen (damit alter gespeicherter localStorage-State ohne das Feld per `Object.assign` korrekt aufgefüllt wird — bestehender Mechanismus, kein neuer Code nötig).

**Hinweis-Text unter den Chips:** „Nur für Goldene-Stunde-Chancen mit Wetter-Overlay (nächste 3 Tage). Chancen ohne Wolkendaten werden ausgeblendet."

---

📏 **Rule 1:** Für Goldene-Stunde- und Blaue-Stunde-Events berechnet das Backend beim Wetter-Overlay einen `golden_cloud_score` (0.0–1.0) aus den drei Wolkenhöhen.
- 🟢 *Scattered clouds (Sweet Spot):* `cl=5, cm=40, ch=30` → Score ≥ 0.70. In der App: Wetter-Sektion zeigt „✨ Gut" oder „🌅 Exzellent".
- 🟢 *Klarer Himmel:* `cl=0, cm=0, ch=0` → Score ≤ 0.20. In der App: „⛅ Gering".
- 🟢 *Tiefe Wolken dominieren:* `cl=90, cm=20, ch=10` → Score ≤ 0.10. In der App: „⛅ Gering".

📏 **Rule 2:** Bei `golden_cloud_score ≥ 0.7` erhält der `weather_score` des Events einen Bonus von 5–10 Prozentpunkten (max. 1.0).
- 🟢 *Bonus greift:* Event hat `weather_score=0.75`, `golden_cloud_score=0.82` → `weather_score` wird auf max. 0.85 angehoben.
- 🟢 *Kein Bonus:* Event hat `golden_cloud_score=0.55` → `weather_score` bleibt unverändert.

📏 **Rule 3:** Für alle anderen Event-Typen (Mond, Milchstraße, Alignment etc.) ist `golden_cloud_score = null` und die Anzeige bleibt ausgeblendet.
- 🟢 *Mond-Alignment:* Event-Typ „Mond-Alignment" → `golden_cloud_score` ist `null` → keine „Wolkenstimmung"-Zeile im Detail-Sheet.

📏 **Rule 4:** Die „Wolkenstimmung"-Zeile erscheint nur wenn das Wetter-Overlay aktiv ist (d.h. `weather_details` vorhanden, Event innerhalb T-3 Tage).
- 🟢 *T+5 Tage:* kein `weather_details` → keine Wolkenstimmungs-Zeile sichtbar, auch wenn Event-Typ passt.

**Akzeptanzkriterien:**

- [ ] AK-1: Beim Öffnen des Detail-Sheets einer Goldene-Stunde-Chance in den nächsten 3 Tagen erscheint in der Wetter-Sektion eine neue Zeile „Wolkenstimmung" mit einem der vier Labels (🌅 Exzellent / ✨ Gut / 🌤 Mäßig / ⛅ Gering).
- [ ] AK-2: Beim Öffnen des Detail-Sheets einer Mond-Alignment- oder Milchstraßen-Chance ist die Zeile „Wolkenstimmung" nicht sichtbar (weder Label noch Platzhalter).
- [ ] AK-3: Beim Öffnen des Detail-Sheets einer Goldene-Stunde-Chance mit `cl=5, cm=40, ch=30` zeigt die App „✨ Gut" oder „🌅 Exzellent" (Score ≥ 0.70).
- [ ] AK-4: Beim Öffnen des Detail-Sheets einer Goldene-Stunde-Chance mit `cl=90, cm=20, ch=10` zeigt die App „⛅ Gering" (Score ≤ 0.10).
- [ ] AK-5: Beim Öffnen des Detail-Sheets einer Goldene-Stunde-Chance bei klarem Himmel (`cl=0, cm=0, ch=0`) zeigt die App „⛅ Gering" (Score ≤ 0.20).
- [ ] AK-6: Eine Goldene-Stunde-Chance mit `golden_cloud_score ≥ 0.7` hat einen `weather_score` der um 5–10 Prozentpunkte höher liegt als ohne den Bonus, maximal 1.0.
- [ ] AK-7: Events weiter als 3 Tage entfernt zeigen keine Wolkenstimmungs-Zeile (da kein Wetter-Overlay aktiv).
- [ ] AK-8 (Regression): Bestehende Wetter-Anzeige (Bewertung, Temperatur, Wolken %, Regen, Wind, Sicht) für alle Event-Typen bleibt unverändert funktionsfähig.
- [ ] AK-9 (Regression): `overall_score`-Berechnung für Nicht-Goldene-Stunde-Events (Mond, Milchstraße, Alignment) bleibt unverändert.
- [ ] Edge Case AK-10: Wenn `cloud_cover_low_pct`, `cloud_cover_mid_pct` oder `cloud_cover_high_pct` im API-Response `null` sind, wird der `golden_cloud_score` auf `null` gesetzt (kein Crash, kein Fallback-Wert).
- [ ] AK-11 (Filter – UI): Im Feed-Filter-Sheet erscheint unterhalb von „Mindest-Wahrscheinlichkeit" ein neuer Abschnitt „☁️ Wolkenstimmung" mit den Chips „Alle", „Mäßig+", „Gut+" und „Exzellent".
- [ ] AK-12 (Filter – Grundfunktion): Ist der Chip „Gut+" aktiv, zeigt der Feed nur noch Goldene-Stunde-Chancen der nächsten 3 Tage mit `golden_cloud_score ≥ 0.65`. Mond-Events, Milchstraßen-Events und Events ohne Wetter-Overlay sind nicht mehr sichtbar.
- [ ] AK-13 (Filter – Chip-Toggle): Antippen des bereits aktiven Chips setzt den Filter zurück auf „Alle" (Filter-Badge zählt –1).
- [ ] AK-14 (Filter – Ausgrauen Karte/Locations): Auf der Karte und im Locations-Tab ist der Wolkenstimmungs-Abschnitt ausgegraut und nicht bedienbar, analog zu Tageszeit und Mindest-Wahrscheinlichkeit.
- [ ] AK-14b (Filter – Scout ausgegraut + Hinweis): Im Scout-Tab ist der Wolkenstimmungs-Abschnitt ausgegraut und nicht bedienbar. Unterhalb der ausgegrautem Chips erscheint der Hinweis-Text „Nur im Feed verfügbar".
- [ ] AK-14c (Filter – Kalender ignoriert Filter): Im Kalender-Tab werden unabhängig vom gewählten Wolkenstimmungs-Chip immer alle Events angezeigt. Der Kalender hat keinen eigenen Ausgrau-Hinweis (Verhalten entspricht dem bei Tageszeit/Wahrscheinlichkeit).
- [ ] AK-15 (Filter – Persistenz): Der gewählte Wolkenstimmungs-Filter bleibt nach App-Neustart erhalten (localStorage). Beim ersten Start nach dem Update ist der Filter auf „Alle" gesetzt (kein alter State ohne `minCloudMood` verursacht Fehler).
- [ ] AK-16 (Filter – Badge): Der Filter-Badge-Zähler am Filter-Icon erhöht sich um 1 wenn ein Wolkenstimmungs-Chip aktiv ist, und sinkt um 1 wenn er zurückgesetzt wird.
- [ ] Edge Case AK-17 (Filter – null-Score): Bei aktivem Wolkenstimmungs-Filter ist eine Goldene-Stunde-Chance, die mehr als 3 Tage entfernt liegt (kein Wetter-Overlay, `golden_cloud_score = null`), im Feed nicht sichtbar.

**Pre-Mortem:**

💀 **Szenario 1: `cloud_cover_low/mid_pct` fehlten bisher in `weather_details`**
- Auslöser: Ticket-Beschreibung suggerierte, die Felder würden noch nicht abgerufen. Tatsächlich werden sie abgerufen (HourlyWeather), aber nicht in das `weather_details`-Dict übernommen.
- Frühwarnung: Test `curl /opportunities` und `weather_details` inspizieren zeigt das sofort.
- Gegenmaßnahme: `_apply_weather_to_event()` erweitern um `cloud_cover_low_pct` und `cloud_cover_mid_pct` (oder golden_cloud_score direkt berechnen und als Feld anhängen — bevorzugt).

💀 **Szenario 2: Cirrus-Bonus in `calculate_photo_weather_score()` wird doppelt bewertet**
- Auslöser: `calculate_photo_weather_score()` enthält bereits einen Cirrus-Bonus (`*1.15`). Wenn US-07 zusätzlich einen `weather_score`-Bonus bei `golden_cloud_score ≥ 0.7` addiert, werden gute Cirrus-Bedingungen zweifach belohnt.
- Frühwarnung: Unit-Test mit `cl=5, cm=0, ch=40` → `weather_score` deutlich > 1.0 vor Kappung.
- Gegenmaßnahme: Den bestehenden Cirrus-Bonus in `calculate_photo_weather_score()` durch den neuen `golden_cloud_score`-Bonus ersetzen — oder den Bonus nur einmal anwenden. Scope-Entscheidung: **Vorschlag ist, den Cirrus-Bonus in `calculate_photo_weather_score()` zu belassen (Nicht-Goldene-Stunde-Events profitieren davon weiter) und den `golden_cloud_score`-Bonus additiv zu deckeneln.** Wegen möglicher Doppelbewertung Bonus max. +5 Pp. (nicht +10).

💀 **Szenario 3: `golden_cloud_score` erscheint fälschlicherweise im Kalender-Detail**
- Auslöser: Kalender-Events kommen von `/calendar`-Endpoint; wenn `OpportunityOut`-Schema erweitert wird, landet das Feld dort ebenfalls.
- Frühwarnung: US-96 Retro zeigte: `/calendar` liefert astronomy-only-Events ohne Wetter-Details → `weather_details = null` → Frontend zeigt sowieso nichts. Sicher, solange Frontend `golden_cloud_score` nur rendert wenn `weather_details` vorhanden.
- Gegenmaßnahme: Frontend-Bedingung immer `if (wd && o.golden_cloud_score !== null && o.golden_cloud_score !== undefined)`.

💀 **Szenario 4: `ALGORITHM_VERSION`-Bump erzwingt vollständigen Precompute-Lauf (~8h)**
- Auslöser: `ALGORITHM_VERSION` von "1.3" auf "1.4" → Cache wird als veraltet markiert → vollständige Neuberechnung beim nächsten Start (ca. 8h Laufzeit).
- Frühwarnung: Bekannt aus Memory `reference_fotoalert_server_paths`.
- Gegenmaßnahme: In Release-Notes dokumentieren; Release außerhalb Stoßzeiten; Wetter-Overlay übernimmt `golden_cloud_score` live, sodass der Score auch vor Ende des Precompute sofort sichtbar ist (für T-3-Events).

💀 **Szenario 5: Blaue-Stunde-Events zeigen „Wolkenstimmung" obwohl Score wenig Aussagekraft hat**
- Auslöser: Blaue Stunde findet nach Sonnenuntergang statt — Wolkenfärbung viel geringer. Ein „Exzellent"-Score könnte Erwartungen wecken, die nicht erfüllt werden.
- Frühwarnung: User-Feedback „warum zeigt mir die App exzellente Wolkenstimmung für die Blaue Stunde, wenn der Himmel nur tiefblau ist?"
- Gegenmaßnahme: ✅ Umgesetzt — Anzeige auf `GOLDEN_HOUR_MORNING` und `GOLDEN_HOUR_EVENING` beschränkt; `BLUE_HOUR_EVENING` explizit ausgeschlossen (bestätigt Stephan 2026-06-29).

**Architektur-Analyse:**

Betroffene Dateien:
1. `backend/calculations/weather.py` — neue Funktion `_golden_cloud_score(cl, cm, ch)` hinzufügen
2. `backend/main.py` — `_apply_weather_to_event()`: `golden_cloud_score` berechnen und als Top-Level-Feld ans Event anhängen; `weather_details`-Dict um `cloud_cover_low_pct`, `cloud_cover_mid_pct` ergänzen
3. `backend/models/schemas.py` — `OpportunityOut`: `golden_cloud_score: Optional[float] = None`
4. `backend/precompute.py` — `ALGORITHM_VERSION` "1.3" → "1.4"
5. `web/index.html` — Wetter-Sektion: neue „Wolkenstimmung"-Zeile + ⓘ-Tooltip

Nicht betroffen: `precompute.py` Scoring-Logik (Wetter-Score wird nicht in Precompute berechnet, nur im Live-Overlay), `discover/`-Pipeline, iOS-App.

**Betroffene Dateien (zusätzlich durch Filter-Erweiterung):**
6. `web/index.html` — `Filter._defaults()`: `minCloudMood: 0` ergänzen; `Filter.activeCount()`: `(s.minCloudMood > 0 ? 1 : 0)` ergänzen; `Filter.apply()`: Filterlogik nach dem `minScore`-Check einfügen; `FilterSheet._render()`: neue `cloudSection` (analog `scoreSection`) mit Ausgrauen auf Karte/Locations, Chips + Hinweis-Text; `FilterSheet.render()`: `cloudSection` in `filter-content`-HTML einbinden.

**Implementierungsoptionen:**

### Option A — Score vollständig im Backend berechnen (empfohlen)

Was du in der App erlebst: Die App liefert dir direkt eine fertige Einschätzung — „Exzellent", „Gut", „Mäßig", „Gering" — ohne dass dein Browser noch etwas berechnen muss. Das Feld `golden_cloud_score` (Zahl 0–1) kommt fertig vom Server und das Frontend zeigt nur das Label dazu.

- Vorgehen: `_golden_cloud_score()` in `calculations/weather.py`; Aufruf in `_apply_weather_to_event()` in `main.py`; Score als `e["golden_cloud_score"]` speichern; `OpportunityOut` um `Optional[float]` ergänzen; Frontend liest `o.golden_cloud_score`.
- Betroffene Dateien: `weather.py`, `main.py`, `schemas.py`, `precompute.py`, `index.html`
- Vorteile: Testbar per pytest; Konsistenz mit allen bestehenden Score-Feldern; keine Logik im Frontend.
- Nachteile: `ALGORITHM_VERSION`-Bump → 8h-Precompute; minimale Schema-Erweiterung.
- Aufwand: mittel

### Option B — Score im Frontend aus den Wolken-Feldern berechnen

Was du in der App erlebst: Gleiche Anzeige wie Option A — aber die App-Logik sitzt im Browser. Die Drei-Schichten-Werte (`cloud_cover_low/mid/high_pct`) müssen alle in `weather_details` stecken und das Frontend rechnet den Score.

- Vorgehen: `weather_details` um `cloud_cover_low_pct` + `cloud_cover_mid_pct` ergänzen; Scoring-Logik als JS-Funktion in `index.html`; kein neues Backend-Feld.
- Betroffene Dateien: `main.py` (weather_details), `index.html`
- Vorteile: Kein `ALGORITHM_VERSION`-Bump nötig; kein Schema-Change.
- Nachteile: Scoring-Logik nicht testbar per pytest; Duplikation (Logik existiert bereits im Backend-Kontext); `weather_score`-Bonus (AK-6) kann nicht im Frontend berechnet werden → AK-6 würde entfallen oder müsste im Backend bleiben → Hybrid-Ansatz nötig.
- Aufwand: mittel (aber schlechtere Qualität wegen fehlender Testbarkeit)

✅ **Empfehlung: Option A** — Score im Backend berechnen. Nur so ist AK-6 (weather_score-Bonus) testbar und konsistent. Der `ALGORITHM_VERSION`-Bump ist bekannter Standardprozess. Option B erzeugt einen Hybrid (Score im Frontend, Bonus im Backend) der schwer zu maintainen ist.

**Testplan:**

- [ ] Automatisiert (pytest in `backend/tests/test_us07.py`):
  - AK-3: `_golden_cloud_score(cl=5, cm=40, ch=30)` → ≥ 0.70
  - AK-4: `_golden_cloud_score(cl=90, cm=20, ch=10)` → ≤ 0.10
  - AK-5: `_golden_cloud_score(cl=0, cm=0, ch=0)` → ≤ 0.20
  - AK-6: Mock-Event mit `golden_cloud_score=0.82`, `weather_score=0.75` → `weather_score` nach Bonus ≤ 1.0 und > 0.75
  - AK-10: `_golden_cloud_score()` mit `None`-Inputs → gibt `None` zurück (kein Crash)
  - Regression Pre-Mortem S2: `cl=5, cm=0, ch=40` → `weather_score` nach Bonus ≤ 1.0

- [ ] Manuell (Browser + curl, nach Serverstart unter http://localhost:8000):
  1. `curl "http://localhost:8000/opportunities?days=3"` → in der Response eines Goldene-Stunde-Events prüfen: Feld `golden_cloud_score` vorhanden (Zahl 0–1 oder null).
  2. App öffnen → Feed → Goldene-Stunde-Event der nächsten 3 Tage antippen → Wetter-Sektion aufklappen → Zeile „Wolkenstimmung" mit Label sichtbar.
  3. Dasselbe für ein Mond-Alignment-Event → Zeile „Wolkenstimmung" darf nicht erscheinen.
  4. Regressions-Check: Bestehende Wetter-Sektion (Bewertung, Temperatur, Wolken, Regen, Wind, Sicht) für alle Event-Typen unverändert vorhanden.
  5. (AK-11) Filter öffnen → Abschnitt „☁️ Wolkenstimmung" mit Chips „Alle / Mäßig+ / Gut+ / Exzellent" sichtbar. Auf Karte: Abschnitt ausgegraut.
  6. (AK-12) Chip „Gut+" antippen → Anwenden → Feed zeigt nur noch Goldene-Stunde-Events der nächsten 3 Tage; Mond-Events verschwunden.
  7. (AK-13) Filter erneut öffnen → aktiven Chip nochmal antippen → Anwenden → Mond-Events wieder sichtbar, Badge–1.
  8. (AK-15) Page reload → Filter „Gut+" bleibt aktiv (aus localStorage).
  9. (AK-17) Feed-Event weiter als 3 Tage in die Zukunft → bei aktivem Filter nicht im Feed.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2026-06-29)
- [x] Pre-Mortem durchgeführt (5 Szenarien, alle mit Gegenmaßnahmen)
- [x] Code-Verifikation: `weather.py`, `main.py`, `schemas.py`, `precompute.py`, `index.html` gelesen
- [x] Architektur analysiert: 5 betroffene Dateien identifiziert
- [ ] Weg-Gate: Option A / B → Empfehlung Option A — Freigabe durch Stephan ausstehend
- [x] ✅ Klärung Annahme A: Score **nur** Goldene Stunde (GOLDEN_HOUR_MORNING + GOLDEN_HOUR_EVENING) — Blaue Stunde ausgeschlossen (bestätigt 2026-06-29)
- [x] ✅ Klärung Annahme B: Kein `GOLDEN_CLOUD_VERSION` — nur `ALGORITHM_VERSION`-Bump auf "1.4" (bestätigt 2026-06-29)

---

### US-08 · GPX-Export (Apple Maps / Google Maps)
> **Status:** Maps-Links für Fotograf-Standort und Motiv sind bereits in der Event-Detailansicht implementiert.
>
> **Offen:** „Alle Locations exportieren" als `.gpx`-Datei
>
> *Navigation & Fahrtzeit-Indikation → US-51 (separate Story)*

### US-09 · Sichtachsen-Check – Hinderniserkennung `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Ready for Dev |
| **Erstellt** | 2026-07-05 |

**Beschreibung:** Aktuell wird die Sichtachse Fotograf→Motiv nur als reine Richtungslinie (Bearing) behandelt — ob dazwischen tatsächlich Gebäude oder Gelände/Topographie die Sicht blockieren, wird nicht geprüft. Ein Raycast-Algorithmus (Höhendaten via OpenTopoData + Gebäudedaten via OSM Buildings) soll Hindernisse entlang der Sichtachse erkennen, damit Stephan nicht zu Standorten geleitet wird, an denen das Motiv tatsächlich verdeckt ist.

**User Story:** Als App-Nutzer möchte ich, dass die App erkennt und mir anzeigt, wenn zwischen meinem Fotostandort und dem Motiv Hindernisse (Gebäude oder Geländeerhebungen) die Sicht versperren, sodass ich nicht zu einem Standort fahre, von dem aus das Motiv gar nicht sichtbar ist.

**Bezug:** Keine Dublette gefunden. Verwandt, aber kein Scope-Overlap: **US-113** (Done) und **US-58** (Done) behandeln „Sichtachse" bisher nur als reinen Azimut-Winkelvergleich (Richtung Fotograf→Motiv bzw. Wolken-/Sonnenrichtung relativ dazu) — keines davon prüft, ob die Sichtlinie geometrisch tatsächlich frei ist. **TASK-45** (Done, „Idealer Azimut automatisch aus Gebäude-Footprints") hat bereits eine OSM-Gebäudedaten-Anbindung für einen anderen Zweck (Azimut-Vorschlag) gebaut — mögliche technische Grundlage/Wiederverwendung für dieses Ticket, aber keine inhaltliche Überschneidung. **US-51** (Navigation & Fahrtzeit) ist fachlich unabhängig (Routing, nicht Sichtprüfung). Empfehlung: eigenständiges Ticket, keine Merge/Split nötig.

#### 🔬 Analyse (fotoalert-analyze, 2026-07-05)

**Code-Verifikation (Pflicht vor Pre-Mortem/Optionen) — gelesen am 2026-07-05:**
- `backend/calculations/weather.py:182-268` (`should_generate_red_sky_event()` u.a.): bestätigt — der bisherige „Sichtachsen-Filter" ist ein reiner Azimut-Winkelvergleich (Antisolarpunkt ± 30°), keine Geometrie/Distanz/Höhe im Spiel. US-09 ist fachlich neu, kein Duplikat.
- `backend/data/qa_azimuth.py:127-234` (TASK-45): bestätigt — es existiert bereits ein produktiver Overpass-Client (`_fetch_overpass_footprint()`, POST an `overpass-api.de/api/interpreter`, Timeout 8s, Suchradius 40m, via `httpx`). Er ermittelt aktuell nur die Gebäudekante am Motiv selbst (für den Idealazimut), fragt aber keine Gebäude *entlang* der Sichtlinie ab. Wiederverwendbar als Query-Vorlage, nicht als fertige Lösung.
- `backend/data/elevation.py`: bestätigt — es existiert bereits ein produktiver OpenTopoData-Client (`api.opentopodata.org/v1`, Dataset-Kette `eudem25m → srtm30m → mapzen`, Rate-Limit-Pause 1.1s zwischen Calls, persistenter JSON-Tile-Cache unter `backend/data/cache/elevation_tiles.json`, async `httpx`, stiller Fallback `(0.0, incomplete=True)` bei Fehlern). Aktuell nur für den Höhenunterschied zwischen den zwei Endpunkten (Fotograf/Motiv) genutzt (US-31) — nicht für ein Höhenprofil mit Zwischenpunkten.
- `backend/data/locations.py:41-91` (`PhotoLocation`-Dataclass): bestätigt — Felder für Koordinaten, Distanz, Höhendifferenz, Idealazimut-Bereich vorhanden; **kein** Feld für einen vorberechneten Sichtachsen-Status.
- `backend/precompute.py:1087-1152`: bestätigt — täglicher Ablauf lädt Locations, wendet QA-Werte (Azimut) und Overrides an, danach Snapshot. Ein Sichtachsen-Check passt strukturell **pro Location einmalig** neben die bestehende Azimut-QA — nicht pro Event in die tägliche Feed-Berechnung, da sich Gebäude/Gelände nicht täglich ändern.
- `web/index.html`: bestätigt vorhandene Infrastruktur — „Sichtachsen-Profil"-Box im Preview-Sheet (Azimut/Distanz/Höhenwinkel, reine Anzeige, ca. Z. 6512), Kompass mit Sichtachsen-Pfeil (`mkCloudCompassSvg()`, ca. Z. 3562, aus US-111), gestrichelte Sichtachsen-Linie auf der Karte (`_drawPinsAndLine()`, ca. Z. 3911). Zusätzlich existiert bereits die manuelle Meldeoption „Sichtachse blockiert" (ca. Z. 2298) als Nutzer-Feedback-Kanal — aber kein automatischer Check. Die Visualisierungs-Bausteine für ein „frei/blockiert"-Badge sind vorhanden, es fehlt nur der Daten-Wert dahinter.
- `backend/requirements.txt`: bestätigt — einzige HTTP-Lib im Projekt ist `httpx==0.27.0` (kein `requests`/`aiohttp`).

**Externe API-Recherche (Pflicht, analog LLM-Gate) — verifiziert am 2026-07-05:**

*OpenTopoData (öffentliche Instanz `api.opentopodata.org`):*
- Kostenlos nutzbar, kein API-Key nötig (Quelle: github.com/ajnisbet/opentopodata README, opentopodata.org/api/).
- Rate-Limit für die öffentliche Instanz ist in der offiziellen Doku **nicht explizit als Zahl dokumentiert** (nur der Software-Default `max_locations_per_request: 100` als Serverparameter, keine bestätigte „X Requests/Sekunde"-Angabe für die konkrete Public-Instanz). Der bereits im Code vorhandene Client pausiert defensiv 1.1s zwischen Calls — das ist die bisherige, bewährte Vorsichtsmaßnahme.
- Kein SLA, Ein-Personen-Betrieb, Best-Effort. Bei dauerhaft höherem Bedarf verweist der Betreiber selbst auf Self-Hosting oder das kostenpflichtige Schwesterprojekt GPXZ.io.

*Overpass API (`overpass-api.de`):*
- Kostenlos nutzbar, kein API-Key zwingend (Quelle: dev.overpass-api.de/overpass-doc/en/preface/commons.html, offizielles User-Manual).
- Dokumentierter Richtwert: max. **~10.000 Requests/Tag** und **<1 GB Downloadvolumen/Tag** pro Nutzer/IP; Timeout-Default 180s, Max-Memory 512 MiB/Request; bei ausgelasteten Servern Warteschlange bis 15s, danach HTTP 429/504.
- **Wichtiger Befund:** Die Doku benennt explizit als unerwünschtes Nutzungsmuster „eine App bauen, die dauerhaft die öffentlichen Instanzen als Backend für mehr als reine OSM-Mapping-Zwecke nutzt" und empfiehlt in diesem Fall ausdrücklich Self-Hosting einer eigenen Instanz.
- Kein SLA, Best-Effort mit Load-Shedding (Heavy User werden zuerst gedrosselt).

**Einordnung für US-09:** Bei ~mehreren hundert Locations × mehreren Sample-Punkten pro Sichtlinie (grob 10–50 für ein Höhenprofil) würde ein **Live-Check pro Nutzeranfrage** built-in in beiden APIs an die fair-use-Grenzen stoßen — vor allem bei Overpass, wo Dauerbetrieb als App-Backend ausdrücklich als Fehlnutzung benannt wird. Ein **einmaliger Precompute pro Location** (ähnlich wie die bestehende Azimut-QA/Elevation-Nutzung) bleibt dagegen weit unter beiden Grenzwerten, weil Gebäude/Gelände sich praktisch nie ändern.

##### Annahmen-Protokoll

| # | Punkt | Typ | Einordnung |
|---|-------|-----|------------|
| 1 | Wird der Check einmalig pro Location vorberechnet (wie Azimut-QA) oder live bei jeder Chancen-Anzeige neu gerechnet? | 🔴 funktional kritisch | **Frage 1** unten |
| 2 | Gilt der Check nur für Alignment-Events (Sonne/Mond/Himmelsrichtung, wie im Ticket-Titel „Sichtachsen-Check" impliziert) oder auch für Wetter-Chancen (Golden Hour, Himmelsröte) die auch eine Blickrichtung haben? | 🔴 funktional kritisch | **Frage 2** unten |
| 3 | Was zeigt die App bei „teilweise blockiert" (z.B. Gebäude verdeckt nur die untere Hälfte der Sonnenscheibe kurz nach Aufgang)? | ⚪ konventionell | ⚠️ Annahme: Ampel-Modell mit 3 Stufen — frei / teilweise verdeckt (informativ) / komplett blockiert (warnend) — analog zum bestehenden Sichtachsen-Profil-UI. Bitte bestätigen. |
| 4 | Woher kommt die Beobachterhöhe (Augenhöhe/Stativhöhe) für den Raycast-Startpunkt? | ⚪ konventionell | ⚠️ Annahme: bereits vorhandenes Feld `observer_floor_height_m` (US-62) + Standard-Augenhöhe 1,6 m wird addiert. Bitte bestätigen. |
| 5 | Soll das Ergebnis nur am Standort selbst angezeigt werden (Location-Detail) oder auch als Filter-Chip nutzbar sein (z.B. „nur freie Sichtachse zeigen")? | ⚪ konventionell | ⚠️ Annahme: Für diesen ersten Schnitt nur Anzeige, kein Filter-Chip (Aufwand + gemäß Schritt 4f separat zu klären, wenn gewünscht). Bitte bestätigen. |
| 6 | Reicht eine 2D-Prüfung (Höhenprofil entlang der Linie ignoriert Erdkrümmung) oder muss Erdkrümmung ab welcher Distanz berücksichtigt werden? | ⚪ konventionell | ⚠️ Annahme: Erdkrümmungskorrektur ab 5 km Distanz einbauen (bei üblichen Motiv-Distanzen von wenigen hundert Metern bis 2-3 km i.d.R. vernachlässigbar, aber bei Fernmotiven wie Bergen relevant). Bitte bestätigen. |

**Offene Fragen (blockierend, bitte vor Freigabe beantworten):**
1. ❓ Soll der Sichtachsen-Check **einmalig vorberechnet** werden (Ergebnis ändert sich nur, wenn sich Standort/Motiv/Gebäude ändern — passt zu Empfehlung Option A unten) oder **live bei jeder Anzeige** neu gerechnet werden (aktueller, aber deutlich teurer und mit Blick auf Overpass-Fair-Use riskanter)?
2. ❓ Soll der Check nur für Alignment-Events (Sonnenuntergang/-aufgang, Mondauf-/-untergang, Himmelsrichtung) gelten, oder auch für Wetter-Chancen (Golden Hour, Blaue Stunde, Himmelsröte), die ebenfalls eine Blickrichtung haben?

**✅ Beantwortet durch Stephan (2026-07-05):**
1. **Prüf-Zeitpunkt:** Einmalig beim Anlegen/Ändern einer Location (Option A, wie empfohlen), Ergebnis wird gespeichert — kein Live-Check bei jeder Anzeige. Zusätzlich: Stephan möchte einen **manuellen "Jetzt aktualisieren"-Menüpunkt** für den Host im Refresh-Menü oben rechts, analog zu den bestehenden Einträgen für Wetter/14-Tage-Feed/Kalender, um den Sichtachsen-Check bei Bedarf bewusst selbst neu anzustoßen (z.B. wenn sich ein Gebäude in der Nähe verändert hat). Siehe neuer Baustein „Manueller Refresh-Trigger" unten.
2. **Geltungsbereich:** Der Check gilt nicht nur für Sonne/Mond/Himmelsrichtung-Alignment-Events, sondern zusätzlich für Wetter-Chancen mit Sichtachsen-Bezug — insbesondere Himmelsröte im Gegenpunkt-Sektor der Sonne (aus US-113, `should_generate_red_sky_event()` in `backend/calculations/weather.py:182-268`). Größerer Umfang für konsistentere Abdeckung über alle Event-Typen mit Blickrichtungsbezug hinweg.

##### Example Mapping

📏 **Regel 1:** Wenn zwischen Fotostandort und Motiv auf Höhe der Sichtlinie ein Gebäude oder eine Geländeerhebung höher liegt als die direkte Sichtlinie, gilt die Sicht als blockiert.
- 🟢 Beispiel: Fotostandort auf einem Hügel, Motiv (Sonnenuntergang-Richtung) liegt hinter einem 40m hohen Gebäude, das 200m vor dem Fotostandort in der Sichtlinie steht und höher ist als die gedachte Linie Auge→Horizont an dieser Stelle → Status „blockiert".
- 🟢 Beispiel: Freies Feld, kein Gebäude und keine Geländeerhebung zwischen Standort und Horizont in Zielrichtung → Status „frei".

📏 **Regel 2:** Eine teilweise Verdeckung (z.B. Sonnenscheibe wird erst kurz über dem Horizont von einem Hindernis verdeckt, danach frei) wird separat von einer vollständigen Blockade ausgewiesen.
- 🟢 Beispiel: Sonnenuntergang-Alignment, Hindernis verdeckt nur den untersten Teil des Sonnenuntergangs (erste 2° über Horizont) → Status „teilweise verdeckt", mit Hinweis „Sonnenuntergang erst ab ca. X° Höhe sichtbar".
- 🟢 Beispiel: Hindernis überdeckt die komplette Zielrichtung inkl. des gesamten Alignment-Zeitfensters → Status „blockiert".

📏 **Regel 3:** Der Check wird pro Location einmalig vorberechnet (nicht pro einzelner Chance/Event), da sich Gebäude/Gelände praktisch nie ändern — analog zur bestehenden Azimut-QA. Zusätzlich kann der Host den Check jederzeit manuell über einen neuen Menüpunkt im Refresh-Menü erneut anstoßen.
- 🟢 Beispiel: Neue Location wird angelegt/bearbeitet → Sichtachsen-Check läuft einmalig im Zuge der QA-Vorberechnung, Ergebnis wird an der Location gespeichert.
- 🟢 Beispiel: Location bleibt unverändert → beim täglichen Precompute wird der bereits gespeicherte Sichtachsen-Status wiederverwendet, kein erneuter externer API-Call.
- 🟢 Beispiel: Stephan öffnet als Host das Refresh-Menü oben rechts und klickt „Sichtachsen aktualisieren" (weil in der Nähe einer Location ein Neubau entstanden ist) → Check läuft für alle Locations neu, Ergebnis wird überschrieben, sobald der Job fertig ist (Statusanzeige im Menü wie bei Wetter/Feed/Kalender).

📏 **Regel 3b (Geltungsbereich):** Der Sichtachsen-Status wird nicht nur bei Alignment-Events (Sonne/Mond/Himmelsrichtung) angezeigt, sondern auch bei Wetter-Chancen mit Sichtachsen-Bezug — insbesondere Himmelsröte im Gegenpunkt-Sektor der Sonne (US-113).
- 🟢 Beispiel: Eine Himmelsröte-Chance (Wetter-Event) wird für eine Location mit bekanntem Hindernis in der Gegenpunkt-Sichtlinie angezeigt → Event-Detail zeigt denselben Sichtachsen-Status („blockiert"/„teilweise verdeckt"/„frei"/„nicht geprüft") wie ein Sonnenuntergangs-Alignment.
- 🟢 Beispiel: Golden-Hour-Chance ohne festen Sichtachsen-Bezug (keine spezifische Blickrichtung im Event) → kein Sichtachsen-Status nötig, da keine feste Ziellinie vorliegt (Regel gilt nur für Events mit Blickrichtungsbezug, nicht pauschal für jede Wetter-Chance).

📏 **Regel 4:** Schlägt die externe Höhen- oder Gebäudedaten-Abfrage fehl (Timeout, Datenlücke), wird das dem Nutzer ehrlich als „nicht geprüft" angezeigt — nicht stillschweigend als „frei" interpretiert.
- 🟢 Beispiel: OpenTopoData liefert für eine abgelegene Location keine Daten (ländliche Lücke) → Status „nicht prüfbar", kein falsches „frei"-Signal.
- 🟢 Beispiel: Overpass-Anfrage läuft in Timeout → Status bleibt „nicht geprüft" bis zum nächsten Precompute-Lauf, alte Anzeige (falls vorhanden) bleibt bestehen statt auf „blockiert" zu kippen.

*(Fragen 1 und 2 oben sind Voraussetzung für die finale Fassung von Regel 2 und den Anwendungsbereich von Regel 1 — nach Antwort ggf. Regeln nachschärfen.)*

##### Akzeptanzkriterien

- [ ] Für eine Location mit einem bekannten Gebäude in der Sichtlinie zeigt die App am Standort „Sichtachse blockiert" statt nur die reine Richtungslinie.
- [ ] Für eine Location mit freiem Blick zeigt die App „Sichtachse frei".
- [ ] Bei teilweiser Verdeckung zeigt die App „teilweise verdeckt" mit einem verständlichen Zusatz (z.B. ab welcher Höhe über dem Horizont das Motiv sichtbar wird), nicht nur ein pauschales Blockiert/Frei.
- [ ] Edge Case: Kann der Check für eine Location nicht durchgeführt werden (externe Daten nicht verfügbar), zeigt die App „nicht geprüft" statt fälschlich „frei" oder „blockiert".
- [ ] Edge Case: Für eine sehr weit entfernte Location (>5 km zum Motiv, z.B. Bergsilhouette) berücksichtigt der Check die Erdkrümmung, sodass keine falschen „blockiert"-Meldungen durch einen rechnerisch falschen, zu geraden Sichtstrahl entstehen.
- [ ] Der Check läuft automatisch beim Anlegen/Ändern einer Location bzw. beim regulären täglichen Vorberechnungslauf, nicht bei jedem einzelnen Aufruf einer Chance im Feed/Kalender (Performance, siehe Pre-Mortem).
- [ ] Bestehende Sichtachsen-Anzeigen (Profil-Box, Kompass-Pfeil, gestrichelte Linie auf der Karte) funktionieren unverändert weiter; das neue Blockiert/Frei-Ergebnis ergänzt sie, ersetzt sie nicht.
- [ ] **(neu, 2026-07-05)** Der Host findet im Refresh-Menü oben rechts einen neuen Menüpunkt „Sichtachsen aktualisieren" (analog zu Wetter/Feed/Kalender), über den er den Sichtachsen-Check für alle Locations manuell neu anstoßen kann; der Menüpunkt zeigt denselben Lauf-/Fertig-/Fehler-Status wie die bestehenden drei Einträge (Spinner während des Laufs, „vor X Min." nach Abschluss, Fehlertext bei Störung).
- [ ] **(neu, 2026-07-05)** Nicht nur Alignment-Events (Sonne/Mond/Himmelsrichtung), sondern auch Wetter-Chancen mit Sichtachsen-Bezug — insbesondere Himmelsröte im Gegenpunkt-Sektor der Sonne (US-113) — zeigen denselben Sichtachsen-Status (frei/teilweise verdeckt/blockiert/nicht geprüft) im Event-Detail an.
- [ ] **(neu, 2026-07-05, Design)** Der Sichtachsen-Status wird als vierfarbige Status-Pille dargestellt (Frei=Grün+Häkchen, Teilweise verdeckt=Orange+Halbdreieck-Icon, Blockiert=Rot+Warndreieck, Nicht geprüft=Grau+Fragezeichen) — sichtbar sowohl auf der Feed-Karte (`oppCard()`) als auch im Detail-Sheet der Chance; die Pille folgt optisch dem bestehenden Muster der `tag-verified`/`tag-issue`-Tags (kein neues Farbsystem).
- [ ] **(neu, 2026-07-05, Design)** Die vorhandene Sichtachsen-Linie/Kompass-Darstellung (Astro-Kompass-Linie, Sichtachsen-Profil-Box) ändert je nach Status ihren Linienstil: durchgezogen (Frei), gestrichelt (Teilweise verdeckt), unterbrochen/mit Balken markiert (Blockiert), gepunktet (Nicht geprüft) — reine Stil-Anpassung an bestehenden Elementen, kein neues Icon-Set.
- [ ] **(neu, 2026-07-05, Design)** Ein neuer Filter-Chip „Sichtachse" erlaubt das gezielte Ein-/Ausblenden nach Sichtachsen-Status (z.B. „nur Frei zeigen" oder „Blockiert ausschließen"), analog zum bestehenden Verifikationsfilter: Drei-Zustand-Zyklus (Off → Include → Exclude → Off) pro Chip, Badge-Zähler in der Filter-Kopfzeile bei aktivem Filter, und Ausgrauen des Chips auf Ansichten ohne Sichtachsen-Bezug (z.B. reine Location-Attribute-Kontexte), analog zur bestehenden Ausgrauen-Regel (BUG-46).

##### Pre-Mortem

- 💀 **Szenario:** Die App zeigt für dutzende Locations dauerhaft „nicht geprüft" an, weil die öffentliche Overpass- oder OpenTopoData-Instanz zeitweise überlastet ist oder den täglichen Bulk-Check als Fehlnutzung einstuft und blockiert.
  - Auslöser: Precompute fragt für alle Locations an einem Tag gebündelt ab, überschreitet Fair-Use-Muster.
  - Frühwarnung: Häufung von Timeout-/429-Fehlern im Precompute-Log.
  - Gegenmaßnahme: Ergebnis dauerhaft cachen (kein täglicher Re-Check, nur bei Standort-/Motiv-Änderung), Anfragen zeitlich entzerren (analog bestehender 1.1s-Pause bei OpenTopoData), Fallback „letzter bekannter Status" statt sofort „nicht geprüft" zu zeigen.
- 💀 **Szenario:** Für ländliche Locations in Brandenburg liefert OSM keine oder unvollständige Gebäudedaten → Check meldet fälschlich „frei", obwohl z.B. ein Wald oder eine Böschung (die OSM nicht als Gebäude, sondern nur als Fläche kennt) die Sicht blockiert.
  - Auslöser: Raycast prüft nur Gebäude-Footprints, nicht Wald/Vegetation/Geländekanten außerhalb des Höhenmodells.
  - Frühwarnung: Manuelle Nutzer-Meldung „Sichtachse blockiert" (bereits vorhandene Funktion) widerspricht dem automatischen „frei"-Status.
  - Gegenmaßnahme: In der Anzeige transparent machen, dass der Check auf Höhendaten + Gebäude basiert, nicht auf Vegetation — plus die bestehende manuelle Meldefunktion als Korrektiv explizit erwähnen/verlinken.
- 💀 **Szenario:** Präzision der Höhendaten (SRTM 30m-Raster) ist zu grob für kurze Distanzen (z.B. Gebäude 30m entfernt) → kleine, aber sichtrelevante Erhebungen werden nicht erkannt, oder Rauschen erzeugt falsche Blockaden.
  - Auslöser: Datensätze wie `eudem25m`/`srtm30m` haben Rasterauflösung von 25–30m, kleinere Objekte „verschwinden" zwischen den Stützpunkten.
  - Frühwarnung: Bekannte Location mit sicher freiem Blick wird fälschlich als „blockiert" markiert (False Positive) oder umgekehrt.
  - Gegenmaßnahme: Gebäude-Footprints (Overpass, punktgenauer als das Höhenraster) für den Nahbereich (<200m) primär nutzen, Höhendaten für den Gelände-Ferner-Bereich; Grenzfälle als „teilweise verdeckt" statt hartem „blockiert" ausweisen (konservativ in Richtung „nicht sicher" statt Falschmeldung).
- 💀 **Szenario:** Bei mehreren hundert Locations dauert der einmalige Precompute-Durchlauf sehr lange (jede Location = 1 Overpass-Call + mehrere OpenTopoData-Calls mit 1.1s-Pause), blockiert den ohnehin schon langen `--full`-Precompute-Lauf zusätzlich.
  - Auslöser: Sequenzielle externe Calls addieren sich (bei z.B. 300 Locations × ~2s im Schnitt ≈ 10 Minuten zusätzlich — grobe Schätzung, nicht gemessen).
  - Frühwarnung: Auffällig verlängerte Precompute-Laufzeit nach Rollout.
  - Gegenmaßnahme: Check nur einmalig bei Neuanlage/Änderung einer Location ausführen (nicht bei jedem täglichen Precompute-Lauf erneut), Ergebnis persistent speichern — deckt sich mit Regel 3 oben.
- 💀 **Szenario:** Erdkrümmung wird bei weit entfernten Motiven (z.B. Bergpanorama 20km entfernt) ignoriert → Sichtlinie wird als „blockiert durch Horizont" gewertet, obwohl in Realität durch die Erdkrümmungskorrektur der Blick frei wäre (oder umgekehrt).
  - Auslöser: Einfache lineare Höhenprofil-Berechnung ohne Erdradius-Korrektur.
  - Frühwarnung: Bekannte Fernmotive (Alpen-Sichtungen, hohe Sendemasten) werden falsch bewertet.
  - Gegenmaßnahme: Standard-Erdkrümmungs-/Refraktionskorrektur-Formel ab 5 km Distanz einbauen (siehe Annahme 6).

**Betroffene Nachbarbereiche für die Regression:** Location-Detail-Anzeige (Sichtachsen-Profil-Box), Event-Detail-Sheets mit Kompass-Pfeil (auch für Wetter-/Himmelsröte-Events, siehe Entscheidung 2), Karten-Darstellung der gestrichelten Sichtlinie, Precompute-Laufzeit gesamt, bestehende manuelle „Sichtachse blockiert"-Meldefunktion, **(neu, 2026-07-05)** bestehendes Refresh-Menü und dessen drei Einträge Wetter/Feed/Kalender (neuer vierter Eintrag darf deren Verhalten nicht stören).

##### Architektur-Analyse

**Betroffene Backend-Module:**
- `backend/data/elevation.py` — Erweiterung um Höhenprofil-Abfrage mit mehreren Zwischenpunkten (statt nur 2 Endpunkten), Wiederverwendung von Cache-/Rate-Limit-Pattern.
- `backend/data/qa_azimuth.py` — Erweiterung/neue Funktion für Gebäude-Footprint-Abfrage entlang der gesamten Sichtlinie (nicht nur am Motiv), Wiederverwendung der bestehenden Overpass-Query-Vorlage.
- `backend/data/locations.py` — neues Feld an `PhotoLocation` für den Sichtachsen-Status (z.B. Enum frei/teilweise/blockiert/nicht geprüft) + optionalem Detailwert (Verdeckungshöhe in Grad).
- `backend/precompute.py` — neuer Schritt neben der bestehenden Azimut-QA (`_apply_qa_values()`), der den Sichtachsen-Check einmalig pro Location/Motiv-Kombination ausführt und persistiert.
- `backend/main.py` — Location-Antwort um das neue Feld ergänzen; zusätzlich neuer Endpoint für den manuellen Refresh-Trigger (siehe Baustein unten).
- `backend/calculations/weather.py:182-268` (`should_generate_red_sky_event()`) — Erweiterung, damit auch für Himmelsröte-Chancen (US-113) der Sichtachsen-Status aus der Location mitgegeben wird, nicht nur für Alignment-Events (siehe Entscheidung 2 unten).
- `backend/calculations/` — neue Raycast-/Geometrie-Funktion (Höhenprofil + Erdkrümmung + Gebäudehöhen kombinieren, Sichtwinkel gegen Horizont berechnen).

**Betroffene Frontend-Teile:**
- `web/index.html` — „Sichtachsen-Profil"-Box (ca. Z. 6512) um Statusanzeige (frei/teilweise/blockiert/nicht geprüft) ergänzen; keine neue Sektion nötig, Erweiterung der bestehenden. Zusätzlich: neuer Menüpunkt im Refresh-Menü (siehe Baustein unten). Event-Detail-Sheets für Himmelsröte-Chancen zeigen künftig ebenfalls den Sichtachsen-Status (nicht nur Alignment-Event-Sheets).
- Optional: Badge/Icon am Location-Eintrag in der Locations-Liste (separates Designer-Thema, siehe unten).

**Neue Datenquellen/Dependencies:** Keine neue Library nötig (`httpx` bereits vorhanden). Neue externe Datenabfragen: erweiterte OpenTopoData-Höhenprofile (mehr Punkte pro Call, bereits unterstütztes API-Feature), erweiterte Overpass-Gebäudeabfragen entlang der Linie (größerer Suchradius/Bounding-Box statt nur 40m am Motiv).

**Designer-Check:** Ja, visuell sichtbar (neue Statusanzeige/Badge in bestehender UI-Box). `fotoalert-designer` sollte vor der Implementierung für die konkrete Darstellung (Icon/Farbe/Text der 4 Status frei/teilweise/blockiert/nicht geprüft) hinzugezogen werden — noch nicht durchgeführt, siehe Empfehlung unten.

**Neuer Baustein (2026-07-05): Manueller Refresh-Trigger**

Stephan möchte den Sichtachsen-Check zusätzlich manuell über das bestehende Refresh-Menü (oben rechts, `#refresh-menu-wrap` in `web/index.html`) anstoßen können — analog zu den drei bereits vorhandenen Menüpunkten. Am Code verifiziertes Muster (`web/index.html:7258-7370`, `backend/main.py:1887-1912`):

- **Frontend:** `RefreshMenu._cfg` (Objekt ca. Z. 7265-7269) definiert je Job `{ endpoint, label, doneMsg, reloadFeed }`. Ein neuer Eintrag `sightlines: { endpoint: '/sightline-refresh', label: 'Sichtachsen aktualisieren', doneMsg: '✅ Sichtachsen aktualisiert', reloadFeed: true }` reiht sich hier ein. Dazu ein neues `<div class="refresh-menu-item" id="rmi-sightlines" onclick="RefreshMenu.trigger('sightlines')">` im Menü-HTML (ca. Z. 1139-1166, neben den bestehenden `rmi-weather`/`rmi-feed`/`rmi-calendar`-Blöcken), inkl. `<div class="rmi-status" id="rms-sightlines">`. `RefreshMenu.trigger()` und `_applyStatus()` sind generisch (arbeiten über den `key`/`_cfg`-Mechanismus) und brauchen keine Änderung.
- **Backend:** Neuer Endpoint nach dem Muster von `@app.post("/refresh-calendar")` bzw. `@app.post("/weather-refresh")` (`backend/main.py:1887-1912`): `@app.post("/sightline-refresh")` mit `background_tasks: BackgroundTasks, _role: str = Depends(auth.require_host)` (Host-only, wie alle drei bestehenden Refresh-Endpoints), Guard gegen parallelen Lauf über `_precompute_running` (wie bei Feed/Kalender) oder einen eigenen Lock, `background_tasks.add_task(...)` stößt den Sichtachsen-Check für alle Locations neu an.
- **Status-Polling:** Läuft über den bereits generischen `_job_status`-Mechanismus (`backend/main.py:265-292`, Endpoint `GET /job-status` Z. 2012) — neuer Job-Key `"sightlines"` reiht sich dort ein, keine Änderung an `job-status` selbst nötig, nur `_job_status`-Dict um den neuen Key ergänzen (analog `weather`/`feed`/`calendar`).
- Damit ist der neue Menüpunkt strukturell identisch zu den drei bestehenden: gleicher Auth-Schutz (Host-Rolle), gleiches Spinner-/Status-/Fehler-Verhalten im Menü, gleiches Polling-Muster (`setInterval`, 3s) im Frontend.

##### Implementierungsoptionen

**Option A — Precompute mit persistentem Status (empfohlen)**
- Vorgehen: Sichtachsen-Check läuft einmalig beim Anlegen/Ändern einer Location bzw. beim nächsten regulären Precompute-Lauf, wenn noch kein Ergebnis vorliegt. Ergebnis (frei/teilweise/blockiert/nicht geprüft + Detailwinkel) wird an der Location gespeichert und in allen Ansichten (Feed, Kalender, Location-Detail) einfach mitgelesen — kein Live-Call bei jeder Chancen-Anzeige.
- Betroffene Dateien: `backend/data/elevation.py`, `backend/data/qa_azimuth.py`, `backend/data/locations.py`, `backend/precompute.py`, `backend/main.py`, `web/index.html`.
- Vorteile: Bleibt weit unter den Fair-Use-Grenzen beider externer APIs (siehe Recherche oben); schnelle Anzeige in der App (kein Warten auf externe Calls); Ergebnis stabil und nachvollziehbar; nutzt bestehende Precompute-Infrastruktur.
- Nachteile/Risiken: Ergebnis ist nicht „live" — wenn sich real ein neues Gebäude baut, merkt die App das erst beim nächsten manuellen Location-Update, nicht automatisch (aber: Gebäude entstehen nicht über Nacht, unkritisch).
- Aufwand: mittel bis groß (neue Geometrie-Berechnung + Precompute-Integration + Datenmodell-Erweiterung + UI-Anzeige).

**Option B — Live-Check bei jeder Anfrage**
- Vorgehen: Sichtachsen-Check wird bei jedem Öffnen einer Chance/eines Location-Details neu berechnet (Live-Call an OpenTopoData + Overpass).
- Betroffene Dateien: zusätzlich zu Option A auch neue Live-Endpoints in `backend/main.py`, keine Persistenz in `locations.py` nötig.
- Vorteile: Immer aktuell, auch bei kurzfristigen Geländeänderungen.
- Nachteile/Risiken: Verstößt gegen die von Overpass explizit benannte Fair-Use-Regel „keine App, die dauerhaft öffentliche Instanzen als Live-Backend nutzt"; spürbar langsamere Ladezeit beim Öffnen einer Chance (mehrere externe Calls mit Timeout-Risiko); höheres Ausfallrisiko bei Rate-Limiting.
- Aufwand: mittel (weniger Precompute-Integration), aber mit strukturellem Betriebsrisiko.

**Option C — Vereinfachter Nur-Gebäude-Check ohne Geländehöhen (kein Raycast über Terrain)**
- Vorgehen: Nur Overpass-Gebäudedaten entlang der Sichtlinie prüfen (Gebäudehöhe vs. Sichtlinienhöhe an dem Punkt), Geländehöhen/Erdkrümmung ignorieren.
- Betroffene Dateien: nur `backend/data/qa_azimuth.py`, `backend/data/locations.py`, `backend/precompute.py`, `web/index.html`.
- Vorteile: Deutlich weniger Aufwand, keine OpenTopoData-Erweiterung nötig.
- Nachteile/Risiken: Erfüllt den Ticket-Wortlaut nicht (explizit „Gebäude ODER Gelände"); in Brandenburg mit viel offener Landschaft/Hügeln wäre gerade die Geländeerhebung oft der relevantere Blocker als Gebäude — Kernnutzen des Tickets ginge verloren.
- Aufwand: klein bis mittel.

✅ **Empfehlung: Option A (Precompute mit persistentem Status).** Sie deckt den vollen Ticket-Scope (Gebäude UND Gelände) ab, bleibt bei beiden externen Diensten sicher innerhalb der recherchierten Fair-Use-Grenzen (Overpass warnt ausdrücklich vor Dauerbetrieb als Live-Backend), passt strukturell zur bestehenden Precompute-Pipeline (Azimut-QA läuft bereits nach demselben Muster) und liefert dem Nutzer eine sofortige Anzeige ohne Wartezeit. Option C wäre günstiger, verfehlt aber die im Ticket explizit geforderte Geländeerkennung.

##### Testplan

- **Automatisiert (Harness):** `backend/tests/test_us09.py` — Testfälle für: (1) bekanntes Gebäude in der Sichtlinie → Status „blockiert"; (2) freie Sichtlinie → Status „frei"; (3) simulierter API-Fehler (Mock-Timeout) → Status „nicht geprüft", nie „frei"; (4) Distanz >5km mit Erdkrümmungskorrektur → erwarteter Grenzwinkel stimmt mit Referenzrechnung überein; (5) teilweise Verdeckung (Hindernishöhe schneidet unteren Teil des Alignment-Fensters) → Status „teilweise verdeckt" mit korrektem Grenzwinkel; (6) **(neu, 2026-07-05)** Himmelsröte-Chance (US-113, `should_generate_red_sky_event()`) für eine Location mit bekanntem Sichtachsen-Status → Event trägt denselben Status wie ein Alignment-Event derselben Location.
- **Manuell:** Nach Implementierung unter `http://localhost:8000` an mind. 2 realen Brandenburg-Locations mit bekannter Sichtsituation (eine mit bekanntem Gebäude in Sichtlinie, eine mit freiem Feld) prüfen, ob die Anzeige im Location-Detail den erwarteten Status zeigt; zusätzlich eine Location ohne verfügbare Höhendaten (falls bekannt) auf „nicht geprüft" statt Fehlanzeige prüfen. Regressionsprüfung: bestehende Sichtachsen-Profil-Box, Kompass-Pfeil und Kartenlinie weiterhin unverändert sichtbar.
- **Manuell (neu, 2026-07-05) — manueller Refresh-Menüpunkt:** Als Host einloggen → Refresh-Menü oben rechts öffnen → neuer Eintrag „Sichtachsen aktualisieren" ist sichtbar, neben Wetter/Feed/Kalender → Klick darauf startet den Lauf (Spinner „Läuft…" erscheint, analog zu den drei bestehenden Einträgen) → nach Abschluss zeigt der Eintrag „vor X Min. (Ys)" und ein Toast „✅ Sichtachsen aktualisiert" erscheint → erneuter Aufruf einer Location bestätigt, dass der Sichtachsen-Status neu berechnet wurde (bzw. unverändert bleibt, wenn sich nichts geändert hat).
- **Manuell (neu, 2026-07-05) — Geltungsbereich Wetter-Chancen:** Eine Himmelsröte-Chance (Wetter-Event, nicht Sonnenuntergang-Alignment) für eine Location mit bekanntem Sichtachsen-Status im Feed/Kalender öffnen → Event-Detail zeigt denselben Status (frei/teilweise verdeckt/blockiert/nicht geprüft) wie bei einem Alignment-Event derselben Location — nicht nur bei Sonne/Mond/Himmelsrichtung-Ereignissen.
- **Manuell (neu, 2026-07-05) — Design: Status-Pille:** Feed öffnen, eine Chance mit Sichtachsen-Status „Blockiert" suchen → auf der Karte (`oppCard()`) erscheint neben den bestehenden Tags (Priorität/Brennweite/Wetter/Stativ/Geprüft) eine rote Pille mit Warndreieck-Icon und Text „Blockiert"; Klick öffnet Detail-Sheet → dieselbe Pille erscheint auch dort. Wiederholen für „Frei" (grün, Häkchen), „Teilweise verdeckt" (orange, Halbdreieck-Icon) und „Nicht geprüft" (grau, Fragezeichen-Icon) — alle vier Zustände optisch klar unterscheidbar, Farben konsistent mit dem bestehenden „Geprüft"-Tag (grün) bzw. „Problem"-Tag (rot).
- **Manuell (neu, 2026-07-05) — Design: Linienstil je Status:** Für je eine Location mit bekanntem Status „Frei", „Teilweise verdeckt", „Blockiert" und „Nicht geprüft" das Astro-/Kompass-Sheet bzw. die Sichtachsen-Profil-Box öffnen → die Sichtachsen-Linie zeigt den passenden Stil (durchgezogen/gestrichelt/unterbrochen-mit-Balken/gepunktet); Kompass-Legende „Sichtachse → Motiv" bleibt lesbar und eindeutig einem Zustand zuordenbar.
- **Manuell (neu, 2026-07-05) — Design: Filter-Chip:** Filter-Sheet öffnen → neuer Chip „Sichtachse" ist sichtbar (analog Verifikationsstatus-Sektion) → Tippen einmal → nur Chancen mit „Frei" werden angezeigt (Include-Zustand, Chip farblich hervorgehoben), Badge-Zähler oben in der Filter-Kopfzeile erhöht sich um 1 → nochmal tippen → Exclude-Zustand (Chancen mit diesem Status werden ausgeblendet, Chip in Warnfarbe) → drittes Tippen → zurück auf Aus. Prüfen, ob der Chip auf Ansichten ohne Sichtachsen-Bezug (falls zutreffend) ausgegraut/deaktiviert dargestellt wird, analog zur bestehenden Ausgrauen-Regel (BUG-46).

#### 🎨 Design-Entscheidung (fotoalert-designer, 2026-07-05)

Stephan hat die folgenden drei Design-Punkte final bestätigt. Code-Referenzen unten wurden am 2026-07-05 im laufenden Code verifiziert (nicht angenommen).

**1. Status-Pille (vier Zustände)**
- Die vier Sichtachsen-Zustände (Frei / Teilweise verdeckt / Blockiert / Nicht geprüft) werden als Tag/Pille dargestellt — analog zum bestehenden „Geprüft"-Tag-Muster.
- Verifiziertes Referenzmuster: `oppCard()` (`web/index.html:1772-1809`) baut die bestehenden Karten-Tags zusammen; Zeile 1790-1791 zeigt das Muster `Verify.getLast(o.location_id) ? '<span class="tag tag-verified">' + ic('i-check',12) + ' Geprüft</span>' : ''`, eingehängt in `<div class="opp-tags">` (Zeile 1805). Die CSS-Klassen `.tag-verified` / `.tag-issue` (Zeile 575-576) sowie `.verified-badge` / `.verified-badge-issue` (Zeile 573-574, fürs Detail-Sheet, siehe `ElementInfo`/Verify-Rendering Zeile 2469-2484) sind die bestehenden Farbbausteine, die wiederverwendet werden.
- Neue Pille folgt demselben Muster: ein neuer `tag-sightline-*`-Klassensatz (vier Varianten) analog zu `tag-verified`/`tag-issue`, eingehängt in `oppCard()` neben den bestehenden Tags sowie im Detail-Sheet der Chance (gleiche Position wie der „Geprüft"-Tag, damit Status-Infos gebündelt an einer Stelle erscheinen).
- Farben/Icons: Frei = Grün (`--green`, wie `.tag-verified`) + Häkchen-Icon (`i-check`, bereits vorhanden und im Code genutzt, Zeile 1791/3408); Teilweise verdeckt = Orange (neuer Ton, an bestehende Warn-/Gold-Paletten anlehnen) + Halbdreieck-Icon (neu anzulegen, kein bestehendes Icon-Kürzel gefunden); Blockiert = Rot (`--red`, wie `.tag-issue`) + Warndreieck-Icon (`i-warn`, bereits vorhanden und mehrfach genutzt, z.B. Zeile 2469/2483); Nicht geprüft = Grau (`--muted`) + Fragezeichen-Icon (neu anzulegen, kein bestehendes Icon-Kürzel gefunden).
- Sichtbar auf: Feed-Karte (`oppCard()`, Ergänzung analog zu Zeile 1790-1791/1805) und im Detail-Sheet der Chance (Detail-Sheet-Bereich ab `web/index.html:3608` „DETAIL SHEET" — exakte Einfügeposition erst bei Implementierung festzulegen, da abhängig vom finalen Sheet-Layout).

**2. Sichtachsen-Linie/Kompass je Zustand anpassen**
- Betroffene, verifizierte Code-Stellen:
  - Astro-Kompass-Legende „Sichtachse → Motiv": `web/index.html:5285` (`<span><i style="background:${this.COL.axis}"></i>Sichtachse → Motiv</span>`).
  - Tatsächliche Linien-Zeichnung der Sichtachse: `web/index.html:5407-5416`, konkret `this._ln(p, axisAz, C.axis, axisDist, 3, false)` (Zeile 5416). Die Zeichenfunktion `_ln(p, az, color, distM, weight, dashed)` (Zeile 5386-5390) setzt aktuell nur binär `dashArray: dashed ? '4 7' : null` — für vier Linienstile muss der `dashed`-Boolean-Parameter zu einem Stil-Parameter erweitert werden (z.B. `dashArray`-String direkt übergeben: `null` durchgezogen, `'4 7'` gestrichelt, `'1 4'` gepunktet, sowie ein separates Muster für „unterbrochen/mit Balken" für Blockiert — konkrete `dashArray`-Werte sind Implementierungsdetail, hier nur die Stelle benannt).
  - „Sichtachsen-Profil"-Box im Location-Anlegen-Preview: `web/index.html:6604-6611` (`AddLocation.renderPreview()`) — das ist eine statische Text-/Stat-Box (Azimut, Distanz, Höhenwinkel), **kein** SVG/Linien-Rendering; die Zeile im Ticket-Analyse-Abschnitt (Z. 6512) war ungenau — verifizierte Fundstelle ist Z. 6604-6611. Für diese Box selbst ist kein Linienstil anpassbar (keine Linie vorhanden), nur die Astro-Kompass-Linie (Punkt oben) trägt einen sichtbaren Linienstil.
  - Anpassung: durchgezogen (Frei, Standard wie bisher `dashed:false`), gestrichelt (Teilweise verdeckt), unterbrochen/durch Balken markiert (Blockiert, neues Muster), gepunktet (Nicht geprüft) — reine `stroke-dasharray`-Anpassung an der bereits bestehenden `_ln()`-Aufrufstelle für die Sichtachse (Zeile 5416), kein neues Icon-Set nötig.

**3. Zusätzlicher Filter-Chip „Sichtachse"**
- Analog zum bestehenden Verifizierungsfilter (`verificationIncl[]`/`verificationExcl[]`, siehe Memory-Referenz `reference_fotoalert_verification_filter`), verifiziertes Code-Pattern in `web/index.html`:
  - State: `verificationIncl: [], verificationExcl: []` im Default-State (Zeile 2832); neues Analogon z.B. `sightlineIncl: [], sightlineExcl: []`.
  - Zustandslogik: `verState()` (Zeile 3402-3406, liest ob ein Wert in Incl/Excl steckt) und `_cycleVerification(v)` (Zeile 3577-3596, Off→Incl→Excl→Off-Zyklus, ruft `Filter.save()`) sind die 1:1-Vorlage für eine neue `_cycleSightline(v)`-Funktion.
  - Rendering: `verChips` (Zeile 3407-3411, drei `chip3(...)`-Aufrufe für die drei Verifikations-Werte) sowie die Einbindung im Filter-Sheet-HTML (Zeile 3552, eigene `<div class="filter-section">` mit `fInfoBtn('verifikationsstatus')`) sind die Vorlage für die neue Sektion „Sichtachse" mit vier Chips (Frei/Teilweise verdeckt/Blockiert/Nicht geprüft).
  - Filteranwendung an den Datenquellen: Verifikationsfilter wirkt aktuell an drei Stellen — Zeile 2967-2973, 3011-3015 und 4794-4798 (jeweils `if (s.verificationIncl.length && !s.verificationIncl.includes(cat)) return false/visible=false; if (s.verificationExcl.includes(cat)) return false/visible=false;`) — der neue Sichtachsen-Filter muss an denselben drei Stellen analog ergänzt werden.
  - Badge-Zähler: Zeile 2885 zählt `((s.verificationIncl.length || s.verificationExcl.length) ? 1 : 0)` in die Gesamtsumme der aktiven Filter für den Badge in der Filter-Kopfzeile — der neue Sichtachsen-Filter zählt nach demselben Muster mit.
  - Ausgrauen-Regel: Die bestehende BUG-46-Logik unterscheidet zwischen Location-Attributen (u.a. auch auf Karte/Locations-Tab wirksam) und Chancen-Attributen (nur Feed/Kalender/Scout wirksam), siehe `isMapView`/`isLocationView`/`isChancenOnly` (Zeile 3433-3441) sowie die Memory-Referenz `reference_fotoalert_filter_criteria`. Da der Sichtachsen-Status an der Location hängt (Precompute-Ergebnis, siehe Analyse oben), ist er fachlich näher an einem Location-Attribut als an einem Chancen-Attribut — sollte also (wie z.B. Schwierigkeitsgrad/Kategorie) NICHT auf Karte/Locations-Tab ausgegraut werden, sondern dort ebenfalls wirken. Diese Einordnung ist eine Designer-Empfehlung basierend auf der Datenherkunft, keine von Stephan explizit bestätigte Entscheidung — bei Implementierung kurz gegenprüfen.

##### Analyse & Planung
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `backend/data/elevation.py`, `backend/data/qa_azimuth.py`, `backend/data/locations.py`, `backend/precompute.py`, `backend/main.py`, `web/index.html`
- [x] Designer-Check: visuell ja → `fotoalert-designer` durchgeführt am 2026-07-05, siehe Abschnitt „Design-Entscheidung" oben (Status-Pille, Linienstil je Zustand, Filter-Chip)
- [x] Implementierungsoptionen: A (empfohlen) / B / C
- [x] Empfehlung: Option A

**Offen vor Weg-Gate:** ~~Fragen 1 und 2 oben (Precompute vs. Live — Empfehlung: Precompute; Scope nur Alignment-Events oder auch Wetter-Chancen) müssen von Stephan bestätigt werden, bevor die Implementierung startet.~~ **Beide Fragen von Stephan beantwortet am 2026-07-05** (siehe „✅ Beantwortet durch Stephan" oben): Precompute-Ansatz bestätigt + manueller Refresh-Menüpunkt gewünscht; Geltungsbereich auf Wetter-Chancen mit Sichtachsen-Bezug (insb. Himmelsröte, US-113) erweitert. ~~Verbleibend offen vor Weg-Gate: Designer-Check (Statusanzeige-Darstellung) noch nicht durchgeführt.~~ **Designer-Check am 2026-07-05 abgeschlossen und von Stephan final bestätigt** (Status-Pille, Linienstil je Zustand, Filter-Chip — siehe Abschnitt „Design-Entscheidung" oben). Keine offenen Punkte mehr vor dem Weg-Gate.

### US-10 · Polarlichter / Aurora-Warnung
> NOAA SWPC Kp-Index, Push bei Kp ≥ 5. *(Offen)*

### US-11 · Bauarbeiten & Sperrungen
> Manuelles Crowdsourcing + Berlin Open Data API. *(Offen)*

---

## 🔬 Analyse (fotoalert-analyze, 2026-06-21)

### Example Mapping

**❓ Scope-Frage (vor Mapping):** „Ein Nutzer = eine Bewertung" — es gibt KEINE Nutzer-Accounts. US-66-Auth ist **rollenbasiert** (`host`/`user`), nicht personenbezogen: das Token ist `"<role>.<hmac>"` und für alle „user" identisch (`auth.py`). „Ein Nutzer" lässt sich serverseitig also nicht aus dem Auth-Token ableiten. Identität muss über einen **clientseitig generierten Geräte-Token** (UUID in localStorage) laufen. Annahme für diese Spec: 1 Gerät ≈ 1 Nutzer (akzeptierte v1-Grenze, analog zur Token-Grenze in US-66). Bei Bestätigung kein weiterer Klärungsbedarf → Mapping vollständig.

📏 **Rule 1 — Persistenz & Aggregation serverseitig.** Eine Bewertung (1–5) wird im Backend gespeichert; pro Location werden Anzahl und Ø aus allen Geräten berechnet und für alle ausgeliefert.
- 🟢 *Positiv:* Given Location L hat Bewertungen 5,4,3 von drei Geräten · When ein viertes Gerät `GET /ratings` lädt · Then es sieht `count=3, avg=4.0` (Ø auf 1 Nachkommastelle).
- 🔴 *Negativ:* Given L hat keine Bewertung · When `GET` · Then `count=0, avg=null` (NICHT `avg=0`, sonst zeigt UI „0 Sterne" statt „noch nicht bewertet").
- ⚠️ *Edge:* Given `value=6` oder `value=0` per POST · Then HTTP 422 (Range 1–5 erzwungen, wie `status`-Guard bei Verifikationen).

📏 **Rule 2 — Ein Gerät = genau eine Bewertung, überschreibbar (Upsert).** Wiederholtes Bewerten desselben Geräts ersetzt den alten Wert, zählt nicht doppelt.
- 🟢 *Positiv:* Given Gerät D bewertet L mit 4 · When D bewertet L erneut mit 2 · Then `count` bleibt 1, gespeicherter Wert = 2.
- 🔴 *Negativ:* Given Gerät D und Gerät E bewerten L · Then `count=2` (verschiedene Geräte zählen getrennt — kein fälschliches Dedup über Geräte hinweg).
- ⚠️ *Edge:* Given D löscht seine Bewertung (`DELETE`) · Then `count` sinkt um 1; war es die einzige → `count=0, avg=null`.

📏 **Rule 3 — Eigene Bewertung sofort & synchron sichtbar (Filter-Kompatibilität).** Der Rating-Filter ruft `Rating.get(id)` **synchron** auf (index.html Z. 1975, 2012). Die eigene Bewertung muss daher client-seitig in einem Cache liegen (wie `Verify._cache`), nicht erst per await nachgeladen.
- 🟢 *Positiv:* Given D hat L mit 4 bewertet, App-Neustart · When Feed lädt · Then `minRating>=3`-Filter behält L sichtbar (eigener Cache aus `GET /ratings` beim Boot befüllt).
- 🔴 *Negativ:* Given Rating-Cache nicht geladen (Netzfehler) · Then Filter wirft nicht, behandelt fehlende Bewertung als 0 (degraded, stabil — wie Verify).

📏 **Rule 4 — Migration aus localStorage, einmalig & idempotent.** Alt-Bewertungen unter `fotoalert_ratings` werden beim ersten Start ans Backend gepusht, danach lokal entfernt.
- 🟢 *Positiv:* Given localStorage `{L1:4, L2:5}` · When `init()` · Then beide als Bewertung dieses Geräts im Backend, `fotoalert_ratings` gelöscht.
- ⚠️ *Edge:* Given Migration läuft, Gerät hatte L1 schon serverseitig bewertet (Re-Install mit altem localStorage) · Then Upsert → kein Duplikat, keine Doppelzählung.

**Questions:** 0 offen (Geräte-Token-Annahme s.o.; bei Ablehnung → Rückfrage an Stephan).

### Akzeptanzkriterien (final, testbar)
- [x] `POST /locations/{id}/ratings` mit `{value:4}` + gültigem Geräte-Token speichert/aktualisiert → `200/201`, danach `GET /locations/{id}/ratings` liefert die Bewertung dieses Geräts.
- [x] `GET /locations/{id}/ratings` liefert `{count, avg, mine}` — `avg` auf 1 Nachkommastelle, `mine` = Wert des aufrufenden Geräts oder `null`.
- [x] Zweite POST desselben Geräts überschreibt: `count` unverändert, neuer Wert gespeichert (Upsert über `(location_id, device_id)`).
- [x] Zwei verschiedene Geräte → `count=2`, `avg` = Mittel beider Werte.
- [x] `value` außerhalb 1–5 → HTTP 422.
- [x] Edge: Location ohne Bewertungen → `count=0, avg=null` (UI zeigt „noch nicht bewertet", keine 0-Sterne).
- [x] `DELETE /locations/{id}/ratings` (Geräte-Token) entfernt eigene Bewertung; war es die letzte → `count=0`.
- [x] Schreib-Endpoints (POST/DELETE) verlangen `auth.require_auth` (401 ohne Bearer-Token); GET ohne Auth.
- [x] Edge (Migration): localStorage `fotoalert_ratings` wird beim ersten Start gepusht und gelöscht; erneuter Start pusht nichts mehr (idempotent, kein Crash bei leerem/kaputtem JSON).
- [x] Edge (Filter): `minRating`-Filter im Feed/Locations bleibt funktionsfähig (synchroner `Rating.get` aus Boot-Cache).

### Pre-Mortem
- 💀 **„Ein Nutzer" über alle Geräte gleich** — Auslöser: Identität fälschlich aus US-66-`user`-Token abgeleitet (ist für alle identisch) → ein Gerät überschreibt die Bewertung aller. Frühwarnung: zwei Geräte → `count` bleibt 1. **Gegenmaßnahme:** clientseitiger `device_id` (UUID via `crypto.randomUUID()` in localStorage `fa_device_id`), als Feld in POST mitgesendet → AK „zwei Geräte = count 2".
- 💀 **Migration-Doppelzählung bei Re-Install** — Auslöser: alter localStorage + bereits serverseitig vorhandene Bewertung → naives INSERT erzeugt 2. Frühwarnung: `count` steigt nach Re-Install. **Gegenmaßnahme:** Upsert per `UNIQUE(location_id, device_id)` (`INSERT … ON CONFLICT … DO UPDATE`) → idempotent.
- 💀 **Filter still tot** — Auslöser: Rating-Cache wird async geladen, aber `Rating.get` ist synchron im Filter → leerer Cache beim ersten Render filtert falsch (vgl. BUG-28). **Gegenmaßnahme:** `Rating.loadAll()` im `init()` VOR `Feed.load()` ziehen (analog `Verify.loadAll()`, Z. 4017–4019).
- 💀 **Python-3.9-Crash in Prod** — Auslöser: `str | None`-Syntax o.Ä. Frühwarnung: grün lokal (3.10), Crash auf Prod (3.9). **Gegenmaßnahme:** `from __future__ import annotations` + `Optional[...]`, exakt wie `store.py`/`auth.py`; `INSERT … ON CONFLICT` ist in SQLite ≥3.24 (Py 3.9 ok).
- 💀 **`avg=0` statt „unbewertet"** — Auslöser: Aggregation gibt 0 bei leerem Set → UI rendert 0 Sterne. **Gegenmaßnahme:** `avg=null` bei `count=0` (AK + Test).

### Architektur-Analyse
- **`backend/data/store.py`** — BUG-26 nutzt **eigene Tabelle** `location_verifications` (AUTOINCREMENT, Index auf `location_id`) + Methoden `add/get/delete_*`. US-89 folgt dem Muster mit **eigener Tabelle** `location_ratings` (NICHT verif-Tabelle erweitern — andere Kardinalität: hier Upsert pro `(location_id, device_id)`, dort append-Liste). Felder: `location_id TEXT`, `device_id TEXT`, `value INTEGER`, `updated TEXT`, `UNIQUE(location_id, device_id)`. Neue Methoden: `upsert_rating`, `get_rating_summary(location_id, device_id)`, `delete_rating`, ggf. `load_all_ratings` (Boot-Preload, analog `/verifications`).
- **`backend/main.py`** — Endpoints analog Z. 1266–1306: `GET /locations/{id}/ratings` (kein Auth), `GET /ratings` (Boot-Preload, kein Auth), `POST /locations/{id}/ratings` + `DELETE …/ratings` (`Depends(auth.require_auth)`). Neues Pydantic-Modell `RatingIn{value:int, device_id:str}`, Range-Guard 1–5 (422) wie `VerificationIn`-`status`-Check.
- **`backend/auth.py`** — unverändert; `require_auth` deckt POST/DELETE ab. Identität läuft NICHT über Auth (rollenbasiert), sondern über `device_id` im Body.
- **`web/index.html`** — `Rating`-Objekt (Z. 1778–1860) wird umgebaut: `_cache` (Aggregat pro Location) + `_mine` (eigene Werte), `device_id` aus localStorage `fa_device_id` (lazy `crypto.randomUUID()`), `loadAll()` + `migrateFromLocalStorage()` analog `Verify`. `get()` liest aus `_mine` (synchron, Filter-kompatibel). `inputHtml/displayHtml/feedTagHtml` zusätzlich Aggregat (Ø + Anzahl) anzeigen. `_set/_clear` → async POST/DELETE statt localStorage. `App.init()` (Z. 4013–4022): `Rating.migrateFromLocalStorage()` + `Rating.loadAll()` vor `Feed.load()`.

### Implementierungsoptionen
**Option A — Eigene Tabelle `location_ratings` mit `device_id`-Upsert (empfohlen).** Neue Tabelle + 4 Store-Methoden + 4 Endpoints; Frontend mit `device_id` + Boot-Cache analog Verify. Vorteile: sauberes Aggregat per `COUNT/AVG`, echte „1 Gerät = 1 Bewertung", folgt exakt dem etablierten BUG-26-Muster. Nachteile: clientseitige Identität (Geräte-Token, nicht personenscharf). Aufwand: mittel.

**Option B — Verif-Tabelle erweitern (`status='rating'`, value in Zusatzspalte).** Bewertungen als Sonder-Verifikationen ablegen. Vorteile: keine neue Tabelle. Nachteile: vermischt zwei Domänen, kein natürliches Upsert (Verif ist append-Liste → Doppelzählung), Aggregation muss filtern. Aufwand: mittel, aber fragiler.

**Option C — Rollenbasierte Identität ohne Geräte-Token (`user`-Token = ein Nutzer).** Vorteile: kein Geräte-Token nötig. Nachteile: **bricht das AK** — alle „user" teilen ein Token → eine globale überschreibbare Bewertung, `count` nie > 1. Verworfen.

✅ **Empfehlung: Option A** — folgt 1:1 dem bewährten BUG-26-Store-/Endpoint-Muster, erfüllt „1 Gerät = 1 Bewertung" sauber über `UNIQUE(location_id, device_id)` + Upsert und hält den synchronen Filter über einen Boot-Cache (Verify-Vorbild) am Leben; Geräte-Token ist die einzige tragfähige Identität, da US-66 rollen- statt nutzerbasiert ist.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (4 Rules, 0 offene Questions; Geräte-Token-Annahme bestätigungsbedürftig)
- [x] Pre-Mortem durchgeführt (5 Szenarien, Gegenmaßnahmen in AK/Plan verankert)
- [x] Architektur analysiert: `backend/data/store.py`, `backend/main.py`, `backend/auth.py`, `web/index.html` (Rating-Objekt)
- [x] Implementierungsoptionen: A (eigene Tabelle + device_id) / B (Verif-Tabelle) / C (rollenbasiert, verworfen)
- [x] Empfehlung **Option A** — Weg-Gate via Board (Lane „Ready for Dev") freigegeben → implementiert

**Implementierungsnotiz (2026-06-21, Pipeline-Heartbeat, Option A):**
- `backend/data/store.py`: Tabelle `location_ratings` (`UNIQUE(location_id, device_id)`) + `upsert_rating` (INSERT … ON CONFLICT DO UPDATE), `get_rating_summary` → `{count, avg, mine}` (avg 1 NK, `None` bei count 0), `delete_rating`, `load_all_ratings` (Boot-Preload). Folgt BUG-26-Muster.
- `backend/main.py`: `RatingIn{value, device_id}`; `GET /ratings` (Boot, kein Auth), `GET /locations/{id}/ratings?device_id=` (kein Auth), `POST` + `DELETE /locations/{id}/ratings` (`Depends(auth.require_auth)`). Range-Guard 1–5 + leeres device_id → 422. POST gibt **201**.
- `web/index.html`: `Rating` mit `_cache`/`_mine`, `fa_device_id` (lazy `crypto.randomUUID()`), `loadAll()` + `migrateFromLocalStorage()` (idempotent, crash-sicher), synchroner `get()` aus `_mine`; `loadAll` in `App.init()` **vor** `Feed.load()`. Ø + Anzahl in input/display/feedTag.
- Abweichungen: DELETE nutzt `device_id` als Query-Param (API.delete sendet keinen Body, konsistent mit `/verifications/last`); `GET /ratings` liefert Roh-Werte (Frontend leitet `mine` ab, analog `/verifications`).
- Unabhängige Verifikation: **GRÜN** — alle 10 finalen AKs + 5 Pre-Mortem-Gegenmaßnahmen im Code belegt; Py-3.9-konform (keine `X | None`, `Optional[...]` + `from __future__`).
- ⏳ **Offen (Test-Gate Stephan):** manueller Browser-/iOS-Test (zweites Gerät/`fa_device_id`, `minRating`-Filter, Migration mit Alt-Daten) + Release-Gate (Deploy am Mac-Terminal).

**Testplan:**
- [x] Automatisiert (`backend/tests/test_api_regression.py`, Docstring „US-89"): POST→GET Roundtrip (`count/avg/mine`), Upsert (zweiter POST gleiches device_id → count stabil), zwei device_ids → count=2, `value=6`→422, DELETE→count sinkt, leeres Set→`avg=null`, POST ohne Token→401. Plus Vollsystem-Regression (alle bestehenden AK-Tests).
- [x] Manuell (http://localhost:8000): Bewertung im Detail-Sheet abgeben → in zweitem Browser-Kontext (anderes `fa_device_id`) Ø + Anzahl sichtbar; `minRating`-Filter prüft eigene Bewertung; localStorage-Migration mit Alt-Daten.

---

### US-116 · Verständliche In-App-Erklärungen für jede Funktion `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done (gemerged in US-21) |
| **Erstellt** | 2026-07-04 |

**Beschreibung:** Als App-User möchte ich jederzeit ohne Verzögerung verstehen, was eine Funktion aussagt, wie sie funktioniert und wie ich sie praktisch anwende, damit ich die App sicher und selbstständig nutzen kann.

**Gemerged in US-21 am 2026-07-05, kein eigenständiger Code, siehe US-21.** US-21 wurde auf das aktuelle Ticket-Format gehoben, um den hier geforderten Scope („jede Funktion" statt nur Scores/Schwierigkeit/Event-Typen, plus „ohne Verzögerung"/Erklärung direkt im Kontext) erweitert und trägt jetzt die vollständige Analyse inkl. Implementierungsoptionen. Dieses Ticket bleibt nur als Herkunftsnachweis stehen, wird nicht separat weiterverfolgt.

**Bezug (Original, zur Nachvollziehbarkeit erhalten):** Deutliche Überschneidung mit **US-21** [ ] („App-Beschreibung & Onboarding" — Onboarding-Slides, „?"-Info-Button, Score-Tooltips, Glossar) sowie **US-55** [x] (Done — Score-Erklärungen via ⓘ-Overlay, aber nur für Astronomie-/Wetter-/Gesamt-Score). US-116 ist breiter gefasst als beide: „jede Funktion" statt nur Scores/Schwierigkeit/Event-Typen, plus die explizite Anforderung „ohne Verzögerung" (also unmittelbar im Kontext, nicht nur über ein zentrales Glossar). Empfehlung zur Klärung mit Stephan: US-21 und US-116 vermutlich **mergen** (US-21 als Kern, US-116 als Scope-Erweiterung „jede Funktion" statt nur die in US-21 genannten Aspekte) — nicht selbst umgebaut, nur vorgeschlagen.

---

### US-117 · Karten-Tab öffnet mit aktuellem Standort + 5-km-Radius `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-05 |

**Beschreibung:** Als Fotograf möchte ich, dass der Karten-Tab beim Öffnen immer meinen aktuellen Standort mit 5 km Radius zeigt, damit ich sofort die relevanten Locations in meiner direkten Umgebung sehe.

**Bezug:** Verwandt, aber nicht identisch mit **BUG-58** [x] (Done, released 2026-07-04 — der Wolken-/Niederschlag-Umschalter im Karten-Tab zoomt neuerdings auf einen **50-km**-Radius um die aktuelle Kartenmitte). BUG-58 betrifft nur das Verhalten beim Umschalten auf Wolken/Niederschlag, nicht den initialen Öffnungszustand des Karten-Tabs selbst, und nutzt einen anderen Radius (50 km statt 5 km). Kein Duplikat, klare Abgrenzung: US-117 = initiales Öffnen des Karten-Tabs mit GPS-Standort, BUG-58 = Zoom-Verhalten beim Wetter-Layer-Umschalten.

---

**Implementation Spec**

**Root Cause / Ist-Zustand (verifiziert am Code, 2026-07-05):**
📎 Code-Verifikation: `web/index.html` gelesen — `MapView.init` (Z. 4514–4522), `MapView.locateMe` (Z. 4664–4695), `App.nav` (Z. 6738–6759), `Filter.requestGps`/`Filter._gps` (Z. 2946–2966), `Locations.load`/`sortByDistance` (Z. 5303–5349), `WeatherMap._localBounds` (Z. 4952–4967).
- Bestätigt: Der Karten-Tab startet **immer** fix auf Berlin-Zentrum (`setView([52.52, 13.40], 10)`), unabhängig vom Nutzerstandort. Kein GPS-Bezug beim Öffnen.
- Bestätigt: Es gibt bereits einen manuellen „Mein Standort"-Button auf der Karte (US-69, `MapView.locateMe()`), der beim Klick per eigenem `navigator.geolocation.getCurrentPosition`-Aufruf auf den GPS-Standort zoomt (Zoom-Stufe 13, kein definierter km-Radius). Dieser Weg ist **komplett unabhängig** vom bestehenden `Filter.requestGps()`/`Filter._gps`-Mechanismus — eigene Fehlerbehandlung, eigenes Caching (keins), kein Toast-Text-Abgleich mit dem Rest der App.
- Bestätigt: `App.nav('map')` ruft bei jedem Tab-Wechsel zur Karte `MapView.init()` auf — aber `init()` hat einen Guard (`if (this.map) return;`). D.h. **nur der allererste** Tab-Wechsel zur Karte in der Session initialisiert sie; jeder weitere Wechsel ist ein No-op, die Leaflet-Karte bleibt exakt im zuletzt aktiven Zustand (Zoom/Pan), inklusive manueller Nutzer-Verschiebungen.
- Bestätigt: `Filter.requestGps()`/`Filter._gps` ist der App-weit etablierte GPS-Mechanismus (genutzt von US-118 Locations-Sortierung, BUG-51 Entfernungsfilter, Kartenmarker-Distanzfilter Z. 2894/4651). Er fragt nur einmal pro Sitzung (cached in `_gps`), zeigt bei Verweigerung/Fehler einen einheitlichen Toast („📍 GPS nicht verfügbar") und wirft keinen Fehler, sondern liefert `true`/`false` zurück.
- Bestätigt: `WeatherMap._localBounds(center)` (BUG-58) ist eine breitengradkorrigierte Radius-Bounds-Funktion, aktuell fest auf 50 km und an das `WeatherMap`-Objekt gebunden — kein generisches, wiederverwendbares Utility. Für einen 5-km-Radius um GPS-Koordinaten (statt um die Kartenmitte) müsste eine eigene, mit Radius parametrisierte Variante existieren; das Muster (Δlat, Δlon mit `cos(lat)`-Korrektur) ist aber 1:1 übertragbar.
- Widerlegt: Es gibt **kein** bestehendes Konzept eines „5-km-Radius" als Zoom-Definition auf der Karte. Der einzige bestehende km-Radius-Begriff auf der Karte ist BUG-58 mit 50 km und dient einem anderen Zweck (Wetter-Mosaik-Sichtbarkeit, nicht initialer Standort-Fokus).

**Scope:**
- Eingeschlossen: Beim **erstmaligen** Öffnen des Karten-Tabs in einer Session (erster `App.nav('map')`-Aufruf, `MapView.map` existiert noch nicht) wird der GPS-Standort angefragt (über den bestehenden `Filter.requestGps()`-Mechanismus, nicht über eine neue Parallel-Implementierung) und die Karte auf ein Sichtfeld zentriert, das einem 5-km-Radius um diesen Standort entspricht.
- Eingeschlossen: Web-App (`web/index.html`) — reines Frontend-Verhalten, keine Backend-Änderung.
- Ausgeschlossen: BUG-58 (50-km-Radius-Zoom beim Wetter-Layer-Umschalten) — bleibt unverändert, eigener Codepfad (`WeatherMap.setMode`/`_localBounds`).
- Ausgeschlossen (offen, siehe Fragen unten): Verhalten bei jedem weiteren Tab-Wechsel zur Karte (nicht nur beim allerersten), Verhalten bei verweigerter/fehlender GPS-Berechtigung, Verhältnis zum bestehenden „Mein Standort"-Button (US-69).
- Ausgeschlossen: iOS-App — Ticket bezieht sich nur auf den Web-Karten-Tab (kein Hinweis im Ticket auf iOS-Pendant, `ios/FotoAlert/` nicht Teil dieser Analyse).

**Entscheidungen von Stephan (2026-07-05, Weg-Gate):**
1. **GPS verweigert/nicht erteilt:** Fallback auf den letzten bekannten Standort (falls z. B. aus dem Locations-Tab oder einer früheren Anfrage schon ein GPS-Punkt bekannt ist). Ist gar kein Standort bekannt, bleibt es beim bisherigen Berlin-Fallback.
2. **Bedeutung „5-km-Radius":** Exakt berechnet — dynamische Bounding-Box analog zum BUG-58-Muster (`_localBounds`, breitengradkorrigiert, per `fitBounds`), nicht nur ein fixer Zoom-Level.
3. **Zeitpunkt:** Nur beim allerersten Öffnen der Session — der bestehende `init()`-Guard bleibt wie er ist, kein Zurückspringen bei späteren Tab-Wechseln, auch wenn der Nutzer zwischendurch manuell woanders hingezoomt hatte.
4. **„Mein Standort"-Button (US-69):** Bleibt unangetastet — keine Konsolidierung in diesem Ticket, verhindert Scope Creep.

→ **Gewählte Implementierung: Option A** (siehe unten).

**Akzeptanzkriterien (final):**
- [x] Öffne ich den Karten-Tab zum ersten Mal in einer Sitzung und erlaube GPS-Zugriff, zeigt die Karte sofort meinen aktuellen Standort in der Mitte, mit einem Ausschnitt, der einem 5-km-Radius um mich herum entspricht (nicht mehr Berlin-Zentrum).
- [x] Edge Case: Verweigere ich beim ersten Kartenöffnen den GPS-Zugriff, aber es ist bereits ein GPS-Standort aus einer früheren Anfrage bekannt (z. B. vom Locations-Tab) → Karte zentriert auf diesen zuletzt bekannten Standort mit 5-km-Ausschnitt.
- [x] Edge Case: Kein GPS-Zugriff möglich UND kein früherer Standort bekannt → Karte zeigt wie bisher die Berlin-Ansicht, kein Fehler, kein Absturz.
- [x] Edge Case: Ich wechsle vom Karten-Tab weg und wieder zurück, ohne manuell etwas an der Karte verändert zu haben → Karte zeigt weiterhin denselben GPS-5-km-Ausschnitt (kein ungewollter Sprung).
- [x] Edge Case: Ich habe nach dem ersten Öffnen manuell woanders hingezoomt/gescrollt, wechsle den Tab und komme zurück → Ausschnitt bleibt wie von mir manuell gewählt (kein Zurückspringen auf GPS+5km bei weiteren Tab-Wechseln).
- [x] Regression: Der „Mein Standort"-Button (US-69) funktioniert weiterhin unverändert wie bisher.
- [x] Regression: BUG-58 (50-km-Zoom beim Wetter-Layer-Umschalten) bleibt unverändert funktionsfähig, unabhängig vom neuen initialen 5-km-Verhalten.

**Pre-Mortem:**
- 💀 Szenario: Der neue GPS-Zentrierungs-Code läuft bei **jedem** `App.nav('map')`-Aufruf statt nur beim ersten, weil der bestehende `init()`-Guard umgangen/entfernt wird → Karte springt dem Nutzer bei jedem Tab-Wechsel unter dem manuell gewählten Ausschnitt weg. → Auslöser: Frage 3 nicht geklärt, Guard-Logik falsch angefasst. → Gegenmaßnahme: Guard-Verhalten explizit in AK verankern (Edge Cases oben), Implementierung so bauen, dass der GPS-Zentrierungscode nur im „echten" Erstinitialisierungspfad läuft (dort wo aktuell `setView([52.52,13.40],10)` steht), nicht in `App.nav`.
- 💀 Szenario: GPS-Anfrage blockiert das Öffnen des Karten-Tabs spürbar (Ladeverzögerung), weil `await Filter.requestGps()` vor dem ersten Rendern der Karte steht und der Browser-Berechtigungsdialog den Hauptthread/die UI blockiert wahrnehmbar verzögert. → Auslöser: Synchrones Warten auf GPS-Antwort vor `L.map(...)`. → Gegenmaßnahme: Karte sofort mit vorläufiger Ansicht (z.B. letzte bekannte oder Fallback) rendern, GPS-Zentrierung asynchron nachziehen sobald `requestGps()` auflöst (Pattern existiert schon in `Locations.load()` — Rendern läuft nach `await`, hier müsste stattdessen ein Zwei-Phasen-Ansatz geprüft werden: erst Karte mit Fallback zeigen, dann per `setView`/`fitBounds` nachjustieren, sobald GPS da ist). Getrennt von Nutzer-Wahrnehmung testen (spürt sich Ladezeit an wie vorher?).
- 💀 Szenario: Zwei parallele, aber unterschiedliche GPS-Zugriffe (`Filter.requestGps()` für diesen Zentrierungs-Fall, `MapView.locateMe()` für den bestehenden Button) fragen den Browser nacheinander unabhängig nach Standort → doppelter Berechtigungsdialog oder inkonsistentes Verhalten (einer nutzt gecachtes `_gps`, der andere fragt immer neu). → Auslöser: Frage 4 nicht geklärt, keine Konsolidierung. → Gegenmaßnahme: mindestens sicherstellen, dass der neue Code `Filter.requestGps()`/`Filter._gps` wiederverwendet (kein dritter, neuer `navigator.geolocation`-Aufruf), damit das gecachte Ergebnis geteilt wird und kein zweiter Dialog erscheint, falls der Nutzer vorher schon (z.B. im Locations-Tab) GPS erlaubt hatte.
- 💀 Szenario: 5-km-Radius als fixer Zoom-Level (statt `fitBounds`) sieht bei extremen Breitengraden (z.B. Norwegen) optisch anders aus als in Berlin, weil ein fixer Leaflet-Zoom keine reale km-Entsprechung hat (BUG-58-Lehre). → Auslöser: Frage 2 mit „fixer Zoom" statt „dynamische Bounding-Box" beantwortet. → Gegenmaßnahme: bei Bestätigung von „dynamischer Radius" das `_localBounds`-Muster (breitengradkorrigiert) wiederverwenden/generisch mit Radius-Parameter extrahieren statt eine zweite feste Zoom-Zahl zu hardcoden.
- 💀 Szenario: Kein Marker/keine Locations sichtbar im 5-km-Ausschnitt (Nutzer wohnt weit außerhalb der erfassten Locations), Karte wirkt nach dem Öffnen „leer". → Auslöser: 5-km-Radius ist klein, `Locations`-Datensatz ist ortsgebunden (aktuell primär Berlin/Brandenburg). → Gegenmaßnahme: kein Blocker für dieses Ticket (Ticket verlangt explizit den engen Radius), aber als bekanntes UX-Verhalten im Test protokollieren, nicht als Bug werten.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (Annahmen-Protokoll ergab 4 🔴-kritische Fragen, s.o. — Rules/Examples final erst nach Antworten formulierbar)
- [x] Pre-Mortem durchgeführt (5 Szenarien, Gegenmaßnahmen s.o.)
- [x] Architektur analysiert: `web/index.html` — `MapView.init` (Startansicht), `MapView.locateMe` (bestehender manueller GPS-Button, US-69), `App.nav` (Tab-Wechsel-Guard), `Filter.requestGps`/`Filter._gps` (wiederverwendbarer GPS-Mechanismus aus US-118/BUG-51), `WeatherMap._localBounds` (Radius-Bounds-Muster aus BUG-58)
- [x] Designer-Check: nicht visuell im Sinne von Farbe/Layout (kein neues UI-Element, keine Farb-/Größenänderung) — betrifft nur Kartenausschnitt/Zoom beim Öffnen. Kein `fotoalert-designer`-Aufruf nötig.
- [x] Implementierungsoptionen: A / B (siehe unten) — Stephan hat Option A gewählt (2026-07-05)
- [x] Empfehlung: Option A (dynamische Bounding-Box analog BUG-58-Muster) — bestätigt

**Implementierungsoptionen:**

### Option A — Standort + 5-km-Ausschnitt über wiederverwendetes Radius-Bounds-Muster (`fitBounds`)
- App-Wirkung: Beim ersten Öffnen der Karte sieht Stephan sofort seinen eigenen Standort in der Mitte, mit einem Ausschnitt, der überall auf der Welt gleich „nah" wirkt (5 km in jede Richtung) — unabhängig davon, ob er in Berlin oder z.B. in Norwegen fotografiert.
- Vorgehen: Beim allerersten Karten-Öffnen `Filter.requestGps()` awaiten (denselben Mechanismus wie Locations-Tab/US-118 nutzen, kein neuer GPS-Aufruf). Bei Erfolg: Karte mit einer auf 5 km parametrisierten, breitengradkorrigierten Bounding-Box zentrieren (Muster aus `WeatherMap._localBounds` generisch mit Radius-Parameter, z.B. als eigenständige Hilfsfunktion, die von beiden Stellen genutzt werden kann). Bei Fehlschlag: Fallback gemäß Antwort auf Frage 1.
- Betroffene Dateien: `web/index.html` (`MapView.init`, ggf. neue kleine gemeinsame Bounds-Hilfsfunktion referenziert von `MapView` und `WeatherMap`).
- Vorteile: Exakte, überall gleich wirkende 5-km-Ansicht; nutzt bestehenden GPS-Mechanismus (kein doppelter Berechtigungsdialog, konsistentes Fehlerverhalten/Toast); Muster bereits im Code etabliert und getestet (BUG-58).
- Nachteile / Risiken: Etwas mehr Umbauaufwand, da `init()` aktuell synchron/einfach ist und async gemacht werden muss (ist es durch `try { await this.loadMarkers(); }` bereits teilweise); Pre-Mortem-Szenario „Ladeverzögerung" muss beachtet werden (Karte ggf. erst mit Fallback zeigen, dann nachjustieren).
- Aufwand: klein–mittel.

### Option B — Fixer Zoom-Level auf GPS-Koordinate (kein `fitBounds`)
- App-Wirkung: Beim ersten Öffnen zentriert die Karte auf den eigenen Standort, aber mit einer festen Zoom-Stufe (z.B. Zoom 13, wie beim bestehenden „Mein Standort"-Button) statt einer exakt berechneten 5-km-Fläche.
- Vorgehen: `Filter.requestGps()` awaiten, dann `this.map.setView([gps.lat, gps.lon], ZOOM)` mit einer fest gewählten Zoom-Zahl, die bei einem Standard-Breitengrad ungefähr 5 km Sichtfeld ergibt.
- Betroffene Dateien: `web/index.html` (`MapView.init`).
- Vorteile: Einfachster Eingriff, kleinster Aufwand, kein neues Bounds-Utility nötig.
- Nachteile / Risiken: Nicht wirklich „5 km" — ein fixer Zoom-Level zeigt je nach Bildschirmgröße und Breitengrad einen unterschiedlich großen realen Radius (BUG-58-Lehre: bei nördlichen Standorten wirkt ein Kartenausschnitt bei gleichem Zoom größer/kleiner). Würde die im Ticket explizit genannte „5 km"-Angabe nur ungefähr erfüllen.
- Aufwand: klein.

✅ Empfehlung: **Option A** — das Ticket nennt explizit einen Radius („5 km"), nicht einen Zoom-Level; ein `fitBounds`-Ansatz erfüllt das exakt und wiederverwendet ein bereits im Code etabliertes, getestetes Muster (BUG-58). Der Mehraufwand gegenüber Option B ist gering, da die Kernlogik (Bounds-Berechnung) schon existiert und nur generisch parametrisiert werden muss. Voraussetzung: Frage 2 wird mit „dynamische Bounding-Box" beantwortet — falls Stephan stattdessen bewusst einen einfachen fixen Zoom will, wird Option B gewählt.

**Testplan:**
- [ ] Automatisiert (Harness): Kartenzoom/-zentrierung ist reines Leaflet-/Browser-Frontend-Verhalten (wie bei BUG-55/BUG-58), nicht über `pytest`/`backend/tests/` abdeckbar. Kein Backend-Test nötig, da keine Backend-Änderung.
- [ ] Manuell (unter http://localhost:8000):
  1. Karten-Tab zum ersten Mal in einer neuen Sitzung öffnen, GPS-Zugriff erlauben → Erwartung: Karte zentriert sofort auf eigenen Standort, Ausschnitt entspricht ca. 5 km Radius (nicht mehr Berlin-Fixansicht).
  2. GPS-Zugriff beim ersten Öffnen verweigern, aber vorher schon einmal (z. B. im Locations-Tab) ein GPS-Standort ermittelt → Erwartung: Karte zentriert auf diesen zuletzt bekannten Standort mit 5-km-Ausschnitt.
  3. GPS-Zugriff verweigern UND kein früherer Standort bekannt (ganz frische Sitzung) → Erwartung: Karte zeigt wie bisher Berlin.
  4. Tab wechseln (z.B. zu Feed) und zurück zur Karte, ohne manuell etwas verändert zu haben → Erwartung: gleicher GPS-Ausschnitt wie beim ersten Öffnen (kein Sprung).
  5. Nach dem ersten Öffnen manuell an einen anderen Ort zoomen/scrollen, Tab wechseln und zurückkehren → Erwartung: Ausschnitt bleibt wie manuell gewählt (kein Zurückspringen).
  6. „Mein Standort"-Button (US-69) danach testen → Erwartung: weiterhin funktionsfähig (Regression).
  7. Wetter-Layer (Wolken/Niederschlag) einschalten → Erwartung: weiterhin 50-km-Zoom wie bei BUG-58 (Regression, unabhängiger Codepfad).
  8. Regression (PRODUCT.md §12, Karten-/CSS-Bereich): Marker, Layer-Umschaltung (Nacht/Standard/Satellit), Filter-Anwendung auf Kartenmarker weiterhin funktionsfähig.

---

### US-118 · Location-Übersicht nach Entfernung vom Standort sortieren `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-04 |

**Beschreibung:** Als Fotograf möchte ich, dass die Location-Übersicht aufsteigend nach Entfernung vom aktuellen Standort sortiert ist (nicht vom Motiv), damit die nächstgelegenen Spots automatisch oben stehen.

**Bezug:** Verwandt zu **BUG-51** [x] (Done, released 2026-06-29 — Entfernungsfilter im Locations-Tab funktioniert, filtert aber nur nach Radius, sortiert nicht). Kein Duplikat: BUG-51 behandelt Filterung (ein-/ausblenden), US-118 behandelt Sortierreihenfolge der sichtbaren Liste. Beide können nebeneinander bestehen (gefiltert UND sortiert).

---

#### Analyse (US-118)

**Datum:** 2026-07-04

📎 **Code-Verifikation:** `web/index.html` gelesen.
- `Locations.render(locs)` (Zeile 5225–5254) übernimmt die Reihenfolge des übergebenen Arrays unverändert — es gibt aktuell **keine Sortierung**, weder nach Entfernung noch nach etwas anderem. Die Liste erscheint in der Reihenfolge, in der `/locations` sie liefert (Datenbank-/Einfügereihenfolge).
- `Filter.applyToLocations(locs)` (Zeile 2764–2795) filtert nur (Schwierigkeit, Kategorie, Bewertung, Verifikation, Score, seit BUG-51 auch Entfernungsradius) — verändert die Reihenfolge der verbleibenden Einträge nicht.
- Location-Objekte besitzen **kein** `distance_m`-Feld von sich aus (anders als manche Event-Objekte in Feed/Kalender/Scout). Sie haben aber `observer_lat`/`observer_lon` (Fotografen-Standpunkt) — dieselben Felder, die BUG-51 bereits für die Radius-Filterung nutzt.
- `haversineKm(lat1, lon1, lat2, lon2)` (Zeile 2576–2583) ist die vorhandene, wiederverwendbare Distanzfunktion — bereits an drei Stellen im Filter-Code im Einsatz (Map, Locations-Filter, Scout).
- `Filter._gps` (gesetzt über `Filter.requestGps()`, Zeile 2841–2861) enthält den aktuellen GPS-Standort des Nutzers, aber **nur wenn vorher ein Entfernungsfilter aktiv war** — `Locations.load()` (Zeile 5200–5204) und `Locations.filter()` (Zeile 5212–5224) fragen GPS bislang nur an, wenn `Filter.state.maxDistKm > 0`. Für eine Sortierung nach Entfernung wäre GPS **immer** nötig, unabhängig vom Filterzustand — das ist eine Erweiterung des bestehenden GPS-Anfrage-Pfads.
- Bestätigt aus BUG-51: „Standort" = GPS-Standort des Nutzers (`observer_lat`/`observer_lon` als Ziel), **nicht** der Motiv-Standort (`subject_lat`/`subject_lon`). Deckt sich mit der Ticket-Formulierung „nicht vom Motiv".

---

##### Example Mapping

**Scope-Check:** Kein Slice-Signal — das Ticket bezieht sich eindeutig auf die gesamte Location-Übersicht (Locations-Tab-Liste), keine Typ-Einschränkung erkennbar.

**Annahmen-Protokoll:**

| # | Punkt | Typ | Entscheidung |
|---|-------|-----|--------------|
| 1 | GPS-Anfrage beim Öffnen des Locations-Tabs, auch wenn kein Entfernungsfilter aktiv ist | 🔴 funktional kritisch | ❓ Frage 1 |
| 2 | Verhalten wenn GPS verweigert/nicht verfügbar ist | 🔴 funktional kritisch | ❓ Frage 2 |
| 3 | Sortierung wirkt auch während/nach Textsuche im Locations-Tab | ⚪ konventionell | ⚠️ Annahme: Sortierung bleibt bei Textsuche aktiv (Suche filtert nur zusätzlich, ändert Reihenfolge nicht) |
| 4 | Live-Nachsortierung wenn sich der GPS-Standort während der Nutzung ändert (Nutzer bewegt sich) | ⚪ konventionell | ⚠️ Annahme: Sortierung erfolgt einmalig beim Laden/Öffnen des Tabs, kein Live-Re-Sort bei GPS-Drift (identisches Verhalten zu bestehendem Entfernungsfilter, der auch nicht live nachsortiert) |
| 5 | Verhalten der Karte (Map-Tab) — wird dort auch sortiert? | ⚪ konventionell | ⚠️ Annahme: Ticket bezieht sich nur auf die Listen-Übersicht (Locations-Tab), nicht auf die Kartenansicht — eine Karte hat keine "Reihenfolge" im UI-Sinn |

**❓ Frage 1 (an Stephan):** Soll die App beim ersten Öffnen des Locations-Tabs automatisch nach dem Standort fragen (GPS-Dialog), auch wenn noch kein Entfernungsfilter gesetzt ist — damit sofort nach Entfernung sortiert werden kann? Oder soll die Sortierung erst greifen, sobald der Standort aus einem anderen Grund (z.B. Entfernungsfilter oder Kartenbesuch) bereits bekannt ist, und vorher bei der bisherigen (unsortierten) Reihenfolge bleiben?

**❓ Frage 2 (an Stephan):** Wenn GPS-Zugriff verweigert wird oder nicht verfügbar ist — soll die Liste dann (a) in der bisherigen unsortierten Reihenfolge bleiben (wie heute, kein Fehler, kein Hinweis), oder (b) ein Hinweis/Toast erscheinen, dass ohne Standort nicht nach Entfernung sortiert werden kann (analog zum bestehenden „GPS nicht verfügbar"-Toast aus BUG-51)?

**📏 Rule 1 — Aufsteigende Sortierung nach Entfernung zum Nutzerstandort**
Sobald der GPS-Standort des Nutzers bekannt ist, wird die Location-Liste im Locations-Tab aufsteigend nach Entfernung vom Nutzerstandort zum Fotografen-Standpunkt (`observer_lat`/`observer_lon`) jeder Location sortiert — nicht nach Entfernung zum Motiv.

🟢 Beispiel: Stephan steht in Berlin-Mitte. Die Location-Liste zeigt einen Spot in Charlottenburg (6 km) vor einem Spot in Potsdam (25 km) — unabhängig davon, wo sich das jeweilige Fotomotiv befindet.

🟢 Beispiel: Zwei Locations haben denselben Fotografen-Standpunkt (gleiches Gebäude, zwei Motive) → beide erscheinen mit identischer Entfernung direkt hintereinander (Reihenfolge zwischen ihnen beliebig/stabil).

**📏 Rule 2 — Sortierung wirkt zusätzlich zu bestehenden Filtern**
Die Sortierung verändert nur die Reihenfolge der sichtbaren Liste, nicht welche Locations sichtbar sind. Aktive Filter (Schwierigkeit, Kategorie, Bewertung, Verifikation, Entfernungsradius aus BUG-51, Textsuche) wirken wie bisher; die gefilterte Teilmenge wird zusätzlich nach Entfernung sortiert.

🟢 Beispiel: Stephan hat den Entfernungsfilter auf „< 15 km" gesetzt (BUG-51). Von den verbleibenden Locations innerhalb 15 km erscheint die nächstgelegene zuerst, die am weitesten entfernte (aber noch < 15 km) zuletzt.

**📏 Rule 3 — Verhalten ohne bekannten Standort (⚠️ Annahme-abhängig, siehe Frage 1/2)**
Ist der GPS-Standort nicht bekannt oder nicht verfügbar, bleibt die Liste in der bisherigen (unsortierten, server-gelieferten) Reihenfolge — die App zeigt keinen Fehlerzustand, sondern degradiert auf das heutige Verhalten.

🟢 Beispiel: Stephan verweigert die Standortfreigabe → Locations-Liste erscheint wie vor diesem Ticket, ohne Absturz oder leere Liste.

---

##### Akzeptanzkriterien

- [x] Wenn der Standort des Nutzers bekannt ist, zeigt die Location-Übersicht die nächstgelegene Location ganz oben und die am weitesten entfernte ganz unten (aufsteigend sortiert).
- [x] Die Entfernung wird immer zum aktuellen Standort des Nutzers gemessen, nicht zum Motiv der jeweiligen Location.
- [x] Ist zusätzlich ein Entfernungsfilter oder ein anderer Filter (Schwierigkeit, Kategorie, Bewertung, Verifikation) aktiv, bleibt die gefilterte Liste weiterhin nach Entfernung sortiert.
- [x] Bei einer Textsuche im Locations-Tab bleiben die Suchtreffer weiterhin nach Entfernung sortiert.
- [x] Edge Case: Ist der Standort nicht bekannt oder wurde die Standortfreigabe verweigert, wird die Liste trotzdem angezeigt (keine leere Liste, kein Absturz) — Reihenfolge dann wie bisher.
- [x] Edge Case: Zwei Locations mit identischer Entfernung werden beide angezeigt, keine geht durch die Sortierung verloren.
- [x] Regression: Karten-Tab, Feed und Scout zeigen weiterhin ihr bisheriges (nicht durch dieses Ticket verändertes) Sortierverhalten.

---

##### Pre-Mortem

💀 **Szenario 1: Sortierung wirkt nur, wenn vorher zufällig schon ein Entfernungsfilter oder Kartenbesuch stattfand**
Auslöser: `Filter._gps` wird aktuell nur gefüllt, wenn `maxDistKm > 0` beim Laden des Locations-Tabs ist (Zeile 5202/5214). Ohne diese Erweiterung bliebe `Filter._gps` beim reinen Öffnen des Locations-Tabs `null` → keine Sortierung, obwohl das Ticket es verlangt.
Frühwarnung: Frischer App-Start, Locations-Tab direkt geöffnet (kein Filter gesetzt, keine Karte besucht) → Liste bleibt unsortiert.
Gegenmaßnahme: GPS-Request in `Locations.load()`/`Locations.filter()` von der Bedingung `maxDistKm > 0` lösen bzw. zusätzlich für die Sortierung unabhängig anfragen (siehe Frage 1) — als eigenes AK/Testfall verankert.

💀 **Szenario 2: GPS-Dialog erscheint jetzt an einer Stelle, wo der Nutzer ihn vorher nicht kannte**
Auslöser: Wird GPS beim bloßen Öffnen des Locations-Tabs angefragt (Antwort auf Frage 1 = ja), poppt der Browser-Berechtigungsdialog künftig früher/häufiger auf als heute — potenziell irritierend, wenn der Nutzer nur schauen wollte.
Frühwarnung: Nutzerfeedback „warum fragt die App jetzt schon wieder nach meinem Standort".
Gegenmaßnahme: BUG-52 („GPS nur einmal pro Session") bleibt in Kraft — der Dialog erscheint dann nur einmal, nicht bei jedem Tab-Wechsel. Zusätzlich in der Test-/Freigabe-Runde explizit gegenprüfen, dass kein Mehrfach-Dialog auftritt.

💀 **Szenario 3: Sortierung bricht bei fehlenden Koordinaten (observer_lat/lon = null/0)**
Auslöser: Falls eine Location fehlerhafte oder fehlende `observer_lat`/`observer_lon`-Werte hat, liefert `haversineKm()` einen NaN- oder Fantasiewert, der die Location an eine unerwartete Position in der sortierten Liste schiebt (z.B. ganz oben durch NaN-Vergleichslogik).
Frühwarnung: Eine offensichtlich weit entfernte oder falsch platzierte Location erscheint plötzlich ganz oben in der Liste.
Gegenmaßnahme: Sortierfunktion so schreiben, dass Locations mit fehlenden/ungültigen Koordinaten ans Ende der Liste fallen (nicht NaN unsortiert vergleichen) — als Edge-Case-Test aufnehmen.

💀 **Szenario 4: Performance-/Re-Render-Kosten bei jedem Filter- oder Suchaufruf**
Auslöser: Die Sortierung müsste bei jedem `Locations.render()`-Aufruf (Filter ändern, Suche tippen) neu berechnet werden — bei vielen Locations theoretisch spürbar, in der Praxis bei der aktuellen Location-Anzahl (siehe `/locations`, üblicherweise niedrige zweistellige Zahl) vernachlässigbar.
Frühwarnung: Spürbares Ruckeln beim Tippen im Suchfeld.
Gegenmaßnahme: Kein Vorab-Fix nötig, da Datenmenge klein; im manuellen Test kurz gegenprüfen, dass Tippen im Suchfeld weiterhin flüssig reagiert.

💀 **Szenario 5: Vermischung mit BUG-51-Filterlogik führt zu Regressionsfehler in `applyToLocations`**
Auslöser: Wird die Sortierung direkt in `applyToLocations()` eingebaut (die auch filtert), könnte ein Fehler dort gleichzeitig Filterung und Sortierung kaputt machen.
Frühwarnung: Nach der Änderung filtert der Entfernungsradius plötzlich nicht mehr korrekt (Regression von BUG-51).
Gegenmaßnahme: Sortierung als eigener, nachgelagerter Schritt nach dem Filtern implementieren (z.B. eigene Funktion `sortByDistance()`, aufgerufen nach `applyToLocations()`), nicht in die bestehende Filterlogik hineinmischen — reduziert Regressionsrisiko und hält BUG-51 unangetastet.

---

##### Architektur-Analyse

**Betroffene Datei:** ausschließlich `web/index.html` (Frontend, keine Backend-Änderung nötig — Locations werden clientseitig sortiert, analog zur clientseitigen Entfernungsfilterung aus BUG-51).

**Betroffene Stellen:**
- `Locations.load()` (Zeile 5200–5204) — lädt Locations, ruft aktuell GPS nur bei aktivem Radiusfilter an.
- `Locations.filter(q)` (Zeile 5212–5224) — kombiniert Filter + Textsuche, ruft ebenfalls nur bedingt GPS an.
- `Locations.render(locs)` (Zeile 5225–5254) — reine Darstellungsfunktion, keine Sortierung enthalten.
- `Filter.applyToLocations(locs)` (Zeile 2764–2795) — reine Filterfunktion, Reihenfolge unverändert.
- `haversineKm()` (Zeile 2576–2583) — bestehende Distanzfunktion, wiederverwendbar.
- `Filter._gps` / `Filter.requestGps()` (Zeile 2614, 2841–2861) — bestehender GPS-State, muss ggf. unabhängig vom Radiusfilter angefragt werden.

**Designer-Check:** Keine visuell neuen Elemente (kein neuer Chip, keine neue Farbe, kein neues Icon) — nur eine veränderte Reihenfolge bestehender Karten. `fotoalert-designer` daher nicht erforderlich.

**Daten-Validierung:** Location-Objekte aus `/locations` enthalten `observer_lat`/`observer_lon` (bereits von BUG-51 bestätigt), aber kein vorgefertigtes `distance_m` — die Entfernung muss wie bei BUG-51 clientseitig per `haversineKm()` berechnet werden, nicht vom Server geliefert.

---

##### Implementierungsoptionen

**Option A — Eigenständige Sortierfunktion nach `applyToLocations()`, GPS-Anfrage von Filterbedingung entkoppeln**
- Was bedeutet das für Stephan: Die Location-Liste ist ab dem ersten Öffnen des Locations-Tabs nach Entfernung sortiert — unabhängig davon, ob vorher ein Entfernungsfilter gesetzt wurde. Der Standort-Dialog erscheint ggf. etwas früher (einmalig pro Sitzung, dank BUG-52).
- Vorgehen: Neue Funktion `sortByDistance(locs)`, die nach `Filter.applyToLocations()` aufgerufen wird, sortiert per `haversineKm()` gegen `Filter._gps`. GPS-Anfrage in `Locations.load()`/`filter()` wird unabhängig vom `maxDistKm`-Zustand ausgelöst (immer anfragen, nicht nur wenn Filter aktiv).
- Betroffene Dateien: `web/index.html` — `Locations.load()`, `Locations.filter()`, neue Hilfsfunktion, Aufruf in `Locations.render()`-Kette.
- Vorteile: Sortierung greift zuverlässig bei jedem Einstieg in den Locations-Tab; sauber getrennt von der Filterlogik (kein Regressionsrisiko für BUG-51); Standort-Erlebnis konsistent mit der User Story („automatisch sofort sortiert").
- Nachteile/Risiken: GPS-Dialog kann jetzt auch ohne Filterinteraktion erscheinen (Szenario 2) — muss im Test gegen Mehrfach-Dialog geprüft werden.
- Aufwand: klein (rund 10–15 Zeilen: 1 Sortierfunktion + 2 angepasste GPS-Aufrufstellen).

**Option B — Sortierung nur, wenn Standort aus anderem Grund bereits bekannt ist (kein zusätzlicher GPS-Request)**
- Was bedeutet das für Stephan: Ist der Standort schon bekannt (weil z.B. vorher die Karte besucht oder ein Entfernungsfilter gesetzt wurde), sortiert die Liste automatisch. Ohne bekannten Standort bleibt die bisherige Reihenfolge — kein zusätzlicher Standort-Dialog wird ausgelöst.
- Vorgehen: Gleiche Sortierfunktion wie Option A, aber **kein** unabhängiger GPS-Request — Sortierung nutzt nur `Filter._gps`, falls bereits vorhanden.
- Betroffene Dateien: `web/index.html` — nur neue Sortierfunktion + Aufruf, keine Änderung an den GPS-Anfragestellen.
- Vorteile: Kein zusätzlicher/früherer GPS-Dialog; minimalinvasiv.
- Nachteile/Risiken: Erfüllt die User Story nicht zuverlässig — bei einem frischen App-Start ohne vorherigen Filter/Kartenbesuch bleibt die Liste unsortiert, obwohl der Fotograf laut Story „automatisch sofort" die nächsten Spots oben sehen möchte. Widerspricht Rule 1 in den meisten Alltagsfällen.
- Aufwand: klein (rund 5 Zeilen).

✅ **Empfehlung: Option A** — nur Option A erfüllt die User Story zuverlässig („automatisch sortiert, ohne manuelles Zutun"); Option B würde in der Praxis meist gar nicht greifen, weil der Locations-Tab oft der erste Einstiegspunkt ist. Das einzige Mehr an Aufwand ist eine unabhängige GPS-Anfrage, die dank BUG-52 (Standort bleibt pro Sitzung gemerkt) nur einmal pro Sitzung sichtbar wird. Voraussetzung: Stephans Antwort auf Frage 1/2 bestätigt diese Richtung — falls Stephan den früheren GPS-Dialog nicht möchte, ist Option B die Alternative.

---

##### Testplan

**Automatisiert:** Kein Backend-Test nötig — reine Frontend-Sortierlogik (analog BUG-51, keine Python-Abbildung vorhanden).

**Manuell (Browser unter http://localhost:8000):**
1. App frisch öffnen (neue Sitzung, kein vorheriger Filter/Kartenbesuch) → Locations-Tab öffnen → Standort-Dialog erlauben → Liste zeigt nächstgelegene Location oben, am weitesten entfernte unten.
2. Entfernungsfilter zusätzlich auf „< 15 km" setzen → verbleibende Locations bleiben nach Entfernung sortiert (nächste zuerst).
3. Im Suchfeld einen Teilbegriff eingeben (z.B. „Schloss") → Treffer bleiben nach Entfernung sortiert.
4. Standortfreigabe verweigern (oder Browser-Standort deaktivieren) → Liste erscheint weiterhin vollständig, in der bisherigen (unsortierten) Reihenfolge, kein Absturz.
5. Tab wechseln (Feed → Karte → Locations mehrfach) → Standort-Dialog erscheint nur beim allerersten Mal (BUG-52-Regression prüfen).
6. Karten-Tab, Feed und Scout gegenprüfen: unverändertes Verhalten (keine neue Sortierung dort, keine Regression aus BUG-51-Filterung).

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2 offene Fragen an Stephan, siehe oben)
- [x] Pre-Mortem durchgeführt (5 Szenarien)
- [x] Architektur analysiert: `web/index.html` — `Locations.load/filter/render`, `Filter.applyToLocations`, `haversineKm`, `Filter._gps/requestGps`
- [x] Designer-Check: nicht visuell verändernd → übersprungen
- [x] Implementierungsoptionen: A (unabhängiger GPS-Request, empfohlen) / B (nur sortieren wenn GPS zufällig schon bekannt)
- [x] Empfehlung: Option A (vorbehaltlich Antwort auf Frage 1/2)

---

### US-119 · Feed-Standardfilter: nur Chancen mit Wahrscheinlichkeit ≥70% `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-04 |

**Beschreibung:** Als Fotograf möchte ich im Feed standardmäßig nur Chancen mit Wahrscheinlichkeit ≥70% sehen, damit ich nicht von unwahrscheinlichen Chancen überflutet werde; reduziere ich den Wahrscheinlichkeits-Filter manuell, sollen auch niedrigere Wahrscheinlichkeiten wieder sichtbar werden.

**Bezug:** Der „Mindest-Wahrscheinlichkeit"-Filter (Slider, Teil des Filter-Systems aus **US-32** [x]/US-18-20/27, siehe auch **BUG-08** [x] Done) existiert bereits, aktueller Standardwert laut Code-Referenzen im Backlog ist **0,35** (35%), nicht 70%. Dieses Ticket ändert vermutlich nur den Default-Wert des bestehenden Sliders (bzw. bestätigt/dokumentiert das Reduzier-Verhalten), kein neuer Mechanismus. Kein Duplikat — reine Wertänderung eines bestehenden Features. Abgrenzung zu prüfen: ob 70% als Feed-Default separat vom Locations-/Karten-Filter-Default gilt.

## Spec

**📎 Code-Verifikation (2026-07-04):** `web/index.html` gelesen.
- Es gibt **zwei unterschiedliche „Score"-Werte**, die im Ticket-Bezugstext vermischt wurden:
  1. `CFG.minScore = 0.35` (Zeile 1277) — ein **fixer Server-Abfragewert**. Er steuert nur, welche Chancen überhaupt vom Server geladen werden (`/opportunities?min_score=${CFG.minScore}`, Zeile 1626). Kommentar im Code: *„Backend-Minimum; wird nicht mehr per Settings-Slider geändert"*. Das ist **nicht** der Slider, den der Fotograf im Filter-Sheet sieht.
  2. Der sichtbare **Wahrscheinlichkeits-Slider** im Filter-Sheet (`Filter._defaults()`, Zeile 2566: `minScore: 0`) — das ist der tatsächliche Ein-/Ausblende-Filter. Sein Standardwert ist aktuell **0 % ("Alle")**, nicht 35 % wie im Ticket-Bezugstext vermutet. Die 35 % aus dem Bezugstext beziehen sich auf den unter Punkt 1 genannten, komplett anderen Wert.
- Der Slider wird angewendet in `Filter.apply()` (Zeile 2669: `if (s.minScore > 0 && o.overall_score < s.minScore / 100) return false;`) und wirkt dadurch sowohl im **Feed** (Zeile 1689) als auch im **Kalender** (Zeile 2065, dort wird nur `skipCloudMood` übersteuert, `minScore` nicht ausgenommen).
- Im **Locations-Tab und auf der Karte** ist der Slider im UI sichtbar ausgegraut/deaktiviert (`isMapView || isLocationView`, Zeile 3155–3164, Hinweistext „Nur im Chancen-Feed verfügbar"), wird aber technisch trotzdem über `applyToLocations()` (Zeile 2729–2733) angewendet, sofern Feed-Daten bereits geladen sind — eine Location ohne ausreichend wahrscheinliche Chance wird dort ausgeblendet.
- Der Filter-Zustand wird komplett in `localStorage` unter dem Schlüssel `fotoalert_filters` persistiert (`Filter._KEY`, Zeile 2556) und beim App-Start über `Object.assign(this._defaults(), gespeicherter Zustand)` wiederhergestellt (Zeile 2569–2572). Ein bereits gespeicherter Wert überschreibt also den Code-Default dauerhaft, bis `Filter.reset()` aufgerufen wird (z. B. über den „Zurücksetzen"-Knopf im Filter-Sheet, Zeile 2971).
- Der Slider selbst reagiert bereits vollständig live: Ziehen nach unten löst `_onScoreSlider()` → `Filter.save()` → sofortige Neu-Filterung aus (Zeile 3014–3022). Das im Ticket verlangte „reduziere ich den Filter manuell, werden niedrigere Werte wieder sichtbar" ist **keine separate Logik, die neu gebaut werden muss** — es ist das bereits bestehende Slider-Verhalten. Es gibt keinen zusätzlichen Mechanismus zu entwickeln, nur der Startwert ändert sich.

**Scope:**
Eingeschlossen: Der Code-Default des Wahrscheinlichkeits-Sliders (`Filter._defaults().minScore`) wird von `0` auf `70` geändert, sodass ein Fotograf ohne bisher gespeicherte Filtereinstellung den Feed künftig direkt mit „≥ 70 %" gefiltert sieht.
Ausdrücklich ausgeschlossen (bis Klärung, siehe Fragen unten): Migration/Zurücksetzen von bereits in `localStorage` gespeicherten Filterständen bestehender Nutzer; Einführung eines eigenen, vom Feed getrennten Default-Werts für Kalender/Scout/Locations-Tab; Änderung des Server-Abfragewerts `CFG.minScore` (0,35) — der bleibt unverändert, da er nur die Rohdatenmenge vom Server begrenzt, nicht das, was der Fotograf sieht.

**Example Mapping:**

📏 **Regel 1:** Beim allerersten Start der App (noch kein gespeicherter Filterstand) zeigt der Feed standardmäßig nur Chancen mit Wahrscheinlichkeit ≥ 70 %.
- 🟢 Beispiel: Ein Fotograf installiert die App neu und öffnet den Feed zum ersten Mal. Von 20 verfügbaren Chancen haben 6 eine Wahrscheinlichkeit von 70 % oder mehr. Im Feed erscheinen genau diese 6.
- 🟢 Beispiel: Der Wahrscheinlichkeits-Regler im Filter-Menü steht beim ersten Öffnen bereits auf „≥ 70 %", nicht auf „Alle".

📏 **Regel 2:** Schiebt der Fotograf den Wahrscheinlichkeits-Regler manuell auf einen niedrigeren Wert (oder auf „Alle"), werden auch die weniger wahrscheinlichen Chancen sofort sichtbar — ohne Neuladen der Seite.
- 🟢 Beispiel: Fotograf zieht den Regler von 70 % auf 40 %. Eine Chance mit 55 % Wahrscheinlichkeit, die vorher ausgeblendet war, erscheint sofort im Feed.
- 🟢 Beispiel: Fotograf zieht den Regler ganz nach links auf „Alle". Jetzt sind wieder alle geladenen Chancen sichtbar, unabhängig von ihrer Wahrscheinlichkeit.

📏 **Regel 3:** Der eingestellte Wert bleibt erhalten, solange die App nicht durch den Fotografen zurückgesetzt wird — auch über App-Neustarts hinweg.
- 🟢 Beispiel: Fotograf stellt den Regler einmalig auf „Alle", schließt die App und öffnet sie am nächsten Tag erneut. Der Feed zeigt weiterhin alle Chancen (nicht wieder nur ≥ 70 %).
- ⚪ Annahme: Das entspricht dem bereits bestehenden Verhalten des gesamten Filter-Menüs (alle anderen Filter-Chips verhalten sich ebenso) — bitte bestätigen, dass für die Wahrscheinlichkeit keine Ausnahme gelten soll.

📏 **Regel 4:** Der neue 70-%-Startwert gilt nur für den Chancen-Feed. Für Kalender-Ansicht, Scout und Karte/Locations-Tab ändert sich nichts an der bisherigen Abgrenzung.
- 🟢 Beispiel: Ein Nutzer stellt im Feed den Regler auf 40 %. Öffnet er danach den Kalender, sieht er dort ebenfalls ab 40 % gefilterte Chancen (weil Regel und Regler geteilt sind — das ist heute schon so, siehe Frage 2 unten).
- ❓ Frage: siehe Klärungsfragen unten — ob der 70-%-Startwert absichtlich auch für Kalender/Scout gelten soll oder ob dort weiterhin „Alle" als Start gewünscht ist.

**Akzeptanzkriterien (erlebbares App-Verhalten):**
- [ ] Bei einer App-Installation ohne vorherige Filter-Einstellung zeigt der Feed direkt nach dem ersten Öffnen nur Chancen mit Wahrscheinlichkeit ≥ 70 %.
- [ ] Der Wahrscheinlichkeits-Regler im Filter-Menü steht beim allerersten Öffnen bereits auf „≥ 70 %" (nicht auf „Alle").
- [ ] Zieht der Fotograf den Regler auf einen Wert unter 70 %, erscheinen die entsprechend wahrscheinlicheren UND weniger wahrscheinlichen Chancen sofort im Feed, ohne dass die Seite neu geladen werden muss.
- [ ] Zieht der Fotograf den Regler auf „Alle" (ganz nach links), sind alle geladenen Chancen unabhängig von ihrer Wahrscheinlichkeit sichtbar.
- [ ] Nach Schließen und erneutem Öffnen der App bleibt der zuletzt manuell eingestellte Reglerwert erhalten (keine Rückkehr auf 70 % ohne aktives Zurücksetzen).
- [ ] Edge Case: Gibt es an einem Tag keine einzige Chance mit Wahrscheinlichkeit ≥ 70 %, zeigt der Feed einen leeren Zustand mit Hinweistext (bereits vorhandenes Verhalten, Zeile ~1722 „Keine Chancen gefunden") statt eines Fehlers.
- [ ] Edge Case: Bereits bestehende Nutzer mit einem zuvor gespeicherten, abweichenden Reglerwert (z. B. „Alle") behalten diesen Wert unverändert bei — der neue Default 70 % gilt ausschließlich für Installationen ohne gespeicherten Zustand (kein rückwirkendes Überschreiben).

**Pre-Mortem:**
- 💀 Szenario: Fotograf installiert die App neu, Feed zeigt „Keine Chancen gefunden", weil an dem Tag zufällig nichts über 70 % liegt — Eindruck „App ist leer/kaputt" statt „App filtert nur zu streng". Auslöser: 70 % könnte je nach Wetterlage/Saison ein großer Teil der Chancen ausblenden. Frühwarnung: schon beim manuellen Test an einem x-beliebigen Tag prüfen, wie viele der aktuell im Feed sichtbaren Chancen die Schwelle real erreichen. Gegenmaßnahme: als Frage an Stephan (siehe unten) — falls zu viele Tage leer wären, ggf. niedrigeren Default oder deutlicheren Empty-State-Hinweis („Filter lockern") in Betracht ziehen.
- 💀 Szenario: Der neue Default wirkt ungewollt auch im Kalender und lässt dort ebenfalls nur ≥ 70 % durch, obwohl Stephan dort weiterhin „Alle" erwartet hatte. Auslöser: `Filter.apply()` wird von Feed UND Kalender geteilt genutzt (Code-verifiziert, Zeile 1689 und 2065) — es gibt aktuell keinen separaten Kalender-Default. Gegenmaßnahme: als 🔴 Klärungsfrage gestellt (siehe unten), vor Implementierung zu entscheiden.
- 💀 Szenario: Ein Test mit bereits vorhandenem `localStorage`-Zustand (z. B. Stephans eigenes Testgerät, auf dem der Filter schon einmal berührt wurde) zeigt weiterhin „Alle" oder „35 %" an, obwohl der Code-Default geändert wurde — Fehleindruck „Fix wirkt nicht". Auslöser: `Filter._KEY` überschreibt den Code-Default dauerhaft, sobald einmal gespeichert wurde (Code-verifiziert, Zeile 2569–2572). Gegenmaßnahme: als Testhinweis in den Testplan aufnehmen — Test entweder auf einem Gerät/Browser ohne vorherigen Filterstand oder nach explizitem „Filter zurücksetzen" durchführen.
- 💀 Szenario: Der Locations-Tab/die Karte zeigt nach der Änderung plötzlich deutlich weniger Locations an, weil `applyToLocations()` den neuen 70-%-Default übernimmt, sobald Feed-Daten geladen sind — obwohl der Slider dort als „nur im Feed relevant" ausgegraut dargestellt wird und ein Nutzer nicht erwartet, dass er dort trotzdem wirkt. Auslöser: bereits bestehendes Verhalten (nicht neu durch dieses Ticket verursacht, aber durch den höheren Default stärker sichtbar). Gegenmaßnahme: in der Regressionsprüfung Locations-Tab nach Feed-Besuch explizit gegenchecken.
- 💀 Szenario: Beim Reduzieren des Reglers unter 70 % erscheinen keine zusätzlichen Chancen, weil der Server (`CFG.minScore = 0.35`) von vornherein nur Chancen ≥ 35 % ausliefert — ein Fotograf, der den Regler auf 10–30 % stellt, wundert sich, warum trotzdem nichts Neues erscheint. Auslöser: Verwechslung der beiden Score-Werte (siehe Code-Verifikation oben) — dieses Verhalten besteht bereits heute unabhängig von diesem Ticket, wird aber durch einen höheren sichtbaren Default (70 % statt 0 %) für den Fotografen erstmals bewusst wahrnehmbar, weil er den Regler jetzt aktiv bedienen muss statt bei „Alle" zu bleiben. Gegenmaßnahme: als Edge-Case-AK aufnehmen und im Testplan gezielt mit einem Reglerwert unterhalb von 35 % testen.

**Klärungsfragen an Stephan:**
1. 🔴 Der Wahrscheinlichkeits-Regler wird laut Code sowohl im Feed als auch im Kalender verwendet (gleicher Filter-Zustand, keine getrennte Logik). Soll der neue 70-%-Startwert **auch für den Kalender** gelten, oder soll der Kalender weiterhin bei „Alle" starten (was eine zusätzliche, heute nicht vorhandene Trennung der beiden Ansichten erfordern würde)? Für Scout gilt laut Code-Verifikation derselbe geteilte Zustand wie für den Feed — falls hier eine Abweichung gewünscht ist, bitte ebenfalls benennen.
   - ✅ **Entschieden (2026-07-04):** Überall gleich — der 70-%-Startwert gilt geteilt für Feed, Kalender und Scout. Keine Trennung der Ansichten (Option C entfällt).
2. 🔴 Soll der neue 70-%-Default auch für Nutzer gelten, die die App schon installiert haben und bereits einen eigenen (ggf. niedrigeren) Reglerwert gespeichert haben — oder ausschließlich für Neuinstallationen/erstmaliges Öffnen ohne vorherigen Filterstand? (Technisch bedeutet „auch für Bestandsnutzer": der gespeicherte Wert müsste beim nächsten App-Start einmalig zurückgesetzt werden — ein zusätzlicher Schritt gegenüber der reinen Default-Änderung.)
   - ✅ **Entschieden (2026-07-04):** Für alle zurücksetzen — auch bereits gespeicherte, abweichende Reglerwerte werden einmalig auf 70 % gesetzt (Option B).
3. ⚪ Annahme, bitte bestätigen: Der Server liefert weiterhin grundsätzlich Chancen ab 35 % Wahrscheinlichkeit aus (unveränderter Wert `CFG.minScore`); der Regler kann also nur zwischen „35 % bis 100 %" sinnvoll etwas ein-/ausblenden, ein Reglerwert unter 35 % zeigt keine zusätzlichen Chancen, weil der Server sie gar nicht erst liefert. Falls Stephan möchte, dass der Regler auch Werte unter 35 % sinnvoll nutzbar macht, wäre zusätzlich eine Änderung am Server-Abfragewert nötig — das wäre ein größerer Eingriff als im Ticket beschrieben.
   - ✅ **Bestätigt per manuellem Test (2026-07-04):** Regler unter 35 % zeigt erwartungsgemäß keine zusätzlichen Chancen — Annahme trifft zu, kein Server-Eingriff nötig.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt (inkl. Code-Verifikation von `web/index.html`)
- [x] Architektur analysiert: betroffene Datei ausschließlich `web/index.html` (`Filter._defaults()` Zeile 2566, ggf. `Filter._render()`-Beschriftung); kein Backend-Bezug
- [x] Ticket-Beziehungsanalyse: US-32/US-18-20/27/BUG-08 geprüft — bestätigt reine Wertänderung eines bestehenden, stabilen Features; keine Überlappung mit offenen Tickets gefunden
- [x] Designer-Check: rein numerische Default-Wert-Änderung eines bestehenden Sliders, keine neue visuelle Komponente → fotoalert-designer nicht erforderlich
- [x] Implementierungsoptionen: A / B / C (siehe unten) — **Option B gewählt** (Stephan, 2026-07-04: überall gleich + für alle Nutzer zurücksetzen)
- [x] Empfehlung/Entscheidung: **Option B**, geteilt über Feed/Kalender/Scout, einmaliger Reset für Bestandsnutzer
- [ ] **Prototyp-Gate:** Stephan möchte vor Implementierung eine Verhaltens-Beschreibung sehen (kein Code-Prototyp nötig, da reine Default-Wert-/Reset-Logik ohne neue UI) — vorgelegt 2026-07-04, Freigabe steht aus

**Implementierungsoptionen:**

### Option A — Reiner Code-Default, bestehender Zustand bleibt unangetastet
- Vorgehen: Nur der Startwert in `Filter._defaults()` wird von `minScore: 0` auf `minScore: 70` geändert. Nutzer ohne bisherigen `localStorage`-Eintrag starten künftig bei 70 %. Nutzer mit bereits gespeichertem Wert (egal welcher) behalten ihren eigenen Stand unverändert.
- Betroffene Dateien: `web/index.html`, eine Zeile (`Filter._defaults()`).
- Vorteile: Minimalinvasiv, kein Risiko für bestehende Nutzer-Einstellungen, entspricht dem Standardverhalten aller anderen Filter-Defaults in dieser App.
- Nachteile/Risiken: Bestandsnutzer, die die App vor diesem Ticket schon einmal geöffnet haben, sehen den neuen 70-%-Default nie (ihr Zustand ist bereits gespeichert) — falls Stephan das für alle will (Frage 2), erfüllt diese Option das nicht.
- Aufwand: klein.

### Option B — Code-Default ändern + einmaliger Reset für Bestandsnutzer
- Vorgehen: Wie Option A, zusätzlich ein einmaliger Migrationsschritt beim App-Start: falls der gespeicherte Filterstand noch nie explizit den Wahrscheinlichkeits-Regler berührt hat (z. B. über ein Versions-Flag erkannt), wird der gespeicherte `minScore`-Wert einmalig auf 70 gesetzt.
- Betroffene Dateien: `web/index.html` (`Filter._defaults()` + zusätzliche Migrationslogik beim Laden des Filterzustands).
- Vorteile: Alle Nutzer, auch Bestandsnutzer, sehen den neuen Default.
- Nachteile/Risiken: Deutlich komplexer als im Ticket beschrieben („vermutlich reine Default-Wert-Änderung"); Gefahr, einen bewusst von einem Nutzer gewählten niedrigen Wert ungewollt zu überschreiben, wenn die Unterscheidung „nie berührt" vs. „bewusst auf 0 gelassen" nicht zuverlässig möglich ist (aktuell gibt es kein Flag dafür, das müsste neu eingeführt werden).
- Aufwand: mittel.

### Option C — Getrennter Default für Feed vs. Kalender/Scout
- Vorgehen: Der Wahrscheinlichkeits-Filter wird pro Ansicht getrennt gespeichert (z. B. `minScoreFeed` und `minScoreCalendar`), sodass der Feed bei 70 % startet, der Kalender aber unabhängig bei „Alle" bleibt.
- Betroffene Dateien: `web/index.html`, mehrere Stellen (`Filter._defaults()`, `Filter.apply()`-Aufrufe in Feed und Kalender, Filter-Sheet-Rendering, Badge-Zählung).
- Vorteile: Löst Klärungsfrage 1 sauber, falls Stephan getrennte Verhalten für Feed und Kalender wünscht.
- Nachteile/Risiken: Deutlich größerer Eingriff in ein zentrales, gut funktionierendes Filter-System (Risiko für Regressionen in allen Ansichten, die den Filter nutzen); nur nötig, falls Frage 1 mit „nein, Kalender soll unverändert bleiben" beantwortet wird.
- Aufwand: groß.

✅ **Empfehlung:** Option A. Sie entspricht exakt dem im Ticket beschriebenen Umfang („vermutlich reine Default-Wert-Änderung", vom Ticket selbst so vermutet und durch Code-Verifikation bestätigt), hat das geringste Regressionsrisiko und passt zum bestehenden Verhalten aller anderen Filter in dieser App (Defaults gelten nur für neue/zurückgesetzte Zustände, nie rückwirkend). Falls Stephan bei Frage 2 „auch für Bestandsnutzer" möchte, empfehle ich, das als eigenes, klar abgegrenztes Ticket zu behandeln statt es hier mit hineinzunehmen — es ändert Aufwand und Risiko erheblich. Bei Frage 1 empfehle ich, den geteilten Zustand beizubehalten (kein Option C), sofern Stephan nicht ausdrücklich einen fachlichen Grund für getrennte Kalender-/Feed-Defaults nennt.

**Testplan:**
- [ ] Automatisiert: Dieses Ticket betrifft ausschließlich clientseitigen UI-Zustand ohne Server-Logik: kein neuer `pytest`-Fall in `backend/tests/` nötig; Verhalten wird über die manuellen Schritte unten geprüft.
- [x] Manuell (nach lokalem Serverstart, siehe `fotoalert-localdev`) — Stephan bestätigt 2026-07-04:
  1. [x] Browser-Profil ohne vorherigen FotoAlert-Filterstand (privates Fenster) → Regler startet direkt bei „≥ 70 %".
  2. [x] Feed öffnen → nur Chancen mit Wahrscheinlichkeit ≥ 70 % sichtbar.
  3. [x] Regler auf 40 % ziehen → zusätzliche, vorher ausgeblendete Chancen erscheinen sofort ohne Neuladen.
  4. [x] Regler ganz auf „Alle" ziehen → alle geladenen Chancen sichtbar. Stephan bestätigt 2026-07-04.
  5. [x] Regler auf einen Wert unter 35 % stellen (z. B. 10 %) → keine zusätzlichen Chancen (Server-Grenze). Stephan bestätigt 2026-07-04, Klärungsfrage 3 damit erledigt.
  6. [x] Seite neu laden → zuletzt gewählter Reglerwert bleibt erhalten (nicht zurück auf 70 %).
  7. [x] Kalender-Tab → derselbe Reglerwert wirkt dort ebenfalls (geteilter Zustand, wie entschieden).
  8. [x] Regression: Locations-Tab nach Feed-Besuch. Stephan bestätigt 2026-07-04.
  9. [x] Regression: übrige Filter-Chips (Eventtyp, Tageszeit, Schwierigkeit, Entfernung, Verifikation). Stephan bestätigt 2026-07-04.

**Implementierungsnotiz (2026-07-04):**
- Datei: `web/index.html`.
- `Filter._defaults()` (Zeile ~2598): `minScore: 0` → `minScore: 70`. Gilt geteilt für Feed, Kalender und Scout (kein separater Wert pro Ansicht, wie entschieden — Option B).
- Neue Funktion `Filter.migrateMinScoreDefault()` (Zeilen ~2617–2637): liest den gespeicherten Filterstand aus `localStorage` (`Filter._KEY = 'fotoalert_filters'`) und setzt `minScore` einmalig auf 70, falls abweichend. Ein neuer Flag-Key `Filter._MIGRATED_KEY = 'fotoalert_filters_v119_migrated'` markiert, dass die Migration bereits gelaufen ist — danach überschreibt sie einen vom Nutzer selbst gewählten niedrigeren Wert nie wieder.
- Aufruf der Migration in `App.init()` (Zeile ~6444), direkt nach `Filter._updateBadge()` und vor den bestehenden einmaligen Migrationen (Verify/Rating/CameraFOV) — gleiches etabliertes Muster wie dort.
- `CFG.minScore = 0.35` (Server-Ladegrenze) unverändert, wie im Scope festgelegt.
- Umgesetzt: Option B (Code-Default ändern + einmaliger Reset für Bestandsnutzer), wie von Stephan am 2026-07-04 freigegeben.

**Unabhängige Verifikation (2026-07-04, separater Subagent):** **GRÜN** — alle 7 geprüften Akzeptanzkriterien im Code belegt; Migrations-Flag wird nachweislich erst nach erfolgreichem Schreiben des neuen Werts gesetzt (kein Race-Risiko); kaputtes/fehlendes localStorage wird per try/catch sauber abgefangen (kein Crash); übrige Filter-Chips und Kalender/Scout-Logik unangetastet; kein Scope Creep (genau die 4 erwarteten Codestellen geändert, keine weiteren).

**Refactor-Check (2026-07-04):** `tools/refactor_check.py --report` ausgeführt — einziger Fund betrifft `backend/main.py` (`startup()`, 84 Zeilen, Threshold 80), außerhalb des Scopes dieses Tickets, keine Maßnahme hier. Die 4 geänderten Codestellen (`Filter._defaults()`, `Filter._MIGRATED_KEY`, `Filter.migrateMinScoreDefault()`, Aufruf in `App.init()`) wurden mit den bestehenden einmaligen Migrationen (`Verify.migrateFromLocalStorage`, `Rating.migrateFromLocalStorage`, `CameraFOV._loadProfile`) verglichen: gleiches Kommentar-Header-Muster (`// ── … ──`), gleiche Platzierung/Reihenfolge der Aufrufe in `App.init()`, try/catch vorhanden und sauber (Flag wird auch bei Fehler gesetzt, verhindert Endlos-Retry). Die Abweichung „eigenes Flag statt Löschen des Quell-Keys als Migrations-Marker" ist sachlich begründet, da `Filter._KEY` weiterhin die aktiven Filtereinstellungen enthält (im Gegensatz zu Verify/Rating, wo der Quell-Key nach Migration gelöscht wird) — keine Inkonsistenz, keine Code-Änderung nötig. Kein Redundanz- oder Klarheitsproblem gefunden. Keine offenen technischen Schulden aus diesem Ticket.

**Release-Notiz (2026-07-04):** Beim Release-Check festgestellt, dass der Frontend-Code technisch bereits mit dem BUG-61-Release (`v1.20.21`, 19:31 Uhr) live ging — `release.sh` committet grundsätzlich den kompletten `web/index.html`-Stand, unabhängig vom Ticket, und hat dabei die zu dem Zeitpunkt schon geschriebenen, aber noch nicht von Stephan getesteten US-119-Änderungen mit eingesammelt. Auf Stephans Wunsch trotzdem ein eigener, sauberer Release nachgezogen: **`v1.20.22`** gepusht und Health-Check auf Produktion bestätigt (`https://fotoalert.stephanschumann.com/health` → `status: ok`). Funktional bestand dadurch kein Risiko, da Stephan das Verhalten anschließend vollständig lokal getestet und bestätigt hat — der Punkt ist rein prozessual (fehlender eigener Versions-Bump/Changelog-Eintrag zum Zeitpunkt des faktischen Deploys) und hiermit nachträglich sauber dokumentiert.

---

### US-120 · Beispielbild pro Location hochladen (Hoch-/Querformat, Größenlimit) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-04 |

**Beschreibung:** Als Host möchte ich pro Location ein Beispielbild hochladen können, das andere Nutzer in Hoch- oder Querformat passend zur Geräteausrichtung sehen (Bild dreht beim Drehen des Handys mit, Hochkant-Bilder vollflächig im Hochkant-Modus), damit Interessierte sofort einen visuellen Eindruck vom Spot bekommen. Bildgröße max. 1 MB, idealerweise serverseitige Kompression auf ca. 500 KB beim Upload, um Performance und Datenvolumen zu schonen.

**Bezug:** Keine Dubletten oder direkt überschneidenden Tickets im Backlog gefunden (Suche nach „Bild", „Upload", „Beispielbild" ergab keine bestehenden Bild-Upload-Tickets). Neues, eigenständiges Feature. Berührt ggf. dieselbe Location-Detail-Sektion wie **US-103** [x] (Karten-Marker & FOV-Legende) und **US-87** [x] (Vollbild-Overlay Bearbeiten-Karte), aber rein layouttechnisch, keine funktionale Überschneidung.

---

#### 📋 Spec (Analyse-Phase, 2026-07-04)

**Annahmen-Protokoll (vor dem Mapping):**

| Punkt | Typ | Entscheidung |
|---|---|---|
| Wer darf hochladen? | ✅ klar ableitbar | Ticket sagt „Als Host" — es existiert bereits eine Host-Rolle (`Auth.isHost()` im Frontend, `auth.require_host` im Server, bisher genutzt für „Location löschen"). Hochladen/Ersetzen/Löschen des Beispielbilds ist eine Host-Aktion. |
| Wo erscheint das Bild im Detail-Bereich? | ⚠️ Annahme | Oben im Hero-Bereich (Titelzone), direkt über oder neben Name/Beschreibung — nicht als eigene aufklappbare Sektion weiter unten, weil es ein Eindrucksbild ist, kein Datenblock. **Bitte bestätigen.** |
| Erscheint das Bild auch als kleines Vorschaubild in der Locations-Liste (Kartenansicht mit Icon)? | 🔴 funktional kritisch | Ticket nennt nur „Location-Detail" implizit über „Interessierte bekommen einen visuellen Eindruck". Die Liste zeigt aktuell nur ein Kategorie-Icon, kein Bild. **Frage 1 an Stephan.** |
| Was passiert, wenn kein Bild hochgeladen wurde? | ⚠️ Annahme | Bereich wird nicht angezeigt bzw. zeigt einen neutralen Platzhalter mit „Bild hinzufügen"-Hinweis nur für den Host, für normale Nutzer bleibt der Bereich einfach weg. **Bitte bestätigen.** |
| Was passiert bei zu großem Bild (> 1 MB) genau? | 🔴 funktional kritisch | Ticket nennt „max. 1 MB" UND „serverseitige Kompression auf ca. 500 KB" im selben Satz — das ist zunächst widersprüchlich (harte Grenze vs. automatische Kompression). **Frage 2 an Stephan.** |
| Erlaubte Bildformate? | ⚠️ Annahme | JPEG/PNG/HEIC (Standard-Fotoformate von iPhone/Android), Server wandelt intern einheitlich in JPEG um. **Bitte bestätigen.** |
| Ein Bild pro Location oder mehrere? | ✅ klar ableitbar | Ticket sagt „ein Beispielbild pro Location" — genau eins, kein Galerie-Feature. |
| Ersetzen eines bestehenden Bilds? | ✅ klar ableitbar | Impliziert („hochladen können") — erneutes Hochladen ersetzt das bisherige Bild, kein Versionsverlauf. |
| EXIF-Rotation / Ausrichtung des Originalfotos | 🔴 funktional kritisch | Smartphone-Fotos tragen die Ausrichtung oft nur als EXIF-Tag, nicht als tatsächlich gedrehte Pixel. Ohne Korrektur landet ein Hochkant-Foto ggf. seitlich verdreht im Hochkant-Modus. **Frage 3 an Stephan** (technische Klärung, aber mit Auswirkung auf erlebbares Verhalten). |

**Fragen an Stephan (vor Rules — bitte auf Antwort warten):**

1. Soll das Beispielbild nur im aufgeklappten Location-Detail erscheinen, oder zusätzlich auch als kleines Vorschaubild in der Locations-Liste (dort wo aktuell nur ein rundes Kategorie-Icon zu sehen ist)?
2. Zur Größengrenze: Ist gemeint „Upload wird bei mehr als 1 MB abgelehnt, Nutzer muss selbst verkleinern" — oder „Upload wird bis 1 MB akzeptiert und der Server komprimiert danach automatisch weiter auf ca. 500 KB, damit am Ende immer ein kleines, schnell ladendes Bild gespeichert wird"? (Empfehlung unten: zweite Variante, unten unter Rule 3 begründet.)
3. Ist es in Ordnung, wenn Fotos, die auf dem Kopf oder seitlich gedreht aufgenommen wurden, automatisch anhand der im Foto gespeicherten Ausrichtungsinformation aufgerichtet werden (Standard-Verhalten von Foto-Apps), bevor sie gespeichert werden?

**Example Mapping** *(vorläufig, unter Vorbehalt der 3 Fragen oben — Rules nutzen die empfohlenen Defaults, werden nach Antwort ggf. angepasst)*

- **Rule 1 — Upload nur für den Host:** Nur ein eingeloggter Host sieht die Möglichkeit, ein Beispielbild hochzuladen, zu ersetzen oder zu entfernen. Normale Besucher sehen nur das fertige Bild (falls vorhanden), keine Upload-Steuerung.
  - Beispiel: Host öffnet eine Location im Bearbeiten-Modus → sieht einen Bereich „Beispielbild" mit einem Button zum Auswählen einer Bilddatei. Ein normaler Nutzer öffnet dieselbe Location → sieht dort keinen Upload-Button, nur das Bild selbst (wenn vorhanden).
- **Rule 2 — Anzeige passend zur Geräteausrichtung, immer mittig eingepasst:** Das Beispielbild füllt die dafür vorgesehene Fläche im Location-Detail vollständig aus und behält dabei sein Seitenverhältnis — dreht der Nutzer sein Handy, dreht sich auch die Anzeigefläche mit und das Bild passt sich unmittelbar an (kein Umschalten zwischen zwei getrennt hochgeladenen Bildern nötig, ein einziges Originalbild wird flexibel dargestellt). Unabhängig davon, ob das Originalfoto hoch- oder querformatig ist und unabhängig von der aktuellen Geräteausrichtung, wird der sichtbare Bildausschnitt **immer mittig aus dem Originalbild genommen** (Bildmitte bleibt Bildmitte) — nie ein Ausschnitt, der zufällig nach oben, unten oder zur Seite verschoben ist.
  - Beispiel: Ein Hochformat-Beispielbild wird auf einem Handy im Hochkant-Modus angesehen → Bild füllt die Breite komplett aus, keine schwarzen Balken links/rechts, der obere und untere überschüssige Bildrand wird gleichmäßig abgeschnitten (nicht nur oben oder nur unten).
  - Beispiel: Derselbe Nutzer dreht sein Handy quer → dieselbe Bilddatei passt sich der neuen, breiteren Fläche an und füllt sie ebenfalls komplett aus, ohne dass ein zweites Bild geladen wird; auch hier bleibt die Bildmitte im Zentrum, links und rechts wird gleichmäßig abgeschnitten.
  - Beispiel: Ein querformatiges Beispielbild wird im Hochkant-Modus angezeigt (schmale, hohe Fläche) → die Fläche füllt sich vollständig, links und rechts wird entsprechend viel vom Originalbild abgeschnitten, aber die Mitte des Fotos bleibt sichtbar und mittig.
- **Rule 3 — Größenbegrenzung mit automatischer Verkleinerung:** Der Host kann Fotos direkt vom Smartphone hochladen (oft mehrere MB groß), ohne sie vorher selbst verkleinern zu müssen — der Server übernimmt die Verkleinerung automatisch bis zu einer sinnvollen Zielgröße, damit die App für alle Betrachter schnell lädt.
  - Beispiel: Host wählt ein 4 MB großes Foto direkt von der Kamera → Upload wird angenommen, der Host sieht kurz „Bild wird verarbeitet …“, danach ist ein deutlich kleineres, aber optisch kaum unterscheidbares Bild sichtbar.
  - Beispiel: Host versucht ein extrem großes Bild hochzuladen, das die vertretbare Obergrenze für einen einzelnen Upload sprengt (z. B. ein 40-Megapixel-RAW-artiges Foto von vielen zig MB) → Upload wird mit einer verständlichen Fehlermeldung abgelehnt, bevor der Server unnötig Rechenzeit investiert.
  - ❓ Frage 2 (s.o.) entscheidet den genauen Grenzwert-Mechanismus.
- **Rule 4 — Kein Bild vorhanden:** Solange kein Host ein Beispielbild hochgeladen hat, bleibt der Bildbereich im Detail schlicht unsichtbar (kein leerer grauer Kasten, kein „Bild fehlt“-Hinweis für normale Nutzer).
  - Beispiel: Nutzer öffnet eine ältere Location ohne Beispielbild → Detail-Ansicht sieht genauso aus wie heute, kein Platzhalter-Element stört das Layout.
  - Beispiel: Host öffnet dieselbe Location im Bearbeiten-Modus → sieht dort einen dezenten Hinweis „Noch kein Beispielbild“ mit Upload-Möglichkeit.

**Akzeptanzkriterien**

- [x] Ein Host kann beim Bearbeiten einer Location ein Foto von seinem Gerät auswählen und hochladen; nach Abschluss ist das Bild direkt im Location-Detail sichtbar.
- [x] Lädt derselbe Host später ein neues Foto für dieselbe Location hoch, ersetzt es das bisherige Bild vollständig (kein zweites Bild, keine Galerie).
- [x] Ein hochformatiges Beispielbild füllt die Bildfläche im Detail vollständig aus, wenn das Handy im Hochkant-Modus gehalten wird.
- [x] Wird dasselbe Handy quer gedreht, passt sich dieselbe Bildfläche unmittelbar an die neue Ausrichtung an und füllt sie ebenfalls komplett aus — ohne dass die Seite neu geladen werden muss.
- [x] Das Gleiche funktioniert spiegelbildlich für ein querformatiges Beispielbild (füllt die Fläche im Querformat-Modus voll aus).
- [x] Edge: Egal ob das Originalfoto hoch- oder querformatig ist und egal in welcher Ausrichtung das Handy gerade gehalten wird — der sichtbare Bildausschnitt ist immer mittig aus dem Originalbild genommen (überschüssiger Rand wird gleichmäßig auf beiden Seiten abgeschnitten, nie einseitig verschoben).
- [x] Lädt der Host ein sehr großes Foto direkt von der Kamera hoch (mehrere MB), wird es automatisch verkleinert; das Ergebnis ist spürbar kleiner als das Original, aber weiterhin gut erkennbar.
- [x] Edge: Versucht der Host ein Foto hochzuladen, das die vertretbare Obergrenze für einen Upload deutlich überschreitet, bekommt er eine klare, verständliche Fehlermeldung statt eines unklaren Abbruchs oder eines hängenden Ladebalkens.
- [x] Edge: Ein Foto, das auf dem Handy auf dem Kopf oder seitlich liegend aufgenommen wurde, erscheint nach dem Hochladen richtig herum (nicht verdreht), unabhängig davon, wie das Handy beim Fotografieren gehalten wurde.
- [x] Edge: Ein normaler Nutzer (nicht Host) sieht in keiner Ansicht eine Möglichkeit, ein Beispielbild hochzuladen, zu ersetzen oder zu löschen.
- [x] Edge: Bei einer Location ohne Beispielbild bleibt die Detail-Ansicht für normale Nutzer unverändert wie heute, ohne Platzhalter oder Leerfläche.
- [x] Edge: Lädt der Host eine Datei hoch, die kein gültiges Bild ist (z. B. ein PDF mit der Endung „.jpg“), wird der Upload mit einer verständlichen Fehlermeldung abgelehnt.
- [x] Edge (Nachtrag 2026-07-04): Löscht der Host eine Location, die ein hochgeladenes Beispielbild hatte, wird die Bilddatei automatisch mit entfernt (keine verwaiste Datei bleibt auf dem Server zurück); das Löschen der Location schlägt dabei nicht fehl, selbst wenn die Bilddatei aus irgendeinem Grund bereits nicht mehr vorhanden ist.

**Pre-Mortem**

1. 💀 **Szenario:** Ein Hochformat-Foto erscheint seitlich gedreht im Detail.
   **Auslöser:** Smartphone-Fotos speichern die Ausrichtung häufig nur als Zusatzinformation im Bild, nicht als tatsächlich gedrehte Bilddaten. Wird diese Zusatzinformation beim Verkleinern auf dem Server ignoriert, kommt ein falsch herum liegendes Bild heraus.
   **Frühwarnung:** Beim ersten Test mit einem am Handy hochkant aufgenommenen Foto zeigt sich das sofort visuell.
   **Gegenmaßnahme:** Ausrichtungskorrektur ist fester Bestandteil der serverseitigen Verarbeitung (siehe AK „auf dem Kopf/seitlich“ oben), Testplan deckt das mit einem echten Handyfoto ab, nicht nur mit einem bereits „geraden“ Testbild.
2. 💀 **Szenario:** Speicherplatz auf dem Server wächst unbemerkt, bis die Festplatte voll ist.
   **Auslöser:** Jede Location bekommt potenziell ein Bild, alte ersetzte Bilder werden nicht gelöscht, sondern sammeln sich an.
   **Frühwarnung:** Erst spürbar, wenn der Server aus Speicherplatzgründen Probleme bekommt — schwer im Normalbetrieb zu bemerken.
   **Gegenmaßnahme:** Beim Ersetzen eines Bildes wird die alte Bilddatei aktiv gelöscht, nicht nur der Verweis darauf überschrieben. Ein Bild pro Location als Obergrenze (Rule Ticket) verhindert unbegrenztes Wachstum von vornherein.
3. 💀 **Szenario:** Zwei parallele Uploads für dieselbe Location (Host lädt auf zwei Geräten gleichzeitig hoch, oder tippt versehentlich zweimal) hinterlassen einen inkonsistenten Zustand (z. B. Bilddatei vorhanden, aber Verweis zeigt noch auf die alte).
   **Auslöser:** Fehlende Reihenfolge-Sicherheit beim Schreiben von Datei + Verweis.
   **Frühwarnung:** Selten reproduzierbar, macht sich nur bei genau diesem Zufallstiming bemerkbar.
   **Gegenmaßnahme:** Bild wird zuerst vollständig auf der Festplatte gespeichert, erst danach der Verweis in der Location aktualisiert (ähnliches Muster wie bestehende atomare Schreibvorgänge in der Datenschicht).
4. 💀 **Szenario:** Sehr viele Nutzer laden gleichzeitig das Location-Detail, das Beispielbild macht die Seite spürbar langsamer als bisher.
   **Auslöser:** Unkomprimiertes oder zu großes Bild wird bei jedem Seitenaufruf erneut vollständig geladen.
   **Frühwarnung:** Fühlbar längere Ladezeit beim Öffnen einer Location mit Bild gegenüber einer ohne.
   **Gegenmaßnahme:** Serverseitige Komprimierung auf die im Ticket genannte Zielgröße (~500 KB) ist keine Kür, sondern Voraussetzung; zusätzlich Cache-Header setzen, damit ein einmal geladenes Bild im Browser wiederverwendet wird.
5. 💀 **Szenario:** Ein hochgeladenes Bild wird als eigentlich für eine andere Location bestimmtes Bild angezeigt (Verwechslung).
   **Auslöser:** Wird der Ziel-Ort des Uploads nicht eindeutig an die ID der gerade bearbeiteten Location gebunden (z. B. wenn der Host zwischen Öffnen des Bearbeiten-Formulars und Abschluss des Uploads zu einer anderen Location wechselt), könnte das Bild versehentlich der falschen Location zugeordnet werden.
   **Frühwarnung:** Fällt nur auf, wenn tatsächlich zwei Locations kurz hintereinander bearbeitet werden.
   **Gegenmaßnahme:** Die Location-Kennung wird fest in den Upload-Vorgang eingebettet (nicht aus einem globalen „aktuell offen“-Zustand zum Zeitpunkt des Abschlusses neu gelesen), Testplan deckt „zwei Locations kurz hintereinander bearbeiten“ ab.

**Analyse & Planung**

- [x] Example Mapping durchgeführt (3 Fragen an Stephan am Weg-Gate beantwortet — s.u.)
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert (Code tatsächlich gelesen, siehe unten)
- [x] Designer-Check: **visuell** (neues Bild-Element im Location-Detail) → siehe Designer-Hinweis unten
- [x] Implementierungsoptionen: A / B (siehe unten) — Option A freigegeben (Weg-Gate 2026-07-04)
- [x] Empfehlung: Option A für Speicherung (Datei statt Base64-in-Datenbank), Option A für Ausrichtung (ein Bild + flexible Anzeige statt zwei getrennter Uploads) — freigegeben durch Stephan (Weg-Gate 2026-07-04)

**Architektur-Analyse (Code tatsächlich gelesen am 2026-07-04):**

- **Datenmodell:** `backend/data/locations.py` — die `PhotoLocation`-Dataclass (Zeile 41–83) hat aktuell **kein** Bild-/Foto-Feld. Für Standard-Locations müsste ein neues optionales Feld (z. B. Bildpfad) ergänzt werden.
- **Custom Locations (nutzerangelegt):** `backend/data/store.py` — die SQLite-Tabelle `custom_locations` (Zeile 45–62) hat ebenfalls kein Bildfeld. Beide Location-Arten (Standard aus `LOCATIONS`, Custom aus SQLite) brauchen dieselbe neue Fähigkeit — Standard-Locations laufen bereits heute über den bestehenden `location_overrides`-Mechanismus (Zeile 64–67: freies JSON-Feld pro Location-ID), Custom Locations bräuchten eine neue Spalte.
- **Bearbeiten-Endpoint:** `backend/main.py`, `PATCH /locations/{loc_id}` (Zeile 2169–2242) ist der einzige bestehende Weg, um Felder einer Location zu ändern — er nimmt aktuell ausschließlich JSON-Werte entgegen (`Body(...)` als `dict`), es gibt **keinen** bestehenden Datei-Upload-Mechanismus im gesamten Backend (`UploadFile`/`multipart` kommt im Code kein einziges Mal vor). Ein Bild-Upload braucht also einen neuen, eigenständigen Endpoint (Bilddaten sind kein sinnvoller Teil eines JSON-`PATCH`-Bodys in vertretbarer Größe).
- **Berechtigung:** `backend/auth.py`, `require_host` (Zeile 76) existiert bereits und wird u. a. beim Löschen einer Location verwendet (`DELETE /locations/{loc_id}`, Zeile 2249). Für den Bild-Upload ist dieselbe Absicherung direkt wiederverwendbar — keine neue Rollenlogik nötig.
- **Statische Auslieferung:** `backend/main.py` Zeile 2459–2476 mountet den gesamten `web`-Ordner über `StaticFiles`. Für Bilddateien ist ein eigenes, nicht mit dem Web-Code vermischtes Verzeichnis sauberer — als Vorbild dient `_CACHE_DIR = Path(__file__).parent / "data" / "cache"` (Zeile 98), also z. B. ein neues `backend/data/location_images/`-Verzeichnis, das ebenfalls über `StaticFiles` (oder eine dedizierte Route) ausgeliefert wird.
- **Bildverarbeitung:** `Pillow==10.3.0` ist bereits eine bestehende Backend-Abhängigkeit (`requirements.txt` Zeile 22, aktuell genutzt für die Wetter-Kartenüberlagerung in `calculations/weather_grib.py`, US-112). Für Verkleinerung, Kompression und Ausrichtungskorrektur ist **keine neue Abhängigkeit** nötig, Pillow deckt das ab (inkl. Standardfunktion zum automatischen Aufrichten anhand der Bild-Ausrichtungsinformation).
- **Frontend — Detail-Ansicht:** `web/index.html`, `LocationDetail._render(loc)` (ab Zeile 5701) baut die Detail-Ansicht aus einem festen Hero-Bereich (Zeile 5702–5713: Titel, Icon, Beschreibung) gefolgt von mehreren aufklappbaren Abschnitten (`mkSec(...)`: Fotograf-Standort, Motiv, Ausrichtung, Karte & Blickwinkel, Links, Events, Bewertung, Verifikation). Ein Beispielbild passt inhaltlich am ehesten oben in den Hero-Bereich (großflächig, sofort sichtbar), nicht als zusätzlicher aufklappbarer Abschnitt weiter unten (siehe Annahmen-Protokoll oben, Frage an Stephan).
- **Frontend — Bearbeiten-Formular:** `LocationDetail.openEdit()` (ab Zeile 5246) und `saveEdit(locId)` (Zeile 5589) sind der bestehende Bearbeiten-Weg; ein Upload-Steuerelement würde in dieses Formular ergänzt, aber wegen der Dateigröße **nicht** über denselben JSON-`saveEdit`-Aufruf laufen, sondern über einen eigenen, sofortigen Upload-Request beim Auswählen der Datei (ähnlich wie ein separater Button, nicht Teil des „Speichern“-Sammel-Requests).
- **Kein Vorbild für Datei-Upload im Frontend:** `const API` (Zeile 1333–1365) kennt nur `get`/`post`/`patch`/`delete` mit JSON-Body (`Content-Type: application/json`, `JSON.stringify`). Ein datei-basierter Upload (`FormData`, kein JSON-Header) ist ein neuer Codepfad, keine Wiederverwendung von `API.post`.
- **Locations-Liste:** `Locations.render(locs)` (ab Zeile 5171) zeigt aktuell nur ein rundes Kategorie-Icon (Zeile 5182) pro Location, kein Bild. Ob das Beispielbild hier ebenfalls als kleines Vorschaubild erscheinen soll, ist die oben gestellte Frage 1 — technisch zusätzlicher, aber kleiner Zusatzaufwand (ein `<img>`-Tag statt/neben dem Icon).
- **Kein Render-Pfad-Konflikt:** Anders als bei BUG-59 (Wetter-Overlay) gibt es hier keine bestehende Fläche, die bereits von einer anderen Quelle (Server-PNG vs. Frontend-Farbwerte) gerendert wird — der Bildbereich ist komplett neu, kein Konflikt mit bestehendem Rendering.

**Designer-Hinweis (visuell sichtbar → `fotoalert-designer` vor Umsetzung empfohlen):**
Dieses Ticket führt ein komplett neues visuelles Element ein (erstes Foto-/Bild-Element der App, bisher rein Icon-/Text-/Kartenbasiert). Empfehlung: vor Implementierungsstart kurz den Designer-Skill für Bildrahmen (Eckenradius, Rand/Schatten, Platzierung im Hero, Verhalten des Platzhalters beim Host ohne Bild) konsultieren, damit das neue Element zum bestehenden Bauhaus-Stil passt statt einer Ad-hoc-Lösung.

**Implementierungsoptionen**

*Option A — Bilddatei auf der Festplatte, Verweis als Text-Feld in der Location; ein Upload, flexible Anzeige je Geräteausrichtung; serverseitige Verkleinerung*
In Alltagssprache: Das Foto wird als normale Bilddatei auf dem Server abgelegt (so wie heute schon die täglichen Wetterkarten-Bilder erzeugt und abgelegt werden), die Location „weiß" nur, unter welchem Namen ihr Bild zu finden ist. Es gibt nur einen Upload-Knopf — dieselbe Datei wird im Hochkant- wie im Querformat-Modus einfach passend in die verfügbare Fläche eingepasst, kein zweiter Upload für die jeweils andere Ausrichtung nötig.

| Aspekt | Bewertung |
|---|---|
| Technischer Ansatz | Neuer Upload-Endpoint (Datei-Upload, nur für Host), Bild wird beim Hochladen serverseitig ausgerichtet, auf sinnvolle Maximalmaße verkleinert und auf die Zielgröße komprimiert, dann als Datei gespeichert; Location bekommt ein neues Text-Feld mit dem Dateinamen/Pfad. Anzeige im Frontend: `object-fit: cover` + `object-position: center` (Bildmitte bleibt immer im Zentrum, egal welche Kante beschnitten wird) |
| Betroffene Dateien | `backend/main.py` (neuer Endpoint + Feld in PATCH-Erlaubnisliste), `backend/data/locations.py` (neues optionales Feld), `backend/data/store.py` (neue Spalte für Custom Locations + ggf. `location_overrides`-Nutzung für Standard-Locations), `requirements.txt` unverändert (Pillow bereits vorhanden), `web/index.html` (Upload-Steuerelement im Bearbeiten-Formular, Anzeige im Hero-Bereich, CSS für flexible Bildfläche) |
| Vorteile | Ein Bild, eine Quelle der Wahrheit; einfach zu verstehen und zu testen; Bilddateien bleiben außerhalb der Datenbank (Datenbank bleibt klein und schnell); Löschen/Ersetzen ist ein einfacher Dateisystem-Vorgang |
| Nachteile / Risiken | Neues Verzeichnis muss bei Server-Backups mitgedacht werden (bestehendes Backup-Verfahren prüft aktuell wohl nur die Datenbank/JSON-Dateien — als offene Frage für die Implementierungsphase vormerken, nicht Teil dieser Analyse) |
| Aufwand | Mittel — neuer Endpoint, neues Feld in zwei Datenquellen, neues Frontend-Steuerelement, aber keine neue Abhängigkeit nötig |

*Option B — Bild als Base64-Text direkt in der Datenbank/JSON gespeichert*
In Alltagssprache: Das Foto wird nicht als eigene Datei abgelegt, sondern in einen langen Text umgewandelt und direkt zusammen mit den anderen Location-Daten gespeichert.

| Aspekt | Bewertung |
|---|---|
| Technischer Ansatz | Bild wird als Text-Kodierung in dasselbe Datenfeld geschrieben, das auch Name/Beschreibung enthält |
| Vorteile | Keine separate Dateiverwaltung nötig |
| Nachteile / Risiken | Macht die Datenbank/JSON-Dateien deutlich größer und langsamer beim Lesen (jede Abfrage aller Locations lädt dann auch alle Bilder mit, selbst wenn nur die Liste ohne Bilder gebraucht wird); textkodierte Bilder sind ca. ein Drittel größer als die Originaldatei; deutlich unüblicher Ansatz, der von bestehenden Mustern in dieser App abweicht |
| Aufwand | Mittel, aber mit strukturellem Nachteil, der sich bei jedem zukünftigen Location-Bild wiederholt verschlechtert |

*Option C (zu Rule 2/Frage 3) — Zwei getrennte Uploads für Hoch- und Querformat statt einem flexiblen Bild*
In Alltagssprache: Der Host lädt zwei Fotos hoch, eines eigens fürs Hochkant-Handy, eines eigens fürs Querformat-Handy; die App zeigt je nach Geräteausrichtung das passende der beiden.

| Aspekt | Bewertung |
|---|---|
| Vorteile | Jedes Bild kann optisch exakt auf sein Zielformat zugeschnitten sein |
| Nachteile / Risiken | Verdoppelter Aufwand für den Host (zwei Uploads statt einem), verdoppelter Speicherbedarf, widerspricht der Ticket-Formulierung „ein Beispielbild" (Singular) |
| Aufwand | Groß gegenüber A, ohne im Ticket geforderten Zusatznutzen |

✅ **Empfehlung:** Option A für die Speicherung (Bilddatei statt Base64/Option B) — deutlich näher an den bestehenden Mustern der App (Wetter-PNGs werden bereits genauso als Dateien abgelegt) und ohne den Lese-Performance-Nachteil von Option B. Zusätzlich Ablehnung von Option C zugunsten eines einzigen, flexibel eingepassten Bildes (Rule 2) — das entspricht der Ticket-Formulierung „ein Beispielbild" wörtlich und spart dem Host doppelten Aufwand.

**Daten-Validierung:** entfällt — kein Berechnungs-/Filterfeature, reine Datenmodell- und Anzeige-Erweiterung.

**Testplan**

- [x] Automatisiert (Harness): 12 pytest-Fälle in `backend/tests/test_us120.py`, alle grün (Stephan, 2026-07-04, `FOTOALERT_ENV=dev python3 -m pytest tests/test_us120.py -v` → 12 passed). Fixture-Bug behoben (Tests legen sich jetzt selbst eine Test-Location an statt eine externe geteilte Fixture-ID vorauszusetzen).
- [x] Manuell (unter http://127.0.0.1:8000): Host-Upload getestet, Bild im Hero-Bereich sichtbar, Hoch-/Querformat per Fenstergröße simuliert — Bild füllt die Fläche vollständig, mittig eingepasst.
- [~] Manuell: echtes, auf dem Kopf/seitlich aufgenommenes Handyfoto — nicht separat mit einem echten Handyfoto durchgeführt (nur generisches Testbild ohne EXIF-Rotation); die zugrundeliegende Logik ist aber durch den pytest-Fall `test_exif_orientation_is_applied_to_pixels` automatisiert abgedeckt und grün.
- [x] Manuell: großes Testbild hochgeladen, automatisch verarbeitet, sichtbar in `GET /locations`.
- [x] Manuell: Datei über der Obergrenze (21 MB) → Ablehnung mit verständlicher Fehlermeldung, kein Hängen (curl, Stephan, 2026-07-04).
- [x] Manuell: Upload ohne Host-Rolle (kein Token) → 401 (curl, Stephan, 2026-07-04).
- [x] Regression: Name/Koordinaten einer Location mit Bild weiterhin änderbar und speicherbar (Berliner Dom Spree, Stephan, 2026-07-04).
- [x] Zusätzlich verifiziert (über den ursprünglichen Testplan hinaus): Ersetzen eines Bildes hinterlässt keine Dateileiche; Löschen einer Location entfernt ihr Bild automatisch (beides per curl, Stephan, 2026-07-04).

**Weg-Gate-Entscheidung (Stephan, 2026-07-04):**
- ✅ Umsetzungsweg **Option A** (Bilddatei auf dem Server, Verweis in der Location) freigegeben.
- **Frage 1 (Vorschaubild):** Nur im Detail — kein Vorschaubild in der Locations-Liste.
- **Frage 2 (Größenlimit):** Automatisch verkleinern — Dateien bis 1 MB werden angenommen und automatisch auf ca. 500 KB komprimiert, kein hartes Ablehnen bei 1 MB.
- **Frage 3 (Ausrichtung):** Ja, automatische Ausrichtungskorrektur bei verdreht aufgenommenen Fotos.

→ Ready for Dev.

**Prototyp-Freigabe (Stephan, 2026-07-04):** Mockup (Hochformat/Querformat mit Bild + Host-Platzhalter) gezeigt und freigegeben, mit einer Ergänzung: Bildausschnitt muss in JEDER Kombination aus Bild- und Geräteausrichtung mittig aus dem Original genommen werden (`object-fit: cover` + `object-position: center`) — als hartes AK in Rule 2 und Akzeptanzkriterien nachgetragen (s.o.).

**Implementierungsnotiz (2026-07-04):**
- `backend/data/locations.py`: `PhotoLocation.image_filename: Optional[str] = None`.
- `backend/data/store.py`: idempotente Spalten-Migration `image_filename TEXT` für `custom_locations`.
- `backend/models/schemas.py`: `LocationOut.image_url: Optional[str]`.
- `backend/main.py`: neues Verzeichnis `_IMAGE_DIR`, neuer Endpoint `POST /locations/{id}/image` (nur Host via `require_host`), `_process_uploaded_image` (EXIF-Transpose, Verkleinerung, iterative JPEG-Kompression auf ~500 KB), `StaticFiles`-Mount `/location-images`, alte Bilddatei wird beim Ersetzen aktiv gelöscht (Pre-Mortem 2).
- `backend/requirements.txt`: `python-multipart==0.0.9` ergänzt (zwingend für `UploadFile`, war bisher nicht vorhanden).
- `backend/tests/test_us120.py`: neu, 12 pytest-Fälle (Host-Pflicht, Größenobergrenze, ungültige Datei, Kompression, Ersetzen löscht Alt-Datei, EXIF-Rotation u. a.).
- `web/index.html`: `API.postFile()` (FormData-Upload statt JSON), CSS für Bildfläche/Platzhalter/Verarbeitungs-Overlay, `LocationDetail._imageAreaHtml/triggerImageUpload/_onImageFileSelected`, Einbindung vor dem Hero-Block.
- **Nachtrag (2026-07-04, von Stephan ausdrücklich freigegeben, reine Ergänzung):** `DELETE /locations/{id}` in `backend/main.py` entfernt jetzt auch die zugehörige Bilddatei (`image_filename`), sobald eine Location final aus der Datenhaltung entfernt wird (Custom Location: SQLite-Löschung; Standard-Location: Tombstone-Override, gilt hier ebenfalls als final, da die Location für alle Nutzer dauerhaft verschwindet und niemand das Bild wieder sichtbar machen kann). Wiederverwendet dasselbe Lösch-Pattern (`_delete_location_image_file`) wie beim Ersetzen eines Bildes beim Upload — fehlertolerant, kein 500er falls die Datei bereits fehlt. Löst den unten offen notierten Punkt 2.

**Validierungsstand (final, 2026-07-04):** Vollständig getestet und grün — automatisiert (12/12 pytest, nach Behebung eines Test-Fixture-Bugs, siehe Testplan), manuell per curl (Upload, Ersetzen ohne Dateileiche, Ablehnung ohne Token/ungültige Datei/Übergröße, Löschen entfernt Bild) und im Browser (Hero-Anzeige, mittige Einpassung bei Fenstergrößenänderung, Host- vs. Nicht-Host-Ansicht, Platzhalter, Regressionscheck Bearbeiten). Offen bleibt nur ein echter Handyfoto-Test mit tatsächlicher EXIF-Rotation (die zugrundeliegende Logik ist automatisiert getestet, s. Testplan).

**Zwei Vorschläge außerhalb des Ticket-Scopes — beide von Stephan entschieden (2026-07-04):**
1. Backup um `location_images/` erweitern → **Ja** — dafür angelegt: **TASK-55** (Inbox).
2. `DELETE /locations/{id}` soll die Bilddatei mitlöschen → **Ja** — bereits umgesetzt, siehe Implementierungsnotiz-Nachtrag oben.

**Release-Befund (2026-07-04):** Der Deploy scheiterte zunächst am Installieren der neuen Abhängigkeit `python-multipart` — der komplette `site-packages`-Ordner des Server-venv gehörte `root` statt `fotoalert` (vermutlich aus einer früheren manuellen Root-Installation), zusätzlich hatte ein erster fehlgeschlagener Versuch die RECORD-Datei einer älteren `python-multipart`-Version zerstört. Behoben durch `chown -R fotoalert:fotoalert` auf das gesamte venv (Root) + `pip install --ignore-installed`. Das betrifft potenziell jeden künftigen Deploy mit neuer Abhängigkeit, nicht nur dieses Ticket — als generelle Server-Absicherung für die Retro vormerken. Deploy danach vollständig verifiziert: `/health` grün, `image_url`-Feld live in `GET /locations` vorhanden.

---

### US-121 · Chancen automatisch neu berechnen bei Änderung des Location-Standorts `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-04 |
| **Ergebnis** | Als Dublette geschlossen — kein Code geändert. Automatische Neuberechnung bei Standort-Änderung existiert bereits vollständig (TASK-12 + US-106), siehe Spec unten. |

**Beschreibung:** Als Fotograf möchte ich, dass alle Foto-Chancen automatisch neu berechnet werden, wenn der Standort des Motivs oder Fotografen einer bestehenden Location geändert wird, damit die Chancen nie auf veralteten Koordinaten basieren.

**Bezug:** Starke Überschneidung mit **TASK-12** [x] (Done, v1.4.2 — führte bereits automatische Neuberechnung von Feed + Jahreskalender nach Koordinaten-Änderung ein: asynchroner `_run_precompute(location_ids=[id])` direkt nach PATCH `/locations/{id}`) und **US-106** [x] (Done, v1.19.5, baut auf TASK-12 auf und schließt drei weitere Lücken: Wetter sofort, Entdecken-Bereich zeitnah, kein Verlust bei laufendem Großlauf). Nach Aktenlage im Backlog **scheint automatische Neuberechnung bereits zu existieren** — abschließend nur durch Stephan/Live-Test zu bestätigen.

**Klärungsbedarf (nicht selbst entschieden, bitte vor Analyse klären):**
- (a) Passiert die automatische Neuberechnung bei Standort-Änderung bereits vollständig (TASK-12 + US-106 scheinen das laut Backlog-Text bereits zu leisten) — oder gibt es einen Rest-Fall, der noch nicht abgedeckt ist?
- (b) Falls doch eine Lücke besteht: Soll die Neuberechnung über denselben „Alignment berechnen"-Button laufen wie bei Neuanlage (Risiko: User löst ihn nach einer Änderung evtl. nicht erneut aus → veraltete Daten bleiben stehen), oder soll sie automatisch bei jeder Änderung erfolgen, mit kurzem Hinweis-Toast („Chancen werden aktualisiert")?

---

#### 📋 Spec (Analyse-Phase, 2026-07-04)

**Code-Befund vorab (bestimmt den gesamten Rest der Analyse):**
Die Code-Recherche zeigt eindeutig: **Die automatische Neuberechnung bei Standort-Änderung existiert bereits vollständig — für beide im Ticket genannten Fälle.** Dieses Ticket beschreibt keine Lücke, sondern eine **vollständige Dublette** von bereits ausgeliefertem, funktionierendem Code (TASK-12, v1.4.2, + US-106, v1.19.5). Belege:

- `backend/main.py`, PATCH-Route für eine Location (Zeile 2169 ff.): Die Liste der Felder, bei deren Änderung automatisch neu gerechnet wird, umfasst ausdrücklich **beide** Standort-Arten — die Koordinaten des Fotografen-Standpunkts (`observer_lat`, `observer_lon`) **und** die Koordinaten des Motivs (`subject_lat`, `subject_lon`). Es gibt keine Unterscheidung, bei der nur einer der beiden Punkte einen Neustart auslöst — beide tun es, einzeln wie gemeinsam geändert.
- Direkt nach dem Speichern der Änderung wird — sofern eine der vier Koordinaten (oder Höhenkorrektur/Brennweiten-Empfehlung) betroffen ist — automatisch und ohne weiteres Zutun eine Neuberechnung genau für diese eine Location angestoßen (kein Warten auf den nächsten großen Nachtlauf).
- Es gibt **keinen zweiten Bearbeitungsweg** für bestehende Locations im Backend außer dieser einen Route — alle Änderungen an Koordinaten einer bestehenden Location laufen über denselben Codepfad, es existiert kein Nebenpfad, der den Trigger umgeht.
- Sichtbare Nutzer-Rückmeldung ist bereits vorhanden: Die betroffene Location wird sofort in eine „wird noch aktualisiert"-Merkliste aufgenommen, die das Frontend abfragt und daraus ein Banner anzeigt. Laut der US-106-Spec (siehe dort, bereits umgesetzt) bleibt dieses Banner ehrlich stehen, bis Chancen, Kalender **und** Wetter für die Location wirklich fertig sind — es verschwindet nicht vorzeitig bei einem Platzhalterwert.
- Zusätzlich sorgt US-106 dafür, dass auch der Entdecken-Bereich zeitnah nachzieht und dass eine Änderung während eines laufenden großen Hintergrundlaufs nicht verloren geht, sondern automatisch nachgeholt wird.

**Beantwortung der beiden Klärungsfragen aus dem Ticket:**
- **(a)** Ja — die automatische Neuberechnung bei Standort-Änderung passiert bereits vollständig, für Fotografen-Standort **und** Motiv-Standort, über den einzigen vorhandenen Bearbeitungsweg, inklusive sichtbarem Hinweis („wird noch aktualisiert") bis alles wirklich fertig ist. Es wurde kein Rest-Fall gefunden, der nicht abgedeckt wäre.
- **(b)** Entfällt — da keine Lücke besteht, stellt sich die Entscheidungsfrage „Button vs. automatisch mit Toast" nicht. Der bereits gebaute Weg ist ohnehin die zweite genannte Variante (automatisch bei jeder Änderung, mit Hinweis statt Button).

**Empfehlung:** Ticket als Dublette schließen, kein Code ändern. Die untenstehenden Akzeptanzkriterien dienen als **Verifikations-AKs** — ein kurzer Live-Test durch Stephan bestätigt, dass das beschriebene Verhalten tatsächlich so funktioniert, bevor das Ticket auf Done gesetzt wird.

**Akzeptanzkriterien (Verifikation, kein Bau-Auftrag):**
- [ ] Wird bei einer bestehenden Location der Standpunkt des Fotografen verschoben, erscheint kurz danach ein Hinweis, dass diese Location gerade aktualisiert wird — ohne dass Stephan etwas zusätzlich anstoßen muss.
- [ ] Wird stattdessen (oder zusätzlich) der Standort des Motivs verschoben, passiert dasselbe: automatischer Hinweis, automatische Neuberechnung, kein Unterschied im Verhalten gegenüber einer Fotografen-Standort-Änderung.
- [ ] Nach Abschluss der Aktualisierung verschwindet der Hinweis, und die Foto-Chancen dieser Location zeigen Werte, die zu den neuen Koordinaten passen (nicht mehr die alten).
- [ ] Edge: Werden Fotografen- und Motiv-Standort in einem Zug geändert, läuft nur eine Aktualisierung für diese Location an (kein doppelter/überflüssiger Lauf).
- [ ] Edge: Ändert Stephan eine Location, während gerade eine große nächtliche Aktualisierung läuft, bleibt der Hinweis stehen und seine Änderung wird automatisch nachgeholt, sobald der große Lauf fertig ist (bereits durch US-106 abgedeckt).

**Analyse & Planung:**
- [x] Example Mapping: entfällt — keine neue Funktionalität, siehe Code-Befund oben.
- [x] Pre-Mortem: entfällt aus demselben Grund.
- [x] Architektur analysiert: `backend/main.py` (PATCH-Route für Locations, Zeilen ~2169–2242), Bezug zu TASK-12- und US-106-Spec (BACKLOG.md, US-106-Abschnitt).
- [x] Designer-Check: nicht visuell (kein neues UI-Element, bestehendes Banner wird nur bestätigt) → übersprungen.
- [x] Implementierungsoptionen: entfällt — kein Bau-Auftrag.
- [x] Empfehlung: Als Dublette schließen nach Stephans Live-Test-Bestätigung.

**Testplan:**
- [ ] Manuell (unter http://localhost:8000 bzw. live): Bei einer bestehenden Location einmal nur den Fotografen-Standort und einmal nur den Motiv-Standort ändern, jeweils prüfen ob der „wird aktualisiert"-Hinweis erscheint und nach Abschluss wieder verschwindet, und ob die neuen Chancen zu den neuen Koordinaten passen.
- [ ] Kein neuer automatisierter Test nötig — bestehende Tests zu TASK-12/US-106 (`backend/tests/test_us106.py`) decken den Mechanismus bereits ab.

---

### US-122 · Sonnen-Alignment als eigenständige Chance in Feed, Kalender und Scout `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-04 |
| **Ergebnis** | Als Dublette geschlossen — kein Code geändert. Sonnen-Alignment existiert bereits vollständig (Backend, Feed, Kalender, Scout, Filter-UI), siehe Spec unten. |

**Beschreibung:** Als Fotograf möchte ich Sonnen-Alignment als eigenständige Chance im 14-Tage-Feed, im Kalender und bei den Scouts sehen — nach derselben Logik wie das bestehende Mond-Alignment, nur zur goldenen Stunde (blaue Stunde entfällt, da die Sonne dann nicht sichtbar ist) — mit Filterkriterien analog zu den bestehenden Mond-Filtern (Drei-Zustand: aktivieren/ausschließen/neutral).

**Bezug:** Wichtiger Klärungspunkt vor Analyse: Der Event-Typ `SUN_ALIGNMENT` wird laut Code-Referenzen im Backlog (Kontext zu **US-108** [x]) bereits **bestehend** neben `MOON_ALIGNMENT` erwähnt („Golden Hour, Blue Hour, SUN_ALIGNMENT, MOON_ALIGNMENT, Milchstraße, Meteoritenschauer werden durch US-108 nicht verändert"). Zusätzlich ist **US-107** [x] (Done, released 2026-06-29, „Sonnen-Alignment-Planung") bereits umgesetzt — dort aber als Richtungsklassifizierungs-Text im Event-/Location-Detail (z. B. „Sonne geht fast genau hinter dem Motiv auf"), **nicht** explizit als eigenständige Feed-/Kalender-/Scout-Karte mit eigenem Icon wie bei Mond-Alignment. Es ist unklar, ob dieses Ticket eine Dublette von bereits bestehendem `SUN_ALIGNMENT`-Code ist oder eine echte Lücke (fehlende Sichtbarkeit in Feed/Kalender/Scout speziell zur goldenen Stunde) beschreibt — vor Analyse-Start unbedingt am Code prüfen, nicht nur am Backlog-Text. Nur als Kontext/Konsistenz-Hinweis (nicht zur Umsetzung in diesem Intake-Schritt): Das Drei-Zustand-Filterpattern ist bereits etabliert, siehe **BUG-46** [x] (Done — führte aktiv/ausgeschlossen/deaktiviert für mehrere Kriterien ein) und den Verifikationsfilter (`verificationIncl[]`/`verificationExcl[]`).

---

#### 📋 Spec (Analyse-Phase, 2026-07-04)

**Code-Befund vorab (bestimmt den gesamten Rest der Analyse):**
Die Code-Recherche zeigt eindeutig: **`SUN_ALIGNMENT` ist bereits vollständig als eigenständige Chance implementiert — identisch zu `MOON_ALIGNMENT` — in Backend-Erzeugung, Feed, Kalender, Scout UND Filter-UI.** Dieses Ticket beschreibt keine Lücke, sondern eine **vollständige Dublette** von bereits ausgeliefertem, funktionierendem Code. Belege:
- `backend/calculations/opportunity.py` Zeile 45/46: `SUN_ALIGNMENT` und `MOON_ALIGNMENT` sind gleichrangige Werte im `EventType`-Enum.
- Zeile 504–616: Die 3D-Präzisions-Alignment-Schleife berechnet Sonne UND Mond nach identischer Logik (`for body_key, body_label, event_type_val, is_solar in [("sun", …, EventType.SUN_ALIGNMENT, True), ("moon", …, EventType.MOON_ALIGNMENT, False)]`), inklusive Sonnen-spezifischem Altitude-Filter (Zeile 522: „nicht zu hoch, sonst kein dramatisches Licht" — faktisch golden-hour-artige Einschränkung) und explizitem ND-Filter-Warnhinweis für Sonne.
- Zeile 618–653: Fallback-Pfad ohne 3D-Gebäudedaten erzeugt `SUN_ALIGNMENT` weiterhin eigenständig über `find_sun_alignment_times()`.
- Beide Pfade filtern bereits über `_in_photo_window(…, sun)` auf goldene/blaue Stunde — für die Sonne ist blaue Stunde durch den Altitude-Gate (`0 < sun_pos.altitude < 15` bzw. `celestial_altitude > 20` → verworfen) faktisch ausgeschlossen, weil die Sonne in der blauen Stunde bereits unter dem Horizont steht. Die im Ticket geforderte Einschränkung „nur goldene Stunde, keine blaue Stunde" ist also bereits Ist-Verhalten, nicht zu bauen.
- `backend/discover/sun_pipeline.py` (gesamte Datei, referenziert als „US-81"): eigenständige, zu `moon_pipeline.py` parallele Scout-Pipeline für Sonnen-Alignment-Chancen, inkl. eigener Gauß-Score-Kurve, eigenem Altitude-Gate (`SUN_ALT_MIN_DEG = 0.5`) und eigener Brennweitenberechnung. `backend/discover/pipeline.py` Zeile 39–41 führt `moon_pipeline.run()` und `sun_pipeline.run()` per `asyncio.gather` parallel aus und mischt beide Ergebnislisten für den Scout-Cache.
- `backend/precompute.py` Zeile 833–839 (Kalender) und Zeile 988–990 (Feed) rufen beide `find_opportunities(...)` bzw. `find_opportunities_multi_day(...)` auf — denselben Generator, der oben `SUN_ALIGNMENT` erzeugt. `astronomy_only=True` schaltet nur die Wetter-Bewertung ab (opportunity.py Zeile 337), nicht die Event-Typ-Erzeugung. Der Qualitätsfilter `_passes_alignment_filter()` (precompute.py Zeile 99–121) prüft Azimut-/Höhentoleranz generisch für alle Alignment-Typen, ohne `SUN_ALIGNMENT` auszunehmen oder zu benachteiligen.
- `web/index.html` Zeile 1424: eigenes Icon `i-sun` für `Sonnen-Alignment` (analog Zeile 1423 `i-moon` für `Mond-Alignment`).
- `web/index.html` Zeile 2807–2822 (`FilterSheet._ET`): `Sonnen-Alignment` ist bereits ein eigener Eintrag in derselben Chip-Liste wie `Mond-Alignment` — diese Liste speist Feed-, Kalender- und Scout-Filter gemeinsam (generischer `event_type`-String-Vergleich in `Filter.apply()`, Zeile 2608–2623).
- `web/index.html` Zeile 2745–2752: Das **Drei-Zustand-Filterpattern** (aktiv/ausgeschlossen/neutral) ist für `Sonnen-Alignment` bereits identisch zu `Mond-Alignment` verdrahtet — sowohl `eventTypes`-Include- als auch `eventTypesExcl`-Exclude-Set (US-71) behandeln beide Alignment-Typen gleich, es gibt keinen separaten `sunAlignmentIncl[]`/`sunAlignmentExcl[]`-State (anders als beim Verifikationsfilter) — die Drei-Zustand-Logik läuft generisch über den `event_type`-String, das bestehende `verificationIncl[]`/`verificationExcl[]`-Pattern ist hier nicht das relevante Vorbild, sondern das bereits aktive generische `eventTypes`/`eventTypesExcl`-Array.
- `BACKLOG.md` Zeile 6468 (US-108-Spec, Done, released 2026-06-30): listet `SUN_ALIGNMENT` explizit als bereits bestehenden, von US-108 unberührten Event-Typ neben `MOON_ALIGNMENT` — bestätigt unabhängig vom jetzt gelesenen Code, dass die Backlog-Historie korrekt war.

**Einordnung der beiden im Ticket erwähnten Altsysteme:**
- **US-107** (Done, 2026-06-29) ist unabhängig davon: Richtungsklassifizierungs-Text im Location-/Event-Detail („Sonne geht fast genau hinter dem Motiv auf"). Das ist reine Text-Anreicherung eines bereits geöffneten Details, keine Feed-/Kalender-/Scout-Kartendarstellung — deckt sich nicht mit dem, was dieses Ticket fordert, aber ist auch keine Lücke, weil die Kartendarstellung bereits an anderer Stelle existiert (siehe oben).
- **US-108** (Done, 2026-06-30) filtert nur `MOON_RISE`/`MOON_SET` nach Azimut-Zonen und erwähnt `SUN_ALIGNMENT` nur beiläufig als unverändert — bestätigt aber dessen Existenz.

**Example Mapping**

Da der Code-Befund zeigt, dass die geforderte Funktionalität bereits vollständig existiert, entfällt ein reguläres Example Mapping für neue Regeln. Stattdessen wird die Ticket-Beschreibung Punkt für Punkt gegen das Ist-Verhalten gespiegelt:

- **Rule 1 — Sonnen-Alignment als eigenständige Chance im 14-Tage-Feed:** ✅ bereits erfüllt. Der Feed (`/opportunities`, gespeist über `find_opportunities_multi_day`) enthält `SUN_ALIGNMENT`-Events mit eigenem Titel, eigener Beschreibung und eigenem `event_type`-Feld — nicht in „Goldene Stunde" verschmolzen.
  - Beispiel: Fotograf öffnet den 14-Tage-Feed, aktiviert im Filter „Sonnen-Alignment" → sieht Karten mit Titel „Sonne [Ausrichtung] – [Motivname]" und Sonnen-Icon, getrennt von Goldene-Stunde-Karten.
- **Rule 2 — Sonnen-Alignment im Kalender:** ✅ bereits erfüllt. Derselbe Berechnungspfad speist den Jahreskalender (`compute_calendar_incremental` → `find_opportunities(astronomy_only=True)`).
  - Beispiel: Fotograf blättert im Kalender zu einem Tag mit Sonnen-Alignment-Chance an einer 3D-vermessenen Location → Kalendertag zeigt einen Sonnen-Alignment-Eintrag mit Sonnen-Icon.
- **Rule 3 — Sonnen-Alignment bei den Scouts:** ✅ bereits erfüllt. `sun_pipeline.py` läuft parallel zu `moon_pipeline.py` und liefert eigene Scout-Chancen für die Sonne.
  - Beispiel: Fotograf öffnet den Scout-Tab, filtert auf „Sonne" als Himmelskörper → sieht Sonnen-Alignment-Vorschläge mit Brennweitenempfehlung, unabhängig von Mond-Vorschlägen.
- **Rule 4 — Nur goldene Stunde, keine blaue Stunde:** ✅ bereits erfüllt, allerdings nicht durch eine explizite Ausschlussregel, sondern als Konsequenz der Astronomie: Der Altitude-Gate für Sonnen-Alignment (Sonne muss über dem Horizont, aber nicht zu hoch stehen) greift nur während der goldenen Stunde; zur blauen Stunde steht die Sonne bereits unter dem Horizont und erzeugt keine Alignment-Treffer.
  - Beispiel: Fotograf sucht im Feed nach Sonnen-Alignment-Chancen während der blauen Stunde → findet keine, weil die Sonne dann nicht sichtbar ist (physikalisch ausgeschlossen, nicht durch einen Software-Filter).
- **Rule 5 — Filterkriterien im Drei-Zustand analog zu Mond:** ✅ bereits erfüllt. „Sonnen-Alignment" ist ein Chip in derselben Filterliste wie „Mond-Alignment" mit identischem Include-/Exclude-/Neutral-Verhalten (kein Sonderfall, keine Einschränkung gegenüber Mond).
  - Beispiel: Fotograf tippt zweimal auf den „Sonnen-Alignment"-Chip → Zustand wechselt von neutral → aktiv → ausgeschlossen, exakt wie beim „Mond-Alignment"-Chip.

Keine offenen ❓ Questions zum Soll-Verhalten — der einzige Klärungsbedarf ist die Konsequenz aus dem Befund (siehe „Empfehlung" unten).

**Akzeptanzkriterien**

Da keine neue Funktionalität fehlt, sind dies **Verifikations-AKs** (Regressionstest gegen den bestehenden Stand), keine Bau-AKs:

- [ ] AK1: Im 14-Tage-Feed erscheinen bei mindestens einer 3D-vermessenen Location eigene Sonnen-Alignment-Karten mit Sonnen-Icon, getrennt von Goldene-Stunde-Karten.
- [ ] AK2: Im Jahreskalender erscheint an einem Tag mit passender Geometrie ein Sonnen-Alignment-Eintrag mit Sonnen-Icon.
- [ ] AK3: Im Scout-Tab erscheinen bei Filterung auf „Sonne" eigenständige Sonnen-Alignment-Vorschläge, unabhängig von Mond-Vorschlägen.
- [ ] AK4: Der Filter-Chip „Sonnen-Alignment" existiert in Feed, Kalender und Scout und verhält sich im Drei-Zustand (aktiv/ausgeschlossen/neutral) identisch zum „Mond-Alignment"-Chip.
- [ ] Edge Case: Wird „Sonnen-Alignment" ausgeschlossen (Exclude-Zustand), verschwinden alle Sonnen-Alignment-Karten aus Feed/Kalender/Scout, während Mond-Alignment-Karten unverändert sichtbar bleiben.
- [ ] Edge Case: Für die blaue Stunde erscheint nie eine Sonnen-Alignment-Karte (weder im Feed noch im Kalender noch im Scout), weil die Sonne dann nicht über dem Horizont steht.

**Pre-Mortem (Code-gestützt)**

📎 Code-Verifikation: `backend/calculations/opportunity.py`, `backend/discover/sun_pipeline.py`, `backend/discover/pipeline.py`, `backend/precompute.py`, `web/index.html` (Zeilen wie oben zitiert) gelesen am 2026-07-04. Bestätigt: `SUN_ALIGNMENT` ist in allen drei Einstiegspunkten (Feed, Kalender, Scout) bereits aktiv und im Frontend-Filter identisch zu `MOON_ALIGNMENT` verdrahtet. Widerlegt: die Ticket-Prämisse „Sonnen-Alignment fehlt als eigenständige Chance" — dieser Zustand existiert nicht, das Feature ist bereits im Live-Code (zuletzt laut BACKLOG-Historie über US-107/US-108, jeweils Done, released 2026-06-29/2026-06-30).

1. 💀 Szenario: Ticket wird trotz Dublette wie beschrieben „umgesetzt" — ein Subagent baut versehentlich einen zweiten, parallelen `SUN_ALIGNMENT`-Erzeugungspfad (z. B. weil er den bestehenden `sun_pipeline.py`/`opportunity.py`-Code nicht findet oder für unvollständig hält).
   Auslöser: Keine Code-Verifikation vor Implementierungsstart, Vertrauen auf den Ticket-Text statt auf den Code.
   Frühwarnung: Doppelte Sonnen-Alignment-Karten für dieselbe Location/Zeit im Feed, doppelte Einträge im Scout-Cache mit leicht unterschiedlichem Scoring.
   Gegenmaßnahme: Dieses Ticket wird NICHT implementiert, sondern mit dem Befund an Stephan zurückgespielt (siehe Empfehlung).
2. 💀 Szenario: Stephan bestätigt versehentlich eine „Implementierung", die in Wahrheit nur bestehenden Code geringfügig umbenennt oder dupliziert, wodurch zwei leicht unterschiedliche Codepfade für dasselbe Konzept entstehen (Wartungslast, Divergenzrisiko bei künftigen Bugfixes).
   Auslöser: Weg-Gate wird ohne den vollständigen Code-Befund gestellt.
   Frühwarnung: `grep -rn "SUN_ALIGNMENT"` liefert nach einer „Implementierung" mehr als die aktuell vier Fundstellen-Cluster (opportunity.py, sun_pipeline.py, discover/pipeline.py, index.html).
   Gegenmaßnahme: Diese Spec macht den Befund explizit und schlägt vor, das Ticket zu schließen statt zu implementieren.
3. 💀 Szenario: Stephan hat bei Freigabe des Tickets ein *tatsächliches* Verhaltensproblem im Kopf gehabt (z. B. „Sonnen-Alignment-Karten sehen im Feed uninteressant/unauffällig aus" oder „ich sehe sie in der Praxis nie"), das der Ticket-Text unpräzise als „fehlt komplett" beschrieben hat — die Dublette wäre dann nur ein Formulierungsproblem, nicht die eigentliche Anforderung.
   Auslöser: Ticket wurde vor Analyse nicht gegen den Live-Zustand der App geprüft (nur gegen Backlog-Text).
   Frühwarnung: Manuelles Nachschauen im Feed/Kalender/Scout zeigt evtl., dass Sonnen-Alignment-Karten zwar technisch erzeugt werden, aber selten/nie auftreten (z. B. weil kaum Locations 3D-Gebäudedaten haben und der Fallback-Pfad selten `min_score` erreicht) — das wäre dann ein Datenabdeckungs- oder Sichtbarkeitsproblem, kein fehlendes Feature.
   Gegenmaßnahme: Als offene Klärungsfrage an Stephan zurückspielen (siehe unten) statt den Code-Befund unkommentiert als alleinige Antwort zu präsentieren.

**Architektur-Analyse (intern, technische Namen erlaubt)**

Bereits bestehende, vollständige Implementierung von `SUN_ALIGNMENT` (kein Neubau nötig):
- `backend/calculations/opportunity.py` — `EventType.SUN_ALIGNMENT` (Zeile 45), 3D-Alignment-Schleife (Zeile 504–616, körper-generisch für Sonne+Mond), Fallback-Azimut-Pfad (Zeile 618–653, `find_sun_alignment_times`).
- `backend/calculations/astronomy.py` — `find_sun_alignment_times()`, `find_precise_alignment_times()` (körper-generisch, `body="sun"`/`"moon"`), `calculate_sun_info()` liefert golden/blue-hour-Fenster.
- `backend/discover/sun_pipeline.py` — komplette eigenständige Scout-Pipeline für Sonne (Gauß-Score, Altitude-Gate, Brennweitenberechnung), analog `moon_pipeline.py`.
- `backend/discover/pipeline.py` Zeile 39–62 — führt `moon_pipeline.run()` und `sun_pipeline.run()` parallel aus, mischt Ergebnisse in den Scout-Cache.
- `backend/precompute.py` Zeile 783–850 (`_compute_calendar_for_location`) und Zeile 983–1000 (`_run_single_location_recompute` Feed-Teil) — rufen den gemeinsamen Generator auf, der `SUN_ALIGNMENT` bereits liefert; `_passes_alignment_filter()` (Zeile 99–121) behandelt alle Alignment-Typen gleich.
- `web/index.html` — Icon-Mapping Zeile 1420–1429 (`i-sun` für „Sonnen-Alignment"), Filter-Chip-Liste `FilterSheet._ET` Zeile 2807–2822, generische Drei-Zustand-Filterlogik `Filter.apply()`/`applyToScout()` Zeile 2608–2780 (arbeitet auf `event_type`-Strings, kein Sonderfall nötig).

Kein neuer Code, keine neuen Dateien, keine neuen Funktionen identifiziert, die für die im Ticket beschriebene Funktionalität fehlen würden.

**Implementierungsoptionen**

*Option A — Ticket als Dublette schließen, kein Code ändern*
In Alltagssprache: Die App zeigt Sonnen-Alignment bereits heute als eigenständige Chance im Feed, Kalender und bei den Scouts, mit eigenem Icon und eigenem Drei-Zustand-Filter — Stephan kann das im laufenden Betrieb direkt nachprüfen. Es gibt nichts zu bauen.

| Aspekt | Bewertung |
|---|---|
| Technischer Ansatz | Keine Codeänderung. Ticket-Status auf „Done" bzw. „Verworfen (Dublette)" mit Verweis auf US-107/US-108/US-81 (Scout-Sonnenpipeline) |
| Aufwand | Keiner |
| Risiko | Keines — es wird nichts angefasst |

*Option B — Gezielte Prüfung + kleine Sichtbarkeits-/Qualitätsverbesserung, falls sich Rule/AK gegen den Live-Zustand als unzureichend erweist*
In Alltagssprache: Stephan schaut sich im laufenden Betrieb aktiv im Feed/Kalender/Scout um, ob Sonnen-Alignment-Karten tatsächlich auftauchen. Falls sie technisch zwar existieren, aber in der Praxis kaum sichtbar sind (z. B. weil zu wenige Locations 3D-Gebäudedaten für den präzisen Pfad haben), wird das als neues, eng abgegrenztes Ticket (z. B. „Sonnen-Alignment-Sichtbarkeit erhöhen") separat behandelt — nicht als Neuimplementierung von US-122.

| Aspekt | Bewertung |
|---|---|
| Technischer Ansatz | Manuelle Stichprobe (Feed/Kalender/Scout-Tab, Filter „Sonnen-Alignment" aktivieren) vor endgültiger Entscheidung |
| Aufwand | Sehr klein (Live-Check, keine Implementierung in diesem Schritt) |
| Risiko | Keines für den bestehenden Code; verhindert vorschnelles Schließen falls doch ein reales Sichtbarkeitsproblem vorliegt |

**Empfehlung:** Option A, ergänzt um den Live-Check aus Option B als letzten Schritt vor dem Schließen. Der Code-Befund ist eindeutig und mehrfach belegt (Backend-Enum, zwei unabhängige Erzeugungspfade, eigene Scout-Pipeline, Frontend-Icon, Frontend-Filter-Chip, Drei-Zustand-Logik) — eine Implementierung würde bestehenden, funktionierenden Code duplizieren (Pre-Mortem Szenario 1/2). Vor dem endgültigen Schließen empfiehlt sich aber ein kurzer Live-Blick in Feed/Kalender/Scout, um Pre-Mortem-Szenario 3 auszuschließen (Sichtbarkeits- statt Existenzproblem).

**Offene Klärungsfrage an Stephan (statt Weg-Gate):**
- ❓ Meintest du mit diesem Ticket wirklich, dass Sonnen-Alignment als Konzept komplett fehlt — oder ist dir beim Nutzen der App aufgefallen, dass die bestehenden Sonnen-Alignment-Karten selten/nie auftauchen bzw. sich anders verhalten als erwartet (z. B. seltener als Mond-Alignment, obwohl beide dieselbe Logik nutzen sollten)? Falls Letzteres: bitte kurz beschreiben, wo/wann du das beobachtet hast — dann wird daraus ein neues, präzises Ticket statt einer Neuimplementierung von bereits vorhandenem Code.

**Testplan-Grundgerüst**

- Manuell: Feed-Tab öffnen, Filter „Sonnen-Alignment" aktivieren → mindestens eine Karte mit Sonnen-Icon sichtbar (bei ausreichend Zeitraum/Locations mit 3D-Daten).
- Manuell: Kalender-Tab, Monat mit bekannter Sonnen-Alignment-Chance öffnen → Eintrag mit Sonnen-Icon sichtbar.
- Manuell: Scout-Tab, Körper-Filter auf „Sonne" stellen → eigenständige Sonnen-Vorschläge sichtbar, unabhängig von Mond.
- Manuell: „Sonnen-Alignment"-Chip zweimal antippen (aktiv → ausgeschlossen) → Sonnen-Karten verschwinden aus Feed/Kalender/Scout, Mond-Karten bleiben unverändert.
- pytest: Kein neuer Testfall nötig, da keine neue Funktionalität entsteht; bestehende Tests (`backend/tests/test_moon_phase_events.py` als Vorbild) könnten um einen analogen `test_sun_alignment_events.py`-Smoke-Test ergänzt werden, falls noch keine Regressionsabdeckung für `SUN_ALIGNMENT` existiert — das wäre optional und nur bei Bedarf, kein Bestandteil dieses Tickets.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (als Ist-Zustand-Abgleich, da keine neuen Regeln nötig)
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `backend/calculations/opportunity.py`, `backend/calculations/astronomy.py`, `backend/discover/sun_pipeline.py`, `backend/discover/pipeline.py`, `backend/precompute.py`, `web/index.html`
- [x] Designer-Check: nicht visuell neu (kein neues Element, bestehendes Icon/Chip) → übersprungen
- [x] Implementierungsoptionen: A / B
- [x] Empfehlung: Option A (Ticket als Dublette schließen, kein Code ändern) + kurzer Live-Check vor endgültigem Schließen

---

### US-123 · Kartenansicht: Standardansicht (Straßenkarte) als Alternative zur Satellitenansicht `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-07-04 |
| **Abgeschlossen** | 2026-07-04 |

**Beschreibung:** Als Host möchte ich bei Neuanlage/Bearbeiten einer Location neben der Satellitenansicht auch eine Standardansicht (Straßenkarte) wählen können, mit Umschaltmöglichkeit zwischen beiden, damit ich je nach Situation die besser lesbare Kartendarstellung nutzen kann.

**Bezug:** Die Bearbeiten-Karte nutzt laut Backlog-Referenzen aktuell fix einen Satelliten-Layer (`CameraFOV.initMap()` verwendet `arcgisonline` fix). Der allgemeine Karten-Tab hat laut PRODUCT.md-Regressionshinweis (Zeile „Layer-Umschaltung Nacht/Standard/Satellit") bereits eine Layer-Umschaltung — diese Umschaltmöglichkeit scheint aber nicht für die Location-Anlage-/Bearbeiten-Karte selbst zu gelten, nur für den normalen Karten-Tab. Keine Dublette gefunden; Abgrenzung zu klären: ob die bestehende Karten-Tab-Layer-Umschaltung einfach auf die Bearbeiten-Karte übertragen werden kann (dann kleiner Aufwand) oder ob dort eine eigene Lösung nötig ist.

---

#### 📋 Spec (Analyse-Phase, 2026-07-04)

**Example Mapping**

- **Rule 1 — Umschalten in der Bearbeiten-Karte:** Beim Anlegen oder Bearbeiten einer Location kann der Host zwischen Satelliten- und Straßenkartenansicht wechseln.
  - Beispiel: Host öffnet „Neue Location", tippt auf den Umschalt-Button über der Karte → Ansicht wechselt sofort von Satellitenbild zu Straßenkarte (Pins, Sichtachse und alle bereits gesetzten Punkte bleiben unverändert sichtbar).
  - Beispiel: Host bearbeitet eine bestehende Location, wechselt auf Straßenkarte, verschiebt den Beobachter-Pin → Pin bleibt an der neuen Position, nur der Kartenhintergrund hat sich geändert.
- **Rule 2 — Konsistenz zwischen kleiner Karte und Vollbild-Karte derselben Sektion:** Wenn eine Sektion sowohl eine kleine Vorschau-Karte als auch eine dazugehörige Vollbild-Karte hat (z. B. Blickwinkel-Kegel-Vorschau + deren Vollbildansicht, oder Bearbeiten-Mini-Karte + deren Vollbildansicht), zeigen beide denselben Kartentyp.
  - Beispiel: Host schaltet in der kleinen Kegel-Vorschau auf Straßenkarte, öffnet danach die Vollbildansicht derselben Karte → Vollbild zeigt ebenfalls Straßenkarte, nicht wieder Satellit.
  - ❓ Noch zu klären: Soll die Wahl auch über verschiedene Sektionen hinweg gelten (z. B. Anlegen-Karte UND Bearbeiten-Karte UND Kegel-Vorschau alle gemeinsam), oder darf jede Sektion ihren eigenen zuletzt gewählten Stand haben? (siehe Pre-Mortem/Optionen unten)
- **Rule 3 — Merken der Wahl:** Die zuletzt gewählte Ansicht (Satellit oder Straßenkarte) bleibt auch nach Schließen und erneutem Öffnen der Bearbeiten-Karte erhalten, statt bei jedem Öffnen wieder auf Satellit zurückzuspringen.
  - Beispiel: Host stellt auf Straßenkarte um, schließt das Formular, öffnet später eine andere Location zum Bearbeiten → Karte startet direkt in Straßenkarten-Ansicht.
  - ❓ Noch zu klären: Soll sich diese Voreinstellung nur auf das jeweilige Gerät beziehen (lokal gespeichert) oder geräteübergreifend gelten? Code-Befund: der bestehende Karten-Tab merkt sich die Wahl aktuell überhaupt nicht (siehe Pre-Mortem Szenario 2) — das ist eine zusätzliche Verbesserung, kein Bestandsverhalten, das einfach übernommen werden kann.
- **Rule 4 — Abgrenzung zur bestehenden Karten-Tab-Umschaltung:** Die Umschaltung im normalen Karten-Tab bleibt unverändert bestehen; das Ticket betrifft ausschließlich die Karte(n) rund um Location-Anlage/-Bearbeitung.
  - Beispiel: Host wechselt im normalen Karten-Tab auf „Nacht"-Ansicht, öffnet danach „Neue Location" → die Location-Karte zeigt weiterhin ihre eigene zuletzt gewählte Ansicht (Satellit oder Straßenkarte), nicht die Nachtansicht — „Nacht" ist für die Location-Karten kein vorgesehener Modus (nur Satellit/Straßenkarte laut Ticket-Wortlaut).

**Akzeptanzkriterien**

- AK1: In der Karte beim Anlegen einer neuen Location gibt es einen sichtbaren Umschalter zwischen Satelliten- und Straßenkartenansicht.
- AK2: In der Karte beim Bearbeiten einer bestehenden Location gibt es denselben Umschalter.
- AK3: Ein Tippen auf den Umschalter wechselt die Kartenansicht sofort, ohne dass gesetzte Pins, Linien oder der Kartenausschnitt (Zoom/Position) verloren gehen.
- AK4: Falls zu einer Karte eine Vollbildansicht existiert (z. B. Blickwinkel-Kegel-Karte, Bearbeiten-Vollbildkarte): die Vollbildansicht zeigt denselben Ansichtsmodus wie die zugehörige kleine Karte, nicht wieder standardmäßig Satellit.
- AK5: Die zuletzt gewählte Ansicht bleibt erhalten, wenn der Host das Formular schließt und später erneut eine Location anlegt oder bearbeitet (auf demselben Gerät).
- AK6: Der normale Karten-Tab (Nacht/Standard/Satellit) verhält sich exakt wie bisher — keine Regression durch diese Änderung.
- AK7: ❓ Noch zu klären mit Stephan: Gilt AK5 (Merken) je Kartentyp einzeln (Anlegen-Karte, Bearbeiten-Karte, Kegel-Vorschau jeweils eigener Stand) oder als eine gemeinsame App-weite Einstellung für alle Location-bezogenen Karten? Empfehlung unten unter Option A/B.

**Pre-Mortem (Code-gestützt)**

1. **Vier bis fünf unabhängige Karten-Instanzen, nicht eine gemeinsame:** `CameraFOV.initMap()` (Panel, Zeile 3612–3625) und `CameraFOV._initMapFs()` (Vollbild, Zeile 3725–3741) sowie `AddLocation.initMap()` (Zeile 5737–5759), `LocationDetail._initEditMap()` (Zeile 5271–5299) und `LocationDetail._initEditMapFs()` (Zeile 5335–5353) haben JEDES für sich einen eigenen, wortgleich hartcodierten Aufruf `L.tileLayer('https://server.arcgisonline.com/.../World_Imagery/...')`. Es gibt **keine** gemeinsame Helper-Funktion für die Layer-Wahl (anders als z. B. `MapMarkers` oder `_drawPinsAndLine`, die bereits geteilt sind). Auslöser: naive Umsetzung ändert nur eine Stelle und vergisst die anderen vier. Frühwarnung: Test nur an einer Karte (z. B. nur Anlegen-Karte), Vollbild oder Bearbeiten-Karte bleiben unbemerkt beim alten Satelliten-Layer. Gegenmaßnahme: gemeinsame Helper-Funktion/-Konstante für die Layer-URLs einführen (analog `MapView.layers`) und an allen fünf Stellen einbinden; Testplan muss alle vier/fünf Karten einzeln abdecken.
2. **Bestehende Karten-Tab-Umschaltung merkt sich nichts:** `MapView.setLayer()` (Zeile 4278–4288) hält den State ausschließlich über die `.active`-CSS-Klasse am Button, es gibt kein `localStorage` oder sonstige Persistenz (Grep nach `localStorage.*Layer` und `mapLayer` ergab keinen Treffer). Auslöser: Team geht davon aus, man könne die bestehende Lösung 1:1 „übertragen" und bekäme Persistenz geschenkt. Frühwarnung: nach Reload/erneutem Öffnen der Location-Karte ist die Wahl wieder auf Satellit, obwohl AK5 das Gegenteil verlangt. Gegenmaßnahme: Persistenz (z. B. lokaler Speicher) ist eine NEUE Ergänzung, kein übernommenes Verhalten — muss explizit mitgeplant und in der Aufwandsschätzung berücksichtigt werden.
3. **Divergenz zwischen Panel- und Vollbildkarte derselben Sektion:** Die Kegel-Vorschau-Karte und ihre Vollbildvariante werden aus getrennten Funktionen aufgebaut (`initMap` vs. `_initMapFs`; ebenso `_initEditMap` vs. `_initEditMapFs`) und bauen ihre Layer unabhängig auf. Auslöser: Layer-Wahl wird nur an einer der beiden Funktionen geändert. Frühwarnung: Host schaltet in der kleinen Karte auf Straßenkarte, öffnet die Vollbildansicht — die zeigt aber wieder Satellit (Regression zu AK4). Gegenmaßnahme: State (aktueller Modus) muss zentral gehalten und von BEIDEN Init-Funktionen gelesen werden, nicht dupliziert.
4. **Tile-Filter-Nebenwirkung aus dem Karten-Tab:** `MapView.setLayer()` wendet für den „dark"-Modus einen CSS-Filter auf `.leaflet-tile` an (Zeile 4282–4285: `brightness(.85) saturate(.7)`), zusätzlich existiert eine globale Regel `.leaflet-tile { filter: brightness(.85) saturate(.7); }` (Zeile 266) für alle Karten. Auslöser: Wird beim Bau der Location-Karten-Umschaltung versehentlich derselbe generische Selektor `.leaflet-tile` verwendet, könnte ein Filter-Wechsel ungewollt alle Leaflet-Karten der Seite gleichzeitig beeinflussen (nicht nur die eine Location-Karte), da der Selektor nicht kartenspezifisch ist. Gegenmaßnahme: beim Umsetzen kartenspezifische Selektoren verwenden (z. B. über die Container-ID `#map_fov_${prefix}` statt global `.leaflet-tile`), oder bewusst DOM-Scoping der Query sicherstellen.
5. **Kein Depot für „welcher Modus ist aktuell aktiv" bei mehrfachem Öffnen/Schließen:** Sowohl `CameraFOV` als auch `AddLocation`/`LocationDetail` bauen ihre Karten bei jedem Öffnen teils komplett neu auf (z. B. `CameraFOV.initMap` zerstört und baut die Instanz neu, Zeile 3618; `_initEditMapFs` prüft dagegen ob schon vorhanden, Zeile 5338–5344 – uneinheitliches Verhalten). Auslöser: der neue Umschalt-State müsste pro Prefix/Instanz sauber mitgeführt werden, sonst „vergisst" die Karte bei jedem Neuaufbau die zuvor gewählte Ansicht, selbst innerhalb derselben Sitzung. Gegenmaßnahme: State pro Location-Formular-Kontext (nicht nur pro Leaflet-Instanz) halten, damit ein Neuaufbau der Karte den zuletzt gewählten Modus wieder anwendet.

**Architektur-Analyse (intern, technische Namen erlaubt)**

Betroffene Karten-Instanzen (jede mit eigenem hartcodiertem `L.tileLayer(arcgisonline...)`-Aufruf):
- `CameraFOV.initMap(prefix, ...)` — Zeile 3612–3625, Tile-Layer Zeile 3620. Panel-Karte für Blickwinkel-Kegel (bei Location anlegen/bearbeiten UND bei Event-Detail, `ev_fov`/`loc_fov`, Zeile 4123/5147).
- `CameraFOV._initMapFs(prefix)` — Zeile 3725–3741, Tile-Layer Zeile 3733. Zugehörige Vollbildkarte (US-114).
- `AddLocation.initMap()` — Zeile 5737–5759, Tile-Layer Zeile 5740. Karte im „Neue Location"-Formular.
- `LocationDetail._initEditMap()` — Zeile 5271–5299, Tile-Layer Zeile 5275. Mini-Karte im Bearbeiten-Formular einer bestehenden Location.
- `LocationDetail._initEditMapFs()` — Zeile 5335–5353, Tile-Layer Zeile 5349. Vollbildkarte zur Bearbeiten-Mini-Karte (US-87).
- (Nicht Teil des Ticket-Scopes, aber gleiches Muster: `AstroLive._init()` Zeile 4887–4891 — Astro-Karte in Event-Detail.)

Bereits vorhandene, wiederverwendbare Layer-Umschaltung (Vorbild, aber NICHT strukturell geteilt):
- `MapView.layers` — Zeile 4264–4268: Objekt mit drei benannten Tile-URLs (`dark`, `standard`, `satellite`).
- `MapView.setLayer(name)` — Zeile 4278–4288: entfernt aktuellen `L.tileLayer`, fügt neuen hinzu, aktualisiert `.map-layer-btn.active`-Klasse, wendet bei „dark" einen Tile-Filter an.
- UI: `#map-layer-toggle` mit drei `.map-layer-btn`-Buttons — Zeile 1007–1010 (HTML), Zeile 267–273 (CSS).
- **Kein** gemeinsamer State (kein `localStorage`), kein Wiederverwendungs-Hook zwischen `MapView` und den fünf Location-Formular-Karten — diese sind vollständig unabhängiger Code.
- Bereits vorhandenes Shared-Pattern als Vorbild für sauberen Ansatz: `MapMarkers` (Icon-Helfer) und `CameraFOV._drawPinsAndLine()` (Zeile 3630–3643) sind bewusst als gemeinsame Helfer ausgelagert — genau dieses Muster fehlt für die Layer-Wahl.

**Implementierungsoptionen**

*Option A — Eigener, einfacher Umschalter direkt an den betroffenen Karten (kein Rückgriff auf MapView)*
In Alltagssprache: Jede Location-bezogene Karte bekommt ihren eigenen kleinen Umschalt-Knopf für Satellit/Straßenkarte, unabhängig vom normalen Karten-Tab. Die Wahl wird direkt für diese Karten gemerkt.

| Aspekt | Bewertung |
|---|---|
| Technischer Ansatz | Neue gemeinsame Helper-Funktion/-Konstante für die zwei Tile-URLs (Straßenkarte + Satellit), an allen fünf Stellen (CameraFOV Panel+FS, AddLocation, LocationDetail Edit+FS) statt der hartcodierten `L.tileLayer(...)`-Zeile eingebunden |
| Persistenz | Neuer, kleiner State (z. B. eine gemeinsame Variable für „Location-Karten-Modus"), lokal je Gerät gespeichert |
| Aufwand | Mittel — fünf Stellen anfassen, aber isoliert vom bestehenden Karten-Tab-Code, geringes Regressionsrisiko für den Karten-Tab selbst |
| Risiko | Gering-mittel, siehe Pre-Mortem 1/3/5 — sauber lösbar durch eine zentrale Helper-Funktion |

*Option B — Bestehende MapView-Layer-Logik erweitern und für die Location-Karten mitnutzen*
In Alltagssprache: Der bereits vorhandene Umschalter aus dem normalen Karten-Tab wird technisch so verallgemeinert, dass ihn auch die Location-Formular-Karten mitbenutzen können.

| Aspekt | Bewertung |
|---|---|
| Technischer Ansatz | `MapView.layers`/`setLayer` wird zu einer generischeren, von der konkreten Leaflet-Instanz entkoppelten Funktion umgebaut, die auch von `CameraFOV`/`AddLocation`/`LocationDetail` aufgerufen werden kann |
| Persistenz | Könnte gleich für den ganzen Karten-Tab mit-verbessert werden (aktuell auch dort nicht gespeichert, Pre-Mortem 2) |
| Aufwand | Höher — Umbau von bestehendem, produktivem Karten-Tab-Code trifft mehr Stellen als nötig für dieses Ticket |
| Risiko | Höher — Regressionsgefahr für den unabhängig funktionierenden, bereits stabilen Karten-Tab (AK6); Scope-Creep-Gefahr (Karten-Tab-Persistenz war nicht angefragt) |

**Empfehlung:** Option A. Die Code-Verifikation zeigt klar: Karten-Tab und Location-Formular-Karten sind bereits vollständig getrennter Code ohne gemeinsame Basis. Eine Verallgemeinerung von `MapView` (Option B) würde bestehenden, funktionierenden Code anfassen, den das Ticket gar nicht adressiert, und damit Aufwand sowie Regressionsrisiko unnötig erhöhen (Verstoß gegen „Kein Scope Creep"). Option A hält die Änderung eng am Ticket-Ziel, mit vertretbarem Aufwand (fünf klar identifizierte Stellen) und geringerem Risiko für den bestehenden Karten-Tab.

**Testplan-Grundgerüst**

- Manuell: Neue Location anlegen → Umschalter sichtbar → auf Straßenkarte wechseln → Pins/Ausschnitt bleiben erhalten (AK1, AK3).
- Manuell: Bestehende Location bearbeiten → Umschalter sichtbar und funktioniert identisch (AK2, AK3).
- Manuell: Blickwinkel-Kegel-Vorschau auf Straßenkarte umschalten → Vollbildansicht derselben Karte öffnen → zeigt ebenfalls Straßenkarte (AK4).
- Manuell: Bearbeiten-Mini-Karte auf Straßenkarte umschalten → Vollbildansicht öffnen → zeigt ebenfalls Straßenkarte (AK4).
- Manuell: Ansicht auf Straßenkarte stellen, Formular schließen, App-Neustart/erneutes Öffnen einer anderen Location → Straßenkarte bleibt aktiv (AK5).
- Regression: normaler Karten-Tab weiterhin mit Nacht/Standard/Satellit unverändert nutzbar, keine Wechselwirkung mit der neuen Location-Karten-Umschaltung (AK6).
- pytest: Für dieses Ticket rein clientseitig (HTML/JS), kein Backend-Endpoint betroffen — kein pytest-Fall zu erwarten; falls doch ein Persistenz-Endpoint nötig wird (siehe AK7/Option-Klärung), dort Test für Lesen/Schreiben des gespeicherten Modus ergänzen.

**Entscheidung (Weg-Gate, 2026-07-04, freigegeben von Stephan):**
- Implementierungsoption: **A** — eigener, schlanker Umschalter direkt an den fünf betroffenen Karten, kein Umbau von `MapView`.
- AK7 (Merk-Umfang): **eine gemeinsame Einstellung** für alle Location-bezogenen Karten (Anlegen, Bearbeiten, Kegel-Vorschau teilen sich einen Stand — nicht je Kartentyp getrennt).
- AK5/Rule 3 (Speicherort): **nur lokal auf dem Gerät** (kein geräteübergreifender Sync, kein Server-Endpoint nötig).
- Status → `Ready for Dev`.

**Umsetzung (Implementierungs-Phase, 2026-07-04):**
- Neuer gemeinsamer Helper `LocMapMode` in `web/index.html` (vor `CameraFOV`): `TILES` (Satellit = bestehende arcgisonline-URL, Standard = dieselbe OSM-URL wie `MapView.layers.standard`), `get()`/`set()` über `localStorage`, `addTileLayer()`, `toggleHtml()`, `syncAllToggles()`.
- Persistenz: `localStorage`-Key `fa_loc_map_mode`, Werte `satellite`/`standard`, Default `satellite` (AK5/AK7).
- Alle fünf Stellen umgestellt: `CameraFOV.initMap`, `CameraFOV._initMapFs`, `AddLocation.initMap` (+ `setLocMapLayer()`), `LocationDetail._initEditMap` (+ `setEditMapLayer()`), `LocationDetail._initEditMapFs`.
- Neues CSS `.loc-map-mode-toggle`/`.loc-map-mode-btn`, an `.map-layer-btn` angelehnt, eigenständig positioniert (links oben, kollidiert nicht mit Expand-Buttons).
- `MapView`/normaler Karten-Tab unangetastet verifiziert (AK6).
- `PRODUCT.md` aktualisiert (Abschnitt Orte-Tab + Changelog-Eintrag US-123).
- Offener, nicht umgesetzter Vorschlag (kein Scope Creep): Toggle-Buttons könnten je ein kleines Icon bekommen statt nur Text.

**Testfeedback (2026-07-04, Stephan):**
- 🐛 Der neue Umschalter überlappt bei Neuanlage und Bearbeiten einer Location mit dem Zoom-Menü (+/-), auch beim Zoomen. Umschalter muss weiter nach rechts, damit kein Überlappen mehr entsteht.
- 🐛 Beschriftung uneinheitlich: Umschalter zeigt „Straße", die übrigen Karten (normaler Karten-Tab) verwenden „Standard" für denselben Modus. Umbenennen für Konsistenz.
- ✅ Umschalten funktioniert (AK3), restliche Akzeptanzkriterien laut Stephan erfüllt.

**Fixes (2026-07-04):** Umschalter-Position von `top/left` auf `bottom/left` geändert (keine Überlappung mehr mit Zoom-Menü), Label „Straße" → „Standard" (interner Speicherwert unverändert `standard`, kein Migrationsrisiko). Von Stephan erneut getestet: **passt.**

---

## 🟡 Mittel – Daten & Integration

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

### TASK-01 · Kometen-Integration `[ ]`
> NASA JPL Horizons API anbinden für aktuelle Kometen-Positionen und -Sichtbarkeit.

### TASK-02 · Sonnenfinsternisse berechnen `[ ]`
> Skyfield-Berechnung der Kontakte (C1–C4) für Berlin/BB-Region.

### TASK-03 · Feuerwerk-Events `[ ]`
> Manuelle Events für wiederkehrende Feuerwerke: Silvester, Pyronale, Havel in Flammen.

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

### TASK-06 · AR-Overlay: Sonnenbahn über Kamera-Live-Preview `[ ]`
> Sonnenbahn als AR-Overlay über dem Kamera-Bild einblenden.

### TASK-07 · Export als PhotoPills-Bookmark `[ ]`
> Location-Daten im PhotoPills-kompatiblen Format exportieren.

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
- [x] **US-96** Einheitliche Chancen-Detailansicht – neue Sektionsreihenfolge, alle Sektionen beim Öffnen zugeklappt, Live-Astro mit Shoot-Datum. v1.17.0.

### BUG-47 · Einstellungsseite zeigt falsche Rolle nach Host-Login `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |
| **Abgeschlossen** | 2026-06-28 |

**Beschreibung:** Nach der Anmeldung mit dem Host-Passwort zeigt die Einstellungsseite „User" statt „Host" an. Die Rolle wird also nach erfolgreichem Login falsch dargestellt — obwohl der Login selbst funktioniert und host-spezifische Rechte greife, stimmt die angezeigte Rollenbezeichnung nicht mit dem tatsächlichen Token überein.

**Bezug:** Abhängig von US-66[x] (Login mit Rollen-Erkennung, Passwort-Mechanismus) — der Fehler liegt in der Darstellungsschicht nach dem Login, nicht im Auth-Mechanismus selbst. Grenzt an US-84 (Host-Passwort-Änderung in der UI), da beide die Einstellungsseite mit host-spezifischen Inhalten betreffen.

---

### Scope

**Eingeschlossen:**
- Korrekte Anzeige der Rolle ("Host" / "User") in der Einstellungsseite nach Login und nach Seiten-Reload
- Robuste Rollenableitung: falls `fa_role` im localStorage fehlt, wird die Rolle aus dem gespeicherten Token abgeleitet

**Ausgeschlossen:**
- Änderungen am Backend-Login-Endpunkt oder am Auth-Mechanismus
- Änderungen an anderen Teilen der Einstellungsseite (US-84, Passwort-Änderung)
- iOS-App

---

### Analyse & Root Cause

**Was passiert wo:**

Das Token hat das Format `"<rolle>.<hmac>"` (z.B. `"host.abc123..."`). Der Login-Endpoint `/login` gibt `{ role: "host", token: "host.abc123..." }` zurück. Das Frontend speichert beides getrennt: Token unter `fa_token` und Rolle unter `fa_role` im localStorage. `CFG.role` wird aus `fa_role` geladen und nach Login auf `d.role` gesetzt.

**Die Einstellungsseite** (`Settings.render()`, `web/index.html` Z. 4978) zeigt:
```
${CFG.role === 'host' ? 'Host' : 'User'}
```

**Root Cause:** Wenn `fa_role` im localStorage fehlt (aber `fa_token` vorhanden ist), initialisiert `CFG.role` sich auf `null` — obwohl das Token die korrekte Rolle enthält. Dies passiert zum Beispiel wenn:
- Der Browser-Storage selektiv geleert wurde (z.B. durch Safari ITP / Storage-Ablauf bei langer Inaktivität), sodass `fa_token` gespeichert bleibt aber `fa_role` fehlt
- Eine ältere App-Version nur das Token speicherte (kein `fa_role`-Key vorhanden)

In diesem Zustand ist `Auth.isLoggedIn()` true (Token vorhanden), aber `CFG.role === null`, und `null === 'host'` ist false → Einstellungen zeigen "User".

**Betroffene Stellen:**
- `web/index.html` Z. 1130: CFG-Initialisierung — `role: localStorage.getItem('fa_role') || null`
- `web/index.html` Z. 1225–1227: `Auth.login()` — setzt `CFG.role = d.role` und speichert `fa_role`
- `web/index.html` Z. 4978: `Settings.render()` — zeigt `CFG.role === 'host' ? 'Host' : 'User'`

---

### Example Mapping

**Regel 1: Nach dem Login zeigt die Einstellungsseite immer die tatsächlich angemeldete Rolle**

- ✅ Positiv: Ich melde mich mit dem Host-Passwort an, öffne die Einstellungen → ich sehe "Host"
- ✅ Positiv: Ich melde mich mit dem User-Passwort an, öffne die Einstellungen → ich sehe "User"
- ❌ Negativ (Bug): Ich melde mich mit dem Host-Passwort an, öffne die Einstellungen → ich sehe "User"
- 🔲 Edge: Ich melde mich als Host an, lade die Seite neu, öffne die Einstellungen → ich sehe "Host" (nicht "User" oder leer)

**Regel 2: Die Rolle wird auch nach einem Seiten-Reload korrekt wiederhergestellt**

- ✅ Positiv: Ich war als Host angemeldet, lade die Seite neu, öffne die Einstellungen → "Host"
- 🔲 Edge: `fa_role` fehlt im localStorage, aber `fa_token` ist vorhanden → Rolle wird aus dem Token abgeleitet, Einstellungen zeigen "Host"
- ❌ Negativ (Bug): `fa_role` fehlt, Token hat "host" kodiert → Einstellungen zeigen "User"

**Regel 3: Ein Logout löscht alle Session-Daten vollständig**

- ✅ Positiv: Ich klicke "Logout", lade die Seite neu → Login-Screen erscheint, keine alte Rolle bleibt
- ❌ Negativ: Nach Logout ist immer noch eine Rolle angezeigt

*Annahme (aus Code verifiziert):* Das Token-Format `"<rolle>.<hmac>"` ist stabil (auth.py Z. 50–52). Wenn sich das Token-Format ändert, muss die Rollenableitung angepasst werden.

---

### Akzeptanzkriterien

- [ ] **AK1:** Wenn ich mich mit dem Host-Passwort anmelde und dann die Einstellungen öffne, steht unter „Konto" der Text „Host" — nicht „User".
- [ ] **AK2:** Wenn ich mich mit dem User-Passwort anmelde und dann die Einstellungen öffne, steht dort „User".
- [ ] **AK3:** Wenn ich als Host angemeldet war, die Seite neu lade und dann die Einstellungen öffne, steht immer noch „Host" — die Anmeldung überlebt den Reload mit korrekter Rollenanzeige.
- [ ] **AK4:** Wenn `fa_role` im localStorage fehlt, aber ein gültiges Host-Token gespeichert ist, wird beim nächsten Öffnen der Einstellungen trotzdem „Host" angezeigt (Rolle aus Token abgeleitet).
- [ ] **AK5:** Nach dem Ausloggen und erneutem Login als andere Rolle zeigt die Einstellungsseite korrekt die neue Rolle an — keine alten Werte bleiben hängen.

---

### Pre-Mortem

**Szenario 1: Token-Format ändert sich, Rollenableitung bricht**
- Risiko: Wenn das Token nicht mehr mit `"."` geteilt werden kann oder das erste Segment keine gültige Rolle enthält, würde `CFG.role` leer bleiben.
- Gegenmaßnahme: Fallback auf `null` einbauen; nur `"host"` und `"user"` als gültige Werte akzeptieren. `test_bug47.py` verifiziert das Token-Format.

**Szenario 2: Alter localStorage ohne `fa_role`-Key**
- Risiko: Nutzer mit altem Token (aus einer Version vor US-66) — Token vorhanden aber kein `fa_role`-Key.
- Gegenmaßnahme: Fix leitet Rolle immer aus Token ab → kein separater Migration-Step nötig.

**Szenario 3: Safari ITP löscht selektiv Storage**
- Risiko: Safari Intelligent Tracking Prevention kann localStorage-Keys ablaufen lassen. Wenn `fa_role` gelöscht wird aber `fa_token` noch gilt, tritt der Bug erneut auf.
- Gegenmaßnahme: Rolle nicht aus separatem Key lesen, sondern aus Token extrahieren → `fa_role` wird nicht mehr gebraucht.

**Szenario 4: CFG.role bleibt nach Logout nicht leer**
- Risiko: Nach Logout mit falscher Rolle für nächsten Login.
- Verifiziert: `Auth.logout()` (Z. 1231) setzt `CFG.role = null` korrekt — kein Problem hier.

---

### Implementierungsoptionen

**Option A: Rolle aus Token ableiten (empfohlen)**

*App-Wirkung:* Beim Start und nach dem Login wird die Rolle immer direkt aus dem Token gelesen — nicht aus einem separaten `fa_role`-Key. Die Einstellungsseite zeigt immer die Rolle, die im Token steht.

*Technische Umsetzung:*
- `web/index.html` Z. 1130: `CFG.role` nicht mehr aus `fa_role` lesen, sondern aus dem Token ableiten: `token ? (token.split('.')[0] === 'host' ? 'host' : token.split('.')[0] === 'user' ? 'user' : null) : null`
- `Auth.login()` Z. 1226–1227: `localStorage.setItem('fa_role', d.role)` kann entfernt werden
- `Auth.logout()` Z. 1232: `localStorage.removeItem('fa_role')` entfernen (optional, sauberer Cleanup)

*Vorteil:* Einzige Quelle der Wahrheit ist das Token. Kein Sync-Problem, kein separater Key.
*Nachteil:* Keiner bei diesem Anwendungsfall.

**Option B: `fa_role` behalten, aber beim Startup aus Token auffüllen wenn leer**

*App-Wirkung:* Falls `fa_role` fehlt aber ein Token vorhanden ist, wird `CFG.role` aus dem Token-Prefix abgeleitet. Im Normalfall bleibt alles beim Alten.

*Technische Umsetzung:*
- `web/index.html` Z. 1130: Initialisierungslogik erweitern — falls `fa_role` leer aber `fa_token` vorhanden, Rolle aus Token-Prefix lesen.

*Vorteil:* Minimale Änderung.
*Nachteil:* Zwei Quellen (Token und `fa_role`), die auseinanderlaufen können.

**Empfehlung: Option A.** Weniger Zustand, keine Sync-Probleme, robuster gegen Storage-Teilbereinigung. Kleiner Change (3–4 Zeilen).

---

### Testplan

**Backend (automatisiert, pytest):**
- `backend/tests/test_bug47.py`: Verifiziert dass `/login` mit Host-Passwort `role: "host"` zurückgibt und das Token-Prefix mit der Rolle übereinstimmt.

**Frontend (manuell, nach Implementierung):**

Schritt 1 — Frischer Login als Host:
```
Einstellungen-Tab öffnen → unter "Konto" muss "Host" stehen
```

Schritt 2 — Reload-Persistenz:
```
Seite neu laden → Einstellungen öffnen → immer noch "Host"
```

Schritt 3 — Rolle aus Token bei fehlendem fa_role:
```
Browser-DevTools Console: localStorage.removeItem('fa_role')
Seite neu laden → Einstellungen öffnen → "Host" (Rolle aus Token)
```

Schritt 4 — Rollenwechsel:
```
Logout → als User anmelden → Einstellungen → "User"
```

---

### BUG-34 · iPhone Safari: Bearbeitungs-Overlay zoomt und ragt rechts aus dem Screen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |

**Beschreibung:** Öffnet man auf dem iPhone (Safari) das Bearbeiten-Overlay einer Location, vergrößert die Seite (Zoom) und der rechte Teil des Overlays ragt außerhalb des sichtbaren Bereichs. Erwartet: Das Overlay passt sich vollständig in den Viewport ein, kein ungewollter Zoom.

**Bezug:** Verwandt mit BUG-19 [x] (Close-Button in Sheets nicht erreichbar) und BUG-07 [x] (Sheets überschreiten iPhone-Breite auf Desktop). Wahrscheinliche Ursache: iOS Safari zoomt automatisch wenn ein fokussiertes Input-Feld eine Font-Size < 16px hat; zusätzlich fehlt ggf. `max-width: 100%` / `overflow-x: hidden` am Overlay-Container.

**Scope:**
- Eingeschlossen: alle `.input-field`-Elemente (Edit-Form, Add-Sheet, Filter), `#loc-detail-content`
- Ausgeschlossen: iOS-App, Backend

**Akzeptanzkriterien:**
- [ ] Öffnet man auf dem iPhone Safari das Bearbeitungs-Overlay und tippt in ein Textfeld, zoomt die Seite nicht.
- [ ] Das Overlay ragt an keiner Seite aus dem sichtbaren Bereich.
- [ ] Auch die Koordinaten-Eingabefelder (vormals 12px) lösen keinen Zoom aus.
- [ ] Edge Case: Auch im Add-Sheet und anderen Formularen tritt kein Zoom auf.

**Implementierung:**
- `web/index.html` Z. 438: `.input-field` `font-size: 14px` → `16px`
- `web/index.html` Z. 457: `.coord-pair .input-field` `font-size: 12px` → `16px`
- `web/index.html` Z. 555: `#loc-detail-content` + `overflow-x: hidden` (Defense-in-depth)

---

### ~~TASK-39 · Refactoring: Lange Funktion local() in index.html aufteilen~~ `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done (Duplicate) |
| **Erstellt** | 2026-06-24 |
| **Geschlossen** | 2026-07-03 |

**Beschreibung:** JS-Funktion `local()` in `web/index.html` (Z. 2633, ~265 Zeilen) überschreitet den 80-Zeilen-Threshold deutlich. In kleinere Hilfsfunktionen aufteilen (z.B. Rendering, Event-Handler, Datenaufbereitung).

**Duplikat von TASK-42:** TASK-42 deckt exakt dieselbe Funktion (`local()`, gleiche Datei, gleiche Zeilengröße) zusätzlich zu `row()` bereits ab. Als Duplikat geschlossen, keine separate Umsetzung — Weiterverfolgung unter TASK-42.

**Quelle:** Automatisch erstellt durch fotoalert-refactor (TASK-29); als Duplikat von TASK-42 geschlossen nach Overlap-Check am 2026-07-03

---

### TASK-49 · Refactoring: Lange JS-Funktionen aufteilen (web/index.html) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-27 |
| **Abgeschlossen** | 2026-07-03 |

**Beschreibung:** `refactor_check.py` meldet sechs lange JS-Funktionen in `web/index.html`:
- `ic()` Z. 847 — ~389 Zeilen (Icon-Helper, eingebracht durch US-100)
- `handler()` Z. 1236 — ~115 Zeilen
- `verState()` Z. 3028 — ~232 Zeilen (neu gemeldet durch BUG-46, 2026-06-28)
- `sectorPath()` Z. 3289 — ~160 Zeilen (neu gemeldet durch US-113-Refactor, 2026-07-02)
- `azDiffFn()` Z. 3716 — ~190 Zeilen (neu gemeldet durch US-109-Refactor, 2026-06-30)
- `sunAlignmentLabel()` Z. 4966 — ~1044 Zeilen (neu gemeldet durch BUG-53, 2026-06-29)

Aufteilen in kleinere Hilfsfunktionen oder Modul-Abschnitte. Kein inhaltlicher Umbau.

**Quelle:** Automatisch erstellt durch fotoalert-refactor (US-102, 2026-06-27); ergänzt durch BUG-46-Refactor (2026-06-28); ergänzt durch BUG-53-Refactor (2026-06-29); Zeilennummern aktualisiert durch BUG-52-Refactor (2026-06-29); Zeilennummern aktualisiert durch US-07-Refactor (2026-06-30); azDiffFn ergänzt + Zeilennummern aktualisiert durch US-109-Refactor (2026-06-30); sectorPath ergänzt + Zeilennummern aktualisiert durch US-113-Refactor (2026-07-02)

**Scope:**
Alle sechs von `refactor_check.py` gemeldeten Funktionen wurden im echten Code (`web/index.html`) verifiziert — mit demselben Ergebnis wie bei TASK-42: **alle sechs sind False Positives** der Regex-Heuristik, keine einzige ist tatsächlich eine lange Funktion. Es gibt daher **nichts aufzuteilen** — der Scope dieses Tickets reduziert sich auf eine Korrektur des Analyse-Werkzeugs (Ignorelist-Ergänzung), analog zu TASK-42.

Verifikationsdetails je Funktion (echte Start-/Endzeile per Read bestimmt, echte Zeilenzahl gezählt):

| Funktion | Ticket-Wert | Echte Zeilen | Tatsächliches Ende | Befund |
|---|---|---|---|---|
| `ic()` Z. 847 | ~389 Zeilen | **4 Zeilen** (847–850) | `}` in Z. 850 | False Positive |
| `handler` Z. 1236 | ~115 Zeilen | **1 Zeile** (komplett einzeilig: `const handler = () => { ... };`) | Semikolon in Z. 1236 | False Positive |
| `verState()` Z. 3028 | ~232 Zeilen | **5 Zeilen** (3028–3032) | `};` in Z. 3032 | False Positive |
| `sectorPath()` Z. 3289 | ~160 Zeilen | **11 Zeilen** (3289–3299) | `}` in Z. 3299 | False Positive |
| `azDiffFn` Z. 3716 | ~190 Zeilen | **1 Zeile** (komplett einzeilig) | Semikolon in Z. 3716 | False Positive |
| `sunAlignmentLabel()` Z. 4966 | ~1044 Zeilen | **9 Zeilen** (4966–4974) | `}` in Z. 4974 | False Positive |

**Ursache identisch zu TASK-42/TASK-32:** Die Regex-Heuristik in `refactor_check.py` (Abschnitt „Sehr lange JS-Funktionen im Frontend", Zeilen 221–273) misst die Funktionslänge als Abstand bis zur *nächsten von der Regex erkannten* Funktion, nicht bis zur echten schließenden `}`. Das wurde durch Nachrechnen exakt bestätigt: die vollständige Liste der Regex-Treffer zeigt, dass z.B. nach `ic()` (Z. 847) der nächste Treffer `handler` in Z. 1236 ist → `1236 − 847 = 389`, exakt der gemeldete Wert. Dasselbe Muster gilt für alle fünf weiteren Funktionen (nächster Regex-Treffer minus Start-Zeile ergibt exakt den gemeldeten Wert in jedem einzelnen Fall). Besonders auffällig: `handler` und `azDiffFn` sind sogar vollständig **einzeilige** Arrow-Functions — die Heuristik kann so etwas grundsätzlich nicht als „kurz" erkennen, weil sie nie die eigentliche schließende Klammer sucht.

Kein inhaltlicher Umbau nötig, weil keine der sechs Funktionen tatsächlich lang oder unübersichtlich ist. Statt eines Code-Refactorings wird `FRONTEND_LONG_FN_IGNORELIST` in `tools/refactor_check.py` um die sechs Namen (`ic`, `handler`, `verState`, `sectorPath`, `azDiffFn`, `sunAlignmentLabel`) ergänzt, mit Kommentar zur echten Zeilenzahl — analog zu den bereits dort gelisteten Einträgen aus TASK-32/TASK-43.

⚠️ Annahme: Die Namen `handler` und `azDiffFn` sind nicht komplett eindeutig (es könnte an anderer Stelle im Code eine andere lokale Variable/Funktion gleichen Namens geben, die künftig fälschlich mitunterdrückt würde). Das Risiko wird als gering eingeschätzt, weil die Ignorelist bereits heute nach demselben Muster funktioniert (z.B. `state3`, `local`, `row` sind ebenfalls generische Namen) und die Konsequenz im schlimmsten Fall nur ein unterdrücktes Ticket-Finding ist, kein Funktionsfehler.

**Example Mapping — Regel: „Verhalten bleibt nach der Korrektur identisch"**

Regel 1 — Die App verhält sich für Stephan unverändert, weil kein Anwendungscode angefasst wird.
- Beispiel (Given/When/Then): Given die App lief vor diesem Ticket fehlerfrei, When `tools/refactor_check.py` um die Ignorelist-Einträge ergänzt wird (kein Edit an `web/index.html`), Then verhält sich die App (Icons, Filter-Sheet, Kompass-Grafik, Sonnen-Ausrichtungstext) exakt wie vorher, weil keine einzige Zeile Anwendungscode verändert wurde.

Regel 2 — `refactor_check.py` meldet die sechs Funktionen nach der Änderung nicht mehr als „lang".
- Beispiel: Given die sechs Namen sind in `FRONTEND_LONG_FN_IGNORELIST` eingetragen, When `python3 tools/refactor_check.py --report` läuft, Then erscheinen `ic`, `handler`, `verState`, `sectorPath`, `azDiffFn`, `sunAlignmentLabel` nicht mehr unter `needs_ticket` / `long_function`.

Regel 3 — Bestehende andere Findings des Tools bleiben unangetastet.
- Beispiel: Given es gibt weitere, unabhängige Findings (z.B. TASK-51 zu `backend/main.py`), When der Report nach der Änderung erneut läuft, Then sind diese anderen Findings unverändert vorhanden (die Ignorelist-Ergänzung wirkt ausschließlich auf die sechs benannten Frontend-Funktionsnamen).

⚠️ Annahme: „Identisches Verhalten" wird hier bewusst nicht durch einen Diff der gerenderten HTML-Ausgabe verifiziert, weil gar keine Zeile in `web/index.html` verändert wird — das Null-Diff an dieser Datei ist der eigentliche Beleg.

**Akzeptanzkriterien:**
- [x] Die App verhält sich in jedem Bereich exakt wie vor diesem Ticket — Icons (z.B. Kalender-, Wetter-, Kompass-Icons), das Filter-Sheet (insbesondere der Verifikations-Chip „Geprüft/Nicht geprüft/Probleme" in allen drei Zuständen), die Kompass-/Sektor-Grafik im Location-Detail und der Sonnen-Ausrichtungstext („fast genau hinter dem Motiv", „nah am Motiv" etc.) sehen und verhalten sich identisch wie vorher. Das ist hier gleichbedeutend mit: es wurde keine Zeile Anwendungscode verändert.
- [x] `python3 tools/refactor_check.py --report` meldet `ic()`, `handler`, `verState()`, `sectorPath()`, `azDiffFn`, `sunAlignmentLabel()` nicht mehr als lange Funktionen.
- [x] Keine der sechs Funktionen wurde tatsächlich aufgeteilt (es gibt inhaltlich nichts aufzuteilen — alle sind 1–11 Zeilen lang).

**Pre-Mortem:**
- 💀 Ein zukünftiger Bearbeiter liest nur die Ticket-Beschreibung (nicht diese Spec) und beginnt trotzdem, `ic()`/`sunAlignmentLabel()` etc. „vorsichtshalber" aufzuteilen, obwohl es dafür keinen Grund gibt → unnötiges Risiko an einem 124× verwendeten Helper (`ic()`) ohne jeden Nutzen. Gegenmaßnahme: Scope-Absatz oben unmissverständlich voranstellen; Ticket-Titel-Ergänzung „(alle sechs False Positive — siehe Scope)" erwägen.
- 💀 Die Ignorelist-Ergänzung wird versehentlich mit falschem Namen oder an falscher Stelle in `tools/refactor_check.py` eingetragen (z.B. Tippfehler bei `sunAlignmentLabel`) → Finding taucht weiter/fälschlich auf oder unterdrückt den falschen Namen. Gegenmaßnahme: Nach dem Edit `python3 tools/refactor_check.py --report` laufen lassen und explizit prüfen, dass genau diese sechs Namen aus dem Report verschwinden und sonst nichts.
- 💀 Ein anderswo im Code später neu eingeführter, gleichnamiger Funktion/Variable (`handler`, `azDiffFn` sind generische Namen) wird künftig fälschlich von der Ignorelist mitunterdrückt, obwohl sie diesmal echt lang ist. Gegenmaßnahme: Kommentar an der Ignorelist-Zeile mit Zeilennummer + „Stand 2026-07" ergänzen, damit ein künftiger Bearbeiter die Diskrepanz bei Bedarf erkennt (wie bereits bei den bestehenden Einträgen gehandhabt).
- 💀 (Ursprünglich befürchtetes Risiko, aber im Code nicht bestätigt) `ic()` liegt scheinbar in einem Hot-Path (124 Aufrufe im gesamten Frontend, u.a. in Filter-Sheet-Renders). Da hier aber kein Code geändert wird, entsteht kein Performance-Risiko durch dieses Ticket — als Hinweis für zukünftige *echte* Refactorings an `ic()` dennoch festgehalten: jede künftige Änderung an `ic()` sollte Performance in Render-Schleifen im Blick behalten.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` — alle sechs Funktionen sind lokale Konstanten/Top-Level-Functions ohne eigenen State; `ic()` ist eine globale Top-Level-Function (124 Aufrufe, u.a. in `FilterSheet`, `oppCard`, `scoutCard`, Location-Detail-Sections); `handler` ist eine lokale Closure innerhalb `ThemeManager.init()` (Media-Query-Change-Listener); `verState` ist eine lokale Closure innerhalb `FilterSheet._render()` (3 Aufrufe in derselben Funktion); `sectorPath` ist eine lokale Closure innerhalb der IIFE `mkCloudCompassSvg()` (3 Aufrufe für Zonen-Pfade); `azDiffFn` ist eine lokale Closure innerhalb eines IIFE im Location-Detail-Rendering (2 Aufrufe direkt danach); `sunAlignmentLabel` ist eine globale Top-Level-Function (3 Aufrufe, u.a. Location-Detail). Keine der sechs teilt State über mehrere Module hinweg — jede ist entweder ein reiner globaler Pure-Helper oder eine eng scope-gebundene lokale Closure.
- [x] Designer-Check: nein (rein technisches Refactoring, keine visuelle Änderung) — übersprungen
- [x] Implementierungsoptionen: A / B
- [x] Empfehlung: Option A

**Implementierungsoptionen:**
- **Option A — Nur Ignorelist-Ergänzung in `tools/refactor_check.py`, kein Edit an `web/index.html` (empfohlen).** Da alle sechs Funktionen echte Zeilenzahlen von 1–11 haben, gibt es funktional nichts aufzuteilen; ein Aufteilen würde nur Risiko erzeugen (insbesondere an `ic()` mit 124 Aufrufen und den vier Closures, deren Aufteilung Scope-Referenzen auf umgebende Variablen wie `s`, `sunAz`, `subAz` gefährden könnte) ohne jeden Lesbarkeits- oder Wartbarkeitsgewinn. Aufwand: minimal (ein Edit in einer Datei, ein Verifikationslauf). Risiko: sehr gering. Testbarkeit: trivial (`--report`-Lauf zeigt sofort ob die sechs Namen verschwunden sind; kein Anwendungscode betroffen, daher kein Regressionsrisiko in der App selbst).
- **Option B — Alle sechs Funktionen dennoch strukturell „aufteilen" (z.B. Kommentar-Sektionen einziehen), um dem Ticket-Wortlaut „Aufteilen in kleinere Hilfsfunktionen" wörtlich zu folgen.** Nicht empfohlen: Bei Funktionen von 1–11 Zeilen gibt es keine sinnvolle Aufteilung — jeder Versuch würde künstliche Zwischenschritte erzeugen, die die Lesbarkeit eher verschlechtern als verbessern, und bei den vier Closures (`verState`, `sectorPath`, `azDiffFn`, `handler`) unnötiges Risiko an Scope-Referenzen (`s.verificationIncl`, `pt()`, `subAz`, `this.pref()`) erzeugen, ohne jeden Gegenwert. Aufwand: höher, Risiko: höher, Nutzen: keiner.
- **Empfehlung: Option A**, mit derselben Begründung wie bei TASK-42: das Ticket ist bereits durch die Verifikation beantwortet — die gemeldeten Funktionen existieren in der gemeldeten Form/Länge nicht, das Werkzeug muss korrigiert werden, nicht der Anwendungscode.

**Testplan:**
- [x] Automatisiert: `python3 tools/refactor_check.py --report` vor und nach der Ignorelist-Änderung laufen lassen und die Diffs vergleichen — die sechs Namen (`ic`, `handler`, `verState`, `sectorPath`, `azDiffFn`, `sunAlignmentLabel`) dürfen danach nicht mehr unter `long_function` erscheinen, alle anderen Findings (u.a. TASK-51-Fund zu `backend/main.py`) müssen unverändert bestehen bleiben.
- [x] Manuell: Da kein Anwendungscode verändert wird, ist kein Klickpfad-Test in der App nötig. Zur Absicherung dennoch ein kurzer Sichttest im lokalen Dev-Server empfohlen (siehe PRODUCT.md-Regressionsmatrix, sofern vorhanden): Filter-Sheet öffnen und den Verifikations-Chip „Geprüft" durch alle drei Zustände klicken (Off → Geprüft → Probleme → Off), ein Location-Detail mit „Goldene Wolken"/„Himmelsröte"-Event öffnen und die Kompass-Grafik sowie den Sonnen-Ausrichtungstext prüfen — erwartetes Ergebnis: alles sieht/verhält sich exakt wie vor diesem Ticket, weil keine Zeile Anwendungscode geändert wurde.

---

### TASK-58 · Refactoring: Lange Funktion `mkCloudCompassSvg()` aufteilen (web/index.html) `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | ToDo |
| **Erstellt** | 2026-07-05 |

**Beschreibung:** `refactor_check.py` meldet eine lange Funktion in `web/index.html`:
- `mkCloudCompassSvg()` Z. 3537 — ~144 Zeilen (Threshold: 100)

Dies ist ein neuer, echter Befund (kein Falsch-Positiv) — aufgedeckt durch den TASK-49-Fix der Längen-Messung (echte Klammer-Zählung statt Distanz-Heuristik, siehe Retro-Eintrag Z. 2858–2860). Vorher wurde die Länge durch die verschachtelte `sectorPath`-Closure verdeckt/falsch zugeordnet. Aufteilen in kleinere Hilfsfunktionen (z.B. SVG-Grundgerüst, Zonen-Pfad-Berechnung, Label-Platzierung separieren). Kein inhaltlicher/visueller Umbau — von `fotoalert-designer` bereits abgenommene Optik (US-111) darf sich nicht ändern.

**Quelle:** Automatisch erstellt durch fotoalert-refactor (BUG-62-Release-Check, 2026-07-05)

---

### TASK-51 · Refactoring: Lange Funktion `startup()` aufteilen (backend/main.py) `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | ToDo |
| **Erstellt** | 2026-07-02 |

**Beschreibung:** `refactor_check.py` meldet eine lange Funktion in `backend/main.py`:
- `startup()` Z. 1237 — 84 Zeilen (Threshold: 80)

Aufteilen in kleinere Hilfsfunktionen (z.B. Scheduler-Setup, QA-Values-Laden, Location-Overrides separieren). Kein inhaltlicher Umbau.

**Quelle:** Automatisch erstellt durch fotoalert-refactor (US-113, 2026-07-02)

---

### BUG-54 · Sections._def: ev_golden_clouds und ev_red_sky fehlen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Bug |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-30 |

**Beschreibung:** `refactor_check.py` (category: `section_missing_default`) meldet, dass zwei Event-Sections gerendert werden, aber keinen Eintrag in `Sections._def` haben:
- `ev_golden_clouds`
- `ev_red_sky`

Fehlt ein `_def`-Eintrag, bleibt die Section beim ersten Render stumm eingeklappt (BUG-40-Klasse). Beide Sections wurden durch US-109 eingebracht. Fix: `_def`-Eintrag für beide ergänzen (analog zu anderen Event-Sections).

**Quelle:** Automatisch erstellt durch fotoalert-refactor (US-109-Refactor, 2026-06-30)

---

### TASK-41 · Refactoring: Lange Funktionen aufteilen (backend/precompute.py) `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | ToDo |
| **Erstellt** | 2026-06-25 |

**Beschreibung:** Drei Funktionen in `backend/precompute.py` überschreiten den 80-Zeilen-Threshold:
- `compute_calendar_incremental()` Z. 590 — 146 Zeilen
- `_run_single_location_flow()` Z. 743 — 92 Zeilen
- `_run_standard_flow()` Z. 838 — 84 Zeilen

**Quelle:** Automatisch erstellt durch fotoalert-refactor (BUG-39, 2026-06-25)

---

### TASK-42 · Refactoring: Lange JS-Funktionen aufteilen (web/index.html) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-25 |
| **Abgeschlossen** | 2026-07-03 — kein Handlungsbedarf, Falsch-Positiv (siehe Analyse-Spec unten) |

**Beschreibung:** Zwei JS-Funktionen in `web/index.html` überschreiten den Threshold erheblich:
- `local()` Z. 2674 — ~265 Zeilen
- `row()` Z. 3531 — ~1034 Zeilen

**Bezug:** TASK-39 deckte denselben `local()`-Teil bereits ab und wurde als Duplikat geschlossen (2026-07-03) — hier mitverfolgen.

**Quelle:** Automatisch erstellt durch fotoalert-refactor (BUG-39, 2026-06-25)

---

#### 🔬 Analyse-Spec (TASK-42) · 2026-07-03

### Kernbefund: Ticket beruht auf einem bereits behobenen Mess-Fehler — kein Refactoring nötig

**📎 Code-Verifikation (Pflicht, Schritt 3):** Beide im Ticket genannten Funktionen wurden im aktuellen Stand von `web/index.html` gelesen:

- **`local` (Zeile 3449 und 3466, nicht 2674):** Ist keine Funktion, sondern eine sofort ausgeführte Konstante (`const local = (() => { … })();`) innerhalb von `CameraFOV._loadProfile()`. Sie liest das gespeicherte Kamera-Profil aus dem Browser-Speicher aus. Die komplette Definition passt in **eine einzige Zeile**. Von „~265 Zeilen" keine Spur.
- **`row` (Zeile 4881, nicht 3531):** Ist eine kleine lokale Hilfsfunktion innerhalb von `AstroMap._draw()` (nicht `AstroMap.render()`, wie ein interner Code-Kommentar fälschlich vermerkt), die eine einzelne Zeile in der Sonne/Mond/Milchstraße-Ausrichtungsanzeige aufbaut. Sie umfasst **12 Zeilen** (Zeile 4881–4893). Von „~1034 Zeilen" keine Spur.

**Ursache des Fehlbefunds:** Das Analyse-Werkzeug `tools/refactor_check.py` misst die Länge einer JS-Funktion über eine Regex-Heuristik, die den Abstand bis zur *nächsten erkannten* Funktionsdefinition zählt — nicht bis zur tatsächlichen schließenden Klammer. Bei kurzen, lokal verschachtelten Hilfsfunktionen (wie `local` und `row`) „läuft" die gemessene Länge bis weit in den nachfolgenden Code hinein und erzeugt Werte, die 100-fach zu hoch sind. Das ist im Werkzeug selbst dokumentiert (Kommentarblock „BEKANNTE LIMITATION (TASK-32)").

**Bereits gefixt:** Beide Namen (`local`, `row`) stehen bereits in der Ausschlussliste des Werkzeugs (`FRONTEND_LONG_FN_IGNORELIST`), mit dem Vermerk „tatsächlich 1 Zeile" bzw. „tatsächlich 12 Zeilen". Ein Refactoring-Ticket wurde also offensichtlich schon einmal analysiert und als Falsch-Alarm eingestuft — TASK-42 ist ein zu diesem Zeitpunkt (2026-06-25) bereits veralteter, nicht mehr zutreffender automatischer Fund, der nie geschlossen wurde.

⚠️ **Kleine offene Unstimmigkeit (unkritisch):** Der Ausschlusslisten-Kommentar im Code verweist auf „TASK-43" als Quelle dieses Fixes. Ein Ticket mit dieser Nummer existiert im aktuellen Backlog nicht (weder offen noch archiviert). Vermutlich ein interner Verweisfehler beim Eintragen des Ausschlusses (z. B. Verwechslung mit einer anderen Ticket-ID) oder das Ticket wurde bei einem früheren Backlog-Cleanup vollständig entfernt statt archiviert. ⚠️ Annahme: Das ist ohne Auswirkung auf TASK-42 — der Ausschluss selbst ist im Code vorhanden und korrekt, unabhängig davon welche Ticket-ID ihn ursprünglich veranlasst hat. Keine weitere Recherche nötig, außer Stephan möchte den Backlog-Verlauf aus anderen Gründen nachvollziehen.

---

### Example Mapping

**Regel 1: Ein Ticket wird nur umgesetzt, wenn sein Befund am aktuellen Code noch zutrifft**

Kontext: Automatisch erzeugte Refactoring-Tickets basieren auf einem Analyse-Lauf zu einem bestimmten Zeitpunkt. Ändert sich der Code (oder wird der Mess-Fehler selbst behoben), kann der ursprüngliche Befund veralten.

- ✅ Positiv: Code-Verifikation zeigt, dass `local` (1 Zeile) und `row` (12 Zeilen) weit unter dem 80-Zeilen-Threshold liegen → kein Refactoring-Bedarf, Ticket wird als „bereits erledigt/falsch-positiv" geschlossen statt umgesetzt.
- ❌ Negativ: Hätte die Verifikation bestätigt, dass die Funktionen wirklich mehrere hundert Zeilen umfassen, wäre eine Aufteilung wie ursprünglich beschrieben nötig gewesen.

**Regel 2: Kein Refactoring ohne echten Verhaltens-Nutzen für Stephan**

Kontext: TASK-42 ist ein reines Code-Aufräum-Ticket ohne sichtbare App-Wirkung. Wird umgesetzt, obwohl der zugrunde liegende Befund falsch ist, entsteht Aufwand ohne Nutzen und ein unnötiges Regressionsrisiko an zwei funktionierenden, viel genutzten Stellen (Kamera-Profil-Laden, Astro-Ausrichtungsanzeige).
- ✅ Positiv: Ticket wird geschlossen statt umgesetzt, kein Code wird angefasst, kein Testaufwand entsteht.

---

### Akzeptanzkriterien

Da der Kernbefund lautet „kein Refactoring nötig", gibt es keine App-Verhaltens-AKs für eine Code-Aufteilung. Stattdessen gelten AKs für den korrekten Ticket-Abschluss:

- [x] AK-1: Das Ticket wird **nicht** implementiert — `web/index.html` bleibt an den Stellen `CameraFOV._loadProfile()` und `AstroMap._draw()` unverändert.
- [x] AK-2: Stephan bestätigt den Befund (Ticket beruht auf veraltetem/fehlerhaftem automatischem Fund), danach wird TASK-42 auf „Done" mit Vermerk „kein Handlungsbedarf — Falsch-Positiv" gesetzt statt normal durch Implementierung/Test/Release zu laufen.
- [x] AK-3 (Regression, indirekt): Kamera-Profil-Laden (Einstellungen → Kamera-Sensor/Brennweite) und die Astro-Ausrichtungsanzeige (Sonne/Mond/Milchstraße-Zeile in der Karten-/Location-Detailansicht) funktionieren unverändert weiter, weil an ihnen nichts geändert wird — keine gesonderte Testrunde nötig.

---

### Pre-Mortem

**Risiko 1 — Ticket wird trotzdem „nach Vorschrift" umgesetzt, weil die Beschreibung ungeprüft übernommen wird**
Auslöser: Wer nur die Ticket-Beschreibung liest (nicht den Code), hält „~265 Zeilen" und „~1034 Zeilen" für bare Münze und beginnt eine unnötige Aufteilung an zwei kleinen, funktionierenden Codestellen.
Gegenmaßnahme: Code-Verifikation ist in dieser Spec bereits dokumentiert und mit Zeilenzahlen belegt (AK-1/AK-2 verhindern die Umsetzung).

**Risiko 2 — Verwechslung mit TASK-49, das echte lange Funktionen in derselben Datei listet**
Auslöser: TASK-49 (ToDo, noch offen) meldet sechs andere lange Funktionen in `web/index.html` (`ic()`, `handler()`, `verState()`, `sectorPath()`, `azDiffFn()`, `sunAlignmentLabel()` — die längste davon `sunAlignmentLabel()` mit ~1044 Zeilen). Es besteht Verwechslungsgefahr, TASK-42 fälschlich als „das große Refactoring-Ticket" zu behandeln.
Gegenmaßnahme: Explizit im Ticket-Text vermerken, dass TASK-49 unabhängig und weiterhin gültig ist (dort wurden echte lange Funktionen nicht auf die Ignorelist gesetzt) — TASK-42 betrifft ausschließlich die zwei genannten, bereits widerlegten Funktionen.

**Risiko 3 — Analyse-Werkzeug erzeugt erneut denselben Falsch-Alarm für andere Funktionen**
Auslöser: Die Regex-Heuristik in `refactor_check.py` hat eine bekannte strukturelle Schwäche (siehe Kommentar „TASK-32"). Weitere Falsch-Positive sind wahrscheinlich, solange kein echter JS-Parser eingesetzt wird.
Gegenmaßnahme: Kein Handlungsbedarf für TASK-42 selbst; als generelle Beobachtung für künftige `fotoalert-refactor`-Läufe festhalten — nicht Teil dieses Tickets.

---

### Architektur-Analyse

`CameraFOV._loadProfile()` (Kamera-Profil aus Server/localStorage laden, Migration zwischen beiden) und `AstroMap._draw()` (Zeichnen der Sonne/Mond/Milchstraße-Ausrichtungslinien inkl. Text-Zeile pro Himmelskörper) sind beide unauffällig kurz und in sich abgeschlossen. Es gibt keine strukturelle Verflechtung zwischen den beiden — sie liegen an völlig unterschiedlichen Stellen der Datei und haben nichts miteinander zu tun außer der gemeinsamen (falschen) Nennung in diesem Ticket.

---

### Implementierungsoptionen

Da der Befund widerlegt ist, gibt es keine sinnvollen Umsetzungsoptionen im ursprünglichen Sinn. Zur Vollständigkeit dennoch die Handlungsalternativen für den Ticket-Abschluss:

#### Option A — Ticket ohne Codeänderung schließen (empfohlen)
Vorgehen: TASK-42 wird mit Vermerk „Falsch-Positiv, Code bereits auf Ignorelist" auf Done gesetzt. Kein Codeeingriff, kein Test, kein Release nötig.
Vorteile: Kein Risiko, kein Aufwand, sauberer Backlog-Zustand.
Nachteile: Keine.
Aufwand: minimal (nur Ticket-Pflege).

#### Option B — Trotzdem eine kosmetische Mini-Aufteilung vornehmen
Vorgehen: `local` in eine benannte Helper-Funktion umwandeln, `row` unverändert lassen oder minimal umbenennen — rein um das Ticket „inhaltlich" zu bedienen.
Nachteile: Löst kein reales Problem, erzeugt unnötigen Diff und Regressionsrisiko an zwei funktionierenden Stellen, widerspricht dem Grundsatz „kein Scope Creep" und „keine Änderung ohne Nutzen".
Aufwand: klein, aber ohne Gegenwert.

✅ **Empfehlung: Option A** — der Befund ist durch Code-Lektüre eindeutig widerlegt (1 Zeile bzw. 12 Zeilen statt 265 bzw. 1034), beide Funktionen stehen bereits auf der Ignorelist des Analyse-Werkzeugs. Eine Umsetzung würde funktionierenden Code ohne Nutzen anfassen.

---

### Testplan

- [ ] Automatisiert: kein neuer Testfall nötig, da keine Codeänderung erfolgt.
- [ ] Manuell: keine Testschritte nötig. Falls Stephan zur Sicherheit gegenprüfen möchte: Einstellungen-Bereich öffnen und Kamera-Sensor/Brennweite ändern (prüft `CameraFOV._loadProfile()`-Pfad indirekt) sowie eine Location-Detailansicht mit Sonnen-/Mond-Ausrichtungsanzeige öffnen (prüft `AstroMap._draw()`/`row()`-Pfad indirekt) — beide sollten sich wie gewohnt verhalten, unverändert gegenüber vor diesem Ticket.

---

---

### BUG-46 · Filter-Inkonsistenz: Nicht alle Kriterien bieten aktiv/ausgeschlossen/deaktiviert an; kein Effekt auf Karte `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |

**Beschreibung:** Der Filter verhält sich in zwei Punkten inkonsistent:

1. **Fehlende Ausschluss-Option:** Nicht alle Filterkriterien bieten die drei Zustände „aktiv", „ausgeschlossen" und „deaktiviert" an. Beispiel: „Geprüfte/verifizierte Standorte" lässt sich nicht exkludieren — es gibt nur aktiv/inaktiv, aber kein „nur nicht-verifizierte zeigen".

2. **Kein Filter-Effekt auf Karte:** Die Kartenansicht ignoriert die gesetzten Filterkriterien vollständig. Die Filterung soll auf alle Ansichten wirken: Chance (14-Tage, Kalender, Scout), Locations-Liste **und** Karte.

**Zusatz:** Wenn ein Filterkriterium für eine Ansicht nicht relevant ist (z. B. ein Chancen-spezifisches Kriterium auf dem Locations-Tab), soll es ausgegraut oder ausgeblendet werden — statt inaktiv aber sichtbar zu bleiben und Verwirrung zu stiften.

---

#### 🔬 Analyse-Spec (BUG-46) · 2026-06-28

### Aktueller Produktstand

Der Filter hat aktuell **neun Kriterien**, von denen nur vier (Eventtyp, Tageszeit, Schwierigkeit, Kategorie) den Drei-Zustands-Mechanismus kennen — also: aktiv (Goldrand), ausgeschlossen (Rotrand), deaktiviert. Die anderen fünf Kriterien — Verifikationsstatus, Mindest-Bewertung (Sterne), Entfernung/GPS, Mindest-Wahrscheinlichkeit und Brennweite — sind einfache Auswahl-Chips oder Slider ohne Ausschluss-Option.

Der Verifikationsstatus bietet heute vier Optionen: „Alle", „Geprüfte", „Nicht geprüft", „Probleme". Man kann also „Nur geprüfte anzeigen" — aber nicht „Geprüfte ausblenden" als Ausschluss-Zustand. Analoges gilt für Bewertung und Entfernung: es gibt keinen „Exclude"-Pfad.

Die **Karte** (Map-Tab) reagiert heute nur auf einen einzigen Filter: den Eventtyp-Include-Filter. Alle anderen Kriterien — Tageszeit, Schwierigkeit, Kategorie, Verifikation, Bewertung, Score, Entfernung — werden auf der Karte vollständig ignoriert. Auch der Eventtyp-Exclude-Filter (Ausschluss) wird auf der Karte nicht berücksichtigt: wer z.B. „Mondaufgang" auf Ausgeschlossen setzt, sieht auf der Karte weiterhin alle Mondaufgang-Locations.

Der **Locations-Tab** filtert nach Schwierigkeit, Kategorie, Bewertung, Verifikation und Score — aber nicht nach Eventtyp oder Tageszeit (weil der Locations-Tab keine Chancen, sondern Standorte zeigt: das ist korrekt). Der **Kalender** und der **Scout** wenden die zutreffenden Filter korrekt an.

**Kurz:** Der Karten-Filter ist rudimentär (nur Eventtyp-Include, kein Exclude, keine anderen Kriterien). Der Verifikationsstatus-Filter kennt keinen echten Ausschluss-Zyklus.

---

### Example Mapping

**Regel 1: Jedes Filterkriterium bietet den Drei-Zustands-Zyklus, wo er semantisch sinnvoll ist**

Kontext: Stephan will gezielt „nur nicht-verifizierte Standorte" sehen, um zu entscheiden, welche er als nächstes prüfen soll — derzeit unmöglich ohne Kriterium „Verifikation = Nicht geprüft".

- ✅ Positiv: Stephan tippt auf „Geprüfte" im Verifikations-Abschnitt — beim zweiten Tap wechselt der Chip auf Rot (Ausschluss), die Liste zeigt nur nicht-verifizierte und problematische Standorte.
- ❌ Negativ: Stephan tippt zweimal auf „Geprüfte", aber nichts passiert beim zweiten Tap — nur ein/aus — Bug bleibt.
- ⚠️ Edge: Stephan hat sowohl „Geprüfte" auf Ausschluss als auch „Nicht geprüft" auf Ausschluss gesetzt → alle Verifikationszustände ausgeblendet → leere Liste mit Hinweis „0 Locations entsprechen den Kriterien", kein Crash.

**Regel 2: Die Karte zeigt nur Locations, die allen aktiven Filterkriterien entsprechen**

Kontext: Stephan setzt Schwierigkeit auf „Einfach" und schaut auf die Karte — er erwartet, nur einfache Standorte als Marker zu sehen.

- ✅ Positiv: Filter Schwierigkeit = Einfach aktiv → Karte zeigt nur Marker für einfache Locations. Anspruchsvolle Locations verschwinden.
- ❌ Negativ: Schwierigkeit = Einfach aktiv, Karte zeigt weiterhin alle Marker unverändert → Bug (Ist-Zustand).
- ⚠️ Edge: Filter Eventtyp = „Mondaufgang" auf Ausschluss + Karte offen → Locations, die im 14-Tage-Feed ausschließlich Mondaufgänge haben, verschwinden von der Karte.

**Regel 3: Die Karte berücksichtigt Eventtyp-Exclude korrekt**

Kontext: Im Feed hat Stephan „Goldene Stunde" auf Ausschluss gesetzt, schaut dann auf die Karte — er erwartet, dass Goldene-Stunde-Locations nicht hervorgehoben/sichtbar sind.

- ✅ Positiv: Eventtyp „Mondaufgang" auf Ausschluss → Karte blendet Locations aus, die im Feed ausschließlich Mondaufgänge haben. Locations mit mehreren Eventtypen bleiben sichtbar (da nur der ausgeschlossene Typ fehlt, aber andere vorhanden sind).
- ❌ Negativ: Eventtyp auf Ausschluss, Karte ändert sich nicht → Bug (Ist-Zustand).
- ⚠️ Edge: Eventtyp „Mond-Alignment" auf Ausschluss + Feed noch nicht geladen → Fallback auf `possible_bodies`: Locations ohne `moon` in `possible_bodies` bleiben sichtbar, Mond-Locations werden ausgeblendet.

**Regel 4: Nicht relevante Kriterien auf der Karte werden ausgegraut — nicht entfernt**

Kontext: Stephan öffnet den Filter im Map-Tab. „Mindest-Wahrscheinlichkeit" ist ein Chancen-Kriterium, nicht direkt auf Locations anwendbar — es soll erkennbar sein, dass dieser Slider hier nichts bewirkt.

- ✅ Positiv: Im Map-Tab ist „Mindest-Wahrscheinlichkeit" ausgegraut und deaktiviert (wie heute schon), mit Hinweis „Nur in Listen-Ansicht verfügbar". Alle anderen Kriterien sind aktiv.
- ⚠️ Edge: Stephan setzt auf dem Feed-Tab einen Score-Filter, wechselt zur Karte → Karte zeigt zwar keine Score-Filterung (Score ist Chancen-spezifisch), der gespeicherte Score-Wert bleibt aber erhalten und wirkt, wenn Stephan zurück zum Feed wechselt.

**Regel 5: Brennweiten-Filter wird auf Karte ausgegraut (da Chancen-spezifisch)**

Kontext: Brennweite ist an Chancen-Daten (camera_hints) geknüpft, nicht direkt an Locations. Eine Karten-Filterung nach Brennweite ist ohne Chancen-Kontext nicht sinnvoll.

- ✅ Positiv: Brennweiten-Slider im Map-Tab ausgegraut + Hinweistext, wie der Score-Slider heute.
- ⚠️ Edge: Brennweite im Locations-Tab: Location-Daten enthalten kein `camera_hints`-Feld direkt → ausgegraut (wie Karte). Brennweiten-Filter wirkt nur auf Chancen-Ansichten (Feed/Kalender/Scout).

---

### Akzeptanzkriterien

- [ ] AK-1: Im Filter-Sheet kann ich den Verifikationsstatus durch Antippen durchschalten: erster Tap = nur diese anzeigen (Goldrand), zweiter Tap = diese ausblenden (Rotrand), dritter Tap = zurück zu „Alle". Das gilt für alle vier Optionen (Geprüfte, Nicht geprüft, Probleme — „Alle" bleibt Ein-Zustand-Reset).
- [ ] AK-2: Im Filter-Sheet kann ich die Mindest-Bewertung nicht ausschließen (Sterne sind eine Mindest-Schwelle, kein Ausschluss) — der Bewertungs-Slider bleibt ein reiner Min-Wert-Filter. Dieser Abschnitt bleibt unverändert.
- [ ] AK-3: Die Karte zeigt nach dem Anwenden eines Schwierigkeits-Filters nur noch Marker für Locations mit der gewählten Schwierigkeit. Marker für andere Schwierigkeiten werden entfernt.
- [ ] AK-4: Die Karte berücksichtigt Kategorie-Filter: setze ich „Natur & Landschaft" auf aktiv, sind nur Natur-Locations als Marker sichtbar.
- [ ] AK-5: Die Karte berücksichtigt Verifikations-Filter: setze ich Verifikation auf „Geprüfte", sind nur verifizierte Locations auf der Karte sichtbar.
- [ ] AK-6: Die Karte berücksichtigt Eventtyp-Exclude: setze ich „Mondaufgang" auf Ausschluss, verschwinden Locations, die im Feed ausschließlich Mondaufgänge haben.
- [ ] AK-7: Die Karte berücksichtigt Entfernung/GPS: setze ich „< 5 km", sind nur Locations innerhalb von 5 km sichtbar (wenn GPS verfügbar). Kein GPS → Toast, kein Crash.
- [ ] AK-8: Mindest-Wahrscheinlichkeit und Brennweite bleiben auf der Karte ausgegraut (wie heute schon für Score — analog für Brennweite neu einführen). Ein erklärender Hinweis ist sichtbar.
- [ ] AK-9: Im Locations-Tab bleiben Eventtyp und Tageszeit ausgegraut (Chancen-spezifisch, keine direkte Location-Entsprechung). Ein Hinweis erklärt, warum.
- [ ] AK-10: Regression — Feed, Kalender und Scout reagieren weiterhin korrekt auf alle Filter. Kein Verlust bestehender Filterlogik.
- [ ] AK-11: Der Filter-Badge (Zahl oben rechts am Filter-Button) zählt den Verifikations-Ausschluss als aktives Kriterium (wie alle anderen Exclude-Zustände heute schon).

---

### Pre-Mortem

**Risiko 1 — Karten-Filter zu aggressiv: leere Karte bei kombinierten Kriterien**
Auslöser: Schwierigkeit + Kategorie + Verifikation kombiniert — viele Kriterien → nur 1–2 Locations übrig → Karte wirkt leer.
Gegenmaßnahme: Der Live-Zähler im Filter-Sheet zeigt schon beim Einstellen „X von Y Locations sichtbar". Kein eigener Schutz nötig, aber klar kommunizieren (AK-8: Score/Brennweite ausgegraut → erklärt, was warum nicht greift).

**Risiko 2 — Verifikations-Exclude-Logik korrekt umkehren**
Auslöser: Exclude bei `verified` soll Locations OHNE `ok`-Verifikation zeigen — falsch implementiert könnte es umgekehrt filtern.
Gegenmaßnahme: Bestehende `applyToLocations`-Logik für Verifikation als Referenz nehmen; Exclude = Negation der Include-Bedingung; Test mit bekannter verifizierten und nicht-verifizierten Location.

**Risiko 3 — MapView.applyFilter() läuft bevor Feed.data geladen**
Auslöser: Beim ersten App-Start ist `Feed.data` noch leer, der Karten-Filter für Schwierigkeit/Kategorie/Verifikation würde auf `Locations.all` zugreifen — das ist beim Tab-Wechsel ggf. noch nicht geladen.
Gegenmaßnahme: `Locations.all` wird beim Boot vorab geladen (bereits implementiert in `_boot()`). Defensive Guards behalten: `if (!Locations.all.length) return true`.

**Risiko 4 — Entfernung auf Karte: GPS-Abfrage-Timing**
Auslöser: GPS-Abfrage ist async, `MapView.applyFilter()` ist sync — wenn GPS noch nicht abgefragt, ist `Filter._gps` null.
Gegenmaßnahme: Verhalten wie heute im Feed: wenn `_gps === null` → Entfernung-Filter überspringen (alle anzeigen). Beim Anwenden wird GPS im `FilterSheet.apply()` vorab abgefragt — dasselbe Muster für die Karte anwenden.

**Risiko 5 — Graue Abschnitte im Filter-Sheet pro Ansicht unterschiedlich**
Auslöser: Die Grau-Logik muss bei jedem `_render()`-Aufruf den aktuellen Tab (`App.current` und `Feed.mode`) kennen — bisher nur für Score und Map-Tab implementiert. Falsches Grauen kann verwirrend sein.
Gegenmaßnahme: Eine zentrale Hilfsfunktion `_isDisabled(criterium)` die auf `App.current` und `Feed.mode` prüft; klar definieren welche Kriterien wo sinnlos sind (Tabelle unten in Implementierungsoptionen). Manuell alle vier Haupt-Tabs nach Grau-Logik testen.

---

### Implementierungsoptionen

#### Option A — Schrittweise Erweiterung: erst Verifikations-Exclude, dann Karten-Filter

**Phase 1 — Verifikationsstatus erhält Drei-Zustands-Zyklus**
Vorgehen: `verChips` in `FilterSheet._render()` von `chip()`-Generierung auf `chip3()` umstellen. Neue State-Variable `verificationExcl` in `Filter._defaults()` einführen. `_cycle`-Mechanismus für Verifikation anpassen (Besonderheit: Verifikation ist ein Enum, kein Array — hier `verification` als Include-Wert und `verificationExcl` als Exclude-Wert). `Filter.apply()`, `Filter.applyToLocations()` und `MapView.applyFilter()` um Exclude-Pfad für Verifikation erweitern.

**Phase 2 — Karten-Filter vollständig**
Vorgehen: `MapView.applyFilter()` um alle Location-relevanten Kriterien erweitern: Schwierigkeit (incl + excl), Kategorie (incl + excl), Verifikation (incl + excl), Entfernung/GPS (async, vorab abgefragt), Mindest-Bewertung. Code aus `Filter.applyToLocations()` wiederverwenden — der Code ist bereits vorhanden, muss nur in `applyFilter()` aufgerufen werden.

**Phase 3 — Ausgrau-Logik pro Tab vollständig**
Vorgehen: Zentrale `_isDisabled(criterium)` Funktion. Brennweite auf Karte + Locations ausgegraut. Eventtyp + Tageszeit auf Locations ausgegraut. Score + Brennweite auf Karte — wie bisher für Score, neu für Brennweite.

Betroffene Dateien: `web/index.html` (Filter, FilterSheet, MapView.applyFilter)
Vorteile: inkrementell, jede Phase einzeln testbar, geringes Regressions-Risiko
Aufwand: mittel (Phase 1: klein, Phase 2: mittel, Phase 3: klein)

#### Option B — Alles in einem Zug: einheitliche Architektur

Vorgehen: `applyToLocations()` wird zur einzigen Filterquelle für alle Location-Ansichten (Locations-Tab UND Karte). `MapView.applyFilter()` ruft `Filter.applyToLocations()` auf statt eigene Logik zu duplizieren. Verifikation und Eventtyp werden gleichzeitig auf Drei-Zustände umgebaut. Ausgrau-Logik als Teil desselben Commits.

Betroffene Dateien: `web/index.html`
Vorteile: eine Quelle der Wahrheit, kein Code-Duplikat zwischen `applyToLocations` und `applyFilter`
Nachteile: größerer Diff, schwieriger zu testen/zu bisecten wenn ein Fehler auftritt; `MapView.applyFilter()` hat Feed-basierte Logik (Eventtyp via Feed.data), die nicht in `applyToLocations()` steckt → muss zusammengeführt werden (aufwendiger)
Aufwand: mittel-groß

---

### Empfehlung

**Option A (Phase 1 → 2 → 3)** ist die klare Empfehlung. Die bestehende `Filter.applyToLocations()`-Logik ist vollständig und korrekt — `MapView.applyFilter()` muss sie nur noch anwenden. Phase 2 kann dafür auf denselben Code zugreifen, ohne ihn zu duplizieren: `MapView.applyFilter()` kann die Location-Attribute direkt prüfen (Referenz auf `Filter.applyToLocations()` als Template). Das minimiert das Regressions-Risiko und macht jeden Schritt einzeln testbar. Option B verlockt zu vorzeitiger Abstraktion an einer Stelle, die stabilen Code hat.

---

### Kriterien-Übersicht: Was wirkt wo?

| Kriterium | Drei-Zustände heute? | Feed/Kalender | Scout | Locations-Tab | Karte (Ist) | Karte (Soll) |
|-----------|---------------------|---------------|-------|---------------|-------------|--------------|
| Eventtyp | ✅ ja | ✅ | ✅ (Mapping) | ⬜ ausgr. | ✅ (nur Incl.) | ✅ Incl. + Excl. |
| Tageszeit | ✅ ja | ✅ | ✅ | ⬜ ausgr. | ❌ nein | ⬜ ausgr. |
| Schwierigkeit | ✅ ja | ✅ | ❌ ausgr. | ✅ | ❌ nein | ✅ Incl. + Excl. |
| Kategorie | ✅ ja | ✅ | ❌ ausgr. | ✅ | ❌ nein | ✅ Incl. + Excl. |
| Verifikation | ❌ nur Auswahl | ✅ | ❌ ausgr. | ✅ | ❌ nein | ✅ + Excl. neu |
| Mindest-Bewertung | ❌ Slider | ✅ | ❌ ausgr. | ✅ | ❌ nein | ✅ |
| Mindest-Score | ❌ Slider | ✅ | ✅ | ✅ (via Feed) | ⬜ ausgr. | ⬜ bleibt ausgr. |
| Brennweite | ❌ Dual-Slider | ✅ | ✅ | ❌ ausgr. | ❌ ausgr.* | ⬜ ausgr. + Hinweis |
| Entfernung/GPS | ❌ Auswahl | ✅ | ✅ | ❌ (kein GPS-Check) | ❌ nein | ✅ |

*Brennweite auf Karte: aktuell nicht explizit ausgegraut, aber faktisch ohne Effekt.

---

### Offene Fragen / Assumptions

**F1 — Verifikations-Exclude: Welche Semantik soll „Geprüfte ausblenden" haben?**
✅ **Entschieden 2026-06-28:** Exclude = zeige nicht-geprüfte UND problematisch markierte Locations (alle außer verifiziert-ok).

**F2 — Karten-Filter für Tageszeit: sinnvoll oder ausgegraut?**
✅ **Entschieden 2026-06-28:** Tageszeit auf der Karte ausgegraut (keine Filterung).

**F3 — Mindest-Bewertung: Soll die Karte nach Bewertung filtern?**
Annahme: Ja — Bewertungen sind an Locations geknüpft, nicht an Chancen. Der Code dafür existiert bereits. Die Karte kann ihn direkt nutzen. → Im Soll als ✅ markiert.

**F4 — Drei-Zustände für „Mindest-Bewertung"?**
✅ **Entschieden 2026-06-28:** Ja, Mindest-Bewertung bekommt Drei-Zustände. „Ausschließen"-Modus kehrt die Logik um: statt „zeige nur ≥ N Sterne" zeigt er „zeige nur < N Sterne". Anwendungsfall: gezielt niedrig bewertete Locations ansehen. „Entfernung" bleibt einfacher Filter ohne Drei-Zustände (Obergrenze, kein sinnvoller Ausschluss).

---

**Analyse:** ✅ fertig 2026-06-28
**Alle offenen Fragen:** ✅ geklärt 2026-06-28 — bereit für Weg-Gate

---

### US-105 · Chancen-Detail: Sektionsreihenfolge optimieren (Beschreibung zuerst, Wetter nach Zeitfenster, Kompositions-Analyse nach Karte) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |

**Beschreibung:** Die Sektionsreihenfolge im Chancen-Detail-Sheet soll thematisch optimiert werden: BESCHREIBUNG kommt als erstes (Kontext zuerst), WETTER direkt nach IDEALES ZEITFENSTER (zeitlich zusammengehörig), KOMPOSITIONS-ANALYSE direkt nach KARTE & BLICKWINKEL (räumlich/visuell zusammengehörig).

**Neue Reihenfolge:**
1. BESCHREIBUNG
2. IDEALES ZEITFENSTER
3. WETTER ZUM SHOOT-ZEITPUNKT
4. KARTE & BLICKWINKEL
5. KOMPOSITIONS-ANALYSE
6. KOORDINATEN
7. HIMMELSPOSITION
8. KAMERA-EMPFEHLUNGEN
9. ASTRONOMIE
10. STANDORT & TOPOGRAPHIE
11. HIMMELSKÖRPER-BAHNEN

**Bezug:** Folgt auf US-96 (hat die aktuelle Reihenfolge eingeführt). Berührt dieselbe Datei (`web/index.html`, `Detail.open()`). Keine Blocking-Dependency mehr (BUG-45 gelöscht). Kein Working-Tree-Konflikt vorhanden (letzter Commit auf web/index.html: v1.19.1 US-104).

**Akzeptanzkriterien:**
- [ ] Öffne im Browser ein beliebiges Feed-Chance-Detail → die erste sichtbare Sektion ist „BESCHREIBUNG" (der erklärende Text zur Fotoopportunity)
- [ ] Direkt unter dem Zeitfenster erscheinen sofort die Wetterdaten — nicht erst nach Himmelsposition oder anderen Sektionen
- [ ] Direkt unter der Karte & Blickwinkel-Sektion erscheint die Kompositions-Analyse (wenn vorhanden) — nicht ganz unten
- [ ] Öffne ein Scout-Detailsheet → kein JavaScript-Fehler in der Console, Kompositions-Analyse erscheint nicht (Scout hat keine), Layout intakt
- [ ] Öffne ein Kalender-Event-Detail → kein Fehler, alle verfügbaren Sektionen zeigen korrekt an
- [ ] Die relative Reihenfolge von KOORDINATEN → HIMMELSPOSITION → KAMERA-EMPFEHLUNGEN → ASTRONOMIE → STANDORT & TOPOGRAPHIE → HIMMELSKÖRPER-BAHNEN ist unverändert gegenüber heute

---

#### Implementation Spec

**Analysiert:** 2026-06-28

---

##### Scope-Klärung

- Betrifft **alle Event-Typen** (Goldene Stunde, Mondaufgang, Milchstraße, Sonnenuntergang etc.) — `Detail.open()` ist eine einzige Renderfunktion für alle Typen.
- Betrifft **alle Entry-Points** (Feed, Kalender, Scout), da alle `Detail.open(obj)` aufrufen. Die Reihenfolge der Sektions-Blöcke im Template ist Entry-Point-unabhängig.
- **Scout-Objekte** haben kein `composition_analysis`-Feld → `ev_kompo` wird nicht gerendert (Guard `if (!ca) return ''` greift). Reihenfolge trotzdem korrekt, da der leere String kein Layout bricht.
- **Kalender-Events** ohne enriched Daten: Wetter, Kompositions-Analyse und Kamera-Empfehlungen fehlen im Objekt → die entsprechenden Sektionen rendern leer oder fallen weg. Kein Problem durch die Umstrukturierung — die Guards in den IIFE-Blöcken bleiben unverändert.
- **Himmelsposition (ev_skypos)** hat einen eigenen Guard (`EV_SKYPOS_EXEMPT`-Set + `if (!ca)`). Bleibt unverändert an seiner neuen Position (nach KOORDINATEN).

---

##### Aktuelle Sektionsreihenfolge im Code (web/index.html, ~Zeile 3214–3418)

| # | ID | Titel | Zeile |
|---|-----|-------|-------|
| 1 | ev_zeit | Ideales Zeitfenster | ~3214 |
| 2 | ev_fov | Karte & Blickwinkel | ~3218 |
| 3 | ev_coords | Koordinaten | ~3220 |
| 4 | ev_skypos | Himmelsposition | ~3306 |
| 5 | ev_wetter | Wetter zum Shoot-Zeitpunkt | ~3323 |
| 6 | ev_kamera | Kamera-Empfehlungen | ~3325 |
| 7 | ev_astro | Astronomie | ~3326 |
| 8 | ev_topo | Standort & Topographie | ~3348 |
| 9 | ev_astro_live | Himmelskörper-Bahnen | ~3350 |
| 10 | ev_desc | Beschreibung | ~3351 |
| 11 | ev_kompo | Kompositions-Analyse | ~3405 |

---

##### Ziel-Sektionsreihenfolge

| # | ID | Titel |
|---|-----|-------|
| 1 | ev_desc | Beschreibung |
| 2 | ev_zeit | Ideales Zeitfenster |
| 3 | ev_wetter | Wetter zum Shoot-Zeitpunkt |
| 4 | ev_fov | Karte & Blickwinkel |
| 5 | ev_kompo | Kompositions-Analyse |
| 6 | ev_coords | Koordinaten |
| 7 | ev_skypos | Himmelsposition |
| 8 | ev_kamera | Kamera-Empfehlungen |
| 9 | ev_astro | Astronomie |
| 10 | ev_topo | Standort & Topographie |
| 11 | ev_astro_live | Himmelskörper-Bahnen |

**Änderungen gegenüber IST:**
- `ev_desc` (Beschreibung) von Position 10 → **Position 1** (ganz nach oben)
- `ev_wetter` (Wetter) von Position 5 → **Position 3** (direkt nach Zeitfenster)
- `ev_kompo` (Kompositions-Analyse) von Position 11 → **Position 5** (direkt nach Karte)
- `ev_coords`, `ev_skypos`, `ev_kamera`, `ev_astro`, `ev_topo`, `ev_astro_live` rutschen jeweils 1–2 Positionen nach hinten

---

##### Example Mapping

**Regel 1: Beschreibung steht als erste Sektion**
- ✅ Positiv: Nutzer öffnet Detailsheet einer Goldene-Stunde-Chance → erste Sektion ist BESCHREIBUNG mit dem Kontext-Text
- ✅ Positiv: Nutzer öffnet Detailsheet eines Mondaufgangs → erste Sektion ist BESCHREIBUNG
- ❌ Negativ (alt): Erste Sektion war IDEALES ZEITFENSTER — kein Kontext, Nutzer weiß nicht warum diese Chance interessant ist
- ⚠️ Edge: Scout-Objekt hat `description` als `desc`-String (adaptiert) → `ev_desc` rendert korrekt

**Regel 2: Wetter steht direkt nach Ideales Zeitfenster**
- ✅ Positiv: Nutzer sieht Zeitfenster 18:45–19:15, darunter sofort Wetterdaten (Bewölkung, Regen, Wind) — zeitlich zusammengehörige Info auf einen Blick
- ❌ Negativ (alt): Wetter stand nach Himmelsposition — thematisch getrennt von Zeitfenster
- ⚠️ Edge: Wetter nicht verfügbar (Event > 3 Tage) → Sektion zeigt Platzhalter-Hinweis „Verfügbar ab T-3 Tage" — bleibt korrekt

**Regel 3: Kompositions-Analyse steht direkt nach Karte & Blickwinkel**
- ✅ Positiv: Nutzer sieht Karte mit Standort + FOV-Overlay, darunter sofort die Kompositions-Analyse (Azimut-Versatz, Größenverhältnis) — räumlich zusammengehörig
- ❌ Negativ (alt): Kompositions-Analyse war letzte Sektion — räumlich von der Karte getrennt
- ⚠️ Edge: Kein `composition_analysis`-Feld im Objekt (Scout, Goldene Stunde etc.) → `ev_kompo` rendert '' → kein Layout-Problem; `ev_coords` folgt direkt auf `ev_fov`

**Regel 4: Alle anderen Sektionen bleiben in unveränderter relativer Reihenfolge**
- ✅ Positiv: KOORDINATEN, HIMMELSPOSITION, KAMERA, ASTRONOMIE, TOPOGRAPHIE, BAHNEN — relative Reihenfolge untereinander identisch zu IST

---

##### Pre-Mortem (Was könnte schiefgehen?)

1. **Falsche Zeilen-Referenz beim Edit:** Die Sektionen sind kein Array, sondern sequenzielle Template-Literal-Blöcke in einem großen Template-String. Ein Edit, der zu wenig Kontext mitgibt, kann an die falsche Stelle treffen (Edit-Tool-Zielpassage-Problem). → Gegenmaßnahme: Jede Sektion hat eindeutige IDs (`ev_desc`, `ev_kompo` etc.) als Anker; gezielt per Read+Grep vor dem Edit die genaue Zielstelle lesen.

2. **IIFE-Blöcke (`${ (() => { ... })() }`) beim Umordnen vergessen zusammenzuhalten:** `ev_skypos`, `ev_wetter`, `ev_topo`, `ev_kompo`, `ev_fov` sind in IIFE-Blöcke eingebettet. Beim Ausschneiden und Einfügen muss der gesamte `${(() => { ... })()}` Block inklusive öffnender und schließender Klammern vollständig verschoben werden, sonst entsteht ein JS-Syntaxfehler. → Gegenmaßnahme: Read des gesamten Abschnitts von ~3214 bis ~3419 vor dem Edit; jeden IIFE-Block vollständig identifizieren.

3. **ev_kompo ist tief verschachtelt (ab ~Zeile 3352–3418):** Der Kompositions-Analyse-Block ist mit ~65 Zeilen der längste einzelne Sektions-Block. Beim Verschieben auf Position 5 muss er vollständig an die richtige Stelle — zwischen `ev_fov` und `ev_coords`. → Gegenmaßnahme: Block vollständig auslesen, dann als ganzes Stück an neuer Position einfügen.

4. **Scout-adapted-Objekt hat kein `composition_analysis`:** Guard `if (!ca) return ''` in `ev_kompo` und `ev_skypos` muss nach dem Umordnen noch korrekt greifen. Da der Guard im IIFE-Block selbst sitzt (nicht im umgebenden Template), ist er durch das Umordnen nicht gefährdet. → Gegenmaßnahme: Nach Impl. manuell Scout-Detailsheet öffnen und prüfen, dass keine JS-Fehler erscheinen.

5. **Regression auf Kalender-Entry-Point:** BUG-44 zeigt, dass Kalender-Events weniger Felder haben. Die neue Reihenfolge ändert die Guards nicht — `ev_desc` rendert immer (wenn `o.description` vorhanden), `ev_wetter` rendert Platzhalter wenn `!wd`. Keine Regression erwartet, aber: nach Impl. Kalender-Detailsheet öffnen und prüfen.

---

##### Architektur-Analyse

**Wo ist die Reihenfolge definiert?**
Alle `mkSec()`-Aufrufe und IIFE-Blöcke befinden sich sequenziell im Template-String innerhalb von `Detail.open()` in `web/index.html` (ab ~Zeile 3190). Die Reihenfolge ergibt sich aus der physischen Reihenfolge der Ausdrücke im Template-Literal — es gibt kein Array, kein Switch, keine Konfiguration. Umordnen = Blöcke im Template physisch umhängen.

**Entry-Points:**
- **Feed** (Zeile 1378): `onclick="Detail.open(${JSON.stringify(o)...})"` — vollständiges opportunities.json-Objekt
- **Kalender** (Zeile 1928): `onclick="Detail.open(${JSON.stringify(e)...})"` — calendar.json-Event (astronomy-only)
- **Scout** (Zeile 1738): `Detail.open(adapted)` — Scout-adaptiertes Objekt ohne `composition_analysis`, `weather_details`, `elevation_difference_m`

Die `Detail.open()`-Funktion ist für alle Entry-Points identisch. Guards in jedem Sektions-Block (`if (!ca)`, `if (!wd)`, `if (!distKm && ...)`) stellen sicher, dass fehlende Felder keine Fehler produzieren.

---

##### Implementierungsoptionen

**Option A — Direkte Blockverschiebung im Template (empfohlen)**
Die Sektions-Blöcke werden in der Datei `web/index.html` durch gezielte Edit-Operationen in die neue Reihenfolge gebracht. Jeder Block wird mit seiner vollständigen `${...}`-Syntax ausgeschnitten und an der Zielposition eingefügt. Vier separate Edit-Operationen (ev_desc nach oben, ev_wetter nach oben, ev_kompo an Position 5, Rest rutscht nach).

- ✅ Minimal invasiv: nur Reihenfolge, kein Logik-Change
- ✅ Alle Guards und IDs bleiben unverändert
- ✅ Testbar sofort nach Speichern im lokalen Dev-Server
- ⚠️ Edit-Tool muss genug Kontext haben — vorher gezielt lesen

**Option B — Sektionen in ein Array auslagern und dann sortieren**
Die Sektions-Blöcke werden in ein Array von `{id, html}`-Objekten umgebaut und dann per Array-Literal in gewünschter Reihenfolge zusammengeführt.

- ❌ Erheblicher Umbau für minimalen Gewinn (reine Reihenfolge-Änderung)
- ❌ Erzeugt unnötige Komplexität im Code (Qualität vor Geschwindigkeit: sauberer ist kleiner)
- Nicht empfohlen

**Empfehlung: Option A** — minimaler, chirurgischer Eingriff. Vier Edit-Operationen, kein Logik-Change, vollständig reversibel.

---

##### Tests

**Vorbedingung:** Lokaler Dev-Server läuft und antwortet auf Health-Check.

**T1 — Feed, Event mit vollständigen Daten (Goldene Stunde o.ä.)**
- Öffne Feed → tippe auf eine Chance → Detailsheet öffnet sich
- Erwartete Reihenfolge der sichtbaren Sektionen (von oben nach unten): BESCHREIBUNG · IDEALES ZEITFENSTER · WETTER · KARTE & BLICKWINKEL · [KOMPOSITIONS-ANALYSE falls Alignment-Event] · KOORDINATEN · [HIMMELSPOSITION falls Alignment] · KAMERA-EMPFEHLUNGEN · ASTRONOMIE · [TOPOGRAPHIE falls vorhanden] · HIMMELSKÖRPER-BAHNEN

**T2 — Feed, Event ohne composition_analysis (Goldene Stunde)**
- KOMPOSITIONS-ANALYSE und HIMMELSPOSITION sollen nicht erscheinen
- Keine JS-Fehler in der Konsole

**T3 — Feed, Event ohne Wetterdaten (> 3 Tage)**
- WETTER zeigt Platzhalter „Verfügbar ab T-3 Tage" — erscheint trotzdem an Position 3 (direkt nach Zeitfenster)

**T4 — Scout-Detailsheet**
- Scout öffnen → Standort antippen → Detail öffnet sich
- BESCHREIBUNG als erste Sektion, WETTER an Position 3
- Keine KOMPOSITIONS-ANALYSE (kein `composition_analysis` im Scout-Objekt) — kein Fehler

**T5 — Kalender-Detailsheet**
- Kalender → Event antippen → Detail öffnet sich
- BESCHREIBUNG als erste Sektion
- Wetter zeigt Platzhalter (Kalender-Events haben kein `weather_details`)
- Keine JS-Fehler

**T6 — Regression: alle bestehenden Sektionen noch vorhanden**
- Für einen Feed-Alignment-Event (z.B. Mondaufgang hinter Turm) alle 11 Sektionen der Zielreihenfolge bestätigen

---

##### Dateien

- `web/index.html` — einzige zu ändernde Datei; Detail-Sheet-Template ab ~Zeile 3190

---

##### Offene Fragen / Assumptions-Protokoll

- **BUG-45 (gelöscht):** War als Blocking-Dependency genannt; wurde durch BUG-46 (Filter-Inkonsistenz) ersetzt. US-105 hat keine Blocking-Dependency mehr.
- **BUG-44** (Kalender-Event-Detail fehlende Sektionen): Separat getracktes Ticket. US-105 ändert die Reihenfolge, BUG-44 wird die fehlenden Daten nachliefern. Beide Tickets sind unabhängig umsetzbar — US-105 verschlechtert BUG-44 nicht, verbessert ihn aber auch nicht.

---

### BUG-44 · Kalender-Event-Detail: Wetter, Kamera-Empfehlung und Kompositions-Analyse fehlen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-27 |
| **Abgeschlossen** | 2026-06-28 |

**Beschreibung:** Wenn man im 365-Tage-Kalender auf ein Event tippt, öffnet sich das Detailsheet — aber die Sektionen Wetter, Kamera-Empfehlungen und Kompositions-Analyse fehlen. Im 14-Tage-Feed sind dieselben Sektionen für dasselbe Event vollständig vorhanden.

**Ursache:** `Detail.open()` ist für beide Einstiegspunkte identisch, aber die Event-Objekte unterscheiden sich. Kalender-Events stammen aus `calendar.json` (astronomy-only, ohne Wetter- und Kompositionsfelder). Feed-Events stammen aus `opportunities.json` (vollständige Daten mit allen enriched Feldern). Das Detail-Sheet rendert nur, was im übergebenen Objekt vorhanden ist.

**Lösungsidee:** Liegt ein Kalender-Event innerhalb des 14-Tage-Fensters, beim Antippen den enriched Event aus dem Feed-Cache (`opportunities.json`) anhand einer passenden Kennung (Location-ID + Event-Zeitstempel) suchen und dieses vollständige Objekt stattdessen an `Detail.open()` übergeben. Liegt das Event außerhalb des 14-Tage-Fensters, bleibt das Verhalten unverändert (kein Wetter verfügbar — korrekt so).

**Ziel:** Wenn ein Event im 14-Tage-Fenster liegt, ist das Detailsheet aus dem Kalender inhaltlich und in der Reihenfolge identisch mit dem aus dem Feed — gleiche Sektionen, gleiche Reihenfolge, gleiches Design.

**Bezug:** Folgeticket von US-96 (einheitliche Detailansicht). Die Reihenfolge der Sektionen ist durch US-96 garantiert; dieses Ticket stellt sicher, dass auch die Inhalte vollständig sind.

**Abgrenzung:** Kein Umbau von `Detail.open()` selbst; reine Lookup-Logik im Kalender-Tab-Handler. Events außerhalb des Feed-Zeitfensters sind bewusst ausgenommen.

---

#### Analyse (BUG-44) — 2026-06-28

##### 📎 Code-Verifikation

Gelesen: `backend/precompute.py` (Z. 378–462), `backend/main.py` (Z. 347–427), `web/index.html` (Z. 3160–3393)

**Bestätigt:**
- Kalender-Events und Feed-Events durchlaufen identisch `_serialize()` → beide haben `camera_hints` und `composition_analysis`.
- `astronomy_only=True` betrifft nur den Wetter-Score-Berechnungsweg — kein Einfluss auf `camera_hints` oder `composition_analysis`.
- Das Wetter-Overlay (`_weather_overlay()` in `main.py`) befüllt **ausschließlich** `_feed_cache`, nie `_calendar_cache`. Kalender-Events erhalten daher: `weather_score: 0.0`, `weather_description: ""`, und **kein `weather_details`-Objekt** (das Dict existiert im Kalender-Event schlicht nicht).
- Im Detail-Sheet rendert die Wetter-Sektion bei `!o.weather_details` → Platzhalter "Verfügbar ab T-3 Tage" — auch wenn das Event morgen stattfindet und echte Wetterdaten vorliegen.
- `camera_hints` Guard: `${hints ? mkSec(...) : ''}` — rendert wenn `camera_hints` befüllt. `composition_analysis` Guard: `if (!ca) return ''` — rendert wenn vorhanden. Beide Felder sind in Kalender-Events vorhanden.

**Widerlegt:**
- Ticket-Beschreibung: "ohne Wetter- und Kompositionsfelder" ist zu weit gefasst. Tatsächlich fehlt **nur `weather_details`** (das Wetter-Detailobjekt). Kamera-Empfehlungen und Kompositions-Analyse sind in `calendar.json` vorhanden — aber ggf. durch den Dedup-Mechanismus im Feed-Cache angereichert oder durch unterschiedliche Min-Score-Schwellen (Feed: 0.30–0.35, Kalender: 0.40) leicht unterschiedlich befüllt.

**Ursache-Präzisierung:** Das Problem ist ausschließlich das fehlende `weather_details`-Objekt. Kamera und Komposition sind da, aber der Nutzer sieht ggf. leere Kamera-Sektion wenn für einen bestimmten Event-Typ keine `camera_hints` berechnet werden — das wäre ein separates Problem.

---

##### Example Mapping

**📏 Rule 1 — Feed-Lookup bei Kalender-Events im 14-Tage-Fenster:**
Tippt der Nutzer im Kalender auf ein Event, das innerhalb der nächsten 14 Tage liegt, wird zunächst im Feed-Cache nachgeschlagen (Schlüssel: `location_id` + `shoot_time`). Wird ein Treffer gefunden, öffnet das Detailsheet mit dem enriched Feed-Event — inklusive Wetter.

🟢 Beispiel: Heute ist 28. Juni. Kalender zeigt ein Goldene-Stunde-Event am 30. Juni um 20:45 an Standort X. Im Feed existiert dasselbe Event. → Detailsheet zeigt Temperatur, Wolkendecke, Regenwahrscheinlichkeit.

🔴 Gegenbeispiel: Kalender zeigt Event am 15. August — liegt außerhalb T+14. → Detailsheet öffnet mit Kalender-Event, Wetter-Sektion zeigt "Verfügbar ab T-3 Tage" (korrekt).

**📏 Rule 2 — Kein Match im Feed = Kalender-Event als Fallback:**
Liegt das Event im 14-Tage-Fenster, aber kein passender Feed-Eintrag existiert (z.B. Score < Feed-Min-Score, Event durch Dedup entfernt), öffnet das Detailsheet trotzdem — mit dem Kalender-Event-Objekt. Kein Fehler, kein leerer Sheet.

🟢 Beispiel: Kalender-Event Score 0.41 (über Kalender-Schwelle 0.40), aber Feed-Schwelle 0.35 hat dieses Event durch Dedup wegoptimiert. → Detailsheet öffnet mit Kalender-Daten, Wetter-Sektion zeigt Platzhalter.

**📏 Rule 3 — Match-Schlüssel: location_id + shoot_time (exakt):**
Der Lookup verwendet `location_id` und `shoot_time` als kombinierten Schlüssel. Der Zeitstempel muss exakt übereinstimmen (beide aus `_serialize()` → ISO-Format).

🟢 Beispiel: Kalender-Event `{location_id: "alexanderplatz", shoot_time: "2026-06-30T18:45:00+00:00"}` findet Feed-Event mit identischen Feldern. → Match.

🔴 Edge Case: Minimal-Zeitabweichung durch Dedup (gleicher Tag, ähnliche Zeit, anderer Sekundenbruchteil) → kein Match. Kalender-Fallback greift.

**⚠️ Annahme: shoot_time-Format ist in beiden Quellen identisch** (beide via `_serialize()` → `.isoformat()`). Bestätigt durch Code-Verifikation.

**⚠️ Annahme: Feed.data ist beim Öffnen eines Kalender-Events garantiert geladen.** Der Feed lädt beim App-Start. Wenn Nutzer direkt zum Kalender-Tab navigiert (ohne je den Feed-Tab zu besuchen), könnte `Feed.data` leer sein. → Als Pre-Mortem-Szenario aufgenommen, Guard nötig.

---

##### Akzeptanzkriterien

- [x] **AK-1 (Wetter sichtbar):** Wenn ich im Kalender auf ein Event tippe, das heute oder in den nächsten 13 Tagen liegt, zeigt das Detailsheet die vollständige Wettersektion: Temperatur, Wolkendecke, Regenwahrscheinlichkeit, Windstärke und Sichtweite — genau wie im Feed-Tab für dasselbe Event.
- [x] **AK-2 (Wetter-Score sichtbar):** Der Wetter-Score im Dreierblock (Gesamt / Astronomie / Wetter) oben im Sheet ist nicht "–", sondern zeigt einen konkreten Prozentwert — identisch mit dem Feed-Detailsheet.
- [x] **AK-3 (Kein Unterschied zum Feed):** Wenn ich dasselbe Event im Feed und im Kalender antippe (beide innerhalb 14 Tage), sind Inhalt, Reihenfolge und Optik der Sektionen identisch.
- [x] **AK-4 (Außerhalb 14 Tage bleibt unverändert):** Ein Event, das in 15 Tagen oder später liegt, zeigt im Kalender-Detail "Wird 3 Tage vorher berechnet" in der Wettersektion. Keine Verschlechterung des heutigen Verhaltens.
- [x] **AK-5 (Kein Match = Fallback):** Wenn ein Event zwar innerhalb 14 Tage liegt, aber kein passender Feed-Eintrag existiert, öffnet das Sheet trotzdem mit den Kalender-Daten. Kein leerer Sheet, kein JavaScript-Fehler.
- [x] **AK-6 (Feed leer = Fallback):** Wenn `Feed.data` beim Antippen noch nicht geladen ist (z.B. wegen Netzwerkproblem), öffnet das Sheet trotzdem mit dem Kalender-Event. Kein Absturz.
- [x] **AK-7 (Kamera-Empfehlungen sichtbar):** Tippt man ein Mond-Alignment oder Golden-Hour-Event im Kalender an (innerhalb 14 Tage), ist die Kamera-Empfehlungs-Sektion im Sheet vorhanden — identisch mit dem Feed.
- [x] **Edge Case AK-8 (Tagesgrenze):** Ein Event exakt heute (shoot_time = jetzt oder in den nächsten Stunden) findet einen Feed-Match und zeigt vollständige Wetterdaten.

---

##### Pre-Mortem

💀 **Szenario 1: Feed.data ist beim Öffnen eines Kalender-Events noch nicht geladen**
- Auslöser: Nutzer öffnet App und navigiert sofort zum Kalender-Tab, bevor der Feed geladen ist (`Feed.data` ist `null` oder leeres Array).
- Frühwarnung: `Feed.data?.find(...)` würde `undefined` zurückgeben, nicht null — kein expliziter Fehler, aber immer Kalender-Fallback.
- Gegenmaßnahme: Guard `if (!Feed.data || !Feed.data.length)` vor dem Lookup → direkt Kalender-Event übergeben. In AK-6 verankert.

💀 **Szenario 2: shoot_time-Schlüssel stimmt nicht exakt überein**
- Auslöser: Kalender und Feed berechnen shoot_time leicht unterschiedlich (z.B. Sekunden-Rundung, Timezone-Suffix unterschiedlich `+00:00` vs `Z`).
- Frühwarnung: Kein Match obwohl Event sichtbar im Feed.
- Gegenmaßnahme: shoot_time-Vergleich auf Minuten-Niveau begrenzen (ersten 16 Zeichen: `"2026-06-30T18:45"`). Code-Verifikation zeigt: beide `_serialize()` via `.isoformat()` → identisches Format. Risiko niedrig, aber minutengenaue Vergleich macht Lookup robuster.

💀 **Szenario 3: Dedup oder Score-Schwelle entfernt Event aus Feed**
- Auslöser: Kalender-Event (min_score 0.40) hat kein Pendant im Feed, weil der Dedup-Mechanismus den Eintrag wegoptimiert hat oder der Score knapp unter Feed-Min-Score (0.35) liegt.
- Frühwarnung: In AK-5 bereits als gültiger Fallback beschrieben.
- Gegenmaßnahme: Fallback auf Kalender-Event, kein Fehler. Guard implementiert.

💀 **Szenario 4: Scope Creep — Kamera/Komposition werden "gefixt" obwohl nicht kaputt**
- Auslöser: Implementierung versucht auch camera_hints / composition_analysis zu "reparieren", obwohl sie im Kalender-Event bereits vorhanden sind.
- Frühwarnung: Unnötige Komplexität, potentielle Regression.
- Gegenmaßnahme: Klar im Scope halten — Impl. nur den Feed-Lookup für `weather_details`. Code-Verifikation bestätigt: camera_hints und composition_analysis brauchen keinen Fix.

💀 **Szenario 5: Regression im Feed-Tab oder Scout-Tab**
- Auslöser: Änderung am CalendarView-onclick-Handler beeinflusst versehentlich andere `Detail.open()`-Aufrufe.
- Frühwarnung: Nach Impl. Feed-Tab und Scout-Tab testen.
- Gegenmaßnahme: Änderung ist lokal im `onclick`-Template in `CalendarView.render()` (Z. 1928). Kein Einfluss auf andere Entry-Points. Regression-Check im Testplan.

---

##### Implementierungsoptionen

**Was bedeutet das für das App-Erlebnis:**

**Option A — Feed-Lookup im onclick-Aufruf (im CalendarView-Render):**
Beim Tippen auf ein Kalender-Event wird kurz im geladenen Feed nachgeschaut, ob es einen Eintrag mit gleicher Location und Uhrzeit gibt. Wenn ja, öffnet das Sheet mit den vollständigen Feed-Daten (inkl. Wetter). Wenn nein, öffnet es mit dem Kalender-Event wie bisher. Der Nutzer merkt nichts vom Lookup — das Sheet öffnet sich genau gleich schnell, aber mit Wetter-Infos.

**Option B — Eigener API-Aufruf beim Öffnen:**
Beim Tippen auf ein Kalender-Event wird ein separater API-Request an `/opportunities?location_id=...` gesendet, um den enriched Event live abzuholen. Das Sheet öffnet sich kurz leer/mit Ladeindikator, dann erscheinen die Daten. Das ist für den Nutzer spürbar langsamer und erfordert eine Netzwerkverbindung beim Tippen.

---

### Option A — Feed-Lookup im Frontend (empfohlen)

- **Vorgehen:** Im `onclick`-Template in `CalendarView.render()` (Z. 1928): vor `Detail.open(e)` aus `Feed.data` einen Match suchen (Schlüssel: `location_id` + erster 16-Zeichen-Block von `shoot_time`). Wenn Match → `Detail.open(match)`, sonst `Detail.open(e)`.
- **Betroffene Dateien:** `web/index.html` (eine Stelle: Z. ~1928, CalendarView-Render)
- **Vorteile:** Zero-Latenz (Feed ist bereits im Memory), keine neue Abhängigkeit, kein API-Call, kein Loading-State. Fallback ist eingebaut. Minimal invasiv.
- **Nachteile:** `Feed.data` muss geladen sein — Guard nötig (bereits in AK-6).
- **Aufwand:** Klein (~5 Zeilen JS)

### Option B — API-Lookup beim Öffnen

- **Vorgehen:** `Detail.open()` erweitern: bei Kalender-Events (erkennbar an fehlendem `weather_details`) live-Request an `/opportunities?location_id=X&event_type=Y` — dann den passenden Event finden.
- **Betroffene Dateien:** `web/index.html` (Detail-Objekt, Detail.open())
- **Vorteile:** Immer aktuellste Wetterdaten.
- **Nachteile:** Umbau von `Detail.open()` (explizit im Ticket ausgeschlossen), Netzwerkabhängigkeit, Loading-State, höhere Komplexität.
- **Aufwand:** Groß

✅ **Empfehlung: Option A** — Feed-Lookup im CalendarView-onclick. Minimal invasiv, zero Latenz, Fallback eingebaut, und entspricht genau der Lösungsidee im Ticket. Option B scheidet aus weil sie `Detail.open()` umbaut (explizit ausgeschlossen) und Netzwerk-Abhängigkeit beim Tippen einführt.

---

##### Scope

**Eingeschlossen:**
- Kalender-Events, die innerhalb T+0 bis T+13 (14-Tage-Fenster) liegen: Feed-Lookup + Detailsheet mit Wetter
- Fallback auf Kalender-Event wenn kein Match im Feed

**Ausgeschlossen:**
- Events außerhalb T+14 (kein Wetter verfügbar — intentional)
- Umbau von `Detail.open()` selbst
- Reparatur von camera_hints / composition_analysis (nicht kaputt)
- Neue API-Endpoints

---

##### Testplan

**Automatisiert (pytest):** Kein Backend-Change → kein pytest nötig. Der Fix ist rein Frontend-JS.

**Manuell:** Lokal testen unter http://localhost:8000

1. **Kalender-Event im 14-Tage-Fenster:**
   - Kalender-Tab öffnen → heutigen Monat anzeigen → Event für die nächsten 14 Tage antippen
   - Erwartet: Detailsheet zeigt Wetter-Sektion mit konkreten Werten (Temperatur, Wolken, Regen)
   - Verifikation AK-1 + AK-2

2. **Kalender-Event außerhalb 14 Tage:**
   - Kalender-Tab → zum übernächsten Monat navigieren → Event antippen
   - Erwartet: Wetter-Sektion zeigt "Wird 3 Tage vorher berechnet"
   - Verifikation AK-4

3. **Vergleich Feed vs. Kalender (dasselbe Event):**
   - Feed-Tab → Event innerhalb 14 Tage öffnen → Screenshot/Notiz aller Sektionen
   - Kalender-Tab → dasselbe Event antippen → Vergleich
   - Erwartet: identische Sektionen, identische Werte
   - Verifikation AK-3

4. **Regression Feed-Tab:** Feed-Event antippen → Detailsheet vollständig wie bisher.
5. **Regression Scout-Tab:** Scout-Event antippen → Detailsheet vollständig wie bisher.

---

##### Analyse & Planung

- [x] Code-Verifikation: `precompute.py` (Z. 378–462), `main.py` (Z. 347–427), `web/index.html` (Z. 1928, 3160–3393)
- [x] Datenstruktur-Diff: Kalender-Events fehlt `weather_details` (Objekt), Feed-Events haben es
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: nur `web/index.html` Z. ~1928 betroffen
- [ ] Implementierungsoptionen: A (empfohlen) / B
- [ ] Weg-Gate: Warten auf Stephans Freigabe


---

### BUG-48 · /opportunities-API liefert nur Mond-Events — Goldene/Blaue Stunde fehlen komplett `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-29 |
| **Abgeschlossen** | 2026-06-29 |

**Beschreibung:** Die `/opportunities`-API gibt 500 Events zurück, aber ausschließlich Mond-Events (Mondaufgang, Monduntergang, Milchstraße, Mond-Alignment). Goldene Stunde und Blaue Stunde erscheinen mit 0 Treffern — obwohl `opportunities.json` im Cache 910× Goldene Stunde Abend und 910× Blaue Stunde enthält.

**Root-Cause-Hypothese:** Die BUG-32-Sortierung priorisiert Nicht-Routine-Events (Mond, Milchstraße) vor Goldene/Blaue Stunde. Mit ~2298 Nicht-Routine-Events im 14-Tage-Cache füllen diese den `:500`-Cap vollständig — Routine-Events fallen heraus.

**Offene Prüffrage:** Gibt es überhaupt valide Goldene-Stunde- und Blaue-Stunde-Events im Cache mit `score ≥ 0.35`? Falls nicht, wäre das ein separates Datenproblem im Precompute (eigenes Ticket).

**Bezug:**
- Abhängig von / direkt verursacht durch die Sortierlogik aus BUG-32 (Sort-Key-Fix: Nicht-Routine-Events werden vorgezogen — verdrängt bei hohem Volumen Routine-Events)
- Grenzt an BUG-28 (Cap+Sort-Diagnose, `:500`-Cap-Verdrängung von seltenen Event-Typen) — gleiches strukturelle Problem, andere Manifestation
- Unabhängig von US-107 (Sonnen-Alignment-Planung, andere Feature-Dimension)

---

#### Analyse (BUG-48)

**Verifizierte Fakten (aus Code + Daten):**

- Cache `opportunities.json` enthält insgesamt **4.178 Events** (Schlüssel `opportunities`)
- Davon Routine-Events: **1.848** (Goldene Stunde Abend: 924, Blaue Stunde: 924)
- Davon Nicht-Routine: **2.330** (Monduntergang: 924, Mondaufgang: 858, Milchstraße: 528, Alignment: 18, Vollmond: 2)
- Nach Score-Filter (≥ 0.35) + Zeitfenster (14 Tage future): **3.912 Events** bleiben → alle Routine-Events sind valide (Score-Range 0.75–1.0)
- Nach Dedup: **3.899 Events** — immer noch weit über dem :500-Cap
- Sort-Key in `_filter_feed` (main.py, Zeile 1275): `(1 if routine else 0, shoot_time, -score)` → Non-Routine-Events (Wert 0) kommen ZUERST
- **Die ersten 500 Einträge nach Sort**: 264× Monduntergang + 235× Mondaufgang + 1× Alignment = **500 Nicht-Routine-Events, 0 Routine-Events**
- ✅ Prüffrage beantwortet: Routine-Events haben Scores 0.75–1.0, alle ≥ 0.35 → kein separates Datenproblem

**Scope:**

Der Sort-Key in `_filter_feed` (main.py, ca. Zeile 1272–1279) muss so angepasst werden, dass alle Event-Typen proportional im :500-Fenster vertreten sind. Der BUG-32-Fix (Non-Routine zuerst) war gedacht um seltene Events nicht zu verdrängen — hat aber das exakte Gegenteil bewirkt: häufige Mond-Events (1.650+ Einträge) verdrängen nun komplett die Routine-Events.

**Akzeptanzkriterien:**

- [ ] Wenn Stephan in der App den Feed öffnet, sieht er Goldene Stunde und Blaue Stunde im Feed — nicht ausschließlich Mond-Events
- [ ] Die API `/opportunities` (ohne Filter) gibt mindestens 100 Goldene-Stunde- und 100 Blaue-Stunde-Events zurück (bei 858 im validen Cache-Window)
- [ ] Mondaufgang und Monduntergang sind weiterhin im Feed sichtbar (werden nicht komplett verdrängt)
- [ ] Milchstraße und Mond-Alignment bleiben auffindbar (werden nicht durch Routine-Events verdrängt)
- [ ] Mit `?event_type=Goldene+Stunde+Abend` gibt die API korrekt nur Goldene-Stunde-Events zurück (bestehende Filter-Funktion unverändert)

**Example Mapping:**

Rule 1: Alle Event-Typen müssen im Feed erscheinen können
- ✅ Positiv: Feed mit Standardparametern enthält Goldene Stunde, Blaue Stunde, Mondaufgang, Monduntergang und Milchstraße gleichzeitig
- ❌ Negativ (aktueller Bug): Feed enthält 0× Goldene Stunde + 0× Blaue Stunde, obwohl 858 davon im Cache vorhanden sind
- 🔶 Edge: Wenn Cache ausschließlich Routine-Events enthält → Feed muss diese zeigen, nicht leer sein

Rule 2: Der :500-Cap darf keine Event-Typen systematisch ausschließen
- ✅ Positiv: Bei 3.899 validen Events nach Dedup ergibt ein fairer Schnitt proportionale Anteile (~130 pro Typ)
- ❌ Negativ: Sort-Key 0/1 für Non-Routine/Routine füllt die ersten 500 komplett mit Non-Routine-Events
- 🔶 Edge: Wenn ein Typ 450+ Events hat und ein anderer nur 5 → der seltene Typ soll trotzdem erscheinen

Rule 3: Score-Filter greift beim Laden, Cap greift beim Ausgeben
- ✅ Positiv: `min_score=0.35` filtert Events heraus bevor der Cap greift
- ❌ Negativ: Wenn Cap vor Score-Filter läge, würden hochwertige Events nach dem Cap wegfallen
- 🔶 Edge: `min_score=0.99` → nur Top-Events → Cap wahrscheinlich nicht binding

**Pre-Mortem:**

- 💀 Szenario 1 — Neuer BUG-32-Effekt in umgekehrter Richtung: Option A (Routine zuerst) verdrängt jetzt Mond/Milchstraße — Stephan beschwert sich, dass Mondaufgänge fehlen. **Frühwarnung:** Test nach Fix zeigt 0 Mondaufgänge im Feed. **Gegenmaßnahme:** Round-Robin oder proportionale Auswahl statt reiner Prioritätssortierung.

- 💀 Szenario 2 — Cache-Inhalt ändert sich saisonal: Im Winter gibt es kaum Milchstraße (528 → 0) → Sort-Key ist irrelevant, aber Cap bleibt Bottleneck bei anderen Typen. **Frühwarnung:** Regression-Test schlägt im Dezember fehl. **Gegenmaßnahme:** AK als dauerhafter API-Test in CI (curl + count per Typ).

- 💀 Szenario 3 — precompute erzeugt zukünftig noch mehr Events: Bei 5.000+ Events pro 14 Tage bleibt das Problem strukturell unlösbar mit reiner Sortierung. **Frühwarnung:** Cap wird regelmäßig erschöpft. **Gegenmaßnahme:** Cap pro Typ statt global (Option C ist robuster langfristig).

**Implementierungsoptionen:**

**Option A – Sort-Key umdrehen (Routine zuerst):**
- Sort-Key: `(0 if routine else 1, shoot_time, -score)` — Routine-Events kommen zuerst
- Vorteil: minimale Änderung, 1 Zeile
- Nachteil: dreht BUG-32 vollständig um — Mond/Milchstraße fallen nun heraus. Löst das Grundproblem nicht, verlagert es nur

**Option B – Zeitbasierte Sortierung (kein Typ-Bias):**
- Sort-Key: `(shoot_time, -score)` — nur nach Zeit sortieren, kein Typ-Gewicht
- Vorteil: fair, einfach, deterministisch
- Nachteil: Bei vielen zukünftigen Nicht-Routine-Events füllen diese wieder den Cap wenn Mond täglich auftritt — kurzfristig besser, strukturell nicht gelöst
- Simuliertes Ergebnis mit aktuellem Cache: ~130 pro Typ im :500-Fenster ✅

**Option C – Typ-proportionale Auswahl (Round-Robin per Typ):**
- Nach Filter + Dedup: Events nach Typ gruppieren, dann reihum je 1 Event pro Typ auswählen bis Cap erreicht
- Vorteil: garantiert Repräsentation aller Typen unabhängig von Volumen; robust bei saisonal variierenden Counts
- Nachteil: komplexer (~20 Zeilen statt 1), Reihenfolge im Feed ist nicht mehr rein zeitlich
- Events sind immer noch nach Score innerhalb jedes Typs priorisiert

**Empfehlung: Option C (Round-Robin)**

Begründung: Option B löst das Problem für den aktuellen Cache, bricht aber bei 500+ Non-Routine-Events pro Typ erneut zusammen. Option C ist die einzige Lösung, die strukturell hält. Die Komplexität ist überschaubar (~20 Zeilen). Der BUG-32-Kommentar im Code belegt, dass dieses Problem schon einmal auftrat — Option B würde es erneut entstehen lassen.

**Architektur:**
- Einzige Änderung: `_filter_feed` in `backend/main.py` (Zeile 1269–1280)
- Der `:500`-Cap in `get_opportunities` (Zeile 1342) bleibt unverändert
- Keine Änderungen an Frontend, Cache, Precompute

**Daten-Validierung:**
- [x] Cache-Probe durchgeführt: 4.178 Events total, davon 1.848 Routine (Score 0.75–1.0, alle ≥ 0.35), 2.330 Non-Routine
- [x] Simulation bestätigt: aktueller Sort-Key liefert 500/500 Nicht-Routine-Events, 0/500 Routine-Events
- [x] Simulation Option B: zeitbasierter Sort → ~130 Goldene Stunde + ~130 Blaue Stunde im :500-Fenster ✅
- [x] Prüffrage beantwortet: Routine-Events haben valide Scores — kein separates Datenproblem

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: nur `_filter_feed` in `backend/main.py` (Zeilen 1272–1279) betroffen
- [x] Implementierungsoptionen: A (Sort umdrehen) / B (zeitbasiert) / C (Round-Robin)
- [ ] Empfehlung: Option C (Round-Robin per Typ) — robust gegen saisonale Volumen-Schwankungen

**Testplan:**
- [ ] Automatisiert: `curl "/opportunities"` → response enthält mindestens 100 Goldene-Stunde-Events und 100 Blaue-Stunde-Events
- [ ] Automatisiert: `curl "/opportunities"` → response enthält mindestens 50 Mondaufgang-Events (Non-Routine nicht verdrängt)
- [ ] Manuell: Feed-Tab in der App öffnen → Goldene Stunde und Blaue Stunde sind sichtbar
- [ ] Manuell: Feed nach Typ „Goldene Stunde Abend" filtern → Events erscheinen korrekt
- [ ] Regression: `/opportunities/today` und `/opportunities?event_type=Mondaufgang` weiterhin korrekt

---

### BUG-49 · Doppeltes Suchfeld im Locations-Panel `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-29 |
| **Abgeschlossen** | 2026-06-29 |

**Beschreibung:** Im Locations-Panel existieren zwei Sucheingaben gleichzeitig: ein statisch sichtbares „Suchen"-Feld und ein weiteres, das sich über das Suchlogo im Menü öffnet. Das ist redundant und verwirrend — es sollte nur einen einzigen konsistenten Sucheinstieg geben.

**Bezug:** Keine Dubletten gefunden.

---

#### Analyse (BUG-49)

##### 📎 Code-Verifikation (durchgeführt 2026-06-29)

- `web/index.html` Z. 935–942 gelesen: Im `#page-locations`-Block existiert ein eigenständiges `<div class="search-wrap">` mit `<input class="search-input" oninput="Locations.filter(this.value)">` — das statisch sichtbare Suchfeld.
- `web/index.html` Z. 891–898 gelesen: Im globalen Header existiert `<div id="search-bar">` mit `<input id="search-input" oninput="Search.onInput(this.value)">` — das per Lupensymbol (Z. 845) geöffnete Overlay-Suchfeld.
- `Search._triggerRender()` (Z. 5235–5238): Wenn `App.current === 'locations'`, ruft das Header-Overlay ebenfalls `Locations.filter(this._query)` auf — beide Felder landen also in derselben Filterfunktion.
- Das lokale `.search-input` übergibt `this.value` direkt (kein Eintrag in `Search._query`), das Header-Overlay schreibt in `Search._query` und triggert darüber. Die zwei Felder sind **nicht synchronisiert** — beide können gleichzeitig Werte haben, die sich nicht kennen.
- Bestätigt: **kein Backend-Bezug** — rein Frontend, nur `web/index.html`.

##### Example Mapping

**📏 Rule 1:** Im Locations-Tab gibt es genau einen sichtbaren Sucheinstieg.

🟢 Beispiel (Positiv): Stephan wechselt zum Locations-Tab. Oben im Panel sieht er ein Suchfeld — das ist die einzige Möglichkeit, nach Locations zu filtern. Er tippt „Teufel" und die Liste filtert sofort.

🔴 Beispiel (Negativ — aktueller Bug): Stephan wechselt zum Locations-Tab. Oben sieht er ein Suchfeld im Panel. Zusätzlich kann er das Lupensymbol im Header antippen und bekommt ein zweites Overlay-Suchfeld. Beide filtern die Locations-Liste — aber unabhängig voneinander.

**📏 Rule 2:** Das Header-Lupensymbol ist nur auf Feed, Kalender und Scout sinnvoll — nicht auf dem Locations-Tab.

🟢 Beispiel: Stephan ist im Feed. Er tippt auf die Lupe im Header, ein Overlay öffnet sich. Er sucht nach „Biesdorf" — der Feed filtert.

⚠️ Edge Case: Stephan hat im lokalen Locations-Suchfeld „Teufel" eingetippt und wechselt dann zum Feed. Die Header-Suche zeigt keinen Wert (Search._query war leer). Erwartung: Feed wird ohne Suchfilter gezeigt — der Locations-Filter ist losgelöst.

**❓ Frage:** Soll beim Wechsel vom Locations-Tab zum Feed der lokale Locations-Filter geleert werden — oder darf er beim Zurückwechseln noch aktiv sein?

⚠️ Annahme: Das lokale Locations-Suchfeld bleibt beim Verlassen des Tabs aktiv (kein Auto-Reset) — bitte bestätigen.

##### Akzeptanzkriterien

- [ ] AK-1: Im Locations-Tab ist das Suchfeld am oberen Rand des Panels dauerhaft sichtbar und sofort benutzbar — kein Antippen einer Schaltfläche nötig.
- [ ] AK-2: Das Lupensymbol im Header öffnet auf dem Locations-Tab **kein** Overlay mehr — der Tap auf die Lupe wird ignoriert oder das Symbol wird auf diesem Tab ausgeblendet.
- [ ] AK-3: Auf Feed, Kalender und Scout funktioniert das Header-Lupe-Overlay wie bisher — kein Rückschritt.
- [ ] AK-4: Stephan tippt im Locations-Suchfeld „Teufel" — die Liste filtert sofort auf passende Locations. Löscht er den Text, erscheint die volle Liste wieder.
- [ ] Edge Case AK-5: Stephan wechselt vom Locations-Tab (mit aktivem Filter) zum Feed und zurück — der Locations-Filter zeigt noch denselben Wert wie vorher (kein ungewolltes Reset).

##### Pre-Mortem

💀 **Szenario 1: Header-Suche funktioniert auf dem Locations-Tab nach Fix nicht mehr**
- Auslöser: `Search.open()` wird für den Locations-Tab deaktiviert, aber `Search._query` wird nicht geleert — Feed/Kalender/Scout übernehmen noch einen alten Query-Wert.
- Frühwarnung: Nach Deaktivierung auf Locations-Tab im Feed suchen → Overlay-Query noch gefüllt.
- Gegenmaßnahme: `Search.close()` beim Tab-Wechsel aufrufen (oder `_query` zurücksetzen) → AK-3 testen.

💀 **Szenario 2: Lokales Suchfeld und Header-Overlay konkurrieren gleichzeitig**
- Auslöser: Beide Felder bleiben aktiv. Stephan tippt lokal „Dom", dann öffnet er das Overlay mit „Teufel" → unklar welcher Filter gilt.
- Frühwarnung: Beide Inputs gleichzeitig ausfüllen, Ergebnis prüfen.
- Gegenmaßnahme: Header-Lupe auf Locations-Tab vollständig deaktivieren (Option A).

💀 **Szenario 3: Locations-Filter-State geht verloren beim Tab-Wechsel (Option B)**
- Auslöser: Option B entfernt das lokale Feld und leitet Locations-Tab auf Header-Overlay um; beim Tab-Wechsel wird `Search.close()` aufgerufen → Filter weg.
- Frühwarnung: Filter eingeben → Tab wechseln → zurück → Feld leer, Liste ungefiltert.
- Gegenmaßnahme: `Search.close()` nur aufrufen wenn Ziel-Tab kein Locations-Tab ist, oder lokalen Filter-State separat halten.

##### Implementierungsoptionen

**Option A — Lokales Suchfeld behalten, Lupe auf Locations-Tab deaktivieren** *(empfohlen)*

- **App-Erlebnis:** Im Locations-Tab bleibt das Suchfeld am oberen Rand des Panels, genau wie heute. Das Lupensymbol im Header tut auf dem Locations-Tab nichts (oder wird ausgeblendet) — kein Overlay erscheint mehr. Der Nutzer hat einen klaren, immer sichtbaren Sucheinstieg.
- Betroffene Dateien: `web/index.html` — `Search.open()` erhält eine Guard-Bedingung: `if (App.current === 'locations') return;`
- Vorteile: Minimale Änderung, kein Risiko für Feed/Kalender/Scout, lokaler Filter-State bleibt erhalten.
- Nachteile: Das Lupensymbol reagiert auf dem Locations-Tab nicht — könnte verwirrend wirken (Schaltfläche ohne Funktion).
- Aufwand: **klein** (1 Zeile JS-Guard, optional: Symbol auf Locations-Tab ausblenden via CSS)

**Option B — Lokales Suchfeld entfernen, Header-Overlay auch für Locations nutzen**

- **App-Erlebnis:** Im Locations-Tab verschwindet das permanente Suchfeld oben. Suchen geht nur noch über das Lupensymbol im Header — genau wie im Feed. Das Feld ist nur aktiv wenn die Lupe angetippt wird; danach schließt es sich wieder.
- Betroffene Dateien: `web/index.html` — `.search-wrap`-Block aus `#page-locations` entfernen, `Search._triggerRender()` bereits korrekt verdrahtet.
- Vorteile: Einheitlicheres Interaktionsmuster über alle Tabs.
- Nachteile: Suchfeld ist nicht dauerhaft sichtbar — mehr Taps nötig; Filter-State geht beim Tab-Wechsel verloren (da `Search.close()` implizit aufgerufen wird); höheres Risiko für Regressions-Seiteneffekte.
- Aufwand: **mittel** (HTML-Entfernung + State-Management prüfen)

✅ **Empfehlung: Option A** — eine Guard-Zeile löst den Bug mit minimalem Risiko; das lokale Suchfeld ist UX-sinnvoll (dauerhaft sichtbar, kein Extra-Tap nötig) und der Locations-Tab hat damit einen klar definierten, stabilen Sucheinstieg.

##### Scope

**Eingeschlossen:** Deaktivierung der Header-Lupe auf dem Locations-Tab (JS-Guard). Optional: visuelles Ausblenden des Lupensymbols auf diesem Tab.

**Ausgeschlossen:** Änderungen an der Suchlogik (`Locations.filter()`), am Filter-Panel, an anderen Tabs.

##### Testplan

- [ ] **Manuell AK-1:** Locations-Tab öffnen → Suchfeld ist sofort sichtbar, kein Antippen nötig.
- [ ] **Manuell AK-2:** Locations-Tab → Lupensymbol antippen → kein Overlay erscheint.
- [ ] **Manuell AK-3 Regression:** Feed-Tab → Lupensymbol antippen → Overlay erscheint und filtert den Feed.
- [ ] **Manuell AK-4:** Locations-Tab → „Teufel" eintippen → Liste filtert → löschen → volle Liste.
- [ ] **Manuell AK-5:** Locations-Tab → „Dom" eintippen → Feed-Tab → zurück zu Locations → Feld noch aktiv.
- [ ] **Automatisiert:** kein pytest-Fall (rein Frontend-JS, kein Backend-Bezug).

##### Analyse & Planung

- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Code-Verifikation: `web/index.html` Z. 845, 891–898, 935–942, 5211–5240 gelesen
- [x] Architektur analysiert: nur `web/index.html` betroffen
- [x] Implementierungsoptionen: A (empfohlen) / B
- [ ] Weg-Gate: Warten auf Stephans Freigabe

---

### BUG-50 · HINWEISE-Feld überschreibt sich nach Quick Location Capture `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-29 |
| **Abgeschlossen** | 2026-06-29 |

**Beschreibung:** Bei Locations, die per Quick Location Capture angelegt wurden, speichert die App den Text „Automatisch erfasst via Quick Location Capture." im HINWEISE-Feld. Löscht der Nutzer diesen Text, schreibt sich der Wert beim nächsten Speichern/Öffnen erneut hinein — der Hinweis lässt sich nicht dauerhaft entfernen (reproduzierbar z. B. bei Ehrenhof-Kollonaden am Schloss Sanssouci).

**Bezug:** Keine Dubletten gefunden.

---

#### Analyse (BUG-50)

##### 📎 Code-Verifikation (durchgeführt 2026-06-29)

- `PATCH /locations/{loc_id}` in `backend/main.py` Zeile 1879–1952 gelesen.
- `all_allowed_fields` (Zeile 1887): `{observer_lat, observer_lon, subject_lat, subject_lon, name, description, observer_floor_height_m, focal_length_suggestions}` — **`special_notes` fehlt vollständig**.
- Frontend `saveEdit()` in `web/index.html` Zeile 4581: sendet `special_notes` im Body — aber der Endpoint filtert es mit `allowed = {k: v for k, v in body.items() if k in all_allowed_fields}` (Zeile 1888) still heraus.
- `_update_custom_location_file()` → `_store.update_custom()` in `store.py` Zeile 211–242: unterstützt `special_notes` vollständig (Spalte existiert in DB, dynamisches SQL).
- **Root-Cause:** `special_notes` ist nicht in der Whitelist des PATCH-Endpoints. Das Frontend sendet den Wert korrekt; der Server ignoriert ihn. Die DB behält den ursprünglichen Wert „Automatisch erfasst via Quick Location Capture." — beim Öffnen des Edit-Formulars erscheint er wieder.
- Bestätigt: **kein zweites Schreibloch** — die DB-Spalte existiert, `update_custom()` verarbeitet sie korrekt, nur die Whitelist fehlt.

##### Example Mapping

**📏 Rule 1:** Löscht der Nutzer den Text im HINWEISE-Feld und speichert, ist der ursprüngliche Text dauerhaft weg.

🟢 Beispiel: Location „Ehrenhof-Kollonaden" wurde per Quick Capture angelegt. Stephan öffnet Bearbeiten, löscht „Automatisch erfasst via Quick Location Capture.", tippt stattdessen „Beste Lichtzeit: 18–20 Uhr" und speichert. Beim erneuten Öffnen steht „Beste Lichtzeit: 18–20 Uhr" im Feld — der ursprüngliche Text ist weg.

🟢 Beispiel (Leerlassen): Stephan löscht den Text und lässt das Feld leer. Nach Speichern ist das Feld dauerhaft leer.

**📏 Rule 2:** Der `PATCH`-Endpoint akzeptiert und persistiert `special_notes` für Custom-Locations.

🟢 Beispiel: `PATCH /locations/custom_xyz {"special_notes": "Neue Info"}` → Antwort `{"ok": true, "updated": {"special_notes": "Neue Info"}}`. Beim GET der Location steht der neue Text.

**📏 Rule 3:** Für Standard-Locations (keine `custom_`-Prefix) wird `special_notes` ebenfalls via Override persistiert.

🟢 Beispiel: `PATCH /locations/loc_123 {"special_notes": "Hinweis"}` → `_save_location_override` wird aufgerufen; beim nächsten Server-Start bleibt der Wert.

##### Akzeptanzkriterien

- [x] AK-1: Stephan öffnet die Bearbeiten-Ansicht einer per Quick Capture angelegten Location, löscht den vorausgefüllten Hinweis-Text und speichert. Beim erneuten Öffnen der Location ist das Hinweisfeld leer — der ursprüngliche Text erscheint nicht erneut.
- [x] AK-2: Stephan ersetzt den Hinweis-Text durch eigenen Text und speichert. Der eigene Text bleibt nach Server-Neustart dauerhaft erhalten.
- [x] AK-3: `PATCH /locations/{custom_id} {"special_notes": "X"}` gibt `{"ok": true, "updated": {"special_notes": "X"}, ...}` zurück (HTTP 200) — `special_notes` erscheint in `updated`.
- [x] AK-4: `PATCH /locations/{standard_id} {"special_notes": "X"}` gibt HTTP 200 zurück und persistiert den Wert via Override.
- [x] AK-5 (Edge Case): Leerer String `""` als `special_notes` wird akzeptiert und korrekt persistiert (nicht abgelehnt oder durch Default ersetzt).
- [x] AK-6 (Regression): Alle bisher erlaubten Felder (name, description, Koordinaten, focal_length_suggestions, observer_floor_height_m) funktionieren nach der Änderung unverändert.

##### Pre-Mortem

💀 **Szenario 1: `special_notes` landet in `recompute_fields` — unerwünschter Recompute**
Auslöser: Jemand fügt `special_notes` versehentlich zu `recompute_fields` hinzu.
Frühwarnung: Jedes Hinweis-Edit löst einen teuren Single-Location Recompute aus.
Gegenmaßnahme: `special_notes` explizit nur zu `text_fields` + `all_allowed_fields` hinzufügen — `recompute_fields` unverändert lassen. Im AK-Test: kein Recompute-Flag in der Response bei reinem `special_notes`-PATCH.

💀 **Szenario 2: Standard-Location Overrides fehlen `special_notes`-Unterstützung**
Auslöser: `_save_location_override()` persistiert `special_notes` nicht.
Frühwarnung: Bei Standard-Locations bleibt der Wert im In-Memory (verschwindet nach Restart).
Gegenmaßnahme: `_save_location_override` prüfen ob `special_notes` in den Override-Write einbezogen wird. (Prüfpunkt in Impl.)

💀 **Szenario 3: `allowed`-Filter bricht die Fehlerbehandlung für leere Updates**
Auslöser: Body enthält nur `special_notes` → `allowed` ist danach nicht-leer → kein 400-Fehler. Korrekt.
Frühwarnung: Kein Risiko — das ist gewünschtes Verhalten. Kein Pre-Mortem-Fall.

💀 **Szenario 4: Validierung für `special_notes` fehlt — XSS oder überlange Strings**
Auslöser: Nutzer sendet sehr langen oder HTML-haltigen String ins Hinweisfeld.
Frühwarnung: Kein Längen-Check in anderen Textfeldern vorhanden — konsistent nicht validiert.
Gegenmaßnahme: Keine zusätzliche Validierung nötig (konsistent mit `name`, `description`). Scope bewusst ausgeschlossen.

##### Architektur-Analyse

**Betroffene Stellen:**

1. `backend/main.py` Zeile 1884 — `text_fields` (enthält `name`, `description`)
2. `backend/main.py` Zeile 1887 — `all_allowed_fields` (Union aller erlaubten Felder)
3. `_save_location_override()` — zu prüfen ob `special_notes` in Overrides unterstützt wird

**Nicht betroffen:**
- `store.py` `update_custom()` — unterstützt `special_notes` bereits korrekt
- Frontend `saveEdit()` — sendet `special_notes` bereits korrekt
- Recompute-Pfad — darf nicht berührt werden

##### Implementierungsoptionen

**Was bedeutet das für die App:**

Option A: Das Hinweisfeld verhält sich wie Name und Beschreibung — editierbar, dauerhaft gespeichert, kein Nebeneffekt.

Option B: Gleiches Ergebnis, aber über einen separaten Endpoint. In der App identisches Erlebnis, mehr technischer Aufwand.

---

### Option A — `special_notes` in `text_fields` aufnehmen (1-Zeilen-Fix)

- **Vorgehen:** `special_notes` in `text_fields` (Zeile 1884) eintragen → automatisch Teil von `all_allowed_fields`. Kein weiterer Code nötig. Zusätzlich prüfen ob `_save_location_override` den Wert für Standard-Locations persistiert.
- **Betroffene Dateien:** `backend/main.py` (1 Zeile); ggf. minimal `_save_location_override` (falls dort Whitelist)
- **Vorteile:** Minimalinvasiv, keine neuen Code-Pfade, konsistent mit bestehender Architektur
- **Nachteile / Risiken:** Keine — `update_custom` und DB unterstützen das Feld bereits
- **Aufwand:** klein

### Option B — Separater `PATCH /locations/{id}/notes` Endpoint

- **Vorgehen:** Neuer dedizierter Endpoint nur für `special_notes`
- **Betroffene Dateien:** `backend/main.py` (neuer Endpoint + Frontend-Anpassung)
- **Vorteile:** Expliziter API-Vertrag
- **Nachteile / Risiken:** Unnötiger Aufwand — kein struktureller Unterschied zu Option A aus App-Sicht
- **Aufwand:** mittel

✅ **Empfehlung: Option A** — 1-Zeilen-Fix in `text_fields`. Unterstützung in DB und `update_custom()` bereits vorhanden. Konsistent mit `name`/`description`.

##### Scope

**Eingeschlossen:** `special_notes` via PATCH editierbar + dauerhaft persistiert (Custom + Standard Locations).

**Ausgeschlossen:** Längen-/HTML-Validierung (nicht vorhanden für andere Textfelder — Konsistenz).

##### Testplan

- [ ] **Automatisiert (pytest):** `backend/tests/test_bug50.py` — PATCH custom location mit `special_notes`; PATCH mit `""` (Leeren); Verify: `special_notes` in `updated`; kein `recompute_triggered`.
- [ ] **Manuell:** Quick-Capture-Location in Edit öffnen → Hinweistext löschen → Speichern → Location erneut öffnen → Feld muss leer sein.
- [ ] **Regression:** PATCH name, description, Koordinaten weiterhin funktionstüchtig.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `backend/main.py` (PATCH-Endpoint, `all_allowed_fields`), `backend/data/store.py` (`update_custom`)
- [x] Implementierungsoptionen: A (1-Zeilen-Fix) / B (separater Endpoint)
- [x] Empfehlung: Option A

---

### BUG-51 · Filter nach Entfernung funktioniert nicht `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-29 |
| **Abgeschlossen** | 2026-06-29 |

**Beschreibung:** Der Entfernungsfilter (Radius-Slider oder Entfernungs-Chips) hat keine sichtbare Wirkung auf die angezeigte Locations- oder Feed-Liste — Locations außerhalb des gewählten Radius werden trotzdem angezeigt. Erwartetes Verhalten: nur Locations innerhalb des gesetzten Radius sind sichtbar.

**Bezug:** Keine Dubletten gefunden; vgl. allgemeines Filter-Thema BUG-46 (Verifikationsfilter), aber anderes Kriterium.

---

#### Analyse (BUG-51)

##### Example Mapping

📎 **Code-Verifikation (durchgeführt 2026-06-29):**
- `applyToLocations()` (web/index.html, Zeile 2546–2572) gelesen: **enthält keinen `maxDistKm`-Check** — das ist die Root-Cause für Locations-Tab und Textsuche.
- `MapView.applyFilter()` (Zeile 3892–3896): enthält Entfernungscheck via `haversineKm` + `Filter._gps` — Karte funktioniert bereits korrekt.
- `Filter.apply()` für Feed (Zeile 2519–2522): enthält Entfernungscheck — Feed funktioniert bereits korrekt.
- `Filter.applyToScout()` (Zeile 2610–2612): enthält Entfernungscheck — Scout funktioniert bereits korrekt.
- `Filter._applyLive()` (Zeile 2732): ruft `requestGps()` auf, dann je nach `App.current` unterschiedliche Render-Wege. Für `'locations'` → `Locations.render(Filter.applyToLocations(...))` — GPS wird also schon angefragt, aber `applyToLocations` ignoriert es danach.
- `haversineKm()` (Zeile 2392–2399): korrekte Haversine-Implementierung, wiederverwendbar.
- Location-Objekte haben `observer_lat`/`observer_lon` Felder (identisch zu den Feldern in der Map-Filterung).

**Befund:** Der Bug existiert ausschließlich in `applyToLocations()`. Die Funktion prüft Schwierigkeit, Kategorie, Bewertung, Verifikation und Score — aber nicht Entfernung. Der GPS-Request wird zwar in `_applyLive()` ausgelöst, aber das Ergebnis (`Filter._gps`) wird in `applyToLocations` nie ausgelesen. Alle anderen Filter-Pfade (Map, Feed, Scout) haben den Entfernungscheck korrekt implementiert.

---

**📏 Rule 1:** Wenn im Locations-Tab ein Entfernungsradius gesetzt ist und GPS-Standort bekannt ist, werden nur Locations angezeigt, deren Fotografen-Standpunkt (observer) innerhalb des Radius liegt.

🟢 Beispiel: Stephan wählt „< 15 km" als Entfernungsfilter. GPS zeigt Berlin-Mitte. Im Locations-Tab erscheinen nur Standorte innerhalb von 15 km — ein Spot in Potsdam (25 km entfernt) verschwindet aus der Liste.

🟢 Beispiel: Stephan tippt gleichzeitig „Schloss" in die Suche. Nur Schloss-Locations innerhalb 15 km sind sichtbar (Entfernungs- und Textfilter kombiniert).

**📏 Rule 2:** Wenn GPS nicht verfügbar oder nicht erteilt ist, wird der Entfernungsfilter übersprungen und alle Locations bleiben sichtbar.

🟢 Beispiel: GPS-Berechtigung verweigert, Entfernungsfilter auf „< 5 km" gesetzt → alle Locations sichtbar, Toast „GPS nicht verfügbar" erscheint.

**📏 Rule 3:** Die Entfernungsmessung erfolgt vom GPS-Standort des Nutzers zum `observer_lat`/`observer_lon` der Location (Fotografen-Standpunkt) — identisch zur Map-Filterung.

🟢 Beispiel: Identischer Spot wird in Map und Locations-Tab mit gleichem Entfernungsfilter übereinstimmend ein-/ausgeblendet.

❓ **Keine offenen Fragen** — die Root-Cause ist eindeutig, das Fix-Pattern ist aus der Map-Filterung direkt ableitbar.

---

##### Akzeptanzkriterien

- [ ] Wenn Stephan im Filtermenü „< 15 km" wählt und GPS-Standort vorhanden ist: Im Locations-Tab sind danach nur Locations sichtbar, deren Fotografen-Standpunkt innerhalb von 15 km liegt.
- [ ] Wenn Stephan „< 5 km" wählt: Locations weiter entfernt verschwinden sofort aus der Liste, sobald er „Anwenden" tippt.
- [ ] Entfernungsfilter und Textsuche (Suchfeld im Locations-Tab) wirken kombiniert: nur Locations die BEIDE Bedingungen erfüllen, werden angezeigt.
- [ ] Map und Locations-Tab zeigen bei gleichem Entfernungsfilter identische Locations an (kein Unterschied mehr zwischen den Ansichten).
- [ ] Edge Case: GPS nicht verfügbar (Berechtigung verweigert) → Locations-Tab zeigt alle Locations, Toast „GPS nicht verfügbar" erscheint, kein leeres Ergebnis.
- [ ] Edge Case: Entfernungsfilter auf „Alle" (= 0) gesetzt → alle Locations sichtbar, kein GPS-Request.
- [ ] Scout-Tab und Feed sind vom Fix nicht betroffen (Regression: weiterhin korrekte Entfernungsfilterung).

---

##### Pre-Mortem

💀 **Szenario 1: GPS-Request fehlt im Locations-Render-Pfad**
Auslöser: `applyToLocations` prüft `Filter._gps`, aber bei direktem Tab-Wechsel (ohne `_applyLive`) wurde noch kein GPS-Request gestellt → `Filter._gps === null` → Filter wirkt nicht.
Frühwarnung: Nur nach frischem App-Start wirkt der Filter nicht; nach einem vorherigen Map-Besuch (wo GPS angefragt wurde) funktioniert er.
Gegenmaßnahme: In `Locations.load()` und `Locations.filter()` einen `await Filter.requestGps()` voranstellen wenn `s.maxDistKm > 0` — analog zu `_applyLive`.

💀 **Szenario 2: Locations-Tab-Render nach Tab-Wechsel ignoriert GPS-State**
Auslöser: Stephan setzt Filter, wechselt Tab, wechselt zum Locations-Tab → `App.current` triggert `Locations.load()` ohne GPS-Abfrage.
Frühwarnung: Filter-Badge zeigt Entfernungsfilter aktiv, aber Liste bleibt ungefiltert.
Gegenmaßnahme: GPS-Check auch in `Locations.load()` integrieren.

💀 **Szenario 3: Regression auf Map oder Feed**
Auslöser: Falsche Stelle in der gemeinsamen Filter-Logik geändert, was bestehende Map- oder Feed-Filterung kaputt macht.
Frühwarnung: Map zeigt nach Fix andere Locations als vorher.
Gegenmaßnahme: Fix isoliert in `applyToLocations` — berührt Map-Code (Zeile 3892) und Feed-Code (Zeile 2519) nicht.

---

##### Implementierungsoptionen

**Option A — Entfernungscheck in `applyToLocations` ergänzen (minimaler Eingriff)**
- Was bedeutet das für Stephan: Die Liste im Locations-Tab verhält sich ab sofort genauso wie die Karte — gleicher Filter, gleiches Ergebnis. Einzige Änderung: 3 Zeilen Code im Locations-Filterblock.
- Betroffene Dateien: `web/index.html` — nur `applyToLocations()` (ca. Zeile 2570, vor `return true`)
- Zusätzlich: In `Locations.load()` und `Locations.filter()` GPS-Request voranstellen wenn `maxDistKm > 0`
- Vorteile: Kleinstmöglicher Fix; identische Logik wie Map (bewährt); kein Risiko für andere Filterfelder
- Nachteile: Kein async in `applyToLocations` möglich → GPS-Request muss VOR dem Filteraufruf erfolgen
- Aufwand: klein (~5 Zeilen Änderung + 2 await-Stellen)

**Option B — GPS-State gemeinsam vor jedem Locations-Render sicherstellen**
- Was bedeutet das für Stephan: Gleiche App-Wirkung wie Option A, aber robusterer GPS-Lifecycle (GPS wird garantiert immer vor dem Locations-Render geprüft, unabhängig vom Einstiegspfad).
- Betroffene Dateien: `web/index.html` — `Locations.load()`, `Locations.filter()`, `applyToLocations()`
- Vorteile: Sauberer GPS-Lifecycle; deckt alle Einstiegspfade ab (Tab-Wechsel, Textsuche, App-Start)
- Nachteile: Etwas mehr Refactoring; minimal mehr Komplexität im Locations-Modul
- Aufwand: klein-mittel (~8–10 Zeilen)

✅ **Empfehlung: Option B** — weil Option A das GPS-Problem nur in `_applyLive` löst, nicht bei direktem Tab-Wechsel oder Textsuche nach Filter-Setzen. Option B schließt alle Einstiegspfade mit überschaubarem Mehraufwand. Konkreter Plan:
1. `applyToLocations()`: Entfernungscheck nach Verifikations-Block ergänzen (3 Zeilen, analog Map-Code Zeile 3893-3895, mit `Filter._gps`)
2. `Locations.load()`: `if (Filter.state.maxDistKm > 0) await Filter.requestGps();` vor dem Render
3. `Locations.filter(q)`: dieselbe GPS-Abfrage vor dem `Filter.applyToLocations(this.all)`-Aufruf

---

##### Scope

**Eingeschlossen:**
- Entfernungsfilter im Locations-Tab (Liste + Textsuche)
- GPS-Request-Sicherung für alle Locations-Render-Pfade

**Ausgeschlossen (bereits korrekt):**
- Map-Filterung (Zeile 3892–3896): funktioniert
- Feed-Filterung (Zeile 2519–2522): funktioniert
- Scout-Filterung (Zeile 2610–2612): funktioniert

---

##### Testplan

**Automatisiert (pytest):** Kein Backend-Test nötig — reine Frontend-Logik. Die Filterlogik ist nicht in Python abgebildet.

**Manuell (Browser unter http://localhost:8000):**
1. App öffnen → Filter-Sheet → „< 5 km" wählen → Anwenden → Locations-Tab öffnen: Nur Locations innerhalb 5 km sichtbar (GPS-Abfrage erscheint falls nicht erteilt)
2. Im Locations-Tab Suchfeld „Schloss" eingeben: Kombinationsfilter — nur Schloss-Locations innerhalb 5 km
3. Auf Karte wechseln: Karte zeigt dieselben Locations wie Liste
4. GPS verweigern: Toast erscheint, alle Locations sichtbar
5. Filter zurücksetzen: Alle Locations wieder sichtbar, kein GPS-Request

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Code-Verifikation: `applyToLocations()` gelesen (Zeile 2546–2572) — `maxDistKm`-Check fehlt bestätigt
- [x] Architektur analysiert: nur `web/index.html` betroffen, `applyToLocations()` + GPS-Request in `Locations.load/filter`
- [x] Implementierungsoptionen: A (minimaler Fix) / B (robuster GPS-Lifecycle)
- [x] Empfehlung: Option B

---

### BUG-52 · Standort-Freigabe (Geolocation) wird nicht für die Session gespeichert `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-29 |
| **Abgeschlossen** | 2026-06-29 |

**Beschreibung:** Die App fordert die Geolocation-Berechtigung wiederholt innerhalb einer Session an — auch wenn der Nutzer sie bereits erteilt hat. Erwartetes Verhalten: Nach einmaliger Zustimmung bleibt die Freigabe für die laufende Session aktiv und wird nicht erneut abgefragt.

**Bezug:** Keine Dubletten gefunden.

---

### Analyse-Spec (BUG-52)

**Datum:** 2026-06-29

---

#### Example Mapping

📏 **Rule 1 — Einmalige GPS-Abfrage pro Session**
Die App darf den Browser-GPS-Dialog innerhalb einer Sitzung (Seite geöffnet, nicht neu geladen) höchstens einmal auslösen — egal wie oft der Entfernungsfilter angewendet oder der Tab gewechselt wird.

🟢 Example:
- Gegeben: Stephan öffnet die App und setzt den Entfernungsfilter auf 10 km
- Wenn: Der Browser-Dialog erscheint und Stephan klickt „Erlauben"
- Dann: Bei jedem weiteren Tab-Wechsel (Feed, Karte, Standorte), Filteränderung oder Reload der aktuellen Ansicht erscheint kein zweiter GPS-Dialog

🟢 Edge Case — gleichzeitige Aufrufe:
- Gegeben: Stephan öffnet den Locations-Tab mit aktivem Entfernungsfilter, während gleichzeitig auch Feed.render() einen GPS-Check auslöst
- Wenn: Beide Code-Pfade gleichzeitig `requestGps()` aufrufen, bevor die erste Antwort zurückkommt
- Dann: Es gibt trotzdem nur einen Browser-Dialog; beide Aufrufe warten auf dasselbe Ergebnis

📏 **Rule 2 — Fehler-Zustand wird nicht wiederholt abgefragt**
Wenn Stephan die GPS-Berechtigung verweigert, erscheint kein weiterer Dialog in dieser Session. Der Entfernungsfilter bleibt inaktiv, die App läuft normal weiter.

🟢 Example:
- Gegeben: GPS-Dialog erscheint, Stephan klickt „Ablehnen"
- Wenn: Stephan zum Feed wechselt und wieder zurück
- Dann: Kein erneuter Dialog — der Entfernungsfilter ist schlicht wirkungslos

📏 **Rule 3 — Page-Reload darf neu fragen**
Ein Neuladen der Seite (Browser-Refresh) ist ein Session-Neustart; die erneute Abfrage ist korrekt (der Browser merkt sich die Berechtigung und fragt ggf. nicht nochmal — das ist Browser-Sache, nicht App-Sache).

⚠️ **Annahme:** Der Bug tritt auf wenn mehrere Code-Stellen gleichzeitig `requestGps()` aufrufen (kein Promise-Deduplication). Bestätigt durch Code-Verifikation (siehe unten).

---

#### Akzeptanzkriterien

- [x] AK-1: Stephan setzt den Entfernungsfilter auf einen Wert > 0 km. Der GPS-Dialog erscheint genau einmal. Beim Wechsel zwischen Feed, Karte und Standorte-Tab erscheint kein zweiter Dialog.
- [x] AK-2: Stephan wechselt mit aktivem Entfernungsfilter schnell zwischen mehreren Tabs (z.B. Locations → Feed → Scout). Dabei erscheint der GPS-Dialog insgesamt nur einmal — nicht mehrfach in schneller Folge.
- [x] AK-3: Stephan lehnt den GPS-Dialog ab. Die App zeigt kein zweites Mal einen Dialog — der Entfernungsfilter ist stumm deaktiviert. (Toast „GPS nicht verfügbar" erscheint einmal.)
- [x] AK-4: Alle anderen Filter (Eventtyp, Schwierigkeit, Bewertung etc.) funktionieren nach der Änderung genauso wie vorher.
- [x] Edge Case AK-5: Stephan lädt die Seite neu (Browser-Refresh). Die App darf nach dem Reload wieder GPS anfragen — das ist kein Bug.

---

#### Pre-Mortem

📎 **Code-Verifikation:** `web/index.html`, Zeilen 2623–2633 gelesen am 2026-06-29.
- Bestätigt: `requestGps()` hat einen Guard `if (this._gps) return true` — funktioniert, sobald `_gps` gesetzt ist.
- Bestätigt: **Kein** `_gpsPromise`-Feld vorhanden — laufende Anfragen werden nicht dedupliziert.
- Bestätigt: `requestGps()` wird an mindestens 3 Stellen aufgerufen: `_applyLive()` (Z. 2737), `Locations.load()` (Z. 4222), `Locations.filter()` (Z. 4234) — alle ohne Koordination untereinander.
- Festgestellt: Wenn zwei dieser Aufrufe gleichzeitig starten (beide sehen `_gps === null`), erzeugen beide ein neues `Promise` und beide rufen `navigator.geolocation.getCurrentPosition()` auf → zwei Browser-Dialoge.

💀 **Szenario 1 — Doppelter Dialog beim Locations-Tab-Wechsel**
Auslöser: `Locations.load()` + gleichzeitiger `_applyLive()`-Trigger rufen beide `requestGps()` auf, bevor die erste Antwort da ist.
Frühwarnung: GPS-Dialog erscheint zweimal kurz hintereinander.
Gegenmaßnahme: Promise-Deduplication in `requestGps()` → in AK-2 abgedeckt.

💀 **Szenario 2 — Fix bricht Fehlerbehandlung**
Auslöser: Der `_gpsPromise`-Cache wird nach Fehler nicht zurückgesetzt — bei Permission-Denial bleibt `_gpsPromise` gecacht und alle späteren `requestGps()`-Aufrufe erhalten `false`.
Frühwarnung: Entfernungsfilter bleibt dauerhaft wirkungslos auch nach Deny.
Gegenmaßnahme: Nach Fehler `_gpsPromise` auf `null` zurücksetzen — nächster Aufruf kann neu fragen. AK-3 prüft dieses Verhalten.

💀 **Szenario 3 — Regression: Andere Filter funktionieren nicht mehr**
Auslöser: Umbau von `requestGps()` bricht das `async/await`-Verhalten in `_applyLive()`.
Frühwarnung: Entfernungsfilter hat keinen Effekt mehr, oder App friert kurz ein.
Gegenmaßnahme: AK-4 prüft andere Filter explizit nach der Änderung.

---

#### Architektur-Analyse

**Betroffene Datei:** `web/index.html` — nur `Filter.requestGps()` (~10 Zeilen) + Feld-Deklaration

**Root Cause:** `requestGps()` (Z. 2623–2633) speichert das laufende Promise nicht zwischen. Werden zwei gleichzeitige Aufrufe ausgelöst — was passiert wenn `Locations.load()` + `_applyLive()` quasi gleichzeitig feuern — erzeugen beide ein eigenes `getCurrentPosition`-Promise, und der Browser zeigt zwei Dialoge.

**Guard existiert bereits, aber greift zu spät:** `if (this._gps) return true` wirkt korrekt, aber nur nachdem die erste Anfrage abgeschlossen ist und `_gps` gesetzt hat. Während die erste Anfrage läuft (bis zu 8 Sekunden Timeout), ist `_gps` noch null — jeder weitere Aufruf startet einen eigenen Dialog.

**Aufruforte (alle in `web/index.html`):**
- Z. 2737: `Filter._applyLive()` — bei jeder Filteränderung
- Z. 4222: `Locations.load()` — beim Öffnen des Locations-Tabs
- Z. 4234: `Locations.filter()` — bei Textsuche im Locations-Tab

**Kein Backend-Eingriff nötig.** Rein frontend-seitiger Fix in ~8 Zeilen.

---

#### Implementierungsoptionen

**In App-Sprache:** Es geht darum, dass die App beim ersten GPS-Dialog wartet bis der Nutzer geantwortet hat — und alle anderen Teile der App, die gleichzeitig auch GPS brauchen, einfach mitlaufen lassen, statt eine zweite Frage zu stellen.

##### Option A — Promise-Caching (empfohlen)

Beim ersten `requestGps()`-Aufruf das laufende Promise in `Filter._gpsPromise` speichern. Alle weiteren Aufrufe während die Anfrage läuft erhalten dasselbe Promise zurück — kein zweiter Browser-Dialog. Nach Abschluss wird `_gpsPromise` geleert.

- Betroffene Datei: `web/index.html` — nur `requestGps()` + Feld-Deklaration `_gps: null`
- Vorteile: Minimaler Eingriff (~8 Zeilen), kein Verhaltens-Change außer dem Fix, keine Regression möglich
- Nachteile: Keine
- Aufwand: **klein**

##### Option B — Einmaliger watchPosition-Aufruf beim App-Start

`navigator.geolocation.watchPosition()` beim Boot aufrufen und Position kontinuierlich tracken. `requestGps()` gibt einfach den letzten bekannten Wert zurück.

- Betroffene Datei: `web/index.html` — App-Boot-Sequenz + `requestGps()`
- Vorteile: Position immer aktuell; elegantere Langfrist-Lösung
- Nachteile: GPS-Dialog erscheint beim App-Start — auch wenn der Nutzer nie den Entfernungsfilter nutzt. Scope-Creep, verändert UX grundsätzlich.
- Aufwand: **mittel**, mehr Änderungen, Risiko für Regression

✅ **Empfehlung: Option A** — Minimaler Eingriff, löst genau das Problem ohne Seiteneffekte. Option B würde den GPS-Dialog für alle Nutzer vorziehen, auch wenn sie den Entfernungsfilter nie nutzen — das geht über den Ticket-Scope hinaus.

---

#### Scope

**Eingeschlossen:** Deduplizierung gleichzeitiger `requestGps()`-Aufrufe innerhalb einer Session.

**Ausgeschlossen:** Persistenz über Page-Reloads hinweg (wäre sessionStorage — nicht angefragt). Kontinuierliches Position-Tracking (Option B). Änderungen an MapView-Geolocation-Aufrufen (`locateMe`, `useMyLocation`, Karten-Init) — diese sind unabhängig und betreffen keine Permission-Dialoge.

---

#### Testplan

- [ ] **Automatisiert:** Kein sinnvoller pytest-Fall (rein frontend, Browser-API). Manueller Test ist der Hauptweg.
- [ ] **Manuell AK-1+2:** Lokalen Server starten (`http://localhost:8000`). Entfernungsfilter auf 5 km setzen. GPS erlauben. Zwischen Feed, Karte und Standorte wechseln — beobachten: erscheint der Dialog erneut? Erwartet: genau 1x gesamt.
- [ ] **Manuell AK-3:** Seite neu laden. Entfernungsfilter setzen. GPS ablehnen. Tab wechseln. Erwartet: kein zweiter Dialog, Toast einmalig, Entfernungsfilter wirkungslos (alle Standorte sichtbar).
- [ ] **Regression AK-4:** Eventtyp-Filter, Bewertungsfilter, Schwierigkeitsfilter testen — sollen weiterhin korrekt filtern.

---

#### Analyse-Status

- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Code-Verifikation: `web/index.html` Z. 2623–2633 gelesen; Root Cause bestätigt
- [x] Architektur analysiert: nur `Filter.requestGps()` + Feld-Deklaration betroffen
- [x] Implementierungsoptionen: A (Promise-Caching) / B (watchPosition)
- [x] Empfehlung: Option A

---

### US-108 · Azimut-Zonen für Sonnen- und Mondauf-/-untergang `[x]`

| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Done |
| **Abgeschlossen** | 2026-06-30 |

**Beschreibung:**
Sonnenauf-/-untergang und Mondauf-/-untergang werden aktuell für jede Location angezeigt, unabhängig davon, ob der Auf-/Untergang zur Sichtachse auf das Motiv passt. Das führt zu irrelevanten Chancen-Einträgen (z. B. Sonnenuntergang seitlich, obwohl er weder im Bild liegt noch das Motiv beleuchtet).

**Gewünschtes Verhalten:**
Die Darstellung soll auf Azimut-Zonen umgestellt werden:

- **Vorne** (zirkuläre Differenz Auf-/Untergang-Azimut zur Sichtachse ≤ 35°): Sonne/Mond im oder nahe am Bild → Frontlicht, Sunstar-Potential → Chance anzeigen
- **Hinten** (zirkuläre Differenz ≥ 145°, also grob 180° gegenüber der Sichtachse): Auf-/Untergang hinter dem Fotografen → beleuchtet das Motiv (Alpenglühen, pastell Wolken) → Chance anzeigen — **nur für Sonne**, nicht für Mond
- **Seitlich** (35°–145°): kein besonderer Bildwert → Chance unterdrücken

**Locations ohne Sichtachsen-Azimut** (kein `observer_lat/lon` + `subject_lat/lon` eingetragen): Der Auf-/Untergang wird nicht angezeigt. Kein Fallback auf das alte Verhalten.

**Labels** bleiben unverändert: Mondaufgang, Monduntergang, Sonnenaufgang, Sonnenuntergang.

**Betroffene Datei:** `FotoAlert/backend/calculations/opportunity.py`

**Bezug / Abgrenzung:**
- **US-107** *(Done, 2026-06-29)*: Hat Richtungsklassifizierung für das Location-Detail-UI eingeführt. US-108 nutzt dasselbe Konzept, aber im Backend zur Filterentscheidung für den Chancen-Feed.
- **TASK-45** *(Done)*: Azimut-Ableitung aus Gebäude-Footprints — liefert `ideal_azimuth_range` / `subject_azimuth` als Basis.
- **US-35** *(Done)*: `possible_bodies`-Berechnung — orthogonal (astronomisch unmöglich ≠ falsche Richtungszone).
- **US-79** *(offen)*: Mondaufgang/-untergang im Detail — US-108 ist dessen Voraussetzung für korrekte Mond-Filterung; US-108 sollte zuerst.
- **US-64** *(offen)*: Live Astro-Visualisierung — unabhängig (Live-UI ≠ Backend-Filterlogik).

**Sequenzierung:** Vor US-79 implementieren.

---

## Implementation Spec (US-108)

### Code-Analyse: Ist-Zustand

**Sichtachsen-Azimut** wird in `find_opportunities()` (opportunity.py, Z. 323–326) aus `observer_lat/lon` + `subject_lat/lon` berechnet:
```python
subject_az = calculate_azimuth_alignment(
    location.observer_lat, location.observer_lon,
    location.subject_lat, location.subject_lon,
)
```
Alle Locations haben `observer_lat/lon` + `subject_lat/lon` — kein separates Sichtachsen-Feld existiert. `subject_az` ist also der Sichtachsen-Azimut (Richtung vom Standpunkt zum Motiv).

**Betroffener Code-Block:** Abschnitt 5b (Z. 672–717): `MOON_RISE` / `MOON_SET`. Dort wird `moon_az_mr` (Mondazimut beim Auf-/Untergang) berechnet, aber kein Vergleich mit `subject_az` gemacht — jeder Mondauf-/-untergang wird (wenn Score ≥ min_score) als Chance ausgegeben.

Analoges Verhalten fehlt für Sonnenauf-/-untergang — dieser Event-Typ wird aktuell gar nicht als eigenständiges Event erzeugt (nur über Goldene Stunde und SUN_ALIGNMENT abgedeckt). US-108 führt also **keinen neuen Sunrise/Sunset-Event-Typ ein** — die Filterung betrifft nur `MOON_RISE` und `MOON_SET`.

### Example Mapping

**Regel 1 — Vorne: Mond im Bild**
- Positiv: Location Brandenburger Tor, Sichtachse Ost (90°). Mondaufgang um 5:32 Uhr, Mondazimut 85°. Delta = 5° → Zone Vorne → Chance erscheint im Feed.
- Negativ: Mondazimut 140°, Delta = 50° → Zone Seitlich → Chance wird unterdrückt.
- Edge: Mondazimut 55°, Delta = 35° → Grenzwert → Vorne (≤ 35° ist inklusiv).

**Regel 2 — Hinten: Monduntergang beleuchtet das Motiv NICHT (nur Sonne darf)**
- Positiv (Sonne, künftig): Sonnenuntergang hinter dem Fotografen (Delta 170°) → beleuchtet Motiv mit Abendlicht → Chance zeigen.
- Negativ (Mond): Monduntergang hinter dem Fotografen (Delta 170°) → kein Alpenglühen-Effekt beim Mond → Chance wird unterdrückt.
- Edge: Delta genau 145° → Grenzwert Hinten (≥ 145° ist inklusiv).

**Regel 3 — Location ohne Koordinaten → kein Fallback**
- Negativ: Location hat `observer_lat = subject_lat` (Punkt-Location ohne echte Sichtachse) → `subject_az` ist rechnerisch instabil (Distanz = 0) → **Chance unterdrücken**.
- Hinweis: Alle aktuellen Locations haben getrennte observer/subject-Koordinaten. Sicherheitscheck: `observer_lat == subject_lat and observer_lon == subject_lon` → überspringen.

**Regel 4 — Seitlich: keine Chance**
- Erlebbar: Mond geht im Süden auf (180°), Sichtachse zeigt Ost (90°). Delta = 90° → Zone Seitlich → kein Eintrag im Feed. Der Mond ist weder im Bild noch beleuchtet er das Motiv sinnvoll.

### Pre-Mortem (Grenzfälle + Risiken)

1. **0°/360°-Wrap**: Delta-Berechnung muss zirkulär sein. `abs(az1 - az2)` reicht nicht — `(az1 - az2 + 180) % 360 - 180` liefert den kürzesten Winkelabstand (bereits im Code für andere Events so verwendet, Z. 336).
2. **Punkt-Location (observer = subject)**: `calculate_azimuth_alignment` mit identischen Koordinaten → undefined/0 → muss vor der Zonen-Prüfung abgefangen werden.
3. **moon_az_mr = None**: `get_body_position()` kann None zurückgeben (Z. 686). Wenn kein Mondazimut bekannt → Chance unterdrücken.
4. **Sunrises/Sunsets fehlen als Event-Typ**: Das Ticket beschreibt Filterung von Auf-/Untergängen — `SUNRISE` und `SUNSET` als eigene EventTypes existieren nicht. Scope: nur `MOON_RISE`/`MOON_SET` filtern.
5. **Performance**: Filterung ist O(1) pro Event — kein Performance-Risiko.
6. **Score-Schwelle**: Die Azimut-Filterung greift **vor** dem Score-Check (Early Return), damit keine unnötigen Score-Berechnungen stattfinden.

### Implementierungsoptionen

**Option A — Inline-Filter je Event (direkt im 5b-Block)**

```python
# Zirkulärer Winkelabstand zwischen Mondazimut und Sichtachse
if moon_az_mr is None:
    continue  # kein Azimut bekannt → überspringen
delta = abs((moon_az_mr - subject_az + 180) % 360 - 180)
# Vorne (≤ 35°): erlaubt für Mond + Sonne
# Hinten (≥ 145°): nur für Sonne (MOON_RISE/MOON_SET → skip)
# Seitlich (35–145°): immer überspringen
if delta > 35:
    continue  # Mond: weder Hinten noch Vorne → skip
```

Einfach, lokal, keine neue Funktion. Schwächer bei Wiederverwendung wenn Sunrise/Sunset als Event-Typ dazukommt.

**Option B — Zentrale Hilfsfunktion `_azimuth_zone()`**

```python
from enum import Enum

class AzimuthZone(str, Enum):
    FRONT = "front"
    BACK  = "back"
    SIDE  = "side"

def _azimuth_zone(celestial_az: float, sightline_az: float) -> AzimuthZone:
    delta = abs((celestial_az - sightline_az + 180) % 360 - 180)
    if delta <= 35:
        return AzimuthZone.FRONT
    if delta >= 145:
        return AzimuthZone.BACK
    return AzimuthZone.SIDE
```

Im 5b-Block dann:
```python
if moon_az_mr is None:
    continue
zone = _azimuth_zone(moon_az_mr, subject_az)
if zone == AzimuthZone.SIDE:
    continue
if zone == AzimuthZone.BACK:
    continue  # Mond: Hinten kein Mehrwert
# zone == FRONT → weiter
```

Sauber, testbar, erweiterbar für künftige Sunrise/Sunset-Events.

**Empfehlung: Option B**
Die Zonenfunktion ist in 10 Zeilen geschrieben, hat keinen Overhead, ist mit pytest isoliert testbar und macht die Logik explizit lesbar. Wenn Sonnenauf-/-untergang als eigener Event-Typ nachkommt (US-79 oder Folgeticket), ist die Erweiterung trivial — Sonne darf in BACK, Mond nicht.

### Akzeptanzkriterien

**AK 1 — Mondaufgang vorne erscheint**
Wenn der Mondaufgang-Azimut ≤ 35° von der Sichtachse abweicht, erscheint im Feed ein „Mondaufgang"-Eintrag für diese Location.

**AK 2 — Mondaufgang seitlich wird unterdrückt**
Wenn der Mondaufgang-Azimut 35°–145° von der Sichtachse abweicht, erscheint kein „Mondaufgang"-Eintrag im Feed.

**AK 3 — Monduntergang hinten wird unterdrückt**
Wenn der Monduntergang-Azimut ≥ 145° von der Sichtachse abweicht (hinter dem Fotografen), erscheint kein „Monduntergang"-Eintrag im Feed — auch nicht als Alpenglühen-Logik (das gilt nur für Sonne).

**AK 4 — Mondaufgang ohne bekannten Azimut wird unterdrückt**
Wenn `get_body_position()` None zurückgibt (Azimut unbekannt), erscheint kein Eintrag im Feed.

**AK 5 — Grenzwerte korrekt**
Delta = 35° → Zone Vorne → Eintrag erscheint. Delta = 145° → Zone Hinten → bei Mond: kein Eintrag.

**AK 6 — Keine Regression bei anderen Event-Typen**
Golden Hour, Blue Hour, SUN_ALIGNMENT, MOON_ALIGNMENT, Milchstraße, Meteoritenschauer werden durch US-108 nicht verändert.

### Betroffene Dateien

- `FotoAlert/backend/calculations/opportunity.py` — `_azimuth_zone()` hinzufügen, Abschnitt 5b anpassen

### Pytest-Testfälle (vor Implementierung schreiben)

```python
def test_azimuth_zone_front():
    assert _azimuth_zone(90, 85) == AzimuthZone.FRONT   # delta=5
    assert _azimuth_zone(90, 55) == AzimuthZone.FRONT   # delta=35 (Grenze)

def test_azimuth_zone_side():
    assert _azimuth_zone(90, 140) == AzimuthZone.SIDE   # delta=50
    assert _azimuth_zone(90, 0) == AzimuthZone.SIDE     # delta=90

def test_azimuth_zone_back():
    assert _azimuth_zone(270, 90) == AzimuthZone.BACK   # delta=180
    assert _azimuth_zone(235, 90) == AzimuthZone.BACK   # delta=145 (Grenze)

def test_wrap_around_360():
    assert _azimuth_zone(355, 5) == AzimuthZone.FRONT   # delta=10, 0/360-Wrap
    assert _azimuth_zone(5, 355) == AzimuthZone.FRONT
```


---

### US-111 · Detail-Sheet: Schematisches Himmels-Kompass-Diagramm für Goldene-Wolken/Himmelsröte-Events `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-30 |
| **Abgeschlossen** | 2026-07-01 |

**Beschreibung:**
Im Detail-Sheet eines „Goldene Wolken"- oder „Himmelsröte"-Events soll eine schematische visuelle Darstellung (SVG-Skizze) zeigen, wo die Sonne steht, wo die Sichtachse Fotograf → Motiv zeigt, und ob die Wolken sich in der richtigen Richtung für das jeweilige Event befinden. Die Darstellung ist locationspezifisch (basiert auf dem Azimut der Location) und sitzt lokal im Detail-Sheet — keine Karten-Heatmap.

Inspiration: Viewfindr zeigt auf ihrer Himmelsröte-Seite eine Karte mit konzentrischen Bögen (Ideal/High/Medium/Low probability) und einer Heatmap. FotoAlert übernimmt das Prinzip als kompaktes Kompass-Diagramm im Detail-Sheet: Nord oben, Sonnenposition als Pfeil/Symbol, Sichtachse als Linie, Wolken-Erwartungsbereich als farbige Zone.

**Warum:**
Ohne visuellen Hinweis muss der Fotograf selbst aus Azimutwinkeln ableiten, ob die Wolken „vor" oder „hinter" ihm stehen. Das Diagramm macht diese räumliche Beziehung sofort erfassbar und erhöht die Planungsqualität für go/no-go-Entscheidungen.

**Bezug:** Nachfolger von **US-109** (Goldene Wolken & Himmelsröte, released 2026-06-30) — in der US-109-Analyse war diese Darstellung als ⚠️ **Annahme D** markiert und explizit als offene Frage geführt. Sie hat es nicht in die AKs geschafft und wird jetzt als eigenständiges Ticket nachgeholt.

---

## Analyse (US-111) · 2026-06-30

### Example Mapping

**Scope-Check:** Das Ticket ist bewusst auf Goldene Wolken + Himmelsröte beschränkt. Andere Event-Typen (Goldene Stunde, Blaue Stunde) könnten theoretisch auch ein Kompass-Diagramm nutzen — aber ihr räumlicher Kontext ist bereits über die bestehende „Himmelsposition"-Sektion (ev_skypos, US-67) abgedeckt. Goldene Wolken/Himmelsröte sind explizit aus ev_skypos ausgenommen (EV_SKYPOS_EXEMPT), weil sie andere Logik brauchen. US-111 schließt diese Lücke gezielt.

**Annahmen-Protokoll:**

| Punkt | Typ | Entscheidung |
|-------|-----|--------------|
| Diagramm-Größe: kompakt (ca. 200px) oder groß (Kartengröße 220px wie FOV-Map)? | ⚪ ästhetisch | Annahme: ~200×200px, wie ein kompaktes Icon-Diagramm — Begründung: kein interaktives Element, kein Leaflet nötig |
| Wolken-Zone für Himmelsröte: Halbkreis oder Vollkreis? | ✅ aus Ticket ableitbar | Himmelsröte ist rundum-sichtbar → kein Richtungsfilter → Zone entfällt oder zeigt Vollkreis |
| Goldene Wolken: Wolken-Zone ±30°, ±45°, oder ±60° um die Sichtachse? | ⚪ ästhetisch | Annahme: ±30° (exakte Winkelgrenze aus US-109-Backend-Logik) |
| Diagramm als inline-SVG im HTML-String oder als Canvas? | ✅ klar | SVG (wie alle anderen UI-Elemente) |
| Soll das Diagramm in einer neuen Section sitzen oder in die bestehende ev_golden_clouds / ev_red_sky-Section eingebettet werden? | ⚪ ästhetisch | Annahme: eingebettet in bestehende Section, kein neues mkSec nötig |
| Fallback wenn subject_azimuth fehlt (Location ohne Motivkoordinaten): Diagramm verstecken oder nur Sonnenposition zeigen? | ✅ aus Ticket-Constraints | Diagramm zeigt nur Sonne + Nord-Markierung; Sichtachse wird weggelassen (graceful) |

**Rules + Examples:**

📏 **Rule 1: Diagramm erscheint im Detail-Sheet eines Goldene-Wolken-Events**
🟢 *Given* ein Goldene-Wolken-Event mit sunset_azimuth=250° und subject_azimuth=255°, *When* ich das Detail-Sheet öffne, *Then* sehe ich in der „Warum Goldene Wolken?"-Sektion ein Kompass-Diagramm mit: Nord oben, einer Linie bei ~250° (Sonne), einer Linie bei ~255° (Sichtachse), und einer goldenen Zone ±30° um 255°.

📏 **Rule 2: Diagramm erscheint im Detail-Sheet eines Himmelsröte-Events**
🟢 *Given* ein Himmelsröte-Event, *When* ich die „Warum Himmelsröte?"-Sektion öffne, *Then* sehe ich ein Kompass-Diagramm mit Nord oben, Sonnenposition als Pfeil, und einem roten Farbring ringsum (rundum-sichtbar — keine Richtungsbevorzugung).

📏 **Rule 3: Graceful Fallback wenn subject_azimuth fehlt**
🟢 *Given* ein Goldene-Wolken-Event für eine Location ohne Motivkoordinaten (subject_azimuth = null), *When* ich das Detail-Sheet öffne, *Then* zeigt das Diagramm nur den Sonnen-Pfeil und die Nord-Markierung — kein Fehler, kein leeres Element.

📏 **Rule 4: Diagramm orientiert sich am echten Azimut (locationspezifisch)**
🟢 *Given* Location A mit subject_azimuth=60° (Ost) und Location B mit subject_azimuth=240° (Südwest), *When* ich beide Detail-Sheets öffne, *Then* zeigen beide Diagramme unterschiedliche Sichtachsen-Winkel (Linie zeigt nach Ost vs. Südwest).

---

### Akzeptanzkriterien

- [ ] **AK-1:** Im Detail-Sheet eines Goldene-Wolken-Events sehe ich unterhalb des bestehenden Textes in der „Warum Goldene Wolken?"-Sektion ein Kompass-Diagramm — Nord zeigt nach oben, die Sonne ist als Pfeil/Symbol am richtigen Himmelsrand eingezeichnet, die Sichtachse (Fotograf → Motiv) als Linie, und eine goldene Zone markiert den ±30°-Bereich um die Sichtachse.
- [ ] **AK-2:** Im Detail-Sheet eines Himmelsröte-Events sehe ich in der „Warum Himmelsröte?"-Sektion ein Kompass-Diagramm mit Sonnenposition und einem roten Farbring ringsum (kein Richtungssektor), der die rundum-Wirkung der Röte visualisiert.
- [ ] **AK-3:** Das Diagramm dreht sich korrekt mit dem Azimut der Location — bei zwei verschiedenen Locations mit unterschiedlichen Sichtachsen zeigen die Sichtachsen-Linien in unterschiedliche Himmelsrichtungen.
- [ ] **AK-4 (Fallback):** Bei einem Goldene-Wolken-Event, dessen Location keine Motivkoordinaten hat (subject_azimuth = null), zeigt das Diagramm nur Sonnenposition und Nord — kein Fehler, keine leere Fläche, kein defektes SVG.
- [ ] **AK-5 (Safari-Kompatibilität):** Das Diagramm ist in Safari sichtbar und korrekt eingefärbt — kein unsichtbarer Strich, kein fehlendes Element (kein SVG `use`+`currentColor` ohne direkte Attribute).
- [ ] **AK-6 (Keine Regression):** Alle anderen Event-Typen (Goldene Stunde, Blaue Stunde, Milchstraße, Mond-Alignment etc.) zeigen kein zusätzliches Kompass-Diagramm — die neue Section erscheint nur bei Goldene Wolken und Himmelsröte.

---

### Pre-Mortem

📎 **Code-Verifikation:** `web/index.html` Zeilen 3540–3600 gelesen am 2026-06-30.
- Bestätigt: `sunAz` wird bereits in ev_golden_clouds berechnet (sunrise/sunset azimuth Vergleich, Fallback auf vorhandenen Wert). Diese Logik ist wiederverwendbar für das Diagramm.
- Bestätigt: `EV_SKYPOS_EXEMPT` enthält explizit 'Goldene Wolken' und 'Himmelsröte' → ev_skypos wird nicht ausgelöst → keine Dopplung.
- Bestätigt: SVG-Symbole liegen in `<symbol>`-Tags mit `g`-Attributen (kein `use`+`currentColor` nötig, da Diagramm inline als Template-Literal gebaut wird).
- Bestätigt: `subject_azimuth` ist am Event-Objekt `o` verfügbar (Zeile 3549), `sunrise_azimuth` + `sunset_azimuth` ebenfalls (Z. 3551–3555).

💀 **Szenario 1: Inline-SVG mit `currentColor` in Safari unsichtbar**
Auslöser: SVG-Elemente erhalten Farbe via CSS-Klasse statt direktem Attribut.
Frühwarnung: In Safari erscheint das Diagramm leer oder nur als Kreislinie.
Gegenmaßnahme: Alle Farben direkt als `stroke="..."` / `fill="..."` Attribute auf den SVG-Elementen setzen (Memory: `reference_svg_use_currentcolor_webkit`). → In AK-5 verankert.

💀 **Szenario 2: sunAz-Berechnung liefert falschen Wert (Fallback-Fallback)**
Auslöser: Weder sunrise_azimuth noch sunset_azimuth vorhanden (unwahrscheinlich aber möglich bei sehr alten Cache-Einträgen).
Frühwarnung: Sonnen-Pfeil zeigt auf 0° (Nord) statt korrekte Richtung.
Gegenmaßnahme: `sunAz != null`-Guard im Diagramm-Renderer — wenn null: nur Kompassring + Sichtachse, kein Sonnen-Pfeil.

💀 **Szenario 3: Diagramm erscheint auch bei anderen Event-Typen (Scope-Leak)**
Auslöser: Bedingung nicht eng genug gefasst (`isGoldenClouds || isRedSky` Guard fehlt oder falsch).
Frühwarnung: Goldene-Stunde-Events zeigen plötzlich ein zweites Diagramm.
Gegenmaßnahme: Diagramm-Code nur innerhalb des bestehenden `if (isGoldenClouds)` / `if (isRedSky)` Blocks. → In AK-6 verankert.

💀 **Szenario 4: SVG-Breite bricht Layout auf schmalen Screens**
Auslöser: `viewBox` zu groß, kein `width:100%` gesetzt.
Frühwarnung: Diagramm überlappt mit Sheet-Rand auf Mobilgerät.
Gegenmaßnahme: `width="100%" height="200"` + `viewBox="0 0 200 200"` → responsive ohne Overflow.

---

### Implementierungsoptionen

**Option A — Diagramm inline in die bestehenden ev_golden_clouds / ev_red_sky Sections einbetten**

*Was du in der App erlebst:* Direkt im aufgeklappten „Warum Goldene Wolken?"-Block erscheint unter dem Text + den Winkelzeilen ein kompaktes Kompass-Diagramm. Keine neue Sektion, kein weiteres Aufklappen nötig.

- Vorgehen: In den bestehenden `if (isGoldenClouds)` und `if (isRedSky)` Blöcken (Z. 3541ff.) nach dem Text-HTML einen SVG-String anhängen. Eine Hilfsfunktion `mkCloudCompassSvg(sunAz, subjectAz, isRedSky)` erzeugt den inline-SVG.
- Betroffene Dateien: `web/index.html` (nur dieser Block, ~30 Zeilen neu)
- Vorteile: Kein neues mkSec nötig, kein neuer Section-State, kein neuer Sections.registerOnOpen. Diagramm ist immer sichtbar wenn die Section offen ist.
- Nachteile: Diagramm kann nicht separat auf-/zugeklappt werden.
- Aufwand: klein

**Option B — Neue eigene Section `ev_compass` direkt nach ev_golden_clouds / ev_red_sky**

*Was du in der App erlebst:* Nach der „Warum Goldene Wolken?"-Sektion gibt es eine weitere aufklappbare Sektion „Kompass-Diagramm", die das SVG enthält.

- Vorgehen: `mkSec('ev_compass', '🧭 Kompass', svgHtml)` nach den bestehenden Sections; neuen Key in `_def` hinzufügen.
- Betroffene Dateien: `web/index.html` (Section-Registrierung, _def-Eintrag, neuer mkSec-Block)
- Vorteile: Kann separat zugeklappt werden.
- Nachteile: Mehr Code-Aufwand, ein weiteres Aufklappen für Nutzer, Section erscheint auch bei anderen Event-Typen wenn Guard nicht exakt; _def braucht neuen Eintrag.
- Aufwand: mittel

✅ **Empfehlung: Option A** — Das Diagramm ist eine visuelle Ergänzung zur Erklärung, keine eigenständige Funktion. Es gehört direkt in die Erklärungssektion, ohne extra Klick. Geringster Code-Overhead, kein neuer Section-State.

---

### Testplan

**Automatisiert (pytest):** Kein Backend betroffen → kein pytest-Fall nötig.

**Manuell (Browser unter http://localhost:8000):**

1. Feed öffnen → Goldene-Wolken-Event antippen → Detail-Sheet öffnet sich → Sektion „Warum Goldene Wolken?" aufklappen → **erwartet: Kompass-Diagramm erscheint** mit Sonnen-Pfeil, Sichtachse, goldene Zone (AK-1).
2. Himmelsröte-Event tippen → Detail-Sheet → „Warum Himmelsröte?" → **erwartet: rotes Rund-Diagramm** ohne Richtungssektor, Sonnen-Pfeil korrekt positioniert (AK-2).
3. Zwei Goldene-Wolken-Events aus verschiedenen Locations vergleichen → **erwartet: Sichtachsen-Linien zeigen in unterschiedliche Richtungen** (AK-3).
4. Location ohne Motivkoordinaten suchen → Goldene-Wolken-Event → Diagramm → **erwartet: Sonnen-Pfeil + Nord sichtbar, keine Sichtachse, kein Fehler** (AK-4).
5. Safari öffnen → gleiche Schritte → **erwartet: Diagramm vollständig sichtbar** (AK-5).
6. Goldene-Stunde-Event öffnen → **erwartet: kein Kompass-Diagramm** (AK-6 Regression).

---

### Analyse & Planung

- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` Z. 3540–3600 (ev_golden_clouds / ev_red_sky), Z. 779–809 (SVG-Symbole), Z. 3692 (EV_SKYPOS_EXEMPT)
- [x] Implementierungsoptionen: A (inline) / B (neue Section)
- [x] Empfehlung: Option A

**Scope:**
- Eingeschlossen: Inline-SVG-Kompass-Diagramm in ev_golden_clouds und ev_red_sky Sections. Nur `web/index.html`.
- Ausgeschlossen: Kein Backend-Change, keine neue Section, kein Filter-Chip, kein Kalender/Scout-Entry, keine andere Event-Typen.

---

### US-113 · Himmelsröte-Chance nur bei Wolken in Sichtachsen-Richtung `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-07-01 |
| **Abgeschlossen** | 2026-07-02 |

**Beschreibung:** Die „Himmelsröte"-Chance (RED_SKY, Sonnenauf-/-untergang-Himmelsfarbe/„goldene Stunde") soll nur ausgelöst werden, wenn sich die Wolkenzone mit der Sichtachse vom Standort zum Motiv überschneidet. Liegen die Wolken zwar vor, aber außerhalb der Blickrichtung, soll keine Chance generiert werden — aktuell wird Himmelsröte bewusst omnidirektional (ohne Richtungsfilter) ausgelöst.

**Bezug:** US-109 [x] hat RED_SKY bewusst **ohne** Richtungsfilter spezifiziert (Rule 2 + Q3-Entscheid: „Röte ist omnidirektional", da keine echte gerichtete Wolkendatenquelle verfügbar war — nur `golden_cloud_score` + `cloud_cover_low/mid ≥ 60 %`). GOLDEN_CLOUDS hat dagegen bereits einen Richtungsfilter (±30° Azimut-Differenz Sonnenazimut↔Sichtachse) erhalten. Dieses Ticket überschreibt/verschärft die US-109-Entscheidung für RED_SKY gezielt — nutzt denselben Azimut-Differenz-Mechanismus wie GOLDEN_CLOUDS (`backend/calculations/weather.py`, `subject_azimuth`, `sunrise/sunset_azimuth`). **Korrektur zum Intake-Kontext:** US-111 ist bereits **`[x]` Done** (abgeschlossen 2026-07-01), nicht mehr „In Progress" — das Kompass-Diagramm für Himmelsröte ist bereits live im Detail-Sheet. Es zeigt (Code-Verifikation, siehe unten) **keinen reinen Vollkreis**, sondern bereits eine Halbring-Zone (±90° gegenüber der Sonnenrichtung, `sunAz+90` bis `sunAz+270`). Falls US-113 einen engeren Richtungsfilter einführt, muss diese Zone in `web/index.html` (`mkCloudCompassSvg()`) mit angepasst werden — das ist Teil des Scopes dieser Analyse, siehe Architektur-Analyse unten.

---

## Analyse (US-113) · 2026-07-01

> ⚠️ **Korrektur nach Live-Test, 2026-07-02:** Die ursprüngliche Analyse (sofort unten) enthielt einen fachlichen Geometrie-Fehler bei der **Referenzrichtung** für RED_SKY. Angenommen wurde: "RED_SKY funktioniert nach demselben Mechanismus wie GOLDEN_CLOUDS" — das stimmt für den generellen **Ansatz** (Azimut-Differenz mit Toleranzwinkel, Sonnenazimut als einzig verfügbarer gerichteter Proxy), aber **nicht** für die Referenzrichtung selbst.
>
> **Fachlicher Fehler:** Die Spec/Implementierung verglich `subject_azimuth` direkt gegen `sun_azimuth` (wie bei GOLDEN_CLOUDS). Das ist für GOLDEN_CLOUDS (Alpenglühen-artiges direktes Streulicht um die Sonne) richtig, aber für RED_SKY/Himmelsröte fachlich falsch.
>
> **Neue Regel:** Himmelsröte (Gegendämmerung, "Belt of Venus") entsteht am **Gegenpunkt der Sonne** (Antisolarpunkt = `(sun_azimuth + 180) % 360`), nicht am Sonnenazimut selbst. Die günstige Zone für RED_SKY muss also um den Gegenpunkt liegen, nicht um die Sonne.
>
> Quellen: [Gegendämmerung (Wikipedia DE)](https://de.wikipedia.org/wiki/Gegend%C3%A4mmerung), [Belt of Venus (Wikipedia EN)](https://en.wikipedia.org/wiki/Belt_of_Venus)
>
> Entdeckt von Stephan per Screenshot: Kompass-Diagramm zeigte die Sonne oben links, die rote "günstige Zone" lag aber fälschlich ebenfalls um die Sonne herum statt gegenüber.
>
> Der generelle Azimut-Toleranz-Ansatz (Wraparound-Vergleich, ±30° Toleranz, Fallback ohne `subject_azimuth`) bleibt unverändert richtig — korrigiert wird ausschließlich der Referenzwert, gegen den `subject_azimuth` verglichen wird (Details in Implementierung, Testplan-Nachtrag und Code, siehe unten sowie `backend/calculations/weather.py`, `web/index.html`, `backend/tests/test_us113.py`).

### Example Mapping

**Scope-Check:** Das Ticket nimmt eine bewusste Design-Entscheidung aus US-109 (Q3: „Röte ist omnidirektional") zurück. Das ist keine Erweiterung eines ersten Slices, sondern eine gezielte Verschärfung einer bereits getroffenen und live ausgerollten Entscheidung. Das wird als 🔴-Frage behandelt (Q1 unten), da es unmittelbar App-Verhalten betrifft, das Nutzer heute schon sehen.

**Annahmen-Protokoll:**

| Punkt | Typ | Entscheidung / Default |
|-------|-----|------------------------|
| Rücknahme der Q3-Entscheidung aus US-109 (RED_SKY omnidirektional → jetzt richtungsgebunden) — ist das wirklich gewollt, oder nur eine Verschärfung für bestimmte Fälle? | 🔴 Kritisch | ❓ Q1 — siehe unten |
| Toleranzwinkel für die Sichtachsen-Bindung bei RED_SKY: identisch zu GOLDEN_CLOUDS (±30°) oder eigener, ggf. größerer Wert? | 🔴 Kritisch | ❓ Q2 — siehe unten |
| Geometrische Prüfung „Wolken überschneiden Sichtachse": echte Wolkenrichtung oder derselbe Azimut-Differenz-Proxy wie GOLDEN_CLOUDS (Sonnenazimut ↔ Motivazimut)? | 🔴 Kritisch (Datenlage) | ❓ Q3 — siehe unten (Datenlage siehe Pre-Mortem) |
| Soll US-111s Kompass-Diagramm (Halbring ±90° für Himmelsröte) in diesem Ticket mit angepasst werden, oder ausdrücklich als Folgeticket abgegrenzt? | 🔴 Kritisch (Scope) | ❓ Q4 — siehe unten |
| Edge Case: Wolken/Sichtachse exakt am Toleranzrand (z. B. Differenz = 30,0°) | ⚪ Konventionell | Default: `≤` (inklusiv), analog zur bestehenden GOLDEN_CLOUDS-Implementierung (`diff <= 30`, siehe Code-Verifikation) |
| Bestehende „Himmelsröte ist rundum sichtbar"-Texte im Detail-Sheet (`web/index.html` Z. 3750) | ⚪ Konventionell | Default: Text muss mit angepasst werden, wenn Q1 mit „ja, Filter einführen" beantwortet wird — sonst widerspricht die App-Erklärung dem neuen Verhalten |

**🔴 Offene Fragen (bitte vor Freigabe beantworten — Best-Effort-Spec unten trotzdem vollständig, mit Annahmen markiert):**

1. **Q1 — Rücknahme bestätigen:** Soll die Q3-Entscheidung aus US-109 („Röte ist omnidirektional") vollständig zurückgenommen werden, sodass RED_SKY ab sofort einen Richtungsfilter wie GOLDEN_CLOUDS bekommt? Oder ist eine mildere Variante gemeint (z. B. größerer Toleranzwinkel als GOLDEN_CLOUDS, weil Himmelsröte physikalisch tatsächlich einen größeren Sichtbarkeitsbereich hat als eng gebündelte goldene Wolken)?
   *Best-Effort-Annahme für diese Spec:* Ja, vollständige Rücknahme — RED_SKY bekommt denselben Mechanismus wie GOLDEN_CLOUDS (harter Azimut-Schwellwert), da das Ticket „soll nur ausgelöst werden, wenn..." eindeutig eine Bedingung statt eine Gewichtung fordert.

2. **Q2 — Toleranzwinkel:** Gleicher Wert wie GOLDEN_CLOUDS (±30°) oder ein eigener, größerer Wert (z. B. ±60°) mit der Begründung, dass Himmelsröte ein flächigeres, weniger scharf gebündeltes Phänomen ist als goldene Wolken direkt hinterm Motiv?
   *Best-Effort-Annahme für diese Spec:* ±30°, identisch zu GOLDEN_CLOUDS — konsistent, einfach zu erklären, keine Sonderregel nötig. Falls Stephan einen größeren Winkel für physikalisch treffender hält, ist das ein Ein-Zeilen-Parameter-Wechsel (`RED_SKY_AZ_TOLERANCE = 30` als eigene Konstante, siehe Implementierungsoptionen).

3. **Q3 — Datenlage (siehe auch Pre-Mortem):** Bestätigt durch Code-Verifikation unten: Es gibt **keine** echte Wolkenrichtungsdaten in den Wetterdaten (Open-Meteo liefert nur `cloud_cover_low/mid/high_pct` als Gesamtprozent über dem Standort — bereits in US-109 abschließend geklärt, siehe dortige Datenquellen-Klärung). Die einzige verfügbare Richtungsinformation ist der Sonnenazimut (`sunrise_azimuth`/`sunset_azimuth`) als Proxy. Frage an Stephan: Ist dieser Proxy (identisch zu GOLDEN_CLOUDS) für Stephan akzeptabel, oder sollte RED_SKY aus fachlicher Sicht anders behandelt werden, weil „Röte am Himmel" nicht zwingend an der Sonnenposition hängt (auch entgegengesetzter Himmel kann rot leuchten – Alpenglühen-Effekt)?
   *Best-Effort-Annahme für diese Spec:* Denselben Proxy-Mechanismus wie GOLDEN_CLOUDS verwenden (keine Alternative verfügbar) — mit dem Hinweis, dass das eine Näherung bleibt und im Detail-Sheet transparent kommuniziert wird (wie bereits bei GOLDEN_CLOUDS in US-109 gehandhabt).

4. **Q4 — Scope zu US-111:** Soll die Anpassung des Kompass-Diagramms (Halbring → Sektor, analog zur GOLDEN_CLOUDS-Zone) **innerhalb** von US-113 miterledigt werden, oder als eigenes Folgeticket abgegrenzt?
   *Best-Effort-Annahme für diese Spec:* Innerhalb von US-113 miterledigen — sonst zeigt das Detail-Sheet nach Release einen Diagramm-Halbring, der dem neuen (engeren) Filterverhalten widerspricht: ein Nutzer sähe im Diagramm eine ±90°-Zone, obwohl die Chance real nur bei ±30° ausgelöst wird. Das wäre eine sofort sichtbare Inkonsistenz. Wird unten als expliziter Teil-Scope geführt (Architektur-Analyse + Implementierungsoptionen).

**Rules + Examples:**

📏 **Rule 1: RED_SKY wird nur noch erzeugt, wenn zusätzlich zur bestehenden Wolkenbedingung auch die Richtungsbedingung erfüllt ist**
- 🟢 *Given* `gcs=0.85`, `cl=40, cm=35` (Wolkenbedingung erfüllt wie bisher), `sunset_azimuth=278°`, `subject_azimuth=265°` (Differenz 13° ≤ 30°), *When* das Wetter-Overlay läuft, *Then* erscheint die „Himmelsröte"-Karte im Feed — wie bisher.
- 🔴 *Given* `gcs=0.85`, `cl=40, cm=35` (Wolkenbedingung erfüllt), `sunset_azimuth=278°`, `subject_azimuth=90°` (Differenz 172°), *When* das Wetter-Overlay läuft, *Then* erscheint **keine** „Himmelsröte"-Karte — obwohl die Wolkenbedingung erfüllt wäre (neues Verhalten ggü. US-109).

📏 **Rule 2: Fehlt die Motivrichtung (kein `subject_azimuth`), kann kein Richtungsvergleich stattfinden**
- 🟢 *Given* eine Location ohne definiertes Motiv (`subject_azimuth = null`), Wolkenbedingung erfüllt, *When* das Wetter-Overlay läuft, *Then* [siehe ❓ hierzu: Fallback-Verhalten muss geklärt werden — zwei plausible Varianten unten].
- ❓ Zwei sinnvolle Verhaltensweisen sind denkbar: (a) ohne Motiv keine Sichtachse definierbar → RED_SKY entfällt komplett (konsistent mit GOLDEN_CLOUDS-Verhalten, AK-12 aus US-109), oder (b) ohne Motiv fällt der Filter automatisch weg → RED_SKY bleibt omnidirektional (Rückfall auf US-109-Verhalten als Fallback). *Best-Effort-Annahme:* Variante (a) — konsistent mit GOLDEN_CLOUDS, einfacher zu erklären („keine Motivrichtung = keine Sichtachsen-Chance"). Als Frage an Stephan im Weg-Gate erneut aufgreifen, falls (b) bevorzugt wird.

📏 **Rule 3: Das Kompass-Diagramm im Detail-Sheet zeigt für Himmelsröte künftig eine Richtungszone statt eines Halbrings**
- 🟢 *Given* ein Himmelsröte-Event mit `sunset_azimuth=278°`, `subject_azimuth=265°`, *When* ich das Detail-Sheet öffne, *Then* zeigt das Kompass-Diagramm eine rote Zone von ±30° um die Sichtachse (analog zur goldenen Zone bei GOLDEN_CLOUDS) statt des bisherigen ±90°-Halbrings.

📏 **Rule 4: Bestehende Erklärungstexte im Detail-Sheet werden an das neue Verhalten angepasst**
- 🟢 *Given* ein Himmelsröte-Event, *When* ich die „Warum Himmelsröte?"-Sektion öffne, *Then* lese ich nicht mehr „Diese Röte ist rundum sichtbar — du brauchst keine bestimmte Blickrichtung", sondern einen Text der die Richtungsbedingung erklärt (analog zum GOLDEN_CLOUDS-Text).

---

### Akzeptanzkriterien

- [ ] **AK-1:** Zeigt eine Location bereits heute die Bedingungen für eine „Himmelsröte"-Karte (Wolken tief+mittel ≥ 60 %, Score ≥ 0,80) UND die Sonne geht in Motivrichtung auf/unter (Winkel-Differenz ≤ 30°), erscheint die Karte weiterhin wie bisher.
- [ ] **AK-2:** Zeigt eine Location die gleichen Wolkenbedingungen, aber die Sonne geht **nicht** in Motivrichtung auf/unter (Winkel-Differenz > 30°), erscheint **keine** „Himmelsröte"-Karte mehr im Feed — auch wenn die Wolken vorhanden sind.
- [ ] **AK-3:** Bei einer Location **ohne** definiertes Motiv (keine Motivkoordinaten) erscheint keine „Himmelsröte"-Karte, selbst wenn die Wolkenbedingung erfüllt ist (kein Richtungsvergleich möglich — analog zu Goldene Wolken).
- [ ] **AK-4:** Im Detail-Sheet einer „Himmelsröte"-Karte zeigt das Kompass-Diagramm eine rote Richtungszone (±30° um die Sichtachse) statt des bisherigen Halbrings ringsum.
- [ ] **AK-5:** Der Erklärungstext in der „Warum Himmelsröte?"-Sektion beschreibt die neue Richtungsbedingung (Sonne ↔ Motiv ≤ 30°) statt der bisherigen Aussage „rundum sichtbar, keine bestimmte Blickrichtung nötig".
- [ ] **AK-6 (Regression):** „Goldene Wolken"-Karten und ihr Verhalten bleiben unverändert (kein Nebeneffekt auf GOLDEN_CLOUDS-Logik).
- [ ] **AK-7 (Regression):** Die normale Wetter-Sektion (Wolken, Temperatur etc.) im Detail-Sheet bleibt unverändert.
- [ ] Edge Case AK-8: Bei einer Winkel-Differenz von genau 30,0° erscheint die Karte weiterhin (inklusive Grenzwert, `≤`).
- [ ] Edge Case AK-9: Fehlt das Wetter-Overlay (Event > 3 Tage in der Zukunft), erscheint wie bisher keine „Himmelsröte"-Karte (unverändert zu US-109).

---

### Pre-Mortem

📎 **Code-Verifikation (2026-07-01):**
- `backend/calculations/weather.py` Z. 211–236 gelesen: `should_generate_red_sky_event(gcs, cl, cm)` prüft aktuell **nur** `gcs >= 0.80` und `(cl + cm) >= 60` — **kein** Azimut-Parameter vorhanden. Docstring bestätigt explizit: „Kein Richtungsfilter: Himmelsröte ist omnidirektional sichtbar." Das ist die Stelle, die geändert werden muss.
- `backend/calculations/weather.py` Z. 182–208 gelesen: `should_generate_golden_clouds_event(gcs, sun_azimuth, subject_azimuth)` ist die exakte Vorlage — bereits als reine, gut testbare Funktion mit Azimut-Differenz-Berechnung (`diff = abs(sun_azimuth - subject_azimuth) % 360`, dann `diff > 180 → 360 - diff`, dann `diff <= 30`). Wiederverwendbares Muster, 1:1 übertragbar.
- `backend/main.py` Z. 504–572 (`_generate_cloud_mood_events`) gelesen: Ruft `should_generate_red_sky_event(gcs, cl, cm)` in Z. 559 auf — **ohne** `sun_az`/`subject_az`, obwohl beide Werte in derselben Funktion für GOLDEN_CLOUDS bereits berechnet sind (Z. 534–540: `sun_az` und `subject_az` stehen zum Zeitpunkt des RED_SKY-Checks längst zur Verfügung). Erweiterung ist ein kleiner, lokaler Eingriff — keine neue Datenbeschaffung nötig.
- **Datenlage bestätigt (zentrale technische Frage):** Open-Meteo liefert laut US-109-Datenquellen-Klärung (BACKLOG.md Z. 2539–2545) **nur Gesamtprozent-Bedeckung pro Höhenschicht** (`cloud_cover_low/mid/high_pct`), keine räumliche/richtungsbezogene Verteilung. Es gibt **keine** Wolkenposition am Himmel in den Wetterdaten — nur die Sonnenazimut-Werte (`sunrise_azimuth`/`sunset_azimuth`) sind gerichtete Daten, die bereits im Event-Objekt verfügbar sind (`backend/precompute.py` Z. 516–537, bestätigt in US-109-Code-Verifikation). Der einzig verfügbare Mechanismus ist somit derselbe Sonnenazimut-Proxy wie bei GOLDEN_CLOUDS — **nicht** eine echte Wolkenrichtungsprüfung.
- `web/index.html` Z. 3275–3394 (`mkCloudCompassSvg`) gelesen: Für RED_SKY wird aktuell eine Zone von `sunAz+90` bis `sunAz+270` gezeichnet (Kommentar Z. 3297: „RED_SKY = ±90° (half-ring opposite of sun)") — das ist bereits **kein** echter Vollkreis, wie der Ticket-Text „Farbring ringsum" nahelegt, sondern ein Halbring gegenüber der Sonne. Diese Zone muss auf einen ±30°-Sektor um die Sichtachse verengt werden, wenn Q1/Q2 wie angenommen entschieden werden — analog zum bestehenden GOLDEN_CLOUDS-Zonencode (Z. 3302–3304).
- `web/index.html` Z. 3735–3753 (RED_SKY-Erklärungssektion) gelesen: Enthält Legende + Erklärtext mit „Diese Röte ist rundum sichtbar — du brauchst keine bestimmte Blickrichtung" (Z. 3750) und Legenden-Text „Günstige Zone (Röte)" (Z. 3377) — beide müssen bei Filtereinführung textlich angepasst werden, sonst widerspricht die App-Erklärung dem neuen Verhalten.

💀 **Szenario 1: Datenlage nur Gesamt-Bedeckungsgrad, keine echte Wolkenrichtung — Ticket-Formulierung „Wolken überschneiden sich mit der Sichtachse" ist geometrisch nicht wörtlich umsetzbar**
- Auslöser: Der Ticket-Text suggeriert eine echte räumliche Wolkenprüfung. Die verfügbare Datenlage (siehe Code-Verifikation) erlaubt das nicht — es gibt nur einen Sonnenazimut-Proxy, keine Wolkenposition.
- Frühwarnung: Wurde bereits in US-109 exakt so durchdekliniert und dokumentiert (Datenquellen-Klärung, Fazit: „nicht realisierbar").
- Gegenmaßnahme: Spec verwendet explizit den Sonnenazimut-Proxy (wie GOLDEN_CLOUDS) statt einer wörtlichen Wolken-Geometrie-Prüfung — im Detail-Sheet und in der Spec transparent als Näherung kommuniziert (siehe AK-5, Implementierungsoptionen).

💀 **Szenario 2: US-111-Diagramm wird vergessen — Diagramm zeigt weiterhin ±90°-Halbring, Filter greift aber bei ±30°**
- Auslöser: US-113 wird als reine Backend-Änderung missverstanden; das Frontend-Diagramm (US-111, bereits live) wird nicht mit angepasst.
- Frühwarnung: Ein Nutzer öffnet eine der wenigen (jetzt selteneren) Himmelsröte-Karten und sieht ein Diagramm, das eine viel größere „günstige Zone" zeigt, als tatsächlich zur Auslösung geführt hat — Diagramm und Realität widersprechen sich sichtbar.
- Gegenmaßnahme: Q4 explizit gestellt; Best-Effort-Annahme nimmt die Diagramm-Anpassung in den Scope von US-113 auf (siehe AK-4, Architektur-Analyse, Implementierungsoptionen).

💀 **Szenario 3: Deutlich weniger Himmelsröte-Events als vorher — Nutzer empfindet Feature als "kaputt"**
- Auslöser: RED_SKY war bisher omnidirektional und damit für jede Location mit passenden Wolken auslösbar. Mit Richtungsfilter fällt ein großer Teil der Locations (die nicht zufällig in Sonnenrichtung liegen) komplett raus — potenziell ein harter Rückgang der Event-Häufigkeit.
- Frühwarnung: Keine quantitative Prüfung möglich ohne Live-Daten (kein Zugriff auf aktuelle Cache-Statistiken in der Analyse-Phase) — sollte vor Release stichprobenartig gegen den Live-Cache geprüft werden (`/opportunities` Counter für `event_type == "Himmelsröte"` vor/nach Deploy vergleichen).
- Gegenmaßnahme: Als Testschritt im Testplan verankert (manueller Vorher/Nachher-Vergleich). Falls der Rückgang zu stark ausfällt, ist Q2 (größerer Toleranzwinkel) die vorgesehene Stellschraube.

💀 **Szenario 4: `subject_azimuth`-Fallback-Verhalten uneindeutig — RED_SKY verschwindet für alle Locations ohne Motiv komplett**
- Auslöser: Viele Locations haben laut US-109-Pre-Mortem-Szenario 3 kein definiertes Motiv (`subject_azimuth IS NULL`). Bisher liefen diese Locations für RED_SKY trotzdem durch (omnidirektional). Mit Filter würden sie komplett wegfallen — eine potenziell große, stille Verhaltensänderung.
- Frühwarnung: Keine Live-Zählung der Locations ohne Motiv in dieser Analyse durchgeführt (siehe ❓ Q2 in Rule 2) — sollte vor Freigabe geprüft werden.
- Gegenmaßnahme: Als offene Rule-2-Frage markiert; Best-Effort-Annahme (a) gewählt, aber Stephan sollte die Zahl der betroffenen Locations vor Freigabe sehen (Empfehlung: kurzer DB-Check `SELECT COUNT(*) FROM locations WHERE subject_lat IS NULL` vor Implementierungsstart).

💀 **Szenario 5: `ev_compass_rs`-Section-Guard und Legendentexte laufen bei der Umstellung auf Sektor-Zone auseinander**
- Auslöser: `mkCloudCompassSvg()` wird für GOLDEN_CLOUDS und RED_SKY gemeinsam genutzt (`isRedSky`-Flag steuert nur Farbe + Zonen-Winkel). Wird die Zonen-Berechnung für RED_SKY versehentlich identisch zur GOLDEN_CLOUDS-Farbe (statt rot) umgestellt, oder der Legendentext nicht mitgezogen, entsteht eine visuell inkonsistente Karte (rote Farbe, aber falscher Zonenwinkel oder falscher Text).
- Frühwarnung: Bei manuellem Test das Diagramm visuell mit einer aktuellen GOLDEN_CLOUDS-Karte vergleichen — Farbe muss rot bleiben, nur der Winkel (90°→30°) ändert sich.
- Gegenmaßnahme: In AK-4 verankert; Implementierung ändert ausschließlich die Zonen-Winkelberechnung in Z. 3299–3304, nicht die Farblogik.

---

### Architektur-Analyse

**Betroffene Dateien (alle gelesen, nicht nur überflogen):**

1. `backend/calculations/weather.py` (Z. 211–236) — `should_generate_red_sky_event()` erhält zwei neue Parameter (`sun_azimuth`, `subject_azimuth`) und die Azimut-Differenz-Prüfung analog zu `should_generate_golden_clouds_event()` (Z. 182–208, direkte Vorlage).
2. `backend/main.py` (Z. 504–572, `_generate_cloud_mood_events`) — Aufruf in Z. 559 wird um `sun_az`, `subject_az` erweitert (beide Werte liegen zum Zeitpunkt des Aufrufs bereits vor, Z. 534–540). Guard für `subject_az is not None` ergänzen (analog zu GOLDEN_CLOUDS-Guard in Z. 543).
3. `web/index.html` (Z. 3275–3394, `mkCloudCompassSvg`) — Zonen-Berechnung für `isRedSky` (Z. 3299–3304) von `sunAz+90…sunAz+270` (Halbring) auf `sunAz-30…sunAz+30` (Sektor, wie GOLDEN_CLOUDS) umstellen. Reine Zahlenänderung, keine neue Funktion nötig — ggf. eigene Konstante statt hartcodiertem `30`, um Q2-Antwort (Toleranzwinkel) leicht änderbar zu halten.
4. `web/index.html` (Z. 3735–3753, RED_SKY-Erklärungssektion) — Text „Diese Röte ist rundum sichtbar — du brauchst keine bestimmte Blickrichtung" durch einen Text ersetzen, der die Richtungsbedingung erklärt (analog zum GOLDEN_CLOUDS-Text Z. 3730). Legendentext Z. 3377 „Günstige Zone (Röte)" bleibt sachlich korrekt, kann bestehen bleiben.
5. `web/index.html` (Z. 3743–3746) — `rsSunAz` und `o.subject_azimuth` werden bereits ans Diagramm übergeben; keine neue Datenübergabe nötig, nur die Zonen-Logik in `mkCloudCompassSvg` ändert sich.
6. `backend/tests/test_us113.py` (neu, siehe Testplan) — Kein `backend/tests/`-Verzeichnis im Repo vorhanden (per Glob geprüft) — muss ggf. neu angelegt werden, analog zur in US-109 referenzierten (aber ebenfalls nicht vorgefundenen) `test_us109.py`. Wird in Implementierungsphase geklärt/angelegt.

**Einstiegspunkt-Check:**
- `/opportunities` → `_feed_cache` → `_generate_cloud_mood_events()` → ✅ betroffen, hier greift der neue Filter.
- `/calendar`, `/discover` (Scout) → kein Wetter-Overlay, RED_SKY erscheint dort laut US-109 ohnehin nicht → nicht betroffen.

**Kein neues Score-Feld, kein neuer Event-Typ (Schritt 4f entfällt):** RED_SKY existiert bereits als Event-Typ mit Filter-Chip (US-109 AK-8) — dieses Ticket ändert nur die Auslöse-Bedingung, keine neue UI-Filterkategorie nötig.

---

### Designer-Check (Schritt 4b)

Diese Änderung hat **sichtbare** Auswirkungen (Kompass-Diagramm-Zone ändert sich von Halbring zu Sektor, Erklärungstext ändert sich) — aber es handelt sich um eine reine **Parameteränderung an einer bereits bestehenden, gestalteten Komponente** (`mkCloudCompassSvg`, durch `fotoalert-designer` im Rahmen von US-111 bereits abgenommen: Farben, Radien, SVG-Aufbau). Es entsteht **kein neues visuelles Element**, keine neue Farbe, kein neues Icon — nur der Winkelbereich einer bestehenden Zone wird verengt (90°→30°) und ein Text angepasst.

**Kein zusätzlicher Designer-Call für dieses Ticket nötig.** Festgehalten als Abhängigkeit: Die Diagramm-Anpassung ist **kein eigenständiger Scope von US-113**, sondern eine notwendige Folgeanpassung an US-111, die hier aus Konsistenzgründen mit erledigt wird (siehe Q4). Sollte Stephan die Diagramm-Anpassung lieber als eigenes Ticket auslagern wollen, ist das im Weg-Gate zu entscheiden.

---

### Implementierungsoptionen

**Option A — Sonnenazimut-Proxy, identischer Mechanismus wie GOLDEN_CLOUDS (empfohlen)**

*Was du in der App erlebst:* Himmelsröte-Karten erscheinen ab sofort nur noch, wenn die Sonne beim Auf-/Untergang aus der Richtung leuchtet, in die du dein Motiv fotografierst — genau wie bei „Goldene Wolken" heute schon. Liegt die Sonne beim Sonnenuntergang im Westen, dein Motiv aber im Osten, bekommst du keine Himmelsröte-Karte mehr für diese Location, selbst wenn genug Wolken da sind. Das Kompass-Diagramm im Detail-Sheet zeigt die günstige Zone dann als engeren Sektor statt als große Halbkreis-Fläche.

- Vorgehen: `should_generate_red_sky_event()` um `sun_azimuth`/`subject_azimuth`-Parameter + Azimut-Differenz-Prüfung (`≤ 30°`, wie GOLDEN_CLOUDS) erweitern. Aufrufstelle in `main.py` entsprechend füttern. Diagramm-Zone in `index.html` von Halbring auf Sektor umstellen. Erklärungstext anpassen.
- Betroffene Dateien: `weather.py`, `main.py`, `index.html` (Diagramm + Text), `tests/test_us113.py` (neu).
- Vorteile: Keine neue Datenquelle nötig, exakt dieselbe Datenlage/Architektur wie bei GOLDEN_CLOUDS bereits produktiv und getestet; kleiner, gut abgrenzbarer Eingriff; konsistente Nutzererfahrung (beide Wolken-Chancen funktionieren nach demselben Prinzip).
- Nachteile / Risiken: Bleibt eine Näherung (Sonnenazimut ≠ echte Wolkenposition) — physikalisch kann Himmelsröte auch entgegengesetzt der Sonne sichtbar sein (Alpenglühen-Effekt), das wird mit diesem Ansatz nicht erfasst. Die Zahl der ausgelösten Himmelsröte-Events sinkt spürbar (siehe Pre-Mortem Szenario 3) — sollte vor Release stichprobenartig geprüft werden.
- Aufwand: klein bis mittel (Backend: klein, Frontend-Diagramm+Text: klein, Tests: klein).

**Option B — Eigener, großzügigerer Toleranzwinkel für RED_SKY (z. B. ±60° statt ±30°)**

*Was du in der App erlebst:* Wie Option A, aber der Sichtachsen-Filter ist bei Himmelsröte großzügiger als bei Goldenen Wolken — Himmelsröte-Karten erscheinen noch, wenn die Motivrichtung bis zu 60° von der Sonnenrichtung abweicht (statt 30°). Grund: Himmelsröte ist ein physikalisch großflächigeres Phänomen als eng gebündelte goldene Wolken direkt hinterm Motiv.

- Vorgehen: Identisch zu Option A, aber mit eigener Konstante `RED_SKY_AZ_TOLERANCE = 60` statt Wiederverwendung des GOLDEN_CLOUDS-Werts.
- Betroffene Dateien: Gleich wie Option A.
- Vorteile: Fängt den Effekt ab, dass Himmelsröte tatsächlich physikalisch weiter sichtbar sein kann als goldene Wolken direkt am Motiv; mildert den befürchteten Event-Rückgang aus Pre-Mortem-Szenario 3.
- Nachteile / Risiken: Der konkrete Winkel (60°? 45°? 90°?) ist reine Schätzung ohne empirische Grundlage — genauso wenig belegt wie 30°. Erfordert eine explizite Entscheidung von Stephan (Q2), die aktuell nicht vorliegt.
- Aufwand: identisch zu Option A (nur ein Konstantenwert unterschiedlich).

✅ **Empfehlung: Option A** — mit `RED_SKY_AZ_TOLERANCE` als **eigene, benannte Konstante** (nicht hart auf denselben Wert wie GOLDEN_CLOUDS verdrahtet), initial auf 30° gesetzt. Das macht Q2 im Nachhinein zu einer Ein-Zeilen-Änderung, falls Stephan nach dem Live-Test einen größeren Winkel bevorzugt — ohne Code-Struktur-Änderung. Reine Datenlage lässt keine bessere Option zu (Option „echte Wolkenrichtung" wurde in US-109 bereits als nicht realisierbar verworfen, siehe Code-Verifikation).

---

### Testplan

- [ ] **Automatisiert** (`backend/tests/test_us113.py`, neu anzulegen — kein bestehendes `backend/tests/`-Verzeichnis gefunden):
  - AK-1: `gcs=0.85, cl=40, cm=35, sunset_azimuth=278, subject_azimuth=265` → `should_generate_red_sky_event(...)` liefert `True`.
  - AK-2: `gcs=0.85, cl=40, cm=35, sunset_azimuth=278, subject_azimuth=90` → liefert `False` (Differenz 172° > 30°).
  - AK-3: `subject_azimuth=None` → liefert `False` (kein Richtungsvergleich möglich).
  - AK-8 (Edge Case): Differenz exakt `30.0°` → liefert `True` (inklusiver Grenzwert).
  - AK-6 (Regression): GOLDEN_CLOUDS-Testfälle aus US-109 laufen unverändert grün.

- [ ] **Manuell** (Browser + curl nach Serverstart unter `http://localhost:8000`):
  1. `curl "http://localhost:8000/opportunities?days=3"` → Anzahl `event_type == "Himmelsröte"` **vor** und **nach** der Änderung zählen (Vergleichswert für Pre-Mortem-Szenario 3 — spürbarer Rückgang erwartet, aber nicht Totalausfall).
  2. App öffnen → Feed → eine verbleibende Himmelsröte-Karte antippen → Detail-Sheet → „Warum Himmelsröte?"-Sektion öffnen → **erwartet:** Kompass-Diagramm zeigt engen roten Sektor (nicht mehr Halbring), Text erklärt die Richtungsbedingung (AK-4, AK-5).
  3. Falls auffindbar: eine Location mit Wolkenbedingung erfüllt, aber Motiv entgegen der Sonnenrichtung → **erwartet:** keine Himmelsröte-Karte mehr (AK-2).
  4. Regression: „Goldene Wolken"-Karten weiterhin normal sichtbar und unverändert (AK-6).
  5. Regression: normale Wetter-Sektion (Temperatur, Wolken %, Regen) im Detail-Sheet unverändert (AK-7).

---

### Analyse & Planung

- [x] Example Mapping durchgeführt (2026-07-01)
- [x] Akzeptanzkriterien abgeleitet (2026-07-01)
- [x] Pre-Mortem durchgeführt inkl. Code-Verifikation (2026-07-01)
- [x] Architektur analysiert: `backend/calculations/weather.py`, `backend/main.py`, `web/index.html` (Kompass-Diagramm + Erklärungstext)
- [x] Designer-Check: visuell sichtbar, aber reine Parameteränderung an bestehender, bereits abgenommener Komponente → kein zusätzlicher Designer-Call nötig
- [x] Implementierungsoptionen: A (Proxy, gleicher Winkel wie GOLDEN_CLOUDS) / B (Proxy, eigener größerer Winkel)
- [x] Empfehlung: Option A mit eigener, leicht änderbarer Toleranzwinkel-Konstante
- [x] 🔴 Offene Fragen Q1–Q4 von Stephan im Weg-Gate pauschal mit "ja" zur empfohlenen Option A bestätigt (2026-07-02) — alle Best-Effort-Annahmen (Q1 volle Rücknahme, Q2 30°, Q3 Sonnenazimut-Proxy, Q4 Diagramm im Scope) gelten damit als freigegeben
- [x] Weg-Gate: Option A gewählt (2026-07-02) — Implementierung gestartet
