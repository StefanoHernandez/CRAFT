"""PostgreSQL storage adapter."""

import json
from typing import List, Optional
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import Json, RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from craft.storage.base import StorageAdapter, ConversationModel
from craft.core.conversation import Conversation
from craft.utils.logging import get_logger


class PostgreSQLStorage(StorageAdapter):
    """
    PostgreSQL storage adapter for conversations.

    Production-ready with advanced features like full-text search.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "craft",
        user: str = "craft",
        password: str = "craft",
        table_name: str = "conversations",
    ):
        """
        Initialize PostgreSQL storage.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            table_name: Table name for conversations
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "psycopg2 not installed. "
                "Install with: pip install 'craft-chatbot[storage]'"
            )

        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }
        self.table_name = table_name
        self.logger = get_logger("craft.storage.postgresql")

        # Initialize database
        self._init_database()

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.connection_params)

    def _init_database(self) -> None:
        """Initialize database and create tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create conversations table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id TEXT PRIMARY KEY,
                messages JSONB NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)

        # Create indexes
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.table_name}_updated_at
            ON {self.table_name}(updated_at DESC)
        """)

        # Create GIN index for full-text search
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.table_name}_messages_gin
            ON {self.table_name} USING GIN (messages)
        """)

        conn.commit()
        cursor.close()
        conn.close()

        self.logger.info(f"PostgreSQL table '{self.table_name}' initialized")

    def save(self, conversation: Conversation) -> bool:
        """Save conversation to PostgreSQL."""
        try:
            model = ConversationModel.from_conversation(conversation)

            conn = self._get_connection()
            cursor = conn.cursor()

            messages_json = [msg.model_dump() for msg in conversation.messages]

            cursor.execute(f"""
                INSERT INTO {self.table_name}
                (id, messages, metadata, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    messages = EXCLUDED.messages,
                    metadata = EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at
            """, (
                model.id,
                Json(messages_json),
                Json(model.metadata),
                model.created_at,
                model.updated_at,
            ))

            conn.commit()
            cursor.close()
            conn.close()

            self.logger.debug(f"Saved conversation {conversation.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving conversation: {e}")
            return False

    def load(self, conversation_id: str) -> Optional[Conversation]:
        """Load conversation from PostgreSQL."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(f"""
                SELECT id, messages, metadata, created_at, updated_at
                FROM {self.table_name}
                WHERE id = %s
            """, (conversation_id,))

            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row:
                model = ConversationModel(
                    id=row["id"],
                    messages=row["messages"],
                    metadata=row["metadata"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                return model.to_conversation()

            return None

        except Exception as e:
            self.logger.error(f"Error loading conversation: {e}")
            return None

    def delete(self, conversation_id: str) -> bool:
        """Delete conversation from PostgreSQL."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(f"""
                DELETE FROM {self.table_name} WHERE id = %s
            """, (conversation_id,))

            deleted = cursor.rowcount > 0
            conn.commit()
            cursor.close()
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
        """List conversations from PostgreSQL."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = f"""
                SELECT id, messages, metadata, created_at, updated_at
                FROM {self.table_name}
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, (limit or 100, offset))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            conversations = []
            for row in rows:
                model = ConversationModel(
                    id=row["id"],
                    messages=row["messages"],
                    metadata=row["metadata"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
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

            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]

            cursor.close()
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

            cursor.execute(f"DELETE FROM {self.table_name}")
            conn.commit()
            cursor.close()
            conn.close()

            self.logger.info("Cleared all conversations")
            return True

        except Exception as e:
            self.logger.error(f"Error clearing conversations: {e}")
            return False

    def search(self, query: str, limit: int = 10) -> List[ConversationModel]:
        """Search conversations using PostgreSQL full-text search."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Use JSONB containment for search
            cursor.execute(f"""
                SELECT id, messages, metadata, created_at, updated_at
                FROM {self.table_name}
                WHERE messages::text ILIKE %s
                ORDER BY updated_at DESC
                LIMIT %s
            """, (f"%{query}%", limit))

            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            conversations = []
            for row in rows:
                model = ConversationModel(
                    id=row["id"],
                    messages=row["messages"],
                    metadata=row["metadata"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                conversations.append(model)

            return conversations

        except Exception as e:
            self.logger.error(f"Error searching conversations: {e}")
            return []
