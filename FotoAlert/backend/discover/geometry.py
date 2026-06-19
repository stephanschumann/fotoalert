"""
Geodätische Hilfsfunktionen für die Discover-Pipeline.
"""
from __future__ import annotations
import math


def destination_point(lat: float, lon: float, bearing_deg: float, distance_m: float) -> tuple[float, float]:
    """
    Berechnet einen Geo-Punkt der `distance_m` Meter vom Ausgangspunkt
    in Richtung `bearing_deg` (Grad, Nord=0, Uhrzeigersinn) entfernt liegt.

    Sphärische Formel (Vincenty-Annäherung), Genauigkeit ~0.1% bei < 100 km.

    Beispiel:
      destination_point(52.5208, 13.4094, 298.4, 5640)
      → (52.493, 13.328)  # SW vom Fernsehturm
    """
    R = 6_371_000.0  # Erdradius in Metern
    δ = distance_m / R
    θ = math.radians(bearing_deg)
    φ1 = math.radians(lat)
    λ1 = math.radians(lon)

    φ2 = math.asin(
        math.sin(φ1) * math.cos(δ)
        + math.cos(φ1) * math.sin(δ) * math.cos(θ)
    )
    λ2 = λ1 + math.atan2(
        math.sin(θ) * math.sin(δ) * math.cos(φ1),
        math.cos(δ) - math.sin(φ1) * math.sin(φ2),
    )
    return math.degrees(φ2), math.degrees(λ2)


def bearing_between(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Azimut (0–360°) vom Punkt 1 zu Punkt 2."""
    d_lon = math.radians(lon2 - lon1)
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    x = math.sin(d_lon) * math.cos(φ2)
    y = math.cos(φ1) * math.sin(φ2) - math.sin(φ1) * math.cos(φ2) * math.cos(d_lon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360
