# Skill-Änderungen: Test-First + PRODUCT.md

> Erstellt: 2026-06-28  
> Hintergrund: Stephan hat fehlende Regression nach Design-Änderung bemängelt (Doppel-Sektionen)
> und verlangt, dass Tests vor der Implementierung geschrieben werden.
>
> **Umsetzung:** Memory-Einträge `feedback_test_first` und `feedback_product_md` sind bereits aktiv
> (gelten sofort für alle zukünftigen Chats). Die folgenden Ergänzungen sollten zusätzlich in die
> Skill-Dateien eingebaut werden (Einstellungen → Capabilities), damit sie auch beim Orchestrator
> als expliziter Schritt sichtbar sind.

---

## 1. `fotoalert-analyze` — Ergänzung in Schritt 6 (Spec in BACKLOG.md)

**Wo einfügen:** Nach dem `Testplan:`-Block im Schritt 6, vor dem „Kanban-Artifact"-Hinweis.

```markdown
### Schritt 6b — Tests schreiben (Pflicht vor Weg-Gate)

**Tests entstehen in der Analyse-Phase — nie nach der Implementierung.**

Für jedes automatisierbare Akzeptanzkriterium:

1. **pytest-Testfall** anlegen in `backend/tests/test_<ticket-id>.py`:
   - Ticket-ID im Docstring
   - Konkrete Eingaben + erwartete Outputs aus den AKs
   - Testet gegen die Spec, nicht gegen die Implementierung

2. **Manuelle Testschritte** direkt im Ticket unter „Testplan → Manuell":
   - Browser-Pfad (URL + konkreter Klickpfad)
   - curl-Befehle mit erwarteter Response (Feldname + Wert)
   - Regressions-Matrix aus PRODUCT.md Sektion 12 heranziehen:
     Welcher Ticket-Typ liegt vor → welche Regressions-Sektionen müssen geprüft werden?

3. **Erst nach Test-Erstellung:** Weg-Gate an Stephan.

Warum: Tests die nach der Implementierung geschrieben werden, werden unbewusst auf die
Implementierung zugeschnitten — nicht auf die Anforderung. Reihenfolge: Spec → Tests → Impl.
```

---

## 2. `fotoalert-impl` — Ergänzung in Schritt 0

**Wo einfügen:** Am Anfang von Schritt 0, vor dem Annahmen-Check.

```markdown
### Schritt 0b — Tests vorhanden? (Pflicht vor erstem Edit)

Bevor Code geschrieben wird: prüfen ob die Tests aus der Analyse-Phase vorhanden sind.

```bash
ls backend/tests/test_<ticket-id>.py
```

- Datei vorhanden → weiter mit Schritt 0 (Annahmen-Check)
- Datei fehlt → Tests jetzt schreiben (analog fotoalert-analyze Schritt 6b), dann erst implementieren

**Regression-Scope bestimmen (Pflicht):**
PRODUCT.md Sektion 12 lesen. Welchem Ticket-Typ entspricht dieses Ticket?
Die Regressions-Matrix zeigt, welche App-Bereiche nach der Implementierung geprüft werden müssen —
nicht nur die neu implementierten.
```

**Außerdem:** In der Reihenfolge am Ticket-Ende (Schritt nach impl):

```markdown
**Reihenfolge am Ticket-Ende:**
0b. Tests vorhanden prüfen (vor Impl)
1. Implementierung
2. Tests ausführen (pytest für automatisierte AKs)
3. `fotoalert-test` (manuelle Testschritte + Regression gegen PRODUCT.md Sektion 12)
4. Test bestätigt ✅
5. PRODUCT.md aktualisieren (Sektionen + Changelog) — vor Done
6. `fotoalert-refactor`
7. `fotoalert-release`
8. Ticket → Done + Kanban sync
9. `retrospective`
```

---

## 3. `fotoalert-test` — Ergänzung nach Schritt 6

**Wo einfügen:** Nach Schritt 6 (Konkrete Testschritte), vor Schritt 6b.

```markdown
### Schritt 6c — Regressions-Check gegen PRODUCT.md (Pflicht)

PRODUCT.md (`FotoAlert/PRODUCT.md`) Sektion 12 (Regressions-Matrix) lesen.
Ticket-Typ bestimmen → zugehörige Regressions-Sektionen prüfen:

Beispiel: Ticket ist ein CSS/Theme-Change →
  Sektion 2 (Globale UI), Sektion 3 (Feed), Sektion 4 (Detail-Sheet) in Hell + Dunkel
  → Pflicht-Regression-Checklisten aus diesen Sektionen als konkrete Testschritte ausgeben.

**Konkret für den häufigsten Fall (CSS/UI-Änderung):**
- [ ] Alle 5 Tabs laden ohne weißen Block oder Absturz
- [ ] Kein Tab zeigt Inhalte doppelt
- [ ] Detail-Sheet: alle Sektionen vorhanden, keine Sektion doppelt
- [ ] Hell- und Dunkel-Modus: kein Kontrast-Problem (Weiß-auf-Weiß, unsichtbare Buttons)
- [ ] Close-Button in allen Sheets erreichbar (Safe Area)

Wenn Tests aus der Analyse-Phase vorhanden (`backend/tests/test_<ticket-id>.py`):
erst pytest ausführen, dann manuelle Schritte.
```

---

## 4. `fotoalert-release` — Ergänzung in Ticket-Abschluss-Reihenfolge

**Wo einfügen:** In der „Ticket-Abschluss-Reihenfolge" zwischen Health-Check und Done-Setzen.

```markdown
2b. **PRODUCT.md aktualisieren (Pflicht vor Done):**
    - Betroffene Sektion(en) in PRODUCT.md updaten (neue/geänderte Funktionen)
    - Sektion 13 (Offene Punkte): Ticket entfernen falls erledigt
    - Sektion 14 (Changelog): Zeile ergänzen: `| DATUM | TICKET-ID | 1-Satz-Beschreibung |`
    - Pfad: `FotoAlert/PRODUCT.md`
    - PRODUCT.md in denselben git-Commit wie BACKLOG.md aufnehmen
```
```
