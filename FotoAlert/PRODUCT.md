# FotoAlert – Product Requirements (Lebende Produktdokumentation)

> **Zweck:** Kanonischer Ist-Stand aller freigegebenen Funktionen.  
> **Pflege:** Nach jedem abgeschlossenen Ticket aktualisieren (vor „Done").  
> **Regression:** Diese Datei ist die Grundlage für den Regressionstest nach jeder Änderung.  
> Zuletzt aktualisiert: 2026-06-28 · Basis: abgeschlossene Tickets bis US-79, US-102, US-100, US-96, BUG-42, BUG-47

---

## 1. App-Übersicht

FotoAlert ist eine PWA + iOS-App, die Fotografen in Berlin/Potsdam/Umland automatisiert berechnet, **wann** ein bestimmtes Motiv (Turm, Brücke, Schloss) von **welchem Standort** aus astronomisch wertvoll ist — Mond oder Sonne im 2°-Fenster um die Motivspitze zur goldenen oder blauen Stunde.

**Technologie-Stack:**
- Frontend: Single-Page-App (`web/index.html`, JS + CSS inline)
- Backend: FastAPI + Python (`backend/main.py`)
- Datenbank: SQLite (WAL, `backend/data/`)
- Hosting: Hetzner-Server, Deploy via `release.sh` + GitHub Actions
- Auth: JWT-basiert, zwei Rollen: `host` und `user`

---

## 2. Navigation & globale UI

| Element | Verhalten |
|---------|-----------|
| Tab Bar (unten) | 5 Tabs: Feed · Karte · + (Quick Add) · Orte · Entdecken |
| Aktiver Tab | `.active`-Klasse, nie `.open` |
| Sheets | `.open`-Klasse für alle Bottom-Sheets; kein `.active` |
| Theme | Automatisch Tag/Nacht basierend auf Systemeinstellung (US-97), manueller Umschalter in Einstellungen |
| Design-System | Bauhaus-Tokens (`--bg`, `--surface`, `--accent`, `--text`, `--on-accent` etc.), Linien-Icon-Set (US-100) |
| Safe Area | Alle Sheet-Header haben `env(safe-area-inset-top)` — gilt für: `#add-sheet .add-header`, `#detail-sheet`, `#loc-detail-sheet`, `#impressum-sheet` |
| Logo | Bauhaus-Logo sichtbar (US-102) |

**Pflicht-Regression globale UI:**
- [ ] Tab-Wechsel funktioniert (alle 5 Tabs)
- [ ] Kein Tab zeigt seinen Inhalt doppelt
- [ ] Kein Sheet öffnet sich ungewollt beim Laden
- [ ] Theme-Wechsel (hell/dunkel) ändert alle Farbtokens konsistent
- [ ] Alle Icons sichtbar in Safari (SVG `<use>` + `currentColor`-Attribute auf `<g>`, nicht per CSS-Klasse)

---

## 3. Feed-Tab (14-Tage-Chancen)

**Was der Nutzer sieht:** Score-sortierte Liste von Foto-Chancen für die nächsten 14 Tage.

| Funktion | Verhalten |
|----------|-----------|
| Chance-Karten | Jede Karte zeigt: Titel, Datum/Uhrzeit, Location-Name, Score-Ring (farbcodiert), Event-Typ |
| Score-Ring | Kreisring, Füllgrad = Score (0–100%), Farbe: grün ≥80%, orange 50–79%, rot <50% |
| Wetter-Badge | Tag-Chip auf Feed-Karten wenn Wetter bekannt (`weather_status: "ok"` bzw. `weather_score > 0`). Wird das Wetter einer gerade geänderten/neuen Location gerade nachgeladen, zeigt die Karte stattdessen ehrlich „Wetter wird nachgeladen" (Uhr-Icon). Chancen weiter als ~3 Tage in der Zukunft (`weather_status: "none"`) zeigen kein Wetter-Badge (kein „lädt ewig"). (BUG-44, US-106) |
| Wetter sofort nach Standort-Änderung (US-106) | Nach dem Verschieben/Anlegen einer Location wird das Wetter gezielt nur für diese Location nachgeladen (Sekunden, nicht bis zu 3 h). Das „wird aktualisiert"-Banner verschwindet erst, wenn Foto-Chancen UND echtes Wetter stehen — nicht schon beim Platzhalter. Schlägt das Wetter-Nachladen fehl, bleibt die Location als „wird aktualisiert" markiert und wird beim nächsten Lauf erneut versucht. |
| Reihenfolge bei Standort-Änderung: Feed+Wetter sofort, Kalender im Hintergrund (US-106 Nachbesserung) | Nach dem Verschieben einer Location werden zuerst die sichtbaren Foto-Chancen + ihr Wetter berechnet; sobald beides steht, verschwindet das „wird aktualisiert"-Banner in Sekunden. Der vollständige Jahres-Kalender dieser Location wird **danach im Hintergrund** nachgerechnet, ohne das Banner aufzuhalten — der Kalender-Tab dieser Location kann dabei ein paar Minuten noch den alten Stand zeigen (bewusst akzeptiert). Ein Fehler beim Hintergrund-Kalender nimmt die bereits erfolgte Freigabe nicht zurück. Es läuft nie mehr als eine schwere Berechnung gleichzeitig; eine zweite Änderung während der laufenden Kalender-Rechnung wird gemerkt und danach automatisch nachgeholt. |
| Feed-Filter | Filter-Panel (Sheet) mit 9 Kriterien; wirkt auf alle Ansichten (Details siehe Sektion 3a) |
| Mondaufgang-Events | Eigenständige Karten im Feed mit Typ `"Mondaufgang"`, Score-Ring, Uhrzeit und Location (US-79) |
| Monduntergang-Events | Eigenständige Karten im Feed mit Typ `"Monduntergang"`, Score-Ring, Uhrzeit und Location (US-79) |
| Alert-Banner | Sichtbar wenn relevante Chancen heute oder morgen |
| Tipp: Chance antippen | Öffnet Detail-Sheet (Pflicht: Detail schließt mit Overlay-Tap) |
| Leer-State | Wenn keine Chancen passen: Hinweis-Text, kein Absturz |
| Kalender-Modus | Button „Jahreskalender" im Feed schaltet auf Monatskalender-Ansicht um; Tap auf Kalender-Event sucht passenden Feed-Eintrag (location_id + ±1h) und übergibt vollständiges Objekt (inkl. weather_details) an Detail-Sheet (BUG-44) |

**Pflicht-Regression Feed:**
- [ ] Mindestens 1 Karte sichtbar (bei min_score 0.2)
- [ ] Chance antippen → Detail-Sheet öffnet
- [ ] Overlay antippen → Sheet schließt sich
- [ ] Filter-Sheet öffnet und schließt
- [ ] Score-Ring korrekt (visuelle Überprüfung: 75% = ring 3/4 gefüllt)
- [ ] Karten nicht doppelt vorhanden
- [ ] Routine-Events-Filter entfernt Goldene/Blaue-Stunde-Karten
- [ ] Filter-Chips „Mondaufgang" / „Monduntergang" filtern Feed korrekt (US-79)
- [ ] Mondaufgang-/Monduntergang-Events erscheinen als eigenständige Karten im Feed (US-79)

---

## 3a. Filter (BUG-46 — vollständige Spezifikation)

Der Filter hat 9 Kriterien. Vier davon haben **Drei-Zustände** (Off → Einschließen → Ausschließen → Off):
Eventtyp, Tageszeit, Schwierigkeit, Kategorie.
Seit BUG-46 haben auch Verifikationsstatus und Mindest-Bewertung Drei-Zustände.

### Kriterien und ihre Zustände

| Kriterium | Drei-Zustände | Anmerkung |
|---|---|---|
| **Eventtyp** | Ja (Off → nur zeigen → ausblenden → Off) | Gilt für Chancen-Feed, Kalender, Scout, Karte |
| **Tageszeit** | Ja (Off → nur zeigen → ausblenden → Off) | Nur Chancen-Feed + Kalender + Scout; **ausgegraut auf Karte + Locations-Tab** |
| **Mindest-Wahrscheinlichkeit** | Nein (Slider 0–100%) | Nur Chancen-Feed + Kalender + Scout; **ausgegraut auf Karte + Locations-Tab** |
| **Brennweite** | Nein (Dual-Handle-Slider) | Nur Chancen-Feed + Kalender + Scout; **ausgegraut auf Karte + Locations-Tab** |
| **Schwierigkeit** | Ja (Off → nur zeigen → ausblenden → Off) | Gilt für alle Ansichten inkl. Karte + Locations-Tab |
| **Kategorie** | Ja (Off → nur zeigen → ausblenden → Off) | Gilt für alle Ansichten inkl. Karte + Locations-Tab |
| **Mindest-Bewertung** | Ja (BUG-46): Off → ≥ N Sterne (gold) → < N Sterne (rot) → Off | Gilt für alle Ansichten |
| **Entfernung (GPS)** | Nein (Einfach-Auswahl) | Gilt für alle Ansichten inkl. Karte |
| **Verifikationsstatus** | Ja (BUG-46): „Geprüfte" hat Off → nur Geprüfte → alle außer Geprüfte → Off; andere Chips (Nicht geprüft, Probleme) togglen einfach | Gilt für alle Ansichten inkl. Karte |

### Semantik der Drei-Zustände für neue Kriterien (BUG-46)

**Mindest-Bewertung:**
- Goldrand (Einschließen): zeigt nur Locations/Chancen mit eigener Bewertung ≥ N Sterne
- Rotrand (Ausschließen): zeigt nur Locations/Chancen mit eigener Bewertung < N Sterne (gezielt niedrig Bewertete ansehen)
- Off: keine Filterung

**Verifikationsstatus:**
- Chip „Geprüfte" — Goldrand (Einschließen): zeigt nur verifiziert-ok
- Chip „Geprüfte" — Rotrand (Ausschließen, `excl_verified`): zeigt alle außer verifiziert-ok (= ungeprüft + Probleme)
- Off: keine Filterung
- Chips „Nicht geprüft" und „Probleme" bleiben einfache Selekt-Chips

### Ausgrauen-Verhalten (BUG-46)

Kriterien ohne Wirkung in der aktuellen Ansicht werden visuell gedimmt (opacity 0.45, pointer-events none) — sie bleiben sichtbar, sind aber nicht bedienbar:

| Ansicht | Ausgegraut |
|---|---|
| **Karte** | Tageszeit, Brennweite, Mindest-Wahrscheinlichkeit |
| **Locations-Tab** | Eventtyp, Tageszeit, Brennweite, Mindest-Wahrscheinlichkeit |
| **Chancen-Feed / Kalender / Scout** | Nichts ausgegraut |

### Wirkungs-Übersicht nach Ansicht

| Kriterium | Chancen-Feed | Kalender | Scout | Locations-Tab | Karte |
|---|---|---|---|---|---|
| Eventtyp | ✓ | ✓ | ✓ (body_name) | — (ausgegraut) | ✓ (via Feed-Daten) |
| Tageszeit | ✓ | ✓ | ✓ (session) | — (ausgegraut) | — (ausgegraut) |
| Wahrscheinlichkeit | ✓ | ✓ | ✓ | — (ausgegraut) | — (ausgegraut) |
| Brennweite | ✓ | ✓ | ✓ | — (ausgegraut) | — (ausgegraut) |
| Schwierigkeit | ✓ | ✓ | — | ✓ | ✓ |
| Kategorie | ✓ | ✓ | — | ✓ | ✓ |
| Mindest-Bewertung | ✓ | ✓ | — | ✓ | ✓ |
| Entfernung (GPS) | ✓ | — | ✓ | — | ✓ |
| Verifikation | ✓ | ✓ | — | ✓ | ✓ |

**Pflicht-Regression Filter (BUG-46):**
- [ ] Filter-Badge zeigt korrekte Anzahl aktiver Kriterien
- [ ] Bewertungs-Chip: Off → gold „≥ N" → rot „< N" → Off (drei Tipp-Schritte)
- [ ] Verifikation „Geprüfte": Off → gold → rot → Off (drei Tipp-Schritte)
- [ ] Tageszeit, Brennweite, Wahrscheinlichkeit auf Karte ausgegraut
- [ ] Eventtyp, Tageszeit, Brennweite, Wahrscheinlichkeit auf Locations-Tab ausgegraut
- [ ] Karte zeigt nach Schwierigkeits-Filter nur passende Pins
- [ ] Karte zeigt nach Kategorie-Filter nur passende Pins
- [ ] Karte zeigt nach Verifikations-Filter nur passende Pins

---

## 4. Detail-Sheet (Chancen-Detailansicht)

Gilt für alle Einstiegspunkte: Feed, Kalender, Scout, Location-Zukünftige-Events (US-96).

**Sektions-Reihenfolge (fest, alle beim Öffnen eingeklappt — US-105):**
1. Beschreibung (Kontext zuerst)
2. Ideales Zeitfenster
3. Wetter zum Shoot-Zeitpunkt (zeitlich zusammengehörig mit Zeitfenster)
4. Karte & Blickwinkel (FOV-Karte, Leaflet)
5. Kompositions-Analyse (räumlich zusammengehörig mit Karte; entfällt bei Scout/Kalender)
6. Koordinaten (mit Street-View-Button nur wenn Azimut vorhanden — BUG-41)
7. Himmelsposition (Azimut + Höhe relativ zur Motivspitze — US-67)
8. Kamera-Empfehlungen (Brennweite, Blende, Belichtungszeit)
9. Astronomie (Erweitert)
10. Standort & Topographie
11. Himmelskörper-Bahnen (AstroLive, US-64 — eingeklappte inline-Sektion)
12. Aktions-Buttons: „Zum Kalender", „Erinnerung setzen", „Erneut prüfen"

| Funktion | Verhalten |
|----------|-----------|
| Sektionen | Alle beim Öffnen eingeklappt; per Tap auf/zu |
| „Zum Kalender" | Lädt `.ics`-Datei herunter; Apple Kalender öffnet Event |
| Close | Overlay antippen oder Close-Button schließt Sheet |
| Mond-Erde-Distanz | Zeigt ~384.400 km (nicht ~370 km — BUG-18 gefixt) |
| Mondaufgang in Astronomie-Sektion | Zeigt Uhrzeit (Berliner Zeit) + Azimut in Grad, wenn an diesem Tag vorhanden (US-79); fehlt kommentarlos wenn null |
| Monduntergang in Astronomie-Sektion | Analog: Uhrzeit (Berliner Zeit) + Azimut in Grad, wenn vorhanden (US-79); fehlt kommentarlos wenn null |
| Koordinaten-Sektion | Kein Overflow-Problem (BUG-38 gefixt); Labels korrekt ausgerichtet |
| Sheet-Header | Kein blaugrauer Strich links (BUG-39 gefixt) |

**Pflicht-Regression Detail:**
- [ ] Sheet öffnet sich von unten (slide-up Animation)
- [ ] Alle 12 Sektionen vorhanden — **keine Sektion doppelt**
- [ ] Beim Öffnen: alle Sektionen eingeklappt
- [ ] Close-Button erreichbar (Safe Area, kein Overlap mit Status Bar)
- [ ] FOV-Karte lädt (Leaflet) und zeigt Verbindungslinie; Zielring-Marker (Ring + Ticks + Mittelpunkt, gold) sichtbar; Legende zeigt Zielring-Icon (US-103)
- [ ] „Zum Kalender" → `.ics` Download startet
- [ ] Street-View-Button nur sichtbar wenn Azimut verfügbar
- [ ] Astronomie-Sektion zeigt Mondaufgang + Monduntergang mit Uhrzeit + Azimut (wenn vorhanden) (US-79)
- [ ] Kein Fehler / keine leere Zeile wenn Mondaufgang/-untergang null (US-79)

---

## 5. Karten-Tab

| Funktion | Verhalten |
|----------|-----------|
| Karte | Leaflet, dunkle Tiles (Carto Dark), Berlin zentriert |
| Marker | ≥10 Pins für gespeicherte Locations; SVG-Tropfen (blau, weißer Kern) im Bauhaus-Stil (US-103) |
| Marker-Tap | Popup mit Location-Name und Kategorie |
| Kartenfilter | Alle location-bezogenen Filterkriterien wirken auf Karten-Pins: Eventtyp (inkl. Ausschließen, BUG-23+BUG-46), Schwierigkeit, Kategorie, Verifikation, Bewertung, Entfernung (GPS). Tageszeit, Brennweite und Wahrscheinlichkeit sind auf der Karte ausgegraut (BUG-46) |
| GPS-Zentrierung | Button zentriert Karte auf aktuelle GPS-Position (US-69) |

**Pflicht-Regression Karte:**
- [ ] Leaflet-Karte lädt (kein weißer/leerer Block)
- [ ] ≥10 Pins sichtbar
- [ ] Pin antippen → Popup erscheint
- [ ] Karte nicht leer nach Theme-Wechsel

---

## 6. Quick-Add-Tab (+)

| Funktion | Verhalten |
|----------|-----------|
| Sheet öffnet | Karte + Eingabeformular sichtbar |
| GPS-Button | Browser fragt nach Standort-Erlaubnis; setzt Fotograf-Marker |
| Karte antippen | Setzt Motiv-Marker; Verbindungslinie zwischen Fotograf ↔ Motiv |
| Koordinaten-Eingabe | Manuell via Textfeld (US-56) |
| „Alignments berechnen" | POST `/preview-alignment`; zeigt Preview-Box mit Profil + Alignment-Liste |
| Ohne Punkte | Toast: „Bitte Standort und Motiv setzen" |
| „Location speichern" | Toast: „✅ Location gespeichert!"; Location erscheint in Orte-Tab |
| Höhe-Korrektur | Fotografenstandort-Höhe einstellbar (US-62) |

**Pflicht-Regression Quick-Add:**
- [ ] Sheet öffnet ohne Absturz
- [ ] GPS-Button fragt nach Erlaubnis
- [ ] Karten-Tap setzt Motiv-Marker + zeigt Linie
- [ ] „Ohne Punkte" → Toast erscheint (kein Absturz)
- [ ] „Mit Punkten" → Preview-Box mit Azimut, Distanz, Höhenwinkel
- [ ] Gespeicherte Location erscheint danach im Orte-Tab

---

## 7. Orte-Tab (Locations)

| Funktion | Verhalten |
|----------|-----------|
| Locations-Liste | ≥15 Location-Karten; scrollbar |
| Suche | Live-Textsuche filtert nach Standortname (US-53) |
| Location antippen | Öffnet Location-Detail-Sheet |
| Location-Detail | Zeigt: Name, Koordinaten, Azimut, Brennweiten-Empfehlung, zukünftige Events |
| Location bearbeiten | Edit-Modus in Location-Detail; Änderungen persistieren via PATCH + Server-Fetch |
| Custom Locations | Vom Nutzer gespeicherte Locations erscheinen hier; Namen ohne 📍-Emoji (BUG-42) |
| Standortverifikation | Verifikationen werden persistiert (BUG-26) |

**Pflicht-Regression Orte:**
- [ ] ≥15 Karten sichtbar
- [ ] Suche „Babelsberg" filtert korrekt
- [ ] Location-Detail-Sheet öffnet und schließt
- [ ] Edit → Speichern → Änderung sofort in Sheet + Liste sichtbar (kein Reload nötig)
- [ ] Close-Button erreichbar (Safe Area — BUG-25 gefixt)

---

## 8. Scout-Tab (Entdecken)

| Funktion | Verhalten |
|----------|-----------|
| Scout-Feed | Automatisiert berechnete Foto-Ephemeride (Mond-Alignments, US-70) |
| Scout zieht nach Standort-Änderung nach (US-106) | Nach dem Verschieben/Anlegen einer Location wird der Scout-Volllauf zeitnah (wenige Minuten) angestoßen, sodass die Location im Entdecken-Bereich erscheint — nicht erst am nächsten Morgen. Mehrere schnelle Änderungen werden zu einem Lauf zusammengefasst (entprellt) und nie parallel ausgeführt (Single-Flight); ändert sich während eines Laufs erneut etwas, folgt genau ein Nachlauf. |
| Scout-Karten | Identisches Design wie Feed-Karten: ScoreRing (farbcodiert), Session-Icon + Session-Label + Uhrzeit, Motivname, Location-Zeile „Blick vom [Himmelsrichtung]", Tag-Chips (Wetter, Entfernung, Mondbeleuchtung bei Mond-Chancen); Navigation-Button vollbreit am Kartenende (US-104) |
| Scout-Detail | Klick auf Scout-Karte öffnet vollständige Detail-Ansicht (identisch mit Feed-Chancen): FOV-Karte, Koordinaten, Himmelsposition, Wetter, Kameraempfehlung, AstroLive-Bahn, Beschreibung (US-83, v1.18.0) |
| Scout-Detail: Als Location speichern | Button „Als Location speichern" (SVG-Pin-Icon) in der Detailansicht; speichert den Scout-Standpunkt via POST `/preview-alignment` (save:true) als neue Location (US-83) |
| Scout-Karten Klick | cursor:pointer auf Scout-Karten (Hover-Hand wie Feed-Karten) |
| Suche | Standortname-Suche (analog Feed-Suche) |

**Pflicht-Regression Scout:**
- [ ] Scout-Tab lädt ohne Fehler
- [ ] ≥1 Scout-Karte sichtbar mit ScoreRing (links), Session-Icon + Label + Uhrzeit, Motivname, Location-Zeile „Blick vom [Richtung]", Tag-Chips
- [ ] Location-Zeile zeigt NUR die Himmelsrichtung (kein Motivname-Duplikat): „Blick vom Nordosten"
- [ ] Tag-Chips: Wetter-Text + Entfernung (km) + Mondbeleuchtung (nur bei Mond-Chancen)
- [ ] Kein Standort-Button auf der Karte (nur Navigation-Button, vollbreit)
- [ ] Navigation-Button öffnet Apple Maps-Routenführung zum Standpunkt; öffnet NICHT die Detailansicht
- [ ] Karte antippen (außerhalb Button) → Detailansicht öffnet sich
- [ ] Karte nicht doppelt (keine Render-Dopplung)
- [ ] Klick auf Scout-Karte öffnet Detail-Sheet mit allen Sektionen (eingeklappt)
- [ ] „Als Location speichern"-Button sichtbar (SVG-Icon, kein Emoji)
- [ ] Klick auf „Als Location speichern" → Toast + neue Location in Locations-Tab
- [ ] AstroLive-Sektion im Scout-Detail öffnet Bahn-Karte ohne Fehler

---

## 9. Einstellungen

| Funktion | Verhalten |
|----------|-----------|
| Mindest-Score Slider | 0–100%; nach Änderung → Feed zeigt weniger/mehr Chancen |
| Erscheinungsbild | System / Hell / Dunkel (US-97); Auswahl persistiert in localStorage |
| Backend-URL | Änderbar; wird in localStorage gespeichert |
| „Jetzt aktualisieren" | POST `/refresh`; Toast „✅ Daten aktualisiert" nach ~3s |
| Impressum | Öffnet Impressum-Sheet |
| Rollen-Anzeige | Zeigt „Host" oder „User" — Rolle wird aus dem Token-Präfix abgeleitet (`CFG.role` als Getter aus `fa_token`), nicht aus `fa_role` in localStorage; robust gegen Safari ITP / Storage-Bereinigung (BUG-47) |

**Pflicht-Regression Einstellungen:**
- [ ] Slider auf 80% → Feed-Reload → weniger Karten
- [ ] Theme-Umschalter ändert sofort das Erscheinungsbild
- [ ] Theme-Auswahl überlebt App-Reload
- [ ] Nach Host-Login sofort „Host" sichtbar (kein Browser-Refresh nötig) (BUG-47)
- [ ] Nach Logout und erneutem Login als User → „User" sichtbar

---

## 10. Login / Auth

| Funktion | Verhalten |
|----------|-----------|
| Login-Screen | Erscheint wenn nicht eingeloggt |
| Host-Login | Volladmin: Locations anlegen/editieren, Refresh starten |
| User-Login | Lesen + eigene Custom-Locations |
| Session | JWT-Token; überlebt App-Reload |
| Logout | Manuell in Einstellungen |
| Rollen-Ableitung | `CFG.role` wird als Getter aus dem Token-Präfix (`fa_token`) gelesen — kein Fallback auf `fa_role` localStorage-Key; nach Login `App.init()` + `App.nav('feed')` sorgen für korrektes Re-Render des Settings-Tabs (BUG-47) |

**Pflicht-Regression Auth:**
- [ ] Nicht-eingeloggter Zugriff → Login-Screen erscheint
- [ ] Login als Host → alle Tabs erreichbar, Einstellungen zeigen sofort „Host"
- [ ] Login als User → Einstellungen zeigen „User"
- [ ] App-Reload nach Host-Login → Einstellungen zeigen weiterhin „Host" (Token-Präfix-Auswertung)
- [ ] Geschützte Endpoints ohne Token → HTTP 401

---

## 11. Backend-Endpoints (freigegebene API)

| Endpoint | Methode | Funktion |
|----------|---------|----------|
| `/health` | GET | Status + locations_count + version |
| `/locations` | GET | Alle Locations (Basis + Overrides + Custom) |
| `/locations/{id}` | PATCH | Location editieren (auth: host) |
| `/opportunities` | GET | 14-Tage-Feed; params: `min_score`, `days`; liefert seit US-79 vier neue Felder je Event: `moonrise_utc`, `moonset_utc`, `moonrise_azimuth`, `moonset_azimuth` (ISO-String oder null / Float oder null) |
| `/calendar` | GET | 365-Tage-Kalender; liefert seit US-79 dieselben vier Mondfelder (nutzt dieselbe `_serialize()`-Funktion) |
| `/discover` | GET | Scout-Ephemeride (Mond-Alignment) |
| `/preview-alignment` | POST | Quick-Add-Vorschau (auth: host) |
| `/refresh` | POST | Manueller Cache-Reload (auth: host) |
| `/daily-briefing` | GET | Tages-Zusammenfassung |
| `/login` | POST | JWT-Token (Prod only; lokal: `auth.issue_token()`) |

**Pflicht-Regression Backend:**
```bash
# Schnell-Check (alle 5 in einem Durchlauf):
curl -s http://localhost:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'; print('✅ Health OK')"
curl -s http://localhost:8000/locations | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d)>10; print(f'✅ Locations OK ({len(d)})')"
curl -s "http://localhost:8000/opportunities?min_score=0.1&days=14" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✅ Feed OK ({len(d)} Events)')"
curl -s http://localhost:8000/discover | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✅ Scout OK ({len(d)} Events)')"
curl -s http://localhost:8000/calendar | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✅ Kalender OK ({len(d)} Events)')"
```

---

## 12. Regressions-Matrix (nach Ticket-Typ)

Welche Sektionen müssen nach welcher Art von Änderung geprüft werden:

| Änderungstyp | Pflicht-Regression |
|---|---|
| **CSS / Theme** | Alle 5 Tabs + alle Sheets in Hell UND Dunkel; kein Weiß-auf-Weiß, kein unsichtbarer Button |
| **Detail-Sheet** | Alle Sektionen vorhanden + nicht doppelt; alle Einstiegspunkte (Feed, Kalender, Scout) |
| **Feed-Rendering** | Feed-Karten nicht doppelt; Filter funktioniert; Score-Ring korrekt |
| **Backend-Endpoint** | Health + Locations + Feed + Scout + Kalender (Schnell-Check oben) |
| **Location-Edit** | curl PATCH + Browser UI-Pfad (nicht nur curl) |
| **Auth** | Geschützter Endpoint mit + ohne Token; Login-Screen für nicht-eingeloggte |
| **Navigation/Tabs** | Alle 5 Tabs erreichbar; kein Tab zeigt doppelten Inhalt |
| **Sheet-Open/Close** | Öffnen über alle Einstiegspunkte; Schließen per Overlay + Close-Button; Safe Area |

---

## 13. Bekannte offene Punkte (ToDo / In Progress)

| Ticket | Beschreibung |
|--------|-------------|
| US-106 | Geänderte/neue Location sofort komplett nutzbar — Wetter + Entdecken + Nachholen (Implemented, lokales Test-Gate + Refactor + Release ausstehend) |
| US-83 | Scout-Detail + „Als Location speichern" (In Progress) |
| US-95 | Chancendetails: Buttons kleiner, Karte größer |
| US-98 | Bauhaus-Redesign Epic (übergeordnet) |
| BUG-21 | Brennweiten-Eingabe: kein Komma auf iOS |
| US-79 offen | Location-Detail Astronomie-Block: Mondaufgang/-untergang für Heute (live berechnet) — noch nicht entschieden ob eigenes Ticket; der restliche Scope (Feed, Filter, Event-Detail) ist fertig |

---

## 14. Changelog

| Datum | Ticket | Änderung |
|-------|--------|----------|
| 2026-06-28 | — | Initiale Erstellung auf Basis abgeschlossener Tickets bis v1.17 |
| — | US-96 | Einheitliche Detailansicht aus allen Einstiegspunkten; Sektionen-Reihenfolge festgelegt |
| — | US-100 | Bauhaus-Linien-Icon-Set |
| — | US-101 | Kompaktere Buttons/Schriftgrößen |
| — | US-102 | Bauhaus-Logo + App-Icon |
| — | US-97 | Automatischer Tag/Nacht-Modus + manueller Umschalter |
| — | US-99 | Bauhaus-Theme-Tokens (hell + dunkel) |
| — | US-88 | Brennweiten-Filter nicht-linear |
| 2026-06-28 | US-103 | Karten-Marker & FOV-Legende im Bauhaus-Stil (Tropfen + Zielring) |
| 2026-06-28 | US-106 | Geänderte/neue Location sofort komplett nutzbar: gezieltes Wetter-Nachladen (Teil 1), debounced Scout-Volllauf mit Single-Flight + Dirty-Nachlauf (Teil 2), Pending-Queue mit Nachlauf am Lauf-Ende + Banner bleibt bis Feed UND Wetter stehen (Teil 3). Status Implemented — Test/Refactor/Release ausstehend. |
| 2026-06-28 | US-106 (Nachbesserung) | Reihenfolge umgestellt: erst Feed+Wetter (Banner weg in Sekunden), Jahres-Kalender dieser Location zieht danach im Hintergrund nach (vorher hing das Banner ~10 Min am 365-Tage-Kalender). Kalender-Fehler nehmen die Freigabe nicht zurück; weiterhin nur eine schwere Berechnung gleichzeitig, zweite Änderung wird nachgeholt. Status Implemented — Test/Refactor/Release ausstehend. |
| 2026-06-28 | US-105 | Chancen-Detail: Sektionsreihenfolge optimiert (Beschreibung zuerst, Wetter nach Zeitfenster, Kompositions-Analyse nach Karte) |
| 2026-06-28 | US-104 | Scout-Karten auf Feed-Design umgestellt (ScoreRing, Himmelsrichtung, Tag-Chips) |
| — | US-70 | Scout-Tab: Mond-Alignment-Ephemeride |
| — | US-66 | Login + Auth (Host/User) |
| — | BUG-42 | Custom Locations: kein 📍-Emoji in Namen |
| — | BUG-41 | Street-View-Button nur bei Azimut sichtbar |
| — | BUG-38/39 | Koordinaten-Sektion: Overflow + Strich gefixt |
| 2026-06-28 | BUG-44 | Kalender-Events im 14-Tage-Fenster zeigen vollständiges Detailsheet inkl. Wetter; „Wetter unbekannt"-Badge entfernt |
| 2026-06-28 | BUG-46 | Filter: Drei-Zustände für Verifikation + Bewertung; Karte an alle Location-Filter angebunden; ansichtsabhängiges Ausgrauen irrelevanter Kriterien |
| 2026-06-28 | US-79 | Mondaufgang + Monduntergang als eigenständige Event-Typen (`"Mondaufgang"`, `"Monduntergang"`) im Feed, Kalender, Filter und Location-Detail (Nächste Chancen); vier neue API-Felder in `_serialize()`: `moonrise_utc`, `moonset_utc`, `moonrise_azimuth`, `moonset_azimuth`; Event-Detail Astronomie-Sektion zeigt Uhrzeit + Azimut; `/refresh-feed` nach Release ausführen |
| 2026-06-28 | BUG-47 | Einstellungsseite zeigt korrekte Rolle nach Host-Login: `CFG.role` als Getter aus Token-Präfix (robust gegen Safari ITP); nach Login `App.init()` + `App.nav('feed')` für sofortiges UI-Update ohne Browser-Refresh |
