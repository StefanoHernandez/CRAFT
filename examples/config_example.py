"""Example using configuration files."""

from craft import Chatbot
from craft.utils.config import load_config
from craft.providers import AnthropicProvider, OpenAIProvider, GoogleProvider


def create_provider_from_config(config):
    """Create provider based on config."""
    provider_map = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "google": GoogleProvider,
    }

    provider_class = provider_map.get(config.provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {config.provider}")

    return provider_class(**config.provider_config)


def main():
    print("📝 CRAFT Configuration Example\n")

    # Load configuration from file or environment
    # Priority: file > environment > defaults
    config = load_config(
        config_path="config.yaml",  # Optional config file
        use_env=True,  # Load from environment variables
    )

    print(f"Provider: {config.provider}")
    print(f"Streaming: {config.streaming}")
    print(f"Memory: {config.memory_enabled}")
    print(f"Log Level: {config.log_level}\n")

    # Create provider from config
    provider = create_provider_from_config(config)

    # Create chatbot
    chatbot = Chatbot(
        provider=provider,
        memory=config.memory_enabled,
        log_level=config.log_level,
    )

    # Test chat
    response = chatbot.chat("Hello! Tell me a fun fact about Python.", stream=config.streaming)

    if config.streaming:
        print("Assistant: ", end="", flush=True)
        for chunk in response:
            if chunk.content:
                print(chunk.content, end="", flush=True)
        print("\n")
    else:
        print(f"Assistant: {response.content}\n")


if __name__ == "__main__":
    main()
