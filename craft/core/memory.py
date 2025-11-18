"""Memory management for conversations."""

from typing import Dict, Optional, TYPE_CHECKING
from craft.core.conversation import Conversation

if TYPE_CHECKING:
    from craft.storage.base import StorageAdapter


class Memory:
    """
    Conversation memory with optional persistent storage.

    By default, conversations are stored in-memory. For production use,
    pass a storage adapter (SQLite, PostgreSQL, Redis, MongoDB) for persistence.

    Examples:
        # In-memory (development)
        memory = Memory()

        # Persistent storage (production)
        from craft.storage import PostgreSQLStorage
        storage = PostgreSQLStorage(...)
        memory = Memory(storage=storage, max_messages=100)
    """

    def __init__(
        self,
        storage: Optional["StorageAdapter"] = None,
        max_messages: Optional[int] = None,
    ) -> None:
        """
        Initialize memory.

        Args:
            storage: Optional storage adapter for persistence.
                     If None, uses in-memory storage.
            max_messages: Optional limit on conversation messages.
                         Older messages are trimmed when limit is reached.
        """
        self.storage = storage
        self.max_messages = max_messages
        self._conversations: Dict[str, Conversation] = {}

    def save(self, conversation: Conversation) -> bool:
        """
        Save a conversation.

        Args:
            conversation: Conversation to save

        Returns:
            True if saved successfully
        """
        # Trim messages if needed
        if self.max_messages and len(conversation.messages) > self.max_messages:
            conversation.messages = conversation.messages[-self.max_messages :]

        if self.storage:
            # Save to persistent storage
            return self.storage.save(conversation)
        else:
            # Save to in-memory storage
            self._conversations[conversation.id] = conversation
            return True

    def load(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation if found, None otherwise
        """
        if self.storage:
            return self.storage.load(conversation_id)
        else:
            return self._conversations.get(conversation_id)

    def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        if self.storage:
            return self.storage.delete(conversation_id)
        else:
            if conversation_id in self._conversations:
                del self._conversations[conversation_id]
                return True
            return False

    def list_conversations(self) -> list[str]:
        """
        List all conversation IDs.

        Returns:
            List of conversation IDs
        """
        if self.storage:
            # Get IDs from storage
            conv_models = self.storage.list_conversations()
            return [conv.id for conv in conv_models]
        else:
            return list(self._conversations.keys())

    def clear(self) -> bool:
        """
        Clear all conversations.

        Returns:
            True if successful
        """
        if self.storage:
            return self.storage.clear()
        else:
            self._conversations.clear()
            return True

    def count(self) -> int:
        """
        Get total number of conversations.

        Returns:
            Count of conversations
        """
        if self.storage:
            return self.storage.count()
        else:
            return len(self._conversations)

    def search(self, query: str, limit: int = 10) -> list[Conversation]:
        """
        Search conversations by content.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching conversations
        """
        if self.storage:
            conv_models = self.storage.search(query, limit)
            return [conv.to_conversation() for conv in conv_models]
        else:
            # Simple in-memory search
            results = []
            query_lower = query.lower()

            for conversation in self._conversations.values():
                for message in conversation.messages:
                    if query_lower in message.content.lower():
                        results.append(conversation)
                        break

                if len(results) >= limit:
                    break

            return results

    @property
    def is_persistent(self) -> bool:
        """Check if memory uses persistent storage."""
        return self.storage is not None

    def __len__(self) -> int:
        return self.count()

    def __repr__(self) -> str:
        backend = self.storage.name if self.storage else "in-memory"
        return f"Memory(backend={backend}, conversations={self.count()})"
