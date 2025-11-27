"""Advanced RAG features: hybrid search, reranking, query rewriting."""

from typing import Any, Dict, List, Optional, Union
from craft.loaders.base import Document

# Optional imports for advanced features
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

try:
    from flashrank import Ranker, RerankRequest
    FLASHRANK_AVAILABLE = True
except ImportError:
    FLASHRANK_AVAILABLE = False


class HybridSearch:
    """
    Hybrid search combining dense (vector) and sparse (BM25) retrieval.

    Uses Reciprocal Rank Fusion (RRF) to combine results from both methods.

    Example:
        >>> from craft.rag import HybridSearch
        >>> from craft.rag.retriever import VectorRetriever
        >>>
        >>> # Setup vector retriever
        >>> vector_retriever = VectorRetriever(vector_store=chroma_store)
        >>>
        >>> # Create hybrid search
        >>> hybrid = HybridSearch(vector_retriever=vector_retriever)
        >>>
        >>> # Add documents to BM25 index
        >>> hybrid.add_documents(documents)
        >>>
        >>> # Search with both dense and sparse
        >>> results = hybrid.search("What is RAG?", k=5)
    """

    def __init__(
        self,
        vector_retriever: Any,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        rrf_k: int = 60
    ):
        """
        Initialize hybrid search.

        Args:
            vector_retriever: Vector-based retriever (VectorRetriever instance)
            bm25_weight: Weight for BM25 scores (0-1)
            vector_weight: Weight for vector scores (0-1)
            rrf_k: Constant for Reciprocal Rank Fusion

        Raises:
            ImportError: If rank-bm25 not installed
        """
        if not BM25_AVAILABLE:
            raise ImportError(
                "rank-bm25 package not installed. "
                "Install with: pip install 'craft-chatbot[advanced-rag]'"
            )

        self.vector_retriever = vector_retriever
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k

        self.bm25_index: Optional[BM25Okapi] = None
        self.documents: List[Document] = []
        self.tokenized_corpus: List[List[str]] = []

    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to BM25 index.

        Args:
            documents: List of documents to index
        """
        self.documents = documents

        # Tokenize documents for BM25
        self.tokenized_corpus = [
            doc.content.lower().split() for doc in documents
        ]

        # Build BM25 index
        self.bm25_index = BM25Okapi(self.tokenized_corpus)

    def search(
        self,
        query: str,
        k: int = 5,
        vector_k: Optional[int] = None,
        bm25_k: Optional[int] = None
    ) -> List[Document]:
        """
        Hybrid search combining vector and BM25.

        Args:
            query: Search query
            k: Final number of results to return
            vector_k: Number of results from vector search (default: k*2)
            bm25_k: Number of results from BM25 (default: k*2)

        Returns:
            List of reranked documents
        """
        if not self.bm25_index:
            raise ValueError("No documents indexed. Call add_documents() first.")

        vector_k = vector_k or k * 2
        bm25_k = bm25_k or k * 2

        # Vector search
        vector_results = self.vector_retriever.retrieve(query, k=vector_k)

        # BM25 search
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25_index.get_scores(tokenized_query)

        # Get top k BM25 results
        bm25_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True
        )[:bm25_k]

        bm25_results = [self.documents[i] for i in bm25_indices]

        # Combine using Reciprocal Rank Fusion
        combined = self._reciprocal_rank_fusion(
            vector_results,
            bm25_results,
            k=k
        )

        return combined

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Document],
        bm25_results: List[Document],
        k: int
    ) -> List[Document]:
        """
        Combine results using Reciprocal Rank Fusion.

        RRF formula: score(d) = sum(1 / (k + rank(d)))
        """
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        # Add vector results
        for rank, doc in enumerate(vector_results):
            doc_id = doc.content[:100]  # Use content prefix as ID
            scores[doc_id] = scores.get(doc_id, 0) + self.vector_weight / (self.rrf_k + rank + 1)
            doc_map[doc_id] = doc

        # Add BM25 results
        for rank, doc in enumerate(bm25_results):
            doc_id = doc.content[:100]
            scores[doc_id] = scores.get(doc_id, 0) + self.bm25_weight / (self.rrf_k + rank + 1)
            doc_map[doc_id] = doc

        # Sort by combined score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

        return [doc_map[doc_id] for doc_id, _ in ranked]


class Reranker:
    """
    Rerank search results using cross-encoder models.

    Uses FlashRank for fast, efficient reranking without GPU.

    Example:
        >>> from craft.rag import Reranker
        >>>
        >>> reranker = Reranker(model="ms-marco-MiniLM-L-12-v2")
        >>>
        >>> # Rerank search results
        >>> reranked = reranker.rerank(
        ...     query="What is machine learning?",
        ...     documents=search_results,
        ...     top_k=5
        ... )
    """

    def __init__(self, model: str = "ms-marco-MiniLM-L-12-v2", cache_dir: Optional[str] = None):
        """
        Initialize reranker.

        Args:
            model: Reranking model name
            cache_dir: Model cache directory

        Available models:
            - ms-marco-MiniLM-L-12-v2 (default, fast)
            - ms-marco-MultiBERT-L-12 (multilingual)
            - rank-T5-flan (T5-based, high quality)

        Raises:
            ImportError: If flashrank not installed
        """
        if not FLASHRANK_AVAILABLE:
            raise ImportError(
                "flashrank package not installed. "
                "Install with: pip install 'craft-chatbot[advanced-rag]'"
            )

        self.ranker = Ranker(model_name=model, cache_dir=cache_dir)

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None
    ) -> List[Document]:
        """
        Rerank documents based on query relevance.

        Args:
            query: Search query
            documents: List of documents to rerank
            top_k: Number of top results to return (None = all)

        Returns:
            Reranked list of documents
        """
        if not documents:
            return []

        # Prepare passages for reranking
        passages = [
            {"text": doc.content, "meta": doc.metadata}
            for doc in documents
        ]

        # Create rerank request
        rerank_request = RerankRequest(query=query, passages=passages)

        # Rerank
        results = self.ranker.rerank(rerank_request)

        # Sort by score and return top_k
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)

        if top_k:
            sorted_results = sorted_results[:top_k]

        # Reconstruct documents with scores
        reranked_docs = []
        for result in sorted_results:
            # Find original document
            doc = documents[result["index"]]

            # Add reranking score to metadata
            doc.metadata["rerank_score"] = result["score"]
            reranked_docs.append(doc)

        return reranked_docs


class QueryRewriter:
    """
    Rewrite queries using LLM for better retrieval.

    Techniques:
    - Query expansion: Generate multiple variations
    - Query decomposition: Break into sub-queries
    - HyDE (Hypothetical Document Embeddings): Generate hypothetical answer

    Example:
        >>> from craft.chatbot import Chatbot
        >>> from craft.rag import QueryRewriter
        >>>
        >>> chatbot = Chatbot(provider="openai", model="gpt-4o")
        >>> rewriter = QueryRewriter(chatbot=chatbot)
        >>>
        >>> # Expand query
        >>> queries = rewriter.expand_query("What is RAG?", num_queries=3)
        >>> print(queries)
        >>> # ["What is RAG?", "What is Retrieval Augmented Generation?", "How does RAG work?"]
        >>>
        >>> # Generate hypothetical document
        >>> hyde_doc = rewriter.hyde("What is RAG?")
    """

    def __init__(self, chatbot: Any):
        """
        Initialize query rewriter.

        Args:
            chatbot: Chatbot instance to use for rewriting
        """
        self.chatbot = chatbot

    def expand_query(self, query: str, num_queries: int = 3) -> List[str]:
        """
        Expand query into multiple variations.

        Args:
            query: Original query
            num_queries: Number of query variations to generate

        Returns:
            List of query variations (includes original)
        """
        prompt = f"""Generate {num_queries - 1} alternative phrasings of this search query.
The alternatives should capture the same intent but use different wording.

Original query: {query}

Return only the alternative queries, one per line. Do not include the original query."""

        response = self.chatbot.chat(prompt)
        alternatives = [q.strip() for q in response.split("\n") if q.strip()]

        # Include original query
        return [query] + alternatives[:num_queries - 1]

    def decompose_query(self, query: str) -> List[str]:
        """
        Decompose complex query into sub-queries.

        Args:
            query: Complex query to decompose

        Returns:
            List of sub-queries
        """
        prompt = f"""Break down this complex question into simpler sub-questions that, when answered together, would fully answer the original question.

Original question: {query}

Return only the sub-questions, one per line."""

        response = self.chatbot.chat(prompt)
        sub_queries = [q.strip() for q in response.split("\n") if q.strip()]

        return sub_queries

    def hyde(self, query: str, document_length: str = "paragraph") -> str:
        """
        Generate hypothetical document (HyDE technique).

        Creates a hypothetical answer that can be embedded and used for retrieval.

        Args:
            query: Query to answer
            document_length: Length of hypothetical document (sentence/paragraph/article)

        Returns:
            Hypothetical document text
        """
        length_prompts = {
            "sentence": "in 1-2 sentences",
            "paragraph": "in a short paragraph",
            "article": "in a detailed explanation"
        }

        length_instruction = length_prompts.get(document_length, "in a short paragraph")

        prompt = f"""Write a hypothetical answer to this question {length_instruction}.
Be specific and factual. Write as if this is an excerpt from a high-quality document.

Question: {query}

Answer:"""

        response = self.chatbot.chat(prompt)
        return response.strip()

    def clarify_query(self, query: str) -> str:
        """
        Clarify ambiguous query.

        Args:
            query: Query to clarify

        Returns:
            Clarified query
        """
        prompt = f"""Rewrite this query to be more specific and clear, resolving any ambiguities.

Original query: {query}

Clarified query:"""

        response = self.chatbot.chat(prompt)
        return response.strip()


__all__ = [
    "HybridSearch",
    "Reranker",
    "QueryRewriter",
    "BM25_AVAILABLE",
    "FLASHRANK_AVAILABLE",
]
