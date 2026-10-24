"""
models/safety.py — Safety and navigation data models.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class DataSource(str, Enum):
    LIVE_API = "live_api"
    FIXTURE = "fixture"         # clearly-labelled test fixture
    USER_REPORT = "user_report"
    OFFICIAL = "official"


class Location(BaseModel):
    """Geographic point. lat/lon in WGS-84 decimal degrees."""
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude")
    label: Optional[str] = Field(None, description="Human-readable name/label")
    accuracy_metres: Optional[float] = Field(None, ge=0.0)


class HazardType(str, Enum):
    ROAD_CLOSURE = "road_closure"
    CRIME_REPORT = "crime_report"
    POOR_LIGHTING = "poor_lighting"
    FLOOD = "flood"
    ACCIDENT = "accident"
    UNKNOWN = "unknown"


class HazardReport(BaseModel):
    """A reported hazard along a route or in an area."""
    hazard_type: HazardType
    description: str
    location: Optional[Location] = None
    source: DataSource = DataSource.FIXTURE
    reported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified: bool = False
    # Hazards older than this many minutes are flagged as stale
    age_minutes: Optional[float] = None

    @property
    def is_stale(self) -> bool:
        if self.age_minutes is None:
            return False
        return self.age_minutes > 120  # 2 hours = stale


class RouteOption(BaseModel):
    """A candidate route between two locations."""
    route_id: str
    description: str
    distance_km: float
    # Duration is a range or None if unknown; never invent a precise value
    duration_min_estimate: Optional[float] = Field(
        None, description="Estimated travel time in minutes (may be None if data unavailable)"
    )
    safety_score: float = Field(
        ..., ge=0.0, le=10.0,
        description="Composite safety score 0 (unsafe) – 10 (safe)"
    )
    hazards: list[HazardReport] = Field(default_factory=list)
    source: DataSource = DataSource.FIXTURE
    data_caveat: str = ""   # Always populated when source=FIXTURE


class SafetyAnalysis(BaseModel):
    """Result of evaluating a route or area for safety."""
    overall_score: float = Field(..., ge=0.0, le=10.0)
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    hazards_found: list[HazardReport] = Field(default_factory=list)
    missing_data_items: list[str] = Field(
        default_factory=list,
        description="Items that COULD affect safety but have no data"
    )
    # IMPORTANT: missing data ≠ safe — always surface this to caller
    explanation: str = ""
    analysed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SafeHaven(BaseModel):
    """A potentially safe location (hospital, pharmacy, police station, etc.)."""

    class PlaceType(str, Enum):
        HOSPITAL = "hospital"
        PHARMACY = "pharmacy"
        POLICE = "police"
        PETROL_STATION = "petrol_station"
        FIRE_STATION = "fire_station"
        OTHER = "other"

    place_id: str
    name: str
    place_type: PlaceType
    location: Location
    distance_km: Optional[float] = None
    # Opening hours caveat: never claim open without live verification
    opening_hours_note: str = (
        "Opening hours NOT verified. Please confirm before relying on this location."
    )
    phone: Optional[str] = None
    source: DataSource = DataSource.FIXTURE
    source_caveat: str = ""


class NavigationRequest(BaseModel):
    origin: Location
    destination: Location
    user_id: str
    prefer_safety: bool = True
    max_routes: int = Field(3, ge=1, le=5)


class NavigationResponse(BaseModel):
    request_id: str
    routes: list[RouteOption]
    recommended_route_id: Optional[str] = None
    explanation: str = ""
    data_source: DataSource = DataSource.FIXTURE
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Flag: if True, data is test fixture and must NOT be used for live navigation
    is_fixture: bool = True
