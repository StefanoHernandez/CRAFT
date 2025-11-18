"""Sentence Transformer embedding provider (local models)."""

from typing import List, Optional
import asyncio

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from pydantic import Field
from craft.rag.embeddings.base import EmbeddingProvider, EmbeddingConfig


class SentenceTransformerConfig(EmbeddingConfig):
    """Sentence Transformer embedding configuration."""

    model: str = Field(default="all-MiniLM-L6-v2")
    device: Optional[str] = Field(default=None)  # cuda, cpu, or None for auto


class SentenceTransformerEmbedding(EmbeddingProvider):
    """
    Sentence Transformer embedding provider.

    Uses local models from Hugging Face. Fast and free!
    """

    # Popular models and their dimensions
    DIMENSIONS = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "all-MiniLM-L12-v2": 384,
        "paraphrase-multilingual-MiniLM-L12-v2": 384,
        "paraphrase-MiniLM-L6-v2": 384,
    }

    def __init__(self, config: Optional[SentenceTransformerConfig] = None, **kwargs):
        """
        Initialize Sentence Transformer embedding provider.

        Args:
            config: Sentence Transformer configuration
            **kwargs: Additional config parameters
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers package not installed. "
                "Install with: pip install 'craft-chatbot[rag]'"
            )

        if config is None:
            config = SentenceTransformerConfig(**kwargs)
        elif kwargs:
            config = SentenceTransformerConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        # Load model
        self.model = SentenceTransformer(
            self.config.model,
            device=self.config.device
        )

    def _validate_config(self) -> None:
        """Validate configuration."""
        # No special validation needed for local models
        pass

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in batch."""
        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embeddings.tolist()

    async def aembed_text(self, text: str) -> List[float]:
        """Async embed a single text."""
        # Run in thread pool since sentence-transformers is sync
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_text, text)

    async def aembed_texts(self, texts: List[str]) -> List[List[float]]:
        """Async embed multiple texts in batch."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_texts, texts)

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self.config.model in self.DIMENSIONS:
            return self.DIMENSIONS[self.config.model]
        # Fallback: encode empty string and get dimension
        return len(self.embed_text(""))
