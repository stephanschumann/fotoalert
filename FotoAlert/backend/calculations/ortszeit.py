"""US-138 (Schritt 2) — Ortszeit fuer Orte in England.

Einfache, bewusst kleine Regel statt einer Zeitzonen-Datenbank:

* "England-Ort" = Koordinaten im Kasten 49,8-55,9 Grad N / 5,8 Grad W - 1,8 Grad O,
  abzueglich der franzoesischen Kanalkueste (Laenge > 0,9 Grad O UND Breite < 50,85 Grad N:
  Dieppe, Boulogne). Dort gilt Londoner Ortszeit (GMT/BST).
* Alle anderen Orte (Deutschland, Norwegen, ...) bleiben bei ihrem bisherigen Verhalten.

Die Regel steht identisch im Frontend (web/index.html, zoneForCoords); ein Test
(test_us138_ortszeit.py) prueft beide gegen dieselbe Punkttabelle.

Grenzfaelle (bewusst akzeptiert): Wales, Isle of Man und Nordirland liegen im Kasten und haben
dieselbe Uhrzeit wie London; die Republik Irland (Dublin) und Schottland nordlich 55,9 Grad
(Edinburgh) liegen ausserhalb.

Sommerzeit Grossbritannien (BST): von letztem Sonntag im Maerz 01:00 UTC bis letztem Sonntag
im Oktober 01:00 UTC (gilt seit 1996 unveraendert). Python 3.9-kompatibel, ohne zoneinfo.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

ENGLAND_LAT_MIN = 49.8
ENGLAND_LAT_MAX = 55.9
ENGLAND_LON_MIN = -5.8
ENGLAND_LON_MAX = 1.8
# Franzoesische Kanalkueste, die der Kasten sonst mit einschliessen wuerde
_KANAL_LON_AB = 0.9
_KANAL_LAT_UNTER = 50.85


def is_england(lat: Optional[float], lon: Optional[float]) -> bool:
    """True, wenn die Koordinaten als Ort in England (Londoner Zeit) gelten."""
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False
    if lat != lat or lon != lon:  # NaN
        return False
    if not (ENGLAND_LAT_MIN <= lat <= ENGLAND_LAT_MAX and ENGLAND_LON_MIN <= lon <= ENGLAND_LON_MAX):
        return False
    if lon > _KANAL_LON_AB and lat < _KANAL_LAT_UNTER:
        return False
    return True


def _last_sunday(year: int, month: int) -> date:
    d = date(year + (month == 12), (month % 12) + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() + 1) % 7)


def london_utc_offset_hours(dt: datetime) -> int:
    """Abstand Londoner Ortszeit zu UTC in Stunden (0 = GMT, 1 = BST) zum Zeitpunkt dt (UTC)."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    start = datetime.combine(_last_sunday(dt.year, 3), datetime.min.time()) + timedelta(hours=1)
    ende = datetime.combine(_last_sunday(dt.year, 10), datetime.min.time()) + timedelta(hours=1)
    return 1 if start <= dt < ende else 0


def london_hhmm(dt: datetime) -> str:
    """Londoner Ortszeit (HH:MM) fuer einen UTC-Zeitpunkt."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return (dt + timedelta(hours=london_utc_offset_hours(dt))).strftime("%H:%M")
