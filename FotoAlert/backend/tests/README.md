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

| Datei | Bereich | Läuft im Sandbox | Marker |
|-------|---------|------------------|--------|
| `test_api_regression.py` | API-Regressionssuite — Endpoint-Verhalten aus AKs (`data_dev`, TestClient) | ⏳ nur mit `--all` (FastAPI-Stack + App-Startup) | `api`, `regression` |
| `test_api_smoke.py` | Schneller Health-Check des FastAPI-Stacks | ⏳ nur mit `--all` (FastAPI-Stack + App-Startup) | `api`, `smoke` |
| `test_astronomy_regression.py` | Berechnungen (Mond/Sonne/Geometrie/Brennweite) | teils ✅ immer (5× `offline`), teils nur mit `--all` + Netzwerk-/Dateicache-Zugriff auf `de421.bsp` (4× `online`) | `regression` (modulweit) + 5× `offline`, 4× `online` |
| `test_bug-61.py` | BUG-61: `subject_name` fehlte im PATCH-Text-Feld-Whitelist | ⏳ nur mit `--all` | `api`, `regression` |
| `test_bug-78.py` | BUG-78: Koordinaten-Parsing Apple-Maps-Format (rein clientseitig) | ⏭️ immer übersprungen (Platzhalter, AKs manuell getestet) | `frontend`, `regression` |
| `test_bug-80.py` | BUG-80: Kopfzeilen-Höhe bleibt beim Infotext-Wechsel stabil | ⏭️ übersprungen ohne Playwright + laufenden Dev-Server | `frontend`, `regression` |
| `test_bug29_calendar_single_recompute.py` | BUG-29: Kalender-Snapshot nach Koordinaten-PATCH | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug43_partial_composition.py` | BUG-43: Kompositions-Analyse liefert Teilergebnis ohne Motivhöhe | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug47.py` | BUG-47: Rollen-Kodierung im Token + `/login`-Antwort | teils ✅ immer (offline-Klasse), teils nur mit `--all` (api-Klasse) | `offline`, `api`, `regression` |
| `test_bug63.py` | BUG-63: `preview_alignment()` setzt `WindowEphemeris`-Fenster-State per `try/finally` zurück (Pre-Mortem-Szenario 4, Referenz-Endpoint `GET /plan`); AK-5 Dedup pro Tag/Himmelskörper-Passage | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug66.py` | BUG-66: „Höhenwinkel Spitze" in `POST /preview-alignment` | ⏳ nur mit `--all` | `api`, `regression` |
| `test_bug67.py` | BUG-67: neue Location erscheint nicht direkt in Karte/Liste | ⏳ nur mit `--all` | `api`, `regression` |
| `test_bug77_weather_job_status.py` | BUG-77: Live-Wetterabruf-Fehlerzustand sichtbar statt stillem Log | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug79_ci_ephemeris_skip.py` | BUG-79: statische Checks (Kommentar-Wortlaut + AST-Marker-Konsistenz gegen `_get_eph()`-Aufrufpfade) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug83.py` | BUG-83: Wetter-API-Drosselung neu kalibriert (`WEATHER_API_MAX_CONCURRENT_REQUESTS`/`WEATHER_API_REQUEST_PACING_SECONDS`) + Retry mit steigender Wartezeit bei HTTP 429 in `_run_one_weather_fetch()`, einheitlich für weather/aerosol/sun_dir/antisolar_dir | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_bug_68.py` | BUG-68: `special_notes`/`subject_name` übersteht Neustart + precompute | ⏳ nur mit `--all` | `api`, `regression` |
| `test_ephemeris_engine.py` | TASK-25: On-Demand-Ephemeriden-Engine (de421, deterministisch) | ✅ immer (offline); 1 `slow`-Test optional per `-m "not slow"` ausschließbar | `offline`, `regression` (+1× `slow`) |
| `test_moon_phase_events.py` | US-91/92/93: Vollmond-/Neumond-/Supermond-Override-Logik | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_patch_cache_consistency.py` | TASK-34: Cache-Konsistenz nach `PATCH /locations/{id}` | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task-41_precompute_refactor.py` | TASK-41: Refactoring `_run_single_location_flow()` in 4 Helferfunktionen | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task-60_patch_location_refactor.py` | TASK-60: Aufrufreihenfolge nach `patch_location()`-Refactoring | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task-66.py` | TASK-66: Playwright-Wrapper für 3 neue Klick-Durchläufe (echter Dev-Server nötig) | ⏭️ übersprungen ohne Playwright + laufenden Dev-Server | `frontend`, `regression` |
| `test_task-83.py` | TASK-83: Login-Ticket als HttpOnly/Secure/SameSite=Lax-Cookie statt Browser-Speicher (Login, Endpunktschutz, Zwangs-Logout, `/logout`, CORS-Credentials) | ⏳ nur mit `--all` (FastAPI-Stack + App-Startup) | `api`, `regression` (+1× `smoke`) |
| `test_task43_qa_model.py` | TASK-43: QA-Datenmodell (Lock-Flags, QA-Tabellen, Geo-Hash) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task45_azimuth.py` | TASK-45: idealer Azimut automatisch aus Sichtlinie | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task46_descriptions.py` | TASK-46: automatische Standortbeschreibung via LLM (Mistral gemockt) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task47_focal.py` | TASK-47: Brennweiten-Empfehlung aus Motivhöhe + Entfernung | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task48_qa_cron.py` | TASK-48: QA-Lauf automatisieren (Change-Detection, Single-Flight) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task48_qa_ondemand.py` | TASK-48: Endpoint `POST /run-qa-pass` (On-Demand-Trigger, Verbesserung gemockt) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_task53_dev_sync.py` | TASK-53: Live-Nutzerdaten periodisch nach Dev spiegeln (subprocess gemockt) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task55_image_backup.py` | TASK-55: `location_images/` im Server-Backup mitsichern | ✅ immer (offline, deterministisch) | `offline`, `regression` |
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
| `test_task84.py` | TASK-84 (Nacharbeit): Vendor-Umstellung (Leaflet/astronomy-engine self-hosted unter `web/vendor/`) + CSP-Verschlankung (`deploy/Caddyfile`) statisch abgesichert | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task-85.py` | TASK-85: Harter Serverstart-Abbruch bei fehlendem/leerem `FOTOALERT_AUTH_SECRET`, kein Notwert-Fallback mehr | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_task86.py` | TASK-86: Häufigkeits-Bremse `/preview-alignment` (AK-1), Kalender-Cache-Normalisierung + Höchstgröße (AK-2/AK-3), Login-Lockout (AK-4/AK-5), Geräte-Token-Validierung + Bremse `/register-device` (AK-6/AK-7), Regression Zeitraum-Deckelung/CORS (AK-8/AK-9) | teils ✅ immer (offline-Klassen: `rate_limit.py`-Unit-Tests + Cache-Normalisierung), teils nur mit `--all` (api-Klassen: `/login`, `/preview-alignment`, `/register-device`) | `offline`, `api`, `regression` |
| `test_task_65_field_roundtrip.py` | TASK-65: generischer Feld-Rundreise-Test (Whitelist-Vollständigkeit aller Location-Felder) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us-129.py` | US-129: Datenvertrag `image_url` für Filter „Hat Beispielbild" | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us07.py` | US-07: Goldene Wolken & Himmelsröte Scoring (AKs) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us07_golden_cloud_score.py` | US-07: `calculate_golden_cloud_score()` Einzelszenarien | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us09_sightline.py` | US-09: Sichtachsen-Check / Hinderniserkennung (Raycast) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us105_section_order.py` | US-105: Sektionsreihenfolge im Chancen-Detail-Template (statischer Check gegen `web/index.html`) | ✅ immer (offline, deterministisch) | `offline`, `regression`, `frontend` |
| `test_us106.py` | US-106: neue/geänderte Location sofort komplett nutzbar (Wetter/Scout/Pending-Queue, gemockt) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us109.py` | US-109: Goldene Wolken & Himmelsröte als eigene Feed-Events | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us112_weather_map.py` | US-112: Wetter-Overlay aus DWD-ICON + MET-Norway-Modelldaten (GRIB-Fixture, PNG) | teils ✅ immer (13× `offline`), teils nur mit `--all` (3× `api`) | `regression` (modulweit) + 13× `offline`, 3× `api` |
| `test_us113.py` | US-113: Himmelsröte-Richtungsfilter (Azimut zum Sonnen-Gegenpunkt) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us120.py` | US-120: Beispielbild-Upload (Host, Kompression, EXIF-Ausrichtung) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us130.py` | US-130: Himmelsröte mit Aerosol-/Dunst-Signal (ODER-Verknüpfung) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us131.py` | US-131: Wolken-/Dunstabfrage entlang der Sichtachse statt Fotografen-Standort | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us66_login.py` | US-66: Pflicht-Login mit Rollen-Erkennung (Token, `/login`, Endpunktschutz); 1 Test zusätzlich `smoke` | teils ✅ immer (offline-Klasse), teils nur mit `--all` (api-Klassen) | `offline`, `api`, `regression` (+1× `smoke`) |
| `test_us67_composition.py` | US-67: Datengrundlage Himmelsposition (`composition_analysis`) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us79_moon_rise_set.py` | US-79: Mondaufgang/-untergang als eigene Event-Typen | ✅ immer (offline, deterministisch) | `offline`, `regression`, `frontend` |
| `test_us_125.py` | US-125: Beispielbild eigenständig löschen (Host) | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us_126.py` | US-126: Bildausschnitt (Crop-Fokuspunkt) selbst wählen | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us_128.py` | US-128: Bauwerkshöhe/-breite nachträglich per PATCH bearbeitbar | ⏳ nur mit `--all` | `api`, `regression` |
| `test_us_132.py` | US-132: „Rote Wolken" (RED_CLOUDS) in Sonnenrichtung, Blaue-Stunde-Fenster | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_us-133.py` | US-133: Kartenschwenk bei Koordinaten-Eingabe (Anlegen + Bearbeiten, rein clientseitig) | ⏭️ immer übersprungen (Platzhalter, AKs manuell getestet) | `frontend`, `regression` |

**Marker `smoke` (TASK-70, erweitert in TASK-71):** kleine, handverlesene Auswahl der
wichtigsten/schnellsten Tests (Health/Locations/Feed/Auth, ein Kernpfad pro Hauptfunktion) für
einen Sekunden-Schnellcheck vor der vollen Suite — Aufruf via `pytest -m smoke`. Getaggt sind
`test_health_ok` (`test_api_smoke.py`), `test_locations`/`test_feed_opportunities`
(`test_task67_backend_regression.py`) sowie `test_user_login` (`test_us66_login.py`) —
bewusst als Marker auf bestehenden Tests statt als neue, duplizierte Tests in
`test_api_smoke.py` (TASK-71, Option A).

**Marker-Pflicht:** Zusätzlich zur Ticket-ID im Docstring bekommt jeder neue Test mindestens
einen passenden Marker aus der Tabelle oben (`offline`/`network`/`api`/`regression`/`frontend`/
`slow`/`smoke`) — kein Test ohne Marker. Das hält die Suite selektiv ausführbar (z. B. schneller
Regressionslauf vs. vollständiger Netzwerk-/API-Lauf).

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
