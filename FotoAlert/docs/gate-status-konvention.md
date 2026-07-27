# Gate-Status — Schritt-Validierung pro Ticket

**Zweck:** verhindern, dass kritische Workflow-Schritte stillschweigend übersprungen werden und
die Produktqualität gefährden. Vorbild ist der Kanban-Lint: nicht das Modell „erinnert sich",
sondern ein deterministisches Skript (`tools/gate_check.py`) prüft am Ticket nach, ob die
Vorstufen ihre Nachweise hinterlassen haben.

## Eine Wahrheitsquelle je Ticket

Jedes Ticket bekommt **einen** maschinenlesbaren Block — analog zum `Status`-Feld fürs Kanban.
Die Skills füllen ihn; `gate_check.py` liest ihn. Die bestehenden Checklisten (Example Mapping,
Pre-Mortem, Testplan …) bleiben als menschliche Detailebene und sind der **Nachweis**, den ein
Skill abhakt, bevor es ein Gate auf ✅ setzt.

```markdown
**Gate-Status:** <!-- maschinell geprüft · nur via Skills oder durch Stephan ändern -->
| Gate | Status | Nachweis / Begründung |
|------|--------|-----------------------|
| Spec | ⬜ | — |
| Tests definiert | ⬜ | — |
| Implementierung | ⬜ | — |
| Test bestanden | ⬜ | — |
| Refactor-Check | ⬜ | — |
| PRODUCT.md | ⬜ | — |
| Release | ⬜ | — |
```

**Status (seit 2026-07-22, siehe `docs/2026-07-02-pipeline-gate-reliability-design.md`):** diese
Tabellenform ist weiterhin ein gültiges, von `gate_check.py` erkanntes Format — aber **faktisch
ungenutzt**. Reale Tickets tracken Fortschritt über Prosa, nicht über diese Tabelle. Für die drei
Gates **Retro / Lernen**, **Refactor-Check** und **Verifikation** gilt stattdessen das
freistehende Marker-Format direkt im Ticket-Fließtext (nächster Abschnitt) — das ist der Weg, wie
diese drei Gates tatsächlich befüllt werden.

## Freistehendes Marker-Format (Retro, Refactor-Check, Verifikation)

Statt einer Tabellenzeile schreibt der zuständige Skill/Subagent eine einzelne Zeile direkt ins
Ticket, im Stil, wie Tickets tatsächlich geschrieben werden:

```markdown
**Retro:** ✅ 2026-07-02 — Memory `reference_x` ergänzt; test_us113_edge.py hinzugefügt
**Refactor-Check:** ✅ 2026-07-02 — keine offenen Befunde
**Verifikation:** ✅ 2026-07-02 — alle 13 AKs bestanden, keine Risiken gefunden
```

`gate_check.py` erkennt diese Zeilen zusätzlich zur Tabellenform und trägt das Ergebnis in
denselben Gate-Status ein (einfache Dict-Vereinigung, kein separates Format). Erlaubte Symbole:
✅ / ⬜ / ⤼ — mit denselben drei Zuständen wie unten beschrieben (⤼ nur gültig mit
`Stephan JJJJ-MM-TT: <Grund>`-Zuschreibung). Auch der Label „Retro / Lernen" wird erkannt.

## Drei Zustände je Gate

- **✅ erledigt** — der Nachweis liegt am Ticket vor (z. B. Spec-Abschnitt, pytest-Datei, Testreport).
- **⬜ offen** — kein Nachweis. Blockiert jeden nachgelagerten Schritt.
- **⤼ übersprungen** — von Stephan bewusst freigegeben. **Nur gültig**, wenn die Nachweis-Spalte
  dem Format `Stephan JJJJ-MM-TT: <Grund>` entspricht. Ein ⤼ ohne diese Zuschreibung gilt als
  **ungültig (= rot)** — so kann das Modell sich nicht selbst freigeben.

## Was jedes Gate als Nachweis verlangt

- **Spec:** `#### 🔬 Analyse-Spec` + `**Akzeptanzkriterien:**` + `**Pre-Mortem:**` im Ticket.
- **Tests definiert:** Testplan ausgefüllt (Automatisiert/Manuell) UND — wo automatisierbar —
  `backend/tests/test_<ticket-id>.py`. Gilt vor der Implementierung (Test-First).
- **Implementierung:** Notiz „geänderte Dateien" + Status mindestens `In Progress`.
- **Test bestanden:** Testreport pass je AK inkl. Regression (nicht nur die geänderte Funktion).
- **Refactor-Check:** `tools/refactor_check.py` gelaufen, ohne offene Befunde — Nachweis als
  Marker-Zeile `**Refactor-Check:** ✅/⤼ <Datum> — <Zusammenfassung der Befunde>` (siehe oben).
- **PRODUCT.md:** Ticket in `PRODUCT.md` nachgezogen.
- **Verifikation:** separater, frisch gestarteter Subagent (nicht der Impl-Kontext) prüft Diff +
  Akzeptanzkriterien, liefert pass/fail je AK, schreibt
  `**Verifikation:** ✅/⬜ <Datum> — <Urteil>` (siehe oben). Ein Urteil „fail" ist **kein**
  automatisch nachholbarer Fall — das ist ein echter Befund, der eine Stephan-Entscheidung braucht.
- **Release:** deployt + Health-Check grün — ODER ⤼ mit Begründung „kein Deploy nötig".
- **Retro / Lernen:** `retrospective`-Subagent gelaufen, Marker-Zeile
  `**Retro:** ✅ <Datum> — <Notiz>` (siehe oben).

## Reihenfolge / welche Vorstufen ein Schritt verlangt

| Bevor dieser Schritt startet | müssen erledigt/übersprungen sein |
|------------------------------|-----------------------------------|
| Implementierung | Spec · Tests definiert |
| Test ausführen | Spec · Tests · Implementierung |
| Refactor-Check | Spec · Tests · Impl · Test bestanden |
| Verifikation | Spec · Tests · Impl · Test bestanden · Refactor · PRODUCT.md |
| Release | Spec · Tests · Impl · Test bestanden · Refactor · PRODUCT.md · Verifikation |
| Done | alle oben + Release |
| Retro | alle oben + Release |

## Verhalten bei Rot (Stephans Wahl 2026-06-28)

- **Hart blockieren:** Fehlt ein Vorschritt (⬜) und ist nicht gültig übersprungen, wird der
  nächste Schritt **gar nicht erst gestartet**.
- **Fehlenden Schritt automatisch anstoßen:** das zuständige Skill holt den fehlenden Schritt in
  einem Subagenten nach und meldet das Ergebnis — ohne dass Stephan es anstoßen muss. Nur wenn der
  Schritt eine Stephan-Entscheidung braucht (Weg-Gate, Release), wird angehalten und gefragt.

## Zwei Prüf-Ebenen (ehrlich)

`gate_check.py` prüft nur, **ob** ein Nachweis vorhanden ist (fängt das Vergessen). **Ob** der
Nachweis taugt (decken die Tests die AKs ab?), prüft der separate Verifikations-Subagent. Beides
zusammen schützt die Control Steps.
