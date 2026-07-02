# Retro-Gate-Zuverlässigkeit — Design

> **Status:** Entwurf zur Freigabe · **Erstellt:** 2026-07-02 · **Owner:** Stephan
> **Verwandt:** `PIPELINE.md` §3.4/§3.5 (Lern-Loop, offen), `docs/gate-status-konvention.md`,
> `tools/gate_check.py`, Scheduled Task `fotoalert-pipeline-heartbeat`

---

## 0. Ausgangslage (Befund)

`PIPELINE.md` beschreibt seit 2026-06-20 eine eigene Lane `🔁 Retro / Lernen`, die nach `Done`
automatisch laufen soll (§3.4). `CLAUDE.md` erklärt Retro seit 2026-06-28 für **Pflicht**.
Trotzdem zeigt das aktuelle Gate-Board 20 Tickets in `🏁 Done` ohne erkennbaren Retro-Nachweis.

Root Cause (verifiziert am Code, 2026-07-02):

1. `tools/gate_check.py` kennt die Phase `retro` **nicht** — `GATE_ORDER` endet bei `release`,
   die einzige geprüfte Zielphase danach ist `done`. Das deterministische Skript, das laut
   `gate-status-konvention.md` genau das „Vergessen" abfangen soll, hat hier eine Lücke.
2. Der Scheduled Task `fotoalert-pipeline-heartbeat` liest das Gate-Board bei jedem Lauf, prüft
   aber nur `🚦 Ready for Analysis` und `✅ Ready for Dev` (Aufgabe B). Die Lane `🏁 Done` wird
   nie angeschaut.
3. `docs/skill-changes-product-test-first.md` (2026-06-28) ist ein reales Beispiel für den in
   §3.4 beschriebenen „Skill-Vorschlag zur Freigabe" — aber lose, ohne Status-Tracking. Unklar,
   ob/wann er je installiert wurde.

Damit ist Retro heute reine Instruktion ohne erzwingenden Mechanismus — genau das Muster, das
`gate-status-konvention.md` für alle anderen Phasen bereits gelöst hat.

---

## 1. Architektur & Lebenszyklus

Retro wird eine reguläre achte Gate-Phase, kein Sonderfall:

```
spec → tests → impl → test_pass → refactor → product → release → done → retro
```

Alles bis `done` bleibt unverändert. Sobald ein Ticket `Done` erreicht — ob über den
Orchestrator oder eine manuelle Board-Änderung — schuldet es einen Retro-Nachweis. Da nach
Retro keine weitere Phase folgt, kann sie (anders als z. B. Release) nichts blockieren; die
Durchsetzung kommt stattdessen vom Heartbeat: jeder Lauf fegt die `Done`-Lane durch und holt
jeden fehlenden Retro-Nachweis nach — nach demselben Auto-Nachhol-Prinzip, das
`gate-status-konvention.md` bereits für alle anderen Phasen definiert.

Damit hört Retro auf, „etwas, das der Orchestrator hoffentlich aufruft" zu sein, und wird zu
„das Board kann nie länger als ein Heartbeat-Intervall aus dem Takt geraten" — dieselbe
Garantie, die `sync_kanban.py` heute schon fürs Kanban-Artifact gibt.

---

## 2. Gate-Mechanismus

### 2.1 `tools/gate_check.py`

- `GATE_ORDER` erhält `"retro"` als letzten Eintrag.
- `REQUIRES["retro"] = ["spec", "tests", "impl", "test_pass", "refactor", "product", "release"]`
  (alles, was `done` bereits verlangt — Retro ergibt nur bei einem tatsächlich fertigen Ticket Sinn).
- `GATE_LABEL["retro"] = "Retro / Lernen"`, `GATE_SKILL["retro"] = "retrospective"`.
- Aufruf: `python3 tools/gate_check.py <TICKET-ID> --phase retro` funktioniert danach analog zu
  `--phase release` — grün/rot, deterministisch, ohne dass ein Modell sich „erinnern" muss.

### 2.2 `docs/gate-status-konvention.md`

Die Gate-Status-Tabelle pro Ticket bekommt eine achte Zeile, im selben Format wie die
bestehenden sieben:

```markdown
**Gate-Status:** <!-- maschinell geprüft · nur via Skills oder durch Stephan ändern -->
| Gate | Status | Nachweis / Begründung |
|------|--------|-----------------------|
| Spec | ✅ | ... |
| Tests definiert | ✅ | ... |
| Implementierung | ✅ | ... |
| Test bestanden | ✅ | ... |
| Refactor-Check | ✅ | ... |
| PRODUCT.md | ✅ | ... |
| Release | ✅ | ... |
| Retro / Lernen | ⬜ | — |
```

- **✅ erledigt:** Nachweis-Spalte nennt Datum + eine Zeile, was Retro erzeugt hat (z. B.
  „2026-07-02 — Memory `reference_x` ergänzt; `test_us113_edge.py` hinzugefügt" oder knapp
  „2026-07-02 — keine neuen Erkenntnisse").
- **⬜ offen:** Default-Zustand, bis der Heartbeat oder eine manuelle Retro es füllt.
- **⤼ übersprungen:** nur gültig im Format `Stephan JJJJ-MM-TT: <Grund>` — identisch zur
  bestehenden Regel für alle anderen Gates.
- Die „Reihenfolge / welche Vorstufen"-Tabelle im selben Dokument bekommt eine Zeile:
  `Retro | alle oben + Release`.

Dies ist bewusst die kleinstmögliche Änderung — Retro folgt exakt demselben Muster wie die
sieben bestehenden Gates, keine neue Konvention.

---

## 3. Heartbeat-Sweep (Aufgabe C)

`fotoalert-pipeline-heartbeat` bekommt eine dritte Aufgabe, nach der bestehenden Aufgabe A
(Kanban-Sync) und Aufgabe B (Auto-Start):

**Aufgabe C — Retro-Sweep:**

1. Die bereits gelesene `🏁 Done`-Lane aus dem Gate-Board verwenden (kein zusätzlicher Read).
2. Für jede Ticket-ID dort: `gate_check.py <ID> --phase retro` ausführen.
3. Jedes rote Ticket (offen, keine gültige Freigabe) → an einen **frischen Retro-Subagenten**
   delegieren: scharf umrissener Auftrag (genau dieses Ticket), Skill `retrospective`,
   isolierter Kontext — dasselbe Auto-Nachhol-Prinzip aus `gate-status-konvention.md`, jetzt auch
   für diese Phase angewandt. Der Heartbeat selbst liest keine Ticket-Inhalte oder Diffs direkt.
4. Der Subagent liefert ein kompaktes Ergebnis zurück (Memory-/Test-Updates, ggf. ein
   angelegter Skill-Vorschlag) → der Heartbeat trägt die Gate-Status-Zeile „Retro / Lernen" auf
   ✅ ein und ergänzt eine Zeile in der Lauf-Zusammenfassung. **Kein Stephan-Gate hier** — Retros
   Outputs sind additiv/risikoarm (§3.4-Prinzip bleibt unverändert), läuft also unbeaufsichtigt.
5. Kein rotes Ticket gefunden → unverändert die knappe „Board synchron"-Zeile wie heute.

Damit kann ein Ticket höchstens ein Heartbeat-Intervall lang ohne Retro-Nachweis bleiben —
unabhängig davon, ob es über den Orchestrator oder manuell nach `Done` gelangt ist.

---

## 4. Retrospektiv-Output & Skill-Vorschlags-Log

Die Aufteilung aus `PIPELINE.md` §3.4 bleibt inhaltlich unverändert — dieser Abschnitt
formalisiert nur die Vorschlags-Seite, die heute nachweislich ungetrackt ist
(`docs/skill-changes-product-test-first.md` seit 2026-06-28 ohne Status).

**Bleibt automatisch, unverändert:** Memory-Einträge (Pre-Mortem-Wissensbasis) und
Regressionstest-Ergänzungen — direkt geschrieben, kein Gate.

**Neu: `docs/skill-change-proposals.md`** — eine Tabelle, append-only, neueste Zeile oben:

| Datum | Ticket | Betroffene Skill(s) | Zusammenfassung | Status |
|-------|--------|----------------------|------------------|--------|
| 2026-07-02 | US-113 | fotoalert-analyze | Pre-Mortem um Sichtachsen-Check ergänzen | proposed |

- **Zusammenfassung:** eine Zeile. Alles, was länger ist (ein echter Diff/Patch, wie bisher
  `skill-changes-product-test-first.md`), kommt in eine eigene Datei unter
  `docs/skill-change-proposals/<datum>-<slug>.md`, aus der Zusammenfassungs-Zelle verlinkt.
- **Status:** einzige Spalte, die Stephan von Hand ändert — `proposed → approved → installed`
  oder `→ rejected`. Retro hängt nur Zeilen an oder liest Status, ändert ihn nie selbst (spiegelt
  die bestehende Regel, dass Agenten Skill-Änderungen nie selbst installieren).
- Aufgabe C des Heartbeats meldet Zeilen, die länger als **7 Tage** `proposed` sind, in der
  Lauf-Zusammenfassung — reine Sichtbarkeit, keine Auto-Aktion. Der Wert ist willkürlich gewählt
  und kann bei Bedarf angepasst werden, ohne den Mechanismus selbst zu ändern.

---

## 5. Edge Cases & Fehlerbehandlung

- **Die 20 bestehenden Done-Tickets (Umstellung).** Backfill ist bewusst ausgeschlossen
  (Entscheidung 2026-07-02). Beim Rollout bekommt jedes der 20 Tickets einmalig die Zeile
  `| Retro / Lernen | ⤼ | Stephan 2026-07-02: Altbestand vor Retro-Gate-Einführung, kein Backfill |`
  — eine gültige Freigabe nach bestehender Konvention. Ohne diesen Schritt würden alle 20 beim
  ersten Heartbeat-Lauf nach dem Rollout rot aufleuchten und 20 Retro-Läufe auslösen, was der
  Backfill-Entscheidung widerspräche.
- **Triviale Fixes.** `CLAUDE.md` erlaubt 1–3-Zeilen-Fixes ohne schwere Datei direkt im
  Hauptthread. Auch diese erreichen `Done` und schulden einen Retro-Nachweis — der
  Retro-Subagent wird hier meist „keine neuen Erkenntnisse" eintragen. Keine Sonderregel, um
  nicht eine zweite Definition von „trivial" pflegen zu müssen.
- **Fehlschlag des Retro-Subagenten.** Bei Fehler/Timeout bleibt die Gate-Status-Zeile `⬜` (kein
  stilles Grünwaschen); der Heartbeat meldet das Ticket weiterhin als rot, der nächste Lauf
  versucht es erneut automatisch.
- **Zusammenspiel mit `BACKLOG-ARCHIVE.md`.** Ein Ticket darf erst archiviert werden, wenn sein
  Retro-Gate ✅ oder gültig ⤼ ist — sonst könnte ein Ticket dem Sweep durch Archivierung entkommen.
- **Nebenläufigkeit.** Heartbeat-Läufe sind durch das Scheduling bereits effektiv serialisiert;
  Aufgabe C startet Subagenten nur für zum Sweep-Zeitpunkt noch rote Tickets. Kein zusätzliches
  Locking nötig.

---

## 6. Rollout & Verifikation

Reihenfolge, jeder Schritt einzeln überprüfbar:

1. **`gate_check.py`** — Phase `retro` ergänzen. Verifikation: `--phase retro` gegen ein Ticket
   ohne Nachweis (rot erwartet) und eines mit von Hand ergänzter Zeile (grün erwartet) laufen
   lassen; bestehende Phasen dürfen sich nicht ändern.
2. **`docs/gate-status-konvention.md`** — neue Zeile dokumentieren.
3. **Umstellungs-Freigabe** der 20 bestehenden Done-Tickets (§5).
4. **`fotoalert-pipeline-heartbeat`** — Aufgabe C ergänzen. Verifikation per Trockenlauf: bei
   einem realen Ticket den Retro-Nachweis testweise entfernen und bestätigen, dass der nächste
   Heartbeat-Lauf es erkennt, einen Subagenten delegiert und die Zeile danach wieder ✅ zeigt.
5. **`docs/skill-change-proposals.md`** — leere Tabelle mit Kopfzeile anlegen.
6. **`retrospective`-Skill** — Instruktionen erweitern: (a) Gate-Status-Zeile „Retro / Lernen"
   als letzten Schritt setzen, (b) Skill-Vorschläge in `skill-change-proposals.md` anhängen statt
   lose Einzeldateien zu erzeugen.

Es gibt keine pytest-Suite für diesen Umbau — es ist Prozess-/Skill-Infrastruktur, keine
App-Logik. „Testen" heißt: die Trockenläufe oben, einmal manuell bestätigt, bevor der Heartbeat
unbeaufsichtigt darauf vertraut wird.

---

## 7. Offene Punkte für spätere Iterationen (bewusst außerhalb dieses Scopes)

- Wie lange darf ein Vorschlag in `skill-change-proposals.md` `proposed` bleiben, bevor er als
  verworfen gilt? (Nicht Teil dieses Designs — reine Sichtbarkeit reicht fürs Erste.)
- Automatisierte Qualitätsprüfung der Retro-Inhalte (deckt der Nachweis wirklich etwas ab, oder
  ist er ein Leerlauf-Eintrag?) — analog zur bestehenden Trennung zwischen `gate_check.py`
  („ist ein Nachweis da?") und dem separaten Verifikations-Subagenten („taugt er?") aus
  `gate-status-konvention.md` §„Zwei Prüf-Ebenen". Für Retro aktuell nicht vorgesehen.
