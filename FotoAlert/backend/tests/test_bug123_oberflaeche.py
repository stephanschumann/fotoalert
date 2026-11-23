"""BUG-123 · Der Kalender zeigt nach einem Neustart einen Hinweis statt stumm zu warten (Oberfläche).

Testfälle der Spec in BACKLOG.md (Abschnitt „Analyse & Spec (BUG-123)“): T-03 (Hinweis im offenen Kalender),
T-04 (Gegenprobe: fertiger Monat ohne Hinweis) und T-05 (Termine erscheinen von selbst, Hinweis verschwindet).
Entscheidung Stephan 2026-11-22, Frage 1: Der Kalender zeigt sofort „wird gerade berechnet, bitte kurz warten“,
danach die Termine. Erlaubter Bereich laut Spec: nur das Kalender-Laden in der App.

Test-Agent (Orchestrator Phase 3), geschrieben VOR der Umsetzung, 2026-11-22.

Nicht hier (nur im echten Browser beim Abschluss prüfbar): wie der Hinweis aussieht, Hell/Dunkel, die echte Wartezeit.
Quelle der erwarteten Werte: Spec BUG-123 (Hinweiswortlaut aus der Entscheidung von Stephan; „solange der Server
‚wird berechnet‘ meldet, weiter nachfragen“). Der Server meldet im Test 8-mal „wird berechnet“ (mehr als die 3
Wiederholungen von heute) und danach 2 Termine.
"""
# ───────────────────────────────────────────────────────────────────────────────
# Technik (Schicht 3/4), bewusst außerhalb der Fachsprache: Der Kalender-Teil der App wird wörtlich aus web/index.html
# geschnitten und unter Node.js ausgeführt (Muster wie in test_us138_ortszeit.py: kein Browser, kein Server). Die
# Antworten des Servers sind festgelegt (erfundene Termine, kein Netz, keine echte Zwischenspeicher-Datei). Wartezeiten
# der App werden für den Test verkürzt (jede gilt als 1 Millisekunde); Datum und Uhrzeit bleiben echt.
# ───────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

INDEX_HTML = Path(__file__).resolve().parents[2] / "web" / "index.html"
node_required = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js nicht installiert")

HINWEIS_TEILE = ("wird gerade berechnet", "bitte kurz warten")   # Wortlaut: Entscheidung Stephan 2026-11-22, Frage 1
HINWEIS_SATZ = "Der Kalender wird gerade berechnet, bitte kurz warten."
TITEL = ["BUG-123 Übungstermin Nordufer", "BUG-123 Übungstermin Südhang"]
ANZAHL_WARTEN = 8


# ═══════════════════════════════════════════════════════════════════════════════════
# Treiber (Schicht 3/4)
# ═══════════════════════════════════════════════════════════════════════════════════
def _kalenderteil():
    """Der Kalender-Teil der App, wörtlich aus web/index.html geschnitten."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    start = html.index("const MONTHS_DE")
    end = html.index("// STANDORT-VERIFIKATION")
    return html[start:end]


_SKRIPT = r"""
const realSetTimeout = setTimeout, realSetInterval = setInterval;
const WARTEN = %(warten)d;           // so oft meldet der Übungs-Server „wird berechnet“, danach „ok“
const HINWEIS_SATZ = %(satz)s;
const TERMINE = %(termine)s;
const toasts = [], snaps = [], els = {};
let n = 0;

function element(id) {
  const store = { innerHTML: '', textContent: '', id: id, style: {}, dataset: {}, className: '', value: '' };
  const classList = { add() {}, remove() {}, toggle() {}, contains() { return false; } };
  return new Proxy(store, {
    get(t, p) { if (p in t) return t[p]; if (p === 'classList') return classList; return function () { return null; }; },
    set(t, p, v) { t[p] = v; return true; },
  });
}
const document = {
  getElementById(id) { return els[id] || (els[id] = element(id)); },
  querySelector() { return null; }, querySelectorAll() { return []; },
  createElement() { return element('neu'); }, body: element('body'),
};
document.getElementById('feed-content');

const dummy = new Proxy(function () {}, {
  get(t, p) { return p === Symbol.toPrimitive ? () => '' : dummy; }, apply() { return dummy; }, construct() { return dummy; },
});
const stubs = {
  document,
  Feed: { mode: 'calendar', data: [] },
  Filter: { apply(e) { return e; } },
  Search: { query: '' },
  Gebiete: { allPaused() { return false; }, emptyAllHtml() { return ''; } },
  Locations: { nameFor(id, name) { return name || id; }, all: [] },
  Detail: { open() {} },
  esc(s) { return String(s); }, ic() { return ''; }, eventIcon() { return ''; },
  dayKeyAt(iso) { return String(iso).slice(0, 10); }, calTimeAt() { return '19:00'; },
  toast(m) { toasts.push(String(m)); },
  API: {
    async get(pfad) {
      n++;
      snaps.push({ n: n, pfad: pfad, html: els['feed-content'].innerHTML });
      await new Promise(r => realSetTimeout(r, 1));
      if (n <= WARTEN) {
        return { status: 'calculating', events: [], total: 0, message: HINWEIS_SATZ };
      }
      return { status: 'ok', on_demand: true, computed_at: null, total: TERMINE.length, events: TERMINE };
    },
  },
};
// Namen aus dem Ablauf außerhalb der App (nicht von der Übungswelt verdecken lassen)
const AUSSEN = new Set(['n', 'snaps', 'els', 'toasts', 'WARTEN', 'realSetTimeout', 'realSetInterval', 'HINWEIS_SATZ', 'TERMINE', 'dummy', 'stubs', 'scope', 'element', 'AUSSEN']);
const scope = new Proxy(stubs, {
  has(t, p) { return typeof p === 'string' && !AUSSEN.has(p); },
  get(t, p) { if (typeof p !== 'string') return undefined; if (p in t) return t[p]; if (p in globalThis) return globalThis[p]; return dummy; },
});
globalThis.setTimeout = (fn, ms, ...a) => realSetTimeout(fn, 1, ...a);
globalThis.setInterval = (fn, ms, ...a) => realSetInterval(fn, 1, ...a);

with (scope) {
%(app)s
  (async () => {
    await CalendarView.show();
    const ziel = (WARTEN === 0 ? 1 : WARTEN + 1);
    const t0 = Date.now();
    while (Date.now() - t0 < 2500 && n < ziel) { await new Promise(r => realSetTimeout(r, 5)); }
    await new Promise(r => realSetTimeout(r, 150));      // Anzeige zur Ruhe kommen lassen
    console.log(JSON.stringify({ n: n, snaps: snaps, ende: els['feed-content'].innerHTML, toasts: toasts }));
    process.exit(0);
  })().catch(e => { console.error('FEHLER-IM-ABLAUF ' + e); process.exit(3); });
}
"""


def _kalender_lauf(warten):
    """Öffnet den Kalender in der Übungswelt. `warten` = wie oft der Server „wird berechnet“ meldet, bevor er die
    Termine liefert. Gibt zurück: Zahl der Abfragen, Anzeige bei jeder Abfrage, Anzeige am Ende, Meldungen."""
    termine = [
        {"id": "t123-ui-%d" % i, "location_id": "t123-ui", "location_name": "Übungsort", "event_type": "golden_hour_evening",
         "title": t, "shoot_time": "2027-01-1%d" % (i + 5) + "T19:00:00+00:00", "overall_score": 0.6 + 0.1 * i}
        for i, t in enumerate(TITEL)
    ]
    skript = _SKRIPT % {"warten": warten, "satz": json.dumps(HINWEIS_SATZ), "termine": json.dumps(termine),
                        "app": _kalenderteil()}
    res = subprocess.run(["node", "-"], input=skript, universal_newlines=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    assert res.returncode == 0, "Node-Lauf fehlgeschlagen (Rückgabe %d):\n%s" % (res.returncode, res.stderr[-1500:])
    return json.loads(res.stdout.strip().splitlines()[-1])


def _hat_hinweis(html):
    t = (html or "").lower()
    return all(teil in t for teil in HINWEIS_TEILE)


@pytest.fixture(scope="module")
def lauf_mit_warten():
    return _kalender_lauf(ANZAHL_WARTEN)


# ═══════════════════════════════════════════════════════════════════════════════════
# Testfälle (Schicht 1)
# ═══════════════════════════════════════════════════════════════════════════════════
@node_required
def test_t03_ak3_offener_kalender_zeigt_den_hinweis_solange_der_monat_berechnet_wird(lauf_mit_warten):
    """T-03 · AK-3 (Oberfläche) · BUG-123
    Angenommen der Kalender wird geöffnet und der Server meldet mehrmals „wird berechnet“,
    dann steht nach der ersten solchen Meldung in jeder Wartepause der Hinweis
    „wird gerade berechnet, bitte kurz warten“ im Kalender, und nie eine leere Seite
    („Keine Daten“ oder „Keine Events“) statt des Hinweises."""
    lauf = lauf_mit_warten
    waehrend_warten = [s for s in lauf["snaps"] if s["n"] >= 2]
    assert waehrend_warten, "Der Kalender hat nach der ersten „wird berechnet“-Meldung nicht erneut nachgefragt."
    ohne_hinweis = [s["n"] for s in waehrend_warten if not _hat_hinweis(s["html"])]
    assert not ohne_hinweis, (
        "In der Wartepause vor Abfrage Nr. %r steht kein Hinweis „wird gerade berechnet, bitte kurz warten“ im Kalender. "
        "Anzeige dort (Auszug): %r" % (ohne_hinweis, next(s["html"] for s in waehrend_warten if s["n"] == ohne_hinweis[0])[-200:]))
    leer = [s["n"] for s in lauf["snaps"] if "Keine Daten für" in s["html"] or "Keine Events im" in s["html"]]
    assert not leer, "Während des Wartens zeigte der Kalender eine leere Seite (vor Abfrage Nr. %r)." % leer


@node_required
def test_t05_ak4_termine_erscheinen_von_selbst_und_der_hinweis_verschwindet(lauf_mit_warten):
    """T-05 · AK-4 (Oberfläche) · BUG-123
    Angenommen der Server meldet 8-mal „wird berechnet“ und liefert danach 2 Termine,
    dann erscheinen beide Termine im offenen Kalender ohne weiteres Zutun, und der Hinweis ist weg."""
    lauf = lauf_mit_warten
    assert lauf["n"] >= ANZAHL_WARTEN + 1, (
        "Der Kalender hat nach %d Abfragen aufgegeben (der Server hätte erst bei Abfrage %d Termine geliefert)."
        % (lauf["n"], ANZAHL_WARTEN + 1))
    for titel in TITEL:
        assert titel in lauf["ende"], "Termin „%s“ fehlt im Kalender. Anzeige am Ende (Auszug): %r" % (titel, lauf["ende"][-200:])
    assert not _hat_hinweis(lauf["ende"]), "Der Hinweis „wird gerade berechnet“ steht nach Eintreffen der Termine noch da."


@node_required
def test_t04_ak3_fertiger_monat_zeigt_termine_ohne_hinweis():
    """T-04 · AK-3 (Oberfläche, Gegenprobe) · BUG-123
    Angenommen der Server hat den Monat schon fertig,
    dann zeigt der Kalender gleich die Termine, ohne den Hinweis „wird gerade berechnet“, nach genau einer Abfrage."""
    lauf = _kalender_lauf(0)
    assert lauf["n"] == 1, "Erwartet genau 1 Abfrage, gefunden %d." % lauf["n"]
    assert not any(_hat_hinweis(s["html"]) for s in lauf["snaps"]), "Der Hinweis erschien trotz fertigem Monat."
    assert not _hat_hinweis(lauf["ende"])
    for titel in TITEL:
        assert titel in lauf["ende"], "Termin „%s“ fehlt im Kalender." % titel
