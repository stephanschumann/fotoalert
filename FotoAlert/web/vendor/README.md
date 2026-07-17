# web/vendor/ — selbst gehostete Fremd-Bibliotheken

Dieser Ordner enthält Bibliotheken, die früher per CDN geladen wurden und seit
TASK-84 (Option B) fest im Repo liegen, statt zur Laufzeit von einem fremden
Server geladen zu werden.

| Bibliothek | Version | Bezugsquelle | Datum | Original-Adresse(n) |
|---|---|---|---|---|
| Leaflet | 1.9.4 | cdnjs.cloudflare.com | 2026-07-16 | `https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js`<br>`https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css` |
| astronomy-engine | 2.1.19 | cdn.jsdelivr.net | 2026-07-16 | `https://cdn.jsdelivr.net/npm/astronomy-engine@2.1.19/astronomy.browser.min.js` |

Bei künftigen Sicherheitsupdates dieser Bibliotheken: Version hier aktualisieren
und neue Datei einspielen (TASK-84).
