"""Anthropic (Claude) provider implementation."""

import os
from typing import Any, AsyncIterator, Dict, List, Optional, Union

try:
    from anthropic import Anthropic, AsyncAnthropic
    from anthropic.types import MessageStreamEvent
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from pydantic import Field
from craft.providers.base import (
    Provider,
    ProviderConfig,
    Message,
    ChatResponse,
    StreamChunk,
    Role,
)


class AnthropicConfig(ProviderConfig):
    """Anthropic-specific configuration."""

    model: str = Field(default="claude-3-5-sonnet-20241022")
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    max_tokens: int = Field(default=4096)


class AnthropicProvider(Provider):
    """
    Anthropic (Claude) provider implementation.

    Supports Claude 3 models with streaming.
    """

    def __init__(self, config: Optional[AnthropicConfig] = None, **kwargs: Any):
        """
        Initialize Anthropic provider.

        Args:
            config: Anthropic configuration
            **kwargs: Additional config parameters
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install 'craft-chatbot[anthropic]'"
            )

        if config is None:
            config = AnthropicConfig(**kwargs)
        elif kwargs:
            # Merge kwargs into config
            config = AnthropicConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        self.client = Anthropic(api_key=self.config.api_key)
        self.async_client = AsyncAnthropic(api_key=self.config.api_key)

    def _validate_config(self) -> None:
        """Validate Anthropic configuration."""
        if not self.config.api_key:
            raise ValueError(
                "Anthropic API key not provided. "
                "Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            )

    def format_messages(self, messages: List[Message]) -> tuple[Optional[str], List[Dict[str, str]]]:
        """
        Format messages for Anthropic API.

        Anthropic requires system messages to be separate.

        Returns:
            Tuple of (system_prompt, messages)
        """
        system_prompt = None
        formatted_messages = []

        for msg in messages:
            if msg.role == Role.SYSTEM:
                # Anthropic uses a separate system parameter
                system_prompt = msg.content
            else:
                formatted_messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        return system_prompt, formatted_messages

    def chat(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Send chat request to Anthropic.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            **kwargs: Additional Anthropic-specific parameters

        Returns:
            ChatResponse or iterator of StreamChunk if streaming
        """
        system_prompt, formatted_messages = self.format_messages(messages)

        params = {
            "model": self.config.model,
            "messages": formatted_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        if system_prompt:
            params["system"] = system_prompt

        if stream:
            return self._stream(params)
        else:
            return self._complete(params)

    def _complete(self, params: Dict[str, Any]) -> ChatResponse:
        """Complete (non-streaming) request."""
        response = self.client.messages.create(**params)

        return ChatResponse(
            content=response.content[0].text,
            role=Role.ASSISTANT,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            metadata={
                "id": response.id,
                "stop_reason": response.stop_reason,
            },
        )

    def _stream(self, params: Dict[str, Any]) -> AsyncIterator[StreamChunk]:
        """Streaming request."""
        with self.client.messages.stream(**params) as stream:
            for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamChunk(content=event.delta.text)
                    elif event.type == "message_stop":
                        yield StreamChunk(content="", finished=True)

    async def achat(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Async chat request to Anthropic.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            **kwargs: Additional Anthropic-specific parameters

        Returns:
            ChatResponse or async iterator of StreamChunk if streaming
        """
        system_prompt, formatted_messages = self.format_messages(messages)

        params = {
            "model": self.config.model,
            "messages": formatted_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        if system_prompt:
            params["system"] = system_prompt

        if stream:
            return self._astream(params)
        else:
            return await self._acomplete(params)

    async def _acomplete(self, params: Dict[str, Any]) -> ChatResponse:
        """Async complete (non-streaming) request."""
        response = await self.async_client.messages.create(**params)

        return ChatResponse(
            content=response.content[0].text,
            role=Role.ASSISTANT,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            metadata={
                "id": response.id,
                "stop_reason": response.stop_reason,
            },
        )

    async def _astream(self, params: Dict[str, Any]) -> AsyncIterator[StreamChunk]:
        """Async streaming request."""
        async with self.async_client.messages.stream(**params) as stream:
            async for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamChunk(content=event.delta.text)
                    elif event.type == "message_stop":
                        yield StreamChunk(content="", finished=True)
