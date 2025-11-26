"""Property-based tests for FlashRankReranker."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import MagicMock, patch

from craft.rag.reranker import FlashRankReranker, RerankResult

# Mock FlashRank to avoid loading models
@pytest.fixture
def mock_ranker():
    with patch("craft.rag.reranker.Ranker") as MockRanker:
        ranker_instance = MockRanker.return_value
        
        # Mock rerank to return input passages with random scores
        def side_effect(request):
            results = []
            for i, passage in enumerate(request.passages):
                # Deterministic pseudo-random score based on length and index
                score = len(passage["text"]) * 0.1 + i * 0.01
                results.append({
                    "id": passage["id"],
                    "text": passage["text"],
                    "score": score,
                    "meta": passage.get("meta", {})
                })
            # Sort by score descending as the real ranker would (mostly)
            results.sort(key=lambda x: x["score"], reverse=True)
            return results
            
        ranker_instance.rerank.side_effect = side_effect
        yield MockRanker

@given(
    st.lists(
        st.fixed_dictionaries({
            "id": st.text(min_size=1),
            "text": st.text(min_size=1),
            "score": st.floats(min_value=0.0, max_value=1.0),
            "metadata": st.dictionaries(st.text(), st.text())
        }),
        min_size=0,
        max_size=20
    ),
    st.one_of(st.none(), st.integers(min_value=1, max_value=20))
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_rerank_properties(mock_ranker, documents, top_k):
    """Test properties of reranking."""
    reranker = FlashRankReranker()
    
    # Perform reranking
    results = reranker.rerank("query", documents, top_k=top_k)
    
    # 1. Output type check
    assert isinstance(results, list)
    assert all(isinstance(r, RerankResult) for r in results)
    
    # 2. Output length check
    expected_len = len(documents)
    if top_k is not None:
        expected_len = min(expected_len, top_k)
    assert len(results) == expected_len
    
    # 3. Score ordering check (descending)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    
    # 4. Data preservation check
    # All result IDs should be in input documents
    input_ids = {d["id"] for d in documents}
    result_ids = {r.id for r in results}
    assert result_ids.issubset(input_ids)

@given(st.lists(st.integers(), min_size=0, max_size=10))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_empty_input(mock_ranker, empty_list):
    """Test handling of empty input."""
    reranker = FlashRankReranker()
    results = reranker.rerank("query", [])
    assert results == []

def test_rerank_idempotency(mock_ranker):
    """Test that reranking is idempotent (deterministic given same mock)."""
    reranker = FlashRankReranker()
    docs = [
        {"id": "1", "text": "A"},
        {"id": "2", "text": "B"}
    ]
    
    results1 = reranker.rerank("query", docs)
    results2 = reranker.rerank("query", docs)
    
    assert len(results1) == len(results2)
    for r1, r2 in zip(results1, results2):
        assert r1.id == r2.id
        assert r1.score == r2.score
