# Fix-Vorschläge zu den Audit-Befunden vom 27.07.2026

*Grundlage: die von Stephan bearbeitete Fassung von `2026-07-27-qualitaets-audit-live-app.md` (7 bestätigte Befunde; der KRITISCH-Befund zu ungeschützten Admin-Funktionen wurde von Stephan aus dieser Runde herausgenommen — offen, ob bewusst oder zur separaten Behandlung). Ursachen wurden durch tatsächliches Lesen/Durchsuchen von `astronomy.py`, `sightline.py`, `opportunity.py`, `main.py` und `web/index.html` verifiziert, nicht vermutet. Wo eine Datei dafür nicht vorlag (`precompute.py`, `calculations/weather.py`, das Schema-Modul mit `LocationOut`/`LocationCategory`), ist das explizit vermerkt.*

---

## 1 — Kategorie-Mismatch im Bearbeitungsformular (KRITISCH)

**Ursache (verifiziert):** `web/index.html`, `LocationDetail.openEdit()`, Zeile 6316. Das Kategorie-Dropdown selektiert über `loc.category_key||'SKYLINE'`. Dieses Feld liefert die API nicht — laut `main.py` (`_loc_to_out()`, Zeile 2289) liefert sie nur `category` als fertigen Klartext-String. `loc.category_key` ist also immer `undefined`, der Fallback `'SKYLINE'` greift **immer**, unabhängig von der echten Kategorie. Liste, Suche und Detailansicht lesen konsequent `loc.category` (Zeilen 3140, 3264, 5187, 6769) — nur die Edit-Vorbelegung nicht.

Das ist schlimmer als ein reiner Anzeigefehler: `saveEdit()` (Zeile 6668) sendet den (falsch vorbelegten) Dropdown-Wert beim Speichern ans Backend. Klickt jemand "Speichern" ohne die Kategorie manuell zu korrigieren, wird die Location **serverseitig stillschweigend umkategorisiert**.

**Konkreter Fix:** Zeile 6316 auf ein tatsächlich vorhandenes Feld umstellen. Zwei Optionen:
- (a) Rückwärts vom gelieferten Label auf den Key mappen (die Label→Key-Tabelle existiert im Frontend bereits als Array).
- (b) Robuster: Backend ergänzt zusätzlich den Kategorie-Schlüssel im `LocationOut`-Schema (analog zu `loc.category.name`), damit das Frontend nicht über Label-Text raten muss. Labels können sich ändern, Keys nicht.

**Systemischer Fix:** Ein Test/Check "jedes Bearbeiten-Formular muss mit dem tatsächlich von der API gelieferten Wert vorbelegt sein" — z. B. ein Abgleich zwischen den in `openEdit()` gelesenen `loc.<feld>`-Zugriffen und den im `LocationOut`-Schema deklarierten Feldern. Geprüft: alle anderen Felder in `openEdit()` (Name, Beschreibung, Koordinaten, Motivhöhe, Etagenhöhe, Brennweiten, Schwierigkeit) matchen korrekt — `category_key` ist der einzige Treffer für dieses Fehlermuster im ganzen File, kein wiederkehrendes Problem.

---

## 2 — Englischer Platzhaltertext statt Statuszeile (KRITISCH)

**Ursache (verifiziert):** `web/index.html`, `Feed.render()`, Zeile 2168–2171. `data` ist bereits das Ergebnis von `Filter.apply(this.data)` — berücksichtigt also sowohl den Standard-Schwellenwert (`minScore: 70`) als auch einen aktiven Event-Typ-Filter. Wird die gefilterte "Heute"-Teilmenge dadurch leer, wird `best = null`, und die Kopfzeile fällt auf den Text `'Capture moments that matter.'` zurück — denselben String, der als statischer Lade-Platzhalter im initialen HTML-Grundgerüst steht (Zeile 1191) und offenbar nie durch einen echten deutschen Leerzustand-Text ersetzt wurde. Kein weiterer englischer String im gesamten ~8200-Zeilen-File — ein isolierter Einzelfall, kein Muster.

**Konkreter Fix:** Zeile 2171 auf einen deutschen, kontextsensitiven Text ändern, z. B. "Heute: keine Treffer für die aktiven Filter" (falls Filter aktiv) bzw. "Heute: keine besonderen Chancen" (falls nicht). Zu klären als Produktentscheidung: soll die Kopfzeile grundsätzlich die Gesamtzahl der Chancen heute zeigen (unabhängig vom Filter) oder die gefilterte Zahl?

**Systemischer Fix:** Ein einfacher Check in der Auslieferung (Grep auf gängige englische Füllwörter außerhalb von Kommentaren/Variablennamen), der englische Reststrings in der sonst durchgängig deutschen Oberfläche aufspürt. Zusätzlich: ein Testfall "Statuszeile bei aktivem Zusatzfilter und leerer Tagesmenge" hätte diesen Fall beim Bauen bereits gefangen.

---

## 3 — Mondphasen-Name passt nicht zum Beleuchtungsgrad (ERNSTHAFT)

**Ursache (verifiziert):** `backend/calculations/astronomy.py`, `_moon_phase_name()`, Zeilen 250–266. Die Bucket-Grenze für "Zunehmender Halbmond" (`fraction` 0.28–0.47) entspricht rechnerisch Beleuchtungswerten von ~59–99 % — nicht den ~50 %, die ein Halbmond per Definition hat. Der echte Halbmond (50 % Beleuchtung, `fraction=0.25`) liegt bereits im vorherigen Bucket "Erstes Viertel". Das Bucket 0.28–0.47 ist astronomisch der zunehmende Dreiviertelmond, wurde aber irreführend "Halbmond" genannt. Einzige Stelle im Backend, die Phasennamen vergibt — kein Duplikat in `opportunity.py` oder Frontend, die reichen den fertigen String nur durch.

**Konkreter Fix:** Bucket-Namen korrigieren, z. B.:
- `< 0.22` → "Zunehmende Sichel"
- `< 0.28` → "Erstes Viertel" (≈ Halbmond, ~50 %)
- `< 0.47` → "Zunehmender Dreiviertelmond" (statt "Halbmond")
- `< 0.53` → "Vollmond"
- `< 0.72` → "Abnehmender Dreiviertelmond"
- `< 0.78` → "Letztes Viertel"
- sonst → "Abnehmende Sichel"

**Systemischer Fix:** Ein Unit-Test, der `phase_name` gegen `illumination_pct` auf Plausibilität prüft (z. B. Assertion: "Halbmond" ⇒ Beleuchtung 40–60 %) für alle Bucket-Grenzen. Vorbild dafür existiert im selben Modul bereits: eine Plausibilitäts-Assertion für die Erde-Mond-Distanz (Zeile 214).

---

## 4 — Zwei Status-Konzepte teilen sich "Geprüft"/"Nicht geprüft" (ERNSTHAFT)

**Ursache (verifiziert):** Zwei unabhängige Backend-Konzepte werden im Frontend mit identischem Wortlaut gerendert:
- Vor-Ort-Verifikation: `Verify.getLast(o.location_id)` → Badge "Geprüft" (Zeile 1947–1948), Tooltip Zeile 7590–7597.
- Sichtachsen-Status: `sightline_status` aus `sightline.py`/`evaluate_sightline()`, gerendert über `SIGHTLINE_LABELS` (Zeile 1902–1907: `nicht_geprueft: 'Nicht geprüft'`), Tooltip Zeile 7599–7609.

Beide Badges stehen nebeneinander auf derselben Karte (Zeile 1964) und in der Detailansicht (Zeile 4572/4573). Laut Code-Kommentar (Zeile 1898–1901) wurde das Sichtachsen-Feature bewusst nach dem bestehenden `tag-verified`-Muster benannt, ohne die Begriffskollision zu erkennen.

**Konkreter Fix:** Nur das Sichtachsen-Label umbenennen, z. B. `nicht_geprueft: 'Daten fehlen'` statt `'Nicht geprüft'` (Anpassung in `SIGHTLINE_LABELS`, Zeile 1906) — der interne Statuscode `"nicht_geprueft"` bleibt unverändert.

**Systemischer Fix:** Ein kleines Glossar bereits vergebener Badge-Texte je Status-Domäne, gegen das neue UI-Labels vor dem Einbau geprüft werden — Konvention "ein Wort = ein Konzept".

---

## 5 — Fehlende Hervorhebung bei Alignment-Ereignissen (ERNSTHAFT)

**Ursache (verifiziert):** `sightlineTagHtml()` (Zeile 1920–1927) rendert alle vier Sichtachsen-Zustände strukturell gleich, nur die Farbe wechselt über `SIGHTLINE_COLORS` (Zeile 1908–1913) — `nicht_geprueft` bekommt ein neutrales Grau (`var(--muted)`). Es gibt keine Eskalationslogik, die berücksichtigt, wie zentral die Sichtachse für den jeweiligen Ereignistyp ist. `SIGHTLINE_RELEVANT_TYPES` (Zeile 1917–1919) entscheidet nur, *ob* das Badge angezeigt wird, nicht *wie prominent*.

**Konkreter Fix:** Für `nicht_geprueft` bei `SIGHTLINE_RELEVANT_TYPES`-Events (Sonnen-/Mond-Alignment) eine auffälligere Behandlung — Warnfarbe statt Grau, oder ein zusätzliches Warn-Icon (analog `verified-badge-issue`, Zeile 601).

**Systemischer Fix:** Fehlende/unsichere Daten grundsätzlich danach staffeln, wie zentral sie für die Kernaussage der jeweiligen Karte sind, statt sie einheitlich neutral zu behandeln — gilt auch für künftige "Daten nicht verfügbar"-Zustände (Wetter, Bauwerke).

---

## 6 — Wetter-Score und "Wolkenstimmung" widersprechen sich scheinbar (MODERAT)

**Ursache (teilweise verifiziert — `calculations/weather.py` lag nicht vor):** Zwei unabhängige Metriken auf derselben Karte:
- Wetter-Score (Zeile 4555–4565): aus `o.weather_score`, Herkunft `calculate_photo_weather_score()` in `calculations/weather.py` (nicht geprüft, vermutlich Regen/Wind/Sicht/Nebel gesamt).
- "Wolkenstimmung" (Zeile 4608–4614, `cloudMoodScoreFor()`, Zeile 2989–2996): richtungsabhängige Bewertung des Farbpotenzials der Wolken, unabhängig von der generellen Wetter-Tauglichkeit.

Beide stehen im selben Abschnitt (Zeile 4619) ohne dass die Karte selbst erklärt, dass es zwei unabhängige Kennzahlen sind — die Erklärung existiert nur im separaten Glossar-Popup.

**Konkreter Fix:** Kurzer erklärender Zusatz direkt auf der Karte (z. B. "Wetter bewertet Sicht/Regen/Wind – Wolkenstimmung nur das Farbpotenzial, unabhängig davon") oder stärkere visuelle Trennung.

**Systemischer Fix:** Bei jeder Kombination zweier fachlich unabhängiger, aber ähnlich präsentierter Scores (Prozent + Kategorie-Label) auf einer Karte einen Inline-Hinweis zur Pflicht machen statt nur einen Tooltip.

---

## 7 — Kompositions-Analyse fehlt bei Mond-Ereignissen + Meter-Angabe (MODERAT)

**Teilweise verifiziert, Rest offen — `precompute.py` lag dem Subagenten nicht vor, das ist bewusst so markiert statt geraten.**

**Bestätigt:** Die geometrischen Grunddaten für eine Kompositions-Analyse entstehen in `opportunity.py` im Block "4. PRÄZISES 3D-ALIGNMENT" (Zeilen 545–665) — symmetrisch für Sonne UND Mond (Zeile 553–556). Das Beispiel aus dem Audit ("Mondaufgang – Schloss Babelsberg") ist aber kein 3D-Alignment-Event, sondern läuft über den separaten Block "5b. MONDAUFGANG UND MONDUNTERGANG" (Zeilen 748–796). Dort wird `celestial_altitude` beim Erzeugen des `PhotoOpportunity`-Objekts gar nicht gesetzt (Default `None`) — diese Events können strukturell keine Kompositions-Analyse-Grundlage liefern. Es ist also nicht "Sonne vs. Mond", sondern "3D-Alignment-Event vs. reines Auf-/Untergangs-Event".

**Nicht abschließend klärbar:** Ob `precompute.py` (Funktion `_serialize`, importiert in `main.py` Zeile 2487) zusätzlich explizit filtert, oder ob der Effekt rein aus der fehlenden Geometrieberechnung resultiert. Muss vor der Umsetzung geprüft werden.

**Zur Meter-Angabe:** Im Frontend bereits fertig gebaut (`vertical_offset_m`/`lateral_offset_m` über `fmtM()`, Zeilen 4784–4820, sowie "Himmelsposition" via `axisPhrase()`, Zeilen 4888–4914). Sobald die Geometriedaten für Mondaufgang/-untergang ergänzt werden, sollte sie automatisch mit erscheinen — vermutlich kein zusätzlicher Frontend-Fix nötig.

**Konkreter Fix:** In `opportunity.py`, Block 5b, für `MOON_RISE`/`MOON_SET` `celestial_altitude` mitgeben (aus der dort bereits berechneten, aber verworfenen `moon_pos_mr.altitude`, Zeile 760) und bei vorhandener `subject_height_m` zusätzlich `calculate_subject_angular_profile()` aufrufen. Danach `precompute.py` prüfen, ob `_serialize`/`_passes_alignment_filter` diese Events dann auch tatsächlich mit `composition_analysis` versieht.

**Systemischer Fix:** Checkliste pro neuem Ereignistyp: welche optionalen Anzeige-Abschnitte (Kompositions-Analyse, Himmelsposition, Sichtachsen-Status) sind sinnvoll, und werden die dafür nötigen Rohdaten überhaupt berechnet? Die im Frontend bereits vorhandenen Exempt-Sets (`SIGHTLINE_RELEVANT_TYPES`, `EV_SKYPOS_EXEMPT`) zeigen, dass es ein Muster dafür gibt — es müsste nur konsequent für alle Event-Typen gepflegt werden.

---

## Übergreifende Muster

- **Befund 1 und 2 sind isolierte Einzelfälle** — kein wiederkehrendes Muster im übrigen Code (einziges `_key`-Feld bzw. einziger englischer String).
- **Befund 3 hat eine einzige zentrale Ursache** (`_moon_phase_name()`) — ein Fix behebt alle Anzeigeorte gleichzeitig.
- **Befund 4 und 5 hängen ursächlich zusammen** — beide sind Symptome derselben Sichtachsen-Badge-Logik und lassen sich in einer Überarbeitung gemeinsam beheben (neues Label + Eskalationsfarbe für den Alignment-Fall).
- **Befund 6 und 7 teilen ein Muster**: unabhängige Werte/Verfügbarkeiten auf derselben Karte ohne Karten-interne Erklärung, warum sie sich unterscheiden bzw. fehlen.
- **Für eine vollständige Diagnose fehlten:** `backend/precompute.py` (Befund 7), `backend/calculations/weather.py` (Befund 6), das Schema-Modul mit `LocationOut`/`LocationCategory` (Befund 1, zur endgültigen Bestätigung).

## Offene Rückfrage an Stephan

Der KRITISCH-Befund zu ungeschützten Admin-Funktionen (Backend-Server-URL wechseln, Locations ohne sichtbare Anmeldung löschen) wurde in der bearbeiteten Fassung entfernt und ist hier bewusst nicht mitbehandelt. War das eine bewusste Entscheidung, oder soll das separat aufgegriffen werden?
