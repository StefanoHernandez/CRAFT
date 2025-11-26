"""OpenRouter provider - Access 400+ AI models through a unified API."""

import os
from typing import Any, List, Optional, AsyncIterator, Union
import logging

try:
    from openai import OpenAI, AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None
    AsyncOpenAI = None

from pydantic import Field, ConfigDict
from craft.providers.base import Provider, ProviderConfig, ChatResponse, StreamChunk, Role

logger = logging.getLogger(__name__)


class OpenRouterConfig(ProviderConfig):
    """OpenRouter-specific configuration."""
    
    model: str = Field(default="google/gemini-2.0-flash-exp:free")
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY"))
    base_url: str = "https://openrouter.ai/api/v1"
    site_url: Optional[str] = None  # For rankings
    app_name: Optional[str] = None  # For rankings
    
    model_config = ConfigDict(extra="allow")


class OpenRouterProvider(Provider):
    """
    OpenRouter provider - Access 400+ AI models through one API.
    
    OpenRouter aggregates models from OpenAI, Anthropic, Google, Meta,
    Mistral, DeepSeek, xAI and many more.
    
    Popular models:
    - google/gemini-2.0-flash-exp:free (FREE!)
    - anthropic/claude-3.5-sonnet
    - openai/gpt-4o
    - x-ai/grok-4.1
    - mistralai/mistral-large
    - meta-llama/llama-3.3-70b-instruct
    
    Example:
        from craft.providers import OpenRouterProvider
        
        provider = OpenRouterProvider(
            model="google/gemini-2.0-flash-exp:free"
        )
        
        response = provider.chat([
            {"role": "user", "content": "Hello!"}
        ])
    """
    
    def __init__(
        self,
        model: str = "google/gemini-2.0-flash-exp:free",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize OpenRouter provider.
        
        Args:
            model: Model identifier (e.g., "google/gemini-2.0-flash-exp:free")
            api_key: OpenRouter API key
            **kwargs: Additional config parameters
        """
        if not HAS_OPENAI:
            raise ImportError(
                "openai package required for OpenRouter. "
                "Install with: pip install openai"
            )
        
        config = OpenRouterConfig(
            model=model,
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
            **kwargs
        )
        super().__init__(config)
        
        # Initialize OpenAI client with OpenRouter base URL
        extra_headers = {}
        if self.config.site_url:
            extra_headers["HTTP-Referer"] = self.config.site_url
        if self.config.app_name:
            extra_headers["X-Title"] = self.config.app_name
            
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            default_headers=extra_headers
        )
        self.async_client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            default_headers=extra_headers
        )
    
    def _validate_config(self) -> None:
        """Validate OpenRouter configuration."""
        if not self.config.api_key:
            raise ValueError(
                "OpenRouter API key required. "
                "Set OPENROUTER_API_KEY or pass api_key parameter."
            )
    
    def chat(self, messages: List[Any], **kwargs) -> ChatResponse:
        """Generate chat completion via OpenRouter."""
        # Convert messages to dicts if needed
        formatted_messages = self._format_messages(messages)
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=formatted_messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens"),
            **kwargs
        )
        
        return ChatResponse(
            content=response.choices[0].message.content,
            role=Role.ASSISTANT,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        )
    
    async def achat(self, messages: List[Any], **kwargs) -> ChatResponse:
        """Async chat completion via OpenRouter."""
        formatted_messages = self._format_messages(messages)
        
        response = await self.async_client.chat.completions.create(
            model=self.config.model,
            messages=formatted_messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens"),
            **kwargs
        )
        
        return ChatResponse(
            content=response.choices[0].message.content,
            role=Role.ASSISTANT,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        )
    
    def _format_messages(self, messages: List[Any]) -> List[dict]:
        """Format messages to OpenRouter API format."""
        formatted = []
        for msg in messages:
            if hasattr(msg, "model_dump"):
                dump = msg.model_dump()
                if hasattr(dump.get("role"), "value"):
                    dump["role"] = dump["role"].value
                formatted.append(dump)
            elif isinstance(msg, dict):
                formatted.append(msg)
            else:
                formatted.append({
                    "role": getattr(msg, "role", "user"),
                    "content": getattr(msg, "content", "")
                })
        return formatted
