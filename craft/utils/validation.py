"""Validation utilities for CRAFT."""

from typing import List, Union, Optional
from craft.tools.base import Tool

def validate_tool_choice(
    tool_choice: Union[str, List[str]], 
    available_tools: List[Tool]
) -> None:
    """
    Validate tool_choice parameter against available tools.
    
    Args:
        tool_choice: Tool choice control parameter.
            - "auto": Model decides (default)
            - "none": Tools disabled
            - "required": Model must use at least one tool
            - "required_first": Model must use a tool in the first step
            - List[str]: Only specified tools are available
            - str: Specific tool name (forced)
        available_tools: List of available Tool objects.
        
    Raises:
        ValueError: If tool_choice is invalid or references non-existent tools.
    """
    valid_modes = {"auto", "none", "required", "required_first"}
    available_tool_names = {t.name for t in available_tools}
    
    # Case 1: Standard modes
    if isinstance(tool_choice, str) and tool_choice in valid_modes:
        return

    # Case 2: Specific tool name
    if isinstance(tool_choice, str):
        if tool_choice not in available_tool_names:
            raise ValueError(
                f"Tool '{tool_choice}' not found in available tools: {sorted(list(available_tool_names))}"
            )
        return

    # Case 3: List of tool names
    if isinstance(tool_choice, list):
        if not tool_choice:
            raise ValueError("Tool choice list cannot be empty. Use 'none' to disable tools.")
            
        invalid_tools = [name for name in tool_choice if name not in available_tool_names]
        if invalid_tools:
            raise ValueError(
                f"Tools {invalid_tools} not found in available tools: {sorted(list(available_tool_names))}"
            )
        return

    # Case 4: Invalid type
    raise ValueError(
        f"Invalid tool_choice type: {type(tool_choice)}. "
        f"Must be str ({valid_modes} or tool name) or List[str]."
    )
