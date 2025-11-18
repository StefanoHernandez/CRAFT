"""Memory management for conversations."""

from typing import Dict, Optional
from craft.core.conversation import Conversation


class Memory:
    """
    Simple in-memory storage for conversations.

    For production, use persistent storage adapters (SQLite, PostgreSQL, etc.)
    """

    def __init__(self) -> None:
        self._conversations: Dict[str, Conversation] = {}

    def save(self, conversation: Conversation) -> None:
        """
        Save a conversation.

        Args:
            conversation: Conversation to save
        """
        self._conversations[conversation.id] = conversation

    def load(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation if found, None otherwise
        """
        return self._conversations.get(conversation_id)

    def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    def list_conversations(self) -> list[str]:
        """List all conversation IDs."""
        return list(self._conversations.keys())

    def clear(self) -> None:
        """Clear all conversations."""
        self._conversations.clear()

    def __len__(self) -> int:
        return len(self._conversations)
