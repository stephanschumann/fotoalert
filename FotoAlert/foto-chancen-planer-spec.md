# Spec: Foto-Chancen-Planer (Berlin · Potsdam · Umland)

> **Arbeitstitel:** `foto-chancen-planer`
> **Status:** Entwurf v0.1 — Handoff aus Chat, zur Weiterbearbeitung in Cowork
> **Methode:** OpenSpec (Requirements mit `WHEN/THEN`-Szenarien, Capability-Dekomposition)
> **Sprache:** Deutsch; OpenSpec-Schlüsselwörter (`SHALL`, `WHEN`, `THEN`, `Scenario`) auf Englisch nach Konvention.

---

## 1. Proposal — Warum & Was

### Problem
Es gibt kein Werkzeug, das automatisiert und bewertet vorschlägt, **welches Motiv** (Schloss, Turm, Windmühle, Stadtansicht, Flusslauf …) von **welchem Standort** aus in den nächsten 14 Tagen fotografisch wertvoll festzuhalten ist — unter der Bedingung einer **freien Sichtachse** und einer **Himmelserscheinung (Mond/Sonne) im 2°-Fenster um die Motivspitze** zur goldenen oder blauen Stunde. Existierende Tools (PhotoPills, TPE/3D, PlanIt Pro) liefern Ephemeride und 3D-Horizont, aber **manuell pro Szene** und ohne automatisches Scoring/Ranking über viele Motive.

### Ziel
Ein System, das aus **öffentlich zugänglichen Daten** einen nach Score sortierten 14-Tage-Ausblick erzeugt. Ausgabeformat pro Chance:

> Um den Vollmond während der Golden Hour über dem *Motiv* zu fotografieren, gehe am **DATUM** um **UHRZEIT** an **STANDORT (GPS)**; das Motiv befindet sich bei **GPS** in **ENTFERNUNG km/m**. (+ Himmelserscheinung, Score, Confidence)

### Nicht-Ziele (v1)
- Keine Echtzeit-/Live-Funktion; reine Vorausplanung.
- Keine eigene Wetter-Modellierung (externe Vorhersage wird konsumiert).
- Keine Komposition jenseits der Mond/Sonne-am-Motiv-Geometrie (z. B. Vordergrund-Layering, Reflexionen) — als spätere Erweiterung.
- Keine Mobile-App; v1 = Pipeline + rangierte Ausgabe (Liste/GeoJSON/Karte).

### Prior Art (Abgrenzung)
PhotoPills / The Photographer's Ephemeris (TPE & TPE 3D) / PlanIt Pro lösen Alignment + teils 3D-Horizont. **Neu hier:** automatische Verschattungsanalyse über amtliche DOM/LoD2-Daten + Scoring + Mehr-Motiv-Ranking über ein 14-Tage-Fenster.

---

## 2. Domänenmodell & Begriffe

| Begriff | Definition |
|---|---|
| **Motiv (M)** | Festes Objekt mit Lat/Lon und absoluter Spitzenhöhe `H` (Geländehöhe + Bauwerkshöhe). |
| **Standort (S)** | Aufnahmeposition des Fotografen (Lat/Lon, Augenhöhe `h_eye`). |
| **Himmelskörper (C)** | Mond oder Sonne, beschrieben durch Azimut `az(C)` und Höhe `alt(C)`. |
| **Chance (Opportunity)** | Tupel (M, S, C, Zeitpunkt) mit berechnetem Score. |
| **Sichtachse** | Sichtlinie S→M; gilt als frei, wenn kein Oberflächenpunkt (DOM/LoD2) sie überragt. |
| **Goldene/Blaue Stunde** | Zeitfenster, abgeleitet aus Sonnenhöhe: golden ≈ −4°…+6°, blau ≈ −6°…−4° (parametrierbar). |
| **2°-Fenster** | Chance gilt als „Alignment", wenn Winkelabstand zwischen `C` und Motivspitze ≤ 2°. |

### Geometrie (Kern)
- **Azimut-Bedingung:** Peilung `bearing(S→M) ≈ az(C)`. S liegt auf der Rückverlängerung von `az(C)` hinter M.
- **Höhen-Bedingung:** scheinbare Höhe der Motivspitze `α = arctan((H − h_eye) / d) − Erdkrümmungs-/Refraktionskorrektur`; für „Mond sitzt auf der Spitze" gilt `alt(C) ≈ α`.
- **Distanz-Ableitung (auf der Spitze):** `d = (H − h_eye) / tan(alt(C))`.
- **Komposition:** Mondscheibe ≈ 0,52° konstant; größere Distanz `d` → kleineres Motiv → relativ größerer Mond (Telekompression). `d` ist kompositorischer Freiheitsgrad innerhalb `[d_min, d_max]`.

---

## 3. Capabilities (dekomponiert)

### Capability: `astronomie`

#### Requirement: Himmelskörper-Position
Das System SHALL für jeden Zeitpunkt und Standort im Planungsfenster Azimut, Höhe (refraktionskorrigiert), Phase und Illuminationsgrad von Sonne und Mond berechnen.

##### Scenario: Mondposition zu gegebenem Zeitpunkt
- **WHEN** ein Zeitpunkt `t` und ein Standort `S` gegeben sind
- **THEN** liefert das System `az(Mond)`, `alt(Mond)` (refraktionskorrigiert), `illumination ∈ [0,1]` und `phase`

##### Scenario: Refraktion am Horizont
- **WHEN** `alt(C)` nahe 0° liegt (Auf-/Untergang)
- **THEN** wird die atmosphärische Refraktion (~0,5°) eingerechnet, sodass das Timing nicht systematisch verschoben ist

#### Requirement: Lichtfenster
Das System SHALL goldene und blaue Stunde aus der Sonnenhöhe ableiten — getrennt für Morgen und Abend.

##### Scenario: Tagesfenster bestimmen
- **WHEN** Datum und Standort gegeben sind
- **THEN** liefert das System Intervalle `[start, end]` für golden_morgen, golden_abend, blau_morgen, blau_abend

---

### Capability: `motiv-katalog`

#### Requirement: Motiv-Inventar
Das System SHALL einen Katalog von Motiven mit Lat/Lon, Geländehöhe (DGM), Bauwerkshöhe, abgeleiteter absoluter Spitzenhöhe `H`, Kategorie und Quelle führen.

##### Scenario: Motiv aus OSM + Höhe aus mehreren Quellen
- **WHEN** ein OSM-Objekt mit passendem Tag (`man_made=tower|windmill`, `historic=castle`, Brücke, Schornstein …) gefunden wird
- **THEN** wird `H` aus (in Priorität) `height`-Tag → Wikidata → LoD2-Firsthöhe abgeleitet; Geländehöhe aus DGM am Fußpunkt addiert

##### Scenario: Höhe unsicher
- **WHEN** keine belastbare Bauwerkshöhe ermittelbar ist
- **THEN** wird das Motiv mit `hoehe_confidence = niedrig` markiert; dies fließt in die Confidence der Chance ein

#### Requirement: Kuratierte Leitmotive
Das System SHALL eine manuell gepflegte Liste regionaler Leitmotive enthalten (u. a. Fernsehturm, Siegessäule, Berliner Dom, Schloss Sanssouci, Schloss Cecilienhof, Flatowturm, Glienicker Brücke, Historische Mühle Sanssouci, Babelsberg).

---

### Capability: `standort-alignment`

#### Requirement: Standort aus Alignment ableiten
Das System SHALL pro Motiv × Mondfenster den Standort `S` so bestimmen, dass `bearing(S→M) = az(C)` und (für „auf der Spitze") `d = (H − h_eye)/tan(alt(C))`.

##### Scenario: Geometrisch gültige Distanz
- **WHEN** `alt(C)` so liegt, dass `d ∈ [d_min, d_max]`
- **THEN** wird `S` als Geo-Punkt entlang der Rückpeilung berechnet und als Kandidat gespeichert

##### Scenario: Mond zu hoch/zu tief
- **WHEN** `d` außerhalb `[d_min, d_max]` fällt
- **THEN** wird die Chance verworfen oder als `suboptimal` markiert (kein „auf der Spitze"-Shot möglich)

#### Requirement: 2°-Fenster
Das System SHALL alle Chancen erfassen, deren Winkelabstand zwischen `C` und Motivspitze ≤ 2° beträgt (nicht nur exakt „auf der Spitze").

#### Requirement: Erreichbarkeit
Das System SHALL prüfen, ob `S` öffentlich erreichbar ist (kein Wasser/Privatgelände) — via OSM-Landuse/Access-Tags.

##### Scenario: Standort im Wasser
- **WHEN** `S` auf eine Wasserfläche oder unzugängliche Fläche fällt
- **THEN** wird `S` entlang der Sichtachse auf den nächstgelegenen erreichbaren Punkt verschoben oder die Chance als `nicht_erreichbar` markiert

---

### Capability: `sichtachse` (Verschattungsanalyse)

#### Requirement: LOS-Gate (Sichtachse S→M)
Das System SHALL entlang des Profils S→M prüfen, dass kein Oberflächenpunkt (DOM bzw. LoD2-Gebäude) die Sichtlinie überragt.

##### Scenario: Baum oder Gebäude verdeckt
- **WHEN** an einem Stützpunkt des Profils der Oberflächen-Höhenwinkel > Sichtlinien-Höhenwinkel ist
- **THEN** wird die Chance verworfen (`gate_los = 0`)

#### Requirement: Horizont-Gate (Sichtbarkeit von C)
Das System SHALL prüfen, dass `C` über dem effektiven, durch Terrain + Bauwerke + Vegetation definierten Horizont in Richtung `az(C)` steht.

##### Scenario: Mond noch hinter Hügelkette
- **WHEN** `alt(C)` unter dem effektiven Horizontprofil in `az(C)` liegt
- **THEN** ist `C` nicht sichtbar (`gate_horizont = 0`)

#### Requirement: Datenwahl & Caching
Das System SHALL DOM als primäre Verschattungsquelle (inkl. Vegetation) und LoD2 für saubere Gebäudehöhen nutzen und Horizontprofile pro Motiv cachen.

---

### Capability: `wetter`

#### Requirement: Bewölkung
Das System SHALL für Standort und Zeitpunkt die stündliche Bewölkung (`cloud_cover`) aus einer externen Vorhersage beziehen.

##### Scenario: Vorhersagehorizont zu weit
- **WHEN** der Zeitpunkt mehr als `N` Tage (Default 7) in der Zukunft liegt
- **THEN** wird `wetter_confidence = niedrig` gesetzt; der Wetter-Faktor geht abgeschwächt in den Score ein

---

### Capability: `scoring`

#### Requirement: Score-Berechnung
Das System SHALL je Chance einen Score gemäß Formel aus Abschnitt 4 berechnen — als Produkt harter Gates und gewichteter weicher Faktoren.

##### Scenario: Gate verletzt
- **WHEN** ein hartes Gate (LOS, Horizont, Lichtfenster) = 0 ist
- **THEN** ist der Gesamtscore 0 und die Chance erscheint nicht im Ranking

##### Scenario: Tightes Alignment + Vollmond + klare Sicht
- **WHEN** Winkelabstand ≈ 0°, Illumination ≈ 1, Bewölkung ≈ 0, alle Gates = 1
- **THEN** erreicht die Chance einen Score nahe dem Maximum

---

### Capability: `ausblick` (Ranking & Ausgabe)

#### Requirement: 14-Tage-Ausblick
Das System SHALL alle Chancen im 14-Tage-Fenster nach Score absteigend rangieren und im definierten Ausgabeformat liefern.

##### Scenario: Ausgabe einer Chance
- **WHEN** das Ranking erzeugt wird
- **THEN** enthält jeder Eintrag: Datum, Uhrzeit, Standort-GPS, Motivname, Motiv-GPS, Entfernung (km/m), Himmelserscheinung (Typ/Phase/Illumination), Lichtphase (golden/blau), Score, Confidence, Kompass-Peilung, empf. Brennweite (abgeleitet aus `d` und Zielbildanteil)

##### Scenario: Mehrformat-Export
- **WHEN** der Nutzer ein Format wählt
- **THEN** liefert das System die Liste als Markdown-Tabelle, JSON und/oder GeoJSON (Punkte S & M + Sichtachse)

---

## 4. Scoring-Definition

```
Score = GATE_los · GATE_horizont · GATE_lichtfenster · (
          w1 · Alignment      // = clip(1 − Winkelabstand/2°, 0, 1)
        + w2 · Phase           // = f(Illumination); Vollmond-Bonus konfigurierbar
        + w3 · Lichtqualitaet  // golden vs. blau + Nähe zum Sonnenstand-Optimum
        + w4 · Komposition     // = g(d): Mond-zu-Motiv-Größenverhältnis, Kompression
        + w5 · Wetter          // = (1 − cloud_cover) · wetter_confidence
        + w6 · Erreichbarkeit  // 1 wenn erreichbar, sonst Abschlag
        )
```

**Startgewichte (tunebar):** `w1=0.35, w2=0.15, w3=0.15, w4=0.15, w5=0.15, w6=0.05`.

**Gates** sind 0/1 und multiplikativ (eine verdeckte Sichtachse oder ein unsichtbarer Mond macht die Chance wertlos). **Weiche Faktoren** sind auf `[0,1]` normiert.

**Confidence** (separat vom Score) aggregiert: `hoehe_confidence` (Motiv), `dom_aktualitaet` (Erfassungsjahr/Saison), `wetter_confidence`. Ausgabe als `hoch | mittel | niedrig`.

---

## 5. Datenquellen (öffentlich)

### Astronomie
- **skyfield** (Python) mit DE440-Ephemeride: Az/Alt Sonne & Mond, Phase, Illumination, Auf-/Untergang, Refraktion. Alternativen: `suncalc`, `pyephem`.

### Motive & Erreichbarkeit
- **OpenStreetMap** via **Overpass API**: Türme, Windmühlen, Schlösser, Brücken, Schornsteine; Landuse/Access für Erreichbarkeit.
- **Wikidata/Wikipedia**: Bauwerkshöhen als Höhenquelle.

### Höhen & Verschattung
**Brandenburg (Potsdam + Umland, inkl. Berlin-Verflechtungsraum) — LGB / geobasis-bb.de**
- **DGM1** (Digitales Geländemodell, 1 m) — Geländehöhen. Download: `https://data.geobasis-bb.de/geobasis/daten/dgm/`
- **bDOM** (bildbasiertes Oberflächenmodell, aktuell 0,2 m, auch 1 m) — Höhen inkl. Bauwerken **und Vegetation**, bildet den Flugtag-Zustand ab. Download: `https://data.geobasis-bb.de/geobasis/daten/bdom/`
- **LoD2-Gebäudemodelle** (CityGML, Höhengenauigkeit ~1 m) — `https://geobasis-bb.de/lgb/de/geodaten/3d-produkte/`

**Berlin — Geoportal/ODIS & gdi.berlin.de**
- **LoD2-Gebäudemodell** (flächendeckend, Grundrisse nach Liegenschaftskataster) — Lizenz **Datenlizenz Deutschland – Zero – Version 2.0** (frei, auch kommerziell).
- **DGM/DOM** Berlin (offen).
- **3DCityLoader** (`daten.berlin.de/anwendungen/3dcityloader`) — bequemer Export von 3D-Gebäude + Gelände + OSM-Straßen nach DXF/STL/OBJ für schnelle Tests.

**Fallback weiteres Umland:** Copernicus DEM / BKG (DGM/DOM bundesweit).

### Wetter
- **open-meteo** (kostenlose API, `cloud_cover` stündlich, ~14 Tage) oder **DWD**.

---

## 6. Architektur / Pipeline

```
[Motiv-Katalog]  [Astronomie-Engine]
       \               /
        v             v
   (1) Kandidaten-Generierung  ── billig, vektorisiert ──
        • pro Motiv × Zeitschritt im Lichtfenster
        • Az/Alt(C) → Alignment-Test (2°) → Standort-Ableitung (d)
        |
        v
   (2) Günstige Gates (Lichtfenster, geometr. Distanz, Erreichbarkeit grob)
        |  ← nur Bestandene weiter
        v
   (3) Sichtachsen-Analyse  ── teuer ──
        • DGM/DOM/LoD2 laden (gecacht), Ray-Marching S→M + Horizont in az(C)
        • GATE_los, GATE_horizont
        |
        v
   (4) Wetter anreichern (open-meteo)
        |
        v
   (5) Scoring + Confidence
        |
        v
   (6) Ranking → Ausgabe (Markdown / JSON / GeoJSON / Karte)
```

**Perf-Prinzip:** Astronomie + Alignment sind billig → erst alle Kandidatenfenster erzeugen, die teure Verschattungsprüfung nur auf bestandene Kandidaten anwenden. Horizontprofile pro Motiv cachen.

**Tech-Stack:** Python — `skyfield`, `numpy`, `geopandas`/`shapely`, `rasterio`/GDAL (DGM/DOM-Raster), optional `pdal`/`laspy` (LAZ), `requests` (Overpass, open-meteo).

---

## 7. Datenmodell (Schema-Skizze)

```jsonc
// Motiv
{
  "id": "fernsehturm_berlin",
  "name": "Berliner Fernsehturm",
  "kategorie": "turm",
  "lat": 52.5208, "lon": 13.4094,
  "gelaendehoehe_m": 38.0,        // aus DGM
  "bauwerkshoehe_m": 368.0,       // aus Wikidata/LoD2
  "spitzenhoehe_abs_m": 406.0,    // gelaende + bauwerk
  "hoehe_confidence": "hoch",
  "quelle": ["wikidata", "dgm1"]
}

// Chance (Opportunity)
{
  "motiv_id": "fernsehturm_berlin",
  "zeitpunkt": "2026-06-29T21:47:00+02:00",
  "lichtphase": "golden_abend",
  "himmelskoerper": { "typ": "mond", "phase": "voll", "illumination": 0.99 },
  "az_c_deg": 118.4, "alt_c_deg": 4.1,
  "standort": { "lat": 52.49, "lon": 13.46, "h_eye_m": 1.6 },
  "entfernung_m": 5180,
  "peilung_deg": 118.4,
  "winkelabstand_deg": 0.3,
  "empf_brennweite_mm": 400,
  "gates": { "los": 1, "horizont": 1, "lichtfenster": 1 },
  "score": 0.91,
  "confidence": "mittel"
}
```

---

## 8. Annahmen & Grenzen

- **DOM = Flugtag-Zustand:** Vegetation saisonal (belaubt/unbelaubt verschiebt die Sichtachse), Wasserstände variieren. Kachel-Aktualität prüfen und in `dom_aktualitaet`/Confidence führen.
- **Schmale hohe Objekte:** Windräder, Masten und ähnliche werden im DOM nur bedingt abgebildet — **Motivhöhen** daher aus LoD2/Wikidata, nicht aus DOM.
- **DOM vs. LoD2:** DOM hat Vegetation, aber „weiche" Gebäudekanten; LoD2 saubere Gebäude ohne Bäume. → DOM als Verschattungsprimär, LoD2 für Motivhöhen.
- **14-Tage-Wetter** ist jenseits ~5–7 Tagen unzuverlässig → Wetter-Faktor zeitlich abschwächen; Alignment/Sichtbarkeit bleiben deterministisch.
- **Refraktion** beim tiefen Mond (~0,5°) muss eingerechnet werden, sonst Timing-Fehler.
- **Erdkrümmung** bei großen Distanzen `d` in die scheinbare Höhe `α` einrechnen.

---

## 9. Offene Entscheidungen (für Cowork)

1. **Scope Himmelskörper v1:** nur Mond, oder Sonne gleich mit? (Sonne = einfacher, aber „Mond hinter Wahrzeichen" ist das Premium-Motiv.)
2. **Verschattungsquelle v1:** reicht **DOM allein**, oder DOM + LoD2 kombiniert? (DOM allein = schneller startklar.)
3. **`d_min`/`d_max` & Brennweiten-Logik:** an welche Objektive ankoppeln (Leica SL Telebereich, ggf. APO 90–280)? Zielbildanteil des Motivs als Parameter?
4. **Motiv-Umfang v1:** nur kuratierte Leitmotive, oder direkt OSM-Bulk für die Region?
5. **Ausgabe-Primärformat:** Markdown-Liste, GeoJSON+Karte, oder beides?
6. **Datenbeschaffung:** On-the-fly über WMS/WCS vs. einmaliges Kachel-Vorab-Tiling der DGM/DOM-Kacheln (Speicher vs. Latenz).

---

## 10. Implementierungs-Tasks (vertikale Slices)

- [ ] **Slice 1 — Astronomie + Alignment (ohne Verschattung):** ein Leitmotiv, Standort-/Zeitberechnung, Lichtfenster, 2°-Test, Score ohne Gates `los/horizont`. Output: Markdown-Liste. *(Schneller End-to-End-Durchstich.)*
- [ ] **Slice 2 — Motiv-Katalog:** OSM/Overpass + Wikidata + DGM-Fußpunkthöhe; kuratierte Leitmotive.
- [ ] **Slice 3 — Sichtachse:** DGM/DOM laden, Ray-Marching S→M, `GATE_los`; danach Horizont-Gate.
- [ ] **Slice 4 — Wetter + vollständiges Scoring + Confidence.**
- [ ] **Slice 5 — Ranking & Multiformat-Export (JSON/GeoJSON/Karte).**
- [ ] **Slice 6 — Tuning:** Gewichte kalibrieren an realen, nachfotografierten Chancen.

---

*Ende v0.1 — bereit für Dekomposition/Verfeinerung in Cowork.*
