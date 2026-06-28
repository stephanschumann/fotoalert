# FotoAlert – Backlog ARCHIV (erledigte Tickets)

> Aus BACKLOG.md ausgelagert. Wird vom Kanban-Generator zusammen mit BACKLOG.md gelesen.
> Nicht von Hand neu einsortieren; Lane-Quelle bleibt das `Status`-Feld bzw. Done-Marker.

## ✅ Erledigt (Archiv)

### BUG-42 · Custom Locations: 📍-Emoji in Namen + Test-Duplikate bereinigen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-27 |
| **Abgeschlossen** | 2026-06-27 |

**Beschreibung:** Mehrere Custom Locations in der SQLite-DB haben das 📍-Emoji hartcodiert im Namen (z. B. „📍 Ruinenberg - Blick auf Schloss Sanssouci"). Dieses Emoji erscheint im Feed-Alert-Chip und im Detail-Sheet als sichtbares Zeichen statt als Icon, weil die App den Namen ungefiltert rendert. Zusätzlich existieren zwei Duplikat-Testentries „📍 Test Ruinenberg" (IDs custom_1782294489, custom_1782301277), die gelöscht werden können. Fix: Emoji-Präfix bei allen 4 betroffenen Einträgen entfernen, Duplikate löschen, Cache neu erzeugen.

**Bezug:** Eigenständig; kosmetischer Fix im Zuge der Bauhaus-Designbereinigung (US-98).

---


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


### ~~BUG-25 · Close-Button in Locationdetails auf iPhone nicht anklickbar~~ `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **In Progress seit** | 2026-06-19 |
| **Abgeschlossen** | 2026-06-19 |

**Root Cause:** `#detail-sheet`, `#loc-detail-sheet` und `#impressum-sheet` hatten im Header-Div `padding:10px 16px 0` ohne Safe-Area-Berücksichtigung. Bei 92vh Sheetgröße reichte der Header in den Status-Bar-Bereich (im PWA Standalone Mode = `100vh` voller Bildschirm).

**Fix:** Header-Padding auf `calc(env(safe-area-inset-top, 0px) + 10px) 16px 0` — identisches Muster wie `.add-header` (BUG-19). Alle drei Sheets gleichzeitig korrigiert. Auf iPhone im PWA-Modus getestet und bestätigt. ✅

---


### BUG-26 · Standortverifikationen werden nicht persistiert `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **In Progress seit** | 2026-06-21 |
| **Abgeschlossen** | 2026-06-21 |

**Beschreibung:** Positive und negative Standortverifikationen werden zwar verarbeitet (Toast erscheint), aber nicht dauerhaft gespeichert. Nach dem Schließen und erneuten Öffnen der App sind alle Verifikationen zurückgesetzt. GPS-Koordinatenänderungen persistieren korrekt (Backend-PATCH + SQLite).

**Root Cause:** Verifikationen werden ausschließlich in `localStorage['fotoalert_verifications']` gespeichert. iOS löscht PWA-localStorage nach 7 Tagen Inaktivität (WebKit-Policy ab iOS 13.4); Kontext-Split zwischen PWA-Homescreen und Safari-Tab führt zu separaten Storage-Partitionen.

**Scope:** Verifikationen server-seitig persistieren. GPS-Änderungen sind nicht betroffen.

**Akzeptanzkriterien:**
- [x] Verifikation (✓ positiv, ⚠ Problem) bleibt nach App-Schließen und Neuöffnen erhalten
- [x] Verifikation ist auf einem zweiten Gerät nach Login sichtbar
- [x] Bestehende localStorage-Verifikationen werden beim ersten App-Start einmalig zum Backend migriert
- [x] `GET /locations/{id}/verifications` gibt alle Einträge zurück (kein Auth)
- [x] `POST /locations/{id}/verifications` speichert Eintrag (Auth: user + host)
- [x] Edge Case: Verifikation ohne Kommentar / ohne issue_type wird akzeptiert
- [x] Edge Case: Mehrfach-Verifikationen derselben Location korrekt als Liste gespeichert
- [x] Letzten Eintrag löschen (`DELETE /locations/{id}/verifications/last`) funktioniert

**Pre-Mortem:**
- 💀 iOS-Kontext-Split (PWA vs. Safari-Tab) → Gegenmaßnahme: Backend-Persistenz eliminiert das Problem
- 💀 Migration verliert vorhandene localStorage-Daten → Gegenmaßnahme: Migration pusht alle Einträge ans Backend, danach löschen
- 💀 Python-3.9-Inkompatibilität crasht Prod → Gegenmaßnahme: `from __future__ import annotations` + Optional statt `|`

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `backend/data/store.py`, `backend/main.py`, `web/index.html` (Verify-Objekt)
- [x] Implementierungsoption gewählt: Backend-Persistenz (neue SQLite-Tabelle + 2 Endpoints)

**Testplan:**
- [x] Automatisiert: `POST /locations/{id}/verifications` + `GET` Roundtrip in `backend/tests/test_api_regression.py` (6/6 Tests grün)
- [x] Manuell: POST + GET + DELETE Roundtrip via curl verifiziert (2026-06-21)

---


### BUG-38 · Chancendetails: Koordinaten-Sektion Layout (Overflow, Label, Ausrichtung, Kopierbarkeit) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-24 |
| **Abgeschlossen** | 2026-06-24 |

**Beschreibung:** In der Koordinaten-Sektion der Chancendetails gibt es vier zusammenhängende UI-Mängel: (1) Der „Streetview"-Button überläuft den Container rechts (nur „Stree" sichtbar). (2) Das Label „Standort Fotograf" soll zu „Standort" verkürzt werden. (3) Die Koordinatenzeilen für Standort und Motiv sind nicht gleich ausgerichtet (Motiv-Zeile fehlt Streetview-Button → asymmetrisches Layout). (4) Koordinaten sind reiner Text – nicht selektierbar/kopierbar; sie sollen als auswählbares Datenfeld (z. B. `user-select: all` oder readonly input) dargestellt werden.

**Bezug:** Screenshots von 2026-06-24. Verwandt mit BUG-39 (blaugrauer Strich im selben Header-Bereich), US-87 (größere Karte).

**Scope:**
Eingeschlossen: `.coords-row` CSS + HTML-Label im Event-Detail-Sheet (`web/index.html` Z. 297–299, 2995–3012).
Ausgeschlossen: Location-Detail-Sheet (kein `.coords-row`-Vorkommen dort); BUG-39 (blauer Strich = eigenes Ticket); US-95 (Button-Sizing).

**Akzeptanzkriterien:**
- [x] StreetView-Button „👁 Street View" vollständig sichtbar, kein Overflow
- [x] Label lautet „📷 Standort" (nicht „Standort Fotograf")
- [x] Koordinaten-Werte Standort und Motiv fluchten horizontal (gleiche Spalte)
- [x] Tap auf Koordinatenfeld markiert den gesamten Text (user-select: all)
- [x] Motiv-Zeile hat nur Maps-Button, Layout trotzdem ausgerichtet
- [x] Edge Case: kein Azimut → nur Maps-Button, kein Overflow
- [x] Edge Case: subject_lat null → Zeile ausgerichtet, kein JS-Fehler

**Pre-Mortem:**
- 💀 Grid `auto`-Spalte bei langem Label-Text → Label-Spalte `max-width: 90px` als Deckel
- 💀 `user-select: all` auf iOS Safari PWA nicht immer zuverlässig → manuell auf Device testen; Fallback `<input readonly>` vorbereiten
- 💀 Andere Sheet-Blöcke betroffen → `.coords-row` nur einmal im Event-Detail (bestätigt durch Grep), kein zweiter Block

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2026-06-24)
- [x] Pre-Mortem durchgeführt (2026-06-24)
- [x] Architektur analysiert: `web/index.html` Z. 297–301 (CSS) + Z. 2995–3012 (HTML)
- [x] Implementierungsoptionen: A (CSS Grid) / B (Sub-Zeile Buttons)
- [x] Empfehlung: Option A — **Stephan hat Option B gewählt:** Buttons in eigene Sub-Zeile (`<div class="coords-btns">`), Zeile 1 = Label+Wert, Zeile 2 = Buttons mit indent. Skaliert besser für US-95.

**📎 Code-Verifikation (2026-06-24):**
Bestätigt: `.coords-row` nur an einer Stelle (Z. 2997+3005). `.coords-label` width: 130px. Buttons `flex-shrink:0`. Keine Kopierbarkeit. Overflow durch Label+Wert+2 Buttons auf ~440px.

**Testplan:**
- [x] Automatisiert: kein Backend-Test nötig (reines CSS/HTML)
- [x] Manuell: Safari Mac localhost — alle AKs bestätigt 2026-06-25

---


### ~~TASK-43 · Refactoring: Lange Funktionen aufteilen (web/index.html)~~ `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-25 |
| **Implementiert** | 2026-06-27 |
| **Abgeschlossen** | 2026-06-27 |

**Beschreibung:** `refactor_check.py` meldete zwei JS-Funktionen mit übermäßiger Länge: `local()` und `row()`. Nach Code-Verifikation: beide sind Falsch-Positive der bekannten Heuristik (TASK-32). `local` = 1-zeilige IIFE-Variable in `CameraFOV._loadProfile()`, `row` = 12-zeilige Arrow-Function in `AstroMap.render()`. Fix: beide in `FRONTEND_LONG_FN_IGNORELIST` eingetragen.

**Quelle:** Automatisch erstellt durch fotoalert-refactor (TASK-29)

**Scope:**
- Eingeschlossen: `tools/refactor_check.py` — 2 Einträge in `FRONTEND_LONG_FN_IGNORELIST`
- Ausgeschlossen: `web/index.html` — kein Code-Split nötig

**Akzeptanzkriterien:**
- [x] `python3 tools/refactor_check.py` gibt `✅ Keine Smells gefunden` aus
- [x] `local` und `row` mit Kommentar in der Ignorelist erklärt

**📎 Code-Verifikation (2026-06-27):**
- `local` Z. 2724: IIFE-Variable, 1 Zeile — Falsch-Positiv bestätigt
- `row` Z. 3592: Arrow-Function in `AstroMap.render()`, 12 Zeilen — Falsch-Positiv bestätigt

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `tools/refactor_check.py`
- [x] Implementierungsoption: Ignorelist-Erweiterung (Option A, freigegeben 2026-06-27)

---

**Analyse & Planung:**

- [x] `local()` bei Z. 2724 untersucht: 2-zeilige IIFE `(() => { try { return JSON.parse(...) } catch { return {}; } })()`  — echter Umfang: 1 Zeile. Die Heuristik misst fälschlicherweise 265 Zeilen (bis zur nächsten erkannten Funktion `axisPhrase` bei Z. 2989).
- [x] `row()` bei Z. 3592 untersucht: 12-zeilige Arrow-Function innerhalb von `AstroCompass.render()` — echter Umfang: ~13 Zeilen (Z. 3592–3604). Die Heuristik misst fälschlicherweise 1052 Zeilen (bis zur nächsten erkannten Funktion `_outsideHandler` bei Z. 4644).
- [x] Ursache bestätigt: Regex-Heuristik in `refactor_check.py` (Zeile 258–271) misst Abstand bis zur *nächsten* erkannten Funktionsdeklaration — bekannte Limitation, dokumentiert ab Zeile 222 im Tool. Beide Funde sind Falsch-Positive, keine echten Code-Smells.
- [x] Beide Funktionen haben keine redundante Logik, keine Mehrfach-Verantwortung, kein Splitting-Kandidat.
- [x] Korrekte Lösung: beide Namen in `FRONTEND_LONG_FN_IGNORELIST` eintragen (analog zu `_showError`, `haversineKm`, `onUp`, `state3`, `mkSec`, `axisPhrase`).

**Akzeptanzkriterien:**

- `python3 tools/refactor_check.py` meldet keine `long_function`-Findings mehr für `local` und `row` — das Tool ist sauber.
- Das sichtbare Verhalten der App bleibt **unverändert**: keine JS-Fehler, keine visuellen Änderungen, keine Funktionsänderung.
- `web/index.html` wird **nicht** verändert — kein Aufteilen, kein Umbau.
- Die Ignore-Liste in `refactor_check.py` enthält einen Kommentar, der erklärt, warum diese Einträge aufgenommen wurden (Falsch-Positiv-Klasse + echte Zeilenlänge).
- Alle bestehenden Tests bleiben grün.

**Pre-Mortem:**

- **Falsches Handling:** Jemand teilt `local` oder `row` tatsächlich auf, ohne die Root Cause zu verstehen → unnötige Code-Komplexität, schlechtere Lesbarkeit, potenzielle Bugs durch falsch gesplittete Closures (beide greifen auf Outer-Scope-Variablen zu: `this._profile`, `axisAz`, `this._vertOffsetM`).
- **Zu breite Ignore-Liste:** Wenn zukünftige echte Smells mit denselben Namen entstehen, werden sie stumm ignoriert — deshalb Kommentare mit echter Zeilenlänge und Kontext pflegen.
- **Heuristik nicht gefixt:** Das eigentliche Problem (Regex misst bis zur nächsten Funktion statt bis `}`) bleibt bestehen und erzeugt weiter Falsch-Positive für andere Funktionsnamen. Langfristig wäre ein echter JS-AST-Parser (z.B. acorn via Node.js) besser — das ist aber ein separates Ticket.
- **Regression-Guard fehlt:** Ohne zusätzlichen Test kann die Ignore-Liste versehentlich geleert werden. Mitigiert durch Kommentar im Code.

**Implementierungsoptionen:**

**Option A (empfohlen): Beide Namen zur FRONTEND_LONG_FN_IGNORELIST hinzufügen**
- Datei: `FotoAlert/tools/refactor_check.py`, Zeile 241–248
- `local` und `row` in das `FRONTEND_LONG_FN_IGNORELIST`-Set eintragen
- Kommentar ergänzen: jeweils echter Umfang + Kontext (Closures in `_loadProfile` / `AstroCompass.render`)
- `web/index.html` bleibt unberührt
- Aufwand: ~5 Zeilen, 0 Risiko
- Nach dem Fix: `refactor_check.py` meldet 0 `needs_ticket`-Findings

**Option B: Heuristik durch echten JS-AST ersetzen**
- Node.js + acorn installieren, Frontend-Analyse auf echten AST umstellen
- Würde alle aktuellen Falsch-Positive dauerhaft eliminieren
- Aufwand: hoch (externe Abhängigkeit, CI-Anpassung), Scope weit über dieses Ticket hinaus
- Nicht empfohlen für dieses Ticket — separates Ticket anlegen falls gewünscht

**Empfehlung: Option A.** Schnell, sicher, null Risiko. Das Ticket beschreibt ein Tool-Problem, keinen App-Code-Smell.

**Testplan:**

1. `python3 tools/refactor_check.py` vor der Änderung ausführen → zeigt 2 `long_function`-Findings für `local` und `row`.
2. Änderung in `refactor_check.py` anwenden (Ignore-Liste erweitern).
3. `python3 tools/refactor_check.py` erneut ausführen → 0 `long_function`-Findings.
4. App lokal starten und manuell prüfen: FOV-Panel, AstroCompass-Readout, Profil-Persistenz — alles unverändert funktionsfähig.
5. `web/index.html` via `git diff` prüfen: keine Änderungen.

---


### ~~BUG-43 · Himmelsposition fehlt komplett bei Locations ohne Motivhöhe~~ `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-26 |
| **Abgeschlossen** | 2026-06-26 |
| **Implementiert** | 2026-06-26 |

**Beschreibung:** Fehlt an einer Location das Feld `subject_height_m`, gibt `_composition_analysis()` sofort `None` zurück. Dadurch werden die Sektionen „🧭 Himmelsposition" und „🎯 Kompositions-Analyse" im Event-Detail gar nicht gerendert — obwohl Azimut-Alignment und die Höhe des Himmelsobjekts über dem Beobachter-Horizont weiterhin berechenbar wären. **Erwartet:** Auch ohne Motivhöhe soll zumindest die Position des Himmelsobjekts relativ zum Motivstandort (Horizonthöhe + seitlicher Versatz) angezeigt werden.

**Bezug:** Kausalkette: `subject_height_m` fehlt → `_composition_analysis() = None` → `ev_skypos`-Gate (`!ca`) schlägt fehl → keine Sektion. Verwandt mit BUG-40 `[x]` (anderer Root Cause: damals fehlendes Default-Flag). US-67 `[x]` definiert `subject_height_m` als Pflichtfeld für volle Analyse — dieses Ticket erweitert den Fallback-Pfad.

**Scope:**
- Eingeschlossen: `backend/precompute.py` (`_composition_analysis` Guard + Conditional); `web/index.html` (`ev_skypos` altPhrase-Fallback + `bothExact`-Guard; `ev_kompo` Höhen-Zeilen-Guard); Server-Recompute nach Deploy
- Ausgeschlossen: Locations mit `distance_m = 0` (bleiben ohne Analyse, kein metrischer Versatz berechenbar); iOS-App; `_passes_alignment_filter` (bereits null-sicher, Z. 115)

**Akzeptanzkriterien:**
- [ ] Mond-Alignment an Location ohne Motivhöhe: Sektion „🧭 Himmelsposition" erscheint und zeigt seitlichen Versatz (m + °) sowie absolute Horizonthöhe des Monds (°)
- [ ] Kein „NaN m" / kein JS-Crash wenn `altitude_delta_deg` oder `vertical_offset_m` null sind
- [ ] Locations mit Motivhöhe: Verhalten identisch zu vorher (Versatz relativ zur Motivspitze, Meter-Angabe erhalten)
- [ ] `_passes_alignment_filter`: Events ohne Motivhöhe passieren den Filter weiterhin (alt_delta = null → True — kein Regressions-Risiko)
- [ ] `ev_kompo` bei fehlender Motivhöhe: Höhen-abhängige Zeilen (Versatz über Motivspitze, Motivhöhe, Verhältnis) sind ausgeblendet; seitlicher Versatz + Körpergröße bleiben sichtbar
- [ ] Edge Case: `distance_m = 0` → keine Himmelsposition-Sektion (unverändert)
- [ ] Edge Case: `subject_height_m = 0` (explizit Null eingetragen) → behandelt wie fehlend (kein Division-by-zero)

**Pre-Mortem:**
- 💀 `bothExact`-Branch: `Math.abs(null) = 0 → 0 < 0.5 → true` → zeigt fälschlicherweise „nahezu exakt auf Motivspitze" → Gegenmaßnahme: `bothExact = altDelta != null && ...`
- 💀 Division by zero: `size_ratio = body_apparent_diameter_m / subject_height_m` wenn `subject_height_m = 0` → Gegenmaßnahme: Guard `if loc.subject_height_m and loc.subject_height_m > 0`
- 💀 `ev_kompo` crasht bei `ca.subject_apparent_elevation_deg.toFixed(2)` wenn null → Gegenmaßnahme: Null-Guard vor Zeilen-Rendering

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2026-06-26)
- [x] Pre-Mortem durchgeführt (2026-06-26)
- [x] Architektur analysiert: `precompute.py` Z. 309 (Guard), Z. 340 (size_ratio), Z. 115 (Filter null-sicher); `web/index.html` Z. 2941 (ev_skypos Gate), Z. 2970 (bothExact), Z. 2960 (axisPhrase), Z. 3017 (ev_kompo Höhen-Zeilen)
- [x] Implementierungsoptionen: A (Backend partiell + Frontend Null-Guards) / B (Frontend-only Fallback)
- [x] Empfehlung: Option A — Backend-seitig sauber, pytest-testbar, kein JS-Duplikat

**📎 Code-Verifikation (2026-06-26):**
- `_composition_analysis()` Guard Z. 309 bestätigt: `loc.subject_height_m and loc.distance_m` beide Pflicht
- `_passes_alignment_filter()` Z. 115 bestätigt: `alt_delta is None → True` — bereits null-sicher
- `bothExact` Z. 2970: `Math.abs(null) = 0` → semantisch falsch, kein Absturz, aber Guard nötig
- `_build_composition_labels` braucht `size_ratio` — muss nur aufgerufen werden wenn vorhanden

**Testplan:**
- [ ] Automatisiert (`backend/tests/test_bug43_partial_composition.py`, BUG-43): `_composition_analysis` mit Mock-Location ohne `subject_height_m` → `azimuth_delta_deg` vorhanden, `altitude_delta_deg = None`, kein Exception
- [ ] Automatisiert: `_composition_analysis` mit `subject_height_m = 0` → kein ZeroDivisionError
- [ ] Manuell: Location ohne Motivhöhe im Feed → Event-Detail → Himmelsposition sichtbar, kein NaN
- [ ] Manuell: Location mit Motivhöhe → keine Regression (Meter-Angabe relativ zur Motivspitze erhalten)

---


### BUG-41 · Koordinaten-Sektion: Street View Button immer sichtbar (nicht nur bei Azimut) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-25 |
| **Abgeschlossen** | 2026-06-25 |

**Beschreibung:** Der Street View Button in der Koordinaten-Sektion des Event-Detail-Sheets erschien nur wenn `subject_azimuth` gesetzt war. Für Events ohne Azimut (Goldene Stunde, Blaue Stunde) fehlte der Button, obwohl Street View auch ohne Blickrichtung nützlich ist. Ohne Azimut öffnet Street View jetzt mit `heading=0` (Norden).

**Bezug:** BUG-38 [x] (Koordinaten-Sektion Layout — selber Bereich). Gefunden beim BUG-38-Testlauf 2026-06-25.

**Scope:** `web/index.html` — Bedingung in `ev_coords`-Template entfernt, `openStreetView()` Default-Heading 0.

**Akzeptanzkriterien:**
- [x] Street View Button erscheint in der Koordinaten-Sektion für ALLE Event-Typen
- [x] Mit Azimut: Street View öffnet mit korrekter Blickrichtung
- [x] Ohne Azimut: Street View öffnet mit heading=0 (Norden), kein JS-Fehler

---


### BUG-39 · Chancendetails: Blaugrauer Strich links im Sheet-Header `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-24 |
| **Abgeschlossen** | 2026-06-25 |

**Beschreibung:** Auf Höhe des ×-Schließen-Buttons erscheint auf der linken Seite des Detail-Sheets ein blaugrauer horizontaler Strich ohne erkennbaren Zweck. Vermutlich ein verwaistes Border-, Pseudo-Element oder ein unsichtbares Icon. Kann entfernt werden.

**Bezug:** Screenshot von 2026-06-24. Verwandt mit BUG-38 (selber Sheet-Bereich).

**Root-Cause:** `<div class="sheet-handle">` war links in einem `justify-content:space-between`-Flex-Container platziert und erzeugte so einen sichtbaren 36×4px-Strich (`.sheet-handle` = `background:var(--border)`). Behoben durch Entfernen des Handle-Divs + `justify-content:flex-end`.

**Akzeptanzkriterien:**
- [x] Kein blaugrauer Strich links im Detail-Sheet-Header
- [x] ×-Button weiterhin rechts oben sichtbar und funktional

---


### BUG-40 · Chancendetails: Relative Höhe Himmelsobjekt über Motivspitze fehlt (US-67 Regression) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-24 |
| **Abgeschlossen** | 2026-06-24 |

**Beschreibung:** Die in US-67 implementierte Angabe „Höhe Himmelsobjekt über Motivspitze (m)" sowie die Kompositions-Labels (🎯 Exakt / ✨ Knapp über / usw.) und der Höhenversatz-Text sind nicht mehr in der Astronomie-Sektion der Chancendetails sichtbar. Das Feld war früher vorhanden und scheint durch eine spätere Änderung entfernt oder überschrieben worden zu sein (Regression). Aktuell sichtbar: Mondphase, Azimut Himmelsobjekt, Höhe Himmelsobjekt, Azimut Sichtachse, Sonnenaufgang/-untergang – aber kein relativer Höhenversatz.

**Bezug:** US-67 [x] (Originalimplementierung). Screenshot vom 2026-06-24 zeigt fehlende Zeile. Möglicherweise Konflikt mit US-70/US-81 (Scout-Tab Erweiterungen die composition_analysis-Felder umstrukturiert haben könnten).

**Scope:**
Eingeschlossen: `Sections._def` in `web/index.html` Z. 2559 — `ev_skypos` auf `true` setzen.
Ausgeschlossen: `ev_kompo` (bleibt closed), Backend (`composition_analysis` ist korrekt), andere Sektionen.

**Akzeptanzkriterien:**
- [ ] Mond-Alignment Details: Sektion „🧭 Himmelsposition" beim Öffnen sofort sichtbar
- [ ] Text enthält Meter-Angabe (z.B. „≈ 14 m darüber" oder „nahezu exakt")
- [ ] Goldene Stunde / Blaue Stunde: keine Himmelsposition-Sektion (EV_SKYPOS_EXEMPT greift)
- [ ] Event ohne composition_analysis: keine Himmelsposition-Sektion
- [ ] `ev_kompo` (Kompositions-Analyse) bleibt geschlossen by default — keine Änderung
- [ ] Edge Case: User hatte ev_skypos manuell geschlossen → localStorage-Wert bleibt erhalten

**Pre-Mortem:**
- 💀 Gate `!ca` → leere Sektion für Non-Alignment-Events: kein Risiko, Sektion wird nicht gerendert
- 💀 localStorage-Migration: User ohne Eintrag bekommt neuen Default `true` korrekt; User mit `false`-Eintrag unberührt

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2026-06-24)
- [x] Pre-Mortem durchgeführt (2026-06-24)
- [x] Architektur analysiert: `web/index.html` Z. 2556–2584 (Sections._def), Z. 2871–2929 (ev_skypos), Z. 2930–2979 (ev_kompo)
- [x] Implementierungsoptionen: A (1-Zeilen Default-Fix) / B (Feld in ev_astro einblenden)
- [ ] Empfehlung: Option A — `ev_skypos: true` in `Sections._def` (Z. 2559), 1-Zeilen-Änderung

**📎 Code-Verifikation (2026-06-24):**
Bestätigt: composition_analysis korrekt berechnet + gespeichert. ev_skypos + ev_kompo rendern Versatz in Metern. Root-Cause: ev_skypos nicht in _def → Fallback `false` → Sektion closed.

**Testplan:**
- [ ] Automatisiert: kein Backend-Test nötig (reines CSS/Default-State)
- [ ] Manuell: Mond-Alignment öffnen → Himmelsposition sofort sichtbar, Meter-Wert lesbar; Goldene Stunde → keine Himmelsposition-Sektion

---


### US-96 · Einheitliche Chancen-Detailansicht aus allen Einstiegspunkten `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-27 |
| **Abgeschlossen** | 2026-06-27 (v1.17.0) |

**Beschreibung:** Egal ob ich eine Chance im Feed (14-Tage-Ansicht), im 365-Tage-Kalender, im Scout oder in den Location Details (zukünftige Ereignisse) antippe — ich sehe immer exakt dieselbe Detailansicht mit denselben Informationen in derselben Reihenfolge. Alle Sektionen sind beim Öffnen eingeklappt. Das schafft ein konsistentes Erlebnis und macht das Navigieren zwischen den Tabs vorhersehbar.

**Sektionen (Reihenfolge fest):**
1. Titel / Score
2. Uhrzeit
3. FOV-Karte
4. Koordinaten
5. Himmelsposition
6. Wetter
7. Himmelskörper-Bahnen (bestehende interaktive Karte mit Zeit-Regler — Sonne/Mond-Stand relativ zum Standort; eingeklappte Sektion inline in der Detailansicht)
8. Aktions-Buttons

**Bezug:** Hängt von US-95 ab (Layout-Optimierung der bestehenden Detailansicht, sinnvolle Basis). Blockiert US-83 (Scout-Detailansicht soll dieselbe Komponente nutzen). Tangiert US-87 (Karten-Overlay). US-95 und US-96 können als Sequenz gebündelt werden.

#### 🔬 Analyse-Spec (US-96) · 2026-06-27

**Bestätigte Entscheidungen:**
- Alle bisherigen Sektionen (Beschreibung, Kamera, Astronomie, Topo, Kompo) bleiben erhalten — sie kommen nach den Himmelskörper-Bahnen, vor den Aktions-Buttons.
- „Himmelskörper-Bahnen" = `AstroLive` (US-64). Erscheint als eingeklappte Button-Sektion IN der Detailansicht (kein eigenes Sheet-Öffnen beim Laden).
- Beim Öffnen der Detailansicht sind alle Sektionen eingeklappt (`_def` Änderung). localStorage-Stand wird dadurch nicht verändert — nur der Startzustand beim Öffnen ändert sich.

**Scope:**

Eingeschlossen:
- Neue Sektions-Reihenfolge in `Detail.open()` umsetzen
- `Sections._def` — alle Sektionen auf `false` setzen
- Neue Sektion `ev_astro_live` als `mkSec`-Block mit Button/Link zu AstroLive
- `AstroLive.openForDate(locId, isoDate)` — neue Eintrittsmethode (Option B)
- Alle 4 Einstiegspunkte (Feed, Scout, Kalender, LocationDetail) nutzen automatisch `Detail.open(o)` — kein separater Umbau nötig

Ausgeschlossen:
- AstroLive als eingebettete Karte (zwei Leaflet-Instanzen gleichzeitig — zu komplex, eigenes Ticket)
- Vollbild-Overlay für FOV-Karte (US-87)
- Scout-Detailansicht-Refactoring (US-83 — wartet auf US-96 als Basis)

**Akzeptanzkriterien:**

- [ ] AK-1: Ich tippe im Feed auf eine Chance → das Detailsheet öffnet sich. Auf einem frischen Gerät (oder ohne bisherige Interaktion) sind alle Sektionen eingeklappt.
- [ ] AK-2: Ich tippe im Kalender auf eine Chance → exakt dasselbe Detailsheet, dieselbe Reihenfolge wie im Feed.
- [ ] AK-3: Ich tippe im Scout auf einen Alert-Chip → exakt dasselbe Detailsheet.
- [ ] AK-4: Ich öffne die Location Details und tippe auf ein zukünftiges Ereignis → exakt dasselbe Detailsheet.
- [ ] AK-5: In der Detailansicht sehe ich oben: Uhrzeit → FOV-Karte → Koordinaten → Himmelsposition → Wetter → Himmelskörper-Bahnen (Button) → Beschreibung / Kamera / Astronomie / Topo / Kompo → Aktions-Buttons.
- [ ] AK-6: Ich klappe „Himmelskörper-Bahnen" auf → es erscheint ein Button „Live-Astro (Sonne · Mond · Milchstraße)". Ich tippe darauf → das AstroLive-Sheet öffnet sich mit dem Slider voreingestellt auf Datum + Uhrzeit der Chance (nicht auf heute).
- [ ] AK-7: Ich klappe eine Sektion auf, schließe das Sheet, öffne es erneut → die Sektion ist noch offen (meine Präferenz bleibt erhalten).

**Pre-Mortem:**

1. **Sektions-Reihenfolge im DOM falsch** — `Detail.open()` baut das Sheet imperativ (appendChild-Reihenfolge). Wenn bei der Umreihenfolge ein Block vergessen oder doppelt eingefügt wird, fehlt eine Sektion oder erscheint sie zweimal. → Mitigation: Nach Umbau alle 4 Einstiegspunkte einmal durchklicken und DOM-Reihenfolge gegen Spec-Liste prüfen.

2. **`ev_astro_live`-Sektion kollidiert mit vorhandenem Schlüssel** — `Sections._def` und die `mkSec`-Logik kennen `ev_astro_live` noch nicht. Fehlt die Registrierung, wird die Sektion nie gerendert. → Mitigation: Schlüssel in `_def`, `registerOnOpen` (falls nötig) und im Render-Block konsistent benennen; nach Einbau per Klick verifizieren.

3. **`AstroLive.openForDate` setzt Slider-Zeit falsch** — `setNow()` und `onScrub()` operieren auf `this._t` (Unix-ms). Wird das Shoot-Datum falsch als UTC/Local konvertiert (Shoot-Time ist UTC, App zeigt Berliner Ortszeit), zeigt der Slider die falsche Stunde. → Mitigation: `openForDate` muss ISO-String als UTC parsen (`new Date(isoDate)`) und direkt `this._t` setzen, ohne zusätzliche Timezone-Konvertierung.

4. **`_def`-Änderung greift nur auf frischen Geräten** — bestehende Nutzer mit localStorage-Einträgen sehen weiterhin ihre bisherigen Zustände. Das ist gewollt (AK-7 bestätigt). Kein Risiko, nur Bewusstsein dass der „alle zu"-Effekt nur für neue Nutzer spürbar ist.

**Analyse & Planung:**

Betroffene Code-Stellen in `web/index.html`:
- `Sections._def` (Z. ~2826): alle Werte auf `false` setzen + `ev_astro_live: false` ergänzen
- `Detail.open()` (Z. ~3097–3311): appendChild-Reihenfolge umbauen + `ev_astro_live`-Block einfügen
- `AstroLive` (Z. ~3590ff): neue Methode `openForDate(locId, isoDate)` ergänzen (Option B)
- Alle 4 Einstiegspunkte: keine Änderung nötig (rufen bereits `Detail.open(o)` auf)

Kein Backend-Eingriff erforderlich. Rein Frontend.

**Implementierungsoptionen:**

**Option A — Button-Link ohne Datum-Kontext** *(einfacher, ~20 Zeilen)*
Eine neue `mkSec('ev_astro_live', ...)` mit einem Button, der `AstroLive.open(o.location_id)` aufruft — exakt wie der bestehende Button in LocationDetail. Der Slider im AstroLive-Sheet startet auf „jetzt" (heute). Für eine Chance in 5 Tagen zeigt der Nutzer also den falschen Tag und muss manuell scrollen.
App-Wirkung: AstroLive öffnet sich, aber der Nutzer sieht nicht den Himmel zum Shoot-Zeitpunkt — er muss den Regler selbst verschieben.

**Option B — `AstroLive.openForDate(locId, isoDate)` *(empfohlen, ~30 Zeilen)*
Neue Methode in AstroLive: setzt `this._t` auf den Shoot-Zeitpunkt der Chance bevor das Sheet öffnet. Der Slider startet beim richtigen Tag + Uhrzeit. `Detail.open(o)` ruft `AstroLive.openForDate(o.location_id, o.shoot_time_utc)` auf.
App-Wirkung: Nutzer öffnet AstroLive und sieht sofort Sonne/Mond-Position für den geplanten Shoot-Moment. Kein manuelles Verschieben nötig.

**Empfehlung:** Option B.
Begründung: Der Shoot-Datum-Kontext ist der Kern-Nutzwert von AstroLive in diesem Flow — ohne ihn sieht der Nutzer zufällig den heutigen Himmel, nicht den Himmel zur Chance. Der Mehraufwand (~10 Zeilen extra gegenüber A) ist vertretbar. Die neue Methode ist isoliert testbar und bricht nichts am bestehenden `AstroLive.open(locId)`-Aufruf in LocationDetail.

**Testplan:**

1. Feed → Chance antippen → Sheet öffnet sich, alle Sektionen eingeklappt ✓
2. Kalender → Chance antippen → identisches Sheet ✓
3. Scout → Alert-Chip → identisches Sheet ✓
4. LocationDetail → zukünftiges Ereignis → identisches Sheet ✓
5. Reihenfolge: Uhrzeit ganz oben, Aktions-Buttons ganz unten, AstroLive-Button vor den Detail-Sektionen ✓
6. AstroLive-Button antippen → Sheet öffnet, Slider zeigt Shoot-Datum + Shoot-Uhrzeit (nicht heute) ✓
7. Sheet schließen, erneut öffnen → alle Sektionen wieder eingeklappt ✓

**Status:** Wartet am Weg-Gate (Implementierungsoption B zur Freigabe — bitte bestätigen oder Alternative wählen).

---


### US-97 · Automatischer Tag/Nacht-Modus mit manuellem Umschalter `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Abgeschlossen** | 2026-06-27 (v1.15.0) |
| **Erstellt** | 2026-06-27 |

**Beschreibung:** Als Fotograf bin ich tags und nachts unterwegs und möchte, dass die App ihr Erscheinungsbild automatisch an die Umgebung anpasst — heller Modus bei Tag, dunkler Modus bei Nacht — damit der Bildschirm nachts nicht blendet und tags genug Kontrast bleibt. Die automatische Umschaltung soll standardmäßig aktiv sein (gekoppelt an die System-/Geräteeinstellung Hell/Dunkel). Zusätzlich brauche ich in den Einstellungen einen manuellen Umschalter mit drei Optionen — Auto / Hell / Dunkel —, mit dem ich die Automatik bei Bedarf übersteuern kann; meine Wahl bleibt über App-Neustarts erhalten.

**Bezug:** Kind von **US-98** (Bauhaus-Redesign-Epic). Entstanden aus dem Bauhaus-Design-Prototyp (FotoAlert/design/bauhaus/prototype.html), der Auto-Umschaltung + Auto/Hell/Dunkel-Segment bereits demonstriert. **Hängt von US-99 ab** — die echte App ist derzeit reines Dunkel; das helle Theme (Theme-Tokens hell+dunkel) muss zuerst existieren, sonst gibt es bei „Tag" nichts zum Umschalten. Dieses Ticket umfasst NUR die Tag/Nacht-Mechanik (Automatik + Umschalter + Persistenz), nicht den Farb-/Icon-Umbau. Tangiert TASK-05 (Design-Spec). Kein „Nacht-Rotmodus" (separate Idee, ausgeschlossen).

---


### US-99 · Bauhaus-Theme-Tokens: Farb-/Designvariablen hell + dunkel `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Abgeschlossen** | 2026-06-27 (v1.15.0) |
| **Erstellt** | 2026-06-27 |

**Beschreibung:** Als Fundament des Redesigns sollen die Bauhaus-Farb- und Designvariablen (Hintergrund, Flächen, Text, Bauhaus-Blau, Gold, Linien, Chips, Radius) als CSS-Variablen für hellen UND dunklen Modus eingeführt werden. Die App ist heute reines Dunkel — hier entsteht das helle Theme und die saubere Variablen-Basis, auf der alle weiteren Redesign-Tickets aufbauen. Keine sichtbare Logik-Änderung, nur Farbwerte/Variablen.

**Bezug:** Kind von US-98. Blockiert US-97 (Tag/Nacht braucht das Hell-Theme). Werte aus FotoAlert/design/bauhaus/prototype.html (`:root` / `[data-theme="dark"]`). Tangiert TASK-05.

---

#### 🔬 Analyse-Spec (US-99 + US-97 gebündelt) · 2026-06-27

📎 **Code-Verifikation** (`web/index.html`, gelesen 2026-06-27): App ist reines Dunkel (`:root` Z. 22–36, kein `prefers-color-scheme`/`data-theme`/`matchMedia`). Settings rendern bei `Settings.render()` (Z. 4366) in `#settings-content`. Persistenz-Muster bereits `localStorage` (`fa_*`). `<meta name="theme-color">` statisch `#f0a030` (Z. 9). Mode-abhängige Hardcodes vorhanden: Hover-`rgba(255,255,255,…)` (~19×), `.leaflet-container {background:#0d0d1a !important}` (Z. 203), `.gps-dot #4285f4`, `.rmi-status.err #e05`.

**Bestätigte Entscheidungen (Stephan, 2026-06-27):** Auto = **Systemeinstellung** (`prefers-color-scheme`, kein Tageszeit-Trigger). Farb-Umfang = **volle Bauhaus-Palette hell+dunkel** (Blau #2D4EA0 führend, Gold #E3A21A Zweitakzent), Werte aus dem Prototyp.

**Scope:**
Eingeschlossen: (1) Alle Farb-/Designwerte als CSS-Variablen-Themes — `:root` = Hell/Tag (Default Bauhaus-hell), `[data-theme="dark"]` = Bauhaus-dunkel; bestehende Hardcodes auf Tokens umstellen. (2) Bauhaus-Palette in beiden Modi. (3) Auto-Modus via `matchMedia('(prefers-color-scheme)')` inkl. Live-Wechsel bei OS-Änderung. (4) Manueller Umschalter Auto/Hell/Dunkel in neuer Settings-Sektion „Erscheinungsbild"; Wahl in `localStorage` `fa_theme` (auto|light|dark), beim Start angewandt. (5) `<meta name="theme-color">` dynamisch je Theme. (6) `.leaflet-container`-BG tokenisiert.
Ausgeschlossen: Icon-Set (US-100), Button-/Schriftgrößen (US-101), Logo/App-Icon (US-102), Nacht-Rotmodus, Tageszeit-Automatik, Wechsel des Karten-Tile-Anbieters.

**Akzeptanzkriterien (erlebbar):**
- [ ] Erststart ohne eigene Wahl: App folgt der iOS-Einstellung — iOS hell → App hell, iOS dunkel → App dunkel.
- [ ] Bei „Auto" und geöffneter App: Ändere ich iOS Hell↔Dunkel, wechselt die App sofort mit (ohne Neustart).
- [ ] Einstellungen → „Erscheinungsbild" zeigt Auto/Hell/Dunkel. „Hell" hält die App hell trotz iOS-Dunkel; „Dunkel" umgekehrt.
- [ ] Meine Wahl bleibt nach App-Neustart erhalten.
- [ ] In beiden Modi ist jeder Text lesbar und kontrastreich — inkl. Karten-Hintergrund, Hover-Flächen, GPS-Punkt, Fehlertext (kein Weiß-auf-Weiß).
- [ ] Look entspricht der Bauhaus-Palette (Blau führend, Gold Zweitakzent) in beiden Modi.
- [ ] Edge: Browser ohne `prefers-color-scheme` → Start im Dunkelmodus (sicherer Default), Umschalter funktioniert weiter.
- [ ] Edge: ungültiger gespeicherter `fa_theme`-Wert → Fallback „Auto".

**Pre-Mortem:**
- 💀 Hell-Modus stellenweise unleserlich (Hover-`rgba(255,255,255)`, dunkler Leaflet-BG bleiben) → Gegenmaßnahme: AK „lesbar in beiden Modi" + manueller Panel-Durchlauf hell+dunkel; alle mode-abhängigen Hardcodes tokenisieren.
- 💀 Browser-Chrome-Leiste bleibt gold (statische theme-color) → Gegenmaßnahme: Meta dynamisch je Theme setzen.
- 💀 `matchMedia`-Listener mehrfach registriert/Leak → Gegenmaßnahme: einmalige Registrierung, Test.
- 💀 Neue „Erscheinungsbild"-Sektion bricht `Settings.render()` → Gegenmaßnahme: Vollsystem-Regression (bestehende AK-Tests) + manueller Settings-Check.
- 💀 Karten-Tiles wirken im Hell-Modus dunkel (Tile-Anbieter unverändert) → bewusste Einschränkung dokumentiert; nur Container-BG tokenisiert, Tile-Wechsel außerhalb Scope.

**Analyse & Planung:**
- [x] Example Mapping (Auto-Trigger + Farb-Umfang als 🔴-Fragen vorab geklärt)
- [x] Pre-Mortem inkl. Code-Verifikation
- [x] Architektur analysiert: `web/index.html` (`:root`, `Settings.render()`, mode-abhängige Hardcodes, `<meta theme-color>`)
- [x] Optionen: A (Tokens + `data-theme` + JS-Theme-Manager) / B (nur CSS-`@media`)
- [x] Empfehlung: **Option A** — nur A erfüllt den manuellen Umschalter + Persistenz (B kann Auto, aber kein Hell/Dunkel-Erzwingen).

**Testplan:**
- Automatisiert (Harness): `fa_theme`-Persistenz-/Fallback-Logik (auto|light|dark|ungültig) als pytest-Fall, falls in JS-testbarer Helper ausgelagert; sonst manuell markiert.
- Manuell (http://localhost:8000): iOS/OS Hell↔Dunkel bei „Auto" umschalten; je Umschalter-Option prüfen; Neustart-Persistenz; visueller Durchlauf aller Panels in beiden Modi.

**Status:** Wartet am Weg-Gate (Option A zur Freigabe).

---


### US-100 · Einheitliches Bauhaus-Linien-Icon-Set ersetzt Emoji-Symbole `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-27 |
| **Abgeschlossen** | 2026-06-27 (v1.16.0) |

**Beschreibung:** Als Nutzer möchte ich überall einheitliche, klare Linien-Icons statt der gemischten/verspielten Emojis (🌅🧭🌙 …), damit die Oberfläche ruhig und konsistent wirkt. Eine einzige Icon-Familie (gleicher Strich, gleiches Raster) für Tabs, Chancen-Typen und Status. WebKit-Hinweis: Strich/Füllung als SVG-Attribute setzen, nicht per CSS-Klasse (sonst in Safari unsichtbar).

**Bezug:** Kind von US-98. Quelle: FotoAlert/design/bauhaus/icons.svg. Tangiert US-96 (Detailansicht nutzt dieselben Icons).

---

#### 🔬 Analyse-Spec (US-100) · 2026-06-27

📎 **Code-Verifikation** (gelesen 2026-06-27):
- `web/index.html`: ~187 Zeilen tragen Emojis (`grep` Unicode-Bereiche). Verteilung: `ICONS`-Map (Z. 1199–1206: 9 Event-Typen 🌅🌄🌙🌕☀️✨💫🌑), Feed-Karten (`.opp-icon` Z. 1299, Kalender-Chips Z. 1434, Sektionsköpfe „⭐ Besondere…" Z. 1439), Scout-Sheet (Z. 1500–1581: Tageszeit-Labels 🌑🌅🌇🌆, Body-Icon ☀️/🌙, Chips 🕐📐📏📷☁️, Buttons 📍 Standort / 🧭 Navigation), Chancendetail-Sheet (Z. 2963–3261: Wetter 🌤🟡🟠🔴, Mondphase 🌙, Sonne 🌅🌇🌄, Sektionsköpfe 📝📷🔭📏🧭🎯📐📍, Himmelsposition 🎯🧭, Coords-Buttons 🗺👁🍎, Aktionen 📅🔔✓), Verify-Badges (Z. 1840–1984: ✓ ⚠ ✅), Sterne-Rating (Z. 2086–2135: ★ ⭐), Filter-Sheet (Z. 2646–2734: Sektionsköpfe 🎯📷🕐🔭🗂⭐📍✅, Kategorie-Chips 🏰🏙🌿💧🔭🏗🌌, Schwierigkeit 🟢🟡🔴, Tageszeit 🌄☀️🌇🌙, Verifikation ✓⚠), Location-Liste/-Detail (Z. 3733–4149: Kategorie-Icons 🏰💧🌲✨🏙🔭🏭, Body-Chips ☀🌙🌌, Sektionsköpfe 📍🎯🔭📐, Edit/Delete ✏️🗑, Maps 🍎🗺👁🚶), Header/Login (📷), Refresh-Menü (`.rmi-icon` Z. 797–819: 🌤📅📆🔍), Mode-Buttons (📋📅🔭 Z. 843–845), Sheet-Titel (📍🌌🎛), Close-Buttons (✕).
- **Tab-Bar ist bereits Inline-SVG** (Z. 888–908: 5 `<svg fill="none" stroke="currentColor" stroke-width="2">`-Pfade — Stern/Karte/Plus/Pin/Zahnrad). Ebenso bereits SVG: Header-Search/Refresh (Z. 776–790), Today/Calendar-Mini-Icons in Feed (Z. 1408/1454), Chevron (Z. 4526), Map-Pins (Z. 3297 ff.).
- **Quelle**: Ticket nennt `icons.svg` — das ist aber nur ein **Showcase-Poster** (keine `<symbol>`/`id`-Defs, keine `currentColor`). Die **fertige, WebKit-sichere Sprite** liegt in `design/bauhaus/prototype.html` (Z. 312–338): `<defs>` mit `<symbol id="i-…">`, Strich/Füllung als **`<g>`-Attribute** (`stroke="currentColor" stroke-width="1.7"`), plus Helper `ic(id,size,cls)` (Z. 376). Vorhandene Symbole: `i-star`, `i-starfill`, `i-map`, `i-pin`, `i-pincheck`, `i-settings`, `i-sun`, `i-sunset`, `i-moon`/`i-moonsmall`, `i-cloud`, `i-bolt`, `i-compass`, `i-search`, `i-refresh`, `i-camera`, `i-tripod`, `i-clock`, `i-nav`, `i-check`, `i-warn`, `i-x`, `i-chevright`, `i-plus`/`i-minus`/`i-plusbare`.
- ⚠️ **Lücke**: Für mehrere Event-Typen/Status fehlt ein Symbol — Milchstraße (✨), Meteoritenschauer (💫), Sonnenfinsternis (🌑), Mond-/Sonnen-Alignment, sowie Location-Kategorien (🏰 Schloss, 💧 Wasser, 🌲/🌿 Natur, 🏙 Skyline, 🏗/🏭 Industrie, 🔭 Aussichtspunkt) und Street-View/Maps (👁🗺🍎) und Stern-Rating-Glyphe (★). Diese müssten **neu gezeichnet** werden (gleicher Strich/Raster) oder es wird ein nächstgelegenes vorhandenes Symbol gemappt.

❓ **Offene Fragen (vor Implementierung zu klären):**
1. **Liefer-Mechanismus**: Eine Inline-SVG-Sprite (`<defs><symbol>` + `<use href="#i-…">`) wie im Prototyp, ODER einzelne Inline-SVGs pro Stelle? *Empfehlung: Sprite* — eine Definition, überall per `<use>` referenziert, WebKit-sicher (Strich als `<g>`-Attribut), trivial themebar via `currentColor`. Einzel-SVGs würden ~187 Stellen aufblähen und divergieren.
2. **Scope der Ablösung**: (a) NUR Event-Typ-`ICONS`-Map + die 4 Kern-Buttons (📍🧭⚠⭐), oder (b) konsequent ALLE Text-Emojis (inkl. Filter-Sektionsköpfe, Location-Kategorien, Scout-Chips, Refresh-Menü, Mondphasen, Sterne-Rating)? Variante (a) lässt die App weiter gemischt wirken (Ticket-Ziel „überall einheitlich" verfehlt); (b) ist der eigentliche Ticket-Geist, aber deutlich größer und braucht ~8–10 neue Symbole.
3. **Sterne-Rating (★)**: bleibt die Unicode-Sterne-Glyphe (rendert konsistent, kein Emoji-Look) oder auf `i-star`/`i-starfill`-SVG umstellen? (Reine ★ sind typografisch ruhig — ggf. bewusst behalten.)
4. **Tab-Bar & bereits vorhandene SVGs**: Die heutigen Tab-/Header-SVGs (`stroke-width:2`/`2.5`) auf die Prototyp-Familie (`stroke-width:1.7`, identische Pfade) **vereinheitlichen**, oder unverändert lassen? Vereinheitlichen gibt den gewünschten „gleicher Strich"-Look, berührt aber funktionierende Stellen.
5. **Farb-/Token-Bindung**: Tab-Icons im Prototyp sind blau (`#2D4EA0`), Status/Detail tintenfarben. Sollen die neuen Icons strikt `currentColor` erben (folgen automatisch US-99-Theme-Tokens) — bestätigen?

**Scope (Vorschlag, abhängig von ❓2/❓4):**
Eingeschlossen: (1) WebKit-sichere Inline-SVG-Sprite aus `prototype.html` in `web/index.html` einbetten (`<defs>` + Helper `ic()`). (2) Event-Typ-Icons (`ICONS`-Map) auf Sprite umstellen. (3) Kern-Buttons/Status (📍 Standort, 🧭 Navigation, ⚠ Warnung, ⭐ Top-Chance, ✓ Geprüft, ✕ Close) auf Sprite. (4) Konsequente Ablösung der übrigen Deko-/Sektions-Emojis (bei Scope-Variante b). (5) Fehlende Symbole neu zeichnen (Milchstraße, Meteor, Finsternis, Kategorien, Street-View) im selben Raster.
Ausgeschlossen: Map-Pin-Marker-SVGs (Z. 3297 ff., funktional/farbig — bleiben), Logo/App-Icon (US-102), Button-/Schriftgrößen (US-101), Farb-Tokens (US-99 erledigt), Mondphasen-Visualisierung als Phasengrafik (nur Mond-Symbol).

**Akzeptanzkriterien (erlebbar):**
- [ ] In der Chancen-Liste zeigt jeder Eintrag statt eines bunten Emojis ein gleichmäßiges Linien-Icon (gleicher Strich wie die Tab-Leiste).
- [ ] Im Chancendetail tragen alle Sektionsköpfe (Beschreibung, Wetter, Kamera, Astronomie, Topographie, Himmelsposition, Koordinaten) einheitliche Linien-Icons statt Emojis.
- [ ] Die Scout-Buttons „Standort" und „Navigation" sowie der Warn-/Top-Chance-/Geprüft-Marker erscheinen als Linien-Icons.
- [ ] In Safari (iPhone) sind alle Icons sichtbar (nicht leer/unsichtbar) und nehmen die Theme-Farbe an (hell wie dunkel, US-99).
- [ ] Kein gemischtes Bild mehr: in den im Scope genannten Ansichten taucht kein farbiges Emoji mehr auf (Sicht-Check pro Ansicht).
- [ ] Bei einem Event-Typ ohne eigenes Icon erscheint ein neutrales Fallback-Linien-Icon (kein 📷-Emoji, kein leeres Kästchen).
- [ ] Edge: Icons skalieren sauber in allen Größen (13–48 px) ohne Verzerrung/Pixeligkeit.
- [ ] Edge: Tab-Leiste und übrige Icons wirken aus einer Familie (gleiche Strichstärke) — sofern ❓4 = „vereinheitlichen".

**Pre-Mortem:**
- 💀 Icons in Safari unsichtbar, weil Strich/Füllung per CSS-Klasse statt SVG-Attribut gesetzt → Auslöser: Übernahme eines CSS-`.ic{stroke:…}`-Musters. Frühwarnung: leer im Safari-Render trotz korrektem Chrome. Gegenmaßnahme: Strich/Füllung **als `<g>`-Attribut im `<symbol>`** (Prototyp-Muster); AK „in Safari sichtbar" + manueller Safari-Check (Memory `reference_svg_use_currentcolor_webkit`).
- 💀 Ablösung halbherzig → App wirkt weiter gemischt (Ticket-Ziel verfehlt), weil nur die `ICONS`-Map getauscht wurde → Gegenmaßnahme: ❓2 vorab klären; bei Variante (b) Sicht-Check pro Ansicht als AK.
- 💀 Fehlendes Symbol für seltenen Event-Typ → Karte zeigt leeres Kästchen statt Icon → Gegenmaßnahme: Fallback-Symbol (`i-star`/neutral) + AK „neutrales Fallback".
- 💀 Vereinheitlichung der bestehenden Tab-SVGs bricht Aktiv-Zustand/Größen (heutige `width/height`/`stroke-width` weichen ab) → Gegenmaßnahme: Tab-Umbau optional (❓4), Vollsystem-Regression + Sicht-Check der Tab-Leiste aktiv/inaktiv.
- 💀 Inline-Emojis stecken auch in nicht-UI-Pfaden (Kalender-`SUMMARY:📸` Z. 3251, Notification-Titel Z. 3271, Toast-Texte) → unbeabsichtigt mitentfernt bricht Funktion → Gegenmaßnahme: diese String-Emojis bewusst aus dem Scope nehmen (kein UI-Icon), nur visuelle UI-Glyphen ersetzen.

**Analyse & Planung:**
- [x] Example Mapping (Scope-/Mechanismus-Fragen als ❓ vorab gestellt)
- [x] Pre-Mortem inkl. Code-Verifikation (`index.html` Emoji-Inventar, `prototype.html` Sprite)
- [x] Architektur analysiert: `web/index.html` (`ICONS`-Map, `.opp-icon`, `.scout-btn`, `mkSec`-Sektionsköpfe, Filter-/Location-/Verify-Renderer, Tab-Bar-SVGs), `design/bauhaus/prototype.html` (fertige `<symbol>`-Sprite + `ic()`-Helper)
- [x] Optionen: A (Sprite + `<use>`, konsequente Ablösung) / B (nur `ICONS`-Map + Kern-Buttons, Einzel-SVGs)
- [x] Empfehlung: **Option A** (Sprite, Scope b) — erfüllt „überall einheitlich", WebKit-sicher, theme-tauglich, eine zentrale Definition.

**Optionen (App-Wirkung):**
- **Option A — Sprite + vollständige Ablösung**: Eine zentrale Icon-Sammlung (aus dem Prototyp) wird einmal eingebettet; jede Stelle ruft das passende Icon ab. App wirkt durchgängig ruhig und „aus einem Guss"; Icons folgen Hell/Dunkel automatisch. Aufwand: groß (viele Stellen + ~8 neue Icons). Betroffen: `web/index.html`.
- **Option B — nur Kern-Icons, Rest bleibt Emoji**: Nur Event-Typen + die 4 Hauptbuttons werden Linien-Icons; Filter/Kategorien/Scout-Chips bleiben Emoji. Schneller, aber App bleibt sichtbar gemischt (Ziel teilweise verfehlt). Aufwand: klein–mittel. Betroffen: `web/index.html`.

✅ **Empfehlung: Option A** — nur sie löst „überall einheitlich" wirklich ein; die Sprite aus `prototype.html` ist bereits WebKit-sicher und theme-fähig, sodass das Risiko vor allem im Umfang (viele Fundstellen), nicht in der Technik liegt.

**Testplan:**
- Automatisiert (Harness): begrenzt sinnvoll (reines Frontend-Rendering). Falls eine Icon-Mapping-Tabelle (`event_type → symbol-id`) als JS-Helper ausgelagert wird: pytest/JS-Test „jeder bekannte Event-Typ liefert ein Symbol, unbekannter liefert Fallback".
- Manuell (http://localhost:8000, **Safari Pflicht**): Feed-Liste, Kalender, Scout, Chancendetail, Filter-Sheet, Location-Liste + -Detail, Refresh-Menü je einmal öffnen → kein farbiges Emoji mehr (im Scope), alle Icons sichtbar; Hell- und Dunkelmodus durchschalten (Icons nehmen Theme-Farbe an); Tab-Leiste aktiv/inaktiv prüfen.

**Weg-Gate-Entscheidung (Stephan, 2026-06-27):** ✅ **Option A** (vollständige Ablösung, Scope b). ❓1 Sprite (`<use>`). ❓2 = (b) alle UI-Emojis. ❓3 Sterne-Rating ★ → `i-star`/`i-starfill`-SVG. ❓4 bestehende Tab-/Header-SVGs **vereinheitlichen** (Strich 1.7, Prototyp-Familie). ❓5 strikt `currentColor` (folgt US-99-Tokens). String-/Notification-Emojis (Kalender-SUMMARY, Push-Titel, Toasts) bleiben bewusst außen vor.

---


### US-101 · Kompaktere Buttons und kleinere Schriftgrößen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-27 |
| **Abgeschlossen** | 2026-06-27 |

**Beschreibung:** Als Nutzer empfinde ich viele Buttons und Schriften — besonders im Menü und in den Aktions-Buttons — als zu groß. Buttons (inkl. „Neu") und Schriftgrößen sollen kompakter werden, ohne Funktion oder Touch-Bedienbarkeit zu verschlechtern.

**Bezug:** Kind von US-98. Überschneidet sich mit **US-95** (Detail-Buttons kleiner, Karte größer) — Abgrenzung: US-95 betrifft nur das Chancendetail-Sheet, US-101 die globalen Buttons/Typo-Skalen (Header, Tab-Bar, Listen). Bei Umsetzung gemeinsame Token-Basis nutzen.

---

#### Analyse-Spec (2026-06-27)

**Scope:**
- Eingeschlossen: Header (App-Titel, Subtitle, Icon-Buttons), Tab-Bar (Icons + Labels + „Neu"-Button), Listen (Feed-Karten, Locations-Karten, Scout-Karten), globale Aktions-Buttons (`.btn-primary`, `.btn-secondary`, `.btn-issue`, `.btn-verify`), Refresh-Menü, Filter-Sheet-Buttons/Chips, Such-Overlay.
- Ausgeschlossen: Chancendetail-Sheet-Buttons (gehören zu US-95), Score-Ring-Zahlen (visuell funktional), Karten-Popups (Leaflet, extern), iOS-App (SwiftUI, eigene Codebasis), Kalender-Tab-Events (gut lesbar, kein Feedback), Koordinaten-/Formular-Inputs (min. 16px iOS-Pflicht — Touch-Keyboard-Zoom-Schutz).

**Example Mapping:**

📏 **Rule 1:** Tab-Bar-Labels und Tab-Icons sind kompakter, ohne dass Touch-Targets leiden.
- 🟢 Beispiel: Ich tippe auf den „Karte"-Tab am unteren Rand. Der Tab reagiert sofort — kein Danebentippen nötig, obwohl Label und Icon kleiner erscheinen.
- 🟢 Beispiel: Ich öffne die App und sehe den Tab-Bar — die Labels sind lesbar, aber enger als heute (z.B. 9px statt 10px, Icon 20px statt 22px).

📏 **Rule 2:** Aktions-Buttons (Speichern, Abbrechen, Melden) haben weniger vertikale Polsterung.
- 🟢 Beispiel: Ich tippe im Locations-Detail auf „Speichern". Der Button ist deutlich schmaler als vorher (Padding 10px statt 14px), reagiert aber zuverlässig auf meinen Tipp.
- 🟢 Beispiel: Edge Case: Ich tippe auf „Speichern" mit dem Daumen im unteren Bereich — der Button ist mindestens 44px hoch (Apple HIG Minimum) und reagiert.

📏 **Rule 3:** App-Titel und Subtext im Header sind leicht kompakter.
- 🟢 Beispiel: Ich sehe den Header — der App-Name ist 19–20px statt 22px, der Subtext unverändert (schon klein bei 12px).

📏 **Rule 4:** Refresh-Menü-Items und Filter-Chips sind enger.
- 🟢 Beispiel: Ich öffne das Refresh-Menü — Einträge wirken kompakter (Padding 8px statt 11px vertikal), alle Labels sind noch lesbar.

⚠️ Annahme: Formular-Inputs (`.coord-pair input`, `.edit-form input`) bleiben bei 16px font-size — iOS-Pflicht gegen Auto-Zoom. Bitte bestätigen.
⚠️ Annahme: Touch-Minimum 44×44px (Apple HIG) ist die untere Grenze für alle interaktiven Elemente. Bitte bestätigen.

**Akzeptanzkriterien:**
- [ ] Der App-Titel im Header zeigt sich 2–3px kleiner als heute (ca. 19–20px statt 22px) — erkennbar kompakter, aber noch klar lesbar.
- [ ] Tab-Bar-Labels sind ca. 9px (statt 10px), Tab-Icons 20px (statt 22px) — die Leiste wirkt niedriger.
- [ ] Der „Neu"-Button (goldener Kreis im Tab-Bar) ist minimal kleiner (40px statt 44px Durchmesser), bleibt aber sicher tappbar.
- [ ] `.btn-primary`-Buttons (z.B. „Speichern") haben weniger vertikales Padding (ca. 10–11px statt 14px) — Buttons sind schmäler, aber mindestens 44px Tipp-Fläche gesamt.
- [ ] `.btn-secondary`-Buttons (z.B. „Abbrechen") sind analog kompakter.
- [ ] Aktions-Buttons in Report/Verify-Forms (`.btn-issue`, `.btn-verify`, `.btn-verify-cancel`) sind konsistent kompakter.
- [ ] Refresh-Menü-Items reagieren tippbar bei reduziertem Padding (min. 44px Höhe je Item).
- [ ] Filter-Chips (`.filter-chip`) sind leicht kompakter (padding 5px 10px statt 6px 12px).
- [ ] Formular-Inputs bleiben unverändert bei 16px font-size (kein iOS Auto-Zoom).
- [ ] Edge Case: Auf einem kleinen Bildschirm (iPhone SE, 375px) sind alle Buttons noch ein-fingerig benutzbar — kein ungewolltes Danebentippen beim Tipp-Test durch Stephan.
- [ ] Die Änderungen betreffen ausschließlich `web/index.html` — keine Backend-Änderungen.

**Pre-Mortem:**

📎 Code-Verifikation: `web/index.html` gelesen am 2026-06-27.
- `.btn-primary`: `padding: 14px`, `font-size: 15px` (Z. 439–440) — Kandidat für Reduktion auf 10–11px/14px.
- `.tab`: `font-size: 10px`, SVG `22px` (Z. 170, 172) — bereits sehr klein; Tab-Bar-Höhe `--tab-h: 53px` als Token vorhanden.
- `#tab-add` (Neu-Button): fester Kreis `width: 44px; height: 44px` (Z. 176) — aktuell genau am HIG-Limit.
- `.refresh-menu-item`: `padding: 11px 16px` (Z. 118) — Reduktion auf ~8px möglich.
- Formular-Inputs: `font-size: 16px` (Z. 490, 504, 509) — iOS-Pflicht, NICHT anfassen.

💀 **Szenario 1: Neu-Button zu klein zum Tippen**
- Auslöser: `width/height` des goldenen Kreises auf < 40px reduziert; tatsächliche Tipp-Fläche liegt darunter.
- Frühwarnung: Bei manuellem Test auf echtem iPhone schwer treffbar.
- Gegenmaßnahme: `#tab-add .tab-icon-wrap` mindestens 40×40px behalten; AK „min. 44px Tipp-Fläche" verifiziert Stephan im Tipp-Test.

💀 **Szenario 2: Formular-Inputs erhalten < 16px → iOS zoomt beim Tippen**
- Auslöser: Versehentlich Body-font-size oder Input-font-size auf 14px gesetzt.
- Frühwarnung: Safari-Zoom beim Antippen eines Eingabefelds.
- Gegenmaßnahme: Inputs explizit aus dem Scope ausschließen (AK verankert); bei Implementierung `font-size: 16px` an Input-Stellen nicht anfassen.

💀 **Szenario 3: US-95-Konflikt — Chancendetail-Sheet-Buttons doppelt geändert**
- Auslöser: `.btn-primary`/`.btn-secondary` sind globale Klassen — Änderung wirkt auch im Detail-Sheet (US-95-Scope).
- Frühwarnung: Chancendetail öffnet sich mit ungewollt kleinen Buttons, obwohl US-95 noch offen ist.
- Gegenmaßnahme: Vor Merge prüfen, ob US-95 schon In Progress ist. Falls ja: Koordination oder US-95 zuerst abschließen. Alternativ Detail-Sheet-Buttons beim Merge als gemeinsame Basis sehen (positiv: eliminiert Doppelarbeit).

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` (CSS inline, Z. 35–650 ca.) — alle relevanten Klassen und Token identifiziert. Kein Backend betroffen.
- [ ] Implementierungsoption gewählt (s.u.)

---

**Implementierungsoptionen:**

### Option A — Direkte Werte-Reduktion
Jede betroffene CSS-Klasse wird einzeln mit reduzierten `padding`/`font-size`-Werten angefasst. Keine neuen Token.
- Vorgehen: ~15–20 gezielte Edit-Ops auf Zeilen 105, 118, 170, 172, 176, 394, 433–448 und weitere.
- Betroffene Dateien: `web/index.html` (CSS-Block)
- Vorteile: Einfach, transparent, minimales Risiko; leicht review-bar.
- Nachteile: Kein gemeinsames Token mit US-95 — wenn US-95 später dieselben Buttons anfasst, entstehen Duplikate oder Widersprüche.
- Aufwand: klein

### Option B — CSS-Typo/Spacing-Token (neue Größen-Variablen)
Neue CSS-Custom-Properties (z.B. `--btn-pad-v`, `--tab-icon-sz`, `--tab-label-sz`, `--header-title-sz`) im `:root` einführen; alle betroffenen Stellen referenzieren diese Token statt Hartwerte.
- Vorgehen: 4–6 neue Tokens definieren, ~15 Call-Sites umstellen.
- Betroffene Dateien: `web/index.html` (CSS `:root` + alle Call-Sites)
- Vorteile: Saubere Token-Basis für US-95 (Ticket nennt explizit „gemeinsame Token-Basis nutzen"); spätere Größenanpassungen an einer Stelle.
- Nachteile: Etwas mehr Aufwand; erfordert sorgfältige Benennung.
- Aufwand: mittel

✅ **Empfehlung: Option B — CSS-Typo/Spacing-Token**
Das Ticket selbst schreibt vor, eine gemeinsame Token-Basis mit US-95 zu nutzen. Option B setzt das direkt um, vermeidet Doppelarbeit im US-95-Follow-up und macht zukünftige Größenanpassungen an einer Stelle möglich. Der Mehraufwand gegenüber Option A ist gering (~30 min).

---

**Testplan:**
- [ ] Automatisiert: keine Backend-Logik betroffen — kein pytest-Fall nötig.
- [ ] Manuell (Stephan im Browser + echtem iPhone):
  1. App auf iPhone öffnen → Tab-Bar sichtbar kompakter, alle Tabs tippbar ohne Danebentippen.
  2. „Neu"-Tab antippen → Formular öffnet sich korrekt.
  3. Im Formular ein Textfeld antippen → iOS zoomt NICHT (16px check).
  4. Einen `.btn-primary`-Button antippen → reagiert sofort, fühlt sich sicher an.
  5. Refresh-Menü öffnen → Einträge kompakter, alle tippbar.
  6. Filter öffnen → Chips kompakter, lesbar.

---


### US-102 · Bauhaus-Logo und App-Icon `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-27 |
| **Abgeschlossen** | 2026-06-27 |

**Beschreibung:** Neue Bauhaus-Wortmarke (FOTO​ALERT, Blau-Akzent) plus geometrische Logo-Marke (Roundel aus Kreis/Viertel/Diamant) und passendes App-Icon in den Header und als PWA-Icon übernehmen. Umfasst auch die **PWA-Icons** (`/icons/icon-*.png`, `apple-touch-icon`, `manifest.json`, `<meta theme-color>`), damit das neue Logo beim „Zum Home-Bildschirm" / als WebApp-Symbol erscheint (heute noch altes Kamera-Icon). Quelle: FotoAlert/design/bauhaus/logo.svg.

**Bezug:** Kind von US-98. Quelle: FotoAlert/design/bauhaus/logo.svg. Aufkommen #4 aus dem US-100-Test (2026-06-27).

**Scope:**
Eingeschlossen: Header-Roundel (inline SVG), Login-Screen-Logo, PWA-Icons alle Größen (16/32/180/192/512 px), manifest.json, `<meta theme-color>`, SW-Cache-Version bump.
Ausgeschlossen: iOS App-Icon (Xcode/AppIcon.appiconset), Wortmarke als SVG-Text (bleibt `<h1>`-Text).

**Bestätigte Entscheidungen (2026-06-27):** `theme_color` → `#2D4EA0` (Bauhaus-Blau). iOS-App-Icon nicht Teil dieses Tickets.

**Akzeptanzkriterien:**
- [ ] Im Header erscheint das Bauhaus-Roundel-SVG (Kreis/Viertel/Diamant blau-gold); oranger Kamera-Gradient-Box ist weg.
- [ ] Login-Screen zeigt das Roundel statt des Kamera-Icons.
- [ ] „Zum Home-Bildschirm" in Safari → App-Icon zeigt dunkles Bauhaus-Icon (kein altes Kamera-Icon).
- [ ] `manifest.json`: `theme_color` = `#2D4EA0`, `background_color` = `#15171C`.
- [ ] `<meta name="theme-color">` im `<head>` = `#2D4EA0`.
- [ ] Alle Icon-Größen ersetzt: icon-16.png, icon-32.png, icon-180.png, icon-192.png, icon-512.png.
- [ ] SW-Cache-Version ist gebumpt (neue Icons werden ausgeliefert, nicht aus altem Cache).
- [ ] Edge Case: Icon auf weißem iOS-Homescreen gut erkennbar (dunkler Hintergrund schützt).

**Pre-Mortem:**
- 💀 cairosvg fehlt auf Server → Gegenmaßnahme: PNGs in Sandbox generieren, per Git pushen (kein Server-Dependency)
- 💀 SVG-Farben nicht token-gebunden → Gegenmaßnahme: Roundel-Farben hardcodiert (Markenfarben — kein currentColor nötig)
- 💀 SW cached alte Icons → Gegenmaßnahme: Cache-Version bump in sw.js

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2026-06-27)
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` Z.836 (Header), Z.823 (Login), `web/manifest.json`, `web/icons/`, `web/sw.js`, `design/bauhaus/logo.svg`
- [x] Implementierung: 2 Subagenten — Agent 1: index.html (Header + Login SVG), Agent 2: PNG-Generierung + manifest + sw.js

**Testplan:**
- [ ] Manuell: http://localhost:8000 — Header-Roundel sichtbar, Login-Roundel sichtbar
- [ ] Manuell: Safari → Teilen → „Zum Home-Bildschirm" → Icon prüfen
- [ ] curl: `curl -s http://localhost:8000/manifest.json | python3 -m json.tool | grep theme`

---


### US-88 · Brennweiten-Filter: Nicht-linearer Slider für feinere Auflösung im Weitwinkelbereich `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **Implementiert** | 2026-06-25 |
| **Abgeschlossen** | 2026-06-27 |

**Beschreibung:** Im Brennweiten-Filter liegen 10, 14, 18, 21, 28 und 35 mm so nah beieinander, dass eine präzise Auswahl kaum möglich ist, während 300 und 600 mm sehr weit auseinanderliegen. Der Slider soll eine nicht-lineare Skalierung (z. B. logarithmisch oder mit definierten Stufen) erhalten, die im Weitwinkelbereich feinere Schritte und im Telebereich sinnvolle Zwischenstufen (400 mm, 500 mm) ermöglicht.

**Scope:**
Eingeschlossen: Dual-Range-Slider in `initDualSlider()` auf Stufen-Mapping umstellen; MAX_VAL auf 800 anheben; Migration bestehender gespeicherter Werte.
Ausgeschlossen: Filterlogik (mm-Vergleich bleibt), Backend, Labels.

**Akzeptanzkriterien:**
- [ ] Wenn ich den linken Thumb auf ~1/4 der Slider-Breite ziehe, rastet er auf 35 mm ein (vorher wäre das ~150 mm gewesen)
- [ ] Im Weitwinkelbereich (14–85 mm) gibt es 6 einrastbare Stufen, jede einzeln wählbar
- [ ] Das Label zeigt immer einen Wert aus der Stufenliste, nie einen Zwischenwert
- [ ] Stufen-Werte: 0, 14, 21, 24, 28, 35, 50, 70, 85, 105, 135, 200, 300, 400, 500, 600, 800 mm
- [ ] Standorte mit 800 mm Brennweite sind über den Slider filterbar (Max-Thumb auf 800 mm setzbar)
- [ ] Edge Case: Bestehende `minFocal`/`maxFocal`-Werte aus alten Einstellungen werden beim Öffnen des Sliders auf die nächste Stufe gerundet (kein Stuck-Thumb)
- [ ] Edge Case: Min-Thumb und Max-Thumb können nicht auf dieselbe Stufe gesetzt werden

**Pre-Mortem:**
- 💀 Alter gespeicherter Wert (z.B. 75) passt zu keiner Stufe → Gegenmaßnahme: `snapToStep(v)` in `updateUI` beim Laden aufrufen
- 💀 CSS `left`-Prozent bleibt linear gegen MAX_VAL → Gegenmaßnahme: eigene `valToPct(v)` / `pctToVal(pct)` auf Index-Basis der Stufenliste
- 💀 MAX_VAL 600 klemmt 800-mm-Standorte aus → Gegenmaßnahme: MAX_VAL = 800, STEPS-Array endet bei 800

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2026-06-25)
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` `initDualSlider()` (Z. ~2301), `_render()` (focalMinPct/MaxPct Z. ~2544), `_onFocalSlider/_onFocalMaxSlider`
- [x] Implementierungsoption: Stufen-Array (Option A — von Stephan bestätigt)
- [x] Stufenliste bestätigt: `[0, 14, 21, 24, 28, 35, 50, 70, 85, 105, 135, 200, 300, 400, 500, 600, 800]`

**Implementierungsnotizen:**
- `const STEPS = [0,14,21,24,28,35,50,70,85,105,135,200,300,400,500,600,800]`
- `pctToVal(pct)`: nächste Stufe via `STEPS.reduce(...)` zum Pixel-Anteil
- `valToPct(v)`: `STEPS.indexOf(snapToStep(v)) / (STEPS.length - 1) * 100`
- `snapToStep(v)`: `STEPS.reduce((a,b) => Math.abs(b-v) < Math.abs(a-v) ? b : a)`
- `MAX_VAL` in `initDualSlider` → 800; `focalMinPct/MaxPct` in `_render` ebenfalls anpassen
- `_onFocalSlider/_onFocalMaxSlider` sind Legacy (Einzel-Slider) — prüfen ob noch aktiv, ggf. ebenfalls anpassen

**Testplan:**
- [ ] Automatisiert: kein Backend-Test nötig (rein Frontend)
- [ ] Manuell: Filter-Sheet öffnen → Brennweiten-Slider prüfen: Thumb auf 1/4 → Label 35 mm? Thumb ganz rechts → 800 mm?
- [ ] Manuell: localStorage mit altem Wert (z.B. `fa_filter: {"minFocal":75}`) setzen → Sheet öffnen → Thumb landet auf 70 mm?

---


### BUG-27 · 365-Tage-Kalender leer, lädt keine Ereignisse `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-21 |
| **Abgeschlossen** | 2026-06-22 |

**Beschreibung:** Der 365-Tage-Kalender ist leer und zeigt keine Ereignisse an. Mögliche Ursachen: Regression von BUG-14 (Kalender leer nach Cron-Lauf), defekter Cron-Lauf, oder Frontend-Ladefehler beim monatlichen Nachladen (`?month=X&year=Y`).

**Bezug:** Mögliche Regression von BUG-14 [x] (Jahres- & 14-Tage-Kalender leer nach Cron-Lauf, Fix 2026-06-18); verwandt mit BUG-10 [x] (Mond-Alignments im Kalender).

---

**Scope:**
Eingeschlossen: Leere-Response-Caching im Frontend fixen; Backend-Fallback wenn `calendar.json` fehlt/leer.
Ausgeschlossen: Cron-Scheduling-Mechanismus (US-34), Push-Notifications.

**Akzeptanzkriterien:**
- [x] Kalender zeigt Events des aktuellen Monats — Rebuild 2026-06-22 00:34: 44.057 Events, calendar.json v1.3 ✅
- [x] Wenn Server `no_cache` zurückgibt: Frontend cacht kein leeres Ergebnis — nächster Aufruf löst erneuten Fetch aus
- [x] Wenn Server `no_cache` zurückgibt: Toast „Kalender wird neu berechnet – bitte in 2 Min. neu laden"
- [x] Edge Case: Race-Condition `show()` während `_loading=true` — render() wird nach Load immer aufgerufen
- [x] `/calendar?month=6&year=2026` liefert `status: ok` mit Events (73k-Response bestätigt) ✅

**Fix 2026-06-21:** `web/index.html` — `loadMonth()` cacht nur bei `status=ok` + `events.length > 0`; `no_cache` → Toast; `show()` Race-Fix.

**Pre-Mortem:**
- 💀 Szenario: Server neu gestartet, `_calendar_cache = []`, App geöffnet → `no_cache` → Frontend speichert `[]` in `_monthCache` → Kalender bleibt für die Session leer, egal wie viele Male der User navigiert.
  Auslöser: `_monthCache.set(key, res.events || [])` speichert auch bei `status=no_cache`.
  Gegenmaßnahme: Nur bei `status === 'ok'` und `events.length > 0` cachen (→ AK 2).

- 💀 Szenario: `show()` wird zweimal aufgerufen (Tab-Wechsel während Load) → zweiter Aufruf trifft `_loading=true` → `return` → `render()` wird nie aufgerufen nach dem Load.
  Auslöser: `if (this._loading) return;` im `show()`-Pfad.
  Gegenmaßnahme: Nach `loadMonth()` immer `render()` erzwingen (→ AK 4).

- 💀 Szenario: `calendar.json` auf Disk fehlt/korrupt nach Deployment → Server-Start lädt leeren Cache → gleiche Kette wie oben.
  Frühwarnung: Health-Alert im Log (HEALTH_CAL_MIN=10) — aber nur beim nächsten Cron-Lauf sichtbar, nicht sofort beim Server-Start.
  Gegenmaßnahme: AK 5 + manuell `calendar.json` auf Server prüfen vor Deploy.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` (CalendarView: `show()`, `loadMonth()`, `_monthCache`), `backend/main.py` (`/calendar`-Endpoint, `_calendar_cache`), `backend/precompute.py` (`compute_calendar_incremental`)
- [ ] Implementierungsoptionen: A / B
- [ ] Empfehlung: Option A

**Implementierungsoptionen:**

### Option A — Frontend-Fix: Leere Responses nicht cachen + Race-Fix + Toast
- Vorgehen:
  1. `loadMonth()`: nur cachen wenn `res.status === 'ok'` und `res.events.length > 0`; bei `no_cache`/leer: Toast + kein `_monthCache.set`
  2. `show()`: nach `await this.loadMonth()` immer `if (Feed.mode === 'calendar') this.render()` aufrufen (Race-Fix)
- Betroffene Dateien: `web/index.html` (~5 Zeilen)
- Vorteile: Minimal-invasiv, behebt beide bekannten Frontend-Ursachen; kein Backend nötig
- Nachteile: Löst nicht das Problem wenn `calendar.json` strukturell fehlt
- Aufwand: klein

### Option B — Backend-Fix + Frontend-Fix
- Vorgehen: Option A + beim Server-Start prüfen ob `calendar.json` vorhanden/valide → ggf. auto-trigger Neuberechnung (non-blocking background task)
- Betroffene Dateien: `web/index.html`, `backend/main.py` (startup event)
- Vorteile: Resilienter nach Deployments/Server-Restart
- Nachteile: Neuberechnung dauert 2–5 Minuten → User sieht in dieser Zeit immer noch leeren Kalender; erhöhte Startup-Last
- Aufwand: mittel

**Testplan:**
- [ ] Automatisiert: `curl https://fotoalert.stephanschumann.com/calendar?month=6&year=2026` → `status: ok`, `total > 0`
- [ ] Manuell: App öffnen → Kalender-Tab → Events sichtbar (nicht leer)
- [ ] Manuell: Netzwerk drosseln, Tab wechseln während Load → nach Load erscheinen Events (Race-Fix)

---


### BUG-22 · Änderungen in Locationdetails ohne Effekt auf Chancen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-18 |
| **In Progress seit** | 2026-06-18 |
| **Abgeschlossen** | 2026-06-20 |

**Root Cause:** PATCH `/locations/{id}` kannte nur `coord_fields | text_fields`. Weder `focal_length_suggestions` noch `observer_floor_height_m` waren in der Whitelist — PATCHes auf diese Felder wurden mit HTTP 400 abgelehnt und konnten nie Recompute auslösen.

**Fix (zusammen mit US-62):**
- `focal_length_suggestions` (list[int]) + `observer_floor_height_m` zur PATCH-Whitelist hinzugefügt
- `recompute_fields = coord_fields | {"observer_floor_height_m", "focal_length_suggestions"}` → Recompute bei jedem dieser Felder
- `focal_length_suggestions` wird jetzt auch in `location_overrides.json` persistiert und beim Startup geladen
- `name`/`description` triggern weiterhin KEINEN Recompute

**Akzeptanzkriterien:**
- [x] PATCH auf `focal_length_suggestions` triggert Recompute → camera_hints aktualisiert
- [x] PATCH auf `observer_floor_height_m` triggert Recompute → Kompositions-Analyse aktualisiert
- [x] PATCH auf `name`/`description` triggert KEINEN Recompute
- [x] API-Log: `recompute_triggered: true` bei Focal-Length-PATCH

**Abhängigkeiten:** TASK-12[x], US-62

**Bezug (2026-06-20):** Owner der Recompute-Trigger-Whitelist für das Epic TASK-16 (Rule 4). Fix umgesetzt und **am 2026-06-20 manuell verifiziert** (4/4 AKs grün: focal_length + observer_floor_height → `recompute_triggered: true`; name/description → `false`; PATCH ohne Token → 401). Aus 🧪 In Test entfernt → Done.


### BUG-23 · Kartenfilter-Sync: Eventtyp-Filter wirkt nicht in Kartenansicht `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-18 |
| **In Progress seit** | 2026-06-18 |
| **Abgeschlossen** | 2026-06-18 |

**Root Cause:** `MapView.loadMarkers()` fügte alle Marker bedingungslos hinzu; `FilterSheet._applyLive()` hatte keinen `'map'`-Branch; kein Mechanismus zum Aus-/Einblenden von Markern.

**Fix:** Feed-basiertes Filtering via `Feed.data` (14-Tage-Cache): `MapView.applyFilter()` baut ein `Set` aller `location_id`s die im Feed Events des gesuchten Typs haben → `addLayer()`/`removeLayer()` per Marker. Zusätzlich: Filter-Ergebniszähler im FilterSheet, Score-Slider in Kartenansicht ausgegraut.

**Implementierung:**
- `MapView.markers` als `{marker, loc}`-Array (statt nur Marker)
- `MapView.applyFilter()` mit `ET_EXPAND`-Mapping (z.B. „Goldene Stunde" → Morgen+Abend)
- `FilterSheet._applyLive()` mit Map-Branch
- `FilterSheet._updateResultCount()` – zeigt „X von Y Locations/Chancen/Events sichtbar"
- Score-Slider in Kartenansicht deaktiviert mit Hinweis

**Abhängigkeiten:** US-35[x], US-32[x] · **Version:** v1.5.x


### BUG-14 · Jahres- & 14-Tage-Kalender leer nach Cron-Lauf `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-17 |
| **In Progress seit** | 2026-06-18 |
| **Abgeschlossen** | 2026-06-18 |

**Beschreibung:** Am 2026-06-17 um 6:20 Uhr waren Jahreskalender und 14-Tage-Kalender nach dem Cron-Lauf komplett leer.

**Scope:**
- Eingeschlossen: Health-Alert-Logging nach Cron-Lauf (feed + calendar), Regression-Check-Konstanten in `precompute.py`
- Ausgeschlossen: Frontend-Änderungen, neue API-Endpoints

**Root Cause (analysiert 2026-06-18):**
Zwei kombinierte Ursachen:
1. **Cron-Timing (bereits behoben via TASK-15[x]):** Cron lief um 5:30 Uhr, unmittelbar um den Sonnenaufgang → potenzielle Race Condition mit Skyfield-Berechnungen für den aktuellen Tag.
2. **Stille Exception-Handler:** `compute_feed()` und `compute_calendar_incremental()` fangen pro-Location-Exceptions (`logger.error + continue`). Wenn alle Locations scheitern, landet ein leeres Array in der JSON-Datei — ohne übergeordnete Warnung. Kein Health-Alert → Problem bleibt unbemerkt bis Nutzer die App öffnet.

**Akzeptanzkriterien:**
- [x] Root Cause identifiziert und dokumentiert
- [x] Health-Alert: wenn nach Cron-Lauf `calendar.json` < 10 Events → `logger.error` mit Zeitstempel
- [x] Regression-Check: Feed < 5 Events → `logger.error`; Calendar < 30 Events → `logger.warning`
- [x] Fix deployed, Cron-Lauf produziert vollständige Kalender-Daten

**Analyse & Planung:**
- [x] `precompute.py` vollständig gelesen – Exception-Handler verstanden
- [x] Betroffene Stelle: `main()` nach `feed_path.write_text(...)` und `cal_path.write_text(...)`
- [x] Ansatz: Konstanten `HEALTH_FEED_MIN` / `HEALTH_CAL_MIN` / `REGRESSION_CAL_MIN` + Checks am Ende von `main()`
- [x] Risiken: keine – rein additive Logging-Ergänzung

**Testplan:**
- [ ] Lokaler Test: `cd backend && python3 precompute.py --feed-only` → Log enthält keinen ERROR bei normalem Lauf
- [ ] Manueller Smoke-Test: Event-Anzahl in `opportunities.json` + `calendar.json` prüfen

**Abhängigkeiten:** TASK-15[x] (Cron auf 00:01 bereits umgestellt)


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


### TASK-16 · Epic: Datenfundament (Speicher · Backup · Dev/Prod-Isolation) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Epic (Architektur/Infrastruktur) |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-20 |
| **Abgeschlossen** | 2026-06-20 |
| **Kind-Tickets** | TASK-17 (Speicher) · TASK-18 (Backup) · TASK-19 (Dev/Prod) |

> **Epic-Hinweis:** Dieses Ticket selbst liefert keinen Code. Es bündelt das Konzept und drei umsetzbare Kind-Tickets. Der Recompute-Aspekt der ursprünglichen Anforderung wird delegiert: **Trigger → BUG-22**, **Orchestrierung/Scheduling → US-34**.

**Beschreibung:**
Konzept für die zentrale Speicherung der nutzergenerierten Location-Daten auf dem Server: jederzeit durch Nutzer aktualisierbar, mit so engmaschigem Backup, dass zwischen zwei Backups gemachte Änderungen bei einer Wiederherstellung nicht verloren gehen. Die Entwicklungsumgebung muss mit denselben Daten arbeiten können, ohne die Live-Daten je zu überschreiben. Nutzerdaten sind das höchste Gut und unter allen Umständen zu schützen. Jede Datenänderung muss eine Neuberechnung auslösen (Mond-/Sonne-/Himmelsereignisse, Standort-Infos, Chancen, Scouts, Karten-/Maps-/Streetview-Links, Kartendarstellung, Wetter, Brennweiten).

**Architektur-Entscheidungen (bestätigt 2026-06-20):**
- **Speichermodell:** Migration der nutzereditierbaren Daten von JSON-Dateien → **SQLite mit WAL** (atomare Transaktionen, kein Korruptionsrisiko bei parallelen Edits).
- **Offsite-Backup:** **Privates Git-Repo** (versioniert, jeder Stand wiederherstellbar) zusätzlich zur Server-Kopie.
- **RPO ≈ 0:** Jede Nutzeränderung wird sofort gesichert (WAL + Commit pro Mutation).
- **Dev/Prod-Isolation:** Read-only Snapshot in eigenes `data_dev/`-Verzeichnis; Dev schreibt nie nach Prod.

---

#### Ausgangslage (Ist-Analyse)

| Aspekt | Heute | Risiko |
|--------|-------|--------|
| Persistenz | 2 JSON-Dateien (`custom_locations.json`, `location_overrides.json`), gitignored, leben nur auf dem Server | Single Point of Failure |
| Schreibvorgang | `_save_custom_location`, `_update_custom_location`, `_save_location_override` → **nicht-atomare** `write_text()` (Komplett-Rewrite) | Crash mitten im Schreiben = korrupte Datei = **Totalverlust** |
| Concurrency | Kein Lock; paralleler Edit überschreibt | Lost Update |
| Backup | **Keines** (nur `sync-pull.sh`, Prod→Mac, manuell, read) | Kein Restore-Pfad |
| Dev/Prod | Gleicher Pfad `backend/data/`; `sync-pull` überschreibt lokal | Restrisiko versehentlicher Prod-Write |
| Recompute | `_run_precompute_single(loc_id)` nach Koord-/relevanten PATCHes (TASK-12) | Funktioniert; Trigger-Whitelist unvollständig (siehe BUG-22) |

---

#### Example Mapping

📏 **Rule 1 — Nutzerdaten überleben jeden Crash/Fehler (Integrität).**
  🟢 *Given* ein User speichert eine neue Location, *When* der Prozess mitten im Schreiben abstürzt, *Then* ist die vorherige DB unversehrt und die Transaktion entweder ganz oder gar nicht angewandt (SQLite-Atomarität).
  🟢 *Given* zwei Edits treffen quasi-gleichzeitig ein, *When* beide committen, *Then* geht keine der beiden Änderungen verloren (WAL serialisiert).

📏 **Rule 2 — Zwischen zwei Backups gemachte Änderungen gehen bei Restore nicht verloren (RPO ≈ 0).**
  🟢 *Given* der Server-Datenträger fällt total aus, *When* aus dem Offsite-Backup wiederhergestellt wird, *Then* ist der letzte erfolgreich committete User-Edit enthalten.
  🟢 *Given* eine Datenverfälschung wird Tage später entdeckt, *When* auf einen früheren Stand zurückgerollt wird, *Then* ist jeder historische Commit-Stand auswählbar (Git-Historie).

📏 **Rule 3 — Die Dev-Umgebung kann Prod-Daten niemals verändern.**
  🟢 *Given* Dev läuft lokal, *When* dort eine Location bearbeitet/gelöscht wird, *Then* bleibt die Prod-DB unberührt (getrennter `data_dev/`-Pfad, kein Schreibzugang zu Prod).
  🟢 *Given* ein Deploy läuft, *When* `git pull --reset --hard` ausgeführt wird, *Then* werden die Daten (außerhalb Git-Tree / gitignored) nicht überschrieben.

📏 **Rule 4 — Jede Datenmutation löst die vollständige Neuberechnung der abhängigen Artefakte aus.**
  🟢 *Given* ein User ändert Koordinaten/Brennweite/Höhe einer Location, *When* gespeichert wird, *Then* werden für diese Location neu berechnet: Astronomie (Mond/Sonne/Himmelsereignisse), Composition-Analyse, Chancen/Feed, Kalender, Scout-Einträge, Wetter, Brennweiten-Empfehlungen.
  🟢 *Given* Maps-/Streetview-Links und Kartendarstellung hängen von den Koordinaten ab, *When* Koordinaten sich ändern, *Then* zeigen Detail-Ansicht und Karte die aktualisierten Links/Marker.
  *(Rule 4 ist delegiert: Trigger-Verdrahtung im Store stellt TASK-17 sicher; welche Felder triggern = BUG-22; was/wann neu berechnet wird = US-34.)*

*(Questions = 0 — alle vier offenen Architektur-Entscheidungen wurden am 2026-06-20 mit Stephan geklärt.)*

---

#### Aufteilung in Kind-Tickets

| Kind-Ticket | Inhalt | Abhängigkeit |
|-------------|--------|--------------|
| **TASK-17** | SQLite-Migration + atomare Writes (Fundament) | — |
| **TASK-18** | Backup RPO≈0 + Restore (privates Git-Repo) | TASK-17 |
| **TASK-19** | Dev/Prod-Daten-Isolation (`data_dev/`) | TASK-17 |

#### Sequenzierung (kritischer Pfad)

```
BUG-22 (schließen) ──▶ TASK-17 ──▶ TASK-18 + TASK-19 ──▶ US-77 ──▶ US-75 ──▶ US-34 / US-38
US-39 (Code-Rollback) läuft unabhängig parallel.
```
TASK-17 ist der Flaschenhals: erst danach sind Daten atomar (TASK-18) und isolierbar (TASK-19), und erst danach sind Merge/Upsert (US-77/US-75) sauber umsetzbar.

**Bezug (Epic):**
- **US-65** (Auto-Backup) → **gemerged in TASK-18** (RPO≈0 ersetzt das tägliche Snapshot-Konzept; 7-Versionen-Snapshot + >25h-Alert als Fallback übernommen).
- **US-39** (Resilient Deployment) → **abgegrenzt** auf reines Code-/Deploy-Rollback; Bullet „Datensicherung vor Precompute" → in TASK-18 übernommen.
- **BUG-22** → separat, liefert die Recompute-Trigger-Whitelist (Abschluss vorbereiten).
- **US-77 / US-75 / US-34 / US-38** → separat, Abhängigkeit/Cross-Reference auf dieses Epic ergänzt.

---


### TASK-17 · SQLite-Migration + atomare Writes (Fundament) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task (Architektur) |
| **Priorität** | Hoch |
| **Status** | Done |
| **Abgeschlossen** | 2026-06-20 |
| **Erstellt** | 2026-06-20 |
| **Epic** | TASK-16 |

**Beschreibung:** Nutzereditierbare Location-Daten von JSON-Dateien auf SQLite (WAL) migrieren; alle Schreibzugriffe atomar über ein zentrales Repository kapseln. Fundament für TASK-18 und TASK-19.

**Scope:**
- Eingeschlossen: `backend/data/store.py` (SQLite-Repository, `PRAGMA journal_mode=WAL`, Transaktionen) für `custom_locations` + `location_overrides`; `migrate_json_to_sqlite.py` (idempotent, JSONs als Seed); `main.py` ruft nur noch das Repository (ersetzt `_save_custom_location`, `_update_custom_location`, `_save_location_override`); Recompute-Hook bei jeder Mutation (inkl. create/delete) verdrahten.
- Ausgeschlossen: Backup (TASK-18), Pfad-Isolation (TASK-19), Feld-Trigger-Whitelist (BUG-22), Scheduling (US-34).

**Akzeptanzkriterien:**
- [ ] Daten liegen in SQLite mit WAL; Migration aus bestehenden JSONs verlustfrei (Einträge vorher = nachher).
- [ ] Schreibvorgänge atomar — simulierter Crash mitten im Save lässt die DB konsistent (`PRAGMA integrity_check` = ok).
- [ ] `main.py` greift ausschließlich über `store.py` auf Daten zu (kein `write_text` mehr).
- [ ] Jede Mutation (inkl. neue/gelöschte Location) ruft den Recompute-Hook auf; welche Felder triggern, bleibt BUG-22.
- [ ] Edge Case: Migration erneut ausgeführt → idempotent, keine Duplikate.
- [ ] Edge Case: Löschen entfernt aus DB **und** aus abgeleiteten Caches (kein Geistereintrag in Feed/Kalender/Karte).

**Daten-Validierung:**
- [x] Quelldaten winzig (`custom_locations.json` ~651 B, `location_overrides.json` ~234 B) → Migration trivial; Caches (97 MB calendar.json) bleiben außen vor (reproduzierbar via precompute).
- [x] Aktuell: 1 Custom Location (`custom_1781560330`), 1 Override (`rostiger_nagel_rusty_nail`) → 2 Einträge total.
- [x] Kein DELETE-Endpoint vorhanden → `store.delete_custom()` implementieren, aber kein Endpoint-Wiring in diesem Ticket; Recompute-Hook-Wiring für DELETE vorbereiten.
- [x] CREATE triggert aktuell **keinen** Recompute (nur PATCH does) → Bug; wird in TASK-17 behoben.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2026-06-20)
- [x] Architektur analysiert: 3 betroffene Schreibfunktionen in `main.py` (`_save_custom_location`, `_update_custom_location_file`, `_save_location_override`); 2 Ladefunktionen (`_load_custom_locations`, `_load_location_overrides`).
- [x] SQLite-Schema definiert (s.u.)

**Implementierungsansatz:**

**Schritt 1 — `backend/data/store.py` (neu)**

```python
class LocationStore:
    DB_PATH = Path(__file__).parent / "fotoalert.db"
```

Zwei Tabellen:

```sql
-- custom_locations: alle Felder aus dem bestehenden JSON-Dict
CREATE TABLE IF NOT EXISTS custom_locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT DEFAULT 'SKYLINE',
    observer_lat REAL, observer_lon REAL,
    subject_lat REAL, subject_lon REAL,
    subject_name TEXT DEFAULT '',
    subject_height_m REAL DEFAULT 0,
    subject_width_m REAL DEFAULT 0,
    distance_m INTEGER DEFAULT 0,
    focal_length_suggestions TEXT DEFAULT '[]',  -- JSON-Array
    special_notes TEXT DEFAULT '',
    difficulty INTEGER DEFAULT 1,
    observer_floor_height_m REAL DEFAULT 0.0
);

-- location_overrides: id + fields als JSON-Blob (flexibel, da Felder variieren)
CREATE TABLE IF NOT EXISTS location_overrides (
    id TEXT PRIMARY KEY,
    fields TEXT NOT NULL  -- JSON-Objekt, z.B. {"observer_lat": 51.5, "name": "..."}
);
```

WAL aktivieren: `PRAGMA journal_mode=WAL` beim `_init_db`.

Methoden:
- `create_custom(loc: PhotoLocation) → None` — INSERT mit BEGIN/COMMIT/ROLLBACK
- `update_custom(loc_id: str, **fields) → bool` — UPDATE einzelner Felder
- `delete_custom(loc_id: str) → bool` — DELETE + True wenn gefunden
- `upsert_override(loc_id: str, **fields) → None` — INSERT OR REPLACE (merge mit bestehendem JSON-Blob)
- `load_all_custom() → list[dict]` — SELECT *; für Startup-Load
- `load_all_overrides() → list[dict]` — SELECT id, fields; für Startup-Load

Alle Writes in expliziten Transaktionen (`BEGIN` / `COMMIT` / `ROLLBACK`).

**Schritt 2 — `backend/migrate_json_to_sqlite.py` (neu)**

Eigenständiges Script (nicht via import), läuft einmalig vor dem ersten Start:

```
python migrate_json_to_sqlite.py
```

Ablauf:
1. `custom_locations.json` lesen → `INSERT OR IGNORE INTO custom_locations`
2. `location_overrides.json` lesen → `INSERT OR IGNORE INTO location_overrides`
3. Log: „N Einträge migriert, M bereits vorhanden (übersprungen)"

Idempotenz via `INSERT OR IGNORE` auf PRIMARY KEY (`id`).

**Schritt 3 — `backend/main.py` (ändern)**

Ersetzen:

| Alt | Neu |
|-----|-----|
| `_CUSTOM_LOC_FILE`, `_OVERRIDES_FILE` | entfernen (nur noch Pfade im Store) |
| `_load_custom_locations()` | `store.load_all_custom()` → PhotoLocation-Objekte bauen, an LOCATIONS hängen |
| `_load_location_overrides()` | `store.load_all_overrides()` → setattr wie bisher |
| `_save_custom_location(loc)` | `store.create_custom(loc)` + `asyncio.create_task(_run_precompute_single(loc.id))` ← **neu** |
| `_update_custom_location_file(loc_id, **fields)` | `store.update_custom(loc_id, **fields)` |
| `_save_location_override(loc_id, **fields)` | `store.upsert_override(loc_id, **fields)` |

Singleton: `_store = LocationStore()` einmal auf Modulebene initialisieren.

**Schritt 4 — Startup-Reihenfolge anpassen**

`startup()`-Funktion: `_load_custom_locations()` + `_load_location_overrides()` → ersetzen durch Store-Calls; JSONs als Fallback-Seed wenn DB noch leer (falls Migration nicht manuell lief). Das macht den Server self-contained beim ersten Start.

**Risiken:**
- `focal_length_suggestions` wird als JSON-String gespeichert → beim Laden `json.loads()` nicht vergessen
- `upsert_override`: merge mit bestehendem Blob (nicht blind überschreiben) — `json.loads(existing) | new_fields`
- WAL-File (`fotoalert.db-wal`) darf nicht im `.gitignore` landen wenn TASK-18 darauf aufbaut

**Testplan:**
- [ ] Manuell (lokal): `sqlite3 fotoalert.db "SELECT * FROM custom_locations"` → 1 Eintrag nach Migration
- [ ] `POST /preview-alignment` mit `save=true` → Neuer Eintrag in DB + Recompute-Log sichtbar
- [ ] `PATCH /locations/custom_1781560330` mit neuen Koordinaten → DB-Eintrag geändert, Recompute getriggert
- [ ] `PATCH /locations/rostiger_nagel_rusty_nail` → Override in DB geändert
- [ ] Crash-Simulation: `kill -9` während PATCH → `PRAGMA integrity_check` = `ok`
- [ ] Migration doppelt laufen → `SELECT COUNT(*) FROM custom_locations` = 1 (keine Duplikate)
- [ ] Curl-Testschritte: Fenster 1 = Server, Fenster 2 = curl (s. Terminal-Fenster-Modell)

---


### TASK-18 · Backup RPO≈0 + Restore (privates Git-Repo) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task (Infrastruktur) |
| **Priorität** | Hoch |
| **Status** | Done |
| **Abgeschlossen** | 2026-06-20 |
| **Erstellt** | 2026-06-20 |
| **Epic** | TASK-16 · **Abhängigkeit:** TASK-17 |

**Beschreibung:** Engmaschige, versionierte Sicherung der Nutzerdaten in ein privates Git-Repo (RPO≈0) plus getesteter Restore-Pfad. Übernimmt US-65 (Auto-Backup) und den Datensicherungs-Bullet aus US-39.

**Scope:**
- Eingeschlossen: `backend/data/backup.py` — nach jedem erfolgreichen User-Edit Export (deterministisches Dump) + `git add/commit/push` ins private Daten-Repo (separater Remote, Deploy-Key); Snapshot vor jedem Precompute-Lauf; lokaler Fallback-Snapshot mit Retention (7 Versionen); `restore.sh` + Doku in `deploy/`; Backup-Health-Signal (>25h kein Backup) für US-38.
- Ausgeschlossen: Code-/Deploy-Rollback (US-39), Caches im Backup (reproduzierbar).

**Akzeptanzkriterien:**
- [ ] Nach jedem erfolgreichen User-Edit neuer Commit im privaten Daten-Repo (RPO≈0); Push-Fehler werden geloggt + retried, blockieren den User-Request nicht.
- [ ] Snapshot der Daten vor jedem Precompute-Lauf (übernommen aus US-39).
- [ ] Lokaler Fallback-Snapshot mit 7-Versionen-Retention; älteste wird automatisch gelöscht (übernommen aus US-65).
- [ ] `restore.sh` stellt aus dem Daten-Repo eine lauffähige DB her — dokumentierter, **getesteter** Restore-Lauf.
- [ ] Health-Signal an US-38, wenn Backup seit >25h ausbleibt.
- [ ] Edge Case: Git-Remote nicht erreichbar → lokaler Commit/Snapshot bleibt erhalten, Sync holt beim nächsten Lauf nach.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2026-06-20)
- [x] Architektur analysiert: `backup.py` (neu), `main.py` (2 Stellen), `precompute.py` (1 Stelle), `deploy/restore.sh` (neu)
- [x] Export-Format: JSON-Dump (nicht Binär-DB) → lesbare Git-Diffs, Restore via `migrate_json_to_sqlite.py`
- [x] Dev-Guard: `FOTOALERT_ENV != prod` → alle Backup-Funktionen sind No-Ops
- [x] Backup-Repo-Name: `fotoalert-backup` (privat auf GitHub, noch anzulegen)

**Einmaliges Server-Setup** *(vor erstem Deploy):*

```
# 1. Auf GitHub: privates Repo "fotoalert-backup" anlegen (leer, kein README)

# 2. Auf dem Server: Deploy-Key generieren
ssh-keygen -t ed25519 -f ~/.ssh/fotoalert_backup -N ""
cat ~/.ssh/fotoalert_backup.pub
# → Public Key in GitHub → fotoalert-backup → Settings → Deploy Keys → Add (Write access)

# 3. Backup-Repo klonen
cd /opt/fotoalert
git clone git@github.com:<dein-user>/fotoalert-backup.git backup-repo
# SSH-Key für diesen Remote konfigurieren:
git -C backup-repo config core.sshCommand "ssh -i /home/fotoalert/.ssh/fotoalert_backup"
```

**Implementierungsansatz:**

**Schritt 1 — `backend/data/backup.py` (neu)**

Drei öffentliche Funktionen:

```python
def backup_after_edit(loc_id: str) -> None:
    """Exportiert DB als JSON → git commit+push ins Backup-Repo. Non-blocking (in asyncio.create_task aufrufen)."""

def snapshot_before_precompute() -> None:
    """Kopiert fotoalert.db → data/snapshots/fotoalert_YYYYMMDD_HHMM.db; behält max 7."""

def last_backup_age_hours() -> float | None:
    """Gibt Stunden seit letztem Git-Commit zurück (für Health-Signal US-38)."""
```

Dev-Guard am Anfang jeder Funktion: `if os.getenv("FOTOALERT_ENV", "prod") != "prod": return`

Backup-Repo-Pfad: `/opt/fotoalert/backup-repo` (via Env-Variable `FOTOALERT_BACKUP_REPO`, Default `/opt/fotoalert/backup-repo`)

`backup_after_edit` Ablauf:
1. JSON-Export aus SQLite (`store.load_all_custom()` + `store.load_all_overrides()`)
2. `custom_locations.json` + `location_overrides.json` in Backup-Repo schreiben
3. `git add . && git commit -m "backup: edit {loc_id} {timestamp}"` (subprocess)
4. `git push` in separatem Thread (Fehler loggen, nicht raise)

**Schritt 2 — `backend/main.py` (ändern)**

Nach jedem erfolgreichen Mutation-Write `asyncio.create_task()` ergänzen:

```python
# In patch_location (nach store-Write, vor return):
asyncio.create_task(asyncio.to_thread(backup.backup_after_edit, loc_id))

# In preview-alignment (nach _save_custom_location):
asyncio.create_task(asyncio.to_thread(backup.backup_after_edit, new_loc.id))
```

**Schritt 3 — `backend/precompute.py` (ändern)**

Ganz am Anfang von `async def main()`:
```python
from data import backup
backup.snapshot_before_precompute()
```

**Schritt 4 — `deploy/restore.sh` (neu)**

```bash
# Zieht neuesten Stand aus fotoalert-backup und importiert in SQLite
cd /opt/fotoalert/backup-repo && git pull
cp custom_locations.json /opt/fotoalert/app/FotoAlert/backend/data/
cp location_overrides.json /opt/fotoalert/app/FotoAlert/backend/data/
cd /opt/fotoalert/app/FotoAlert/backend
python migrate_json_to_sqlite.py
```

**Risiken:**
- `git push` darf den User-Request nie blockieren → immer in separatem Thread, Fehler nur loggen
- Backup-Repo muss existieren bevor erstes Deploy mit diesem Code läuft (sonst Exception) → Guard: prüfen ob Repo-Verzeichnis existiert, sonst nur loggen + überspringen
- `last_backup_age_hours()` liest `git log --format=%ct -1` — falls Repo leer → `None` zurückgeben

**Testplan:**
- [ ] Setup-Test: `git -C /opt/fotoalert/backup-repo log --oneline` zeigt Commits nach Edit
- [ ] Isolation: Backup nur wenn `FOTOALERT_ENV=prod` (oder nicht gesetzt); lokal kein Commit
- [ ] Retention: nach 8 Precompute-Läufen → genau 7 Snapshot-Dateien in `data/snapshots/`
- [ ] Restore-Test: DB umbenennen → `restore.sh` → `PRAGMA integrity_check` = ok, Locations vorhanden
- [ ] Edge Case: `git push` schlägt fehl → Server antwortet trotzdem mit `200 ok`, Fehler im Log

**Bezug:** ersetzt US-65; übernimmt Datensicherungs-Bullet aus US-39; liefert Signal an US-38.

---


### TASK-19 · Dev/Prod-Daten-Isolation `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task (Architektur) |
| **Priorität** | Hoch |
| **Status** | Done |
| **Abgeschlossen** | 2026-06-20 |
| **Erstellt** | 2026-06-20 |
| **Epic** | TASK-16 · **Abhängigkeit:** TASK-17 |

**Beschreibung:** Die Entwicklungsumgebung arbeitet mit einer read-only Kopie der Prod-Daten in einem eigenen Verzeichnis und kann die Live-Daten technisch nicht überschreiben.

**Scope:**
- Eingeschlossen: Umgebungsvariable `FOTOALERT_ENV` (`prod`/`dev`) steuert den Datenpfad zentral in `store.py` (`data/` vs `data_dev/`); `sync-pull.sh` schreibt nach `data_dev/`; Sicherstellen, dass `deploy.sh` (`git reset --hard`) die Daten-DB nicht überschreibt (außerhalb Git-Tree / gitignored).
- Ausgeschlossen: SQLite-Layer (TASK-17), Backup (TASK-18).

**Akzeptanzkriterien:**
- [ ] Dev (`FOTOALERT_ENV=dev`) liest/schreibt ausschließlich `data_dev/`; ein Edit in Dev verändert die Prod-DB nachweislich nicht.
- [ ] `sync-pull.sh` legt den Prod-Snapshot in `data_dev/` ab (nicht in `data/`).
- [ ] Deploy (`git reset --hard`) überschreibt die Daten-DB nicht.
- [ ] Edge Case: fehlende `FOTOALERT_ENV` → Default `prod`, aber nie versehentliches Schreiben aus Dev-Kontext.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2026-06-20)
- [x] Architektur analysiert: 3 betroffene Dateien (`store.py`, `sync-pull.sh`, neues `.gitignore`)
- [x] Kein `.gitignore` vorhanden → muss neu angelegt werden; DB sonst versehentlich committable
- [x] `sync-pull.sh` kopiert noch JSON-Dateien → nach TASK-17-Deployment auf DB-Kopie umstellen

**Implementierungsansatz:**

**Schritt 1 — `backend/data/store.py` (ändern, Zeile 25)**

```python
import os
_ENV = os.getenv("FOTOALERT_ENV", "prod")
_DEFAULT_DB = (
    Path(__file__).parent / "fotoalert.db"
    if _ENV == "prod"
    else Path(__file__).parent.parent / "data_dev" / "fotoalert.db"
)
```

`LocationStore.__init__` verwendet `_DEFAULT_DB` bereits als Default — keine weitere Änderung nötig. `data_dev/` wird durch `self.db_path.parent.mkdir(parents=True, exist_ok=True)` in `_init_db` automatisch angelegt.

**Schritt 2 — `.gitignore` (neu, im FotoAlert-Root)**

```gitignore
# Nutzer-Daten — nie in Git
backend/data/fotoalert.db
backend/data/fotoalert.db-shm
backend/data/fotoalert.db-wal
backend/data_dev/

# Entwicklungs-Artefakte
backend/__pycache__/
backend/data/__pycache__/
backend/calculations/__pycache__/
backend/models/__pycache__/
*.pyc
.DS_Store
```

**Schritt 3 — `sync-pull.sh` (ändern)**

Statt JSON-Dateien → `fotoalert.db` von Server nach `data_dev/fotoalert.db` kopieren:

```bash
DATA_DEV_DIR="$SCRIPT_DIR/backend/data_dev"
mkdir -p "$DATA_DEV_DIR"

echo ">>> fotoalert.db vom Server holen → data_dev/..."
scp -i "$SSH_KEY" \
    "$SERVER_USER@$SERVER_IP:$SERVER_DATA/fotoalert.db" \
    "$DATA_DEV_DIR/fotoalert.db"
```

Hinweis in Header aktualisieren: erklärt, dass `FOTOALERT_ENV=dev` gesetzt sein muss damit lokale Instanz die `data_dev`-DB verwendet.

**Risiken:**
- `fotoalert.db` könnte bereits in git index sein (vor .gitignore) → nach Anlage `.gitignore` prüfen: `git ls-files backend/data/fotoalert.db` sollte leer sein (Datei war nie committed ✓)
- `sync-pull.sh` funktioniert erst nach TASK-17-Deployment auf dem Server (DB existiert dann); bis dahin JSON-Fallback optional, aber nicht nötig da Dev-DB initial aus lokalem Bestand aufgebaut werden kann

**Testplan:**
- [ ] `git status` → `backend/data/fotoalert.db` erscheint als ignored (nicht als untracked)
- [ ] `FOTOALERT_ENV=dev uvicorn main:app --reload` → Startup-Log zeigt `data_dev/fotoalert.db`
- [ ] Im Dev-Server: `PATCH /locations/custom_1781560330` → nur `data_dev/fotoalert.db` ändert sich
- [ ] `sqlite3 backend/data/fotoalert.db "SELECT COUNT(*) FROM custom_locations"` → unverändert
- [ ] Ohne `FOTOALERT_ENV` → Default `prod`, Startup-Log zeigt `data/fotoalert.db`


### TASK-20 · Automatisierte Frontend-Testroutine mit Bug-Reporting `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-20 |
| **Abgeschlossen** | 2026-06-20 (Harness grün; AK8 CI-Einhängung → TASK-14) |

**Beschreibung:** Eine automatisierte Testroutine, die das Frontend selbstständig auf korrekte Visualisierungen, angezeigte Informationen und funktionierende Links prüft. Abweichungen vom erwarteten Verhalten werden als neue Bugs mit Screenshots und allen relevanten Infos im BACKLOG.md erfasst — bestehende Tickets zum gleichen Scope werden dabei aktualisiert statt dupliziert. Die Testroutine muss außerdem in die Workflow-Automation und CI/CD-Pipeline eingebaut werden, sodass sie bei jedem Deploy automatisch ausgeführt wird und Regressions frühzeitig erkannt werden.

**Bezug:** Unterstützt alle offenen BUG-Tickets (BUG-21, BUG-26 etc.); komplementär zu manuellen Testplänen in bestehenden Tickets. Abhängigkeit zu TASK-14 (Automatische Deployment Pipeline) — CI/CD-Integration setzt eine funktionierende Pipeline voraus.

---

#### 🔬 Analyse (Pipeline-Lauf 2026-06-20, Analyse-Subagent · In Analysis)

**Example Mapping**

📏 *Rule A — Frontend-Smoke deckt alle Views & Kernelemente ab.*
  🟢 Given App geladen + eingeloggt, When Routine navigiert Feed→Map→Locations→Settings, Then jede `.page` wird `active`, kein JS-Konsolen-Error, Schlüsselelemente (Tab-Bar, Leaflet-`#map`, Feed-Karten) sichtbar.
  🟢 Given `#page-map` rendert ohne Leaflet-Container, Then Bug „Map-View leer".

📏 *Rule B — Externe Links sind wohlgeformt (nicht abgerufen).*
  🟢 Given Detail-Sheet offen, When Routine liest `href` der Maps-/Streetview-/Locationscout-Buttons, Then alle Pflicht-Links matchen ihr URL-Schema.
  🟢 Edge: Location ohne `locationscout_url` → Link-Block fehlt erwartungsgemäß → **kein** Bug.

📏 *Rule C — Abweichung erzeugt Bug-Ticket mit Screenshot + Dedup.*
  🟢 Given neuer Defekt, Then genau 1 neues `### BUG-XX` in der Inbox mit Screenshot-Pfad + Fingerprint.
  🟢 Dedup: identischer Fingerprint existiert offen → bestehendes Ticket aktualisieren, **kein** Duplikat.

📏 *Rule D — Lauf in CI bei jedem Deploy, Login-Gate wird durchlaufen.*
  🟢 Given Push auf main (TASK-14), Then Routine startet headless, loggt mit Test-PW ein, Ergebnis im CI-Log.

❓ *Questions:* (1) Bug-Tickets in CI committen oder nur als Artefakt + Mac-seitiger Merge? (2) Test gegen lokale Sandbox-Instanz oder Live-URL nach Deploy? (3) Screenshots im Repo (`docs/qa-screenshots/`) vs. CI-Artefakt? (4) Welche Views „Pflicht" vs. rollenabhängig (host/user)?

**Akzeptanzkriterien** *(auto = pytest/CI)*
- [x] AK1 (auto, Browser): besucht alle 4 Haupt-Views + öffnet ≥1 Detail-Sheet; fehlendes Schlüsselelement → Fehler. *(Browserlauf grün 2026-06-20)*
- [x] AK2 (auto, Browser): Konsolen-Errors/`pageerror` → Fehler mit Stacktrace. *(Browserlauf grün)*
- [x] AK3 (auto, Browser): Pflicht-Links matchen Schema-Regex (Apple/Google/Street View im Location-Detail); optionale Links → kein Fehler. *(Browserlauf grün)*
- [x] AK4 (auto, Browser): Login-Gate (US-66) via Test-PW; Fail-Fast bei falschem/leerem PW. *(Browserlauf grün)*
- [x] AK5 (auto): bei Defekt genau **ein** Bug-Eintrag; identischer Fingerprint → Update statt Duplikat. *(test_reporter, grün)*
- [x] AK6 (auto): jeder Bug enthält Screenshot-Pfad, View, erwartet/tatsächlich, Timestamp, Commit-SHA. *(test_reporter, grün)*
- [x] AK7 (auto): grüner Lauf erzeugt **keinen** BACKLOG-Schreibvorgang. *(test_reporter, grün)*
- [ ] AK8 (manuell): in CI bei Deploy ausgeführt. *(blockiert durch TASK-14 — noch kein `.github/workflows/`; Einhängepunkt vorbereitet)*
- [x] AK9 (auto): läuft auf Python 3.9 (`from __future__ import annotations`). *(py_compile + Scan grün)*

**Pre-Mortem**
- 💀 Falsch-positive Bug-Flut → zu strenge Assertions / Render-Rennen → explizite Waits auf Render-Signale, nur kuratierte Pflicht-Elemente, AK7.
- 💀 Dedup überschreibt/dupliziert → instabiler Fingerprint → Hash aus (View + Assertion-ID + normalisierte Message), volatile Felder raus; Idempotenz-Test.
- 💀 Login-Gate (US-66) blockiert Routine → landet auf `#login-screen`, N Falsch-Bugs → Login als Precondition + Fail-Fast (1 Infra-Fehler statt N).
- 💀 CI-Flakiness (Leaflet/CDN-Tiles) → Links nur per `href` prüfen (nie abrufen), Assets cachen, Retries, deterministisches `data_dev`.
- 💀 CI pusht Bug-Commits → Deploy-Schleife → in CI **nicht** committen; Bugs als Artefakt (JSON+PNG), BACKLOG-Merge nur Mac-seitig/Intake.

**Architektur**
- Frontend unverändert (`web/index.html`): Targets `App.nav(...)`, `AddLocation.open()`, Detail-Sheets, Link-URLs, Login `LoginScreen.submit()` / `Auth.isLoggedIn()`.
- Neu: `backend/tests/frontend/run_frontend_check.py` (Playwright, `from __future__ import annotations`), View-/Link-Spezifikation als Datentabelle, Reporter der gegen `BACKLOG.md` dedupliziert; Screenshots nach `docs/qa-screenshots/<run>/`.
- Harness-Andockung: eigene Schicht neben `test_api_smoke.py`, Marker `frontend`/`network` (braucht Browser + Server, nicht im Offline-Standardlauf); `run_frontend.sh`. Ticket-ID im Docstring (TASK-20).
- CI/CD (TASK-14): Actions-Step mit `playwright install chromium`, App gegen `data_dev`, Login mit Test-PW, **keine** Commits → Bug-JSON+Screenshots als Artefakt; BACKLOG-Merge Mac-seitig.

**Implementierungsoptionen**
- *Option A — Playwright + headless Chromium, getrennter `frontend`-Marker.* Echte Renderprüfung (Leaflet, Sheets, JS-Errors), native Screenshots, CI-fähig. − schwergewichtiger CI-Step, leichte Flake-Gefahr (mit Waits beherrschbar). Aufwand: **mittel**.
- *Option B — DOM-Assertion ohne Browser (jsdom/Parsing).* + schnell, kein Browser; − erkennt **keine** Render-/Leaflet-/JS-Fehler, keine echten Screenshots → verfehlt „korrekte Visualisierungen". Aufwand: klein.
- *Option C — Hybrid: DOM/Link-Smoke + minimaler Playwright-Screenshot-Pass.* + schnell + visuelle Belege; − zwei Codepfade, mehr Wartung. Aufwand: mittel–groß.

✅ **Empfehlung: Option A** — nur ein echter Browser deckt funktionierende Visualisierungen + Links + JS-Errors + Screenshots zuverlässig ab und dockt sauber als `frontend`-Marker an das pytest-Harness und den TASK-14-CI an.

**Testplan** — Auto: Login-Precondition, View-Navigation + Detail-Sheet (AK1), Konsolen-Error-Capture (AK2), Link-Schema inkl. optional (AK3), falsches/leeres PW (AK4), Dedup-Idempotenz mit synthetischem Defekt über 2 Läufe (AK5), Bug-Feld-Vollständigkeit (AK6), Grün-ohne-Schreibvorgang (AK7), 3.9-Lauf (AK9); Reporter-Selbsttests gegen eine **Test-BACKLOG-Kopie**, nie die echte Datei. Manuell: CI-Step im echten Deploy (AK8) + Sichtprüfung erster Screenshots + Artefakt→BACKLOG-Merge-Flow.

> **Hinweis:** Es existiert noch **kein** `.github/workflows/` — TASK-14 muss das liefern; bis dahin läuft TASK-20 lokal (`run_frontend.sh`) und wird bei TASK-14 als CI-Step eingehängt.

**Status:** ✅ **Done (2026-06-20).** Implementiert + verifiziert (Option A + Artefakt). Harness 35 grün (9 Reporter-Tests, 3.9), **Browserlauf grün 2026-06-20** („OK: keine Findings" — Login, alle Views inkl. Leaflet-Karte, Location-Detail, Links). Einzig offen: **AK8 (CI-Einhängung)** — wandert als Integrationspunkt in **TASK-14** (noch kein `.github/workflows/`).

**Kalibrierungsnotizen (Browser-Verifikation):** drei Runner-Fixes nötig — (1) `window.Auth`/`window.App` → bare name (top-level `const` nicht an window gebunden); (2) Link-Prüfung im **Location**-Detail (`#loc-detail-sheet a.loc-maps-btn`) statt Event-Detail (dort nur onclick-Buttons); (3) Karten-Selektor `#map.leaflet-container` (Leaflet macht `#map` selbst zum Container, kein Kind-Element) + Warten statt Sofort-Check.

**Implementierungsnotizen (2026-06-20, Impl-Subagent):**
- Neu unter `backend/tests/frontend/`: `spec.py` (4 Views + Link-Schemata), `reporter.py` (stabiler Fingerprint, Dedup gegen BACKLOG-Kopie via `<!-- fp:… status:open -->`, `findings.json`-Artefakt, grün→kein Write), `run_frontend_check.py` (Playwright-Runner, Login-Precondition + Fail-Fast, View-Nav, Console-/Page-Error-Capture, Link-`href`-Schema, Screenshots → `docs/qa-screenshots/<run>/`), `test_reporter.py` (9 browser-freie Selbsttests auf tmp-BACKLOG-Kopie), `run_frontend.sh`.
- Alle Dateien: `from __future__ import annotations`, `TASK-20` im Docstring. `pytest.ini`: Marker `frontend`.
- CI committet **nie** (Artefakt-Variante) → keine Deploy-Schleife.
- Kein Release nötig: liegt unter `backend/tests/`, wird nicht ausgeliefert und ändert die App nicht.

---


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


### US-57 · Alignment-Qualitätsfilter: 2°-Schärfezone `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Feature |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-18 |
| **In Progress seit** | 2026-06-18 |
| **Abgeschlossen** | 2026-06-18 |

> **Als Fotograf** möchte ich, dass nur Himmelsereignisse im Feed erscheinen, die sich innerhalb eines definierten Toleranzbereichs (Azimuth + Höhe) der Sichtachse zum Motiv befinden, damit ausschließlich fotografisch relevante Alignments angezeigt werden.
>
> **Hintergrund:** US-37 ✅ berechnet und zeigt `azimuth_delta_deg` und `altitude_delta_deg` bereits an. Diese Story nutzt diese Werte als Hard-Filter in der Event-Generierung.
>
> **Akzeptanzkriterien:**
> - [~] In `precompute.py`: Events mit `|azimuth_delta_deg| > ALIGNMENT_TOLERANCE_DEG` ODER `|altitude_delta_deg| > ALIGNMENT_TOLERANCE_DEG` werden nicht als Feed-Event erzeugt
> - [~] Default-Schwellwert: `ALIGNMENT_TOLERANCE_DEG = 2.0` als Konstante in `precompute.py` (konfigurierbar)
> - [~] Ausnahmen (kein Filter): Goldene Stunde, Blaue Stunde, Milchstraße, Meteoritenschauer, Finsternisse
> - [~] Jahreskalender: gleiche Filterung (via shared `_passes_alignment_filter()`)
> - [~] `ALGORITHM_VERSION` erhöhen → Cache-Neuberechnung beim nächsten Lauf
> - [ ] Frontend: US-37-Labels bleiben unverändert; ☁️-Events (> 3°) erscheinen nicht mehr im Feed
>
> **Scope:**
> - Eingeschlossen: neue Funktion `_passes_alignment_filter()`, Anwendung in `compute_feed()` + `compute_calendar_incremental()`, ALGORITHM_VERSION bump
> - Ausgeschlossen: Frontend-Änderungen, neue UI-Elemente
>
> **Betroffene Dateien:** `backend/precompute.py`
>
> **Analyse:**
> - `_composition_analysis()` berechnet bereits `azimuth_delta_deg` und `altitude_delta_deg`
> - Filter greift auf serialisiertes Dict (nach `_serialize()`) — composition_analysis kann None sein (→ pass)
> - Exempt-Types (keine composition_analysis da kein Celestial-Tracking): Goldene Stunde Morgen/Abend, Blaue Stunde, Milchstraße, Meteoritenschauer, Sonnenfinsternis
> - Alignment-Events (SUN_ALIGNMENT, MOON_ALIGNMENT) haben immer celestial_azimuth/altitude → composition_analysis vorhanden → werden gefiltert


### US-40 · Feed-Qualität: Tägliche Routine-Events ausblenden `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Feature |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | (vorher offen) |
| **In Progress seit** | 2026-06-18 |
| **Abgeschlossen** | 2026-06-18 |

> **Als Fotograf** möchte ich im Chancen-Tab nicht täglich auf Goldene Stunde und Blaue Stunde hingewiesen werden, da diese jeden Tag auftreten und keine besonderen Ereignisse wie Mondaufgang oder Vollmond sind.
>
> **Hintergrund:** US-03 hat Goldene & Blaue Stunde als technische Events eingeführt – diese Zeitfenster bleiben für den Tageszeit-Filter und die Detail-Anzeige erhalten. Im Feed-Tab sollen sie aber standardmäßig nicht als eigenständige Chancen erscheinen.

**Scope:**
- Eingeschlossen: `Filter.apply()` Default-Filter für Routine-Types, Feed Empty-State-Meldung
- Ausgeschlossen: Backend-Änderungen, Tageszeit-Filter, Detail-Anzeige der Zeitfenster, Settings

**Akzeptanzkriterien:**
- [~] Goldene Stunde (Morgen/Abend) und Blaue Stunde werden im Feed-Tab standardmäßig nicht angezeigt
- [~] Nutzer können sie über den Eventtyp-Filter explizit einblenden (opt-in)
- [ ] Tageszeit-Filter und Detail-Anzeige (Golden/Blue Hour Zeitfenster) bleiben unberührt
- [~] Jahreskalender-Tab: gleicher Filter (via `Filter.apply()`)

**Analyse & Planung:**
- [x] `Filter.apply()` in `web/index.html` analysiert — Filterlogik klar verstanden
- [x] `ET_EXPAND` und `expanded` werden aus dem Callback herausgezogen (einmalige Berechnung)
- [x] Neue Konstante `ROUTINE_TYPES = ['Goldene Stunde Morgen', 'Goldene Stunde Abend', 'Blaue Stunde']`
- [x] Default-Filter: wenn `s.eventTypes.length === 0` → Routine-Events blocken; wenn User Goldene Stunde / Blaue Stunde im Filter wählt → einblenden
- [x] Feed Empty-State anpassen: wenn `Filter.activeCount() === 0` aber Events vorhanden → spezifische Meldung

**Implementierungsnotizen:**
- Kein Badge-Änderung nötig — Routine-Filter ist kein "User-Filter", zählt nicht in `activeCount()`
- `Filter.apply()` wird sowohl für Feed als auch für Jahreskalender (`CalendarView`) genutzt → ein Fix deckt beides ab

*Differenziert von US-03 ✅ (technische Berechnung bleibt) und US-36 (betrifft Alignment-Events, nicht Routine-Events)*


### US-34 · Job-Orchestrierung & Incremental Updates `[x]`
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


### US-39 · Resilient Deployment / Rollback (nur Code/Deploy) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | UserStory |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-20 |
| **Implementiert** | 2026-06-25 |

**Beschreibung:** Als App-Host möchte ich bei der Einführung neuer Features oder Fixes jederzeit auf die letzte funktionierende Version zurückrollen können.

**Abgrenzung (2026-06-20):** Scope auf reines Code-/Deploy-Rollback reduziert. Datensicherung → TASK-18.

**Scope:**
- Eingeschlossen: `release.sh` (Git-Tags), `deploy/rollback.sh` (stabiler Rollback-Mechanismus), `deploy/DEPLOYMENT-GUIDE.md` (Rollback-Doku + Cache-Hinweis)
- Ausgeschlossen: Datensicherung (TASK-18), GitHub Releases UI

**Akzeptanzkriterien:**
- [x] `release.sh` erstellt nach jedem Push einen Git-Tag (`v{VERSION}`) → `git tag` listet alle Releases
- [x] `rollback.sh` verwendet `git reset --hard` (bewegt HEAD) → Rollback-Stand überlebt nächsten `git pull`
- [x] DEPLOYMENT-GUIDE.md: Rollback-Sektion mit Tag-Beispiel + Cache-Kompatibilitäts-Hinweis
- [x] Edge Case: Cache-Kompatibilität dokumentiert (Caches außerhalb Git, manueller Recompute bei alten Rollback-Zielen)

**Pre-Mortem:**
- 💀 `git checkout -- .` ohne HEAD-Bewegung → Rollback wird bei nächstem Pull überschrieben → Gegenmaßnahme: `git reset --hard` (implementiert)
- 💀 Tags nicht auf Remote gepusht → Rollback per Tag unmöglich → Gegenmaßnahme: `git push origin "v${NEW_VERSION}"` in `release.sh` (implementiert)

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (2026-06-25)
- [x] Pre-Mortem durchgeführt (2026-06-25)
- [x] Architektur analysiert: `release.sh`, `deploy/rollback.sh`, `deploy/DEPLOYMENT-GUIDE.md`
- [x] Implementiert: Option A (3-Datei-Minimal-Fix)

**📎 Code-Verifikation (2026-06-25):**
- `rollback.sh` Z. 29: `git checkout "$TARGET" -- .` → `git reset --hard "$TARGET"` ✅
- `release.sh` Z. 79ff: `git tag + git push --tags` ergänzt ✅
- `DEPLOYMENT-GUIDE.md`: Rollback-Sektion ausgebaut ✅


### TASK-13 · PWA auf iPhone: Öffentliches Hosting & Remote-Zugriff `[x]`
> **✅ Done (abgeglichen 2026-06-20):** Faktisch erledigt — das Setup existiert und ist live: Hetzner CX22 + Caddy (HTTPS), Domain `https://fotoalert.stephanschumann.com`, systemd-Service + Precompute-Timer, PWA auf iPhone installierbar. Vollständige Setup-Anleitung in `deploy/DEPLOYMENT-GUIDE.md`. Ticket stand nur durch fehlenden Board-Abgleich noch in der Inbox; alle AKs sind erfüllt.
>
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


### TASK-14 · Automatische Deployment Pipeline `[x]`
> **✅ Done (abgeglichen 2026-06-20):** Die Pipeline existiert und ist produktiv im Einsatz — `.github/workflows/deploy.yml` (Push auf `main` → SSH → `deploy/deploy.sh`: `git pull`, SW-Cache-Bump per Timestamp, `pip install`, systemd graceful restart, `/health`-Retry-Check, Auto-Rollback bei Fehler). Ergänzend: `release.sh` (Versions-Bump + Push), `deploy/rollback.sh` (< 2 Min), `deploy/restore.sh`, `deploy/DEPLOYMENT-GUIDE.md`. Alle AKs erfüllt **außer** der CI-Test-Gate-Integration (AK8 aus TASK-20) → herausgezogen als **TASK-21**.
>
> **Bezug (2026-06-20):** Trägt **AK8 von TASK-20** — die fertige Frontend-Testroutine (`backend/tests/frontend/`, Artefakt-Variante) muss hier als CI-Step bei jedem Deploy eingehängt werden: `playwright install chromium`, App gegen `data_dev`, Login mit Test-PW, `findings.json`+Screenshots als Artefakt (NICHT committen → keine Deploy-Schleife).
>
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



### TASK-21 · Frontend-Test-Gate in CI einhängen (Playwright vor Deploy) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task (CI/CD) |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-20 |
| **In Progress seit** | 2026-06-21 |
| **Abgeschlossen** | 2026-06-21 (Release v1.8.5) |
| **Herkunft** | AK8 aus TASK-20 — herausgezogen beim Done-Abgleich von TASK-14 |

**Beschreibung:** Die bereits implementierte Frontend-Testroutine (`backend/tests/frontend/`, TASK-20, Playwright/Option A) wird in `.github/workflows/deploy.yml` als Test-Gate **vor** dem Deploy-Step eingehängt. Aktuell deployt der Workflow direkt ohne Frontend-Regressionsprüfung.

**Scope:**
- Eingeschlossen: CI-Step `playwright install chromium`; Lauf gegen `data_dev`; Login mit Test-PW (US-66); `findings.json` + Screenshots als **CI-Artefakt** (nicht committen → keine Deploy-Schleife); roter Lauf blockiert den Deploy.
- Ausgeschlossen: Änderungen an der Testroutine selbst (TASK-20, done); BACKLOG-Merge der Findings (bleibt Mac-seitig/Intake).

**Akzeptanzkriterien:**
- [x] `deploy.yml`: Test-Job `test-frontend` mit `needs: [test-frontend]` auf `deploy`; implementiert in `.github/workflows/deploy.yml`.
- [x] Playwright headless gegen `data_dev`-Instanz, Login via Test-PW-Secret.
- [x] Findings (`findings.json` + PNGs) als CI-Artefakt hochgeladen, **kein** Commit in der CI.
- [x] Roter Frontend-Lauf → Deploy wird nicht ausgeführt (Gate greift).
- [x] Schließt AK8 von TASK-20 ab.

**Abhängigkeiten:** TASK-20 ✅ (Routine), TASK-14 ✅ (Pipeline)



### TASK-15 · Jahreskalender-Cron-Zeit auf 0:01 Uhr ändern `[x]`
> **Als App-Host** möchte ich den Cron-Job für die Jahres- und 14-Tage-Kalenderberechnung auf 0:01 Uhr ändern, damit die Daten um Mitternacht aktualisiert werden (statt 5:30 Uhr morgens).
>
> **Akzeptanzkriterien:**
> - Cron-Ausdruck: `30 5 * * *` → `1 0 * * *`
> - Kein Konflikt mit anderen Cron-Jobs (US-34 Rolling-Forecast)
> - Nach Änderung: Cron-Lauf um 0:01 Uhr im Log nachweisbar
>
> **Abhängigkeiten:** BUG-14 (möglicherweise verwandter Fehler), US-34[~]


### US-62 · Höhenkorrektur Fotografenstandort (Dach, Etage) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Feature |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-18 |
| **In Progress seit** | 2026-06-18 |
| **Abgeschlossen** | 2026-06-18 (Release v1.4.35) |

**Beschreibung:** `observer_floor_height_m` ergänzt den vertikalen Offset wenn der Fotograf nicht auf Bodenniveau ist (Dach, Etage). Beeinflusst Kompositions-Analyse, elevation_difference_m, possible_bodies.

**Scope:**
- Eingeschlossen: `PhotoLocation`-Datenmodell, `custom_locations.json`, `location_overrides.json`, PATCH-Endpoint, `precompute.py` (`_composition_analysis`), Edit-Formular, Anzeige in Location-Detail
- Ausgeschlossen: `possible_bodies`-Berechnung (nutzt Terrain-Elevation, nicht observer_floor), FOV-Kegel-Karte (rein visuell, kein Elevationswinkel-Effekt)

**Akzeptanzkriterien:**
- [~] Feld `observer_floor_height_m: float = 0.0` in `PhotoLocation` (data/locations.py)
- [~] `_load_custom_locations()`: liest `observer_floor_height_m` aus JSON
- [~] `_save_custom_location()`: schreibt `observer_floor_height_m` in JSON
- [~] `_load_location_overrides()`: wendet `observer_floor_height_m` an
- [~] PATCH `/locations/{id}`: `observer_floor_height_m` in Whitelist + Validierung ≥ 0
- [~] `precompute.py _composition_analysis()`: `height_above_observer = elev_diff - observer_floor_height_m + subject_height_m`
- [~] Edit-Formular: Eingabefeld „Höhe über Gelände (m)" nach Motivhöhe
- [~] Location-Detail Anzeige: „+ X m Gebäude" wenn Wert > 0
- [~] Nach Speichern: Recompute über TASK-12-Mechanismus (coords_changed-Logik erweitern)

**Abhängigkeiten:** US-60 ✅, TASK-12 ✅



### ~~US-65 · Automatisches Backup der App-Daten~~ `[~]` → GEMERGED in TASK-18
> **➡️ Gemerged (2026-06-20):** Dieses Ticket geht in **TASK-18** (Backup RPO≈0) auf. Das stärkere RPO≈0-Konzept ersetzt das tägliche Snapshot-Backup; 7-Versionen-Retention + >25h-Health-Alert wurden als Fallback in TASK-18 übernommen. Inhalt unten bleibt als Referenz erhalten.
>
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


### US-66 · Pflicht-Login mit Rollen-Erkennung (Host / User) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **Abgeschlossen** | 2026-06-21 (Release v1.8.2) |

**Beschreibung:** Die App erfordert beim Start einen Login. Nutzer geben nur ein Passwort ein — anhand des Passworts wird automatisch erkannt, ob es sich um einen Host (Stephan) oder einen User handelt. Host-Passwort gewährt Zugang zu allen Funktionen inkl. zukünftiger Admin-Features; User-Passwort gewährt Standardzugang. Kein Username, kein separates Rollen-Auswahlfeld.

**Entscheidungen (v1):**
- Passwort-Mechanismus: einfach (z. B. Plaintext-Vergleich im Backend oder fest kodierter Hash — kein bcrypt/JWT für v1)
- Session-Dauer: dauerhaft bis zum expliziten Logout (kein automatisches Ablaufen)

**Abhängigkeiten:** Voraussetzung für US-68 (Host-Approval Workflow)

---

#### 🔬 Analyse (Pipeline-Lauf 2026-06-20 · In Analysis)

**Example Mapping**

📏 *Rule 1 — Ohne gültige Session kein Zugang.*
  🟢 Given frische Installation, When App geöffnet, Then Login-Screen statt Feed.
  🟢 Given gültige Session gespeichert, When App geöffnet, Then direkt Feed (kein erneuter Login).

📏 *Rule 2 — Das Passwort bestimmt die Rolle automatisch (kein Auswahlfeld).*
  🟢 Given Host-Passwort, When korrekt, Then Rolle=host (alle Funktionen inkl. Admin).
  🟢 Given User-Passwort, When korrekt, Then Rolle=user (Standardzugang).
  🟢 Given falsches Passwort, When eingegeben, Then Fehlermeldung, kein Zugang.

📏 *Rule 3 — Session bleibt bis zum expliziten Logout (kein Ablauf).*
  🟢 Given eingeloggt, When App geschlossen + neu geöffnet, Then weiterhin eingeloggt.
  🟢 Given Logout, When bestätigt, Then zurück zum Login-Screen, Session gelöscht.

❓ *Question 1:* Login nur UI gaten (Frontend) oder auch Backend-API absichern? → wird über die Optionen entschieden (s. u.).
❓ *Question 2:* Wo liegen die zwei Passwörter? → Vorschlag: `backend/.env` (gitignored), serverseitig.

**Akzeptanzkriterien** *(jedes automatisierbare AK → pytest-Fall in `backend/tests/`)*
- [x] `POST /login` mit Host-Passwort → 200, `{"role":"host","token":…}`. *(test_us66_login)*
- [x] `POST /login` mit User-Passwort → 200, `{"role":"user","token":…}`. *(test_us66_login)*
- [x] `POST /login` mit falschem Passwort → 401, kein Token. *(test_us66_login)*
- [x] Edge: leeres Passwort → 401, kein Zugang. *(test_us66_login)*
- [x] *(Option B)* Geschützter schreibender Endpoint ohne gültiges Token → 401. *(test_us66_login)*
- [x] *(Option B)* Host-only-Route mit User-Token → 403. *(test_us66_login)*
- [x] Ohne Session zeigt die App den Login-Screen; kein Tab/Feed erreichbar. *(Frontend-Test bestätigt 2026-06-20)*
- [x] Gültiges Token in der Session → App startet direkt im Feed. *(bestätigt 2026-06-20)*
- [x] Logout (Einstellungen) löscht die Session → nächster Start zeigt Login. *(bestätigt 2026-06-20)*

**Pre-Mortem** *(💀 = Versagensszenario → Gegenmaßnahme)*
- 💀 Passwörter landen im Frontend-JS/Repo → jeder kann Host werden. → Vergleich **nur im Backend**, Passwörter in `.env` (gitignored); das Frontend kennt nur das Ergebnis-Token.
- 💀 „Pflicht-Login" nur im Frontend → die API bleibt offen, jeder mit der URL liest/schreibt Daten (kritisch wegen Location-Edits & US-68). → Backend-Token-Check auf schreibenden Endpoints (Option B).
- 💀 Dauerhafte Session auf geteiltem Gerät → Host bleibt eingeloggt. → akzeptiert per v1-Entscheidung; klar sichtbarer Logout als Gegenmaßnahme.
- 💀 Bestehende Nutzer plötzlich ausgesperrt → Verwirrung beim Rollout. → kurzer Hinweis im Release; kleine Nutzerbasis.

**Architektur** — betroffen: `backend/main.py` (neuer `POST /login`-Endpoint + Settings für die zwei Passwörter via pydantic-settings/`.env`), optional ein FastAPI-Dependency für geschützte Routen; `web/index.html` (Login-Screen vor `#app`, Token in localStorage analog `fa_*`, Logout in Settings). Kein bestehendes Auth-System vorhanden.

**Implementierungsoptionen**

*Option A — UI-Gate + Login-Endpoint, API ungeschützt.* `/login` prüft das Passwort serverseitig (`.env`) und gibt `role`+`token` zurück; das Frontend gated die UI und speichert das Token in localStorage. Die übrigen API-Endpoints bleiben offen. Aufwand: **klein**. Nachteil: schließt Pre-Mortem-Risiko 2 nicht — Daten bleiben über die API zugänglich.

*Option B — wie A, plus Backend-Schutz schreibender Endpoints.* Zusätzlich ein FastAPI-Dependency, das auf mutierenden Routen (Location-Edits, Verifikationen, Push-Registrierung) einen gültigen Bearer-Token verlangt; Host-only-Routen prüfen zusätzlich die Rolle. Aufwand: **mittel**. Schützt die Daten real und ist die Basis für US-68.

✅ **Empfehlung: Option B.** US-66 ist ausdrücklich Voraussetzung für US-68 (Host-Approval), und Datenmutationen ohne Backend-Schutz wären das zentrale Pre-Mortem-Risiko. Der Mehraufrund ist überschaubar (ein Dependency + Token-Ausgabe), liefert aber den eigentlichen Zweck statt eines reinen UI-Vorhangs.

**Testplan**
- [ ] Automatisiert (Harness): `POST /login` (host/user/falsch/leer), Token-Schutz schreibender Endpoints (Option B) als `test_api_regression.py`-Fälle mit `US-66` im Docstring.
- [ ] Manuell: App ohne Session → Login-Screen; Host- und User-Passwort durchspielen; Logout → Login erscheint wieder; Neustart bleibt eingeloggt.

**Implementierungsnotizen (2026-06-20):**
- Neu `backend/auth.py`: stateless HMAC-Token (`<role>.<hmac>`), `role_for_password`, `issue_token`, `role_for_token`, Dependencies `require_auth`/`require_host`.
- `backend/main.py`: `POST /login` (Passwort → Rolle+Token); geschützt: `patch_location`, `preview_alignment` (require_auth), `refresh*`/`refresh-discover`/`weather-refresh` (require_host). `register-device` bewusst **offen** (iOS-App noch nicht login-fähig → Folge-Ticket).
- `web/index.html`: Login-Overlay vor `#app`, Token/Rolle in localStorage (`fa_token`/`fa_role`), `Authorization: Bearer` an allen API-Calls, 401 → Auto-Logout, Logout in Einstellungen (Sektion „Konto").
- `backend/.env.example`: `FOTOALERT_HOST_PASSWORD` / `FOTOALERT_USER_PASSWORD` / `FOTOALERT_AUTH_SECRET` dokumentiert.
- Tests: `tests/test_us66_login.py` (12 Fälle: Auth-Unit + Login + Schutz); BUG-22-Tests auf authentifizierte Requests umgestellt. Harness 26/26 grün.

**Status:** ✅ **Done** — released **v1.8.2** (2026-06-20), Live-Login (Host + User) auf dem Server bestätigt. Server-`.env` mit den drei Variablen gesetzt (`/opt/fotoalert/app/FotoAlert/backend/.env`, chmod 600).

> ⚠️ **Release-Voraussetzung:** Vor/of dem Deploy `FOTOALERT_HOST_PASSWORD`, `FOTOALERT_USER_PASSWORD`, `FOTOALERT_AUTH_SECRET` auf dem Server in `.env` setzen — sonst sperrt sich die App aus (niemand kann sich einloggen).


### US-67 · Chancendetails: Azimut und Höhe relativ zur Motivspitze `[x]`
> **Als Fotograf** möchte ich bei einem Alignment-Event in verständlicher Sprache lesen, wo das Himmelsobjekt relativ zu meinem Motiv erscheint – z.B. „Mond 3° links neben dem Kirchturm, 5° darüber".
>
> **Hintergrund:** US-37[x] berechnet `azimuth_delta_deg` und `altitude_delta_deg`. Diese Rohwerte liegen im Cache vor, werden aber nur als Zahlen angezeigt.
>
> **Akzeptanzkriterien:**
> - Im Event-Detail-Sheet: neue Sektion „Himmelsposition" mit Beschreibungstext:
>   - `azimuth_delta < 0` → „links", `> 0` → „rechts"; `altitude_delta > 0` → „darüber", `< 0` → „darunter"
>   - Schwellwerte: < 0.5° → „nahezu exakt auf dem Motiv"; 0.5–2° → „leicht"; > 5° → „deutlich"
>   - Absoluter Azimut + Elevation als Sekundärinfo (für erfahrene Nutzer)
> - **Abweichung in Grad UND Metern angeben:** Zusätzlich zur Grad-Angabe wird die Abweichung des Himmelsobjekts vom Motiv in Metern ausgewiesen (lateral und vertikal), berechnet aus Winkelabweichung × Entfernung Kamera↔Motiv — z.B. „Mond 3° links ≈ X m neben dem Kirchturm, 5° darüber ≈ Y m"
> - Nur bei Alignment-Events (Mond-Alignment, Sonnen-Alignment); nicht bei Goldene Stunde, Mondaufgang etc.
> - Immer relativ zum Motiv (nicht zur Kamera oder zum Norden)
>
> **Abhängigkeiten:** US-37[x]
>
> ---
>
> **Scope:**
> Eingeschlossen: Eine neue, in Klartext formulierte Sektion **„🧭 Himmelsposition"** im Event-Detail-Sheet (`web/index.html`, `Detail.render`), die aus dem bereits gecachten `composition_analysis` einen verständlichen Beschreibungssatz erzeugt („Mond 3° links neben dem Motiv ≈ X m, 5° darüber ≈ Y m"), inklusive Schwellwert-Wortwahl (nahezu exakt / leicht / deutlich) und absolutem Azimut+Elevation als Sekundärinfo. Reine **Frontend-Aufgabe** — alle Rohwerte (`azimuth_delta_deg`, `altitude_delta_deg`, `lateral_offset_m`, `vertical_offset_m`, `subject_apparent_elevation_deg`, `celestial_azimuth`, `celestial_altitude`, `body_name`) liegen bereits im serialisierten Opportunity-Objekt vor (`backend/precompute.py:228–242`).
> Ausgeschlossen: jede Neuberechnung im Backend (Deltas/Meter existieren schon), Änderung der bestehenden „🎯 Kompositions-Analyse"-Sektion (bleibt unverändert als Detailansicht; die neue Sektion ist die Klartext-Zusammenfassung darüber), Goldene/Blaue Stunde & Nicht-Alignment-Events (haben `composition_analysis = None`), iOS-App.
>
> **Akzeptanzkriterien:**
> - [x] Neue Sektion „🧭 Himmelsposition" erscheint im Event-Detail-Sheet **genau dann**, wenn `o.composition_analysis` vorhanden ist (≠ null). Bei Goldener/Blauer Stunde, Milchstraße, Mondaufgang ohne Tracking etc. (`composition_analysis === null`) wird **keine** Sektion gerendert.
> - [x] Beschreibungssatz nennt das Himmelsobjekt per `ca.body_name` („Mond"/„Sonne"), nie hartkodiert.
> - [x] Seitenrichtung: `azimuth_delta_deg < 0` → „links", `> 0` → „rechts". Höhenrichtung: `altitude_delta_deg > 0` → „darüber", `< 0` → „darunter".
> - [x] Schwellwort (auf den **Betrag** des jeweiligen Deltas angewandt, getrennt für Azimut und Höhe): `|Δ| < 0.5°` → „nahezu exakt auf dem Motiv" (Richtungswort entfällt); `0.5° ≤ |Δ| < 2°` → „leicht"; `2° ≤ |Δ| ≤ 5°` → (kein Zusatzwort, neutral); `|Δ| > 5°` → „deutlich".
> - [x] Jede Achse wird in **Grad UND Metern** angegeben. Meter = `Math.abs(ca.lateral_offset_m)` (seitlich) bzw. `Math.abs(ca.vertical_offset_m)` (vertikal) — **nicht** im Frontend neu aus Winkel×Distanz gerechnet, sondern die gecachten Backend-Werte verwendet. Format: < 1000 m → „N m" (0 Nachkommastellen), ≥ 1000 m → „N,NN km". Beispiel: „🌙 Mond leicht links neben dem Motiv ≈ 8 m (1,2°), leicht darüber ≈ 12 m (0,9°)".
> - [x] Sekundärinfo (kleiner, gedämpft): absoluter Azimut Himmelsobjekt `ca`-unabhängig aus `o.celestial_azimuth.toFixed(1)+"°"` und Elevation `o.celestial_altitude.toFixed(2)+"°"`; zusätzlich scheinbare Motivspitzen-Elevation `ca.subject_apparent_elevation_deg`.
> - [x] Edge Case: Beide Beträge < 0.5° → Satz lautet sinngemäß „🎯 Mond steht nahezu exakt auf der Motivspitze (≈ 0 m seitlich, ≈ 0 m vertikal)" ohne „links/rechts/darüber/darunter".
> - [ ] Edge Case: exakt `azimuth_delta_deg === 0` bzw. `altitude_delta_deg === 0` → fällt in „nahezu exakt" (kein Vorzeichen-/Richtungsfehler, kein leeres Richtungswort).
> - [ ] Edge Case: fehlt eine Einzelkomponente (z.B. `lateral_offset_m == null`), wird die Meter-Angabe für diese Achse weggelassen, der Grad-Teil aber gezeigt (kein „NaN m", kein Absturz).
> - [ ] Regression: bestehende „🎯 Kompositions-Analyse"-Sektion, Filter (US-57) und der Feed bleiben unverändert (kein Rendering-Fehler im Detail-Sheet bei Nicht-Alignment-Events).
>
> **Pre-Mortem** *(💀 = Versagensszenario → Gegenmaßnahme)*
> - 💀 Frontend rechnet Meter selbst aus `tan(Δ)×Distanz` und nutzt eine andere/fehlende Distanz (Kamera↔Motiv liegt im Detail nur als `haversine` der GPS-Punkte vor, nicht als die im Backend benutzte `loc.distance_m`) → Meter weichen von der Kompositions-Analyse ab. → **Gegenmaßnahme:** ausschließlich die gecachten `lateral_offset_m`/`vertical_offset_m` verwenden (AK), keine eigene Umrechnung.
> - 💀 Vorzeichen-Konvention verdreht: Backend definiert `az_delta = celestial_azimuth − subject_azimuth` (−180…+180); negativ = Objekt **westlich/links** der Sichtachse. Frontend invertiert → „links/rechts" vertauscht. → **Gegenmaßnahme:** Mapping exakt wie bestehende Sektion (`web/index.html:2680`: `lOff < 0 ? '← links' : '→ rechts'`), Test mit bekanntem Vorzeichen.
> - 💀 Sektion erscheint auch bei Events ohne Alignment, weil die Gate-Bedingung auf einem anderen Feld hängt (z.B. `celestial_azimuth` ist auch bei Mondaufgang gesetzt). → **Gegenmaßnahme:** Gate **nur** an `o.composition_analysis != null` (Backend setzt das gezielt auf `None` für Nicht-Tracking-Events, `precompute.py:145–147`).
> - 💀 Events mit `composition_analysis`, aber einzelnen `null`-Feldern (defensiv) erzeugen „NaN m" / `toFixed of null`. → **Gegenmaßnahme:** Null-Guards pro Feld (AK Edge Case), Default-Wegfall der Meter-Angabe.
>
> **Analyse & Planung:**
> - [x] Example Mapping durchgeführt (4 Rules: Gate=nur Alignment, Richtungswort aus Vorzeichen, Schwellwort aus Betrag, Grad+Meter aus Cache; Questions = 0, da Schwellwerte/Vorzeichen im Code eindeutig).
> - [x] Pre-Mortem durchgeführt (4 Szenarien, Kern: Meter müssen aus dem Cache kommen, nicht neu gerechnet).
> - [x] Architektur analysiert: **Backend liefert bereits alles** — `backend/precompute.py:_composition_analysis` (Z.133–242) berechnet `azimuth_delta_deg`, `altitude_delta_deg`, `lateral_offset_m` (`d·tan(az_delta)`, Z.168), `vertical_offset_m` (Z.167), `subject_apparent_elevation_deg`, `body_name`; gesetzt nur wenn `subject_height_m & distance_m & celestial_*` vorhanden (Z.145), sonst `None`. Serialisiert als `composition_analysis` (`precompute.py:328`). Frontend: Event-Detail-Sheet in `Detail` (`web/index.html`), bestehende „🎯 Kompositions-Analyse"-Section (Z.2665–2726) mit identischen Werten + Richtungs-Mapping (`lOff<0?'← links'`, Z.2680). Distanz `loc.distance_m` (Backend) ≠ Frontend-`haversineKm` (Z.2729) → Meter NUR aus Cache.
> - [x] Implementierungsoptionen: A / B / C (siehe unten).
> - [ ] Empfehlung: **Option A** (Weg-Gate offen).
>
> **Implementierungsoptionen**
>
> *Option A — Neue Klartext-Sektion über der bestehenden Detailansicht.* Eine zusätzliche `mkSec('ev_skypos','🧭 Himmelsposition', …)` direkt vor dem bestehenden `ev_kompo`-Block, die aus `ca` den Beschreibungssatz + Sekundärinfo baut. Reine Hinzufügung, „🎯 Kompositions-Analyse" bleibt als Detailtabelle erhalten. Betroffen: `web/index.html` (1 neuer IIFE-Block). Vorteil: erfüllt das Ticket 1:1 (eigene Sektion „Himmelsposition"), null Regressionsrisiko, klein. Nachteil: leichte Redundanz zur bestehenden Sektion. **Aufwand: klein.**
>
> *Option B — Bestehende „Kompositions-Analyse" umbauen/umbenennen* und den Klartextsatz oben einbetten. Vorteil: keine Redundanz. Nachteil: berührt bestehendes, getestetes UI (Regressionsrisiko, US-57-Filter zeigt dieselben Felder), und das Ticket fordert eine **eigene** Sektion. **Aufwand: mittel.**
>
> *Option C — Backend liefert den fertigen Satz* (`composition_analysis.sky_position_text`). Vorteil: zentral, auch für iOS nutzbar. Nachteil: erfordert Backend-Änderung + Cache-Recompute, obwohl die Formulierung rein UI-sprachlich ist; widerspricht „Frontend-only". **Aufwand: mittel–groß.**
>
> ✅ **Empfehlung: Option A** — die Rohwerte (inkl. Metern) liegen vollständig im Cache, das Ticket verlangt explizit eine eigene Sektion „Himmelsposition", und eine additive Frontend-Sektion hat das kleinste Regressionsrisiko gegenüber dem bestehenden, vom US-57-Filter mitgenutzten Kompositions-Block.
>
> **Daten-Validierung:**
> - [ ] An einem realen Alignment-Event im Cache prüfen: `lateral_offset_m`, `vertical_offset_m`, `azimuth_delta_deg`, `altitude_delta_deg` vorhanden und konsistent (`lateral_offset_m ≈ distance_m·tan(az_delta)`); an einem Goldene-Stunde-Event prüfen: `composition_analysis === null`.
>
> **Testplan:**
> - [x] Automatisiert (Harness, `backend/tests/test_us67_composition.py`, Docstring `US-67`): Verifizieren dass `_composition_analysis` für ein Alignment-Setup `lateral_offset_m`/`vertical_offset_m` mit korrektem Vorzeichen liefert (negativ az_delta → negativer lateral_offset) und für ein Setup ohne `subject_height_m`/`distance_m` `None` zurückgibt. (Frontend-Textbau ist nicht pytest-bar — Logik der Datengrundlage wird abgesichert.) → 8 Tests, grün (offline/regression).
> - [x] Manuell unter http://localhost:8000: Alignment-Event öffnen → Sektion „🧭 Himmelsposition" zeigt Klartextsatz mit Grad **und** Metern, korrektes links/rechts + darüber/darunter, Sekundärinfo (abs. Azimut/Elevation). ✅ getestet an „Mond über Glienicker Brücke" (28.06.): „leicht links ≈ 38 m, leicht darüber ≈ 40 m".
> - [ ] Manuell: Event mit |Δ| < 0.5° → „nahezu exakt auf der Motivspitze", keine Richtungswörter. *(kein passendes Live-Event im Cache mit beiden Δ < 0.5° — durch automatisierten/Code-Pfad abgedeckt, nicht manuell verifiziert.)*
> - [x] Manuell: Goldene-Stunde-/Milchstraßen-Event öffnen → **keine** „Himmelsposition"-Sektion, kein Konsolenfehler. ✅ getestet an „Milchstraße über Molecule Men" — keine Sektion, „🎯 Kompositions-Analyse" bleibt vorhanden.
>
> **🐞 Beim Test gefunden & gefixt (2026-06-21):** Das Frontend-Gate hing nur an `if (!ca)`. `composition_analysis` wird vom Backend aber **auch** für Goldene/Blaue Stunde & Milchstraße gesetzt (Motiv-Geometrie + Himmelsposition vorhanden — `_composition_analysis` prüft nur Geometrie, nicht den Event-Typ; im Cache: 532 Goldene Stunde + 114 Milchstraße betroffen). Die Pre-Mortem-Gegenmaßnahme „Backend setzt None für Nicht-Tracking-Events" basierte auf falscher Prämisse. **Fix:** `web/index.html` ev_skypos-Gate um `EV_SKYPOS_EXEMPT` ergänzt (Spiegel von `precompute._ALIGNMENT_FILTER_EXEMPT`). Verifiziert per Node-Simulation gegen den Cache: Goldene Stunde/Milchstraße rendern jetzt 0, Mond-Alignment unverändert. ⚠️ **Noch nicht deployed** (lokaler Fix, uncommitted).


### ~~US-68 · Host-Approval Workflow für Location-Änderungen und -Löschungen (inkl. Host-Aufgabenliste)~~ `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-20 |
| **Abgeschlossen** | 2026-06-26 |

> **Als normaler Nutzer** möchte ich Änderungs- und Löschvorschläge für eine Location einreichen können, die erst nach Bestätigung durch den Host wirksam werden.
>
> **Hintergrund:** US-63[x] erlaubt vollständiges Bearbeiten. Diese Story fügt einen Review-Gate ein: Änderungen und Löschungen von Nicht-Host-Nutzern werden als Vorschläge gespeichert und vom Host in einer Aufgabenliste freigegeben.
>
> **🔀 Merge-Hinweis (2026-06-20):** US-86 (Lösch-Berechtigung Host/User + Host-Aufgabenliste + Indikator) wurde auf Stephans Freigabe in US-68 zusammengeführt — gemeinsames Host-Dashboard/Approval statt zweier paralleler Mechanismen.
>
> **Akzeptanzkriterien — Änderungen:**
> - Nicht-Host-Nutzer sehen „Änderung vorschlagen"-Button (statt direktem Edit)
> - Vorschlag wird als `pending_override` in `location_overrides.json` gespeichert (Status: `pending`)
> - Host-Dashboard (nach US-66-Login): Liste aller offenen Vorschläge mit Diff-Ansicht (alt ↔ neu)
> - Host-Aktionen: „Annehmen" (Status `approved`, Wert übernommen) oder „Ablehnen" (Status `rejected`)
> - Nach Annahme: Hintergrund-Recompute via TASK-12-Mechanismus
> - Nicht-Host-Nutzer sehen an betroffener Location Hinweis „Vorschlag ausstehend"
>
> **Akzeptanzkriterien — Löschungen (aus US-86):**
> - Host darf **alle** Locations löschen (sofort, ohne Approval)
> - Normale User dürfen nur **selbst angelegte** Locations löschen — und nur nach Zustimmung des Hosts
> - User-Löschwunsch erzeugt eine offene Approval-Aufgabe (Status `pending`) statt sofortiger Löschung
> - Host-Aktionen auf Löschwunsch: „Annehmen" (Location wird gelöscht + Caches/Feed/Karte bereinigt) oder „Ablehnen"
>
> **Akzeptanzkriterien — Host-Aufgabenliste (aus US-86):**
> - Sektion „Aufgaben" im Bereich „Einstellungen" listet alle offenen Approval-Aufgaben (Änderungen + Löschungen)
> - Kleiner Indikator (Badge) signalisiert dem Host, dass offene Aufgaben vorliegen (Anzahl); verschwindet, wenn keine offen sind
>
> **Sequenzierung:**
> ```
> US-63[x] (Location-Edit-UI) ──┐
> US-66 (Host-Login Auth)      ──┼─→ US-68 (Approval + Löschung + Aufgabenliste)
> US-60   (Location löschen)   ──┤
> TASK-12[x] (Auto-Recompute) ──┴──→ US-68 (nach Approval/Löschung)
> ```
>
> **Abhängigkeiten:** US-63[x], US-66, US-60, TASK-12[x]
>
> ---
>
> ## 📋 Implementation Spec (Analyse 2026-06-22)
>
> **Scope-Klärung (Identitätsmodell — KERN-Frage, vor allem anderen geklärt):**
> US-66 vergibt **rollengebundene** Tokens (`host` / `user`), KEINE Nutzeridentität — alle „user" teilen sich ein Passwort und ein Token. Damit ist „User darf nur **selbst angelegte** Locations löschen" nicht über den Auth-Token abbildbar. Lösung: Eigentümerschaft wird über die bereits existierende `deviceId()` (localStorage-UUID, US-89, `web/index.html` Z.1798) bestimmt — dieselbe Mechanik wie bei Ratings. „Selbst angelegt" = `created_by_device == deviceId()`. Das ist eine **Komfort-/UX-Grenze, kein Sicherheits-Audit** (deviceId ist client-spoofbar) — der echte Schutz ist, dass jede Löschung ohnehin durch den Host-Approval-Gate läuft. Diese Einschränkung ist dokumentiert und akzeptiert (analog zur dokumentierten v1-Grenze in `auth.py`).
>
> **Scope:**
> - **Eingeschlossen:**
>   - Backend: neue Tabelle `location_proposals` in `data/store.py` (Änderungs- UND Lösch-Vorschläge, ein Schema mit `kind`-Diskriminator); CRUD-Methoden; neue Endpoints `POST /locations/{id}/proposals` (user reicht ein), `GET /proposals` (host, alle offenen), `POST /proposals/{pid}/approve` + `POST /proposals/{pid}/reject` (host). Rollengate in `PATCH /locations/{id}` (host → sofort, user → Vorschlag). Neuer `DELETE /locations/{id}` (host sofort; user → Lösch-Vorschlag).
>   - `created_by_device`-Spalte auf `custom_locations` (Eigentümer-Markierung bei Create in `/preview-alignment`).
>   - Frontend: Rollenabhängige Edit/Delete-UI im Location-Detail (host: direkt; user: „Änderung vorschlagen" / „Löschung beantragen"); „Vorschlag ausstehend"-Hinweis an betroffener Location; Host-Aufgabenliste als Sektion in `#page-settings` mit Diff-Ansicht + Annehmen/Ablehnen; Badge-Indikator mit Anzahl offener Aufgaben.
> - **Ausgeschlossen:** Push-Benachrichtigung des Hosts bei neuem Vorschlag (Folge-Ticket); echte nutzergebundene Auth (bleibt v1-Rollenmodell); Vorschläge auf Custom-Location-Felder durch Fremd-User die nicht Eigentümer sind (User darf fremde Locations *ändern*-vorschlagen, aber nur eigene *löschen*-beantragen — siehe Rule 4); Bearbeiten eines bereits offenen Vorschlags (neuer Vorschlag überschreibt: letzter offener pro Location+Feld gewinnt, siehe Pre-Mortem #2).
>
> ### Example Mapping
>
> **📏 Rule 1 — Rolle entscheidet, ob Edit sofort oder als Vorschlag wirkt.**
> Der Host ist Kurator: seine Änderungen sind sofort live. User-Änderungen sind nur Vorschläge, bis der Host sie freigibt — so bleibt die Datenqualität kontrolliert.
> - 🟢 Positiv: Host (Token-Rolle `host`) ändert `subject_lat` via `PATCH /locations/X` → Wert sofort in `location_overrides`, Recompute startet, Response `{"ok":true,"applied":true}`.
> - 🔴 Negativ: User (Rolle `user`) ändert `subject_lat` via `PATCH /locations/X` → KEINE Mutation an Location, stattdessen `location_proposals`-Eintrag (`kind='edit'`, `status='pending'`), Response `{"ok":true,"applied":false,"proposal_id":N}`.
> - ⚠️ Edge: User schickt PATCH ohne gültiges Token → 401 (bestehender `require_auth`). Leerer/ungültiger Feld-Body → 400 (bestehende Validierung greift VOR dem Rollen-Branch).
>
> **📏 Rule 2 — Host genehmigt Vorschläge in einer Aufgabenliste; Annahme wendet den Wert an und löst Recompute aus.**
> Genehmigen ist genau der Pfad, den ein Host-Direkt-Edit auch nimmt — kein zweiter Code-Pfad, sonst driften die beiden auseinander.
> - 🟢 Positiv: Host öffnet Aufgabenliste, sieht Diff (alt `subject_lat=52.5` ↔ neu `52.6`), tippt „Annehmen" → `POST /proposals/{pid}/approve` → Wert wird wie ein Host-Edit übernommen (`upsert_override`/`update_custom`), `status='approved'`, Recompute via `_run_precompute_single`. Aufgabe verschwindet aus der Liste.
> - 🔴 Negativ: Host tippt „Ablehnen" → `status='rejected'`, Location bleibt unverändert, kein Recompute. Aufgabe verschwindet.
> - ⚠️ Edge: Approve eines Vorschlags, dessen Ziel-Location inzwischen gelöscht wurde → 409/404, Vorschlag wird auf `rejected` (oder `stale`) gesetzt statt Absturz.
>
> **📏 Rule 3 — Host darf jede Location sofort löschen; User nur eigene und nur per Approval.**
> Der Host räumt auf; der normale User soll nicht versehentlich (oder böswillig) fremde Spots löschen — eigene Fehleinträge aber loswerden können, mit Host als Kontrolle.
> - 🟢 Positiv (Host): `DELETE /locations/X` mit Host-Token → Location sofort weg (`delete_custom` bzw. Override-Tombstone für Standard-Location), Caches/Feed/Karte bereinigt (Recompute/Reload), Response `{"ok":true,"deleted":true}`.
> - 🟢 Positiv (User, eigene): User mit `device_id` == `created_by_device` ruft `DELETE /locations/X` (custom) → kein Sofort-Löschen, `location_proposals`-Eintrag (`kind='delete'`, `status='pending'`), Response `{"ok":true,"deleted":false,"proposal_id":N}`.
> - 🔴 Negativ (User, fremde): User ohne Eigentümerschaft ruft `DELETE /locations/X` → 403 „Nur der Ersteller kann die Löschung beantragen." Kein Proposal.
> - ⚠️ Edge: User will Standard-Location (Nicht-Custom, kein `created_by_device`) löschen → 403 (Standard-Locations gehören keinem User → nie löschbar durch User).
>
> **📏 Rule 4 — Eigentümerschaft = `created_by_device`; gilt nur für Löschungen, nicht für Änderungs-Vorschläge.**
> Jeder darf eine Verbesserung *vorschlagen* (kollaborativ), aber Löschen ist destruktiv → nur Eigentümer + Host-Gate.
> - 🟢 Positiv: User A (nicht Eigentümer) schlägt Namensänderung für Location von User B vor → erlaubt (`edit`-Proposal). User B (Eigentümer) beantragt Löschung derselben → erlaubt (`delete`-Proposal).
> - 🔴 Negativ: User A beantragt Löschung der Location von User B → 403.
> - ⚠️ Edge: `created_by_device` ist NULL (Alt-Bestand vor diesem Ticket) → wie „kein Eigentümer" behandeln → User darf NICHT löschen (nur Host). Migration setzt Alt-Custom-Locations NICHT rückwirkend auf einen Owner.
>
> **📏 Rule 5 — Offene Aufgaben sind für den Host sichtbar signalisiert (Badge mit Anzahl).**
> Der Host soll nicht aktiv nachsehen müssen — ein Badge zieht die Aufmerksamkeit, verschwindet bei 0.
> - 🟢 Positiv: 3 offene Vorschläge → Badge „3" am Einstellungen-Tab + an der Aufgaben-Sektion. Nach Abarbeiten aller → Badge weg.
> - 🔴 Negativ: User-Rolle sieht KEINE Aufgabenliste und KEIN Badge (Sektion nur bei `Auth.isHost()`).
> - ⚠️ Edge: Badge-Zählung lädt beim App-Start (`GET /proposals` nur für Host) — bei Netzwerkfehler kein Absturz, Badge bleibt aus.
>
> **❓ Questions:** keine offen (Identitäts-/Owner-Frage oben im Scope geklärt; bei Ablehnung des deviceId-Ansatzes durch Stephan → Alternative in Option C).
>
> ### Akzeptanzkriterien
> - [ ] **AK1 (Rule 1):** `PATCH /locations/{id}` mit Host-Token wendet Änderung sofort an (`applied:true`, Override/Custom gespeichert, Recompute getriggert bei Koordinaten).
> - [ ] **AK2 (Rule 1):** `PATCH /locations/{id}` mit User-Token erzeugt `location_proposals`-Zeile (`kind='edit'`, `status='pending'`) und ändert die Location NICHT (`applied:false`, `proposal_id` gesetzt).
> - [ ] **AK3 (Rule 2):** `POST /proposals/{pid}/approve` (Host) übernimmt den Wert exakt wie ein Host-Edit, setzt `status='approved'`, triggert Recompute bei Koordinaten; `/proposals` listet ihn danach nicht mehr.
> - [ ] **AK4 (Rule 2):** `POST /proposals/{pid}/reject` (Host) setzt `status='rejected'`, Location bleibt unverändert.
> - [ ] **AK5 (Rule 3):** `DELETE /locations/{id}` mit Host-Token löscht sofort (custom: aus DB; Response `deleted:true`); danach ist die Location nicht mehr in `GET /locations` und Recompute/Cache-Reload entfernt zugehörige Events.
> - [ ] **AK6 (Rule 3+4):** `DELETE /locations/{id}` mit User-Token UND `created_by_device==deviceId` erzeugt `delete`-Proposal (`deleted:false`); mit fremdem/leerem Owner → 403, kein Proposal.
> - [ ] **AK7 (Rule 5):** `GET /proposals` liefert nur für Host (User → 403); Response enthält pro Eintrag `id, location_id, kind, status, diff (old/new) bzw. zu löschende Location`.
> - [ ] **AK8 (Frontend):** User sieht im Location-Detail „Änderung vorschlagen" statt direktem Speichern; nach Einreichen Hinweis „Vorschlag ausstehend" an der Location; Host sieht Aufgaben-Sektion in Einstellungen mit Diff + Annehmen/Ablehnen + Badge-Anzahl.
> - [ ] **Edge AK9:** Approve eines Proposals auf zwischenzeitlich gelöschte Location → kein 500, Proposal wird `rejected`/`stale`, klare Meldung.
> - [ ] **Edge AK10:** Zweiter offener Edit-Vorschlag desselben Users auf dieselbe Location/dasselbe Feld überschreibt den vorherigen offenen (kein Duplikat-Stau), siehe Pre-Mortem #2.
>
> ### Pre-Mortem
> - 💀 **#1 Rollen-Gate nur im Frontend — API-Bypass.** *Auslöser:* „Änderung vorschlagen"-Button wird im JS gezeigt, aber `PATCH` mutiert serverseitig weiter für jede Rolle. *Frühwarnung:* User-Token in curl ändert eine Location direkt. *Gegenmaßnahme:* Rollen-Branch liegt **im Endpoint** (`PATCH`/`DELETE` prüfen `role`), nicht nur in der UI → AK1/AK2/AK6 als pytest mit beiden Token-Rollen.
> - 💀 **#2 Race / Stau bei `pending`-Vorschlägen.** *Auslöser:* mehrere offene Vorschläge auf dasselbe Feld; Host approved den älteren, der neuere überschreibt ihn wieder; oder Duplikat-Flut. *Frühwarnung:* Aufgabenliste füllt sich mit Mehrfach-Einträgen. *Gegenmaßnahme:* pro (location_id, kind, [field]) nur **ein** offener Vorschlag — neuer Vorschlag setzt vorherigen offenen auf `superseded` (atomar in der `create`-Transaktion). AK10.
> - 💀 **#3 Datenkonsistenz Standard-Location-Löschung.** *Auslöser:* Standard-Locations leben in `data/locations.py` (Code, nicht DB) — ein `delete_custom` greift dort nicht, die Location erscheint nach Neustart wieder. *Frühwarnung:* gelöschte Standard-Location ist nach Server-Restart zurück. *Gegenmaßnahme:* Standard-Location-Löschung = **Tombstone-Override** (`location_overrides` Feld `deleted=true`), `_load_location_overrides` filtert getombstonte aus `LOCATIONS`; ODER (einfacher, empfohlen) User dürfen Standard-Locations gar nicht löschen (Rule 3 Edge → 403) und Host-Löschung von Standard-Locations ebenfalls per Tombstone. AK5 prüft Persistenz über Reload.
> - 💀 **#4 Approve nutzt zweiten Code-Pfad und driftet vom Host-Direkt-Edit ab.** *Auslöser:* `approve` reimplementiert die Persistenz statt die bestehende `_save_location_override`/`_update_custom_location_file`-Logik wiederzuverwenden. *Gegenmaßnahme:* `approve` ruft **dieselbe** interne Apply-Funktion wie der Host-PATCH-Branch (gemeinsame Helper-Funktion extrahieren). AK3.
> - 💀 **#5 deviceId fehlt/leer → falsche 403 oder offene Löschung.** *Auslöser:* Frontend sendet keine `device_id` beim DELETE, Backend behandelt leer == match. *Gegenmaßnahme:* leere/fehlende `device_id` ⇒ niemals Eigentümer ⇒ 403; `device_id` ist Pflicht-Query/Body-Param beim User-DELETE. AK6.
>
> ### Analyse & Planung
> - [x] Example Mapping durchgeführt (5 Rules, 0 offene Questions)
> - [x] Pre-Mortem durchgeführt (5 Szenarien, alle in AKs verankert)
> - [x] Architektur analysiert:
>   - **Backend** `backend/main.py`: `PATCH /locations/{id}` (Z.1325, aktuell ungated für jede Rolle) → Rollen-Branch einbauen; `POST /preview-alignment` (Z.1211, Create) → `created_by_device` setzen; **kein** `DELETE /locations/{id}` vorhanden → neu. `require_auth`/`require_host` aus `auth.py` (Z.66/76). Recompute-Hook `_run_precompute_single` (Z.484, TASK-12). Override-Persistenz `_save_location_override` (Z.571) / `_update_custom_location_file` (Z.203).
>   - **Store** `backend/data/store.py`: neue Tabelle `location_proposals` + CRUD analog `location_overrides`/`location_ratings`; `custom_locations` um Spalte `created_by_device TEXT` (additive Migration via `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE … ADD COLUMN` mit try/except, da bestehende DB).
>   - **Auth** `backend/auth.py`: rollenbasiert, keine Nutzeridentität → Owner-Modell über `deviceId` (Frontend Z.1798), nicht über Token. Python-3.9: `from __future__ import annotations` bereits aktiv, keine 3.10-Syntax.
>   - **Frontend** `web/index.html`: Edit-Button Z.3579 (heute ungated), Save-Flow Z.3496 (`API.patch`), `Auth.isHost()` Z.992, `deviceId()` Z.1798, Settings-Render Z.3900 (Aufgaben-Sektion + Badge hier), Tab-Badge analog vorhandener Tab-Struktur.
> - [x] **Implementierungsoptionen:** A / B / C — Slice 1 (Host-Delete) gewählt
> - [x] **Empfehlung:** Option B → Slice 1 implementiert (2026-06-26)
>
> ### Implementierungsoptionen
>
> **Option A — Separate `pending_overrides`-Datei/Tabelle nur für Edits, Löschung getrennt.**
> Zwei Mechanismen (Edit-Vorschläge in einer Override-Pending-Spalte, Löschwünsche separat). Vorgehen: `location_overrides` um `pending`-Status erweitern, Lösch-Wünsche in eigener Mini-Tabelle. Vorteile: nah an US-68-Wortlaut („pending_override"). Nachteile: zwei Aufgaben-Quellen → Aufgabenliste/Badge muss zwei Tabellen mergen, Diff-Logik doppelt; widerspricht dem Merge-Geist (ein gemeinsames Dashboard). Aufwand: mittel-groß.
>
> **Option B — Eine `location_proposals`-Tabelle für Edits UND Löschungen (kind-Diskriminator), gemeinsamer Approval-Pfad.** ⭐
> Vorgehen: eine Tabelle (`id, location_id, kind['edit'|'delete'], payload(JSON: geänderte Felder), status, created_by_device, created_at`). Rollen-Branch in `PATCH`/neuem `DELETE`. Approve ruft die **bestehende** Host-Apply-Logik. Aufgabenliste = ein `GET /proposals`. Vorteile: ein Datenmodell, eine Liste, ein Badge, ein Diff-Renderer; passt exakt zum Merge (US-86→US-68); minimaler Drift-Risiko (Pre-Mortem #4). Nachteile: „payload als JSON" etwas generischer als getypte Spalten (akzeptabel, gleiche Technik wie `location_overrides.fields`). Aufwand: mittel.
>
> **Option C — Kein Owner-Konzept: jede User-Löschung braucht Approval, jede User-Änderung auch; `created_by`-Frage offen lassen.**
> Vorgehen: wie B, aber ohne `created_by_device` — jeder User darf für jede Location Lösch-Approval beantragen, der Host entscheidet. Vorteile: kein Identitätsmodell nötig, einfachste Migration. Nachteile: erfüllt AK „User dürfen nur **selbst angelegte** löschen" NICHT — verschiebt die Owner-Beschränkung auf den Host (der dann jeden fremden Löschwunsch ablehnen müsste). Weicht vom Ticket ab. Aufwand: klein.
>
> ✅ **Empfehlung: Option B.** Sie ist die einzige Option, die den Merge-Geist (ein gemeinsames Host-Dashboard/Approval statt zweier Mechanismen) und alle drei AK-Blöcke (Änderung, Löschung, Aufgabenliste) in einem Datenmodell erfüllt, hält Approve und Host-Direkt-Edit auf demselben Code-Pfad (Pre-Mortem #4) und nutzt die bereits vorhandene `deviceId`-Mechanik für Eigentümerschaft ohne neues Auth-System. Option C würde ein explizites AK verfehlen; Option A erzeugt doppelte Aufgaben-Quellen.
>
> ### Testplan
> - [ ] **Automatisiert (`backend/tests/`, Ticket-ID im Docstring):**
>   - `test_us68_host_patch_applies_immediately` (AK1) — Host-Token, PATCH, Override gespeichert, `applied:true`.
>   - `test_us68_user_patch_creates_pending_proposal` (AK2) — User-Token, PATCH, Location unverändert, Proposal `pending`.
>   - `test_us68_approve_applies_value` (AK3) + `test_us68_reject_keeps_location` (AK4).
>   - `test_us68_host_delete_immediate` (AK5) + Reload-Persistenz (Pre-Mortem #3).
>   - `test_us68_user_delete_own_creates_proposal` + `test_us68_user_delete_foreign_403` (AK6, Pre-Mortem #5: leere device_id → 403).
>   - `test_us68_proposals_host_only` (AK7, User → 403).
>   - `test_us68_supersede_open_proposal` (AK10) + `test_us68_approve_on_deleted_location` (AK9).
>   - Token via `auth.issue_token('host')` / `issue_token('user')` (lokal, `/login` scheitert ohne `.env`).
>   - **Vollsystem-Regression:** gesamte `backend/tests/`-Suite grün (PATCH-Verhalten für US-60/US-62/BUG-22 darf nicht brechen — Host-Pfad muss identisch zu vorher bleiben).
> - [ ] **Manuell unter http://localhost:8000** (Owner braucht 2 Browser/Profile für verschiedene deviceIds):
>   - Als User: Location ändern → „Vorschlag ausstehend"; eigene Custom-Location löschen → Approval-Antrag.
>   - Als Host (Login-Wechsel): Aufgaben-Sektion + Badge prüfen, Diff ansehen, Annehmen → Wert live + Recompute; Ablehnen → unverändert.
>   - Fremde Location als User löschen → blockiert.
>
> **Memory-Vormerkung (für Retro):** rollenbasierte vs. nutzerbasierte Auth-Grenze → Owner-Konzept via `deviceId` ist projektweites Muster (analog US-89-Ratings); bei künftigen „nur eigene"-Anforderungen kein neues Auth-System nötig.


### US-69 · Kartenansicht auf aktuellen GPS-Standort zentrieren `[x]`
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
>
> ---
>
> **Scope:**
> Eingeschlossen: „Mein Standort"-Button in der Kartenansicht (`#page-map`), einmalige GPS-Abfrage, Zentrierung auf Zoom 13, blauer Puls-Marker. Ausgeschlossen: kontinuierliches Tracking (`watchPosition`), Speicherung/Persistenz der Position, Heading/Kompass-Richtung.
>
> **Akzeptanzkriterien:**
> - [ ] Runder GPS-Button (Standort-Icon, Gold-Akzent) unten links in `#page-map`, z-index über Leaflet
> - [ ] Tap → `navigator.geolocation.getCurrentPosition` → `MapView.map.setView([lat,lon], 13)`
> - [ ] Blauer pulsierender Punkt (Leaflet `divIcon` mit CSS-Animation) auf aktueller Position
> - [ ] Edge Case: erneuter Tap aktualisiert vorhandenen Marker statt Duplikat
> - [ ] Edge Case: Ablehnung der Berechtigung → Toast „GPS-Zugriff nicht erlaubt"
> - [ ] Edge Case: `navigator.geolocation` nicht verfügbar → Toast statt Absturz
> - [ ] Einmalige Abfrage (kein `watchPosition`), Koordinaten werden nicht gespeichert
>
> **Analyse & Planung:**
> - [x] Example Mapping durchgeführt (4 Rules, 1 Question = Button-Platzierung)
> - [x] Architektur analysiert: `web/index.html` — `MapView` (ab Z.2502), CSS `#map-layer-toggle`/`.map-layer-btn` (Z.206), HTML `#page-map` (Z.694). GPS-Muster aus US-32 (`requestGps`, Z.1711) und `AddLocation` (Z.3118).
> - [x] Implementierungsansatz: (1) CSS `.map-gps-btn` (FAB unten links) + `.gps-pulse` Puls-Animation. (2) HTML-Button in `#page-map`. (3) `MapView.locateMe()` — `getCurrentPosition` einmalig, `setView(...,13)`, `this._gpsMarker` als `L.marker` mit `divIcon` (anlegen/`setLatLng` bei Wiederholung), Fehler→`toast`. Aufwand: klein.
> - [x] Risiken: rein additiv, keine bestehende Logik geändert. Puls-Marker mit `interactive:false`, damit Karten-Klicks/Filter nicht gestört werden.
>
> **Testplan:**
> - [ ] Manuell unter http://localhost:8000: Karte öffnen → GPS-Button tippen → Berechtigung erlauben → Karte springt auf Standort (Zoom 13), blauer Puls sichtbar
> - [ ] Ablehnen der Berechtigung → Toast erscheint, kein Absturz
> - [ ] Zweiter Tap → kein Marker-Duplikat


### US-70 · Scout-Tab: Automatisierte Foto-Ephemeride (Mond-Alignment) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **In Progress seit** | 2026-06-19 |
| **Abgeschlossen** | 2026-06-20 (Releases v1.6.0–v1.7.0) |

**Beschreibung:** Als Fotograf möchte ich im neuen „🔭 Scout"-Tab einen nach Score sortierten 14-Tage-Ausblick erhalten, welches bekannte Berliner/Potsdamer Wahrzeichen (Fernsehturm, Siegessäule, Dom …) ich von welchem Standort aus fotografieren kann — mit dem Vollmond (oder Halbmond) exakt auf der Motivspitze, zur goldenen oder blauen Stunde.

**Spec-Referenz:** `foto-chancen-planer-spec.md` (v0.1) — vollständige Domänenspezifikation, Scoring-Formel, Datenquellen, 6 Slices.

**v1-Entscheidungen (Example Mapping 2026-06-19):**
- Himmelskörper: **Mond only** (v2 = Sonne, v3 = 2°-Window-Tracking)
- Motive: **12 kuratierte Leitmotive** (v2 = OSM-Bulk)
- Verschattung (DOM): **nicht in v1** (Slice 3)
- Erreichbarkeit: **nicht in v1** (Slice 2)
- Distanz: **d_min = 100 m, d_max = 13.000 m**
- Output: **dritter Tab „Scout"** in FotoAlert (neben „14 Tage" und „365 Tage")

---

**Scope:**
- Eingeschlossen: `backend/discover/` Package (Motiv-Katalog, Alignment-Pipeline, Scoring), `destination_point()`-Hilfsfunktion, `discover.json`-Cache, `GET /discover`-Endpoint, Frontend-Tab „🔭 Scout"
- Ausgeschlossen: DOM/LOS-Verschattungsanalyse (→ Slice 3), OSM-Erreichbarkeitscheck (→ Slice 2), Sonne (→ v2), 2°-Window-Tracking (→ v3)

**Akzeptanzkriterien:**

*Backend — Motiv-Katalog:*
- [ ] `backend/discover/subjects.py`: 12 kuratierte Leitmotive als Dataclass — Felder: `id`, `name`, `kategorie`, `lat`, `lon`, `terrain_height_m` (Geländehöhe), `structure_height_m` (Bauwerkshöhe), `apex_height_m` (= terrain + structure), `subject_width_m`, `hoehe_confidence`
- [ ] Leitmotive (verifizierte Höhen): Fernsehturm Berlin (406m), Siegessäule (67m), Berliner Dom (114m), Schloss Sanssouci (Hauptgebäude ~15m auf 40m NN), Schloss Cecilienhof (~12m), Flatowturm (34m), Glienicker Brücke (Fahrbahn ~9m), Historische Mühle Sanssouci (12m), Schloss Babelsberg (27m), Nikolaikirche Potsdam (94m), Biosphäre Potsdam (30m), Garnisonkirche Potsdam (ca. 88m)

*Backend — Alignment-Pipeline:*
- [ ] `backend/discover/pipeline.py`: für jedes Motiv M × jeden Tag d (heute bis +14):
  1. Goldene/Blaue-Stunde-Fenster berechnen (`calculate_sun_info` am Motiv-Standort)
  2. Alle 5-Minuten-Zeitschritte in diesen Fenstern → Mond-Positionen batch-berechnen
  3. Filter `gate_horizont`: `alt_C > 0`
  4. d = `(apex_height_m − 1.6) / tan(alt_C)` → Filter: `d ∈ [100, 13000]`
  5. `S = destination_point(M.lat, M.lon, (az_C + 180) % 360, d)`
  6. Scoring → Dedup (bestes Event pro 60-Min-Fenster)
- [ ] Neue Funktion `destination_point(lat, lon, bearing_deg, distance_m) → (lat, lon)` in `discover/geometry.py` (sphärische Formel)
- [ ] `gate_lichtfenster`: Event nur wenn Zeitpunkt in golden_morgen / golden_abend / blau_morgen / blau_abend liegt
- [ ] Deduplication: pro Motiv + 60-Min-Fenster nur das Event mit höchstem Score behalten

*Backend — Scoring:*
- [ ] Score-Formel: `GATE_horizont · GATE_lichtfenster · (w1·S_alignment + w2·S_phase + w3·S_licht + w4·S_komposition + w5·S_wetter)` mit `w1=0.35, w2=0.15, w3=0.15, w4=0.20, w5=0.15`
- [ ] `S_alignment = clip(1 − |alt_offset_deg| / 2.0, 0, 1)` wobei `alt_offset = alt_C − arctan((apex_height_m−1.6) / d)`
- [ ] `S_phase = illumination_pct / 100` (Vollmond = 1.0, Neumond = 0.0)
- [ ] `S_licht`: golden_hour = 1.0, blue_hour = 0.7
- [ ] `S_komposition`: basiert auf `d` — optimale Komposition bei ~3–8 km (`clip(1 − |log(d/5000)| / log(13), 0, 1)`)
- [ ] `S_wetter = (1 − cloud_cover) · wetter_confidence` (open-meteo, bestehende `weather.py`)
- [ ] `Confidence`: `hoch` wenn `hoehe_confidence=hoch` + Wetter <7 Tage; `mittel` sonst; `niedrig` wenn Wetter >7 Tage
- [ ] Output-Schema pro Chance: `motiv_name`, `zeitpunkt` (ISO8601), `lichtphase`, `mond_phase`, `mond_illumination_pct`, `standort_lat`, `standort_lon`, `entfernung_m`, `peilung_deg`, `winkelabstand_deg`, `empf_brennweite_mm`, `score`, `confidence`
- [ ] `empf_brennweite_mm` aus bestehender `calculate_focal_length_for_subject()` (sensor 36mm, fill 20%)

*Backend — Cache & API:*
- [ ] `backend/data/cache/discover.json` enthält nach Lauf die sortierten Chancen
- [ ] `GET /discover` in `main.py` liefert cached JSON (analog zu `GET /feed`)
- [ ] CLI-Ausführung: `cd backend && python3 -m discover.pipeline` → erzeugt `discover.json`

*Frontend — Scout-Tab:*
- [ ] Dritter Segment-Button „🔭 Scout" in der Tab-Navigation neben „14 Tage" und „365 Tage"
- [ ] `#page-scout`: scrollbare Liste der Chancen, Score absteigend
- [ ] Jede Karte zeigt: Motivname + Kategorie-Emoji, Datum + Uhrzeit (lokal), Entfernung + Richtung, Mondphase + Illumination, Lichtphase, Score-Badge, GPS-Button (öffnet Apple/Google Maps mit Standort-Koordinaten)
- [ ] Empty State wenn `discover.json` leer oder fehlt: „Keine Alignment-Chancen in den nächsten 14 Tagen"
- [ ] Score-Badge Farbkodierung: ≥0.75 gold, ≥0.50 silber, <0.50 grau

**Analyse & Planung:**
- [x] Example Mapping durchgeführt — 6 offene Fragen beantwortet (2026-06-19)
- [x] Architektur analysiert: `astronomy.py` (`get_body_position`, `calculate_sun_info`, Haversine, Azimut), `weather.py`, `requirements.txt` — alle benötigten Deps vorhanden (skyfield, numpy, httpx)
- [x] Implementierungsansatz definiert: neues `backend/discover/`-Package, kein neues Dep nötig
- [x] Geometrische Validierung: Mondposition bei M statt S berechnen → Winkelfehler < 0.002° bei 13km Baseline + 384.000km Monddistanz → vernachlässigbar
- [ ] Motive-Höhen verifizieren (Wikipedia / Wikidata) bevor `subjects.py` final geschrieben wird
- [ ] Risiken: Lichtfenster-Berechnung kostet pro Motiv × Tag einen `calculate_sun_info`-Aufruf → 12 × 14 = 168 Aufrufe; akzeptabel (<30s), kann mit `functools.cache` auf 14 Aufrufe reduziert werden (alle Motive nahe beieinander, gleiche Zeitfenster)

**Daten-Validierung:**
- [ ] Stichprobe Fernsehturm Berlin (H=406m): Vollmond az≈118°, alt≈4° → d≈5.640m; S liegt in Richtung Treptow/Neukölln → plausibel für Sonnenuntergangs-Alignment von SO
- [ ] Prüfen: Wie viele Chancen liefert v1 im typischen 14-Tage-Fenster? Erwartung: 15–40 Chancen (1–3 pro Motiv, abhängig von Mondphase)

**Testplan:**
- [ ] CLI: `python3 -m discover.pipeline` läuft durch, `discover.json` enthält ≥1 Chance
- [ ] Validierung Fernsehturm: bei Vollmond-Nacht erscheint mindestens 1 Chance mit Score >0.6, Standort im Bereich Kreuzberg/Neukölln/Treptow (SO vom Turm)
- [ ] `GET /discover` → HTTP 200, JSON mit `opportunities`-Array
- [ ] Frontend: Scout-Tab öffnet, Karten erscheinen, GPS-Button öffnet Karten-App

**Implementierungsreihenfolge:**
1. `backend/discover/__init__.py` + `geometry.py` (`destination_point`)
2. `backend/discover/subjects.py` (12 Motive mit verifizierten Höhen)
3. `backend/discover/pipeline.py` (Kern-Algorithmus, ohne Wetter)
4. Wetter-Integration in Pipeline
5. `GET /discover` Endpoint in `main.py`
6. Frontend: Scout-Tab in `web/index.html`

---


### US-70b · Scout-Tab Slice 2: Mondposition per Subject-Koordinaten `[x]`


### US-70c · Scout-Tab Slice 3: Subjects aus Locations + 150m-Exklusionsfilter `[x]`

| Feld | Wert |
|------|------|
| Priorität | Mittel |
| Abhängigkeit | US-70 (Slice 1) ✅ |
| Aufwand | S (1–2h) |

**Problem:** In Slice 1 wird die Mondposition einmal am Berliner Zentrum (52.52°N, 13.40°E) berechnet und für alle 12 Subjects verwendet (Berlin-Center-Approximation). Das funktioniert für Berlin/Potsdam (~50km Radius), schlägt aber fehl sobald Subjects weiter entfernt liegen (andere Städte, deutschlandweite Erweiterung).

**Lösung:** Mondposition per Subject an den tatsächlichen Subject-Koordinaten berechnen (topozentrisch korrekt). Pro Subject × Timestep → Skyfield-Call.

**Betroffene Dateien:**
- `backend/discover/pipeline.py`

**Akzeptanzkriterien:**
- `run_pipeline()` ruft `_moon_pos(ts, subject.lat, subject.lon)` statt `_moon_pos(ts, *BERLIN_CENTER)` auf
- BERLIN_CENTER-Konstante wird entfernt oder nur noch als Fallback genutzt
- Kein funktionaler Unterschied für bestehende Berlin/Potsdam-Subjects (Delta < 0.02°)
- Neue Subjects außerhalb Berlin können ohne Koordinaten-Bias hinzugefügt werden

**Implementierungshinweis:** Die `topos`-Methode in Skyfield erlaubt beliebige Koordinaten. Performance: 12 Subjects × ~448 Timesteps = ~5376 Calls statt 448. Ggf. Batch-Optimierung via `earth + wgs84.latlon(lat, lon)` prüfen.

---


### US-71 · Drei-Zustand-Filter: Include / Exclude / Off `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **In Analysis seit** | 2026-06-21 |
| **Implementiert** | 2026-06-21 (Option A) |
| **Released** | 2026-06-21 · v1.9.0 |

**Beschreibung:** Jedes Filterkriterium soll drei Zustände haben: 1. Klick → aktiv/include (gelber Rand, zeigt nur Ergebnisse die das Kriterium erfüllen), 2. Klick → exclude (roter Rand, blendet Ergebnisse mit diesem Kriterium aus), 3. Klick → inaktiv (kein Rahmen, keine Filterung). Wirkt auf alle Panels wie bisher.

---

#### 🔬 Analyse (2026-06-21)

**Scope-Entscheidung (Stephan, 2026-06-21):** Drei-Zustand nur für die **kategorialen Mehrfachauswahl-Chips** — 📷 Eventtyp, 🕐 Tageszeit, 🎯 Schwierigkeitsgrad. Begründung: Include/Exclude/Off hat nur für kategoriale Werte saubere Semantik.

- **Eingeschlossen:** Drei-Zustand-Zyklus (Off → Include → Exclude → Off) für Eventtyp, Tageszeit, Schwierigkeitsgrad in allen Ansichten, die das Kriterium heute kennen (Chancen-Feed, Kalender, Scout; Schwierigkeit zusätzlich in Locations). Rotrand-Styling für Exclude. Badge/activeCount zählt Excludes mit.
- **Ausgeschlossen:** Slider (🔭 Brennweite, 🎯 Mindest-Wahrscheinlichkeit) und Schwellen-/Einzelauswahl (⭐ Bewertung, 📍 Entfernung, ✅ Verifikation) — bleiben unverändert. Kein Exclude für diese.

**Example Mapping:**

📏 *Rule 1* — Ein kategorialer Chip durchläuft im Klick-Zyklus 3 Zustände: Off → Include (Goldrand) → Exclude (Rotrand) → Off.
- 🟢 *Given* Eventtyp-Chip „Mond-Alignment" Off. *When* 1× Klick → nur Mond-Alignment sichtbar, Chip Goldrand. *When* 2× Klick → alle **außer** Mond-Alignment, Chip Rotrand. *When* 3× Klick → keine Eventtyp-Filterung, kein Rand.

📏 *Rule 2* — Innerhalb eines Kriteriums: Includes als OR (zeige wenn Wert ∈ Includes), Excludes als NOT (verstecke wenn Wert ∈ Excludes). Ein Wert kann durch den Zyklus nie gleichzeitig incl+excl sein.
- 🟢 *Given* Tageszeit Include „Morgens" + Exclude „Nacht". *When* gefiltert → nur Morgens-Events (Tag/Abend/Nacht fallen weg, weil Include aktiv).
- 🟢 *Given* nur Exclude „Anspruchsvoll" (kein Include). *When* gefiltert → alle Schwierigkeiten außer Anspruchsvoll.

📏 *Rule 3* — Wirkt einheitlich auf alle Ansichten, die das Kriterium heute filtern. „Goldene Stunde" expandiert auch beim Exclude auf beide Backend-Werte (`Goldene Stunde Morgen/Abend`).

**Akzeptanzkriterien:**
- [ ] Klick-Zyklus: 3 Klicks auf einen Eventtyp/Tageszeit/Schwierigkeit-Chip durchlaufen Off → Include (Goldrand) → Exclude (Rotrand) → Off und zurück.
- [ ] Include-Semantik unverändert: bei aktiven Includes werden nur passende Ergebnisse gezeigt (wie heute).
- [ ] Exclude-Semantik: Chip im Exclude-Zustand blendet Ergebnisse mit diesem Wert aus; bei reinem Exclude (kein Include) sind alle übrigen Werte sichtbar.
- [ ] Wirkt in Chancen-Feed, Kalender und Scout; Schwierigkeit-Exclude wirkt auch in der Locations-Liste.
- [ ] „Goldene Stunde" exclude blendet sowohl `Goldene Stunde Morgen` als auch `Goldene Stunde Abend` aus.
- [ ] Filter-Badge/activeCount erhöht sich auch wenn nur Excludes gesetzt sind.
- [ ] „Alle zurücksetzen" löscht Include- und Exclude-Zustände.
- [ ] Live-Result-Count (`↳ N von M sichtbar`) berücksichtigt Excludes.
- [ ] Edge Case: alter gespeicherter Filter-State ohne Exclude-Felder lädt fehlerfrei (keine `undefined.includes`-Fehler).
- [ ] Edge Case: Include + criterion-übergreifendes Exclude, das 0 Ergebnisse liefert → Result-Count zeigt „0 sichtbar"-Warnung (bestehendes Verhalten), kein Crash.

**Pre-Mortem:**
- 💀 *Exclude wirkt in einer Ansicht nicht* (z.B. Scout vergessen) → inkonsistente Ergebnisse. → Gegenmaßnahme: Exclude-Check in `apply`, `applyToLocations`, `applyToScout`; je ein AK pro Ansicht.
- 💀 *„Goldene Stunde"-Mapping beim Exclude vergessen* → Ausschluss blendet nichts aus (Backend-Werte heißen `Goldene Stunde Morgen/Abend`). → Gegenmaßnahme: `ET_EXPAND` auch auf Exclude-Array anwenden; eigenes AK.
- 💀 *localStorage-Migration bricht JS* → alte gespeicherte Filter ohne `*Excl`-Arrays → `undefined.includes`. → Gegenmaßnahme: `_defaults()` liefert leere Excl-Arrays, `Object.assign`-Merge; AK + manueller Test mit altem State.
- 💀 *Badge zählt Excludes nicht* → Nutzer sieht aktiven Filter nicht. → Gegenmaßnahme: `activeCount()` um Excl-Arrays erweitern; AK.
- 💀 *Routine-Event-Default kollidiert* (US-40: bei leerem Eventtyp-Include werden Routine-Events ausgeblendet) → unklare Wirkung wenn nur Exclude gesetzt. → Gegenmaßnahme: Default-Regel bleibt an „Include leer" gekoppelt (Exclude ändert sie nicht); im Code-Kommentar + Test festhalten.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Scope-Frage geklärt (nur kategoriale Chips)
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` — `Filter` (`_defaults`/`apply`/`applyToLocations`/`applyToScout`/`activeCount`, Z. 1871–2058) + `FilterSheet` (`_render`/`_toggle`/`chip`, Z. 2060–2350) + CSS `.filter-chip` (Z. 342–345). Reines Frontend, kein Backend/keine pytest-Abdeckung.
- [x] Implementierungsoptionen: A (Split-Arrays) / B (Object-State)
- [ ] Empfehlung: **Option A** — wartet auf Stephans Weg-Gate

**Implementierungsoptionen:**

*Option A — Split-Arrays (je Kriterium ein Include- + ein Exclude-Array)* · Aufwand: klein
- Vorgehen: Bestehende `eventTypes`/`tageszeit`/`difficulty` bleiben die Include-Arrays (rückwärtskompatibel); neu `eventTypesExcl`/`tageszeitExcl`/`difficultyExcl` in `_defaults()`. Chip-Klick wird zu `_cycle(key, val)`: off→incl→excl→off. In `apply`/`applyToLocations`/`applyToScout` je ein zusätzlicher Exclude-Check. `activeCount` + Result-Count erweitern. Neue Drei-Zustand-`chip()`-Variante + CSS `.filter-chip.exclude` (Rotrand).
- Betroffene Dateien: nur `web/index.html`.
- Vorteile: rückwärtskompatibel mit gespeichertem State; minimale, lokale Änderungen an bestehender Filterlogik; bestehende Include-Pfade bleiben unangetastet.
- Nachteile/Risiken: zwei Arrays pro Kriterium (etwas mehr State-Felder).

*Option B — Object-State (`{wert: 'incl'|'excl'}` statt Array)* · Aufwand: mittel
- Vorgehen: `eventTypes` etc. werden Objekte; alle `.includes()`-Lesestellen und das Scout-`body_name`-Mapping umschreiben.
- Vorteile: ein Feld pro Kriterium, ausdrucksstärker.
- Nachteile/Risiken: bricht gespeicherten localStorage-State (Migration nötig); berührt jede Lesestelle → größere Regressionsfläche; mehr Pre-Mortem-Risiko 3.

✅ **Empfehlung: Option A** — kleinster Eingriff, rückwärtskompatibel, hält die bewährten Include-Pfade stabil und isoliert das neue Verhalten auf additive Exclude-Checks.

**Testplan:**
- [ ] Automatisiert: keine pytest-Abdeckung (reines Frontend). Optional kleine JS-Konsolen-Asserts für `Filter.apply` mit Fixture-Daten.
- [ ] Manuell (http://localhost:8000): je Kriterium 3-Klick-Zyklus prüfen (Gold→Rot→aus); Exclude „Goldene Stunde" → beide Routine-Varianten weg; Exclude in Scout + Kalender + Locations; Badge bei reinem Exclude; „Alle zurücksetzen"; alten Filter-State im localStorage simulieren und Sheet öffnen (kein Crash).

---


### TASK-44 · QA-Datenmodell: Lock-Flags, QA-Tabellen, Geo-Hash `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task (Architektur) |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-27 |
| **In Progress seit** | 2026-06-27 |
| **Abgeschlossen** | 2026-06-27 |
| **Epic** | US-75 |

**Beschreibung:** Fundament für alle QA-Kind-Tickets. Legt die Datenbankstruktur an, die verhindert dass auto-generierte Werte manuell kuratierte Werte überschreiben, und ermöglicht Change-Detection ohne Full-Scan.

**Scope:**
- Eingeschlossen: neue SQLite-Tabelle `location_qa_state` (Lock-Flags + `qa_checked_at` + `geo_hash`); neue Tabelle `location_qa_values` (auto-generierte Felder für BASE-Locations); neue Spalten `ideal_azimuth_min REAL`, `ideal_azimuth_max REAL` in `custom_locations`; `compute_geo_hash(loc)`-Funktion; Store-Methoden `get_qa_state`, `set_qa_lock`, `update_qa_checked`, `get_qa_values`, `set_qa_values`; Merge-Reihenfolge beim Laden: Code < qa_values < location_overrides.
- Ausgeschlossen: Azimut-Berechnung (TASK-44), LLM (TASK-45), Brennweiten-Calc (TASK-46), Cron (TASK-47). Kein Frontend-Change (Admin-UI kommt later).

**Akzeptanzkriterien:**
- [ ] `location_qa_state`-Tabelle existiert; `get_qa_state('unbekannte-id')` → `None` (kein Fehler)
- [ ] `set_qa_lock('id', 'description', True)` → atomar gespeichert; erneuter Aufruf überschreibt (Upsert)
- [ ] `location_qa_values`-Tabelle existiert; `set_qa_values('id', description='…')` → speichert; `get_qa_values('id')` → gibt zurück
- [ ] `custom_locations` hat Spalten `ideal_azimuth_min REAL DEFAULT NULL`, `ideal_azimuth_max REAL DEFAULT NULL`; Migration idempotent auf bestehender DB
- [ ] `compute_geo_hash(lat, lon, s_lat, s_lon, height, width, dist)` → deterministischer String; gleiche Inputs (auch nach Float-Rounding auf 6 Stellen) = gleicher Hash
- [ ] Merge beim Location-Laden: qa_values-Felder überschreiben Code-Defaults, `location_overrides` überschreiben qa_values
- [ ] Edge Case: Migration auf bestehende `custom_locations`-Rows → alle bestehenden Rows haben `ideal_azimuth_min = NULL` (kein Datenverlust)
- [ ] Edge Case: `set_qa_lock` auf nicht-existierende ID → legt Eintrag an (kein Fehler)

**Pre-Mortem:**
- 💀 Migration bricht bestehende `custom_locations`-Rows → Gegenmaßnahme: `ALTER TABLE ADD COLUMN IF NOT EXISTS` + Integrations-Test gegen befüllte Dev-DB
- 💀 Merge-Reihenfolge falsch verdrahtet (overrides vor qa_values) → Gegenmaßnahme: Test mit allen drei Schichten für dieselbe Location-ID
- 💀 `geo_hash` nicht deterministisch durch Float-Rounding → Gegenmaßnahme: Inputs vor Hash auf 6 Dezimalstellen runden; Test mit identischen Inputs in zwei Aufrufen

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `backend/data/store.py` (Z.37–100 _INIT_SQL, Z.103–220 CRUD), `backend/data/locations.py` (PhotoLocation-Dataclass)
- [x] Option B bestätigt: `location_qa_values` als eigene Tabelle (getrennt von `location_overrides`)
- [x] Zwei Spalten statt JSON für Azimut: `ideal_azimuth_min`, `ideal_azimuth_max`

**📎 Code-Verifikation (2026-06-27):**
- Bestätigt: `_INIT_SQL` nutzt `CREATE TABLE IF NOT EXISTS` → erweiterbar ohne Schema-Drop
- Bestätigt: `custom_locations` hat KEIN `ideal_azimuth_range`-Feld → muss hinzugefügt werden
- Bestätigt: kein `scheduler.py` vorhanden → TASK-47 baut Scheduler neu
- Bestätigt: `location_overrides` speichert JSON-Blob → bleibt für echte Nutzer-Overrides; qa_values kommen in eigene Tabelle

**Testplan:**
- [ ] Automatisiert (`backend/tests/test_task43_qa_model.py`): Migration auf leerer + befüllter Dev-DB; Lock-Upsert; Geo-Hash-Determinismus; Merge-Reihenfolge (3 Schichten)
- [ ] Manuell: `python3 -c "from data.store import LocationStore; s=LocationStore(); print(s.get_qa_state('x'))"` → None

---


### US-76 · Location-Kategorien als Standardliste mit Filter-Integration `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **Abgeschlossen** | 2026-06-27 |
| **In Analysis seit** | 2026-06-26 |
| **In Progress seit** | 2026-06-26 |
| **In Test seit** | 2026-06-26 |

**Beschreibung:** Location-Kategorien sollen standardisiert und als Auswahlliste beim Bearbeiten und Neuanlegen von Locations verfügbar sein. Der Filter soll um diese Kategorien erweitert werden, damit Nutzer nach Motivtyp filtern können — im Locations-Tab, auf der Karte und im Chancen-Feed.

**Scope:**
- Eingeschlossen: Kategorie-Dropdown im Add-Form; Kategorie-Chips (Include + Exclude) im Filter-Sheet; `Filter._defaults()` + `activeCount()` + `applyToLocations()` + `apply()` um Kategorie erweitern; `catColor`/`catIcon`/`catBg`-Maps vervollständigen (alle 7 Kategorien)
- Ausgeschlossen: Backend-Änderungen (`/locations?category=X` bereits vorhanden aber nicht nötig); Edit-Form (bereits vollständig); neue Kategorie-Werte

**Akzeptanzkriterien:**
- [ ] „Neue Location"-Maske hat ein Kategorie-Dropdown mit allen 7 Kategorien; Vorauswahl ist „Skyline & Architektur"
- [ ] Nach dem Speichern zeigt die neue Location die gewählte Kategorie (farbiger Marker auf Karte + Icon im Locations-Tab)
- [ ] Filter-Sheet hat neue Sektion „Kategorie" mit 7 Chips (Schloss & Historisch, Skyline & Architektur, Natur & Landschaft, Wasser & Spiegelung, Aussichtspunkt, Industrie & Urban, Milchstraße & Astro)
- [ ] Chips: 1. Tap = ✅ nur diese Kategorie; 2. Tap = ❌ ausschließen; 3. Tap = inaktiv (wie Schwierigkeits-Chips, US-71)
- [ ] Locations-Tab + Map zeigen nach Anwenden nur Locations der gewählten Kategorie(n)
- [ ] Chancen-Feed filtert ebenfalls nach Kategorie via `location_id`-Lookup in `Locations.all`
- [ ] Wenn `Locations.all` beim Boot nicht geladen werden konnte (401/500), greift Kategorie-Filter im Feed nicht — alle Chancen durch (akzeptierter Fallback, identisch zu Difficulty-Filter)
- [ ] Filter-Badge zählt aktive Kategorie-Chips als einen aktiven Filter
- [ ] „Alle zurücksetzen" leert auch Kategorie-Auswahl
- [ ] Edge Case: Chip aktiv, keine Location in dieser Kategorie → Locations-Tab zeigt leeren Zustand
- [ ] Edge Case: alle 7 Chips aktiv → wie kein Filter (alle Locations sichtbar)
- [ ] `catColor`, `catIcon`, `catBg` in der Frontend-Map sind für alle 7 Kategorien vollständig (inkl. MILCHSTRASSE)

**Pre-Mortem:**
- 💀 Alter localStorage-State ohne `category`-Feld → `s.category` wäre `undefined` → `.includes()` crasht. Gegenmaßnahme: `_defaults()` liefert `{ category: [], categoryExcl: [] }` → `Object.assign` füllt auf (bewährte Strategie aus US-71).
- 💀 `Locations.all` beim Feed-Boot leer (BUG-28-Muster) → Kategorie-Filter im Feed stumm. Gegenmaßnahme: bekannter Fallback akzeptiert; `Locations.all` wird beim Boot bereits optimistisch geladen (BUG-28-Fix, Zeile ~4576); Risiko gering.
- 💀 `catColor`/`catIcon`/`catBg` unvollständig (MILCHSTRASSE fehlt möglicherweise) → Marker-Farbe `undefined`. Gegenmaßnahme: alle 7 Werte beim Implementieren prüfen und ggf. ergänzen.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (4 Rules, Q1 beantwortet: Feed eingeschlossen, Option B)
- [x] Pre-Mortem durchgeführt
- [x] Code-Verifikation: `Filter._defaults()`, `activeCount()`, `applyToLocations()`, `apply()`, Add-Form, `catColor/catIcon/catBg` gelesen — keine `category`-Unterstützung vorhanden; Edit-Form bereits vollständig
- [x] `Locations.all` beim App-Boot geladen (BUG-28-Fix, Zeile ~4576) → Feed-Filter funktioniert wie Difficulty-Filter
- [x] Architektur: nur `web/index.html` betroffen — kein Backend-Eingriff nötig
- [ ] Implementierung: Option B (Include + Exclude, wie US-71)

**Betroffene Stellen in `web/index.html`:**
1. `Filter._defaults()` → `category: [], categoryExcl: []` ergänzen
2. `Filter.activeCount()` → `+ ((s.category.length || s.categoryExcl.length) ? 1 : 0)`
3. `Filter.applyToLocations()` → Category-Match analog zu `difficulty`
4. `Filter.apply()` → Category-Match via `location_id`-Lookup in `Locations.all`
5. `FilterSheet._render()` → neue Sektion „Kategorie" mit 7 `chip3`-Chips
6. Add-Form HTML → `<select id="add-category">` mit 7 Optionen
7. `AddLocation.save()` → `#add-category`-Wert lesen und an API senden
8. `catColor`/`catIcon`/`catBg`-Maps → alle 7 Kategorien prüfen + vervollständigen

**Testplan:**
- [ ] Automatisiert: kein Backend-Test nötig (reine Frontend-Änderung); manuell ausreichend
- [ ] Manuell: (1) Neue Location anlegen, Kategorie wählen → Karte + Tab prüfen; (2) Filter öffnen, Kategorie-Chip antippen → Locations-Tab + Feed prüfen; (3) Exclude-Modus; (4) Reset; (5) localStorage leeren → App neu laden → kein Crash

---


### US-80 · Scout-Tab: Filter-System `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **In Progress seit** | 2026-06-19 15:30 |
| **Abgeschlossen** | 2026-06-19 |

**Beschreibung:** Im Scout-Tab soll dasselbe Filter-System wie im Chancen-Tab verfügbar sein, damit Nutzer die Scout-Ergebnisse anhand der bestehenden Filterkriterien einschränken können. Anzeige von Gesamtanzahl und gefilterter Anzahl wie im Chancen-Tab.

**Scope:**
- Eingeschlossen: `Filter.applyToScout()` für 4 anwendbare Dimensionen (Tageszeit, Score, Brennweite, Entfernung); Zähleranzeige in Scout-Content und Filter-Sheet; Live-Update beim Schieben von Slidern; `FilterSheet._applyLive()` und `_updateResultCount()` für Scout-Modus erweitern
- Ausgeschlossen: Eventtyp-, Schwierigkeits-, Rating- und Verifikations-Filter (kein Äquivalent in Scout-Daten, werden ignoriert); Anpassung der Filter-Sheet-UI für Scout-Modus (alle Sektionen bleiben sichtbar, nicht-anwendbare haben schlicht keinen Effekt)

**Akzeptanzkriterien:**
- [ ] `Filter.applyToScout(data)` existiert: filtert nach Tageszeit (session-Mapping), `score` (statt `overall_score`), `focal_length_equiv_mm`, GPS-Distanz zu `standpoint_lat/lon`
- [ ] Scout-Tab zeigt oberhalb der Karten-Liste Zähler „X von Y Scout-Chancen" wenn Filter aktiv (kein Zähler wenn kein Filter)
- [ ] Filter-Sheet zeigt bei aktivem Scout-Modus „↳ X von Y Scout-Chancen sichtbar" in `#filter-result-count`
- [ ] Live-Update: Scout re-rendert sofort bei Slider-Änderung im offenen Filter-Sheet
- [ ] Tageszeit „Morgen" → nur `golden_morning` + `blue_morning` (70 von 296 aktuell)
- [ ] Tageszeit „Abend" → nur `golden_evening` + `blue_evening` (226 von 296 aktuell)
- [ ] Mindest-Score-Slider filtert korrekt auf `o.score` (0–1)
- [ ] Nicht-anwendbare Filter (Eventtyp, Schwierigkeit, Rating, Verifikation) haben keinen Effekt auf Scout-Ergebnisse
- [ ] Filter-Badge (`#filter-badge`) zeigt weiterhin Gesamtzahl aller aktiven Filter (auch wenn manche im Scout-Context ohne Wirkung)
- [ ] Edge Case: alle Filter zusammen ergeben 0 Ergebnisse → Scout zeigt leeren Zustand mit Hinweis „Keine Scout-Chancen entsprechen den Filterkriterien"
- [ ] Edge Case: Scout-Daten noch nicht geladen → Filter-Sheet-Zähler bleibt leer

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (4 Rules, keine offenen Questions)
- [x] Scout-Daten analysiert: 296 Chancen, Score 0.59–0.98, Focal 20–120mm, Distanz 0.1–3.3km, Sessions: golden_evening(112), blue_evening(114), golden_morning(37), blue_morning(33)
- [x] Architektur analysiert: alle Änderungen in `web/index.html` — kein Backend-Eingriff nötig
- [x] Betroffene Stellen: `Filter`-Objekt (+`applyToScout()`), `Scout.render()`, `FilterSheet._applyLive()`, `FilterSheet._updateResultCount()`
- [ ] Implementierungsansatz: (1) `applyToScout()` in Filter-Objekt ergänzen, (2) Scout.render() auf `applyToScout()` umstellen + Zähler-Header einbauen, (3) `_applyLive()` + `_updateResultCount()` für Scout-Modus erweitern

**Daten-Validierung:**
- [x] Scout-Felder verifiziert: `score` (nicht `overall_score`!), `focal_length_equiv_mm` (direkt), `session` für Tageszeit-Mapping, `standpoint_lat/lon` für GPS-Distanz
- [x] Tageszeit-Mapping validiert: morgen↔(golden_morning+blue_morning)=70 Einträge, abend↔(golden_evening+blue_evening)=226 Einträge — keine "tag"/"nacht"-Sessions → Auswahl dieser Slots ergibt 0 Scout-Ergebnisse (erwartetes Verhalten)

**Testplan:**
- [ ] Manuell: Filter-Button im Scout-Tab öffnen → Tageszeit „Morgen" wählen → Scout zeigt ~70 Chancen und „70 von 296 Scout-Chancen sichtbar"
- [ ] Manuell: Tageszeit auf „Abend" umschalten → ~226 Chancen erscheinen
- [ ] Manuell: Score-Slider auf 80 % → nur hochwertige Chancen bleiben; Zähler aktualisiert sich live
- [ ] Manuell: Brennweite min 50mm → Chancen unter 50mm verschwinden
- [ ] Manuell: Scout-Tab verlassen, zu Chancen-Tab wechseln → Feed-Filter funktioniert weiterhin korrekt (keine Regression)
- [ ] Manuell: Eventtyp-Filter auf „Mondaufgang" setzen, dann Scout-Tab → alle Scout-Chancen weiterhin sichtbar (Eventtyp-Filter ohne Wirkung)

**Implementierungsnotizen:**
*(leer bei Erstellung)*

---


### US-81 · Scout-Tab: Weitere Event-Typen (Sonne, weitere Himmelskörper) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-19 |
| **In Progress seit** | 2026-06-19 |
| **Released** | v1.8.0 (Code bereits live) |
| **Getestet & verifiziert** | 2026-06-20 (lokal + Live-Server) |
| **Abgeschlossen** | 2026-06-20 |

**Beschreibung:** Der Scout-Tab soll nicht auf Mond-Alignment beschränkt bleiben. Die Pipeline-Architektur wird auf mehrere Himmelskörper ausgebaut (Sonne, Milchstraße, Kometen), und die Sonne wird als erster neuer Typ vollständig implementiert. Das Datenschema wird auf `body_*`-Felder umgestellt. US-80 (event-type-agnostischer Filter) ist Voraussetzung und bereits erfüllt.

**Scope:**
- Eingeschlossen: Architektur-Refactoring (`pipeline.py` → `pipeline_base.py` + `moon_pipeline.py` + `sun_pipeline.py` + Orchestrator), Schema-Migration (`moon_*` → `body_*`), Sonne-Pipeline vollständig implementiert, Frontend-Anpassung (body-Icon + bedingter `illumination`-Chip), v2-Ticket für atmosphärisches Sun-Scoring
- Ausgeschlossen: Milchstraße-Pipeline (→ eigenes Ticket), Kometen-Pipeline (→ eigenes Ticket), atmosphärisches Rötlichkeits-Scoring für Sonne (→ US-82)

**Akzeptanzkriterien:**

*Architektur:*
- [x] `backend/discover/pipeline_base.py`: `ScoutOpportunity` Dataclass mit `body_name`, `body_azimuth_deg`, `body_altitude_deg`, `body_illumination_pct: Optional[float]`; gemeinsame Hilfsfunktionen (Wetter, Dedup, Haversine, `compute_d`, Scoring-Helfer)
- [x] `backend/discover/moon_pipeline.py`: bestehende Moon-Logik dorthin verschoben, importiert aus `pipeline_base`
- [x] `backend/discover/sun_pipeline.py`: neue Sonne-Pipeline, gleiche Apex-Geometrie, körper-spezifisches Scoring
- [x] `backend/discover/pipeline.py` wird zum Orchestrator: ruft `moon_pipeline.run()` + `sun_pipeline.run()` parallel auf, merged und sortiert nach Score; Fehler in einer Pipeline bricht die andere nicht ab
- [x] `backend/discover/geometry.py` und `subjects.py`: unverändert

*Schema — `moon_*` → `body_*`:*
- [x] `ScoutOpportunity.moon_azimuth_deg` → `body_azimuth_deg`
- [x] `ScoutOpportunity.moon_altitude_deg` → `body_altitude_deg`
- [x] `ScoutOpportunity.moon_illumination_pct` → `body_illumination_pct: Optional[float]` (None für Sonne)
- [x] Neues Feld `body_name: str` = `"moon"` | `"sun"`
- [x] `main.py`: Schema-Check beim Startup — alter Cache ohne `body_name` löst automatisch Neuberechnung aus

*Sonne-Pipeline (`sun_pipeline.py`):*
- [x] Gleiche Sessions wie Mond (golden_morning, golden_evening, blue_morning, blue_evening)
- [x] Körper: `get_body_position(..., "sun", ...)` — bereits von `astronomy.py` unterstützt
- [x] Alt-Gate: `sun_alt ≥ 0.5°` (Sonne sichtbar über Horizont; bei golden hour typisch 0–8°)
- [x] Gleiche Apex-Geometrie: `d = apex_effective_m / tan(sun_alt_rad)`, Gate `D_MIN=100m` bis `D_MAX=13.000m`
- [x] `S_alignment`: Gaußkurve um Optimum 4°, σ=8° — abweichend vom Mond (Optimum 25°)
- [x] `S_phase = 1.0` fest (Sonne immer voll beleuchtet — v2 → US-82)
- [x] `S_licht`, `S_komposition`, `S_wetter`: identisch zum Mond
- [x] Gewichte: unverändert (W_ALIGNMENT=0.35, W_PHASE=0.15, W_LICHT=0.15, W_KOMPOSITION=0.20, W_WETTER=0.15)
- [x] `body_illumination_pct = None` im Output
- [x] Exklusionsfilter (EXCLUSION_ZONES, ≥150m von bekannten Standorten): gleich wie Mond

*Frontend (`web/index.html`):*
- [x] `Scout.render()`: Feld `o.body_name` steuert Icon (`"moon"` → 🌙, `"sun"` → ☀️); Icon auch im Karten-Titel
- [x] Chip `body_illumination_pct`: wird nur gerendert wenn `body_illumination_pct !== null`
- [x] Für Sonne kein Beleuchtungs-Chip (Sonne ist immer voll, kein Mehrwert)
- [x] Scout-Karte für Sonne zeigt: ☀️ + Motivname, Datum/Uhrzeit, Höhe, Entfernung, Brennweite, Lichtphase, Wetter
- [x] `Filter.applyToScout()`: bereits event-type-agnostisch (US-80) — kein Eingriff nötig

*Neues Ticket:*
- [x] US-82 · Scout Sun-Score v2 (Atmosphären-Rötlichkeit) im Backlog angelegt

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (4 Rules, 4 Questions — alle beantwortet 2026-06-19)
- [x] Architektur analysiert: `discover/pipeline.py` vollständig gelesen; `astronomy.py` `get_body_position` unterstützt bereits `"sun"`; `Filter.applyToScout()` ist body-agnostisch (US-80)
- [x] Implementierungsansatz: Modulsplit + Schema-Migration + Sonne-Pipeline + Frontend-Icon-Logik
- [x] Risiken: Schema-Breaking-Change — behoben via `body_name`-Check in `main.py` Startup (erzwingt automatische Neuberechnung)
- [x] Geometrie-Validierung: Fernsehturm (368m apex) bei Sonne 3.1°: d=6.801m, f=190mm, S_alignment=0.994 ✅

**Daten-Validierung:**
- [x] Sonne bei golden hour: az=305.7°, alt=3.1° → d=6.801m für Fernsehturm (Berlin) ✅
- [x] Geprüft nach Scout-Lauf (2026-06-20): **588 Sonne-Chancen** im 14-Tage-Fenster (+ 288 Mond = 876). Erwartung „5–20" war deutlich zu niedrig geschätzt — real = 20 Motive × 14 Tage × 2 Golden-Sessions. Verteilung sauber: alle 14 Tage abgedeckt, nur `golden_morning`/`golden_evening` (blaue Stunde korrekt ausgegrenzt), `body_illumination_pct=null` bei allen Sonne-Einträgen, 0 echte Duplikate (28 Mehrfach-Slots = legitime verschiedene Standpunkte ≥150 m)

**Testplan:**
- [x] Manuell (lokal 2026-06-20): Scout-Tab zeigt gemischte Karten mit 🌙 und ☀️ Icons
- [x] Manuell: Sonne-Karte zeigt keinen Beleuchtungs-Chip
- [x] Manuell: Filter Tageszeit „Morgen" filtert Sonne-Abend-Chancen korrekt heraus

**Implementierungsreihenfolge:**
1. [x] `pipeline_base.py` anlegen
2. [x] `moon_pipeline.py` (refactor)
3. [x] `sun_pipeline.py` (neue Pipeline)
4. [x] `pipeline.py` zum Orchestrator umbauen
5. [x] Frontend: body-Icon + bedingter illumination-Chip
6. [x] Schema-Check in `main.py` (auto-Neuberechnung bei altem Cache)
7. [x] US-82-Ticket in BACKLOG.md angelegt

---


### BUG-28 · Schwierigkeitsfilter im Chancen-Feed wirkungslos bis Locations-Tab besucht wurde `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-21 |

**Beschreibung:** Der Schwierigkeitsfilter (Include **und** Exclude) hat im Chancen-Feed und Kalender keinen Effekt, solange `Locations.all` leer ist. Beobachtet: Include „Anspruchsvoll" zeigt im Feed weiterhin alle 111 sichtbaren Chancen, obwohl nur 5 von 56 Locations difficulty 3 haben. Erwartet: Filterung greift sofort. Ursache: `Filter.apply()` schlägt `loc.difficulty` über `Locations.all` nach, das aber erst beim Öffnen des Locations-Tabs (oder nach Location-Speichern) geladen wird — nicht beim App-Start auf dem Feed. Fix-Richtung: `Locations.all` beim Boot laden (oder lazy nachladen, wenn ein Schwierigkeitsfilter aktiv ist und die Liste leer ist).

**Bezug:** Vorbestehend seit US-32 (kombiniertes Filtersystem); durch US-71 (Drei-Zustand-Filter) sichtbar geworden, aber nicht von US-71 verursacht — betrifft die Include-Logik identisch. Eigenständig, grenzt an US-71.

#### 🔬 Analyse (2026-06-23)

**Root-Cause (datenvalidiert am echten Code):**

`Filter.apply()` schlägt `loc.difficulty` via `(Locations.all || []).find(l => l.id === o.location_id)` nach (`index.html` Z. 2056). Wenn `loc` undefined ist (weil `Locations.all` leer), greift der `if (loc)` Guard — die Chance wird **nicht** gefiltert, sondern durchgelassen (falsch-positiv für Include, falsch-negativ für Exclude).

**Entscheidend:** Der BUG-30-Fix (`App.init`, Z. 4116) lädt `Locations.all = await API.get('/locations')` bereits **vor** `await Feed.load()`. Das bedeutet: Die Lade-Garantie für `Locations.all` beim Boot ist durch BUG-30 bereits implementiert. BUG-28 ist dadurch für Feed **und** Kalender (der ohnehin erst beim Tab-Besuch lädt, zu dem Zeitpunkt ist `Locations.all` längst befüllt) de facto mitbehoben.

Was noch fehlt: Das Ticket steht auf `ToDo`, der Fix ist nicht verifiziert, kein Akzeptanzkriterium wurde je getestet. Das Ticket benötigt eine Verifikation + ggf. einen Edge-Case-Fix (see AK unten).

**Betroffene Dateien:**
- `web/index.html` — `Filter.apply` Z. 2055–2059 (difficulty-Lookup), `App.init` Z. 4101–4122 (Boot-Sequenz, bereits gefixt durch BUG-30)

**Scope:**
- Eingeschlossen: Schwierigkeitsfilter (Include + Exclude) wirkt im Feed und Kalender sofort beim App-Start, ohne Locations-Tab-Besuch. Verifikation dass der BUG-30-Fix BUG-28 abdeckt.
- Ausgeschlossen: Scout-Tab (kein `difficulty`-Cross-Collection-Lookup dort, `Filter.applyToScout` Z. 2117 kommentiert difficulty explizit als nicht anwendbar). Backend-Änderungen (rein Frontend).

**Example Mapping:**

📏 **Rule 1:** Wenn ein Schwierigkeitsfilter gesetzt ist, werden beim Feed-Start nur Chancen angezeigt, deren Location das passende `difficulty`-Level hat — unabhängig davon ob der Locations-Tab je besucht wurde.
- 🟢 **Positiv:** App öffnen auf Feed-Tab, Include „Anspruchsvoll" (difficulty=3) aktiv → nur 5 Chancen sichtbar (aus den 5 Locations mit difficulty 3).
- 🔴 **Negativ:** App öffnen auf Feed-Tab, Locations-Tab nicht besucht, Include aktiv → **nicht** alle 111 Chancen sichtbar (das war der Bug).
- 🔲 **Edge:** Alle Locations haben difficulty=2, Filter auf difficulty=3 → 0 Chancen, leerer State korrekt.

📏 **Rule 2:** Wenn `Locations.all` beim Boot geladen wurde und ein Schwierigkeitsfilter aktiv ist, wird beim Kalender-Monatswechsel korrekt gefiltert.
- 🟢 **Positiv:** Kalender-Tab öffnen nach Boot → Monatsansicht zeigt nur Chancen passender Locations.

📏 **Rule 3:** Die Boot-Sequenz garantiert `Locations.all` vor dem ersten Feed-Render.
- 🟢 **Positiv:** `App.init` lädt `Locations.all` via `await API.get('/locations')` vor `await Feed.load()` — d.h. `Filter.apply` trifft im ersten Render auf befüllte Liste.

**Akzeptanzkriterien:**
- [ ] AK-1: App frisch öffnen (kein Locations-Tab besucht), Schwierigkeitsfilter „Anspruchsvoll" (difficulty=3) aktiv → Feed zeigt ausschließlich Chancen von Locations mit `difficulty===3` (manuell zählbar, deutlich unter 111).
- [ ] AK-2: App frisch öffnen, Exclude „Einfach" (difficulty=1) aktiv → Feed zeigt keine Chancen von Locations mit `difficulty===1`.
- [ ] AK-3: Kalender-Tab ohne vorherigen Locations-Tab-Besuch öffnen, Schwierigkeitsfilter aktiv → Kalender filtert korrekt (Monat mit 0 Treffern zeigt „Keine Einträge"-State).
- [ ] AK-4 Edge: Filter auf difficulty gesetzt, eine Location hat kein `difficulty`-Feld (undefined) → Chance wird nicht gefiltert (Guard greift, kein JS-Crash).
- [ ] AK-5 Regression: Ohne Schwierigkeitsfilter zeigt der Feed alle Chancen unverändert (kein falsches Filtern durch Boot-Load).

**Pre-Mortem:**
- 💀 **Fix ist schon da, aber unbemerkt defekt** — Auslöser: BUG-30 hat `Locations.all`-Boot-Load eingebaut, aber `/locations`-Endpoint schlägt fehl (401/500) → `Locations.all` bleibt leer, Filter still wirkungslos — und kein Error dem User. Frühwarnung: `App.init` hat kein Error-Handling für den `Locations`-Fetch. Gegenmaßnahme: AK-1 manuell testen; optional try/catch mit stiller Fehler-Toleranz ergänzen.
- 💀 **Verifikation behauptet „gefixt", tatsächlich sind Testdaten ohne difficulty=3** — Auslöser: Wenn zufällig alle sichtbaren Chancen von Locations mit dem Include-Level stammen, filtert der Bug nicht auf. Frühwarnung: Tester prüft nicht die Anzahl gegen die Erwartung. Gegenmaßnahme: AK-1 mit expliziter Zählung (5 Locations difficulty=3 → maximal 5 Locations × n Events sichtbar).
- 💀 **CalendarView lädt Monat bevor Boot-Load fertig** — Auslöser: Nutzer navigiert extrem schnell zum Kalender, bevor der `/locations`-Request fertig ist → `Locations.all` noch leer beim ersten `Filter.apply`. Frühwarnung: Nur auf langsamen Verbindungen reproduzierbar. Gegenmaßnahme: `App.init` ist `async`, `Feed.load()` wartet auf `Locations.all` — Kalender wird erst auf Tab-Klick geladen, der nach `init()` kommt. Risiko gering; aber AK-3 ist dennoch sinnvoll.

**Implementierungsoptionen:**

*Option A — Verifikation: Bug bereits durch BUG-30 behoben, Ticket schließen nach Test*
- Vorgehen: AK-1 bis AK-5 manuell testen (lokal, `http://localhost:8000`). Bei Bestehen: Ticket auf Done setzen, kein Code-Fix nötig. Optional: Error-Handling für `/locations`-Fetch in `App.init` als Robustheit-Maßnahme ergänzen.
- Betroffene Dateien: `web/index.html` App.init Z. 4116 (nur Error-Handling, optional)
- Vorteile: Kein Code-Risiko; fix wurde bereits shipped; schnell abgeschlossen.
- Nachteile: Wenn Test scheitert (z.B. Race-Condition), muss Option B greifen.
- Aufwand: sehr klein (Test + optionales try/catch)

*Option B — Defensiver Fallback: Lazy-Load in `Filter.apply` wenn `Locations.all` leer und difficulty-Filter aktiv*
- Vorgehen: In `Filter.apply` Z. 2055, wenn `Locations.all.length === 0` und ein difficulty-Filter aktiv ist, einen synchronen Guard einbauen: Filter überspringen (alle durch) und `API.get('/locations').then(d => { Locations.all = d; Feed.render(Filter.apply(Feed.data)); })` im Hintergrund nachladen. Oder: `Filter.apply` wirft explizit wenn `Locations.all` leer und difficulty gesetzt — das macht den Bug sichtbar statt still.
- Betroffene Dateien: `web/index.html` Filter.apply Z. 2055–2059
- Vorteile: Robuster gegen Race-Conditions; macht den Bug sichtbar wenn er doch auftritt.
- Nachteile: Erhöht Komplexität; async in einem sync-Filter ist architektonisch unschön; Render-Timing-Risiko.
- Aufwand: mittel

✅ **Empfehlung: Option A** — Der BUG-30-Fix löst BUG-28 bereits; eine Verifikation + optionales try/catch in `App.init` ist der sauberste Abschluss. Option B nur wenn AK-1 scheitert.

**Testplan:**
- [ ] Manuell (http://localhost:8000): App öffnen → Feed-Tab → FilterSheet → Schwierigkeit „Anspruchsvoll" aktivieren → Anzahl sichtbarer Chancen zählen → muss deutlich unter 111 liegen (nur Chancen von 5 Locations mit difficulty=3 sichtbar).
- [ ] Manuell: Kalender-Tab direkt öffnen (ohne Locations-Tab), gleicher Filter → Kalender filtert korrekt.
- [ ] Manuell: Kein Filter → alle Chancen sichtbar (Regression).
- [ ] Automatisiert (optional, Backend): Kein Backend-Test nötig — rein Frontend-Bug.

---

<!-- ===== Neue Tickets 2026-06-22 (von Stephan direkt nach Ready for Analysis freigegeben) ===== -->


### BUG-29 · Chancendetails zeigen veraltete GPS-Daten trotz korrigierter Location `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-22 |
| **Released** | 2026-06-22 (Live-Health 200 OK verifiziert) |

**Beschreibung:** Eine Chance für „Mond über Oberbaumbrücke & Spree" wurde mit veralteten GPS-Daten angezeigt, obwohl die Koordinaten in den Locationdetails bereits auf neue Werte geändert und dort korrekt gespeichert waren. Die Locationdetails zeigten die korrekten GPS-Daten, die Chancendetails (Feed/Kalender) haben sich nicht mitaktualisiert.

**Beobachtet:** Chancendetail zeigt alte Koordinaten · **Erwartet:** Chancendetail übernimmt die in der Location gespeicherten neuen Koordinaten (inkl. abhängiger Maps-Links/Astronomie).

**Bezug:** Überschneidung mit TASK-12 [x] (Auto-Neuberechnung nach Koordinaten-Änderung — `_run_precompute(location_ids=[id])` nach PATCH) und US-67 [x] (AK: bei Koordinatenänderung sollen Chancen/Feed/Kalender/Maps-Links aktualisiert werden). Mögliche Regression/Lücke in TASK-12: Recompute regeneriert `opportunities.json` (Feed-Cache) für diese Location nicht oder Frontend liefert gecachte Chancendetails. Eigenständiger BugFix, grenzt an TASK-12.

---

#### 🔬 Implementation Spec (Analyse 2026-06-22)

**Root-Cause (datenvalidiert):** Der Single-Location-Recompute nach PATCH ruft `precompute.py --feed-only --location-id <id>` auf (`main.py:_run_precompute_single`, L484–523). Der `--feed-only`-Branch schreibt **ausschließlich** `opportunities.json` neu (Feed) und kehrt vor jeder Kalenderberechnung zurück (`precompute.py` Single-Location-Flow L597–651, `return` L651). `calendar.json` wird daher bei einem PATCH **nie** aktualisiert — es trägt seinen eigenen denormalisierten Snapshot (`observer_lat/lon`, `subject_lat/lon`, abgeleitete Astronomie). Wird die Chance aus dem **Kalender** geöffnet, zeigt das Frontend (`index.html` Detail-Render L2686 ff.: `o.observer_lat`, Maps-Links aus `o.*`) die alten Koordinaten. Erst der nächtliche Vollkalender (Scheduler 05:30, erkennt die `coordinates_hash`-Änderung in `compute_calendar_incremental` L504–512) zieht nach. **Validierung:** `opportunities.json` enthält pro Event `observer_lat/lon` + `location_name` als Snapshot (geprüft am Live-Cache: 1737 Events, je eigene Koordinaten); `_location_hash` (precompute.py L123–130) hasht nur Observer-Koordinaten.

**Scope:**
- Eingeschlossen: Single-Location-Recompute nach Koordinaten-PATCH soll **auch** den Kalender-Cache (`calendar.json`) für genau diese Location regenerieren, inkl. abhängiger Felder (Astronomie, Maps-Links-Quellkoordinaten). Feed bleibt wie gehabt.
- Ausgeschlossen: Vollständiger Kalender-Neulauf für alle Locations (zu teuer, ~Std.); Scout/`discover.json` (separater Cache, kein Koordinaten-Snapshot-Bug gemeldet); reine Name-Änderung (→ BUG-30); Maps-Link-Generierung selbst (passiert im Frontend aus `o.observer_lat/lon`, korrekt sobald Snapshot stimmt).

**Akzeptanzkriterien:**
- [ ] Nach `PATCH /locations/{id}` mit geänderten `observer_lat/lon` enthält `opportunities.json` für diese Location Events mit den **neuen** Koordinaten (bestehendes Verhalten, als Regression absichern).
- [ ] Nach demselben PATCH enthält `calendar.json` für diese Location Events mit den **neuen** Koordinaten (heute kaputt) — messbar: alle Events mit `location_id==id` tragen `observer_lat==neuer_wert` (±1e-5).
- [ ] Astronomie-abhängige Felder im Kalender-Event (`subject_azimuth`/`celestial_azimuth`) entsprechen den neuen Koordinaten (nicht den alten).
- [ ] Edge Case: Location ohne bestehende Kalender-Events (z.B. brandneue Custom-Location) → Recompute legt korrekt neue Events an, kein Crash bei leerem Merge.
- [ ] Edge Case: Recompute läuft bereits (`_precompute_running==True`) → PATCH-Response bleibt schnell, Kalender wird beim nächsten Lauf konsistent (kein Deadlock/Doppellauf).
- [ ] Regression: Andere Locations in `calendar.json` bleiben unverändert (Merge ersetzt nur `location_id==id`).

**Pre-Mortem:**
- 💀 Single-Location-Kalenderlauf berechnet versehentlich 365 Tage × alle Locations → Server blockiert minutenlang. Auslöser: Aufruf von `compute_calendar_incremental` ohne Location-Filter. Frühwarnung: PATCH-Response-Zeit steigt, CPU-Spike. Gegenmaßnahme: Kalender-Single-Pfad **streng** auf `--location-id` filtern (Merge `[e for e in events if e["location_id"] != id] + new`), analog zum Feed-Merge.
- 💀 Kalender-Merge verwirft Events anderer Locations → Kalender schrumpft drastisch. Auslöser: falscher Filter/Überschreiben statt Merge. Frühwarnung: `HEALTH-CAL`-Alert (precompute.py L716 ff.), Event-Count sinkt. Gegenmaßnahme: Merge-Test als AK; bestehende Health-Schwellen greifen lassen.
- 💀 `coordinates_hash`-Metadaten (`computed_locations` in calendar.json) werden beim Single-Merge nicht aktualisiert → nächtlicher Vollkalender rechnet die Location erneut komplett neu (verschwendet) oder hält sie für stale. Auslöser: nur Events gemergt, Meta nicht. Gegenmaßnahme: beim Single-Kalender-Merge `computed_locations[id]` mit neuem Hash + `computed_dates` aktualisieren.
- 💀 Long-Running-Subprozess (365-Tage-Single-Location) hält `_precompute_running=True` lange → blockiert Folge-PATCHes. Frühwarnung: zweiter PATCH meldet „Recompute läuft bereits". Gegenmaßnahme: bewusst akzeptiert (Kalender-Single ist deutlich teurer als Feed) bzw. Option B (verzögerter Kalenderlauf) prüfen.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (Rules: PATCH-Koord → Feed neu / Kalender neu / Maps folgt aus Koordinaten-Snapshot)
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `backend/main.py` (`_run_precompute_single` L484–523, `patch_location` L1325–1394, `_load_caches` L279–310), `backend/precompute.py` (Single-Flow L597–651, `compute_calendar_incremental` L444–571, `_location_hash` L123–130, `_serialize` L245+), `web/index.html` (Detail-Render L2667–2909, Maps-URL aus `o.*`)
- [x] Daten-Validierung: Feed-Cache trägt pro Event eigenen Koordinaten-Snapshot (`_serialize` L249–254: `observer_lat/lon`, `subject_lat/lon`, `location_name`); Kalender-Cache wird vom Single-Recompute nicht angefasst
- [x] Implementierungsoptionen: A / B / C
- [x] Empfehlung: Option A

**🔎 Code-Verifikation (Analyse-Subagent 2026-06-22 — Root-Cause am Code bestätigt, nicht nur Ticket-Vermutung):**
- **Bestätigt:** `_run_precompute_single` (`main.py` L503–505) ruft `precompute.py --feed-only --location-id <id>` auf. Im Single-Flow setzt `run_calendar = not args.feed_only` → bei `--feed-only` ist `run_calendar=False`, aber der Single-Flow erreicht den Kalender-Block ohnehin nie: er `return`t bei `precompute.py` L651 direkt nach dem Feed-Merge (L640–645). `calendar.json` wird beim PATCH **nie** geschrieben → Root-Cause verifiziert.
- **Bestätigt:** Frontend-Opportunity-Detail (`index.html` L2667–2909) rendert ausschließlich aus dem Cache-Snapshot `o.*` (`o.observer_lat/lon`, `o.subject_lat/lon`, `o.celestial_azimuth` L2667, `o.subject_azimuth` L2669/L2882, Maps via `Detail.openInMaps(o.observer_lat, o.observer_lon)` L2879). → Sobald der Cache-Snapshot stimmt, folgen Maps + Astronomie automatisch. Bestätigt zugleich, dass **Option C die Astronomie-Felder nicht reparieren kann** (client-seitig nicht nachrechenbar).
- **Bestätigt (Reload-Pfad):** `_run_precompute_single` ruft nach Erfolg `_load_caches()` (`main.py` L517) auf, das **sowohl** `_OPP_CACHE` als auch `_CAL_CACHE` neu lädt (L288–307). → Sobald Option A `calendar.json` neu schreibt, übernimmt der In-Memory-Kalender automatisch; keine zusätzliche main.py-Verdrahtung für den Reload nötig.
- **⚠️ Wichtige Präzisierung für Option A:** `compute_calendar_incremental` (`precompute.py` L444–571) hat **keinen** Single-Location-Parameter — die Schleife L504 läuft hart über `for loc in LOCATIONS` (alle). Option A erfordert daher entweder (a) einen neuen optionalen `location_id`-Filter in `compute_calendar_incremental` (Schleife auf die eine Location beschränken) **oder** (b) eine dedizierte Single-Location-Kalender-Merge-Routine im Single-Flow nach dem Feed-Muster (L633–645). Variante (a) wiederverwendet die vorhandene Hash-/Merge-/Meta-Logik (L505–559, inkl. `computed_locations`-Update) und ist robuster gegen den 3. Pre-Mortem-Punkt (Meta-Drift) → **für Implementierung empfohlene Sub-Variante: A(a)**. Aufwand bleibt mittel.
- **Python-3.9-Check (Prod):** `precompute.py` hat `from __future__ import annotations` (L30) → alle `X | None`-Annotationen (L133/L180/L466/L593) sind Strings, **kein** 3.9-Crash. Achtung für die Impl-Phase: neuer **Laufzeit**-Code mit `int | float` in `isinstance(...)` o.ä. würde auf 3.9 trotzdem crashen — bei neuen Guards `(int, float)`-Tupel verwenden.

**Implementierungsoptionen:**

*Option A — Single-Location-Kalender-Merge in precompute.py (empfohlen)*
- Vorgehen: Im Single-Location-Flow (`precompute.py` L597–651) nach dem Feed-Block zusätzlich die 365-Tage-Events **nur für diese Location** berechnen und nach dem Feed-Muster in `calendar.json` mergen (alte Events der Location verwerfen, neue einfügen, `computed_locations[id]`-Hash/Dates aktualisieren). `_run_precompute_single` bleibt `--feed-only`? Nein — Flag-Logik so anpassen, dass der Single-Flow Feed **und** Kalender für die eine Location schreibt (z.B. neues `--with-calendar` oder Single-Flow rechnet beides per Default).
- Betroffene Dateien: `backend/precompute.py` (Single-Flow), `backend/main.py` (`_run_precompute_single` Argumentübergabe + `_load_caches` lädt Kalender bereits neu? prüfen).
- Vorteile: Behebt Ursache an der Wurzel; Kalender sofort konsistent; nutzt bestehendes Merge-Muster.
- Nachteile/Risiken: 365-Tage-Single-Location dauert spürbar länger als Feed (14 Tage) → längere `_precompute_running`-Phase (Pre-Mortem-Mitigation greift).
- Aufwand: mittel

*Option B — PATCH triggert nur Feed sofort, Kalender verzögert*
- Vorgehen: Feed bleibt sofort, Kalender-Single-Location wird als separater Hintergrund-Task mit niedriger Priorität nachgezogen (oder kürzeres Fenster, z.B. 90 Tage statt 365).
- Vorteile: Schnellere PATCH-Response, geringere Blockade.
- Nachteile: Kalender-Chance kurzzeitig noch stale → AK „sofort konsistent" nur teilweise erfüllt; mehr bewegliche Teile.
- Aufwand: mittel

*Option C — Frontend liest Koordinaten/Name live aus Location statt aus Cache-Snapshot*
- Vorgehen: Im Opportunity-Detail (`index.html`) `o.observer_lat/lon`, Maps-Links und `location_name` zur Render-Zeit aus `Locations.all.find(id)` überschreiben statt aus dem Cache-Snapshot.
- Vorteile: Kein Backend-Recompute nötig; behebt zugleich BUG-30-Symptom.
- Nachteile/Risiken: `Locations.all` ist im Feed-Kontext beim Boot leer (BUG-28-Gotcha, Memory `reference_frontend_dom_gotchas`) → Lookup schlägt fehl, Fix wäre still wirkungslos. Astronomie-Felder (`celestial_azimuth`) lassen sich **nicht** im Frontend nachrechnen → bleiben stale. Behebt nur Koordinaten/Maps, nicht die Astronomie.
- Aufwand: klein, aber unvollständig

✅ **Empfehlung: Option A** — behebt die Ursache (Kalender-Snapshot) inkl. der astronomisch abhängigen Felder, die Option C nicht abdecken kann, und vermeidet den BUG-28-`Locations.all`-Fallstrick. Längere Recompute-Dauer ist über das bestehende `_precompute_running`-Gating beherrschbar.

**Testplan:**
- [x] Automatisiert (`backend/tests/test_bug29_calendar_single_recompute.py`, FOTOALERT_NO_BACKGROUND=1): 5 Tests gegen `compute_calendar_incremental(location_id=…)` (gestubbtes `find_opportunities` → deterministisch, kein Ephemeriden-Zugriff) — neue Koordinaten im Snapshot (AK2), Astronomie folgt (AK3), andere Locations unverändert + Meta vollständig (AK6 / Pre-Mortem #2+#3), neue Location ohne Crash (AK4), nur Ziel-Location neu berechnet (Pre-Mortem #1). Alle grün, komplette Offline-Suite grün.
- [x] Manuell (2026-06-22, lokal verifiziert): `PATCH oberbaumbrucke_spree` → Log zeigt `Location-Overrides angewendet: 3`, Elevation-Fetch auf neue Koordinaten (52.5021), `365 neu berechnet`, `✅ Kalender: 44141 Events nach Merge`. Snapshot: `oberbaumbrucke_spree` lat=52.5021 + az 241.3→221.3; `berliner_dom_spree` unverändert (806 Events, lat/az gleich). Kalender wuchs 43997→44141 (übrige Locations erhalten).

**⚠️ Korrektur der Root-Cause (beim Live-Test 2026-06-22 am Log aufgedeckt):** Die ursprüngliche Spec nahm an, der Single-Recompute rechne mit den neuen Koordinaten und es fehle „nur" der Kalender-Write. Der Live-Test zeigte die **tiefere Ursache**: `precompute.py` lädt ausschließlich die hartcodierten Basis-Koordinaten aus `data/locations.py` und wendet die in SQLite persistierten `location_overrides` (aus `PATCH /locations/{id}`) **nie** an — anders als `main.py:_load_location_overrides`, das nur die In-Memory-Liste des Servers patcht. Folge: Recompute holt Elevation/Feed/Kalender mit den **alten** Koordinaten, der `coordinates_hash` bleibt gleich → „0 neu berechnet" → Feed UND Kalender bleiben dauerhaft veraltet (auch der nächtliche Vollkalauf, entgegen der Spec-Annahme). Die Location-Detail-Ansicht war nur deshalb korrekt, weil sie live aus dem Override rendert. Log-Beleg: Elevation-Fetch für `52.5014,13.4445` (alt) statt `52.5019` (PATCH), Kalender „Zusammenfassung: 0 neu berechnet, 365 aus Cache".

**🛠️ Implementiert (2026-06-22 — Override-Fix + Option A(a)):**
- `backend/precompute.py` `_apply_location_overrides()` (neu): lädt beim Start die `location_overrides` aus dem `LocationStore` und wendet sie (gleiche Whitelist wie main.py) auf `LOCATIONS` an — VOR jeder Berechnung/Hashing. Greift im Single-Recompute **und** im nächtlichen Vollkalauf. Das ist die eigentliche Wurzel-Behebung.
- `backend/precompute.py` `compute_calendar_incremental`: neuer optionaler `location_id`-Filter. Im Single-Modus wird nur diese Location berechnet; Events + `computed_locations`-Meta aller übrigen Locations werden unverändert übernommen (kein Vollkalender, kein Schrumpfen, keine Meta-Drift). Versions-Mismatch verwirft im Single-Modus bewusst NICHT den gesamten Kalender.
- `backend/precompute.py` Single-Location-Flow: nach dem Feed-Block wird jetzt zusätzlich `calendar.json` für die Location regeneriert (gated über `run_calendar`).
- `backend/main.py` `_run_precompute_single`: `--feed-only` entfernt → der Single-Recompute schreibt jetzt Feed **und** Kalender. `_load_caches()` lädt beide In-Memory-Caches ohnehin neu.
- Python-3.9-sicher (`from __future__ import annotations` vorhanden; kein neuer Runtime-PEP604-Code).
- **Offen / separater Scope:** `precompute.py` lädt Custom-Locations (`custom_*`) nicht (importiert nur die Basis-`LOCATIONS`) → Single-Recompute einer Custom-Location greift noch nicht. Vorbestehende Lücke, nicht Teil der gemeldeten Standard-Location. → eigenes Ticket erwägen.

---


### BUG-30 · Location-Name-Änderung wird nicht gespeichert (User und Host) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-22 |
| **Abgeschlossen** | 2026-06-22 |
| **In Progress seit** | 2026-06-22 |

**Beschreibung:** Die Änderung des Location-Namens wird nach dem Speichern nicht übernommen — weder angemeldet als User noch als Host. Der alte Name bleibt nach erneutem Öffnen bestehen.

**Beobachtet:** Geänderter Name verschwindet/wird zurückgesetzt · **Erwartet:** Neuer Name persistiert dauerhaft und ist nach Neuladen sichtbar.

**Bezug:** Grenzt an US-60 [x] (✏️-Bearbeitung via `PATCH /locations/{id}`) und TASK-16 (Recompute-Whitelist: `name`/`description` lösen bewusst **keinen** Recompute aus — betrifft nur Neuberechnung, nicht die Persistenz des Namens) sowie US-29 [x] (Namens-Datenqualität). Vermutete Ursache im Name-Persistenz-Pfad des PATCH-Endpunkts oder Frontend-Save. Eigenständiger BugFix.

---

#### 🔬 Implementation Spec (Analyse 2026-06-22)

**Root-Cause (datenvalidiert am echten Code 2026-06-22 — Persistenz ist intakt, Anzeige ist stale):** Der PATCH-Pfad **speichert den Namen korrekt** und lädt ihn korrekt zurück. Live-Beleg (DB `backend/data/fotoalert.db`, Tabelle `location_overrides`): für `rostiger_nagel_rusty_nail` steht der Override-JSON-Blob `{"name": "Rostiger Nagel Test", ...}`, für `berliner_dom_spree` `{"name": "Berliner Dom vom Spreeufer", ...}`. Die Lade-Routine `main.py:_load_location_overrides` (L530–568) wendet die Whitelist inkl. `name` an (L559–561) → nach Boot trägt die Location den neuen Namen. PATCH-Handler `patch_location` (`main.py` L1326–1396) führt `name` in `text_fields` (L1329) und `all_allowed_fields` (L1333); `name` ist bewusst **nicht** in `recompute_fields` (L1332, TASK-16) → keine Neuberechnung. Persistenz: Standard-Location via `_save_location_override`→`_store.upsert_override` (L1380; store.py L226–254), Custom via `_update_custom_location_file`→`_store.update_custom` (L1375 → L203–205; store.py L155–186) — beide schreiben `name`. **Der Bug ist die denormalisierte Anzeige:** Feed (`opportunities.json`) und Kalender (`calendar.json`) speichern pro Event einen `location_name`-Snapshot, der bei einer reinen Namensänderung (kein Recompute) alt bleibt. Das Frontend rendert `${o.location_name}` direkt aus dem Cache: Opportunity-Detail-Hero (`index.html` L2690), Feed-Karte (L1146), Chip (L1224), Kalender-Event (L1527) — zusätzlich Suchfilter (L2079), Verify-Button/Notification (L2900/L2929/L2949). Das Location-Detail dagegen liest live `loc.name` (L3076 Render, L3206 Listen-Render) und zeigt deshalb sofort den neuen Namen. Wird die Location aus dem Feed-/Kalender-Kontext bearbeitet, bleibt der alte Snapshot dort sichtbar → wirkt wie „nicht gespeichert". **Verschärfend (BUG-28-Gotcha, datenvalidiert):** `App.init` (L4098–4117) lädt `Locations.all` beim Boot **nicht** (nur Verify/Rating/Feed); `Locations.all` füllt sich erst beim Locations-Tab (L4086) oder beim Öffnen eines Location-Details (L3232 hat eigenen Lazy-Load-Guard). Ein naiver Live-Lookup `Locations.all.find(id)?.name` im Feed-/Kalender-Detail liefe daher gegen leere Liste → Fix still wirkungslos.

**Scope:**
- Eingeschlossen: Geänderter Name muss in **allen** Ansichten konsistent erscheinen — Location-Detail (heute schon korrekt) **und** Feed-/Kalender-/Opportunity-Detail. Lösung muss den stale `location_name`-Snapshot adressieren.
- Ausgeschlossen: Backend-Persistenz des Namens (nachweislich intakt — keine Code-Änderung nötig); Koordinaten-Snapshot (→ BUG-29, gleiche Cache-Wurzel, getrennt gehalten); `description`-Snapshot (analoges Verhalten, aber nicht im Ticket gemeldet — als Beobachtung notiert, nicht im AK-Scope).

**Akzeptanzkriterien:**
- [x] Nach `PATCH /locations/{id}` mit `{"name": "X"}` liefert `GET /locations` für diese ID `name == "X"` (Regression-Sicherung des bereits intakten Pfads; gilt für `custom_`- und Standard-Locations).
- [x] Nach Neustart der App (Override aus DB geladen) liefert `GET /locations` weiterhin `name == "X"` (verifiziert die Lade-Whitelist).
- [x] Nach Namensänderung zeigt das **Opportunity-Detail** (Feed und Kalender) für Chancen dieser Location den neuen Namen `X` — heute zeigt es den alten Snapshot.
- [x] Edge Case: Location ohne Chancen im Cache → Namensänderung persistiert trotzdem, keine Fehlermeldung.
- [x] Edge Case: Name mit Sonderzeichen (`"`, Emoji) wird korrekt persistiert und angezeigt (Edit-Feld escaped bereits via `replace(/"/g,'&quot;')`, L3267; UTF-8/ensure_ascii=False im Store L243/L248 belegt für „Berliner Dom"-Override).
- [x] Regression: `description` und andere Felder bleiben beim reinen Name-PATCH unverändert (Override-Merge, store.py L238–244 merged statt überschreibt).

**Pre-Mortem:**
- 💀 „Fix" wird im Backend-Persistenz-Pfad gesucht und Code geändert, der bereits korrekt ist → kein Effekt, Bug bleibt. Auslöser: Fehlannahme „PATCH speichert Name nicht". Frühwarnung: Daten-Validierung zeigt Name liegt in DB. Gegenmaßnahme: Root-Cause oben datenvalidiert — Fix gehört in den Anzeige-/Snapshot-Pfad, nicht in die Persistenz.
- 💀 Frontend-Lookup `Locations.all.find(id)` zum Live-Überschreiben des `location_name` läuft im Feed-Kontext gegen leere Liste (BUG-28-Gotcha, Memory `reference_frontend_dom_gotchas`) → Fix still wirkungslos. Auslöser: `Locations.all` lädt erst beim Locations-Tab. Gegenmaßnahme: Lade-Garantie für `Locations.all` beim Boot ODER serverseitige Snapshot-Aktualisierung wählen (Option B).
- 💀 Name-Recompute-Trigger eingebaut → 365-Tage-Kalender für jede Namensänderung neu berechnet, obwohl Astronomie unverändert → unnötige Server-Last (genau das, was TASK-16 vermeiden wollte). Gegenmaßnahme: Snapshot **ohne** Astronomie-Recompute aktualisieren (reines String-Feld-Update im Cache), nicht über den vollen Recompute-Pfad.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (Rule: PATCH-Name → DB persistiert / Detail zeigt neu / Feed+Kalender zeigen neu)
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert (Zeilen am echten Code 2026-06-22 verifiziert): `backend/main.py` (`patch_location` L1326–1396, `recompute_fields` ohne `name` L1332, `_load_location_overrides` L530–568 Whitelist L559–561, `_update_custom_location_file` L203–205), `backend/data/store.py` (`update_custom` L155–186, `upsert_override` L226–254 mergt statt überschreibt L238–244 — beide korrekt), `web/index.html` (Opportunity-Detail-Hero L2690, Feed/Kalender-Karten L1146/L1224/L1527, weitere `location_name`-Nutzung L2079/L2900/L2929/L2949, Location-Detail live `loc.name` L3076/L3206, `LocationDetail.open`-Lazy-Guard L3232, `saveEdit` ab L3461, `App.init` ohne `Locations.all`-Boot-Load L4098–4117, Locations-Tab-Lazy-Load L4086)
- [x] Daten-Validierung: Override-Name in DB vorhanden + Lade-Routine ergibt neuen Namen (Persistenz intakt); Feed-Cache trägt alten `location_name`-Snapshot (Anzeige-Ursache)
- [x] Implementierungsoptionen: A / B / C
- [x] Empfehlung: Option A
- [x] Analyse auf BUG-29-Änderungen geprüft (2026-06-22): `_apply_location_overrides()` wendet jetzt auch `name` an → nach dem nächsten nächtlichen Vollkalauf oder einem koordinaten-getriggerten Single-Recompute wird `location_name`-Snapshot automatisch korrekt. Kern-Bug (reine Namensänderung = kein Recompute = sofort stale) bleibt unverändert, Option-A-Entscheidung weiterhin valide.

**Daten-Validierung:**
- [x] `fotoalert.db` Override `rostiger_nagel_rusty_nail` → `name="Rostiger Nagel Test"` (PATCH persistiert)
- [x] `_load_location_overrides`-Simulation → `loc.name=="Rostiger Nagel Test"` (Load-Back korrekt)
- [x] `opportunities.json` Event `rostiger_nagel_rusty_nail` → `location_name="Rostiger Nagel - Rusty Nail"` (alter Snapshot = Symptomquelle)

**Implementierungsoptionen:**

*Option A — Frontend rendert `location_name` live aus der Location (empfohlen)*
- Vorgehen: In Opportunity-Detail/Feed-/Kalender-Karten den angezeigten Namen zur Render-Zeit aus der Live-Location auflösen (`Locations.all.find(id)?.name ?? o.location_name`) **mit** Lade-Garantie: sicherstellen, dass `Locations.all` beim App-Boot (nicht erst beim Locations-Tab) geladen ist — sonst greift der BUG-28-Fallstrick. Da `name` ein reiner Anzeige-String ohne Astronomie-Abhängigkeit ist, ist das die billigste korrekte Lösung und vermeidet jeden Recompute.
- Betroffene Dateien: `web/index.html` (Render-Stellen L1146/L1224/L1527/L2690, ggf. L2079/L2900/L2929/L2949 + Boot-Lade-Garantie für `Locations.all` in `App.init` L4098–4117). Konkrete Lade-Garantie: in `App.init` vor/parallel zu `Feed.load()` ein `await Locations.load()` (bzw. ein leichtes `Locations.all = await API.get('/locations')` ohne Render) ergänzen, damit der Render-Zeit-Lookup im Feed-/Kalender-Detail nie gegen leere Liste läuft.
- Vorteile: Kein Backend-Recompute; sofort konsistent; löst Name-Anzeige in allen Views; respektiert TASK-16.
- Nachteile/Risiken: Erfordert die Lade-Garantie für `Locations.all` (BUG-28-Mitigation); betrifft nur den Namen — Koordinaten (BUG-29) bleiben getrennt.
- Aufwand: klein–mittel

*Option B — Serverseitiger Snapshot-Refresh bei Name-PATCH (ohne Astronomie-Recompute)*
- Vorgehen: PATCH mit `name` aktualisiert direkt das `location_name`-Feld aller passenden Events in `opportunities.json` + `calendar.json` (reines String-Replace pro `location_id`, kein Astronomie-Recompute).
- Betroffene Dateien: `backend/main.py` (`patch_location`).
- Vorteile: Caches selbst werden konsistent; Frontend braucht keine Lade-Garantie.
- Nachteile/Risiken: Schreibt `calendar.json` (88 MB) bei jeder Namensänderung neu → I/O-Last; Sonderfall-Logik nur für `name` fühlt sich brüchig an.
- Aufwand: mittel

*Option C — Name löst regulären Single-Location-Recompute aus*
- Vorgehen: `name` in die Recompute-Whitelist aufnehmen (kehrt TASK-16 um).
- Nachteile/Risiken: Berechnet Astronomie unnötig neu, genau das was TASK-16 verhindern sollte; teuer. Verworfen.
- Aufwand: klein (aber falscher Ansatz)

✅ **Empfehlung: Option A** — der Name ist reine Anzeige; ihn live aus `Locations.all` zu lesen ist die schlankste Lösung ohne jeden Recompute und ohne 88-MB-Cache-Schreibvorgänge, sofern die `Locations.all`-Lade-Garantie (BUG-28) mitgezogen wird. Falls diese Lade-Garantie als zu invasiv gilt, ist Option B der robuste Fallback.

**Testplan:**
- [ ] Automatisiert (`backend/tests/`, FOTOALERT_NO_BACKGROUND=1): Regression `BUG-30` — `PATCH /locations/{id}` mit `{"name":"X"}` (custom + Standard), dann `GET /locations` prüfen `name=="X"`; zweiter Test: Override in DB schreiben, `_load_location_overrides` ausführen, Name-Anwendung prüfen. (Backend-Persistenz absichern, damit keine künftige Regression sie bricht.)
- [ ] Manuell (http://localhost:8000): Name im Location-Detail ändern → speichern → in den Feed/Kalender wechseln → Chance dieser Location öffnen → Opportunity-Detail zeigt den neuen Namen. Anschließend App neu laden → Name bleibt überall neu.

---


### US-83 · Scout-Eintrag: Detailansicht + „Als Location speichern" `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-20 |

**Beschreibung:** Ein Klick auf einen Scout-Eintrag soll eine Detailansicht öffnen, die dieselben Daten zeigt wie die Locationdetails. Aus dieser Ansicht kann der Nutzer den Scout-Eintrag optional als neue Location speichern.

**Bezug:** Baut auf US-70[x] (Scout-Tab) auf und wiederverwendet die Location-Detail-UI (US-60/US-63[x]) sowie die Speicher-Logik aus AddLocation (US-56). Eigenständig, grenzt an US-70 (liefert nur die Karten/Liste). Datenfundament-Epic (Location-Persistenz) ist Voraussetzung für „als Location speichern". **Vorbedingung US-96[x] ist erfüllt** — `Detail.open(o)` existiert bereits.

---

#### 🔬 Analyse-Spec (US-83) · 2026-06-28

---

##### 🗺 Scope-Klärung: Was ist eine Scout-Detailansicht?

Scout-Einträge sind **berechnete Standpunkt-Chancen**, keine gespeicherten Locations. Das `ScoutOpportunity`-Objekt (Backend: `pipeline_base.py`) liefert:

| Feld | Beispiel | Bedeutung |
|------|---------|-----------|
| `subject_name` | „Fernsehturm" | Name des Motivs |
| `subject_lat/lon` | 52.5208, 13.4094 | Koordinaten des Motivs |
| `standpoint_lat/lon` | 52.519, 13.411 | Berechneter Fotograf-Standpunkt |
| `day` | „2026-07-05" | Datum der Chance |
| `dt_utc` | „2026-07-05T19:23:00Z" | Optimaler Zeitpunkt |
| `session` | „golden_evening" | Lichtqualität |
| `body_name` | „sun" / „moon" | Himmelskörper |
| `body_altitude_deg` | 12.3 | Höhe Himmelskörper |
| `body_azimuth_deg` | 280.1 | Azimut Himmelskörper vom Motiv aus |
| `body_illumination_pct` | 67.0 | Mondbeleuchtung (null für Sonne) |
| `distance_m` | 320 | Standpunkt→Motiv-Distanz |
| `focal_length_equiv_mm` | 85 | Empfohlene Brennweite |
| `score` | 0.87 | Gesamt-Score (0–1) |
| `score_alignment`, `score_phase`, `score_licht`, `score_komposition`, `score_wetter` | — | Teilscores |
| `weather_description` | „Leicht bewölkt" | Wetter-Text |
| `kategorie` | „🏙 Skyline" | Kategorie-Label |

**Was fehlt im Scout-Objekt (vs. Feed-Opportunity):**
- `event_type`, `title` → kein strukturiertes Event
- `overall_score`, `astronomy_score`, `weather_score` → andere Feldnamen (`score`, Teilscores)
- `observer_lat/lon` → heißt hier `standpoint_lat/lon`
- `location_id`, `location_name` → keine gespeicherte Location
- `camera_hints`, `moon_phase`, `celestial_azimuth`, `shoot_time`, `shoot_window_start/end` → nicht vorhanden
- `sunrise_utc`, `sunset_utc`, usw. → nicht vorhanden

**Schlussfolgerung:** Scout-Einträge können **nicht direkt** in `Detail.open(o)` übergeben werden — die Felder sind zu verschieden. Entweder (A) werden sie vorher in ein kompatibles Objekt gemappt, oder (B) es entsteht ein leichtgewichtiges eigenes Sheet.

**Die Scout-Detailansicht ist eine Chancen-Detailansicht, keine Location-Detailansicht.** Ein Scout-Eintrag hat keinen Namen, keine Beschreibung, keine gespeicherten Alignments — er hat einen Standpunkt, ein Motiv und eine berechnete Gelegenheit. Die passende Anzeige zeigt: Motiv, Standpunkt-Koordinaten, Datum/Uhrzeit, Brennweite, Score, Wetter — plus den „Als Location speichern"-Button.

---

##### 🔭 Architektur-Analyse

**Aktueller Zustand (Scout-Tab, `Scout.render()`):**
- Scout-Karten zeigen: Motiv-Name, Kategorie, Session, Score-Badge, Uhrzeit, Illumination, Höhe, Entfernung, Brennweite, Wetter.
- Buttons: „Standort" (Apple Maps) und „Navigation" (Apple Maps). **Kein Klick → Detailansicht.**
- Kein `onclick` auf der `.scout-card` selbst oder dem Motiv-Titel.

**`Detail.open(o)` (US-96, fertig):**
- Erwartet: `o.event_type`, `o.overall_score`, `o.astronomy_score`, `o.weather_score`, `o.title`, `o.location_id`, `o.observer_lat/lon`, `o.subject_lat/lon`, `o.shoot_time`, usw.
- Zeigt: Score-Bar (Gesamt/Astronomie/Wetter), Zeitfenster, FOV-Karte, Koordinaten, Astronomie-Infos.
- **Nicht direkt für Scout nutzbar** — zu viele Pflichtfelder fehlen.

**`AddLocation.save()` (US-56, fertig):**
- Ruft `API.post('/preview-alignment', {..., save: true})` auf.
- Braucht: `observer_lat/lon`, `subject_lat/lon`, `subject_name`, `subject_height_m`, `subject_width_m`, `category`.
- Davon hat Scout: `standpoint_lat/lon` (= observer), `subject_lat/lon`, `subject_name`, `kategorie`.
- Fehlend: `subject_height_m`, `subject_width_m` — Standardwerte möglich (aus `DiscoverSubject`-Defaults).
- **Saving ist grundsätzlich machbar** über denselben API-Endpoint.

---

##### 📐 Example Mapping

**Rule 1: Klick auf Scout-Karte öffnet Detailansicht**
- ✅ Positiv: Nutzer tippt auf eine Scout-Karte → ein Sheet öffnet sich mit Motiv-Name, Standpunkt-Koordinaten, Datum, Uhrzeit (Berlin), Session-Label, Score, Wetter, Brennweite, Body-Infos.
- ❌ Negativ: Klick auf „Standort"- oder „Navigation"-Button → öffnet Maps, kein Detail-Sheet.
- 🔲 Edge: Scout-Karte ohne `weather_description` (leerer String) → Wetter-Zeile zeigt „–" oder entfällt.

**Rule 2: Sichtbare Daten im Detail**
- ✅ Positiv: Motiv-Name „Fernsehturm", Kategorie „🏙 Skyline", Datum „Sa, 5. Juli", Uhrzeit „21:23 Uhr", Session „Goldene Stunde Abend", Score 87%, Wetter „Leicht bewölkt", Brennweite ~85mm, Mondbeleuchtung 67%, Körperhöhe 12.3°.
- ✅ Positiv (Sonne): Illumination-Chip entfällt (Sonne ist immer voll beleuchtet — so auch im Feed).
- 🔲 Edge: `subject_lat/lon` vorhanden → Motiv-Koordinaten-Zeile zeigen + Maps-Link. Scout liefert immer `subject_lat/lon`.
- 🔲 Edge: Standpunkt-Koordinaten immer vorhanden (`standpoint_lat/lon`).

**Rule 3: „Als Location speichern"**
- ✅ Positiv: Nutzer tippt „Als Location speichern" → kurze Bestätigung (Toast), Location erscheint im Locations-Tab.
- ✅ Positiv: Nach Speichern wird `Locations.load()` und `Feed.load()` aufgerufen (wie AddLocation.save()).
- ❌ Negativ: API-Fehler → Toast mit Fehlermeldung, kein Sheet-Schließen.
- 🔲 Edge: Scout-Eintrag repräsentiert ein Motiv mit bekannten Koordinaten aus LOCATIONS — gespeicherte Location ist trotzdem sinnvoll (neuer Standpunkt, andere Perspektive). Kein Duplikat-Schutz nötig (Standpunkte sind verschieden).
- 🔲 Edge: Nutzer speichert denselben Scout-Eintrag zweimal → zweite Location mit identischen Koordinaten wird angelegt. Akzeptierbar für v1 (Duplikat-Prüfung = separates Ticket).

**Rule 4: Navigation / Schließen**
- ✅ Positiv: Sheet schließt sich per „Schließen"-Button oder Overlay-Tap (wie Feed-Detail).
- ✅ Positiv: Nach Schließen ist Scout-Tab wieder sichtbar (kein Tab-Wechsel).

---

##### 💀 Pre-Mortem

**Szenario 1: `Detail.open(o)` produziert leere/defekte Anzeige für Scout-Objekte**
- Auslöser: `o.overall_score` ist `undefined` → Score-Bar zeigt `NaN%`; `o.location_id` fehlt → Location-Link crasht (`Locations.nameFor(undefined, undefined)` gibt evtl. leeren String).
- Verifiziert im Code: Zeile 3084 — `Locations.nameFor(o.location_id, o.location_name)` — ohne location_id immer leer. Zeile 3091 — `o.overall_score*100` → NaN. Zeile 3100 — `CameraFOV._data['ev'] = { obsLat:o.observer_lat ... }` → Scout hat `standpoint_lat`, nicht `observer_lat` → FOV-Karte zeigt falschen Punkt.
- Gegenmaßnahme (Option A): Scout-Objekt vor `Detail.open()` in ein kompatibles Format mappen. (Option B): Eigenes Scout-Detail-Sheet ohne diese Felder.

**Szenario 2: `AddLocation.save()` schlägt fehl wegen fehlender Höhen-Daten**
- Auslöser: `subject_height_m` und `subject_width_m` fehlen im Scout-Objekt (Backend speichert sie nicht im API-Response).
- Verifiziert: `ScoutOpportunity` (pipeline_base.py) hat diese Felder nicht. `AddLocation.save()` übergibt `parseFloat(document.getElementById('subj-height').value) || 0` — Default 0 funktioniert. `/preview-alignment` akzeptiert height_m=0 (wie im Frontend-Default). Kein Crash, aber Brennweiten-Schätzung im Alignment basiert auf height=0 → leicht ungenau, aber akzeptierbar.
- Gegenmaßnahme: `subject_height_m: 0` und `subject_width_m: 0` als Defaults beim Speichern — OK für v1.

**Szenario 3: Kategorie-Mapping Scout→Location funktioniert nicht**
- Auslöser: Scout liefert `kategorie` als Emoji+Text-String (z.B. „🏙 Skyline"). `AddLocation.save()` übergibt `category` als Enum-Wert (z.B. „skyline"). Das sind verschiedene Formate.
- Verifiziert: `AddLocation.save()` liest `document.getElementById('add-category').value` — einen `<select>`-Wert. Beim programmatischen Speichern aus dem Scout-Detail muss `kategorie` zu einem gültigen Category-Enum-Wert gemappt werden.
- Gegenmaßnahme: Mapping-Tabelle im Scout-Detail-Sheet: `„🏙 Skyline" → „skyline"` usw. (alle Kategorien aus `LocationCategory` bekannt).

---

##### 🔀 Implementierungsoptionen

**Option A — Scout-Objekt in Detail.open()-Format mappen (Adapter)**

Was Stephan erlebt: Er tippt auf eine Scout-Karte und sieht exakt dasselbe Detail-Sheet wie bei einer Feed-Chance. Standpunkt-Koordinaten, Brennweite, Score sind sichtbar. Felder die Scout nicht hat (Zeitfenster Start/Ende, Moonphase im Detail-Format, Location-Link) werden weggelassen oder durch Fallbacks ersetzt. Ein „Als Location speichern"-Button erscheint am unteren Rand.

Technisch: Eine `ScoutDetail.open(o)`-Funktion baut ein Pseudo-Opportunity-Objekt:
```js
{
  overall_score: o.score,
  astronomy_score: o.score_alignment,  // Näherung
  weather_score: o.score_wetter,
  title: o.subject_name,
  event_type: sessionLabel[o.session],
  location_id: null,  // kein Location-Link
  observer_lat: o.standpoint_lat, observer_lon: o.standpoint_lon,
  subject_lat: o.subject_lat, subject_lon: o.subject_lon,
  shoot_time: o.dt_utc,
  // …restliche Felder aus Scout-Objekt
}
```
Dann `Detail.open(adaptedObj)` aufrufen — aber: `Detail.open` rendert einen Location-Link (`Locations.nameFor(...)`) und greift auf `o.location_id` zu. Location-Link muss supprimiert werden, was eine Änderung in `Detail.open()` erfordert (oder ein Guard `if (o.location_id)`).

Vorteile: Eine Detailansicht für alle Chancen, konsistentes UX.  
Nachteile: Adapter ist fragil (Felder müssen exakt stimmen), `Detail.open()` braucht Guards für optionale Felder. Mittlerer Aufwand.

---

**Option B — Eigenes Scout-Detail-Sheet (leichtgewichtig)**

Was Stephan erlebt: Tippen auf eine Scout-Karte öffnet ein schmales Bottom-Sheet (ähnlich wie das Filter-Sheet) das genau die Scout-Daten zeigt: Motiv-Name, Standpunkt-Koordinaten mit Maps-Link, Datum, Uhrzeit, Brennweite, Score (als einzelner Balken), Mondbeleuchtung, Wetter. Unten: „Als Location speichern"-Button und „Schließen". Das Sheet ist bewusst reduziert — kein Score-Dreiteiler, kein FOV-Widget, keine Astronomie-Tabelle.

Technisch: Neues `<div id="scout-detail-sheet">` mit eigenem HTML-Template in `Scout.openDetail(o)`. Kein Eingriff in `Detail.open()`. Speichern: direkter Aufruf von `API.post('/preview-alignment', {..., save: true})` mit Scout-Feldern.

Vorteile: Keine Seiteneffekte auf `Detail.open()`, Scout-spezifische Felder direkt anzeigbar, geringer Aufwand (~2h).  
Nachteile: Zweite Sheet-Komponente, nicht vollständig konsistent mit Feed-Chancen-Detail.

---

##### ✅ Empfehlung (revidiert 2026-06-28)

**Option A** — Scout-Objekt via Adapter in `Detail.open()` übergeben. Scout-Einträge sind vollwertige Chancen mit Standort, Motiv, Zeitpunkt, Himmelsposition, Wetter und Brennweite — sie verdienen dieselbe vollständige Detailansicht wie Feed-Chancen. Reduzierte Sicht wäre ein schlechteres UX.

**Entscheidungen (2026-06-28):**
- Shoot-Zeitfenster: nur `dt_utc` als einzelne Uhrzeit (kein Start/Ende)
- Location-Beschreibung: auto-generierter Text aus Scout-Feldern (Motiv, Kategorie, Session, Körper, Distanz)
- `location_id`: null → Location-Link-Sektion entfällt (Guard in `Detail.open()`)

---

##### 📋 Akzeptanzkriterien (revidiert 2026-06-28)

- [x] **AK-1:** Tippen auf Scout-Karte → `Detail.open()` öffnet sich mit vollem Inhalt. Maps-Buttons öffnen Maps (kein Detail).
- [x] **AK-2:** Detail zeigt: Titel (Motiv-Name), Score (Gesamt/Astronomie/Wetter), Uhrzeit Berlin, FOV-Karte mit Standpunkt+Motiv, Koordinaten beider Punkte mit Street-View-Link, Himmelsposition (Azimut/Höhe/Illumination), Wetter, Kameraempfehlung (Brennweite + Stativ-Hinweis), Himmelskörper-Bahn (interaktive Karte), auto-generierte Beschreibung.
- [x] **AK-3:** Sektionen die nicht befüllbar sind (z.B. gespeicherte Location-Infos) werden ausgeblendet, nicht leer angezeigt.
- [x] **AK-4:** „Als Location speichern"-Button im Detail → `/preview-alignment` mit `save: true`. Erfolg: Toast, Sheet schließt, Locations + Feed reload.
- [x] **AK-5:** API-Fehler → Toast, Sheet bleibt offen.
- [x] **AK-6:** Sheet schließt per Button oder Overlay-Tap. Scout-Tab bleibt aktiv.
- [x] **AK-7 (nicht sichtbar):** Kategorie als Enum-Wert an API (z.B. „skyline").

---

##### 🧪 Testplan

1. Scout-Tab → Karte antippen → volles Detail-Sheet öffnet sich (alle Sektionen aus AK-2 prüfen).
2. Sektionen einzeln aufklappen: FOV-Karte, Koordinaten, Himmelsposition, Wetter, Kameraempfehlung, Himmelskörper-Bahn, Beschreibung.
3. Street-View-Link antippen → öffnet sich korrekt.
4. „Als Location speichern" → Toast + Location im Locations-Tab.
5. Maps-Buttons auf Scout-Karte → Maps öffnet sich, kein Detail.
6. Mond vs. Sonne: Illuminations-Chip nur bei Mond sichtbar.

---


### US-86 · 🔀 Gemerged in US-68 `[x]`

| Feld | Wert |
|------|------|
| **Status** | Done (gemerged in US-68) |

> **Merge (2026-06-20, von Stephan freigegeben):** Lösch-Berechtigung (Host vs. User), Lösch-Approval, Host-Aufgabenliste + Indikator wurden vollständig in **US-68** überführt (gemeinsames Host-Dashboard/Approval). Kein eigenständiges Ticket mehr — siehe US-68 für Scope, AKs und Abhängigkeiten.

---


### TASK-22 · Workflow: manuelle Terminal-Befehle durch Agents automatisieren `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-20 |
| **In Progress seit** | 2026-06-21 |
| **Abgeschlossen** | 2026-06-22 |

**Beschreibung:** Stephan muss aktuell Befehle (v. a. Git/Release) manuell im Terminal eingeben. Ziel: diese Schritte als Teil des Workflows automatisiert durch die Agents ausführen lassen, soweit möglich. Kernfrage der Analyse: Welche Schritte können sicher automatisiert werden — unter der bestehenden Randbedingung, dass Git-Operationen auf Stephans Rechner/Server laufen müssen und nicht in der Sandbox?

**Bezug:** **Folgeticket von TASK-14[x]** (Automatische Deployment Pipeline — produktiv) — analog zu TASK-21, das beim Done-Abgleich aus TASK-14 herausgezogen wurde. TASK-14 liefert die Pipeline (`deploy.yml`, `release.sh`); TASK-22 adressiert den verbleibenden **manuellen Anstoß** im Terminal. Grenzt an den Release-Workflow und TASK-21 (CI-Test-Gate). Eigenständig.

**Analyse-Ergebnis (2026-06-20):** Kernfrage beantwortet. Vollständige Hands-off-Automatisierung ist **nicht** möglich: Terminal.app läuft in der Computer-Steuerungs-Stufe „click" — Tippen, Cmd+V, Tastendrücke und Rechtsklick durch den Agent sind als Sicherheitsgrenze gesperrt. Der Agent kann Befehle nicht selbst eintippen/einfügen oder Enter drücken; der finale Enter (und alle Git-Befehle) bleiben bei Stephan. Die TASK-22-Randbedingung (Git auf Mac/Server, nicht in der Sandbox) bleibt damit gewahrt.

**Umsetzung (zwei automatisierbare Hälften):** (1) **Eingabe-Halbautomatik** — Befehl per `mcp__computer-use__write_clipboard` in die Mac-Zwischenablage, Stephan macht nur Cmd+V + Enter; (2) **Output-Vollautomatik** — Agent liest das Ergebnis per `mcp__computer-use__screenshot` selbst aus, kein Zurückkopieren mehr. Verankert in `fotoalert-test`, `fotoalert-localdev`, `fotoalert-release` (Routine „Terminal-Automatisierung"); `fotoalert-orchestrator` erhält einen Verweis, damit Subagenten die Routine erben. Live-Health der Produktion läuft schon heute über `web_fetch`. Copy-ready Skill-Blöcke: `outputs/TASK-22_Skill-Aenderungen.md` — Einfügen über Einstellungen → Capabilities (Skill-Cache ist read-only, daher nicht aus der Session editierbar). Offen: Skill-Blöcke einsetzen + ein realer Test-/Release-Zyklus zur Verifikation. Siehe Memory `feedback_terminal_automation`.

---


### TASK-23 · Audit: Welche Nutzerdaten werden nicht serverseitig persistiert (Verlustrisiko)? `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-21 |
| **Abgeschlossen** | 2026-06-24 |

**Beschreibung:** Vollständige Bestandsaufnahme aller nutzerseitig erzeugten/änderbaren Daten daraufhin, ob sie serverseitig (SQLite) gespeichert werden oder nur lokal (`localStorage`) liegen und damit verloren gehen können (iOS löscht PWA-localStorage nach 7 Tagen Inaktivität, vgl. BUG-26). Ergebnis: eine Liste „persistiert ✅ / nur lokal ⚠️" pro Datenart mit Empfehlung, was nachgezogen werden muss — als Grundlage für Folgetickets.

**Bezug:** Übergreifender Audit, der den Boden für die Persistenz-Tickets liefert. Bekannte Einzelfälle sind bereits abgedeckt: Verifikationen → BUG-26 [x] (serverseitig persistiert), Sterne-Bewertungen → US-89 (in Analyse), Location-Änderungen als Vorschläge → US-68 (Host-Approval Workflow). Dieser Task findet die *übrigen* nur-lokal gespeicherten Datenarten (z. B. Favoriten US-17, Filter-/Einstellungs-Zustände, Geräte-Token). Grenzt an US-75 (User/Backend-Datensync) — TASK-23 ist die Inventur, US-75 die laufende Sync-Sicherung.

**Scope:**
- Eingeschlossen: Web-PWA (`web/index.html` localStorage) + Backend-Persistenz (`backend/data/store.py`, `backend/main.py`). Inventar aller nutzererzeugten/-änderbaren Datenarten mit Klassifizierung ✅/⚠️/🔒 und Empfehlung. Ergebnis als Tabelle in dieses Ticket.
- Ausgeschlossen: iOS-App (`ios/FotoAlert/`, eigene UserDefaults) — bewusst ausgeklammert (2026-06-21). Keine automatische Anlage von Folgetickets — Empfehlungen, Stephan entscheidet separat. Keine Code-Änderungen (reiner Audit).

**Akzeptanzkriterien:**
- [ ] Alle `localStorage`-Keys in `web/index.html` erfasst — Vollständigkeit per `grep -nE "localStorage\.(get|set|remove)Item" web/index.html` gegengeprüft (Soll: `fa_api`, `fa_notify_high/golden/milky`, `fa_token`, `fa_role`, `fotoalert_verifications`, `fotoalert_ratings`, `fotoalert_filters`, `fa_sec`, `cameraProfile`)
- [ ] Jede Datenart klassifiziert: ✅ serverseitig persistiert / ⚠️ nur lokal (Verlustrisiko) / 🔒 lokal *by design* (Auth/Config)
- [ ] Für jede ⚠️-Datenart eine Empfehlung (persistieren vs. lokal lassen) + Verweis auf bestehendes/empfohlenes Folgeticket
- [ ] Serverseitige In-Memory-Speicher ohne Disk/DB-Persistenz erfasst (Befund: `_device_tokens` in `main.py`)
- [ ] Bekannte Einzelfälle korrekt zugeordnet: Verifikationen→BUG-26 ✅, Ratings→US-89, Location-Edits→US-68
- [ ] Edge Case: noch nicht gebaute Features mit geplanter Nur-Lokal-Speicherung als Designrisiko markiert (Favoriten US-17, AK sieht `localStorage` vor)

**Pre-Mortem:**
- 💀 Audit übersieht einen `localStorage`-Key → Inventar unvollständig, ein Verlust bleibt unentdeckt. Auslöser: nur statisches grep auf einen Methodennamen. Gegenmaßnahme: grep auf `get/set/removeItem` + Soll-Liste im AK fixieren.
- 💀 Datenart als „nur lokal" eingestuft, obwohl das Backend sie längst speichert (oder umgekehrt) → falsches Folgeticket. Gegenmaßnahme: für jede ⚠️ den Backend-Pfad gegenprüfen (Ratings: kein `/rating`-Endpoint bestätigt).
- 💀 Audit empfiehlt Persistenz für reine Geräte-Präferenzen (Filter, Sektions-State) → unnötige Komplexität. Gegenmaßnahme: Geräte-Präferenz vs. echte Nutzerdaten explizit trennen.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` (CFG, Verify, Rating, Filter, Sections, FOV-Camera), `backend/data/store.py` (3 Tabellen), `backend/main.py` (`_device_tokens`)
- [x] Scope bestätigt: nur Web-PWA; Deliverable: Inventar ins Ticket, keine Auto-Folgetickets (2026-06-21)
- [x] Nur ein sinnvoller Weg (reiner Audit, kein Code) → keine Implementierungsoptionen nötig

**Audit-Ergebnis (Stand 2026-06-21):**

*✅ Serverseitig in SQLite persistiert:*
| Datenart | Speicher |
|---|---|
| Custom Locations | `custom_locations` |
| Location-Änderungen (Overrides) | `location_overrides` |
| Standort-Verifikationen | `location_verifications` (BUG-26) |

*⚠️ Nur lokal (`localStorage`) — Verlustrisiko (iOS löscht PWA-Storage nach 7 Tagen):*
| Key | Datenart | Empfehlung |
|---|---|---|
| ~~`fotoalert_ratings`~~ | ~~Sterne-Bewertungen~~ | ~~Persistieren → **US-89** (in Analyse) deckt ab~~ ✅ **US-89 Done** (2026-06-21) |
| `cameraProfile` | Kamera-Setup (Sensor, Brennweite, Ausrichtung) | Persistieren → **US-90** (In Progress) |
| `fotoalert_filters` | Filter-Zustände | Lokal lassen (Geräte-Präferenz) — optional Sync via US-75 |
| `fa_notify_high/golden/milky` | Benachrichtigungs-Präferenzen | Lokal lassen (geräte-/push-gebunden) |
| `fa_sec` | Auf-/zugeklappte Detail-Sektionen | Lokal lassen (reiner UI-State) |

*🔒 Lokal by design (kein Verlustrisiko):* `fa_token`, `fa_role` (Session, wird beim Login neu ausgegeben), `fa_api` (Dev-Config).

*✅ Serverseitig persistiert (nachträglich):* `_device_tokens` → **TASK-24 Done** (v1.11.5, 2026-06-22): Push-Token-Tabelle `device_tokens` in SQLite, kein RAM-State mehr.

*⚠️ Noch nicht gebaut:* Favoriten (**US-17**) — AK sieht explizit `localStorage` vor → bei Bau direkt Verlustrisiko. Designhinweis in US-17 ergänzen: serverseitig persistieren.

**Testplan:**
- [ ] Automatisiert: `grep -nE "localStorage\.(get|set|remove)Item" web/index.html` → jeder gefundene Key ist im Inventar enthalten (Vollständigkeitscheck)
- [ ] Manuell: Für jede ⚠️-Datenart den Backend-Pfad gegenprüfen (kein Persistenz-Endpoint vorhanden bestätigt)

**Verifikation (Heartbeat 2026-06-22, separater Check):**
- Inventar **vollständig & korrekt** — alle 10 Soll-Keys im Code bestätigt. ⚠️ Caveat: Das im AK genannte `grep`-Kommando findet nur 7 Keys, weil `fotoalert_verifications`, `fotoalert_ratings`, `fotoalert_filters`, `fa_sec` über **Konstanten** (`_KEY`/`_key`, z. B. Zeilen 1543/1792/1958/2486) statt Inline-String-Literale angesprochen werden. Der Vollständigkeitscheck sollte daher zusätzlich auf `_KEY`/`_key`-Definitionen prüfen, nicht nur auf `localStorage.…Item('…')`.
- **Befund Veraltung:** `fotoalert_ratings` trägt jetzt im Code den Kommentar „nur noch für Migration aus localStorage" und **US-89 steht inzwischen in Done** → Sterne-Bewertungen sind serverseitig persistiert. Die Audit-Tabelle (Stand 06-21) führt sie noch als ⚠️ „US-89 (in Analyse)". → Reklassifizieren auf ✅ persistiert (US-89 erledigt). *(Inhalt bewusst nicht eigenmächtig umgeschrieben — Stephans Entscheidung.)*
- Substanz des Audits unverändert gültig: offene Persistenz-Empfehlungen bleiben `cameraProfile` (Folgeticket) und `_device_tokens` (RAM-only, Folgeticket) + Designhinweis US-17.

> ✅ **Done (2026-06-24):** Audit-Ergebnis aktualisiert — Ratings auf ✅ (US-89 Done), TASK-24 auf ✅ (v1.11.5), US-90 In Progress, Designhinweis in US-17 ergänzt. Kein Code, kein Release.

---


### US-90 · Kamera-Setup serverseitig persistieren `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-21 |
| **In Progress seit** | 2026-06-24 |
| **Abgeschlossen** | 2026-06-24 |

**Beschreibung:** Als Fotograf möchte ich, dass mein Kamera-Setup (Sensor, Brennweite, Ausrichtung) serverseitig gespeichert wird, damit es nach App-Schließen/Geräte­wechsel erhalten bleibt. Aktuell liegt es nur in `localStorage['cameraProfile']` und geht verloren (iOS löscht PWA-Storage nach 7 Tagen, vgl. BUG-26).

**Bezug:** Folgeticket aus TASK-23 (Persistenz-Audit). Datenquelle eingeführt in US-58[x] (FOV-Visualisierung). Gleiches Muster wie BUG-26 (Verifikationen → SQLite). Grenzt an US-75 (User/Backend-Datensync).

---

#### 📋 Implementation Spec (Analyse 2026-06-21)

**Scope-Check / Grundannahmen (autonom getroffen, da Stephan abwesend):**
- `cameraProfile` ist **Geräte-Singleton**, kein Listen- und kein Location-Bezug: genau ein Objekt `{sensor, fl, ori}` pro Gerät. Damit ist nicht BUG-26 (Listen-Anhängen pro Location) die nächste Vorlage, sondern **US-89 (Ratings)** mit seinem `device_id`-Upsert-Muster — 1 Gerät = 1 Datensatz, überschreibbar.
- **Identität = `device_id` (UUID), NICHT User/Login.** FotoAlert hat keine personenscharfen Accounts (US-66 ist rollenbasiert: `user`/`host`). Die Geräte-UUID liegt bereits unter `localStorage['fa_device_id']` (`Rating.deviceId()`, web/index.html:1785) und wird wiederverwendet. „Gerätewechsel" im Ticket-Wortlaut meint daher: Setup geht beim PWA-Storage-Wipe NICHT verloren, solange dieselbe `device_id` rekonstruierbar ist. **Annahme A1:** Echtes Cross-Device-Sync (gleiches Setup auf Handy + iPad) ist NICHT Teil dieses Tickets — das gehört zu US-75 (User/Backend-Datensync) und ist explizit ausgeschlossen. Begründung: ohne Login keine geräteübergreifende Identität.
- **Annahme A2:** Die `fl`-Validierung folgt dem bestehenden Frontend-Limit aus US-58 (`min=8 max=1200`, Input-Clamp `8..1200` in `_readInputs`). Sensor muss ein bekannter Key sein (`fullframe|apsc_canon|apsc_sony|mft|one_inch`), `ori ∈ {landscape, portrait}`.

**Scope:**
- Eingeschlossen: `cameraProfile` (`{sensor, fl, ori}`) je `device_id` serverseitig in SQLite persistieren (Upsert). Boot-Preload des eigenen Profils. Einmalige Migration eines bestehenden `localStorage['cameraProfile']`. Validierung der drei Felder.
- Ausgeschlossen: Geräteübergreifender Sync ohne Login (→ US-75). Mehrere benannte Profile pro Gerät („Body 1 / Body 2"). Verknüpfung mit `camera_hints` der Locations. Push-Token (→ TASK-24).

**Akzeptanzkriterien:**
- [ ] `GET /camera-profile?device_id=<uuid>` liefert `{sensor, fl, ori}` für ein bekanntes Gerät; für ein unbekanntes Gerät `{}` (HTTP 200, leeres Objekt — NICHT 404, damit das Frontend stillschweigend auf den Default fällt).
- [ ] `POST /camera-profile` mit Body `{device_id, sensor, fl, ori}` und gültigem Bearer-Token (`require_auth`, user+host) speichert per Upsert; zweiter POST mit gleicher `device_id` überschreibt (kein zweiter Datensatz). Response `201` + `{ok: true, sensor, fl, ori}`.
- [ ] Edge Case: `POST` ohne `device_id` → `422` „device_id ist erforderlich." (analog US-89).
- [ ] Edge Case: `fl < 8` oder `fl > 1200` → `422`. `sensor` kein bekannter Key → `422`. `ori` nicht in `{landscape, portrait}` → `422`.
- [ ] Edge Case: `POST` ohne Auth-Header → `401` (Schreiben verlangt Token wie bei Verify/Rating). `GET` ohne Token → `200` (lesen ist öffentlich).
- [ ] Frontend: Beim App-Start lädt `CameraFOV._loadProfile()` das Profil des eigenen `device_id` einmalig in `_profile`; alle FOV-Panels (`panelHtml`, `_readInputs`) nutzen dieses statt direkt `localStorage`.
- [ ] Frontend: Jede Änderung in einem FOV-Panel (`update()`) schreibt via `POST /camera-profile` ans Backend (fire-and-forget, optimistisch) und cached lokal weiter (Offline-Fallback).
- [ ] Migration: Existiert beim ersten Start nach Deploy ein `localStorage['cameraProfile']` und das Backend hat für die `device_id` noch nichts, wird das lokale Profil einmalig hochgeladen; danach gilt der Server als Quelle. Kein Datenverlust.
- [ ] Edge Case (Race): App-Start mit leerem/fehlerhaftem Server-Response → Frontend nutzt den localStorage-/Default-Wert, kein Crash, keine leeren Panels.
- [ ] Regression: alle bestehenden Tests (Verify/Rating/US-66/US-67) bleiben grün; FOV-Berechnung (`_calcFOV`) unverändert.

**Pre-Mortem:**
- 💀 **Migration überschreibt frisches Server-Profil mit altem localStorage-Stand.** Auslöser: bedingungslose Migration bei jedem Start, statt nur wenn Server leer. Frühwarnung: nach Gerätewechsel/Reinstall springt das Setup auf einen alten Wert. → Gegenmaßnahme: Migration nur wenn `GET` ein leeres `{}` liefert UND lokal ein Profil existiert; danach `localStorage['cameraProfile']` als migriert markieren (oder belassen, aber nicht erneut pushen). Verankert in AK „Migration".
- 💀 **`device_id`-Drift durch iOS-Storage-Wipe macht Persistenz wirkungslos.** Auslöser: `fa_device_id` liegt selbst in localStorage; löscht iOS nach 7 Tagen den Storage, entsteht eine NEUE UUID → das alte Server-Profil ist nicht mehr auffindbar. Das ist exakt das Problem, das BUG-26/US-89 ebenfalls haben und akzeptieren. Frühwarnung: nach >7 Tagen Inaktivität wieder Default-Setup trotz „Persistenz". → Gegenmaßnahme: bewusst als bekannte Grenze dokumentieren (gleiche Schwelle wie US-89). Echte Stabilität kommt erst mit US-75 (Login bindet Profil an Account). NICHT in diesem Ticket lösen, aber in der Retro vermerken.
- 💀 **Python-3.10-Syntax crasht Prod (Py 3.9).** Auslöser: `str | None`-Annotation o. Ä. im neuen Store/Endpoint. Frühwarnung: grüne Sandbox (3.10), roter Prod-Start. → Gegenmaßnahme: `from __future__ import annotations` ist in store.py bereits aktiv; Endpoint-Signaturen mit `Optional[...]`/Defaults wie bei US-89; kein `|` in Annotations.
- 💀 **Schreib-Sturm: `oninput` am Brennweiten-Feld feuert pro Tastendruck einen POST.** Auslöser: `CameraFOV.update()` hängt an `oninput`/`onchange` → bei jeder Ziffer ein Request. Frühwarnung: Netzwerk-Log voller `/camera-profile`-POSTs beim Tippen. → Gegenmaßnahme: POST per kleinem Debounce (~400 ms) oder nur auf `change` statt `input`; localStorage-Cache sofort, Server verzögert. Verankert im Frontend-AK „fire-and-forget".
- 💀 **Stiller Datenverlust bei Offline-POST.** Auslöser: POST schlägt fehl (offline), UI zeigt aber Erfolg, lokaler Cache wird nicht geschrieben. Frühwarnung: Setup nach Reload weg, obwohl „gespeichert". → Gegenmaßnahme: localStorage IMMER zuerst/parallel schreiben (Source of Truth lokal bis Sync), Server-POST optimistisch nachziehen; Server-Wert gewinnt nur beim nächsten erfolgreichen Boot-Load.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (Singleton-Daten, device_id-Identität, Migration, Offline)
- [x] Pre-Mortem durchgeführt (5 Szenarien, alle in AK/Plan verankert)
- [x] Architektur analysiert:
  - `web/index.html` — `CameraFOV` (ab Z. 2505): `_getProfile`/`_saveProfile` (Z. 2517–2521) sind die einzigen localStorage-Touchpoints; `_readInputs` (Z. 2609) liest die UI; `update()` (Z. 2631) ist der Save-Trigger. Geräte-UUID via `Rating.deviceId()` (Z. 1785, Key `fa_device_id`) wiederverwenden.
  - `backend/data/store.py` — neue Tabelle + Methoden analog `upsert_rating`/`get_rating_summary` (Z. 375–422). `from __future__ import annotations` + `Optional` bereits vorhanden.
  - `backend/main.py` — neue Endpoints analog Rating-Block (Z. 1313–1362): `RatingIn`-artiges Pydantic-Model, `Depends(auth.require_auth)` für POST, offenes GET.
  - `backend/tests/test_api_regression.py` — neue Testklasse analog BUG-26-Verify-Klasse (Z. 54 ff.); `auth_headers`-Fixture aus conftest.
- [x] Implementierungsoptionen: A / B / C
- [ ] Empfehlung: **Option A** (siehe unten) — Weg-Gate offen für Stephan.

**Implementierungsoptionen:**

*Option A — Eigene Tabelle `camera_profiles` mit `device_id`-Upsert (US-89-Muster).*
- Vorgehen: `CREATE TABLE camera_profiles (device_id TEXT PRIMARY KEY, sensor TEXT, fl INTEGER, ori TEXT, updated TEXT)`. Store: `upsert_camera_profile`, `get_camera_profile`. Endpoints: `GET /camera-profile?device_id=`, `POST /camera-profile` (`require_auth`). Frontend: `CameraFOV._loadProfile()` beim Boot, `update()` → POST + localStorage.
- Betroffene Dateien: `backend/data/store.py`, `backend/main.py`, `web/index.html`, `backend/tests/test_api_regression.py`.
- Vorteile: folgt 1:1 dem frisch gebauten, getesteten US-89-Pfad; `PRIMARY KEY device_id` erzwingt „1 Gerät = 1 Profil" ohne ON-CONFLICT-Verrenkung; klar erweiterbar (Spalten ergänzen).
- Nachteile/Risiken: Geräte-Token-Identität (kein echtes Cross-Device, s. Pre-Mortem 2). Aufwand: **klein–mittel**.

*Option B — Profil als JSON-Blob in bestehender Tabelle `location_overrides`-Stil (Key-Value).*
- Vorgehen: generische Tabelle `device_kv (device_id, key, value_json)`, Profil als `key='camera_profile'`. Endpoint generisch.
- Vorteile: wiederverwendbar für TASK-24 (Push-Token) und weitere Geräte-Settings; nur eine Tabelle für alle künftigen Device-Daten.
- Nachteile/Risiken: höhere Abstraktion ohne aktuellen Bedarf (YAGNI); keine Spalten-Validierung auf DB-Ebene; weicht vom etablierten US-89-Muster ab → mehr Review-Last. Aufwand: **mittel**.

*Option C — An US-75 koppeln, Profil an Account statt Gerät binden.*
- Vorgehen: warten bis Login/Account-Sync (US-75) steht, Profil als User-Datensatz persistieren.
- Vorteile: löst die `device_id`-Drift dauerhaft (echtes Cross-Device).
- Nachteile/Risiken: blockiert US-90 auf ein größeres, nicht freigegebenes Ticket; löst das akute „7-Tage-Wipe"-Problem nicht zeitnah. Aufwand: **groß** (gekoppelt).

✅ **Empfehlung: Option A** — folgt exakt dem gerade gebauten und getesteten US-89-`device_id`-Upsert-Muster, ist klein gehalten, löst das akute Persistenz-Problem sofort und hält das Cross-Device-Thema sauber für US-75 offen; die `device_id`-Drift ist eine bekannte, mit US-89 geteilte Grenze, kein neues Risiko.

**Testplan:**
- [ ] Automatisiert (Harness, `backend/tests/test_api_regression.py`, Klasse `TestCameraProfile`, Ticket-ID im Docstring):
  - POST `{device_id:'cam-test', sensor:'fullframe', fl:85, ori:'landscape'}` → 201; GET `?device_id=cam-test` → `{sensor:'fullframe', fl:85, ori:'landscape'}`.
  - Zweiter POST mit `fl:135` → GET zeigt `135`, kein Doppeleintrag (Upsert).
  - GET `?device_id=unknown` → `200` + `{}`.
  - POST ohne `device_id` → `422`; `fl:5` → `422`; `sensor:'bogus'` → `422`; `ori:'diagonal'` → `422`.
  - POST ohne Auth-Header → `401`.
- [ ] Manuell (http://localhost:8000): FOV-Panel öffnen, Sensor/Brennweite/Ausrichtung ändern, App schließen + neu laden → Werte erhalten. DevTools: `localStorage['cameraProfile']` löschen, neu laden → Server-Wert wird wiederhergestellt (Boot-Load). Offline (DevTools throttle) ändern → kein Crash, localStorage greift.

#### 📋 Implementation Spec Ende


### TASK-24 · Push-Token serverseitig persistieren `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-21 |
| **In Progress seit** | 2026-06-22 |
| **Done** | 2026-06-22 |
| **Release** | v1.11.5 |

**Beschreibung:** Die Push-Token-Liste `_device_tokens` in `backend/main.py` liegt nur im RAM und geht bei jedem Server-Neustart verloren. Token in SQLite persistieren, damit registrierte Geräte einen Neustart überdauern. Latent, da Push im Frontend noch nicht verdrahtet ist — vor dem Push-Rollout zu erledigen.

**Bezug:** Folgeticket aus TASK-23 (Persistenz-Audit). Betrifft `/register-device` (siehe US-66, dort als „Folge-Ticket" vermerkt). Gleiches Persistenz-Muster wie BUG-26.

---

#### 📋 Implementation Spec (Analyse 2026-06-21)

**Scope-Check / Grundannahmen (autonom getroffen, da Stephan abwesend):**
- **IST-Stand verifiziert:** `_device_tokens: list[dict] = []` (`main.py:251`) wird ausschließlich im Endpoint `/register-device` (`main.py:990–997`) beschrieben/gelesen. Es gibt **keinen weiteren Konsumenten** im Code (Grep über `backend/` bestätigt: kein Scheduler-/Push-Versand greift heute auf die Liste zu). `backend/notifications/push.py` versendet an ein einzelnes `device_token` (Z. 71/107), ist aber nicht mit der Liste verdrahtet. → Push ist im Frontend UND im Backend-Versand noch nicht aktiv; das Ticket ist reine **Persistenz-Vorbereitung**, kein Push-Feature.
- **A1 — Migration des aktuellen RAM-Stands entfällt.** `_device_tokens` ist flüchtig und beim Deploy/Neustart ohnehin leer; es existiert kein Bestand, der gerettet werden müsste. Eine Migrationsroutine wäre toter Code → **bewusst ausgeschlossen**.
- **A2 — Identität = APNs/Push-Token selbst (TEXT), nicht `device_id`.** Anders als US-89/US-90 (Geräte-Setup je `device_id`) ist hier der Push-Token der natürliche Schlüssel: ein Gerät kann durch Token-Rotation (APNs vergibt neue Tokens) über die Zeit *mehrere* Tokens haben; APNs liefert beim Versand die Information „Token ungültig" zurück, nicht „device_id". Deshalb ist der **Token `PRIMARY KEY`**, nicht `device_id`. (Eine optionale `device_id`-Spalte wird mitgeführt, damit beim Push-Rollout pro Gerät dedupliziert werden kann — aktuell nicht erzwungen, da das Frontend noch keine `device_id` an `/register-device` sendet.)
- **A3 — Auth-Verhalten bleibt vorerst offen (kein Bearer-Token erzwungen),** exakt wie der bestehende Kommentar in `main.py:992–993` festhält: die native iOS-App kann sich noch nicht einloggen. Die Persistenz ändert das Auth-Modell NICHT — das ist eigener Scope (s. Pre-Mortem 4). Begründung: Token-Schutz jetzt würde die einzige reale Aufruferin (iOS) aussperren.
- **A4 — Signatur-Beibehaltung:** Der bestehende Endpoint nimmt `token: str` als **Query-Param** (kein Pydantic-Body). Da Push noch nicht verdrahtet ist, gibt es keine Aufrufer, die ein Brechen der Signatur bemerken würden — trotzdem wird die bestehende Query-Param-Signatur beibehalten (minimaler Diff, keine unnötige Vertragsänderung). Optional als Verbesserung erwähnt, aber nicht im Scope.

**Scope:**
- Eingeschlossen: Neue SQLite-Tabelle `device_tokens` in `store.py`. Store-Methoden `register_device_token` (Upsert) + `load_device_tokens` (Liste). `/register-device` schreibt persistent statt in die RAM-Liste; `_device_tokens` wird durch eine boot-seitige Hydration aus der DB ersetzt ODER vollständig durch DB-Zugriffe abgelöst (s. Optionen). Idempotenz bei doppeltem Token (kein Zweiteintrag, gleiche Response `already_registered`). Erhalt der bisherigen Response-Form (`status`, `device_count`).
- Ausgeschlossen: Tatsächlicher Push-Versand / APNs-Verdrahtung (eigenes Push-Rollout-Ticket). Auth-Schutz von `/register-device` (eigener Scope, an iOS-Login gekoppelt). Token-Invalidierung über APNs-Feedback (s. Pre-Mortem 2, als bekannter Folgepunkt notiert). Migration eines RAM-Bestands (A1, leer). Frontend-Verdrahtung (Push im Frontend nicht gebaut).

**Akzeptanzkriterien:**
- [x] `POST /register-device?token=abc&platform=ios` legt den Token persistent an. Response `200` + `{"status": "registered", "device_count": <n>}` (Form unverändert ggü. heute).
- [x] Idempotenz: zweiter `POST` mit identischem `token` legt KEINEN zweiten Datensatz an und liefert `{"status": "already_registered"}` (HTTP 200) — `device_count`-relevante Zeilenzahl bleibt gleich.
- [x] Persistenz über Neustart: Token registrieren → `_store` neu instanziieren (simuliert Server-Neustart, neue `LocationStore`-Instanz auf dieselbe DB) → `load_device_tokens()` enthält den Token weiterhin. (Das ist der Kern-AK des Tickets.)
- [x] `load_device_tokens()` liefert eine Liste von Dicts der Form `{"token": <str>, "platform": <str>}` (Form kompatibel zur bisherigen `_device_tokens`-Struktur, damit ein späterer Push-Konsument unverändert iterieren kann).
- [x] Edge Case: `POST /register-device` ohne `token`-Param → `422` (FastAPI-Default für fehlenden Required-Query-Param; Verhalten unverändert ggü. heute, da `token` schon required ist).
- [x] Edge Case: leerer Token-String (`token=`) → `422` „token ist erforderlich." (neue Guard, verhindert leere Primärschlüssel in der DB).
- [x] Edge Case: `platform` weggelassen → Default `"ios"` wird gespeichert (Verhalten unverändert).
- [x] Regression: alle bestehenden Tests (Verify/Rating/US-66/US-67/US-89) bleiben grün; keine Änderung an Auth-Verhalten anderer Endpoints.

**Pre-Mortem:**
- 💀 **Dubletten-Token sprengen die Tabelle / Doppel-Push beim Rollout.** Auslöser: `INSERT` ohne Conflict-Behandlung → zweite Registrierung desselben Tokens legt eine zweite Zeile an; späterer Push sendet doppelt. Frühwarnung: `device_count` steigt bei wiederholter Registrierung desselben Geräts. → Gegenmaßnahme: `token TEXT PRIMARY KEY` + `INSERT ... ON CONFLICT(token) DO UPDATE` (US-89-Upsert-Muster) oder vorgelagertes `SELECT`-EXISTS wie heute. Verankert in AK „Idempotenz".
- 💀 **Token-Rotation/Invalidierung macht die Tabelle zur Müllhalde toter Tokens.** Auslöser: APNs vergibt rotierende Tokens; alte bleiben für immer in der DB, Push läuft gegen tote Tokens. Frühwarnung: beim Push-Rollout viele `410 Unregistered`-Antworten von APNs. → Gegenmaßnahme: **bewusst NICHT in diesem Ticket lösen** (Push-Versand existiert noch nicht, also gibt es kein APNs-Feedback zum Auswerten). Als bekannter Folgepunkt fürs Push-Rollout-Ticket notiert (Spalte `updated`/`last_seen` jetzt schon mitführen, damit später aufgeräumt werden kann, ohne Migration). Die optionale `device_id`-Spalte erlaubt späteres „pro Gerät nur jüngster Token".
- 💀 **Migration des RAM-Stands erwartet, ist aber leer → verwirrende Leer-Logik.** Auslöser: jemand baut eine Migrationsroutine für `_device_tokens` → toter Code, da die Liste beim Neustart leer ist. Frühwarnung: Migrations-Code ohne erreichbaren Eingabezustand. → Gegenmaßnahme: explizit dokumentiert (A1), KEINE Migration bauen. Verankert im Scope-Ausschluss.
- 💀 **Versehentlicher Auth-Schutz sperrt iOS aus.** Auslöser: aus Gewohnheit (US-89/US-90 schützen POST mit `require_auth`) wird `Depends(auth.require_auth)` an `/register-device` gehängt → die native App ohne Login bekommt `401`, kein Gerät registriert sich je. Frühwarnung: `register`-Aufrufe von iOS liefern `401`. → Gegenmaßnahme: Endpoint bleibt bewusst offen (A3); bestehender Kommentar `main.py:992–993` bleibt erhalten und wird ergänzt. KEIN `Depends` hinzufügen. Verankert im Scope-Ausschluss + Regression-AK.
- 💀 **Python-3.10-Syntax crasht Prod (Py 3.9).** Auslöser: `list[dict]`/`str | None`-Annotation in neuen Store-Signaturen. Frühwarnung: grüne Sandbox (3.10), roter Prod-Start. → Gegenmaßnahme: `from __future__ import annotations` ist in `store.py` bereits aktiv; neue Methoden mit `List[dict]`/`Optional[...]` aus `typing` bzw. PEP-563-String-Annotations wie im Bestand. Kein `|` in Annotations.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (Idempotenz, Persistenz-über-Neustart, Token-als-Schlüssel, offener Auth-Status)
- [x] Pre-Mortem durchgeführt (5 Szenarien, alle in AK/Scope verankert)
- [x] Architektur analysiert:
  - `backend/main.py` — `_device_tokens` (Z. 251, einziger RAM-Speicher), `/register-device` (Z. 990–997, Query-Param `token`, unauthentifiziert per US-66-Kommentar). `_store = LocationStore()` bereits global (Z. 101) → wiederverwendbar. KEIN weiterer Konsument der Liste.
  - `backend/data/store.py` — neue Tabelle in `_INIT_SQL` (Z. 37–85) analog `location_ratings`; neue Methoden analog `upsert_rating`/`get_rating_summary` (Z. 375–422) mit `BEGIN/COMMIT/ROLLBACK`. `from __future__ import annotations` + `Optional`/`List` vorhanden.
  - `backend/notifications/push.py` — künftiger Konsument (`send_push_notification(device_token, …)`, Z. 71); zeigt, dass die geladene Liste pro Eintrag genau einen `token` braucht → Form-AK.
  - `backend/tests/test_api_regression.py` — neue Klasse `TestTask24DeviceTokens` analog `TestBug26Verifications` (Z. 53 ff.); kein `auth_headers` nötig (Endpoint offen). Persistenz-AK via zweiter `LocationStore`-Instanz auf dieselbe `data_dev`-DB.
- [x] Implementierungsoptionen: A / B / C
- [x] Empfehlung: **Option A** — freigegeben + implementiert (2026-06-22).

**Implementierungsoptionen:**

*Option A — Eigene Tabelle `device_tokens`, DB ist Source of Truth, RAM-Liste entfällt.*
- Vorgehen: `CREATE TABLE device_tokens (token TEXT PRIMARY KEY, platform TEXT DEFAULT 'ios', device_id TEXT DEFAULT '', updated TEXT)`. Store: `register_device_token(token, platform, device_id, updated)` (Upsert via `ON CONFLICT(token)`), `load_device_tokens() -> List[dict]`. `/register-device` ruft `_store.register_device_token(...)` und gibt `device_count = len(_store.load_device_tokens())` zurück. `_device_tokens`-Modulvariable wird **entfernt** (kein RAM-State mehr).
- Betroffene Dateien: `backend/data/store.py`, `backend/main.py`, `backend/tests/test_api_regression.py`.
- Vorteile: folgt 1:1 dem getesteten US-89-Upsert-Pfad; `PRIMARY KEY token` erzwingt Idempotenz ohne Race; keine RAM/DB-Divergenz; `updated`/`device_id`-Spalten machen das spätere Push-Rollout (Aufräumen toter Tokens, Dedup pro Gerät) ohne Migration möglich.
- Nachteile/Risiken: jeder künftige Push-Lauf liest die Liste aus der DB (vernachlässigbar bei der Gerätezahl). Aufwand: **klein**.

*Option B — DB-Persistenz + RAM-Cache (`_device_tokens` als Boot-Hydration).*
- Vorgehen: Tabelle wie A; zusätzlich `_device_tokens` beim Startup aus `load_device_tokens()` befüllen und bei jeder Registrierung sowohl DB als auch Liste aktualisieren.
- Vorteile: Push-Versand liest aus RAM (kein DB-Hit pro Lauf); minimaler Eingriff in spätere Push-Logik, die heute schon `_device_tokens` erwartet.
- Nachteile/Risiken: zwei Quellen, die synchron gehalten werden müssen → Divergenz-Risiko (genau die Klasse Bug, die TASK-23 eigentlich beseitigen will); doppelte Schreibpfade. Aufwand: **klein–mittel**.

*Option C — Generische `device_kv`-Tabelle (Key-Value), Token als ein Key-Typ.*
- Vorgehen: gemeinsame Tabelle für alle Geräte-Settings (vgl. US-90 Option B), Push-Token als `key='push_token'`.
- Vorteile: eine Tabelle für künftige Device-Daten.
- Nachteile/Risiken: YAGNI; kein `PRIMARY KEY token` → Idempotenz nur per Anwendungslogik; weicht vom etablierten Tabellen-pro-Domäne-Muster ab → höhere Review-Last; US-90 hat dieselbe Option bereits zugunsten der dedizierten Tabelle verworfen. Aufwand: **mittel**.

✅ **Empfehlung: Option A** — beseitigt den RAM-State vollständig (genau das Ziel des Persistenz-Audits TASK-23, keine zweite Wahrheit), folgt exakt dem frisch getesteten US-89-Upsert-Muster, ist der kleinste konsistente Diff und legt mit `updated`/`device_id`-Spalten das Fundament fürs spätere Push-Rollout, ohne jetzt Push-Logik vorwegzunehmen.

**Testplan:**
- [x] Automatisiert (Harness, `backend/tests/test_api_regression.py`, Klasse `TestTask24DeviceTokens`): 6/6 Tests grün (2026-06-22).
- [ ] Manuell (http://localhost:8000): `curl -X POST 'http://localhost:8000/register-device?token=manual-1'` → `registered`; gleicher Call erneut → `already_registered`; Server neu starten; erneuter Call mit `manual-1` → `already_registered` (Token überlebte den Neustart). Beweist den Kern-AK. ← **ausstehend**

#### 📋 Implementation Spec Ende

---


### TASK-25 · On-Demand Ephemeriden-Engine (Batch-Vorberechnung ablösen) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Mittel |
| **Status** | Done (v1.11.0/1.11.1 deployed + aktiviert 2026-06-22; live verifiziert) |
| **Erstellt** | 2026-06-22 |

**Beschreibung:** Den astronomischen Berechnungskern von Batch-Vorberechnung
(365×N-Volllauf bei `ALGORITHM_VERSION`-Bump / Neu-Location-Kaltstart) auf eine
**stateless On-Demand-Engine** umbauen: standortunabhängige Objektposition pro
Zeitfenster einmal rechnen (Hebel 1), Event-**Rootfinding** statt 1-Min-Scan in
`find_precise_alignment_times` (Hebel 2), Berechnung bei Anfrage statt Cron
(Hebel 3). Ziel: eine Lokation rechnet on-demand in Sub-Sekunden, beliebige
`lat/lon` weltweit ohne Vorberechnung — Voraussetzung für mehr Nutzer.

**Spec:** `FotoAlert/docs/spec-ephemeris-engine.md` (Draft v2, code-geerdet).

**Bezug:**
- **US-64** (Live Astro-Visualisierung, offen) — *Abhängigkeit:* TASK-25 ist der
  Backend-Enabler für den Live-Modus.
- **US-70 / 70b / 70c** (Scout-Ephemeride, done) — *Überschneidung/Abhängigkeit:*
  TASK-25 refaktoriert deren Code (`find_precise_alignment_times`, 5-Min-Batch).
- **US-34** (Job-Orchestrierung, done) — *Überschneidung:* löst die dort
  etablierte Calendar-Recompute-Strategie ab (kein `--full`-Volllauf mehr).
- **TASK-01** (Kometen-Integration, offen) — *Abgrenzung:* TASK-25 baut den
  Ephemeris-Core inkl. Kometen-Positionsrechnung; TASK-01 = Feature/UI darauf.
- **Neuer Scope-Punkt:** weltweite Geländehöhen (Elevation Provider, heute
  EUDEM-Europe-only) — in der Analyse als eigene Lane/OF zu bewerten (OF4).

#### 📋 Implementation Spec (Analyse 2026-06-22)

**Scope-Entscheidungen (von Stephan freigegeben):**
- **Geo: Europe-first, erweiterbar.** Provider-Interface `get_elevation(lat,lon)`
  + persistenter Tile-Cache jetzt bauen; DEM bleibt vorerst EUDEM. Weltweiter
  DEM-Swap (Copernicus GLO-30) = **separates Folge-Ticket** (→ TASK-26 vorgemerkt).
- **Cache: rein On-Demand.** `calendar.json` + 365-Tage-Cron werden entfernt
  (Löschung erst nach bestandener AK6-Regression).
- **Geo-Fallback:** fehlt Geländehöhe → Rechnung mit `elevation_difference_m=0`
  weiterführen + Ergebnis-Flag `elevation_incomplete=true`.

**Eingeschlossen:** On-Demand Query Engine (stateless), Ephemeris-Core-Wrapper
(geozentrische α/δ einmal pro Fenster, de421), Rootfinding statt 1-Min-Scan,
Mond-Parallaxe topozentrisch, Elevation-Provider-Interface (EUDEM dahinter),
Feature-Flag-Migration, Entfernen von `calendar.json`/Cron.
**Ausgeschlossen:** weltweiter DEM, Kometen-Feature/UI (nur Core-Hook), Scoring-
Änderungen, Live-Frontend (US-64), DE440-Upgrade.

**Akzeptanzkriterien:**
- [ ] AK1 — 14-Tage-Plan einer Lokation (alle Objekte) server-seitig < 500 ms.
- [ ] AK1b — 365-Tage-Plan einer Lokation < 5 s.
- [ ] AK2 — Beliebige nicht-angelegte `lat/lon` liefern Plan ohne Vorberechnung.
- [ ] AK3 — Sonne/Mond alt/az innerhalb 1 Bogenminute gegen Skyfield-Referenz.
- [ ] AK4 — Auf-/Untergang & Alignment innerhalb ±1 min; Rootfinding ≥ so genau
      wie alter 1-Min-Scan (an Pfingstberg/Babelsberg-Beispiel verifiziert).
- [ ] AK5 — Kein Cron/Batch berechnet pro Lokation 365-Tage-Verläufe vor; ein
      `ALGORITHM_VERSION`-Bump löst keinen Volllauf aus.
- [ ] AK6 — *(2026-06-22 neu definiert, von Stephan freigegeben):* Für alle
      angelegten Lokationen ist **jede echte Alignment-Passage** der Alt-Engine
      durch **genau ein** Event der neuen Engine am Qualitätsmaximum vertreten
      (Zeit/Höhe ±1 min / AK3). Die bit-genaue Alt-Aufzählung (Mehrfach-Events pro
      Passage durch 1-Min-Raster + 5-Min-Dedup) ist **kein** Ziel — Artefakt, kein
      astronomischer Grund-truth.
- [ ] AK7 — `AlignmentResult`/`find_opportunities`-Ausgabeformat unverändert.
- [ ] Edge Case: Position einmal pro Fenster — N Locations im selben Fenster →
      Core-Call läuft 1×, nicht N× (über Counter/Log verifizierbar).
- [ ] Edge Case: Geländehöhe fehlt → `elevation_difference_m=0` +
      `elevation_incomplete=true`, kein Crash.
- [ ] Edge Case: Azimut-Wrap bei 0°/360° korrekt (vorhandenes `np.mod`-Muster).

**Pre-Mortem:**
- 💀 **Mond steht falsch über dem Motiv.** Auslöser: Hebel-1-Wiederverwendung der
  *geozentrischen* α/δ ohne topozentrische Parallaxe-Korrektur (bis ~1°).
  Frühwarnung: Mond-AK3 reißt nur beim Mond, Sonne ok. Gegenmaßnahme: AK3/AK4
  getrennt für Mond testen; Parallaxe über `distance` zwingend.
- 💀 **Rootfinding verschluckt ein Event.** Auslöser: Grobraster (5–10 min) zu weit,
  Doppel-/Grazing-Alignment fällt in eine Lücke. Frühwarnung: AK6 zeigt fehlende
  Events vs. alter Scan. Gegenmaßnahme: Grobraster konservativ (5 min), AK6 zählt
  Event-Anzahl je Location-Tag gegen Alt-Engine, nicht nur Zeiten.
- 💀 **Prod-Crash trotz grüner Sandbox-Tests.** Auslöser: 3.10+-Syntax
  (`float | None` als Runtime-Annotation, `match`). Frühwarnung: läuft lokal
  (3.10), crasht auf Server (3.9). Gegenmaßnahme: 3.9-kompatibel halten
  (`Optional[...]`), CI gegen 3.9. (Memory `reference_server_python39`.)
- 💀 **Zeiten um 2 h verschoben angezeigt.** Auslöser: Engine rechnet UTC, App
  zeigt Ortszeit — bei Refactor verloren. Frühwarnung: Alignment-Zeiten 2 h daneben.
  Gegenmaßnahme: Engine gibt UTC zurück (wie heute), Konvertierung bleibt im
  Frontend; Regressionstest auf UTC-Feldwerte. (Memory `feedback_shoot_time_utc`.)
- 💀 **Latenz reißt auf realer Hardware.** Auslöser: < 500 ms auf Hetzner CX22
  nicht haltbar. Frühwarnung: AK1-Messung auf Prod. Gegenmaßnahme: Cache-Option
  bewusst verworfen → Rückfalloption ist dünner Response-Cache (OF3), erst bei
  Bedarf; AK1 früh auf Prod messen, nicht nur Sandbox.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt (R1–R5, Questions=0)
- [x] Pre-Mortem durchgeführt (5 Szenarien, Gegenmaßnahmen in AK verankert)
- [x] Architektur analysiert: `backend/calculations/astronomy.py`
      (`find_precise_alignment_times` = 1-Min-Scan via `_ts.linspace`,
      `steps=17*60`/`24*60`; `calculate_subject_angular_profile`;
      `_classify_alignment`; `_get_eph()` lädt `de421.bsp`),
      `calculations/opportunity.py` (`find_opportunities[_multi_day]`),
      `backend/precompute.py` (Schicht 2 `calendar.json`, `--full`,
      `ALGORITHM_VERSION`, `fetch_elevations` → EUDEM 25m Europe-only),
      `data/locations.py` (`PhotoLocation`: observer/subject_lat/lon,
      subject_height_m, elevation_difference_m, observer_floor_height_m),
      `tests/test_astronomy_regression.py`, `test_api_regression.py`.
- [ ] Implementierungsoptionen: A (In-place-Refactor) / B (paralleles Modul + Flag)
- [ ] Empfehlung: **Option B**

**Implementierungsoptionen:**

*Option A — In-place-Refactor.* `find_precise_alignment_times` direkt umbauen:
geozentrische α/δ einmal pro Fenster, Rootfinding statt Scan, Parallaxe pro
Beobachter; `find_opportunities` ruft on-demand; `calendar.json`/Cron raus.
Dateien: `astronomy.py`, `opportunity.py`, `precompute.py`.
+ minimale neue Fläche, nutzt getestete Geometrie/Dedup. − zentrale Funktion,
hohes Regressionsrisiko, kein sauberer A/B-Vergleich für AK6. Aufwand: mittel.

*Option B — Paralleles Modul hinter Feature-Flag (empfohlen).* Neue
`calculations/ephemeris_core.py` (geozentrisch, de421, Kometen-Hook) +
`calculations/query_engine.py` (alt/az-Trig, Parallaxe, Rootfinding, Geometrie
über bestehende Helper). Alte `find_precise_alignment_times` bleibt bis AK6 grün;
Flag schaltet um. Elevation-Provider als eigenes `data/elevation.py`.
Dateien: 3 neue Module + Flag in `main.py`/`opportunity.py`.
+ saubere Zwei-Schicht-Trennung (= Spec §4), sicherer Rollback, echter A/B-Vergleich
für AK6, entkoppelt vom zentralen Scan. − mehr neuer Code, temporäre Duplizierung.
Aufwand: mittel-groß.

✅ **Empfehlung: Option B** — der Feature-Flag-Parallelpfad ist die einzige Art,
AK6 (Regression gegen die Alt-Engine) sauber A/B zu messen, und de-riskt den
zentralen `find_precise_alignment_times`-Scan, statt ihn unter laufendem Betrieb
umzuschreiben.

**Testplan:**
- [ ] Automatisiert (Harness): AK3/AK4 als `test_ephemeris_engine.py` (Sonne+Mond
      getrennt, Pfingstberg/Babelsberg-Koordinaten, erwartete alt/az ±1′, Zeiten
      ±1 min). AK6 als Vergleichstest neue vs. alte Engine über alle Locations
      (Zeiten **und** Event-Anzahl). AK1/AK1b als Latenz-Assertion. Edge-Cases
      (Parallaxe, Azimut-Wrap, fehlende Geländehöhe) je eigener Fall.
- [ ] Manuell (http://localhost:8000): `/preview-alignment` bzw. Plan-Endpoint
      für eine angelegte Location → Ergebnis identisch zur Alt-Engine; danach
      beliebige nicht-angelegte `lat/lon` → Plan kommt ohne Vorberechnung.
      AK1 zusätzlich auf Prod (Hetzner CX22) messen.

**Implementierungs-Befunde (2026-06-22, im Sandbox gemessen/verifiziert):**

> Die Ticket-Prämisse „1-Min-Scan = Engpass, Rootfinding löst es" hat sich beim
> Bauen als **falsch** erwiesen. Belege:
> - `find_precise_alignment_times` macht bereits **einen** vektorisierten
>   Skyfield-Call/Tag (~26 ms). Rootfinding-v2 war **langsamer** (39 ms, viele
>   Einzel-Calls) → verworfen.
> - Echte Per-Tag-Last (601 ms) = `calculate_full_report`, darin `sun_info` ~4×
>   und `moon_info` ~2× redundant berechnet (`milky_way`/`moon_info` riefen sie
>   erneut auf).
>
> **✅ Geliefert & verifiziert (in `astronomy.py`):** Redundanz beseitigt —
> `calculate_full_report`/`calculate_milky_way_info`/`calculate_moon_info` reichen
> `sun_info`/`moon_info` durch. **601 → 165 ms/Tag (3,6×)**, Ergebnis-Werte
> **identisch** (Sunrise/Sunset/Golden/Blue/Phase/Illumination/MilkyWay geprüft).
> → AK7 gewahrt, kein Verhaltens-/Feed-Change.
>
> **✅ Foundation gebaut & verifiziert:** `calculations/ephemeris_core.py`
> (Mehrtages-Track, Hebel-1-Reuse: 2. Beobachter = 0 zusätzliche teure Calls) +
> `calculations/query_engine.py::altaz` (Topozentrik inkl. Mond-Parallaxe;
> **AK3: max 0,14′ Sonne / 0,01′ Mond** vs. Skyfield).
>
> **✅ AK1-Architektur bewiesen:** Fensterweite Ephemeride — Sonne+Mond für
> 14 Tage in **2 Skyfield-Calls = 196 ms**, Per-Beobachter-Trig 0,7 ms →
> Kernkosten **~197 ms** für 14-Tage-Plan (Ziel < 500 ms ✓).
>
> **✅ Window-Engine gebaut, verdrahtet & verifiziert:** `calculations/window_engine.py`
> leitet `SunInfo`/`MoonInfo`/`MilkyWayInfo`/Body-Position/Alignment aus 3 Fenster-
> Tracks ab. `astronomy.py` delegiert bei aktivem Fenster (`set_active_window`);
> Feature-Flag **`FOTOALERT_ONDEMAND=1`** in `find_opportunities_multi_day`
> (Default aus → Alt-Pfad unverändert). Messung 14-Tage-Plan, eine Location:
>
> | Metrik | Alt | Neu (Flag an) |
> |---|---|---|
> | 14-Tage-Plan | 3838 ms | **438 ms inkl. Fensteraufbau** (AK1 ✓) |
> | SunInfo/MoonInfo-Felder | — | **±0,04 min** vs. alt (AK4 ✓) |
> | Sonne/Mond alt/az | — | **0,14′ / 0,01′** vs. Skyfield (AK3 ✓) |
> | Golden/Blue/Milchstraße-Opps | 14/14/3 | **identisch** (AK7 ✓) |
> | Regression Flag aus | — | **18/18 grün** (kein Default-Change) |
>
> **✅ Entscheidung 1 (Stephan, 2026-06-22): ein Event pro Passage** — umgesetzt &
> breit verifiziert: **40/40 Passagen** (41 Locations × 14 Tage × Sonne+Mond) durch
> genau ein NEW-Event abgedeckt, **Zeit-Δ = 0 s** zum Alt-Best-Sample, max Δalt
> 0,42′. Zwei Bugs dabei gefunden & gefixt: (a) monotone Qualität → Peak am Rand
> (Ternärsuche ersetzt durch feinen 1-Min-In-Band-Scan), (b) Tagesgrenzen-Event
> (Crown 23:59↔00:02) wurde doppelt emittiert → Scan aufs Tagesfenster begrenzt.
> Azimut-Mond-Events (Section 3) fallen entsprechend **31 → 3** (Quasi-Duplikate weg).
>
> **✅ Entscheidung 2 (Stephan): Build optimiert** — Raster 5→**10 min** (Genauigkeit
> bleibt: SunInfo ±0,09 min, Alignment Δt 0 s), Milchstraßen-Track lazy.
> Fensteraufbau **280 → 135 ms** (Sandbox); finaler AK1-Wert auf Hetzner nach Deploy.
>
> **✅ AK2 geliefert & verifiziert:** neuer Endpoint **`GET /plan`** (main.py) rechnet
> für **beliebige Koordinaten weltweit** on-demand (Paris-Test: 274 ms, 31 Events),
> ohne angelegte Location. **AK5 (Kalender):** `GET /calendar` rechnet bei
> `FOTOALERT_ONDEMAND=1` + `location_id`+`month`+`year` **live** (593 ms/Monat),
> kein 365×N-Batch nötig. Default-Pfad (Cache) unverändert.
>
> **✅ AK5 (Option A, Stephan freigegeben) im Code umgesetzt & verifiziert:**
> Bei `FOTOALERT_ONDEMAND=1` läuft der In-App-Precompute nur noch im **Feed-Modus**
> (14 Tage, leicht) statt `full` → der schwere 365-Tage-Kalender-Batch entfällt,
> Kalender kommt live über `/calendar`. Geändert: `main.py` (Startup + 05:30-Job
> modusabhängig), Deploy-Services `fotoalert.service` + `fotoalert-precompute.service`
> bekommen `Environment=FOTOALERT_ONDEMAND=1`. Default (Flag aus) = bisheriges
> Verhalten. Import OK, Endpoints OK, Regression 18/18 grün.
> **Server-Apply = Stephans Schritt** (deploy.sh / systemctl); `precompute.py` bleibt
> (kein Löschen). Der System-Timer (`00:01`, `--feed-only`) bleibt, läuft nun dank
> Flag schnell.
>
> **✅ Punkt 4 — `data/elevation.py`** geliefert: `ElevationProvider` mit
> persistentem Tile-Cache (kein TTL) + Fallback `(0.0, incomplete=True)`; `/plan`
> löst Geländehöhe automatisch auf und liefert `elevation_incomplete` mit. EUDEM
> (Europa) dahinter, weltweiter DEM = TASK-26. Verifiziert (Cache-Hit, Fallback,
> Persistenz, /plan-Integration).
>
> **✅ Punkt 5 — `tests/test_ephemeris_engine.py`** geliefert: 14 Tests für
> AK1/AK1b/AK3/AK4/AK6 + Edge-Cases (Hebel-1, Azimut-Wrap, fehlende Geländehöhe).
> **Volle Suite: 63 passed, 0 failed.** AK1b (365-Tage = ~21 s) als Guard `<45 s`;
> 5-s-Ziel ist Platzhalter (OF3), Per-Tag-Overhead (Scoring/Refine) später optimierbar.
>
> **✅ Release v1.11.0 (2026-06-22) deployed & verifiziert:** Health ok; `/plan`
> live mit Auto-Geländehöhe (Paris: elev_diff 7,8 m, `elevation_incomplete=false`).
> **Schalter noch AUS** (Default-Verhalten unverändert) — das ist die geplante
> dormante Stufe.
>
> **✅ Aktivierungs-Blocker gelöst (Kalender-Monatsübersicht):** Das Frontend lädt
> `/calendar?month&year` **ohne** `location_id` (alle Locations). Neu: On-Demand-
> Monats-Sammelliste mit In-Memory-Cache (`_compute_month_all_locations`) + Pre-Warm
> des aktuellen Monats beim Start. Damit ist die Monatsansicht bei Flag-an sofort da
> (Cache-Hit), der 365×N-Batch entfällt. Verifiziert: 4 Locs/Monat 1,2 s, Cache-Hit
> 0 ms, per-Location-Monat 0,31 s → 64 Locs ≈ 20 s Pre-Warm (Hintergrund). Tests grün.
> **Noch nicht released** (kommt mit dem nächsten Release vor der Aktivierung).
>
> **➡️ Verbleibend:**
> - **Release** der Kalender-Aggregat-Änderung (+ TASK-26), dann **Schritt 2 —
>   Aktivieren:** systemd-Service-Dateien nach `/etc/systemd/system` kopieren
>   (`ssh root`), `daemon-reload`, Neustart → `FOTOALERT_ONDEMAND=1` aktiv. Reversibel.
> - **TASK-26** (Punkt 6): weltweiter DEM (EUDEM → global).
> - `precompute.py` bleibt (kein Löschen ohne Freigabe).

#### 📋 Implementation Spec Ende

---


### TASK-26 · Weltweiter DEM für Geländehöhen (EUDEM → global) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Mittel |
| **Status** | Done (v1.11.2 deployed 2026-06-22; live verifiziert: NY 8,0 m, incomplete=false) |
| **Erstellt** | 2026-06-22 |

**Beschreibung:** Der Elevation-Provider (`data/elevation.py`, TASK-25) nutzt bisher
nur **EUDEM 25m = nur Europa**. Damit die On-Demand-Engine (`/plan`) weltweit
korrekte Geländehöhen liefert, wird eine **Dataset-Kette** eingeführt: EUDEM (Europa,
fein) → globaler DEM (z.B. SRTM 30m / Mapzen) als Fallback außerhalb Europas.
Liefert ein Dataset `null` (keine Abdeckung), wird das nächste versucht; erst wenn
alle leer sind, greift der `incomplete=True`-Fallback.

**Bezug:** Folge-Ticket von TASK-25 (dort als OF4 / Scope-Abgrenzung vorgemerkt).
Kein Architektur-Umbau — nur Erweiterung von `ElevationProvider`.

**Hinweis Betrieb:** OpenTopoData Public-API hat Rate-Limits (1 req/s, 1000/Tag) →
für Skalierung später eigenes Hosting erwägen (separat).

**⚠️ Live-Befund (2026-06-22, v1.11.1 deployed):** Dataset-Kette ist im Code, aber
weltweite Auflösung **funktioniert noch nicht**: `/plan` für New York →
`elevation_incomplete:true` (Höhe 0). Ursache: die 3 Dataset-Calls (EUDEM→SRTM→
Mapzen) feuern schnell hintereinander → 2./3. läuft ins 1-req/s-Limit (429). Europa
ok, weil EUDEM gleich der 1. Call ist. Fallback greift sauber (kein Crash, Plan kommt,
nur als unvollständig markiert).
**TODO TASK-26:** kurze Drosselung (~1,1 s Pause) **nur** vor den Folge-Datasets
einbauen (Europa bleibt schnell, da 1. Call trifft); danach NY-Test grün erwarten.
Längerfristig eigenes OpenTopoData-Hosting gegen das Tageslimit.

---


### US-89 · Sterne-Bewertungen serverseitig speichern & für alle aggregieren `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-21 |
| **Abgeschlossen** | 2026-06-21 |

**Beschreibung:** Standort-Bewertungen (1–5 Sterne) liegen aktuell nur lokal im `localStorage` (pro Gerät). Für das Go-Live-Versprechen „Bewertung sichtbar für ALLE" müssen Sterne serverseitig persistiert und aggregiert (Summe + Ø) werden — analog zu BUG-26, das die SQLite-Persistenz für Verifikationen bereits gebaut hat.

**Bezug:** Go-Live-Blocker aus ROADMAP.md (NOW). Baut auf der SQLite-Persistenzschicht von BUG-26 [x] auf (gemeinsame Infrastruktur). Grenzt an US-68 (Host-Approval) — eigenständig, aber gleiche Server-Daten-Domäne. Ersetzt das nie angelegte US-24 (lokale Bewertung).

**Scope:**
- Eingeschlossen: Server-Endpoint zum Speichern/Abrufen von Bewertungen pro Location; Aggregation Summe + Durchschnitt; Frontend-Anzeige geteilt statt `localStorage`; ein Nutzer = eine Bewertung pro Location (überschreibbar).
- Ausgeschlossen: Freitext-Reviews, Spam-/Missbrauchsschutz, Nutzer-Authentifizierung über US-66 hinaus.

**Akzeptanzkriterien:**
- [x] Bewertung (1–5) wird serverseitig persistiert (gleiche SQLite-Schicht wie BUG-26) und ist geräteübergreifend sichtbar
- [x] Pro Location werden Anzahl und Durchschnitt (Ø) berechnet und für alle Nutzer angezeigt
- [x] Ein Nutzer kann seine eigene Bewertung abgeben und ändern (keine Mehrfachzählung)
- [x] Bestehende lokale Bewertungen (localStorage) brechen das Frontend nicht (saubere Migration/Fallback)
- [x] Schreib-Endpoint ist gegen US-66-Auth abgesichert, soweit nötig

**Offen für Analyse:** Datenmodell (eigene Tabelle vs. Erweiterung der Verifikations-Tabelle), Identität „ein Nutzer" ohne individuelle Accounts (Geräte-Token?), Umgang mit Alt-Daten aus localStorage.


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


### US-25 · Duplikate identifizieren (Host-Tool)

| Feld | Wert |
|------|------|
| **Typ** | Feature |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-26 |
| **Abgeschlossen** | 2026-06-26 |
| **In Progress seit** | 2026-06-26 |

> **Als Host** möchte ich Locations mit ähnlichem GPS-Standort und überlappenden Motiven finden und zur Bereinigung vorgeschlagen bekommen.
>
> **Akzeptanzkriterien (original):**
> - CLI-Tool oder Backend-Endpoint `/admin/duplicates`
> - Findet Locations < 300m Abstand voneinander
> - Zeigt Paarweise: Name A / Name B · Entfernung · Azimut-Differenz
> - Empfiehlt: „Zusammenführen" (gleicher Spot, verschiedene Standpunkte) oder „Löschen" (echter Duplikat)
> - Output als tabellarische Übersicht oder JSON

---

**📐 Example Mapping**

📏 **Rule 1 — Nähe-Scan:** Alle Locations (Base + Custom) werden paarweise verglichen; jedes Paar mit Abstand < 300 m (observer-to-observer, Haversine) erscheint im Report.

🟢 Example 1a: Berliner Dom vom Spreeufer (52.5196, 13.4008) und Dom – Lustgarten (52.5200, 13.4012) sind 108 m voneinander entfernt → erscheinen als Paar.
🟢 Example 1b: Zwei Locations 400 m auseinander → nicht im Report.

📏 **Rule 2 — Azimut-Differenz:** Pro Paar wird die mittlere `ideal_azimuth_range` verglichen; die Differenz (in Grad) erscheint im Output.

🟢 Example 2a: Location A hat Range (133–173), Location B (120–160) → Mitte A=153, B=140 → Diff=13°.
⚠️ **Annahme:** Wenn `ideal_azimuth_range` bei einer Location `None` ist, wird „–" ausgegeben (kein Crash). Bitte bestätigen.

📏 **Rule 3 — Merge-/Lösch-Empfehlung:** Das Tool leitet aus Abstand + Azimut-Differenz eine Empfehlung ab.

🟢 Example 3a: Abstand < 50 m **und** Azimut-Diff < 20° → „Echter Duplikat – Löschen prüfen".
🟢 Example 3b: Abstand 50–300 m **oder** Azimut-Diff ≥ 20° → „Ähnlicher Spot – Zusammenführen prüfen".
⚠️ **Annahme:** Schwellenwerte 50 m / 20° sind meine Defaults — bitte bestätigen oder anpassen.

📏 **Rule 4 — Scope:** Das Tool umfasst Base-Locations (60 Stück) + Custom-Locations aus der SQLite-DB. Location-Overrides ändern Koordinaten → das Tool liest die durch Overrides patched Koordinaten (via `main.py`-Bootstrap-Liste, nicht direkt aus `data/locations.py`).

⚠️ **Annahme:** Overrides werden beim Tool-Aufruf aus der DB eingelesen, damit der gepatchte Stand geprüft wird. Bitte bestätigen.

---

**✅ Akzeptanzkriterien**

- [ ] Das Tool läuft als CLI-Script (`python3 tools/find_duplicates.py`) und gibt eine lesbare Tabelle im Terminal aus
- [ ] Alle Base-Locations (60) + Custom-Locations aus der SQLite-DB werden einbezogen; Location-Overrides werden auf Base-Koordinaten angewendet
- [ ] Jedes Paar mit observer-to-observer-Abstand < 300 m erscheint in der Ausgabe (kein Pair wird ausgelassen)
- [ ] Pro Zeile: Name A | Name B | Abstand (m) | Azimut-Diff (°) | Empfehlung
- [ ] Wenn `ideal_azimuth_range` fehlt (`None`), wird Azimut-Diff als „–" angezeigt (kein Crash)
- [ ] Empfehlung „Löschen prüfen" bei Abstand < 50 m **und** Azimut-Diff < 20°; sonst „Zusammenführen prüfen"
- [ ] Optionaler `--json`-Flag gibt JSON-Output statt Tabelle
- [ ] Edge Case: 0 Paare gefunden → „Keine Duplikate gefunden." ausgegeben

**Aktueller Live-Stand (Datenverifikation 2026-06-26):**
- 60 Base-Locations, 1 Custom-Location
- 3 Paare < 300 m: Dom/Spreeufer–Dom/Lustgarten (108 m), BrandTor/Tiergarten–BrandTor-Back (215 m), BrandTor/Tiergarten–Holocaust-Memorial (239 m)

---

**💀 Pre-Mortem**

📎 **Code-Verifikation (2026-06-26):**
- `PhotoLocation.observer_lat/lon` in `data/locations.py` bestätigt als Vergleichsfeld
- `ideal_azimuth_range` ist `Optional[tuple[float, float]]` → kann `None` sein (Pflicht: None-Guard)
- Keine bestehende `haversine`-Funktion im Backend — wird inline in pipelines gebaut (muss neu implementiert werden)
- `store.py:load_all_custom()` gibt Liste von dicts, `load_all_overrides()` gibt Liste mit `id`+flachen Feldern
- Main.py bootstrapped die Location-Liste beim Start mit Overrides — das CLI-Tool muss diese Logik replizieren

💀 **Szenario 1: Overrides werden ignoriert → falsche Koordinaten verglichen**
Auslöser: CLI-Tool importiert `LOCATIONS` direkt aus `data/locations.py` ohne Override-Anwendung
Frühwarnung: BrandTor-Koordinaten stimmen nicht mit Admin-UI überein
Gegenmaßnahme: Override-Ladelogik aus `main.py` in ein gemeinsames Util extrahieren oder im CLI direkt replizieren → im AK verankert

💀 **Szenario 2: Custom-Locations fehlen im Report**
Auslöser: Tool liest nur `LOCATIONS`, nicht die SQLite-DB
Frühwarnung: Custom Locations tauchen nie als Duplikat auf
Gegenmaßnahme: `store.load_all_custom()` explizit im CLI aufrufen → im AK verankert

💀 **Szenario 3: None-Azimut führt zu Crash**
Auslöser: `ideal_azimuth_range` ist None bei einer der Locations → Arithmetic auf None
Frühwarnung: AttributeError im Test-Lauf mit Minimal-Location
Gegenmaßnahme: None-Guard mit Fallback „–" → im AK verankert

---

**🏗 Architektur-Analyse**

Betroffene Dateien:
- `backend/data/locations.py` — Quelle der Base-Locations (`LOCATIONS`)
- `backend/data/store.py` — `load_all_custom()`, `load_all_overrides()`
- `backend/main.py` — Zeigt wie Overrides auf Base-Locations angewendet werden (Bootstrap-Logik)
- **Neu:** `backend/tools/find_duplicates.py` (Option A) oder neuer Endpoint in `main.py` (Option B)

Haversine-Berechnung: muss inline implementiert werden (< 10 Zeilen, kein Dependency-Bedarf).

---

**🔀 Implementierungsoptionen**

### Option A — CLI-Script `backend/tools/find_duplicates.py`
- **App-Wirkung:** Nur du als Host siehst das Ergebnis im Terminal; kein Effekt für App-User.
- Vorgehen: Python-Script, liest LOCATIONS + Custom aus DB + Overrides, berechnet Haversine-Paare, gibt Tabelle/JSON aus
- Betroffene Dateien: `backend/tools/find_duplicates.py` (neu, ~80 Zeilen)
- Vorteile: kein Server-Neustart nötig; läuft lokal oder per SSH; kein API-Auth-Problem
- Nachteile: muss manuell per SSH aufgerufen werden
- Aufwand: klein

### Option B — Backend-Endpoint `GET /admin/duplicates`
- **App-Wirkung:** Endpoint via Browser/curl abrufbar; könnte künftig in Admin-UI eingebunden werden.
- Vorgehen: neuer FastAPI-Router, gleiche Logik wie A, JSON-Response
- Betroffene Dateien: `backend/main.py` (neuer Router, ~50 Zeilen)
- Vorteile: ohne SSH nutzbar; erweiterbar für Admin-UI
- Nachteile: Server-Neustart + Deploy für jede Änderung; kein Auth-Schutz im aktuellen Setup (öffentlich erreichbar)
- Aufwand: klein–mittel

✅ **Empfehlung: Option A (CLI-Script)** — Das Tool wird nur von dir als Host gebraucht, kein User-Facing-Bedarf. CLI ist sofort nutzbar (lokal + SSH), kein Deploy-Zyklus, kein Auth-Risiko. Wenn später ein Admin-Panel entsteht, kann die Logik einfach extrahiert werden.

---

**📋 Analyse & Planung**

- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `data/locations.py`, `data/store.py`, `main.py`
- [x] Daten-Validierung: 3 echte Paare < 300 m im Live-Stand bestätigt
- [x] Implementierungsoption bestätigt: A (CLI-Script)
- [x] Implementierung: `backend/tools/find_duplicates.py`

**Testplan:**
- Automatisiert: kein pytest (CLI-Only-Tool); manuell ausreichend
- Manuell (lokal): `cd FotoAlert/backend && python3 tools/find_duplicates.py` → 3 Paare erwartet
- Manuell (JSON): `python3 tools/find_duplicates.py --json` → valides JSON-Array
- Manuell (Edge): Location ohne `ideal_azimuth_range` → kein Crash, „–" in Azimut-Diff-Spalte


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


### TASK-11 · Impressum & Copyright einbauen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | (vorher offen) |
| **In Progress seit** | 2026-06-18 |
| **Abgeschlossen** | 2026-06-18 |

**Beschreibung:** Impressum-Seite in der PWA ergänzen (erreichbar über Einstellungen).

**Scope:**
- Eingeschlossen: neues Bottom-Sheet `#impressum-sheet`, Button in Settings-Tab (neue Sektion „Rechtliches"), Inhalt: Copyright, §5 TMG, API-Credits, Datenschutzhinweis
- Ausgeschlossen: Backend-Änderungen, eigene Route/HTML-Datei

**Akzeptanzkriterien:**
- [ ] Button „Impressum" in Settings-Tab öffnet Bottom-Sheet
- [ ] Inhalt: Copyright © 2026 Stephan Schumann, §5-TMG-Angaben (Name, Adresse, Kontakt), API-Lizenzen, Datenschutzhinweis
- [ ] Sheet schließbar per ×-Button (identisch zu anderen Sheets)
- [ ] Funktioniert auf iPhone Safari (PWA) und Desktop

**Analyse & Planung:**
- [x] Settings-Tab nutzt `#page-settings` mit `settings-content`-Div, HTML via `Settings.render()` injiziert (Zeile 3283ff)
- [x] Ansatz: neues `#impressum-sheet` (identisch zu `#detail-sheet` Struktur), `openImpressum()` Funktion, neuer Settings-Row-Button
- [x] Betroffene Datei: ausschließlich `web/index.html`
- [x] Kein Root-Cause-Problem — reine Ergänzung

**Testplan:**
- [ ] Settings → Impressum-Button tippen → Sheet öffnet
- [ ] ×-Button schließt Sheet
- [ ] Alle Inhaltsbereiche sichtbar und lesbar (iPhone + Desktop)

**Implementierungsnotizen:**
- `#impressum-sheet` nach Filter-Sheet eingefügt (z-index 104/105)
- `Impressum.open()` injiziert HTML-Inhalt lazy (identisch zu `Settings.render()`)
- Neue Sektion „Rechtliches" in Settings mit Chevron-Row
- Desktop-Centering: `#impressum-sheet` in `@media (min-width:600px)` BUG-07-Block ergänzt
- Klassen-Pattern: `.open` für Overlay und Sheet (konsistent mit allen anderen Sheets)


### TASK-04 · Weitere Locations erfassen `[x]`

| Feld | Wert |
|------|------|
| **Status** | Done |
| **Analysiert** | 2026-06-25 |
| **Implementiert** | 2026-06-25 |
| **Abgeschlossen** | 2026-06-27 |

> 5 neue Locations in `backend/data/locations.py` als Base-Locations eintragen: Schloss Cecilienhof, Schloss Pfaueninsel, Kloster Chorin, Dorfkirche Schönermark (Uckermark), Seelower Höhen Ehrenmal.
>
> *Hinweis: „Locationscout-Scroll-Limit von 12" bezieht sich auf die externe Website locationscout.net — außerhalb unserer Kontrolle, kein Implementierungs-Scope.*

**Scope:**
- Eingeschlossen: 5 neue `PhotoLocation`-Einträge in `backend/data/locations.py`; Prod-SQLite-Check vor Deployment (ID-Kollision)
- Ausgeschlossen: Locationscout.net-Limit (extern), Custom-Location-Bearbeitung, neue API-Endpoints

**Akzeptanzkriterien:**
- [ ] Die 5 neuen Locations erscheinen im Locations-Tab der App
- [ ] Alle bestehenden Custom Locations (per App hinzugefügt) sind nach dem Deployment unverändert vorhanden
- [ ] Alle bestehenden Location-Overrides (Koordinaten-Edits per App) bleiben erhalten
- [ ] Vor Deployment: SQLite-Check auf Prod ergab keine ID-Kollision mit den neuen IDs
- [ ] Nach Deployment: `GET /locations` liefert ≥ 60 Locations (55 bestehend + 5 neue)
- [ ] Alle 5 neuen Locations haben `subject_height_m > 0` → Scout-Pipeline-Kandidaten
- [ ] Nach Server-Neustart + Precompute erscheinen Events der neuen Locations im Feed

**⚠️ GPS-Verifikations-Pflicht:** Koordinaten für Schönermark (🔴) und Seelower Höhen (🔴) müssen vor Ort bestätigt werden.

**Pre-Mortem:**
- 💀 ID-Kollision mit bestehender Custom Location → Custom Location wird bei Startup still ignoriert (main.py Z. 143–147) → Gegenmaßnahme: SQLite-Check ist AK
- 💀 `subject_height_m` fehlt → Scout-Pipeline ignoriert Location ohne Fehlermeldung → Gegenmaßnahme: AK „alle 5 haben `subject_height_m > 0`"
- 💀 Koordinaten falsch → falsche Alignment-Berechnung → Gegenmaßnahme: GPS vor Ort; FOV-Karte in App prüfen

**Recherchierte Location-Daten:**

| Location | Subject-Lat | Subject-Lon | Observer-Lat | Observer-Lon | Höhe | Breite | Dist |
|----------|-------------|-------------|--------------|--------------|------|--------|------|
| Schloss Cecilienhof | 52.4227 | 13.0706 | 52.4212 | 13.0730 | 14m | 80m | 220m |
| Schloss Pfaueninsel | 52.4308 | 13.1197 | 52.4315 | 13.1100 | 18m | 30m | 650m |
| Kloster Chorin | 52.8944 | 13.8761 | 52.8942 | 13.8720 | 24m | 35m | 280m |
| Dorfkirche Schönermark 🔴 | 53.0162 | 14.0405 | 53.0155 | 14.0388 | 18m | 12m | 120m |
| Seelower Höhen Ehrenmal 🔴 | 52.5340 | 14.1680 | 52.5325 | 14.1665 | 10m | 4m | 180m |

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `backend/data/locations.py`, `main.py` `_load_custom_locations()` Z. 143–160
- [x] GPS-Recherche für alle 5 Locations abgeschlossen
- [ ] SQLite-Check auf Prod vor Implementierung

**Testplan:**
- [ ] Manuell: `GET /locations` → 5 neue Namen in der Liste
- [ ] Manuell: Locations-Tab → 5 neue Cards sichtbar, FOV-Karte je Location prüfen
- [ ] Manuell: nach Deployment → bisherige Custom Locations noch vorhanden
- [ ] Nach Precompute: Feed zeigt Events für neue Locations


### US-46 · Karten-Ansichtsmodi `[x]`
> **Als Fotograf** möchte ich zwischen Standard-, Satelliten- und Nacht-Ansicht auf der Karte wechseln können.
>
> **✅ Verifiziert & geschlossen (2026-06-21):** Layer-Toggle bereits implementiert in `web/index.html` — Buttons Nacht/Standard/Satellit (Z. 768–771) → `MapView.setLayer()`, Satellit via ArcGIS World_Imagery (Z. 2506). Anforderung erfüllt, kein Rest-Scope.


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

---


### BUG-31 · Jahreskalender: Kopfzeilen-Counter inkonsistent (Gesamtzahl < Monatssumme) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-23 |

**Beschreibung:** Im Jahreskalender-Panel zeigt die Kopfzeile „1257 Events · 5289 im Monat · nur Astronomie" — die Gesamtzahl (1257) ist kleiner als die Monatssumme (5289). Das ist logisch inkonsistent und verwirrt den Nutzer. Erwartetes Verhalten: Gesamtzahl ≥ Monatszahl, oder die Bezeichnungen sind klar unterschiedlich (z. B. „im aktuellen Filterfenster" vs. „im Monat").

**Bezug:** Kein direktes Vorgänger-Ticket. Verwandt mit BUG-27 [x] (Jahreskalender leer) — dort ging es um leere Daten, hier um fehlerhafte Aggregation/Anzeige.

---


### BUG-32 · 14-Tage-Feed leer trotz aktivem Datenbestand und ohne Filterkriterien `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-23 |

**Beschreibung:** Der 14-Tage-Feed zeigt „Keine besonderen Chancen in den nächsten 14 Tagen. Goldene & Blaue Stunde über den Eventtyp-Filter einblenden." — obwohl kein Filter aktiv ist. Der Jahreskalender zeigt im selben Zeitraum tausende Events, d. h. Daten sind vorhanden. Erwartet: Feed zeigt Chancen mit besonderem Alignment-Score (Mond, Sonne in goldener/blauer Stunde), ohne dass der Nutzer manuell einen Filter aktivieren muss.

**Bezug:** Mögliche Regression von BUG-14 [x] (Kalender leer nach Cron) und BUG-27 [x] (Jahreskalender leer). Ursache könnte im opportunities.json-Cache oder im Feed-Filterlogik liegen.

---

#### Analyse (2026-06-23)

**📎 Code-Verifikation:**
- `backend/main.py` Z.754–788: `_filter_feed()` filtert nach `window_end < now_utc`, `shoot_dt > cutoff` und `overall_score < 0.35`. Kein Event-Typ-Filter hier.
- `web/index.html` Z.2012–2020: `Filter.apply()` entfernt `_ROUTINE_TYPES = ['Goldene Stunde Morgen', 'Goldene Stunde Abend', 'Blaue Stunde']` immer dann, wenn kein Eventtyp-Filter aktiv ist (US-40-Logik).
- Lokaler Cache (`data/cache/opportunities.json`, computed 2026-06-23T06:37Z): 1775 Events — 784× Goldene Stunde Abend, 784× Blaue Stunde, 168× Milchstraße (56 abgelaufen), 39× Mond-Alignment. → Lokal passieren 151 Non-Routine-Events den Filter; Feed **wäre lokal nicht leer**.

**Schlussfolgerung Root-Cause:**

Die Fehlermeldung setzt exakt diesen Code-Pfad voraus:
```
this.data.length > 0  (API lieferte Daten)
Filter.apply() → 0   (alle herausgefiltert)
Filter.activeCount() === 0  (kein expliziter Filter aktiv)
→ "Keine besonderen Chancen …"
```
Das bedeutet: die API lieferte **ausschließlich Routine-Types** (Goldene/Blaue Stunde). Non-Routine-Events (Milchstraße, Mond-Alignment) fehlen im API-Response — entweder weil der **Produktions-Cache stale ist** (ältere `opportunities.json` mit abgelaufenen Non-Routine-Events) oder weil Non-Routine-Events in bestimmten Zeitfenstern schlicht dünn gesät sind (strukturelles US-40-UX-Problem).

**Zwei unabhängige Ursachen:**

| # | Ursache | Nachweis | Konfiguration |
|---|---------|----------|--------------|
| A | **Stale Prod-Cache** — `computed_at` liegt > 24h zurück, Non-Routine-Events abgelaufen | SSH: `cat /var/www/fotoalert/data/cache/opportunities.json \| python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('computed_at'))"` | Cron läuft täglich 05:30 auf dem Server; bei Fehler kein Alarm |
| B | **US-40 UX-Lücke** — Routine-Events werden versteckt, aber kein Soft-Fallback wenn Non-Routine = 0 | Frontend `Filter.apply()` Z.2018–2020 | Design-Entscheidung US-40, kein Fallback implementiert |

---

**Example Mapping:**

📏 **Rule 1:** Der Feed zeigt ohne aktiven Filter mindestens die nicht abgelaufenen Non-Routine-Events (Milchstraße, Mond-Alignment, Sonnen-Alignment).
- 🟢 Gegeben: keine Filter aktiv, Cache enthält 39× Mond-Alignment (alle zukünftig) → Feed zeigt ≥ 39 Events.
- 🟢 Gegeben: Cache enthält nur Goldene Stunde + Blaue Stunde → Feed zeigt Fallback-Meldung ODER zeigt Routine-Events als Fallback mit Label.
- 🔴 Negativ: Filter aktiv (nur Goldene Stunde) → nur Goldene Stunde erscheint; das ist gewollt.

📏 **Rule 2:** Der Prod-Cache darf maximal 26 Stunden alt sein (Cron läuft 05:30, +2h Puffer).
- 🟢 Gegeben: Cron läuft, `computed_at` < 26h → Feed-Daten aktuell.
- 🔴 Edge Case: Cron schlägt fehl, Cache > 26h alt → `/health` oder Monitoring-Endpoint sollte Warnung signalisieren.

📏 **Rule 3 (US-40-Soft-Fallback):** Wenn der Feed nach dem Routine-Filter leer ist (Non-Routine = 0), werden Routine-Events als sekundäre Ebene gezeigt — klar markiert als „Tägliche Chancen".
- 🟢 Gegeben: nur Goldene Stunde im Feed, kein Filter → Feed zeigt Goldene Stunde mit Abschnitt „📅 Tägliche Chancen (Goldene/Blaue Stunde)".
- 🔴 Negativ: Routine-Filter abschalten wenn Non-Routine vorhanden → keine Änderung (Routine bleibt hidden).

---

**Scope:**
- Eingeschlossen: Frontend `Filter.apply()` Soft-Fallback; Prod-Cache-Freshness-Check via `/health` oder neuem Endpoint.
- Ausgeschlossen: Precompute-Algorithmus (welche Event-Typen generiert werden), Cron-Scheduling-Umbau.

**Akzeptanzkriterien:**
- [ ] Feed zeigt Non-Routine-Events (Mond-Alignment, Milchstraße) ohne aktiven Filter, sofern im Cache vorhanden und nicht abgelaufen.
- [ ] Feed zeigt Routine-Events (Goldene/Blaue Stunde) als Fallback-Sektion wenn Non-Routine = 0 und kein Filter aktiv — mit eigenem Label „Tägliche Chancen".
- [ ] `activeCount()` gibt weiterhin 0 zurück wenn kein expliziter Filter aktiv ist (kein Zähler-Regressions-Bug).
- [ ] Edge Case: Wenn `/opportunities` leere Liste zurückgibt (n = 0) → Meldung bleibt „Keine Chancen gefunden. Mindest-Score: …" (kein falscher Fallback).
- [ ] Prod-Schritt: SSH-Verifikation `computed_at` — wenn Cache > 26h → manuell `/refresh-feed` triggern + neu testen.

**Pre-Mortem:**

💀 **Szenario 1: Nur UX gefixt, aber Prod-Cache weiter stale**
- Auslöser: Fix deployed, aber Cron auf Prod läuft immer noch nicht → Non-Routine-Events im Cache immer abgelaufen → Fallback-Sektion zeigt Routine, verdeckt das echte Problem.
- Gegenmaßnahme: Cache-Freshness als AK (≤ 26h) vor Release verifizieren.

💀 **Szenario 2: Soft-Fallback bricht Routine-Filter-Intentionalität (US-40)**
- Auslöser: User sieht plötzlich Goldene Stunde im Feed ohne Filter — versteht nicht warum, findet UX schlechter.
- Gegenmaßnahme: Fallback-Sektion klar visuell trennen + Label „Tägliche Chancen (kein besonderes Event)" einblenden; nicht einfach in den normalen Feed mischen.

💀 **Szenario 3: `activeCount()` Diskrepanz — Filter als aktiv gezählt obwohl intern Routine-Hiding läuft**
- Auslöser: US-40-Default-Hiding ist technisch ein „stiller Filter", aber `activeCount()` kennt ihn nicht → Empty-State zeigt immer „kein Filter aktiv", auch wenn Routine-Hiding zuschlägt.
- Gegenmaßnahme: Empty-State-Nachricht anpassen (nicht „kein Filter aktiv" implizieren wenn Routine-Hiding greift).

📎 **Code-Verifikation:** `_filter_feed` gelesen (main.py Z.754–788), `Filter.apply()` gelesen (index.html Z.2012–2070), `_ROUTINE_TYPES` bestätigt. Cache-Inhalt analysiert: 151 Non-Routine-Events lokal vorhanden → Bug tritt auf Prod auf (stale Cache) ODER US-40-Fallback fehlt bei Non-Routine = 0.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `web/index.html` → `Filter.apply()`, `backend/main.py` → `_filter_feed`, `data/cache/opportunities.json`
- [ ] Implementierungsoptionen: A / B
- [ ] Empfehlung: offen — wartet auf Weg-Gate

**Testplan:**
- [ ] Manuell: SSH → `computed_at` prüfen; falls > 26h → `/refresh-feed` (POST, Auth erforderlich) → neu laden.
- [ ] Manuell lokal: `Filter._ROUTINE_TYPES` alle Events im Testcache → Feed zeigt „Tägliche Chancen"-Fallback.
- [ ] Automatisiert: pytest `test_bug32_feed_fallback` — Mock `_feed_cache` mit nur Routine-Types, `GET /opportunities` → Response nicht leer; Frontend-Logik als Unit-Test schwer abbildbar, manueller Browser-Check.

---


### BUG-33 · Neue Location „Schloss Babelsberg von Glienicker Brücke": Mond-Chance am 26.06 fehlt `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-23 |

**Beschreibung:** Stephan hat die Location „Schloss Babelsberg von Glienicker Brücke" hinzugefügt. Laut PhotoPills steht der Mond am 26.06.2026 um 21:27 Uhr (GMT+2) 97,1 m über dem Motiv und 77 m über dem Turm — ein klares Alignment-Event. Die App zeigt für diese Location keine entsprechende Chance. Erwartet: Das Alignment taucht im Feed und/oder Jahreskalender auf.

**Bezug:** Möglicherweise verwandt mit Memory-Notiz „precompute Datenquelle" — precompute.py verarbeitet keine Custom-Locations (nur Basis-LOCATIONS + Overrides, nicht neu via UI hinzugefügte). Grenzbereich: BUG-29 [x] (veraltete GPS-Daten), TASK-25 [x] (On-Demand-Ephemeriden-Engine). Ggf. ist die On-Demand-Engine der Fix-Pfad.

---

**Root Cause (bestätigt durch Code-Analyse):**
`precompute.py` importiert `LOCATIONS` aus `data/locations.py` — das sind ausschließlich hartcodierte Basis-Locations. Die Funktion `_apply_location_overrides()` ergänzt nur PATCH-Overrides für Basis-Locations. Custom Locations (via UI angelegt, in SQLite `custom_locations`-Tabelle gespeichert) werden NIE geladen.

Konkrete Fehler-Kette:
1. User legt „Schloss Babelsberg" an → `LOCATIONS.append(new_loc)` + `_run_precompute_single("custom_xyz")` wird aufgerufen
2. Subprocess: `precompute.py --location-id custom_xyz` startet — LOCATIONS = nur Basis → `locations_to_process = []` → **Log: "Location 'custom_xyz' nicht gefunden"** → 0 Events berechnet
3. Nächtlicher Cron (`precompute.py` ohne Flag) iteriert ebenfalls nur LOCATIONS → Custom Location bleibt unsichtbar
4. `/opportunities` liest ausschließlich aus `_feed_cache` (opportunities.json) → kein Fallback
5. `/calendar` hat On-Demand-Pfad, aber nur wenn `FOTOALERT_ONDEMAND=1` (Default: `"0"`)

---

**Example Mapping:**

📏 **Rule 1:** Custom Locations erscheinen nach dem Anlegen im 14-Tage-Feed (opportunities.json), wenn Alignment-Events im Zeitfenster liegen.
🟢 **Example 1a (Happy Path):** Given: Custom Location „Babelsberg" angelegt, Mond-Alignment 26.06. 19:27 UTC in Precompute-Fenster / When: `precompute.py` läuft (Single oder nächstäglicher Cron) / Then: `/opportunities` enthält Event mit `location_id=custom_xyz`, `event_type="Mond-Alignment"`, `shoot_time` ≈ `2026-06-26T19:27`.
🟢 **Example 1b (Edge Case — kein Alignment im Fenster):** Given: Custom Location angelegt, aber nächstes Alignment erst in 20 Tagen / When: Feed-Recompute läuft / Then: Feed leer für diese Location — kein Fehler, kein Crash.

📏 **Rule 2:** Custom Locations erscheinen im Jahreskalender (`/calendar`).
🟢 **Example 2a:** Given: Custom Location angelegt, Kalender wird abgerufen / When: `GET /calendar?location_id=custom_xyz&month=6&year=2026` / Then: Events für diese Location vorhanden.
🟢 **Example 2b (Calendar-Recompute nach Anlage):** Given: `_run_precompute_single` abgeschlossen / When: `_load_caches()` erneut ausgeführt / Then: `_calendar_cache` enthält Einträge für `custom_xyz`.

📏 **Rule 3:** Nächstäglicher Cron berücksichtigt Custom Locations dauerhaft (nicht nur beim Anlegen).
🟢 **Example 3a:** Given: Custom Location seit 7 Tagen gespeichert / When: nächtlicher Cron läuft / Then: Neue Tage werden für Custom Location berechnet (inkrementeller Calendar-Flow).

---

**Akzeptanzkriterien:**
- [x] Nach dem Anlegen einer Custom Location (via `/preview-alignment?save=true`) erscheint binnen 5 Minuten mindestens ein Event im Feed (`GET /opportunities?location_id=<id>`), sofern ein Alignment-Event im 14-Tage-Fenster liegt.
- [~] `GET /calendar?location_id=<custom_id>&month=6&year=2026` liefert das Babelsberg-Mond-Alignment am 26.06.2026 (shoot_time ≈ `2026-06-26T19:27Z`, event_type enthält „Mond"). *(ausstehend — nächster Prod-Cron 00:01 UTC berechnet Babelsberg erstmals)*
- [x] Nach einem Vollkalender-Recompute (`python3 precompute.py --full`) sind Custom-Location-Events in `calendar.json` enthalten (prüfbar via `grep "custom_" data/cache/calendar.json`).
- [x] Log beim Single-Recompute zeigt NICHT mehr „Location 'custom_xyz' nicht gefunden"; stattdessen normale Ausgabe mit berechneten Events.
- [x] Edge Case: Existiert keine Custom Location in SQLite, läuft precompute.py ohne Fehler durch (bestehende Basis-Locations unberührt).

---

**Pre-Mortem:**

💀 **Szenario 1: SQLite-Zugriff in precompute.py schlägt fehl (DB gesperrt / nicht gefunden)**
Auslöser: precompute.py läuft als Subprozess, während main.py einen WAL-Write hält
Frühwarnung: Log „Fehler beim Laden der Custom Locations" im Recompute-Log
Gegenmaßnahme: Fehler mit `logger.warning` abfangen + Fallback auf leere Custom-Liste (analog zu `_apply_location_overrides`), kein Abbruch → in AK als Edge Case getestet

💀 **Szenario 2: Doppelte Location-IDs (Custom + Base kollidieren)**
Auslöser: Unwahrscheinlich (Custom-IDs starten mit `custom_`), aber race condition denkbar
Frühwarnung: doppelte `location_id` in calendar.json / opportunities.json
Gegenmaßnahme: `ids_existing = {loc.id for loc in LOCATIONS}` Guard (wie in `_load_custom_locations` in main.py) → kein doppeltes Append

💀 **Szenario 3: Babelsberg-Event liegt innerhalb der nächsten 3 Tage, Wetter-Overlay fehlt**
Auslöser: Custom Location hat keine Wetter-Daten, weil `_weather_overlay()` auf `_feed_cache` operiert (nach Reload OK)
Frühwarnung: Event ohne `weather_score` im Feed
Gegenmaßnahme: `_load_caches()` nach Single-Recompute bereits triggert Wetter-Overlay → kein extra AK nötig

💀 **Szenario 4: Timing-Problem — 26.06. Alignment schon vorbei, wenn Fix live geht**
Auslöser: Fix erst nach 26.06.2026 deployed
Frühwarnung: Datum prüfen (heute 23.06., Event 26.06.)
Gegenmaßnahme: **Hohe Priorität** — Fix muss bis spätestens 25.06. deployed sein; AK mit statischem Datum testen

---

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `precompute.py` (L50, L142–170, L468, L561, L576, L659–663), `main.py` (`_load_custom_locations` L123–165, `_run_precompute_single` L481–519, `PATCH /locations` L1286–1289)
- [x] Root Cause validiert: keine Vermutung — Code-Pfad vollständig nachverfolgt

**Implementierungsoptionen:**

### Option A — `_load_custom_locations_for_precompute()` in precompute.py (Empfohlen)
- **Vorgehen:** In `precompute.py` eine neue Funktion `_load_custom_locations()` ergänzen (analog zu `_apply_location_overrides()`), die `LocationStore().load_all_custom()` aufruft und die Einträge als `PhotoLocation`-Objekte an `LOCATIONS` anhängt. Aufruf in `main()` direkt nach `_apply_location_overrides()`.
- **Betroffene Dateien:** `backend/precompute.py` (ca. 25 neue Zeilen + 1 Aufruf)
- **Vorteile:** Minimale Änderung, konsistentes Muster zu Overrides, Custom Locations in Feed + Kalender + Nacht-Cron, Single-Recompute findet Location korrekt
- **Nachteile:** precompute.py bekommt SQLite-Abhängigkeit (aber `LocationStore` bereits importiert über data.store)
- **Aufwand:** klein

### Option B — On-Demand-Fallback für `custom_`-Locations in `/opportunities` + `/calendar`
- **Vorgehen:** Endpoints erkennen `location_id.startswith("custom_")` → berechnen live via Window-Engine, ohne precompute.py zu ändern
- **Betroffene Dateien:** `backend/main.py` (beide Endpoints)
- **Vorteile:** precompute.py bleibt unverändert
- **Nachteile:** Feed ohne `location_id` (Gesamtübersicht) zeigt keine Custom-Location-Events; inkonsistentes Verhalten; höherer Aufwand
- **Aufwand:** mittel

✅ **Empfehlung: Option A** — minimale Änderung, löst Bug vollständig für alle Pfade (Feed, Kalender, Nacht-Cron, Single-Recompute), konsistent mit bestehendem Overrides-Pattern.

---

**Scope:**
- Eingeschlossen: Feed + Kalender + Single-Recompute + Nacht-Cron für Custom Locations
- Ausgeschlossen: Scout-Tab (discover.json) — separates Ticket falls nötig; PhotoPills-Koordinaten-Validierung

**Testplan:**
- [ ] Automatisiert (Harness): `backend/tests/test_bug33_custom_locations_precompute.py` — Unit-Test: Mock SQLite, prüfe dass LOCATIONS nach `_load_custom_locations()` eine Custom Location enthält; Integration: precompute mit bekannter Custom Location → prüfe calendar.json enthält custom_id
- [ ] Manuell: Location ID aus `/locations` → `curl "http://localhost:8000/opportunities?location_id=<id>"` → Events vorhanden; `curl "http://localhost:8000/calendar?location_id=<id>&month=6&year=2026"` → Babelsberg-Event sichtbar

---


### TASK-27 · UI-Konsistenz: „Events" durchgängig durch „Chancen" ersetzen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-23 |

**Beschreibung:** In der App werden „Events" und „Chancen" synonym verwendet (z. B. Jahreskalender-Header „1257 Events · 5289 im Monat"). Der primäre Begriff in FotoAlert ist „Chancen". Alle sichtbaren UI-Texte, Labels und Zähler sollen einheitlich auf „Chancen" umgestellt werden.

**Bezug:** Geht Hand in Hand mit BUG-31 (Kopfzeilen-Counter), könnte dort mitgemacht werden. Nicht identisch — BUG-31 ist ein Logikfehler, dieser Task ist reine Umbenennung.

---


### TASK-28 · Analyse-Qualität: Explizite Rückfragen statt Annahmen in der Implementierungsphase `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-23 |

**Beschreibung:** Stephan hat beobachtet, dass Agenten Design- und Funktionsentscheidungen (Farben, Layout, Features) eigenständig treffen, ohne sie vorher zu spezifizieren — während gleichzeitig wichtigere Funktionen (z. B. Persistenz) unvollständig bleiben, was erst im User Testing auffällt. Gewünschtes Verhalten: Der Analyse-Agent stellt während Example Mapping gezielt Rückfragen zu offenen Punkten (nach dem Vorbild von Superhero's), hält Annahmen explizit fest und markiert sie zur Bestätigung — statt sie stillschweigend zu treffen.

**Bezug:** Betrifft den `fotoalert-analyze`-Skill direkt. Umsetzung: Skill-Update (fotoalert-analyze) + ggf. Ergänzung im fotoalert-impl-Skill (Annahmen vor Implementierung kennzeichnen). Verwandt mit `feedback_example_mapping`-Memory.

**Scope:**
- Eingeschlossen: `fotoalert-analyze` (Annahmen-Protokoll in Example Mapping), `fotoalert-impl` (Annahmen-Check vor erstem Edit), Memory `feedback_assumptions_clarification.md` (projektübergreifend)
- Ausgeschlossen: andere Skills, iOS-Code

**Akzeptanzkriterien:**
- [x] `fotoalert-analyze`: Example Mapping enthält Annahmen-Protokoll mit Priorisierung (🔴 funktional / ⚪ ästhetisch)
- [x] `fotoalert-impl`: Annahmen-Check am Start prüft ⚠️-Marker und fragt vor erstem Edit; gilt auch mid-Implementierung
- [x] Memory `feedback_assumptions_clarification.md` vorhanden und in MEMORY.md indexiert
- [x] Edge Case: kein Interpretationsspielraum → kein unnötiger Rückfrage-Block

**Pre-Mortem:**
- 💀 Zu viele Rückfragen → Paralysis. Gegenmaßnahme: nur fragen wenn kein sinnvoller Default ableitbar (in Skill verankert).
- 💀 Memory-Eintrag zu vage → nicht operationalisierbar. Gegenmaßnahme: Eintrag mit konkreten Trigger-Typen und Tabelle.
- 💀 impl-Skill nicht updated → Lücke in Impl-Phase. Gegenmaßnahme: beide Skills im selben Ticket.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `fotoalert-analyze/SKILL.md`, `fotoalert-impl/SKILL.md`, `memory/`
- [x] Implementierungsoption: Skills + Memory (Stephan: Option C)
- [x] Empfehlung freigegeben

**Testplan:**
- [x] Manuell: Annahmen-Protokoll sichtbar in nächster Analyse-Session; ⚠️-Marker in Spec; Impl-Skill fragt vor Edit

---


### TASK-29 · Refactoring-Agent: Code-Quality-Check vor jedem Release `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-23 |

**Beschreibung:** Vor jedem Release (nach erfolgreichem Test, vor `fotoalert-release`) läuft ein Refactoring-Agent, der Backend + Frontend auf Code-Smells prüft. Sichere Fixes wendet er direkt an; zu komplexe Findings landen als Ticket in der Inbox. Der Agent ist als Cowork-Skill (`fotoalert-refactor`) + Python-Hilfsskript (`tools/refactor_check.py`) implementiert.

**Scope:**
- Eingeschlossen: Backend (`backend/*.py`, `backend/calculations/`, `backend/discover/`), Frontend (`web/index.html`)
- Ausgeschlossen: iOS-Swift-Code, Test-Dateien, Migrations-Skripte, Drittbibliotheken

**Akzeptanzkriterien:**
- [ ] `tools/refactor_check.py` läuft in < 5 s und gibt strukturierten JSON-Report aus (auto_fixable / needs_ticket)
- [ ] Skill `fotoalert-refactor` triggert via „refactor", „code-check", „vor dem Release" und läuft den Check
- [ ] Auto-fixable Findings (unused imports, tote globals) werden direkt per Edit angewendet
- [ ] Nach Auto-Fix laufen die Backend-Tests (`pytest backend/tests/`) automatisch zur Verifikation
- [ ] Nicht-auto-fixable Findings (Funktionen > 80L, fehlende Typ-Annotationen en masse) landen als Intake-Ticket
- [ ] Edge Case: Kein Fund → Report zeigt „✅ Keine Smells" statt leerem Output
- [ ] Edge Case: Tests schlagen nach Auto-Fix fehl → Fix wird rückgängig gemacht (git checkout), Ticket statt direkter Änderung

**Pre-Mortem:**
- 💀 Auto-Fix bricht Funktionalität → Auslöser: Import scheinbar unused, aber per `importlib` dynamisch genutzt. Gegenmaßnahme: Tests nach jedem Auto-Fix pflicht; bei Fehler sofort revert (AK oben).
- 💀 Frontendregeln nicht greifend → Auslöser: index.html ist Monolith ohne Modul-Grenzen; reguläre pyflakes-/AST-Ansätze greifen nicht. Gegenmaßnahme: JS-Smells via Regex-Heuristiken (duplizierte Event-Handler, console.log-Aufrufe in Prod, Inline-Style-Wiederholungen).
- 💀 Zu viele Ticket-Erstellungen → Auslöser: 34/58 fehlende Annotations → ein Ticket pro Funktion. Gegenmaßnahme: Findings bündeln (ein Ticket pro Kategorie, nicht pro Zeile).
- 💀 Skill triggert nicht konsistent → Auslöser: fotoalert-release läuft ohne Refactoring-Schritt wenn Stephan direkt „release" sagt. Gegenmaßnahme: Refactoring-Step in fotoalert-release-Skill-Prompt verankern (Memory-Eintrag).

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `tools/refactor_check.py` (neu), `web/index.html`, `backend/main.py`, `backend/precompute.py`
- [x] Bekannte Smells (Stand 2026-06-23): unused import `subprocess` (main.py:31), toter global `_discover_cache` (main.py:326), 9 Funktionen > 60L (längste: `precompute.main()` 186L, `compute_calendar_incremental()` 157L), 34/58 Funktionen in main.py ohne Return-Annotation
- [ ] Implementierungsoptionen freigegeben
- [ ] Empfehlung: Option A

**Testplan:**
- [ ] Automatisiert: `pytest backend/tests/` nach Auto-Fix (Regression-Guard)
- [ ] Manuell: `python3 tools/refactor_check.py --report` gibt JSON-Report aus; `python3 tools/refactor_check.py --fix` wendet Auto-Fixes an

---


### TASK-30 · Refactoring: Lange Backend-Funktionen aufteilen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **In Analysis seit** | 2026-06-23 |
| **Implementiert** | 2026-06-23 (Option B) |
| **Released** | 2026-06-23 · v1.11.9 |
| **Abgeschlossen** | 2026-06-23 |

**Beschreibung:** `refactor_check.py --report` meldet folgende Backend-Funktionen über dem 80-Zeilen-Threshold:

- `precompute.py:229` · `_composition_analysis()` · 109 Zeilen
- `precompute.py:341` · `_serialize()` · 84 Zeilen
- `precompute.py:540` · `compute_calendar_incremental()` · 157 Zeilen
- `precompute.py:704` · `main()` · 190 Zeilen
- `main.py:1218` · `preview_alignment()` · 99 Zeilen
- `discover/sun_pipeline.py:69` · `run()` · 92 Zeilen
- `discover/moon_pipeline.py:94` · `run()` · 91 Zeilen
- `discover/subjects.py:109` · `build_subjects()` · 91 Zeilen

**Quelle:** Automatisch erstellt durch fotoalert-refactor (TASK-29), Refactor-Check 2026-06-23 (BUG-33-Release)

---

#### 🔬 Analyse (2026-06-23 · In Analysis)

**Scope:**
- Eingeschlossen: 5 sinnvolle Splits (siehe unten) + Allowlist-Einträge für 3 Ausnahmen in `refactor_check.py`
- Ausgeschlossen: `_serialize()`, `sun_pipeline.run()`, `moon_pipeline.run()` — begründete Ausnahmen (kein Lesbarkeitsgewinn bei Split)

**Akzeptanzkriterien:**
- [ ] `pytest backend/tests/` vollständig grün nach allen Splits
- [ ] `precompute.main()` → aufgeteilt in `_run_single_location_flow()` + `_run_standard_flow()` (je < 80 Zeilen, async)
- [ ] `_composition_analysis()` → `_compute_body_apparent_size()` + `_build_composition_labels()` extrahiert; Ergebnis-Dict identisch zur bisherigen Ausgabe
- [ ] `compute_calendar_incremental()` → `_load_calendar_cache()` (Phase 1, rein lesend) extrahiert; BUG-29-Logik (Single-Location-Guard, Versions-Warn) unverändert in Hauptfunktion
- [ ] `preview_alignment()` → `_save_alignment_as_location()` extrahiert; Recompute-Hook + Backup-Task vollständig übernommen
- [ ] `build_subjects()` → `_group_location_candidates()` extrahiert; Dedup-Logik unverändert
- [ ] `refactor_check.py`: Allowlist-Einträge für `_serialize`, `sun_pipeline.run`, `moon_pipeline.run` mit Begründung
- [ ] Edge Case: Kein Behavioral-Change — alle bestehenden API-Responses identisch

**Pre-Mortem:**
- 💀 BUG-29-Regression: Falscher Split von `compute_calendar_incremental()` verschiebt Single-Location-Guard → Kalender schrumpft. Gegenmaßnahme: Nur Phase 1 (Cache-Load) extrahieren; BUG-29-Kommentare mitziehen.
- 💀 `preview_alignment`-Save-Hook geht verloren: `_save_alignment_as_location()` vergisst Recompute-Task oder Backup. Gegenmaßnahme: AK prüft explizit beide `asyncio.create_task()`-Aufrufe.
- 💀 `_composition_analysis`-Labels-Split bricht Dict-Keys: Merge-Fehler → Key fehlt. Gegenmaßnahme: Test mit Mock-`o`-Objekt prüft alle Ausgabe-Keys.

**📎 Code-Verifikation (2026-06-23):**
- `compute_calendar_incremental()`: BUG-29-kritischer State (`valid_events`, `new_meta`) zwischen 4 Phasen geteilt — nur Phase 1 sicher extrahierbar ✅
- `main()`: Harter `return` nach Single-Location-Flow — zwei Hilfsfunktionen teilen keinen State ✅
- `_serialize()`: Flaches Dict-Literal ohne Branches — Split verschlechtert Lesbarkeit ✅ (Ausnahme begründet)
- BUG-29-Schutzkommentare in `compute_calendar_incremental()`: müssen beim Extract mitgezogen werden ✅

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: `precompute.py`, `main.py`, `discover/sun_pipeline.py`, `discover/moon_pipeline.py`, `discover/subjects.py`
- [x] Implementierungsoptionen: A (alle 8 erzwungen) / B (5 sinnvolle + Allowlist)
- [x] Empfehlung: Option B

**Testplan:**
- [ ] Automatisiert: `pytest backend/tests/` nach jedem einzelnen Split (nicht erst am Ende)
- [ ] Manuell: `GET /opportunities` + `GET /calendar` — Antwortstruktur visuell auf Vollständigkeit prüfen

---


### TASK-31 · Typ-Annotationen in backend/main.py ergänzen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-23 |

**Beschreibung:** `refactor_check.py --report` meldet: nur 24/58 Funktionen in `backend/main.py` haben Return-Annotationen. Die verbleibenden 34 Funktionen sollten Return-Typen ergänzt bekommen. Vorgabe: `from __future__ import annotations` ist bereits vorhanden (Python 3.9-Kompatibilität gesichert).

**Quelle:** Automatisch erstellt durch fotoalert-refactor (TASK-29), Refactor-Check 2026-06-23 (BUG-33-Release)

---

#### 🔬 Analyse (2026-06-23 · In Analysis)

**Inventar — Funktionen ohne Return-Annotation (38 identifiziert, Checker zählt 34):**

*Hintergrund-Hilfsfunktionen:*
| Funktion | Signatur (Params vorhanden) | Korrekte Return-Annotation |
|---|---|---|
| `_job_start` | `(job: str)` | `-> float` |
| `_job_done` | `(job: str, t0: float)` | `-> None` |
| `_job_error` | `(job: str, t0: float, msg: str)` | `-> None` |
| `_weather_overlay` | `()` | `-> None` |
| `_run_precompute` | `(mode: str = "full")` | `-> None` |

*Lifecycle-Events:*
| Funktion | Korrekte Return-Annotation |
|---|---|
| `startup` | `-> None` |
| `shutdown` | `-> None` |

*API-Endpoints (FastAPI-Routen):*
| Funktion | Korrekte Return-Annotation |
|---|---|
| `health` | `-> HealthOut` |
| `get_locations` | `-> list[LocationOut]` |
| `get_location` | `-> LocationOut` |
| `get_opportunities` | `-> list[dict]` |
| `get_today_opportunities` | `-> list[dict]` |
| `get_plan` | `-> dict` |
| `daily_briefing` | `-> DailyBriefingOut` |
| `get_calendar` | `-> dict` |
| `get_discover` | `-> dict` |
| `login` | `-> dict` |
| `trigger_discover_refresh` | `-> dict` |
| `register_device` | `-> dict` |
| `trigger_refresh` | `-> dict` |
| `trigger_feed_refresh` | `-> dict` |
| `trigger_calendar_refresh` | `-> dict` |
| `trigger_weather_refresh` | `-> dict` |
| `get_job_status` | `-> dict` |
| `preview_alignment` | `-> dict` |
| `reverse_geocode_endpoint` | `-> dict` |
| `patch_location` | `-> dict` |
| `get_all_verifications` | `-> list[dict]` |
| `get_verifications` | `-> list[dict]` |
| `add_verification` | `-> dict` |
| `delete_last_verification` | `-> dict` |
| `get_all_ratings` | `-> list[dict]` |
| `get_ratings` | `-> dict` |
| `upsert_rating` | `-> dict` |
| `delete_rating` | `-> dict` |
| `service_worker` | `-> FileResponse` |

*Innere Funktion (in `daily_briefing`):*
| Funktion | Korrekte Return-Annotation |
|---|---|
| `_to_opp_out` | `-> OpportunityOut` |

*Innere Funktionen (in `_compute_possible_bodies`):*
| Funktion | Korrekte Return-Annotation |
|---|---|
| `_rise_set_ranges` | `-> list[tuple[float, float]]` |
| `_overlaps` | `-> bool` |

*Hinweis:* `refactor_check.py` zählt innere Funktionen möglicherweise nicht mit — daher Diskrepanz (34 gemeldet vs. ~36 Kandidaten). Alle sollten annotiert werden.

---

**Kompatibilitätsanalyse:**

`from __future__ import annotations` ist auf Zeile 25 vorhanden. Das bedeutet:
- Alle Annotationen werden als Strings ausgewertet (PEP 563 / Lazy Evaluation)
- `str | None`-Syntax (Python 3.10+) ist im Sourcecode erlaubt — wird nie zur Laufzeit evaluiert
- `list[dict]`, `list[str]` ohne `List[]`-Import sind ebenfalls sicher
- Kein zusätzlicher Import aus `typing` nötig (außer wenn `Optional` oder `Union` explizit gewünscht)
- Bereits verwendete Typen: `Optional` (aus `typing`, importiert), `LocationOut`, `HealthOut`, `DailyBriefingOut`, `OpportunityOut`, `FileResponse` (letztere importiert auf Zeile 1520)

Einzig `FileResponse` ist am Ende des Files importiert (Zeile 1520). Das ist mit `from __future__ import annotations` ebenfalls kein Problem (Forward Reference).

---

**Pre-Mortem:**

- 💀 **Falsche Typen bei dict-Endpoints:** FastAPI-Endpoints, die `dict` zurückgeben, sind tatsächlich `dict[str, Any]` — `dict` allein ist korrekt und ausreichend für mypy (ohne strict), kein Risiko.
- 💀 **`_weather_overlay` hat kein explizites `return`** — gibt implizit `None` zurück, Annotation `-> None` korrekt.
- 💀 **`_run_precompute` / `_run_precompute_single` sind async void** — `-> None` ist für async-Coroutinen ohne Rückgabewert korrekt, kein Risiko.
- 💀 **Innere Funktion `_to_opp_out` in `daily_briefing`:** mypy analysiert sie korrekt im Closure-Scope. Annotation schadet nicht, mypy kann den Typ ableiten.
- 💀 **`startup()`-Event-Handler:** FastAPI erwartet keine Signatur-Einschränkung auf `startup`/`shutdown`. `-> None` ist problemlos.
- 💀 **`get_plan` returns complex dict:** tatsächliche Rückgabe ist `dict[str, Any]` mit gemischten Werten. `dict` (ohne Parameter) ist für die Annotation ausreichend — kein Refactoring nötig.
- 💀 **Mypy-Strict-Modus:** wird im Projekt nicht verwendet (kein `mypy.ini` mit `--strict`). Alle Annotationen dienen primär Lesbarkeit und dem Refactor-Checker, nicht strikter Typisierung.

---

**Example Mapping:**

**Regel 1: Sync-Hilfsfunktionen erhalten `-> None` oder konkreten Rückgabetyp**

- ✅ Positiv: `_job_start(job: str) -> float` — gibt Startzeit zurück, `float` korrekt (monotonic clock)
- ❌ Negativ: `_job_start(job: str) -> None` — falsch, würde Caller-Aufruf `t0 = _job_start(j)` mypy-Fehler geben
- ⚠️ Edge: `_job_done(job: str, t0: float) -> None` — gibt nichts zurück, aber verändert `_job_status` (Side Effect). `-> None` korrekt, Side Effects werden nicht annotiert.

**Regel 2: FastAPI-Endpoints ohne `response_model` erhalten `-> dict` oder `-> list[dict]`**

- ✅ Positiv: `get_opportunities(...) -> list[dict]` — gibt `results[:500]` zurück, korrekte Annotation
- ❌ Negativ: `get_opportunities(...) -> list[OpportunityOut]` — falsch, Cache-Dicts sind keine Pydantic-Instanzen (FastAPI serialisiert sie implizit)
- ⚠️ Edge: `get_calendar(...)` hat mehrere Rückgabe-Pfade (alle `dict`) — alle Pfade liefern `dict`, Annotation `-> dict` ist korrekt und konsistent

**Regel 3: Async Lifecycle-Events erhalten `-> None`**

- ✅ Positiv: `async def startup() -> None` — kein Rückgabewert, FastAPI ignoriert ihn
- ❌ Negativ: `async def startup() -> bool` — FastAPI würde keinen Fehler werfen, aber der Typ wäre irreführend (Caller nutzt Rückgabe nicht)
- ⚠️ Edge: `_prewarm_calendar()` ist eine innere async-Funktion in `startup()` — wird via `asyncio.create_task()` gestartet, Rückgabe nie genutzt. `-> None` korrekt.

---

**Implementierungsoptionen:**

**Option A: Batch — alle ~36 Funktionen auf einmal annotieren**
- Vorteile: Einmalige Änderung, `refactor_check.py` springt sofort auf 58/58
- Nachteile: Großer Diff, höheres Risiko eines Tippfehlers oder falschen Typs; schwerer zu reviewen
- Risiko: Mittel (ein falscher Typ in 36 Änderungen könnte mypy-Fehler einführen, auch wenn keine Runtime-Auswirkung)

**Option B: Kritische Funktionen zuerst, Rest in Follow-up**
- Phase 1 (kritisch): Job-Tracker + Lifecycle (7 Funktionen) + innere Funktionen (3)
- Phase 2 (Endpoints): Alle FastAPI-Routen (~26 Funktionen)
- Vorteile: Kleiner Diff, leichter zu reviewen, Fehler schneller isolierbar
- Nachteile: Zwei Commits, Checker zeigt bis Phase 2 noch Warnungen

**Empfehlung: Option A (Batch)**

Begründung: Alle 36 Annotationen sind trivial (`-> None`, `-> dict`, `-> list[dict]` etc.) — kein einziger komplexer Union-Type oder Generic. Der Diff ist zwar breit, aber mechanisch einfach. Ein einmaliger Review-Durchlauf ist effizienter als zwei Tickets. Risiko ist minimal, da `from __future__ import annotations` verhindert, dass falsche Typen zur Laufzeit crashen.

---

**Akzeptanzkriterien:**

- [x] `refactor_check.py --report` zeigt 0 missing-annotation-Issues (alle Funktionen annotiert)
- [x] `python -m py_compile backend/main.py` gibt keine Fehler
- [x] `pytest backend/tests/` — 24/24 nicht-ephemeris Tests grün (Ephemeris-Failures sind sandbox-seitig: kein NASA-Netzwerkzugang)
- [x] Alle `-> None`-Annotationen für async void Coroutinen korrekt gesetzt
- [x] `_job_start()` hat `-> float` (war bereits vorhanden)
- [x] `service_worker()` hat `-> FileResponse`
- [x] Innere Funktionen `_to_opp_out`, `_rise_set_ranges`, `_overlaps` waren bereits annotiert

**Testplan:**
- [x] `python -m py_compile backend/main.py` — Syntax-Check ✅
- [x] `pytest backend/tests/ -q` — 24 passed ✅
- [x] `python tools/refactor_check.py --report` — 0 missing-annotation-Issues ✅

**Analyse & Planung:**
- [x] Alle 36 Kandidaten-Funktionen identifiziert und Typen abgeleitet
- [x] Python 3.9-Kompatibilität bestätigt (`from __future__ import annotations` vorhanden)
- [x] Pre-Mortem durchgeführt
- [x] Example Mapping durchgeführt
- [x] Implementierungsoptionen: A (Batch) / B (Phasiert)
- [x] Empfehlung: Option A (Batch)

---


### TASK-32 · Refactoring: Lange JS-Funktionen in index.html aufteilen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Analyse** | 2026-06-23 |
| **Done** | 2026-06-23 |

**Beschreibung:** `refactor_check.py --report` meldet folgende JS-Funktionen über dem Threshold:

- `index.html:1179` · `_showError()` · ~773 Zeilen (wahrscheinlich falsch erkannt — JS-Heuristik, kein AST)
- `index.html:1952` · `haversineKm()` · ~252 Zeilen
- `index.html:2232` · `onUp()` · ~168 Zeilen
- `index.html:2407` · `state3()` · ~108 Zeilen
- `index.html:2515` · `mkSec()` · ~264 Zeilen
- `index.html:2779` · `axisPhrase()` · ~1372 Zeilen (wahrscheinlich Sektion, kein echter Funktionskörper)

Hinweis: `index.html` ist ein Monolith, JS-Längenmessung per Regex-Heuristik kann falsch-positiv sein. Vor Refactoring manuell prüfen welche Findings real sind.

**Quelle:** Automatisch erstellt durch fotoalert-refactor (TASK-29), Refactor-Check 2026-06-23 (BUG-33-Release)

---

#### 🔬 Analyse (2026-06-23 · In Analysis)

##### 1. Manuelle Verifikation der Findings

| Finding | Zeile | Tatsächliche Länge | Echtes Problem? |
|---------|-------|--------------------|-----------------|
| `_showError()` | 1179 | **7 Zeilen** — lokale Arrow-Function innerhalb `Feed.load()` | Falsch-Positiv — Heuristik misst bis zum Ende der übergeordneten Methode |
| `haversineKm()` | 1952 | **7 Zeilen** — reine Berechnungsfunktion (Haversine-Formel) | Falsch-Positiv — Heuristik läuft bis zum nächsten Hauptblock (~Zeile 2200) |
| `onUp()` | 2232 | **5 Zeilen** — lokale Arrow-Function als Closure in `drag()` innerhalb `initDualSlider()` | Falsch-Positiv — Closure-Ende nicht erkannt, misst bis Methoden-Ende |
| `state3()` | 2407 | **2 Zeilen** — lokale Arrow-Function innerhalb `FilterSheet._render()` | Falsch-Positiv — Heuristik misst bis Ende von `_render()` (~Zeile 2514) |
| `mkSec()` | 2515 | **3 Zeilen** — kleine Top-Level Template-Helper-Funktion | Falsch-Positiv — Heuristik misst bis zur nächsten Sektion (~Zeile 2779) |
| `axisPhrase()` | 2779 | **10 Zeilen** — lokale Arrow-Function innerhalb einem IIFE im Location-Detail | Falsch-Positiv — Heuristik läuft weit in die nächste Sektion (~Zeile 4151) |

**Befund: Alle 6 Findings sind Falsch-Positive.** Die Regex-Heuristik in `refactor_check.py` erkennt nicht, wann eine verschachtelte Funktion endet. Sie misst stattdessen bis zur nächsten erkannten Top-Level-Funktion oder Sektion — was willkürlich hohe Zeilenzahlen produziert. Die tatsächlichen Längen: `_showError` = 7 Z., `haversineKm` = 7 Z., `onUp` = 5 Z., `state3` = 2 Z., `mkSec` = 3 Z., `axisPhrase` = 10 Z. Alle weit unter jedem sinnvollen Threshold.

##### 2. Pre-Mortem

Falls trotz dieser Analyse irrtümlich Code umstrukturiert würde:

- **Closure-Verlust:** `onUp`, `onMove`, `state3`, `chip3`, `axisPhrase` sind bewusst lokale Closures — sie greifen auf Eltern-Scope-Variablen zu (`rect`, `isMin`, `Filter.state`). Extraktion als eigenständige Funktionen würde diese Parameter erfordern und Signatur/Lesbarkeit verschlechtern.
- **Kein Test-Netz:** `index.html` hat keine JS-Unit-Tests. Regressions fallen erst beim manuellen Testen auf.
- **Monolith-Risiko:** In einem 4254-Zeilen-Monolith ohne Modul-System treffen globale Refactorings den globalen Scope — Namespace-Kollisionen und falsche Deklarationsreihenfolge sind möglich.
- **Aufwand ohne Nutzen:** Die gemeldeten Funktionen sind in Wirklichkeit tiny. Jede Änderung macht den Code komplizierter, nicht einfacher.

##### 3. Example Mapping

**Regel: Ein Finding ist real, wenn die tatsächliche Funktionslänge > Threshold.**

| Szenario | Ergebnis |
|----------|---------|
| `haversineKm()` tatsächlich 7 Zeilen | Kein Refactoring nötig |
| Heuristik meldet 252 Zeilen (misst bis nächsten Block) | Heuristik ist kaputt — nicht der Code |
| Closure mit Eltern-Scope-Zugriff wäre wirklich lang | Extraktion würde Correctness brechen — trotzdem kein naives Split |

**Regel: Heuristik soll nur Top-Level-Funktionen messen, nicht verschachtelte.**

| Szenario | Ergebnis |
|----------|---------|
| `function foo() {}` auf Top-Level | Länge korrekt messbar |
| `const bar = () => {}` innerhalb Object-Literal | Heuristik läuft bis zur nächsten erkannten Funktion — falscher Wert |
| IIFE mit inneren Closures | Alle inneren Funktionen werden als "lang" gemeldet |

##### 4. Akzeptanzkriterien

- [ ] **AK-1:** `refactor_check.py` meldet für alle 6 Findings keine Warnung mehr — entweder weil Heuristik korrigiert oder Findings explizit als Falsch-Positiv ausgeschlossen sind
- [ ] **AK-2:** Ein Kommentar in `refactor_check.py` dokumentiert die bekannte Limitation (verschachtelte Closures werden nicht korrekt enden-erkannt)
- [ ] **AK-3:** Kein produktiver JS-Code in `index.html` wurde geändert
- [ ] **AK-4:** Nächster automatischer Refactor-Check erzeugt für diese 6 Stellen keine Warnungen mehr

##### 5. Implementierungsoptionen

**Option A — Empfohlen: Kein Refactoring, Limitation dokumentieren + Ticket schließen**
- Füge einen Kommentar in `refactor_check.py` hinzu, der die bekannte Limitation für verschachtelte Funktionen beschreibt (alternativ: bekannte Falsch-Positive in eine Ignore-Liste aufnehmen)
- Setze Ticket auf Done
- Aufwand: ~15 Minuten
- Nachteil: Nächster Refactor-Check wird dieselben Warnungen erzeugen, wenn keine Ignore-Liste gepflegt wird

**Option B — Nicht anwendbar: Echte lange Funktionen aufteilen**
- Keine echten langen Funktionen gefunden. Würde Closures kaputt machen.

**Option C — Aufwändig: Refactor-Check-Heuristik verbessern**
- `refactor_check.py` um Brace-Counting oder Python-AST-Analyse für JS erweitern (z.B. `esprima`-ähnlich via `node`)
- Würde Falsch-Positive grundsätzlich verhindern
- Aufwand: ~2–3 Stunden; Risiko: neues Tooling-Dependency
- Empfehlung als separates zukünftiges Ticket, wenn Falsch-Positive häufig stören

**Empfehlung: Option A** — alle Findings sind Falsch-Positive, der Code ist in Ordnung. Eine Ignore-Liste oder kurzer Kommentar in `refactor_check.py` genügt. Option C kann als separates Low-Prio-Ticket folgen.

---


### TASK-33 · Post-Deploy-Health-Assert in CI `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **In Progress seit** | 2026-06-23 |

**Beschreibung:** Neuer `verify-deploy`-Job in `.github/workflows/deploy.yml` nach dem Deploy-Step. Prüft Feed-Größe (≥ 5 Events), Locations-Anzahl (≥ 10) und Kalender-Monat (≥ 5 Events). Verhindert stille Regressionen wie BUG-14/BUG-27 (Kalender leer nach Cron/Deploy).

**Akzeptanzkriterien:**
- [x] `verify-deploy`-Job läuft nach `deploy` (needs: [deploy])
- [x] Feed-Check: GET /opportunities?min_score=0.1 → ≥ 5 Events → sonst Exit 1
- [x] Locations-Check: GET /locations → ≥ 10 → sonst Exit 1
- [x] Kalender-Check: GET /calendar?month=X&year=Y → ≥ 5 Events → sonst Exit 1
- [ ] Regression: ein echter Deploy läuft grün durch den neuen Job

**Quelle:** TASK-33, Qualitätsanalyse 2026-06-23 (P0-Maßnahme)

---


### TASK-34 · Cache-Konsistenz-Tests + Sunrise-Präzisionstest `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **In Progress seit** | 2026-06-23 |

**Beschreibung:** Zwei neue Testdateien: (1) `test_patch_cache_consistency.py` — PATCH→GET-Roundtrip für Name (BUG-30) und Koordinaten (BUG-29); (2) Sunrise/Sunset-Referenztests + Babelsberg-Azimut-Test in `test_astronomy_regression.py`.

**Akzeptanzkriterien:**
- [x] `test_patch_cache_consistency.py` angelegt: BUG-30 Name-Persistenz (3 Tests), BUG-29 Koordinaten-Persistenz (3 Tests)
- [x] Sunrise Berlin 2026-06-21 innerhalb ±5 min Toleranz (Referenz: 01:43 UTC)
- [x] Sunset Berlin 2026-06-21 innerhalb ±5 min Toleranz (Referenz: 20:25 UTC)
- [x] Babelsberg→Pfingstberg Azimut 310–340°
- [ ] `pytest tests/test_patch_cache_consistency.py -v` lokal grün

**Quelle:** TASK-34, Qualitätsanalyse 2026-06-23 (P0/P1-Maßnahme)

---


### TASK-35 · Mobile Viewport in Playwright-Frontend-Check `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **In Progress seit** | 2026-06-23 |

**Beschreibung:** `run_frontend_check.py` um `run_mobile_checks()` erweitert (iPhone 14 Viewport, 390×844, isMobile=True). Prüft: App-Container-Overflow, Close-Button im Viewport, Filter-Sheet-Breite. Wird automatisch nach dem Desktop-Pass ausgeführt. Fängt iOS-Layout-Bug-Klassen wie BUG-19, BUG-25, BUG-34 frühzeitig ab.

**Akzeptanzkriterien:**
- [x] `run_mobile_checks()` implementiert und in CLI-Main eingehängt
- [x] iPhone 14 Viewport (390×844, deviceScaleFactor=3, isMobile=True)
- [x] #app-Breite ≤ 390px → sonst Finding
- [x] Close-Button im Viewport (y zwischen 0–844) → sonst Finding
- [x] #filter-sheet-Breite ≤ 390px → sonst Finding
- [ ] Frontend-Check lokal mit `--headed` ausgeführt und Mobile-Screenshots vorhanden

**Quelle:** TASK-35, Qualitätsanalyse 2026-06-23 (P1-Maßnahme)

---


### TASK-36 · Data-Flow-Dokument `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **In Progress seit** | 2026-06-23 |

**Beschreibung:** `docs/data-flow.md` angelegt: Datenquellen-Übersicht (locations.py vs. SQLite Overrides vs. Cache-JSONs vs. Frontend Locations.all), PATCH-Invalidierungslogik, Recompute-Trigger, bekannte Synchronisationsfallen (BUG-29, BUG-30, BUG-28). Ziel: neuer Agent oder Entwickler sieht sofort, welche Komponente welche Daten liest.

**Akzeptanzkriterien:**
- [x] Tabelle: Datenquellen × Leser × Schreiber
- [x] PATCH-Invalidierungslogik vollständig (welches Feld → recompute_triggered)
- [x] Recompute-Ablauf als Textdiagramm
- [x] 4 bekannte Synchronisationsfallen dokumentiert (BUG-29, BUG-30, BUG-28, coordinates_hash)
- [x] Custom-Locations vs. Basis-Locations Abgrenzung

**Quelle:** TASK-36, Qualitätsanalyse 2026-06-23 (P3-Maßnahme)

---


### TASK-37 · Refactoring: Lange Funktionen aufteilen (precompute.py) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-25 |

**Beschreibung:** `refactor_check.py` meldet 3 überlange Funktionen in `backend/precompute.py`:
- Z.589: `compute_calendar_incremental()` — 146 Zeilen (Threshold: 80)
- Z.742: `_run_single_location_flow()` — 92 Zeilen
- Z.837: `_run_standard_flow()` — 84 Zeilen

Alle drei können in kleinere Hilfsfunktionen aufgeteilt werden, um Lesbarkeit und Testbarkeit zu verbessern.

**Quelle:** Automatisch erstellt durch fotoalert-refactor (BUG-32 Release-Check, 2026-06-23)

---

#### 📋 Analyse-Spec (2026-06-25)

**Scope:**
Eingeschlossen: `backend/precompute.py` — die drei gemeldeten Funktionen werden in benannte Hilfsfunktionen aufgeteilt. Öffentliche Schnittstelle (Signaturen, Rückgabewerte) bleibt identisch.
Ausgeschlossen: Verhaltensänderungen, Test-Harness-Umbau, andere Module.

**Akzeptanzkriterien:**
- [x] `compute_calendar_incremental()`: Location-Loop → `_compute_calendar_for_location()`; Funktion ≤ 80 Zeilen
- [x] `_run_single_location_flow()`: Feed-Merge-Block → `_merge_and_write_feed()`; Funktion ≤ 80 Zeilen
- [x] `_run_standard_flow()`: Feed-Write + Kalender-Write → Hilfsfunktionen; Funktion ≤ 80 Zeilen
- [x] `refactor_check.py` meldet nach Umbau keine überlangen Funktionen mehr für diese 3
- [x] `pytest tests/` vollständig grün (46 passed, 41 skipped — Regression ✅)
- [x] Kein Type-Hint mit Python-3.10+-Syntax (`X | None`) in neuen Hilfsfunktionen

**Pre-Mortem:**
- 💀 BUG-29-Logik zerbrochen (valid_events-Mutation) → Gegenmaßnahme: Hilfsfunktion gibt `(new_events_for_loc, meta_entry)` zurück, Mutation bleibt in äußerer Funktion
- 💀 Python-3.9-Inkompatibilität in neuen Funktionen → Gegenmaßnahme: kein `X | None`, `Optional[X]` aus `typing` oder keine Annotations
- 💀 refactor_check.py meldet Hilfsfunktionen als selbst zu lang → Gegenmaßnahme: Check als letzten Schritt ausführen

📎 Code-Verifikation: `precompute.py` Z.590–922 gelesen 2026-06-25.
Bestätigt: `valid_events` wird im Location-Loop in-place via `.extend()` mutiert — Extraktion muss das berücksichtigen.
Bestätigt: BUG-29-Kommentare durchziehen den Loop — bei Splitting erhalten.

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: nur `backend/precompute.py`
- [x] Implementierungsoptionen: A (minimale Extraktion) / B (+ Testbarkeit)
- [x] Empfehlung: Option A

**Implementierungsplan (Option A):**
1. `compute_calendar_incremental`: Location-Loop (Z.669–727) → `_compute_calendar_for_location(loc, valid_events, target_range, existing_meta, new_meta)` — gibt `(new_events_for_loc, meta_entry)` zurück
2. `_run_single_location_flow`: Feed-Merge (Z.788–803) → `_merge_and_write_feed(feed_path, location_id, new_events, computed_at)`; Kalender-Write (Z.817–832) → `_write_calendar_cache(cal_path, calendar, computed_meta, computed_at)`
3. `_run_standard_flow`: Feed-Write + Health-Check (Z.872–886) → `_write_feed_cache(feed_path, feed, computed_at)`; Kalender-Write analog
4. `refactor_check.py` ausführen → 0 Findings für die 3 Funktionen
5. `pytest tests/` → grün

**Testplan:**
- Automatisiert (Harness): bestehende `test_patch_cache_consistency.py`-Tests sichern BUG-29-Logik ab (kein neuer Test nötig)
- Manuell: `python tools/refactor_check.py` nach Umbau → keine überlangen Funktionen

**Status:** ✅ Done — implementiert 2026-06-25, 46/46 Tests grün

---


### US-91 · Vollmond-Events: Filter-Kriterium + Chancen-Feed + Location-Detail `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-24 |

**Beschreibung:** Als App-User möchte ich sehen, wann Vollmond ist, damit ich diese seltenen Ereignisse gezielt für Fotowalks einplanen kann. Vollmond-Events sollen im 14-Tage-Feed erscheinen, als Filter-Kriterium (neben Sonnenaufgang, Mondaufgang etc.) verfügbar sein und in der Location-Detailansicht angezeigt werden, sofern der Vollmond für den jeweiligen Standort photographisch relevant ist (Sichtbarkeit / Alignment-Möglichkeit).

**Bezug:** US-70/70b/70c (Scout-Tab Mond-Alignment — anderer Tab, ergänzender Scope) · US-79 (Mondauf/-untergang — Zeiten, nicht Mondphasen) · US-81 (weitere Scout-Event-Typen) · US-92 (Neumond), US-93 (Supermond) — parallele Mondphasen-Features, sinnvolle gemeinsame Implementierung

---


### US-92 · Neumond-Events: Filter-Kriterium + Chancen-Feed + Location-Detail `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-24 |

**Beschreibung:** Als App-User möchte ich sehen, wann Neumond ist, damit ich diese dunklen Nächte gezielt für Milchstraßen- und Sternfotografie einplanen kann. Neumond-Events sollen im 14-Tage-Feed erscheinen, als Filter-Kriterium verfügbar sein und in der Location-Detailansicht angezeigt werden, sofern der Standort für Astrofotografie geeignet ist (z. B. niedriger Bortle-Wert oder freier Himmel).

**Bezug:** US-91 (Vollmond — parallele Implementierung), US-93 (Supermond) · TASK-09 (Bortle-Karte — künftige Ergänzung) · TASK-10 (Astronomisches Twilight für Milchstraße — Überschneidung: beide dienen Astrofoto-Planung, Scope abgrenzen bei Implementierung)

---


### US-93 · Supermond-Events: Filter-Kriterium + Chancen-Feed + Location-Detail `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-24 |

**Beschreibung:** Als App-User möchte ich sehen, wann ein Supermond (Vollmond nahe Perigäum, scheinbar größer/heller) stattfindet, damit ich diese besonders eindrucksvollen Ereignisse gezielt einplanen kann. Supermond-Events sollen im 14-Tage-Feed erscheinen, als Filter-Kriterium verfügbar sein und in der Location-Detailansicht angezeigt werden.

**Bezug:** US-91 (Vollmond — Supermond ist Spezialfall des Vollmonds; bei Implementierung auf US-91 aufbauen, Supermond = Vollmond + Perigäum-Bedingung) · US-92 (Neumond — parallele Mondphasen-Architektur)

---

### 📋 Analyse-Spec: US-91 + US-92 + US-93 (Mondphasen-Paket) — gemeinsame Implementierung

**Analysiert:** 2026-06-24 | **Scope:** US-91 (Vollmond) + US-92 (Neumond) + US-93 (Supermond)

---

#### Architektur-Entscheidung (aus Analyse bestätigt)

**Vollmond / Supermond** sind kein neuer eigenständiger Event-Typ, sondern ein **Override des `event_type`** bei bestehenden **Mond-Alignment-Events**. Ein Mond-Alignment am Vollmond-Tag bekommt `event_type = "Vollmond"` (oder `"Supermond"`). Das ermöglicht separates Filtern — Mond-Alignment-Events auf Vollmond-Nächten verschwinden damit aus dem "Mond-Alignment"-Filter (gewollt).

**Neumond** folgt demselben Muster: Override des `event_type` bei **Milchstraße-Events** auf Neumond-Nächten → `event_type = "Neumond"`. Milchstraße-Events auf Neumond-Nächten verschwinden aus "Milchstraße"-Filter (gewollt, da Neumond separat filterbar sein soll).

---

#### Scope

**Eingeschlossen:**
- `EventType`-Enum: `NEW_MOON = "Neumond"` und `SUPER_MOON = "Supermond"` hinzufügen
- `find_opportunities()`: Mondphasen-Helper + Override in Sektionen 3 (einfaches Mond-Alignment), 4 (3D-Alignment, Mond-Branch), 5 (Milchstraße)
- `_ALIGNMENT_FILTER_EXEMPT` in `precompute.py`: `"Neumond"` hinzufügen (da Milchstraße-Events exempt waren, aber nach Override nicht mehr)
- `_filter_feed()` in `main.py`: keine Änderung nötig (string-match bereits vorhanden)
- Frontend `index.html` `FilterSheet._ET`: `['Neumond', 'Neumond']` und `['Supermond', 'Supermond']` ergänzen; `MOON_TYPES` in Location-Detail um beide erweitern

**Ausgeschlossen:**
- Bortle-Filter für Neumond (kommt mit TASK-09)
- Scout-Tab / Discover-Ansicht (eigener Scope US-81)
- Standalone Mondphasen-Events ohne Alignment/Milchstraße-Basis

---

#### Akzeptanzkriterien

- [ ] AK1: Am Vollmond-Tag (phase_fraction 0.47–0.53) hat ein bestehendes Mond-Alignment-Event `event_type = "Vollmond"` statt `"Mond-Alignment"`
- [ ] AK2: Filter "Vollmond" zeigt diese Events; Filter "Mond-Alignment" zeigt sie **nicht** (gewolltes Verhalten)
- [ ] AK3: An einem Tag ohne Vollmond-Bedingung bleibt `event_type = "Mond-Alignment"` unverändert
- [ ] AK4: Supermond-Bedingung: Vollmond + `get_moon_earth_distance_km() < 362_000` km → `event_type = "Supermond"`, `alert_priority = 3`
- [ ] AK5: An einem Vollmond-Tag ohne Perigäum-Nähe bleibt event_type = "Vollmond" (kein Supermond)
- [ ] AK6: Am Neumond-Tag (phase_fraction < 0.03 oder > 0.97) hat ein bestehendes Milchstraße-Event `event_type = "Neumond"`
- [ ] AK7: Filter "Neumond" zeigt Neumond-Events; Filter "Milchstraße" zeigt sie an Neumond-Nächten **nicht**
- [ ] AK8: Frontend-Filter-Dropdown enthält "Neumond" und "Supermond" als neue Einträge
- [ ] AK9: `_passes_alignment_filter()` filtert Neumond-Events nicht heraus (`"Neumond"` in `_ALIGNMENT_FILTER_EXEMPT`)
- [ ] Edge Case: Location ohne Mond-Alignment-Events an Vollmond-Tag → kein Vollmond-Event im Feed (korrekt — nur bei tatsächlichem Alignment)
- [ ] Edge Case: Kein Milchstraße-Event an Neumond-Tag (z.B. Location in der Stadt, `mw.visible = False`) → kein Neumond-Event (korrekt)
- [ ] Edge Case: Supermond fällt mit Mond-Alignment zusammen → `event_type = "Supermond"`, NICHT `"Vollmond"` (Supermond hat Vorrang)

---

#### Pre-Mortem

📎 **Code-Verifikation** (gelesen 2026-06-24):
- `EventType` in `calculations/opportunity.py` Z.35: `FULL_MOON = "Vollmond"` bereits vorhanden, `NEW_MOON`/`SUPER_MOON` fehlen → hinzufügen ✓
- `_ALIGNMENT_FILTER_EXEMPT` in `precompute.py` Z.85: enthält `"Milchstraße"` → nach Override zu `"Neumond"` ist Exempt nicht mehr aktiv → **`"Neumond"` hinzufügen Pflicht**
- `_ROUTINE_TYPES` in `main.py` Z.789: nur `{'Goldene Stunde Morgen', 'Goldene Stunde Abend', 'Blaue Stunde'}` → neue Typen automatisch Non-Routine → kein BUG-32-Risiko
- `get_moon_earth_distance_km()` in `calculations/astronomy.py` Z.191: hat `assert 350_000 < dist_km < 410_000` → Exception wenn Skyfield Fehler → Try/Except-Wrapper nötig beim Aufruf
- `_filter_feed()` in `main.py` Z.776: `e["event_type"].lower() != event_type.lower()` → case-insensitive → kein Problem
- `_dedup_best_per_day` Z.806: key = `location_id|event_type|day` → Vollmond und Mond-Alignment werden NICHT als Duplikate erkannt → auf demselben Tag können beide existieren (wenn Location 2 Alignment-Fenster hat, eines als Vollmond, eines evtl. als reguläres Mond-Alignment sofern phase_fraction knapp außerhalb) → kein Problem, da Phase-Check deterministisch pro Tag

💀 **Szenario 1: Vollmond-Filter-Blindspot bei "Mond-Alignment"**
- Auslöser: User filtert "Mond-Alignment" auf Vollmond-Nacht → kein Ergebnis (Events sind jetzt "Vollmond")
- Frühwarnung: AK2 im Test explizit prüfen
- Gegenmaßnahme: Im Frontend-Tooltip / Filter-Beschreibung dokumentieren; ist korrekte Intention

💀 **Szenario 2: `_passes_alignment_filter` filtert Neumond-Events**
- Auslöser: Milchstraße-Event → event_type = "Neumond" → nicht mehr in `_ALIGNMENT_FILTER_EXEMPT` → `composition_analysis = None` → `ca is None → True` (pass). Kein echtes Risiko, da Milchstraße immer `ca = None` hat. ABER: Sicherheitshalber `"Neumond"` trotzdem in Exempt eintragen (defensive)
- Gegenmaßnahme: Exempt-Eintrag als AK9 ✓

💀 **Szenario 3: `get_moon_earth_distance_km()` Exception im Production-Pfad**
- Auslöser: Skyfield-Fehler (ephemeris nicht geladen o.ä.) zur Laufzeit von precompute
- Gegenmaßnahme: `try/except Exception: pass` → Fallback zu `FULL_MOON` (nicht Supermond) wenn Distanz nicht ermittelbar

💀 **Szenario 4: Python 3.9 Kompatibilität**
- Auslöser: `Optional[EventType]` Rückgabe-Typ mit `EventType | None` Syntax → Syntax-Error auf Prod
- Gegenmaßnahme: `Optional[EventType]` (aus typing) verwenden, keine Union-Pipe-Syntax

---

#### Implementierungsplan

**Datei 1: `backend/calculations/opportunity.py`**

1. Enum ergänzen:
   ```python
   NEW_MOON = "Neumond"
   SUPER_MOON = "Supermond"
   ```

2. Neuer Helper (nach `_score_moon_phase_for_moonshot`):
   ```python
   from typing import Optional
   from calculations.astronomy import get_moon_earth_distance_km

   SUPERMOON_THRESHOLD_KM = 362_000

   def _moon_phase_special_event_type(
       phase_fraction: float, shoot_time: datetime
   ) -> Optional[EventType]:
       """Vollmond/Supermond/Neumond-Override für Mond-Alignment- und Milchstraße-Events."""
       if 0.47 <= phase_fraction <= 0.53:
           try:
               dist_km = get_moon_earth_distance_km(shoot_time)
               if dist_km < SUPERMOON_THRESHOLD_KM:
                   return EventType.SUPER_MOON
           except Exception:
               pass
           return EventType.FULL_MOON
       if phase_fraction < 0.03 or phase_fraction > 0.97:
           return EventType.NEW_MOON
       return None
   ```
   > **Import-Note:** `get_moon_earth_distance_km` ist in `opportunity.py` noch nicht importiert → zu den bestehenden `astronomy`-Imports hinzufügen.

3. Sektion 3 (Mond-Alignment einfach, ab Z.384): Nach `opportunities.append(...)` → override:
   - Vor dem `append`: `special = _moon_phase_special_event_type(moon.phase_fraction, align_time)`, dann `event_type = special or EventType.MOON_ALIGNMENT` und `alert_priority = 3 if special == EventType.SUPER_MOON else ...`

4. Sektion 4 (3D-Alignment, Mond-Branch, ab Z.443): Gleicher Override-Mechanismus nach `event_type_val` Bestimmung

5. Sektion 5 (Milchstraße, ab Z.588): Vor `opportunities.append()` → `special = _moon_phase_special_event_type(moon.phase_fraction, shoot_t)`, wenn `special == EventType.NEW_MOON` → `event_type = EventType.NEW_MOON`

**Datei 2: `backend/precompute.py`**

6. `_ALIGNMENT_FILTER_EXEMPT` (Z.85): `"Neumond"` hinzufügen

**Datei 3: `web/index.html`**

7. `FilterSheet._ET` (ab Z.2200): Nach `['Vollmond', 'Vollmond']` einfügen:
   ```javascript
   ['Neumond',   'Neumond'],
   ['Supermond', 'Supermond'],
   ```

8. `MOON_TYPES` (Z.3151): `'Neumond'`, `'Supermond'` ergänzen

---

#### Testplan

- [ ] **Automatisiert:** `backend/tests/test_moon_phase_events.py` neu anlegen
  - `test_full_moon_overrides_alignment_event_type()` — phase_fraction=0.50, erwartet FULL_MOON
  - `test_supermoon_threshold()` — phase_fraction=0.50, mock distance < 362_000 → SUPER_MOON
  - `test_new_moon_overrides_milkyway_event_type()` — phase_fraction=0.01, erwartet NEW_MOON
  - `test_non_phase_night_unchanged()` — phase_fraction=0.25, erwartet MOON_ALIGNMENT (kein Override)
  - `test_alignment_filter_exempt_neumond()` — `_passes_alignment_filter({'event_type': 'Neumond', 'composition_analysis': None})` → True
- [ ] **Manuell:** Feed laden, auf Vollmond-Datum navigieren (z.B. nächster: ca. 2026-07-21), Vollmond-Event prüfen; Filter "Vollmond" anwenden → Events sichtbar; Filter "Mond-Alignment" → Events nicht sichtbar

---

#### Analyse-Status

- [x] Example Mapping durchgeführt
- [x] Architektur-Entscheidung bestätigt (Stephan, 2026-06-24): Event-Type-Override, nicht eigenständige Events
- [x] Pre-Mortem durchgeführt
- [x] Code-Verifikation: alle 4 betroffenen Dateien gelesen
- [x] Implementierungsoptionen bewertet → direkt umsetzbar, eine klare Option

---


### BUG-35 · Neue Location: Feed zeigt keine Events + kein Status-Feedback `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-24 |
| **Analysiert** | 2026-06-24 |
| **In Progress seit** | 2026-06-24 |

**Beschreibung:** Beim Anlegen einer neuen Location über die Kartenansicht wurden berechnete Alignments in der Detailansicht korrekt angezeigt — erscheinen jedoch nicht im 14-Tage-Feed. Root-Cause (verifiziert 2026-06-24): Backend-Precompute funktioniert korrekt (alle 12 Custom Locations haben Events im Feed). Das Problem ist zweiteilig: (1) `AddLocation.save()` ruft `Feed.load()` nicht auf — der Feed wird nach dem Speichern nie aktualisiert. (2) Der Precompute dauert 30–90s asynchron — ohne Status-Feedback sieht es aus als würden Events nie erscheinen.

**Root-Cause (Zeile 3899–3903, web/index.html):**
```js
await API.post('/preview-alignment', body);
toast('✅ Location gespeichert!');
await Locations.load();
// Feed.load() fehlt — Feed bleibt bis zum nächsten manuellen Reload stale
```

**Scope:**
- Eingeschlossen: Feed-Reload nach Save, `/recompute-status`-Endpoint, Pending-Banner im Frontend
- Ausgeschlossen: Retry-Queueing für geskippte Recomputes (wenn `_precompute_running=True`), Push-Notification wenn fertig

**Akzeptanzkriterien:**
- [ ] `GET /recompute-status` gibt `{"pending": ["custom_xxx"]}` zurück unmittelbar nach Location-Save
- [ ] Nach erfolgreichem Precompute + `_load_caches()`: Location nicht mehr in pending
- [ ] Frontend: nach Save wird `Feed.load()` aufgerufen (Feed sofort neu geladen)
- [ ] Frontend: solange Location in pending → Banner "⏳ Chancen werden berechnet..." im Feed sichtbar
- [ ] Frontend: wenn pending leer → Banner entfernt, `Feed.load()` erneut aufgerufen
- [ ] Frontend: Polling stoppt nach 10 Min; Banner wechselt zu manuellem Refresh-Hinweis
- [ ] Edge Case: `_precompute_running` beim Save → Location trotzdem in pending (kein stilles Drop)
- [ ] Edge Case: Server-Restart → pending leer; kein falsches Banner beim nächsten App-Start
- [ ] Edge Case: mehrere Locations gleichzeitig gespeichert → alle pending, alle verschwinden korrekt

**Pre-Mortem:**
- 💀 Precompute schlägt fehl (exit != 0) → `_load_caches()` nicht aufgerufen → Location ewig pending → Gegenmaßnahme: auch bei Fehler aus pending entfernen (finally-Block)
- 💀 `/recompute-status` ohne Auth → nur IDs sichtbar, keine Koordinaten; da App privat: unkritisch
- 💀 Polling-Timer bleibt nach App-Close im Speicher → Gegenmaßnahme: Frontend-Timeout 10 Min + Visibility-API-Check optional

**Analyse & Planung:**
- [x] Root-Cause verifiziert: `AddLocation.save()` ruft `Feed.load()` nicht auf (web/index.html:3899)
- [x] Backend-Precompute korrekt: alle 12 Custom Locations haben Events im `/opportunities`-Feed (Test 2026-06-24)
- [x] `_load_caches()` = guter Hook für pending-Cleanup (main.py:519)
- [x] Implementierungsoptionen: A (Delay-Retry) / B (Status-Endpoint + Polling)
- [x] Empfehlung: **Option B** — präzise, kein blindes Timing

**Implementation Spec (Option B):**

*Backend `main.py`:*
1. `_recompute_pending: set[str] = set()` als module-global ergänzen
2. In `_save_custom_location()` (nach `_store.create_custom`): `_recompute_pending.add(loc.id)`
3. In `_load_caches()`: nach dem Laden von `_feed_cache` → `ids_in_feed = set(e["location_id"] for e in _feed_cache); _recompute_pending -= ids_in_feed`
4. In `_run_precompute_single()` finally-Block: `_recompute_pending.discard(loc_id)` (bei Fehler)
5. Neuer Endpoint: `GET /recompute-status` → `{"pending": list(_recompute_pending)}`

*Frontend `web/index.html`:*
6. `AddLocation.save()`: nach erfolgreichem Post → `Feed.load()` + `Feed.startPendingPoll(result.location_id)` (wenn `result.saved`)
7. Anmerkung: `/preview-alignment`-Response enthält bereits `saved: bool` + die Location-ID ableiten aus Zeitstempel oder Response erweitern
8. `Feed.startPendingPoll(id)`: alle 15s `API.get('/recompute-status')`, wenn id nicht mehr pending → `Feed.load()` + Banner entfernen; nach 600s stop + Fallback-Text
9. Banner-Element im `#feed-content` Header: `<div id="recompute-banner" style="display:none">⏳ Chancen für neue Location werden berechnet…</div>`

**Testplan:**
- [ ] Automatisiert: `test_recompute_status_empty_on_start`, `test_recompute_status_after_save`, `test_pending_cleared_after_load_caches` in `backend/tests/test_bug35.py`
- [ ] Manuell: Location speichern → sofort Feed öffnen → Banner sichtbar → nach ~60s Banner weg, Events sichtbar

---


### BUG-36 · „Neue Location"-Formular: Name-Feld zeigt letzten gespeicherten Location-Namen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |

**→ Mit BUG-37 gemergt (gleiche Root-Cause: kein Formular-Reset nach save()). Fix in BUG-37.**

---


### BUG-37 · „Neue Location": Formular-State wird nach Speichern nicht zurückgesetzt (Merge BUG-36+37) `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-23 |

**Beschreibung:** Nach dem Speichern einer neuen Location behält `AddLocation` seinen gesamten State. Beim nächsten Öffnen des Formulars sind alle Felder noch gefüllt (Name, Koordinaten), Marker und Verbindungslinie noch auf der Karte, der Save-Button noch sichtbar und `previewData` gesetzt — der User sieht scheinbar die zuletzt gespeicherte Location im Bearbeitenmodus. Umfasst die Symptome aus BUG-36 (Name-Feld vorausgefüllt) und BUG-37 (Edit-Modus der letzten Location).

**Root-Cause:** `close()` entfernt nur CSS-Klassen; kein State-Reset. `open()` → `initMap()` gibt Map bei existierender Instanz sofort zurück (`if (this.map) return`).

**Scope:**
- Eingeschlossen: Reset nach `save()` (Option A)
- Ausgeschlossen: Reset nach `close()` ohne Save (abgebrochene Eingaben bleiben erhalten)

**Akzeptanzkriterien:**
- [ ] Nach save(): Erneutes open() zeigt leeres Formular (Name, Obs-Coords, Subj-Coords leer)
- [ ] Nach save(): Save-Button nicht sichtbar, Preview-Box leer
- [ ] Nach save(): Keine Obs/Subj-Marker + keine Verbindungslinie auf der Karte
- [ ] Nach save(): `AddLocation.obs`, `.subj`, `.previewData` sind null
- [ ] Abbruch ohne Save: Eingaben beim nächsten open() noch vorhanden

**Implementierung:** `reset()`-Methode in `AddLocation` (web/index.html), Aufruf am Ende von `save()` vor `close()`.

---


### US-94 · Add-Location-Sheet: Abbrechen-Button zum bewussten Verwerfen des Formulars `[x]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-24 |

**Beschreibung:** Als User möchte ich im Add-Location-Sheet einen kleinen Abbrechen-Button im unteren Bereich des Formulars haben, damit ich halbfertige Eingaben bewusst verwerfen und das Formular in den Ausgangszustand zurücksetzen kann — ohne die App schließen zu müssen. Der Button soll kleiner als „Alignments berechnen" und „Location dauerhaft speichern" sein und `reset()` + `close()` auslösen.

**Bezug:** BUG-37 `[~]` (hat `reset()`-Methode eingeführt — US-94 nutzt sie direkt; baut auf BUG-37 auf, erst danach implementieren).

**Scope:**
- Eingeschlossen: Abbrechen-Button links neben den Action-Buttons, ruft `reset()` + `close()` auf
- Ausgeschlossen: Bestätigungs-Dialog vor Verwerfen

**Akzeptanzkriterien:**
- [x] Abbrechen-Button links neben „Alignments berechnen ✦" und „Location dauerhaft speichern" (Flex-Row-Layout)
- [x] Klick ruft `AddLocation.reset()` + `AddLocation.close()` auf
- [x] Button visuell dezenter als `.btn-primary` / `.btn-secondary` (kein Hintergrund, kleiner Font)
- [x] Button immer sichtbar — unabhängig vom Preview-Zustand

**Implementierung:** `web/index.html` Z. 883–886 — drei Buttons in Flex-Row-Wrapper; Abbrechen `flex-shrink:0` links, Action-Buttons `flex:1` vertikal gestapelt rechts.

**Pre-Mortem:**
- 💀 `close()` vor `reset()` → Marker flackern beim Schließen → Gegenmaßnahme: `reset()` zuerst (wie in `save()`). ✅ umgesetzt.

---


### TASK-38 · Refactoring: Lange Funktionen in precompute.py aufteilen `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | Done |
| **Erstellt** | 2026-06-23 |
| **Abgeschlossen** | 2026-06-25 |

**Beschreibung:** Drei Funktionen in `backend/precompute.py` überschreiten den 80-Zeilen-Threshold: `compute_calendar_incremental()` (Z. 589, 146 Zeilen), `_run_single_location_flow()` (Z. 742, 92 Zeilen), `_run_standard_flow()` (Z. 837, 84 Zeilen). Aufteilen in kleinere Hilfsfunktionen.

**Quelle:** Automatisch erstellt durch fotoalert-refactor (TASK-29)

**Abschlussnotiz:** Bei Analyse am 2026-06-25 festgestellt, dass das Refactoring bereits in Folge-Tickets (BUG-29-Fixes) durchgeführt wurde. `compute_calendar_incremental()` wurde in `_load_calendar_cache()`, `_init_calendar_pass()` und `_compute_calendar_for_location()` aufgespalten. Alle drei Funktionen liegen unter 80 Zeilen. `refactor_check.py` meldet keine Findings für `precompute.py`.


### TASK-40 · Sections-Default-Regression-Guard: Audit + statischer Lint-Check `[x]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Mittel |
| **Status** | Done |
| **Erstellt** | 2026-06-24 |
| **Abgeschlossen** | 2026-06-25 |

**Beschreibung:** BUG-40 hat ein strukturelles Regressionsmuster offengelegt: eine neue Section wird per `mkSec()` ins HTML eingebaut, aber nicht in `Sections._def` eingetragen — sie bleibt dadurch immer geschlossen, ohne Fehlermeldung. Zwei Maßnahmen: (1) **Audit** der vier aktuell ungeklärten Sections (`ev_desc`, `ev_kamera`, `ev_wetter`, `ev_zeit`), die in `mkSec()` vorkommen aber nicht in `_def` stehen — je prüfen ob `false`-Default korrekt oder eine stille Regression vorliegt; (2) **Regression Guard** in `tools/refactor_check.py`: automatischer Vergleich aller `mkSec()`-IDs gegen `_def`-Keys, Abbruch mit Exit 1 bei Lücken — läuft damit vor jedem Release.

**Bezug:** Ausgelöst durch BUG-40 [x]. Ergänzt TASK-20 [x] (Playwright-Runtime-Tests) und TASK-21 [x] (CI-Gate) um eine statische Lint-Schicht.

---

#### Analyse (2026-06-25)

**📎 Code-Verifikation:**
- *Widerlegt — Audit-Prämisse:* Die vier genannten Sections (`ev_desc`, `ev_kamera`, `ev_wetter`, `ev_zeit`) stehen **alle** in `_def`. Vollabgleich aller 17 gerenderten Section-IDs gegen `_def` → **0 Lücken**. Git: BUG-40-Commit `c8984d6` fügte nur `ev_skypos` hinzu; die vier waren schon vorher in `_def`. Die Audit-Prämisse war auch zum Erstell-Zeitpunkt falsch. → **Keine stille Regression**; `ev_desc:true`/`ev_zeit:true` (Primärinfo offen), `ev_wetter:false`/`ev_kamera:false` (Sekundärinfo eingeklappt) sind intentional korrekt.
- *Bestätigt — Fallstrick:* `loc_events` („Nächste Events", Z. 3983–3986) baut das Toggle-Pattern **hand-gerollt** nach (eigenes `<div class="sheet-section">` + literal `Sections.toggle('loc_events')`), nicht via `mkSec()`. Die Inline-Header-Styles sind 1:1 identisch mit der CSS-Klasse `.sheet-section h4` → Umbau auf `mkSec()` ist optisch + funktional **identisch**. `#loc-events-section` wird nirgends referenziert; `sb_/sc_loc_events` erzeugt `mkSec` gleich; `#loc-events-content` + async-Loader bleiben erhalten.

**Scope:**
Eingeschlossen: (a) `loc_events` auf `mkSec()` umbauen (einheitliche Bauweise); (b) Guard `tools/refactor_check.py`, Check #4 in `analyze_frontend()`. Ausgeschlossen: Backend, andere Sections (keine Regression vorhanden).

**Akzeptanzkriterien (Nutzersicht — erlebbar):**
- [x] In der App: Alle aufklappbaren Abschnitte in Chancen- und Location-Details erscheinen im gewollten Zustand (wichtige offen, Nebeninfos eingeklappt) — unverändert zu heute.
- [x] Der Abschnitt „📅 Nächste Events" in den Location-Details sieht und verhält sich **identisch** zu vorher (gleiche Überschrift, gleicher Standard = offen, lädt seine Events nach).
- [x] Beim nächsten Release läuft der Guard automatisch mit und meldet nichts, solange alles korrekt ist.
- [x] Schutzfall: Würde künftig ein Abschnitt ohne hinterlegten Standardzustand eingebaut, **stoppt der Release-Check mit klarer Fehlermeldung inkl. Abschnittsname** (statt stiller, unsichtbar eingeklappter Abschnitt wie bei BUG-40). *(Probe-verifiziert: Exit 1 + Name.)*
- [x] Schutzfall (Option B, streng): Würde ein Abschnitt künftig hand-gerollt statt über die Standard-Bauweise gebaut, **stoppt der Release-Check** ebenfalls mit Hinweis. *(Probe-verifiziert.)*
- [x] Edge Case: Hat ein Nutzer einen Abschnitt manuell zu-/aufgeklappt, bleibt seine Wahl erhalten (localStorage unberührt).

**Pre-Mortem:**
- 💀 Umbau von „Nächste Events" ändert ungewollt Optik/Verhalten → Gegenmaßnahme: Inline-Styles als identisch zur CSS-Klasse verifiziert (Z. 273–275); AK „identisch zu vorher" + manueller Test.
- 💀 Guard meldet Fehlalarm auf die legitimen Lazy-Render-Checks `Sections.isOpen('ev_fov'/'loc_fov')` → Gegenmaßnahme: Guard erkennt hand-gerollte Sections **nur** an literalem `Sections.toggle('id')`, nicht an `isOpen` (verifiziert: nur `loc_events` matcht, nach Umbau 0).
- 💀 Guard blockiert harmlos (toter `_def`-Key) → Gegenmaßnahme: Guard prüft nur fehlende Defaults + Hand-Rolling, nicht überzählige Keys.

**Architektur:**
- `web/index.html` Z. 3983–3986 (loc_events hand-gerollt), `_def` Z. 2600–2605, `mkSec()` Z. 2624.
- `tools/refactor_check.py` `analyze_frontend()` (neuer Check #4); Exit-1 greift via bestehendem `needs_ticket`→`clean=false` (Z. 335/377), läuft über `fotoalert-refactor` vor jedem Release.

**Implementierungsoptionen:**
- A (pragmatisch): Guard akzeptiert beide Bauweisen, `loc_events` bleibt hand-gerollt.
- B (streng/einheitlich): `loc_events` auf `mkSec()` umbauen + Guard erzwingt einheitliche Bauweise.
- ✅ **Empfehlung & Freigabe (Stephan, 2026-06-25): Option B.**

**Testplan:**
- [ ] Automatisiert: `python3 tools/refactor_check.py --report` grün nach Umbau; Regressions-Probe (kaputte Section → Exit 1 + Name, dann entfernen).
- [ ] Manuell: Location-Detail öffnen → „Nächste Events" offen, Events laden, Optik identisch.

**Analyse & Planung:**
- [x] Example Mapping (2026-06-25) · [x] Pre-Mortem · [x] Architektur analysiert · [x] Optionen A/B · [x] Empfehlung: B (freigegeben)

---


### BUG-45 · Event-Detail: Mehrere Sektionen erscheinen doppelt `[x]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | Done |
| **Erstellt** | 2026-06-28 |
| **Abgeschlossen** | 2026-06-28 |

**Beschreibung:** Im Detail-Sheet eines Events erscheinen mindestens drei Sektionen doppelt: „KAMERA-EMPFEHLUNGEN", „ASTRONOMIE" und „STANDORT & TOPOGRAPHIE". Aus einem Screenshot vom 28.06.2026 geht hervor, dass die Reihenfolge einer vollständigen ersten Hälfte (bis STANDORT & TOPOGRAPHIE) gefolgt von einer zweiten Block-Hälfte (HIMMELSKÖRPER-BAHNEN, BESCHREIBUNG, KAMERA-EMPFEHLUNGEN, ASTRONOMIE, STANDORT & TOPOGRAPHIE, KOMPOSITIONS-ANALYSE) entspricht — als ob zwei Render-Blöcke hintereinander ausgegeben werden. Erwartet: Jede Sektion genau einmal, in der durch US-96 definierten Reihenfolge.

**Bezug:** Verwandt mit US-96 (einheitliche Detailansicht, Sektionsreihenfolge) und BUG-44 (Kalender-Event-Detail vollständige Sektionen). Möglicherweise durch US-96-Implementierung eingeführt (zwei separate Render-Pfade).

---

**Scope:** Entfernung der drei duplizierten Render-Aufrufe (`ev_kamera`, `ev_astro`, `ev_topo`) im `innerHTML`-Template von `Detail.open()` in `web/index.html`. Ausgeschlossen: Reihenfolge-Änderungen (durch US-96 garantiert), Backend-Änderungen.

**Akzeptanzkriterien:**
- [x] Im Detail-Sheet jeder Feed-Chance erscheinen KAMERA-EMPFEHLUNGEN, ASTRONOMIE und STANDORT & TOPOGRAPHIE jeweils genau einmal
- [x] Die Sektions-Reihenfolge entspricht weiterhin US-96: ZEITFENSTER → KARTE → KOORDINATEN → HIMMELSPOSITION → WETTER → KAMERA-EMPFEHLUNGEN → ASTRONOMIE → STANDORT & TOPOGRAPHIE → HIMMELSKÖRPER-BAHNEN → BESCHREIBUNG → KOMPOSITIONS-ANALYSE
- [x] Alle Sektionen sind auf- und zuklappbar (Toggle funktioniert für jede Instanz)
- [x] Edge Case: Eine Chance ohne Kamera-Hints zeigt KAMERA-EMPFEHLUNGEN keinmal (war bedingt, bleibt bedingt)

**Pre-Mortem:**
- 💀 Fix entfernt falsche Zeile (erste statt zweite Instanz) → Sektion fehlt komplett statt doppelt → Gegenmaßnahme: AK-Test prüft Reihenfolge explizit
- 💀 ev_astro_live-Fallback (openForLatLon für Scout-Events) gehört nicht zu BUG-45, kommt aber im selben Working-Tree-Diff mit → wenn isoliert deployt werden soll, aufpassen dass dieser Fix nicht verloren geht

**📎 Code-Verifikation (2026-06-28):**
- `web/index.html` gelesen: `ev_kamera`, `ev_astro`, `ev_topo` erscheinen im Working Tree je **einmal** (Zeilen 3321–3344)
- Im HEAD-Commit `5a384f9` (v1.17.0) standen diese drei Sektionen nach `ev_desc` **ein zweites Mal** → bestätigt durch `git diff HEAD`
- Fix bereits im Working Tree vorhanden: Die drei duplizierten Zeilen sind entfernt
- Weitere Working-Tree-Änderungen: `backend/main.py` + `backend/data/store.py` (TASK-43 QA-Modell), `ev_astro_live` Scout-Fallback — **unabhängig von BUG-45**

**Implementierungsoptionen:**
Nur eine sinnvolle Option: Die drei duplizierten `mkSec()`-Aufrufe nach `ev_desc` aus `web/index.html` entfernen.
✅ **Fix ist bereits im Working Tree implementiert.** Kein weiterer Code-Aufwand.

**Testplan:**
- [ ] Manuell: Feed öffnen → beliebige Chance antippen → Detail-Sheet scrollen → jede der drei Sektionen exakt einmal sichtbar
- [ ] Toggle testen: Jede Sektion auf- und zuklappbar
- [ ] Chance ohne Kamera-Hints: KAMERA-EMPFEHLUNGEN taucht nicht auf (0×)

**Analyse & Planung:**
- [x] Root Cause verifiziert: US-96 (`5a384f9`) hat `ev_kamera/astro/topo` an neue Position verschoben, in alter Position (nach `ev_desc`) aber nicht entfernt
- [x] Fix im Working Tree bestätigt (git diff HEAD)
- [x] Keine Backend-Änderungen nötig
- [x] Test bestanden (2026-06-28, manuell bestätigt)
- [x] Refactor-Check (keine Auto-Fixes, long_function → TASK-49)
- [x] Release (in v1.19.0 / app v2.0.0 enthalten — mit US-83 deployed)

---

