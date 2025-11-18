"""PDF document loader."""

from pathlib import Path
from typing import List, Union

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from craft.loaders.base import DocumentLoader, Document


class PDFLoader(DocumentLoader):
    """
    PDF document loader using pypdf.

    Supports:
    - Multi-page PDFs
    - Text extraction from all pages
    - Page-level metadata
    - Automatic chunking with overlap

    Example:
        >>> from craft.loaders import PDFLoader
        >>>
        >>> loader = PDFLoader()
        >>> documents = loader.load("path/to/document.pdf")
        >>> print(f"Loaded {len(documents)} pages")
        >>>
        >>> # Load and split into chunks
        >>> chunks = loader.load_and_split("path/to/document.pdf", chunk_size=500)
        >>> print(f"Split into {len(chunks)} chunks")
    """

    def __init__(self, extract_images: bool = False, **kwargs):
        """
        Initialize PDF loader.

        Args:
            extract_images: Whether to extract images (experimental)
            **kwargs: Additional loader configuration
        """
        if not PDF_AVAILABLE:
            raise ImportError(
                "pypdf package not installed. "
                "Install with: pip install 'craft-chatbot[loaders]'"
            )

        super().__init__(extract_images=extract_images, **kwargs)
        self.extract_images = extract_images

    def load(self, source: Union[str, Path]) -> List[Document]:
        """
        Load PDF and return one document per page.

        Args:
            source: Path to PDF file

        Returns:
            List of documents (one per page)
        """
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"PDF file not found: {source}")

        if not source_path.suffix.lower() == ".pdf":
            raise ValueError(f"Not a PDF file: {source}")

        documents = []
        reader = PdfReader(str(source_path))

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()

            if text.strip():  # Only add non-empty pages
                metadata = {
                    "source": str(source_path),
                    "page": page_num + 1,
                    "total_pages": len(reader.pages),
                    "format": "pdf",
                }

                # Add PDF metadata if available
                if reader.metadata:
                    pdf_meta = {
                        "title": reader.metadata.get("/Title"),
                        "author": reader.metadata.get("/Author"),
                        "subject": reader.metadata.get("/Subject"),
                        "creator": reader.metadata.get("/Creator"),
                    }
                    # Filter out None values
                    pdf_meta = {k: v for k, v in pdf_meta.items() if v}
                    metadata.update(pdf_meta)

                documents.append(Document(
                    content=text,
                    metadata=metadata
                ))

        return documents

    def load_and_split(
        self,
        source: Union[str, Path],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Document]:
        """
        Load PDF and split pages into chunks.

        Args:
            source: Path to PDF file
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks

        Returns:
            List of chunked documents
        """
        pages = self.load(source)
        all_chunks = []

        for page_doc in pages:
            # Split each page into chunks
            chunks = self._split_text(
                page_doc.content,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                metadata=page_doc.metadata
            )
            all_chunks.extend(chunks)

        return all_chunks

    def load_pages(
        self,
        source: Union[str, Path],
        page_numbers: List[int]
    ) -> List[Document]:
        """
        Load specific pages from PDF.

        Args:
            source: Path to PDF file
            page_numbers: List of page numbers to load (1-indexed)

        Returns:
            List of documents for specified pages
        """
        all_pages = self.load(source)
        return [page for page in all_pages if page.metadata["page"] in page_numbers]


__all__ = ["PDFLoader", "PDF_AVAILABLE"]
