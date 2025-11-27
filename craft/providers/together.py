
import os
from typing import Any, Dict, List, Optional, AsyncIterator, Union

try:
    import together
except ImportError:
    together = None

from craft.providers.base import Provider, ProviderConfig, ChatResponse, StreamChunk, Role
from craft.core.conversation import Message

class TogetherAIProvider(Provider):
    """
    Provider for Together AI API.
    
    Requires `together` package: `pip install together`
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "meta-llama/Llama-3-8b-chat-hf",
        **kwargs
    ):
        """
        Initialize Together AI provider.
        
        Args:
            api_key: Together AI API key (or set TOGETHER_API_KEY env var)
            model: Model ID
        """
        if together is None:
            raise ImportError(
                "TogetherAIProvider requires 'together'. "
                "Install it with: pip install together"
            )
            
        api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not api_key:
            raise ValueError("Together AI API key is required")
            
        config = ProviderConfig(api_key=api_key, model=model, **kwargs)
        super().__init__(config)
        
        self.client = together.Together(api_key=self.config.api_key)

    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.config.api_key:
            raise ValueError("Together AI API key is required")

    def _chat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List[Any]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Send a chat request to Together AI.
        """
        # Convert messages
        formatted_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
        
        params = {
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 1024),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }
        
        if stream:
            return self._stream_chat(formatted_messages, **params)
            
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=formatted_messages,
                stream=False,
                **params
            )
            
            content = response.choices[0].message.content
            
            return ChatResponse(
                role=Role.ASSISTANT,
                content=content,
                model=self.config.model,
                raw_response=response
            )
            
        except Exception as e:
            raise e

    def _stream_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat response."""
        try:
            stream = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                stream=True,
                **kwargs
            )
            
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield StreamChunk(
                        content=delta,
                        metadata={"raw": chunk}
                    )
                    
        except Exception as e:
            raise e

    async def _achat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List[Any]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """Async chat implementation."""
        raise NotImplementedError("Async chat not implemented for TogetherAIProvider yet")
