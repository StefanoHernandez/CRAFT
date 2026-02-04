"""Memory management for conversations."""

from typing import Dict, Optional, TYPE_CHECKING, Any, List
from craft.core.conversation import Conversation
from craft.providers.base import Role

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
        max_tokens: Optional[int] = None,
    ) -> None:
        """
        Initialize memory.

        Args:
            storage: Optional storage adapter for persistence.
                     If None, uses in-memory storage.
            max_messages: Optional limit on conversation messages.
                         Older messages are trimmed when limit is reached.
            max_tokens: Optional limit on total tokens in conversation.
        """
        self.storage = storage
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self._conversations: Dict[str, Conversation] = {}

    def trim_messages(self, messages: List[Any]) -> List[Any]:
        """
        Trim messages to fit within limits.

        Args:
            messages: List of messages to trim

        Returns:
            Trimmed list of messages
        """
        if not messages:
            return messages

        # Always keep system prompt if present (usually first message)
        system_msg = None
        if messages[0].role in (Role.SYSTEM, Role.SYSTEM.value):
            system_msg = messages[0]
            messages_to_trim = messages[1:]
        else:
            messages_to_trim = messages

        # Trim by count
        if self.max_messages and len(messages_to_trim) > self.max_messages:
            messages_to_trim = messages_to_trim[-self.max_messages :]

        # Trim by tokens with improved heuristic
        # Average English word is 4.7 characters, plus space = ~5.7
        # LLM tokens are typically ~0.75 words. 
        # So 1 token ~= 4 characters is a decent floor, but 1 token ~= 3.5 is safer.
        if self.max_tokens:
            def estimate_tokens(text: str) -> int:
                # Better heuristic: max(chars/3.5, words/0.75)
                # This accounts for both long words and many short words
                char_count = len(text)
                word_count = len(text.split())
                return int(max(char_count / 3.5, word_count / 0.75))

            current_tokens = sum(estimate_tokens(m.content) for m in messages_to_trim)
            
            while current_tokens > self.max_tokens and messages_to_trim:
                removed = messages_to_trim.pop(0)
                current_tokens -= estimate_tokens(removed.content)

        # Reconstruct
        if system_msg:
            return [system_msg] + messages_to_trim
        return messages_to_trim

    def save(self, conversation: Conversation) -> bool:
        """
        Save a conversation.

        Args:
            conversation: Conversation to save

        Returns:
            True if saved successfully
        """
        # Trim messages if needed
        conversation.messages = self.trim_messages(conversation.messages)

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

    def __bool__(self) -> bool:
        """Always return True for Memory instance."""
        return True

    def __repr__(self) -> str:
        backend = self.storage.name if self.storage else "in-memory"
        return f"Memory(backend={backend}, conversations={self.count()})"
