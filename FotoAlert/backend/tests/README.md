# FotoAlert Test-Harness

Das automatisierte Test-Harness der Pipeline (siehe `FotoAlert/PIPELINE.md` §3.3, Roadmap-Schritt 3).
Es macht die **Test-Phase des Orchestrators** ausführbar: statt Stephan curl-Schritte zu geben,
laufen die Akzeptanzkriterien als `pytest`-Tests im Sandbox.

## Kernidee: Akzeptanzkriterien werden zu dauerhaften Tests

Jedes abgeschlossene Ticket hinterlässt seine Akzeptanzkriterien als ausführbare Tests.
Die Summe aller Tests ist die **Vollsystem-Regression**: eine neue Änderung wird nicht nur
gegen ihr eigenes Feature geprüft, sondern gegen die AKs *aller* bisherigen Tickets — so
fallen Seiteneffekte auf, bevor sie live gehen.

**Konvention:** Jeder Test nennt im Docstring die Ticket-ID, deren AK er absichert. Neue
Tickets ergänzen ihre Tests nach demselben Muster (Datei nach Bereich, z. B.
`test_astronomy_regression.py`, `test_api_smoke.py`).

## Schichten

| Datei | Bereich | Läuft im Sandbox | Marker |
|-------|---------|------------------|--------|
| `test_astronomy_regression.py` | Berechnungen (Mond/Sonne/Geometrie/Brennweite) | ✅ immer (offline, deterministisch) | `offline`, `regression` |
| `test_api_smoke.py` | FastAPI-Endpoints gegen `data_dev` | ⏳ sobald Stack + Startup sandbox-sicher | `api`, `network` |

## Sicherheit: niemals Prod-Daten

`conftest.py` setzt `FOTOALERT_ENV=dev` **vor** allen Importen → der Store nutzt
`backend/data_dev/` (TASK-19). Tests fassen die Prod-DB nie an.

## Ausführen

```bash
# einmalig: Abhängigkeiten installieren
bash tests/bootstrap_sandbox.sh

# Standard: schnelle, netzunabhängige Offline-Regression
bash tests/run_tests.sh

# inkl. API-/Netzwerk-Tests
bash tests/run_tests.sh --all
```

## Rolle im Orchestrator

Die Test-Phase (`fotoalert-orchestrator`, Schritt 1) ruft `tests/run_tests.sh` in einem
isolierten Subagenten auf und gibt nur den **kompakten Report** (pass/fail je Test) zurück —
nicht die Testausgabe in den Orchestrator-Kontext. Bei rot: Ticket bleibt in `In Test`,
der Fehler geht an die Implementierungs-Phase zurück.

## Wie ein neues Ticket Tests beisteuert

1. In der Analyse-Phase werden die AKs messbar formuliert (`fotoalert-analyze`).
2. In der Impl-Phase wird pro AK, das automatisierbar ist, ein Test ergänzt — mit Ticket-ID
   im Docstring.
3. Der Test bleibt dauerhaft Teil der Regression. So wächst die Abdeckung mit jedem Ticket.
