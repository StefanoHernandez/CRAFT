"""Context management for RAG and conversation state."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Context(BaseModel):
    """
    Context holder for RAG-retrieved documents and conversation state.
    """

    # RAG-retrieved documents
    documents: List[Dict[str, Any]] = Field(default_factory=list)

    # Custom context data
    data: Dict[str, Any] = Field(default_factory=dict)

    # System instructions
    system_prompt: Optional[str] = None

    def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None, score: Optional[float] = None) -> None:
        """
        Add a retrieved document to context.

        Args:
            content: Document content
            metadata: Document metadata
            score: Relevance score
        """
        doc = {
            "content": content,
            "metadata": metadata or {},
        }
        if score is not None:
            doc["score"] = score

        self.documents.append(doc)

    def get_documents_text(self, limit: Optional[int] = None) -> str:
        """
        Get formatted text of all documents.

        Args:
            limit: Optional limit on number of documents

        Returns:
            Formatted document text
        """
        docs = self.documents[:limit] if limit else self.documents
        if not docs:
            return ""

        formatted = []
        for i, doc in enumerate(docs, 1):
            formatted.append(f"[Document {i}]")
            formatted.append(doc["content"])
            formatted.append("")

        return "\n".join(formatted)

    def set(self, key: str, value: Any) -> None:
        """Set a context value."""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self.data.get(key, default)

    def clear_documents(self) -> None:
        """Clear all retrieved documents."""
        self.documents = []

    def clear(self) -> None:
        """Clear all context data."""
        self.documents = []
        self.data = {}
        self.system_prompt = None

    def __len__(self) -> int:
        return len(self.documents)

    def __str__(self) -> str:
        return f"Context(documents={len(self.documents)}, data_keys={list(self.data.keys())})"
