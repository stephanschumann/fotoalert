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
| **🔬 In Analysis** | Pre-Mortem + Spec laufen | *(leer)* |
| **✅ Ready for Dev** | Spec freigegeben, wartet auf Implementierung | *(leer)* |
| **🔄 In Progress** | wird gerade implementiert | *(leer)* |
| **🧪 In Test** | implementiert, wartet auf (Test-)Bestätigung | TASK-22 |
| **🔁 Retro / Lernen** | auto nach Done: Erkenntnisse → Memory/Tests, Skill-Vorschläge zur Freigabe | *(transient — läuft automatisch)* |
| **🚫 Excluded** | explizit ausgeschlossen — nie aufnehmen | *(leer)* |
| **📥 Inbox** | offene Tickets, **nicht** freigegeben | BUG-28, US-83, US-84, US-85, US-87, US-88, BUG-21, BUG-27 · **+ alle übrigen offenen Tickets unten** |

**So benutzt du das Board:**
1. **Freigeben:** Ticket-ID von `Inbox` nach `Ready for Analysis` verschieben → Agenten dürfen starten.
2. **Ausschließen:** ID unter `🚫 Excluded` eintragen → bleibt unangetastet.
3. **Release-Gate:** Steht ein Ticket in `In Test` und ist ein Deploy nötig, wartet die Pipeline auf dein „release".

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

### US-88 · Brennweiten-Filter: Nicht-linearer Slider für feinere Auflösung im Weitwinkelbereich `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Im Brennweiten-Filter liegen 10, 14, 18, 21, 28 und 35 mm so nah beieinander, dass eine präzise Auswahl kaum möglich ist, während 300 und 600 mm sehr weit auseinanderliegen. Der Slider soll eine nicht-lineare Skalierung (z. B. logarithmisch oder mit definierten Stufen) erhalten, die im Weitwinkelbereich feinere Schritte und im Telebereich sinnvolle Zwischenstufen (400 mm, 500 mm) ermöglicht.

---

### BUG-27 · 365-Tage-Kalender leer, lädt keine Ereignisse `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | ToDo |
| **Erstellt** | 2026-06-21 |

**Beschreibung:** Der 365-Tage-Kalender ist leer und zeigt keine Ereignisse an. Mögliche Ursachen: Regression von BUG-14 (Kalender leer nach Cron-Lauf), defekter Cron-Lauf, oder Frontend-Ladefehler beim monatlichen Nachladen (`?month=X&year=Y`).

**Bezug:** Mögliche Regression von BUG-14 [x] (Jahres- & 14-Tage-Kalender leer nach Cron-Lauf, Fix 2026-06-18); verwandt mit BUG-10 [x] (Mond-Alignments im Kalender).

---

**Scope:**
Eingeschlossen: Leere-Response-Caching im Frontend fixen; Backend-Fallback wenn `calendar.json` fehlt/leer.
Ausgeschlossen: Cron-Scheduling-Mechanismus (US-34), Push-Notifications.

**Akzeptanzkriterien:**
- [ ] Kalender zeigt Events des aktuellen Monats, wenn `calendar.json` auf dem Server vorhanden und nicht leer ist
- [ ] Wenn Server `no_cache` zurückgibt: Frontend **cacht kein leeres Ergebnis** (kein `_monthCache.set`) — nächster Aufruf löst erneuten Fetch aus
- [ ] Wenn Server `no_cache` zurückgibt: Toast „Kalender wird neu berechnet – bitte in 2 Min. neu laden" statt lautloser leerer Ansicht
- [ ] Edge Case: Race-Condition — `show()` während `_loading=true` sorgt nach Abschluss trotzdem für `render()`-Aufruf (aktuell: silentes `return`)
- [ ] Edge Case: `calendar.json` auf Server-Disk vorhanden und nicht leer → `/calendar?month=6&year=2026` liefert `status: ok` und `total > 0`

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

## 🔴 Hoch – Kern-Features


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

### US-39 · Resilient Deployment / Rollback (nur Code/Deploy)
> **Abgegrenzt (2026-06-20):** Scope auf reines **Code-/Deploy-Rollback** reduziert. Der Daten-Aspekt („Datensicherung vor Precompute") wurde nach **TASK-18** verschoben.
>
> **Als App-Host** möchte ich bei der Einführung neuer Features oder Fixes jederzeit auf die letzte funktionierende Version zurückrollen können, damit nie die gesamte App verloren geht.
>
> **Akzeptanzkriterien:**
> - Git-basiertes Versioning: jeder Deploy-Stand ist als Tag oder Branch nachvollziehbar
> - Rollback-Anleitung dokumentiert (welcher Befehl, welcher Stand)
> - Cache-Kompatibilität: Rollback bricht keine bestehenden JSON-Caches (oder migriert sie)
> - *(Datensicherung → ausgelagert nach TASK-18)*

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

### US-68 · Host-Approval Workflow für Location-Änderungen und -Löschungen (inkl. Host-Aufgabenliste) `[ ]`
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

### US-72 · Wetterkarte `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Als Fotograf möchte ich eine Wetterkarte für Berlin/Potsdam/Umland sehen, um Wolkendecke und Niederschlag für meine geplanten Shooting-Fenster visuell einschätzen zu können.

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

### US-75 · User/Backend-Datensync: Qualitätssicherung & Automatisierung `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Als Betreiber möchte ich sicherstellen, dass von Nutzern hinzugefügte/geänderte Locations (Motive, Standorte, Beschreibungen) regelmäßig und geprüft ins Backend übertragen werden — inkl. automatischer Generierung von Standortbeschreibungen, idealem Azimut, konsistenter Kategorisierung und automatischer Aktualisierung der Brennweitenempfehlungen.

**Abhängigkeit:** TASK-17 (Datenfundament) + US-76 (Kategorien); baut auf US-77 (Merge) auf.

---

### US-76 · Location-Kategorien als Standardliste mit Filter-Integration `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Hoch |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Location-Kategorien sollen standardisiert und als Auswahlliste beim Bearbeiten und Neuanlegen von Locations verfügbar sein. Der Filter soll um diese Kategorien erweitert werden, damit Nutzer nach Motivtyp filtern können.

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

<!-- ===== INBOX: neue Tickets 2026-06-20 (warten auf Stephans Gate → Ready for Analysis) ===== -->

### BUG-28 · Schwierigkeitsfilter im Chancen-Feed wirkungslos bis Locations-Tab besucht wurde `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-21 |

**Beschreibung:** Der Schwierigkeitsfilter (Include **und** Exclude) hat im Chancen-Feed und Kalender keinen Effekt, solange `Locations.all` leer ist. Beobachtet: Include „Anspruchsvoll" zeigt im Feed weiterhin alle 111 sichtbaren Chancen, obwohl nur 5 von 56 Locations difficulty 3 haben. Erwartet: Filterung greift sofort. Ursache: `Filter.apply()` schlägt `loc.difficulty` über `Locations.all` nach, das aber erst beim Öffnen des Locations-Tabs (oder nach Location-Speichern) geladen wird — nicht beim App-Start auf dem Feed. Fix-Richtung: `Locations.all` beim Boot laden (oder lazy nachladen, wenn ein Schwierigkeitsfilter aktiv ist und die Liste leer ist).

**Bezug:** Vorbestehend seit US-32 (kombiniertes Filtersystem); durch US-71 (Drei-Zustand-Filter) sichtbar geworden, aber nicht von US-71 verursacht — betrifft die Include-Logik identisch. Eigenständig, grenzt an US-71.

---

### US-83 · Scout-Eintrag: Detailansicht + „Als Location speichern" `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-20 |

**Beschreibung:** Ein Klick auf einen Scout-Eintrag soll eine Detailansicht öffnen, die dieselben Daten zeigt wie die Locationdetails. Aus dieser Ansicht kann der Nutzer den Scout-Eintrag optional als neue Location speichern.

**Bezug:** Baut auf US-70[x] (Scout-Tab) auf und wiederverwendet die Location-Detail-UI (US-60/US-63[x]) sowie die Speicher-Logik aus AddLocation (US-56). Eigenständig, grenzt an US-70 (liefert nur die Karten/Liste). Datenfundament-Epic (Location-Persistenz) ist Voraussetzung für „als Location speichern".

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

### US-86 · 🔀 Gemerged in US-68 `[x]`

| Feld | Wert |
|------|------|
| **Status** | Done (gemerged in US-68) |

> **Merge (2026-06-20, von Stephan freigegeben):** Lösch-Berechtigung (Host vs. User), Lösch-Approval, Host-Aufgabenliste + Indikator wurden vollständig in **US-68** überführt (gemeinsames Host-Dashboard/Approval). Kein eigenständiges Ticket mehr — siehe US-68 für Scope, AKs und Abhängigkeiten.

---

### TASK-22 · Workflow: manuelle Terminal-Befehle durch Agents automatisieren `[~]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Mittel |
| **Status** | In Test |
| **Erstellt** | 2026-06-20 |
| **In Progress seit** | 2026-06-21 |

**Beschreibung:** Stephan muss aktuell Befehle (v. a. Git/Release) manuell im Terminal eingeben. Ziel: diese Schritte als Teil des Workflows automatisiert durch die Agents ausführen lassen, soweit möglich. Kernfrage der Analyse: Welche Schritte können sicher automatisiert werden — unter der bestehenden Randbedingung, dass Git-Operationen auf Stephans Rechner/Server laufen müssen und nicht in der Sandbox?

**Bezug:** **Folgeticket von TASK-14[x]** (Automatische Deployment Pipeline — produktiv) — analog zu TASK-21, das beim Done-Abgleich aus TASK-14 herausgezogen wurde. TASK-14 liefert die Pipeline (`deploy.yml`, `release.sh`); TASK-22 adressiert den verbleibenden **manuellen Anstoß** im Terminal. Grenzt an den Release-Workflow und TASK-21 (CI-Test-Gate). Eigenständig.

**Analyse-Ergebnis (2026-06-20):** Kernfrage beantwortet. Vollständige Hands-off-Automatisierung ist **nicht** möglich: Terminal.app läuft in der Computer-Steuerungs-Stufe „click" — Tippen, Cmd+V, Tastendrücke und Rechtsklick durch den Agent sind als Sicherheitsgrenze gesperrt. Der Agent kann Befehle nicht selbst eintippen/einfügen oder Enter drücken; der finale Enter (und alle Git-Befehle) bleiben bei Stephan. Die TASK-22-Randbedingung (Git auf Mac/Server, nicht in der Sandbox) bleibt damit gewahrt.

**Umsetzung (zwei automatisierbare Hälften):** (1) **Eingabe-Halbautomatik** — Befehl per `mcp__computer-use__write_clipboard` in die Mac-Zwischenablage, Stephan macht nur Cmd+V + Enter; (2) **Output-Vollautomatik** — Agent liest das Ergebnis per `mcp__computer-use__screenshot` selbst aus, kein Zurückkopieren mehr. Verankert in `fotoalert-test`, `fotoalert-localdev`, `fotoalert-release` (Routine „Terminal-Automatisierung"); `fotoalert-orchestrator` erhält einen Verweis, damit Subagenten die Routine erben. Live-Health der Produktion läuft schon heute über `web_fetch`. Copy-ready Skill-Blöcke: `outputs/TASK-22_Skill-Aenderungen.md` — Einfügen über Einstellungen → Capabilities (Skill-Cache ist read-only, daher nicht aus der Session editierbar). Offen: Skill-Blöcke einsetzen + ein realer Test-/Release-Zyklus zur Verifikation. Siehe Memory `feedback_terminal_automation`.

---

### US-87 · Locationdetails: größere Karte / Vollbild-Overlay zum Pin-Setzen `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-20 |

**Beschreibung:** Die Karte in den Locationdetails ist zu klein für komfortables Navigieren und Setzen der Location-Pins. Sie soll deutlich größer werden — idealerweise in einem bildschirmfüllenden Overlay, das sich per Klick auf ein Symbol wieder schließen lässt.

**Bezug:** Verbessert die Edit-Karte des Location-Details (US-60). Grenzt an US-58[x] (Blickwinkel-Karte) und US-69[x] (GPS-Zentrierung). Eigenständig.

---

### US-79 · Mondauf- und -untergang in Event- und Locationdetails `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Ergänzend zu Sonnenaufgang und -untergang sollen auch Mondaufgang und -untergang (Uhrzeit, Azimut) in der Astronomie-Kategorie der Event- und Locationdetails angezeigt werden.

---

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
