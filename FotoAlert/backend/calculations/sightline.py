"""
FotoAlert – Sichtachsen-Check: Raycast-Hinderniserkennung (US-09)

Prüft, ob die Sichtlinie Fotostandort → Motiv durch Gebäude oder Gelände
blockiert wird. Kombiniert:
  - Geländehöhenprofil entlang der Linie (OpenTopoData, via elevation.py)
  - Gebäude-Footprints entlang der Linie (Overpass, via qa_azimuth.py)
  - Erdkrümmungs-/Refraktionskorrektur (relevant ab ~5 km, siehe Pre-Mortem)

Vier Zustände (siehe BACKLOG.md US-09, Example Mapping):
  - "frei":              keine Hindernisse über der Sichtlinie gefunden
  - "teilweise_verdeckt": ein Hindernis verdeckt nur den unteren Teil des
                          Sichtfensters (z.B. knapp über Horizont)
  - "blockiert":          ein Hindernis verdeckt die komplette Ziellinie
  - "nicht_geprueft":     externe Daten nicht verfügbar (Regel 4: niemals
                          stillschweigend als "frei" werten)

Dieser Check läuft NUR als einmaliger Precompute-Schritt (Location anlegen/
ändern bzw. manueller Refresh) — NIE live pro Chancen-Anzeige. Das ist ein
explizites Pre-Mortem-Ergebnis der Spec: die öffentlichen Overpass-/
OpenTopoData-Instanzen sind für Live-Backend-Nutzung nicht vorgesehen.

Python-3.9-kompatibel.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Ab dieser Distanz (m) wird die Erdkrümmung/Refraktion in der Sichtlinien-
# Berechnung berücksichtigt (⚠️ Annahme aus der Analyse-Phase, von Stephan
# noch nicht explizit bestätigt — siehe Rückmeldung an Stephan).
CURVATURE_THRESHOLD_M: float = 5000.0

# Standard-Erdradius (m) für die Krümmungskorrektur.
EARTH_RADIUS_M: float = 6_371_000.0

# Refraktionskoeffizient (Standardwert der Geodäsie, atmosphärische Lichtbrechung
# hebt den scheinbaren Horizont leicht an — reduziert die Netto-Krümmung um ~13%).
REFRACTION_COEFFICIENT: float = 0.13

# Standard-Augenhöhe (m), addiert auf observer_floor_height_m (US-62) für den
# Raycast-Startpunkt (von Stephan am 2026-07-06 auf 1,8m bestätigt/korrigiert).
DEFAULT_EYE_HEIGHT_M: float = 1.8

# Toleranzband (Grad) für "teilweise verdeckt": liegt der höchste Blockadewinkel
# innerhalb dieses Bands über 0°, gilt die Sicht als teilweise (nicht komplett)
# verdeckt (Regel 2 der Spec: unterer Teil des Alignment-Fensters verdeckt).
PARTIAL_BAND_DEG: float = 3.0


def _curvature_drop_m(distance_m: float) -> float:
    """Effektiver Höhenabfall des Horizonts durch Erdkrümmung minus Refraktion,
    an einem Punkt `distance_m` vom Beobachter entfernt. Unterhalb von
    CURVATURE_THRESHOLD_M vernachlässigbar (Spec-Annahme), wird hier aber für
    jede Distanz korrekt mitgerechnet (stetige Funktion, kein Sprung am
    Schwellwert) — der Schwellwert steuert nur, ob der AK-Testfall greift.
    """
    net_curvature = (1.0 - REFRACTION_COEFFICIENT) / (2.0 * EARTH_RADIUS_M)
    return net_curvature * (distance_m ** 2)


def _max_obstruction_angle_deg(
    observer_height_m: float,
    sample_heights_m: List[Optional[float]],
    sample_distances_m: List[float],
) -> Tuple[Optional[float], Optional[int]]:
    """Größter Erhebungswinkel (Grad, über der Horizontalen am Beobachter) unter
    allen Sample-Punkten, inkl. Erdkrümmungskorrektur. None-Werte werden
    übersprungen (Aufrufer entscheidet anhand `incomplete`, ob das Ergebnis
    verwertbar ist). Gibt (max_angle_deg, index_des_max_punkts) zurück, oder
    (None, None) wenn keine gültigen Punkte vorhanden sind.
    """
    max_angle: Optional[float] = None
    max_idx: Optional[int] = None
    for idx, (h, d) in enumerate(zip(sample_heights_m, sample_distances_m)):
        if h is None or d <= 0:
            continue
        drop = _curvature_drop_m(d)
        rel_height = (h - observer_height_m) - drop
        angle = math.degrees(math.atan2(rel_height, d))
        if max_angle is None or angle > max_angle:
            max_angle = angle
            max_idx = idx
    return max_angle, max_idx


def evaluate_sightline(
    observer_lat: float,
    observer_lon: float,
    observer_floor_height_m: float,
    subject_lat: Optional[float],
    subject_lon: Optional[float],
    subject_height_m: Optional[float],
    terrain_heights_m: Optional[List[Optional[float]]],
    terrain_incomplete: bool,
    buildings: Optional[List[dict]],
    distance_m: Optional[float] = None,
) -> dict:
    """Bewertet die Sichtlinie Fotostandort → Motiv anhand von Terrain- und
    Gebäudedaten. Reine Berechnung, KEINE Netzwerk-Calls (die sind bereits
    erledigt — dieser Funktion werden nur die Rohdaten übergeben, damit sie
    ohne Netzwerkzugriff/synchron testbar ist).

    Rückgabe (immer ein dict, nie eine Exception nach außen):
      {
        "status": "frei" | "teilweise_verdeckt" | "blockiert" | "nicht_geprueft",
        "obstruction_angle_deg": float | None,   # höchster Verdeckungswinkel
        "visible_from_deg": float | None,        # ab welcher Höhe über Horizont frei (teilweise-Fall)
        "reason": str,                            # kurzer interner Grund (Logging/Debug)
      }
    """
    if subject_lat is None or subject_lon is None:
        return {"status": "nicht_geprueft", "obstruction_angle_deg": None,
                "visible_from_deg": None, "reason": "kein_motiv"}

    if terrain_heights_m is None or terrain_incomplete or buildings is None:
        return {"status": "nicht_geprueft", "obstruction_angle_deg": None,
                "visible_from_deg": None, "reason": "daten_unvollstaendig"}

    n = len(terrain_heights_m)
    if n < 2:
        return {"status": "nicht_geprueft", "obstruction_angle_deg": None,
                "visible_from_deg": None, "reason": "profil_zu_kurz"}

    if distance_m is None:
        # Grobe Distanz aus Sample-Anzahl nicht ableitbar ohne Koordinaten;
        # der Aufrufer (precompute) übergibt distance_m normalerweise mit.
        return {"status": "nicht_geprueft", "obstruction_angle_deg": None,
                "visible_from_deg": None, "reason": "keine_distanz"}

    observer_height_m = observer_floor_height_m + DEFAULT_EYE_HEIGHT_M
    sample_distances_m = [distance_m * (i / (n - 1)) for i in range(n)]

    # Terrain-Verdeckungswinkel (Zwischenpunkte, Index 0/letzter = Endpunkte
    # selbst ausschließen — die sind Beobachter/Motiv, kein Hindernis).
    terrain_angle, _ = _max_obstruction_angle_deg(
        observer_height_m,
        terrain_heights_m[1:-1] if n > 2 else [],
        sample_distances_m[1:-1] if n > 2 else [],
    )

    # Gebäude-Verdeckungswinkel: für jedes Gebäude den Punkt nehmen, an dem
    # seine Peilung die Standort-Motiv-Linie kreuzt (Näherung: nutze die
    # Gebäude-Distanz vom Beobachter über den Schwerpunkt, da Gebäude im
    # Nahbereich präziser als das Höhenraster sind, siehe Pre-Mortem).
    from discover.geometry import bearing_between  # lokaler Import: zirkulär vermeiden

    building_angle: Optional[float] = None
    obs_terrain = terrain_heights_m[0] if terrain_heights_m[0] is not None else 0.0
    for b in buildings:
        nodes = b.get("nodes") or []
        if not nodes:
            continue
        c_lat = sum(p[0] for p in nodes) / len(nodes)
        c_lon = sum(p[1] for p in nodes) / len(nodes)
        d = _haversine_m(observer_lat, observer_lon, c_lat, c_lon)
        if d <= 0 or d > distance_m * 1.05:
            # Gebäude liegt (deutlich) hinter dem Motiv oder exakt am Standort
            # → kein Hindernis auf dem Weg dorthin.
            continue
        height_m = b.get("height_m", 0.0)
        # Grundhöhe am Gebäudestandort: gleicher linearer Interpolationsansatz
        # wie das Terrain-Profil, damit Gebäude auf abschüssigem Gelände nicht
        # künstlich zu hoch/niedrig gegen den Beobachter gerechnet werden.
        frac = min(1.0, d / distance_m) if distance_m > 0 else 0.0
        idx = min(n - 1, int(round(frac * (n - 1))))
        base_h = terrain_heights_m[idx] if terrain_heights_m[idx] is not None else obs_terrain
        top_h = base_h + height_m
        drop = _curvature_drop_m(d)
        rel_height = (top_h - observer_height_m) - drop
        angle = math.degrees(math.atan2(rel_height, d))
        if building_angle is None or angle > building_angle:
            building_angle = angle

    candidates = [a for a in (terrain_angle, building_angle) if a is not None]
    if not candidates:
        return {"status": "frei", "obstruction_angle_deg": None,
                "visible_from_deg": None, "reason": "keine_hindernisse"}

    max_angle = max(candidates)

    # Zielwinkel: Höhenwinkel der Motivspitze über dem Beobachter-Horizont.
    subj_h = subject_height_m or 0.0
    target_rel_height = subj_h - observer_height_m - _curvature_drop_m(distance_m)
    target_angle = math.degrees(math.atan2(target_rel_height, distance_m))

    if max_angle <= 0.0:
        # Hindernis liegt komplett unter der Horizontalen → keine Verdeckung.
        return {"status": "frei", "obstruction_angle_deg": round(max_angle, 2),
                "visible_from_deg": None, "reason": "unter_horizont"}

    if max_angle >= target_angle:
        # Hindernis reicht bis (mindestens) zur Motivspitze → komplett blockiert.
        return {"status": "blockiert", "obstruction_angle_deg": round(max_angle, 2),
                "visible_from_deg": round(max_angle, 2), "reason": "voll_verdeckt"}

    # Hindernis liegt über 0° aber unter der Motivspitze → teilweise verdeckt
    # (Regel 2: unterer Teil des Sichtfensters verdeckt, ab max_angle frei).
    return {"status": "teilweise_verdeckt", "obstruction_angle_deg": round(max_angle, 2),
            "visible_from_deg": round(max_angle, 2), "reason": "teilweise_verdeckt"}


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distanz zweier Punkte in Metern (Haversine)."""
    R = EARTH_RADIUS_M
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


async def compute_location_sightline(loc, elevation_provider, num_samples: int = 20) -> dict:
    """Führt den vollständigen Sichtachsen-Check für eine Location aus:
    holt Höhenprofil (OpenTopoData) + Gebäude entlang der Linie (Overpass),
    ruft dann `evaluate_sightline` auf. Fängt jeden Fehler ab und liefert
    "nicht_geprueft" statt einer Exception (Regel 4).

    `loc`: Objekt mit observer_lat/lon, subject_lat/lon, subject_height_m,
    observer_floor_height_m, distance_m (Duck-Typing, funktioniert für
    PhotoLocation und Custom-Location-Dicts gleichermaßen über getattr).
    """
    from data.qa_azimuth import fetch_buildings_along_line

    observer_lat = getattr(loc, "observer_lat", None)
    observer_lon = getattr(loc, "observer_lon", None)
    subject_lat = getattr(loc, "subject_lat", None)
    subject_lon = getattr(loc, "subject_lon", None)
    subject_height_m = getattr(loc, "subject_height_m", None)
    observer_floor_height_m = getattr(loc, "observer_floor_height_m", 0.0) or 0.0
    distance_m = getattr(loc, "distance_m", None)

    if observer_lat is None or observer_lon is None or subject_lat is None or subject_lon is None:
        return {"status": "nicht_geprueft", "obstruction_angle_deg": None,
                "visible_from_deg": None, "reason": "koordinaten_fehlen"}

    if distance_m is None:
        distance_m = _haversine_m(observer_lat, observer_lon, subject_lat, subject_lon)

    try:
        terrain_heights, terrain_incomplete = await elevation_provider.elevation_profile(
            observer_lat, observer_lon, subject_lat, subject_lon, num_samples=num_samples,
        )
    except Exception as exc:
        logger.warning("Sichtachsen-Check: Höhenprofil fehlgeschlagen (%s): %s", loc, exc)
        return {"status": "nicht_geprueft", "obstruction_angle_deg": None,
                "visible_from_deg": None, "reason": "hoehenprofil_fehler"}

    try:
        buildings = fetch_buildings_along_line(observer_lat, observer_lon, subject_lat, subject_lon)
    except Exception as exc:  # noqa: BLE001 — defensiv, fetch_buildings_along_line fängt bereits selbst ab
        logger.warning("Sichtachsen-Check: Gebäudeabfrage fehlgeschlagen (%s): %s", loc, exc)
        buildings = None

    return evaluate_sightline(
        observer_lat, observer_lon, observer_floor_height_m,
        subject_lat, subject_lon, subject_height_m,
        terrain_heights, terrain_incomplete, buildings,
        distance_m=distance_m,
    )


async def update_location_sightline(store, loc, elevation_provider) -> dict:
    """Führt den Sichtachsen-Check für EINE Location aus und persistiert das
    Ergebnis im Store (location_qa_values, analog zu qa_azimuth.update_location_azimuth).

    Wird sowohl beim Anlegen/Ändern einer Location (Regel 3) als auch beim
    manuellen "Sichtachsen aktualisieren"-Refresh aufgerufen. Schreibt IMMER
    (auch bei "nicht_geprueft"), damit der Zeitstempel `sightline_checked_at`
    zeigt, wann zuletzt versucht wurde — unabhängig vom Ergebnis.

    Gibt das Ergebnis-dict zurück (siehe evaluate_sightline), wirft nie.
    """
    from datetime import datetime, timezone

    result = await compute_location_sightline(loc, elevation_provider)
    if result["status"] == "nicht_geprueft":
        # BUG-Diagnose (US-09): das `reason`-Feld wurde bisher nirgends geloggt,
        # wodurch ein dauerhaftes "nicht_geprueft" für alle Locations (z.B. weil
        # Overpass/OpenTopoData-Daten systematisch unvollständig sind) sich nicht
        # von außen unterscheiden ließ. Warning-Level, damit es auch bei Standard-
        # Log-Konfiguration (INFO/WARNING) sichtbar ist.
        logger.warning(
            "Sichtachsen-Check für %s ergab 'nicht_geprueft' (Grund: %s)",
            loc.id, result.get("reason"),
        )
    try:
        store.set_qa_values(
            loc.id,
            sightline_status=result["status"],
            sightline_angle_deg=result.get("obstruction_angle_deg"),
            sightline_checked_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        logger.warning("Sichtachsen-Ergebnis für %s nicht speicherbar: %s", loc.id, exc)
    return result
