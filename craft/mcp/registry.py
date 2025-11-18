"""Tool registry for managing MCP tools."""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from craft.mcp.client import MCPTool
from craft.utils.logging import get_logger


@dataclass
class ToolExecution:
    """Result of a tool execution."""

    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None


class ToolRegistry:
    """
    Registry for managing and executing tools.

    Supports both MCP tools and custom Python functions.
    """

    def __init__(self):
        """Initialize tool registry."""
        self.logger = get_logger("craft.mcp.registry")
        self._mcp_tools: Dict[str, MCPTool] = {}
        self._custom_tools: Dict[str, Callable] = {}

    def register_mcp_tool(self, tool: MCPTool) -> None:
        """
        Register an MCP tool.

        Args:
            tool: MCP tool to register
        """
        self._mcp_tools[tool.name] = tool
        self.logger.info(f"Registered MCP tool: {tool.name}")

    def register_custom_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any],
    ) -> None:
        """
        Register a custom Python function as a tool.

        Args:
            name: Tool name
            func: Python function to call
            description: Tool description
            parameters: JSON schema for parameters
        """
        # Store function
        self._custom_tools[name] = func

        # Create MCP-compatible tool representation
        tool = MCPTool(name=name, description=description, input_schema=parameters)
        self._mcp_tools[name] = tool

        self.logger.info(f"Registered custom tool: {name}")

    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return self._mcp_tools.get(name)

    def list_tools(self) -> List[MCPTool]:
        """List all registered tools."""
        return list(self._mcp_tools.values())

    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """
        Get function schemas for LLM function calling.

        Returns:
            List of function schemas
        """
        return [tool.to_function_schema() for tool in self._mcp_tools.values()]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        mcp_client: Optional[Any] = None,
    ) -> ToolExecution:
        """
        Execute a tool.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            mcp_client: Optional MCP client for MCP tools

        Returns:
            ToolExecution result
        """
        if tool_name not in self._mcp_tools:
            return ToolExecution(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Tool not found: {tool_name}",
            )

        try:
            # Check if it's a custom tool
            if tool_name in self._custom_tools:
                func = self._custom_tools[tool_name]
                result = await func(**arguments) if asyncio.iscoroutinefunction(func) else func(**arguments)
            elif mcp_client:
                # It's an MCP tool
                result = await mcp_client.call_tool(tool_name, arguments)
            else:
                return ToolExecution(
                    tool_name=tool_name,
                    success=False,
                    result=None,
                    error="MCP client required for MCP tools",
                )

            self.logger.info(f"Tool executed successfully: {tool_name}")
            return ToolExecution(
                tool_name=tool_name,
                success=True,
                result=result,
            )

        except Exception as e:
            self.logger.error(f"Tool execution failed: {tool_name} - {e}")
            return ToolExecution(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e),
            )

    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if tool was removed
        """
        if name in self._mcp_tools:
            del self._mcp_tools[name]
            if name in self._custom_tools:
                del self._custom_tools[name]
            self.logger.info(f"Unregistered tool: {name}")
            return True
        return False

    def clear(self) -> None:
        """Clear all registered tools."""
        self._mcp_tools.clear()
        self._custom_tools.clear()
        self.logger.info("All tools cleared")

    def __len__(self) -> int:
        return len(self._mcp_tools)

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={len(self._mcp_tools)})"


# Need to import asyncio for iscoroutinefunction
import asyncio
