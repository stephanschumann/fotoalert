#!/bin/bash
# =============================================================================
# FotoAlert – Deploy-Script (läuft auf dem Hetzner-Server)
# Aufgerufen von: Forgejo Actions via SSH
# =============================================================================
set -euo pipefail

APP_DIR="/opt/fotoalert/app"
VENV_DIR="/opt/fotoalert/venv"
BACKEND_DIR="$APP_DIR/FotoAlert/backend"
SW_FILE="$APP_DIR/FotoAlert/web/sw.js"
HEALTH_URL="http://localhost:8000/health"
ROLLBACK_COMMITS=1  # Wie viele Commits zurück beim Rollback

echo "=== FotoAlert Deploy – $(date '+%Y-%m-%d %H:%M:%S') ==="
cd "$APP_DIR"

# ── 1. Aktuellen Stand sichern (für Rollback) ────────────────────────────────
PREV_COMMIT=$(git rev-parse HEAD)
echo "Aktueller Stand: $PREV_COMMIT"

# ── 2. Neuesten Code holen ───────────────────────────────────────────────────
echo ">>> git pull..."
git pull --ff-only origin main

NEW_COMMIT=$(git rev-parse HEAD)
if [ "$PREV_COMMIT" = "$NEW_COMMIT" ]; then
    echo ">>> Kein neuer Code. Deploy übersprungen."
    exit 0
fi
echo "Neuer Stand: $NEW_COMMIT"

# ── 3. Service Worker Cache-Name aktualisieren ───────────────────────────────
# Jeder Deploy bekommt einen eindeutigen Timestamp-basierten Cache-Namen.
# Das stellt sicher, dass alle Clients beim nächsten Laden den neuen SW installieren.
DEPLOY_TS=$(date +%Y%m%d%H%M)
echo ">>> SW Cache-Name: fotoalert-$DEPLOY_TS"
sed -i "s/const CACHE_NAME = 'fotoalert-[^']*'/const CACHE_NAME = 'fotoalert-$DEPLOY_TS'/" "$SW_FILE"

# ── 4. Python-Dependencies prüfen und aktualisieren ─────────────────────────
echo ">>> Dependencies prüfen..."
"$VENV_DIR/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"

# ── 5. Service neu starten ───────────────────────────────────────────────────
echo ">>> Service neustarten..."
sudo systemctl restart fotoalert.service
sleep 4  # Kurz warten bis uvicorn bereit ist

# ── 6. Health-Check ──────────────────────────────────────────────────────────
echo ">>> Health-Check..."
HTTP_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" != "200" ]; then
    echo "❌ Health-Check fehlgeschlagen (HTTP $HTTP_STATUS) – Rollback wird eingeleitet..."
    git checkout "$PREV_COMMIT" -- .
    # SW-File auch zurücksetzen
    git checkout "$PREV_COMMIT" -- FotoAlert/web/sw.js 2>/dev/null || true
    sudo systemctl restart fotoalert.service
    sleep 3
    ROLLBACK_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
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
