# MCP Integration Guide

CRAFT supports the Model Context Protocol (MCP), enabling powerful tool integration capabilities.

## What is MCP?

MCP (Model Context Protocol) is a standardized protocol for connecting AI assistants with external tools and data sources. It allows:

- **Exposing functionality** as tools that other applications can use
- **Consuming tools** from external MCP servers
- **Standardized communication** between different AI systems

## CRAFT as an MCP Server

Expose your CRAFT chatbot as an MCP server that others can use:

### Quick Start

```python
import asyncio
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.mcp import CRAFTMCPServer

async def main():
    # Create chatbot
    chatbot = Chatbot(
        provider=AnthropicProvider(api_key="your-key"),
        memory=True
    )

    # Create MCP server
    mcp_server = CRAFTMCPServer(
        chatbot=chatbot,
        server_name="my-craft-bot"
    )

    # Run server (uses stdio)
    await mcp_server.run()

asyncio.run(main())
```

### Available Tools

When you run CRAFT as an MCP server, it exposes these tools:

1. **craft_chat** - Send a message to the chatbot
   ```json
   {
     "message": "Hello!",
     "use_rag": true,
     "conversation_id": "optional-id"
   }
   ```

2. **craft_clear_conversation** - Clear conversation history

3. **craft_add_documents** - Add documents to RAG (if enabled)
   ```json
   {
     "documents": ["doc1", "doc2"],
     "chunk": true
   }
   ```

4. **craft_query_knowledge** - Query RAG directly
   ```json
   {
     "query": "search term",
     "top_k": 5
   }
   ```

5. **craft_clear_knowledge** - Clear RAG knowledge base

6. **craft_list_conversations** - List saved conversations (if memory enabled)

### Using with Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "craft-chatbot": {
      "command": "python",
      "args": ["path/to/mcp_server_example.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your-key"
      }
    }
  }
}
```

## Using External MCP Tools

CRAFT can consume tools from other MCP servers:

```python
import asyncio
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.core.tool_calling import ToolCallingMixin

class ToolEnabledChatbot(Chatbot, ToolCallingMixin):
    def __init__(self, *args, **kwargs):
        Chatbot.__init__(self, *args, **kwargs)
        ToolCallingMixin.__init__(self)

async def main():
    chatbot = ToolEnabledChatbot(
        provider=AnthropicProvider(api_key="your-key")
    )

    # Connect to external MCP server
    await chatbot.add_mcp_server("path/to/server_script.py")

    # List available tools
    tools = chatbot.get_available_tools()
    print(f"Available tools: {len(tools)}")

    # Execute a tool
    result = await chatbot.execute_tool(
        "tool_name",
        {"arg": "value"}
    )

asyncio.run(main())
```

## Custom Python Tools

Register your own Python functions as tools:

```python
def get_weather(location: str) -> str:
    """Get weather for a location."""
    # Your implementation
    return f"Weather in {location}: Sunny"

chatbot.add_custom_tool(
    name="get_weather",
    func=get_weather,
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name"
            }
        },
        "required": ["location"]
    }
)
```

## Tool Registry

Manage all tools in one place:

```python
from craft.mcp import ToolRegistry

registry = ToolRegistry()

# Register MCP tools
registry.register_mcp_tool(mcp_tool)

# Register custom tools
registry.register_custom_tool(name, func, description, parameters)

# List all tools
tools = registry.list_tools()

# Execute a tool
result = await registry.execute_tool("tool_name", {"arg": "value"})
```

## Advanced Usage

### With RAG

```python
from craft.rag import RetrievalEngine
from craft.rag.embeddings import SentenceTransformerEmbedding
from craft.rag.vectorstores import ChromaVectorStore

# Setup RAG
embeddings = SentenceTransformerEmbedding()
vector_store = ChromaVectorStore(collection_name="docs")
rag = RetrievalEngine(embeddings, vector_store)
rag.add_documents(["Knowledge here..."])

# Create chatbot with RAG
chatbot = Chatbot(
    provider=AnthropicProvider(api_key="your-key"),
    rag=rag
)

# Expose as MCP server (includes RAG tools)
server = CRAFTMCPServer(chatbot=chatbot)
await server.run()
```

### Multiple Tool Sources

```python
# Connect to multiple MCP servers
await chatbot.add_mcp_server("server1.py")
await chatbot.add_mcp_server("server2.py")

# Add custom tools
chatbot.add_custom_tool("tool1", func1, desc1, params1)
chatbot.add_custom_tool("tool2", func2, desc2, params2)

# All tools available together!
all_tools = chatbot.get_available_tools()
```

## Error Handling

```python
result = await chatbot.execute_tool("tool_name", args)

if result.success:
    print(f"Success: {result.result}")
else:
    print(f"Error: {result.error}")
```

## Best Practices

1. **Descriptive Names**: Use clear, descriptive tool names
2. **Good Descriptions**: Help the LLM understand when to use each tool
3. **Type Schemas**: Provide detailed JSON schemas for parameters
4. **Error Handling**: Always check `result.success` before using results
5. **Resource Cleanup**: Call `await chatbot.close_mcp_connections()` when done

## Examples

See the `examples/` directory for complete examples:

- `mcp_server_example.py` - Run CRAFT as MCP server
- `mcp_custom_tools.py` - Using custom Python tools
- `mcp_config.json` - Claude Desktop configuration

## Troubleshooting

**"mcp package not installed"**
```bash
pip install 'craft-chatbot[mcp]'
```

**Server not responding**
- Check that the server script is executable
- Verify environment variables are set
- Check logs for errors

**Tools not appearing**
- Ensure server is properly initialized
- Check that tools are registered before listing
- Verify MCP client connection is established

## Learn More

- [MCP Specification](https://modelcontextprotocol.io)
- [Claude Desktop MCP](https://www.anthropic.com/news/model-context-protocol)
- [CRAFT Documentation](../README.md)
