"""Tests for storage adapters."""

import pytest
import os
import json
from datetime import datetime
from craft.storage.sqlite import SQLiteStorage
from craft.storage.json_file import JSONFileStorage
from craft.core.conversation import Conversation
from craft.providers.base import Message, Role

@pytest.fixture
def conversation():
    conv = Conversation(id="test_conv")
    conv.messages = [
        Message(role=Role.USER, content="Hello"),
        Message(role=Role.ASSISTANT, content="Hi there")
    ]
    conv.metadata = {"key": "value"}
    return conv

def test_sqlite_storage(tmp_path, conversation):
    """Test SQLite storage adapter."""
    db_path = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path=db_path)
    
    # Save
    assert storage.save(conversation)
    assert storage.count() == 1
    
    # Load
    loaded = storage.load("test_conv")
    assert loaded is not None
    assert loaded.id == conversation.id
    assert len(loaded.messages) == 2
    assert loaded.messages[0].content == "Hello"
    assert loaded.metadata == {"key": "value"}
    
    # List
    conversations = storage.list_conversations()
    assert len(conversations) == 1
    assert conversations[0].id == "test_conv"
    
    # Search
    results = storage.search("Hello")
    assert len(results) == 1
    assert results[0].id == "test_conv"
    
    # Delete
    assert storage.delete("test_conv")
    assert storage.count() == 0
    assert storage.load("test_conv") is None

def test_json_storage(tmp_path, conversation):
    """Test JSON file storage adapter."""
    file_path = str(tmp_path / "test.json")
    storage = JSONFileStorage(file_path=file_path)
    
    # Save
    assert storage.save(conversation)
    assert storage.count() == 1
    
    # Verify file content
    with open(file_path, "r") as f:
        data = json.load(f)
        assert "test_conv" in data
        
    # Load
    loaded = storage.load("test_conv")
    assert loaded is not None
    assert loaded.id == conversation.id
    assert len(loaded.messages) == 2
    
    # Delete
    assert storage.delete("test_conv")
    assert storage.count() == 0
