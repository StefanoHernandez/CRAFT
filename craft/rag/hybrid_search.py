"""Hybrid Search combining vector similarity and BM25 sparse retrieval.

Hybrid search leverages both semantic (vector) and keyword (BM25) retrieval
to provide more robust and accurate search results. Results are combined using
Reciprocal Rank Fusion (RRF).
"""

from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass
import logging

from craft.rag.bm25 import BM25Retriever, BM25Document


logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Unified search result from hybrid retrieval."""
    
    id: str
    score: float
    content: str
    metadata: Dict[str, Any]
    source: str  # "vector", "bm25", or "hybrid"
    
    def __repr__(self) -> str:
        return f"SearchResult(id='{self.id}', score={self.score:.4f}, source='{self.source}')"


class VectorStore(Protocol):
    """Protocol for vector store implementations."""
    
    def similarity_search(
        self,
        query: str,
        k: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Returns list of dicts with at least: id, content, metadata, score
        """
        ...


class HybridSearch:
    """
    Hybrid search combining vector similarity and BM25 keyword matching.
    
    Uses Reciprocal Rank Fusion (RRF) to combine results from both retrievers.
    RRF formula: score(d) = Σ 1 / (rank(d) + k) where k=60 is standard.
    
    Example:
        from craft.rag.hybrid_search import HybridSearch
        from craft.rag.vectorstores import FAISSVectorStore
        from craft.rag.embeddings import OpenAIEmbeddings
        
        # Setup
        embeddings = OpenAIEmbeddings()
        vector_store = FAISSVectorStore(embeddings)
        
        hybrid = HybridSearch(
            vector_store=vector_store,
            alpha=0.5  # Equal weight to vector and BM25
        )
        
        # Add documents
        hybrid.add_documents([
            {"id": "1", "content": "The cat sat on the mat", "metadata": {}},
            {"id": "2", "content": "Python is great for AI", "metadata": {}}
        ])
        
        # Search
        results = hybrid.search("cat on mat", top_k=5)
        for result in results:
            print(f"{result.id}: {result.score:.4f} ({result.source})")
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        alpha: float = 0.5,
        rrf_k: int = 60
    ):
        """
        Initialize hybrid search.
        
        Args:
            vector_store: Vector store for semantic search (optional)
            bm25_retriever: BM25 retriever for keyword search (optional)
            alpha: Weight for combining scores (0-1):
                   0 = only BM25, 1 = only vector, 0.5 = equal weight
                   Only used when NOT using RRF
            rrf_k: Constant for Reciprocal Rank Fusion (default: 60)
                   Higher values give more weight to lower-ranked items
        """
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever or BM25Retriever()
        self.alpha = alpha
        self.rrf_k = rrf_k
        
        # Track indexed documents
        self.documents: Dict[str, Dict[str, Any]] = {}
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to both retrievers.
        
        Args:
            documents: List of dicts with keys: id, content, metadata
        """
        # Store documents
        for doc in documents:
            self.documents[doc["id"]] = doc
        
        # Index in vector store
        if self.vector_store:
            # Assuming vector store has an add_texts method
            texts = [doc["content"] for doc in documents]
            metadatas = [{"id": doc["id"], **doc.get("metadata", {})} for doc in documents]
            
            if hasattr(self.vector_store, "add_texts"):
                self.vector_store.add_texts(texts, metadatas=metadatas)
            else:
                logger.warning("Vector store doesn't have add_texts method, skipping vector indexing")
        
        # Index in BM25
        bm25_docs = [
            BM25Document.from_text(
                doc_id=doc["id"],
                text=doc["content"],
                metadata=doc.get("metadata", {})
            )
            for doc in documents
        ]
        self.bm25_retriever.index_documents(bm25_docs)
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        use_rrf: bool = True,
        vector_weight: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Hybrid search combining vector and BM25.
        
        Args:
            query: Search query
            top_k: Number of results to return
            use_rrf: If True, use Recipr ocal Rank Fusion. If False, use weighted combination.
            vector_weight: Override alpha for this query (0-1)
        
        Returns:
            List of SearchResult objects, sorted by score descending
        """
        # Get results from both retrievers
        vector_results = self._vector_search(query, top_k * 2)  # Get more for fusion
        bm25_results = self._bm25_search(query, top_k * 2)
        
        # Combine results
        if use_rrf:
            combined_results = self._reciprocal_rank_fusion(
                vector_results=vector_results,
                bm25_results=bm25_results
            )
        else:
            weight = vector_weight if vector_weight is not None else self.alpha
            combined_results = self._weighted_combination(
                vector_results=vector_results,
                bm25_results=bm25_results,
                vector_weight=weight
            )
        
        # Return top-k
        return combined_results[:top_k]
    
    def _vector_search(self, query: str, top_k: int) -> List[tuple[str, float]]:
        """
        Perform vector similarity search.
        
        Returns:
            List of (doc_id, score) tuples
        """
        if not self.vector_store:
            return []
        
        try:
            results = self.vector_store.similarity_search(query, k=top_k)
            return [(r.get("id") or r.get("metadata", {}).get("id"), r.get("score", 0.0)) for r in results]
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []
    
    def _bm25_search(self, query: str, top_k: int) -> List[tuple[str, float]]:
        """
        Perform BM25 keyword search.
        
        Returns:
            List of (doc_id, score) tuples
        """
        try:
            return self.bm25_retriever.search(query, top_k=top_k)
        except Exception as e:
            logger.warning(f"BM25 search failed: {e}")
            return []
    
    def _reciprocal_rank_fusion(
        self,
        vector_results: List[tuple[str, float]],
        bm25_results: List[tuple[str, float]]
    ) -> List[SearchResult]:
        """
        Combine results using Reciprocal Rank Fusion (RRF).
        
        RRF formula: score(d) = Σ 1 / (rank(d) + k)
        
        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
        
        Returns:
            Fused and sorted results
        """
        rrf_scores: Dict[str, float] = {}
        sources: Dict[str, str] = {}
        
        # Add vector scores
        for rank, (doc_id, _) in enumerate(vector_results, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1 / (rank + self.rrf_k)
            if doc_id not in sources:
                sources[doc_id] = "vector"
            elif sources[doc_id] == "bm25":
                sources[doc_id] = "hybrid"
        
        # Add BM25 scores
        for rank, (doc_id, _) in enumerate(bm25_results, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1 / (rank + self.rrf_k)
            if doc_id not in sources:
                sources[doc_id] = "bm25"
            elif sources[doc_id] == "vector":
                sources[doc_id] = "hybrid"
        
        # Convert to SearchResult objects
        results = []
        for doc_id, score in rrf_scores.items():
            if doc_id in self.documents:
                doc = self.documents[doc_id]
                results.append(SearchResult(
                    id=doc_id,
                    score=score,
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                    source=sources[doc_id]
                ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _weighted_combination(
        self,
        vector_results: List[tuple[str, float]],
        bm25_results: List[tuple[str, float]],
        vector_weight: float
    ) -> List[SearchResult]:
        """
        Combine results using weighted score combination.
        
        Final score = vector_weight * vector_score + (1 - vector_weight) * bm25_score
        
        Scores are normalized to [0, 1] before combining.
        
        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
            vector_weight: Weight for vector scores (0-1)
        
        Returns:
            Combined and sorted results
        """
        combined_scores: Dict[str, float] = {}
        sources: Dict[str, str] = {}
        
        # Normalize and add vector scores
        if vector_results:
            max_vector_score = max(score for _, score in vector_results)
            for doc_id, score in vector_results:
                normalized_score = score / max_vector_score if max_vector_score > 0 else 0
                combined_scores[doc_id] = vector_weight * normalized_score
                sources[doc_id] = "vector"
        
        # Normalize and add BM25 scores
        if bm25_results:
            max_bm25_score = max(score for _, score in bm25_results)
            for doc_id, score in bm25_results:
                normalized_score = score / max_bm25_score if max_bm25_score > 0 else 0
                bm25_contribution = (1 - vector_weight) * normalized_score
                
                if doc_id in combined_scores:
                    combined_scores[doc_id] += bm25_contribution
                    sources[doc_id] = "hybrid"
                else:
                    combined_scores[doc_id] = bm25_contribution
                    sources[doc_id] = "bm25"
        
        # Convert to SearchResult objects
        results = []
        for doc_id, score in combined_scores.items():
            if doc_id in self.documents:
                doc = self.documents[doc_id]
                results.append(SearchResult(
                    id=doc_id,
                    score=score,
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                    source=sources[doc_id]
                ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def __len__(self) -> int:
        """Return number of indexed documents."""
        return len(self.documents)


if __name__ == "__main__":
    # Example usage without vector store (BM25 only for demonstration)
    hybrid = HybridSearch()
    
    # Add documents
    docs = [
        {"id": "1", "content": "The cat sat on the mat in the house", "metadata": {"category": "animals"}},
        {"id": "2", "content": "The dog played in the park with the ball", "metadata": {"category": "animals"}},
        {"id": "3", "content": "Python programming is great for data science and AI", "metadata": {"category": "tech"}},
        {"id": "4", "content": "Machine learning models need large datasets", "metadata": {"category": "tech"}},
    ]
    
    hybrid.add_documents(docs)
    
    # Search
    query = "cat on mat"
    results = hybrid.search(query, top_k=3, use_rrf=True)
    
    print(f"Hybrid Search Results for: '{query}'\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.id} (score: {result.score:.4f}, source: {result.source})")
        print(f"   Content: {result.content}")
        print()
