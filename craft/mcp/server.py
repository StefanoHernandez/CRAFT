"""MCP Server implementation - Expose CRAFT as MCP tools."""

import asyncio
from typing import Any, Dict, List, Optional, Callable
import json

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, CallToolResult
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from craft.core.chatbot import Chatbot
from craft.utils.logging import get_logger


class CRAFTMCPServer:
    """
    MCP Server that exposes CRAFT functionality as tools.

    Allows other applications to use CRAFT chatbot via MCP protocol.
    """

    def __init__(self, chatbot: Chatbot, server_name: str = "craft-chatbot"):
        """
        Initialize CRAFT MCP Server.

        Args:
            chatbot: CRAFT Chatbot instance
            server_name: Server name for MCP
        """
        if not MCP_AVAILABLE:
            raise ImportError(
                "mcp package not installed. "
                "Install with: pip install 'craft-chatbot[mcp]'"
            )

        self.chatbot = chatbot
        self.server_name = server_name
        self.logger = get_logger("craft.mcp.server")

        # Create MCP server
        self.server = Server(server_name)

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register CRAFT tools with MCP server."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available CRAFT tools."""
            tools = [
                Tool(
                    name="craft_chat",
                    description="Chat with the CRAFT AI assistant. Send a message and get a response.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to send to the assistant",
                            },
                            "use_rag": {
                                "type": "boolean",
                                "description": "Whether to use RAG for retrieval",
                                "default": True,
                            },
                            "conversation_id": {
                                "type": "string",
                                "description": "Optional conversation ID to continue",
                            },
                        },
                        "required": ["message"],
                    },
                ),
                Tool(
                    name="craft_clear_conversation",
                    description="Clear the current conversation history",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
            ]

            # Add RAG-specific tools if RAG is enabled
            if self.chatbot.rag:
                tools.extend([
                    Tool(
                        name="craft_add_documents",
                        description="Add documents to the RAG knowledge base",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "documents": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of document texts to add",
                                },
                                "chunk": {
                                    "type": "boolean",
                                    "description": "Whether to chunk documents",
                                    "default": True,
                                },
                            },
                            "required": ["documents"],
                        },
                    ),
                    Tool(
                        name="craft_query_knowledge",
                        description="Query the RAG knowledge base directly without chatting",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The query to search for",
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "Number of results to return",
                                    "default": 5,
                                },
                            },
                            "required": ["query"],
                        },
                    ),
                    Tool(
                        name="craft_clear_knowledge",
                        description="Clear all documents from the RAG knowledge base",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                        },
                    ),
                ])

            # Add conversation tools if memory is enabled
            if self.chatbot.memory:
                tools.append(
                    Tool(
                        name="craft_list_conversations",
                        description="List all saved conversation IDs",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                        },
                    )
                )

            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            self.logger.info(f"Tool called: {name} with args: {arguments}")

            try:
                if name == "craft_chat":
                    return await self._handle_chat(arguments)
                elif name == "craft_clear_conversation":
                    return await self._handle_clear_conversation()
                elif name == "craft_add_documents":
                    return await self._handle_add_documents(arguments)
                elif name == "craft_query_knowledge":
                    return await self._handle_query_knowledge(arguments)
                elif name == "craft_clear_knowledge":
                    return await self._handle_clear_knowledge()
                elif name == "craft_list_conversations":
                    return await self._handle_list_conversations()
                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                self.logger.error(f"Error calling tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _handle_chat(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle chat tool call."""
        message = arguments["message"]
        use_rag = arguments.get("use_rag", True)
        conversation_id = arguments.get("conversation_id")

        # Load conversation if ID provided
        if conversation_id and self.chatbot.memory:
            self.chatbot.load_conversation(conversation_id)

        # Get response
        response = await self.chatbot.achat(
            message=message,
            use_rag=use_rag,
        )

        # Format response
        result = {
            "response": response.content,
            "conversation_id": self.chatbot.conversation_id,
            "model": response.model,
        }

        if response.usage:
            result["usage"] = response.usage

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_clear_conversation(self) -> List[TextContent]:
        """Handle clear conversation tool call."""
        self.chatbot.clear_conversation()
        return [TextContent(type="text", text="Conversation cleared successfully")]

    async def _handle_add_documents(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle add documents tool call."""
        if not self.chatbot.rag:
            return [TextContent(type="text", text="Error: RAG is not enabled")]

        documents = arguments["documents"]
        chunk = arguments.get("chunk", True)

        doc_ids = await self.chatbot.rag.aadd_documents(
            documents=documents,
            chunk=chunk,
        )

        result = {
            "status": "success",
            "documents_added": len(doc_ids),
            "total_documents": self.chatbot.rag.document_count,
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_query_knowledge(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle query knowledge tool call."""
        if not self.chatbot.rag:
            return [TextContent(type="text", text="Error: RAG is not enabled")]

        query = arguments["query"]
        top_k = arguments.get("top_k", 5)

        results = await self.chatbot.rag.aretrieve(query, top_k=top_k)

        formatted_results = [
            {
                "content": doc.content,
                "score": doc.score,
                "metadata": doc.metadata,
            }
            for doc in results
        ]

        return [TextContent(type="text", text=json.dumps(formatted_results, indent=2))]

    async def _handle_clear_knowledge(self) -> List[TextContent]:
        """Handle clear knowledge tool call."""
        if not self.chatbot.rag:
            return [TextContent(type="text", text="Error: RAG is not enabled")]

        self.chatbot.rag.clear()
        return [TextContent(type="text", text="Knowledge base cleared successfully")]

    async def _handle_list_conversations(self) -> List[TextContent]:
        """Handle list conversations tool call."""
        if not self.chatbot.memory:
            return [TextContent(type="text", text="Error: Memory is not enabled")]

        conversations = self.chatbot.memory.list_conversations()

        result = {
            "total": len(conversations),
            "conversation_ids": conversations,
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def run(self) -> None:
        """Run the MCP server."""
        self.logger.info(f"Starting CRAFT MCP Server: {self.server_name}")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    def run_sync(self) -> None:
        """Run the server synchronously."""
        asyncio.run(self.run())
