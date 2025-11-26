"""BM25 implementation for hybrid search.

BM25 (Best Matching 25) is a ranking function used in information retrieval
that scores documents based on term frequency, inverse document frequency,
and document length normalization.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    BM25Okapi = None


@dataclass
class BM25Document:
    """Document with tokenized content for BM25."""
    
    id: str
    tokens: List[str]
    metadata: Dict[str, Any]
    
    @classmethod
    def from_text(cls, doc_id: str, text: str, metadata: Optional[Dict] = None) -> "BM25Document":
        """
        Create BM25Document from raw text.
        
        Args:
            doc_id: Document identifier
            text: Raw document text
            metadata: Optional metadata dictionary
        
        Returns:
            BM25Document with tokenized content
        """
        # Simple tokenization (lowercase + split)
        tokens = text.lower().split()
        return cls(
            id=doc_id,
            tokens=tokens,
            metadata=metadata or {}
        )


class BM25Retriever:
    """
    BM25-based sparse retrieval for keyword matching.
    
    Uses the rank-bm25 library to provide efficient BM25 ranking.
    BM25 complements vector search by providing precise keyword matching.
    
    Example:
        from craft.rag.bm25 import BM25Retriever, BM25Document
        
        # Create documents
        docs = [
            BM25Document.from_text("1", "The cat sat on the mat", {"source": "a"}),
            BM25Document.from_text("2", "The dog played in the park", {"source": "b"}),
        ]
        
        # Create retriever
        retriever = BM25Retriever()
        retriever.index_documents(docs)
        
        # Search
        results = retriever.search("cat mat", top_k=5)
        for doc_id, score in results:
            print(f"{doc_id}: {score}")
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 retriever.
        
        Args:
            k1: Term frequency saturation parameter (default: 1.5)
                Higher values give more weight to term frequency
            b: Document length normalization parameter (default: 0.75)
                0 = no normalization, 1 = full normalization
        """
        if not HAS_BM25:
            raise ImportError(
                "rank-bm25 is not installed. "
                "Install it with: pip install rank-bm25"
            )
        
        self.k1 = k1
        self.b = b
        self.documents: List[BM25Document] = []
        self.bm25: Optional[BM25Okapi] = None
    
    def index_documents(self, documents: List[BM25Document]) -> None:
        """
        Index documents for BM25 retrieval.
        
        Args:
            documents: List of BM25Document objects to index
        """
        self.documents = documents
        
        # Extract token lists
        tokenized_corpus = [doc.tokens for doc in documents]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(tokenized_corpus)
    
    def search(self, query: str, top_k: int = 10) -> List[tuple[str, float]]:
        """
        Search documents using BM25.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
        
        Returns:
            List of (document_id, score) tuples, sorted by score descending
        """
        if not self.bm25 or not self.documents:
            return []
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        # Return document IDs with scores
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only return docs with positive scores
                results.append((self.documents[idx].id, float(scores[idx])))
        
        return results
    
    def get_document_by_id(self, doc_id: str) -> Optional[BM25Document]:
        """
        Retrieve document by ID.
        
        Args:
            doc_id: Document identifier
        
        Returns:
            BM25Document if found, None otherwise
        """
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None
    
    def __len__(self) -> int:
        """Return number of indexed documents."""
        return len(self.documents)


def simple_tokenize(text: str) -> List[str]:
    """
    Simple tokenization: lowercase and split on whitespace.
    
    For production use, consider more sophisticated tokenization:
    - Remove stopwords
    - Stemming/lemmatization
    - Handle punctuation
    - Language-specific processing
    
    Args:
        text: Input text
    
    Returns:
        List of tokens
    """
    return text.lower().split()


if __name__ == "__main__":
    # Example usage
    docs = [
        BM25Document.from_text(
            "1",
            "The cat sat on the mat in the house",
            {"category": "animals"}
        ),
        BM25Document.from_text(
            "2",
            "The dog played in the park with the ball",
            {"category": "animals"}
        ),
        BM25Document.from_text(
            "3",
            "Python programming language is great for data science",
            {"category": "tech"}
        ),
    ]
    
    retriever = BM25Retriever()
    retriever.index_documents(docs)
    
    query = "cat mat house"
    results = retriever.search(query, top_k=3)
    
    print(f"Query: '{query}'")
    print("\nResults:")
    for doc_id, score in results:
        doc = retriever.get_document_by_id(doc_id)
        print(f"  - Doc {doc_id} (score: {score:.4f}): {' '.join(doc.tokens[:10])}...")
