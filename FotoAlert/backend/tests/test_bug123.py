"""BUG-123 · Der Kalender legt die App nach einem Neustart nicht lahm — Rechnungsseite (Server).

Testfälle T-03 bis T-09 aus der Spec in BACKLOG.md (Abschnitt „Analyse & Spec (BUG-123)“, Testfall-Liste),
1:1 übernommen; Entscheidungen Stephan 2026-11-22 (Frage 1: Hinweis „wird gerade berechnet, bitte kurz warten“;
Messplan AK-5). Die Oberflächen-Seite (Hinweis im offenen Kalender, Termine erscheinen von selbst) steht in
der zweiten Testdatei zu diesem Ticket, der Messmodus in der dritten. Live-messbar und deshalb NICHT hier: T-01, T-02 (Antwortzeiten nach dem Neustart),
T-10 (Stille beim Neustart), T-11 (echter Release-Lauf), das Protokoll mit Zeitstempel aus AK-5 sowie T-12.

Test-Agent (Orchestrator Phase 3), geschrieben VOR der Umsetzung, 2026-11-22.

Aufbau nach dem Vier-Schichten-Modell (Grundgerüst für Gherkin-Dateien fehlt noch, daher pytest-Datei, Skill
fotoalert-test Teil A3):
  Schicht 1 (Testfälle) = die Testfunktionen unten; ihr Docstring ist der Testfall in Fachsprache.
  Schicht 2 (Fachsprache) = die Sätze „Angenommen … wenn … dann …“ im Docstring, nur Alltagsbegriffe.
  Schicht 3/4 (Treiber, Übungswelt) = der Abschnitt „Übungswelt und Treiber“ weiter unten. Er bedient nur und
  beobachtet nur; er legt nie selbst ein Ergebnis fest.

Isolation: Die drei Übungs-Orte, ihre Termine und die „Rechnung“ sind im Test selbst festgelegt (erfundene Orte,
keine echten Daten). Es wird nie eine echte Zwischenspeicher-Datei (Feed, Kalender, Scout) gelesen oder
geschrieben; der Monatsspeicher im Arbeitsspeicher wird vor und nach jedem Test geleert. Jeder Test benutzt einen
eigenen Monat, damit nichts von einem Test in den nächsten hinüberwirkt.

Quellen der erwarteten Werte: Schwellen und Zahlen aus der Spec (2 Sekunden, genau eine Rechnung je Ort und Monat,
dieselben Termine wie bei einer Rechnung je Ort einzeln = Kontrollrechnung per Handzählung: 3 Orte × 1 Termin).
Der Hinweistext stammt wörtlich aus der Entscheidung von Stephan (Frage 1).
"""
from __future__ import annotations

import asyncio
import time
from collections import Counter

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]

HINWEIS_TEILE = ("wird gerade berechnet", "bitte kurz warten")   # Wortlaut: Entscheidung Stephan 2026-11-22, Frage 1
ORTE_IDS = ["t123-a", "t123-b", "t123-c"]


# ═══════════════════════════════════════════════════════════════════════════════════
# Übungswelt und Treiber (Schicht 3/4) — bedient und beobachtet nur
# ═══════════════════════════════════════════════════════════════════════════════════
class _Ort:
    """Erfundener Übungs-Ort."""

    def __init__(self, ort_id):
        self.id = ort_id
        self.name = "Übungsort " + ort_id
        self.observer_lat = 52.0
        self.observer_lon = 13.0
        self.subject_lat = None
        self.subject_lon = None


def _termin(ort_id, jahr, monat):
    """Der eine Übungs-Termin, den die Rechnung für einen Ort und einen Monat liefert (fest, ohne Astronomie)."""
    zeit = "%04d-%02d-15T19:00:00+00:00" % (jahr, monat)
    return {
        "id": "t123-%s-%04d-%02d" % (ort_id, jahr, monat),
        "location_id": ort_id,
        "location_name": "Übungsort " + ort_id,
        "event_type": "golden_hour_evening",
        "title": "BUG-123 Übungstermin " + ort_id,
        "shoot_time": zeit,
        "overall_score": 0.6,
    }


def _erwartet(ort_ids, jahr, monat):
    """Kontrollrechnung: jeder Ort einzeln gerechnet, nach Nummer sortiert."""
    return sorted((_termin(o, jahr, monat) for o in ort_ids), key=lambda e: e["id"])


def _nach_nummer(termine):
    return sorted(termine, key=lambda e: e["id"])


class _Welt:
    """Übungswelt: drei erfundene Orte, eine steuerbare „Rechnung“ (wartet auf ein Tor, liefert Termine, nichts
    oder einen Fehler) und ein Zähler, wie oft die Rechnung je Ort und Monat gestartet wurde."""

    def __init__(self, monkeypatch):
        import data.locations as dl
        import main
        self.main = main
        self.orte = [_Ort(i) for i in ORTE_IDS]
        self.pausiert = set()
        self.aufrufe = []          # (Ort, Jahr, Monat) je gestarteter Rechnung eines Orts
        self.tor = None            # asyncio.Event im laufenden Ablauf; None = Rechnung wartet nicht
        self.verhalten = "termine"  # "termine" | "leer" | "fehler"
        monkeypatch.setattr(dl, "LOCATIONS", self.orte)
        monkeypatch.setattr(main, "LOCATIONS", self.orte, raising=False)
        monkeypatch.setattr(main.gz, "aktive_orte",
                            lambda orte, z=None: [o for o in orte if o.id not in self.pausiert])
        monkeypatch.setattr(main.gz, "ist_pausiert", lambda ort, z=None: ort.id in self.pausiert)
        monkeypatch.setattr(main, "_pausierte_ort_ids", lambda z=None: set(self.pausiert))
        monkeypatch.setattr(main, "_compute_location_month", self._rechnung)
        monkeypatch.setattr(main, "_gebiets_version", 0)
        monkeypatch.setenv("FOTOALERT_ONDEMAND", "1")
        main._ondemand_month_cache.clear()

    async def _rechnung(self, loc, year, month, min_score):
        self.aufrufe.append((loc.id, year, month))
        if self.tor is not None:
            await self.tor.wait()
        if self.verhalten == "fehler":
            raise RuntimeError("BUG-123-Übungsfehler")
        if self.verhalten == "leer":
            return []
        return [_termin(loc.id, year, month)]

    def rechnungen_je_ort_und_monat(self):
        return dict(Counter(self.aufrufe))

    def monat_gespeichert(self, jahr, monat):
        praefix = "%04d-%02d" % (jahr, monat)
        return [k for k in self.main._ondemand_month_cache if k.startswith(praefix)]

    async def kalender_abrufen(self, jahr, monat):
        """Eine einzelne Anfrage des Kalenders für einen Monat (alle Orte)."""
        return await self.main.get_calendar(location_id=None, month=monat, year=jahr, min_score=0.35)

    async def abrufen_bis_termine(self, jahr, monat, bis_s):
        """Ein Gerät fragt den Monat immer wieder ab, bis die Termine da sind (status ok) oder die Zeit um ist.
        Gibt die letzte Antwort zurück (None, wenn nie eine Antwort kam)."""
        ende = time.monotonic() + bis_s
        letzte = None
        while time.monotonic() < ende:
            try:
                letzte = await asyncio.wait_for(self.kalender_abrufen(jahr, monat),
                                                timeout=max(0.05, ende - time.monotonic()))
            except asyncio.TimeoutError:
                return letzte
            if letzte.get("status") == "ok":
                return letzte
            await asyncio.sleep(0.05)
        return letzte


@pytest.fixture
def welt(monkeypatch):
    w = _Welt(monkeypatch)
    yield w
    w.main._ondemand_month_cache.clear()


def _ablauf(welt, ablauf):
    """Führt einen Ablauf in einer frischen Ereignisschleife aus und räumt danach alles auf, was noch läuft."""
    async def huelle():
        try:
            return await ablauf()
        finally:
            if welt.tor is not None:
                welt.tor.set()
            uebrig = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if uebrig:
                _, offen = await asyncio.wait(uebrig, timeout=3)
                for t in offen:
                    t.cancel()
                await asyncio.gather(*offen, return_exceptions=True)
    return asyncio.run(huelle())


def _hinweis_enthalten(text):
    t = (text or "").lower()
    return all(teil in t for teil in HINWEIS_TEILE)


# ═══════════════════════════════════════════════════════════════════════════════════
# Testfälle (Schicht 1)
# ═══════════════════════════════════════════════════════════════════════════════════
def test_t03_ak3_nicht_berechneter_monat_bekommt_sofort_den_hinweis(welt):
    """T-03 · AK-3 · BUG-123
    Angenommen ein Monat ist noch nicht berechnet und die Rechnung dauert lange,
    wenn der Kalender diesen Monat abruft,
    dann kommt innerhalb von 2 Sekunden die Antwort „wird berechnet“ mit dem Hinweis
    „wird gerade berechnet, bitte kurz warten“ — keine leere Terminliste ohne Hinweis und kein Warten ohne Antwort."""
    jahr, monat = 2027, 1

    async def ablauf():
        welt.tor = asyncio.Event()      # die Rechnung wartet, bis der Test sie freigibt
        t0 = time.monotonic()
        try:
            antwort = await asyncio.wait_for(welt.kalender_abrufen(jahr, monat), timeout=2.0)
        except asyncio.TimeoutError:
            antwort = None
        return antwort, time.monotonic() - t0

    antwort, dauer = _ablauf(welt, ablauf)
    assert antwort is not None, (
        "Der Kalender hat nicht innerhalb von 2 Sekunden geantwortet: der Abruf hing, bis die Rechnung fertig war "
        "(kein Hinweis „wird berechnet“, die Seite wartet stumm)."
    )
    assert dauer < 2.0, "Antwort kam nach %.2f Sekunden, erlaubt sind weniger als 2." % dauer
    assert antwort.get("status") == "calculating", (
        "Erwartet die Antwort „wird berechnet“ (status calculating), gefunden: %r" % antwort.get("status"))
    assert antwort.get("events") == [] and antwort.get("total", 0) == 0, (
        "Beim Warten darf keine Terminliste geliefert werden (weder leer-ohne-Hinweis noch Teilergebnis).")
    assert _hinweis_enthalten(antwort.get("message")), (
        "Der Hinweistext fehlt: erwartet „wird gerade berechnet, bitte kurz warten“, gefunden: %r"
        % antwort.get("message"))


def test_t04_ak3_fertiger_monat_liefert_termine_ohne_hinweis(welt):
    """T-04 · AK-3 (Gegenprobe) · BUG-123
    Angenommen ein Monat ist fertig berechnet,
    wenn der Kalender diesen Monat abruft,
    dann kommen die Termine und kein Hinweis „wird berechnet“.
    Gegenprobe im selben Test: Der fertige Monat wird dabei nicht noch einmal gerechnet — das sichert ab, dass der
    Hinweis nur im Wartefall kommt und nicht jede Antwort verzögert."""
    jahr, monat = 2027, 2

    async def ablauf():
        erste = await welt.abrufen_bis_termine(jahr, monat, bis_s=5)       # Monat wird fertig berechnet
        rechnungen_vorher = len(welt.aufrufe)
        t0 = time.monotonic()
        zweite = await asyncio.wait_for(welt.kalender_abrufen(jahr, monat), timeout=2.0)
        return erste, zweite, rechnungen_vorher, time.monotonic() - t0

    erste, zweite, vorher, dauer = _ablauf(welt, ablauf)
    assert erste is not None and erste.get("status") == "ok", "Der Monat wurde nicht fertig: %r" % (erste,)
    assert zweite.get("status") == "ok", "Fertiger Monat muss status ok liefern, gefunden: %r" % zweite.get("status")
    assert _nach_nummer(zweite["events"]) == _erwartet(ORTE_IDS, jahr, monat)
    assert not _hinweis_enthalten(zweite.get("message")), "Bei einem fertigen Monat darf kein Hinweis kommen."
    assert len(welt.aufrufe) == vorher, "Der fertige Monat darf nicht erneut gerechnet werden."
    assert dauer < 2.0


def test_t05_ak4_nach_dem_warten_kommen_dieselben_termine_wie_bei_der_einzelrechnung(welt):
    """T-05 · AK-4 (Termine) · BUG-123
    Angenommen die Rechnung wird fertig, während ein Gerät den Monat immer wieder abfragt,
    dann bekommt das Gerät am Ende genau dieselben Termine wie bei einer Kontrollrechnung jedes Ortes einzeln —
    nichts fehlt, nichts ist doppelt, nichts ist dazugekommen.
    Quelle: Kontrollrechnung per Handzählung (3 Orte mit je 1 Termin). Der Vergleich eines echten Monats mit der
    Rechnung vor dem Umbau ist Aufgabe der Umfangsprüfung, nicht dieses Tests; die Anzeige im offenen Kalender prüft die
    Oberflächen-Testdatei."""
    jahr, monat = 2027, 3

    async def ablauf():
        welt.tor = asyncio.Event()
        asyncio.get_running_loop().call_later(0.3, welt.tor.set)      # Rechnung wird nach 0,3 s fertig
        return await welt.abrufen_bis_termine(jahr, monat, bis_s=8)

    antwort = _ablauf(welt, ablauf)
    assert antwort is not None and antwort.get("status") == "ok", "Es kamen nie Termine: %r" % (antwort,)
    assert antwort["total"] == len(ORTE_IDS)
    assert _nach_nummer(antwort["events"]) == _erwartet(ORTE_IDS, jahr, monat)


def test_t06_ak5_drei_gleichzeitige_abrufe_rechnen_den_monat_nur_einmal(welt):
    """T-06 · AK-5 · BUG-123
    Angenommen drei Geräte rufen gleichzeitig denselben, noch nicht berechneten Monat ab,
    dann wird der Monat nur einmal gerechnet (jeder Ort genau einmal), und alle drei bekommen dasselbe Ergebnis."""
    jahr, monat = 2027, 4

    async def ablauf():
        welt.tor = asyncio.Event()
        geraete = [asyncio.ensure_future(welt.abrufen_bis_termine(jahr, monat, bis_s=8)) for _ in range(3)]
        await asyncio.sleep(0.5)          # alle drei sind angekommen, die Rechnung steht noch
        welt.tor.set()
        return await asyncio.gather(*geraete)

    antworten = _ablauf(welt, ablauf)
    je_ort = welt.rechnungen_je_ort_und_monat()
    erwartet = {(o, jahr, monat): 1 for o in ORTE_IDS}
    assert je_ort == erwartet, (
        "Der Monat wurde mehrfach gerechnet. Rechnungen je Ort und Monat: %r (erwartet: jeder Ort genau einmal)"
        % je_ort)
    for a in antworten:
        assert a is not None and a.get("status") == "ok", "Ein Gerät bekam keine Termine: %r" % (a,)
    ergebnisse = [_nach_nummer(a["events"]) for a in antworten]
    assert ergebnisse[0] == ergebnisse[1] == ergebnisse[2] == _erwartet(ORTE_IDS, jahr, monat)


def test_t07_ak5_zwei_verschiedene_monate_rechnen_beide(welt):
    """T-07 · AK-5 (Gegenprobe) · BUG-123
    Angenommen zwei Geräte rufen gleichzeitig zwei verschiedene Monate ab,
    dann werden beide Monate gerechnet (keine falsche Zusammenlegung), und jedes Gerät bekommt die Termine seines Monats."""
    monat_a, monat_b = (2027, 5), (2027, 6)

    async def ablauf():
        welt.tor = asyncio.Event()
        g1 = asyncio.ensure_future(welt.abrufen_bis_termine(*monat_a, bis_s=8))
        g2 = asyncio.ensure_future(welt.abrufen_bis_termine(*monat_b, bis_s=8))
        await asyncio.sleep(0.5)
        welt.tor.set()
        return await asyncio.gather(g1, g2)

    a1, a2 = _ablauf(welt, ablauf)
    erwartet = {(o, j, m): 1 for (j, m) in (monat_a, monat_b) for o in ORTE_IDS}
    assert welt.rechnungen_je_ort_und_monat() == erwartet, (
        "Erwartet: jeder Ort für jeden der beiden Monate genau einmal, gefunden: %r" % welt.rechnungen_je_ort_und_monat())
    assert a1 is not None and a1.get("status") == "ok" and a2 is not None and a2.get("status") == "ok"
    assert _nach_nummer(a1["events"]) == _erwartet(ORTE_IDS, *monat_a)
    assert _nach_nummer(a2["events"]) == _erwartet(ORTE_IDS, *monat_b)


def test_t08a_ak6_monat_mit_lauter_fehlern_bleibt_leer_und_wird_nicht_gespeichert(welt):
    """T-08 (Teil a) · AK-6 · BUG-123
    Angenommen bei der Rechnung schlagen alle Orte fehl, während drei Geräte denselben Monat abfragen,
    dann wird der leere Monat nicht gespeichert, und sobald die Ursache weg ist, bekommt das nächste Abfragen
    die richtigen Termine (kein Gerät behält den Fehler bis zum nächsten Neustart)."""
    jahr, monat = 2027, 7

    async def ablauf():
        welt.verhalten = "fehler"
        welt.tor = asyncio.Event()
        geraete = [asyncio.ensure_future(welt.abrufen_bis_termine(jahr, monat, bis_s=3)) for _ in range(3)]
        await asyncio.sleep(0.5)
        welt.tor.set()
        await asyncio.gather(*geraete)
        gespeichert_nach_fehler = welt.monat_gespeichert(jahr, monat)
        welt.verhalten = "termine"                # Ursache ist weg
        welt.tor = None
        spaeter = await welt.abrufen_bis_termine(jahr, monat, bis_s=5)
        return gespeichert_nach_fehler, spaeter

    gespeichert, spaeter = _ablauf(welt, ablauf)
    assert gespeichert == [], "Ein Monat, der wegen Fehlern leer ausfiel, wurde gespeichert: %r" % gespeichert
    assert spaeter is not None and spaeter.get("status") == "ok", "Nach dem Fehler kamen nie wieder Termine."
    assert _nach_nummer(spaeter["events"]) == _erwartet(ORTE_IDS, jahr, monat)


def test_t08b_ak6_echt_leerer_monat_wird_gespeichert_und_nicht_neu_gerechnet(welt):
    """T-08 (Teil b) · AK-6 · BUG-123
    Angenommen ein Monat ist echt leer (kein Fehler, nur keine Termine),
    dann wird er gespeichert und beim nächsten Abruf nicht noch einmal gerechnet; die Antwort ist „fertig, 0 Termine“,
    nicht „wird berechnet“."""
    jahr, monat = 2027, 8

    async def ablauf():
        welt.verhalten = "leer"
        erste = await welt.abrufen_bis_termine(jahr, monat, bis_s=5)
        gespeichert = welt.monat_gespeichert(jahr, monat)
        rechnungen = len(welt.aufrufe)
        zweite = await asyncio.wait_for(welt.kalender_abrufen(jahr, monat), timeout=2.0)
        return erste, gespeichert, rechnungen, zweite

    erste, gespeichert, rechnungen, zweite = _ablauf(welt, ablauf)
    assert erste is not None and erste.get("status") == "ok" and erste.get("total") == 0
    assert len(gespeichert) == 1, "Der echt leere Monat muss gespeichert werden, gefunden: %r" % gespeichert
    assert rechnungen == len(ORTE_IDS), "Erste Rechnung: jeder Ort einmal, gefunden %d" % rechnungen
    assert zweite.get("status") == "ok" and zweite.get("total") == 0
    assert len(welt.aufrufe) == rechnungen, "Der echt leere Monat wurde beim zweiten Abruf erneut gerechnet."


def test_t09_ak7_umschalten_waehrend_der_rechnung_speichert_nichts_und_liefert_keine_pausierten(welt):
    """T-09 · AK-7 · BUG-123
    Angenommen während der Rechnung wird ein Gebiet ausgeschaltet (Ort b pausiert) und ein zweites Gerät fragt danach
    denselben Monat ab,
    dann enthält keine Antwort Termine des pausierten Ortes, und im Speicher liegt nie ein Ergebnis mit Terminen
    des pausierten Ortes.
    Hinweis zur Prüfung: „nicht gespeichert“ wird indirekt geprüft, nämlich dadurch, dass im Speicher kein Termin des
    pausierten Ortes liegt; ob der Speicher ganz leer bleibt, lässt der Test bewusst offen."""
    jahr, monat = 2027, 9
    pausierter = "t123-b"

    async def ablauf():
        welt.tor = asyncio.Event()
        g1 = asyncio.ensure_future(welt.abrufen_bis_termine(jahr, monat, bis_s=8))
        await asyncio.sleep(0.3)
        # Umschalten, wie es der Server bei einer Gebietsänderung tut: Stand hochzählen, Monatsspeicher leeren
        welt.pausiert.add(pausierter)
        welt.main._gebiets_version += 1
        welt.main._ondemand_month_cache.clear()
        g2 = asyncio.ensure_future(welt.abrufen_bis_termine(jahr, monat, bis_s=8))
        await asyncio.sleep(0.3)
        welt.tor.set()
        return await asyncio.gather(g1, g2)

    a1, a2 = _ablauf(welt, ablauf)
    for a in (a1, a2):
        assert a is not None and a.get("status") == "ok", "Ein Gerät bekam keine Termine: %r" % (a,)
        orte = {e["location_id"] for e in a["events"]}
        assert pausierter not in orte, "Termine des pausierten Ortes wurden ausgeliefert: %r" % sorted(orte)
        assert orte, "Die Termine der aktiven Orte fehlen."
    for schluessel, termine in welt.main._ondemand_month_cache.items():
        assert pausierter not in {e["location_id"] for e in termine}, (
            "Im Monatsspeicher (%s) liegen Termine des pausierten Ortes." % schluessel)
