"""Tool decorator for registering functions as tools with MCP integration."""

from typing import Callable, Optional, Any, Dict, get_type_hints
from inspect import signature, Parameter
import functools

from craft.tools.base import Tool, ToolParameter, ToolMetadata
from craft.mcp.registry import ToolRegistry as MCPToolRegistry

# Global registry instance for auto-registration
_global_registry: Optional[MCPToolRegistry] = None


def set_global_registry(registry: MCPToolRegistry) -> None:
    """Set the global tool registry for auto-registration."""
    global _global_registry
    _global_registry = registry


def get_global_registry() -> Optional[MCPToolRegistry]:
    """Get the global tool registry."""
    return _global_registry


def _python_type_to_json_type(python_type: Any) -> str:
    """Convert Python type to JSON schema type."""
    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    # Handle string representations
    if isinstance(python_type, str):
        python_type_lower = python_type.lower()
        if "str" in python_type_lower:
            return "string"
        elif "int" in python_type_lower:
            return "integer"
        elif "float" in python_type_lower:
            return "number"
        elif "bool" in python_type_lower:
            return "boolean"
        elif "list" in python_type_lower:
            return "array"
        elif "dict" in python_type_lower:
            return "object"

    # Handle actual types
    return type_mapping.get(python_type, "string")


def _generate_json_schema(func: Callable, tool_name: str, tool_desc: str) -> Dict[str, Any]:
    """Generate JSON schema from function signature."""
    sig = signature(func)
    type_hints = {}
    
    try:
        type_hints = get_type_hints(func)
    except Exception:
        # If type hints fail, we'll infer from annotations
        pass

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        # Get type from hints or annotation
        param_type = type_hints.get(param_name, param.annotation)
        
        if param_type == Parameter.empty:
            param_type = str  # Default to string if no type hint

        json_type = _python_type_to_json_type(param_type)

        properties[param_name] = {
            "type": json_type,
            "description": f"Parameter {param_name}"
        }

        if param.default == Parameter.empty:
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_desc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    auto_register: bool = True
) -> Callable:
    """
    Decorator to register a function as a tool with MCP integration.

    Automatically extracts metadata from the function signature including:
    - Function name (or custom name)
    - Docstring as description
    - Parameter names, types, and defaults
    - Return type
    - JSON schema for LLM providers

    The decorated function is automatically registered with the global MCP registry
    if auto_register=True and a global registry has been set.

    Example:
        @tool
        def search_web(query: str, max_results: int = 5) -> List[str]:
            '''Search the web for information.'''
            return search_results

        @tool(name="custom_search", description="Custom search tool")
        def my_search(query: str) -> str:
            return results

    Args:
        name: Optional custom name for the tool (defaults to function name)
        description: Optional custom description (defaults to docstring)
        auto_register: Whether to auto-register with global MCP registry (default: True)

    Returns:
        Decorated function as a Tool instance
    """
    # Handle both @tool and @tool() syntax
    if callable(name):
        # Called as @tool without parentheses
        func = name
        return _create_tool(func, None, description, auto_register)
    
    # Called as @tool() or @tool(name="...", description="...")
    def decorator(func: Callable) -> Tool:
        return _create_tool(func, name, description, auto_register)
    
    return decorator


def _create_tool(
    func: Callable,
    name: Optional[str],
    description: Optional[str],
    auto_register: bool
) -> Tool:
    """Internal function to create a Tool instance from a function."""
    # Extract tool name
    tool_name = name or func.__name__

    # Extract description from docstring or use provided description
    tool_desc = description or (func.__doc__ or "").strip() or f"Tool: {tool_name}"

    # Get function signature
    sig = signature(func)
    type_hints = {}
    
    try:
        type_hints = get_type_hints(func)
    except Exception:
        pass

    # Extract parameters
    parameters = []
    for param_name, param in sig.parameters.items():
        # Get type from hints or annotation
        param_type = type_hints.get(param_name, param.annotation)
        
        if param_type == Parameter.empty:
            param_type = str

        param_type_str = str(param_type).replace("<class '", "").replace("'>", "")

        # Extract parameter description from docstring if available
        param_desc = f"Parameter {param_name}"

        parameters.append(
            ToolParameter(
                name=param_name,
                type=param_type_str,
                description=param_desc,
                required=param.default == Parameter.empty,
                default=param.default if param.default != Parameter.empty else None
            )
        )

    # Get return type
    return_type = type_hints.get("return", sig.return_annotation)
    if return_type == Parameter.empty:
        return_type = Any
    return_type_str = str(return_type).replace("<class '", "").replace("'>", "")

    # Generate JSON schema
    json_schema = _generate_json_schema(func, tool_name, tool_desc)

    # Create metadata
    metadata = ToolMetadata(
        name=tool_name,
        description=tool_desc,
        parameters=parameters,
        return_type=return_type_str,
        json_schema=json_schema
    )

    # Create Tool instance
    tool_instance = Tool(
        name=tool_name,
        description=tool_desc,
        func=func,
        metadata=metadata
    )

    # Auto-register with global MCP registry if available
    if auto_register and _global_registry is not None:
        _global_registry.register_custom_tool(
            name=tool_name,
            func=func,
            description=tool_desc,
            parameters=json_schema["function"]["parameters"]
        )

    return tool_instance
