# Spec: On-Demand Ephemeriden-Engine (Sonne / Mond / Milchstraße / Kometen)

> Status: Draft v2 (verfeinert, code-geerdet) · Typ: Architektur-Umbau
> Scope: Berechnungskern + API · Projekt: FotoAlert

---

## 0. Was wurde gegenüber v1 verfeinert

Die Draft-Spec war architektonisch richtig, aber an mehreren Stellen an einer
**Hypothese** statt am echten Code geerdet. Diese Version korrigiert das. Die
wichtigsten Änderungen:

| Punkt | v1 (Annahme) | v2 (Realität laut Code) |
|---|---|---|
| Ephemeride | „Skyfield + DE440" | Code nutzt **`de421.bsp`** (`calculations/astronomy.py`). Ausreichend genau; DE440 ist optionales Upgrade, kein Requirement. |
| Zeithorizont | „14 Tage" | Astronomy-Cache deckt **365 Tage** ab (`precompute.py`, `range(365)`). Feed = 14 Tage. Beides muss die Engine bedienen. |
| Root Cause | „quadratisch mit #Lokationen" | Precompute ist **bereits inkrementell & linear** (nur fehlende Location×Datum-Paare). Echte Schmerzen: (a) `--full` bei `ALGORITHM_VERSION`-Bump, (b) neue Location = 365-Tage-Kaltstart. |
| Minuten-Scan | „Hypothese: pro Minute volle Auswertung" | **Bestätigt** in `find_precise_alignment_times`: `steps = 17*60` (Sonne) bzw. `24*60` (Mond) pro Tag. Bereits numpy-vektorisiert, aber weiterhin 1-Min-Raster. Genau hier greift Rootfinding. |
| Vordergrund-Datenmodell | erfundene Felder (`foreground_azimuth`, `motif`, `eye_height`) | Existiert real in `PhotoLocation`: `observer_lat/lon`, `subject_lat/lon`, `subject_height_m`, `elevation_difference_m`, `observer_floor_height_m`, `ideal_azimuth_range`. Geometrie ist via `calculate_subject_angular_profile` **schon implementiert**. |
| Weltweit-Blocker | „nur Trigonometrie" | Übersehen: Geländehöhen kommen aus **OpenTopoData EUDEM 25m = nur Europa** (`fetch_elevations`). „Weltweit on-demand" scheitert nicht an der Astronomie, sondern am **globalen DEM**. Neuer First-Class-Concern (s. §5.5). |

---

## 1. Kontext & Problem

FotoAlert berechnet astronomische Foto-Chancen (Höhe & Azimut von Sonne, Mond,
Milchstraße, Kometen über einem Motivstandort, gesehen vom Fotografen-Standort)
über einen **Drei-Schichten-Cache** (`precompute.py`):

1. **Geo-Cache** (`elevations.json`) — Geländehöhen via OpenTopoData, inkrementell.
2. **Astronomy-Cache** (`calendar.json`) — 365-Tage-Verläufe + Chancen, inkrementell.
3. **Wetter-Overlay** — zur Laufzeit in `main.py` via Open-Meteo.

**Echte Root Cause (am Code verifiziert):** Nicht der tägliche Inkrement-Lauf
(~1 Tag × N Locations) ist das Problem, sondern zwei Fälle, die einen
**365×N-Volllauf** erzwingen:

- **Version-Bump:** Jede Änderung an `opportunity.py` / `astronomy.py`, die andere
  Ergebnisse liefert, erfordert `ALGORITHM_VERSION`-Bump → `--full` → 365 Tage ×
  alle Locations × alle Objekte neu. Genau das sind die „Stunden".
- **Neue Location:** 365-Tage-Kaltstart nur für diese Location.

**Verstärker:** `find_precise_alignment_times` tastet das Tagesfenster im
**1-Minuten-Raster** ab (`steps = 17*60` Sonne / `24*60` Mond). Auch vektorisiert
sind das ~1.020–1.440 Auswertungen pro Location × Tag × Objekt — der mit Abstand
größte Posten im Volllauf.

**Fakt:** Eine einzelne Horizonttransformation ist O(1). Die Laufzeit ist ein
**Architektur- + Sampling-Problem**, nicht die Astronomie.

---

## 2. Ziele / Nicht-Ziele

### Ziele
- Kein 365×N-Volllauf mehr nötig, auch nicht bei `ALGORITHM_VERSION`-Bump. Eine
  Lokation für 14 **oder** 365 Tage rechnet **on-demand in Sub-Sekunden**.
- Berechnung für **beliebige `lat/lon`** ohne vorab angelegte Lokation —
  innerhalb der Grenzen der Geländehöhen-Verfügbarkeit (§5.5).
- Horizontal skalierbar: stateless Worker, mehr Nutzer = mehr Worker.
- Rückwärtskompatibel: bestehendes `PhotoLocation`-Datenmodell und die
  `AlignmentResult`-Ausgabe bleiben erhalten.

### Nicht-Ziele
- Kein vollständiges Planetarium / keine Sub-Bogensekunden-Astrometrie.
- Keine Satelliten-/ISS-Überflüge (TLE).
- Keine Änderung am Scoring/Chancen-Modell (`opportunity.py`-Logik bleibt;
  nur das *wann/wie oft* gerechnet wird ändert sich).

---

## 3. Kernidee: Die architektonische Umkehr

Drei Hebel, die zusammen das Laufzeitproblem auflösen:

### Hebel 1 — Standortunabhängige vs. standortabhängige Berechnung trennen
Die geozentrische scheinbare Position (α, δ) eines Objekts zu Zeit `t` ist für
jeden Beobachter identisch (Ausnahme: Mond-Parallaxe). → Die teure Objekt-Zeitreihe
**einmal pro Zeitfenster** rechnen, für **alle** Beobachter/Vordergründe
wiederverwenden. Die pro-Lokation-Arbeit ist dann nur Trigonometrie.
*Heute:* `find_precise_alignment_times` rechnet die Body-Position pro Location neu.

### Hebel 2 — Event-Rootfinding statt 1-Minuten-Scan
Statt 1.020–1.440 Samples/Tag: grob abtasten (5–10 min), Vorzeichenwechsel der
Zielbedingung bracketen, dann per **Bisektion/Newton** auf Sekundengenauigkeit
verfeinern. ~20–100× weniger Auswertungen **und** höhere Genauigkeit (kein
Raster-Quantisierungsfehler von bis zu ±30 s wie beim 1-Min-Scan).

### Hebel 3 — On-Demand statt Batch
Weil eine Query Millisekunden kostet, entfällt die Vorberechnung. Kein `--full`,
kein 365×N-Volllauf bei Version-Bumps mehr. Astronomy-Cache wird optional
(reiner Geschwindigkeits-Cache mit TTL, kein Korrektheits-Requirement).

---

## 4. Architektur (zwei Schichten)

```
┌─────────────────────────────────────────────────────────────┐
│  Location Query Engine   (standortabhängig, on-demand, ms)   │
│  ─ Horizonttransformation (alt/az)                           │
│  ─ Vordergrund-Geometrie  →  calculate_subject_angular_profile│
│  ─ Event-Rootfinding (Auf-/Untergang, Transit, Alignment)    │
│  ─ stateless, horizontal skalierbar                          │
└───────────────▲─────────────────────────────────────────────┘
                │ α(t), δ(t), dist(t)  (weltweit identisch)
┌───────────────┴─────────────────────────────────────────────┐
│  Ephemeris Core          (standortunabhängig, global)        │
│  ─ Skyfield + de421 (Chebyshev-Polynome, µs/Auswertung)      │
│  ─ Sonne / Mond / Planeten                                   │
│  ─ Milchstraße: galakt. Zentrum als fester Punkt             │
│  ─ Kometen: Bahnelemente (MPC/Horizons) + Kepler-Solver      │
└──────────────────────────────────────────────────────────────┘
        ▲ benötigt für Vordergrund-Geometrie:
┌───────┴──────────────────────────────────────────────────────┐
│  Elevation Provider      (globaler DEM, der echte Engpass)    │
│  ─ heute: OpenTopoData EUDEM 25m  → NUR Europa                │
│  ─ Ziel weltweit: SRTM / Copernicus GLO-30 + Tile-Cache      │
└──────────────────────────────────────────────────────────────┘
```

Der **Ephemeris Core** ist global geteilt (nicht pro Lokation). Die **Query
Engine** ist reine Mathe. Der **Elevation Provider** ist die einzige Komponente,
die „weltweit on-demand" real ausbremst — sie braucht Netz und ist datenlimitiert.

---

## 5. Komponenten & Datenmodell

### 5.1 Ephemeris Core
- **Sonne / Mond / Planeten:** Skyfield mit **de421** (bestehend). Liefert
  `radec(t) → (α, δ, distance)`. Mond: `distance` zwingend für topozentrische
  Parallaxe. *DE440 nur, falls Genauigkeit unter AK3 fällt — derzeit nicht nötig.*
- **Milchstraße:** Galaktisches Zentrum (Sgr A*, fester Punkt α≈17h45m, δ≈−29°)
  + galaktische Ebene als fester Großkreis; galaktisch→äquatorial→horizontal.
- **Kometen:** Bahnelemente (q, e, i, ω, Ω, T) aus JPL Horizons / MPC. Skyfield
  bringt `skyfield.data.mpc` bereits mit (im Code importiert). Kepler einmalig per
  Newton-Raphson → heliozentrisch → Erdposition (de421) abziehen → geozentrisch →
  α/δ. Elemente periodisch aktualisieren (§5.6).

### 5.2 Location Query Engine (stateless)
Signatur (konzeptionell, an bestehende Funktionen angelehnt):
```
compute(observer{lat, lon, floor_height},
        subject{lat, lon, height_m, width_m, elevation_difference_m},
        window{start, end},
        objects[]) -> list[AlignmentResult]
```
Schritte je Objekt:
1. α(t), δ(t) vom Ephemeris Core (einmal für das Fenster — Hebel 1).
2. Sternzeit (LST) am Beobachter → Stundenwinkel `H = LST − α`.
3. Horizont: `sin h = sinφ·sinδ + cosφ·cosδ·cos H`, dazu Azimut A.
4. Mond: topozentrische Korrektur (Parallaxe bis ~1°) über `distance`.
5. Refraktion: am Horizont +~34′; Auf-/Untergang bei `h = −0,833°`.
6. Vordergrund: `calculate_subject_angular_profile(...)` (bestehend) liefert
   `azimuth_deg` und `angular_altitude_top_deg`.

### 5.3 Lokations-Datenmodell (BESTEHEND — kein Umbau nötig)
`PhotoLocation` (`data/locations.py`) hat bereits alle Vordergrund-Felder:
- `observer_lat`, `observer_lon`
- `subject_lat`, `subject_lon`, `subject_name`, `subject_height_m`
- `elevation_difference_m` (Motiv-Basis minus Fotograf)
- `observer_floor_height_m` (vertikaler Offset, US-62)
- `ideal_azimuth_range`

→ Spec v1 wollte neue Felder erfinden; das ist **nicht** nötig. Die On-Demand-
Engine konsumiert dieselben Felder. Für „beliebige `lat/lon` ohne Lokation"
werden `subject_*`/`elevation_difference_m` zur Query-Zeit übergeben statt
gespeichert.

### 5.4 Wiederverwendbare bestehende Bausteine
Beim Umbau **nicht neu erfinden**, sondern refaktorieren:
- `find_precise_alignment_times` → Sampling-Loop durch Rootfinding ersetzen,
  Body-Position pro Fenster cachen (Hebel 1 + 2). Vektorisierung & 5-Min-Dedup
  bleiben.
- `calculate_subject_angular_profile` → unverändert (Vordergrund-Geometrie).
- `_classify_alignment`, `AlignmentResult` → Ausgabeformat bleibt stabil.
- `find_opportunities` / `find_opportunities_multi_day` → rufen künftig die
  On-Demand-Engine, statt Cache-Einträge zu schreiben.

### 5.5 Elevation Provider (NEU — der eigentliche Weltweit-Engpass)
Heute: `fetch_elevations` nutzt `api.opentopodata.org/v1/eudem25m` → **Europa-only,
25 m**. Für „weltweit on-demand" reicht das nicht. Optionen:

| Option | Abdeckung | Auflösung | Trade-off |
|---|---|---|---|
| OpenTopoData SRTM 30m | ~global (60°N–56°S) | 30 m | gratis, Polar-Lücken, Rate-Limit |
| Copernicus GLO-30 | global | 30 m | beste freie Wahl, ggf. eigenes Hosting |
| EUDEM 25m (heute) | nur Europa | 25 m | Status quo, nicht weltweit |

Anforderung: Elevation hinter ein Interface (`get_elevation(lat, lon)`) mit
**Tile-Cache** (Geländehöhe ändert sich nie → dauerhaft cachebar, kein TTL).
Das ist die einzige Stelle mit echter Netz-/Datenlatenz beim weltweiten Betrieb.

### 5.6 Komet-Elemente (Refresh-Job)
Kleiner periodischer Job (z. B. täglich): aktuelle Bahnelemente sichtbarer
Kometen aus MPC/Horizons ziehen und im Core ablegen. **Nur** Elemente werden
aktualisiert; die Positionsrechnung bleibt on-demand.

---

## 6. Berechnungsverfahren

### 6.1 Event-Rootfinding (ersetzt den 1-Min-Scan in `find_precise_alignment_times`)
Pro Event eine Zielfunktion `g(t)`, deren Nullstelle das Event ist:
- **Auf-/Untergang:** `g(t) = h(t) + 0,833°`
- **Transit (max. Höhe):** `g(t) = dh/dt`
- **Azimut-Alignment über Motiv:** `g(t) = A_obj(t) − A_motif`

Verfahren:
1. Grobes Sampling (5–10 min) über das Fenster (statt 1 min).
2. Vorzeichenwechsel von `g` → Intervall bracketen.
3. Bisektion/Newton auf Sekundengenauigkeit.
4. Skyfield bringt `almanac` (im Code importiert) für Auf-/Untergang & Transite
   bereits mit — bevorzugt nutzen statt Eigenbau.
5. Pro Event ausgeben: Zeit, Azimut, Höhe, **Höhe über Motivspitze**
   `h_obj − angular_altitude_top_deg`.

### 6.2 Alignment-Logik („steht das Objekt über dem Motiv?")
`A_obj ≈ A_motif` **und** `h_obj > α_motif`. Scheinbare Höhe über der Motivspitze
= `h_obj − angular_altitude_top_deg`. (Entspricht heute `altitude_offset_deg`.)

### 6.3 Azimut-Wrap (Edge-Case, heute schon gelöst — beibehalten)
Azimut-Differenz über `np.mod(Δ + 180, 360) − 180` rechnen, damit der 360°/0°-
Sprung korrekt behandelt wird (vorhandenes Muster in `find_precise_alignment_times`).

---

## 7. Skalierung & Caching

| Aspekt | Falsch (heute) | Richtig (Ziel) |
|---|---|---|
| Wann gerechnet | Batch, vorab (365×N bei `--full`) | On-demand, bei Query |
| Was gecacht | Endergebnisse pro Lokation (`calendar.json`) | Nur Geländehöhen (deterministisch, ewig); Ephemeride nicht nötig |
| Version-Bump | erzwingt 365×N-Volllauf | irrelevant — nichts vorberechnet |
| Skalierung | explodiert bei `--full` | linear mit #Requests, stateless |

**Caching-Strategie (nuanciert):**
- **Nicht** Endergebnisse pro Lokation cachen → genau das ist die heutige Falle.
- de421-Auswertung ist deterministisch und µs-schnell → kein Astronomie-Cache nötig.
- **Geländehöhen sehr wohl cachen** — global, ohne TTL (ändern sich nie).
- **Optional:** dünner Response-Cache mit kurzer TTL für „heiße" Spots
  (Key: gerundete `lat/lon` + Motiv + Datum). Reine Optimierung.

---

## 8. Anforderungen & Akzeptanzkriterien

### SHALL-Requirements
1. Höhe & Azimut für Sonne, Mond, Milchstraße und Kometen für beliebige `lat/lon`
   berechnen, ohne vorab angelegte Lokation (Astronomie-Teil; Geländehöhe gemäß
   Elevation-Provider-Abdeckung, §5.5).
2. Die standortunabhängige Objektposition pro Zeitfenster nur **einmal** berechnen
   und über alle Beobachter/Vordergründe wiederverwenden.
3. Events per **Rootfinding** statt 1-Min-Scan ermitteln.
4. Mond-Parallaxe topozentrisch korrigieren.
5. Atmosphärische Refraktion bei Auf-/Untergang berücksichtigen (`h = −0,833°`).
6. Berechnung **stateless** (horizontal skalierbar, kein `--full`-Volllauf).
7. Geländehöhen hinter ein Provider-Interface mit globalem DEM + Tile-Cache legen.

### Messbare Akzeptanzkriterien
- **AK1 — Latenz (14 Tage):** Ein 14-Tage-Plan für eine Lokation (alle Objekte)
  rechnet server-seitig in **< 500 ms** (Ziel; vorher Teil des 365×N-Laufs).
  *Hinweis OF3:* an reale Hardware anpassen; mit Skyfield oft < 100 ms.
- **AK1b — Latenz (365 Tage):** Ein voller 365-Tage-Plan einer Lokation in
  **< 5 s** (ersetzt den heutigen Stunden-Vollllauf für diese Location).
- **AK2 — Weltweit on-demand:** *Given* beliebige `lat/lon` (nicht angelegt),
  *when* Plan angefragt, *then* ohne Vorberechnung geliefert; Geländehöhe via
  Provider (innerhalb DEM-Abdeckung) oder explizit als „elevation unavailable".
- **AK3 — Genauigkeit Position:** Sonne/Mond alt/az innerhalb **1 Bogenminute**
  gegen Referenz (PhotoPills / Skyfield direkt).
- **AK4 — Genauigkeit Zeit:** Auf-/Untergang & Alignment innerhalb **±1 min**;
  Rootfinding muss mindestens so genau sein wie der alte 1-Min-Scan (Ziel: besser,
  da kein Raster-Quantisierungsfehler).
- **AK5 — Kein Volllauf:** Es existiert **kein** Cron/Batch, der pro Lokation
  365-Tage-Verläufe vorberechnet; ein `ALGORITHM_VERSION`-Bump löst **keinen**
  Volllauf aus.
- **AK6 — Regression:** Für alle aktuell angelegten Lokationen stimmt die neue
  Engine mit den bisherigen Batch-Ergebnissen (`calendar.json`) innerhalb AK3/AK4
  überein. → Bestehende Tests `test_astronomy_regression.py` /
  `test_api_regression.py` als Sicherheitsnetz nutzen/erweitern.

---

## 9. Technologie-Wahl

- **Skyfield + de421** (bestehend): Chebyshev-Polynome, µs/Auswertung,
  topozentrisch, getestet. Beibehalten. DE440 nur falls AK3 reißt.
- **Rootfinding:** Skyfield `almanac` (schon importiert) für Standardevents;
  eigener Bisektions-/Newton-Wrapper nur für Azimut-Alignment.
- **Geodäsie:** Haversine (ausreichend) für Distanz & Peilung Fotograf↔Motiv;
  Vincenty falls nötig.
- **Elevation:** Provider-Interface; weltweit Copernicus GLO-30 oder SRTM 30m
  statt EUDEM-Europe-only.
- **Kometen:** Element-Pull via JPL Horizons / MPC (`skyfield.data.mpc`);
  Kepler-Solver Newton-Raphson (3–4 Iterationen).

---

## 10. Migration / Rollout

1. Query Engine als neuen, parallelen Pfad **hinter Feature-Flag** implementieren
   (refaktoriert `find_precise_alignment_times`; alte Funktion bleibt vorerst).
2. Gegen `calendar.json` aller angelegten Lokationen validieren (AK6) via
   `test_astronomy_regression.py`.
3. Bei bestandener Validierung Default auf neue Engine umschalten.
4. `precompute.py` Schicht 2 (`calendar.json`) + zugehörigen Cron **entfernen**.
   Schicht 1 (Geländehöhen) bleibt — wird zum Tile-Cache des Elevation Providers.
   *(Löschung erst nach expliziter Freigabe von Stephan.)*
5. Elevation Provider auf globalen DEM umstellen (separater Schritt; erst nötig,
   wenn echte Nicht-Europa-Lokationen kommen).
6. Optionalen Response-Cache erst bei Lastbedarf.

---

## 11. Offene Fragen / Risiken

- **OF1:** Welche Zeit-Auflösung erwartet das UI? (bestimmt Grob-Sampling-Raster
  im Rootfinding — 5 oder 10 min)
- **OF2:** Wie viele Kometen gleichzeitig tracken? (Refresh-Job-Umfang)
- **OF3:** Latenz-Ziele AK1/AK1b an reale Server-Hardware bestätigen.
- **OF4 (NEU):** Soll „weltweit" sofort umgesetzt werden, oder reicht zunächst
  Europa (EUDEM, Status quo) bei wenigen Nutzern? Der DEM-Wechsel ist der größte
  Einzelaufwand — ggf. eigenes Lane/Ticket.
- **OF5 (NEU):** Verhalten, wenn keine Geländehöhe verfügbar ist (außerhalb DEM-
  Abdeckung): Fallback `elevation_difference_m = 0` mit Warnung, oder Query
  ablehnen?
- **Risiko 1:** Vordergrund-Geometrie ist nur so gut wie `subject_height_m` /
  `elevation_difference_m` — Datenqualität der Lokationen wird zum Genauigkeitsfaktor.
- **Risiko 2 (NEU):** Rootfinding kann nahe beieinanderliegende Doppel-Events
  (z. B. Grazing-Alignment) übersehen, wenn das Grobraster zu weit ist —
  Bracketing-Raster konservativ wählen und gegen den alten 1-Min-Scan gegentesten.
- **Risiko 3:** Server läuft **Python 3.9** (Prod) — keine 3.10+-Syntax
  (`str | None` als Runtime-Annotation etc.), sonst Crash trotz grüner Sandbox-Tests.

---

## 12. Anknüpfpunkte im Code (für die Umsetzung)

| Aufgabe | Datei / Funktion |
|---|---|
| Rootfinding statt 1-Min-Scan | `backend/calculations/astronomy.py` → `find_precise_alignment_times` |
| Body-Position pro Fenster cachen (Hebel 1) | dito + Ephemeris-Core-Wrapper |
| Vordergrund-Geometrie (bleibt) | `astronomy.py` → `calculate_subject_angular_profile` |
| Chancen-Aggregation umstellen | `calculations/opportunity.py` → `find_opportunities[_multi_day]` |
| Volllauf/Cron entfernen | `backend/precompute.py` (Schicht 2, `--full`, `ALGORITHM_VERSION`) |
| Elevation Provider | `precompute.py` → `fetch_elevations` (EUDEM → globaler DEM) |
| Regression absichern | `backend/tests/test_astronomy_regression.py`, `test_api_regression.py` |
