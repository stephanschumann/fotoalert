"""US-141 (Phase A, 2026-10-14) — Betrieb: Statusseite, Koordinaten pausierter Orte, Wiedereinschalten, schnelles Umschalten.

Ergänzt test_us141_schalter.py, test_us141_nachladen.py, test_us141_neue_orte.py und test_us141_filter_ergebnisse.py
um Kriterien, die dort noch ohne Test waren.

Geprüft wird (Akzeptanzkriterien AK-15, AK-46, AK-47, AK-55, AK-57, AK-68):
  - Die Statusseite (/health) weist aktive und gesamte Orte getrennt aus; die bisherige Zahl bleibt unverändert (AK-55, AK-57).
  - Ändert der Host die Koordinaten eines pausierten Orts, bekommt er keine Feed-Chancen und keinen Kalender;
    selbst wenn ein Rechenlauf sie versehentlich mitrechnet, werden sie nie ausgeliefert (AK-46, AK-79).
  - Nach dem Wiedereinschalten erscheinen die Chancen wieder (AK-15, Polarität zu AK-01).
  - Schnelles Umschalten aus/an/aus/an: es gilt der zuletzt gedrückte Zustand, nie zwei Rechenläufe gleichzeitig (AK-68).

ANNAHMEN (siehe backend/tests/README.md):
  B1  /health liefert zusätzlich zur bisherigen Zahl ‚locations_count‘ (alle Orte) ein weiteres Zahlenfeld, dessen
      Name ‚aktiv‘ oder ‚active‘ enthält und das die Zahl der aktiven Orte trägt. Der genaue Name ist frei.
  B2  Läuft für einen pausierten Ort ein Rechenprozess, trägt er ein Merkmal, das ihn von einem Feed- oder
      Kalender-Lauf unterscheidet (Option A, Baustein 3: eigener Ortsdaten-Modus). Fehlt jedes Merkmal, ist es ein
      Voll-Lauf und damit falsch (AK-46).
Python-3.9-kompatibel. Offline.
"""
from __future__ import annotations

import asyncio
import json
import threading

import pytest

from us141_adapter import (  # noqa: F401  (welt/welt_z sind Fixtures)
    FELD_LAND, FELD_REGION, ORTE, ProzessSpion, als_host, aktive_ids, feed_ids, host_schaltet_land,
    host_schaltet_region, ort_id, pausierte_ids, warte_bis, welt, welt_z,
)

pytestmark = [pytest.mark.api, pytest.mark.regression]

BB = {ort_id("potsdam"), ort_id("cottbus")}
ALLE = {ort_id(k) for k in ORTE}
WARTEZEIT = 8.0


# ── Statusseite ───────────────────────────────────────────────────────────────

def _zahlenfelder(daten, pfad=""):
    """Alle Zahlenfelder der Antwort, auch verschachtelt: {Pfad: Wert}."""
    aus = {}
    if isinstance(daten, dict):
        for k, v in daten.items():
            aus.update(_zahlenfelder(v, pfad + "/" + str(k)))
    elif isinstance(daten, (int, float)) and not isinstance(daten, bool):
        aus[pfad] = daten
    return aus


def test_statusseite_weist_aktive_und_gesamte_orte_getrennt_aus(client, welt_z):
    """AK-55 (Annahme B1) und AK-57: Nach dem Ausschalten von Brandenburg zeigt /health weiter die Gesamtzahl aller
    Orte im bisherigen Feld (locations_count) und zusätzlich die Zahl der aktiven Orte in einem eigenen Feld."""
    gesamt = len(ALLE)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    r = client.get("/health")
    assert r.status_code == 200, r.text
    daten = r.json()
    zahlen = _zahlenfelder(daten)
    alte = [p for p in zahlen if p.endswith("/locations_count")]
    assert alte, "Das bisherige Feld locations_count fehlt in /health"
    assert zahlen[alte[0]] == gesamt, "locations_count hat sich geändert: %s statt %s (AK-57)" % (zahlen[alte[0]], gesamt)
    aktiv = [p for p, v in zahlen.items() if ("aktiv" in p.lower() or "active" in p.lower()) and v == gesamt - len(BB)]
    assert aktiv, "Kein Feld mit der Zahl der aktiven Orte (%d) in /health: %s" % (gesamt - len(BB), sorted(zahlen))


# ── Koordinaten eines pausierten Orts ─────────────────────────────────────────

@pytest.fixture
def mit_spion(client, welt_z, monkeypatch):
    """Rechenprozesse werden durch den Spion ersetzt; Wetter, Entdecken, Höhenabfrage und Geocoding sind stillgelegt.
    `scharf()` schaltet erst NACH dem Vorbereiten des Ausgangszustands die Hintergrundläufe frei."""
    import main

    spion = ProzessSpion()

    async def _nichts(*a, **k):
        return None

    async def _wahr(*a, **k):
        return True

    async def _kein_ort(lat, lon):
        return ""

    async def _keine_hoehe(*a, **k):
        return (0.0, False)

    monkeypatch.setattr(main, "_trigger_discover_debounced", lambda *a, **k: None)
    monkeypatch.setattr(main, "_refresh_discover", _nichts)
    monkeypatch.setattr(main, "_weather_overlay", _nichts)
    monkeypatch.setattr(main, "_weather_overlay_single", _wahr)
    monkeypatch.setattr(main, "_apply_calendar_delta", _nichts)
    monkeypatch.setattr(main, "_reverse_geocode", _kein_ort)
    monkeypatch.setattr(main._elevation_provider, "elevation_difference", _keine_hoehe)
    monkeypatch.setattr(main, "_load_caches", lambda *a, **k: main._load_feed_cache())

    def scharf():
        monkeypatch.setattr(main, "_NO_BACKGROUND", False)
        monkeypatch.setattr(asyncio, "create_subprocess_exec", spion.fake_exec)

    class _Z:
        pass
    z = _Z()
    z.welt, z.spion, z.scharf = welt_z, spion, scharf
    yield z
    if spion.sperre is not None:
        spion.sperre.set()


def _schreibe_feed_mit(welt, keys):
    def _ende(args):
        welt.feed.write_text(json.dumps({"computed_at": "2026-10-14T01:00:00+00:00",
                                         "opportunities": welt.termine_fuer(keys)}), encoding="utf-8")
    return _ende


def test_koordinaten_eines_pausierten_orts_rechnen_keine_chancen_und_keinen_kalender(client, mit_spion):
    """AK-46 (Annahme B2) und AK-79: Verschiebt der Host Potsdam (Brandenburg ist aus), sind die neuen Koordinaten
    sofort gespeichert; ein dafür gestarteter Rechenprozess ist weder ein Feed- noch ein Kalender- noch ein
    Voll-Lauf; und selbst wenn ein Lauf die Chancen des Orts mitrechnet, liefert der Server sie nicht aus."""
    w, s = mit_spion.welt, mit_spion.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.beim_ende = _schreibe_feed_mit(w, ("potsdam", "berlin1"))
    mit_spion.scharf()
    als_host(client)
    r = client.patch("/locations/" + ort_id("potsdam"), json={"observer_lat": 52.3950, "observer_lon": 13.0700})
    assert r.status_code == 200, r.text
    orte = {o["id"]: o for o in client.get("/locations").json()}
    assert orte[ort_id("potsdam")]["observer_lat"] == pytest.approx(52.3950), "neue Koordinaten nicht gespeichert"
    warte_bis(lambda: s.aktiv == 0 and (s.beendet >= len(s.starts)), WARTEZEIT)
    for args in s.starts:
        text = " ".join(str(a) for a in args)
        if ort_id("potsdam") not in text:
            continue
        assert "--feed-only" not in args and "--calendar-only" not in args, \
            "für den pausierten Ort lief ein Feed- oder Kalender-Lauf: %s" % text
        modus = [a for a in args if str(a).startswith("--") and a not in ("--location-id", "--location-ids")]
        assert modus, "für den pausierten Ort lief ein Voll-Lauf (kein Ortsdaten-Modus): %s" % text
    assert ort_id("potsdam") not in feed_ids(client), "Chancen des pausierten Orts werden ausgeliefert"
    assert ort_id("potsdam") in pausierte_ids(client)


# ── Wiedereinschalten und schnelles Umschalten ────────────────────────────────

def test_nach_dem_wiedereinschalten_erscheinen_die_chancen_wieder(client, mit_spion):
    """AK-15: Brandenburg aus -> keine Chancen im Feed; Brandenburg an -> das Nachladen rechnet die beiden Orte, und
    ihre Chancen erscheinen wieder (Polarität zu AK-01)."""
    w, s = mit_spion.welt, mit_spion.spion
    w.setze_feed(w.termine_fuer(("potsdam", "cottbus", "berlin1", "muenchen")))
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert not (feed_ids(client) & BB), "Gegenprobe: pausierte Chancen sind noch im Feed"
    s.beim_ende = _schreibe_feed_mit(w, ("potsdam", "cottbus", "berlin1", "muenchen"))
    mit_spion.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: BB <= feed_ids(client), WARTEZEIT), \
        "nach dem Einschalten kommen die Chancen von Brandenburg nicht wieder: %s" % feed_ids(client)
    assert not (pausierte_ids(client) & BB)


def test_schnelles_umschalten_aus_an_aus_an_gilt_der_letzte_zustand(client, mit_spion):
    """AK-68: Aus, an, aus, an, kurz nacheinander (der erste Lauf ist noch nicht fertig): Am Ende ist Brandenburg an,
    seine Chancen sind da, es lief nie mehr als ein Rechenprozess gleichzeitig, und nichts bleibt als
    ‚wird aktualisiert‘ hängen."""
    w, s = mit_spion.welt, mit_spion.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    s.beim_ende = _schreibe_feed_mit(w, ("potsdam", "cottbus", "berlin1"))
    mit_spion.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT), "kein Rechenprozess nach dem Einschalten"
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    s.sperre.set()
    assert warte_bis(lambda: BB <= feed_ids(client), WARTEZEIT), "Endzustand ‚an‘: Chancen fehlen: %s" % feed_ids(client)
    assert warte_bis(lambda: not (set(client.get("/recompute-status").json()["pending"]) & BB), WARTEZEIT), \
        "‚wird aktualisiert‘ bleibt hängen"
    assert s.max_aktiv == 1, "zwei Rechenläufe liefen gleichzeitig"
    assert not (pausierte_ids(client) & BB)


def test_schnelles_umschalten_aus_an_aus_gilt_der_letzte_zustand(client, mit_spion):
    """AK-68, Gegenstück: Aus, an, aus: Am Ende ist Brandenburg aus; das Ergebnis des Laufs aus der Zwischenzeit
    wird nicht ausgeliefert."""
    w, s = mit_spion.welt, mit_spion.spion
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre = threading.Event()
    s.beim_ende = _schreibe_feed_mit(w, ("potsdam", "cottbus", "berlin1"))
    mit_spion.scharf()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert warte_bis(lambda: s.aktiv == 1, WARTEZEIT)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    s.sperre.set()
    warte_bis(lambda: s.aktiv == 0, WARTEZEIT)
    assert not (feed_ids(client) & BB), "Chancen des zuletzt ausgeschalteten Gebiets werden ausgeliefert"
    assert BB <= pausierte_ids(client)
