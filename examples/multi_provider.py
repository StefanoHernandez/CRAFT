"""Example showing how to switch between different providers."""

import os
from craft import Chatbot
from craft.providers import AnthropicProvider, OpenAIProvider, GoogleProvider


def chat_with_provider(provider_name: str, provider, question: str):
    """Chat with a specific provider."""
    print(f"\n{'='*60}")
    print(f"Provider: {provider_name}")
    print(f"Model: {provider.model_name}")
    print(f"{'='*60}")

    chatbot = Chatbot(
        provider=provider,
        system_prompt="You are a helpful assistant. Keep responses concise.",
    )

    response = chatbot.chat(question)
    print(f"\nQ: {question}")
    print(f"A: {response.content}\n")

    if response.usage:
        print(f"Tokens: {response.usage['total_tokens']}")


def main():
    question = "What is the meaning of life in one sentence?"

    print("🌐 CRAFT Multi-Provider Example")
    print("This example shows the same question answered by different providers\n")

    # Anthropic (Claude)
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            provider = AnthropicProvider(
                model="claude-sonnet-4.5",
                temperature=0.7
            )
            chat_with_provider("Anthropic Claude", provider, question)
        except Exception as e:
            print(f"❌ Anthropic error: {e}")
    else:
        print("⚠️  ANTHROPIC_API_KEY not set, skipping...")

    # OpenAI (GPT)
    if os.getenv("OPENAI_API_KEY"):
        try:
            provider = OpenAIProvider(
                model="gpt-4o",
                temperature=0.7
            )
            chat_with_provider("OpenAI GPT-4", provider, question)
        except Exception as e:
            print(f"❌ OpenAI error: {e}")
    else:
        print("⚠️  OPENAI_API_KEY not set, skipping...")

    # Google (Gemini)
    if os.getenv("GOOGLE_API_KEY"):
        try:
            provider = GoogleProvider(
                model="gemini-2.5-pro",
                temperature=0.7
            )
            chat_with_provider("Google Gemini", provider, question)
        except Exception as e:
            print(f"❌ Google error: {e}")
    else:
        print("⚠️  GOOGLE_API_KEY not set, skipping...")


if __name__ == "__main__":
    main()
