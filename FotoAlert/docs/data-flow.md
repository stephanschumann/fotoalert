# FotoAlert – Data-Flow-Dokument

> Welche Komponente liest welche Datenquelle, was invalidiert welchen Cache, was löst Recompute aus.  
> Angelegt: 2026-06-23 (TASK-36) · Hintergrund: BUG-29 Root-Cause (precompute ignorierte SQLite-Overrides)

---

## Datenquellen im System

| Quelle | Inhalt | Wer schreibt | Wer liest |
|--------|--------|-------------|-----------|
| `data/locations.py` | Basis-Locations (hartcodiert) | Entwickler (manuell) | `precompute.py` (beim Start), `main.py` (beim Start) |
| `data_dev/` / `data_prod/` | SQLite-DB (`fotoalert.db`) + Cache-JSONs | `main.py` via `data/store.py` | `main.py`, Frontend via API |
| SQLite `location_overrides` | User-Änderungen via PATCH (Koordinaten, Name, …) | `main.py:PATCH /locations/{id}` | `main.py:_load_location_overrides()` |
| `opportunities.json` | Feed-Cache (14-Tage-Ephemeriden-Ergebnis) | `precompute.py`, `main.py:_run_precompute()` | Frontend via `GET /opportunities` |
| `calendar.json` | Jahreskalender-Cache | `precompute.py`, `main.py:_run_precompute()` | Frontend via `GET /calendar` |
| `discover.json` | Scout-Tab-Cache | `precompute.py` | Frontend via `GET /scout` |

---

## Wer liest was — Komponentenübersicht

### `main.py` (FastAPI-Server)

```
Start:
  1. Lädt data/locations.py → LOCATIONS (Basis)
  2. Ruft _load_location_overrides() → merged SQLite location_overrides in LOCATIONS
  3. LOCATIONS + Overrides = In-Memory-Zustand des Servers

GET /locations:
  → liefert In-Memory-LOCATIONS (inkl. Overrides ✅)

PATCH /locations/{id}:
  → schreibt in SQLite location_overrides
  → ruft _load_location_overrides() → aktualisiert In-Memory-LOCATIONS
  → triggers _run_precompute(location_ids=[id]) bei recompute-relevanten Feldern

GET /opportunities:
  → liest opportunities.json aus Cache

GET /calendar:
  → liest calendar.json aus Cache
```

### `precompute.py` (eigenständiger Subprocess)

```
Beim Start / bei Aufruf durch main.py:
  1. Lädt data/locations.py → LOCATIONS (Basis)  ⚠️ KEINE SQLite-Overrides bis BUG-29-Fix
  2. Seit BUG-29-Fix: lädt zusätzlich SQLite location_overrides → merged in LOCATIONS
  3. Berechnet Ephemeriden → schreibt opportunities.json, calendar.json, discover.json

⚠️ WICHTIG: precompute.py ist ein SEPARATER PROZESS.
  Er teilt NICHT den In-Memory-Zustand von main.py.
  Jede Änderung der Datenquellen muss in beiden Komponenten ankommen.
```

### Frontend (`web/index.html`)

```
App-Start:
  → lädt NICHT Locations.all (lazy — erst beim Locations-Tab-Öffnen!) ⚠️ BUG-28

Locations-Tab öffnen:
  → GET /locations → Locations.all = [...]

saveEdit() (nach PATCH):
  → Locations.all = await API.get('/locations')  ✅ Server-Fetch (seit BUG-30-Fix)
  → Feed.render()

Filter.apply():
  → schlägt loc.difficulty über Locations.all nach
  → wenn Locations.all leer → Filter wirkungslos ⚠️ BUG-28 (noch offen)
```

---

## PATCH-Invalidierungslogik

Was welcher PATCH-Endpoint invalidiert / neu auslöst:

| Geändertes Feld | recompute_triggered | Was wird neu berechnet |
|-----------------|--------------------|-----------------------|
| `observer_lat`, `observer_lon`, `subject_lat`, `subject_lon` | ✅ True | Feed (14 Tage) + Kalender (365 Tage) für diese Location |
| `subject_height_m`, `subject_width_m` | ✅ True | Feed + Kalender |
| `focal_length_suggestions`, `observer_floor_height_m` | ✅ True | Feed + Kalender |
| `name`, `description` | ❌ False | nichts (bewusst, TASK-16) |
| Unbekanntes Feld | HTTP 400 | nichts |

### Recompute-Ablauf nach PATCH

```
PATCH /locations/{id} mit recompute-Feld
  → SQLite location_overrides schreiben
  → _load_location_overrides() → In-Memory aktualisieren
  → _run_precompute(location_ids=[id])
      → precompute.py startet als Subprocess
      → liest data/locations.py + SQLite Overrides (seit BUG-29-Fix)
      → compute_opportunities_incremental(location_id=id) → opportunities.json partial update
      → compute_calendar_incremental(location_id=id) → calendar.json partial update
      → Merge: nur Einträge für location_id==id werden ersetzt, Rest bleibt
```

---

## Typische Synchronisations-Fallen (gelernt aus Bugs)

### Falle 1: precompute liest keine Overrides (BUG-29)

**Symptom:** Nach PATCH Koordinaten zeigen Kalender/Feed weiter alte Werte.  
**Ursache:** precompute.py lud nur `data/locations.py`, ignorierte SQLite-Overrides.  
**Fix:** `precompute.py` merged nach dem Start SQLite `location_overrides` in LOCATIONS.  
**Prüfen:** Wenn neue Felder zu `location_overrides` kommen → sicherstellen, dass `precompute.py:_load_overrides()` sie ebenfalls lädt.

### Falle 2: In-Memory-Mutation statt Server-Fetch (BUG-30)

**Symptom:** Name nach PATCH sofort im UI sichtbar, aber nach Reload oder curl alt.  
**Ursache:** Frontend mutierte nur `Locations.all[i].name` im Speicher, ohne Re-Fetch.  
**Fix:** Nach jedem PATCH `Locations.all = await API.get('/locations')`.  
**Regel:** Kein Feature darf `Locations.all` direkt mutieren — immer Server-Fetch.

### Falle 3: Locations.all beim App-Start leer (BUG-28, noch offen)

**Symptom:** Schwierigkeitsfilter wirkungslos bis Locations-Tab besucht.  
**Ursache:** `Locations.all` wird lazy geladen (erst beim Tab-Öffnen).  
**Fix ausstehend:** `Locations.all` beim Boot laden, oder lazy-trigger wenn Filter aktiv.

### Falle 4: coordinates_hash verhindert Recompute (BUG-29 Nebeneffekt)

**Symptom:** Log zeigt "0 neu berechnet" — kein Fehler, aber veraltete Daten.  
**Ursache:** Hash der Koordinaten unverändert, weil precompute die neuen Koordinaten noch nicht kannte.  
**Prüfen:** Nach PATCH Koordinaten → im Log auf "X neu berechnet" prüfen (X > 0).

---

## Custom-Locations vs. Basis-Locations

| Typ | Wo gespeichert | precompute liest | Recompute-fähig |
|-----|---------------|-----------------|-----------------|
| Basis-Locations | `data/locations.py` | ✅ immer | ✅ |
| Location-Overrides | SQLite `location_overrides` | ✅ seit BUG-29-Fix | ✅ |
| Custom-Locations (User-angelegt) | SQLite `locations`-Tabelle | ⚠️ noch nicht (TASK-?)| ⚠️ ausstehend |

> **Custom-Locations** werden vom Server in-memory gehalten und erscheinen in GET /locations, aber precompute.py hat dafür noch keinen Ladepfad. Feed/Kalender für Custom-Locations entstehen nur durch manuellen Full-Recompute.

---

## Cache-Datei-Referenz

| Datei | Endpoint | Aktualisiert durch | Typische Größe |
|-------|---------|-------------------|---------------|
| `opportunities.json` | `GET /opportunities` | Precompute (Feed), Cron (täglich) | ~2–5 MB |
| `calendar.json` | `GET /calendar` | Precompute (Kalender), Cron (0:01 Uhr) | ~10–30 MB |
| `discover.json` | `GET /scout` | Precompute (Scout) | ~1–3 MB |

Pfad: `backend/data_prod/cache/` (Prod) / `backend/data_dev/cache/` (Dev).

---

*Aktualisieren wenn: neue Datenquellen hinzukommen, PATCH-Whitelist erweitert wird, Custom-Locations-Recompute implementiert wird.*
