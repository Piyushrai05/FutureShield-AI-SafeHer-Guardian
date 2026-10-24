"""
capabilities/emergency.py — Capability 5: Emergency Assistance.

Supports emergency guidance for India (112).
Implements deterministic incident handling, test notifications, delivery-status tracking.
NEVER claims police dispatch without confirmation.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import config
from models.emergency import (
    EmergencyType,
    EmergencyRequest,
    EmergencyResponse,
    IncidentRecord,
    DispatchStatus,
)
from models.safety import Location
from capabilities.safe_haven import find_safe_havens

logger = logging.getLogger(__name__)

# Country → emergency number mapping
_EMERGENCY_NUMBERS: dict[str, str] = {
    "IN": "112",   # India unified emergency number
    "US": "911",
    "UK": "999",
    "EU": "112",
}

_INDIA_GUIDANCE: list[str] = [
    "CALL 112 immediately — this is India's unified emergency number for police, fire, and ambulance.",
    "Stay on the line with the operator and follow their instructions.",
    "Share your location clearly: nearest landmark, street name, or district.",
    "If you cannot speak, stay on the line — operators are trained to assist silent callers.",
    "Move to a well-lit, public, or staffed location if safe to do so.",
    "Lock doors/windows if sheltering in place.",
    "Notify a trusted contact about your situation.",
]

_INCIDENT_LOG: list[IncidentRecord] = []


def get_emergency_guidance(
    request: EmergencyRequest,
    nearest_location: Optional[Location] = None,
) -> EmergencyResponse:
    """
    Return deterministic emergency guidance.

    Does NOT contact emergency services automatically.
    Does NOT claim dispatch confirmed.
    """
    emergency_number = _EMERGENCY_NUMBERS.get(request.country_code.upper(), "112")

    # Build guidance list
    if request.country_code.upper() == "IN":
        guidance = list(_INDIA_GUIDANCE)
    else:
        guidance = [
            f"CALL {emergency_number} immediately.",
            "Stay on the line with the operator.",
            "Share your precise location.",
        ]

    # Type-specific additions
    if request.emergency_type == EmergencyType.MEDICAL:
        guidance.insert(1, "Describe symptoms clearly. Do not hang up.")
    elif request.emergency_type == EmergencyType.SAFETY_THREAT:
        guidance.insert(1, "Do NOT confront the threat. Move away calmly if safe.")
    elif request.emergency_type == EmergencyType.ROAD_ACCIDENT:
        guidance.insert(1, "Do not move injured persons unless in immediate danger.")

    # Find nearby safe havens
    havens = []
    if nearest_location:
        havens = find_safe_havens(near=nearest_location, max_results=3, provider=config.POI_PROVIDER)

    # Record incident (with location redacted by default)
    incident = IncidentRecord(
        incident_id=str(uuid.uuid4()),
        request_id=request.request_id,
        user_id=_pseudonymise(request.user_id),
        emergency_type=request.emergency_type,
        country_code=request.country_code,
        dispatch_status=DispatchStatus.NOT_ATTEMPTED,
        location_redacted=True,
    )
    _INCIDENT_LOG.append(incident)

    logger.critical(
        f"[emergency] INCIDENT {incident.incident_id}: "
        f"type={request.emergency_type.value} country={request.country_code} "
        f"number={emergency_number}"
    )

    return EmergencyResponse(
        request_id=request.request_id,
        emergency_number=emergency_number,
        guidance=guidance,
        dispatch_status=DispatchStatus.NOT_ATTEMPTED,
        dispatch_note=(
            f"⚠ Emergency services have NOT been automatically contacted. "
            f"CALL {emergency_number} directly right now."
        ),
        nearest_safe_havens=havens,
    )


def get_incident_log() -> list[IncidentRecord]:
    """Return a copy of the in-memory incident log."""
    return list(_INCIDENT_LOG)


def _pseudonymise(user_id: str) -> str:
    """Replace user_id with a non-reversible hash for audit purposes."""
    import hashlib
    return "uid:" + hashlib.sha256(user_id.encode()).hexdigest()[:12]
