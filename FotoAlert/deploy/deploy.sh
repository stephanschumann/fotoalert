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

# ── 1. Aktuellen Stand sichern (für Rollback) ────────────────────────────────
PREV_COMMIT=$(git rev-parse HEAD)
echo "Aktueller Stand: $PREV_COMMIT"

# ── 2. Neuesten Code holen ───────────────────────────────────────────────────
# Alle lokalen Änderungen an Tracked-Files zurücksetzen (sw.js etc.).
# Gitignored Dateien (custom_locations.json, cache/, location_overrides.json) bleiben unberührt.
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

# ── 2b. Nicht-öffentliche Dateien aus web/ entfernen ─────────────────────────
# Diese Dateien sollen nie öffentlich über den Webserver erreichbar sein.
WEB_DIR="$APP_DIR/FotoAlert/web"
echo ">>> Nicht-öffentliche Dateien aus web/ entfernen..."
rm -f "$WEB_DIR/kanban.html" \
      "$WEB_DIR/BACKLOG.md"
# Alle .md-Dateien und temporäre HTML-Dateien (außer index.html) entfernen
find "$WEB_DIR" -maxdepth 1 -name "*.md" -delete
find "$WEB_DIR" -maxdepth 1 -name "*.html" ! -name "index.html" -delete
echo ">>> web/ bereinigt."

# ── 3. Service Worker Cache-Name aktualisieren ───────────────────────────────
# Jeder Deploy bekommt einen eindeutigen Timestamp-basierten Cache-Namen.
# Das stellt sicher, dass alle Clients beim nächsten Laden den neuen SW installieren.
DEPLOY_TS=$(date +%Y%m%d%H%M)
echo ">>> SW Cache-Name: fotoalert-$DEPLOY_TS"
sed -i "s/const CACHE_NAME = 'fotoalert-[^']*'/const CACHE_NAME = 'fotoalert-$DEPLOY_TS'/" "$SW_FILE"

# ── 4. Python-Dependencies prüfen und aktualisieren ─────────────────────────
echo ">>> Dependencies prüfen..."
"$VENV_DIR/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"

# ── 5. systemd-Units aktualisieren ──────────────────────────────────────────
# Service- und Timer-Dateien werden einmalig per Root-Setup installiert.
# Deploy überschreibt sie nicht (sudo cp nicht in fotoalert-Sudoers-Whitelist).
# Nur daemon-reload + Timer-Neustart, damit der Timer weiterläuft.
echo ">>> systemd-Units aktualisieren..."
sudo systemctl daemon-reload
sudo systemctl restart fotoalert-precompute.timer
echo ">>> Timer neu geladen: $(systemctl show fotoalert-precompute.timer --property=OnCalendar --value)"

echo ">>> App-Service neustarten..."
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
