"""
models/privacy.py — Privacy, audit, and data-sharing models.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    NONE = "none"
    ANONYMISED = "anonymised"    # Only general area, no precise coords
    TRUSTED = "trusted"          # Precise location to verified trusted contacts only
    FULL = "full"                # All data; requires explicit consent


class LocationShareRecord(BaseModel):
    """Time-limited location sharing grant."""
    share_id: str
    user_id: str
    recipient_id: str            # Agent address or contact ID
    permission_level: PermissionLevel
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime         # MUST be set; no indefinite sharing
    revoked: bool = False
    revoked_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        if self.revoked:
            return False
        return datetime.now(timezone.utc) < self.expires_at


class AuditEntry(BaseModel):
    """Immutable audit log entry. Written to AUDIT_LOG_FILE."""
    entry_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    user_id: str                # May be pseudonymised hash
    action: str
    outcome: str
    # Never log precise location in the audit trail without consent
    metadata: dict[str, Any] = Field(default_factory=dict)
    location_included: bool = False

    def redacted_dict(self) -> dict:
        """Return dict safe for logging: excludes any location fields."""
        d = self.model_dump()
        if not self.location_included:
            d.pop("metadata", None)  # metadata may contain location context
            d["metadata"] = "[redacted]"
        return d
