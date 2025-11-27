"""Example: Running CRAFT as an MCP server."""

import os
import asyncio
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.rag import RetrievalEngine
from craft.rag.embeddings import SentenceTransformerEmbedding
from craft.rag.vectorstores import ChromaVectorStore
from craft.mcp import CRAFTMCPServer


async def main():
    print("🛠️  CRAFT MCP Server Example\n")

    # Setup RAG (optional)
    print("1. Setting up RAG system...")
    embeddings = SentenceTransformerEmbedding(model="all-MiniLM-L6-v2")
    vector_store = ChromaVectorStore(collection_name="mcp_demo")
    rag = RetrievalEngine(embeddings, vector_store)

    # Add some knowledge
    rag.add_documents([
        "CRAFT is a chatbot framework with MCP support.",
        "MCP allows tools to be exposed and consumed across applications.",
        "You can use CRAFT as an MCP server to expose chat functionality.",
    ])

    print("   ✓ RAG configured\n")

    # Create chatbot
    print("2. Creating chatbot...")
    chatbot = Chatbot(
        provider=AnthropicProvider(
            model="claude-sonnet-4.5",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        ),
        rag=rag,
        memory=True,
        system_prompt="You are a helpful AI assistant with knowledge about CRAFT.",
    )

    print("   ✓ Chatbot ready\n")

    # Create MCP server
    print("3. Starting MCP server...")
    mcp_server = CRAFTMCPServer(
        chatbot=chatbot,
        server_name="craft-chatbot"
    )

    print("=" * 60)
    print("🚀 CRAFT MCP Server Running!")
    print("\nAvailable Tools:")
    print("  - craft_chat: Chat with the assistant")
    print("  - craft_clear_conversation: Clear conversation")
    print("  - craft_add_documents: Add documents to RAG")
    print("  - craft_query_knowledge: Query RAG directly")
    print("  - craft_clear_knowledge: Clear knowledge base")
    print("  - craft_list_conversations: List saved conversations")
    print("\nServer communicates via stdio (standard input/output)")
    print("Use with MCP-compatible clients like Claude Desktop")
    print("=" * 60 + "\n")

    # Run server
    await mcp_server.run()


if __name__ == "__main__":
    asyncio.run(main())
