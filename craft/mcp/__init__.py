"""MCP (Model Context Protocol) integration for CRAFT."""

from craft.mcp.server import CRAFTMCPServer
from craft.mcp.client import MCPToolClient
from craft.mcp.registry import ToolRegistry, ToolExecution

__all__ = [
    "CRAFTMCPServer",
    "MCPToolClient",
    "ToolRegistry",
    "ToolExecution",
]
