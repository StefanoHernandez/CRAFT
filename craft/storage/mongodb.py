"""MongoDB storage adapter."""

from typing import List, Optional
from datetime import datetime

try:
    from pymongo import MongoClient, DESCENDING
    from pymongo.errors import PyMongoError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

from craft.storage.base import StorageAdapter, ConversationModel
from craft.core.conversation import Conversation
from craft.utils.logging import get_logger


class MongoDBStorage(StorageAdapter):
    """
    MongoDB storage adapter for conversations.

    NoSQL storage with flexible schema and powerful querying.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 27017,
        database: str = "craft",
        collection: str = "conversations",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize MongoDB storage.

        Args:
            host: MongoDB host
            port: MongoDB port
            database: Database name
            collection: Collection name
            username: Optional username
            password: Optional password
            **kwargs: Additional MongoClient parameters
        """
        if not PYMONGO_AVAILABLE:
            raise ImportError(
                "pymongo not installed. "
                "Install with: pip install 'craft-chatbot[storage]'"
            )

        self.logger = get_logger("craft.storage.mongodb")

        # Build connection string
        if username and password:
            connection_string = f"mongodb://{username}:{password}@{host}:{port}/"
        else:
            connection_string = f"mongodb://{host}:{port}/"

        # Connect to MongoDB
        self.client = MongoClient(connection_string, **kwargs)
        self.db = self.client[database]
        self.collection = self.db[collection]

        # Create indexes
        self._init_indexes()

        self.logger.info(f"Connected to MongoDB at {host}:{port}/{database}")

    def _init_indexes(self) -> None:
        """Create indexes for better performance."""
        # Index on id (unique)
        self.collection.create_index("id", unique=True)

        # Index on updated_at for sorting
        self.collection.create_index([("updated_at", DESCENDING)])

        # Text index for search
        self.collection.create_index([("messages.content", "text")])

    def save(self, conversation: Conversation) -> bool:
        """Save conversation to MongoDB."""
        try:
            model = ConversationModel.from_conversation(conversation)

            # Convert to dict for MongoDB
            doc = {
                "id": model.id,
                "messages": model.messages,
                "metadata": model.metadata,
                "created_at": model.created_at,
                "updated_at": model.updated_at,
            }

            # Upsert (insert or update)
            self.collection.update_one(
                {"id": model.id},
                {"$set": doc},
                upsert=True,
            )

            self.logger.debug(f"Saved conversation {conversation.id}")
            return True

        except PyMongoError as e:
            self.logger.error(f"Error saving conversation: {e}")
            return False

    def load(self, conversation_id: str) -> Optional[Conversation]:
        """Load conversation from MongoDB."""
        try:
            doc = self.collection.find_one({"id": conversation_id})

            if doc:
                # Remove MongoDB's _id field
                doc.pop("_id", None)

                model = ConversationModel(**doc)
                return model.to_conversation()

            return None

        except PyMongoError as e:
            self.logger.error(f"Error loading conversation: {e}")
            return None

    def delete(self, conversation_id: str) -> bool:
        """Delete conversation from MongoDB."""
        try:
            result = self.collection.delete_one({"id": conversation_id})
            deleted = result.deleted_count > 0

            if deleted:
                self.logger.debug(f"Deleted conversation {conversation_id}")

            return deleted

        except PyMongoError as e:
            self.logger.error(f"Error deleting conversation: {e}")
            return False

    def list_conversations(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ConversationModel]:
        """List conversations from MongoDB."""
        try:
            cursor = (
                self.collection.find()
                .sort("updated_at", DESCENDING)
                .skip(offset)
                .limit(limit or 100)
            )

            conversations = []
            for doc in cursor:
                # Remove MongoDB's _id field
                doc.pop("_id", None)

                model = ConversationModel(**doc)
                conversations.append(model)

            return conversations

        except PyMongoError as e:
            self.logger.error(f"Error listing conversations: {e}")
            return []

    def count(self) -> int:
        """Get total number of conversations."""
        try:
            return self.collection.count_documents({})
        except PyMongoError as e:
            self.logger.error(f"Error counting conversations: {e}")
            return 0

    def clear(self) -> bool:
        """Clear all conversations."""
        try:
            self.collection.delete_many({})
            self.logger.info("Cleared all conversations")
            return True

        except PyMongoError as e:
            self.logger.error(f"Error clearing conversations: {e}")
            return False

    def search(self, query: str, limit: int = 10) -> List[ConversationModel]:
        """Search conversations using MongoDB text search."""
        try:
            # Use text search
            cursor = (
                self.collection.find(
                    {"$text": {"$search": query}},
                    {"score": {"$meta": "textScore"}},
                )
                .sort([("score", {"$meta": "textScore"})])
                .limit(limit)
            )

            conversations = []
            for doc in cursor:
                # Remove MongoDB fields
                doc.pop("_id", None)
                doc.pop("score", None)

                model = ConversationModel(**doc)
                conversations.append(model)

            return conversations

        except PyMongoError as e:
            self.logger.error(f"Error searching conversations: {e}")
            return []

    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.logger.info("Closed MongoDB connection")
