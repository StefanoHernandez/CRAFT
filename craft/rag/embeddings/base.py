"""Base embedding provider interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class EmbeddingConfig(BaseModel):
    """Base configuration for embedding providers."""

    model: str
    api_key: Optional[str] = None
    batch_size: int = Field(default=32, ge=1)
    max_length: Optional[int] = None

    model_config = ConfigDict(extra="allow")


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.

    All embedding implementations must inherit from this class.
    """

    def __init__(self, config: EmbeddingConfig):
        """
        Initialize embedding provider.

        Args:
            config: Embedding configuration
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    async def aembed_text(self, text: str) -> List[float]:
        """
        Async version of embed_text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def aembed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Async version of embed_texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @property
    def name(self) -> str:
        """Get provider name."""
        return self.__class__.__name__.replace("Embedding", "").lower()

    @property
    def dimension(self) -> int:
        """
        Get embedding dimension.

        Should be overridden by subclasses.
        """
        raise NotImplementedError("Subclass must implement dimension property")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.config.model})"
