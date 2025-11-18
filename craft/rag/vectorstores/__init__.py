"""Vector store implementations for RAG."""

from craft.rag.vectorstores.base import VectorStore, VectorStoreConfig, Document

__all__ = [
    "VectorStore",
    "VectorStoreConfig",
    "Document",
]

# Conditional imports for optional vector stores
try:
    from craft.rag.vectorstores.chroma import ChromaVectorStore
    __all__.append("ChromaVectorStore")
except ImportError:
    pass

try:
    from craft.rag.vectorstores.faiss import FAISSVectorStore
    __all__.append("FAISSVectorStore")
except ImportError:
    pass

try:
    from craft.rag.vectorstores.pinecone import PineconeVectorStore
    __all__.append("PineconeVectorStore")
except ImportError:
    pass
