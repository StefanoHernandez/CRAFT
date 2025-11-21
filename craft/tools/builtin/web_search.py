"""Web search tools."""

from typing import List, Dict, Optional
from craft.tools import tool


@tool
def duckduckgo_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo.

    Args:
        query: Search query
        max_results: Maximum number of results to return (default: 5)

    Returns:
        List of search results with title, url, and snippet
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        raise ImportError(
            "duckduckgo-search not installed. "
            "Install with: pip install duckduckgo-search"
        )

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
                for r in results
            ]
    except Exception as e:
        raise RuntimeError(f"DuckDuckGo search failed: {e}")


@tool
def google_search(
    query: str, max_results: int = 5, api_key: Optional[str] = None, cx: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Search the web using Google Custom Search API.

    Args:
        query: Search query
        max_results: Maximum number of results to return (default: 5)
        api_key: Google API key (optional, can be set via GOOGLE_API_KEY env var)
        cx: Custom Search Engine ID (optional, can be set via GOOGLE_CSE_ID env var)

    Returns:
        List of search results with title, url, and snippet
    """
    import os
    import requests

    # Get API credentials
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    cx = cx or os.getenv("GOOGLE_CSE_ID")

    if not api_key or not cx:
        raise ValueError(
            "Google API key and Custom Search Engine ID required. "
            "Set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables or pass as arguments."
        )

    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": api_key, "cx": cx, "q": query, "num": min(max_results, 10)}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        return [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
            for item in items[:max_results]
        ]
    except requests.RequestException as e:
        raise RuntimeError(f"Google search failed: {e}")
