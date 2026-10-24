"""
models/emergency.py — Emergency assistance data models.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EmergencyType(str, Enum):
    GENERAL = "general"
    MEDICAL = "medical"
    SAFETY_THREAT = "safety_threat"
    ROAD_ACCIDENT = "road_accident"
    FIRE = "fire"
    OTHER = "other"


class DispatchStatus(str, Enum):
    NOT_ATTEMPTED = "not_attempted"
    SIMULATED = "simulated"       # Test/demo mode — police NOT notified
    CALL_INITIATED = "call_initiated"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    # IMPORTANT: never return CONFIRMED without real confirmation


class EmergencyRequest(BaseModel):
    request_id: str
    user_id: str
    emergency_type: EmergencyType
    description: str
    location: Optional[object] = None  # models.safety.Location — avoids circular import
    country_code: str = "IN"           # Default: India
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmergencyResponse(BaseModel):
    request_id: str
    emergency_number: str            # e.g. "112" for India
    guidance: list[str]              # Ordered steps the user should take
    dispatch_status: DispatchStatus = DispatchStatus.NOT_ATTEMPTED
    dispatch_note: str = (
        "Emergency services have NOT been automatically contacted. "
        "Please call the number shown directly."
    )
    nearest_safe_havens: list[object] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IncidentRecord(BaseModel):
    """Audit record for every emergency event."""
    incident_id: str
    request_id: str
    user_id: str                  # May be pseudonymised
    emergency_type: EmergencyType
    country_code: str
    dispatch_status: DispatchStatus
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Location is stored only with explicit consent; otherwise None
    location_redacted: bool = True
