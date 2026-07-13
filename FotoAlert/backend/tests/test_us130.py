"""
US-130: Tests für Himmelsröte-Erkennung mit Aerosol-/Dunst-Signal (ODER-Verknüpfung,
Option B) — RED_SKY wird jetzt zusätzlich ausgelöst, wenn statt ausreichender
Wolkenbedeckung ein hoher Aerosol-/Dunst-Wert (aerosol_optical_depth) in
Antisolar-Richtung vorliegt.

Abgedeckte Akzeptanzkriterien:
  AK-1: Kein ausreichender Wolkenanteil, aber hoher Dunst-/Aerosolwert in
        Antisolar-Richtung -> RED_SKY erscheint trotzdem (Dunst-Zweig).
  AK-2: Beschreibungstext benennt Dunst (nicht Wolken) als Auslöser, wenn der
        Aerosol-Zweig (nicht die Wolkenbedingung) das Event ausgelöst hat.
  AK-3 (Regression): Eine bereits heute allein durch Wolken ausgelöste
        RED_SKY-Karte erscheint weiterhin genauso (inkl. Wolken-Text), unabhängig
        vom Aerosolwert.
  AK-4 (Regression): Weder Wolken- noch Dunstbedingung erfüllt -> weiterhin keine
        RED_SKY-Karte.
  AK-5: GOLDEN_CLOUDS bleibt von der Aerosol-Erweiterung vollständig unberührt.
  AK-6 (Edge Case): Aerosol-Abruf nicht verfügbar (aerosol_optical_depth=None) ->
        Verhalten identisch zum reinen Wolken-Pfad, kein Fehler.
  AK-7 (Edge Case): Aerosolwert exakt auf dem Schwellenwert (RED_SKY_AOD_THRESHOLD)
        -> Karte erscheint (inklusiver Grenzwert, >=).

Testwerte für AK-1/AK-4 aus dem Testplan in BACKLOG.md US-130 übernommen
(gcs=0.85, cl=10, cm=5, sunset_azimuth=278, subject_azimuth=98, aod=0.45/0.12).
Azimut-Richtungslogik (Antisolarpunkt, US-113) bleibt für den Aerosol-Zweig
unverändert Pflicht — ohne gültige Sichtachse kein RED_SKY-Event, unabhängig vom
Auslöser (Wolken oder Dunst).
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculations.weather import (
    RED_SKY_AOD_THRESHOLD,
    should_generate_golden_clouds_event,
    should_generate_red_sky_event,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ---------------------------------------------------------------------------
# should_generate_red_sky_event — Aerosol-/Dunst-Zweig (US-130, Option B: ODER)
# ---------------------------------------------------------------------------

def test_red_sky_dunst_loest_aus_ohne_wolkenbedingung():
    """AK-1: gcs=0.85, cl=10, cm=5 (Summe 15 < 60, Wolkenbedingung NICHT erfuellt),
    aod=0.45 (>= 0.3 Schwelle). sunset_azimuth=278 -> Gegenpunkt=98, subject_azimuth=98
    -> Differenz 0 <= 30 -> True (Dunst-Zweig loest aus, Testplan-Werte)."""
    assert should_generate_red_sky_event(
        0.85, cl=10, cm=5, sun_azimuth=278, subject_azimuth=98,
        aerosol_optical_depth=0.45,
    ) is True


def test_red_sky_weder_wolken_noch_dunst():
    """AK-4 (Regression): cl=10, cm=5 (15 < 60) UND aod=0.12 (< 0.3) -> False,
    trotz gueltiger Sichtachse (Testplan-Werte)."""
    assert should_generate_red_sky_event(
        0.85, cl=10, cm=5, sun_azimuth=278, subject_azimuth=98,
        aerosol_optical_depth=0.12,
    ) is False


def test_red_sky_wolken_bereits_erfuellt_aerosol_aendert_nichts():
    """AK-3 (Regression): cl+cm=70 (erfuellt, wie bisher), aod=0.05 (niedrig,
    unter der Schwelle) -> weiterhin True, keine Verschlechterung durch das neue
    Kriterium (Testplan Rule 3)."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=30, sun_azimuth=278, subject_azimuth=98,
        aerosol_optical_depth=0.05,
    ) is True


def test_red_sky_wolken_bereits_erfuellt_ohne_aerosolwert():
    """AK-3 (Regression): identisch zum US-113-Verhalten, wenn aerosol_optical_depth
    gar nicht uebergeben wird (Default None) -> unveraendert True."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=278, subject_azimuth=85,
    ) is True


def test_red_sky_aerosol_abruf_nicht_verfuegbar_faellt_auf_wolken_zurueck_true():
    """AK-6 (Edge Case): aerosol_optical_depth=None (Abruf fehlgeschlagen), aber
    Wolkenbedingung erfuellt (cl+cm=75 >= 60) -> Verhalten identisch zum reinen
    Wolken-Pfad -> True, kein Fehler."""
    assert should_generate_red_sky_event(
        0.85, cl=40, cm=35, sun_azimuth=278, subject_azimuth=85,
        aerosol_optical_depth=None,
    ) is True


def test_red_sky_aerosol_abruf_nicht_verfuegbar_faellt_auf_wolken_zurueck_false():
    """AK-6 (Edge Case): aerosol_optical_depth=None UND Wolkenbedingung nicht
    erfuellt (cl+cm=15 < 60) -> False, identisch zum reinen Wolken-Pfad."""
    assert should_generate_red_sky_event(
        0.85, cl=10, cm=5, sun_azimuth=278, subject_azimuth=98,
        aerosol_optical_depth=None,
    ) is False


def test_red_sky_aerosol_genau_auf_schwellenwert():
    """AK-7 (Edge Case): aod exakt RED_SKY_AOD_THRESHOLD (0.3) -> True (inklusiver
    Grenzwert, analog zur bestehenden <=30°-Regelung bei der Richtung)."""
    assert should_generate_red_sky_event(
        0.85, cl=10, cm=5, sun_azimuth=278, subject_azimuth=98,
        aerosol_optical_depth=RED_SKY_AOD_THRESHOLD,
    ) is True


def test_red_sky_aerosol_knapp_unter_schwellenwert():
    """Ergaenzender Grenzfall zu AK-7: aod knapp unter der Schwelle -> False."""
    assert should_generate_red_sky_event(
        0.85, cl=10, cm=5, sun_azimuth=278, subject_azimuth=98,
        aerosol_optical_depth=RED_SKY_AOD_THRESHOLD - 0.01,
    ) is False


def test_red_sky_dunst_ohne_gueltige_sichtachse_bleibt_false():
    """Die Richtungsbedingung (US-113, Antisolarpunkt) gilt unveraendert auch fuer
    den Aerosol-Zweig: hoher Dunstwert, aber Motiv liegt nicht am Gegenpunkt der
    Sonne -> weiterhin False, unabhaengig vom Aerosolwert."""
    assert should_generate_red_sky_event(
        0.85, cl=10, cm=5, sun_azimuth=278, subject_azimuth=265,
        aerosol_optical_depth=0.9,
    ) is False


def test_red_sky_dunst_ohne_subject_azimuth_bleibt_false():
    """Analog AK-3 (US-113): fehlt subject_azimuth, ist kein Richtungsvergleich
    moeglich -> False, auch bei sehr hohem Aerosolwert."""
    assert should_generate_red_sky_event(
        0.85, cl=10, cm=5, sun_azimuth=278, subject_azimuth=None,
        aerosol_optical_depth=0.9,
    ) is False


def test_red_sky_zu_niedriger_score_trotz_hohem_aerosol():
    """gcs < 0.80 -> weiterhin False, unabhaengig vom Aerosolwert (Score-Schwelle
    hat Vorrang vor beiden Zweigen)."""
    assert should_generate_red_sky_event(
        0.75, cl=10, cm=5, sun_azimuth=278, subject_azimuth=98,
        aerosol_optical_depth=0.9,
    ) is False


# ---------------------------------------------------------------------------
# AK-5: GOLDEN_CLOUDS bleibt von der US-130-Erweiterung unberuehrt
# ---------------------------------------------------------------------------

def test_golden_clouds_unveraendert_durch_aerosol_erweiterung():
    """AK-5: should_generate_golden_clouds_event() kennt gar keinen
    Aerosol-Parameter -> Signatur/Verhalten unveraendert."""
    assert should_generate_golden_clouds_event(0.82, sun_azimuth=278, subject_azimuth=265) is True
    assert should_generate_golden_clouds_event(0.65, sun_azimuth=278, subject_azimuth=265) is False


# ---------------------------------------------------------------------------
# Integration: _generate_cloud_mood_events (main.py)
# ---------------------------------------------------------------------------

def _make_golden_event(event_type="Goldene Stunde Abend", gcs=0.82, sun_azimuth=278,
                        subject_azimuth=265, cl=40, cm=35, ch=10, aod=None,
                        weather_status="ok"):
    """Minimaler Event-Dict mit Wetter-Daten analog zu _apply_weather_to_event output
    (Muster aus test_us113.py, um aerosol_optical_depth in weather_details erweitert)."""
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
        "shoot_time": "2026-07-12T18:00:00+00:00",
        "shoot_window_start": "2026-07-12T17:45:00+00:00",
        "shoot_window_end": "2026-07-12T18:15:00+00:00",
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
            "aerosol_optical_depth": aod,
        },
    }


def test_integration_red_sky_ueber_dunst_ohne_wolken():
    """AK-1: cl=10, cm=5 (Wolkenbedingung nicht erfuellt), aod=0.45 (>= Schwelle),
    sun_azimuth=278 -> Gegenpunkt=98, subject_azimuth=98 -> Himmelsröte-Event wird
    trotzdem erzeugt (Testplan-Werte)."""
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.85, cl=10, cm=5, sun_azimuth=278,
                                subject_azimuth=98, aod=0.45)]
    neue, _ = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" in typen, f"Himmelsröte fehlt. Erzeugte Typen: {typen}"


def test_integration_red_sky_text_nennt_dunst_bei_aerosol_ausloeser():
    """AK-2: Beschreibungstext der ueber Dunst ausgeloesten Karte nennt „Dunst"/
    „Aerosol", NICHT die Wolken-Formulierung aus dem bisherigen Text."""
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.85, cl=10, cm=5, sun_azimuth=278,
                                subject_azimuth=98, aod=0.45)]
    neue, _ = _generate_cloud_mood_events(feed)
    red_sky_events = [e for e in neue if e["event_type"] == "Himmelsröte"]
    assert len(red_sky_events) == 1
    desc = red_sky_events[0]["description"]
    assert "Dunst" in desc or "Aerosol" in desc, f"Text nennt keinen Dunst-Auslöser: {desc}"
    assert "Wolkenschichten" not in desc, f"Text nennt faelschlich Wolken statt Dunst: {desc}"


def test_integration_red_sky_text_nennt_weiterhin_wolken_bei_wolken_ausloeser():
    """AK-3 (Regression) + Gegenprobe zu AK-2: eine ausschliesslich ueber Wolken
    ausgeloeste Karte behaelt den bisherigen Wolken-Text, auch wenn (irrelevanter,
    unter der Schwelle liegender) Aerosolwert vorhanden ist."""
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.85, cl=40, cm=35, sun_azimuth=278,
                                subject_azimuth=85, aod=0.05)]
    neue, _ = _generate_cloud_mood_events(feed)
    red_sky_events = [e for e in neue if e["event_type"] == "Himmelsröte"]
    assert len(red_sky_events) == 1
    desc = red_sky_events[0]["description"]
    assert "Wolkenschichten" in desc, f"Text haette weiterhin Wolken nennen muessen: {desc}"


def test_integration_red_sky_text_bleibt_wolken_wenn_beide_bedingungen_erfuellt():
    """Gegenprobe: sind Wolken- UND Aerosolbedingung beide erfuellt, bleibt der
    Text unveraendert bei „Wolken" (Wolkenbedingung hat textlich Vorrang, Rule 3)."""
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.85, cl=40, cm=35, sun_azimuth=278,
                                subject_azimuth=85, aod=0.9)]
    neue, _ = _generate_cloud_mood_events(feed)
    red_sky_events = [e for e in neue if e["event_type"] == "Himmelsröte"]
    assert len(red_sky_events) == 1
    desc = red_sky_events[0]["description"]
    assert "Wolkenschichten" in desc, f"Text haette bei erfuellter Wolkenbedingung Wolken nennen muessen: {desc}"


def test_integration_kein_event_weder_wolken_noch_dunst():
    """AK-4 (Regression): weder Wolken- noch Dunstbedingung erfuellt -> keine
    Himmelsröte-Karte."""
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.85, cl=10, cm=5, sun_azimuth=278,
                                subject_azimuth=98, aod=0.12)]
    neue, _ = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" not in typen, f"Himmelsröte haette nicht erscheinen duerfen. Erzeugte Typen: {typen}"


def test_integration_aerosol_fehlt_faellt_auf_wolken_pfad_zurueck():
    """AK-6 (Edge Case): aerosol_optical_depth fehlt im weather_details-Dict
    komplett (wd.get(...) -> None, wie bei fehlgeschlagenem Abruf) -> Verhalten
    identisch zum reinen Wolken-Pfad, kein Fehler, keine Exception."""
    from main import _generate_cloud_mood_events

    event = _make_golden_event(gcs=0.85, cl=40, cm=35, sun_azimuth=278, subject_azimuth=85)
    del event["weather_details"]["aerosol_optical_depth"]
    feed = [event]
    neue, _ = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Himmelsröte" in typen, f"Wolken-Pfad haette weiterhin auslösen muessen. Erzeugte Typen: {typen}"


def test_integration_golden_clouds_unveraendert_trotz_hohem_aerosolwert():
    """AK-5: GOLDEN_CLOUDS-Erzeugung bleibt unberuehrt, auch wenn ein hoher
    Aerosolwert im selben Event vorhanden ist (US-130 betrifft ausschliesslich
    RED_SKY, nicht GOLDEN_CLOUDS)."""
    from main import _generate_cloud_mood_events

    feed = [_make_golden_event(gcs=0.82, sun_azimuth=278, subject_azimuth=265,
                                cl=5, cm=10, aod=0.95)]
    neue, entfernte = _generate_cloud_mood_events(feed)
    typen = [e["event_type"] for e in neue]
    assert "Goldene Wolken" in typen, f"GOLDEN_CLOUDS fehlt (Regression). Erzeugte Typen: {typen}"
    assert "test-event-1" in entfernte
    # Kein zusaetzliches/falsches Himmelsröte-Event durch den hohen Aerosolwert,
    # solange die Richtungsbedingung fuer RED_SKY (Gegenpunkt) nicht erfuellt ist.
    assert "Himmelsröte" not in typen, f"Himmelsröte haette hier nicht erscheinen duerfen: {typen}"
