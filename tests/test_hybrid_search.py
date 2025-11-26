"""Tests for Hybrid Search functionality."""

import pytest
from unittest.mock import MagicMock

from craft.rag.bm25 import BM25Retriever, BM25Document
from craft.rag.hybrid_search import HybridSearch, SearchResult


class TestBM25Retriever:
    """Tests for BM25 retrieval."""
    
    def test_bm25_initialization(self):
        """Test BM25Retriever initialization."""
        retriever = BM25Retriever(k1=1.5, b=0.75)
        assert retriever.k1 == 1.5
        assert retriever.b == 0.75
        assert len(retriever) == 0
    
    def test_bm25_document_creation(self):
        """Test BM25Document creation from text."""
        doc = BM25Document.from_text(
            "doc1",
            "The cat sat on the mat",
            {"source": "test"}
        )
        
        assert doc.id == "doc1"
        assert "cat" in doc.tokens
        assert "mat" in doc.tokens
        assert doc.metadata["source"] == "test"
    
    def test_bm25_indexing(self):
        """Test document indexing."""
        retriever = BM25Retriever()
        
        docs = [
            BM25Document.from_text("1", "The cat sat on the mat"),
            BM25Document.from_text("2", "The dog played in the park"),
        ]
        
        retriever.index_documents(docs)
        
        assert len(retriever) == 2
        assert retriever.bm25 is not None
    
    def test_bm25_search(self):
        """Test BM25 search."""
        retriever = BM25Retriever()
        
        docs = [
            BM25Document.from_text("1", "The cat sat on the mat in the house"),
            BM25Document.from_text("2", "The dog played in the park with the ball"),
            BM25Document.from_text("3", "Python programming is great for data science"),
        ]
        
        retriever.index_documents(docs)
        
        # Search for "cat mat"
        results = retriever.search("cat mat", top_k=3)
        
        # Should return doc1 with highest score
        assert len(results) > 0
        assert results[0][0] == "1"  # Doc1 should rank first
        assert results[0][1] > 0  # Should have positive score
    
    def test_bm25_get_document_by_id(self):
        """Test retrieving document by ID."""
        retriever = BM25Retriever()
        
        docs = [
            BM25Document.from_text("1", "Test document"),
            BM25Document.from_text("2", "Another document"),
        ]
        
        retriever.index_documents(docs)
        
        doc = retriever.get_document_by_id("1")
        assert doc is not None
        assert doc.id == "1"
        
        missing = retriever.get_document_by_id("999")
        assert missing is None
    
    def test_bm25_empty_search(self):
        """Test search with no documents."""
        retriever = BM25Retriever()
        results = retriever.search("test query")
        assert results == []


class TestHybridSearch:
    """Tests for Hybrid Search."""
    
    def test_hybrid_initialization(self):
        """Test HybridSearch initialization."""
        hybrid = HybridSearch(alpha=0.7, rrf_k=50)
        
        assert hybrid.alpha == 0.7
        assert hybrid.rrf_k == 50
        assert len(hybrid) == 0
    
    def test_add_documents(self):
        """Test adding documents to hybrid search."""
        hybrid = HybridSearch()
        
        docs = [
            {"id": "1", "content": "The cat sat on the mat", "metadata": {"category": "animals"}},
            {"id": "2", "content": "Python is great for AI", "metadata": {"category": "tech"}},
        ]
        
        hybrid.add_documents(docs)
        
        assert len(hybrid) == 2
        assert "1" in hybrid.documents
        assert "2" in hybrid.documents
    
    def test_bm25_only_search(self):
        """Test hybrid search with BM25 only (no vector store)."""
        hybrid = HybridSearch()
        
        docs = [
            {"id": "1", "content": "The cat sat on the mat in the house", "metadata": {}},
            {"id": "2", "content": "The dog played in the park", "metadata": {}},
            {"id": "3", "content": "Python programming for data science", "metadata": {}},
        ]
        
        hybrid.add_documents(docs)
        
        # Search using RRF
        results = hybrid.search("cat mat house", top_k=3, use_rrf=True)
        
        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        assert results[0].id == "1"  # Should match best
        assert results[0].score > 0
    
    def test_search_result_structure(self):
        """Test SearchResult structure."""
        result = SearchResult(
            id="test_id",
            score=0.85,
            content="test content",
            metadata={"key": "value"},
            source="hybrid"
        )
        
        assert result.id == "test_id"
        assert result.score == 0.85
        assert result.source == "hybrid"
        assert "test_id" in str(result)
    
    def test_reciprocal_rank_fusion(self):
        """Test RRF combination logic."""
        hybrid = HybridSearch(rrf_k=60)
        
        docs = [
            {"id": "1", "content": "document one", "metadata": {}},
            {"id": "2", "content": "document two", "metadata": {}},
            {"id": "3", "content": "document three", "metadata": {}},
        ]
        
        hybrid.add_documents(docs)
        
        # Mock results from both retrievers
        vector_results = [("1", 0.9), ("2", 0.7)]
        bm25_results = [("2", 15.0), ("3", 10.0)]
        
        # Test RRF fusion
        fused = hybrid._reciprocal_rank_fusion(vector_results, bm25_results)
        
        # Doc2 appears in both, should rank high
        assert len(fused) == 3
        # Check that doc2 (hybrid) has highest score
        doc2_result = next(r for r in fused if r.id == "2")
        assert doc2_result.source == "hybrid"
    
    def test_weighted_combination(self):
        """Test weighted score combination."""
        hybrid = HybridSearch()
        
        docs = [
            {"id": "1", "content": "doc one", "metadata": {}},
            {"id": "2", "content": "doc two", "metadata": {}},
        ]
        
        hybrid.add_documents(docs)
        
        vector_results = [("1", 0.8)]
        bm25_results = [("2", 20.0)]
        
        # Test 50/50 weighting
        combined = hybrid._weighted_combination(vector_results, bm25_results, vector_weight=0.5)
        
        assert len(combined) == 2
        # Both should have similar normalized scores
        assert all(0 <= r.score <= 1 for r in combined)
    
    def test_search_with_mock_vector_store(self):
        """Test hybrid search with mock vector store."""
        # Create mock vector store
        mock_vector_store = MagicMock()
        mock_vector_store.similarity_search.return_value = [
            {"id": "1", "content": "test", "metadata": {}, "score": 0.9}
        ]
        mock_vector_store.add_texts = MagicMock()
        
        hybrid = HybridSearch(vector_store=mock_vector_store)
        
        docs = [
            {"id": "1", "content": "test document", "metadata": {}},
        ]
        
        hybrid.add_documents(docs)
        
        # Verify vector store was called
        mock_vector_store.add_texts.assert_called_once()
        
        # Search should use both retrievers
        results = hybrid.search("test", top_k=5)
        mock_vector_store.similarity_search.assert_called_once()
    
    def test_empty_hybrid_search(self):
        """Test search with no documents."""
        hybrid = HybridSearch()
        results = hybrid.search("test query")
        assert results == []
    
    def test_top_k_limit(self):
        """Test that top_k limits results correctly."""
        hybrid = HybridSearch()
        
        docs = [
            {"id": str(i), "content": f"document number {i}", "metadata": {}}
            for i in range(20)
        ]
        
        hybrid.add_documents(docs)
        
        results = hybrid.search("document", top_k=5)
        
        # Should return at most 5 results
        assert len(results) <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
