"""Base storage interface for conversation persistence."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from craft.core.conversation import Conversation


class ConversationModel(BaseModel):
    """Model for stored conversations."""

    id: str
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_conversation(cls, conversation: Conversation) -> "ConversationModel":
        """Create model from Conversation object."""
        return cls(
            id=conversation.id,
            messages=[msg.model_dump() for msg in conversation.messages],
            metadata=conversation.metadata,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    def to_conversation(self) -> Conversation:
        """Convert model back to Conversation object."""
        from craft.providers.base import Message, Role

        conversation = Conversation(
            id=self.id,
            messages=[],
            metadata=self.metadata,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

        # Reconstruct messages
        for msg_data in self.messages:
            message = Message(
                role=Role(msg_data["role"]),
                content=msg_data["content"],
                metadata=msg_data.get("metadata", {}),
            )
            conversation.messages.append(message)

        return conversation


class StorageAdapter(ABC):
    """
    Abstract base class for storage adapters.

    All storage implementations must inherit from this class.
    """

    @abstractmethod
    def save(self, conversation: Conversation) -> bool:
        """
        Save a conversation.

        Args:
            conversation: Conversation to save

        Returns:
            True if saved successfully
        """
        pass

    @abstractmethod
    def load(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation if found, None otherwise
        """
        pass

    @abstractmethod
    def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def list_conversations(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ConversationModel]:
        """
        List conversations.

        Args:
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            List of conversation models
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get total number of conversations.

        Returns:
            Count of conversations
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all conversations.

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> List[ConversationModel]:
        """
        Search conversations by content.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching conversations
        """
        pass

    def export_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a conversation to dictionary.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation data as dict
        """
        conversation = self.load(conversation_id)
        if conversation:
            model = ConversationModel.from_conversation(conversation)
            return model.model_dump()
        return None

    def import_conversation(self, data: Dict[str, Any]) -> bool:
        """
        Import a conversation from dictionary.

        Args:
            data: Conversation data

        Returns:
            True if imported successfully
        """
        try:
            model = ConversationModel(**data)
            conversation = model.to_conversation()
            return self.save(conversation)
        except Exception:
            return False

    @property
    def name(self) -> str:
        """Get storage adapter name."""
        return self.__class__.__name__.replace("Storage", "").lower()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(conversations={self.count()})"
