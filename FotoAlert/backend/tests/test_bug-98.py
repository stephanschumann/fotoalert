"""
Regressionssuite -- BUG-98: Location-Daten: Beobachter- und Motivkoordinaten bei
mehreren Locations identisch.

Bug: `calculate_azimuth_alignment()` (calculations/astronomy.py) liefert bei
identischen Beobachter-/Motivkoordinaten keinen Fehler und kein None, sondern einen
scheinbar gueltigen, aber komplett irrefuehrenden Wert -- atan2(0,0)=0 -> exakt 0.0
Grad (Nord), jedes Mal. Dieser Wert floss unveraendert in alle vier verifizierten
Aufrufer (astronomy.find_precise_alignment_times(), window_engine.WindowEphemeris.
alignments(), query_engine.find_precise_alignment_times_v2(), main.py
/preview-alignment) sowie in calculations/opportunity.py (subject_azimuth auf JEDER
Foto-Chance, nicht nur Alignment-Events).

Fix (Weg-Gate-Entscheidung Stephan 2026-09-04, Option A):
  - Regel 1 (Code-Schutz): SubjectAngularProfile.is_degenerate wird gesetzt, wenn
    ground_distance_m < DEGENERATE_SUBJECT_DISTANCE_M (5m) liegt. Alle Aufrufer
    pruefen dieses Flag und liefern bei Degenerierung leere Ergebnisse/None/400
    statt eines irrefuehrenden Zahlenwerts.
  - Regel 2/3 (Datenkorrektur): 13 Kategorie-1-Panorama-Locations bekommen
    subject_lat=subject_lon=None (kein Motiv); Brandenburger Tor -- Tiergartenseite
    und Glienicker Bruecke (Kategorie 3) bekommen einen recherchierten, echten
    Beobachter-Standpunkt.
  - Regel 4: die 12 Kategorie-2-Locationscout-Import-Platzhalter bleiben in den
    Koordinaten unveraendert (weiterhin identisch), sind aber durch Regel 1 vor der
    Fehlanzeige geschuetzt (AK6).

Testplan-Referenz (BACKLOG.md, Ticket BUG-98, Abschnitt "Testplan"):
  - calculate_azimuth_alignment()/calculate_subject_angular_profile() mit
    identischen Koordinaten -> is_degenerate=True (AK1).
  - find_precise_alignment_times() UND WindowEphemeris.alignments() (beide Pfade
    einzeln) mit identischen Koordinaten -> leere Ergebnisliste (AK2).
  - Alle 13 Kategorie-1-IDs: subject_lat is None and subject_lon is None (AK3).
  - brandenburger_tor_tiergarten/glienicker_brucke: observer != subject,
    Distanz-/Azimut-Toleranzcheck (AK4).
  - Regressions-Stichprobe: 3-5 bestehende, unveraenderte Locations -> identisches
    Azimut-/Alignment-Ergebnis wie vor dem Fix (AK5).
  - /preview-alignment mit identischen Koordinaten -> HTTP 400 (AK9).

Python-3.12-kompatibel (Server/CI laufen auf 3.12, siehe CLAUDE.md).
"""
from __future__ import annotations

import asyncio
from datetime import date

import pytest

import calculations.astronomy as astro
import calculations.window_engine as window_engine
from calculations.opportunity import EventType, find_opportunities
from calculations.weather import WeatherForecast
from data.locations import LOCATIONS

pytestmark = [pytest.mark.offline, pytest.mark.regression]

# WICHTIG: `_LOC_BY_ID` haelt tiefe Kopien, NICHT die Original-Objekte aus dem
# geteilten `LOCATIONS`-Singleton. Grund: main.py:_load_location_overrides() wird
# beim allerersten Test der Session ausgefuehrt (main.conftest.py's autouse-Fixture
# `_isolate_client_cookies` verlangt die session-weite `client`-Fixture, die beim
# TestClient-Startup main.startup() -- und damit _load_location_overrides() --
# ausloest, siehe --setup-show). Dieses Startup wendet in `data_dev/fotoalert.db`
# persistierte Location-Overrides PER setattr() AUF DIE ORIGINAL-OBJEKTE an, bevor
# ueberhaupt ein Testkoerper laeuft -- unabhaengig von der Reihenfolge der
# Testklassen in dieser Datei. Ein direkter Verweis auf die LOCATIONS-Objekte wuerde
# deshalb hier bereits durch echte (aber fuer dieses Ticket irrelevante) Dev-DB-
# Overrides verfaelschte Werte liefern, statt der frischen Werte aus data/locations.py.
# Tiefe Kopien, angelegt beim Modul-Import (Collection-Zeit, VOR jedem Fixture-Setup),
# umgehen das sauber, ohne die geteilte data_dev/fotoalert.db anzufassen (Regel:
# keine Mutation der aktiven Dev-Datenbank durch Testlaeufe).
import copy as _copy
_LOC_BY_ID = {loc.id: _copy.deepcopy(loc) for loc in LOCATIONS}

_CATEGORY1_IDS = [
    "volkspark_friedrichshain_wasserturm", "muggelturm", "wannsee_strandbad",
    "nikolaisee_potsdam", "schweriner_see_havelland", "spreewald_kanal",
    "stechlin_see", "schorfheide_herbst", "elbtalaue_wittenberge",
    "rügen_kreidefelssen_jasmund", "tempelhofer_feld_landebahn", "teufelsberg",
    "muggelspree_kopenick",
]


def _empty_forecast(lat: float, lon: float) -> WeatherForecast:
    """Leerer Wetter-Forecast -- ausreichend, solange find_opportunities() mit
    astronomy_only=True (kein Wetter-Score-Zugriff) aufgerufen wird."""
    from datetime import datetime, timezone
    return WeatherForecast(location_lat=lat, location_lon=lon,
                            fetched_at=datetime.now(timezone.utc), hourly=[])


# ---------------------------------------------------------------------------
# AK1: calculate_subject_angular_profile() markiert identische/quasi-identische
# Koordinaten als degeneriert, statt einen irrefuehrenden 0.0-Grad-Azimut zu liefern.
# ---------------------------------------------------------------------------

class TestCalculateSubjectAngularProfileDegenerateGuard:

    def test_identische_koordinaten_sind_degeneriert(self):
        profile = astro.calculate_subject_angular_profile(52.5271, 13.4360, 52.5271, 13.4360)
        assert profile.is_degenerate is True
        assert profile.ground_distance_m == 0.0

    def test_koordinaten_knapp_unter_der_schwelle_sind_degeneriert(self):
        # ca. 1m Versatz (GPS-Rundungsfehler) -- deutlich unter der 5m-Schwelle
        profile = astro.calculate_subject_angular_profile(52.5271, 13.4360, 52.527109, 13.4360)
        assert profile.ground_distance_m < astro.DEGENERATE_SUBJECT_DISTANCE_M
        assert profile.is_degenerate is True

    def test_kleinste_reale_distanz_im_bestand_bleibt_unberuehrt(self):
        # Telegrafenberg -- Einsteinturm: kleinste reale distance_m>0 im gesamten
        # Bestand (80m, siehe backend/data/locations.py) -- muss klar oberhalb der
        # 5m-Schwelle bleiben, damit keine echte Nah-Location faelschlich erfasst wird.
        loc = _LOC_BY_ID["telegrafenberg_potsdam"]
        profile = astro.calculate_subject_angular_profile(
            loc.observer_lat, loc.observer_lon, loc.subject_lat, loc.subject_lon,
        )
        assert profile.is_degenerate is False
        assert profile.ground_distance_m > astro.DEGENERATE_SUBJECT_DISTANCE_M


# ---------------------------------------------------------------------------
# AK2: find_precise_alignment_times() (Fallback-Pfad ohne Window-Engine) UND
# WindowEphemeris.alignments() (aktiver TASK-25-Pfad) liefern bei identischen
# Koordinaten eine leere Ergebnisliste -- keine falsche Alignment-Chance.
# ---------------------------------------------------------------------------

class TestAlignmentSearchDegenerateGuard:

    def test_find_precise_alignment_times_leer_bei_identischen_koordinaten(self):
        results = astro.find_precise_alignment_times(
            52.5271, 13.4360, 52.5271, 13.4360,
            subject_height_m=50.0, subject_width_m=20.0,
            target_date=date(2026, 6, 21), body="sun",
        )
        assert results == []

    def test_window_ephemeris_alignments_leer_bei_identischen_koordinaten(self):
        we = window_engine.WindowEphemeris(52.5271, 13.4360, date(2026, 6, 21), 1)
        results = we.alignments(52.5271, 13.4360, 50.0, 20.0, date(2026, 6, 21), "sun")
        assert results == []
        results_moon = we.alignments(52.5271, 13.4360, 50.0, 20.0, date(2026, 6, 21), "moon")
        assert results_moon == []


# ---------------------------------------------------------------------------
# AK3: Kategorie 1 -- alle 13 Panorama-/Aussichtspunkt-Locations haben
# subject_lat=subject_lon=None (kein dupliziertes Motiv mehr).
# ---------------------------------------------------------------------------

class TestKategorie1PanoramaLocationsOhneMotiv:

    @pytest.mark.parametrize("loc_id", _CATEGORY1_IDS)
    def test_subject_koordinaten_sind_none(self, loc_id):
        loc = _LOC_BY_ID[loc_id]
        assert loc.subject_lat is None
        assert loc.subject_lon is None

    def test_alle_13_ids_tatsaechlich_im_bestand_gefunden(self):
        # Schuetzt gegen einen still verschwundenen/umbenannten Fixture-Eintrag.
        assert len(_CATEGORY1_IDS) == 13
        for loc_id in _CATEGORY1_IDS:
            assert loc_id in _LOC_BY_ID, f"Location {loc_id} nicht im Bestand gefunden"


# ---------------------------------------------------------------------------
# AK4: Kategorie 3 -- Brandenburger Tor/Glienicker Bruecke bekommen einen
# recherchierten, echten Beobachter-Standpunkt (kein Duplikat mehr).
# ---------------------------------------------------------------------------

class TestKategorie3RecherchierterBeobachterStandpunkt:

    @pytest.mark.parametrize("loc_id,expected_azimuth_hint", [
        ("brandenburger_tor_tiergarten", 90.0),
        ("glienicker_brucke", 280.0),
    ])
    def test_beobachter_weicht_vom_motiv_ab_und_haelt_toleranzen(self, loc_id, expected_azimuth_hint):
        loc = _LOC_BY_ID[loc_id]

        # Kein Duplikat mehr
        assert (loc.observer_lat, loc.observer_lon) != (loc.subject_lat, loc.subject_lon)

        dist = astro.calculate_haversine_distance(
            loc.observer_lat, loc.observer_lon, loc.subject_lat, loc.subject_lon,
        )
        az = astro.calculate_azimuth_alignment(
            loc.observer_lat, loc.observer_lon, loc.subject_lat, loc.subject_lon,
        )

        # Distanz innerhalb +/-20% des bestehenden distance_m
        assert loc.distance_m * 0.8 <= dist <= loc.distance_m * 1.2, (
            f"{loc_id}: neue Distanz {dist:.1f}m weicht zu stark von distance_m="
            f"{loc.distance_m} ab"
        )
        # Azimut Beobachter->Motiv innerhalb +/-15 Grad um den in solar_alignment_note
        # dokumentierten Wert (wrap-sicher via (diff+180)%360-180)
        az_diff = abs((az - expected_azimuth_hint + 180) % 360 - 180)
        assert az_diff <= 15.0, (
            f"{loc_id}: Azimut {az:.1f} Grad weicht {az_diff:.1f} Grad vom erwarteten "
            f"Wert {expected_azimuth_hint} Grad ab (solar_alignment_note)"
        )

        # Der neue Standpunkt ist selbst nicht degeneriert
        profile = astro.calculate_subject_angular_profile(
            loc.observer_lat, loc.observer_lon, loc.subject_lat, loc.subject_lon,
        )
        assert profile.is_degenerate is False

    def test_access_note_bleibt_unveraendert_konsistent(self):
        # Pre-Mortem Szenario 4: der neue Standpunkt darf der bestehenden
        # Zugangsbeschreibung nicht widersprechen -- hier verifiziert ueber
        # Unveraendertheit der Notiz selbst (keine neue, widerspruechliche Angabe).
        assert _LOC_BY_ID["brandenburger_tor_tiergarten"].access_note == (
            "17. Juni Straße, öffentlich, Stativ-Erlaubnis morgens meist ok"
        )
        assert _LOC_BY_ID["glienicker_brucke"].access_note == (
            "Öffentlich, Uferweg auf beiden Seiten"
        )


# ---------------------------------------------------------------------------
# AK5 (Regression): bestehende, unveraenderte Locations mit unterschiedlichen
# Koordinaten bleiben unberuehrt -- weder Azimut- noch Alignment-Verhalten aendert
# sich durch den neuen Degenerations-Schutz.
# ---------------------------------------------------------------------------

class TestRegressionBestehendeLocationsUnveraendert:

    @pytest.mark.parametrize("loc_id", [
        "schloss_babelsberg_pfingstberg",
        "schloss_sanssouci",
        "telegrafenberg_potsdam",
        "oberbaumbrucke_spree",
        "treptower_park_spree",
    ])
    def test_unveraenderte_locations_bleiben_nicht_degeneriert(self, loc_id):
        loc = _LOC_BY_ID[loc_id]
        assert loc.subject_lat is not None and loc.subject_lon is not None
        assert (loc.observer_lat, loc.observer_lon) != (loc.subject_lat, loc.subject_lon)
        profile = astro.calculate_subject_angular_profile(
            loc.observer_lat, loc.observer_lon, loc.subject_lat, loc.subject_lon,
        )
        assert profile.is_degenerate is False

    def test_babelsberg_belvedere_azimut_bleibt_wie_dokumentiert(self):
        # Docstring-Beispiel calculate_subject_angular_profile()/
        # find_precise_alignment_times(): subject_azimuth ~315 Grad.
        loc = _LOC_BY_ID["schloss_babelsberg_pfingstberg"]
        profile = astro.calculate_subject_angular_profile(
            loc.observer_lat, loc.observer_lon, loc.subject_lat, loc.subject_lon,
            subject_height_m=loc.subject_height_m or 0.0,
            subject_width_m=loc.subject_width_m or 0.0,
            elevation_difference_m=loc.elevation_difference_m,
        )
        assert profile.is_degenerate is False
        assert 310.0 <= profile.azimuth_deg <= 320.0


# ---------------------------------------------------------------------------
# AK6/AK7: Kategorie-2-Platzhalter (weiterhin identische Koordinaten, bewusst nicht
# korrigiert) UND jede zukuenftige/unbekannte Location mit identischen Koordinaten
# sind durch den Code-Schutz trotzdem vor Fehlanzeige/Falsch-Chance geschuetzt.
# ---------------------------------------------------------------------------

class TestKategorie2UndZukunftssicherheitDerOpportunityEbene:

    def test_kategorie2_platzhalter_liefert_kein_subject_azimuth_und_keine_alignment_chance(self):
        # berlin_cathedral_berliner_dom: Kategorie-2-Locationscout-Import-Platzhalter,
        # Koordinaten bewusst unveraendert (weiterhin identisch), subject_height_m=20.0
        # gesetzt -- haette VOR dem Fix den 3D-Alignment-Pfad mit degenerierter
        # Geometrie ausgeloest (falscher Nordpfeil + evtl. falsche Alignment-Chance).
        loc = _LOC_BY_ID["berlin_cathedral_berliner_dom"]
        assert loc.subject_lat == loc.observer_lat and loc.subject_lon == loc.observer_lon
        forecast = _empty_forecast(loc.observer_lat, loc.observer_lon)

        opportunities = asyncio.run(find_opportunities(
            loc, date(2026, 6, 21), forecast, min_score=0.0, astronomy_only=True,
        ))

        assert opportunities, "Keine Chancen generiert -- Testaufbau pruefen"
        for opp in opportunities:
            assert opp.subject_azimuth is None, (
                f"{opp.id}: subject_azimuth={opp.subject_azimuth} statt None "
                f"(degenerierte Koordinaten muessen None liefern, AK1/AK6)"
            )
            assert opp.event_type not in (EventType.SUN_ALIGNMENT, EventType.MOON_ALIGNMENT), (
                f"{opp.id}: {opp.event_type} haette bei degenerierten Koordinaten nicht "
                f"erzeugt werden duerfen (AK2/AK6)"
            )

    def test_beliebige_zukuenftige_location_mit_identischen_koordinaten_ist_geschuetzt(self):
        # AK7: nicht nur die aktuell bekannten Faelle -- eine voellig neue, synthetische
        # Location mit identischen Koordinaten wird ebenso geschuetzt (keine Sonderliste
        # von IDs im Guard, reine Distanzpruefung).
        from data.locations import PhotoLocation, LocationCategory
        synth = PhotoLocation(
            id="bug98_test_zukuenftige_location",
            name="Test-Location (BUG-98 AK7)",
            description="Synthetische Location fuer den Zukunftssicherheits-Test.",
            category=LocationCategory.SKYLINE,
            observer_lat=50.0, observer_lon=10.0,
            subject_lat=50.0, subject_lon=10.0,
            subject_name="Test-Motiv",
            subject_height_m=30.0,
            distance_m=0,
        )
        forecast = _empty_forecast(synth.observer_lat, synth.observer_lon)
        opportunities = asyncio.run(find_opportunities(
            synth, date(2026, 6, 21), forecast, min_score=0.0, astronomy_only=True,
        ))
        for opp in opportunities:
            assert opp.subject_azimuth is None
            assert opp.event_type not in (EventType.SUN_ALIGNMENT, EventType.MOON_ALIGNMENT)


# ---------------------------------------------------------------------------
# AK8: PATCH-Pfad -- eine zur Laufzeit (nicht im Datenbestand) veraenderte Location
# wird ohne Server-Neustart sofort korrekt als degeneriert erkannt.
# ---------------------------------------------------------------------------

class TestPatchPfadSofortWirksam:

    def test_nachtraeglich_identisch_gesetzte_koordinaten_greifen_sofort(self):
        from data.locations import PhotoLocation, LocationCategory
        loc = PhotoLocation(
            id="bug98_test_patch_location",
            name="Test-Location (BUG-98 AK8)",
            description="Simuliert einen PATCH, der Motiv-Koordinaten identisch zum "
                        "Standort setzt.",
            category=LocationCategory.SKYLINE,
            observer_lat=51.0, observer_lon=11.0,
            subject_lat=51.001, subject_lon=11.001,  # zunaechst ein echtes Motiv
            subject_name="Test-Motiv",
            subject_height_m=30.0,
            distance_m=140,
        )
        forecast = _empty_forecast(loc.observer_lat, loc.observer_lon)

        before = asyncio.run(find_opportunities(loc, date(2026, 6, 21), forecast,
                                                 min_score=0.0, astronomy_only=True))
        assert any(o.subject_azimuth is not None for o in before), (
            "Vor dem simulierten PATCH sollte ein echter subject_azimuth vorliegen"
        )

        # Simulierter PATCH: Host setzt Motiv-Koordinaten versehentlich = Standort.
        loc.subject_lat = loc.observer_lat
        loc.subject_lon = loc.observer_lon

        after = asyncio.run(find_opportunities(loc, date(2026, 6, 21), forecast,
                                                min_score=0.0, astronomy_only=True))
        for opp in after:
            assert opp.subject_azimuth is None
            assert opp.event_type not in (EventType.SUN_ALIGNMENT, EventType.MOON_ALIGNMENT)


# ---------------------------------------------------------------------------
# AK9: POST /preview-alignment mit identischen Beobachter-/Motivkoordinaten liefert
# einen erklaerenden 400er statt eines stillen, bedeutungslosen Ergebnisses.
# ---------------------------------------------------------------------------

@pytest.mark.api
class TestPreviewAlignmentEndpointDegenerateGuard:

    def test_identische_koordinaten_liefern_400(self, client, host_token):
        payload = {
            "observer_lat": 52.5271, "observer_lon": 13.4360,
            "subject_lat": 52.5271, "subject_lon": 13.4360,
            "subject_name": "Unbenannt", "subject_height_m": 30.0,
            "subject_width_m": 10.0, "days": 1, "save": False,
        }
        r = client.post("/preview-alignment", json=payload)
        assert r.status_code == 400, r.text

    def test_unterschiedliche_koordinaten_bleiben_unveraendert_funktionsfaehig(self, client, host_token, monkeypatch):
        from data.elevation import provider

        async def _fake_elevation_difference(*args, **kwargs):
            return 0.0, False

        monkeypatch.setattr(provider, "elevation_difference", _fake_elevation_difference)

        payload = {
            "observer_lat": 52.3975, "observer_lon": 13.0976,
            "subject_lat": 52.4158, "subject_lon": 13.0688,
            "subject_name": "Unbenannt", "subject_height_m": 15.0,
            "subject_width_m": 10.0, "days": 1, "save": False,
        }
        r = client.post("/preview-alignment", json=payload)
        assert r.status_code == 200, r.text
