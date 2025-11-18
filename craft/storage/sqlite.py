"""SQLite storage adapter."""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from craft.storage.base import StorageAdapter, ConversationModel
from craft.core.conversation import Conversation
from craft.utils.logging import get_logger


class SQLiteStorage(StorageAdapter):
    """
    SQLite storage adapter for conversations.

    Perfect for development and small-scale applications.
    """

    def __init__(self, database_path: str = "./craft_conversations.db"):
        """
        Initialize SQLite storage.

        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.logger = get_logger("craft.storage.sqlite")

        # Create database and tables
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database and create tables."""
        # Ensure directory exists
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Create conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                messages TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create index for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_updated_at
            ON conversations(updated_at DESC)
        """)

        conn.commit()
        conn.close()

        self.logger.info(f"SQLite database initialized at {self.database_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.database_path)

    def save(self, conversation: Conversation) -> bool:
        """Save conversation to SQLite."""
        try:
            model = ConversationModel.from_conversation(conversation)

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO conversations
                (id, messages, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                model.id,
                json.dumps([msg.model_dump() for msg in conversation.messages]),
                json.dumps(model.metadata),
                model.created_at.isoformat(),
                model.updated_at.isoformat(),
            ))

            conn.commit()
            conn.close()

            self.logger.debug(f"Saved conversation {conversation.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving conversation: {e}")
            return False

    def load(self, conversation_id: str) -> Optional[Conversation]:
        """Load conversation from SQLite."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, messages, metadata, created_at, updated_at
                FROM conversations
                WHERE id = ?
            """, (conversation_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                model = ConversationModel(
                    id=row[0],
                    messages=json.loads(row[1]),
                    metadata=json.loads(row[2]),
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                )
                return model.to_conversation()

            return None

        except Exception as e:
            self.logger.error(f"Error loading conversation: {e}")
            return None

    def delete(self, conversation_id: str) -> bool:
        """Delete conversation from SQLite."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM conversations WHERE id = ?
            """, (conversation_id,))

            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()

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
        """List conversations from SQLite."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT id, messages, metadata, created_at, updated_at
                FROM conversations
                ORDER BY updated_at DESC
            """

            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            conversations = []
            for row in rows:
                model = ConversationModel(
                    id=row[0],
                    messages=json.loads(row[1]),
                    metadata=json.loads(row[2]),
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                )
                conversations.append(model)

            return conversations

        except Exception as e:
            self.logger.error(f"Error listing conversations: {e}")
            return []

    def count(self) -> int:
        """Get total number of conversations."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM conversations")
            count = cursor.fetchone()[0]

            conn.close()
            return count

        except Exception as e:
            self.logger.error(f"Error counting conversations: {e}")
            return 0

    def clear(self) -> bool:
        """Clear all conversations."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM conversations")
            conn.commit()
            conn.close()

            self.logger.info("Cleared all conversations")
            return True

        except Exception as e:
            self.logger.error(f"Error clearing conversations: {e}")
            return False

    def search(self, query: str, limit: int = 10) -> List[ConversationModel]:
        """Search conversations by content."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Simple text search in messages
            cursor.execute("""
                SELECT id, messages, metadata, created_at, updated_at
                FROM conversations
                WHERE messages LIKE ?
                ORDER BY updated_at DESC
                LIMIT ?
            """, (f"%{query}%", limit))

            rows = cursor.fetchall()
            conn.close()

            conversations = []
            for row in rows:
                model = ConversationModel(
                    id=row[0],
                    messages=json.loads(row[1]),
                    metadata=json.loads(row[2]),
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                )
                conversations.append(model)

            return conversations

        except Exception as e:
            self.logger.error(f"Error searching conversations: {e}")
            return []
