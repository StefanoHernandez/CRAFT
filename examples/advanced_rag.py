"""
Examples for Advanced RAG: Hybrid Search, Reranking, Query Rewriting

This demonstrates the advanced RAG features added in CRAFT v1.4.0
"""

from craft.chatbot import Chatbot
from craft.loaders import Document
from craft.rag import HybridSearch, Reranker, QueryRewriter


def create_sample_documents():
    """Create sample documents for testing"""
    return [
        Document(
            content="CRAFT is a Python framework for building chatbots with RAG capabilities.",
            metadata={"source": "docs", "topic": "introduction"}
        ),
        Document(
            content="RAG stands for Retrieval-Augmented Generation, combining search with LLM generation.",
            metadata={"source": "docs", "topic": "concepts"}
        ),
        Document(
            content="CRAFT supports multiple LLM providers including OpenAI, Anthropic, and Google.",
            metadata={"source": "docs", "topic": "providers"}
        ),
        Document(
            content="Vector stores like ChromaDB and FAISS enable semantic search in CRAFT.",
            metadata={"source": "docs", "topic": "vector-stores"}
        ),
        Document(
            content="Document loaders in CRAFT can process PDF, CSV, and web content.",
            metadata={"source": "docs", "topic": "loaders"}
        ),
        Document(
            content="CRAFT v1.4.0 introduces hybrid search combining dense and sparse retrieval.",
            metadata={"source": "changelog", "topic": "features"}
        ),
        Document(
            content="Reranking improves search quality by reordering results based on relevance.",
            metadata={"source": "docs", "topic": "advanced-rag"}
        ),
        Document(
            content="Query rewriting uses LLMs to rephrase queries for better retrieval.",
            metadata={"source": "docs", "topic": "advanced-rag"}
        ),
        Document(
            content="HyDE generates hypothetical documents to improve semantic search.",
            metadata={"source": "research", "topic": "techniques"}
        ),
        Document(
            content="Azure OpenAI, AWS Bedrock, and Cohere are new providers in v1.4.0.",
            metadata={"source": "changelog", "topic": "providers"}
        ),
    ]


def example_1_hybrid_search_basic():
    """Example 1: Basic hybrid search"""
    print("\n=== Example 1: Hybrid Search Basic ===\n")

    try:
        # Setup (requires vector retriever from RAG setup)
        from craft.rag.retrieval import RetrievalEngine, RetrievalConfig
        from craft.rag.vectorstores.chroma import ChromaStore

        # Create vector store
        vector_store = ChromaStore(collection_name="craft_docs")

        # Add documents
        documents = create_sample_documents()
        for doc in documents:
            vector_store.add_document(doc.content, metadata=doc.metadata)

        # Create retrieval engine
        config = RetrievalConfig(top_k=5)
        retriever = RetrievalEngine(vector_store=vector_store, config=config)

        # Create hybrid search
        hybrid = HybridSearch(
            vector_retriever=retriever,
            bm25_weight=0.5,
            vector_weight=0.5
        )

        # Add documents to BM25 index
        hybrid.add_documents(documents)

        # Search
        query = "What is RAG?"
        results = hybrid.search(query, k=3)

        print(f"Query: {query}")
        print(f"Found {len(results)} results:\n")

        for i, doc in enumerate(results, 1):
            print(f"{i}. {doc.content}")
            print(f"   Source: {doc.metadata.get('source')}\n")

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install 'craft-chatbot[rag,advanced-rag]'")


def example_2_hybrid_search_weighted():
    """Example 2: Hybrid search with custom weights"""
    print("\n=== Example 2: Hybrid Search with Custom Weights ===\n")

    try:
        from craft.rag.retrieval import RetrievalEngine, RetrievalConfig
        from craft.rag.vectorstores.chroma import ChromaStore

        vector_store = ChromaStore(collection_name="craft_docs_weighted")
        documents = create_sample_documents()

        for doc in documents:
            vector_store.add_document(doc.content, metadata=doc.metadata)

        config = RetrievalConfig(top_k=5)
        retriever = RetrievalEngine(vector_store=vector_store, config=config)

        # Favor vector search (semantic) over BM25 (keyword)
        hybrid = HybridSearch(
            vector_retriever=retriever,
            bm25_weight=0.3,  # Less weight on keywords
            vector_weight=0.7  # More weight on semantics
        )

        hybrid.add_documents(documents)

        query = "How does semantic search work?"
        results = hybrid.search(query, k=3)

        print(f"Query: {query}")
        print("(Weighted toward semantic/vector search)\n")

        for i, doc in enumerate(results, 1):
            print(f"{i}. {doc.content[:100]}...")

    except ImportError as e:
        print(f"Missing dependency for hybrid search")


def example_3_reranking_basic():
    """Example 3: Basic reranking"""
    print("\n=== Example 3: Reranking Basic ===\n")

    try:
        # Initial search results (simulated)
        documents = create_sample_documents()[:5]

        # Create reranker
        reranker = Reranker(model="ms-marco-MiniLM-L-12-v2")

        # Rerank results
        query = "What providers does CRAFT support?"
        reranked = reranker.rerank(query, documents, top_k=3)

        print(f"Query: {query}")
        print(f"Reranked top {len(reranked)} results:\n")

        for i, doc in enumerate(reranked, 1):
            score = doc.metadata.get("rerank_score", 0)
            print(f"{i}. [Score: {score:.4f}] {doc.content}")

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install 'craft-chatbot[advanced-rag]'")


def example_4_reranking_comparison():
    """Example 4: Compare results before/after reranking"""
    print("\n=== Example 4: Reranking Comparison ===\n")

    try:
        documents = create_sample_documents()

        reranker = Reranker()

        query = "document loaders PDF CSV"

        print(f"Query: {query}\n")

        # Show original order
        print("Original order (first 3):")
        for i, doc in enumerate(documents[:3], 1):
            print(f"{i}. {doc.content[:80]}...")

        # Rerank
        reranked = reranker.rerank(query, documents, top_k=3)

        print("\nAfter reranking (top 3):")
        for i, doc in enumerate(reranked, 1):
            score = doc.metadata.get("rerank_score", 0)
            print(f"{i}. [Score: {score:.4f}] {doc.content[:80]}...")

    except ImportError:
        print("Reranking requires: pip install 'craft-chatbot[advanced-rag]'")


def example_5_query_expansion():
    """Example 5: Query expansion"""
    print("\n=== Example 5: Query Expansion ===\n")

    try:
        chatbot = Chatbot(provider="openai", model="gpt-3.5-turbo")
        rewriter = QueryRewriter(chatbot=chatbot)

        original_query = "RAG"
        expanded_queries = rewriter.expand_query(original_query, num_queries=4)

        print(f"Original query: {original_query}\n")
        print("Expanded queries:")
        for i, query in enumerate(expanded_queries, 1):
            print(f"{i}. {query}")

    except Exception as e:
        print(f"Error: {e}")
        print("Requires OpenAI API key: export OPENAI_API_KEY=your-key")


def example_6_query_decomposition():
    """Example 6: Query decomposition for complex questions"""
    print("\n=== Example 6: Query Decomposition ===\n")

    try:
        chatbot = Chatbot(provider="openai", model="gpt-3.5-turbo")
        rewriter = QueryRewriter(chatbot=chatbot)

        complex_query = "How do I set up CRAFT with Azure OpenAI, load PDF documents, and use hybrid search?"

        sub_queries = rewriter.decompose_query(complex_query)

        print(f"Complex query: {complex_query}\n")
        print(f"Decomposed into {len(sub_queries)} sub-queries:")
        for i, query in enumerate(sub_queries, 1):
            print(f"{i}. {query}")

    except Exception as e:
        print(f"Error: {e}")


def example_7_hyde():
    """Example 7: HyDE (Hypothetical Document Embeddings)"""
    print("\n=== Example 7: HyDE ===\n")

    try:
        chatbot = Chatbot(provider="openai", model="gpt-3.5-turbo")
        rewriter = QueryRewriter(chatbot=chatbot)

        query = "What is hybrid search in RAG?"

        # Generate hypothetical document
        hyde_doc = rewriter.hyde(query, document_length="paragraph")

        print(f"Query: {query}\n")
        print("Hypothetical document (for embedding):")
        print(hyde_doc)
        print("\nThis hypothetical answer can be embedded and used for semantic search,")
        print("often improving retrieval quality.")

    except Exception as e:
        print(f"Error: {e}")


def example_8_query_clarification():
    """Example 8: Query clarification"""
    print("\n=== Example 8: Query Clarification ===\n")

    try:
        chatbot = Chatbot(provider="openai", model="gpt-3.5-turbo")
        rewriter = QueryRewriter(chatbot=chatbot)

        ambiguous_query = "providers"
        clarified = rewriter.clarify_query(ambiguous_query)

        print(f"Ambiguous query: {ambiguous_query}")
        print(f"Clarified query: {clarified}")

    except Exception as e:
        print(f"Error: {e}")


def example_9_full_pipeline():
    """Example 9: Full advanced RAG pipeline"""
    print("\n=== Example 9: Full Advanced RAG Pipeline ===\n")

    try:
        # Setup
        chatbot = Chatbot(provider="openai", model="gpt-3.5-turbo")
        documents = create_sample_documents()

        # Step 1: Query rewriting
        rewriter = QueryRewriter(chatbot=chatbot)
        original_query = "loaders"
        clarified_query = rewriter.clarify_query(original_query)

        print(f"Original query: {original_query}")
        print(f"Clarified query: {clarified_query}\n")

        # Step 2: Hybrid search (simulated)
        print("Step 2: Hybrid search (combining vector + BM25)...")
        # Would use HybridSearch here with actual vector store
        initial_results = documents[:5]

        # Step 3: Reranking
        print("Step 3: Reranking results...\n")
        reranker = Reranker()
        final_results = reranker.rerank(clarified_query, initial_results, top_k=3)

        print("Final results (after full pipeline):")
        for i, doc in enumerate(final_results, 1):
            score = doc.metadata.get("rerank_score", 0)
            print(f"{i}. [Score: {score:.4f}]")
            print(f"   {doc.content[:100]}...\n")

    except Exception as e:
        print(f"Error: {e}")


def example_10_hyde_with_retrieval():
    """Example 10: HyDE + retrieval"""
    print("\n=== Example 10: HyDE + Retrieval ===\n")

    try:
        chatbot = Chatbot(provider="openai", model="gpt-3.5-turbo")
        rewriter = QueryRewriter(chatbot=chatbot)

        # Original query
        query = "How does reranking improve RAG?"

        # Generate hypothetical document
        hyde_text = rewriter.hyde(query, document_length="paragraph")

        print(f"Query: {query}\n")
        print("Generated hypothetical document:")
        print(hyde_text)
        print("\n" + "=" * 50)
        print("Now embed this hypothetical document instead of the query")
        print("to find semantically similar real documents.")
        print("=" * 50)

        # In practice, you would:
        # 1. Embed hyde_text
        # 2. Search vector store with this embedding
        # 3. Get better results than searching with original query

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("CRAFT v1.4.0 - Advanced RAG Examples")
    print("=" * 50)

    examples = [
        example_1_hybrid_search_basic,
        example_2_hybrid_search_weighted,
        example_3_reranking_basic,
        example_4_reranking_comparison,
        example_5_query_expansion,
        example_6_query_decomposition,
        example_7_hyde,
        example_8_query_clarification,
        example_9_full_pipeline,
        example_10_hyde_with_retrieval,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nExample error: {str(e)[:100]}")

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNote: Some examples require additional dependencies:")
    print("  pip install 'craft-chatbot[rag,advanced-rag]'")
    print("  pip install 'craft-chatbot[all]'")
