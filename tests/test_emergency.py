"""
tests/test_emergency.py — Tests for Capability 5: Emergency Assistance.
"""
import pytest
import uuid
from models.emergency import EmergencyType, EmergencyRequest, DispatchStatus
from capabilities.emergency import get_emergency_guidance


def _make_request(emergency_type=EmergencyType.GENERAL, country_code="IN"):
    return EmergencyRequest(
        request_id=str(uuid.uuid4()),
        user_id="test-user",
        emergency_type=emergency_type,
        description="Test emergency",
        country_code=country_code,
    )


def test_india_emergency_number():
    """India emergency must use 112."""
    req = _make_request(country_code="IN")
    result = get_emergency_guidance(req)
    assert result.emergency_number == "112"


def test_guidance_not_empty():
    """Guidance list must not be empty."""
    req = _make_request()
    result = get_emergency_guidance(req)
    assert len(result.guidance) > 0


def test_dispatch_never_confirmed_automatically():
    """Dispatch status must NEVER be CONFIRMED without real confirmation."""
    req = _make_request()
    result = get_emergency_guidance(req)
    assert result.dispatch_status != DispatchStatus.CONFIRMED, (
        "Dispatch should never be auto-confirmed"
    )
    assert result.dispatch_status == DispatchStatus.NOT_ATTEMPTED


def test_dispatch_note_warns_to_call():
    """Dispatch note must direct user to call emergency number."""
    req = _make_request()
    result = get_emergency_guidance(req)
    assert "112" in result.dispatch_note or "call" in result.dispatch_note.lower()


def test_medical_guidance_includes_symptoms():
    """Medical emergencies should include symptom-related guidance."""
    req = _make_request(emergency_type=EmergencyType.MEDICAL)
    result = get_emergency_guidance(req)
    full_text = " ".join(result.guidance).lower()
    assert "symptom" in full_text or "describe" in full_text


def test_incident_recorded():
    """Every emergency request must be logged to the incident record."""
    from capabilities.emergency import get_incident_log
    initial_count = len(get_incident_log())
    req = _make_request()
    get_emergency_guidance(req)
    assert len(get_incident_log()) == initial_count + 1


def test_incident_location_redacted_by_default():
    """Incident records must redact location unless explicitly given consent."""
    from capabilities.emergency import get_incident_log
    req = _make_request()
    get_emergency_guidance(req)
    latest = get_incident_log()[-1]
    assert latest.location_redacted is True
