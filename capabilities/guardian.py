"""
capabilities/guardian.py — Capability 4: Guardian Mode.

Consent validation, trusted-contact workflows, authorization checks.
CLEARLY distinguishes simulated notifications from actual delivery.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import config
from models.guardian import (
    GuardianSession,
    TrustedContact,
    ConsentRecord,
    ConsentType,
    NotificationRecord,
    NotificationStatus,
)

logger = logging.getLogger(__name__)

# In-memory session store (single agent; replace with persistent store for multi-user)
_sessions: dict[str, GuardianSession] = {}


# ── Session management ────────────────────────────────────────

def create_session(user_id: str) -> GuardianSession:
    """Create a new guardian session for a user."""
    session_id = str(uuid.uuid4())
    session = GuardianSession(session_id=session_id, user_id=user_id)
    _sessions[session_id] = session
    logger.info(f"[guardian] Session created: {session_id} user={user_id}")
    return session


def get_session(session_id: str) -> Optional[GuardianSession]:
    return _sessions.get(session_id)


def end_session(session_id: str) -> bool:
    session = _sessions.get(session_id)
    if session:
        session.active = False
        session.end_time = datetime.now(timezone.utc)
        logger.info(f"[guardian] Session ended: {session_id}")
        return True
    return False


# ── Consent management ────────────────────────────────────────

def grant_consent(
    session_id: str,
    consent_type: ConsentType,
    ttl_seconds: Optional[int] = None,
    scope_note: str = "",
) -> ConsentRecord:
    """Record explicit consent. TTL defaults to config.LOCATION_SHARE_TTL."""
    session = _sessions.get(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")

    ttl = ttl_seconds if ttl_seconds is not None else config.LOCATION_SHARE_TTL
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

    record = ConsentRecord(
        consent_id=str(uuid.uuid4()),
        user_id=session.user_id,
        consent_type=consent_type,
        granted=True,
        expires_at=expires_at,
        scope_note=scope_note or f"Granted via guardian session {session_id}",
    )
    session.consents.append(record)
    logger.info(
        f"[guardian] Consent granted: type={consent_type.value} "
        f"session={session_id} expires={expires_at.isoformat()}"
    )
    return record


def check_consent(session_id: str, consent_type: ConsentType) -> bool:
    """Return True only if a valid, non-expired consent exists."""
    session = _sessions.get(session_id)
    if not session:
        return False
    result = session.has_consent(consent_type)
    if not result:
        logger.warning(
            f"[guardian] Consent check FAILED: type={consent_type.value} session={session_id}"
        )
    return result


# ── Trusted-contact management ────────────────────────────────

def add_trusted_contact(
    session_id: str,
    agent_address: str,
    alias: str,
) -> TrustedContact:
    session = _sessions.get(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")

    contact = TrustedContact(
        contact_id=str(uuid.uuid4()),
        agent_address=agent_address,
        alias=alias,
        verified=False,  # Requires bidirectional handshake to verify
    )
    session.trusted_contacts.append(contact)
    logger.info(f"[guardian] Trusted contact added: {alias} ({agent_address})")
    return contact


# ── Notification dispatch ─────────────────────────────────────

async def notify_trusted_contacts(
    session_id: str,
    message_summary: str,
    ctx=None,  # uAgents Context — None in tests
) -> list[NotificationRecord]:
    """
    Attempt to notify trusted contacts.

    When ctx is None or no real contacts are configured → SIMULATED.
    When ctx is provided and contacts have agent addresses → actual uAgent message.
    Status clearly recorded as SIMULATED vs DELIVERED.
    """
    session = _sessions.get(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")

    if not check_consent(session_id, ConsentType.NOTIFICATION):
        raise PermissionError(
            f"Notification consent not granted for session {session_id}"
        )

    records: list[NotificationRecord] = []

    # Determine real contacts
    real_contacts = [
        c for c in session.trusted_contacts
        if c.agent_address and c.agent_address.startswith("agent1q")
    ]
    # Also include configured contacts from env
    env_contacts = [
        TrustedContact(
            contact_id=f"env-{i}",
            agent_address=addr,
            alias=f"env-contact-{i}",
            verified=False,
        )
        for i, addr in enumerate(config.TRUSTED_CONTACT_ADDRESSES)
    ]
    all_contacts = real_contacts + env_contacts

    if not all_contacts:
        # No contacts configured — record as SIMULATED
        record = NotificationRecord(
            notification_id=str(uuid.uuid4()),
            session_id=session_id,
            recipient_agent="[none configured]",
            message_summary=message_summary[:200],
            status=NotificationStatus.SIMULATED,
        )
        records.append(record)
        session.notifications_sent.append(record)
        logger.warning(
            f"[guardian] No contacts configured — notification SIMULATED only. "
            f"session={session_id}"
        )
        return records

    for contact in all_contacts:
        status = NotificationStatus.SIMULATED
        if ctx is not None:
            try:
                from uagents import Model as UModel
                class AlertMsg(UModel):
                    text: str
                await ctx.send(contact.agent_address, AlertMsg(text=message_summary))
                status = NotificationStatus.UNCONFIRMED  # Sent, no delivery receipt
                logger.info(f"[guardian] Notification sent to {contact.alias} ({contact.agent_address})")
            except Exception as e:
                status = NotificationStatus.FAILED
                logger.error(f"[guardian] Failed to notify {contact.alias}: {e}")
        else:
            logger.info(f"[guardian] SIMULATED notification to {contact.alias} (no ctx provided)")

        record = NotificationRecord(
            notification_id=str(uuid.uuid4()),
            session_id=session_id,
            recipient_agent=contact.agent_address,
            message_summary=message_summary[:200],
            status=status,
            delivered_at=datetime.now(timezone.utc) if status == NotificationStatus.UNCONFIRMED else None,
        )
        records.append(record)
        session.notifications_sent.append(record)

    return records
