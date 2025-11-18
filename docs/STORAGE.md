# Storage & Persistence Guide

CRAFT provides flexible storage adapters for persisting conversations across different database backends.

## Overview

The storage system allows you to:

- **Persist conversations** across sessions
- **Search** conversation history
- **Export/Import** conversations
- **Migrate** between storage backends
- **Scale** from development to production

## Available Storage Adapters

### SQLite Storage

Perfect for development and small-scale deployments.

**Features:**
- File-based, no server required
- Zero configuration
- Full-text search support
- ACID compliant

**Usage:**
```python
from craft.storage import SQLiteStorage

storage = SQLiteStorage(database_path="./conversations.db")
```

**Best for:**
- Development and testing
- Small applications
- Single-server deployments
- Embedded systems

---

### PostgreSQL Storage

Production-ready relational database with advanced features.

**Features:**
- JSONB columns for flexible message storage
- GIN indexes for fast full-text search
- Connection pooling
- ACID compliance
- Horizontal scalability

**Usage:**
```python
from craft.storage import PostgreSQLStorage

storage = PostgreSQLStorage(
    host="localhost",
    port=5432,
    database="craft",
    username="postgres",
    password="your-password",
    pool_size=10
)
```

**Best for:**
- Production applications
- High-volume traffic
- Complex queries
- Multi-server deployments
- When you need strong data consistency

---

### Redis Storage

In-memory cache with optional persistence.

**Features:**
- Extremely fast (sub-millisecond latency)
- TTL support for automatic expiration
- Sorted sets for timestamp-based indexing
- Optional persistence to disk
- Pub/Sub capabilities

**Usage:**
```python
from craft.storage import RedisStorage

storage = RedisStorage(
    host="localhost",
    port=6379,
    db=0,
    password=None,
    ttl=3600  # 1 hour TTL
)
```

**Best for:**
- Session storage
- Caching
- Real-time applications
- Temporary conversation storage
- High-speed requirements

---

### MongoDB Storage

NoSQL document database with flexible schemas.

**Features:**
- Flexible document structure
- Text search indexes
- Horizontal scalability
- Automatic sharding
- Geospatial queries

**Usage:**
```python
from craft.storage import MongoDBStorage

storage = MongoDBStorage(
    host="localhost",
    port=27017,
    database="craft",
    collection="conversations",
    username=None,
    password=None
)
```

**Best for:**
- Rapid development
- Flexible schemas
- Large-scale deployments
- Document-oriented data
- When you need horizontal scaling

## Basic Operations

### Saving Conversations

```python
from craft import Chatbot, Conversation
from craft.storage import SQLiteStorage

# Create storage
storage = SQLiteStorage()

# Create chatbot
chatbot = Chatbot(provider=provider)

# Have a conversation
chatbot.chat("Hello!")

# Save conversation
success = storage.save(chatbot.conversation)
```

### Loading Conversations

```python
# Load by ID
conversation = storage.load("conversation-id-123")

if conversation:
    # Use in new chatbot
    chatbot.conversation = conversation
    chatbot.chat("Continue our chat...")
```

### Listing Conversations

```python
# List recent conversations
conversations = storage.list_conversations(limit=10, offset=0)

for conv in conversations:
    print(f"ID: {conv.id}")
    print(f"Messages: {len(conv.messages)}")
    print(f"Updated: {conv.updated_at}")
```

### Searching Conversations

```python
# Search by content
results = storage.search("Python programming", limit=5)

for conv in results:
    print(f"Found in: {conv.id}")
```

### Deleting Conversations

```python
# Delete a conversation
deleted = storage.delete("conversation-id-123")

if deleted:
    print("Conversation deleted")
```

### Counting Conversations

```python
# Get total count
total = storage.count()
print(f"Total conversations: {total}")
```

### Clearing All Conversations

```python
# Clear all (use with caution!)
storage.clear()
```

## Export & Import

### Exporting Conversations

```python
# Export single conversation
data = storage.export_conversation("conversation-id-123")

# Save to JSON file
import json
with open("conversation.json", "w") as f:
    json.dump(data, f, indent=2, default=str)
```

### Importing Conversations

```python
# Load from JSON
import json
with open("conversation.json", "r") as f:
    data = json.load(f)

# Import
success = storage.import_conversation(data)
```

### Batch Export

```python
# Export all conversations
conversations = storage.list_conversations()

exported_data = {
    "count": len(conversations),
    "conversations": [
        storage.export_conversation(conv.id)
        for conv in conversations
    ]
}

with open("all_conversations.json", "w") as f:
    json.dump(exported_data, f, indent=2, default=str)
```

## Migration Between Storage Backends

### Migrating from SQLite to PostgreSQL

```python
from craft.storage import SQLiteStorage, PostgreSQLStorage

# Source
source = SQLiteStorage(database_path="./dev.db")

# Destination
destination = PostgreSQLStorage(
    host="prod-db.example.com",
    database="craft_production",
    username="craft_user",
    password="secure-password"
)

# Migrate all conversations
conversations = source.list_conversations()

for conv_model in conversations:
    conversation = conv_model.to_conversation()
    destination.save(conversation)

print(f"Migrated {len(conversations)} conversations")
```

### Using the Migration Tool

```python
from examples.storage_migration import migrate_storage

stats = migrate_storage(
    source=sqlite_storage,
    destination=postgres_storage,
    batch_size=100,
    clear_destination=False
)

print(f"Migrated: {stats['migrated']}")
print(f"Failed: {stats['failed']}")
```

## Integration with Memory System

CRAFT's Memory system can use storage adapters for persistence:

```python
from craft import Chatbot
from craft.core.memory import Memory
from craft.storage import PostgreSQLStorage

# Create storage-backed memory
storage = PostgreSQLStorage(...)
memory = Memory(storage=storage, max_messages=100)

# Create chatbot with persistent memory
chatbot = Chatbot(
    provider=provider,
    memory=memory
)

# Conversations are automatically saved to storage
chatbot.chat("Hello!")
```

## Performance Comparison

| Operation | SQLite | PostgreSQL | Redis | MongoDB |
|-----------|--------|------------|-------|---------|
| Save      | ~5ms   | ~10ms      | ~1ms  | ~8ms    |
| Load      | ~3ms   | ~8ms       | ~0.5ms| ~6ms    |
| Search    | ~20ms  | ~15ms      | ~30ms | ~12ms   |
| List      | ~10ms  | ~12ms      | ~5ms  | ~10ms   |

*Note: Times are approximate and depend on hardware, data size, and configuration.*

## Best Practices

### 1. Choose the Right Storage

- **Development**: SQLite
- **Production (small-medium)**: PostgreSQL
- **Production (large-scale)**: PostgreSQL or MongoDB
- **Caching/Sessions**: Redis
- **Temporary storage**: Redis with TTL

### 2. Use Connection Pooling

For PostgreSQL:
```python
storage = PostgreSQLStorage(
    host="localhost",
    pool_size=20,
    max_overflow=10
)
```

### 3. Implement TTL for Redis

```python
storage = RedisStorage(
    ttl=86400  # 24 hours
)

# Or set per-conversation
storage.set_ttl("conversation-id", 3600)  # 1 hour
```

### 4. Regular Backups

```python
# Backup to JSON
def backup_to_json(storage, filename):
    conversations = storage.list_conversations()
    data = {
        "count": len(conversations),
        "conversations": [
            storage.export_conversation(conv.id)
            for conv in conversations
        ]
    }
    with open(filename, "w") as f:
        json.dump(data, f, default=str)

# Schedule daily backups
backup_to_json(storage, "backup_2024_01_01.json")
```

### 5. Index Optimization

For PostgreSQL, ensure indexes are created:
```sql
-- Check existing indexes
SELECT * FROM pg_indexes WHERE tablename = 'conversations';

-- Create custom indexes if needed
CREATE INDEX idx_custom ON conversations(created_at DESC);
```

### 6. Cleanup Old Conversations

```python
from datetime import datetime, timedelta

# Delete conversations older than 30 days
cutoff = datetime.now() - timedelta(days=30)

conversations = storage.list_conversations()
for conv in conversations:
    if conv.updated_at < cutoff:
        storage.delete(conv.id)
```

## Error Handling

```python
try:
    storage = PostgreSQLStorage(
        host="localhost",
        database="craft"
    )
    success = storage.save(conversation)

    if not success:
        print("Failed to save conversation")

except Exception as e:
    print(f"Storage error: {e}")
    # Fallback to SQLite
    storage = SQLiteStorage()
    storage.save(conversation)
```

## Installation

Different storage backends require different dependencies:

```bash
# SQLite (included by default)
pip install craft-chatbot

# PostgreSQL
pip install 'craft-chatbot[storage]'
# or
pip install craft-chatbot psycopg2-binary sqlalchemy

# Redis
pip install 'craft-chatbot[storage]'
# or
pip install craft-chatbot redis

# MongoDB
pip install 'craft-chatbot[storage]'
# or
pip install craft-chatbot pymongo
```

## Docker Setup

### PostgreSQL

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: craft
      POSTGRES_USER: craft_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Redis

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### MongoDB

```yaml
services:
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: craft
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

## Troubleshooting

### Connection Errors

**PostgreSQL:**
```python
# Check connection
try:
    storage = PostgreSQLStorage(...)
    count = storage.count()
    print(f"Connected! {count} conversations")
except Exception as e:
    print(f"Connection failed: {e}")
```

**Redis:**
```python
# Test Redis connection
try:
    storage = RedisStorage(...)
    storage.client.ping()
    print("Redis connected!")
except Exception as e:
    print(f"Redis connection failed: {e}")
```

### Performance Issues

1. **Enable connection pooling** (PostgreSQL)
2. **Add indexes** for frequently queried fields
3. **Use batching** for bulk operations
4. **Consider Redis** for caching frequently accessed conversations

### Data Inconsistency

```python
# Verify data integrity
conversation = storage.load("id-123")
if conversation:
    assert len(conversation.messages) > 0
    assert conversation.id == "id-123"
```

## Examples

See the `examples/` directory:

- `storage_sqlite.py` - Basic SQLite usage
- `storage_comparison.py` - Compare all storage backends
- `storage_migration.py` - Migrate between backends

## Learn More

- [Main Documentation](../README.md)
- [API Integration](API_INTEGRATION.md)
- [MCP Integration](MCP_INTEGRATION.md)
