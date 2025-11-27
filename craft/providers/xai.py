"""xAI Grok provider implementation."""

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


class xAIConfig(ProviderConfig):
    """xAI (Grok) specific configuration."""
    
    model: str = Field(default="grok-2-1212")
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("XAI_API_KEY"))
    base_url: str = "https://api.x.ai/v1"
    
    model_config = ConfigDict(extra="allow")


class xAIProvider(Provider):
    """
    xAI Grok provider implementation.
    
    Access to Elon Musk's Grok models with real-time X (Twitter) data.
    
    Supported models:
    - grok-2-1212 (Latest, December 2024)
    - grok-2-vision-1212 (Vision support)
    - grok-beta
    
    Example:
        from craft.providers import xAIProvider
        
        provider = xAIProvider(model="grok-2-1212")
        
        response = provider.chat([
            {"role": "user", "content": "What's trending on X today?"}
        ])
    """
    
    def __init__(
        self,
        model: str = "grok-2-1212",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize xAI provider.
        
        Args:
            model: Grok model name
            api_key: xAI API key
            **kwargs: Additional config
        """
        if not HAS_OPENAI:
            raise ImportError(
                "openai package required for xAI. "
                "Install with: pip install openai"
            )
        
        config = xAIConfig(
            model=model,
            api_key=api_key or os.getenv("XAI_API_KEY"),
            **kwargs
        )
        super().__init__(config)
        
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        self.async_client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
    
    def _validate_config(self) -> None:
        """Validate xAI configuration."""
        if not self.config.api_key:
            raise ValueError(
                "xAI API key required. "
                "Set XAI_API_KEY or pass api_key parameter."
            )
    
    def _chat(self, messages: List[Any], **kwargs) -> ChatResponse:
        """Internal chat completion via xAI."""
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
    
    async def _achat(self, messages: List[Any], **kwargs) -> ChatResponse:
        """Internal async chat completion via xAI."""
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
        """Format messages to xAI API format."""
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
