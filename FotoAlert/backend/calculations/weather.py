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


def should_generate_red_sky_event(
    gcs: float,
    cl: float,
    cm: float,
    sun_azimuth: Optional[float] = None,
    subject_azimuth: Optional[float] = None,
) -> bool:
    """
    US-109 / US-113: Prüft ob ein RED_SKY-Event erzeugt werden soll.

    Bedingungen:
    - golden_cloud_score >= 0.80
    - cloud_cover_low + cloud_cover_mid >= 60 % (dominante tiefe/mittlere Bewölkung)
      → der Gesamthimmel rötet sich, nicht nur Cirrus-Schleier
    - US-113: Azimut-Differenz zwischen Motivrichtung und dem GEGENPUNKT der Sonne
      <= RED_SKY_AZIMUTH_TOLERANCE_DEG (siehe Korrektur unten)

    US-113-Korrektur (2026-07-02, fachlicher Analysefehler behoben):
    Himmelsröte (Gegendämmerung, "Belt of Venus") entsteht am GEGENPUNKT der Sonne
    (Antisolarpunkt = sun_azimuth + 180°), NICHT am Sonnenazimut selbst wie bei
    GOLDEN_CLOUDS (Alpenglühen, direktes Streulicht rund um die Sonne). Die ursprüngliche
    Implementierung verglich subject_azimuth fälschlich direkt gegen sun_azimuth (1:1
    von GOLDEN_CLOUDS übernommen) — das ist geometrisch falsch für RED_SKY. Quellen:
    https://de.wikipedia.org/wiki/Gegend%C3%A4mmerung, https://en.wikipedia.org/wiki/Belt_of_Venus

    Ohne sun_azimuth oder subject_azimuth (z. B. Location ohne definiertes Motiv) ist kein
    Richtungsvergleich möglich → kein RED_SKY-Event (analog zum GOLDEN_CLOUDS-Verhalten).

    Args:
        gcs:             Golden Cloud Score (0.0–1.0)
        cl:              cloud_cover_low in Prozent (0–100)
        cm:              cloud_cover_mid in Prozent (0–100)
        sun_azimuth:      Sonnen-Azimut in Grad (0–360, 0=Nord im Uhrzeigersinn), optional
        subject_azimuth:  Motiv-Azimut vom Standpunkt aus (0–360), optional

    Returns:
        True wenn RED_SKY-Event erzeugt werden soll
    """
    if gcs < 0.80:
        return False
    if (cl + cm) < 60:
        return False
    if sun_azimuth is None or subject_azimuth is None:
        return False
    # Gegendämmerung/Belt of Venus: die Himmelsröte liegt gegenüber der Sonne, nicht bei ihr.
    antisolar_azimuth = (sun_azimuth + 180) % 360
    diff = abs(antisolar_azimuth - subject_azimuth) % 360
    if diff > 180:
        diff = 360 - diff
    return diff <= RED_SKY_AZIMUTH_TOLERANCE_DEG


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
