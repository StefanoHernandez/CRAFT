"""Conversation management."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
from craft.providers.base import Message, Role


class Conversation(BaseModel):
    """Conversation model to manage chat history."""

    id: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    messages: List[Message] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_message(self, role: Role, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """
        Add a message to the conversation.

        Args:
            role: Message role
            content: Message content
            metadata: Optional metadata

        Returns:
            The created message
        """
        message = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)
        return message

    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add a user message."""
        return self.add_message(Role.USER, content, metadata)

    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add an assistant message."""
        return self.add_message(Role.ASSISTANT, content, metadata)

    def add_system_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add a system message."""
        return self.add_message(Role.SYSTEM, content, metadata)

    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from conversation.

        Args:
            limit: Optional limit on number of messages (most recent)

        Returns:
            List of messages
        """
        if limit is None:
            return self.messages
        return self.messages[-limit:]

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []
        self.updated_at = datetime.now(timezone.utc)

    def __len__(self) -> int:
        return len(self.messages)

    def __str__(self) -> str:
        return f"Conversation(id={self.id}, messages={len(self.messages)})"
