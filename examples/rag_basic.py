"""Basic RAG example with CRAFT."""

import os
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.rag import RetrievalEngine
from craft.rag.embeddings import SentenceTransformerEmbedding
from craft.rag.vectorstores import ChromaVectorStore


def main():
    print("🧠 CRAFT RAG Demo - Basic Example\n")

    # Step 1: Create embedding provider (local, free!)
    print("1. Initializing embedding provider...")
    embeddings = SentenceTransformerEmbedding(
        model="all-MiniLM-L6-v2"  # Fast, 384 dimensions
    )

    # Step 2: Create vector store
    print("2. Initializing vector store (ChromaDB)...")
    vector_store = ChromaVectorStore(
        collection_name="craft_demo",
        persist_directory="./demo_chroma"
    )

    # Step 3: Create retrieval engine
    print("3. Creating retrieval engine...")
    rag = RetrievalEngine(
        embedding_provider=embeddings,
        vector_store=vector_store,
    )

    # Step 4: Add some documents
    print("4. Adding documents to knowledge base...\n")
    documents = [
        "CRAFT is a flexible chatbot framework that supports multiple LLM providers like Anthropic, OpenAI, and Google.",
        "RAG (Retrieval-Augmented Generation) allows chatbots to access external knowledge by retrieving relevant documents.",
        "ChromaDB is an open-source embedding database that makes it easy to build LLM applications with memory.",
        "FAISS is a library for efficient similarity search developed by Facebook AI Research.",
        "Vector embeddings convert text into numerical representations that capture semantic meaning.",
    ]

    rag.add_documents(documents)
    print(f"✓ Added {rag.document_count} document chunks\n")

    # Step 5: Create chatbot with RAG
    print("5. Creating chatbot with RAG enabled...")
    chatbot = Chatbot(
        provider=AnthropicProvider(
            model="claude-sonnet-4.5",
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ),
        rag=rag,
        system_prompt="You are a helpful assistant. Use the provided context to answer questions accurately.",
        memory=True,
    )

    print(f"\n{chatbot}\n")
    print("=" * 60)

    # Step 6: Ask questions
    questions = [
        "What is CRAFT?",
        "Tell me about RAG",
        "What vector databases are mentioned?",
    ]

    for question in questions:
        print(f"\n❓ Question: {question}")
        print("-" * 60)

        response = chatbot.chat(question)
        print(f"🤖 Answer: {response.content}\n")

    # Cleanup
    vector_store.clear()
    print("\n✨ Demo completed!")


if __name__ == "__main__":
    main()
