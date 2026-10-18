"""BUG-117: Zwischenspeicher und Tagesstand für die Wetterabrufe beim Wetterdienst (Open-Meteo).

Zwei kleine Dateien im Cache-Ordner des Servers:

  - weather_forecast_cache.json  Zwischenspeicher der zuletzt erfolgreich geholten Vorhersagen (je Abrufart und
    Punkt). Überlebt einen Neustart. Wer schon frisch genug ist, wird beim nächsten Lauf nicht erneut abgefragt.
  - weather_tagesstand.json      Zähler des laufenden Tages (UTC-Tag): Anfragen, abgelehnte Anfragen, gewichteter
    Verbrauch, getrennt für Ortswetter und Entdecken (Scout). Überlebt einen Neustart.

Beide Dateien werden atomar geschrieben (data/cache_io.py). Fehlt eine Datei oder ist sie unlesbar, ist das kein
Fehler: dann gibt es keinen Zwischenspeicher bzw. der Tag beginnt bei null.

Nur Standardbibliothek plus die Wetter-Datenklassen. Python 3.9-kompatibel.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from calculations.weather import AerosolForecast, HourlyAerosol, HourlyWeather, WeatherForecast
from data.cache_io import atomar_schreiben

logger = logging.getLogger(__name__)

SPEICHER_DATEI = "weather_forecast_cache.json"
TAGESSTAND_DATEI = "weather_tagesstand.json"

MAX_ALTER_S = 24 * 3600
"""Einträge, die älter sind, werden beim Speichern entfernt (der Zwischenspeicher wächst nicht unbegrenzt)."""

GEWICHT_WETTER = 1.2
"""Gewicht einer Wetterabfrage beim Tageslimit: die Abfrage holt 12 Größen; ab mehr als 10 Größen zählt sie laut
Preisseite von Open-Meteo mehrfach (15 Größen = 1,5 Abrufe). 12 Größen ergeben rechnerisch 1,2 (Annahme)."""
GEWICHT_AEROSOL = 1.0
"""Die Luftdunst-Abfrage holt 1 Größe, zählt also einfach."""
TAGESLIMIT = 10_000
"""Kostenloses Tageslimit von Open-Meteo (Preisseite, gelesen 2026-10-18)."""


# ---------------------------------------------------------------------------
# Vorhersagen <-> JSON
# ---------------------------------------------------------------------------

def forecast_zu_json(fc) -> dict:
    """Wandelt eine Wetter- oder Dunst-Vorhersage in ein kompaktes JSON-Wörterbuch (eine Zeile je Stunde)."""
    if isinstance(fc, AerosolForecast):
        return {
            "typ": "a", "lat": fc.location_lat, "lon": fc.location_lon, "t": fc.fetched_at.timestamp(),
            "h": [[h.time.timestamp(), h.aerosol_optical_depth] for h in fc.hourly],
        }
    return {
        "typ": "w", "lat": fc.location_lat, "lon": fc.location_lon, "t": fc.fetched_at.timestamp(),
        "h": [[h.time.timestamp(), h.cloud_cover_pct, h.cloud_cover_low_pct, h.cloud_cover_mid_pct,
               h.cloud_cover_high_pct, h.visibility_m, h.precipitation_mm, h.precipitation_prob_pct,
               h.wind_speed_kmh, h.wind_direction_deg, h.temperature_c, h.dew_point_c, h.weather_code]
              for h in fc.hourly],
    }


def forecast_aus_json(d: dict):
    """Gegenstück zu forecast_zu_json(). Wirft bei kaputten Daten eine Ausnahme (Aufrufer behandelt das als 'nicht im
    Zwischenspeicher')."""
    fetched = datetime.fromtimestamp(float(d["t"]), tz=timezone.utc)
    if d["typ"] == "a":
        return AerosolForecast(
            location_lat=d["lat"], location_lon=d["lon"], fetched_at=fetched,
            hourly=[HourlyAerosol(time=datetime.fromtimestamp(r[0], tz=timezone.utc), aerosol_optical_depth=r[1])
                    for r in d["h"]],
        )
    return WeatherForecast(
        location_lat=d["lat"], location_lon=d["lon"], fetched_at=fetched,
        hourly=[HourlyWeather(
            time=datetime.fromtimestamp(r[0], tz=timezone.utc), cloud_cover_pct=r[1], cloud_cover_low_pct=r[2],
            cloud_cover_mid_pct=r[3], cloud_cover_high_pct=r[4], visibility_m=r[5], precipitation_mm=r[6],
            precipitation_prob_pct=r[7], wind_speed_kmh=r[8], wind_direction_deg=r[9], temperature_c=r[10],
            dew_point_c=r[11], weather_code=int(r[12])) for r in d["h"]],
    )


# ---------------------------------------------------------------------------
# Zwischenspeicher
# ---------------------------------------------------------------------------

def speicher_laden(ordner) -> Dict[str, dict]:
    """Liest den Zwischenspeicher. Fehlt er oder ist er unlesbar, kommt ein leeres Wörterbuch zurück."""
    pfad = Path(ordner) / SPEICHER_DATEI
    if not pfad.exists():
        return {}
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
        return daten if isinstance(daten, dict) else {}
    except (OSError, ValueError) as exc:
        logger.warning("BUG-117: Wetter-Zwischenspeicher nicht lesbar (%s), es gilt: leer", exc)
        return {}


def speicher_speichern(ordner, eintraege: Dict[str, dict], jetzt: Optional[float] = None) -> int:
    """Schreibt den Zwischenspeicher atomar; Einträge älter als MAX_ALTER_S entfallen. Gibt die Zahl der
    gespeicherten Einträge zurück."""
    jetzt = time.time() if jetzt is None else jetzt
    behalten = {k: v for k, v in eintraege.items() if jetzt - float(v.get("t", 0)) <= MAX_ALTER_S}
    Path(ordner).mkdir(parents=True, exist_ok=True)
    atomar_schreiben(Path(ordner) / SPEICHER_DATEI, json.dumps(behalten, separators=(",", ":")))
    return len(behalten)


def ist_frisch(eintrag: Optional[dict], max_alter_s: float, jetzt: Optional[float] = None) -> bool:
    jetzt = time.time() if jetzt is None else jetzt
    if not eintrag:
        return False
    try:
        return 0 <= jetzt - float(eintrag["t"]) < max_alter_s
    except (KeyError, TypeError, ValueError):
        return False


def eintrag_aus_forecast(fc) -> dict:
    d = forecast_zu_json(fc)
    return {"t": d["t"], "f": d}


# ---------------------------------------------------------------------------
# Tagesstand
# ---------------------------------------------------------------------------

def _leerer_tag(tag: str) -> dict:
    leer = {"anfragen": 0, "abgelehnt": 0, "gewichtet": 0.0, "laeufe": 0}
    return {"tag": tag, "ortswetter": dict(leer), "scout": dict(leer)}


def _heute_utc(jetzt: Optional[datetime] = None) -> str:
    return (jetzt or datetime.now(timezone.utc)).strftime("%Y-%m-%d")


def tagesstand_lesen(ordner, jetzt: Optional[datetime] = None) -> dict:
    """Aktueller Tagesstand; beginnt ein neuer UTC-Tag oder fehlt die Datei, ist er null."""
    heute = _heute_utc(jetzt)
    pfad = Path(ordner) / TAGESSTAND_DATEI
    try:
        d = json.loads(pfad.read_text(encoding="utf-8"))
        if d.get("tag") == heute and isinstance(d.get("ortswetter"), dict) and isinstance(d.get("scout"), dict):
            return d
    except (OSError, ValueError):
        pass
    return _leerer_tag(heute)


def gewichtet(je_art: Dict[str, int]) -> float:
    """Gewichteter Verbrauch aus den Anfragen je Abrufart."""
    return sum(n * (GEWICHT_AEROSOL if art == "aerosol" else GEWICHT_WETTER) for art, n in je_art.items())


def tagesstand_buchen(ordner, quelle: str, anfragen: int, abgelehnt: int, gewicht: float,
                      jetzt: Optional[datetime] = None) -> dict:
    """Bucht einen Lauf auf den Tagesstand ('ortswetter' oder 'scout'). Gibt den neuen Stand zurück."""
    d = tagesstand_lesen(ordner, jetzt)
    z = d[quelle]
    z["anfragen"] += int(anfragen)
    z["abgelehnt"] += int(abgelehnt)
    z["gewichtet"] = round(z["gewichtet"] + float(gewicht), 1)
    z["laeufe"] += 1
    Path(ordner).mkdir(parents=True, exist_ok=True)
    atomar_schreiben(Path(ordner) / TAGESSTAND_DATEI, json.dumps(d, separators=(",", ":")))
    return d


def tagesstand_text(d: dict) -> str:
    """Kurztext für die Zählzeile, ohne Ortsnamen."""
    gesamt = d["ortswetter"]["gewichtet"] + d["scout"]["gewichtet"]
    anteil = 100.0 * gesamt / TAGESLIMIT
    return ("Tagesstand (UTC-Tag %s): %s gewichtete Abrufe von %s (%s %%) · Ortswetter %s, Entdecken %s · "
            "Läufe heute %d") % (
        d["tag"], ("%.0f" % gesamt), ("{:,}".format(TAGESLIMIT)).replace(",", "."),
        ("%.1f" % anteil).replace(".", ","), ("%.0f" % d["ortswetter"]["gewichtet"]),
        ("%.0f" % d["scout"]["gewichtet"]), d["ortswetter"]["laeufe"])
