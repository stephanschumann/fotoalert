"""
FotoAlert – Ephemeris Core (TASK-25, Option B)

Standortunabhängige Schicht der On-Demand-Engine.

Kernidee (Hebel 1 der Spec): Die geozentrische *scheinbare* Position eines
Objekts (Rektaszension α, Deklination δ, Distanz) zu einem Zeitpunkt ist für
jeden Beobachter auf der Erde identisch. Diese teure Größe wird **einmal pro
Zeitfenster** berechnet (Skyfield + de421, vektorisiert) und über alle
Beobachter/Vordergründe wiederverwendet. Die pro-Beobachter-Arbeit (alt/az,
Parallaxe, Refraktion) liegt in `query_engine.py` und ist reine Trigonometrie.

Python-3.9-kompatibel (Prod-Server). `from __future__ import annotations` macht
alle Annotationen zu Strings → PEP-604-Syntax (`x | None`) ist unkritisch.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import numpy as np
from skyfield.api import Star

# Geteilte Timescale + Ephemeride aus astronomy.py wiederverwenden (kein
# Doppel-Laden von de421). astronomy._ts / astronomy._get_eph() sind dort
# einmalig initialisiert.
from . import astronomy as _astro

# Äquatorialradius der Erde in AU – für die topozentrische Mond-Parallaxe.
# 6378.140 km / 149_597_870.7 km/AU
EARTH_RADIUS_AU = 6378.140 / 149_597_870.7  # ≈ 4.2635e-5

# Mapping unserer kurzen Body-Keys auf die de421-Namen.
_SKY_BODY: Dict[str, str] = {
    "sun": "sun",
    "moon": "moon",
    "venus": "venus",
    "mars": "mars",
    "jupiter": "jupiter barycenter",
    "saturn": "saturn barycenter",
}

# Milchstraße: Galaktisches Zentrum (Sgr A*) als fester Himmelspunkt.
_GALACTIC_CENTER = Star(ra_hours=17.761, dec_degrees=-28.936)

# Objekte, deren topozentrische Parallaxe relevant ist (nur der Mond ist mit
# bis zu ~1° spürbar; Sonne/Planeten < ~30'' → vernachlässigbar, aber wir
# wenden die Korrektur generisch an, wenn distance_au endlich ist).
_PARALLAX_BODIES = {"moon"}

# Instrumentierung für AK „Position einmal pro Fenster":
#   track_calls  = teure vektorisierte Fenster-Berechnungen (Hebel 1 relevant)
#   sample_calls = günstige Einzelpunkt-Auswertungen (Rootfinding-Verfeinerung)
_eval_counter = {"track_calls": 0, "sample_calls": 0}

# Cache der geozentrischen Fenster-Tracks, damit mehrere Beobachter im selben
# Fenster den teuren Skyfield-Call NICHT erneut auslösen (Hebel 1).
_track_cache: "Dict[tuple, GeocentricTrack]" = {}


def reset_eval_counter() -> None:
    _eval_counter["track_calls"] = 0
    _eval_counter["sample_calls"] = 0


def track_eval_count() -> int:
    """Anzahl teurer Fenster-Berechnungen (für AK „1× pro Fenster")."""
    return _eval_counter["track_calls"]


def sample_eval_count() -> int:
    return _eval_counter["sample_calls"]


def clear_cache() -> None:
    _track_cache.clear()


@dataclass
class GeocentricTrack:
    """Geozentrische scheinbare Bahn eines Objekts über ein Zeitfenster."""
    body: str
    tt_jd: np.ndarray        # Terrestrial Time (JD) der Stützstellen
    gast_hours: np.ndarray   # Greenwich Apparent Sidereal Time (Stunden)
    ra_hours: np.ndarray     # scheinbare Rektaszension (Stunden, Äquinoktium des Datums)
    dec_deg: np.ndarray      # scheinbare Deklination (Grad)
    distance_au: np.ndarray  # geozentrische Distanz (AU)


def _resolve_target(body: str):
    if body == "milkyway":
        return _GALACTIC_CENTER
    if body not in _SKY_BODY:
        raise ValueError(f"Unbekannter Body: {body!r}")
    return _astro._get_eph()[_SKY_BODY[body]]


def _radec_apparent(target, times):
    """Geozentrische scheinbare α/δ/Distanz (Äquinoktium des Datums)."""
    earth = _astro._get_eph()["earth"]
    astrometric = earth.at(times).observe(target).apparent()
    ra, dec, dist = astrometric.radec(epoch="date")
    return ra.hours, dec.degrees, dist.au


def compute_track(body: str, t0: datetime, t1: datetime, n: int) -> GeocentricTrack:
    """
    Geozentrischen Track für [t0, t1] mit n Stützstellen berechnen — einmal pro
    Fenster, danach gecacht. Wiederverwendung durch verschiedene Beobachter löst
    KEINEN weiteren Skyfield-Call aus (Hebel 1).
    """
    t0u = t0.astimezone(timezone.utc)
    t1u = t1.astimezone(timezone.utc)
    key = (body, round(t0u.timestamp()), round(t1u.timestamp()), int(n))
    cached = _track_cache.get(key)
    if cached is not None:
        return cached

    ts = _astro._ts
    times = ts.linspace(_astro._skyfield_time(t0u), _astro._skyfield_time(t1u), int(n))
    _eval_counter["track_calls"] += 1
    ra_hours, dec_deg, dist_au = _radec_apparent(_resolve_target(body), times)

    track = GeocentricTrack(
        body=body,
        tt_jd=np.asarray(times.tt, dtype=float),
        gast_hours=np.asarray(times.gast, dtype=float),
        ra_hours=np.asarray(ra_hours, dtype=float),
        dec_deg=np.asarray(dec_deg, dtype=float),
        distance_au=np.asarray(dist_au, dtype=float),
    )
    _track_cache[key] = track
    return track


def sample_at(body: str, when: datetime) -> Tuple[float, float, float, float]:
    """
    Geozentrische scheinbare α/δ/Distanz + GAST für einen einzelnen Zeitpunkt
    (für die Rootfinding-Verfeinerung). Nicht gecacht; wenige Aufrufe pro Event.
    """
    ts = _astro._ts
    t = _astro._skyfield_time(when.astimezone(timezone.utc))
    _eval_counter["sample_calls"] += 1
    ra_hours, dec_deg, dist_au = _radec_apparent(_resolve_target(body), t)
    return (
        float(np.asarray(ra_hours)),
        float(np.asarray(dec_deg)),
        float(np.asarray(dist_au)),
        float(np.asarray(t.gast)),
    )


def has_parallax(body: str) -> bool:
    return body in _PARALLAX_BODIES
