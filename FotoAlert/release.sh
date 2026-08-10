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

# ── Argumente prüfen ────────────────────────────────────────────────────────
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

# ── Bestätigung ──────────────────────────────────────────────────────────────
read -rp "Release v${NEW_VERSION} erstellen und pushen? [j/N] " CONFIRM
if [[ "$CONFIRM" != "j" && "$CONFIRM" != "J" ]]; then
    echo "Abgebrochen."
    exit 0
fi

# ── Git: Repo-Root wechseln ───────────────────────────────────────────────────
cd "$SCRIPT_DIR/.."  # Repo-Root

# ── Merge-Konflikte prüfen (Pflicht vor jeder Datei-Änderung, TASK-88) ───────
# Läuft bewusst VOR den sed-Edits an index.html/sw.js weiter unten: würde die
# Prüfung erst nach dem Versions-Bump laufen, bliebe bei einem Abbruch der
# Bump bereits (uncommitted) im Arbeitsverzeichnis stehen — ein zweiter Versuch
# würde CURRENT_VERSION dann fälschlich schon als hochgezählt einlesen und
# nochmal draufzählen (Doppel-Bump). Deshalb: erst prüfen, dann ändern.
#
# git status --porcelain ist die git-native Quelle für den Konfliktstatus
# (Status-Codes UU/AA/DD/AU/UA/UD/DU) und damit robuster als eine reine
# Textsuche nach Konfliktmarkern: kein False-Positive durch Marker-Text in
# legitimen Dateiinhalten, kein False-Negative bei binären Dateien.
CONFLICT_FILES=$(git status --porcelain | grep -E '^(UU|AA|DD|AU|UA|UD|DU) ' | awk '{print $2}' || true)
if [ -n "$CONFLICT_FILES" ]; then
    echo ""
    echo "❌ Release abgebrochen: Es liegen ungelöste Merge-Konflikte vor."
    echo "   Betroffene Datei(en):"
    echo "$CONFLICT_FILES" | sed 's/^/     - /'
    echo ""
    echo "   Nächste Schritte:"
    echo "     1. Konflikt(e) in den genannten Datei(en) manuell lösen"
    echo "        (Konfliktmarker <<<<<<< / ======= / >>>>>>> entfernen)"
    echo "     2. git add <datei> && git commit"
    echo "     3. Danach das Release erneut starten:"
    echo "        ./release.sh ${BUMP_TYPE} \"${COMMIT_MSG}\""
    echo ""
    exit 1
fi

# ── Tag-Kollisions-Check (TASK-98, AK4/AK8) ──────────────────────────────────
# Läuft bewusst VOR jeder Datei-Änderung und vor jedem schreibenden Git-Befehl
# (also auch vor dem sed-Versionsbump weiter unten): bisher wurde "git tag"
# erst NACH "git commit"/"git push origin main" ausgeführt (Z.107-109 alt) -
# eine Tag-Kollision fiel damit erst auf, nachdem der Release-Commit bereits
# öffentlich auf main lag. Statt die Tag-Erstellung selbst vor den Push zu
# ziehen (unüblicher Git-Workflow), wird hier vorab geprüft, ob der Ziel-Tag
# bereits existiert (lokal oder auf origin) - dann bricht das Skript ab, bevor
# irgendetwas geschrieben oder gepusht wird.
if git rev-parse -q --verify "refs/tags/v${NEW_VERSION}" >/dev/null 2>&1 || \
   git ls-remote --exit-code --tags origin "refs/tags/v${NEW_VERSION}" >/dev/null 2>&1; then
    echo ""
    echo "❌ Release abgebrochen: Tag v${NEW_VERSION} existiert bereits (lokal oder auf origin)."
    echo "   Vermutliche Ursache: ein vorheriger Release-Lauf ist fehlgeschlagen, ohne dass"
    echo "   APP_VERSION tatsächlich erhöht wurde (siehe TASK-98-Retrospektive/TASK-07)."
    echo "   Bitte Versions-/Tag-Historie prüfen, bevor das Release erneut gestartet wird."
    echo ""
    exit 1
fi

# ── index.html: APP_VERSION aktualisieren ────────────────────────────────────
sed -i '' "s/APP_VERSION = '$CURRENT_VERSION'/APP_VERSION = '$NEW_VERSION'/" "$INDEX_HTML"
# Verifikation (TASK-98, AK2): BSD-sed bricht bei einem Nicht-Treffer still mit
# Exit 0 ab - ohne diese Prüfung würde das folgende "✓"-Echo unconditional
# ausgegeben, obwohl APP_VERSION unverändert geblieben ist (TASK-07-Fund).
if ! grep -qE "APP_VERSION = '${NEW_VERSION}'" "$INDEX_HTML"; then
    echo ""
    echo "❌ Fehler: APP_VERSION in $INDEX_HTML wurde nicht auf $NEW_VERSION gesetzt."
    echo "   Rolle Änderung zurück, damit kein halb geänderter Stand liegen bleibt..."
    git checkout -- "$INDEX_HTML"
    exit 1
fi
echo "✓ APP_VERSION in index.html auf $NEW_VERSION gesetzt (verifiziert)"

# ── sw.js: CACHE_NAME aktualisieren ──────────────────────────────────────────
sed -i '' "s/const CACHE_NAME = 'fotoalert-v[^']*'/const CACHE_NAME = 'fotoalert-v${NEW_VERSION}'/" "$SW_JS"
# Verifikation (TASK-98, AK3): siehe Begründung oben bei index.html. Bei einem
# Fehlschlag hier auch die bereits verifizierte index.html-Änderung zurückrollen,
# damit kein inkonsistenter Zwischenstand (nur eine der zwei Dateien geändert)
# im Arbeitsverzeichnis zurückbleibt (TASK-98, AK5).
if ! grep -qE "const CACHE_NAME = 'fotoalert-v${NEW_VERSION}'" "$SW_JS"; then
    echo ""
    echo "❌ Fehler: CACHE_NAME in $SW_JS wurde nicht auf fotoalert-v${NEW_VERSION} gesetzt."
    echo "   Rolle beide Änderungen (index.html + sw.js) zurück..."
    git checkout -- "$INDEX_HTML" "$SW_JS"
    exit 1
fi
echo "✓ CACHE_NAME in sw.js auf fotoalert-v${NEW_VERSION} gesetzt (verifiziert)"

# ── Git: committen und pushen ─────────────────────────────────────────────────
git add \
    "FotoAlert/web/index.html" \
    "FotoAlert/web/sw.js"

# Pathspec auch beim Commit (TASK-98, AK1): "git add <dateien>" ist zwar schon
# dateispezifisch, aber ein "git commit" OHNE Pathspec committet trotzdem den
# gesamten Index - also auch alles, was zu diesem Zeitpunkt bereits von einem
# anderen, gerade in Bearbeitung befindlichen Ticket gestaged war (TASK-07-
# Ursache). Mit Pathspec werden ausschließlich diese zwei Dateien committet,
# fremde gestagte Änderungen bleiben unangetastet weiterhin gestaged.
#
# Rollback-Abdeckung ab hier (TASK-98-Nachbesserung, Verifikations-Review
# 2026-08-10): die bisherige Version rollte nur bei einem Fehlschlag der
# sed-Verifikation zurück (Zeile ~119/134) - schlug stattdessen "git commit"
# oder "git push origin main" fehl (z.B. Pre-Commit-Hook lehnt ab, Netzwerk-
# fehler, main ist zwischenzeitlich divergiert), blieb index.html/sw.js mit
# der neuen Versionsnummer ohne Rollback stehen. Ein zweiter Skriptlauf hätte
# CURRENT_VERSION dann bereits als hochgezählt eingelesen und nochmal
# draufgezählt - exakt das Doppel-Bump-Muster, das AK5 eigentlich schließen
# sollte, nur einen Schritt später im Ablauf.
if ! git commit -m "release: v${NEW_VERSION} – ${COMMIT_MSG}" -- \
    "FotoAlert/web/index.html" \
    "FotoAlert/web/sw.js"; then
    echo ""
    echo "❌ Fehler: 'git commit' ist fehlgeschlagen (z.B. Pre-Commit-Hook lehnt ab)."
    echo "   Rolle beide Änderungen (index.html + sw.js) zurück, nichts wurde committet..."
    git checkout -- "$INDEX_HTML" "$SW_JS"
    exit 1
fi

if ! git push origin main; then
    echo ""
    echo "❌ Fehler: 'git push origin main' ist fehlgeschlagen (z.B. Netzwerk oder"
    echo "   main ist zwischenzeitlich divergiert). Der Release-Commit liegt lokal,"
    echo "   aber NICHT auf origin. Rolle den lokalen Commit zurück (git reset --soft)"
    echo "   und stelle index.html/sw.js auf den Vorzustand zurück, damit ein erneuter"
    echo "   Lauf von $0 sauber neu starten kann..."
    git reset --soft HEAD~1
    git checkout -- "$INDEX_HTML" "$SW_JS"
    exit 1
fi

if ! git tag "v${NEW_VERSION}"; then
    echo ""
    echo "❌ Fehler: 'git tag v${NEW_VERSION}' ist fehlgeschlagen, ABER der Release-"
    echo "   Commit ist bereits erfolgreich auf origin/main gepusht - kein Rollback"
    echo "   mehr möglich, ohne den bereits öffentlichen main-Verlauf zu verändern."
    echo "   Bitte manuell nachholen:"
    echo "     git tag \"v${NEW_VERSION}\" && git push origin \"v${NEW_VERSION}\""
    exit 1
fi

if ! git push origin "v${NEW_VERSION}"; then
    echo ""
    echo "❌ Fehler: 'git push origin v${NEW_VERSION}' ist fehlgeschlagen, ABER Commit"
    echo "   und Tag existieren bereits lokal bzw. auf origin/main - kein Rollback nötig."
    echo "   Bitte manuell nachholen:"
    echo "     git push origin \"v${NEW_VERSION}\""
    exit 1
fi

echo ""
echo "✅ v${NEW_VERSION} gepusht. GitHub Actions deployt jetzt automatisch."
echo "   Status: https://github.com/stephanschumann/fotoalert/actions"
echo "   App:    https://fotoalert.stephanschumann.com"
