"""Tool calling integration for LLM providers."""

from typing import Any, Dict, List, Optional, Union
from craft.mcp.registry import ToolRegistry, ToolExecution
from craft.mcp.client import MCPToolClient
from craft.utils.logging import get_logger


class ToolCallingMixin:
    """
    Mixin to add tool calling capabilities to Chatbot.

    Enables chatbots to use MCP tools and custom functions.
    """

    def __init__(self):
        """Initialize tool calling."""
        self.tool_registry = ToolRegistry()
        self.mcp_clients: List[MCPToolClient] = []
        self.logger = get_logger("craft.toolcalling")

    async def add_mcp_server(self, server_script_path: str) -> MCPToolClient:
        """
        Connect to an MCP server and register its tools.

        Args:
            server_script_path: Path to MCP server script

        Returns:
            Connected MCP client
        """
        client = MCPToolClient(server_script_path)
        await client.connect()

        # Register all tools from this server
        for tool in client.get_tools():
            self.tool_registry.register_mcp_tool(tool)

        self.mcp_clients.append(client)
        self.logger.info(f"Added MCP server with {len(client.tools)} tools")

        return client

    def add_custom_tool(
        self,
        name: str,
        func: callable,
        description: str,
        parameters: Dict[str, Any],
    ) -> None:
        """
        Register a custom Python function as a tool.

        Args:
            name: Tool name
            func: Python function
            description: Tool description
            parameters: JSON schema for parameters

        Example:
            def get_weather(location: str) -> str:
                return f"Weather in {location}: Sunny, 72°F"

            chatbot.add_custom_tool(
                name="get_weather",
                func=get_weather,
                description="Get current weather for a location",
                parameters={
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"}
                    },
                    "required": ["location"]
                }
            )
        """
        self.tool_registry.register_custom_tool(name, func, description, parameters)
        self.logger.info(f"Added custom tool: {name}")

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecution:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        # Find which MCP client owns this tool (if any)
        mcp_client = None
        for client in self.mcp_clients:
            if any(t.name == tool_name for t in client.tools):
                mcp_client = client
                break

        return await self.tool_registry.execute_tool(
            tool_name=tool_name,
            arguments=arguments,
            mcp_client=mcp_client,
        )

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of all available tools in function calling format.

        Returns:
            List of function schemas for LLM providers
        """
        return self.tool_registry.get_function_schemas()

    async def close_mcp_connections(self) -> None:
        """Close all MCP client connections."""
        for client in self.mcp_clients:
            await client.close()
        self.mcp_clients.clear()
        self.logger.info("Closed all MCP connections")
