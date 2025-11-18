"""MCP Client implementation - Use external MCP tools in CRAFT."""

from typing import Any, Dict, List, Optional
import json

try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from craft.utils.logging import get_logger


class MCPTool:
    """Represents an MCP tool that can be called."""

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        """
        Initialize MCP tool.

        Args:
            name: Tool name
            description: Tool description
            input_schema: JSON schema for tool inputs
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def to_function_schema(self) -> Dict[str, Any]:
        """
        Convert to function calling schema for LLM providers.

        Returns:
            Function schema compatible with OpenAI/Anthropic function calling
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema,
        }

    def __repr__(self) -> str:
        return f"MCPTool(name={self.name})"


class MCPToolClient:
    """
    Client for consuming external MCP tools.

    Allows CRAFT chatbot to use tools from other MCP servers.
    """

    def __init__(self, server_script_path: str):
        """
        Initialize MCP tool client.

        Args:
            server_script_path: Path to MCP server script/executable
        """
        if not MCP_AVAILABLE:
            raise ImportError(
                "mcp package not installed. "
                "Install with: pip install 'craft-chatbot[mcp]'"
            )

        self.server_script_path = server_script_path
        self.logger = get_logger("craft.mcp.client")
        self.session: Optional[ClientSession] = None
        self.tools: List[MCPTool] = []

    async def connect(self) -> None:
        """Connect to MCP server and list available tools."""
        self.logger.info(f"Connecting to MCP server: {self.server_script_path}")

        # Start server and create session
        server_params = stdio_client(self.server_script_path)

        async with server_params as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session

                # Initialize
                await session.initialize()

                # List tools
                tools_response = await session.list_tools()

                self.tools = [
                    MCPTool(
                        name=tool.name,
                        description=tool.description or "",
                        input_schema=tool.inputSchema,
                    )
                    for tool in tools_response.tools
                ]

                self.logger.info(f"Connected! Found {len(self.tools)} tools")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        self.logger.debug(f"Calling tool: {tool_name} with args: {arguments}")

        result = await self.session.call_tool(tool_name, arguments)

        # Extract text content
        if result.content:
            text_content = [c.text for c in result.content if hasattr(c, "text")]
            return "\n".join(text_content)

        return None

    def get_tools(self) -> List[MCPTool]:
        """Get list of available tools."""
        return self.tools

    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """
        Get function schemas for LLM function calling.

        Returns:
            List of function schemas
        """
        return [tool.to_function_schema() for tool in self.tools]

    async def close(self) -> None:
        """Close connection to MCP server."""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("Disconnected from MCP server")

    def __repr__(self) -> str:
        return f"MCPToolClient(server={self.server_script_path}, tools={len(self.tools)})"
