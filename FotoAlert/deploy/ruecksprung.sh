#!/bin/bash
# =============================================================================
# FotoAlert – Automatischer Rücksprung auf die zuletzt bestätigte Version (TASK-118)
#
# Läuft auf dem Hetzner-Server, nicht-interaktiv (keine Rückfrage).
# Aufgerufen von: GitHub Actions via SSH (nach rotem Live-Check) und von deploy.sh
# (nach fehlgeschlagener Statusabfrage) – beide nutzen dieselbe Mechanik.
#
# Verwendung:
#   ruecksprung.sh bestaetigen [--nur-wenn-keine-marke]
#       Vermerkt die gerade laufende Version als „zuletzt bestätigt“ (Live-Check bzw.
#       Vorab-Probe grün). Mit --nur-wenn-keine-marke nur, wenn es noch keine Marke gibt
#       (allerster Lauf, AK24).
#   ruecksprung.sh zurueck
#       Holt die zuletzt bestätigte Version zurück (nicht einfach die vorherige, AK15/AK16):
#       Dateien + gespeicherter Stand des Servers (git) → Service-Worker-Cache-Name neu stempeln →
#       Webserver-Einstellungen angleichen und neu laden → App neu starten → Statusabfrage.
#       Nur die App wird zurückgesetzt, nie die Datenbank (AK21) und keine Python-Pakete.
#       Scheitert der Rücksprung, endet er mit „Rücksprung fehlgeschlagen – manueller Eingriff
#       nötig“ und Rückgabewert 1; es folgt nie ein weiterer automatischer Rücksprung (AK22).
#
# Die Marke „zuletzt bestätigt“ ist eine kleine Textdatei AUSSERHALB der Datenbank und außerhalb
# des Git-Ordners (Standard: /opt/fotoalert/zuletzt_bestaetigt.txt, erste Zeile = Commit).
#
# Einstellungen (Umgebungsvariablen, alle optional – für Tests und Sonderfälle):
#   FOTOALERT_APP_DIR        App-Ordner (Standard /opt/fotoalert/app)
#   FOTOALERT_MARKE_DATEI    Marken-Datei (Standard /opt/fotoalert/zuletzt_bestaetigt.txt)
#   FOTOALERT_HEALTH_URL     Statusabfrage (Standard http://localhost:8000/health)
#   FOTOALERT_CADDY_LIVE     laufende Webserver-Einstellungen (Standard /etc/caddy/Caddyfile)
#   FOTOALERT_RUECKFALL_COMMIT  nur wenn es noch keine Marke gibt: Ersatzziel (deploy.sh übergibt
#                            hier den Stand vor der Veröffentlichung – altes Verhalten bis zur
#                            ersten Bestätigung)
# Befehle (sudo, systemctl, caddy, curl, git …) werden über den Suchpfad aufgerufen.
#
# Rückgabewert: 0 = gelungen · 1 = fehlgeschlagen · 2 = falscher Aufruf
# Maschinenlesbare Zeilen am Ende (für die Meldung im GitHub-Lauf):
#   RUECKSPRUNG_ERGEBNIS=gelungen|fehlgeschlagen
#   RUECKSPRUNG_VON_VERSION=<App-Version, die zurückgenommen wurde>
#   RUECKSPRUNG_AUF_VERSION=<App-Version, die jetzt läuft bzw. laufen sollte>
# =============================================================================
set -euo pipefail

APP_DIR="${FOTOALERT_APP_DIR:-/opt/fotoalert/app}"
MARKE_DATEI="${FOTOALERT_MARKE_DATEI:-/opt/fotoalert/zuletzt_bestaetigt.txt}"
HEALTH_URL="${FOTOALERT_HEALTH_URL:-http://localhost:8000/health}"
CADDY_LIVE="${FOTOALERT_CADDY_LIVE:-/etc/caddy/Caddyfile}"
CADDY_DOMAIN="fotoalert.stephanschumann.com"
CADDY_CANDIDATE="/tmp/fotoalert_caddyfile_candidate"
SW_DATEI="FotoAlert/web/sw.js"
INDEX_DATEI="FotoAlert/web/index.html"
MELDUNG_FEHLGESCHLAGEN="Rücksprung fehlgeschlagen – manueller Eingriff nötig"

# App-Version aus index.html – aus einem Commit (Argument) oder aus den Dateien auf der Platte
version_von_commit() {
    git show "$1:$INDEX_DATEI" 2>/dev/null \
        | sed -n "s/.*const APP_VERSION = '\([^']*\)'.*/\1/p" | head -1
}
version_auf_platte() {
    sed -n "s/.*const APP_VERSION = '\([^']*\)'.*/\1/p" "$APP_DIR/$INDEX_DATEI" 2>/dev/null | head -1
}

ergebnis_zeilen() {  # $1 = gelungen|fehlgeschlagen, $2 = von, $3 = auf
    echo "RUECKSPRUNG_ERGEBNIS=$1"
    echo "RUECKSPRUNG_VON_VERSION=${2:-unbekannt}"
    echo "RUECKSPRUNG_AUF_VERSION=${3:-unbekannt}"
}

marke_lesen() {  # erste Zeile, erstes Wort; leer wenn keine Marke
    if [ -f "$MARKE_DATEI" ]; then
        head -1 "$MARKE_DATEI" | awk '{print $1}'
    fi
}

befehl="${1:-}"
[ $# -gt 0 ] && shift

cd "$APP_DIR"

# ── bestaetigen ──────────────────────────────────────────────────────────────
if [ "$befehl" = "bestaetigen" ]; then
    nur_neu=0
    for a in "$@"; do
        [ "$a" = "--nur-wenn-keine-marke" ] && nur_neu=1
    done
    vorhanden="$(marke_lesen)"
    if [ "$nur_neu" = "1" ] && [ -n "$vorhanden" ]; then
        echo ">>> Marke „zuletzt bestätigt“ ist schon vorhanden ($vorhanden) – unverändert."
        exit 0
    fi
    COMMIT="$(git rev-parse HEAD)"
    VERSION="$(version_auf_platte)"
    mkdir -p "$(dirname "$MARKE_DATEI")"
    TMP_MARKE="$MARKE_DATEI.neu"
    {
        echo "$COMMIT"
        echo "App-Version: ${VERSION:-unbekannt}"
        echo "Vermerkt: $(date '+%Y-%m-%d %H:%M:%S')"
    } > "$TMP_MARKE"
    mv -f "$TMP_MARKE" "$MARKE_DATEI"
    echo "✅ Zuletzt bestätigte Version vermerkt: App-Version ${VERSION:-unbekannt} (Commit $COMMIT)"
    exit 0
fi

# ── zurueck ──────────────────────────────────────────────────────────────────
if [ "$befehl" != "zurueck" ]; then
    echo "Verwendung: ruecksprung.sh bestaetigen [--nur-wenn-keine-marke] | zurueck" >&2
    exit 2
fi

echo "=== FotoAlert automatischer Rücksprung – $(date '+%Y-%m-%d %H:%M:%S') ==="

CURRENT="$(git rev-parse HEAD)"
VON_VERSION="$(version_auf_platte)"
ZIEL_ROH="$(marke_lesen)"
ZIEL=""
if [ -n "$ZIEL_ROH" ]; then
    ZIEL="$(git rev-parse --verify --quiet "$ZIEL_ROH^{commit}" || true)"
    if [ -z "$ZIEL" ]; then
        echo "⚠️  Die Marke „zuletzt bestätigt“ ($ZIEL_ROH) zeigt auf keinen bekannten Stand."
    fi
elif [ -n "${FOTOALERT_RUECKFALL_COMMIT:-}" ]; then
    ZIEL="$(git rev-parse --verify --quiet "${FOTOALERT_RUECKFALL_COMMIT}^{commit}" || true)"
    [ -n "$ZIEL" ] && echo "⚠️  Noch keine bestätigte Version vermerkt – Rücksprung auf den Stand vor der Veröffentlichung."
fi

if [ -z "$ZIEL" ]; then
    echo "❌ $MELDUNG_FEHLGESCHLAGEN"
    echo "   Es ist keine bestätigte Version bekannt (Marke fehlt oder ungültig): $MARKE_DATEI"
    echo "   Letzter bekannter Zustand: Commit $CURRENT, App-Version ${VON_VERSION:-unbekannt}"
    ergebnis_zeilen fehlgeschlagen "$VON_VERSION" ""
    exit 1
fi

AUF_VERSION="$(version_von_commit "$ZIEL")"
echo "Zurückgenommen:       App-Version ${VON_VERSION:-unbekannt} (Commit $CURRENT)"
echo "Zurückgeholt auf:     App-Version ${AUF_VERSION:-unbekannt} (Commit $ZIEL) – zuletzt bestätigte Version"

# 1. Dateien UND gespeicherten Stand des Servers zurücksetzen: Jedes weitere Ziehen und jeder
#    Neustart setzt auf diesem Stand auf (AK17). Datenbank und Nutzerdaten liegen nicht im
#    Git-Bestand und bleiben unberührt (AK21).
echo ">>> App-Dateien und gespeicherten Stand zurücksetzen..."
git reset --hard "$ZIEL"

# 2. Service-Worker-Datei: Stand der zurückgeholten Version, mit frischem Cache-Namen (wie bei
#    einer normalen Veröffentlichung), damit Browser, die die kaputte Fassung hatten, sicher neu laden.
DEPLOY_TS="$(date +%Y%m%d%H%M)"
if [ -f "$APP_DIR/$SW_DATEI" ]; then
    sed -i.bak "s/const CACHE_NAME = 'fotoalert-[^']*'/const CACHE_NAME = 'fotoalert-$DEPLOY_TS'/" "$APP_DIR/$SW_DATEI"
    rm -f "$APP_DIR/$SW_DATEI.bak"
    echo ">>> SW Cache-Name: fotoalert-$DEPLOY_TS"
fi

# 3. App neu starten
echo ">>> App-Service neustarten..."
sudo systemctl restart fotoalert.service

# 4. Webserver-Einstellungen auf den Stand der zurückgeholten Version (wie deploy.sh Schritt 7)
CADDY_OK=1
echo ">>> Caddy-Konfiguration abgleichen..."
sed "s|YOUR_DOMAIN|$CADDY_DOMAIN|g" "$APP_DIR/FotoAlert/deploy/Caddyfile" > "$CADDY_CANDIDATE"
if ! sudo caddy validate --config "$CADDY_CANDIDATE" --adapter caddyfile; then
    echo "❌ Caddyfile der zurückgeholten Version ist ungültig – Webserver bleibt unverändert."
    CADDY_OK=0
elif ! sudo cmp -s "$CADDY_CANDIDATE" "$CADDY_LIVE" 2>/dev/null; then
    sudo cp "$CADDY_CANDIDATE" "$CADDY_LIVE"
    if sudo systemctl reload caddy; then
        echo ">>> Caddy erfolgreich neu geladen."
    else
        echo "❌ Caddy-Reload fehlgeschlagen (journalctl -u caddy -n 50)."
        CADDY_OK=0
    fi
else
    echo ">>> Caddyfile unverändert – kein Reload nötig."
fi
rm -f "$CADDY_CANDIDATE"

# 5. Statusabfrage (Retry-Schleife, max. ca. 30 s) – danach prüft der GitHub-Lauf mit dem Kurztest weiter
HTTP_STATUS="000"
for i in 1 2 3 4 5 6; do
    sleep 5
    HTTP_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_STATUS" = "200" ]; then break; fi
    echo "    Rücksprung-Versuch $i: HTTP $HTTP_STATUS – warte..."
done

if [ "$HTTP_STATUS" = "200" ] && [ "$CADDY_OK" = "1" ]; then
    echo "⚠️  Rücksprung gelungen: App-Version ${AUF_VERSION:-unbekannt} läuft wieder (Commit $ZIEL)"
    ergebnis_zeilen gelungen "$VON_VERSION" "$AUF_VERSION"
    exit 0
fi

echo "❌ $MELDUNG_FEHLGESCHLAGEN"
echo "   Letzter bekannter Zustand: Commit $ZIEL, App-Version ${AUF_VERSION:-unbekannt}, Statusabfrage HTTP $HTTP_STATUS, Webserver-Abgleich $([ "$CADDY_OK" = "1" ] && echo ok || echo fehlgeschlagen)"
echo "   Logs: journalctl -u fotoalert -n 100"
ergebnis_zeilen fehlgeschlagen "$VON_VERSION" "$AUF_VERSION"
exit 1
