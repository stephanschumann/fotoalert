"""
BUG-117: Wetterabruf scheitert für fast alle Orte (Tageslimit des Wetterdienstes).

Tests ENTSTEHEN IN DER ANALYSE-PHASE (2026-10-18, Weg-Gate: Weg B + gröbere Rote-Wolken-Punkte) und
schlagen gegen den heutigen Code ERWARTUNGSGEMÄSS fehl (Rot-Nachweis). Schutztests, die schon heute
grün sind, sind im Docstring ausdrücklich als "Schutztest" gekennzeichnet (Polarität / Regression).

Isolation: Kein Test liest echte lokale Caches. Die Feed-Liste wird synthetisch gesetzt, der Cache-Ordner
(main._CACHE_DIR) zeigt auf ein leeres Wegwerf-Verzeichnis, der Wetterdienst ist durch Attrappen ersetzt
(KEIN Netzwerk). Jeder Lauf-Test läuft zweimal: Cache "leer" und Cache "befuellt" (vorab mit anderen Orten
gefüllt, damit ein vorhandener Zwischenspeicher die geprüften Orte nicht verdeckt).

Annahmen an die Umsetzung (Teil der Spec): Der Zwischenspeicher und der Tagesstand liegen als Dateien
unter main._CACHE_DIR (damit sie hier umgelenkt werden können). Abgedeckte AKs: AK-4, AK-5, AK-6, AK-7,
AK-8 (schwach), AK-9, AK-10, AK-11, AK-13, AK-14 (Rote-Wolken-Punkte gröber, übrige unverändert).
Noch NICHT testbar ohne festgelegte Schnittstelle (bei der Implementierung nachzuziehen): Neustart-Test
für AK-8 (echter Wiederanlauf), Veralten des Zwischenspeichers (AK-9, zweiter Teil), Staffelung der
späteren Tage über mehrere Läufe (AK-15).
"""
import asyncio
import math
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi import BackgroundTasks

import main
from discover.geometry import destination_point
from calculations.weather import (
    HourlyWeather, WeatherForecast, HourlyAerosol, AerosolForecast,
)

pytestmark = [pytest.mark.offline, pytest.mark.regression]

RC_TOLERANZ_KM = 6.6   # Winkel-Äquivalent zur BUG-104-Toleranz (2 km bei 30 km = 3,8 Grad) bei 100 km


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------

def _hourly(t):
    return HourlyWeather(
        time=t, cloud_cover_pct=30.0, cloud_cover_low_pct=10.0, cloud_cover_mid_pct=10.0,
        cloud_cover_high_pct=10.0, visibility_m=20000.0, precipitation_mm=0.0,
        precipitation_prob_pct=0.0, wind_speed_kmh=5.0, wind_direction_deg=180.0,
        temperature_c=18.0, dew_point_c=8.0, weather_code=1,
    )


def _forecast(lat=0.0, lon=0.0):
    ref = datetime.now(timezone.utc)
    return WeatherForecast(location_lat=lat, location_lon=lon, fetched_at=ref,
                           hourly=[_hourly(ref + timedelta(hours=i)) for i in range(-2, 96)])


def _aerosol(lat=0.0, lon=0.0):
    ref = datetime.now(timezone.utc)
    return AerosolForecast(location_lat=lat, location_lon=lon, fetched_at=ref,
                           hourly=[HourlyAerosol(time=ref + timedelta(hours=i), aerosol_optical_depth=0.05)
                                   for i in range(-2, 96)])


def _err429():
    req = httpx.Request("GET", "http://attrappe.invalid/")
    return httpx.HTTPStatusError("429", request=req, response=httpx.Response(429, request=req))


def _golden(loc_id, i, shoot_offset_h=12, subject=None, observer=None):
    s_lat, s_lon = subject or (51.0 + i * 0.05, 12.0 + i * 0.03)
    o_lat, o_lon = observer or (s_lat + 0.01, s_lon + 0.01)
    shoot = datetime.now(timezone.utc) + timedelta(hours=shoot_offset_h)
    return {
        "id": f"t-{loc_id}", "location_id": loc_id, "location_name": loc_id,
        "event_type": "Goldene Stunde Abend",
        "observer_lat": o_lat, "observer_lon": o_lon,
        "subject_lat": s_lat, "subject_lon": s_lon, "subject_azimuth": 98,
        "sunset_azimuth": 278, "sunrise_azimuth": None,
        "shoot_time": shoot.isoformat(),
        "astronomy_score": 0.8, "overall_score": 0.8,
        "weather_score": 0.0, "weather_description": "",
    }


def _blue(loc_id, i, shoot_offset_h=12, subject=None, az=278):
    s_lat, s_lon = subject or (51.0 + i * 0.05, 12.0 + i * 0.03)
    shoot = datetime.now(timezone.utc) + timedelta(hours=shoot_offset_h)
    return {
        "id": f"b-{loc_id}", "location_id": loc_id, "location_name": loc_id,
        "event_type": "Blaue Stunde",
        "observer_lat": s_lat + 0.01, "observer_lon": s_lon + 0.01,
        "subject_lat": s_lat, "subject_lon": s_lon, "subject_azimuth": 98,
        "celestial_azimuth": az, "celestial_altitude": -5.0,
        "shoot_time": shoot.isoformat(),
        "astronomy_score": 0.8, "overall_score": 0.8,
        "weather_score": 0.0, "weather_description": "",
    }


def _subject_fuer_ziel(ziel, az, dist_m):
    """Sucht den Motiv-Punkt, dessen Projektion (az, dist_m) auf ziel=(lat, lon) fällt."""
    s = ziel
    for _ in range(8):
        p = destination_point(s[0], s[1], az, dist_m)
        s = (s[0] + (ziel[0] - p[0]), s[1] + (ziel[1] - p[1]))
    p = destination_point(s[0], s[1], az, dist_m)
    assert abs(p[0] - ziel[0]) < 1e-5 and abs(p[1] - ziel[1]) < 1e-5, "Testaufbau ungültig: Zielpunkt nicht erreichbar"
    return s


def _km(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


class Attrappe:
    """Ersetzt den Wetterdienst. Zählt Aufrufe und gleichzeitig laufende Aufrufe."""
    def __init__(self):
        self.calls = []          # (art, lat, lon)
        self.in_flight = 0
        self.peak = 0
        self.dauer = 0.0
        self.regel = lambda art, lat, lon: None   # None = Erfolg, sonst Exception

    async def _hit(self, art, lat, lon):
        self.calls.append((art, lat, lon))
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        try:
            if self.dauer:
                await asyncio.sleep(self.dauer)
            exc = self.regel(art, lat, lon)
            if exc is not None:
                raise exc
        finally:
            self.in_flight -= 1

    async def weather(self, lat, lon, days=7):
        await self._hit("weather", lat, lon)
        return _forecast(lat, lon)

    async def aerosol(self, lat, lon, days=7):
        await self._hit("aerosol", lat, lon)
        return _aerosol(lat, lon)


@pytest.fixture(autouse=True)
def isoliert(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(main, "_CACHE_DIR", cache)
    assert list(cache.iterdir()) == [], "Testaufbau: Cache-Ordner muss leer starten"
    monkeypatch.setattr(main, "_pausierte_ort_ids", lambda z=None: set())
    monkeypatch.setattr(main, "_maybe_alert", lambda *a, **k: None)
    monkeypatch.setattr(main, "WEATHER_API_REQUEST_PACING_SECONDS", 0.0)
    monkeypatch.setattr(main, "WEATHER_API_RETRY_BACKOFF_BASE_SECONDS", 0.0)
    main._feed_cache = []
    main._job_status["weather"] = {"status": "idle", "last_run": None, "last_error": None,
                                   "duration_s": None, "error_class": None, "spec": None}
    yield cache
    main._feed_cache = []


@pytest.fixture
def attrappe(monkeypatch):
    a = Attrappe()
    monkeypatch.setattr(main, "fetch_weather_forecast", a.weather)
    monkeypatch.setattr(main, "fetch_aerosol_forecast", a.aerosol)
    return a


@pytest.fixture(params=["leer", "befuellt"])
def cache_zustand(request, attrappe, isoliert):
    """leer = frischer Ordner; befuellt = vorab ein erfolgreicher Lauf für ANDERE Orte (Namen 'alt_*')."""
    if request.param == "befuellt":
        main._feed_cache = [_golden(f"alt_{i}", 500 + i) for i in range(10)]
        asyncio.run(main._weather_overlay())
        attrappe.calls.clear()
        attrappe.peak = 0
        main._feed_cache = []
        main._job_status["weather"].update(status="idle", last_error=None)
    return request.param


def _feed(n, offset_h=12):
    return [_golden(f"loc{i}", i, shoot_offset_h=offset_h) for i in range(n)]


# ---------------------------------------------------------------------------
# AK-5 / AK-7 / AK-13 (Notbremse) — Herkunft: Beobachtung 42 von 42 Läufen, Fehlerklasse "Unknown"
# ---------------------------------------------------------------------------

def test_ak5_dauerablehnung_bricht_fruh_ab_und_nennt_grund(attrappe, cache_zustand):
    """Lehnt der Dienst jeden Abruf mit 429 ab, hört der Lauf nach wenigen Abrufen auf (nicht erst nach allen
    rund 700) und die Statusmeldung nennt den Grund in Klartext ("Limit")."""
    attrappe.regel = lambda art, lat, lon: _err429()
    main._feed_cache = _feed(60)                      # 60 Orte x 4 Abrufarten = 240 Aufgaben
    asyncio.run(main._weather_overlay())
    assert len(attrappe.calls) <= 40, (
        f"Notbremse fehlt: {len(attrappe.calls)} Abrufe trotz Dauer-Ablehnung (Soll: höchstens 40)")
    st = main._job_status["weather"]
    assert st["status"] == "error"
    assert "Limit" in (st["last_error"] or ""), f"Statusmeldung nennt keinen Klartext-Grund: {st['last_error']!r}"


def test_ak13_dienst_nicht_erreichbar_bricht_ebenfalls_fruh_ab(attrappe, cache_zustand):
    """503 / 'Verbindung abgelehnt' in Folge beenden den Lauf ebenfalls früh mit Klartext (AK-13)."""
    req = httpx.Request("GET", "http://attrappe.invalid/")
    attrappe.regel = lambda art, lat, lon: httpx.ConnectError("Connection refused", request=req)
    main._feed_cache = _feed(60)
    asyncio.run(main._weather_overlay())
    assert len(attrappe.calls) <= 40, f"{len(attrappe.calls)} Abrufe trotz durchgehend nicht erreichbarem Dienst"
    assert main._job_status["weather"]["last_error"]


def test_ak5_schutztest_einzelne_ablehnungen_brechen_nicht_ab(attrappe, cache_zustand):
    """SCHUTZTEST (heute schon grün, Polarität zu AK-5 und AK-10): Fallen nur 2 von 50 Orten aus, werden alle
    übrigen 48 normal geholt, der Lauf geht weiter."""
    schlecht = {(51.0 + i * 0.05 + 0.01) for i in (3, 7)}
    attrappe.regel = lambda art, lat, lon: (
        _err429() if art == "weather" and any(abs(lat - s) < 1e-6 for s in schlecht) else None)
    main._feed_cache = _feed(50)
    asyncio.run(main._weather_overlay())
    ok = {c[1] for c in attrappe.calls if c[0] == "weather"}
    assert len(ok) >= 48, f"Nur {len(ok)} verschiedene Orte abgefragt"
    # die beiden schlechten Orte wurden versucht; alle anderen Orte haben ihr Wetter bekommen
    mit_wetter = [e for e in main._feed_cache if e.get("weather_score")]
    assert len(mit_wetter) >= 40


# ---------------------------------------------------------------------------
# AK-6 (nie zwei Läufe gleichzeitig) — Herkunft: keine Lauf-Sperre im Code, Drossel je Lauf lokal
# ---------------------------------------------------------------------------

def test_ak6_zwei_gleichzeitige_laeufe_bleiben_unter_der_drossel(attrappe, cache_zustand):
    attrappe.dauer = 0.02
    main._feed_cache = _feed(12)

    async def zwei():
        await asyncio.gather(main._weather_overlay(triggered_by="cron"),
                             main._weather_overlay(triggered_by="manual"))
    asyncio.run(zwei())
    assert attrappe.peak <= main.WEATHER_API_MAX_CONCURRENT_REQUESTS, (
        f"{attrappe.peak} gleichzeitige Abrufe (erlaubt: {main.WEATHER_API_MAX_CONCURRENT_REQUESTS}) — "
        "zwei Läufe liefen parallel")
    assert len(attrappe.calls) <= 12 * 4, f"{len(attrappe.calls)} Abrufe: Lauf wurde doppelt ausgeführt"


def test_ak6_host_knopf_meldet_laeuft_bereits(attrappe, cache_zustand):
    attrappe.dauer = 0.05
    main._feed_cache = _feed(8)

    async def ablauf():
        lauf = asyncio.create_task(main._weather_overlay())
        await asyncio.sleep(0.03)
        antwort = await main.trigger_weather_refresh(BackgroundTasks(), _role="host")
        await lauf
        return antwort
    antwort = asyncio.run(ablauf())
    assert "läuft bereits" in str(antwort.get("message", "")).lower().replace("laeuft", "läuft"), antwort
    assert antwort.get("status") != "started", antwort


# ---------------------------------------------------------------------------
# AK-4 (Heute/Morgen zuerst)
# ---------------------------------------------------------------------------

def test_ak4_termine_von_heute_und_morgen_kommen_zuerst(attrappe):
    spaet = [_golden(f"spaet{i}", i, shoot_offset_h=60) for i in range(5)]     # Tag 3
    frueh = [_golden(f"frueh{i}", 20 + i, shoot_offset_h=12) for i in range(5)]  # heute
    tasks = main._plan_weather_fetch_tasks(spaet + frueh)    # Feed-Reihenfolge: spät zuerst
    namen = [t[4] for t in tasks]
    letzte_frueh = max(i for i, n in enumerate(namen) if n.startswith("frueh"))
    erste_spaet = min(i for i, n in enumerate(namen) if n.startswith("spaet"))
    assert letzte_frueh < erste_spaet, "Abrufe für spätere Tage stehen vor denen für heute"


# ---------------------------------------------------------------------------
# AK-9 / AK-8 (Zwischenspeicher, Tagesstand)
# ---------------------------------------------------------------------------

def test_ak9_zwischenspeicher_verhindert_doppelabrufe(attrappe, cache_zustand):
    """Zweiter Lauf kurz nach einem erfolgreichen ersten holt für dieselben Orte nichts erneut."""
    main._feed_cache = _feed(10)
    asyncio.run(main._weather_overlay())
    erster = len(attrappe.calls)
    assert erster >= 10
    attrappe.calls.clear()
    asyncio.run(main._weather_overlay(triggered_by="startup"))
    assert len(attrappe.calls) == 0, f"{len(attrappe.calls)} Abrufe im zweiten Lauf trotz frischer Daten"


def test_ak9_zwischenspeicher_liefert_wetter_auch_ohne_abruf(attrappe, cache_zustand):
    """Orte, die aus dem Zwischenspeicher kommen, haben nach dem zweiten Lauf weiterhin Wetterwerte."""
    main._feed_cache = _feed(10)
    asyncio.run(main._weather_overlay())
    main._feed_cache = _feed(10)          # frische Termine ohne Wetterwerte (wie nach Neuladen des Feeds)
    attrappe.calls.clear()
    asyncio.run(main._weather_overlay())
    assert len(attrappe.calls) == 0
    assert all(e.get("weather_score") for e in main._feed_cache), "Wetterwerte fehlen trotz Zwischenspeicher"


def test_ak8_tagesstand_wird_auf_der_platte_gespeichert(attrappe, cache_zustand, isoliert):
    """AK-8 (umgeschrieben am 2026-10-18 mit Freigabe von Stephan; der alte Test verlangte im Fall "befuellt" eine
    NEUE Datei, obwohl der Vorlauf dieselben Dateien schon angelegt hatte, und war so nie erfüllbar).
    Nach einem Lauf ist der Tagesverbrauch auf der Platte höher als vorher, und nach einem simulierten Neustart
    (Lauf-Zustand im Speicher zurückgesetzt, Stand frisch von der Platte gelesen) liefert er denselben Wert.
    Gilt mit leerem und mit befülltem Cache; im Fall "befuellt" ist der Ausgangswert schon größer als null."""
    from data import wetter_speicher
    vorher = wetter_speicher.tagesstand_lesen(isoliert)["ortswetter"]["gewichtet"]
    if cache_zustand == "befuellt":
        assert vorher > 0, "Testaufbau: der Vorlauf mit anderen Orten muss bereits Verbrauch gebucht haben"
    else:
        assert vorher == 0, "Testaufbau: ein leerer Cache-Ordner beginnt bei null"
    main._feed_cache = _feed(5)
    asyncio.run(main._weather_overlay())
    nach_lauf = wetter_speicher.tagesstand_lesen(isoliert)["ortswetter"]["gewichtet"]
    assert nach_lauf > vorher, f"Verbrauch nicht gespeichert: vorher {vorher}, nach dem Lauf {nach_lauf}"
    # "Neustart": alles im Speicher weg, nur die Dateien bleiben
    main._weather_run_active = False
    main._weather_run_pending = False
    main._feed_cache = []
    nach_neustart = wetter_speicher.tagesstand_lesen(isoliert)["ortswetter"]["gewichtet"]
    assert nach_neustart == nach_lauf, f"Nach Neustart {nach_neustart} statt {nach_lauf}"


# ---------------------------------------------------------------------------
# AK-11 / AK-14 (Rote-Wolken-Punkte gröber, alles andere unverändert)
# ---------------------------------------------------------------------------

def _rc_events(deltas_lat, deltas_lon, basis=(52.50, 13.50)):
    ev = []
    for i, (dl, dn) in enumerate(zip(deltas_lat, deltas_lon)):
        ziel = (basis[0] + dl, basis[1] + dn)
        subj = _subject_fuer_ziel(ziel, 278, main.RED_CLOUDS_PROJECTION_DISTANCE_M)
        ev.append(_blue(f"rc{i}", i, subject=subj))
    return ev


def test_ak14_rote_wolken_punkte_in_derselben_naehe_werden_zusammengefasst():
    """Zwei Rote-Wolken-Punkte ~1,3 km auseinander (0,012 Grad) ergeben nur EINEN Abruf (heute: zwei)."""
    ev = _rc_events([-0.006, 0.006], [-0.006, 0.006])
    rc = [t for t in main._plan_weather_fetch_tasks(ev) if t[0] == "red_clouds_dir"]
    assert len(rc) == 1, f"{len(rc)} Rote-Wolken-Abrufe für zwei fast gleiche Punkte"


def test_ak14_schutztest_ferne_rote_wolken_punkte_bleiben_getrennt():
    """SCHUTZTEST (heute grün): Punkte 0,3 Grad (rund 30 km) auseinander werden nie zusammengelegt."""
    ev = _rc_events([-0.15, 0.15], [-0.15, 0.15])
    rc = [t for t in main._plan_weather_fetch_tasks(ev) if t[0] == "red_clouds_dir"]
    assert len(rc) == 2


def test_ak11_schutztest_abruf_punkt_bleibt_innerhalb_der_toleranz():
    """SCHUTZTEST (heute grün, begrenzt die wählbare Schrittweite): Für jedes Ereignis liegt der tatsächlich
    abgefragte Rote-Wolken-Punkt höchstens 6,6 km (= 3,8 Grad bei 100 km, gleich der BUG-104-Toleranz) vom
    genauen Punkt entfernt. Gefundene Abruf-Koordinaten kommen über Planung UND Nachschlagen (BUG-104-Muster)."""
    spread = [-0.14, -0.09, -0.04, 0.0, 0.03, 0.08, 0.13, 0.17]
    ev = _rc_events(spread, list(reversed(spread)))
    tasks = [t for t in main._plan_weather_fetch_tasks(ev) if t[0] == "red_clouds_dir"]
    fcs = {t[1]: (t[2], t[3]) for t in tasks}
    for e in ev:
        abgefragt = main._lookup_red_clouds_forecast(e, fcs)
        assert abgefragt is not None, "Nachschlagen findet den geplanten Punkt nicht (Plan/Lookup laufen auseinander)"
        genau = main._red_clouds_projection_point(e)
        assert _km(abgefragt, genau) <= RC_TOLERANZ_KM, f"Versatz {_km(abgefragt, genau):.1f} km"


def test_ak14_plan_und_nachschlagen_finden_zusammengefasste_punkte():
    """Rot, solange nicht zusammengefasst; danach: beide Ereignisse finden ihren (gemeinsamen) Forecast."""
    ev = _rc_events([-0.006, 0.006], [-0.006, 0.006])
    tasks = [t for t in main._plan_weather_fetch_tasks(ev) if t[0] == "red_clouds_dir"]
    assert len(tasks) == 1, "Punkte wurden nicht zusammengefasst"
    fcs = {tasks[0][1]: "FC"}
    assert all(main._lookup_red_clouds_forecast(e, fcs) == "FC" for e in ev)


def test_ak14_schutztest_uebrige_punkte_und_ortswetter_unveraendert():
    """SCHUTZTEST (heute grün): Sonnen-/Gegenrichtungs-/Dunst-Punkte behalten Rundung auf 2 Stellen,
    Standortwetter auf 3 Stellen; Ereignisse 1,3 km auseinander bleiben getrennte Abrufe."""
    assert main.PROJECTED_POINT_CACHE_PRECISION == 2
    ev = []
    for i, d in enumerate((-0.006, 0.006)):
        subj = _subject_fuer_ziel((52.50 + d, 13.50 + d), 278, main.CLOUD_MOOD_PROJECTION_DISTANCE_M)
        ev.append(_golden(f"g{i}", i, subject=subj, observer=(52.30 + 0.0006 * i, 13.40 + 0.0006 * i)))
    tasks = main._plan_weather_fetch_tasks(ev)
    arten = {k: len([t for t in tasks if t[0] == k]) for k in ("weather", "sun_dir")}
    assert arten["sun_dir"] == 2, arten
    assert arten["weather"] == 2, arten


# ---------------------------------------------------------------------------
# Nachgezogene Tests (Umsetzungsphase 2026-10-18, nachdem die Schnittstelle steht): AK-8 Neustart,
# AK-9 Teil 2 (Veralten), AK-15 (Staffelung nah/fern). Bestehende Tests oben unverändert.
# ---------------------------------------------------------------------------

def _speicher_altern(cache_ordner, sekunden):
    """Setzt den Abrufzeitpunkt aller Einträge im Zwischenspeicher um `sekunden` in die Vergangenheit."""
    import json
    pfad = cache_ordner / "weather_forecast_cache.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    for ein in daten.values():
        ein["t"] -= sekunden
        ein["f"]["t"] -= sekunden
    pfad.write_text(json.dumps(daten), encoding="utf-8")


def test_ak8_tagesstand_ueberlebt_neustart(attrappe, cache_zustand, isoliert):
    """BUG-117 AK-8: Der Tagesstand steht auf der Platte und wird nach einem (simulierten) Neustart weitergezählt
    statt bei null zu beginnen."""
    from data import wetter_speicher
    main._feed_cache = _feed(5)
    asyncio.run(main._weather_overlay())
    stand1 = wetter_speicher.tagesstand_lesen(isoliert)
    assert stand1["ortswetter"]["gewichtet"] > 0 and stand1["ortswetter"]["laeufe"] >= 1
    # "Neustart": Lauf-Zustand im Speicher zurücksetzen; nur die Dateien bleiben
    main._weather_run_active = False
    main._weather_run_pending = False
    asyncio.run(main._weather_overlay(triggered_by="startup"))
    stand2 = wetter_speicher.tagesstand_lesen(isoliert)
    assert stand2["ortswetter"]["laeufe"] == stand1["ortswetter"]["laeufe"] + 1
    assert stand2["ortswetter"]["gewichtet"] >= stand1["ortswetter"]["gewichtet"]


def test_ak9_veralteter_zwischenspeicher_wird_neu_geholt(attrappe, cache_zustand, isoliert):
    """BUG-117 AK-9 Teil 2: Nach Ablauf der Gültigkeit (nahe Termine: 2 Stunden) wird neu geholt."""
    main._feed_cache = _feed(6, offset_h=12)
    asyncio.run(main._weather_overlay())
    attrappe.calls.clear()
    _speicher_altern(isoliert, 3 * 3600)
    asyncio.run(main._weather_overlay())
    assert len(attrappe.calls) >= 6, f"Nur {len(attrappe.calls)} Abrufe trotz veralteter Daten"


def test_ak15_staffelung_nah_wird_oefter_aufgefrischt_als_fern(attrappe, cache_zustand, isoliert):
    """BUG-117 AK-15: Zweieinhalb Stunden später sind Daten für Termine in 12 Stunden veraltet (Soll: neu holen),
    Daten für Termine in 60 Stunden noch gültig (Soll: nichts holen). Nach 13 Stunden auch die fernen."""
    main._feed_cache = _feed(5, offset_h=12)
    asyncio.run(main._weather_overlay())
    attrappe.calls.clear()
    _speicher_altern(isoliert, int(2.5 * 3600))
    asyncio.run(main._weather_overlay())
    assert len(attrappe.calls) >= 5, "Nahe Termine wurden nach 2,5 Stunden nicht aufgefrischt"

    main._feed_cache = _feed(5, offset_h=60)
    asyncio.run(main._weather_overlay())          # füllt den Zwischenspeicher für die fernen Termine
    attrappe.calls.clear()
    _speicher_altern(isoliert, int(2.5 * 3600))
    asyncio.run(main._weather_overlay())
    assert len(attrappe.calls) == 0, f"{len(attrappe.calls)} Abrufe für ferne Termine nach nur 2,5 Stunden"
    _speicher_altern(isoliert, 11 * 3600)         # insgesamt 13,5 Stunden
    asyncio.run(main._weather_overlay())
    assert len(attrappe.calls) >= 5, "Ferne Termine wurden nach 13,5 Stunden nicht aufgefrischt"


def test_ak7_notbremse_meldung_nennt_ursache_in_klartext(attrappe, cache_zustand):
    """BUG-117 AK-7: Die Statusmeldung nennt Hauptursache und nächsten Versuch in Klartext."""
    attrappe.regel = lambda art, lat, lon: _err429()
    main._feed_cache = _feed(40)
    asyncio.run(main._weather_overlay())
    text = main._job_status["weather"]["last_error"] or ""
    assert "Limit" in text and "Hauptursache" in text and "Nächster Versuch" in text, text
