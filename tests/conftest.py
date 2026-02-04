"""Pytest configuration and shared fixtures."""

import pytest
import os
from typing import Generator
from unittest.mock import Mock, AsyncMock

from craft.providers.base import Provider, ProviderConfig, ChatResponse, StreamChunk, Message, Role
from craft.core.conversation import Conversation
from craft.storage import SQLiteStorage


# Mock Provider for testing
class MockProvider(Provider):
    """Mock provider for testing."""

    def __init__(self, name: str = "mock", model: str = "mock-model"):
        config = ProviderConfig(api_key="mock-key", model=model)
        super().__init__(config)
        self._name = name
        self._call_count = 0
        self._responses = []
        self._should_fail = False

    @property
    def name(self) -> str:
        return self._name

    def _mock_stream_sync(self):
        """Create mock sync stream."""
        chunks = ["Mock ", "streaming ", "response"]
        for text in chunks:
            yield StreamChunk(content=text, role=Role.ASSISTANT, model=self.config.model)

    def _mock_response(self, messages: list[Message]) -> ChatResponse:
        """Create mock response."""
        if self._responses:
            content = self._responses.pop(0)
        else:
            content = f"Mock response to: {messages[-1].content}"

        return ChatResponse(
            content=content,
            role=Role.ASSISTANT,
            model=self.config.model,
            finish_reason="stop",
            usage={"input_tokens": 10, "output_tokens": 20},
        )

    async def _mock_stream(self):
        """Create mock stream."""
        chunks = ["Mock ", "streaming ", "response"]
        for text in chunks:
            yield StreamChunk(content=text, role=Role.ASSISTANT, model=self.config.model)

    def _validate_config(self) -> None:
        """Validate config."""
        pass

    def _chat(self, messages: list[Message], stream: bool = False, **kwargs):
        """Mock sync chat implementation."""
        self._call_count += 1
        if self._should_fail:
            raise Exception("Mock provider error")
        if stream:
            return self._mock_stream_sync()
        return self._mock_response(messages)

    async def _achat(self, messages: list[Message], stream: bool = False, **kwargs):
        """Mock async chat implementation."""
        self._call_count += 1
        if self._should_fail:
            raise Exception("Mock provider error")
        if stream:
            async def async_gen():
                async for chunk in self._mock_stream():
                    yield chunk
            return async_gen()
        return self._mock_response(messages)

    def set_responses(self, responses: list[str]):
        """Set predefined responses."""
        self._responses = responses

    def set_should_fail(self, should_fail: bool):
        """Configure whether provider should fail."""
        self._should_fail = should_fail


# Fixtures
@pytest.fixture
def mock_provider() -> MockProvider:
    """Create a mock provider."""
    return MockProvider()


@pytest.fixture
def conversation() -> Conversation:
    """Create a fresh conversation."""
    return Conversation()


@pytest.fixture
def sample_messages() -> list[Message]:
    """Create sample messages."""
    return [
        Message(role=Role.USER, content="Hello!"),
        Message(role=Role.ASSISTANT, content="Hi there!"),
        Message(role=Role.USER, content="How are you?"),
    ]


@pytest.fixture
def temp_sqlite_storage(tmp_path) -> Generator[SQLiteStorage, None, None]:
    """Create temporary SQLite storage."""
    db_path = tmp_path / "test.db"
    storage = SQLiteStorage(database_path=str(db_path))
    yield storage
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    mock = Mock()
    mock.messages = Mock()
    mock.messages.create = Mock()
    mock.messages.stream = Mock()
    return mock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    mock = Mock()
    mock.chat = Mock()
    mock.chat.completions = Mock()
    mock.chat.completions.create = Mock()
    return mock


@pytest.fixture(autouse=True)
def reset_env_vars():
    """Reset environment variables before each test."""
    # Store original values
    original_env = dict(os.environ)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Set mock API keys in environment."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")


# Async helpers
@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Skip markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: mark test as requiring real API keys"
    )
    config.addinivalue_line(
        "markers", "requires_storage: mark test as requiring storage backend"
    )
