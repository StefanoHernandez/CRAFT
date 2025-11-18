"""Streaming chatbot example with CRAFT."""

import os
import sys
from craft import Chatbot
from craft.providers import AnthropicProvider


def main():
    # Create chatbot with streaming enabled
    chatbot = Chatbot(
        provider=AnthropicProvider(
            model="claude-3-5-sonnet-20241022",
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ),
        system_prompt="You are a helpful assistant that provides detailed explanations.",
        memory=True,
    )

    print("🚀 CRAFT Streaming Chatbot Demo")
    print("=" * 50)
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Goodbye! 👋")
            break

        # Stream response
        try:
            print("Assistant: ", end="", flush=True)

            stream = chatbot.chat(user_input, stream=True)

            for chunk in stream:
                if chunk.content:
                    print(chunk.content, end="", flush=True)
                    sys.stdout.flush()

            print("\n")

        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
