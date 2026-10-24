"""
models/__init__.py — Shared Pydantic models for FutureShield AI SafeHer Guardian.
"""

from .safety import (
    Location,
    RouteOption,
    SafetyAnalysis,
    HazardReport,
    SafeHaven,
    NavigationRequest,
    NavigationResponse,
)
from .guardian import (
    GuardianSession,
    TrustedContact,
    ConsentRecord,
    NotificationRecord,
)
from .emergency import (
    EmergencyRequest,
    EmergencyResponse,
    IncidentRecord,
)
from .privacy import (
    LocationShareRecord,
    AuditEntry,
    PermissionLevel,
)

__all__ = [
    "Location",
    "RouteOption",
    "SafetyAnalysis",
    "HazardReport",
    "SafeHaven",
    "NavigationRequest",
    "NavigationResponse",
    "GuardianSession",
    "TrustedContact",
    "ConsentRecord",
    "NotificationRecord",
    "EmergencyRequest",
    "EmergencyResponse",
    "IncidentRecord",
    "LocationShareRecord",
    "AuditEntry",
    "PermissionLevel",
]
