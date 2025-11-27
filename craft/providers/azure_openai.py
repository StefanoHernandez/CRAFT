"""Azure OpenAI provider implementation."""

import os
from typing import Any, AsyncIterator, Dict, List, Optional, Union

try:
    from openai import AzureOpenAI, AsyncAzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False

from pydantic import Field
from craft.providers.base import (
    Provider,
    ProviderConfig,
    Message,
    ChatResponse,
    StreamChunk,
    Role,
)


class AzureOpenAIConfig(ProviderConfig):
    """Azure OpenAI-specific configuration."""

    model: str = Field(default="gpt-4o")  # Azure deployment name
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_KEY"))
    azure_endpoint: Optional[str] = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT"))
    api_version: str = Field(default="2024-02-15-preview")
    max_tokens: Optional[int] = Field(default=None)
    # Azure AD authentication (alternative to API key)
    azure_ad_token: Optional[str] = Field(default=None)
    azure_ad_token_provider: Optional[Any] = Field(default=None)


class AzureOpenAIProvider(Provider):
    """
    Azure OpenAI provider implementation.

    Supports GPT-4, GPT-3.5, and custom deployments on Azure OpenAI Service.

    Key differences from OpenAI:
    - Uses Azure endpoints (https://<resource>.openai.azure.com/)
    - Requires API version
    - Uses deployment names instead of model names
    - Supports Azure AD authentication

    Example:
        >>> from craft.providers import AzureOpenAIProvider, Message, Role
        >>>
        >>> config = AzureOpenAIConfig(
        ...     model="gpt-4-deployment",  # Your Azure deployment name
        ...     azure_endpoint="https://myresource.openai.azure.com/",
        ...     api_key="your-api-key"
        ... )
        >>> provider = AzureOpenAIProvider(config)
        >>>
        >>> response = provider.chat([
        ...     Message(role=Role.USER, content="Hello!")
        ... ])
        >>> print(response.content)
    """

    def __init__(self, config: Optional[AzureOpenAIConfig] = None, **kwargs: Any):
        """
        Initialize Azure OpenAI provider.

        Args:
            config: Azure OpenAI configuration
            **kwargs: Additional config parameters

        Environment Variables:
            AZURE_OPENAI_API_KEY: Azure OpenAI API key
            AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
        """
        if not AZURE_OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install 'craft-chatbot[openai]'"
            )

        if config is None:
            config = AzureOpenAIConfig(**kwargs)
        elif kwargs:
            config = AzureOpenAIConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        # Build client kwargs
        client_kwargs = {
            "api_version": self.config.api_version,
            "azure_endpoint": self.config.azure_endpoint,
        }

        # Authentication: API key or Azure AD
        if self.config.api_key:
            client_kwargs["api_key"] = self.config.api_key
        elif self.config.azure_ad_token:
            client_kwargs["azure_ad_token"] = self.config.azure_ad_token
        elif self.config.azure_ad_token_provider:
            client_kwargs["azure_ad_token_provider"] = self.config.azure_ad_token_provider

        self.client = AzureOpenAI(**client_kwargs)
        self.async_client = AsyncAzureOpenAI(**client_kwargs)

    def _validate_config(self) -> None:
        """Validate Azure OpenAI configuration."""
        if not self.config.azure_endpoint:
            raise ValueError(
                "Azure OpenAI endpoint not provided. "
                "Set AZURE_OPENAI_ENDPOINT environment variable or pass azure_endpoint parameter. "
                "Example: https://myresource.openai.azure.com/"
            )

        # Must have at least one authentication method
        if not any([
            self.config.api_key,
            self.config.azure_ad_token,
            self.config.azure_ad_token_provider
        ]):
            raise ValueError(
                "Azure OpenAI authentication not provided. "
                "Set AZURE_OPENAI_API_KEY environment variable, pass api_key parameter, "
                "or configure Azure AD authentication."
            )

    def chat(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Send chat request to Azure OpenAI.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            **kwargs: Additional Azure OpenAI-specific parameters
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature (0.0-2.0)
                - top_p: Nucleus sampling parameter (0.0-1.0)
                - frequency_penalty: Frequency penalty (-2.0 to 2.0)
                - presence_penalty: Presence penalty (-2.0 to 2.0)
                - stop: Stop sequences

        Returns:
            ChatResponse or iterator of StreamChunk if streaming
        """
        formatted_messages = self.format_messages(messages)

        params = {
            "model": self.config.model,  # Azure deployment name
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "stream": stream,
        }

        # Optional parameters
        if self.config.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)

        for param in ["frequency_penalty", "presence_penalty", "stop"]:
            if param in kwargs:
                params[param] = kwargs[param]

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
                "provider": "azure_openai",
                "deployment": params["model"],
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

    async def achat(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Async chat request to Azure OpenAI.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            **kwargs: Additional Azure OpenAI-specific parameters

        Returns:
            ChatResponse or async iterator of StreamChunk if streaming
        """
        formatted_messages = self.format_messages(messages)

        params = {
            "model": self.config.model,  # Azure deployment name
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "stream": stream,
        }

        # Optional parameters
        if self.config.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)

        for param in ["frequency_penalty", "presence_penalty", "stop"]:
            if param in kwargs:
                params[param] = kwargs[param]

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
                "provider": "azure_openai",
                "deployment": params["model"],
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


__all__ = ["AzureOpenAIProvider", "AzureOpenAIConfig", "AZURE_OPENAI_AVAILABLE"]
