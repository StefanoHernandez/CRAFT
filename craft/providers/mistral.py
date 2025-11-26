"""Mistral AI provider for their API.

Mistral AI provides powerful open-weight models via API.
Includes Mistral Large, Mixtral MoE, and specialized models.
"""

from typing import List, Dict, Any, Optional, Iterator
import logging

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None

from craft.providers.base import Provider, ProviderConfig, ChatResponse, Role


logger = logging.getLogger(__name__)


class MistralConfig(ProviderConfig):
    """Configuration for Mistral AI provider."""
    
    api_key: str
    model: str = "mistral-large-latest"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    
    class Config:
        extra = "allow"


class MistralProvider(Provider):
    """
    Mistral AI provider.
    
    Mistral AI offers powerful open-weight models via API:
    - State-of-the-art performance
    - Competitive pricing
    - European company (GDPR compliant)
    
    Supported models:
    - mistral-large-latest (Best, 128k context)
    - mistral-medium-latest (Balanced)
    - mistral-small-latest (Fast)
    - codestral-latest (Code specialist, 32k context)
    - open-mixtral-8x7b (Open-source MoE)
    - open-mixtral-8x22b (Larger MoE)
    - open-mistral-7b (Fastest open model)
    
    Example:
        from craft.providers import MistralProvider
        
        provider = MistralProvider(
            api_key="your-mistral-api-key",
            model="mistral-large-latest"
        )
        
        response = provider.chat([
            {"role": "user", "content": "Hello!"}
        ])
        print(response.content)
    
    Get API key: https://console.mistral.ai/
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "mistral-large-latest",
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Initialize Mistral provider.
        
        Args:
            api_key: Mistral API key
            model: Model name
            temperature: Sampling temperature
            **kwargs: Additional parameters
        """
        if not HAS_OPENAI:
            raise ImportError(
                "openai package is required for Mistral provider. "
                "Install it with: pip install openai"
            )
        
        config = MistralConfig(
            api_key=api_key,
            model=model,
            temperature=temperature,
            **kwargs
        )
        super().__init__(config)
        
        # Mistral API is OpenAI-compatible
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.mistral.ai/v1"
        )
        
        self.model = model
        logger.info(f"Initialized Mistral provider with model: {model}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate chat completion."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                top_p=self.config.top_p,
                **kwargs
            )
            
            message = response.choices[0].message
            
            return ChatResponse(
                content=message.content or "",
                role=Role(message.role),
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "id": response.id,
                }
            )
        
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            raise RuntimeError(f"Mistral chat failed: {e}")
    
    def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[ChatResponse]:
        """Stream chat completion."""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                top_p=self.config.top_p,
                stream=True,
                **kwargs
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield ChatResponse(
                        content=chunk.choices[0].delta.content,
                        role=Role.ASSISTANT,
                        model=self.model
                    )
        
        except Exception as e:
            logger.error(f"Mistral streaming error: {e}")
            raise RuntimeError(f"Mistral streaming failed: {e}")
    
    async def achat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Async chat completion."""
        return self.chat(messages, temperature, max_tokens, **kwargs)


if __name__ == "__main__":
    import os
    
    print("=" * 60)
    print("🇫🇷 Mistral AI Provider Example")
    print("=" * 60)
    print("\n💡 Get your API key: https://console.mistral.ai/\n")
    
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        print("❌ MISTRAL_API_KEY environment variable not set")
    else:
        try:
            provider = MistralProvider(
                api_key=api_key,
                model="mistral-small-latest"
            )
            
            response = provider.chat([
                {"role": "user", "content": "Say hello in French"}
            ])
            print(f"✅ Response: {response.content}\n")
        
        except Exception as e:
            print(f"❌ Error: {e}")
