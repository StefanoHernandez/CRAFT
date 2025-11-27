"""JSON file storage adapter for conversation persistence."""

import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from craft.core.conversation import Conversation
from craft.storage.base import StorageAdapter, ConversationModel

class JSONFileStorage(StorageAdapter):
    """
    JSON file storage adapter.
    
    Stores conversations in a local JSON file.
    Suitable for development and simple use cases.
    """
    
    def __init__(self, file_path: str = "craft_conversations.json"):
        """
        Initialize JSON file storage.
        
        Args:
            file_path: Path to JSON file
        """
        self.file_path = file_path
        self._ensure_file()
        
    def _ensure_file(self):
        """Ensure JSON file exists."""
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump({}, f)
                
    def _load_data(self) -> Dict[str, Dict[str, Any]]:
        """Load all data from file."""
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
            
    def _save_data(self, data: Dict[str, Dict[str, Any]]):
        """Save all data to file."""
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)
            
    def save(self, conversation: Conversation) -> bool:
        """Save a conversation."""
        model = ConversationModel.from_conversation(conversation)
        data = self._load_data()
        
        # Convert model to dict, handling datetime serialization
        conv_data = model.model_dump()
        conv_data["created_at"] = model.created_at.isoformat()
        conv_data["updated_at"] = model.updated_at.isoformat()
        
        data[model.id] = conv_data
        self._save_data(data)
        return True
            
    def load(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation by ID."""
        data = self._load_data()
        conv_data = data.get(conversation_id)
        
        if not conv_data:
            return None
            
        try:
            # Parse datetime strings
            conv_data["created_at"] = datetime.fromisoformat(conv_data["created_at"])
            conv_data["updated_at"] = datetime.fromisoformat(conv_data["updated_at"])
            
            model = ConversationModel(**conv_data)
            return model.to_conversation()
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return None
            
    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        data = self._load_data()
        if conversation_id in data:
            del data[conversation_id]
            self._save_data(data)
            return True
        return False
            
    def list_conversations(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ConversationModel]:
        """List conversations."""
        data = self._load_data()
        conversations = list(data.values())
        
        # Sort by updated_at desc
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        
        # Apply pagination
        if limit is not None:
            conversations = conversations[offset : offset + limit]
        else:
            conversations = conversations[offset:]
            
        models = []
        for conv_data in conversations:
            try:
                conv_data["created_at"] = datetime.fromisoformat(conv_data["created_at"])
                conv_data["updated_at"] = datetime.fromisoformat(conv_data["updated_at"])
                models.append(ConversationModel(**conv_data))
            except Exception:
                continue
                
        return models
            
    def count(self) -> int:
        """Get total number of conversations."""
        data = self._load_data()
        return len(data)
            
    def clear(self) -> bool:
        """Clear all conversations."""
        self._save_data({})
        return True
            
    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> List[ConversationModel]:
        """Search conversations by content."""
        data = self._load_data()
        results = []
        query_lower = query.lower()
        
        for conv_data in data.values():
            # Search in messages
            messages = conv_data.get("messages", [])
            found = False
            for msg in messages:
                if query_lower in msg.get("content", "").lower():
                    found = True
                    break
            
            if found:
                try:
                    conv_data["created_at"] = datetime.fromisoformat(conv_data["created_at"])
                    conv_data["updated_at"] = datetime.fromisoformat(conv_data["updated_at"])
                    results.append(ConversationModel(**conv_data))
                except Exception:
                    continue
                    
            if len(results) >= limit:
                break
                
        return results
