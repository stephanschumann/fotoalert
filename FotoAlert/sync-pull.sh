#!/usr/bin/env bash
# =============================================================================
# FotoAlert – Sync-Pull: Server-Daten auf den Mac holen
#
# Verwendung:
#   ./sync-pull.sh
#
# Was das Skript tut:
#   Holt fotoalert.db vom Produktionsserver per scp in backend/data_dev/.
#   Vor Dev-Sessionen aufrufen, wenn auf der Production-App
#   (fotoalert.stephanschumann.com) Locations bearbeitet oder hinzugefügt wurden.
#
# Danach den lokalen Server mit Dev-Isolation starten:
#   FOTOALERT_ENV=dev uvicorn main:app --reload --port 8000
#
# Hinweis:
#   Der Server ist die Single Source of Truth für Location-Daten.
#   FOTOALERT_ENV=dev verhindert, dass lokale Änderungen die Prod-DB überschreiben.
#   Daten-Bearbeitungen in Prod immer über fotoalert.stephanschumann.com.
#
# TASK-17/TASK-19: Setzt TASK-17-Deployment auf dem Server voraus (SQLite-DB vorhanden).
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DEV_DIR="$SCRIPT_DIR/backend/data_dev"

SERVER_USER="fotoalert"
SERVER_IP="167.233.138.36"
SERVER_DATA="/opt/fotoalert/app/FotoAlert/backend/data"
SSH_KEY="$HOME/.ssh/fotoalert_deploy"

echo "=== FotoAlert Sync-Pull ==="
echo "Server: $SERVER_USER@$SERVER_IP"
echo ""

# SSH-Key prüfen
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH-Key nicht gefunden: $SSH_KEY"
    echo "   Stelle sicher, dass der Deploy-Key eingerichtet ist."
    exit 1
fi

# Lokalen Stand anzeigen
echo "Lokaler Stand (data_dev/):"
ls -lh "$DATA_DEV_DIR/fotoalert.db" 2>/dev/null || echo "  fotoalert.db: (nicht vorhanden)"
echo ""

# Server-Stand anzeigen
echo "Server-Stand:"
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" \
    "ls -lh '$SERVER_DATA/fotoalert.db' 2>/dev/null || echo '  fotoalert.db: (nicht gefunden — TASK-17 noch nicht deployed?)'"
echo ""

read -rp "Prod-DB in data_dev/ übernehmen? [j/N] " CONFIRM
if [[ "$CONFIRM" != "j" && "$CONFIRM" != "J" ]]; then
    echo "Abgebrochen."
    exit 0
fi

# data_dev/ anlegen falls nicht vorhanden
mkdir -p "$DATA_DEV_DIR"

# DB holen
echo ""
echo ">>> fotoalert.db holen → backend/data_dev/..."
scp -i "$SSH_KEY" \
    "$SERVER_USER@$SERVER_IP:$SERVER_DATA/fotoalert.db" \
    "$DATA_DEV_DIR/fotoalert.db"

echo ""
echo "✅ Sync abgeschlossen. Mac hat jetzt den aktuellen Prod-Datenstand in data_dev/."
echo ""
echo "   Lokalen Dev-Server starten mit:"
echo "   cd backend && FOTOALERT_ENV=dev uvicorn main:app --reload --port 8000"
echo ""

# Einträge zählen
python3 - <<'EOF'
import sqlite3, sys
try:
    conn = sqlite3.connect("backend/data_dev/fotoalert.db")
    cl = conn.execute("SELECT COUNT(*) FROM custom_locations").fetchone()[0]
    ov = conn.execute("SELECT COUNT(*) FROM location_overrides").fetchone()[0]
    print(f"   custom_locations:   {cl} Einträge")
    print(f"   location_overrides: {ov} Einträge")
except Exception as e:
    print(f"   (Zählen fehlgeschlagen: {e})")
EOF
