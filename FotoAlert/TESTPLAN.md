# FotoAlert – Testplan

> Versionierter, wiederholt ausführbarer Testplan.  
> Status: `[ ]` offen · `[~]` in Arbeit · `[x]` bestanden · `[!]` fehlgeschlagen

---

## 1. Voraussetzungen & Setup

### 1.1 Backend starten

```bash
# Terminal 1: in das Backend-Verzeichnis wechseln
cd "/Users/stephan/Claude/Projects/Foto Location Guide/FotoAlert/backend"

# Python-Abhängigkeiten (einmalig)
pip install fastapi uvicorn apscheduler skyfield requests aiohttp

# Server starten
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Erwartetes Log beim Start:**
```
INFO  FotoAlert Backend startet...
INFO  Scheduler gestartet. Initialer Opportunity-Refresh läuft im Hintergrund.
INFO  PWA Web-App wird ausgeliefert aus: .../FotoAlert/web
INFO  Starte Opportunity-Refresh für N Locations...
```

### 1.2 App im Browser öffnen

```
http://localhost:8000
```

Für Test im Netzwerk (iPhone/iPad): `http://[Mac-IP]:8000`  
Mac-IP ermitteln: `ipconfig getifaddr en0` im Terminal.

---

## 2. Smoke Tests – Backend

### 2.1 Health-Check
```bash
curl http://localhost:8000/ | python3 -m json.tool
```
**Erwartung:** `{"status": "ok", "locations_count": 20, "version": "1.0.0"}`
- [ ] Status = "ok"
- [ ] locations_count ≥ 15

### 2.2 Locations-Liste
```bash
curl http://localhost:8000/locations | python3 -m json.tool | head -60
```
**Erwartung:** Array mit ≥ 15 Location-Objekten
- [ ] Schloss Babelsberg → Belvedere vorhanden (`id: schloss_babelsberg_pfingstberg`)
- [ ] Jede Location hat `observer_lat`, `observer_lon`
- [ ] `focal_length_suggestions` nicht leer

### 2.3 Opportunities
```bash
curl "http://localhost:8000/opportunities?min_score=0.2&days=14" | python3 -m json.tool | head -80
```
**Erwartung:** Array mit Opportunities
- [ ] Mindestens 1 Opportunity zurückgegeben
- [ ] Jedes Objekt hat: `shoot_time`, `title`, `overall_score`, `camera_hints`
- [ ] Scores zwischen 0.0 und 1.0
- [ ] `shoot_window_start` ≤ `shoot_time` ≤ `shoot_window_end`

### 2.4 Daily Briefing
```bash
curl "http://localhost:8000/daily-briefing" | python3 -m json.tool
```
- [ ] `summary` vorhanden und nicht leer
- [ ] `top_opportunities` ist Array (kann leer sein)
- [ ] `highest_score` zwischen 0.0 und 1.0

### 2.5 Wetter-Integration
```bash
# Open-Meteo direkt testen (kein API-Key erforderlich)
curl "https://api.open-meteo.com/v1/forecast?latitude=52.3975&longitude=13.0976&hourly=cloudcover,visibility,precipitation&timezone=Europe/Berlin&forecast_days=3"
```
- [ ] API antwortet (HTTP 200)
- [ ] `hourly.cloudcover` enthält 72 Werte (3 Tage × 24h)

---

## 3. Kern-Szenario: Babelsberg → Belvedere / Pfingstberg

> **Stephans Leit-Beispiel:** Von Schloss Babelsberg auf das Belvedere auf dem Pfingstberg schauen. Sonne oder Mond direkt hinter dem Turm. Azimut ~330°, Distanz ~3200m, Motiv-Höhe ~75m → Höhenwinkel ~1.16°.

### 3.1 Alignment-Vorschau via API
```bash
curl -X POST http://localhost:8000/preview-alignment \
  -H "Content-Type: application/json" \
  -d '{
    "observer_lat": 52.3975,
    "observer_lon": 13.0976,
    "subject_lat": 52.4158,
    "subject_lon": 13.0688,
    "subject_name": "Belvedere Pfingstberg",
    "subject_height_m": 75,
    "subject_width_m": 40,
    "days": 14
  }' | python3 -m json.tool
```
**Erwartung:**
- [ ] `profile.azimuth_deg` ≈ 320–340° (nordwestlich)
- [ ] `profile.ground_distance_m` ≈ 3000–3400m
- [ ] `profile.angular_altitude_top_deg` ≈ 1.1–1.3°
- [ ] `focal_length_mm` zwischen 200 und 400
- [ ] `alignments` enthält mindestens 1 Eintrag in 14 Tagen
- [ ] Alignment mit `alignment_type = "AT_CROWN"` oder `"CLEARING_TOP"` vorhanden

### 3.2 Sonnenfinsternis 12. August 2026 (Partiell)
```bash
curl "http://localhost:8000/opportunities?min_score=0.1&days=14" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); [print(o['title'],o['shoot_time'][:16],f'{o[\"overall_score\"]:.0%}') for o in d if 'Sonnenfinsternis' in o.get('event_type','') or 'Babelsberg' in o.get('location_name','')]"
```
- [ ] Wenn innerhalb des 14-Tage-Fensters: Opportunity für die Sonnenfinsternis erscheint
- [ ] Zeitfenster enthält ca. 20:09 Uhr (MESZ = 18:09 UTC)

### 3.3 Vollmond-Alignment Babelsberg
```bash
# Nächsten Vollmond finden und auf Alignment prüfen
python3 - << 'EOF'
from skyfield.api import load, wgs84
from datetime import date, timedelta
ts = load.timescale()
eph = load('de421.bsp')
earth, moon = eph['earth'], eph['moon']
sun = eph['sun']
for d in range(30):
    t = ts.utc(date.today().year, date.today().month, date.today().day + d)
    obs = earth + wgs84.latlon(52.3975, 13.0976)
    alt_sun = (earth + wgs84.latlon(52.3975, 13.0976)).at(t).observe(sun).apparent().altaz()[0]
    print(f"{date.today() + timedelta(d)}: Sonne Höhe {alt_sun.degrees:.1f}°")
    break
print("Skyfield OK")
EOF
```
- [ ] Skyfield importiert ohne Fehler
- [ ] de421.bsp wird geladen (wird bei erstem Aufruf heruntergeladen: ~17MB)

---

## 4. Szenario: Quick Location Capture – Reichstag → Potsdamer Platz

> **Beispiel:** Ich stehe auf dem Platz vor dem Reichstag und blicke durch den Tiergarten auf den Potsdamer Platz. Wann geht der Mond dort auf?

### 4.1 API-Test
```bash
curl -X POST http://localhost:8000/preview-alignment \
  -H "Content-Type: application/json" \
  -d '{
    "observer_lat": 52.5186,
    "observer_lon": 13.3762,
    "subject_lat": 52.5096,
    "subject_lon": 13.3762,
    "subject_name": "Potsdamer Platz Hochhaus",
    "subject_height_m": 100,
    "subject_width_m": 50,
    "days": 14
  }' | python3 -m json.tool
```
**Erwartung:**
- [ ] `profile.azimuth_deg` ≈ 175–185° (südlich)
- [ ] `profile.ground_distance_m` ≈ 900–1100m
- [ ] Mond-Alignments vorhanden

### 4.2 Web-UI Test (manuell)
1. App im Browser öffnen: `http://localhost:8000`
2. „+" Tab antippen
3. „📍 GPS"-Button klicken → erlaubt Standortzugriff → Punkt wird auf Karte gesetzt
4. Auf Karte klicken für Motiv-Position
5. „Alignments berechnen ✦" klicken
6. Ergebnis-Vorschau erscheint

- [ ] GPS-Button funktioniert (fragt nach Erlaubnis)
- [ ] Karten-Klick setzt Motiv-Marker
- [ ] Verbindungslinie zwischen Fotograf und Motiv wird gezeichnet
- [ ] Preview-Box zeigt Azimut, Distanz, Höhenwinkel
- [ ] Alignment-Liste mit Datum/Uhrzeit erscheint

---

## 5. Szenario: Schillingstraße → Oberbaumbrücke

> **Beispiel:** Ich stehe auf der Brücke in der Schillingstraße über die Spree und fotografiere den aufgehenden Mond oder Sonne über der Oberbaumbrücke.

### 5.1 API-Test
```bash
curl -X POST http://localhost:8000/preview-alignment \
  -H "Content-Type: application/json" \
  -d '{
    "observer_lat": 52.5133,
    "observer_lon": 13.4289,
    "subject_lat": 52.5015,
    "subject_lon": 13.4452,
    "subject_name": "Oberbaumbrücke Nordturm",
    "subject_height_m": 33,
    "subject_width_m": 25,
    "days": 14
  }' | python3 -m json.tool
```
**Erwartung:**
- [ ] `profile.azimuth_deg` ≈ 145–165° (südöstlich)
- [ ] `profile.ground_distance_m` ≈ 1600–1900m
- [ ] `angular_altitude_top_deg` ≈ 0.8–1.3°
- [ ] Empfohlene Brennweite 200–400mm

---

## 6. PWA Web-App – UI-Tests (manuell im Browser)

### 6.1 Grundfunktion
| Test | Erwartung | Status |
|------|-----------|--------|
| Seite lädt unter `localhost:8000` | Dark Theme, Logo sichtbar, Tab Bar | [ ] |
| Feed-Tab zeigt Chancen | Mindestens 1 Opportunity-Karte | [ ] |
| Score-Ring korrekt (z.B. 75%) | Ring zu 75% gefüllt, Farbe orange | [ ] |
| Opportunity antippen | Detail-Sheet öffnet sich von unten | [ ] |
| Detail-Sheet: Zeitfenster | 3 Spalten: Start / Optimal / Ende | [ ] |
| Detail-Sheet: Kamera-Tipps | Brennweite, Blende, Zeit sichtbar | [ ] |
| „Zum Kalender" Tap | `.ics`-Datei wird heruntergeladen | [ ] |
| „Zum Kalender"-Datei öffnen | Apple Kalender öffnet Event | [ ] |
| Overlay antippen | Sheet schließt sich | [ ] |

### 6.2 Karte
| Test | Erwartung | Status |
|------|-----------|--------|
| Karte-Tab → Leaflet-Karte lädt | Dunkle Karte, Berlin zentriert | [ ] |
| Locations als farbige Pins | ≥ 10 Pins sichtbar | [ ] |
| Pin antippen | Popup mit Name und Kategorie | [ ] |

### 6.3 Quick-Add (+ Tab)
| Test | Erwartung | Status |
|------|-----------|--------|
| „+" Tab → Sheet öffnet | Add-Sheet erscheint, Karte vorhanden | [ ] |
| GPS-Button | Browser fragt nach Standort | [ ] |
| Karte antippen | Motiv-Marker erscheint, Linie zu Fotograf | [ ] |
| „Alignments berechnen" ohne Punkte | Toast: „Bitte Standort und Motiv setzen" | [ ] |
| „Alignments berechnen" mit Punkten | Preview-Box mit Profil + Alignment-Liste | [ ] |
| „Location speichern" | Toast: „✅ Location gespeichert!" | [ ] |

### 6.4 Locations-Tab
| Test | Erwartung | Status |
|------|-----------|--------|
| Locations-Liste lädt | ≥ 15 Location-Karten sichtbar | [ ] |
| Suchfeld: „Babelsberg" | Filtert auf Babelsberg-Location | [ ] |
| Suchfeld: „Wasser" | Zeigt Wasser-Locations | [ ] |

### 6.5 Einstellungen
| Test | Erwartung | Status |
|------|-----------|--------|
| Mindest-Score Slider auf 80% | Nach Feed-Wechsel: weniger Chancen | [ ] |
| Backend-URL ändern | Wird in localStorage gespeichert | [ ] |
| „Jetzt" Refresh | Toast nach ~3s: „✅ Daten aktualisiert" | [ ] |

---

## 7. Astronomie-Präzisionstests

### 7.1 Sonnenauf-/Untergang Berlin (Referenz-Check)
```bash
python3 - << 'EOF'
from skyfield.api import load, wgs84, N, E
from datetime import date
ts = load.timescale()
eph = load('de421.bsp')
earth, sun = eph['earth'], eph['sun']
from skyfield import almanac
t0 = ts.utc(date.today().year, date.today().month, date.today().day)
t1 = ts.utc(date.today().year, date.today().month, date.today().day + 1)
observer = earth + wgs84.latlon(52.5200 * N, 13.4050 * E)
f = almanac.sunrise_sunset(eph, observer)
times, events = almanac.find_discrete(t0, t1, f)
for t, e in zip(times, events):
    print(f"{'Sonnenaufgang' if e else 'Sonnenuntergang'}: {t.utc_strftime('%H:%M')} UTC")
EOF
```
- [ ] Sonnenaufgang für Berlin (Sommer) zwischen 01:00–03:30 UTC
- [ ] Sonnenuntergang zwischen 19:00–22:00 UTC
- [ ] Differenz zu Zeitangaben auf [timeanddate.com](https://www.timeanddate.com/sun/germany/berlin) < 2 Minuten

### 7.2 Mondphase Check
```bash
python3 - << 'EOF'
from skyfield.api import load
from skyfield import almanac
ts = load.timescale()
eph = load('de421.bsp')
from datetime import date
t = ts.utc(date.today().year, date.today().month, date.today().day)
phase = almanac.moon_phase(eph, t)
print(f"Mondphase heute: {phase.degrees:.1f}° ({['Neumond','Zunehmend','Vollmond','Abnehmend'][int(phase.degrees/90)%4]})")
EOF
```
- [ ] Ergebnis plausibel (Vergleich mit [timeanddate.com/moon/germany/berlin](https://www.timeanddate.com/moon/germany/berlin))

### 7.3 Haversine-Distanz Babelsberg → Pfingstberg
```bash
python3 - << 'EOF'
import math
def haversine(lat1,lon1,lat2,lon2):
    R=6371000; phi1,phi2=math.radians(lat1),math.radians(lat2)
    dlat,dlon=math.radians(lat2-lat1),math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(phi1)*math.cos(phi2)*math.sin(dlon/2)**2
    return R*2*math.asin(math.sqrt(a))
d = haversine(52.3975, 13.0976, 52.4158, 13.0688)
print(f"Distanz: {d:.0f}m (erwartet: ~3200m)")
angle = math.degrees(math.atan(75 / d))
print(f"Höhenwinkel Belvedere-Spitze: {angle:.3f}° (erwartet: ~1.16°)")
EOF
```
- [ ] Distanz ≈ 3100–3300m
- [ ] Höhenwinkel ≈ 1.1–1.2°

---

## 8. Performance & Edge-Case Tests

### 8.1 Response-Zeiten
```bash
time curl -s "http://localhost:8000/opportunities?min_score=0.2&days=14" > /dev/null
```
- [ ] < 500ms (Cache warm)
- [ ] < 30s beim ersten Start (Refresh im Hintergrund)

### 8.2 /preview-alignment Edge Cases
```bash
# Gleicher Punkt für Fotograf und Motiv
curl -X POST http://localhost:8000/preview-alignment \
  -H "Content-Type: application/json" \
  -d '{"observer_lat":52.52,"observer_lon":13.40,"subject_lat":52.52,"subject_lon":13.40,"subject_height_m":0,"subject_width_m":0}'
```
- [ ] Keine Exception, sinnvoller Fehler oder 0-Distanz-Ergebnis

```bash
# Ungültige Koordinaten
curl -X POST http://localhost:8000/preview-alignment \
  -H "Content-Type: application/json" \
  -d '{"observer_lat":999,"observer_lon":13.40,"subject_lat":52.52,"subject_lon":13.40}'
```
- [ ] HTTP 400 mit verständlichem Fehlertext

### 8.3 CORS
```bash
curl -H "Origin: http://localhost:3000" -I http://localhost:8000/locations
```
- [ ] `Access-Control-Allow-Origin: *` im Response-Header

---

## 9. Regressions-Checkliste (nach jeder Code-Änderung)

Schnelltest – dauert ca. 2 Minuten:

```bash
cd "/Users/stephan/Claude/Projects/Foto Location Guide/FotoAlert/backend"

# 1. Syntax-Check
python3 -m py_compile main.py calculations/astronomy.py calculations/opportunity.py && echo "Syntax OK"

# 2. Health
curl -s http://localhost:8000/ | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'; print('Health OK')"

# 3. Locations
curl -s http://localhost:8000/locations | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d)>10; print(f'Locations OK ({len(d)})')"

# 4. Opportunities (min_score sehr niedrig)
curl -s "http://localhost:8000/opportunities?min_score=0.1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Opportunities: {len(d)} zurückgegeben')"

# 5. Preview-Alignment Babelsberg
curl -s -X POST http://localhost:8000/preview-alignment \
  -H "Content-Type: application/json" \
  -d '{"observer_lat":52.3975,"observer_lon":13.0976,"subject_lat":52.4158,"subject_lon":13.0688,"subject_height_m":75,"subject_width_m":40}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); az=d['profile']['azimuth_deg']; assert 300<=az<=360, f'Azimut falsch: {az}'; print(f'Preview OK (Azimut {az:.1f}°)')"

echo "=== Alle Smoke-Tests bestanden ==="
```

---

## 10. Bekannte Einschränkungen (aktuelle Version)

| Einschränkung | Workaround | Backlog |
|---------------|------------|---------|
| Geländehöhen-Unterschied ignoriert (beide auf NN) | Manuelle Korrektur über `subject_height_m` | US-Höhenkorrektur (OpenTopoData) |
| Wetter nur bis 7 Tage via Open-Meteo | Feed zeigt "Wetter unbekannt" für T+7 | US-02 |
| Sichtachsen-Hindernisse nicht geprüft (Gebäude, Bäume) | Manuell über Google Street View prüfen | US-Sichtachsen-Check |
| Atmosphärische Phänomene (Nebel, goldene Wolken) | Cloudcover als Proxy | US-Atmosphärische-Optik |
| Apple Maps Sync nicht implementiert | GPX-Export manuell | US-Apple-Maps |

---

*Zuletzt aktualisiert: 2026-06-13 · Testplan-Version: 1.1*
