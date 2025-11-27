"""OpenAI provider implementation."""

import os
from typing import Any, AsyncIterator, Dict, List, Optional, Union

try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from pydantic import Field
from craft.providers.base import (
    Provider,
    ProviderConfig,
    Message,
    ChatResponse,
    StreamChunk,
    Role,
)


class OpenAIConfig(ProviderConfig):
    """OpenAI-specific configuration."""

    model: str = Field(default="gpt-4o")
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    max_tokens: Optional[int] = Field(default=None)
    base_url: Optional[str] = Field(default=None)


class OpenAIProvider(Provider):
    """
    OpenAI provider implementation.

    Supports GPT-4, GPT-3.5, and compatible models with streaming.
    """

    def __init__(self, config: Optional[OpenAIConfig] = None, **kwargs: Any):
        """
        Initialize OpenAI provider.

        Args:
            config: OpenAI configuration
            **kwargs: Additional config parameters
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install 'craft-chatbot[openai]'"
            )

        if config is None:
            config = OpenAIConfig(**kwargs)
        elif kwargs:
            config = OpenAIConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        client_kwargs = {"api_key": self.config.api_key}
        if self.config.base_url:
            client_kwargs["base_url"] = self.config.base_url

        self.client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)

    def _validate_config(self) -> None:
        """Validate OpenAI configuration."""
        if not self.config.api_key:
            raise ValueError(
                "OpenAI API key not provided. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

    def _chat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List["Tool"]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Internal chat request to OpenAI.
        """
        formatted_messages = self.format_messages(messages)

        params = {
            "model": self.config.model,
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "stream": stream,
        }

        # Handle tools
        if tools:
            params["tools"] = [t.to_function_schema() for t in tools]
            params["tool_choice"] = self._format_tool_choice(tool_choice)

        if self.config.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)

        if stream:
            return self._stream(params)
        else:
            return self._complete(params)

    def _complete(self, params: Dict[str, Any]) -> ChatResponse:
        """Complete (non-streaming) request."""
        response = self.client.chat.completions.create(**params)

        choice = response.choices[0]
        usage = response.usage

        return ChatResponse(
            content=choice.message.content or "",
            role=Role.ASSISTANT,
            model=response.model,
            usage={
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
            metadata={
                "id": response.id,
                "finish_reason": choice.finish_reason,
            },
        )

    def _stream(self, params: Dict[str, Any]) -> AsyncIterator[StreamChunk]:
        """Streaming request."""
        stream = self.client.chat.completions.create(**params)

        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield StreamChunk(content=delta.content)

                # Check if streaming finished
                if chunk.choices[0].finish_reason:
                    yield StreamChunk(content="", finished=True)

    async def _achat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List["Tool"]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Internal async chat request to OpenAI.
        """
        formatted_messages = self.format_messages(messages)

        params = {
            "model": self.config.model,
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "stream": stream,
        }

        # Handle tools
        if tools:
            params["tools"] = [t.to_function_schema() for t in tools]
            params["tool_choice"] = self._format_tool_choice(tool_choice)

        if self.config.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)

        if stream:
            return self._astream(params)
        else:
            return await self._acomplete(params)

    async def _acomplete(self, params: Dict[str, Any]) -> ChatResponse:
        """Async complete (non-streaming) request."""
        response = await self.async_client.chat.completions.create(**params)

        choice = response.choices[0]
        usage = response.usage

        return ChatResponse(
            content=choice.message.content or "",
            role=Role.ASSISTANT,
            model=response.model,
            usage={
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
            metadata={
                "id": response.id,
                "finish_reason": choice.finish_reason,
            },
        )

    async def _astream(self, params: Dict[str, Any]) -> AsyncIterator[StreamChunk]:
        """Async streaming request."""
        stream = await self.async_client.chat.completions.create(**params)

        async for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield StreamChunk(content=delta.content)

                # Check if streaming finished
                if chunk.choices[0].finish_reason:
                    yield StreamChunk(content="", finished=True)
