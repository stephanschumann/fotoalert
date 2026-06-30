"""
US-109: Tests für Goldene Wolken & Himmelsröte als eigene Feed-Events.

Abgedeckte Akzeptanzkriterien:
  AK-1:  GOLDEN_CLOUDS erscheint bei gcs >= 0.70 + Azimut-Differenz <= 30°
  AK-4:  RED_SKY erscheint bei gcs >= 0.80 + cl+cm >= 60 %
  AK-6:  Kein Event bei gcs < Schwellwert
  AK-7:  Kein GOLDEN_CLOUDS bei Differenz > 90°
  AK-10: GOLDEN_CLOUDS verdrängt Goldene-Stunde-Original
  AK-12: Kein GOLDEN_CLOUDS wenn subject_azimuth fehlt
"""

import sys
import os
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculations.weather import (
    should_generate_golden_clouds_event,
    should_generate_red_sky_event,
    calculate_golden_cloud_score,
)

# ---------------------------------------------------------------------------
# should_generate_golden_clouds_event
# ---------------------------------------------------------------------------

def test_golden_clouds_ausgeloest():
    """AK-1: gcs=0.82, Sonne und Motiv auf gleicher Seite (13° Differenz) → True."""
    assert should_generate_golden_clouds_event(0.82, sun_azimuth=278, subject_azimuth=265) is True


def test_golden_clouds_zu_niedriger_score():
    """AK-6: gcs=0.65 < 0.70 → kein GOLDEN_CLOUDS."""
    assert should_generate_golden_clouds_event(0.65, sun_azimuth=278, subject_azimuth=265) is False


def test_golden_clouds_genau_schwellwert():
    """AK-1: gcs=0.70 genau am Schwellwert → True."""
    assert should_generate_golden_clouds_event(0.70, sun_azimuth=100, subject_azimuth=100) is True


def test_golden_clouds_azimut_grenzwert_30():
    """AK-1: Differenz exakt 30° → True (inklusiv)."""
    assert should_generate_golden_clouds_event(0.80, sun_azimuth=100, subject_azimuth=70) is True


def test_golden_clouds_azimut_zu_gross():
    """AK-7: Differenz 31° > 30° → False."""
    assert should_generate_golden_clouds_event(0.80, sun_azimuth=100, subject_azimuth=69) is False


def test_golden_clouds_sonne_gegenseite():
    """AK-7: Sonne im Osten (278°), Motiv im Westen (90°) → Differenz 188° → False."""
    assert should_generate_golden_clouds_event(0.82, sun_azimuth=278, subject_azimuth=90) is False


def test_golden_clouds_azimut_wrap_around():
    """Azimut-Wraparound: 355° vs 5° → Differenz 10° → True."""
    assert should_generate_golden_clouds_event(0.80, sun_azimuth=355, subject_azimuth=5) is True


def test_golden_clouds_azimut_wrap_um_180():
    """Azimut 0° vs 200° → Differenz 160° → False."""
    assert should_generate_golden_clouds_event(0.80, sun_azimuth=0, subject_azimuth=200) is False


# ---------------------------------------------------------------------------
# should_generate_red_sky_event
# ---------------------------------------------------------------------------

def test_red_sky_ausgeloest():
    """AK-4: gcs=0.85, cl=40, cm=35 (Summe 75 >= 60) → True."""
    assert should_generate_red_sky_event(0.85, cl=40, cm=35) is True


def test_red_sky_zu_niedriger_score():
    """AK-6: gcs=0.75 < 0.80 → kein RED_SKY."""
    assert should_generate_red_sky_event(0.75, cl=40, cm=35) is False


def test_red_sky_zu_wenig_tiefe_wolken():
    """AK-4: gcs=0.85, aber cl+cm=15 < 60 → False (nur Cirrus)."""
    assert should_generate_red_sky_event(0.85, cl=5, cm=10) is False


def test_red_sky_genau_schwellwert_beides():
    """AK-4: gcs=0.80 genau, cl+cm=60 genau → True."""
    assert should_generate_red_sky_event(0.80, cl=30, cm=30) is True


# ---------------------------------------------------------------------------
# Integration: _generate_cloud_mood_events
# ---------------------------------------------------------------------------

def _make_golden_event(event_type="Goldene Stunde Abend", gcs=0.82, sun_azimuth=278,
                       subject_azimuth=265, cl=40, cm=35, ch=10):
    """Minimaler Event-Dict mit Wetter-Daten analog zu _apply_weather_to_event output."""
    return {
        "id": "test-event-1",
        "event_type": event_type,
        "title": event_type,
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
        "golden_cloud_score": gcs,
        "sunset_azimuth": sun_azimuth,
        "sunrise_azimuth": None,
        "subject_azimuth": subject_azimuth,
        "composition_analysis": None,
        "moon_phase": None,
        "moon_illumination_pct": None,
        "weather_description": "Teilweise bewölkt",
        "weather_details": {
            "temperature_c": 18.0,
            "precipitation_prob_pct": 10,
            "precipitation_mm": 0.0,
            "cloud_cover_pct": cl + cm + ch,
            "cloud_cover_low_pct": cl,
            "cloud_cover_mid_pct": cm,
            "cloud_cover_high_pct": ch,
            "wind_speed_kmh": 10,
            "wind_direction_deg": 270,
            "visibility_m": 15000,
        },
    }


def test_integration_golden_clouds_erzeugt():
    """AK-1: gcs=0.82, Azimut-Differenz 13° → GOLDEN_CLOUDS-Event wird erzeugt."""
    # Import des zu testenden Moduls (erfordert sys.path von oben)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event()]
    neue, entfernte = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Goldene Wolken" in typen, f"GOLDEN_CLOUDS fehlt. Erzeugte Typen: {typen}"


def test_integration_golden_clouds_verdraengt_original(monkeypatch):
    """AK-10: GOLDEN_CLOUDS → Original-Goldene-Stunde-ID in zu_entfernende_ids."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event()]
    neue, entfernte = _generate_cloud_mood_events(feed)
    assert "test-event-1" in entfernte, "Original-Event-ID nicht in zu_entfernenden_ids"


def test_integration_red_sky_erzeugt():
    """AK-4: gcs=0.85, cl=40, cm=35 → Himmelsröte-Event wird erzeugt."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.85, cl=40, cm=35)]
    neue, _ = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" in typen, f"Himmelsröte fehlt. Erzeugte Typen: {typen}"


def test_integration_kein_event_unter_schwellwert():
    """AK-6: gcs=0.50 → keine neuen Events."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.50)]
    neue, entfernte = _generate_cloud_mood_events(feed)
    assert neue == [], f"Unerwartete Events: {[e['event_type'] for e in neue]}"
    assert entfernte == set()


def test_integration_kein_golden_clouds_ohne_subject_azimuth():
    """AK-12: subject_azimuth=None → kein GOLDEN_CLOUDS (aber ggf. RED_SKY wenn gcs >= 0.80)."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from main import _generate_cloud_mood_events

    event = _make_golden_event(gcs=0.82, cl=5, cm=10)  # cl+cm<60 → kein RED_SKY
    event["subject_azimuth"] = None
    feed = [event]
    neue, _ = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Goldene Wolken" not in typen, "GOLDEN_CLOUDS darf ohne subject_azimuth nicht erzeugt werden"


def test_integration_kein_event_ohne_wetter():
    """AK-13: weather_status != 'ok' → keine neuen Events."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from main import _generate_cloud_mood_events

    event = _make_golden_event(gcs=0.82)
    event["weather_status"] = "none"
    feed = [event]
    neue, _ = _generate_cloud_mood_events(feed)
    assert neue == [], "Kein Event darf ohne Wetter-Overlay erzeugt werden"


def test_integration_goldene_wolken_id_unique():
    """Zwei Events gleicher Location: verschiedene IDs für GOLDEN_CLOUDS."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from main import _generate_cloud_mood_events

    e1 = _make_golden_event()
    e2 = copy.deepcopy(e1)
    e2["id"] = "test-event-2"
    feed = [e1, e2]
    neue, _ = _generate_cloud_mood_events(feed)
    gc_ids = [e["id"] for e in neue if e["event_type"] == "Goldene Wolken"]
    assert len(gc_ids) == len(set(gc_ids)), "GOLDEN_CLOUDS-IDs müssen eindeutig sein"
