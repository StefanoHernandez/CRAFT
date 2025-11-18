"""
SQLite Storage Example

Demonstrates using SQLite for persistent conversation storage.
Perfect for development and small-scale deployments.
"""

from craft import Chatbot, Conversation
from craft.providers import AnthropicProvider
from craft.storage import SQLiteStorage
from craft.core.memory import Memory
import os


def main():
    print("🗄️  SQLite Storage Example\n")

    # Initialize SQLite storage
    storage = SQLiteStorage(database_path="./craft_conversations.db")
    print(f"✅ Connected to SQLite database")
    print(f"   Conversations stored: {storage.count()}\n")

    # Create chatbot with storage-backed memory
    chatbot = Chatbot(
        provider=AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY")),
        memory=True,
        system_prompt="You are a helpful assistant with persistent memory."
    )

    # Chat with the bot
    print("💬 Chat 1:")
    response = chatbot.chat("My name is Alice and I love Python programming.")
    print(f"   Bot: {response.content}\n")

    print("💬 Chat 2:")
    response = chatbot.chat("What programming language did I mention?")
    print(f"   Bot: {response.content}\n")

    # Save conversation to storage
    conversation_id = chatbot.conversation.id
    success = storage.save(chatbot.conversation)

    if success:
        print(f"✅ Conversation saved with ID: {conversation_id}\n")
    else:
        print("❌ Failed to save conversation\n")
        return

    # List all conversations
    print("📋 All Conversations:")
    conversations = storage.list_conversations(limit=5)
    for conv_model in conversations:
        msg_count = len(conv_model.messages)
        print(f"   - {conv_model.id}: {msg_count} messages (updated: {conv_model.updated_at})")
    print()

    # Search conversations
    print("🔍 Searching for 'Python':")
    results = storage.search("Python", limit=3)
    for conv_model in results:
        print(f"   - Found in conversation: {conv_model.id}")
    print()

    # Load conversation in a new chatbot
    print("🔄 Loading conversation in new chatbot:")
    loaded_conversation = storage.load(conversation_id)

    if loaded_conversation:
        new_chatbot = Chatbot(
            provider=AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY")),
            memory=True
        )
        new_chatbot.conversation = loaded_conversation

        print(f"   Loaded {len(loaded_conversation.messages)} messages\n")

        # Continue conversation
        print("💬 Continued Chat:")
        response = new_chatbot.chat("Can you remind me what my name is?")
        print(f"   Bot: {response.content}\n")

        # Update storage with new message
        storage.save(new_chatbot.conversation)
        print("✅ Updated conversation in storage\n")

    # Export conversation
    print("📤 Exporting conversation:")
    exported = storage.export_conversation(conversation_id)
    if exported:
        print(f"   Exported {len(exported['messages'])} messages")
        print(f"   Created: {exported['created_at']}")
        print(f"   Updated: {exported['updated_at']}\n")

    # Statistics
    print("📊 Storage Statistics:")
    print(f"   Total conversations: {storage.count()}")
    print(f"   Database: {storage.db_path}")

    # Optional: Clear all conversations
    # print("\n🗑️  Clearing all conversations...")
    # storage.clear()
    # print(f"   Remaining conversations: {storage.count()}")


if __name__ == "__main__":
    main()
