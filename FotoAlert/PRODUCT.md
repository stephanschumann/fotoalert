# FotoAlert – Product Requirements (Lebende Produktdokumentation)

> **Zweck:** Kanonischer Ist-Stand aller freigegebenen Funktionen.  
> **Pflege:** Nach jedem abgeschlossenen Ticket aktualisieren (vor „Done").  
> **Regression:** Diese Datei ist die Grundlage für den Regressionstest nach jeder Änderung.  
> Zuletzt aktualisiert: 2026-07-11 · Basis: abgeschlossene Tickets bis BUG-65, US-09, BUG-56, US-113, US-108, US-07, US-107, US-79, US-102, US-100, US-96, BUG-42, BUG-47, BUG-48, BUG-49, BUG-50, BUG-51, BUG-52, BUG-53, TASK-67 (Etappe 4: „Nur manuell prüfbar"-Restliste, Abschnitt 15)

---

## 1. App-Übersicht

FotoAlert ist eine PWA + iOS-App, die Fotografen automatisiert berechnet, **wann** ein bestimmtes Motiv (Turm, Brücke, Schloss) von **welchem Standort** aus astronomisch wertvoll ist — Mond oder Sonne im 2°-Fenster um die Motivspitze zur goldenen oder blauen Stunde.

**Technologie-Stack:**
- Frontend: Single-Page-App (`web/index.html`, JS + CSS inline)
- Backend: FastAPI + Python (`backend/main.py`)
- Datenbank: SQLite (WAL, `backend/data/`)
- Hosting: Hetzner-Server, Deploy via `release.sh` + GitHub Actions
- Auth: signiertes Sitzungs-Token, zwei Rollen: `host` und `user`; TASK-83: Transport per HttpOnly/Secure/SameSite=Lax-Cookie (`fa_session`), nicht mehr per Browser-Speicher/Authorization-Header (siehe Abschnitt 10)

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
| Onboarding (US-21) | 4 Einführungs-Slides (`Onboarding`-Objekt) beim allerersten App-Start; Fortschrittspunkte unten, „Weiter" wird auf Slide 4 zu „Los geht's", ab Slide 2 Zurück-Pfeil links, „Überspringen" oben rechts auf allen Screens außer dem letzten. Erscheint nur einmal (localStorage-Flag `fa_onboarding_seen`), danach nur noch über Glossar aufrufbar. |
| „?"-Header-Button (US-21) | Ganz rechts im Header, öffnet `Glossary.open()`. Seit Korrektur (2026-07-05) optisch identisch zu den übrigen Header-Icons (Suche/Filter/Refresh): gleiche Größe, gleiche graue Grundfarbe (`var(--muted)`), gleiches Hover-Verhalten — keine Sonderstellung mehr (vorherige Kreis-Outline in Akzentfarbe zurückgenommen). |
| Glossar-Overlay (US-21) | Bottom-Sheet (22px Radius, gleiches Muster wie Filter-/Detail-Sheet) mit Suchfeld oben und Accordion-Einträgen, gruppiert nach Einführung/Scores/Kernbegriffe. Erster Eintrag „Onboarding erneut ansehen" startet die Slides neu. Texte werden aus `ScoreInfo._texts`/`ElementInfo`-Objekten wiederverwendet (eine Pflegestelle statt Duplikat). Seit Scope-Erweiterung (2026-07-05, US-21) zusätzlich 2 Einträge: „Wie unterscheiden sich Feed, Kalender und Scout?" (Text seit Korrektur 2026-07-05 fachlich präzisiert: Feed = 14-Tage-Feed, Kalender unverändert, Scout errechnet eigene Chancen unabhängig von Nutzer-Standorten, Betaversion, nicht verifiziert) und „Wie funktionieren die Filter?". |
| Inline-ⓘ-Erklärungen (`.el-info-btn`, US-21) | 14px, dezent grau (`var(--muted)`), Hover→Gold. Bestehende 5 Stellen: Schwierigkeitsgrad-Badge, Event-Typ, Verifikations-Badge, Filter-Gruppen, Kartenlegende. Seit Scope-Erweiterung (2026-07-05) zusätzlich 10 Stellen im Chancen-Detail (Wetterwerte, Ideales Zeitfenster, Wolken/Kompass-Ausrichtung, Karte & Blickwinkel, Kompositions-Analyse, Koordinaten, Himmelsposition/Astronomie) und Location-Detail (Fotograf-Standort/Motiv/Ausrichtung — 3 Sektionen mit demselben Erklärtext, Nächste Events, Verifikationsbereich). Kartenlegende (`.map-legend-info-btn`) im gleichen Zug kleiner (22px statt 44px) und dezenter gemacht; Hover-Verhalten unverändert. Legendentext (`ElementInfo._mapLegendData()`) seit drittem Testdurchlauf (2026-07-05) nur noch 3 Punkte: Pin-Symbol (mit Inline-SVG-Beispiel), Kartenebenen-Umschalter, GPS-Zentrier-Button — der Fotograf-Standort/Motiv/Sichtachse-Absatz wurde komplett entfernt (auf dieser Übersichtskarte nicht relevant, nicht nur textlich korrigiert; verursachte zudem ein Block-in-Inline-Rendering-Problem, siehe Ticket). Layer-Switcher und GPS-Button sind beide verifiziert Teil des Haupt-Karten-Tabs (`#page-map`), keine Anzeige-Bugs gefunden. |

**Pflicht-Regression globale UI:**
- [ ] Tab-Wechsel funktioniert (alle 5 Tabs) (Teilabdeckung automatisiert: `run_frontend_check.py`-VIEWS-Loop deckt Feed/Karte/Orte/Einstellungen; Kalender-/Scout-Modus zusätzlich über `_check_calendar_view`/`_check_scout_mode` (TASK-67 Etappe 3, Playwright-Code geschrieben — lokaler Browser-Lauf durch Stephan noch ausstehend, Sandbox hat kein Playwright/Chromium); „+"-Tab bereits über TASK-66 `_check_location_create` abgedeckt)
- [ ] Kein Tab zeigt seinen Inhalt doppelt
- [ ] Kein Sheet öffnet sich ungewollt beim Laden
- [ ] Theme-Wechsel (hell/dunkel) ändert alle Farbtokens konsistent
- [ ] Alle Icons sichtbar in Safari (SVG `<use>` + `currentColor`-Attribute auf `<g>`, nicht per CSS-Klasse)
- [ ] Onboarding erscheint beim ersten Start, nicht mehr nach Reload/zweitem Start
- [ ] „?"-Button im Header immer erreichbar, öffnet Glossar (automatisiert: `run_frontend_check.py::_check_help_glossary`, TASK-67 Etappe 3, lokal grün bestätigt)
- [ ] Glossar: Suche filtert Einträge live, Accordion klappt auf/zu, „Onboarding erneut ansehen" startet die Slides neu
- [ ] Glossar zeigt die 2 neuen Einträge (Filter-Logik, Feed/Kalender/Scout-Unterschied)
- [ ] Alle 15 ⓘ-Stellen (5 bestehend + 10 neu) öffnen das `ElementInfo`-Overlay mit dem korrekten Text
- [ ] Kartenlegende-ⓘ wirkt klein/dezent im Ruhezustand, wird bei Hover gold

---

## 3. Feed-Tab (14-Tage-Chancen)

**Was der Nutzer sieht:** Score-sortierte Liste von Foto-Chancen für die nächsten 14 Tage.

| Funktion | Verhalten |
|----------|-----------|
| Chance-Karten | Jede Karte zeigt: Titel, Datum/Uhrzeit, Location-Name, Score-Ring (farbcodiert), Event-Typ |
| Score-Ring | Kreisring, Füllgrad = Score (0–100%), Farbe: grün ≥80%, orange 50–79%, rot <50% |
| Wetter-Badge | Tag-Chip auf Feed-Karten wenn Wetter bekannt (`weather_status: "ok"` bzw. `weather_score > 0`). Wird das Wetter einer gerade geänderten/neuen Location gerade nachgeladen, zeigt die Karte stattdessen ehrlich „Wetter wird nachgeladen" (Uhr-Icon). Chancen weiter als ~3 Tage in der Zukunft (`weather_status: "none"`) zeigen kein Wetter-Badge (kein „lädt ewig"). (BUG-44, US-106) |
| Golden Cloud Score (US-07) | Jede Foto-Chance hat ein Feld `golden_cloud_score` (0.0–1.0): bewertet wie gut Wolken das Licht bei Goldener/Blauer Stunde verstärken könnten — hoher Score = dramatische Struktur zu erwarten. Berechnung in `backend/weather.py` (`calculate_golden_cloud_score`), Feld in `schemas.py` definiert. Im Frontend Filter-Slider „Bewölkungs-Qualität" (0–100%) — nur Chancen ab diesem Schwellwert werden gezeigt. (US-07) |
| Wetter sofort nach Standort-Änderung (US-106) | Nach dem Verschieben/Anlegen einer Location wird das Wetter gezielt nur für diese Location nachgeladen (Sekunden, nicht bis zu 3 h). Das „wird aktualisiert"-Banner verschwindet erst, wenn Foto-Chancen UND echtes Wetter stehen — nicht schon beim Platzhalter. Schlägt das Wetter-Nachladen fehl, bleibt die Location als „wird aktualisiert" markiert und wird beim nächsten Lauf erneut versucht. Seit TASK-73 (2026-07-13) wird bei diesem gezielten Nachladen zusätzlich das Dunst-/Aerosolsignal parallel mitgeholt (nicht mehr nur beim regulären 3-Stunden-Cronlauf) — die erste Himmelsröte-Karte einer neuen/geänderten Location enthält das Dunst-Signal damit sofort statt erst nach bis zu 3 Stunden; schlägt nur der Aerosol-Abruf fehl, bleibt das bestehende Verhalten (reiner Wolken-Check) unverändert erhalten. |
| Sichtachsen-Projektion für Himmelsröte & Goldene Wolken (US-131) | Der für Himmelsröte (RED_SKY) genutzte Dunst-/Wolkenwert und der für Goldene Wolken (GOLDEN_CLOUDS) genutzte Wolkenwert werden nicht mehr am Standort des Fotografen abgefragt, sondern an einem 30 km entlang der Sichtachse projizierten Punkt — für Himmelsröte in Gegenrichtung der Sonne (Antisolarpunkt), für Goldene Wolken in Sonnenrichtung; beide getrennt berechnet (keine geteilte Wolken-Score-Berechnung mehr), identisch für den schnellen Einzelabruf-Pfad (US-106) und den regulären Cronlauf. Schlägt der Abruf am projizierten Punkt fehl, gibt es **keinen** Fallback auf den Fotografen-Standort — die betroffene Karte gilt schlicht als „Signal nicht verfügbar". Die allgemeine Wetteranzeige (Temperatur, Niederschlag, Wind, `weather_score`) bleibt davon unberührt und weiterhin am Fotografen-Standort verankert. Zusätzlich wurde die externe Wetter-API-Anbindung gedrosselt (`WEATHER_API_MAX_CONCURRENT_REQUESTS = 5` gleichzeitige Requests + `WEATHER_API_REQUEST_PACING_SECONDS = 0.15` Pacing pro Slot), nachdem Live-Messungen ohne Drosselung ein signifikantes Rate-Limiting der externen API (bis zu 31 % HTTP 429) gezeigt hatten. |
| Rote Wolken (RED_CLOUDS, US-132) | Dritter, eigenständiger Wolkenstimmungs-Event-Typ neben Goldene Wolken und Himmelsröte: Steht die Sonne bereits unter dem Horizont (Blaue-Stunde-Fenster, Sonnenhöhe -6° bis -4°), können hohe Wolken (Cirrus) noch aus Sonnenrichtung angestrahlt werden und rot/purpurn statt golden glühen. Auslösebedingung: ausreichend hohe Wolken (`cloud_cover_high_pct >= 20`) UND keine komplett verstellende tiefe Bewölkung (`cloud_cover_low_pct < 30`) UND Motiv-Azimut innerhalb ±30° des Sonnenazimuts (nicht Gegenrichtung wie bei Himmelsröte). Erscheint sowohl abends als auch morgens — dafür wurde ein neuer, zur bestehenden „Blaue Stunde" (Abend) symmetrischer Event-Typ „Blaue Stunde Morgen" eingeführt, der ebenfalls erstmals einen Sonnenazimut/-höhe berechnet (vorher nur intern als Zeitfenster genutzt). Eigener Erklärtext im Detail-Sheet, eigener Filter-Chip, eigenes Icon (rotes Wolken-Icon) — von Himmelsröte trotz gleicher Rot-Farbe (beide „Sonne unter Horizont") durch das Icon unterscheidbar (Wolke vs. Bogen/Himmelsfläche). |
| Reihenfolge bei Standort-Änderung: Feed+Wetter sofort, Kalender im Hintergrund (US-106 Nachbesserung) | Nach dem Verschieben einer Location werden zuerst die sichtbaren Foto-Chancen + ihr Wetter berechnet; sobald beides steht, verschwindet das „wird aktualisiert"-Banner in Sekunden. Der vollständige Jahres-Kalender dieser Location wird **danach im Hintergrund** nachgerechnet, ohne das Banner aufzuhalten — der Kalender-Tab dieser Location kann dabei ein paar Minuten noch den alten Stand zeigen (bewusst akzeptiert). Ein Fehler beim Hintergrund-Kalender nimmt die bereits erfolgte Freigabe nicht zurück. Es läuft nie mehr als eine schwere Berechnung gleichzeitig; eine zweite Änderung während der laufenden Kalender-Rechnung wird gemerkt und danach automatisch nachgeholt. |
| Feed-Filter | Filter-Panel (Sheet) mit 9 Kriterien; wirkt auf alle Ansichten (Details siehe Sektion 3a) |
| Mondaufgang-Events | Eigenständige Karten im Feed mit Typ `"Mondaufgang"`, Score-Ring, Uhrzeit und Location (US-79); werden nur angezeigt wenn Mond ≤ 35° zur Sichtachse liegt (vordere Zone) — seitlich oder hinter dem Fotografen werden unterdrückt (US-108) |
| Monduntergang-Events | Eigenständige Karten im Feed mit Typ `"Monduntergang"`, Score-Ring, Uhrzeit und Location (US-79); werden nur angezeigt wenn Mond ≤ 35° zur Sichtachse liegt (vordere Zone) — seitlich oder hinter dem Fotografen werden unterdrückt (US-108) |
| Sichtachsen-Check-Pille (US-09) | Auf der Feed-Karte zeigt eine Pille (Augen-Icon + farbiger Text) den Hinderniserkennungs-Status der Sichtachse zwischen Fotostandort und Motiv: **Grün** „Frei", **Orange** „Teilweise verdeckt", **Rot** „Blockiert", **Grau** „Nicht geprüft". Gilt für Sonne-/Mond-/Himmelsrichtung-Ereignisse UND Golden-Hour-/Himmelsröte-Wetter-Chancen. „Nicht geprüft" ist ein ehrlicher Unsicherheits-Status bei fehlenden Höhen-/Gebäudedaten — **wird niemals fälschlich als „Frei" angezeigt.** ⓘ-Erklärtext neben der Pille. |
| Alert-Banner | Sichtbar wenn relevante Chancen heute oder morgen |
| Tipp: Chance antippen | Öffnet Detail-Sheet (Pflicht: Detail schließt mit Overlay-Tap) |
| Event-Typ-Verteilung | Round-Robin-Cap im `/opportunities`-Endpoint: alle Event-Typen (Goldene Stunde, Blaue Stunde, Mondaufgang, Monduntergang, Milchstraße) sind proportional im Feed vertreten — kein Typ verdrängt einen anderen vollständig (BUG-48) |
| Leer-State | Wenn keine Chancen passen: Hinweis-Text, kein Absturz |
| Kalender-Modus | Button „Jahreskalender" im Feed schaltet auf Monatskalender-Ansicht um; Tap auf Kalender-Event sucht passenden Feed-Eintrag (location_id + ±1h) und übergibt vollständiges Objekt (inkl. weather_details) an Detail-Sheet (BUG-44) |

**Pflicht-Regression Feed:**
- [ ] Mindestens 1 Karte sichtbar (bei min_score 0.2) (automatisiert: `test_task67_feed_regression.py`, prüft `main._filter_feed()` direkt — Karten-Rendering selbst bleibt manuell/Etappe 3)
- [ ] Chance antippen → Detail-Sheet öffnet (automatisiert: `run_frontend_check.py::_check_event_detail_from_feed_card`, TASK-67 Etappe 3, lokal grün bestätigt)
- [ ] Overlay antippen → Sheet schließt sich
- [ ] Filter-Sheet öffnet und schließt
- [ ] Jahreskalender-Modus lädt fehlerfrei und zeigt Termine (automatisiert: `run_frontend_check.py::_check_calendar_view`, TASK-67 Etappe 3, übernommen aus TASK-69 AK1, lokal grün bestätigt)
- [ ] Score-Ring korrekt (visuelle Überprüfung: 75% = ring 3/4 gefüllt)
- [ ] Karten nicht doppelt vorhanden (automatisiert: `test_task67_feed_regression.py`, prüft `main._dedup_best_per_day()`/`_filter_feed()`)
- [ ] Routine-Events-Filter entfernt Goldene/Blaue-Stunde-Karten
- [ ] Filter-Chips „Mondaufgang" / „Monduntergang" filtern Feed korrekt (US-79)
- [ ] Mondaufgang-/Monduntergang-Events erscheinen als eigenständige Karten im Feed (US-79) (automatisiert: `test_us79_moon_rise_set.py`, Event-Erzeugung + Serialisierung geprüft — Karten-Rendering selbst bleibt manuell/Etappe 3)
- [ ] Feed enthält sowohl Goldene Stunde als auch Blaue Stunde (nicht nur Mond-Events) — Round-Robin-Cap (BUG-48) (automatisiert: `test_task67_feed_regression.py`, Kernszenario: dominanter Typ verdrängt seltenen Typ nicht aus dem Cap)
- [ ] Feed-Karten zeigen Sichtachsen-Check-Pille (Augen-Icon + Grün/Orange/Rot/Grau je nach Status) für Sonne/Mond/Himmelsrichtung UND Golden-Hour/Himmelsröte-Karten (US-09) (Datengarantie automatisiert: `test_us09_sightline.py` — Pillen-Darstellung selbst bleibt manuell/Etappe 3)
- [ ] Fehlen Höhen-/Gebäudedaten: Pille zeigt „Nicht geprüft" (grau), niemals „Frei" (US-09) (automatisiert: `test_us09_sightline.py`)

---

## 3a. Filter (BUG-46 — vollständige Spezifikation)

Der Filter hat 11 Kriterien. Vier davon haben **Drei-Zustände** (Off → Einschließen → Ausschließen → Off):
Eventtyp, Tageszeit, Schwierigkeit, Kategorie.
Seit BUG-46 haben auch Verifikationsstatus und Mindest-Bewertung Drei-Zustände.
Seit US-09 hat auch der Sichtachsen-Check-Status Drei-Zustände.
Seit US-129 hat auch „Hat Beispielbild" Drei-Zustände.

### Kriterien und ihre Zustände

| Kriterium | Drei-Zustände | Anmerkung |
|---|---|---|
| **Eventtyp** | Ja (Off → nur zeigen → ausblenden → Off) | Gilt für Chancen-Feed, Kalender, Scout, Karte |
| **Tageszeit** | Ja (Off → nur zeigen → ausblenden → Off) | Nur Chancen-Feed + Kalender + Scout; **ausgegraut auf Karte + Locations-Tab** |
| **Mindest-Wahrscheinlichkeit** | Nein (Slider 0–100%) | Nur Chancen-Feed + Kalender + Scout; **ausgegraut auf Karte + Locations-Tab**. Standardwert seit US-119: **70%** (vorher 0% = „Alle"); gilt geteilt für Feed/Kalender/Scout. Bestandsnutzer mit abweichendem gespeicherten Wert wurden einmalig auf 70% zurückgesetzt (Migrations-Flag `fotoalert_filters_v119_migrated`); ein danach selbst gewählter Wert bleibt dauerhaft erhalten |
| **Brennweite** | Nein (Dual-Handle-Slider) | Gilt für alle Ansichten inkl. Karte + Locations-Tab (seit TASK-47: jede Location hat eine automatisch berechnete Brennweiten-Empfehlung als eigene Eigenschaft, filtert dort aktiv mit — **Klärung Stephan, 2026-07-12**: Code ist korrekt, ältere Doku-Zeilen zu „ausgegraut" waren nach TASK-47 nicht mehr nachgezogen) |
| **Schwierigkeit** | Ja (Off → nur zeigen → ausblenden → Off) | Gilt für alle Ansichten inkl. Karte + Locations-Tab |
| **Kategorie** | Ja (Off → nur zeigen → ausblenden → Off) | Gilt für alle Ansichten inkl. Karte + Locations-Tab |
| **Mindest-Bewertung** | Ja (BUG-46): Off → ≥ N Sterne (gold) → < N Sterne (rot) → Off | Gilt für alle Ansichten |
| **Entfernung (GPS)** | Nein (Einfach-Auswahl) | Gilt für alle Ansichten inkl. Karte + Locations-Tab (BUG-51). GPS-Dialog erscheint pro Session maximal einmal — laufende Anfragen werden dedupliziert via `Filter._gpsPromise`-Caching (BUG-52) |
| **Verifikationsstatus** | Ja (BUG-46): „Geprüfte" hat Off → nur Geprüfte → alle außer Geprüfte → Off; andere Chips (Nicht geprüft, Probleme) togglen einfach | Gilt für alle Ansichten inkl. Karte |
| **Hat Beispielbild** (US-129) | Ja: Off → Nur mit Bild (Rahmen `--accent`) → Nur ohne Bild (Rahmen `--red`, Label „Ohne Bild") → Off | Gilt für Locations-Tab, Karte, Chancen-Feed, Kalender (Lookup der Location über `location_id`); **ausgegraut bei Entdecken/Scout** (Scout-Chancen haben kein `location_id`-Äquivalent); ⓘ-Erklärtext am Filter-Chip |
| **Sichtachsen-Check** (US-09) | Ja: Off → nur diesen Status zeigen → diesen Status ausschließen → Off; Statuswerte: Frei / Teilweise verdeckt / Blockiert / Nicht geprüft | Gilt für Chancen-Feed, Kalender, Scout, Locations-Tab, Karte (Sichtachsen-Ergebnis ist Location-Eigenschaft); ⓘ-Erklärtext am Filter-Chip |

**Geklärt (TASK-67 Etappe 6, Stephan 2026-07-12):** Frühere Doku-Zeilen führten Brennweite
als „ausgegraut auf Karte + Locations-Tab" — das war seit TASK-47 nicht mehr aktuell. Der
Code (`web/index.html` ~Zeile 3576 `dimFocalOnMap = false`, Filterlogik ~5068-5073 und
~3046-3049) filtert Karte UND Locations-Tab bewusst aktiv nach Brennweite, weil seither
jede Location eine automatisch berechnete Brennweiten-Empfehlung als eigene Eigenschaft
hat. Entscheidung: Code ist korrekt, Tabellen oben wurden entsprechend korrigiert.

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

**Hat Beispielbild (US-129):**
- Rahmen `--accent` (Einschließen, „Hat Bild"): zeigt nur Locations/Chancen, deren Location ein Beispielbild hat (`image_url` gesetzt)
- Rahmen `--red` (Ausschließen, Label wechselt zu „Ohne Bild"): zeigt nur Locations/Chancen ohne Beispielbild
- Off: keine Filterung
- Für Chancen im Feed/Kalender bestimmt die zugehörige Location (`location_id`-Lookup) den Bildstatus; eine Chance ohne auflösbare Location zählt als „ohne Bild" (eindeutige Zuordnung)
- Bei Entdecken/Scout ist der Chip ausgegraut ohne Wirkung — Scout-Chancen haben kein `location_id`-Feld

### Ausgrauen-Verhalten (BUG-46)

Kriterien ohne Wirkung in der aktuellen Ansicht werden visuell gedimmt (opacity 0.45, pointer-events none) — sie bleiben sichtbar, sind aber nicht bedienbar:

| Ansicht | Ausgegraut |
|---|---|
| **Karte** | Tageszeit, Mindest-Wahrscheinlichkeit |
| **Locations-Tab** | Eventtyp, Tageszeit, Mindest-Wahrscheinlichkeit |
| **Chancen-Feed / Kalender** | Nichts ausgegraut |
| **Scout (Entdecken)** | Hat Beispielbild (US-129, kein `location_id`-Äquivalent bei Scout-Chancen) |

### Wirkungs-Übersicht nach Ansicht

| Kriterium | Chancen-Feed | Kalender | Scout | Locations-Tab | Karte |
|---|---|---|---|---|---|
| Eventtyp | ✓ | ✓ | ✓ (body_name) | — (ausgegraut) | ✓ (via Feed-Daten) |
| Tageszeit | ✓ | ✓ | ✓ (session) | — (ausgegraut) | — (ausgegraut) |
| Wahrscheinlichkeit | ✓ | ✓ | ✓ | — (ausgegraut) | — (ausgegraut) |
| Brennweite | ✓ | ✓ | ✓ | ✓ | ✓ |
| Schwierigkeit | ✓ | ✓ | — | ✓ | ✓ |
| Kategorie | ✓ | ✓ | — | ✓ | ✓ |
| Mindest-Bewertung | ✓ | ✓ | — | ✓ | ✓ |
| Entfernung (GPS) | ✓ | — | ✓ | — | ✓ |
| Verifikation | ✓ | ✓ | — | ✓ | ✓ |
| Hat Beispielbild (US-129) | ✓ | ✓ | — (ausgegraut) | ✓ | ✓ |
| Sichtachsen-Check (US-09) | ✓ | ✓ | ✓ | ✓ | ✓ |

**Pflicht-Regression Filter (BUG-46):**
- [ ] Filter-Badge zeigt korrekte Anzahl aktiver Kriterien (automatisiert: `run_frontend_check.py::_check_filter_badge_count`, TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12)
- [ ] Bewertungs-Chip: Off → gold „≥ N" → rot „< N" → Off (drei Tipp-Schritte) (automatisiert: `run_frontend_check.py::_check_rating_chip_tristate`, TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12)
- [ ] Verifikation „Geprüfte": Off → gold → rot → Off (drei Tipp-Schritte) (automatisiert: `run_frontend_check.py::_check_filter_tristate_and_dimming`, TASK-67 Etappe 3, Referenzmuster verifiziert, lokal grün bestätigt)
- [ ] Tageszeit, Wahrscheinlichkeit auf Karte ausgegraut, Brennweite filtert dort aktiv mit (kein Ausgrauen mehr, s. Klärung 2026-07-12) (Teilabdeckung: Tageszeit automatisiert in `_check_filter_tristate_and_dimming` (Etappe 3, lokal grün bestätigt); Wahrscheinlichkeit automatisiert in `_check_wahrscheinlichkeit_dimming` (TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12); Brennweite-Wirkung auf der Karte noch nicht separat automatisiert getestet)
- [ ] Eventtyp, Tageszeit, Wahrscheinlichkeit auf Locations-Tab ausgegraut, Brennweite filtert dort aktiv mit (Teilabdeckung: Tageszeit automatisiert in `_check_filter_tristate_and_dimming` (Etappe 3, lokal grün bestätigt); Wahrscheinlichkeit automatisiert in `_check_wahrscheinlichkeit_dimming` (TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12); Eventtyp weiterhin offen; Brennweite-Wirkung auf dem Orte-Tab noch nicht separat automatisiert getestet)
- [ ] Karte zeigt nach Schwierigkeits-Filter nur passende Pins (automatisiert: `run_frontend_check.py::_check_map_pin_filtering`, TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12)
- [ ] Karte zeigt nach Kategorie-Filter nur passende Pins (automatisiert: `run_frontend_check.py::_check_map_pin_filtering`, TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12)
- [ ] Karte zeigt nach Verifikations-Filter nur passende Pins (automatisiert: `run_frontend_check.py::_check_map_pin_filtering`, TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12)
- [ ] Sichtachsen-Check-Chip: Off → nur diesen Status → diesen Status ausschließen → Off (drei Tipp-Schritte, US-09) (automatisiert: `run_frontend_check.py::_check_sightline_chip_tristate_and_effect`, TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12)
- [ ] Sichtachsen-Check-Filter wirkt in allen Ansichten (Feed, Kalender, Scout, Karte, Locations-Tab) — nicht ausgegraut (US-09) (Teilabdeckung automatisiert: `_check_sightline_chip_tristate_and_effect` prüft Nicht-Ausgegraut-Sein auf Feed/Karte/Locations-Tab sowie realen Filter-Effekt auf der Karte; Kalender/Scout und der volle Effekt-Nachweis auf Feed/Locations bleiben aufgrund identischer, bereits an anderer Stelle geprüfter Codepfade unautomatisiert, TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12)
- [ ] „Hat Beispielbild"-Chip: Off → gold „Hat Bild" → rot „Ohne Bild" → Off (drei Tipp-Schritte, US-129) (automatisiert: `run_frontend_check.py::_check_has_image_chip_tristate_and_effect`, TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12)
- [ ] „Hat Beispielbild" wirkt auf Locations-Tab, Karte, Feed und Kalender (nur mit/nur ohne Bild korrekt gefiltert); im Feed/Kalender additiv UND-kombinierbar mit den übrigen Chancen-Filtern (US-129) (Teilabdeckung automatisiert: `_check_has_image_chip_tristate_and_effect` prüft den Effekt nur auf dem Orte-Tab gegen `Filter.applyToLocations()`; Karte/Feed/Kalender bleiben offen, TASK-67 Etappe 6, lokal grün bestätigt 2026-07-12)
- [ ] „Hat Beispielbild" bleibt bei Entdecken/Scout ausgegraut ohne Wirkung (US-129) (Test geschrieben: `run_frontend_check.py::_check_has_image_chip_tristate_and_effect`, TASK-67 Etappe 6, lokal ausgeführt 2026-07-12 — **schlägt aktuell fehl**, echter App-Bug gefunden und als **BUG-76** erfasst: die Ausgrauen-Bedingung `App.current === 'scout'` kann nie zutreffen, Scout ist kein eigener Reiter. Bleibt rot bis BUG-76 behoben ist.)

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
| Sonnenaufgang in Astronomie-Sektion | Zeigt Uhrzeit (Berliner Zeit) + Azimut in Grad, wenn vorhanden (US-107); fehlt kommentarlos wenn null (z.B. Polarsommer) |
| Sonnenuntergang in Astronomie-Sektion | Analog: Uhrzeit (Berliner Zeit) + Azimut in Grad, wenn vorhanden (US-107); fehlt kommentarlos wenn null |
| Live-Astro-Übersicht aus Ereignis öffnen | Übernimmt exakt Datum + Ortszeit (Berlin) des Ereignisses (nicht „heute"); Zeit-Schieberegler startet zentriert auf der Ereigniszeit und lässt sich ±12h davon navigieren, ohne dass sich das Fenster verschiebt; gilt für Feed-/Kalender-Chancen mit gespeichertem Ort und für Entdecken-Modus-Chancen ohne Ort (BUG-75); Live-Astro direkt aus der Orts-Übersicht („jetzt"-Modus) bleibt unverändert: aktuelles Datum/Uhrzeit, läuft automatisch weiter |
| Zeitanzeige an der Zeitleiste (Live-Astro) | Zeigt neben der Uhrzeit zusätzlich das Datum, Format „TT.MM. · HH:MM Uhr" (z.B. „18.07. · 22:17 Uhr"); gilt einheitlich in allen Anzeige-Situationen: Ereignis-Öffnen, Schieberegler-Bedienung, Pin-Ziehen und „jetzt"-Live-Modus (BUG-75-Nachtrag) |
| Koordinaten-Sektion | Kein Overflow-Problem (BUG-38 gefixt); Labels korrekt ausgerichtet |
| Sheet-Header | Kein blaugrauer Strich links (BUG-39 gefixt) |
| Karte & Blickwinkel im Vollbild | Sobald die FOV-Karte Motivkoordinaten hat, zeigt sie ein Vollbild-Symbol (oben rechts); antippen öffnet dieselbe Karte (Beobachter-Pin, Motiv-Pin, Sichtachse, Sichtfeld-Kegel) bildschirmfüllend, rein zum Ansehen — Pins lassen sich dort NICHT verschieben, Zoomen/Verschieben der Karte funktioniert normal. Kreuz oben oder Antippen des abgedunkelten Hintergrunds schließt zurück zur Detailansicht. Gilt identisch in allen vier Einstiegspunkten: Chancen-Detail, Kalender-Detail, Scout-Detail, Location-Detail (US-114). Ohne Motivkoordinaten erscheint kein Vollbild-Symbol (wie schon der Hinweistext statt Karte). Getrennt vom Bearbeiten-Vollbild-Overlay (US-87), das nur im Location-Detail-Editiermodus zum Pin-Setzen dient. |
| Sichtfeld-Kegel-Verlängerung (US-85) | Die gefüllte Kegelfläche (Standort→Motiv) zeigt zusätzlich zwei gestrichelte Verlängerungslinien der beiden Kegelkanten über das Motiv hinaus bis zur doppelten Entfernung (gleiche Farbe/Stärke wie der Kegelrand, eigenes gleichmäßiges Strichmuster, keine Fläche — nur Linien, zur Unterscheidung von der bestehenden Sichtachsen-Linie). Kegel + Verlängerung werden als eine Einheit verwaltet, damit beim Verstellen von Brennweite/Sensor/Ausrichtung keine alten Verlängerungslinien stehen bleiben. Beim erstmaligen Aufbau der Karte für einen Standort/eine Chance zoomt die Karte automatisch so weit heraus, dass die komplette Verlängerung sichtbar ist (nicht bei jedem Reglerwechsel). Gilt identisch in allen vier Einbindungen: Location-Detail/Chancen-Detail, jeweils normal + Vollbild. |
| Sichtachsen-Check-Pille (US-09) | Im Detail-Sheet (analog Feed-Karte) erscheint dieselbe Pille (Augen-Icon + Grün/Orange/Rot/Grau) mit dem Hinderniserkennungs-Status der Sichtachse. Zusätzlich wird die bestehende Sichtachsen-Linie/Kompass-Darstellung (FOV-Karte + Kompass-Diagramm bei Golden-Hour/Himmelsröte, US-111) im Linienstil an den Status angepasst: **durchgezogen** = Frei, **gestrichelt** = Teilweise verdeckt, **unterbrochen** = Blockiert, **gepunktet** = Nicht geprüft. ⓘ-Erklärtext neben der Pille. Gilt für alle Einstiegspunkte (Feed, Kalender, Scout, Location-Detail). |
| Sichtachsen-Check-Auslöser | Die Sichtachsen-Prüfung läuft automatisch einmalig beim Anlegen/Ändern einer Location (Raycast über Höhendaten OpenTopoData + Gebäudedaten OSM/Overpass). Zusätzlich manuell auslösbar über den neuen Menüpunkt „Sichtachsen aktualisieren" im Location-Detail (Orte-Tab, siehe Abschnitt 7). Ergebnis wird je Location gespeichert, nicht bei jedem Feed-Aufruf neu berechnet. |

**Pflicht-Regression Detail:**
- [ ] Sheet öffnet sich von unten (slide-up Animation)
- [ ] Alle 12 Sektionen vorhanden — **keine Sektion doppelt**
- [ ] Beim Öffnen: alle Sektionen eingeklappt
- [ ] Close-Button erreichbar (Safe Area, kein Overlap mit Status Bar)
- [ ] FOV-Karte lädt (Leaflet) und zeigt Verbindungslinie; Zielring-Marker (Ring + Ticks + Mittelpunkt, gold) sichtbar; Legende zeigt Zielring-Icon (US-103)
- [ ] FOV-Karte mit Motivkoordinaten zeigt Vollbild-Symbol; Antippen öffnet bildschirmfüllende Karte mit Pins + Sichtachse + Sichtfeld-Kegel, Pins darin nicht verschiebbar, Zoomen/Verschieben normal, Kreuz + Hintergrund-Tap schließen zurück (US-114)
- [ ] Sichtfeld-Kegel zeigt gestrichelte Verlängerung der beiden Kegelkanten über das Motiv hinaus (bis doppelte Entfernung); Verstellen von Brennweite/Sensor/Ausrichtung ersetzt Kegel + Verlängerung gemeinsam ohne stehenbleibende alte Linien; initialer Kartenaufbau zoomt automatisch auf die komplette Verlängerung, Reglerwechsel zoomt nicht neu; identisch in allen vier Einbindungen (Location-/Chancen-Detail, normal + Vollbild) (US-85)
- [ ] FOV-Karte ohne Motivkoordinaten zeigt kein Vollbild-Symbol (US-114)
- [ ] „Zum Kalender" → `.ics` Download startet
- [ ] Street-View-Button nur sichtbar wenn Azimut verfügbar
- [ ] Astronomie-Sektion zeigt Mondaufgang + Monduntergang mit Uhrzeit + Azimut (wenn vorhanden) (US-79) (automatisiert: `test_us79_moon_rise_set.py`)
- [ ] Kein Fehler / keine leere Zeile wenn Mondaufgang/-untergang null (US-79) (automatisiert: `test_us79_moon_rise_set.py`)
- [ ] Astronomie-Sektion zeigt Sonnenaufgang + Sonnenuntergang mit Uhrzeit + Azimut in Grad (US-107) (automatisiert: `test_task67_detail_regression.py`, prüft `precompute._serialize()` end-to-end — Anzeige selbst bleibt manuell/Etappe 3)
- [ ] Kein Azimut-Wert wenn `sunrise_utc`/`sunset_utc` null (kein Placeholder „0°") (US-107) (automatisiert: `test_task67_detail_regression.py`)
- [ ] Sichtachsen-Check-Pille sichtbar mit korrekter Farbe/Text (Grün/Orange/Rot/Grau) — in allen vier Einstiegspunkten identisch (US-09) (Datengarantie automatisiert: `test_us09_sightline.py` — Pillen-Darstellung selbst bleibt manuell/Etappe 3)
- [ ] Sichtachsen-Linie in FOV-Karte + Kompass-Diagramm zeigt korrekten Linienstil je Status (durchgezogen/gestrichelt/unterbrochen/gepunktet) (US-09)
- [ ] Fehlende Höhen-/Gebäudedaten → Status „Nicht geprüft" (grau, gepunktet), niemals „Frei" (US-09) (automatisiert: `test_us09_sightline.py`)

---

## 5. Karten-Tab

| Funktion | Verhalten |
|----------|-----------|
| Karte | Leaflet, dunkle Tiles (Carto Dark). Beim allerersten Öffnen des Karten-Tabs einer Sitzung zentriert sich die Karte automatisch auf den aktuellen GPS-Standort mit einem ca. 5-km-Radius-Ausschnitt (breitengradkorrigiert, analog BUG-58-Muster); ist kein GPS möglich, aber schon ein früherer Standort bekannt, wird dieser genutzt; ist gar kein Standort bekannt, bleibt es beim Berlin-Fallback (US-117). Bei jedem weiteren Tab-Wechsel bleibt die Karte unverändert an der zuletzt gewählten Position/Zoomstufe stehen (bestehendes Guard-Verhalten). |
| Marker | ≥10 Pins für gespeicherte Locations; SVG-Tropfen (blau, weißer Kern) im Bauhaus-Stil (US-103) |
| Marker-Tap | Popup mit Location-Name und Kategorie |
| Kartenfilter | Alle location-bezogenen Filterkriterien wirken auf Karten-Pins: Eventtyp (inkl. Ausschließen, BUG-23+BUG-46), Schwierigkeit, Kategorie, Verifikation, Bewertung, Entfernung (GPS), Brennweite (seit TASK-47 Location-Eigenschaft, filtert aktiv mit). Tageszeit und Wahrscheinlichkeit sind auf der Karte ausgegraut (BUG-46) |
| Suche (BUG-82) | Live-Textsuche filtert Karten-Pins nach Name/Beschreibung/Kategorie (identisches Matching wie Orte-Tab, `Filter._matchesSearch()`), kombiniert per UND mit aktiven Chip-Filtern. Eine bereits im Feed/Orte-Tab aktive Suche wird beim Wechsel in den Karten-Tab automatisch mit angewendet, ohne erneute Eingabe. |
| GPS-Zentrierung | Button zentriert Karte auf aktuelle GPS-Position (US-69) |
| Wetter-Overlay (US-112) | Umschalter „aus / Wolken / Niederschlag". Zeigt einen **weichen, fließenden Verlauf** (kein Kachelraster) aus **echten Wettermodell-Daten**: DWD ICON-D2 (~2 km, Stunde 0–48) + DWD ICON-EU (Stunde 48–72) über Deutschland/Österreich/Norditalien, plus MET Norway über Norwegen. Ein **72-Stunden-Schieber** wählt die Vorhersagestunde (Label in Berliner Zeit). Serverseitig wird je Stunde ein PNG gerendert (`backend/calculations/weather_grib.py`, Endpoints `/weather-map` + `/weather-map/png/{field}/{idx}`), im Frontend als `L.imageOverlay` gelegt (`WeatherMap`, zwischen Tiles und Markern). Pflicht-Quellenangabe „Daten: DWD · MET Norway (CC BY 4.0)" unten links. Gratis + kommerziell nutzbar; ersetzt die frühere Open-Meteo-Kacheldarstellung (US-72/BUG-55). Ist die Karte gerade im Neubau, zeigt der Endpoint ehrlich `ready:false` und die App „Wetterdaten werden geladen …" statt zu blockieren. Tippt man auf „Wolken" oder „Niederschlag", zoomt die Karte auf einen **ca. 50-km-Radius um die aktuelle Kartenmitte** bzw. um den zuletzt betrachteten Standort — **nicht** mehr auf die volle Mehrländer-Ansicht (bewusste Änderung an US-112/BUG-55, siehe BUG-58). Die Wetterfläche auf der Karte ist jetzt auch bei leichtem Wetter gut sichtbar, bleibt aber bei echtem Klarwetter bewusst unauffällig (Schwellwert-Deckkraft in `_alpha_curve`/`field_to_png`, `weather_grib.py`, BUG-59). |
| Karten-Bedienleiste (US-112, BUG-62) | Basiskarten-Menü (Nacht/Standard/Satellit) und Wetter-Menü (aus/Wolken/Niederschlag) stehen **nebeneinander** in einer Reihe oben; Zeitachse, GPS-Taste und Zoom-Buttons sitzen am **unteren** Kartenrand → maximale Kartenfläche. Seit BUG-62 zeigen beide Gruppen **Icons statt Textbeschriftung** (Mond-Sichel/Raster/Satellit-Symbol rechts, durchgestrichener Kreis/Wolke/Wolke-mit-Tropfen links, je mit Tooltip), damit sie auch auf schmalen iPhone-Bildschirmen (ab 375px) nicht mehr ineinander laufen. |
| Wetter-Legende (TASK-52) | Die Prozent-Skala für Wolken/Niederschlag sitzt **direkt über dem 72-Stunden-Zeitregler**, unten links (`#map-weather-legend`, `bottom: 100px`) — nicht mehr in der Kartenmitte. Bleibt beim Umschalten Wolken↔Niederschlag an derselben Stelle, überlappt weder Regler noch Quellenangabe. |

**Pflicht-Regression Karte:**
- [ ] Leaflet-Karte lädt (kein weißer/leerer Block)
- [ ] ≥10 Pins sichtbar
- [ ] Pin antippen → Popup erscheint
- [ ] Karte nicht leer nach Theme-Wechsel
- [ ] Wetter-Overlay „Wolken"/„Niederschlag": weicher Verlauf über DE + Norwegen sichtbar (nicht leer), 72-h-Schieber zeigt Berliner Zeit und ändert die Fläche, Quellenangabe sichtbar (US-112) (Teil automatisiert: `test_us112_weather_map.py` deckt die Datenebene ab — Endpoint liefert Frames/PNG-Bytes statt leer, Attribution-String vorhanden, Cache-Verhalten; Grundbedienung Ebenen-Umschalter + Zeit-Schieberegler zusätzlich automatisiert: `run_frontend_check.py::_check_weather_map_controls`, TASK-67 Etappe 3, übernommen aus TASK-69 AK5, lokal grün bestätigt (Etappe 5); ob der Verlauf optisch „weich und gut lesbar" wirkt, bleibt Regel-2-Grenzfall, siehe Example Mapping — manuell)
- [ ] Suche filtert Karten-Pins nach Name/Beschreibung/Kategorie, kombiniert per UND mit Chip-Filtern; eine im Feed/Orte-Tab aktive Suche wird beim Wechsel zur Karte automatisch übernommen (BUG-82)

---

## 6. Quick-Add-Tab (+)

| Funktion | Verhalten |
|----------|-----------|
| Sheet öffnet | Karte + Eingabeformular sichtbar |
| GPS-Button | Browser fragt nach Standort-Erlaubnis; setzt Fotograf-Marker |
| Karte antippen | Setzt Motiv-Marker; Verbindungslinie zwischen Fotograf ↔ Motiv |
| Vollbild-Modus (Anlege-Karte) | Vollbild-Symbol auf der kleinen Anlege-Karte öffnet eine bildschirmfüllende Kartenansicht (analog Bearbeiten-Vollbild US-87, aber Antippen statt Ziehen); bereits gesetzte Punkte + Kartentyp erscheinen sofort im selben Zustand. Im Vollbild verfügbar: Zoomen/Verschieben, Satellit/Standard-Umschalter (US-123), sowie ein Beobachter/Motiv-Umschalter direkt im Header (ohne dafür das Vollbild zu verlassen). Antippen der Karte setzt den jeweils aktiven Punkt. Schließen über „X" übernimmt Position(en) + Kartentyp sofort in die kleine Karte + Koordinatenfelder — ohne das Formular zu speichern (US-124). |
| Koordinaten-Eingabe | Manuell via Textfeld (US-56). Erkennt zusätzlich das aus Apple Maps kopierte Koordinatenformat (Komma als Dezimaltrennzeichen, `°` direkt an der Zahl, Himmelsrichtung N/S/O/W ausgeschrieben nachgestellt) — sowohl deutsch (N/S/O/W) als auch englisch lokalisiert (N/S/E/W), mit oder ohne Leerzeichen vor dem `°`. Gilt gleichermaßen für das Feld „Mein Standort (Fotograf)" und „Motiv (Gebäude / Landmark)" sowie für den „Einfügen"-Button (Zwischenablage) — alle drei nutzen dieselbe Parse-Funktion. Bisher unterstützte Formate (Dezimal mit Punkt, DMS) funktionieren unverändert weiter (BUG-78). Verlässt man ein Koordinatenfeld nach einer vollständigen, gültigen Eingabe (Feld-Blur), schwenkt die kleine Anlege-Karte automatisch zur neuen Position — die aktuell eingestellte Zoomstufe bleibt dabei unverändert (reines Schwenken, kein Zoomsprung). Bei unvollständiger/ungültiger Eingabe oder komplett geleertem Feld bleibt die Karte unverändert stehen (US-133). |
| „Alignments berechnen" | POST `/preview-alignment`; zeigt Preview-Box mit Profil + Alignment-Liste. „Höhenwinkel Spitze" berücksichtigt seit BUG-66 automatisch den echten Geländeunterschied zwischen Fotograf-Standort und Motiv (bisher immer 0,0°, weil dieser Wert in der Vorschau nie ermittelt wurde) — bei Locations ohne nennenswerten Höhenunterschied bleibt der Wert weiterhin nahe 0°. Die Berechnung lief vorher gelegentlich mehrere Sekunden, läuft jetzt durchgängig unter 2 Sekunden (BUG-63); auch bei mehreren gleichzeitigen Anfragen verschiedener Nutzer bleibt der Server responsiv. |
| Ohne Punkte | Toast: „Bitte Standort und Motiv setzen" |
| „Location speichern" | Toast: „✅ Location gespeichert!"; Location erscheint in Orte-Tab. HINWEISE-Feld (`special_notes`) bleibt dabei leer, solange der Nutzer nichts einträgt — kein automatischer Vorbelegungstext mehr (BUG-60; vorher: „Automatisch erfasst via Quick Location Capture."). Seit BUG-64 (Stand 2026-07-06) ist zusätzlich der historische Altbestand auf Produktion bereinigt — 57 zuvor betroffene Bestands-Locations wurden per Cleanup-Lauf geleert (idempotent bestätigt, keine anderen Felder verändert). Seit BUG-67 erscheint die neu gespeicherte Location **sofort ohne App-Neustart** sowohl auf der Karte als auch in der Locations-Liste — auch wenn der Karten-Tab beim Speichern bereits offen war (kein Warten auf den nächsten Tab-Wechsel nötig). Bestehende Marker/Einträge bleiben dabei unverändert sichtbar (keine Duplikate), aktive Kartenfilter wirken nach dem Nachladen weiterhin korrekt. |
| Hinweise-Eingabe in der Anlage-Maske | Im Bereich „Optionale Angaben" gibt es ein Textfeld „Hinweise (Zugang, beste Jahreszeit etc.)" — derselbe Wert (`special_notes`) wie im Bearbeiten-Modus. Eingetragener Text wird beim Speichern übernommen und erscheint sofort in der Hinweise-Sektion der neuen Location; bleibt das Feld leer, wird ganz normal ohne Fehler gespeichert (BUG-65). |
| Beispielbild bereits bei der Neuanlage hochladen | Im Bereich „Optionale Angaben" kann optional bereits beim Anlegen ein Beispielbild ausgewählt werden. Der eigentliche Bild-Upload erfolgt automatisch direkt nach erfolgreichem Speichern der neuen Location (gleiche Validierung/Verkleinerung/Kompression wie beim nachträglichen Hochladen im Bearbeiten-Modus, US-120). Wird kein Bild ausgewählt, wird ganz normal ohne Bild gespeichert (Platzhalter „Noch kein Beispielbild" für den Host) (US-127). Seit BUG-71 bleibt der Bezug zum gerade offenen Anlage-Formular auch über die asynchrone Fotoauswahl hinweg zuverlässig erhalten; geht dieser Bezug ausnahmsweise doch verloren, erscheint immer der Toast „Bitte Location erneut öffnen und Bild noch einmal hochladen" statt eines stillen Abbruchs. Die eigentliche Ursache des ursprünglichen BUG-71-Fehlbilds (Bild-Upload auf iPhone/iOS scheiterte, auf Mac/Safari nicht) lag im Service Worker (`web/sw.js`): dieser fing bislang jede Anfrage per `respondWith()` ab, auch POST-Uploads mit binärem Datei-Inhalt — ein bekannter WebKit/iOS-Bug, der dabei den Request-Body leert. Fix: expliziter Methodenfilter, non-GET-Anfragen laufen jetzt direkt am Service Worker vorbei ans Netzwerk. Released als v1.22.14, auf echtem iPhone verifiziert. |
| Höhe-Korrektur | Fotografenstandort-Höhe einstellbar (US-62) |

**Pflicht-Regression Quick-Add:**
- [ ] Sheet öffnet ohne Absturz
- [ ] GPS-Button fragt nach Erlaubnis
- [ ] Karten-Tap setzt Motiv-Marker + zeigt Linie
- [ ] „Ohne Punkte" → Toast erscheint (kein Absturz)
- [ ] „Mit Punkten" → Preview-Box mit Azimut, Distanz, Höhenwinkel
- [ ] Gespeicherte Location erscheint danach im Orte-Tab (durchgängiger Ablauf öffnen→Koordinaten setzen→Alignments berechnen→speichern bereits automatisiert: `run_frontend_check.py::_check_location_create`, TASK-66 — übernommen aus TASK-69 AK6, keine Dopplung in TASK-67 Etappe 3 gebaut)
- [ ] Hinweise-Text in „Optionale Angaben" eingetragen → nach dem Speichern sofort in der Hinweise-Sektion der neuen Location sichtbar (BUG-65)
- [ ] Hinweise-Feld leer gelassen → Speichern funktioniert normal, keine automatische Notiz, keine Hinweise-Sektion sichtbar (BUG-65, Regression zu BUG-60)
- [ ] Beispielbild in „Optionale Angaben" ausgewählt → nach dem Speichern automatisch hochgeladen, erscheint sofort im Hero-Bereich der neuen Location (US-127)
- [ ] Kein Beispielbild ausgewählt → Speichern funktioniert normal, Platzhalter „Noch kein Beispielbild" für den Host sichtbar (US-127, Regression)
- [ ] Standort und Motiv mit echtem Höhenunterschied gesetzt → „Höhenwinkel Spitze" in der Preview-Box zeigt einen Wert ungleich 0,00° (BUG-66) (automatisiert: `test_bug66.py`, `TestAngularAltitudeReflectsElevationDifference`)
- [ ] Standort und Motiv ohne nennenswerten Höhenunterschied gesetzt → „Höhenwinkel Spitze" bleibt nahe 0,00° (BUG-66, Regression) (automatisiert: `test_bug66.py`, `TestAngularAltitudeStaysNearZeroWithoutElevationDifference`)
- [ ] Neue Location gespeichert, Karten-Tab war vorher schon einmal geöffnet → neuer Marker sofort ohne Reload sichtbar, keine doppelten Marker, aktive Kartenfilter wirken weiterhin (BUG-67) (Datenebene automatisiert: `test_bug67.py`, `TestNewLocationImmediatelyAvailableViaGetLocations` — neue Location ist sofort über `GET /locations` sichtbar; Marker-Rendering auf der Karte selbst bleibt manuell/Etappe 3)
- [ ] Neue Location gespeichert, Locations-Tab war vorher schon einmal geöffnet → neuer Eintrag sofort ohne Reload in der Liste sichtbar (BUG-67) (Datenebene automatisiert: `test_bug67.py`, siehe oben)

---

## 7. Orte-Tab (Locations)

| Funktion | Verhalten |
|----------|-----------|
| Locations-Liste | ≥15 Location-Karten; scrollbar |
| Sortierung nach Entfernung (US-118) | Sobald der GPS-Standort des Nutzers bekannt ist, ist die Location-Liste aufsteigend nach Entfernung vom aktuellen Standort des Fotografen sortiert (Fotografen-Standpunkt, nicht das Motiv) — die nächstgelegene Location erscheint oben. Aktive Filter und die Textsuche bleiben zusätzlich wirksam, die gefilterte/gefundene Teilmenge bleibt dabei nach Entfernung sortiert. Ist der Standort nicht bekannt oder wird die Standortfreigabe verweigert, bleibt die Liste in der bisherigen (unsortierten) Reihenfolge — kein Fehler, keine leere Liste. |
| Suche | Live-Textsuche filtert nach Standortname/Beschreibung/Kategorie — Sucheinstieg über das Lupensymbol im Header (BUG-49; lokales Suchfeld im Panel entfernt). Eine bereits im Feed/Karten-Tab aktive Suche wird beim Wechsel in den Orte-Tab automatisch mit angewendet, ohne erneute Eingabe (BUG-82). |
| Location antippen | Öffnet Location-Detail-Sheet |
| Location-Detail | Zeigt: Name, Koordinaten, Azimut, Brennweiten-Empfehlung, Sonnen-Ausrichtung heute, zukünftige Events, Sichtachsen-Check-Pille (US-09) |
| Hinweise-Sektion (Location-Detail) | Ist ein Hinweise-Text (`special_notes`) vorhanden, erscheint direkt nach dem Abschnitt „Ausrichtung" eine eigene, rein lesende Sektion „Hinweise" mit dem vollständigen Text — ohne dass zuvor „Bearbeiten" geöffnet werden muss. Ist kein Text vorhanden, fehlt die Sektion komplett (kein leerer Kasten). Dasselbe Feld lässt sich weiterhin nur über „Bearbeiten" ändern (BUG-65). |
| Sichtachsen-Check-Pille (Location-Detail, US-09) | Zeigt denselben Status wie im Feed/Chancen-Detail (Augen-Icon + Grün „Frei" / Orange „Teilweise verdeckt" / Rot „Blockiert" / Grau „Nicht geprüft"), ⓘ-Erklärtext daneben. Ergebnis stammt aus der zuletzt gelaufenen Raycast-Prüfung (Höhendaten OpenTopoData + Gebäudedaten OSM/Overpass) dieser Location. |
| Menüpunkt „Sichtachsen aktualisieren" (US-09) | Neuer Menüpunkt im Location-Detail; löst die Raycast-Sichtachsenprüfung manuell erneut aus (zusätzlich zum automatischen Lauf beim Anlegen/Ändern der Location). Nützlich z. B. nach Neubau eines Gebäudes in der Sichtachse oder bei zunächst fehlenden Höhen-/Gebäudedaten. |
| Sonnen-Ausrichtung im Location-Detail | Abschnitt „Ausrichtung": Sonnenaufgang und -untergang heute mit Azimut in Grad + Richtungsklassifizierung relativ zum Motiv (US-107). Bei Locations ohne Motiv-Koordinaten: nur Uhrzeit + Azimut ohne Motivvergleich. |
| Richtungsklassifizierung | Lesbare Einschätzung: „Sonne geht fast genau hinter dem Motiv auf (nur X° Abweichung)" / „Gegenlicht" / Grad-Differenz zum Motiv-Azimut (±15°-Toleranz für „nah am Motiv") (US-107) |
| Location bearbeiten | Edit-Modus in Location-Detail; Änderungen persistieren via PATCH + Server-Fetch. Editierbare Felder: Name, Beschreibung, Koordinaten, Brennweiten-Empfehlung, Stockwerkshöhe, **Motivname (`subject_name`)** (BUG-61), **HINWEISE (`special_notes`)** (BUG-50), **Bauwerkshöhe (`subject_height_m`)** und **Bauwerksbreite (`subject_width_m`)** (US-128, Details in eigener Zeile unten). Das HINWEISE-Feld kann beliebig geändert oder geleert werden — der ursprüngliche Text kehrt nach dem Speichern nicht zurück. Der Motivname wird nach dem Speichern sofort in der Motiv-Sektionsüberschrift des Detail-Sheets angezeigt und bleibt auch nach komplettem App-Neuladen erhalten (BUG-61). |
| Bauwerkshöhe/-breite nachträglich korrigierbar (US-128) | Im Bearbeiten-Modus zusätzlich zur bestehenden Fotografen-Standhöhe (`observer_floor_height_m`) korrigierbar: Bauwerkshöhe (`subject_height_m`) und Bauwerksbreite (`subject_width_m`) — für Custom- und Standard-Locations gleichermaßen. Eine Korrektur löst automatisch dieselbe Neuberechnung aus wie eine Koordinatenkorrektur (Feed + Kalender). Der neue Wert übersteht jetzt zuverlässig sowohl einen Server-Neustart als auch den nächtlichen/manuellen Recompute-Subprozess (`precompute.py`) — vorher gab es dafür strukturell keinen verlässlichen Weg. Wichtig für konkrete Sonnen-/Mond-Alignments (z. B. „Sonne steht exakt auf der Kirchturmspitze"); für reine Horizont-Ereignisse (Mondaufgang, Sonnenaufgang, Golden/Blue Hour) spielt die Bauwerkshöhe keine Rolle. |
| Bearbeiten-Karte im Vollbild | Auf der kleinen Bearbeiten-Karte öffnet ein Symbol (oben rechts) ein bildschirmfüllendes Overlay zum komfortablen Setzen beider Pins (Fotograf-Standort, Motiv); Schließen übernimmt die neuen Positionen sofort in die kleine Karte + Koordinatenfelder, gespeichert wird weiterhin erst über „Speichern" (US-87). Die readonly „Karte & Blickwinkel"-Ansicht (US-58) ist davon getrennt und hat ihr eigenes, rein anzeigendes Vollbild-Symbol ohne Pin-Verschieben (US-114, siehe Abschnitt 4). |
| Bearbeiten-Karte schwenkt bei Koordinaten-Eingabe (US-133) | Verlässt man das Feld „Fotograf-Standort (Koordinaten)" oder „Motiv (Koordinaten)" nach einer vollständigen, gültigen Eingabe (Feld-Blur), schwenkt die kleine Bearbeiten-Karte automatisch zur neuen Position — die aktuell eingestellte Zoomstufe bleibt unverändert. Bei unvollständiger/ungültiger Eingabe oder komplett geleertem Feld bleibt die Karte unverändert stehen. Öffnen/Schließen des Vollbild-Overlays (Zeile oben, US-87) löst dabei bewusst KEIN zusätzliches Schwenken der kleinen Karte aus, auch wenn dabei intern derselbe Koordinaten-Resync läuft wie beim Tippen — das Schwenken hängt an einem eigenen Blur-Pfad, nicht am internen Resync. |
| Satellit/Straßenkarte-Umschalter (Location-Karten) | Alle Location-bezogenen Karten (Neue Location anlegen, Bearbeiten-Mini-Karte + deren Vollbild, „Karte & Blickwinkel"-Kegel-Vorschau + deren Vollbild) zeigen oben links einen schlanken Umschalter „Satellit"/„Straße". Umschalten wirkt sofort, ohne gesetzte Pins/Linien/Kegel oder den aktuellen Kartenausschnitt (Zoom/Position) zu verlieren; Vollbild-Ansicht übernimmt automatisch denselben Modus wie die zugehörige kleine Karte. Es gibt EINE gemeinsame Einstellung für alle diese Karten (nicht je Kartentyp getrennt), gespeichert nur lokal auf dem Gerät (`localStorage`-Key `fa_loc_map_mode`, kein Server-Sync). Der normale Karten-Tab (`MapView`, Abschnitt 5, mit eigenem Nacht/Standard/Satellit-Umschalter) ist davon komplett getrennt und unverändert (US-123). |
| Custom Locations | Vom Nutzer gespeicherte Locations erscheinen hier; Namen ohne 📍-Emoji (BUG-42) |
| Standortverifikation | Verifikationen werden persistiert (BUG-26) |
| Beispielbild (Location-Detail) | Host kann pro Location genau ein Beispielbild hochladen/ersetzen (nur Host sieht die Upload-Steuerung); erscheint oben im Hero-Bereich, füllt die Fläche in Hoch- wie Querformat vollständig aus und bleibt dabei immer mittig zum Originalbild zentriert (`object-fit: cover` + `object-position: center`). Server verkleinert/komprimiert automatisch auf ~500 KB und korrigiert die Ausrichtung anhand der EXIF-Information. Ohne Bild bleibt der Bereich für normale Nutzer komplett unsichtbar, für den Host erscheint ein Platzhalter „Noch kein Beispielbild". Ersetzen entfernt die alte Bilddatei; Löschen der Location entfernt ihr Beispielbild ebenfalls automatisch (US-120). Kein Vorschaubild in der Locations-Liste (bewusste Abgrenzung). Zusätzlich kann der Host ein vorhandenes Beispielbild über einen eigenen Löschen-Button eigenständig entfernen (mit Sicherheitsabfrage vor dem endgültigen Löschen, analog zum Löschen einer ganzen Location) — danach erscheint wieder der leere Platzhalter, ohne dass die Location selbst gelöscht werden muss (US-125). Über einen „Ausschnitt wählen"-Button kann der Host außerdem per Klick auf die wichtige Bildstelle selbst festlegen, welcher Bereich in Hoch-/Querformat-Ansicht sichtbar bleibt (Fokuspunkt) — eine rein clientseitige Anzeigeposition, das Originalbild bleibt unverändert; gilt auch nachträglich für bereits vorhandene Bilder (Standard: Bildmitte) und wird beim Ersetzen des Bildes zurückgesetzt (US-126). Der Button selbst ist kontraststark gestaltet (deckende Bauhaus-Akzentfarbe mit dazu passender Textfarbe, gleiches Muster wie der „Fertig"-Knopf im selben Editor) und bleibt dadurch auf jedem Foto-Hintergrund gut lesbar, egal ob sehr dunkel oder sehr hell (BUG-69). Seit BUG-71 bleibt der Bezug zur gerade geöffneten Location auch über die asynchrone Fotoauswahl hinweg zuverlässig erhalten (übersteht auch einen zwischenzeitlichen Neustart der Seite); geht der Bezug ausnahmsweise doch verloren, erscheint immer der Toast „Bitte Location erneut öffnen und Bild noch einmal hochladen" statt eines stillen Abbruchs. Die eigentliche Ursache des ursprünglichen BUG-71-Fehlbilds (Bild-Upload auf iPhone/iOS scheiterte, auf Mac/Safari nicht) lag im Service Worker (`web/sw.js`): dieser fing bislang jede Anfrage per `respondWith()` ab, auch POST-Uploads mit binärem Datei-Inhalt — ein bekannter WebKit/iOS-Bug, der dabei den Request-Body leert. Fix: expliziter Methodenfilter, non-GET-Anfragen laufen jetzt direkt am Service Worker vorbei ans Netzwerk. Released als v1.22.14, auf echtem iPhone verifiziert. |

**Pflicht-Regression Orte:**
- [ ] ≥15 Karten sichtbar (automatisiert: `test_task67_orte_regression.py`)
- [ ] Suche „Babelsberg" filtert korrekt
- [ ] Eine im Feed/Karten-Tab aktive Suche wird beim Wechsel in den Orte-Tab automatisch übernommen, ohne erneute Eingabe (BUG-82)
- [ ] Location-Detail-Sheet öffnet und schließt
- [ ] Bewertungsfunktion: Anlegen/Abrufen/Löschen einer Bewertung (übernommen aus TASK-69 AK3) (automatisiert: `test_task67_ratings_regression.py`, 12 pytest-Fälle über GET/POST/DELETE `/locations/{id}/ratings` — lokal grün verifiziert, TASK-67 Etappe 3; zusätzlicher UI-Klickfluss `run_frontend_check.py::_check_rating_flow`, lokal grün bestätigt (Etappe 5))
- [ ] Abschnitt „Ausrichtung" zeigt Sonnenaufgang/-untergang mit Azimut für heute (US-107) (Datenebene automatisiert: `test_task67_detail_regression.py`, dieselbe `precompute._serialize()`-Logik — Anzeige im Abschnitt „Ausrichtung" selbst bleibt manuell/Etappe 3)
- [ ] Locations mit Motiv-Koordinaten zeigen Richtungsklassifizierung relativ zum Motiv (US-107)
- [ ] Locations ohne Motiv-Koordinaten zeigen nur Uhrzeit + Azimut, kein leerer Abschnitt (US-107)
- [ ] Location-Detail zeigt Sichtachsen-Check-Pille mit korrektem Status + ⓘ-Erklärtext (US-09) (Datengarantie automatisiert: `test_us09_sightline.py` — Pillen-Darstellung selbst bleibt manuell/Etappe 3)
- [ ] Menüpunkt „Sichtachsen aktualisieren" löst neue Prüfung aus, Pille aktualisiert sich mit dem Ergebnis (US-09)
- [ ] Anlegen/Ändern einer Location löst automatisch eine Sichtachsenprüfung aus (US-09) *(Grenzfall, siehe AK „Edge Case" in TASK-67: Auto-Trigger läuft im precompute-Subprozess (`precompute.py`, Zeile ~1001), ist aber bisher durch keine bestehende oder neue Testdatei abgedeckt — echte Lücke, nicht automatisiert, für eine spätere Etappe vorgemerkt statt stillschweigend als erledigt markiert)*
- [ ] Edit → Speichern → Änderung sofort in Sheet + Liste sichtbar (kein Reload nötig)
- [ ] Close-Button erreichbar (Safe Area — BUG-25 gefixt)
- [ ] Bearbeiten-Karte: Vollbild-Symbol öffnet bildschirmfüllendes Overlay, Pins darin setzbar, Schließen übernimmt Position in kleine Karte (US-87)
- [ ] Location-Karten (Anlegen/Bearbeiten/Kegel-Vorschau) zeigen Satellit/Straße-Umschalter; Umschalten verliert keine Pins/Zoom; gewählte Ansicht bleibt nach Schließen/erneutem Öffnen erhalten; Karten-Tab (`MapView`) unverändert (US-123)
- [ ] Host kann Beispielbild hochladen/ersetzen, Bild füllt Hero-Bereich mittig in Hoch- und Querformat; ohne Bild kein Platzhalter für normale Nutzer; Nicht-Host sieht keine Upload-Steuerung (US-120) (Datenebene automatisiert: `test_us120.py` — Upload/Resize/EXIF-Korrektur; Hero-Bereich-Darstellung selbst bleibt manuell/Etappe 3)
- [ ] Host kann vorhandenes Beispielbild über eigenen Löschen-Button entfernen, Sicherheitsabfrage erscheint vorher, danach wieder Platzhalter (US-125) (Datenebene automatisiert: `test_us_125.py` — Lösch-Endpoint entfernt `image_url` + Datei; Sicherheitsabfrage-Dialog selbst bleibt manuell/Etappe 3)
- [ ] Host kann über „Ausschnitt wählen" per Klick einen Fokuspunkt setzen, sichtbarer Bildausschnitt verschiebt sich entsprechend in Hoch- und Querformat; gilt auch nachträglich für bereits vorhandene Bilder; wird beim Ersetzen des Bildes zurückgesetzt (US-126) (Datenebene automatisiert: `test_us_126.py` — `image_focus_x`/`image_focus_y`-Persistenz + Reset beim Ersetzen; Klick-Interaktion selbst bleibt manuell/Etappe 3)
- [ ] Location mit Hinweise-Text: eigene Sektion „Hinweise" direkt nach „Ausrichtung" sichtbar, ohne „Bearbeiten" zu öffnen; rein lesend, kein Eingabefeld (BUG-65)
- [ ] Location ohne Hinweise-Text: keine Hinweise-Sektion sichtbar, kein leerer Kasten (BUG-65)
- [ ] Bauwerkshöhe/-breite im Bearbeiten-Modus geändert → löst automatisch Neuberechnung aus (Feed + Kalender); Wert bleibt nach Server-Neustart UND nach einem precompute-Lauf erhalten (US-128) (automatisiert: `test_us_128.py`, `TestRecomputeTriggered` + `TestStandardLocationOverrideReloadSurvivesRestart` + `TestPrecomputeSubprocessSeesHeightAndWidthOverride`)

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
| Suche (BUG-82) | Live-Textsuche filtert nach Motivname (`subject_name`) und Session-Bezeichnung — Scout-Chancen haben anders als Feed/Orte keine Bindung an eine gespeicherte Location (`location_id` ist bei Scout-Einträgen immer `null`), daher kein Standortname-Match. Wirkt sowohl beim direkten Tippen im Scout-Tab als auch beim automatischen Übernehmen einer bereits im Feed aktiven Suche beim Tab-Wechsel. Vor BUG-82 wirkungslos (Suche routete auf den unsichtbaren Feed-Container statt auf Scout). |
| Korrekte Platzhalter-Erkennung (US-128) | Ob eine Location eine recherchierte Bauwerkshöhe hat, wird über ein explizites Datenfeld (`subject_height_researched`) bestimmt statt über eine Heuristik am Zahlenwert. Vorher wurden Locations mit exakt 20 m Bauwerkshöhe und fehlender Bauwerksbreite fälschlich als „unbearbeiteter Platzhalter" behandelt und aus der Scout-Pipeline ausgeschlossen — unabhängig vom tatsächlichen, ggf. korrekten Wert. |

**Pflicht-Regression Scout:**
- [ ] Scout-Tab lädt ohne Fehler (Basistest automatisiert: `run_frontend_check.py::_check_scout_mode`, TASK-67 Etappe 3, übernommen aus TASK-69 AK7, lokal grün bestätigt)
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
- [ ] Suche filtert Scout-Chancen nach Motivname/Session-Bezeichnung; eine im Feed aktive Suche wird beim Wechsel in den Scout-Tab automatisch übernommen (BUG-82)

---

## 9. Einstellungen

| Funktion | Verhalten |
|----------|-----------|
| Mindest-Score Slider | 0–100%; nach Änderung → Feed zeigt weniger/mehr Chancen |
| Erscheinungsbild | System / Hell / Dunkel (US-97); Auswahl persistiert in localStorage |
| Backend-URL | TASK-83: feste Auswahl (Prod / `http://localhost:8000`) statt Freitextfeld; Auswahl persistiert in localStorage, Wert außerhalb der Liste wird verworfen |
| „Jetzt aktualisieren" | POST `/refresh`; Toast „✅ Daten aktualisiert" nach ~3s |
| Impressum | Öffnet Impressum-Sheet |
| Rollen-Anzeige | Zeigt „Host" oder „User" — TASK-83: Rolle wird aus `fa_role` in localStorage gelesen (unkritischer UI-Hinweis, reine Anzeige); die eigentliche Autorisierung läuft serverseitig über das Sitzungscookie, nicht mehr über ein JS-lesbares Token-Präfix (löst BUG-47-Mechanismus ab) |

**Pflicht-Regression Einstellungen:**
- [ ] Slider auf 80% → Feed-Reload → weniger Karten
- [ ] Theme-Umschalter ändert sofort das Erscheinungsbild
- [ ] Theme-Auswahl überlebt App-Reload
- [ ] Nach Host-Login sofort „Host" sichtbar (kein Browser-Refresh nötig) (BUG-47) (Serverseitiger Vertrag automatisiert: `test_task67_auth_regression.py`/`test_us66_login.py` — Rollenvergabe + Token-Präfix-Ableitung; sichtbarer Text im Tab bleibt manuell/Etappe 3)
- [ ] Nach Logout und erneutem Login als User → „User" sichtbar (Serverseitiger Vertrag automatisiert: `test_task67_auth_regression.py`/`test_us66_login.py`, siehe oben)

---

## 10. Login / Auth

| Funktion | Verhalten |
|----------|-----------|
| Login-Screen | Erscheint wenn nicht eingeloggt |
| Host-Login | Volladmin: Locations anlegen/editieren, Refresh starten |
| User-Login | Lesen + eigene Custom-Locations |
| Session | TASK-83: HttpOnly/Secure/SameSite=Lax-Sitzungscookie (`fa_session`, 30 Tage Max-Age), gesetzt von `POST /login`; kein JS-lesbares Token mehr (Body enthält nur `role`) |
| Logout | Settings-Sheet ruft `POST /logout` — löscht das Cookie serverseitig (Max-Age=0); JS kann ein HttpOnly-Cookie nicht selbst entfernen |
| Endpunktschutz | `require_auth`/`require_host` lesen ausschließlich das Cookie (`fastapi.Cookie`), kein Authorization-Header-Fallback — ein Deploy dieses Tickets erzwingt Zwangs-Logout aller vorher ausgestellten Bearer-Token |
| Server-Start (TASK-85) | Prozess bricht beim Start sofort mit `RuntimeError` ab, wenn `FOTOALERT_AUTH_SECRET` fehlt oder leer ist — kein Notwert-Fallback mehr im Code. Verhindert, dass eine Fehlkonfiguration (fehlende `.env`) ein frei berechenbares Admin-Ticket ermöglicht; App bleibt in dem Fall komplett offline statt „unsicher aber erreichbar" |
| CORS | Explizite Origin-Liste (`https://fotoalert.stephanschumann.com`, `http://localhost:8000`) + `allow_credentials=True` statt Wildcard — Voraussetzung für Cookie-Auth (Wildcard+Credentials ist per Fetch-Spec verboten) |
| Backend-Adresse (Settings) | Feste Auswahl (Prod / `http://localhost:8000`) statt Freitextfeld — verhindert Umbiegen der API-Zieladresse per Skript; ein Wert außerhalb der Liste wird beim nächsten Start verworfen (`CFG.setApi`) |
| Rollen-Ableitung | `CFG.role` liest `fa_role` aus localStorage (unkritischer UI-Hinweis, reine Anzeige) — die eigentliche Autorisierung läuft serverseitig ausschließlich über das Cookie; `Auth.isLoggedIn()` = `!!CFG.role` (optimistischer Boot-Check, echte Prüfung passiert beim ersten geschützten Request via 401→Logout) |
| Login-Sperre (TASK-86) | `POST /login` sperrt nach 5 falschen Passwörtern derselben Absenderadresse innerhalb 15 Minuten (HTTP 429 statt weiterer Passwortprüfung, inkl. Wartezeit-Angabe); Zähler setzt sich bei erfolgreichem Login zurück — Teil der TASK-86-Härtung gegen Endpunkt-Missbrauch (Details siehe Changelog) |

**Pflicht-Regression Auth:**
- [ ] Nicht-eingeloggter Zugriff → Login-Screen erscheint (automatisiert: `test_task67_auth_regression.py`, `test_task-83.py`, serverseitiger Vertrag geprüft — DOM-Sichtbarkeit selbst bleibt manuell, s. Datei-Docstring)
- [ ] Login als Host → alle Tabs erreichbar, Einstellungen zeigen sofort „Host" (automatisiert: `test_task67_auth_regression.py` + `test_us66_login.py` + `test_task-83.py`, Rollenvergabe + Endpunktschutz + Cookie-Attribute geprüft — sichtbarer Tab/Text bleibt manuell)
- [ ] Login als User → Einstellungen zeigen „User" (automatisiert: `test_task67_auth_regression.py` + `test_us66_login.py`, Rollenvergabe geprüft — sichtbarer Text bleibt manuell)
- [ ] App-Reload nach Host-Login → Einstellungen zeigen weiterhin „Host" (`fa_role` aus localStorage) (automatisiert: `test_task67_auth_regression.py`, sichtbarer Text bleibt manuell)
- [ ] Logout beendet die Sitzung serverseitig — direkt danach zeigt ein geschützter Vorgang wieder den Login-Bildschirm (automatisiert: `test_task-83.py::TestLogoutInvalidatesCookie`)
- [ ] CORS: erlaubte Origin bekommt `Access-Control-Allow-Credentials: true` + exakte (nicht Wildcard-)Origin, fremde Origin bekommt keinen Credential-Header (automatisiert: `test_task-83.py::TestCorsAllowsCredentialsOnlyForKnownOrigins`)
- [ ] Geschützte Endpoints ohne Token → HTTP 401 (automatisiert: `test_task67_auth_regression.py` + `test_us66_login.py`)

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
| `/run-qa-pass` | POST | Stößt den Standort-Qualitätslauf sofort an, statt auf die Nacht zu warten (auth: host) |

**Pflicht-Regression Backend:** (automatisiert: `test_task67_backend_regression.py`, läuft im CI-Gate mit)
```bash
# Schnell-Check (alle 5 in einem Durchlauf):
curl -s http://localhost:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'; print('✅ Health OK')"
curl -s http://localhost:8000/locations | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d)>10; print(f'✅ Locations OK ({len(d)})')"
curl -s "http://localhost:8000/opportunities?min_score=0.1&days=14" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✅ Feed OK ({len(d)} Events)')"
curl -s http://localhost:8000/discover | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✅ Scout OK ({len(d)} Events)')"
curl -s http://localhost:8000/calendar | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✅ Kalender OK ({len(d)} Events)')"
```
- Health → 1:1 automatisiert (`test_health`).
- Locations → 1:1 automatisiert (`test_locations`).
- Feed (`/opportunities`) → automatisiert (`test_feed_opportunities`, prüft Liste + Status statt Event-Anzahl).
- Scout (`/discover`) → automatisiert (`test_scout_discover`); **Befund bei Gelegenheit dieser Etappe:** `/discover` liefert ein dict (`{"status", "opportunities", ...}`), keine flache Liste — der obige curl-Einzeiler zählt daher fälschlich `len(d)` über die Dict-Keys (immer 4), nicht über die Events; der automatisierte Test prüft stattdessen korrekt, dass `d["opportunities"]` eine Liste ist.
- Kalender (`/calendar`) → automatisiert (`test_calendar`); gleicher Befund wie bei Scout (`/calendar` liefert ebenfalls ein dict mit `"events"`-Liste, kein flaches Array).

**Fünf Zusatzfunktionen (übernommen aus TASK-69 AK8, TASK-67 Etappe 3) — jeweils mindestens ein automatisierter Basistest, lokal grün verifiziert (`test_task67_zusatzfunktionen_regression.py`):**
- Tagesübersicht (`/opportunities/today` + `/daily-briefing`) — automatisiert: `TestTagesuebersicht`.
- Empfehlungsplan (`/plan`, On-Demand-Alignment für beliebige Koordinaten, TASK-25) — automatisiert: `TestEmpfehlungsplan`.
- Adress-Umkehrsuche (`/reverse-geocode`) — automatisiert: `TestAdressUmkehrsuche`; prüft nur die Antwortstruktur (Statuscode + Feld `place`), nicht den Nominatim-Inhalt selbst (externer Netzwerkzugriff, vom Endpoint bei Fehler bewusst zu `""` abgefangen statt Absturz).
- Verarbeitungsstatus-Anzeigen (`/job-status` + `/recompute-status`) — automatisiert: `TestVerarbeitungsstatusAnzeigen`.

**Wetter-Job-Status bei fehlgeschlagenem Live-Wetter-Abruf (BUG-77):** Der 3-stündliche Wetter-Job (`_weather_overlay`) holt für Himmelsröte-/Goldene-Wolken-Chancen live Wetterdaten je Location. Schlägt der Abruf für mindestens eine Location fehl (Teil- oder Totalausfall), zeigt der `/job-status`-Endpunkt für „weather" einen Fehlerzustand statt „done", inkl. Klartext-Hinweis mit den Namen der betroffenen Locations (bei mehr als 5 gekürzt auf „…und N weitere") — vorher wurde ein fehlgeschlagener Abruf nur als Warning geloggt, ohne Sichtbarkeit im Job-Status. Erfolgreiche Locations werden trotz Teilausfall normal aktualisiert. Läuft der Abruf für alle Locations fehlerfrei durch oder gibt es keine relevanten Events in den nächsten 3 Tagen, bleibt der Status unverändert „done". (automatisiert: `test_bug77_weather_job_status.py`)

---

## 11a. Automatische Standort-Verbesserung (Datensync, Epic US-75)

**Was der Nutzer davon hat:** Neue oder geänderte Standorte werden automatisch sinnvoll ausgefüllt, ohne dass jemand Werte von Hand eintragen muss.

| Funktion | Verhalten |
|----------|-----------|
| Ideale Blickrichtung automatisch | Für einen Standort wird die ideale Blickrichtung (Azimut) selbsttätig bestimmt und eingetragen. |
| Brennweiten-Empfehlung automatisch | Passend zum Motiv und zur Entfernung wird eine empfohlene Brennweite berechnet und hinterlegt. |
| Nächtlicher Lauf (01:00 Uhr) | Einmal pro Nacht prüft die App alle Standorte und erkennt am „Fingerabdruck" eines Standorts, ob sich etwas geändert hat oder er neu ist. Nur diese werden neu durchgerechnet — der Rest bleibt unangetastet, damit der Lauf schnell bleibt. |
| Werte erscheinen in Feed & Kalender | Die automatisch ermittelten Werte fließen in die nächste Neuberechnung ein, sodass sie danach auch in den Foto-Chancen (Feed) und im Kalender sichtbar sind. |
| Standortbeschreibung automatisch | Für Standorte ohne (oder mit leerer) Beschreibung wird automatisch ein kurzer deutscher Text aus den vorhandenen Fakten (Name, Motiv, Kategorie, Koordinaten) erzeugt und hinterlegt. |
| Manuelle Werte bleiben geschützt | Hat jemand eine Blickrichtung, Brennweite oder Beschreibung selbst gesetzt oder gesperrt, rührt die Automatik diese Werte nicht an. |
| Sofort-Auslöser | Ein geschützter Auslöser (nur für den Host) startet diesen Qualitätslauf bei Bedarf sofort, ohne auf die Nacht zu warten. |
| QA-Teilerfolg konsistent behandelt (TASK-78) | Scheitert beim automatischen Lauf ein einzelner Teilschritt (Blickrichtung/Brennweite/Beschreibung) an einem Datenbank-Fehler, nachdem ein anderer Teilschritt für denselben Standort bereits erfolgreich geschrieben hat, wird der Prüf-Eintrag trotzdem nachgezogen — es bleiben keine Werte ohne zugehörigen Prüf-Eintrag zurück. Nur wenn für einen Standort gar kein Wert geschrieben wurde, bleibt er wie bisher fällig und wird beim nächsten Lauf erneut versucht. Zusätzlich reduziert ein `PRAGMA busy_timeout` beim Datenbankzugriff die Häufigkeit kurzzeitiger Sperr-Konflikte als Auslöser. |

**Pflicht-Regression Standort-Automatik:**
- [ ] Neuer Standort ohne Blickrichtung erhält nach dem Lauf eine automatische Blickrichtung (automatisiert: `test_task45_azimuth.py`, `test_unlocked_is_written`)
- [ ] Standort ohne Brennweiten-Empfehlung erhält nach dem Lauf eine Empfehlung (automatisiert: `test_task47_focal.py`, `test_unlocked_empty_is_written`)
- [ ] Standort ohne Beschreibung erhält nach dem Lauf einen automatisch erzeugten deutschen Text (automatisiert: `test_task46_descriptions.py`, `test_description_written_when_empty`)
- [ ] Manuell gesetzte/gesperrte Werte (inkl. Beschreibung) bleiben nach dem Lauf unverändert (automatisiert: `test_task45_azimuth.py`/`test_task46_descriptions.py`/`test_task47_focal.py`, je `test_lock_is_respected`/`test_description_lock_respected`)
- [ ] Unveränderte Standorte werden nicht erneut durchgerechnet (nur geänderte/neue) (automatisiert: `test_task48_qa_cron.py`, `test_unchanged_checked_is_skipped`)
- [ ] Automatische Werte erscheinen nach der Neuberechnung in Feed + Kalender (automatisiert: `test_task48_qa_cron.py`, `test_apply_qa_values_patches_location` + `test_apply_qa_values_merge_order`)
- [ ] Sofort-Auslöser ohne Host-Token → HTTP 401 (automatisiert: `test_task48_qa_ondemand.py`, `TestRunQaPassEndpoint::test_without_token_rejected`)

---

## 11b. Automatische Server-Sicherung (Backup)

**Was der Nutzer davon hat:** Standort-Daten und Standort-Fotos sind gegen Datenverlust abgesichert — bei jeder Änderung sichert der Server automatisch im Hintergrund, ohne dass jemand daran denken muss.

| Funktion | Verhalten |
|----------|-----------|
| Automatische Sicherung bei jeder Änderung | Nach jeder Bearbeitung (Standort-Daten, Standort-Fotos) läuft im Hintergrund sofort eine Sicherung mit, ohne dass ein Test oder eine Aktion von Stephan nötig ist. |
| Standort-Fotos Teil der Sicherung (TASK-55) | Seit TASK-55 sichert der Server auch die hochgeladenen Standort-Fotos vollständig mit, nicht mehr nur die Standort-Daten selbst. Wird ein Foto ersetzt oder gelöscht, verschwindet es auch aus der Sicherung — die Sicherung spiegelt also immer den aktuellen Stand, sie ist kein Archiv alter Foto-Versionen. |
| Wiederherstellung schließt Fotos ein | Beim Zurückspielen einer Sicherung (Restore) werden seit TASK-55 auch die Standort-Fotos mit wiederhergestellt, vorher nur die Standort-Daten. |
| Sicherung deckt jetzt den gesamten Datenbestand ab (TASK-61) | Seit TASK-61 sichert der Server bei jeder Standort-Änderung nicht mehr nur Standort-Daten, sondern zusätzlich Bewertungen, Vor-Ort-Meldungen, Geräte-Tokens, Kamera-Profile und die automatisch ermittelten Qualitätswerte (inkl. manueller Sperren). Zusätzlich läuft dieselbe vollständige Sicherung jetzt auch beim täglichen automatischen Berechnungslauf mit — auch wenn zwischenzeitlich gar keine Location bearbeitet wurde. Ein Fehler bei einem einzelnen Datenbestand verhindert nicht mehr die Sicherung der übrigen. |

**Pflicht-Regression Backup:**
- [ ] Foto hochladen → im Hintergrund läuft die Sicherung mit (keine sichtbare Wartezeit für Stephan) (automatisiert: `test_task55_image_backup.py`, `test_new_image_is_copied_to_backup` + `test_replaced_image_content_is_updated_in_backup`)
- [ ] Foto löschen/ersetzen → alte Version verschwindet auch aus der Sicherung (automatisiert: `test_task55_image_backup.py`, `test_deleted_image_is_removed_from_backup`)
- [ ] Restore spielt Standort-Daten UND Standort-Fotos zurück *(Grenzfall: im Code existiert aktuell keine Restore-Funktion — Wiederherstellung ist ein manueller Ops-Vorgang auf dem Server (git checkout aus dem Backup-Repo), kein automatisierbarer Code-Pfad. Bleibt bewusst manuell/Server-Ops, nicht Etappe-3-Playwright-Scope, da keine App-UI involviert ist)*
- [ ] Bewertung/Vor-Ort-Meldung/Geräte-Token/Kamera-Profil ändern → alle acht gesicherten Datenbestände sind danach aktuell, nicht nur Standort-Daten (automatisiert: `test_task61_backup_coverage.py`, Inhaltsprüfung aller 8 Dateien)
- [ ] Ohne zwischenzeitliche Standort-Änderung: spätestens nach dem nächsten automatischen Berechnungslauf sind alle acht Datenbestände aktuell gesichert (automatisiert im Sandbox-Umfang: `test_task61_backup_coverage.py`; echter Trigger am täglichen Berechnungslauf nur auf dem Produktivserver prüfbar, kein Code-Pfad in der Sandbox)
- [ ] Fehler bei einem einzelnen Datenbestand verhindert nicht die Sicherung der übrigen sieben (automatisiert: `test_task61_backup_coverage.py`, erzwungener Einzelfehler)

---

## 11c. Automatisiertes Testen (CI/CD)

**Was der Nutzer davon hat:** Fehler werden vor dem Deploy erkannt, nicht erst danach — jeder Release ist automatisch gegen die bestehende Backend-Logik geprüft.

| Funktion | Verhalten |
|----------|-----------|
| Backend-pytest-Suite als Pflicht-Gate (TASK-64) | Bei jedem Release läuft in GitHub Actions ein eigener, paralleler Job „Backend-Tests (pytest)" (~2 Minuten Laufzeit). Schlägt die Test-Suite fehl, wird nicht deployt — der Job ist ein Pflicht-Gate, kein optionaler Hinweis. Verifiziert im echten CI-Lauf (v1.22.12, GitHub Actions #Backend-Tests): Job grün in 2m 11s, Deploy erfolgreich, Health-Check ok. |
| Generischer Feld-Rundreise-Test (TASK-65) | `backend/tests/test_task_65_field_roundtrip.py` prüft automatisch für **jedes** Location-Feld (Anker: `PhotoLocation`-Datenklasse, nicht nur die Regel-Tabelle), ob eine PATCH-Änderung einen simulierten Server-Neustart UND einen simulierten precompute-Lauf übersteht — getrennt für Standard- und Custom-Locations. Verallgemeinert den Regressionsschutz aus BUG-50/BUG-61/BUG-68 (Feld vergessen in einer Whitelist → Änderung verschwindet still) auf Felder, die es heute noch gar nicht gibt. 65 Testfälle, < 1 Sekunde Laufzeit, kein echter Serverneustart/precompute-Subprozess nötig. Läuft automatisch im CI-Gate aus TASK-64 mit. |
| Ephemeriden-Download gecacht + timeout-abgesichert (BUG-79) | GitHub-Actions-Cache (`actions/cache`, Key `de421-bsp-v1`) für die Ephemeridendatei `de421.bsp` verhindert einen ungemockten Download bei jedem CI-Lauf. Ein CI-Lauf kann dadurch nicht mehr durch einen hängenden externen Server das 15-Minuten-Zeitlimit reißen. |
| Release-Skript bricht bei Merge-Konflikt sauber ab (TASK-88) | `release.sh` prüft vor jeder Datei-Änderung (vor dem Versions-Bump) per `git status --porcelain` auf ungelöste Merge-Konflikte. Bei Fund: sofortiger Abbruch mit betroffener(n) Datei(en) + 3 konkreten nächsten Schritten, kein Commit, kein Tag, keine Versionsänderung. Verhindert den bei US-133 aufgetretenen Ad-hoc-Commit ohne Standard-Message/Tag. |

**Pflicht-Regression CI/Deploy-Testing:**
- [ ] Release-Push löst den Job „Backend-Tests (pytest)" parallel zu den übrigen CI-Schritten aus
- [ ] Test-Suite grün → Deploy läuft normal weiter
- [ ] Test-Suite rot → Deploy wird nicht ausgeführt (Gate greift)
- [ ] Neues Location-Feld ergänzt, aber nicht in `LOCATION_FIELD_RULES`/Ausnahmeliste eingetragen → `test_task_65_field_roundtrip.py` meldet das Feld namentlich als fehlend

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
| TASK-83 | HttpOnly-Cookie-Auth implementiert + Backend-Testsuite grün (In Test); manuelle Browser-Verifikation (Chrome + Safari, Cookie-Attribute + Secure-über-`http://localhost`, `fa_api`-Allow-Liste) noch ausstehend |

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
| 2026-06-28 | TASK-45 | Ideale Blickrichtung (Azimut) wird für Standorte automatisch bestimmt; manuelle/gesperrte Werte bleiben unangetastet |
| 2026-06-28 | TASK-47 | Brennweiten-Empfehlung wird automatisch aus Motiv + Entfernung berechnet; respektiert gesetzte/gesperrte Werte |
| 2026-06-28 | TASK-48 | Nächtlicher Standort-Qualitätslauf (01:00) erkennt geänderte/neue Standorte per Fingerabdruck und rechnet nur diese neu; Auto-Werte fließen in Feed + Kalender; geschützter Sofort-Auslöser `/run-qa-pass` (host) |
| 2026-06-29 | TASK-46 | Standortbeschreibungen werden automatisch per Mistral AI erzeugt (Deutsch, faktenbasiert); respektiert `description_lock`; überspringt bei fehlendem Key/API-Fehler sauber |
| 2026-06-29 | BUG-53 | 📍-Emoji wird nicht mehr in Location-Namen gespeichert; bestehende Locations bereinigt |
| — | US-70 | Scout-Tab: Mond-Alignment-Ephemeride |
| — | US-66 | Login + Auth (Host/User) |
| — | BUG-42 | Custom Locations: kein 📍-Emoji in Namen |
| — | BUG-41 | Street-View-Button nur bei Azimut sichtbar |
| — | BUG-38/39 | Koordinaten-Sektion: Overflow + Strich gefixt |
| 2026-06-28 | BUG-44 | Kalender-Events im 14-Tage-Fenster zeigen vollständiges Detailsheet inkl. Wetter; „Wetter unbekannt"-Badge entfernt |
| 2026-06-28 | BUG-46 | Filter: Drei-Zustände für Verifikation + Bewertung; Karte an alle Location-Filter angebunden; ansichtsabhängiges Ausgrauen irrelevanter Kriterien |
| 2026-06-28 | US-79 | Mondaufgang + Monduntergang als eigenständige Event-Typen (`"Mondaufgang"`, `"Monduntergang"`) im Feed, Kalender, Filter und Location-Detail (Nächste Chancen); vier neue API-Felder in `_serialize()`: `moonrise_utc`, `moonset_utc`, `moonrise_azimuth`, `moonset_azimuth`; Event-Detail Astronomie-Sektion zeigt Uhrzeit + Azimut; `/refresh-feed` nach Release ausführen |
| 2026-06-28 | BUG-47 | Einstellungsseite zeigt korrekte Rolle nach Host-Login: `CFG.role` als Getter aus Token-Präfix (robust gegen Safari ITP); nach Login `App.init()` + `App.nav('feed')` für sofortiges UI-Update ohne Browser-Refresh |
| 2026-06-28 | BUG-34 | iOS-Zoom in "Karte & Blickwinkel" behoben (font-size 16px) |
| 2026-06-29 | US-107 | Sonnen-Alignment-Planung: Sonnenaufgang/-untergang mit Azimut im Event-Detail (Astronomie-Sektion, analog Mondaufgang US-79); Richtungsklassifizierung relativ zum Motiv im Location-Detail (Abschnitt Ausrichtung, ±15°-Toleranz); neue API-Felder `sunrise_azimuth`/`sunset_azimuth` in `_serialize()`; Klassifizierungslogik `classify_sun_alignment()` neu; `/refresh-feed` nach Release ausführen |
| 2026-06-29 | BUG-51 | Entfernungsfilter wirkt jetzt im Locations-Tab (applyToLocations + GPS-Lifecycle) |
| 2026-06-29 | BUG-52 | GPS-Dialog erscheint pro Session nur einmal (Promise-Caching via `Filter._gpsPromise`) |
| 2026-06-29 | BUG-48 | Round-Robin-Cap im /opportunities-Feed: alle Event-Typen proportional vertreten |
| 2026-06-29 | BUG-49 | Lokales Suchfeld aus Locations-Panel entfernt; Suche läuft jetzt ausschließlich über Lupensymbol im Header (Option B) |
| 2026-06-30 | US-108 | Mondaufgang/-untergang: Events werden nur erzeugt wenn Mond ≤ 35° zur Sichtachse (vordere Azimut-Zone); seitlich + hinter dem Fotografen werden unterdrückt; `/refresh-feed` nach Release ausführen |
| 2026-06-30 | US-07 | Golden Cloud Score: neues Feld `golden_cloud_score` (0.0–1.0) je Foto-Chance; bewertet Wolkenstruktur-Qualität für Goldene/Blaue Stunde; `calculate_golden_cloud_score()` in `backend/weather.py`, Schema in `schemas.py`; Frontend-Slider „Bewölkungs-Qualität" in Filter-Sheet (index.html) |
| 2026-06-30 | US-109 | Goldene Wolken & Himmelsröte als eigene Event-Typen im Feed; richtungsbewusstes Scoring (Azimut-Differenz Sonne ↔ Motiv ≤ 30°); eigene Detail-Sheets mit Erklärtext + Wetterdaten; Filter-Chips; Cap+Sort-Schutz gegen Verdrängung |
| 2026-06-30 | US-111 | Kompass-Diagramm im Detail-Sheet für Goldene Wolken + Himmelsröte: zeigt Sonnenposition (gold), Sichtachse Fotograf→Motiv (blau gestrichelt, mit Pfeil), Wolken-Erwartungsbereich als farbige Zone (±30° golden / ±90° rot — **von US-113 am 2026-07-02 auf ±30°-Sektor am Gegenpunkt der Sonne korrigiert, siehe dort**); Entfernungsanzeige unter dem Diagramm (Haversine aus Koordinaten); Hinweis bei Motiv < 500 m |
| 2026-06-30 | BUG-55 | Wetterkarte: Beim Einschalten von „Wolken"/„Niederschlag" zoomt die Karte automatisch auf das Wetter-Gitter heraus (vorher nur eine senkrechte Linie, weil bei Stadt-Zoom nur 1–2 von 100 Kacheln im Bild lagen); beim Ausschalten zurück zur vorherigen Ansicht (`WeatherMap._savedView`/`_gridBounds`/`fitBounds`, nur Frontend) |
| 2026-07-02 | US-113 | Himmelsröte-Chance nur noch bei Sichtachse im Gegenpunkt-Sektor der Sonne (±30°), Kompass-Diagramm + Legende entsprechend angepasst |
| 2026-07-03 | BUG-56 | Astronomie-Regressionstest korrigiert: falscher Vergleichswert für Sonnenauf-/-untergang Berlin (21.06.2026) im Test berichtigt (01:43→02:43 UTC, 20:25→19:33 UTC); Berechnung selbst war korrekt, nur der Testreferenzwert war falsch; Toleranz unverändert |
| 2026-07-03 | TASK-49 | Sechs False-Positive-Meldungen in refactor_check.py behoben (Ausnahmeliste ergänzt), kein App-Code geändert |
| 2026-07-03 | US-87 | Bearbeiten-Karte im Location-Detail: neues Vollbild-Overlay (Symbol oben rechts) zum komfortablen Zoomen/Verschieben und Setzen beider Pins (Fotograf-Standort, Motiv); Schließen übernimmt neue Position sofort in kleine Karte + Koordinatenfelder, Speicherung weiterhin nur über „Speichern"; readonly „Karte & Blickwinkel" (US-58) unverändert; verifiziert gegen BUG-34-Zoom-Regression auf iPhone Safari |
| 2026-07-03 | US-114 | Readonly „Karte & Blickwinkel"-Sektion (`CameraFOV`) bekommt eigenes Vollbild-Symbol, getrennt vom Bearbeiten-Overlay aus US-87: Antippen öffnet dieselbe Karte (Beobachter-Pin, Motiv-Pin, Sichtachse, Sichtfeld-Kegel) bildschirmfüllend nur zum Ansehen, ohne Drag-Handler auf den Pins; Kreuz oder Hintergrund-Tap schließt zurück. Da `CameraFOV` bereits prefix-parametrisiert ist (`ev`/`loc`), wirkt die Änderung automatisch in allen vier Einstiegspunkten (Chancen-, Kalender-, Scout-, Location-Detail). Neue eigenständige IDs (`#fov-map-fs-*`), keine Kollision mit US-87 (`#edit-map-fs-*`); Vollbild-Karte wird bei jedem Öffnen aus dem aktuellen Datensatz neu aufgebaut (kein „eingefrorener" Stand einer zuvor angezeigten anderen Chance/Location); kein Vollbild-Symbol wenn keine Motivkoordinaten vorhanden sind. |
| 2026-07-04 | TASK-53 | Neues Dev-Werkzeug `tools/sync_dev_from_live.py`: kopiert auf Zuruf den aktuellen Live-Datenbestand (Standorte, Bewertungen, Vor-Ort-Meldungen) in die lokale Dev-Umgebung und ersetzt dortige Testdaten, damit lokal mit realistischen Daten getestet werden kann; sichert die alte Dev-Datenbank vorher automatisch weg (max. 5 Stände); rein lesender Zugriff auf Live, feste Sync-Richtung Live→Dev; v1 manuell angestoßen, keine Automatisierung. Kein Server-/App-Code geändert, kein Deploy nötig. |
| 2026-07-04 | BUG-58 | Wolken-/Niederschlag-Umschalter im Karten-Tab zoomt jetzt auf 50-km-Radius um die Kartenmitte statt auf die Mehrländer-Ansicht (bewusste Änderung an US-112/BUG-55) |
| 2026-07-04 | BUG-59 | Wetter-Overlay: Sichtbarkeit bei leichtem Wetter verbessert (Schwellwert-Deckkraft) |
| 2026-07-04 | TASK-52 | Wolken-/Regen-Legende im Karten-Tab von Kartenmitte nach unten-links über den Zeitregler verschoben |
| 2026-07-04 | US-123 | Alle Location-bezogenen Karten (Neue Location, Bearbeiten-Mini-Karte + Vollbild, „Karte & Blickwinkel"-Kegel-Vorschau + Vollbild) bekommen einen schlanken Satellit/Straße-Umschalter oben links; gemeinsamer Helper `LocMapMode` (Tile-URLs, Toggle-Rendering, Live-Tile-Layer-Tausch ohne Verlust von Pins/Zoom); eine gemeinsame Einstellung für alle diese Karten, nur lokal gespeichert (`localStorage`-Key `fa_loc_map_mode`); Karten-Tab (`MapView`) bewusst unangetastet (eigener, getrennter Nacht/Standard/Satellit-Umschalter). |
| 2026-07-04 | BUG-61 | Motivname wird nach Bearbeiten jetzt korrekt gespeichert und im Detail-Sheet angezeigt (Server-Whitelist-Fix) |
| 2026-07-04 | US-119 | Standardwert des Wahrscheinlichkeits-Filters von „Alle" (0%) auf 70% erhöht, geteilt für Feed/Kalender/Scout; Bestandsnutzer mit abweichendem Wert einmalig auf 70% zurückgesetzt (danach bleibt ein selbst gewählter Wert dauerhaft erhalten). Hinweis: Frontend-Code kam technisch bereits mit dem BUG-61-Release (v1.20.21) live, da `release.sh` den kompletten `index.html`-Stand committet; dieser Eintrag + ein eigener Versions-Bump dokumentieren US-119 nachträglich sauber. |
| 2026-07-04 | US-120 | Host kann pro Location ein Beispielbild hochladen/ersetzen (nur Host), serverseitige Verkleinerung/Kompression (~500 KB) + EXIF-Ausrichtungskorrektur, mittige Einpassung in Hoch- und Querformat (`object-fit: cover` + `object-position: center`), Platzhalter für Host ohne Bild, Löschen einer Location entfernt ihr Bild automatisch. Hinweis: Frontend-Code kam technisch bereits mit dem US-119-Release (v1.20.22) live, da `release.sh` den kompletten `index.html`-Stand committet — bis zu diesem Backend-Release war der Upload-Button auf der Live-Seite sichtbar, aber ohne funktionierenden Endpunkt (404). Dieser Eintrag + der zugehörige Backend-Release schließen die Lücke. |
| 2026-07-04 | US-118 | Location-Übersicht nach Entfernung vom Standort sortiert |
| 2026-07-04 | BUG-60 | Hinweise-Feld bleibt bei Neuanlage über Quick Location Capture leer, statt automatisch mit „Automatisch erfasst via Quick Location Capture." vorbelegt zu werden; einmaliges Cleanup-Skript (`tools/cleanup_bug60_special_notes.py`) bereinigt bestehende Locations mit exaktem alten Text (JSON + SQLite) |
| 2026-07-06 | BUG-64 | Nachgeholter Prod-Cleanup-Lauf des BUG-60-Skripts: 57 Bestands-Locations auf Produktion vom alten Platzhaltertext im Hinweise-Feld befreit (1 in `custom_locations.json`, 56 in der Datenbank); zweiter Lauf direkt danach fand 0 Treffer (Idempotenz live bestätigt); Stichprobe (`custom_1781821527`, „Potsdamer Platz Panorama") zeigte leeres Hinweise-Feld, alle anderen Felder unverändert; keine Liste-B-Grenzfälle aufgetreten |
| 2026-07-04 | US-124 | Vollbild-Modus für die Karte beim Anlegen eines neuen Standorts: Vollbild-Symbol auf der kleinen Anlege-Karte (analog Bearbeiten-Vollbild US-87, aber Antippen statt Ziehen der Pins); Satellit/Standard-Umschalter (US-123) und ein neuer Beobachter/Motiv-Umschalter im Header sind im Vollbild verfügbar; Schließen übernimmt Position(en) + Kartentyp sofort in die kleine Karte, ohne das Formular zu speichern |
| 2026-07-05 | US-125 | Host kann ein vorhandenes Beispielbild einer Location über einen eigenen Löschen-Button eigenständig entfernen (Sicherheitsabfrage vor dem endgültigen Löschen, analog zum Löschen einer ganzen Location); Bilddatei wird serverseitig wirklich entfernt, danach wieder Platzhalter „Noch kein Beispielbild" |
| 2026-07-05 | US-126 | Host kann den sichtbaren Bildausschnitt (Fokuspunkt) eines Beispielbilds über „Ausschnitt wählen" per Klick auf die wichtige Bildstelle selbst festlegen, statt der bisherigen festen Bildmitte (US-120 Rule 2); rein clientseitige Anzeigeposition (`image_focus_x`/`image_focus_y`), Originalbild bleibt unverändert; gilt auch nachträglich für bereits vorhandene Bilder (Default Bildmitte); wird beim Ersetzen des Bildes zurückgesetzt |
| 2026-07-05 | US-117 | Karten-Tab zentriert sich beim allerersten Öffnen einer Sitzung automatisch auf den aktuellen GPS-Standort mit ca. 5-km-Radius (statt fester Berlin-Ansicht); Fallback auf zuletzt bekannten Standort falls GPS verweigert, sonst Berlin; spätere Tab-Wechsel bleiben unverändert an der zuletzt gewählten Position stehen; „Mein Standort"-Button (US-69) und Wetter-Layer-Zoom (BUG-58, 50 km) unverändert |
| 2026-07-05 | TASK-57 | `refactor_check.py`: Wurzelursache der wiederkehrenden Falsch-Positive bei langen JS-Funktionen behoben (echte Klammer-Zählung statt Abstand-zur-nächsten-Funktion-Heuristik); Retro-Folge aus US-117. Reines Analyse-Werkzeug, kein App-Code geändert, kein Deploy nötig |
| 2026-07-05 | BUG-62 | Wetter-Filter und Kartenmodus-Umschalter im Karten-Tab zeigen jetzt Icons statt Textbeschriftung (Mond-Sichel/Raster/Satellit rechts, durchgestrichener Kreis/Wolke/Wolke-mit-Tropfen links, je mit Tooltip), damit sich beide Gruppen auf schmalen iPhone-Bildschirmen (ab 375px) nicht mehr überlappen |
| 2026-07-05 | US-21 (Onboarding + Glossar) | Vier Onboarding-Slides beim allerersten App-Start (`Onboarding`-Objekt, localStorage-Flag `fa_onboarding_seen`); zentraler „?"-Header-Button (optisch abgehoben, Kreis-Outline in Akzentfarbe) öffnet ein Glossar-Bottom-Sheet (`Glossary`-Objekt, gleicher Radius wie Filter-/Detail-Sheet) mit Suchfeld + Accordion, gruppiert nach Einführung/Scores/Kernbegriffe; erster Eintrag startet das Onboarding erneut. Die bereits vorher fertigen ⓘ-Element-Erklärungen (Schwierigkeitsgrad, Event-Typ, Verifikation, Filter-Gruppen, Kartenlegende, `ElementInfo`/`ScoreInfo`) bleiben unverändert. Zwei neue SVG-Symbole `i-chevleft`/`i-chevdown` ergänzt. |
| 2026-07-05 | US-21 (Korrekturen nach 2. Testdurchlauf) | „?"-Header-Button optisch zurückgebaut auf gleiches Muster wie Suche/Filter/Refresh (kein Kreis-Outline/Sonderfarbe mehr, Kurskorrektur ggü. „soll auffallen"); Kartenlegende-Text korrigiert (Realitäts-Abgleich-Fehler: Haupt-Karte zeigt nur einheitliches Pin-Symbol, Fotograf-Standort/Motiv/Sichtachse existiert nur im Detail-Sheet „Karte & Blickwinkel") + Inline-SVG-Symbolbeispiele je Legendenpunkt ergänzt + Wetter-Legende-Verweis-Satz gelöscht; Glossar-Eintrag „Feed, Kalender, Scout" fachlich präzisiert (Feed = 14-Tage-Feed, Scout errechnet eigene Chancen unabhängig von Nutzer-Standorten, Betaversion, nicht verifiziert). |
| 2026-07-05 | US-21 (Korrektur nach 3. Testdurchlauf) | Kartenlegende: Fotograf-Standort/Motiv/Sichtachse-Absatz komplett entfernt statt nur textlich korrigiert (auf Haupt-Karte nicht relevant) — behebt zugleich ein Rendering-Problem (Bold-Tags/Komma auf eigener Zeile), das durch Einbetten eines Block-Elements (`MapMarkers.legendHtml()`) in einen inline-flex-Span innerhalb eines `<p>` in der schmalen Overlay-Box entstand. Legende zeigt jetzt nur noch Pin-Symbol, Kartenebenen-Umschalter, GPS-Button. Layer-Switcher (`#map-layer-toggle`/`MapView.setLayer`) und GPS-Button (`.map-gps-btn`/`MapView.locateMe`) im Code verifiziert: beide sind eigenständige Buttons direkt im Haupt-Karten-Tab (`#page-map`), CSS zeigt keine Sichtbarkeits-Auffälligkeit. |
| 2026-07-06 | TASK-55 | Automatische Server-Sicherung umfasst jetzt auch die Standort-Fotos, nicht mehr nur die Standort-Daten; Wiederherstellung spielt Fotos ebenfalls zurück. |
| 2026-07-07 | US-09 | Sichtachsen-Check (Hinderniserkennung): Raycast-Prüfung über Höhendaten (OpenTopoData) + Gebäudedaten (OSM/Overpass), ob Gebäude/Gelände die Sichtachse Fotostandort↔Motiv blockieren. Läuft automatisch einmalig beim Anlegen/Ändern einer Location, zusätzlich manuell über neuen Menüpunkt „Sichtachsen aktualisieren" im Location-Detail. Vier Zustände: Frei (grün) / Teilweise verdeckt (orange) / Blockiert (rot) / Nicht geprüft (grau, bei fehlenden Daten — **wird niemals fälschlich als „Frei" angezeigt**, das ist die zentrale Verhaltens-Garantie und Regressionsbasis für künftige Tickets). Gilt für Sonne-/Mond-/Himmelsrichtung-Ereignisse UND Golden-Hour-/Himmelsröte-Wetter-Chancen. Sichtbar als Pille (Augen-Icon + farbiger Text) auf Feed-Karte + in Chancen-Detail + Location-Detail; zusätzlich angepasster Linienstil der bestehenden Sichtachsen-Linie/Kompass-Darstellung (durchgezogen/gestrichelt/unterbrochen/gepunktet je Status). Neuer Drei-Zustands-Filter-Chip (Off → nur Status zeigen → Status ausschließen → Off), wirkt in allen Ansichten (Feed, Kalender, Scout, Karte, Locations-Tab). Je ein ⓘ-Erklärtext für Pille und Filter-Chip. Released als v1.22.0. |
| 2026-07-07 | BUG-65 | Hinweise-Feld (`special_notes`) zusätzlich an zwei Stellen sichtbar/eingebbar gemacht: neue, rein lesende Sektion „Hinweise" in der Location-Detailansicht direkt nach „Ausrichtung" (nur wenn Text vorhanden, sonst keine Sektion); neues Eingabefeld in der Anlage-Maske („Optionale Angaben"), Text wird beim Speichern übernommen und ist sofort in der Detailansicht sichtbar; leer lassen speichert weiterhin ohne automatische Notiz (keine Regression zu BUG-60). Bearbeiten-Modus unverändert. Released als v1.22.1. |
| 2026-07-08 | US-85 | Sichtfeld-Kegel („Karte & Blickwinkel") bekommt eine gestrichelte Verlängerung der beiden Kegelkanten über das Motiv hinaus bis zur doppelten Standort→Motiv-Entfernung (gleiche Farbe/Stärke wie der Kegelrand, eigenes gleichmäßiges Strichmuster `dashArray:'6,6'`, keine Fläche); Kegel + Verlängerung als eine `L.layerGroup` verwaltet, damit beim Verstellen von Brennweite/Sensor/Ausrichtung keine alten Verlängerungslinien stehen bleiben; beim initialen Kartenaufbau (nicht bei Reglerwechsel) zoomt die Karte automatisch auf die komplette Verlängerung (`fitBounds`); gilt identisch in allen vier Einbindungen (Location-/Chancen-Detail, normal + Vollbild). |
| 2026-07-09 | US-127 | Host kann bereits beim Anlegen einer neuen Location optional ein Beispielbild auswählen; automatischer Upload direkt nach erfolgreichem Speichern mit gleicher Validierung/Verkleinerung/Kompression wie im Bearbeiten-Modus (US-120). |
| 2026-07-09 | BUG-66 | „Höhenwinkel Spitze" in der Anlage-Vorschau zeigte immer 0,0°, weil der Geländeunterschied nie ermittelt wurde. Vorschau nutzt jetzt denselben automatischen Höhendaten-Abruf wie bereits gespeicherte Locations (einmal pro Anfrage, kein Mehrfach-Call). Released als v1.22.4. |
| 2026-07-09 | BUG-67 | Neu angelegte Location erscheint jetzt sofort ohne App-Neustart auf der Karte UND in der Locations-Liste, auch wenn der Karten-Tab beim Speichern bereits offen war: `AddLocation.save()` stößt nach dem Speichern zusätzlich zu `Locations.load()` explizit `MapView.loadMarkers()` (nur falls Karte schon initialisiert) und einen defensiven `Locations.render()` an. Nebenbei behoben: `MapView.loadMarkers()` entfernte bislang die vorher geladenen Marker nicht von der Karte, bevor neue hinzugefügt wurden — bei wiederholtem Aufruf wären doppelte Marker entstanden; jetzt werden alte Marker vor dem Neuaufbau korrekt per `removeLayer` entfernt. Aktive Kartenfilter werden nach dem Neuladen weiterhin angewendet (bestehender `applyFilter()`-Aufruf am Ende von `loadMarkers()`). Status In Progress — Test ausstehend. |
| 2026-07-10 | US-129 | Filter "Hat Beispielbild" für Locations, Karte, Feed und Kalender |
| 2026-07-10 | US-128 | Bauwerkshöhe (`subject_height_m`) und Bauwerksbreite (`subject_width_m`) sind jetzt im Bearbeiten-Modus nachträglich korrigierbar (analog zur bestehenden Fotografen-Standhöhe), für Custom- und Standard-Locations; eine Korrektur löst automatisch eine Neuberechnung (Feed + Kalender) aus, analog zur Koordinatenkorrektur, und übersteht jetzt zuverlässig sowohl Server-Neustart als auch den precompute-Subprozess. Nebenbefund im selben Ticket: Scout-Platzhalter-Erkennung von einer 20-Meter-Heuristik auf ein explizites Feld `subject_height_researched` umgestellt (verhinderte vorher fälschlichen Ausschluss korrekt recherchierter Locations aus der Scout-Pipeline). Code-Release als v1.22.6 (Health-Check auf Produktion bestätigt). Vollständiger Neuberechnungslauf über alle Bestandslocations abgeschlossen (162/162 Locations, 59.130 neu berechnet, keine Fehler im Log). |
| 2026-07-10 | BUG-69 | Bildausschnitt-Button jetzt gut lesbar auf jedem Foto-Hintergrund |
| 2026-07-11 | BUG-70 | Datenbank-Korruption in `location_qa_values` durch einen harten Prozess-Abbruch (OOM-Kill) repariert. Code-Härtung: `LocationStore.integrity_check()` liefert jetzt eine vollständige Fehlerliste statt nur einer einzelnen Zeile und wirft auch bei stark beschädigten Datenbanken keine ungefangene Exception mehr; Ladefehler beim Server-Start werden jetzt als ERROR statt WARNING geloggt (fällt beim Monitoring auf statt unterzugehen); zusätzlich läuft beim Start jetzt generell eine Integritätsprüfung. Für eine eventuelle erneute Reparatur steht das Skript `tools/repair_bug70_qa_values.py` bereit. |
| 2026-07-11 | BUG-71 | Beispielbild-Upload (Location-Detail + Anlage-Formular) behält den Location-/Draft-Bezug jetzt robust über die asynchrone Fotoauswahl hinweg; fehlt der Bezug dennoch, erscheint ein Toast statt eines stillen Abbruchs. Released als v1.22.11. |
| 2026-07-11 | BUG-75 | Live-Astro-Übersicht übernimmt beim Öffnen aus einem Ereignis (Feed/Kalender-Chance mit gespeichertem Ort UND Entdecken-Modus-Chance ohne Ort) jetzt exakt Datum + Ortszeit (Berlin) des Ereignisses statt „heute"; behebt zusätzlich einen ca. 2-Stunden-Versatz durch fälschlich als Ortszeit interpretierte UTC-Ziffern. Nachtrag: Zeit-Schieberegler startet beim Ereignis-Öffnen zentriert genau auf der Ereigniszeit und lässt sich ±12h in beide Richtungen navigieren (`_windowStart`-Fensterlogik in `AstroLive._curDate()`, additiv/abwärtskompatibel — ohne gesetztes Fenster exakt das alte Kalendertag-Verhalten). Zweiter Nachtrag: Die Zeitanzeige an der Zeitleiste zeigt jetzt zusätzlich das Datum (Format „TT.MM. · HH:MM Uhr“, `AstroLive._clockText()`), einheitlich in allen Render-Pfaden (Live-Timer, Scrub, Pin-Drag, Event-Öffnen). „Jetzt"-Live-Modus (Orts-Übersicht) unverändert außer der neuen Datumsanzeige. Released als v1.22.18. |
| 2026-07-11 | TASK-64 | Backend-pytest-Suite läuft jetzt als Pflicht-Gate vor jedem Deploy (paralleler CI-Job, ~2 Min Laufzeit) |
| 2026-07-11 | BUG-71 | Nachtrag: Service-Worker-Methodenfilter behebt 0-Byte-Bild-Upload auf iOS |
| 2026-07-11 | TASK-66 | Bestehender Playwright-Frontend-Check im CI-Gate (TASK-64) um drei echte Bedien-Durchläufe erweitert: Location über den „+"-Tab anlegen (erscheint danach in `GET /locations` + als zusätzlicher Kartenmarker), Beispielbild gezielt über das Location-Detail-Sheet hochladen (BUG-71-Regressionsschutz, eigener isolierter Host-Login), Wahrscheinlichkeits-Filter auf einen deterministischen Extremwert setzen und zurücksetzen. Kein Cleanup nötig (jeder CI-Lauf startet mit frischer, nicht geteilter Dev-Datenbank). Reines Test-Tooling, keine sichtbare App-Änderung. |
| 2026-07-11 | TASK-65 | Neuer generischer Feld-Rundreise-Test (`test_task_65_field_roundtrip.py`, 65 Testfälle) sichert dauerhaft ab, dass jedes Location-Feld einen Server-Neustart und einen precompute-Lauf übersteht — auch Felder, die es heute noch nicht gibt (Regressionsschutz gegen die BUG-50/61/68-Fehlerklasse). Reines Test-Tooling, keine Produktivcode-Änderung. |
| 2026-07-11 | TASK-67 (Etappe 2) | PRODUCT.md-Pflichtliste weiter automatisiert: neue Testdateien `test_task67_feed_regression.py` (Round-Robin-Cap BUG-48, Dedup, Min-Score-Filter direkt auf `main._filter_feed()`), `test_task67_detail_regression.py` (Sonnenaufgang/-untergang-Azimut inkl. Null-Guard, US-107, end-to-end über `precompute._serialize()`) und `test_task67_orte_regression.py` (≥15 Locations). Für den überwiegenden Rest der 11 restlichen PRODUCT.md-Abschnitte (Global UI, Feed, Filter, Detail, Karte, Quick-Add, Orte, Scout, Einstellungen, Standort-Automatik, Backup) bestand bereits Testabdeckung an anderer Stelle (u.a. `test_us09_sightline.py`, `test_us79_moon_rise_set.py`, `test_us112_weather_map.py`, `test_bug66.py`, `test_bug67.py`, `test_us120.py`/`test_us_125.py`/`test_us_126.py`, `test_us_128.py`, `test_task45/46/47/48_*.py`, `test_task55_image_backup.py`) — diese wurde in PRODUCT.md referenziert statt dupliziert. Standort-Automatik-Abschnitt (11a) ist damit vollständig referenziert automatisiert, Backup-Abschnitt (11b) bis auf die reine Server-Ops-Restore-Funktion (kein Code-Pfad vorhanden). Zwei Grenzfälle bewusst NICHT als automatisiert markiert: (1) automatischer Sichtachsen-Trigger beim Anlegen/Ändern einer Location (Orte-Abschnitt, läuft im precompute-Subprozess, aber ungetestet), (2) Wetter-Overlay-optische Beurteilung (Karte-Abschnitt, nur Teil automatisiert). Reines Test-/Dokumentations-Tooling, keine Produktivcode-Änderung. Filter (3a) und Global UI (Abschnitt 2) bleiben in dieser Etappe komplett unautomatisiert, da alle dortigen Pflicht-Regression-Punkte echte Klick-/DOM-Interaktion oder rein optische Beurteilung voraussetzen (Etappe 3, Playwright). |
| 2026-07-11 | TASK-67 (Etappe 4) | Abschluss-Dokumentation: kompakte „Nur manuell prüfbar"-Restliste am Ende der Datei ergänzt (Abschnitt 15) — sammelt alle Pflicht-Regressions-Punkte aus den Abschnitten 2–11c, die nach den Etappen 1–3 noch keinen Testverweis haben. Zwei bereits bekannte Lücken (Sichtachsen-Auto-Trigger beim Anlegen/Ändern einer Location, Backup-Restore-Funktion) sowie der Wetter-Overlay-Punkt sind darin explizit als Grenzfall/bekannte offene Automatisierungslücke gekennzeichnet, nicht stillschweigend einsortiert. Reine Dokumentationsarbeit, kein Code geändert. |
| 2026-07-12 | TASK-61 | Automatische Server-Sicherung deckt jetzt alle acht Datenbestände ab statt nur zwei — zusätzlich zu Standort-Daten jetzt auch Bewertungen, Vor-Ort-Meldungen, Geräte-Tokens, Kamera-Profile und automatisch ermittelte Qualitätswerte (inkl. manueller Sperren). Zusätzlicher Sicherungs-Zeitpunkt beim täglichen automatischen Berechnungslauf, unabhängig von Standort-Änderungen. Ein Fehler bei einem einzelnen Datenbestand blockiert nicht mehr die Sicherung der übrigen sieben. Released als v1.22.20. Manuelle Prüfung auf dem Produktivserver (echter Sicherungs-Ordner-Abgleich) steht noch aus. |
| 2026-07-12 | TASK-70 | Nachträglich released: `smoke`-Marker auf `test_health_ok` in `test_api_smoke.py` (Ticket war bereits auf Done gesetzt, kein Commit-Bezug im Status-Feld — dieser konkrete Code blieb unkommittiert liegen. Jetzt zusammen mit TASK-72 nachgeholt; die Marker-Registrierung selbst in `pytest.ini` war bereits vorher committet). Reines Test-Tooling, keine Produktivcode-Änderung. |
| 2026-07-12 | TASK-72 | 30 bestehende Testdateien nachträglich mit passenden pytest-Markern (`offline`/`network`/`api`/`regression`/`frontend`/`slow`/`smoke`/`online`) versehen; `online` als achter Marker in `pytest.ini` registriert. `pytest -m <marker>` erfasst jetzt den vollständigen historischen Testbestand (48 Dateien), nicht mehr nur künftig neu geschriebene Tests (TASK-70). Reines Test-Tooling, keine Produktivcode-Änderung. Released Commit `6cf7d79`, CI-Lauf #205 grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 161`). |
| 2026-07-12 | BUG-77 | Wetter-Job für Himmelsröte-/Goldene-Wolken-Berechnung meldet jetzt einen Fehlerzustand („Wetter: Fehler", inkl. Namen der betroffenen Standorte), wenn der Wetterdaten-Abruf für mindestens einen Standort fehlschlägt — vorher zeigte der Status stillschweigend weiterhin „erledigt", obwohl Himmelsröte-Daten fehlten. Erfolgreiche Standorte bleiben unbeeinträchtigt; kein neuer Alarmkanal (weiterhin nur über den bestehenden `/job-status`-Endpunkt sichtbar). Released als v1.22.21, CI-Lauf #207 grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 161`). |
| 2026-07-13 | US-130 | Himmelsröte (RED_SKY) berücksichtigt jetzt zusätzlich ein Dunst-/Aerosolsignal, nicht mehr nur Wolkenbedeckung: neue Funktion `fetch_aerosol_forecast()` (Open-Meteo Air Quality API, `domains=cams_global`) in `weather.py`, neue Konstante `RED_SKY_AOD_THRESHOLD` (0.3, inklusiv); `should_generate_red_sky_event()` löst jetzt bei Wolkenbedingung ODER signifikantem Dunstwert aus (Richtungsprüfung gegen den Sonnen-Gegenpunkt bleibt unverändert wie seit US-113). Wetter- und Aerosol-Abruf laufen parallelisiert (`asyncio.gather`) in `_weather_overlay()`, kein zusätzlicher Latenz-Aufschlag. Detail-Sheet-Text unterscheidet jetzt Dunst- vs. Wolken-Auslöser. Schlägt der Aerosol-Abruf fehl, fällt die Prüfung sauber auf die bisherige reine Wolkenbedingung zurück (kein Absturz, sichtbar über denselben BUG-77-Job-Status-Mechanismus statt still). „Goldene Wolken" (GOLDEN_CLOUDS) unverändert. Zwei Live-Bugs während der Testphase gefunden und behoben: ungültiger `domains`-Parameterwert sowie die Erkenntnis, dass `cams_europe` an Berlin/Brandenburg-Koordinaten keine Aerosoldaten liefert (nur `cams_global` liefert reale Werte) — live verifiziert (498/498 Events mit echtem Dunstwert nach Fix). Zwei nicht-kritische Folgepunkte (Aerosol fehlt im schnellen Einzelabruf-Pfad `_weather_overlay_single`; fehlender Regressionstest für isolierten Aerosol-Abruf-Fehler) als TASK-73 ausgelagert. |
| 2026-07-13 | TASK-73 | US-130-Nacharbeit: Der schnelle Einzelabruf-Pfad (`_weather_overlay_single()`, US-106-Fast-Path beim Anlegen/Ändern einer Location) holt jetzt parallel zum Wetter auch das Aerosol-/Dunstsignal ab, statt es erst beim nächsten 3-Stunden-Cronlauf nachzuholen; schlägt nur der Aerosol-Abruf fehl, bleibt der bestehende non-fatale Fallback (reiner Wolken-Check) erhalten. Zusätzlich neuer Regressionstest für den bisher ungetesteten Job-Status-Fehlerpfad „nur Aerosol-Abruf schlägt fehl" in `_weather_overlay()`. Released als v1.22.23, CI-Lauf #211 grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 161`), gemeinsam mit TASK-74. |
| 2026-07-13 | TASK-74 | Reines internes Refactoring: `_generate_cloud_mood_events()` und `_weather_overlay()` in `backend/main.py` (durch die US-130-Erweiterung über den 80-Zeilen-Threshold von `tools/refactor_check.py` gewachsen) in kleinere Helper-Funktionen aufgeteilt, Signaturen/Verhalten unverändert, bestehende Tests weiterhin grün. Kein sichtbares App-Verhalten geändert. Released als v1.22.23, CI-Lauf #211 grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 161`), gemeinsam mit TASK-73. |
| 2026-07-14 | US-131 | Himmelsröte- und Goldene-Wolken-Karten fragen ihren Dunst-/Wolkenwert jetzt an einem 30 km entlang der Sichtachse projizierten Punkt statt am Fotografen-Standort ab (getrennte Projektionen für beide Kartentypen, kein Fallback bei Fehlschlag); zusätzlich wurde die externe Wetter-API-Anbindung gedrosselt (Semaphore max. 5 gleichzeitige Requests + 0,15 s Pacing), nachdem Live-Messungen signifikantes Rate-Limiting zeigten. Released als v1.22.24, CI-Lauf #213 grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 161`), gemeinsam mit US-132. |
| 2026-07-14 | US-132 | Neuer Event-Typ „Rote Wolken" (RED_CLOUDS): hohe Wolken (Cirrus) glühen in Sonnenrichtung rot/purpurn, wenn die Sonne bereits unter dem Horizont steht (Blaue Stunde); dafür wurde auch ein neuer, zur bestehenden „Blaue Stunde" (Abend) symmetrischer „Blaue Stunde Morgen"-Event-Typ eingeführt. Released als v1.22.24, CI-Lauf #213 grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 161`), gemeinsam mit US-131. |
| 2026-07-14 | BUG-78 | Apple-Maps-Koordinatenformat im Standort-/Motiv-Feld wird jetzt akzeptiert |
| 2026-07-14 | TASK-78 | QA-Teilerfolg konsistent behandeln: Prüf-Eintrag wird immer nachgezogen, PRAGMA busy_timeout ergänzt |
| 2026-07-14 | TASK-77 | Beim Löschen einer Location (hart bei selbst angelegten, per Tombstone bei Standard-Locations) werden jetzt auch ihre automatisch erzeugten Prüf-Daten (Beschreibung, Blickwinkel-Empfehlung, Brennweiten-Tipp) mitentfernt — keine verwaisten Datensätze mehr nach dem Löschen. Released als v1.22.27, CI-Lauf #221 grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 161`); Verhalten zusätzlich manuell bestätigt (hartes Löschen + Softlöschen). |
| 2026-07-14 | TASK-76 | Reines internes Refactoring: `_apply_weather_to_event()` und `_fetch_weather_and_aerosol()` in `backend/main.py` (durch die US-131-Erweiterung über den 80-Zeilen-Threshold von `tools/refactor_check.py` gewachsen) in 6 kleinere Helper-Funktionen aufgeteilt, Signaturen/Verhalten unverändert, 106 betroffene Tests weiterhin grün. Kein sichtbares App-Verhalten geändert. Released als v1.22.28, CI-Lauf #223 (nach Re-Run) grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 161`). Im ersten CI-Lauf Zeitüberschreitung durch einen vorbestehenden, unabhängigen Bug entdeckt (ungemockter Ephemeriden-Download in `test_astronomy_regression.py` ohne Timeout/Skip-Logik in CI) — als Folgeticket vorgesehen. |
| 2026-07-14 | TASK-60 | Reines internes Refactoring: `patch_location()` in `backend/main.py` in vier Helper-Funktionen aufgeteilt (`_validate_patch_fields`, `_compute_patch_persist_fields`, `_persist_location_patch`, `_trigger_patch_recompute`), Signaturen/Verhalten unverändert. Kein sichtbares App-Verhalten geändert — PATCH-Endpunkt-Verhalten (Response-Form, Statuscodes, Recompute-/Backup-Trigger) exakt unverändert. Released als v1.22.29, Health-Check bestätigt. |
| 2026-07-14 | BUG-79 | CI-Ephemeriden-Download gecacht + timeout-abgesichert, irreführender Kommentar + Marker-Fehlklassifizierung korrigiert |
| 2026-07-15 | TASK-51 | Reines internes Refactoring: `startup()` in `backend/main.py` (durch mehrere frühere Erweiterungen über den 80-Zeilen-Threshold von `tools/refactor_check.py` gewachsen, 100 Zeilen) in vier Helper-Funktionen aufgeteilt (`_startup_integrity_check`, `_startup_check_discover_schema`, `_prewarm_calendar`, `_startup_setup_scheduler`), Signaturen/Verhalten unverändert — Test-/Sandbox-Kurzschluss, Lade-Reihenfolge, Fehlerbehandlung und Scheduler-Bindungstechnik bleiben exakt erhalten. Kein sichtbares App-Verhalten geändert. Released als v1.22.30, CI-Lauf #228 grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 164`). |
| 2026-07-15 | TASK-41 | Reines internes Refactoring: `_run_single_location_flow()` in `backend/precompute.py` (81 Zeilen, 1 über dem 80-Zeilen-Threshold von `tools/refactor_check.py`) in vier Helper-Funktionen aufgeteilt (`_refresh_single_location_elevation`, `_check_single_location_sightline`, `_refresh_single_location_feed`, `_refresh_single_location_calendar`), jede mit eigenem lokalem Fehlerhandling wie im Original (ein Fehler in einem Schritt bricht die übrigen nicht ab). Kein sichtbares App-Verhalten geändert. In einer ersten Umsetzungsrunde fehlte das Fehlerhandling bei zwei der vier Helfer — von einer unabhängigen Verifikation gefunden und in einer zweiten Runde nachgebessert, danach erneut unabhängig bestätigt. Neuer Regressionstest `test_task-41_precompute_refactor.py` (4 Fälle) deckt Merge-Verhalten und Fehlerisolation ab. Released als v1.22.31, CI-Lauf #230 grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 164`). |
| 2026-07-15 | TASK-79 | Marker-Tabelle in `backend/tests/README.md` auf alle 59 Testdateien erweitert (Option B, gegen Empfehlung gewählt); korrigiert zudem die durch BUG-79 veraltete Marker-Zeile zu `test_astronomy_regression.py` (jetzt 5× `offline` + 4× `online` statt nur „offline") sowie die vorbestehende `test_api_smoke.py`-Ungenauigkeit (real `api` + `smoke`, nicht „network"). Neuer Regressionstest `test_task79_readme_marker_sync.py` (3 Fälle) prüft künftig automatisiert, dass jede Testdatei in der README-Tabelle vorkommt und die BUG-79-relevanten Angaben stimmen. Reines Test-Tooling, kein Produktivcode geändert. Released Commit `09d4ff4`, CI-Lauf #232 grün, Health-Check bestätigt (`version 2.0.0`, `locations_count 164`). |
| 2026-07-16 | BUG-63 | Alignments-Berechnung entblockt (Fenster-Engine + parallele Geländehöhenabfrage), Race-Fix für gleichzeitige Requests |
| 2026-07-16 | BUG-80 | Kopfzeile springt beim Filtern nicht mehr: Infozeile (`#header .subtitle`) bleibt immer einzeilig und wird bei Platzmangel mit „…" gekürzt statt die Header-Höhe zu verändern (Option A). Reines CSS, kein Backend-/API-Bezug. Alle 5 Akzeptanzkriterien manuell auf Mac und iPhone (Ursprungsgerät des gemeldeten Bugs) bestätigt. |
| 2026-07-16 | US-133 | Kartenschwenk bei Koordinaten-Eingabe (Anlegen + Bearbeiten, alle 4 Felder): sobald ein Koordinatenfeld nach vollständiger, gültiger Eingabe verlassen wird (Blur), schwenkt die kleine Formular-/Bearbeiten-Karte automatisch zur neuen Position — aktuelle Zoomstufe bleibt erhalten (reines `panTo`, keine feste Zoomstufe). Weg-Gate-Entscheidung gegen ursprüngliche Empfehlung (Blur statt live, Zoom-Erhalt statt fester Zoomstufe 14). Reines Frontend, kein Backend-/API-Bezug. Released als v1.22.34, CI-Lauf #237 grün (Frontend-Check/Playwright, Backend-Tests/pytest, Deploy), Commit `13151d3`, Health-Check bestätigt (`version 2.0.0`, `locations_count 172`). Alle 9 Akzeptanzkriterien manuell bestätigt. |
| 2026-07-17 | TASK-84 | Leaflet und astronomy-engine werden nicht mehr von fremden CDNs (cdnjs.cloudflare.com, cdn.jsdelivr.net) geladen, sondern lokal aus `web/vendor/` selbst gehostet (Weg-Gate-Option B) — die App ist damit unabhängig von der Erreichbarkeit dieser beiden CDNs, ein kompromittiertes CDN kann keinen Code mehr einschleusen. Die CSP in `deploy/Caddyfile` (TASK-82) wurde passend verschlankt: `cdnjs.cloudflare.com`/`cdn.jsdelivr.net` aus `script-src`/`style-src`/`connect-src` entfernt. Automatisiert: `backend/tests/test_task84.py` (Marker `offline`) prüft lokale Pfade + verschlankte CSP. Manuell bestätigt (Browser-Test: Netzwerk-Tab zeigt lokale `/vendor/...`-Quelle für beide Bibliotheken, keine Konsolenfehler, alle drei Kartenansichten funktionsfähig). Released v1.22.37, GitHub Actions CI grün (Frontend-Check Playwright, Backend-Tests inkl. `test_task84.py`, Deploy), Health-Check bestätigt (`version 2.0.0`, `locations_count 172`) auf https://fotoalert.stephanschumann.com. |
| 2026-07-16 | TASK-83 | Sitzungs-Ticket vom JS-lesbaren `localStorage`/Bearer-Header auf HttpOnly/Secure/SameSite=Lax-Cookie (`fa_session`, 30 Tage) umgestellt — ein XSS-Skript kann das Ticket dadurch nicht mehr auslesen. `/login`-Antwort enthält kein `token`-Feld mehr (nur `role`); neuer `POST /logout` verfällt das Cookie serverseitig; `require_auth`/`require_host` lesen ausschließlich das Cookie, kein Header-Fallback (Zwangs-Logout aller alten Bearer-Token). CORS von `allow_origins=["*"]` auf explizite Origin-Liste (Prod-Domain + `http://localhost:8000`) + `allow_credentials=True` umgestellt (Voraussetzung für Cookie-Auth). Settings-Sheet: `fa_api`-Freitextfeld durch feste Auswahl ersetzt. Rollen-Anzeige liest jetzt `fa_role` aus localStorage statt Token-Präfix (löst BUG-47-Mechanismus ab, weiterhin nur UI-Anzeige, keine Autorisierung). Automatisiert: `test_task-83.py` (10/10 grün) + volle Regressionssuite migriert (Cookie-Isolation in `conftest.py`, Header-basierte Legacy-Tests auf Cookie-Login umgestellt: `test_us66_login.py`, `test_task67_auth_regression.py`, `test_bug47.py`, `test_bug63.py`, `test_us120.py`, `test_us_125.py`, `test_us_126.py`, `test_task77_qa_cleanup_on_delete.py`). Status In Test — manuelle Browser-Verifikation (Chrome + Safari, Cookie-Attribute/Secure-über-localhost) noch ausstehend. |
| 2026-07-16 | TASK-82 | Sechs Schutz-Header live über Caddy ausgeliefert: die vier vorher schon im Programm-Ordner vorhandenen (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, HSTS, Server-Software-Hinweis entfernt) kamen zuvor nie auf dem Server an — der normale Release-Weg (`deploy/deploy.sh`) rührte die Webserver-Konfiguration nie an, nur die einmalige Ersteinrichtung tat das. Neu: Content-Security-Policy (eigene Seite, die zwei Bibliotheks-CDNs, die drei Kartenkachel-Anbieter, eingebetteter Code bewusst erlaubt) und Permissions-Policy (alles gesperrt außer Standortabfrage + Zwischenablage). Option B umgesetzt: `deploy/deploy.sh` gleicht die Konfigurationsdatei jetzt bei jedem Release automatisch mit dem Server ab (inkl. Prüfmodus vor dem Neuladen, damit ein Tippfehler den Webserver nicht lahmlegt). Im Live-Browser-Test zwei Nachbesserungsrunden nötig: `connect-src` fehlte zunächst komplett (der Service Worker lädt Fremd-Inhalte per eigenem `fetch()` nach, das läuft über `connect-src`, nicht über `script-src`/`img-src`) — nach Ergänzung liefen Karte, Sternenberechnung, GPS-Knopf, Kopieren-Knopf und Login/Service-Worker unverändert. Zusätzlich ein vorbestehender, unabhängiger Fund behoben: die Server-eigene Log-Datei hatte beim ersten echten Einsatz falsche Besitzrechte (root statt Webserver-Nutzer), einmalig korrigiert. Released als v1.22.35 + 2 Nachbesserungscommits, Health-Check bestätigt (`version 2.0.0`, `locations_count 172`). Alle 8 Akzeptanzkriterien manuell in Safari bestätigt. |
| 2026-07-17 | BUG-81 | Gespeicherte/reflektierte XSS über ungefilterte Text- und Beschreibungsfelder (Standorte, Events, Chancen, Kalender, Verifikation) unterbunden: neue globale Escape-Helfer `esc()` (HTML-Text/Attribute), `isSafeUrl()` (Schema-Whitelist `http(s)://` für Links) und `escJsAttr()` (zweistufige Maskierung für `onclick`-Attribute mit eingebettetem JS-String) in `web/index.html`. Angewendet an allen betroffenen Rendering-Stellen: Karten-Popups (`MapView.loadMarkers`), Orte-Karten (`Locations.render`), Standort-Detailansicht inkl. Bearbeiten-Formular (`LocationDetail`), Verifikations-Abzeichen/-Verlauf/-Formulare (`Verify.*`), Glossar-Suche, Chancen-Karten (`oppCard`, `scoutCard`), Alarm-Chip, Kalender-Ansicht (Titel + Standort), Sheet-Hero (Titel + Standort), Event-Beschreibung, „Nächste Events" im Standort-Detail. Weg-Gate-Entscheidung: bei ungültigem URL-Schema verschwindet der Link-Bereich (Option A) — angewendet auf `locationscout_url`; bei der Pflicht-Attribution der Wetterkarte (`attribution_url`) stattdessen Rückfall auf feste Standardadresse statt den Link wegzulassen. Erste Umsetzungsrunde hatte 10 weitere, im Analyse-Scope übersehene Fundstellen offen gelassen — von Stephans eigenem Test entdeckt (Screenshot mit tatsächlich auslösendem `alert('XSS')` in „Nächste Events"), in einer zweiten Runde vollständig nachgebessert und erneut bestätigt. Refactor-Durchgang fand eine weitere Lücke (`WeatherMap._updateAttribution()`) und schloss sie. Zwei während des Retests gemeldete Verhaltensweisen (Suche wirkt nicht in Kartenansicht; zweites Speichern wirkte sehr langsam) als vorbestehend/unabhängig von BUG-81 identifiziert — ersteres als eigenes Ticket BUG-82 im Backlog erfasst, zweites auf den bekannten Vollständig-Neuladen-Mechanismus nach dem Speichern zurückgeführt. Released als v1.22.38, Commit `8b2c8b7`, CI grün (Frontend-Check Playwright, Backend-Tests pytest, Deploy FotoAlert), Health-Check bestätigt (`version 2.0.0`, `locations_count 172`) auf https://fotoalert.stephanschumann.com. |
| 2026-07-18 | BUG-82 | Textsuche wirkte in der Kartenansicht überhaupt nicht (`Search._triggerRender()` hatte keinen Karten-Zweig, `MapView.applyFilter()` prüfte `Search.query` nie) — behoben über eine zentrale `Filter._matchesSearch()`-Hilfsfunktion (Weg-Gate-Entscheidung gegen Empfehlung: Option B/Zentralisierung statt Option A/Duplikation), die jetzt sowohl `Locations.filter()` als auch `MapView.applyFilter()` speist. Beim Testen des Karten-Fixes zwei weitere, unabhängige Lücken derselben Fehlerklasse entdeckt und auf Stephans Entscheidung in dieses Ticket mit aufgenommen statt als eigene Tickets: Locations-Tab-Wechsel ignorierte eine bereits aktive Suche (`App.nav('locations')` rief `Filter.applyToLocations()` statt `Locations.filter()`), und Scout hatte gar keine Textsuche (`Filter.applyToScout()` ohne Suchbegriff-Check, `Search._triggerRender()` ohne Scout-Zweig — lief ins unsichtbare `Feed.render()`). Scout durchsucht dabei Motivname + Session-Bezeichnung statt Standortname, da Scout-Chancen keine Bindung an eine gespeicherte Location haben. Alle 10 Akzeptanzkriterien (7 ursprüngliche + 3 Scope-Erweiterung) manuell von Stephan bestätigt. |
| 2026-07-20 | TASK-85 | Notwert-Fallback für `FOTOALERT_AUTH_SECRET` entfernt (Security-Audit, Option A): `backend/auth.py::_load_secret()` bricht beim Modul-Import mit `RuntimeError` ab, wenn das Secret fehlt oder leer ist — Prozess startet dann gar nicht, kein Endpunkt wird gebunden. Verhindert ein frei berechenbares Admin-Ticket bei fehlender `.env`. Neuer Test `backend/tests/test_task-85.py` (5 Fälle, Marker `offline`+`regression`), unabhängig verifiziert (Code gelesen, kein zweiter Ladepfad, `conftest.py` setzt Test-Secret nachweislich vor jedem Import). Released als v1.22.40, CI grün (Frontend-Check Playwright, Backend-Tests pytest, Deploy FotoAlert), Health-Check bestätigt (`version 2.0.0`, `locations_count 172`) auf https://fotoalert.stephanschumann.com. |
| 2026-07-20 | TASK-88 | `release.sh` bricht bei ungelöstem Merge-Konflikt (Status-Codes UU/AA/DD/AU/UA/UD/DU über `git status --porcelain`) sofort ab, bevor der Versions-Bump oder irgendein Commit passiert — verhindert den bei US-133 aufgetretenen Ad-hoc-Commit ohne Standard-Message/Tag. Prüfung läuft bewusst vor den `sed`-Edits an `index.html`/`sw.js`, damit ein Abbruch keinen unkommittierten Doppel-Bump-Risikozustand hinterlässt (im Zuge der Implementierung selbst gefunden und korrigiert). Funktional auf echtem Konfliktfall verifiziert (Testbranch mit divergierenden Commits gemerged, `./release.sh` abgebrochen, kein Commit/Tag entstanden, Version unverändert, sauber aufgeräumt). Unabhängig code-verifiziert (alle 4 AKs erfüllt, vollständige Status-Code-Abdeckung, `pipefail`/`|| true`-Zusammenspiel robust). Released als v1.22.41, CI grün (Frontend-Check Playwright, Backend-Tests pytest, Deploy FotoAlert), Health-Check bestätigt (`version 2.0.0`, `locations_count 172`) auf https://fotoalert.stephanschumann.com. |
| 2026-07-22 | TASK-85 | Nachbesserung aus der Refactor-Phase: `_load_secret()` behandelt jetzt auch reine Leerzeichen-Werte als „fehlt" (`strip()`), Login-Flow-Test trägt zusätzlich den `api`-Marker. Kein neuer Funktionsumfang. Released als v1.22.43, CI grün (Frontend-Check Playwright, Backend-Tests pytest — 662 passed/5 failed, alle 5 Fehlschläge nachweislich TASK-86-Regressionen bzw. bekannte Altlasten, keiner in `test_task-85.py` —, Deploy FotoAlert), Health-Check bestätigt (`version 2.0.0`, `locations_count 172`) auf https://fotoalert.stephanschumann.com. |
| 2026-07-22 | TASK-86 | Vier bislang ungeschützte Endpunkte gegen Missbrauch gehärtet: neues Hilfsmodul `backend/rate_limit.py` (schlanke eigene In-Memory-Rate-Limit-Lösung, keine neue Abhängigkeit) an vier Stellen genutzt. `POST /preview-alignment` bekommt eine Häufigkeits-Bremse pro Absenderadresse (20 Aufrufe/Minute; der bereits durch BUG-63 gelöste 14-Tage-Zeitraum-Deckel bleibt unverändert). `GET /calendar`: Kalender-Zwischenspeicher-Schlüssel wird jetzt auf 2 Nachkommastellen gerundet (verhindert unnötiges Cache-Wachstum durch minimal unterschiedliche Score-Schwellen) und auf 200 Einträge mit FIFO-Verdrängung des jeweils ältesten Eintrags gedeckelt. `POST /login`: Sperre nach 5 falschen Passwörtern derselben Absenderadresse innerhalb 15 Minuten (HTTP 429 statt weiterer Passwortprüfung), Zähler setzt sich bei erfolgreichem Login zurück. `POST /register-device`: Geräte-Token wird auf Plausibilität geprüft (20–256 Zeichen, druckbares ASCII/Hex) und die Registrierungshäufigkeit pro Absenderadresse begrenzt. Alle vier Bremsen antworten einheitlich mit HTTP 429 + Klartext-Wartezeit statt stiller Verzögerung. CORS unverändert (bereits durch TASK-83 gelöst, hier nur regressionsgetestet). Nachbesserung während der unabhängigen Verifikation: `client_identity()` las zunächst den ERSTEN Eintrag eines `X-Forwarded-For`-Headers — vom Client selbst fälschbar, dadurch waren alle drei adressbasierten Bremsen umgehbar; behoben auf den LETZTEN Eintrag (in der Ein-Hop-Topologie mit Caddy als einzigem Proxy der garantiert von Caddy selbst gesetzte, nicht clientseitig fälschbare Wert), zusätzlich per dediziertem Regressionstest abgesichert. Automatisiert: `backend/tests/test_task86.py` (30/30 grün, Marker `offline`/`api`/`regression`), in `backend/tests/README.md` nachgetragen. Unabhängige Verifikation bestätigt 9/9 Akzeptanzkriterien, Refactor-Check abgeschlossen. Status In Test — Release durch Stephan noch ausstehend. |

---

## 15. Nur manuell prüfbar — Restliste (Stand 2026-07-11, TASK-67)

**Wozu diese Liste:** Nach den Etappen 1–6 ist ein großer Teil der Pflicht-Regression automatisiert, inzwischen auch der Filter-Bereich größtenteils (TASK-67 Etappe 6). Was hier steht, hat in seinem jeweiligen Abschnitt (oben) noch **keinen** Testverweis — das muss also weiterhin von Hand geprüft werden. Drei Gründe kommen dafür in Frage: (a) reine Optik/Layout/Animation, die kein Test bewerten kann, (b) Verhalten, das nur im echten Safari/iOS auffällt (ein Chromium-Test läuft blind daran vorbei), oder (c) Bereiche, die schlicht noch nicht drangekommen sind bzw. bewusst nur teilweise automatisiert wurden (z. B. der volle Mehr-Ansichten-Effektnachweis für Sichtachse/Hat-Beispielbild sowie der ungeklärte Brennweite-Befund, siehe Abschnitt 3a).

Bei Punkten, wo die Daten dahinter schon automatisch geprüft werden, aber niemand das tatsächliche Bild auf dem Bildschirm anschaut, steht das explizit dabei („Datengrundlage ist bereits geprüft").

Zwei Punkte, die schon länger als bekannte Lücke gelten, sowie ein Grenzfall sind unten **nicht** in die normale Liste gemischt, sondern eigens als „Grenzfall" bzw. „bekannte offene Automatisierungslücke" hervorgehoben.

### Global-UI (Abschnitt 2)
- Kein Tab zeigt seinen Inhalt doppelt
- Kein Sheet öffnet sich ungewollt beim Laden der App
- Theme-Wechsel (hell/dunkel) ändert wirklich alle Farben konsistent
- Alle Icons sind in Safari sichtbar (bekannte WebKit-Falle: ein grüner Chrome-Test würde das nicht auffangen)
- Onboarding erscheint nur beim allerersten Start, nicht mehr danach
- Glossar: Suche filtert live, Accordion klappt auf/zu, „Onboarding erneut ansehen" funktioniert
- Glossar zeigt die 2 neuen Einträge korrekt
- Alle 15 kleinen ⓘ-Erklär-Symbole öffnen den passenden Text
- Kartenlegende-ⓘ wirkt im Ruhezustand klein/dezent, wird bei Berühren gold

### Feed (Abschnitt 3)
- Dass mindestens eine Chance auch wirklich als Karte zu sehen ist (Datengrundlage ist bereits geprüft)
- Overlay antippen schließt das Detail-Sheet wieder
- Filter-Sheet öffnet und schließt sich sauber
- Score-Ring ist optisch korrekt gefüllt (z. B. 75 % = Ring zu drei Vierteln voll) — reine Sehprüfung
- Routine-Events-Filter blendet Goldene-/Blaue-Stunde-Karten sichtbar aus
- Filter-Chips „Mondaufgang"/„Monduntergang" wirken sichtbar auf den Feed
- Dass Mondaufgang-/Monduntergang-Karten wirklich als eigene Karten zu sehen sind (Datengrundlage ist bereits geprüft)
- Dass die Sichtachsen-Pille (Auge-Symbol, Grün/Orange/Rot/Grau) auf der Karte wirklich richtig eingefärbt zu sehen ist (Datengrundlage ist bereits geprüft)

### Filter (Abschnitt 3a) — nach TASK-67 Etappe 6 größtenteils automatisiert, Details siehe Abschnitt 3a
- Brennweiten-Filterwirkung auf Karte/Orte-Tab optisch verifizieren, dass die Pins wirklich nur passend zur Brennweite angezeigt werden (funktional bestätigt korrekt, s. Klärung 2026-07-12 in Abschnitt 3a — nur der sichtbare Effekt noch nicht automatisiert)
- Eventtyp-Sektion ist auf dem Orte-Tab sichtbar ausgegraut (kein automatisierter Test bislang, nur Tageszeit + Wahrscheinlichkeit sind abgedeckt)
- „Sichtachsen-Check wirkt in allen Ansichten" — visueller Effekt auf Kalender/Scout sowie der volle Datenabgleich auf Feed/Locations-Tab (Teilabdeckung: Nicht-Ausgegraut-Sein + Karten-Effekt sind automatisiert, siehe Abschnitt 3a)
- „Hat Beispielbild" wirkt sichtbar auf Karte/Feed/Kalender (Teilabdeckung: nur der Orte-Tab-Effekt ist automatisiert, siehe Abschnitt 3a)

### Detail-Sheet (Abschnitt 4)
- Sheet öffnet mit Slide-up-Animation von unten
- Alle 12 Sektionen vorhanden, keine doppelt, beim Öffnen alle eingeklappt
- Close-Button gut erreichbar (Safe Area, kein Overlap mit Status Bar)
- FOV-Karte lädt sichtbar mit Verbindungslinie, Zielring-Marker und passender Legende
- Vollbild-Symbol der FOV-Karte öffnet/schließt korrekt, Pins darin bleiben unverschiebbar
- Sichtfeld-Kegel-Verlängerung sieht korrekt gestrichelt aus, bleibt beim Reglerwechsel sauber ohne alte Reste
- Ohne Motivkoordinaten erscheint korrekt kein Vollbild-Symbol
- „Zum Kalender"-Download startet wirklich sichtbar
- Street-View-Button erscheint nur, wenn ein Azimut da ist
- Dass Sonnenaufgang/-untergang wirklich sichtbar mit Uhrzeit + Azimut angezeigt werden (Datengrundlage ist bereits geprüft)
- Dass die Sichtachsen-Pille wirklich sichtbar korrekt eingefärbt ist (Datengrundlage ist bereits geprüft)
- Sichtachsen-Linie zeigt den passenden Linienstil (durchgezogen/gestrichelt/unterbrochen/gepunktet) je nach Status

### Karten-Tab (Abschnitt 5)
- Karte lädt sichtbar (kein weißer/leerer Block)
- Mindestens 10 Pins sind sichtbar
- Pin antippen zeigt ein Popup
- Karte bleibt nach Theme-Wechsel sichtbar (kein leerer Block)

**Grenzfall (teilautomatisiert):** Wetter-Overlay „Wolken"/„Niederschlag" — dass überhaupt ein Bild kommt (nicht leer/grau) und Zeitregler/Ebenen-Umschalter grundsätzlich bedienbar sind, ist automatisiert geprüft und lokal grün bestätigt. Ob der Wetterverlauf dabei optisch „weich und gut lesbar" wirkt, bleibt bewusst eine reine Sehprüfung von Hand.

### Quick-Add (Abschnitt 6)
- Sheet öffnet ohne Absturz
- GPS-Button fragt sichtbar nach Standort-Erlaubnis
- Karten-Tap setzt sichtbar den Motiv-Marker + Verbindungslinie
- Ohne gesetzte Punkte erscheint der Hinweis-Toast
- Mit gesetzten Punkten erscheint die Vorschau-Box mit Azimut/Distanz/Höhenwinkel
- Eingetragener Hinweise-Text ist nach dem Speichern sofort sichtbar
- Leer gelassenes Hinweise-Feld speichert normal, ohne automatische Notiz
- Ausgewähltes Beispielbild erscheint nach dem Speichern automatisch im Hero-Bereich
- Ohne Beispielbild erscheint korrekt der Platzhalter „Noch kein Beispielbild"
- Dass ein neuer Marker/Eintrag auf Karte bzw. Orte-Liste wirklich ohne Neuladen sichtbar erscheint (Datengrundlage ist bereits geprüft)

### Orte-Tab (Abschnitt 7)
- Suche „Babelsberg" filtert sichtbar korrekt
- Location-Detail-Sheet öffnet und schließt sauber
- Dass Sonnenaufgang/-untergang im Abschnitt „Ausrichtung" wirklich sichtbar angezeigt werden (Datengrundlage ist bereits geprüft)
- Locations mit Motiv-Koordinaten zeigen die Richtungsklassifizierung sichtbar korrekt
- Locations ohne Motiv-Koordinaten zeigen nur Uhrzeit + Azimut, keinen leeren Abschnitt
- Dass die Sichtachsen-Pille im Location-Detail wirklich sichtbar korrekt eingefärbt ist (Datengrundlage ist bereits geprüft)
- Menüpunkt „Sichtachsen aktualisieren" löst sichtbar eine neue Prüfung aus, Pille aktualisiert sich
- Bearbeiten → Speichern → Änderung ist sofort in Sheet + Liste sichtbar
- Close-Button gut erreichbar (Safe Area)
- Bearbeiten-Karte: Vollbild-Symbol öffnet/schließt korrekt, Pins darin setzbar
- Satellit/Straße-Umschalter auf allen Location-Karten funktioniert sichtbar, gewählte Ansicht bleibt gemerkt
- Dass Beispielbild hochladen/ersetzen wirklich mittig im Hero-Bereich sichtbar erscheint (Datengrundlage ist bereits geprüft)
- Dass der Löschen-Button für ein Beispielbild wirklich mit vorheriger Sicherheitsabfrage arbeitet (Datengrundlage ist bereits geprüft)
- Dass „Ausschnitt wählen" den sichtbaren Bildausschnitt per Klick wirklich verschiebt (Datengrundlage ist bereits geprüft)
- Location mit Hinweise-Text zeigt die eigene Sektion sichtbar nach „Ausrichtung"
- Location ohne Hinweise-Text zeigt korrekt keine leere Sektion

**Grenzfall / bekannte offene Automatisierungslücke:** Dass das Anlegen/Ändern einer Location automatisch eine Sichtachsenprüfung auslöst, läuft im Hintergrund-Prozess, ist aber bislang durch keinen Test abgedeckt — bewusst als offene Lücke vorgemerkt statt stillschweigend als erledigt markiert.

### Scout-Tab / Entdecken (Abschnitt 8)
- Scout-Karte sichtbar mit ScoreRing, Session-Symbol, Motivname, Location-Zeile, Tag-Chips
- Location-Zeile zeigt nur die Himmelsrichtung, ohne Motivname-Dopplung
- Tag-Chips zeigen Wetter, Entfernung, Mondbeleuchtung korrekt
- Kein Standort-Button auf der Karte, nur der Navigation-Button
- Navigation-Button öffnet Apple Maps, nicht die Detailansicht
- Karte antippen öffnet die Detailansicht
- Karte erscheint nicht doppelt
- Klick auf Scout-Karte öffnet das Detail-Sheet vollständig und eingeklappt
- „Als Location speichern"-Button ist sichtbar (echtes Symbol, kein Emoji)
- Klick darauf zeigt Toast + neue Location im Orte-Tab
- AstroLive-Sektion im Scout-Detail öffnet die Bahn-Karte fehlerfrei

### Einstellungen (Abschnitt 9)
- Slider auf 80 % → Feed zeigt sichtbar weniger Karten
- Theme-Umschalter ändert sofort das Erscheinungsbild
- Theme-Auswahl übersteht einen App-Reload
- Dass nach Host-/User-Login sofort die richtige Rollen-Anzeige im Tab zu sehen ist (Server-Logik ist bereits geprüft)

### Login/Auth (Abschnitt 10)
- Dass der Login-Screen für nicht eingeloggte Nutzer wirklich zu sehen ist (Server-Logik ist bereits geprüft)
- Dass nach Host-/User-Login wirklich die passenden Tabs/Rollen-Texte zu sehen sind, auch nach einem Reload (Server-Logik ist bereits geprüft)

### CI/Deploy-Testing (Abschnitt 11c)
- Dass ein Release-Push den Testlauf wirklich mit auslöst
- Dass ein grüner Testlauf den Deploy normal weiterlaufen lässt
- Dass ein roter Testlauf den Deploy wirklich stoppt
- Dass ein neues, vergessenes Location-Feld wirklich namentlich als fehlend gemeldet wird

**Grenzfall / bekannte offene Automatisierungslücke (Backup, Abschnitt 11b):** Die gemeinsame Wiederherstellung von Standort-Daten UND Standort-Fotos (Restore) ist kein automatisierbarer Code-Pfad — es gibt aktuell keine Restore-Funktion in der App, das Zurückspielen ist ein manueller Vorgang direkt auf dem Server. Bleibt bewusst dauerhaft ein manueller Ops-Vorgang, nicht Teil einer künftigen Test-Etappe.
