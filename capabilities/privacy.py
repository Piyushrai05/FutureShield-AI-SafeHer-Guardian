"""
capabilities/privacy.py — Capability 7: Privacy and Audit.

Permission checks, data minimization, redacted logging, expiring-sharing logic,
and audit records. NEVER discloses precise location without authorization.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import config
from models.privacy import LocationShareRecord, AuditEntry, PermissionLevel

logger = logging.getLogger(__name__)

# In-memory share store
_shares: dict[str, LocationShareRecord] = {}


# ── Location sharing ──────────────────────────────────────────

def create_location_share(
    user_id: str,
    recipient_id: str,
    permission_level: PermissionLevel,
    ttl_seconds: Optional[int] = None,
) -> LocationShareRecord:
    """
    Create a time-limited location sharing grant.
    NEVER creates an indefinite share.
    """
    if permission_level == PermissionLevel.FULL:
        logger.warning(
            f"[privacy] FULL permission level requested by {user_id} — "
            "requires explicit consent check in calling code."
        )

    ttl = ttl_seconds if ttl_seconds is not None else config.LOCATION_SHARE_TTL
    share = LocationShareRecord(
        share_id=str(uuid.uuid4()),
        user_id=user_id,
        recipient_id=recipient_id,
        permission_level=permission_level,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl),
    )
    _shares[share.share_id] = share
    audit(
        event_type="location_share_created",
        user_id=user_id,
        action="create_share",
        outcome="success",
        metadata={
            "share_id": share.share_id,
            "permission_level": permission_level.value,
            "recipient_id": recipient_id,
            "expires_at": share.expires_at.isoformat(),
        },
    )
    return share


def revoke_location_share(share_id: str, user_id: str) -> bool:
    """Revoke an active location share."""
    share = _shares.get(share_id)
    if not share or share.user_id != user_id:
        return False
    share.revoked = True
    share.revoked_at = datetime.now(timezone.utc)
    audit(
        event_type="location_share_revoked",
        user_id=user_id,
        action="revoke_share",
        outcome="success",
        metadata={"share_id": share_id},
    )
    return True


def get_permission_for_recipient(
    user_id: str,
    recipient_id: str,
) -> PermissionLevel:
    """
    Return the highest active permission level the recipient holds.
    If no active share exists, return NONE — never default to exposing location.
    """
    now = datetime.now(timezone.utc)
    best = PermissionLevel.NONE

    _level_order = [
        PermissionLevel.NONE,
        PermissionLevel.ANONYMISED,
        PermissionLevel.TRUSTED,
        PermissionLevel.FULL,
    ]

    for share in _shares.values():
        if (
            share.user_id == user_id
            and share.recipient_id == recipient_id
            and share.is_active
        ):
            if _level_order.index(share.permission_level) > _level_order.index(best):
                best = share.permission_level

    return best


def filter_location_for_permission(
    lat: float,
    lon: float,
    permission: PermissionLevel,
) -> Optional[dict[str, Any]]:
    """
    Apply data minimisation. Only return what the permission level allows.

    NONE        → None (location not disclosed)
    ANONYMISED  → General area only (rounded to ~5.5 km grid)
    TRUSTED     → Rounded to ~550 m
    FULL        → Exact coordinates
    """
    if permission == PermissionLevel.NONE:
        return None  # Never disclose
    if permission == PermissionLevel.ANONYMISED:
        return {"lat": round(lat, 2), "lon": round(lon, 2), "precision": "~5km area"}
    if permission == PermissionLevel.TRUSTED:
        return {"lat": round(lat, 3), "lon": round(lon, 3), "precision": "~500m area"}
    if permission == PermissionLevel.FULL:
        return {"lat": lat, "lon": lon, "precision": "exact"}
    return None


def cleanup_expired_shares() -> int:
    """Remove expired shares from memory. Returns count removed."""
    expired = [sid for sid, s in _shares.items() if not s.is_active]
    for sid in expired:
        del _shares[sid]
    if expired:
        logger.info(f"[privacy] Cleaned up {len(expired)} expired location share(s)")
    return len(expired)


# ── Audit logging ─────────────────────────────────────────────

def audit(
    event_type: str,
    user_id: str,
    action: str,
    outcome: str,
    metadata: Optional[dict[str, Any]] = None,
    include_location: bool = False,
) -> AuditEntry:
    """
    Write a redacted audit entry to the audit log file.
    Precise location is excluded unless include_location=True.
    """
    entry = AuditEntry(
        entry_id=str(uuid.uuid4()),
        event_type=event_type,
        user_id=pseudonymise(user_id),
        action=action,
        outcome=outcome,
        metadata=metadata or {},
        location_included=include_location,
    )

    try:
        with open(config.AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.redacted_dict(), default=str) + "\n")
    except OSError as e:
        logger.error(f"[privacy] Failed to write audit log: {e}")

    return entry


def pseudonymise(user_id: str) -> str:
    """Return a one-way hash of user_id for audit records."""
    return "uid:" + hashlib.sha256(user_id.encode()).hexdigest()[:12]
