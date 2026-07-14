"""
Wetter-Integration via Open-Meteo API.
Kostenlos, kein API-Key nötig, sehr präzise für Deutschland.

Liefert:
- Wolkenbedeckung (0–100%)
- Sichtweite (m)
- Niederschlagswahrscheinlichkeit
- Windstärke und -richtung
- Wetter-Score für Fotografie (0–1)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

import httpx


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
"""US-130: Separate Open-Meteo Air Quality API (CAMS-Aerosolvorhersage), liefert
aerosol_optical_depth (Dunst-/Aerosol-Signal) — nicht Teil der Standard-Forecast-API."""


@dataclass
class HourlyWeather:
    time: datetime
    cloud_cover_pct: float          # 0–100
    cloud_cover_low_pct: float      # Niedrige Wolken
    cloud_cover_mid_pct: float      # Mittlere Wolken
    cloud_cover_high_pct: float     # Cirrus (dünn, fotogen!)
    visibility_m: float             # Sichtweite in Metern
    precipitation_mm: float         # Niederschlag
    precipitation_prob_pct: float   # Wahrscheinlichkeit Niederschlag
    wind_speed_kmh: float
    wind_direction_deg: float
    temperature_c: float
    dew_point_c: float
    weather_code: int               # WMO Code


@dataclass
class WeatherForecast:
    location_lat: float
    location_lon: float
    fetched_at: datetime
    hourly: list[HourlyWeather]

    def get_at(self, dt: datetime) -> Optional[HourlyWeather]:
        """Nächste Stunde zum gesuchten Zeitpunkt."""
        if not self.hourly:
            return None
        target = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        best = min(self.hourly, key=lambda h: abs((h.time - target).total_seconds()))
        return best

    def get_window(self, start: datetime, end: datetime) -> list[HourlyWeather]:
        """Wetterdaten für ein Zeitfenster."""
        s = start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start
        e = end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end
        return [h for h in self.hourly if s <= h.time <= e]


@dataclass
class HourlyAerosol:
    """US-130: Ein Aerosol-Datenpunkt (nur das für RED_SKY relevante Signal)."""
    time: datetime
    aerosol_optical_depth: Optional[float]  # Aerosol-Optische-Dicke bei 550 nm, dimensionslos


@dataclass
class AerosolForecast:
    """US-130: Ergebnis von fetch_aerosol_forecast(), analog zu WeatherForecast."""
    location_lat: float
    location_lon: float
    fetched_at: datetime
    hourly: list[HourlyAerosol]

    def get_at(self, dt: datetime) -> Optional[HourlyAerosol]:
        """Nächste Stunde zum gesuchten Zeitpunkt (analog zu WeatherForecast.get_at)."""
        if not self.hourly:
            return None
        target = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        best = min(self.hourly, key=lambda h: abs((h.time - target).total_seconds()))
        return best


def calculate_photo_weather_score(hw: HourlyWeather) -> float:
    """
    Berechnet einen Foto-Wetter-Score (0–1).

    Ideales Fotowetter:
    - Klarer Himmel oder dramatische Wolken (nicht geschlossen grau)
    - Gute Sichtweite
    - Kein Regen
    - Leichter Wind (Spiegelungen)

    Score-Faktoren:
    - Niederschlag: starker Malus
    - Wolkenbedeckung: partiell gut (Dramatik), voll bedeckt schlecht
    - Sichtweite: je weiter, desto besser
    - Hohe Cirrus-Wolken: Bonus (färben sich bei Sonnenuntergang)
    """
    score = 1.0

    # Niederschlag: harter Malus
    if hw.precipitation_prob_pct > 70:
        score *= 0.1
    elif hw.precipitation_prob_pct > 40:
        score *= 0.4
    elif hw.precipitation_prob_pct > 20:
        score *= 0.7

    if hw.precipitation_mm > 0.5:
        score *= 0.3

    # Wolkenbedeckung: nicht-linear
    cc = hw.cloud_cover_pct
    if cc < 10:
        cloud_score = 0.9   # Klarer Himmel – gut, aber wenig Dramatik
    elif cc < 30:
        cloud_score = 1.0   # Ideal: vereinzelte Wolken, goldene Stunde leuchtet
    elif cc < 60:
        cloud_score = 0.85  # Teilbewölkt – kann sehr dramatisch sein
    elif cc < 80:
        cloud_score = 0.5   # Überwiegend bewölkt
    else:
        cloud_score = 0.2   # Geschlossen bedeckt – kein Licht
    score *= cloud_score

    # Bonus für hohe Cirrus-Wolken (leuchtend bei goldener Stunde)
    if hw.cloud_cover_high_pct > 20 and hw.cloud_cover_low_pct < 30:
        score *= 1.15

    # Sichtweite
    vis = hw.visibility_m
    if vis > 20000:
        score *= 1.0
    elif vis > 10000:
        score *= 0.95
    elif vis > 5000:
        score *= 0.8
    elif vis > 2000:
        score *= 0.6
    else:
        score *= 0.3  # Nebel/Dunst

    return round(min(1.0, score), 2)


def _golden_cloud_score(cl: Optional[float], cm: Optional[float], ch: Optional[float]) -> Optional[float]:
    """
    US-07: Private Wrapper mit None-Handling.
    Gibt None zurück wenn ein Input None ist.
    """
    if cl is None or cm is None or ch is None:
        return None
    return calculate_golden_cloud_score(cl, cm, ch)


def calculate_golden_cloud_score(cl: float, cm: float, ch: float) -> float:
    """
    US-07: Berechnet Goldene-Wolken-Score für Goldene Stunde (0.0–1.0).

    Tiefe Wolken blockieren das Licht komplett → starker Malus.
    Mittlere und hohe Wolken reflektieren und färben das Licht golden → Sweet Spot.

    Args:
        cl: cloudcover_low 0–100 % (tiefe Wolken)
        cm: cloudcover_mid 0–100 % (mittlere Wolken)
        ch: cloudcover_high 0–100 % (Cirrus)

    Returns:
        Score 0.0–1.0
    """
    # Tiefe Wolken blockieren das Licht vollständig
    if cl > 80:
        return 0.10

    # Mittlere + hohe Bewölkung zusammen
    mid_high = (cm + ch) / 2.0

    # Klarer Himmel: kaum etwas zum Einfärben
    if mid_high < 10:
        return 0.20

    # Gleichmäßige Decke: diffuses Licht ohne Dramatik
    if mid_high > 90:
        return 0.25

    # Sweet Spot: 25–65 % mittlere+hohe Wolken, tiefe Wolken < 30 %
    if 25 <= mid_high <= 65 and cl < 30:
        base_score = 0.70 + (mid_high - 25) / (65 - 25) * 0.30
    else:
        # Außerhalb Sweet Spot: linearer Score aus mid_high
        base_score = 0.30 + mid_high / 100.0 * 0.40

    # Penalty: exponentiell für tiefe Wolken über 30 %
    if cl > 30:
        penalty = ((cl - 30) / 70.0) ** 2
        base_score *= (1.0 - penalty)

    return round(max(0.0, min(1.0, base_score)), 3)


CLOUD_MOOD_PROJECTION_DISTANCE_M = 30_000
"""
US-131: Projektionsdistanz (Meter) entlang der Sichtachse, an der die Wolkenwerte fuer
GOLDEN_CLOUDS (Sonnenrichtung) und RED_SKY (Gegenrichtung/Antisolarpunkt) sowie der
Dunst-/Aerosolwert fuer RED_SKY (ebenfalls Gegenrichtung) abgefragt werden — statt am
Fotografen-Standort. Feste, pauschale Konstante (keine trigonometrische Herleitung wie bei
sun_pipeline.py/moon_pipeline.py, da die Wetter-/Aerosol-API keinen Anhaltspunkt fuer die
tatsaechliche Entfernung des Wolken-/Dunstsignals liefert). Wert 30 km: mittlere Option aus
dem Ticket-Vorschlag (20-50 km), von Stephan im Weg-Gate am 2026-07-13 bestaetigt (siehe
BACKLOG.md US-131). Gemeinsame Konstante fuer alle drei Projektionen (ersetzt die
urspruenglich fuer Option A vorgesehene RED_SKY_PROJECTION_DISTANCE_M).
"""


def should_generate_golden_clouds_event(
    gcs: float,
    sun_azimuth: float,
    subject_azimuth: float,
) -> bool:
    """
    US-109: Prüft ob ein GOLDEN_CLOUDS-Event erzeugt werden soll.

    Bedingungen:
    - golden_cloud_score >= 0.70
    - Azimut-Differenz zwischen Sonnenposition und Motivrichtung <= 30°
      (Sonne scheint aus Motivrichtung → Wolken werden von vorne beleuchtet)

    Args:
        gcs:              Golden Cloud Score (0.0–1.0)
        sun_azimuth:      Sonnen-Azimut in Grad (0–360, 0=Nord im Uhrzeigersinn)
        subject_azimuth:  Motiv-Azimut vom Standpunkt aus (0–360)

    Returns:
        True wenn GOLDEN_CLOUDS-Event erzeugt werden soll
    """
    if gcs < 0.70:
        return False
    diff = abs(sun_azimuth - subject_azimuth) % 360
    if diff > 180:
        diff = 360 - diff
    return diff <= 30


RED_SKY_AZIMUTH_TOLERANCE_DEG = 30
"""
US-113: Toleranzwinkel für den Sonnenazimut-Sichtachsen-Filter bei RED_SKY.
Eigene, unabhängig änderbare Konstante (nicht an GOLDEN_CLOUDS' 30°-Wert gekoppelt,
auch wenn sie initial denselben Wert hat) — siehe Implementierungsoption A, US-113.
"""

RED_SKY_AOD_THRESHOLD = 0.3
"""
US-130: Schwellenwert für die Aerosol-Optische-Dicke (aerosol_optical_depth, 550 nm),
ab dem ein signifikanter Dunst-/Aerosolwert vorliegt (inklusiv, >=). Startwert ohne
empirische Kalibrierung für Berlin/Brandenburg — bewusst als eigene, benannte Konstante
gehalten, um sie nach Live-Beobachtung nachjustieren zu können (siehe BACKLOG.md US-130,
Pre-Mortem Szenario 2, von Stephan im Weg-Gate am 2026-07-12 bestätigt).
"""


def should_generate_red_sky_event(
    gcs: float,
    cl: float,
    cm: float,
    sun_azimuth: Optional[float] = None,
    subject_azimuth: Optional[float] = None,
    aerosol_optical_depth: Optional[float] = None,
) -> bool:
    """
    US-109 / US-113 / US-130: Prüft ob ein RED_SKY-Event erzeugt werden soll.

    Bedingungen:
    - golden_cloud_score >= 0.80
    - Azimut-Differenz zwischen Motivrichtung und dem GEGENPUNKT der Sonne
      <= RED_SKY_AZIMUTH_TOLERANCE_DEG (siehe Korrektur unten, US-113)
    - US-130 (ODER-Verknüpfung, Option B): mindestens EINE der beiden Bedingungen muss
      zusätzlich erfüllt sein —
        (a) cloud_cover_low + cloud_cover_mid >= 60 % (dominante tiefe/mittlere Bewölkung,
            der Gesamthimmel rötet sich, nicht nur Cirrus-Schleier), ODER
        (b) aerosol_optical_depth >= RED_SKY_AOD_THRESHOLD (signifikanter Dunst/Aerosol,
            klassischer Gegendämmerungsbogen/"Belt of Venus"-Effekt auch bei wolkenarmem,
            aber diesigem Himmel — siehe BACKLOG.md US-130)
      Ist die Wolkenbedingung bereits erfüllt, ändert sich am Auslöseverhalten nichts
      (Regression, unabhängig vom Aerosolwert). Fehlt aerosol_optical_depth (Abruf nicht
      verfügbar/fehlgeschlagen), verhält sich die Funktion identisch zum reinen
      Wolken-Check (kein Fehler, kein Absturz — AK-6).

    US-113-Korrektur (2026-07-02, fachlicher Analysefehler behoben):
    Himmelsröte (Gegendämmerung, "Belt of Venus") entsteht am GEGENPUNKT der Sonne
    (Antisolarpunkt = sun_azimuth + 180°), NICHT am Sonnenazimut selbst wie bei
    GOLDEN_CLOUDS (Alpenglühen, direktes Streulicht rund um die Sonne). Die ursprüngliche
    Implementierung verglich subject_azimuth fälschlich direkt gegen sun_azimuth (1:1
    von GOLDEN_CLOUDS übernommen) — das ist geometrisch falsch für RED_SKY. Quellen:
    https://de.wikipedia.org/wiki/Gegend%C3%A4mmerung, https://en.wikipedia.org/wiki/Belt_of_Venus

    Ohne sun_azimuth oder subject_azimuth (z. B. Location ohne definiertes Motiv) ist kein
    Richtungsvergleich möglich → kein RED_SKY-Event (analog zum GOLDEN_CLOUDS-Verhalten).
    Diese Bedingung gilt unverändert auch für den neuen Aerosol-Zweig (US-130) — ohne
    Richtungsvergleich kein RED_SKY-Event, unabhängig vom Auslöser.

    Args:
        gcs:                    Golden Cloud Score (0.0–1.0)
        cl:                     cloud_cover_low in Prozent (0–100)
        cm:                     cloud_cover_mid in Prozent (0–100)
        sun_azimuth:            Sonnen-Azimut in Grad (0–360, 0=Nord im Uhrzeigersinn), optional
        subject_azimuth:        Motiv-Azimut vom Standpunkt aus (0–360), optional
        aerosol_optical_depth:  Aerosol-Optische-Dicke (550 nm), optional (US-130)

    Returns:
        True wenn RED_SKY-Event erzeugt werden soll
    """
    if gcs < 0.80:
        return False
    if sun_azimuth is None or subject_azimuth is None:
        return False
    # Gegendämmerung/Belt of Venus: die Himmelsröte liegt gegenüber der Sonne, nicht bei ihr.
    antisolar_azimuth = (sun_azimuth + 180) % 360
    diff = abs(antisolar_azimuth - subject_azimuth) % 360
    if diff > 180:
        diff = 360 - diff
    if diff > RED_SKY_AZIMUTH_TOLERANCE_DEG:
        return False

    cloud_condition = (cl + cm) >= 60
    aerosol_condition = (
        aerosol_optical_depth is not None
        and aerosol_optical_depth >= RED_SKY_AOD_THRESHOLD
    )
    return cloud_condition or aerosol_condition


RED_CLOUDS_AZIMUTH_TOLERANCE_DEG = 30
"""
US-132: Toleranzwinkel für den Sonnenazimut-Sichtachsen-Filter bei RED_CLOUDS.
Eigene, unabhängig änderbare Konstante (nicht an GOLDEN_CLOUDS'/RED_SKY's 30°-Wert
gekoppelt, auch wenn sie initial denselben Wert hat) — siehe BACKLOG.md US-132,
Annahmen-Protokoll.
"""

RED_CLOUDS_HIGH_CLOUD_THRESHOLD_PCT = 20
"""
US-132: Schwellenwert für cloud_cover_high_pct (in Prozent, inklusiv >=), ab dem
genug hohe Wolken (Cirrus) für ein RED_CLOUDS-Event vorhanden sind. Startwert ohne
empirische Kalibrierung, bewusst als eigene, benannte Konstante gehalten (analog
RED_SKY_AOD_THRESHOLD), um sie nach Live-Beobachtung nachjustieren zu können
(siehe BACKLOG.md US-132, von Stephan im Weg-Gate am 2026-07-13 bestätigt).
"""

RED_CLOUDS_LOW_CLOUD_CAP_PCT = 30
"""
US-132: Deckel für cloud_cover_low_pct (in Prozent, exklusiv <), oberhalb dessen
tiefe Wolken die Sicht auf die hohen Wolken als komplett verstellt gelten (Edge
Case AK-5) — verhindert eine "Rote Wolken"-Meldung bei komplett zugezogenem
Himmel. Identisches Muster wie der bestehende Cirrus-Bonus in
calculate_photo_weather_score() (Sweet-Spot-Deckel cl < 30).
"""


def should_generate_red_clouds_event(
    sun_altitude: float,
    ch: float,
    cl: float,
    sun_azimuth: Optional[float] = None,
    subject_azimuth: Optional[float] = None,
) -> bool:
    """
    US-132: Prüft ob ein RED_CLOUDS-Event ("Rote Wolken") erzeugt werden soll.

    Physikalisch eigenständiges drittes Wolkenstimmungs-Phänomen neben GOLDEN_CLOUDS
    (Sonne über Horizont) und RED_SKY (Antisolarpunkt-Richtung): Steht die Sonne
    bereits unter dem Horizont (Blaue-Stunde-Fenster), können hohe Wolken (Cirrus)
    noch aus der Sonnenrichtung angestrahlt werden und sich rot/purpurn färben.

    Bedingungen (siehe BACKLOG.md US-132, Rules 1-4):
    - sun_altitude < 0 (Sonne unter dem Horizont — explizit geprüft, nicht nur über
      den Event-Typ-Namen abgeleitet, siehe Pre-Mortem Szenario 1)
    - ch (cloud_cover_high_pct) >= RED_CLOUDS_HIGH_CLOUD_THRESHOLD_PCT
    - cl (cloud_cover_low_pct) < RED_CLOUDS_LOW_CLOUD_CAP_PCT (Edge Case AK-5: tiefe
      Wolken dürfen die Sicht nicht komplett verstellen)
    - Azimut-Differenz zwischen Sonnenposition und Motivrichtung
      <= RED_CLOUDS_AZIMUTH_TOLERANCE_DEG (Sonnenrichtung, NICHT Antisolarpunkt wie
      bei RED_SKY, siehe Edge Case AK-6)

    Ohne sun_azimuth oder subject_azimuth (z. B. Location ohne definiertes Motiv oder
    fehlende celestial_azimuth-Berechnung) ist kein Richtungsvergleich möglich → kein
    RED_CLOUDS-Event (analog GOLDEN_CLOUDS/RED_SKY-Verhalten).

    Args:
        sun_altitude:     Sonnenhöhe in Grad zum Aufnahmezeitpunkt (negativ = unter
                           dem Horizont)
        ch:               cloud_cover_high_pct in Prozent (0-100)
        cl:               cloud_cover_low_pct in Prozent (0-100)
        sun_azimuth:      Sonnen-Azimut in Grad (0-360, 0=Nord im Uhrzeigersinn), optional
        subject_azimuth:  Motiv-Azimut vom Standpunkt aus (0-360), optional

    Returns:
        True wenn RED_CLOUDS-Event erzeugt werden soll
    """
    if sun_altitude >= 0:
        return False
    if ch < RED_CLOUDS_HIGH_CLOUD_THRESHOLD_PCT:
        return False
    if cl >= RED_CLOUDS_LOW_CLOUD_CAP_PCT:
        return False
    if sun_azimuth is None or subject_azimuth is None:
        return False

    diff = abs(sun_azimuth - subject_azimuth) % 360
    if diff > 180:
        diff = 360 - diff
    return diff <= RED_CLOUDS_AZIMUTH_TOLERANCE_DEG


def wmo_code_to_description(code: int) -> str:
    """WMO Wettercodes zu Beschreibung."""
    codes = {
        0: "Klarer Himmel",
        1: "Überwiegend klar",
        2: "Teilweise bewölkt",
        3: "Bedeckt",
        45: "Nebel",
        48: "Gefrierender Nebel",
        51: "Leichter Nieselregen",
        53: "Mäßiger Nieselregen",
        55: "Starker Nieselregen",
        61: "Leichter Regen",
        63: "Mäßiger Regen",
        65: "Starker Regen",
        71: "Leichter Schneefall",
        73: "Mäßiger Schneefall",
        75: "Starker Schneefall",
        80: "Leichte Regenschauer",
        81: "Mäßige Regenschauer",
        82: "Starke Regenschauer",
        95: "Gewitter",
        96: "Gewitter mit leichtem Hagel",
        99: "Gewitter mit schwerem Hagel",
    }
    return codes.get(code, f"Wetter-Code {code}")


async def fetch_weather_forecast(lat: float, lon: float, days: int = 7) -> WeatherForecast:
    """
    Holt stündliche Wettervorhersage von Open-Meteo.
    Kein API-Key nötig. Bis zu 16 Tage im Voraus.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "temperature_2m",
            "dew_point_2m",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "cloud_cover",
            "cloud_cover_low",
            "cloud_cover_mid",
            "cloud_cover_high",
            "visibility",
            "wind_speed_10m",
            "wind_direction_10m",
        ],
        "forecast_days": min(days, 16),
        "timezone": "UTC",           # UTC statt Europe/Berlin → kein Timezone-Offset-Bug
        "wind_speed_unit": "kmh",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(OPEN_METEO_URL, params=params)
        response.raise_for_status()
        data = response.json()

    hourly = data["hourly"]
    times = [
        # Open-Meteo gibt bei timezone=UTC Strings wie "2026-06-14T14:00" zurück (keine Offset-Angabe)
        # → naive datetime korrekt als UTC taggen
        datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
        for t in hourly["time"]
    ]

    weather_list = []
    for i, t in enumerate(times):
        hw = HourlyWeather(
            time=t,
            cloud_cover_pct=hourly["cloud_cover"][i] or 0,
            cloud_cover_low_pct=hourly["cloud_cover_low"][i] or 0,
            cloud_cover_mid_pct=hourly["cloud_cover_mid"][i] or 0,
            cloud_cover_high_pct=hourly["cloud_cover_high"][i] or 0,
            visibility_m=hourly["visibility"][i] or 0,
            precipitation_mm=hourly["precipitation"][i] or 0,
            precipitation_prob_pct=hourly["precipitation_probability"][i] or 0,
            wind_speed_kmh=hourly["wind_speed_10m"][i] or 0,
            wind_direction_deg=hourly["wind_direction_10m"][i] or 0,
            temperature_c=hourly["temperature_2m"][i] or 0,
            dew_point_c=hourly["dew_point_2m"][i] or 0,
            weather_code=hourly["weather_code"][i] or 0,
        )
        weather_list.append(hw)

    return WeatherForecast(
        location_lat=lat,
        location_lon=lon,
        fetched_at=datetime.now(timezone.utc),
        hourly=weather_list,
    )


async def fetch_aerosol_forecast(lat: float, lon: float, days: int = 7) -> AerosolForecast:
    """
    US-130: Holt stündliche Aerosol-/Dunst-Vorhersage (aerosol_optical_depth) von der
    separaten Open-Meteo Air Quality API (analog zu fetch_weather_forecast(), anderer
    Hostname/Endpunkt). Kein API-Key nötig, kostenlos.

    domains=cams_global wird explizit gesetzt. Live-Verifikation in der Testphase
    (2026-07-12) zeigte: das feinere cams_europe-Regionalmodell liefert für
    aerosol_optical_depth an Berlin/Brandenburg-Koordinaten durchgängig null (Rohantwort
    der API geprüft) — das globale CAMS-Modell (~45 km Auflösung) liefert dagegen reale
    Werte. Das passt inhaltlich auch besser zum Ticket-Anlass (Viewfindr-Vergleichsfall:
    weiträumige, nicht an lokale Wolkenfelder gebundene Dunst-Rotfärbung). Ursprünglich war
    cams_europe vorgesehen (siehe Pre-Mortem Szenario 3, Sorge vor Sprüngen an der
    Domain-Grenze) — diese Annahme war unzutreffend, da cams_europe hier keine Daten liefert,
    nicht nur eine feinere Auflösung. Gültige Werte laut Open-Meteo Air Quality API: "auto",
    "cams_europe", "cams_global" — "europe" (ohne Präfix) ist KEIN gültiger Wert und löste
    zuvor einen 400 Bad Request aus (erster Live-Fund der Testphase, 2026-07-12).
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["aerosol_optical_depth"],
        "domains": "cams_global",
        "forecast_days": min(days, 16),
        "timezone": "UTC",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(AIR_QUALITY_URL, params=params)
        response.raise_for_status()
        data = response.json()

    hourly = data["hourly"]
    times = [
        datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
        for t in hourly["time"]
    ]

    aerosol_list = []
    for i, t in enumerate(times):
        aod = hourly["aerosol_optical_depth"][i]
        aerosol_list.append(HourlyAerosol(time=t, aerosol_optical_depth=aod))

    return AerosolForecast(
        location_lat=lat,
        location_lon=lon,
        fetched_at=datetime.now(timezone.utc),
        hourly=aerosol_list,
    )


def is_golden_hour_weather_good(
    forecast: WeatherForecast,
    golden_hour_start: datetime,
    golden_hour_end: datetime,
    min_score: float = 0.5,
) -> tuple[bool, float]:
    """
    Prüft ob das Wetter während der goldenen Stunde gut genug ist.
    Gibt (gut_genug, durchschnittlicher_score) zurück.
    """
    window = forecast.get_window(golden_hour_start, golden_hour_end)
    if not window:
        return False, 0.0

    scores = [calculate_photo_weather_score(h) for h in window]
    avg_score = sum(scores) / len(scores)
    return avg_score >= min_score, round(avg_score, 2)
