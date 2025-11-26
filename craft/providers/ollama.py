"""Ollama provider for local LLM inference.

Ollama enables running open-source models locally (Llama 3, Mistral, Qwen, etc.)
with zero API costs and full privacy.

Install Ollama: https://ollama.ai
Run a model: ollama run llama3
"""

from typing import List, Dict, Any, Optional, Iterator, AsyncIterator
import logging
import json

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None

from craft.providers.base import Provider, ProviderConfig, ChatResponse
from pydantic import ConfigDict


logger = logging.getLogger(__name__)


class OllamaConfig(ProviderConfig):
    """Configuration for Ollama provider."""
    
    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    num_ctx: int = 2048  # Context window size
    num_predict: int = -1  # Max tokens to generate (-1 = unlimited)
    stop: Optional[List[str]] = None
    
    model_config = ConfigDict(extra="allow")


class OllamaProvider(Provider):
    """
    Ollama provider for local LLM inference.
    
    Ollama runs open-source models locally with zero API costs.
    Perfect for development, testing, and privacy-sensitive applications.
    
    Supported models:
    - llama3, llama3:70b
    - mistral, mistral:7b
    - codellama, codellama:34b
    - qwen2.5, qwen2.5:7b
    - gemma2, gemma2:9b
    - phi3, phi3:mini
    - And many more!
    
    Example:
        from craft.providers import OllamaProvider
        
        # Create provider
        provider = OllamaProvider(
            model="llama3",
            temperature=0.7
        )
        
        # Chat completion
        response = provider.chat([
            {"role": "user", "content": "Hello!"}
        ])
        print(response.content)
        
        # Streaming
        for chunk in provider.stream([
            {"role": "user", "content": "Tell me a story"}
        ]):
            print(chunk.content, end='', flush=True)
    
    Prerequisites:
        1. Install Ollama: https://ollama.ai
        2. Pull a model: `ollama pull llama3`
        3. Start Ollama: `ollama serve` (usually auto-started)
    """
    
    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model name (e.g., "llama3", "mistral", "codellama")
            base_url: Ollama server URL
            temperature: Sampling temperature (0-1)
            **kwargs: Additional Ollama parameters
        """
        if not HAS_REQUESTS:
            raise ImportError(
                "requests is required for Ollama provider. "
                "Install it with: pip install requests"
            )
        
        config = OllamaConfig(
            model=model,
            base_url=base_url,
            temperature=temperature,
            **kwargs
        )
        super().__init__(config)
        
        self.base_url = base_url.rstrip('/')
        self.model = model
        
        # Test connection
        try:
            self._test_connection()
        except Exception as e:
            logger.warning(f"Ollama connection test failed: {e}")
            logger.warning("Make sure Ollama is running: ollama serve")
    
    def _test_connection(self) -> bool:
        """Test connection to Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
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
            **kwargs: Additional Ollama options
        
        Returns:
            ChatResponse with generated text
        """
        # Prepare request
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "num_ctx": self.config.num_ctx,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        elif self.config.num_predict != -1:
            payload["options"]["num_predict"] = self.config.num_predict
        
        if self.config.stop:
            payload["options"]["stop"] = self.config.stop
        
        # Add custom options
        if kwargs:
            payload["options"].update(kwargs)
        
        # Make request
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            
            return ChatResponse(
                content=result["message"]["content"],
                role=result["message"]["role"],
                model=self.model,
                usage={
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                },
                metadata={
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "eval_duration": result.get("eval_duration"),
                }
            )
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            raise RuntimeError(f"Ollama API error: {e}")
    
    def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[ChatResponse]:
        """
        Stream chat completion.
        
        Args:
            messages: List of message dicts
            temperature: Override temperature
            max_tokens: Max tokens
            **kwargs: Additional options
        
        Yields:
            ChatResponse chunks
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature or self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "num_ctx": self.config.num_ctx,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        if kwargs:
            payload["options"].update(kwargs)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    
                    if chunk.get("done"):
                        # Final chunk with metadata
                        yield ChatResponse(
                            content="",
                            role="assistant",
                            model=self.model,
                            usage={
                                "prompt_tokens": chunk.get("prompt_eval_count", 0),
                                "completion_tokens": chunk.get("eval_count", 0),
                            },
                            finish_reason="stop"
                        )
                    else:
                        # Content chunk
                        yield ChatResponse(
                            content=chunk["message"]["content"],
                            role=chunk["message"]["role"],
                            model=self.model
                        )
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise RuntimeError(f"Ollama streaming error: {e}")
    
    async def achat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Async chat completion."""
        if not HAS_AIOHTTP:
            raise ImportError(
                "aiohttp is required for async Ollama. "
                "Install it with: pip install aiohttp"
            )
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "num_ctx": self.config.num_ctx,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                result = await response.json()
                
                return ChatResponse(
                    content=result["message"]["content"],
                    role=result["message"]["role"],
                    model=self.model,
                    usage={
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "completion_tokens": result.get("eval_count", 0),
                    }
                )
    
    def list_models(self) -> List[str]:
        """
        List available models on Ollama server.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("🦙 Ollama Provider Example")
    print("=" * 60)
    print("\n💡 Make sure Ollama is running: ollama serve")
    print("   And you have a model: ollama pull llama3\n")
    
    try:
        # Create provider
        provider = OllamaProvider(model="llama3", temperature=0.7)
        
        # List available models
        models = provider.list_models()
        print(f"Available models: {', '.join(models) if models else 'None (pull a model first!)'}\n")
        
        if not models:
            print("❌ No models available. Run: ollama pull llama3")
        else:
            # Test chat
            print("Testing chat completion...")
            response = provider.chat([
                {"role": "user", "content": "Say hello in one sentence"}
            ])
            print(f"✅ Response: {response.content}\n")
            
            # Test streaming
            print("Testing streaming...")
            for chunk in provider.stream([
                {"role": "user", "content": "Count to 5"}
            ]):
                if chunk.content:
                    print(chunk.content, end='', flush=True)
            print("\n")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Install Ollama: https://ollama.ai")
        print("   2. Start Ollama: ollama serve")
        print("   3. Pull a model: ollama pull llama3")
