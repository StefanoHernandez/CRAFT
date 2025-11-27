"""Tests for memory management."""

import pytest
from unittest.mock import MagicMock
from craft.core.memory import Memory
from craft.providers.base import Message, Role

def test_memory_trimming_count():
    """Test trimming messages by count."""
    memory = Memory(max_messages=3)
    messages = [
        Message(role=Role.SYSTEM, content="System"),
        Message(role=Role.USER, content="1"),
        Message(role=Role.ASSISTANT, content="2"),
        Message(role=Role.USER, content="3"),
        Message(role=Role.ASSISTANT, content="4"),
    ]
    
    trimmed = memory.trim_messages(messages)
    
    # Should keep system prompt + last 3 messages
    assert len(trimmed) == 4
    assert trimmed[0].role == Role.SYSTEM
    assert trimmed[1].content == "2"
    assert trimmed[2].content == "3"
    assert trimmed[3].content == "4"

def test_memory_trimming_tokens():
    """Test trimming messages by token estimation."""
    # 1 token ~= 4 chars
    # "System" = 6 chars = 1 token
    # "Long message" = 12 chars = 3 tokens
    memory = Memory(max_tokens=10)
    
    messages = [
        Message(role=Role.SYSTEM, content="System"), # ~1 token
        Message(role=Role.USER, content="A" * 20),   # ~5 tokens
        Message(role=Role.ASSISTANT, content="B" * 20), # ~5 tokens
        Message(role=Role.USER, content="C" * 4),    # ~1 token
    ]
    
    trimmed = memory.trim_messages(messages)
    
    # Total tokens: 1 + 5 + 5 + 1 = 12 > 10
    # Should remove first non-system message ("A"*20)
    # New total: 1 + 5 + 1 = 7 <= 10
    
    assert len(trimmed) == 3
    assert trimmed[0].role == Role.SYSTEM
    assert trimmed[1].content == "B" * 20
    assert trimmed[2].content == "C" * 4

def test_memory_no_trimming_needed():
    """Test memory doesn't trim if within limits."""
    memory = Memory(max_messages=10, max_tokens=100)
    messages = [
        Message(role=Role.SYSTEM, content="System"),
        Message(role=Role.USER, content="Hi"),
    ]
    
    trimmed = memory.trim_messages(messages)
    assert len(trimmed) == 2
    assert trimmed == messages
