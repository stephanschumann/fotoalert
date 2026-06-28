# FotoAlert – Deployment-Guide
## Vollständige Schritt-für-Schritt Anleitung

---

## Wie hängt alles zusammen?

Bevor du anfängst, hier das große Bild — damit du weißt, warum du was tust:

```
Dein iPhone
    │  tippt: https://fotoalert.deinedomain.com
    ▼
Squarespace-DNS
    │  kennt "fotoalert" → zeigt auf deinen Hetzner-Server
    ▼
Hetzner-Server (Frankfurt, ~4,49 €/Monat)
    │
    ├── Caddy          → nimmt HTTPS-Anfragen entgegen, gibt grünes Schloss
    ├── FotoAlert-App  → antwortet mit Events, Locations etc.
    └── Precompute     → läuft täglich 05:30 Uhr automatisch
```

```
Dein Mac
    │  git push (Code hochladen)
    ▼
GitHub (kostenloser Code-Speicher)
    │  erkennt automatisch: neuer Code!
    ▼
GitHub Actions (automatischer Helfer)
    │  loggt sich per SSH auf Hetzner ein
    │  installiert neue Version, startet App neu
    ▼
App ist live — in ~60 Sekunden
```

**Was du dauerhaft tust:** `git push` — das war's. Alles andere läuft automatisch.

---

## Welche Dienste brauchst du?

| Dienst | Wofür | Kosten |
|---|---|---|
| **Hetzner** | Server, auf dem die App läuft | ~4,49 €/Monat |
| **GitHub** | Code online speichern + Deploy auslösen | Kostenlos |
| **Squarespace** | Subdomain für die App | Hast du bereits |
| **Caddy** | HTTPS (grünes Schloss), läuft auf Server | Kostenlos |

---

## Überblick: Die 8 Schritte

```
Schritt 1 → Git auf dem Mac einrichten          (5 Min.)
Schritt 2 → GitHub-Account + Repository         (10 Min.)
Schritt 3 → Hetzner-Server erstellen            (5 Min.)  → du bekommst eine IP-Adresse
Schritt 4 → Squarespace: Subdomain einrichten   (5 Min.)  → nutzt die IP aus Schritt 3
Schritt 5 → Server-Setup ausführen              (10 Min.) → installiert alles automatisch
Schritt 6 → Deploy-Schlüssel einrichten         (10 Min.) → GitHub darf auf Server
Schritt 7 → Ersten automatischen Deploy testen  (5 Min.)
Schritt 8 → App auf iPhone installieren         (2 Min.)
```

---

## Schritt 1 – Git auf dem Mac einrichten

Git ist ein Programm, das Änderungen an deinem Code aufzeichnet — wie der Versionsverlauf in Word, nur für Code.

**1a. Terminal öffnen**
Drücke `Cmd + Leertaste`, tippe „Terminal", drücke Enter.

**1b. Prüfen ob Git installiert ist**
```bash
git --version
```
Zeigt es eine Versionsnummer? Gut, weiter zu 1c.
Erscheint ein Installations-Dialog? Klicke „Installieren" und warte.

**1c. Git einmalig konfigurieren**
```bash
git config --global user.name "Stephan Schumann"
git config --global user.email "stephanschumann@me.com"
```

**1d. In den Projektordner navigieren**
```bash
cd "/Users/stephan/Claude/Projects/Foto Location Guide"
```

**1e. Git für das Projekt initialisieren**
```bash
git init
git add .
git commit -m "FotoAlert v1.4.2 – erster Commit"
```
Du siehst eine Liste von Dateien und am Ende eine Zeile mit „main (root-commit)". Das ist gut.

---

## Schritt 2 – GitHub-Account und Repository

GitHub ist der Ort, wo dein Code online gespeichert wird und von wo das automatische Deployment ausgelöst wird.

**2a. Account erstellen**
1. Gehe auf [https://github.com](https://github.com)
2. Klicke „Sign up"
3. E-Mail, Passwort und Benutzernamen wählen (z.B. `stephan-schumann`)
4. Den kostenlosen „Free"-Plan wählen
5. E-Mail-Adresse bestätigen

**2b. Neues Repository erstellen**
1. Klicke nach dem Login oben rechts auf das **+** Symbol → „New repository"
2. Fülle aus:
   - **Repository name:** `fotoalert`
   - **Visibility:** Private *(nur du siehst es)*
   - **„Initialize this repository":** **NICHT ankreuzen** *(wichtig!)*
3. Klicke „Create repository"

**2c. Code von deinem Mac zu GitHub hochladen**

GitHub zeigt dir nach dem Erstellen eine Seite mit Befehlen. Nutze die Sektion
„…or push an existing repository from the command line".
Ersetze `DEIN-USERNAME` durch deinen GitHub-Benutzernamen:

```bash
git remote add origin https://github.com/DEIN-USERNAME/fotoalert.git
git branch -M main
git push -u origin main
```

Terminal fragt nach Benutzername — das ist dein GitHub-Benutzername.
Beim Passwort: GitHub akzeptiert hier kein normales Passwort, sondern einen
**Personal Access Token**. Den erstellst du so:

1. GitHub → rechts oben dein Profilbild → **Settings**
2. Ganz unten links: **Developer settings**
3. **Personal access tokens** → **Tokens (classic)** → „Generate new token (classic)"
4. Note: `fotoalert-push`
5. Expiration: `No expiration`
6. Haken setzen bei: **repo** *(erste Checkbox, wählt alles darunter aus)*
7. Klicke „Generate token"
8. Den angezeigten Token **sofort kopieren** (er wird nur einmal gezeigt!)
9. Diesen Token als Passwort im Terminal eingeben

✅ Wenn du jetzt auf GitHub gehst und dein Repository öffnest, siehst du alle Dateien.

---

## Schritt 3 – Hetzner-Server erstellen

Hetzner ist ein deutsches Unternehmen, das dir einen kleinen Computer in Frankfurt mietet (~4,49 €/Monat, monatlich kündbar).

**3a. Account erstellen**
1. Gehe auf [https://www.hetzner.com/cloud](https://www.hetzner.com/cloud)
2. Klicke „Get started" und erstelle einen Account
3. Kreditkarte oder PayPal für die Abrechnung hinterlegen

**3b. SSH-Schlüssel erstellen**

Damit du dich sicher mit dem Server verbinden kannst, brauchst du einen SSH-Schlüssel — das ist wie ein digitaler Hausschlüssel.

Im Terminal auf deinem Mac:
```bash
ssh-keygen -t ed25519 -C "mein-mac"
```
Alle Fragen einfach mit Enter bestätigen (kein Passwort setzen).

Den öffentlichen Schlüssel anzeigen und kopieren:
```bash
cat ~/.ssh/id_ed25519.pub
```
Die angezeigte Zeile (beginnt mit `ssh-ed25519 AAAA...`) komplett kopieren.

**3c. Server erstellen**
1. Im Hetzner Cloud Dashboard: Klicke „Add Server"
2. Wähle:
   - **Location:** Nuremberg oder Falkenstein (Deutschland)
   - **Image:** Ubuntu 22.04
   - **Type:** Shared CPU → **CX22** (2 vCPUs, 4 GB RAM)
   - **SSH Keys:** Klicke „Add SSH Key", füge den kopierten Schlüssel ein, Name: `mein-mac`
   - **Server name:** `fotoalert-server`
3. Klicke „Create & Buy Now"

**3d. IP-Adresse notieren**
Nach ~30 Sekunden erscheint der Server in der Übersicht.
Notiere die **IPv4-Adresse** (z.B. `157.90.123.45`) — du brauchst sie in Schritt 4 und 5.

---

## Schritt 4 – Squarespace: Subdomain einrichten

Du richtest eine Subdomain auf deiner bestehenden Domain ein — z.B. `fotoalert.deinedomain.com`.
Deine Squarespace-Website bleibt davon vollständig unberührt.

**4a. Squarespace DNS öffnen**
1. Logge dich bei Squarespace ein
2. Klicke links im Menü auf **Domains**
3. Klicke auf deine Domain
4. Klicke auf **DNS-Einstellungen** (oder „DNS Settings")

**4b. Neuen A-Record hinzufügen**
Klicke auf „Eintrag hinzufügen" (oder „Add Record") und fülle aus:

| Feld | Wert |
|---|---|
| **Typ / Type** | `A` |
| **Host / Name** | `fotoalert` *(ergibt dann fotoalert.deinedomain.com)* |
| **Wert / Data / Points to** | deine Hetzner-IP aus Schritt 3 (z.B. `157.90.123.45`) |
| **TTL** | Standard lassen |

Klicke „Speichern" / „Save".

> ⏳ DNS-Änderungen brauchen 15–60 Minuten bis sie aktiv sind.
> Du kannst in der Zwischenzeit mit Schritt 5 weitermachen.

**Optional:** Du kannst auf deiner Squarespace-Website eine Seite oder einen Button erstellen,
der auf `https://fotoalert.deinedomain.com` verlinkt. Das ist unabhängig vom technischen Setup.

---

## Schritt 5 – Server-Setup ausführen

Jetzt richtest du den Server ein. Das Setup-Script installiert alles automatisch.

**5a. Zwei Zeilen in der Datei anpassen**

Öffne `FotoAlert/deploy/setup_server.sh` und ändere ganz oben:

```bash
DOMAIN="fotoalert.deinedomain.com"   # ← deine echte Subdomain
CODEBERG_USER="DEIN-GITHUB-USERNAME"  # ← dein GitHub-Benutzername
```

Speichere die Datei.

> Hinweis: Der Parameter heißt noch `CODEBERG_USER` im Script, funktioniert aber für GitHub genauso —
> der Wert wird nur beim initialen Clone verwendet.

**5b. Änderung auf GitHub hochladen**
```bash
git add FotoAlert/deploy/setup_server.sh
git commit -m "Deploy: Domain und Benutzername konfiguriert"
git push
```

**5c. Setup auf dem Server ausführen**

Ersetze `157.90.123.45` durch deine echte Hetzner-IP:
```bash
cat "/Users/stephan/Claude/Projects/Foto Location Guide/FotoAlert/deploy/setup_server.sh" \
  | ssh root@157.90.123.45 "bash -s"
```

Das Script läuft ~5–10 Minuten. Am Ende siehst du:
```
✅ FotoAlert läuft erfolgreich!
   Lokal: http://localhost:8000
   Öffentlich: https://fotoalert.deinedomain.com
```

Falls eine Fehlermeldung erscheint: die komplette Ausgabe kopieren und Claude fragen.

**5d. Testen**
Öffne im Browser: `https://fotoalert.deinedomain.com`
*(Falls DNS noch nicht propagiert ist, kurz warten und nochmal versuchen.)*

---

## Schritt 6 – Deploy-Schlüssel einrichten

Damit GitHub Actions automatisch auf deinen Server deployen darf, brauchst du
einen speziellen Schlüssel — wie einen Hausschlüssel, den du GitHub gibst.

**6a. Schlüsselpaar erstellen**
```bash
ssh-keygen -t ed25519 -f ~/.ssh/fotoalert_deploy -C "github-deploy" -N ""
```
Das erstellt:
- `~/.ssh/fotoalert_deploy` → **privater Schlüssel** (kommt zu GitHub, geheim halten)
- `~/.ssh/fotoalert_deploy.pub` → **öffentlicher Schlüssel** (kommt auf den Server)

**6b. Öffentlichen Schlüssel auf den Server kopieren**
```bash
cat ~/.ssh/fotoalert_deploy.pub | ssh root@157.90.123.45 \
  "cat >> /opt/fotoalert/.ssh/authorized_keys"
```

**6c. Privaten Schlüssel anzeigen und kopieren**
```bash
cat ~/.ssh/fotoalert_deploy
```
Die **gesamte Ausgabe** kopieren — von `-----BEGIN OPENSSH PRIVATE KEY-----`
bis einschließlich `-----END OPENSSH PRIVATE KEY-----`.

**6d. Secrets in GitHub eintragen**
1. Gehe auf [github.com](https://github.com) → dein `fotoalert`-Repository
2. Klicke oben auf **Settings**
3. Links im Menü: **Secrets and variables** → **Actions**
4. Klicke „New repository secret" und erstelle drei Einträge:

| Name | Wert |
|---|---|
| `DEPLOY_SSH_KEY` | Der gesamte private Schlüssel aus Schritt 6c (alle Zeilen) |
| `SERVER_IP` | deine Hetzner-IP (z.B. `157.90.123.45`) |
| `SERVER_USER` | `fotoalert` |

---

## Schritt 7 – Ersten automatischen Deploy testen

**7a. Workflow-Datei auf GitHub hochladen**
```bash
git add .github/workflows/deploy.yml
git commit -m "CI/CD: Automatisches Deployment via GitHub Actions"
git push
```

**7b. Pipeline beobachten**
1. Gehe auf GitHub → dein Repository
2. Klicke oben auf **Actions**
3. Du siehst einen laufenden Workflow
   - 🟡 gelber Kreis = läuft gerade
   - ✅ grüner Haken = erfolgreich
   - ❌ rotes X = Fehler
4. Nach ~60 Sekunden sollte ✅ erscheinen

Falls ❌ erscheint: auf den Workflow klicken → auf den fehlgeschlagenen Schritt klicken →
Fehlermeldung kopieren → Claude fragen.

**7c. App im Browser testen**
Öffne `https://fotoalert.deinedomain.com` — du solltest FotoAlert sehen.

---

## Schritt 8 – App auf dem iPhone installieren

1. Öffne **Safari** auf deinem iPhone 14 Pro
   *(wichtig: Safari, nicht Chrome — nur Safari unterstützt PWA-Installation auf iOS)*
2. Tippe in die Adressleiste: `https://fotoalert.deinedomain.com`
3. Tippe auf das **Teilen-Symbol** (Quadrat mit Pfeil nach oben, am unteren Bildschirmrand)
4. Scrolle in der Liste nach unten → tippe **„Zum Home-Bildschirm"**
5. Name anpassen falls gewünscht → tippe **„Hinzufügen"** oben rechts
6. Das FotoAlert-Icon erscheint auf deinem Home-Bildschirm
7. Tippe es an → die App startet im Vollbild, ohne Safari-Leiste ✅

---

## Ab jetzt: Dein normaler Arbeitsablauf

### Code ändern und deployen
```bash
# Im Projektordner:
git add .
git commit -m "Kurze Beschreibung der Änderung"
git push
# → GitHub Actions startet automatisch
# → In ~60 Sekunden ist die neue Version auf deinem iPhone
```

### Rollback auf vorherige Version

Jeder Release wird als Git-Tag gespeichert (`v1.2.3`). Du hast zwei Wege:

**Option A — ein Commit zurück (Standardfall):**
```bash
ssh fotoalert@157.90.123.45
bash /opt/fotoalert/app/FotoAlert/deploy/rollback.sh
```
Das Skript fragt nach Bestätigung und zeigt aktuellen + Ziel-Commit vor dem Rollback.

**Option B — auf einen bestimmten Release-Tag zurück:**
```bash
ssh fotoalert@157.90.123.45
bash /opt/fotoalert/app/FotoAlert/deploy/rollback.sh v1.4.2
```

**Alle Releases anzeigen (lokal):**
```bash
git tag --sort=-version:refname | head -10
```

**Hinweis Cache-Kompatibilität:** JSON-Caches (`/opt/fotoalert/cache/`) liegen außerhalb von Git und werden durch einen Rollback nicht verändert. Bei sehr alten Rollback-Zielen (neue Cache-Felder fehlen) nach dem Rollback manuellen Recompute starten:
```bash
ssh fotoalert@157.90.123.45
sudo systemctl start fotoalert-precompute.service
```

### Logs anschauen
```bash
ssh fotoalert@157.90.123.45
sudo journalctl -u fotoalert -n 50 --no-pager
```

### Was du NIE manuell tun musst
- ❌ SW-Version bumpen → passiert automatisch bei jedem Deploy
- ❌ Server neustarten → passiert automatisch
- ❌ SSL-Zertifikat verlängern → Caddy erledigt das automatisch alle 90 Tage
- ❌ Precompute starten → läuft täglich um 05:30 Uhr von selbst

---

## Kosten-Übersicht

| Was | Dienst | Kosten |
|---|---|---|
| Server | Hetzner CX22, Frankfurt 🇩🇪 | ~4,49 €/Monat |
| Code-Hosting + CI/CD | GitHub | Kostenlos |
| HTTPS-Zertifikat | Let's Encrypt via Caddy | Kostenlos |
| Domain / Subdomain | Deine Squarespace-Domain | Hast du bereits |

**Gesamtkosten: ~4,49 €/Monat**

---

## Troubleshooting: Die häufigsten Probleme

| Problem | Wahrscheinliche Ursache | Lösung |
|---|---|---|
| `https://fotoalert.deinedomain.com` lädt nicht | DNS noch nicht propagiert | 30–60 Minuten warten, dann nochmal |
| `Permission denied` im Terminal | SSH-Key nicht korrekt hinterlegt | Schritt 3b wiederholen |
| `git push` fragt nach Passwort und scheitert | GitHub braucht Token statt Passwort | Personal Access Token aus Schritt 2c verwenden |
| GitHub Actions ❌ | Secret falsch eingegeben | Secrets in GitHub prüfen (Schritt 6d) |
| App auf iPhone zeigt alten Stand | Service Worker Cache | Develop → Empty Caches → Cmd+R in Safari |
| Server antwortet nicht | App abgestürzt | `sudo journalctl -u fotoalert -n 50` |

Bei jedem Problem: Fehlermeldung komplett kopieren und Claude fragen.
