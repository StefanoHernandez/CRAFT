"""Base document loader interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field


class Document(BaseModel):
    """
    Document model representing loaded content.

    Attributes:
        content: The main text content
        metadata: Additional metadata (source, page, etc.)
        embedding: Optional embedding vector
    """

    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        preview = self.content[:100] + "..." if len(self.content) > 100 else self.content
        return f"Document(content='{preview}', metadata={self.metadata})"


class DocumentLoader(ABC):
    """
    Abstract base class for document loaders.

    All loader implementations must inherit from this class.
    """

    def __init__(self, **kwargs: Any):
        """
        Initialize document loader.

        Args:
            **kwargs: Loader-specific configuration
        """
        self.config = kwargs

    @abstractmethod
    def load(self, source: str | Path) -> List[Document]:
        """
        Load documents from source.

        Args:
            source: Path to file, URL, or other source identifier

        Returns:
            List of loaded documents
        """
        pass

    @abstractmethod
    def load_and_split(
        self,
        source: str | Path,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Document]:
        """
        Load documents and split into chunks.

        Args:
            source: Path to file, URL, or other source identifier
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks

        Returns:
            List of chunked documents
        """
        pass

    def _split_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to split
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
            metadata: Metadata to attach to each chunk

        Returns:
            List of chunked documents
        """
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk_text = text[start:end]

            # Try to break at sentence boundary if possible
            if end < text_length:
                # Look for sentence endings
                for delimiter in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                    last_delim = chunk_text.rfind(delimiter)
                    if last_delim > chunk_size * 0.5:  # Only if reasonably close to chunk_size
                        chunk_text = chunk_text[:last_delim + 1]
                        end = start + last_delim + 1
                        break

            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_index": len(chunks),
                "chunk_start": start,
                "chunk_end": min(end, text_length),
            })

            chunks.append(Document(
                content=chunk_text.strip(),
                metadata=chunk_metadata
            ))

            start = end - chunk_overlap

        return chunks


__all__ = ["DocumentLoader", "Document"]
