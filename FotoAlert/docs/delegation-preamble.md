# Delegations-Preamble für die FotoAlert-Phasen-Skills

**Zweck:** Defense-in-depth zu `FotoAlert/CLAUDE.md` §1. CLAUDE.md erzwingt den Delegations-Default
bereits global (immer geladen). Dieser Block macht jedes einzelne Phasen-Skill **selbst-delegierend**,
falls ein Skill mal außerhalb des CLAUDE.md-Kontexts ausgelöst wird.

**Anwenden auf:** `fotoalert-analyze`, `fotoalert-impl`, `fotoalert-test`, `fotoalert-refactor`,
`fotoalert-release`. (`fotoalert-intake` und `retrospective` analog, wenn sie schwere Dateien lesen.)

**Wie:** Diesen Block als **erste Sektion direkt nach dem Frontmatter** einfügen — vor „Schritt 1".
Die Skill-Dateien im Plugin-Cache sind read-only; die Änderung in den **Quell-`.skill`-Paketen**
machen (bzw. via `skill-creator` neu paketieren) und in den Einstellungen → Capabilities neu installieren.

---

## Block zum Einfügen (Wortlaut)

```markdown
## Schritt 0 — Kontext-Check: laufe ich im Hauptthread?

**Wenn dieser Skill im Hauptthread (sichtbares Fenster) ausgelöst wird und NICHT bereits in
einem Subagenten läuft: STOPP.** Diese Phase an einen Task-Subagenten delegieren, statt sie
inline auszuführen (siehe `FotoAlert/CLAUDE.md` §1, Memory `feedback_subagents_multiphase`).

Auftrag an den Subagenten (Pflicht-Form):
- **Ziel:** diese Phase für Ticket <ID> ausführen, dieses Skill anwenden.
- **Pfade:** nur die betroffenen Dateien (nicht ganz BACKLOG.md / web/index.html).
- **Rückgabe-Vertrag:** kompakt + strukturiert — Spec-Diff / Liste geänderter Dateien /
  pass-fail je AK / Urteil+Risiken. **Keine Datei-Dumps, kein Roh-Code-Paste.**

Der Hauptthread nimmt nur das kompakte Ergebnis entgegen, setzt Lane/Status, zieht das Kanban
mit und prüft das nächste Gate. Nur triviale 1–3-Zeilen-Fixes ohne schwere Datei darf der
Hauptthread selbst machen.

Läufst du bereits als Subagent? Dann diesen Schritt überspringen und normal mit Schritt 1 fortfahren.
```

---

## Orchestrator als Vordertür (Hebel 3)

In `fotoalert-orchestrator` die Beschreibung/Schritt 0 so erweitern, dass er **auch für ein
einzelnes Ticket** die Vordertür ist — nicht erst ab „arbeite das ganze Backlog ab". Vorschlag
für die Description-Trigger zusätzlich aufnehmen:

> „fix das", „implementier das", „analysier das Ticket", „mach Ticket <ID>" — auch Einzeltickets
> laufen durch den Lane-Zyklus (jede Phase im eigenen Subagenten).

So greift die Auslagerung beim Normalfall (Einzel-Trigger), nicht nur beim Voll-Pipeline-Lauf.
