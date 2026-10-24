"""
tests/test_guardian.py — Tests for Capability 4: Guardian Mode.
"""
import pytest
from datetime import datetime, timedelta
from models.guardian import ConsentType, NotificationStatus
from capabilities import guardian as guardian_cap


def test_session_created():
    """A new session should be active."""
    session = guardian_cap.create_session("test-user-1")
    assert session.active is True
    assert session.user_id == "test-user-1"


def test_consent_grant_and_check():
    """Granted consent should pass the check."""
    session = guardian_cap.create_session("test-user-2")
    guardian_cap.grant_consent(
        session.session_id,
        ConsentType.LOCATION_SHARE,
        ttl_seconds=3600,
    )
    assert guardian_cap.check_consent(session.session_id, ConsentType.LOCATION_SHARE) is True


def test_consent_check_fails_without_grant():
    """Consent check must return False when no consent was given."""
    session = guardian_cap.create_session("test-user-3")
    assert guardian_cap.check_consent(session.session_id, ConsentType.NOTIFICATION) is False


def test_end_session():
    """Ending a session sets active=False."""
    session = guardian_cap.create_session("test-user-4")
    result = guardian_cap.end_session(session.session_id)
    assert result is True
    stored = guardian_cap.get_session(session.session_id)
    assert stored.active is False


def test_no_contacts_gives_simulated_notification():
    """When no contacts are configured, notification is SIMULATED."""
    import asyncio
    session = guardian_cap.create_session("test-user-5")
    guardian_cap.grant_consent(session.session_id, ConsentType.NOTIFICATION)

    records = asyncio.run(
        guardian_cap.notify_trusted_contacts(
            session_id=session.session_id,
            message_summary="Test alert",
            ctx=None,  # No real context
        )
    )
    assert len(records) >= 1
    assert all(r.status == NotificationStatus.SIMULATED for r in records)


def test_notification_without_consent_raises():
    """Notifying without consent must raise PermissionError."""
    import asyncio
    session = guardian_cap.create_session("test-user-6")
    # No consent granted
    with pytest.raises(PermissionError):
        asyncio.run(
            guardian_cap.notify_trusted_contacts(
                session_id=session.session_id,
                message_summary="Test",
            )
        )
