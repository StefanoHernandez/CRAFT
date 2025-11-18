"""Basic tests for Chatbot class."""

import pytest
from unittest.mock import Mock, MagicMock
from craft.core.chatbot import Chatbot
from craft.providers.base import Provider, ProviderConfig, ChatResponse, Role


class MockProvider(Provider):
    """Mock provider for testing."""

    def __init__(self):
        config = ProviderConfig(model="mock-model")
        super().__init__(config)

    def _validate_config(self):
        pass

    def chat(self, messages, stream=False, **kwargs):
        return ChatResponse(
            content="Mock response",
            role=Role.ASSISTANT,
            model="mock-model",
        )

    async def achat(self, messages, stream=False, **kwargs):
        return ChatResponse(
            content="Mock async response",
            role=Role.ASSISTANT,
            model="mock-model",
        )


def test_chatbot_initialization():
    """Test chatbot initialization."""
    provider = MockProvider()
    chatbot = Chatbot(provider=provider)

    assert chatbot.provider == provider
    assert chatbot.memory is None
    assert len(chatbot.conversation) == 0


def test_chatbot_with_system_prompt():
    """Test chatbot with system prompt."""
    provider = MockProvider()
    chatbot = Chatbot(
        provider=provider,
        system_prompt="You are a test assistant."
    )

    assert len(chatbot.conversation) == 1
    assert chatbot.conversation.messages[0].content == "You are a test assistant."


def test_chatbot_chat():
    """Test basic chat functionality."""
    provider = MockProvider()
    chatbot = Chatbot(provider=provider, memory=True)

    response = chatbot.chat("Hello!")

    assert response.content == "Mock response"
    assert len(chatbot.conversation) == 2  # User + Assistant
    assert chatbot.conversation.messages[0].content == "Hello!"
    assert chatbot.conversation.messages[1].content == "Mock response"


def test_chatbot_clear_conversation():
    """Test clearing conversation."""
    provider = MockProvider()
    chatbot = Chatbot(provider=provider)

    chatbot.chat("Test message")
    assert len(chatbot.conversation) > 0

    chatbot.clear_conversation()
    assert len(chatbot.conversation) == 0


def test_chatbot_with_memory():
    """Test chatbot with memory enabled."""
    provider = MockProvider()
    chatbot = Chatbot(provider=provider, memory=True)

    chatbot.chat("Test")
    conv_id = chatbot.save_conversation()

    assert chatbot.memory.load(conv_id) is not None
