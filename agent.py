"""
agent.py — FutureShield AI SafeHer Guardian uAgent.

Implements the official Agent Chat Protocol for Agentverse/ASI:One integration.
Run locally with: python agent.py

Agentverse onboarding:
  1. python agent.py  (copy the agent address printed on startup)
  2. Visit https://agentverse.ai/inspect/?uri=http://127.0.0.1:<PORT>&address=<ADDR>
  3. Click Connect → Mailbox to link to Agentverse
"""
from __future__ import annotations

import sys
import os

# ── Ensure project root is on sys.path ────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime, timedelta, timezone

# ── Project imports ───────────────────────────────────────────
import config
config.log_config_summary()

import coordinator
from capabilities import privacy as privacy_cap

# ── uAgents imports ───────────────────────────────────────────
try:
    from uagents import Agent, Context, Protocol
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement,
        ChatMessage,
        TextContent,
        chat_protocol_spec,
    )
    UAGENTS_AVAILABLE = True
except ImportError as e:
    logging.critical(f"[agent] uAgents not importable: {e}")
    UAGENTS_AVAILABLE = False

logger = logging.getLogger("futureshield.agent")

# ── Agent instantiation ───────────────────────────────────────
if UAGENTS_AVAILABLE:
    endpoint_param = None
    if config.AGENT_ENDPOINT:
        clean_ep = config.AGENT_ENDPOINT.rstrip("/")
        if not clean_ep.endswith("/submit"):
            clean_ep = f"{clean_ep}/submit"
        endpoint_param = [clean_ep]

    agent = Agent(
        name=config.AGENT_NAME,
        seed=config.AGENT_SEED,
        port=config.AGENT_PORT,
        endpoint=endpoint_param,
        mailbox=True if not endpoint_param else config.MAILBOX_ENABLED,
        readme_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        description=(
            "SafeHer Guardian: AI-powered safety assistant providing safety-first navigation, "
            "safe haven discovery, consent-based guardian monitoring, and India 112 emergency guidance."
        ),
        publish_agent_details=True,
        report_events=True,
    )

    # ── Chat Protocol handler ─────────────────────────────────
    chat_proto = Protocol(spec=chat_protocol_spec)

    @chat_proto.on_message(ChatMessage)
    async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
        """
        Receive a ChatMessage via Agent Chat Protocol.
        1. Acknowledge receipt
        2. Extract text
        3. Route to coordinator
        4. Return structured plain-text reply
        """
        # 1. Acknowledge
        await ctx.send(
            sender,
            ChatAcknowledgement(acknowledged_msg_id=msg.msg_id),
        )

        # 2. Extract user text
        user_text = ""
        for item in msg.content:
            if isinstance(item, TextContent):
                user_text = item.text
                break

        if not user_text.strip():
            reply_text = "I received an empty message. Please describe what you need."
        else:
            ctx.logger.info(f"[agent] Received from {sender[:12]}…: {user_text[:80]}")

            # 3. Coordinate
            try:
                result = coordinator.process_message(user_text)
                reply_text = result.get("explanation", str(result))

                # Append data-quality notice when fixtures are in use
                if result.get("is_fixture"):
                    reply_text += (
                        "\n\n⚠ DATA NOTICE: Results above are from static test fixtures, "
                        "not live sources. Do not rely on this for real navigation or safety decisions."
                    )
            except Exception as e:
                ctx.logger.error(f"[agent] Coordinator error: {e}")
                reply_text = (
                    f"Sorry, I encountered an internal error: {e}. "
                    "If this is an emergency, call 112 immediately."
                )

        # 4. Reply
        reply_msg = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=msg.msg_id,
            content=[TextContent(type="text", text=reply_text)],
        )
        await ctx.send(sender, reply_msg)

        # Audit the interaction (no location, no PII)
        privacy_cap.audit(
            event_type="chat_interaction",
            user_id=sender,
            action="process_chat_message",
            outcome="replied",
        )

    @chat_proto.on_message(ChatAcknowledgement)
    async def handle_chat_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
        """Handle incoming ChatAcknowledgement confirming receipt of our outbound message."""
        ctx.logger.info(
            f"[agent] Received delivery acknowledgement from {sender[:12]}… "
            f"for message {msg.acknowledged_msg_id}"
        )

    # ── Startup event ─────────────────────────────────────────
    @agent.on_event("startup")
    async def on_startup(ctx: Context):
        ctx.logger.info("=" * 60)
        ctx.logger.info("  FutureShield AI — SafeHer Guardian")
        ctx.logger.info(f"  Agent address : {ctx.address}")
        ctx.logger.info(f"  Mailbox       : {config.MAILBOX_ENABLED}")
        ctx.logger.info(f"  LLM available : {config.LLM_AVAILABLE}")
        ctx.logger.info(f"  Routing       : {config.ROUTING_PROVIDER}")
        ctx.logger.info(f"  POI provider  : {config.POI_PROVIDER}")
        ctx.logger.info("=" * 60)
        ctx.logger.info(
            "Agent Inspector: "
            f"https://agentverse.ai/inspect/?uri=http://127.0.0.1:{config.AGENT_PORT}"
            f"&address={ctx.address}"
        )
        ctx.logger.info(
            "NOTE: To connect to Agentverse, add AGENTVERSE_API_KEY to .env and restart."
        )

    # ── Periodic cleanup ──────────────────────────────────────
    @agent.on_interval(period=3600.0)  # Every hour
    async def cleanup_expired_shares(ctx: Context):
        removed = privacy_cap.cleanup_expired_shares()
        if removed:
            ctx.logger.info(f"[agent] Cleaned up {removed} expired location share(s)")

    # Include protocol (publishes manifest so Agentverse/ASI:One can discover it)
    agent.include(chat_proto, publish_manifest=True)


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    if not UAGENTS_AVAILABLE:
        print("ERROR: uagents not installed. Run: pip install 'uagents>=0.25.5' uagents-core")
        sys.exit(1)
    agent.run()
