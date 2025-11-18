"""RAG (Retrieval-Augmented Generation) components."""

from craft.rag.retrieval import RetrievalEngine, RetrievalConfig, RetrievedDocument
from craft.rag.chunking import DocumentChunker, ChunkConfig, ChunkingStrategy

__all__ = [
    "RetrievalEngine",
    "RetrievalConfig",
    "RetrievedDocument",
    "DocumentChunker",
    "ChunkConfig",
    "ChunkingStrategy",
]

# Advanced RAG features (optional)
try:
    from craft.rag.advanced import HybridSearch, Reranker, QueryRewriter
    __all__.extend(["HybridSearch", "Reranker", "QueryRewriter"])
except ImportError:
    pass
