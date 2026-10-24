"""
models/guardian.py — Guardian Mode data models.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConsentType(str, Enum):
    LOCATION_SHARE = "location_share"
    GUARDIAN_MONITORING = "guardian_monitoring"
    NOTIFICATION = "notification"


class ConsentRecord(BaseModel):
    """Immutable record of an explicit consent decision."""
    consent_id: str
    user_id: str
    consent_type: ConsentType
    granted: bool
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    scope_note: str = ""


class TrustedContact(BaseModel):
    """A trusted contact in a user's guardian network."""
    contact_id: str
    agent_address: str   # uAgent address (agent1q...)
    alias: str
    verified: bool = False   # True only after bidirectional handshake


class NotificationStatus(str, Enum):
    SIMULATED = "simulated"      # Not actually sent — for testing
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNCONFIRMED = "unconfirmed"  # Sent but no delivery receipt


class NotificationRecord(BaseModel):
    """Tracks a notification dispatched to a trusted contact."""
    notification_id: str
    session_id: str
    recipient_agent: str
    message_summary: str          # Redacted; never includes precise location without consent
    status: NotificationStatus = NotificationStatus.SIMULATED
    dispatched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: Optional[datetime] = None
    # IMPORTANT: SIMULATED means the contact was NOT actually notified.
    simulated_note: str = (
        "SIMULATED — actual delivery to trusted contact NOT confirmed. "
        "Configure TRUSTED_CONTACT_ADDRESSES in .env for real notifications."
    )


class GuardianSession(BaseModel):
    """An active guardian monitoring session."""
    session_id: str
    user_id: str
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    active: bool = True
    consents: list[ConsentRecord] = Field(default_factory=list)
    notifications_sent: list[NotificationRecord] = Field(default_factory=list)
    trusted_contacts: list[TrustedContact] = Field(default_factory=list)

    def has_consent(self, consent_type: ConsentType) -> bool:
        """Check if a valid, non-expired consent exists for this session."""
        now = datetime.now(timezone.utc)
        for c in self.consents:
            if c.consent_type == consent_type and c.granted:
                if c.expires_at is None or c.expires_at > now:
                    return True
        return False
