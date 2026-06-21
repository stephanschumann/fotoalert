#!/usr/bin/env bash
# TASK-20 — Lokaler Runner für die Frontend-Testroutine (Option A, Playwright/Chromium).
#
# Ablauf:
#   1. Playwright-Chromium sicherstellen (idempotent).
#   2. Dev-Server (FOTOALERT_ENV=dev) erwarten/starten unter http://localhost:8000.
#   3. run_frontend_check.py gegen die laufende Instanz ausführen.
#
# Läuft IMMER gegen data_dev — nie gegen Prod. Schreibt KEINE Commits; Bugs als
# findings.json (+ Screenshots unter docs/qa-screenshots/<run>/). Optionaler lokaler
# BACKLOG-Merge über --backlog (bewusst nicht in CI).
#
# Hinweis: Im Sandbox ist Playwright evtl. nicht installierbar — dann nur lokal auf
# dem Mac sinnvoll. Die pure-Python-Selbsttests (test_reporter.py) laufen separat
# über run_tests.sh und brauchen weder Browser noch Server.
set -euo pipefail

cd "$(dirname "$0")/.."   # → backend/
export FOTOALERT_ENV=dev
export FOTOALERT_NO_BACKGROUND="${FOTOALERT_NO_BACKGROUND:-0}"
export FOTOALERT_HOST_PASSWORD="${FOTOALERT_HOST_PASSWORD:-test-host-pw}"
export FOTOALERT_USER_PASSWORD="${FOTOALERT_USER_PASSWORD:-test-user-pw}"
export FOTOALERT_AUTH_SECRET="${FOTOALERT_AUTH_SECRET:-test-secret}"

BASE_URL="${BASE_URL:-http://localhost:8000}"
FINDINGS_JSON="${FINDINGS_JSON:-$PWD/findings.json}"

echo "→ [1/3] Playwright-Chromium sicherstellen"
if ! python3 -c "import playwright" >/dev/null 2>&1; then
  echo "   playwright nicht installiert. Installiere: pip install playwright" >&2
  echo "   (im Sandbox evtl. nicht möglich — dann nur lokal auf dem Mac ausführen)" >&2
  exit 2
fi
python3 -m playwright install chromium

echo "→ [2/3] Dev-Server unter ${BASE_URL} erwarten/starten"
SERVER_PID=""
if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
  echo "   Server läuft bereits."
else
  echo "   Starte uvicorn (data_dev) im Hintergrund…"
  python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 >/tmp/fotoalert-frontend-server.log 2>&1 &
  SERVER_PID=$!
  for i in $(seq 1 30); do
    if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then break; fi
    sleep 1
  done
  if ! curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
    echo "   Server kam nicht hoch — siehe /tmp/fotoalert-frontend-server.log" >&2
    [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
    exit 1
  fi
fi

cleanup() { [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT

echo "→ [3/3] Frontend-Check ausführen"
python3 tests/frontend/run_frontend_check.py \
  --base-url "${BASE_URL}" \
  --password "${FOTOALERT_USER_PASSWORD}" \
  --findings-json "${FINDINGS_JSON}" \
  "$@"
