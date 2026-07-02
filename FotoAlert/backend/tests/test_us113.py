"""
US-113: Tests für Himmelsröte-Richtungsfilter (RED_SKY nur bei Wolken in Sichtachsen-Richtung).

Abgedeckte Akzeptanzkriterien:
  AK-1: RED_SKY erscheint weiterhin, wenn Wolkenbedingung erfuellt UND Azimut-Differenz
        zum GEGENPUNKT der Sonne <= 30°.
  AK-2: RED_SKY entfaellt, wenn Wolkenbedingung erfuellt, aber Azimut-Differenz zum
        Gegenpunkt > 30° (inkl. explizitem Test fuer den urspruenglich falschen Fall:
        Motiv nahe der Sonne selbst statt am Gegenpunkt).
  AK-3: RED_SKY entfaellt ohne subject_azimuth (kein Richtungsvergleich moeglich).
  AK-6: GOLDEN_CLOUDS bleibt unveraendert (Regression, vergleicht weiterhin direkt
        gegen die Sonne, NICHT gegen den Gegenpunkt).
  AK-8: Edge Case - Azimut-Differenz zum Gegenpunkt exakt 30,0° -> weiterhin True
        (inklusiver Grenzwert).
  AK-9: Kein Wetter-Overlay -> weiterhin kein RED_SKY (unveraendert zu US-109, ueber
        Integrationstest).

US-113-Korrektur (2026-07-02, fachlicher Analysefehler behoben):
Himmelsröte (Gegendämmerung, "Belt of Venus") entsteht am GEGENPUNKT der Sonne
(Antisolarpunkt = sun_azimuth + 180°), NICHT am Sonnenazimut selbst wie bei
GOLDEN_CLOUDS. Alle Testwerte unten sind gegen den Gegenpunkt gerechnet, nicht mehr
gegen den rohen Sonnenazimut. Quellen: siehe BACKLOG.md US-113 / weather.py-Docstring.
"""

import sys
import os
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculations.weather import (
    should_generate_golden_clouds_event,
    should_generate_red_sky_event,
)

# ---------------------------------------------------------------------------
# should_generate_red_sky_event — neue Signatur mit Azimut-Parametern,
# Vergleich gegen den Gegenpunkt der Sonne (Antisolarpunkt)
# ---------------------------------------------------------------------------

def test_red_sky_ausgeloest_in_sichtachse():
    """AK-1: gcs=0.85, cl=40, cm=35 (Summe 75 >= 60).
    sun_azimuth=278 -> Gegenpunkt = (278+180)%360 = 98. subject_azimuth=85 ->
    Differenz zum Gegenpunkt = |98-85| = 13° <= 30° -> True."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=278, subject_azimuth=85
    ) is True


def test_red_sky_ausserhalb_sichtachse():
    """AK-2: gleiche Wolkenbedingung, aber Motiv liegt nicht am Gegenpunkt der Sonne.
    sun_azimuth=278 -> Gegenpunkt = 98. subject_azimuth=265 -> Differenz zum
    Gegenpunkt = |98-265| = 167° > 30° -> False (neues Verhalten)."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=278, subject_azimuth=265
    ) is False


def test_red_sky_verwechslungsfall_motiv_bei_sonne_statt_gegenpunkt():
    """Deckt die urspruengliche Verwechslungsgefahr ab: subject_azimuth liegt nahe
    dem SONNENAZIMUT selbst (wie bei GOLDEN_CLOUDS), NICHT nahe dessen Gegenpunkt.
    sun_azimuth=320, subject_azimuth=305 -> Differenz zur Sonne waere nur 15°
    (faelschlich 'True' bei der alten, fehlerhaften Logik), aber Gegenpunkt von 320°
    ist 140° -> Differenz zum Gegenpunkt = |140-305| = 165° > 30° -> muss False sein."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=320, subject_azimuth=305
    ) is False


def test_red_sky_screenshot_beispiel_gegenpunkt_direkter_treffer():
    """Screenshot-Beispiel aus der Live-Test-Korrektur: sun_azimuth=320, subject_azimuth=140.
    Gegenpunkt von 320° ist (320+180)%360 = 140° -> direkter Treffer, Differenz = 0° -> True."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=320, subject_azimuth=140
    ) is True


def test_red_sky_ohne_subject_azimuth():
    """AK-3: subject_azimuth=None -> kein Richtungsvergleich moeglich -> False."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=278, subject_azimuth=None
    ) is False


def test_red_sky_ohne_sun_azimuth():
    """Analog AK-3: sun_azimuth=None -> ebenfalls kein Richtungsvergleich moeglich -> False."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=None, subject_azimuth=98
    ) is False


def test_red_sky_azimut_grenzwert_30():
    """AK-8: Differenz zum Gegenpunkt exakt 30,0° -> True (inklusiver Grenzwert).
    sun_azimuth=100 -> Gegenpunkt = 280. subject_azimuth=250 -> Differenz = 30° -> True."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=100, subject_azimuth=250
    ) is True


def test_red_sky_azimut_knapp_ueber_grenzwert():
    """Differenz zum Gegenpunkt 31° > 30° -> False.
    sun_azimuth=100 -> Gegenpunkt = 280. subject_azimuth=249 -> Differenz = 31° -> False."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=100, subject_azimuth=249
    ) is False


def test_red_sky_zu_niedriger_score_trotz_azimut_ok():
    """Regression (AK-6 sinngemaess fuer RED_SKY selbst): gcs=0.75 < 0.80 -> False,
    unabhaengig vom Azimut. sun_azimuth=100 -> Gegenpunkt = 280 = subject_azimuth
    (perfekter Treffer), aber Score-Schwelle wird trotzdem nicht erreicht."""
    assert should_generate_red_sky_event(
        0.75, cl=40, cm=35, sun_azimuth=100, subject_azimuth=280
    ) is False


def test_red_sky_zu_wenig_wolken_trotz_azimut_ok():
    """Wolkenbedingung bleibt bestehen: cl+cm=15 < 60 -> False, auch bei perfektem
    Azimut-Treffer auf den Gegenpunkt (sun_azimuth=100 -> Gegenpunkt=280=subject_azimuth)."""
    assert should_generate_red_sky_event(
        0.85, cl=5, cm=10, sun_azimuth=100, subject_azimuth=280
    ) is False


def test_red_sky_azimut_wrap_around():
    """Azimut-Wraparound: sun_azimuth=175 -> Gegenpunkt = (175+180)%360 = 355.
    subject_azimuth=5 -> Differenz = |355-5| = 350, > 180 -> 360-350 = 10° -> True.
    Deckt denselben Grenzuebergang (Werte nahe 0°/360°) ab wie zuvor."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=175, subject_azimuth=5
    ) is True


# ---------------------------------------------------------------------------
# Regression: GOLDEN_CLOUDS unveraendert (AK-6) — vergleicht weiterhin direkt
# gegen die Sonne, NICHT gegen deren Gegenpunkt (US-113 betrifft nur RED_SKY).
# ---------------------------------------------------------------------------

def test_golden_clouds_unveraendert_regression():
    """AK-6: GOLDEN_CLOUDS-Logik bleibt unberuehrt von der RED_SKY-Korrektur."""
    assert should_generate_golden_clouds_event(0.82, sun_azimuth=278, subject_azimuth=265) is True
    assert should_generate_golden_clouds_event(0.65, sun_azimuth=278, subject_azimuth=265) is False


# ---------------------------------------------------------------------------
# Integration: _generate_cloud_mood_events
# ---------------------------------------------------------------------------

def _make_golden_event(event_type="Goldene Stunde Abend", gcs=0.82, sun_azimuth=278,
                       subject_azimuth=265, cl=40, cm=35, ch=10, weather_status="ok"):
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
        "weather_status": weather_status,
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


def test_integration_red_sky_erzeugt_in_sichtachse():
    """AK-1: gcs=0.85, cl=40, cm=35. sun_azimuth=278 -> Gegenpunkt=98,
    subject_azimuth=85 -> Differenz 13° -> Himmelsröte-Event wird erzeugt."""
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.85, cl=40, cm=35, sun_azimuth=278, subject_azimuth=85)]
    neue, _ = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" in typen, f"Himmelsröte fehlt. Erzeugte Typen: {typen}"


def test_integration_red_sky_entfaellt_ausserhalb_sichtachse():
    """AK-2: Wolkenbedingung erfuellt, aber Motiv liegt nicht am Gegenpunkt der Sonne
    (sun_azimuth=278 -> Gegenpunkt=98, subject_azimuth=265 -> Differenz 167°)
    -> keine Himmelsröte-Karte."""
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.85, cl=40, cm=35, sun_azimuth=278, subject_azimuth=265)]
    neue, _ = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" not in typen, f"Himmelsröte haette nicht erscheinen duerfen. Erzeugte Typen: {typen}"


def test_integration_red_sky_entfaellt_ohne_subject_azimuth():
    """AK-3: subject_azimuth=None -> kein Richtungsvergleich moeglich -> keine Himmelsröte-Karte."""
    from main import _generate_cloud_mood_events

    event = _make_golden_event(gcs=0.85, cl=40, cm=35)
    event["subject_azimuth"] = None
    feed = [event]
    neue, _ = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" not in typen, "Himmelsröte darf ohne subject_azimuth nicht erzeugt werden"


def test_integration_golden_clouds_weiterhin_unabhaengig_regression():
    """AK-6/AK-7 (Regression): GOLDEN_CLOUDS-Erzeugung bleibt unberuehrt von der RED_SKY-Korrektur."""
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.82, sun_azimuth=278, subject_azimuth=265, cl=5, cm=10)]
    neue, entfernte = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Goldene Wolken" in typen, f"GOLDEN_CLOUDS fehlt (Regression). Erzeugte Typen: {typen}"
    assert "test-event-1" in entfernte


def test_integration_red_sky_kein_event_ohne_wetter():
    """AK-9: weather_status != 'ok' -> keine neuen Events (unveraendert zu US-109)."""
    from main import _generate_cloud_mood_events

    event = _make_golden_event(gcs=0.85, cl=40, cm=35, sun_azimuth=278, subject_azimuth=85, weather_status="none")
    feed = [event]
    neue, _ = _generate_cloud_mood_events(feed)
    assert neue == [], "Kein Event darf ohne Wetter-Overlay erzeugt werden"
