"""
find_duplicates.py — US-25: Locations mit ähnlichem GPS-Standort finden.

Verwendung:
    cd FotoAlert/backend
    python3 tools/find_duplicates.py          # Tabellen-Output
    python3 tools/find_duplicates.py --json   # JSON-Output

Vergleicht alle Locations (Base + Custom) paarweise per Haversine (observer_lat/lon).
Zeigt Paare mit Abstand < 300 m.
Empfehlung:
    „Löschen prüfen"        → Abstand < 50 m UND Azimut-Diff < 20°
    „Zusammenführen prüfen" → sonst
Locations ohne ideal_azimuth_range werden beim Azimut-Vergleich übersprungen
(Paar erscheint trotzdem im Report, Azimut-Diff = „–").
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Optional

# Pfad-Setup so dass Backend-Module importierbar sind
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.locations import LOCATIONS
from data.store import LocationStore as Store


# ---------------------------------------------------------------------------
# Haversine
# ---------------------------------------------------------------------------

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Gibt Abstand in Metern zurück (observer-to-observer)."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Azimut-Differenz
# ---------------------------------------------------------------------------

def _azimuth_diff(
    r1: Optional[tuple[float, float]],
    r2: Optional[tuple[float, float]],
) -> Optional[float]:
    """Gibt Differenz der Azimut-Mitten in Grad zurück, oder None wenn eine Range fehlt."""
    if r1 is None or r2 is None:
        return None
    mid1 = (r1[0] + r1[1]) / 2
    mid2 = (r2[0] + r2[1]) / 2
    diff = abs(mid1 - mid2)
    return min(diff, 360 - diff)  # kürzester Winkel


# ---------------------------------------------------------------------------
# Empfehlung
# ---------------------------------------------------------------------------

def _recommendation(distance_m: float, az_diff: Optional[float]) -> str:
    if distance_m < 50 and az_diff is not None and az_diff < 20:
        return "Löschen prüfen"
    return "Zusammenführen prüfen"


# ---------------------------------------------------------------------------
# Locations laden (Base + Overrides + Custom)
# ---------------------------------------------------------------------------

def _load_locations() -> list[dict]:
    """Gibt Liste von dicts mit id, name, observer_lat, observer_lon, ideal_azimuth_range."""

    store = Store()

    # 1. Base-Locations als dicts
    locs: dict[str, dict] = {}
    for loc in LOCATIONS:
        locs[loc.id] = {
            "id": loc.id,
            "name": loc.name,
            "observer_lat": loc.observer_lat,
            "observer_lon": loc.observer_lon,
            "ideal_azimuth_range": loc.ideal_azimuth_range,
            "source": "base",
        }

    # 2. Overrides anwenden (Tombstones herausfiltern)
    overrides = store.load_all_overrides()
    tombstoned = {ov["id"] for ov in overrides if ov.get("deleted")}
    for oid in tombstoned:
        locs.pop(oid, None)

    for ov in overrides:
        loc_id = ov.get("id")
        if ov.get("deleted") or loc_id not in locs:
            continue
        for field in ("observer_lat", "observer_lon", "name"):
            if field in ov:
                locs[loc_id][field] = ov[field]

    # 3. Custom-Locations aus DB
    for entry in store.load_all_custom():
        az = None
        # Custom-Locations haben kein ideal_azimuth_range-Feld in der DB
        locs[entry["id"]] = {
            "id": entry["id"],
            "name": entry.get("name", entry["id"]),
            "observer_lat": entry["observer_lat"],
            "observer_lon": entry["observer_lon"],
            "ideal_azimuth_range": az,
            "source": "custom",
        }

    return list(locs.values())


# ---------------------------------------------------------------------------
# Duplikat-Suche
# ---------------------------------------------------------------------------

THRESHOLD_M = 300      # Paare unterhalb dieser Distanz erscheinen im Report
MERGE_THRESHOLD_M = 50  # Unterhalb + AZ-Diff < 20° → „Löschen prüfen"
MERGE_THRESHOLD_AZ = 20


def find_pairs(locs: list[dict]) -> list[dict]:
    pairs = []
    for i in range(len(locs)):
        for j in range(i + 1, len(locs)):
            a, b = locs[i], locs[j]
            dist = _haversine(a["observer_lat"], a["observer_lon"],
                              b["observer_lat"], b["observer_lon"])
            if dist >= THRESHOLD_M:
                continue
            az_diff = _azimuth_diff(a["ideal_azimuth_range"], b["ideal_azimuth_range"])
            pairs.append({
                "name_a": a["name"],
                "name_b": b["name"],
                "distance_m": round(dist),
                "azimuth_diff_deg": round(az_diff, 1) if az_diff is not None else None,
                "recommendation": _recommendation(dist, az_diff),
            })
    pairs.sort(key=lambda p: p["distance_m"])
    return pairs


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _table(pairs: list[dict]) -> None:
    if not pairs:
        print("Keine Duplikate gefunden.")
        return

    col_a = max(len(p["name_a"]) for p in pairs)
    col_b = max(len(p["name_b"]) for p in pairs)
    col_a = max(col_a, 10)
    col_b = max(col_b, 10)

    header = (
        f"{'Location A':<{col_a}}  {'Location B':<{col_b}}  "
        f"{'Abstand':>8}  {'Az-Diff':>8}  Empfehlung"
    )
    print(header)
    print("-" * len(header))

    for p in pairs:
        az = f"{p['azimuth_diff_deg']}°" if p["azimuth_diff_deg"] is not None else "–"
        print(
            f"{p['name_a']:<{col_a}}  {p['name_b']:<{col_b}}  "
            f"{p['distance_m']:>6} m  {az:>8}  {p['recommendation']}"
        )


def _json_out(pairs: list[dict]) -> None:
    print(json.dumps(pairs, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="FotoAlert Duplikat-Finder (US-25)")
    parser.add_argument("--json", action="store_true", help="JSON statt Tabelle ausgeben")
    args = parser.parse_args()

    locs = _load_locations()
    pairs = find_pairs(locs)

    if args.json:
        _json_out(pairs)
    else:
        print(f"\nFotoAlert Duplikat-Finder — {len(locs)} Locations geladen\n")
        _table(pairs)
        if pairs:
            print(f"\n{len(pairs)} Paar(e) gefunden (Schwelle: {THRESHOLD_M} m).")
        print()


if __name__ == "__main__":
    main()
