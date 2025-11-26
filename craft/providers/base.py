"""Base provider interface and models."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class Role(str, Enum):
    """Message role types."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message model."""

    role: Role
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamChunk(BaseModel):
    """Streaming response chunk."""

    content: str
    finished: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Complete chat response."""

    content: str
    role: Role = Role.ASSISTANT
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        return self.content


class ProviderConfig(BaseModel):
    """Base configuration for providers."""

    api_key: Optional[str] = None
    model: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    timeout: int = Field(default=60, ge=1)
    max_retries: int = Field(default=3, ge=0)

    model_config = ConfigDict(extra="allow")


class Provider(ABC):
    """
    Abstract base class for LLM providers.

    All provider implementations must inherit from this class.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration."""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List["Tool"]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Send chat request to provider.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            tools: Optional list of tools available to the model
            tool_choice: Tool choice control ("auto", "none", "required", tool name, or list)
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse or AsyncIterator of StreamChunk if streaming
        """
        pass

    @abstractmethod
    async def achat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List["Tool"]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Async version of chat.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            tools: Optional list of tools available to the model
            tool_choice: Tool choice control ("auto", "none", "required", tool name, or list)
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse or AsyncIterator of StreamChunk if streaming
        """
        pass

    def format_messages(self, messages: List[Message]) -> Any:
        """
        Format messages for provider-specific API.

        Args:
            messages: List of messages

        Returns:
            Formatted messages
        """
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    @property
    def name(self) -> str:
        """Get provider name."""
        return self.__class__.__name__.replace("Provider", "").lower()

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self.config.model

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.config.model})"
