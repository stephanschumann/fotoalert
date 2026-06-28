# Skill-Ergänzung: Ticket-Beziehungsanalyse & Sequenzierung

> **Hinweis:** Diese Blöcke müssen in die *gespeicherten* Skills eingepflegt werden
> (Einstellungen → Capabilities → jeweiligen Skill bearbeiten). Aus einer Cowork-Session
> heraus lassen sich Skills nicht persistent ändern.

Ziel: Bevor ein Ticket angelegt oder ein Change Request analysiert wird, prüft der
Agent systematisch auf überlappende Tickets und entscheidet **Merge / Split / Separieren /
Abgrenzen** inkl. **Sequenzierung**. Das verhindert Doppelarbeit, widersprüchliche
Verantwortlichkeiten und falsche Reihenfolgen.

---

## 1) Einfügen in `book-of-work` (bei der Anlage)

Im Abschnitt **„Workflow – Kurzübersicht → Neues Ticket anlegen"** als Schritt 0
voranstellen, und folgende Sektion ergänzen:

```markdown
## Verwandte Tickets prüfen (vor dem Anlegen — Pflicht)

Vor dem Anlegen BACKLOG.md nach thematisch überlappenden Tickets durchsuchen
(Stichwörter aus der Beschreibung + betroffene Dateien/Module). Für jeden Treffer
die Beziehung bestimmen:

| Beziehung | Bedeutung | Aktion |
|-----------|-----------|--------|
| **Duplikat** | Gleiches Ziel & Scope | Nicht neu anlegen — bestehendes nutzen/ergänzen |
| **Teilmenge** | Neues deckt ein bestehendes mit ab | Bestehendes nach Freigabe als „merged in [ID]" markieren |
| **Obermenge / Epic** | Neues ist zu groß, bündelt mehrere Lieferungen | In Epic + sequenzierte Kind-Tickets splitten |
| **Überlappung** | Teilbereiche überschneiden sich | Sauber abgrenzen; Verantwortung je Ticket eindeutig |
| **Abhängigkeit** | Setzt anderes voraus / blockiert es | „Abhängigkeit: [ID]" + Sequenz dokumentieren |

Ergebnis im neuen Ticket unter **Bezug:** festhalten (verlinkte IDs + Beziehungstyp).
Merge, Split oder Verschieben bestehender Tickets **niemals ohne explizite Freigabe**
von Stephan (siehe Lösch-/Änderungsregel). Bei Epic-Split: Kind-Tickets sofort mit
Abhängigkeiten (`addBlockedBy`) anlegen.
```

---

## 2) Einfügen in `fotoalert-analyze` (bei der Analyse eines Change Requests)

Als neuen **Schritt 1.5** zwischen „Schritt 1 — Example Mapping" und
„Schritt 2 — Akzeptanzkriterien ableiten" einfügen:

```markdown
## Schritt 1.5 — Ticket-Beziehungsanalyse & Sequenzierung

Vor der Architektur-Analyse das Ticket gegen den restlichen Backlog prüfen — Ziel ist
eine eindeutige Verantwortlichkeit je Ticket und eine umsetzbare Reihenfolge.

1. BACKLOG.md nach überlappenden Tickets durchsuchen (Thema, betroffene Dateien/Module).
2. Pro Treffer Beziehung klassifizieren:
   Duplikat / Teilmenge / Obermenge (Epic) / Überlappung / Abhängigkeit
   (Definitionen siehe book-of-work).
3. Konkrete Empfehlung formulieren — pro betroffenem Ticket genau eine Aktion:
   - **Merge:** welches Ticket geht in welches auf, mit Begründung
   - **Split:** zu großes Ticket → Epic + Kind-Tickets, jedes mit eigenem Scope
   - **Separieren:** bleibt eigenständig (eigener User-Value)
   - **Abgrenzen:** überlappende Verantwortung eindeutig je Ticket zuweisen
4. **Sequenzierung** ableiten: Foundation-Ticket(s) zuerst, was parallel laufen kann,
   was nachgelagert ist. Kritischen Pfad + Flaschenhals explizit benennen.
   Abhängigkeiten als Kette/Graph darstellen (`A ──▶ B ──▶ C`).
5. Bei Datenmodell-/Architektur-Tickets: prüfen ob nachgelagerte Tickets erst durch
   das Fundament sauber umsetzbar werden (z. B. Merge/Upsert braucht echten Store).
6. Empfehlung Stephan vorlegen; Umstrukturierung des Backlogs **erst nach Freigabe**.

Ergebnis im Ticket dokumentieren unter:
- **Bezug:** verlinkte IDs + Beziehungstyp + Aktion
- **Sequenzierung:** Abhängigkeitskette + kritischer Pfad
```

---

## 3) Optional: Memory-Regel

Als wiederkehrendes Prinzip lässt sich zusätzlich eine `feedback`-Memory anlegen:

> „Vor Ticket-Anlage und CR-Analyse immer überlappende Backlog-Tickets prüfen und
> Merge/Split/Abgrenzung + Sequenzierung vorschlagen; Umstrukturierung nur nach Freigabe."
