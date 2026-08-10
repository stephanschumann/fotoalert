"""
extract_building_data.py — TASK-59 Option E: Batch-Extraktion von OSM-Gebäude-
Footprints aus einem lokalen Geofabrik-PBF-Auszug für die bekannten FotoAlert-
Basis-Locations.

Ersetzt (für diese Locations) die bisherigen Live-Overpass-Anfragen in
`backend/data/qa_azimuth.py` durch eine vorab (z.B. wöchentlich per
GitHub-Actions-Workflow, siehe .github/workflows/update-building-data.yml)
erzeugte lokale Datei, aus der `qa_azimuth.py` primär liest — Live-Anfragen an
die öffentlichen Mirrors bleiben nur noch Fallback für Locations, die (noch)
nicht in dieser Datei stehen.

Verwendung:
    cd FotoAlert/backend
    python3 tools/extract_building_data.py \
        --pbf /pfad/zu/<region>-latest.osm.pbf \
        --output data/cache/building_footprints.json \
        --radius 200

Scope-Grenze (bewusst, siehe TASK-59 BACKLOG.md): Nur die Basis-Locations aus
`data/locations.py` werden exportiert (~60, Stand 2026-08-02) — Custom-
Locations (vom Host über die App angelegt) leben ausschließlich in der
Server-DB und sind diesem git-basierten Workflow nicht zugänglich. Für sie
bleibt der Live-Mirror-Pfad in qa_azimuth.py die einzige Datenquelle.

Architektur: Die eigentliche PBF/osmium-Anbindung (`_iter_ways_from_pbf`) ist
ein dünner Adapter, der NUR beim tatsächlichen CLI-Aufruf gegen eine echte
PBF-Datei importiert wird (lazy `import osmium`, analog zum lazy `import
httpx` in qa_azimuth.py). Die Kernlogik (Radius-Filter, JSON-Struktur-Aufbau)
arbeitet auf einfachen, osmium-unabhängigen Python-Objekten (WayRecord) und
ist dadurch ohne osmium-Installation und ohne echte PBF-Datei offline testbar
(siehe backend/tests/test_extract_building_data.py) — in dieser Sandbox war
kein echter Netzwerkzugriff auf Geofabrik/osmium-Testdaten möglich, daher ist
dieser Trennschnitt Pflicht, nicht nur Stil.

Python-3.9-kompatibel.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, NamedTuple, Optional, Tuple

# Pfad-Setup so dass Backend-Module importierbar sind (analog find_duplicates.py)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Default-Höhe (m) für Gebäude ohne "height"/"building:levels"-Tag in OSM.
# Bewusst identisch zu qa_azimuth.DEFAULT_BUILDING_HEIGHT_M/LEVEL_HEIGHT_M
# gehalten (kleine, stabile Konstanten, hier dupliziert statt eines Imports
# eines privaten "_"-Symbols über Modulgrenzen hinweg — bei Änderung an einer
# Stelle die andere mitziehen).
DEFAULT_BUILDING_HEIGHT_M: float = 9.0
LEVEL_HEIGHT_M: float = 3.0

DEFAULT_RADIUS_M: float = 200.0


class WayRecord(NamedTuple):
    """Osmium-unabhängige Darstellung eines OSM-Way mit Tags + Knoten-
    Koordinaten — das Ergebnis von `_iter_ways_from_pbf()` bzw. das, was Tests
    direkt konstruieren, ohne osmium/PBF zu benötigen."""
    way_id: int
    tags: Dict[str, str]
    nodes: List[Tuple[float, float]]  # (lat, lon), Reihenfolge wie im Way


class KnownLocation(NamedTuple):
    location_id: str
    observer_lat: float
    observer_lon: float
    subject_lat: float
    subject_lon: float


# ---------------------------------------------------------------------------
# Bekannte Locations laden
# ---------------------------------------------------------------------------

def load_known_locations() -> List[KnownLocation]:
    """Lädt die Basis-Locations aus `data/locations.py` (LOCATIONS-Liste) als
    einfache, JSON-taugliche KnownLocation-Tupel. Siehe Scope-Grenze im
    Modul-Docstring: Custom-Locations aus der Server-DB sind hier NICHT
    enthalten."""
    from data.locations import LOCATIONS  # lokaler Import: Modul soll ohne Backend-Kontext importierbar bleiben

    return [
        KnownLocation(
            location_id=loc.id,
            observer_lat=loc.observer_lat,
            observer_lon=loc.observer_lon,
            subject_lat=loc.subject_lat,
            subject_lon=loc.subject_lon,
        )
        for loc in LOCATIONS
    ]


# ---------------------------------------------------------------------------
# Geometrie-Hilfsfunktionen
# ---------------------------------------------------------------------------

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Abstand in Metern zwischen zwei (lat, lon)-Punkten."""
    import math
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _building_height(tags: Dict[str, str]) -> float:
    """Schätzt die Gebäudehöhe aus OSM-Tags — Spiegelbild von
    qa_azimuth._building_height() (siehe Kommentar bei den Modul-Konstanten)."""
    height_raw = tags.get("height")
    if height_raw:
        try:
            return float(str(height_raw).replace("m", "").strip())
        except (ValueError, TypeError):
            pass
    levels_raw = tags.get("building:levels")
    if levels_raw:
        try:
            return float(levels_raw) * LEVEL_HEIGHT_M
        except (ValueError, TypeError):
            pass
    return DEFAULT_BUILDING_HEIGHT_M


def _way_centroid(nodes: List[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    if not nodes:
        return None
    c_lat = sum(n[0] for n in nodes) / len(nodes)
    c_lon = sum(n[1] for n in nodes) / len(nodes)
    return c_lat, c_lon


# ---------------------------------------------------------------------------
# Kernlogik: Radius-Filter (offline testbar, kein osmium/PBF nötig)
# ---------------------------------------------------------------------------

def extract_buildings_for_locations(
    ways: Iterable[WayRecord],
    locations: List[KnownLocation],
    radius_m: float = DEFAULT_RADIUS_M,
) -> Dict[str, List[dict]]:
    """Filtert `ways` (bereits auf `building`-getaggte Ways beschränkt oder
    nicht — wird hier zusätzlich geprüft) auf die, deren Schwerpunkt innerhalb
    `radius_m` um die Standort- ODER Motiv-Koordinate MINDESTENS EINER
    Location liegt, und ordnet sie jeder passenden Location zu.

    Gibt ein Dict location_id -> Liste von {"nodes": [(lat,lon),...],
    "height_m": float} zurück. Locations ohne Treffer bekommen eine leere
    Liste (bedeutet später in qa_azimuth.py: "bestätigt kein Gebäude in der
    Nähe", NICHT "nicht geprüft").
    """
    result: Dict[str, List[dict]] = {loc.location_id: [] for loc in locations}

    for way in ways:
        if "building" not in way.tags:
            continue
        if len(way.nodes) < 3:
            continue
        centroid = _way_centroid(way.nodes)
        if centroid is None:
            continue
        c_lat, c_lon = centroid
        height_m = _building_height(way.tags)
        for loc in locations:
            near_subject = _haversine_m(c_lat, c_lon, loc.subject_lat, loc.subject_lon) <= radius_m
            near_observer = _haversine_m(c_lat, c_lon, loc.observer_lat, loc.observer_lon) <= radius_m
            if near_subject or near_observer:
                result[loc.location_id].append({
                    "nodes": [[round(n[0], 7), round(n[1], 7)] for n in way.nodes],
                    "height_m": height_m,
                })

    return result


def build_output(
    locations: List[KnownLocation],
    buildings_by_location: Dict[str, List[dict]],
    radius_m: float,
    source_label: str,
) -> dict:
    """Baut die finale JSON-Struktur, deterministisch sortiert (stabiler Diff
    zwischen zwei Läufen, damit ein Commit im GitHub-Actions-Workflow nur bei
    echter inhaltlicher Änderung entsteht)."""
    locations_out = []
    for loc in sorted(locations, key=lambda l: l.location_id):
        locations_out.append({
            "location_id": loc.location_id,
            "observer_lat": loc.observer_lat,
            "observer_lon": loc.observer_lon,
            "subject_lat": loc.subject_lat,
            "subject_lon": loc.subject_lon,
            "buildings": buildings_by_location.get(loc.location_id, []),
        })

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source_label,
        "radius_m": radius_m,
        "location_count": len(locations_out),
        "locations": locations_out,
    }


# ---------------------------------------------------------------------------
# PBF-Anbindung (osmium) — NICHT Teil der offline testbaren Kernlogik
# ---------------------------------------------------------------------------

def _iter_ways_from_pbf(pbf_path: str) -> Iterator[WayRecord]:
    """Liest alle Ways mit einem `building`-Tag aus der gegebenen PBF-Datei
    per osmium (pyosmium, `pip install osmium`) und liefert sie als
    WayRecord — inkl. bereits aufgelöster Knoten-Koordinaten
    (`locations=True` im Handler löst Node-Referenzen direkt zu lat/lon auf,
    kein zweiter Durchlauf nötig).

    Lazy Import: Dieses Modul soll ohne osmium-Installation importierbar und
    testbar bleiben (siehe Modul-Docstring) — nur dieser eine Adapter braucht
    die echte Bibliothek, und nur wenn tatsächlich eine PBF-Datei verarbeitet
    wird (CLI-Aufruf mit --pbf).

    NICHT in der Sandbox verifiziert (kein Netzzugriff, keine reale PBF-Test-
    datei verfügbar) — Stephan muss den ersten echten GitHub-Actions-Lauf
    gegen echte Geofabrik-Daten selbst prüfen (siehe BACKLOG.md TASK-59).
    """
    import osmium  # pyosmium — nur hier gebraucht, siehe Docstring

    records: List[WayRecord] = []

    class _BuildingHandler(osmium.SimpleHandler):  # type: ignore[misc]
        def way(self, w):  # noqa: N802 — osmium-API-Methode
            tags = {tag.k: tag.v for tag in w.tags}
            if "building" not in tags:
                return
            try:
                nodes = [(n.lat, n.lon) for n in w.nodes if n.location.valid()]
            except Exception:
                return
            if len(nodes) < 3:
                return
            records.append(WayRecord(way_id=w.id, tags=tags, nodes=nodes))

    handler = _BuildingHandler()
    handler.apply_file(pbf_path, locations=True)
    return iter(records)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="TASK-59 Option E: Gebäude-Footprints aus einem lokalen "
                     "Geofabrik-PBF-Auszug für die bekannten FotoAlert-Locations extrahieren."
    )
    parser.add_argument("--pbf", required=True, help="Pfad zur lokalen .osm.pbf-Datei")
    parser.add_argument(
        "--output", required=True,
        help="Zielpfad der JSON-Ausgabedatei (z.B. data/cache/building_footprints.json)",
    )
    parser.add_argument(
        "--radius", type=float, default=DEFAULT_RADIUS_M,
        help="Suchradius in Metern um Standort/Motiv jeder Location (Default: %(default)s)",
    )
    args = parser.parse_args(argv)

    locations = load_known_locations()
    ways = _iter_ways_from_pbf(args.pbf)
    buildings_by_location = extract_buildings_for_locations(ways, locations, radius_m=args.radius)
    output = build_output(locations, buildings_by_location, args.radius, source_label=Path(args.pbf).name)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )

    total_buildings = sum(len(v) for v in buildings_by_location.values())
    locations_with_hits = sum(1 for v in buildings_by_location.values() if v)
    print(
        f"{len(locations)} Locations verarbeitet, {locations_with_hits} mit mindestens "
        f"einem Gebäude im {args.radius:.0f}m-Radius, {total_buildings} Gebäude insgesamt "
        f"-> {out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
