
import os
from typing import Any, Dict, List, Optional, AsyncIterator, Union

try:
    import replicate
except ImportError:
    replicate = None

from craft.providers.base import Provider, ProviderConfig, ChatResponse, StreamChunk, Role
from craft.core.conversation import Message

class ReplicateProvider(Provider):
    """
    Provider for Replicate API.
    
    Requires `replicate` package: `pip install replicate`
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "meta/meta-llama-3-8b-instruct",
        **kwargs
    ):
        """
        Initialize Replicate provider.
        
        Args:
            api_key: Replicate API token (or set REPLICATE_API_TOKEN env var)
            model: Model ID (e.g., "owner/model-name" or "owner/model-name:version")
        """
        if replicate is None:
            raise ImportError(
                "ReplicateProvider requires 'replicate'. "
                "Install it with: pip install replicate"
            )
            
        api_key = api_key or os.getenv("REPLICATE_API_TOKEN")
        if not api_key:
            raise ValueError("Replicate API token is required")
            
        config = ProviderConfig(api_key=api_key, model=model, **kwargs)
        super().__init__(config)
        
        self.client = replicate.Client(api_token=self.config.api_key)

    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.config.api_key:
            raise ValueError("Replicate API token is required")

    def _chat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List[Any]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Send a chat request to Replicate model.
        """
        system_prompt = next((m.content for m in messages if m.role == Role.SYSTEM), "")
        user_prompt = "\n".join(f"{m.role.value}: {m.content}" for m in messages if m.role != Role.SYSTEM)
        
        input_data = {
            "prompt": user_prompt,
            "system_prompt": system_prompt,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 1024),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }
        
        if stream:
            return self._stream_chat(input_data, **kwargs)
            
        try:
            # Replicate run usually returns an iterator
            output = self.client.run(self.config.model, input=input_data)
            
            # Join all chunks for non-streaming
            full_response = "".join(list(output))
            
            return ChatResponse(
                role=Role.ASSISTANT,
                content=full_response,
                model=self.config.model,
                raw_response=output
            )
            
        except Exception as e:
            raise e

    def _stream_chat(
        self,
        input_data: Dict[str, Any],
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat response."""
        try:
            stream = self.client.stream(self.config.model, input=input_data)
            
            for event in stream:
                # event is usually a string chunk
                if event:
                    yield StreamChunk(
                        content=str(event),
                        metadata={"raw": event}
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
        raise NotImplementedError("Async chat not implemented for ReplicateProvider yet")
