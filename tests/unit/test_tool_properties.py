"""Property-based tests for the tool system.

These tests verify correctness properties using hypothesis for property-based testing.
Each test runs a minimum of 100 iterations to ensure properties hold across diverse inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings
from typing import Any, Dict, List, Optional
from inspect import Parameter

from craft.tools.decorator import tool
from craft.tools.base import Tool, ToolParameter, ToolMetadata
from craft.mcp.registry import ToolRegistry
from craft.core.errors import ToolExecutionError, ToolValidationError


# Custom strategies for generating test data
@st.composite
def valid_python_identifiers(draw):
    """Generate valid Python identifiers for function/parameter names."""
    first_char = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz_"))
    rest = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", max_size=10))
    return first_char + rest


@st.composite
def function_parameters(draw):
    """Generate valid function parameters with types."""
    param_count = draw(st.integers(min_value=0, max_value=5))
    params = []
    used_names = set()
    
    for i in range(param_count):
        # Generate unique parameter names
        name = draw(valid_python_identifiers())
        # Ensure uniqueness by appending index if needed
        while name in used_names:
            name = f"{name}{i}"
        used_names.add(name)
        
        param_type = draw(st.sampled_from([str, int, float, bool, list, dict]))
        required = draw(st.booleans())
        default = None if required else draw(st.one_of(
            st.none(),
            st.integers(),
            st.text(max_size=10),
            st.booleans()
        ))
        
        params.append({
            "name": name,
            "type": param_type,
            "required": required,
            "default": default
        })
    
    return params


@st.composite
def tool_functions(draw):
    """Generate valid tool functions dynamically."""
    func_name = draw(valid_python_identifiers())
    # Use simple docstring without special characters that could break the code
    docstring = "Test function"
    params = draw(function_parameters())
    
    # Build function signature
    param_strs = []
    for p in params:
        type_name = p["type"].__name__
        if p["required"]:
            param_strs.append(f"{p['name']}: {type_name}")
        else:
            default_repr = repr(p["default"])
            param_strs.append(f"{p['name']}: {type_name} = {default_repr}")
    
    signature = ", ".join(param_strs)
    
    # Create function dynamically
    func_code = f"""def {func_name}({signature}):
    '''{docstring}'''
    return "result"
"""
    
    namespace = {}
    exec(func_code, namespace)
    func = namespace[func_name]
    
    return func, params


# Feature: craft-v2-agents-tools, Property 1: Tool Registration Completeness
@settings(max_examples=100)
@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20).filter(
        lambda x: x[0] != '_' or len(x) > 1  # Valid Python identifier
    ),
    st.integers(min_value=0, max_value=3)  # Number of parameters
)
def test_property_1_tool_registration_completeness(func_name, param_count):
    """
    Property 1: Tool Registration Completeness
    
    For any valid Python function decorated with @tool, the tool registry SHALL contain
    an entry with complete metadata including name, description, and parameter schema.
    
    **Validates: Requirements 1.1, 1.2**
    """
    # Create a simple function with the given name and parameter count
    params = [f"param{i}: str" for i in range(param_count)]
    signature = ", ".join(params)
    
    func_code = f"""def {func_name}({signature}):
    '''Test function {func_name}'''
    return "result"
"""
    
    namespace = {}
    try:
        exec(func_code, namespace)
        func = namespace[func_name]
    except SyntaxError:
        # Skip invalid function names
        return
    
    # Create a registry for this test
    registry = ToolRegistry()
    
    # Decorate the function
    tool_instance = tool(func)
    
    # Manually register since we're not using global registry
    registry.register_custom_tool(
        name=tool_instance.name,
        func=tool_instance.func,
        description=tool_instance.description,
        parameters=tool_instance.metadata.json_schema["function"]["parameters"]
    )
    
    # Verify tool is in registry
    registered_tool = registry.get_tool(tool_instance.name)
    assert registered_tool is not None, f"Tool {tool_instance.name} not found in registry"
    
    # Verify complete metadata
    assert tool_instance.metadata is not None, "Tool metadata is None"
    assert tool_instance.metadata.name == func.__name__, "Tool name doesn't match function name"
    assert tool_instance.metadata.description is not None, "Tool description is None"
    assert tool_instance.metadata.parameters is not None, "Tool parameters is None"
    assert tool_instance.metadata.json_schema is not None, "Tool JSON schema is None"
    
    # Verify parameter count matches
    assert len(tool_instance.metadata.parameters) == param_count, \
        f"Parameter count mismatch: expected {param_count}, got {len(tool_instance.metadata.parameters)}"


# Feature: craft-v2-agents-tools, Property 2: Tool Parameter Validation
@settings(max_examples=100)
@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3),
    st.booleans()
)
def test_property_2_tool_parameter_validation(param_names, should_be_valid):
    """
    Property 2: Tool Parameter Validation
    
    For any registered tool and any input arguments, validation against the tool's JSON schema
    SHALL either succeed with valid parameters or fail with specific validation errors.
    
    **Validates: Requirements 1.3, 15.5**
    """
    # Create a simple tool with known parameters
    @tool
    def test_func(arg1: str, arg2: int = 5):
        """Test function."""
        return "result"
    
    if should_be_valid:
        # Provide valid arguments
        args = {"arg1": "test_value", "arg2": 10}
        validated = test_func.validate_args(**args)
        assert "arg1" in validated
        assert validated["arg1"] == "test_value"
        assert "arg2" in validated
        assert validated["arg2"] == 10
    else:
        # Provide invalid arguments (wrong types or missing required)
        invalid_args = {name: 123 for name in param_names if name != "arg1"}
        
        if "arg1" not in invalid_args:
            # Missing required parameter
            with pytest.raises(ValueError) as exc_info:
                test_func.validate_args(**invalid_args)
            assert "Missing required parameter" in str(exc_info.value)
        else:
            # Has arg1 but might have unexpected parameters
            try:
                validated = test_func.validate_args(**invalid_args)
                # If validation succeeds, arg1 must be present
                assert "arg1" in validated
            except ValueError as e:
                # Validation failed with specific error
                assert "Validation errors" in str(e) or "Unexpected parameter" in str(e)


# Feature: craft-v2-agents-tools, Property 3: Tool Error Capture
@settings(max_examples=100)
@given(st.text(min_size=1, max_size=50))
def test_property_3_tool_error_capture(error_message):
    """
    Property 3: Tool Error Capture
    
    For any tool execution that raises an exception, the system SHALL capture the exception
    details and make them available to the calling agent.
    
    **Validates: Requirements 1.4**
    """
    # Create a tool that always fails
    @tool
    def failing_tool(input_val: str):
        """Tool that always raises an exception."""
        raise ValueError(error_message)
    
    # Execute the tool and verify error is captured
    with pytest.raises(ToolExecutionError) as exc_info:
        failing_tool(input_val="test")
    
    # Verify error details are captured
    error = exc_info.value
    assert error.tool_name == "failing_tool"
    assert error.message is not None
    assert error.details is not None
    assert "stack_trace" in error.details
    assert "arguments" in error.details
    assert error.original_exception is not None
    assert isinstance(error.original_exception, ValueError)
    assert str(error.original_exception) == error_message


# Feature: craft-v2-agents-tools, Property 4: Tool Registry Completeness
@settings(max_examples=100)
@given(st.integers(min_value=1, max_value=10))
def test_property_4_tool_registry_completeness(tool_count):
    """
    Property 4: Tool Registry Completeness
    
    For any set of registered tools, querying the registry SHALL return all tools with
    their complete descriptions and parameters.
    
    **Validates: Requirements 1.5**
    """
    registry = ToolRegistry()
    
    # Register multiple tools with unique names
    tool_names = [f"test_tool_{i}" for i in range(tool_count)]
    registered_tools = []
    
    for name in tool_names:
        # Create a simple function
        func_code = f"""def {name}(arg: str):
    '''Tool {name}'''
    return 'result'
"""
        namespace = {}
        exec(func_code, namespace)
        func = namespace[name]
        
        # Decorate and register
        tool_instance = tool(func)
        registry.register_custom_tool(
            name=tool_instance.name,
            func=tool_instance.func,
            description=tool_instance.description,
            parameters=tool_instance.metadata.json_schema["function"]["parameters"]
        )
        registered_tools.append(tool_instance)
    
    # Query registry
    all_tools = registry.list_tools()
    
    # Verify all tools are present
    assert len(all_tools) == tool_count, \
        f"Expected {tool_count} tools, got {len(all_tools)}"
    
    # Verify each tool has complete information
    tool_names_in_registry = {t.name for t in all_tools}
    for expected_name in tool_names:
        assert expected_name in tool_names_in_registry, \
            f"Tool {expected_name} not found in registry"
    
    # Verify function schemas are available
    schemas = registry.get_function_schemas()
    assert len(schemas) == tool_count, \
        f"Expected {tool_count} schemas, got {len(schemas)}"
    
    # Each schema should have required fields (MCP format)
    for schema in schemas:
        assert "name" in schema, "Schema missing 'name' field"
        assert "description" in schema, "Schema missing 'description' field"


# Additional edge case tests
def test_tool_with_no_parameters():
    """Test tool with no parameters."""
    @tool
    def no_params_tool():
        """Tool with no parameters."""
        return "result"
    
    assert len(no_params_tool.metadata.parameters) == 0
    result = no_params_tool()
    assert result == "result"


def test_tool_with_all_optional_parameters():
    """Test tool with all optional parameters."""
    @tool
    def optional_params_tool(a: str = "default_a", b: int = 42):
        """Tool with optional parameters."""
        return f"{a}_{b}"
    
    # Call with no arguments
    result = optional_params_tool()
    assert result == "default_a_42"
    
    # Call with some arguments
    result = optional_params_tool(a="custom")
    assert result == "custom_42"


def test_tool_validation_with_wrong_types():
    """Test that validation catches type mismatches."""
    @tool
    def typed_tool(text: str, number: int):
        """Tool with typed parameters."""
        return f"{text}_{number}"
    
    # Valid call
    validated = typed_tool.validate_args(text="hello", number=42)
    assert validated == {"text": "hello", "number": 42}
    
    # Invalid type for number (string instead of int)
    with pytest.raises(ValueError) as exc_info:
        typed_tool.validate_args(text="hello", number="not_a_number")
    assert "invalid type" in str(exc_info.value).lower()


def test_tool_execution_with_validation_error():
    """Test that validation errors are properly wrapped."""
    @tool
    def strict_tool(required_param: str):
        """Tool with required parameter."""
        return required_param
    
    # Missing required parameter
    with pytest.raises(ToolValidationError) as exc_info:
        strict_tool()
    
    error = exc_info.value
    assert error.tool_name == "strict_tool"
    assert "validation" in error.message.lower()
