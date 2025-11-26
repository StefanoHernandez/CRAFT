"""Tests for storage module."""

import pytest
from pathlib import Path

from craft.core.conversation import Conversation, Message
from craft.storage import SQLiteStorage
from craft.storage.base import StorageAdapter, ConversationModel


@pytest.mark.unit
class TestSQLiteStorage:
    """Test SQLite storage adapter."""

    def test_create_storage(self, tmp_path):
        """Test creating SQLite storage."""
        db_path = tmp_path / "test.db"
        storage = SQLiteStorage(database_path=str(db_path))

        assert storage.database_path == str(db_path)
        assert Path(db_path).exists()

    def test_save_conversation(self, temp_sqlite_storage):
        """Test saving a conversation."""
        conv = Conversation()
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi there")

        success = temp_sqlite_storage.save(conv)

        assert success is True

    def test_load_conversation(self, temp_sqlite_storage):
        """Test loading a conversation."""
        # Save first
        conv = Conversation()
        conv.add_user_message("Test message")
        temp_sqlite_storage.save(conv)

        # Load
        loaded = temp_sqlite_storage.load(conv.id)

        assert loaded is not None
        assert loaded.id == conv.id
        assert len(loaded.messages) == 1
        assert loaded.messages[0].content == "Test message"

    def test_load_nonexistent(self, temp_sqlite_storage):
        """Test loading non-existent conversation."""
        loaded = temp_sqlite_storage.load("nonexistent-id")
        assert loaded is None

    def test_delete_conversation(self, temp_sqlite_storage):
        """Test deleting a conversation."""
        conv = Conversation()
        temp_sqlite_storage.save(conv)

        deleted = temp_sqlite_storage.delete(conv.id)
        assert deleted is True

        # Verify it's gone
        loaded = temp_sqlite_storage.load(conv.id)
        assert loaded is None

    def test_list_conversations(self, temp_sqlite_storage):
        """Test listing conversations."""
        # Create multiple conversations
        for i in range(3):
            conv = Conversation()
            conv.add_user_message(f"Message {i}")
            temp_sqlite_storage.save(conv)

        conversations = temp_sqlite_storage.list_conversations()

        assert len(conversations) == 3

    def test_list_with_limit(self, temp_sqlite_storage):
        """Test listing with limit."""
        for i in range(5):
            conv = Conversation()
            temp_sqlite_storage.save(conv)

        conversations = temp_sqlite_storage.list_conversations(limit=3)

        assert len(conversations) == 3

    def test_count(self, temp_sqlite_storage):
        """Test counting conversations."""
        assert temp_sqlite_storage.count() == 0

        for i in range(3):
            conv = Conversation()
            temp_sqlite_storage.save(conv)

        assert temp_sqlite_storage.count() == 3

    def test_clear(self, temp_sqlite_storage):
        """Test clearing all conversations."""
        # Add some conversations
        for i in range(3):
            conv = Conversation()
            temp_sqlite_storage.save(conv)

        assert temp_sqlite_storage.count() == 3

        success = temp_sqlite_storage.clear()
        assert success is True
        assert temp_sqlite_storage.count() == 0

    def test_search(self, temp_sqlite_storage):
        """Test searching conversations."""
        conv1 = Conversation()
        conv1.add_user_message("I love Python programming")
        temp_sqlite_storage.save(conv1)

        conv2 = Conversation()
        conv2.add_user_message("JavaScript is great")
        temp_sqlite_storage.save(conv2)

        results = temp_sqlite_storage.search("Python")

        assert len(results) >= 1
        # First result should contain "Python"
        found_python = any(
            "Python" in msg.content
            for conv in results
            for msg in conv.to_conversation().messages
        )
        assert found_python

    def test_export_conversation(self, temp_sqlite_storage):
        """Test exporting conversation."""
        conv = Conversation()
        conv.add_user_message("Export test")
        temp_sqlite_storage.save(conv)

        exported = temp_sqlite_storage.export_conversation(conv.id)

        assert exported is not None
        assert exported["id"] == conv.id
        assert "messages" in exported
        assert len(exported["messages"]) == 1

    def test_import_conversation(self, temp_sqlite_storage):
        """Test importing conversation."""
        conv = Conversation()
        conv.add_user_message("Import test")

        data = {
            "id": conv.id,
            "messages": [msg.model_dump() for msg in conv.messages],
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
            "metadata": {}
        }

        success = temp_sqlite_storage.import_conversation(data)
        assert success is True

        # Verify it was imported
        loaded = temp_sqlite_storage.load(conv.id)
        assert loaded is not None

    def test_update_conversation(self, temp_sqlite_storage):
        """Test updating an existing conversation."""
        conv = Conversation()
        conv.add_user_message("First message")
        temp_sqlite_storage.save(conv)

        # Add more messages
        conv.add_user_message("Second message")
        temp_sqlite_storage.save(conv)

        # Load and verify
        loaded = temp_sqlite_storage.load(conv.id)
        assert len(loaded.messages) == 2


@pytest.mark.unit
class TestConversationModel:
    """Test ConversationModel."""

    def test_to_conversation(self):
        """Test converting model to conversation."""
        conv = Conversation()
        conv.add_user_message("Test")

        model = ConversationModel(
            id=conv.id,
            messages=[msg.model_dump() for msg in conv.messages],
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            metadata={}
        )

        converted = model.to_conversation()

        assert isinstance(converted, Conversation)
        assert converted.id == conv.id
        assert len(converted.messages) == len(conv.messages)
