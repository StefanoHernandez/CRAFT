"""Query rewriting for improved retrieval.

Query rewriting transforms user queries into better search queries,
improving retrieval recall and precision through:
- Query expansion (adding synonyms, related terms)
- Query reformulation (rephrasing for better matches)
- Multi-query generation (creating multiple search variations)
"""

from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class RewriteStrategy(str, Enum):
    """Query rewriting strategies."""
    
    EXPAND = "expand"              # Add synonyms and related terms
    REFORMULATE = "reformulate"    # Rephrase the query
    MULTI_QUERY = "multi_query"    # Generate multiple query variations
    DECOMPOSE = "decompose"        # Break complex query into sub-queries
    CLARIFY = "clarify"            # Add missing context


@dataclass
class RewrittenQuery:
    """Result from query rewriting."""
    
    original_query: str
    rewritten_query: str
    strategy: RewriteStrategy
    metadata: Dict[str, Any]
    
    def __repr__(self) -> str:
        return f"RewrittenQuery(strategy={self.strategy}, rewritten='{self.rewritten_query}')"


class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """Generate chat completion."""
        ...


class QueryRewriter:
    """
    LLM-based query rewriter for improved retrieval.
    
    Uses an LLM to transform user queries into better search queries,
    improving retrieval quality through various strategies.
    
    Example:
        from craft.rag.query_rewriter import QueryRewriter, RewriteStrategy
        from craft.providers import OpenAIProvider
        
        provider = OpenAIProvider(api_key="...")
        rewriter = QueryRewriter(provider=provider)
        
        # Expand query with synonyms
        result = rewriter.rewrite(
            "How to fix Python bugs",
            strategy=RewriteStrategy.EXPAND
        )
        print(result.rewritten_query)
        # → "How to debug, troubleshoot, and fix Python errors and bugs"
        
        # Generate multiple query variations
        results = rewriter.multi_query(
            "Best practices for microservices",
            num_queries=3
        )
        for r in results:
            print(r.rewritten_query)
    """
    
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7
    ):
        """
        Initialize query rewriter.
        
        Args:
            provider: LLM provider for query rewriting
            model: Model name to use
            temperature: Sampling temperature (0-1)
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
    
    def rewrite(
        self,
        query: str,
        strategy: RewriteStrategy = RewriteStrategy.EXPAND,
        context: Optional[str] = None
    ) -> RewrittenQuery:
        """
        Rewrite query using specified strategy.
        
        Args:
            query: Original user query
            strategy: Rewriting strategy to use
            context: Optional context for clarification
        
        Returns:
            RewrittenQuery with rewritten query
        """
        if not self.provider:
            # Fallback: return original query
            logger.warning("No LLM provider configured, returning original query")
            return RewrittenQuery(
                original_query=query,
                rewritten_query=query,
                strategy=strategy,
                metadata={"fallback": True}
            )
        
        # Get prompt for strategy
        prompt = self._get_prompt(strategy, query, context)
        
        # Call LLM
        messages = [
            {"role": "system", "content": "You are a query rewriting assistant that improves search queries."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.provider.chat(messages, temperature=self.temperature)
            rewritten = response.content.strip()
            
            return RewrittenQuery(
                original_query=query,
                rewritten_query=rewritten,
                strategy=strategy,
                metadata={"model": self.model}
            )
        
        except Exception as e:
            logger.error(f"Query rewriting failed: {e}")
            return RewrittenQuery(
                original_query=query,
                rewritten_query=query,
                strategy=strategy,
                metadata={"error": str(e), "fallback": True}
            )
    
    def multi_query(
        self,
        query: str,
        num_queries: int = 3,
        context: Optional[str] = None
    ) -> List[RewrittenQuery]:
        """
        Generate multiple query variations.
        
        This is particularly useful for improving recall by searching
        with multiple formulations of the same question.
        
        Args:
            query: Original query
            num_queries: Number of variations to generate
            context: Optional context
        
        Returns:
            List of RewrittenQuery objects
        """
        if not self.provider:
            logger.warning("No LLM provider, returning original query")
            return [RewrittenQuery(
                original_query=query,
                rewritten_query=query,
                strategy=RewriteStrategy.MULTI_QUERY,
                metadata={"fallback": True}
            )]
        
        prompt = f"""Generate {num_queries} different ways to search for the following query.
Make them diverse but semantically equivalent.
Return only the queries, one per line, without numbering.

Original query: {query}"""
        
        if context:
            prompt += f"\nContext: {context}"
        
        messages = [
            {"role": "system", "content": "You are a query variation generator for search systems."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.provider.chat(messages, temperature=self.temperature)
            lines = [line.strip() for line in response.content.strip().split('\n') if line.strip()]
            
            # Remove numbering if present
            cleaned_queries = []
            for line in lines:
                # Remove "1. ", "2. ", etc.
                import re
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                if cleaned:
                    cleaned_queries.append(cleaned)
            
            results = []
            for rewritten in cleaned_queries[:num_queries]:
                results.append(RewrittenQuery(
                    original_query=query,
                    rewritten_query=rewritten,
                    strategy=RewriteStrategy.MULTI_QUERY,
                    metadata={"model": self.model, "total_generated": len(cleaned_queries)}
                ))
            
            return results
        
        except Exception as e:
            logger.error(f"Multi-query generation failed: {e}")
            return [RewrittenQuery(
                original_query=query,
                rewritten_query=query,
                strategy=RewriteStrategy.MULTI_QUERY,
                metadata={"error": str(e), "fallback": True}
            )]
    
    def decompose(
        self,
        query: str,
        context: Optional[str] = None
    ) -> List[RewrittenQuery]:
        """
        Decompose complex query into sub-queries.
        
        Useful for complex questions that require multiple retrieval steps.
        
        Args:
            query: Complex query to decompose
            context: Optional context
        
        Returns:
            List of sub-queries
        """
        if not self.provider:
            return [RewrittenQuery(
                original_query=query,
                rewritten_query=query,
                strategy=RewriteStrategy.DECOMPOSE,
                metadata={"fallback": True}
            )]
        
        prompt = f"""Break down this complex query into simpler sub-queries.
Each sub-query should retrieve information needed to answer the original query.
Return only the sub-queries, one per line, without numbering.

Complex query: {query}"""
        
        if context:
            prompt += f"\nContext: {context}"
        
        messages = [
            {"role": "system", "content": "You are a query decomposition expert."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.provider.chat(messages, temperature=0.5)
            lines = [line.strip() for line in response.content.strip().split('\n') if line.strip()]
            
            # Clean numbering
            import re
            sub_queries = []
            for line in lines:
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                if cleaned:
                    sub_queries.append(RewrittenQuery(
                        original_query=query,
                        rewritten_query=cleaned,
                        strategy=RewriteStrategy.DECOMPOSE,
                        metadata={"model": self.model, "is_sub_query": True}
                    ))
            
            return sub_queries if sub_queries else [RewrittenQuery(
                original_query=query,
                rewritten_query=query,
                strategy=RewriteStrategy.DECOMPOSE,
                metadata={"fallback": True}
            )]
        
        except Exception as e:
            logger.error(f"Query decomposition failed: {e}")
            return [RewrittenQuery(
                original_query=query,
                rewritten_query=query,
                strategy=RewriteStrategy.DECOMPOSE,
                metadata={"error": str(e), "fallback": True}
            )]
    
    def _get_prompt(
        self,
        strategy: RewriteStrategy,
        query: str,
        context: Optional[str] = None
    ) -> str:
        """Get prompt for rewriting strategy."""
        prompts = {
            RewriteStrategy.EXPAND: f"""Expand this search query by adding relevant synonyms, related terms, and key concepts.
Keep it concise but comprehensive.

Original query: {query}

Return only the expanded query, nothing else.""",
            
            RewriteStrategy.REFORMULATE: f"""Reformulate this query to make it more effective for search.
Make it clearer, more specific, and better structured.

Original query: {query}

Return only the reformulated query, nothing else.""",
            
            RewriteStrategy.CLARIFY: f"""Add missing context and clarify this query to make it more explicit.
Fill in implicit assumptions and make the intent clearer.

Original query: {query}

Return only the clarified query, nothing else.""",
        }
        
        prompt = prompts.get(strategy, prompts[RewriteStrategy.EXPAND])
        
        if context:
            prompt += f"\nContext: {context}"
        
        return prompt


# Rule-based query expansion (no LLM needed)
def expand_with_synonyms(query: str, synonyms: Dict[str, List[str]]) -> str:
    """
    Simple rule-based query expansion with synonyms.
    
    Args:
        query: Original query
        synonyms: Dictionary mapping terms to their synonyms
    
    Returns:
        Expanded query
    
    Example:
        synonyms = {
            "bug": ["error", "defect", "issue"],
            "fix": ["resolve", "repair", "debug"]
        }
        
        expanded = expand_with_synonyms("fix bug", synonyms)
        # → "fix resolve repair debug bug error defect issue"
    """
    words = query.lower().split()
    expanded = list(words)
    
    for word in words:
        if word in synonyms:
            expanded.extend(synonyms[word])
    
    return " ".join(expanded)


if __name__ == "__main__":
    # Demo with mock provider
    class MockProvider:
        def chat(self, messages, **kwargs):
            class Response:
                content = "How to debug, troubleshoot, and resolve Python errors, bugs, and defects"
            return Response()
    
    # Example 1: Expand query
    rewriter = QueryRewriter(provider=MockProvider())
    result = rewriter.rewrite("fix Python bug", strategy=RewriteStrategy.EXPAND)
    print(f"Original: {result.original_query}")
    print(f"Expanded: {result.rewritten_query}")
    print()
    
    # Example 2: Rule-based expansion
    synonyms = {
        "bug": ["error", "defect", "issue"],
        "fix": ["resolve", "repair", "debug"]
    }
    expanded = expand_with_synonyms("fix bug", synonyms)
    print(f"Rule-based expansion: {expanded}")
