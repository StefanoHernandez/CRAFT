"""Tests for conversation module."""

import pytest
from datetime import datetime

from craft.core.conversation import Conversation, Message
from craft.providers.base import Role


@pytest.mark.unit
class TestMessage:
    """Test Message class."""

    def test_create_message(self):
        """Test creating a message."""
        msg = Message(role=Role.USER, content="Hello")

        assert msg.role == Role.USER
        assert msg.content == "Hello"
        # Message does not have timestamp in current implementation
        # assert isinstance(msg.timestamp, datetime)

    def test_message_serialization(self):
        """Test message serialization."""
        msg = Message(role=Role.ASSISTANT, content="Hi there")
        data = msg.model_dump()

        assert data["role"] == "assistant"
        assert data["content"] == "Hi there"
        # assert "timestamp" in data

    def test_message_deserialization(self):
        """Test message deserialization."""
        data = {
            "role": "user",
            "content": "Test message",
            "metadata": {}
        }
        msg = Message.model_validate(data)

        assert msg.role == Role.USER
        assert msg.content == "Test message"


@pytest.mark.unit
class TestConversation:
    """Test Conversation class."""

    def test_create_conversation(self):
        """Test creating a conversation."""
        conv = Conversation()

        assert conv.id is not None
        assert len(conv.messages) == 0
        assert isinstance(conv.created_at, datetime)

    def test_add_message(self):
        """Test adding messages."""
        conv = Conversation()
        
        # add_message expects role and content arguments, not a Message object
        msg = conv.add_message(Role.USER, "Hello")

        assert len(conv.messages) == 1
        assert conv.messages[0] == msg
        assert conv.messages[0].content == "Hello"
        assert conv.messages[0].role == Role.USER

    def test_add_user_message(self):
        """Test convenience method for user messages."""
        conv = Conversation()
        conv.add_user_message("Hello")

        assert len(conv.messages) == 1
        assert conv.messages[0].role == Role.USER
        assert conv.messages[0].content == "Hello"

    def test_add_assistant_message(self):
        """Test convenience method for assistant messages."""
        conv = Conversation()
        conv.add_assistant_message("Hi there")

        assert len(conv.messages) == 1
        assert conv.messages[0].role == Role.ASSISTANT
        assert conv.messages[0].content == "Hi there"

    # get_messages_for_api is not in Conversation class
    # def test_get_messages_for_api(self):
    #     """Test getting messages formatted for API."""
    #     conv = Conversation()
    #     conv.add_user_message("Hello")
    #     conv.add_assistant_message("Hi")
    #
    #     api_messages = conv.get_messages_for_api()
    #
    #     assert len(api_messages) == 2
    #     assert api_messages[0]["role"] == "user"
    #     assert api_messages[1]["role"] == "assistant"

    def test_clear_messages(self):
        """Test clearing all messages."""
        conv = Conversation()
        conv.add_user_message("Test 1")
        conv.add_user_message("Test 2")

        conv.clear()

        assert len(conv.messages) == 0

    def test_serialization(self):
        """Test conversation serialization."""
        conv = Conversation()
        conv.add_user_message("Hello")

        data = conv.model_dump()

        assert data["id"] == conv.id
        assert "messages" in data
        assert len(data["messages"]) == 1

    def test_deserialization(self):
        """Test conversation deserialization."""
        data = {
            "id": "test-123",
            "messages": [
                {"role": "user", "content": "Hello", "metadata": {}}
            ],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": {}
        }

        conv = Conversation.model_validate(data)

        assert conv.id == "test-123"
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello"

    def test_message_count(self):
        """Test getting message count."""
        conv = Conversation()
        assert len(conv) == 0

        conv.add_user_message("Test")
        assert len(conv) == 1

    def test_updated_at_changes(self):
        """Test that updated_at changes when adding messages."""
        conv = Conversation()
        original_updated = conv.updated_at

        import time
        time.sleep(0.01)  # Small delay

        conv.add_user_message("Test")

        assert conv.updated_at > original_updated
