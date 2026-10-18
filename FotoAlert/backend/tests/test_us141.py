"""US-141 — Host schaltet Orte und Regionen ein/aus (Bundle mit BUG-118).

Diese Datei enthält bewusst NUR Schutz-Tests (Regressionsschutz) für die bereits
ENTSCHIEDENEN Teile, die unabhängig von der noch offenen Wahl der Umsetzung
(Weg-Gate: Option A/B/C) formulierbar sind. Sie entstanden in der Analyse-Phase
(test-first, 2026-10-11) und sichern das Gegenstück zur künftigen Pause-Regel ab
(Pre-Mortem 10 „Verwechslung Ortsdaten/Berechnungsdienste"):

  - Ortsdaten-Dienste (Gruppe A, Entscheidungen Frage 6/7/8) laufen weiter für JEDEN Ort
    der Ortsliste: nächtliche Qualitätsprüfung, Sichtachsen-Prüfung (Host-Knopf
    „alle prüfen"), Höhen- und Sichtachsen-Schritt der Einzel-Neuberechnung.
  - Der Wetterabruf richtet sich ausschließlich nach den Terminen im Feed (Wirkungs-Tabelle
    Zeile 1): was nicht im Feed steht, bekommt kein Wetter.

Die Tests für Schalter, Regionen, Nachlade-Lauf und Host-Rechte der neuen Funktion
(rot, test-first) können erst geschrieben werden, wenn das Weg-Gate die Schnittstelle
festgelegt hat — sonst würde die Schnittstelle hier still entschieden. Siehe Ticket
US-141, Abschnitt „Tests (Stand 2026-10-11)".

Alle Tests laufen offline (eigene temporäre Datenbank, gestubbte externe Dienste).
"""
import asyncio
from datetime import date, datetime, timedelta, timezone

import pytest

import main
import precompute as P
from data.locations import LOCATIONS as _GETEILTE_LISTE, LocationCategory, PhotoLocation
from data.store import LocationStore

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _ort(loc_id: str) -> PhotoLocation:
    return PhotoLocation(
        id=loc_id, name=f"Testort {loc_id}", description="US-141-Testort",
        category=LocationCategory.SKYLINE,
        observer_lat=52.5, observer_lon=13.4,
        subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
    )


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Gruppe A bleibt auf der GANZEN Ortsliste (Fragen 6 und 7)
# ---------------------------------------------------------------------------

def test_nachtliche_qualitaetspruefung_nimmt_jeden_ort_der_liste(monkeypatch, tmp_path):
    """US-141 Frage 7: Die nächtliche Qualitätsprüfung (inkl. KI-Beschreibung) prüft jeden
    neuen/geänderten Ort der Ortsliste — die künftige Pause-Regel darf sie nicht erfassen."""
    store = LocationStore(db_path=tmp_path / "us141_qa.db")
    orte = [_ort("us141_a"), _ort("us141_b"), _ort("us141_c")]
    geprueft: list = []

    def _verbessere(loc, s):
        geprueft.append(loc.id)
        return True

    monkeypatch.setattr(main, "LOCATIONS", orte)
    monkeypatch.setattr(main, "_store", store)
    monkeypatch.setattr(main, "_qa_improve_one", _verbessere)
    monkeypatch.setattr(main, "_QA_PASS_THROTTLE_S", 0.0)
    monkeypatch.setattr(main, "_qa_pass_running", False)
    monkeypatch.setattr(main, "_precompute_running", False)
    _run(main._run_qa_pass())
    assert sorted(geprueft) == ["us141_a", "us141_b", "us141_c"]


def test_sichtachsen_knopf_alle_pruefen_besucht_jeden_ort(monkeypatch):
    """US-141 Frage 6 (+ Annahme „alle prüfen"): Der Host-Knopf prüft jeden Ort der Liste."""
    orte = [_ort("us141_s1"), _ort("us141_s2")]
    besucht: list = []

    async def _fake_check(store, loc, provider):
        besucht.append(loc.id)
        return {"status": "ok"}

    async def _kein_warten(*a, **k):
        return None

    monkeypatch.setattr(main, "LOCATIONS", orte)
    monkeypatch.setattr(main.sightline_calc, "update_location_sightline", _fake_check)
    monkeypatch.setattr(main, "_load_qa_values", lambda: None)
    monkeypatch.setattr(main, "_load_feed_cache", lambda: True)
    monkeypatch.setattr(main, "_job_start", lambda job: 0.0)
    monkeypatch.setattr(main, "_job_done", lambda job, t0: None)
    monkeypatch.setattr(main, "_job_error", lambda job, t0, msg: None)
    monkeypatch.setattr(main.asyncio, "sleep", _kein_warten)
    _run(main._run_sightline_refresh())
    assert sorted(besucht) == ["us141_s1", "us141_s2"]


@pytest.mark.parametrize("run_feed,run_calendar", [(True, False), (False, True), (True, True)])
def test_einzelberechnung_fuehrt_hoehe_und_sichtachse_immer_aus(monkeypatch, run_feed, run_calendar):
    """US-141 Pre-Mortem 8: Die Einzel-Neuberechnung mischt Ortsdaten (Höhe, Sichtachse)
    und Berechnungsdienste (Feed, Kalender). Die Ortsdaten-Schritte laufen heute in jedem
    Teillauf; Feed/Kalender nur, wenn angefordert. Schutz für die künftige Aufteilung."""
    aufrufe: list = []

    async def _rec(name):
        aufrufe.append(name)

    async def _hoehe(**k):
        await _rec("hoehe")

    async def _sicht(**k):
        await _rec("sichtachse")

    async def _feed(**k):
        await _rec("feed")

    async def _kal(**k):
        await _rec("kalender")

    monkeypatch.setattr(P, "_refresh_single_location_elevation", _hoehe)
    monkeypatch.setattr(P, "_check_single_location_sightline", _sicht)
    monkeypatch.setattr(P, "_refresh_single_location_feed", _feed)
    monkeypatch.setattr(P, "_refresh_single_location_calendar", _kal)
    vorher = list(_GETEILTE_LISTE)
    _GETEILTE_LISTE[:] = [_ort("us141_e1")]
    try:
        _run(P._run_single_location_flow(
            location_id="us141_e1", today=date.today(), computed_at="2026-10-11T00:00:00+00:00",
            run_feed=run_feed, run_calendar=run_calendar, feed_path=None, elev_path=None, t0=0.0,
        ))
    finally:
        _GETEILTE_LISTE[:] = vorher
    assert aufrufe.count("hoehe") == 1 and aufrufe.count("sichtachse") == 1
    assert ("feed" in aufrufe) == run_feed
    assert ("kalender" in aufrufe) == run_calendar


# ---------------------------------------------------------------------------
# Wetterabruf hängt nur am Feed (Wirkungs-Tabelle Zeile 1)
# ---------------------------------------------------------------------------

def _termin(loc_id: str, lat: float) -> dict:
    zeit = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    return {"location_id": loc_id, "shoot_time": zeit, "overall_score": 0.7,
            "observer_lat": lat, "observer_lon": 13.4}


def test_wetterabruf_fragt_nur_orte_mit_terminen_im_feed_ab(monkeypatch):
    """US-141 Wirkungs-Tabelle Zeile 1: Wetter wird nur für Orte mit Terminen in den
    nächsten 3 Tagen im Feed abgerufen. Ein Ort ohne Feed-Termine (künftig: pausiert,
    weil sein Feed leer bleibt) löst keinen Abruf aus."""
    angefragt: list = []

    async def _fake_fetch(near_events):
        angefragt.append({e["location_id"] for e in near_events})
        return ({}, {}, {}, {}, {}, [], [], [], [], [])

    monkeypatch.setattr(main, "_fetch_weather_and_aerosol", _fake_fetch)
    monkeypatch.setattr(main, "_lookup_projected_forecasts", lambda *a, **k: (None, None, None))
    monkeypatch.setattr(main, "_lookup_red_clouds_forecast", lambda *a, **k: None)
    monkeypatch.setattr(main, "_apply_weather_to_event", lambda *a, **k: False)
    monkeypatch.setattr(main, "_inject_cloud_mood_events", lambda: None)
    monkeypatch.setattr(main, "_job_start", lambda job: 0.0)
    monkeypatch.setattr(main, "_job_done", lambda job, t0: None)
    monkeypatch.setattr(main, "_job_error", lambda job, t0, msg: None)

    monkeypatch.setattr(main, "_feed_cache", [_termin("us141_w1", 52.5), _termin("us141_w2", 50.1)])
    _run(main._weather_overlay(triggered_by="test"))
    assert angefragt[-1] == {"us141_w1", "us141_w2"}

    monkeypatch.setattr(main, "_feed_cache", [_termin("us141_w1", 52.5)])
    _run(main._weather_overlay(triggered_by="test"))
    assert angefragt[-1] == {"us141_w1"}, "Ort ohne Feed-Termine darf keinen Wetterabruf auslösen"
