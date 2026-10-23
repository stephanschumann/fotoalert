"""
BUG-119: Feed zeigt nach Serverstart oder Neuladen kurzzeitig zu hohe Werte ohne Wetter.

Umsetzung Option A (Weg-Gate Stephan, 2026-10-23): Beim Neuladen der Feed-Datei wird das zuletzt gespeicherte Wetter
(Wetter-Zwischenspeicher auf der Platte, ohne Netzabruf) sofort wieder auf die Termine der nächsten 3 Tage gelegt,
bevor der neue Stand ausgeliefert wird. Danach werden die Besonderen Ereignisse neu erzeugt.

Tests entstanden VOR der Umsetzung (test-first); die als "Schutztest" gekennzeichneten sind schon gegen den alten
Code grün (Polarität / Regression), alle anderen waren dort rot.

Isolation (wie test_bug117.py): kein Netzwerk (Wetterdienst durch Attrappen ersetzt), der Cache-Ordner
(main._CACHE_DIR) zeigt auf ein leeres Wegwerf-Verzeichnis, die Feed-Datei (main._OPP_CACHE) liegt ebenfalls dort.
Alle Termine liegen RELATIV zur echten Uhr (kein festes Kalenderdatum), damit der Test nicht aus dem
Vorhersagefenster wandert. Im Test-Modus ist der echte Cache-Ordner gesperrt (main._wetter_speicher_erlaubt());
dank des umgelenkten Ordners ist der Zwischenspeicher hier trotzdem benutzbar.

Abgedeckte AKs: AK-1, AK-2, AK-3, AK-4, AK-5, AK-6, AK-7, AK-8, AK-9, AK-10, AK-11, AK-13, AK-14.
Nicht hier prüfbar: AK-12 (Dauer auf dem Produktionsserver, Messung dort).
"""
import asyncio
import copy
import json
import logging
import re
import threading
import time
from datetime import datetime, timedelta, timezone

import pytest

import main
from calculations.weather import (
    AerosolForecast, HourlyAerosol, HourlyWeather, WeatherForecast,
)
from data import wetter_speicher

pytestmark = [pytest.mark.offline, pytest.mark.regression]

# Orte mit Termin im 3-Tage-Fenster (loc3 liegt 5 Tage entfernt, ausserhalb)
NAH = ("loc0", "loc1", "loc2", "loc4")
ASTRO = 0.8     # Astronomie-Wert der Test-Termine = Gesamtwert ohne Wetter


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------

def _hourly(t, wolken=30.0):
    return HourlyWeather(
        time=t, cloud_cover_pct=wolken, cloud_cover_low_pct=10.0, cloud_cover_mid_pct=10.0,
        cloud_cover_high_pct=10.0, visibility_m=20000.0, precipitation_mm=0.0,
        precipitation_prob_pct=0.0, wind_speed_kmh=5.0, wind_direction_deg=180.0,
        temperature_c=18.0, dew_point_c=8.0, weather_code=1,
    )


def _forecast(lat=0.0, lon=0.0, von_h=-2, bis_h=96, wolken=30.0):
    ref = datetime.now(timezone.utc)
    return WeatherForecast(location_lat=lat, location_lon=lon, fetched_at=ref,
                           hourly=[_hourly(ref + timedelta(hours=i), wolken) for i in range(von_h, bis_h)])


def _aerosol(lat=0.0, lon=0.0):
    ref = datetime.now(timezone.utc)
    return AerosolForecast(location_lat=lat, location_lon=lon, fetched_at=ref,
                           hourly=[HourlyAerosol(time=ref + timedelta(hours=i), aerosol_optical_depth=0.05)
                                   for i in range(-2, 96)])


def _termin(loc_id, i, art, offset_h):
    s_lat, s_lon = 51.0 + i * 0.05, 12.0 + i * 0.03
    shoot = datetime.now(timezone.utc) + timedelta(hours=offset_h)
    e = {
        "id": f"t-{loc_id}", "location_id": loc_id, "location_name": f"Zugspitzblick{i}",
        "event_type": art,
        "observer_lat": s_lat + 0.01, "observer_lon": s_lon + 0.01,
        "subject_lat": s_lat, "subject_lon": s_lon, "subject_azimuth": 98,
        "shoot_time": shoot.isoformat(),
        "astronomy_score": ASTRO, "overall_score": ASTRO,
        "weather_score": 0.0, "weather_description": "",
        "sightline_status": "nicht_geprueft", "sightline_angle_deg": None,
    }
    if art.startswith("Goldene"):
        e.update(sunset_azimuth=278, sunrise_azimuth=None)
    else:
        e.update(celestial_azimuth=278, celestial_altitude=-5.0)
    return e


def _roh_feed():
    """Die Termine so, wie sie in der Feed-Datei stehen: nie mit Wetter."""
    return [
        _termin("loc0", 0, "Goldene Stunde Abend", 12),
        _termin("loc1", 1, "Goldene Stunde Abend", 30),
        _termin("loc2", 2, "Goldene Stunde Abend", 60),
        _termin("loc3", 3, "Goldene Stunde Abend", 120),     # 5 Tage: ausserhalb des Wetterfensters
        _termin("loc4", 4, "Blaue Stunde", 12),
    ]


class Attrappe:
    """Ersetzt den Wetterdienst und zählt die Aufrufe."""
    def __init__(self):
        self.calls = []

    async def weather(self, lat, lon, days=7):
        self.calls.append(("weather", lat, lon))
        return _forecast(lat, lon)

    async def aerosol(self, lat, lon, days=7):
        self.calls.append(("aerosol", lat, lon))
        return _aerosol(lat, lon)


@pytest.fixture(autouse=True)
def welt(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(main, "_CACHE_DIR", cache)
    monkeypatch.setattr(main, "_OPP_CACHE", tmp_path / "opportunities.json")
    monkeypatch.setattr(main, "_pausierte_ort_ids", lambda z=None: set())
    monkeypatch.setattr(main, "_geloeschte_ids", lambda: set())
    monkeypatch.setattr(main, "_maybe_alert", lambda *a, **k: None)
    monkeypatch.setattr(main, "WEATHER_API_REQUEST_PACING_SECONDS", 0.0)
    monkeypatch.setattr(main, "WEATHER_API_RETRY_BACKOFF_BASE_SECONDS", 0.0)
    main._feed_cache = []
    main._job_status["weather"] = {"status": "idle", "last_run": None, "last_error": None,
                                   "duration_s": None, "error_class": None, "spec": None}
    yield {"cache": cache, "opp": tmp_path / "opportunities.json"}
    main._feed_cache = []


@pytest.fixture
def attrappe(monkeypatch):
    a = Attrappe()
    monkeypatch.setattr(main, "fetch_weather_forecast", a.weather)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", a.aerosol)
    return a


def _feed_datei_schreiben(welt, termine):
    welt["opp"].write_text(json.dumps({"computed_at": datetime.now(timezone.utc).isoformat(),
                                       "opportunities": termine}), encoding="utf-8")


def _speicher_pfad(welt):
    return welt["cache"] / wetter_speicher.SPEICHER_DATEI


def _mit_wetter_vorbereiten(welt, attrappe):
    """Normaler Wetterlauf auf dem Feed: Der Speicher im Arbeitsspeicher hat Wetter, der Zwischenspeicher auf der
    Platte ist gefüllt, die Feed-Datei enthält (wie in echt) die Termine OHNE Wetter. Gibt {Termin-Nr: Termin} des
    Standes MIT Wetter zurück."""
    roh = _roh_feed()
    _feed_datei_schreiben(welt, roh)
    main._feed_cache = copy.deepcopy(roh)
    asyncio.run(main._weather_overlay())
    attrappe.calls.clear()
    return {e["location_id"]: copy.deepcopy(e) for e in main._feed_cache if e["id"].startswith("t-")}


def _je_ort(termine=None):
    termine = main._feed_cache if termine is None else termine
    return {e["location_id"]: e for e in termine if e["id"].startswith("t-")}


def _speicher_aendern(welt, funktion):
    daten = json.loads(_speicher_pfad(welt).read_text(encoding="utf-8"))
    funktion(daten)
    _speicher_pfad(welt).write_text(json.dumps(daten), encoding="utf-8")


# ---------------------------------------------------------------------------
# AK-1 / AK-3 / AK-14 — Neuladen mit gespeichertem Wetter: Werte wie vorher
# ---------------------------------------------------------------------------

def test_ak1_neuladen_legt_gespeichertes_wetter_sofort_wieder_auf(welt, attrappe):
    """BUG-119 AK-1: Nach dem Neuladen zeigen die Termine der nächsten 3 Tage dieselben gerechneten Werte mit
    Wetter wie vorher (Wetter-Etikett gesetzt), nicht die hohen Rohwerte."""
    vorher = _mit_wetter_vorbereiten(welt, attrappe)
    assert all(vorher[k]["weather_status"] == "ok" for k in NAH), "Testaufbau: Wetterlauf hat kein Wetter gesetzt"
    assert vorher["loc0"]["overall_score"] != ASTRO, "Testaufbau: Wetter muss den Gesamtwert verändern"

    assert main._load_feed_cache() is True
    nachher = _je_ort()
    for k in NAH:
        assert nachher[k].get("weather_status") == "ok", f"{k}: nach dem Neuladen ohne Wetter-Etikett"
        assert nachher[k]["overall_score"] == vorher[k]["overall_score"], (
            f"{k}: Gesamtwert nach Neuladen {nachher[k]['overall_score']} statt {vorher[k]['overall_score']}")
        assert nachher[k]["weather_score"] == vorher[k]["weather_score"]


def test_ak3_zahl_der_chancen_ueber_dem_mindestwert_bleibt_gleich(welt, attrappe, monkeypatch):
    """BUG-119 AK-3: Wie viele Termine der nächsten 3 Tage den Mindestwert (hier die Mitte zwischen Wert mit und
    ohne Wetter) erreichen, ist vor und nach dem Neuladen gleich — genau das ließ im Feed ganze Tage verschwinden."""
    vorher = _mit_wetter_vorbereiten(welt, attrappe)
    schwelle = (vorher["loc0"]["overall_score"] + ASTRO) / 2
    anzahl_vorher = sum(1 for k in NAH if vorher[k]["overall_score"] >= schwelle)
    main._load_feed_cache()
    anzahl_nachher = sum(1 for e in _je_ort().values() if e["location_id"] in NAH and e["overall_score"] >= schwelle)
    assert anzahl_nachher == anzahl_vorher, f"{anzahl_nachher} statt {anzahl_vorher} Termine über dem Mindestwert"


def test_ak14_felder_der_termine_bleiben_unveraendert(welt, attrappe):
    """BUG-119 AK-14: Nach dem Auflegen haben die Termine genau dieselben Felder wie nach einem normalen
    Wetterlauf (keine neuen, keine fehlenden); die Feed-Datei selbst wird nicht verändert."""
    vorher = _mit_wetter_vorbereiten(welt, attrappe)
    datei_vorher = welt["opp"].read_bytes()
    main._load_feed_cache()
    nachher = _je_ort()
    for k in NAH:
        assert set(nachher[k]) == set(vorher[k]), (
            f"{k}: Feldnamen weichen ab: {set(nachher[k]) ^ set(vorher[k])}")
    assert welt["opp"].read_bytes() == datei_vorher, "Feed-Datei wurde verändert"


# ---------------------------------------------------------------------------
# AK-2 — Einzel-Ort-Neuberechnung und Sichtachsen-Prüfung: andere Orte unverändert
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("weg", ["einzel_ort", "sichtachsen"])
def test_ak2_andere_orte_behalten_ihre_werte(welt, attrappe, weg):
    """BUG-119 AK-2: Neuberechnung eines Einzelorts (Neuladen + Wetter nur für diesen Ort) und Sichtachsen-Prüfung
    (nur Neuladen) lassen die Gesamtwerte aller ANDEREN Orte unverändert (Abweichung 0)."""
    vorher = _mit_wetter_vorbereiten(welt, attrappe)
    main._load_feed_cache()
    if weg == "einzel_ort":
        asyncio.run(main._weather_overlay_single("loc0"))
    nachher = _je_ort()
    for k in ("loc1", "loc2", "loc4"):
        assert nachher[k]["overall_score"] == vorher[k]["overall_score"], f"{k} hat sich verändert ({weg})"
        assert nachher[k].get("weather_status") == "ok"


# ---------------------------------------------------------------------------
# AK-4 — nie ein Zeitpunkt ohne Wetter während des Neuladens
# ---------------------------------------------------------------------------

def test_ak4_feed_abfragen_sehen_waehrend_des_neuladens_nie_werte_ohne_wetter(welt, attrappe, monkeypatch):
    """BUG-119 AK-4: Eine Feed-Abfrage parallel zum Neuladen liefert zu keinem Zeitpunkt Termine der nächsten 3 Tage
    ohne Wetter, wenn vorher Wetter da war (das Wetter wird auf der NEUEN Liste aufgelegt, bevor sie die alte
    ersetzt). Das Einlesen der Zwischenspeicher-Einträge wird künstlich verlangsamt, damit ein Fenster entstünde."""
    _mit_wetter_vorbereiten(welt, attrappe)
    original = wetter_speicher.forecast_aus_json

    def langsam(d):
        time.sleep(0.003)
        return original(d)
    monkeypatch.setattr(wetter_speicher, "forecast_aus_json", langsam)

    schnappschuesse = []
    stop = threading.Event()

    def beobachter():
        while not stop.is_set():
            liste = main._feed_cache            # genau das, was eine Abfrage zu diesem Zeitpunkt sähe
            schnappschuesse.append([e.get("weather_status") for e in list(liste)
                                    if e.get("location_id") in NAH and e["id"].startswith("t-")])
            time.sleep(0.0005)

    t = threading.Thread(target=beobachter)
    t.start()
    try:
        time.sleep(0.02)
        main._load_feed_cache()
        time.sleep(0.05)                        # auch danach noch beobachten
    finally:
        stop.set()
        t.join()
    assert len(schnappschuesse) > 10, "Testaufbau: zu wenige Beobachtungen"
    schlecht = [s for s in schnappschuesse if s != ["ok"] * len(NAH)]
    assert not schlecht, f"{len(schlecht)} von {len(schnappschuesse)} Abfragen sahen Termine ohne Wetter: {schlecht[0]}"


# ---------------------------------------------------------------------------
# AK-5 — kein / kaputter / zu alter Zwischenspeicher, neuer Ort
# ---------------------------------------------------------------------------

def _zwischenspeicher_verderben(welt, art):
    pfad = _speicher_pfad(welt)
    if art == "fehlt":
        pfad.unlink()
    elif art == "kaputt":
        pfad.write_text("{{{ das ist kein JSON", encoding="utf-8")
    elif art == "zu_alt":
        def alt(d):
            for v in d.values():
                v["t"] = time.time() - 25 * 3600
        _speicher_aendern(welt, alt)
    elif art == "eintraege_kaputt":
        _speicher_aendern(welt, lambda d: [d.__setitem__(k, {"t": time.time(), "f": {"typ": "w"}}) for k in list(d)])


@pytest.mark.parametrize("art", ["fehlt", "kaputt", "zu_alt", "eintraege_kaputt"])
def test_ak5_ohne_brauchbaren_zwischenspeicher_wie_heute(welt, attrappe, art):
    """BUG-119 AK-5: Fehlt der Zwischenspeicher, ist er kaputt, einzelne Einträge kaputt oder älter als 24 Stunden,
    läuft das Neuladen ohne Fehler durch und die Termine behalten die Werte ohne Wetter (wie heute) bis zum
    nächsten Wetterlauf. Schutztest für den Fehlerfall: schon gegen den alten Code grün."""
    _mit_wetter_vorbereiten(welt, attrappe)
    _zwischenspeicher_verderben(welt, art)
    assert main._load_feed_cache() is True
    for k, e in _je_ort().items():
        assert e.get("weather_status") != "ok", f"{k}: Wetter aus unbrauchbarem Zwischenspeicher aufgelegt ({art})"
        assert e["overall_score"] == ASTRO
    assert len(main._feed_cache) == len(_roh_feed())


def test_ak5_ort_ohne_eintrag_bleibt_ohne_wetter_andere_bekommen_es(welt, attrappe):
    """BUG-119 AK-5: Ein Ort ohne Zwischenspeicher-Eintrag (z. B. frisch angelegt) bleibt wie heute ohne Wetter,
    die übrigen Orte bekommen ihr gespeichertes Wetter."""
    vorher = _mit_wetter_vorbereiten(welt, attrappe)
    ref = vorher["loc0"]
    schluessel = f"weather|{ref['observer_lat']:.3f},{ref['observer_lon']:.3f}"

    def entfernen(d):
        assert schluessel in d, "Testaufbau: Schlüssel des Ortswetters nicht im Zwischenspeicher"
        del d[schluessel]
    _speicher_aendern(welt, entfernen)
    main._load_feed_cache()
    nachher = _je_ort()
    assert nachher["loc0"].get("weather_status") != "ok" and nachher["loc0"]["overall_score"] == ASTRO
    for k in ("loc1", "loc2", "loc4"):
        assert nachher[k].get("weather_status") == "ok"


# ---------------------------------------------------------------------------
# AK-6 — der nächste Wetterlauf ersetzt den Überbrückungswert
# ---------------------------------------------------------------------------

def test_ak6_ueberbrueckung_bis_24h_und_naechster_lauf_holt_frisch(welt, attrappe):
    """BUG-119 AK-6: Ein 20 Stunden altes gespeichertes Wetter (ältere als die normale Gültigkeit von 2 h nah /
    12 h fern) wird beim Neuladen als Überbrückung genutzt; der nächste reguläre Wetterlauf ruft trotzdem frisch
    ab (Gültigkeit des normalen Laufs unverändert) und ersetzt den Wert durch den frischen."""
    frisch = _mit_wetter_vorbereiten(welt, attrappe)

    def altern_und_bewoelken(d):
        for k, v in d.items():
            v["t"] = time.time() - 20 * 3600
            if v["f"]["typ"] == "w":
                for zeile in v["f"]["h"]:
                    zeile[1] = 95.0          # Wolkenbedeckung gesamt
    _speicher_aendern(welt, altern_und_bewoelken)

    main._load_feed_cache()
    ueberbrueckt = _je_ort()
    assert ueberbrueckt["loc0"].get("weather_status") == "ok", "20 Stunden altes Wetter wird nicht zur Überbrückung genutzt"
    assert ueberbrueckt["loc0"]["overall_score"] != frisch["loc0"]["overall_score"], (
        "Testaufbau: der gespeicherte Wert muss sich vom frischen unterscheiden")

    asyncio.run(main._weather_overlay())
    assert attrappe.calls, "Regulärer Wetterlauf hat nicht frisch abgerufen (Gültigkeit des normalen Laufs verändert?)"
    danach = _je_ort()
    for k in NAH:
        assert danach[k]["overall_score"] == frisch[k]["overall_score"], f"{k}: alter Wert nicht durch frischen ersetzt"


def test_ak6_gueltigkeit_des_normalen_laufs_unveraendert():
    """BUG-119 AK-6 (Schutztest): Die Gültigkeit des normalen Wetterlaufs (BUG-117) bleibt 2 h nah / 12 h fern."""
    assert main.WEATHER_CACHE_VALID_NEAR_S == 2 * 3600
    assert main.WEATHER_CACHE_VALID_FAR_S == 12 * 3600


# ---------------------------------------------------------------------------
# AK-7 / AK-8 — weit entfernte Termine, pausierte und gelöschte Orte
# ---------------------------------------------------------------------------

def test_ak7_termin_in_fuenf_tagen_bleibt_unveraendert(welt, attrappe):
    """BUG-119 AK-7: Ein Termin jenseits von 3 Tagen bekommt auch dann kein Wetter, wenn der Zwischenspeicher
    zufällig einen passenden Eintrag hat; Werte vorher/nachher gleich. (Die nahen Termine bekommen Wetter.)"""
    _mit_wetter_vorbereiten(welt, attrappe)
    fern = _je_ort(_roh_feed())["loc3"]
    lang = _forecast(fern["observer_lat"], fern["observer_lon"], von_h=-2, bis_h=200)
    eintrag = wetter_speicher.eintrag_aus_forecast(lang)
    _speicher_aendern(welt, lambda d: d.__setitem__(f"weather|{fern['observer_lat']:.3f},{fern['observer_lon']:.3f}", eintrag))

    main._load_feed_cache()
    nachher = _je_ort()
    assert nachher["loc0"].get("weather_status") == "ok", "Testaufbau: nahe Termine müssen Wetter bekommen"
    assert nachher["loc3"].get("weather_status") != "ok"
    assert nachher["loc3"]["overall_score"] == ASTRO
    assert nachher["loc3"]["weather_score"] == 0.0


def test_ak8_pausierter_ort_taucht_nicht_wieder_auf(welt, attrappe, monkeypatch):
    """BUG-119 AK-8: Ein pausierter Ort bleibt beim Neuladen weg (auch wenn sein Wetter im Zwischenspeicher steht);
    die übrigen Orte bekommen ihr Wetter."""
    _mit_wetter_vorbereiten(welt, attrappe)
    monkeypatch.setattr(main, "_pausierte_ort_ids", lambda z=None: {"loc1"})
    main._load_feed_cache()
    ids = {e["location_id"] for e in main._feed_cache}
    assert "loc1" not in ids
    assert _je_ort()["loc0"].get("weather_status") == "ok"


def test_ak8_geloeschter_ort_taucht_nicht_wieder_auf(welt, attrappe, monkeypatch):
    """BUG-119 AK-8: Ein gelöschter Ort bleibt beim Neuladen weg; die übrigen Orte bekommen ihr Wetter."""
    _mit_wetter_vorbereiten(welt, attrappe)
    monkeypatch.setattr(main, "_geloeschte_ids", lambda: {"loc2"})
    main._load_feed_cache()
    ids = {e["location_id"] for e in main._feed_cache}
    assert "loc2" not in ids
    assert _je_ort()["loc0"].get("weather_status") == "ok"


# ---------------------------------------------------------------------------
# AK-9 — Besondere Ereignisse
# ---------------------------------------------------------------------------

def test_ak9_besondere_ereignisse_sofort_wieder_da_ohne_doppelte(welt, attrappe, monkeypatch):
    """BUG-119 AK-9: Die Besonderen Ereignisse (Kennungen gc_/rs_/rc_) stehen nach dem Neuladen sofort wieder in
    derselben Zahl da wie nach dem Wetterlauf — erzeugt NACH dem Auflegen des Wetters — und ein zweites Neuladen
    erzeugt keine Doppelten. (Die Erzeugung ist hier durch eine Attrappe ersetzt, die nur Termine MIT Wetter
    berücksichtigt; so wird auch die Reihenfolge geprüft.)"""
    def attrappe_ereignisse(liste):
        neu = []
        for e in liste:
            if e.get("weather_status") == "ok" and e["event_type"].startswith("Goldene"):
                c = copy.deepcopy(e)
                c["id"] = "gc_" + e["id"]
                c["event_type"] = "Goldene Wolken"
                neu.append(c)
        return neu, set()
    monkeypatch.setattr(main, "_generate_cloud_mood_events", attrappe_ereignisse)

    _mit_wetter_vorbereiten(welt, attrappe)
    vorher = sorted(e["id"] for e in main._feed_cache if e["id"].startswith(("gc_", "rs_", "rc_")))
    assert len(vorher) == 3, f"Testaufbau: erwartet 3 Besondere Ereignisse nach dem Wetterlauf, sind {len(vorher)}"

    main._load_feed_cache()
    nach1 = sorted(e["id"] for e in main._feed_cache if e["id"].startswith(("gc_", "rs_", "rc_")))
    assert nach1 == vorher, f"Besondere Ereignisse nach dem Neuladen: {nach1} statt {vorher}"
    main._load_feed_cache()
    nach2 = sorted(e["id"] for e in main._feed_cache if e["id"].startswith(("gc_", "rs_", "rc_")))
    assert nach2 == vorher, "Zweites Neuladen erzeugt Doppelte oder verliert Ereignisse"


# ---------------------------------------------------------------------------
# AK-10 — Abdeckung der gespeicherten Vorhersage
# ---------------------------------------------------------------------------

def test_ak10_zu_kurze_vorhersage_wird_nicht_benutzt(welt, attrappe):
    """BUG-119 AK-10: Reicht die gespeicherte Vorhersage nur 20 Stunden in die Zukunft, bekommt der Termin in 12 h
    sein Wetter, die Termine in 30 h und 60 h aber NICHT (sonst würde still die letzte Stunde genommen)."""
    _mit_wetter_vorbereiten(welt, attrappe)

    def kuerzen(d):
        grenze = time.time() + 20 * 3600
        for v in d.values():
            v["f"]["h"] = [z for z in v["f"]["h"] if z[0] <= grenze]
    _speicher_aendern(welt, kuerzen)
    main._load_feed_cache()
    nachher = _je_ort()
    assert nachher["loc0"].get("weather_status") == "ok", "Termin innerhalb der Abdeckung bekam kein Wetter"
    for k in ("loc1", "loc2"):
        assert nachher[k].get("weather_status") != "ok", f"{k}: Wetter aus nicht abdeckender Vorhersage benutzt"
        assert nachher[k]["overall_score"] == ASTRO


def test_ak10_vorhersage_aus_der_vergangenheit_wird_nicht_benutzt(welt, attrappe):
    """BUG-119 AK-10 (Schutztest): Eine Vorhersage, die vor Tagen endete (Eintrag aber jung), wird nicht benutzt."""
    _mit_wetter_vorbereiten(welt, attrappe)

    def verschieben(d):
        for v in d.values():
            for z in v["f"]["h"]:
                z[0] -= 4 * 86400
    _speicher_aendern(welt, verschieben)
    main._load_feed_cache()
    assert all(e.get("weather_status") != "ok" for e in _je_ort().values())


# ---------------------------------------------------------------------------
# AK-11 — keine zusätzlichen Abrufe, nichts in den Zwischenspeicher geschrieben
# ---------------------------------------------------------------------------

def test_ak11_auflegen_ruft_den_wetterdienst_nie_auf(welt, attrappe, monkeypatch):
    """BUG-119 AK-11: Das Wiederauflegen löst keinen einzigen Abruf beim Wetterdienst aus (Anfragen = 0), legt aber
    trotzdem Wetter auf, und es schreibt nichts in den Zwischenspeicher."""
    _mit_wetter_vorbereiten(welt, attrappe)
    speicher_vorher = _speicher_pfad(welt).read_bytes()

    async def verboten(*a, **k):
        raise AssertionError("Netzabruf beim Wiederauflegen")
    monkeypatch.setattr(main, "fetch_weather_forecast", verboten)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", verboten)
    main._load_feed_cache()
    assert attrappe.calls == []
    assert _je_ort()["loc0"].get("weather_status") == "ok", "Testaufbau: es muss Wetter aufgelegt worden sein"
    assert _speicher_pfad(welt).read_bytes() == speicher_vorher, "Zwischenspeicher wurde beim Auflegen verändert"


def test_einzel_ort_schnellpfad_schreibt_nichts_in_den_zwischenspeicher(welt, attrappe):
    """BUG-119 (Schutztest zu Vorgabe): Der Einzel-Ort-Schnellpfad holt frisch und schreibt NICHTS in den
    Zwischenspeicher (so war es schon vorher und bleibt so)."""
    main._feed_cache = _roh_feed()
    asyncio.run(main._weather_overlay_single("loc0"))
    assert attrappe.calls, "Testaufbau: Schnellpfad muss abrufen"
    assert not _speicher_pfad(welt).exists()


# ---------------------------------------------------------------------------
# AK-13 — Log-Zeile; Verdrahtung der vier Auslöser
# ---------------------------------------------------------------------------

def test_ak13_log_zeile_mit_ausloeser_zahlen_dauer_ohne_ortsnamen(welt, attrappe, caplog):
    """BUG-119 AK-13: Beim Wiederauflegen steht eine Zeile im Log mit Auslöser, Zahl der Termine mit und ohne
    gespeichertes Wetter und Dauer — ohne Ortsnamen."""
    _mit_wetter_vorbereiten(welt, attrappe)
    main._feed_ausloeser_var.set("einzel-ort")
    with caplog.at_level(logging.INFO):
        main._load_feed_cache()
    zeilen = [r.getMessage() for r in caplog.records if "Wetter wieder aufgelegt" in r.getMessage()]
    assert len(zeilen) == 1, f"erwartet genau eine Log-Zeile, gefunden: {zeilen}"
    z = zeilen[0]
    assert "einzel-ort" in z
    m = re.search(r"(\d+) Termine mit gespeichertem Wetter, (\d+) ohne", z)
    assert m, f"Zahlen fehlen in: {z}"
    assert (int(m.group(1)), int(m.group(2))) == (len(NAH), 0)
    assert re.search(r"Dauer \d+[.,]\d+ s", z), f"Dauer fehlt in: {z}"
    assert "Zugspitzblick" not in z and "loc0" not in z, f"Ortsname in der Log-Zeile: {z}"


def test_ak13_alle_vier_ausloeser_sind_verdrahtet():
    """BUG-119: Serverstart, Vorberechnung, Einzel-Ort-Neuberechnung und Sichtachsen-Prüfung benennen vor dem
    Neuladen ihren Auslöser (für die Log-Zeile). Quelltext-Prüfung, weil die Pfade selbst Subprozesse starten."""
    import inspect
    quelle = inspect.getsource(main)
    for name in ("start", "vorberechnung", "einzel-ort", "sichtachsen"):
        assert f'_feed_ausloeser_var.set("{name}")' in quelle, f"Auslöser '{name}' nicht verdrahtet"
