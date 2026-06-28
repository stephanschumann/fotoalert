#!/usr/bin/env bash
# =============================================================================
# FotoAlert – Release-Skript (läuft auf dem Mac)
#
# Verwendung:
#   ./release.sh patch "Kurze Bugfix-Beschreibung"
#   ./release.sh minor "Neues Feature XY"
#   ./release.sh major "Breaking Change"
#
# Was das Skript tut:
#   1. APP_VERSION in web/index.html hochzählen
#   2. CACHE_NAME in web/sw.js aktualisieren (fotoalert-vX.Y.Z)
#   3. Alles committen und auf GitHub pushen
#   4. GitHub Actions deployt automatisch auf den Server
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INDEX_HTML="$SCRIPT_DIR/web/index.html"
SW_JS="$SCRIPT_DIR/web/sw.js"

# ── Argumente prüfen ─────────────────────────────────────────────────────────
if [ $# -lt 2 ]; then
    echo "Verwendung: $0 <patch|minor|major> \"Commit-Message\""
    echo "Beispiel:   $0 patch \"Fix: Karten-Anzeige auf iPhone korrigiert\""
    exit 1
fi

BUMP_TYPE="$1"
COMMIT_MSG="$2"

if [[ "$BUMP_TYPE" != "patch" && "$BUMP_TYPE" != "minor" && "$BUMP_TYPE" != "major" ]]; then
    echo "Fehler: Ersten Parameter muss 'patch', 'minor' oder 'major' sein."
    exit 1
fi

# ── Aktuelle Version auslesen ─────────────────────────────────────────────────
CURRENT_VERSION=$(grep -oE "APP_VERSION = '[0-9]+\.[0-9]+\.[0-9]+'" "$INDEX_HTML" | grep -oE "[0-9]+\.[0-9]+\.[0-9]+")
if [ -z "$CURRENT_VERSION" ]; then
    echo "Fehler: APP_VERSION nicht in $INDEX_HTML gefunden."
    exit 1
fi

echo "Aktuelle Version: $CURRENT_VERSION"

# ── Neue Version berechnen ────────────────────────────────────────────────────
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"
case "$BUMP_TYPE" in
    major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
    minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
    patch) PATCH=$((PATCH + 1)) ;;
esac
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "Neue Version:     $NEW_VERSION"

# ── Bestätigung ───────────────────────────────────────────────────────────────
read -rp "Release v${NEW_VERSION} erstellen und pushen? [j/N] " CONFIRM
if [[ "$CONFIRM" != "j" && "$CONFIRM" != "J" ]]; then
    echo "Abgebrochen."
    exit 0
fi

# ── index.html: APP_VERSION aktualisieren ────────────────────────────────────
sed -i '' "s/APP_VERSION = '$CURRENT_VERSION'/APP_VERSION = '$NEW_VERSION'/" "$INDEX_HTML"
echo "✓ APP_VERSION in index.html auf $NEW_VERSION gesetzt"

# ── sw.js: CACHE_NAME aktualisieren ──────────────────────────────────────────
sed -i '' "s/const CACHE_NAME = 'fotoalert-v[^']*'/const CACHE_NAME = 'fotoalert-v${NEW_VERSION}'/" "$SW_JS"
echo "✓ CACHE_NAME in sw.js auf fotoalert-v${NEW_VERSION} gesetzt"

# ── Git: committen und pushen ─────────────────────────────────────────────────
cd "$SCRIPT_DIR/.."  # Repo-Root

git add \
    "FotoAlert/web/index.html" \
    "FotoAlert/web/sw.js"

git commit -m "release: v${NEW_VERSION} – ${COMMIT_MSG}"
git push origin main
git tag "v${NEW_VERSION}"
git push origin "v${NEW_VERSION}"

echo ""
echo "✅ v${NEW_VERSION} gepusht. GitHub Actions deployt jetzt automatisch."
echo "   Status: https://github.com/stephanschumann/fotoalert/actions"
echo "   App:    https://fotoalert.stephanschumann.com"
