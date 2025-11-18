"""Cohere provider implementation."""

import os
from typing import Any, AsyncIterator, Dict, List, Optional, Union

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

from pydantic import Field
from craft.providers.base import (
    Provider,
    ProviderConfig,
    Message,
    ChatResponse,
    StreamChunk,
    Role,
)


class CohereConfig(ProviderConfig):
    """Cohere-specific configuration."""

    model: str = Field(default="command")
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("COHERE_API_KEY"))
    max_tokens: Optional[int] = Field(default=None)


class CohereProvider(Provider):
    """
    Cohere provider implementation.

    Supports Command, Command Light, and other Cohere models.

    Available models:
    - command: Most capable model for complex tasks
    - command-light: Faster, lighter model for simple tasks
    - command-nightly: Latest experimental features
    - command-r: Retrieval-augmented generation optimized
    - command-r-plus: Enhanced RAG with larger context

    Example:
        >>> from craft.providers import CohereProvider, Message, Role
        >>>
        >>> config = CohereConfig(
        ...     model="command",
        ...     api_key="your-api-key"
        ... )
        >>> provider = CohereProvider(config)
        >>>
        >>> response = provider.chat([
        ...     Message(role=Role.USER, content="Hello!")
        ... ])
        >>> print(response.content)
    """

    def __init__(self, config: Optional[CohereConfig] = None, **kwargs: Any):
        """
        Initialize Cohere provider.

        Args:
            config: Cohere configuration
            **kwargs: Additional config parameters

        Environment Variables:
            COHERE_API_KEY: Cohere API key
        """
        if not COHERE_AVAILABLE:
            raise ImportError(
                "cohere package not installed. "
                "Install with: pip install 'craft-chatbot[cohere]'"
            )

        if config is None:
            config = CohereConfig(**kwargs)
        elif kwargs:
            config = CohereConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        self.client = cohere.Client(api_key=self.config.api_key)
        # Cohere v5+ has AsyncClient
        try:
            self.async_client = cohere.AsyncClient(api_key=self.config.api_key)
        except AttributeError:
            self.async_client = None

    def _validate_config(self) -> None:
        """Validate Cohere configuration."""
        if not self.config.api_key:
            raise ValueError(
                "Cohere API key not provided. "
                "Set COHERE_API_KEY environment variable or pass api_key parameter."
            )

    def chat(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Send chat request to Cohere.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            **kwargs: Additional Cohere-specific parameters
                - preamble: System message override
                - conversation_id: Track conversations
                - search_queries_only: Return only search queries
                - documents: Add documents for RAG
                - connectors: Use Cohere connectors

        Returns:
            ChatResponse or iterator of StreamChunk if streaming
        """
        # Cohere uses different format: message + chat_history
        message, chat_history, preamble = self._format_cohere_messages(messages)

        params = {
            "model": self.config.model,
            "message": message,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "p": kwargs.get("top_p", self.config.top_p),  # Cohere uses 'p' not 'top_p'
        }

        if chat_history:
            params["chat_history"] = chat_history

        if preamble or kwargs.get("preamble"):
            params["preamble"] = kwargs.get("preamble", preamble)

        if self.config.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)

        # Optional Cohere-specific parameters
        for param in ["conversation_id", "search_queries_only", "documents", "connectors"]:
            if param in kwargs:
                params[param] = kwargs[param]

        params["stream"] = stream

        if stream:
            return self._stream(params)
        else:
            return self._complete(params)

    def _format_cohere_messages(
        self, messages: List[Message]
    ) -> tuple[str, List[Dict[str, str]], Optional[str]]:
        """
        Format messages for Cohere API.

        Cohere expects:
        - message: The current user message
        - chat_history: Previous messages
        - preamble: System message (optional)
        """
        preamble = None
        chat_history = []
        current_message = ""

        for i, msg in enumerate(messages):
            if msg.role == Role.SYSTEM:
                preamble = msg.content
            elif i == len(messages) - 1:
                # Last message is the current message
                current_message = msg.content
            else:
                # Previous messages go to chat_history
                chat_history.append({
                    "role": "USER" if msg.role == Role.USER else "CHATBOT",
                    "message": msg.content
                })

        return current_message, chat_history, preamble

    def _complete(self, params: Dict[str, Any]) -> ChatResponse:
        """Complete (non-streaming) request."""
        response = self.client.chat(**params)

        return ChatResponse(
            content=response.text,
            role=Role.ASSISTANT,
            model=self.config.model,
            usage={
                "prompt_tokens": response.meta.tokens.input_tokens if hasattr(response, "meta") else 0,
                "completion_tokens": response.meta.tokens.output_tokens if hasattr(response, "meta") else 0,
                "total_tokens": (
                    (response.meta.tokens.input_tokens + response.meta.tokens.output_tokens)
                    if hasattr(response, "meta") else 0
                ),
            },
            metadata={
                "generation_id": response.generation_id if hasattr(response, "generation_id") else None,
                "provider": "cohere",
                "citations": response.citations if hasattr(response, "citations") else None,
                "documents": response.documents if hasattr(response, "documents") else None,
            },
        )

    def _stream(self, params: Dict[str, Any]) -> AsyncIterator[StreamChunk]:
        """Streaming request."""
        stream = self.client.chat_stream(**params)

        for event in stream:
            if event.event_type == "text-generation":
                yield StreamChunk(content=event.text)
            elif event.event_type == "stream-end":
                yield StreamChunk(content="", finished=True)

    async def achat(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Async chat request to Cohere.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            **kwargs: Additional Cohere-specific parameters

        Returns:
            ChatResponse or async iterator of StreamChunk if streaming
        """
        if not self.async_client:
            # Fallback to sync if async not available
            return self.chat(messages, stream, **kwargs)

        message, chat_history, preamble = self._format_cohere_messages(messages)

        params = {
            "model": self.config.model,
            "message": message,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "p": kwargs.get("top_p", self.config.top_p),
        }

        if chat_history:
            params["chat_history"] = chat_history

        if preamble or kwargs.get("preamble"):
            params["preamble"] = kwargs.get("preamble", preamble)

        if self.config.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)

        for param in ["conversation_id", "search_queries_only", "documents", "connectors"]:
            if param in kwargs:
                params[param] = kwargs[param]

        params["stream"] = stream

        if stream:
            return self._astream(params)
        else:
            return await self._acomplete(params)

    async def _acomplete(self, params: Dict[str, Any]) -> ChatResponse:
        """Async complete (non-streaming) request."""
        response = await self.async_client.chat(**params)

        return ChatResponse(
            content=response.text,
            role=Role.ASSISTANT,
            model=self.config.model,
            usage={
                "prompt_tokens": response.meta.tokens.input_tokens if hasattr(response, "meta") else 0,
                "completion_tokens": response.meta.tokens.output_tokens if hasattr(response, "meta") else 0,
                "total_tokens": (
                    (response.meta.tokens.input_tokens + response.meta.tokens.output_tokens)
                    if hasattr(response, "meta") else 0
                ),
            },
            metadata={
                "generation_id": response.generation_id if hasattr(response, "generation_id") else None,
                "provider": "cohere",
                "citations": response.citations if hasattr(response, "citations") else None,
                "documents": response.documents if hasattr(response, "documents") else None,
            },
        )

    async def _astream(self, params: Dict[str, Any]) -> AsyncIterator[StreamChunk]:
        """Async streaming request."""
        stream = await self.async_client.chat_stream(**params)

        async for event in stream:
            if event.event_type == "text-generation":
                yield StreamChunk(content=event.text)
            elif event.event_type == "stream-end":
                yield StreamChunk(content="", finished=True)


__all__ = ["CohereProvider", "CohereConfig", "COHERE_AVAILABLE"]
