"""
tests/test_privacy.py — Tests for Capability 7: Privacy and Audit.
"""
import pytest
from datetime import timedelta
from models.privacy import PermissionLevel
from capabilities import privacy as privacy_cap


def test_no_permission_returns_none_location():
    """NONE permission must never disclose location."""
    result = privacy_cap.filter_location_for_permission(12.9716, 77.5946, PermissionLevel.NONE)
    assert result is None


def test_anonymised_location_is_coarsened():
    """ANONYMISED must return a significantly rounded location."""
    result = privacy_cap.filter_location_for_permission(12.9716, 77.5946, PermissionLevel.ANONYMISED)
    assert result is not None
    # Rounded to 2 decimal places (~5 km precision)
    assert result["lat"] == round(12.9716, 2)
    assert result["lon"] == round(77.5946, 2)


def test_full_permission_exact_location():
    """FULL permission must return exact coordinates."""
    result = privacy_cap.filter_location_for_permission(12.9716, 77.5946, PermissionLevel.FULL)
    assert result is not None
    assert result["lat"] == 12.9716
    assert result["lon"] == 77.5946


def test_create_share_has_expiry():
    """Created share must have an expiry date."""
    share = privacy_cap.create_location_share(
        user_id="user-a",
        recipient_id="contact-b",
        permission_level=PermissionLevel.TRUSTED,
        ttl_seconds=300,
    )
    assert share.expires_at is not None
    assert share.is_active is True


def test_revoke_share():
    """Revoking a share must make it inactive."""
    share = privacy_cap.create_location_share(
        user_id="user-c",
        recipient_id="contact-d",
        permission_level=PermissionLevel.ANONYMISED,
        ttl_seconds=3600,
    )
    result = privacy_cap.revoke_location_share(share.share_id, "user-c")
    assert result is True
    assert share.revoked is True
    assert share.is_active is False


def test_no_share_returns_none_permission():
    """Recipient with no active share must get NONE permission."""
    perm = privacy_cap.get_permission_for_recipient("user-x", "contact-y")
    assert perm == PermissionLevel.NONE


def test_audit_entry_written(tmp_path, monkeypatch):
    """Audit entries must be written to the audit log file."""
    import config
    monkeypatch.setattr(config, "AUDIT_LOG_FILE", tmp_path / "audit.jsonl")
    (tmp_path / "audit.jsonl").parent.mkdir(parents=True, exist_ok=True)

    privacy_cap.audit(
        event_type="test_event",
        user_id="test-user",
        action="test_action",
        outcome="success",
    )
    content = (tmp_path / "audit.jsonl").read_text()
    assert "test_event" in content


def test_pseudonymise_is_not_reversible():
    """Pseudonymised ID must not contain the original user_id."""
    result = privacy_cap.pseudonymise("real-user-id-12345")
    assert "real-user-id-12345" not in result
    assert result.startswith("uid:")
