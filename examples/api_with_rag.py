"""Example: API server with RAG enabled."""

import os
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.rag import RetrievalEngine
from craft.rag.embeddings import SentenceTransformerEmbedding
from craft.rag.vectorstores import ChromaVectorStore
from craft.integrations.api import CRAFTServer


def main():
    print("🧠 CRAFT API Server with RAG Example\n")

    # Setup RAG system
    print("1. Initializing RAG system...")
    embeddings = SentenceTransformerEmbedding(model="all-MiniLM-L6-v2")
    vector_store = ChromaVectorStore(
        collection_name="api_docs",
        persist_directory="./api_rag_db"
    )

    rag = RetrievalEngine(
        embedding_provider=embeddings,
        vector_store=vector_store,
    )

    # Add knowledge base
    print("2. Adding documents to knowledge base...")
    documents = [
        "CRAFT is a flexible chatbot framework that supports multiple LLM providers.",
        "The API server provides REST endpoints and WebSocket support for real-time chat.",
        "You can enable RAG to give your chatbot access to custom knowledge bases.",
        "The JavaScript widget makes it easy to integrate CRAFT into any website.",
        "CRAFT supports streaming responses for a better user experience.",
    ]

    rag.add_documents(documents)
    print(f"   ✓ Added {rag.document_count} documents\n")

    # Create chatbot with RAG
    print("3. Creating chatbot with RAG...")
    chatbot = Chatbot(
        provider=AnthropicProvider(
            model="claude-3-5-sonnet-20241022",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        ),
        rag=rag,
        system_prompt="You are a helpful assistant with knowledge about CRAFT. Use the provided context to answer questions.",
        memory=True,
    )

    # Create API server
    print("4. Starting API server...\n")
    server = CRAFTServer(
        chatbot=chatbot,
        title="CRAFT API with RAG",
        description="API server with RAG-enabled chatbot",
        enable_cors=True,
    )

    print("=" * 60)
    print("🌐 Server Info:")
    print("   📍 API Docs: http://localhost:8000/docs")
    print("   📍 Health: http://localhost:8000/health")
    print("   🧠 RAG: Enabled")
    print("   📚 Documents: " + str(rag.document_count))
    print("\n🚀 Try asking:")
    print('   "What is CRAFT?"')
    print('   "How do I integrate CRAFT into my website?"')
    print('   "Does CRAFT support streaming?"')
    print("=" * 60 + "\n")

    server.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
