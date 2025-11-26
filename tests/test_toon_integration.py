import pytest
from unittest.mock import MagicMock, patch
from craft.tools.base import Tool, ToolMetadata, ToolParameter

# Mock function for the tool
def sample_function(name: str, age: int = 30):
    """A sample function."""
    return f"{name} is {age} years old"

@pytest.fixture
def sample_tool():
    metadata = ToolMetadata(
        name="sample_tool",
        description="A sample tool for testing",
        parameters=[
            ToolParameter(name="name", type="str", description="The name"),
            ToolParameter(name="age", type="int", description="The age", required=False, default=30)
        ],
        return_type="str",
        json_schema={
            "type": "function",
            "function": {
                "name": "sample_tool",
                "description": "A sample tool for testing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "The name"},
                        "age": {"type": "integer", "description": "The age", "default": 30}
                    },
                    "required": ["name"]
                }
            }
        }
    )
    return Tool(
        name="sample_tool",
        description="A sample tool for testing",
        func=sample_function,
        metadata=metadata
    )

def test_toon_schema_generation(sample_tool):
    """Test that TOON schema is generated correctly when requested."""
    # We assume TOON is available in the environment for this test
    # If not, we might need to mock TOON_AVAILABLE in craft.tools.base
    
    with patch('craft.tools.base.TOON_AVAILABLE', True):
        schema = sample_tool.to_function_schema(format="toon")
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "sample_tool"
        assert schema["function"]["parameters"]["format"] == "toon"
        
        params = schema["function"]["parameters"]["schema"]
        assert len(params) == 2
        assert params[0]["name"] == "name"
        assert params[0]["type"] == "str"
        assert params[0]["required"] is True
        
        assert params[1]["name"] == "age"
        assert params[1]["type"] == "int"
        assert params[1]["required"] is False
        assert params[1]["default"] == 30

def test_toon_fallback_to_json(sample_tool):
    """Test that it falls back to JSON schema if TOON is not available."""
    with patch('craft.tools.base.TOON_AVAILABLE', False):
        schema = sample_tool.to_function_schema(format="toon")
        
        # Should return the standard JSON schema
        assert schema["function"]["parameters"]["type"] == "object"
        assert "format" not in schema["function"]["parameters"]
        assert "properties" in schema["function"]["parameters"]

def test_default_is_json(sample_tool):
    """Test that default format is JSON."""
    schema = sample_tool.to_function_schema()
    assert schema["function"]["parameters"]["type"] == "object"
