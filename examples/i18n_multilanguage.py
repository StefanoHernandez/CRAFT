"""
Multi-language Support Example

Demonstrates CRAFT's i18n system for multi-language chatbots.
"""

from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.i18n import Translator, Language, detect_language
import os


def main():
    print("🌍 Multi-language Support Example\n")

    # Create chatbot
    provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
    chatbot = Chatbot(provider=provider)

    # Example 1: Manual language selection
    print("=" * 60)
    print("Example 1: Italian chatbot")
    print("=" * 60)

    translator_it = Translator(language=Language.ITALIAN)
    print(translator_it.get("welcome"))  # "Benvenuto in CRAFT"

    # Add language instruction to system prompt
    italian_prompt = translator_it.translate_prompt(
        "You are a helpful AI assistant."
    )
    chatbot_it = Chatbot(
        provider=provider,
        system_prompt=italian_prompt
    )

    response = chatbot_it.chat("Ciao! Come stai?")
    print(f"\nUser: Ciao! Come stai?")
    print(f"Bot: {response.content}\n")

    # Example 2: Auto-detect language
    print("=" * 60)
    print("Example 2: Auto-detect language")
    print("=" * 60)

    texts = [
        ("Hello, how are you?", Language.ENGLISH),
        ("Bonjour, comment allez-vous?", Language.FRENCH),
        ("Hola, ¿cómo estás?", Language.SPANISH),
        ("Hallo, wie geht es dir?", Language.GERMAN),
        ("Ciao, come stai?", Language.ITALIAN),
    ]

    for text, expected_lang in texts:
        detected = detect_language(text)
        translator = Translator(language=detected)
        welcome = translator.get("welcome")

        print(f"\nText: {text}")
        print(f"Detected: {detected.value} (expected: {expected_lang.value})")
        print(f"Welcome message: {welcome}")

    # Example 3: Using translator for system messages
    print("\n" + "=" * 60)
    print("Example 3: Translated system messages")
    print("=" * 60)

    for lang in [Language.ENGLISH, Language.ITALIAN, Language.SPANISH, Language.FRENCH]:
        translator = Translator(language=lang)
        print(f"\n{lang.value.upper()}:")
        print(f"  Welcome: {translator.get('welcome')}")
        print(f"  Error: {translator.get('error')}")
        print(f"  Goodbye: {translator.get('goodbye')}")

    # Example 4: Chatbot with automatic language adaptation
    print("\n" + "=" * 60)
    print("Example 4: Multi-language conversation")
    print("=" * 60)

    def chat_in_language(user_message: str):
        """Chat with auto-detected language."""
        # Detect language
        lang = detect_language(user_message)
        translator = Translator(language=lang)

        # Create chatbot with language-specific prompt
        lang_prompt = translator.translate_prompt(
            "You are a helpful AI assistant."
        )
        bot = Chatbot(provider=provider, system_prompt=lang_prompt)

        # Chat
        response = bot.chat(user_message)

        print(f"\n[{lang.value}] User: {user_message}")
        print(f"[{lang.value}] Bot: {response.content}")

    # Test different languages
    chat_in_language("Hello! Tell me a joke.")
    chat_in_language("Ciao! Raccontami una barzelletta.")
    chat_in_language("¡Hola! Cuéntame un chiste.")

    # Example 5: Custom translations
    print("\n" + "=" * 60)
    print("Example 5: Using translation keys")
    print("=" * 60)

    translator = Translator(language=Language.ITALIAN)

    # System messages
    print(f"Conversation started: {translator.get('conversation_started')}")
    print(f"Message sent: {translator.get('message_sent')}")
    print(f"Connection error: {translator.get('connection_error')}")

    # With formatting
    response_msg = translator.get(
        "respond_in_language",
        language=translator.get("language_name_it")
    )
    print(f"Instruction: {response_msg}")


if __name__ == "__main__":
    main()
