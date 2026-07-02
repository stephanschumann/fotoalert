# Pipeline-Gate-Zuverlässigkeit — Design (vereinheitlicht)

> **Status:** Entwurf zur Freigabe · **Erstellt:** 2026-07-02 · **Owner:** Stephan
> **Ersetzt:** `docs/2026-07-02-retro-gate-reliability-design.md` (nur Retro-Scope — überholt,
> siehe Hinweis dort). Dieses Dokument erweitert den gleichen Mechanismus auf drei Gates.
> **Verwandt:** `PIPELINE.md` §3.4/§3.6, `docs/gate-status-konvention.md`, `tools/gate_check.py`,
> `tools/refactor_check.py`, Scheduled Task `fotoalert-pipeline-heartbeat`

---

## 0. Ausgangslage (Befund)

Ursprünglich sollte dieses Design nur die Lücke bei `🔁 Retro / Lernen` schließen (siehe
ersetztes Dokument). Eine Recherche vor der Plan-Erstellung ergab jedoch ein größeres,
systemisches Muster: **mehrere Prozess-Mechanismen sind in `CLAUDE.md`/`PIPELINE.md` als
automatisch/erzwungen dokumentiert, hinterlassen aber in keinem realen Ticket eine Spur.**

Verifiziert am Code und an `BACKLOG.md`/`BACKLOG-ARCHIVE.md` (2026-07-02):

| Mechanismus | Befund |
|-------------|--------|
| **Gate-Status-Tabelle** (7 Gates, `gate-status-konvention.md`) | **Aspirational.** Null Treffer für „Gate-Status" in beiden Backlog-Dateien. Reale Tickets tracken Fortschritt über Prosa (Example Mapping, Pre-Mortem, AK-Checkboxen), nie über die Tabelle. |
| **Refactor-Check-Gate** | **Aspirational.** `tools/refactor_check.py` ist ein funktionierendes 167-Zeilen-Tool — aber nirgends im Backlog als „gelaufen"/„bestanden" pro Ticket festgehalten. |
| **Verifikations-Subagent** (PIPELINE.md §3.6) | **Aspirational.** Im Roadmap als „✅ installiert" markiert, aber null Treffer für „Verifikation" im Backlog. |
| **Retro / Lernen** | **Aspirational.** 20 Tickets in `🏁 Done` ohne Retro-Nachweis; der Heartbeat sweept `Done` nie. |
| Kanban-Auto-Sync | Ursprünglich als weiterer Befund vermutet, aber die Heartbeat-Instruktionen schreiben in ein session-eigenes Output-Verzeichnis + Cowork-Artifact, nicht in die lokale Repo-Datei. Die geprüfte lokale Datei ist daher kein verlässlicher Indikator — **aus diesem Design bewusst ausgeklammert.** |
| PRODUCT.md-Pflege | **Teilweise.** Changelog existiert und ist meist aktuell, hinkt aber den neuesten Releases hinterher. Nicht Teil dieses Designs (kein Gate-Mechanismus-Problem, sondern Disziplin-Frage). |

**Root Cause (gemeinsam für die drei behandelten Gates):** Die Tabellen-Konvention wurde nie in
den tatsächlichen Ticket-Schreibprozess eingebaut — keiner der fünf Phasen-Skills
(`fotoalert-analyze/-impl/-test/-refactor/-release`) schreibt sie. `gate_check.py` prüft daher
gegen eine Datenquelle, die nie befüllt wird.

---

## 1. Architektur & Entscheidung

Statt die Tabelle nachträglich in fünf bestehende, global geteilte Skills einzubauen (großer,
riskanter Umbau — explizit **nicht** Teil dieses Designs, siehe §7), bekommen die drei
betroffenen Gates einen **leichtgewichtigen, freistehenden Marker** direkt im Ticket-Fließtext —
im Stil, wie Tickets tatsächlich geschrieben werden:

```
**Retro:** ✅ 2026-07-02 — Memory `reference_x` ergänzt; test_us113_edge.py hinzugefügt
**Refactor-Check:** ✅ 2026-07-02 — keine offenen Befunde
**Verifikation:** ✅ 2026-07-02 — alle 13 AKs bestanden, keine Risiken gefunden
```

`gate_check.py` erkennt diese Zeilen zusätzlich zur (weiterhin gültigen, aber faktisch
ungenutzten) Tabellenform. Durchsetzung läuft über zwei verschiedene Hebel, je nachdem ob dem
Gate ein nachgelagerter Schritt folgt:

- **Verifikation** blockiert hart vor `Release` (wie `Refactor-Check`/`PRODUCT.md` es dort
  bereits tun) — es gibt einen nachgelagerten Schritt, der warten kann.
- **Retro** und **Refactor-Check** haben nach `Done` keinen nachgelagerten Schritt mehr, der
  blockieren könnte. Sie werden stattdessen vom **Heartbeat-Sweep** durchgesetzt: jeder Lauf
  prüft die `Done`-Lane und holt fehlende Nachweise automatisch nach.

---

## 2. Gate-Mechanismus (`tools/gate_check.py`)

### 2.1 Parser-Erweiterung

`parse_gate_status()` liest heute ausschließlich Tabellenzeilen. Neu: eine zweite Erkennung für
freistehende Marker-Zeilen, deren Ergebnis mit der Tabellen-Erkennung zusammengeführt wird
(einfache Dict-Vereinigung — da aktuell kein Ticket Tabellenzeilen hat, gibt es keine
Konfliktfälle zu lösen).

```python
STANDALONE_RE = re.compile(
    r'^\*\*(Retro(?:\s*/\s*Lernen)?|Refactor-Check|Verifikation):\*\*\s*(✅|⬜|⤼)\s*(.*)$'
)
STANDALONE_KEY = {"retro": "retro", "retro / lernen": "retro",
                  "refactor-check": "refactor", "verifikation": "verification"}
```

- `parse_gate_status()` scannt zusätzlich zeilenweise mit `STANDALONE_RE`; bei Treffer wird
  `STANDALONE_KEY[label.lower()]` als Key verwendet, `✅`→`done`, `⬜`→`open`,
  `⤼`→`waived`/`waived_invalid` (gleiche `WAIVER_RE`-Prüfung wie bei Tabellenzeilen).
- Ergebnis wird ins selbe `result`-Dict wie die Tabellen-Zeilen geschrieben (Update, kein
  getrenntes Dict).

### 2.2 Neue/geänderte Keys

| Key | Status | Label | Zuständiger Skill/Subagent |
|-----|--------|-------|------------------------------|
| `retro` | **neu** | „Retro / Lernen" | `retrospective` |
| `verification` | **neu** | „Verifikation" | frischer Subagent (kein eigenes Skill-Paket, siehe §3.2) |
| `refactor` | **bestehender Key**, nur Marker-Erkennung neu | „Refactor-Check" (unverändert) | `fotoalert-refactor` |

`GATE_ORDER` erhält `"verification"` (zwischen `product` und `release`, da es Release
vorgelagert ist) und `"retro"` (ans Ende, da nach Done). `refactor` bleibt an seiner
bestehenden Position:

```python
GATE_ORDER = ["spec", "tests", "impl", "test_pass", "refactor", "product",
              "verification", "release", "retro"]
```

### 2.3 `REQUIRES`-Änderungen

```python
REQUIRES = {
    "impl":     ["spec", "tests"],
    "test":     ["spec", "tests", "impl"],
    "refactor": ["spec", "tests", "impl", "test_pass"],
    "release":  ["spec", "tests", "impl", "test_pass", "refactor", "product", "verification"],
    "done":     ["spec", "tests", "impl", "test_pass", "refactor", "product", "verification", "release"],
    "retro":    ["spec", "tests", "impl", "test_pass", "refactor", "product", "verification", "release"],
}
```

`release` verlangt neu `verification` (hart blockierend, analog zu `refactor`/`product` heute
schon). `done` und `retro` übernehmen das transitiv.

---

## 3. Wer schreibt die Marker

### 3.1 Retro & Refactor-Check

Beide Skills (`retrospective`, `fotoalert-refactor`) sind global geteilte Plugin-Skills, keine
lokal editierbaren Dateien in diesem Projekt (bestätigt: keine lokale `.skill`-Paketdatei für
`retrospective` gefunden, anders als z. B. `fotoalert-analyze.skill`). Projektspezifisches
Verhalten für geteilte Skills läuft in diesem Projekt bereits über `CLAUDE.md` (immer geladen,
überstimmt generische Skill-Instruktionen) — dieselbe Stelle bekommt zwei neue Zeilen in §5:

- „Nach Retro (Pflicht, siehe §2/§3): Zeile `**Retro:** ✅ <Datum> — <Notiz>` ins Ticket
  schreiben."
- „Nach `refactor_check.py` (Pflicht vor Release): Ergebnis als
  `**Refactor-Check:** ✅/⤼ <Datum> — <Zusammenfassung der Befunde>` ins Ticket schreiben."

### 3.2 Verifikation (neuer Subagent, kein neues Skill-Paket)

`PIPELINE.md` §3.6 beschreibt diesen Schritt bereits als „ein eigener Subagent mit isoliertem
Kontext" — analog zu `Explore`/`Plan`, die ebenfalls keine installierten Skills sind, sondern
gezielt beauftragte Task-Dispatches. Diese Form wird beibehalten (kein neues `.skill`-Paket,
kleinerer Fußabdruck).

`CLAUDE.md` bekommt eine dokumentierte Dispatch-Vorlage: vor dem Release-Gate wird ein frischer
Subagent (nicht der Impl-Kontext — vermeidet den Bias, dass derselbe Kontext, der den Code
geschrieben hat, ihn auch „grün" prüft) mit Diff + Akzeptanzkriterien des Tickets beauftragt. Er
liefert ein pass/fail je AK + gefundene Risiken zurück und schreibt
`**Verifikation:** ✅/⬜ <Datum> — <Urteil>` ins Ticket.

**Wichtige Unterscheidung:** ein **fehlender** Marker ist automatisch nachholbar (Standard-Fall
für den Heartbeat-Sweep, §4). Ein Marker mit **Urteil „fail"** ist das nicht — das ist ein
echter Befund, der laut bestehender Regel eine Stephan-Entscheidung braucht (Halt + Frage), kein
automatischer Nachhol-Fall.

---

## 4. Heartbeat-Sweep (Aufgabe C)

`fotoalert-pipeline-heartbeat` bekommt Aufgabe C, nach der bestehenden Aufgabe A (Kanban-Sync)
und Aufgabe B (Auto-Start):

1. `🏁 Done`-Lane aus dem bereits gelesenen Gate-Board verwenden.
2. Pro Ticket: `gate_check.py <ID> --phase retro` **und** `gate_check.py <ID> --phase refactor`
   laufen lassen (Verifikation läuft primär als Release-Blocker, siehe §5 — der Sweep prüft sie
   hier nur als Sicherheitsnetz für den unwahrscheinlichen Fall, dass ein Ticket trotzdem ohne
   sie `Done` erreicht hat).
3. Jedes rote Gate → frischer, scharf umrissener Subagent (genau dieses Ticket + dieses Gate,
   isolierter Kontext) holt es nach, meldet kompakt zurück.
4. Heartbeat trägt den Marker als ✅ ein, ergänzt eine Zeile in der Lauf-Zusammenfassung.
5. Nichts rot → unverändert die knappe „Board synchron"-Zeile.

Verifikation selbst wird **primär durch das harte Release-Blocking** (§2.3) erzwungen, nicht
durch den Sweep — der Sweep ist hier nur Rückversicherung.

---

## 5. Edge Cases & Umstellung

- **20 bestehende Done-Tickets:** bekommen einmalig drei Waiver-Zeilen statt einer:
  ```
  **Retro:** ⤼ Stephan 2026-07-02: Altbestand vor Gate-Erweiterung, kein Backfill
  **Refactor-Check:** ⤼ Stephan 2026-07-02: Altbestand vor Gate-Erweiterung, kein Backfill
  **Verifikation:** ⤼ Stephan 2026-07-02: Altbestand vor Gate-Erweiterung, kein Backfill
  ```
  Ohne diesen Schritt würde der erste Heartbeat-Lauf nach Rollout 20 Tickets gleichzeitig rot
  melden und 40 Subagenten-Läufe auslösen (Retro + Refactor je Ticket) — Widerspruch zur
  „kein Backfill"-Entscheidung.
- **Unterschiedlicher Cutover-Zeitpunkt je Gate:** Retro/Refactor-Check gelten forward-only **ab
  `Done`** (nur neue Abschlüsse). Verifikation gilt forward-only **ab `Release`** — also auch für
  Tickets, die aktuell schon in Arbeit sind (z. B. `US-113`, `In Progress`), aber noch nicht
  released haben. Nur bereits released/Done-Tickets bekommen den Waiver.
- **Fehlschlag des Subagenten:** Marker bleibt `⬜` (kein stilles Grünwaschen), nächster
  Heartbeat-Lauf versucht es erneut.
- **Archivierung (`BACKLOG-ARCHIVE.md`):** ein Ticket darf erst archiviert werden, wenn Retro und
  Refactor-Check ✅ oder gültig ⤼ sind — sonst entkommt es dem Sweep durch Archivierung.
- **Marker vs. Tabelle:** kein Konfliktfall aktuell (keine Tabellenzeilen im Bestand), Dict-Merge
  reicht.

---

## 6. Skill-Vorschlags-Log (unverändert übernommen)

Wie im ersetzten Dokument beschrieben: **neu `docs/skill-change-proposals.md`** — append-only
Tabelle mit Spalten Datum / Ticket / betroffene Skill(s) / Zusammenfassung / Status
(`proposed → approved → installed`/`rejected`). Löst das bestehende, ungetrackte
`docs/skill-changes-product-test-first.md`-Muster ab. Heartbeat meldet Zeilen, die länger als
7 Tage `proposed` sind, als Sichtbarkeits-Hinweis (keine Auto-Aktion).

---

## 7. Rollout & Verifikation

1. **`gate_check.py`** — Parser-Erweiterung (§2.1) + neue Keys `retro`/`verification` +
   `REQUIRES`-Änderungen (§2.3). Verifikation: `--phase retro`/`--phase refactor`/
   `--phase verification` gegen Test-Ticket mit/ohne Marker laufen lassen (rot/grün wie
   erwartet); bestehende Phasen dürfen sich nicht ändern.
2. **`docs/gate-status-konvention.md`** — Marker-Format dokumentieren, Tabellenform als
   weiterhin gültig, aber faktisch ungenutzt kennzeichnen.
3. **`CLAUDE.md` §5** — drei neue Instruktionszeilen (Retro-Marker, Refactor-Check-Marker,
   Verifikations-Dispatch-Vorlage).
4. **Umstellungs-Freigabe** der 20 bestehenden Done-Tickets (§5) — vor Schritt 5, sonst
   Fehlalarm-Flut beim ersten Sweep.
5. **`fotoalert-pipeline-heartbeat`** — Aufgabe C ergänzen. Trockenlauf: bei einem realen Ticket
   testweise einen Marker entfernen, nächsten Heartbeat-Lauf beobachten.
6. **`docs/skill-change-proposals.md`** — leere Tabelle mit Kopfzeile.

Keine pytest-Suite nötig (Prozess-Infrastruktur, keine App-Logik) — Verifikation über die
Trockenläufe oben, einmal manuell bestätigt.

---

## 8. Bewusst außerhalb dieses Scopes

- **Volle Rückkehr zur 7-Gate-Tabelle** (alle fünf Phasen-Skills umbauen, damit sie die Tabelle
  tatsächlich befüllen) — expliziter Non-Goal dieses Designs (Entscheidung 2026-07-02). Größerer,
  eigener Umbau, falls später gewünscht.
- **Kanban-Sync-Frische** — ursprünglich vermuteter weiterer Befund, aber die lokale Messung war
  unzuverlässig (falsche Datei geprüft, siehe §0). Braucht eigene Diagnose, bevor ein Fix
  designt wird.
- **PRODUCT.md-Pflege-Lücke** — Disziplin-/Reihenfolge-Frage, kein fehlender
  Erzwingungs-Mechanismus wie bei den drei behandelten Gates.
- Qualitätsprüfung der Marker-Inhalte selbst (ist die Verifikation inhaltlich richtig, nicht nur
  vorhanden?) — bleibt wie bisher Aufgabe des jeweiligen Subagenten, nicht von `gate_check.py`.
