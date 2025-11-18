"""Retrieval engine for RAG."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from craft.rag.embeddings.base import EmbeddingProvider
from craft.rag.vectorstores.base import VectorStore, Document
from craft.rag.chunking import DocumentChunker, ChunkConfig
from craft.utils.logging import get_logger


class RetrievalConfig(BaseModel):
    """Configuration for retrieval engine."""

    top_k: int = Field(default=5, ge=1)
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    rerank: bool = Field(default=False)
    chunk_config: Optional[ChunkConfig] = None


class RetrievedDocument(BaseModel):
    """A retrieved document with relevance score."""

    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None


class RetrievalEngine:
    """
    RAG retrieval engine.

    Orchestrates embedding, chunking, and vector search.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        config: Optional[RetrievalConfig] = None,
    ):
        """
        Initialize retrieval engine.

        Args:
            embedding_provider: Embedding provider instance
            vector_store: Vector store instance
            config: Retrieval configuration
        """
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.config = config or RetrievalConfig()
        self.chunker = DocumentChunker(self.config.chunk_config)
        self.logger = get_logger("craft.rag.retrieval")

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        chunk: bool = True,
    ) -> List[str]:
        """
        Add documents to the retrieval system.

        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            chunk: Whether to chunk documents

        Returns:
            List of document IDs
        """
        self.logger.info(f"Adding {len(documents)} documents to retrieval system")

        if chunk:
            # Chunk documents
            chunks = self.chunker.chunk_documents(documents, metadatas)
            texts = [chunk.content for chunk in chunks]
            chunk_metadatas = [chunk.metadata for chunk in chunks]
        else:
            texts = documents
            chunk_metadatas = metadatas or [{}] * len(documents)

        # Generate embeddings
        self.logger.debug(f"Generating embeddings for {len(texts)} texts")
        embeddings = self.embedding_provider.embed_texts(texts)

        # Create Document objects
        docs = [
            Document(content=text, metadata=meta)
            for text, meta in zip(texts, chunk_metadatas)
        ]

        # Add to vector store
        doc_ids = self.vector_store.add_documents(docs, embeddings)

        self.logger.info(f"Added {len(doc_ids)} document chunks to vector store")
        return doc_ids

    async def aadd_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        chunk: bool = True,
    ) -> List[str]:
        """Async version of add_documents."""
        self.logger.info(f"Adding {len(documents)} documents to retrieval system (async)")

        if chunk:
            chunks = self.chunker.chunk_documents(documents, metadatas)
            texts = [chunk.content for chunk in chunks]
            chunk_metadatas = [chunk.metadata for chunk in chunks]
        else:
            texts = documents
            chunk_metadatas = metadatas or [{}] * len(documents)

        # Generate embeddings asynchronously
        self.logger.debug(f"Generating embeddings for {len(texts)} texts (async)")
        embeddings = await self.embedding_provider.aembed_texts(texts)

        # Create Document objects
        docs = [
            Document(content=text, metadata=meta)
            for text, meta in zip(texts, chunk_metadatas)
        ]

        # Add to vector store
        doc_ids = self.vector_store.add_documents(docs, embeddings)

        self.logger.info(f"Added {len(doc_ids)} document chunks to vector store")
        return doc_ids

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Query text
            top_k: Number of documents to retrieve (overrides config)
            filter_metadata: Optional metadata filters

        Returns:
            List of retrieved documents with scores
        """
        top_k = top_k or self.config.top_k

        self.logger.debug(f"Retrieving top {top_k} documents for query: {query[:50]}...")

        # Generate query embedding
        query_embedding = self.embedding_provider.embed_text(query)

        # Search vector store
        documents = self.vector_store.search(
            query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        # Convert to RetrievedDocument
        results = []
        for doc in documents:
            # Apply score threshold if configured
            if self.config.score_threshold and doc.score:
                if doc.score < self.config.score_threshold:
                    continue

            results.append(
                RetrievedDocument(
                    content=doc.content,
                    score=doc.score or 0.0,
                    metadata=doc.metadata,
                    source=doc.metadata.get("source"),
                )
            )

        self.logger.info(f"Retrieved {len(results)} documents")
        return results

    async def aretrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedDocument]:
        """Async version of retrieve."""
        top_k = top_k or self.config.top_k

        self.logger.debug(f"Retrieving top {top_k} documents for query (async): {query[:50]}...")

        # Generate query embedding asynchronously
        query_embedding = await self.embedding_provider.aembed_text(query)

        # Search vector store (sync for now, most vector stores don't have async)
        documents = self.vector_store.search(
            query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        # Convert to RetrievedDocument
        results = []
        for doc in documents:
            if self.config.score_threshold and doc.score:
                if doc.score < self.config.score_threshold:
                    continue

            results.append(
                RetrievedDocument(
                    content=doc.content,
                    score=doc.score or 0.0,
                    metadata=doc.metadata,
                    source=doc.metadata.get("source"),
                )
            )

        self.logger.info(f"Retrieved {len(results)} documents (async)")
        return results

    def format_context(self, documents: List[RetrievedDocument]) -> str:
        """
        Format retrieved documents into context string.

        Args:
            documents: Retrieved documents

        Returns:
            Formatted context string
        """
        if not documents:
            return ""

        context_parts = ["Retrieved context:\n"]

        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[Document {i}]")
            if doc.source:
                context_parts.append(f"Source: {doc.source}")
            if doc.score:
                context_parts.append(f"Relevance: {doc.score:.2f}")
            context_parts.append(doc.content)
            context_parts.append("")  # Empty line between documents

        return "\n".join(context_parts)

    def clear(self) -> bool:
        """Clear all documents from the retrieval system."""
        self.logger.info("Clearing all documents from retrieval system")
        return self.vector_store.clear()

    @property
    def document_count(self) -> int:
        """Get total number of documents in the system."""
        return self.vector_store.count()

    def __repr__(self) -> str:
        return (
            f"RetrievalEngine("
            f"embedding={self.embedding_provider.name}, "
            f"vector_store={self.vector_store.name}, "
            f"documents={self.document_count})"
        )
