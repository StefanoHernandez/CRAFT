"""Property tests for tool choice validation."""

import pytest
from hypothesis import given, strategies as st
from craft.utils.validation import validate_tool_choice
from craft.tools.base import Tool, ToolMetadata, ToolParameter

def create_mock_tool(name):
    return Tool(
        name=name,
        description=f"Mock tool {name}",
        func=lambda x: x,
        metadata=ToolMetadata(
            name=name,
            description=f"Mock tool {name}",
            parameters=[ToolParameter(name="arg", type="str")],
            return_type="str",
            json_schema={"type": "function", "function": {"name": name}}
        )
    )

TOOLS = [create_mock_tool(f"tool_{i}") for i in range(5)]
TOOL_NAMES = [t.name for t in TOOLS]

@given(st.sampled_from(["auto", "none", "required", "required_first"]))
def test_valid_modes(mode):
    """Test that valid modes are accepted."""
    validate_tool_choice(mode, TOOLS)

@given(st.sampled_from(TOOL_NAMES))
def test_valid_tool_names(name):
    """Test that existing tool names are accepted."""
    validate_tool_choice(name, TOOLS)

@given(st.lists(st.sampled_from(TOOL_NAMES), min_size=1))
def test_valid_tool_lists(names):
    """Test that lists of existing tool names are accepted."""
    validate_tool_choice(names, TOOLS)

@given(st.text())
def test_invalid_strings(s):
    """Test that invalid strings raise ValueError."""
    if s in ["auto", "none", "required", "required_first"] or s in TOOL_NAMES:
        return
    
    with pytest.raises(ValueError):
        validate_tool_choice(s, TOOLS)

@given(st.lists(st.text(), min_size=1))
def test_invalid_lists(names):
    """Test that lists with invalid tool names raise ValueError."""
    # Ensure at least one name is invalid
    if all(n in TOOL_NAMES for n in names):
        return
        
    with pytest.raises(ValueError):
        validate_tool_choice(names, TOOLS)
