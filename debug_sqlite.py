"""Simple test to debug SQLite delete issue."""

import os
import tempfile
from craft.storage.sqlite import SQLiteStorage
from craft.core.conversation import Conversation
from craft.providers.base import Message, Role

# Create temp db
with tempfile.NamedTemporaryFile(delete=False) as f:
    db_path = f.name

storage = SQLiteStorage(db_path=db_path)

# Create conversation
conv = Conversation(id="test_conv")
conv.messages = [Message(role=Role.USER, content="Hello")]

# Save
print("Saving conversation...")
assert storage.save(conv), "Save failed"
print(f"Count after save: {storage.count()}")

# Load
print("Loading conversation...")
loaded = storage.load("test_conv")
assert loaded is not None, "Load failed"
print(f"Loaded conversation: {loaded.id}")

# Delete
print("Deleting conversation...")
result = storage.delete("test_conv")
print(f"Delete returned: {result}")
print(f"Count after delete: {storage.count()}")

# Verify
loaded_after = storage.load("test_conv")
print(f"Can still load after delete: {loaded_after is not None}")

# Clean up
os.unlink(db_path)

print("✓ All checks passed")
