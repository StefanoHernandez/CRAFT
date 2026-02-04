"""
Tool Decorators.

Simplifies tool creation using Python decorators.
Inspired by DataPizza's simple tool definition style.
"""

import inspect
import functools
from typing import Optional, Callable, Dict, Any, List

from craft.tools.base import Tool, ToolMetadata, ToolParameter

def tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator to convert a Python function into a CRAFT Tool.
    
    Usage:
    
    @tool(name="calculator")
    def add(a: int, b: int) -> int:
        "Adds two numbers."
        return a + b
    
    tool_instance = add 
    """
    def decorator(func: Callable) -> Tool:
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or f"Tool {tool_name}"
        
        # Introspect function signature for parameters
        sig = inspect.signature(func)
        parameters = []
        
        type_mapping = {
            int: "integer",
            str: "string",
            bool: "boolean",
            float: "number",
            list: "array",
            dict: "object"
        }
        
        for param_name, param in sig.parameters.items():
            if param_name == "self": 
                continue # Skip self for methods
                
            param_type = "string" # Default
            if param.annotation in type_mapping:
                param_type = type_mapping[param.annotation]
            
            # Check for defaults
            default = None
            required = True
            if param.default != inspect.Parameter.empty:
                default = param.default
                required = False
                
            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                required=required,
                default=default
            ))
            
        # Construct Metadata
        metadata = ToolMetadata(
            name=tool_name,
            description=tool_desc.strip(),
            parameters=parameters,
            return_type="string", # Simplified for now
            json_schema=_generate_json_schema(tool_name, tool_desc, parameters)
        )
        
        # Instantiate Tool
        tool_instance = Tool(
            name=tool_name,
            description=tool_desc.strip(),
            func=func,
            metadata=metadata
        )
        
        return tool_instance

    return decorator

def _generate_json_schema(name: str, desc: str, params: List[ToolParameter]) -> Dict[str, Any]:
    """Helper to generate standard JSON schema."""
    properties = {}
    required = []
    
    for p in params:
        properties[p.name] = {
            "type": p.type,
            "description": p.description or f"Parameter {p.name}"
        }
        if p.required:
            required.append(p.name)
            
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }
