#!/usr/bin/env bash
# =============================================================================
# FotoAlert – Release-Befehl (läuft auf dem Mac) — einziger Weg zu einem Release
#
# Verwendung:
#   ./release.sh patch "TASK-123 Kurze Beschreibung"
#   ./release.sh minor "US-45 Neues Feature XY"
#   ./release.sh major "TASK-200 Breaking Change"
#   (Bei einer reinen Doku-Veröffentlichung wird die Art ignoriert.)
#
# Vorher: Ticket-Dateiliste FotoAlert/release-dateien.txt anlegen — eine Datei je
# Zeile, relativ zum Repo-Root; Leerzeilen und Zeilen mit „#“ zählen nicht. Die
# Liste selbst wird nie veröffentlicht.
#
# Ablauf (TASK-117 inkl. TASK-112):
#   1. Vorab-Prüfungen, alle vor jeder Änderung: Python 3.12, läuft schon,
#      Git-Sperrdatei, Merge-Konflikt, GitHub erreichbar und nicht neuer,
#      Ticket-Dateiliste, fremde Commits, „Nichts Neues“, Versionsnummer frei
#   2. Vorschau: was live geht (Dateien, Commits, Version) und was hier bleibt
#   3. Probelauf auf einer sauberen Kopie genau der Fassung, die hochgeladen wird,
#      mit leerem Datenbestand, über die gemeinsame Prüfliste tools/pruefliste.sh
#      (dieselbe, die GitHub aufruft)
#   4. Nur bei Grün: Sicherungskopie des Backlogs, ein Commit mit Ticket-Dateien
#      und neuer Versionsnummer, ein Upload, Versionskennzeichen — ohne Rückfrage
#   Rot oder Abbruch: nichts verändert, nichts hochgeladen. Protokoll bleibt in
#   FotoAlert/_to_delete/release-protokolle/.
# Exit-Codes: 0 veröffentlicht · 1 abgebrochen/rot · 3 nichts Neues · 130 unterbrochen
# Bewusst plattformneutral (macOS-bash 3.2 / BSD-Werkzeuge und Linux, kein sed -i).
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJ="$(basename "$SCRIPT_DIR")"
INDEX_REL="$PROJ/web/index.html"
SW_REL="$PROJ/web/sw.js"
TICKETLISTE_REL="$PROJ/release-dateien.txt"
BACKLOG_REL="$PROJ/BACKLOG.md"
PRUEFLISTE_REL="$PROJ/tools/pruefliste.sh"
BEKANNTE_UEBERSPRUENGE_REL="$PROJ/tools/bekannte_uebersprungene_tests.txt"   # AK9a, feste Liste
PROBELAUF_PORT="${FOTOALERT_PROBELAUF_PORT:-8765}"
GITHUB_PRUEFUNG="https://github.com/stephanschumann/fotoalert/actions"
APP_URL="https://fotoalert.stephanschumann.com"

PROTOKOLL=""
ARBEIT=""
SPERRE=""
SPERRE_MEIN=0
PHASE="vorab"

sag() {
    echo "$*"
    if [ -n "$PROTOKOLL" ]; then echo "$*" >> "$PROTOKOLL"; fi
}

abbruch() {   # abbruch "<Grund>" ["<weitere Zeile>" …] — nur vor jeder Änderung
    sag ""
    sag "❌ Release abgebrochen: $1"
    shift
    for Z in "$@"; do sag "   $Z"; done
    sag "   Es wurde nichts verändert und nichts hochgeladen."
    exit 1
}

anzeigename() {
    case "$1" in
        backend) echo "Backend" ;;
        oberflaechen_check) echo "Oberflächen-Check" ;;
        browser_tests) echo "Browser-Tests" ;;
        *) echo "$1" ;;
    esac
}

# Ersetzt die Werte der Geheimnisse in einem Datenstrom durch *** (AK15).
schwaerzen() {
    awk 'BEGIN { n = 0; split("FOTOALERT_HOST_PASSWORD FOTOALERT_USER_PASSWORD FOTOALERT_AUTH_SECRET", k, " ");
                 for (i in k) { v = ENVIRON[k[i]]; if (length(v) >= 4) { n++; s[n] = v } } }
         { z = $0; for (j = 1; j <= n; j++) { aus = "";
             while ((p = index(z, s[j])) > 0) { aus = aus substr(z, 1, p - 1) "***"; z = substr(z, p + length(s[j])) }
             z = aus z }
           print z; fflush() }'
}

# Plattformneutrale Textersetzung ohne „sed -i“ (BSD und GNU verhalten sich dort verschieden).
ersetzen() {   # ersetzen <datei> <sed-ausdruck>
    sed "$2" "$1" > "$ARBEIT/ersetzen.tmp" && cat "$ARBEIT/ersetzen.tmp" > "$1" && rm -f "$ARBEIT/ersetzen.tmp"
}

version_setzen() {   # version_setzen <wurzel> — setzt NEW_VERSION in index.html und sw.js, prüft beides
    ersetzen "$1/$INDEX_REL" "s/APP_VERSION = '$CURRENT_VERSION'/APP_VERSION = '$NEW_VERSION'/" || return 1
    grep -qE "APP_VERSION = '${NEW_VERSION}'" "$1/$INDEX_REL" || { echo "❌ APP_VERSION in $INDEX_REL nicht auf $NEW_VERSION gesetzt."; return 1; }
    ersetzen "$1/$SW_REL" "s/const CACHE_NAME = 'fotoalert-v[^']*'/const CACHE_NAME = 'fotoalert-v${NEW_VERSION}'/" || return 1
    grep -qE "const CACHE_NAME = 'fotoalert-v${NEW_VERSION}'" "$1/$SW_REL" || { echo "❌ CACHE_NAME in $SW_REL nicht auf fotoalert-v${NEW_VERSION} gesetzt."; return 1; }
    return 0
}

# Lokalen Stand exakt auf den Zustand vor dem Festschreiben zurücksetzen (AK8/AK29/AK31).
zuruecknehmen() {
    [ "$PHASE" = "festschreiben" ] || return 0
    if [ -n "${ALT_HEAD:-}" ] && [ "$(git rev-parse HEAD 2>/dev/null)" != "$ALT_HEAD" ]; then
        git reset -q --soft "$ALT_HEAD"
    fi
    [ -f "$ARBEIT/sicherung-index" ] && cp "$ARBEIT/sicherung-index" "$GIT_DIR_ABS/index"
    [ -f "$ARBEIT/sicherung-index.html" ] && cat "$ARBEIT/sicherung-index.html" > "$REPO_DIR/$INDEX_REL"
    [ -f "$ARBEIT/sicherung-sw.js" ] && cat "$ARBEIT/sicherung-sw.js" > "$REPO_DIR/$SW_REL"
    PHASE="zurueckgenommen"
    sag "   Lokaler Stand zurückgesetzt: alte Versionsnummer, nichts eingecheckt."
}

aufraeumen() {
    if [ -n "$ARBEIT" ] && [ -d "$ARBEIT" ]; then rm -rf "$ARBEIT"; fi
    if [ "$SPERRE_MEIN" = 1 ]; then rm -f "$SPERRE"; fi
}

unterbrochen() {
    trap '' INT HUP TERM
    sag ""
    sag "⚠️  Release unterbrochen ($1)."
    if [ "$PHASE" = "festschreiben" ]; then zuruecknehmen; else sag "   Es wurde nichts verändert und nichts hochgeladen."; fi
    exit 130
}

trap aufraeumen EXIT
trap 'unterbrochen Abbruch-Tastenkombination' INT
trap 'unterbrochen "Fenster geschlossen"' HUP
trap 'unterbrochen beendet' TERM

# ── Argumente ────────────────────────────────────────────────────────────────
if [ $# -lt 2 ]; then
    echo "Verwendung: $0 <patch|minor|major> \"TICKET-ID Beschreibung\""
    echo "Beispiel:   $0 patch \"BUG-123 Karten-Anzeige auf iPhone korrigiert\""
    exit 1
fi
BUMP_TYPE="$1"
COMMIT_MSG="$2"
if [ "$BUMP_TYPE" != "patch" ] && [ "$BUMP_TYPE" != "minor" ] && [ "$BUMP_TYPE" != "major" ]; then
    echo "Fehler: Ersten Parameter muss 'patch', 'minor' oder 'major' sein."
    exit 1
fi
TICKET="$(printf '%s\n' "$COMMIT_MSG" | grep -oE '[A-Z]+-[0-9]+' | head -n 1)"

# ── Python 3.12 (AK2) ────────────────────────────────────────────────────────
if [ -x "$SCRIPT_DIR/backend/venv/bin/python3" ]; then
    PY="$SCRIPT_DIR/backend/venv/bin/python3"
else
    PY="$(command -v python3 || true)"
fi
[ -n "$PY" ] || abbruch "Python 3.12 nötig, aber kein python3 gefunden."
PY_VERSION="$("$PY" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n 1)"
case "$PY_VERSION" in
    3.12|3.12.*) ;;
    *) abbruch "Python 3.12 nötig, gefunden ${PY_VERSION:-unbekannt} ($PY)." \
               "Bitte die Python-3.12-Umgebung unter $PROJ/backend/venv einrichten." ;;
esac

cd "$REPO_DIR" || exit 1
GIT_DIR_ABS="$(git rev-parse --absolute-git-dir 2>/dev/null)" || abbruch "$REPO_DIR ist kein Git-Repo."

# ── Läuft schon? (AK19) ──────────────────────────────────────────────────────
SPERRE="$GIT_DIR_ABS/fotoalert-release.lock"
if ! ln -s "$$" "$SPERRE" 2>/dev/null; then
    ALT_PID="$(readlink "$SPERRE" 2>/dev/null || true)"
    if [ -n "$ALT_PID" ] && kill -0 "$ALT_PID" 2>/dev/null; then
        echo ""
        echo "❌ Release abgebrochen: Der Release-Befehl läuft bereits (PID $ALT_PID)."
        echo "   Dieser zweite Aufruf ändert nichts; der laufende Release läuft ungestört weiter."
        exit 1
    fi
    rm -f "$SPERRE"   # verwaiste Sperre eines hart beendeten Laufs
    ln -s "$$" "$SPERRE" 2>/dev/null || abbruch "Der Release-Befehl läuft bereits (Sperre $SPERRE)."
fi
SPERRE_MEIN=1

# ── Git-Sperrdatei (AK21) ────────────────────────────────────────────────────
if [ -e "$GIT_DIR_ABS/index.lock" ]; then
    abbruch "Git ist gerade gesperrt (Sperrdatei $GIT_DIR_ABS/index.lock vorhanden)." \
            "Läuft noch ein anderer Git-Vorgang? Wenn nicht: Sperrdatei löschen und erneut starten."
fi

# ── Merge-Konflikte (TASK-88, AK31) ──────────────────────────────────────────
CONFLICT_FILES="$(git diff --name-only --diff-filter=U 2>/dev/null || true)"
if [ -n "$CONFLICT_FILES" ]; then
    echo ""
    echo "❌ Release abgebrochen: Es liegen ungelöste Merge-Konflikte vor."
    echo "   Betroffene Datei(en):"
    printf '%s\n' "$CONFLICT_FILES" | sed 's/^/     - /'
    echo "   Konflikt(e) lösen, committen und das Release erneut starten."
    echo "   Es wurde nichts verändert und nichts hochgeladen."
    exit 1
fi

# ── GitHub erreichbar und nicht neuer? (AK30, AK20) ──────────────────────────
REMOTE_AUS="$(GIT_TERMINAL_PROMPT=0 GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=30 \
              git ls-remote origin refs/heads/main 2>/dev/null)" || \
    abbruch "GitHub ist nicht erreichbar (Abfrage von origin scheiterte)." \
            "Bitte Internetverbindung bzw. GitHub-Anmeldung prüfen und erneut starten."
R="$(printf '%s\n' "$REMOTE_AUS" | awk 'NR==1 {print $1}')"
[ -n "$R" ] || abbruch "Auf GitHub gibt es keinen Stand „main“ (GitHub nicht erreichbar oder falsches Ziel)."
if ! git cat-file -e "${R}^{commit}" 2>/dev/null || ! git merge-base --is-ancestor "$R" HEAD 2>/dev/null; then
    abbruch "GitHub hat einen neueren Stand als dieser Mac (z. B. automatisches Gebäudedaten-Update)." \
            "Bitte zuerst holen (git pull origin main) und danach erneut starten."
fi

# ── Ticket-Dateiliste (AK25) ─────────────────────────────────────────────────
if [ ! -f "$REPO_DIR/$TICKETLISTE_REL" ]; then
    abbruch "Die Ticket-Dateiliste $TICKETLISTE_REL fehlt (eine Datei je Zeile, relativ zum Repo-Root)."
fi
LISTE="$(tr -d '\r' < "$REPO_DIR/$TICKETLISTE_REL" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | grep -vE '^(#|$)' | sort -u || true)"
if [ -z "$LISTE" ]; then
    abbruch "Die Ticket-Dateiliste $TICKETLISTE_REL ist leer (keine Dateien eingetragen)."
fi
while IFS= read -r F; do
    if [ ! -e "$F" ] && ! git cat-file -e "HEAD:$F" 2>/dev/null; then
        abbruch "Die Datei $F aus der Ticket-Dateiliste gibt es nicht (weder im Arbeitsordner noch eingecheckt)."
    fi
done <<< "$LISTE"
in_liste() { printf '%s\n' "$LISTE" | grep -qxF -- "$1" || [ "$1" = "$BACKLOG_REL" ]; }

# ── Noch nicht veröffentlichte Commits: nur eigene, nur Ticket-Dateien (AK23/AK24) ──
COMMITS="$(git rev-list --reverse "$R..HEAD")"
FREMD=""
if [ -n "$COMMITS" ]; then
    while IFS= read -r C; do
        S="$(git log -1 --format='%h %s' "$C")"
        if [ -n "$TICKET" ] && printf '%s\n' "$S" | grep -qE "(^|[^A-Za-z0-9-])${TICKET}([^0-9]|\$)"; then
            for D in $(git diff-tree --no-commit-id --name-only -r "$C"); do
                in_liste "$D" || FREMD="${FREMD}     - $S  (ändert $D, nicht auf der Ticket-Dateiliste)
"
            done
        else
            FREMD="${FREMD}     - $S
"
        fi
    done <<< "$COMMITS"
fi
if [ -n "$FREMD" ]; then
    echo ""
    echo "❌ Release abgebrochen: Es liegen noch nicht veröffentlichte Commits vor, die nicht zu diesem"
    echo "   Release (${TICKET:-ohne Ticket-ID in der Beschreibung}) gehören und mit hochgehen würden:"
    printf '%s' "$FREMD"
    echo "   Erst klären (eigenes Release oder zurücknehmen), dann erneut starten."
    echo "   Es wurde nichts verändert und nichts hochgeladen."
    exit 1
fi

# ── Was geht mit? (AK22, AK23a, AK23b) ───────────────────────────────────────
geaendert() {   # Datei weicht vom eingecheckten Stand ab oder ist neu
    ! git diff --quiet HEAD -- "$1" 2>/dev/null || [ -n "$(git ls-files --others --exclude-standard -- "$1")" ]
}
GEHT_WT=""
for F in $(printf '%s\n%s\n' "$LISTE" "$BACKLOG_REL" | sort -u); do
    if geaendert "$F"; then GEHT_WT="${GEHT_WT}${F}
"; fi
done
GEHT_WT="$(printf '%s' "$GEHT_WT" | grep -v '^$' || true)"
COMMIT_DATEIEN=""
[ -n "$COMMITS" ] && COMMIT_DATEIEN="$(git diff --name-only "$R" HEAD)"
ALLE_DATEIEN="$(printf '%s\n%s\n' "$GEHT_WT" "$COMMIT_DATEIEN" | grep -v '^$' | sort -u || true)"

if [ -z "$GEHT_WT" ] && [ -z "$COMMITS" ]; then
    echo ""
    echo "ℹ️  Nichts Neues zu veröffentlichen — seit dem letzten Release hat sich an den Dateien der"
    echo "   Ticket-Dateiliste nichts geändert. Keine neue Version, nichts hochgeladen, kein Deploy."
    exit 3
fi

# Reine Doku (nur .md-Dateien) → keine neue Versionsnummer (AK26/AK27)
NUR_DOKU=1
while IFS= read -r F; do
    case "$F" in *.md) ;; *) NUR_DOKU=0 ;; esac
done <<< "$ALLE_DATEIEN"

CURRENT_VERSION="$(grep -oE "APP_VERSION = '[0-9]+\.[0-9]+\.[0-9]+'" "$INDEX_REL" | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -n 1)"
[ -n "$CURRENT_VERSION" ] || abbruch "APP_VERSION nicht in $INDEX_REL gefunden."
NEW_VERSION=""
if [ "$NUR_DOKU" = 0 ]; then
    MAJOR="${CURRENT_VERSION%%.*}"; REST="${CURRENT_VERSION#*.}"; MINOR="${REST%%.*}"; PATCH="${REST#*.}"
    case "$BUMP_TYPE" in
        major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
        minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
        patch) PATCH=$((PATCH + 1)) ;;
    esac
    NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
    # Tag-Kollision (TASK-98, AK31) — vor jeder Änderung
    if git rev-parse -q --verify "refs/tags/v${NEW_VERSION}" >/dev/null 2>&1 || \
       git ls-remote --exit-code --tags origin "refs/tags/v${NEW_VERSION}" >/dev/null 2>&1; then
        abbruch "Tag v${NEW_VERSION} existiert bereits (lokal oder auf GitHub)." \
                "Vermutlich ist ein früherer Release-Lauf gescheitert, ohne APP_VERSION zu erhöhen." \
                "Bitte Versions-/Tag-Historie prüfen, bevor das Release erneut gestartet wird."
    fi
fi

# ── Protokoll und Vorschau (AK17) ────────────────────────────────────────────
ZEIT="$(date +%Y%m%d-%H%M%S)"
PROTOKOLL_DIR="$SCRIPT_DIR/_to_delete/release-protokolle"
mkdir -p "$PROTOKOLL_DIR"
PROTOKOLL="$PROTOKOLL_DIR/release_${ZEIT}_$$.log"
ARTEFAKTE="$PROTOKOLL_DIR/release_${ZEIT}_$$_artefakte"
: > "$PROTOKOLL"
echo "Protokoll: $PROTOKOLL"
sag ""
sag "══ Was live gehen wird (${TICKET:-ohne Ticket-ID}: $COMMIT_MSG) ══"
sag "Dateien:"
while IFS= read -r F; do sag "   - $F"; done <<< "$ALLE_DATEIEN"
if [ "$NUR_DOKU" = 0 ]; then
    sag "   - $INDEX_REL, $SW_REL (Versionsnummer)"
fi
sag "Noch nicht veröffentlichte Commits:"
if [ -n "$COMMITS" ]; then
    while IFS= read -r C; do sag "   - $(git log -1 --format='%h %s' "$C")"; done <<< "$COMMITS"
else
    sag "   (keine)"
fi
if [ "$NUR_DOKU" = 1 ]; then
    sag "Versionsnummer: keine neue Version (nur Doku), bleibt $CURRENT_VERSION"
else
    sag "Versionsnummer: $CURRENT_VERSION → $NEW_VERSION ($BUMP_TYPE)"
fi
BLEIBT="$(git status --porcelain=v1 --untracked-files=all 2>/dev/null | cut -c4- | sed 's/.* -> //' | sort -u || true)"
sag "bleibt hier, wird nicht veröffentlicht:"
N_BLEIBT=0
while IFS= read -r F; do
    [ -z "$F" ] && continue
    [ "$F" = "$TICKETLISTE_REL" ] && continue
    printf '%s\n' "$ALLE_DATEIEN" | grep -qxF -- "$F" && continue
    sag "   - $F"; N_BLEIBT=$((N_BLEIBT + 1))
done <<< "$BLEIBT"
[ "$N_BLEIBT" = 0 ] && sag "   (nichts)"

# ── Saubere Prüfkopie genau der Upload-Fassung (AK3/AK4/AK5) ─────────────────
ARBEIT="$(mktemp -d "${TMPDIR:-/tmp}/fotoalert-release.XXXXXX")" || abbruch "Temp-Ordner für die Prüfkopie nicht anlegbar."
KOPIE="$ARBEIT/kopie"
mkdir -p "$KOPIE" "$ARTEFAKTE"
if ! git archive --format=tar HEAD | (cd "$KOPIE" && tar -xf -); then
    abbruch "Prüfkopie konnte nicht erstellt werden (git archive)."
fi
: > "$ARBEIT/fassung.txt"
while IFS= read -r F; do
    [ -z "$F" ] && continue
    if [ -e "$REPO_DIR/$F" ]; then
        mkdir -p "$(dirname "$KOPIE/$F")"
        cp -p "$REPO_DIR/$F" "$KOPIE/$F"
        echo "$F $(git hash-object -- "$F")" >> "$ARBEIT/fassung.txt"
    else
        rm -rf "$KOPIE/$F"
        echo "$F GELOESCHT" >> "$ARBEIT/fassung.txt"
    fi
done <<< "$GEHT_WT"
if [ "$NUR_DOKU" = 0 ]; then
    version_setzen "$KOPIE" || abbruch "Versionsnummer in der Prüfkopie nicht setzbar."
fi
# Ephemeridendatei wie bei GitHub aus dem Zwischenspeicher (nicht versioniert, nur kopiert)
[ -f "$SCRIPT_DIR/backend/de421.bsp" ] && cp "$SCRIPT_DIR/backend/de421.bsp" "$KOPIE/$PROJ/backend/de421.bsp"

# Geheimnisse aus der lokalen Passwortdatei (statt GitHub-Secrets), nie als Parameter (AK15)
ENV_DATEI="$SCRIPT_DIR/backend/.env"
for NAME in FOTOALERT_HOST_PASSWORD FOTOALERT_USER_PASSWORD FOTOALERT_AUTH_SECRET; do
    W=""
    if [ -f "$ENV_DATEI" ]; then
        W="$(tr -d '\r' < "$ENV_DATEI" | sed -n "s/^[[:space:]]*\(export[[:space:]][[:space:]]*\)\{0,1\}${NAME}[[:space:]]*=[[:space:]]*//p" | tail -n 1 \
             | sed -e 's/[[:space:]]*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/")"
    fi
    if [ -n "$W" ]; then
        export "$NAME=$W"
    elif [ -z "$(eval "printf '%s' \"\${$NAME:-}\"")" ]; then
        sag "⚠️  $NAME fehlt in $PROJ/backend/.env – der Probelauf läuft ohne diesen Wert."
    fi
done

# ── Probelauf über die gemeinsame Prüfliste (AK1, AK6–AK10, AK12–AK14) ────────
sag ""
sag "══ Probelauf (saubere Kopie, leerer Datenbestand, Python $PY_VERSION, Port $PROBELAUF_PORT) ══"
T0="$(date +%s)"
# Ruhezustand-Schutz (macOS): caffeinate -i hält den Mac während der Prüfliste wach. Wo es fehlt
# (Linux/GitHub), läuft die Prüfliste unverändert ohne Schutz.
WACH=""
if command -v caffeinate >/dev/null 2>&1; then WACH="caffeinate -i"; sag "☕ Ruhezustand-Schutz aktiv (caffeinate -i)"; fi
( cd "$KOPIE" && PRUEFLISTE_PYTHON="$PY" PRUEFLISTE_PORT="$PROBELAUF_PORT" PRUEFLISTE_ABLAGE="$ARTEFAKTE" \
      $WACH bash "$KOPIE/$PRUEFLISTE_REL" ) < /dev/null 2>&1 | schwaerzen | while IFS= read -r Z; do
    printf '%s\n' "$Z" >> "$PROTOKOLL"
    case "$Z" in
        "PRUEFLISTE block="*" start") B="${Z#PRUEFLISTE block=}"; B="${B% start}"
                                      echo "▶ Prüfblock läuft: $(anzeigename "$B")" ;;
        "Browser-Werkzeug:"*) echo "   $Z" ;;
    esac
done
RC=${PIPESTATUS[0]}
T1="$(date +%s)"
DAUER=$((T1 - T0))

ROT=""
GEPRUEFT=""

# AK9a/AK9b: Übersprünge in den Blöcken Backend und Browser-Tests sind nur erlaubt, wenn Test-ID UND
# Grund als Paar in der festen Liste (aus genau der geprüften Fassung) stehen; der aufgelistete Grund
# muss im gemeldeten enthalten sein.
uebersprungen_bekannt() {   # uebersprungen_bekannt <block> <anzahl laut ergebnis>
    UB_NAME="$(anzeigename "$1")"
    BEFUND="$(awk -v liste="$KOPIE/$BEKANNTE_UEBERSPRUENGE_REL" -v praefix="PRUEFLISTE block=$1 uebersprungen_test=" '
        function trim(t) { sub(/^[ \t]+/, "", t); sub(/[ \t\r]+$/, "", t); return t }
        BEGIN { n = 0
                while ((getline z < liste) > 0) {
                    if (z ~ /^[ \t]*(#|$)/) continue
                    p = index(z, "|"); if (p == 0) continue
                    n++; lid[n] = trim(substr(z, 1, p - 1)); lg[n] = trim(substr(z, p + 1)) } }
        index($0, praefix) == 1 {
            r = substr($0, length(praefix) + 1)
            p = index(r, " grund="); if (p == 0) { id = r; g = "" } else { id = substr(r, 1, p - 1); g = substr(r, p + 7) }
            ok = 0
            for (i = 1; i <= n; i++) if (lid[i] == id && lg[i] != "" && index(g, lg[i]) > 0) ok = 1
            print (ok ? "BEKANNT" : "UNBEKANNT") "\t" id "\t" g }' "$PROTOKOLL")"
    N_GEMELDET=0; N_UNBEKANNT=0
    TAB="$(printf '\t')"
    while IFS="$TAB" read -r ART ID GRUND; do
        [ -z "$ART" ] && continue
        N_GEMELDET=$((N_GEMELDET + 1))
        if [ "$ART" = "BEKANNT" ]; then
            sag "   ℹ️  bekannter Übersprung (Liste): $ID – $GRUND"
        else
            N_UNBEKANNT=$((N_UNBEKANNT + 1))
            rot "Prüfblock $UB_NAME: Test $ID übersprungen – Grund: ${GRUND:-ohne Angabe} – nicht in der Liste bekannter Gründe ($BEKANNTE_UEBERSPRUENGE_REL), gilt als rot"
        fi
    done <<< "$BEFUND"
    if [ "$N_GEMELDET" -lt "$2" ]; then
        N_UNBEKANNT=$((N_UNBEKANNT + 1))
        rot "Prüfblock $UB_NAME: $(($2 - N_GEMELDET)) übersprungene(r) Test(s) ohne Angabe von Test und Grund – gilt als rot"
    fi
    [ "$N_UNBEKANNT" -eq 0 ]
}
rot() { ROT="${ROT}❌ $1
"; }
for B in $(grep -E '^PRUEFLISTE block=[A-Za-z0-9_]+ (start|bestanden=)' "$PROTOKOLL" | sed 's/^PRUEFLISTE block=\([A-Za-z0-9_]*\).*/\1/' | sort -u) \
         backend oberflaechen_check browser_tests; do
    case " $GEPRUEFT " in *" $B "*) continue ;; esac
    GEPRUEFT="$GEPRUEFT $B"
    NAME="$(anzeigename "$B")"
    Z="$(grep -E "^PRUEFLISTE block=$B bestanden=" "$PROTOKOLL" | tail -n 1)"
    if [ -z "$Z" ]; then
        case "$B" in
            backend|oberflaechen_check|browser_tests) rot "Prüfblock $NAME: kein Ergebnis gemeldet (lief nicht oder brach ab) – gilt als rot" ;;
        esac
        continue
    fi
    BEST="$(printf '%s' "$Z" | sed -n 's/.* bestanden=\([0-9]*\).*/\1/p')"
    FEHL="$(printf '%s' "$Z" | sed -n 's/.* fehlgeschlagen=\([0-9]*\).*/\1/p')"
    SKIP="$(printf '%s' "$Z" | sed -n 's/.* uebersprungen=\([0-9]*\).*/\1/p')"
    TEST="$(printf '%s' "$Z" | sed -n 's/.* rot=//p')"
    BEST="${BEST:-0}"; FEHL="${FEHL:-0}"; SKIP="${SKIP:-0}"
    if [ "$FEHL" -gt 0 ]; then
        rot "Prüfblock $NAME rot – Test: ${TEST:-unbekannt} ($FEHL fehlgeschlagen)"
    elif [ "$BEST" -eq 0 ] && [ "$SKIP" -gt 0 ]; then
        rot "Prüfblock $NAME: Tests übersprungen, kein Test gelaufen (0 Tests bestanden, $SKIP übersprungen${TEST:+, Grund: $TEST}) – gilt als rot, auch bei Einträgen in der Liste bekannter Gründe"
    elif [ "$BEST" -eq 0 ]; then
        rot "Prüfblock $NAME: keine Tests gefunden (0 Tests) – gilt als rot"
    elif [ "$SKIP" -gt 0 ] && [ "$B" != "backend" ] && [ "$B" != "browser_tests" ]; then
        rot "Prüfblock $NAME: $SKIP Test(s) übersprungen – gilt als rot"
    elif [ "$SKIP" -gt 0 ] && ! uebersprungen_bekannt "$B" "$SKIP"; then
        :   # rot-Meldungen je unbekanntem Übersprung stehen schon in ROT (AK9a/AK9b)
    else
        if [ "$SKIP" -gt 0 ]; then
            sag "✓ Prüfblock $NAME grün ($BEST bestanden; $SKIP übersprungen, alle mit bekanntem Grund laut Liste)"
        else
            sag "✓ Prüfblock $NAME grün ($BEST bestanden)"
        fi
    fi
done
if [ -z "$ROT" ] && [ "$RC" -ne 0 ]; then
    rot "Prüfliste endete mit Fehlercode $RC"
fi
# Dauer je Prüfblock (AK13/AK14): aus den Dauer-Zeilen der Prüfliste
DAUER_BLOECKE=""
for B in backend oberflaechen_check browser_tests; do
    S="$(grep -E "^PRUEFLISTE block=$B dauer=[0-9]+" "$PROTOKOLL" | tail -n 1 | sed 's/.*dauer=//')"
    [ -n "$S" ] || continue
    DAUER_BLOECKE="${DAUER_BLOECKE:+$DAUER_BLOECKE · }$(anzeigename "$B") $((S / 60)) min $((S % 60)) s"
done
sag "⏱  Gesamtdauer des Probelaufs: $((DAUER / 60)) min $((DAUER % 60)) s"
[ -n "$DAUER_BLOECKE" ] && sag "   Prüfblöcke: $DAUER_BLOECKE"

if [ -n "$ROT" ]; then
    sag ""
    sag "❌ Probelauf ROT – nichts wird hochgeladen."
    printf '%s' "$ROT" | while IFS= read -r Z; do sag "   $Z"; done
    sag "   Vollständiges Protokoll: $PROTOKOLL"
    sag "   Es wurde nichts verändert: alte Versionsnummer, nichts eingecheckt, nichts hochgeladen."
    exit 1
fi
sag "✅ Probelauf grün."

# Fassung während des Probelaufs unverändert? (AK3: geprüft = hochgeladen)
while IFS=' ' read -r F H; do
    [ -z "$F" ] && continue
    if [ "$H" = "GELOESCHT" ]; then IST="GELOESCHT"; [ -e "$F" ] && IST="da"; else IST="$(git hash-object -- "$F" 2>/dev/null)"; fi
    [ "$IST" = "$H" ] || abbruch "$F wurde während des Probelaufs geändert – geprüfte und hochzuladende Fassung wären verschieden. Bitte erneut starten."
done < "$ARBEIT/fassung.txt"

# ── Sicherungskopie des Backlogs (AK23b, BACKLOG-Schutz) ─────────────────────
if [ -f "$BACKLOG_REL" ]; then
    mkdir -p "$SCRIPT_DIR/_to_delete"
    cp "$BACKLOG_REL" "$SCRIPT_DIR/_to_delete/BACKLOG.vor_release-${NEW_VERSION:-doku}_${ZEIT}.md"
    sag "Sicherungskopie des Backlogs: $PROJ/_to_delete/BACKLOG.vor_release-${NEW_VERSION:-doku}_${ZEIT}.md"
fi

# ── Festschreiben: ein Commit mit Ticket-Dateien + Versionsnummer (AK22) ──────
ALT_HEAD="$(git rev-parse HEAD)"
[ -f "$GIT_DIR_ABS/index" ] && cp "$GIT_DIR_ABS/index" "$ARBEIT/sicherung-index"
cp "$INDEX_REL" "$ARBEIT/sicherung-index.html"
cp "$SW_REL" "$ARBEIT/sicherung-sw.js"
PHASE="festschreiben"
COMMIT_PFADE="$GEHT_WT"
if [ "$NUR_DOKU" = 0 ]; then
    if ! version_setzen "$REPO_DIR"; then
        sag "❌ Fehler: Versionsnummer nicht setzbar."
        zuruecknehmen; exit 1
    fi
    sag "✓ APP_VERSION und CACHE_NAME auf $NEW_VERSION gesetzt (verifiziert)"
    COMMIT_PFADE="$(printf '%s\n%s\n%s\n' "$GEHT_WT" "$INDEX_REL" "$SW_REL" | grep -v '^$' | sort -u)"
    MSG="release: v${NEW_VERSION} – ${COMMIT_MSG}"
else
    MSG="docs: ${COMMIT_MSG} (keine neue Version)"
fi
if [ -n "$COMMIT_PFADE" ]; then
    # Pathspec bei add UND commit (TASK-98): fremde vorgemerkte Dateien bleiben unberührt vorgemerkt.
    PFADE_DATEI="$ARBEIT/pfade.txt"
    printf '%s\n' "$COMMIT_PFADE" > "$PFADE_DATEI"
    if ! git add -A --pathspec-from-file="$PFADE_DATEI" || \
       ! git commit -q -m "$MSG" --pathspec-from-file="$PFADE_DATEI"; then
        sag ""
        sag "❌ Fehler: 'git commit' ist fehlgeschlagen (z. B. Pre-Commit-Hook lehnt ab)."
        zuruecknehmen; exit 1
    fi
fi

# ── Ein Upload (AK22) ────────────────────────────────────────────────────────
if ! git push -q origin main; then
    sag ""
    sag "❌ Fehler: 'git push origin main' ist fehlgeschlagen (z. B. Netzwerk oder main ist"
    sag "   zwischenzeitlich auf GitHub weitergegangen). Nichts liegt auf GitHub."
    zuruecknehmen
    sag "   Ein erneuter Start zählt die Versionsnummer genau einmal hoch."
    exit 1
fi
PHASE="hochgeladen"

VEROEFFENTLICHT="$(git log --reverse --format='   - %h %s' "$R..HEAD")"
if [ "$NUR_DOKU" = 0 ]; then
    if ! git tag "v${NEW_VERSION}"; then
        sag ""
        sag "❌ Fehler: 'git tag v${NEW_VERSION}' ist fehlgeschlagen, ABER der Release-Commit ist"
        sag "   bereits auf GitHub – kein Rollback mehr möglich."
        sag "   Bitte manuell nachholen:"
        sag "     git tag \"v${NEW_VERSION}\" && git push origin \"v${NEW_VERSION}\""
        exit 1
    fi
    if ! git push -q origin "v${NEW_VERSION}"; then
        sag ""
        sag "❌ Fehler: 'git push origin v${NEW_VERSION}' ist fehlgeschlagen, ABER Commit und Tag"
        sag "   existieren bereits lokal bzw. auf GitHub – kein Rollback nötig."
        sag "   Bitte manuell nachholen:"
        sag "     git push origin \"v${NEW_VERSION}\""
        exit 1
    fi
fi

# ── Abschluss (AK28) ─────────────────────────────────────────────────────────
sag ""
if [ "$NUR_DOKU" = 0 ]; then
    sag "✅ Veröffentlicht: v${NEW_VERSION}. GitHub prüft und deployt jetzt automatisch."
else
    sag "✅ Veröffentlicht – keine neue Version (nur Doku, bleibt $CURRENT_VERSION)."
fi
sag "   Mitveröffentlichte Commits:"
sag "$VEROEFFENTLICHT"
[ -n "${DAUER_BLOECKE:-}" ] && sag "   Probelauf:      $((DAUER / 60)) min $((DAUER % 60)) s ($DAUER_BLOECKE)"
sag "   GitHub-Prüfung: $GITHUB_PRUEFUNG"
sag "   App:            $APP_URL"
sag "   Protokoll:      $PROTOKOLL"
exit 0
