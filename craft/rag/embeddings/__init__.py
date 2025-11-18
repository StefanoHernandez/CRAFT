"""Embedding providers for RAG."""

from craft.rag.embeddings.base import EmbeddingProvider, EmbeddingConfig

__all__ = [
    "EmbeddingProvider",
    "EmbeddingConfig",
]

# Conditional imports for optional embedding providers
try:
    from craft.rag.embeddings.openai import OpenAIEmbedding
    __all__.append("OpenAIEmbedding")
except ImportError:
    pass

try:
    from craft.rag.embeddings.sentence_transformer import SentenceTransformerEmbedding
    __all__.append("SentenceTransformerEmbedding")
except ImportError:
    pass
