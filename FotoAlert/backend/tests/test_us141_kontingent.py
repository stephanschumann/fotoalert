"""US-141 (Phase A, 2026-10-14) — Wetterdienst-Kontingent: Zählzeile je Lauf, Scout fragt für pausierte Orte
kein Wetter an, Protokolle nennen keine pausierten Orte.

Geprüft wird (Akzeptanzkriterien AK-04, AK-53, AK-104, AK-105, AK-109; Ziel ‚Wetterdienst-Kontingent sparen‘,
Wirkungs-Tabelle Zeile 7, Entscheidung 4 ‚Wetter muss aus bleiben‘):
  - Jeder Wetterlauf schreibt am Ende GENAU EINE Zeile mit Anfragen, abgelehnten Anfragen (Fehler 429),
    Anteil in Prozent und Dauer (AK-104). Wiederholungen nach einem 429 zählen als eigene Anfragen,
    weil jede beim Dienst Kontingent verbraucht.
  - Entdecken (Scout) wird getrennt ausgewiesen (AK-105).
  - Orte eines pausierten Landes/einer pausierten Region lösen auch beim Scout keine Wetteranfrage aus (AK-109).
  - In keinem Protokoll der Berechnungsdienste taucht ein pausierter Ort auf (AK-53).

NICHT automatisch prüfbar (bleibt Live-Messung durch Stephan, AK-106/AK-107): der Ausgangswert über einen vollen
Tag, der Rückgang nach dem Pausieren eines Landes und die Obergrenze für abgelehnte Anfragen beim Einschalten
von Deutschland. Grenzwert offen, kommt aus der Messung — ein erfundener Grenzwert stünde hier falsch.

ANNAHMEN dieser Datei (Wortlaut der Zeile ist im Ticket nicht festgelegt, siehe backend/tests/README.md):
  K1  Die Zählzeile ist EIN Protokolleintrag (Stufe INFO oder höher), der das Wort ‚Anfrage‘ und ein Prozentzeichen
      enthält; er nennt die Zahl der Anfragen, die Zahl der abgelehnten Anfragen, den Anteil in Prozent und die
      Dauer in Sekunden. Reihenfolge und weitere Wörter sind frei.
  K2  Die Zeile des Ortswetter-Laufs enthält das Wort ‚Ortswetter‘, die des Scout-Laufs das Wort ‚Entdecken‘ oder ‚Scout‘.
  K3  Der Scout-Lauf (moon_pipeline.run / sun_pipeline.run) schreibt seine Zählzeile selbst; ein anderer Ort ist
      möglich, solange sie im Protokoll steht, nachdem beide Pipelines gelaufen sind.
Python-3.9-kompatibel. Offline: alle Wetterabrufe sind Attrappen, kein Netz.
"""
from __future__ import annotations

import asyncio
import copy
import logging
import math
import re

import httpx
import pytest

from us141_adapter import (  # noqa: F401  (welt/welt_z sind Fixtures)
    ORTE, host_schaltet_land, host_schaltet_region, ort_id, welt, welt_z,
)

pytestmark = [pytest.mark.api, pytest.mark.regression]

BR = ("potsdam", "cottbus")
REST = ("berlin1", "muenchen", "london1", "sterzing")


class _Zaehler:
    """Attrappe für die Wetter-Abrufe. Jeder Abruf wird gezählt; Abrufe für Koordinaten in `abgelehnt_bei` werden
    mit 429 beantwortet, alle anderen schlagen mit einem Verbindungsfehler fehl (damit keine echten Wetterdaten
    verarbeitet werden müssen — gezählt wird die Anfrage trotzdem)."""

    def __init__(self, abgelehnt_bei=()):
        self.abgelehnt_bei = [tuple(x) for x in abgelehnt_bei]
        self.koordinaten = []        # jede Anfrage: (Breite, Länge)
        self.anfragen = 0
        self.n429 = 0

    def _nah(self, lat, lon):
        return any(abs(lat - a) < 0.05 and abs(lon - b) < 0.05 for a, b in self.abgelehnt_bei)

    async def abruf(self, lat, lon, *a, **k):
        self.anfragen += 1
        self.koordinaten.append((lat, lon))
        if self._nah(lat, lon):
            self.n429 += 1
            req = httpx.Request("GET", "https://example.invalid/forecast")
            raise httpx.HTTPStatusError("429", request=req, response=httpx.Response(429, request=req))
        raise httpx.ConnectError("Attrappe: kein Netz")


def _schnell(monkeypatch):
    import main
    monkeypatch.setattr(main, "WEATHER_API_REQUEST_PACING_SECONDS", 0.0)
    monkeypatch.setattr(main, "WEATHER_API_RETRY_BACKOFF_BASE_SECONDS", 0.0)


def _wetterlauf(welt_z, monkeypatch, zaehler):
    import main
    _schnell(monkeypatch)
    monkeypatch.setattr(main, "fetch_weather_forecast", zaehler.abruf)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", zaehler.abruf)
    monkeypatch.setattr(main, "_job_status", copy.deepcopy(main._job_status))
    welt_z.setze_feed(welt_z.termine_fuer(BR + REST, tage=1.0))
    asyncio.run(main._weather_overlay("test"))


def _zaehlzeilen(caplog):
    return [r for r in caplog.records
            if r.levelno >= logging.INFO and "anfrage" in r.getMessage().lower() and "%" in r.getMessage()]


def _zahlen(text):
    return [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", text)]


# ── AK-104: eine Zählzeile je Wetterlauf ──────────────────────────────────────

def test_wetterlauf_schreibt_genau_eine_zaehlzeile_mit_allen_vier_angaben(client, welt, monkeypatch, caplog):
    """AK-104: Am Ende jedes Wetterlaufs steht eine Zeile im Protokoll: Anzahl der Anfragen, Anzahl der abgelehnten
    Anfragen (429), Anteil in Prozent, Dauer. Hier: Potsdam wird jedes Mal abgelehnt (mit zwei Wiederholungen), alle
    anderen Anfragen scheitern anders — die Zahlen der Zeile müssen zu dem passen, was die Attrappe wirklich sah."""
    caplog.set_level(logging.INFO)
    potsdam = welt.koord("potsdam")
    z = _Zaehler(abgelehnt_bei=[potsdam])
    _wetterlauf(welt, monkeypatch, z)
    assert z.anfragen > 0 and z.n429 > 0, "Attrappe hat nichts gesehen — Testaufbau kaputt"
    zeilen = _zaehlzeilen(caplog)
    assert len(zeilen) == 1, "erwartet genau eine Zählzeile je Wetterlauf, gefunden: %d" % len(zeilen)
    text = zeilen[0].getMessage()
    zahlen = _zahlen(text)
    assert float(z.anfragen) in zahlen, "Zahl der Anfragen (%d) fehlt in: %s" % (z.anfragen, text)
    assert float(z.n429) in zahlen, "Zahl der abgelehnten Anfragen (%d) fehlt in: %s" % (z.n429, text)
    prozent = re.findall(r"(\d+(?:[.,]\d+)?)\s*%", text)
    assert prozent, "kein Anteil in Prozent in: %s" % text
    erwartet = 100.0 * z.n429 / z.anfragen
    assert abs(float(prozent[0].replace(",", ".")) - erwartet) <= 0.6, "Anteil %s statt %.1f %% in: %s" % (prozent[0], erwartet, text)
    assert re.search(r"\d+(?:[.,]\d+)?\s*(s\b|sek)", text.lower()), "keine Dauer in Sekunden in: %s" % text


def test_zaehlzeile_wird_auch_bei_einem_lauf_ohne_abgelehnte_anfragen_geschrieben(client, welt, monkeypatch, caplog):
    """AK-104, Randfall null abgelehnte: Die Zeile steht trotzdem, mit 0 abgelehnten und 0 Prozent
    (kein Teilen durch Null, keine fehlende Zeile)."""
    caplog.set_level(logging.INFO)
    z = _Zaehler(abgelehnt_bei=[])
    _wetterlauf(welt, monkeypatch, z)
    zeilen = _zaehlzeilen(caplog)
    assert len(zeilen) == 1, "erwartet genau eine Zählzeile, gefunden: %d" % len(zeilen)
    text = zeilen[0].getMessage()
    assert re.search(r"\b0(?:[.,]0+)?\s*%", text), "Anteil 0 %% fehlt in: %s" % text
    assert float(z.anfragen) in _zahlen(text)


def test_wiederholungen_nach_429_zaehlen_als_eigene_anfragen(client, welt, monkeypatch, caplog):
    """AK-104 / Annahme: Jede Wiederholung verbraucht beim Dienst Kontingent. Bei immer abgelehnten Anfragen für
    Potsdam (1 Versuch + 2 Wiederholungen je Abruf) ist die Zahl der abgelehnten Anfragen ein Vielfaches von drei
    und genau so hoch, wie die Attrappe 429 gesendet hat."""
    import main
    caplog.set_level(logging.INFO)
    z = _Zaehler(abgelehnt_bei=[welt.koord("potsdam")])
    _wetterlauf(welt, monkeypatch, z)
    assert z.n429 % (main.WEATHER_API_MAX_RETRIES_ON_429 + 1) == 0
    zeilen = _zaehlzeilen(caplog)
    assert len(zeilen) == 1, "erwartet genau eine Zählzeile, gefunden: %d" % len(zeilen)
    assert float(z.n429) in _zahlen(zeilen[0].getMessage())


# ── AK-105: Ortswetter und Entdecken getrennt ─────────────────────────────────

def test_zaehlzeile_des_wetterlaufs_ist_als_ortswetter_gekennzeichnet(client, welt, monkeypatch, caplog):
    """AK-105 (Annahme K2): Der Wetterlauf für Orte weist sich als ‚Ortswetter‘ aus, damit er nicht mit dem Scout
    verwechselt wird, der aus demselben Kontingent schöpft."""
    caplog.set_level(logging.INFO)
    _wetterlauf(welt, monkeypatch, _Zaehler())
    zeilen = _zaehlzeilen(caplog)
    assert len(zeilen) == 1, "erwartet genau eine Zählzeile, gefunden: %d" % len(zeilen)
    assert "ortswetter" in zeilen[0].getMessage().lower()


@pytest.fixture
def scout_gesichert():
    """Der Scout baut seine Motivliste aus der Ortsliste; nach dem Test wird sie wie vorher hergestellt."""
    from discover import subjects as S
    vorher = (list(S.SUBJECTS), list(S.EXCLUSION_ZONES) if not isinstance(S.EXCLUSION_ZONES, dict) else dict(S.EXCLUSION_ZONES),
              dict(S.SUBJECT_BY_ID))
    yield S
    S.SUBJECTS[:] = vorher[0]
    if isinstance(S.EXCLUSION_ZONES, dict):
        S.EXCLUSION_ZONES.clear()
        S.EXCLUSION_ZONES.update(vorher[1])
    else:
        S.EXCLUSION_ZONES[:] = vorher[1]
    S.SUBJECT_BY_ID.clear()
    S.SUBJECT_BY_ID.update(vorher[2])


def _scout_lauf(monkeypatch, zaehler):
    from discover import moon_pipeline, pipeline_base, sun_pipeline
    pipeline_base.clear_weather_cache()
    monkeypatch.setattr(pipeline_base, "fetch_weather_forecast", zaehler.abruf)
    asyncio.run(moon_pipeline.run(1))
    asyncio.run(sun_pipeline.run(1))
    pipeline_base.clear_weather_cache()


def test_scout_weist_seine_wetteranfragen_getrennt_aus(client, welt, scout_gesichert, monkeypatch, caplog):
    """AK-105 (Annahmen K2, K3): Nach einem Scout-Lauf steht im Protokoll eine eigene Zählzeile ‚Entdecken/Scout‘ mit
    der Zahl seiner Anfragen — getrennt von der Zeile des Ortswetters."""
    caplog.set_level(logging.INFO)
    scout_gesichert.refresh_subjects()
    z = _Zaehler(abgelehnt_bei=[welt.koord("potsdam")])
    _scout_lauf(monkeypatch, z)
    assert z.anfragen > 0, "der Scout hat gar keine Wetteranfrage gestellt — Testaufbau kaputt"
    zeilen = [r.getMessage() for r in _zaehlzeilen(caplog)
              if "entdecken" in r.getMessage().lower() or "scout" in r.getMessage().lower()]
    assert len(zeilen) >= 1, "keine Zählzeile für Entdecken (Scout) im Protokoll"
    assert float(z.anfragen) in _zahlen(zeilen[-1]), "Zahl der Scout-Anfragen (%d) fehlt in: %s" % (z.anfragen, zeilen[-1])


# ── Aufbau-Schutz: beweist, dass die Attrappen sehen, was die Tests unten voraussetzen ──

def test_schutz_aufbau_scout_fragt_im_aktiven_zustand_fuer_alle_orte_wetter_an(client, welt, scout_gesichert, monkeypatch):
    """SCHUTZ-TEST (sofort grün erwartet): Ohne Pause fragt der Scout für Potsdam, Cottbus und München an. Das ist die
    Gegenprobe, ohne die ‚keine Anfrage für pausierte Orte‘ (AK-109) nichts beweisen würde."""
    scout_gesichert.refresh_subjects()
    z = _Zaehler()
    _scout_lauf(monkeypatch, z)
    for k in BR + ("muenchen",):
        assert _naehe(z.koordinaten, welt.koord(k)), "Scout fragt nicht für %s an — Testaufbau kaputt" % k


def test_schutz_aufbau_wetterlauf_nennt_orte_im_protokoll(client, welt, monkeypatch, caplog):
    """SCHUTZ-TEST (sofort grün erwartet): Das Protokoll eines Wetterlaufs enthält die Orte (Gegenprobe zu AK-53)."""
    caplog.set_level(logging.DEBUG)
    _wetterlauf(welt, monkeypatch, _Zaehler())
    text = _protokolltext(caplog)
    assert ort_id("potsdam") in text or "Potsdam" in text, "Protokoll nennt Potsdam gar nicht — AK-53-Test wäre leer"


# ── AK-109: der Scout fragt für pausierte Orte kein Wetter an ─────────────────

def _naehe(koordinaten, ort, grad=0.2):
    la, lo = ort
    return [k for k in koordinaten if abs(k[0] - la) < grad and abs(k[1] - lo) < grad]


def test_scout_fragt_fuer_orte_einer_pausierten_region_kein_wetter_an(client, welt_z, scout_gesichert, monkeypatch):
    """AK-109 / Wirkungs-Tabelle 7: Ist Brandenburg ausgeschaltet, stellt der Scout für Potsdam und Cottbus keine
    Wetteranfrage mehr; für die übrigen Orte schon. Gegenprobe VOR dem Ausschalten: Er fragte für beide an
    (sonst bewiese der Test nichts)."""
    scout_gesichert.refresh_subjects()
    vorher = _Zaehler()
    _scout_lauf(monkeypatch, vorher)
    for k in BR:
        assert _naehe(vorher.koordinaten, welt_z.koord(k)), "Gegenprobe: der Scout fragt nicht einmal im aktiven Zustand für %s an" % k

    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    scout_gesichert.refresh_subjects()
    nachher = _Zaehler()
    _scout_lauf(monkeypatch, nachher)
    for k in BR:
        assert not _naehe(nachher.koordinaten, welt_z.koord(k)), "Scout fragt für den pausierten Ort %s Wetter an" % k
    assert _naehe(nachher.koordinaten, welt_z.koord("muenchen")), "Scout fragt nicht einmal mehr für aktive Orte an"


def test_scout_fragt_fuer_ein_ausgeschaltetes_land_kein_wetter_an(client, welt_z, scout_gesichert, monkeypatch):
    """AK-109, Land statt Region: Italien aus -> keine Anfrage für Sterzing und Venedig."""
    scout_gesichert.refresh_subjects()
    host_schaltet_land(client, "Italien", False)
    scout_gesichert.refresh_subjects()
    z = _Zaehler()
    _scout_lauf(monkeypatch, z)
    for k in ("sterzing", "venedig"):
        assert not _naehe(z.koordinaten, welt_z.koord(k)), "Scout fragt für %s (Italien aus) Wetter an" % k
    assert _naehe(z.koordinaten, welt_z.koord("berlin1"))


# ── AK-53: Protokolle nennen keinen pausierten Ort ────────────────────────────

def _protokolltext(caplog) -> str:
    import main
    teile = [r.getMessage() for r in caplog.records]
    fehler = (main._job_status.get("weather") or {}).get("last_error")
    if fehler:
        teile.append(str(fehler))
    return "\n".join(teile)


def test_wetterlauf_nennt_pausierte_orte_nicht_im_protokoll(client, welt_z, monkeypatch, caplog):
    """AK-53 / AK-04: Das Protokoll eines Wetterlaufs (Zeilen und Fehlermeldung) enthält keinen Ort einer pausierten
    Region. Gegenprobe vorher: Mit Brandenburg an taucht Potsdam in der Meldung auf (sonst wäre der Test leer)."""
    caplog.set_level(logging.DEBUG)
    z = _Zaehler()
    _wetterlauf(welt_z, monkeypatch, z)
    vorher = _protokolltext(caplog)
    assert ort_id("potsdam") in vorher or "Potsdam" in vorher, \
        "Gegenprobe: Potsdam steht im aktiven Zustand gar nicht im Protokoll (Testaufbau prüft nichts)"

    caplog.clear()
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    _wetterlauf(welt_z, monkeypatch, _Zaehler())
    nachher = _protokolltext(caplog)
    for k in BR:
        assert ort_id(k) not in nachher and ORTE[k][0] not in nachher, "Protokoll nennt den pausierten Ort %s" % k
