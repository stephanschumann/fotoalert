#!/bin/bash
# =============================================================================
# FotoAlert – Restore aus Backup-Repo
#
# Stellt die Nutzerdaten (custom_locations + location_overrides) aus dem
# privaten fotoalert-backup-Repo wieder her.
#
# Verwendung (auf dem Server):
#   ./deploy/restore.sh
#   ./deploy/restore.sh --commit abc1234   # bestimmten Commit wiederherstellen
#
# Voraussetzung:
#   - fotoalert-backup-Repo ist unter /opt/fotoalert/backup-repo geklont
#   - Deploy-Key ~/.ssh/fotoalert_backup ist konfiguriert
#
# TASK-18: Backup RPO≈0 + Restore
# =============================================================================
set -euo pipefail

APP_DIR="/opt/fotoalert/app"
BACKEND_DIR="$APP_DIR/FotoAlert/backend"
BACKUP_REPO="${FOTOALERT_BACKUP_REPO:-/opt/fotoalert/backup-repo}"
VENV="$APP_DIR/../venv/bin/python3"

echo "=== FotoAlert Restore – $(date '+%Y-%m-%d %H:%M:%S') ==="
echo "Backup-Repo: $BACKUP_REPO"
echo ""

# Backup-Repo prüfen
if [ ! -d "$BACKUP_REPO/.git" ]; then
    echo "❌ Backup-Repo nicht gefunden: $BACKUP_REPO"
    echo "   Setup aus TASK-18 Spec durchführen (git clone fotoalert-backup)."
    exit 1
fi

# Neuesten Stand holen (oder bestimmten Commit auschecken)
cd "$BACKUP_REPO"
if [ "${1:-}" = "--commit" ] && [ -n "${2:-}" ]; then
    COMMIT="${2}"
    echo ">>> Checkout Commit: $COMMIT"
    git fetch
    git checkout "$COMMIT" -- custom_locations.json location_overrides.json
else
    echo ">>> Aktuellen Stand holen (git pull)..."
    git pull
fi

# Stand anzeigen
echo ""
echo "Letzter Backup-Commit:"
git log --oneline -3
echo ""

# Sicherung der aktuellen DB (falls vorhanden)
DB_PATH="$BACKEND_DIR/data/fotoalert.db"
if [ -f "$DB_PATH" ]; then
    BACKUP_COPY="$DB_PATH.before-restore-$(date +%Y%m%d_%H%M%S)"
    echo ">>> Aktuelle DB sichern → $BACKUP_COPY"
    cp "$DB_PATH" "$BACKUP_COPY"
fi

# JSON-Dateien in data/ kopieren
echo ">>> JSON-Dateien nach backend/data/ kopieren..."
cp "$BACKUP_REPO/custom_locations.json"   "$BACKEND_DIR/data/custom_locations.json"
cp "$BACKUP_REPO/location_overrides.json" "$BACKEND_DIR/data/location_overrides.json"

# In SQLite importieren (Migration)
echo ">>> SQLite-Migration (idempotent)..."
cd "$BACKEND_DIR"

# Bestehende DB entfernen damit migrate_json_to_sqlite.py frisch importiert
# (Migration ist INSERT OR IGNORE — bestehende IDs werden übersprungen)
# Wenn die DB beschädigt ist, umbenennen statt löschen:
if [ -f "$DB_PATH" ]; then
    python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$DB_PATH')
    result = conn.execute('PRAGMA integrity_check').fetchone()[0]
    conn.close()
    if result != 'ok':
        import os, shutil
        shutil.move('$DB_PATH', '${DB_PATH}.corrupt-$(date +%s)')
        print('Beschädigte DB verschoben, starte mit leerer DB.')
except Exception as e:
    import os
    os.rename('$DB_PATH', '${DB_PATH}.error-$(date +%s)')
    print(f'DB-Fehler: {e} — DB verschoben.')
"
fi

"$VENV" migrate_json_to_sqlite.py

# Integrity-Check
echo ""
echo ">>> Integrity Check..."
INTEGRITY=$(python3 -c "
import sqlite3
conn = sqlite3.connect('data/fotoalert.db')
print(conn.execute('PRAGMA integrity_check').fetchone()[0])
")
if [ "$INTEGRITY" != "ok" ]; then
    echo "❌ Integrity Check fehlgeschlagen: $INTEGRITY"
    exit 1
fi

# Einträge anzeigen
python3 -c "
import sqlite3
conn = sqlite3.connect('data/fotoalert.db')
cl = conn.execute('SELECT COUNT(*) FROM custom_locations').fetchone()[0]
ov = conn.execute('SELECT COUNT(*) FROM location_overrides').fetchone()[0]
print(f'custom_locations:   {cl} Einträge')
print(f'location_overrides: {ov} Einträge')
"

echo ""
echo "✅ Restore abgeschlossen."
echo "   Service neu starten: sudo systemctl restart fotoalert.service"
