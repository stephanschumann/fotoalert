# FotoAlert Test-Harness

Das automatisierte Test-Harness der Pipeline (siehe `FotoAlert/PIPELINE.md` §3.3, Roadmap-Schritt 3).
Es macht die **Test-Phase des Orchestrators** ausführbar: statt Stephan curl-Schritte zu geben,
laufen die Akzeptanzkriterien als `pytest`-Tests im Sandbox.

## Kernidee: Akzeptanzkriterien werden zu dauerhaften Tests

Jedes abgeschlossene Ticket hinterlässt seine Akzeptanzkriterien als ausführbare Tests.
Die Summe aller Tests ist die **Vollsystem-Regression**: eine neue Änderung wird nicht nur
gegen ihr eigenes Feature geprüft, sondern gegen die AKs *aller* bisherigen Tickets — so
fallen Seiteneffekte auf, bevor sie live gehen.

**Konvention:** Jeder Test nennt im Docstring die Ticket-ID, deren AK er absichert. Neue
Tickets ergänzen ihre Tests nach demselben Muster (Datei nach Bereich, z. B.
`test_astronomy_regression.py`, `test_api_smoke.py`).

## Schichten

**Stand (TASK-79, 2026-07-15):** vollständige Tabelle über alle 59 Testdateien in
`backend/tests/` (Weg-Gate-Entscheidung Option B). Die inhaltliche Richtigkeit jeder
einzelnen Zeile wurde gegen die tatsächlichen `@pytest.mark.*`-Dekoratoren der jeweiligen
Datei geprüft (kein Raten). Ein automatisierter Test (`test_task79_readme_marker_sync.py`)
sichert nur ab, dass jede `*.py`-Datei überhaupt als Zeile vorkommt — nicht, dass die
Marker-Angabe stimmt; das bleibt manuelle Sorgfaltspflicht bei künftigen Testdatei-Änderungen.

**Marker `requires_full_checkout` (TASK-96, 2026-08-10):** `offline` bedeutet nur
"deterministisch, ohne Netzwerk/externe Dienste" — das ist NICHT dasselbe wie
"läuft auch bei einem Teil-Checkout, der nur `backend/` enthält" (z. B. ein schmal
gestagter Cloud-Sandbox-Abzug oder ein CI-Job ohne vollständigen Checkout). Sieben als
`offline`/`frontend` markierte Testdateien lösen Pfade relativ zum Repo-Root außerhalb von
`backend/` auf (`web/`, `deploy/`, `tools/`, `docs/`) und brechen deshalb bei einem
Backend-only-Checkout, obwohl ihre Markierung etwas anderes suggeriert: `test_task84.py`,
`test_task89_caddy_log_permissions.py`, `test_us105_section_order.py`,
`test_us79_moon_rise_set.py` (verifiziert in der TASK-96-Analyse, 2026-08-09/10) sowie
`test_task53_dev_sync.py` und `test_task-66.py` (nachträglich per Verifikations-Review am
2026-08-10 gefunden — sys.path-Import aus Repo-Root-`tools/` bzw. Screenshot-Pfad unter
Repo-Root-`docs/`) sowie `test_us38.py` (BUG-107-CI-Nachtrag, 2026-08-23 gefunden — laedt
`tools/job_history.py` per Repo-Root-relativem Pfad). Diese sieben tragen deshalb zusätzlich den Marker
`requires_full_checkout` (Option B aus der TASK-96-Analyse — ein reiner Pfad-Fix wurde
bewusst verworfen, da er das eigentliche Problem, fehlende Sichtbarkeit der
Repo-Root-Abhängigkeit, nur verdeckt hätte). Ein automatisierter Test
(`test_task96_requires_full_checkout_marker.py`) sichert ab, dass jede Testdatei, die
per Heuristik einen Pfad außerhalb von `backend/` referenziert (Path-Join mit dem
Literal `"web"`, `"deploy"`, `"tools"` oder `"docs"`), auch tatsächlich diesen Marker trägt
— künftige, strukturell gleiche Fälle bleiben so nicht unbemerkt unmarkiert (analog zum
TASK-79-Muster, das die README-Tabellen-Vollständigkeit gegen alle Testdateien
absichert, hier aber für Marker-Konsistenz statt Tabellen-Vollständigkeit).

| Datei | Bereich | Läuft im Sandbox | Marker |
|-------|---------|------------------|--------|
| `test_api_regression.py` | API-Regressionssuite — Endpoint-Verhalten aus AKs (`data_dev`, TestClient) | ⏳ nur mit `--all` (FastAPI-Stack + App-Startup) | `api`, `regression` |
| `test_api_smoke.py` | Schneller Health-Check des FastAPI-Stacks | ⏳ nur mit `--all` (FastAPI-Stack + App-Startup) | `api`, `smoke` |
| `test_astronomy_regression.py` | Berechnungen (Mond/Sonne/Geometrie/Brennweite) | teils ✅ immer (5× `offline`), teils nur mit `--all` + Netzwerk-/Dateicache-Zugriff auf `de421.bsp` (4× `online`) | `regression` (modulweit) + 5× `offline`, 4× `online` |
| `test_bug-61.py` | BUG-61: `subject_name` fehlte im PATCH-Text-Feld-Whitelist | ⏳ nur mit `--all` | `api`, `regression` |
| `test_bug-78.py` | BUG-78: Koordinaten-Parsing Apple-Maps-Format (rein clientseitig) | ⏭️ immer übersprungen (Platzhalter, AKs manuell getestet) | `frontend`, `regression` |
| `test_bug-80.py` | BUG-80: Kopfzeilen-Höhe bleibt beim Infotext-Wechsel stabil | ⏭️ im Sandbox weiterhin übersprungen (kein Playwright/Dev-Server) — läuft jetzt real im test-frontend-Job (CI, BUG-100) | `frontend`, `regression` |
| `test_bug-84.py` | BUG-84: Kategorie/Schwierigkeitsgrad im Bearbeiten-Formular falsch vorbelegt bzw. beim Speichern wirkungslos (category_key + PATCH-Whitelist) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_bug-86.py` | BUG-86: Mondphasen-Bezeichnung passt nicht zum Beleuchtungsgrad (`_moon_phase_name()` Bucket-Namen korrigiert, „Halbmond“ nur noch bei ~50% statt 90-97%) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug29_calendar_single_recompute.py` | BUG-29: Kalender-Snapshot nach Koordinaten-PATCH | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug43_partial_composition.py` | BUG-43: Kompositions-Analyse liefert Teilergebnis ohne Motivhöhe | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug47.py` | BUG-47: Rollen-Kodierung im Token + `/login`-Antwort | teils ✅ immer (offline-Klasse), teils nur mit `--all` (api-Klasse) | `offline`, `api`, `regression` |
| `test_bug63.py` | BUG-63: `preview_alignment()` setzt `WindowEphemeris`-Fenster-State per `try/finally` zurück (Pre-Mortem-Szenario 4, Referenz-Endpoint `GET /plan`); AK-5 Dedup pro Tag/Himmelskörper-Passage | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug66.py` | BUG-66: „Höhenwinkel Spitze" in `POST /preview-alignment` | ⏳ nur mit `--all` | `api`, `regression` |
| `test_bug67.py` | BUG-67: neue Location erscheint nicht direkt in Karte/Liste | ⏳ nur mit `--all` | `api`, `regression` |
| `test_bug77_weather_job_status.py` | BUG-77: Live-Wetterabruf-Fehlerzustand sichtbar statt stillem Log | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug79_ci_ephemeris_skip.py` | BUG-79: statische Checks (Kommentar-Wortlaut + AST-Marker-Konsistenz gegen `_get_eph()`-Aufrufpfade) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug100_ci_playwright_gate.py` | BUG-100: statischer Wortlaut-/Struktur-Check gegen `.github/workflows/deploy.yml` — sichert ab, dass `test_bug_85.py`/`test_bug-80.py`/`test_task-66.py` real im `test-frontend`-Job laufen (nicht mehr lautlos übersprungen) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug83.py` | BUG-83: Wetter-API-Drosselung neu kalibriert (`WEATHER_API_MAX_CONCURRENT_REQUESTS`/`WEATHER_API_REQUEST_PACING_SECONDS`) + Retry mit steigender Wartezeit bei HTTP 429 in `_run_one_weather_fetch()`, einheitlich für weather/aerosol/sun_dir/antisolar_dir | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug-90.py` | BUG-90: Kompositions-Analyse (celestial_altitude + Alignment-Filter-Exempt-Set) fehlt bei Mondaufgang-/Monduntergang-Events | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug-93.py` | BUG-93: Kalender-Vollneuberechnung nach ALGORITHM_VERSION-Bump berechnete 0 Events statt vollständig neu — `_init_calendar_pass()` gibt das (ggf. bei Versions-Mismatch zurückgesetzte) `existing_meta` jetzt zusätzlich zurück, `compute_calendar_incremental()` verwendet diesen Wert statt seiner eigenen, nie aktualisierten Kopie | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug-94.py` | BUG-94: Kartentitel bei Wolkenstimmungs-Chancen ("Rote Wolken", "Goldene Wolken", "Himmelsröte") nennen jetzt das Motiv statt nur den Event-Typ, inkl. Fallback bei unbekannter location_id + automatischer Konsistenz-Wächter (Introspektion/AST) gegen künftige Titel-Regressionen in main.py und calculations/opportunity.py | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug-98.py` | BUG-98: Beobachter- und Motivkoordinaten bei mehreren Locations identisch — `SubjectAngularProfile.is_degenerate`-Schutz (Azimut/Alignment-Suche/`/preview-alignment`/`find_opportunities`) gegen den irrefuehrenden 0.0°-Nord-Wert bei identischen Koordinaten, plus Datenkorrektur (13 Kategorie-1-Panorama-Locations ohne Motiv, 2 Kategorie-3-Locations mit recherchiertem Beobachter-Standpunkt) | ✅ immer (offline, deterministisch) | `offline`, `regression`, teils `api` |
| `test_bug-99.py` | BUG-99: Gesamtzeit-Obergrenze (`WEATHER_OVERLAY_MAX_TOTAL_SECONDS`) um `_fetch_weather_and_aerosol()` gegen einen unbegrenzt wachsenden Wetter-Overlay-Lauf bei durchgehend nicht (rechtzeitig) antwortenden Locations (Timeout, kein Retry) — Teilergebnis bereits erfolgreicher Abrufe bleibt bei Abbruch erhalten; zusätzlich Regressionsschutz „`/refresh-calendar` triggert weiterhin keinen Wetter-Abruf" | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug-104.py` | BUG-104: Direktionale Wolkenwerte (`golden_cloud_score_sun_dir`/`_antisolar_dir`) blieben bei realistischer Location-Zahl dauerhaft null — `PROJECTED_POINT_CACHE_PRECISION` von 3 auf 2 Nachkommastellen vergröbert, damit die Projektionspunkt-Dedup in `_plan_weather_fetch_tasks()`/`_lookup_projected_forecasts()` wieder greift | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug-87.py` | BUG-87: Badge-Wortlaut „Geprüft"/„Nicht geprüft" kollidierte zwischen Host-Verifikation und Sichtachsen-Datenverfügbarkeit — `SIGHTLINE_LABELS.nicht_geprueft` zeigt jetzt „Daten fehlen" statt „Nicht geprüft", Host-Verifikations-Wortlaut unverändert — benötigt vollständigen Checkout (TASK-96) | ✅ immer (offline, deterministisch) — benötigt vollständigen Checkout (TASK-96) | `offline`, `regression`, `requires_full_checkout` |
| `test_bug95.py` | BUG-95: Einzelne Wolkenstimmungs-Karte (Berliner Dom – Lustgarten Spreeseite) zeigte trotz BUG-94-Fix weiterhin nur den Event-Typ statt das Motiv im Titel | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug107.py` | BUG-107: job_history.py zeigte Timeout/DataError-Häufungen aus test_us38.py-Testartefakten statt echter Job-Fehler — neue session-scoped autouse-Fixture in `conftest.py` leitet `main._store.insert_job_run` während der Testsitzung auf eine Wegwerf-DB um, geteilte `backend/data_dev/fotoalert.db` bleibt unberührt | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us38.py` | US-38: Observability & Self-Healing — job_runs-Tabelle (SQLite-Persistenz), Fehlerklassifizierer (observability.py), Alarm-Mail-Debounce, job_history.py-CLI (laedt tools/job_history.py per Repo-Root-relativem Pfad) | ✅ immer (offline, deterministisch) — benötigt vollständigen Checkout (TASK-96) | `offline`, `regression`, `requires_full_checkout` |
| `test_bug101.py` | BUG-101: Scout-Zugänglichkeitsprüfung erkannte nur Gebäude-Verdeckung, keine Bäume/Wald in der Sichtachse (Fund Schloss Pfaueninsel) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug102.py` | BUG-102: Motiv-Koordinaten `SUBJECTS` froren beim Serverstart ein — Scout-Chancen ignorierten nachträgliche Koordinatenkorrekturen (Fund Einsteinturm) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug103.py` | BUG-103: Scout-Zugänglichkeits-Cache prüfte beim Wiederverwenden gespeicherter Einträge nicht, ob sie zum aktuellen Programmstand passen (Fund US-135, Pfaueninsel) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug106.py` | BUG-106: Wetter-Overlay — kalter Cache nach Server-Neustart kollidiert mit dem 180s-Zeitbudget aus BUG-99, viele Events blieben ohne Wetterdaten | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug108.py` | BUG-108: "Rote Wolken"-Events projizieren das Wetter jetzt 100km entlang der Blickrichtung statt nur am Fotografen-Standort (`ch_red_clouds_dir`/`cl_red_clouds_dir`), inkl. Regressionsschutz für `WEATHER_OVERLAY_MAX_TOTAL_SECONDS`-Anhebung 180.0→1500.0 | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug109.py` | BUG-109: "Warum Rote Wolken?"-Erklärungstext auf der Event-Detail-Ansicht zeigt jetzt den Wolkenwert vom 100km-Projektionspunkt (`ch_red_clouds_dir`/`cl_red_clouds_dir`) statt vom Fotografen-Standort, reiner Source-Check auf `web/index.html` (kein Browser/Server nötig), benötigt vollständigen Checkout (`web/`-Ordner) | ✅ immer (offline, deterministisch) | `offline`, `regression`, `requires_full_checkout` |
| `test_bug110.py` | BUG-110: Jahreskalender zeigt für den aktuellen Monat keine Einträge — Architektur-Schwachstelle in `main._compute_month_all_locations()` (bedingungsloses Caching in `_ondemand_month_cache`, auch bei leerem Ergebnis durch geschluckte Exceptions); Astronomie-Berechnung komplett gefaked | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug21.py` | BUG-21: Brennweiten-Eingabe (`#edit-focal`) zeigt auf iOS keine Komma-Taste — `inputmode="numeric"` → `"decimal"` + Parser-Härtung (Komma UND Semikolon als Trennzeichen in `saveEdit()`), reiner Source-Check auf `web/index.html` (AK1/AK5) plus API-Regressionstest für Mehrfachwert-Persistenz inkl. Ausreißer (800mm) und leere Liste (AK2-4) | teils ✅ immer (3× `offline`, benötigt vollständigen Checkout), teils ⏳ nur mit `--all` (3× `api`) | `offline`, `api`, `regression`, `requires_full_checkout` |
| `test_bug92.py` | BUG-92: Kalender zeigte nicht denselben Terminbestand wie der Feed — Kalender-Mindestschwelle im Live-On-Demand-Pfad (`_compute_location_month`/`_compute_month_all_locations`/`get_calendar`) UND im Hintergrund-Batch-Pfad (`precompute._compute_calendar_for_location`) von 0.40 auf 0.35 angeglichen (Feed-Default); zusätzlich Regressionstest fürs Fallback-Vergleichsliteral `if min_score != 0.35:` bei explizit abweichendem min_score | teils ✅ immer (4× `offline`), teils nur mit `--all` (5× `api`) | `offline`, `api`, `regression` |
| `test_bug_68.py` | BUG-68: `special_notes`/`subject_name` übersteht Neustart + precompute | ⏳ nur mit `--all` | `api`, `regression` |
| `test_bug_85.py` | BUG-85: Kopfzeile (`#header-subtitle`) aktualisiert sich nicht, wenn der komplette 14-Tage-Feed durch aktive Filter auf 0 Treffer reduziert wird | ⏭️ im Sandbox weiterhin übersprungen (kein Playwright/Dev-Server) — läuft jetzt real im test-frontend-Job (CI, BUG-100) | `frontend`, `regression` |
| `test_ephemeris_engine.py` | TASK-25: On-Demand-Ephemeriden-Engine (de421, deterministisch) | ✅ immer (offline); 1 `slow`-Test optional per `-m "not slow"` ausschließbar | `offline`, `regression` (+1× `slow`) |
| `test_moon_phase_events.py` | US-91/92/93: Vollmond-/Neumond-/Supermond-Override-Logik | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_patch_cache_consistency.py` | TASK-34: Cache-Konsistenz nach `PATCH /locations/{id}` | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task02_eclipses.py` | TASK-02: Sonnen-/Mondfinsternisse (vier Typen, Berlin/BB-Region), gegen reale, extern verifizierbare Ereignisse geprüft (Skyfield-Kontaktsuche + `eclipselib.lunar_eclipses()`) | ⏳ nur mit `--all` (Datei-Cache-Zugriff auf `de421.bsp`, wie bei `test_astronomy_regression.py`) | `regression`, `online` |
| `test_task-41_precompute_refactor.py` | TASK-41: Refactoring `_run_single_location_flow()` in 4 Helferfunktionen | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task-60_patch_location_refactor.py` | TASK-60: Aufrufreihenfolge nach `patch_location()`-Refactoring | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task-66.py` | TASK-66: Playwright-Wrapper für 3 neue Klick-Durchläufe (echter Dev-Server nötig) | ⏭️ im Sandbox weiterhin übersprungen (kein Playwright/Dev-Server) — läuft jetzt real im test-frontend-Job (CI, BUG-100) — benötigt vollständigen Checkout (TASK-96) | `frontend`, `regression`, `requires_full_checkout` |
| `test_task-83.py` | TASK-83: Login-Ticket als HttpOnly/Secure/SameSite=Lax-Cookie statt Browser-Speicher (Login, Endpunktschutz, Zwangs-Logout, `/logout`, CORS-Credentials) | ⏳ nur mit `--all` (FastAPI-Stack + App-Startup) | `api`, `regression` (+1× `smoke`) |
| `test_task43_qa_model.py` | TASK-43: QA-Datenmodell (Lock-Flags, QA-Tabellen, Geo-Hash) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task45_azimuth.py` | TASK-45: idealer Azimut automatisch aus Sichtlinie | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task46_descriptions.py` | TASK-46: automatische Standortbeschreibung via LLM (Mistral gemockt) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task47_focal.py` | TASK-47: Brennweiten-Empfehlung aus Motivhöhe + Entfernung | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task48_qa_cron.py` | TASK-48: QA-Lauf automatisieren (Change-Detection, Single-Flight) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task48_qa_ondemand.py` | TASK-48: Endpoint `POST /run-qa-pass` (On-Demand-Trigger, Verbesserung gemockt) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task53_dev_sync.py` | TASK-53: Live-Nutzerdaten periodisch nach Dev spiegeln (subprocess gemockt) | ✅ immer (offline, deterministisch) — benötigt vollständigen Checkout (TASK-96) | `offline`, `regression`, `requires_full_checkout` |
| `test_task54_weather_map_disk_cache.py` | TASK-54: dauerhafter Festplatten-Cache für Wetterkarten-PNGs (`_persist_weather_map_cache()`/`_load_weather_map_cache_from_disk()`, Option A analog `_load_caches()`) — sofortige Anzeige nach Neustart, unveränderter Leerzustand ohne vorherigen Bau, unveränderte Hintergrund-Aktualisierung, robuster Fallback bei korrupter/fehlender Cache-Datei, konstanter Speicherbedarf, unveränderte Endpoint-Verträge | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task55_image_backup.py` | TASK-55: `location_images/` im Server-Backup mitsichern | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task59_own_overpass.py` | TASK-59: Optionaler eigener Overpass-Server (Code-Vorbereitung in `data/qa_azimuth.py`, komplett gemockt — der eigene Server existiert noch nicht) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task59_local_building_cache.py` | TASK-59 Option E: lokale Gebäudedaten-Cache-Nachschau in `data/qa_azimuth.py` vor dem Live-Mirror-Fallback (komplett gemockt) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task59_extract_building_data.py` | TASK-59 Option E: Extraktions-Skript `tools/extract_building_data.py` (Radius-Filter, Höhenschätzung, JSON-Struktur — osmium-unabhängig, komplett gemockt) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug112_extract_building_data.py` | BUG-112: `extract_buildings_for_locations()` in `tools/extract_building_data.py` crashte mit TypeError bei Locations ohne Motivkoordinaten (`subject_lat`/`subject_lon` = None, BUG-98 Kategorie 1) — `near_subject`-Vergleich rief `_haversine_m()` ungeprüft mit None auf; Inline-None-Guard + `Optional[float]`-Typkorrektur bei `KnownLocation` | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug113.py` | BUG-113: Standort anlegen — zweiter/weiterer Standort war langsamer als der erste, weil die Nacharbeit nach dem Speichern (Scout-Auswertung "Entdecken", Neuladen der Vorberechnungs-Ergebnisse) den Server für Sekunden einfror (Ticker-Messung des Event-Loop-Stillstands, Berechnen/Speichern parallel zum Scout-Lauf; Regression: Scout-Fehler folgenlos, Speichern stößt Neuberechnung + Scout weiterhin an) | ✅ immer (offline, deterministisch; ohne Netz/Subprozess) — seit der Umsetzung (2026-09-19, Weg B) alle 6 grün; davor waren 4 bewusst rot (test-first) | `offline`, `regression` |
| `test_bug113_kalender_austausch.py` | BUG-113 (Ergänzung zur Umsetzung): Korrektheit des Kalender-Austauschs je Standort — `main._apply_calendar_delta()` ersetzt genau die Ereignisse des geänderten Standorts, hält die Sortierung, lässt fremde Standorte unberührt und ignoriert fehlende/veraltete/fremde Übergabedateien; `precompute._write_calendar_single_delta()` schreibt nur die Ereignisse dieser Location (Pre-Mortem Szenario 2: Kalender veraltet/doppelt) | ✅ immer (offline, deterministisch; keine großen Dateien) | `offline`, `regression` |
| `test_bug113_nachbesserung.py` | BUG-113 Nachbesserung (gate-auditor 2026-09-19, Punkte 2/3/5): AK3 stark — Kalender-Austausch mit realistischer Übergabedatei (~5,7 MB, 1 750 Termine) und ~475 000 Terminen im Arbeitsspeicher, Inhalt korrekt (alte Termine ersetzt, fremde unverändert, keine Dubletten, Sortierung) UND Event-Loop-Stillstand ≤ 0,5 s (Ticker-Messung; ~370 MB calendar.json auf der Platte, damit ein Komplett-Neuladen auffällt); AK4 Nachrechnen stößt Feed-Neuladen + Austausch an (kein Voll-Ladeweg); AK5 5 Standorte hintereinander mit Nacharbeit + Scout im Hintergrund ohne Anstieg; AK6 Fehler einer Scout-Pipeline im Worker-Thread; leerer Kalender im Speicher → Vollneuladen statt nur ein Standort | ✅ immer (offline, deterministisch; ohne Netz/Subprozess; schreibt ~370 MB Testdatei in tmp_path, Laufzeit ~20 s) | `offline`, `regression` |
| `test_bug113_punkt6.py` | BUG-113 Nachbesserung Punkt 6: scheitert nur das Schreiben der Übergabedatei, meldet das Protokoll das ehrlich (Warnung statt „Kalenderberechnung fehlgeschlagen") und die Kalender-Erfolgszeile bleibt; echter Kalenderfehler wird weiter als Fehler gemeldet | ✅ immer (offline, deterministisch; ohne Netz/Subprozess, < 1 s) | `offline`, `regression` |
| `test_bug114.py` | BUG-114: Kalender-Abruf (Weg ohne Live-Berechnung) liest die Kalenderdatei nicht mehr bei jedem Aufruf komplett ein — Ticker-Messung des Event-Loop-Stillstands bei 200-MB-Kalenderdatei (≤ 0,5 s); „zuletzt berechnet“ stimmt nach Laden, Einzel-Nachberechnung und Volllauf; halb geschriebene Datei / Datei ohne Zeitpunkt führt nicht zu Serverfehler; Regression: Leerzustand, Filter, Live-Berechnung unverändert | ✅ immer (offline, deterministisch; ohne Netz/Subprozess; schreibt ~400 MB Testdateien in tmp_path) — test-first 2026-09-27: 3 bewusst rot (AK1, 2× AK5), 6 grün (Regressionsschutz) | `offline`, `regression` |
| `test_bug117.py` | BUG-117: Wetterabruf hält das Tageslimit des Wetterdienstes ein — Zwischenspeicher, Staffelung nach Terminnähe (36 Stunden / 12 Stunden), gröbere Punkte nur für Rote Wolken, Notbremse, nur ein Wetterlauf gleichzeitig, Scout-Verbrauch auf den Tagesstand gebucht (Wetterdienst durch Attrappen ersetzt, kein Netzwerk) |
| `test_bug117_menue.py` | BUG-117 AK-6 (Oberfläche, Browser-Test): Meldet der Server „Wetterlauf läuft bereits“, zeigt die Zeile im Aktualisieren-Menü genau diesen Satz statt „Gestartet…“ |
| `test_bug117_nachfunde.py` | BUG-117 Nachfunde (Prüfbericht 2026-10-18): (1) neu geladener Feed bekommt nach einer Notbremse des Wetterlaufs trotzdem sein Wetter (ein Nachlauf, nie zwei Läufe gleichzeitig); (2) Scout-Verbrauch wird genau einmal auf den Tagesstand gebucht; Attrappen, Wegwerf-Cache-Ordner | ✅ immer (offline, deterministisch; ohne Netz) — test-first 2026-10-18: beide bewusst rot | `offline`, `regression` |
| `test_bug118.py` | BUG-118: Gelöschte Orte (Standard-Orte und eigene Orte) kommen nicht zurück — Löschen räumt auch die Feed-Datei auf der Festplatte auf, Neustart und Einzel-Neuberechnung eines anderen Orts bringen sie nicht zurück, Einlesen sortiert Termine gelöschter Orte aus, Vorberechnung rechnet gelöschte Standard-Orte nicht mehr mit (nicht gelöschte weiterhin); eigene temporäre Datenbank/Feed-Datei je Test | ✅ immer (offline, deterministisch; ohne Netz) — test-first 2026-10-11: 7 bewusst rot (AK1–AK5a), 1 grün (Gegenfall AK5b) | `offline`, `regression` |
| `test_us141.py` | US-141: Schutz-Tests für die entschiedenen Teile, die vom Weg-Gate unabhängig sind — Qualitätsprüfung, Sichtachsen-Knopf, Höhen-/Sichtachsen-Schritt der Einzelberechnung laufen für jeden Ort der Liste; Wetterabruf hängt nur an den Terminen im Feed. Tests für Schalter/Regionen folgen nach dem Weg-Gate | ✅ immer (offline, deterministisch; ohne Netz) — test-first 2026-10-11: 6 grün (Regressionsschutz, bewusst keine roten) | `offline`, `regression` |
| `test_us141_baustein1.py` | US-141 Baustein 1 (Ergänzung zur Umsetzung): Speicher-Tabelle für den Zustand je Land/Region, Sammelschalter aus dem Gespeicherten, einmalige Übernahme (wiederholbar, überschreibt nichts, legt vorher eine Sicherung an), Dateisperre und atomares Schreiben, Aufräumen der Feed-Datei nach dem Löschen. Eigene temporäre Datenbank/Dateien. | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us141_abdeckung.py` | US-141 (Abdeckungs-Check): Schreib-Sicherheit der Vorberechnungs-Dateien — bricht das Schreiben von Feed oder Kalender mittendrin ab, bleibt die alte Datei ganz (3 Tests); zwei gleichzeitige Einmisch-Läufe verlieren keine Termine (1 Test). Test-first, vor der Umsetzung rot. Offline. |
| `test_us141_regel.py` | US-141 (Weg-Gate Option A): zentrale Regel ohne Oberfläche — Gebiet (Land und Region) aus Koordinaten nach Lage, nicht nach Namen (Sächsische Schweiz = Deutschland, Südtirol/Venetien = Italien, unklar = Sonstige, feste Liste von neun Ländern; Vereinigtes Königreich mit England, Nordirland, Schottland, Wales), Aktiv-Regel (gelöscht, Land aus, Region aus, fehlende Angabe = an), Ortsdaten- und Berechnungsliste, Startzustand neuer Orte. Offline. |
| `us141_adapter.py` | US-141: gemeinsame Hilfsdatei (keine Testdatei) für die Schalter-/Nachlade-/Neue-Orte-/Filter-/Betriebs-Tests — Testwelt mit Gastgeber- und Nutzer-Login, Prozess-Spion statt echter Unterprozesse, Vorschlags-Konstanten der Schnittstelle (`/areas`, `/areas/{land}`, `/areas/{land}/{region}`, PUT mit `{"enabled": bool}`). Ohne die Schnittstelle brechen abhängige Tests in der Vorbereitung mit „Schnittstelle fehlt" ab. | — | — |
| `test_us141_schalter.py` | US-141: Schalter-Schnittstelle — Gastgeber-Rechte, Land/Region setzen, Sammelschalter (an/aus/teilweise) wird abgeleitet. Test-first, vor der Umsetzung rot (Fehler in der Vorbereitung). Offline über Testclient. **Stand Baustein 2 (2026-10-15): 24/24 grün.** | ✅ immer (ohne Netz) | `api`, `regression` |
| `test_us141_nachladen.py` | US-141: direktes Nachladen beim Einschalten — eigener gedrosselter Lauf, ein Backup je Lauf, Wiederaufnahme nach Neustart; ergänzt `test_us141_abdeckung.py` (Dateisperre/atomares Schreiben). Test-first, vor der Umsetzung rot. **Stand Baustein 2: 9 rot / 4 grün — bewusst, gehört zu Baustein 3.** | ✅ immer (ohne Netz, Prozess-Spion) | `api`, `regression` |
| `test_us141_nachladen_betrieb.py` | US-141 Baustein 3 (eigene Ergänzung, 2026-10-15): gebündelter Rechenlauf `precompute --location-ids` (nur genannte aktive Orte, höchstens ein Backup je Lauf, Fortschrittsdatei), Nachtlauf überschreibt nachgeladene Orte nicht, gespeicherter Nachlade-Zustand überlebt Neustart, Fortschritt und Restzeit in `/areas` und in der Antwort auf das Schalten, Fehler wird gemeldet, Ausschalten beendet den Rechenprozess. 7 Tests, Prozess-Spion, offline. | ✅ immer (ohne Netz) | `api`, `regression` |
| `test_us141_kalender_nachladen.py` | US-141 (Entscheidung 2026-10-15, Kalender beim Einschalten): `precompute --location-ids … --mit-kalender` rechnet den Kalender nur für die Orte des Gebiets und mischt ihn in EINEM atomaren Schreibvorgang in `calendar.json` ein (andere Orte und Algorithmus-Stand unverändert, ein Backup je Lauf), fehlende/kaputte Datei, zu wenig Platz und Schreibfehler lassen die Datei unversehrt, Kollision unter der Dateisperre, ausgeschaltete Orte werden nicht eingemischt; Server: Wetter läuft während des Kalender-Schritts, Fortschritt nennt den Kalender, Übernahme ohne Neueinlesen der großen Datei, Fehler machen Chancen/Wetter nicht ungültig, Ausschalten beendet den Prozess, nach Neustart nur noch `--nur-kalender`. 26 Tests, gestubbte Rechnung und Prozess-Spion, offline (ein Test rechnet 3 Tage echte Astronomie). | ✅ immer (ohne Netz) | `api`, `regression` |
| `test_us141_kalender_live.py` | US-141 (Entscheidung 2026-10-17, Kalender im Live-Modus überspringen): bei `FOTOALERT_ONDEMAND=1` startet das Nachladen den Rechenprozess ohne `--mit-kalender`, merkt keinen offenen Kalender, zeigt im Menü keinen Kalender-Schritt, lässt `calendar.json` und den Kalender im Arbeitsspeicher unverändert (auch ein liegengebliebenes Postfach wird nicht übernommen); nach einem Neustart startet ein alter gemerkter Kalender keinen Nachholauf (wird verworfen), offene Chancen werden ohne Kalender fortgesetzt; Ausschalten beendet den Prozess; ohne Live-Modus (nicht gesetzt, `0`, leer) unverändert mit Kalender-Schritt und Nachholen. |
| `test_us141_refactor.py` | US-141/BUG-118 Refactor-Check (2026-10-15): sichert die beim Aufräumen zusammengeführten Stellen ab, die vorher keinen eigenen Test hatten — die drei Merklisten im Speicher (offene Entscheidung, Nachladen, Kalender-Nachladen) sind unabhängig, Einmischen eines Orts in die Feed-Datei (inkl. Warnung bei unlesbarer Datei), Austausch der Kalendertermine eines Orts im Arbeitsspeicher, Lesen der Nachlade-Fortschrittsdatei. 7 Tests, offline. | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us141_refactor_m1m2.py` | US-141 Refactor-Check, Befunde M1 und M2 (2026-10-15): M1 — scheitert die Überwachung des Nachlade-Rechenprozesses mit einem Fehler, wird der Prozess sicher beendet (terminate, dann kill) bevor der Arbeiter weitermacht, der Lauf zählt als fehlgeschlagen, nie zwei Prozesse gleichzeitig; M2 — beim Einschalten eines Gebiets wird die Feed-Datei nicht im Haupt-Thread der Ereignisschleife gelesen. 12 Tests, offline. | ✅ immer (offline, deterministisch) | `api`, `regression` |
| `test_us141_neue_orte.py` | US-141: Startzustand und Hinweis beim Anlegen neuer Orte in pausierten Gebieten; Entdecken/Scout für pausierte Orte. Test-first, vor der Umsetzung rot. **Stand Baustein 2: 7/7 grün.** | ✅ immer (ohne Netz) | `api`, `regression` |
| `test_us141_filter_ergebnisse.py` | US-141: Filterwirkung — Zähler, Ortsliste, Karte, Kalender, Heute-/Tagesübersicht, 500er-Deckel; bereits berechnete Chancen pausierter Orte verschwinden. Test-first, vor der Umsetzung rot. **Stand Baustein 2: 14/14 grün.** | ✅ immer (ohne Netz) | `api`, `regression` |
| `test_us141_zuordnung.py` | US-141 Phase A (2026-10-14): Zuordnung Koordinaten → Land/Region und Regionslisten (Deutschland 16, Niederlande 12, Italien 20, Frankreich 13/18, Österreich 9, Schweiz 26, Norwegen 15, UK 4; Sortierung mit Umlauten; Grenzfall Glienicker Brücke = unsicher). Nutzt den Schnittstellenentwurf `data/regionen.py`. 50 rot + 1 grün (Schutztest `is_england`); mit Wegwerf-Referenzmodul 51/51 grün. | ✅ immer (offline) | `offline`, `regression` |
| `test_us141_kontingent.py` | US-141 Phase A: Wetter-Kontingent — pausierte Orte kosten keine Wetter-Anfragen im Wetterlauf, Zählzeile im Protokoll, Scout/Entdecken überspringt pausierte Orte. 5 rot (eigener Grund) + 2 grüne Schutztests + 3 Vorbereitungsfehler (Schnittstelle fehlt). Kein Netz (Attrappe). **Stand Baustein 2: 5 rot / 5 grün — der Rest gehört zu Baustein 3.** | ✅ immer (ohne Netz) | `api`, `regression` |
| `test_us141_betrieb.py` | US-141 Phase A: Betrieb — Gesundheitsmeldung aktiv/gesamt, Koordinaten-Änderung eines pausierten Ortes, Wieder-Einschalten, schnelles Hin-und-Her-Schalten. 5 Vorbereitungsfehler (Schnittstelle fehlt), Rumpf unbewiesen. **Stand Baustein 2: 3 grün, 2 rot (schnelles Hin-und-Her-Schalten braucht den Nachlade-Lauf aus Baustein 3).** | ✅ immer (ohne Netz) | `api`, `regression` |
| `test_us141_browser.py` | US-141 Phase A: Playwright-Gerüst für den nicht wegklickbaren Hinweis beim Anlegen eines Ortes und die Oberflächen-Wirkung der Filter. Wird ohne `playwright` und ohne `FOTOALERT_E2E_URL` übersprungen (5 skipped); Alternative: manuelle Anleitung im Ticket. **Stand 2026-10-15 (Stephan hat die Änderung dieser einen Datei erlaubt, Protokoll `outputs/2026-10-15_US-141-testkorrektur/`): 6 Tests (vorher 5), gegen die echte Oberfläche alle 6 grün. Korrigiert: Einführungsfenster wird vorab als gesehen markiert; ‚Alle Gebiete pausiert‘ wird nur noch erwartet, wenn wirklich alle Gebiete aus sind (bei nur Berlin und Brandenburg aus: Meldung erscheint nicht, übrige Orte laufen weiter); der Filter-Chip wird gezielt im Filter-Fenster angetippt; jeder Test stellt den Ausgangszustand her und räumt auf.** | ⏭ nur mit Browser und Test-URL | `frontend` |
| `test_us141_frankreich.py` | US-141 (Entscheidung 2026-10-15, NEU): Frankreich mit Übersee — genau 18 Regionen (13 Festland mit Korsika + Französisch-Guayana, Guadeloupe, La Réunion, Martinique, Mayotte), Zuordnung aus der Lage (Fort-de-France, Saint-Denis La Réunion, Cayenne, Pointe-à-Pitre, Mamoudzou, Paris, Ajaccio, Metz), Name zählt nie, Grenzdatei und Regionsliste passen zusammen (120), Menü führt alle 18. Offline, ohne Server. | ✅ immer (ohne Netz) | `offline`, `regression` |
| `test_us141_oberflaeche.py` | US-141 Baustein 2 (NEU): Oberflächen-Tests im echten Browser — Host-Menü ‚Länder & Regionen‘ (Sammelschalter an/aus/teilweise, Ortszahlen), pausierte Orte in Liste und Karte, Zähler ‚davon n pausiert‘, Feed ohne Chancen pausierter Orte, ‚Alle Gebiete pausiert‘, nicht wegklickbarer Hinweis (Host), ‚Host muss freischalten‘ (Nutzer), kein Menü für Nutzer. 5 Tests; ohne `playwright`/`FOTOALERT_E2E_URL` übersprungen. | ⏭ nur mit Browser und Test-URL | `frontend` |
| `test_task61_backup_coverage.py` | TASK-61: Backup auf alle 8 DB-Tabellen erweitert | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task67_auth_regression.py` | TASK-67 Etappe 1: PRODUCT.md „Pflicht-Regression Auth" | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task67_backend_regression.py` | TASK-67 Etappe 1: PRODUCT.md „Pflicht-Regression Backend" (Health/Locations/Feed/Kalender/Scout); 2 Tests zusätzlich `smoke` | ⏳ nur mit `--all` | `api`, `regression` (+2× `smoke`) |
| `test_task67_detail_regression.py` | TASK-67 Etappe 2: PRODUCT.md „Pflicht-Regression Detail" (Astronomie-Sektion) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task67_feed_regression.py` | TASK-67 Etappe 2: PRODUCT.md „Pflicht-Regression Feed" (Filter/Dedup) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task67_orte_regression.py` | TASK-67 Etappe 2: PRODUCT.md „Pflicht-Regression Orte" (≥15 Karten) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task67_ratings_regression.py` | TASK-67 Etappe 3: Bewertungsfunktion (Anlegen/Abrufen/Löschen) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task67_zusatzfunktionen_regression.py` | TASK-67 Etappe 3: Basistests der 5 Zusatzfunktionen (Tagesübersicht, Empfehlungsplan, Adress-Umkehrsuche u.a.) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task77_qa_cleanup_on_delete.py` | TASK-77: QA-Zeilen werden bei Location-Löschung mitentfernt | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task78_qa_transactional.py` | TASK-78: QA-Teilerfolg konsistent behandeln (Option B) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task79_readme_marker_sync.py` | TASK-79: diese README-Tabelle gegen die BUG-79-Testrealität + Vollständigkeit gegen alle Testdateien absichern | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task96_requires_full_checkout_marker.py` | TASK-96: Konsistenz zwischen Repo-Root-Pfadaufloesung und Marker `requires_full_checkout` gegen alle Testdateien absichern (analog TASK-79-Muster) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task97_ci_env_dev_guard.py` | TASK-97 (AK4): Regressionsguard, dass `FOTOALERT_ENV: dev` im `test-frontend`-Job von `.github/workflows/deploy.yml` erhalten bleibt (verhindert stillen Rückfall in den TASK-83-Cookie/Secure-Flag-Fehler aus CI-Run #277) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task106.py` | TASK-106: manueller Sichtachsen-Check lädt nur noch den kleinen Feed im Nebenstrang neu und liest die große Kalenderdatei nicht mehr ein — Kalender im Speicher bleibt unverändert, Server bleibt während des Neuladens ansprechbar (Ticker-Messung), Fehlerpfad und Regression der übrigen Neulade-Wege | ✅ immer (offline, deterministisch; ohne Netz/Subprozess) | `offline`, `regression` |
| `test_task106_gebaeude.py` | TASK-106 Nachbesserung: die Gebäudeabfrage des Sichtachsen-Checks läuft im Nebenstrang — Server bleibt bei 1,5 s künstlicher Wartezeit ansprechbar (Ticker-Messung ≤ 0,5 s), Abfrage läuft in einem anderen Thread, Ergebnis („frei“ / „nicht geprüft“ bei Fehler oder None) und Speichern im Store unverändert | ✅ immer (offline, deterministisch; ohne Netz/Subprozess) | `offline`, `regression` |
| `test_task-94.py` | TASK-94: `_load_custom_locations()` in main.py nutzt jetzt `coerce_category_value()` (statt direktem `LocationCategory[...]`-Zugriff) UND ist pro Eintrag try/except-abgesichert (Referenzimplementierung: `precompute.py:_load_custom_locations()`, BUG-33) — ein einzelner beschädigter Kategoriewert/Eintrag bricht das Laden der übrigen Custom-Locations beim Serverstart nicht mehr ab | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task-102.py` | TASK-102: Sicherheits-Härtungen Teil 1 — (a) `_run_precompute()`/`_run_sightline_refresh()` legen bei internem Fehler keinen rohen Exception-Text mehr in `_job_status` ab (GET /job-status ist unauthentifiziert), voller Text bleibt per `logger.error()` im Server-Log; (c) `upload_location_image()` prüft die Upload-Größe jetzt per Streaming-Read in Chunks statt erst nach vollständigem Einlesen | teils ✅ immer (2× `offline`), teils nur mit `--all` (3× `api`) | `offline`, `api`, `regression` |
| `test_task-103.py` | TASK-103: Bearbeiten gespeicherter Orte auf Host beschränken (`PATCH /locations/{id}` von `auth.require_auth` auf `auth.require_host` umgestellt, Anlegen über `POST /preview-alignment` bleibt für User unverändert möglich) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task-105.py` | TASK-105: Analyse-Ampel Rot (Python-3.9-EOL blockiert 4 von 7 TASK-104-Paketen) — haelt 3 Konsistenz-Regressionstests fest, die beim spaeteren Python-Sprung im selben Zug gruen werden muessen: `pandas`-Obergrenze in requirements.txt, identischer `python-version`-Pin in beiden GitHub-Workflows, aktualisierte CLAUDE.md-Regel; bewusst aktuell rot (Migration noch nicht umgesetzt) | 🔴 aktuell rot (Migration aussteht) — benoetigt vollstaendigen Checkout (TASK-96) | `offline`, `regression`, `requires_full_checkout` |
| `test_task84.py` | TASK-84 (Nacharbeit): Vendor-Umstellung (Leaflet/astronomy-engine self-hosted unter `web/vendor/`) + CSP-Verschlankung (`deploy/Caddyfile`) statisch abgesichert | ✅ immer (offline, deterministisch) — benötigt vollständigen Checkout (TASK-96) | `offline`, `regression`, `requires_full_checkout` |
| `test_task-85.py` | TASK-85: Harter Serverstart-Abbruch bei fehlendem/leerem `FOTOALERT_AUTH_SECRET`, kein Notwert-Fallback mehr | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task86.py` | TASK-86: Häufigkeits-Bremse `/preview-alignment` (AK-1), Kalender-Cache-Normalisierung + Höchstgröße (AK-2/AK-3), Login-Lockout (AK-4/AK-5), Geräte-Token-Validierung + Bremse `/register-device` (AK-6/AK-7), Regression Zeitraum-Deckelung/CORS (AK-8/AK-9) | teils ✅ immer (offline-Klassen: `rate_limit.py`-Unit-Tests + Cache-Normalisierung), teils nur mit `--all` (api-Klassen: `/login`, `/preview-alignment`, `/register-device`) | `offline`, `api`, `regression` |
| `test_task89_caddy_log_permissions.py` | TASK-89: Caddy-Logdatei-Berechtigung bei Server-Neuaufbau (Text-/Grep-Check gegen `deploy/setup_server.sh`, kein echter Server-Neuaufbau) | ✅ immer (offline, deterministisch) — benötigt vollständigen Checkout (TASK-96) | `offline`, `regression`, `requires_full_checkout` |
| `test_task_65_field_roundtrip.py` | TASK-65: generischer Feld-Rundreise-Test (Whitelist-Vollständigkeit aller Location-Felder) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us-129.py` | US-129: Datenvertrag `image_url` für Filter „Hat Beispielbild" | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us07.py` | US-07: Goldene Wolken & Himmelsröte Scoring (AKs) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us07_golden_cloud_score.py` | US-07: `calculate_golden_cloud_score()` Einzelszenarien | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us09_sightline.py` | US-09: Sichtachsen-Check / Hinderniserkennung (Raycast) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us105_section_order.py` | US-105: Sektionsreihenfolge im Chancen-Detail-Template (statischer Check gegen `web/index.html`) | ✅ immer (offline, deterministisch) — benötigt vollständigen Checkout (TASK-96) | `offline`, `regression`, `frontend`, `requires_full_checkout` |
| `test_us106.py` | US-106: neue/geänderte Location sofort komplett nutzbar (Wetter/Scout/Pending-Queue, gemockt) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us109.py` | US-109: Goldene Wolken & Himmelsröte als eigene Feed-Events | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us112_weather_map.py` | US-112: Wetter-Overlay aus DWD-ICON + MET-Norway-Modelldaten (GRIB-Fixture, PNG) | teils ✅ immer (13× `offline`), teils nur mit `--all` (3× `api`) | `regression` (modulweit) + 13× `offline`, 3× `api` |
| `test_us113.py` | US-113: Himmelsröte-Richtungsfilter (Azimut zum Sonnen-Gegenpunkt) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us120.py` | US-120: Beispielbild-Upload (Host, Kompression, EXIF-Ausrichtung) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us130.py` | US-130: Himmelsröte mit Aerosol-/Dunst-Signal (ODER-Verknüpfung) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us131.py` | US-131: Wolken-/Dunstabfrage entlang der Sichtachse statt Fotografen-Standort | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us135.py` | US-135: Scout — nur zugängliche Standorte mit freier Sicht vorschlagen (Sichtachsen-Blockade durch Gebäude, Wald-/Wasser-/Bahn-Ausschluss inkl. Weg-Nähe-Ausnahme, Overpass-Cache, geteilter Rate-Limit-Tracker, Threadpool-Entkopplung) | ✅ immer (offline, deterministisch, Overpass-HTTP-Client gemockt) | `offline`, `regression` |
| `test_us137.py` | US-137: Standort-Detail „Nächste Events" zeigt das nächste Sonnen-Alignment auch über 30 Tage hinaus — `GET /plan` gehärtet (Tages-Obergrenze `min(days,365)` analog BUG-63, Häufigkeits-Bremse `_plan_limiter` 20/60s analog `/preview-alignment`, AK11) | ✅ immer (offline, deterministisch, `elevation_difference_m` explizit → kein Netzwerkcall) | `offline`, `regression` |
| `test_us138_england.py` | US-138 Schritt 1: Wetterkarte deckt England (London) ab — Kartengrenzen, Stützpunkte westlich von 0°, Bildpunkt London, Ausfall der England-Quelle, Werte an Berlin/München/Oslo ±2 Prozentpunkte, Ersatz-Grenzen in web/index.html, Wetterplanung London-Ort | ✅ immer (offline, deterministisch; Gitter-Tests überspringen ohne eccodes/Pillow) | `regression`, `offline` (je Test), `requires_full_checkout` (T5) |
| `test_us138_ortszeit.py` | US-138 Schritt 2: Ortszeit für England-Orte (Londoner Zeit + Zusatz „London"), Berliner Zeit für alle anderen Orte, Tageszuordnung nach Datum am Ort, Zeitspanne mit einem Zusatz, Regel „England-Ort" (JS = Python), Beschreibungstexte vom Server; die App-Zeitfunktionen aus web/index.html laufen unter Node.js (Test wird ohne Node übersprungen) | ✅ immer (offline, deterministisch; Node.js-Tests überspringen ohne Node) | `offline`, `regression`, `requires_full_checkout` |
| `test_us138_entdecken.py` | US-138 Schritt 3: Entdecken-Tab (Scout) für London — Lichtfenster der Sonnen- und Mond-Pipeline je Bezugspunkt (England-Motive: eigener Ort, alle anderen unverändert Berlin), Berliner/norwegische Motive unverändert, Lichtfenster je Bezugspunkt und Tag nur einmal berechnet | ✅ immer (offline, deterministisch; überspringt ohne skyfield) | `offline`, `regression` |
| `test_us138_feeddeckel.py` | US-138 AK18: Feed-Deckel 500 behält Chancen von England-Orten zuerst (auch bei vielen stärkeren Berliner Chancen), Gesamtzahl höchstens 500, ohne England-Orte identisch zum bisherigen Ergebnis, Ausgabe weiter nach Zeit sortiert, übrige Chancen in bisheriger Round-Robin-Reihenfolge | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us66_login.py` | US-66: Pflicht-Login mit Rollen-Erkennung (Token, `/login`, Endpunktschutz); 1 Test zusätzlich `smoke` | teils ✅ immer (offline-Klasse), teils nur mit `--all` (api-Klassen) | `offline`, `api`, `regression` (+1× `smoke`) |
| `test_us67_composition.py` | US-67: Datengrundlage Himmelsposition (`composition_analysis`) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us79_moon_rise_set.py` | US-79: Mondaufgang/-untergang als eigene Event-Typen | ✅ immer (offline, deterministisch) — benötigt vollständigen Checkout (TASK-96) | `offline`, `regression`, `frontend`, `requires_full_checkout` |
| `test_us_125.py` | US-125: Beispielbild eigenständig löschen (Host) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us_126.py` | US-126: Bildausschnitt (Crop-Fokuspunkt) selbst wählen | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us_128.py` | US-128: Bauwerkshöhe/-breite nachträglich per PATCH bearbeitbar | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us_132.py` | US-132: „Rote Wolken" (RED_CLOUDS) in Sonnenrichtung, Blaue-Stunde-Fenster | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us-133.py` | US-133: Kartenschwenk bei Koordinaten-Eingabe (Anlegen + Bearbeiten, rein clientseitig) | ⏭️ immer übersprungen (Platzhalter, AKs manuell getestet) | `frontend`, `regression` |
| `test_us-134.py` | US-134: Bestätigen-Button neben Koordinaten-Eingabefeldern (zweiter Auslöseweg fuer Kartenschwenk, rein clientseitig) | ⏭️ immer übersprungen (Platzhalter, AKs manuell zu testen) | `frontend`, `regression` |

**Marker `smoke` (TASK-70, erweitert in TASK-71):** kleine, handverlesene Auswahl der
wichtigsten/schnellsten Tests (Health/Locations/Feed/Auth, ein Kernpfad pro Hauptfunktion) für
einen Sekunden-Schnellcheck vor der vollen Suite — Aufruf via `pytest -m smoke`. Getaggt sind
`test_health_ok` (`test_api_smoke.py`), `test_locations`/`test_feed_opportunities`
(`test_task67_backend_regression.py`) sowie `test_user_login` (`test_us66_login.py`) —
bewusst als Marker auf bestehenden Tests statt als neue, duplizierte Tests in
`test_api_smoke.py` (TASK-71, Option A).

**Marker-Pflicht:** Zusätzlich zur Ticket-ID im Docstring bekommt jeder neue Test mindestens
einen passenden Marker aus der Tabelle oben (`offline`/`network`/`api`/`regression`/`frontend`/
`slow`/`smoke`/`requires_full_checkout`) — kein Test ohne Marker. Das hält die Suite selektiv
ausführbar (z. B. schneller Regressionslauf vs. vollständiger Netzwerk-/API-Lauf). Zusätzlich
gilt seit TASK-96: jeder `offline`-Test, der Pfade außerhalb von `backend/` auflöst (`web/`,
`deploy/`), bekommt zusätzlich `requires_full_checkout` — sonst schlägt
`test_task96_requires_full_checkout_marker.py` fehl.

## Sicherheit: niemals Prod-Daten

`conftest.py` setzt `FOTOALERT_ENV=dev` **vor** allen Importen → der Store nutzt
`backend/data_dev/` (TASK-19). Tests fassen die Prod-DB nie an.

## Ausführen

```bash
# einmalig: Abhängigkeiten installieren
bash tests/bootstrap_sandbox.sh

# Standard: schnelle, netzunabhängige Offline-Regression
bash tests/run_tests.sh

# inkl. API-/Netzwerk-Tests
bash tests/run_tests.sh --all
```

## Rolle im Orchestrator

Die Test-Phase (`fotoalert-orchestrator`, Schritt 1) ruft `tests/run_tests.sh` in einem
isolierten Subagenten auf und gibt nur den **kompakten Report** (pass/fail je Test) zurück —
nicht die Testausgabe in den Orchestrator-Kontext. Bei rot: Ticket bleibt in `In Test`,
der Fehler geht an die Implementierungs-Phase zurück.

## Wie ein neues Ticket Tests beisteuert

1. In der Analyse-Phase werden die AKs messbar formuliert (`fotoalert-analyze`).
2. In der Impl-Phase wird pro AK, das automatisierbar ist, ein Test ergänzt — mit Ticket-ID
   im Docstring.
3. Der Test bleibt dauerhaft Teil der Regression. So wächst die Abdeckung mit jedem Ticket.


## US-141 Phase A — Annahmen der neuen Tests (2026-10-14)

- Python 3.9 kompatibel; Red-Beweis lief in einem Wegwerf-Venv mit Python 3.10.12 (pytest 9.0.3, fastapi 0.111.0), nicht gegen die große `calendar.json`.
- A1: `data/regionen.py` liefert pro Koordinate Land und Region (Tupel, Wörterbuch oder Objekt) und eine Liste `REGIONEN` als {Land: [Regionen]}. Das ist ein Vorschlag aus dem Schnittstellenentwurf im Ticket, keine bestehende Schnittstelle.
- A2: `data/aktiv_regel.py` bleibt wie in `test_us141_regel.py` vorgeschlagen.
- A3: Die Schalter-Pfade sind die Vorschlags-Konstanten in `us141_adapter.py`; bei anderer Umsetzung nur dort ändern.
- A4: Deutsche Regionsnamen sind Claudes Schreibvorschlag (z. B. „Nordholland"), keine Quellenangabe.
- K1: Die Wetter-Zählzeile erkennt man im Protokoll an einer INFO-Zeile mit „Anfrage" und „%".
- K2: Zähler zählen Anfragen über eine Attrappe von `fetch_weather_forecast`/`fetch_aerosol_forecast`; es geht nie eine echte Anfrage raus.
- K3: Scout wird über `moon_pipeline.run(1)` / `sun_pipeline.run(1)` mit gesichertem `SUBJECTS` geprüft.
- B1/B2: Tests auf Basis der Testwelt mit Schalter (`welt_z`) sind erst nach Umbau des Orte-Änderns um Land/Region lauffähig; bis dahin brechen sie in der Vorbereitung ab (richtiger Grund, Rumpf unbewiesen).
- Vorschlag zum Umbau von 8 Fällen in `test_us141_regel.py`: siehe `_vorschlag_us141_regel_umbau.md` (nur Stephan darf bestehende Tests ändern).

## US-141 Baustein 2 — Stand und bekannte Abweichungen der Tests (2026-10-15)

- Ziel-Dateien von Baustein 2 sind grün: `test_us141_schalter.py` (24), `test_us141_neue_orte.py` (7), `test_us141_filter_ergebnisse.py` (14); `test_us141_betrieb.py` 3 von 5 (die beiden roten Fälle ‚schnelles Umschalten‘ erwarten einen Rechenprozess nach dem Einschalten = Baustein 3).
- `test_us141_nachladen.py` (9 rot) und `test_us141_kontingent.py` (5 rot) bleiben bis Baustein 3 rot.
- `test_us141_browser.py`: **am 2026-10-15 mit Stephans ausdrücklicher Erlaubnis korrigiert** (siehe Tabellenzeile oben; alle 6 Fälle grün). Der Befund unten ist der Stand VOR der Korrektur. Gegen die fertige Oberfläche scheitern 3 Fälle an Annahmen des Tests selbst: (a) beim ersten Start deckt das Einführungsfenster die Oberfläche ab (andere Browser-Tests rufen dafür `_dismiss_onboarding_if_present` auf); (b) ‚Alle Gebiete pausiert‘ wird nach dem Ausschalten von nur Berlin und Brandenburg erwartet, die Entwicklungsdaten enthalten aber auch Orte in anderen Ländern; (c) der zweite Tipp auf ‚Goldene Stunde‘ trifft eine Feed-Karte statt des Filterchips. Mit vorab geschlossenem Einführungsfenster und allen Ländern aus waren 4 von 5 grün, wenn der Zustand frisch war (nur Fall (c) rot, auch mit der alten Oberfläche); (d) der erste Fall hinterlässt einen unentschiedenen Ort, dessen Hinweis dem Host beim nächsten Öffnen absichtlich nicht wegklickbar angezeigt wird und dann den Filterknopf der Karten-Fälle verdeckt. Vorschlag an Stephan: Test anpassen — nur er darf ihn ändern.
- Lauf der Browser-Tests: Chromium über Playwright 1.56.0, Server mit `FOTOALERT_ENV=dev` auf einer Wegwerf-Kopie der Entwicklungsdaten, nie Produktion.

