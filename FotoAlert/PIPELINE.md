# FotoAlert — Autonome, lernende CI/CD-Pipeline

> Strategie- und Architekturdokument für den Umbau des FotoAlert-Entwicklungsprozesses
> von einer manuell angestoßenen Skill-Kette hin zu einer teilautonomen, lernenden
> Pipeline mit Product-Management- und Dev-Agenten.
>
> **Status:** Konzept · **Erstellt:** 2026-06-20 · **Owner:** Stephan
> **Verwandt:** `BACKLOG.md` (🚦 Pipeline-Steuerung), Skills `book-of-work`, `fotoalert-*`, `retrospective`

---

## 1. Leitprinzip

Alles zwischen zwei Kontroll-Gates läuft autonom; die Gates bleiben bei Stephan.
Die Pipeline soll mit jedem Ticket besser werden — durch einen wachsenden Regressionstest-Korpus
und eine Pre-Mortem-Wissensbasis, die aus echten Erfahrungen gespeist werden.

**Stephans drei Gates:**

1. **Intake-Gate** — welche Tickets in `Ready for Analysis` gehen (inkl. explizitem Ausschluss).
2. **Implementierungsweg-Gate** — Freigabe der empfohlenen Option (für Low-Risk optional automatisierbar).
3. **Release-Gate** — jeder Deploy wird manuell freigegeben (Git läuft per Regel nur am Mac, nie in der Sandbox).

Alles dazwischen — Dedup, Sequenzierung, Spec, Pre-Mortem, Code, Vollsystem-Test, Auto-Weiterlauf — ist autonom.

---

## 2. Ist-Zustand

### 2.1 Globale (projektunabhängige) Bausteine

| Typ | Bausteine |
|-----|-----------|
| Prozess-Skills | `book-of-work` (Ticketing), `retrospective` (Lernen), `skill-creator`, `schedule`, `consolidate-memory` |
| Output-Skills | `docx`, `pptx`, `xlsx`, `pdf` |
| Subagents | `Plan` (Architektur), `Explore` (Code-Suche), `general-purpose`, `claude-code-guide` |
| Infrastruktur | Memory-Dateien, Scheduled Tasks, Artifacts (Kanban), MCP-Registry |

### 2.2 Projektbezogene (FotoAlert) Skills

| Skill | Rolle |
|-------|-------|
| `fotoalert-analyze` | Example Mapping → messbare Akzeptanzkriterien → Architektur-Spec ins Ticket |
| `fotoalert-impl` | Code-Patterns (Sheets/Overlays, Location-Routine, Edit-Regeln) |
| `fotoalert-localdev` | Lokaler Dev-Zyklus (Server, Service Worker, 2-Terminal-Modell) |
| `fotoalert-test` | curl/Browser-Testschritte aus Akzeptanzkriterien |
| `fotoalert-release` | Deploy via Mac-Terminal + GitHub Actions + Health-Check |
| (`fotowalk-pptx`) | gehört zum FotoCommunity-Projekt, nicht zur Dev-Pipeline |

### 2.3 Heutige Kette (linear, jeder Übergang manuell)

```
Idee → book-of-work (Ticket) → [Freigabe] → fotoalert-analyze (Spec) → [Freigabe]
     → fotoalert-impl (Code) → fotoalert-localdev + fotoalert-test (Stephan testet manuell)
     → fotoalert-release (Stephan committet am Mac) → retrospective (Lernen)
```

### 2.4 Automatisierungs-Lücken

1. **Kein Backlog-Management-Layer** — Tickets entstehen einzeln auf Zuruf; Dedup/Merge/Split/Sequenzierung nur auf explizite Anweisung.
2. **Kein Intake-Gate** — gelöst durch die neue Pipeline-Steuerung in `BACKLOG.md` (siehe §4.1).
3. **Testing vollständig manuell** — Stephan führt curl in zwei Terminals aus; getestet wird nur das geänderte Feature, nie Regressionen im Gesamtsystem. **Größter Blocker.**
4. **Kein Pre-Mortem** — Risiken werden erst grob in `analyze` benannt, nicht systematisch vorab durchgespielt und in Tests übersetzt.
5. **Kein Auto-Weiterlauf** — nach `Done` endet die Kette.
6. **Lernen ist passiv** — `retrospective` verbessert Skills, speist aber keinen Regressionstest-Korpus oder eine Pre-Mortem-Wissensbasis.

---

## 3. Zielbild: drei Agenten-Schichten + Orchestrator

```
                         🚦 INTAKE-GATE (Stephan)
                                  │
   roh: Feature/Bug-Notiz ──▶ [A] PM-Layer ──▶ Ready for Analysis
                                  │
                          [B] Dev-Layer  ◀── Orchestrator zieht oberstes Ready-for-Dev-Ticket
                       Pre-Mortem → Analyse(Optionen) → [Weg-Gate] → Impl
                                  │
                          [C] Test-Harness (Sandbox + CI)
                       Vollsystem-Regression gegen ALLE Akzeptanzkriterien
                                  │
                           🚦 RELEASE-GATE (Stephan) ──▶ Deploy ──▶ Done
                                  │
                          retrospective ──▶ speist Regressionskorpus + Pre-Mortem-Basis
                                  │
                          Auto-Weiterlauf: nächstes Ticket (außer Release nötig)
```

### 3.1 Schicht A — Product-Management-Agenten (neue Skills)

**`fotoalert-intake`** — verwandelt rohe Feature-/Bug-Notizen in Tickets und:
- gleicht automatisch gegen das bestehende Backlog ab (Dubletten, Überschneidungen),
- schlägt **Merge/Split** vor (Umbau nur nach Freigabe — vgl. Memory `feedback_ticket_beziehungsanalyse`),
- **sequenziert** nach Abhängigkeit + Priorität,
- legt das Ticket in `Inbox` an (nie direkt in `Ready for Analysis`).

**`fotoalert-groom`** — läuft als Scheduled Task:
- re-priorisiert das Backlog,
- schlägt neue Features vor,
- identifiziert Bugs aus Server-Logs / Health-Checks / Retrospektiven,
- meldet Vorschläge zur Sichtung — entscheidet nie selbst über das Intake-Gate.

### 3.2 Schicht B — Dev-Agenten (Erweiterung bestehender Skills)

**Pre-Mortem-Schritt (neu, vor der Implementierung):**
> „Angenommen, dieses Ticket ist live und hat etwas kaputt gemacht — was war es?"
Die Erkenntnisse fließen in Implementierungsplan **und** Testfälle. Speist sich aus der
Pre-Mortem-Wissensbasis (§3.4) und schreibt neue Erkenntnisse zurück.

**`fotoalert-analyze` erweitert:** generiert **mehrere Implementierungsoptionen**, bewertet
Trade-offs, **empfiehlt eine** und setzt nach Freigabe genau die um.

**`fotoalert-impl`:** implementiert den empfohlenen Weg (bestehende Patterns bleiben gültig).

### 3.3 Schicht C — Automatisiertes Test-Harness (kritischer Enabler)

Statt Stephan curl-Schritte zu geben, **führt der Agent die Tests selbst aus**:
- In der Sandbox läuft eine eigene Backend-Instanz (Python/uvicorn ist vorhanden).
- **Jedes Akzeptanzkriterium wird zu einem permanenten `pytest`-Fall.**
- Getestet wird das **Gesamtsystem** — die Akzeptanzkriterien *aller* bisherigen Tickets
  als Regressionssuite, nicht nur das neue Feature. Damit werden „Auswirkungen auf andere
  Funktionalität" überhaupt erst prüfbar.
- Dieselbe `pytest`-Suite läuft als **CI-Stage in GitHub Actions vor dem Deploy** — ein roter
  Test blockt den Release.

### 3.4 Lern-Loop (eigene Lane nach Done + Lern-Agent)

Damit Lernen nicht vergessen wird, bekommt die Pipeline eine **eigene Lane `🔁 Retro / Lernen`
hinter Done**. Erreicht ein Ticket `Done`, schiebt der Orchestrator es automatisch dorthin und
startet den **Lern-Subagenten** (`retrospective`) — ohne Ansage, auch bei kurzer Bestätigung.

**Was der Lern-Subagent erzeugt — und was davon automatisch vs. freigabepflichtig ist:**

| Erkenntnis-Typ | Ziel | Automatik |
|----------------|------|-----------|
| Fehlerursachen / „nicht nochmal" | Pre-Mortem-Wissensbasis (Memory) | **auto** geschrieben |
| Neue Akzeptanztests | Regressionstest-Bestand | **auto** ergänzt |
| Projektfakten / Kontext | Memory-Dateien | **auto** geschrieben |
| **Skill-/Agent-Änderungen** | `fotoalert-*` / Orchestrator | **vorbereitet, NICHT auto-installiert** |

**Wichtige Grenze — Agenten ändern ihre eigenen Instruktionen nicht unbemerkt:**
Skill-/Agent-Anpassungen werden vom Lern-Subagenten als fertiges `.skill`-Paket + Änderungs-Diff
**vorbereitet** und dir vorgelegt; aktiv werden sie erst durch dein „Save skill". Das ist hier
ohnehin technisch erzwungen (installierte Skills sind read-only) — und es ist die richtige
Sicherung: ein Agent, der sich selbst umschreibt, braucht ein menschliches Gate. Memory-Einträge
und Regressionstests dagegen fließen sofort ein, weil sie additiv und risikoarm sind.

So speist der Loop drei wachsende Korpora: **Regressionstests**, **Pre-Mortem-Wissensbasis**
und ein **Backlog vorgeschlagener Skill-/Agent-Verbesserungen** zur Freigabe.

### 3.5 Orchestrator (Scheduled Task + Steuer-Skill)

Der Orchestrator ist der dünne Steuer-Thread, der Tickets durch die Lanes fährt. Er hält
**nur** Ticket-ID, Lane-Status und die kompakten Phasen-Ergebnisse — keine vollständigen
Datei-Inhalte (siehe §3.6).

**Lane-getriebene Trigger:**

| Auslöser | Aktion des Orchestrators |
|----------|--------------------------|
| Ticket landet in **`Ready for Analysis`** | startet **automatisch** den Analyse-Subagenten (Pre-Mortem + Example Mapping + Spec) und legt das Ergebnis zur Freigabe vor → danach `In Analysis` |
| Spec freigegeben (Weg-Gate) | Ticket → `Ready for Dev` |
| Ticket in **`Ready for Dev`** | zieht das oberste, fährt Impl → Vollsystem-Test → `In Test` |
| Test grün + (ggf.) Release freigegeben | Ticket → `Done` |
| `Done` erreicht | schiebt das Ticket nach **`🔁 Retro / Lernen`** und startet **automatisch** den Lern-Subagenten (§3.4) |
| Retro abgeschlossen | **startet direkt das nächste Ticket — außer ein Release ist nötig**, dann Stopp am Release-Gate |

So bedeutet „Karte nach Ready for Analysis schieben" künftig konkret: der Analyse-Subagent
beginnt sofort mit Pre-Mortem + Spec. Die **Implementierung** startet aber erst hinter deinem
Weg-Gate (`Ready for Dev`) — das Gate-Schieben löst nie direkt Code-Änderungen aus.

### 3.6 Agenten-Orchestrierung & Kontext-Strategie

Damit das Hauptkontextfenster klein und relevant bleibt, läuft **keine** Phase inline im
Orchestrator-Thread. Stattdessen delegiert der Orchestrator jede Phase an einen **eigenen
Subagenten mit isoliertem Kontext** (Task-Tool) und erhält nur ein **kompaktes Ergebnis** zurück.

**Prinzip: dünner Orchestrator, fette Subagenten.**

| Phase | Subagent | Liest (isoliert) | Gibt zurück (kompakt) |
|-------|----------|------------------|------------------------|
| Recherche/Codesuche | `Explore` | Auszüge statt ganzer Dateien | Fundstellen + Pfade |
| Architektur/Optionen | `Plan` | relevante Module | Optionen + Empfehlung |
| Analyse + Pre-Mortem | Analyse-Subagent | nur das Ticket + betroffene Dateien | Spec-Diff + Akzeptanzkriterien |
| Implementierung | Impl-Subagent | nur die zu ändernden Dateien | Liste geänderter Dateien + Notizen |
| Test | Test-Subagent | Akzeptanzkriterien + Testsuite | Testreport (pass/fail) |
| Verifikation | **separater** Verifikations-Subagent | Diff + Akzeptanzkriterien | Urteil + gefundene Risiken |
| Retro / Lernen | Lern-Subagent (`retrospective`) | Phasen-Ergebnisse + Diff | Memory-/Test-Updates + Skill-Vorschläge |

**Warum das wichtig ist:**
- Lange Lesevorgänge (2187-Zeilen-`BACKLOG.md`, >2000-Zeilen-`index.html`, 97-MB-Caches)
  belasten nur den jeweiligen Subagenten, nie den Orchestrator.
- Der Orchestrator kann beliebig viele Tickets nacheinander fahren, ohne dass sein Kontext
  vollläuft — Voraussetzung für den Auto-Weiterlauf (§3.5).
- **Verifikation in einem separaten Subagenten** vermeidet den Bias, dass derselbe Kontext,
  der den Code geschrieben hat, ihn auch „grün" prüft.
- Jeder Subagent bekommt einen **scharf umrissenen Auftrag** und gibt strukturierte Ergebnisse
  zurück — das ist zugleich die Schnittstelle, an der der Lern-Loop (§3.4) ansetzt.

**Faustregel:** Was ein Subagent gelesen hat, bleibt in seinem Kontext; in den Orchestrator
fließt nur das Ergebnis. Skills definieren *wie* eine Phase abläuft, Subagenten kapseln *wo*
sie abläuft.

---

## 4. Governance & Steuerung

### 4.1 Pipeline-Lanes (umgesetzt in `BACKLOG.md`)

```
Inbox → [🚦 Ready for Analysis] → In Analysis → Ready for Dev
      → In Progress → In Test → [🚦 Release] → Done → 🔁 Retro / Lernen     ·  🚫 Excluded
```

`🔁 Retro / Lernen` ist eine transiente Lane: der Lern-Subagent läuft automatisch (§3.4),
danach verlässt das Ticket die Pipeline und der Orchestrator startet das nächste.

Das **🚦 Pipeline-Steuerung-Board** oben in `BACKLOG.md` ist die maßgebliche Quelle:
Agenten nehmen ausschließlich Tickets auf, deren ID unter **Ready for Analysis** oder
einer nachgelagerten Lane steht. `Inbox` wird nie automatisch angefasst; `🚫 Excluded`
hat Vorrang vor allem.

### 4.2 Stephans Kontroll-Gates

| Gate | Entscheidung | Was es auslöst |
|------|--------------|----------------|
| **Ready for Analysis** | Welche Tickets die Agenten aufnehmen — inkl. explizitem Ausschluss | **Auto-Start** des Analyse-Subagenten (Pre-Mortem + Spec) |
| **Implementierungsweg** | Freigabe der empfohlenen Option (Low-Risk optional automatisierbar) | Ticket → `Ready for Dev`, Impl beginnt |
| **Release** | Jeder Deploy manuell — Git nur am Mac, nie in der Sandbox | Deploy + `Done` |

---

## 5. Kritischer technischer Knackpunkt

„Vollautomatisches Testen" steht und fällt damit, dass die **Sandbox das Backend selbst
hochfahren und testen** kann. Heute läuft es auf Stephans Mac — deshalb manuell. Der Umbau:

- Backend in der Sandbox startbar machen (uvicorn gegen `localhost` in-Sandbox).
- Akzeptanzkriterien → `pytest`-Fälle (wachsende Suite).
- Gleiche Suite als CI-Stage in GitHub Actions **vor** den Deploy hängen.

Die bestehenden Schutzregeln bleiben unangetastet: **kein Git in der Sandbox**, **kein curl
für externe URLs in der Sandbox** (stattdessen `web_fetch`), **keine Löschung ohne Freigabe**.

---

## 6. Roadmap

| # | Schritt | Ergebnis | Status |
|---|---------|----------|--------|
| 1 | **Backlog-Lanes + Gate** | Intake-Gate scharf; `BACKLOG.md` mit Steuer-Board | ✅ umgesetzt 2026-06-20 |
| 2 | **`fotoalert-intake`** | PM-Layer: Dedup/Merge/Split/Sequenzierung | ✅ installiert |
| 3 | **Sandbox-Test-Harness + pytest-aus-AKs** | Vollsystem-Regression, größter Hebel | ✅ Offline-Regression (10) + API-Regression (BUG-22 u. a.) grün im Sandbox; App-Startup via `FOTOALERT_NO_BACKGROUND` test-sicher (kein Scheduler/Precompute/Netzwerk/Backup) — 16 Tests in `backend/tests/` |
| 4 | **Pre-Mortem-Schritt + Mehr-Optionen in `analyze`** | risikoinformierte Pläne & Tests | 🟡 gebaut — aktualisiertes `fotoalert-analyze.skill` zur Installation |
| 5 | **Orchestrator + Subagent-Architektur** | Manuell startbar, dünner Orchestrator mit isolierten Phasen-Subagenten (§3.5/§3.6), respektiert alle Gates | ✅ installiert (Test-Phase nutzt jetzt das Harness aus Schritt 3) |
| 6 | **Lern-Loop + Retro-Lane koppeln** | Auto-Retro hinter Done; Memory/Tests auto, Skill-/Agent-Änderungen vorbereitet zur Freigabe (§3.4) | offen |

> Schritt 1 ist der kleinste Hebel mit sofortiger Wirkung. Schritt 3 ist der größte
> Enabler Richtung Vollautomatik — ohne ihn bleibt Testing der Engpass.

---

## 7. Entscheidungen & offene Punkte

**Entschieden (2026-06-20):**
- **Gate-Trigger:** Verschieben nach `Ready for Analysis` startet **automatisch** die Analyse
  (Pre-Mortem + Spec). Implementierung bleibt hinter dem Weg-Gate. *(umgesetzt im Konzept §3.5)*
- **Kontext-Strategie:** dünner Orchestrator + isolierte Phasen-Subagenten *(§3.6)*.

**Noch offen:**
- **Weg-Gate automatisieren?** Soll der empfohlene Implementierungsweg bei klar Low-Risk-Tickets
  automatisch ohne Freigabe umgesetzt werden, oder immer Freigabe?
- **Groom-Frequenz?** Wie oft soll `fotoalert-groom` laufen (täglich, wöchentlich)?
- **Skill-Updates:** Schritte 2–6 erfordern teils Änderungen an installierten Skills — diese
  werden über `skill-creator` als `.skill`-Paket gebaut und von Stephan via „Save skill" installiert.
