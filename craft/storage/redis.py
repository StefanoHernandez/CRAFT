"""Redis storage adapter."""

import json
from typing import List, Optional
from datetime import datetime

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from craft.storage.base import StorageAdapter, ConversationModel
from craft.core.conversation import Conversation
from craft.utils.logging import get_logger


class RedisStorage(StorageAdapter):
    """
    Redis storage adapter for conversations.

    Fast, in-memory storage with optional persistence. Great for caching and sessions.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "craft:conversations:",
        ttl: Optional[int] = None,
    ):
        """
        Initialize Redis storage.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional password
            key_prefix: Prefix for all keys
            ttl: Optional TTL in seconds for conversations
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package not installed. "
                "Install with: pip install 'craft-chatbot[storage]'"
            )

        self.key_prefix = key_prefix
        self.ttl = ttl
        self.logger = get_logger("craft.storage.redis")

        # Connect to Redis
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )

        # Test connection
        try:
            self.client.ping()
            self.logger.info(f"Connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _make_key(self, conversation_id: str) -> str:
        """Create Redis key from conversation ID."""
        return f"{self.key_prefix}{conversation_id}"

    def _index_key(self) -> str:
        """Get key for conversation index (sorted set by timestamp)."""
        return f"{self.key_prefix}index"

    def save(self, conversation: Conversation) -> bool:
        """Save conversation to Redis."""
        try:
            model = ConversationModel.from_conversation(conversation)
            key = self._make_key(conversation.id)

            # Serialize conversation
            data = model.model_dump_json()

            # Save to Redis
            self.client.set(key, data)

            # Set TTL if configured
            if self.ttl:
                self.client.expire(key, self.ttl)

            # Add to index (sorted set by updated_at timestamp)
            timestamp = model.updated_at.timestamp()
            self.client.zadd(self._index_key(), {conversation.id: timestamp})

            self.logger.debug(f"Saved conversation {conversation.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving conversation: {e}")
            return False

    def load(self, conversation_id: str) -> Optional[Conversation]:
        """Load conversation from Redis."""
        try:
            key = self._make_key(conversation_id)
            data = self.client.get(key)

            if data:
                model = ConversationModel.model_validate_json(data)
                return model.to_conversation()

            return None

        except Exception as e:
            self.logger.error(f"Error loading conversation: {e}")
            return None

    def delete(self, conversation_id: str) -> bool:
        """Delete conversation from Redis."""
        try:
            key = self._make_key(conversation_id)

            # Delete from Redis
            deleted = self.client.delete(key) > 0

            # Remove from index
            self.client.zrem(self._index_key(), conversation_id)

            if deleted:
                self.logger.debug(f"Deleted conversation {conversation_id}")

            return deleted

        except Exception as e:
            self.logger.error(f"Error deleting conversation: {e}")
            return False

    def list_conversations(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ConversationModel]:
        """List conversations from Redis."""
        try:
            # Get conversation IDs from index (sorted by timestamp, newest first)
            conversation_ids = self.client.zrevrange(
                self._index_key(),
                offset,
                offset + (limit or 100) - 1 if limit else -1,
            )

            conversations = []
            for conv_id in conversation_ids:
                key = self._make_key(conv_id)
                data = self.client.get(key)

                if data:
                    model = ConversationModel.model_validate_json(data)
                    conversations.append(model)

            return conversations

        except Exception as e:
            self.logger.error(f"Error listing conversations: {e}")
            return []

    def count(self) -> int:
        """Get total number of conversations."""
        try:
            return self.client.zcard(self._index_key())
        except Exception as e:
            self.logger.error(f"Error counting conversations: {e}")
            return 0

    def clear(self) -> bool:
        """Clear all conversations."""
        try:
            # Get all conversation IDs
            conversation_ids = self.client.zrange(self._index_key(), 0, -1)

            # Delete all conversation keys
            if conversation_ids:
                keys = [self._make_key(conv_id) for conv_id in conversation_ids]
                self.client.delete(*keys)

            # Clear index
            self.client.delete(self._index_key())

            self.logger.info("Cleared all conversations")
            return True

        except Exception as e:
            self.logger.error(f"Error clearing conversations: {e}")
            return False

    def search(self, query: str, limit: int = 10) -> List[ConversationModel]:
        """
        Search conversations (limited in Redis).

        Note: This does a simple scan and filter, not as efficient as SQL.
        For advanced search, consider using PostgreSQL or Elasticsearch.
        """
        try:
            # Get all conversation IDs
            all_ids = self.client.zrevrange(self._index_key(), 0, -1)

            conversations = []
            for conv_id in all_ids:
                if len(conversations) >= limit:
                    break

                key = self._make_key(conv_id)
                data = self.client.get(key)

                if data and query.lower() in data.lower():
                    model = ConversationModel.model_validate_json(data)
                    conversations.append(model)

            return conversations

        except Exception as e:
            self.logger.error(f"Error searching conversations: {e}")
            return []

    def set_ttl(self, conversation_id: str, ttl: int) -> bool:
        """
        Set TTL for a specific conversation.

        Args:
            conversation_id: Conversation ID
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        try:
            key = self._make_key(conversation_id)
            return self.client.expire(key, ttl)
        except Exception as e:
            self.logger.error(f"Error setting TTL: {e}")
            return False
