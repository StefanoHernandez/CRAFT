"""Document Q&A with RAG - Load documents from files."""

import os
from pathlib import Path
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.rag import RetrievalEngine, RetrievalConfig
from craft.rag.embeddings import SentenceTransformerEmbedding
from craft.rag.vectorstores import ChromaVectorStore


def load_documents_from_directory(directory: str) -> list:
    """Load text documents from a directory."""
    documents = []
    path = Path(directory)

    for file_path in path.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            documents.append({
                "content": content,
                "metadata": {
                    "source": file_path.name,
                    "path": str(file_path),
                }
            })

    return documents


def main():
    print("📄 CRAFT RAG Demo - Document Q&A\n")

    # Create demo documents
    demo_docs_dir = Path("./demo_documents")
    demo_docs_dir.mkdir(exist_ok=True)

    # Create sample documents
    sample_docs = {
        "python_basics.txt": """
        Python is a high-level, interpreted programming language known for its simplicity and readability.
        It was created by Guido van Rossum and first released in 1991. Python supports multiple programming
        paradigms including procedural, object-oriented, and functional programming. It has a comprehensive
        standard library and a vast ecosystem of third-party packages available through PyPI.
        """,
        "machine_learning.txt": """
        Machine Learning is a subset of artificial intelligence that enables systems to learn and improve
        from experience without being explicitly programmed. There are three main types: supervised learning,
        unsupervised learning, and reinforcement learning. Popular frameworks include TensorFlow, PyTorch,
        and scikit-learn. Deep learning, using neural networks with multiple layers, has achieved remarkable
        results in computer vision, natural language processing, and speech recognition.
        """,
        "web_development.txt": """
        Web development involves building websites and web applications. The frontend (client-side) uses
        HTML, CSS, and JavaScript, often with frameworks like React, Vue, or Angular. The backend (server-side)
        can be built with various languages including Python (Django, Flask), JavaScript (Node.js), or Ruby
        (Rails). Modern web development also includes API development, database management, authentication,
        and deployment using cloud platforms like AWS, Google Cloud, or Azure.
        """,
    }

    for filename, content in sample_docs.items():
        with open(demo_docs_dir / filename, "w") as f:
            f.write(content.strip())

    print(f"✓ Created {len(sample_docs)} sample documents in {demo_docs_dir}\n")

    # Initialize RAG components
    print("1. Initializing RAG system...")
    embeddings = SentenceTransformerEmbedding(model="all-MiniLM-L6-v2")
    vector_store = ChromaVectorStore(
        collection_name="document_qa",
        persist_directory="./demo_doc_qa_chroma"
    )

    rag = RetrievalEngine(
        embedding_provider=embeddings,
        vector_store=vector_store,
        config=RetrievalConfig(top_k=2),
    )

    # Load and index documents
    print("2. Loading documents from directory...")
    docs = load_documents_from_directory(demo_docs_dir)

    print(f"3. Indexing {len(docs)} documents...")
    for doc in docs:
        rag.add_documents(
            documents=[doc["content"]],
            metadatas=[doc["metadata"]],
            chunk=True,
        )

    print(f"✓ Indexed {rag.document_count} chunks\n")

    # Create chatbot
    chatbot = Chatbot(
        provider=AnthropicProvider(
            model="claude-sonnet-4.5",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        ),
        rag=rag,
        system_prompt=(
            "You are a knowledgeable assistant. Answer questions based on the provided documents. "
            "Always cite the source document when giving answers."
        ),
    )

    print("=" * 70)
    print("📚 Document Q&A System Ready!")
    print("=" * 70)
    print("\nType 'exit' to quit, 'docs' to list documents\n")

    # Interactive Q&A loop
    while True:
        question = input("❓ Your question: ").strip()

        if not question:
            continue

        if question.lower() == "exit":
            break

        if question.lower() == "docs":
            print("\n📄 Available documents:")
            for doc in docs:
                print(f"  - {doc['metadata']['source']}")
            print()
            continue

        # Get answer with RAG
        response = chatbot.chat(question)
        print(f"\n🤖 Answer:\n{response.content}\n")
        print("-" * 70 + "\n")

    # Cleanup
    print("\n🧹 Cleaning up...")
    vector_store.clear()

    # Remove demo files
    for filename in sample_docs.keys():
        (demo_docs_dir / filename).unlink()
    demo_docs_dir.rmdir()

    print("✨ Demo completed!")


if __name__ == "__main__":
    main()
