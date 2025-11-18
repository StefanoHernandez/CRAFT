"""Storage adapters for persistent conversation storage."""

from craft.storage.base import StorageAdapter, ConversationModel

__all__ = [
    "StorageAdapter",
    "ConversationModel",
]

# Conditional imports for optional storage backends
try:
    from craft.storage.sqlite import SQLiteStorage
    __all__.append("SQLiteStorage")
except ImportError:
    pass

try:
    from craft.storage.postgresql import PostgreSQLStorage
    __all__.append("PostgreSQLStorage")
except ImportError:
    pass

try:
    from craft.storage.redis import RedisStorage
    __all__.append("RedisStorage")
except ImportError:
    pass

try:
    from craft.storage.mongodb import MongoDBStorage
    __all__.append("MongoDBStorage")
except ImportError:
    pass
