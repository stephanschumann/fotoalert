"""
US-132: Tests für "Rote Wolken" (RED_CLOUDS) — rötliches Nachglühen hoher Wolken in
Sonnenrichtung, wenn die Sonne bereits unter dem Horizont steht (Blaue-Stunde-Fenster,
Sonnenhöhe -4° bis -6°), zu unterscheiden von "Goldene Wolken" (GOLDEN_CLOUDS, US-109,
Sonne über Horizont) und "Himmelsröte" (RED_SKY, US-109/US-113, Antisolarpunkt-Richtung).

Namenskonvention (von Stephan festgelegt, 2026-07-13, siehe BACKLOG.md US-132):
"Rote Wolken" = Wolken in Sonnenrichtung (dieses Ticket). "Himmelsröte" = Himmel gegenüber
Motiv/Sonne, Antisolarpunkt (RED_SKY, US-113) — NICHT verwechseln.

Implementierung (2026-07-13, nach Abschluss TASK-74): `should_generate_red_clouds_event()`
in backend/calculations/weather.py, dritter Zweig in `_generate_cloud_mood_events()`
(backend/main.py) sowie Sonnenazimut-Ergänzung für Blaue Stunde Morgen+Abend in
backend/calculations/opportunity.py (Pre-Mortem Szenario 2).

Abgedeckte Akzeptanzkriterien (siehe BACKLOG.md US-132):
  AK-1: Sonne unter Horizont + genug hohe Wolken + Sonnenrichtung + tiefe Wolken verstellen
        die Sicht nicht -> "Rote Wolken"-Event wird erzeugt.
  AK-2: Sonne über Horizont (Goldene Stunde) -> kein "Rote Wolken"-Event, unabhängig von den
        Wolkenwerten (Regression/Abgrenzung zu GOLDEN_CLOUDS).
  AK-5 (Edge Case): Tiefe Wolken verstellen die Sicht komplett -> kein "Rote Wolken"-Event,
        selbst bei ausreichend hohen Wolken.
  AK-6 (Edge Case): Motiv liegt nicht in Sonnenrichtung (z. B. Antisolarpunkt) -> kein
        "Rote Wolken"-Event.
  AK-7 (Regression): GOLDEN_CLOUDS/RED_SKY bleiben von der neuen Prüfung unberührt.
  AK-8 (Edge Case): Kein Wetter-Overlay ("Blaue Stunde"-Event ohne weather_status == "ok")
        -> kein "Rote Wolken"-Event.
  AK-9: Das Phänomen wird auch vor Sonnenaufgang erkannt ("Blaue Stunde Morgen"), symmetrisch
        zum Abend-Fall — sowohl auf Ebene der Event-Generierung (_generate_cloud_mood_events)
        als auch auf Ebene der Astronomie-Berechnung (opportunity.py liefert celestial_azimuth/
        celestial_altitude für beide Blaue-Stunde-Blöcke, Pre-Mortem Szenario 2).

AK-3/AK-4/AK-10/AK-11/AK-12 (Erklärungstexte, Filter-Chip, Icon/Farbe im Frontend) sind NICHT
Teil dieser Testdatei — separater Frontend-Scope (web/index.html), siehe BACKLOG.md US-132
Architektur-Analyse Punkt 5.
"""

import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ---------------------------------------------------------------------------
# should_generate_red_clouds_event — reine Prüf-Funktion (noch zu implementieren,
# siehe BACKLOG.md US-132 Architektur-Analyse: backend/calculations/weather.py)
# ---------------------------------------------------------------------------

def _import_should_generate_red_clouds_event():
    """Lazy-Import mit sprechendem Fehler, solange die Funktion noch nicht existiert."""
    try:
        from calculations.weather import should_generate_red_clouds_event
    except ImportError as exc:
        pytest.skip(
            f"should_generate_red_clouds_event() noch nicht implementiert (US-132 Analysephase, "
            f"Test-First-Grundgerüst) — {exc}"
        )
    return should_generate_red_clouds_event


def test_red_clouds_ausgeloest_sonne_unter_horizont_genug_hohe_wolken_sonnenrichtung():
    """AK-1: sun_altitude=-5 (unter Horizont), ch=45 (>= Schwelle 20), cl=10 (< Deckel 30),
    sun_azimuth=280, subject_azimuth=275 (Differenz 5° <= 30°) -> True."""
    should_generate_red_clouds_event = _import_should_generate_red_clouds_event()
    assert should_generate_red_clouds_event(
        sun_altitude=-5, ch=45, cl=10, sun_azimuth=280, subject_azimuth=275
    ) is True


def test_red_clouds_kein_event_sonne_ueber_horizont():
    """AK-2: identische Wolken-/Azimutwerte wie Rule 1, aber sun_altitude=+3 (Goldene Stunde,
    Sonne über Horizont) -> False. Das ist der GOLDEN_CLOUDS-Fall, nicht RED_CLOUDS."""
    should_generate_red_clouds_event = _import_should_generate_red_clouds_event()
    assert should_generate_red_clouds_event(
        sun_altitude=3, ch=45, cl=10, sun_azimuth=280, subject_azimuth=275
    ) is False


def test_red_clouds_kein_event_ausserhalb_sonnenrichtung():
    """AK-6: sun_altitude=-5, ch=45, cl=10 (Wolkenbedingung erfuellt), aber subject_azimuth=100
    liegt 180° von sun_azimuth=280 entfernt (weit ausserhalb der 30°-Toleranz) -> False."""
    should_generate_red_clouds_event = _import_should_generate_red_clouds_event()
    assert should_generate_red_clouds_event(
        sun_altitude=-5, ch=45, cl=10, sun_azimuth=280, subject_azimuth=100
    ) is False


def test_red_clouds_kein_event_tiefe_wolken_verstellen_sicht():
    """AK-5 (Edge Case): sun_altitude=-5, ch=50 (Schwelle erfuellt), aber cl=90 (dicht bewoelkt,
    >= Deckel 30) -> False, obwohl genug hohe Wolken vorhanden waeren."""
    should_generate_red_clouds_event = _import_should_generate_red_clouds_event()
    assert should_generate_red_clouds_event(
        sun_altitude=-5, ch=50, cl=90, sun_azimuth=280, subject_azimuth=280
    ) is False


def test_red_clouds_kein_event_zu_wenig_hohe_wolken():
    """Grenzfall: sun_altitude=-5, ch=15 (< Schwelle 20), cl=5, Sonnenrichtung passt -> False."""
    should_generate_red_clouds_event = _import_should_generate_red_clouds_event()
    assert should_generate_red_clouds_event(
        sun_altitude=-5, ch=15, cl=5, sun_azimuth=280, subject_azimuth=280
    ) is False


def test_red_clouds_grenzwert_azimut_differenz_exakt_30_grad():
    """Edge Case (inklusiver Grenzwert, analog GOLDEN_CLOUDS/RED_SKY-Pattern): Differenz exakt
    30° -> weiterhin True."""
    should_generate_red_clouds_event = _import_should_generate_red_clouds_event()
    assert should_generate_red_clouds_event(
        sun_altitude=-5, ch=45, cl=10, sun_azimuth=280, subject_azimuth=310
    ) is True


def test_red_clouds_grenzwert_sonnenhoehe_exakt_null():
    """Edge Case: sun_altitude=0 (exakt am Horizont) -> per Definition ("unter dem Horizont" =
    negativ) kein RED_CLOUDS -> False."""
    should_generate_red_clouds_event = _import_should_generate_red_clouds_event()
    assert should_generate_red_clouds_event(
        sun_altitude=0, ch=45, cl=10, sun_azimuth=280, subject_azimuth=280
    ) is False


# ---------------------------------------------------------------------------
# Integration: _generate_cloud_mood_events() — dritter Zweig fuer "Blaue Stunde"
# (siehe BACKLOG.md US-132 Architektur-Analyse: backend/main.py)
# ---------------------------------------------------------------------------

def _make_blue_hour_event(sun_altitude=-5, sun_azimuth=280, subject_azimuth=280,
                           cl=10, cm=20, ch=45, weather_status="ok"):
    """Minimaler Event-Dict analog zu _apply_weather_to_event()-Output fuer ein
    'Blaue Stunde'-Event — inkl. celestial_azimuth/celestial_altitude, die laut
    Pre-Mortem Szenario 2 erst noch in opportunity.py ergaenzt werden muessen, damit
    dieses Feld ueberhaupt real befuellt wird (hier synthetisch fuer den Test gesetzt)."""
    return {
        "id": "test-blue-hour-1",
        "event_type": "Blaue Stunde",
        "title": "Blaue Stunde",
        "description": "Test",
        "location_id": "loc-1",
        "location_name": "Test Location",
        "observer_lat": 52.5,
        "observer_lon": 13.4,
        "subject_lat": 52.51,
        "subject_lon": 13.41,
        "shoot_time": "2026-07-01T19:30:00+00:00",
        "shoot_window_start": "2026-07-01T19:20:00+00:00",
        "shoot_window_end": "2026-07-01T19:45:00+00:00",
        "astronomy_score": 0.75,
        "weather_score": 0.70,
        "overall_score": 0.72,
        "location_score": 0.90,
        "alert_priority": 1,
        "weather_status": weather_status,
        "golden_cloud_score": None,  # Pre-Mortem Szenario 3: fuer "Blaue Stunde" bislang None
        "celestial_azimuth": sun_azimuth,
        "celestial_altitude": sun_altitude,
        "subject_azimuth": subject_azimuth,
        "composition_analysis": None,
        "moon_phase": None,
        "moon_illumination_pct": None,
        "weather_description": "Teilweise bewölkt",
        "weather_details": {
            "temperature_c": 17.0,
            "precipitation_prob_pct": 5,
            "precipitation_mm": 0.0,
            "cloud_cover_pct": cl + cm + ch,
            "cloud_cover_low_pct": cl,
            "cloud_cover_mid_pct": cm,
            "cloud_cover_high_pct": ch,
            "wind_speed_kmh": 8,
            "wind_direction_deg": 260,
            "visibility_m": 18000,
        },
    }


def _import_generate_cloud_mood_events():
    from main import _generate_cloud_mood_events
    return _generate_cloud_mood_events


def test_integration_rote_wolken_erzeugt():
    """AK-1: Blaue-Stunde-Event (Abend) mit passender Wetterlage -> 'Rote Wolken'-Event
    wird erzeugt."""
    _generate_cloud_mood_events = _import_generate_cloud_mood_events()

    feed = [_make_blue_hour_event()]
    neue, _entfernte = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Rote Wolken" in typen, f"Erwartetes 'Rote Wolken'-Event fehlt: {typen}"


def test_integration_kein_rote_wolken_ohne_wetter():
    """AK-8: weather_status != 'ok' -> kein 'Rote Wolken'-Event."""
    _generate_cloud_mood_events = _import_generate_cloud_mood_events()

    feed = [_make_blue_hour_event(weather_status="none")]
    neue, _entfernte = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Rote Wolken" not in typen, "Kein Event darf ohne Wetter-Overlay erzeugt werden"


def test_integration_golden_clouds_und_red_sky_unveraendert_regression():
    """AK-7 (Regression): Ein bestehendes Goldene-Stunde-Event mit GOLDEN_CLOUDS-Bedingungen
    erzeugt weiterhin genau 'Goldene Wolken', unabhaengig von der neuen RED_CLOUDS-Logik."""
    _generate_cloud_mood_events = _import_generate_cloud_mood_events()

    golden_event = {
        "id": "test-golden-1",
        "event_type": "Goldene Stunde Abend",
        "title": "Goldene Stunde Abend",
        "description": "Test",
        "location_id": "loc-1",
        "location_name": "Test Location",
        "observer_lat": 52.5,
        "observer_lon": 13.4,
        "subject_lat": 52.51,
        "subject_lon": 13.41,
        "shoot_time": "2026-07-01T18:00:00+00:00",
        "shoot_window_start": "2026-07-01T17:45:00+00:00",
        "shoot_window_end": "2026-07-01T18:15:00+00:00",
        "astronomy_score": 0.85,
        "weather_score": 0.70,
        "overall_score": 0.79,
        "location_score": 0.90,
        "alert_priority": 1,
        "weather_status": "ok",
        "golden_cloud_score": 0.82,
        # US-131-Nachtrag (2026-07-13, Option B): _build_golden_clouds_event() liest
        # seither golden_cloud_score_sun_dir statt des geteilten golden_cloud_score.
        "golden_cloud_score_sun_dir": 0.82,
        "cl_sun_dir": 40,
        "cm_sun_dir": 35,
        "golden_cloud_score_antisolar_dir": 0.82,
        "cl_antisolar_dir": 40,
        "cm_antisolar_dir": 35,
        "sunset_azimuth": 278,
        "sunrise_azimuth": None,
        "subject_azimuth": 265,
        "composition_analysis": None,
        "moon_phase": None,
        "moon_illumination_pct": None,
        "weather_description": "Teilweise bewölkt",
        "weather_details": {
            "temperature_c": 18.0,
            "precipitation_prob_pct": 10,
            "precipitation_mm": 0.0,
            "cloud_cover_pct": 85,
            "cloud_cover_low_pct": 40,
            "cloud_cover_mid_pct": 35,
            "cloud_cover_high_pct": 10,
            "wind_speed_kmh": 10,
            "wind_direction_deg": 270,
            "visibility_m": 15000,
        },
    }
    feed = [golden_event]
    neue, entfernte = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Goldene Wolken" in typen, f"GOLDEN_CLOUDS-Regression: {typen}"
    assert "Rote Wolken" not in typen, "RED_CLOUDS darf bei einem Goldene-Stunde-Event nicht erscheinen"


def test_integration_rote_wolken_id_praefix_rc():
    """Konvention (siehe BACKLOG.md US-132, Vorab-Verifikation): neue Event-IDs sollen das
    Praefix 'rc_' tragen, analog 'gc_'/'rs_'."""
    _generate_cloud_mood_events = _import_generate_cloud_mood_events()

    feed = [_make_blue_hour_event()]
    neue, _entfernte = _generate_cloud_mood_events(feed)
    rote_wolken_events = [e for e in neue if e["event_type"] == "Rote Wolken"]
    assert rote_wolken_events, "Kein 'Rote Wolken'-Event erzeugt"
    for e in rote_wolken_events:
        assert e["id"].startswith("rc_"), f"Erwartetes ID-Praefix 'rc_', bekommen: {e['id']}"


def test_integration_rote_wolken_morgen_erzeugt():
    """AK-9 (beide Richtungen, Stephan 2026-07-13): 'Blaue Stunde Morgen'-Event mit
    passender Wetterlage -> 'Rote Wolken'-Event wird auch vor Sonnenaufgang erzeugt,
    symmetrisch zum Abend-Fall (test_integration_rote_wolken_erzeugt)."""
    _generate_cloud_mood_events = _import_generate_cloud_mood_events()

    morgen_event = _make_blue_hour_event()
    morgen_event["event_type"] = "Blaue Stunde Morgen"
    morgen_event["title"] = "Blaue Stunde Morgen"
    morgen_event["id"] = "test-blue-hour-morning-1"

    feed = [morgen_event]
    neue, _entfernte = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Rote Wolken" in typen, f"AK-9: 'Rote Wolken' fehlt fuer Blaue Stunde Morgen: {typen}"


def test_integration_kein_rote_wolken_ohne_sonnenazimut():
    """Pre-Mortem Szenario 2 (Regressions-Falle): Fehlt celestial_azimuth/celestial_altitude
    (z.B. weil die opportunity.py-Ergaenzung ausbliebe), darf kein 'Rote Wolken'-Event
    entstehen -- kein Fehler, aber auch kein falscher Alarm."""
    _generate_cloud_mood_events = _import_generate_cloud_mood_events()

    event_ohne_sonnenazimut = _make_blue_hour_event()
    event_ohne_sonnenazimut["celestial_azimuth"] = None
    event_ohne_sonnenazimut["celestial_altitude"] = None

    feed = [event_ohne_sonnenazimut]
    neue, _entfernte = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Rote Wolken" not in typen, (
        "Ohne Sonnenazimut/-hoehe darf kein 'Rote Wolken'-Event entstehen "
        "(Pre-Mortem Szenario 2)"
    )


# ---------------------------------------------------------------------------
# Astronomie-Ebene (opportunity.py): Pre-Mortem Szenario 2 — Blaue-Stunde-Events
# (Morgen + Abend) muessen aus der echten Astronomie-Berechnung heraus einen
# Sonnenazimut/-hoehe mitbekommen, sonst bleibt die Richtungspruefung oben wirkungslos,
# ohne dass ein Fehler sichtbar wird.
# ---------------------------------------------------------------------------

def _make_test_location():
    """Eigene, UUID-basierte Test-Location (siehe Memory feedback_fotoalert_ongoing_test_coverage/
    Test-Fixture-Konvention) -- rein In-Memory-Dataclass, keine DB-Mutation."""
    import uuid

    from data.locations import PhotoLocation, LocationCategory

    return PhotoLocation(
        id=f"test-us132-{uuid.uuid4().hex[:8]}",
        name="US-132 Testlocation",
        description="Nur fuer Tests",
        category=LocationCategory.SKYLINE,
        observer_lat=52.5163,
        observer_lon=13.3777,
        subject_lat=52.5200,
        subject_lon=13.4050,
        subject_name="Testmotiv",
    )


@pytest.mark.parametrize("target_date_offset", [10, 40])
def test_opportunity_blaue_stunde_hat_sonnenazimut(target_date_offset):
    """Pre-Mortem Szenario 2: ruft find_opportunities() (echte Astronomie, offline/
    lokale Ephemeride, kein Netzwerk) fuer ein paar Tage in der Zukunft auf und prueft:
    falls ein 'Blaue Stunde'- oder 'Blaue Stunde Morgen'-Event erzeugt wird, hat es ein
    gesetztes celestial_azimuth UND celestial_altitude (nicht None) -- sonst waere die
    RED_CLOUDS-Richtungspruefung fuer jedes reale Event wirkungslos."""
    import asyncio
    from datetime import date, timedelta

    from calculations.opportunity import find_opportunities

    location = _make_test_location()
    target_date = date.today() + timedelta(days=target_date_offset)

    opportunities = asyncio.run(
        find_opportunities(location, target_date, forecast=None, min_score=0.0, astronomy_only=True)
    )
    blue_hour_events = [
        o for o in opportunities if o.event_type in ("Blaue Stunde", "Blaue Stunde Morgen")
    ]
    assert blue_hour_events, (
        f"Erwartete mindestens ein Blaue-Stunde-Event fuer {target_date}, keins gefunden "
        f"(min_score=0.0 sollte das ausschliessen)"
    )
    for o in blue_hour_events:
        assert o.celestial_azimuth is not None, (
            f"{o.event_type} am {target_date}: celestial_azimuth fehlt (Pre-Mortem Szenario 2)"
        )
        assert o.celestial_altitude is not None, (
            f"{o.event_type} am {target_date}: celestial_altitude fehlt (Pre-Mortem Szenario 2)"
        )
        assert o.celestial_altitude < 0, (
            f"{o.event_type} am {target_date}: Sonnenhoehe {o.celestial_altitude} sollte "
            f"unter dem Horizont liegen (Blaue Stunde per Definition)"
        )
