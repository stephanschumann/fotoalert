"""BUG-114 — Kalender-Abruf liest bei jedem Aufruf die gesamte Kalender-Datenbasis
(~1,1 GB) ein, nur um den Zeitpunkt der letzten Berechnung anzuzeigen.

Diese Tests entstanden in der Analyse-Phase (test-first, 2026-09-27) und beschreiben
die ANFORDERUNG, nicht eine bestimmte Umsetzung:
  - Ein Kalender-Abruf (Weg ohne Live-Berechnung) liest die Kalenderdatei NICHT erneut
    von der Platte und hält den Server nicht an.
  - Die Angabe "zuletzt berechnet" (computed_at) bleibt korrekt: nach dem Laden, nach
    dem Nachrechnen eines einzelnen Standorts und nach einem Volllauf.
  - Eine halb geschriebene oder unvollständige Kalenderdatei führt nicht zu einem
    Server-Fehler beim Kalender-Abruf.

Messgrundlage (Analyse 2026-09-27, Linux-VM auf Stephans Mac, synthetische Dateien):
Stillstand pro Abruf 0,36 s (53 MB), 1,07 s (160 MB), 2,0 s (320 MB) — ~6,3 ms/MB,
hochgerechnet ~7,5 s bei der echten Datei (1,19 GB). Spitzen-Arbeitsspeicher ~4,4 MB
je MB Datei (hochgerechnet ~5 GB). Die echte Datei wurde NICHT eingelesen (VM hat 3,9 GB).

Alle Tests laufen offline (kein Netz, kein Subprozess); die echte calendar.json wird
nie angefasst — jeder Test lenkt den Kalenderpfad auf tmp_path um.
"""
import asyncio
import json
import shutil

import pytest

import main
from test_bug113 import _messe_stillstand, _schreibe_kalenderdatei

pytestmark = [pytest.mark.offline, pytest.mark.regression]

MAX_STILLSTAND_S = 0.5
ZEIT_ALT = "2026-09-25T03:30:04+00:00"
ZEIT_NEU = "2026-09-27T10:00:00+00:00"


def _ev(loc_id: str, shoot_time: str, score: float) -> dict:
    return {"location_id": loc_id, "shoot_time": shoot_time, "overall_score": score}


def _bestand() -> list:
    return [
        _ev("alt_a", "2026-10-01T05:00:00+00:00", 0.9),
        _ev("neu_x", "2026-10-02T06:00:00+00:00", 0.4),
        _ev("alt_b", "2026-11-02T05:00:00+00:00", 0.8),
    ]


def _schreibe_kalender(pfad, computed_at, events) -> None:
    daten = {"algorithm_version": "1.5", "computed_locations": {}, "events": events}
    if computed_at is not None:
        daten["computed_at"] = computed_at
    pfad.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def kalender(monkeypatch, tmp_path):
    """Kleine Kalenderdatei (Stand ZEIT_ALT) über den regulären Ladeweg in den
    Arbeitsspeicher bringen — Weg ohne Live-Berechnung."""
    monkeypatch.delenv("FOTOALERT_ONDEMAND", raising=False)
    monkeypatch.setattr(main, "_precompute_running", False)
    kal = tmp_path / "calendar.json"
    _schreibe_kalender(kal, ZEIT_ALT, _bestand())
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    monkeypatch.setattr(main, "_calendar_cache", [])
    main._load_calendar_cache()
    assert len(main._calendar_cache) == 3, "Vorbedingung: Kalender im Arbeitsspeicher geladen"
    return kal


def _abruf(**kw) -> dict:
    return asyncio.run(main.get_calendar(**kw))


# ---------------------------------------------------------------------------
# AK1 — Kalender öffnen hält den Server nicht an (auch bei großer Kalenderdatei)
# ---------------------------------------------------------------------------

def test_kalender_abruf_haelt_server_nicht_an(monkeypatch, tmp_path, kalender):
    """BUG-114 AK1: Ein Monatsabruf des Kalenders lässt den Server nicht länger als
    0,5 s am Stück stehen — auch wenn die Kalenderdatei auf der Platte groß ist
    (Testgröße 200 MB; echte Datei aktuell ~1,19 GB)."""
    roh = tmp_path / "calendar_roh.json"
    _schreibe_kalenderdatei(roh, 200)
    gross = tmp_path / "calendar_gross.json"
    # Realistischer Aufbau wie precompute.py: Berechnungszeitpunkt steht in der Datei.
    with open(roh, "rb") as quelle, open(gross, "wb") as ziel:
        quelle.read(1)  # führende "{" überspringen
        ziel.write(('{"computed_at": "%s", ' % ZEIT_NEU).encode("utf-8"))
        shutil.copyfileobj(quelle, ziel, 16 * 1024 * 1024)
    roh.unlink()
    # Die große Datei liegt jetzt am Kalenderpfad; im Arbeitsspeicher steht weiter
    # der bereits geladene Stand. Ein Abruf darf die Datei nicht erneut einlesen.
    monkeypatch.setattr(main, "_CAL_CACHE", gross)

    ergebnis = {}

    async def arbeit():
        ergebnis["r"] = await main.get_calendar(month=10, year=2026)

    stillstand = asyncio.run(_messe_stillstand(arbeit))
    assert ergebnis["r"]["status"] == "ok"
    assert stillstand <= MAX_STILLSTAND_S, (
        f"Kalender-Abruf hielt den Server {stillstand:.2f} s am Stück an "
        f"(erlaubt: {MAX_STILLSTAND_S} s) — BUG-114 AK1 nicht erfüllt."
    )


# ---------------------------------------------------------------------------
# AK2 — "zuletzt berechnet" stimmt, ohne die Datei erneut zu lesen
# ---------------------------------------------------------------------------

def test_zeitpunkt_entspricht_dem_geladenen_stand(kalender):
    """BUG-114 AK2: Nach dem Laden zeigt der Kalender den Berechnungszeitpunkt der
    geladenen Kalenderdatei."""
    r = _abruf(month=10, year=2026)
    assert r["status"] == "ok"
    assert r["computed_at"] == ZEIT_ALT


def test_halb_geschriebene_datei_fuehrt_nicht_zu_serverfehler(kalender):
    """BUG-114 AK5 (Fehlerfall): Wird die Kalenderdatei gerade neu geschrieben (Inhalt
    noch unvollständig), antwortet der Kalender trotzdem normal mit den Einträgen aus
    dem Arbeitsspeicher und dem Zeitpunkt des geladenen Stands — kein Server-Fehler."""
    kalender.write_text('{"algorithm_version": "1.5", "computed_at": "2026-09-2', encoding="utf-8")
    r = _abruf(month=10, year=2026)
    assert r["status"] == "ok"
    assert r["total"] == 2
    assert r["computed_at"] == ZEIT_ALT


def test_datei_ohne_zeitpunkt_fuehrt_nicht_zu_serverfehler(monkeypatch, tmp_path):
    """BUG-114 AK5 (Fehlerfall): Enthält die Kalenderdatei keinen Berechnungszeitpunkt,
    antwortet der Kalender normal; die Angabe bleibt leer."""
    monkeypatch.delenv("FOTOALERT_ONDEMAND", raising=False)
    kal = tmp_path / "calendar.json"
    _schreibe_kalender(kal, None, _bestand())
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    monkeypatch.setattr(main, "_calendar_cache", [])
    main._load_calendar_cache()
    r = _abruf(month=10, year=2026)
    assert r["status"] == "ok"
    assert r["total"] == 2
    assert r["computed_at"] is None


# ---------------------------------------------------------------------------
# AK3/AK4 — Zeitpunkt folgt Einzel-Nachberechnung und Volllauf (Regressionsschutz)
# ---------------------------------------------------------------------------

def test_zeitpunkt_nach_einzel_nachberechnung(kalender):
    """BUG-114 AK3: Nach dem Nachrechnen eines einzelnen Standorts zeigt der Kalender
    den neuen Berechnungszeitpunkt (wie heute: der Einzellauf schreibt Kalenderdatei
    UND Übergabedatei mit demselben Zeitpunkt)."""
    neue = [_ev("neu_x", "2026-10-03T06:00:00+00:00", 0.7)]
    events = [e for e in _bestand() if e["location_id"] != "neu_x"] + neue
    _schreibe_kalender(kalender, ZEIT_NEU, events)
    (kalender.parent / main._CAL_SINGLE_DELTA_NAME).write_text(
        json.dumps({"location_id": "neu_x", "computed_at": ZEIT_NEU, "events": neue}),
        encoding="utf-8",
    )
    assert asyncio.run(main._apply_calendar_delta("neu_x")) is True
    r = _abruf(month=10, year=2026)
    assert r["computed_at"] == ZEIT_NEU
    assert [e["shoot_time"] for e in r["events"] if e["location_id"] == "neu_x"] == [
        "2026-10-03T06:00:00+00:00"
    ]


def test_zeitpunkt_nach_volllauf(kalender):
    """BUG-114 AK4: Nach einem vollständigen Neuladen des Kalenders (Volllauf,
    Serverstart) zeigt der Kalender den neuen Berechnungszeitpunkt."""
    _schreibe_kalender(kalender, ZEIT_NEU, _bestand())
    main._load_calendar_cache()
    assert _abruf(month=10, year=2026)["computed_at"] == ZEIT_NEU


# ---------------------------------------------------------------------------
# AK6/AK7 — Leerzustand, Filter und Live-Berechnung unverändert (Regression)
# ---------------------------------------------------------------------------

def test_leerer_kalender_meldet_weiter_kein_cache(monkeypatch, tmp_path):
    """BUG-114 AK6: Ist kein Kalender geladen, bleibt die bisherige Meldung."""
    monkeypatch.delenv("FOTOALERT_ONDEMAND", raising=False)
    monkeypatch.setattr(main, "_calendar_cache", [])
    monkeypatch.setattr(main, "_precompute_running", False)
    monkeypatch.setattr(main, "_CAL_CACHE", tmp_path / "gibt_es_nicht.json")
    assert _abruf(month=10, year=2026)["status"] == "no_cache"
    monkeypatch.setattr(main, "_precompute_running", True)
    assert _abruf(month=10, year=2026)["status"] == "calculating"


def test_filter_liefern_dieselben_eintraege(kalender):
    """BUG-114 AK7: Standort-, Monats-, Jahres- und Mindestwert-Filter liefern dieselben
    Einträge wie vorher."""
    assert _abruf(month=10, year=2026)["total"] == 2
    assert _abruf(month=11, year=2026)["total"] == 1
    assert _abruf(location_id="alt_a")["total"] == 1
    assert _abruf(month=10, year=2026, min_score=0.5)["total"] == 1
    assert _abruf()["total"] == 3


def test_live_berechnung_unveraendert(monkeypatch):
    """BUG-114 AK7: Mit eingeschalteter Live-Berechnung (Produktiv-Konfiguration laut
    Dienstdatei) bleibt die Antwort unverändert: live berechnet, Zeitpunkt leer."""
    monkeypatch.setenv("FOTOALERT_ONDEMAND", "1")

    async def monat(year, month, min_score=0.35):
        return [_ev("alt_a", "2026-10-01T05:00:00+00:00", 0.9)]

    monkeypatch.setattr(main, "_compute_month_all_locations", monat)
    r = _abruf(month=10, year=2026)
    assert r["on_demand"] is True
    assert r["computed_at"] is None
    assert r["total"] == 1
