"""Basic chatbot example with CRAFT."""

import os
from craft import Chatbot
from craft.providers import AnthropicProvider

# Make sure to set ANTHROPIC_API_KEY environment variable
# or create a .env file with your API key

def main():
    # Create chatbot with Anthropic provider
    chatbot = Chatbot(
        provider=AnthropicProvider(
            model="claude-sonnet-4.5",
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ),
        system_prompt="You are a helpful assistant.",
        memory=True,  # Enable conversation memory
    )

    print("🤖 CRAFT Chatbot Demo")
    print("=" * 50)
    print(f"Provider: {chatbot.provider.name}")
    print(f"Model: {chatbot.provider.model_name}")
    print("=" * 50)
    print("\nType 'exit' to quit, 'clear' to reset conversation\n")

    while True:
        # Get user input
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Goodbye! 👋")
            break

        if user_input.lower() == "clear":
            chatbot.clear_conversation()
            print("🔄 Conversation cleared!\n")
            continue

        # Get response
        try:
            response = chatbot.chat(user_input)
            print(f"\nAssistant: {response.content}\n")

            # Show token usage if available
            if response.usage:
                print(f"[Tokens: {response.usage['total_tokens']}]\n")

        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
