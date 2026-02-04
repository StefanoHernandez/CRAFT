"""SQLite storage adapter for conversation persistence."""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from craft.core.conversation import Conversation
from craft.storage.base import StorageAdapter, ConversationModel

class SQLiteStorage(StorageAdapter):
    """
    SQLite storage adapter.
    
    Stores conversations in a local SQLite database file.
    """
    
    def __init__(self, db_path: str = "craft.db", database_path: Optional[str] = None):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database file
            database_path: Alias for db_path (backward compatibility)
        """
        if database_path is not None:
            db_path = database_path
        self.db_path = db_path
        self.database_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    messages TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
    def save(self, conversation: Conversation) -> bool:
        """Save a conversation."""
        model = ConversationModel.from_conversation(conversation)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO conversations 
                    (id, messages, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        model.id,
                        json.dumps(model.messages), # Already serialized dicts
                        json.dumps(model.metadata),
                        model.created_at.isoformat(),
                        model.updated_at.isoformat()
                    )
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
            
    def load(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id, messages, metadata, created_at, updated_at FROM conversations WHERE id = ?",
                    (conversation_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                    
                id, messages_json, metadata_json, created_at, updated_at = row
                
                # Reconstruct model data
                model_data = {
                    "id": id,
                    "messages": json.loads(messages_json),
                    "metadata": json.loads(metadata_json) if metadata_json else {},
                    "created_at": datetime.fromisoformat(created_at),
                    "updated_at": datetime.fromisoformat(updated_at)
                }
                
                model = ConversationModel(**model_data)
                return model.to_conversation()
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return None
            
    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM conversations WHERE id = ?",
                    (conversation_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False
            
    def list_conversations(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ConversationModel]:
        """List conversations."""
        query = "SELECT id, messages, metadata, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        params = []
        
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                models = []
                for row in rows:
                    id, messages_json, metadata_json, created_at, updated_at = row
                    model_data = {
                        "id": id,
                        "messages": json.loads(messages_json), # Load messages to satisfy model, though inefficient for list
                        "metadata": json.loads(metadata_json) if metadata_json else {},
                        "created_at": datetime.fromisoformat(created_at),
                        "updated_at": datetime.fromisoformat(updated_at)
                    }
                    models.append(ConversationModel(**model_data))
                return models
        except Exception as e:
            print(f"Error listing conversations: {e}")
            return []
            
    def count(self) -> int:
        """Get total number of conversations."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM conversations")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error counting conversations: {e}")
            return 0
            
    def clear(self) -> bool:
        """Clear all conversations."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM conversations")
            return True
        except Exception as e:
            print(f"Error clearing conversations: {e}")
            return False
            
    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> List[ConversationModel]:
        """Search conversations by content."""
        # Simple LIKE search on messages JSON string
        sql_query = """
            SELECT id, messages, metadata, created_at, updated_at 
            FROM conversations 
            WHERE messages LIKE ? 
            ORDER BY updated_at DESC 
            LIMIT ?
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(sql_query, (f"%{query}%", limit))
                rows = cursor.fetchall()
                
                models = []
                for row in rows:
                    id, messages_json, metadata_json, created_at, updated_at = row
                    model_data = {
                        "id": id,
                        "messages": json.loads(messages_json),
                        "metadata": json.loads(metadata_json) if metadata_json else {},
                        "created_at": datetime.fromisoformat(created_at),
                        "updated_at": datetime.fromisoformat(updated_at)
                    }
                    models.append(ConversationModel(**model_data))
                return models
        except Exception as e:
            print(f"Error searching conversations: {e}")
            return []
