"""
Storage Comparison Example

Demonstrates different storage backends and their characteristics.
Shows how to easily switch between storage adapters.
"""

from craft import Chatbot, Conversation
from craft.providers import AnthropicProvider
from craft.storage import SQLiteStorage
from craft.providers.base import Message, Role
import os
import time

# Try to import optional storage backends
try:
    from craft.storage import PostgreSQLStorage
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    from craft.storage import RedisStorage
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from craft.storage import MongoDBStorage
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


def test_storage(storage, name: str):
    """Test a storage adapter with basic operations."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}\n")

    # Create a test conversation
    conversation = Conversation()
    conversation.add_message(Message(
        role=Role.USER,
        content="What is the capital of France?"
    ))
    conversation.add_message(Message(
        role=Role.ASSISTANT,
        content="The capital of France is Paris."
    ))

    # Test save
    start = time.time()
    success = storage.save(conversation)
    save_time = (time.time() - start) * 1000

    if success:
        print(f"✅ Save: {save_time:.2f}ms")
    else:
        print(f"❌ Save failed")
        return

    # Test load
    start = time.time()
    loaded = storage.load(conversation.id)
    load_time = (time.time() - start) * 1000

    if loaded:
        print(f"✅ Load: {load_time:.2f}ms")
        print(f"   Messages: {len(loaded.messages)}")
    else:
        print(f"❌ Load failed")
        return

    # Test list
    start = time.time()
    conversations = storage.list_conversations(limit=10)
    list_time = (time.time() - start) * 1000

    print(f"✅ List: {list_time:.2f}ms")
    print(f"   Found: {len(conversations)} conversations")

    # Test search
    start = time.time()
    results = storage.search("France", limit=5)
    search_time = (time.time() - start) * 1000

    print(f"✅ Search: {search_time:.2f}ms")
    print(f"   Results: {len(results)}")

    # Test count
    count = storage.count()
    print(f"✅ Count: {count} total conversations")

    # Test delete
    start = time.time()
    deleted = storage.delete(conversation.id)
    delete_time = (time.time() - start) * 1000

    if deleted:
        print(f"✅ Delete: {delete_time:.2f}ms")

    # Summary
    print(f"\n📊 Performance Summary:")
    print(f"   Save:   {save_time:>8.2f}ms")
    print(f"   Load:   {load_time:>8.2f}ms")
    print(f"   List:   {list_time:>8.2f}ms")
    print(f"   Search: {search_time:>8.2f}ms")
    print(f"   Delete: {delete_time:>8.2f}ms")


def main():
    print("🗄️  Storage Backend Comparison\n")

    # Test SQLite (always available)
    print("Testing SQLite - File-based storage")
    sqlite = SQLiteStorage(database_path="./test_storage.db")
    test_storage(sqlite, "SQLite")

    # Test PostgreSQL (if available)
    if POSTGRES_AVAILABLE:
        try:
            print("\n" + "="*60)
            print("Testing PostgreSQL - Production database")
            postgres = PostgreSQLStorage(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "craft"),
                username=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", ""),
            )
            test_storage(postgres, "PostgreSQL")
            postgres.close()
        except Exception as e:
            print(f"\n⚠️  PostgreSQL not available: {e}")
    else:
        print("\n⚠️  PostgreSQL not installed (pip install 'craft-chatbot[storage]')")

    # Test Redis (if available)
    if REDIS_AVAILABLE:
        try:
            print("\n" + "="*60)
            print("Testing Redis - In-memory cache")
            redis = RedisStorage(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
            )
            test_storage(redis, "Redis")
        except Exception as e:
            print(f"\n⚠️  Redis not available: {e}")
    else:
        print("\n⚠️  Redis not installed (pip install 'craft-chatbot[storage]')")

    # Test MongoDB (if available)
    if MONGODB_AVAILABLE:
        try:
            print("\n" + "="*60)
            print("Testing MongoDB - NoSQL database")
            mongodb = MongoDBStorage(
                host=os.getenv("MONGODB_HOST", "localhost"),
                port=int(os.getenv("MONGODB_PORT", "27017")),
            )
            test_storage(mongodb, "MongoDB")
            mongodb.close()
        except Exception as e:
            print(f"\n⚠️  MongoDB not available: {e}")
    else:
        print("\n⚠️  MongoDB not installed (pip install 'craft-chatbot[storage]')")

    print("\n" + "="*60)
    print("Storage Comparison Complete")
    print("="*60)

    print("\n📝 Recommendations:")
    print("   • SQLite: Development, small apps, single server")
    print("   • PostgreSQL: Production apps, complex queries, ACID compliance")
    print("   • Redis: Caching, sessions, high-speed temporary storage")
    print("   • MongoDB: Flexible schemas, rapid development, scalability")


if __name__ == "__main__":
    main()
