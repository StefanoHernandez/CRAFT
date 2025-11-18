"""Web document loader."""

from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False

from craft.loaders.base import DocumentLoader, Document


class WebLoader(DocumentLoader):
    """
    Web document loader using requests and BeautifulSoup.

    Supports:
    - HTML web pages
    - Automatic text extraction
    - Metadata from HTML tags
    - Custom CSS selectors
    - Multiple URL loading

    Example:
        >>> from craft.loaders import WebLoader
        >>>
        >>> loader = WebLoader()
        >>> documents = loader.load("https://example.com")
        >>> print(documents[0].content[:200])
        >>>
        >>> # Load multiple URLs
        >>> docs = loader.load_batch([
        ...     "https://example.com/page1",
        ...     "https://example.com/page2"
        ... ])
        >>>
        >>> # Extract only article content
        >>> loader = WebLoader(selector="article")
        >>> docs = loader.load("https://blog.example.com/post")
    """

    def __init__(
        self,
        selector: Optional[str] = None,
        remove_tags: Optional[List[str]] = None,
        timeout: int = 30,
        headers: Optional[dict] = None,
        **kwargs
    ):
        """
        Initialize web loader.

        Args:
            selector: CSS selector to extract specific content (None = all text)
            remove_tags: HTML tags to remove (e.g., ['script', 'style'])
            timeout: Request timeout in seconds
            headers: Custom HTTP headers
            **kwargs: Additional loader configuration
        """
        if not WEB_AVAILABLE:
            raise ImportError(
                "requests and beautifulsoup4 packages not installed. "
                "Install with: pip install 'craft-chatbot[loaders]'"
            )

        super().__init__(
            selector=selector,
            remove_tags=remove_tags,
            timeout=timeout,
            headers=headers,
            **kwargs
        )

        self.selector = selector
        self.remove_tags = remove_tags or ["script", "style", "nav", "footer", "header"]
        self.timeout = timeout
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (compatible; CRAFT-Bot/1.3; +https://github.com/StefanoHernandez/CRAFT)"
        }

    def load(self, source: Union[str, Path]) -> List[Document]:
        """
        Load web page as document.

        Args:
            source: URL to load

        Returns:
            List with single document
        """
        url = str(source)
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers=self.headers
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch URL {url}: {e}")

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract metadata
        metadata = self._extract_metadata(soup, url)

        # Remove unwanted tags
        for tag in self.remove_tags:
            for element in soup.find_all(tag):
                element.decompose()

        # Extract content
        if self.selector:
            # Use CSS selector
            selected = soup.select(self.selector)
            content = "\n\n".join([elem.get_text(strip=True, separator=" ") for elem in selected])
        else:
            # Extract all text
            content = soup.get_text(strip=True, separator=" ")

        # Clean up whitespace
        content = self._clean_text(content)

        return [Document(
            content=content,
            metadata=metadata
        )]

    def load_and_split(
        self,
        source: Union[str, Path],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Document]:
        """
        Load web page and split into chunks.

        Args:
            source: URL to load
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks

        Returns:
            List of chunked documents
        """
        docs = self.load(source)
        if not docs:
            return []

        return self._split_text(
            docs[0].content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            metadata=docs[0].metadata
        )

    def load_batch(self, urls: List[str]) -> List[Document]:
        """
        Load multiple URLs.

        Args:
            urls: List of URLs to load

        Returns:
            List of documents (one per URL)
        """
        documents = []
        for url in urls:
            try:
                docs = self.load(url)
                documents.extend(docs)
            except Exception as e:
                # Log error but continue with other URLs
                print(f"Warning: Failed to load {url}: {e}")
                continue

        return documents

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> dict:
        """Extract metadata from HTML."""
        metadata = {
            "source": url,
            "format": "web",
        }

        # Title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)

        # Meta tags
        meta_tags = {
            "description": soup.find("meta", attrs={"name": "description"}),
            "author": soup.find("meta", attrs={"name": "author"}),
            "keywords": soup.find("meta", attrs={"name": "keywords"}),
        }

        for key, tag in meta_tags.items():
            if tag and tag.get("content"):
                metadata[key] = tag["content"]

        # Open Graph tags
        og_tags = {
            "og_title": soup.find("meta", attrs={"property": "og:title"}),
            "og_description": soup.find("meta", attrs={"property": "og:description"}),
            "og_type": soup.find("meta", attrs={"property": "og:type"}),
        }

        for key, tag in og_tags.items():
            if tag and tag.get("content"):
                metadata[key] = tag["content"]

        # Language
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            metadata["language"] = html_tag["lang"]

        return metadata

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]  # Remove empty lines

        # Join and normalize spaces
        cleaned = " ".join(lines)
        cleaned = " ".join(cleaned.split())  # Normalize multiple spaces

        return cleaned


__all__ = ["WebLoader", "WEB_AVAILABLE"]
