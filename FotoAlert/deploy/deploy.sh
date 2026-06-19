#!/bin/bash
# =============================================================================
# FotoAlert – Deploy-Script (läuft auf dem Hetzner-Server)
# Aufgerufen von: GitHub Actions via SSH
# =============================================================================
set -euo pipefail

APP_DIR="/opt/fotoalert/app"
VENV_DIR="/opt/fotoalert/venv"
BACKEND_DIR="$APP_DIR/FotoAlert/backend"
DEPLOY_DIR="$APP_DIR/FotoAlert/deploy"
SW_FILE="$APP_DIR/FotoAlert/web/sw.js"
HEALTH_URL="http://localhost:8000/health"
ROLLBACK_COMMITS=1  # Wie viele Commits zurück beim Rollback

echo "=== FotoAlert Deploy – $(date '+%Y-%m-%d %H:%M:%S') ==="
cd "$APP_DIR"

# ── 1. Code holen + Re-exec ──────────────────────────────────────────────────
# Bash cached das Script beim Start. Wenn deploy.sh selbst durch git pull
# aktualisiert wird, läuft trotzdem die alte Version — bis zum Re-exec.
# Lösung: Nach dem Pull immer re-exec, damit Bash die neue Version lädt.
# FOTOALERT_DID_PULL verhindert eine Endlosschleife.
if [ "${FOTOALERT_DID_PULL:-0}" = "0" ]; then
    PREV_COMMIT=$(git rev-parse HEAD)
    echo "Aktueller Stand: $PREV_COMMIT"

    echo ">>> Lokale Änderungen zurücksetzen (git reset --hard HEAD)..."
    git reset --hard HEAD

    echo ">>> git pull..."
    git pull --ff-only origin main

    NEW_COMMIT=$(git rev-parse HEAD)
    if [ "$PREV_COMMIT" = "$NEW_COMMIT" ]; then
        echo ">>> Kein neuer Code. Deploy übersprungen."
        exit 0
    fi
    echo "Neuer Stand: $NEW_COMMIT"

    # Re-exec mit ggf. aktualisierter deploy.sh
    echo ">>> Re-exec mit aktueller deploy.sh..."
    export FOTOALERT_DID_PULL=1
    export FOTOALERT_PREV_COMMIT="$PREV_COMMIT"
    export FOTOALERT_NEW_COMMIT="$NEW_COMMIT"
    exec bash "$DEPLOY_DIR/deploy.sh"
else
    # Zweiter Lauf nach Re-exec: Pull bereits erledigt, Commits aus Env lesen
    PREV_COMMIT="${FOTOALERT_PREV_COMMIT}"
    NEW_COMMIT="${FOTOALERT_NEW_COMMIT}"
    echo "Aktueller Stand: $PREV_COMMIT"
    echo "Neuer Stand:     $NEW_COMMIT"
fi

# ── 2b. Nicht-öffentliche Dateien aus web/ entfernen ─────────────────────────
WEB_DIR="$APP_DIR/FotoAlert/web"
echo ">>> Nicht-öffentliche Dateien aus web/ entfernen..."
rm -f "$WEB_DIR/kanban.html" \
      "$WEB_DIR/BACKLOG.md"
find "$WEB_DIR" -maxdepth 1 -name "*.md" -delete
find "$WEB_DIR" -maxdepth 1 -name "*.html" ! -name "index.html" -delete
echo ">>> web/ bereinigt."

# ── 3. Service Worker Cache-Name aktualisieren ───────────────────────────────
DEPLOY_TS=$(date +%Y%m%d%H%M)
echo ">>> SW Cache-Name: fotoalert-$DEPLOY_TS"
sed -i "s/const CACHE_NAME = 'fotoalert-[^']*'/const CACHE_NAME = 'fotoalert-$DEPLOY_TS'/" "$SW_FILE"

# ── 4. Python-Dependencies prüfen und aktualisieren ─────────────────────────
echo ">>> Dependencies prüfen..."
"$VENV_DIR/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"

# ── 5. systemd-Units aktualisieren ──────────────────────────────────────────
echo ">>> systemd-Units aktualisieren..."
sudo systemctl daemon-reload
sudo systemctl restart fotoalert-precompute.timer
echo ">>> Timer neu geladen: $(systemctl show fotoalert-precompute.timer --property=OnCalendar --value)"

echo ">>> App-Service neustarten..."
sudo systemctl restart fotoalert.service

# ── 6. Health-Check (Retry-Loop, max 25s) ────────────────────────────────────
echo ">>> Health-Check..."
HTTP_STATUS="000"
for i in 1 2 3 4 5; do
    sleep 5
    HTTP_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_STATUS" = "200" ]; then break; fi
    echo "    Versuch $i: HTTP $HTTP_STATUS – warte..."
done

if [ "$HTTP_STATUS" != "200" ]; then
    echo "❌ Health-Check fehlgeschlagen (HTTP $HTTP_STATUS) – Rollback wird eingeleitet..."
    git checkout "$PREV_COMMIT" -- .
    git checkout "$PREV_COMMIT" -- FotoAlert/web/sw.js 2>/dev/null || true
    sudo systemctl restart fotoalert.service

    # Rollback-Health-Check ebenfalls mit Retry-Loop (max 15s)
    ROLLBACK_STATUS="000"
    for i in 1 2 3; do
        sleep 5
        ROLLBACK_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
        if [ "$ROLLBACK_STATUS" = "200" ]; then break; fi
        echo "    Rollback-Versuch $i: HTTP $ROLLBACK_STATUS – warte..."
    done

    if [ "$ROLLBACK_STATUS" = "200" ]; then
        echo "⚠️  Rollback erfolgreich auf $PREV_COMMIT"
    else
        echo "❌ Rollback ebenfalls fehlgeschlagen! Manueller Eingriff nötig."
        echo "   journalctl -u fotoalert -n 100"
    fi
    exit 1
fi

echo ""
echo "✅ Deploy erfolgreich!"
echo "   Commit: $NEW_COMMIT"
echo "   SW-Cache: fotoalert-$DEPLOY_TS"
echo "   Zeit: $(date '+%Y-%m-%d %H:%M:%S')"
