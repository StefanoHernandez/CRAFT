"""Groq provider for ultra-fast LLM inference.

Groq provides the fastest LLM inference with their LPU (Language Processing Unit).
Perfect for real-time applications requiring low latency.

API is OpenAI-compatible, making integration simple.
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
from pydantic import ConfigDict


logger = logging.getLogger(__name__)


class GroqConfig(ProviderConfig):
    """Configuration for Groq provider."""
    
    api_key: str
    model: str = "llama-3.1-70b-versatile"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    
    model_config = ConfigDict(extra="allow")


class GroqProvider(Provider):
    """
    Groq provider for ultra-fast LLM inference.
    
    Groq's LPU technology provides the fastest LLM inference available,
    with 70+ tokens/second for Llama 3 70B models.
    
    Perfect for:
    - Real-time chat applications
    - Low-latency AI assistants
    - High-throughput use cases
    - Production deployments requiring speed
    
    Supported models:
    - llama-3.1-405b-reasoning (Most capable)
    - llama-3.1-70b-versatile (Balanced)
    - llama-3.1-8b-instant (Fastest)
    - llama3-70b-8192 (Legacy)
    - llama3-8b-8192 (Legacy)
    - mixtral-8x7b-32768 (Mixtral MoE)
    - gemma2-9b-it (Google Gemma 2)
    - gemma-7b-it (Google Gemma)
    
    Example:
        from craft.providers import GroqProvider
        
        # Create provider
        provider = GroqProvider(
            api_key="your-groq-api-key",
            model="llama-3.1-70b-versatile"
        )
        
        # Chat completion
        response = provider.chat([
            {"role": "user", "content": "Hello!"}
        ])
        print(response.content)
        
        # Streaming (ultra-fast!)
        for chunk in provider.stream([
            {"role": "user", "content": "Tell me a story"}
        ]):
            print(chunk.content, end='', flush=True)
    
    Get API key: https://console.groq.com/keys
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Initialize Groq provider.
        
        Args:
            api_key: Groq API key
            model: Model name (e.g., "llama-3.1-70b-versatile")
            temperature: Sampling temperature (0-2)
            **kwargs: Additional Groq parameters
        """
        if not HAS_OPENAI:
            raise ImportError(
                "openai package is required for Groq provider. "
                "Install it with: pip install openai"
            )
        
        config = GroqConfig(
            api_key=api_key,
            model=model,
            temperature=temperature,
            **kwargs
        )
        super().__init__(config)
        
        # Initialize Groq client (uses OpenAI SDK)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        self.model = model
        logger.info(f"Initialized Groq provider with model: {model}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Max tokens to generate
            **kwargs: Additional Groq options
        
        Returns:
            ChatResponse with generated text
        """
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
                    "created": response.created,
                }
            )
        
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise RuntimeError(f"Groq chat failed: {e}")
    
    def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[ChatResponse]:
        """
        Stream chat completion (ultra-fast with Groq LPU!).
        
        Args:
            messages: List of message dicts
            temperature: Override temperature
            max_tokens: Max tokens
            **kwargs: Additional options
        
        Yields:
            ChatResponse chunks
        """
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
                        model=self.model,
                        metadata={
                            "finish_reason": chunk.choices[0].finish_reason
                        }
                    )
        
        except Exception as e:
            logger.error(f"Groq streaming error: {e}")
            raise RuntimeError(f"Groq streaming failed: {e}")
    
    async def achat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Async chat completion."""
        # Use sync version for now (Groq is so fast it doesn't matter)
        return self.chat(messages, temperature, max_tokens, **kwargs)


if __name__ == "__main__":
    import os
    
    print("=" * 60)
    print("⚡ Groq Provider Example (Ultra-Fast!)")
    print("=" * 60)
    print("\n💡 Get your API key: https://console.groq.com/keys\n")
    
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ GROQ_API_KEY environment variable not set")
        print("   Set it with: export GROQ_API_KEY='your-key'")
    else:
        try:
            # Create provider
            provider = GroqProvider(
                api_key=api_key,
                model="llama-3.1-8b-instant"  # Fastest model
            )
            
            print("Testing chat completion...")
            response = provider.chat([
                {"role": "user", "content": "Say hello in one sentence"}
            ])
            print(f"✅ Response: {response.content}\n")
            
            print("Testing streaming (watch the speed!)...")
            import time
            start = time.time()
            token_count = 0
            
            for chunk in provider.stream([
                {"role": "user", "content": "Count from 1 to 10"}
            ]):
                if chunk.content:
                    print(chunk.content, end='', flush=True)
                    token_count += len(chunk.content.split())
            
            elapsed = time.time() - start
            print(f"\n\n⚡ Speed: {token_count / elapsed:.1f} tokens/sec")
            print("   (Groq is FAST! 🚀)\n")
        
        except Exception as e:
            print(f"❌ Error: {e}")
