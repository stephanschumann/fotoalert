#!/bin/bash
# =============================================================================
# FotoAlert – Manueller Rollback auf vorherigen Commit
# Verwendung: ssh fotoalert@SERVER "bash /opt/fotoalert/app/FotoAlert/deploy/rollback.sh"
# Oder mit Commit-Hash: ... rollback.sh abc1234
# =============================================================================
set -euo pipefail

APP_DIR="/opt/fotoalert/app"
HEALTH_URL="http://localhost:8000/health"
TARGET_COMMIT="${1:-HEAD~1}"  # Standard: ein Commit zurück

echo "=== FotoAlert Rollback – $(date '+%Y-%m-%d %H:%M:%S') ==="
cd "$APP_DIR"

CURRENT=$(git rev-parse HEAD)
TARGET=$(git rev-parse "$TARGET_COMMIT")

echo "Aktuell:  $CURRENT"
echo "Rollback: $TARGET"
echo ""

read -rp "Rollback durchführen? [j/N] " confirm
if [[ "$confirm" != "j" && "$confirm" != "J" ]]; then
    echo "Abgebrochen."
    exit 0
fi

git checkout "$TARGET" -- .
sudo systemctl restart fotoalert.service
sleep 4

HTTP_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Rollback erfolgreich auf $TARGET"
else
    echo "❌ Service antwortet nicht (HTTP $HTTP_STATUS). Logs:"
    sudo journalctl -u fotoalert -n 30
fi
