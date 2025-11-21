"""Tool system for CRAFT agents with MCP integration."""

from craft.tools.base import Tool, ToolParameter, ToolMetadata
from craft.tools.decorator import tool, set_global_registry, get_global_registry
from craft.mcp.registry import ToolRegistry

__all__ = [
    "Tool",
    "ToolParameter",
    "ToolMetadata",
    "tool",
    "ToolRegistry",
    "set_global_registry",
    "get_global_registry",
]
