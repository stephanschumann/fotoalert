#!/usr/bin/env bash
# =============================================================================
# FotoAlert – Gemeinsame Prüfliste (TASK-117)
#
# EINE Beschreibung der Prüfungen, die GitHub (.github/workflows/deploy.yml) und
# der Probelauf von release.sh auf dem Mac gleichermaßen aufrufen. Ein hier
# ergänzter Prüfschritt läuft damit automatisch auf beiden Seiten mit (AK10).
#
# Aufruf:  bash FotoAlert/tools/pruefliste.sh [backend] [oberflaechen_check] [browser_tests]
#          ohne Angabe: alle drei Prüfblöcke (so ruft release.sh sie auf)
#   GitHub test-backend:  … pruefliste.sh backend
#   GitHub test-frontend: … pruefliste.sh oberflaechen_check browser_tests
#
# Einstellungen über Umgebungsvariablen (Standard = bisheriges GitHub-Verhalten):
#   PRUEFLISTE_PYTHON  Python-Interpreter            (Standard: python3)
#   PRUEFLISTE_PORT    Port des eigenen Testservers  (Standard: 8000)
#   PRUEFLISTE_ABLAGE  Ablage für Server-Log, Screenshots, Findings (Standard: /tmp)
# Geheimnisse (FOTOALERT_*_PASSWORD, FOTOALERT_AUTH_SECRET) kommen ausschließlich
# aus der Umgebung und werden nie als Aufruf-Parameter übergeben (AK15).
#
# Maschinenlesbare Ergebnis-Zeilen (wertet release.sh aus):
#   PRUEFLISTE block=<kennung> start
#   PRUEFLISTE block=<kennung> uebersprungen_test=<Test-ID> grund=<Grund>   (je übersprungenem Test, AK9a)
#   PRUEFLISTE block=<kennung> bestanden=<n> fehlgeschlagen=<n> uebersprungen=<n> [rot=<Test>]
#   PRUEFLISTE block=<kennung> dauer=<Sekunden>                              (je Prüfblock, AK13/AK14)
# Bewusst plattformneutral (macOS-bash 3.2 / BSD-Werkzeuge und Linux).
# =============================================================================
set -u

SELBST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJEKT_DIR="$(cd "$SELBST_DIR/.." && pwd)"          # FotoAlert/
BACKEND_DIR="$PROJEKT_DIR/backend"
PY="${PRUEFLISTE_PYTHON:-python3}"
PORT="${PRUEFLISTE_PORT:-8000}"
ABLAGE="${PRUEFLISTE_ABLAGE:-/tmp}"
# Adresse für Oberflächen-Check und Browser-Tests: Die App (web/index.html) schickt ihre API-Aufrufe
# bei Hostname „localhost“ fest an http://localhost:8000. Auf dem bisherigen GitHub-Port 8000 ist das
# derselbe Server (Verhalten wie bisher); auf einem eigenen Port (Probelauf, AK12) würde die App sonst
# einen fremden bzw. keinen Server ansprechen. Dort deshalb 127.0.0.1 → API über dieselbe Herkunft.
if [ "$PORT" = "8000" ]; then BASIS_HOST="localhost"; else BASIS_HOST="127.0.0.1"; fi
BASIS_URL="http://${BASIS_HOST}:${PORT}"
SERVER_LOG="$ABLAGE/fotoalert-ci-server.log"
SERVER_PID_DATEI="$ABLAGE/fotoalert-ci-server.pid"
BROWSER_ANFORDERUNG="$BACKEND_DIR/requirements-browser.txt"
# AK9a: Plugin, das jeden übersprungenen Test mit Grund meldet (ändert keinen Test)
PLUGIN_DIR="$SELBST_DIR/pruefliste_plugin"
PLUGIN_PYTHONPATH="$PLUGIN_DIR${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$ABLAGE"

BLOECKE="$*"
[ -z "$BLOECKE" ] && BLOECKE="backend oberflaechen_check browser_tests"
for B in $BLOECKE; do
    case "$B" in
        backend|oberflaechen_check|browser_tests) ;;
        *) echo "❌ Unbekannter Prüfblock: $B"; exit 2 ;;
    esac
done

GESAMT=0
SERVER_PID=""

# Limit offener Dateien wie bei GitHub (Linux-Runner: 65536) anheben — macOS startet oft mit 256,
# daran scheitern sonst Backend-Tests mit „Too many open files“ (AK1: dieselben Prüfungen wie GitHub).
DATEILIMIT_MIN=8192
dateilimit_anheben() {
    VORHER="$(ulimit -n)"
    [ "$VORHER" = "unlimited" ] && return 0
    [ "$VORHER" -ge 65536 ] && return 0
    HART="$(ulimit -Hn)"
    for W in 65536 24576 10240 "$DATEILIMIT_MIN" "$HART"; do
        [ "$W" = "unlimited" ] && continue
        [ "$W" -gt "$VORHER" ] || continue
        if [ "$HART" != "unlimited" ] && [ "$W" -gt "$HART" ]; then continue; fi
        ulimit -n "$W" 2>/dev/null && break
    done
    NACHHER="$(ulimit -n)"
    if [ "$NACHHER" != "$VORHER" ]; then
        echo "Limit offener Dateien angehoben: $VORHER → $NACHHER"
    fi
    if [ "$NACHHER" != "unlimited" ] && [ "$NACHHER" -lt "$DATEILIMIT_MIN" ]; then
        echo "⚠️  Limit offener Dateien nur $NACHHER (nötig mindestens $DATEILIMIT_MIN, GitHub: 65536) und nicht anhebbar –"
        echo "    Backend-Tests können mit „Too many open files“ scheitern. Abhilfe: ulimit -n $DATEILIMIT_MIN im Terminal."
    fi
    return 0
}
dateilimit_anheben

# Ersetzt die Werte der Geheimnisse in einem Datenstrom durch *** (AK15).
schwaerzen() {
    awk 'BEGIN { n = 0; split("FOTOALERT_HOST_PASSWORD FOTOALERT_USER_PASSWORD FOTOALERT_AUTH_SECRET", k, " ");
                 for (i in k) { v = ENVIRON[k[i]]; if (length(v) >= 4) { n++; s[n] = v } } }
         { z = $0; for (j = 1; j <= n; j++) { aus = "";
             while ((p = index(z, s[j])) > 0) { aus = aus substr(z, 1, p - 1) "***"; z = substr(z, p + length(s[j])) }
             z = aus z }
           print z; fflush() }'
}

# Meldet die vom Plugin erfassten übersprungenen Tests maschinenlesbar (AK9a).
uebersprungene_melden() {   # uebersprungene_melden <block> <datei>
    [ -f "$2" ] || return 0
    while IFS="$(printf '\t')" read -r ID GRUND; do
        [ -n "$ID" ] && echo "PRUEFLISTE block=$1 uebersprungen_test=$ID grund=$GRUND"
    done < "$2"
    return 0
}

ergebnis() {   # ergebnis <block> <bestanden> <fehlgeschlagen> <uebersprungen> [rot]
    Z="PRUEFLISTE block=$1 bestanden=$2 fehlgeschlagen=$3 uebersprungen=$4"
    [ -n "${5:-}" ] && Z="$Z rot=$5"
    echo "$Z"
    [ "$3" -gt 0 ] && GESAMT=1
    return 0
}

# Liest die Schlusszeile einer pytest-Ausgabe und meldet das Ergebnis.
pytest_ergebnis() {   # pytest_ergebnis <block> <ausgabedatei> <exitcode>
    SCHLUSS="$(grep -E '(passed|failed|skipped|error|errors|no tests ran)' "$2" | grep -E ' in [0-9.]+s' | tail -n 1)"
    zahl() { echo "$SCHLUSS" | grep -oE "[0-9]+ $1" | head -n 1 | grep -oE '^[0-9]+' || true; }
    BEST="$(zahl passed)"; FEHL="$(zahl failed)"; ERR="$(zahl 'error')"; SKIP="$(zahl skipped)"
    BEST="${BEST:-0}"; FEHL="${FEHL:-0}"; ERR="${ERR:-0}"; SKIP="${SKIP:-0}"
    FEHL=$((FEHL + ERR))
    if [ "$3" -ne 0 ] && [ "$3" -ne 5 ] && [ "$FEHL" -eq 0 ]; then FEHL=1; fi   # Absturz ohne Zählung
    ROT="$(grep -E '^(FAILED|ERROR) ' "$2" | head -n 1 | awk '{print $2}' | sed 's/.*:://')"
    [ "$FEHL" -gt 0 ] && [ -z "$ROT" ] && ROT="pytest_exitcode_$3"
    [ "$3" -ne 0 ] && GESAMT=1          # Exit-Code wie bisher bei GitHub (auch 5 = keine Tests)
    ergebnis "$1" "$BEST" "$FEHL" "$SKIP" "$ROT"
}

server_stoppen() {
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
        for _ in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$SERVER_PID" 2>/dev/null || break; sleep 0.5; done
        kill -9 "$SERVER_PID" 2>/dev/null || true
        SERVER_PID=""
        if [ -f "$SERVER_LOG" ]; then
            schwaerzen < "$SERVER_LOG" > "$SERVER_LOG.tmp" && cat "$SERVER_LOG.tmp" > "$SERVER_LOG"
            rm -f "$SERVER_LOG.tmp"
        fi
    fi
    rm -f "$SERVER_PID_DATEI"
}
trap server_stoppen EXIT
trap 'server_stoppen; exit 130' INT
trap 'server_stoppen; exit 143' TERM
trap 'server_stoppen; exit 129' HUP

# Eigener Testserver (leerer Datenbestand der jeweiligen Kopie, eigener Port, AK5/AK12).
server_starten() {
    [ -n "$SERVER_PID" ] && return 0
    ( cd "$BACKEND_DIR" && FOTOALERT_ENV="${FOTOALERT_ENV:-dev}" \
        FOTOALERT_NO_BACKGROUND="${FOTOALERT_NO_BACKGROUND:-1}" \
        exec "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$PORT" ) > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    echo "$SERVER_PID" > "$SERVER_PID_DATEI"
    for i in $(seq 1 30); do
        if curl -fsS "$BASIS_URL/health" >/dev/null 2>&1; then
            echo "✅ Testserver bereit nach ${i}s (Port $PORT)"
            return 0
        fi
        kill -0 "$SERVER_PID" 2>/dev/null || break
        sleep 1
    done
    echo "❌ Testserver nicht bereit (Port $PORT). Server-Log:"
    schwaerzen < "$SERVER_LOG" | tail -n 40
    return 1
}

# Browser-Werkzeug vorhanden und genau in der fest eingestellten Version (AK9/AK11)?
browser_werkzeug_pruefen() {   # gibt den Grund aus, wenn es nicht passt
    SOLL="$(grep -oE 'playwright==[0-9][0-9A-Za-z.]*' "$BROWSER_ANFORDERUNG" 2>/dev/null | head -n 1 | sed 's/playwright==//')"
    IST="$("$PY" -c 'from importlib.metadata import version; print(version("playwright"))' 2>/dev/null)"
    if [ -z "$IST" ]; then
        echo "Browser-Werkzeug (playwright) nicht installiert"
        return 1
    fi
    echo "Browser-Werkzeug: playwright $IST (fest eingestellt: ${SOLL:-?})" >&2
    if [ -n "$SOLL" ] && [ "$IST" != "$SOLL" ]; then
        echo "Browser-Werkzeug playwright $IST statt fest eingestellter $SOLL (pip install -r backend/requirements-browser.txt)"
        return 1
    fi
    return 0
}

# Dauer je Prüfblock (AK13/AK14): wird beim Start des nächsten Blocks bzw. nach der Schleife gemeldet,
# damit auch Blöcke mit `continue` erfasst sind.
BLOCK_LAUFEND=""; BLOCK_T0=0
block_dauer_melden() {
    [ -n "$BLOCK_LAUFEND" ] || return 0
    echo "PRUEFLISTE block=$BLOCK_LAUFEND dauer=$(( $(date +%s) - BLOCK_T0 ))"
    BLOCK_LAUFEND=""
    return 0
}

for B in $BLOECKE; do
    block_dauer_melden
    BLOCK_LAUFEND="$B"; BLOCK_T0="$(date +%s)"
    echo "PRUEFLISTE block=$B start"
    case "$B" in
        backend)
            # Wie bisher der GitHub-Job test-backend: ohne Geheimnisse und ohne Dev-Server-Umgebung.
            AUS="$ABLAGE/pruefliste-backend.txt"
            SKIPS="$ABLAGE/pruefliste-backend-uebersprungen.txt"; : > "$SKIPS"
            # Ohne Server wie bei GitHub: Browser-Tests im Backend-Block erreichen nie einen laufenden
            # (Entwicklungs-)Server — auch nicht Stephans eigenen auf Port 8000 (AK5/AK12).
            ( cd "$BACKEND_DIR" && env -u FOTOALERT_HOST_PASSWORD -u FOTOALERT_USER_PASSWORD \
                -u FOTOALERT_AUTH_SECRET -u FOTOALERT_ENV -u FOTOALERT_NO_BACKGROUND \
                -u FOTOALERT_E2E_URL -u FOTOALERT_E2E_HOST_PW -u FOTOALERT_E2E_USER_PW \
                FOTOALERT_TEST_BASE_URL="http://127.0.0.1:9" \
                PYTHONPATH="$PLUGIN_PYTHONPATH" PRUEFLISTE_UEBERSPRUNGEN_DATEI="$SKIPS" \
                "$PY" -m pytest tests/ -v -p pruefliste_uebersprungen ) 2>&1 | schwaerzen | tee "$AUS"
            RC=${PIPESTATUS[0]}
            uebersprungene_melden backend "$SKIPS" | schwaerzen
            pytest_ergebnis backend "$AUS" "$RC"
            ;;
        oberflaechen_check|browser_tests)
            GRUND="$(browser_werkzeug_pruefen)"
            if [ -n "$GRUND" ] && echo "$GRUND" | grep -q "nicht installiert"; then
                echo "⚠️  $GRUND – Prüfblock $B übersprungen"
                ergebnis "$B" 0 0 1 "$GRUND"; GESAMT=1; continue
            elif [ -n "$GRUND" ]; then
                echo "❌ $GRUND"
                ergebnis "$B" 0 1 0 "$GRUND"; continue
            fi
            if ! server_starten; then
                ergebnis "$B" 0 1 0 "testserver_start"; continue
            fi
            if [ "$B" = oberflaechen_check ]; then
                # Passwörter liest der Check aus der Umgebung (kein --password-Parameter mehr, AK15).
                AUS="$ABLAGE/pruefliste-oberflaechen-check.txt"
                ( cd "$BACKEND_DIR" && "$PY" tests/frontend/run_frontend_check.py \
                    --base-url "$BASIS_URL" \
                    --screenshot-root "$ABLAGE/qa-screenshots" \
                    --findings-json "$ABLAGE/findings.json" ) 2>&1 | schwaerzen | tee "$AUS"
                RC=${PIPESTATUS[0]}
                if [ "$RC" -eq 0 ]; then
                    ergebnis "$B" 1 0 0
                else
                    N="$(grep -cE '^  - \[' "$AUS" || true)"; [ "${N:-0}" -gt 0 ] || N=1
                    ROT="$(grep -E '^  - \[' "$AUS" | head -n 1 | sed 's/^  - \[[^]]*\] //; s/:.*//')"
                    ergebnis "$B" 0 "$N" 0 "${ROT:-run_frontend_check_exitcode_$RC}"
                fi
            else
                # BUG-100: die drei Playwright-Dateien laufen hier gegen den laufenden Testserver.
                AUS="$ABLAGE/pruefliste-browser-tests.txt"
                SKIPS="$ABLAGE/pruefliste-browser-uebersprungen.txt"; : > "$SKIPS"
                ( cd "$BACKEND_DIR" && FOTOALERT_TEST_BASE_URL="$BASIS_URL" \
                    PYTHONPATH="$PLUGIN_PYTHONPATH" PRUEFLISTE_UEBERSPRUNGEN_DATEI="$SKIPS" "$PY" -m pytest \
                    tests/test_bug_85.py "tests/test_bug-80.py" "tests/test_task-66.py" -v -p pruefliste_uebersprungen ) 2>&1 | schwaerzen | tee "$AUS"
                RC=${PIPESTATUS[0]}
                uebersprungene_melden browser_tests "$SKIPS" | schwaerzen
                pytest_ergebnis browser_tests "$AUS" "$RC"
            fi
            ;;
    esac
done
block_dauer_melden

server_stoppen
exit $GESAMT
