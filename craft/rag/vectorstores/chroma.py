"""ChromaDB vector store implementation."""

import uuid
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from pydantic import Field
from craft.rag.vectorstores.base import VectorStore, VectorStoreConfig, Document


class ChromaConfig(VectorStoreConfig):
    """ChromaDB specific configuration."""

    persist_directory: Optional[str] = Field(default="./chroma_db")
    collection_name: str = Field(default="craft_documents")


class ChromaVectorStore(VectorStore):
    """
    ChromaDB vector store implementation.

    Easy to use, embedded vector database. Perfect for development!
    """

    def __init__(self, config: Optional[ChromaConfig] = None, **kwargs):
        """
        Initialize ChromaDB vector store.

        Args:
            config: ChromaDB configuration
            **kwargs: Additional config parameters
        """
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "chromadb package not installed. "
                "Install with: pip install 'craft-chatbot[rag]'"
            )

        if config is None:
            config = ChromaConfig(**kwargs)
        elif kwargs:
            config = ChromaConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.config.persist_directory,
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": self._get_distance_metric()},
        )

    def _validate_config(self) -> None:
        """Validate ChromaDB configuration."""
        pass  # ChromaDB is very forgiving

    def _get_distance_metric(self) -> str:
        """Map distance metric to ChromaDB format."""
        metric_map = {
            "cosine": "cosine",
            "euclidean": "l2",
            "dot": "ip",  # inner product
        }
        return metric_map.get(self.config.distance_metric, "cosine")

    def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[str]:
        """Add documents to ChromaDB."""
        ids = []
        contents = []
        metadatas = []
        doc_embeddings = []

        for i, doc in enumerate(documents):
            # Generate ID if not provided
            doc_id = doc.id or str(uuid.uuid4())
            ids.append(doc_id)
            contents.append(doc.content)
            metadatas.append(doc.metadata)

            # Use provided embeddings or document's embedding
            if embeddings:
                doc_embeddings.append(embeddings[i])
            elif doc.embedding:
                doc_embeddings.append(doc.embedding)
            else:
                raise ValueError("No embeddings provided for documents")

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=doc_embeddings,
            documents=contents,
            metadatas=metadatas,
        )

        return ids

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for similar documents in ChromaDB."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
        )

        documents = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                doc = Document(
                    id=results["ids"][0][i],
                    content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    score=1.0 - results["distances"][0][i] if results["distances"] else None,
                )
                documents.append(doc)

        return documents

    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents from ChromaDB."""
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception:
            return False

    def get_document(self, id: str) -> Optional[Document]:
        """Get a document by ID from ChromaDB."""
        results = self.collection.get(ids=[id])

        if results["ids"]:
            return Document(
                id=results["ids"][0],
                content=results["documents"][0],
                metadata=results["metadatas"][0] if results["metadatas"] else {},
            )
        return None

    def count(self) -> int:
        """Get total number of documents in ChromaDB."""
        return self.collection.count()

    def clear(self) -> bool:
        """Clear all documents from ChromaDB collection."""
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.config.collection_name)
            self.collection = self.client.create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": self._get_distance_metric()},
            )
            return True
        except Exception:
            return False
