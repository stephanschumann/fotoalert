# Qualitäts-Audit: FotoAlert (Live-App)

*Geprüft: 27.07.2026, live unter https://fotoalert.stephanschumann.com/, echte Bedienung im Browser (kein lokaler Nachbau).*

## 1. Kurze Zusammenfassung

FotoAlert liefert im Kern das, was es verspricht: Die Grundrechnung stimmt — die Gesamt-Score-Formel ("Astronomie × 65 % + Wetter × 35 %") und die Azimut-Berechnung zwischen Fotograf-Standort und Motiv wurden anhand der angezeigten GPS-Koordinaten von Hand nachgerechnet, beides ging exakt auf. Die App ist inhaltlich reichhaltig (Wetter, Mondphasen, Sichtachsen, Live-Astro-Visualisierung) und war ohne Login-Wand vollständig zugänglich — allerdings lief die gesamte Prüfung in einer bereits als "Host" authentifizierten Sitzung (Stephans eigener Browser), sodass unklar ist, ob eine unangemeldete Person dieselben Bearbeitungs- und Admin-Funktionen sieht (siehe Abschnitt 5).

Das größte Problem: Mehrere Stellen der App zeigen sich selbst widersprechende oder falsch vorausgefüllte Daten — ein Bearbeitungsformular lädt die falsche Kategorie einer Location, eine Mondphase wird "Halbmond" genannt obwohl 96–99 % beleuchtet angegeben sind, und der Kopfbereich zeigt bei aktivem Mehrfachfilter einen englischen Marketing-Satz statt der eigentlichen Statuszeile. Dazu kommt eine verwirrende Doppelverwendung des Wortes "Geprüft" für zwei völlig verschiedene Sachverhalte. In der aktuellen Form würde ich das nicht ungeprüft weiterlaufen lassen — die gefundenen Probleme sind überschaubar, aber teils vertrauensschädigend, weil sie genau die Daten betreffen, um die es in einer Astro-Foto-App geht (Zeit, Winkel, Mondphase, Kategorie).

## 2. Bewertung nach Prüfdimension

| Dimension | Einschätzung | Anzahl Befunde |
|---|---|---|
| 1. Inhaltliche Klarheit | befriedigend – Fachbegriffe gut im Glossar erklärt, aber auf den Karten selbst mehrdeutig | 2 |
| 2. Ablauf/Mechanik | gut mit Ausreißern – Kernrechnung stimmt, aber Statusanzeigen widersprechen sich teils | 3 |
| 3. Wirkung fürs Zielpublikum | gut | 1 |
| 4. Bedienung | befriedigend – funktioniert meist sauber, aber ein sichtbarer Anzeige-Bug im Kopfbereich | 2 |
| 5. Konsistenz | mangelhaft an einer Stelle – Datenmismatch zwischen Formular und Anzeige | 1 |
| 6. Technische Korrektheit | gut mit einem harten Ausreißer – Mondphasen-Label falsch, Kategorie-Vorbelegung falsch | 2 |

(Einzelne Befunde berühren mehrere Dimensionen gleichzeitig, daher Überschneidungen in der Zählung.)

## 3. Befunde

### KRITISCH

**Bearbeitungsformular einer Location zeigt eine andere Kategorie als überall sonst angezeigt**
- Fundstelle: Location "Nikolaisee – Baumspiegelung" (Locations-Liste, Suche und Detailansicht zeigen übereinstimmend das Tag "Wasser & Spiegelung"). Öffnet man über das Stift-Symbol das Formular "Location bearbeiten", zeigt das Dropdown-Feld "Kategorie" dort "Skyline & Architektur" – eine andere Kategorie, die nirgends sonst mit dieser Location verknüpft ist.
- Problem: Das Bearbeitungsformular lädt beim Öffnen offenbar nicht zuverlässig den tatsächlich gespeicherten Kategoriewert.
- Auswirkung: Würde jemand die Location aus einem anderen Grund bearbeiten und einfach speichern (ohne die Kategorie bewusst zu prüfen), würde die Location dabei unbemerkt von "Wasser & Spiegelung" auf "Skyline & Architektur" umkategorisiert – ein Nutzer, der gezielt nach Wasser-Spiegelungs-Spots filtert, würde diesen Ort danach nicht mehr finden.
- Empfehlung: Beim Öffnen des Bearbeitungsformulars den tatsächlich gespeicherten Kategoriewert vorbelegen (nicht einen Default-/ersten Listenwert), und stichprobenartig weitere Locations auf denselben Fehler prüfen.

**Kopfzeile zeigt englischen Platzhaltertext statt Status, sobald mehr als ein Filter aktiv ist**
- Fundstelle: Kopfbereich der App, normalerweise "Heute: 4 Chancen · Bester Score 84 %". Sobald im Filter-Dialog neben der Standard-Wahrscheinlichkeitsschwelle (≥ 70 %) zusätzlich ein Ereignistyp ausgewählt wird (getestet mit "Milchstraße" und separat mit "Goldene Stunde"), ändert sich die Zeile zu: "Capture moments that matter." Reproduziert in zwei unabhängigen Testläufen.
- Problem: Ein englischer Marketing-Satz ersetzt die deutsche Statuszeile; das Filter-Symbol-Badge zeigt in diesem Zustand korrekt "2" an, der Zeileninhalt selbst ist aber ein Fremdkörper.
- Auswirkung: Bruch der Sprachkonsistenz (die App ist sonst konsequent deutsch) und Verlust einer nützlichen Information (wie viele Chancen es heute gibt) genau in dem Moment, in dem ein Nutzer aktiv filtert und die Info am meisten braucht.
- Empfehlung: Den Fallback-/Platzhaltertext entfernen bzw. durch die tatsächliche gefilterte Statuszeile ersetzen (z. B. "36 von 500 Chancen sichtbar", wie es der Filter-Dialog selbst korrekt anzeigt).

**Administrative Funktionen ohne erkennbare Zugriffsschranke im Client sichtbar (mit Vorbehalt, siehe Abschnitt 5)**
- Fundstelle: Einstellungen → "Backend": Dropdown "Server URL" (aktuell "Prod (fotoalert.stephanschumann.com)") sowie Button "Astronomie neu berechnen" ("Dauert 2–5 Minuten"); Locations-Detailansicht: Stift- und Papierkorb-Symbol zum Bearbeiten/Löschen jeder Location, direkt neben jedem Eintrag, ohne Bestätigungsschritt sichtbar getestet.
- Problem: Diese Funktionen wirken wie Werkzeuge für den Betreiber (Serverumgebung wechseln, teuren Neuberechnungs-Job anstoßen, Inhalte löschen), sind aber ohne sichtbare zusätzliche Anmeldung direkt im normalen App-Menü erreichbar.
- Auswirkung: Falls diese Ansicht auch für nicht angemeldete Besucher der öffentlichen URL identisch aussieht, könnte jede Person mit dem Link kuratierte Locations verändern/löschen oder einen 2–5-minütigen Server-Job auslösen.
- Empfehlung: In einem privaten/inkognito-Fenster ohne bestehende Sitzung prüfen, ob diese Bedienelemente dort ebenfalls sichtbar/klickbar sind; falls ja, hinter eine echte Authentifizierung legen.

### ERNSTHAFT

**Mondphasen-Bezeichnung widerspricht dem angegebenen Beleuchtungsgrad**
- Fundstelle: Mehrere Karten, z. B. "Mondaufgang – Schloss Babelsberg" (heute) und "Mondaufgang – Schloss Babelsberg von Glienicker Brücke" (morgen): Beschreibungstext wörtlich "Mondphase: Zunehmender Halbmond (96 % beleuchtet)" bzw. "(99 % beleuchtet)"; im "Live-Astro"-Werkzeug identisch: "Mondphase … 99 % beleuchtet".
- Problem: Ein Halbmond ist per Definition etwa zur Hälfte beleuchtet (~50 %); ein Wert von 96–99 % beschreibt einen nahezu vollen Mond. Name und Zahl passen nicht zusammen.
- Auswirkung: Nutzer, die sich auf die Mondphasen-Angabe verlassen (z. B. um die Belichtung zu planen oder die Bildwirkung einzuschätzen), bekommen eine falsche Vorstellung vom tatsächlichen Erscheinungsbild des Mondes.
- Empfehlung: Zuordnung von Phasenname zu Beleuchtungsgrad-Prozent korrigieren (bei ~96–99 % müsste es "Zunehmender Mond" bzw. kurz vor Vollmond heißen, nicht "Halbmond").

**Zwei unterschiedliche Prüf-Konzepte teilen sich dieselben Badge-Texte "Geprüft"/"Nicht geprüft"**
- Fundstelle: Jede Ereignis-Karte kann zwei grundverschiedene Badges gleichzeitig zeigen: einen grünen "✓ Geprüft" (laut Tooltip "Verifikationsstatus": "ein Nutzer war vor Ort und hat die Angaben … bestätigt") und direkt darunter einen grauen "◎ Nicht geprüft" (laut Tooltip "Sichtachsen-Status": "die externen Höhen-/Gebäudedaten waren beim letzten Versuch nicht verfügbar").
- Problem: Auf den ersten Blick liest sich das wie ein Widerspruch ("geprüft" und "nicht geprüft" zugleich), obwohl es zwei unabhängige Dinge sind (Vor-Ort-Besuch vs. automatische Sichtlinien-Prüfung). Nur über zwei separate Info-Icons lässt sich das auflösen.
- Auswirkung: Verunsicherung, ob eine Empfehlung nun verlässlich ist oder nicht – gerade bei einer App, deren Kernversprechen Verlässlichkeit von Ort und Zeitpunkt ist.
- Empfehlung: Unterschiedliche Begriffe verwenden, z. B. "Vor Ort bestätigt" / "Vor Ort noch nicht bestätigt" für den einen Status und "Sichtlinie frei" / "Sichtlinie ungeprüft" für den anderen, damit die Wortwahl selbst schon den Unterschied trägt.

**Ausgerechnet bei einem "Sichtachsen-Alignment"-Ereignis ist die Sichtachse nicht geprüft**
- Fundstelle: Karte "Sonne in Sichtachse – THF Feld & Skyline" (Tempelhofer Feld, Azimut Sonne = Azimut Sichtachse = 301,1°): Badge "◎ Nicht geprüft" (Sichtachsen-Status).
- Problem: Genau der Ereignistyp, dessen ganze Aussage auf einer exakten, freien Sichtlinie beruht, wird mit einem "Sichtachse ungeprüft"-Hinweis ausgeliefert, ohne dass das in der Kurzansicht besonders hervorgehoben würde.
- Auswirkung: Nutzer könnten losfahren in der Annahme, die Sichtachse sei frei, und vor Ort feststellen, dass ein Gebäude im Weg steht.
- Empfehlung: Bei Alignment-Ereignissen mit ungeprüfter Sichtachse einen deutlicheren Warnhinweis in der Kartenübersicht zeigen (nicht nur im aufgeklappten Detail).

### MODERAT

**Wetter-Score und Wolkenstimmung wirken auf derselben Karte widersprüchlich**
- Fundstelle: Karte "Goldene Wolken": "Wetter 20 % – Schwierig" direkt neben "Wolkenstimmung 89 % · Exzellent".
- Problem: Beides sind laut Glossar unterschiedliche, unabhängige Kennzahlen (Wetter-Score bewertet u. a. die Gesamtbewölkung von 82 % als ungünstig; Wolkenstimmung bewertet nur das Potenzial für goldene Wolken anhand der Wolkenschicht-Verteilung) – ohne diesen Hintergrund liest sich "Schwierig" neben "Exzellent" wie ein Fehler.
- Auswirkung: Nutzer, die das Glossar nicht gelesen haben, könnten den beiden Zahlen misstrauen oder falsch gewichten.
- Empfehlung: Auf der Karte selbst einen Kurz-Hinweis ergänzen (z. B. "Wolkenstimmung bewertet nur den goldenen Effekt, nicht die Gesamt-Wetterlage").

**Kompositions-Analyse (Rahmung/Versatz) gibt es bei Sonnen-, aber nicht bei Mond-Ereignissen**
- Fundstelle: Karte "Rote Wolken" zeigt einen Abschnitt "Kompositions-Analyse" mit Höhen- und Seitenversatz zum Motiv. Bei "Mondaufgang – Schloss Babelsberg" (Azimut Himmelsobjekt 131,7° vs. Azimut Sichtachse 157,8°, eine Differenz von 26°) fehlt dieser Abschnitt komplett.
- Problem: Gerade wenn Himmelsobjekt-Richtung und Sichtachse spürbar auseinanderliegen, wäre die Information "wie weit versetzt erscheint der Mond neben dem Motiv" besonders hilfreich – bei Sonnen-Ereignissen gibt es sie, beim Mond nicht.
- Auswirkung: Nutzer können bei Mond-Ereignissen schwerer einschätzen, ob der Mond tatsächlich nah am Motiv erscheint oder deutlich versetzt.
- Empfehlung: Kompositions-Analyse auch für Mond-Ereignisse anbieten.

## 4. Allgemeine Empfehlungen

1. **Formulare immer mit den tatsächlich gespeicherten Werten vorbelegen** – der Kategorie-Mismatch im Bearbeitungsformular deutet auf ein grundsätzliches Muster hin; weitere Formulare sollten stichprobenartig auf dieselbe Klasse von Fehler geprüft werden.
2. **Eine einheitliche Wortliste für Status-Badges einführen**, damit "geprüft" nicht für zwei unabhängige Konzepte (Vor-Ort-Besuch vs. Sichtachsen-Berechnung) wiederverwendet wird.
3. **Platzhalter-/Fallback-Texte durchsuchen und entfernen** – der englische Satz "Capture moments that matter." sollte kein Produktionscode-Pfad mehr sein; das deutet darauf hin, dass es weitere versteckte Fallback-Zustände geben könnte, die nur unter bestimmten Kombinationen sichtbar werden.
4. **Zugriffsrechte für administrative Funktionen einmal bewusst von außen (abgemeldet/inkognito) gegentesten**, bevor die App breiter geteilt wird.
5. **Mondphasen-Berechnung (Name ↔ Beleuchtungsgrad) einmal grundsätzlich durchgehen**, da dieselbe Diskrepanz an mehreren Stellen (verschiedene Tage, verschiedene Locations, Live-Astro-Tool) konsistent auftrat – vermutlich ein zentraler Berechnungs- oder Zuordnungsfehler, kein Einzelfall.

## 5. Was nicht geprüft werden konnte

- **Anmeldezustand:** Der gesamte Test lief in einer bereits als "Host" authentifizierten Sitzung (Stephans eigener, bereits eingeloggter Browser). Bewusst nicht auf "Logout" geklickt, um die reale Sitzung nicht zu beenden. Dadurch bleibt offen, ob eine anonyme/unangemeldete Person dieselben Bearbeitungs-, Lösch- und Backend-Funktionen sieht – das ist die wichtigste offene Frage aus diesem Audit.
- **Echte Zerstörungs-/Kostenoperationen:** Weder den Papierkorb-Button einer Location angeklickt (unwiderrufliches Löschen) noch "Astronomie neu berechnen" ausgelöst (realer 2–5-minütiger Server-Job) noch ein neues Location-Formular tatsächlich abgeschickt, um keine echten Produktionsdaten zu verändern.
- **Push-Benachrichtigungen:** Die Schalter in den Einstellungen ("Besondere Ereignisse", "Goldene & Blaue Stunde", "Milchstraße") wurden nur als UI-Elemente gesehen, eine tatsächliche Zustellung von Benachrichtigungen konnte in dieser Umgebung nicht geprüft werden.
- **GPS-Standortbestimmung** ("Mein Standort setzen" im Location-Formular) wurde nicht getestet, da kein reales Gerätestandort verfügbar war.
- **Echte Wetter-/Astronomiedaten-Richtigkeit gegen eine unabhängige Quelle:** Die Azimut-Berechnung wurde geometrisch aus den GPS-Koordinaten nachgerechnet (stimmte exakt), Sonnenauf-/-untergangszeiten und Wetterprognose selbst konnten nicht gegen eine unabhängige externe Quelle verifiziert werden.
- **Vollständige Abdeckung von Jahreskalender und Scout:** Beide Ansichten wurden nur stichprobenartig geöffnet (Jahreskalender: ein Monat; Scout: die ersten Einträge), nicht vollständig durch alle 2794 bzw. 2232 Einträge durchgeblättert.
- **Bild-Upload-Funktion** ("Bild hochladen") wurde nicht bis zum Abschluss durchgespielt.
- **Tastaturbedienung/Barrierefreiheit** wurde nicht systematisch geprüft (nur Maus-/Touch-Interaktion).
- **Standorte außerhalb Berlin/Brandenburg:** Im Scout- bzw. Milchstraßen-Filter tauchten Locations in den Dolomiten (Südtirol, z. B. "Passo Giau", "Seiser Alm – Langkofelblick") auf, obwohl die App als Berlin/Brandenburg-Tool beschrieben ist. Nur beiläufig bemerkt, nicht tiefer untersucht, ob das bewusst erweiterter Umfang oder eine Inkonsistenz ist – daher hier nur als Beobachtung vermerkt, nicht als eingestufter Befund.
