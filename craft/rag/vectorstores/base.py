"""Base vector store interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class Document(BaseModel):
    """Document model for vector stores."""

    id: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    score: Optional[float] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class VectorStoreConfig(BaseModel):
    """Base configuration for vector stores."""

    collection_name: str = Field(default="craft_documents")
    embedding_dimension: Optional[int] = None
    distance_metric: str = Field(default="cosine")  # cosine, euclidean, dot

    model_config = ConfigDict(extra="allow")


class VectorStore(ABC):
    """
    Abstract base class for vector stores.

    All vector store implementations must inherit from this class.
    """

    def __init__(self, config: VectorStoreConfig):
        """
        Initialize vector store.

        Args:
            config: Vector store configuration
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate vector store configuration."""
        pass

    @abstractmethod
    def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[str]:
        """
        Add documents to the vector store.

        Args:
            documents: List of documents to add
            embeddings: Optional pre-computed embeddings

        Returns:
            List of document IDs
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of documents with similarity scores
        """
        pass

    @abstractmethod
    def delete_documents(self, ids: List[str]) -> bool:
        """
        Delete documents by IDs.

        Args:
            ids: List of document IDs to delete

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_document(self, id: str) -> Optional[Document]:
        """
        Get a document by ID.

        Args:
            id: Document ID

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get total number of documents.

        Returns:
            Document count
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all documents from the store.

        Returns:
            True if successful
        """
        pass

    @property
    def name(self) -> str:
        """Get vector store name."""
        return self.__class__.__name__.replace("VectorStore", "").lower()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(collection={self.config.collection_name})"
