"""
tests/test_agent_chat.py — Tests for Agent Chat Protocol message handling in agent.py.
"""
from __future__ import annotations

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
import uuid

from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
)
import agent


class MockContext:
    def __init__(self):
        self.sent_messages = []
        self.logger = MagicMock()
        self.address = "agent1q_test_safeher_guardian"

    async def send(self, destination: str, message: object):
        self.sent_messages.append((destination, message))


@pytest.mark.asyncio
async def test_chat_message_acknowledgement_and_reply():
    """Agent must send ChatAcknowledgement and a reply ChatMessage."""
    ctx = MockContext()
    sender = "agent1q_user_sender"
    test_msg_id = uuid.uuid4()

    msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=test_msg_id,
        content=[TextContent(type="text", text="What is FutureShield?")],
    )

    await agent.handle_chat_message(ctx, sender, msg)

    # Must have sent at least 2 messages: Ack + Reply
    assert len(ctx.sent_messages) == 2

    # First message: ChatAcknowledgement
    dest1, ack = ctx.sent_messages[0]
    assert dest1 == sender
    assert isinstance(ack, ChatAcknowledgement)
    assert ack.acknowledged_msg_id == test_msg_id

    # Second message: ChatMessage with TextContent
    dest2, reply = ctx.sent_messages[1]
    assert dest2 == sender
    assert isinstance(reply, ChatMessage)
    assert len(reply.content) > 0
    assert isinstance(reply.content[0], TextContent)
    assert len(reply.content[0].text) > 0


@pytest.mark.asyncio
async def test_empty_chat_message_handling():
    """Agent must handle empty messages gracefully without error."""
    ctx = MockContext()
    sender = "agent1q_user_sender"
    test_msg_id = uuid.uuid4()

    msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=test_msg_id,
        content=[],
    )

    await agent.handle_chat_message(ctx, sender, msg)

    assert len(ctx.sent_messages) == 2
    dest2, reply = ctx.sent_messages[1]
    assert isinstance(reply, ChatMessage)
    assert "empty" in reply.content[0].text.lower()


@pytest.mark.asyncio
async def test_chat_message_emergency_handling():
    """Emergency queries must yield immediate 112 emergency response."""
    ctx = MockContext()
    sender = "agent1q_emergency_user"
    test_msg_id = uuid.uuid4()

    msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=test_msg_id,
        content=[TextContent(type="text", text="Help me! Emergency situation, danger!")],
    )

    await agent.handle_chat_message(ctx, sender, msg)

    assert len(ctx.sent_messages) == 2
    _, reply = ctx.sent_messages[1]
    assert "112" in reply.content[0].text
