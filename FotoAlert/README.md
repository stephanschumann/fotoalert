# FotoAlert – Intelligente Foto-Chancen für Berlin & Brandenburg

> **Du stellst dich vor Schloss Babelsberg. Die App sagt dir: heute um 20:09 Uhr, 135mm,  
> partielle Sonnenfinsternis über dem Belvedere auf dem Pfingstberg.**

FotoAlert kombiniert Astronomie-Berechnungen, Wetterdaten und eine kuratierte Location-Datenbank  
zu konkreten, priorisierten Foto-Empfehlungen mit exakten Uhrzeiten und Kamera-Einstellungen.

---

## Was die App erkennt

| Ereignis | Details |
|---|---|
| **Goldene Stunde** | Morgen & Abend, tagesgenau pro Location |
| **Blaue Stunde** | Künstliches Licht trifft Tageslicht |
| **Sonnen-Alignment** | Sonne hinter Turm, Dom, Schloss (Azimut-Kalkulation) |
| **Mond-Alignment** | Mond über Motiv – mit Mondphase & Brennweite |
| **Vollmond** | Mondaufgang/-untergang nahe Landmarks |
| **Milchstraße** | Galaktisches Zentrum, Dunkel-Score, April–September |
| **Meteoritenschauer** | Perseiden (12. Aug), Geminiden (14. Dez), alle 8 Hauptschauer |
| **Sonnenfinsternisse** | Über astronomische Ephemeriden |

---

## Architektur

```
FotoAlert/
├── backend/          # Python FastAPI Backend
│   ├── main.py       # API + Scheduler
│   ├── calculations/
│   │   ├── astronomy.py    # Skyfield: Sonne/Mond/Sterne
│   │   ├── weather.py      # Open-Meteo (kostenlos)
│   │   └── opportunity.py  # Scoring-Algorithmus
│   ├── data/
│   │   └── locations.py    # ~20 kuratierte Locations BB
│   └── notifications/
│       └── push.py         # Apple Push Notification Service
└── ios/
    └── FotoAlert/          # SwiftUI iOS App
        ├── Views/          # Feed, Karte, Detail, Settings
        ├── Models/         # Datenmodelle
        └── Services/       # API-Client, Push-Service
```

---

## Setup Backend

### 1. Python-Umgebung

```bash
cd FotoAlert/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Skyfield-Ephemeride herunterladen

Beim ersten Start lädt Skyfield automatisch `de421.bsp` herunter (~17 MB).  
Alternativ manuell: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/

### 3. Umgebungsvariablen (optional, nur für Push-Notifications)

```bash
cp .env.example .env
# .env mit deinen APNs-Zugangsdaten befüllen
```

### 4. Backend starten

```bash
python main.py
# Läuft auf http://localhost:8000
# API-Dokumentation: http://localhost:8000/docs
```

Der Scheduler berechnet täglich um 6:00 Uhr (Berliner Zeit) alle Foto-Chancen  
für die nächsten 7 Tage und sendet Push-Notifications für besondere Ereignisse.

### Verfügbare Endpoints

| Endpoint | Beschreibung |
|---|---|
| `GET /` | Health-Check |
| `GET /locations` | Alle Locations |
| `GET /locations/{id}` | Einzelne Location |
| `GET /opportunities` | Kommende Chancen (7 Tage) |
| `GET /opportunities/today` | Chancen für heute |
| `GET /daily-briefing` | Tages-Briefing Top 10 |
| `POST /refresh` | Manueller Daten-Refresh |
| `POST /register-device` | Push-Token registrieren |

---

## Setup iOS App

### Voraussetzungen
- Xcode 15+
- iOS 17+
- Apple Developer Account (für Push-Notifications auf echtem Gerät)

### Xcode-Projekt anlegen

Da die Quelldateien bereits vorhanden sind, erstelle ein neues SwiftUI-Projekt in Xcode:

1. **Xcode → New Project → iOS → App**
2. Product Name: `FotoAlert`
3. Bundle Identifier: `de.fotoalert.app`
4. Interface: **SwiftUI**, Language: **Swift**
5. Alle Dateien aus `ios/FotoAlert/` in das Xcode-Projekt ziehen

### Backend-URL konfigurieren

In `APIService.swift` Zeile 10:
```swift
let BACKEND_URL = "http://localhost:8000"   // lokales Testen
// oder für echte Nutzung:
let BACKEND_URL = "https://dein-server.de"
```

### Push-Notifications aktivieren

1. Xcode → Target → Signing & Capabilities → **+ Push Notifications**
2. developer.apple.com → Certificates → **Keys → Create Key**
3. Key-Typ: Apple Push Notifications service (APNs)
4. `.p8` Datei herunterladen, **Key ID** und **Team ID** notieren
5. In `.env` eintragen

---

## Backend auf einem Server betreiben

Für echte Push-Notifications und automatische Berechnungen empfehle ich  
einen kleinen VPS (z.B. Hetzner CX22, ~4€/Monat):

```bash
# systemd Service-Datei
sudo nano /etc/systemd/system/fotoalert.service
```

```ini
[Unit]
Description=FotoAlert Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/fotoalert/backend
ExecStart=/opt/fotoalert/backend/venv/bin/python main.py
Restart=always
EnvironmentFile=/opt/fotoalert/backend/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable fotoalert
sudo systemctl start fotoalert
```

---

## Locations erweitern

Neue Locations zur Datenbank hinzufügen in `backend/data/locations.py`:

```python
PhotoLocation(
    id="mein_standort",
    name="Mein Standort",
    description="Beschreibung...",
    category=LocationCategory.SKYLINE,
    observer_lat=52.123,  # GPS des Fotografen
    observer_lon=13.456,
    subject_lat=52.124,   # GPS des Motivs
    subject_lon=13.457,
    subject_name="Motiv-Name",
    subject_height_m=50,  # Höhe des Gebäudes
    distance_m=500,       # Entfernung Fotograf → Motiv
    best_times=[BestTime.GOLDEN_EVENING],
    focal_length_suggestions=[135, 200],
    solar_alignment_note="Sonnenuntergang hinter dem Turm: April/August",
)
```

---

## Datenquellen

- **Wetter**: [Open-Meteo](https://open-meteo.com) – kostenlos, kein API-Key
- **Astronomie**: [Skyfield](https://rhodesmill.org/skyfield/) + JPL DE421 Ephemeride
- **Push-Notifications**: Apple Push Notification Service (APNs)
- **Locations**: Manuell kuratiert, inspiriert von Locationscout.net

---

## Geplante Erweiterungen

- [ ] Kometen-Integration (NASA JPL Horizons API)
- [ ] Feuerwerk-Events (Berlin/Potsdam)
- [ ] Locationscout Web-Scraping für neue Spots
- [ ] Wetter-Radar-Overlay auf der Karte
- [ ] Augmented Reality: Sonnenbahn über Kamera-Vorschau
- [ ] Apple Watch Komplikation mit nächster Chance
- [ ] Export als PhotoPills-Bookmark
