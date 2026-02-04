"""Base provider interface and models."""

import random
import time
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
    role: Optional[Role] = None
    model: Optional[str] = None
    finished: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Complete chat response."""

    content: str
    role: Role = Role.ASSISTANT
    model: str
    finish_reason: Optional[str] = None
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

    def chat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List["Tool"]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Send chat request to provider with automatic retries.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            tools: Optional list of tools available to the model
            tool_choice: Tool choice control
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse or AsyncIterator of StreamChunk if streaming
        """
        # We don't retry streaming responses for now as it's complex to resume
        if stream:
            return self._chat(messages, stream=True, tools=tools, tool_choice=tool_choice, **kwargs)

        # Custom retry logic to respect 'retryable' flag
        from craft.core.errors import ProviderError
        import random
        
        attempt = 0
        while True:
            try:
                return self._chat(messages, stream=False, tools=tools, tool_choice=tool_choice, **kwargs)
            except ProviderError as e:
                # Stop immediately if not retryable
                if not e.retryable or attempt >= self.config.max_retries:
                    raise e
                
                attempt += 1
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
            except Exception as e:
                # For generic exceptions, we assume they might be transient
                if attempt >= self.config.max_retries:
                    raise e
                
                attempt += 1
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)

    @abstractmethod
    def _chat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List["Tool"]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Internal method to send chat request to provider.
        Must be implemented by subclasses.
        """
        pass

    async def achat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List["Tool"]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Async version of chat with automatic retries.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            tools: Optional list of tools available to the model
            tool_choice: Tool choice control
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse or AsyncIterator of StreamChunk if streaming
        """
        if stream:
            return await self._achat(messages, stream=True, tools=tools, tool_choice=tool_choice, **kwargs)

        # Custom async retry logic to respect 'retryable' flag
        from craft.core.errors import ProviderError
        import random
        import asyncio
        
        attempt = 0
        while True:
            try:
                return await self._achat(messages, stream=False, tools=tools, tool_choice=tool_choice, **kwargs)
            except ProviderError as e:
                # Stop immediately if not retryable
                if not e.retryable or attempt >= self.config.max_retries:
                    raise e
                
                attempt += 1
                delay = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            except Exception as e:
                # For generic exceptions, we assume they might be transient
                if attempt >= self.config.max_retries:
                    raise e
                
                attempt += 1
                delay = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)

    @abstractmethod
    async def _achat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List["Tool"]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Internal async method to send chat request to provider.
        Must be implemented by subclasses.
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
