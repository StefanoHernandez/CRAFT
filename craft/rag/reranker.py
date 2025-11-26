"""Reranking with FlashRank for improved retrieval quality.

Reranking re-scores retrieved documents using cross-encoders to improve
relevance ordering. FlashRank provides ultra-fast, lightweight reranking
without heavy dependencies.
"""

from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
import logging

try:
    from flashrank import Ranker, RerankRequest
    HAS_FLASHRANK = True
except ImportError:
    HAS_FLASHRANK = False
    Ranker = None
    RerankRequest = None


logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """Result from reranking."""
    
    id: str
    text: str
    score: float
    original_score: float
    original_rank: int
    metadata: Dict[str, Any]
    
    def __repr__(self) -> str:
        return f"RerankResult(id='{self.id}', score={self.score:.4f}, original_score={self.original_score:.4f})"


class FlashRankReranker:
    """
    Fast reranker using FlashRank cross-encoders.
    
    FlashRank is ultra-lightweight (~4-34MB models) and runs on CPU
    without PyTorch. Perfect for production deployments.
    
    Example:
        from craft.rag.reranker import FlashRankReranker
        
        # Create reranker
        reranker = FlashRankReranker(model="ms-marco-TinyBERT-L-2-v2")
        
        # Rerank search results
        results = [
            {"id": "1", "text": "Python is great", "score": 0.8},
            {"id": "2", "text": "Python programming rocks", "score": 0.7},
        ]
        
        reranked = reranker.rerank(
            query="Python coding",
            documents=results,
            top_k=5
        )
        
        for result in reranked:
            print(f"{result.id}: {result.score:.4f}")
    """
    
    def __init__(
        self,
        model: Literal[
            "ms-marco-TinyBERT-L-2-v2",  # ~4MB, fast
            "ms-marco-MiniLM-L-12-v2",   # ~34MB, more accurate
            "rank-T5-flan",               # ~84MB, best quality
        ] = "ms-marco-TinyBERT-L-2-v2",
        cache_dir: Optional[str] = None
    ):
        """
        Initialize FlashRank reranker.
        
        Args:
            model: Reranking model to use
                - ms-marco-TinyBERT-L-2-v2: ~4MB, fastest (default)
                - ms-marco-MiniLM-L-12-v2: ~34MB, balanced
                - rank-T5-flan: ~84MB, most accurate
            cache_dir: Optional cache directory for models
        """
        if not HAS_FLASHRANK:
            raise ImportError(
                "flashrank is not installed. "
                "Install it with: pip install flashrank"
            )
        
        self.model_name = model
        self.cache_dir = cache_dir
        
        # Initialize ranker
        logger.info(f"Loading FlashRank model: {model}")
        if cache_dir:
            self.ranker = Ranker(model_name=model, cache_dir=cache_dir)
        else:
            self.ranker = Ranker(model_name=model)
        logger.info(f"FlashRank model loaded successfully")
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        text_field: str = "text"
    ) -> List[RerankResult]:
        """
        Rerank documents based on query relevance.
        
        Args:
            query: Search query
            documents: List of documents with at least 'text' field
                      Each doc should have: id, text, score (optional), metadata (optional)
            top_k: Number of top results to return (None = all)
            text_field: Field name containing document text
        
        Returns:
            List of RerankResult objects, sorted by reranking score descending
        """
        if not documents:
            return []
        
        # Prepare passages for FlashRank
        passages = []
        doc_map = {}
        
        for idx, doc in enumerate(documents):
            doc_id = doc.get("id", str(idx))
            text = doc.get(text_field, "")
            
            if not text:
                logger.warning(f"Document {doc_id} has no text, skipping")
                continue
            
            passages.append({
                "id": doc_id,
                "text": text,
                "meta": {
                    "original_score": doc.get("score", 0.0),
                    "original_rank": idx,
                    "metadata": doc.get("metadata", {})
                }
            })
            
            doc_map[doc_id] = doc
        
        if not passages:
            logger.warning("No valid passages to rerank")
            return []
        
        # Create rerank request
        rerank_request = RerankRequest(
            query=query,
            passages=passages
        )
        
        # Perform reranking
        reranked = self.ranker.rerank(rerank_request)
        
        # Convert to RerankResult objects
        results = []
        for item in reranked:
            doc_id = item["id"]
            meta = item.get("meta", {})
            
            results.append(RerankResult(
                id=doc_id,
                text=item["text"],
                score=item.get("score", 0.0),
                original_score=meta.get("original_score", 0.0),
                original_rank=meta.get("original_rank", 0),
                metadata=meta.get("metadata", {})
            ))
        
        # Apply top_k if specified
        if top_k and top_k > 0:
            results = results[:top_k]
        
        return results
    
    def rerank_hybrid_results(
        self,
        query: str,
        search_results: List[Any],  # From HybridSearch
        top_k: Optional[int] = None
    ) -> List[RerankResult]:
        """
        Rerank results from HybridSearch.
        
        Args:
            query: Search query
            search_results: Results from HybridSearch.search()
            top_k: Number of top results
        
        Returns:
            Reranked results
        """
        # Convert HybridSearch results to document format
        documents = []
        for result in search_results:
            documents.append({
                "id": result.id if hasattr(result, 'id') else str(result),
                "text": result.content if hasattr(result, 'content') else str(result),
                "score": result.score if hasattr(result, 'score') else 0.0,
                "metadata": result.metadata if hasattr(result, 'metadata') else {}
            })
        
        return self.rerank(query, documents, top_k)


def create_reranker(
    model: str = "ms-marco-TinyBERT-L-2-v2",
    cache_dir: Optional[str] = None
) -> FlashRankReranker:
    """
    Helper function to create a FlashRank reranker.
    
    Args:
        model: Reranking model
        cache_dir: Cache directory
    
    Returns:
        FlashRankReranker instance
    """
    return FlashRankReranker(model=model, cache_dir=cache_dir)


if __name__ == "__main__":
    # Example usage
    reranker = FlashRankReranker()
    
    # Sample documents
    docs = [
        {
            "id": "1",
            "text": "Python is a high-level programming language",
            "score": 0.7,
            "metadata": {"source": "wiki"}
        },
        {
            "id": "2",
            "text": "Machine learning with Python is very popular",
            "score": 0.6,
            "metadata": {"source": "blog"}
        },
        {
            "id": "3",
            "text": "Java and C++ are also programming languages",
            "score": 0.5,
            "metadata": {"source": "docs"}
        },
        {
            "id": "4",
            "text": "Deep learning frameworks like PyTorch use Python",
            "score": 0.8,
            "metadata": {"source": "paper"}
        },
    ]
    
    query = "Python programming for machine learning"
    
    print(f"Query: '{query}'\n")
    print("Original ranking:")
    for doc in docs:
        print(f"  {doc['id']}: {doc['score']:.2f} - {doc['text'][:50]}...")
    
    print("\nReranking...")
    results = reranker.rerank(query, docs, top_k=3)
    
    print("\nReranked results (top 3):")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.id}: {result.score:.4f} (was #{result.original_rank + 1}, {result.original_score:.2f})")
        print(f"     {result.text[:60]}...")
