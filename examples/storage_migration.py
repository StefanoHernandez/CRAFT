"""
Storage Migration Example

Demonstrates migrating conversations between different storage backends.
Useful when transitioning from development to production or changing databases.
"""

from craft.storage import SQLiteStorage
from craft.storage.base import StorageAdapter
from typing import List, Optional
import sys

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


def migrate_storage(
    source: StorageAdapter,
    destination: StorageAdapter,
    batch_size: int = 100,
    clear_destination: bool = False
) -> dict:
    """
    Migrate conversations from one storage to another.

    Args:
        source: Source storage adapter
        destination: Destination storage adapter
        batch_size: Number of conversations per batch
        clear_destination: Clear destination before migration

    Returns:
        Migration statistics
    """
    print(f"\n🔄 Starting migration: {source.name} → {destination.name}\n")

    stats = {
        "total": 0,
        "migrated": 0,
        "failed": 0,
        "skipped": 0
    }

    # Optionally clear destination
    if clear_destination:
        print("🗑️  Clearing destination storage...")
        destination.clear()

    # Get total count
    total = source.count()
    stats["total"] = total
    print(f"📊 Total conversations to migrate: {total}\n")

    if total == 0:
        print("⚠️  No conversations found in source storage")
        return stats

    # Migrate in batches
    offset = 0
    batch_num = 1

    while offset < total:
        print(f"📦 Batch {batch_num}:")

        # Load batch
        conversations = source.list_conversations(limit=batch_size, offset=offset)

        if not conversations:
            break

        # Migrate each conversation
        for conv_model in conversations:
            try:
                # Convert to Conversation object
                conversation = conv_model.to_conversation()

                # Check if already exists in destination
                existing = destination.load(conversation.id)
                if existing:
                    print(f"   ⏭️  Skipped {conversation.id} (already exists)")
                    stats["skipped"] += 1
                    continue

                # Save to destination
                success = destination.save(conversation)

                if success:
                    print(f"   ✅ Migrated {conversation.id}")
                    stats["migrated"] += 1
                else:
                    print(f"   ❌ Failed {conversation.id}")
                    stats["failed"] += 1

            except Exception as e:
                print(f"   ❌ Error migrating conversation: {e}")
                stats["failed"] += 1

        offset += len(conversations)
        batch_num += 1
        print()

    # Summary
    print("="*60)
    print("Migration Complete")
    print("="*60)
    print(f"Total:    {stats['total']}")
    print(f"Migrated: {stats['migrated']}")
    print(f"Skipped:  {stats['skipped']}")
    print(f"Failed:   {stats['failed']}")
    print()

    # Verify
    dest_count = destination.count()
    print(f"✅ Destination now has {dest_count} conversations")

    return stats


def example_sqlite_to_postgres():
    """Migrate from SQLite to PostgreSQL."""
    if not POSTGRES_AVAILABLE:
        print("⚠️  PostgreSQL not available")
        return

    print("\n" + "="*60)
    print("Example: SQLite → PostgreSQL")
    print("="*60)

    # Setup source (SQLite)
    source = SQLiteStorage(database_path="./craft_conversations.db")

    # Setup destination (PostgreSQL)
    destination = PostgreSQLStorage(
        host="localhost",
        database="craft",
        username="postgres",
        password="your-password"
    )

    # Migrate
    stats = migrate_storage(source, destination, batch_size=50)

    # Cleanup
    destination.close()


def example_redis_to_sqlite():
    """Backup Redis conversations to SQLite."""
    if not REDIS_AVAILABLE:
        print("⚠️  Redis not available")
        return

    print("\n" + "="*60)
    print("Example: Redis → SQLite (Backup)")
    print("="*60)

    # Setup source (Redis)
    source = RedisStorage(host="localhost")

    # Setup destination (SQLite backup)
    destination = SQLiteStorage(database_path="./redis_backup.db")

    # Migrate
    stats = migrate_storage(source, destination, clear_destination=True)


def example_mongodb_to_postgres():
    """Migrate from MongoDB to PostgreSQL."""
    if not MONGODB_AVAILABLE or not POSTGRES_AVAILABLE:
        print("⚠️  MongoDB or PostgreSQL not available")
        return

    print("\n" + "="*60)
    print("Example: MongoDB → PostgreSQL")
    print("="*60)

    # Setup source (MongoDB)
    source = MongoDBStorage(host="localhost", database="craft")

    # Setup destination (PostgreSQL)
    destination = PostgreSQLStorage(
        host="localhost",
        database="craft_postgres",
        username="postgres",
        password="your-password"
    )

    # Migrate
    stats = migrate_storage(source, destination)

    # Cleanup
    source.close()
    destination.close()


def export_to_json(storage: StorageAdapter, output_file: str):
    """Export all conversations to JSON file."""
    import json

    print(f"\n📤 Exporting to {output_file}...")

    conversations = storage.list_conversations()

    data = {
        "exported_at": str(storage.list_conversations()[0].updated_at) if conversations else None,
        "count": len(conversations),
        "conversations": [
            storage.export_conversation(conv.id)
            for conv in conversations
        ]
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"✅ Exported {len(conversations)} conversations")


def import_from_json(storage: StorageAdapter, input_file: str):
    """Import conversations from JSON file."""
    import json

    print(f"\n📥 Importing from {input_file}...")

    with open(input_file, 'r') as f:
        data = json.load(f)

    success_count = 0
    for conv_data in data.get("conversations", []):
        if storage.import_conversation(conv_data):
            success_count += 1

    print(f"✅ Imported {success_count}/{len(data['conversations'])} conversations")


def main():
    print("🔄 CRAFT Storage Migration Tool\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "sqlite-to-postgres":
            example_sqlite_to_postgres()
        elif command == "redis-backup":
            example_redis_to_sqlite()
        elif command == "mongo-to-postgres":
            example_mongodb_to_postgres()
        else:
            print(f"Unknown command: {command}")
    else:
        print("Usage:")
        print("  python storage_migration.py <command>")
        print()
        print("Commands:")
        print("  sqlite-to-postgres  - Migrate SQLite to PostgreSQL")
        print("  redis-backup        - Backup Redis to SQLite")
        print("  mongo-to-postgres   - Migrate MongoDB to PostgreSQL")
        print()
        print("Example:")
        print("  python storage_migration.py sqlite-to-postgres")
        print()
        print("Or use as a library:")
        print()
        print("  from storage_migration import migrate_storage")
        print("  migrate_storage(source_storage, dest_storage)")


if __name__ == "__main__":
    main()
