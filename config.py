"""
config.py — Centralised configuration for FutureShield AI SafeHer Guardian.

All settings are loaded from environment variables (or .env via python-dotenv).
No secrets are hardcoded here.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env if present ──────────────────────────────────────
load_dotenv()

# ── Logging ──────────────────────────────────────────────────
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("futureshield.config")


def _require(key: str) -> str:
    """Return env var value; raise if missing."""
    value = os.getenv(key, "").strip()
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Check your .env file (copy from .env.example)."
        )
    return value


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


# ── Agent Identity ────────────────────────────────────────────
AGENT_SEED: str = _optional("AGENT_SEED", "futureshield-safeher-guardian-dev-seed-do-not-use-in-prod")
AGENT_PORT: int = int(_optional("AGENT_PORT", "8000"))
AGENT_NAME: str = "safeher_guardian"
AGENT_ENDPOINT: str = _optional("AGENT_ENDPOINT", "")

# ── Agentverse ───────────────────────────────────────────────
AGENTVERSE_API_KEY: str = _optional("AGENTVERSE_API_KEY", "")

# Mailbox is enabled only when an API key is provided
MAILBOX_ENABLED: bool = bool(AGENTVERSE_API_KEY)

# ── ASI:One LLM ──────────────────────────────────────────────
ASI1_API_KEY: str = _optional("ASI1_API_KEY", "")
ASI1_BASE_URL: str = _optional("ASI1_BASE_URL", "https://api.asi1.ai/v1")
ASI1_MODEL: str = _optional("ASI1_MODEL", "asi1-mini")
LLM_AVAILABLE: bool = bool(ASI1_API_KEY)

# ── Privacy / Sharing ────────────────────────────────────────
LOCATION_SHARE_TTL: int = int(_optional("LOCATION_SHARE_TTL_SECONDS", "3600"))

# ── Guardian Mode ────────────────────────────────────────────
_raw_contacts = _optional("TRUSTED_CONTACT_ADDRESSES", "")
TRUSTED_CONTACT_ADDRESSES: list[str] = (
    [addr.strip() for addr in _raw_contacts.split(",") if addr.strip()]
    if _raw_contacts
    else []
)

# ── Notifications ────────────────────────────────────────────
NOTIFICATION_WEBHOOK_URL: str = _optional("NOTIFICATION_WEBHOOK_URL", "")

# ── Routing Provider ─────────────────────────────────────────
ROUTING_API_KEY: str = _optional("ROUTING_API_KEY", "")
ROUTING_PROVIDER: str = _optional("ROUTING_PROVIDER", "fixture")  # fixture | ors | here

# ── Safe-Haven / POI Provider ────────────────────────────────
POI_API_KEY: str = _optional("POI_API_KEY", "")
POI_PROVIDER: str = _optional("POI_PROVIDER", "fixture")  # fixture | overpass | google

# ── Audit Logging ────────────────────────────────────────────
AUDIT_LOG_FILE: Path = Path(_optional("AUDIT_LOG_FILE", "logs/audit.jsonl"))
AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── Emergency ────────────────────────────────────────────────
EMERGENCY_NUMBER_INDIA: str = "112"

# ── Sanity summary at startup ────────────────────────────────
def log_config_summary() -> None:
    logger.info("=== SafeHer Guardian — Configuration Summary ===")
    logger.info(f"  AGENT_NAME     : {AGENT_NAME}")
    logger.info(f"  AGENT_PORT     : {AGENT_PORT}")
    logger.info(f"  AGENT_ENDPOINT : {AGENT_ENDPOINT or '[none — local only]'}")
    logger.info(f"  MAILBOX_ENABLED: {MAILBOX_ENABLED}")
    logger.info(f"  LLM_AVAILABLE  : {LLM_AVAILABLE}  (model={ASI1_MODEL})")
    logger.info(f"  ROUTING        : {ROUTING_PROVIDER}")
    logger.info(f"  POI            : {POI_PROVIDER}")
    logger.info(f"  TRUSTED_CONTACTS: {len(TRUSTED_CONTACT_ADDRESSES)} configured")
    logger.info(f"  AUDIT_LOG      : {AUDIT_LOG_FILE}")
    logger.info("=================================================")
