"""
Scout-Tab Motive: automatisch aus data/locations.py abgeleitet.

Jedes Motiv (DiscoverSubject) repräsentiert eine fotografierbare Struktur.
Die Scout-Pipeline berechnet dazu neue Fotografen-Standpunkte aus der Mond-Position —
abweichend von allen gespeicherten Standorten in data/locations.py.

Deduplication: Motive mit Subject-Koordinaten < 200m Abstand werden zusammengeführt
(gleiche Struktur, verschiedene Fotografen-Perspektiven in locations.py).

Bekannte Fotografen-Standorte: als Ausschlusszone (≥ 150 m Abstand erforderlich),
damit Scout wirklich neue Perspektiven liefert.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional

from data.locations import LOCATIONS, LocationCategory


# ---------------------------------------------------------------------------
# Default-Breiten nach Kategorie (für Locations ohne subject_width_m)
# ---------------------------------------------------------------------------

_DEFAULT_WIDTH_M: dict[LocationCategory, float] = {
    LocationCategory.SKYLINE:    80.0,
    LocationCategory.SCHLOSS:    70.0,
    LocationCategory.AUSSICHT:   30.0,
    LocationCategory.INDUSTRIE:  15.0,
    LocationCategory.WASSER:     30.0,
    LocationCategory.NATUR:      30.0,
    LocationCategory.MILCHSTRASSE: 30.0,
}


# ---------------------------------------------------------------------------
# DiscoverSubject
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DiscoverSubject:
    id: str
    name: str
    kategorie: str           # Emoji + Kurzname für UI
    lat: float               # Koordinaten der Motivspitze / Hauptstruktur
    lon: float
    structure_height_m: float
    terrain_offset_m: float  # Höhe Gelände relativ zu Beobachter am Boden
    subject_width_m: float
    hoehe_confidence: str    # "hoch" | "mittel" | "niedrig"

    @property
    def apex_effective_m(self) -> float:
        """Effektive Höhe über dem Beobachter."""
        return self.structure_height_m + self.terrain_offset_m


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Entfernung in Metern zwischen zwei GPS-Punkten."""
    R = 6_371_000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _slug(name: str) -> str:
    """Einfacher ID-Slug aus Name."""
    s = name.lower()
    s = re.sub(r'[äöü]', lambda m: {'ä': 'ae', 'ö': 'oe', 'ü': 'ue'}[m.group()], s)
    s = re.sub(r'[^a-z0-9]+', '_', s)
    return s.strip('_')[:40]


def _kategorie_label(category: LocationCategory) -> str:
    return {
        LocationCategory.SKYLINE:    "🏙 Skyline",
        LocationCategory.SCHLOSS:    "🏰 Schloss",
        LocationCategory.AUSSICHT:   "🔭 Aussicht",
        LocationCategory.INDUSTRIE:  "🏗 Urban",
        LocationCategory.WASSER:     "💧 Wasser",
        LocationCategory.NATUR:      "🌿 Natur",
        LocationCategory.MILCHSTRASSE: "🌌 Astro",
    }.get(category, "📍 Ort")


def _is_placeholder(loc) -> bool:
    """True wenn height/width offensichtlich Defaultwerte ohne echte Daten sind.

    US-128 (Example Mapping, Frage 1, Option B): Die reine Magic-Number-Heuristik
    `height == 20 and width is None` kollidierte mit einem echten, recherchierten
    Höhenwert von exakt 20m. Zusätzliches Kriterium: `subject_height_researched`
    (Default True bei normalen Locations, explizit False bei den unbearbeiteten
    Locationscout-Import-Platzhaltern in data/locations.py sowie bei einer Korrektur
    per PATCH automatisch wieder auf True gesetzt) muss ebenfalls False sein.
    """
    return (
        loc.subject_height_m == 20
        and loc.subject_width_m is None
        and not getattr(loc, "subject_height_researched", True)
    )


# ---------------------------------------------------------------------------
# Hauptfunktion: Subjects + Exklusionszonen aus Locations ableiten
# ---------------------------------------------------------------------------

_DEDUP_RADIUS_M = 200.0      # Motive < 200m zusammenführen
_SCOUT_MIN_APEX_M = 5.0      # Motiv muss mindestens 5m höher als Beobachter sein


def _group_location_candidates(candidates: list) -> list[dict]:
    """
    Dedupliziert Location-Kandidaten nach Subject-Koordinaten (DEDUP_RADIUS_M).

    Für jede Gruppe gewinnt das erste Vorkommen als DiscoverSubject;
    alle bekannten Fotografen-Standorte werden gesammelt.

    Rückgabe: groups — [{id, name, category, subject_lat/lon,
                          structure_height_m, terrain_offset_m,
                          subject_width_m, observers: [(lat,lon)]}]
    """
    groups: list[dict] = []

    for loc in candidates:
        matched_group = None
        for g in groups:
            dist = _haversine_m(
                loc.subject_lat, loc.subject_lon,
                g["subject_lat"], g["subject_lon"],
            )
            if dist < _DEDUP_RADIUS_M:
                matched_group = g
                break

        if matched_group is None:
            groups.append({
                "id": _slug(loc.subject_name),
                "name": loc.subject_name,
                "category": loc.category,
                "subject_lat": loc.subject_lat,
                "subject_lon": loc.subject_lon,
                "structure_height_m": loc.subject_height_m,
                "terrain_offset_m": loc.elevation_difference_m or 0.0,
                "subject_width_m": (
                    loc.subject_width_m
                    or _DEFAULT_WIDTH_M.get(loc.category, 30.0)
                ),
                "observers": [(loc.observer_lat, loc.observer_lon)],
            })
        else:
            # Gleiche Struktur, neuer Fotografen-Standpunkt
            matched_group["observers"].append((loc.observer_lat, loc.observer_lon))
            # Beste Höhendaten gewinnen (höchster apex)
            apex_existing = (matched_group["structure_height_m"]
                             + matched_group["terrain_offset_m"])
            apex_new = (loc.subject_height_m
                        + (loc.elevation_difference_m or 0.0))
            if apex_new > apex_existing:
                matched_group["structure_height_m"] = loc.subject_height_m
                matched_group["terrain_offset_m"] = loc.elevation_difference_m or 0.0
            # Breite: konkrete Angabe bevorzugen
            if loc.subject_width_m and not matched_group.get("_width_confirmed"):
                matched_group["subject_width_m"] = loc.subject_width_m
                matched_group["_width_confirmed"] = True

    return groups


def build_subjects(
) -> tuple[list[DiscoverSubject], dict[str, list[tuple[float, float]]]]:
    """
    Leitet Scout-Subjects und Exklusionszonen aus data/locations.py ab.

    Rückgabe:
      subjects      — Liste einzigartiger DiscoverSubject-Objekte
      exclusion_zones — {subject_id: [(observer_lat, observer_lon), ...]}
                        Bekannte Fotografen-Standorte die im Scout ausgeschlossen werden
    """
    # 1. Filtere ungeeignete Locations
    candidates = [
        loc for loc in LOCATIONS
        if (loc.subject_height_m is not None
            and loc.subject_height_m > 0
            and loc.subject_lat is not None
            and loc.subject_lon is not None
            and not _is_placeholder(loc))
    ]

    # 2. Dedupliziere nach Subject-Koordinaten (DEDUP_RADIUS_M)
    groups = _group_location_candidates(candidates)

    # 3. Baue DiscoverSubject-Objekte
    subjects: list[DiscoverSubject] = []
    exclusion_zones: dict[str, list[tuple[float, float]]] = {}

    for g in groups:
        apex = g["structure_height_m"] + g["terrain_offset_m"]
        if apex < _SCOUT_MIN_APEX_M:
            continue   # Motiv nicht hoch genug für Inverse-Berechnung

        subj = DiscoverSubject(
            id=g["id"],
            name=g["name"],
            kategorie=_kategorie_label(g["category"]),
            lat=g["subject_lat"],
            lon=g["subject_lon"],
            structure_height_m=g["structure_height_m"],
            terrain_offset_m=g["terrain_offset_m"],
            subject_width_m=g["subject_width_m"],
            hoehe_confidence="mittel",
        )
        subjects.append(subj)
        exclusion_zones[subj.id] = g["observers"]

    return subjects, exclusion_zones


# ---------------------------------------------------------------------------
# Gecachte Instanzen (einmal pro Prozess aufgebaut)
# ---------------------------------------------------------------------------

SUBJECTS, EXCLUSION_ZONES = build_subjects()
SUBJECT_BY_ID: dict[str, DiscoverSubject] = {s.id: s for s in SUBJECTS}
