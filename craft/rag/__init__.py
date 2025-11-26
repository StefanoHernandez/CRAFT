"""RAG (Retrieval-Augmented Generation) components."""

__all__ = [
    "chunking",
    "embeddings",
    "retrieval",
    "vectorstores",
    "bm25",
    "hybrid_search",
]

# Core modules
from craft.rag import chunking, embeddings, retrieval, vectorstores

# New hybrid search modules
from craft.rag import bm25, hybrid_search

# Try to import advanced (may fail if BeautifulSoup not installed)
try:
    from craft.rag.advanced import HybridSearch, Reranker, QueryRewriter
    __all__.extend(["HybridSearch", "Reranker", "QueryRewriter"])
except (ImportError, NameError) as e:
    # advanced.py has dependencies that may not be available
    pass
