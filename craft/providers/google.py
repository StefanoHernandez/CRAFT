"""Google (Gemini) provider implementation."""

import os
from typing import Any, AsyncIterator, Dict, List, Optional, Union

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from pydantic import Field
from craft.providers.base import (
    Provider,
    ProviderConfig,
    Message,
    ChatResponse,
    StreamChunk,
    Role,
)


class GoogleConfig(ProviderConfig):
    """Google (Gemini) specific configuration."""

    model: str = Field(default="gemini-1.5-pro")
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))
    max_tokens: Optional[int] = Field(default=8192)


class GoogleProvider(Provider):
    """
    Google (Gemini) provider implementation.

    Supports Gemini Pro and other Google models with streaming.
    """

    def __init__(self, config: Optional[GoogleConfig] = None, **kwargs: Any):
        """
        Initialize Google provider.

        Args:
            config: Google configuration
            **kwargs: Additional config parameters
        """
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install 'craft-chatbot[google]'"
            )

        if config is None:
            config = GoogleConfig(**kwargs)
        elif kwargs:
            config = GoogleConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        genai.configure(api_key=self.config.api_key)
        self.model = genai.GenerativeModel(self.config.model)

    def _validate_config(self) -> None:
        """Validate Google configuration."""
        if not self.config.api_key:
            raise ValueError(
                "Google API key not provided. "
                "Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

    def format_messages(self, messages: List[Message]) -> tuple[Optional[str], List[Dict[str, str]]]:
        """
        Format messages for Google API.

        Google uses a different format where system messages are handled separately.

        Returns:
            Tuple of (system_instruction, formatted_messages)
        """
        system_instruction = None
        formatted_messages = []

        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_instruction = msg.content
            else:
                # Google uses "user" and "model" instead of "assistant"
                role = "model" if msg.role == Role.ASSISTANT else "user"
                formatted_messages.append({
                    "role": role,
                    "parts": [msg.content],
                })

        return system_instruction, formatted_messages

    def chat(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Send chat request to Google.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            **kwargs: Additional Google-specific parameters

        Returns:
            ChatResponse or iterator of StreamChunk if streaming
        """
        system_instruction, formatted_messages = self.format_messages(messages)

        # Recreate model with system instruction if provided
        if system_instruction:
            model = genai.GenerativeModel(
                self.config.model,
                system_instruction=system_instruction
            )
        else:
            model = self.model

        # Build generation config
        generation_config = {
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        if self.config.max_tokens:
            generation_config["max_output_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)

        # Start chat session
        chat = model.start_chat(history=formatted_messages[:-1] if len(formatted_messages) > 1 else [])

        # Get last message
        last_message = formatted_messages[-1]["parts"][0] if formatted_messages else ""

        if stream:
            return self._stream(chat, last_message, generation_config)
        else:
            return self._complete(chat, last_message, generation_config)

    def _complete(
        self,
        chat: Any,
        message: str,
        generation_config: Dict[str, Any]
    ) -> ChatResponse:
        """Complete (non-streaming) request."""
        response = chat.send_message(message, generation_config=generation_config)

        # Extract usage metadata if available
        usage = {}
        if hasattr(response, "usage_metadata"):
            usage = {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
            }

        return ChatResponse(
            content=response.text,
            role=Role.ASSISTANT,
            model=self.config.model,
            usage=usage if usage else None,
            metadata={
                "finish_reason": getattr(response.candidates[0] if response.candidates else None, "finish_reason", None),
            },
        )

    def _stream(
        self,
        chat: Any,
        message: str,
        generation_config: Dict[str, Any]
    ) -> AsyncIterator[StreamChunk]:
        """Streaming request."""
        response = chat.send_message(
            message,
            generation_config=generation_config,
            stream=True
        )

        for chunk in response:
            if chunk.text:
                yield StreamChunk(content=chunk.text)

        # Signal end of stream
        yield StreamChunk(content="", finished=True)

    async def achat(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Async chat request to Google.

        Note: Google's SDK doesn't have native async support,
        so we use the sync methods. For true async, consider using httpx directly.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            **kwargs: Additional Google-specific parameters

        Returns:
            ChatResponse or async iterator of StreamChunk if streaming
        """
        # For now, delegate to sync implementation
        # In production, you might want to use asyncio.to_thread or implement native async
        return self.chat(messages, stream, **kwargs)

    async def _acomplete(self, chat: Any, message: str, generation_config: Dict[str, Any]) -> ChatResponse:
        """Async complete - delegates to sync for now."""
        return self._complete(chat, message, generation_config)

    async def _astream(
        self,
        chat: Any,
        message: str,
        generation_config: Dict[str, Any]
    ) -> AsyncIterator[StreamChunk]:
        """Async streaming - delegates to sync for now."""
        for chunk in self._stream(chat, message, generation_config):
            yield chunk
