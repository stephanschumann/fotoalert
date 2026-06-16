"""
Pydantic-Schemas für die FastAPI REST-Responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CameraHintOut(BaseModel):
    focal_length_mm: int
    aperture_suggestion: str
    shutter_suggestion: str
    iso_suggestion: str
    tripod_required: bool
    extra_tip: str


class LocationOut(BaseModel):
    id: str
    name: str
    description: str
    category: str
    observer_lat: float
    observer_lon: float
    subject_lat: Optional[float]
    subject_lon: Optional[float]
    ideal_azimuth_range: Optional[list[float]]
    subject_name: str
    subject_height_m: Optional[float]
    elevation_difference_m: float = 0.0
    distance_m: Optional[float]
    focal_length_suggestions: list[int]
    special_notes: str
    solar_alignment_note: str
    lunar_alignment_note: str
    access_note: str
    locationscout_url: str
    difficulty: int
    possible_bodies: list[str] = []  # US-35: ["sun","moon","milkyway"] – welche Körper jemals im Azimutbereich erscheinen


class OpportunityOut(BaseModel):
    id: str
    location_id: str
    location_name: str
    event_type: str
    title: str
    description: str
    shoot_time: datetime
    shoot_window_start: datetime
    shoot_window_end: datetime
    overall_score: float
    astronomy_score: float
    weather_score: float
    location_score: float
    camera_hints: list[CameraHintOut]
    subject_azimuth: Optional[float]
    celestial_azimuth: Optional[float]
    celestial_altitude: Optional[float]
    alert_priority: int
    weather_description: str
    # Mond/Sonne Details
    moon_phase: Optional[str] = None
    moon_illumination_pct: Optional[float] = None
    elevation_difference_m: Optional[float] = None
    sunrise_utc: Optional[datetime] = None
    sunset_utc: Optional[datetime] = None
    # Golden & Blue Hour – exakte Skyfield-Zeiten pro Location
    golden_hour_morning_start: Optional[datetime] = None
    golden_hour_morning_end: Optional[datetime] = None
    golden_hour_evening_start: Optional[datetime] = None
    golden_hour_evening_end: Optional[datetime] = None
    blue_hour_morning_start: Optional[datetime] = None
    blue_hour_morning_end: Optional[datetime] = None
    blue_hour_evening_start: Optional[datetime] = None
    blue_hour_evening_end: Optional[datetime] = None


class DailyBriefingOut(BaseModel):
    date: str
    location_count: int
    top_opportunities: list[OpportunityOut]
    highest_score: float
    alert_count: int  # Anzahl Opportunities mit Priority >= 2
    summary: str


class HealthOut(BaseModel):
    status: str
    version: str
    locations_count: int
