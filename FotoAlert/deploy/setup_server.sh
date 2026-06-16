#!/bin/bash
# =============================================================================
# FotoAlert – Einmaliges Server-Setup auf Hetzner CX22 (Ubuntu 22.04 LTS)
# =============================================================================
# Ausführen als root: ssh root@YOUR_SERVER_IP "bash -s" < setup_server.sh
#
# Voraussetzungen:
#   1. Hetzner-Konto anlegen: https://www.hetzner.com/cloud
#   2. Server erstellen: CX22 | Ubuntu 22.04 | Frankfurt | SSH-Key hinterlegen
#   3. Domain oder Subdomain auf Server-IP zeigen (vor HTTPS-Setup erledigen!)
#      Option A: Eigene .de-Domain (~1€/Jahr bei IONOS/Strato/Hetzner)
#      Option B: Kostenlose Subdomain bei desec.io (z.B. fotoalert.dedyn.io)
#
# Nach dem Setup: App erreichbar unter https://YOUR_DOMAIN
# =============================================================================

set -euo pipefail

# ── Konfiguration ────────────────────────────────────────────────────────────
DOMAIN="fotoalert.stephanschumann.com"
CODEBERG_USER="stephanschumann"  # GitHub-Benutzername
REPO_NAME="fotoalert"          # Name des Codeberg-Repositories
APP_DIR="/opt/fotoalert/app"
VENV_DIR="/opt/fotoalert/venv"
DATA_DIR="/opt/fotoalert/app/FotoAlert/backend/data"
SERVICE_USER="fotoalert"
# ─────────────────────────────────────────────────────────────────────────────

echo "=== FotoAlert Server-Setup ==="
echo "Domain: $DOMAIN"
echo "Server: $(hostname)"

# ── System-Updates ───────────────────────────────────────────────────────────
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq git python3 python3-pip python3-venv curl wget unzip \
    python3.12 python3.12-venv python3.12-dev

# ── Caddy installieren (automatisches HTTPS via Let's Encrypt) ───────────────
if ! command -v caddy &> /dev/null; then
    echo ">>> Caddy installieren..."
    apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
        | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
        | tee /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -qq
    apt-get install -y -qq caddy
    echo ">>> Caddy installiert: $(caddy version)"
fi

# ── App-User anlegen ─────────────────────────────────────────────────────────
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home /opt/fotoalert --create-home "$SERVICE_USER"
    echo ">>> User '$SERVICE_USER' angelegt."
fi

# ── SSH-Key für Deploy vorbereiten ───────────────────────────────────────────
mkdir -p /opt/fotoalert/.ssh
chmod 700 /opt/fotoalert/.ssh
touch /opt/fotoalert/.ssh/authorized_keys
chmod 600 /opt/fotoalert/.ssh/authorized_keys
chown -R "$SERVICE_USER:$SERVICE_USER" /opt/fotoalert/.ssh
echo ">>> SSH-Verzeichnis vorbereitet."
echo "    WICHTIG: Deploy-Public-Key in /opt/fotoalert/.ssh/authorized_keys eintragen!"
echo "    (Schritt 'Codeberg Deploy Key' weiter unten)"

# ── Repository klonen ────────────────────────────────────────────────────────
mkdir -p /opt/fotoalert
if [ ! -d "$APP_DIR/.git" ]; then
    echo ">>> Repository klonen..."
    git clone "https://github.com/$CODEBERG_USER/$REPO_NAME.git" "$APP_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"
else
    echo ">>> Repository bereits vorhanden, überspringe Clone."
fi

# ── Python venv + Dependencies ───────────────────────────────────────────────
echo ">>> Python venv erstellen (Python 3.12)..."
# Ubuntu 26.04 hat Python 3.14 als Standard; astropy und pydantic-core
# unterstützen 3.14 noch nicht – deshalb explizit 3.12 verwenden.
python3.12 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$APP_DIR/FotoAlert/backend/requirements.txt"
echo ">>> Dependencies installiert."

# ── Persistente Daten-Verzeichnisse anlegen ──────────────────────────────────
echo ">>> Daten-Verzeichnisse anlegen..."
mkdir -p "$DATA_DIR/cache"
# Startwerte für leere JSON-Dateien (werden beim ersten Precompute befüllt)
[ ! -f "$DATA_DIR/custom_locations.json" ]    && echo "[]" > "$DATA_DIR/custom_locations.json"
[ ! -f "$DATA_DIR/location_overrides.json" ]  && echo "{}" > "$DATA_DIR/location_overrides.json"
chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"

# ── Skyfield-Ephemeridendatei herunterladen ──────────────────────────────────
BSP_FILE="$APP_DIR/FotoAlert/backend/de421.bsp"
if [ ! -f "$BSP_FILE" ]; then
    echo ">>> Skyfield-Ephemeridendatei herunterladen (de421.bsp, ~17 MB)..."
    curl -L -o "$BSP_FILE" \
        "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de421.bsp"
    chown "$SERVICE_USER:$SERVICE_USER" "$BSP_FILE"
fi

# ── systemd-Services installieren ────────────────────────────────────────────
echo ">>> systemd Services installieren..."
DEPLOY_DIR="$APP_DIR/FotoAlert/deploy"

cp "$DEPLOY_DIR/fotoalert.service"              /etc/systemd/system/
cp "$DEPLOY_DIR/fotoalert-precompute.service"   /etc/systemd/system/
cp "$DEPLOY_DIR/fotoalert-precompute.timer"     /etc/systemd/system/

# Platzhalter im Service-File ersetzen
sed -i "s|__APP_DIR__|$APP_DIR|g"   /etc/systemd/system/fotoalert.service
sed -i "s|__VENV_DIR__|$VENV_DIR|g" /etc/systemd/system/fotoalert.service
sed -i "s|__APP_DIR__|$APP_DIR|g"   /etc/systemd/system/fotoalert-precompute.service
sed -i "s|__VENV_DIR__|$VENV_DIR|g" /etc/systemd/system/fotoalert-precompute.service

systemctl daemon-reload
systemctl enable --now fotoalert.service
systemctl enable --now fotoalert-precompute.timer

echo ">>> Services gestartet."

# ── Caddy konfigurieren ──────────────────────────────────────────────────────
echo ">>> Caddy konfigurieren..."
cp "$DEPLOY_DIR/Caddyfile" /etc/caddy/Caddyfile
sed -i "s|YOUR_DOMAIN|$DOMAIN|g" /etc/caddy/Caddyfile
systemctl reload caddy || systemctl restart caddy
echo ">>> Caddy konfiguriert."

# ── Erster Precompute-Lauf ────────────────────────────────────────────────────
echo ">>> Ersten Precompute-Lauf starten (kann einige Minuten dauern)..."
sudo -u "$SERVICE_USER" bash -c "
    cd '$APP_DIR/FotoAlert/backend' && \
    '$VENV_DIR/bin/python3' precompute.py --feed-only
"
echo ">>> Erster Precompute abgeschlossen."

# ── Health-Check ─────────────────────────────────────────────────────────────
sleep 3
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    echo ""
    echo "✅ FotoAlert läuft erfolgreich!"
    echo "   Lokal: http://localhost:8000"
    echo "   Öffentlich: https://$DOMAIN (sobald DNS propagiert ist)"
    echo ""
    echo "📱 Nächste Schritte:"
    echo "   1. https://$DOMAIN im iPhone Safari öffnen"
    echo "   2. 'Zum Home-Bildschirm hinzufügen' → App-Icon erscheint"
    echo "   3. Codeberg Deploy-Key einrichten (siehe TASK-14)"
else
    echo ""
    echo "⚠️  Health-Check fehlgeschlagen (HTTP $HTTP_STATUS). Logs prüfen:"
    echo "   journalctl -u fotoalert -n 50"
fi
