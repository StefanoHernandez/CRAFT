"""FAISS vector store implementation."""

import uuid
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from pydantic import Field
from craft.rag.vectorstores.base import VectorStore, VectorStoreConfig, Document


class FAISSConfig(VectorStoreConfig):
    """FAISS specific configuration."""

    index_path: Optional[str] = Field(default="./faiss_index")
    index_type: str = Field(default="Flat")  # Flat, IVFFlat, HNSW


class FAISSVectorStore(VectorStore):
    """
    FAISS vector store implementation.

    Fast similarity search library by Facebook. Great for local use!
    """

    def __init__(self, config: Optional[FAISSConfig] = None, **kwargs):
        """
        Initialize FAISS vector store.

        Args:
            config: FAISS configuration
            **kwargs: Additional config parameters
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "faiss package not installed. "
                "Install with: pip install 'craft-chatbot[rag]'"
            )

        if config is None:
            config = FAISSConfig(**kwargs)
        elif kwargs:
            config = FAISSConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        # Storage for documents and metadata
        self.documents: Dict[str, Document] = {}
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}

        # Initialize or load index
        self.index = None
        self.dimension = config.embedding_dimension
        self._load_or_create_index()

    def _validate_config(self) -> None:
        """Validate FAISS configuration."""
        if not self.config.embedding_dimension:
            raise ValueError("embedding_dimension is required for FAISS")

    def _load_or_create_index(self) -> None:
        """Load existing index or create new one."""
        index_file = Path(self.config.index_path) / f"{self.config.collection_name}.index"
        metadata_file = Path(self.config.index_path) / f"{self.config.collection_name}.pkl"

        if index_file.exists() and metadata_file.exists():
            # Load existing index
            self.index = faiss.read_index(str(index_file))
            with open(metadata_file, "rb") as f:
                data = pickle.load(f)
                self.documents = data["documents"]
                self.id_to_index = data["id_to_index"]
                self.index_to_id = data["index_to_id"]
        else:
            # Create new index
            if self.config.index_type == "Flat":
                self.index = faiss.IndexFlatL2(self.dimension)
            elif self.config.index_type == "IVFFlat":
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            elif self.config.index_type == "HNSW":
                self.index = faiss.IndexHNSWFlat(self.dimension, 32)
            else:
                raise ValueError(f"Unknown index type: {self.config.index_type}")

    def _save_index(self) -> None:
        """Save index and metadata to disk."""
        index_path = Path(self.config.index_path)
        index_path.mkdir(parents=True, exist_ok=True)

        index_file = index_path / f"{self.config.collection_name}.index"
        metadata_file = index_path / f"{self.config.collection_name}.pkl"

        # Save index
        faiss.write_index(self.index, str(index_file))

        # Save metadata
        with open(metadata_file, "wb") as f:
            pickle.dump(
                {
                    "documents": self.documents,
                    "id_to_index": self.id_to_index,
                    "index_to_id": self.index_to_id,
                },
                f,
            )

    def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[str]:
        """Add documents to FAISS index."""
        ids = []
        vectors = []

        for i, doc in enumerate(documents):
            # Generate ID if not provided
            doc_id = doc.id or str(uuid.uuid4())
            ids.append(doc_id)

            # Get embedding
            if embeddings:
                embedding = embeddings[i]
            elif doc.embedding:
                embedding = doc.embedding
            else:
                raise ValueError("No embeddings provided for documents")

            vectors.append(embedding)

            # Store document
            index_pos = self.index.ntotal + i
            self.documents[doc_id] = doc
            self.id_to_index[doc_id] = index_pos
            self.index_to_id[index_pos] = doc_id

        # Add to FAISS index
        vectors_array = np.array(vectors, dtype=np.float32)
        self.index.add(vectors_array)

        # Save to disk
        self._save_index()

        return ids

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for similar documents in FAISS."""
        query_vector = np.array([query_embedding], dtype=np.float32)

        # Search
        distances, indices = self.index.search(query_vector, top_k)

        documents = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:  # No more results
                continue

            doc_id = self.index_to_id.get(int(idx))
            if doc_id and doc_id in self.documents:
                doc = self.documents[doc_id]

                # Apply metadata filter if provided
                if filter_metadata:
                    if not all(
                        doc.metadata.get(k) == v for k, v in filter_metadata.items()
                    ):
                        continue

                # Create result document with score
                result_doc = Document(
                    id=doc.id,
                    content=doc.content,
                    metadata=doc.metadata,
                    score=1.0 / (1.0 + float(distances[0][i])),  # Convert distance to similarity
                )
                documents.append(result_doc)

        return documents

    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents from FAISS (requires rebuilding index)."""
        try:
            # Remove from metadata
            for doc_id in ids:
                if doc_id in self.documents:
                    idx = self.id_to_index[doc_id]
                    del self.documents[doc_id]
                    del self.id_to_index[doc_id]
                    del self.index_to_id[idx]

            # Rebuild index (FAISS doesn't support deletion)
            if self.documents:
                embeddings = [doc.embedding for doc in self.documents.values()]
                doc_ids = list(self.documents.keys())

                # Reset
                self._load_or_create_index()
                self.documents.clear()
                self.id_to_index.clear()
                self.index_to_id.clear()

                # Re-add
                docs = [self.documents[did] for did in doc_ids]
                self.add_documents(docs, embeddings)

            self._save_index()
            return True
        except Exception:
            return False

    def get_document(self, id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self.documents.get(id)

    def count(self) -> int:
        """Get total number of documents."""
        return self.index.ntotal

    def clear(self) -> bool:
        """Clear all documents from FAISS index."""
        try:
            self.documents.clear()
            self.id_to_index.clear()
            self.index_to_id.clear()
            self._load_or_create_index()
            self._save_index()
            return True
        except Exception:
            return False
