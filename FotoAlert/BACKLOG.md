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
| **🔬 In Analysis** | Pre-Mortem + Spec laufen | US-38 *(…wartet am Weg-Gate)* |
| **✅ Ready for Dev** | Spec freigegeben, wartet auf Implementierung | *(leer)* |
| **🔄 In Progress** | wird gerade implementiert | *(leer)* |
| **🧪 In Test** | implementiert, wartet auf (Test-)Bestätigung | **BUG-50** |
| **🏁 Done** | abgeschlossen + deployed | **BUG-52** *(GPS-Dialog nur einmal pro Session, released 2026-06-29)* · **BUG-53** *(Pin-Emoji nicht mehr in Location-Namen, released 2026-06-29)* · **BUG-51** *(Entfernungsfilter Locations-Tab, released 2026-06-29)* · **US-107** *(Sonnen-Alignment, released 2026-06-29)* · **US-106** *(v1.19.5 released 2026-06-28)* · **BUG-47** · **BUG-46** · **TASK-45** · **TASK-47** · **TASK-48** *(Epic Datensync, v2.0.x released 2026-06-28)* · **BUG-34** *(iOS-Zoom Fix, released 2026-06-28)* |
| **🔁 Retro / Lernen** | auto nach Done: Erkenntnisse → Memory/Tests, Skill-Vorschläge zur Freigabe | *(transient — läuft automatisch)* |
| **🚫 Excluded** | explizit ausgeschlossen — nie aufnehmen | *(leer)* |
| **📥 Inbox** | offene Tickets, **nicht** freigegeben | US-72 · US-84, US-85, US-87, BUG-21, TASK-37, TASK-38, TASK-39, TASK-41, TASK-42 · US-94 · **BUG-43** · **TASK-49** · **US-104** · **BUG-48** · **BUG-49** · **+ alle übrigen offenen Tickets unten** |

**So benutzt du das Board:**
1. **Freigeben:** Ticket-ID von `Inbox` nach `Ready for Analysis` verschieben → Agenten dürfen starten.
2. **Ausschließen:** ID unter `🚫 Excluded` eintragen → bleibt unangetastet.
3. **Release-Gate:** Steht ein Ticket in `In Test` und ist ein Deploy nötig, wartet die Pipeline auf dein „release".

---

## 🐛 BugFixes

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

### US-72 · Wetterkarte `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | User Story |
| **Priorität** | Mittel |
| **Status** | ToDo |
| **Erstellt** | 2026-06-19 |

**Beschreibung:** Als Fotograf möchte ich eine Wetterkarte für Berlin/Potsdam/Umland sehen, um Wolkendecke und Niederschlag für meine geplanten Shooting-Fenster visuell einschätzen zu können.

---

**Annahmen (autonomer Lauf, ohne Rückfrage getroffen):**
- A1: „Wetterkarte" = ein zuschaltbares **Overlay auf der bestehenden Leaflet-Karte** im Map-Tab (`MapView`), kein neuer Tab. Begründung: Beschreibung sagt „eine Wetterkarte … sehen", Map-Tab hat bereits Leaflet + Layer-Buttons (`web/index.html` Z. 767–774, `MapView` Z. 3034–3166).
- A2: Open-Meteo liefert **Punkt-Vorhersagen, keine Bild-Tiles**. Eine echte flächige „Wetterkarte" wird daher als **Grid aus Punkt-Forecasts** gerendert (farbcodierte Zellen/Kreise), nicht als externe Radar-Tile. Begründung: kein Lizenzrisiko (US-74), bleibt bei der bewährten Open-Meteo-Quelle, kein neuer Provider/Key.
- A3: Scope „Berlin/Potsdam/Umland" = festes Bounding-Box-Grid um den App-Default-Center [52.52, 13.40], Radius ~50 km. Auflösung Phase 1: grobes Raster (z. B. 6×6 = 36 Punkte) — Open-Meteo erlaubt Komma-getrennte Multi-Punkt-Abfrage in **einem** Request.
- A4: „geplante Shooting-Fenster" = ein **Zeit-Slider/Stundenwahl** (jetzt + nächste Stunden/Tage), der das Overlay auf die gewählte Stunde umschaltet. Phase 1: stündliche Schritte bis T+3 Tage (deckt sich mit bestehendem Wetter-Overlay-Horizont).
- A5: Zwei umschaltbare Layer: **Wolkendecke (%)** und **Niederschlag (mm bzw. Wahrscheinlichkeit %)** — getrennt, nicht überlagert (Lesbarkeit).

**Example Mapping:**

📏 **Rule 1 — Das Overlay zeigt flächige Wetterinformation für die gewählte Stunde.**
Kontext: Der Fotograf will *visuell* einschätzen, wo es aufreißt. Eine Zahl pro Location reicht nicht; er braucht das räumliche Muster (Westen klar, Osten zu).
- 🟢 Positiv: Given Map-Tab offen + Wetter-Layer „Wolken" aktiv, When Stunde = heute 19:00, Then erscheint über Berlin/Potsdam ein Raster farbiger Zellen (0 % = klar/transparent-blau → 100 % = grau/deckend), und ein nördlich klares Feld ist sichtbar heller als ein südlich bedecktes.
- 🔴 Negativ: Given Wetter-Layer aus, When Map-Tab offen, Then keine Wetterzellen sichtbar, die normale Karte (Marker, Tiles) ist unverändert und nicht eingefärbt.
- ⚠️ Edge: Given Open-Meteo liefert für einen Grid-Punkt `null`/Fehler, When Overlay rendert, Then diese Zelle wird ausgelassen (nicht als „0 % klar" fehlgefärbt) und der Rest rendert weiter.

📏 **Rule 2 — Wolkendecke und Niederschlag sind getrennt wählbar.**
Kontext: Wolken und Regen beantworten verschiedene Fragen (Licht vs. Nass-werden). Übereinander wären beide unlesbar.
- 🟢 Positiv: Given Wolken-Layer aktiv, When Nutzer tippt „Niederschlag", Then verschwindet die Wolken-Einfärbung und die Niederschlags-Einfärbung (mm-Skala blau) erscheint; nur ein Wetter-Layer gleichzeitig.
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

❓ Questions (autonom entschieden, da kein Rückfrage-Modus): alle über A1–A5 + Pre-Mortem-Gegenmaßnahmen aufgelöst. Offen für Weg-Gate: gewünschte Grid-Auflösung (36 vs. feiner) und ob Niederschlag als mm oder als Wahrscheinlichkeit (%) primär.

**Scope:**
- Eingeschlossen: zuschaltbares Wetter-Overlay im Map-Tab (`MapView`), zwei Wetter-Layer (Wolkendecke %, Niederschlag), Zeit-Slider bis T+3, Grid-Forecast via Open-Meteo Multi-Punkt, Backend-Endpoint mit Cache + Legende + Lade-/Fehlerzustand.
- Ausgeschlossen: animierte Radar-Loop, externe Radar-Tile-Provider (Lizenzrisiko, US-74), Push-Benachrichtigung bei Wetteränderung, iOS-App (`ios/`), Auflösung > T+3 Tage, Überlagerung beider Wetter-Layer gleichzeitig.

**Akzeptanzkriterien:**
- [ ] Neuer Endpoint `GET /weather-map?hours=72` liefert JSON `{ "grid": [{"lat","lon"}...], "hourly_times": [...iso UTC...], "cloud_cover": [[pro-Punkt-pro-Stunde]], "precipitation": [[...]], "fetched_at": iso }` für das Berlin/Potsdam-Grid; Statuscode 200; `len(grid) == 36` (6×6); jede Wertereihe gleich lang wie `hourly_times`.
- [ ] Edge: Wenn ein einzelner Grid-Punkt von Open-Meteo fehlt/`null` liefert, enthält die Antwort für diesen Punkt `null`-Werte (kein 500, kein 0-Wert) und die übrigen Punkte sind vollständig.
- [ ] Endpoint cached das Ergebnis im Prozess (TTL 60 min); zweiter Aufruf innerhalb TTL macht **keinen** neuen Open-Meteo-Call (verifizierbar via `fetched_at` unverändert).
- [ ] Frontend: Im Map-Tab existiert ein Wetter-Toggle mit zwei Optionen „Wolken" / „Niederschlag" + „aus" (Default aus); aktivieren zeichnet ein farbcodiertes Grid-Overlay über die Leaflet-Karte.
- [ ] Frontend: Ein Zeit-Slider/Selector schaltet die angezeigte Stunde um (Schritt = 1 h, Bereich jetzt…T+3); Label zeigt Berliner Ortszeit; Stundenwechsel löst **keinen** neuen Backend-Call aus (rein clientseitiges Re-Render aus geladenem Datensatz).
- [ ] Nur ein Wetter-Layer gleichzeitig sichtbar; Wechsel der Karten-Basis (Standard/Satellit/Nacht via `MapView.setLayer`) lässt das aktive Wetter-Overlay erhalten und korrekt darüber liegen.
- [ ] Edge: Open-Meteo komplett nicht erreichbar → Frontend zeigt dezenten Hinweis („Wetterdaten nicht verfügbar"), Karte + Marker bleiben voll funktionsfähig (keine JS-Exception, Map-Tab nutzbar).
- [ ] Legende sichtbar (Skala Wolken 0–100 %, bzw. Niederschlag mm); Werte-Farbzuordnung dokumentiert.

**Pre-Mortem:**
- 💀 Open-Meteo Rate-Limit/Block durch Slider-Spam (pro Tick ein Call) → Karte hängt, 429. Auslöser: kein Cache, Fetch an Slider gekoppelt. Frühwarnung: Lag beim Schieben, 429 im Log. → Gegenmaßnahme: **ein** Multi-Punkt-Request für den ganzen Horizont + Prozess-Cache (AK 3 + AK 5) — Slider rendert nur clientseitig.
- 💀 Overlay-Z-Index kollidiert mit Filter/Leaflet-Panes → Overlay verdeckt Marker oder liegt unter den Tiles. Auslöser: bekannter Leaflet-Stacking-Context (siehe CSS-Kommentar Z. 200, BUG-24). Frühwarnung: Marker unklickbar / Overlay unsichtbar. → Gegenmaßnahme: Overlay als eigenes Leaflet-Pane mit definiertem `zIndex` zwischen Tile- und Marker-Pane; nicht via globalem CSS-Filter. Manueller Test „Basis-Wechsel + Marker klickbar".
- 💀 Falsche Stunde angezeigt (UTC/Ortszeit-Verwechslung) → Fotograf plant nach falschem Wetter. Auslöser: Open-Meteo liefert UTC (`timezone=UTC` in `weather.py`), App zeigt Berlin (+2/+1). Frühwarnung: Overlay-Label weicht von Event-Detail-Zeit ab. → Gegenmaßnahme: intern durchgängig UTC, nur im Label konvertieren (Memory `shoot_time_utc`); AK 5 prüft Label-Konsistenz.
- 💀 Grid zu grob → „Wetterkarte" wirkt wie 4 Klötze, kein Mehrwert; oder zu fein → langsamer/größerer Request. Auslöser: willkürliche Auflösung. Frühwarnung: visuell blockig oder Request > paar Sek. → Gegenmaßnahme: Start 6×6=36 (ein Request bleibt schlank), Auflösung als eine Konstante kapseln, Weg-Gate-Frage.
- 💀 Map-Tab lädt das Overlay automatisch und kostet jedem Nutzer Open-Meteo-Calls/Latenz, auch wenn er es nie braucht. Auslöser: Eager-Load in `MapView.init()`. → Gegenmaßnahme: Overlay **lazy** — Default „aus", Fetch erst beim ersten Aktivieren (AK 4).

**Analyse & Planung:**
- [x] Example Mapping durchgeführt
- [x] Pre-Mortem durchgeführt
- [x] Architektur analysiert: Backend `backend/calculations/weather.py` (`fetch_weather_forecast`, `HourlyWeather` — liefert `cloud_cover_pct`/`precipitation_mm`/`precipitation_prob_pct`; Open-Meteo Punkt-API, kein Tile-Dienst) + `backend/main.py` (`_weather_overlay` Z. 343–420 als Vorbild für Aggregation/Logging, `/weather-refresh` Z. 1031 als Endpoint-Pattern, `_CACHE_DIR`/Prozess-Cache-Globals Z. 94–98/218, `auth.require_host`-Dependency-Muster). Frontend `web/index.html`: `MapView` (Z. 3034–3166 — `init`/`setLayer`/`loadMarkers`/eigenes Pane), Map-Tab-HTML + Layer-Buttons (Z. 767–774), Leaflet-CSS/Stacking-Hinweise (Z. 200–204), Tab-Aktivierung `if (page === 'map') MapView.init()` (Z. 4084). Reines Add-on, keine bestehende Wetter-Score-Logik wird verändert.
- [ ] Implementierungsoptionen: A (Grid aus Open-Meteo-Punkten, eigener Render) / B (externe Radar-Tile-Layer) / C (nur Marker-basierte Wetter-Badges, kein Flächen-Overlay)
- [ ] Empfehlung: **Option A** — wartet auf Stephans Weg-Gate

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
- [ ] Open-Meteo Multi-Punkt-Request (Komma-getrennte `latitude`/`longitude`) liefert für 36 Punkte in einem Call die parallelen `cloud_cover`/`precipitation`-Arrays — vor dem Frontend-Bau mit echtem Aufruf gegen das Grid prüfen (Antwortgröße, Antwortzeit, null-Verhalten an Bbox-Rändern).
- [ ] Wertebereiche real prüfen: typische Wolkendecke 0–100, Niederschlag meist 0 — Farbskala an realen Sommer-Werten kalibrieren, nicht raten.

**Testplan:**
- [ ] Automatisiert (Harness, `backend/tests/`): Endpoint-Form von `/weather-map` (Grid-Länge 36, Reihenlängen == `hourly_times`); null-Handling bei fehlendem Grid-Punkt; Cache-Verhalten (zweiter Call → `fetched_at` unverändert / kein erneuter HTTP-Call, gemockt). Docstring mit `US-72`. Python 3.9-kompatibel (keine `X | Y`-Typen — `Optional[...]`/`List[...]` verwenden, wie in `weather.py`).
- [ ] Manuell (http://localhost:8000, Map-Tab): Overlay aktivieren → Grid erscheint; Wolken↔Niederschlag wechseln (nur eins sichtbar); Slider schieben → Stunde/Label ändert sich, kein Netzwerk-Call (DevTools-Network); Basis-Layer wechseln → Overlay bleibt, Marker klickbar (BUG-24-Stacking); Open-Meteo offline simulieren → Hinweis statt Crash.

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

### TASK-39 · Refactoring: Lange Funktion local() in index.html aufteilen `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | ToDo |
| **Erstellt** | 2026-06-24 |

**Beschreibung:** JS-Funktion `local()` in `web/index.html` (Z. 2633, ~265 Zeilen) überschreitet den 80-Zeilen-Threshold deutlich. In kleinere Hilfsfunktionen aufteilen (z.B. Rendering, Event-Handler, Datenaufbereitung).

**Quelle:** Automatisch erstellt durch fotoalert-refactor (TASK-29)

---

### TASK-49 · Refactoring: Lange JS-Funktionen aufteilen (web/index.html) `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | ToDo |
| **Erstellt** | 2026-06-27 |

**Beschreibung:** `refactor_check.py` meldet vier lange JS-Funktionen in `web/index.html`:
- `ic()` Z. 805 — ~365 Zeilen (Icon-Helper, eingebracht durch US-100)
- `handler()` Z. 1170 — ~114 Zeilen
- `verState()` Z. 2949 — ~196 Zeilen (neu gemeldet durch BUG-46, 2026-06-28)
- `sunAlignmentLabel()` Z. 4291 — ~1034 Zeilen (neu gemeldet durch BUG-53, 2026-06-29)

Aufteilen in kleinere Hilfsfunktionen oder Modul-Abschnitte. Kein inhaltlicher Umbau.

**Quelle:** Automatisch erstellt durch fotoalert-refactor (US-102, 2026-06-27); ergänzt durch BUG-46-Refactor (2026-06-28); ergänzt durch BUG-53-Refactor (2026-06-29); Zeilennummern aktualisiert durch BUG-52-Refactor (2026-06-29)

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

### TASK-42 · Refactoring: Lange JS-Funktionen aufteilen (web/index.html) `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | Task |
| **Priorität** | Niedrig |
| **Status** | ToDo |
| **Erstellt** | 2026-06-25 |

**Beschreibung:** Zwei JS-Funktionen in `web/index.html` überschreiten den Threshold erheblich:
- `local()` Z. 2674 — ~265 Zeilen
- `row()` Z. 3531 — ~1034 Zeilen

**Quelle:** Automatisch erstellt durch fotoalert-refactor (BUG-39, 2026-06-25)

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

### BUG-48 · /opportunities-API liefert nur Mond-Events — Goldene/Blaue Stunde fehlen komplett `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | ToDo |
| **Erstellt** | 2026-06-29 |

**Beschreibung:** Die `/opportunities`-API gibt 500 Events zurück, aber ausschließlich Mond-Events (Mondaufgang, Monduntergang, Milchstraße, Mond-Alignment). Goldene Stunde und Blaue Stunde erscheinen mit 0 Treffern — obwohl `opportunities.json` im Cache 910× Goldene Stunde Abend und 910× Blaue Stunde enthält.

**Root-Cause-Hypothese:** Die BUG-32-Sortierung priorisiert Nicht-Routine-Events (Mond, Milchstraße) vor Goldene/Blaue Stunde. Mit ~2298 Nicht-Routine-Events im 14-Tage-Cache füllen diese den `:500`-Cap vollständig — Routine-Events fallen heraus.

**Offene Prüffrage:** Gibt es überhaupt valide Goldene-Stunde- und Blaue-Stunde-Events im Cache mit `score ≥ 0.35`? Falls nicht, wäre das ein separates Datenproblem im Precompute (eigenes Ticket).

**Bezug:**
- Abhängig von / direkt verursacht durch die Sortierlogik aus BUG-32 (Sort-Key-Fix: Nicht-Routine-Events werden vorgezogen — verdrängt bei hohem Volumen Routine-Events)
- Grenzt an BUG-28 (Cap+Sort-Diagnose, `:500`-Cap-Verdrängung von seltenen Event-Typen) — gleiches strukturelle Problem, andere Manifestation
- Unabhängig von US-107 (Sonnen-Alignment-Planung, andere Feature-Dimension)

---

### BUG-49 · Doppeltes Suchfeld im Locations-Panel `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Niedrig |
| **Status** | ToDo |
| **Erstellt** | 2026-06-29 |

**Beschreibung:** Im Locations-Panel existieren zwei Sucheingaben gleichzeitig: ein statisch sichtbares „Suchen"-Feld und ein weiteres, das sich über das Suchlogo im Menü öffnet. Das ist redundant und verwirrend — es sollte nur einen einzigen konsistenten Sucheinstieg geben.

**Bezug:** Keine Dubletten gefunden.

---

### BUG-50 · HINWEISE-Feld überschreibt sich nach Quick Location Capture `[ ]`

| Feld | Wert |
|------|------|
| **Typ** | BugFix |
| **Priorität** | Hoch |
| **Status** | In Test |
| **Erstellt** | 2026-06-29 |

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

- [ ] AK-1: Stephan öffnet die Bearbeiten-Ansicht einer per Quick Capture angelegten Location, löscht den vorausgefüllten Hinweis-Text und speichert. Beim erneuten Öffnen der Location ist das Hinweisfeld leer — der ursprüngliche Text erscheint nicht erneut.
- [ ] AK-2: Stephan ersetzt den Hinweis-Text durch eigenen Text und speichert. Der eigene Text bleibt nach Server-Neustart dauerhaft erhalten.
- [ ] AK-3: `PATCH /locations/{custom_id} {"special_notes": "X"}` gibt `{"ok": true, "updated": {"special_notes": "X"}, ...}` zurück (HTTP 200) — `special_notes` erscheint in `updated`.
- [ ] AK-4: `PATCH /locations/{standard_id} {"special_notes": "X"}` gibt HTTP 200 zurück und persistiert den Wert via Override.
- [ ] AK-5 (Edge Case): Leerer String `""` als `special_notes` wird akzeptiert und korrekt persistiert (nicht abgelehnt oder durch Default ersetzt).
- [ ] AK-6 (Regression): Alle bisher erlaubten Felder (name, description, Koordinaten, focal_length_suggestions, observer_floor_height_m) funktionieren nach der Änderung unverändert.

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

