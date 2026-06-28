# FotoAlert – Produkt-Roadmap

> **Zweck:** Lebendes Strategie-Dokument. Hält fest, was bis zum **Go-Live** nötig ist und was
> danach kommt. Dient als **Priorisierungs-Input für das [Backlog](BACKLOG.md)** und deckt
> **Lücken** auf, wo Backlog/Implementierung von der Roadmap abweichen.
>
> **Format:** Zeitstrahl ohne fixe Daten – Kategorien **Now · Next · Later**.
> Stand: vor dem Go-Live (viele Funktionen bereits gebaut).
>
> **Pflege:** Stephan editiert diese Datei fortlaufend. Claude gleicht bei jeder Backlog-Sitzung
> Roadmap ↔ Backlog ab (siehe [Pflege & Abgleich](#-pflege--abgleich) unten).

**Letzter Abgleich mit Backlog:** 2026-06-20

---

## Legende

| Symbol | Bedeutung |
|--------|-----------|
| ✅ | Implementiert & erfüllt die Roadmap-Anforderung |
| 🟡 | Teilweise vorhanden – Rest offen (Detail in Spalte „Lücke / Rest") |
| 🔴 | Nicht vorhanden / **Launch-Blocker** |
| ❓ | Offene strategische Frage (Entscheidung durch Stephan) |
| `US-XX` / `BUG-XX` / `TASK-XX` | Verknüpftes Backlog-Ticket |

---

## Begriffe (verbindliche Definitionen)

- **Location** = Standort des Fotografen **und** das Motiv (zwei Koordinaten je Eintrag).
- **Ereignis** = ein astronomisches/atmosphärisches Vorkommnis: Mond-Alignment, Sonnen-Alignment,
  Milchstraße, Komet, Meteoritenschauer (Next: + Goldene Wolken, Himmelsröte).
- **Chance** = konkreter Zeitpunkt, zu dem an einer Location ein Ereignis stattfindet.
- **Regel:** nur **eine Chance** pro Location, Tag und Ereignis (in 14-Tage-Vorschau & 365-Tage-Kalender).
- **Alignment-Kriterium:** Mond-/Sonnen-Alignment mit ≤ **2° Abweichung** von Azimut **und**
  Objekthöhe im Bildausschnitt, **nur** zur Goldenen und Blauen Stunde.

---

## 🟢 NOW — Go-Live (MVP für offiziellen Launch)

> Ziel: vollständiges, host-kuratiertes Launch-Erlebnis für Berlin, Potsdam & Umgebung.
> Der Großteil ist gebaut – kritisch sind drei serverseitige Lücken (unten **🔴**).

### Daten & Feeds

| Roadmap-Punkt | Status | Tickets | Lücke / Rest |
|---|---|---|---|
| Verifizierte, host-kuratierte Standorte (Berlin/Potsdam/Umgebung) | ✅ | 55 Spots (Locations-DB), US-12 | Kuratierung laufend; Host-Verifikations-Loop hängt an US-68 |
| 14-Tage-Vorschau (rollend, aufsteigend, nach Tag gruppiert; Location · Wahrscheinlichkeit · Ereignis · Wetter) | ✅ | US-01, US-02 | — |
| 365-Tage-Kalender (rollend, aufsteigend, nach Tag gruppiert; gleiche Felder) | ✅ | US-13, TASK-15 | — |
| Nur **eine** Chance pro Location/Tag/Ereignis | ✅ | US-40, US-36, Feed-Dedup | — |
| Mond-/Sonnen-Alignment mit 2°-Zone, nur Goldene/Blaue Stunde | ✅ | US-57, US-36, US-81 | Azimut/Höhe **relativ zur Motivspitze** verfeinert offen → US-67 (🟡) |
| Wetter pro Chance, hochfrequente Aktualisierung ab T-3 | ✅ | US-02, US-42 | Rolling-Forecast-Eskalation (T-3 alle 6h, T-0 stündl.) Teil von US-34 – prüfen ob vollständig aktiv |

### Ansichten & Navigation

| Roadmap-Punkt | Status | Tickets | Lücke / Rest |
|---|---|---|---|
| Übersicht aller kuratierten Locations | ✅ | US-22 | — |
| Kartenansicht: Standard / Nacht / Satellit, zentriert auf User-Standort | ✅ | Layer-Toggle (s. BUG-24), US-69 | ⚠️ **US-46 steht im Backlog noch als offen**, obwohl Layer-Toggle existiert → Status abgleichen/schließen |
| Link von der Chance → Locationdetails | ✅ | US-61 | — |
| Locationdetails: Infos · Ereignisse · Perspektive · Wetter · Maps/StreetView (Fotograf) · Maps (Motiv) · nächste Ereignisse · Entfernung · Niveauunterschied · Motivhöhe | 🟡 | US-22, US-14, US-31, US-41, US-62, US-58 | **Motivhöhe (Bauwerkshöhe)** als eigenes Datenfeld prüfen – US-62 deckte Fotografen-Höhe ab; ggf. Ticket nötig |
| Filter nach allen Detail-Informationen | ✅ | US-32 (6 Gruppen) | Kategorien-Filter als Standardliste offen → US-76 (🟡, optional für Launch) |

### Community, Login & Host-Funktionen

| Roadmap-Punkt | Status | Tickets | Lücke / Rest |
|---|---|---|---|
| Host- & User-Login (alle User ein Passwort) | ✅ | US-66 | — |
| **Verifikation (pos./neg.) gespeichert & sichtbar für ALLE** | 🔴 | US-23, US-30 (lokal) · **BUG-26** | Liegt nur in `localStorage` (pro Gerät). Für „sichtbar für alle" fehlt **serverseitige Persistenz** → **Launch-Blocker** |
| **Bewertung 1–5 Sterne, Summe + Ø sichtbar für ALLE** | 🔴 | US-24 (lokal) | Ebenfalls nur `localStorage`. Aggregation (Summe/Ø) serverseitig + geteilt fehlt → **Launch-Blocker** (ggf. neues Ticket) |
| Neue Locations vorschlagen → Host verifiziert | 🔴 | **US-68** | Host-Approval-Workflow noch offen → Vorschlags-Loop fehlt |
| Host-only: Locationdetails bearbeiten | ✅ | US-60, US-56, BUG-22 (PATCH + Auth) | — |
| Host-only: Locations hinzufügen & löschen | 🟡 | US-56 (add), US-77 (backend add), US-68 (delete/approval) | Löschen/Hinzufügen über Host-Workflow vereinheitlichen |

> **🚨 Launch-Blocker (Now, kritischer Pfad):**
> 1. **BUG-26** – Verifikationen serverseitig persistieren (statt `localStorage`).
> 2. **Geteilte Bewertungen** – Sterne serverseitig speichern + aggregieren (eigenes Ticket nötig).
> 3. **US-68** – Host-Approval-Workflow (Vorschläge, Löschungen).
>
> Diese drei machen den Unterschied zwischen „funktioniert auf meinem Gerät" und „host-kuratierte,
> für alle sichtbare App". Alles andere im Now ist im Wesentlichen erledigt.

---

## 🔵 NEXT — 2. Release (nach Go-Live)

| Roadmap-Punkt | Status | Tickets | Anmerkung |
|---|---|---|---|
| User-Login mit E-Mail & Passwort, DSGVO-konforme Speicherung & Löschung | ❓ / 🔴 | *(kein Ticket)* | **Offene Frage:** Wird das durch App-Store-Veröffentlichung + Apple-ID-Login obsolet? Entscheidung vor Aufwand. Ticket anlegen sobald geklärt |
| DSGVO-Datenspeicherungsauskunft | ❓ / 🔴 | *(kein Ticket)* | Gleiche offene Frage (Apple-ID/App-Store). Abhängig von obigem |
| Locations hinzufügen (User) | 🟡 | US-77 | Backend-Add + Merge mit Nutzerdaten |
| Favoriten: speichern · löschen · filtern · suchen · sortieren | 🟡 | US-17, US-06 | — |
| Goldene Wolken & Himmelsröte als Ereignisse (Chancen + Locationdetails ergänzt) | 🟡 | US-07, US-82 | Scoring-Grundlage in US-82 (Sun-Score v2) |
| Ideale Richtung für Goldene Wolken / Himmelsröte auf Karte | 🔴 | US-07, US-85 | — |
| Sichtachse zum Ereignis auf Karte in Chancendetails sichtbar | 🟡 | US-85, US-09 | FOV-Trichter (US-85) + Hinderniserkennung (US-09) |

> **Strategische Klärung zuerst:** Die zwei DSGVO/Login-Punkte (❓) entscheiden über erheblichen
> Aufwand. Wenn App-Store + Apple-ID-Login die Anforderung abdecken, entfällt eigene
> E-Mail/Passwort-Verwaltung samt DSGVO-Auskunfts-Mechanik.

---

## ⚪ LATER — Ausblick / Vision (noch nicht eingeplant)

> Gespeist aus offenen Backlog-Tickets. Reihenfolge offen; bei Reifung nach **Next** ziehen.

**Weitere Ereignistypen & Astronomie**
TASK-01 Kometen · TASK-02 Sonnenfinsternisse · TASK-03 Feuerwerk · TASK-09 Bortle-Karte ·
TASK-10 Astronomisches Twilight (Milchstraße) · US-10 Polarlichter/Aurora · US-79 Mondauf-/untergang ·
US-49 Historische Alignments

**Karte, Sicht & Navigation**
US-64 Live-Astro-Visualisierung (PhotoPills-like) · US-72 Wetterkarte · US-73 Anreise zum Standort ·
US-51 Navigation & Fahrtzeit · US-52 Smarte Abfahrts-Erinnerung · US-87 Vollbild-Karte zum Pin-Setzen ·
US-08 GPX-Export · US-11 Bauarbeiten & Sperrungen

**Datenqualität & Host-Tools**
US-76 Location-Kategorien · US-78 Duplikatserkennung · US-25 Duplikate (Host-Tool) ·
US-84 Host-Passwortänderung in der App · US-75 User/Backend-Datensync · US-33 Locationscout Import-Mgmt

**Plattform & Wachstum**
US-26 Sprachumschaltung DE/EN · US-21 App-Beschreibung & Onboarding · US-43 Apple Watch ·
US-44 Push-Vorlaufzeit · US-45 Wochenvorschau-Widget · US-50 Analytics (Matomo) ·
US-47 KI-Kompositions-Vorschläge · US-48 Community-Locations · US-04 Kalender-Integration Fotowalks

**Kleinere Verbesserungen (jederzeit ziehbar)**
US-88 Nicht-linearer Brennweiten-Slider · BUG-21 Komma-Eingabe iOS · US-83 Scout-Detail „Als Location speichern"

---

## 🔎 Gap-Analyse (Roadmap ↔ Backlog)

**Wo die Implementierung hinter der Roadmap zurückliegt (Now):**

1. **Geteilte, persistente Community-Daten fehlen.** Verifikationen (BUG-26) und Bewertungen (US-24)
   existieren nur lokal pro Gerät. Die Go-Live-Anforderung „gespeichert & **sichtbar für alle**"
   ist damit *nicht* erfüllt – obwohl die UI fertig ist. Höchste Priorität.
2. **Host-Approval-Loop fehlt (US-68).** Ohne ihn gibt es keinen sauberen „Vorschlagen → verifizieren"-Pfad.
3. **Motivhöhe (Bauwerkshöhe)** als eigenes Detailfeld nicht eindeutig abgedeckt – prüfen, ggf. Ticket.

**Status-Inkonsistenzen, die bereinigt werden sollten:**

- **US-46 (Karten-Ansichtsmodi)** steht offen, obwohl Standard/Nacht/Satellit-Layer-Toggle bereits
  funktioniert (siehe BUG-24-AK). → Ticket schließen oder Rest-Scope präzisieren.

**Fehlende Tickets (Roadmap-Punkte ohne Backlog-Eintrag):**

- Serverseitige **Bewertungs-Aggregation** (Summe/Ø, geteilt) — Now.
- **DSGVO/E-Mail-Login** — Next, erst nach Klärung der Apple-ID-Frage.

**Über die Roadmap hinaus implementiert (kein Roadmap-Konflikt, nur zur Kenntnis):**
Score-Erklärungen (US-55), Kompositions-Analyse (US-37), aufklappbare Sektionen (US-59),
Kamera-Sichtfeld/FOV-Kegel (US-58) — bereits gebaut, stärkt das Now.

---

## 🧭 Empfohlene Sequenzierung bis Go-Live

1. **US-46-Status klären** (schnell, räumt Inkonsistenz auf).
2. **BUG-26** – Verifikationen serverseitig persistieren.
3. **Bewertungen serverseitig** (neues Ticket, baut auf gleicher Persistenz-Schicht wie BUG-26 auf → gemeinsam denken).
4. **US-68** – Host-Approval-Workflow (Vorschläge/Löschungen).
5. **Motivhöhe** prüfen, ggf. nachziehen.
6. *(optional vor Launch)* US-67 Azimut/Höhe-Verfeinerung, US-76 Kategorien-Filter.

→ Danach Go-Live. Erst dann **Next** öffnen, beginnend mit der DSGVO/Login-Entscheidung (❓).

---

## 🔄 Pflege & Abgleich

- **Quelle der Priorisierung:** Diese Roadmap. Das [Pipeline-Board in BACKLOG.md](BACKLOG.md) ordnet
  Tickets entsprechend ein (Now-Blocker → zuerst `Ready for Analysis`).
- **Bei jeder Backlog-Sitzung** gleicht Claude ab:
  1. Erfüllt ein neu erledigtes Ticket einen Roadmap-Punkt? → Status hier auf ✅ setzen.
  2. Gibt es Roadmap-Punkte ohne Ticket? → als Lücke markieren / Ticket vorschlagen.
  3. Gibt es Tickets, die keinem Roadmap-Punkt dienen? → Now/Next/Later zuordnen oder hinterfragen.
- **„Letzter Abgleich"-Datum oben** nach jedem Durchlauf aktualisieren.
- Stephan entscheidet Kategorien-Verschiebungen (Later → Next → Now) und die ❓-Fragen.
