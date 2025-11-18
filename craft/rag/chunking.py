"""Document chunking strategies for RAG."""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ChunkingStrategy(str, Enum):
    """Chunking strategy types."""

    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"


class ChunkConfig(BaseModel):
    """Configuration for document chunking."""

    strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    chunk_size: int = Field(default=512, ge=1)
    chunk_overlap: int = Field(default=50, ge=0)
    separator: str = Field(default="\n\n")


class DocumentChunk(BaseModel):
    """A chunk of a document."""

    content: str
    metadata: dict = Field(default_factory=dict)
    chunk_index: int = 0


class DocumentChunker:
    """
    Document chunker with multiple strategies.

    Splits documents into smaller chunks for better RAG performance.
    """

    def __init__(self, config: Optional[ChunkConfig] = None):
        """
        Initialize document chunker.

        Args:
            config: Chunking configuration
        """
        self.config = config or ChunkConfig()

    def chunk_text(self, text: str, metadata: Optional[dict] = None) -> List[DocumentChunk]:
        """
        Chunk text using configured strategy.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of document chunks
        """
        metadata = metadata or {}

        if self.config.strategy == ChunkingStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(text, metadata)
        elif self.config.strategy == ChunkingStrategy.SENTENCE:
            return self._chunk_by_sentence(text, metadata)
        elif self.config.strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(text, metadata)
        elif self.config.strategy == ChunkingStrategy.SEMANTIC:
            return self._chunk_semantic(text, metadata)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.config.strategy}")

    def _chunk_fixed_size(self, text: str, metadata: dict) -> List[DocumentChunk]:
        """Chunk by fixed character size with overlap."""
        chunks = []
        chunk_index = 0

        for i in range(0, len(text), self.config.chunk_size - self.config.chunk_overlap):
            chunk_text = text[i : i + self.config.chunk_size]

            if chunk_text.strip():
                chunks.append(
                    DocumentChunk(
                        content=chunk_text.strip(),
                        metadata={**metadata, "chunk_index": chunk_index},
                        chunk_index=chunk_index,
                    )
                )
                chunk_index += 1

        return chunks

    def _chunk_by_sentence(self, text: str, metadata: dict) -> List[DocumentChunk]:
        """Chunk by sentences, respecting chunk size."""
        # Simple sentence splitting (can be improved with nltk or spacy)
        sentences = self._split_sentences(text)

        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.config.chunk_size and current_chunk:
                # Create chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    DocumentChunk(
                        content=chunk_text,
                        metadata={**metadata, "chunk_index": chunk_index},
                        chunk_index=chunk_index,
                    )
                )

                # Handle overlap
                overlap_sentences = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.config.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break

                current_chunk = overlap_sentences
                current_length = overlap_length
                chunk_index += 1

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                DocumentChunk(
                    content=chunk_text,
                    metadata={**metadata, "chunk_index": chunk_index},
                    chunk_index=chunk_index,
                )
            )

        return chunks

    def _chunk_by_paragraph(self, text: str, metadata: dict) -> List[DocumentChunk]:
        """Chunk by paragraphs."""
        paragraphs = text.split(self.config.separator)

        chunks = []
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If paragraph is too long, split it further
            if len(para) > self.config.chunk_size:
                sub_chunks = self._chunk_fixed_size(para, metadata)
                for sub_chunk in sub_chunks:
                    sub_chunk.chunk_index = chunk_index
                    chunks.append(sub_chunk)
                    chunk_index += 1
            else:
                chunks.append(
                    DocumentChunk(
                        content=para,
                        metadata={**metadata, "chunk_index": chunk_index},
                        chunk_index=chunk_index,
                    )
                )
                chunk_index += 1

        return chunks

    def _chunk_semantic(self, text: str, metadata: dict) -> List[DocumentChunk]:
        """
        Semantic chunking (placeholder for future implementation).

        This would use embeddings to create semantically coherent chunks.
        For now, falls back to sentence chunking.
        """
        # TODO: Implement semantic chunking with embeddings
        return self._chunk_by_sentence(text, metadata)

    def _split_sentences(self, text: str) -> List[str]:
        """
        Simple sentence splitter.

        For production, consider using nltk.sent_tokenize or spacy.
        """
        # Simple regex-based splitting
        import re

        # Split on common sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_documents(
        self, documents: List[str], metadatas: Optional[List[dict]] = None
    ) -> List[DocumentChunk]:
        """
        Chunk multiple documents.

        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dicts for each document

        Returns:
            List of all chunks from all documents
        """
        all_chunks = []

        for i, doc in enumerate(documents):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            metadata["document_index"] = i

            chunks = self.chunk_text(doc, metadata)
            all_chunks.extend(chunks)

        return all_chunks
