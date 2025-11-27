"""Advanced RAG example with different configurations."""

import os
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.rag import RetrievalEngine, RetrievalConfig, ChunkConfig, ChunkingStrategy
from craft.rag.embeddings import SentenceTransformerEmbedding
from craft.rag.vectorstores import FAISSVectorStore


def main():
    print("🚀 CRAFT RAG Demo - Advanced Example\n")

    # Configure chunking strategy
    chunk_config = ChunkConfig(
        strategy=ChunkingStrategy.SENTENCE,  # Chunk by sentences
        chunk_size=512,
        chunk_overlap=50,
    )

    # Configure retrieval
    retrieval_config = RetrievalConfig(
        top_k=3,  # Retrieve top 3 most relevant chunks
        score_threshold=0.5,  # Minimum similarity threshold
        chunk_config=chunk_config,
    )

    # Create embedding provider
    print("1. Initializing embedding provider (Sentence Transformers)...")
    embeddings = SentenceTransformerEmbedding(
        model="all-mpnet-base-v2"  # Better quality, 768 dimensions
    )

    # Create FAISS vector store
    print("2. Initializing FAISS vector store...")
    vector_store = FAISSVectorStore(
        collection_name="advanced_demo",
        index_path="./demo_faiss",
        embedding_dimension=embeddings.dimension,
        index_type="Flat",  # or "HNSW" for larger datasets
    )

    # Create retrieval engine
    print("3. Creating retrieval engine with custom config...")
    rag = RetrievalEngine(
        embedding_provider=embeddings,
        vector_store=vector_store,
        config=retrieval_config,
    )

    # Add documents from a knowledge base
    print("4. Adding documents from knowledge base...\n")

    knowledge_base = """
    CRAFT Framework Overview:
    CRAFT (Chatbot & RAG Framework Toolkit) is a comprehensive Python framework for building
    intelligent chatbots. It provides a provider-agnostic interface for working with multiple
    LLM providers including Anthropic Claude, OpenAI GPT, and Google Gemini.

    Key Features:
    - Provider-agnostic architecture allows switching between LLMs with minimal code changes
    - Built-in RAG (Retrieval-Augmented Generation) system for knowledge-enhanced responses
    - Multiple vector store backends: ChromaDB, FAISS, Pinecone, and more
    - Flexible embedding options: OpenAI embeddings, Sentence Transformers, and custom providers
    - Streaming support for real-time responses across all providers
    - Conversation memory management with multiple storage backends
    - Docker and docker-compose support for easy deployment

    RAG System:
    The RAG system in CRAFT consists of three main components:
    1. Embedding Providers: Convert text to vector embeddings
    2. Vector Stores: Store and search embeddings efficiently
    3. Retrieval Engine: Orchestrates the entire RAG pipeline

    Document Chunking:
    CRAFT supports multiple chunking strategies:
    - Fixed size: Split documents by character count
    - Sentence-based: Split on sentence boundaries
    - Paragraph-based: Split on paragraph boundaries
    - Semantic: Group semantically similar content (future)

    Best Practices:
    - Choose embedding model based on your use case (speed vs quality)
    - Use chunking strategy appropriate for your document type
    - Tune top_k and score_threshold for optimal retrieval
    - Monitor and evaluate RAG performance with your specific data
    """

    # Add with metadata
    rag.add_documents(
        documents=[knowledge_base],
        metadatas=[{"source": "CRAFT Documentation", "type": "overview"}],
        chunk=True,  # Enable chunking
    )

    print(f"✓ Added {rag.document_count} document chunks\n")

    # Create chatbot
    print("5. Creating RAG-enabled chatbot...")
    chatbot = Chatbot(
        provider=AnthropicProvider(
            model="claude-sonnet-4.5",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.7,
        ),
        rag=rag,
        system_prompt=(
            "You are an expert on the CRAFT framework. "
            "Use the provided context to give detailed, accurate answers. "
            "If the context doesn't contain enough information, say so."
        ),
        memory=True,
    )

    print(f"\n{chatbot}\n")
    print("=" * 70)

    # Interactive Q&A
    questions = [
        "What are the key features of CRAFT?",
        "What chunking strategies are available?",
        "How does the RAG system work?",
        "What embedding providers can I use?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/4] ❓ {question}")
        print("-" * 70)

        response = chatbot.chat(question)
        print(f"\n🤖 {response.content}\n")

        if response.usage:
            print(f"📊 Tokens used: {response.usage['total_tokens']}")

    # Show retrieval stats
    print("\n" + "=" * 70)
    print(f"📚 Total documents in knowledge base: {rag.document_count}")
    print("✨ Advanced demo completed!")


if __name__ == "__main__":
    main()
