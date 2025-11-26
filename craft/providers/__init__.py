"""LLM Provider implementations."""

from craft.providers.base import Provider, ProviderConfig, ChatResponse, StreamChunk

__all__ = [
    "Provider",
    "ProviderConfig",
    "ChatResponse",
    "StreamChunk",
]

# Conditional imports for optional providers
try:
    from craft.providers.anthropic import AnthropicProvider
    __all__.append("AnthropicProvider")
except ImportError:
    pass

try:
    from craft.providers.openai import OpenAIProvider
    __all__.append("OpenAIProvider")
except ImportError:
    pass

try:
    from craft.providers.google import GoogleProvider
    __all__.append("GoogleProvider")
except ImportError:
    pass

try:
    from craft.providers.azure_openai import AzureOpenAIProvider
    __all__.append("AzureOpenAIProvider")
except ImportError:
    pass

try:
    from craft.providers.aws_bedrock import AWSBedrockProvider
    __all__.append("AWSBedrockProvider")
except ImportError:
    pass

try:
    from craft.providers.cohere import CohereProvider
    __all__.append("CohereProvider")
except ImportError:
    pass

try:
    from craft.providers.ollama import OllamaProvider, OllamaConfig
    __all__.append("OllamaProvider")  # Local LLM inference
    __all__.append("OllamaConfig")
except ImportError:
    pass

try:
    from craft.providers.groq import GroqProvider
    __all__.append("GroqProvider")  # Ultra-fast inference
except ImportError:
    pass

try:
    from craft.providers.mistral import MistralProvider
    __all__.append("MistralProvider")  # European AI
except ImportError:
    pass

try:
    from craft.providers.openrouter import OpenRouterProvider
    __all__.append("OpenRouterProvider")  # 400+ models aggregator
except ImportError:
    pass

try:
    from craft.providers.xai import xAIProvider
    __all__.append("xAIProvider")  # Grok (xAI)
except ImportError:
    pass
