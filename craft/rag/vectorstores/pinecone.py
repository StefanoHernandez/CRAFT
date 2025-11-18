"""Pinecone vector store implementation."""

import uuid
import os
from typing import Any, Dict, List, Optional

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

from pydantic import Field
from craft.rag.vectorstores.base import VectorStore, VectorStoreConfig, Document


class PineconeConfig(VectorStoreConfig):
    """Pinecone specific configuration."""

    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("PINECONE_API_KEY"))
    environment: str = Field(default="us-east-1-aws")
    index_name: str = Field(default="craft-index")
    namespace: str = Field(default="")


class PineconeVectorStore(VectorStore):
    """
    Pinecone vector store implementation.

    Cloud-based, scalable vector database. Great for production!
    """

    def __init__(self, config: Optional[PineconeConfig] = None, **kwargs):
        """
        Initialize Pinecone vector store.

        Args:
            config: Pinecone configuration
            **kwargs: Additional config parameters
        """
        if not PINECONE_AVAILABLE:
            raise ImportError(
                "pinecone package not installed. "
                "Install with: pip install 'craft-chatbot[rag]'"
            )

        if config is None:
            config = PineconeConfig(**kwargs)
        elif kwargs:
            config = PineconeConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.config.api_key)

        # Get or create index
        if self.config.index_name not in self.pc.list_indexes().names():
            if not self.config.embedding_dimension:
                raise ValueError("embedding_dimension required to create new Pinecone index")

            self.pc.create_index(
                name=self.config.index_name,
                dimension=self.config.embedding_dimension,
                metric=self._get_distance_metric(),
                spec=ServerlessSpec(cloud="aws", region=self.config.environment),
            )

        self.index = self.pc.Index(self.config.index_name)

    def _validate_config(self) -> None:
        """Validate Pinecone configuration."""
        if not self.config.api_key:
            raise ValueError(
                "Pinecone API key not provided. "
                "Set PINECONE_API_KEY environment variable or pass api_key parameter."
            )

    def _get_distance_metric(self) -> str:
        """Map distance metric to Pinecone format."""
        metric_map = {
            "cosine": "cosine",
            "euclidean": "euclidean",
            "dot": "dotproduct",
        }
        return metric_map.get(self.config.distance_metric, "cosine")

    def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[str]:
        """Add documents to Pinecone."""
        vectors = []

        for i, doc in enumerate(documents):
            # Generate ID if not provided
            doc_id = doc.id or str(uuid.uuid4())

            # Get embedding
            if embeddings:
                embedding = embeddings[i]
            elif doc.embedding:
                embedding = doc.embedding
            else:
                raise ValueError("No embeddings provided for documents")

            # Prepare vector for Pinecone
            metadata = {
                **doc.metadata,
                "content": doc.content,  # Store content in metadata
            }

            vectors.append({
                "id": doc_id,
                "values": embedding,
                "metadata": metadata,
            })

        # Upsert to Pinecone
        self.index.upsert(
            vectors=vectors,
            namespace=self.config.namespace,
        )

        return [v["id"] for v in vectors]

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for similar documents in Pinecone."""
        # Prepare filter (remove 'content' as it's not a filterable field)
        filter_dict = None
        if filter_metadata:
            filter_dict = {k: v for k, v in filter_metadata.items() if k != "content"}

        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=self.config.namespace,
            filter=filter_dict if filter_dict else None,
        )

        documents = []
        for match in results.matches:
            metadata = dict(match.metadata)
            content = metadata.pop("content", "")

            doc = Document(
                id=match.id,
                content=content,
                metadata=metadata,
                score=float(match.score),
            )
            documents.append(doc)

        return documents

    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents from Pinecone."""
        try:
            self.index.delete(
                ids=ids,
                namespace=self.config.namespace,
            )
            return True
        except Exception:
            return False

    def get_document(self, id: str) -> Optional[Document]:
        """Get a document by ID from Pinecone."""
        results = self.index.fetch(
            ids=[id],
            namespace=self.config.namespace,
        )

        if id in results.vectors:
            vector_data = results.vectors[id]
            metadata = dict(vector_data.metadata)
            content = metadata.pop("content", "")

            return Document(
                id=id,
                content=content,
                metadata=metadata,
            )
        return None

    def count(self) -> int:
        """Get total number of documents in Pinecone."""
        stats = self.index.describe_index_stats()
        return stats.total_vector_count

    def clear(self) -> bool:
        """Clear all documents from Pinecone namespace."""
        try:
            self.index.delete(
                delete_all=True,
                namespace=self.config.namespace,
            )
            return True
        except Exception:
            return False
