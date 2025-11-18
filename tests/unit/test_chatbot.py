"""Tests for chatbot module."""

import pytest
from unittest.mock import Mock, patch

from craft.core.chatbot import Chatbot
from craft.core.conversation import Conversation
from craft.providers.base import Role, ChatResponse


@pytest.mark.unit
class TestChatbot:
    """Test Chatbot class."""

    def test_create_chatbot(self, mock_provider):
        """Test creating a chatbot."""
        chatbot = Chatbot(provider=mock_provider)

        assert chatbot.provider == mock_provider
        assert isinstance(chatbot.conversation, Conversation)
        assert chatbot.system_prompt is None

    def test_create_with_system_prompt(self, mock_provider):
        """Test creating chatbot with system prompt."""
        system_prompt = "You are a helpful assistant."
        chatbot = Chatbot(provider=mock_provider, system_prompt=system_prompt)

        assert chatbot.system_prompt == system_prompt

    def test_create_with_memory(self, mock_provider):
        """Test creating chatbot with memory enabled."""
        chatbot = Chatbot(provider=mock_provider, memory=True)

        assert chatbot.memory is not None

    def test_chat_basic(self, mock_provider):
        """Test basic chat."""
        chatbot = Chatbot(provider=mock_provider)
        response = chatbot.chat("Hello!")

        assert isinstance(response, ChatResponse)
        assert response.content is not None
        assert len(chatbot.conversation.messages) == 2  # User + assistant

    def test_chat_adds_to_conversation(self, mock_provider):
        """Test that chat adds messages to conversation."""
        chatbot = Chatbot(provider=mock_provider)
        user_message = "What is AI?"

        chatbot.chat(user_message)

        messages = chatbot.conversation.messages
        assert len(messages) == 2
        assert messages[0].role == Role.USER
        assert messages[0].content == user_message
        assert messages[1].role == Role.ASSISTANT

    def test_chat_with_system_prompt(self, mock_provider):
        """Test chat with system prompt."""
        system_prompt = "You are a helpful assistant."
        chatbot = Chatbot(provider=mock_provider, system_prompt=system_prompt)

        chatbot.chat("Hello")

        # System prompt should be included in provider call
        assert mock_provider._call_count == 1

    def test_chat_streaming(self, mock_provider):
        """Test streaming chat."""
        chatbot = Chatbot(provider=mock_provider)

        chunks = list(chatbot.chat("Hello", stream=True))

        assert len(chunks) > 0
        # Check that chunks are yielded

    def test_clear_conversation(self, mock_provider):
        """Test clearing conversation."""
        chatbot = Chatbot(provider=mock_provider)

        chatbot.chat("Message 1")
        chatbot.chat("Message 2")
        assert len(chatbot.conversation.messages) > 0

        chatbot.clear_conversation()
        assert len(chatbot.conversation.messages) == 0

    def test_provider_error_handling(self, mock_provider):
        """Test handling provider errors."""
        mock_provider.set_should_fail(True)
        chatbot = Chatbot(provider=mock_provider)

        with pytest.raises(Exception, match="Mock provider error"):
            chatbot.chat("This should fail")

    def test_chat_with_empty_message(self, mock_provider):
        """Test chat with empty message."""
        chatbot = Chatbot(provider=mock_provider)

        # Should handle empty messages
        response = chatbot.chat("")
        assert response is not None

    def test_multiple_chats_maintain_context(self, mock_provider):
        """Test that multiple chats maintain conversation context."""
        chatbot = Chatbot(provider=mock_provider)

        chatbot.chat("My name is Alice")
        chatbot.chat("What is my name?")

        # Both user messages and responses should be in conversation
        assert len(chatbot.conversation.messages) == 4

    def test_chat_with_predefined_responses(self, mock_provider):
        """Test chat with predefined mock responses."""
        mock_provider.set_responses(["Response 1", "Response 2"])
        chatbot = Chatbot(provider=mock_provider)

        response1 = chatbot.chat("Message 1")
        response2 = chatbot.chat("Message 2")

        assert response1.content == "Response 1"
        assert response2.content == "Response 2"

    def test_new_conversation(self, mock_provider):
        """Test starting a new conversation."""
        chatbot = Chatbot(provider=mock_provider)

        chatbot.chat("Message 1")
        old_conv_id = chatbot.conversation.id

        chatbot.new_conversation()
        new_conv_id = chatbot.conversation.id

        assert old_conv_id != new_conv_id
        assert len(chatbot.conversation.messages) == 0

    def test_set_conversation(self, mock_provider):
        """Test setting a specific conversation."""
        chatbot = Chatbot(provider=mock_provider)

        new_conv = Conversation()
        new_conv.add_user_message("Pre-existing message")

        chatbot.conversation = new_conv

        assert chatbot.conversation.id == new_conv.id
        assert len(chatbot.conversation.messages) == 1
