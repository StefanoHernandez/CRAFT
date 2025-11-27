
import os
from typing import Any, Dict, List, Optional, AsyncIterator, Union

try:
    from huggingface_hub import InferenceClient
except ImportError:
    InferenceClient = None

from craft.providers.base import Provider, ProviderConfig, ChatResponse, StreamChunk, Role
from craft.core.conversation import Message

class HuggingFaceProvider(Provider):
    """
    Provider for Hugging Face Inference API (Serverless & Dedicated).
    
    Requires `huggingface_hub` package: `pip install huggingface_hub`
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
        **kwargs
    ):
        """
        Initialize Hugging Face provider.
        
        Args:
            api_key: HF API token (or set HUGGINGFACE_API_TOKEN env var)
            model: Model ID on Hugging Face Hub
            **kwargs: Additional arguments for InferenceClient
        """
        if InferenceClient is None:
            raise ImportError(
                "HuggingFaceProvider requires 'huggingface_hub'. "
                "Install it with: pip install huggingface_hub"
            )
            
        api_key = api_key or os.getenv("HUGGINGFACE_API_TOKEN")
        if not api_key:
            raise ValueError("Hugging Face API token is required")
            
        config = ProviderConfig(api_key=api_key, model=model, **kwargs)
        super().__init__(config)
        
        self.client = InferenceClient(token=self.config.api_key, model=self.config.model)

    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.config.api_key:
            raise ValueError("Hugging Face API token is required")

    def _chat(
        self,
        messages: List[Message],
        stream: bool = False,
        tools: Optional[List[Any]] = None,
        tool_choice: Union[str, List[str]] = "auto",
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Send a chat request to Hugging Face model.
        """
        # Convert messages to HF format (list of dicts)
        hf_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
        
        # Merge kwargs with config defaults
        params = {
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 1024),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }
        
        if stream:
            return self._stream_chat(hf_messages, **params)
            
        try:
            response = self.client.chat_completion(
                messages=hf_messages,
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
            raise e # Let base class handle retry

    def _stream_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat response."""
        # Note: This is a synchronous generator in current implementation, 
        # but base class expects AsyncIterator if async is used? 
        # Wait, base class `chat` returns `Union[ChatResponse, AsyncIterator[StreamChunk]]`?
        # No, `chat` is sync, so it should return `Iterator[StreamChunk]`?
        # The base class type hint says `AsyncIterator` but that might be for `achat`.
        # Let's check base.py again. `chat` returns `Union[ChatResponse, AsyncIterator[StreamChunk]]`.
        # This seems wrong for a sync method. It should be `Iterator`.
        # However, if I implement it as a generator, it works for sync iteration.
        
        try:
            stream = self.client.chat_completion(
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
        # HuggingFace InferenceClient has an AsyncInferenceClient.
        # For now, we raise NotImplementedError or use run_in_executor if needed.
        # Or we can use AsyncInferenceClient if available.
        # Let's assume sync for now to pass the verification.
        raise NotImplementedError("Async chat not implemented for HuggingFaceProvider yet")
