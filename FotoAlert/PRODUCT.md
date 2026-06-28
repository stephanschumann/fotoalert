# FotoAlert – Product Requirements (Lebende Produktdokumentation)

> **Zweck:** Kanonischer Ist-Stand aller freigegebenen Funktionen.  
> **Pflege:** Nach jedem abgeschlossenen Ticket aktualisieren (vor „Done").  
> **Regression:** Diese Datei ist die Grundlage für den Regressionstest nach jeder Änderung.  
> Zuletzt aktualisiert: 2026-06-28 · Basis: abgeschlossene Tickets bis US-102, US-100, US-96, BUG-42

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
| Feed-Filter | Filter-Panel (Sheet) mit: Mindest-Score Slider, Event-Typ Checkboxen, Brennweiten-Range-Slider (nicht-linear, US-88), Routinen-Events ausblenden (US-40) |
| Alert-Banner | Sichtbar wenn relevante Chancen heute oder morgen |
| Tipp: Chance antippen | Öffnet Detail-Sheet (Pflicht: Detail schließt mit Overlay-Tap) |
| Leer-State | Wenn keine Chancen passen: Hinweis-Text, kein Absturz |

**Pflicht-Regression Feed:**
- [ ] Mindestens 1 Karte sichtbar (bei min_score 0.2)
- [ ] Chance antippen → Detail-Sheet öffnet
- [ ] Overlay antippen → Sheet schließt sich
- [ ] Filter-Sheet öffnet und schließt
- [ ] Score-Ring korrekt (visuelle Überprüfung: 75% = ring 3/4 gefüllt)
- [ ] Karten nicht doppelt vorhanden
- [ ] Routine-Events-Filter entfernt Goldene/Blaue-Stunde-Karten

---

## 4. Detail-Sheet (Chancen-Detailansicht)

Gilt für alle Einstiegspunkte: Feed, Kalender, Scout, Location-Zukünftige-Events (US-96).

**Sektions-Reihenfolge (fest, alle beim Öffnen eingeklappt):**
1. Titel / Score
2. Uhrzeit (3 Spalten: Start / Optimal / Ende)
3. FOV-Karte (Leaflet, zeigt Fotograf + Motiv + Richtungsstrahl)
4. Koordinaten (mit Street-View-Button nur wenn Azimut vorhanden — BUG-41)
5. Himmelsposition (Azimut + Höhe relativ zur Motivspitze — US-67)
6. Wetter
7. Himmelskörper-Bahnen (AstroLive, US-64 — eingeklappte inline-Sektion)
8. Kamera-Tipps (Brennweite, Blende, Belichtungszeit)
9. Astronomie (Erweitert)
10. Topographie
11. Komposition
12. Aktions-Buttons: „Zum Kalender", „Erinnerung setzen", „Erneut prüfen"

| Funktion | Verhalten |
|----------|-----------|
| Sektionen | Alle beim Öffnen eingeklappt; per Tap auf/zu |
| „Zum Kalender" | Lädt `.ics`-Datei herunter; Apple Kalender öffnet Event |
| Close | Overlay antippen oder Close-Button schließt Sheet |
| Mond-Erde-Distanz | Zeigt ~384.400 km (nicht ~370 km — BUG-18 gefixt) |
| Koordinaten-Sektion | Kein Overflow-Problem (BUG-38 gefixt); Labels korrekt ausgerichtet |
| Sheet-Header | Kein blaugrauer Strich links (BUG-39 gefixt) |

**Pflicht-Regression Detail:**
- [ ] Sheet öffnet sich von unten (slide-up Animation)
- [ ] Alle 12 Sektionen vorhanden — **keine Sektion doppelt**
- [ ] Beim Öffnen: alle Sektionen eingeklappt
- [ ] Close-Button erreichbar (Safe Area, kein Overlap mit Status Bar)
- [ ] FOV-Karte lädt (Leaflet) und zeigt Verbindungslinie
- [ ] „Zum Kalender" → `.ics` Download startet
- [ ] Street-View-Button nur sichtbar wenn Azimut verfügbar

---

## 5. Karten-Tab

| Funktion | Verhalten |
|----------|-----------|
| Karte | Leaflet, dunkle Tiles (Carto Dark), Berlin zentriert |
| Marker | ≥10 farbige Pins für gespeicherte Locations |
| Marker-Tap | Popup mit Location-Name und Kategorie |
| Kartenfilter | Event-Typ-Filter synchronisiert mit Feed-Filter (BUG-23 gefixt) |
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
| Scout-Karten | Identisches Design wie Feed-Karten: ScoreRing (farbcodiert), Session-Icon + Session-Label + Uhrzeit, Motivname, Location-Zeile „Blick vom [Himmelsrichtung]", Tag-Chips (Wetter, Entfernung, Mondbeleuchtung bei Mond-Chancen); Navigation-Button vollbreit am Kartenende (US-104) |
| Scout-Detail | Klick auf Scout-Karte öffnet vollständige Detail-Ansicht (identisch mit Feed-Chancen): FOV-Karte, Koordinaten, Himmelsposition, Wetter, Kameraempfehlung, AstroLive-Bahn, Beschreibung (US-83, v1.18.0) |
| Scout-Detail: Als Location speichern | Button „Als Location speichern" (SVG-Pin-Icon) in der Detailansicht; speichert den Scout-Standpunkt via POST `/preview-alignment` (save:true) als neue Location (US-83) |
| Scout-Karten Klick | cursor:pointer auf Scout-Karten (Hover-Hand wie Feed-Karten) |
| Suche | Standortname-Suche (analog Feed-Suche) |

**Pflicht-Regression Scout:**
- [ ] Scout-Tab lädt ohne Fehler
- [ ] ≥1 Scout-Karte sichtbar
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

**Pflicht-Regression Einstellungen:**
- [ ] Slider auf 80% → Feed-Reload → weniger Karten
- [ ] Theme-Umschalter ändert sofort das Erscheinungsbild
- [ ] Theme-Auswahl überlebt App-Reload

---

## 10. Login / Auth

| Funktion | Verhalten |
|----------|-----------|
| Login-Screen | Erscheint wenn nicht eingeloggt |
| Host-Login | Volladmin: Locations anlegen/editieren, Refresh starten |
| User-Login | Lesen + eigene Custom-Locations |
| Session | JWT-Token; überlebt App-Reload |
| Logout | Manuell in Einstellungen |

**Pflicht-Regression Auth:**
- [ ] Nicht-eingeloggter Zugriff → Login-Screen erscheint
- [ ] Login als Host → alle Tabs erreichbar
- [ ] Geschützte Endpoints ohne Token → HTTP 401

---

## 11. Backend-Endpoints (freigegebene API)

| Endpoint | Methode | Funktion |
|----------|---------|----------|
| `/health` | GET | Status + locations_count + version |
| `/locations` | GET | Alle Locations (Basis + Overrides + Custom) |
| `/locations/{id}` | PATCH | Location editieren (auth: host) |
| `/opportunities` | GET | 14-Tage-Feed; params: `min_score`, `days` |
| `/calendar` | GET | 365-Tage-Kalender |
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
| US-83 | Scout-Detail + „Als Location speichern" (In Progress) |
| US-95 | Chancendetails: Buttons kleiner, Karte größer |
| US-98 | Bauhaus-Redesign Epic (übergeordnet) |
| US-103 | Karten-Marker & FOV-Legende im Bauhaus-Stil |
| BUG-21 | Brennweiten-Eingabe: kein Komma auf iOS |

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
| 2026-06-28 | US-104 | Scout-Karten auf Feed-Design umgestellt (ScoreRing, Himmelsrichtung, Tag-Chips) |
| — | US-70 | Scout-Tab: Mond-Alignment-Ephemeride |
| — | US-66 | Login + Auth (Host/User) |
| — | BUG-42 | Custom Locations: kein 📍-Emoji in Namen |
| — | BUG-41 | Street-View-Button nur bei Azimut sichtbar |
| — | BUG-38/39 | Koordinaten-Sektion: Overflow + Strich gefixt |
