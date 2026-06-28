# FotoAlert – Qualitätsanalyse & Handlungsempfehlungen

> Basis: 34 Bugs (BUG-01 bis BUG-34), alle Memory/Feedback-Dateien, Testplan, Pre-Mortems und Root-Cause-Dokumentationen.  
> Datum: 2026-06-23

---

## 1. Muster aus den Bugs

### 1.1 Stale-Data / Kein vollständiger Reload (häufigster Bugtyp)

**Betroffene Tickets:** BUG-22, BUG-29, BUG-30, BUG-14

`precompute.py` ignorierte die in SQLite gespeicherten Location-Overrides vollständig — es lud immer die Basis-Koordinaten aus `data/locations.py`. Das war kein gelegentlicher Fehler, sondern ein strukturelles Versäumnis: der Recompute-Prozess und der Server teilten nicht dieselbe Datenquelle. Folge: Selbst nach einem Patch einer Location rechnete das System mit veralteten Koordinaten weiter — und das stille, weil der `coordinates_hash` unverändert blieb und „0 neu berechnet" im Log erschien.

Parallel dazu: BUG-30 wurde zunächst mit einer In-Memory-Mutation gefixt (`loc.name = newName`) statt einem Server-Fetch — funktionierte kurz, brach bei externen PATCHes. BUG-22: PATCH-Endpoint hatte eine hartcodierte Whitelist, die neue Felder nicht erfasste.

**Muster:** Jedes Mal wenn Daten an mehreren Stellen leben (In-Memory-Server, SQLite-Overrides, Cache-Files, Frontend `Locations.all`), entsteht eine Synchronisationsschuld, die erst bei einem Usecase-Test sichtbar wird.

### 1.2 UI-State nicht komponentenübergreifend synchronisiert

**Betroffene Tickets:** BUG-23, BUG-28, BUG-02, BUG-08

Filter werden im Feed implementiert, aber nicht in der Kartenansicht (`FilterSheet._applyLive()` hatte keinen `'map'`-Branch). `Locations.all` wird nur beim Locations-Tab-Öffnen geladen, nicht beim App-Start — daher ist der Schwierigkeitsfilter wirkungslos bis der User diesen Tab besucht hat (BUG-28). Das ist ein bekannter DOM-Gotcha, aber er wurde erst durch einen Bug-Report sichtbar.

**Muster:** Features werden pro Komponente implementiert, ohne systemisches „welche anderen Komponenten müssen diesen State kennen?"-Thinking.

### 1.3 iOS/PWA-spezifische Layoutfehler (wiederkehrender Bugtyp)

**Betroffene Tickets:** BUG-07, BUG-13, BUG-15, BUG-17, BUG-19, BUG-25, BUG-34

Mindestens 6 Bugs betrafen iOS-spezifisches Verhalten: Close-Buttons hinter der Dynamic Island oder Safe Area, Sheets die scrollten statt sticky blieben, Overlays die Desktop-Max-Width ignorierten, das Edit-Overlay das auf iPhone rausragt. Diese Bugs waren ausnahmslos auf echtem Gerät reproduzierbar, nicht im Desktop-Browser. Der Testplan enthält manuelle UI-Tests — aber sie sind nicht Teil des automatisierten CI-Gates.

**Muster:** iOS-PWA-Tests finden nicht statt, bevor Code live geht.

### 1.4 Regressionen: Gefixte Bugs kommen zurück

**Betroffene Tickets:** BUG-27 als potenzielle Regression von BUG-14

BUG-14 (Kalender leer nach Cron) wurde in 2026-06-18 gefixt. BUG-27 (365-Tage-Kalender leer) wurde wenige Tage später gemeldet und als „mögliche Regression von BUG-14" eingestuft. Der Testplan enthält eine Regressions-Checkliste (Abschnitt 9), aber sie wird manuell ausgeführt — nicht automatisch bei jedem Deploy. TASK-21 (Playwright-Gate in CI) wurde implementiert, deckt aber keine Kalender-Datenpfade ab.

### 1.5 Kleine Berechnungsfehler mit großem Sichtbarkeitseffekt

**Betroffene Tickets:** BUG-01, BUG-03, BUG-18

BUG-18: Frontend dividierte `moon_earth_distance_km` nochmals durch 1000 → zeigte ~364 km statt 364.312 km. BUG-01: Brennweiten-Empfehlung ignorierte `distance_m` der Location. BUG-03: Scheinbare Größe mit Horizontaldistanz statt Schrägdistanz gerechnet. Diese Bugs entstanden, weil mathematische Formeln und Einheitenumrechnungen ohne automatisierten Zahlen-Check implementiert wurden.

---

## 2. Wo Agents nicht wie erwartet agieren

### 2.1 Annahmen über Codebase werden nicht gegen echten Code verifiziert

**Konkretes Beispiel:** BUG-29 Pre-Mortem — die Spec nahm an, der Single-Recompute rechne mit den neuen Koordinaten, es fehle „nur" der Kalender-Write. Der Live-Test zeigte die **tiefere Ursache**: `precompute.py` wendet Overrides nie an. Die Spec war auf Basis einer falschen Prämisse gebaut.

Die Pre-Mortem-Gegenmaßnahme für US-67 basierte auf der Annahme „Backend setzt `composition_analysis` auf None für Nicht-Alignment-Events". Tatsächlich setzt das Backend sie für Goldene Stunde + Milchstraße ebenfalls — weil `_composition_analysis` nur Geometrie, nicht Event-Typ prüft. Erst beim Test entdeckt.

**Regel, die verletzt wird:** `feedback_validate_premise` — vor Wahl eines Ansatzes den echten Engpass am Code prüfen, nicht der vermuteten Root-Cause vertrauen.

### 2.2 Stille Entscheidungen während der Implementierung

Aus `feedback_assumptions_clarification`: Agents treffen Design- und Funktionsentscheidungen eigenständig (Farben, Layout, Features), während wichtigere Funktionen (z.B. Persistenz) unvollständig bleiben. Das taucht erst im User-Testing auf.

Die Leitlinie ist bereits dokumentiert — aber die Grenze zwischen „klar aus Kontext ableitbar" und „funktional kritisch" wird nicht konsistent gezogen. Besonders riskant: wenn ein Agent eine falsche technische Annahme trifft (wie in BUG-29) und diese Annahme still als Basis für die Implementierung nimmt.

### 2.3 Done zu früh gesetzt

Mindestens zweimal (US-89, BUG-27) wurde Done gesetzt, bevor das Release-Bundle vollständig und AKs ohne Pending-Marker waren. `feedback_done_gate_release_bundle` und `feedback_release_before_done` existieren als Memory — aber sie sind reaktiv entstanden (nach dem Fehler), nicht proaktiv in die Skills eingebaut.

### 2.4 Kanban läuft aus dem Sync

Das Kanban-Artifact wurde nicht bei jeder Ticket-Bewegung aktualisiert — weil die Regel in manchen Skills fehlte. Das Board zeigte 22 Done, obwohl 61 erledigt waren. Die Lane-Auflösungslogik des Generators war kaputt (matchte `~~`-Headings nicht, las veraltetes `Status`-Feld statt Heading-Marker).

---

## 3. Testabdeckung — wo sie nicht reicht

### 3.1 Keine automatisierten Tests für Berechnungskorrektheit

Der Testplan enthält manuelle Astronomie-Präzisionstests (Abschnitt 7), aber keine automatisierten Unit-Tests für:
- Haversine-Distanzberechnung
- Höhenwinkel-Formel
- Brennweitenempfehlung in Abhängigkeit von `distance_m`
- Einheitenumrechnung (km ↔ m, UTC ↔ Lokalzeit)

Diese sind genau die Fehlerklasse, die BUG-01, BUG-03, BUG-18 produziert hat.

### 3.2 Kein Regressionstest für Cache-Konsistenz

Es gibt keinen automatisierten Test der prüft:
- Nach PATCH Location: ist `opportunities.json` für diese Location aktualisiert?
- Nach PATCH Koordinaten: stimmen Koordinaten im Cache mit SQLite-Overrides überein?
- Nach Cron-Lauf: enthält `calendar.json` ≥ N Events?

Abschnitt 9 (Regressions-Checkliste) ist manuell. Der Regression-Check in `precompute.py` (`feed < 5 Events → logger.error`) ist gut — aber er ist erst nach BUG-14 eingebaut worden, nicht vorher.

### 3.3 Keine iOS/PWA-Tests in CI

Der gesamte iOS-Safari-Testzweig ist manuell. Das bedeutet: UI-Bugs wie BUG-19, BUG-25, BUG-34 (Overlays, Safe Area, Zoom) gehen unbemerkt in Production. Playwright läuft im Desktop-Chrome-Modus — kein Mobile Viewport, kein Safari-WebKit.

### 3.4 Fehlende Edge-Case-Tests im Testplan

Testplan Abschnitt 8.2 deckt zwei Edge Cases ab (gleicher Punkt, ungültige Koordinaten). Nicht abgedeckt:
- Filter aktiv, aber `Locations.all` noch nicht geladen (= BUG-28)
- Location-Name der auf einen bestehenden Namen gesetzt wird
- Zweiter PATCH auf dieselbe Location bevor Recompute abgeschlossen ist
- Cache-Datei fehlt beim Serverstart
- Cron schlägt fehl — wie verhält sich die App?

### 3.5 Test-Erwartungswerte nicht maschinenprüfbar

Astronomie-Tests vergleichen Ergebnisse mit `timeanddate.com` — manuell. Es gibt keine automatisierte Referenz-Assertion, die z.B. „Sonnenuntergang Berlin am 2026-06-23 = 19:21 UTC ± 2min" als Dauertest eingebaut hat.

---

## 4. Regressionstesting — die strukturelle Lücke

TASK-21 (Playwright-Gate vor Deploy) ist implementiert. Aber:

- Die Frontend-Tests (TASK-20) prüfen Visualisierungen und Links, nicht Datenkorrektheit
- Kein Backend-Regressions-Bundle das nach jedem Deploy ausgeführt wird
- Die manuelle Checkliste aus Abschnitt 9 TESTPLAN wird nicht erzwungen
- BUG-27 (Kalender-Regression) wäre mit einem Post-Deploy-Check auf `calendar.json`-Größe sofort sichtbar gewesen

Der Regressions-Check ist reaktiv: `precompute.py` loggt einen Error wenn Feed < 5 Events. Es gibt keinen Alert oder Monitoring-Hook, der Stephan bei einem Cron-Fehler informiert (US-38 „Observability & Self-Healing" steht noch im Backlog, nicht erledigt).

---

## 5. Performance und Sicherheit

### 5.1 Performance

Batch-Precompute (`--full = ~8h`) wurde als Architektur-Risiko erst spät adressiert (TASK-25 — On-Demand Ephemeriden-Engine). Bis dahin war jede Koordinatenänderung einer Location potenziell ein 8h-Neuberechnung-Trigger.

Keine Laufzeitmessungen in der Implementierungsphase neuer Features (z.B. Scout-Tab US-70 mit 12 Subjects × 448 Timesteps — der Implementierungshinweis erwähnt eine Batch-Optimierungsoption, aber sie wurde nicht gemessen, sondern als „ggf. prüfen" vermerkt).

Response-Zeit-Tests (Testplan Abschnitt 8.1) sind manuell — kein p95-Monitoring im Betrieb.

### 5.2 Sicherheit

Die Auth-Implementierung (US-66) bot zunächst Option A (UI-Gate, API offen) und Option B (Backend-Schutz). Die Analyse empfahl korrekt Option B — aber der Entscheidungspunkt wäre nicht entstanden, wenn API-Absicherung als Default-Anforderung für alle neuen Endpoints gegolten hätte.

Bekannte, dokumentierte Schwächen:
- `deviceId` (localStorage-UUID) ist client-spoofbar. Explizit als „Komfort-/UX-Grenze, kein Sicherheits-Audit" dokumentiert. Echte Eigentümerschaft kommt erst mit US-75.
- `localStorage`-Daten (Verifikationen, Ratings, Push-Token) werden von iOS nach 7 Tagen Inaktivität gelöscht. Einige dieser Daten sind inzwischen serverseitig persistiert, andere noch nicht (TASK-23 ist noch offen).
- Keine Input-Validierung jenseits der PATCH-Whitelist dokumentiert. Koordinaten werden im Testplan auf Plausibilität (HTTP 400) geprüft — aber nicht auf Injection-Angriffe oder extrem große Werte die Ephemeriden-Berechnungen zum Absturz bringen.

---

## 6. Handlungsempfehlungen — direkt umsetzbar

Die folgenden Empfehlungen sind nach Aufwand/Wirkung sortiert. Sie können als Tickets ins Backlog wandern.

---

### 🔴 P0 — Sofort: Annahmen über Codeverhalten verifizieren bevor Spec geschrieben wird

**Problem:** BUG-29 und US-67 wurden auf falschen Prämissen spezifiziert. Der tatsächliche Codefehler war tiefer als angenommen.

**Maßnahme:** In den `fotoalert-analyze`-Skill eine verpflichtende Phase einbauen: **„Code-Verifikation vor Pre-Mortem"** — der Agent grep't die betroffenen Funktionen, liest die relevanten Code-Stellen und prüft seine Annahmen gegen den tatsächlichen Code, bevor er Pre-Mortem-Szenarien formuliert.

Konkret: vor jeder Spec prüfen ob `precompute.py`, `main.py` und `store.py` dieselben Daten lesen (Basis-LOCATIONS vs. SQLite-Overrides vs. In-Memory).

---

### 🔴 P0 — Sofort: Automatisierter Post-Deploy-Check

**Problem:** BUG-14 und BUG-27 (Kalender leer nach Cron/Deploy) wären mit einem einfachen Größencheck auf `calendar.json` sofort erkannt worden.

**Maßnahme:** In `deploy.yml` nach dem Deploy-Step einen Health-Assertion-Step einbauen:

```bash
# 60s nach Deploy: Feed + Kalender prüfen
sleep 60
FEED=$(curl -s "https://fotoalert.stephanschumann.com/opportunities?min_score=0.1" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[ "$FEED" -gt 5 ] || (echo "FEHLER: Feed leer nach Deploy" && exit 1)
```

Verwandter Backlog-Eintrag: US-38 (Observability) vorgezogen oder als Mini-TASK eigenständig anlegen.

---

### 🔴 P0 — Sofort: `Locations.all` beim App-Start laden (BUG-28 beheben)

**Problem:** Schwierigkeitsfilter wirkungslos bis der User den Locations-Tab öffnet.

**Maßnahme:** In der App-Initialisierung `Locations.all` laden (oder einen Lazy-Trigger im Filter einbauen, wenn Schwierigkeitsfilter aktiv und `Locations.all` leer ist). BUG-28 ist offen — als P0 einplanen.

---

### 🟠 P1 — Nächster Sprint: Automatisierte Berechnungs-Assertions

**Problem:** BUG-01, BUG-03, BUG-18 — Formelfehler werden nicht automatisch erkannt.

**Maßnahme:** Drei parametrisierte pytest-Tests anlegen, die mit Referenzwerten aus `timeanddate.com` vergleichen:

```python
def test_haversine_babelsberg_pfingstberg():
    d = haversine(52.3975, 13.0976, 52.4158, 13.0688)
    assert 3100 <= d <= 3300, f"Distanz {d:.0f}m außerhalb Toleranz"

def test_moon_earth_distance_unit():
    # Aus Cache laden, prüfen ob Wert > 300_000 (also in km, nicht m)
    ...

def test_sunrise_berlin_today_utc():
    # Skyfield-Aufgang innerhalb ±2min von Referenzwert
    ...
```

Diese Tests laufen als Teil der CI-Suite vor jedem Deploy.

---

### 🟠 P1 — Nächster Sprint: Cache-Konsistenz-Test nach PATCH

**Problem:** Nach `PATCH /locations/{id}` kann der Cache veraltet sein — ohne automatischen Check unbemerkt.

**Maßnahme:** Einen Integrations-Test anlegen (analog zu `test_bug29_calendar_single_recompute.py`):

```python
def test_patch_coordinates_updates_feed_cache():
    # PATCH Location mit neuen Koordinaten
    # Warte auf Recompute-Abschluss
    # Lies opportunities.json → prüfe ob Koordinaten = neue Werte
    ...
```

Ebenfalls: sicherstellen dass `precompute.py` nach BUG-29 auch Custom-Locations aus Overrides lädt (nicht nur Basis-LOCATIONS + standard Overrides).

---

### 🟠 P1 — Nächster Sprint: Mobile Viewport in Playwright-Tests

**Problem:** iOS-PWA-Bugs (BUG-19, BUG-25, BUG-34) gehen durch CI unbemerkt.

**Maßnahme:** Die bestehenden Playwright-Tests um einen Mobile-Viewport-Pass erweitern (iPhone 14 Dimensionen, `deviceScaleFactor: 3`, `isMobile: true`). Mindest-Checks:
- Close-Button sichtbar und klickbar
- Sheet bleibt innerhalb Viewport-Breite
- Edit-Overlay übersteigt nicht `window.innerWidth`

Das ist kein vollständiger Ersatz für echte Gerätetests, fängt aber die häufigsten Layout-Klassen ab.

---

### 🟡 P2 — Mittelfristig: Done-Gate als automatisierte Checkliste

**Problem:** Done wird zu früh gesetzt (vor Release-Bundle, trotz Pending-AKs).

**Maßnahme:** In den `fotoalert-test`-Skill eine explizite „Pre-Done-Checkliste" einbauen, die der Agent durchgehen und als ✅/❌ ausgeben muss, bevor er Done setzen darf:

```
[ ] git log --oneline -3 geprüft: keine Geschwister-Tickets im Bundle ausstehend
[ ] AK-Block gescannt: kein "ausstehend", "nach Rebuild", "[~]" mehr
[ ] Deploy verifiziert: git log auf Prod = lokaler Commit-Hash
[ ] Live-Health nach Deploy: status = ok, locations_count ≥ 15
```

---

### 🟡 P2 — Mittelfristig: US-38 Observability vorgezogen

**Problem:** Cron-Fehler und leere Caches werden nur durch User-Meldungen entdeckt.

**Maßnahme:** US-38 in Ready for Analysis verschieben. Minimalausbau:
- Täglicher Health-Check-Cron: Feed-Größe, Kalender-Größe → bei Unterschreitung einer Schwelle E-Mail an `stephanschumann@me.com`
- Server-Log-Rotation: verhindert dass Fehler in alten Logs begraben werden

---

### 🟡 P2 — Mittelfristig: `deviceId`-Drift dokumentieren und einschränken

**Problem:** `fa_device_id` liegt in localStorage und wird nach 7 Tagen iOS-Inaktivität gelöscht. Neue UUID → altes Server-Profil nicht mehr auffindbar.

**Maßnahme:** Solange US-75 (Login) nicht implementiert ist: In der App einen Hinweis anzeigen wenn serverseitig persistierte Daten (Kamera-Setup, Ratings) vorhanden sind aber die `deviceId` neu erzeugt wurde. Mindestens: in der UI anzeigen ob ein Server-Profil vorhanden ist und wann es zuletzt synchronisiert wurde.

---

### 🟢 P3 — Langfristig: Systemisches Data-Flow-Dokument

**Problem:** Daten-Synchronisationsschuld entsteht, weil unklar ist welche Komponente welche Datenquelle liest (Server In-Memory vs. SQLite-Overrides vs. Cache-Files vs. Frontend `Locations.all`).

**Maßnahme:** Ein kurzes Data-Flow-Diagramm in `/docs/` anlegen, das zeigt:
- Welche Komponente welche Daten liest
- Welche PATCH-Operationen welche Caches invalidieren
- Welche Felder einen Recompute auslösen

Ziel: neuer Agent (oder neuer Entwickler) sieht sofort, dass `precompute.py` und `main.py:_load_location_overrides` unterschiedliche Datenquellen haben.

---

## 7. Zusammenfassung: Die drei wichtigsten Strukturprobleme

**1. Daten-Synchronisationsschuld** — mehrere Komponenten lesen dieselben Daten aus unterschiedlichen Quellen, ohne dass das explizit dokumentiert oder automatisch getestet wird. Jede neue Feature-Implementierung produziert potenzielle Lücken.

**2. Annahmen-getriebene Specs** — Pre-Mortems und Implementierungsoptionen werden auf Basis von Annahmen über den Code geschrieben, nicht auf Basis von gelesesenem Code. Wenn die Annahme falsch ist, ist die Spec falsch — und der Fehler taucht erst beim Live-Test auf.

**3. Manuelle Tests für die kritischsten Pfade** — iOS-Layout, Kalender-Korrektheit nach Cron, Cache-Konsistenz nach PATCH sind alle manuell. Genau diese Klassen produzieren die wiederkehrenden Bugs.

---

*Analyse erstellt auf Basis von: BACKLOG.md (34 Bugs, Pre-Mortems, Root-Cause-Dokumentationen), TESTPLAN.md, 38 Memory/Feedback-Dateien, 2026-06-23*
