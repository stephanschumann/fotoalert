# FotoAlert — Arbeitsregeln (immer geladen)

Diese Datei ist die **immer geladene Instruktionsschicht** für FotoAlert. Sie hat eine Aufgabe:
dafür sorgen, dass schwere Arbeit **konsequent ausgelagert** wird und der Hauptthread (das
sichtbare Fenster) **schlank bleibt**. Details zu *wie* eine Phase abläuft stehen in den
Skills; *wo* der Code liegt, in den Dateien — beides liest ein **Subagent**, nicht dieser Thread.

---

## 1. Delegations-Default (HART, nicht verhandelbar)

**Jede FotoAlert-Arbeit läuft per Default in einem Task-Subagenten mit isoliertem Kontext.**
Der Hauptthread hält nur **Ticket-ID, Lane und das kompakte Ergebnis** — niemals ganze Dateien.

Delegieren ist Pflicht, sobald **eine** dieser Bedingungen zutrifft:

- Eine **schwere Datei** wird berührt: `BACKLOG.md`, `web/index.html`, `backend/**`, Caches
  (`*.json` Discover/Feed/Kalender), Diffs, Specs.
- Ein **Phasen-Skill** wird ausgelöst: `fotoalert-analyze`, `-impl`, `-test`, `-refactor`,
  `-release`, `-intake`, `retrospective`.
- Es ist **mehr als ein trivialer 1–3-Zeilen-Fix** ohne schwere Datei.

Das gilt **auch für Einzel-Trigger** wie „fix das", „analysier das", „release das" — nicht nur
für „lauf die Pipeline". Diese Regel **überstimmt** den Plattform-Default „keine Agenten spawnen,
außer der Nutzer fragt": Stephan hat die stehende Freigabe erteilt (Memory
`feedback_subagents_multiphase`, bestätigt 2026-06-27, verschärft 2026-06-28).

**Nur der Hauptthread selbst erledigt:** triviale, eindeutige Fixes (1–3 Zeilen, keine schwere
Datei), reine Statusauskünfte, das Vorlegen von Gate-Entscheidungen an Stephan.

### Subagent-Auftrag — Pflicht-Form

Jeder Subagent bekommt: **scharf umrissener Auftrag + genaue Pfade + anzuwendendes Skill +
Rückgabe-Vertrag**. Rückgabe ist **immer kompakt und strukturiert** (Spec-Diff, geänderte
Dateien, pass/fail je AK, Urteil+Risiken) — **keine Datei-Dumps, kein Roh-Code-Paste**.
Was der Subagent gelesen hat, bleibt in seinem Kontext; in den Hauptthread fließt nur das Ergebnis.

---

## 2. Vordertür: Orchestrator auch für Einzeltickets

Jede Implementierungs-, Bug- oder Feature-Anfrage — **auch ein einzelnes Ticket** — geht durch
den **Lane-Zyklus** des `fotoalert-orchestrator` (dünner Steuer-Thread, delegiert jede Phase).
Nicht erst ab „arbeite das ganze Backlog ab". Der Orchestrator selbst liest **nur den
🚦 Gate-Board-Abschnitt** von `BACKLOG.md`, nie die ganze Datei.

Phasen (jede in eigenem Subagenten): **Analyse → [Weg-Gate] → Impl → Test → [Test-Gate] →
Verifikation (separater Subagent!) → [Release-Gate] → Done → Retro.**

---

## 3. Stephans Gates (immer Halt, nie autonom überschreiten)

1. **Weg-Gate** nach der Analyse: Optionen+Empfehlung kompakt vorlegen, auf Freigabe warten.
2. **Test-Bestätigung** bei Browser-/iOS-/visuellen Checks: validierte Schritte übergeben, „passt" abwarten.
3. **Release-Gate:** Deploy ist manuell. **Niemals `git` in der Sandbox.** Befehl fürs Mac-Terminal
   erzeugen, auf Stephans Bestätigung (Deploy + Health-Check grün) warten.

Reihenfolge fix: **Test ✅ → Refactor → Release → erst dann Ticket auf Done → Retro (Pflicht).**

---

## 3b. Schritt-Validierung (Gate-Check) — HART, vor jedem Schritt

Bevor eine Phase startet (Impl, Test, Refactor, Release, Done), **zuerst** prüfen, ob die
Vorstufen ihre Nachweise am Ticket hinterlassen haben — deterministisch, nicht aus dem Gedächtnis:

```
python3 FotoAlert/tools/gate_check.py <TICKET-ID> --phase <impl|test|refactor|release|done>
```

- **Exit 0 (grün):** Vorstufen erledigt oder von Stephan gültig übersprungen → Schritt darf starten.
- **Exit 1 (rot):** **hart blockieren** — den Schritt **nicht** starten. Stattdessen den fehlenden
  Vorschritt **automatisch in einem Subagenten nachholen** (Stephans Vorgabe 2026-06-28) und das
  Ergebnis melden. **Ausnahme:** verlangt der fehlende Schritt eine Stephan-Entscheidung
  (Weg-Gate, Release), anhalten und fragen — nie selbst entscheiden.

Jede Phase **pflegt nach Abschluss ihren Gate-Status-Block** im Ticket (✅). Überspringen darf
**nur Stephan** — Vermerk `⤼ Stephan JJJJ-MM-TT: Grund`; ein ⤼ ohne diese Zuschreibung gilt als
ungültig (rot). Das Modell setzt **nie** selbst ein ⤼. Konvention: `docs/gate-status-konvention.md`.
Der Skript-Check fängt das **Vergessen**; die inhaltliche Qualität prüft der separate
Verifikations-Subagent (§ Verifikation).

---

## 4. Kontext-schonende Leseregeln

- `BACKLOG.md` ist groß: **nie ganz lesen.** Nur den Gate-Board-Abschnitt oder ein einzelnes
  Ticket gezielt (grep/offset). Volltext-Reads gehören in einen Subagenten.
- Analyse-Specs: pro Ticket, gezielt — nicht das ganze Backlog mitziehen.
- Caches sind groß (bis ~97 MB): nur Subagenten lesen sie, nie der Hauptthread.

---

## 5. Harte Projektregeln (gelten in jeder Phase, Haupt- wie Subagent)

- Kein `git`/`curl`-zu-externen-URLs in der Sandbox (Release am Mac-Terminal; Health-Check via `web_fetch`).
- Server-Validierung vor Tests (Terminal-Fenster-Modell: Fenster 1 = Server, Fenster 2 = curl).
- **Keine Löschung** (Datei/Ticket/Daten) ohne Erklärung + explizites Ja von Stephan.
- Kein Scope-Creep — nur was im Ticket steht; Extras als Vorschlag.
- Kanban nach **jeder** Status-Änderung mitziehen (`tools/sync_kanban.py` → `update_artifact`).
- PRODUCT.md nach jedem Ticket pflegen (Basis für Regression).
- Server läuft **Python 3.9** — keine 3.10+-Syntax (`str|None`).
- **Subagenten-Erfolgsmeldung zu Schreiboperationen nie ungeprüft übernehmen** ("Datei X
  geändert/ergänzt" o.ä.): sofort nach dem Edit/Write per Grep/Read gegen die genannte
  Zielstelle verifizieren, Rohausgabe zitieren — nicht nur die Prosa-Zusammenfassung des
  Subagenten glauben. Zweifach aufgetreten (TASK-64, TASK-84) — reines Memory reichte beim
  ersten Mal nicht aus, deshalb hier zusätzlich verankert (Memory
  `feedback_subagent_false_positive_claims`, `fotoalert-impl` Pattern 21).
- **Kein Tool-Call vor einer reinen Text-/Codeblock-Antwort** (Handoff-Schritt, Erklärung,
  Terminal-Befehl zum Kopieren) — kein `bash echo`/`true`, kein sachfremder Werkzeug-Griff nur
  um "etwas zu tun". Selbst-Check vor JEDEM Call: „Braucht die Antwort dieses Ergebnis?" Wenn nein
  → direkt antworten. Gilt besonders in Ketten aus mehreren Handoff-Antworten hintereinander
  (Release/Test-Dialoge) — dort ist der Fehlreflex am stärksten. 11-fach rückfällig trotz
  globaler Memory `feedback_no_tool_call_before_text_answer` — deshalb hier zusätzlich verankert,
  weil diese Datei bei jedem Chat-Start geladen wird (globale Memory offenbar nicht ausreichend).

Vollständige Details und Warum: siehe Memory-Dateien und `FotoAlert/PIPELINE.md` §3.5/§3.6.
