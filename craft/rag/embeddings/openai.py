"""OpenAI embedding provider."""

import os
from typing import List, Optional

try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from pydantic import Field
from craft.rag.embeddings.base import EmbeddingProvider, EmbeddingConfig


class OpenAIEmbeddingConfig(EmbeddingConfig):
    """OpenAI embedding configuration."""

    model: str = Field(default="text-embedding-3-small")
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))


class OpenAIEmbedding(EmbeddingProvider):
    """
    OpenAI embedding provider.

    Supports text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002.
    """

    # Model dimensions
    DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, config: Optional[OpenAIEmbeddingConfig] = None, **kwargs):
        """
        Initialize OpenAI embedding provider.

        Args:
            config: OpenAI embedding configuration
            **kwargs: Additional config parameters
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install 'craft-chatbot[openai]'"
            )

        if config is None:
            config = OpenAIEmbeddingConfig(**kwargs)
        elif kwargs:
            config = OpenAIEmbeddingConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        self.client = OpenAI(api_key=self.config.api_key)
        self.async_client = AsyncOpenAI(api_key=self.config.api_key)

    def _validate_config(self) -> None:
        """Validate OpenAI configuration."""
        if not self.config.api_key:
            raise ValueError(
                "OpenAI API key not provided. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        response = self.client.embeddings.create(
            model=self.config.model,
            input=text,
        )
        return response.data[0].embedding

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in batch."""
        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i : i + self.config.batch_size]
            response = self.client.embeddings.create(
                model=self.config.model,
                input=batch,
            )
            all_embeddings.extend([data.embedding for data in response.data])

        return all_embeddings

    async def aembed_text(self, text: str) -> List[float]:
        """Async embed a single text."""
        response = await self.async_client.embeddings.create(
            model=self.config.model,
            input=text,
        )
        return response.data[0].embedding

    async def aembed_texts(self, texts: List[str]) -> List[List[float]]:
        """Async embed multiple texts in batch."""
        all_embeddings = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i : i + self.config.batch_size]
            response = await self.async_client.embeddings.create(
                model=self.config.model,
                input=batch,
            )
            all_embeddings.extend([data.embedding for data in response.data])

        return all_embeddings

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.DIMENSIONS.get(self.config.model, 1536)
