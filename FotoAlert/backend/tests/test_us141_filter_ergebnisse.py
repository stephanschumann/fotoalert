"""US-141 — Was ein ausgeschaltetes Land / eine ausgeschaltete Region für Feed, Heute, Tagesübersicht,
Kalender, Wetterabruf und Entdecken (Scout) bedeutet — soweit serverseitig prüfbar.

Geprüft wird (Akzeptanzkriterien AK-01, AK-02, AK-04, AK-08, AK-64 bis AK-66, AK-68, AK-69, AK-73, AK-76,
AK-96, AK-100; Entscheidungen 4, 22/Annahme (n); Fragen 10, 18, 19 mit Empfehlung — von Stephan als
entschieden vorgegeben):
  - Chancen pausierter Orte verschwinden SOFORT (ohne Neustart) aus Feed, „Heute“, Tagesübersicht, Kalender
    — auch mit Ereignis-/Score-/Ort-Filter. Aktive Orte bleiben unverändert.
  - Der Deckel von 500 gilt für aktive Orte zusammen; pausierte Orte belegen keinen Platz (AK-96).
  - Der Wetterabruf bekommt keine Termine pausierter Orte (AK-04).
  - Kalender: auch der Monatsspeicher des Servers kennt den Schalterzustand (AK-02/AK-68); der Abruf für
    einen einzelnen pausierten Ort liefert nichts (AK-73).
  - Entdecken: Motive nur aus aktiven Orten, Sperrzonen aus ALLEN Orten (Fragen 10/18, AK-65);
    bei gleichem Platz stammen Name und Höhe vom aktiven Ort (AK-66); die Ausgabe blendet Ergebnisse aus,
    deren Orte alle pausiert sind (AK-64); jedes Umschalten stößt einen Neulauf an (AK-69).
Nur im Browser prüfbare Teile (Filterfenster, Zähler, Meldungen bei leerem Ergebnis, Karte) stehen NICHT hier.
Python-3.9-kompatibel.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone

import pytest

from us141_adapter import (  # noqa: F401  (welt/welt_z sind Fixtures)
    FELD_LAND, FELD_REGION, ORTE, als_host, aktive_ids, feed_ids, host_schaltet_land, host_schaltet_region,
    ort_id, termin, termin_heute, welt, welt_z, _custom_dict,
)

pytestmark = [pytest.mark.api, pytest.mark.regression]

BR = ("potsdam", "cottbus")                      # Brandenburg
REST = ("berlin1", "muenchen", "london1", "sterzing")


def _feed(welt_z, keys=BR + REST, **kw):
    welt_z.setze_feed(welt_z.termine_fuer(keys, **kw))


# ── Feed, Heute, Tagesübersicht ───────────────────────────────────────────────

@pytest.mark.parametrize("filter_", [
    {}, {"event_type": "GOLDEN_HOUR"}, {"min_score": 0.5}, {"days": 14}, {"priority": 1},
], ids=["ohne-filter", "ereignisart", "mindest-score", "tage", "prioritaet"])
def test_pausierte_region_verschwindet_sofort_aus_dem_feed_auch_mit_filtern(client, welt_z, filter_):
    """AK-01, AK-08: Region aus -> keine Chance dieser Region mehr im Feed, ohne Neustart, mit und ohne Filter;
    die übrigen Orte bleiben unverändert."""
    _feed(welt_z)
    assert feed_ids(client, **filter_) == welt_z.ids(*BR, *REST), "Ausgangslage: alle Orte haben Chancen"
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert feed_ids(client, **filter_) == welt_z.ids(*REST)


def test_feed_fuer_einen_pausierten_ort_ist_leer_und_land_aus_trifft_alle_regionen(client, welt_z):
    """AK-01, AK-80: ?location_id=<pausierter Ort> liefert nichts; Land aus lässt keine Chance des Landes übrig."""
    _feed(welt_z)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert feed_ids(client, location_id=welt_z.id("potsdam")) == set()
    assert feed_ids(client, location_id=welt_z.id("berlin1")) == welt_z.ids("berlin1")
    host_schaltet_land(client, "Deutschland", False)
    assert feed_ids(client) == welt_z.ids("london1", "sterzing")


def test_heute_und_tagesuebersicht_zaehlen_keine_pausierten_orte(client, welt_z):
    """AK-100: Die Abrufe für „heute“ und die Tagesübersicht (iOS-App) lesen den Feed-Speicher direkt und müssen
    pausierte Orte ausklammern — Anzahl der Orte, Bestenliste und besondere Ereignisse."""
    welt_z.setze_feed([termin_heute(welt_z.id(k), lat=welt_z.koord(k)[0], lon=welt_z.koord(k)[1], score=s)
                       for k, s in (("berlin1", 0.7), ("potsdam", 0.95), ("cottbus", 0.9), ("muenchen", 0.6))])
    vorher = client.get("/daily-briefing").json()
    assert vorher["location_count"] == 4
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    heute = client.get("/opportunities/today").json()
    assert {e["location_id"] for e in heute} == welt_z.ids("berlin1", "muenchen")
    tag = client.get("/daily-briefing").json()
    assert tag["location_count"] == 2
    assert {e["location_id"] for e in tag["top_opportunities"]} == welt_z.ids("berlin1", "muenchen")
    assert tag["highest_score"] == pytest.approx(0.7), "bester Score darf nicht von einem pausierten Ort stammen"


def test_deckel_500_gilt_fuer_aktive_orte_pausierte_belegen_keinen_platz(client, welt_z):
    """AK-96: 560 starke Chancen in Brandenburg + 10 schwächere in Berlin. Vor dem Pausieren kappt der Deckel auf 500;
    nach dem Pausieren stehen genau die 10 Berliner Chancen im Feed (keine Plätze für Pausierte)."""
    termine = []
    for ort in BR:
        lat, lon = welt_z.koord(ort)
        for tag in range(1, 15):
            for t in range(20):
                termine.append(termin(welt_z.id(ort), tage=tag - 0.5, typ="TYP%d" % t, score=0.9, lat=lat, lon=lon))
    lat, lon = welt_z.koord("berlin1")
    for tag in range(1, 11):
        termine.append(termin(welt_z.id("berlin1"), tage=tag - 0.5, typ="TYP0", score=0.5, lat=lat, lon=lon))
    welt_z.setze_feed(termine)
    assert len(client.get("/opportunities").json()) == 500, "Ausgangslage: der Deckel greift"
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    ergebnis = client.get("/opportunities").json()
    assert len(ergebnis) == 10
    assert {e["location_id"] for e in ergebnis} == welt_z.ids("berlin1")


# ── Wetterabruf ──────────────────────────────────────────────────────────────

def test_wetterabruf_bekommt_keine_termine_pausierter_orte(client, welt_z, monkeypatch):
    """AK-04: Nach dem Pausieren ruft der Wetterlauf für Orte der Region kein Wetter mehr ab — der Wetterabruf
    richtet sich nach den Feed-Terminen der nächsten 3 Tage."""
    import copy
    import main

    class _Halt(Exception):
        pass

    gesehen = {}

    async def _spion(near_events):
        gesehen["ids"] = {e["location_id"] for e in near_events}
        raise _Halt()

    monkeypatch.setattr(main, "_fetch_weather_and_aerosol", _spion)
    monkeypatch.setattr(main, "_job_status", copy.deepcopy(main._job_status))
    _feed(welt_z, tage=1.0)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    with pytest.raises(_Halt):
        asyncio.run(main._weather_overlay("test"))
    assert gesehen["ids"] == welt_z.ids(*REST), "Wetter wurde auch für pausierte Orte angefragt: %s" % gesehen["ids"]


# ── Kalender ─────────────────────────────────────────────────────────────────

def _mitte_des_monats():
    heute = date.today()
    return datetime(heute.year, heute.month, 15, 12, 0, tzinfo=timezone.utc), heute.year, heute.month


def test_kalender_zeigt_keine_termine_pausierter_orte_auch_aus_frueheren_laeufen(client, welt_z):
    """AK-02, AK-73, AK-76: Alte Kalender-Einträge pausierter Orte werden nicht angezeigt; der Abruf für einen
    einzelnen pausierten Ort liefert nichts; aktive Orte bleiben unverändert."""
    zeit, jahr, monat = _mitte_des_monats()
    welt_z.setze_kalender([termin(welt_z.id(k), zeit=zeit, lat=welt_z.koord(k)[0], lon=welt_z.koord(k)[1])
                           for k in BR + REST])
    params = {"month": monat, "year": jahr}
    assert {e["location_id"] for e in client.get("/calendar", params=params).json()["events"]} == welt_z.ids(*BR, *REST)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert {e["location_id"] for e in client.get("/calendar", params=params).json()["events"]} == welt_z.ids(*REST)
    assert client.get("/calendar", params=dict(params, location_id=welt_z.id("potsdam"))).json()["events"] == []
    aktiv = client.get("/calendar", params=dict(params, location_id=welt_z.id("berlin1"))).json()["events"]
    assert [e["location_id"] for e in aktiv] == [welt_z.id("berlin1")]


def test_kalender_monatsspeicher_des_servers_kennt_den_schalterzustand(client, welt_z, monkeypatch):
    """AK-02, AK-68 (Fund F15): Im Live-Betrieb rechnet der Server einen Monat über ALLE Orte und merkt ihn sich.
    Wird ein schon abgerufener Monat nach dem Umschalten erneut abgerufen, zeigt er den neuen Stand — auch bei
    aus, an, aus kurz hintereinander gilt der zuletzt gedrückte Zustand. Auch der Einzel-Ort-Abruf für einen
    pausierten Ort bleibt leer."""
    import main
    zeit, jahr, monat = _mitte_des_monats()

    async def _ein_termin_je_ort(loc, year, month, min_score):
        return [termin(loc.id, zeit=zeit, lat=loc.observer_lat, lon=loc.observer_lon)]

    monkeypatch.setenv("FOTOALERT_ONDEMAND", "1")
    monkeypatch.setattr(main, "_compute_location_month", _ein_termin_je_ort)
    params = {"month": monat, "year": jahr}

    def ids():
        return {e["location_id"] for e in client.get("/calendar", params=params).json()["events"]}

    alle = welt_z.ids(*ORTE.keys())
    assert ids() == alle, "Ausgangslage: der Monat ist berechnet und gemerkt"
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert ids() == alle - welt_z.ids(*BR)
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert ids() == alle - welt_z.ids(*BR), "zuletzt gedrückt gilt (aus)"
    assert client.get("/calendar", params=dict(params, location_id=welt_z.id("potsdam"))).json()["events"] == []
    assert len(client.get("/calendar", params=dict(params, location_id=welt_z.id("berlin1"))).json()["events"]) == 1


# ── Entdecken (Scout) ────────────────────────────────────────────────────────

def _fuege_ort_hinzu(client, welt, key, name, lat, lon, subj_lat, subj_lon, subj_name, hoehe, land, region):
    """Zusätzlicher Testort mit eigenem Motiv (für die Scout-Prüfungen)."""
    from data import locations as dl
    from data.locations import LocationCategory, PhotoLocation
    o = PhotoLocation(
        id=ort_id(key), name=name, description="US-141-Scout-Testort", category=LocationCategory.SKYLINE,
        observer_lat=lat, observer_lon=lon, subject_lat=subj_lat, subject_lon=subj_lon,
        subject_name=subj_name, subject_height_m=hoehe, subject_width_m=20.0, distance_m=1000,
        focal_length_suggestions=[50], difficulty=1,
    )
    welt.store.create_custom(_custom_dict(o))
    dl.LOCATIONS.append(o)
    als_host(client)
    r = client.patch("/locations/" + o.id, json={FELD_LAND: land, FELD_REGION: region})
    assert r.status_code == 200, r.text
    return o


def _scout_welt(client, welt_z):
    """Gemeinsames Motiv (zwei Standpunkte: pausierter Ort ZUERST gelistet, aktiver danach) + ein Motiv nur
    eines pausierten Orts + ein Motiv nur eines aktiven Orts. Brandenburg wird danach ausgeschaltet."""
    from data import locations as dl
    # die Standard-Testorte stören die Prüfung nicht: ihre Motive sind weit weg
    p_geteilt = _fuege_ort_hinzu(client, welt_z, "scout_b", "Standpunkt Brandenburg", 52.40, 13.00,
                                 52.5000, 13.5000, "Motiv Pausiert-Name", 60.0, "Deutschland", "Brandenburg")
    a_geteilt = _fuege_ort_hinzu(client, welt_z, "scout_a", "Standpunkt Bayern", 48.10, 11.50,
                                 52.5003, 13.5002, "Motiv Aktiv-Name", 80.0, "Deutschland", "Bayern")
    p_allein = _fuege_ort_hinzu(client, welt_z, "scout_c", "Standpunkt nur Brandenburg", 51.80, 14.30,
                                51.9000, 14.4000, "Motiv Nur-Pausiert", 70.0, "Deutschland", "Brandenburg")
    a_allein = _fuege_ort_hinzu(client, welt_z, "scout_d", "Standpunkt nur aktiv", 47.90, 11.40,
                                48.5000, 11.9000, "Motiv Nur-Aktiv", 70.0, "Deutschland", "Bayern")
    # Reihenfolge: der pausierte Ort des gemeinsamen Motivs steht VOR dem aktiven (Fund 5, Frage 18)
    liste = [o for o in dl.LOCATIONS if o.id not in (p_geteilt.id, a_geteilt.id)]
    dl.LOCATIONS[:] = [p_geteilt, a_geteilt] + liste
    return p_geteilt, a_geteilt, p_allein, a_allein


def test_entdecken_motive_nur_aus_aktiven_orten_sperrzonen_aus_allen(client, welt_z):
    """AK-65, AK-66, Fragen 10 und 18 (Empfehlung): Nach dem Pausieren von Brandenburg
    - gibt es kein Motiv, das nur zu pausierten Orten gehört;
    - bleibt das gemeinsame Motiv, mit Name und Höhe des AKTIVEN Orts (auch wenn der pausierte zuerst gelistet ist);
    - enthält die Sperrzone des gemeinsamen Motivs die Standpunkte ALLER Orte (auch des pausierten), damit der
      Standpunkt des pausierten Orts nicht als ‚neue Perspektive‘ vorgeschlagen wird."""
    from discover.subjects import build_subjects
    p_geteilt, a_geteilt, p_allein, a_allein = _scout_welt(client, welt_z)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    subjects, zonen = build_subjects()
    namen = {s.name: s for s in subjects}
    assert "Motiv Nur-Pausiert" not in namen, "Motiv eines nur pausierten Orts darf nicht gescoutet werden"
    assert "Motiv Pausiert-Name" not in namen, "Name des Motivs muss vom aktiven Ort stammen"
    assert "Motiv Aktiv-Name" in namen and "Motiv Nur-Aktiv" in namen
    assert namen["Motiv Aktiv-Name"].structure_height_m == pytest.approx(80.0), "Höhe vom aktiven Ort"
    zone = zonen[namen["Motiv Aktiv-Name"].id]
    assert (p_geteilt.observer_lat, p_geteilt.observer_lon) in zone, "Sperrzone muss den pausierten Standpunkt enthalten"
    assert (a_geteilt.observer_lat, a_geteilt.observer_lon) in zone


def _scout_ergebnis(subj, tage=1):
    from discover.pipeline_base import ScoutOpportunity
    tag = (date.today() + timedelta(days=tage)).isoformat()
    return asdict(ScoutOpportunity(
        body_name="moon", subject_id=subj.id, subject_name=subj.name, subject_lat=subj.lat, subject_lon=subj.lon,
        day=tag, session="golden_evening", dt_utc=tag + "T17:00:00+00:00", body_azimuth_deg=250.0,
        body_altitude_deg=10.0, body_illumination_pct=80.0, distance_m=1500.0, standpoint_lat=subj.lat,
        standpoint_lon=subj.lon, focal_length_equiv_mm=200.0, score=0.8, score_alignment=0.8, score_phase=0.8,
        score_licht=0.8, score_komposition=0.8, score_wetter=0.8, weather_description="",
    ))


def test_entdecken_ausgabe_blendet_ergebnisse_aus_deren_orte_alle_pausiert_sind(client, welt_z):
    """AK-64, Frage 19 (Empfehlung): Der Scout läuft nur als Volllauf. Beim Ausliefern werden Ergebnisse sofort
    ausgeblendet, deren Orte ALLE pausiert sind; ein Ergebnis mit mindestens einem aktiven Ort bleibt; der
    Neulauf folgt im Hintergrund. Das Zwischenergebnis (Cache) wurde vor dem Pausieren berechnet."""
    import main
    from discover.subjects import build_subjects
    _scout_welt(client, welt_z)
    subjects, _ = build_subjects()                      # Stand VOR dem Pausieren: alle Orte aktiv
    ids = {s.name: s.id for s in subjects}
    nur_pausiert = next(s for s in subjects if s.name == "Motiv Nur-Pausiert")
    geteilt = next(s for s in subjects if s.name == "Motiv Pausiert-Name")   # pausierter Ort zuerst gelistet
    nur_aktiv = next(s for s in subjects if s.name == "Motiv Nur-Aktiv")
    ergebnisse = [_scout_ergebnis(nur_pausiert), _scout_ergebnis(geteilt), _scout_ergebnis(nur_aktiv)]
    main._discover_cache = {"generated_at": "2026-10-11T00:00:00Z", "count": 3, "opportunities": ergebnisse}
    assert client.get("/discover").json()["total"] == 3
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    ausgeliefert = {o["subject_id"] for o in client.get("/discover").json()["opportunities"]}
    assert nur_pausiert.id not in ausgeliefert, "Ergebnis eines nur pausierten Orts muss sofort verschwinden"
    assert geteilt.id in ausgeliefert, "Ergebnis mit mindestens einem aktiven Ort bleibt"
    assert nur_aktiv.id in ausgeliefert


def test_jedes_umschalten_stoesst_einen_entdecken_neulauf_an(client, welt_z, monkeypatch):
    """AK-69: Jedes Umschalten — auch das Pausieren — stößt einen Entdecken-Neulauf an (über die vorhandenen
    Auslöser: entprellter Anstoß oder direkter Lauf)."""
    import main
    aufrufe = []

    def _spion_entprellt():
        aufrufe.append("entprellt")

    async def _spion_lauf():
        aufrufe.append("lauf")

    monkeypatch.setattr(main, "_trigger_discover_debounced", _spion_entprellt)
    monkeypatch.setattr(main, "_refresh_discover", _spion_lauf)
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    nach_aus = len(aufrufe)
    assert nach_aus >= 1, "Pausieren hat keinen Entdecken-Neulauf angestoßen"
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert len(aufrufe) > nach_aus, "Einschalten hat keinen Entdecken-Neulauf angestoßen"
